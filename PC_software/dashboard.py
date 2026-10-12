"""Local SmartRail passenger display. Run this file, then open the printed URL."""

import argparse
import socket
from pathlib import Path

from flask import Flask, jsonify, request
from serial.tools import list_ports
from waitress import serve

from dashboard_model import DemoError, DemoModel
from dashboard_serial import SerialWorker

WEB = Path(__file__).resolve().parent / "dashboard_web"


def create_app(model: DemoModel | None = None, extra_hosts: tuple = ()) -> Flask:
    app = Flask(__name__, static_folder=str(WEB), static_url_path="/assets")
    # Requests for any other host name are refused by Flask. --host adds this
    # machine's network address, so a phone can load the passenger display.
    app.config.update(MAX_CONTENT_LENGTH=4096,
                      TRUSTED_HOSTS=["127.0.0.1", "localhost", *extra_hosts])
    state = model if model is not None else DemoModel()

    @app.before_request
    def controls_stay_on_this_machine():
        # With --host the passenger display is reachable from the network, so
        # anything that changes the demo (or lists the machine's serial ports)
        # is refused unless the request came from this computer. There is no
        # password: viewing is public, control is local.
        if request.remote_addr in ("127.0.0.1", "::1", None):
            return None
        if request.method != "GET" or request.path in ("/controls", "/api/ports"):
            return jsonify(error="Controls are available only on the computer "
                                 "running the dashboard."), 403

    @app.before_request
    def local_requests_only():
        if request.method == "POST":
            origin = request.headers.get("Origin")
            if origin and origin != request.host_url.rstrip("/"):
                return jsonify(error="Cross-origin controls are not allowed."), 403
            if request.headers.get("Sec-Fetch-Site") == "cross-site":
                return jsonify(error="Cross-site controls are not allowed."), 403
            if not request.is_json:
                return jsonify(error="Controls require application/json."), 415

    @app.after_request
    def headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"
        )
        return response

    @app.errorhandler(DemoError)
    def bad_control(error):
        return jsonify(error=str(error)), 400

    def body(*keys):
        data = request.get_json()
        if not isinstance(data, dict) or any(not isinstance(data.get(key), str) for key in keys):
            raise DemoError("Expected a JSON object with string fields: " + ", ".join(keys))
        return data

    @app.get("/")
    @app.get("/controls")
    def index():
        return app.send_static_file("index.html")

    @app.get("/api/state")
    def snapshot():
        return jsonify(state.snapshot())

    @app.get("/api/ports")
    def ports():
        return jsonify(ports=[{"device": p.device, "description": p.description}
                              for p in sorted(list_ports.comports())])

    @app.post("/api/mode")
    def mode():
        data = body("mode", "port")
        state.configure(data["mode"], data["port"])
        return jsonify(state.snapshot())

    @app.post("/api/seats/<seat_id>")
    def seat(seat_id):
        data = body("state")
        state.set_seat(seat_id, data["state"])
        return jsonify(state.snapshot())

    @app.post("/api/preset")
    def preset():
        state.preset(body("name")["name"])
        return jsonify(state.snapshot())

    @app.post("/api/next_stop")
    def next_stop():
        # Random boarding/alighting on the simulated seats only.
        state.next_stop()
        return jsonify(state.snapshot())

    @app.post("/api/auto")
    def auto():
        # Seconds between automatic stops; "0" turns it off.
        state.configure_auto(body("interval")["interval"])
        return jsonify(state.snapshot())

    return app


def local_address() -> str:
    """This machine's address on the local network, for phones to open."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        try:
            probe.connect(("192.0.2.1", 80))  # no packet is sent
            return probe.getsockname()[0]
        except OSError:
            return socket.gethostbyname(socket.gethostname())


def main() -> None:
    parser = argparse.ArgumentParser(description="SmartRail local passenger dashboard")
    parser.add_argument("--http-port", type=int, default=8765)
    parser.add_argument("--host", default="127.0.0.1",
                        help="0.0.0.0 also serves the passenger view to this "
                             "network (phones, a second laptop). The controls "
                             "page stays on this computer.")
    parser.add_argument("--serial-port", help="Start hybrid mode on this port, e.g. COM5")
    args = parser.parse_args()
    if not 1 <= args.http_port <= 65535:
        parser.error("HTTP port must be between 1 and 65535")
    model = DemoModel()
    if args.serial_port:
        model.configure("hybrid", args.serial_port)
    worker = SerialWorker(model)
    worker.start()
    print(f"Passenger display: http://127.0.0.1:{args.http_port}/", flush=True)
    print(f"Demo controls:     http://127.0.0.1:{args.http_port}/controls", flush=True)
    network_hosts = []
    if args.host not in ("127.0.0.1", "localhost"):
        network_hosts.append(local_address())
        print(f"On this network:   http://{network_hosts[0]}:{args.http_port}/  "
              "(display only; the controls stay on this computer)", flush=True)
    print("Ctrl+C to stop. No hardware required in simulation mode.", flush=True)
    try:
        serve(create_app(model, extra_hosts=tuple(network_hosts)),
              host=args.host, port=args.http_port, threads=4)
    finally:
        worker.stop()


if __name__ == "__main__":
    main()