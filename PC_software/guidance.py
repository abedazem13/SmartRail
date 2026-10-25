"""
guidance.py - decides which carriage each waiting passenger should go to.

This module used to carry its own routing rule. It now delegates to
`dispatcher.py`, which is the same rule the phone app serves to passengers, so
the console tool, the simulator and the app cannot drift apart and give three
different answers to the same question.

Input : the carriage messages produced by CarriageController
        (free_min = seats known free, free_max = free_min + seats we can't see)
Output: a status per carriage for the platform display, and a carriage
        for each passenger.

The rule, for each passenger, in order:
  1. keep only carriages within walking range of where they are standing;
  2. of those, prefer ones with a CONFIRMED free seat;
  3. among the candidates, take the one FEWEST passengers have been sent to;
  4. break ties on free seats, then walking distance, then carriage number.

Step 3 is the primary key and step 4 only breaks ties. That is what divides a
waiting crowd: the emptiest carriage wins the first passenger and loses the
second, so six people standing together are sent six different ways. Against
the measured boarding model this is worth about 43% of the dwell-time saving,
where the previous nearest-carriage-with-a-seat rule was worth about 13%.

Two deliberate differences from the previous rule:

  * An unsensed seat is no longer a reason to send someone anywhere. The old
    rule preferred a carriage whose sensors had failed over spreading the load,
    which meant guessing. A seat is free only when a sensor says so.
  * Walking range is enforced. The old rule could send a passenger the whole
    length of the train for one confirmed seat, which costs more walking time
    than the seat is worth.

The public names and return shapes are unchanged, so `seat_live.py` and
`seat_sim.py` keep working as they did.

Run on its own for a demo:  python guidance.py
"""

from dispatcher import DEFAULT_WALK_LIMIT, Dispatcher
from platform_view import build_view

# Both of these read as "there is a seat here" on the console's three-state
# display. The platform screen draws the finer distinction; see platform_view.
_FREE_STATES = ("space", "filling")


def _snapshot(messages, seats_per_car=None):
    """Carriage messages in the shape the dispatcher and the screen read.

    `free_max - free_min` is the number of seats no sensor can account for.
    They are carried as `unknown`, never folded into `free`.
    """
    return [{"id": m["car"], "zone": f"C{m['car']}",
             "free": max(0, m["free_min"]),
             "unknown": max(0, m["free_max"] - m["free_min"]),
             "total": seats_per_car or 0}
            for m in messages]


def carriage_status(msg):
    if msg["free_min"] > 0:
        return "FREE"
    if msg["free_max"] > 0:
        return "UNKNOWN"
    return "FULL"


def display_line(messages, seats_per_car=None):
    """What the platform screen would show, in one console line.

    Carriages appear in their physical order along the platform and are never
    sorted by how many seats they have. Pass `seats_per_car` to enable the
    screen's crush-load behaviour: below 20% of the train's seats free, the
    counts stop being graded and the line becomes one instruction to spread
    out. Without it the train's size is unknown and no such claim is made.
    """
    view = build_view({"cars": _snapshot(messages, seats_per_car)})
    if view["mode"] == "spread":
        return "TRAIN BUSY - spread along the platform, use all the doors"
    states = {"space": "FREE", "filling": "FREE",
              "full": "FULL", "unknown": "UNKNOWN"}
    return " | ".join(f"C{car['id']} {states[car['state']]}"
                      for car in view["cars"])


def assign_passengers(messages, passenger_positions,
                      walk_limit=DEFAULT_WALK_LIMIT, dispatcher=None):
    """
    passenger_positions: for each waiting passenger, the carriage number they
    are standing in front of (1, 2, 3...). Returns a list of
    (position, assigned_carriage, reason).

    The passengers in one call are divided between carriages: each assignment
    is remembered while the call runs, so the second passenger standing at a
    given door is not sent where the first one was.

    Pass `dispatcher` to share one running Dispatcher across several calls -
    that is how the phone app keeps dividing a crowd that arrives over several
    minutes. Without it each call starts fresh, which is what the console tool
    and the simulator want.
    """
    cars = tuple(m["car"] for m in messages)
    router = dispatcher or Dispatcher(
        cars, zones={m["car"]: f"C{m['car']}" for m in messages},
        walk_limit=walk_limit)
    state = _snapshot(messages)

    result = []
    for position in passenger_positions:
        assignment = router.assign(position, state)
        reason = ("free seat" if assignment.reason == "confirmed free seat"
                  else "no confirmed seat nearby - least crowded door")
        result.append((position, assignment.car, reason))
    return result


def boarders_per_door(assignments, cars):
    counts = {c: 0 for c in cars}
    for _, car, _ in assignments:
        counts[car] += 1
    return counts


# ------------------------------------------------------------------ demo ---
def _msg(car, free_min, free_max):
    return {"car": car, "free_min": free_min, "free_max": free_max}


def demo():
    scenarios = [
        ("All seats free, 1 passenger at carriage 1",
         [_msg(1, 1, 1), _msg(2, 1, 1), _msg(3, 0, 1)], [1]),
        ("Carriage 1 full, 1 passenger at carriage 1",
         [_msg(1, 0, 0), _msg(2, 1, 1), _msg(3, 0, 1)], [1]),
        ("Carriages 1 and 2 full, carriage 3 has no sensor",
         [_msg(1, 0, 0), _msg(2, 0, 0), _msg(3, 0, 1)], [2]),
        ("Everything full, 6 passengers bunched in front of carriage 2",
         [_msg(1, 0, 0), _msg(2, 0, 0), _msg(3, 0, 0)], [2, 2, 2, 1, 2, 3]),
    ]
    for title, msgs, positions in scenarios:
        print(f"\n=== {title}")
        print(f"Display: {display_line(msgs)}")
        assignments = assign_passengers(msgs, positions)
        for i, (pos, car, reason) in enumerate(assignments, 1):
            move = "stay" if car == pos else f"walk {pos} -> {car}"
            print(f"  passenger {i}: at C{pos} -> board C{car}  ({move}; {reason})")
        cars = [m["car"] for m in msgs]
        guided = boarders_per_door(assignments, cars)
        baseline = boarders_per_door([(p, p, "") for p in positions], cars)
        print(f"  boarders per door  without app: {baseline}  (busiest door: "
              f"{max(baseline.values())})")
        print(f"  boarders per door  with app:    {guided}  (busiest door: "
              f"{max(guided.values())})")


if __name__ == "__main__":
    demo()
