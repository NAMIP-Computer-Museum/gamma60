"""Semi-logarithmic numbers handled by ARIT (two catenae) [B61 p.18 ; COURS p.61-62].

First catena: bit 24 sign (0 = +, 1 = -), bits 23-21 tens digit of the exponent (binary,
0-7), bits 20-17 units digit of the exponent (BCD), bits 16-1 mantissa digits m1-m4 (BCD).
Second catena: mantissa digits m5-m10 (BCD). The exponent is biased by 40; the mantissa is
read as 0.m1...m10, so ``value = ±0.m1...m10 × 10^(E - 40) = ±m × 10^(E - 50)`` with ``m`` the
10-digit integer. Arithmetic is exact (integers and fractions), never binary floats.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from gamma60.catena import bits, from_bcd

MANTISSA_LIMIT = 10**10
EXPONENT_MAX = 79


class NotANumber(ValueError):
    """Two catenae that do not hold a semi-logarithmic number (non-BCD tetrad)."""


@dataclass(frozen=True)
class Number:
    negative: bool
    exponent: int  # biased, 0-79
    mantissa: int  # 10 decimal digits as an integer, 0 ≤ m < 10^10

    def __post_init__(self) -> None:
        if not 0 <= self.exponent <= EXPONENT_MAX:
            raise ValueError(f"exponent {self.exponent} outside 0-79")
        if not 0 <= self.mantissa < MANTISSA_LIMIT:
            raise ValueError(f"mantissa {self.mantissa} outside 10 digits")

    @property
    def value(self) -> Fraction:
        v = Fraction(self.mantissa) * Fraction(10) ** (self.exponent - 50)
        return -v if self.negative else v

    @property
    def digits(self) -> str:
        return f"{self.mantissa:010d}"

    def to_catenae(self) -> tuple[int, int]:
        d = self.digits
        tens, units = divmod(self.exponent, 10)
        first = (int(self.negative) << 23) | (tens << 20) | (units << 16)
        for i, ch in enumerate(d[:4]):
            first |= int(ch) << (12 - 4 * i)
        second = 0
        for ch in d[4:]:
            second = (second << 4) | int(ch)
        return first, second

    @classmethod
    def from_catenae(cls, first: int, second: int) -> Number:
        units = bits(first, 20, 17)
        if units > 9:
            raise NotANumber(f"exponent units tetrad {units:04b} is not BCD")
        exponent = bits(first, 23, 21) * 10 + units
        try:
            digits = from_bcd(bits(first, 16, 1))[2:] + from_bcd(second)
        except ValueError as e:
            raise NotANumber(str(e)) from e
        return cls(bool(bits(first, 24, 24)), exponent, int(digits))

    def __str__(self) -> str:
        sign = "-" if self.negative else "+"
        return f"{sign}{self.exponent:02d} {self.digits[:4]}|{self.digits[4:]}"


def proof7_key(n: Number) -> int:
    """Decimal check key of an operand: remainder of its mantissa by 7 [COURS p.66]."""
    return n.mantissa % 7
