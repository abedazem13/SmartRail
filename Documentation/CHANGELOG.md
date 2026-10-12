# Changelog

## 2026-10-12 — full-train simulation: 12 cars × 108 seats

- `NUM_CARS=12`, `SEATS_PER_CAR=108`, `REAL_SENSORS=2` (1296 seats) defined once at the top of `PC_software/dashboard_model.py`. Cars are A–L; the two physical sensor seats stay A1 and B1.
- Added **Next stop** (`POST /api/next_stop`): at each station 5–20% of occupied seats free up, then 5–20% of the free seats fill, chosen at random across all cars. It can never free more than are occupied or fill more than are free, and it never changes a physical sensor seat. A station counter is shown on both views and resets with the scenario presets.
- Passenger view: per-car free count, occupancy percentage and bar, overall totals, station number, and a highlight of the emptiest car for platform guidance. The clickable 1296-seat map is in the controls view only, with sensor seats outlined.
- Firmware, `parameters.h` and the serial parsing are unchanged. Real seats are still read-only in hybrid mode and unknown during calibration, on disconnect or when data goes stale.
- `/api/state` sends per-car aggregates plus one compact states string per car instead of 1296 seat objects: 3.7 KB and ~1.5 ms per poll.
- Tests: 37 pass (was 30). New coverage for train size, next-stop bounds, empty/full trains, station counter, real seats unaffected by next stop, and the new endpoint. Fixed a bug found while testing: `seat_view()` did not age out stale sensor readings.
- **Next stop** is applied over ~2.4 s (passengers off, then on) instead of in one jump, with a BOARDING badge while it runs; an operator click, a preset or a mode change cancels whatever is still in progress.
- **Auto stops** (, 5–30 s from the UI, 3–300 s accepted): repeats the stop automatically for an unattended demo. Driven by display polling, so it runs only while a tab is open, and it never touches the sensor seats.
- **Network display** (`--host 0.0.0.0`, `start_dashboard_network.bat`): the passenger view can be opened from a phone or second laptop as the platform sign. The controls page, `/api/ports` and every POST are refused unless the request comes from the machine running the dashboard. Default is unchanged: 127.0.0.1 only.
- Added `start_dashboard.bat` for one-click start.
- Physical hardware validation still outstanding — see [the handoff](HARDWARE_DASHBOARD_AGENT_HANDOFF.md).

## 2026-10-09 — three-car hybrid passenger dashboard

- Added a local laptop passenger view and separate controls: 3 cars × 3 seats, fully simulated or two real sensors (A1/B1) plus seven simulated seats.
- Reused the existing firmware serial parser without changing firmware or console programs; added a dedicated reconnecting serial reader, unknown-on-stale/calibration behavior, and protection against manually editing real seats.
- Added colors/text, per-car counts, simple non-reserving availability suggestion, scenarios, source labels, and browser offline recovery.
- Added model/API/fake-serial and browser regression tests; physical testing remains pending. See [software evidence](assets/test-results/hybrid-dashboard-software-2026-10-09.md).
- Added [dashboard guide](17_HYBRID_DASHBOARD.md) and [teammate/AI hardware-testing handoff](HARDWARE_DASHBOARD_AGENT_HANDOFF.md).
- Recorded Abed's report that the earlier hardware presentation happened; date/result/evidence remain unspecified.

## 2026-09-21 — two sensors, compile fix, PC software

- **Firmware:** `NUM_SEATS` set to 2 (second sensor wired on GPIO35) [R].
- **Firmware, unit test — compile fix:** `ADC_ATTEN_DB_12` did not compile on a member's installed ESP32 core (`'ADC_ATTEN_DB_12' was not declared in this scope`) [V: compiler output]. Both sketches now use `ADC_11db` directly.
- **Unit test:** `Unit Tests/ir_sensor_check` now checks both sensors side by side.
- **New:** `PC_software/` — reads the firmware's serial output, counts free seats per carriage, shows passenger guidance. Includes a simulated board for testing without hardware. See DR-007, DR-008.
- **New:** `Documentation/08_COMMUNICATION_AND_DATA.md` — serial line format (IF-01) now has a consumer, so it is a contract: changing the firmware's print format requires updating `PC_software/seat_live.py`.

## 2026-09-21 — initial firmware and documentation

- Seat occupancy firmware for the hardware feasibility demo (commit `7b2940f`).
- Status, requirements, hardware, wiring, firmware, troubleshooting, design decisions and open questions documented from team interviews.
