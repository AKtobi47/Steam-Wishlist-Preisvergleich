Link zu Database File (steam_price_tracker)in Seafile, da zu gross für Git:
https://seafile.rlp.net/d/263379a1691f4472968b/


# 💰 Steam Price Tracker v1.0

**Vollständiges System für automatisches Steam-Preis-Tracking mit CheapShark API**

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)

## ✨ Features

- 🎯 **Direktes CheapShark-Tracking** mit Steam App IDs (kein komplexes Mapping)
- 📊 **Multi-Store Preisvergleich** für 6 major Stores (Steam, GOG, etc.)
- 📥 **Steam Wishlist Import** für automatisches Setup
- ⚡ **Automatisches Preis-Tracking** mit konfigurierbaren Intervallen
- 🗄️ **SQLite-Datenbank** für historische Preisdaten
- 📈 **Preisverlauf und Trend-Analyse**
- 🏆 **Best Deals Detection** mit Rabatt-Tracking
- 📄 **CSV-Export** kompatibel mit Excel/Pandas
- 🔧 **Benutzerfreundliche CLI** für alle Funktionen
- 🛡️ **Robuste Fehlerbehandlung** und Rate Limiting
- 📦 **Einfache Installation** mit Setup-Wizard

## 🚀 Schnellstart

### 1. Installation

```bash
# Repository klonen
git clone <repository-url>
cd steam-price-tracker

# Setup-Wizard starten (installiert alles automatisch)
python setup.py setup
```

### 2. Steam API Key

