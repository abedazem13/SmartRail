## This folder contains Valdation tests done to check sensors/hardware parts

### ir_sensor_check — GP2Y0A21YK0F bring-up

**Purpose:** confirm both sensors are wired and powered correctly before running the main firmware. It prints each sensor's raw output and noise figure side by side (seat 0 = GPIO34 on the left, seat 1 = GPIO35 on the right) and makes no decisions. One line per second.

**Setup:** wiring as in [Documentation/05_WIRING_AND_PINOUT.md](../Documentation/05_WIRING_AND_PINOUT.md). Open `ir_sensor_check/ir_sensor_check.ino`, upload, Serial Monitor at 115200.

**Pass criteria**

| Check | Expected |
|---|---|
| Hand at ~30 cm in front of one sensor | That sensor's `volt` rises immediately, `cm` ≈ 30; the other side does not change (if it does, the two signal wires are swapped) |
| Nothing in front | `cm` shows `>80` |
| Static object, `noise` column | < 100 mV good, > 150 mV check capacitor / wiring |
| Object at 3–4 cm | computed `cm` goes UP (non-monotonic zone — expected, documents a sensor limit) |

**Calibration table — TODO: fill with measured values**

Place white cardboard at measured distances and record the printed `cm`.

| Seat | True distance [cm] | Printed cm | Volt | Noise [mV] | Date | Operator |
|---|---|---|---|---|---|---|
| 0 | 15 | TODO | | | | |
| 0 | 30 | TODO | | | | |
| 0 | 60 | TODO | | | | |
| 0 | 80 | TODO | | | | |
| 1 | 15 | TODO | | | | |
| 1 | 30 | TODO | | | | |
| 1 | 60 | TODO | | | | |
| 1 | 80 | TODO | | | | |

### Seat occupancy acceptance test (main firmware)

1. Upload `ESP32/ESP32.ino`, keep both seats empty during the 3 s calibration.
2. Record the `CAL` lines: baseline distance and noise of each seat.
3. Perform 10 consecutive sit-down / stand-up cycles on each seat.
4. **Pass:** 10/10 `EVENT ... OCCUPIED` and 10/10 `EVENT ... EMPTY`, no extra events, each within ~2 s.

| Date | Seat | Baseline [cm] | Occupied reading [cm] | Noise [mV] | Cycles passed | Capacitor fitted | Operator |
|---|---|---|---|---|---|---|---|
| TODO | | | | | /10 | | |
