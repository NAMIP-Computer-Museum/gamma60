"""Arithmetic calculator (ARIT): exact decimal semantics, no timing.

Semantics from COURS p.63-72 and B61 p.35-36 (summarised in docs/MACHINE.md §8). The unit
holds three two-catena registers: P (principal: 1st operand, then result, high digits), S
(secondary: low digits, same sign, exponent of P − 10) and O (2nd operand). Operands are
fetched and results stored through callables, so the unit is independent of memory, RACs and
time. Behaviour the sources leave open is read from ``data/behavior.yaml`` (U-35 to U-37).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from fractions import Fraction

from gamma60 import data
from gamma60.number import EXPONENT_MAX, MANTISSA_LIMIT, NotANumber, Number

#: Operand designator: "P" (register P) or ("rac", index, progress).
Designator = str | tuple[str, int, bool]

ZERO = Number(False, 0, 0)
DIGITS20 = 10**20


class Incident(Exception):
    """The unit sets its incident indicators and stops the sequence (U-37)."""


def _rules() -> dict:
    return data.resolve(data.load("behavior")["arit_fitting"])


def _exponent_out_of_range(exponent: int) -> Number:
    """Apply the U-35 rule to an exponent outside 0-79; return the zero to use instead.

    The sources give the bounds (COURS p.63, B61 p.18) but not what happens beyond them in
    normalised form: overflow (> 79) and underflow (< 0) are read from behavior.yaml.
    """
    rules = _rules()
    key, allowed = (
        ("exponent_overflow", ("incident",))
        if exponent > EXPONENT_MAX
        else ("exponent_underflow", ("incident", "zero"))
    )
    action = rules[key]
    if action not in allowed:
        raise ValueError(f"{key}: unsupported value {action!r} (expected one of {allowed})")
    if action == "incident":
        raise Incident(f"exponent {exponent} outside 0-79")
    return Number(False, rules["zero_exponent_normalized"], 0)


def set_position(qualitative: int, position: int) -> int:
    return qualitative | (1 << (position - 1))


def magnitude(a: Fraction) -> int:
    """k such that 10^(k-1) <= a < 10^k (a > 0)."""
    k = len(str(a.numerator)) - len(str(a.denominator))
    while a >= Fraction(10) ** k:
        k += 1
    while a < Fraction(10) ** (k - 1):
        k -= 1
    return k


def fit(value: Fraction, point: int | None) -> tuple[Number, Number]:
    """Put an exact value into the accumulator P + S.

    ``point`` None = normalised (first digit of P significant); otherwise programmed point
    at boundary ``point`` (0-10) of P, exponent 50 − point. Digits beyond the 20 of P + S
    are truncated (U-35); lost high digits raise an incident.
    """
    rules = _rules()
    negative = value < 0
    a = abs(value)
    if point is None:
        exponent = rules["zero_exponent_normalized"] if a == 0 else 40 + magnitude(a)
    else:
        if not 0 <= point <= 10:
            raise Incident(f"decimal point position {point} outside 0-10")
        exponent = 50 - point
    if not 0 <= exponent <= EXPONENT_MAX:
        zero = _exponent_out_of_range(exponent)  # U-35
        return zero, Number(False, max(zero.exponent - 10, 0), 0)
    scaled = a * Fraction(10) ** (60 - exponent)
    digits = scaled.numerator // scaled.denominator  # truncation toward zero
    if digits >= DIGITS20:
        raise Incident("overflow: high-order digits lost")
    high, low = divmod(digits, MANTISSA_LIMIT)
    negative = negative and digits > 0
    s_exponent = exponent - 10
    if s_exponent < 0:  # S cannot hold digits below exponent 0: they are lost (U-35)
        s_exponent, low = 0, 0
    return Number(negative, exponent, high), Number(negative, s_exponent, low)


def accumulator_value(p: Number, s: Number) -> Fraction:
    return p.value + s.value


def sign_positions(value: Fraction) -> int:
    """Qualitative positions 7 (= 0), 8 (< 0), 9 (> 0) [COURS p.65]."""
    return set_position(0, 7 if value == 0 else 8 if value < 0 else 9)


def compare_positions(x: Fraction, y: Fraction) -> int:
    """Qualitative positions 1-6: > < = >= <= != [B61 p.35 ; COURS p.72]."""
    q = 0
    for position, holds in enumerate((x > y, x < y, x == y, x >= y, x <= y, x != y), 1):
        if holds:
            q = set_position(q, position)
    return q


def round_off(p: Number, s: Number) -> Number:
    """Round to the nearest on the last digit of P: add 5 to the first digit of S."""
    digits = p.mantissa * MANTISSA_LIMIT + s.mantissa + 5 * 10**9
    high = digits // MANTISSA_LIMIT
    exponent = p.exponent
    if high >= MANTISSA_LIMIT:  # carry out of P: shift right, exponent + 1
        high //= 10
        exponent += 1
        if exponent > EXPONENT_MAX:
            _exponent_out_of_range(exponent)  # U-35
    return Number(p.negative and high > 0, exponent, high)


def _shift_exponent(n: Number, delta: int) -> Number:
    e = n.exponent + delta
    if not 0 <= e <= EXPONENT_MAX:
        return _exponent_out_of_range(e)  # U-35
    return Number(n.negative, e, n.mantissa)


@dataclass
class ArithmeticUnit:
    p: Number = ZERO
    s: Number = ZERO
    o: Number = ZERO
    qualitative: int = 0

    def execute(
        self,
        op: str,
        *,
        mode: str | None = None,
        double: bool = False,
        point: int | None = None,
        o1: Designator | None = None,
        o2: Designator | None = None,
        r: Designator | None = None,
        load: Callable[[Designator], Number],
        store: Callable[[Designator, Sequence[Number]], None],
    ) -> None:
        """Run one directive (identifiers of data/directives.yaml, elements.arithmetic).

        ``mode``: "P" programmed point, "N" normalised, "A" normalised then rounded, None.
        ``point``: V field (0-10 point position, or 0-15 power of ten for MPT/DPT).
        """
        if data.resolve(data.load("behavior")["qualitative_reset_each_directive"]):
            self.qualitative = 0  # U-07
        try:
            self._execute(op, mode, double, point, o1, o2, r, load, store)
        except (Incident, NotANumber) as exc:
            for position in data.resolve(data.load("behavior")["incident"])[
                "qualitative_positions"
            ]:
                self.qualitative = set_position(self.qualitative, position)
            raise Incident(str(exc)) from exc

    # -- helpers ---------------------------------------------------------------------------

    def _operand(self, designator: Designator, load) -> Number:
        if designator == "P":
            return self.p
        return load(designator)

    def _point(self, mode: str | None, point: int | None) -> int | None:
        if mode == "P":
            return _rules()["missing_point_position"] if point is None else point
        return None

    def _result(self, value: Fraction, r, double, store, numbers: Sequence[Number]) -> None:
        self.qualitative |= sign_positions(value)
        if r is not None and r != "P":
            store(r, list(numbers) if double else list(numbers[:1]))

    # -- directives ------------------------------------------------------------------------

    def _execute(self, op, mode, double, point, o1, o2, r, load, store) -> None:
        if o2 == "P":
            raise Incident("P is not allowed as second operand")
        if op in ("add", "subtract", "multiply"):
            self.s = ZERO  # S cleared before the operation, even if O1 = P [COURS p.70]
            x = self._operand(o1, load).value
            self.o = load(o2)
            y = self.o.value
            value = x + y if op == "add" else x - y if op == "subtract" else x * y
            self.p, self.s = fit(value, self._point(mode, point))
            if mode == "A":
                self.p, self.s = round_off(self.p, self.s), ZERO
            self._result(accumulator_value(self.p, self.s), r, double, store, (self.p, self.s))
        elif op in ("divide", "divide_with_remainder"):
            self.s = ZERO
            x = self._operand(o1, load).value
            self.o = load(o2)
            y = self.o.value
            if y == 0:
                raise Incident("division by zero")
            exact = x / y
            pt = self._point(mode, point)
            if pt is None:
                quotient = fit(exact, None)[0]  # 10 significant digits, truncated
            else:
                scaled = abs(exact) * 10**pt
                truncated = Fraction(scaled.numerator // scaled.denominator, 10**pt)
                quotient, rest = fit(-truncated if exact < 0 else truncated, pt)
                if rest.mantissa:
                    raise Incident("quotient does not fit in the register")
            remainder = fit(x - quotient.value * y, None)[0]  # U-36
            if op == "divide":
                self.p, self.s = quotient, ZERO
                self._result(quotient.value, r, False, store, (self.p,))
            else:
                self.p, self.s = remainder, quotient
                self._result(remainder.value, r, double, store, (self.p, self.s))
        elif op == "transfer":
            if o1 == "P":
                value = accumulator_value(self.p, self.s)
                source = (self.p, self.s)
            else:
                self.s = ZERO
                loaded = load(o1)
                value, source = loaded.value, (loaded, ZERO)
            if mode is None:
                self.p, self.s = source
            else:
                self.p, self.s = fit(value, self._point(mode, point))
                if mode == "A":
                    self.p, self.s = round_off(self.p, self.s), ZERO
            self._result(accumulator_value(self.p, self.s), r, double, store, (self.p, self.s))
        elif op in ("multiply_pow10", "divide_pow10", "reverse_sign", "absolute_value"):
            if o1 == "P":
                p, s = self.p, self.s
            else:
                p, s = load(o1), ZERO
            if op in ("multiply_pow10", "divide_pow10"):
                n = point or 0
                if not 0 <= n <= 15:
                    raise Incident(f"power of ten {n} outside 0-15")
                delta = n if op == "multiply_pow10" else -n
                p = _shift_exponent(p, delta)
                if s.mantissa and s.exponent + delta < 0:  # S below exponent 0: lost (U-35)
                    s = Number(False, 0, 0)
                elif s.mantissa:
                    s = _shift_exponent(s, delta)
            else:
                negative = (not p.negative) if op == "reverse_sign" else False
                p = Number(negative and p.mantissa > 0, p.exponent, p.mantissa)
                s = Number(negative and s.mantissa > 0, s.exponent, s.mantissa)
            self.p, self.s = p, s
            self._result(accumulator_value(p, s), r, double and o1 == "P", store, (p, s))
        elif op in ("compare_absolute", "compare_algebraic"):
            first = self._operand(o1, load)
            self.o = load(o2)
            x, y = first.value, self.o.value
            if op == "compare_absolute":
                x, y = abs(x), abs(y)
            self.qualitative |= compare_positions(x, y)
        elif op == "round_off":
            self.p, self.s = round_off(self.p, self.s), ZERO
            self._result(self.p.value, r, False, store, (self.p,))
        else:
            raise ValueError(f"unknown ARIT directive {op!r}")
