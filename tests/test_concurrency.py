"""Concurrency (J4): recall chains, SIMU, joins, virtual elements, special cuts [COURS p.17-39]."""

from __future__ import annotations

import io
import itertools
from pathlib import Path

import pytest

from gamma60 import debug, machine, seq

PROGRAMS = Path(__file__).parent / "programs"


def branch(label: str, out: str, end: str = "STOP", element: str = "ARIT") -> str:
    op = "DIV N - 0 1 2" if element == "ARIT" else "ADD 4 2"
    return f"{label}: {element}\n    VIERGE\n    L 0 X\n    L 1 Y\n    L 2 {out}\n    {op}\n    {end}\n"


DATA = "X: NUM +22\nY: NUM +7\nO1: NUM +0\nO2: NUM +0\nO3: NUM +0\nO4: NUM +0\n"


def chain_events(m, whats=("queue", "resume", "release")):
    events = []

    def listen(r):
        if r.unit == "PD" and r.what in whats:
            b, c = m.memory.raw(4).value, m.memory.raw(5).value  # B, C of ARIT (number 2, U-30)
            events.append((r.what, r.get("sequence"), b, c))

    m.engine.listeners.append(listen)
    return events


# --- recall chain of a real element [COURS p.24-26, plate 3] ------------------------------------


def test_recall_chain_fifo():
    text = (
        "; langue: en\nSTART: SIMU S2 R\n    VIERGE\n    SIMU S3 R\n    VIERGE\n    SIMU S4 R\n"
        "    VIERGE\n"
        + branch("S1", "O1")
        + branch("S2", "O2")
        + branch("S3", "O3")
        + branch("S4", "O4")
        + DATA
    )
    m = machine.build(text)
    events = chain_events(m)
    result = m.run()
    assert result.status == "halted"
    blank = {k: m.image.labels[k] + 1 for k in ("S1", "S2", "S3", "S4")}
    # S2 takes ARIT; S3, S4 and S1 are queued: B = first waiting, C = last (COURS: 541, 113…)
    assert events[:3] == [
        ("queue", blank["S3"], blank["S3"], blank["S3"]),
        ("queue", blank["S4"], blank["S3"], blank["S4"]),
        ("queue", blank["S1"], blank["S3"], blank["S1"]),
    ]
    # they resume in the order they came; B follows the links, C is reset with the last one
    assert [e[:2] for e in events[3:]] == [
        ("resume", blank["S3"]),
        ("resume", blank["S4"]),
        ("resume", blank["S1"]),
        ("release", None),
    ]
    assert events[-1][2:] == (0, 0)
    assert all(m.memory.read(b) == 0 for b in blank.values())  # links cleared [COURS p.26]
    log = m.elements["arithmetic"].log
    assert all(a[1] <= b[0] for a, b in itertools.pairwise(log))  # never two at once


# --- SIMU cascade and the PD's own chain [COURS p.36-37] -----------------------------------------


def test_simu_cascade_on_the_extraordinary_branch():
    text = (
        "; langue: en\n"
        "START: SIMU B2 R\n    VIERGE\n"
        + branch("C1", "O1", "STOP")
        + "B2: SIMU B3 R\n    VIERGE\n"
        + branch("C2", "O2", "STOP", "LOGI")
        + "B3: SIMU B4 R\n    VIERGE\n    STOP\n"
        + "B4: ARIT\n    VIERGE\n    STOP\n"
        + DATA
    )
    m = machine.build(text)
    own = []
    m.engine.listeners.append(
        lambda r: (
            own.append(r.get("sequence"))
            if r.unit == "PD" and r.what == "resume own chain"
            else None
        )
    )
    result = m.run()
    assert result.status == "halted"
    labels = m.image.labels
    # the ordinary branches wait on the PD's chain and are taken in the order of the SIMU
    assert own == [labels["START"] + 1, labels["B2"] + 1, labels["B3"] + 1]
    assert m.dp.pd_b == m.dp.pd_c == 0


# --- forkjoin_tumlin and joins ------------------------------------------------------------------


@pytest.mark.parametrize("profile", ["B61", "COURS"])
def test_forkjoin_on_the_machine(profile):
    a = seq.run_file(PROGRAMS / "forkjoin_tumlin.g60b", profile)
    b = machine.run_file(PROGRAMS / "forkjoin_tumlin.g60b", profile)
    assert b.status == "halted"
    for label in "ABCDEF":
        assert a.number(label) == b.number(label)
    assert b.number("F").value == 132


@pytest.mark.parametrize("arrivals", [2, 3, 4])
def test_join_of_n_sequences(arrivals):
    m = arrivals - 1
    simus = "".join(f"    SIMU W{k} R\n    VIERGE\n" for k in range(2, arrivals + 1))
    branches = "".join(branch(f"W{k}", f"O{k}", "31 FIN") for k in range(1, arrivals + 1))
    text = (
        f"; langue: en\nSTART: {simus.lstrip()}    31 W1\n{branches}"
        f"FIN: LOGI {m}\n    VIERGE\n    STOP\n{DATA}"
    )
    mach = machine.build(text)
    joins = []
    mach.engine.listeners.append(
        lambda r: joins.append(r.get("arrival")) if r.what == "join" else None
    )
    result = mach.run()
    assert result.status == "halted"
    assert joins == list(range(1, arrivals + 1))  # effective at the last arrival only
    fin_blank = mach.image.labels["FIN"] + 1
    assert mach.memory.read(fin_blank) == 0  # counter reset when the join fires (U-26)
    assert all(result.number(f"O{k}").value > 3 for k in range(1, arrivals + 1))


