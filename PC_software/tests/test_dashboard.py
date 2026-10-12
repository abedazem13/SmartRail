"""Software-only regression tests. No serial device is opened."""

import itertools
import queue
import random
import threading
import time
import unittest

from dashboard import create_app
from dashboard_model import (AVAILABLE_FREE_MIN, CARS, DemoError, DemoModel, EMPTY,
                             EXAMPLE_FREE_PER_CAR, NUM_CARS, OCCUPIED, RECOMMEND_CARS,
                             SEAT_IDS, SEATS_PER_CAR, SENSOR_MAP, STOP_ANIMATION_S,
                             TOTAL_SEATS, UNKNOWN)

EXAMPLE_FREE_TOTAL = sum(EXAMPLE_FREE_PER_CAR)
from dashboard_serial import LineBuffer, SerialWorker


def status(a="EMPTY", b="EMPTY"):
    return f"S0 dist= 58.3cm base= 58.4cm noise= 52mV {a}  S1 dist= 27.5cm base= 59.0cm noise= 30mV {b}"


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.model = DemoModel(clock=lambda: self.now, rng=random.Random(20261012))

    def hybrid(self):
        self.model.configure("hybrid", "FAKE")
        generation = self.model.generation
        self.model.transport(generation, True)
        return generation

    def seat(self, seat_id):
        return self.model.seat_view(seat_id)

    def test_train_size_and_initial_example(self):
        s = self.model.snapshot()
        self.assertEqual((s["num_cars"], s["seats_per_car"], s["total"]), (12, 108, 1296))
        self.assertEqual([c["id"] for c in s["cars"]], list(CARS))
        self.assertEqual([len(c["states"]) for c in s["cars"]], [SEATS_PER_CAR] * NUM_CARS)
        self.assertEqual([c["free"] for c in s["cars"]], list(EXAMPLE_FREE_PER_CAR))
        self.assertEqual(s["free"], EXAMPLE_FREE_TOTAL)
        self.assertEqual(s["occupied"], TOTAL_SEATS - EXAMPLE_FREE_TOTAL)
        self.assertEqual(s["station"], 1)
        self.assertEqual(s["unknown"], 0)
        self.assertEqual(s["real_seats"], sorted(SENSOR_MAP))
        # The three emptiest cars in the example scenario: L=72, J=60, E=48.
        self.assertEqual(s["recommended"], ["L", "J", "E"])
        self.assertIn("Car L (72 free)", s["message"])
        for car, free in zip(s["cars"], EXAMPLE_FREE_PER_CAR):
            expected = ("full" if free == 0 else "available"
                        if free >= AVAILABLE_FREE_MIN else "filling")
            self.assertEqual(car["status"], expected)
            self.assertEqual(car["occupied"] + car["free"], SEATS_PER_CAR)

    def test_car_status_thresholds(self):
        self.model.preset("occupied")
        self.assertEqual(self.model.snapshot()["cars"][0]["status"], "full")
        # One free seat: about to be full, orange, and still not recommended last.
        self.model.set_seat("A5", EMPTY)
        car = self.model.snapshot()["cars"][0]
        self.assertEqual((car["status"], car["free"]), ("filling", 1))
        for number in range(6, 6 + AVAILABLE_FREE_MIN - 1):
            self.model.set_seat(f"A{number}", EMPTY)
        car = self.model.snapshot()["cars"][0]
        self.assertEqual((car["status"], car["free"]), ("available", AVAILABLE_FREE_MIN))

    def test_a_car_with_unknown_seats_is_never_called_full(self):
        g = self.hybrid()
        self.model.preset("occupied")
        self.model.feed(g, status(OCCUPIED, OCCUPIED))
        self.now += 3  # sensor data goes stale -> unknown
        car = self.model.snapshot()["cars"][0]
        self.assertEqual(car["status"], "unknown")
        self.assertEqual(car["free"], 0)

    def test_several_cars_recommended_in_order(self):
        self.model.preset("occupied")
        for seat_id, count in (("C", 5), ("F", 9), ("J", 2), ("A", 7)):
            for number in range(1, count + 1):
                self.model.set_seat(f"{seat_id}{number}", EMPTY)
        s = self.model.snapshot()
        self.assertEqual(len(s["recommended"]), RECOMMEND_CARS)
        self.assertEqual(s["recommended"], ["F", "A", "C"])  # 9, 7, 5 free
        self.assertNotIn("J", s["recommended"])  # only 2 free, ranked fourth

    def test_recommendation_ignores_full_cars_and_ties_alphabetically(self):
        self.model.preset("occupied")
        for car in ("D", "B", "K"):
            self.model.set_seat(f"{car}1", EMPTY)  # a three-way tie on 1 free
        s = self.model.snapshot()
        self.assertEqual(s["recommended"], ["B", "D", "K"])
        for car in s["cars"]:
            if car["id"] not in ("B", "D", "K"):
                self.assertEqual(car["status"], "full")

    def finish_stop(self):
        self.now += STOP_ANIMATION_S + 0.01
        return self.model.snapshot()

    def test_next_stop_moves_passengers_within_bounds(self):
        self.model.preset("example")
        for expected_station in range(2, 12):
            before = self.model.snapshot()
            result = self.model.next_stop()
            after = self.finish_stop()
            self.assertEqual(result["station"], expected_station)
            self.assertEqual(after["station"], expected_station)
            # Never frees more than were occupied, never fills more than are free.
            self.assertLessEqual(result["alighted"], before["occupied"])
            self.assertLessEqual(result["boarded"], before["free"] + result["alighted"])
            self.assertEqual(after["free"], before["free"] + result["alighted"] - result["boarded"])
            self.assertEqual(after["free"] + after["occupied"], TOTAL_SEATS)
            self.assertGreaterEqual(after["free"], 0)
            self.assertGreaterEqual(after["occupied"], 0)

    def test_next_stop_spreads_across_cars(self):
        self.model.preset("example")
        before = [c["free"] for c in self.model.snapshot()["cars"]]
        for _ in range(3):
            self.model.next_stop()
            self.finish_stop()
        after = [c["free"] for c in self.model.snapshot()["cars"]]
        self.assertGreater(sum(1 for a, b in zip(before, after) if a != b), 1)

    def test_next_stop_cannot_change_real_seats(self):
        g = self.hybrid()
        self.model.feed(g, status(OCCUPIED, EMPTY))
        for _ in range(5):
            self.model.next_stop()
            self.finish_stop()
            self.model.feed(g, status(OCCUPIED, EMPTY))  # the board keeps reporting
            self.assertEqual(self.seat("A1")["state"], OCCUPIED)
            self.assertEqual(self.seat("B1")["state"], EMPTY)
            self.assertFalse(self.seat("A1")["editable"])

    def test_empty_and_full_trains_cannot_overflow(self):
        for preset, free, occupied in (("empty", TOTAL_SEATS, 0), ("occupied", 0, TOTAL_SEATS)):
            self.model.preset(preset)
            self.assertEqual(self.model.snapshot()["free"], free)
            self.assertEqual(self.model.snapshot()["occupied"], occupied)
            result = self.model.next_stop()
            s = self.finish_stop()
            self.assertEqual(s["free"] + s["occupied"], TOTAL_SEATS)
            if preset == "empty":
                self.assertEqual(result["alighted"], 0)  # nobody to get off
                self.assertLessEqual(result["boarded"], TOTAL_SEATS)
            else:
                # A full train: people get off first, so only those seats fill.
                self.assertGreater(result["alighted"], 0)
                self.assertLessEqual(result["boarded"], result["alighted"])

    def test_preset_resets_the_station_counter(self):
        self.model.next_stop()
        self.finish_stop()
        self.model.next_stop()
        self.finish_stop()
        self.assertEqual(self.model.snapshot()["station"], 3)
        self.model.preset("example")
        self.assertEqual(self.model.snapshot()["station"], 1)

    def test_a_stop_is_applied_gradually_not_in_one_jump(self):
        self.model.preset("example")
        start = self.model.snapshot()["free"]
        result = self.model.next_stop()
        self.assertTrue(self.model.snapshot()["boarding"])
        self.assertEqual(self.model.snapshot()["free"], start)  # nothing yet

        # First half: passengers leave, so free seats rise above the start.
        self.now += STOP_ANIMATION_S / 2
        midpoint = self.model.snapshot()
        self.assertGreater(midpoint["free"], start)
        self.assertEqual(midpoint["free"], start + result["alighted"])

        # Second half: others board, ending at the stop's net result.
        end = self.finish_stop()
        self.assertEqual(end["free"], start + result["alighted"] - result["boarded"])
        self.assertFalse(end["boarding"])
        self.assertEqual(end["free"] + end["occupied"], TOTAL_SEATS)

    def test_a_click_overrides_a_stop_in_progress(self):
        self.model.preset("occupied")
        self.model.next_stop()  # schedules a batch of seats to empty
        self.model.set_seat("A7", OCCUPIED)
        self.finish_stop()
        self.assertEqual(self.seat("A7")["state"], OCCUPIED)

    def test_presets_and_mode_changes_cancel_a_stop_in_progress(self):
        self.model.next_stop()
        self.model.preset("empty")
        self.finish_stop()
        self.assertEqual(self.model.snapshot()["free"], TOTAL_SEATS)
        self.model.next_stop()
        self.model.configure("hybrid", "FAKE")
        self.model.configure("simulation")
        before = self.model.snapshot()["free"]
        self.finish_stop()
        self.assertEqual(self.model.snapshot()["free"], before)

    def test_automatic_stops_run_on_their_interval(self):
        self.assertEqual(self.model.snapshot()["auto_interval"], 0)
        self.model.configure_auto(10)
        self.assertEqual(self.model.snapshot()["auto_interval"], 10)
        self.assertEqual(self.model.snapshot()["station"], 1)  # not yet due
        self.now += 10.1
        self.assertEqual(self.model.snapshot()["station"], 2)
        self.now += 5
        self.assertEqual(self.model.snapshot()["station"], 2)  # no double stop
        self.now += 5.1
        self.assertEqual(self.model.snapshot()["station"], 3)
        self.model.configure_auto(0)
        self.now += 100
        self.assertEqual(self.model.snapshot()["station"], 3)  # stopped

    def test_automatic_stops_never_touch_real_seats(self):
        g = self.hybrid()
        self.model.feed(g, status(OCCUPIED, EMPTY))
        self.model.configure_auto(3)
        for _ in range(4):
            self.now += 3.1
            self.model.snapshot()
            self.model.feed(g, status(OCCUPIED, EMPTY))
        self.assertGreater(self.model.snapshot()["station"], 1)
        self.assertEqual(self.seat("A1")["state"], OCCUPIED)
        self.assertEqual(self.seat("B1")["state"], EMPTY)

    def test_auto_interval_validation(self):
        for bad in ("abc", None, 1, 0.5, 1000):
            with self.assertRaises(DemoError):
                self.model.configure_auto(bad)
        self.assertEqual(self.model.snapshot()["auto_interval"], 0)

    def test_every_simulation_combination_of_a_sample(self):
        # 2**1296 combinations cannot be enumerated; exhaust nine seats spread
        # over three cars while the rest of the train stays empty.
        sample = ("A1", "A2", "A108", "B1", "B54", "B108", "L1", "L2", "L108")
        for states in itertools.product((EMPTY, OCCUPIED), repeat=len(sample)):
            self.model.preset("empty")
            for seat_id, state in zip(sample, states):
                self.model.set_seat(seat_id, state)
            result = self.model.snapshot()
            self.assertEqual(result["free"], TOTAL_SEATS - states.count(OCCUPIED))
            self.assertEqual(result["unknown"], 0)
            for car in result["cars"]:
                occupied = sum(1 for seat_id, state in zip(sample, states)
                               if seat_id[0] == car["id"] and state == OCCUPIED)
                self.assertEqual(car["free"], SEATS_PER_CAR - occupied)
                self.assertEqual(car["states"].count("O"), occupied)

    def test_hybrid_is_two_real_seats_and_the_rest_simulated(self):
        self.hybrid()
        s = self.model.snapshot()
        self.assertEqual(s["unknown"], 2)
        self.assertEqual(sum(len(c["seats"]) for c in s["cars"]), 2)
        self.assertEqual(sum(c["states"].count("U") for c in s["cars"]), 2)
        for seat_id in SENSOR_MAP:
            self.assertFalse(self.seat(seat_id)["editable"])
        self.assertTrue(self.seat("A2")["editable"])
        # An unknown seat is never counted as free.
        for car in s["cars"][:2]:
            self.assertEqual(car["status"], "unknown")
            self.assertEqual(car["free"] + car["occupied"] + car["unknown"], SEATS_PER_CAR)
        self.assertEqual(sum(1 for seat_id in SEAT_IDS if seat_id not in SENSOR_MAP),
                         TOTAL_SEATS - 2)

    def test_real_seats_read_only(self):
        self.hybrid()
        for seat_id in ("A1", "B1"):
            with self.assertRaises(DemoError):
                self.model.set_seat(seat_id, EMPTY)

    def test_presets_never_override_real_states(self):
        g = self.hybrid()
        self.model.feed(g, status(OCCUPIED, EMPTY))
        for preset in ("example", "empty", "occupied"):
            self.model.preset(preset)
            self.assertEqual(self.seat("A1")["state"], OCCUPIED)
            self.assertEqual(self.seat("B1")["state"], EMPTY)

    def test_status_and_event_mapping(self):
        g = self.hybrid()
        self.model.feed(g, status())
        self.model.feed(g, "EVENT seat=0 state=OCCUPIED dist=23.6cm")
        self.assertEqual(self.seat("A1")["state"], OCCUPIED)
        self.assertEqual(self.seat("B1")["state"], EMPTY)
        self.assertEqual(self.seat("A1")["distance_cm"], 23.6)
        self.assertEqual(self.model.snapshot()["connection"]["status"], "live")

    def test_pending_and_raw_debug_do_not_flip_state(self):
        g = self.hybrid()
        self.model.feed(g, "S0 dist= 23.5cm base= 58.4cm noise= 52mV EMPTY   ? (raw=850mV) S1 dist= 58.0cm base= 59.0cm noise= 12mV EMPTY (raw=550mV)")
        self.assertEqual(self.seat("A1")["state"], EMPTY)
        self.assertTrue(self.seat("A1")["pending"])

    def test_per_seat_stale_data_and_recovery(self):
        g = self.hybrid()
        self.model.feed(g, status())
        self.now += 2.01
        self.model.feed(g, "EVENT seat=1 state=OCCUPIED dist=24.0cm")
        self.assertEqual(self.seat("A1")["state"], UNKNOWN)
        self.assertEqual(self.seat("B1")["state"], OCCUPIED)
        self.assertEqual(self.model.snapshot()["connection"]["status"], "waiting")
        self.model.feed(g, status())
        self.assertEqual(self.seat("A1")["state"], EMPTY)

    def test_disconnect_and_reconnect_clear_old_values(self):
        g = self.hybrid()
        self.model.feed(g, status())
        self.model.transport(g, False, "Unplugged")
        self.assertEqual(self.model.snapshot()["unknown"], 2)
        self.assertIsNone(self.seat("A1")["distance_cm"])
        self.model.transport(g, True)
        self.assertEqual(self.model.snapshot()["unknown"], 2)

    def test_calibration_unknown_until_new_status(self):
        g = self.hybrid()
        self.model.feed(g, status())
        self.model.feed(g, "--- CALIBRATION: keep all seats EMPTY. starting in 3 s ---")
        self.model.feed(g, "CAL seat=0 baseline=58.4cm mv=566 noise=38mV")
        self.assertEqual(self.model.snapshot()["unknown"], 2)
        self.model.feed(g, "CAL seat=1 baseline=59.4cm mv=566 noise=38mV")
        self.model.feed(g, "--- calibration done ---")
        self.assertEqual(self.model.snapshot()["unknown"], 2)
        self.model.feed(g, status())
        self.assertEqual(self.model.snapshot()["unknown"], 0)

    def test_partial_calibration_connection_and_reboot(self):
        g = self.hybrid()
        self.model.feed(g, status())
        self.model.feed(g, "CAL seat=0 baseline=58.4cm mv=566 noise=38mV")
        self.assertEqual(self.model.snapshot()["unknown"], 2)
        self.model.feed(g, "SmartRail seat occupancy - GP2Y0A21YK0F")
        self.assertEqual(self.model.snapshot()["connection"]["status"], "calibrating")

    def test_old_mode_generation_cannot_update_new_mode(self):
        g = self.hybrid()
        self.model.configure("simulation")
        self.model.feed(g, status(OCCUPIED, OCCUPIED))
        self.assertFalse(self.model.transport(g, False, "late disconnect"))
        # Back in simulation, A1 shows its simulated state, not the late feed.
        self.assertEqual(self.seat("A1")["source"], "simulated")
        self.assertEqual(self.seat("A1")["state"], self.model.simulated["A1"])
        self.model.configure("hybrid", "OTHER")
        self.model.feed(g, status())
        self.assertEqual(self.model.snapshot()["unknown"], 2)

    def test_malformed_and_unknown_sensor_lines_do_not_refresh(self):
        g = self.hybrid()
        self.model.feed(g, status())
        self.now += 3
        self.model.feed(g, "EVENT seat=0 state=EMPTY dist=..cm")
        self.model.feed(g, "EVENT seat=9 state=EMPTY dist=23.0cm")
        self.model.feed(g, "random noise")
        self.assertEqual(self.model.snapshot()["unknown"], 2)

    def test_warnings_remain_visible_after_status(self):
        g = self.hybrid()
        self.model.feed(g, "  WARN noise too high: check bypass capacitor and wiring")
        self.model.feed(g, status())
        self.assertEqual(len(self.model.snapshot()["warnings"]), 1)
        self.model.configure("simulation")
        self.assertEqual(self.model.snapshot()["warnings"], [])

    def test_no_free_seats_reports_no_seats_and_suggests_nothing(self):
        self.model.preset("occupied")
        s = self.model.snapshot()
        self.assertEqual(s["recommended"], [])
        self.assertEqual(s["message"], "No free seats currently reported")

    def test_unknown_seats_never_recommended_as_available(self):
        self.hybrid()
        self.model.preset("occupied")
        s = self.model.snapshot()
        self.assertEqual(s["recommended"], [])
        self.assertEqual(s["free"], 0)
        self.assertEqual(s["unknown"], 2)

    def test_recommendations_are_stable_and_never_reserve(self):
        self.assertEqual(self.model.snapshot()["recommended"], ["L", "J", "E"])
        self.model.preset("empty")  # every car ties: first three alphabetically
        for _ in range(5):
            s = self.model.snapshot()
            self.assertEqual(s["recommended"], ["A", "B", "C"])
            self.assertEqual(s["free"], TOTAL_SEATS)  # suggesting reserves nothing

    def test_validation(self):
        for mode, port in (("bad", ""), ("hybrid", ""), ("hybrid", "COM5\n")):
            with self.assertRaises(DemoError):
                self.model.configure(mode, port)
        for unknown_seat in ("Z1", "A109", "A0", "A", "1A"):
            with self.assertRaises(DemoError):
                self.model.set_seat(unknown_seat, EMPTY)
        with self.assertRaises(DemoError):
            self.model.set_seat("A1", UNKNOWN)
        with self.assertRaises(DemoError):
            self.model.preset("bad")


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.model = DemoModel()
        self.app = create_app(self.model)
        self.client = self.app.test_client()

    def test_pages_and_static_files(self):
        for route in ("/", "/controls", "/assets/app.js", "/assets/style.css"):
            with self.client.get(route) as response:
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_independent_clients_share_state(self):
        self.client.post("/api/seats/A1", json={"state": EMPTY})
        other = self.app.test_client()
        self.assertEqual(other.get("/api/state").json["cars"][0]["free"],
                         EXAMPLE_FREE_PER_CAR[0] + 1)

    def test_real_seat_write_rejected_by_server(self):
        self.client.post("/api/mode", json={"mode": "hybrid", "port": "FAKE"})
        response = self.client.post("/api/seats/A1", json={"state": EMPTY})
        self.assertEqual(response.status_code, 400)
        self.assertIn("read-only", response.json["error"])

    def test_cross_origin_control_blocked(self):
        response = self.client.post("/api/preset", json={"name": "empty"}, headers={"Origin": "https://evil.example"})
        self.assertEqual(response.status_code, 403)
        response = self.client.post("/api/preset", json={"name": "empty"}, headers={"Sec-Fetch-Site": "cross-site"})
        self.assertEqual(response.status_code, 403)

    def test_same_origin_control_accepted(self):
        response = self.client.post("/api/preset", json={"name": "empty"}, headers={"Origin": "http://localhost"})
        self.assertEqual(response.status_code, 200)

    def test_foreign_host_blocked(self):
        self.assertEqual(self.client.get("/api/state", headers={"Host": "evil.example"}).status_code, 400)

    def test_network_address_is_served_only_when_configured(self):
        phone = {"REMOTE_ADDR": "192.168.1.50"}
        lan = {"Host": "10.0.0.14:8765"}
        # Default: the laptop address only, so a phone request is refused.
        self.assertEqual(self.client.get("/", headers=lan, environ_base=phone).status_code, 400)
        # With --host the machine network address is trusted for viewing.
        shared = create_app(self.model, extra_hosts=("10.0.0.14",)).test_client()
        self.assertEqual(shared.get("/", headers=lan, environ_base=phone).status_code, 200)
        self.assertEqual(shared.get("/api/state", headers=lan, environ_base=phone).status_code, 200)
        # Controlling it from the phone is still refused, and so is any other host.
        self.assertEqual(shared.get("/controls", headers=lan, environ_base=phone).status_code, 403)
        self.assertEqual(shared.post("/api/next_stop", json={}, headers=lan,
                                     environ_base=phone).status_code, 403)
        self.assertEqual(shared.get("/", headers={"Host": "evil.example"}).status_code, 400)

    def test_bad_input_never_mutates(self):
        for body in ([], None, {}, {"state": True}, {"state": []}, {"state": "bad"}):
            response = self.client.post("/api/seats/A1", json=body)
            self.assertIn(response.status_code, (400, 415))
        self.assertEqual(self.client.get("/api/state").json["free"], EXAMPLE_FREE_TOTAL)

    def test_next_stop_endpoint(self):
        before = self.client.get("/api/state").json
        response = self.client.post("/api/next_stop", json={})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["station"], before["station"] + 1)
        self.assertEqual(response.json["free"] + response.json["occupied"], TOTAL_SEATS)

    def test_auto_endpoint(self):
        self.assertEqual(self.client.post("/api/auto", json={"interval": "10"}).status_code, 200)
        self.assertEqual(self.client.get("/api/state").json["auto_interval"], 10)
        self.assertEqual(self.client.post("/api/auto", json={"interval": "0"}).status_code, 200)
        self.assertEqual(self.client.get("/api/state").json["auto_interval"], 0)
        for bad in ({"interval": "9999"}, {"interval": "x"}, {}, {"interval": 10}):
            self.assertIn(self.client.post("/api/auto", json=bad).status_code, (400, 415))
        self.assertEqual(self.client.get("/api/state").json["auto_interval"], 0)

    def test_remote_device_can_watch_but_not_control(self):
        phone = {"REMOTE_ADDR": "192.168.1.50"}
        # The passenger display and the data it needs are readable.
        for route in ("/", "/api/state", "/assets/app.js", "/assets/style.css"):
            self.assertEqual(self.client.get(route, environ_base=phone).status_code, 200)
        # Anything that changes the demo, or lists this machine ports, is not.
        self.assertEqual(self.client.get("/controls", environ_base=phone).status_code, 403)
        self.assertEqual(self.client.get("/api/ports", environ_base=phone).status_code, 403)
        for route, body in (("/api/next_stop", {}), ("/api/preset", {"name": "empty"}),
                            ("/api/seats/A2", {"state": EMPTY}),
                            ("/api/auto", {"interval": "10"}),
                            ("/api/mode", {"mode": "hybrid", "port": "COM9"})):
            response = self.client.post(route, json=body, environ_base=phone)
            self.assertEqual(response.status_code, 403)
            self.assertIn("only on the computer", response.json["error"])
        # Nothing moved, and the controls still work on this machine.
        self.assertEqual(self.client.get("/api/state").json["free"], EXAMPLE_FREE_TOTAL)
        self.assertEqual(self.client.get("/controls").status_code, 200)
        self.assertEqual(self.client.post("/api/next_stop", json={}).status_code, 200)

    def test_next_stop_rejected_cross_origin(self):
        response = self.client.post("/api/next_stop", json={},
                                    headers={"Origin": "https://evil.example"})
        self.assertEqual(response.status_code, 403)

    def test_size_limit_and_non_json(self):
        self.assertEqual(self.client.post("/api/preset", data="name=empty").status_code, 415)
        self.assertEqual(self.client.post("/api/preset", json={"name": "x" * 5000}).status_code, 413)


