# 02 — Requirements and Scope

**Status:** proposed draft. [TODO] confirm with both members and the mentor. Requirement statuses are tracked in [01_CURRENT_STATUS_AND_HANDOFF.md](01_CURRENT_STATUS_AND_HANDOFF.md).

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

| Deliverable | Date | Source |
|---|---|---|
| Hardware feasibility (empty/occupied detection) | 2026-10-04 | [R] course announcement |
| Feature list (written) | TODO | Course rules deck |
| POC | TODO | Course rules deck |
| Final submission / poster | TODO | |

## Main risk

FR-007 must be demonstrable in 2 minutes with a quantitative metric. Per the course rules, any predictive/algorithmic element must have its demonstration method agreed with the mentor in advance. [TODO] agree the metric and demo format early.
