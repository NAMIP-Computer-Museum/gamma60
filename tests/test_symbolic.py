"""J6 step 5: symbolic debugging (labels, LABEL+k, ARTICLE.LABEL, breakpoints) and disasm."""

import io
from pathlib import Path

import pytest

from gamma60 import codeb, debug, machine
from gamma60.__main__ import main
from gamma60.toolchain import chain, disassembler
from gamma60.toolchain.assembler import AsmUnsupported
from gamma60.toolchain.distributor import distribute
from gamma60.toolchain.linker import link

PROGRAMS = sorted(Path("tests/programs").glob("*.g60b"))
FIB = Path("tests/programs/fibonacci.g60b")

A = "; langue: fr\n        REP   DEBUT\nDEBUT:  31    ?SUITE\n"
B = "; langue: fr\n        REP   ICI\nICI:    31    ?FIN\n"
SHEET = """
articles: {1: {sp: a.g60b}, 2: {sp: b.g60b}}
assembl: [1.X1 = 2.R1]
distr: {implantation: {1: 400}, sortie: 2.X1}
"""


def _two_articles(tmp_path: Path):
    (tmp_path / "a.g60b").write_text(A, encoding="utf-8")
    (tmp_path / "b.g60b").write_text(B, encoding="utf-8")
    (tmp_path / "p.g60c.yaml").write_text(SHEET, encoding="utf-8")
    assert main(["distribute", str(tmp_path / "p.g60c.yaml")]) == 0
    return tmp_path / "p.ut.json"


def test_symbolic_and_resolve():
    program = codeb.parse(FIB.read_text(encoding="utf-8"))
    boucle = program.labels["BOUCLE"]
    assert debug.symbolic(program, boucle) == "BOUCLE"
    assert debug.symbolic(program, boucle + 2) == "BOUCLE+2"
    assert debug.symbolic(program, 32000) == ""  # outside the program
    assert debug.resolve_address(program, "BOUCLE+2") == boucle + 2
    assert debug.resolve_address(program, "BOUCLE-1") == boucle - 1
    assert debug.resolve_address(program, "300") == 300


def test_qualified_labels_of_several_articles(tmp_path):
    prog = link(_write_ambiguous(tmp_path))
    program, _ = chain.program_from_ut(distribute(prog, {}, "p"))
    assert debug.resolve_address(program, "a.DEBUT") == 400
    assert debug.resolve_address(program, "ICI") == program.labels["b.ICI"]  # unique
    with pytest.raises(ValueError, match="ambiguous label 'X'"):
        debug.resolve_address(program, "X")


def _write_ambiguous(tmp_path):
    (tmp_path / "a.g60b").write_text(A + "X:      STOP\n", encoding="utf-8")
    (tmp_path / "b.g60b").write_text(B + "X:      STOP\n", encoding="utf-8")
    (tmp_path / "p.g60c.yaml").write_text(SHEET, encoding="utf-8")
    return tmp_path / "p.g60c.yaml"


def test_trace_shows_symbol_and_source_line():
    out = io.StringIO()
    m = machine.build(
        FIB.read_text(encoding="utf-8"), observer=debug.InstructionTrace(debug.Names("fr"), out)
    )
    m.run()
    first = out.getvalue().splitlines()[0]
    assert "00256 START" in first and "10: START:  ARIT" in first


def test_break_on_a_label_stops_at_its_address(capsys, monkeypatch):
    """Acceptance criterion of J6: a breakpoint on a code B label stops at the right address."""
    program = codeb.parse(FIB.read_text(encoding="utf-8"))
    monkeypatch.setattr("sys.stdin", io.StringIO("q\n"))
    assert main(["run", str(FIB), "--break", "BOUCLE+2"]) == 1
    out = capsys.readouterr().out
    assert f"break at {program.labels['BOUCLE'] + 2:05d}" in out
    assert "BOUCLE+2" in out and "25: ADD" in out
    assert main(["run", str(FIB), "--break", "NULLE"]) == 2


def test_break_on_article_label_of_a_processing_unit(tmp_path, capsys, monkeypatch):
    ut = _two_articles(tmp_path)
    capsys.readouterr()
    monkeypatch.setattr("sys.stdin", io.StringIO("c\n"))
    assert main(["run", str(ut), "--break", "b.ICI"]) == 0
    out = capsys.readouterr().out
    assert "00401 b.ICI" in out and "status: halted" in out


def test_dump_shows_label_plus_offset(capsys):
    assert main(["run", str(FIB), "--dump", "RESULT+1", "2"]) == 0
    out = capsys.readouterr().out
    assert "RESULT+1" in out and "RESULT+2" in out


@pytest.mark.parametrize("path", PROGRAMS, ids=lambda p: p.stem)
def test_disasm_gives_back_the_mnemonics(path):
    program = codeb.parse(path.read_text(encoding="utf-8"))
    try:
        ut, _ = chain.processing_unit(program, None, path.stem)
    except AsmUnsupported:
        pytest.skip("element not assembled yet (J8)")
    source = disassembler.source_of(ut)
    lines = {a: text for a, _, _, text in disassembler.disassemble(source)}
    for line in program.lines:
        if line.to in codeb.DATA:
            continue
        assert lines[line.address].split()[0] == line.to, (line.text, lines[line.address])


def test_disasm_files_and_language(tmp_path, capsys):
    ut = _two_articles(tmp_path)
    capsys.readouterr()
    assert main(["disasm", str(ut)]) == 0
    out = capsys.readouterr().out
    assert "a.DEBUT:" in out and "31    b.ICI" in out and "FIN_UT:" in out
    assert main(["disasm", str(FIB), "--lang", "en"]) == 0
    assert "ADD   N - 0 1 2" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("text", "shown"),
    [("+1", "+1"), ("-22", "-22"), ("+3,14", "+3.14"), ("+0", "+0"), ("+0,00125", "+0.00125")],
)
def test_disasm_decodes_num_exactly(tmp_path, text, shown):
    src = tmp_path / "n.g60b"
    src.write_text(f"        STOP\nX:      NUM   {text}\n", encoding="utf-8")
    program = codeb.parse(src.read_text(encoding="utf-8"))
    ut, _ = chain.processing_unit(program, None, "n")
    lines = {a: t for a, _, _, t in disassembler.disassemble(disassembler.source_of(ut))}
    assert lines[program.labels["X"]] == f"NUM   {shown}"


def test_files_of_the_chain_hold_code_a_in_hexadecimal(tmp_path):
    from gamma60.toolchain.subprogram import Subprogram

    assert main(["transpose", str(FIB), "-o", str(tmp_path / "f.g60a.json")]) == 0
    d = __import__("json").loads((tmp_path / "f.g60a.json").read_text(encoding="utf-8"))
    assert d["words"]["0"] == "400002" and d["words"]["2"] == "8E8012"
    d["words"] = {k: int(v, 16) for k, v in d["words"].items()}  # decimal still read
    assert Subprogram.from_json(d).words[2] == 0x8E8012


def test_disasm_raw_reads_only_the_catenae(capsys):
    assert main(["disasm", str(FIB), "--raw"]) == 0
    out = capsys.readouterr().out
    assert "START" not in out and ";" not in out  # no label, no source
    assert "TRA   N - T - 2" in out  # element of the directive: the last cut (ARIT)
    assert "00274  000014  D00274:             00    20" in out  # data read as an instruction
    # labels rebuilt from the code A: code targets L, data addresses D, quantities as numbers
    assert "00269  A40115  L00269:             IC    D00277" in out
    assert "31    L00269" in out and "LB    D00274 S" in out and "SB    2 " in out
