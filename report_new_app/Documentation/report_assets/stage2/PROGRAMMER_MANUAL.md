# SmartRail — programmer manual

**Purpose:** let another developer understand, reproduce and safely extend the presentation implementation.  
**Source baseline:** `0883d93`, inspected 13 October 2026. No code changes, new test execution or physical validation were performed to produce this manual. Use the actual tested commit in the final report.

## 1. Architecture and responsibilities

The ESP32 owns the calibrated sensor-to-occupancy decision. Python receives that decision, adds unknown/data-age handling, combines it with simulated seats, and exposes shared snapshots to browser views. One serial thread serves all tabs.

| File | Responsibility |
|---|---|
| [ESP32.ino](../ESP32/ESP32.ino) | ADC sampling, calibration, median filtering, occupancy state machine, serial output |
| [parameters.h](../ESP32/parameters.h) | Firmware pin mapping, thresholds, timing and sensor conversion constants |
| [seat_live.py](../PC_software/seat_live.py) | Existing `Board`/`Seat` parser, regular expressions, stale logic; also a standalone console program |
| [dashboard_model.py](../PC_software/dashboard_model.py) | `DemoModel`, logical seats, source protection, counts/ranking, simulated stations |
| [dashboard_serial.py](../PC_software/dashboard_serial.py) | `SerialWorker`, bounded `LineBuffer`, serial ownership, retry and shutdown |
| [dashboard.py](../PC_software/dashboard.py) | Flask `create_app()`, API validation, local/network access checks, Waitress entry point |
| [app.js](../PC_software/dashboard_web/app.js) | Shared passenger/control rendering, compact-state decoding, polling, operations and offline UI |
| [index.html](../PC_software/dashboard_web/index.html) | Both views' structure and controls |
| [style.css](../PC_software/dashboard_web/style.css) | Responsive visual design, status colors and seat map |
| [test_dashboard.py](../PC_software/tests/test_dashboard.py) | Model, HTTP and fake-serial regression tests |
| [browser_dashboard_check.py](../PC_software/tests/browser_dashboard_check.py) | Browser integration checks using synthetic firmware input |

The older [guidance.py](../PC_software/guidance.py) passenger-assignment demo is imported by the console software but is **not** the dashboard's recommendation algorithm. Dashboard recommendations are computed in `DemoModel.snapshot()`.

## 2. Dependencies and operation

- Python 3.10+; Flask 3.1.2, pyserial 3.5, Waitress 3.0.2, pinned in [requirements.txt](../PC_software/requirements.txt).
- Optional browser checks: Playwright 1.63.0 from [requirements-dev.txt](../PC_software/requirements-dev.txt), plus Chromium or installed Edge.
- Vanilla HTML/CSS/JS: no Node toolchain, CDN or external font dependency.
- Firmware: Arduino IDE 2.x with ESP32 core. The newer setup documentation reports 3.0.7; record actual installed version/build output rather than relying on older TODOs.

Follow [USER_MANUAL.md](USER_MANUAL.md) for setup. Launchers assume a repository-root virtual environment. The server defaults to localhost:8765; CLI options are `--http-port`, `--serial-port` and `--host`. Source paths for web assets are resolved relative to the server file, not the shell's current directory.

## 3. Model and source mapping

Current constants in `dashboard_model.py`:

| Constant | Value / role |
|---|---|
| `NUM_CARS` | 12; IDs A–L |
| `SEATS_PER_CAR` | 108; seat IDs A1–A108 through L1–L108 |
| `TOTAL_SEATS` | 1,296 |
| `REAL_SENSORS` | 2; asserted against map length |
| `SENSOR_MAP` | A1→firmware 0, B1→firmware 1 |
| `AVAILABLE_FREE_MIN` | 10 confirmed free seats for green |
| `RECOMMEND_CARS` | 3 |
| `STOP_ANIMATION_S` | 2.4 |
| `STOP_MIN_FRACTION` / `STOP_MAX_FRACTION` | 0.05 / 0.20 |
| `AUTO_INTERVAL_MIN` / `AUTO_INTERVAL_MAX` | 3 / 300 s; zero disables |

