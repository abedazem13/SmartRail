# 01 — Current Status and Handoff

**Status date:** 2026-09-21
**Applies to commit:** TODO: fill in after this commit is pushed

Provenance tags used in this file: **[V]** verified (code, photo, or measured output), **[R]** reported by a team member, not independently verified, **[TODO]** unknown.

## Next milestone

Hardware feasibility demo: detect an empty seat and an occupied seat. **Due 2026-10-04** [R]. The earlier optional slots (3/9, 10/9, 15/9) have passed. Arrange the demo slot with the lab staff in advance.

## Status matrix

| Item | Status | Notes |
|---|---|---|
| Single sensor reading on GPIO34 | Working [R] | Empty vs occupied gap measured ≈ 40 cm |
| Empty/occupied decision firmware | Implemented [V] | `ESP32/ESP32.ino`. Compile-checked; not yet validated on hardware at this commit |
| Bypass capacitor (10 µF) | **Missing** [R] | Required by the sensor datasheet. Detection still works thanks to the 40 cm gap, but noise is higher than it should be |
| Second sensor (GPIO35) | Not wired | Set `NUM_SEATS 2` in `parameters.h` once connected |
| Acceptance test (10 cycles) | Not run | Procedure in `Unit Tests/README.md` |
| Calibration table | Not recorded | Template in `Unit Tests/README.md` |
| Communication car → platform | Not started | |
| Platform signage | Not started | |
| Queue / dispersion simulation | Not started | Highest project risk — see 02 |
| Flutter app | Not started | [TODO] confirm whether it is in scope |

## Known issues

1. No bypass capacitor fitted — see [11_TROUBLESHOOTING.md](11_TROUBLESHOOTING.md#noisy-readings).
2. An earlier breadboard photo showed the sensor wires near the VIN/GND rows and unpowered breadboard rails. [TODO] confirm the current wiring matches [05_WIRING_AND_PINOUT.md](05_WIRING_AND_PINOUT.md).
3. Absolute empty/occupied distances not recorded, only the gap. Needed to confirm both are inside 15–80 cm.

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

## Ownership

| Area | Owner |
|---|---|
| TODO | TODO |
