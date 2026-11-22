"""J5: general comparator, drum, uniselectors and tape drives [COURS p.73-78, p.135-154]."""

from __future__ import annotations

import itertools
from fractions import Fraction
from pathlib import Path

import pytest

from gamma60 import code_a, machine
from gamma60.__main__ import main
from gamma60.codeb import ProgramError, parse
from gamma60.core.arit import fit
from gamma60.elements.tape import MARK, TapeDrive
from gamma60.number import Number
from gamma60.toolchain.assembler import assemble

PROGRAMS = Path(__file__).parent / "programs"
MEDIA = Path(__file__).parent / "media"


def bins(label: str, values) -> str:
    lines = [f"{label}: BIN {values[0]}"] + [f"    BIN {v}" for v in values[1:]]
    return "\n".join(lines) + "\n"


def log(m, key):
    return m.elements[key].log


# --- COMP [COURS p.74-78] ----------------------------------------------------------------------


def comp_run(op: str, x, y, z=None, length=None):
    length = length if length is not None else len(x)
    text = "; langue: en\nS: COMP\n    VIERGE\n    L 0 X\n    L 1 Y\n    L 2 Z\n"
    text += f"    {op} {length}\n    STOP\n" + bins("X", x) + bins("Y", y)
    text += bins("Z", z or [0] * len(x))
    m = machine.build(text)
    result = m.run()
    assert result.status == "halted", result.message
    comp = m.elements["comparator"]
    racs = [r - m.image.labels[k] for r, k in zip(m.dd.racs.of("COMP"), "XYZ", strict=True)]
    positions = {i + 1 for i in range(24) if comp.qualitative >> i & 1}
    ((start, end, _),) = comp.log
    return positions, racs, (end - start) // m.dd.cycle, m


def test_simple_compare_stops_at_the_first_inequality():
    positions, racs, n_cycles, _ = comp_run("OWC 1", [7, 5, 0, 0, 0], [7, 9, 0, 0, 0])
    assert positions == {2, 5, 6}  # <, <=, != (first operand smaller)
    assert racs[:2] == [4, 3]  # last catena compared + 3 (CAR 0), + 2 (CAR 1) [COURS p.76]
    assert n_cycles == 5 + 3 * 2  # 5 + 3n, n = effective length [COURS p.78]


@pytest.mark.parametrize("length", [1, 2])
def test_simple_compare_short_zones_end_on_the_length(length):
    positions, racs, _, _ = comp_run("OWC 1", [1, 1], [1, 1], length=length)
    assert 3 in positions and racs[:2] == [length, length]  # initial content + length


def test_simple_compare_zero_and_ones_tests():
    positions, _, _, _ = comp_run("OWC 2", [0, 0], [0, 0], [0, 0])
    assert {3, 4, 5, 7, 9} <= positions  # =, >=, <=, op1 zero, op2 zero (U-49)
    positions, _, _, _ = comp_run("OWC 1", [16777215], [16777215])
    assert {8, 10} <= positions  # both all ones


@pytest.mark.parametrize(
    ("x", "expected"),
    [(50, {1}), (5, {2, 7} - {7}), (20, {3, 6}), (10, {3, 4}), (30, {3, 5})],
)
def test_two_bounds_compare(x, expected):
    positions, racs, _, _ = comp_run("TWC", [0, x], [0, 10], [0, 30])
    assert positions == expected  # [COURS p.77]
    assert racs == [2, 2, 2]  # length 2: initial content + length


def test_erase_and_transfer():
    _, racs, n_cycles, m = comp_run("DEL", [1, 2, 3], [0, 0, 0])
    x = m.image.labels["X"]
    assert [m.memory.read(x + k) for k in range(3)] == [0, 0, 0]
    assert racs[0] == 3 and n_cycles == 2 + 3  # EFL: 2 + n
    _, racs, n_cycles, m = comp_run("TSS 1", [4, 5, 6], [0, 0, 0])
    y = m.image.labels["Y"]
    assert [m.memory.read(y + k) for k in range(3)] == [4, 5, 6]
    assert racs[:2] == [3, 3] and n_cycles == 2 + 3 * 3  # TRR: 2 + 3n


