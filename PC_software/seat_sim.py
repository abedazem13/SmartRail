"""
seat_sim.py - run the PC software without hardware.

Simulates the ESP32 board: produces the same serial lines as ESP32/ESP32.ino
(banner, calibration, status lines every 0.5 s, EVENT lines) for a scripted
scenario, and feeds them through seat_live.py exactly as a real board would.
Lines marked REAL show what "really" happens, so you can compare it with
what the PC software reports.

This tests the PC side (parsing, carriage counts, guidance, lost-connection
handling). It does NOT simulate the firmware's filtering: the simulated board
simply reports each change CONFIRM_DELAY_S after it happens, which is roughly
the latency of the real firmware (median window + 1 s confirmation).

Usage:
  python seat_sim.py                       # run the scenario
  python seat_sim.py --save sim_log.txt    # also save it; replay with
                                           #   python seat_live.py --replay sim_log.txt
"""

import argparse
import random

import seat_live

CONFIRM_DELAY_S = 1.2
STATUS_EVERY_S = 0.5
END_S = 48.0

# (time [s], seat or None, action)   actions: sit, leave, unplug, plug
SCENARIO = [
    (8.0,  0,    "sit"),
    (14.0, 1,    "sit"),
    (22.0, 0,    "leave"),
    (26.0, 1,    "leave"),
    (28.0, None, "unplug"),   # USB disconnected: board stops sending
    (32.0, None, "plug"),     # board restarts and recalibrates (seats are empty)
    (40.0, 1,    "sit"),
]

BASELINE = {0: 58.4, 1: 62.1}   # empty-seat distance [cm]
OCCUPIED_CM = {0: 24.0, 1: 27.5}


def boot_lines(t0, n_seats, rng):
    """Banner and calibration, timed like the real firmware."""
    lines = [
        (t0, "SmartRail seat occupancy - GP2Y0A21YK0F"),
        (t0, f"seats={n_seats} window=11 sample=40ms enter=20cm exit=12cm stable=1000ms"),
        (t0, "commands: c = recalibrate, d = toggle raw debug"),
        (t0, "--- CALIBRATION: keep all seats EMPTY. starting in 3 s ---"),
    ]
    t = t0 + 3.0
    for s in range(n_seats):
        t += 0.9                                  # 22 samples x 40 ms per seat
        lines.append((t, f"CAL seat={s} baseline={BASELINE[s]:.1f}cm "
                         f"mv={int(1000 * (BASELINE[s] / 29.988) ** (1 / -1.173))} "
                         f"noise={rng.randint(30, 80)}mV"))
    lines.append((t, "--- calibration done ---"))
    return lines, t


def board_lines(seed=1):
    """All lines the simulated board sends, as a sorted list of (t, line),
    plus the REAL events as (t, text)."""
    rng = random.Random(seed)
    seats = sorted(BASELINE)
    truth = {s: False for s in seats}        # really occupied?
    shown = {s: False for s in seats}        # what the board reports
    changes = []                             # (report_time, seat, new_state)
    real = []
    lines, running_from = boot_lines(0.0, len(seats), rng)
    connected = True
    offline = []                             # (start, end) intervals with no output

    for t, seat, action in SCENARIO:
        if action in ("sit", "leave"):
            truth[seat] = action == "sit"
            changes.append((t + CONFIRM_DELAY_S, seat, truth[seat]))
            real.append((t, f"person {'sits on' if truth[seat] else 'leaves'} seat {seat}"))
        elif action == "unplug":
            offline.append([t, None])
            real.append((t, "USB unplugged"))
        elif action == "plug":
            offline[-1][1] = t
            real.append((t, "USB plugged back in - board restarts"))
            boot, running_from2 = boot_lines(t, len(seats), rng)
            lines += boot
            offline.append([t + 0.001, running_from2])   # silent while calibrating
            for s in seats:
                changes.append((running_from2, s, False))  # firmware resets to EMPTY

    def is_offline(t):
        return any(a <= t < (b if b is not None else END_S + 1) for a, b in offline)

    # EVENT lines
    for t, s, occ in sorted(changes):
        if is_offline(t) or t < running_from:
            continue
        if shown[s] != occ:
            d = OCCUPIED_CM[s] if occ else BASELINE[s]
            lines.append((t, f"EVENT seat={s} state={'OCCUPIED' if occ else 'EMPTY'} "
                             f"dist={d + rng.uniform(-0.8, 0.8):.1f}cm"))
        shown[s] = occ

    # status lines every 0.5 s
    shown = {s: False for s in seats}
    ch = sorted(changes)
    t = running_from
    while t < END_S:
        while ch and ch[0][0] <= t:
            _, s, occ = ch.pop(0)
            shown[s] = occ
        if not is_offline(t):
            parts = []
            for s in seats:
                pending = any(abs(rt - CONFIRM_DELAY_S - t) < CONFIRM_DELAY_S and rt > t
                              for rt, ss, _ in changes if ss == s)
                d = (OCCUPIED_CM[s] if shown[s] else BASELINE[s]) + rng.uniform(-0.6, 0.6)
                parts.append(f"S{s} dist={d:5.1f}cm base={BASELINE[s]:5.1f}cm "
                             f"noise={rng.randint(30, 90):3d}mV "
                             f"{'OCCUPIED' if shown[s] else 'EMPTY   '}{'?' if pending else ' '}  ")
            lines.append((t, "".join(parts)))
        t = round(t + STATUS_EVERY_S, 3)

    return sorted(lines, key=lambda x: x[0]), sorted(real)


def sim_source(save_path=None):
    lines, real = board_lines()
    log = open(save_path, "w", encoding="utf-8") if save_path else None
    tick, i, r = 0.0, 0, 0
    while tick <= END_S:
        while r < len(real) and real[r][0] <= tick:
            print(f"[{real[r][0]:7.1f}s] REAL: {real[r][1]}")
            r += 1
        while i < len(lines) and lines[i][0] <= tick:
            t, text = lines[i]
            if log:
                log.write(f"{t:.2f}\t{text}\n")
            yield t, text
            i += 1
        yield tick, None
        tick = round(tick + seat_live.TICK_S, 3)
    if log:
        log.close()


def main():
    ap = argparse.ArgumentParser(description="Run the PC software on a simulated board.")
    ap.add_argument("--save", help="also save the simulated session for --replay")
    ap.add_argument("--report", type=float, default=4.0, help="summary interval [s]")
    args = ap.parse_args()
    print("Simulated board: 2 seats (seat 0 -> car 1, seat 1 -> car 2).\n")
    seat_live.run(sim_source(args.save),
                  on_info=lambda t, s: print(f"[{t:7.1f}s] board: {s}"),
                  on_report=seat_live.print_report, report_every=args.report)
    if args.save:
        print(f"\nsaved to {args.save} - replay with: python seat_live.py --replay {args.save}")


if __name__ == "__main__":
    main()
