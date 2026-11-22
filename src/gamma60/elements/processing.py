"""ARIT and LOGI as elements: operands and results through the DD, timed (milestone J3).

The computation itself is the pure code of J1 (:mod:`gamma60.core.arit`,
:mod:`gamma60.core.logi`). Durations [docs/MACHINE.md §8 ; data/timings.yaml]:

- ARIT: the global time of the directive (B61 200 / 350 / 550 / 150 µs; COURS 100 / 300 /
  600 µs, "transferts compris"); internal time = global time − transfer cycles (U-08), so a
  directive without contention lasts exactly the published time. The internal work is rounded
  down to whole memory cycles (results are written on a cycle boundary) and the end is then
  padded to the published time;
- LOGI: the cycle formulas of COURS p.120-121 (+ 3 cycles when L is stored), times the memory
  cycle of the profile (U-08 for B61).
"""

from __future__ import annotations

from collections import deque
from collections.abc import Generator
from typing import Any

from gamma60 import code_a, data
from gamma60.core.arit import ArithmeticUnit
from gamma60.core.logi import LogicalUnit
from gamma60.elements.base import Element, cycles, microseconds
from gamma60.number import Number


def _timings() -> dict:
    return data.load("timings")


class Processing(Element):
    """Common part: CAR reads and writes with or without progression [COURS p.68]."""

    def _timed(self, total: int, transfers: int, stores):
        """Internal work, then the writes, then pad the directive to ``total`` µs."""
        cycle = self.machine.dd.cycle
        internal = max(0, total - transfers * cycle) // cycle * cycle
        yield ("wait", internal)
        count = [0]
        for d, values in stores:
            yield from self._write(d, values, count)
        yield ("until", self._started + total)

    def _read(self, designator, width: int, count: list[int]):
        _, i, progress = designator
        racs = self.machine.dd.racs
        start = racs.get(self.name, i)
        values = []
        for _ in range(width):
            values.append((yield ("read", i)))
            count[0] += 1
        if not progress:
            racs.set(self.name, i, start)  # Z U D T / Z F S T: back to its initial value
        return values

    def _write(self, designator, values: list[int], count: list[int]):
        _, i, progress = designator
        racs = self.machine.dd.racs
        start = racs.get(self.name, i)
        for v in values:
            yield ("write", i, v)
            count[0] += 1
        if not progress:
            racs.set(self.name, i, start)


class Arithmetic(Processing):
    def __init__(self, machine, name: str = "ARIT", number: int | None = None) -> None:
        super().__init__(machine, "arithmetic", name, number if number is not None else 2)
        self.unit = ArithmeticUnit()

    def global_time(self, op: str) -> int:
        t = _timings()["arithmetic"]
        key = data.resolve(t["directive_time"]).get(op)
        times = self.machine.profile.times_us
        return times[key] if key in times else data.resolve(t["other_us"])

    def operate(self, characteristic: int) -> Generator[Any, Any, None]:
        op, f = code_a.decode_arit(characteristic)
        self._directive = op
        count = [0]
        fetched: deque[list[int]] = deque()
        used = code_a.ARIT_FIELDS[op]
        for name in ("o1", "o2"):  # operands in the order the unit asks for them
            d = getattr(f, name)
            if name in used and isinstance(d, tuple):
                fetched.append((yield from self._read(d, 2, count)))
        stores: list[tuple[Any, list[int]]] = []
        try:
            self.unit.execute(
                op,
                mode=f.mode,
                double=f.double,
                point=f.point,
                o1=f.o1,
                o2=f.o2,
                r=f.r,
                load=lambda _d: Number.from_catenae(*fetched.popleft()),
                store=lambda d, numbers: stores.append(
                    (d, [c for n in numbers for c in n.to_catenae()])
                ),
            )
        finally:
            self.qualitative = self.unit.qualitative
        writes = sum(len(v) for _, v in stores)
        yield from self._timed(self.global_time(op), count[0] + writes, stores)


class Logical(Processing):
    def __init__(self, machine, name: str = "LOGI", number: int | None = None) -> None:
        super().__init__(machine, "logical", name, number if number is not None else 1)
        self.unit = LogicalUnit()

    def operate(self, characteristic: int) -> Generator[Any, Any, None]:
        op, f = code_a.decode_logi(characteristic)
        self._directive = op
        cycle = self.machine.dd.cycle
        count = [0]
        loaded: list[int] = []
        if op in ("transfer_shift_to_K", "transfer_shift_to_L") and isinstance(f.r, tuple):
            loaded = yield from self._read(f.r, 1, count)
        stores: list[tuple[Any, int]] = []
        multiplier_ones = self.unit.l.bit_count()
        try:
            self.unit.execute(
                op,
                length=f.length,
                r=f.r,
                load=lambda _d: loaded[0],
                store=lambda d, value: stores.append((d, value)),
            )
        finally:
            self.qualitative = self.unit.qualitative
        t = _timings()["logical_cycles"]
        n_cycles = cycles(t["directives"][op], l=f.length, n=multiplier_ones)
        if stores:
            n_cycles += t["store_result"]
        total = microseconds(n_cycles, cycle)
        yield from self._timed(total, count[0] + len(stores), [(d, [v]) for d, v in stores])
