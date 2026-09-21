# Changelog

## 2026-09-21 — two sensors, compile fix, PC software

- **Firmware:** `NUM_SEATS` set to 2 (second sensor wired on GPIO35) [R].
- **Firmware, unit test — compile fix:** `ADC_ATTEN_DB_12` did not compile on a member's installed ESP32 core (`'ADC_ATTEN_DB_12' was not declared in this scope`) [V: compiler output]. Both sketches now use `ADC_11db` directly.
- **Unit test:** `Unit Tests/ir_sensor_check` now checks both sensors side by side.
- **New:** `PC_software/` — reads the firmware's serial output, counts free seats per carriage, shows passenger guidance. Includes a simulated board for testing without hardware. See DR-007, DR-008.
- **New:** `Documentation/08_COMMUNICATION_AND_DATA.md` — serial line format (IF-01) now has a consumer, so it is a contract: changing the firmware's print format requires updating `PC_software/seat_live.py`.

## 2026-09-21 — initial firmware and documentation

- Seat occupancy firmware for the hardware feasibility demo (commit `7b2940f`).
- Status, requirements, hardware, wiring, firmware, troubleshooting, design decisions and open questions documented from team interviews.
