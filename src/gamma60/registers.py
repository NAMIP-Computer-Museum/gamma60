"""Registers of the central unit (J2: the CAR matrix; J3 adds the IARs and the PD registers).

Sizes and counts come from ``data/registers.yaml``: the CAR / RAC matrix (MAQ) holds 128
registers of 15 address bits [ONDE §2.2.1 p.16]; each element type takes a fixed number of
them (``rac_per_element``). A CAR advances by +1 (or −1) at each transfer [B61 p.22-23].
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gamma60 import data
from gamma60.catena import MASK15


def register(ident: str) -> dict:
    return next(r for r in data.load("registers")["registers"] if r["id"] == ident)


def racs_for(kind: str) -> int:
    return data.resolve(data.load("registers")["rac_per_element"][kind])


@dataclass
class RacMatrix:
    """The MAQ matrix: CARs allocated to elements, addressed as (element, index)."""

    size: int = field(default_factory=lambda: register("rac")["count"])
    _values: list[int] = field(init=False)
    _base: dict[str, tuple[int, int]] = field(init=False, default_factory=dict)
    _next: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        self._values = [0] * self.size

    def allocate(self, element: str, count: int) -> None:
        if element in self._base:
            raise ValueError(f"element {element} already has its CARs")
        if self._next + count > self.size:
            raise ValueError(f"CAR matrix full ({self.size} registers)")
        self._base[element] = (self._next, count)
        self._next += count

    def _slot(self, element: str, index: int) -> int:
        base, count = self._base[element]
        if not 0 <= index < count:
            raise IndexError(f"{element} has {count} CARs, not CAR {index}")
        return base + index

    def get(self, element: str, index: int) -> int:
        return self._values[self._slot(element, index)]

    def set(self, element: str, index: int, address: int) -> None:
        self._values[self._slot(element, index)] = address & MASK15

    def advance(self, element: str, index: int, step: int = 1) -> int:
        """Return the current address and move the CAR by ``step`` (+1 or −1)."""
        slot = self._slot(element, index)
        address = self._values[slot]
        self._values[slot] = (address + step) & MASK15
        return address

    def of(self, element: str) -> list[int]:
        base, count = self._base[element]
        return self._values[base : base + count]

    @property
    def used(self) -> int:
        return self._next
