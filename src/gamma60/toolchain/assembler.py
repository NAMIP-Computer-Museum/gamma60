"""Minimal assembler: code B (``fr`` or ``en``) → memory image in code A (milestone J3).

Two passes over the parsed program (:mod:`gamma60.codeb`): labels are known after parsing,
then each line becomes one catena (``NUM``: two, ``ZONE n``: n; ``BIN n``: a binary integer). Address functions
[COURS p.47-49 ; docs/TOOLCHAIN.md]:

- ``R``: differential addressing (bit d); X is a label, or a line number of the sheet
  (relative to the origin); the catena holds the offset from the instruction, negative in
  complement to 32,768;
- ``M``: working memory number n, placed after the program, also as a differential offset;
- ``S``: substitution (bit s).

The join count of a cut is taken from its C.C. [B61 p.31] or from the X of its blank catena
[COURS p.52] (U-20). Sub-codes and element directive layouts are reconstructed (U-01).

Subprograms (J6, U-52): a free variable ``?NAME`` (or ``BIN ?NAME``) is an *unknown*, left
blank and recorded in :attr:`Image.fixups`; every X that holds an absolute address of the
program itself is recorded in :attr:`Image.relocations`, so the code A can be moved
[DR-E p.178 ; MAIT §Sous-programmes].
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction

from gamma60 import code_a, data
from gamma60.catena import MASK15
from gamma60.code_a import ADDRESS, BRANCH, CENTRAL, CUT, ELEMENT, Word
from gamma60.codeb import DATA, Line, Program, ProgramError, Syntax, binary_value, split_af
from gamma60.core.arit import fit

ASSEMBLED_ELEMENTS = {"arithmetic", "logical", "comparator", "drum", "uniselector"}
DRUM_POSITIONS = 200  # catenae per drum track [COURS p.152]


class AsmUnsupported(NotImplementedError):
    """Valid code B whose code A is not reconstructed yet (other elements: J5-J8)."""


@dataclass
class Listing:
    address: int
    value: int
    line: Line | None
    note: str = ""


@dataclass(frozen=True)
class Fixup:
    """A blank of the code A to be filled by code C or code D (U-52).

    ``field``: ``x`` (free variable, bits 15-1) or ``word`` (whole catena, ``BIN ?NAME``);
    ``mode``: ``abs`` (value as is), ``diff`` (R: value minus the address of the catena),
    ``unit:<cut>`` (unit number converted to an element number, U-44), ``drum`` (continuous
    drum address converted to track × 256 + position).
    """

    address: int
    name: str
    field: str = "x"
    mode: str = "abs"


@dataclass
class Image:
    """Assembled program: catenae by address, symbols and listing."""

    program: Program
    words: dict[int, int] = field(default_factory=dict)
    listing: list[Listing] = field(default_factory=list)
    elements: dict[int, str] = field(default_factory=dict)  # directive address → element kind
    joins: dict[int, int] = field(default_factory=dict)  # cut address → join count m
    entry: int = 0
    fixups: list[Fixup] = field(default_factory=list)  # unknowns ?NAME, in order (J6)
    relocations: list[int] = field(default_factory=list)  # X = absolute internal address
    working: int = 0  # working memories used after the program (M0, M1...: count)

    @property
    def unknowns(self) -> list[str]:
        """Names of the unknowns, in order of first appearance (X1, X2...)."""
        return list(dict.fromkeys(f.name for f in self.fixups))

    @property
    def labels(self) -> dict[str, int]:
        return self.program.labels

    def line_at(self, address: int) -> Line | None:
        for entry in self.listing:
            if entry.address == address:
                return entry.line
        return None


class Assembler:
    def __init__(self, program: Program, profile: data.Profile | None = None) -> None:
        self.program = program
        self.profile = profile or data.get_profile(program.profile)
        lang = program.language
        self.syntax = Syntax(lang)
        self.cuts = data.cut_index(lang)
        self.address_ops = data.address_index(lang)
        self.central = data.central_index(lang)
        self.special_cuts = {
            data.spelling(v["mnemonic"], lang): k
            for k, v in data.load("directives")["special_cuts_cours"].items()
            if data.spelling(v["mnemonic"], lang)
        }
        numbers = data.resolve(data.load("topology")["element_numbers"])
        self.element_numbers = {k: v for k, v in numbers.items()}
        self.unit_numbers = data.resolve(data.load("topology")["unit_numbers"])
        self.fixups: list[Fixup] = []
        self.relocations: list[int] = []
        self.working = 0

    # -- operands ---------------------------------------------------------------------------

    def _x(self, token: str, af: str, here: int, where: str) -> tuple[int, bool, bool]:
        """X field, d bit and s bit of a free variable."""
        labels = self.program.labels
        if token.startswith("?"):  # unknown: blank, filled by code C or code D (U-52)
            if "M" in af or not re.fullmatch(r"\?[A-Za-z_]\w*", token):
                raise ProgramError(f"{where}invalid unknown {token!r}")
            self.fixups.append(Fixup(here, token[1:], "x", "diff" if "R" in af else "abs"))
            return 0, "R" in af, "S" in af
        if "M" in af:
            if not token.isdigit():
                raise ProgramError(f"{where}working memory number expected, got {token!r}")
            target, d = self.program.end + int(token), True
            self.working = max(self.working, int(token) + 1)
        elif token in labels:
            target, d = labels[token], "R" in af
        elif re.fullmatch(r"\d+", token):
            # with R, a number is a line of the sheet, relative to the origin
            target, d = (
                (self.program.origin + int(token), True) if "R" in af else (int(token), False)
            )
        else:
            raise ProgramError(f"{where}unknown label or value {token!r}")
        x = (target - here) & MASK15 if d else target
        if not d and token in labels:  # absolute address of the program: moves with it
            self.relocations.append(here)
        if not d and not 0 <= x <= MASK15:
            raise ProgramError(f"{where}X {x} outside 0-32767")
        return x, d, "S" in af

    # -- assembly ---------------------------------------------------------------------------

    def assemble(self) -> Image:
        image = Image(self.program)
        element: str | None = None
        lines = self.program.lines
        for k, line in enumerate(lines):
            where = f"line {line.source_line}: "
            to, here = line.to, line.address
            if to == "NUM":
                p, _ = fit(Fraction(line.args[0].replace(",", ".")), None)
                for j, value in enumerate(p.to_catenae()):
                    self._put(image, here + j, value, line if j == 0 else None, "data")
                continue
            if to == "BIN":
                token = line.args[0]
                if token.startswith("?"):  # unknown catena, e.g. an address for RS (U-52)
                    if not re.fullmatch(r"\?[A-Za-z_]\w*", token):
                        raise ProgramError(f"{where}invalid unknown {token!r}")
                    self.fixups.append(Fixup(here, token[1:], "word"))
                    self._put(image, here, 0, line, "data")
                else:
                    self._put(image, here, binary_value(token, where), line, "data")
                continue
            if to == "ZONE":
                for j in range(line.size):
                    self._put(image, here + j, 0, line if j == 0 else None, "data")
                continue
            if to == "VIERGE":
                self._put(image, here, 0, line, "blank catena")
                continue
            if re.fullmatch(r"\d{2}", to):
                cond = int(to)
                if not (cond in (code_a.NEVER, code_a.ALWAYS) or 1 <= cond <= 24):
                    raise ProgramError(f"{where}branch condition {cond}")
                args, af = split_af(line.args, 1)
                x, d, s = self._x(args[0], af, here, where)
                word = Word(BRANCH, cond, d=d, s=s, x=x)
            elif to in self.cuts:
                ident = self.cuts[to]
                word = self._cut(line, ident, lines[k + 1] if k + 1 < len(lines) else None, where)
                if word.m:
                    image.joins[here] = word.m
                if ident in data.ELEMENT_KINDS or ident in ("desk",):
                    element = ident
            elif to in self.address_ops:
                args, af = split_af(line.args, 2)
                x, d, s = self._x(args[1], af, here, where)
                word = Word(ADDRESS, self.address_ops[to], car=int(args[0]), d=d, s=s, x=x)
            elif to in self.central:
                ident = self.central[to]
                if line.args:
                    args, af = split_af(line.args, 1)
                    x, d, s = self._x(args[0], af, here, where)
                else:
                    x, d, s = 0, False, False
                word = Word(CENTRAL, ident, d=d, s=s, x=x)
            else:
                if element is None:
                    raise ProgramError(f"{where}{to} before any cut")
                directive = data.element_index(element, self.program.language).get(to)
                if directive is None:
                    raise ProgramError(f"{where}{to} unknown for {element}")
                if element not in ASSEMBLED_ELEMENTS:
                    raise AsmUnsupported(
                        f"{where}code A of {element} directives (milestones J5-J8)"
                    )
                if element == "arithmetic":
                    char = code_a.encode_arit(directive, self.syntax.arit(line.args, where))
                elif element == "logical":
                    char = code_a.encode_logi(directive, self.syntax.logi(line.args, where))
                else:
                    char = self._free(element, directive, line.args, here, where)
                word = Word(ELEMENT, characteristic=char)
                image.elements[here] = element
            self._put(image, here, code_a.encode(word), line)
        image.entry = next((ln.address for ln in lines if ln.to not in DATA), self.program.origin)
        image.fixups, image.relocations = self.fixups, self.relocations
        image.working = self.working
        return image

    def _set_mode(self, here: int, token: str, mode: str) -> None:
        """Conversion applied when the unknown of the catena at ``here`` gets its value."""
        if token.startswith("?"):
            last = self.fixups[-1]
            assert last.address == here
            self.fixups[-1] = Fixup(here, last.name, last.field, mode)

    def _cut(self, line: Line, ident: str, blank: Line | None, where: str) -> Word:
        if ident == "end_of_sequence":
            return Word(CUT, "STOP")
        if blank is None or blank.to != "VIERGE" or blank.address != line.address + 1:
            raise ProgramError(f"{where}a cut must be followed by VIERGE")
        args = list(line.args)
        if ident in code_a.SPECIAL_CUTS:  # SIMU, PROT, LIBE: X = address
            cc = args.pop(0) if len(args) >= 2 and args[0].isdigit() and len(args[0]) == 1 else "0"
            head, af = split_af(args, 1)
            x, d, s = self._x(head[0], af, line.address, where)
            return Word(CUT, code_a.SPECIAL_CUTS[ident], m=self._join(cc, blank), d=d, s=s, x=x)
        kind, cc = "normal", "0"
        if args and args[0] in self.special_cuts:  # COURS: C.C. A / B (special cuts)
            kind = self.special_cuts[args.pop(0)]
            kind = {"no_release_of_requester": "no_release", "no_busy_check": "no_busy_check"}[kind]
        numbered = data.load("directives")["cuts"][ident].get("numbered")
        if numbered:  # [C.C.] X [A.F.]: number of the unit (drum k, uniselector k)
            if len(args) >= 2 and args[1].isdigit():
                cc = args.pop(0)
            head, af = split_af(args, 1)
            x, d, s = self._x(head[0], af, line.address, where)
            unit = self.unit_numbers.get(ident)
            if unit and not af:
                self._set_mode(line.address, head[0], f"unit:{ident}")
            if unit and not af and head[0].isdigit():  # unit k → element number (U-44)
                if int(head[0]) < 1:
                    raise ProgramError(f"{where}unit number {head[0]} (from 1)")
                x = unit["first"] + unit["step"] * (int(head[0]) - 1)
        else:
            if args:
                cc = args.pop(0)
            if args:
                raise ProgramError(f"{where}unexpected fields {' '.join(args)!r}")
            x, d, s = self.element_numbers[ident], False, False
        return Word(CUT, kind, m=self._join(cc, blank), d=d, s=s, x=x)

    def _free(self, element: str, op: str, args: list[str], here: int, where: str) -> int:
        """Directive with a free variable: COMP, drum, uniselector (layouts: U-01)."""
        args = list(args)
        if (
            element == "uniselector"
            and op in code_a._encoding()["free_variable_layouts"]["execution_order"]
        ):
            if args:
                raise ProgramError(f"{where}{op} has no free variable [COURS p.145]")
            return code_a.encode_free(element, op)
        cc = 0
        if element == "comparator" and op in code_a.CC_DIRECTIVES:
            if not args or args[0] not in ("1", "2"):
                raise ProgramError(f"{where}C.C. 1 or 2 expected (CAR of the second operand)")
            cc = int(args.pop(0))
        head, af = split_af(args, 1)
        x, d, s = self._x(head[0], af, here, where)
        if element == "comparator" and not af and x > 255:
            raise ProgramError(f"{where}length {x} > 255 [COURS p.75]")
        if element == "drum" and op == "set_drum_origin" and not af:
            self._set_mode(here, head[0], "drum")
            # continuous drum address of code B → track × 256 + position in code A [COURS p.154]
            track, position = divmod(x, DRUM_POSITIONS)
            if track > 127:
                raise ProgramError(f"{where}drum address {x} > 25599")
            x = (track << 8) | position
        return code_a.encode_free(element, op, x, cc, d, s)

    @staticmethod
    def _join(cc: str, blank: Line) -> int:
        m = int(cc) if cc.isdigit() else 0
        if blank.args:  # COURS: join count in the X of the blank catena [COURS p.52]
            m = max(m, int(blank.args[0]))
        if not 0 <= m <= 3:
            raise ProgramError(f"join count {m} outside 0-3")
        return m

    @staticmethod
    def _put(image: Image, address: int, value: int, line: Line | None, note: str = "") -> None:
        if address in image.words:
            raise ProgramError(f"address {address} assembled twice")
        image.words[address] = value
        image.listing.append(Listing(address, value, line, note))


def assemble(program: Program, profile: data.Profile | None = None) -> Image:
    return Assembler(program, profile).assemble()


def listing_lines(image: Image) -> list[str]:
    """``address  code A (fields)  source`` for each catena."""
    out = []
    for entry in image.listing:
        source = entry.line.text if entry.line else ""
        code = f"{entry.value:06X} (data)" if entry.note == "data" else code_a.text(entry.value)
        out.append(f"{entry.address:05d}  {code:<32} {source}")
    return out
