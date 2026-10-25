"""Tests that the phone app's dispatcher obeys its design rules.

These are not incidental checks. Each one pins a constraint that the
boarding model showed to be the difference between shortening boarding and
lengthening it, so a regression here is a regression in the result. The
central one is TestCrowdDivides: if consecutive passengers standing in the
same place are sent to the same carriage, the app has become a broadcast and
the mechanism is gone.
"""

import unittest

from dispatcher import Dispatcher, DispatcherError

CARS = tuple("ABCDEFGHIJKL")


def state(free_by_car: dict, unknown_by_car: dict | None = None,
          total: int = 108) -> list[dict]:
    """A per-carriage snapshot in the shape DemoModel.snapshot() produces."""
    unknown_by_car = unknown_by_car or {}
    return [{"id": c, "free": free_by_car.get(c, 0),
             "unknown": unknown_by_car.get(c, 0), "total": total}
            for c in CARS]


class Clock:
    """Hand-wound clock, so expiry is tested without waiting for it."""

    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


class TestCrowdDivides(unittest.TestCase):
    """The point of the dispatcher: passengers at one spot are split up."""

    def test_consecutive_passengers_get_different_carriages(self):
        d = Dispatcher(CARS)
        snap = state({c: 40 for c in CARS})
        got = [d.assign("D", snap).car for _ in range(6)]
        self.assertEqual(len(set(got)), 6, f"crowd not divided: {got}")

    def test_routing_stays_balanced_over_many_requests(self):
        d = Dispatcher(CARS, walk_limit=3)
        snap = state({c: 40 for c in CARS})
        for _ in range(60):
            d.assign("F", snap)
        routed = d.routed()
        reachable = list("CDEFGHI")              # F plus three either side
        counts = [routed[c] for c in reachable]
        self.assertEqual(sum(counts), 60)
        self.assertLessEqual(max(counts) - min(counts), 1,
                             f"load not balanced across the reachable set: {routed}")

    def test_the_fewest_routed_carriage_wins_before_the_emptiest(self):
        """Fewest-routed is the primary key; free seats only break ties."""
        d = Dispatcher(CARS, walk_limit=1)
        snap = state({"C": 90, "D": 20, "E": 20})
        self.assertEqual(d.assign("D", snap).car, "C")   # emptiest, nothing routed
        self.assertNotEqual(d.assign("D", snap).car, "C",
                            "sent a second passenger to the same carriage")

    def test_two_separate_crowds_do_not_converge(self):
        """The failure mode a shared screen has: everyone sent to one place."""
        d = Dispatcher(CARS, walk_limit=3)
        snap = state({c: 5 for c in CARS} | {"H": 90})   # H is the obvious winner
        for _ in range(20):
            d.assign("B", snap)
            d.assign("J", snap)
        routed = d.routed()
        self.assertLess(routed["H"], 20,
                        "the dispatcher funnelled the crowd into one carriage")


class TestWalkingRange(unittest.TestCase):
    def test_never_sends_beyond_the_walk_limit(self):
        d = Dispatcher(CARS, walk_limit=2)
        snap = state({c: 0 for c in CARS} | {"L": 100})
        for _ in range(10):
            a = d.assign("A", snap)
            self.assertLessEqual(abs(a.walk_carriages), 2)
            self.assertIn(a.car, "ABC")

    def test_walk_is_signed_and_correct(self):
        d = Dispatcher(CARS, walk_limit=3)
        snap = state({"A": 50})
        a = d.assign("D", snap)
        self.assertEqual(a.car, "A")
        self.assertEqual(a.walk_carriages, -3)   # negative: towards the front

    def test_a_walk_limit_of_zero_still_answers(self):
        d = Dispatcher(CARS, walk_limit=0)
        a = d.assign("D", state({c: 40 for c in CARS}))
        self.assertEqual(a.car, "D")
        self.assertEqual(a.walk_carriages, 0)


