"""Software-only regression tests. No serial device is opened."""

import itertools
import queue
import threading
import time
import unittest

from dashboard import create_app
from dashboard_model import DemoError, DemoModel, EMPTY, OCCUPIED, SEAT_IDS, UNKNOWN
from dashboard_serial import LineBuffer, SerialWorker


def status(a="EMPTY", b="EMPTY"):
    return f"S0 dist= 58.3cm base= 58.4cm noise= 52mV {a}  S1 dist= 27.5cm base= 59.0cm noise= 30mV {b}"


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.model = DemoModel(clock=lambda: self.now)

    def hybrid(self):
        self.model.configure("hybrid", "FAKE")
        generation = self.model.generation
        self.model.transport(generation, True)
        return generation

    def seat(self, seat_id):
        return next(s for c in self.model.snapshot()["cars"] for s in c["seats"] if s["id"] == seat_id)

    def test_initial_example(self):
        s = self.model.snapshot()
        self.assertEqual([c["free"] for c in s["cars"]], [1, 3, 0])
        self.assertEqual([c["status"] for c in s["cars"]], ["limited", "available", "none"])
        self.assertEqual(s["recommended"], "B")
        self.assertEqual(s["unknown"], 0)

    def test_every_simulation_combination(self):
        for states in itertools.product((EMPTY, OCCUPIED), repeat=9):
            for seat_id, state in zip(SEAT_IDS, states):
                self.model.set_seat(seat_id, state)
            result = self.model.snapshot()
            self.assertEqual(result["free"], states.count(EMPTY))
            self.assertEqual(result["unknown"], 0)
            for index, car in enumerate(result["cars"]):
                self.assertEqual(car["free"], states[index * 3:index * 3 + 3].count(EMPTY))

    def test_hybrid_is_two_unknown_seven_simulated(self):
        self.hybrid()
        s = self.model.snapshot()
        self.assertEqual(s["unknown"], 2)
        self.assertEqual(sum(x["editable"] for c in s["cars"] for x in c["seats"]), 7)
        self.assertEqual(s["cars"][1]["free"], 2)  # B1 is NOT assumed free.
        self.assertEqual(s["cars"][1]["status"], "unknown")

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
        self.assertEqual(self.seat("A1")["state"], EMPTY)
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

    def test_no_free_seats_is_not_full_car_claim(self):
        self.model.preset("occupied")
        s = self.model.snapshot()
        self.assertIsNone(s["recommended"])
        self.assertEqual(s["message"], "No free seats currently reported")

    def test_unknown_seats_never_recommended_as_available(self):
        self.hybrid()
        self.model.preset("occupied")
        s = self.model.snapshot()
        self.assertIsNone(s["recommended"])
        self.assertEqual(s["free"], 0)
        self.assertEqual(s["unknown"], 2)

    def test_recommendations_preserve_ties_and_never_reserve(self):
        self.assertEqual(self.model.snapshot()["recommended"], "B")
        self.model.preset("empty")
        for _ in range(5):
            s = self.model.snapshot()
            self.assertEqual(s["recommended"], "B")
            self.assertEqual(s["free"], 9)

    def test_validation(self):
        for mode, port in (("bad", ""), ("hybrid", ""), ("hybrid", "COM5\n")):
            with self.assertRaises(DemoError):
                self.model.configure(mode, port)
        with self.assertRaises(DemoError):
            self.model.set_seat("D1", EMPTY)
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
        self.client.post("/api/seats/A1", json={"state": OCCUPIED})
        other = self.app.test_client()
        self.assertEqual(other.get("/api/state").json["cars"][0]["free"], 0)

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

    def test_bad_input_never_mutates(self):
        for body in ([], None, {}, {"state": True}, {"state": []}, {"state": "bad"}):
            response = self.client.post("/api/seats/A1", json=body)
            self.assertIn(response.status_code, (400, 415))
        self.assertEqual(self.client.get("/api/state").json["free"], 4)

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
            self.assertEqual(model.snapshot()["cars"][1]["free"], 2)
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