1. Gehe zu [Steam Web API Key](https://steamcommunity.com/dev/apikey)
2. Erstelle einen API Key für deine Domain (z.B. "localhost")
3. Der Setup-Wizard erstellt automatisch eine `.env`-Datei
4. Trage deinen API Key ein:

```env
STEAM_API_KEY=dein_api_key_hier
```

### 3. Erste Nutzung

```bash
# Hauptanwendung starten
python main.py

# Oder Setup-Script verwenden
python setup.py run
```

## 📦 Architektur

### Hauptkomponenten

```
steam-price-tracker/
├── main.py                     # 🎯 Hauptanwendung mit interaktiver CLI
├── price_tracker.py            # 🦈 Kern-Klasse für CheapShark Integration
├── database_manager.py         # 🗄️ SQLite-Datenbank-Management
├── steam_wishlist_manager.py   # 📥 Steam Wishlist Import
├── config.py                   # ⚙️ Konfigurationsverwaltung
├── setup.py                    # 🚀 Setup-Wizard und Tools
├── requirements.txt            # 📦 Python-Dependencies
├── .env.example               # 📋 Environment Template
├── config.json                # ⚙️ Konfigurationsdatei
└── README.md                   # 📖 Diese Dokumentation
```

### Unterstützte Stores

| Store ID | Store Name | API Support | Rabatt-Tracking |
|----------|------------|-------------|-----------------|
| 1 | Steam | ✅ | ✅ |
| 3 | GreenManGaming | ✅ | ✅ |
| 7 | GOG | ✅ | ✅ |
| 11 | HumbleStore | ✅ | ✅ |
| 15 | Fanatical | ✅ | ✅ |
| 27 | GamesPlanet | ✅ | ✅ |

### Datenbank-Schema

**tracked_apps** - Apps die getrackt werden
```sql
steam_app_id TEXT PRIMARY KEY
name TEXT NOT NULL
added_at TIMESTAMP
last_price_update TIMESTAMP
active BOOLEAN
```

**price_snapshots** - Historische Preisdaten
```sql
steam_app_id TEXT
game_title TEXT
timestamp TIMESTAMP
steam_price, steam_original_price, steam_discount_percent, steam_available
greenmangaming_price, greenmangaming_original_price, ...
-- Für alle 6 Stores
```

## 🎯 Nutzung

### CLI-Interface

```bash
python main.py
```

**Verfügbare Aktionen:**
1. 📱 App manuell zum Tracking hinzufügen
2. 📥 Steam Wishlist importieren
3. 🔍 Aktuelle Preise anzeigen
4. 📊 Beste Deals anzeigen
5. 📈 Preisverlauf anzeigen
6. 🔄 Preise manuell aktualisieren
7. 🚀 Automatisches Tracking starten/stoppen
8. 📋 Getrackte Apps verwalten
9. 🗑️ Apps entfernen
10. 📄 CSV-Export erstellen
11. 📊 Detaillierte Statistiken
12. 👋 Beenden

### Programmatische Nutzung

```python
from price_tracker import SteamPriceTracker
from database_manager import DatabaseManager

# Tracker initialisieren
db = DatabaseManager()
tracker = SteamPriceTracker(db)

# App zum Tracking hinzufügen
tracker.add_app_to_tracking("413150", "Stardew Valley")

# Preise aktualisieren
result = tracker.track_app_prices(["413150", "105600"])
print(f"✅ {result['successful']}/{result['processed']} Apps aktualisiert")

# Automatisches Tracking starten
tracker.start_scheduler(interval_hours=6)

# Preisverlauf abrufen
history = tracker.get_price_history("413150", days_back=30)

# Beste Deals anzeigen
deals = tracker.get_current_best_deals(limit=10)
for deal in deals:
    print(f"{deal['game_title']}: €{deal['best_price']:.2f} (-{deal['discount_percent']}%)")
```

### Steam Wishlist Import

```python
# Vereinfachter Import
result = tracker.import_steam_wishlist("76561197960435530", "dein_api_key")

if result['success']:
    print(f"✅ {result['imported']} Apps hinzugefügt")
    
    # Preise für alle neuen Apps abrufen
    batch_result = tracker.process_all_pending_apps_optimized()
    print(f"📊 {batch_result['total_successful']} Apps verarbeitet")
```

## 🔧 Konfiguration

### Environment Variables (.env)

```env
# Erforderlich
STEAM_API_KEY=dein_steam_api_key

# Optional - Rate Limiting
STEAM_RATE_LIMIT=1.0
CHEAPSHARK_RATE_LIMIT=1.5

# Optional - Tracking
TRACKING_INTERVAL_HOURS=6
MAX_APPS_PER_UPDATE=100

# Optional - Export
EXPORT_FORMAT=csv
EXPORT_DIRECTORY=exports
```

### Konfigurationsdatei (config.json)

```json
{
  "database": {
    "path": "steam_price_tracker.db",
    "cleanup_days": 90,
    "backup_enabled": true
  },
  "tracking": {
    "default_interval_hours": 6,
    "max_apps_per_update": 100,
    "enable_automatic_tracking": false
  },
  "cheapshark": {
    "rate_limit_seconds": 1.5,
    "timeout_seconds": 15,
    "store_ids": "1,3,7,11,15,27"
  }
}
```

## 📈 Erweiterte Features

### Automatisches Tracking

```python
# Scheduler starten (alle 6 Stunden)
tracker.start_scheduler(interval_hours=6)

# Status prüfen
status = tracker.get_scheduler_status()
print(f"Läuft: {status['scheduler_running']}")
print(f"Nächster Lauf: {status['next_run']}")

# Scheduler stoppen
tracker.stop_scheduler()
```

### Batch-Processing

```python
# Alle Apps die Updates benötigen (älter als 6h)
result = tracker.process_all_pending_apps_optimized(hours_threshold=6)

print(f"📊 {result['total_successful']}/{result['total_apps']} Apps")
print(f"⏱️ Dauer: {result['total_duration']}s")
print(f"⚡ {result['apps_per_second']:.1f} Apps/s")
```

### CSV-Export

```python
# Export für einzelne App
csv_file = tracker.export_price_history_csv("413150")
print(f"✅ Export erstellt: {csv_file}")
```

**CSV-Format (Excel/Pandas kompatibel):**
```csv
date,Steam,GreenManGaming,GOG,HumbleStore,Fanatical,GamesPlanet
2024-12-20,14.99,13.49,,12.99,13.99,14.49
2024-12-19,14.99,13.49,,12.99,13.99,14.49
```

### Datenbank-Wartung

```python
# Alte Daten bereinigen (>90 Tage)
deleted = db.cleanup_old_prices(days=90)
print(f"🧹 {deleted} alte Snapshots entfernt")

# Backup erstellen
backup_file = db.backup_database()
print(f"💾 Backup: {backup_file}")

# Datenbank optimieren
db.vacuum_database()
```

## 🛠️ Setup und Tools

### Setup-Wizard

```bash
# Vollständiges Setup
python setup.py setup

# Nur Abhängigkeiten installieren
python setup.py install

# System-Status prüfen
python setup.py status

# API-Verbindungen testen
python setup.py test-api
```

### Systemanforderungen

- **Python:** 3.8 oder höher
- **Betriebssystem:** Windows, macOS, Linux
- **Speicher:** ~50MB für Datenbank bei 1000 Apps
- **Internet:** Für CheapShark und Steam APIs

### Dependencies

**Kern-Requirements:**
- `requests>=2.31.0` - HTTP-Requests
- `schedule>=1.2.0` - Automatisches Scheduling
- `python-dotenv>=1.0.0` - Environment Variables

**Optional:**
- `pandas>=2.0.0` - Erweiterte Datenanalyse
- `rich>=13.7.0` - Bessere CLI-Ausgabe
- `tqdm>=4.66.0` - Progress Bars

## 📊 Beispiel-Workflows

### 1. Erste Einrichtung

```bash
# 1. Setup-Wizard starten
python setup.py setup

# 2. Steam API Key in .env eintragen
# 3. Hauptanwendung starten
python main.py

# 4. Wishlist importieren (Option 2)
# 5. Automatisches Tracking starten (Option 7)
```

### 2. Tägliche Nutzung

```bash
# Beste Deals anzeigen
python main.py
# -> Option 4: Beste aktuelle Deals

# Preisverlauf einer App
python main.py
# -> Option 5: Preisverlauf für App

# CSV-Export erstellen
python main.py
# -> Option 10: CSV-Export
```

### 3. Wartung

```bash
# System-Status prüfen
python setup.py status

# Datenbank-Cleanup
python -c "
from database_manager import DatabaseManager
db = DatabaseManager()
db.cleanup_old_prices(days=60)
db.vacuum_database()
"
```

## 🔍 Troubleshooting

### Häufige Probleme

**1. AttributeError: 'SteamPriceTracker' object has no attribute 'get_scheduler_status'**
```bash
# Lösung: Verwende die vollständigen Dateien aus diesem Repository
# Alle Methoden sind in price_tracker.py implementiert
```

**2. Steam API Key Fehler**
```bash
# Prüfe API Key in .env
python setup.py test-api

# Neu generieren auf: https://steamcommunity.com/dev/apikey
```

**3. CheapShark API Rate Limiting**
```bash
# Rate Limit in .env erhöhen
CHEAPSHARK_RATE_LIMIT=2.0
```

**4. Datenbank-Fehler**
```bash
# Datenbank neu initialisieren
python setup.py init-db
```

### Debug-Modus

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Ausführliche API-Logs
tracker = SteamPriceTracker()
tracker.print_price_summary("413150")  # Debug-Ausgabe
```

## 🤝 Beitragen

1. Fork das Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/AmazingFeature`)
3. Committe deine Änderungen (`git commit -m 'Add AmazingFeature'`)
4. Push zum Branch (`git push origin feature/AmazingFeature`)
5. Öffne eine Pull Request

## 📄 Lizenz

Dieses Projekt ist unter der MIT Lizenz lizensiert - siehe [LICENSE](LICENSE) für Details.

## 🙏 Danksagungen

- **CheapShark API** für kostenlose Preisdaten
- **Steam Web API** für Wishlist-Integration
- **Projekt_SteamGoG.ipynb** für Store-Mapping Insights

## 📞 Support

- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/your-repo/issues)
- 💡 **Feature Requests:** [GitHub Discussions](https://github.com/your-repo/discussions)
- 📧 **Email:** your-email@example.com

---

**⭐ Gefällt dir das Projekt? Gib uns einen Stern auf GitHub!**
