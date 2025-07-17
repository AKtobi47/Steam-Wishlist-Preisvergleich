#!/bin/bash

# Steam Price Tracker Startup Script
# Unterstützt: Linux, macOS, WSL

set -e  # Exit bei Fehlern

echo "========================================"
echo "   Steam Price Tracker - Unix/Linux"
echo "========================================"
echo

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funktionen
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Python Version prüfen
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        log_error "Python ist nicht installiert"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

log_info "Verwende $PYTHON_CMD ($(${PYTHON_CMD} --version))"

# Virtual Environment aktivieren (falls vorhanden)
if [ -f "venv/bin/activate" ]; then
    log_info "Aktiviere Virtual Environment..."
    source venv/bin/activate
fi

# Dependencies prüfen
if ! ${PYTHON_CMD} -c "import requests" &> /dev/null; then
    log_warning "Dependencies fehlen, installiere..."
    ${PYTHON_CMD} -m pip install -r requirements.txt
fi

# Steam Price Tracker starten
log_success "Steam Price Tracker wird gestartet..."
echo

if ${PYTHON_CMD} main.py; then
    log_success "Anwendung beendet"
else
    log_error "Fehler beim Starten der Anwendung"
    log_info "Überprüfe die Logs in logs/steam_tracker.log"
    exit 1
fi
