"""Code A: one instruction = one catena, typed by a prefix code TK [COURS p.33-52].

| TK | type | fields |
|---|---|---|
| ``00`` | branch | 22-18 condition (0 never, 1-24 bit of A, 31 always) · 17 d · 16 s · 15-1 X |
| ``01`` | cut | 22-20 kind · 19-18 m (join) · 17 d · 16 s · 15-1 element number or address |
| ``10`` | central directive | 22-18 directive · 17 d · 16 s · 15-1 X |
| ``110`` | address instruction | 21-20 operation · 19-18 CAR · 17 d · 16 s · 15-1 X |
| ``1111`` | element directive | 20-1 proper to the element (ARIT, LOGI: ``element_layouts``) |
| ``1110`` | undocumented (U-24) | |

Prefixes and fields are sourced; the values of the sub-codes and the layout of the ARIT and
LOGI directives are reconstructed (U-01, ``data/encoding.yaml``). A catena whose 7 left bits
are 0 (blank catena, data) executes as a "never" branch [COURS p.42].
"""

from __future__ import annotations

from dataclasses import dataclass

from gamma60 import data
from gamma60.catena import bits, set_bits
from gamma60.codeb import AritFields, Designator, LogiFields

BRANCH, CUT, CENTRAL, ADDRESS, ELEMENT, UNDOCUMENTED = (
    "branch",
    "cut",
    "central",
    "address",
    "element",
    "undocumented",
)
NEVER, ALWAYS = 0, 31

#: cut identifiers of directives.yaml → cut kind of encoding.yaml (element cuts: "normal")
SPECIAL_CUTS = {
    "virtual_engage": "PROT",
    "virtual_release": "LIBE",
    "fork": "SIMU",
    "end_of_sequence": "STOP",
}

#: fields used by each ARIT directive [COURS p.65-72 ; docs/MACHINE.md §8]
ARIT_FIELDS = {
    "add": ("o1", "o2", "r"),
    "subtract": ("o1", "o2", "r"),
    "multiply": ("o1", "o2", "r"),
    "divide": ("o1", "o2", "r"),
    "divide_with_remainder": ("o1", "o2", "r"),
    "transfer": ("o1", "r"),
    "multiply_pow10": ("o1", "r"),
    "divide_pow10": ("o1", "r"),
    "reverse_sign": ("o1", "r"),
    "absolute_value": ("o1", "r"),
    "compare_absolute": ("o1", "o2"),
    "compare_algebraic": ("o1", "o2"),
    "round_off": ("r",),
}
ARIT_USES_MODE = {"add", "subtract", "multiply", "divide", "divide_with_remainder", "transfer"}
ARIT_USES_POWER = {"multiply_pow10", "divide_pow10"}


class DecodeError(ValueError):
    """The catena is not a valid instruction ("directive décodée erronée")."""


@dataclass(frozen=True)
class Word:
    """A decoded catena of code A."""

    kind: str
    op: str | int | None = None  # branch: condition; cut: kind; central / address: identifier
    m: int = 0  # join count of a cut
    car: int = 0  # address instruction
    d: bool = False  # differential addressing (bit 17)
    s: bool = False  # substitution (bit 16)
    x: int = 0  # free variable, 15 bits
    characteristic: int = 0  # element directive: bits 20-1


def _encoding() -> dict:
    return data.load("encoding")


def _subcodes() -> dict:
    return _encoding()["synthetic_subcodes"]


def _field(name: str) -> dict:
    return _encoding()["types"][name]


# --- catena ↔ Word ---------------------------------------------------------------------------


def encode(w: Word) -> int:
    if w.kind == ELEMENT:
        return set_bits(0b1111 << 20, 20, 1, w.characteristic)
    value = 0
    if w.kind == BRANCH:
        value = set_bits(value, 22, 18, w.op)
    elif w.kind == CUT:
        value = set_bits(0b01 << 22, 22, 20, _subcodes()["cut_kind"][w.op])
        value = set_bits(value, 19, 18, w.m)
    elif w.kind == CENTRAL:
        value = set_bits(0b10 << 22, 22, 18, _subcodes()["central_directive"][w.op])
    elif w.kind == ADDRESS:
        value = set_bits(0b110 << 21, 21, 20, _subcodes()["address_op"][w.op])
        value = set_bits(value, 19, 18, w.car)
    else:
        raise ValueError(f"cannot encode a {w.kind} word")
    value = set_bits(value, 17, 17, int(w.d))
    value = set_bits(value, 16, 16, int(w.s))
    return set_bits(value, 15, 1, w.x)


