"""Program Distributor (PD, « Distributeur de Programme », DP) — milestone J3.

Cycle of one instruction [COURS p.13-16 ; docs/MACHINE.md §5.1-5.2]: the PD serves the most
urgent instruction request (DI); RNE ← element number; A ← its qualitative catena; RAPA ← its
IAR; RAPP ← RAPA + 1; it asks the Data Distributor for the catena at RAPA, which arrives in
REDP [BAT72 p.102]; it executes it without being released (address instruction, branch,
central directive) and goes on with RAPA ← RAPP, until the directive that starts the element
(sent through RSDP; IAR ← RAPP; RNE cleared) or a cut.

J3 runs one sequence at a time: recall chains, SIMU, joins, virtual elements and special cuts
come at J4 and are refused with :class:`MachineUnsupported`.
"""

from __future__ import annotations

from collections.abc import Callable

from gamma60 import data
from gamma60.catena import MASK15, MASK24, bits, set_bits
from gamma60.code_a import (
    ADDRESS,
    ALWAYS,
    BRANCH,
    CENTRAL,
    CUT,
    ELEMENT,
    NEVER,
    DecodeError,
    decode,
)
from gamma60.core.arit import compare_positions, set_position
from gamma60.data_distributor import INSTRUCTION, PD, QUANTITY, READ, WRITE, Request
from gamma60.elements.base import IDLE, WAITING
from gamma60.registers import IarMatrix, PDRegisters


class MachineUnsupported(NotImplementedError):
    """Valid code A that the J3 machine does not execute yet (J4: concurrency)."""


