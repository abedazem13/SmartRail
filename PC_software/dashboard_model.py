"""Thread-safe nine-seat demo, reusing the existing firmware serial parser.

No sensor decisions are made here. Physical seats are read-only in hybrid
mode; simulated state and confirmed hardware state never replace each other.
"""

import threading
import time
from collections.abc import Callable

from seat_live import Board, EMPTY, OCCUPIED, UNKNOWN, STALE_S

CARS = ("A", "B", "C")
SEAT_IDS = tuple(f"{car}{number}" for car in CARS for number in range(1, 4))
SENSOR_MAP = {"A1": 0, "B1": 1}
EXAMPLE = dict(zip(SEAT_IDS, (
    EMPTY, OCCUPIED, OCCUPIED,
    EMPTY, EMPTY, EMPTY,
    OCCUPIED, OCCUPIED, OCCUPIED,
)))


class DemoError(ValueError):
    """An operator request that cannot safely be applied."""


class DemoModel:
    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._lock = threading.RLock()
        self._clock = clock
        self.mode = "simulation"
        self.port = ""
        self.generation = 0
        self.simulated = EXAMPLE.copy()
        self.board = Board({1: [0], 2: [1]})
        self.connection = "simulation"
        self.detail = "All nine seats are controlled in software."
        self.last_message = ""
        self.warnings: list[str] = []
        self._recommended = None

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
            self.generation += 1  # Ignore late data from an old port/mode.
            self.board = Board({1: [0], 2: [1]})
            self.connection = "connecting" if mode == "hybrid" else "simulation"
            self.detail = ("Opening port. Keep both physical seats empty during calibration."
                           if mode == "hybrid" else "All nine seats are controlled in software.")
            self.last_message = ""
            self.warnings.clear()
            self._recommended = None

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

    def snapshot(self) -> dict:
        with self._lock:
            now = self._clock()
            self.board.check_stale(now)
            seats = []
            for seat_id in SEAT_IDS:
                sensor = SENSOR_MAP.get(seat_id)
                real = self.mode == "hybrid" and sensor is not None
                item = {"id": seat_id, "car": seat_id[0], "source": "sensor" if real else "simulated",
                        "sensor_id": sensor, "state": self.simulated[seat_id], "editable": not real,
                        "reason": "operator-controlled", "distance_cm": None,
                        "noise_mv": None, "pending": False, "age_s": None}
                if real:
                    seat = self.board.seats[sensor]
                    state, reason = seat.state, seat.reason
                    if self.board.calibrating:
                        state, reason = UNKNOWN, "calibrating; keep both seats empty"
                    elif self.connection != "connected":
                        state, reason = UNKNOWN, "board disconnected"
                    item.update(state=state, reason=reason, distance_cm=seat.dist,
                                noise_mv=seat.noise, pending=seat.pending and state != UNKNOWN,
                                age_s=None if seat.last_seen is None else round(now - seat.last_seen, 2))
                seats.append(item)

            cars = []
            for car in CARS:
                members = [s for s in seats if s["car"] == car]
                free = sum(s["state"] == EMPTY for s in members)
                unknown = sum(s["state"] == UNKNOWN for s in members)
                status = "unknown" if unknown else "none" if free == 0 else "limited" if free == 1 else "available"
                cars.append({"id": car, "zone": car, "free": free, "unknown": unknown,
                             "total": 3, "status": status, "seats": members})

            most_free = max(car["free"] for car in cars)
            choices = [car["id"] for car in cars if car["free"] == most_free] if most_free else []
            if self._recommended not in choices:
                self._recommended = choices[0] if choices else None
            unknown_total = sum(car["unknown"] for car in cars)
            if self._recommended:
                message = f"More confirmed free seats in Car {self._recommended} · Zone {self._recommended}"
            elif unknown_total:
                message = "Availability incomplete — waiting for sensor data"
            else:
                message = "No free seats currently reported"

            link = self.connection
            if self.mode == "hybrid" and link == "connected":
                if self.board.calibrating:
                    link = "calibrating"
                elif any(s["source"] == "sensor" and s["state"] == UNKNOWN for s in seats):
                    link = "waiting"
                else:
                    link = "live"
            return {"mode": self.mode, "generation": self.generation, "cars": cars,
                    "free": sum(car["free"] for car in cars), "unknown": unknown_total, "total": 9,
                    "recommended": self._recommended, "message": message,
                    "connection": {"status": link, "port": self.port, "detail": self.detail,
                                   "last_message": self.last_message}, "warnings": self.warnings.copy(),
                    "stale_s": STALE_S}