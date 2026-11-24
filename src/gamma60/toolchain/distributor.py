"""Distribution: values of the symbols (code D2) → processing unit (U.T.) (J6).

"[La distribution est] chargée de transformer un programme issu de l'assemblage en programme
personnalisé exécutable appelé unité de traitement (U.T.) ; ce logiciel est chargé de
distribuer au programme assemblé les valeurs numériques prévues pour les inconnues y ayant
reçu un code symbolique. Ces paramètres, de différents types (adresse mémoire, adresse
tambour, numéro d'appareil ou d'élément, longueur de zone, ...) sont introduits soit par des
ordres du pupitre, soit sous forme de cartes en code D2. On constitue ainsi une bibliothèque
d'U.T. exploitables directement, en remarquant que tout est figé" [MAIT §G.G.Z.].

Code D2 is a modern YAML file (``.g60d.yaml``, U-54)::

    programme: prog.g60c.yaml      # code C sheet (assembled here) or .g60pa.json
    valeurs:                       # one value per symbol
      DEROULEUR: 2                 # unit number, converted like in code B (U-44)
      LONG: 50

The values are written as in code B: a unit number for a cut, a continuous drum address for
DAO, an address or a length otherwise; the conversion recorded by the transposition is applied.
The U.T. is a JSON file (``.ut.json``): everything is fixed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from gamma60.toolchain.linker import Assembled, distribute_value, link
from gamma60.toolchain.subprogram import LinkError, words_in, words_out

FORMAT = "gamma60-ut/1"


@dataclass
class ProcessingUnit:
    """U.T.: fixed code A, ready to load; debug tables kept beside it."""

    name: str
    words: dict[int, int]
    entry: int
    exit: int | None = None
    profile: str | None = None
    language: str = "en"
    elements: dict[int, str] = field(default_factory=dict)
    joins: dict[int, int] = field(default_factory=dict)
    labels: dict[str, int] = field(default_factory=dict)
    lines: dict[int, tuple[str, int, str]] = field(default_factory=dict)
    layout: list[tuple[int, str, int, int]] = field(default_factory=list)
    distribution: dict[str, int] = field(default_factory=dict)  # symbol → value given

    def to_json(self) -> dict:
        return {
            "format": FORMAT,
            "name": self.name,
            "profile": self.profile,
            "language": self.language,
            "entry": self.entry,
            "exit": self.exit,
            "distribution": self.distribution,
            "layout": [
                {"article": n, "name": name, "base": base, "size": size}
                for n, name, base, size in self.layout
            ],
            "words": words_out(self.words),
            "elements": {str(k): v for k, v in sorted(self.elements.items())},
            "joins": {str(k): v for k, v in sorted(self.joins.items())},
            "labels": self.labels,
            "lines": {str(k): list(v) for k, v in sorted(self.lines.items())},
        }

    @classmethod
    def from_json(cls, d: dict) -> ProcessingUnit:
        if d.get("format") != FORMAT:
            raise LinkError(f"not a processing unit ({d.get('format')!r})")
        return cls(
            name=d["name"],
            words=words_in(d["words"]),
            entry=d["entry"],
            exit=d["exit"],
            profile=d["profile"],
            language=d["language"],
            elements={int(k): v for k, v in d["elements"].items()},
            joins={int(k): v for k, v in d["joins"].items()},
            labels=dict(d["labels"]),
            lines={int(k): (v[0], v[1], v[2]) for k, v in d["lines"].items()},
            layout=[(a["article"], a["name"], a["base"], a["size"]) for a in d["layout"]],
            distribution=dict(d["distribution"]),
        )

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_json(), indent=1) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> ProcessingUnit:
        return cls.from_json(json.loads(Path(path).read_text(encoding="utf-8")))


def distribute(prog: Assembled, values: dict[str, int], name: str) -> ProcessingUnit:
    """Fill every blank of ``prog`` with the value of its symbol."""
    missing = [s for s in prog.symbols if s not in values]
    if missing:
        raise LinkError(f"code D2: no value for {', '.join(missing)}")
    extra = [s for s in values if s not in prog.symbols]
    if extra:
        raise LinkError(f"code D2: {', '.join(extra)} is not a symbol of the program")
    words = dict(prog.words)
    for f in prog.fixups:
        value = values[f.name]
        if not isinstance(value, int):
            raise LinkError(f"code D2: {f.name} must be an integer, got {value!r}")
        distribute_value(f, value, words)
    return ProcessingUnit(
        name=name,
        words=words,
        entry=prog.entry,
        exit=prog.exit,
        profile=prog.profile,
        language=prog.language,
        elements=dict(prog.elements),
        joins=dict(prog.joins),
        labels=dict(prog.labels),
        lines=dict(prog.lines),
        layout=list(prog.layout),
        distribution={s: values[s] for s in prog.symbols},
    )


def load_assembled(path: Path) -> Assembled:
    """A ``.g60pa.json`` file, or a code C sheet assembled on the fly."""
    return Assembled.load(path) if path.name.endswith(".json") else link(path)


def distribute_file(path: str | Path) -> ProcessingUnit:
    path = Path(path)
    try:
        sheet = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise LinkError(f"{path.name}: invalid YAML ({exc})") from None
    if "programme" not in sheet:
        raise LinkError("code D2: programme (code C sheet or .g60pa.json) expected")
    prog = load_assembled(path.parent / sheet["programme"])
    return distribute(prog, dict(sheet.get("valeurs") or {}), path.name.split(".")[0])
