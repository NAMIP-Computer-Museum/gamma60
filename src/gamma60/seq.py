"""Provisional sequential interpreter of code B (milestone J1).

It runs a program written in code B (``.g60b``, language ``fr`` or ``en``) one sequence at a
time, without time, Program Distributor or code A: those arrive at J2-J3. It supports cuts on
ARIT and LOGI, address instructions, branches, ``SIMU`` / join / ``STOP`` (executed in a
deterministic sequential order: the named branch first, as in COURS p.36-37) and the ARIT and
LOGI directives. Anything else raises :class:`Unsupported`.

Parsing of code B is in :mod:`gamma60.codeb` (shared with the assembler).
"""

from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

from gamma60 import data
from gamma60.catena import MASK15, bits, set_bits
from gamma60.codeb import DATA, Line, Program, ProgramError, Syntax, binary_value, parse, split_af
from gamma60.core.arit import ArithmeticUnit, Incident, fit
from gamma60.core.logi import LogicalUnit
from gamma60.memory import Memory
from gamma60.number import Number

SUPPORTED_ELEMENTS = {"arithmetic", "logical"}
NUMBERED_SPECIAL = {"virtual_engage", "virtual_release", "fork"}


class Unsupported(NotImplementedError):
    """Valid code B that the J1 interpreter does not execute yet."""


@dataclass
class Result:
    status: str  # "halted" or "incident"
    trace: list[tuple[int, int, str, str]]
    memory: Memory
    program: Program
    units: dict[str, object]
    message: str = ""

    def number(self, label: str) -> Number:
        a = self.program.labels[label]
        return Number.from_catenae(self.memory.read(a), self.memory.read(a + 1))


