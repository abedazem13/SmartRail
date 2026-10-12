"""Thread-safe nine-seat demo, reusing the existing firmware serial parser.

No sensor decisions are made here. Physical seats are read-only in hybrid
mode; simulated state and confirmed hardware state never replace each other.
"""

import random
import threading
import time
from collections.abc import Callable

from seat_live import Board, EMPTY, OCCUPIED, UNKNOWN, STALE_S

# ---- train size (the only place these numbers are defined) ----
NUM_CARS = 12
SEATS_PER_CAR = 108
REAL_SENSORS = 2
TOTAL_SEATS = NUM_CARS * SEATS_PER_CAR  # 1296

CARS = tuple(chr(ord("A") + index) for index in range(NUM_CARS))  # A..L
SEAT_IDS = tuple(f"{car}{number}" for car in CARS
                 for number in range(1, SEATS_PER_CAR + 1))
# Physical sensors: firmware seat 0 -> GPIO34 -> A1, seat 1 -> GPIO35 -> B1.
SENSOR_MAP = {"A1": 0, "B1": 1}
assert len(SENSOR_MAP) == REAL_SENSORS

# A car is "available" (green) with this many confirmed free seats,
# "filling" (orange, about to be full) with 1..N-1, and "full" (red) with 0.
# Unknown seats are never counted as free, so a car with any unknown seat is
# reported as "unknown" (grey) rather than being called full.
AVAILABLE_FREE_MIN = 10

# How many cars the platform display suggests at once.
RECOMMEND_CARS = 3

# A stop is not applied in one jump: passengers leave during the first half of
# this window and others board during the second, so the display shows seats
# emptying and filling. The seats really do change over time; nothing here is
# a visual-only effect.
STOP_ANIMATION_S = 2.4

# Automatic stops: 0 is off, otherwise seconds between stops. Driven by the
# browser's polling, so stops only happen while a display is open.
AUTO_INTERVAL_MIN = 3
AUTO_INTERVAL_MAX = 300

# Each stop: this fraction of occupied seats leaves, then the same fraction of
# free seats fills. Never more than exists, so a car cannot overfill.
STOP_MIN_FRACTION = 0.05
STOP_MAX_FRACTION = 0.20

# Demo starting scenario: free seats per car, scattered inside each car so the
# seat map does not look sorted. Deterministic, so demos and tests repeat.
EXAMPLE_FREE_PER_CAR = (12, 3, 0, 25, 48, 7, 36, 18, 1, 60, 29, 72)
_SCATTER = 37  # coprime with 108, so exactly `free` seats come out free


def example_states() -> dict:
    """The demo scenario as {seat_id: EMPTY/OCCUPIED}."""
    states = {}
    for index, car in enumerate(CARS):
        free = EXAMPLE_FREE_PER_CAR[index]
        for number in range(1, SEATS_PER_CAR + 1):
            scattered = (number * _SCATTER) % SEATS_PER_CAR
            states[f"{car}{number}"] = EMPTY if scattered < free else OCCUPIED
    return states


EXAMPLE = example_states()
SIMULATION_DETAIL = f"All {TOTAL_SEATS} seats are controlled in software."


class DemoError(ValueError):
    """An operator request that cannot safely be applied."""


