# Steam Price Tracker PowerShell Startup Script
# Für Windows PowerShell und PowerShell Core

[CmdletBinding()]
param()

# Titel setzen
$host.ui.RawUI.WindowTitle = "Steam Price Tracker"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Steam Price Tracker - PowerShell" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan
Write-Host

# Python prüfen
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python gefunden: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python ist nicht installiert oder nicht im PATH" -ForegroundColor Red
    Write-Host "Bitte installiere Python von https://python.org" -ForegroundColor Yellow
    Read-Host "Drücke Enter zum Beenden"
    exit 1
}

# Virtual Environment aktivieren (falls vorhanden)
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "🔧 Aktiviere Virtual Environment..." -ForegroundColor Blue
    & ".\venv\Scripts\Activate.ps1"
}

# Dependencies prüfen
try {
    python -c "import requests" 2>$null
    Write-Host "✅ Dependencies verfügbar" -ForegroundColor Green
} catch {
    Write-Host "📦 Installiere Dependencies..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
}

# Steam Price Tracker starten
Write-Host "🚀 Steam Price Tracker wird gestartet..." -ForegroundColor Green
Write-Host

try {
    python main.py
    Write-Host "✅ Anwendung beendet" -ForegroundColor Green
} catch {
    Write-Host "❌ Fehler beim Starten der Anwendung" -ForegroundColor Red
    Write-Host "Überprüfe die Logs in logs/steam_tracker.log" -ForegroundColor Yellow
}

Write-Host
Read-Host "Drücke Enter zum Beenden"
