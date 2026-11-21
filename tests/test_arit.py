"""ARIT: every directive of data/directives.yaml (elements.arithmetic) [COURS p.65-72]."""

from fractions import Fraction

import pytest

from gamma60 import data
from gamma60.core.arit import ArithmeticUnit, Incident, fit
from gamma60.number import Number

F = Fraction


def num(x) -> Number:
    return fit(F(x), None)[0]


def positions(q: int) -> set[int]:
    return {i + 1 for i in range(24) if q >> i & 1}


class Store:
    """Operands by name; results collected by name."""

    def __init__(self, **values):
        self.values = {k: (v if isinstance(v, Number) else num(v)) for k, v in values.items()}
        self.out: dict[str, list[Number]] = {}

    def load(self, d):
        return self.values[d]

    def store(self, d, numbers):
        self.out[d] = list(numbers)


def run(op, unit=None, **kw):
    unit = unit or ArithmeticUnit()
    s = Store(**kw.pop("values", {}))
    unit.execute(op, load=s.load, store=s.store, **kw)
    return unit, s


def test_all_directives_are_covered():
    ids = set(data.load("directives")["elements"]["arithmetic"]["directives"])
    tested = {name[5:] for name in globals() if name.startswith("test_")}
    assert ids <= tested, ids - tested


def test_add():
    u, s = run("add", mode="N", o1="a", o2="b", r="r", values={"a": 3, "b": 4})
    assert s.out["r"][0].value == 7 and positions(u.qualitative) == {9}


def test_subtract():
    u, s = run("subtract", mode="N", o1="a", o2="b", r="r", values={"a": 3, "b": 5})
    assert s.out["r"][0].value == -2 and positions(u.qualitative) == {8}
    u, _ = run("subtract", mode="N", o1="a", o2="b", r="r", values={"a": 3, "b": 3})
    assert positions(u.qualitative) == {7}


def test_multiply():
    _u, s = run("multiply", mode="N", o1="b", o2="c", r="r", values={"b": 3, "c": 4})
    assert s.out["r"][0].value == 12
    # programmed point 2: 15 x 2.50 = 37.50 (exponent 48)
    _, s = run("multiply", mode="P", point=2, o1="q", o2="p", r="r", values={"q": 15, "p": "2.5"})
    assert str(s.out["r"][0]) == "+48 0000|003750"


def test_multiply_double_length():
    a = F(9_999_999_999)
    _u, s = run("multiply", mode="N", double=True, o1="a", o2="a", r="r", values={"a": a})
    p, low = s.out["r"]
    assert p.value + low.value == a * a  # 20 digits: P high, S low (exponent of P - 10)
    assert low.exponent == p.exponent - 10


def test_s_cleared_even_if_o1_is_p():
    u = ArithmeticUnit(p=num(1), s=num(5))
    run("add", unit=u, mode="N", o1="P", o2="b", r="P", values={"b": 2})
    assert u.p.value == 3 and u.s.mantissa == 0


def test_mode_a_equals_n_then_round_off():
    a = F(1_234_567_891)
    _u1, s1 = run("multiply", mode="A", o1="a", o2="a", r="r", values={"a": a})
    u2, _ = run("multiply", mode="N", o1="a", o2="a", r="P", values={"a": a})
    _, s2 = run("round_off", unit=u2, r="r")
    assert s1.out["r"][0] == s2.out["r"][0]  # MUL.A = MUL.N + ARR [COURS p.68]


def test_round_off():
    u = ArithmeticUnit(p=Number(False, 50, 1234), s=Number(False, 40, 5_000_000_000))
    _, s = run("round_off", unit=u, r="r")
    assert s.out["r"][0].mantissa == 1235 and u.s.mantissa == 0  # S cleared [COURS p.72]
    u = ArithmeticUnit(p=Number(False, 50, 9_999_999_999), s=Number(False, 40, 9 * 10**9))
    run("round_off", unit=u, r="P")
    assert u.p == Number(False, 51, 1_000_000_000)  # carry out of P: shift, exponent + 1


