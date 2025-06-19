# Steam Price Tracker API Documentation

> **Version:** 1.1  
> **Base URL:** `http://localhost:5601` (Kibana Dashboard - Optional)  
> **API Type:** Local CLI Application (Kein Webserver)  
> **Authentication:** Steam Web API Key  
> **Note:** Dies ist eine Desktop-Anwendung ohne HTTP-API. Die URLs dienen zur Kibana-Integration.

## 🚀 API-Übersicht

Die Steam Price Tracker API ermöglicht automatisches Preis-Tracking für Steam-Spiele durch Integration der Steam Web API und CheapShark API. Entwickler können Wishlist-Management, Preisüberwachung und detaillierte Preisverlaufsanalysen implementieren.

**Hauptfunktionen:**
- 📋 Steam Wishlist Import/Export
- 💰 Multi-Store Preisvergleich (Steam, GOG, HumbleBundle, etc.)
- 📊 Historische Preistrends und Charts
- 🔔 Preis-Alerts und Benachrichtigungen
- 📈 Batch-Processing für große App-Listen

**Limitierungen:**
- Steam API: 1 Request/Sekunde
- CheapShark API: 1 Request/1.5 Sekunden
- Max. 100 Apps pro Batch-Update

---

## 📋 Inhaltsverzeichnis

