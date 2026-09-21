# 05 — Wiring and Pinout

**Wiring revision:** A, 2026-09-21. [TODO] verify against the physical prototype and add a photo.

## Pin map

| Component | Component pin | ESP32 DevKit V1 pin | Direction | Voltage | Notes |
|---|---|---|---|---|---|
| Sensor seat 0 (HW-02) | Red (Vcc) | VIN | Power | ~5 V | Via the breadboard + rail |
| Sensor seat 0 | Black (GND) | GND | Power | 0 V | Common ground |
| Sensor seat 0 | Yellow (Vo) | **GPIO34** | Analog in | 0–3.1 V | ADC1_CH6, input-only pin |
| Sensor seat 1 | Red / Black | VIN / GND | Power | ~5 V | Shares rails with seat 0 |
| Sensor seat 1 | Yellow (Vo) | **GPIO35** | Analog in | 0–3.1 V | ADC1_CH7, input-only pin |
| Capacitor 10 µF (HW-03) | + / − | VIN rail / GND rail | — | — | One per sensor, **next to the sensor**. Stripe on the case marks −. |
| Status LED seat 0 | — | GPIO2 | Digital out | 3.3 V | On-board LED, no wiring needed |
| Status LED seat 1 (HW-07) | Anode via 220–330 Ω | GPIO4 | Digital out | 3.3 V | Cathode to GND |

Cross-check: these values match `SENSOR_PINS` and `LED_PINS` in `ESP32/parameters.h`.

## Locating the pins

With the USB connector at the top, the right-hand header reads, top to bottom:

`VIN, GND, D13, D12, D14, D27, D26, D25, D33, D32, D35, D34, VN, VP, EN`

So **GPIO34 is the 12th pin** from VIN, and GPIO35 is the 11th. The breadboard row matching each pin is where its wire goes.

## Assembly steps

1. Unplug USB.
2. Jumper from the board's **VIN** to the breadboard **+** rail, and from **GND** to the **−** rail. Breadboard rails are isolated strips — without these jumpers they carry no power.
3. Sensor red → + rail, black → − rail, yellow → the row of GPIO34.
4. 10 µF capacitor across + and − rails, as close to the sensor's wires as possible. Long leg/unmarked side to +.
5. Keep all wires short.
6. Plug in USB. Measure between the rails: expect ~4.6–4.9 V. 0 V or 3.3 V means the power wiring is wrong.

## Pin selection notes

- **ADC1 only.** ADC2 pins (e.g. GPIO2, 4, 12–15, 25–27) stop working as analog inputs whenever WiFi is on, which the later stages need.
- GPIO34–39 are input-only and have no internal pull-ups — fine for analog input.
- GPIO2 is a strapping pin; driving the on-board LED on it is safe.
- **Never** feed more than 3.3 V into any GPIO. The sensor's output (max ~3.1 V) is safe; its supply (5 V) must never touch a GPIO.
