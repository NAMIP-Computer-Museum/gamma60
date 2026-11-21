"""Debugger (J2, step 1): names from registers.yaml, register trace, step by step."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from gamma60 import data, debug, seq
from gamma60.__main__ import main

FORKJOIN = Path(__file__).parent / "programs" / "forkjoin_tumlin.g60b"
LOGI_PROGRAM = """; langue: en
START:  LOGI
        VIERGE
        L     0     X
        TSK   0     0
        TSL   0     0
        FOL   24    L
        STOP
X:      ZONE  1
"""


def interpreter(path=FORKJOIN, observer=None, profile=None):
    program = seq.parse(Path(path).read_text(encoding="utf-8"))
    return seq.Interpreter(program, data.get_profile(profile), observer=observer)


# --- names ---------------------------------------------------------------------------------


def test_labels_follow_the_case_convention():
    en, fr = debug.Names("en"), debug.Names("fr")
    assert (en.label("rapa"), fr.label("rapa")) == ("cpar", "RAPA")
    assert (en.label("z"), fr.label("z")) == ("z", "Z")
    assert (en.label("rac", 2), fr.label("rac", 2)) == ("CAR2", "RAC2")
    assert (en.label("chain_head_tail", 1), fr.label("chain_head_tail", 1)) == ("i2", "C")
    assert en.label("pd_chain", 1) == "pdc1"


def test_unknown_language_is_rejected():
    with pytest.raises(ValueError):
        debug.Names("de")


def test_legend_tells_the_origin_of_each_label():
    en = debug.Names("en").legend(["rapa", "rai"])
    assert "cpar" in en[0] and "emulator label" in en[0] and "fr: RAPA" in en[0]
    assert "IAR" in en[1] and "attested name" in en[1] and "B61 p.22" in en[1]
    fr = debug.Names("fr").legend(["rapa"])
    assert "RAPA" in fr[0] and "Programme Actuel" in fr[0] and "nom attesté" in fr[0]


# --- snapshot and determinism -----------------------------------------------------------------


@pytest.mark.parametrize("language", ["en", "fr"])
def test_snapshot_uses_display_names(language):
    interp = interpreter()
    interp.run()
    state = debug.snapshot(interp, debug.Names(language))
    car = "CAR" if language == "en" else "RAC"
    qual = "qcr" if language == "en" else "rcq"
    arit = state["ARIT"]
    assert {"P", "S", "O", qual, f"{car}0", f"{car}3"} <= set(arit)
    assert "(= 132)" in arit["P"]  # last operation: F = A x D [forkjoin_tumlin]
    assert state["CU"]["A"] == "{9}"  # result > 0


@pytest.mark.parametrize("language", ["en", "fr"])
@pytest.mark.parametrize("profile", ["B61", "COURS"])
def test_observer_does_not_change_the_run(language, profile):
    plain = interpreter(profile=profile).run()
    out = io.StringIO()
    traced = interpreter(
        profile=profile, observer=debug.RegisterTrace(debug.Names(language), out)
    ).run()
    assert traced.trace == plain.trace
    assert [traced.memory.raw(a) for a in range(64)] == [plain.memory.raw(a) for a in range(64)]
    again = io.StringIO()
    interpreter(profile=profile, observer=debug.RegisterTrace(debug.Names(language), again)).run()
    assert out.getvalue() == again.getvalue()  # same input, same trace


def test_register_trace_marks_changed_registers():
    out = io.StringIO()
    interpreter(observer=debug.RegisterTrace(debug.Names("en"), out)).run()
    lines = out.getvalue().splitlines()
    add = next(i for i, text in enumerate(lines) if text.endswith("ADD N - 0 1 2"))
    regs = "\n".join(lines[add + 1 : add + 4])
    assert "P* +42 1100|000000 (= 11)" in regs and "A* {9}" in regs and "CAR3 00000" in regs


def test_register_trace_of_logi_shows_bits(tmp_path):
    prog = tmp_path / "logi.g60b"
    prog.write_text(LOGI_PROGRAM, encoding="utf-8")
    out = io.StringIO()
    interpreter(prog, observer=debug.RegisterTrace(debug.Names("en"), out)).run()
    text = out.getvalue()
    assert "L* 111111 111111 111111 111111" in text  # FOL 24: all 24 bits of L set to 1
    assert "K 000000 000000 000000 000000" in text


def test_register_trace_reports_an_incident(tmp_path):
    prog = Path(__file__).parent / "programs" / "test-arith02-overflow.g60b"
    out = io.StringIO()
    result = interpreter(prog, observer=debug.RegisterTrace(debug.Names("fr"), out)).run()
    assert result.status == "incident"
    assert "! line" in out.getvalue() and "exponent 80" in out.getvalue()


# --- step by step ----------------------------------------------------------------------------


def stepper(commands: str, language="en"):
    out = io.StringIO()
    return debug.Stepper(debug.Names(language), io.StringIO(commands), out), out


def test_step_breakpoint_registers_memory_and_quit():
    s, out = stepper("b I3\nc\nr\nm F 2\nm NOPE\nq\n")
    with pytest.raises(debug.Quit):
        interpreter(observer=s).run()
    text = out.getvalue()
    assert "break at 00016" in text
    assert "P +42 1100|000000 (= 11)" in text  # after D = D + E, before F = A x D
    assert "  F        000000" in text  # F not computed yet
    assert "? unknown address or label" in text


def test_step_unknown_label_and_help_in_french():
    s, out = stepper("b NULLE\nh\nq\n", "fr")
    with pytest.raises(debug.Quit):
        interpreter(observer=s).run()
    text = out.getvalue()
    assert "étiquette inconnue" in text and "point d'arrêt" in text


def test_step_end_of_input_continues_to_the_end():
    s, _ = stepper("s\ns\n")
    result = interpreter(observer=s).run()
    assert result.status == "halted" and result.number("F").value == 132


def test_step_does_not_change_the_run():
    s, _ = stepper("s\nr\nb I3\nc\nl\ns\nc\n")
    assert interpreter(observer=s).run().trace == interpreter().run().trace


def test_delete_breakpoint():
    s, out = stepper("b I3\nd I3\nc\n")
    interpreter(observer=s).run()
    assert "break at" not in out.getvalue()


# --- command line ----------------------------------------------------------------------------


def test_cli_trace_regs_in_french(capsys):
    assert main(["run", str(FORKJOIN), "--trace=regs", "--names", "fr"]) == 0
    text = capsys.readouterr().out
    assert "registres (fr)" in text and "RAC0" in text and "rcq" in text


def test_cli_step_quit(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("q\n"))
    assert main(["run", str(FORKJOIN), "--step"]) == 1
    assert "status: quit" in capsys.readouterr().out


def test_cli_trace_steps_unchanged(capsys):
    assert main(["run", str(FORKJOIN), "--trace"]) == 0
    assert "SIMU I2 R" in capsys.readouterr().out