`simulated` stores EMPTY/OCCUPIED for every logical ID. In hybrid mode, `_seat_view()` substitutes the two real states from the `Board`; stored simulated values never fill gaps in real data. Switching back to simulation intentionally shows the last software values, not physical readings.

Simulation starts from a deterministic example: free counts `(12, 3, 0, 25, 48, 7, 36, 18, 1, 60, 29, 72)`. Seat placement uses `(number * 37) % 108 < free_count`. A1/B1 are occupied in that example. Total free = 311; occupied = 985. In hybrid mode those two values depend on hardware, so do not assert the software-only total unconditionally.

All public operations use an `RLock`. `configure()` increments a generation and resets the board state. The serial worker tags transport/data callbacks with that generation; late callbacks from an old mode or port cannot overwrite the current model.

## 4. State invariants and aggregation

- EMPTY = confirmed free; OCCUPIED = confirmed occupied; UNKNOWN = not currently established.
- A1/B1 cannot be edited through `set_seat()` in hybrid mode. Presets and simulated stops exclude them too.
- Per car: `free + occupied + unknown == total`.
- Unknown seats do not increase `free` and do not count as occupied in the occupancy percentage.
- Car status: `unknown` if any unknowns; otherwise `full` if free=0, `available` if free≥10, else `filling`.
- Occupancy percentage is confirmed occupied / total × 100, rounded to one decimal. Do not use `100 - occupancy_pct` as a guaranteed free percentage if unknowns exist.
- Suggestions rank cars with confirmed free seats by descending `free`, then alphabetical ID. Take at most three. Unlike the old nine-seat implementation, ties do not retain a previous preference.
- Ranking does not mutate seat states, reserve seats, count waiting passengers or quantify boarding-time benefit.

## 5. Firmware behavior and protocol

Current [parameters](../ESP32/parameters.h): two ADC1 sensor pins GPIO34/35, LED GPIO2/4, 40 ms sample interval, 11-sample median window, 500 ms status interval. Calibration waits 3 s and fills each sensor's window twice to establish an empty baseline. The team must keep physical seats empty throughout.

Distance conversion uses `29.988 * V^-1.173`, with low-voltage handling and 10–90 cm output clamps. These are firmware values, **not a guarantee of valid physical sensing across that entire interval**. Very close targets can produce misleading readings; use the sensor datasheet and measured mounting geometry.

Occupancy compares filtered distance with baseline-relative margins: enter at baseline−20 cm; exit when the occupied condition at baseline−12 cm ceases. A changed condition must persist for 1,000 ms. Noise above 150 mV or baseline outside 20–75 cm triggers a calibration warning. Do not infer actual accuracy/latency from these constants alone.

Serial is 115200 baud. Examples below are **illustrative protocol values**, not measured evidence:

```text
SmartRail seat occupancy - GP2Y0A21YK0F
--- CALIBRATION: keep all seats EMPTY. starting in 3 s ---
CAL seat=0 baseline=58.4cm mv=566 noise=38mV
--- calibration done ---
S0 dist= 58.3cm base= 58.4cm noise= 52mV EMPTY   S1 dist= 27.5cm base= 59.0cm noise= 30mV OCCUPIED
EVENT seat=0 state=OCCUPIED dist=23.6cm
```

The full two-seat calibration emits a CAL entry for each sensor. Status may include a `?` pending-confirmation marker and optional raw-voltage diagnostics. `c` requests recalibration and `d` toggles raw debug output through serial; the dashboard does not provide these as control endpoints. To use another serial tool, release the dashboard's port first.

`seat_live.py` regular expressions define the parser contract. Changing firmware print formats requires corresponding parser and test updates. Consult [communication documentation](../Documentation/08_COMMUNICATION_AND_DATA.md) for serial fields, but use this manual for the current HTTP/train model.

## 6. Calibration, stale data and serial lifecycle

