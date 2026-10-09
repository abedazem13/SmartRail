# SmartRail — hardware + dashboard testing handoff for teammates and their AI agent

**Prepared:** 2026-10-09. **Physical hardware validation:** NOT PERFORMED by the implementing agent; Abed does not have the hardware. The earlier hardware presentation happened (reported by Abed); its exact date, result and evidence have not been supplied. Do not infer that this new dashboard was demonstrated or passed.

## Give this file to your agent

> Read this whole handoff and the linked source/documentation. Help us set up and validate the three-car dashboard with our actual ESP32 and two IR sensors. Run the software tests first, guide a human through physical tests one step at a time, preserve evidence, fix only reproduced issues, and report PASS/FAIL/NOT RUN honestly. Do not replace real sensor data with simulated values to make a test pass. Never claim you saw or measured hardware behavior without evidence from the connected device or the human operator. Do not change firmware thresholds or wiring without explaining why and asking the hardware operator to confirm safe changes. Do not commit or push until asked; never include secrets or unrelated work.

## 1. Exact scope

The laptop is the passenger-facing platform display. Three **logical** cars A/B/C each have three seats. This milestone is seat availability only: it does not simulate passenger movement, quantify boarding/dwell time, represent a real approaching train, implement wireless train-to-platform communication, or reserve seats.

| Display seat | Hybrid input | Physical mapping |
|---|---|---|
| A1 | Real, read-only | Firmware seat 0 → first SENSOR_PINS entry → GPIO34 |
| A2, A3 | Simulated, clickable | No hardware |
| B1 | Real, read-only | Firmware seat 1 → second SENSOR_PINS entry → GPIO35 |
| B2, B3 | Simulated, clickable | No hardware |
| C1, C2, C3 | Simulated, clickable | No hardware |

One ESP32 serves both sensors; there are not three physical train-car controllers. In **simulation mode**, all nine seats are editable and no serial port is opened. In **hybrid mode**, exactly two seats are driven by the board and seven remain simulated.

Display rules:
- 2–3 confirmed free, no unknowns: green, “Seats available”.
- 1 confirmed free, no unknowns: yellow, “Limited availability”.
- 0 confirmed free, no unknowns: red, “No free seats” (NOT “car full”: standing capacity is not measured).
- Any unknown seat in a car: gray and explicit known-free + unknown counts. Unknown is never counted free.
- The optional suggestion names the car with the most **confirmed** free seats. Ties retain the previous suggestion; initial ties choose alphabetically. It never reserves/decrements seats and makes no optimization claim.
- Calibration, USB disconnect and >2 s without valid per-seat data make real seats UNKNOWN. During calibration, even CAL lines do not establish passenger-facing availability; fresh post-calibration status is required.
- Losing the dashboard web server clears displayed counts. Automatic browser retry restores them after recovery.

## 2. Read before changing anything

- [Dashboard guide](17_HYBRID_DASHBOARD.md)
- [Current status](01_CURRENT_STATUS_AND_HANDOFF.md)
- [Hardware](04_HARDWARE.md) and [wiring](05_WIRING_AND_PINOUT.md)
- [Firmware](06_ESP32_FIRMWARE.md) and [serial contract](08_COMMUNICATION_AND_DATA.md)
- [Component tests](../Unit%20Tests/README.md)
- [Firmware source](../ESP32/ESP32.ino) and [parameters](../ESP32/parameters.h)
- [Dashboard model](../PC_software/dashboard_model.py), [serial worker](../PC_software/dashboard_serial.py), [server](../PC_software/dashboard.py)

Inspect Git status and record the commit before testing. Preserve local changes. Confirm `NUM_SEATS` is 2 and both sensor pins match the physical prototype. Do not assume an old compiled binary matches current source.

## 3. Software setup (Windows PowerShell)

These commands assume the terminal is in the **SmartRail Git root**, which contains ESP32 and PC_software. They create a local environment only if one does not already exist. Use your team's existing compatible interpreter/environment if preferred; do not copy Abed's machine-specific interpreter path.

Use Python 3.10 or newer. Record the actual Python version and installed package versions. If `py` is unavailable but `python` works, use `python` for the environment-creation command.

```powershell
if (-not (Test-Path .venv)) { py -3 -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -r .\PC_software\requirements.txt
Push-Location .\PC_software
..\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
Pop-Location
.\.venv\Scripts\python.exe .\PC_software\dashboard.py
```

No Node, Flutter, cloud account, API key or internet at runtime is needed. Installing dependencies may require internet. Do not install optional browser-test packages merely to operate the dashboard.

Open:
- Passenger view: http://127.0.0.1:8765/
- Operator view: http://127.0.0.1:8765/controls

Keep both tabs open. Start with simulation mode; only switch to hybrid after the hardware steps below. Full screen uses the button or F11. All tabs share one server state. Browser refresh does not reset seats. Restarting the server resets to simulation/example unless started with `--serial-port COM5`.