def _reverse(table: dict) -> dict:
    return {v: k for k, v in table.items()}


def decode(value: int) -> Word:
    """Decode a catena; raise ``DecodeError`` for an undocumented prefix or sub-code."""
    d, s, x = bool(bits(value, 17, 17)), bool(bits(value, 16, 16)), bits(value, 15, 1)
    tk2 = bits(value, 24, 23)
    if tk2 == 0b00:
        condition = bits(value, 22, 18)
        if 24 < condition < ALWAYS:
            raise DecodeError(f"branch condition {condition} is not a bit of A")
        return Word(BRANCH, condition, d=d, s=s, x=x)
    if tk2 == 0b01:
        kind = _reverse(_subcodes()["cut_kind"]).get(bits(value, 22, 20))
        if kind is None:
            raise DecodeError(f"unknown cut kind {bits(value, 22, 20)}")
        return Word(CUT, kind, m=bits(value, 19, 18), d=d, s=s, x=x)
    if tk2 == 0b10:
        ident = _reverse(_subcodes()["central_directive"]).get(bits(value, 22, 18))
        if ident is None:
            raise DecodeError(f"unknown central directive {bits(value, 22, 18)}")
        return Word(CENTRAL, ident, d=d, s=s, x=x)
    if bits(value, 24, 22) == 0b110:
        op = _reverse(_subcodes()["address_op"])[bits(value, 21, 20)]
        return Word(ADDRESS, op, car=bits(value, 19, 18), d=d, s=s, x=x)
    if bits(value, 24, 21) == 0b1111:
        return Word(ELEMENT, characteristic=bits(value, 20, 1))
    raise DecodeError("undocumented prefix 1110 (U-24)")


# --- element directives (layouts reconstructed: U-01) ----------------------------------------------


def _layout(element: str) -> dict:
    return _encoding()["element_layouts"][element]


def directive_ids(element: str) -> list[str]:
    return list(data.load("directives")["elements"][element]["directives"])


def _designator_code(d: Designator) -> int:
    if d is None:
        return 0
    if isinstance(d, str):
        return 8
    _, i, progress = d
    return i if progress else 4 + i


def _designator(code: int, register: str) -> Designator:
    if code == 8:
        return register
    if code > 8:
        raise DecodeError(f"invalid operand designator {code}")
    return ("rac", code % 4, code < 4)


def encode_arit(op: str, f: AritFields) -> int:
    lay = _layout("arithmetic")
    used = ARIT_FIELDS[op]
    o1 = _designator_code(f.o1) if "o1" in used else 0
    o2 = _designator_code(f.o2) if "o2" in used else 0
    r = _designator_code(f.r) if "r" in used else 0
    if o2 == 8:
        raise ValueError("P is not allowed as second operand")
    mode = f.mode if op in ARIT_USES_MODE else None
    point = f.point or 0
    if mode == "P":
        if not 0 <= point <= 10:
            raise ValueError(f"decimal point position {point} outside 0-10")
        mp = 16 + point
    elif mode == "N":
        mp = 27
    elif mode == "A":
        mp = 28
    else:
        if not 0 <= point <= 15:
            raise ValueError(f"V {point} outside 0-15")
        mp = point if op in ARIT_USES_POWER else 0
    value = set_bits(0, *lay["directive"], directive_ids("arithmetic").index(op))
    value = set_bits(value, *lay["mode_point"], mp)
    value = set_bits(value, lay["double"], lay["double"], int(f.double))
    return set_bits(value, *lay["operands"], o1 * 72 + o2 * 9 + r)


def decode_arit(characteristic: int) -> tuple[str, AritFields]:
    lay = _layout("arithmetic")
    ids = directive_ids("arithmetic")
    index = bits(characteristic, *lay["directive"])
    if index >= len(ids):
        raise DecodeError(f"unknown ARIT directive {index}")
    op = ids[index]
    mp = bits(characteristic, *lay["mode_point"])
    if mp <= 15:
        mode, point = None, (mp if op in ARIT_USES_POWER else None)
    elif mp <= 26:
        mode, point = "P", mp - 16
    elif mp in (27, 28):
        mode, point = ("N" if mp == 27 else "A"), None
    else:
        raise DecodeError(f"invalid ARIT mode {mp}")
    packed = bits(characteristic, *lay["operands"])
    o1, rest = divmod(packed, 72)
    o2, r = divmod(rest, 9)
    used = ARIT_FIELDS[op]
    fields = AritFields(
        mode,
        bool(bits(characteristic, lay["double"], lay["double"])),
        point,
        _designator(o1, "P") if "o1" in used else None,
        _designator(o2, "P") if "o2" in used else None,
        _designator(r, "P") if "r" in used else None,
    )
    return op, fields


