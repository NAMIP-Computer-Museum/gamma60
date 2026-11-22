"""Magnetic drum (DRUM / TAMB) — milestone J5 [COURS p.152-154 ; B61 p.12, p.24, p.53].

128 tracks of 200 catenae, plus 4 unused positions for switching tracks: 204 physical positions
per track, one revolution in 20 ms (U-46: 20 000 / 204 µs per position). In code A a drum
address is track × 256 + position, held in the element's register RAE, set by the preparatory
directive DAO. TCD / TRT (store → drum) and TDC / TTR (drum → store) carry the length; RAE and
the CAR advance together; at the end of a track the RAE jumps by 57 (199 → 256). After a
transfer the qualitative catena holds the final RAE in its 15 right positions [COURS p.153].

Each catena is exchanged with the store through the Data Distributor while its position passes
under the head. A catena not served in time costs one revolution [B61 p.24].
"""

from __future__ import annotations

from collections.abc import Generator
from fractions import Fraction
from typing import Any

from gamma60 import code_a, data
from gamma60.core.arit import Incident
from gamma60.elements.base import Element, microseconds

TRACKS, POSITIONS = 128, 200


class Drum(Element):
    def __init__(self, machine, name: str, number: int, unit: int = 1) -> None:
        super().__init__(machine, "drum", name, number)
        t = data.load("timings")["drum"]
        self.unit = unit
        self.revolution = t["revolution_us"]
        self.physical = t["physical_per_track"]
        self.position_us = Fraction(self.revolution, self.physical)  # U-46
        self.rae = 0  # Registre Adresse dans l'Élément [COURS p.153]
        self.store = [0] * (TRACKS * POSITIONS)
        self.lost_revolutions = 0
        rules = data.resolve(data.load("behavior")["drum"])
        self.overflow = rules["address_overflow"]
        self.directive_us = data.resolve(data.load("timings")["drum_directive_cycles"]) * (
            machine.dd.cycle
        )

    # -- geometry ---------------------------------------------------------------------------

    @staticmethod
    def index(rae: int) -> int:
        track, position = rae >> 8, rae & 0xFF
        if track >= TRACKS or position >= POSITIONS:
            raise Incident(f"drum address track {track} position {position} outside the drum")
        return track * POSITIONS + position

    def angle(self, t: int) -> Fraction:
        """Physical position (0-203, fractional) under the head at date t."""
        return (Fraction(t) / self.position_us) % self.physical

    def next_passage(self, position: int, t: int) -> int:
        """First date ≥ t (µs, rounded up) at which ``position`` starts passing under the head."""
        k = max(0, -(-(Fraction(t) / self.position_us - position) // self.physical))
        return microseconds((position + k * self.physical) * self.position_us, 1)

    def _advance_rae(self) -> None:
        position = (self.rae & 0xFF) + 1
        if position == POSITIONS:  # next track, position 0: + 57 in code A [COURS p.154]
            self.rae = ((self.rae >> 8) + 1) << 8
        else:
            self.rae += 1

    # -- directives ---------------------------------------------------------------------------

    def operate(self, characteristic: int) -> Generator[Any, Any, None]:
        op, _cc, _d, _s, x = code_a.decode_free("drum", characteristic)
        self._directive = op
        self.qualitative = 0
        if op == "set_drum_origin":
            self.rae = x
            yield ("wait", self.directive_us)
            return
        to_drum = op == "core_to_drum"
        yield ("wait", self.directive_us)
        for _ in range(x):
            if self.rae >> 8 >= TRACKS:
                raise Incident("drum capacity exceeded")
            slot = self.index(self.rae)
            position = self.rae & 0xFF
            if to_drum:  # the catena must be in the buffer register before its position passes
                target = self.next_passage(position, self.machine.engine.now)
                value = yield ("read", 0)
                if self.machine.engine.now > target:  # too late: wait for the next revolution
                    self.lost_revolutions += 1
                when = self.next_passage(position, self.machine.engine.now)
                yield ("until", when)
                self.store[slot] = value
            else:  # read under the head, then the buffer must reach the store before the next one
                when = self.next_passage(position, self.machine.engine.now)
                yield ("until", when)
                value = self.store[slot]
                deadline = when + microseconds(self.position_us, 1)
                yield ("write", 0, value)
                if self.machine.engine.now > deadline:  # served too late: one revolution lost
                    self.lost_revolutions += 1
                    yield ("wait", self.revolution)
            self._advance_rae()
        self.qualitative = self.rae & 0o77777  # final RAE in the qualitative catena [COURS p.153]

    def load(self, path) -> None:
        """Initial contents: YAML ``{address: [catenae…]}``, continuous code B addresses 0-25599."""
        from pathlib import Path

        import yaml

        spec = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        for address, catenae in spec.items():
            for k, c in enumerate(catenae):
                self.store[int(address) + k] = int(c, 0) if isinstance(c, str) else int(c)
