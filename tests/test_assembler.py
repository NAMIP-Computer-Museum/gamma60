"""Assembler code B → code A (J3)."""

from __future__ import annotations

from pathlib import Path

import pytest

from gamma60 import code_a
from gamma60.code_a import ADDRESS, BRANCH, CENTRAL, CUT, ELEMENT, decode
from gamma60.codeb import ProgramError, parse
from gamma60.toolchain.assembler import AsmUnsupported, assemble, listing_lines

PROGRAMS = Path(__file__).parent / "programs"


def asm(text: str):
    return assemble(parse(text))


def word(image, label):
    return decode(image.words[image.labels[label]])


@pytest.mark.parametrize(
    "name",
    [
        "test-arith01",
        "test-arith02-overflow",
        "test-arith03-underflow",
        "arit_logi",
        "forkjoin_tumlin",
    ],
)
@pytest.mark.parametrize("profile", ["B61", "COURS"])
def test_programs_assemble(name, profile):
    from gamma60 import data

    image = assemble(
        parse((PROGRAMS / f"{name}.g60b").read_text(encoding="utf-8")), data.get_profile(profile)
    )
    origin = image.program.origin
    assert origin == 256  # after the table of the recall chain registers (U-30)
    assert image.entry == origin and len(image.words) == image.program.end - origin


def test_other_elements_are_not_assembled_yet():
    with pytest.raises(AsmUnsupported):
        assemble(parse((PROGRAMS / "namip_classement.g60b").read_text(encoding="utf-8")))


def test_cut_carries_the_element_number():
    image = asm("; langue: en\nS: ARIT\n VIERGE\n STOP\nT: LOGI\n VIERGE\n STOP\n")
    assert word(image, "S") == code_a.Word(CUT, "normal", x=2)  # ARIT: 2 (U-44)
    assert word(image, "T") == code_a.Word(CUT, "normal", x=1)
    assert decode(image.words[image.program.origin + 2]) == code_a.Word(CUT, "STOP")


def test_join_count_in_both_notations():
    b61 = asm("; langue: en\nS: ARIT 2\n VIERGE\n STOP\n")
    cours = asm("; langue: fr\nS: ARIT\n VIERGE 2\n STOP\n")  # COURS: X of the blank catena
    assert word(b61, "S").m == word(cours, "S").m == 2
    assert cours.words[cours.program.origin + 1] == 0  # stays blank (bits 19-18: counter)
    assert b61.joins == {b61.labels["S"]: 2}


def test_address_functions():
    text = (
        "; langue: en\n"
        "S:  ARIT\n    VIERGE\n"
        "A1: L 0 DATA\n"  # absolute
        "A2: L 1 DATA R\n"  # differential to a label
        "A3: L 2 DATA S\n"  # substitution
        "B1: 31 2 R\n"  # line 2 of the sheet, differential
        "C1: TA 1 M\n"  # working memory 1, differential
        "    STOP\nDATA: ZONE 1\n"
    )
    image = asm(text)
    end, data_addr = image.program.end, image.labels["DATA"]
    assert word(image, "A1") == code_a.Word(ADDRESS, "load", car=0, x=data_addr)
    here = image.labels
    assert word(image, "A2") == code_a.Word(
        ADDRESS, "load", car=1, d=True, x=data_addr - here["A2"]
    )
    assert word(image, "A3") == code_a.Word(ADDRESS, "load", car=2, s=True, x=data_addr)
    assert word(image, "B1") == code_a.Word(
        BRANCH, 31, d=True, x=(2 - 5) & 0o77777
    )  # line 2: back 3
    assert word(image, "C1") == code_a.Word(
        CENTRAL, "transfer_to_A", d=True, x=end + 1 - here["C1"]
    )


def test_origin_and_line_numbers():
    text = "; langue: en\n; origine: 1000\n000 S: ARIT\n001    VIERGE\n002    31 0 R\n003    STOP\n"
    image = asm(text)
    assert image.entry == 1000 and sorted(image.words) == [1000, 1001, 1002, 1003]
    assert decode(image.words[1002]) == code_a.Word(BRANCH, 31, d=True, x=(1000 - 1002) & 0o77777)


def test_element_directives_follow_the_last_cut():
    image = asm(
        "; langue: en\n ARIT\n VIERGE\nX: ADD N - 0 1 2\n LOGI\n VIERGE\nY: ADD 4 L\n STOP\n"
    )
    assert image.elements == {image.labels["X"]: "arithmetic", image.labels["Y"]: "logical"}
    x, y = word(image, "X"), word(image, "Y")
    assert x.kind == y.kind == ELEMENT
    assert code_a.decode_arit(x.characteristic)[0] == "add"
    assert code_a.decode_logi(y.characteristic)[0] == "add"


@pytest.mark.parametrize(
    "text",
    [
        "; langue: en\n ARIT\n STOP\n",  # cut without blank catena
        "; langue: en\n ARIT\n VIERGE\n L 0 NOWHERE\n STOP\n",
        "; langue: en\n ADD N - 0 1 2\n",  # directive before any cut
        "; langue: en\n ARIT\n VIERGE\n ZZZ\n STOP\n",
        "; langue: en\n ARIT 4\n VIERGE\n STOP\n",  # join count > 3
        "; langue: en\n 25 0\n",  # not a bit of A
        "; langue: en\n001 ARIT\n001 VIERGE\n",  # same address twice
    ],
)
def test_errors(text):
    with pytest.raises(ProgramError):
        asm(text)


def test_listing():
    image = assemble(parse((PROGRAMS / "test-arith01.g60b").read_text(encoding="utf-8")))
    lines = listing_lines(image)
    assert lines[0].startswith("00256  01 000 00 0 0 000000000000010") and "ARIT" in lines[0]
    assert "(data)" in lines[7] and "NUM" in lines[7]
    assert listing_lines(image) == lines  # stable