class TestNeverRoutesOnUnknown(unittest.TestCase):
    def test_unknown_seats_are_not_treated_as_free(self):
        d = Dispatcher(CARS, walk_limit=3)
        # B has nothing confirmed, only unknown seats. C has a real seat.
        snap = state({"C": 8}, unknown_by_car={"B": 100})
        a = d.assign("B", snap)
        self.assertEqual(a.car, "C", "routed on the strength of unknown seats")
        self.assertEqual(a.reason, "confirmed free seat")

    def test_falls_back_to_spreading_when_nothing_is_confirmed(self):
        d = Dispatcher(CARS, walk_limit=2)
        snap = state({}, unknown_by_car={c: 108 for c in CARS})
        got = [d.assign("E", snap) for _ in range(5)]
        self.assertTrue(all("spreading" in a.reason for a in got))
        self.assertEqual(len({a.car for a in got}), 5,
                         "should still divide the crowd when seats are unprovable")

    def test_confirmed_free_reported_back_is_the_proven_count(self):
        d = Dispatcher(CARS, walk_limit=0)
        a = d.assign("C", state({"C": 7}, unknown_by_car={"C": 20}))
        self.assertEqual(a.confirmed_free, 7)


class TestIdempotency(unittest.TestCase):
    def test_same_ticket_returns_same_answer_without_double_counting(self):
        d = Dispatcher(CARS)
        snap = state({c: 40 for c in CARS})
        first = d.assign("D", snap, ticket="rider-1")
        again = d.assign("D", snap, ticket="rider-1")
        self.assertEqual(first, again)
        self.assertEqual(sum(d.routed().values()), 1, "a refresh counted twice")

    def test_release_frees_the_slot(self):
        d = Dispatcher(CARS)
        snap = state({c: 40 for c in CARS})
        a = d.assign("D", snap, ticket="rider-1")
        self.assertTrue(d.release("rider-1"))
        self.assertEqual(d.routed()[a.car], 0)
        self.assertFalse(d.release("rider-1"))


class TestExpiryAndReset(unittest.TestCase):
    def test_assignments_expire_so_counts_track_the_waiting_crowd(self):
        clock = Clock()
        d = Dispatcher(CARS, hold_s=60.0, clock=clock)
        snap = state({c: 40 for c in CARS})
        for _ in range(5):
            d.assign("D", snap)
        self.assertEqual(sum(d.routed().values()), 5)
        clock.t = 61.0
        self.assertEqual(sum(d.routed().values()), 0, "stale assignments not released")

    def test_an_expired_ticket_is_answered_afresh(self):
        clock = Clock()
        d = Dispatcher(CARS, hold_s=60.0, clock=clock)
        snap = state({c: 40 for c in CARS})
        first = d.assign("D", snap, ticket="rider-1")
        clock.t = 61.0
        again = d.assign("D", snap, ticket="rider-1")
        self.assertEqual(again.car, first.car)   # nothing else is routed now
        self.assertEqual(sum(d.routed().values()), 1)

    def test_reset_clears_everything_on_departure(self):
        d = Dispatcher(CARS)
        snap = state({c: 40 for c in CARS})
        for _ in range(4):
            d.assign("D", snap)
        d.reset()
        self.assertEqual(sum(d.routed().values()), 0)
        self.assertEqual(d.stats()["live_assignments"], 0)


class TestInputHandling(unittest.TestCase):
    def test_position_accepts_car_zone_or_index(self):
        d = Dispatcher(CARS, zones={c: f"Zone {c}" for c in CARS})
        snap = state({c: 40 for c in CARS})
        self.assertEqual(d.assign("C", snap).zone, "Zone C")
        d.reset()
        self.assertEqual(d.assign("Zone C", snap).car, "C")
        d.reset()
        self.assertEqual(d.assign("3", snap).car, "C")

    def test_unknown_position_is_rejected(self):
        d = Dispatcher(CARS)
        with self.assertRaises(DispatcherError):
            d.assign("Platform 9 3/4", state({"A": 1}))

    def test_negative_or_missing_counts_do_not_crash(self):
        d = Dispatcher(CARS)
        snap = [{"id": "A", "free": -5}, {"id": "B"}, {"id": "ZZ", "free": 99}]
        a = d.assign("A", snap)
        self.assertIn(a.car, CARS)


class TestConcurrency(unittest.TestCase):
    def test_parallel_requests_are_not_double_booked(self):
        """Several phones ask at once; the routed counts must still add up."""
        import threading

        d = Dispatcher(CARS, walk_limit=3)
        snap = state({c: 40 for c in CARS})
        results = []
        lock = threading.Lock()

        def ask():
            a = d.assign("F", snap)
            with lock:
                results.append(a.car)

        threads = [threading.Thread(target=ask) for _ in range(40)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 40)
        self.assertEqual(sum(d.routed().values()), 40)
        counts = [d.routed()[c] for c in "CDEFGHI"]
        self.assertLessEqual(max(counts) - min(counts), 1,
                             "concurrent requests broke the balance")


if __name__ == "__main__":
    unittest.main(verbosity=2)
