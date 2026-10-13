## SmartRail — Seat Occupancy Sensing and Platform Guidance

**Project by:** Yazan Rabea, Abed Azem, Samar Khatib

**Mentor:** Itai Dabran

SmartRail aims to detect train-seat availability and show it to waiting passengers so they can choose suitable cars and platform zones. The current prototype combines two physical sensor inputs with a simulated train and a browser display. A quantitative comparison of passenger distributions and train dwell time is a separate planned evaluation, not a result established by the current seat-change animation.

**Current maturity (2026-10-13):** the earlier hardware presentation happened (reported by Abed; result not recorded). Firmware supports two IR seat sensors. The current laptop dashboard represents 12 logical cars × 108 seats: all 1,296 simulated, or two real inputs (A1/B1) plus 1,294 simulated seats. Simulated station stops and optional LAN passenger viewing are implemented. Current-version physical integration and final acceptance evidence still need recording; old software results do not certify the newer version. Wireless ESP32 → platform deployment and the quantitative dwell-time comparison are not implemented.

## October 18 presentation package

Start at [Presentation/README.md](Presentation/README.md) for the project overview, slide outline and speaker notes, live demo script, user manual, programmer manual, readiness checklist and test-results template. This package reflects the current 12-car source; parts of the older status/dashboard/handoff documentation still describe the previous nine-seat version. Confirm scope and submission formats with course staff, and add actual test evidence before submitting.

## Run the passenger display

Start with the current [user manual](Presentation/USER_MANUAL.md). It works without hardware and includes a separate control screen for changing simulated seats. Teammates with the board should use the current [demo script](Presentation/DEMO_SCRIPT.md) and [test-results template](Presentation/TEST_RESULTS_TEMPLATE.md) for physical acceptance; the older hardware handoff contains obsolete nine-seat expectations.

## Documentation handoff

Current project members should give [DOCUMENTATION_AGENT_TASK.md](DOCUMENTATION_AGENT_TASK.md) to their AI agent and complete the documentation handoff described there.

## Details about the project

| Area | Technology |
|---|---|
| Sensing | Sharp GP2Y0A21YK0F IR distance sensor (analog, 10–80 cm), one per seat |
| Controller | ESP32 DevKit V1 (30-pin, CP2102 USB-UART) |
| Firmware | Arduino framework, Arduino IDE 2.x |
| PC software (interim) | Python 3.10+, Flask/Waitress + pyserial: local passenger dashboard, controls, USB seat states |
| Communication | TODO: not selected yet (candidates: ESP-NOW, WiFi + Firebase) |
| Platform signage | Laptop browser demo implemented; final deployment/hardware approval pending |
| Simulation | Random seat-change/station demo implemented; quantitative passenger-flow/dwell-time comparison not implemented |

## Folder description :
* ESP32: source code for the esp side (firmware). Open `ESP32/ESP32.ino` in Arduino IDE.
* PC_software: Python programs that read the ESP32 over USB, count free seats per carriage and show passenger guidance. See [PC_software/README.md](PC_software/README.md).
* Documentation: wiring diagram + basic operating instructions
* Unit Tests: tests for individual hardware components (input / output devices)
* flutter_app : dart code for our Flutter app. TODO: confirm whether an app is in scope
* Parameters: `ESP32/parameters.h` holds every tunable setting (pins, thresholds, timings)
* Assets: link to 3D printed parts, Fritzing file for connection diagram (FZZ format) etc

## Files

| File | What it does |
|---|---|
| [PC_software/dashboard.py](PC_software/dashboard.py) | New local passenger screen and controls: simulation or two-sensor hybrid mode |
| `ESP32/ESP32.ino` | Firmware: reads both seat sensors, calibrates the empty-seat distance at boot, decides EMPTY/OCCUPIED per seat, lights a status LED, prints status and events over USB |
| `ESP32/parameters.h` | Every tunable setting: number of seats, pins, sampling, thresholds |
| `ESP32/SECRETS.example.h` | Template for WiFi credentials (not used yet). Real values go in `ESP32/SECRETS.h`, which Git ignores |
| `ESP32/compiled_program.bin` | Compiled firmware, flashable without Arduino IDE. See [06_ESP32_FIRMWARE.md](Documentation/06_ESP32_FIRMWARE.md#compiled-binary) |
| `PC_software/seat_live.py` | Reads the board over USB: seat changes, free seats per carriage, platform display line. Records sessions for replay |
| `PC_software/seat_status.py` | Short version: prints only when a seat becomes occupied or empty |
| `PC_software/guidance.py` | Decides which carriage each waiting passenger should board |
| `PC_software/seat_sim.py` | Runs the PC software on a simulated board, no hardware needed |
| `Unit Tests/ir_sensor_check/ir_sensor_check.ino` | Hardware test: voltage, distance and noise of both sensors, no decisions |
| `DOCUMENTATION_AGENT_TASK.md` | Course instructions for the documentation handoff |

## Documentation index
* [Presentation package](Presentation/README.md) — current overview, manuals, demo and preparation checklist
* [01 Current status and handoff](Documentation/01_CURRENT_STATUS_AND_HANDOFF.md) — read first
* [09 Setup, build and run](Documentation/09_SETUP_BUILD_AND_RUN.md) — how to start the dashboard, show it on a phone, connect the ESP32
* [02 Requirements and scope](Documentation/02_REQUIREMENTS_AND_SCOPE.md)
* [04 Hardware](Documentation/04_HARDWARE.md)
* [05 Wiring and pinout](Documentation/05_WIRING_AND_PINOUT.md)
* [06 ESP32 firmware](Documentation/06_ESP32_FIRMWARE.md)
* [08 Communication and data](Documentation/08_COMMUNICATION_AND_DATA.md) — serial line format
* [11 Troubleshooting](Documentation/11_TROUBLESHOOTING.md)
* [12 Design decisions](Documentation/12_DESIGN_DECISIONS.md)
* [Open questions](Documentation/OPEN_QUESTIONS.md)
* [Changelog](Documentation/CHANGELOG.md)
* [PC software](PC_software/README.md)
* [17 Hybrid dashboard](Documentation/17_HYBRID_DASHBOARD.md)
* [Hardware dashboard agent handoff](Documentation/HARDWARE_DASHBOARD_AGENT_HANDOFF.md)

## ESP32 SDK version used in this project:
TODO: fill from Arduino IDE → Boards Manager → "esp32 by Espressif Systems" installed version

## Arduino/ESP32 libraries used in this project:
* None beyond the ESP32 Arduino core (hardware-feasibility stage)

PC side: Python 3 (TODO: version) and pyserial (TODO: version, `python -m pip show pyserial`).

## Connection diagram:
See [Documentation/05_WIRING_AND_PINOUT.md](Documentation/05_WIRING_AND_PINOUT.md). TODO: add Fritzing diagram.

## Project Poster:
TODO

This project is part of ICST - The Interdisciplinary Center for Smart Technologies, Taub Faculty of Computer Science, Technion
https://icst.cs.technion.ac.il/
