@echo off
title 🔄 Charts_charts_price_updates - ENHANCED v2.0
color 0A
echo 🚀 ENHANCED Background Scheduler v2.0
echo ================================================================
echo 📊 Scheduler: Charts
echo 🎯 Task: charts_price_updates
echo 👁️ Parent-Monitoring: AKTIVIERT
echo 💓 Sign of Life: AKTIVIERT
echo ⏰ Zeit: %date% %time%
echo ================================================================
echo 💡 Automatisches Cleanup wenn Hauptprogramm beendet wird
echo 💡 Parent-Process-Monitoring für saubere Beendigung
echo.
cd /d "B:\Dokumente\.Studium\7\BIGData\Steam-Wishlist-Preisvergleich"
python "temp_task_charts_price_updates.py"
echo.
echo 🏁 Task beendet - drücke eine Taste zum Schließen
pause
