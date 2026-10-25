"""Tests the two interfaces end to end: HTTP, and the files that are served.

The constraint tests in test_platform_view.py prove the server never publishes
a ranking. These prove the browser never reintroduces one - the screen's own
markup and script are searched for the language and the sorting a later change
would most plausibly add back.
"""

import re
import sys
import unittest
from pathlib import Path


def _team_pc_software():
    """Locate the team's PC_software, which holds dashboard_model.py.

    These files can sit either merged into PC_software or in a folder of their
    own beside it, such as report_new_app/PC_software. Both layouts are checked
    so the suite runs either way without being edited.
    """
    here = Path(__file__).resolve()
    for candidate in (here.parent.parent,                                  # merged
                      here.parent.parent.parent.parent / "PC_software"):   # alongside
        if (candidate / "dashboard_model.py").exists():
            return candidate
    return None


TEAM = _team_pc_software()
if TEAM and str(TEAM) not in sys.path:
    sys.path.insert(1, str(TEAM))

from flask import Flask

from dashboard_model import CARS, DemoModel
from passenger_routes import WEB, PassengerService, register_passenger_routes


def app_with_model():
    model = DemoModel()
    app = Flask(__name__)
    app.config.update(MAX_CONTENT_LENGTH=4096, TESTING=True)
    service = register_passenger_routes(app, model)
    return app, model, service


class TestPlatformEndpoint(unittest.TestCase):
    def setUp(self):
        self.app, self.model, self.service = app_with_model()
        self.client = self.app.test_client()

    def get(self, url) -> int:
        """Status code only. Closing the response keeps the file handle tidy,
        because these routes stream a file from disk."""
        response = self.client.get(url)
        try:
            return response.status_code
        finally:
            response.close()

    def test_serves_both_pages_and_their_assets(self):
        self.assertEqual(self.get("/platform"), 200)
        self.assertEqual(self.get("/app"), 200)
        for asset in ("platform.css", "platform.js", "phone.css", "phone.js"):
            self.assertEqual(self.get(f"/passenger/{asset}"), 200)

    def test_refuses_a_path_it_does_not_ship(self):
        self.assertEqual(self.get("/passenger/dashboard.py"), 404)
        self.assertNotEqual(self.get("/passenger/../dashboard.py"), 200)

    def test_state_is_in_platform_order_with_no_ranking(self):
        view = self.client.get("/api/platform").get_json()
        self.assertEqual([c["id"] for c in view["cars"]], list(CARS))
        self.assertNotIn("recommended", view)
        self.assertNotIn("message", view)      # the old leaderboard sentence

    def test_the_dashboards_ranking_does_not_leak_into_the_screen(self):
        """The existing /api/state does rank cars. This view must not carry it."""
        dashboard_state = self.model.snapshot()
        self.assertIn("recommended", dashboard_state)      # the old behaviour
        view = self.client.get("/api/platform").get_json()
        text = str(view).lower()
        for banned in ("recommend", "most confirmed free", "best"):
            self.assertNotIn(banned, text)


