"""Assembly driven by a code C sheet: subprograms and zones → assembled program (J6).

"Le programmeur liste et numérote les sous-programmes - y compris les zones de manœuvre -
avec pour chacun la liste de ses inconnues (X). Il effectue alors pour chacune la liaison
SPy.Xn = SPz.Rm ou l'affectation SPy.Xn = constante dans les colonnes assembl. ; il affecte au
moins au premier sous-programme dans les colonnes distr une adresse d'implantation" ; the entry
repère and the exit unknown are given in the « distr. » columns; unknowns that cannot be fixed
at assembly receive a distribution symbol. The assembler condenses subprograms and zones,
makes the links and builds the table of the remaining unknowns with their symbols
[MAIT §Assemblage & code C].

The sheet is a modern YAML file (``.g60c.yaml``, U-53)::

    articles:                       # numbered: subprograms AND zones
      1: {sp: lecture.g60b}         # .g60b (transposed here) or .g60a.json
      2: {sp: traitement.g60a.json, nom: TRAIT}
      3: {zone: 50}                 # working zone; its start is repère R1
    assembl:                        # links and constants
      - 1.X1 = 2.R1                 # SPy.Xn = SPz.Rm (numbers or names: 1.?SUITE = TRAIT.DEBUT)
      - 2.X2 = 50                   # SPy.Xn = constante
    distr:
      implantation: {1: 1000}       # at least the first article; the others follow
      entree: 1.R1                  # default: entry of the first subprogram
      sortie: 2.X3                  # exit unknown → FIN_UT, a STOP added after the articles
      symboles: {1.X3: DEROULEUR}   # left to the distribution (code D2)

The result (``.g60pa.json``) is code A at its final addresses, with the blanks still to be
distributed and their symbols.
"""

from __future__ import annotations

import itertools
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from gamma60 import code_a, codeb
from gamma60.code_a import CUT, Word
from gamma60.toolchain.assembler import Fixup, assemble
from gamma60.toolchain.subprogram import (
    LinkError,
    Subprogram,
    convert,
    from_image,
    words_in,
    words_out,
)

FORMAT = "gamma60-assembled/1"
EXIT = "FIN_UT"  # exit of the processing unit: a STOP after the articles (U-53)
_REF = re.compile(r"^\s*([A-Za-z_0-9]+)\.(\??[A-Za-z_]\w*)\s*$")


@dataclass
class Article:
    number: int
    name: str
    sp: Subprogram | None = None  # None: zone
    size: int = 0
    base: int = 0


@dataclass
class Assembled:
    """Assembled program: code A in place, blanks left for the distribution."""

    words: dict[int, int]
    entry: int
    fixups: list[Fixup]  # absolute addresses; ``name`` = distribution symbol
    profile: str | None = None
    language: str = "en"
    elements: dict[int, str] = field(default_factory=dict)
    joins: dict[int, int] = field(default_factory=dict)
    labels: dict[str, int] = field(default_factory=dict)  # ARTICLE.LABEL → address
    lines: dict[int, tuple[str, int, str]] = field(default_factory=dict)  # (article, line, text)
    layout: list[tuple[int, str, int, int]] = field(default_factory=list)  # n, name, base, size
    exit: int | None = None

    @property
    def symbols(self) -> list[str]:
        return list(dict.fromkeys(f.name for f in self.fixups))

    def to_json(self) -> dict:
        return {
            "format": FORMAT,
            "profile": self.profile,
            "language": self.language,
            "entry": self.entry,
            "exit": self.exit,
            "layout": [
                {"article": n, "name": name, "base": base, "size": size}
                for n, name, base, size in self.layout
            ],
            "words": words_out(self.words),
            "symbols": [
                {
                    "name": s,
                    "uses": [
                        {"at": f.address, "field": f.field, "mode": f.mode}
                        for f in self.fixups
                        if f.name == s
                    ],
                }
                for s in self.symbols
            ],
            "elements": {str(k): v for k, v in sorted(self.elements.items())},
            "joins": {str(k): v for k, v in sorted(self.joins.items())},
            "labels": self.labels,
            "lines": {str(k): list(v) for k, v in sorted(self.lines.items())},
        }

    @classmethod
    def from_json(cls, d: dict) -> Assembled:
        if d.get("format") != FORMAT:
            raise LinkError(f"not an assembled program ({d.get('format')!r})")
        fixups = [
            Fixup(u["at"], s["name"], u["field"], u["mode"])
            for s in d["symbols"]
            for u in s["uses"]
        ]
        return cls(
            words=words_in(d["words"]),
            entry=d["entry"],
            fixups=sorted(fixups, key=lambda f: f.address),
            profile=d["profile"],
            language=d["language"],
            elements={int(k): v for k, v in d["elements"].items()},
            joins={int(k): v for k, v in d["joins"].items()},
            labels=dict(d["labels"]),
            lines={int(k): (v[0], v[1], v[2]) for k, v in d["lines"].items()},
            layout=[(a["article"], a["name"], a["base"], a["size"]) for a in d["layout"]],
            exit=d["exit"],
        )

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_json(), indent=1) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> Assembled:
        return cls.from_json(json.loads(Path(path).read_text(encoding="utf-8")))


