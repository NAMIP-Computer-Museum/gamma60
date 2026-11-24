"""J6 step 4: ``run`` goes through the whole chain; same trace as the plain assembly.

Acceptance criterion of J6 (ROADMAP): every program of ``tests/programs/`` passes through the
complete chain. The run through code B → subprogram → code C → code D2 → U.T. must give the
same trace, record by record, the same store and the same status as the plain assembly of J3.
"""

from pathlib import Path

import pytest

from gamma60 import codeb, data, machine
from gamma60.__main__ import main
from gamma60.elements.tape import TapeDrive
from gamma60.toolchain import chain
from gamma60.toolchain.assembler import AsmUnsupported
from gamma60.toolchain.distributor import ProcessingUnit

PROGRAMS = sorted(Path("tests/programs").glob("*.g60b"))
MEDIA = {  # reels of tests/programs/README.md
    "bande_continue": {10: "fichier_6_blocs.yaml"},
    "bande_continue_task": {10: "fichier_6_blocs.yaml"},
    "lecture_bande": {3: "bloc_128.yaml"},
}


def _run(path: Path, m: machine.Machine):
    for n, reel in MEDIA.get(path.stem, {}).items():
        m.tape_drives[n] = TapeDrive.load(n, Path("tests/media") / reel)
    result = m.run()
    store = [m.memory.raw(a) for a in range(m.memory.size)]
    return m.engine.trace, store, result.status, result.message, m.engine.now


@pytest.mark.parametrize("path", PROGRAMS, ids=lambda p: p.stem)
def test_same_trace_through_the_chain(path):
    text = path.read_text(encoding="utf-8")
    try:
        plain = machine.build(text, through_chain=False)
    except AsmUnsupported:
        pytest.skip("element not assembled yet (J8)")
    reference = _run(path, plain)
    assert _run(path, machine.build(text)) == reference
    # the U.T. alone, without its source (debug tables rebuilt from the U.T.)
    program = codeb.parse(text)
    profile = data.get_profile(program.profile)
    ut, _ = chain.processing_unit(program, profile, path.stem)
    ut = ProcessingUnit.from_json(ut.to_json())
    alone = machine.Machine(chain.machine_image(ut), profile)
    assert _run(path, alone) == reference


def test_ut_debug_view_keeps_labels_and_lines():
    program = codeb.parse(Path("tests/programs/fibonacci.g60b").read_text(encoding="utf-8"))
    ut, _ = chain.processing_unit(program, None, "fibonacci")
    image = chain.machine_image(ut)
    assert image.labels == program.labels
    for line in program.lines:
        rebuilt = image.line_at(line.address)
        assert (rebuilt.source_line, rebuilt.to, rebuilt.args) == (
            line.source_line,
            line.to,
            line.args,
        )


def test_cli_run_ut_same_output(tmp_path, capsys):
    src = Path("tests/programs/fibonacci.g60b").resolve().as_posix()
    sheet = tmp_path / "fib.g60c.yaml"
    sheet.write_text(f"articles: {{1: {{sp: '{src}'}}}}\ndistr: {{implantation: {{1: 256}}}}\n")
    assert main(["distribute", str(sheet)]) == 0
    capsys.readouterr()
    assert main(["run", src, "--dump", "RESULT", "4"]) == 0
    direct = capsys.readouterr().out
    assert main(["run", str(tmp_path / "fib.ut.json"), "--dump", "RESULT", "4"]) == 0
    assert capsys.readouterr().out == direct
    assert main(["run", str(tmp_path / "fib.ut.json"), "--seq"]) == 2


def test_endless_loop_reports_the_event_limit():
    m = machine.build("BOUCLE: 31    BOUCLE\n")
    result = m.run(max_events=1000)
    assert result.status == "limit" and "event limit reached (1000 events)" in result.message
