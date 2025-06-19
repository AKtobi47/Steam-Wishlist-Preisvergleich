#!/bin/bash
echo "🚀 Steam Price Tracker v3.0 wird gestartet..."
echo "==============================================="
echo

cd "$(dirname "$0")"

echo "📊 Prüfe Python Installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 nicht gefunden!"
    echo "Installiere Python3 über deinen Package Manager"
    exit 1
fi

echo "✅ Python gefunden"
echo

echo "🔄 Starte Steam Price Tracker..."
python3 main.py

echo
echo "👋 Steam Price Tracker beendet"