class TestAssignEndpoint(unittest.TestCase):
    def setUp(self):
        self.app, self.model, self.service = app_with_model()
        self.client = self.app.test_client()

    def post(self, url, payload):
        return self.client.post(url, json=payload)

    def test_consecutive_requests_from_one_zone_get_different_carriages(self):
        got = []
        for _ in range(5):
            response = self.post("/api/assign", {"position": "F"})
            self.assertEqual(response.status_code, 200)
            got.append(response.get_json()["car"])
        self.assertEqual(len(set(got)), 5, f"crowd not divided over HTTP: {got}")

    def test_the_same_ticket_is_answered_identically(self):
        first = self.post("/api/assign", {"position": "F", "ticket": "abc"}).get_json()
        again = self.post("/api/assign", {"position": "F", "ticket": "abc"}).get_json()
        self.assertEqual(first["car"], again["car"])
        self.assertEqual(sum(self.service.dispatcher.routed().values()), 1)

    def test_walk_is_described_in_words_the_passenger_can_act_on(self):
        body = self.post("/api/assign", {"position": "A"}).get_json()
        self.assertRegex(body["walk"],
                         r"already at the right zone|carriages? towards the (front|back)")

    def test_release_returns_the_slot(self):
        body = self.post("/api/assign", {"position": "F", "ticket": "abc"}).get_json()
        out = self.post("/api/release", {"ticket": "abc"}).get_json()
        self.assertTrue(out["released"])
        self.assertEqual(out["routed"][body["car"]], 0)

    def test_bad_requests_are_rejected_not_guessed_at(self):
        self.assertEqual(self.post("/api/assign", {}).status_code, 400)
        self.assertEqual(self.post("/api/assign", {"position": 7}).status_code, 400)
        self.assertEqual(self.post("/api/assign", {"position": "Zone 99"}).status_code, 400)
        self.assertEqual(self.post("/api/assign",
                                   {"position": "A", "ticket": "x" * 65}).status_code, 400)
        self.assertEqual(self.post("/api/release", {}).status_code, 400)

    def test_a_response_never_lists_other_carriages(self):
        """The app must not be able to build a comparison from its own reply."""
        body = self.post("/api/assign", {"position": "F"}).get_json()
        self.assertEqual([k for k in body if isinstance(body[k], (list, dict))], [])
        self.assertNotIn("cars", body)


class TestServiceResetsWithTheTrain(unittest.TestCase):
    def test_a_stop_clears_the_routing_counts(self):
        app, model, service = app_with_model()
        client = app.test_client()
        for _ in range(4):
            client.post("/api/assign", json={"position": "F"})
        self.assertEqual(sum(service.dispatcher.routed().values()), 4)

        model.next_stop()                       # the train departs and arrives again
        client.get("/api/platform")             # the next poll notices
        self.assertEqual(sum(service.dispatcher.routed().values()), 0,
                         "the last train's crowd was still being divided")


class TestShippedFilesHoldTheLine(unittest.TestCase):
    """Greps the delivered UI. A ranking is most likely to come back here."""

    files = {name: (WEB / name).read_text(encoding="utf-8")
             for name in ("platform.html", "platform.css", "platform.js",
                          "phone.html", "phone.css", "phone.js")}

    def body(self, name: str) -> str:
        """The file with its comments stripped, so prose about the rule is not
        mistaken for the rule being broken."""
        text = self.files[name]
        text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)       # css and js blocks
        text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)      # html
        text = re.sub(r"^\s*(//|\*).*$", " ", text, flags=re.M)  # line comments
        return text.lower()

    def test_no_leaderboard_language_is_shown_to_a_passenger(self):
        for name in self.files:
            text = self.body(name)
            for banned in ("best carriage", "good choice", "recommended",
                           "top 3", "quietest", "emptiest", "most free",
                           "least busy"):
                self.assertNotIn(banned, text, f"{name} shows {banned!r}")

    def test_the_screen_never_sorts_its_carriages(self):
        script = self.body("platform.js")
        for banned in (".sort(", "localecompare", "rank"):
            self.assertNotIn(banned, script,
                             f"platform.js reorders the map ({banned!r})")

    def test_the_phone_app_never_reads_the_whole_trains_counts(self):
        """It may read the zone list; it must not keep a seat count per car."""
        script = self.body("phone.js")
        self.assertIn("/api/assign", script)
        self.assertNotIn(".free", script, "the app is holding per-car seat counts")
        self.assertNotIn(".sort(", script)

    def test_the_screen_has_no_slot_a_badge_could_fill(self):
        markup = self.body("platform.html")
        for banned in ("badge", "pill", "rank"):
            self.assertNotIn(banned, markup, f"platform.html has a {banned!r} slot")

    def test_both_pages_load_only_their_own_assets(self):
        """The strict CSP allows no inline script or style, and no CDN."""
        for name in ("platform.html", "phone.html"):
            markup = self.files[name]
            self.assertNotIn("<script>", markup)
            self.assertNotIn("<style", markup)
            self.assertNotIn("http://", markup)
            self.assertNotIn("https://", markup)
            for url in re.findall(r'(?:src|href)="([^"]+)"', markup):
                self.assertTrue(url.startswith("/") or url.startswith("data:"),
                                f"{name} loads an outside asset: {url}")


