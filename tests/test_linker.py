"""J6 step 2: assembly driven by a code C sheet [MAIT §Assemblage & code C ; U-53]."""

from pathlib import Path

import pytest

from gamma60 import code_a, codeb
from gamma60.__main__ import main
from gamma60.toolchain.assembler import assemble
from gamma60.toolchain.linker import EXIT, Assembled, link
from gamma60.toolchain.subprogram import LinkError

MAIN = """; langue: fr
        REP   DEBUT
DEBUT:  GB    ?TAMPON                  ; X1: a zone
        31    ?CALCUL                  ; X2: entry of the other subprogram
        DERU  ?DEROUL                  ; X3: left to the distribution
        VIERGE
        31    ?FIN                     ; X4: exit of the program
"""

CALC = """; langue: fr
        REP   CALCUL
CALCUL: GB    ZL                       ; internal absolute address: relocated
        31    ?RETOUR  R               ; X1: back to the main subprogram, differential
ZL:     BIN   ?LONG                    ; X2: a constant
"""

SHEET = """
articles:
  1: {sp: main.g60b}
  2: {sp: calc.g60b, nom: C}
  3: {zone: 20}
assembl:
  - 1.X1 = 3.R1
  - 1.X2 = C.R1
  - 2.?RETOUR = 1.DEBUT
  - 2.X2 = 50
distr:
  implantation: {1: 1000}
  entree: 1.R1
  sortie: 1.X4
  symboles: {1.X3: DEROULEUR}
"""


def _write(tmp_path: Path, sheet: str = SHEET) -> Path:
    (tmp_path / "main.g60b").write_text(MAIN, encoding="utf-8")
    (tmp_path / "calc.g60b").write_text(CALC, encoding="utf-8")
    path = tmp_path / "prog.g60c.yaml"
    path.write_text(sheet, encoding="utf-8")
    return path


def test_condensation_links_and_exit(tmp_path):
    prog = link(_write(tmp_path))
    assert [(n, name, base, size) for n, name, base, size in prog.layout] == [
        (1, "main", 1000, 5),
        (2, "C", 1005, 3),
        (3, "Z3", 1008, 20),
    ]
    w = {a: code_a.decode(v) for a, v in prog.words.items() if a < 1008 and a != 1007}
    assert w[1000].x == 1008  # GB ?TAMPON = start of the zone
    assert w[1001].x == 1005  # 31 ?CALCUL = C.R1
    assert w[1005].x == 1007  # GB ZL relocated
    assert w[1006].d and w[1006].x == (1000 - 1006) & 0x7FFF
    assert prog.words[1007] == 50
    assert prog.exit == 1028 and prog.labels[EXIT] == 1028
    assert code_a.decode(prog.words[1028]).op == "STOP"
    assert w[1004].x == 1028  # 31 ?FIN → FIN_UT
    assert prog.entry == 1000
    assert [(f.address, f.name, f.mode) for f in prog.fixups] == [
        (1002, "DEROULEUR", "unit:uniselector")
    ]
    assert prog.labels["C.ZL"] == 1007 and prog.lines[1005][0] == "C"


def test_json_round_trip(tmp_path):
    prog = link(_write(tmp_path))
    prog.save(tmp_path / "p.json")
    assert Assembled.load(tmp_path / "p.json") == prog


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (("  - 2.X2 = 50\n", ""), "neither linked nor given a symbol: C.\\?LONG"),
        (("{1: 1000}", "{2: 1000}"), "first article needs an address"),
        (("{1: 1000}", "{1: 1000, 2: 1002}"), "overlap"),
        (("  - 2.X2 = 50\n", "  - 2.X2 = 50\n  - 2.X2 = 51\n"), "assigned twice"),
        (("1.X2 = C.R1", "1.X2 = C.R9"), "no repère R9"),
        (("1.X1 = 3.R1", "1.X1 = 3.R2"), "a zone has only R1"),
        (("1.X2 = C.R1", "1.X2 = 7.R1"), "no article 7"),
    ],
)
def test_errors(tmp_path, change, message):
    with pytest.raises(LinkError, match=message):
        link(_write(tmp_path, SHEET.replace(*change)))


@pytest.mark.parametrize("name", ["fibonacci", "bande_continue_task", "pi"])
def test_single_article_matches_the_plain_assembly(tmp_path, name):
    src = Path("tests/programs") / f"{name}.g60b"
    image = assemble(codeb.parse(src.read_text(encoding="utf-8")))
    sheet = tmp_path / "s.g60c.yaml"
    sheet.write_text(
        f"articles: {{1: {{sp: '{src.resolve().as_posix()}'}}}}\n"
        f"distr: {{implantation: {{1: {image.program.origin}}}}}\n",
        encoding="utf-8",
    )
    prog = link(sheet)
    assert prog.words == image.words and prog.entry == image.entry
    assert prog.joins == image.joins and prog.elements == image.elements


def test_cli_assemble(tmp_path, capsys):
    path = _write(tmp_path)
    assert main(["assemble", str(path), "--listing"]) == 0
    out = capsys.readouterr().out
    assert "symbol DEROULEUR      01002" in out
    assert "<- DEROULEUR (distribution)" in out
    assert (tmp_path / "prog.g60pa.json").exists()
