"""J6 step 1: assemblable subprograms (code A with blanks, unknowns, repères, relocations)."""

from pathlib import Path

import pytest

from gamma60 import code_a, codeb
from gamma60.__main__ import main
from gamma60.toolchain.assembler import AsmUnsupported, assemble
from gamma60.toolchain.subprogram import LinkError, Subprogram, from_image

PROGRAMS = sorted(Path("tests/programs").glob("*.g60b"))

SP = """; langue: fr
        REP   DEBUT  SUITE
DEBUT:  GB    ZA                ; absolute address of the program: relocated
        31    ?SORTIE           ; unknown branch target (absolute)
SUITE:  31    ?RETOUR  R        ; unknown, differential
        31    ADR    S          ; jump to the address held in ADR [B61 p.29]
        DERU  ?DEROUL           ; unit number given later
        VIERGE
        LAV   ?DEROUL
ZA:     ZONE  2
ADR:    BIN   ?SORTIE           ; unknown catena
"""


def _sp(text: str = SP, name: str = "t") -> Subprogram:
    return from_image(assemble(codeb.parse(text)), name)


def test_rep_declares_reperes_without_catena():
    p = codeb.parse(SP)
    assert p.reperes == ["DEBUT", "SUITE"]
    assert p.labels["DEBUT"] == p.origin  # REP takes no address
    with pytest.raises(codeb.ProgramError, match="unknown label"):
        codeb.parse("        REP   NULLE\n        STOP\n")


def test_unknowns_numbered_in_order_of_appearance():
    sp = _sp()
    assert sp.unknowns == ["SORTIE", "RETOUR", "DEROUL"]
    assert sp.unknown("X2") == "RETOUR" and sp.unknown("?DEROUL") == "DEROUL"
    assert sp.repere("R2") == sp.repere("SUITE") == 2
    modes = {(f.name, f.address): (f.field, f.mode) for f in sp.fixups}
    assert modes[("SORTIE", 1)] == ("x", "abs")
    assert modes[("RETOUR", 2)] == ("x", "diff")
    assert modes[("DEROUL", 4)] == ("x", "unit:uniselector")
    assert modes[("SORTIE", 9)] == ("word", "abs")
    assert sp.relocations == [0, 3]  # GB ZA, 31 ADR S


def test_place_relocates_and_fills_blanks():
    sp = _sp()
    w = sp.place(1000, {"SORTIE": 5000, "RETOUR": 990, "DEROUL": 2})
    assert code_a.decode(w[1000]).x == 1007  # ZA moved with the program
    assert code_a.decode(w[1001]).x == 5000
    assert code_a.decode(w[1002]).x == (990 - 1002) & 0x7FFF
    word = code_a.decode(w[1003])
    assert word.s and word.x == 1009
    assert w[1009] == 5000
    ref = assemble(codeb.parse("; langue: fr\n        DERU  2\n        VIERGE\n"))
    assert code_a.decode(w[1004]).x == code_a.decode(ref.words[ref.entry]).x
    with pytest.raises(LinkError, match="has no value"):
        sp.place(0, {"SORTIE": 1})


def test_unknown_with_working_memory_refused():
    with pytest.raises(codeb.ProgramError, match="invalid unknown"):
        assemble(codeb.parse("        31    ?X  M\n"))


@pytest.mark.parametrize("path", PROGRAMS, ids=lambda p: p.stem)
def test_every_program_relocates_like_a_reassembly(path):
    text = path.read_text(encoding="utf-8")
    try:
        image = assemble(codeb.parse(text))
    except AsmUnsupported:
        pytest.skip("element not assembled yet")
    sp = from_image(image, path.stem)
    assert sp.place(image.program.origin, {}) == image.words
    moved = assemble(codeb.parse(text + "\n; origine: 3000\n"))
    assert sp.place(3000, {}) == moved.words


def test_json_round_trip(tmp_path):
    sp = _sp()
    sp.save(tmp_path / "t.g60a.json")
    back = Subprogram.load(tmp_path / "t.g60a.json")
    values = {"SORTIE": 7, "RETOUR": 8, "DEROUL": 1}
    assert back.place(500, values) == sp.place(500, values)
    assert back.reperes == sp.reperes and back.lines == sp.lines


def test_cli_transpose_and_run_refuses_unknowns(tmp_path, capsys):
    src = tmp_path / "t.g60b"
    src.write_text(SP, encoding="utf-8")
    assert main(["transpose", str(src)]) == 0
    out = capsys.readouterr().out
    assert "X1   ?SORTIE" in out and "R2   SUITE" in out
    assert (tmp_path / "t.g60a.json").exists()
    assert main(["run", str(src)]) == 2
    assert "?SORTIE, ?RETOUR, ?DEROUL have no value" in capsys.readouterr().out