def test_length_zero_does_nothing():
    positions, racs, _, _ = comp_run("OWC 1", [1], [2], length=0)
    assert positions == set() and racs[:2] == [0, 0]  # [COURS p.75]


def test_comp_assembly_checks():
    with pytest.raises(ProgramError):
        assemble(parse("; langue: en\n COMP\n VIERGE\n OWC 300\n STOP\n"))
    with pytest.raises(ProgramError):
        assemble(parse("; langue: en\n COMP\n VIERGE\n OWC 5\n STOP\n"))  # C.C. 1 or 2


# --- drum [COURS p.152-154] ------------------------------------------------------------------------


def drum_program(address: int, count: int, values) -> str:
    return (
        "; langue: en\nS: DRUM 1\n    VIERGE\n    L 0 SRC\n"
        f"    DAO {address}\n    TCD {count}\n    L 0 DST\n    DAO {address}\n    TDC {count}\n"
        "    STOP\n" + bins("SRC", values) + f"DST: ZONE {count}\n"
    )


def test_drum_address_in_code_a():
    image = assemble(parse("; langue: en\n DRUM 1\n VIERGE\n DAO 17400\n STOP\n"))
    char = code_a.decode(image.words[image.program.origin + 2]).characteristic
    assert code_a.decode_free("drum", char)[4] == (87 << 8) | 0  # 17400 = track 87, position 0
    cut = code_a.decode(image.words[image.program.origin])
    assert cut.x == 100  # drum 1 = element 100 [COURS p.51]


def test_drum_write_then_read():
    m = machine.build(drum_program(1000, 8, [11, 22, 33, 44, 55, 66, 77, 88]))
    assert m.run().status == "halted"
    drum = m.elements["drum1"]
    assert drum.store[1000:1008] == [11, 22, 33, 44, 55, 66, 77, 88]
    dst = m.image.labels["DST"]
    assert [m.memory.read(dst + k) for k in range(8)] == [11, 22, 33, 44, 55, 66, 77, 88]
    assert drum.rae == (5 << 8) | 8 and drum.qualitative == drum.rae  # final RAE [COURS p.153]
    assert drum.lost_revolutions == 0


def test_drum_catenae_follow_the_rotation():
    m = machine.build(drum_program(0, 4, [1, 2, 3, 4]))
    m.run()
    times = [r.time for r in m.engine.trace if r.what == "transfer" and r.get("element") == "DRUM1"]
    write, read = times[:4], times[4:]
    # the first catena is fetched ahead; the next ones follow the positions, ~98 us apart (U-46)
    assert all(90 <= b - a <= 110 for a, b in itertools.pairwise(write[1:]))
    assert all(90 <= b - a <= 110 for a, b in itertools.pairwise(read))
    assert read[0] - write[1] >= 19_000  # the same positions come back one revolution later


def test_drum_track_switch():
    m = machine.build(drum_program(199, 3, [7, 8, 9]))
    m.run()
    drum = m.elements["drum1"]
    assert drum.store[199:202] == [7, 8, 9]  # positions 199, then track 1 positions 0 and 1
    assert drum.rae == (1 << 8) | 2  # RAE: 199 → 256 (+ 57) [COURS p.154]


def test_drum_beyond_the_last_track_is_an_incident():
    result = machine.run_text(drum_program(25599, 2, [1, 2]))
    assert result.status == "incident"


def test_drum_and_arit_overlap():
    result = machine.run_file(PROGRAMS / "tambour_arit.g60b")
    m = result.machine
    assert result.status == "halted"
    copy = m.image.labels["COPIE"]
    assert [m.memory.read(copy + k) for k in range(8)] == [11, 22, 33, 44, 55, 66, 77, 88]
    drum = log(m, "drum1")
    divisions = [e for e in log(m, "arithmetic") if e[2] == "divide"]
    assert len(divisions) == 30
    assert all(d[1] < drum[-1][1] for d in divisions)  # all done while the drum works
    work = sum(e[1] - e[0] for e in drum + divisions)
    assert m.engine.now < work  # shorter than the two branches one after the other