- Opening the port may reset the ESP32. Real seats start unknown.
- Boot/calibration-start resets the tracked board and sets calibrating.
- CAL messages supply baseline/diagnostic information but do not make seats passenger-visible as free during calibration.
- After calibration-done, the dashboard explicitly waits for a fresh status/event before establishing occupancy.
- Per-seat stale threshold is more than 2 s (`STALE_S` in `seat_live.py`). Status normally arrives every 0.5 s; one missing seat can age out independently.
- Detected transport disconnect resets both real seat values immediately. `SerialWorker` retries opening/reading roughly every second. It does not switch to simulation on failure.
- One serial handle is shared through the server, not one per browser tab. Closing a tab does not release hybrid mode; switching to simulation or shutting down does.
- `LineBuffer` handles partial reads/CRLF, replaces invalid UTF-8 and discards lines longer than its 4,096-byte limit including their tails.
- WARN messages are retained visibly, bounded in number, until a new boot/calibration or mode setup clears them. They are not a complete sensor-fault diagnosis.
- Sensor disconnection that still produces plausible firmware messages is not automatically detectable. USB/stream stale handling is not full `FR-009` health monitoring.

## 7. Simulated station state machine

`next_stop()` applies currently due changes and schedules a new stop. `_run_stop()` samples only editable simulated IDs:

1. Select a rounded random 5–20% of currently occupied simulated seats to alight, at least one if nonempty, capped at population size.
2. Select a rounded random 5–20% from previously free seats plus newly alighted seats to board, with the same minimum/cap rules.
3. Spread alighting over the first 1.2 s, boarding over the second 1.2 s.
4. Increment the station counter immediately; `boarding` reflects whether pending changes remain.

These fractions apply to the eligible population across cars, not to exactly that fraction in each individual car. Rounding/minimum-one matters for small populations. Selection is random; the deterministic example preset does not make later stops deterministic.

`snapshot()` advances due changes and automatic stops using a monotonic clock. Automatic operation is request/poll-driven, not a background simulation timer. A long gap in polling does not replay every missed station at real-time frequency.

| Operation | Pending changes | Station counter | Auto setting |
|---|---|---|---|
| Click one seat | Cancels pending changes for that seat only | Preserved | Preserved |
| Scenario preset | Clears all | Resets to 1 | Preserved |
| Mode/port configuration | Clears all | Preserved | Preserved |
| Stop auto (`0`) | Existing pending changes can finish | Preserved | Disabled |
| Restart server | New model | 1 | Disabled |

For clean demonstrations, explicitly stop auto and wait/apply a preset. Do not rapidly queue manual Next stop calls while another animation is active; the UI normally prevents this. The backend is a demo mechanism, not a validated railway event scheduler.

## 8. HTTP API

JSON input is required for mutations. Body size is limited to 4,096 bytes. String fields are validated by the route helper; invalid operations produce an error rather than silently changing mode/source. Some framework errors return HTML, so callers should not assume every failure body is JSON.

| Method / path | Body / purpose |
|---|---|
| GET `/` | Passenger page |
| GET `/controls` | Local operator page |
| GET `/api/state` | Shared compact snapshot; also advances due simulated events |
| GET `/api/ports` | Local serial port list; does not open a port |
| POST `/api/mode` | `{"mode":"simulation","port":""}` or `{"mode":"hybrid","port":"COM5"}` |
| POST `/api/seats/A2` | `{"state":"EMPTY"}` or `{"state":"OCCUPIED"}` |
| POST `/api/preset` | `{"name":"example"}`, `{"name":"empty"}`, `{"name":"occupied"}` |
| POST `/api/next_stop` | `{}`; schedule a simulated stop |
| POST `/api/auto` | `{"interval":"10"}` or `{"interval":"0"}`; route expects a string, model parses seconds |

Top-level snapshot contains `mode`, `generation`, `station`, `auto_interval`, `boarding`, train dimensions, totals, `recommended` (list), `message`, `connection`, `warnings` and `stale_s`.

Each car contains `id`, `zone`, `free`, `occupied`, `unknown`, `total`, `occupancy_pct`, `status`, **`states`** and **`seats`**:
- `states` is a 108-character string: `E`, `O` or `U` per seat in numeric order; character 0 = seat 1.
- `seats` contains detailed records only for the mapped sensor positions, not every seat. It can include A1/B1 as simulated records in simulation mode; always inspect `source`, not just `sensor_id`.
- Detailed records include source/state/editability, reason, distance in cm, noise in mV, pending flag and age in seconds; diagnostics can be null.

Clients must not interpret `len(car.seats)` as the car's capacity or treat a gray car's known-free count as zero. UI code decodes the compact state strings for the large control map.

## 9. Frontend and network behavior

