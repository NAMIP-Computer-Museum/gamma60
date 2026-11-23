"""The machine (J3-J5): engine, store, Data Distributor, Program Distributor and the elements.

The elements come from a configuration (``data/configs/``, default ``max``): ARIT, LOGI, COMP,
the drums and the uniselectors with their tape drives (wired as on B61 p.54). Element numbers:
``topology.yaml`` (U-44).

A code B program is assembled into code A, loaded at its origin (default 256, after the table
of the recall chain registers, U-30) and started by the PD as one of its own sequences (an
emulator convention until the GGZ loader of J7). The run ends when no event is left: ``halted``
if every element is idle and every chain empty, ``blocked`` otherwise, ``incident`` after an
incident. In diagnostic mode, a join that never fired (its blank catena still counts arrivals)
makes the run ``blocked``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from gamma60 import codeb, data
from gamma60.catena import bits
from gamma60.data_distributor import DataDistributor
from gamma60.elements.base import IDLE
from gamma60.elements.comparator import Comparator
from gamma60.elements.drum import Drum
from gamma60.elements.processing import Arithmetic, Logical
from gamma60.elements.tape import TapeDrive, Uniselector, UniselectorUnit
from gamma60.engine import Engine
from gamma60.memory import Memory
from gamma60.number import Number
from gamma60.program_distributor import ProgramDistributor
from gamma60.toolchain.assembler import Image, assemble

SINGLE_ELEMENTS = {"arithmetic": Arithmetic, "logical": Logical, "comparator": Comparator}
DEFAULT_CONFIG = "max"


def uniselector_wiring(config: str, unit: int) -> list[int]:
    """Drives wired to uniselector ``unit`` (1-10): two groups of five [B61 p.54 ; COURS p.144]."""
    table = (
        data.load(f"configs/{config}").get("uniselector_wiring")
        or data.load(f"configs/{DEFAULT_CONFIG}")["uniselector_wiring"]
    )
    group, index = divmod(unit - 1, 5)
    low, high = table[f"U{index + 1}"]
    return list(range(low + 24 * group, high + 24 * group + 1))


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
    config: str = DEFAULT_CONFIG
    engine: Engine = field(init=False)
    memory: Memory = field(init=False)
    dd: DataDistributor = field(init=False)
    dp: ProgramDistributor = field(init=False)
    elements: dict[str, object] = field(init=False, default_factory=dict)
    tape_drives: dict[int, TapeDrive] = field(init=False, default_factory=dict)
    status: str = field(init=False, default="running")
    message: str = field(init=False, default="")

    def __post_init__(self) -> None:
        self.engine = Engine()
        cfg = data.get_config(self.config)
        p = self.profile  # blocks of the configuration, within the bounds of the profile
        blocks = min(max(cfg.memory_blocks, p.memory_blocks_min), p.memory_blocks_max)
        self.memory = Memory(p, blocks)
        self.dd = DataDistributor(
            self.engine, self.memory, self.profile, mode=self.mode, classes=cfg.classes
        )
        numbers = data.resolve(data.load("topology")["element_numbers"])
        units = data.resolve(data.load("topology")["unit_numbers"])
        for kind, cls in SINGLE_ELEMENTS.items():
            if cfg.elements.get(kind, 0):
                self.elements[kind] = cls(self, number=numbers[kind])
        for k in range(1, cfg.elements.get("drum", 0) + 1):
            number = units["drum"]["first"] + units["drum"]["step"] * (k - 1)
            self.elements[f"drum{k}"] = Drum(self, f"DRUM{k}", number, k)
        for n in range(1, cfg.elements.get("tape_units", 0) + 1):
            self.tape_drives[n] = TapeDrive(n)
        for k in range(
            1, cfg.elements.get("uniselector", 0) + 1
        ):  # two elements each [COURS p.147]
            shared = UniselectorUnit(k, set(uniselector_wiring(self.config, k)))
            for n in (2 * k - 1, 2 * k):
                number = units["uniselector"]["first"] + units["uniselector"]["step"] * (n - 1)
                self.elements[f"uniselector{n}"] = Uniselector(self, f"MATA{n}", number, n, shared)
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
            if active or self.dp.busy or self.dp.pd_b:
                self.status = "blocked"
                self.message = f"no event left, still active: {', '.join(active) or 'PD'}"
            else:
                self.status = "halted"
            if self.mode == "diagnostic":
                self._check_joins()
        return Result(self.status, self.message, self, self.image)

    def _check_joins(self) -> None:
        """Diagnostic: a join whose blank catena still counts arrivals never fired."""
        for address, m in sorted(self.image.joins.items()):
            count = bits(self.memory.raw(address + 1).value, 19, 18)
            if count:
                line = self.image.line_at(address)
                where = f"line {line.source_line}" if line else f"address {address:05d}"
                self.status = "blocked"
                self.message = f"join never reached at {where}: {count} of {m + 1} arrivals"
                self.engine.record("machine", "warning", text=self.message)


def build(
    text: str,
    profile: str | None = None,
    mode: str = "faithful",
    observer=None,
    config: str = DEFAULT_CONFIG,
) -> Machine:
    program = codeb.parse(text)
    prof = data.get_profile(profile or program.profile)
    return Machine(assemble(program, prof), prof, mode, observer, config)


def run_text(text: str, profile: str | None = None, **kwargs) -> Result:
    return build(text, profile, **kwargs).run()


def run_file(path: str | Path, profile: str | None = None, **kwargs) -> Result:
    return run_text(Path(path).read_text(encoding="utf-8"), profile, **kwargs)