class FramingTests(unittest.TestCase):
    def test_split_crlf_multiple_lines_and_encoding(self):
        frames = LineBuffer()
        self.assertEqual(frames.feed(b"abc"), [])
        self.assertEqual(frames.feed(b"def\r\nsecond\n\xff\n"), ["abcdef", "second", "\ufffd"])

    def test_oversized_line_discarded_with_tail(self):
        frames = LineBuffer(limit=8)
        self.assertEqual(frames.feed(b"a" * 10), [])
        self.assertEqual(frames.feed(b"EMPTY\ngood\n"), ["good"])


class FakeSerial:
    def __init__(self):
        self.incoming = queue.Queue()
        self.closed = threading.Event()

    @property
    def in_waiting(self):
        return 4096

    def read(self, size):
        try:
            value = self.incoming.get(timeout=0.03)
        except queue.Empty:
            return b""
        if isinstance(value, Exception):
            raise value
        return value

    def close(self):
        self.closed.set()


class SerialWorkerTests(unittest.TestCase):
    def wait_for(self, predicate, timeout=3):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return
            threading.Event().wait(0.01)
        self.fail("Timed out waiting for fake serial worker")

    def test_fragmentation_disconnect_retry_and_mode_switch(self):
        model = DemoModel()
        model.configure("hybrid", "FAKE")
        first, second = FakeSerial(), FakeSerial()
        handles = iter([first, second])
        worker = SerialWorker(model, factory=lambda *args, **kwargs: next(handles), retry_s=0.1)
        worker.start()
        try:
            first.incoming.put(b"S0 dist= 58.3cm base= 58.4cm noise= 52mV EMP")
            first.incoming.put(b"TY S1 dist= 24.0cm base= 59.0cm noise= 30mV OCCUPIED\n")
            self.wait_for(lambda: model.snapshot()["unknown"] == 0)
            self.assertEqual(model.seat_view("B1")["state"], OCCUPIED)
            first.incoming.put(OSError("fake USB unplug"))
            self.wait_for(lambda: first.closed.is_set())
            self.assertEqual(model.snapshot()["unknown"], 2)
            second.incoming.put((status() + "\n").encode())
            self.wait_for(lambda: model.snapshot()["unknown"] == 0)
            model.configure("simulation")
            self.wait_for(lambda: second.closed.is_set())
            self.assertEqual(model.snapshot()["mode"], "simulation")
        finally:
            worker.stop()
        self.assertFalse(worker.is_alive())

    def test_initial_port_failure_retries_without_simulation_fallback(self):
        model = DemoModel()
        model.configure("hybrid", "FAKE")
        calls = []

        def fail(*args, **kwargs):
            calls.append(1)
            raise OSError("fake port missing")

        worker = SerialWorker(model, factory=fail, retry_s=0.02)
        worker.start()
        try:
            self.wait_for(lambda: len(calls) >= 2)
            self.assertEqual(model.snapshot()["unknown"], 2)
            self.assertEqual(model.snapshot()["mode"], "hybrid")
        finally:
            worker.stop()


if __name__ == "__main__":
    unittest.main()