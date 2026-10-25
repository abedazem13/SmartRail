"""Serves the two passenger-facing interfaces on top of the existing model.

  /platform       the platform entrance screen: a positional map
  /app            the phone app: a stateful dispatcher, one answer per person

Both read the same `DemoModel.snapshot()` the current dashboard reads. Neither
changes a seat. The split between them is deliberate and is the whole point:

  * The screen is read by everybody at once, so it may only carry positional
    information - this carriage, in this place, has this many seats. It names
    no winner, because a winner moves the whole crowd to one set of doors.
  * The app is read by one person, so it may give one instruction - go to that
    carriage - precisely because the dispatcher remembers what it told the
    last person and sends this one somewhere else.

`PassengerService` holds the dispatcher's state between requests. The state is
per-train, not per-passenger, so it resets when the train departs; the service
notices a departure by watching the model's station counter.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path

from flask import jsonify, request

from dispatcher import Dispatcher, DispatcherError
from platform_view import build_view

WEB = Path(__file__).resolve().parent / "passenger_web"

# Which display "/" serves. The positional map is the product; the ranked list
# it replaced is kept at /baseline, unmodified, as the control case. Set
# SMARTRAIL_DISPLAY=ranked to put the old one back in front.
DEFAULT_DISPLAY_IS_MAP = os.environ.get("SMARTRAIL_DISPLAY", "map").lower() != "ranked"

# Endpoints a passenger's own phone must be able to reach over the network.
# `dashboard.py` keeps every other POST on the host machine; these are listed
# so its guard can let them through. None of them can change a seat, a mode or
# a serial port: the most a stranger on the network can do is ask for guidance
# or hand an assignment back.
PASSENGER_PATHS = ("/api/assign", "/api/release", "/api/platform")


class PassengerService:
    """Owns the dispatcher and keeps it in step with the train.

    `model` is the existing DemoModel. Only `snapshot()` is called on it, so
    the service cannot disturb the demo it reads from.
    """

    def __init__(self, model, cars: tuple[str, ...] | None = None, **dispatcher_kw):
        self._model = model
        snapshot = model.snapshot()
        order = cars or tuple(car["id"] for car in snapshot["cars"])
        zones = {car["id"]: car.get("zone") or car["id"] for car in snapshot["cars"]}
        self.dispatcher = Dispatcher(order, zones=zones, **dispatcher_kw)
        self._lock = threading.RLock()
        self._seen = self._train_id(snapshot)

    @staticmethod
    def _train_id(snapshot: dict) -> tuple:
        """What makes this a different waiting crowd from the last one."""
        return (snapshot.get("generation"), snapshot.get("station"))

    def snapshot(self) -> dict:
        """The model's state, with the dispatcher reset if the train moved on."""
        snapshot = self._model.snapshot()
        with self._lock:
            current = self._train_id(snapshot)
            if current != self._seen:
                # A stop happened: the people the dispatcher was dividing have
                # boarded and gone. Routing counts from the last train would
                # make every carriage look equally used to the next crowd.
                self.dispatcher.reset()
                self._seen = current
        return snapshot

    # -------------------------------------------------------------- the views

    def platform(self) -> dict:
        """What a platform entrance screen shows. No ranking, no winner."""
        snapshot = self.snapshot()
        view = build_view(snapshot)
        view["station"] = snapshot.get("station")
        view["boarding"] = bool(snapshot.get("boarding"))
        view["connection"] = snapshot.get("connection", {}).get("status", "unknown")
        return view

    def assign(self, position: str, ticket: str | None = None) -> dict:
        """What one passenger is told. Each call routes a different carriage."""
        snapshot = self.snapshot()
        assignment = self.dispatcher.assign(position, snapshot["cars"], ticket=ticket)
        out = assignment.as_dict()
        out["now"] = assignment.issued_at
        out["seconds_left"] = max(0, round(assignment.expires_at - assignment.issued_at))
        # Shown to the passenger so the instruction is legible as a walk, not a
        # carriage number they have to find on a platform they do not know.
        steps = abs(assignment.walk_carriages)
        if steps == 0:
            out["walk"] = "You are already at the right zone"
        else:
            way = "towards the front" if assignment.walk_carriages < 0 else "towards the back"
            out["walk"] = (f"{steps} carriage{'s' if steps > 1 else ''} {way}")
        out["zones_total"] = len(snapshot["cars"])
        return out

    def release(self, ticket: str) -> dict:
        released = self.dispatcher.release(ticket)
        return {"released": released, "routed": self.dispatcher.routed()}


