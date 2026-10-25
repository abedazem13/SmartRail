"""Builds what a platform entrance screen shows: a positional map.

The screen is a map, not a leaderboard. Every carriage appears in its physical
position along the platform, showing its own state and the zone it stops at.
Nothing is ranked, nothing is badged, no carriage is named as the best one.

The reason is not aesthetic. Everyone waiting reads the same screen at the
same moment, so any global recommendation moves the whole crowd to the same
doors and makes the busiest door worse than showing nothing at all. A map
poses a local question instead: which of the carriages near me has room.
Two passengers standing fifty metres apart read the same screen and walk in
different directions.

Two rules protect the numbers:

  * A seat whose sensor has stopped reporting is unknown, never free. A
    carriage holding any unknown seat is shown as unknown and states only the
    seats it can prove, so the screen never claims more availability than it
    has evidence for.
  * When fewer than `scarce_fraction` of the train's seats are free, the
    screen stops grading carriages by how many seats they have and shows a
    single instruction to spread out. Near capacity the counts are small,
    noisy and nearly equal, and grading them invites everyone to chase the
    same two or three carriages.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

SCARCE_FRACTION = 0.20   # below this share of seats free, drop to spread mode
AVAILABLE_MIN = 10       # confirmed free seats before a carriage reads "space"

SPACE, FILLING, FULL, UNKNOWN = "space", "filling", "full", "unknown"


@dataclass(frozen=True)
class CarTile:
    """One carriage, drawn at its own place on the platform.

    `headline` is the authoritative text and the one a screen reader hears.
    `figure`/`unit` are the same thing split for typesetting, and are set only
    when the tile shows a count; the screen sets a count in large numerals and
    a phrase in smaller words, which is why the split is made here rather than
    guessed at by parsing the headline in JavaScript.
    """
    id: str
    zone: str
    position: int            # 0-based, front of the train first
    state: str               # space | filling | full | unknown
    headline: str            # what the tile says in large type
    detail: str              # the qualifying line underneath
    figure: str              # the number, when the tile shows one
    unit: str                # what the number counts
    confirmed_free: int
    unknown_seats: int

    def as_dict(self) -> dict:
        return asdict(self)


def _tile(car: dict, position: int, zone: str, scarce: bool) -> CarTile:
    free = max(0, int(car.get("free", 0) or 0))
    unknown = max(0, int(car.get("unknown", 0) or 0))
    total = int(car.get("total", 0) or 0)

    if unknown:
        # Never imply certainty we do not have. "At least" is the honest form.
        return CarTile(
            id=car["id"], zone=zone, position=position, state=UNKNOWN,
            headline="Some seats not reported",
            detail=(f"At least {free} free, {unknown} of {total} seats unknown"
                    if free else f"{unknown} of {total} seats unknown"),
            figure="", unit="", confirmed_free=free, unknown_seats=unknown)

    if free == 0:
        # "No free seats" and not "full": standing room is not sensed, and a
        # passenger may still legitimately board here.
        return CarTile(car["id"], zone, position, FULL,
                       "No free seats", "Standing room not measured",
                       "", "", 0, 0)

    if scarce:
        # Grading by count is switched off: every carriage with room reads the
        # same, so no one can infer a ranking from the tiles. The detail line
        # is empty because the banner already carries the one instruction, and
        # repeating it under all twelve carriages is noise, not emphasis.
        return CarTile(car["id"], zone, position, SPACE,
                       "Space here", "", "", "", free, 0)

    state = SPACE if free >= AVAILABLE_MIN else FILLING
    return CarTile(car["id"], zone, position, state,
                   f"{free} free",
                   "Seats available" if state == SPACE else "Filling up",
                   str(free), "free", free, 0)


def build_view(snapshot: dict, zones: dict | None = None,
               scarce_fraction: float = SCARCE_FRACTION) -> dict:
    """Turn a model snapshot into the screen's view model.

    `snapshot` is what `DemoModel.snapshot()` already returns. The output
    carries no ordering of its own: carriages are listed front to back, the
    order they stand in on the platform.
    """
    cars = list(snapshot.get("cars", []))
    zones = zones or {}

    total_seats = sum(int(c.get("total", 0) or 0) for c in cars)
    confirmed_free = sum(max(0, int(c.get("free", 0) or 0)) for c in cars)
    unknown_seats = sum(max(0, int(c.get("unknown", 0) or 0)) for c in cars)

    scarce = bool(total_seats) and confirmed_free < scarce_fraction * total_seats

    # The zone is the carriage's physical place on the platform: the model's own
    # `zone` field if it has one, else a caller-supplied map, else the car id.
    tiles = [_tile(car, i,
                   car.get("zone") or zones.get(car["id"]) or car["id"],
                   scarce)
             for i, car in enumerate(cars)]

    if scarce:
        banner = ("Train is busy. Please spread along the platform "
                  "and use all the doors.")
    elif unknown_seats:
        banner = ("Seats shown are the ones we can confirm. "
                  "Wait by the zone nearest you that has space.")
    else:
        banner = "Wait by the zone nearest you that has space."

    return {
        "mode": "spread" if scarce else "counts",
        "banner": banner,
        # Deliberately front-to-back, never sorted by availability.
        "cars": [t.as_dict() for t in tiles],
        "totals": {
            "seats": total_seats,
            "confirmed_free": confirmed_free,
            "unknown": unknown_seats,
            "free_share": round(confirmed_free / total_seats, 3) if total_seats else 0.0,
        },
        "scarce_threshold": scarce_fraction,
    }
