@echo off
rem SmartRail - start the dashboard and open both views.
rem Double-click this file. Keep this window open while demonstrating;
rem closing it (or pressing Ctrl+C) stops the dashboard.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo The .venv folder is missing. Create it once with:
    echo     py -3 -m venv .venv
    echo     .venv\Scripts\python.exe -m pip install -r PC_software\requirements.txt
    pause
    exit /b 1
)

echo Starting the SmartRail dashboard...
start "" http://127.0.0.1:8765/
start "" http://127.0.0.1:8765/controls
.venv\Scripts\python.exe PC_software\dashboard.py

echo.
echo The dashboard has stopped.
pause
