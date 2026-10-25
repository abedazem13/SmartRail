"""
SmartRail — boarding and dwell-time simulation.

Answers one question: does telling waiting passengers where the free seats are
shorten the time the train stands at the platform?

THE MODEL IN ONE PARAGRAPH
--------------------------
Passengers arrive at the platform as a Poisson process, so the number waiting
at a stop is Poisson(lambda). Each passenger picks a carriage. Because every
passenger picks independently, the number boarding carriage i is itself
Poisson, with mean lambda * p_i (the thinning property of a Poisson process).
What changes between the two scenarios is not the shape of that distribution
but its means:

  baseline   p_i is bunched around the platform entrances (a Gaussian profile)
  with app   a share of passengers walk to a nearby carriage with more free
             seats, which pushes p_i towards uniform (1/C for every carriage)

The train cannot leave until its slowest door has finished, so dwell time is
set by the busiest door, not the average one. Flattening p_i lowers the
expected maximum, which is where any time saving comes from.

  door time  = t_alight * A_i + t_board * B_i * crowding_i
  dwell      = t_fixed + max over carriages of (door time)

PARAMETERS ARE LITERATURE-INFORMED DEFAULTS, NOT MEASUREMENTS
-------------------------------------------------------------
The structure (dwell = fixed term + per-passenger terms, taken at the busiest
door) follows the standard dwell-time formulation; see Simulation/README.md
for sources. The constants below are defaults in the published range. They
have NOT been measured at the team's own station. Use --sweep-board to see
how much the conclusion depends on them.

Usage
-----
    python boarding_sim.py                      # headline comparison + charts
    python boarding_sim.py --compliance 0.5
    python boarding_sim.py --stops 500 --seed 7
    python boarding_sim.py --no-charts          # numbers only
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from dataclasses import dataclass, asdict, field

import numpy as np

# --------------------------------------------------------------------------
# Default parameters. Every one of these is an assumption; see README.
# --------------------------------------------------------------------------

@dataclass
class Params:
    cars: int = 12                 # carriages, matching the SmartRail display
    seats_per_car: int = 108       # seats per carriage, as in dashboard_model.py

    # --- demand ---
    arrivals: float = 240.0        # mean passengers boarding per stop (Poisson)
    alight_fraction: float = 0.25  # share of seated passengers leaving per stop
                                   # (sets the equilibrium load: arrivals per car
                                   #  divided by this, here ~80 of 108 seats)
    start_occupancy: float = 0.76  # train arrives this full (0-1)

    # --- where people wait, with no guidance ---
    # Access points given as carriage positions (1-based) with a weight each:
    # a main entrance near the front and a staircase near the middle.
    access_points: tuple = ((3.0, 0.6), (8.0, 0.4))
    spread_cars: float = 1.6       # std dev of the waiting profile, in carriages

    # --- behaviour with the app ---
    compliance: float = 0.6        # share of passengers who act on the display
    max_walk_cars: float = 3.0     # how far a passenger will walk to a better car
    strategy: str = "proportional" # how a passenger reads the display:
                                   #  "avoid_full"   spread over the reachable
                                   #                 carriages the display marks as
                                   #                 having seats (what SmartRail shows)
                                   #  "proportional" weight by the free-seat count
                                   #  "best"         all walk to the emptiest carriage
                                   #  "spread"       ignore the counts, spread evenly
    available_min: int = 10        # free seats before the display calls a carriage
                                   # "seats available" (AVAILABLE_FREE_MIN in the app)
    scarce_seats_frac: float = 0.20  # below this share of seats free, "adaptive"
                                   # stops ranking carriages by free seats and
                                   # simply spreads people out instead

    # --- dwell time, seconds ---
    t_fixed: float = 11.0          # door open + close + reaction, per stop
    t_board: float = 1.5           # per boarding passenger at one door
    t_alight: float = 1.0          # per alighting passenger at one door
    crowding: float = 0.45         # extra boarding time at a full carriage

    foresee_alighting: bool = True  # True: the display shows free seats AFTER the
                                   #   passengers who are about to get off have gone.
                                   #   Optimistic: no sensor can know that in advance.
                                   # False: the display shows what the sensors see as
                                   #   the train approaches, before anyone alights.

    stops: int = 500               # simulated station stops per scenario
    seed: int = 12345


# --------------------------------------------------------------------------
# Where passengers wait when nothing guides them
# --------------------------------------------------------------------------

def baseline_profile(p: Params) -> np.ndarray:
    """Probability of choosing each carriage with no guidance.

    A mixture of Gaussians centred on the platform access points: people stand
    where they entered the platform. This is the 'bunched' case the project
    sets out to improve.
    """
    x = np.arange(1, p.cars + 1, dtype=float)
    profile = np.zeros_like(x)
    for centre, weight in p.access_points:
        profile += weight * np.exp(-((x - centre) ** 2) / (2 * p.spread_cars ** 2))
    return profile / profile.sum()


# --------------------------------------------------------------------------
# One station stop
# --------------------------------------------------------------------------

def choose_cars(n: int, base_p: np.ndarray, free: np.ndarray, p: Params,
                guided: bool, rng: np.random.Generator) -> np.ndarray:
    """Return the number of passengers boarding each carriage.

    Every passenger first picks the carriage they would naturally walk to,
    drawn from the baseline profile. With the app, a `compliance` share of them
    act on the display, choosing among the carriages within `max_walk_cars`
    of where they are standing.

    Which rule they follow matters more than it looks. Under "best" everyone
    reads the same screen and walks to the same emptiest carriage, so the
    crowd moves instead of spreading and the busiest door gets worse. Under
    "proportional" a carriage attracts passengers in proportion to the free
    seats it is showing, which spreads them.
    """
    counts = np.zeros(p.cars, dtype=int)
    if n == 0:
        return counts

    natural = rng.choice(p.cars, size=n, p=base_p)          # 0-based carriage
    if not guided:
        return np.bincount(natural, minlength=p.cars)

    follows = rng.random(n) < p.compliance
    positions = np.arange(p.cars)
    counts += np.bincount(natural[~follows], minlength=p.cars)   # ignore the sign

    if p.strategy == "personalised":
        # Only an app can do this: each request gets its own answer, chosen to
        # even out the load so far. A shared screen cannot, because everyone
        # reading it sees the same picture. Requests are served in arrival
        # order, not grouped by where people stand, so no part of the platform
        # is systematically served first.
        asking = natural[follows].copy()
        rng.shuffle(asking)
        for start in asking:
            reach = np.flatnonzero(np.abs(positions - start) <= p.max_walk_cars)
            counts[min(reach, key=lambda c: (counts[c], -free[c], c))] += 1
        return counts

    # Everyone standing in the same place sees the same screen, so handle them
    # per starting carriage.
    starts = np.bincount(natural[follows], minlength=p.cars)
    for start, n_here in enumerate(starts):
        if n_here == 0:
            continue
        reachable = np.abs(positions - start) <= p.max_walk_cars
        weights = np.where(reachable, free, 0.0)
        if weights.sum() <= 0:                       # nothing better within reach
            counts[start] += n_here
        elif p.strategy == "best":
            counts[int(np.argmax(weights))] += n_here
        elif p.strategy == "top3":
            # What the SmartRail screen actually does: it names the three
            # carriages with the most free seats, train-wide, and badges them
            # "good choice". A passenger walks to the nearest badged carriage
            # within reach, and stays put if none of the three is reachable.
            top = np.argsort(-free, kind="stable")[:3]
            options = [c for c in top if abs(c - start) <= p.max_walk_cars]
            if not options:
                counts[start] += n_here
            else:
                nearest = min(options, key=lambda c: (abs(c - start), c))
                counts[nearest] += n_here
        elif p.strategy == "proportional" or (
                p.strategy == "adaptive"
                and free.sum() >= p.scarce_seats_frac * p.cars * p.seats_per_car):
            counts += rng.multinomial(n_here, weights / weights.sum())
        else:
            # What the display actually shows: carriages are marked as having
            # seats or not. Passengers spread over the ones that have them.
            good = reachable & (free >= p.available_min)
            if p.strategy in ("spread", "adaptive") or not good.any():
                good = reachable
            share = good / good.sum()
            counts += rng.multinomial(n_here, share)
    return counts


def dwell_seconds(boarders: np.ndarray, alighters: np.ndarray,
                  occupancy: np.ndarray, p: Params) -> float:
    """Dwell is set by the busiest door, not the average one."""
    load = np.clip(occupancy / p.seats_per_car, 0.0, 1.5)
    crowd = 1.0 + p.crowding * load
    door_times = p.t_alight * alighters + p.t_board * boarders * crowd
    return p.t_fixed + float(door_times.max())


def run(p: Params, guided: bool) -> dict:
    """Simulate `p.stops` station stops.

    Arrivals, alighting and behaviour draw from separate random streams, so the
    guided and unguided runs face the same sequence of passenger arrivals. The
    comparison is paired: a difference in dwell comes from where people choose
    to stand, not from different demand.
    """
    arrivals_rng = np.random.default_rng(p.seed)
    alight_rng = np.random.default_rng(p.seed + 1)
    behaviour_rng = np.random.default_rng(p.seed + 2)

    base_p = baseline_profile(p)
    occupancy = np.full(p.cars, p.start_occupancy * p.seats_per_car)

    dwells, boarders_log, busiest_log = [], [], []
    for _ in range(p.stops):
        seen_on_approach = np.maximum(p.seats_per_car - occupancy, 0.0)

        alighters = alight_rng.binomial(np.round(occupancy).astype(int),
                                        p.alight_fraction)
        occupancy = occupancy - alighters

        waiting = arrivals_rng.poisson(p.arrivals)
        # What the waiting passenger actually had to go on. They chose where to
        # stand before the train arrived, so they could not see the alighting.
        free = (np.maximum(p.seats_per_car - occupancy, 0.0) if p.foresee_alighting
                else seen_on_approach)
        boarders = choose_cars(waiting, base_p, free, p, guided, behaviour_rng)

        dwells.append(dwell_seconds(boarders, alighters, occupancy + boarders, p))
        boarders_log.append(boarders)
        busiest_log.append(int(boarders.max()))
        occupancy = occupancy + boarders

    boarders_log = np.array(boarders_log)
    return {
        "dwell": np.array(dwells),
        "boarders": boarders_log,              # stops x cars
        "per_car_mean": boarders_log.mean(axis=0),
        "busiest": np.array(busiest_log),
        "base_profile": base_p,
    }


# --------------------------------------------------------------------------

def evenness(per_car_mean: np.ndarray) -> dict:
    """How far the boarding distribution is from uniform.

    `peak_to_mean` is the one that matters for dwell: the busiest carriage
    against the average carriage. 1.0 means perfectly uniform.
    """
    mean = per_car_mean.mean()
    uniform = np.full_like(per_car_mean, mean)
    return {
        "peak_to_mean": float(per_car_mean.max() / mean),
        "cv": float(per_car_mean.std() / mean),
        # total variation distance from uniform, 0 = uniform, 1 = all in one car
        "distance_from_uniform": float(np.abs(per_car_mean - uniform).sum()
                                       / (2 * per_car_mean.sum())),
    }


def poisson_check(boarders: np.ndarray, car_index: int) -> dict:
    """Evidence that the per-carriage counts really are Poisson.

    For a Poisson variable the variance equals the mean. The model never
    samples a per-car Poisson directly: it draws a Poisson total and then
    assigns each passenger independently, so this is a property that emerges.
    """
    counts = boarders[:, car_index]
    mean, var = float(counts.mean()), float(counts.var(ddof=1))
    return {"car": car_index + 1, "mean": mean, "variance": var,
            "variance_over_mean": var / mean if mean else float("nan")}


# --------------------------------------------------------------------------
# Experiments
# --------------------------------------------------------------------------

def compare(p: Params) -> dict:
    base = run(p, False)
    app = run(p, True)
    saving = base["dwell"].mean() - app["dwell"].mean()
    return {
        "baseline": base, "app": app,
        "summary": {
            "dwell_baseline_s": float(base["dwell"].mean()),
            "dwell_app_s": float(app["dwell"].mean()),
            "saving_s": float(saving),
            "saving_pct": float(100 * saving / base["dwell"].mean()),
            "busiest_door_baseline": float(base["busiest"].mean()),
            "busiest_door_app": float(app["busiest"].mean()),
            "evenness_baseline": evenness(base["per_car_mean"]),
            "evenness_app": evenness(app["per_car_mean"]),
            "poisson_check_baseline": poisson_check(base["boarders"], 2),
            "poisson_check_app": poisson_check(app["boarders"], 2),
        },
    }


def sweep_compliance(p: Params, points: int = 11,
                     strategy: str | None = None) -> list[dict]:
    """Dwell time against the share of passengers who act on the display.

    `strategy` says what those passengers then do; see Params.strategy. The
    sign of the result depends on it, so both are reported.
    """
    out = []
    baseline = run(p, False)["dwell"].mean()
    for c in np.linspace(0.0, 1.0, points):
        q = Params(**{**asdict(p), "compliance": float(c),
                      "strategy": strategy or p.strategy})
        r = run(q, True)
        out.append({
            "compliance": float(c),
            "dwell_s": float(r["dwell"].mean()),
            "saving_s": float(baseline - r["dwell"].mean()),
            "saving_pct": float(100 * (baseline - r["dwell"].mean()) / baseline),
            "peak_to_mean": evenness(r["per_car_mean"])["peak_to_mean"],
        })
    return out


def compare_strategies(p: Params) -> list[dict]:
    """How much does the *advice* matter, as opposed to the compliance rate?"""
    base = run(p, False)
    rows = [{"strategy": "no guidance",
             "dwell_s": float(base["dwell"].mean()),
             "saving_pct": 0.0,
             "busiest_door": float(base["busiest"].mean()),
             "peak_to_mean": evenness(base["per_car_mean"])["peak_to_mean"]}]
    labels = {"personalised": "a different carriage per passenger (app only)",
              "top3": "the three best carriages (what SmartRail shows)",
              "proportional": "weight by free seats",
              "avoid_full": "avoid the full carriages",
              "spread": "just spread out (no counts)",
              "best": "all to the emptiest carriage"}
    for strat, label in labels.items():
        q = Params(**{**asdict(p), "strategy": strat})
        r = run(q, True)
        rows.append({"strategy": label,
                     "dwell_s": float(r["dwell"].mean()),
                     "saving_pct": float(100 * (base["dwell"].mean() - r["dwell"].mean())
                                         / base["dwell"].mean()),
                     "busiest_door": float(r["busiest"].mean()),
                     "peak_to_mean": evenness(r["per_car_mean"])["peak_to_mean"]})
    return rows


def sweep_board_rate(p: Params, rates=(0.8, 1.0, 1.25, 1.5, 2.0, 2.5)) -> list[dict]:
    """Does the conclusion survive a different boarding rate per passenger?"""
    out = []
    for t in rates:
        q = Params(**{**asdict(p), "t_board": float(t)})
        b = run(q, False)["dwell"].mean()
        a = run(q, True)["dwell"].mean()
        out.append({"t_board_s": float(t), "dwell_baseline_s": float(b),
                    "dwell_app_s": float(a), "saving_s": float(b - a),
                    "saving_pct": float(100 * (b - a) / b)})
    return out


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

def print_report(p: Params, res: dict, comp: list[dict], strat: list[dict],
                 board: list[dict]) -> None:
    s = res["summary"]
    print("\nSmartRail boarding simulation")
    print("=" * 64)
    print(f"{p.cars} carriages, {p.arrivals:.0f} passengers per stop (Poisson), "
          f"{p.stops} stops, seed {p.seed}")
    print(f"compliance {p.compliance:.0%}, passengers walk at most "
          f"{p.max_walk_cars:.0f} carriages\n")

    print("Dwell time")
    print("-" * 64)
    print(f"  no guidance        {s['dwell_baseline_s']:7.1f} s")
    print(f"  with the display   {s['dwell_app_s']:7.1f} s")
    print(f"  saving             {s['saving_s']:7.1f} s  ({s['saving_pct']:.1f}%)\n")

    print("Busiest door (the one that holds the train)")
    print("-" * 64)
    print(f"  no guidance        {s['busiest_door_baseline']:7.1f} passengers")
    print(f"  with the display   {s['busiest_door_app']:7.1f} passengers\n")

    print("How far the boarding distribution is from uniform")
    print("-" * 64)
    eb, ea = s["evenness_baseline"], s["evenness_app"]
    print(f"  busiest / average carriage   {eb['peak_to_mean']:.2f}  ->  "
          f"{ea['peak_to_mean']:.2f}   (1.00 = uniform)")
    print(f"  distance from uniform        {eb['distance_from_uniform']:.3f}  ->  "
          f"{ea['distance_from_uniform']:.3f}\n")

    print("Are the per-carriage counts Poisson?  (variance / mean = 1 if so)")
    print("-" * 64)
    for tag, key in (("no guidance", "poisson_check_baseline"),
                     ("with display", "poisson_check_app")):
        c = s[key]
        print(f"  {tag:<13} carriage {c['car']}: mean {c['mean']:6.2f}, "
              f"variance {c['variance']:6.2f}, ratio {c['variance_over_mean']:.2f}")

    print("\nDwell against the share of passengers who follow the display")
    print("-" * 64)
    print("  compliance   dwell (s)   saving (s)   saving (%)   busiest/avg")
    for row in comp:
        print(f"  {row['compliance']:9.0%}   {row['dwell_s']:9.1f}   "
              f"{row['saving_s']:10.1f}   {row['saving_pct']:10.1f}   "
              f"{row['peak_to_mean']:11.2f}")

    print("\nWhat the display tells people matters as much as how many obey")
    print("-" * 64)
    print("  advice                                            dwell (s)  saving (%)  busiest")
    for row in strat:
        print(f"  {row['strategy']:<48}{row['dwell_s']:9.1f}  {row['saving_pct']:10.1f}  "
              f"{row['busiest_door']:8.1f}")

    print("\nSensitivity: does the result depend on the boarding rate?")
    print("-" * 64)
    print("  s/passenger   baseline (s)   with app (s)   saving (%)")
    for row in board:
        print(f"  {row['t_board_s']:11.2f}   {row['dwell_baseline_s']:12.1f}   "
              f"{row['dwell_app_s']:12.1f}   {row['saving_pct']:10.1f}")
    print()


def write_outputs(outdir: str, p: Params, res: dict, comp: list[dict],
                  strat: list[dict], board: list[dict]) -> None:
    os.makedirs(outdir, exist_ok=True)

    with open(os.path.join(outdir, "summary.json"), "w") as f:
        json.dump({"params": asdict(p), "summary": res["summary"],
                   "compliance_sweep": comp, "strategy_comparison": strat,
                   "board_rate_sweep": board},
                  f, indent=2)

    with open(os.path.join(outdir, "boarders_per_car.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["car", "mean_boarders_no_guidance", "mean_boarders_with_app",
                    "uniform_reference"])
        uniform = res["baseline"]["per_car_mean"].mean()
        for i, (b, a) in enumerate(zip(res["baseline"]["per_car_mean"],
                                       res["app"]["per_car_mean"]), start=1):
            w.writerow([i, round(float(b), 2), round(float(a), 2), round(float(uniform), 2)])

    with open(os.path.join(outdir, "compliance_sweep.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(comp[0]))
        w.writeheader()
        w.writerows(comp)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stops", type=int, default=Params.stops)
    ap.add_argument("--arrivals", type=float, default=Params.arrivals)
    ap.add_argument("--compliance", type=float, default=Params.compliance)
    ap.add_argument("--max-walk-cars", type=float, default=Params.max_walk_cars)
    ap.add_argument("--t-board", type=float, default=Params.t_board)
    ap.add_argument("--strategy", default=Params.strategy,
                    choices=["proportional", "avoid_full", "spread", "best"])
    ap.add_argument("--seed", type=int, default=Params.seed)
    ap.add_argument("--outdir", default="results")
    ap.add_argument("--no-charts", action="store_true")
    args = ap.parse_args()

    p = Params(stops=args.stops, arrivals=args.arrivals, compliance=args.compliance,
               max_walk_cars=args.max_walk_cars, t_board=args.t_board,
               strategy=args.strategy, seed=args.seed)

    res = compare(p)
    comp = sweep_compliance(p)
    comp_top3 = sweep_compliance(p, strategy="top3")
    strat = compare_strategies(p)
    board = sweep_board_rate(p)

    print_report(p, res, comp, strat, board)
    write_outputs(args.outdir, p, res, comp, strat, board)
    print(f"numbers written to {os.path.abspath(args.outdir)}")

    if not args.no_charts:
        import charts
        charts.make_all(p, res, comp, comp_top3, strat, args.outdir)
        charts.busiest_door_spread(p, [
            ("No display", "grey", res["baseline"]),
            ("Stage 3: positional map, each carriage shows its own state", "green",
             run(Params(**{**asdict(p), "strategy": "proportional"}), True)),
            ("Stage 2: display names the three best carriages", "red",
             run(Params(**{**asdict(p), "strategy": "top3"}), True)),
        ], os.path.join(args.outdir, "busiest_door.png"),
           note=("Dwell is set at each stop by this number, so what matters is the whole spread, "
                 "not its average.\nThe stage 2 design evens out the average distribution compared "
                 "with no display, yet routinely puts 70 to 110 passengers through a single door."))
        print("charts written to the same folder")


if __name__ == "__main__":
    main()
