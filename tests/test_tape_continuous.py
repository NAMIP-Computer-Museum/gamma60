"""J5b: uniselectors as double elements, continuous tape mode [COURS p.138, p.147-150; B61 p.54]."""

from __future__ import annotations

import itertools
from pathlib import Path

import pytest

from gamma60 import debug, machine
from gamma60.elements.tape import MARK, TapeDrive
from gamma60.gantt import Gantt

PROGRAMS = Path(__file__).parent / "programs"
MEDIA = Path(__file__).parent / "media"
BLOCK = list(range(100, 150))
PER = 190  # µs per catena, B61
BLOCK_US = (len(BLOCK) + 2 + 4) * PER  # 2 length catenae, 2 pilot zones of 2 catenae
GAP_US = int(2 / 190 * 1e6)  # 2 cm at 1.90 m/s (U-50)


def zone(m, label, n):
    a = m.image.labels[label]
    return [m.memory.read(a + k) for k in range(n)]


def continuous_run(mode: str = "faithful"):
    m = machine.build((PROGRAMS / "bande_continue.g60b").read_text(encoding="utf-8"), mode=mode)
    m.tape_drives[10] = TapeDrive.load(10, MEDIA / "fichier_6_blocs.yaml")
    return m, m.run()


def test_two_elements_per_uniselector():
    m = machine.build("; langue: en\nS: STOP\n")
    one, two = m.elements["uniselector1"], m.elements["uniselector2"]
    assert one.shared is two.shared and one.number + 1 == two.number  # [COURS p.147]
    assert m.elements["uniselector3"].shared is not one.shared


def test_deru_n_names_the_element_n():
    m = machine.build("; langue: fr\nS: DERU 2\n    VIERGE\n    STOP\n")
    assert m.run().status == "halted"
    assert m.image.labels["S"] is not None
    # element 2 is the second element of uniselector 1 (U-44)
    assert m.elements["uniselector2"].number == m.elements["uniselector1"].number + 1


def test_bande_continue_reads_the_file_without_stopping():
    m, result = continuous_run()
    assert result.status == "halted", result.message
    unit = m.elements["uniselector1"].shared
    # 6 blocks, the mark and the block after it: 8 blocks, one stop at the very end
    assert (unit.handovers, unit.stops) == (7, 1)
    assert m.tape_drives[10].position == 8
    assert zone(m, "ZA", 50)[0] == 5000 and zone(m, "ZB", 50)[0] == 9000


def read_ends(m, *names):
    return sorted(e[1] for name in names for e in m.elements[name].log if e[2] == "read_transfer")


def steps(ends):
    return [b - a for a, b in itertools.pairwise(ends)]


def test_handover_lets_the_space_pass_at_full_speed():
    m, _ = continuous_run()
    gaps = steps(read_ends(m, "uniselector1", "uniselector2"))
    mark_us = (16 + 4) * PER  # 16 zero catenae and the pilot zones [COURS p.137]
    # consecutive blocks follow each other: the 2 cm space at 1.90 m/s, then the block; the
    # last one ends with the deceleration (the tape stops)
    assert gaps == pytest.approx(
        [GAP_US + BLOCK_US] * 5 + [GAP_US + mark_us, GAP_US + BLOCK_US + 5000], abs=2 * PER
    )


def test_continuous_is_faster_than_discontinuous():
    discontinuous = """; langue: en
S:  MATA 1
    VIERGE
    REF 10
L:  L 0 Z
    TRA
    19 FIN
    31 L
FIN: STOP
Z:  ZONE 50
"""
    m = machine.build(discontinuous)
    m.tape_drives[10] = TapeDrive.load(10, MEDIA / "fichier_6_blocs.yaml")
    slow = m.run()
    assert slow.status == "halted"
    assert m.elements["uniselector1"].shared.handovers == 0
    slow_steps = steps(read_ends(m, "uniselector1"))[:5]
    cm, _ = continuous_run()
    fast_steps = steps(read_ends(cm, "uniselector1", "uniselector2"))[:5]
    # discontinuous: deceleration 5 ms, acceleration 5 ms and the rest of the space (U-47);
    # continuous: the whole space at full speed; 5 ms saved per block
    for slow_step, fast_step in zip(slow_steps, fast_steps, strict=True):
        assert slow_step - fast_step == pytest.approx(5000, abs=2 * PER)