class ProgramDistributor:
    name = "PD"

    def __init__(self, machine) -> None:
        self.m = machine
        self.regs = PDRegisters()
        self.iar = IarMatrix()
        self.port = machine.dd.attach(self, PD, "PD")
        self.di: list = []  # elements whose DI line is raised
        self.busy = False
        self.element = None  # element being served (None: the PD's own sequence at start)
        self.instr_address = 0
        self.executed = 0
        self._then: Callable[[int], None] | None = None
        t = data.load("timings")["program_distributor"]
        cycle = machine.dd.cycle
        self.exec_us = data.resolve(t["instruction_cycles"]) * cycle
        self.send_us = data.resolve(t["directive_send_cycles"]) * cycle
        self.class_order = data.load("priorities")["dti"]["by_class"]

    # -- instruction requests -----------------------------------------------------------------

    def request_instruction(self, element) -> None:
        element.state = WAITING
        if element not in self.di:
            self.di.append(element)
        self._try_serve()

    def _try_serve(self) -> None:
        if self.busy or not self.di or self.m.stopped:
            return
        rank = {c: i for i, c in enumerate(self.class_order)}
        element = min(self.di, key=lambda e: (rank.get(e.port.cls, 99), e.port.order))
        self.busy = True
        self.m.engine.after(0, lambda: self._serve(element), "PD serve")

    def _serve(self, element) -> None:
        self.di.remove(element)
        self.element = element
        r = self.regs
        r.rne, r.a, r.rapa = element.number, element.qualitative, self.iar.address[element.number]
        self.m.engine.record("PD", "serve", element=element.name, rapa=r.rapa)
        self._fetch()

    def start(self, entry: int) -> None:
        """Run the first instruction as a sequence of the PD itself (emulator convention)."""
        self.busy, self.element = True, None
        self.regs.rapa = entry
        self.m.engine.after(0, self._fetch, "PD start")

    # -- memory through the Data Distributor ---------------------------------------------------

    def _rank(self) -> str | None:
        return self.element.kind if self.element is not None else None

    def _read(self, address: int, then: Callable[[int], None], nature: str = QUANTITY) -> None:
        self._then = then
        self.m.dd.request(
            self.port, 0, READ, nature=nature, rank_as=self._rank(), address=address & MASK15
        )

    def _write(self, address: int, value: int, then: Callable[[], None]) -> None:
        self._then = lambda _v: then()
        self.m.dd.request(
            self.port,
            0,
            WRITE,
            value=value & MASK24,
            rank_as=self._rank(),
            address=address & MASK15,
        )

    def transfer_done(self, request: Request, value: int) -> None:
        then, self._then = self._then, None
        assert then is not None
        then(value)

    def transfer_incident(self, request: Request, reason: str) -> None:
        self.m.incident(f"PD: {reason} error at address {request.address:05d}")

    # -- one instruction --------------------------------------------------------------------------

    def _fetch(self) -> None:
        r = self.regs
        r.rapp = (r.rapa + 1) & MASK15
        self.instr_address = r.rapa
        self._read(r.rapa, self._fetched, INSTRUCTION)

    def _fetched(self, value: int) -> None:
        self.regs.redp = value
        self.executed += 1
        self.m.engine.after(self.exec_us, self._execute, "PD execute")

    def _execute(self) -> None:
        r = self.regs
        try:
            word = decode(r.redp)
        except DecodeError as exc:
            if self.m.mode == "diagnostic":
                self.m.engine.record("PD", "warning", text=str(exc))
            self.m.incident(f"decoded directive error at {self.instr_address:05d}: {exc}")
            return
        self.m.engine.record(
            "PD", "instruction", address=self.instr_address, word=word, element=self._name()
        )
        self.m.observe(self)
        x = word.x
        if word.d:
            x = (self.instr_address + x) & MASK15
        if word.s:
            self._read(x, lambda v: self._do(word, v & MASK15))
        else:
            self._do(word, x)

    def _name(self) -> str:
        return self.element.name if self.element is not None else "-"

    def _next(self) -> None:
        self.regs.rapa = self.regs.rapp
        self._fetch()

    def _do(self, w, x: int) -> None:
        if w.kind == BRANCH:
            cond = w.op
            taken = cond == ALWAYS or (1 <= cond <= 24 and bits(self.regs.a, cond, cond))
            if taken:
                self.regs.rsdp, self.regs.rapa = self.regs.rapp, x
                self._fetch()
            else:
                self._next()
        elif w.kind == ADDRESS:
            self._address(w.op, w.car, x)
        elif w.kind == CENTRAL:
            self._central(w.op, x)
        elif w.kind == CUT:
            self._cut(w, x)
        elif w.kind == ELEMENT:
            if self.element is None:
                self.m.incident(f"directive at {self.instr_address:05d} before any cut")
                return
            self.regs.rsdp = self.regs.redp
            self.m.engine.after(self.send_us, self._deliver, "PD directive")

    def _deliver(self) -> None:
        element, r = self.element, self.regs
        self.iar.address[element.number] = r.rapp
        r.rne, self.element, self.busy = None, None, False
        self.m.engine.record("PD", "directive", element=element.name, iar=r.rapp)
        element.directive_address = self.instr_address
        element.receive(bits(r.rsdp, 20, 1))
        self._try_serve()

    def _release(self) -> None:
        self.regs.rne, self.element, self.busy = None, None, False
        self._try_serve()

    # -- address instructions [COURS p.33-52 ; ISA.md §2] ---------------------------------------------

    def _address(self, op: str, car: int, x: int) -> None:
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
            self._write(x, racs.get(name, car), self._next)
            return
        self._next()

    # -- central directives [COURS p.53-60] ---------------------------------------------------------

    def _central(self, op: str, x: int) -> None:
        r = self.regs
        b15 = r.b & MASK15
        if op == "store_instruction_number":  # 15 right positions, 9 left cleared
            self._write(x, r.rsdp & MASK15, self._next)
        elif op == "load_element_number":
            r.rne = x & 0x7F
            self.element = self.m.element_by_number(r.rne)
            self._next()
        elif op == "store_element_number":
            self._write(x, r.rne or 0, self._next)
        elif op == "transfer_to_A":  # implicit substitution: X is an address
            self._read(x, lambda v: (setattr(r, "a", v), self._next()))
        elif op == "place_A":
            self._write(x, r.a, self._next)
        elif op == "transfer_to_B":
            self._read(x, lambda v: (setattr(r, "b", v), self._next()))
        elif op == "place_B":
            self._write(x, r.b, self._next)
        elif op == "load_B_15":  # 15 right positions of B; the 9 left ones unchanged
            r.b = (r.b & ~MASK15 & MASK24) | x
            self._next()
        elif op == "add_B_15":  # carry beyond position 15 lost
            r.b = (r.b & ~MASK15 & MASK24) | ((b15 + x) & MASK15)
            self._next()
        elif op == "subtract_B_15":
            r.b = (r.b & ~MASK15 & MASK24) | ((b15 - x) & MASK15)
            self._next()
        elif op == "compare_B_15":  # B relative to X, positions 1-6 of A [COURS p.55]
            positions = compare_positions(b15, x)
            reset = data.resolve(data.load("behavior")["qualitative_reset_each_directive"])
            r.a = positions if reset else r.a | positions  # rest of A: U-07
            self._next()
        elif op == "substitute_quantity_in_B":
            self._read(b15, lambda v: (setattr(r, "b", v), self._next()))
        elif op == "substitute_instruction":
            self._read(b15, lambda v: self._substituted(v, b15))
        elif op in ("switch_branch_always", "switch_branch_never", "reverse_switches"):
            self._read(x, lambda v: self._switch(op, x, v))
        elif op == "fill_ones":
            self._write(x, MASK24, self._next)
        elif op == "fill_zeros":
            self._write(x, 0, self._next)
        elif op == "iteration_control":
            self._read(x, lambda v: self._iteration(x, v))
        elif op == "counter_progression":
            self._read(x, lambda v: self._progress(x, v))
        else:  # pragma: no cover - every identifier of encoding.yaml is handled
            raise MachineUnsupported(op)

    def _substituted(self, value: int, address: int) -> None:
        """SI: execute the instruction at the address held in B, then go on after SI."""
        self.regs.redp = value
        self.instr_address = address
        self.m.engine.after(self.exec_us, self._execute, "PD execute (SI)")

    def _switch(self, op: str, x: int, value: int) -> None:
        cond = bits(value, 22, 18)
        if op == "switch_branch_always":
            cond = ALWAYS
        elif op == "switch_branch_never":
            cond = NEVER
        elif cond in (ALWAYS, NEVER):  # FI / RR: always ↔ never
            cond = NEVER if cond == ALWAYS else ALWAYS
        new = set_bits(value, 22, 18, cond)
        self.regs.b = new  # register B is implicit in these directives [COURS p.56]
        self._write(x, new, self._next)

    def _iteration(self, x: int, value: int) -> None:
        r = self.regs
        r.b = value
        if value & MASK15 == 0:
            r.a = set_position(0, 14)  # the whole register A is changed [COURS p.57]
            self._read(x + 1, lambda n: self._write(x, n, self._next))
        else:
            r.a = set_position(0, 15)
            self._write(x, value - 1, self._next)

    def _progress(self, x: int, value: int) -> None:
        self.regs.b = value  # B keeps the old content [COURS p.57]
        self._write(x, (value & ~MASK15 & MASK24) | ((value + 1) & MASK15), self._next)

    # -- cuts ---------------------------------------------------------------------------------------

    def _cut(self, w, x: int) -> None:
        requester = self.element
        if w.op == "STOP":
            if requester is not None:
                self.iar.busy[requester.number] = False
                requester.state = IDLE
            self.m.engine.record("PD", "stop", element=self._name())
            self._release()
            return
        if w.op != "normal":
            raise MachineUnsupported(f"{w.op} at {self.instr_address:05d} (milestone J4)")
        if w.m:
            raise MachineUnsupported(f"join at {self.instr_address:05d} (milestone J4)")
        target = self.m.element_by_number(x)
        if target is None:
            self.m.incident(f"cut at {self.instr_address:05d}: no element number {x}")
            return
        if target is not requester and target.state != IDLE:
            raise MachineUnsupported(
                f"cut on busy {target.name} at {self.instr_address:05d}: recall chains (J4)"
            )
        # (1) activate the element named by the cut, after the blank catena [COURS p.38]
        self.iar.address[target.number] = (self.instr_address + 2) & MASK15
        self.iar.busy[target.number] = True
        # (3) release the requesting element
        if requester is not None and requester is not target:
            self.iar.busy[requester.number] = False
            requester.state = IDLE
        self.m.engine.record("PD", "cut", element=target.name, iar=self.iar.address[target.number])
        self.regs.rne, self.element, self.busy = None, None, False
        # (4) serve a new instruction request
        self.request_instruction(target)
