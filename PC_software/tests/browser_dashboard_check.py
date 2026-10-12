"""Optional real-browser check. Fake serial data only; never opens a COM port.

Run from PC_software: python tests/browser_dashboard_check.py
Requires requirements-dev.txt and `python -m playwright install chromium`.
Alternatively set SMARTRAIL_BROWSER_CHANNEL=msedge for installed Edge.
"""

import logging
import os
from pathlib import Path
import random
import sys
import tempfile
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server

from dashboard import create_app
from dashboard_model import DemoModel, EXAMPLE_FREE_PER_CAR, SEATS_PER_CAR, TOTAL_SEATS


def main():
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    clock = [100.0]
    model = DemoModel(clock=lambda: clock[0], rng=random.Random(20261012))
    server = make_server("127.0.0.1", 0, create_app(model), threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    free_a, free_b, free_c = EXAMPLE_FREE_PER_CAR[:3]
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

            # Twelve cars on both views; the example scenario's free counts.
            expect(display.locator("#count-A")).to_have_text(str(free_a))
            expect(display.locator("#count-B")).to_have_text(str(free_b))
            expect(display.locator("#count-C")).to_have_text(str(free_c))
            expect(display.locator("#station-number")).to_have_text("1")
            assert display.locator("article.car").count() == len(EXAMPLE_FREE_PER_CAR)
            expect(display.locator("#controls")).to_be_hidden()

            # The passenger display carries no seat map and no seat buttons.
            assert display.locator("button.cell").count() == 0
            assert controls.locator("#seats-A button.cell").count() == SEATS_PER_CAR
            assert controls.locator("button.cell").count() == TOTAL_SEATS

            # Every simulated seat is clickable, not only the sensor seats.
            for seat in ("A2", "A54", "B108", "L1", "L108"):
                expect(controls.locator(f"#seat-{seat}")).to_be_enabled()
            assert controls.locator("button.cell:disabled").count() == 0
            controls.locator("#seat-L108").click()
            first = controls.locator("#count-L").text_content()
            controls.locator("#seat-L108").click()  # and back again
            expect(controls.locator("#count-L")).not_to_have_text(first)

            # A1 is occupied in the example scenario; freeing it adds one seat.
            expect(controls.locator("#seat-A1")).to_be_enabled()
            controls.locator("#seat-A1").click()
            expect(display.locator("#count-A")).to_have_text(str(free_a + 1))
            expect(controls.locator("#count-A")).to_have_text(str(free_a + 1))
            controls.locator('[data-preset="example"]').click()
            expect(display.locator("#count-A")).to_have_text(str(free_a))

            # Next stop: the station advances and seats move, bounded by the model.
            controls.locator("#next-stop").click()
            expect(display.locator("#station-number")).to_have_text("2")
            expect(controls.locator("#station-number")).to_have_text("2")
            controls.locator('[data-preset="example"]').click()
            expect(display.locator("#station-number")).to_have_text("1")

            # Automatic stops: the badge appears on both views and stops run
            # without clicking. 5 s is the shortest option in the UI.
            controls.locator("#auto-interval").select_option("5")
            controls.locator("#auto-toggle").click()
            expect(controls.locator("#auto-toggle")).to_have_text("Stop auto stops")
            expect(display.locator("#auto-badge")).to_have_text("AUTO · EVERY 5s")
            clock[0] += 5.1
            expect(display.locator("#station-number")).to_have_text("2")
            # A stop lands over about 2.4 s, so the boarding badge is visible.
            expect(display.locator("#boarding-badge")).to_be_visible()
            clock[0] += 3
            expect(display.locator("#boarding-badge")).to_be_hidden()
            controls.locator("#auto-toggle").click()
            expect(display.locator("#auto-badge")).to_be_hidden()
            clock[0] += 30
            expect(display.locator("#station-number")).to_have_text("2")  # stopped
            controls.locator('[data-preset="example"]').click()

            screenshot = Path(tempfile.gettempdir()) / "smartrail-passenger-display.png"
            display.screenshot(path=str(screenshot), full_page=True)
            display.set_viewport_size({"width": 1366, "height": 768})
            display.screenshot(path=str(Path(tempfile.gettempdir()) / "smartrail-passenger-laptop.png"), full_page=True)

            controls.locator("#serial-port").fill("FAKE_TEST_PORT")
            controls.locator("#hybrid").click()
            expect(controls.locator("#seat-A1")).to_be_disabled()
            expect(controls.locator("#seat-B1")).to_be_disabled()
            # Only the two sensor seats lock; the rest stay editable.
            assert controls.locator("button.cell:disabled").count() == 2
            expect(controls.locator("#seat-A2")).to_be_enabled()
            expect(controls.locator("#diagnostic-A1")).to_contain_text("UNKNOWN")
            expect(display.locator("#car-A")).to_have_class("car unknown")
            generation = model.generation
            model.transport(generation, True)
            model.feed(generation, "--- CALIBRATION: keep all seats EMPTY. starting in 3 s ---")
            expect(display.locator("#connection-text")).to_contain_text("Calibrating")
            model.feed(generation, "CAL seat=0 baseline=58.4cm mv=566 noise=38mV")
            model.feed(generation, "CAL seat=1 baseline=58.4cm mv=566 noise=38mV")
            model.feed(generation, "--- calibration done ---")
            model.feed(generation, "S0 dist= 58.3cm base= 58.4cm noise= 52mV EMPTY S1 dist= 58.3cm base= 58.4cm noise= 52mV EMPTY")
            # A1 and B1 now come from the board, both read free.
            expect(display.locator("#count-A")).to_have_text(str(free_a + 1))
            expect(display.locator("#count-B")).to_have_text(str(free_b + 1))
            model.feed(generation, "EVENT seat=0 state=OCCUPIED dist=23.6cm")
            expect(display.locator("#count-A")).to_have_text(str(free_a))

            # A preset cannot touch the real seats: B1 stays free, A1 stays occupied.
            controls.locator('[data-preset="occupied"]').click()
            expect(display.locator("#count-A")).to_have_text("0")
            expect(display.locator("#count-B")).to_have_text("1")
            # Next stop must not move the real seats either.
            controls.locator("#next-stop").click()
            expect(controls.locator("#diagnostic-A1")).to_contain_text("OCCUPIED")
            expect(controls.locator("#diagnostic-B1")).to_contain_text("EMPTY")

            # The stop freed random simulated seats; refill them for the next check.
            controls.locator('[data-preset="occupied"]').click()
            expect(display.locator("#count-B")).to_have_text("1")  # real B1 only

            clock[0] += 3  # stale sensor data -> unknown, never counted free
            expect(display.locator("#car-B")).to_have_class("car unknown")
            expect(display.locator("#count-B")).to_have_text("0")
            model.transport(generation, False, "Fake unplug")
            expect(display.locator("#connection-text")).to_contain_text("disconnected")
            controls.locator("#simulation").click()
            expect(controls.locator("#seat-A1")).to_be_enabled()
            controls.locator('[data-preset="example"]').click()
            expect(display.locator("#count-B")).to_have_text(str(free_b))

            # At a phone width, no horizontal overflow or inaccessible controls.
            controls.set_viewport_size({"width": 390, "height": 844})
            assert controls.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            controls.screenshot(path=str(Path(tempfile.gettempdir()) / "smartrail-controls-mobile.png"), full_page=True)

            # A broken HTTP connection must not leave stale availability visible.
            display.route("**/api/state", lambda route: route.abort())
            expect(display.locator("#offline")).to_be_visible(timeout=6000)
            expect(display.locator("#count-B")).to_have_text("—")
            expect(display.locator("#station-number")).to_have_text("—")
            display.unroute("**/api/state")
            expect(display.locator("#offline")).to_be_hidden(timeout=6000)
            expect(display.locator("#count-B")).to_have_text(str(free_b))
            assert not errors, errors
            browser.close()
            print(f"PASS: browser tabs, {TOTAL_SEATS}-seat controls map, next stop, fake sensor events, "
                  "calibration, stale data, presets, mobile layout, server loss/recovery; no JS exceptions.")
            print(f"Screenshot: {screenshot}")
    finally:
        server.shutdown()
        thread.join(timeout=5)


if __name__ == "__main__":
    main()
