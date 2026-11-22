"""General comparator (COMP, « Comparateur Général ») — milestone J5 [COURS p.73-78 ; B61 p.36-37].

Zones of 1 to 255 catenae (length register of 8 bits), compared in pure binary, high-order
catena first. CAR 0 holds the first operand (the variable x); CAR 1 or 2 the second (simple
comparison, transfer: named by the C.C.); CARs 1 and 2 the bounds p and q (two-bound
comparison). A length 0 executes nothing and leaves the qualitative catena blank.

The operands are fetched ahead of the comparison [COURS p.75-77]: the work stops at the first
inequality, and the CARs then hold the address of the last catena compared plus 3 (CAR 0) or
plus 2 (CAR 1 / 2) for a simple comparison, plus 2 for all three in a two-bound comparison,
unless the count of the length stopped the requests before. The emulator reads those
anticipated catenae through the DD, so the CARs and the traffic follow the source.
Durations in memory cycles: CMP 5 + 3n, CDB 5 + 5n, EFL 2 + n, TRR 2 + 3n, n = effective length.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

from gamma60 import code_a, data
from gamma60.catena import MASK24
from gamma60.core.arit import Incident, set_position
from gamma60.elements.base import Element, cycles, microseconds

MAX_LENGTH = 255


def _value(catenae: list[int]) -> int:
    v = 0
    for c in catenae:
        v = (v << 24) | c
    return v


class Comparator(Element):
    def __init__(self, machine, name: str = "COMP", number: int = 3) -> None:
        super().__init__(machine, "comparator", name, number)
        self.operands = [0, 0]  # the two operand registers (one catena each) [COURS p.74-75]
        self.length = 0  # length register (8 bits)

    def _timed(self, n_cycles) -> Generator[Any, Any, None]:
        total = microseconds(n_cycles, self.machine.dd.cycle)
        yield ("until", self._started + total)

    def _read(self, car: int) -> Generator[Any, Any, int]:
        value = yield ("read", car)
        return value

    def operate(self, characteristic: int) -> Generator[Any, Any, None]:
        op, cc, _d, _s, length = code_a.decode_free("comparator", characteristic)
        self._directive = op
        self.qualitative = 0
        if length > MAX_LENGTH:
            self.qualitative = set_position(set_position(0, 23), 24)  # [COURS p.78]
            raise Incident(f"length {length} > {MAX_LENGTH}")
        self.length = length
        formulas = data.load("timings")["comparator_cycles"]
        if length == 0:  # no execution, qualitative blank [COURS p.75]
            yield from self._timed(1)
            return
        if op == "erase":
            for _ in range(length):
                yield ("write", 0, 0)
                self.length -= 1
            yield from self._timed(cycles(formulas["erase"], n=length))
        elif op == "transfer":
            for _ in range(length):
                value = yield from self._read(0)
                self.operands[0] = value
                yield ("write", cc, value)
                self.length -= 1
            yield from self._timed(cycles(formulas["transfer"], n=length))
        elif op == "simple_compare":
            yield from self._simple(cc, length, formulas["simple_compare"])
        else:
            yield from self._two_bounds(length, formulas["two_bounds_compare"])

    def _simple(self, cc: int, length: int, formula: str) -> Generator[Any, Any, None]:
        x, y = [], []
        n = 0
        while n < length:
            x.append((yield from self._read(0)))
            y.append((yield from self._read(cc)))
            self.operands = [x[-1], y[-1]]
            n += 1
            if x[-1] != y[-1]:
                break
        # requests already issued before the comparison stopped [COURS p.76]
        for _ in range(min(n + 2, length) - n):
            yield from self._read(0)
        for _ in range(min(n + 1, length) - n):
            yield from self._read(cc)
        a, b = _value(x), _value(y)
        positions = data.resolve(data.load("qualitative")["comparator"]["simple_positions"])
        tests = {
            ">=": a >= b,
            "<=": a <= b,
            "!=": a != b,
            "op1_zero": a == 0,
            "op1_ones": all(c == MASK24 for c in x),
            "op2_zero": b == 0,
            "op2_ones": all(c == MASK24 for c in y),
        }
        q = 0
        for position, holds in ((1, a > b), (2, a < b), (3, a == b)):
            if holds:
                q = set_position(q, position)
        for position, test in positions.items():
            if tests[test]:
                q = set_position(q, int(position))
        self.qualitative = q
        self.length = length - n
        yield from self._timed(cycles(formula, n=n))

    def _two_bounds(self, length: int, formula: str) -> Generator[Any, Any, None]:
        x, p, q_ = [], [], []
        n = 0
        while n < length:
            x.append((yield from self._read(0)))
            p.append((yield from self._read(1)))
            q_.append((yield from self._read(2)))
            n += 1
            if x[-1] != p[-1] and x[-1] != q_[-1]:
                break  # both inequalities known
        for car in (0, 1, 2):  # anticipated requests [COURS p.77]
            for _ in range(min(n + 1, length) - n):
                yield from self._read(car)
        a, lo, hi = _value(x), _value(p), _value(q_)
        flags = {
            1: a > lo and a > hi,
            2: a < lo and a < hi,
            3: lo <= a <= hi,
            4: a == lo,
            5: a == hi,
            6: lo < a < hi,
            7: a == 0,
            8: all(c == MASK24 for c in x),
        }
        q = 0
        for position, holds in flags.items():
            if holds:
                q = set_position(q, position)
        self.qualitative = q
        self.length = length - n
        yield from self._timed(cycles(formula, n=n))