If port 8765 is in use, add `--http-port 8766` and use that port in both URLs. The server intentionally listens only on 127.0.0.1. Do not bind to 0.0.0.0, forward it publicly, or assume the local controls have authentication.

### Optional browser regression check

From SmartRail root, install development dependencies, then from PC_software run the browser test:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\PC_software\requirements-dev.txt
.\.venv\Scripts\python.exe -m playwright install chromium
Push-Location .\PC_software
..\.venv\Scripts\python.exe .\tests\browser_dashboard_check.py
Pop-Location
```

Alternatively use installed Edge by setting `$env:SMARTRAIL_BROWSER_CHANNEL = 'msedge'` before the browser test; then the Chromium download is unnecessary. This test uses **fake serial input only**. It does not verify hardware.

## 4. Software acceptance — before connecting the board

Record each result, do not just tick a box because the source exists.

| ID | Action | Expected result |
|---|---|---|
| SW-01 | Start dashboard, open both tabs | Simulation label; A=1 yellow, B=3 green, C=0 red; total=4 |
| SW-02 | Click A1 in controls | A=0 red in both tabs; A1 occupied; passenger page has no seat-edit buttons |
| SW-03 | Click A1 again | A=1 yellow in both tabs |
| SW-04 | Empty all simulated seats | Each car=3 green; total=9 |
| SW-05 | Occupy all simulated seats | Each car=0 red; no free-seat suggestion |
| SW-06 | Example scenario | A=1, B=3, C=0 restored |
| SW-07 | Refresh passenger tab | State persists; it is not browser-local data |
| SW-08 | Stop server with Ctrl+C | Within about 3 s, page shows offline and dashes, not old availability |
| SW-09 | Restart server | Pages recover automatically; default example restored |

## 5. Physical readiness — human operator required

The AI agent must ask the operator for observations; it cannot infer physical wiring from code.

1. Disconnect power before inspecting or rewiring. Follow course low-voltage and USB power rules; do not combine external power and PC USB without an approved isolation/power arrangement.
2. Verify sensor VCC/GND/OUT from the actual part pinout; wire colors alone are not proof. Confirm common ground, supply, GPIO34 and GPIO35 against the wiring document. Do not put 5 V on an ESP32 GPIO.
3. Record whether each sensor has the manufacturer-recommended bypass capacitor. Previous notes say neither was fitted. Follow the datasheet recommendation, observe capacitor polarity and voltage rating, and record actual noise rather than claiming the omission is safe because detection sometimes works.
4. Measure each seat's absolute empty AND occupied distance. Do not place a hand against the sensor face: close-range foldback can report a misleading distance. Existing project guidance targets approximately 15–80 cm; verify against the actual model/datasheet and mounting.
5. Ensure both sensors are firmly mounted and do not point into each other. Measure noise in the actual lighting.
6. Run the existing two-sensor diagnostic sketch first. Preserve its calibration/noise measurements and fill the test table.
7. Compile **current** main firmware in Arduino IDE, select the real board and port, and record ESP32 core version, build output, and upload result. This handoff does not certify compilation on your actual toolchain.
8. In Serial Monitor at 115200, keep seats empty until calibration finishes and regular S0/S1 status appears. Verify independent empty/occupied changes for each sensor.
9. Save raw serial evidence now if using Serial Monitor or seat_live. Then **close Serial Monitor, Serial Plotter, seat_live, seat_status and any other serial reader** before connecting the dashboard. Only one program may own the COM port.

Do not change the existing sensor thresholds to hide a dashboard bug. First separate sensor/firmware behavior from parsing/mapping/UI behavior.

## 6. Connect the real board

1. Keep the dashboard running. In Demo controls, click Refresh ports and choose the board's port, or enter it (e.g. COM5). Do not assume COM5 is correct.
2. Keep both real seats empty and click **Connect hardware · hybrid mode**.
3. The board may reset. Both A1 and B1 must show UNKNOWN while opening/calibrating. Wait for actual live status, not just a fixed delay (about 5 s is typical, not a guarantee).
4. Verify A1 and B1 say **Sensor · locked** and cannot be clicked. All other seven seats remain clickable.
5. Load Example while both physical seats are empty. Expected totals: A=1 yellow, B=3 green, C=0 red.
6. Cover sensor 0 at a valid distance. Only A1 should become occupied; A=0 red. Uncover it; A returns to 1 yellow.
7. Cover sensor 1. Only B1 should become occupied; B=2 green. Uncover it; B returns to 3 green.
8. To show B changing yellow/red with hardware: manually occupy B2 and B3. B is then 1/yellow while physical B1 is empty, and 0/red when B1 becomes occupied.

The firmware makes the detection decision with filtering and ~1 s stable-state confirmation. The browser polls every 0.5 s. Physical-action-to-display latency includes both; measure it rather than promising instant updates or claiming NFR-001 passed.

## 7. Physical integration acceptance

| ID | Action | Expected result / evidence |
|---|---|---|
| HW-01 | Compile/upload and boot current firmware | Actual toolchain passes; both CAL and status entries visible; versions + log captured |
| HW-02 | Ten occupy/vacate cycles on sensor 0 | 10 occupied + 10 empty transitions on A1, no false events; B1 unaffected; record latency and video |
| HW-03 | Ten occupy/vacate cycles on sensor 1 | Same for B1; A1 unaffected |
| HW-04 | Change both sensors and simulated seats together | Correct independent state and totals across all 9 seats in both browser tabs |
| HW-05 | Apply each preset while real seats are occupied | A1/B1 remain controlled by hardware; no preset can force them free |
| HW-06 | Try to click real seat controls | Disabled; HTTP API also rejects manual changes (automated test covers rejection) |
| HW-07 | Unplug board USB during hybrid mode | A1/B1 unknown on detected disconnect or within ~2 s plus one polling interval if stream stops silently; A/B gray; seven simulated seats preserved |
| HW-08 | Plug back in, leave seats empty for calibration | Reconnect to same COM port automatically; unknown during calibration; fresh readings restore state. If Windows assigns a new port, select it and reconnect manually |
| HW-09 | Reset board during operation | Old availability not used during reboot/calibration; fresh status required |
| HW-10 | Switch hybrid → simulation → hybrid | All 9 editable in simulation; switching back resets real seats to unknown until new real data; simulated values never masquerade as hardware |
| HW-11 | Open nonexistent or busy port | Helpful connection error; retry; no automatic switch to simulation; correct port recovers |
| HW-12 | Observe any firmware WARN line | Warning remains visible even as regular status messages continue; investigate cause |

**Do not unplug a live sensor signal wire to demonstrate “sensor health.”** The firmware does not reliably detect a disconnected or stuck sensor. An ADC can keep producing plausible data, so the dashboard cannot infer a sensor fault from that. The 2-second timeout detects missing serial seat updates, not all electrical failures. Power down before hardware changes.

For the formal detection latency requirement, separately measure the board's event delay and the dashboard's display delay. Record both. Do not change the acceptance target or mark it passed without measurements.

## 8. Evidence and result file to create

Create a dated Markdown report in `Documentation/assets/test-results/`, using a descriptive name such as `hybrid-dashboard-hardware-YYYY-MM-DD.md`. This report must contain:

- Git commit tested and whether the worktree was dirty; exact file changes if relevant.
- Test operator, date, OS, browser/version, Python/package versions, Arduino IDE/core version, board and sensor models, COM port.
- Wiring photo showing GPIO34/35 and power; capacitor status per sensor; measured distances/noise.
- Every SW/HW ID with PASS / FAIL / NOT RUN, actual observations, timing, and evidence links.
- The two 10-cycle tables: cycle, occupied delay, empty delay, unexpected transitions, result.
- A clear label distinguishing hardware measurements from mocked automated tests.
- Screenshots/video of the two views, sensor mapping, live transition, USB loss and recovery.
- Remaining issues with owners and next actions; do not invent measurements, dates or approval.

**The dashboard does not save raw serial sessions automatically.** Its “last board message” is transient diagnostics, not evidence logging. Preserve a video/screen recording during the dashboard test. To collect a raw log separately, switch dashboard to simulation (releasing the port), then run the existing `seat_live.py --port COM5 --log <descriptive-file>` workflow and repeat the physical sequence. Stop it before reconnecting the dashboard. Do not present a separately captured console run as a simultaneous dashboard capture. Keep large videos outside Git and link an approved shared location; sanitize all evidence.

After real results exist, update the current-status document and changelog with facts and links. Re-run automated tests after code changes. Keep a failed test as regression coverage when fixing a software bug.

## 9. Failure triage

| Symptom | Check first |
|---|---|
| Browser page cannot load | Python server running, terminal error, correct HTTP port and URL |
| Missing Flask/serial/waitress | Install requirements using the SAME interpreter used to launch |
| No COM port | USB data cable/driver/port identification; simulation remains available |
| Access denied / port busy | Close all other serial applications; let dashboard retry |
| USB open but no seat data | Correct firmware/115200 baud/NUM_SEATS=2; inspect last board message and raw console output separately |
| Only A1 updates | Confirm firmware emits S1 too, GPIO35 wiring, physical sensor 1, calibration; no fake fallback |
| Wrong car changes | Sensor ordering: firmware index 0→A1, index 1→B1; identify physically instead of swapping arbitrary code |
| False detection or high noise | Supply/capacitors/common ground/mounting/range/light before adjusting thresholds |
| Stuck calibration state | Inspect completion line and actual board resets; current dashboard intentionally waits for fresh post-calibration status |
| Yellow expected but gray shown | Gray means at least one real seat is unknown; do not count it free |
| Hybrid example differs from 1/3/0 | Those totals require both physical seats empty; presets only affect simulated seats |

## 10. Agent's completion report

Return: setup performed, tests actually run, software-only vs physical results separately, evidence paths, reproduced bugs and exact fixes, remaining blockers, and whether the hybrid demo is ready. Never declare “hardware verified” based on the browser test, a fake serial source, compile mocks or the earlier presentation alone.