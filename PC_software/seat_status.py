"""
seat_status.py - prints only whether each seat is occupied or empty.

Short version of seat_live.py (which it reuses): one line each time a seat
changes, nothing else.

    [   9.4s] seat 0 (car 1): OCCUPIED
    [  23.1s] seat 0 (car 1): EMPTY

Usage:
  python seat_status.py --port COM5
  python seat_status.py --replay seat_log.txt
Live runs are still recorded to seat_log.txt (change with --log).
"""

import argparse

from seat_live import run, live_source, replay_source, EMPTY, OCCUPIED


def print_status(change):
    t, s, _old, new = change
    if new in (EMPTY, OCCUPIED):
        label = new
    elif s.reason == "calibrating":
        label = "CALIBRATING - keep the seat empty"
    else:
        label = "NO DATA - check the USB cable / board"
    print(f"[{t:7.1f}s] seat {s.id} (car {s.car}): {label}", flush=True)


def main():
    ap = argparse.ArgumentParser(description="Print only seat occupied / empty changes.")
    ap.add_argument("--port", help="serial port of the ESP32, e.g. COM5")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--replay", help="log file recorded by seat_live.py or this program")
    ap.add_argument("--log", default="seat_log.txt")
    ap.add_argument("--recalibrate", action="store_true",
                    help="send 'c' to the board after connecting (seats must be empty)")
    args = ap.parse_args()

    if args.replay:
        source = replay_source(args.replay)
    elif args.port:
        source = live_source(args.port, args.baud, args.log, args.recalibrate)
    else:
        ap.error("give --port (live) or --replay (recorded file)")

    print("Watching seats. Keep them empty for ~5 s in case the board recalibrates. "
          "Ctrl+C to stop.\n")
    try:
        run(source, on_change=print_status)
    except KeyboardInterrupt:
        print("\nstopped" + ("" if args.replay else f" - session saved to {args.log}"))


if __name__ == "__main__":
    main()
