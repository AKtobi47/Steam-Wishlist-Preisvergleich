# 💰 Steam Price Tracker v1.0

**Direktes CheapShark-Preis-Tracking für Steam Apps ohne Mapping-Komplexität**

## ✨ Features

- 🎯 **Direktes CheapShark-Tracking** mit Steam App IDs (kein Mapping erforderlich)
- 📊 **Multi-Store Preisvergleich** für Steam, GreenManGaming, GOG, HumbleStore, Fanatical, GamesPlanet
- 📥 **Steam Wishlist Import** für automatisches Setup
- ⚡ **Automatisches Preis-Tracking** mit konfigurierbaren Intervallen
- 🗄️ **SQLite-Datenbank** für historische Preisdaten
- 📈 **Preisverlauf und Trend-Analyse**
- 🏆 **Best Deals Detection** mit Rabatt-Tracking
- 📄 **CSV-Export** kompatibel mit Projekt_SteamGoG.ipynb
- 🔧 **Einfache CLI-Interface** für alle Funktionen

## 🚀 Schnellstart

### 1. Setup

```bash
# Repository klonen
git clone <repository-url>
cd steam-price-tracker

# Dependencies installieren
pip install -r requirements.txt

# Steam API Key konfigurieren
cp .env.example .env
# .env bearbeiten und STEAM_API_KEY eintragen
```

### 2. Steam API Key

