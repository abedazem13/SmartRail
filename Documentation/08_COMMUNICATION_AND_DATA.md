# 08 — Communication and Data

Provenance: **[V]** verified from code, **[R]** reported by a member, **[TODO]** unknown.

## Interfaces

| ID | From → To | Channel | Status |
|---|---|---|---|
| IF-01 | ESP32 → PC | USB serial, 115200 baud, text lines | **Implemented** [V] |
| IF-02 | PC → ESP32 | USB serial, single-character commands | **Implemented** [V] |
| IF-03 | Car → platform | [TODO] not selected (candidates: ESP-NOW, WiFi + Firebase) — Q-07 | Planned |

## IF-01 — ESP32 → PC serial lines

Produced by `ESP32/ESP32.ino`, parsed by `PC_software/seat_live.py` [V].
Seat numbers are 0-based: seat N is the Nth entry of `SENSOR_PINS` in `ESP32/parameters.h`.

| Line | When | Example | Fields |
|---|---|---|---|
| Banner | Boot | `SmartRail seat occupancy - GP2Y0A21YK0F` | — |
| Parameters | Boot | `seats=2 window=11 sample=40ms enter=20cm exit=12cm stable=1000ms` | Active `parameters.h` values |
| Calibration start | Boot, command `c` | `--- CALIBRATION: keep all seats EMPTY. starting in 3 s ---` | — |
| `CAL` | Once per seat during calibration | `CAL seat=0 baseline=58.4cm mv=566 noise=38mV` | baseline [cm], median [mV], noise = max − min [mV] |
| `WARN` | After a `CAL` line if a check fails | `  WARN noise too high: check bypass capacitor and wiring` | Free text |
| Calibration end | After the last `CAL` | `--- calibration done ---` | — |
| Status | Every 500 ms (`PRINT_INTERVAL_MS`) | `S0 dist= 58.3cm base= 58.4cm noise= 52mV EMPTY      S1 dist= 27.5cm ...` | Per seat: filtered distance [cm], baseline [cm], noise [mV], state `EMPTY`/`OCCUPIED`, `?` = change pending confirmation. All seats on one line |
| `EVENT` | On each confirmed state change | `EVENT seat=0 state=OCCUPIED dist=23.6cm` | seat, new state, distance [cm] |
| Debug | Command `d` toggles it | `(raw=566mV)` appended to status entries | Instantaneous reading [mV] |

Distances are clamped to 10–90 cm by the firmware (`DIST_MIN_CM`, `DIST_MAX_CM`).
After calibration every seat starts as `EMPTY` without an `EVENT` line.

Example values above are from the simulated board (`PC_software/seat_sim.py`) and a compile test, not from the physical prototype. [TODO] add a sanitized log from the real board.

## IF-02 — PC → ESP32 commands

| Byte | Action |
|---|---|
| `c` | Recalibrate — all seats must be empty. `seat_live.py --recalibrate` sends it |
| `d` | Toggle raw millivolt debug output |

## Connection lifecycle (PC side)

- Opening the serial port may restart the ESP32 (USB auto-reset), which triggers calibration. Seats must be empty for ~5 s after connecting. [R: typical ESP32 DevKit behaviour; TODO confirm on the prototype]
- `seat_live.py` marks a seat **UNKNOWN** during calibration and when no line about it arrives for 2 s (`STALE_S`).
- If the USB connection drops, `seat_live.py` retries every second and resumes automatically [V: code; tested with a simulated disconnect only].

## PC internal data: carriage summary

`seat_live.py` builds one record per carriage and passes it to `guidance.py`:

| Field | Type | Meaning |
|---|---|---|
| `car` | int | Carriage number (`CARRIAGES` in `seat_live.py`) |
| `seats_total` | int | Seats in the carriage |
| `free_min` | int | Seats known to be EMPTY |
| `free_max` | int | `free_min` + seats in UNKNOWN state |
| `sensors_reporting` | int | Seats not in UNKNOWN state |

## Security and privacy

IF-01/IF-02 are local USB links: no credentials, no personal data (distances only).
