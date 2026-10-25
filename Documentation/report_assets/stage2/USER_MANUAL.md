# SmartRail — user manual

**Audience:** demonstrator/operator and someone viewing the passenger display.  
**Version described:** source `0883d93`, reviewed 13 October 2026.  
**Scope:** current 12-car prototype. Physical testing must be completed by the teammates with the board; this manual does not certify their hardware.

## 1. What the system does

The passenger page shows available seats in 12 logical train cars A–L. Each car has 108 seats. The control page lets the operator change simulated seats, run simulated station stops and connect two real sensor inputs.

- **Simulation mode:** 1,296 simulated seats; no ESP32 required.
- **Hybrid mode:** A1 and B1 are real sensor seats, with 1,294 simulated seats.
- Counts are information, not seat reservations or a guarantee of a place to sit.
- The station number and boarding animation are simulated, not live train tracking.

## 2. What you need

### Software-only operation

- Windows laptop with Python **3.10 or newer**, a web browser, and this repository.
- A working Python virtual environment with the project dependencies installed.
- Internet for initial installation if dependencies are not already available. The local demo itself needs no cloud service or internet access.

### Hybrid operation

- ESP32 DevKit V1 with the current firmware uploaded.
- Two correctly powered and mounted Sharp analog IR sensors, connected to GPIO34 and GPIO35.
- USB **data** cable and the correct serial driver (the documented prototype uses CP210x).
- Known working power, common ground and manufacturer-recommended supply decoupling. Follow [hardware](../Documentation/04_HARDWARE.md) and [wiring](../Documentation/05_WIRING_AND_PINOUT.md) instructions with the hardware operator.

Power down before changing wires. Do not apply 5 V to an ESP32 signal pin or combine external power with PC USB without an approved arrangement. Do not put a hand directly against the sensor; use the measured working range.

## 3. One-time Windows setup

Open PowerShell in the **SmartRail repository root**—the folder containing ESP32, PC_software and the batch launchers, not the Presentation folder.

```powershell
if (-not (Test-Path .venv)) { py -3 -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -r .\PC_software\requirements.txt
```

If `py` is unavailable but a compatible `python` command works, use `python` for the environment-creation command. Existing team environments may be reused, but installation and startup must use the same interpreter. Do not overwrite an existing environment without checking it.

Firmware setup is separate: use Arduino IDE 2.x and the ESP32 Arduino core, select the actual board/port and upload [ESP32.ino](../ESP32/ESP32.ino). The newer setup document reports core 3.0.7; confirm and record the version actually used. Leave the seats empty through startup calibration. Uploading or verifying hardware requires the board; simulation mode does not.

## 4. Start and stop

After setup, double-click [start_dashboard.bat](../start_dashboard.bat). It starts the server and opens the passenger and control pages. Keep its console window open.

Equivalent command from the repository root:

```powershell
.\.venv\Scripts\python.exe .\PC_software\dashboard.py
```

| View | Address | Purpose |
|---|---|---|
| Passenger | http://127.0.0.1:8765/ | Availability, car suggestions, platform zones, simulated station |
| Controls | http://127.0.0.1:8765/controls | Seat maps, scenarios, station controls, hardware connection |

Use the Full screen button or browser F11 for the passenger display. To stop the server, press Ctrl+C in its terminal. Closing the terminal also stops the display's data source.

If the HTTP port is occupied, stop the old server or launch with a different port:

```powershell
.\.venv\Scripts\python.exe .\PC_software\dashboard.py --http-port 8766
```

Use 8766 in both browser URLs in that case. Browser refresh preserves the running server's state. Restarting the server resets the example and station 1; it normally starts in simulation mode. The optional startup argument `--serial-port COM5` starts hybrid mode directly—replace COM5 with the actual board port.

## 5. Read the passenger display

| Indicator | Meaning |
|---|---|
| Green car | At least 10 confirmed free seats and no unknown seats |
| Amber/orange car | 1–9 confirmed free seats and no unknown seats |
| Red / “Full” | Zero free seats with complete data; only seating is measured, not standing room |
| Gray car | At least one seat state is unknown; known free seats are still shown separately |
| Occupancy percentage | Confirmed occupied seats divided by all seats; unknown seats are not silently treated as occupied or free |
| Suggested cars | Up to three with the most confirmed free seats; ties alphabetically |
| Station | Simulated station counter, initially 1 |
| BOARDING | A simulated stop is applying its scheduled changes |
| Offline warning / dashes | Dashboard server unavailable; do not rely on old counts |

Platform zones are logical labels matching car letters for this prototype. No real railway stopping-position integration is implemented.

## 6. Simulation controls

1. Open Controls and choose **Use simulation** if necessary.
2. If auto stops are on, press **Stop auto stops** before preparing a static scene.
3. Click **Example scenario · station 1**.
4. Click a seat in the car maps to switch between empty and occupied. Both views update from the same shared model.

Example free counts: **A12, B3, C0, D25, E48, F7, G36, H18, I1, J60, K29, L72**. Total **311**. Suggestions **L, J, E**. A1 and B1 are occupied in this deterministic software example.