1. Gehe zu [Steam Web API Key](https://steamcommunity.com/dev/apikey)
2. Erstelle einen API Key
3. Trage ihn in die `.env`-Datei ein:

```env
STEAM_API_KEY=dein_api_key_hier
```

### 3. Erste Nutzung

```bash
# Hauptanwendung starten
python main.py

# Oder direkter Import einer Wishlist
python -c "
from price_tracker import SteamPriceTracker
tracker = SteamPriceTracker()
tracker.import_steam_wishlist('76561197960435530', 'dein_api_key')
"
```

## 📦 Architektur

### Hauptkomponenten

```
steam-price-tracker/
├── main.py                     # Hauptanwendung mit CLI
├── price_tracker.py            # Kern-Klasse für CheapShark-Tracking
├── database_manager.py         # SQLite-Datenbank-Management
├── steam_wishlist_manager.py   # Vereinfachter Wishlist-Import
├── config.json                 # Konfigurationsdatei
├── requirements.txt            # Python-Dependencies
└── .env                        # API Keys (nicht versioniert)
```

### Datenbank-Schema

**tracked_apps** - Apps die getrackt werden
- `steam_app_id` (PRIMARY KEY)
- `name`, `added_at`, `last_price_update`, `active`

**price_snapshots** - Historische Preisdaten
- `steam_app_id`, `game_title`, `timestamp`
- Preise für alle 6 Stores: `steam_price`, `greenmangaming_price`, etc.
- Rabatt-Informationen: `*_discount_percent`, `*_available`

**price_alerts** - Preis-Benachrichtigungen (geplant)
- `steam_app_id`, `target_price`, `store_name`, `active`

## 🎯 Nutzung

### CLI-Interface

Das Hauptprogramm bietet ein interaktives Menü:

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
9. 📄 CSV-Export

### Programmatische Nutzung

```python
from price_tracker import SteamPriceTracker

# Tracker initialisieren
tracker = SteamPriceTracker()

# App zum Tracking hinzufügen
tracker.add_app_to_tracking("413150", "Stardew Valley")

# Steam Wishlist importieren
result = tracker.import_steam_wishlist("76561197960435530", "dein_api_key")

# Preise aktualisieren
tracker.track_app_prices(["413150", "105600", "582010"])

# Automatisches Tracking starten
tracker.start_price_tracking_scheduler(interval_hours=6)

# Preisverlauf abrufen
history = tracker.get_price_history("413150", days_back=30)

# Beste Deals abrufen
deals = tracker.get_current_best_deals(limit=10)
```

## 🔧 Konfiguration

### Umgebungsvariablen (.env)

```env
# Erforderlich
STEAM_API_KEY=dein_steam_api_key

# Optional
TRACKER_DB_PATH=steam_price_tracker.db
TRACKING_INTERVAL_HOURS=6
CHEAPSHARK_RATE_LIMIT=1.5
```

### Konfigurationsdatei (config.json)

```json
{
  "database": {
    "path": "steam_price_tracker.db",
    "cleanup_days": 90
  },
  "tracking": {
    "default_interval_hours": 6,
    "stores": ["Steam", "GreenManGaming", "GOG", "HumbleStore", "Fanatical", "GamesPlanet"],
    "max_apps_per_update": 100
  },
  "cheapshark": {
    "rate_limit_seconds": 1.5,
    "timeout_seconds": 15
  }
}
```

## 📊 Store-Integration

### Unterstützte Stores

Basierend auf **Projekt_SteamGoG.ipynb** werden folgende Stores getrackt:

| Store ID | Store Name | API Support |
|----------|------------|-------------|
| 1 | Steam | ✅ |
| 3 | GreenManGaming | ✅ |
| 7 | GOG | ✅ |
| 11 | HumbleStore | ✅ |
| 15 | Fanatical | ✅ |
| 27 | GamesPlanet | ✅ |

### CheapShark API

- **Direkte Steam App ID Abfrage:** `GET /deals?steamAppID={app_id}&storeID=1,3,7,11,15,27`
- **Rate Limiting:** 1.5 Sekunden zwischen Requests
- **Automatische Retry-Logic** bei Fehlern

## 📈 Features im Detail

### Automatisches Tracking

```python
# Scheduler starten (alle 6 Stunden)
tracker.start_price_tracking_scheduler(interval_hours=6)

# Status prüfen
status = tracker.get_scheduler_status()
print(f"Läuft: {status['scheduler_running']}")
print(f"Nächster Lauf: {status['next_run']}")
```

### Preisverlauf-Analyse

```python
# 30-Tage Preisverlauf
history = tracker.get_price_history("413150", days_back=30)

for snapshot in history:
    print(f"Datum: {snapshot['timestamp']}")
    for store, prices in snapshot['prices'].items():
        if prices['available']:
            print(f"  {store}: €{prices['price']:.2f}")
```

### Best Deals Detection

```python
# Top 10 aktuelle Deals (höchste Rabatte)
deals = tracker.get_current_best_deals(limit=10)

for deal in deals:
    print(f"{deal['game_title']}: €{deal['price']:.2f} "
          f"(-{deal['discount_percent']}%) bei {deal['store']}")
```

### CSV-Export (Kompatibel mit Projekt_SteamGoG.ipynb)

```python
# Export in gleichem Format wie Projekt_SteamGoG.ipynb
csv_file = tracker.export_price_history_csv("413150")
```

**CSV-Format:**
```csv
date,Steam,GreenManGaming,GOG,HumbleStore,Fanatical,GamesPlanet
2024-12-20,14.99,13.49,,12.99,13.99,14.49
2024-12-19,14.99,13.49,,12.99,13.99,14.49
```

## 🔧 Erweiterte Funktionen

### Datenbank-Wartung

```python
from database_manager import DatabaseManager

db = DatabaseManager()

# Alte Daten bereinigen (>90 Tage)
db.cleanup_old_prices(days=90)

# Backup erstellen
backup_file = db.backup_database()

# Datenbank optimieren
db.vacuum_database()

# Statistiken abrufen
stats = db.get_tracking_statistics()
```

### Steam Wishlist Integration

```python
from steam_wishlist_manager import SteamWishlistManager

wishlist_manager = SteamWishlistManager("dein_api_key")

# Einfacher Wishlist-Abruf
wishlist = wishlist_manager.get_simple_wishlist("76561197960435530")

# Automatischer Import ins Tracking
for item in wishlist:
    tracker.add_app_to_tracking(str(item['appid']), item['name'])
```

## 🚦 Performance & Limits

### Geschwindigkeiten
- **CheapShark-Abfrage:** ~40 Apps/Minute (API-limitiert)
- **Steam Wishlist-Import:** 50-200 Apps in 10-30 Sekunden
- **Preisverlauf-Export:** 1000+ Snapshots in <1 Sekunde

### API-Limits
- **CheapShark API:** ~40 Requests/Minute (1.5s Intervall)
- **Steam API:** ~60 Requests/Minute (1s Intervall)

### Speicherbedarf
- **Minimale Installation:** ~5MB
- **Pro getrackte App:** ~50KB Preisverlauf/Jahr
- **100 Apps, 1 Jahr:** ~10-20MB

## 🔄 Migration von Projekt_SteamGoG.ipynb

Wenn Sie bereits CSV-Daten aus dem Jupyter Notebook haben:

```python
import csv
from datetime import datetime

# CSV-Daten importieren (manuell)
def import_csv_history(app_id, csv_file, game_title):
    tracker = SteamPriceTracker()
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Konvertiere CSV-Format zu Tracker-Format
            price_data = {
                'steam_app_id': app_id,
                'game_title': game_title,
                'timestamp': row['date'] + 'T12:00:00',
                'status': 'success',
                'prices': {}
            }
            
            for store in tracker.STORES.values():
                price = row.get(store, '')
                price_data['prices'][store] = {
                    'price': float(price) if price else None,
                    'available': bool(price),
                    'original_price': float(price) if price else None,
                    'discount_percent': 0
                }
            
            tracker.db_manager.save_price_snapshot(price_data)

# Beispiel-Import
import_csv_history("413150", "StardewValley.csv", "Stardew Valley")
```

## 🛠️ Troubleshooting

### Häufige Probleme

#### "❌ Kein API Key gefunden"
**Lösung:** 
1. Erstelle einen Steam Web API Key: https://steamcommunity.com/dev/apikey
2. Trage ihn in die `.env`-Datei ein: `STEAM_API_KEY=dein_key`

#### "⚠️ Rate Limit erreicht"
**Lösung:**
- Das System hat automatisches Rate Limiting
- Bei Problemen in `config.json` anpassen:
```json
{
  "cheapshark": {"rate_limit_seconds": 2.0}
}
```

#### "❌ Keine Preisdaten gefunden"
**Ursachen:**
- App nicht auf CheapShark verfügbar
- Ungültige Steam App ID
- Temporäre API-Probleme

**Lösung:**
```python
# Prüfe App manuell
tracker.print_price_summary("413150")
```

#### "📭 Wishlist ist leer"
**Ursachen:**
- Steam-Profil ist privat
- Ungültige Steam ID
- API-Probleme

**Lösung:**
```python
# Validiere Steam ID
wishlist_manager.validate_steam_id("76561197960435530")
```

### Debug-Modus

```python
import logging

# Verbose Logging aktivieren
logging.basicConfig(level=logging.DEBUG)

# Oder einzelne Komponenten debuggen
tracker = SteamPriceTracker()
tracker.get_game_prices_from_cheapshark("413150")
```

## 📊 Vergleich mit dem ursprünglichen System

### Vereinfachungen
- ❌ **Entfernt:** CheapShark-zu-Steam-App-Mapping
- ❌ **Entfernt:** Komplexe Bulk-Import-Strategien  
- ❌ **Entfernt:** CheapShark-Mapping-Processor

### Neue Features
- ✅ **Neu:** Direkter CheapShark-Zugriff mit Steam App IDs
- ✅ **Neu:** Fokussiertes Preis-Tracking ohne Mapping-Overhead
- ✅ **Neu:** CSV-Export kompatibel mit Projekt_SteamGoG.ipynb
- ✅ **Neu:** Vereinfachte Datenbank-Struktur
- ✅ **Neu:** Streamlined CLI-Interface

### Performance-Verbesserungen
- 🚀 **Faster:** Keine Mapping-Schritte erforderlich
- 🚀 **Simpler:** Direkte API-Calls
- 🚀 **Lighter:** Reduzierte Datenbank-Komplexität

## 🔮 Geplante Features

- 🚨 **Price Alerts:** E-Mail/Push-Benachrichtigungen bei Zielpreisen
- 📱 **Web Interface:** Browser-basierte GUI
- 📈 **Advanced Analytics:** Preistrend-Vorhersagen
- 🔄 **Auto-Wishlist-Sync:** Automatische Synchronisation mit Steam
- 🎯 **Smart Tracking:** ML-basierte Deal-Empfehlungen

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE) für Details.

## 🙏 Danksagungen

- **CheapShark** für die kostenlose Preisvergleichs-API
- **Valve** für die Steam Web API
- **Projekt_SteamGoG.ipynb** als Basis für Store-Integration

---

**Viel Spaß beim Preis-Tracking! 💰✨**