"""Tests that guidance.py is now the dispatcher, and still fits its callers.

Two jobs. One: prove the module routes the way the phone app routes, rather
than keeping its own older rule. Two: prove the names and return shapes that
`seat_live.py` and `seat_sim.py` import have not moved, so rewiring the rule
did not break the console tools.
"""

import unittest

import guidance
from dispatcher import Dispatcher


def msg(car, free_min, free_max=None):
    return {"car": car, "free_min": free_min,
            "free_max": free_min if free_max is None else free_max}


THREE_CARS = [msg(1, 0), msg(2, 0), msg(3, 0)]


class TestItDividesTheCrowd(unittest.TestCase):
    """The behaviour the boarding model measured: the busiest door shrinks."""

    def test_a_bunched_queue_is_spread_across_the_doors(self):
        positions = [2, 2, 2, 1, 2, 3]
        assignments = guidance.assign_passengers(THREE_CARS, positions)
        cars = [m["car"] for m in THREE_CARS]

        unguided = guidance.boarders_per_door([(p, p, "") for p in positions], cars)
        guided = guidance.boarders_per_door(assignments, cars)
        self.assertEqual(max(unguided.values()), 4)
        self.assertEqual(max(guided.values()), 2, f"not spread: {guided}")

    def test_the_least_loaded_carriage_wins_before_the_emptiest(self):
        """Fewest-routed is the primary key; free seats only break ties."""
        messages = [msg(1, 9), msg(2, 1), msg(3, 1)]
        got = [car for _, car, _ in guidance.assign_passengers(messages, [2, 2, 2])]
        self.assertEqual(len(set(got)), 3, f"same carriage reused: {got}")
        self.assertEqual(got[0], 1)          # emptiest takes the first passenger

    def test_walking_range_is_enforced(self):
        messages = [msg(n, 0) for n in range(1, 10)]
        messages[8] = msg(9, 50)             # the only seats are nine cars away
        _, car, _ = guidance.assign_passengers(messages, [1], walk_limit=2)[0]
        self.assertLessEqual(abs(car - 1), 2, "sent the length of the train")


class TestUnknownSeatsAreNotSeats(unittest.TestCase):
    def test_an_unsensed_carriage_is_not_preferred_over_spreading(self):
        """The old rule guessed here. A seat is free only when sensed."""
        messages = [msg(1, 0), msg(2, 0), msg(3, 0, 1)]   # C3: sensor cannot see
        _, car, reason = guidance.assign_passengers(messages, [2])[0]
        self.assertEqual(car, 2)
        self.assertIn("no confirmed seat", reason)

    def test_a_confirmed_seat_still_wins(self):
        messages = [msg(1, 0), msg(2, 1), msg(3, 0, 1)]
        _, car, reason = guidance.assign_passengers(messages, [1])[0]
        self.assertEqual((car, reason), (2, "free seat"))


class TestSharedDispatcher(unittest.TestCase):
    def test_a_passed_dispatcher_keeps_dividing_across_calls(self):
        """How the phone app serves a crowd that arrives over several minutes."""
        router = Dispatcher((1, 2, 3), walk_limit=3)
        got = [guidance.assign_passengers(THREE_CARS, [2], dispatcher=router)[0][1]
               for _ in range(3)]
        self.assertEqual(len(set(got)), 3, f"state not carried between calls: {got}")

    def test_without_one_each_call_starts_fresh(self):
        """What the console tool and the simulator expect: a stable answer."""
        got = [guidance.assign_passengers(THREE_CARS, [2])[0][1] for _ in range(3)]
        self.assertEqual(len(set(got)), 1, f"console output would jitter: {got}")


class TestDisplayLine(unittest.TestCase):
    def test_keeps_the_three_state_console_vocabulary(self):
        line = guidance.display_line([msg(1, 1), msg(2, 0, 1), msg(3, 0)])
        self.assertEqual(line, "C1 FREE | C2 UNKNOWN | C3 FULL")

    def test_carriages_stay_in_physical_order(self):
        line = guidance.display_line([msg(1, 0), msg(2, 99), msg(3, 0)])
        self.assertEqual([part.split()[0] for part in line.split(" | ")],
                         ["C1", "C2", "C3"])

    def test_crush_load_drops_the_per_carriage_counts(self):
        """Below 20% free, the screen stops grading and says one thing."""
        busy = [msg(n, 2) for n in range(1, 13)]          # 24 free of 1296
        line = guidance.display_line(busy, seats_per_car=108)
        self.assertIn("spread along the platform", line.lower())
        self.assertNotIn("C1", line)

    def test_without_a_train_size_no_crush_claim_is_made(self):
        busy = [msg(n, 2) for n in range(1, 13)]
        self.assertIn("C1", guidance.display_line(busy))


class TestTheCallersStillFit(unittest.TestCase):
    """seat_live.py line 245: assign_passengers(msgs, [1])[0][1]"""

    def test_the_shape_seat_live_unpacks(self):
        assignments = guidance.assign_passengers(THREE_CARS, [1])
        self.assertEqual(len(assignments), 1)
        position, car, reason = assignments[0]
        self.assertEqual(position, 1)
        self.assertIn(car, (1, 2, 3))
        self.assertIsInstance(reason, str)

    def test_the_names_seat_live_imports_still_exist(self):
        for name in ("display_line", "assign_passengers", "carriage_status",
                     "boarders_per_door"):
            self.assertTrue(callable(getattr(guidance, name)), name)

    def test_carriage_status_is_unchanged(self):
        self.assertEqual(guidance.carriage_status(msg(1, 3)), "FREE")
        self.assertEqual(guidance.carriage_status(msg(1, 0, 2)), "UNKNOWN")
        self.assertEqual(guidance.carriage_status(msg(1, 0)), "FULL")

    def test_the_demo_still_runs(self):
        import contextlib
        import io

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            guidance.demo()
        printed = out.getvalue()
        self.assertIn("busiest door", printed)
        self.assertIn("passenger 6", printed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
