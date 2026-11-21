"""Data Distributor (DD, « Distributeur de Données / de Transferts », DT): one catena per cycle.

What the sources give (docs/MACHINE.md §5.3):

- the store transfers one catena per memory cycle, 10 µs (B61) or 11 µs (COURS), for the whole
  machine [B61 p.11, p.23];
- each element has a one-catena buffer register (RLN), filled or emptied in one cycle
  [B61 p.23 ; COURS p.8];
- the CAR of the element advances by one at each transfer [B61 p.22-23];
- requests are served in an order preset by the nature of the element, the drum before ARIT
  [B61 p.23-24]; at equal nature, quantities before instructions [COURS p.6];
- the DD runs a priority chain and opens the channels DDC (store → elements) and DCC (elements
  → store) through gates of each class circuit [BAT72 p.100-101, fig. 1];
- the Program Distributor reads the program through transfer requests like the other units
  [BAT72 p.102].

What they do not give is read from ``data/`` (U-03, U-16, U-32, U-40 to U-43).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from gamma60 import data
from gamma60.catena import KeyError_
from gamma60.engine import Engine
from gamma60.memory import Memory, SelectionError
from gamma60.registers import RacMatrix, racs_for

READ, WRITE = "read", "write"  # read: store → element (DDC); write: element → store (DCC)
CHANNEL = {READ: "DDC", WRITE: "DCC"}
QUANTITY, INSTRUCTION = "quantity", "instruction"
PD = "program_distributor"  # the PD reads at the address of its RAPA, not through a CAR


class Client(Protocol):
    name: str

    def transfer_done(self, request: Request, value: int) -> None: ...

    def transfer_incident(self, request: Request, reason: str) -> None: ...


@dataclass
class Port:
    """An element attached to the DD: its kind, class, circuit and rank in the configuration."""

    client: Any
    name: str
    kind: str
    cls: int | None
    circuit: str
    order: int
    buffer: int = 0  # buffer register (RLN): last catena transferred


@dataclass
class Request:
    """A data transfer request (DTQ, DTR in BAT72)."""

    port: Port
    rac: int
    direction: str
    nature: str = QUANTITY
    value: int | None = None  # catena to write (direction WRITE)
    step: int = 1  # CAR progression: +1, or −1 (e.g. tape read backwards)
    rank_as: str | None = None  # rank of another element kind (PD fetches: U-16)
    address: int | None = None  # explicit address (PD: RAPA); otherwise the CAR ``rac``
    raised: int = 0
    seq: int = 0


@dataclass
class Stats:
    served: dict[str, int] = field(default_factory=dict)
    wait_total: dict[str, int] = field(default_factory=dict)
    wait_max: dict[str, int] = field(default_factory=dict)
    gates: dict[tuple[str, str], int] = field(default_factory=dict)
    busy_cycles: int = 0
    incidents: int = 0
    warnings: int = 0

    def mean_wait(self, name: str) -> float:
        return self.wait_total.get(name, 0) / self.served[name] if self.served.get(name) else 0.0


class DataDistributor:
    def __init__(
        self,
        engine: Engine,
        memory: Memory,
        profile: data.Profile | None = None,
        *,
        order: list[str] | None = None,
        behavior: dict[str, Any] | None = None,
        classes: dict[str, int] | None = None,
        mode: str = "faithful",
    ) -> None:
        if mode not in ("faithful", "diagnostic"):
            raise ValueError(f"unknown mode {mode!r}")
        self.engine, self.memory, self.mode = engine, memory, mode
        self.profile = profile or memory.profile
        self.cycle = self.profile.memory_cycle_us
        self.racs = RacMatrix()

        prio = data.load("priorities")["dtd"]
        self.order = list(order or prio["order"])
        self.nature_order = list(prio["nature_order"])
        if data.resolve(prio["tie_break"]) != "configuration_order":
            raise ValueError("unsupported tie_break (expected configuration_order)")

        defaults = {k: data.resolve(v) for k, v in data.load("behavior").items()}
        self.behavior = {**defaults, **(behavior or {})}
        if self.behavior["dd_cycle_grid"] != "aligned_on_zero":
            raise ValueError("unsupported dd_cycle_grid (expected aligned_on_zero)")

        topo = data.load("topology")
        self.classes = {k: data.resolve(v) for k, v in topo["classes"].items()}
        self.classes.update(classes or {})
        self.circuits = data.resolve(topo["circuits"])
        self.multiplexed = {c["id"] for c in self.circuits if c.get("multiplexer")}
        if data.resolve(topo["multiplexer"]["service"]) != "round_robin":
            raise ValueError("unsupported multiplexer service (expected round_robin)")
        if data.resolve(topo["circuit_assignment"]) != "alternate":
            raise ValueError("unsupported circuit assignment (expected alternate)")
        self._per_class: dict[int, int] = {}

        self.ports: dict[str, Port] = {}
        self.pending: list[Request] = []
        self.stats = Stats()
        self._seq = 0
        self._last_cycle = -self.cycle
        self._cycle_event = None
        self._mux_last: dict[str, int] = {}
        self._warned: set[int] = set()

    # -- attachment ---------------------------------------------------------------------------

    def attach(self, client: Any, kind: str, name: str | None = None) -> Port:
        """Attach an element: allocate its CARs and give it the circuit of its class."""
        name = name or getattr(client, "name", kind)
        if name in self.ports:
            raise ValueError(f"element {name} already attached")
        if kind == PD:  # central unit: no class gate, no CAR [BAT72 p.102 ; COURS p.14]
            port = Port(client, name, kind, None, "PD", len(self.ports))
            self.ports[name] = port
            return port
        cls = self.classes[kind]
        circuits = [c["id"] for c in self.circuits if cls in c["classes"]]
        n = self._per_class.get(cls, 0)
        self._per_class[cls] = n + 1
        port = Port(client, name, kind, cls, circuits[n % len(circuits)], len(self.ports))
        self.racs.allocate(name, racs_for(kind))
        self.ports[name] = port
        return port

    # -- requests -----------------------------------------------------------------------------

    def request(
        self,
        port: Port,
        rac: int,
        direction: str,
        *,
        nature: str = QUANTITY,
        value: int | None = None,
        step: int = 1,
        rank_as: str | None = None,
        address: int | None = None,
    ) -> Request:
        if direction not in CHANNEL or nature not in self.nature_order or step not in (1, -1):
            raise ValueError(f"invalid request {direction} {nature} {step}")
        if direction == WRITE and value is None:
            raise ValueError("a write request carries the catena to write")
        if (port.kind == PD) != (address is not None):
            raise ValueError("the PD gives an explicit address; elements use their CARs")
        req = Request(
            port, rac, direction, nature, value, step, rank_as, address, self.engine.now, self._seq
        )
        self._seq += 1
        self.pending.append(req)
        self._schedule()
        return req

    def _next_boundary(self) -> int:
        now = self.engine.now
        grid = -(-now // self.cycle) * self.cycle  # next multiple of the cycle (U-42)
        return max(grid, self._last_cycle + self.cycle)

    def _schedule(self) -> None:
        if self._cycle_event is None and self.pending:
            self._cycle_event = self.engine.at(self._next_boundary(), self._run_cycle, "DD cycle")

    # -- one memory cycle -----------------------------------------------------------------------

    def _rank(self, req: Request) -> tuple:
        kind = req.rank_as or req.port.kind
        nature_rank = self.order.index(kind) if kind in self.order else len(self.order)
        return (nature_rank, self.nature_order.index(req.nature), req.port.order, req.seq)

    def _choose(self, candidates: list[Request]) -> Request:
        best = min(candidates, key=self._rank)
        circuit = best.port.circuit
        if circuit not in self.multiplexed:
            return best
        # the multiplexer serves its elements in turn behind one gate (U-43)
        waiting = sorted({r.port.order for r in candidates if r.port.circuit == circuit})
        last = self._mux_last.get(circuit, -1)
        turn = next((o for o in waiting if o > last), waiting[0])
        self._mux_last[circuit] = turn
        return min((r for r in candidates if r.port.order == turn), key=self._rank)

    def _run_cycle(self) -> None:
        self._cycle_event = None
        self._last_cycle = self.engine.now
        if self.behavior["dd_channels_same_cycle"]:
            chosen = []
            for direction in (READ, WRITE):
                pool = [r for r in self.pending if r.direction == direction]
                if pool:
                    chosen.append(self._choose(pool))
        else:
            chosen = [self._choose(self.pending)]
        for req in chosen:
            self.pending.remove(req)
        waiting = [r.port.name for r in sorted(self.pending, key=self._rank)]
        for req in chosen:
            self._transfer(req, waiting)
        self.stats.busy_cycles += 1
        if self.mode == "diagnostic":
            self._watch_starvation()
        self._schedule()

    def _transfer(self, req: Request, waiting: list[str]) -> None:
        port, now = req.port, self.engine.now
        address = req.address if req.address is not None else self.racs.get(port.name, req.rac)
        waited = now - req.raised
        try:
            if req.direction == READ:
                value = self.memory.read(address)
            else:
                value = req.value
                self.memory.write(address, value)
        except (KeyError_, SelectionError) as exc:
            reason = "key" if isinstance(exc, KeyError_) else "selection"
            self.stats.incidents += 1
            self.engine.record(
                "DD", "incident", element=port.name, rac=req.rac, address=address, reason=reason
            )
            self.engine.after(self.cycle, lambda: port.client.transfer_incident(req, reason))
            return
        if req.address is None:
            self.racs.advance(port.name, req.rac, req.step)
        port.buffer = value
        s = self.stats
        s.served[port.name] = s.served.get(port.name, 0) + 1
        s.wait_total[port.name] = s.wait_total.get(port.name, 0) + waited
        s.wait_max[port.name] = max(s.wait_max.get(port.name, 0), waited)
        gate = (port.circuit, CHANNEL[req.direction])
        s.gates[gate] = s.gates.get(gate, 0) + 1
        self.engine.record(
            "DD",
            "transfer",
            element=port.name,
            kind=port.kind,
            nature=req.nature,
            rac=req.rac,
            address=address,
            next=address if req.address is not None else self.racs.get(port.name, req.rac),
            channel=CHANNEL[req.direction],
            gate=port.circuit,
            value=value,
            waited=waited,
            waiting=tuple(waiting),
        )
        # the buffer register is filled (or emptied) in the course of the cycle [B61 p.23]
        self.engine.after(self.cycle, lambda: port.client.transfer_done(req, value))

    def _watch_starvation(self) -> None:
        limit = self.behavior["dd_starvation_cycles"] * self.cycle
        for req in self.pending:
            if req.seq not in self._warned and self.engine.now - req.raised > limit:
                self._warned.add(req.seq)
                self.stats.warnings += 1
                self.engine.record(
                    "DD", "starvation", element=req.port.name, waited=self.engine.now - req.raised
                )

    # -- measures -----------------------------------------------------------------------------

    def occupancy(self, duration: int) -> float:
        """Share of the memory cycles used for transfers over ``duration`` µs."""
        return self.stats.busy_cycles / (duration / self.cycle) if duration else 0.0