def encode_logi(op: str, f: LogiFields) -> int:
    lay = _layout("logical")
    if not 0 <= f.length <= 24:
        raise ValueError(f"length {f.length} outside 0-24")
    value = set_bits(0, *lay["directive"], directive_ids("logical").index(op))
    value = set_bits(value, *lay["length"], f.length)
    return set_bits(value, *lay["r"], _designator_code(f.r))


def decode_logi(characteristic: int) -> tuple[str, LogiFields]:
    lay = _layout("logical")
    ids = directive_ids("logical")
    index = bits(characteristic, *lay["directive"])
    if index >= len(ids):
        raise DecodeError(f"unknown LOGI directive {index}")
    length = bits(characteristic, *lay["length"])
    if length > 24:
        raise DecodeError(f"length {length} outside 0-24")
    return ids[index], LogiFields(length, _designator(bits(characteristic, *lay["r"]), "L"))


def text(value: int) -> str:
    """Binary form grouped by fields, e.g. ``00 11111 1 0 000000000001010``."""
    b = f"{value:024b}"
    try:
        kind = decode(value).kind
    except DecodeError:
        return f"{b[:4]} {b[4:]}"
    if kind in (BRANCH, CENTRAL):
        return f"{b[:2]} {b[2:7]} {b[7]} {b[8]} {b[9:]}"
    if kind == CUT:
        return f"{b[:2]} {b[2:5]} {b[5:7]} {b[7]} {b[8]} {b[9:]}"
    if kind == ADDRESS:
        return f"{b[:3]} {b[3:5]} {b[5:7]} {b[7]} {b[8]} {b[9:]}"
    return f"{b[:4]} {b[4:]}"


# --- element directives with a free variable (COMP, drum, uniselector: U-01) ----------------------

FREE_VARIABLE_ELEMENTS = ("comparator", "drum", "uniselector")
CC_DIRECTIVES = {"simple_compare", "transfer"}  # C.C. = CAR 1 or 2 [COURS p.75]


def _free_layout(element: str) -> dict:
    return _encoding()["free_variable_layouts"][element]


def encode_free(
    element: str, op: str, x: int = 0, cc: int = 0, d: bool = False, s: bool = False
) -> int:
    """Characteristic (bits 20-1) of a directive: type 20-18, d 17, s 16, X 15-1 [COURS p.41]."""
    layout = _free_layout(element)
    execution = _encoding()["free_variable_layouts"]["execution_order"]
    if element == "uniselector" and op in execution:
        type_, x, d, s = layout["execution"], execution.index(op), False, False
    elif op in CC_DIRECTIVES and element == "comparator":
        if cc not in (1, 2):
            raise ValueError(f"{op} needs C.C. 1 or 2 (the CAR of the second operand)")
        type_ = layout[f"{op}_{cc}"]
    else:
        type_ = layout[op]
    if not 0 <= x <= 0o77777:
        raise ValueError(f"X {x} outside 0-32767")
    return (type_ << 17) | (int(d) << 16) | (int(s) << 15) | x


def decode_free(element: str, characteristic: int) -> tuple[str, int, bool, bool, int]:
    """(directive, C.C., d, s, X) of a characteristic."""
    layout = _free_layout(element)
    type_ = bits(characteristic, 20, 18)
    d, s, x = (
        bool(bits(characteristic, 17, 17)),
        bool(bits(characteristic, 16, 16)),
        bits(characteristic, 15, 1),
    )
    by_type = {v: k for k, v in layout.items()}
    name = by_type.get(type_)
    if name is None:
        raise DecodeError(f"unknown {element} directive type {type_}")
    if name == "execution":
        order = _encoding()["free_variable_layouts"]["execution_order"]
        if x >= len(order):
            raise DecodeError(f"unknown {element} execution directive {x}")
        return order[x], 0, False, False, 0
    if element == "comparator" and name[-2:] in ("_1", "_2"):
        return name[:-2], int(name[-1]), d, s, x
    return name, 0, d, s, x


def has_address_function(element: str, characteristic: int) -> bool:
    """True when the PD must apply d / s to the X of this directive before sending it."""
    if element not in FREE_VARIABLE_ELEMENTS:
        return False
    return not (
        element == "uniselector"
        and bits(characteristic, 20, 18) == _free_layout(element)["execution"]
    )
