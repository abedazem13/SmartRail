# 02 — Requirements and Scope

**Status:** proposed draft. The concept below is confirmed by the team [R, 2026-09-21]; the requirement table is still a draft. [TODO] confirm with the mentor. Requirement statuses are tracked in [01_CURRENT_STATUS_AND_HANDOFF.md](01_CURRENT_STATUS_AND_HANDOFF.md).

## Project concept [R]

Smart transportation project with three parts:

1. **Seat sensing.** Distance sensors detect whether each train seat is occupied.
2. **Platform signage.** Digital signs at the station tell waiting passengers how to spread out along the platform when the train arrives, so they spread evenly (linear/uniform distribution) instead of bunching around one point (Gaussian distribution).
3. **Simulation.** Simulate passenger arrival and queueing on the platform, Gaussian vs linear, and show the improvement in the train's dwell time at the station.

## Project hypothesis

Spreading waiting passengers evenly along the platform shortens boarding time and therefore the train's dwell time. The simulation exists to quantify that improvement.

## Functional requirements

| ID | Requirement | Acceptance criterion | Priority |
|---|---|---|---|
| FR-001 | Detect whether a seat is empty or occupied | Correct state on 10/10 sit/stand cycles | Must (hardware demo) |
| FR-002 | Automatic empty-seat calibration | Baseline measured at boot; recalibration without recompiling | Must |
| FR-003 | Noise filtering and hysteresis | No state flicker when a seated person shifts or someone passes in the aisle | Must |
| FR-004 | Per-car aggregation | Count of free seats per car | Must |
| FR-005 | Car → platform communication | Platform updated < 3 s after a state change | Must |
| FR-006 | Platform signage | Shows which platform zone passengers should move to | Must |
| FR-007 | Dispersion simulation | Quantitative comparison: Gaussian vs linear distribution, dwell/wait time | Must |
| FR-008 | Visual seat map | Per-seat free/occupied map in a UI | Should |
| FR-009 | Sensor health monitoring | Detect stuck, disconnected or out-of-range sensors and report it | Should |
| FR-010 | Physical platform indicator | NeoPixel strip lights the recommended zones | Could |
| FR-011 | Forgotten-item alert | Occupied seat with no reading change for a long period flagged as a probable object | Could |

## Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-001 | Detection latency ≤ 2 s |
| NFR-002 | Settings (WiFi, thresholds) changeable without recompiling — course robustness criterion |
| NFR-003 | Recover automatically from WiFi disconnection — course robustness criterion |
| NFR-004 | Each feature demonstrable within 2 minutes — course demo rule |
| SAFE-001 | No credentials in Git (see `ESP32/SECRETS.example.h`) |

## Out of scope

Reliable person-vs-object discrimination, counting passengers on the platform, cameras or face recognition, integration with real Israel Railways systems.

## Course deliverables and deadlines

The course rules deck (*IOT project rules – W26*, 236333) defines a 13-week semester. SmartRail runs in the **summer semester**, so these week numbers do not map directly to dates; the team reports it is up to date with the milestones [R, 2026-09-21]. The table shows the order of deliverables.

| Week | Deliverable | Type |
|---|---|---|
| — | Hardware feasibility: detect an empty seat and an occupied seat. 2026-10-04 [R] | Mandatory (team requirement for the hardware submission) [R] |
| 1 | Feature list | Mandatory, written |
| 2 | Final feature list after feedback | Mandatory, written |
| 3 | HW unit tests report | Mandatory, written |
| 5 | Feasibility checks: communication, DB, UI | Recommended |
| 6 | **POC** | Mandatory, attendance required |
| 7 | Enclosure sketch (for manufacturing) | Recommended. Part-manufacturing requests are due up to one week after POC |
| 9 | Edge-case design | Recommended |
| 12 | **Final submission** | Mandatory, attendance required |
| End of semester | Public Git per course guide, poster, project video, return of hardware and locker key | Administrative condition for receiving a grade |

Mandatory deliverables are ungraded but late submission needs written approval from the course TA in charge.

## Course rules that constrain the design

From the course rules deck:

- **Demo:** every feature must be demonstrable at the final submission, with time constants that fit a demo of about 2 minutes per feature. Anything that cannot be demonstrated needs a written alternative agreed with the TA in charge.
- **Algorithmic elements:** agree in advance with the mentor how they will be demonstrated, preferably with a quantitative evaluation. This applies to the simulation (FR-007).
- **Robustness criteria:** WiFi reconnect and offline mode, handling user misuse, recovery from common faults, settings such as WiFi SSID and password changeable from a UI without recompiling, and the system reporting its status (faults, connectivity) to the user.
- **Code and Git quality:** code split into classes, a state machine, and an organized Git with parameters and usage instructions.
- **Scope changes:** adding significant features or new hardware after POC is not recommended.
- **Significant decisions** must be shared in writing with the direct mentor and the TA in charge, together with the reasoning and sources.
- **Power and safety:** low voltage only (≤ 12 V). While connected to a PC over USB, do not connect any other power source (use a USB isolator if needed). Default power is a power bank or USB phone charger.
- **Grading:** all team members receive the same grade. Criteria are the robustness of the final hardware and software, the documentation, and following the project procedures.
- **Technology options offered by the course:** UI: Flutter app, on-board HTTP server, Telegram, Google Sheets. Cloud/DB: Firebase Firestore, Firebase RTDB, Google Sheets, Adafruit.io, local storage (SD card or on-board). Communication: Bluetooth Classic/BLE, WiFi client, WiFi access point, ESP-NOW.

## Main risk

FR-007 must be demonstrable in 2 minutes with a quantitative metric. Per the course rules, any predictive/algorithmic element must have its demonstration method agreed with the mentor in advance. [TODO] agree the metric and demo format early.