PAIR = """; langue: en
S:  MATA 1
    VIERGE
    REF 10
    SIMU B2
    VIERGE
    MATA 1
    VIERGE
    L 0 Z1
    TRA
    18 BAD1
    19 MRK1
    31 J
BAD1: FO F1
    31 J
MRK1: FO M1
    31 J
B2: MATA 2
    VIERGE
    L 0 Z2
    TRA
    18 BAD2
    31 J
BAD2: FO F2
    31 J
J:  ARIT 1
    VIERGE
    STOP
F1: ZONE 1
F2: ZONE 1
M1: ZONE 1
Z1: ZONE 50
Z2: ZONE 50
"""


def pair_run(blocks):
    m = machine.build(PAIR)
    m.tape_drives[10] = TapeDrive(10, list(blocks))
    return m, m.run()


def test_bad_reading_blocks_the_waiting_directive():
    m, result = pair_run([])  # nothing recorded: bad reading (U-48)
    assert result.status == "halted", result.message
    assert m.memory.read(m.image.labels["F1"]) == 0xFFFFFF
    assert m.memory.read(m.image.labels["F2"]) == 0xFFFFFF  # blocked: 18 [COURS p.149]
    unit = m.elements["uniselector1"].shared
    assert (unit.handovers, unit.stops) == (0, 1)
    assert m.tape_drives[10].position == 0  # the blocked directive did not move the tape


def test_tape_mark_does_not_block_the_waiting_directive():
    m, result = pair_run([MARK, BLOCK])
    assert result.status == "halted", result.message
    assert m.memory.read(m.image.labels["M1"]) == 0xFFFFFF  # position 19
    assert m.memory.read(m.image.labels["F2"]) == 0
    assert zone(m, "Z2", 50) == BLOCK  # read after the mark, tape still running [COURS p.150]
    assert m.elements["uniselector1"].shared.handovers == 1


def test_parked_time_is_shown_in_the_gantt():
    m, _ = continuous_run()
    assert m.elements["uniselector2"].parked
    lines = Gantt(m, debug.Names("en")).by_element()
    row = next(line for line in lines if line.startswith("MATA2"))
    assert ":" in row


@pytest.mark.parametrize("mode", ["faithful", "diagnostic"])
def test_preparatory_directive_during_a_transfer(mode):
    text = PAIR.replace("B2: MATA 2\n    VIERGE\n", "B2: MATA 2\n    VIERGE\n    REF 10\n", 1)
    m = machine.build(text, mode=mode)
    m.tape_drives[10] = TapeDrive(10, [BLOCK, BLOCK])
    m.run()
    warned = any(r.what == "warning" and "preparatory" in r.get("text") for r in m.engine.trace)
    assert warned == (mode == "diagnostic")  # it disturbs the other element [COURS p.149]


def test_bande_continue_task_processes_each_block_while_reading_the_next():
    m = machine.build((PROGRAMS / "bande_continue_task.g60b").read_text(encoding="utf-8"))
    m.tape_drives[10] = TapeDrive.load(10, MEDIA / "fichier_6_blocs.yaml")
    result = m.run()
    assert result.status == "halted", result.message
    # the 6 blocks of the file, each summed by LOGI on its own branch; the block after the
    # mark is read (in ZB) but belongs to the next file: not processed [COURS p.150]
    expected = sum(sum(j * 1000 + k for k in range(50)) for j in (1, 2, 3, 4, 5, 6))
    assert m.memory.read(m.image.labels["TOTAL"]) == expected == 1_057_350
    assert m.memory.read(m.image.labels["NBLOC"]) == 6
    assert zone(m, "ZB", 50)[0] == 9000
    # the processing is shorter than a block: the tape still never stops [COURS p.139]
    unit = m.elements["uniselector1"].shared
    assert (unit.handovers, unit.stops) == (7, 1)


def test_sequences_sharing_a_label_leave_a_blank_when_none_lives():
    m = machine.build((PROGRAMS / "bande_continue_task.g60b").read_text(encoding="utf-8"))
    m.tape_drives[10] = TapeDrive.load(10, MEDIA / "fichier_6_blocs.yaml")
    m.run()
    lines = Gantt(m, debug.Names("en")).by_sequence()
    row = next(line for line in lines if line.startswith("TRAIT"))[7:]
    body = row.strip()
    # 6 processings, each ending by STOP, then nothing: the block after the mark is not processed
    assert body.count("S") == 6
    assert body.endswith("S")
    lines_elem = Gantt(m, debug.Names("en")).by_element()
    logi = next(line for line in lines_elem if line.startswith("LOGI"))[7:]
    assert logi.rstrip().endswith(".")  # LOGI rests at the end
