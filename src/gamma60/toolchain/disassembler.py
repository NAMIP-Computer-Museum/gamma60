"""Disassembler: code A → code B, in ``en`` (B61) or ``fr`` (COURS) mnemonics (J6).

The inverse of the transposition, catena by catena, for a processing unit, an assembled
program or a subprogram, even without its source. Targets of the free variable are shown
symbolically (``LABEL+k``) when the tables of the chain know a label. The text is meant to be
read, not reassembled: a differential X is shown as its target, followed by ``R``.

What the code A alone does not tell: which catenae are data (the debug tables of the chain
say so when present; otherwise an undecodable catena is shown as data), the element of an
element directive (given by the table ``elements`` of the chain), and the place of the join
count in code B (shown as the C.C. of the cut, B61 form, U-20).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from gamma60 import code_a, data
from gamma60.catena import MASK15
from gamma60.code_a import ADDRESS, BRANCH, CENTRAL, CUT, ELEMENT, DecodeError
from gamma60.codeb import DATA, Syntax
from gamma60.number import NotANumber, Number
from gamma60.toolchain.assembler import DRUM_POSITIONS

SPECIAL_MNEMONIC = {"SIMU": "fork", "PROT": "virtual_engage", "LIBE": "virtual_release"}
#: role of the X of an instruction without S [COURS p.53-60] (raw mode: synthetic labels)
X_IS_QUANTITY = {  # a 15-bit quantity or an element number, not an address
    "load_element_number",
    "load_B_15",
    "add_B_15",
    "subtract_B_15",
    "compare_B_15",
    "add",  # address instructions A / S: X added to the CAR
    "subtract",
}
X_IS_CODE = {"switch_branch_never", "switch_branch_always", "reverse_switches"}  # a branch


@dataclass
class Source:
    """What the disassembler needs; built from any file of the chain."""

    words: dict[int, int]
    language: str
    elements: dict[int, str]
    labels: dict[str, int]
    data: set[int]  # addresses known to hold data
    numbers: set[int]  # first catena of a NUM (2 catenae)
    lines: dict[int, str]  # address → original code B (when known)
    synthetic: bool = False  # labels rebuilt from the code A (raw): quantities stay numbers


def number_text(n: Number) -> str:
    """Exact decimal value of a semi-logarithmic number (no binary float, rule 5)."""
    d = (Decimal(n.mantissa).scaleb(n.exponent - 50)).normalize()
    text = format(d, "f") if -12 <= d.adjusted() <= 15 else str(d)
    return ("-" if n.negative else "+") + text


def _reverse(index: dict[str, str]) -> dict[str, str]:
    return {ident: word for word, ident in index.items()}


class Disassembler:
    def __init__(self, source: Source) -> None:
        self.s = source
        lang = source.language
        self.syntax = Syntax(lang)
        self.cuts = _reverse(data.cut_index(lang))
        self.address_ops = _reverse(data.address_index(lang))
        self.central = _reverse(data.central_index(lang))
        numbers = data.resolve(data.load("topology")["element_numbers"])
        units = data.resolve(data.load("topology")["unit_numbers"])
        self.element_by_number = {
            v: k
            for k, v in numbers.items()
            if k not in units and k in data.load("directives")["cuts"]
        }
        self.units = units
        d = data.load("directives")
        self.special_cuts = {
            {"no_release_of_requester": "no_release", "no_busy_check": "no_busy_check"}[k]: (
                data.spelling(v["mnemonic"], lang)
            )
            for k, v in d["special_cuts_cours"].items()
        }
        cc1 = d["elements"]["arithmetic"]["cc1"]
        self.cc1 = {
            "P": data.spelling(cc1["programmed_point"]["mnemonic"], lang),
            "N": data.spelling(cc1["normalized"]["mnemonic"], lang),
            "A": data.spelling(cc1["normalized_rounded"]["mnemonic"], lang),
        }
        self.cc2 = data.spelling(
            d["elements"]["arithmetic"]["cc2"]["double_length"]["mnemonic"], lang
        )
        self.by_address = sorted(((a, lab) for lab, a in source.labels.items()), reverse=True)
        self.current: str | None = None  # element named by the last cut read (raw mode)

    # -- helpers ------------------------------------------------------------------------------

    def symbol(self, address: int) -> str:
        """``LABEL``, ``LABEL+k`` (nearest label before) or the address."""
        for a, label in self.by_address:
            if a <= address:
                if address == a:
                    return label
                if address - a < 64:
                    return f"{label}+{address - a}"
                break
        return str(address)

    def _x(self, here: int, x: int, d: bool, s: bool, op=None) -> str:
        if self.s.synthetic and op in X_IS_QUANTITY and not (d or s):
            return str(x)
        if d:
            target = (here + x) & MASK15
            text = f"{self.symbol(target)} R"
        else:
            text = self.symbol(x) if x in self.s.labels.values() else str(x)
        return text + (" S" if s else "")

    # -- one catena ---------------------------------------------------------------------------

    def line(self, address: int) -> str:
        value = self.s.words[address]
        if address in self.s.numbers:
            second = self.s.words.get(address + 1, 0)
            try:
                return f"NUM   {number_text(Number.from_catenae(value, second))}"
            except NotANumber:
                return f"NUM   ?          ; {value:06X} {second:06X}: not BCD"
        if address - 1 in self.s.numbers:
            return "      (NUM, 2nd catena)"
        if address in self.s.data:
            return f"BIN   {value}"
        if value == 0:
            return "VIERGE"
        try:
            w = code_a.decode(value)
        except DecodeError:
            return f"BIN   {value}        ; not an instruction"
        if w.kind == BRANCH:
            return f"{w.op:02d}    {self._x(address, w.x, w.d, w.s)}"
        if w.kind == CUT:
            return self._cut(address, w)
        if w.kind == CENTRAL:
            name = self.central.get(w.op, w.op)
            free = self._x(address, w.x, w.d, w.s, w.op) if (w.x or w.d or w.s) else ""
            return f"{name:<5} {free}".rstrip()
        if w.kind == ADDRESS:
            name = self.address_ops.get(w.op, w.op)
            return f"{name:<5} {w.car}     {self._x(address, w.x, w.d, w.s, w.op)}"
        if w.kind == ELEMENT:
            return self._element(address, w.characteristic)
        return f"BIN   {value}        ; undocumented code A (U-24)"

    def _cut(self, address: int, w) -> str:
        if w.op == "STOP":
            return "STOP"
        cc = f"{w.m} " if w.m else ""
        if w.op in SPECIAL_MNEMONIC:
            name = self.cuts[SPECIAL_MNEMONIC[w.op]]
            return f"{name:<5} {cc}{self._x(address, w.x, w.d, w.s)}"
        kind = self.special_cuts.get(w.op)
        prefix = f"{kind} " if kind else ""
        if w.d or w.s:  # element number computed by the PD
            return f"CUT   {prefix}{cc}{self._x(address, w.x, w.d, w.s)}"
        for ident, unit in self.units.items():
            k, rest = divmod(w.x - unit["first"], unit["step"])
            limit = 20 if ident == "uniselector" else 4  # 20 elements, 4 drums [MAIT §b]
            if not rest and w.x >= unit["first"] and 0 <= k < limit:
                self.current = ident
                return f"{self.cuts[ident]:<5} {prefix}{cc}{k + 1}"
        ident = self.element_by_number.get(w.x)
        if ident is None:
            return f"CUT   {prefix}{cc}{w.x}        ; element {w.x}"
        self.current = ident
        return f"{self.cuts[ident]:<5} {prefix}{cc}".rstrip()

    def _element(self, address: int, characteristic: int) -> str:
        kind = self.s.elements.get(address) or self.current  # raw: element of the last cut
        if kind is None:
            return f"BIN   {characteristic}        ; element directive, element unknown"
        names = _reverse(data.element_index(kind, self.s.language))
        if kind == "arithmetic":
            op, f = code_a.decode_arit(characteristic)
            cc = (self.cc1[f.mode] if f.mode else "") + (self.cc2 if f.double else "")
            fields = [
                "-" if f.point is None else str(f.point),
                *(self.syntax.designator_text(x) for x in (f.o1, f.o2, f.r)),
            ]
            return f"{names[op]:<5} {cc + ' ' if cc else ''}{' '.join(fields)}"
        if kind == "logical":
            op, f = code_a.decode_logi(characteristic)
            return f"{names[op]:<5} {f.length}    {self.syntax.designator_text(f.r)}"
        op, cc, d, s, x = code_a.decode_free(kind, characteristic)
        if op in code_a._encoding()["free_variable_layouts"]["execution_order"]:
            return names[op]
        if kind == "drum" and op == "set_drum_origin" and not (d or s):
            track, position = divmod(x, 256)
            x = track * DRUM_POSITIONS + position
            return f"{names[op]:<5} {x}"
        free = self._x(address, x, d, s) if (d or s) else str(x)
        return f"{names[op]:<5} {f'{cc} ' if cc else ''}{free}"


def disassemble(source: Source) -> list[tuple[int, int, str, str]]:
    """``(address, catena, symbol, code B)`` for every catena, in address order."""
    dis = Disassembler(source)
    labels = {a: lab for lab, a in source.labels.items()}
    return [(a, source.words[a], labels.get(a, ""), dis.line(a)) for a in sorted(source.words)]


def load(path) -> Source:
    """A :class:`Source` from a ``.ut.json``, ``.g60pa.json`` or ``.g60a.json`` file."""
    import json
    from pathlib import Path

    from gamma60.toolchain.distributor import ProcessingUnit
    from gamma60.toolchain.linker import Assembled
    from gamma60.toolchain.subprogram import LinkError, Subprogram

    d = json.loads(Path(path).read_text(encoding="utf-8"))
    kinds = {"gamma60-ut/1": ProcessingUnit, "gamma60-assembled/1": Assembled}
    kinds["gamma60-subprogram/1"] = Subprogram
    if d.get("format") not in kinds:
        raise LinkError(f"{path}: not a file of the chain ({d.get('format')!r})")
    return source_of(kinds[d["format"]].from_json(d))


def source_of(obj) -> Source:
    """A :class:`Source` from a U.T., an assembled program or a subprogram."""
    lines = {a: v[-1] for a, v in obj.lines.items()}
    data_addresses: set[int] = set()
    numbers: set[int] = set()
    for a, text in sorted(lines.items()):
        tokens = text.split(";")[0].split()
        while tokens and (tokens[0].isdigit() or tokens[0].endswith(":")):
            tokens.pop(0)
        if tokens and tokens[0] in DATA:
            size = 2 if tokens[0] == "NUM" else int(tokens[1]) if tokens[0] == "ZONE" else 1
            data_addresses.update(range(a, a + size))
            if tokens[0] == "NUM":
                numbers.add(a)
    labels = dict(obj.labels)
    if len(getattr(obj, "layout", ())) == 1:  # one article: bare labels, as in its source
        labels = {lab.split(".", 1)[-1]: a for lab, a in labels.items()}
    return Source(
        words=dict(obj.words),
        language=obj.language,
        elements=dict(obj.elements),
        labels=labels,
        data=data_addresses,
        numbers=numbers,
        lines=lines,
    )


def raw(source: Source) -> Source:
    """Only what is in the store: the catenae. No source line, no data marks, no element
    table (the element of a directive is the one named by the last cut, as for the
    assembler; a directive reached by a branch from elsewhere may be attributed wrongly).
    The labels are rebuilt from the code A: see :func:`synthetic_labels`."""
    words = dict(source.words)
    labels = synthetic_labels(words)
    return Source(words, source.language, {}, labels, set(), set(), {}, synthetic=True)


def synthetic_labels(words: dict[int, int]) -> dict[str, int]:
    """Labels rebuilt from the code A alone: ``Lnnnnn`` for a code target (branch, SIMU),
    ``Dnnnnn`` for a data address (address instruction, central directive with an address,
    PROT / LIBE image catena, catena read by substitution). Only addresses of ``words``."""
    code: set[int] = set()
    data_: set[int] = set()
    for here, value in words.items():
        if value == 0:
            continue
        try:
            w = code_a.decode(value)
        except DecodeError:
            continue
        if w.kind not in (BRANCH, CUT, CENTRAL, ADDRESS) or (w.kind == CUT and w.op == "STOP"):
            continue
        if w.kind == CUT and w.op not in SPECIAL_MNEMONIC:  # element number, not an address
            continue
        if w.kind == CENTRAL and not (w.x or w.d or w.s):
            continue
        if w.op in X_IS_QUANTITY and not (w.d or w.s):
            continue
        target = (here + w.x) & MASK15 if w.d else w.x
        if w.s:  # the catena at X holds the address actually used
            data_.add(target)
        elif w.kind == BRANCH and w.op == 0 and not w.d:
            continue  # "never" with an X: most likely a data catena, not a jump
        elif w.kind == BRANCH or (w.kind == CUT and w.op == "SIMU") or w.op in X_IS_CODE:
            code.add(target)
        else:
            data_.add(target)
    labels = {f"L{a:05d}": a for a in sorted(code) if a in words}
    labels.update({f"D{a:05d}": a for a in sorted(data_ - code) if a in words})
    return labels


def listing(source: Source, language: str | None = None) -> list[str]:
    if language:
        source = Source(**{**source.__dict__, "language": language})
    out, skipped = [], False
    for a, value, label, text in disassemble(source):
        orig = source.lines.get(a, "")
        previous_zero = source.words.get(a - 1) == 0 and a - 1 not in source.numbers
        if value == 0 and not orig and not label and previous_zero:  # run of zeros: a zone
            if not skipped:
                out.append("  ...")
            skipped = True
            continue
        skipped = False
        tail = f"   ; {orig}" if orig else ""
        out.append(f"{a:05d}  {value:06X}  {label + ':' if label else '':<20}{text:<28}{tail}")
    return out
