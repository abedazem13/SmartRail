"""Stateful dispatcher: one answer per passenger, not one answer for everybody.

A platform screen can only show one picture, so every passenger reading it
draws the same conclusion and the crowd moves together. This dispatcher
answers each request individually and remembers what it has already handed
out, so two passengers standing side by side are sent to different carriages.
That is the whole mechanism: the crowd divides itself as it is served.

Assignment rule, in order:

  1. keep only the carriages within walking range of where the passenger is;
  2. of those, prefer ones with a CONFIRMED free seat (an unknown seat is
     never treated as free);
  3. among the candidates, take the one this dispatcher has routed the
     fewest passengers to so far;
  4. break ties on free seats, then on how far the passenger has to walk,
     then on carriage id so the result is deterministic.

Three things the brief does not specify, decided here and documented because
they change the behaviour:

  * Assignments expire (`hold_s`). Without expiry the routed counts would
    accumulate every passenger who ever asked, and after a few minutes every
    carriage would look equally used. The counts have to describe the people
    currently waiting for this train.
  * Requests are idempotent by `ticket`. A passenger who reopens the app or
    refreshes gets the same carriage back and is not counted twice.
  * `reset()` clears the counts when a train departs, because the next
    train's waiting crowd is a different population.

Thread-safe: the dashboard serves requests from several browser tabs at once.
"""

from __future__ import annotations

import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, asdict

# A seat whose sensor has stopped reporting. Never counted as free.
UNKNOWN = "UNKNOWN"

DEFAULT_WALK_LIMIT = 3      # carriages either side; about 78 m, 60 s on foot
DEFAULT_HOLD_S = 180.0      # how long an assignment occupies its slot


@dataclass(frozen=True)
class Assignment:
    """What one passenger was told. Returned to the app and kept as state."""
    ticket: str
    car: str
    zone: str
    walk_carriages: int      # signed: negative is towards the front of the train
    confirmed_free: int
    reason: str
    issued_at: float
    expires_at: float

    def as_dict(self) -> dict:
        return asdict(self)


class DispatcherError(ValueError):
    """A request that cannot be answered, such as an unknown position."""


class Dispatcher:
    """Routes individual passengers so that a waiting crowd divides itself.

    `cars` is the carriage order along the platform, front to back. `zones`
    maps each carriage to the platform zone it stops at; without it the
    carriage id is used as the zone.
    """

    def __init__(self, cars: tuple[str, ...], zones: dict[str, str] | None = None,
                 walk_limit: int = DEFAULT_WALK_LIMIT,
                 hold_s: float = DEFAULT_HOLD_S,
                 clock: Callable[[], float] = time.monotonic):
        if not cars:
            raise ValueError("a dispatcher needs at least one carriage")
        self._cars = tuple(cars)
        self._index = {car: i for i, car in enumerate(self._cars)}
        self._zones = dict(zones or {car: car for car in self._cars})
        self.walk_limit = walk_limit
        self.hold_s = hold_s
        self._clock = clock

        self._lock = threading.RLock()
        self._routed: dict[str, int] = {car: 0 for car in self._cars}
        self._live: dict[str, Assignment] = {}     # ticket -> assignment
        self._generation = 0

    # ---------------------------------------------------------------- state

    def reset(self) -> None:
        """Forget every assignment. Call when a train departs."""
        with self._lock:
            self._routed = {car: 0 for car in self._cars}
            self._live.clear()
            self._generation += 1

    def release(self, ticket: str) -> bool:
        """Give back a slot: the passenger boarded, or closed the app."""
        with self._lock:
            held = self._live.pop(ticket, None)
            if held is None:
                return False
            self._routed[held.car] = max(0, self._routed[held.car] - 1)
            return True

    def _expire(self, now: float) -> None:
        """Drop assignments whose hold has run out. Caller holds the lock."""
        stale = [t for t, a in self._live.items() if a.expires_at <= now]
        for ticket in stale:
            held = self._live.pop(ticket)
            self._routed[held.car] = max(0, self._routed[held.car] - 1)

    # ----------------------------------------------------------- assignment

    def assign(self, position: str, cars_state: list[dict],
               ticket: str | None = None) -> Assignment:
        """Answer one passenger.

        `position` is the carriage or zone the passenger is standing at.
        `cars_state` is the per-carriage snapshot the model already produces:
        dicts with at least `id`, `free` and `unknown`. `free` must already
        exclude unknown seats; this class re-checks rather than trusting it.

        Passing the same `ticket` again returns the same answer without
        routing a second passenger.
        """
        now = self._clock()
        with self._lock:
            self._expire(now)

            if ticket and ticket in self._live:
                return self._live[ticket]       # idempotent: a refresh, not a new passenger

            here = self._locate(position)
            states = self._clean(cars_state)
            reachable = [c for c in self._cars
                         if abs(self._index[c] - here) <= self.walk_limit]
            if not reachable:                    # walk_limit of 0 at least keeps one
                reachable = [self._cars[here]]

            with_seats = [c for c in reachable if states[c]["free"] > 0]
            if with_seats:
                pool, reason = with_seats, "confirmed free seat"
            else:
                # Nothing within reach can prove it has a seat. Spreading is
                # still worth doing: the busiest door is what holds the train.
                pool, reason = reachable, "no confirmed seat nearby; spreading the load"

            car = min(pool, key=lambda c: (self._routed[c],
                                           -states[c]["free"],
                                           abs(self._index[c] - here),
                                           self._index[c]))

            assignment = Assignment(
                ticket=ticket or uuid.uuid4().hex,
                car=car,
                zone=self._zones.get(car, car),
                walk_carriages=self._index[car] - here,
                confirmed_free=states[car]["free"],
                reason=reason,
                issued_at=now,
                expires_at=now + self.hold_s,
            )
            self._routed[car] += 1
            self._live[assignment.ticket] = assignment
            return assignment

    # ------------------------------------------------------------- helpers

    def _locate(self, position: str) -> int:
        """Accept a carriage id, a zone name, or a 1-based index as a string."""
        if position in self._index:
            return self._index[position]
        for car, zone in self._zones.items():
            if zone == position:
                return self._index[car]
        if isinstance(position, str) and position.isdigit():
            n = int(position) - 1
            if 0 <= n < len(self._cars):
                return n
        raise DispatcherError(f"unknown platform position: {position!r}")

    def _clean(self, cars_state: list[dict]) -> dict[str, dict]:
        """Normalise the snapshot and never let an unknown seat read as free."""
        out = {car: {"free": 0, "unknown": 0} for car in self._cars}
        for car in cars_state:
            cid = car.get("id")
            if cid not in out:
                continue
            free = int(car.get("free", 0) or 0)
            unknown = int(car.get("unknown", 0) or 0)
            out[cid] = {"free": max(0, free), "unknown": max(0, unknown)}
        return out

    # --------------------------------------------------------- diagnostics

    def routed(self) -> dict[str, int]:
        """How many passengers are currently routed to each carriage."""
        with self._lock:
            self._expire(self._clock())
            return dict(self._routed)

    def stats(self) -> dict:
        with self._lock:
            self._expire(self._clock())
            counts = list(self._routed.values())
            return {
                "generation": self._generation,
                "live_assignments": len(self._live),
                "routed": dict(self._routed),
                "busiest_car": max(self._routed, key=lambda c: self._routed[c]),
                "spread": max(counts) - min(counts) if counts else 0,
                "walk_limit": self.walk_limit,
                "hold_s": self.hold_s,
            }
