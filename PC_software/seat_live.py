"""
seat_live.py - PC side of SmartRail.

Reads the serial output of the ESP32 firmware (ESP32/ESP32.ino), keeps the
state of every seat, counts free seats per carriage and shows which carriage
the next passenger should board (guidance.py).

The EMPTY / OCCUPIED decision is made on the ESP32 (calibrated baseline,
hysteresis, 1 s confirmation - see Documentation/06_ESP32_FIRMWARE.md).
This program does not change those decisions; it only collects them.
It adds one state of its own: UNKNOWN, when the board is calibrating or has
stopped sending data (unplugged, reset, crashed).

Setup:   python -m pip install pyserial
Usage:
  python seat_live.py --port COM5                 # live, logs to seat_log.txt
  python seat_live.py --port COM5 --recalibrate   # also ask the board to recalibrate
  python seat_live.py --replay seat_log.txt       # re-run a recorded session
  python seat_live.py --port COM5 --verbose       # also print every status line

The board may restart when this program connects. It then recalibrates:
keep all seats EMPTY for the first ~5 seconds.

Serial line formats parsed here are defined in
Documentation/08_COMMUNICATION_AND_DATA.md. If the firmware's print format
changes, update the regular expressions below.
"""

import argparse
import re
import time

from guidance import display_line, assign_passengers

# carriage number -> firmware seat numbers (seat N = the Nth entry of SENSOR_PINS)
CARRIAGES = {1: [0], 2: [1]}

STALE_S = 2.0    # status lines arrive every 0.5 s; none for 2 s -> seat UNKNOWN
TICK_S = 0.1     # how often time-based checks run

EMPTY, OCCUPIED, UNKNOWN = "EMPTY", "OCCUPIED", "UNKNOWN"

RE_STATUS = re.compile(
    r"S(\d+) dist=\s*([\d.]+)cm base=\s*([\d.]+)cm noise=\s*(\d+)mV (OCCUPIED|EMPTY)\s*(\?)?")
RE_EVENT = re.compile(r"EVENT seat=(\d+) state=(OCCUPIED|EMPTY) dist=\s*([\d.]+)cm")
RE_CAL = re.compile(r"CAL seat=(\d+) baseline=\s*([\d.]+)cm mv=(\d+) noise=(\d+)mV")


# ---------------------------------------------------------------- model ----
class Seat:
    def __init__(self, seat_id, car):
        self.id = seat_id
        self.car = car
        self.state = UNKNOWN
        self.reason = "waiting for board"
        self.dist = None        # filtered distance from the firmware [cm]
        self.base = None        # calibrated empty-seat distance [cm]
        self.noise = None       # spread inside the firmware's median window [mV]
        self.pending = False    # firmware is confirming a change ('?')
        self.last_seen = None   # PC time of the last line about this seat [s]


class Board:
    """Tracks what the ESP32 reports. feed() and check_stale() return a list
    of changes: (t, seat, old_state, new_state)."""

    def __init__(self, carriages=CARRIAGES):
        self.carriages = carriages
        self.seats = {sid: Seat(sid, car)
                      for car, ids in carriages.items() for sid in ids}
        self.calibrating = False

    def _set(self, t, seat, new, reason):
        if seat.state == new:
            return []
        old = seat.state
        seat.state, seat.reason = new, reason
        return [(t, seat, old, new)]

    def feed(self, t, line):
        """Process one serial line. Returns (changes, info) where info is a
        board message worth showing (calibration, warnings, banner) or None."""
        changes, info = [], None
        text = line.strip()

        if text.startswith("--- CALIBRATION"):
            self.calibrating = True
            for s in self.seats.values():
                changes += self._set(t, s, UNKNOWN, "calibrating")
            info = text
        elif m := RE_CAL.search(text):
            s = self.seats.get(int(m.group(1)))
            if s:
                s.base, s.dist, s.noise = float(m.group(2)), float(m.group(2)), int(m.group(4))
                s.last_seen = t
                changes += self._set(t, s, EMPTY, "calibrated")   # firmware resets to EMPTY
            info = text
        elif text.startswith("--- calibration done"):
            self.calibrating = False
            info = text
        elif m := RE_EVENT.search(text):
            s = self.seats.get(int(m.group(1)))
            if s:
                s.dist, s.pending, s.last_seen = float(m.group(3)), False, t
                changes += self._set(t, s, m.group(2), "event")
        elif matches := RE_STATUS.findall(text):
            for sid, dist, base, noise, state, pend in matches:
                s = self.seats.get(int(sid))
                if not s:
                    continue
                s.dist, s.base, s.noise = float(dist), float(base), int(noise)
                s.pending, s.last_seen = bool(pend), t
                if not self.calibrating:
                    changes += self._set(t, s, state, "status")
        elif text:
            info = text                                   # banner, WARN, commands...
        return changes, info

    def check_stale(self, t):
        changes = []
        for s in self.seats.values():
            if s.state != UNKNOWN and s.last_seen is not None and t - s.last_seen > STALE_S:
                changes += self._set(t, s, UNKNOWN, "no data from board")
        return changes

    def messages(self):
        """Per-carriage summary in the format guidance.py expects."""
        msgs = []
        for car, ids in sorted(self.carriages.items()):
            states = [self.seats[i].state for i in ids]
            free = states.count(EMPTY)
            unknown = states.count(UNKNOWN)
            msgs.append({"car": car, "seats_total": len(ids),
                         "free_min": free, "free_max": free + unknown,
                         "sensors_reporting": len(ids) - unknown})
        return msgs


