"""
Extract a real Israel Railways service from the GTFS feed.

Why this exists
---------------
`israel_journey.py` models a southbound coastal-line service over ten
stations. Its station order is real, but its run times and its passenger
loads are estimates. This script replaces the guesswork with what the
published timetable actually says:

  * the real sequence of stations and the real time at each one, for a
    morning, a midday and a night train;
  * how many southbound trains call at each station in those hours, which
    is the headway.

The headway matters more than it looks. The simulation currently assumes
240 passengers board per stop. With a headway, that number can be derived
instead: a station's annual ridership, spread over the operating year and
divided by the trains per hour, gives boardings per train.

Dwell time is NOT available here. `gtfs_dwell.py` establishes that every
rail stop in the feed has arrival_time equal to departure_time, so the
timetable absorbs dwell into the run time between stations.

Usage
-----
    python gtfs_service.py                        # downloads the feed
    python gtfs_service.py --zip israel.zip       # a feed already on disk
    python gtfs_service.py --headway-at Netanya   # station to count trains at

It writes `service_profile.json`, a small file (a few KB) that can be sent
straight back for the simulation to read. Standard library only.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import urllib.request
import zipfile
from collections import defaultdict
from datetime import date

FEED = "https://gtfs.mot.gov.il/gtfsfiles/israel-public-transportation.zip"

# The ten stations of the modelled service, north to south. Each entry is the
# English name used in the report and the distinctive part of the Hebrew name
# as it appears in the feed. Matching is on the Hebrew fragment, so the script
# does not depend on the feed's exact punctuation or word order.
STATIONS = [
    ("Haifa-Hof HaCarmel",     "חוף הכרמל"),
    ("Atlit",                  "עתלית"),
    ("Binyamina",              "בנימינה"),
    ("Caesarea-Pardes Hanna",  "קיסריה"),
    ("Hadera West",            "חדרה"),
    ("Netanya",                "נתניה"),
    ("Beit Yehoshua",          "בית יהושע"),
    ("Herzliya",               "הרצליה"),
    ("Tel Aviv University",    "אוניברסיטה"),
    ("Tel Aviv Savidor Center", "סבידור"),
]

BANDS = {"morning": (6 * 3600, 9 * 3600),
         "midday":  (11 * 3600, 14 * 3600),
         "night":   (20 * 3600, 23 * 3600)}


def seconds(hhmmss: str) -> int | None:
    parts = hhmmss.strip().split(":")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        return None
    h, m, s = (int(p) for p in parts)
    return h * 3600 + m * 60 + s


def hhmm(sec: int) -> str:
    return f"{sec // 3600 % 24:02d}:{sec // 60 % 60:02d}"


def read_table(zf: zipfile.ZipFile, name: str):
    with zf.open(name) as raw:
        yield from csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", help="a feed already downloaded; otherwise fetched")
    ap.add_argument("--route-type", default="2", help="GTFS route_type; 2 = rail")
    ap.add_argument("--headway-at", default="Netanya",
                    help="English station name to count trains at")
    ap.add_argument("--out", default="service_profile.json")
    args = ap.parse_args()

    path = args.zip
    if not path:
        path = "israel-public-transportation.zip"
        print(f"downloading {FEED}\n(about 100 MB, once)")
        urllib.request.urlretrieve(FEED, path)

    zf = zipfile.ZipFile(path)
    for needed in ("routes.txt", "trips.txt", "stop_times.txt", "stops.txt"):
        if needed not in set(zf.namelist()):
            sys.exit(f"{needed} is missing from the feed")

    routes = {r["route_id"] for r in read_table(zf, "routes.txt")
              if r.get("route_type") == args.route_type}
    trips = {t["trip_id"]: t.get("trip_headsign", "")
             for t in read_table(zf, "trips.txt") if t["route_id"] in routes}
    print(f"rail routes {len(routes)}, rail trips {len(trips)}")
    if not trips:
        sys.exit("no rail trips; try a different --route-type")

    # ---- match our ten stations to stop_ids -------------------------------
    stops = list(read_table(zf, "stops.txt"))
    stop_name = {s["stop_id"]: s["stop_name"] for s in stops}
    want: dict[str, set] = {}
    for english, fragment in STATIONS:
        hits = {s["stop_id"] for s in stops if fragment in s["stop_name"]}
        want[english] = hits
    id_to_station = {sid: eng for eng, ids in want.items() for sid in ids}

    print("\nstation matching:")
    for english, _ in STATIONS:
        ids = want[english]
        names = sorted({stop_name[i] for i in ids})
        flag = "  " if len(ids) == 1 else "? " if ids else "! "
        print(f" {flag}{english:<26}{len(ids):>3} stop(s)  {', '.join(names)[:46]}")
    missing = [e for e, _ in STATIONS if not want[e]]
    if missing:
        print(f"\n!! no stop matched: {', '.join(missing)}")
        print("   Open stops.txt, find the real name and edit STATIONS above.")

    # ---- collect the rail stop times --------------------------------------
    print("\nreading stop_times.txt ...")
    per_trip: dict[str, list] = defaultdict(list)
    zero = total = 0
    for row in read_table(zf, "stop_times.txt"):
        tid = row["trip_id"]
        if tid not in trips:
            continue
        a, d = seconds(row["arrival_time"]), seconds(row["departure_time"])
        if a is None or d is None:
            continue
        total += 1
        if d == a:
            zero += 1
        per_trip[tid].append((int(row["stop_sequence"]), row["stop_id"], a, d))

    print(f"rail stop rows {total:,}; arrival == departure on "
          f"{zero:,} ({100 * zero / max(total, 1):.1f}%)")

    # ---- southbound trips that serve our stations in order ----------------
    order = {eng: i for i, (eng, _) in enumerate(STATIONS)}
    candidates = []
    for tid, rows in per_trip.items():
        rows.sort()
        seq = [(id_to_station[sid], a) for _, sid, a, _ in rows if sid in id_to_station]
        # keep the first visit to each station, in the trip's own order
        seen, clean = set(), []
        for name, t in seq:
            if name not in seen:
                seen.add(name)
                clean.append((name, t))
        if len(clean) < 4:
            continue
        ranks = [order[n] for n, _ in clean]
        if ranks != sorted(ranks):          # northbound, or an odd pattern
            continue
        candidates.append((len(clean), tid, clean))

    if not candidates:
        sys.exit("\nno southbound trip served four or more of these stations; "
                 "check the station matching above")
    best_len = max(c[0] for c in candidates)
    print(f"\nsouthbound candidates {len(candidates)}; "
          f"most stations served by one trip: {best_len}")

    # ---- pick one trip per time band --------------------------------------
    services = {}
    for band, (lo, hi) in BANDS.items():
        pool = [c for c in candidates if lo <= c[2][0][1] < hi]
        if not pool:
            print(f"  {band}: no trip departs in this window")
            continue
        n_stops, tid, clean = max(pool, key=lambda c: (c[0], -c[2][0][1]))
        legs = [{"station": n, "time": hhmm(t)} for n, t in clean]
        for i in range(1, len(legs)):
            legs[i]["run_from_previous_min"] = round((clean[i][1] - clean[i - 1][1]) / 60, 1)
        services[band] = {
            "trip_id": tid,
            "train": trips[tid],
            "stations_served": n_stops,
            "total_journey_min": round((clean[-1][1] - clean[0][1]) / 60, 1),
            "stops": legs,
        }

    # ---- headways ---------------------------------------------------------
    hw_ids = want.get(args.headway_at, set())
    headways: dict[str, dict] = {}
    if hw_ids:
        per_hour: dict[int, int] = defaultdict(int)
        for _, tid, clean in candidates:
            for name, t in clean:
                if name == args.headway_at:
                    per_hour[t // 3600 % 24] += 1
        for band, (lo, hi) in BANDS.items():
            hours = range(lo // 3600, hi // 3600)
            headways[band] = {
                "hours": f"{lo // 3600:02d}:00-{hi // 3600:02d}:00",
                "southbound_trains": sum(per_hour.get(h, 0) for h in hours),
                "per_hour": {f"{h:02d}": per_hour.get(h, 0) for h in hours},
            }

    # ---- report + write ---------------------------------------------------
    for band, svc in services.items():
        print(f"\n{band}: train {svc['train']}, {svc['stations_served']} of 10 "
              f"stations, {svc['total_journey_min']:.0f} min end to end")
        for leg in svc["stops"]:
            gap = leg.get("run_from_previous_min")
            print(f"   {leg['time']}  {leg['station']:<26}"
                  + (f"+{gap:.0f} min" if gap else ""))

    if headways:
        print(f"\nsouthbound trains calling at {args.headway_at}:")
        for band, h in headways.items():
            n = h["southbound_trains"]
            detail = "  ".join(f"{k}h {v}" for k, v in h["per_hour"].items())
            print(f"   {band:<8}{h['hours']}   {n} train{'' if n == 1 else 's'}"
                  f"   ({detail})")

    profile = {
        "generated": date.today().isoformat(),
        "source": "Israel Ministry of Transport GTFS, " + FEED,
        "dwell_check": {"rail_stop_rows": total, "arrival_equals_departure": zero},
        "headway_station": args.headway_at,
        "headways": headways,
        "services": services,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=1, ensure_ascii=False)
    print(f"\nwritten to {args.out} — send this file back, it is only a few KB")


if __name__ == "__main__":
    main()