def load_subprogram(path: Path) -> Subprogram:
    """A ``.g60a.json`` file, or a ``.g60b`` source transposed on the fly."""
    if path.name.endswith(".json"):
        return Subprogram.load(path)
    program = codeb.parse(path.read_text(encoding="utf-8"))
    sp = from_image(assemble(program), path.name.split(".")[0])
    sp.source = path.name
    return sp


class Linker:
    def __init__(self, sheet: dict, base_dir: Path) -> None:
        self.sheet = sheet or {}
        self.base_dir = base_dir
        self.articles: dict[int, Article] = {}
        self.by_name: dict[str, Article] = {}

    # -- references ---------------------------------------------------------------------------

    def _article(self, key: str, where: str) -> Article:
        if key.isdigit() and int(key) in self.articles:
            return self.articles[int(key)]
        if key in self.by_name:
            return self.by_name[key]
        raise LinkError(f"{where}: no article {key}")

    def _ref(self, text: str, where: str) -> tuple[Article, str]:
        m = _REF.match(str(text))
        if not m:
            raise LinkError(f"{where}: reference ARTICLE.Xn / ARTICLE.Rm expected, got {text!r}")
        return self._article(m.group(1), where), m.group(2)

    def _unknown(self, text: str, where: str) -> tuple[Article, str]:
        art, ref = self._ref(text, where)
        if art.sp is None:
            raise LinkError(f"{where}: article {art.number} is a zone (no unknown)")
        return art, art.sp.unknown(ref)

    def _address(self, text: str, where: str) -> int:
        """Address of ``ARTICLE.Rm`` (a zone has a single repère R1: its start)."""
        art, ref = self._ref(text, where)
        if art.sp is None:
            if ref not in ("R1", "DEBUT"):
                raise LinkError(f"{where}: a zone has only R1 (its start)")
            return art.base
        return art.base + art.sp.repere(ref)

    # -- assembly -----------------------------------------------------------------------------

    def link(self) -> Assembled:
        self._read_articles()
        distr = self.sheet.get("distr") or {}
        self._implant(distr.get("implantation") or {})
        values: dict[tuple[int, str], int] = {}
        symbols: dict[tuple[int, str], str] = {}
        for i, item in enumerate(self.sheet.get("assembl") or [], 1):
            where = f"assembl #{i}"
            left, sep, right = str(item).partition("=")
            if not sep:
                raise LinkError(f"{where}: SPy.Xn = SPz.Rm or SPy.Xn = constante")
            art, name = self._unknown(left, where)
            key = (art.number, name)
            if key in values:
                raise LinkError(f"{where}: {art.name}.{name} assigned twice")
            right = right.strip()
            values[key] = (
                int(right) if re.fullmatch(r"-?\d+", right) else self._address(right, where)
            )
        end = max(a.base + a.size for a in self.articles.values())
        exit_address = None
        if "sortie" in distr:
            art, name = self._unknown(distr["sortie"], "distr.sortie")
            if (art.number, name) in values:
                raise LinkError(f"distr.sortie: {art.name}.{name} already assigned")
            exit_address = end
            values[(art.number, name)] = exit_address
        for ref, symbol in (distr.get("symboles") or {}).items():
            art, name = self._unknown(ref, "distr.symboles")
            if (art.number, name) in values:
                raise LinkError(f"distr.symboles: {art.name}.{name} already assigned")
            if not re.fullmatch(r"[A-Za-z_]\w*", str(symbol)):
                raise LinkError(f"distr.symboles: invalid symbol {symbol!r}")
            symbols[(art.number, name)] = str(symbol)
        return self._condense(values, symbols, distr, exit_address)

    def _read_articles(self) -> None:
        raw = self.sheet.get("articles")
        if not raw:
            raise LinkError("code C: no article")
        for number in sorted(raw, key=int):
            spec = raw[number] or {}
            n = int(number)
            if isinstance(spec.get("sp"), Subprogram):  # already transposed (chain of run)
                sp = spec["sp"]
                art = Article(n, str(spec.get("nom") or sp.name), sp, sp.size)
            elif "sp" in spec:
                sp = load_subprogram(self.base_dir / spec["sp"])
                name = str(spec.get("nom") or sp.name)
                art = Article(n, name, sp, sp.size)
            elif "zone" in spec:
                art = Article(n, str(spec.get("nom") or f"Z{n}"), None, int(spec["zone"]))
            else:
                raise LinkError(f"article {n}: sp or zone expected")
            if art.name in self.by_name:
                raise LinkError(f"article {n}: name {art.name} already used (give a nom)")
            self.articles[n] = art
            self.by_name[art.name] = art

    def _implant(self, implantation: dict) -> None:
        numbers = sorted(self.articles)
        if numbers[0] not in {int(k) for k in implantation}:
            raise LinkError("distr.implantation: the first article needs an address [MAIT]")
        fixed = {int(k): int(v) for k, v in implantation.items()}
        cursor = 0
        for n in numbers:  # condensation: each article after the previous one
            art = self.articles[n]
            art.base = fixed.get(n, cursor)
            cursor = art.base + art.size
        spans = sorted((a.base, a.base + a.size, a.name) for a in self.articles.values())
        for (_, end1, n1), (start2, _, n2) in itertools.pairwise(spans):
            if start2 < end1:
                raise LinkError(f"implantation: {n1} and {n2} overlap")

    def _condense(self, values, symbols, distr, exit_address) -> Assembled:
        words: dict[int, int] = {}
        fixups: list[Fixup] = []
        out = Assembled(words, 0, fixups)
        profiles = {a.sp.profile for a in self.articles.values() if a.sp and a.sp.profile}
        if len(profiles) > 1:
            raise LinkError(f"subprograms transposed for different profiles {sorted(profiles)}")
        out.profile = profiles.pop() if profiles else None
        first = next((a.sp for a in self.articles.values() if a.sp), None)
        out.language = first.language if first else "en"
        for n in sorted(self.articles):
            art = self.articles[n]
            out.layout.append((n, art.name, art.base, art.size))
            if art.sp is None:
                for k in range(art.size):
                    words[art.base + k] = 0
                out.labels[art.name] = art.base
                out.lines[art.base] = (art.name, 0, f"ZONE  {art.size}")
                continue
            sp = art.sp
            missing = [
                f"{art.name}.?{x}"
                for x in sp.unknowns
                if (n, x) not in values and (n, x) not in symbols
            ]
            if missing:
                raise LinkError(f"unknowns neither linked nor given a symbol: {', '.join(missing)}")
            known = {x: values[(n, x)] for x in sp.unknowns if (n, x) in values}
            left = frozenset(x for x in sp.unknowns if x not in known)
            placed = sp.place(art.base, known, left)
            for f in sp.fixups:
                if f.name in left:  # still blank: the distribution fills it
                    a = art.base + f.address
                    fixups.append(Fixup(a, symbols[(n, f.name)], f.field, f.mode))
            words.update(placed)
            out.elements.update({art.base + k: v for k, v in sp.elements.items()})
            out.joins.update({art.base + k: v for k, v in sp.joins.items()})
            out.labels.update({f"{art.name}.{lab}": art.base + k for lab, k in sp.labels.items()})
            out.lines.update({art.base + k: (art.name, ln, t) for k, (ln, t) in sp.lines.items()})
        if exit_address is not None:
            words[exit_address] = code_a.encode(Word(CUT, "STOP"))
            out.labels[EXIT] = exit_address
            out.lines[exit_address] = (EXIT, 0, "STOP")
            out.exit = exit_address
        if "entree" in distr:
            out.entry = self._address(distr["entree"], "distr.entree")
        else:
            art = next(a for a in (self.articles[n] for n in sorted(self.articles)) if a.sp)
            out.entry = art.base + art.sp.entry
        fixups.sort(key=lambda f: f.address)
        return out


