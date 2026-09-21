# 04 — Hardware

Provenance: **[V]** verified (photo/datasheet), **[R]** reported by a member, **[TODO]** unknown.

## Bill of materials

| ID | Part | Qty | Purpose | Key specs | Interface | Status |
|---|---|---|---|---|---|---|
| HW-01 | ESP32 DevKit V1, 30-pin, CP2102 USB-UART [V] | 1 | Seat controller | 3.3 V logic, ADC1 on GPIO32–39 | USB (CP210x VCP driver) | In use |
| HW-02 | Sharp GP2Y0A21YK0F IR distance sensor [R] | 2 | Seat occupancy | Supply 4.5–5.5 V, ~30 mA avg, range 10–80 cm, update ~38 ms | Analog voltage out, max ~3.1 V | 2 in use [R, 2026-09-21] |
| HW-03 | Electrolytic capacitor 10 µF (≥ 10 V) | 1 per sensor | Supply bypass for pulsed sensor current | Place right next to the sensor | — | **Not fitted — member's choice** [R, 2026-09-21]. Fit if `noise` > ~150 mV |
| HW-04 | Ceramic capacitor 100 nF (optional) | 1 per sensor | High-frequency bypass, parallel to HW-03 | — | — | Optional |
| HW-05 | Breadboard + jumper wires | — | Prototype wiring | — | — | In use |
| HW-06 | USB cable with data lines | 1 | Power + programming | Charge-only cables will not show a COM port | USB | In use |
| HW-07 | LED + 220–330 Ω resistor | 1 | Status LED for seat 1 (seat 0 uses on-board LED) | — | GPIO4 | Not in hand |

Datasheet: Sharp GP2Y0A21YK0F. [TODO] add link and supplier links.

## Sensor behaviour to understand

- **Output is not linear.** Distance fit used by the firmware: `d[cm] = 29.988 · V^-1.173` (course datasheet slide).
- **Non-monotonic below ~8 cm.** An object pressed against the sensor gives the same voltage as one far away. The mounting must keep every real reading above ~15 cm.
- **Noise in cm grows with distance.** The same ±50 mV of noise is under 1 cm of error around 19 cm but about 9 cm around 68 cm. Mount the sensor as close as the geometry allows.
- **Surface colour matters little** above ~20 cm (white 90% and grey 18% curves nearly overlap) because the sensor measures by triangulation (angle of the returning beam), not intensity.
- **Pulsed current draw.** The IR LED fires in bursts, which makes the supply sag through wire and breadboard resistance. The 10 µF bypass capacitor supplies these bursts locally.
- **Sunlight** contains strong IR and can blind the sensor. Two sensors aimed at the same area can interfere with each other.

## Power

The sensor needs 5 V; its output never exceeds ~3.1 V, so it connects directly to the ESP32 ADC without a divider. On the DevKit V1, 5 V is the **VIN** pin, which carries ~4.6–4.9 V only when the board is powered over USB. [TODO] measure VIN with a multimeter and record.

## Mounting

Sensor above the seat, pointing down, offset forward so the beam hits the lap/thigh area rather than the head [R]. Reason: a seated person is ~85–90 cm from cushion to head, beyond the sensor's 80 cm range. Target: empty seat 50–70 cm, occupied 20–45 cm. Current prototype: empty seat ≈ 50–60 cm [R, 2026-09-21]; occupied not measured, estimated 10–20 cm from the ≈ 40 cm gap [assumption], which may be below target. See [12_DESIGN_DECISIONS.md](12_DESIGN_DECISIONS.md#dr-001).

Measured: gap between empty and occupied ≈ 40 cm [R]. [TODO] record the absolute values.
