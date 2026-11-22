"""ASCII timelines of a run (``run --gantt``): by element, or by sequence.

Both views are computed from the trace of the engine after the run; they change nothing in the
simulation. Column c covers the dates [start + c × scale, start + (c + 1) × scale[ µs; the last
column holds the end of the run (or of the window). The ruler and every row have exactly one
character per column; a time label starts on its tick.

View by element (one row per unit):

- ``PD``: letter of the element served when the PD reads an instruction (``A`` ARIT,
  ``L`` LOGI…), ``F`` when it works for itself (start, SIMU, its own chain), ``S`` for a STOP;
- one row per element that worked: ``[DIV===]`` a directive (name shortened, or left out when
  the bar is too short), ``~`` waiting for the PD (instruction request raised), ``.`` idle;
- ``mem``: number of catenae transferred by the Data Distributor in the column (``.`` none);
- markers ``^`` under the rows: SIMU and join arrivals, listed below.

View by sequence (one row per sequence, named after the label where it starts): the letter of
the element working for it (``A``, ``L``: the PD reading its instructions, or the element
executing its directive), ``F`` the PD working for itself, ``~`` waiting for the PD, ``.``
waiting for a busy element on its recall chain; it ends with ``>`` (SIMU or join passed),
``|`` (join not yet complete: the sequence stops there) or ``S`` (STOP).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gamma60 import data
from gamma60.code_a import CUT, ELEMENT
from gamma60.debug import Names, unit_name

LABEL = 7

#: legends printed under the timelines (plain ASCII in both languages)
LEGEND = {
    "en": {
        "title": "legend",
        "bar": "[DIV===] directive (code B mnemonic)   === short directive   ~ waiting for the PD"
        "   . idle",
        "cut": "=DIV===   no bracket on a side cut by the time window",
        "pd": "{pd}: letter of the element served ({letters})   F the PD for itself   S STOP"
        "   . free",
        "mem": "mem: catenae transferred by the DD in the column (1-9, . none)"
        "   ^ events listed above",
        "seq": "letter of the element working for the sequence ({letters})   F the PD for itself",
        "wait": "~ waiting for the PD   . waiting on a recall chain (busy element)   blank: not running",
        "end": "end: > fork (SIMU) or join passed   | stops at a join not yet complete   S STOP",
    },
    "fr": {
        "title": "legende",
        "bar": "[DIV===] directive (mnemonique du code B)   === directive courte   ~ attente du DP"
        "   . repos",
        "cut": "=DIV===   pas de crochet du cote coupe par la fenetre de temps",
        "pd": "{pd} : lettre de l'element servi ({letters})   F le DP pour lui-meme   S STOP"
        "   . libre",
        "mem": "mem : catenes transferes par le DD dans la colonne (1-9, . aucun)"
        "   ^ evenements ci-dessus",
        "seq": "lettre de l'element qui travaille pour la sequence ({letters})"
        "   F le DP pour lui-meme",
        "wait": "~ attente du DP   . attente sur une chaine de reprise (element occupe)"
        "   blanc : hors sequence",
        "end": "fin : > separation (SIMU) ou JOIN franchi   | arret sur un JOIN incomplet   S STOP",
    },
}
TICK = 20  # columns between two labelled ticks; "+" half way
SCALES = (1, 2, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 25000, 50000)
SHORT = {
    "add": "ADD",
    "subtract": "SUB",
    "multiply": "MUL",
    "divide": "DIV",
    "divide_with_remainder": "DIR",
    "transfer": "TRA",
    "multiply_pow10": "MPT",
    "divide_pow10": "DPT",
    "reverse_sign": "RSI",
    "absolute_value": "AVA",
    "compare_absolute": "CAV",
    "compare_algebraic": "CAL",
    "round_off": "ROF",
    "transfer_shift_to_K": "K",
    "transfer_shift_to_L": "L",
    "transfer_K_to_L": "TKL",
    "shift_left_L": "SHL",
    "insert_K_in_L": "IKL",
    "fill_zeros_L": "FZL",
    "fill_ones_L": "FOL",
    "complement_L": "FLC",
    "intersection": "INT",
    "union": "REU",
    "binary_logical_compare": "BLC",
}


def auto_scale(duration: int, columns: int = 100) -> int:
    """Smallest round scale (µs per character) that fits ``duration`` in ``columns``."""
    return next((s for s in SCALES if duration // s + 1 <= columns), SCALES[-1])


@dataclass
class Gantt:
    machine: object
    names: Names
    scale: int | None = None
    start: int = 0
    stop: int | None = None
    program_name: str = ""
    columns: int = field(init=False)

    def __post_init__(self) -> None:
        m = self.machine
        self.stop = m.engine.now if self.stop is None else min(self.stop, m.engine.now)
        if self.stop < self.start:
            raise ValueError(f"empty window {self.start}-{self.stop} us")
        self.scale = self.scale or auto_scale(self.stop - self.start)
        self.columns = (self.stop - self.start) // self.scale + 1
        self.kind_of = {e.name: k for k, e in m.elements.items()}
        self.letter = {k: self.names.element(e.kind)[0] for k, e in m.elements.items()}
        self.addr_label = {a: lab for lab, a in m.image.labels.items()}
        self._replay()

    # -- geometry -----------------------------------------------------------------------------

    def col(self, t: int) -> int | None:
        """Column of a date, None outside the window."""
        if t < self.start or t > self.stop:
            return None
        return min(self.columns - 1, (t - self.start) // self.scale)

    def span(self, a: int, b: int) -> tuple[int, int] | None:
        """Columns covered by [a, b[, clipped to the window."""
        if b <= a:
            b = a + 1
        if b <= self.start or a > self.stop:
            return None
        c0 = self.col(max(a, self.start))
        c1 = self.col(min(b - 1, self.stop))
        return c0, max(c0, c1)

    def _row(self, ch: str = ".") -> list[str]:
        return [ch] * self.columns

    def _put(self, row: list[str], t: int, ch: str) -> None:
        c = self.col(t)
        if c is not None:
            row[c] = ch

    def axis(self, title: str) -> list[str]:
        labels = [(c, str(self.start + c * self.scale)) for c in range(0, self.columns, TICK)]
        width = max(self.columns, max(c + len(s) for c, s in labels))
        marks = [" "] * width
        for c, s in labels:
            marks[c : c + len(s)] = list(s)
        ruler = [
            "|" if c % TICK == 0 else "+" if c % (TICK // 2) == 0 else "-"
            for c in range(self.columns)
        ]
        return [title.ljust(LABEL) + "".join(marks).rstrip(), " " * LABEL + "".join(ruler)]

    def title(self) -> str:
        m = self.machine
        window = f" ({self.start}-{self.stop} us)" if self.start or self.stop < m.engine.now else ""
        return (
            f"{self.program_name} - {m.profile.name} - {m.engine.now} us{window}"
            f" - 1 char = {self.scale} us"
        )

    # -- replay of the trace ------------------------------------------------------------------

    def _label_at(self, address: int) -> str:
        return self.addr_label.get(address, f"@{address:05d}")

    def _replay(self) -> None:
        m = self.machine
        entry = m.image.entry
        flow = self._label_at(entry)
        self.pd = self._row()
        self.mem = [0] * self.columns
        self.waits: dict[str, list[tuple[int, int]]] = {k: [] for k in m.elements}
        self.events: list[tuple[int, str]] = []
        self.seq_rows: dict[str, list[str]] = {}
        self.seq_first: dict[str, int] = {}
        self.seq_end: dict[str, tuple[int, str]] = {}
        self.chain_wait: dict[str, list[list[int | None]]] = {}
        raised: dict[str, int] = {}
        elem_seq: dict[str, str] = {}
        own_pending: dict[int, str] = {}
        chain_pending: dict[int, str] = {}
        self.directive_seq: dict[str, list[str]] = {k: [] for k in m.elements}

        def mark(seq: str, t: int, ch: str) -> None:
            row = self.seq_rows.setdefault(seq, self._row(" "))
            self.seq_first.setdefault(seq, t)
            c = self.col(t)
            if c is not None and (row[c] in " ~." or ch != "F"):
                row[c] = ch

        for r in m.engine.trace:
            unit, what = r.unit, r.what
            if what == "transfer":
                c = self.col(r.time)
                if c is not None:
                    self.mem[c] += 1
                continue
            if unit in self.kind_of and what == "done":
                raised[unit] = r.time
                continue
            if unit != "PD":
                continue
            if what == "serve":
                element = r.get("element")
                flow = elem_seq.get(element, flow)
                if element in raised:
                    self.waits[self.kind_of[element]].append((raised.pop(element), r.time))
            elif what == "instruction":
                element = r.get("element")
                ch = self.letter.get(self.kind_of.get(element), "F")
                c = self.col(r.time)
                if c is not None and self.pd[c] in ".F":
                    self.pd[c] = ch
                mark(flow, r.time, ch)
                word = r.get("word")
                if word.kind == CUT and word.op == "SIMU":
                    a = r.get("address")
                    x = (a + word.x) & 0o77777 if word.d else word.x
                    own_pending[a + 1] = self._label_at(a + 2)
                    self.seq_end[flow] = (r.time, ">")
                    self.events.append((r.time, "SIMU"))
                    flow = self._label_at(x)
                elif word.kind == ELEMENT and element in self.kind_of:
                    self.directive_seq[self.kind_of[element]].append(flow)
            elif what == "resume own chain":
                flow = own_pending.get(r.get("sequence"), flow)
            elif what == "cut":  # activation of an element for the current sequence
                elem_seq[r.get("element")] = flow
                raised[r.get("element")] = r.time
            elif what == "queue" and r.get("element"):
                chain_pending[r.get("sequence")] = flow
                self.chain_wait.setdefault(flow, []).append([r.time, None])
            elif what == "resume":
                seq = chain_pending.pop(r.get("sequence"), flow)
                elem_seq[r.get("element")] = seq
                raised[r.get("element")] = r.time
                if self.chain_wait.get(seq):
                    self.chain_wait[seq][-1][1] = r.time
            elif what == "join":
                arrival, expected = r.get("arrival"), r.get("expected")
                self.events.append((r.time, f"JOIN {arrival}/{expected}"))
                self.seq_end[flow] = (r.time, "|" if arrival < expected else ">")
                if arrival == expected:
                    flow = self._label_at(r.get("address"))
            elif what == "stop":
                self._put(self.pd, r.time, "S")
                self.seq_end[flow] = (r.time, "S")

        for kind, element in m.elements.items():
            for (a, b, _op), seq in zip(element.log, self.directive_seq[kind], strict=False):
                row = self.seq_rows.setdefault(seq, self._row(" "))
                cols = self.span(a, b)
                if cols:
                    for c in range(cols[0], cols[1] + 1):
                        row[c] = self.letter[kind]

        for seq, row in self.seq_rows.items():
            end_t, end_ch = self.seq_end.get(seq, (self.stop, ""))
            cols = self.span(self.seq_first[seq], end_t + 1)
            if cols is None:
                continue
            for c in range(cols[0], cols[1] + 1):
                if row[c] == " ":
                    t = self.start + c * self.scale
                    on_chain = any(
                        a <= t < (b if b is not None else self.stop)
                        for a, b in self.chain_wait.get(seq, [])
                    )
                    row[c] = "." if on_chain else "~"
            if end_ch:
                self._put(row, end_t, end_ch)

    # -- views --------------------------------------------------------------------------------

    def _bar(self, row: list[str], a: int, b: int, name: str) -> None:
        """``[NAME===]``; no bracket on a side cut by the window; ``=`` only when too short."""
        cols = self.span(a, b)
        if cols is None:
            return
        c0, c1 = cols
        w = c1 - c0 + 1
        if w < 3:  # too short to show its limits (coarse scale): just "busy"
            row[c0 : c1 + 1] = ["="] * w
            return
        left = "=" if a < self.start else "["
        right = "=" if b - 1 > self.stop else "]"
        inner = w - 2
        body = (name if inner >= len(name) else "") + "=" * inner
        row[c0 : c1 + 1] = list(left + body[:inner] + right)

    def _mnemonic(self, kind: str, op: str) -> str:
        """Code B mnemonic of a directive in the language of the names (K / L for TSK / TSL)."""
        if op in ("transfer_shift_to_K", "transfer_shift_to_L"):
            return SHORT[op]
        by_op = {v: k for k, v in data.element_index(kind, self.names.language).items()}
        return by_op.get(op) or SHORT.get(op, op[:3].upper())

    def by_element(self) -> list[str]:
        m = self.machine
        lines = [self.title(), *self.axis("us")]
        lines.append(self.names.say("pd").ljust(LABEL) + "".join(self.pd))
        for kind, element in m.elements.items():
            if not element.log:
                continue
            row = self._row()
            for a, b in self.waits[kind]:
                cols = self.span(a, b)
                if cols:
                    for c in range(cols[0], cols[1] + 1):
                        row[c] = "~"
            for a, b, op in element.log:
                self._bar(row, a, b, self._mnemonic(element.kind, op))
            lines.append(unit_name(element, self.names)[: LABEL - 1].ljust(LABEL) + "".join(row))
        lines.append(
            "mem".ljust(LABEL) + "".join("." if n == 0 else str(min(n, 9)) for n in self.mem)
        )
        shown = [(t, s) for t, s in self.events if self.col(t) is not None]
        if shown:
            marks = [" "] * self.columns
            for t, _ in shown:
                marks[self.col(t)] = "^"
            lines.append(" " * LABEL + "".join(marks).rstrip())
            lines.append(" " * LABEL + "^ " + " ; ".join(f"{t} us {s}" for t, s in shown))
        keys = ["bar", "pd", "mem"]
        if self.start or self.stop < self.machine.engine.now:
            keys.insert(1, "cut")
        return [*lines, "", *self._legend(keys)]

    def _letters(self) -> str:
        """``A=ARIT L=LOGI D=DRUM1,DRUM2`` for the elements that worked."""
        groups: dict[str, list[str]] = {}
        for element in self.machine.elements.values():
            if element.log:
                letter = self.names.element(element.kind)[0]
                groups.setdefault(letter, []).append(unit_name(element, self.names))
        return " ".join(f"{k}={','.join(v)}" for k, v in groups.items())

    def _legend(self, keys: list[str]) -> list[str]:
        text = LEGEND[self.names.language]
        values = {"pd": self.names.say("pd"), "letters": self._letters()}
        lines = [f"{text['title']}:"]
        lines += ["  " + text[k].format(**values) for k in keys]
        return lines

    def by_sequence(self) -> list[str]:
        lines = [self.title(), *self.axis("seq.")]
        for seq, row in sorted(self.seq_rows.items(), key=lambda kv: self.seq_first[kv[0]]):
            if row.count(" ") == len(row):
                continue
            lines.append(seq[: LABEL - 1].ljust(LABEL) + "".join(row).rstrip())
        return [*lines, "", *self._legend(["seq", "wait", "end"])]