The same HTML/JS bundle serves both views; pathname selects the control UI. Browser polling occurs around every 500 ms with a 2.5 s request timeout. Shared server state synchronizes tabs/devices; request sequencing protects the UI against outdated in-flight responses. Failed state polls hide old counts and display offline; successful polls restore the display.

The server defaults to 127.0.0.1. `--host 0.0.0.0` exposes viewing to the local network and prints a detected LAN address. Flask Host checks, same-origin JSON mutation checks, no-store responses and a content security policy are present. Remote clients are denied the controls route, port list and non-GET requests; local controls require access from loopback, not the host's LAN URL.

This is not authentication, encryption or a production security design. Network viewers can access state snapshots, so use only a trusted network, never a public tunnel. Do not put a reverse proxy in front without redesigning/testing trust checks: a proxy can make remote requests appear local. No credentials or personal passenger identities are needed for the demo.

## 10. Build and test workflow

Firmware: open [ESP32.ino](../ESP32/ESP32.ino) in Arduino IDE, select the actual ESP32 board/COM port, compile/upload, and record toolchain versions. Do not assume an old binary corresponds to current source or guess a flashing offset. Preserve the tested build's provenance.

Software tests, from SmartRail root after installing dependencies:

```powershell
Push-Location .\PC_software
..\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
Pop-Location
```

Optional actual-browser checks (fake serial inputs, still not hardware tests):

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\PC_software\requirements-dev.txt
.\.venv\Scripts\python.exe -m playwright install chromium
Push-Location .\PC_software
..\.venv\Scripts\python.exe .\tests\browser_dashboard_check.py
Pop-Location
```

Alternatively use installed Edge: set `$env:SMARTRAIL_BROWSER_CHANNEL = 'msedge'` before the browser test and omit the Chromium download. Record the actual interpreter, browser version, test count, exit result and revision. Do not hardcode an old reported test count as current proof.

Visible test coverage includes dimensions/example, ranking, simulated stop bounds/timing, auto stops, real-input protection, stale/calibration handling, generation guards, validation/network access, framing and fake reconnects. Browser tests cover both views and synthetic events. Physical tests remain a separate human/device procedure in [TEST_RESULTS_TEMPLATE.md](TEST_RESULTS_TEMPLATE.md).

## 11. Changing or extending the implementation

### Change train size

Review `NUM_CARS`, `SEATS_PER_CAR`, the example tuple length, `SENSOR_MAP`, and the scatter rule. The current scatter multiplier is coprime with 108; another seat count may need a different permutation to preserve exact totals. Also update hardcoded UI text, labels, thresholds, tests and manuals. Changing one constant is not guaranteed to produce a consistent presentation.

### Add real sensors

Update wiring and firmware `NUM_SEATS`/pin arrays with safe ADC choices. Update the parser's tracked board mapping, `SENSOR_MAP`, `REAL_SENSORS`, model and UI assumptions, diagnostics, tests and docs. Adding only a display mapping is insufficient if the `Board` still tracks just two firmware IDs. Hardware acceptance is required.

### Change recommendation policy

Keep it separate from measured availability. Add deterministic tests, document tie handling/unknowns, and do not reduce free counts merely because a passenger was advised to go somewhere. A passenger-flow study needs a defined model, equal comparison conditions, repeated trials and a mentor-approved metric.

### Introduce wireless transport

Define an explicit message schema, device/car/seat identifiers, freshness, reconnection, authentication and trust boundaries first. Preserve unknown-on-missing semantics. Viewing the laptop page over Wi-Fi is not this feature.

### Change serial messages or persistence

Modify producer/parser/tests together. The current server is memory-only; session restart resets data. If adding a database/log, define retention, privacy and timestamps. The latest-message UI is not a raw session recorder.

## 12. Known boundaries

No accepted dwell-time performance claim, no full sensor-health guarantee, no real train location feed, no complete wireless deployment, no reservations, no production authentication, no persistent dashboard sessions. The proposed requirements remain subject to mentor confirmation. Use [READINESS_CHECKLIST.md](READINESS_CHECKLIST.md) and [TEST_RESULTS_TEMPLATE.md](TEST_RESULTS_TEMPLATE.md) to close acceptance/evidence gaps rather than claiming success from source inspection.