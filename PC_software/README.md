## PC software (Python)

Runs on a laptop connected to the ESP32 by USB. It reads the firmware's serial
output, keeps the state of every seat, counts free seats per carriage and shows
which carriage the next passenger should board.

The EMPTY / OCCUPIED decision is made **on the ESP32** (see
[06_ESP32_FIRMWARE.md](../Documentation/06_ESP32_FIRMWARE.md)); these programs
only collect it. They add one state: **UNKNOWN**, while the board calibrates or
when no data has arrived for 2 s.

This is an interim stage for requirements FR-004 (free seats per car) and
FR-006 (guidance) until the car → platform link and the platform signage are
chosen (Q-07, Q-08). See [12_DESIGN_DECISIONS.md](../Documentation/12_DESIGN_DECISIONS.md#dr-008).

| File | What it does |
|---|---|
| `seat_live.py` | Main program. Reads the board, prints seat changes, free seats per carriage and the platform display line. Records every session so it can be replayed. Reconnects automatically if USB drops. |
| `seat_status.py` | Short version: prints only when a seat becomes OCCUPIED, EMPTY or has no data. |
| `guidance.py` | Decides which carriage each waiting passenger should board. `python guidance.py` runs a demo. |
| `seat_sim.py` | Runs the PC software on a simulated board (same serial lines as the real firmware), for testing without hardware. |

Keep all four files in this folder - they import each other.

### Setup

```
python -m pip install pyserial
```
Mac/Linux: use `python3`. Windows: if `python` is not found, use `py`.

### Run

```
python seat_sim.py                        # no hardware: simulated board
python guidance.py                        # guidance demo on its own
python seat_live.py --port COM5           # real board
python seat_status.py --port COM5         # real board, seat changes only
python seat_live.py --replay seat_log.txt # re-run a recorded session
```

Replace `COM5` with your port (Arduino IDE → Tools → Port). Upload
`ESP32/ESP32.ino` first, then **close the Arduino Serial Monitor** - only one
program can use the port.

**Keep all seats empty for the first ~5 s.** The board may restart when the
program connects, and it then recalibrates the empty-seat distance.

| Option | Meaning |
|---|---|
| `--port` | Serial port of the ESP32 |
| `--replay FILE` | Re-run a recorded session instead of reading the board |
| `--log FILE` | Where a live session is recorded (default `seat_log.txt`) |
| `--recalibrate` | Send `c` to the board after connecting (seats must be empty) |
| `--report SECONDS` | `seat_live.py` only: summary interval (default 2) |
| `--verbose` | `seat_live.py` only: also print every line from the board |

### Example output (`seat_live.py`, simulated board)

```
[    9.2s] seat 0 (car 1): EMPTY -> OCCUPIED  (dist 23.6 cm)
[   12.0s] car 1: 0/1 free  car 2: 1/1 free
           DISPLAY: C1 FULL | C2 FREE  ->  next passenger: C2
[   29.9s] seat 0 (car 1): EMPTY -> UNKNOWN  (no data from board)
```

`0-1/1 free` means the seat's state is UNKNOWN, so it may or may not be free.

### Settings (top of `seat_live.py`)

| Setting | Default | Meaning |
|---|---|---|
| `CARRIAGES` | `{1: [0], 2: [1]}` | Which firmware seats belong to which carriage. Seat N = Nth entry of `SENSOR_PINS` in `ESP32/parameters.h`. [TODO] confirm mapping for the demo model (Q-15) |
| `STALE_S` | 2.0 s | No line about a seat for this long → UNKNOWN. The firmware sends a status line every 0.5 s |

### Session logs

Live runs are recorded as `<seconds>\t<line from the board>`. `seat_log.txt` is
overwritten on every run and ignored by Git. To keep a run as test evidence,
rename it descriptively (e.g. `seat-test-2seats-2026-09-21.txt`) and store it in
`Documentation/assets/test-results/`.

The serial formats parsed here are specified in
[08_COMMUNICATION_AND_DATA.md](../Documentation/08_COMMUNICATION_AND_DATA.md).
If the firmware's print format changes, update the regular expressions at the
top of `seat_live.py`.
