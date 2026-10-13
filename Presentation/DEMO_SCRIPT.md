# SmartRail — rehearsal and live demo script

**Baseline:** 12 cars × 108 seats; physical A1/B1 in hybrid mode. Suggested live sequence: 3–4 minutes, adaptable to the staff's allowance. This is a procedure, not evidence that the hardware steps already pass.

## Before the audience arrives

- Follow [USER_MANUAL.md](USER_MANUAL.md) to install and start the exact tested revision.
- Prepare one passenger tab and one control tab. Fullscreen the passenger view when speaking about passengers.
- Keep the terminal running; close Arduino Serial Monitor/Plotter and other serial readers before hybrid mode.
- Ask the hardware operator to confirm wiring, stable mounting, supply/capacitors and valid detection range. Do not rewire powered hardware.
- If auto stops are on, **stop them explicitly**. Wait for BOARDING to finish, then load the chosen preset. Presets reset the station counter but do not disable auto stops.
- Confirm the physical setup passed rehearsal; record the tested commit and evidence. Have an honest fallback ready.
- If using a phone, test its connection first on a trusted hotspot. Keep a laptop-only option; phone viewing is optional.

## Sequence 1 — show the complete software train (about 45 seconds)

**Operator:** select Use simulation, stop auto stops if needed, load Example scenario.

**Narrator:**
> This is the passenger view of a logical 12-car train. We display confirmed availability by car and the matching platform zones. These values are simulated in this mode.

Expected source-defined example:

| Car | A | B | C | D | E | F | G | H | I | J | K | L |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Free | 12 | 3 | 0 | 25 | 48 | 7 | 36 | 18 | 1 | 60 | 29 | 72 |

Total: **311 free / 1,296 seats**, station 1. Suggestions: **L, J, E**. A1 and B1 happen to be **occupied** in this software example; this is not a physical measurement.

Show one manual change in controls, then the corresponding passenger count. Restore Example before the next segment.

## Sequence 2 — simulated station (about 30 seconds)

**Operator:** press Next stop once. Wait for BOARDING to finish before another press.

**Narrator:**
> This is a random demonstration of passengers leaving and boarding. It updates simulated seats over about 2.4 seconds; it is not a model proving shorter dwell time.

Expected:
- Station advances to 2 immediately.
- Simulated seats empty first, then fill; totals/suggestions may change.
- Do not promise exact counts for a random stop.
- Optional: enable auto stops for one interval, then stop them. Do not leave auto running during the physical demonstration.

## Sequence 3 — make the two physical sensors easy to see (about 90 seconds)

### Prepare the physical scene

1. Keep both physical seats empty, select the actual port and connect hybrid mode.
2. Wait for calibration completion **and fresh sensor states**. Initially unknown is expected. Do not keep pressing Connect—it can restart calibration.
3. Verify A1/B1 are marked Sensor and locked. Confirm their initial EMPTY states in diagnostics.
4. Stop auto stops. Click **Occupy simulated seats**. This does not modify A1/B1.

With both physical sensors reporting EMPTY, expected totals are:

| Item | Expected |
|---|---|
| A1 / B1 | Free, physical, read-only |
| Car A / B | 1 free each, amber |
| Cars C–L | 0 free, red |
| Whole train | 2 confirmed free |
| Suggested cars | A and B, tied alphabetically |

This scene deliberately puts each real sensor at the **one-seat / zero-seat boundary**, so the audience sees a color and count change even though each car has 108 logical seats.

### Demonstrate

| Human action | Expected physical change | Expected passenger output |
|---|---|---|
| Place a target at a valid occupied distance from sensor 0 | A1 → OCCUPIED after firmware confirmation | A: 1→0, amber→red; B stays 1; total 1 |
| Remove target from sensor 0 | A1 → EMPTY | A: 0→1, red→amber; total 2 |
| Repeat with sensor 1 | B1 changes independently | B count/color changes; A unaffected |
| Optional: occupy both | A1/B1 occupied | Total 0, no free-seat suggestion |

**Narrator:**
> These two changes came from physical sensors. The ESP32 filtered the readings and confirmed the state; the laptop received the message and updated the same model as the simulated seats.

The firmware has a one-second confirmation period plus sampling/filtering; browser polling adds delay. State measured latency from the rehearsal, not a guessed “instant” response. Keep targets in the validated range rather than against the sensor face.

## Sequence 4 — safe handling of lost data (about 30 seconds)

1. With stable readings, unplug the board's USB cable—not a powered sensor wire.
2. A1/B1 become unknown on detected disconnect, or after stale-data timeout if the stream merely stops.
3. A/B become gray, not automatically free. Simulated seats remain as configured.
4. Reconnect; leave seats empty for recalibration and wait for fresh data. If the operating system changes the COM name, select the new port.

**Narrator:**
> Missing information is shown as unknown. This is serial-data failure handling, not a guarantee that every electrical sensor fault can be detected.

## Optional network screen

Use the network launcher only on a trusted network; open the printed LAN URL on the phone. It should show the same counts, while the laptop retains the controls. Say: “The phone is a second passenger display. The sensor link is still USB.” Do not spend the live slot troubleshooting campus Wi-Fi; switch back to the laptop.

## Closing sentence

> We have demonstrated simulated multi-car availability, two physical sensor inputs when connected, passenger-facing updates and missing-data handling. We have not demonstrated a full physical train deployment or quantified boarding-time improvement.

## Recovery and fallback

| Problem | Response |
|---|---|
| Wrong counts or unexpected motion | Stop auto, wait/cancel pending stop with a preset, verify mode and real-seat state; do not silently overwrite physical inputs |
| Busy COM port | Close all other serial applications; retry the correct port |
| Calibration seems wrong | Empty both seats and reset the board; inspect diagnostics; do not recalibrate with the target present |
| No hardware available or repeatable failure | Explicitly switch to simulation. Explain that hardware integration cannot be shown live; use a labeled recording only if it is from an actual test |
| Phone cannot connect | Continue on laptop; no change to core demo |
| Dashboard process stops | Counts should show offline. Restart using the tested launcher; demo state resets |
| Presenter loses time | Skip auto stops and phone display; keep explanation, one physical transition, simulated transition and honest limitations |

Before trying these steps live, complete [the test report](TEST_RESULTS_TEMPLATE.md). A procedure with expected results is not a test result.