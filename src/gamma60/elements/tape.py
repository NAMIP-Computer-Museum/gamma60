"""Magnetic tapes: uniselectors (MATA / DERU) and tape drives — milestone J5.

Sources: COURS p.135-151 ; B61 p.13, p.26, p.53-55 ; docs/MACHINE.md §8.

The element is the **uniselector**, not the drive: the cut names the uniselector, which owns the
CAR and the recall chain [COURS p.145]. A preparatory directive (ECR / WRI, LAV / REF,
LAR / REB) names the drive (X) and connects it, wired as on B61 p.54; it stays valid across
cuts. The execution directives (TRA, SAU / JUM, EFF / DEL, ECM / WRM) have no free variable;
TRA reads or writes one block. Service directives (REB / SPO, REM / SPN, MAN, MAI) name the
drive, which then works on its own while the uniselector asks at once for its next instruction;
the drive signals that it is busy (position 21) [COURS p.146-147].

A block: pilot zone, the length catena (kept by the uniselector, not transferred), the
catenae, the length again, a pilot zone [COURS p.140-141]. Read forwards the CAR advances,
read backwards it goes back, so the image in the store is the same [COURS p.141]. A tape mark
(16 zeros) is not transferred and sets position 19 [COURS p.137]. Discontinuous mode only:
the tape starts (5 ms) and stops (5 ms) around each block (U-47). The continuous mode (an
uniselector seen as a double element, COURS p.147-148) is not run yet.

A reel is a list of blocks (lists of catenae) and tape marks, loaded from a YAML file:
``blocks: [[1, 2, 3], mark, ["0x123456", 7]]``, ``write_protected: false``.
"""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from gamma60 import code_a, data
from gamma60.core.arit import Incident, set_position
from gamma60.elements.base import Element

MARK = "mark"
MARK_LENGTH = 16  # catenae of a tape mark [COURS p.137]


def _settings() -> tuple[dict, dict, dict]:
    tape = data.load("timings")["tape"]
    block = data.resolve(data.load("timings")["tape_block"])
    rules = data.resolve(data.load("behavior")["tape"])
    return tape, block, rules


@dataclass
class TapeDrive:
    """A tape drive with its reel: blocks, position (index of the next block), flags."""

    number: int
    blocks: list = field(default_factory=list)
    write_protected: bool = False
    position: int = 0
    busy_until: int = 0
    lamp: str = ""  # "green" (normal manipulation) or "red" (incident)
    centimetres: float = 0.0  # distance from the start of the reel

    @classmethod
    def load(cls, number: int, path: str | Path) -> TapeDrive:
        spec = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        blocks = []
        for b in spec.get("blocks", []):
            if b == MARK:
                blocks.append(MARK)
            else:
                blocks.append([int(c, 0) if isinstance(c, str) else int(c) for c in b])
        return cls(number, blocks, bool(spec.get("write_protected", False)))

    def busy(self, t: int) -> bool:
        return t < self.busy_until

    def length_cm(self, block) -> float:
        tape, block_t, _ = _settings()
        n = MARK_LENGTH if block == MARK else len(block) + 2  # with its two length catenae
        n += 2 * block_t["pilot_catenae"]
        return n / tape["density_catenae_per_cm"] + tape["start_stop_gap_cm"]

    def summary(self) -> list[str]:
        lines = [f"drive {self.number}: {len(self.blocks)} block(s), position {self.position}"]
        for k, b in enumerate(self.blocks):
            if b == MARK:
                lines.append(f"  {k:3d}  tape mark")
            else:
                head = " ".join(f"{c:06X}" for c in b[:6])
                more = " ..." if len(b) > 6 else ""
                lines.append(f"  {k:3d}  {len(b):4d} catenae  {head}{more}")
        return lines


