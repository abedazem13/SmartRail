"""
SmartRail — one Israel Railways journey, with and without the display.

The generic model in `boarding_sim.py` answers whether guidance shortens a
stop. This file asks the question the project actually cares about: on a real
line, with a real train, how much time does a whole journey lose to boarding,
and how much of it would the display give back?

THE SERVICE MODELLED
--------------------
A southbound morning-peak service on the coastal line, calling at ten
stations from Haifa-Hof HaCarmel to Tel Aviv Savidor Center. The train is an
eight-car Bombardier Twindexx Vario double-deck set, the type Israel Railways
runs on this line, with about 1,000 seats.

The 60-second reference line is OUR ASSUMPTION, not an Israel Railways
figure. No per-station allowance is published: we downloaded the national
GTFS feed, kept the rail trips and compared arrival_time with departure_time
at every stop. They are identical at every one, so Israel Railways absorbs
dwell into the run time between stations rather than publishing it
(gtfs_dwell.py performs this check). Treat the line as "about a minute, the
usual order of magnitude for an intermediate stop" and replace it with a
stopwatch measurement before quoting any overrun figure.

WHAT IS REAL AND WHAT IS ASSUMED
--------------------------------
Real: the line and its station order, the eight-car 1,000-seat train, and the
relative size of the stations, anchored on published annual passenger counts
(Tel Aviv HaShalom 15.3 m in 2019, the busiest in the country; Haifa-Hof
HaCarmel 4.6 m, fifth; Herzliya 3.0 m, fourteenth).

Assumed: how those annual totals translate into one peak train, the 60-second
reference line (see above), and the boarding and alighting rates per
passenger. The
per-station passenger numbers below are the team's estimates for a busy
morning service, not figures from Israel Railways. Replace them with counts
from a real platform before quoting any of this as fact.

Usage:
    python israel_journey.py
    python israel_journey.py --runs 400 --compliance 0.4
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from dataclasses import dataclass, asdict

import numpy as np

from boarding_sim import Params, baseline_profile, choose_cars, dwell_seconds

# --------------------------------------------------------------------------
# The service
# --------------------------------------------------------------------------

CARS = 8                 # Twindexx Vario eight-car set
SEATS_PER_CAR = 125      # about 1,000 seats per train
SCHEDULED_DWELL_S = 60   # ASSUMED reference only - not a published figure
START_ON_BOARD = 300     # already aboard from Nahariya and Akko


@dataclass
class Stop:
    name: str
    boarding: int        # passengers joining this train at this station
    alighting: int       # passengers leaving it here
    entrances: tuple     # platform access points, as car positions (1..8)


# Southbound morning peak. Boarding is heavy at the suburban stations and
# alighting is heavy in Tel Aviv, which is how this line actually loads.
JOURNEY = [
    Stop("Haifa-Hof HaCarmel",     220,  25, ((2.0, 0.6), (6.0, 0.4))),
    Stop("Atlit",                   40,   8, ((3.0, 1.0),)),
    Stop("Binyamina",              120,  15, ((2.5, 0.7), (6.5, 0.3))),
    Stop("Caesarea-Pardes Hanna",   70,  10, ((3.0, 1.0),)),
    Stop("Hadera West",            130,  20, ((2.0, 0.6), (6.0, 0.4))),
    Stop("Netanya",                180,  30, ((3.0, 0.6), (7.0, 0.4))),
    Stop("Beit Yehoshua",           50,  10, ((4.0, 1.0),)),
    Stop("Herzliya",               150,  60, ((2.0, 0.5), (6.0, 0.5))),
    Stop("Tel Aviv University",     40, 260, ((3.0, 0.5), (7.0, 0.5))),
    Stop("Tel Aviv Savidor Center", 20, 430, ((2.0, 0.5), (6.0, 0.5))),
]


# --------------------------------------------------------------------------
# One journey
# --------------------------------------------------------------------------

def run_journey(guided: bool, compliance: float, seed: int,
                strategy: str = "adaptive") -> dict:
    """Simulate the ten stops once. Returns dwell and overrun per station."""
    arrivals_rng = np.random.default_rng(seed)
    behaviour_rng = np.random.default_rng(seed + 10_000)

    occupancy = np.full(CARS, START_ON_BOARD / CARS, dtype=float)
    dwells, boarders_per_stop, busiest = [], [], []
    peak_load = occupancy.sum()

    for stop in JOURNEY:
        p = Params(cars=CARS, seats_per_car=SEATS_PER_CAR,
                   access_points=stop.entrances, spread_cars=1.3,
                   compliance=compliance, max_walk_cars=2.0,
                   strategy=strategy, available_min=10,
                   t_fixed=11.0, t_board=1.5, t_alight=1.0, crowding=0.45)

        # Alighting is spread over the cars in proportion to who is aboard.
        share = occupancy / occupancy.sum()
        alighters = arrivals_rng.multinomial(stop.alighting, share)
        alighters = np.minimum(alighters, np.round(occupancy).astype(int))
        occupancy = occupancy - alighters

        waiting = arrivals_rng.poisson(stop.boarding)
        free = np.maximum(SEATS_PER_CAR - occupancy, 0.0)
        boarders = choose_cars(waiting, baseline_profile(p), free, p,
                               guided, behaviour_rng)

        dwells.append(dwell_seconds(boarders, alighters, occupancy + boarders, p))
        boarders_per_stop.append(boarders)
        busiest.append(int(boarders.max()))
        occupancy = occupancy + boarders
        peak_load = max(peak_load, occupancy.sum())

    dwells = np.array(dwells)
    return {
        "dwell": dwells,
        "overrun": np.maximum(dwells - SCHEDULED_DWELL_S, 0.0),
        "busiest": np.array(busiest),
        "boarders": np.array(boarders_per_stop),
        "peak_load": float(peak_load),
    }


def average(guided: bool, compliance: float, runs: int, strategy: str) -> dict:
    """Mean over `runs` independent journeys."""
    out = [run_journey(guided, compliance, seed, strategy) for seed in range(runs)]
    return {
        "dwell": np.mean([r["dwell"] for r in out], axis=0),
        "overrun": np.mean([r["overrun"] for r in out], axis=0),
        "busiest": np.mean([r["busiest"] for r in out], axis=0),
        "peak_load": float(np.mean([r["peak_load"] for r in out])),
    }


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=300)
    ap.add_argument("--compliance", type=float, default=0.6)
    ap.add_argument("--strategy", default="adaptive")
    ap.add_argument("--outdir", default="results")
    args = ap.parse_args()

    base = average(False, 0.0, args.runs, args.strategy)
    app = average(True, args.compliance, args.runs, args.strategy)

    print("\nSmartRail on Israel Railways — coastal line, southbound morning peak")
    print("=" * 78)
    print(f"{CARS}-car Twindexx Vario, {CARS * SEATS_PER_CAR} seats. "
          f"{args.runs} simulated journeys, compliance {args.compliance:.0%}.")
    print(f"Reference dwell line {SCHEDULED_DWELL_S} s per stop (assumed, not published).\n")

    print(f"{'Station':<26}{'Board':>7}{'Dwell now':>11}{'With app':>10}{'Saved':>8}")
    print("-" * 78)
    for stop, d0, d1 in zip(JOURNEY, base["dwell"], app["dwell"]):
        print(f"{stop.name:<26}{stop.boarding:>7}{d0:>10.0f}s{d1:>9.0f}s"
              f"{d0 - d1:>7.0f}s")
    print("-" * 78)
    t0, t1 = base["dwell"].sum(), app["dwell"].sum()
    print(f"{'Total time standing still':<26}{'':>7}{t0:>10.0f}s{t1:>9.0f}s"
          f"{t0 - t1:>7.0f}s")
    print(f"{'':<26}{'':>7}{t0/60:>9.1f}m{t1/60:>8.1f}m{(t0-t1)/60:>6.1f}m\n")

    over0 = int(sum(1 for d in base["dwell"] if d > SCHEDULED_DWELL_S))
    over1 = int(sum(1 for d in app["dwell"] if d > SCHEDULED_DWELL_S))
    print(f"Stops that overrun the {SCHEDULED_DWELL_S} s allowance: "
          f"{over0} of {len(JOURNEY)} now, {over1} with the display")
    print(f"Delay accumulated over the journey: {base['overrun'].sum():.0f} s now, "
          f"{app['overrun'].sum():.0f} s with the display "
          f"({base['overrun'].sum() - app['overrun'].sum():.0f} s recovered)")
    print(f"Busiest door, averaged over the ten stops: "
          f"{base['busiest'].mean():.0f} passengers now, "
          f"{app['busiest'].mean():.0f} with the display")
    print(f"Fullest point of the journey: {base['peak_load']:.0f} passengers "
          f"of {CARS * SEATS_PER_CAR} seats\n")

    os.makedirs(args.outdir, exist_ok=True)
    with open(os.path.join(args.outdir, "israel_journey.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["station", "boarding", "alighting", "dwell_now_s",
                    "dwell_with_app_s", "saved_s", "overrun_now_s",
                    "overrun_with_app_s"])
        for stop, d0, d1, o0, o1 in zip(JOURNEY, base["dwell"], app["dwell"],
                                        base["overrun"], app["overrun"]):
            w.writerow([stop.name, stop.boarding, stop.alighting, round(d0, 1),
                        round(d1, 1), round(d0 - d1, 1), round(o0, 1), round(o1, 1)])

    with open(os.path.join(args.outdir, "israel_journey.json"), "w") as f:
        json.dump({"cars": CARS, "seats_per_car": SEATS_PER_CAR,
                   "scheduled_dwell_s": SCHEDULED_DWELL_S,
                   "runs": args.runs, "compliance": args.compliance,
                   "total_dwell_now_s": float(t0),
                   "total_dwell_with_app_s": float(t1),
                   "saved_s": float(t0 - t1),
                   "overrun_now_s": float(base["overrun"].sum()),
                   "overrun_with_app_s": float(app["overrun"].sum()),
                   "stations": [s.name for s in JOURNEY]}, f, indent=2)

    import charts
    charts.israel_journey([s.name for s in JOURNEY], base, app, SCHEDULED_DWELL_S,
                          os.path.join(args.outdir, "israel_journey.png"))
    print(f"written to {os.path.abspath(args.outdir)}")


if __name__ == "__main__":
    main()
