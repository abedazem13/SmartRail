# 09 — Setup, Build and Run

How to start the SmartRail dashboard, show it on a phone, and connect the ESP32.
Windows instructions; the repository lives at `C:\Users\yazan\OneDrive\Desktop\IOT\SmartRail` on Yazan's laptop.

## 1. One-time setup (per computer)

Needed once per machine. Python 3.10 or newer, from python.org.

```powershell
cd <the SmartRail folder>
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r PC_software\requirements.txt
```

That creates `.venv\` (ignored by Git) with Flask, pyserial and waitress.

For the firmware: Arduino IDE 2.x with the **esp32 by Espressif Systems** core (the team uses 3.0.7), board **ESP32 Dev Module** / DOIT ESP32 DEVKIT V1.

## 2. Start the dashboard

**Double-click `start_dashboard.bat`** in the repository root. It starts the server and opens both pages.

Or by hand:

```powershell
.\.venv\Scripts\python.exe PC_software\dashboard.py
```

| Page | Address | What it is |
|---|---|---|
| Passenger display | http://127.0.0.1:8765/ | What travellers see: per-car availability, the cars to walk to, station number. No controls |
| Demo controls | http://127.0.0.1:8765/controls | The seat map, Next stop, auto stops, scenarios, hardware connection |

A console window stays open while the dashboard runs. **Keep it open**; closing it, or pressing Ctrl+C, stops the dashboard. State lives in that process only, so restarting resets the train to the example scenario.

### Using it

- **Click any seat** in the controls view to flip it free/occupied.
- **Next stop**: 5–20% of occupied seats free up, then 5–20% of free seats fill, at random across all cars, applied over about 2.4 s so it is visible.
- **Start auto stops**: repeats that every 5–30 s, for a demo that runs itself. It only advances while a display tab is open.
- **Scenarios** (example / empty / occupied) reset the simulated seats and the station counter.

## 3. Show the display on a phone or a second laptop

**Double-click `start_dashboard_network.bat`**, or:

```powershell
.\.venv\Scripts\python.exe PC_software\dashboard.py --host 0.0.0.0
```

The console then prints a third line:

```
On this network:   http://10.0.0.14:8765/  (display only; the controls stay on this computer)
```

Open **that** address on the phone. The address changes with the network, so read it each time.

- Phone and laptop must be on the **same WiFi**.
- Windows may ask to allow Python through the firewall: allow it for **private** networks.
- The phone can only **watch**. `/controls`, the serial-port list and every change are refused (HTTP 403) for any device other than the computer running the dashboard.
- There is **no password**: anyone on that network can view the display. Do not use it on a network you do not trust; a phone hotspot with the laptop joined is the safest option.
- Campus WiFi often blocks device-to-device traffic. If the phone cannot load the page there, use a hotspot.

## 4. Connect the ESP32 (hybrid mode)

1. Upload `ESP32/ESP32.ino` from Arduino IDE (board: ESP32 Dev Module, port: the CP210x one, e.g. COM5).
2. **Close the Arduino Serial Monitor.** Only one program can hold the serial port.
3. In the controls view: **Refresh ports** → pick the port → **Connect hardware · hybrid mode**.
4. Keep both physical seats empty for about 5 seconds while the board calibrates.

A1 and B1 then come from the sensors and cannot be clicked; the other 1294 seats stay simulated and editable. Sensor seats show as **unknown** during calibration, after a disconnect, or after 2 seconds without data — unknown is never counted as free.

## 5. Run the tests

```powershell
cd PC_software
..\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
```

Expected: `Ran 50 tests ... OK`. No serial port is opened.

Optional real-browser check (needs `requirements-dev.txt`; `SMARTRAIL_BROWSER_CHANNEL=msedge` uses installed Edge instead of downloading Chromium):

```powershell
cd PC_software
..\.venv\Scripts\python.exe tests\browser_dashboard_check.py
```

## 6. If something goes wrong

| Symptom | Cause and fix |
|---|---|
| `No module named flask` | Wrong interpreter. Use `.\.venv\Scripts\python.exe`, not plain `python` |
| Browser cannot reach the page | The server is not running, or its window was closed |
| `Address already in use` | An older server still runs. Close that window, or add `--http-port 8766` and use that port in the URLs |
| Phone shows **Bad Request** | Started without `--host`. Use `start_dashboard_network.bat` |
| Phone cannot connect at all | Different WiFi, firewall, or a network that blocks device-to-device traffic. Try a hotspot |
| Phone shows the display but no controls | Intended: controls are restricted to the computer running the dashboard |
| No COM port listed | USB cable without data lines, missing CP210x driver, or the Serial Monitor holds the port |
| Connected but no seat data | Wrong sketch on the board, baud not 115200, or `NUM_SEATS` not 2 |
| Seats stuck on unknown | Calibration still running, board disconnected, or no valid reading for 2 s |

See also: [dashboard guide](17_HYBRID_DASHBOARD.md), [hardware testing handoff](HARDWARE_DASHBOARD_AGENT_HANDOFF.md), [troubleshooting](11_TROUBLESHOOTING.md).
