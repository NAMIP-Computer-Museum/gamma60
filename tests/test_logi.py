"""LOGI: every directive of data/directives.yaml (elements.logical) [COURS p.110-119]."""

import pytest

from gamma60 import data
from gamma60.core.arit import Incident
from gamma60.core.logi import LogicalUnit, rotate_right


def positions(q: int) -> set[int]:
    return {i + 1 for i in range(24) if q >> i & 1}


class Mem:
    def __init__(self, **values):
        self.values = dict(values)
        self.stored: dict[str, int] = {}

    def load(self, d):
        return self.values[d]

    def store(self, d, value):
        self.stored[d] = value


def run(op, unit=None, length=0, r="L", **values):
    unit = unit or LogicalUnit()
    m = Mem(**values)
    unit.execute(op, length=length, r=r, load=m.load, store=m.store)
    return unit, m


def test_all_directives_are_covered():
    ids = set(data.load("directives")["elements"]["logical"]["directives"])
    tested = {name[5:] for name in globals() if name.startswith("test_")}
    assert ids <= tested, ids - tested


def test_rotate_right():
    assert rotate_right(1, 1) == 1 << 23
    assert rotate_right(0xABCDEF, 24) == 0xABCDEF


def test_transfer_shift_to_K():
    u, _ = run("transfer_shift_to_K", length=4, r="m", m=0x000012)
    assert u.k == 0x200001  # circular shift right by 4 [COURS p.112]


def test_transfer_shift_to_L():
    u, _ = run("transfer_shift_to_L", length=0, r="m", m=0x123456)
    assert u.l == 0x123456
    with pytest.raises(Incident):
        run("transfer_shift_to_L", length=0, r="L")  # L meaningless in R


def test_transfer_K_to_L():
    u, m = run("transfer_K_to_L", unit=LogicalUnit(k=0xFFFFFF, l=0x123456), length=8, r="m")
    assert u.l == 0xFF and u.k == 0xFFFFFF and m.stored["m"] == 0xFF


def test_shift_left_L():
    u, _ = run("shift_left_L", unit=LogicalUnit(l=0x000001), length=23)
    assert u.l == 0x000002  # left shift by n = right rotation by 24 - n


def test_filter_example_of_cours():
    """Keep bits between boundaries 10 and 17, clear the rest: TCK 10, TKL 07, MCL 14."""
    x = 0b101101101101101101101101
    u, _ = run("transfer_shift_to_K", length=10, r="m", m=x)
    run("transfer_K_to_L", unit=u, length=7)
    _, m = run("shift_left_L", unit=u, length=14, r="m")
    assert m.stored["m"] == x & (0b1111111 << 10)  # [COURS p.112-113]


def test_insert_K_in_L():
    u, _ = run("insert_K_in_L", unit=LogicalUnit(k=0x00000A, l=0xFFFFF0), length=4)
    assert u.l == rotate_right(0xFFFFFA, 4) and u.k == rotate_right(0x00000A, 4)


def test_fill_zeros_L():
    u, _ = run("fill_zeros_L", unit=LogicalUnit(l=0xFFFFFF), length=4)
    assert u.l == rotate_right(0xFFFFF0, 4)


def test_fill_ones_L():
    u, _ = run("fill_ones_L", unit=LogicalUnit(l=0), length=4)
    assert u.l == rotate_right(0x00000F, 4)


def test_add():
    u, _ = run("add", unit=LogicalUnit(k=0xF00005, l=3), length=4)
    assert u.l == 8 and u.k == 0xF00005  # only the l rightmost bits of K
    u, _ = run("add", unit=LogicalUnit(k=1, l=0xFFFFFF), length=1)
    assert u.l == 0  # carry beyond bit 24 lost (U-38)


def test_subtract():
    u, _ = run("subtract", unit=LogicalUnit(k=9, l=3), length=4)
    assert u.l == 6  # |B - A| [COURS p.114]


def test_multiply():
    u, _ = run("multiply", unit=LogicalUnit(k=0xF00006, l=7), length=4)
    assert u.l == 42 and u.k == 6  # bits 24 - l of K cleared
    with pytest.raises(Incident):
        run("multiply", unit=LogicalUnit(k=0xFFF, l=0xFFFFF), length=12)


def test_divide():  # example of COURS p.116-117
    dividend = 0b000000000011110110111111  # COURS p.117: quotient 110001011001, remainder 10
    with pytest.raises(Incident):
        run("divide", unit=LogicalUnit(k=0b101, l=dividend), length=16)  # quotient too long
    u, _ = run("divide", unit=LogicalUnit(k=0b101, l=dividend), length=10)
    assert u.l & ((1 << 14) - 1) == 0b110001011001
    assert u.l >> 14 == 0b10
    with pytest.raises(Incident):
        run("divide", unit=LogicalUnit(k=0, l=1), length=4)


def test_complement_L():
    u, _ = run("complement_L", unit=LogicalUnit(l=0xA0005A), length=6)
    assert u.l == 0xA00065  # low 6 bits 011010 -> 100101, rest kept, no shift


def test_intersection():
    u, _ = run("intersection", unit=LogicalUnit(k=0b1100, l=0xF0_101E), length=4)
    assert u.l == 0xF0_101C  # 1110 AND 1100 = 1100, rest of L kept


def test_union():
    u, _ = run("union", unit=LogicalUnit(k=0b10101, l=0b11010), length=5)
    assert u.l == 0b11111


@pytest.mark.parametrize(
    ("k", "l_", "length", "expected"),
    [  # examples of COURS p.119
        (0b1011, 0b1001, 4, 7),  # L included in K
        (0b10101, 0b11100, 5, 8),  # L not included in K
        (0b111001, 0b000110, 6, 11),  # K excluded from L
        (0b101001, 0b011110, 6, 12),  # overlap
        (0b10101, 0b11010, 5, 13),  # union all ones
        (0b10101, 0b10011, 5, 14),  # union with a zero
    ],
)
def test_binary_logical_compare(k, l_, length, expected):
    u, m = run("binary_logical_compare", unit=LogicalUnit(k=k, l=l_), length=length, r="m")
    assert expected in positions(u.qualitative)
    assert not m.stored and (u.k, u.l) == (k, l_)  # nothing stored, registers kept


def test_compare_orders():
    u, _ = run("binary_logical_compare", unit=LogicalUnit(k=3, l=5), length=4)
    assert {1, 4, 6} <= positions(u.qualitative)  # L > K, L >= K, L != K (2-6: U-38)


def test_store_through_rac_keeps_l():
    u, m = run("complement_L", unit=LogicalUnit(l=0), length=3, r="m")
    assert m.stored["m"] == 7 and u.l == 7


def test_length_out_of_range():
    with pytest.raises(Incident):
        run("add", length=25)