### Scenario buttons

- **Example scenario:** restores the source-defined simulated pattern.
- **Empty simulated seats:** makes all editable seats empty.
- **Occupy simulated seats:** makes all editable seats occupied.

Each preset resets the station counter to 1 and clears pending stop animation. It does **not** turn off automatic stops. In hybrid mode presets skip A1/B1, so totals depend on real readings.

### Next stop

Press once and wait for BOARDING to finish. The station advances and simulated passengers leave during the first half of about 2.4 seconds, then others board during the second half. Selections are random and bounded; exact resulting counts are not predictable.

This is synthetic occupancy activity, not a quantitative passenger-flow or dwell-time model. Physical seats are never modified by a simulated stop in hybrid mode.

### Automatic stops

Choose 5, 10, 15 or 30 seconds, then press **Start auto stops**. Stops are advanced by browser polling; keep a display tab open. Press **Stop auto stops** to disable further scheduling. An already-running stop may still finish; wait or use a preset to cancel remaining changes.

For a predictable scene: **stop auto → wait or load preset → demonstrate**. Do not assume changing mode stops auto or resets the station counter; current mode changes do neither.

## 7. Connect physical sensors

1. Ask the hardware operator to confirm the current firmware, safe wiring and mounting. Sensor index 0/GPIO34 maps to **A1**; index 1/GPIO35 maps to **B1**.
2. Close Arduino Serial Monitor/Plotter, the console seat programs and any other process using the port. Only one reader can own it.
3. In Controls, choose **Refresh ports**, select or type the actual port, and click **Connect hardware · hybrid mode**.
4. Leave both physical seats empty through calibration. Connecting may reset the ESP32. About five seconds is typical, not a guarantee; wait for completion and fresh sensor states.
5. A1/B1 show sensor sources and cannot be clicked. All other 1,294 seats remain editable.
6. Place a target within the validated detection range; after firmware confirmation the corresponding seat/count updates. Remove it to restore empty.

For a clear audience demonstration, stop auto, connect hybrid with both real seats empty, then choose **Occupy simulated seats**. A and B should each show one free seat. Covering one sensor changes its car to zero/red; the other car should not change. See the complete [demo script](DEMO_SCRIPT.md).

If the ESP32 disconnects, A1/B1 become unknown; simulated values do not silently replace them. The worker retries the same COM port. If the OS assigns a different name, select it and reconnect. Reconnection/reset may recalibrate, so keep physical seats empty again.

Use **Hardware diagnostics & mapping** to view last distance, noise, state age, pending change, connection detail and latest board message. This message is not a saved log. Persistent WARN messages need investigation; they are not automatically cleared by ordinary status updates.

## 8. Phone or second-laptop passenger display (optional)

1. Stop the existing local server before starting another on the same port.
2. Put the devices on a trusted private network or hotspot.
3. Double-click [start_dashboard_network.bat](../start_dashboard_network.bat), or start with `--host 0.0.0.0`.
4. Read the **On this network** URL printed in the console; open that exact LAN address on the phone. `127.0.0.1` on the phone refers to the phone, not the laptop.
5. If Windows asks, allow the application only on the appropriate private network. Do not disable the firewall globally.

The phone is read-only: the controls page, serial-port list and mutation requests are refused for remote clients. Use localhost on the host laptop for controls. Network viewing has no password; anyone able to access the service on that network can view data. Do not expose it to the internet, add a public tunnel or treat it as production security.

Campus Wi-Fi may isolate devices. Use a tested hotspot or simply present on the laptop. This network feature does **not** make the ESP32-to-laptop USB connection wireless.

## 9. Common problems

| Symptom | Action |
|---|---|
| Missing Flask, serial or Waitress | Install requirements using the same interpreter that launches the server |
| Page unavailable | Check the server terminal, URL and HTTP port; keep terminal open |
| Port already in use | Stop the old server or choose another HTTP port |
| No COM device | Check USB data cable, driver and actual Arduino port |
| COM access denied | Close every other serial reader, then retry |
| A1/B1 gray after connecting | Wait for calibration; inspect messages; verify correct firmware, 115200 baud and two sensor entries |
| Wrong physical seat changes | Verify sensor index/GPIO mapping with the operator, rather than guessing |
| False readings | Check range, mounting, noise, supply, capacitors and lighting before changing thresholds |
| Preset changes again by itself | Stop automatic stops before reapplying the preset |
| Phone cannot load | Check private network, printed LAN URL, firewall and client isolation; fall back to laptop |
| “Full” seems misleading | It means no free seats, not standing capacity or a boarding restriction |

## 10. Evidence and limits

Capture current screenshots, a real hardware video and completed [test results](TEST_RESULTS_TEMPLATE.md). Raw serial recording can be done with the existing console program in a **separate** run after releasing the dashboard's port. Do not call that a simultaneous dashboard capture.

No persistent database, saved dashboard session, reservation system, live train arrival feed or measured dwell-time optimization is included. Source-based descriptions in this manual must not be relabeled as physical test results.