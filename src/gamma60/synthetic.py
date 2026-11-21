"""Synthetic elements: programmable clients of the Data Distributor (J2 tests and scenarios).

They stand for real elements until J3-J8 and request transfers at a chosen rhythm:

- ``continuous``: a new request as soon as the previous transfer is done (ARIT fetching its
  operands, a block copy);
- ``periodic``: one request every ``period_us`` (a drum or a tape drive, whose medium moves on
  its own). The catena must be transferred before the next one comes under the head: a late
  transfer counts as a *miss* (for a drum, a lost revolution [B61 p.24]).

A scenario is a YAML file (``tests/scenarios/*.yaml``) listing the clients; ``load_scenario``
builds the engine, the store, the DD and the clients from it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from gamma60 import data
from gamma60.data_distributor import PD, QUANTITY, READ, WRITE, DataDistributor, Port, Request
from gamma60.engine import Engine
from gamma60.memory import Memory


@dataclass
class Synthetic:
    name: str
    kind: str
    dd: DataDistributor
    pattern: str = "continuous"
    direction: str = READ
    count: int = 1
    period_us: int | None = None
    start_us: int = 0
    rac: int = 0
    address: int = 0
    step: int = 1
    nature: str = QUANTITY
    rank_as: str | None = None
    port: Port = field(init=False)
    issued: int = field(init=False, default=0)
    done: list[tuple[int, int]] = field(init=False, default_factory=list)  # (time, value)
    misses: int = field(init=False, default=0)
    incidents: list[str] = field(init=False, default_factory=list)
    _deadline: dict[int, int] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        if self.pattern not in ("continuous", "periodic"):
            raise ValueError(f"unknown pattern {self.pattern!r}")
        if self.pattern == "periodic" and not self.period_us:
            raise ValueError("a periodic client needs period_us")
        self.port = self.dd.attach(self, self.kind, self.name)
        if self.kind != PD:
            self.dd.racs.set(self.name, self.rac, self.address)
        engine = self.dd.engine
        if self.pattern == "continuous":
            engine.at(self.start_us, self._issue, f"{self.name} start")
        else:
            for k in range(self.count):
                engine.at(self.start_us + k * self.period_us, self._issue, f"{self.name} {k}")

    def _issue(self) -> None:
        if self.issued >= self.count:
            return
        value = None
        if self.direction == WRITE:
            value = (self.issued + 1) & 0xFFFFFF  # catena k + 1, easy to recognise in the store
        req = self.dd.request(
            self.port,
            self.rac,
            self.direction,
            nature=self.nature,
            value=value,
            step=self.step,
            rank_as=self.rank_as,
            address=self.address + self.issued if self.kind == PD else None,  # RAPA ← RAPP
        )
        if self.pattern == "periodic":
            deadline = self.dd.engine.now + self.period_us
            self._deadline[req.seq] = deadline
            # checked just after the deadline: not transferred by then = a miss
            self.dd.engine.at(deadline + 1, lambda seq=req.seq: self._check(seq), "deadline")
        self.issued += 1

    def _check(self, seq: int) -> None:
        if self._deadline.pop(seq, None) is not None:
            self.misses += 1

    def transfer_done(self, request: Request, value: int) -> None:
        now = self.dd.engine.now
        self.done.append((now, value))
        self._deadline.pop(request.seq, None)  # done in time (a late one was already counted)
        if self.pattern == "continuous":
            self._issue()

    def transfer_incident(self, request: Request, reason: str) -> None:
        self.incidents.append(reason)


@dataclass
class Scenario:
    title: str
    engine: Engine
    memory: Memory
    dd: DataDistributor
    clients: list[Synthetic]
    until_us: int | None

    def run(self) -> int:
        """Run over the window [0, until_us[ (the whole scenario if until_us is None)."""
        return self.engine.run(until=None if self.until_us is None else self.until_us - 1)


def build(spec: dict[str, Any], profile: str | None = None, mode: str = "faithful") -> Scenario:
    """Build a scenario from its description (the content of a scenario YAML file)."""
    prof = data.get_profile(profile or spec.get("profile"))
    engine = Engine()
    memory = Memory(prof, spec.get("memory_blocks", prof.memory_blocks_max))
    dd = DataDistributor(
        engine,
        memory,
        prof,
        order=spec.get("dtd_order"),
        behavior=spec.get("behavior"),
        mode=mode,
    )
    clients = []
    for c in spec["clients"]:
        params = dict(c)
        clients.append(Synthetic(dd=dd, **params))
    return Scenario(spec.get("title", ""), engine, memory, dd, clients, spec.get("until_us"))


def load_scenario(path: str | Path, profile: str | None = None, mode: str = "faithful") -> Scenario:
    spec = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return build(spec, profile, mode)