class TestDocumentedIntegration(unittest.TestCase):
    """Applies the edit PASSENGER_INTERFACES.md tells a teammate to make.

    The point is the guard in `dashboard.py`: it refuses every non-GET request
    that did not come from this computer, and a passenger's phone is by
    definition not this computer. If that edit stops working, the phone app
    silently 403s for everyone except the person running the demo, so the
    instructions are tested rather than trusted.
    """

    PATCHES = (
        ("from dashboard_model import DemoError, DemoModel",
         "from dashboard_model import DemoError, DemoModel\n"
         "from passenger_routes import PASSENGER_PATHS, register_passenger_routes"),
        ('        if request.remote_addr in ("127.0.0.1", "::1", None):\n'
         '            return None\n',
         '        if request.remote_addr in ("127.0.0.1", "::1", None):\n'
         '            return None\n'
         '        if request.path in PASSENGER_PATHS:\n'
         '            return None\n'),
        ("    return app\n",
         "    register_passenger_routes(app, state)\n    return app\n"),
    )

    def patched_app(self):
        source = (TEAM / "dashboard.py") if TEAM else None
        if source is None or not source.exists():
            self.skipTest("the team's dashboard.py was not found next to these files")
        text = source.read_text(encoding="utf-8")
        for anchor, replacement in self.PATCHES:
            if anchor not in text:
                self.skipTest("dashboard.py has changed; re-check the documented edit")
            text = text.replace(anchor, replacement, 1)

        namespace = {"__name__": "patched_dashboard", "__file__": str(source)}
        exec(compile(text, str(source), "exec"), namespace)
        # extra_hosts is what `--host 0.0.0.0` passes in: without it Flask
        # refuses any request addressed to this machine's network name.
        return namespace["create_app"](extra_hosts=("192.168.1.50",))

    phone = {"REMOTE_ADDR": "192.168.1.50", "HTTP_HOST": "192.168.1.50:8765"}

    def test_a_phone_on_the_network_can_ask_for_guidance(self):
        client = self.patched_app().test_client()
        page = client.get("/app", environ_overrides=self.phone)
        page.close()
        self.assertEqual(page.status_code, 200)
        answer = client.post("/api/assign", json={"position": "F"},
                             environ_overrides=self.phone)
        self.assertEqual(answer.status_code, 200)
        self.assertIn(answer.get_json()["car"], CARS)

    def test_the_map_is_what_a_passenger_gets_at_the_front_door(self):
        client = self.patched_app().test_client()
        home = client.get("/", environ_overrides=self.phone)
        body = home.get_data(as_text=True)
        home.close()
        self.assertEqual(home.status_code, 200)
        self.assertIn("platform.css", body, "/ is not serving the positional map")

    def test_the_ranked_display_is_retained_unmodified_for_comparison(self):
        client = self.patched_app().test_client()
        baseline = client.get("/baseline", environ_overrides=self.phone)
        body = baseline.get_data(as_text=True)
        baseline.close()
        self.assertEqual(baseline.status_code, 200)
        # It is the team's original page, untouched: it still loads the old
        # bundle, which is what makes it a fair control case.
        self.assertIn("/assets/app.js", body)

    def test_the_demo_controls_stay_on_the_host_machine(self):
        client = self.patched_app().test_client()
        for url, payload in (("/api/mode", {"mode": "simulation", "port": ""}),
                             ("/api/preset", {"name": "empty"}),
                             ("/api/next_stop", {})):
            response = client.post(url, json=payload, environ_overrides=self.phone)
            self.assertEqual(response.status_code, 403,
                             f"{url} became reachable from the network")


class TestDeliveredFilesExist(unittest.TestCase):
    def test_every_asset_the_pages_ask_for_is_shipped(self):
        for page in ("platform.html", "phone.html"):
            markup = (WEB / page).read_text(encoding="utf-8")
            for url in re.findall(r'(?:src|href)="(/passenger/[^"]+)"', markup):
                self.assertTrue((WEB / Path(url).name).exists(), f"missing {url}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
