@echo off
title Steam Price Tracker v3.0
echo 🚀 Steam Price Tracker v3.0 wird gestartet...
echo ===============================================
echo.

cd /d "%~dp0"

echo 📊 Prüfe Python Installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python nicht gefunden!
    echo Installiere Python von https://python.org
    pause
    exit /b 1
)

echo ✅ Python gefunden
echo.

echo 🔄 Starte Steam Price Tracker...
python main.py

echo.
echo 👋 Steam Price Tracker beendet
pause
