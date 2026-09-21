"""
guidance.py - decides which carriage each waiting passenger should go to.

Input : the carriage messages produced by CarriageController
        (free_min = seats known free, free_max = free_min + seats we can't see)
Output: a status per carriage for the platform display, and a carriage
        for each passenger.

Rules, in order of preference for each passenger:
  1. a carriage with a CONFIRMED free seat (nearest one first)
  2. a carriage with a POSSIBLY free seat (no sensor / sensor fault)
  3. no seats anywhere -> the carriage with the fewest people assigned so far,
     so boarding is spread evenly across doors (this is what cuts dwell time)
Each assignment "uses up" a seat, so two passengers are never sent to the
same single free seat.

Run on its own for a demo:  python guidance.py
"""


def carriage_status(msg):
    if msg["free_min"] > 0:
        return "FREE"
    if msg["free_max"] > 0:
        return "UNKNOWN"
    return "FULL"


def display_line(messages):
    """What the platform screen would show."""
    return " | ".join(f"C{m['car']} {carriage_status(m)}" for m in messages)


def assign_passengers(messages, passenger_positions):
    """
    passenger_positions: for each waiting passenger, the carriage number they
    are standing in front of (1, 2, 3...). Returns a list of
    (position, assigned_carriage, reason).
    """
    sure = {m["car"]: m["free_min"] for m in messages}
    maybe = {m["car"]: m["free_max"] - m["free_min"] for m in messages}
    boarding = {m["car"]: 0 for m in messages}
    result = []

    for pos in passenger_positions:
        def score(car):
            if sure[car] > 0:
                tier = 0
            elif maybe[car] > 0:
                tier = 1
            else:
                tier = 2
            crowd = boarding[car] if tier == 2 else 0
            return (tier, crowd, abs(car - pos))

        car = min(sure, key=score)
        tier = score(car)[0]
        if tier == 0:
            sure[car] -= 1
            reason = "free seat"
        elif tier == 1:
            maybe[car] -= 1
            reason = "seat possibly free (not sensed)"
        else:
            reason = "no seats - least crowded door"
        boarding[car] += 1
        result.append((pos, car, reason))
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
