"""J3 machine: Program Distributor, ARIT and LOGI elements, timings, cross-check with J1."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

from gamma60 import debug, machine, seq
from gamma60.__main__ import main
from gamma60.catena import MASK15
from gamma60.data_distributor import INSTRUCTION

sys.path.insert(0, str(Path(__file__).parent))
from test_seq import _cases, _program_for

PROGRAMS = Path(__file__).parent / "programs"
HEAD = "; langue: en\nS:  ARIT\n    VIERGE\n"


def run(body: str, profile=None, **kw):
    result = machine.run_text(HEAD + body, profile, **kw)
    return result, result.machine


def mem(result, label, offset=0):
    return result.memory.read(result.image.labels[label] + offset)


# --- same results as the sequential interpreter of J1 ---------------------------------------------


@pytest.mark.parametrize(("kind", "ident", "mnemonic", "language"), list(_cases()))
def test_every_directive_matches_j1(kind, ident, mnemonic, language):
    text = _program_for(kind, ident, mnemonic, language)
    a, b = seq.run_text(text), machine.run_text(text)
    assert a.status == b.status == "halted", b.message
    data_addresses = [
        ln.address + j for ln in a.program.lines if ln.to in ("NUM", "ZONE") for j in range(ln.size)
    ]
    assert [a.memory.read(x) for x in data_addresses] == [b.memory.read(x) for x in data_addresses]
    assert a.units[kind].qualitative == b.machine.elements[kind].qualitative


@pytest.mark.parametrize(
    "name", ["test-arith01", "test-arith02-overflow", "test-arith03-underflow", "arit_logi"]
)
@pytest.mark.parametrize("profile", ["B61", "COURS"])
def test_programs_match_j1(name, profile):
    path = PROGRAMS / f"{name}.g60b"
    a, b = seq.run_file(path, profile), machine.run_file(path, profile)
    assert a.status == b.status
    assert a.message.split(":")[0] == b.message.split(":")[0]  # same source line
    for line in a.program.lines:
        if line.to == "NUM" and line.label:
            assert a.memory.read(line.address) == b.memory.read(line.address)


# --- timings ---------------------------------------------------------------------------------


ARIT_TIMES = {
    "B61": {"ADD": 200, "MUL": 350, "DIV": 550, "CAV": 150},
    "COURS": {"ADD": 100, "MUL": 300, "DIV": 600},
}


@pytest.mark.parametrize(
    ("profile", "mnemonic", "expected"),
    [(p, m, t) for p, times in ARIT_TIMES.items() for m, t in times.items()],
)
def test_arit_directive_lasts_the_published_time(profile, mnemonic, expected):
    fields = "- 0 1 -" if mnemonic == "CAV" else "N - 0 1 2"
    body = f"    L 0 X\n    L 1 Y\n    L 2 Z\n    {mnemonic} {fields}\n    STOP\nX: NUM +7\nY: NUM +2\nZ: NUM +0\n"
    result, m = run(body, profile)
    assert result.status == "halted"
    ((start, end, _),) = m.elements["arithmetic"].log
    assert end - start == expected  # « transferts compris » [B61 p.35-36 ; COURS]


@pytest.mark.parametrize(("profile", "cycle"), [("B61", 10), ("COURS", 11)])
def test_logi_follows_the_cours_formulas(profile, cycle):
    text = (
        "; langue: en\nS: LOGI\n VIERGE\n L 0 X\n TSK 0 0\n ADD 8 L\n DIV 8 0\n STOP\nX: ZONE 1\n"
    )
    m = machine.build(text, profile)
    m.memory.write(m.image.labels["X"], 3)  # K = 3, then L = 3: DIV gives 1, remainder 0
    result = m.run()
    assert result.status == "halted", result.message
    took = [end - start for start, end, _ in m.elements["logical"].log]
    # TSK: 6 + l/2 (l = 0); ADD: 12 (L kept); DIV: 24 + 12(24 - l) + 3 (stored) [COURS p.120-121]
    assert took == [6 * cycle, 12 * cycle, (24 + 12 * 16 + 3) * cycle]


def test_pd_reads_every_instruction_through_the_dd():
    _result, m = run("    L 0 X\n    31 NEXT\nNEXT: TRA N - 0 - P\n    STOP\nX: NUM +1\n")
    fetches = [r for r in m.engine.trace if r.what == "transfer" and r.get("nature") == INSTRUCTION]
    # cut, its blank catena (IAR <- cut + 1, a never branch), L, 31, TRA, then STOP
    assert len(fetches) == m.dp.executed == 6
    assert all(r.get("element") == "PD" for r in fetches)


# --- cuts ------------------------------------------------------------------------------------


def test_cuts_activate_and_release_elements():
    result = machine.run_file(PROGRAMS / "arit_logi.g60b")
    m = result.machine
    assert result.status == "halted"
    assert result.number("S").value == 42 and result.number("T").value == 84
    assert all(e.state == "idle" for e in m.elements.values())
    assert not any(m.dp.iar.busy)
    cuts = [r.get("element") for r in m.engine.trace if r.unit == "PD" and r.what == "cut"]
    assert cuts == ["ARIT", "LOGI", "ARIT"]


def test_join_never_reached_in_diagnostic_mode():
    body = "    LOGI 1\n    VIERGE\n    STOP\n"  # a join waiting for 2 arrivals, reached once
    assert run(body)[0].status == "halted"  # faithful: nothing to notice
    result, _ = run(body, mode="diagnostic")
    assert result.status == "blocked" and "join never reached at line 4: 1 of 2" in result.message


def test_decoded_directive_error():
    m = machine.build(HEAD + "X:  ZONE 1\n    STOP\n")
    m.memory.write(m.image.labels["X"], 0b1110 << 20)
    result = m.run()
    assert result.status == "incident" and "decoded directive error" in result.message


def test_diagnostic_mode_warns_before_the_incident():
    m = machine.build(HEAD + "X:  ZONE 1\n    STOP\n", mode="diagnostic")
    m.memory.write(m.image.labels["X"], 0b1110 << 20)
    m.run()
    assert any(r.what == "warning" for r in m.engine.trace)


def test_incident_message_gives_the_source_line():
    result = machine.run_file(PROGRAMS / "test-arith02-overflow.g60b")
    assert result.message.startswith("line 9: ARIT: exponent 80")


# --- address instructions and central directives [COURS p.53-60] ----------------------------------


def test_address_instructions_and_functions():
    body = "    L 0 100\n    A 0 5\n    S 0 2\n    P 0 OUT\n    L 1 PTR S\n    P 1 OUT2\n    STOP\nOUT: ZONE 1\nOUT2: ZONE 1\nPTR: ZONE 1\n"
    m = machine.build(HEAD + body)
    m.memory.write(m.image.labels["PTR"], 0o1234)
    result = m.run()
    assert mem(result, "OUT") == 103 and mem(result, "OUT2") == 0o1234


def test_branches_on_register_a():
    body = (
        "    L 0 X\n    L 1 Y\n    CAL - 0 1 -\n"  # X > Y: positions 1, 4, 6
        "    01 GREATER\n    FZ FLAG\n    STOP\nGREATER: FO FLAG\n    STOP\n"
        "X: NUM +9\nY: NUM +2\nFLAG: ZONE 1\n"
    )
    result, _ = run(body)
    assert mem(result, "FLAG") == 0xFFFFFF


def test_pi_stores_the_return_address():
    result, _ = run("    31 SUB\nBACK: STOP\nSUB: PI RET\n    STOP\nRET: ZONE 1\n")
    assert mem(result, "RET") == result.image.labels["BACK"]  # RAPP of the branch, via RSDP


def test_le_pe_ta_pa_tb_pb():
    body = "    LE 1\n    PE NUM\n    TA SRC\n    PA OUTA\n    TB SRC\n    PB OUTB\n    STOP\nSRC: ZONE 1\nNUM: ZONE 1\nOUTA: ZONE 1\nOUTB: ZONE 1\n"
    m = machine.build(HEAD + body)
    m.memory.write(m.image.labels["SRC"], 0xABCDEF)
    result = m.run()
    assert mem(result, "NUM") == 1
    assert mem(result, "OUTA") == mem(result, "OUTB") == 0xABCDEF


def test_b_register_15_bits():
    body = "    TB SRC\n    LB 100\n    AB 5\n    SB 2\n    PB OUT\n    CB 7\n    PA CMP\n    STOP\nSRC: ZONE 1\nOUT: ZONE 1\nCMP: ZONE 1\n"
    m = machine.build(HEAD + body)
    m.memory.write(m.image.labels["SRC"], 0xFF8000)  # 9 left bits set, 15 right bits at 0
    result = m.run()
    assert mem(result, "OUT") == 0xFF8000 | 103  # the 9 left bits are kept [COURS p.55]
    assert mem(result, "CMP") == (1 << 0) | (1 << 3) | (1 << 5)  # 103 > 7: >, >=, !=


def test_ab_carry_is_lost():
    result, _ = run("    LB 32767\n    AB 1\n    PB OUT\n    STOP\nOUT: ZONE 1\n")
    assert mem(result, "OUT") == 0


def test_sq_substitutes_the_quantity():
    body = "    LB PTR\n    SQ\n    PB OUT\n    STOP\nPTR: ZONE 1\nOUT: ZONE 1\n"
    m = machine.build(HEAD + body)
    m.memory.write(m.image.labels["PTR"], 0x123456)
    assert mem(m.run(), "OUT") == 0x123456


def test_si_executes_the_instruction_at_b():
    body = (
        "    LB T1\n    SI\n    PB OUT1\n"  # T1 is not a branch: go on after SI
        "    LB T2\n    SI\n    FZ OUT2\n    STOP\n"  # T2 is an effective branch: go to its target
        "AWAY: FO OUT2\n    STOP\n"
        "T1: LB 42\nT2: 31 AWAY\nOUT1: ZONE 1\nOUT2: ZONE 1\n"
    )
    result, _ = run(body)
    assert mem(result, "OUT1") & MASK15 == 42
    assert mem(result, "OUT2") == 0xFFFFFF


def test_switches_change_a_branch():
    body = "    SA BR\nBR: 00 YES\n    STOP\nYES: FO FLAG\n    SN BR\n    RR BR2\nBR2: 31 NO\n    STOP\nNO: FZ FLAG\n    STOP\nFLAG: ZONE 1\n"
    result, m = run(body)
    assert mem(result, "FLAG") == 0xFFFFFF  # BR forced to always, BR2 reversed to never
    assert (mem(result, "BR") >> 17) & 0b11111 == 0
    assert m.dp.regs.b == mem(result, "BR2")  # register B is implicit [COURS p.56]


def test_iteration_control():
    body = "    IC Q\n    IC Q\n    IC Q\n    PA A3\n    STOP\nQ: ZONE 2\nA3: ZONE 1\n"
    m = machine.build(HEAD + body)
    q = m.image.labels["Q"]
    m.memory.write(q, 2)
    m.memory.write(q + 1, 2)
    result = m.run()
    assert result.memory.read(q) == 2  # 2 → 1 → 0 → reloaded with N [COURS p.56-57]
    assert mem(result, "A3") == 1 << 13  # third call: n = 0, position 14 only


def test_counter_progression():
    body = "    CP CNT\n    PB OLD\n    STOP\nCNT: ZONE 1\nOLD: ZONE 1\n"
    m = machine.build(HEAD + body)
    m.memory.write(m.image.labels["CNT"], 0xFF8000 | 9)
    result = m.run()
    assert mem(result, "CNT") == 0xFF8000 | 10 and mem(result, "OLD") == 0xFF8000 | 9


# --- determinism and debugger ------------------------------------------------------------------


@pytest.mark.parametrize("profile", ["B61", "COURS"])
def test_same_input_same_trace(profile):
    a = machine.run_file(PROGRAMS / "arit_logi.g60b", profile).machine.engine.trace
    b = machine.run_file(PROGRAMS / "arit_logi.g60b", profile).machine.engine.trace
    assert a == b


@pytest.mark.parametrize("language", ["en", "fr"])
def test_debugger_does_not_change_the_run(language):
    out = io.StringIO()
    traced = machine.run_file(
        PROGRAMS / "arit_logi.g60b", observer=debug.RegisterTrace(debug.Names(language), out)
    )
    plain = machine.run_file(PROGRAMS / "arit_logi.g60b")
    assert traced.machine.engine.trace == plain.machine.engine.trace
    text = out.getvalue()
    assert ("cpar" if language == "en" else "RAPA") in text
    assert ("IAR" if language == "en" else "RAI") in text


def test_stepper_on_the_machine():
    out = io.StringIO()
    stepper = debug.Stepper(debug.Names("en"), io.StringIO("s\nr\nm START 2\nc\n"), out)
    result = machine.run_file(PROGRAMS / "test-arith01.g60b", observer=stepper)
    assert result.status == "halted"
    text = out.getvalue()
    assert "next:" in text and "cpar" in text and "START:" in text and "00256  START" in text


# --- command line ---------------------------------------------------------------------------------


def test_cli_run_on_the_machine(capsys):
    assert main(["run", str(PROGRAMS / "test-arith01.g60b"), "--profile", "COURS"]) == 0
    out = capsys.readouterr().out
    assert "COURS" in out and "ARIT  1 directive(s), 600 µs" in out


def test_cli_trace_variants(capsys):
    assert main(["run", str(PROGRAMS / "arit_logi.g60b"), "--trace"]) == 0
    assert "1111" in capsys.readouterr().out
    assert main(["run", str(PROGRAMS / "arit_logi.g60b"), "--trace=dd", "--names", "fr"]) == 0
    assert "instr." in capsys.readouterr().out


def test_cli_simu_runs_on_the_machine(capsys):
    assert main(["run", str(PROGRAMS / "forkjoin_tumlin.g60b")]) == 0
    assert "F          +43 1320|000000" in capsys.readouterr().out


def test_cli_asm(capsys):
    assert main(["asm", str(PROGRAMS / "test-arith01.g60b")]) == 0
    assert "00261  1111" in capsys.readouterr().out
    assert main(["asm", str(PROGRAMS / "namip_classement.g60b")]) == 2


def test_cli_program_error(capsys, tmp_path):
    bad = tmp_path / "bad.g60b"
    bad.write_text("; langue: en\n ARIT\n STOP\n", encoding="utf-8")
    assert main(["run", str(bad)]) == 2
    assert "error:" in capsys.readouterr().out


# --- memory dump -----------------------------------------------------------------------------------


def test_cli_dump_zones(capsys):
    args = ["run", str(PROGRAMS / "arit_logi.g60b"), "--dump", "S", "2", "--dump", "32767", "3"]
    assert main(args) == 0
    out = capsys.readouterr().out
    assert "memory 00281 - 00282:" in out
    assert "00281  S        424200  key" in out  # S = +42 (exponent 42, digits 42...)
    assert "32768  outside the store" in out


@pytest.mark.parametrize("seq_flag", [[], ["--seq"]])
def test_cli_dump_all(capsys, seq_flag):
    assert main(["run", str(PROGRAMS / "test-arith01.g60b"), *seq_flag, "--dump", "all"]) == 0
    out = capsys.readouterr().out
    assert "memory 00256 - 00268:" in out and "00267  R        413142" in out


def test_cli_dump_errors(capsys):
    assert main(["run", str(PROGRAMS / "test-arith01.g60b"), "--dump", "NOPE"]) == 2
    assert main(["run", str(PROGRAMS / "test-arith01.g60b"), "--dump", "R", "x"]) == 2
    assert "error:" in capsys.readouterr().out


def test_dump_lines_reads_without_checking_the_key():
    m = machine.build(HEAD + "    STOP\nX: ZONE 1\n")
    m.memory.poke_raw(m.image.labels["X"], m.memory.raw(0).__class__(0x123456, 0))
    (line,) = debug.dump_lines(m.image.program, m.memory, m.image.labels["X"], 1)
    assert "X        123456  key 0" in line  # a wrong key is shown, not raised


# --- a complete program: Fibonacci -------------------------------------------------------------


@pytest.mark.parametrize("profile", ["B61", "COURS"])
@pytest.mark.parametrize("n", [2, 3, 20])
def test_fibonacci(profile, n):
    from gamma60.number import Number

    text = (PROGRAMS / "fibonacci.g60b").read_text(encoding="utf-8")
    text = text.replace("BIN   20", f"BIN   {n}").replace("ZONE  40", f"ZONE  {2 * n}")
    result = machine.run_text(text, profile)
    assert result.status == "halted", result.message
    base = result.image.labels["RESULT"]
    terms = [
        Number.from_catenae(result.memory.read(base + 2 * k), result.memory.read(base + 2 * k + 1))
        for k in range(n)
    ]
    expected = [1, 1]
    while len(expected) < n:
        expected.append(expected[-1] + expected[-2])
    assert [t.value for t in terms] == expected[:n]
    assert len(result.machine.elements["arithmetic"].log) == 2 + (n - 2)  # 2 TRA, n - 2 ADD


@pytest.mark.parametrize("profile", ["B61", "COURS"])
def test_pi_by_machin(profile):
    from fractions import Fraction

    result = machine.run_file(PROGRAMS / "pi.g60b", profile)
    assert result.status == "halted", result.message
    pi = result.number("VALPI")
    assert str(pi) == "+41 3141|592653"  # 10 correct digits of 3.14159265358...
    assert abs(pi.value - Fraction(314159265358979, 10**14)) < Fraction(1, 10**9)
