"""Discrete-event engine (J2): simulated time, deterministic order, trace."""

import pytest

from gamma60.engine import Engine


def test_events_run_in_date_then_scheduling_order():
    e, seen = Engine(), []
    e.at(20, lambda: seen.append("b"))
    e.at(10, lambda: seen.append("a"))
    e.at(20, lambda: seen.append("c"))  # same date as "b": scheduled later, runs later
    e.run()
    assert seen == ["a", "b", "c"] and e.now == 20


def test_after_and_nested_scheduling():
    e, seen = Engine(), []

    def first():
        seen.append(e.now)
        e.after(5, lambda: seen.append(e.now))

    e.after(10, first)
    e.run()
    assert seen == [10, 15]


def test_run_until_is_inclusive_and_advances_time():
    e, seen = Engine(), []
    for t in (10, 20, 30):
        e.at(t, lambda t=t: seen.append(t))
    assert e.run(until=20) == 2 and seen == [10, 20] and e.now == 20
    assert e.pending() == 1
    e.run(until=100)
    assert seen == [10, 20, 30] and e.now == 100


def test_cancel():
    e, seen = Engine(), []
    ev = e.at(5, lambda: seen.append("x"))
    Engine.cancel(ev)
    e.run()
    assert seen == [] and e.pending() == 0


def test_no_scheduling_in_the_past():
    e = Engine()
    e.at(10, lambda: None)
    e.run()
    with pytest.raises(ValueError):
        e.at(5, lambda: None)


def test_trace_records_and_listeners():
    e, heard = Engine(), []
    e.listeners.append(heard.append)
    e.at(7, lambda: e.record("DD", "transfer", element="ARIT", address=12))
    e.run()
    (rec,) = e.trace
    assert (rec.time, rec.unit, rec.what, rec.get("address")) == (7, "DD", "transfer", 12)
    assert heard == [rec] and rec.get("missing", "-") == "-"


def test_same_input_same_trace():
    def scenario():
        e = Engine()
        for k in range(50):
            e.at((k * 7) % 13, lambda k=k: e.record("X", "tick", k=k))
        e.run()
        return e.trace

    assert scenario() == scenario()