class Uniselector(Element):
    def __init__(self, machine, name: str, number: int, unit: int, drives: list[int]) -> None:
        super().__init__(machine, "uniselector", name, number)
        self.unit = unit
        self.wired = set(drives)  # drives this uniselector can select [B61 p.54]
        self.drive: TapeDrive | None = None
        self.mode = ""  # write, read_forward, read_backward (kept across cuts)
        self.block_length = 0  # register of the length catena [COURS p.141]
        self.overruns = 0

    def _cycles(self, n: int) -> int:
        return n * self.machine.dd.cycle

    def _flag(self, *positions: int) -> None:
        for p in positions:
            self.qualitative = set_position(self.qualitative, p)

    def operate(self, characteristic: int) -> Generator[Any, Any, None]:
        op, _cc, _d, _s, x = code_a.decode_free("uniselector", characteristic)
        self._directive = op
        tape, block_t, rules = _settings()
        self.qualitative = 0
        now = self.machine.engine.now
        if op in ("write", "read_forward", "read_backward"):
            yield ("wait", self._cycles(block_t["preparatory_cycles"]))
            self._connect(x)
            self.mode = op
            if self.drive.write_protected:
                self._flag(rules["write_protect_position"])
            if self.drive.busy(self.machine.engine.now):
                self._flag(21, 23)
            return
        if op in ("rewind", "rewind_and_request", "normal_request", "incident_request"):
            yield ("wait", self._cycles(block_t["service_cycles"]))
            drive = self._connect(x)
            self._service(op, drive, tape)
            return  # the uniselector asks at once for its next instruction [COURS p.146]
        if self.drive is None or not self.mode:
            raise Incident(f"{op} without a preparatory directive")
        drive = self.drive
        if drive.busy(now):  # the directive waits for the end of the service [COURS p.146]
            yield ("until", drive.busy_until)
        if op == "erase":
            seconds = block_t["erase_cm"] / (tape["speed_m_s"] * 100)
            yield ("wait", int(seconds * 1_000_000))
            drive.centimetres += block_t["erase_cm"]
            del drive.blocks[drive.position :]
            return
        if op == "write_tape_mark":
            if drive.write_protected:
                self._flag(rules["write_protect_position"], 23)
                return
            yield from self._motion(MARK_LENGTH, None)
            self._store_block(drive, MARK, rules)
            return
        if self.mode == "write":
            if op != "read_transfer":
                raise Incident(f"{op} has no meaning after a write directive [COURS p.146]")
            if drive.write_protected:
                self._flag(rules["write_protect_position"], 23)
                return
            yield from self._write_block(drive, rules)
            return
        yield from self._read_block(drive, op == "read_transfer", rules)

    # -- connection and service ---------------------------------------------------------------

    def _connect(self, number: int) -> TapeDrive:
        drive = self.machine.tape_drives.get(number)
        if drive is None or number not in self.wired:  # « sécurité d'appel » [COURS p.150]
            self._flag(24, 17)
            raise Incident(f"drive {number} is not connected to {self.name}")
        self.drive = drive
        return drive

    def _service(self, op: str, drive: TapeDrive, tape: dict) -> None:
        now = self.machine.engine.now
        operator = data.load("behavior")["operator_delay_us"]
        duration = 0
        if op in ("rewind", "rewind_and_request"):
            duration += int(drive.centimetres / (tape["rewind_m_s"] * 100) * 1_000_000)
            drive.position, drive.centimetres = 0, 0.0
        if op in ("rewind_and_request", "normal_request"):
            drive.lamp, duration = "green", duration + operator
        if op == "incident_request":
            drive.lamp, duration = "red", duration + operator
        drive.busy_until = max(drive.busy_until, now) + duration
        self.machine.engine.record(
            self.name, "service", directive=op, drive=drive.number, until=drive.busy_until
        )

    # -- one block ------------------------------------------------------------------------------

    def _motion(self, catenae: int, per_catena: int | None):
        """Start, pilot zone, ``catenae`` passing under the head, pilot zone, stop."""
        _tape, block_t, _ = _settings()
        per = per_catena or self.machine.profile.times_us["tape_per_catena"]
        yield ("wait", block_t["acceleration_us"] + block_t["pilot_catenae"] * per)
        start = self.machine.engine.now
        yield ("until", start + catenae * per)
        yield ("wait", block_t["pilot_catenae"] * per + block_t["deceleration_us"])

    def _read_block(self, drive: TapeDrive, transfer: bool, rules: dict):
        backwards = self.mode == "read_backward"
        index = drive.position - 1 if backwards else drive.position
        if not 0 <= index < len(drive.blocks):  # nothing recorded there (U-48)
            yield from self._motion(MARK_LENGTH, None)
            self._flag(18, 23)
            return
        block = drive.blocks[index]
        drive.position = index if backwards else index + 1
        if block == MARK:
            yield from self._motion(MARK_LENGTH, None)
            self._flag(19, 23)  # tape mark: not transferred [COURS p.137]
            self.block_length = 0
            return
        _tape, block_t, _ = _settings()
        per = self.machine.profile.times_us["tape_per_catena"]
        self.block_length = len(block)
        yield ("wait", block_t["acceleration_us"] + (block_t["pilot_catenae"] + 1) * per)
        start = self.machine.engine.now
        order = list(reversed(block)) if backwards else list(block)
        for k, value in enumerate(order):
            arrival = start + k * per
            yield ("until", arrival)
            if transfer:
                yield ("write", 0, value, -1 if backwards else 1)
                if self.machine.engine.now > arrival + per:  # buffer not emptied in time (U-48)
                    self.overruns += 1
                    if rules["overrun"] == "bad_read":
                        self._flag(18, 23)
        yield ("until", start + len(block) * per)
        yield ("wait", (block_t["pilot_catenae"] + 1) * per + block_t["deceleration_us"])
        drive.centimetres += drive.length_cm(block)
        self._end_warning(drive, block_t)

    def _write_block(self, drive: TapeDrive, rules: dict):
        _tape, block_t, _ = _settings()
        per = self.machine.profile.times_us["tape_per_catena"]
        yield ("wait", block_t["acceleration_us"] + block_t["pilot_catenae"] * per)
        length = yield ("read", 0)  # the leading length catena [COURS p.141]
        self.block_length = length
        start = self.machine.engine.now
        block = []
        for k in range(length + 1):  # the catenae, then the trailing length catena
            due = start + (k + 1) * per
            value = yield ("read", 0)
            if self.machine.engine.now > due:  # not supplied in time: bad recording (U-48)
                self.overruns += 1
                self._flag(18, 23)
            yield ("until", due)
            if k < length:
                block.append(value)
        yield ("wait", block_t["pilot_catenae"] * per + block_t["deceleration_us"])
        self._store_block(drive, block, rules)
        self._end_warning(drive, block_t)

    def _store_block(self, drive: TapeDrive, block, rules: dict) -> None:
        if rules["write_truncates_following_blocks"]:  # partial update impossible [COURS p.141]
            del drive.blocks[drive.position :]
        drive.blocks.insert(drive.position, block)
        drive.position += 1
        drive.centimetres += drive.length_cm(block)

    def _end_warning(self, drive: TapeDrive, block_t: dict) -> None:
        if drive.centimetres >= (block_t["reel_m"] - block_t["end_warning_m"]) * 100:
            self._flag(20, 23)  # approach of the end of the reel [COURS p.139]
