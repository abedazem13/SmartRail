# 12 — Design Decisions

## DR-001

**Sensor mounted above the seat, aimed at the lap**
Date: 2026-09 · Status: accepted [R]

- **Context:** the sensor's useful range is 15–80 cm. A seated person measures ~85–90 cm from cushion to head.
- **Options:** (a) overhead aimed at the head, (b) overhead aimed at the lap, (c) horizontal from the seat back in front, (d) under/inside the seat.
- **Choice:** (b). Aiming at the head would put the empty seat beyond 80 cm. Aiming at the lap keeps both states inside the range.
- **Consequences:** does not trigger on people standing in the aisle or bags on the floor. A person leaning far forward may leave the beam. Measured gap ≈ 40 cm [R].

## DR-002

**Analog inputs on ADC1 (GPIO34/35)**
Date: 2026-09 · Status: accepted

- **Context:** ESP32 ADC2 cannot be read while WiFi is active; later stages need WiFi.
- **Choice:** ADC1 pins only. The course tutorial example uses GPIO2 (ADC2), which would break once WiFi is added.

## DR-003

**Relative threshold with calibrated baseline, hysteresis and time confirmation**
Date: 2026-09 · Status: accepted

- **Context:** the datasheet formula is an approximation; each unit and mounting differs.
- **Options:** fixed absolute distance threshold vs threshold relative to the measured empty seat.
- **Choice:** relative. Enter at baseline − 20 cm, exit at baseline − 12 cm, confirm for 1 s. Margins derived from the measured ~40 cm gap.
- **Consequences:** needs an empty seat at calibration time. Latency ~1–1.5 s, acceptable for a train seat.

## DR-004

**Median of 11 samples taken every 40 ms, non-blocking**
Date: 2026-09 · Status: accepted

- **Context:** sensor output has spikes; it updates only every ~38 ms.
- **Options:** mean vs median; blocking burst sampling vs periodic sampling.
- **Choice:** median (robust to spikes, unlike the mean). 40 ms spacing so each sample is independent. Non-blocking so the time confirmation is accurate and WiFi can be added without restructuring.
- **Superseded:** an earlier draft sampled 9 times 5 ms apart inside a blocking loop — most samples were duplicates and the loop took ~1 s.

## DR-005

**Sensor powered from VIN (5 V), output wired directly to the ADC**
Date: 2026-09 · Status: accepted

- **Context:** the sensor needs 4.5–5.5 V, while ESP32 GPIOs tolerate 3.3 V max.
- **Choice:** power from VIN; the sensor's output peaks at ~3.1 V, so no voltage divider is needed. Powering it from 3.3 V is outside its specification.

## DR-006

**Arduino IDE sketch at `ESP32/ESP32.ino`**
Date: 2026-09-21 · Status: accepted

- **Context:** the course template keeps `parameters.h` and `SECRETS.h` directly in `ESP32/`, and Arduino IDE requires the `.ino` name to match its folder.
- **Choice:** name the sketch `ESP32.ino` so every template path stays valid and the IDE opens it directly.
- **Alternative:** PlatformIO (pioarduino) in VS Code. Not adopted yet — the course asks all members to use the same IDE. [TODO] team decision.
