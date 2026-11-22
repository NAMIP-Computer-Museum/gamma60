"""Code A (J3): prefixes and fields [COURS p.33-52], reconstructed sub-codes (U-01)."""

from __future__ import annotations

import itertools

import pytest

from gamma60 import code_a, data
from gamma60.code_a import (
    ADDRESS,
    BRANCH,
    CENTRAL,
    CUT,
    ELEMENT,
    DecodeError,
    Word,
    decode,
    decode_arit,
    decode_logi,
    encode,
    encode_arit,
    encode_logi,
)
from gamma60.codeb import AritFields, LogiFields


def test_cours_p44_example():
    # « 31, 10 lignes plus loin, en différentiel » = 00 11111 1 0 000000000001010 [COURS p.44]
    value = encode(Word(BRANCH, 31, d=True, x=10))
    assert f"{value:024b}" == "001111110000000000001010"
    assert code_a.text(value) == "00 11111 1 0 000000000001010"


def test_blank_catena_is_a_never_branch():
    assert decode(0) == Word(BRANCH, 0)  # [COURS p.42]


@pytest.mark.parametrize(
    "word",
    [
        Word(BRANCH, cond, d=d, s=s, x=x)
        for cond, d, s, x in itertools.product(
            (0, 1, 24, 31), (False, True), (False, True), (0, 32767)
        )
    ]
    + [
        Word(CUT, kind, m=m, x=99)
        for kind in data.load("encoding")["synthetic_subcodes"]["cut_kind"]
        for m in range(4)
    ]
    + [
        Word(CENTRAL, ident, s=True, x=5)
        for ident in data.load("encoding")["synthetic_subcodes"]["central_directive"]
    ]
    + [
        Word(ADDRESS, op, car=car, d=True, x=7)
        for op in ("load", "place", "add", "subtract")
        for car in range(4)
    ]
    + [Word(ELEMENT, characteristic=c) for c in (0, 1, 0xFFFFF)],
)
def test_round_trip(word):
    assert decode(encode(word)) == word


def test_prefixes():
    assert encode(Word(CUT, "normal")) >> 22 == 0b01
    assert encode(Word(CENTRAL, "fill_zeros")) >> 22 == 0b10
    assert encode(Word(ADDRESS, "load")) >> 21 == 0b110
    assert encode(Word(ELEMENT)) >> 20 == 0b1111


@pytest.mark.parametrize(
    "value",
    [0b1110 << 20, (0b00 << 22) | (25 << 17), (0b01 << 22) | (7 << 19), (0b10 << 22) | (30 << 17)],
)
def test_decode_errors(value):
    with pytest.raises(DecodeError):
        decode(value)


DESIGNATORS = [("rac", i, p) for i in range(4) for p in (True, False)]


@pytest.mark.parametrize("op", list(code_a.ARIT_FIELDS))
def test_arit_layout_round_trip(op):
    used = code_a.ARIT_FIELDS[op]
    for mode, point in [(None, None), ("P", 0), ("P", 10), ("N", None), ("A", None)]:
        if op not in code_a.ARIT_USES_MODE and mode is not None:
            continue
        if op in code_a.ARIT_USES_POWER:
            point = 15
        for o1, r in [
            (DESIGNATORS[0], DESIGNATORS[5]),
            ("P", "P"),
            (DESIGNATORS[7], DESIGNATORS[2]),
        ]:
            f = AritFields(
                mode,
                True,
                point,
                o1 if "o1" in used else None,
                DESIGNATORS[3] if "o2" in used else None,
                r if "r" in used else None,
            )
            assert decode_arit(encode_arit(op, f)) == (op, f)
    assert encode_arit(op, AritFields(None, False, None, None, None, None)) >> 20 == 0  # 20 bits


def test_arit_layout_rejects():
    with pytest.raises(ValueError):
        encode_arit("add", AritFields("N", False, None, "P", "P", "P"))  # P not in O2
    with pytest.raises(ValueError):
        encode_arit("add", AritFields("P", False, 11, "P", DESIGNATORS[0], "P"))
    with pytest.raises(DecodeError):
        decode_arit(15 << 16)  # directive 15 does not exist
    with pytest.raises(DecodeError):
        decode_arit(31 << 11)  # mode 31


@pytest.mark.parametrize("op", code_a.directive_ids("logical"))
def test_logi_layout_round_trip(op):
    for length, r in [(0, "L"), (24, DESIGNATORS[1]), (7, DESIGNATORS[6])]:
        f = LogiFields(length, r)
        assert decode_logi(encode_logi(op, f)) == (op, f)


def test_logi_layout_rejects():
    with pytest.raises(ValueError):
        encode_logi("add", LogiFields(25, "L"))
    with pytest.raises(DecodeError):
        decode_logi(25 << 11)
