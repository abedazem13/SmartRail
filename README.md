## SmartRail — Seat Occupancy Sensing and Platform Guidance

**Project by:** TODO: team member names

SmartRail detects in real time which train seats are free, sends that information to digital signage on the station platform, and guides waiting passengers to spread evenly along the platform (a uniform/linear distribution) instead of crowding around one point (a Gaussian distribution). A simulation quantifies how much this shortens the train's dwell time at the station.

**Current maturity (2026-09-21):** hardware feasibility stage. One IR distance sensor on an ESP32 distinguishes an empty seat from an occupied one. Communication, signage and simulation are not started. See [Documentation/01_CURRENT_STATUS_AND_HANDOFF.md](Documentation/01_CURRENT_STATUS_AND_HANDOFF.md).

## Documentation handoff

Current project members should give [DOCUMENTATION_AGENT_TASK.md](DOCUMENTATION_AGENT_TASK.md) to their AI agent and complete the documentation handoff described there.

## Details about the project

| Area | Technology |
|---|---|
| Sensing | Sharp GP2Y0A21YK0F IR distance sensor (analog, 10–80 cm), one per seat |
| Controller | ESP32 DevKit V1 (30-pin, CP2102 USB-UART) |
| Firmware | Arduino framework, Arduino IDE 2.x |
| Communication | TODO: not selected yet (candidates: ESP-NOW, WiFi + Firebase) |
| Platform signage | TODO: not selected yet |
| Simulation | TODO: not started |

## Folder description :
* ESP32: source code for the esp side (firmware). Open `ESP32/ESP32.ino` in Arduino IDE.
* Documentation: wiring diagram + basic operating instructions
* Unit Tests: tests for individual hardware components (input / output devices)
* flutter_app : dart code for our Flutter app. TODO: confirm whether an app is in scope
* Parameters: `ESP32/parameters.h` holds every tunable setting (pins, thresholds, timings)
* Assets: link to 3D printed parts, Fritzing file for connection diagram (FZZ format) etc

## Documentation index
* [01 Current status and handoff](Documentation/01_CURRENT_STATUS_AND_HANDOFF.md) — read first
* [02 Requirements and scope](Documentation/02_REQUIREMENTS_AND_SCOPE.md)
* [04 Hardware](Documentation/04_HARDWARE.md)
* [05 Wiring and pinout](Documentation/05_WIRING_AND_PINOUT.md)
* [06 ESP32 firmware](Documentation/06_ESP32_FIRMWARE.md)
* [11 Troubleshooting](Documentation/11_TROUBLESHOOTING.md)
* [12 Design decisions](Documentation/12_DESIGN_DECISIONS.md)
* [Open questions](Documentation/OPEN_QUESTIONS.md)

## ESP32 SDK version used in this project:
TODO: fill from Arduino IDE → Boards Manager → "esp32 by Espressif Systems" installed version

## Arduino/ESP32 libraries used in this project:
* None beyond the ESP32 Arduino core (hardware-feasibility stage)

## Connection diagram:
See [Documentation/05_WIRING_AND_PINOUT.md](Documentation/05_WIRING_AND_PINOUT.md). TODO: add Fritzing diagram.

## Project Poster:
TODO

This project is part of ICST - The Interdisciplinary Center for Smart Technologies, Taub Faculty of Computer Science, Technion
https://icst.cs.technion.ac.il/
