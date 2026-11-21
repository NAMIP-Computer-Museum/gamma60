"""Catena: check keys of both profiles, bit fields, BCD and alphanumeric codings; memory."""

import pytest

from gamma60 import data
from gamma60.catena import (
    Catena,
    KeyError_,
    bits,
    check_key,
    from_alpha,
    from_bcd,
    set_bits,
    to_alpha,
    to_bcd,
)
from gamma60.memory import Memory

B61 = data.get_profile("B61")
COURS = data.get_profile("COURS")


def test_b61_key_parity_and_mod3():
    # bits 16-24: one bit set -> parity 1; bits 1-15 = 7 -> 7 mod 3 = 1  [B61 p.26]
    value = (1 << 20) | 7
    assert check_key(value, "parity9_mod3_15") == 0b101
    assert check_key(0, "parity9_mod3_15") == 0
    assert check_key((0b11 << 15) | 3, "parity9_mod3_15") == 0b000  # even parity, 3 mod 3 = 0


def test_cours_key_mod7():
    assert check_key(2548, "mod7_24bits") == 0  # COURS p.11-12: remainder of the 24-bit number
    assert check_key(8452, "mod7_24bits") == 8452 % 7


def test_unknown_key_kind():
    with pytest.raises(ValueError):
        check_key(1, "nothing")


@pytest.mark.parametrize("profile", [B61, COURS])
def test_catena_checked(profile):
    c = Catena.make(0xABCDEF, profile)
    assert c.checked(profile) == 0xABCDEF
    with pytest.raises(KeyError_):
        Catena(c.value ^ 1, c.key).checked(profile)


def test_catena_range():
    with pytest.raises(ValueError):
        Catena.make(1 << 24)


def test_bit_fields():
    v = set_bits(0, 19, 18, 0b11)
    assert v == 0b11 << 17 and bits(v, 19, 18) == 3
    with pytest.raises(ValueError):
        set_bits(0, 19, 18, 4)


def test_bcd():
    assert to_bcd("123456") == 0x123456
    assert from_bcd(0x098765) == "098765"
    with pytest.raises(ValueError):
        from_bcd(0x00000A)
    with pytest.raises(ValueError):
        to_bcd("12345")


def test_alphanumeric_examples_of_b61():
    # B = 000010, U = 010101, L = 001100 (B61 p.16, data/charset.yaml)
    value = to_alpha("BUL ")
    assert bits(value, 24, 19) == 0b000010
    assert bits(value, 18, 13) == 0b010101
    assert bits(value, 12, 7) == 0b001100
    assert from_alpha(value) == "BUL "


@pytest.mark.parametrize("profile", [B61, COURS])
def test_memory_read_write_and_key_check(profile):
    m = Memory(profile)
    m.write(100, 0x123456)
    assert m.read(100) == 0x123456
    raw = m.raw(100)
    m.poke_raw(100, Catena(raw.value ^ 0b100, raw.key))
    with pytest.raises(KeyError_):
        m.read(100)
    with pytest.raises(IndexError):
        m.read(m.size)


def test_memory_block_range_depends_on_profile():
    assert Memory(COURS, blocks=1).size == 4096
    with pytest.raises(ValueError):
        Memory(B61, blocks=1)  # B61: 2 to 8 blocks
