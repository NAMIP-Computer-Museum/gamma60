"""ASCII timelines (``run --gantt``): alignment, attribution of the sequences, options."""

from __future__ import annotations

from pathlib import Path

import pytest

from gamma60 import debug, machine
from gamma60.__main__ import main
from gamma60.gantt import LABEL, Gantt, auto_scale

PROGRAMS = Path(__file__).parent / "programs"


def chart(name="parallele.g60b", language="en", **kw):
    m = machine.run_file(PROGRAMS / name).machine
    return m, Gantt(m, debug.Names(language), program_name=name, **kw)


def row(lines, title):
    line = next(line for line in lines if line.startswith(title.ljust(LABEL)))
    return line[LABEL:].ljust(len(lines[2]) - LABEL)  # sequence rows are right-stripped


# --- alignment -----------------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["parallele.g60b", "forkjoin_tumlin.g60b", "arit_logi.g60b"])
def test_every_row_has_one_character_per_column(name):
    m, g = chart(name, scale=25)
    lines = g.by_element()
    columns = m.engine.now // 25 + 1
    assert g.columns == columns
    ruler = lines[2][LABEL:]
    assert len(ruler) == columns  # the time axis goes exactly to the end of the rows
    for title in ("PD", "ARIT", "mem"):
        assert len(row(lines, title)) == columns
    for c in range(0, columns, 20):  # a labelled tick every 20 columns, label on its tick
        assert ruler[c] == "|"
        text = str(c * 25)
        assert lines[1][LABEL + c : LABEL + c + len(text)] == text


def test_bars_start_and_end_in_the_columns_of_their_dates():
    m, g = chart(scale=25)
    lines = g.by_element()
    for kind, title in (("arithmetic", "ARIT"), ("logical", "LOGI")):
        r = row(lines, title)
        for a, b, _op in m.elements[kind].log:
            assert r[a // 25] == "[" and r[(b - 1) // 25] == "]"
    assert "[DIV" in row(lines, "ARIT") and "[MUL" in row(lines, "LOGI")
    stop = next(r.time for r in m.engine.trace if r.what == "stop")
    assert row(lines, "PD")[stop // 25] == "S"
    mem = next(i for i, line in enumerate(lines) if line.startswith("mem"))
    marks = lines[mem + 1][LABEL:]
    for r in m.engine.trace:
        if r.what == "join":
            assert marks[r.time // 25] == "^"
    assert lines[mem + 2].endswith("1000 us JOIN 1/2 ; 1660 us JOIN 2/2")


def test_mem_counts_the_transfers():
    m, g = chart(scale=25)
    transfers = sum(1 for r in m.engine.trace if r.what == "transfer")
    assert sum(g.mem) == transfers
    assert max(g.mem) <= 3  # 25 us = 2.5 cycles of 10 us


# --- view by sequence -------------------------------------------------------------------------------


def test_parallel_sequences():
    m, g = chart(scale=25)
    lines = g.by_sequence()
    joins = [r.time for r in m.engine.trace if r.what == "join"]
    assert row(lines, "START").strip() == ">"  # the SIMU forks the start sequence
    assert row(lines, "BRA")[joins[0] // 25] == "|"  # first arrival: stops at the join
    assert row(lines, "BRL")[joins[1] // 25] == ">"  # second arrival: the join is passed
    fin = row(lines, "FIN").rstrip()
    assert fin.endswith("S") and set(fin.strip()) <= {"A", "~", "S"}
    bra, brl = row(lines, "BRA"), row(lines, "BRL")
    both = [c for c in range(g.columns) if bra[c] == "A" and brl[c] == "L"]
    assert len(both) > 10  # ARIT and LOGI work for the two sequences at the same time


def test_serialized_sequences_wait_on_the_recall_chain():
    _, g = chart("forkjoin_tumlin.g60b", scale=25)
    lines = g.by_sequence()
    i1, i2 = row(lines, "I1"), row(lines, "I2")
    assert "." in i1  # I1 waits on ARIT's chain…
    assert not any(i1[c] == "A" and i2[c] == "A" for c in range(g.columns))  # …never together
    assert row(lines, "I3").rstrip().endswith("S")


# --- scale, window, names ------------------------------------------------------------------------------


def test_auto_scale_fits_in_100_columns():
    assert auto_scale(2040) == 25 and auto_scale(26680) == 500 and auto_scale(80) == 1
    _, g = chart("pi.g60b")
    assert g.scale == 500 and g.columns <= 100
    arit = row(g.by_element(), "ARIT")
    assert "[" not in arit and set(arit) <= {"=", ".", "~"}  # short directives: just "busy"


def test_window():
    _, g = chart(scale=10, start=500, stop=1100)
    lines = g.by_element()
    assert "(500-1100 us)" in lines[0] and lines[1][LABEL:].startswith("500")
    assert row(lines, "ARIT").startswith("=DIV")  # began before the window: no "["
    assert row(lines, "LOGI").rstrip().endswith("=")  # MUL goes on after the window: no "]"
    with pytest.raises(ValueError):
        chart(start=3000, stop=10)


def test_names_follow_the_language():
    _, g = chart(language="fr")
    assert any(line.startswith("DP ") for line in g.by_element())


# --- command line -----------------------------------------------------------------------------------


def test_cli_gantt(capsys):
    assert main(["run", str(PROGRAMS / "parallele.g60b"), "--gantt"]) == 0
    out = capsys.readouterr().out
    assert "1 char = 25 us" in out and "[DIV" in out and "mem" in out
    assert (
        main(["run", str(PROGRAMS / "parallele.g60b"), "--gantt=seq", "--gantt-scale", "50"]) == 0
    )
    out = capsys.readouterr().out
    assert "1 char = 50 us" in out and "BRL" in out
    args = ["run", str(PROGRAMS / "parallele.g60b"), "--gantt", "--gantt-from", "500"]
    assert main([*args, "--gantt-to", "1100"]) == 0
    assert "(500-1100 us)" in capsys.readouterr().out


def test_cli_gantt_needs_the_machine(capsys):
    assert main(["run", str(PROGRAMS / "forkjoin_tumlin.g60b"), "--seq", "--gantt"]) == 2
    assert "needs the machine" in capsys.readouterr().out


def test_gantt_does_not_change_the_run():
    a = machine.run_file(PROGRAMS / "parallele.g60b").machine
    Gantt(a, debug.Names("en")).by_sequence()
    b = machine.run_file(PROGRAMS / "parallele.g60b").machine
    assert a.engine.trace == b.engine.trace


# --- legends ------------------------------------------------------------------------------------


def test_legend_under_each_view():
    _, g = chart()
    lines = g.by_element()
    start = lines.index("legend:")
    legend = "\n".join(lines[start:])
    assert "A=ARIT L=LOGI" in legend and "~ waiting for the PD" in legend and "mem:" in legend
    assert "cut by the time window" not in legend  # only shown with a window
    seq = g.by_sequence()
    legend = "\n".join(seq[seq.index("legend:") :])
    assert ". waiting on a recall chain" in legend and "| stops at a join" in legend


def test_legend_with_a_window_and_in_french():
    _, g = chart(language="fr", start=500, stop=1100)
    lines = g.by_element()
    legend = "\n".join(lines[lines.index("legende:") :])
    assert "fenetre de temps" in legend and "DP :" in legend
    assert all(ord(c) < 128 for line in lines for c in line)  # plain ASCII in both languages
