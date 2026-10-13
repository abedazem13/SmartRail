# SmartRail — final-version validation record

**Template only. No test results are claimed here.** Copy this to a dated report or fill it during real execution. Preserve exact observations and supporting evidence. Do not mark source inspection, a test plan or a mock serial message as physical validation.

Status values: **PASS**, **FAIL**, **NOT RUN**, or **BLOCKED** with a reason. Use “source reviewed” separately if that is all that happened. This package creation did not execute the current suite or hardware tests.

## 1. Identification and environment

| Field | Recorded value |
|---|---|
| Test date/time/timezone | TODO |
| Human operator(s) | TODO |
| Git commit and branch | TODO |
| Worktree clean? If not, list changes | TODO |
| OS and laptop | TODO |
| Python interpreter/version | TODO |
| Flask / pyserial / Waitress versions | TODO |
| Browser/version and viewport or display resolution | TODO |
| Test framework/browser automation versions, if used | TODO |
| Arduino IDE / ESP32 core / selected board | TODO |
| Firmware source revision and upload result | TODO |
| Board and sensor model labels | TODO |
| Serial port / baud | TODO / expected 115200 |
| Sensor 0 / 1 physical mapping | TODO / expected GPIO34→A1, GPIO35→B1 |
| Local-only or LAN display? Network arrangement | TODO |
| Approved scope / mentor confirmation reference | TODO |

## 2. Software results — no physical device required

| ID | Check / expected behavior | Status | Actual result and evidence |
|---|---|---|---|
| SW-01 | Current unittest suite completes successfully | NOT RUN | Record command, actual count, output and exit result |
| SW-02 | Browser automation completes or manual equivalent is explicitly identified | NOT RUN | Record which method, browser/version and results |
| SW-03 | Example: 12×108 seats, 311 free, station 1, suggestions L/J/E | NOT RUN | |
| SW-04 | Simulation click on A1: originally occupied, becomes empty; A count 12→13 | NOT RUN | Restore example afterward |
| SW-05 | Both tabs update; passenger page cannot edit seats | NOT RUN | |
| SW-06 | Empty/occupied presets affect all software seats; reset station to 1 | NOT RUN | Auto stopped first |
| SW-07 | One Next stop increments station and animates over roughly 2.4 s within population bounds | NOT RUN | Record before/after counts; do not demand predetermined random totals |
| SW-08 | Auto stops start/stop; pending stop behavior understood | NOT RUN | Record interval and stop behavior |
| SW-09 | Modes/presets do not silently disable auto; mode change does not reset station | NOT RUN | Verify current documented behavior |
| SW-10 | Missing server → old counts hidden; restart → pages recover | NOT RUN | Timing and screenshot |
| SW-11 | Simulated missing/stale serial data cannot be counted free; real-seat API writes rejected in hybrid | NOT RUN | State clearly if only automated fake input was used |
| SW-12 | Optional LAN view works; remote controls/port listing/mutations refused | NOT RUN | Real device/network or Flask test-client method? Record which |
| SW-13 | Passenger screen readable on intended projector/laptop; controls usable | NOT RUN | Resolution/photo or screenshot |

Raw console output / software evidence references: TODO. A historic report from 9 October is not a new test run for this revision.

## 3. Physical conditions

| Measurement | Sensor 0 / A1 | Sensor 1 / B1 |
|---|---|---|
| Model/part label | TODO | TODO |
| Measured supply voltage | TODO | TODO |
| Bypass capacitor fitted, value/rating/polarity checked | TODO | TODO |
| Absolute empty distance | TODO | TODO |
| Absolute occupied distance | TODO | TODO |
| Calibration baseline | TODO | TODO |
| Calibration noise in mV | TODO | TODO |
| WARN messages / interpretation | TODO | TODO |
| Mounting, lighting, target and possible interference | TODO | TODO |

Attach an actual wiring photo and component diagnostic measurements. Never infer absolute occupied distance merely by subtracting an informal reported gap. Do not change powered sensor wiring during testing.

## 4. Hardware integration acceptance