# --- tapes [COURS p.135-151] ----------------------------------------------------------------------------


READ = """; langue: en
S:  MATA 1
    VIERGE
    {prep} 3
    L 0 {start}
    TRA
    STOP
T:  ZONE 127
LAST: ZONE 1
"""


def tape_machine(text: str, reels: dict) -> machine.Machine:
    m = machine.build(text)
    for number, blocks in reels.items():
        if isinstance(blocks, TapeDrive):
            blocks.number = number
            m.tape_drives[number] = blocks
        else:
            m.tape_drives[number] = TapeDrive(number, list(blocks))
    return m


BLOCK = list(range(1, 129))


def zone(m, label, n):
    a = m.image.labels[label]
    return [m.memory.read(a + k) for k in range(n)]


def test_read_forward_one_block():
    m = tape_machine(READ.format(prep="REF", start="T"), {3: [BLOCK]})
    result = m.run()
    assert result.status == "halted"
    assert zone(m, "T", 128) == BLOCK
    ((start, end, _),) = [e for e in log(m, "uniselector1") if e[2] == "read_transfer"]
    per = 190  # B61
    assert end - start == pytest.approx(5000 + 5000 + (128 + 4) * per, abs=40)  # U-47
    assert m.tape_drives[3].position == 1


def test_read_backward_gives_the_same_image():
    reel = TapeDrive(3, [BLOCK], position=1)  # after the block: read it backwards
    m = tape_machine(READ.format(prep="REB", start="LAST"), {3: reel})
    assert m.run().status == "halted"
    assert zone(m, "T", 128) == BLOCK  # the CAR goes back [COURS p.141]
    assert m.tape_drives[3].position == 0


def test_tape_mark_sets_position_19():
    text = READ.format(prep="REF", start="T").replace(
        "    STOP\n", "    19 MARK\n    STOP\nMARK: FO T\n    STOP\n", 1
    )
    m = tape_machine(text, {3: [MARK, BLOCK]})
    assert m.run().status == "halted"
    assert m.memory.read(m.image.labels["T"]) == 0xFFFFFF  # branch 19 taken; nothing transferred


def test_write_then_rewind_then_read():
    text = (
        "; langue: en\nS: MATA 1\n    VIERGE\n    WRI 4\n    L 0 OUT\n    TRA\n"
        "    SPO 4\n    REF 4\n    L 0 IN\n    TRA\n    STOP\n"
        + bins("OUT", [16, *range(100, 116), 16])
        + "IN: ZONE 16\n"
    )
    m = tape_machine(text, {4: []})
    result = m.run()
    assert result.status == "halted", result.message
    assert m.tape_drives[4].blocks == [list(range(100, 116))]
    assert zone(m, "IN", 16) == list(range(100, 116))
    # the execution directive waits for the end of the rewinding [COURS p.146]
    service = next(r for r in m.engine.trace if r.what == "service")
    read = [e for e in log(m, "uniselector1") if e[2] == "read_transfer"][-1]
    assert read[1] > service.get("until")


def test_write_protected_reel():
    text = (
        "; langue: en\nS: MATA 1\n    VIERGE\n    WRI 4\n    L 0 OUT\n    TRA\n"
        "    16 PROT\n    STOP\nPROT: FO FLAG\n    STOP\n"
        + bins("OUT", [16, *range(16), 16])
        + "FLAG: ZONE 1\n"
    )
    m = tape_machine(text, {4: TapeDrive(4, [], write_protected=True)})
    assert m.run().status == "halted"
    assert m.memory.read(m.image.labels["FLAG"]) == 0xFFFFFF  # position 16 (U-48)
    assert m.tape_drives[4].blocks == []


def test_drive_not_wired_to_the_uniselector():
    result = tape_machine(READ.format(prep="REF", start="T").replace("REF 3", "REF 30"), {}).run()
    assert result.status == "incident" and "not connected" in result.message  # [B61 p.54]