def test_divide():
    u, s = run("divide", mode="N", o1="a", o2="b", r="r", values={"a": 1, "b": 3})
    assert str(s.out["r"][0]) == "+40 3333|333333"
    u, s = run("divide", mode="P", point=0, o1="a", o2="b", r="r", values={"a": 7, "b": 2})
    assert s.out["r"][0].value == 3 and u.p.value == 3


def test_divide_with_remainder():
    _u, s = run(
        "divide_with_remainder",
        mode="P",
        point=0,
        double=True,
        o1="a",
        o2="b",
        r="r",
        values={"a": 7, "b": 2},
    )
    remainder, quotient = s.out["r"]  # remainder then quotient [COURS p.70]
    assert remainder.value == 1 and quotient.value == 3


def test_division_by_zero_is_an_incident():
    u = ArithmeticUnit()
    with pytest.raises(Incident):
        run("divide", unit=u, mode="N", o1="a", o2="b", r="r", values={"a": 1, "b": 0})
    assert {23, 24} <= positions(u.qualitative)


def test_transfer():
    raw = Number(False, 39, 482000000)  # +0.00482 not normalised [B61 p.18]
    _, s = run("transfer", mode="N", o1="a", o2=None, r="r", values={"a": raw})
    assert str(s.out["r"][0]) == "+38 4820|000000"
    _, s = run("transfer", mode="P", point=3, o1="a", r="r", values={"a": 4832})
    assert str(s.out["r"][0]) == "+47 0004|832000"
    _, s = run("transfer", o1="a", r="r", values={"a": raw})
    assert s.out["r"][0] == raw  # no C.C.1: copied as is
    with pytest.raises(Incident):
        run("transfer", mode="P", point=7, o1="a", r="r", values={"a": 4832})


def test_transfer_from_p_keeps_s():
    u = ArithmeticUnit(p=Number(False, 50, 1), s=Number(False, 40, 5 * 10**9))
    _, s = run("transfer", unit=u, mode="P", point=1, double=True, o1="P", r="r")
    assert sum(n.value for n in s.out["r"]) == F("1.5")


def test_multiply_pow10():
    _, s = run("multiply_pow10", point=2, o1="a", r="r", values={"a": 3})
    assert s.out["r"][0].value == 300
    with pytest.raises(Incident):
        run("multiply_pow10", point=16, o1="a", r="r", values={"a": 3})
    with pytest.raises(Incident):
        run("multiply_pow10", point=15, o1="a", r="r", values={"a": Number(False, 70, 1)})


def test_divide_pow10():
    # COURS p.71: DPD 2 takes exponent 50 to 48
    _, s = run("divide_pow10", point=2, o1="a", r="r", values={"a": Number(False, 50, 4832)})
    assert s.out["r"][0] == Number(False, 48, 4832)


def test_reverse_sign():
    u, s = run("reverse_sign", o1="a", r="r", values={"a": 5})
    assert s.out["r"][0].value == -5 and positions(u.qualitative) == {8}


def test_absolute_value():
    _, s = run("absolute_value", o1="a", r="r", values={"a": -5})
    assert s.out["r"][0].value == 5


def test_compare_algebraic():
    u, s = run("compare_algebraic", o1="a", o2="b", values={"a": 3, "b": -5})
    assert positions(u.qualitative) == {1, 4, 6} and not s.out  # > >= != ; nothing stored


def test_compare_absolute():
    u, _ = run("compare_absolute", o1="a", o2="b", values={"a": 3, "b": -5})
    assert positions(u.qualitative) == {2, 5, 6}
    u, _ = run("compare_absolute", o1="a", o2="b", values={"a": -5, "b": 5})
    assert positions(u.qualitative) == {3, 4, 5}


def test_p_not_allowed_as_second_operand():
    with pytest.raises(Incident):
        run("add", mode="N", o1="a", o2="P", r="r", values={"a": 1})


def test_not_a_number_operand_is_an_incident():
    bad = Number(False, 40, 0)
    s = Store(a=bad)

    def load(_):
        from gamma60.number import Number as N

        return N.from_catenae(0x00000A, 0)

    with pytest.raises(Incident):
        ArithmeticUnit().execute("add", mode="N", o1="a", o2="a", r="r", load=load, store=s.store)


def test_unknown_directive():
    with pytest.raises(ValueError):
        run("nothing", o1="a", values={"a": 1})
