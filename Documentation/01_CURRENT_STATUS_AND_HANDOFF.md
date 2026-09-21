# 01 — Current Status and Handoff

**Status date:** 2026-09-21
**Applies to commit:** `7b2940f`

Provenance tags used in this file: **[V]** verified (code, photo, or measured output), **[R]** reported by a team member, not independently verified, **[TODO]** unknown.

## Next milestone

Hardware feasibility demo: detect an empty seat and an occupied seat. **Due 2026-10-04** [R]. The earlier optional slots (3/9, 10/9, 15/9) have passed. Arrange the demo slot with the lab staff in advance.

## Status matrix

| Item | Status | Notes |
|---|---|---|
| Single sensor reading | Working [R] | Detection worked on several different ADC pins the team tried [R, 2026-09-21]. Default stays GPIO34. Empty seat ≈ 50–60 cm from the sensor, empty vs occupied gap ≈ 40 cm [R] |
| Empty/occupied decision firmware | Implemented [V] | `ESP32/ESP32.ino`. Compile-checked; not yet validated on hardware at this commit |
| Bypass capacitor (10 µF) | **Missing** [R] | Required by the sensor datasheet. Detection still works thanks to the 40 cm gap, but noise is higher than it should be |
| Second sensor (GPIO35) | Not in hand [R, 2026-09-21] | Request from the lab if the demo needs 2 seats. Then set `NUM_SEATS 2` in `parameters.h` |
| Acceptance test (10 cycles) | Not run | Procedure in `Unit Tests/README.md` |
| Calibration table | Not recorded | Template in `Unit Tests/README.md` |
| Communication car → platform | Not started | |
| Platform signage | Not started | |
| Queue / dispersion simulation | Not started | Highest project risk — see 02 |
| Flutter app | Not started | [TODO] confirm whether it is in scope |

## Known issues

1. No bypass capacitor fitted — see [11_TROUBLESHOOTING.md](11_TROUBLESHOOTING.md#noisy-readings).
2. An earlier breadboard photo showed the sensor wires near the VIN/GND rows and unpowered breadboard rails. [TODO] confirm the current wiring matches [05_WIRING_AND_PINOUT.md](05_WIRING_AND_PINOUT.md).
3. Occupied distance not measured directly. Empty seat ≈ 50–60 cm [R] minus the ≈ 40 cm gap gives an occupied reading of roughly 10–20 cm [assumption]. That is at or below the ~15 cm safe minimum: if a person comes within ~8 cm of the sensor, the output folds back and can read as "far" (EMPTY). Measure the occupied distance; if it is under ~15 cm, raise the sensor or angle it further forward.

## Immediate next actions (priority order)

1. Fit a 10 µF capacitor across VIN/GND next to the sensor (ask lab staff / check the course kit).
2. Run `Unit Tests/ir_sensor_check`, fill in the calibration table.
3. Run the main firmware, record the `CAL` line and the absolute occupied distance.
4. Run the 10-cycle acceptance test, record the result.
5. Wire the second sensor, set `NUM_SEATS 2`, repeat step 4.
6. Record the installed ESP32 core version in `README.md`.
7. Raise with the mentor how the simulation will be demonstrated and measured.

## Reproduce the latest working state

1. Wire per [05_WIRING_AND_PINOUT.md](05_WIRING_AND_PINOUT.md).
2. Arduino IDE → open `ESP32/ESP32.ino` → board "ESP32 Dev Module" → upload.
3. Serial Monitor 115200. Keep the seat empty for the first 3 s (calibration).
4. Sit down: within ~1.5 s the log prints `EVENT seat=0 state=OCCUPIED` and the on-board LED lights.

## Team and mentor

Mentor: Itai Dabran [R]. Summer semester: the course deck's week-by-week plan does not apply directly; the team reports it is up to date with the course milestones [R, 2026-09-21].

## Ownership

All three members (Yazan Rabea, Abed Azem, Samar Khatib) work jointly on every area. There is no per-area split [R, 2026-09-21].

| Area | Owner |
|---|---|
| Hardware, firmware, communication, signage, simulation, documentation | Shared: Yazan, Abed, Samar |