# --- real parallelism ------------------------------------------------------------------------------


def test_arit_and_logi_work_at_the_same_time():
    result = machine.run_file(PROGRAMS / "parallele.g60b")
    m = result.machine
    assert result.status == "halted"
    assert str(result.number("R")) == "+41 4142|857142"  # 22 / 7 + 1
    assert m.memory.read(m.image.labels["M"]) == 1234 * 3001
    div = next(e for e in m.elements["arithmetic"].log if e[2] == "divide")
    mul = next(e for e in m.elements["logical"].log if e[2] == "multiply")
    assert div[0] < mul[1] and mul[0] < div[1]  # the two directives overlap in time
    # the same work without SIMU (ARIT branch, then LOGI branch, then the addition) is longer
    text = (PROGRAMS / "parallele.g60b").read_text(encoding="utf-8")
    first_goto = "        31          FIN          R\n"
    sequential = (
        text.replace("START:  SIMU        BRL          R", "START:  31          BRA          R")
        .replace(first_goto, "        31          BRL          R\n", 1)
        .replace("FIN:    ARIT  1", "FIN:    ARIT")
    )
    seq_run = machine.run_text(sequential)
    assert seq_run.status == "halted" and seq_run.number("R") == result.number("R")
    assert m.engine.now + 400 < seq_run.machine.engine.now  # the DIV (550 µs) is hidden


# --- virtual elements [COURS p.27-31, p.37] ---------------------------------------------------------


def test_virtual_element_serializes_protected_sections():
    def section(label, out):
        return (
            f"{label}: PROT IMG\n    VIERGE\n    ARIT\n    VIERGE\n    L 0 X\n    L 1 Y\n"
            f"    L 2 {out}\n    DIV N - 0 1 2\n    LOGI\n    VIERGE\n    L 0 X\n    L 1 Y\n"
            f"    L 2 {out}\n    ADD 4 L\n    LIBE IMG\n    VIERGE\n    STOP\n"
        )

    text = (
        "; langue: en\nSTART: SIMU P2 R\n    VIERGE\n    SIMU P3 R\n    VIERGE\n"
        + section("P1", "O1")
        + section("P2", "O2")
        + section("P3", "O3")
        + DATA
        + "IMG: ZONE 2\n"
    )
    m = machine.build(text)
    events = []
    m.engine.listeners.append(
        lambda r: (
            events.append(r.what)
            if r.unit == "PD" and r.what in ("occupy", "queue", "free", "own chain")
            else None
        )
    )
    result = m.run()
    assert result.status == "halted"
    assert events.count("occupy") == 1 and events.count("queue") == 2
    assert events[-1] == "free"
    image = m.image.labels["IMG"]
    assert m.memory.read(image) == 0 and m.memory.read(image + 1) == 0
    # protected sections never overlap: each LOGI step ends before the next DIV starts
    arit = [e for e in m.elements["arithmetic"].log]
    logi = [e for e in m.elements["logical"].log]
    for k in range(len(arit) - 1):
        assert logi[k][1] <= arit[k + 1][0]


# --- special cuts (COURS profile) [COURS p.39] --------------------------------------------------------


SPECIAL = (
    "; langue: fr\n; profil: COURS\n"
    "DEBUT: SIMU PRINC R\n    VIERGE\n"  # PRINC takes ARIT first; AUTRE then waits on its chain
    "AUTRE: ARIT\n    VIERGE\n    G 0 X\n    G 1 Y\n    G 2 O4\n    MUL N - 0 1 2\n    STOP\n"
    "PRINC: ARIT\n    VIERGE\n    G 0 X\n    G 1 Y\n    G 2 O1\n    DIV N - 0 1 2\n"
    "    LOGI{a}\n    VIERGE\n"  # « incident program » on LOGI
    "    G 0 X\n    G 1 Y\n    G 2 O2\n    ADD 4 L\n"
    "    ARIT{b}\n    VIERGE\n"  # back to ARIT
    "    G 0 X\n    G 1 Y\n    G 2 O3\n    ADD N - 0 1 2\n    STOP\n"
) + DATA


def test_special_cuts_for_an_incident_program():
    """COURS p.39: without release (« A »), then without busy check (« B »)."""
    special = machine.run_text(SPECIAL.format(a=" A", b=" B"))
    normal = machine.run_text(SPECIAL.format(a="", b=""))
    assert special.status == normal.status == "halted", special.message
    ops = [e[2] for e in special.machine.elements["arithmetic"].log]
    # ARIT is kept by the sequence while it runs on LOGI, then the sequence comes back to it
    # before AUTRE, which was waiting on ARIT's chain
    assert ops == ["divide", "add", "multiply"]
    # with normal cuts, LOGI releases ARIT: AUTRE runs in between
    assert [e[2] for e in normal.machine.elements["arithmetic"].log] == [
        "divide",
        "multiply",
        "add",
    ]


# --- debugger -----------------------------------------------------------------------------------------


def test_trace_shows_the_chains():
    out = io.StringIO()
    machine.run_file(
        PROGRAMS / "forkjoin_tumlin.g60b", observer=debug.RegisterTrace(debug.Names("en"), out)
    )
    text = out.getvalue()
    assert "pdc1" in text and "i1" in text and "i2" in text


def test_watch_an_element_in_the_stepper():
    out = io.StringIO()
    stepper = debug.Stepper(debug.Names("en"), io.StringIO("w LOGI\nc\nr\nc\n"), out)
    result = machine.run_file(PROGRAMS / "parallele.g60b", observer=stepper)
    assert result.status == "halted"
    assert "watch LOGI" in out.getvalue()