@dataclass
class Interpreter:
    program: Program
    profile: data.Profile
    max_steps: int = 100_000
    observer: object | None = None  # debug.RegisterTrace / debug.Stepper: before() and after()
    memory: Memory = field(init=False)
    racs: dict[str, list[int]] = field(init=False, default_factory=dict)
    units: dict[str, object] = field(init=False, default_factory=dict)
    register_a: int = field(init=False, default=0)
    chain: deque[int] = field(init=False, default_factory=deque)
    trace: list[tuple[int, int, str, str]] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self.memory = Memory(self.profile)
        lang = self.program.language
        self.cuts = data.cut_index(lang)
        self.address_ops = data.address_index(lang)
        self.central = data.central_index(lang)
        self.syntax = Syntax(lang)
        for line in self.program.lines:
            if line.to == "NUM":
                value = Fraction(line.args[0].replace(",", "."))
                p, _ = fit(value, None)  # NUM: normalised form (assembler convention)
                first, second = p.to_catenae()
                self.memory.write(line.address, first)
                self.memory.write(line.address + 1, second)
            elif line.to == "BIN":
                self.memory.write(line.address, binary_value(line.args[0]))

    # -- operands ----------------------------------------------------------------------------

    def resolve_x(self, token: str, af: str) -> int:
        if token in self.program.labels:
            x = self.program.labels[token]
        elif re.fullmatch(r"\d+", token):
            x = int(token)
            if "M" in af:
                x += self.program.end  # working memories follow the program [COURS p.47-49]
        else:
            raise ProgramError(f"unknown label or value {token!r}")
        if "S" in af:
            x = self.memory.read(x & MASK15) & MASK15
        return x & MASK15

    def _rac_io(self, element: str, width: int):
        racs = self.racs.setdefault(element, [0, 0, 0, 0])

        def load(d):
            _, i, progress = d
            start = racs[i]
            values = [self.memory.read((start + j) & MASK15) for j in range(width)]
            racs[i] = (start + width) & MASK15 if progress else start
            return values

        def store(d, values):
            _, i, progress = d
            start = racs[i]
            for j, v in enumerate(values):
                self.memory.write((start + j) & MASK15, v)
            racs[i] = (start + len(values)) & MASK15 if progress else start

        return load, store

    # -- execution -----------------------------------------------------------------------

    def run(self, entry: str | int | None = None) -> Result:
        if entry is None:
            pc = next(ln.address for ln in self.program.lines if ln.to not in DATA)
        else:
            pc = self.program.labels[entry] if isinstance(entry, str) else entry
        element: str | None = None
        status, message = "halted", ""
        for step in range(self.max_steps):
            line = self.program.at(pc)
            self.trace.append((step, pc, element or "-", " ".join([line.to, *line.args])))
            next_pc = pc + line.size
            if self.observer is not None:
                self.observer.before(self, step, line, element)
            try:
                outcome = self._step(line, element)
            except Incident as exc:
                status, message = "incident", f"line {line.source_line}: {exc}"
                if self.observer is not None:
                    self.observer.after(self, step, line, element, message)
                break
            if self.observer is not None:
                self.observer.after(self, step, line, element, None)
            kind = outcome[0]
            if kind == "next":
                pc = next_pc
            elif kind == "goto":
                pc = outcome[1]
            elif kind == "cut":
                element, pc = outcome[1], outcome[2]
            elif kind == "end":
                if not self.chain:
                    break
                pc, element = self.chain.popleft(), None
            elif kind == "fork":
                self.chain.append(outcome[2])
                element, pc = None, outcome[1]
        else:
            raise ProgramError(f"no STOP after {self.max_steps} steps")
        return Result(status, self.trace, self.memory, self.program, self.units, message)

    def _step(self, line: Line, element: str | None):
        to = line.to
        if to == "VIERGE":
            return ("next",)  # a blank catena executes as a "never" branch [COURS p.42]
        if to in DATA:
            raise ProgramError(f"line {line.source_line}: execution reached data")
        if re.fullmatch(r"\d{2}", to):
            args, af = split_af(line.args, 1)
            target = self.resolve_x(args[0], af)
            cond = int(to)
            taken = cond == 31 or (1 <= cond <= 24 and bits(self.register_a, cond, cond))
            return ("goto", target) if taken else ("next",)
        if to in self.cuts:
            return self._cut(line, self.cuts[to])
        if to in self.address_ops:
            return self._address(line, self.address_ops[to], element)
        if to in self.central:
            raise Unsupported(f"line {line.source_line}: central directive {to} (milestone J3)")
        if element is None:
            raise ProgramError(f"line {line.source_line}: {to} before any cut")
        directive = data.element_index(element, self.program.language).get(to)
        if directive is None:
            raise ProgramError(f"line {line.source_line}: {to} unknown for {element}")
        if element == "arithmetic":
            self._arit(line, directive)
        else:
            self._logi(line, directive)
        return ("next",)

    def _cut(self, line: Line, cut: str):
        if cut == "end_of_sequence":
            return ("end",)
        blank_address = line.address + 1
        blank = self.program.at(blank_address)
        if blank.to != "VIERGE":
            raise ProgramError(f"line {line.source_line}: a cut must be followed by VIERGE")
        if cut == "fork":
            args, af = split_af(line.args, 1)
            return ("fork", self.resolve_x(args[0], af), blank_address + 1)
        if cut in NUMBERED_SPECIAL:
            raise Unsupported(f"line {line.source_line}: {line.to} (milestone J4)")
        if cut not in SUPPORTED_ELEMENTS:
            raise Unsupported(f"line {line.source_line}: element {cut} (milestones J5-J8)")
        m = int(line.args[0]) if line.args else 0
        if blank.args:  # COURS: join count in the X of the blank catena [COURS p.52]
            m = max(m, int(blank.args[0]))
        if m:
            counter = bits(self.memory.read(blank_address), 19, 18)
            if counter < m:  # earlier arrivals end here (join)
                self.memory.write(
                    blank_address, set_bits(self.memory.read(blank_address), 19, 18, counter + 1)
                )
                return ("end",)
            self.memory.write(blank_address, set_bits(self.memory.read(blank_address), 19, 18, 0))
        return ("cut", cut, blank_address + 1)

    def _address(self, line: Line, op: str, element: str | None):
        if element is None:
            raise ProgramError(f"line {line.source_line}: address instruction before any cut")
        args, af = split_af(line.args, 2)
        car, x = int(args[0]), self.resolve_x(args[1], af)
        racs = self.racs.setdefault(element, [0, 0, 0, 0])
        if op == "load":
            racs[car] = x
        elif op == "place":
            self.memory.write(x, racs[car])
        elif op == "add":
            racs[car] = (racs[car] + x) & MASK15
        elif op == "subtract":
            racs[car] = (racs[car] - x) & MASK15
        return ("next",)

    def _arit(self, line: Line, op: str) -> None:
        f = self.syntax.arit(line.args, f"line {line.source_line}: ")
        load_raw, store_raw = self._rac_io("arithmetic", 2)

        def load(d):
            return Number.from_catenae(*load_raw(d))

        def store(d, numbers):
            store_raw(d, [c for n in numbers for c in n.to_catenae()])

        unit = self.units.setdefault("arithmetic", ArithmeticUnit())
        try:
            unit.execute(
                op,
                mode=f.mode,
                double=f.double,
                point=f.point,
                o1=f.o1,
                o2=f.o2,
                r=f.r,
                load=load,
                store=store,
            )
        finally:
            self.register_a = unit.qualitative

    def _logi(self, line: Line, op: str) -> None:
        f = self.syntax.logi(line.args, f"line {line.source_line}: ")
        load_raw, store_raw = self._rac_io("logical", 1)
        unit = self.units.setdefault("logical", LogicalUnit())
        try:
            unit.execute(
                op,
                length=f.length,
                r=f.r,
                load=lambda d: load_raw(d)[0],
                store=lambda d, value: store_raw(d, [value]),
            )
        finally:
            self.register_a = unit.qualitative


def run_file(path: str | Path, profile: str | None = None, **kwargs) -> Result:
    program = parse(Path(path).read_text(encoding="utf-8"))
    chosen = data.get_profile(profile or program.profile)
    return Interpreter(program, chosen, **kwargs).run()


def run_text(text: str, profile: str | None = None, **kwargs) -> Result:
    program = parse(text)
    return Interpreter(program, data.get_profile(profile or program.profile), **kwargs).run()


__all__ = ["Interpreter", "Line", "Program", "ProgramError", "Result", "Unsupported", "parse"]
