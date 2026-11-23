"""Program Distributor (PD, « Distributeur de Programme », DP) — milestones J3 and J4.

Cycle of one instruction [COURS p.13-16 ; docs/MACHINE.md §5.1-5.2]: the PD serves the most
urgent instruction request (DI); RNE ← element number; A ← its qualitative catena; RAPA ← its
IAR; RAPP ← RAPA + 1; it asks the Data Distributor for the catena at RAPA, which arrives in
REDP [BAT72 p.102]; it executes it without being released (address instruction, branch,
central directive) and goes on with RAPA ← RAPP, until the directive that starts the element
(sent through RSDP; IAR ← RAPP; RNE cleared) or a cut.

Concurrency (J4) [COURS p.17-18, p.24-31, p.33-39]:

- a normal cut (1) loads the IAR of the named element with the address of the blank catena
  that follows the cut (executed as a "never" branch), or queues the sequence on the element's
  recall chain if it is active; (2) empties the PD's own chain; (3) resumes the chain of the
  requesting element or releases it; (4) only then serves a new DI;
- recall chains: registers B (head) and C (tail) of each element, in a table in central memory
  (U-30); the links are written in the blank catenae; FIFO order;
- SIMU: the ordinary branch (its blank catena) goes on the PD's own chain (registers B, C of the
  PD), the extraordinary branch is executed first;
- joins: a cut with m > 0 becomes effective at its (m + 1)-th call, counted in bits 19-18 of
  its blank catena (U-26 for the early arrivals);
- virtual elements: PROT / LIBE on two image catenae (busy bit 24 + head, tail);
- special cuts (COURS profile): without release of the requester; without observing the busy
  state of the named element.

The work of the PD is a generator of commands (read / write through the DD, wait), so that the
long chains of memory accesses stay readable and deterministic.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

from gamma60 import data
from gamma60.catena import MASK15, MASK24, bits, set_bits
from gamma60.code_a import (
    ADDRESS,
    ALWAYS,
    BRANCH,
    CENTRAL,
    ELEMENT,
    NEVER,
    DecodeError,
    decode,
    has_address_function,
)
from gamma60.core.arit import compare_positions, set_position
from gamma60.data_distributor import INSTRUCTION, PD, QUANTITY, READ, WRITE, Request
from gamma60.elements.base import IDLE, OPERATING, WAITING
from gamma60.registers import IarMatrix, PDRegisters

BUSY_BIT = 1 << 23  # bit 24 of the first image catena of a virtual element [COURS p.29-31]

Work = Generator[tuple, Any, Any]


class MachineUnsupported(NotImplementedError):
    """Valid code A that the machine does not execute yet."""


class ProgramDistributor:
    name = "PD"

    def __init__(self, machine) -> None:
        self.m = machine
        self.regs = PDRegisters()
        self.iar = IarMatrix()
        self.port = machine.dd.attach(self, PD, "PD")
        self.di: list = []  # elements whose DI line is raised
        self.busy = False
        self.element = None  # element being served (None: the PD works for no element)
        self.instr_address = 0
        self.executed = 0
        self.pd_b = 0  # own recall chain: head (B) and tail (C) [COURS p.36-37]
        self.pd_c = 0
        self._gen: Work | None = None
        t = data.load("timings")["program_distributor"]
        cycle = machine.dd.cycle
        self.exec_us = data.resolve(t["instruction_cycles"]) * cycle
        self.send_us = data.resolve(t["directive_send_cycles"]) * cycle
        self.class_order = data.load("priorities")["dti"]["by_class"]
        chain = data.resolve(data.load("behavior")["recall_chain_registers"])
        self.chain_base = chain["base_address"]
        self.chain_size = chain["catenae_per_element"]
        self.release_rule = data.resolve(data.load("behavior")["requester_release"])

    # -- addresses of the recall chain registers B, C of an element (U-30) ----------------------

    def chain_b(self, element) -> int:
        return self.chain_base + self.chain_size * element.number

    def chain_c(self, element) -> int:
        return self.chain_b(element) + 1

    # -- driving the generator ----------------------------------------------------------------

    def _start(self, work: Work) -> None:
        self.busy = True
        self._gen = work
        self.m.engine.after(0, lambda: self._advance(None), "PD")

    def _advance(self, value: Any) -> None:
        if self.m.stopped or self._gen is None:
            return
        try:
            cmd = self._gen.send(value)
        except StopIteration:
            self._gen = None
            self.busy, self.element, self.regs.rne = False, None, None
            self._try_serve()
            return
        if cmd[0] == "read":
            _, address, nature = cmd
            self.m.dd.request(
                self.port, 0, READ, nature=nature, rank_as=self._rank(), address=address & MASK15
            )
        elif cmd[0] == "write":
            self.m.dd.request(
                self.port,
                0,
                WRITE,
                value=cmd[2] & MASK24,
                rank_as=self._rank(),
                address=cmd[1] & MASK15,
            )
        else:  # wait
            self.m.engine.after(cmd[1], lambda: self._advance(None), "PD work")

    def transfer_done(self, request: Request, value: int) -> None:
        self._advance(value)

    def transfer_incident(self, request: Request, reason: str) -> None:
        self.m.incident(f"PD: {reason} error at address {request.address:05d}")

    def _rank(self) -> str | None:
        return self.element.kind if self.element is not None else None

    @staticmethod
    def _read(address: int, nature: str = QUANTITY) -> Work:
        value = yield ("read", address, nature)
        return value

    @staticmethod
    def _write(address: int, value: int) -> Work:
        yield ("write", address, value)

    # -- instruction requests -----------------------------------------------------------------

    def request_instruction(self, element) -> None:
        self._raise_di(element)
        self._try_serve()

    def _raise_di(self, element) -> None:
        """DI line raised; while the PD is busy it is taken into account at step (4)."""
        element.state = WAITING
        if element not in self.di:
            self.di.append(element)

    def _try_serve(self) -> None:
        if self.busy or self.m.stopped:
            return
        if self.pd_b:  # the PD's own chain goes before the DI [COURS p.36]
            self._start(self._own_chain())
            return
        if not self.di:
            return
        rank = {c: i for i, c in enumerate(self.class_order)}
        element = min(self.di, key=lambda e: (rank.get(e.port.cls, 99), e.port.order))
        self._start(self._serve(element))

    def _serve(self, element) -> Work:
        self.di.remove(element)
        self.element = element
        r = self.regs
        r.rne, r.a, r.rapa = element.number, element.qualitative, self.iar.address[element.number]
        self.m.engine.record("PD", "serve", element=element.name, rapa=r.rapa)
        yield from self._sequence()
        yield from self._own_chain()

    def start(self, entry: int) -> None:
        """Run the first instruction as a sequence of the PD itself (emulator convention)."""
        self.regs.rapa = entry

        def work() -> Work:
            yield from self._sequence()
            yield from self._own_chain()

        self._start(work())

    # -- one sequence: instruction after instruction ------------------------------------------------

    def _sequence(self) -> Work:
        """Fetch and execute instructions until the PD is released from this sequence."""
        while True:
            r = self.regs
            r.rapp = (r.rapa + 1) & MASK15
            self.instr_address = r.rapa
            r.redp = yield from self._read(r.rapa, INSTRUCTION)
            self.executed += 1
            yield ("wait", self.exec_us)
            if (yield from self._execute(r.redp, self.instr_address)):
                return

    def _execute(self, value: int, address: int) -> Work:
        """Execute one instruction; True when the PD is released from the sequence."""
        r = self.regs
        try:
            word = decode(value)
        except DecodeError as exc:
            if self.m.mode == "diagnostic":
                self.m.engine.record("PD", "warning", text=str(exc))
            self.m.incident(f"decoded directive error at {address:05d}: {exc}")
            yield ("wait", 0)
            return True
        self.m.engine.record("PD", "instruction", address=address, word=word, element=self._name())
        self.m.observe(self)
        x = word.x
        if word.d:
            x = (address + x) & MASK15
        if word.s:
            x = (yield from self._read(x)) & MASK15
        if word.kind == BRANCH:
            cond = word.op
            if cond == ALWAYS or (1 <= cond <= 24 and bits(r.a, cond, cond)):
                r.rsdp, r.rapa = r.rapp, x
            else:
                r.rapa = r.rapp
            return False
        if word.kind == ADDRESS:
            yield from self._address(word.op, word.car, x)
            r.rapa = r.rapp
            return self.m.stopped
        if word.kind == CENTRAL:
            if word.op == "substitute_instruction":  # SI: the instruction at the address in B
                b15 = r.b & MASK15
                r.redp = yield from self._read(b15)
                yield ("wait", self.exec_us)
                return (yield from self._execute(r.redp, b15))
            yield from self._central(word.op, x)
            r.rapa = r.rapp
            return False
        if word.kind == ELEMENT:
            element = self.element
            if element is None:
                self.m.incident(f"directive at {address:05d} before any cut")
                return True
            characteristic = bits(r.redp, 20, 1)
            if has_address_function(element.kind, characteristic):  # d / s on the X [COURS p.75]
                xd = bits(characteristic, 15, 1)
                if bits(characteristic, 17, 17):
                    xd = (address + xd) & MASK15
                if bits(characteristic, 16, 16):
                    xd = (yield from self._read(xd)) & MASK15
                characteristic = set_bits(set_bits(characteristic, 17, 16, 0), 15, 1, xd)
            r.rsdp = set_bits(r.redp, 20, 1, characteristic)
            yield ("wait", self.send_us)
            self.iar.address[element.number] = r.rapp
            self.m.engine.record("PD", "directive", element=element.name, iar=r.rapp)
            self.element, r.rne = None, None
            element.directive_address = address
            element.receive(bits(r.rsdp, 20, 1))
            return True
        return (yield from self._cut(word, x))

    def _name(self) -> str:
        return self.element.name if self.element is not None else "-"

    # -- address instructions [COURS p.33-52 ; ISA.md §2] ---------------------------------------------

    def _address(self, op: str, car: int, x: int) -> Work:
        if self.element is None:
            self.m.incident(f"address instruction at {self.instr_address:05d} before any cut")
            return
        racs, name = self.m.dd.racs, self.element.name
        if op == "load":
            racs.set(name, car, x)
        elif op == "add":
            racs.set(name, car, racs.get(name, car) + x)
        elif op == "subtract":
            racs.set(name, car, racs.get(name, car) - x)
        elif op == "place":
            yield from self._write(x, racs.get(name, car))

    # -- central directives [COURS p.53-60] ---------------------------------------------------------

    def _central(self, op: str, x: int) -> Work:
        r = self.regs
        b15 = r.b & MASK15
        if op == "store_instruction_number":  # 15 right positions, 9 left cleared
            yield from self._write(x, r.rsdp & MASK15)
        elif op == "load_element_number":
            r.rne = x & 0x7F
            self.element = self.m.element_by_number(r.rne)
        elif op == "store_element_number":
            yield from self._write(x, r.rne or 0)
        elif op == "transfer_to_A":  # implicit substitution: X is an address
            r.a = yield from self._read(x)
        elif op == "place_A":
            yield from self._write(x, r.a)
        elif op == "transfer_to_B":
            r.b = yield from self._read(x)
        elif op == "place_B":
            yield from self._write(x, r.b)
        elif op == "load_B_15":  # 15 right positions of B; the 9 left ones unchanged
            r.b = (r.b & ~MASK15 & MASK24) | x
        elif op == "add_B_15":  # carry beyond position 15 lost
            r.b = (r.b & ~MASK15 & MASK24) | ((b15 + x) & MASK15)
        elif op == "subtract_B_15":
            r.b = (r.b & ~MASK15 & MASK24) | ((b15 - x) & MASK15)
        elif op == "compare_B_15":  # B relative to X, positions 1-6 of A [COURS p.55]
            positions = compare_positions(b15, x)
            reset = data.resolve(data.load("behavior")["qualitative_reset_each_directive"])
            r.a = positions if reset else r.a | positions  # rest of A: U-07
        elif op == "substitute_quantity_in_B":
            r.b = yield from self._read(b15)
        elif op in ("switch_branch_always", "switch_branch_never", "reverse_switches"):
            value = yield from self._read(x)
            cond = bits(value, 22, 18)
            if op == "switch_branch_always":
                cond = ALWAYS
            elif op == "switch_branch_never":
                cond = NEVER
            elif cond in (ALWAYS, NEVER):  # FI / RR: always ↔ never
                cond = NEVER if cond == ALWAYS else ALWAYS
            r.b = set_bits(value, 22, 18, cond)  # register B is implicit [COURS p.56]
            yield from self._write(x, r.b)
        elif op == "fill_ones":
            yield from self._write(x, MASK24)
        elif op == "fill_zeros":
            yield from self._write(x, 0)
        elif op == "iteration_control":
            value = yield from self._read(x)
            r.b = value
            if value & MASK15 == 0:
                r.a = set_position(0, 14)  # the whole register A is changed [COURS p.57]
                reload = yield from self._read(x + 1)
                yield from self._write(x, reload)
            else:
                r.a = set_position(0, 15)
                yield from self._write(x, value - 1)
        elif op == "counter_progression":
            value = yield from self._read(x)
            r.b = value  # B keeps the old content [COURS p.57]
            yield from self._write(x, (value & ~MASK15 & MASK24) | ((value + 1) & MASK15))
        else:  # pragma: no cover - every identifier of encoding.yaml is handled
            raise MachineUnsupported(op)

    # -- recall chains [COURS p.24-26, p.36-37] -----------------------------------------------------

    def _enqueue(self, b_address: int, c_address: int, sequence: int, keep_bit24: bool) -> Work:
        """Put ``sequence`` (address of its blank catena) at the tail of a chain in memory."""
        tail = (yield from self._read(c_address)) & MASK15
        if tail == 0:
            head = (yield from self._read(b_address)) if keep_bit24 else 0
            yield from self._write(b_address, (head & BUSY_BIT) | sequence)
        else:
            link = yield from self._read(tail)
            yield from self._write(tail, set_bits(link, 15, 1, sequence))
        yield from self._write(c_address, sequence)

    def _push_own_chain(self, sequence: int) -> Work:
        if self.pd_c == 0:
            self.pd_b = sequence
        else:
            link = yield from self._read(self.pd_c)
            yield from self._write(self.pd_c, set_bits(link, 15, 1, sequence))
        self.pd_c = sequence
        self.m.engine.record("PD", "own chain", sequence=sequence)

    def _own_chain(self) -> Work:
        """Step (2): run the sequences waiting on the PD's own chain, in their order."""
        while self.pd_b and not self.m.stopped:
            sequence = self.pd_b
            link = yield from self._read(sequence)
            yield from self._write(sequence, 0)  # the blank catena is reset [COURS p.26]
            self.pd_b = link & MASK15
            if self.pd_b == 0:
                self.pd_c = 0
            self.m.engine.record("PD", "resume own chain", sequence=sequence, element=self._name())
            self.regs.rapa = sequence
            yield from self._sequence()

    def _release(self, requester) -> Work:
        """Step (3): resume the requester's chain, or release it [COURS p.25-26, p.38]."""
        if requester is None:
            return
        if self.release_rule == "keep_if_operating" and (
            requester.state == OPERATING or requester in self.di
        ):
            return  # U-45: step (2) gave it new work (a directive, or its chain resumed)
        b = self.chain_b(requester)
        head = (yield from self._read(b)) & MASK15
        if head:
            link = yield from self._read(head)
            yield from self._write(head, 0)
            yield from self._write(b, link & MASK15)
            if link & MASK15 == 0:
                yield from self._write(self.chain_c(requester), 0)
            self.iar.address[requester.number] = head
            self.iar.busy[requester.number] = True
            self._raise_di(requester)
            self.m.engine.record("PD", "resume", element=requester.name, sequence=head)
        else:
            self.iar.busy[requester.number] = False
            requester.state = IDLE
            if requester in self.di:
                self.di.remove(requester)
            self.m.engine.record("PD", "release", element=requester.name)

    def _activate(self, element, sequence: int) -> None:
        self.iar.address[element.number] = sequence
        self.iar.busy[element.number] = True
        self.m.engine.record("PD", "cut", element=element.name, iar=sequence)
        self._raise_di(element)

    # -- cuts [COURS p.33-39] -----------------------------------------------------------------------

    def _end_of_cut(self, requester, release: bool = True) -> Work:
        """Steps (2) and (3) of a cut; step (4) follows when the PD is released."""
        yield from self._own_chain()
        if release:
            yield from self._release(requester)

    def _cut(self, w, x: int) -> Work:
        r, requester = self.regs, self.element
        blank = (self.instr_address + 1) & MASK15
        if w.op == "STOP":
            self.m.engine.record("PD", "stop", element=self._name())
            yield from self._end_of_cut(requester)
            return True
        if w.m:  # join: effective at the (m + 1)-th call [COURS p.17-18, p.35]
            value = yield from self._read(blank)
            count = bits(value, 19, 18)
            if count < w.m:
                yield from self._write(blank, set_bits(value, 19, 18, count + 1))
                self.m.engine.record(
                    "PD", "join", arrival=count + 1, expected=w.m + 1, address=self.instr_address
                )
                yield from self._end_of_cut(requester)  # U-26: ends like a STOP
                return True
            yield from self._write(blank, set_bits(value, 19, 18, 0))
            self.m.engine.record(
                "PD", "join", arrival=count + 1, expected=w.m + 1, address=self.instr_address
            )
        if w.op == "SIMU":  # ordinary branch on the PD's own chain, extraordinary branch now
            yield from self._push_own_chain(blank)
            r.rapa = x
            return False
        if w.op == "PROT":
            image = yield from self._read(x)
            if not image & BUSY_BIT:  # free: occupy it, go on with this sequence
                yield from self._write(x, image | BUSY_BIT)
                self.m.engine.record("PD", "occupy", image=x)
                r.rapa = r.rapp
                return False
            yield from self._enqueue(x, x + 1, blank, keep_bit24=True)
            self.m.engine.record("PD", "queue", virtual=x, sequence=blank)
            yield from self._end_of_cut(requester)
            return True
        if w.op == "LIBE":
            image = yield from self._read(x)
            head = image & MASK15
            if head == 0:
                yield from self._write(x, 0)  # nobody waiting: the virtual element is free
                self.m.engine.record("PD", "free", image=x)
            else:
                link = yield from self._read(head)
                yield from self._write(head, 0)
                yield from self._write(x, BUSY_BIT | (link & MASK15))
                if link & MASK15 == 0:
                    yield from self._write(x + 1, 0)
                yield from self._push_own_chain(head)  # [COURS p.37]
            r.rapa = r.rapp
            return False
        # cut on a real element: normal or special (COURS profile)
        target = self.m.element_by_number(x)
        if target is None:
            self.m.incident(f"cut at {self.instr_address:05d}: no element number {x}")
            return True
        if w.op == "no_busy_check":
            # its IAR is free because a cut without release came before: this sequence runs
            # before those waiting on the chain [COURS p.39]
            self._activate(target, blank)
        elif self.iar.busy[target.number]:
            shared = getattr(target, "shared", None)
            if (
                self.m.mode == "diagnostic"
                and shared is not None
                and shared.handovers
                and getattr(requester, "shared", None) is not shared
            ):  # « système fermé »: no recall chain on an uniselector in continuous mode [COURS p.150]
                self.m.engine.record(
                    "PD", "warning", text=f"recall chain on {target.name} in continuous mode"
                )
            yield from self._enqueue(self.chain_b(target), self.chain_c(target), blank, False)
            self.m.engine.record("PD", "queue", element=target.name, sequence=blank)
        else:
            self._activate(target, blank)
        yield from self._end_of_cut(requester, release=w.op != "no_release")
        return True
