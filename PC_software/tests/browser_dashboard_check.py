"""Optional real-browser check. Fake serial data only; never opens a COM port.

Run from PC_software: python tests/browser_dashboard_check.py
Requires requirements-dev.txt and `python -m playwright install chromium`.
Alternatively set SMARTRAIL_BROWSER_CHANNEL=msedge for installed Edge.
"""

import logging
import os
from pathlib import Path
import sys
import tempfile
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server

from dashboard import create_app
from dashboard_model import DemoModel


def main():
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    clock = [100.0]
    model = DemoModel(clock=lambda: clock[0])
    server = make_server("127.0.0.1", 0, create_app(model), threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    try:
        with sync_playwright() as p:
            channel = os.environ.get("SMARTRAIL_BROWSER_CHANNEL")
            browser = p.chromium.launch(channel=channel, headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 1100})
            display = context.new_page()
            controls = context.new_page()
            errors = []
            for page in (display, controls):
                page.on("pageerror", lambda error: errors.append(str(error)))
            display.goto(url)
            controls.goto(url + "/controls")
            expect(display.locator("#count-A")).to_have_text("1")
            expect(display.locator("#count-B")).to_have_text("3")
            expect(display.locator("#count-C")).to_have_text("0")
            expect(display.locator("#controls")).to_be_hidden()
            assert display.locator("button.seat").count() == 0
            expect(controls.locator("#seat-A1")).to_be_enabled()
            controls.locator("#seat-A1").click()
            expect(display.locator("#count-A")).to_have_text("0")
            expect(controls.locator("#count-A")).to_have_text("0")
            controls.locator('[data-preset="example"]').click()
            expect(display.locator("#count-A")).to_have_text("1")
            screenshot = Path(tempfile.gettempdir()) / "smartrail-passenger-display.png"
            display.screenshot(path=str(screenshot), full_page=True)
            display.set_viewport_size({"width": 1366, "height": 768})
            assert display.locator("#cars").bounding_box()["y"] + display.locator("#cars").bounding_box()["height"] < 768
            display.screenshot(path=str(Path(tempfile.gettempdir()) / "smartrail-passenger-laptop.png"), full_page=True)

            controls.locator("#serial-port").fill("FAKE_TEST_PORT")
            controls.locator("#hybrid").click()
            expect(controls.locator("#seat-A1")).to_be_disabled()
            expect(controls.locator("#seat-B1")).to_be_disabled()
            expect(controls.locator("#state-A1")).to_have_text("Unknown")
            generation = model.generation
            model.transport(generation, True)
            model.feed(generation, "--- CALIBRATION: keep all seats EMPTY. starting in 3 s ---")
            expect(display.locator("#connection-text")).to_contain_text("Calibrating")
            model.feed(generation, "CAL seat=0 baseline=58.4cm mv=566 noise=38mV")
            model.feed(generation, "CAL seat=1 baseline=58.4cm mv=566 noise=38mV")
            model.feed(generation, "--- calibration done ---")
            model.feed(generation, "S0 dist= 58.3cm base= 58.4cm noise= 52mV EMPTY S1 dist= 58.3cm base= 58.4cm noise= 52mV EMPTY")
            expect(display.locator("#count-A")).to_have_text("1")
            expect(display.locator("#count-B")).to_have_text("3")
            model.feed(generation, "EVENT seat=0 state=OCCUPIED dist=23.6cm")
            expect(display.locator("#count-A")).to_have_text("0")
            controls.locator('[data-preset="occupied"]').click()
            expect(display.locator("#count-B")).to_have_text("1")  # Real B1 remains free.
            expect(display.locator("#state-A1")).to_have_text("Occupied")
            expect(display.locator("#state-B1")).to_have_text("Free")
            clock[0] += 3
            expect(display.locator("#state-A1")).to_have_text("Unknown")
            expect(display.locator("#car-B")).to_have_class("car unknown")
            expect(display.locator("#count-B")).to_have_text("0")
            model.transport(generation, False, "Fake unplug")
            expect(display.locator("#connection-text")).to_contain_text("disconnected")
            controls.locator("#simulation").click()
            expect(controls.locator("#seat-A1")).to_be_enabled()
            controls.locator('[data-preset="example"]').click()
            expect(display.locator("#count-B")).to_have_text("3")

            # At a phone width, no horizontal overflow or inaccessible controls.
            controls.set_viewport_size({"width": 390, "height": 844})
            assert controls.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            controls.screenshot(path=str(Path(tempfile.gettempdir()) / "smartrail-controls-mobile.png"), full_page=True)

            # A broken HTTP connection must not leave stale availability visible.
            display.route("**/api/state", lambda route: route.abort())
            expect(display.locator("#offline")).to_be_visible(timeout=6000)
            expect(display.locator("#count-B")).to_have_text("—")
            expect(display.locator("#state-B1")).to_have_text("Unknown")
            display.unroute("**/api/state")
            expect(display.locator("#offline")).to_be_hidden(timeout=6000)
            expect(display.locator("#count-B")).to_have_text("3")
            assert not errors, errors
            browser.close()
            print("PASS: browser tabs, 9-seat controls, fake sensor events, calibration, stale data, presets, mobile layout, server loss/recovery; no JS exceptions.")
            print(f"Screenshot: {screenshot}")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


if __name__ == "__main__":
    main()