"""Assemblable subprogram: code A "with blanks" + table of unknowns and repères (J6).

The transposition of a code B subprogram yields relocatable code A, numbered from 0, plus the
table of its unknowns (X1, X2... ``?NAME``) and of its repères (R1, R2... ``REP``), "destinée
à l'assemblage" [MAIT §Sous-programmes ; DR-E p.178 ; COURS p.43-44]. The file format
(``.g60a.json``) is modern and not historical (U-14, U-52).

:meth:`Subprogram.place` puts the code at an implantation address: every relocatable X gets
the base added, every blank gets its value (from code C or code D).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from gamma60 import data
from gamma60.catena import MASK15
from gamma60.codeb import ProgramError
from gamma60.toolchain.assembler import DRUM_POSITIONS, Fixup, Image

FORMAT = "gamma60-subprogram/1"
MASK24 = (1 << 24) - 1


class LinkError(ProgramError):
    """Inconsistent subprogram, code C or code D."""


@dataclass
class Subprogram:
    name: str
    language: str
    profile: str | None
    words: dict[int, int]  # offset → catena (code A, blanks at 0)
    entry: int  # offset of the first instruction
    unknowns: list[str]  # X1, X2... in order of first appearance
    reperes: dict[str, int]  # R1, R2... (REP) → offset, in order of declaration
    fixups: list[Fixup]  # offsets
    relocations: list[int]  # offsets of the X holding an internal absolute address
    elements: dict[int, str] = field(default_factory=dict)
    joins: dict[int, int] = field(default_factory=dict)
    labels: dict[str, int] = field(default_factory=dict)  # debug table: label → offset
    lines: dict[int, tuple[int, str]] = field(default_factory=dict)  # offset → (line, text)
    source: str = ""
    end: int = 0  # offset of the end of the program: base of the working memories (M)
    working: int = 0  # number of working memories after ``end`` [COURS p.47-49]

    @property
    def size(self) -> int:
        """Catenae to reserve: the code, then its working memories."""
        return max(max(self.words, default=-1) + 1, self.end + self.working)

    # -- numbering of code C (U-53) ----------------------------------------------------------

    def unknown(self, ref: str) -> str:
        """``X2`` or ``NAME`` → name of the unknown."""
        if ref.startswith("X") and ref[1:].isdigit():
            n = int(ref[1:])
            if not 1 <= n <= len(self.unknowns):
                raise LinkError(f"{self.name}: no unknown {ref}")
            return self.unknowns[n - 1]
        name = ref.removeprefix("?")
        if name not in self.unknowns:
            raise LinkError(f"{self.name}: no unknown {ref}")
        return name

    def repere(self, ref: str) -> int:
        """``R1`` or ``NAME`` → offset of the repère."""
        names = list(self.reperes)
        if ref.startswith("R") and ref[1:].isdigit() and ref not in self.reperes:
            n = int(ref[1:])
            if not 1 <= n <= len(names):
                raise LinkError(f"{self.name}: no repère {ref}")
            return self.reperes[names[n - 1]]
        if ref not in self.reperes:
            raise LinkError(f"{self.name}: {ref} is not a repère (REP)")
        return self.reperes[ref]

    # -- implantation ------------------------------------------------------------------------

    def place(
        self, base: int, values: dict[str, int], leave: frozenset[str] = frozenset()
    ) -> dict[int, int]:
        """Code A at ``base``: relocations applied, blanks filled from ``values`` (except the
        unknowns in ``leave``, still blank)."""
        words = {base + k: v for k, v in self.words.items()}
        for k in self.relocations:
            a = base + k
            words[a] = (words[a] & ~MASK15) | ((words[a] + base) & MASK15)
        for f in self.fixups:
            if f.name in leave:
                continue
            if f.name not in values:
                raise LinkError(f"{self.name}: unknown {f.name} has no value")
            a = base + f.address
            value = convert(f.mode, values[f.name], a, f"{self.name}.{f.name}", f.field)
            if f.field == "word":
                words[a] = value & MASK24
            else:
                words[a] = (words[a] & ~MASK15) | value
        return words

    # -- files -------------------------------------------------------------------------------

    def to_json(self) -> dict:
        return {
            "format": FORMAT,
            "name": self.name,
            "language": self.language,
            "profile": self.profile,
            "source": self.source,
            "entry": self.entry,
            "words": words_out(self.words),
            "unknowns": [
                {
                    "n": i,
                    "name": name,
                    "uses": [
                        {"at": f.address, "field": f.field, "mode": f.mode}
                        for f in self.fixups
                        if f.name == name
                    ],
                }
                for i, name in enumerate(self.unknowns, 1)
            ],
            "reperes": [
                {"n": i, "name": name, "at": at}
                for i, (name, at) in enumerate(self.reperes.items(), 1)
            ],
            "relocations": self.relocations,
            "end": self.end,
            "working": self.working,
            "elements": {str(k): v for k, v in self.elements.items()},
            "joins": {str(k): v for k, v in self.joins.items()},
            "labels": self.labels,
            "lines": {str(k): list(v) for k, v in sorted(self.lines.items())},
        }

    @classmethod
    def from_json(cls, d: dict) -> Subprogram:
        if d.get("format") != FORMAT:
            raise LinkError(f"not a subprogram file ({d.get('format')!r})")
        fixups = [
            Fixup(u["at"], x["name"], u["field"], u["mode"])
            for x in d["unknowns"]
            for u in x["uses"]
        ]
        fixups.sort(key=lambda f: f.address)
        return cls(
            name=d["name"],
            language=d["language"],
            profile=d["profile"],
            words=words_in(d["words"]),
            entry=d["entry"],
            unknowns=[x["name"] for x in d["unknowns"]],
            reperes={r["name"]: r["at"] for r in d["reperes"]},
            fixups=fixups,
            relocations=list(d["relocations"]),
            elements={int(k): v for k, v in d["elements"].items()},
            joins={int(k): v for k, v in d["joins"].items()},
            labels=dict(d["labels"]),
            lines={int(k): (v[0], v[1]) for k, v in d["lines"].items()},
            source=d.get("source", ""),
            end=d.get("end", 0),
            working=d.get("working", 0),
        )

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_json(), indent=1) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> Subprogram:
        return cls.from_json(json.loads(Path(path).read_text(encoding="utf-8")))


def words_out(words: dict[int, int]) -> dict[str, str]:
    """Code A in a file of the chain: address → catena in hexadecimal (as listings and dumps)."""
    return {str(k): f"{v:06X}" for k, v in sorted(words.items())}


def words_in(words: dict[str, str | int]) -> dict[int, int]:
    """Inverse of :func:`words_out` (a decimal integer is accepted too)."""
    return {int(k): int(v, 16) if isinstance(v, str) else int(v) for k, v in words.items()}


def convert(mode: str, value: int, address: int, what: str, field: str = "x") -> int:
    """Value of a blank as it goes into the catena (see :class:`Fixup`)."""
    if mode == "diff":
        return (value - address) & MASK15
    if mode == "drum":
        track, position = divmod(value, DRUM_POSITIONS)
        if not 0 <= track <= 127:
            raise LinkError(f"{what}: drum address {value} > 25599")
        return (track << 8) | position
    if mode.startswith("unit:"):
        unit = data.resolve(data.load("topology")["unit_numbers"])[mode[5:]]
        if value < 1:
            raise LinkError(f"{what}: unit number {value} (from 1)")
        value = unit["first"] + unit["step"] * (value - 1)
    limit = MASK24 if field == "word" else MASK15
    if not 0 <= value <= limit:
        raise LinkError(f"{what}: value {value} outside 0-{limit}")
    return value


def from_image(image: Image, name: str) -> Subprogram:
    """Transposition result: the image moved to offset 0, with its tables."""
    o = image.program.origin
    prog = image.program
    words = {a - o: v for a, v in image.words.items()}
    for a in image.relocations:  # internal absolute addresses become offsets
        k = a - o
        words[k] = (words[k] & ~MASK15) | ((words[k] - o) & MASK15)
    return Subprogram(
        name=name,
        language=prog.language,
        profile=prog.profile,
        words=words,
        entry=image.entry - o,
        unknowns=image.unknowns,
        reperes={r: prog.labels[r] - o for r in prog.reperes},
        fixups=[Fixup(f.address - o, f.name, f.field, f.mode) for f in image.fixups],
        relocations=[a - o for a in image.relocations],
        elements={a - o: k for a, k in image.elements.items()},
        joins={a - o: m for a, m in image.joins.items()},
        labels={lab: a - o for lab, a in prog.labels.items()},
        lines={e.address - o: (e.line.source_line, e.line.text) for e in image.listing if e.line},
        end=prog.end - o,
        working=image.working,
    )
