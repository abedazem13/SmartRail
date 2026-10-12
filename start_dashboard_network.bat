@echo off
rem SmartRail - start the dashboard and also serve the PASSENGER DISPLAY to
rem this network, so a phone or a second laptop can show it.
rem The controls page stays on this computer only; there is no password.
rem Windows may ask to allow Python through the firewall: allow private networks.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo The .venv folder is missing. Create it once with:
    echo     py -3 -m venv .venv
    echo     .venv\Scripts\python.exe -m pip install -r PC_software\requirements.txt
    pause
    exit /b 1
)

echo Starting SmartRail for this network...
echo Open the address printed below as "On this network" on your phone.
start "" http://127.0.0.1:8765/controls
.venv\Scripts\python.exe PC_software\dashboard.py --host 0.0.0.0

echo.
echo The dashboard has stopped.
pause
