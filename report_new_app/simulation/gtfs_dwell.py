"""
Measure scheduled dwell time from the Israeli GTFS feed.

Why this exists
---------------
The simulation uses a 60-second reference line for the time a train is
allowed to stand at an intermediate station. That number is an assumption.
This script replaces it with whatever the published timetable actually says.

The feed is published nightly by the Ministry of Transport at
https://gtfs.mot.gov.il/gtfsfiles/ and includes Israel Railways. Each row of
stop_times.txt carries an arrival_time and a departure_time; the difference
between them is the scheduled dwell at that stop. The GTFS documentation
states the two are identical unless a scheduled break applies, so there are
two possible outcomes, and both are worth reporting:

  * mostly non-zero  -> the timetable does publish dwell. Use the median
                        printed below in israel_journey.py and cite the feed.
  * nearly all zero  -> the timetable absorbs dwell into the running time
                        between stations. The 60 s line stays an assumption
                        and should be measured with a stopwatch instead.

Usage
-----
    python gtfs_dwell.py                       # downloads the feed (~100 MB)
    python gtfs_dwell.py --zip israel.zip      # use a feed already downloaded
    python gtfs_dwell.py --route-type 2        # 2 = rail, the GTFS default

Standard library only. stop_times.txt is large, so it is streamed rather
than loaded into memory.
"""

from __future__ import annotations

import argparse
import csv
import io
import statistics
import sys
import urllib.request
import zipfile

FEED = "https://gtfs.mot.gov.il/gtfsfiles/israel-public-transportation.zip"


def seconds(hhmmss: str) -> int | None:
    """GTFS times may exceed 24 h for services running past midnight."""
    parts = hhmmss.strip().split(":")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        return None
    h, m, s = (int(p) for p in parts)
    return h * 3600 + m * 60 + s


def read_table(zf: zipfile.ZipFile, name: str):
    with zf.open(name) as raw:
        yield from csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", help="a feed already downloaded; otherwise it is fetched")
    ap.add_argument("--route-type", default="2", help="GTFS route_type; 2 = rail")
    ap.add_argument("--sample-trips", type=int, default=2,
                    help="print this many whole trips, stop by stop")
    args = ap.parse_args()

    path = args.zip
    if not path:
        path = "israel-public-transportation.zip"
        print(f"downloading {FEED}\n(about 100 MB, once)")
        urllib.request.urlretrieve(FEED, path)

    zf = zipfile.ZipFile(path)
    names = set(zf.namelist())
    for needed in ("routes.txt", "trips.txt", "stop_times.txt", "stops.txt"):
        if needed not in names:
            sys.exit(f"{needed} is missing from the feed")

    routes = {r["route_id"] for r in read_table(zf, "routes.txt")
              if r.get("route_type") == args.route_type}
    print(f"rail routes: {len(routes)}")

    trips = {t["trip_id"]: t.get("trip_headsign", "")
             for t in read_table(zf, "trips.txt") if t["route_id"] in routes}
    print(f"rail trips:  {len(trips)}")
    if not trips:
        sys.exit("no trips matched; try a different --route-type")

    stop_name = {s["stop_id"]: s["stop_name"] for s in read_table(zf, "stops.txt")}

    dwells, zero, rows = [], 0, 0
    by_stop: dict[str, list[int]] = {}
    samples: dict[str, list] = {}
    wanted = set(list(trips)[:args.sample_trips])

    print("reading stop_times.txt ...")
    for row in read_table(zf, "stop_times.txt"):
        tid = row["trip_id"]
        if tid not in trips:
            continue
        a, d = seconds(row["arrival_time"]), seconds(row["departure_time"])
        if a is None or d is None:
            continue
        rows += 1
        dwell = d - a
        if dwell == 0:
            zero += 1
        else:
            dwells.append(dwell)
            by_stop.setdefault(row["stop_id"], []).append(dwell)
        if tid in wanted:
            samples.setdefault(tid, []).append(
                (int(row["stop_sequence"]), stop_name.get(row["stop_id"], row["stop_id"]),
                 row["arrival_time"], row["departure_time"], dwell))

    print(f"\nrail stop rows examined: {rows:,}")
    if not rows:
        sys.exit("no rail stop times found")
    print(f"rows with zero dwell:    {zero:,}  ({100 * zero / rows:.1f}%)")
    print(f"rows with dwell > 0:     {len(dwells):,}  ({100 * len(dwells) / rows:.1f}%)")

    if dwells:
        dwells.sort()
        print(f"\nscheduled dwell where it is published, in seconds")
        print(f"  median {statistics.median(dwells):.0f}   mean {statistics.mean(dwells):.0f}"
              f"   min {dwells[0]}   max {dwells[-1]}")
        print(f"  10th percentile {dwells[len(dwells)//10]}   "
              f"90th percentile {dwells[9*len(dwells)//10]}")
        print("\nbusiest stations by published dwell (median seconds, count):")
        ranked = sorted(by_stop.items(), key=lambda kv: -len(kv[1]))[:12]
        for sid, vals in ranked:
            print(f"  {stop_name.get(sid, sid)[:38]:<40}"
                  f"{statistics.median(vals):>6.0f}s{len(vals):>8}")
        print("\n=> the timetable DOES publish dwell. Put the median above into")
        print("   SCHEDULED_DWELL_S in israel_journey.py and cite the feed.")
    else:
        print("\n=> every rail stop has arrival_time == departure_time, so the")
        print("   timetable does not publish dwell at all. Keep the 60 s line as")
        print("   an assumption and measure it with a stopwatch instead.")

    for tid, stops in samples.items():
        print(f"\nsample trip {tid}  (train {trips[tid]}):")
        for seq, name, a, d, dw in sorted(stops):
            print(f"  {seq:>3}  {name[:34]:<36}{a}  {d}  dwell {dw:>4}s")


if __name__ == "__main__":
    main()
