"""Tests that the platform screen stays a map and never becomes a leaderboard.

The model result these pin down: a ranked list of carriages was the worst of
every design tested, 49% worse than showing nothing, because everyone reading
the screen at the same moment walks to the same doors. So the tests below are
mostly negative - they assert the absence of ranking, of badges, and of any
wording that names a winning carriage.
"""

import math
import unittest

from platform_view import (AVAILABLE_MIN, SCARCE_FRACTION, build_view)

CARS = tuple("ABCDEFGHIJKL")
SEATS_PER_CAR = 108


def snapshot(free_by_car: dict, unknown_by_car: dict | None = None,
             total: int = SEATS_PER_CAR) -> dict:
    unknown_by_car = unknown_by_car or {}
    return {"cars": [{"id": c, "free": free_by_car.get(c, 0),
                      "unknown": unknown_by_car.get(c, 0), "total": total}
                     for c in CARS]}


def tile(view: dict, car: str) -> dict:
    return next(c for c in view["cars"] if c["id"] == car)


def all_text(view: dict) -> str:
    return " ".join([view["banner"]] +
                    [f"{c['headline']} {c['detail']}" for c in view["cars"]]).lower()


class TestNoLeaderboard(unittest.TestCase):
    def test_carriages_are_listed_in_physical_order_never_ranked(self):
        view = build_view(snapshot({"A": 1, "F": 90, "L": 45}))
        self.assertEqual([c["id"] for c in view["cars"]], list(CARS))
        self.assertEqual([c["position"] for c in view["cars"]], list(range(12)))

    def test_order_is_unchanged_by_which_carriage_is_emptiest(self):
        order = [c["id"] for c in build_view(snapshot({"L": 108})) ["cars"]]
        self.assertEqual(order, [c["id"] for c in
                                 build_view(snapshot({"A": 108}))["cars"]],
                         "the layout moved when availability moved")

    def test_no_recommendation_language_anywhere_in_the_view(self):
        view = build_view(snapshot({c: i * 9 for i, c in enumerate(CARS)}))
        text = all_text(view)
        for banned in ("best", "good choice", "recommend", "top ", "#1",
                       "most free", "board here", "choice", "ranked", "emptiest"):
            self.assertNotIn(banned, text, f"leaderboard language present: {banned!r}")

    def test_no_badge_or_rank_fields_are_published(self):
        view = build_view(snapshot({c: i * 9 for i, c in enumerate(CARS)}))
        for banned in ("recommended", "recommendation", "suggestion", "rank",
                       "ranked", "best", "badge"):
            self.assertNotIn(banned, view, f"view exposes a ranking field: {banned!r}")
        for car in view["cars"]:
            for banned in ("rank", "badge", "recommended", "score"):
                self.assertNotIn(banned, car, f"tile exposes {banned!r}")

    def test_the_banner_names_no_carriage(self):
        view = build_view(snapshot({c: i * 9 for i, c in enumerate(CARS)}))
        for car in CARS:
            self.assertNotIn(f"Car {car}", view["banner"])
            self.assertNotIn(f"Zone {car}", view["banner"])

    def test_the_banner_asks_a_local_question_not_a_global_one(self):
        """'nearest you' is the whole design: it splits readers by position."""
        view = build_view(snapshot({c: 50 for c in CARS}))
        self.assertIn("nearest you", view["banner"].lower())


class TestUnknownSeats(unittest.TestCase):
    def test_carriage_with_an_unknown_seat_is_marked_unknown(self):
        view = build_view(snapshot({"C": 30}, unknown_by_car={"C": 4}))
        self.assertEqual(tile(view, "C")["state"], "unknown")

    def test_never_claims_more_than_it_can_prove(self):
        t = tile(build_view(snapshot({"C": 30}, unknown_by_car={"C": 4})), "C")
        self.assertEqual(t["confirmed_free"], 30)
        self.assertIn("At least 30", t["detail"])
        self.assertIn("unknown", t["detail"])

    def test_a_silent_carriage_shows_no_count_at_all(self):
        t = tile(build_view(snapshot({}, unknown_by_car={"C": 108})), "C")
        self.assertEqual(t["state"], "unknown")
        self.assertEqual(t["confirmed_free"], 0)
        self.assertNotIn("At least", t["detail"])

    def test_unknown_outranks_a_healthy_looking_count(self):
        """One dead sensor demotes the tile; it does not round up to 'space'."""
        t = tile(build_view(snapshot({"C": 100}, unknown_by_car={"C": 1})), "C")
        self.assertEqual(t["state"], "unknown")
        self.assertNotEqual(t["headline"], "100 free")

    def test_unknown_seats_are_excluded_from_the_total(self):
        view = build_view(snapshot({"A": 10}, unknown_by_car={"B": 108}))
        self.assertEqual(view["totals"]["confirmed_free"], 10)
        self.assertEqual(view["totals"]["unknown"], 108)

    def test_the_banner_says_the_counts_are_only_what_is_confirmed(self):
        view = build_view(snapshot({c: 50 for c in CARS},
                                   unknown_by_car={"C": 4}))
        self.assertIn("confirm", view["banner"].lower())


