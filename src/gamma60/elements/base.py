"""State machine of an element [COURS p.13-14 ; B61 p.22-23].

An element is **idle** (no sequence) or **active**; an active element is either **waiting**
(its instruction request line, DI, is raised) or **operating** on its own. It takes the
initiative of the exchanges: instruction requests to the Program Distributor, data transfer
requests to the Data Distributor. It never reads the program itself.

The work of a directive is written as a generator (:meth:`Element.operate`) that yields
commands, so that the element waits for the DD without threads:

- ``("read", car[, step])`` → the catena read at the address of the CAR (which moves by
  ``step``, +1 by default, −1 for a tape read backwards);
- ``("write", car, value[, step])`` → writes ``value`` at the address of the CAR;
- ``("wait", µs)`` → internal work;
- ``("until", date)`` → wait until a date (no-op if it is already past).
"""

from __future__ import annotations

import ast
import math
import operator
from collections.abc import Generator
from fractions import Fraction
from typing import Any

from gamma60.core.arit import Incident
from gamma60.data_distributor import READ, WRITE, Request

IDLE, WAITING, OPERATING = "idle", "waiting", "operating"

Command = tuple[Any, ...]


class Element:
    def __init__(self, machine, kind: str, name: str, number: int) -> None:
        self.machine, self.kind, self.name, self.number = machine, kind, name, number
        self.port = machine.dd.attach(self, kind, name)
        self.state = IDLE
        self.qualitative = 0
        self.log: list[tuple[int, int, str]] = []  # (start, end, directive) of each operation
        self._gen: Generator[Command, Any, None] | None = None
        self._started = 0
        self._directive = ""
        self.directive_address = 0  # address of the directive being executed (for messages)

    # -- directive from the Program Distributor ----------------------------------------------

    def receive(self, characteristic: int) -> None:
        self.state = OPERATING
        self._started = self.machine.engine.now
        self._gen = self.operate(characteristic)
        self._advance(None)

    def operate(self, characteristic: int) -> Generator[Command, Any, None]:  # pragma: no cover
        raise NotImplementedError

    def _advance(self, value: Any) -> None:
        assert self._gen is not None
        try:
            cmd = self._gen.send(value)
        except StopIteration:
            self._finish()
            return
        except Incident as exc:
            self.machine.element_incident(self, str(exc))
            return
        dd, engine = self.machine.dd, self.machine.engine
        if cmd[0] == "read":  # ("read", car[, step])
            dd.request(self.port, cmd[1], READ, step=cmd[2] if len(cmd) > 2 else 1)
        elif cmd[0] == "write":  # ("write", car, value[, step])
            dd.request(self.port, cmd[1], WRITE, value=cmd[2], step=cmd[3] if len(cmd) > 3 else 1)
        elif cmd[0] == "wait":
            engine.after(max(0, cmd[1]), lambda: self._advance(None), f"{self.name} work")
        elif cmd[0] == "until":
            engine.at(max(engine.now, cmd[1]), lambda: self._advance(None), f"{self.name} work")
        else:  # pragma: no cover - programming error
            raise ValueError(f"unknown command {cmd!r}")

    def _finish(self) -> None:
        now = self.machine.engine.now
        self.log.append((self._started, now, self._directive))
        self.machine.engine.record(
            self.name, "done", directive=self._directive, took=now - self._started
        )
        self.state = WAITING
        self.machine.dp.request_instruction(self)

    # -- DD client -----------------------------------------------------------------------------

    def transfer_done(self, request: Request, value: int) -> None:
        self._advance(value)

    def transfer_incident(self, request: Request, reason: str) -> None:
        self.machine.element_incident(self, f"{reason} error at CAR {request.rac}")


# --- durations in cycles (timings.yaml: "6 + l/2", "24 + 12*(24 - l)") -------------------------

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def cycles(expression: str, **names: int) -> Fraction:
    """Evaluate a duration formula of timings.yaml (numbers, l, n, + - * / and brackets)."""

    def ev(node: ast.AST) -> Fraction:
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            return Fraction(node.value)
        if isinstance(node, ast.Name) and node.id in names:
            return Fraction(names[node.id])
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.left), ev(node.right))
        raise ValueError(f"invalid duration formula {expression!r}")

    return ev(ast.parse(str(expression), mode="eval"))


def microseconds(n_cycles: Fraction, cycle_us: int) -> int:
    return math.ceil(n_cycles * cycle_us)
