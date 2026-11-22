"""The J3 machine: engine, store, Data Distributor, Program Distributor, ARIT and LOGI.

A code B program is assembled into code A, loaded at its origin (default 0) and started by
the PD as one of its own sequences (an emulator convention until the GGZ loader of J7). The
run ends when no event is left: ``halted`` if every element is idle, ``blocked`` otherwise,
``incident`` after an incident.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from gamma60 import codeb, data
from gamma60.data_distributor import DataDistributor
from gamma60.elements.base import IDLE
from gamma60.elements.processing import Arithmetic, Logical
from gamma60.engine import Engine
from gamma60.memory import Memory
from gamma60.number import Number
from gamma60.program_distributor import ProgramDistributor
from gamma60.toolchain.assembler import Image, assemble

ELEMENT_CLASSES = {"arithmetic": Arithmetic, "logical": Logical}


@dataclass
class Result:
    status: str  # halted | blocked | incident
    message: str
    machine: Machine
    image: Image

    @property
    def memory(self) -> Memory:
        return self.machine.memory

    def number(self, label: str) -> Number:
        a = self.image.labels[label]
        return Number.from_catenae(self.memory.read(a), self.memory.read(a + 1))


@dataclass
class Machine:
    image: Image
    profile: data.Profile
    mode: str = "faithful"
    observer: object | None = None  # debug observer: called after each instruction read
    engine: Engine = field(init=False)
    memory: Memory = field(init=False)
    dd: DataDistributor = field(init=False)
    dp: ProgramDistributor = field(init=False)
    elements: dict[str, object] = field(init=False, default_factory=dict)
    status: str = field(init=False, default="running")
    message: str = field(init=False, default="")

    def __post_init__(self) -> None:
        self.engine = Engine()
        self.memory = Memory(self.profile, self.profile.memory_blocks_max)
        self.dd = DataDistributor(self.engine, self.memory, self.profile, mode=self.mode)
        numbers = data.resolve(data.load("topology")["element_numbers"])
        for kind, cls in ELEMENT_CLASSES.items():
            self.elements[kind] = cls(self, number=numbers[kind])
        self.dp = ProgramDistributor(self)
        for address, value in self.image.words.items():
            self.memory.write(address, value)

    @property
    def stopped(self) -> bool:
        return self.status != "running"

    def element_by_number(self, number: int):
        return next((e for e in self.elements.values() if e.number == number), None)

    def observe(self, dp: ProgramDistributor) -> None:
        if self.observer is not None:
            self.observer.instruction(self, dp)

    def element_incident(self, element, message: str) -> None:
        line = self.image.line_at(element.directive_address)
        where = f"line {line.source_line}: " if line else ""
        self.incident(f"{where}{element.name}: {message}")

    def incident(self, message: str) -> None:
        self.status, self.message = "incident", message
        self.engine.record("machine", "incident", text=message)
        self.engine.stop()

    def run(self, max_events: int = 5_000_000) -> Result:
        self.dp.start(self.image.entry)
        self.engine.run(max_events=max_events)
        if self.status == "running":
            active = [e.name for e in self.elements.values() if e.state != IDLE]
            if active or self.dp.busy:
                self.status = "blocked"
                self.message = f"no event left, still active: {', '.join(active) or 'PD'}"
            else:
                self.status = "halted"
        return Result(self.status, self.message, self, self.image)


def build(text: str, profile: str | None = None, mode: str = "faithful", observer=None) -> Machine:
    program = codeb.parse(text)
    prof = data.get_profile(profile or program.profile)
    return Machine(assemble(program, prof), prof, mode, observer)


def run_text(text: str, profile: str | None = None, **kwargs) -> Result:
    return build(text, profile, **kwargs).run()


def run_file(path: str | Path, profile: str | None = None, **kwargs) -> Result:
    return run_text(Path(path).read_text(encoding="utf-8"), profile, **kwargs)