def test_lecture_bande_program():
    m = machine.build((PROGRAMS / "lecture_bande.g60b").read_text(encoding="utf-8"))
    m.tape_drives[3] = TapeDrive.load(3, MEDIA / "bloc_128.yaml")
    assert m.run().status == "halted"
    assert zone(m, "TAMPON", 128) == BLOCK


# --- the NAM-IP sheet (extract, completed by a STOP) --------------------------------------------------


@pytest.mark.parametrize(
    ("c", "positions"), [(50, [10, 30, 50]), (20, [10, 20, 30]), (5, [5, 30, 10])]
)
def test_namip_sheet(c, positions):
    text = (PROGRAMS / "namip_classement.g60b").read_text(encoding="utf-8") + "053     STOP\n"
    m = machine.build(text, "COURS")
    end = m.image.program.end

    def put(offset, value):
        first, second = fit(Fraction(value), None)[0].to_catenae()
        m.memory.write(end + offset, first)
        m.memory.write(end + offset + 1, second)

    def number(offset):
        return Number.from_catenae(
            m.memory.read(end + offset), m.memory.read(end + offset + 1)
        ).value

    put(0, c)  # M0-3 = C, M6-9 = A, M10-13 = B (header of the transcription)
    put(6, 10)
    put(10, 30)
    assert m.run().status == "halted"
    assert number(4) == c + 40  # the sum is always right
    # sorted when C > A, B or A < C < B; for C < A, B the sheet leaves B 2nd, A 3rd (its note)
    assert [number(6), number(10), number(14)] == positions


# --- command line ------------------------------------------------------------------------------------


def test_cli_tape_and_dump(capsys):
    args = ["run", str(PROGRAMS / "lecture_bande.g60b"), "--tape", f"3={MEDIA / 'bloc_128.yaml'}"]
    assert main([*args, "--dump-tape", "3", "--dump", "TAMPON", "2"]) == 0
    out = capsys.readouterr().out
    assert "drive 3: 3 block(s), position 1" in out and "tape mark" in out
    assert "TAMPON   000001" in out


def test_cli_drum_contents(capsys, tmp_path):
    contents = tmp_path / "drum.yaml"
    contents.write_text("1000: [5, 6]\n", encoding="utf-8")
    program = tmp_path / "read.g60b"
    program.write_text(
        "; langue: en\nS: DRUM 1\n    VIERGE\n    L 0 DST\n    DAO 1000\n    TDC 2\n    STOP\n"
        "DST: ZONE 2\n",
        encoding="utf-8",
    )
    assert main(["run", str(program), "--drum", f"1={contents}", "--dump", "DST", "2"]) == 0
    out = capsys.readouterr().out
    assert "000005" in out and "000006" in out


def test_cli_media_errors(capsys):
    args = ["run", str(PROGRAMS / "lecture_bande.g60b")]
    assert main([*args, "--tape", "99=x.yaml"]) == 2
    assert main([*args, "--drum", "9=x.yaml"]) == 2
    assert main([*args, "--config", "rtt_1963", "--tape", f"3={MEDIA / 'bloc_128.yaml'}"]) == 0
    assert "no drive 99" in capsys.readouterr().out


def test_gantt_shows_the_drum():
    from gamma60 import debug, gantt

    m = machine.run_file(PROGRAMS / "tambour_arit.g60b").machine
    lines = gantt.Gantt(m, debug.Names("en")).by_element()
    assert any(line.startswith("DRUM1") and "[TCD" in line for line in lines)


def test_trace_shows_the_new_registers():
    import io

    from gamma60 import debug

    out = io.StringIO()
    m = machine.build(
        (PROGRAMS / "tambour_arit.g60b").read_text(encoding="utf-8"),
        observer=debug.RegisterTrace(debug.Names("fr"), out),
    )
    m.run()
    text = out.getvalue()
    assert "TAMB1" in text and "RAE" in text  # the drum and its address register, in French
    out = io.StringIO()
    m = tape_machine(READ.format(prep="REF", start="T"), {3: [BLOCK]})
    m.observer = debug.RegisterTrace(debug.Names("en"), out)
    m.run()
    assert (
        "MATA1" in out.getvalue()
        and "blr" in out.getvalue()
        and "read_forward #3" in out.getvalue()
    )
