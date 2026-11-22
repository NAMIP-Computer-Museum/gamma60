"""Code B: parsing of ``.g60b`` programs, shared by the J1 interpreter and the assembler.

Layout (docs/TOOLCHAIN.md): optional 3-digit line number, optional ``LABEL:``, T.O., then the
fields. ARIT directives: ``[C.C.] V O1 O2 R`` (``-`` = empty); LOGI directives: ``V R``.
Pseudo-instructions: ``VIERGE [m]``, ``NUM ±d``, ``BIN n``, ``ZONE n``. Header comments ``; langue:``,
``; profil:`` and ``; origine:`` (load address; default after the table of the recall chain
registers B / C, ``program_origin_default`` of behavior.yaml, U-30).
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from gamma60 import data

AF_TOKENS = {"R", "S", "RS", "M", "MS"}
PSEUDO = {"VIERGE", "NUM", "BIN", "ZONE"}
DATA = {"NUM", "BIN", "ZONE"}  # data lines: never executed

#: designator of an operand: ("rac", index, progress), "P" / "L" (register), or None (empty)
Designator = tuple[str, int, bool] | str | None


class ProgramError(ValueError):
    """The program text is invalid."""


@dataclass
class Line:
    source_line: int
    address: int
    label: str | None
    to: str
    args: list[str]
    size: int
    text: str = ""


@dataclass
class Program:
    lines: list[Line]
    labels: dict[str, int]
    language: str
    profile: str | None
    end: int  # first address after the program: base of the working memories
    origin: int = 0

    def at(self, address: int) -> Line:
        for line in self.lines:
            if line.address == address:
                return line
        raise ProgramError(f"no instruction at address {address}")


def binary_value(token: str, where: str = "") -> int:
    """``BIN n``: a 24-bit binary integer, 0 ≤ n < 2^24 (emulator pseudo-instruction)."""
    if not token.isdigit() or int(token) >> 24:
        raise ProgramError(f"{where}BIN expects an integer from 0 to 16777215, got {token!r}")
    return int(token)


def parse(text: str) -> Program:
    language, profile = data.default_language(), None
    origin = data.resolve(data.load("behavior")["program_origin_default"])
    for raw in text.splitlines():
        if m := re.match(r";\s*origine:\s*(\d+)", raw):
            origin = int(m.group(1))
    lines: list[Line] = []
    labels: dict[str, int] = {}
    address = origin
    for number, raw in enumerate(text.splitlines(), 1):
        if m := re.match(r";\s*langue:\s*(\w+)", raw):
            language = m.group(1)
        if m := re.match(r";\s*profil:\s*(\w+)", raw):
            profile = m.group(1)
        code = raw.split(";", 1)[0]
        tokens = code.split()
        if not tokens:
            continue
        if re.fullmatch(r"\d{3}", tokens[0]):
            address = origin + int(tokens.pop(0))
        label = None
        if tokens and tokens[0].endswith(":"):
            label = tokens.pop(0)[:-1]
            if label in labels:
                raise ProgramError(f"line {number}: label {label} defined twice")
            labels[label] = address
        if not tokens:
            raise ProgramError(f"line {number}: label without instruction")
        to, args = tokens[0], tokens[1:]
        size = 1
        if to == "NUM":
            size = 2
        elif to == "ZONE":
            size = int(args[0])
        lines.append(Line(number, address, label, to, args, size, code.strip()))
        address += size
    if language not in data.languages():
        raise ProgramError(f"unknown language {language!r}")
    end = max((ln.address + ln.size for ln in lines), default=origin)
    return Program(lines, labels, language, profile, end, origin)


def split_af(args: Sequence[str], fields: int) -> tuple[list[str], str]:
    """Split ``fields`` mandatory fields from the address function (R, S, M...)."""
    args = list(args)
    head, tail = args[:fields], args[fields:]
    af = "".join(tail)
    if len(head) < fields or (tail and not all(t in AF_TOKENS for t in tail)):
        raise ProgramError(f"invalid fields {' '.join(args)!r}")
    return head, af


@dataclass(frozen=True)
class AritFields:
    mode: str | None  # "P" programmed point, "N" normalised, "A" normalised and rounded
    double: bool
    point: int | None  # V field
    o1: Designator
    o2: Designator
    r: Designator


@dataclass(frozen=True)
class LogiFields:
    length: int
    r: Designator


class Syntax:
    """Language-dependent spellings of code B (data/directives.yaml)."""

    def __init__(self, language: str) -> None:
        self.language = language
        d = data.load("directives")
        self.no_progress = [
            str(data.resolve(c)) for c in d["operand_designators"]["car_no_progression"][language]
        ]
        cc1 = d["elements"]["arithmetic"]["cc1"]
        self.cc1_modes = {
            data.spelling(cc1["programmed_point"]["mnemonic"], language): "P",
            data.spelling(cc1["normalized"]["mnemonic"], language): "N",
            data.spelling(cc1["normalized_rounded"]["mnemonic"], language): "A",
        }
        self.cc2_double = data.spelling(
            d["elements"]["arithmetic"]["cc2"]["double_length"]["mnemonic"], language
        )

    def designator(self, token: str, allow: str) -> Designator:
        if token == "-":
            return None
        if token in "0123":
            return ("rac", int(token), True)
        if token in self.no_progress:
            return ("rac", self.no_progress.index(token), False)
        if token in allow:
            return token
        raise ProgramError(f"invalid operand designator {token!r}")

    def designator_text(self, d: Designator) -> str:
        if d is None:
            return "-"
        if isinstance(d, str):
            return d
        _, i, progress = d
        return str(i) if progress else self.no_progress[i]

    def arit(self, args: Sequence[str], where: str = "") -> AritFields:
        args = list(args)
        cc = args.pop(0) if len(args) == 5 else ""
        if len(args) != 4:
            raise ProgramError(f"{where}ARIT expects [C.C.] V O1 O2 R")
        mode = self.cc1_modes.get(cc[:1]) if cc[:1] != self.cc2_double else None
        double = bool(self.cc2_double) and self.cc2_double in cc
        if cc and mode is None and not double:
            raise ProgramError(f"{where}invalid C.C. {cc!r}")
        v, o1, o2, r = args
        if v != "-" and not v.isdigit():
            raise ProgramError(f"{where}invalid V field {v!r}")
        return AritFields(
            mode,
            double,
            None if v == "-" else int(v),
            self.designator(o1, "P"),
            self.designator(o2, ""),
            self.designator(r, "P"),
        )

    def logi(self, args: Sequence[str], where: str = "") -> LogiFields:
        if len(args) != 2:
            raise ProgramError(f"{where}LOGI expects V R")
        v, r = args
        if not v.isdigit():
            raise ProgramError(f"{where}invalid V field {v!r}")
        return LogiFields(int(v), self.designator(r, "L"))
