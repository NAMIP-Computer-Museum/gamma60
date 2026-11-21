"""Semi-logarithmic numbers: layout and examples of B61 p.18 and COURS p.61-64."""

from fractions import Fraction

import pytest

from gamma60.catena import bits
from gamma60.core.arit import Incident, fit
from gamma60.number import NotANumber, Number, proof7_key


@pytest.mark.parametrize(
    ("text", "negative", "exponent", "mantissa", "value"),
    [
        ("+39 0482|000000", False, 39, 482000000, Fraction("0.00482")),  # not normalised
        ("+43 3254|200000", False, 43, 3254200000, Fraction("325.42")),  # floating
        ("+50 0000|004832", False, 50, 4832, Fraction(4832)),  # point at position 0
        ("+45 0483|200000", False, 45, 483200000, Fraction(4832)),  # point at position 5
    ],
)
def test_b61_examples(text, negative, exponent, mantissa, value):
    n = Number(negative, exponent, mantissa)
    assert str(n) == text
    assert n.value == value


def test_catena_layout_and_round_trip():
    n = Number(True, 43, 3254200000)
    first, second = n.to_catenae()
    assert bits(first, 24, 24) == 1  # sign: 1 = minus
    assert bits(first, 23, 21) == 4  # tens digit of the exponent, binary
    assert bits(first, 20, 17) == 3  # units digit, BCD
    assert bits(first, 16, 1) == 0x3254
    assert second == 0x200000
    assert Number.from_catenae(first, second) == n


def test_not_a_number():
    with pytest.raises(NotANumber):
        Number.from_catenae(0x00000A, 0)  # non-BCD mantissa tetrad
    with pytest.raises(NotANumber):
        Number.from_catenae(0b1111 << 16, 0)  # exponent units > 9


def test_ranges():
    with pytest.raises(ValueError):
        Number(False, 80, 0)
    with pytest.raises(ValueError):
        Number(False, 40, 10**10)


def test_normalised_form():
    p, s = fit(Fraction("325.42"), None)
    assert str(p) == "+43 3254|200000" and s.mantissa == 0
    p, _ = fit(Fraction("-0.0000542"), None)  # COURS p.61
    assert str(p) == "-36 5420|000000"


def test_programmed_point():
    assert str(fit(Fraction(4832), 5)[0]) == "+45 0483|200000"  # B61 p.18
    assert str(fit(Fraction(4832), 3)[0]) == "+47 0004|832000"  # COURS p.64
    with pytest.raises(Incident):
        fit(Fraction(4832), 7)  # high digits lost -> incident [COURS p.64]


def test_low_digits_go_to_s():
    p, s = fit(Fraction(12345678901234), None)
    assert str(p) == "+54 1234|567890" and s.exponent == 44 and s.mantissa == 1234000000


def test_zero():
    p, s = fit(Fraction(0), None)
    assert p == Number(False, 0, 0) and s.mantissa == 0
    assert fit(Fraction(0), 2)[0].exponent == 48


def test_exponent_out_of_range():
    with pytest.raises(Incident):
        fit(Fraction(10) ** 45, None)
    with pytest.raises(Incident):
        fit(Fraction(1, 10**45), None)
    with pytest.raises(Incident):
        fit(Fraction(1), 11)


def test_proof_by_seven():
    # "2,548 and 8,452 ... remainders equal to 0 and 3" [B61 p.35 ; COURS p.66]
    assert proof7_key(Number(False, 50, 2548)) == 0
    assert proof7_key(Number(False, 50, 8452)) == 3