class DemoModel:
    def __init__(self, clock: Callable[[], float] = time.monotonic,
                 rng: random.Random | None = None):
        self._lock = threading.RLock()
        self._clock = clock
        self._rng = rng or random.Random()
        self.mode = "simulation"
        self.port = ""
        self.generation = 0
        self.station = 1
        self.auto_interval = 0.0
        self._next_auto = None
        self._pending = []  # [(apply_at, seat_id, state)] - a stop in progress
        self.simulated = EXAMPLE.copy()
        self.board = Board({1: [0], 2: [1]})
        self.connection = "simulation"
        self.detail = SIMULATION_DETAIL
        self.last_message = ""
        self.warnings: list[str] = []
        self._recommended = []

    def configure(self, mode: str, port: str = "") -> None:
        if mode not in ("simulation", "hybrid"):
            raise DemoError("Mode must be simulation or hybrid.")
        if not isinstance(port, str) or len(port) > 200 or any(ord(c) < 32 for c in port):
            raise DemoError("Invalid serial port.")
        port = port.strip()
        if mode == "hybrid" and not port:
            raise DemoError("Select or enter the ESP32 serial port first.")
        with self._lock:
            self.mode, self.port = mode, port if mode == "hybrid" else ""
            self._pending.clear()
            self.generation += 1  # Ignore late data from an old port/mode.
            self.board = Board({1: [0], 2: [1]})
            self.connection = "connecting" if mode == "hybrid" else "simulation"
            self.detail = ("Opening port. Keep both physical seats empty during calibration."
                           if mode == "hybrid" else SIMULATION_DETAIL)
            self.last_message = ""
            self.warnings.clear()
            self._recommended = []

    def serial_config(self) -> tuple[int, str, str]:
        with self._lock:
            return self.generation, self.mode, self.port

    def transport(self, generation: int, connected: bool, detail: str = "") -> bool:
        with self._lock:
            if generation != self.generation or self.mode != "hybrid":
                return False
            self.board = Board({1: [0], 2: [1]})
            self.connection = "connected" if connected else "disconnected"
            self.detail = detail or "USB open; waiting for firmware seat data."
            self.last_message = ""
            return True

    def feed(self, generation: int, line: str) -> None:
        with self._lock:
            if generation != self.generation or self.mode != "hybrid" or self.connection != "connected":
                return
            text = line.strip()
            if not text:
                return
            if text.startswith(("SmartRail seat occupancy", "--- CALIBRATION")):
                self.board = Board({1: [0], 2: [1]})
                self.board.calibrating = True
                self.warnings.clear()
            elif text.startswith("CAL seat="):
                # Also handle connecting partway through calibration.
                self.board.calibrating = True
            if text.startswith("WARN") and text not in self.warnings:
                self.warnings = (self.warnings + [text[:500]])[-10:]
            try:
                self.board.feed(self._clock(), text)
            except (ValueError, OverflowError):
                self.last_message = "Ignored malformed firmware measurement."
                return
            if text.startswith("--- calibration done"):
                # A CAL line is not a fresh occupancy observation. Wait for status.
                for seat in self.board.seats.values():
                    seat.state, seat.last_seen = UNKNOWN, None
                    seat.reason = "waiting for status after calibration"
            self.last_message = text[:500]

    def set_seat(self, seat_id: str, state: str) -> None:
        with self._lock:
            if seat_id not in SEAT_IDS:
                raise DemoError("Unknown seat.")
            if state not in (EMPTY, OCCUPIED):
                raise DemoError("State must be EMPTY or OCCUPIED.")
            if self.mode == "hybrid" and seat_id in SENSOR_MAP:
                raise DemoError("Real sensor seats are read-only in hybrid mode.")
            # An operator click wins over a stop still in progress.
            self._pending = [p for p in self._pending if p[1] != seat_id]
            self.simulated[seat_id] = state

    def preset(self, name: str) -> None:
        if name not in ("example", "empty", "occupied"):
            raise DemoError("Unknown scenario.")
        with self._lock:
            for seat_id in SEAT_IDS:
                if self.mode == "hybrid" and seat_id in SENSOR_MAP:
                    continue
                self.simulated[seat_id] = (EXAMPLE[seat_id] if name == "example"
                                           else EMPTY if name == "empty" else OCCUPIED)
            self._pending.clear()
            self.station = 1

    def _simulated_ids(self) -> list:
        """Seat ids the simulation may change: never a live sensor seat."""
        return [seat_id for seat_id in SEAT_IDS
                if not (self.mode == "hybrid" and seat_id in SENSOR_MAP)]

    def _stop_count(self, available: int) -> int:
        """How many passengers move, as a fraction of what is actually there."""
        if available <= 0:
            return 0
        low = max(1, round(available * STOP_MIN_FRACTION))
        high = max(low, round(available * STOP_MAX_FRACTION))
        return min(available, self._rng.randint(low, high))

    def _apply_due(self, now: float) -> None:
        """Apply the part of a stop whose moment has arrived."""
        if not self._pending:
            return
        waiting = []
        for apply_at, seat_id, state in self._pending:
            if apply_at <= now:
                self.simulated[seat_id] = state
            else:
                waiting.append((apply_at, seat_id, state))
        self._pending = waiting

    def _auto_tick(self, now: float) -> None:
        """Run an automatic stop when one is due."""
        if self.auto_interval and self._next_auto is not None and now >= self._next_auto:
            self._run_stop(now)
            self._next_auto = now + self.auto_interval

    def _schedule(self, now: float, seat_ids: list, state: str,
                  start: float, end: float) -> None:
        """Spread these seat changes evenly across a slice of the window."""
        for index, seat_id in enumerate(seat_ids, start=1):
            share = index / len(seat_ids)
            self._pending.append((now + start + (end - start) * share, seat_id, state))

    def _run_stop(self, now: float) -> dict:
        editable = self._simulated_ids()
        occupied = [s for s in editable if self.simulated[s] == OCCUPIED]
        free = [s for s in editable if self.simulated[s] == EMPTY]

        alighting = self._rng.sample(occupied, self._stop_count(len(occupied)))
        boarding = self._rng.sample(free + alighting,
                                    self._stop_count(len(free) + len(alighting)))

        # Passengers leave first, then others take the seats.
        half = STOP_ANIMATION_S / 2
        self._schedule(now, alighting, EMPTY, 0.0, half)
        self._schedule(now, boarding, OCCUPIED, half, STOP_ANIMATION_S)

        self.station += 1
        return {"station": self.station, "alighted": len(alighting),
                "boarded": len(boarding), "simulated_seats": len(editable),
                "animation_s": STOP_ANIMATION_S}

    def next_stop(self) -> dict:
        """Simulate a station stop: some passengers get off, then some board.

        Random but bounded: never frees more seats than are occupied and never
        fills more than are free. Physical sensor seats are never touched. The
        changes are applied over STOP_ANIMATION_S instead of in one jump.
        """
        with self._lock:
            now = self._clock()
            self._apply_due(now)
            return self._run_stop(now)

    def configure_auto(self, interval_s: float) -> dict:
        """Run a stop every interval_s seconds; 0 turns it off."""
        try:
            interval = float(interval_s)
        except (TypeError, ValueError):
            raise DemoError("Interval must be a number of seconds.")
        if interval and not AUTO_INTERVAL_MIN <= interval <= AUTO_INTERVAL_MAX:
            raise DemoError(f"Interval must be 0 (off) or {AUTO_INTERVAL_MIN}"
                            f"-{AUTO_INTERVAL_MAX} seconds.")
        with self._lock:
            self.auto_interval = interval
            self._next_auto = self._clock() + interval if interval else None
            return {"auto_interval": self.auto_interval}

    def seat_view(self, seat_id: str) -> dict:
        """One seat as the UI sees it. Sensor seats carry their diagnostics."""
        with self._lock:
            if seat_id not in self.simulated:
                raise DemoError("Unknown seat.")
            now = self._clock()
            self.board.check_stale(now)
            return self._seat_view(seat_id, now)

    def _seat_view(self, seat_id: str, now: float) -> dict:
        sensor = SENSOR_MAP.get(seat_id)
        real = self.mode == "hybrid" and sensor is not None
        item = {"id": seat_id, "car": seat_id[0],
                "source": "sensor" if real else "simulated",
                "sensor_id": sensor, "state": self.simulated[seat_id],
                "editable": not real, "reason": "operator-controlled",
                "distance_cm": None, "noise_mv": None, "pending": False, "age_s": None}
        if real:
            seat = self.board.seats[sensor]
            state, reason = seat.state, seat.reason
            if self.board.calibrating:
                state, reason = UNKNOWN, "calibrating; keep both seats empty"
            elif self.connection != "connected":
                state, reason = UNKNOWN, "board disconnected"
            item.update(state=state, reason=reason, distance_cm=seat.dist,
                        noise_mv=seat.noise,
                        pending=seat.pending and state != UNKNOWN,
                        age_s=None if seat.last_seen is None else round(now - seat.last_seen, 2))
        return item

    def snapshot(self) -> dict:
        """Current state for the UI.

        With 1296 seats the per-seat detail would be too large to send twice a
        second, so each car carries a compact `states` string (one character
        per seat: E/O/U) and detailed entries only for the sensor seats.
        """
        with self._lock:
            now = self._clock()
            self._apply_due(now)
            self._auto_tick(now)
            self._apply_due(now)
            self.board.check_stale(now)
            letter = {EMPTY: "E", OCCUPIED: "O", UNKNOWN: "U"}

            cars = []
            for car in CARS:
                states = []
                sensor_seats = []
                for number in range(1, SEATS_PER_CAR + 1):
                    seat_id = f"{car}{number}"
                    if self.mode == "hybrid" and seat_id in SENSOR_MAP:
                        view = self._seat_view(seat_id, now)
                        sensor_seats.append(view)
                        states.append(letter[view["state"]])
                    else:
                        if seat_id in SENSOR_MAP:
                            sensor_seats.append(self._seat_view(seat_id, now))
                        states.append(letter[self.simulated[seat_id]])
                joined = "".join(states)
                free = joined.count("E")
                unknown = joined.count("U")
                occupied = joined.count("O")
                status = ("unknown" if unknown else "full" if free == 0
                          else "available" if free >= AVAILABLE_FREE_MIN else "filling")
                cars.append({"id": car, "zone": car, "free": free,
                             "occupied": occupied, "unknown": unknown,
                             "total": SEATS_PER_CAR,
                             "occupancy_pct": round(occupied * 100 / SEATS_PER_CAR, 1),
                             "status": status, "states": joined,
                             "seats": sensor_seats})

            # The emptiest cars first, ties alphabetically. A suggestion only:
            # nothing is reserved or decremented, and a car is never suggested
            # on the strength of unknown seats.
            ranked = sorted((car for car in cars if car["free"] > 0),
                            key=lambda car: (-car["free"], car["id"]))
            self._recommended = [car["id"] for car in ranked[:RECOMMEND_CARS]]
            unknown_total = sum(car["unknown"] for car in cars)
            free_total = sum(car["free"] for car in cars)
            occupied_total = sum(car["occupied"] for car in cars)
            if self._recommended:
                named = ", ".join(f"Car {car['id']} ({car['free']} free)"
                                  for car in ranked[:RECOMMEND_CARS])
                message = f"Most confirmed free seats: {named}"
            elif unknown_total:
                message = "Availability incomplete — waiting for sensor data"
            else:
                message = "No free seats currently reported"

            link = self.connection
            if self.mode == "hybrid" and link == "connected":
                if self.board.calibrating:
                    link = "calibrating"
                elif any(s["state"] == UNKNOWN for car in cars for s in car["seats"]):
                    link = "waiting"
                else:
                    link = "live"
            return {"mode": self.mode, "generation": self.generation, "cars": cars,
                    "free": free_total, "occupied": occupied_total,
                    "unknown": unknown_total, "total": TOTAL_SEATS,
                    "occupancy_pct": round(occupied_total * 100 / TOTAL_SEATS, 1),
                    "station": self.station, "num_cars": NUM_CARS,
                    "auto_interval": self.auto_interval,
                    "boarding": bool(self._pending),
                    "seats_per_car": SEATS_PER_CAR, "real_seats": sorted(SENSOR_MAP),
                    "recommended": self._recommended, "message": message,
                    "connection": {"status": link, "port": self.port, "detail": self.detail,
                                   "last_message": self.last_message},
                    "warnings": self.warnings.copy(), "stale_s": STALE_S}