### 🚀 Einstieg
- [Getting Started Guide](#-getting-started-guide) - Schritt-für-Schritt Setup
- [Authentifizierung](#-authentifizierung) - Steam API Key Setup
- [Installation und Setup](#-installation-und-setup) - Lokale Installation & Docker

### 📚 Referenz-Dokumentation
- [Vollständige Klassen- und Methoden-Referenz](#-vollständige-klassen--und-methoden-referenz)
  - [DatabaseManager](#databasemanager) - Datenbank-Verwaltung
  - [SteamPriceTracker](#steampricetracker) - Haupt-Tracking-Klasse
  - [SteamWishlistManager](#steamwishlistmanager) - Steam API Integration
  - [SteamChartsManager](#steamchartsmanager) - Charts-Tracking
  - [BackgroundScheduler](#backgroundscheduler) - Task-Scheduling
  - [ConfigManager](#configmanager) - Konfigurationsverwaltung
  - [CLI-Anwendungen](#cli-anwendungen) - Kommandozeilen-Tools

### 💻 Funktions-Referenz
- [CLI-Funktionen Referenz](#-cli-funktionen-referenz)
  - [Steam Wishlist Manager](#steam-wishlist-manager) - Wishlist Import/Export
  - [Price Tracker Manager](#price-tracker-manager) - Preis-Tracking
  - [Batch Processing](#batch-processing) - Automatisierte Updates

### ⚠️ Entwicklung
- [Fehlerbehandlung](#️-fehlerbehandlung) - Error Handling & Debugging
- [Code-Beispiele und Tutorials](#-code-beispiele-und-tutorials)
  - [Tutorial 1: Vollständiges Wishlist-Tracking Setup](#tutorial-1-vollständiges-wishlist-tracking-setup)
  - [Tutorial 2: Automatisches Deal-Monitoring](#tutorial-2-automatisches-deal-monitoring)
  - [Tutorial 3: Preis-Alert System](#tutorial-3-preis-alert-system)

### 🔧 Erweiterte Features
- [Performance-Optimierung](#-performance-optimierung) - Batch-Processing & Caching
- [Datenexport und -integration](#-datenexport-und--integration) - CSV/JSON Export
- [Python-Bibliothek und Integration](#-python-bibliothek-und-integration) - Package-Integration
- [Integration mit anderen Services](#-integration-mit-anderen-services)
  - [Discord Bot Integration](#discord-bot-integration-lokal)
  - [Web Dashboard Integration](#web-dashboard-integration-flask)
  - [Telegram Bot Integration](#telegram-bot-integration)

### 📊 Analytics & Monitoring
- [Analytics und Monitoring](#-analytics-und-monitoring) - Prometheus Metriken
- [Support und Wartung](#-support-und-wartung) - Logging & Health Checks

### 🆘 Support
- [Support und Community](#-support-und-community) - Hilfe & Beitragen
- [Roadmap und zukünftige Features](#-roadmap-und-zukünftige-features) - Entwicklungsplan

---

## 🏁 Getting Started Guide

### Voraussetzungen

- **Python 3.8+** installiert
- **Steam Web API Key** ([hier anfordern](https://steamcommunity.com/dev/apikey))
- **Internetverbindung** für API-Zugriffe

### 1. Installation

```bash
# Repository klonen
git clone https://github.com/your-repo/steam-price-tracker.git
cd steam-price-tracker

# Abhängigkeiten installieren  
pip install -r requirements.txt

# Setup-Wizard ausführen
python setup.py setup
```

### 2. Authentifizierung einrichten

```bash
# .env-Datei erstellen
cp env_Template.txt .env

# Steam API Key eintragen (ersetzen Sie YOUR_KEY_HERE)
echo "STEAM_API_KEY=YOUR_STEAM_API_KEY_HERE" > .env
```

#### Steam API Key erhalten:
1. Besuchen Sie [steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey)
2. Melden Sie sich mit Ihrem Steam-Account an
3. Geben Sie eine Domain ein (für lokale Entwicklung: `localhost`)
4. Kopieren Sie den generierten API Key

### 3. Erster API-Aufruf

```python
from steam_wishlist_manager import SteamWishlistManager

# Manager initialisieren
api_key = "YOUR_STEAM_API_KEY"
steam_manager = SteamWishlistManager(api_key)

# API Key validieren
if steam_manager.validate_api_key():
    print("✅ Steam API Key funktioniert!")
    
    # Erste Wishlist laden
    steam_id = "76561198000000000"  # Ihre Steam ID
    wishlist = steam_manager.get_simple_wishlist(steam_id)
    print(f"📋 {len(wishlist)} Spiele in der Wishlist gefunden")
else:
    print("❌ Steam API Key ungültig")
```

**Erwartete Antwort:**
```json
[
  {
    "steam_app_id": "413150",
    "name": "Stardew Valley",
    "price": "13.79",
    "discount_percent": 0,
    "original_price": "13.79"
  }
]
```

### 4. Troubleshooting

| Problem | Lösung |
|---------|--------|
| `403 Forbidden` | API Key ungültig oder Domain falsch |
| `Rate Limit Exceeded` | 1 Sekunde zwischen Requests warten |
| `Empty Response` | Steam ID prüfen oder Wishlist öffentlich machen |

### 5. Was als nächstes?

- 📚 [Vollständige API-Referenz](#api-referenz) durchgehen
- 🛠️ [Code-Beispiele](#code-beispiele-und-tutorials) ausprobieren
- 🔔 [Preis-Alerts einrichten](#preis-tracking-einrichten)

---

## 📚 Vollständige Klassen- und Methoden-Referenz

### Core Classes

#### `DatabaseManager`
**Datei:** `database_manager.py`  
**Zweck:** Zentrale Datenbank-Verwaltung für alle Steam Price Tracker Operationen

**Konstruktor:**
```python
DatabaseManager(db_path: str = "steam_price_tracker.db")
```

**Hauptmethoden:**

| Methode | Beschreibung | Parameter | Rückgabe |
|---------|--------------|-----------|----------|
| `get_connection()` | Erstellt neue DB-Verbindung | - | `sqlite3.Connection` |
| `add_tracked_app()` | Fügt App zum Tracking hinzu | `steam_app_id`, `name`, `target_price` | `bool` |
| `get_tracked_apps()` | Holt alle getrackte Apps | `active_only=True` | `List[Dict]` |
| `save_price_snapshot()` | Speichert Preis-Snapshot | `steam_app_id`, `price_data` | `bool` |
| `get_price_history()` | Holt Preisverlauf | `steam_app_id`, `days` | `List[Dict]` |
| `cleanup_old_prices()` | Löscht alte Preisdaten | `days=90` | `int` |
| `get_database_stats()` | DB-Statistiken | - | `Dict` |
| `backup_database()` | Erstellt DB-Backup | `backup_path` | `bool` |
| `vacuum_database()` | Optimiert DB | - | `bool` |

**Charts-spezifische Methoden:**
```python
init_charts_tables()                    # Initialisiert Charts-Tabellen
add_chart_game()                        # Fügt Charts-Spiel hinzu
get_active_chart_games()                # Holt aktive Charts-Spiele
cleanup_old_chart_games()               # Bereinigt alte Charts-Daten
get_charts_statistics()                 # Charts-Statistiken
```

---

#### `SteamPriceTracker`
**Datei:** `price_tracker.py`  
**Zweck:** Hauptklasse für Preis-Tracking und Scheduler-Management

**Konstruktor:**
```python
SteamPriceTracker(db_manager=None, api_key=None, enable_charts=True)
```

**Kern-Funktionalitäten:**

| Methode | Beschreibung | Parameter | Rückgabe |
|---------|--------------|-----------|----------|
| `add_or_update_app()` | App zum Tracking hinzufügen | `steam_app_id`, `name`, `target_price` | `bool` |
| `track_app_prices()` | Preise für Apps aktualisieren | `app_ids: List[str]` | `Dict` |
| `get_best_deals()` | Beste aktuelle Deals | `min_discount_percent`, `limit` | `List[Dict]` |
| `print_price_summary()` | Preis-Zusammenfassung anzeigen | `steam_app_id` | `None` |
| `export_to_csv()` | CSV-Export erstellen | `filename`, `include_history` | `str` |

**Batch-Processing:**
```python
process_all_pending_apps_optimized()   # Optimiertes Batch-Update
process_app_batch()                     # Batch-Verarbeitung
get_apps_needing_update()              # Apps die Updates benötigen
```

**Scheduler-Management:**
```python
start_background_scheduler()           # Startet Background-Tracking
stop_background_scheduler()            # Stoppt Background-Tracking
get_scheduler_status()                 # Scheduler-Status abrufen
enable_charts_tracking()               # Charts-Tracking aktivieren
disable_charts_tracking()              # Charts-Tracking deaktivieren
```

**Charts-Integration:**
```python
_initialize_charts_integration_fixed() # Charts-Integration initialisieren
get_tracked_charts_summary()          # Charts-Übersicht
```

---

#### `SteamWishlistManager`
**Datei:** `steam_wishlist_manager.py`  
**Zweck:** Steam Wishlist und App-Daten Management

**Konstruktor:**
```python
SteamWishlistManager(api_key: str)
```

**Hauptmethoden:**

| Methode | Beschreibung | Parameter | Rückgabe |
|---------|--------------|-----------|----------|
| `validate_api_key()` | API Key validieren | - | `bool` |
| `get_simple_wishlist()` | Wishlist abrufen | `steam_id` | `List[Dict]` |
| `get_app_details()` | App-Details abrufen | `app_id` | `Dict` |
| `get_app_name_only()` | Nur App-Name abrufen | `app_id` | `str` |
| `get_multiple_app_names()` | Mehrere App-Namen | `app_ids: List[str]` | `Dict[str, str]` |
| `get_user_info()` | Benutzer-Info abrufen | `steam_id` | `Dict` |

**ID-Konvertierung:**
```python
get_steam_id_64()                      # Steam ID zu 64-bit konvertieren
_wait_for_rate_limit()                 # Rate Limiting
```

**Standalone-Funktionen:**
```python
load_api_key_from_env()                # API Key aus .env laden
quick_wishlist_import()                # Schneller Wishlist-Import
bulk_get_app_names()                   # Bulk-App-Namen abrufen
validate_steam_api_key()               # API Key validieren
get_user_profile()                     # Benutzerprofil abrufen
create_env_template()                  # .env Template erstellen
```

---

#### `SteamChartsManager`
**Datei:** `steam_charts_manager.py`  
**Zweck:** Automatisches Tracking von Steam Charts

**Konstruktor:**
```python
SteamChartsManager(api_key: str, db_manager=None)
```

**Charts-API-Aufrufe:**

| Methode | Beschreibung | Parameter | Rückgabe |
|---------|--------------|-----------|----------|
| `get_most_played_games()` | Meistgespielte Spiele | `count=100` | `List[Dict]` |
| `get_top_sellers()` | Bestseller abrufen | `count=100` | `List[Dict]` |
| `get_new_releases()` | Neue Releases | `count=100` | `List[Dict]` |
| `update_all_charts()` | Alle Charts aktualisieren | - | `Dict` |

**Charts-Verwaltung:**
```python
process_charts_data()                  # Charts-Daten verarbeiten
cleanup_old_chart_games()              # Alte Charts-Daten bereinigen
get_active_chart_games()               # Aktive Charts-Spiele
get_chart_statistics()                 # Charts-Statistiken
set_price_tracker()                    # PriceTracker verknüpfen
```

**Scheduler-Funktionalität:**
```python
start_charts_scheduler()               # Charts-Scheduler starten
stop_charts_scheduler()                # Charts-Scheduler stoppen
get_charts_scheduler_status()          # Scheduler-Status
```

---

#### `BackgroundScheduler`
**Datei:** `background_scheduler.py`  
**Zweck:** Universal Background Task Scheduler

**Hauptklassen:**
```python
BackgroundScheduler(scheduler_name)           # Basis-Scheduler
EnhancedBackgroundScheduler(scheduler_name)   # Erweiterte Version
```

**Scheduler-Management:**

| Methode | Beschreibung | Parameter | Rückgabe |
|---------|--------------|-----------|----------|
| `register_scheduler()` | Scheduler registrieren | `type`, `task_function`, `interval` | `bool` |
| `start_scheduler()` | Scheduler starten | `scheduler_type` | `bool` |
| `stop_scheduler()` | Scheduler stoppen | `scheduler_type` | `bool` |
| `get_scheduler_status()` | Status abrufen | - | `Dict` |
| `cleanup_processes()` | Prozesse bereinigen | - | `int` |

**Factory-Funktionen:**
```python
create_price_tracker_scheduler()       # Price Tracker Scheduler
create_charts_scheduler()              # Charts Scheduler
create_enhanced_price_tracker_scheduler()  # Enhanced Version
create_enhanced_charts_scheduler()     # Enhanced Charts Version
```

---

#### `ConfigManager`
**Datei:** `config.py`  
**Zweck:** Konfigurationsverwaltung

**Konstruktor:**
```python
ConfigManager(config_path: str = "config.json")
```

**Konfigurationsmethoden:**

| Methode | Beschreibung | Parameter | Rückgabe |
|---------|--------------|-----------|----------|
| `load_config()` | Konfiguration laden | - | `None` |
| `save_config()` | Konfiguration speichern | - | `bool` |
| `load_from_environment()` | Aus .env laden | - | `None` |
| `get_database_config()` | DB-Konfiguration | - | `DatabaseConfig` |
| `get_steam_api_config()` | Steam API Config | - | `SteamAPIConfig` |

**Konfigurationsklassen:**
```python
@dataclass DatabaseConfig             # Datenbank-Einstellungen
@dataclass SteamAPIConfig             # Steam API Einstellungen  
@dataclass CheapSharkConfig           # CheapShark API Einstellungen
@dataclass TrackingConfig             # Tracking-Einstellungen
@dataclass ExportConfig               # Export-Einstellungen
@dataclass WishlistConfig             # Wishlist-Einstellungen
```

---

#### `SteamPriceTrackerSetup`
**Datei:** `setup.py`  
**Zweck:** System-Setup und Installation

**Setup-Methoden:**

| Methode | Beschreibung | Parameter | Rückgabe |
|---------|--------------|-----------|----------|
| `basic_setup()` | Basis-Setup | - | `bool` |
| `charts_setup()` | Charts-Setup | - | `bool` |
| `full_setup()` | Vollständiges Setup | - | `bool` |
| `check_python_version()` | Python-Version prüfen | - | `bool` |
| `install_dependencies()` | Dependencies installieren | `upgrade=False` | `bool` |
| `initialize_database()` | Datenbank initialisieren | - | `bool` |
| `test_api_connection_detailed()` | API-Tests | - | `None` |
| `create_backup()` | Backup erstellen | - | `bool` |
| `show_system_status()` | System-Status anzeigen | - | `None` |

---

### CLI-Anwendungen

#### Main CLI (`main.py`)
**Interaktives Hauptmenü mit 27 Optionen:**

1-5: **Wishlist & Apps Management**
- Wishlist-Status anzeigen
- Steam Wishlist importieren  
- Manuell App hinzufügen
- Apps aus Liste importieren
- App aus Tracking entfernen

6-10: **Preis-Tracking**
- Beste aktuelle Deals
- Preisverlauf für App
- Alle Preise aktualisieren
- Einzelne App aktualisieren  
- Batch-Update konfigurieren

11-15: **Automatisierung & Scheduler**
- Automatisches Tracking starten/stoppen
- Scheduler-Status anzeigen
- Charts-Tracking aktivieren
- Background-Prozesse verwalten
- Task-Historie anzeigen

16-20: **Daten & Export**
- CSV-Export erstellen
- Datenbank-Statistiken
- Datenbank bereinigen
- Backup erstellen
- Daten importieren

21-25: **System & Konfiguration**
- Setup-Wizard starten
- System-Status prüfen
- API-Verbindung testen
- Konfiguration anzeigen
- Logs anzeigen

26-27: **Erweiterte Features**
- Elasticsearch-Integration
- Programm beenden

#### Batch Processor CLI (`batch_processor.py`)
**Kommandozeilen-Tool für Batch-Operations:**

```bash
python batch_processor.py [COMMAND] [OPTIONS]

# Verfügbare Kommandos:
batch           # Batch-Update mit Zeitfilter
specific        # Update für spezifische Apps  
pending         # Zeige Apps die Updates benötigen
status          # System-Status anzeigen
test-single     # Teste einzelne App
update-names    # Namen-Updates durchführen
name-candidates # Apps mit generischen Namen
name-history    # Namen-Update Historie
test-name-fetch # Teste Namen-Abruf
```

#### Charts CLI (`charts_cli_manager.py`)
**Charts-Management via Kommandozeile:**

```bash
python charts_cli_manager.py [COMMAND] [OPTIONS]

# Verfügbare Kommandos:
enable          # Charts-Tracking aktivieren
disable         # Charts-Tracking deaktivieren
status          # Charts-Status anzeigen
update          # Manuelle Charts-Aktualisierung
price-update    # Charts-Preise aktualisieren
automate        # Vollautomatisierung einrichten
```

#### Elasticsearch Setup (`elasticsearch_setup.py`)
**Elasticsearch-Integration Setup:**

```bash
python elasticsearch_setup.py [COMMAND] [OPTIONS]

# Verfügbare Kommandos:  
setup           # Vollständiges ES-Setup
export          # Daten zu ES exportieren
status          # ES-Status anzeigen
reset           # ES-Indizes zurücksetzen
```

---

### Utility-Funktionen

#### Convenience Functions (`price_tracker.py`)
```python
create_price_tracker()                 # Tracker-Instanz erstellen
setup_full_automation()                # Vollautomation einrichten
```

#### Environment Management (`steam_wishlist_manager.py`)
```python
load_api_key_from_env()                # API Key aus .env
create_env_template()                  # .env Template erstellen
```

#### Background Task Templates (`background_scheduler.py`)
```python
class EnhancedSchedulerTasks:
    enhanced_price_tracking_task()      # Enhanced Preis-Task
    enhanced_name_update_task()         # Enhanced Namen-Task  
    enhanced_charts_update_task()       # Enhanced Charts-Task
    enhanced_charts_cleanup_task()      # Enhanced Cleanup-Task
```

---

## 🔐 Authentifizierung

### Steam Web API Key

Die Steam Price Tracker API verwendet Steam Web API Keys für die Authentifizierung.

#### Request Header
```http
User-Agent: SteamPriceTracker/1.1
```

#### Environment Setup
```bash
# .env Datei
STEAM_API_KEY=your_steam_api_key_here
STEAM_RATE_LIMIT=1.0
STEAM_TIMEOUT=15
```

#### Programmische Verwendung
```python
from steam_wishlist_manager import load_api_key_from_env

# API Key aus .env laden
api_key = load_api_key_from_env()

# oder direkt verwenden
steam_manager = SteamWishlistManager("your_api_key_here")
```

### Sicherheitsbest-Practices

- ⚠️ **Niemals API Keys in Code committen**
- 🔒 Verwenden Sie `.env` Dateien für lokale Entwicklung
- 🚫 API Keys nicht in Frontend-Code verwenden
- 🔄 Implementieren Sie Token-Rotation für Production

### Authentifizierungsfehler

| HTTP Code | Bedeutung | Lösung |
|-----------|-----------|--------|
| `401` | API Key fehlt | `STEAM_API_KEY` in .env setzen |
| `403` | API Key ungültig | Neuen Key auf Steam generieren |
| `429` | Rate Limit | Request-Frequenz reduzieren |

---

## 📖 CLI-Funktionen Referenz

> **Hinweis:** Steam Price Tracker ist eine Desktop-Anwendung ohne HTTP-API. Die folgenden "Endpunkte" repräsentieren CLI-Funktionen und Programmfunktionalitäten.

### Steam Wishlist Manager

#### Wishlist Import (CLI-Funktion)

**Zweck:** Steam Wishlist für einen Benutzer importieren und in lokaler Datenbank speichern.

**CLI-Verwendung:**
```bash
# Über Hauptmenü
python main.py
# -> Option 2: Steam Wishlist importieren

# Über Python Code
from steam_wishlist_manager import SteamWishlistManager
manager = SteamWishlistManager(api_key)
result = manager.get_simple_wishlist(steam_id)
```

**Funktions-Parameter:**

| Name | Typ | Erforderlich | Beschreibung | Beispiel |
|------|-----|--------------|--------------|----------|
| `steam_id` | string | ✅ | 64-bit Steam ID des Benutzers | `76561198000000000` |
| `api_key` | string | ❌ | Steam API Key (falls nicht in .env) | `ABCD1234567890` |
| `update_names` | boolean | ❌ | Namen von Steam API aktualisieren | `true` |

**Programm-Input:**
```python
# Via Code
manager = SteamWishlistManager(api_key)
result = manager.get_simple_wishlist("76561198000000000")

# Via CLI
# Hauptmenü -> Option 2 -> Steam ID eingeben
```

**Return-Schema:**
```python
[
  {
    "steam_app_id": "413150",
    "name": "Stardew Valley", 
    "price": "13.79",
    "discount_percent": 0,
    "original_price": "13.79"
  }
]
```

**Status-Codes (via Exception Handling):**
- `Success` - Import erfolgreich
- `ValueError` - Ungültige Steam ID
- `requests.HTTPError(401)` - API Key fehlt oder ungültig
- `requests.HTTPError(429)` - Rate Limit erreicht

**Code-Beispiele:**

<details>
<summary>CLI-Verwendung</summary>

```bash
# Interaktives Hauptmenü
python main.py
# Wähle Option 2: "Steam Wishlist importieren"
# Gib deine Steam ID ein: 76561198000000000

# Batch-Modus
python batch_processor.py wishlist-import --steam-id 76561198000000000
```
</details>

<details>
<summary>Python-Integration</summary>

```python
from steam_wishlist_manager import SteamWishlistManager, load_api_key_from_env

# API Key laden
api_key = load_api_key_from_env()
manager = SteamWishlistManager(api_key)

# Wishlist importieren
steam_id = "76561198000000000"
wishlist = manager.get_simple_wishlist(steam_id)

print(f"✅ {len(wishlist)} Wishlist-Items geladen")
for item in wishlist[:5]:  # Erste 5 anzeigen
    print(f"🎮 {item['name']} - €{item['price']}")
```
</details>

<details>
<summary>Vollständiges Setup-Beispiel</summary>

```python
from price_tracker import SteamPriceTracker, create_price_tracker

# Tracker erstellen
tracker = create_price_tracker(enable_charts=True)

# Wishlist importieren und automatisch zum Tracking hinzufügen
steam_id = "76561198000000000"
result = tracker.import_steam_wishlist(steam_id, update_names=True)

print(f"Import-Ergebnis: {result}")
```
</details>

---

#### App-Details abrufen (CLI-Funktion)

**Zweck:** Detaillierte Informationen für eine spezifische Steam-App abrufen.

**CLI-Verwendung:**
```bash
# Über Hauptmenü
python main.py
# -> Option 6: Preisverlauf für App -> App ID eingeben

# Über Batch-Processor
python batch_processor.py test-single --app-id 413150
```

**Funktions-Parameter:**

| Name | Typ | Erforderlich | Beschreibung | Beispiel |
|------|-----|--------------|--------------|----------|
| `app_id` | string | ✅ | Steam App ID | `413150` |
| `country_code` | string | ❌ | Ländercode für Preise | `DE` |
| `language` | string | ❌ | Sprache für Beschreibungen | `german` |

**Return-Schema:**
```python
{
  "steam_app_id": "413150",
  "name": "Stardew Valley",
  "type": "game",
  "is_free": False,
  "developers": ["ConcernedApe"],
  "publishers": ["ConcernedApe"], 
  "genres": ["Indie", "Simulation", "RPG"],
  "release_date": "26 Feb, 2016",
  "price_info": {
    "currency": "EUR",
    "initial": 1379,
    "final": 1379,
    "discount_percent": 0
  },
  "platforms": {
    "windows": True,
    "mac": True,
    "linux": True
  },
  "metacritic": {
    "score": 89,
    "url": "https://www.metacritic.com/game/..."
  }
}
```

**Code-Beispiele:**

<details>
<summary>Python-Code</summary>

```python
from steam_wishlist_manager import SteamWishlistManager, load_api_key_from_env

api_key = load_api_key_from_env()
manager = SteamWishlistManager(api_key)
app_details = manager.get_app_details("413150")

if app_details:
    print(f"🎮 {app_details['name']}")
    print(f"💰 Preis: €{app_details['price_info']['final']/100:.2f}")
    print(f"📅 Release: {app_details['release_date']}")
    print(f"🏆 Metacritic: {app_details['metacritic']['score']}/100")
else:
    print("❌ App nicht gefunden")
```
</details>

---

### Price Tracker Manager

#### App zum Tracking hinzufügen (CLI-Funktion)

**Zweck:** Eine oder mehrere Steam-Apps zum Preis-Tracking hinzufügen.

**CLI-Verwendung:**
```bash
# Über Hauptmenü
python main.py  
# -> Option 3: Manuell App hinzufügen

# Über Batch-Processor  
python batch_processor.py add-apps --app-ids "413150,570,440"
```

**Funktions-Parameter:**

| Name | Typ | Erforderlich | Beschreibung | Beispiel |
|------|-----|--------------|--------------|----------|
| `app_ids` | list | ✅ | Liste von Steam App IDs | `["413150", "570"]` |
| `target_price` | float | ❌ | Zielpreis für Alerts | `9.99` |
| `notify_on_sale` | bool | ❌ | Bei Rabatt benachrichtigen | `True` |

**Programm-Input:**
```python
# Via Code
tracker = SteamPriceTracker()
success = tracker.add_or_update_app(
    steam_app_id="413150",
    name="Stardew Valley", 
    target_price=9.99
)

# Via CLI  
# Hauptmenü -> Option 3 -> App ID und Details eingeben
```

**Return-Schema:**
```python
{
  "success": True,
  "added": 3,
  "skipped": 0, 
  "failed": 0,
  "app_details": [
    {"steam_app_id": "413150", "name": "Stardew Valley", "added": True}
  ]
}
```

**Code-Beispiele:**

<details>
<summary>Python-Code</summary>

```python
from price_tracker import SteamPriceTracker, create_price_tracker

tracker = create_price_tracker()
app_ids = ["413150", "570", "440"]

for app_id in app_ids:
    success = tracker.add_or_update_app(
        steam_app_id=app_id,
        target_price=9.99,
        notify_on_sale=True
    )
    print(f"{'✅' if success else '❌'} App {app_id} hinzugefügt")
```
</details>

---

#### Beste Deals anzeigen (CLI-Funktion)

**Zweck:** Aktuelle beste Deals für getrackte Apps abrufen.

**CLI-Verwendung:**
```bash
# Über Hauptmenü
python main.py
# -> Option 4: Beste aktuelle Deals

# Mit Filtern
python batch_processor.py deals --min-discount 25 --max-price 20
```

**Funktions-Parameter:**

| Name | Typ | Erforderlich | Beschreibung | Beispiel |
|------|-----|--------------|--------------|----------|
| `min_discount` | float | ❌ | Mindestrabatt in Prozent | `25` |
| `max_price` | float | ❌ | Maximaler Preis | `19.99` |
| `limit` | int | ❌ | Anzahl Ergebnisse | `10` |
| `sort_by` | str | ❌ | Sortierung (discount, price, savings) | `discount` |

**Return-Schema:**
```python
{
  "deals": [
    {
      "steam_app_id": "413150",
      "name": "Stardew Valley",
      "current_price": 6.89,
      "original_price": 13.79,
      "discount_percent": 50,
      "savings": 6.90,
      "store": "Steam",
      "deal_url": "https://store.steampowered.com/app/413150/",
      "ends_at": "2024-12-25T23:59:59Z"
    }
  ],
  "total_deals": 1,
  "filters_applied": {
    "min_discount": 25,
    "max_price": 19.99
  }
}
```

**Code-Beispiele:**

<details>
<summary>Python-Code</summary>

```python
from price_tracker import SteamPriceTracker, create_price_tracker

tracker = create_price_tracker()
deals = tracker.get_best_deals(
    min_discount_percent=25,
    max_price=19.99,
    limit=10
)

print(f"🔥 {len(deals)} Top-Deals gefunden:")
for deal in deals:
    savings = deal['original_price'] - deal['current_price']
    print(f"🎮 {deal['name']}")
    print(f"💰 €{deal['current_price']:.2f} (war €{deal['original_price']:.2f})")
    print(f"💸 {deal['discount_percent']}% Rabatt - Sparen Sie €{savings:.2f}")
    print()
```
</details>

---

#### Preisverlauf abrufen (CLI-Funktion)

**Zweck:** Preisverlauf für eine spezifische App abrufen.

**CLI-Verwendung:**
```bash
# Über Hauptmenü
python main.py
# -> Option 5: Preisverlauf für App -> App ID eingeben

# Über Batch-Processor
python batch_processor.py price-history --app-id 413150 --days 90
```

**Funktions-Parameter:**

| Name | Typ | Erforderlich | Beschreibung | Beispiel |
|------|-----|--------------|--------------|----------|
| `app_id` | string | ✅ | Steam App ID | `413150` |
| `days` | int | ❌ | Anzahl Tage zurück | `90` |
| `stores` | list | ❌ | Spezifische Stores | `["steam", "gog"]` |

**Return-Schema:**
```python
{
  "steam_app_id": "413150",
  "name": "Stardew Valley",
  "price_history": [
    {
      "date": "2024-01-15",
      "price": 13.79,
      "store": "Steam",
      "discount_percent": 0
    },
    {
      "date": "2024-01-20", 
      "price": 6.89,
      "store": "Steam",
      "discount_percent": 50
    }
  ],
  "lowest_price": {
    "price": 4.13,
    "date": "2023-12-22",
    "store": "Steam",
    "discount_percent": 70
  },
  "price_stats": {
    "average_price": 10.34,
    "median_price": 11.03,
    "price_volatility": "medium"
  }
}
```

**Code-Beispiele:**

<details>
<summary>Python-Code</summary>

```python
from price_tracker import create_price_tracker
from datetime import datetime, timedelta

tracker = create_price_tracker()

# Preisverlauf der letzten 90 Tage
app_id = "413150"
end_date = datetime.now()
start_date = end_date - timedelta(days=90)

price_history = tracker.get_price_history(
    app_id, 
    start_date=start_date,
    end_date=end_date
)

print(f"📊 Preisverlauf für App {app_id}:")
for entry in price_history[-5:]:  # Letzte 5 Einträge
    print(f"📅 {entry['timestamp'][:10]} - €{entry['price']:.2f} ({entry['store']})")
```
</details>

---

### Batch Processing

#### Batch Preis-Update (CLI-Funktion)

**Zweck:** Preise für mehrere Apps in einem Batch-Vorgang aktualisieren.

**CLI-Verwendung:**
```bash
# Batch-Update mit Zeitfilter
python batch_processor.py batch --hours 6 --max-apps 50

# Alle ausstehenden Apps
python batch_processor.py pending --hours 12
```

**Funktions-Parameter:**

| Name | Typ | Erforderlich | Beschreibung | Beispiel |
|------|-----|--------------|--------------|----------|
| `app_ids` | list | ❌ | Spezifische App IDs | `["413150", "570"]` |
| `hours_threshold` | int | ❌ | Min. Stunden seit letztem Update | `6` |
| `max_apps` | int | ❌ | Max. Apps pro Batch | `100` |

**Programm-Input:**
```bash
# Über Hauptmenü
python main.py
# -> Option 7: Alle Preise aktualisieren

# Über CLI
python batch_processor.py batch --hours 6
```

**Return-Schema:**
```python
{
  "success": True,
  "total_apps": 50,
  "total_successful": 47,
  "total_failed": 3,
  "total_duration": 125.5,
  "apps_per_second": 0.4,
  "failed_apps": ["12345", "67890", "11111"]
}
```

**Code-Beispiele:**

<details>
<summary>Python-Code</summary>

```python
from price_tracker import create_price_tracker

tracker = create_price_tracker()

# Optimiertes Batch-Update
result = tracker.process_all_pending_apps_optimized(hours_threshold=6)

print(f"✅ Batch-Update abgeschlossen:")
print(f"   📊 {result['total_successful']}/{result['total_apps']} Apps erfolgreich")
print(f"   ⏱️ Dauer: {result['total_duration']:.1f}s")
print(f"   ⚡ Geschwindigkeit: {result.get('apps_per_second', 0):.1f} Apps/s")
```
</details>
```

---

## ⚠️ Fehlerbehandlung

### HTTP Status Codes

| Code | Status | Bedeutung | Lösung |
|------|--------|-----------|--------|
| `200` | OK | Request erfolgreich | - |
| `400` | Bad Request | Ungültige Parameter | Parameter prüfen |
| `401` | Unauthorized | API Key fehlt/ungültig | Steam API Key prüfen |
| `403` | Forbidden | Zugriff verweigert | Berechtigungen prüfen |
| `404` | Not Found | Ressource nicht gefunden | App ID/Endpoint prüfen |
| `429` | Too Many Requests | Rate Limit erreicht | Request-Frequenz reduzieren |
| `500` | Internal Server Error | Server-Fehler | Support kontaktieren |
| `503` | Service Unavailable | Wartungsmodus | Später versuchen |

### Fehlerresponse-Format

```json
{
  "error": {
    "code": "INVALID_APP_ID",
    "message": "Steam App ID '12345' not found",
    "details": {
      "app_id": "12345",
      "suggestion": "Verify the App ID exists on Steam"
    },
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Häufige Fehlerszenarien

#### 1. Steam API Key Probleme
```python
from steam_wishlist_manager import validate_steam_api_key

if not validate_steam_api_key():
    print("❌ Steam API Key ungültig")
    print("🔗 Neuen Key generieren: https://steamcommunity.com/dev/apikey")
```

#### 2. Rate Limiting
```python
import time
from requests.exceptions import HTTPError

def safe_api_call(func, *args, **kwargs):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except HTTPError as e:
            if e.response.status_code == 429:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"⏳ Rate limit erreicht, warte {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
    raise Exception("Max retries erreicht")
```

#### 3. Netzwerk-Timeouts
```python
import requests

# Timeout-Konfiguration
session = requests.Session()
session.timeout = (5, 30)  # (connect, read) timeout

# Retry-Strategie
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    backoff_factor=1
)

adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)
```

---

## 💻 Code-Beispiele und Tutorials

### Tutorial 1: Vollständiges Wishlist-Tracking Setup

Dieses Tutorial zeigt, wie Sie ein komplettes Preis-Tracking für Ihre Steam Wishlist einrichten.

```python
"""
Vollständiges Wishlist-Tracking Setup
Schritt-für-Schritt Implementation
"""

from steam_wishlist_manager import SteamWishlistManager, load_api_key_from_env
from price_tracker import SteamPriceTracker
import time

def setup_wishlist_tracking(steam_id: str):
    """Komplettes Wishlist-Tracking Setup"""
    
    # 1. API Key laden und validieren
    api_key = load_api_key_from_env()
    if not api_key:
        print("❌ Steam API Key nicht gefunden in .env")
        return False
    
    # 2. Steam Manager initialisieren
    steam_manager = SteamWishlistManager(api_key)
    if not steam_manager.validate_api_key():
        print("❌ Steam API Key ungültig")
        return False
    
    print("✅ Steam API Key validiert")
    
    # 3. Price Tracker initialisieren
    tracker = SteamPriceTracker()
    
    # 4. Wishlist importieren
    print(f"📋 Importiere Wishlist für Steam ID: {steam_id}")
    wishlist = steam_manager.get_simple_wishlist(steam_id)
    
    if not wishlist:
        print("❌ Wishlist leer oder nicht öffentlich")
        return False
    
    print(f"✅ {len(wishlist)} Spiele in Wishlist gefunden")
    
    # 5. Apps zum Tracking hinzufügen
    added_count = 0
    for item in wishlist:
        app_id = item['steam_app_id']
        name = item['name']
        
        # Zielpreis: 50% des aktuellen Preises
        current_price = float(item.get('price', '0') or '0')
        target_price = current_price * 0.5 if current_price > 0 else None
        
        success = tracker.add_or_update_app(
            steam_app_id=app_id,
            name=name,
            target_price=target_price,
            notify_on_sale=True
        )
        
        if success:
            added_count += 1
            print(f"➕ {name} hinzugefügt (Zielpreis: €{target_price:.2f})")
        
        # Rate limiting beachten
        time.sleep(0.5)
    
    print(f"✅ {added_count}/{len(wishlist)} Spiele zum Tracking hinzugefügt")
    
    # 6. Erstes Preis-Update durchführen
    print("🔄 Starte erstes Preis-Update...")
    update_result = tracker.process_all_pending_apps_optimized(hours_threshold=0)
    
    print(f"✅ Setup abgeschlossen!")
    print(f"   📊 {update_result['total_successful']} Apps erfolgreich aktualisiert")
    print(f"   ⏱️ Dauer: {update_result['total_duration']:.1f}s")
    
    return True

# Verwendung
if __name__ == "__main__":
    # Ihre Steam ID hier eintragen
    steam_id = "76561198000000000"
    setup_wishlist_tracking(steam_id)
```

### Tutorial 2: Automatisches Deal-Monitoring

```python
"""
Automatisches Deal-Monitoring System
Überwacht Preise und benachrichtigt bei guten Deals
"""

from price_tracker import SteamPriceTracker
from datetime import datetime
import json

class DealMonitor:
    def __init__(self):
        self.tracker = SteamPriceTracker()
    
    def find_hot_deals(self, min_discount=30, max_price=20.0):
        """Findet aktuelle Hot Deals"""
        
        deals = self.tracker.get_best_deals(
            min_discount_percent=min_discount,
            max_price=max_price,
            limit=20
        )
        
        hot_deals = []
        for deal in deals:
            # Deal-Score berechnen (Rabatt % + Bewertung)
            score = deal.get('discount_percent', 0)
            if deal.get('metacritic_score'):
                score += deal['metacritic_score'] / 10
            
            deal['score'] = score
            hot_deals.append(deal)
        
        # Nach Score sortieren
        hot_deals.sort(key=lambda x: x['score'], reverse=True)
        return hot_deals
    
    def generate_deal_report(self, deals):
        """Generiert Deal-Report"""
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_deals': len(deals),
            'deals': []
        }
        
        for deal in deals[:10]:  # Top 10
            savings = deal.get('original_price', 0) - deal.get('current_price', 0)
            
            deal_info = {
                'name': deal.get('name', 'Unknown'),
                'current_price': deal.get('current_price', 0),
                'original_price': deal.get('original_price', 0),
                'discount_percent': deal.get('discount_percent', 0),
                'savings': round(savings, 2),
                'score': round(deal.get('score', 0), 1),
                'store': deal.get('store', 'Steam'),
                'url': deal.get('deal_url', '')
            }
            
            report['deals'].append(deal_info)
        
        return report
    
    def save_deal_report(self, report, filename=None):
        """Speichert Deal-Report als JSON"""
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"deals_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Deal-Report gespeichert: {filename}")
        return filename

# Verwendung
def daily_deal_check():
    """Tägliche Deal-Überprüfung"""
    
    monitor = DealMonitor()
    
    print("🔍 Suche nach Hot Deals...")
    deals = monitor.find_hot_deals(min_discount=30, max_price=25.0)
    
    if deals:
        print(f"🔥 {len(deals)} Hot Deals gefunden!")
        
        report = monitor.generate_deal_report(deals)
        filename = monitor.save_deal_report(report)
        
        # Top 3 Deals anzeigen
        print("\n🏆 Top 3 Deals:")
        for i, deal in enumerate(report['deals'][:3], 1):
            print(f"{i}. {deal['name']}")
            print(f"   💰 €{deal['current_price']:.2f} (war €{deal['original_price']:.2f})")
            print(f"   💸 {deal['discount_percent']}% Rabatt - Score: {deal['score']}")
            print()
    else:
        print("😔 Keine interessanten Deals gefunden")

if __name__ == "__main__":
    daily_deal_check()
```

### Tutorial 3: Preis-Alert System

```python
"""
Erweiterte Preis-Alert Implementation
E-Mail/Discord Benachrichtigungen für Zielpreise
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from price_tracker import SteamPriceTracker

class PriceAlertSystem:
    def __init__(self, email_config=None):
        self.tracker = SteamPriceTracker()
        self.email_config = email_config
    
    def check_price_alerts(self):
        """Überprüft alle Apps auf Preis-Alerts"""
        
        # Alle getrackte Apps laden
        tracked_apps = self.tracker.get_tracked_apps()
        alerts = []
        
        for app in tracked_apps:
            app_id = app['steam_app_id']
            target_price = app.get('target_price')
            
            if not target_price:
                continue
            
            # Aktuelle Preise abrufen
            current_deals = self.tracker.get_best_deals_for_app(app_id)
            
            if current_deals:
                best_deal = min(current_deals, key=lambda x: x['current_price'])
                current_price = best_deal['current_price']
                
                # Alert auslösen wenn Zielpreis erreicht
                if current_price <= target_price:
                    alert = {
                        'app_id': app_id,
                        'name': app['name'],
                        'target_price': target_price,
                        'current_price': current_price,
                        'savings': target_price - current_price,
                        'discount_percent': best_deal.get('discount_percent', 0),
                        'store': best_deal.get('store', 'Steam'),
                        'url': best_deal.get('deal_url', '')
                    }
                    alerts.append(alert)
        
        return alerts
    
    def send_email_alert(self, alerts):
        """Sendet E-Mail Benachrichtigung für Alerts"""
        
        if not self.email_config or not alerts:
            return False
        
        # E-Mail HTML generieren
        html_body = self._generate_email_html(alerts)
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🔥 {len(alerts)} Steam Preis-Alert(s)!"
        msg['From'] = self.email_config['from_email']
        msg['To'] = self.email_config['to_email']
        
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        try:
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['username'], self.email_config['password'])
                server.send_message(msg)
            
            print(f"✅ E-Mail Alert gesendet für {len(alerts)} Deals")
            return True
            
        except Exception as e:
            print(f"❌ E-Mail Fehler: {e}")
            return False
    
    def _generate_email_html(self, alerts):
        """Generiert HTML für E-Mail Alert"""
        
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                .deal { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .price { font-size: 18px; font-weight: bold; color: #c73e1d; }
                .savings { color: #00a651; font-weight: bold; }
                .store { background: #1b2838; color: white; padding: 2px 8px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h2>🔥 Steam Preis-Alerts</h2>
            <p>Ihre Zielpreise wurden erreicht!</p>
        """
        
        for alert in alerts:
            html += f"""
            <div class="deal">
                <h3>{alert['name']}</h3>
                <p class="price">€{alert['current_price']:.2f}</p>
                <p>Zielpreis: €{alert['target_price']:.2f}</p>
                <p class="savings">Sie sparen: €{alert['savings']:.2f}</p>
                <p>Rabatt: {alert['discount_percent']}%</p>
                <p><span class="store">{alert['store']}</span></p>
                <p><a href="{alert['url']}">Jetzt kaufen →</a></p>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html

# Verwendung
def setup_price_alerts():
    """Setup für automatische Preis-Alerts"""
    
    # E-Mail Konfiguration (optional)
    email_config = {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'username': 'your-email@gmail.com',
        'password': 'your-app-password',
        'from_email': 'your-email@gmail.com',
        'to_email': 'your-email@gmail.com'
    }
    
    alert_system = PriceAlertSystem(email_config)
    
    # Preis-Alerts überprüfen
    alerts = alert_system.check_price_alerts()
    
    if alerts:
        print(f"🚨 {len(alerts)} Preis-Alert(s) ausgelöst!")
        
        for alert in alerts:
            print(f"🎮 {alert['name']}")
            print(f"💰 €{alert['current_price']:.2f} (Ziel: €{alert['target_price']:.2f})")
            print(f"💸 Sie sparen €{alert['savings']:.2f}")
            print()
        
        # E-Mail senden (optional)
        alert_system.send_email_alert(alerts)
    else:
        print("😔 Keine Preis-Alerts ausgelöst")

if __name__ == "__main__":
    setup_price_alerts()
```

---

## 🔧 Performance-Optimierung

### Batch-Processing Best Practices

```python
# Optimierte Batch-Verarbeitung
from price_tracker import SteamPriceTracker

tracker = SteamPriceTracker()

# Große App-Listen in kleinere Batches aufteilen
app_ids = ["app1", "app2", ...]  # Ihre App-Liste

batch_size = 50
for i in range(0, len(app_ids), batch_size):
    batch = app_ids[i:i + batch_size]
    
    # Batch verarbeiten
    result = tracker.process_app_batch(batch)
    print(f"Batch {i//batch_size + 1}: {result['successful']}/{len(batch)} erfolgreich")
    
    # Rate Limiting zwischen Batches
    time.sleep(2)
```

### Caching-Strategien

```python
from functools import lru_cache
import time

class CachedSteamManager:
    def __init__(self, api_key):
        self.manager = SteamWishlistManager(api_key)
        self._cache_timestamp = {}
    
    @lru_cache(maxsize=1000)
    def get_app_details_cached(self, app_id, cache_duration=3600):
        """App-Details mit Caching (1 Stunde Standard)"""
        cache_key = f"details_{app_id}"
        current_time = time.time()
        
        # Cache-Gültigkeit prüfen
        if cache_key in self._cache_timestamp:
            if current_time - self._cache_timestamp[cache_key] < cache_duration:
                return self.manager.get_app_details(app_id)
        
        # Neuer API-Aufruf
        result = self.manager.get_app_details(app_id)
        self._cache_timestamp[cache_key] = current_time
        
        return result
```

---

## 📊 Datenexport und -integration

### CSV-Export für Excel/Google Sheets

```python
"""
Enhanced CSV Export mit Preishistorie
"""

from price_tracker import SteamPriceTracker
import csv
from datetime import datetime, timedelta

def export_price_tracking_data(filename=None, days=30):
    """Exportiert Tracking-Daten als CSV"""
    
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"steam_tracking_export_{timestamp}.csv"
    
    tracker = SteamPriceTracker()
    
    # Alle getrackte Apps laden
    tracked_apps = tracker.get_tracked_apps()
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'Steam_App_ID', 'Name', 'Current_Price', 'Target_Price',
            'Lowest_Price_30d', 'Highest_Price_30d', 'Average_Price_30d',
            'Discount_Percent', 'Best_Store', 'Days_Since_Update',
            'Metacritic_Score', 'Release_Date', 'Genres'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for app in tracked_apps:
            app_id = app['steam_app_id']
            
            # Preisverlauf der letzten 30 Tage
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            price_history = tracker.get_price_history(
                app_id, 
                start_date=start_date, 
                end_date=end_date
            )
            
            # Preisstatistiken berechnen
            if price_history:
                prices = [p['price'] for p in price_history]
                lowest_price = min(prices)
                highest_price = max(prices)
                average_price = sum(prices) / len(prices)
            else:
                lowest_price = highest_price = average_price = 0
            
            # Aktuelle beste Deals
            current_deals = tracker.get_best_deals_for_app(app_id)
            best_deal = min(current_deals, key=lambda x: x['current_price']) if current_deals else {}
            
            # App-Details laden
            app_details = tracker.get_app_details(app_id)
            
            writer.writerow({
                'Steam_App_ID': app_id,
                'Name': app.get('name', ''),
                'Current_Price': best_deal.get('current_price', 0),
                'Target_Price': app.get('target_price', ''),
                'Lowest_Price_30d': lowest_price,
                'Highest_Price_30d': highest_price, 
                'Average_Price_30d': round(average_price, 2),
                'Discount_Percent': best_deal.get('discount_percent', 0),
                'Best_Store': best_deal.get('store', ''),
                'Days_Since_Update': (datetime.now() - datetime.fromisoformat(app.get('last_update', datetime.now().isoformat()))).days,
                'Metacritic_Score': app_details.get('metacritic', {}).get('score', '') if app_details else '',
                'Release_Date': app_details.get('release_date', '') if app_details else '',
                'Genres': '; '.join(app_details.get('genres', [])) if app_details else ''
            })
    
    print(f"✅ CSV-Export erstellt: {filename}")
    print(f"📊 {len(tracked_apps)} Apps exportiert")
    
    return filename

# Verwendung
export_price_tracking_data(days=90)
```

---

## 🚀 Installation und Setup

### Lokale Installation

#### Systemanforderungen

```text
- Python 3.8 oder höher
- 200 MB freier Festplattenspeicher
- Internetverbindung für API-Zugriffe
- Steam Web API Key (kostenlos)
```

#### Standard-Installation

```bash
# Repository klonen
git clone https://github.com/your-repo/steam-price-tracker.git
cd steam-price-tracker

# Setup-Wizard ausführen
python setup.py setup

# .env-Datei konfigurieren
cp env_Template.txt .env
# Steam API Key in .env eintragen

# Anwendung starten
python main.py
```

#### Docker Container Setup (Optional für Server-Deployment)

```dockerfile
# Dockerfile für Steam Price Tracker
FROM python:3.9-slim

WORKDIR /app

# System-Dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App-Code kopieren
COPY . .

# Environment
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Datenbank-Verzeichnis
VOLUME ["/app/data"]

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "from setup import SteamPriceTrackerSetup; setup = SteamPriceTrackerSetup(); setup.test_apis()" || exit 1

# Start Command (Interaktiver Modus)
CMD ["python", "main.py"]
```

#### Docker Compose für vollständige Stack

```yaml
# docker-compose.yml
version: '3.8'

services:
  steam-tracker:
    build: .
    volumes:
      - ./data:/app/data
      - ./.env:/app/.env:ro
    environment:
      - TRACKER_DB_PATH=/app/data/steam_price_tracker.db
    stdin_open: true
    tty: true
    
  # Optional: Kibana für Analytics  
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
      
  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

### Automatisierung Setup

#### Systemd Service (Linux)

```ini
# /etc/systemd/system/steam-tracker.service
[Unit]
Description=Steam Price Tracker Background Service
After=network.target

[Service]
Type=simple
User=steam-tracker
WorkingDirectory=/opt/steam-price-tracker
Environment=PYTHONPATH=/opt/steam-price-tracker
ExecStart=/usr/bin/python3 main.py --automated
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Service aktivieren
sudo systemctl enable steam-tracker
sudo systemctl start steam-tracker
sudo systemctl status steam-tracker
```

#### Windows Service Setup

```python
# windows_service.py
import win32serviceutil
import win32service
import win32event
import servicemanager
import sys
import os

class SteamTrackerService(win32serviceutil.ServiceFramework):
    _svc_name_ = "SteamPriceTracker"
    _svc_display_name_ = "Steam Price Tracker Service"
    _svc_description_ = "Automatisches Steam Preis-Tracking"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        # Service Hauptlogik
        os.chdir(os.path.dirname(__file__))
        
        from price_tracker import create_price_tracker, setup_full_automation
        
        tracker = create_price_tracker(enable_charts=True)
        setup_full_automation(tracker)
        
        # Service läuft bis Stop-Signal
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(SteamTrackerService)
```

#### Scheduled Tasks Setup

```bash
# Linux Cron Job
# crontab -e
0 */6 * * * cd /path/to/steam-tracker && python batch_processor.py batch --hours 6
0 2 * * * cd /path/to/steam-tracker && python batch_processor.py update-names --generic-only
0 4 * * 0 cd /path/to/steam-tracker && python -c "from price_tracker import create_price_tracker; t=create_price_tracker(); t.db_manager.cleanup_old_prices(90)"
```

```powershell
# Windows Task Scheduler PowerShell
$action = New-ScheduledTaskAction -Execute "python" -Argument "batch_processor.py batch --hours 6" -WorkingDirectory "C:\steam-tracker"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).Date -RepetitionInterval (New-TimeSpan -Hours 6)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "Steam Price Tracker" -Action $action -Trigger $trigger -Settings $settings
```

---

## 📚 Python-Bibliothek und Integration

### Steam Price Tracker als Python-Package

```python
"""
Steam Price Tracker Python Library
Einfache Integration für Python-Projekte
"""

class SteamPriceTrackerClient:
    def __init__(self, api_key=None, db_path="steam_price_tracker.db"):
        self.api_key = api_key or self._load_api_key()
        self.tracker = self._init_tracker(db_path)
    
    def _load_api_key(self):
        """API Key aus .env laden"""
        from steam_wishlist_manager import load_api_key_from_env
        return load_api_key_from_env()
    
    def _init_tracker(self, db_path):
        """Tracker initialisieren"""
        from price_tracker import create_price_tracker
        return create_price_tracker(
            api_key=self.api_key, 
            db_path=db_path, 
            enable_charts=True
        )
    
    def add_to_tracking(self, app_ids, target_price=None):
        """Apps zum Tracking hinzufügen"""
        results = []
        for app_id in app_ids:
            success = self.tracker.add_or_update_app(
                steam_app_id=app_id,
                target_price=target_price
            )
            results.append({"app_id": app_id, "success": success})
        return results
    
    def get_deals(self, min_discount=25, max_price=None):
        """Aktuelle Deals abrufen"""
        return self.tracker.get_best_deals(
            min_discount_percent=min_discount,
            max_price=max_price
        )
    
    def import_wishlist(self, steam_id):
        """Steam Wishlist importieren"""
        return self.tracker.import_steam_wishlist(steam_id)
    
    def get_price_history(self, app_id, days=30):
        """Preisverlauf abrufen"""
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return self.tracker.get_price_history(app_id, start_date, end_date)
    
    def start_automated_tracking(self, interval_hours=6):
        """Automatisches Tracking starten"""
        return self.tracker.start_background_scheduler(
            price_interval_hours=interval_hours
        )
    
    def get_status(self):
        """Tracker-Status abrufen"""
        return {
            "scheduler_running": self.tracker.get_scheduler_status(),
            "tracked_apps": len(self.tracker.get_tracked_apps()),
            "charts_enabled": self.tracker.charts_enabled,
            "database_stats": self.tracker.db_manager.get_database_stats()
        }

# Verwendung des Client
client = SteamPriceTrackerClient()

# Wishlist importieren
result = client.import_wishlist("76561198000000000")
print(f"✅ {result.get('imported', 0)} Spiele importiert")

# Deals abrufen
deals = client.get_deals(min_discount=30, max_price=20.0)
print(f"🔥 {len(deals)} Deals gefunden")

# Automatisches Tracking starten
client.start_automated_tracking(interval_hours=6)
print("🚀 Automatisches Tracking gestartet")
```

### Als Python-Package installieren

```bash
# Setup für Package-Installation
pip install -e .

# requirements.txt für Abhängigkeiten
pip install -r requirements.txt
```

```python
# setup.py für Package-Distribution
from setuptools import setup, find_packages

setup(
    name="steam-price-tracker",
    version="1.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "schedule>=1.2.0",
        "pandas>=1.5.0",
        # weitere Requirements...
    ],
    entry_points={
        'console_scripts': [
            'steam-tracker=main:main',
            'steam-batch=batch_processor:main',
            'steam-charts=charts_cli_manager:main',
        ],
    },
    author="Your Name",
    description="Steam Price Tracker for automatic game price monitoring",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-repo/steam-price-tracker",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
```

---

## 🔗 Integration mit anderen Services

### Discord Bot Integration (Lokal)

```python
"""
Discord Bot für Steam Price Alerts
Integration mit lokaler Steam Price Tracker Installation
"""

import discord
from discord.ext import commands, tasks
import sys
import os

# Steam Tracker Module hinzufügen
sys.path.append('/path/to/steam-price-tracker')
from price_tracker import create_price_tracker

class SteamPriceBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tracker = create_price_tracker(enable_charts=True)
        self.check_deals.start()
    
    @commands.command(name='deals')
    async def get_deals(self, ctx, min_discount: int = 30):
        """Zeigt aktuelle Steam Deals"""
        
        deals = self.tracker.get_best_deals(
            min_discount_percent=min_discount,
            limit=5
        )
        
        if deals:
            embed = discord.Embed(
                title=f"🔥 Top Steam Deals ({min_discount}%+ Rabatt)",
                color=0x00ff00
            )
            
            for deal in deals[:5]:
                embed.add_field(
                    name=deal['name'],
                    value=f"€{deal['current_price']:.2f} (war €{deal['original_price']:.2f})\n"
                          f"{deal['discount_percent']}% Rabatt - {deal['store']}",
                    inline=False
                )
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("😔 Keine Deals gefunden")
    
    @commands.command(name='track')
    async def add_tracking(self, ctx, app_id: str, target_price: float = None):
        """App zum Tracking hinzufügen"""
        
        success = self.tracker.add_or_update_app(
            steam_app_id=app_id,
            target_price=target_price
        )
        
        if success:
            await ctx.send(f"✅ App {app_id} zum Tracking hinzugefügt!")
        else:
            await ctx.send(f"❌ Fehler beim Hinzufügen von App {app_id}")
    
    @commands.command(name='wishlist')
    async def import_wishlist(self, ctx, steam_id: str):
        """Steam Wishlist importieren"""
        
        try:
            result = self.tracker.import_steam_wishlist(steam_id)
            if result.get('success'):
                await ctx.send(
                    f"✅ Wishlist importiert!\n"
                    f"📥 {result.get('imported', 0)} neue Apps\n"
                    f"⏭️ {result.get('skipped_existing', 0)} bereits vorhanden"
                )
            else:
                await ctx.send(f"❌ Import fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")
        except Exception as e:
            await ctx.send(f"❌ Fehler beim Import: {str(e)}")
    
    @tasks.loop(hours=6)
    async def check_deals(self):
        """Automatische Deal-Benachrichtigungen"""
        
        deals = self.tracker.get_best_deals(min_discount_percent=50, limit=3)
        
        if deals:
            channel = self.bot.get_channel(YOUR_CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title="🚨 Hot Steam Deals Alert!",
                    description="Große Rabatte verfügbar!",
                    color=0xff0000
                )
                
                for deal in deals:
                    embed.add_field(
                        name=deal['name'],
                        value=f"€{deal['current_price']:.2f} (-{deal['discount_percent']}%)",
                        inline=True
                    )
                
                await channel.send(embed=embed)

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} is connected to Discord!')
    await bot.add_cog(SteamPriceBot(bot))

bot.run('YOUR_DISCORD_BOT_TOKEN')
```

### Web Dashboard Integration (Flask)

```python
"""
Simple Web Dashboard für Steam Price Tracker
"""

from flask import Flask, render_template, jsonify, request
import sys
import os

# Steam Tracker Module
sys.path.append('/path/to/steam-price-tracker')
from price_tracker import create_price_tracker

app = Flask(__name__)
tracker = create_price_tracker(enable_charts=True)

@app.route('/')
def dashboard():
    """Haupt-Dashboard"""
    stats = tracker.db_manager.get_database_stats()
    return render_template('dashboard.html', stats=stats)

@app.route('/api/deals')
def api_deals():
    """API für aktuelle Deals"""
    min_discount = request.args.get('min_discount', 25, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    deals = tracker.get_best_deals(
        min_discount_percent=min_discount,
        limit=limit
    )
    return jsonify(deals)

@app.route('/api/apps')
def api_apps():
    """API für getrackte Apps"""
    apps = tracker.get_tracked_apps()
    return jsonify(apps)

@app.route('/api/status')
def api_status():
    """System-Status API"""
    status = {
        'scheduler_running': bool(tracker.get_scheduler_status()),
        'tracked_apps': len(tracker.get_tracked_apps()),
        'charts_enabled': tracker.charts_enabled,
        'database_stats': tracker.db_manager.get_database_stats()
    }
    return jsonify(status)

@app.route('/api/track', methods=['POST'])
def api_track():
    """App zum Tracking hinzufügen"""
    data = request.get_json()
    app_id = data.get('app_id')
    target_price = data.get('target_price')
    
    if not app_id:
        return jsonify({'error': 'app_id required'}), 400
    
    success = tracker.add_or_update_app(
        steam_app_id=app_id,
        target_price=target_price
    )
    
    return jsonify({'success': success})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

### Telegram Bot Integration

```python
"""
Telegram Bot für Steam Price Notifications
"""

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import sys

sys.path.append('/path/to/steam-price-tracker')
from price_tracker import create_price_tracker

class SteamTelegramBot:
    def __init__(self, token):
        self.token = token
        self.tracker = create_price_tracker(enable_charts=True)
        self.app = Application.builder().token(token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Bot-Handler einrichten"""
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("deals", self.deals))
        self.app.add_handler(CommandHandler("track", self.track))
        self.app.add_handler(CommandHandler("status", self.status))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start-Kommando"""
        await update.message.reply_text(
            "🎮 Steam Price Tracker Bot\n\n"
            "/deals - Aktuelle Top-Deals\n"
            "/track <app_id> - App zum Tracking hinzufügen\n"
            "/status - System-Status"
        )
    
    async def deals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Aktuelle Deals anzeigen"""
        deals = self.tracker.get_best_deals(min_discount_percent=30, limit=5)
        
        if deals:
            message = "🔥 *Top Steam Deals:*\n\n"
            for deal in deals:
                message += (
                    f"🎮 *{deal['name']}*\n"
                    f"💰 €{deal['current_price']:.2f} "
                    f"(war €{deal['original_price']:.2f})\n"
                    f"💸 {deal['discount_percent']}% Rabatt\n\n"
                )
        else:
            message = "😔 Keine aktuellen Deals gefunden"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def track(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """App zum Tracking hinzufügen"""
        if not context.args:
            await update.message.reply_text("❌ App ID erforderlich: /track <app_id>")
            return
        
        app_id = context.args[0]
        success = self.tracker.add_or_update_app(steam_app_id=app_id)
        
        if success:
            await update.message.reply_text(f"✅ App {app_id} zum Tracking hinzugefügt!")
        else:
            await update.message.reply_text(f"❌ Fehler beim Hinzufügen von App {app_id}")
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """System-Status"""
        stats = self.tracker.db_manager.get_database_stats()
        
        message = (
            f"📊 *System-Status:*\n\n"
            f"🎮 Getrackte Apps: {stats.get('total_apps', 0)}\n"
            f"📈 Preis-Snapshots: {stats.get('total_snapshots', 0)}\n"
            f"🚀 Scheduler: {'Aktiv' if self.tracker.get_scheduler_status() else 'Inaktiv'}\n"
            f"📊 Charts: {'Aktiviert' if self.tracker.charts_enabled else 'Deaktiviert'}"
        )
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    def run(self):
        """Bot starten"""
        print("🤖 Telegram Bot gestartet...")
        self.app.run_polling()

# Bot starten
if __name__ == '__main__':
    bot = SteamTelegramBot('YOUR_TELEGRAM_BOT_TOKEN')
    bot.run()
```

---

## 📈 Analytics und Monitoring

### Prometheus Metriken

```python
"""
Prometheus Monitoring für Steam Price Tracker
"""

from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Metriken definieren
api_requests_total = Counter('steam_api_requests_total', 'Total Steam API requests', ['endpoint', 'status'])
api_request_duration = Histogram('steam_api_request_duration_seconds', 'Steam API request duration')
tracked_apps_total = Gauge('tracked_apps_total', 'Total number of tracked apps')
price_updates_total = Counter('price_updates_total', 'Total price updates', ['status'])

class MonitoredSteamTracker:
    def __init__(self, tracker):
        self.tracker = tracker
    
    def get_app_details(self, app_id):
        """Überwachte App-Details Abfrage"""
        start_time = time.time()
        
        try:
            result = self.tracker.get_app_details(app_id)
            api_requests_total.labels(endpoint='app_details', status='success').inc()
            return result
            
        except Exception as e:
            api_requests_total.labels(endpoint='app_details', status='error').inc()
            raise
            
        finally:
            duration = time.time() - start_time
            api_request_duration.observe(duration)
    
    def update_tracked_apps_metric(self):
        """Aktualisiert Anzahl getrackte Apps"""
        apps = self.tracker.get_tracked_apps()
        tracked_apps_total.set(len(apps))

# Prometheus Server starten
start_http_server(8001)
```

---

## 🆘 Support und Wartung

### Logging und Debugging

```python
import logging
from datetime import datetime

# Erweiterte Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('steam_tracker.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('steam_tracker')

# Performance Logging
class PerformanceTracker:
    def __init__(self):
        self.start_times = {}
    
    def start_timer(self, operation):
        self.start_times[operation] = time.time()
    
    def end_timer(self, operation):
        if operation in self.start_times:
            duration = time.time() - self.start_times[operation]
            logger.info(f"⏱️ {operation} completed in {duration:.2f}s")
            del self.start_times[operation]

# Verwendung
perf = PerformanceTracker()
perf.start_timer("wishlist_import")
# ... API-Operationen ...
perf.end_timer("wishlist_import")
```

### Health Checks

```python
def health_check():
    """Vollständiger System-Health Check"""
    
    health_status = {
        'timestamp': datetime.now().isoformat(),
        'status': 'healthy',
        'checks': {}
    }
    
    # Steam API Check
    try:
        from steam_wishlist_manager import validate_steam_api_key
        steam_ok = validate_steam_api_key()
        health_status['checks']['steam_api'] = 'ok' if steam_ok else 'error'
    except Exception as e:
        health_status['checks']['steam_api'] = f'error: {str(e)}'
    
    # Datenbank Check
    try:
        from database_manager import DatabaseManager
        db = DatabaseManager()
        with db.get_connection() as conn:
            conn.execute('SELECT 1')
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['checks']['database'] = f'error: {str(e)}'
    
    # CheapShark API Check
    try:
        import requests
        response = requests.get('https://www.cheapshark.com/api/1.0/stores', timeout=5)
        health_status['checks']['cheapshark_api'] = 'ok' if response.status_code == 200 else 'error'
    except Exception as e:
        health_status['checks']['cheapshark_api'] = f'error: {str(e)}'
    
    # Gesamtstatus bestimmen
    if any('error' in status for status in health_status['checks'].values()):
        health_status['status'] = 'unhealthy'
    
    return health_status
```

---

## 🔮 Roadmap und zukünftige Features

### Geplante Erweiterungen

1. **GraphQL API Support**
   - Flexible Datenabfragen
   - Reduzierte Over-fetching

2. **Machine Learning Preisvorhersagen**
   - Preistrend-Algorithmen
   - Optimale Kaufzeitpunkt-Empfehlungen

3. **Mobile Apps**
   - iOS/Android Companion Apps
   - Push-Benachrichtigungen

4. **Erweiterte Analytics**
   - Markttrend-Analysen
   - Publisher/Genre-Statistiken

5. **Integration mit Gaming-Plattformen**
   - Epic Games Store
   - Xbox Game Pass
   - PlayStation Store

---

## 📞 Support und Community

### Offizielle Kanäle

- 📖 **Dokumentation:** [docs.steamprice-tracker.com](https://docs.steamprice-tracker.com)
- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/your-repo/issues)
- 💬 **Community:** [Discord Server](https://discord.gg/steam-tracker)
- 📧 **E-Mail Support:** support@steamprice-tracker.com

### Beitragen zur Entwicklung

```bash
# Repository forken und klonen
git clone https://github.com/your-username/steam-price-tracker.git
cd steam-price-tracker

# Development Environment setup
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

pip install -r requirements-dev.txt

# Tests ausführen
python -m pytest tests/

# Linting
black .
flake8 .

# Feature Branch erstellen
git checkout -b feature/amazing-feature
```

### API Versioning und Backwards Compatibility

Die Steam Price Tracker Desktop-Anwendung folgt [Semantic Versioning](https://semver.org/):

- **Major Version** (v1 → v2): Breaking Changes in Klassen/Methoden
- **Minor Version** (v1.1 → v1.2): Neue Features, backwards compatible
- **Patch Version** (v1.1.0 → v1.1.1): Bug Fixes

**Deprecation Policy:**
- 3 Monate Ankündigung vor Breaking Changes
- Legacy-Funktionen werden 6 Monate unterstützt
- Migration-Guides für alle Major Updates
- Automatische Migration-Tools wo möglich

**Aktueller Kompatibilitätsstatus:**
```text
v1.0.x - Basis-Implementation ✅
v1.1.x - Charts-Integration ✅ (Aktuell)
v1.2.x - Elasticsearch-Integration 🚧 (In Entwicklung)
v2.0.x - Moderne GUI-Interface 📋 (Geplant)
```

---

*Diese Dokumentation wurde automatisch generiert basierend auf dem Steam Price Tracker v1.1 Codebase. Das Programm ist eine lokale Desktop-Anwendung ohne HTTP-Server-Funktionalität. Letzte Aktualisierung: June 2025*