# ------------------------------------------------------------ sources ------
def open_serial(port, baud):
    import serial
    try:
        return serial.Serial(port, baud, timeout=0)
    except serial.SerialException as e:
        msg = str(e)
        if "Access is denied" in msg or "PermissionError" in msg or "Resource busy" in msg:
            raise SystemExit(
                f"\nCould not open {port}: another program is using it.\n"
                "Close the Arduino IDE Serial Monitor / Serial Plotter, and any other\n"
                "window running seat_live.py or seat_status.py, then try again.")
        raise SystemExit(
            f"\nCould not open {port}: port not found.\n"
            "Check the port name under Arduino IDE -> Tools -> Port, and that the\n"
            "USB cable is plugged in (some cables only charge).")


def live_source(port, baud, log_path, recalibrate=False):
    """Yields (t, line) for every serial line and (t, None) every TICK_S.
    Every line is logged as '<t>\\t<line>' so the run can be replayed.
    Reconnects automatically if the USB connection drops."""
    import serial
    ser = open_serial(port, baud)
    t0 = time.monotonic()
    next_tick = t0
    recal_at = t0 + 1.0 if recalibrate else None
    retry_at = 0.0
    buf = b""
    log = open(log_path, "w", encoding="utf-8", buffering=1)
    try:
        while True:
            now = time.monotonic()
            if ser is None:                                   # reconnecting
                if now >= retry_at:
                    try:
                        ser = serial.Serial(port, baud, timeout=0)
                        print(f"[{now - t0:7.1f}s] reconnected to {port}")
                    except serial.SerialException:
                        retry_at = now + 1.0
            else:
                try:
                    if recal_at is not None and now >= recal_at:
                        ser.write(b"c")
                        recal_at = None
                    waiting = ser.in_waiting
                    if waiting:
                        buf += ser.read(waiting)
                except (serial.SerialException, OSError):
                    print(f"[{now - t0:7.1f}s] connection to {port} lost - retrying every second")
                    ser.close()
                    ser, buf, retry_at = None, b"", now + 1.0

            *lines, buf = buf.split(b"\n")
            for raw in lines:
                text = raw.decode(errors="replace").rstrip("\r")
                t = time.monotonic() - t0
                log.write(f"{t:.2f}\t{text}\n")
                yield t, text

            now = time.monotonic()
            if now >= next_tick:
                next_tick += TICK_S
                yield now - t0, None
            else:
                time.sleep(0.005)
    finally:
        log.close()
        if ser is not None:
            ser.close()


def replay_source(path):
    """Yields (t, line) from a log written by live_source, with (t, None)
    ticks in between so timeouts behave as they did live."""
    tick = 0.0
    with open(path, encoding="utf-8") as f:
        for raw in f:
            if "\t" not in raw:
                continue
            ts, text = raw.rstrip("\n").split("\t", 1)
            t = float(ts)
            while tick < t:
                yield tick, None
                tick += TICK_S
            yield t, text


# --------------------------------------------------------------- output ----
def fmt_free(m):
    return f"{m['free_min']}" if m["free_min"] == m["free_max"] else f"{m['free_min']}-{m['free_max']}"


def print_change(change):
    t, s, old, new = change
    extra = ""
    if new in (EMPTY, OCCUPIED) and s.dist is not None:
        extra = f"  (dist {s.dist:.1f} cm)"
    elif new == UNKNOWN:
        extra = f"  ({s.reason})"
    print(f"[{t:7.1f}s] seat {s.id} (car {s.car}): {old} -> {new}{extra}")


def print_report(t, board):
    msgs = board.messages()
    cars = "  ".join(f"car {m['car']}: {fmt_free(m)}/{m['seats_total']} free" for m in msgs)
    best = assign_passengers(msgs, [1])[0][1]
    print(f"[{t:7.1f}s] {cars}")
    print(f"           DISPLAY: {display_line(msgs)}  ->  next passenger: C{best}")


def run(source, on_change=print_change, on_info=None, on_report=None,
        report_every=2.0, verbose=False):
    board = Board()
    next_report = 0.0
    for t, line in source:
        if line is None:
            changes = board.check_stale(t)
        else:
            if verbose:
                print(f"[{t:7.1f}s] > {line}")
            changes, info = board.feed(t, line)
            if info and on_info:
                on_info(t, info)
        for c in changes:
            on_change(c)
        if on_report and line is None and t >= next_report:
            on_report(t, board)
            while next_report <= t:
                next_report += report_every
    return board


def main():
    ap = argparse.ArgumentParser(description="SmartRail PC side: seat states, free seats, guidance.")
    ap.add_argument("--port", help="serial port of the ESP32, e.g. COM5")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--replay", help="log file recorded by a live run")
    ap.add_argument("--log", default="seat_log.txt", help="where live runs are recorded")
    ap.add_argument("--recalibrate", action="store_true",
                    help="send 'c' to the board after connecting (seats must be empty)")
    ap.add_argument("--report", type=float, default=2.0, help="summary interval [s]")
    ap.add_argument("--verbose", action="store_true", help="print every line from the board")
    args = ap.parse_args()

    if args.replay:
        source = replay_source(args.replay)
    elif args.port:
        source = live_source(args.port, args.baud, args.log, args.recalibrate)
        print("Connected. If the board restarts it recalibrates: keep all seats EMPTY "
              "for ~5 s. Ctrl+C to stop.")
    else:
        ap.error("give --port (live) or --replay (recorded file)")

    try:
        run(source, on_info=lambda t, s: print(f"[{t:7.1f}s] board: {s}"),
            on_report=print_report, report_every=args.report, verbose=args.verbose)
    except KeyboardInterrupt:
        print("\nstopped" + ("" if args.replay else f" - session saved to {args.log}"))


if __name__ == "__main__":
    main()
