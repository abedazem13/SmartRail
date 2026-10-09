"""Local SmartRail passenger display. Run this file, then open the printed URL."""

import argparse
from pathlib import Path

from flask import Flask, jsonify, request
from serial.tools import list_ports
from waitress import serve

from dashboard_model import DemoError, DemoModel
from dashboard_serial import SerialWorker

WEB = Path(__file__).resolve().parent / "dashboard_web"


def create_app(model: DemoModel | None = None) -> Flask:
    app = Flask(__name__, static_folder=str(WEB), static_url_path="/assets")
    app.config.update(MAX_CONTENT_LENGTH=4096, TRUSTED_HOSTS=["127.0.0.1", "localhost"])
    state = model if model is not None else DemoModel()

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

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="SmartRail local passenger dashboard")
    parser.add_argument("--http-port", type=int, default=8765)
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
    print("Local demo only. Ctrl+C to stop. No hardware required in simulation mode.", flush=True)
    try:
        serve(create_app(model), host="127.0.0.1", port=args.http_port, threads=4)
    finally:
        worker.stop()


if __name__ == "__main__":
    main()