| ID | Check / expected behavior | Status | Actual result and evidence |
|---|---|---|---|
| HW-01 | Actual firmware compile/upload succeeds on recorded toolchain | NOT RUN | |
| HW-02 | Calibration keeps A1/B1 unknown until fresh occupancy status | NOT RUN | Capture actual markers/UI |
| HW-03 | Sensor 0 affects only A1; sensor 1 affects only B1 | NOT RUN | |
| HW-04 | With auto off and all simulated seats occupied, empty A1/B1 give A=1, B=1, total=2 | NOT RUN | |
| HW-05 | Physical occupy/vacate changes correct count/color and leaves other sensor unaffected | NOT RUN | |
| HW-06 | Ten complete cycles per sensor without unexpected events | NOT RUN | Fill cycle table below |
| HW-07 | Manual controls/presets/Next stop/auto cannot overwrite real seats | NOT RUN | |
| HW-08 | USB unplug → both real seats unknown, simulated state preserved | NOT RUN | Measured delay and screenshot/video |
| HW-09 | USB replug → retry/recalibration/fresh data restore correct state | NOT RUN | Same/new COM port? |
| HW-10 | Board reset during operation does not present calibration as valid availability | NOT RUN | |
| HW-11 | Busy/wrong port fails visibly without fake fallback | NOT RUN | Close competing reader afterward |
| HW-12 | Actual end-to-end latency and false events recorded | NOT RUN | Separate firmware delay from display delay where measurable |

The requirements draft specifies correct state on 10/10 cycles and detection latency ≤2 s. Record actual measured values and the agreed measurement definition. Do not silently relax criteria or infer latency from constants. A full sensor-fault detection claim cannot be established merely by unplugging USB.

## 5. Ten-cycle measurements

Record sensor 0 and sensor 1 separately. “Occupied delay” and “empty delay” must state whether they end at the firmware event or visible dashboard change. Use measured seconds or “not measured”, never invented precision.

| Sensor | Cycle | Occupied delay (s) | Empty delay (s) | Unexpected / missed events | Result / evidence |
|---|---:|---|---|---|---|
| 0 / A1 | 1 | — | — | — | NOT RUN |
| 0 / A1 | 2 | — | — | — | NOT RUN |
| 0 / A1 | 3 | — | — | — | NOT RUN |
| 0 / A1 | 4 | — | — | — | NOT RUN |
| 0 / A1 | 5 | — | — | — | NOT RUN |
| 0 / A1 | 6 | — | — | — | NOT RUN |
| 0 / A1 | 7 | — | — | — | NOT RUN |
| 0 / A1 | 8 | — | — | — | NOT RUN |
| 0 / A1 | 9 | — | — | — | NOT RUN |
| 0 / A1 | 10 | — | — | — | NOT RUN |
| 1 / B1 | 1 | — | — | — | NOT RUN |
| 1 / B1 | 2 | — | — | — | NOT RUN |
| 1 / B1 | 3 | — | — | — | NOT RUN |
| 1 / B1 | 4 | — | — | — | NOT RUN |
| 1 / B1 | 5 | — | — | — | NOT RUN |
| 1 / B1 | 6 | — | — | — | NOT RUN |
| 1 / B1 | 7 | — | — | — | NOT RUN |
| 1 / B1 | 8 | — | — | — | NOT RUN |
| 1 / B1 | 9 | — | — | — | NOT RUN |
| 1 / B1 | 10 | — | — | — | NOT RUN |

Timing method and limitations: TODO. If raw serial output is collected with a separate console tool, release the dashboard's serial port first. Label that as a separate run. The dashboard's latest-message field is not a saved log.

## 6. Evidence inventory

| Item | Captured when / revision | Mode and physical/fake source | File/link and caption |
|---|---|---|---|
| Passenger example screenshot | TODO | TODO | TODO |
| Control-map screenshot | TODO | TODO | TODO |
| Wiring photo | TODO | Physical | TODO |
| Sensor transition video | TODO | TODO | TODO |
| Disconnect/reconnect video | TODO | TODO | TODO |
| Software test output | TODO | No hardware unless explicitly stated | TODO |
| Separate raw serial log, if collected | TODO | TODO | TODO |

Follow [assets/README.md](assets/README.md). Evidence must actually exist and be accessible before replacing TODO with a link.

## 7. Conclusion

- Passed checks: TODO.
- Failed checks, reproduction and owner: TODO.
- Not run / blocked checks and reason: TODO.
- Changes made after testing and required retests: TODO.
- What may honestly be demonstrated live: TODO.
- Approved limitations / staff decision reference: TODO.
- Final readiness decision and reviewers: TODO.

**No dwell-time improvement, wireless ESP32 integration or production readiness is established by these tests.** Evaluate those separately if required by the milestone.