def link(path: str | Path) -> Assembled:
    path = Path(path)
    try:
        sheet = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise LinkError(f"{path.name}: invalid YAML ({exc})") from None
    return Linker(sheet, path.parent).link()


def distribute_value(f: Fixup, value: int, words: dict[int, int]) -> None:
    """Put the value of a symbol into its blank (used by the distribution, code D2)."""
    v = convert(f.mode, value, f.address, f.name, f.field)
    words[f.address] = v if f.field == "word" else (words[f.address] & ~0x7FFF) | v


def listing_lines(prog: Assembled) -> list[str]:
    """``address  code A  article.line  source`` for the assembled program."""
    blanks = {f.address: f.name for f in prog.fixups}
    out, skipped = [], False
    for n, name, base, size in prog.layout:
        out.append(f"; article {n} {name}: {base:05d} - {base + size - 1:05d} ({size} catenae)")
    for a in sorted(prog.words):
        if a not in prog.lines and prog.words[a] == 0:  # rest of a zone
            if not skipped:
                out.append("  ...")
            skipped = True
            continue
        skipped = False
        art, ln, text = prog.lines.get(a, ("", 0, ""))
        tokens = text.split(";")[0].split()
        while tokens and (re.fullmatch(r"\d{3}", tokens[0]) or tokens[0].endswith(":")):
            tokens.pop(0)
        is_data = not tokens or tokens[0] in codeb.DATA
        value = prog.words[a]
        code = f"{value:06X} (data)" if is_data else code_a.text(value)
        mark = f"  <- {blanks[a]} (distribution)" if a in blanks else ""
        where = f"{art}:{ln}" if ln else art
        out.append(f"{a:05d}  {code:<32} {where:<16} {text}{mark}")
    return out
