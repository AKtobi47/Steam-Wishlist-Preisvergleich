@echo off
title Steam Price Tracker
echo.
echo ========================================
echo    Steam Price Tracker - Windows
echo ========================================
echo.

REM Prüfe Python Installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python ist nicht installiert oder nicht im PATH
    echo Bitte installiere Python von https://python.org
    pause
    exit /b 1
)

REM Prüfe ob Virtual Environment existiert
if exist "venv\Scripts\activate.bat" (
    echo 🔧 Aktiviere Virtual Environment...
    call venv\Scripts\activate.bat
)

REM Prüfe Dependencies
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installiere Dependencies...
    python -m pip install -r requirements.txt
)

echo 🚀 Steam Price Tracker wird gestartet...
echo.
python main.py

if errorlevel 1 (
    echo.
    echo ❌ Fehler beim Starten der Anwendung
    echo Überprüfe die Logs in logs/steam_tracker.log
)

echo.
pause
