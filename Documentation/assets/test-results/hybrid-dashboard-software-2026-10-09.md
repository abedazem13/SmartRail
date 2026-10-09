# Hybrid dashboard — software-only validation

**Date:** 2026-10-09

**Revision:** uncommitted dashboard implementation on top of `0d7ee98`. Record a final commit hash when publishing; these results concern the files in this change, not the older base commit alone.

**Hardware:** NOT AVAILABLE. No ESP32, IR sensor, real serial device or physical prototype was tested. The earlier presentation is not evidence for this dashboard.

## Environment observed

- Windows, Python 3.13.5 (64-bit), editor-selected virtual environment.
- Flask 3.1.2, pyserial 3.5, Waitress 3.0.2.
- Playwright 1.63.0 driving installed Microsoft Edge 154.0.4258.62 in headless mode.
- All scripts used that same virtual environment. Installation/setup helpers initially reported a different system interpreter path; the effective editor-selected interpreter was checked before executing tests.

## Results

| Check | Result | Method / limits |
|---|---|---|
| Model/API/serial regression suite | PASS — 30 tests | Python unittest, no physical ports opened |
| All binary nine-seat arrangements | PASS — 512 combinations | One exhaustive model test checks total and per-car counts |
| Example colors/counts | PASS | A=1/yellow, B=3/green, C=0/red |
| Sensor mapping and read-only protection | PASS | Synthetic firmware sensor 0→A1, 1→B1; presets/API cannot overwrite real seats |
| Calibration, boot and partial calibration | PASS | Synthetic serial markers; unknown until fresh post-calibration status |
| Per-seat stale data, reconnect and mode changes | PASS | Controlled clock and fake serial handles; generation guards reject old input |
| Fragmented/oversized serial lines | PASS | Bounded byte framing, no real UART |
| Unknown-safe counts and stable suggestions | PASS | No reservations/decrements, no recommendation based solely on unknown seats |
| Local API input validation and origin checks | PASS | Flask test clients; no public/network security certification |
| Two actual browser tabs | PASS | Control clicks/presets update passenger view; passenger seat icons read-only |
| Hybrid browser flow | PASS | Fake firmware input only: calibration, occupancy, stale data, disconnect and mode switching |
| Responsive UI | PASS | 1440×1100 desktop; 1366×768 laptop cards fit viewport height; 390×844 control page has no horizontal overflow |
| Browser server-loss recovery | PASS | Abort state requests; old counts disappear, automatic recovery restores them |
| JavaScript execution | PASS | No uncaught page exceptions during browser test |
| Static/editor checks | PASS | No reported errors in changed software files at validation time |

Commands are documented in [the dashboard guide](../../17_HYBRID_DASHBOARD.md) and [teammate handoff](../../HARDWARE_DASHBOARD_AGENT_HANDOFF.md). From PC_software, the suite is `python -m unittest discover -s tests -p "test_*.py" -v`; the browser check is `python tests/browser_dashboard_check.py` using the same selected interpreter. Edge was selected with `SMARTRAIL_BROWSER_CHANNEL=msedge`.

The browser test creates screenshots in the OS temporary directory: `smartrail-passenger-display.png`, `smartrail-passenger-laptop.png`, and `smartrail-controls-mobile.png`. They were visually inspected locally; these temporary images are not committed evidence files. Rerunning the check regenerates them.

## NOT RUN — teammates must supply physical evidence

- Actual Arduino IDE build/upload with their installed ESP32 core.
- Correct sensor wiring, power stability, capacitor effects, mounting and physical range.
- Real USB-driver behavior and serial exclusivity on their machine.
- Physical two-sensor occupancy accuracy, ten-cycle tests and measured latency.
- Real unplug/replug/reboot behavior and end-to-end passenger-display latency.
- Mentor/course acceptance of the hybrid topology and laptop signage.

Follow [HARDWARE_DASHBOARD_AGENT_HANDOFF.md](../../HARDWARE_DASHBOARD_AGENT_HANDOFF.md). Do not relabel simulated results as hardware passes.