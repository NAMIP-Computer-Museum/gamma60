"""Discrete-event engine: simulated time in microseconds, deterministic order (rule 4).

Events are processed in the order (date, sequence number): two events at the same date run
in the order they were scheduled, so the same input always gives the same trace. There is no
thread, no asyncio and no real clock.
"""

from __future__ import annotations

import heapq
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(order=True)
class Event:
    time: int
    seq: int
    action: Callable[[], None] = field(compare=False)
    label: str = field(compare=False, default="")
    cancelled: bool = field(compare=False, default=False)


@dataclass(frozen=True)
class Record:
    """One line of the trace: date, unit, what happened, details (ordered key-value pairs)."""

    time: int
    unit: str
    what: str
    details: tuple[tuple[str, Any], ...] = ()

    def get(self, key: str, default: Any = None) -> Any:
        return dict(self.details).get(key, default)


class Engine:
    def __init__(self) -> None:
        self.now = 0
        self._queue: list[Event] = []
        self._seq = 0
        self.trace: list[Record] = []
        self.listeners: list[Callable[[Record], None]] = []

    # -- scheduling ---------------------------------------------------------------------------

    def at(self, time: int, action: Callable[[], None], label: str = "") -> Event:
        if time < self.now:
            raise ValueError(f"cannot schedule in the past ({time} < {self.now})")
        event = Event(int(time), self._seq, action, label)
        self._seq += 1
        heapq.heappush(self._queue, event)
        return event

    def after(self, delay: int, action: Callable[[], None], label: str = "") -> Event:
        return self.at(self.now + delay, action, label)

    @staticmethod
    def cancel(event: Event) -> None:
        event.cancelled = True

    def pending(self) -> int:
        return sum(1 for e in self._queue if not e.cancelled)

    # -- running ------------------------------------------------------------------------------

    def run(self, until: int | None = None, max_events: int = 10_000_000) -> int:
        """Process events up to date ``until`` (inclusive); return the number processed."""
        done = 0
        while self._queue and done < max_events:
            if until is not None and self._queue[0].time > until:
                break
            event = heapq.heappop(self._queue)
            if event.cancelled:
                continue
            self.now = event.time
            event.action()
            done += 1
        if until is not None and self.now < until:
            self.now = until
        return done

    # -- trace --------------------------------------------------------------------------------

    def record(self, unit: str, what: str, **details: Any) -> Record:
        rec = Record(self.now, unit, what, tuple(details.items()))
        self.trace.append(rec)
        for listener in self.listeners:
            listener(rec)
        return rec

    def stop(self) -> None:
        """Drop every pending event (end of the run after an incident)."""
        self._queue.clear()
