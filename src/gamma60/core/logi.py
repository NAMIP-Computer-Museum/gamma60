"""Logical calculator (LOGI): binary operations on registers K and L, no timing.

Semantics from COURS p.110-119 (summarised in docs/MACHINE.md §8). Every directive has a
field ``l`` (V, 0-24) and a column R holding either a RAC designator or ``"L"``. "The first l
positions" are the l rightmost bits. TCK/TCL read their operand through R; every other
directive except CBL stores L through R when a RAC is named. Open points: U-38.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from gamma60 import data
from gamma60.catena import MASK24
from gamma60.core.arit import Incident, set_position

#: R column: "L" (keep the result in L) or ("rac", index, progress).
Designator = str | tuple[str, int, bool]


def rotate_right(value: int, n: int) -> int:
    n %= 24
    return ((value >> n) | (value << (24 - n))) & MASK24


def low_mask(length: int) -> int:
    return (1 << length) - 1


def _rules() -> dict:
    return data.resolve(data.load("behavior")["logi"])


def compare_positions(k: int, l_: int, mask: int) -> int:
    """Qualitative of CBL [COURS p.118-119 ; positions 2-6: U-38]."""
    k, l_ = k & mask, l_ & mask
    order = {">": l_ > k, "<": l_ < k, "=": l_ == k, ">=": l_ >= k, "<=": l_ <= k, "!=": l_ != k}
    symbols = [">", *_rules()["cbl_positions_2_6"]]
    q = 0
    for position, symbol in enumerate(symbols, 1):
        if order[symbol]:
            q = set_position(q, position)
    union, inter = k | l_, k & l_
    flags = {
        7: union == k,
        8: union != k,
        9: union == l_,
        10: union != l_,
        11: inter == 0,
        12: inter != 0,
        13: union == mask,
        14: union != mask,
    }
    for position, holds in flags.items():
        if holds:
            q = set_position(q, position)
    return q


@dataclass
class LogicalUnit:
    k: int = 0
    l: int = 0
    qualitative: int = 0

    def execute(
        self,
        op: str,
        *,
        length: int,
        r: Designator,
        load: Callable[[Designator], int],
        store: Callable[[Designator, int], None],
    ) -> None:
        """Run one directive (identifiers of data/directives.yaml, elements.logical)."""
        if data.resolve(data.load("behavior")["qualitative_reset_each_directive"]):
            self.qualitative = 0  # U-07
        try:
            self._execute(op, length, r, load, store)
        except Incident:
            for position in data.resolve(data.load("behavior")["incident"])[
                "qualitative_positions"
            ]:
                self.qualitative = set_position(self.qualitative, position)
            raise

    def _execute(self, op, n, r, load, store) -> None:
        if not 0 <= n <= 24:
            raise Incident(f"length {n} outside 0-24")
        mask = low_mask(n)
        if op in ("transfer_shift_to_K", "transfer_shift_to_L"):
            if r == "L":
                raise Incident("L is meaningless in R for TCK / TCL")
            value = rotate_right(load(r), n)
            if op == "transfer_shift_to_K":
                self.k = value
            else:
                self.l = value
            return
        if op == "binary_logical_compare":
            self.qualitative = compare_positions(self.k, self.l, mask)
            return
        k, l_ = self.k, self.l
        if op == "transfer_K_to_L":
            l_ = k & mask
        elif op == "shift_left_L":  # MCL / SHL: circular shift of L by l to the right
            l_ = rotate_right(l_, n)
        elif op == "insert_K_in_L":
            l_ = (l_ & ~mask & MASK24) | (k & mask)
            k, l_ = rotate_right(k, n), rotate_right(l_, n)
        elif op in ("fill_zeros_L", "fill_ones_L"):
            l_ = (l_ & ~mask & MASK24) | (mask if op == "fill_ones_L" else 0)
            l_ = rotate_right(l_, n)
        elif op == "add":
            total = l_ + (k & mask)
            if total > MASK24 and _rules()["add_carry_beyond_24"] != "lost":
                raise Incident("carry beyond bit 24")
            l_ = total & MASK24
        elif op == "subtract":
            l_ = abs(l_ - (k & mask))  # negative result is "redressed" [COURS p.114]
        elif op == "multiply":
            product = (k & mask) * l_
            if product > MASK24:
                if _rules()["mul_overflow"] == "incident":
                    raise Incident("product longer than 24 bits")
                product &= MASK24
            l_, k = product, k & mask
        elif op == "divide":
            divisor = k & mask
            if divisor == 0:
                raise Incident("division by zero")
            quotient, remainder = divmod(l_, divisor)
            if quotient >> (24 - n):
                raise Incident("quotient longer than 24 - l bits")  # [COURS p.117]
            l_, k = (remainder << (24 - n)) | quotient, k & mask
        elif op == "complement_L":
            l_ ^= mask
        elif op in ("intersection", "union"):
            combined = (k & l_) if op == "intersection" else (k | l_)
            l_ = (l_ & ~mask & MASK24) | (combined & mask)
        else:
            raise ValueError(f"unknown LOGI directive {op!r}")
        self.k, self.l = k, l_
        if r != "L":
            store(r, self.l)