class TestScarceFallback(unittest.TestCase):
    def test_counts_shown_when_seats_are_plentiful(self):
        view = build_view(snapshot({c: 50 for c in CARS}))
        self.assertEqual(view["mode"], "counts")
        self.assertIn("50 free", [c["headline"] for c in view["cars"]])

    def test_drops_to_spread_mode_below_the_threshold(self):
        # 12 x 108 = 1296 seats, so 20% is 259.2
        view = build_view(snapshot({c: 20 for c in CARS}))   # 240 free, 18.5%
        self.assertEqual(view["mode"], "spread")
        self.assertIn("spread along the platform", view["banner"].lower())

    def test_spread_mode_stops_grading_by_seat_count(self):
        view = build_view(snapshot({"A": 200, "B": 1, "C": 1}))
        self.assertEqual(view["mode"], "spread")
        with_room = [c for c in view["cars"] if c["state"] != "full"]
        self.assertEqual(len(with_room), 3)
        # Every carriage with room reads identically, so no ranking can be
        # inferred from the tiles even though A holds 200 of the 202 seats.
        self.assertEqual({c["headline"] for c in with_room}, {"Space here"})
        self.assertEqual({c["state"] for c in with_room}, {"space"})

    def test_spread_mode_publishes_no_number_a_passenger_could_compare(self):
        view = build_view(snapshot({"A": 200, "B": 1}))
        for t in view["cars"]:
            self.assertNotIn(str(t["confirmed_free"]), t["headline"] + t["detail"],
                             "a comparable count survived into spread mode")

    def test_threshold_boundary(self):
        seats = len(CARS) * SEATS_PER_CAR
        just_enough = math.ceil(SCARCE_FRACTION * seats)          # 260
        self.assertEqual(build_view(snapshot({"A": just_enough}))["mode"], "counts")
        self.assertEqual(build_view(snapshot({"A": just_enough - 1}))["mode"], "spread")

    def test_empty_train_does_not_divide_by_zero(self):
        view = build_view({"cars": []})
        self.assertEqual(view["mode"], "counts")
        self.assertEqual(view["totals"]["free_share"], 0.0)


class TestTileStates(unittest.TestCase):
    def test_zero_free_does_not_claim_the_carriage_is_full(self):
        t = tile(build_view(snapshot({c: 40 for c in CARS} | {"D": 0})), "D")
        self.assertEqual(t["state"], "full")
        self.assertEqual(t["headline"], "No free seats")
        self.assertIn("standing room not measured", t["detail"].lower())

    def test_filling_up_below_the_available_minimum(self):
        t = tile(build_view(snapshot({c: 40 for c in CARS}
                                     | {"D": AVAILABLE_MIN - 1})), "D")
        self.assertEqual(t["state"], "filling")
        t2 = tile(build_view(snapshot({c: 40 for c in CARS}
                                      | {"D": AVAILABLE_MIN})), "D")
        self.assertEqual(t2["state"], "space")

    def test_every_tile_carries_its_own_zone_and_position(self):
        zones = {c: f"Zone {i + 1}" for i, c in enumerate(CARS)}
        view = build_view(snapshot({c: 40 for c in CARS}), zones=zones)
        for i, t in enumerate(view["cars"]):
            self.assertEqual(t["zone"], f"Zone {i + 1}")
            self.assertEqual(t["position"], i)


if __name__ == "__main__":
    unittest.main(verbosity=2)
