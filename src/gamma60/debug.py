"""Traces and step-by-step debugger (milestone J2, extended at each milestone).

Register names come from ``data/registers.yaml`` (field ``display``), in the language chosen
with ``--names en|fr``: UPPER CASE = name attested in that language, lower case = initials
proposed by the emulator (not validated). The debugger only *reads* the state of the
simulation: a run gives the same trace with or without it.

J2 step 1 covers the sequential interpreter of J1 (``seq.py``): register A, the registers and
CARs of ARIT and LOGI, their qualitative catena. The Data Distributor, the Program
Distributor and the other elements add their registers in later steps.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TextIO

from gamma60 import data
from gamma60.catena import MASK15

#: element kind → register ids shown for it (besides its CARs and qualitative catena)
ELEMENT_REGISTERS = {
    "arithmetic": ("arit_p", "arit_s", "arit_o"),
    "logical": ("logi_k", "logi_l"),
}


#: messages of the debugger in each language of the emulator
MESSAGES = {
    "en": {
        "help": (
            "commands: <Enter>/s step   r registers   m <address|label> [n] memory\n"
            "          b <address|label> breakpoint   d <address|label> delete it   c continue\n"
            "          l legend   q quit   h help"
        ),
        "next": "next:",
        "break": "break at",
        "registers": "registers",
        "emulator": "emulator label",
        "attested": "attested name",
        "unknown": "unknown address or label",
        "waiting": "waiting",
        "incident": "incident",
        "starvation": "starvation: waiting for",
        "served": "served",
        "wait": "wait mean / max",
        "misses": "misses",
        "occupancy": "store occupancy",
        "share": "share of cycles",
        "quantity": "qty",
        "instruction": "instr",
        "gates": "gates",
    },
    "fr": {
        "help": (
            "commandes : <Entrée>/s pas   r registres   m <adresse|étiquette> [n] mémoire\n"
            "            b <adresse|étiquette> point d'arrêt   d <adresse|étiquette> l'enlever\n"
            "            c continuer   l légende   q quitter   h aide"
        ),
        "next": "suivant :",
        "break": "arrêt en",
        "registers": "registres",
        "emulator": "libellé de l'émulateur",
        "attested": "nom attesté",
        "unknown": "adresse ou étiquette inconnue",
        "waiting": "en attente",
        "incident": "incident",
        "starvation": "famine : attend depuis",
        "served": "servis",
        "wait": "attente moyenne / max",
        "misses": "ratés",
        "occupancy": "occupation de la mémoire",
        "share": "part des cycles",
        "quantity": "quant.",
        "instruction": "instr.",
        "gates": "vannes",
    },
}


class Quit(Exception):
    """The user left the debugger."""


# --- names -----------------------------------------------------------------------------------


@dataclass
class Names:
    """Display names of registers and elements in one language."""

    language: str
    registers: dict[str, dict] = field(init=False)
    elements: dict[str, str] = field(init=False)

    def __post_init__(self) -> None:
        if self.language not in data.languages():
            raise ValueError(f"unknown language {self.language!r}")
        self.registers = {r["id"]: r for r in data.load("registers")["registers"]}
        self.elements = {kind: mnem for mnem, kind in data.cut_index(self.language).items()}

    def label(self, ident: str, index: int | None = None) -> str:
        """Display label of a register, indexed for a register with several copies."""
        shown = self.registers[ident]["display"][self.language]
        if isinstance(shown, list):
            return shown[index or 0]
        return shown if index is None else f"{shown}{index}"

    def say(self, key: str) -> str:
        return MESSAGES[self.language][key]

    def element(self, kind: str) -> str:
        return self.elements.get(kind, kind)

    def legend(self, idents: Iterable[str]) -> list[str]:
        """One line per register: label, expanded name, period name(s), source."""
        other = "fr" if self.language == "en" else "en"
        lines = []
        for ident in idents:
            reg = self.registers[ident]
            shown = reg["display"][self.language]
            label = ", ".join(shown) if isinstance(shown, list) else shown
            long = reg["long"][self.language].replace(" (emulator)", "")
            origin = self.say("emulator") if label.islower() else self.say("attested")
            period = reg["name"][other]
            also = f"; {other}: {period}" if period else ""
            lines.append(f"  {label:<8} {long} ({origin}{also}) [{reg['source']}]")
        return lines


# --- state snapshot ---------------------------------------------------------------------------


def _bits24(value: int) -> str:
    text = f"{value:024b}"
    return " ".join(text[i : i + 6] for i in range(0, 24, 6))


def _positions(value: int) -> str:
    on = [str(i + 1) for i in range(24) if value >> i & 1]
    return "{" + ",".join(on) + "}" if on else "{}"


def _number(n) -> str:
    try:
        return f"{n} (= {float(n.value):g})"
    except Exception:  # noqa: BLE001 - a register may hold anything
        return str(n)


def snapshot(interp, names: Names) -> dict[str, dict[str, str]]:
    """Registers of the interpreter, grouped by unit: {unit: {label: value}} (ordered)."""
    state: dict[str, dict[str, str]] = {"CU": {names.label("a"): _positions(interp.register_a)}}
    for kind in ("arithmetic", "logical"):
        unit = interp.units.get(kind)
        racs = interp.racs.get(kind)
        if unit is None and racs is None:
            continue
        regs: dict[str, str] = {}
        if unit is not None:
            for ident in ELEMENT_REGISTERS[kind]:
                attr = ident.split("_", 1)[1]
                value = getattr(unit, attr)
                regs[names.label(ident)] = (
                    _number(value) if kind == "arithmetic" else _bits24(value)
                )
            regs[names.label("qualitative")] = _positions(unit.qualitative)
        for i, address in enumerate(racs or []):
            regs[names.label("rac", i)] = f"{address:05d}"
        state[names.element(kind)] = regs
    return state


def changes(before: dict, after: dict) -> set[tuple[str, str]]:
    return {
        (unit, label)
        for unit, regs in after.items()
        for label, value in regs.items()
        if before.get(unit, {}).get(label) != value
    }


WIDTH = 96


def format_state(state: dict, changed: set | None = None, units: Iterable[str] | None = None):
    """Lines ``UNIT  label value  label* value`` (``*`` = changed by the last step)."""
    changed = changed or set()
    lines = []
    for unit in units if units is not None else state:
        if unit not in state:
            continue
        cells = [
            f"{label}{'*' if (unit, label) in changed else ''} {value}"
            for label, value in state[unit].items()
        ]
        line = f"      {unit:<5} "
        for cell in cells:
            if len(line) + len(cell) > WIDTH and line.strip() != unit:
                lines.append(line.rstrip())
                line = " " * 12
            line += cell + "   "
        lines.append(line.rstrip())
    return lines


def legend_ids(state_units: Iterable[str], names: Names) -> list[str]:
    ids = ["a"]
    kinds = {names.element(k): k for k in ELEMENT_REGISTERS}
    for unit in state_units:
        if unit in kinds:
            ids += [*ELEMENT_REGISTERS[kinds[unit]], "qualitative", "rac"]
    return list(dict.fromkeys(ids))


# --- observers (hooks of seq.Interpreter) -------------------------------------------------------


def _instruction(step: int, line, element: str | None, names: Names) -> str:
    unit = names.element(element) if element else "-"
    return f"{step:5d}  {line.address:05d}  {unit:<5}  {' '.join([line.to, *line.args])}"


@dataclass
class RegisterTrace:
    """``--trace=regs``: each instruction, then the registers of the units it changed."""

    names: Names
    out: TextIO | None = None  # None: sys.stdout at run time
    _before: dict = field(default_factory=dict, init=False)
    _legend_done: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.out = self.out or sys.stdout

    def before(self, interp, step: int, line, element: str | None) -> None:
        self._before = snapshot(interp, self.names)

    def after(self, interp, step: int, line, element: str | None, error: str | None) -> None:
        state = snapshot(interp, self.names)
        changed = changes(self._before, state)
        print(_instruction(step, line, element, self.names), file=self.out)
        touched = [u for u in state if any(c[0] == u for c in changed)]
        for text in format_state(state, changed, touched):
            print(text, file=self.out)
        if error:
            print(f"      ! {error}", file=self.out)

    def header(self) -> None:
        print(f"{self.names.say('registers')} ({self.names.language}) :", file=self.out)
        everything = ["a", "qualitative", "rac", *ELEMENT_REGISTERS["arithmetic"]]
        everything += ELEMENT_REGISTERS["logical"]
        for text in self.names.legend(everything):
            print(text, file=self.out)


@dataclass
class Stepper:
    """``--step``: interactive step-by-step debugger, reading commands from ``inp``."""

    names: Names
    inp: TextIO | None = None  # None: sys.stdin / sys.stdout at run time
    out: TextIO | None = None
    breakpoints: set[int] = field(default_factory=set)
    running: bool = False
    _before: dict = field(default_factory=dict, init=False)
    _interp: object = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.inp = self.inp or sys.stdin
        self.out = self.out or sys.stdout

    def _say(self, text: str) -> None:
        print(text, file=self.out)

    def _address(self, token: str) -> int:
        labels = self._interp.program.labels
        if token in labels:
            return labels[token]
        if re.fullmatch(r"\d+", token):
            return int(token) & MASK15
        raise ValueError(f"{self.names.say('unknown')} {token!r}")

    def _memory(self, start: int, count: int) -> None:
        by_address = {a: name for name, a in self._interp.program.labels.items()}
        for address in range(start, start + count):
            cat = self._interp.memory.raw(address)
            label = by_address.get(address, "")
            self._say(f"      {address:05d}  {label:<8} {cat.value:06X}  key {cat.key}")

    def before(self, interp, step: int, line, element: str | None) -> None:
        self._interp = interp
        self._before = snapshot(interp, self.names)
        if self.running and line.address not in self.breakpoints:
            return
        if self.running:
            self._say(f"{self.names.say('break')} {line.address:05d}")
        self.running = False
        self._say(self.names.say("next") + _instruction(step, line, element, self.names)[5:])
        self._prompt(interp)

    def after(self, interp, step: int, line, element: str | None, error: str | None) -> None:
        if self.running:
            return
        state = snapshot(interp, self.names)
        changed = changes(self._before, state)
        touched = [u for u in state if any(c[0] == u for c in changed)]
        for text in format_state(state, changed, touched):
            self._say(text)
        if error:
            self._say(f"      ! {error}")

    def _prompt(self, interp) -> None:
        while True:
            self.out.write("(g60) ")
            self.out.flush()
            raw = self.inp.readline()
            if raw == "":  # end of input: behave as "continue"
                self.running = True
                return
            words = raw.split()
            cmd = words[0] if words else "s"
            try:
                if cmd == "s":
                    return
                if cmd == "c":
                    self.running = True
                    return
                if cmd == "q":
                    raise Quit
                if cmd == "r":
                    for text in format_state(snapshot(interp, self.names)):
                        self._say(text)
                elif cmd == "m":
                    count = int(words[2]) if len(words) > 2 else 1
                    self._memory(self._address(words[1]), count)
                elif cmd == "b":
                    self.breakpoints.add(self._address(words[1]))
                elif cmd == "d":
                    self.breakpoints.discard(self._address(words[1]))
                elif cmd == "l":
                    for text in self.names.legend(
                        legend_ids(snapshot(interp, self.names), self.names)
                    ):
                        self._say(text)
                else:
                    self._say(self.names.say("help"))
            except (IndexError, ValueError) as exc:
                self._say(f"? {exc}")


Observer = RegisterTrace | Stepper


# --- Data Distributor ---------------------------------------------------------------------------


@dataclass
class DDTrace:
    """Engine listener: one line per memory cycle of the Data Distributor."""

    names: Names
    out: TextIO | None = None

    def __post_init__(self) -> None:
        self.out = self.out or sys.stdout

    def __call__(self, rec) -> None:
        if rec.unit != "DD":
            return
        say = self.names.say
        if rec.what == "transfer":
            if rec.get("kind") == "program_distributor":  # reads at RAPA into REDP, no CAR
                where = f"{self.names.label('rapa')} {rec.get('address'):05d}"
                br = self.names.label("redp")
            else:
                car = self.names.label("rac", rec.get("rac"))
                where = f"{car} {rec.get('address'):05d}→{rec.get('next'):05d}"
                br = self.names.label("rln")
            queue = ", ".join(rec.get("waiting")) or "-"
            text = (
                f"{rec.time:7d}  {rec.get('channel')}  {rec.get('gate'):<4}  "
                f"{rec.get('element'):<6} {say(rec.get('nature')):<6} {where:<18} "
                f"{br} {rec.get('value'):06X}  {say('waiting')}: {queue}"
            )
        elif rec.what == "incident":
            car = self.names.label("rac", rec.get("rac"))
            text = (
                f"{rec.time:7d}  ! {say('incident')} {rec.get('reason')}  "
                f"{rec.get('element')} {car} {rec.get('address'):05d}"
            )
        else:  # starvation (diagnostic mode)
            text = (
                f"{rec.time:7d}  ! {rec.get('element')} {say('starvation')} {rec.get('waited')} µs"
            )
        print(text, file=self.out)


def dd_summary(scenario, names: Names, duration: int) -> list[str]:
    """Per-client statistics of a Data Distributor scenario."""
    say, dd = names.say, scenario.dd
    lines = []
    for c in scenario.clients:
        served = dd.stats.served.get(c.name, 0)
        lines.append(
            f"  {c.name:<6} {say('served')} {served:4d}   "
            f"{say('wait')} {dd.stats.mean_wait(c.name):5.1f} / {dd.stats.wait_max.get(c.name, 0)} µs   "
            f"{say('misses')} {c.misses}   {say('share')} {served / (duration / dd.cycle):.1%}"
        )
    lines.append(f"  {say('occupancy')} : {dd.occupancy(duration):.1%}")
    gates = ", ".join(f"{g}/{ch} {n}" for (g, ch), n in sorted(dd.stats.gates.items()))
    lines.append(f"  {say('gates')} : {gates}")
    return lines