def register_passenger_routes(app, model, service: PassengerService | None = None,
                              as_default: bool = DEFAULT_DISPLAY_IS_MAP):
    """Add the two interfaces to an existing Flask app.

    `as_default` makes the positional map the display served at "/", and moves
    the older ranked display to "/baseline". The ranked display is left exactly
    as it was: it is the control case the boarding model measured, and editing
    it would spoil the comparison. It stays reachable so the two designs can be
    shown side by side, and it is the only place in the system where a carriage
    is still named as a recommendation.

    Returns the service, so a caller (or a test) can inspect the dispatcher.
    """
    service = service or PassengerService(model)

    if as_default:
        @app.before_request
        def map_is_the_passenger_display():
            # A before_request rather than a second "/" rule, so the existing
            # route in dashboard.py is left in place and keeps serving
            # /baseline below.
            if request.path == "/":
                return _send("platform.html")

        @app.get("/baseline")
        def ranked_baseline():
            """The superseded ranked display, retained for comparison."""
            return app.send_static_file("index.html")

    @app.get("/platform")
    def platform_screen():
        return _send("platform.html")

    @app.get("/app")
    def phone_app():
        return _send("phone.html")

    @app.get("/passenger/<path:name>")
    def passenger_asset(name):
        # Only the files shipped with this module, never a path from the URL.
        allowed = {"platform.css", "platform.js", "phone.css", "phone.js"}
        if name not in allowed:
            return jsonify(error="Not found"), 404
        return _send(name)

    @app.get("/api/platform")
    def platform_state():
        return jsonify(service.platform())

    @app.post("/api/assign")
    def assign():
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or not isinstance(data.get("position"), str):
            return jsonify(error="Expected a JSON object with a string 'position'."), 400
        ticket = data.get("ticket")
        if ticket is not None and (not isinstance(ticket, str) or len(ticket) > 64):
            return jsonify(error="'ticket' must be a short string."), 400
        try:
            return jsonify(service.assign(data["position"].strip(), ticket))
        except DispatcherError as error:
            return jsonify(error=str(error)), 400

    @app.post("/api/release")
    def release():
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or not isinstance(data.get("ticket"), str):
            return jsonify(error="Expected a JSON object with a string 'ticket'."), 400
        return jsonify(service.release(data["ticket"]))

    @app.get("/api/dispatcher")
    def dispatcher_stats():
        # Diagnostics for the demo: shows the crowd dividing as people ask.
        service.snapshot()
        return jsonify(service.dispatcher.stats())

    def _send(name: str):
        from flask import send_from_directory
        return send_from_directory(WEB, name)

    return service


def main() -> None:
    """Run the two interfaces on their own, without touching dashboard.py."""
    import argparse

    from flask import Flask
    from waitress import serve

    from dashboard_model import DemoModel

    parser = argparse.ArgumentParser(
        description="SmartRail passenger interfaces (platform screen + phone app)")
    parser.add_argument("--http-port", type=int, default=8766)
    parser.add_argument("--host", default="127.0.0.1",
                        help="0.0.0.0 also serves phones on this network")
    args = parser.parse_args()

    model = DemoModel()
    app = Flask(__name__)
    app.config.update(MAX_CONTENT_LENGTH=4096)

    @app.after_request
    def headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
            "base-uri 'none'")
        return response

    @app.get("/")
    def home():
        from flask import redirect
        return redirect("/platform")

    register_passenger_routes(app, model)
    print(f"Platform screen: http://127.0.0.1:{args.http_port}/platform", flush=True)
    print(f"Phone app:       http://127.0.0.1:{args.http_port}/app", flush=True)
    print("Ctrl+C to stop. No hardware required.", flush=True)
    serve(app, host=args.host, port=args.http_port, threads=4)


if __name__ == "__main__":
    main()
