"""The catena: 24 data bits plus a 3-bit check key (27 bits in store).

Bits are numbered 1 (right, least significant) to 24 (left) [B61 p.15]. The check key
depends on the machine profile (``check_key`` in ``data/profiles.yaml``):

- ``parity9_mod3_15`` (B61 p.26): 1 parity bit over bits 16-24 and 2 bits holding the
  remainder modulo 3 of bits 1-15 read as an integer;
- ``mod7_24bits`` (COURS p.11-12): the remainder modulo 7 of the 24-bit number.
"""

from __future__ import annotations

from dataclasses import dataclass

from gamma60 import data

MASK24 = (1 << 24) - 1
MASK15 = (1 << 15) - 1


class KeyError_(Exception):
    """A stored catena does not match its check key."""


def bits(value: int, high: int, low: int) -> int:
    """Field of bits ``high`` down to ``low`` (1-based, inclusive)."""
    return (value >> (low - 1)) & ((1 << (high - low + 1)) - 1)


def set_bits(value: int, high: int, low: int, field: int) -> int:
    width = high - low + 1
    if field >> width:
        raise ValueError(f"field {field} does not fit in bits {high}-{low}")
    mask = ((1 << width) - 1) << (low - 1)
    return (value & ~mask) | (field << (low - 1))


def check_key(value: int, kind: str) -> int:
    """3-bit check key of a 24-bit value for a key ``kind`` from profiles.yaml."""
    value &= MASK24
    if kind == "parity9_mod3_15":
        parity = bits(value, 24, 16).bit_count() & 1
        return (parity << 2) | (bits(value, 15, 1) % 3)
    if kind == "mod7_24bits":
        return value % 7
    raise ValueError(f"unknown check key kind {kind!r}")


@dataclass(frozen=True)
class Catena:
    """A stored catena: 24-bit value and its 3-bit key."""

    value: int
    key: int

    @classmethod
    def make(cls, value: int, profile: data.Profile | None = None) -> Catena:
        if not 0 <= value <= MASK24:
            raise ValueError(f"catena value out of range: {value}")
        kind = (profile or data.get_profile()).check_key
        return cls(value, check_key(value, kind))

    def checked(self, profile: data.Profile | None = None) -> int:
        """Return the value after verifying the key (raises ``KeyError_`` on mismatch)."""
        kind = (profile or data.get_profile()).check_key
        if check_key(self.value, kind) != self.key:
            raise KeyError_(f"check key mismatch on {self.value:024b}")
        return self.value


# --- codings of a catena ------------------------------------------------------------------


def to_bcd(digits: str) -> int:
    """6 decimal digits → 24-bit BCD (first digit in bits 24-21)."""
    if len(digits) != 6 or not digits.isdigit():
        raise ValueError(f"expected 6 decimal digits, got {digits!r}")
    value = 0
    for d in digits:
        value = (value << 4) | int(d)
    return value


def from_bcd(value: int) -> str:
    """24-bit BCD → 6 decimal digits (raises ValueError on a non-BCD tetrad)."""
    out = []
    for i in range(6):
        tetrad = bits(value, 24 - 4 * i, 21 - 4 * i)
        if tetrad > 9:
            raise ValueError(f"tetrad {tetrad:04b} is not BCD")
        out.append(str(tetrad))
    return "".join(out)


def _charset() -> tuple[dict[str, int], dict[int, str]]:
    table = data.load("charset")["characters"]
    by_code = {int(c["code"], 2): c["char"] for c in table}
    by_char = {char: code for code, char in by_code.items()}
    by_char[" "] = by_char["space"]
    return by_char, by_code


def to_alpha(text: str) -> int:
    """4 characters → 24-bit internal code (data/charset.yaml), first char in bits 24-19."""
    if len(text) != 4:
        raise ValueError(f"expected 4 characters, got {text!r}")
    by_char, _ = _charset()
    value = 0
    for ch in text:
        value = (value << 6) | by_char[ch]
    return value


def from_alpha(value: int) -> str:
    _, by_code = _charset()
    chars = [by_code[bits(value, 24 - 6 * i, 19 - 6 * i)] for i in range(4)]
    return "".join(" " if c == "space" else c for c in chars)
