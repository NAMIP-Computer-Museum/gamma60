"""J6 step 3: distribution of the symbols (code D2) → processing unit [MAIT §G.G.Z. ; U-54]."""

from pathlib import Path

import pytest
from test_linker import _write

from gamma60 import code_a, codeb
from gamma60.__main__ import main
from gamma60.toolchain.assembler import assemble
from gamma60.toolchain.distributor import ProcessingUnit, distribute, distribute_file
from gamma60.toolchain.linker import link
from gamma60.toolchain.subprogram import LinkError


def _x_of(text: str) -> int:
    image = assemble(codeb.parse("; langue: fr\n" + text))
    return code_a.decode(image.words[image.entry]).x


def test_values_go_into_the_blanks(tmp_path):
    prog = link(_write(tmp_path))
    ut = distribute(prog, {"DEROULEUR": 2}, "prog")
    assert code_a.decode(ut.words[1002]).x == _x_of("        DERU  2\n        VIERGE\n")
    assert {a: v for a, v in ut.words.items() if a != 1002} == {
        a: v for a, v in prog.words.items() if a != 1002
    }
    assert ut.distribution == {"DEROULEUR": 2} and ut.exit == prog.exit


def test_drum_address_converted_like_code_b(tmp_path):
    (tmp_path / "t.g60b").write_text(
        "; langue: fr\n        TAMB  1\n        VIERGE\n        DAO   ?PISTE\n        STOP\n",
        encoding="utf-8",
    )
    (tmp_path / "t.g60c.yaml").write_text(
        "articles: {1: {sp: t.g60b}}\ndistr: {implantation: {1: 500}, symboles: {1.X1: ADRTAM}}\n",
        encoding="utf-8",
    )
    ut = distribute(link(tmp_path / "t.g60c.yaml"), {"ADRTAM": 1234}, "t")
    ref = assemble(
        codeb.parse("; langue: fr\n        TAMB  1\n        VIERGE\n        DAO   1234\n")
    )
    assert ut.words[502] == ref.words[ref.entry + 2]


@pytest.mark.parametrize(
    ("values", "message"),
    [
        ({}, "no value for DEROULEUR"),
        ({"DEROULEUR": 2, "AUTRE": 1}, "AUTRE is not a symbol"),
        ({"DEROULEUR": "deux"}, "must be an integer"),
        ({"DEROULEUR": 0}, "unit number 0"),
    ],
)
def test_errors(tmp_path, values, message):
    with pytest.raises(LinkError, match=message):
        distribute(link(_write(tmp_path)), values, "prog")


def test_d2_file_and_round_trip(tmp_path):
    _write(tmp_path)
    d2 = tmp_path / "prod.g60d.yaml"
    d2.write_text("programme: prog.g60c.yaml\nvaleurs:\n  DEROULEUR: 3\n", encoding="utf-8")
    ut = distribute_file(d2)
    assert ut.name == "prod" and ut.distribution == {"DEROULEUR": 3}
    ut.save(tmp_path / "u.json")
    assert ProcessingUnit.load(tmp_path / "u.json") == ut


def test_cli_distribute(tmp_path, capsys):
    _write(tmp_path)
    d2 = tmp_path / "prod.g60d.yaml"
    d2.write_text("programme: prog.g60c.yaml\nvaleurs: {DEROULEUR: 3}\n", encoding="utf-8")
    assert main(["distribute", str(d2)]) == 0
    assert "DEROULEUR        = 3" in capsys.readouterr().out
    assert (tmp_path / "prod.ut.json").exists()
    assert main(["distribute", str(tmp_path / "prog.g60c.yaml")]) == 2  # a symbol, no value
    assert "no value for DEROULEUR" in capsys.readouterr().out


def test_cli_distribute_without_symbols(tmp_path):
    src = Path("tests/programs/fibonacci.g60b").resolve().as_posix()
    image = assemble(codeb.parse(Path(src).read_text(encoding="utf-8")))
    sheet = tmp_path / "fib.g60c.yaml"
    sheet.write_text(
        f"articles: {{1: {{sp: '{src}'}}}}\ndistr: {{implantation: {{1: {image.program.origin}}}}}\n",
        encoding="utf-8",
    )
    assert main(["distribute", str(sheet)]) == 0
    ut = ProcessingUnit.load(tmp_path / "fib.ut.json")
    assert ut.words == image.words and ut.entry == image.entry
