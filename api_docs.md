# Steam Price Tracker API Documentation

> **Version:** 1.2-dev  
> **API Type:** Desktop CLI Application + Optional Elasticsearch Integration  
> **Authentication:** Steam Web API Key  
> **Base URL:** `http://localhost:5601` (Kibana Dashboard - Optional)  
> **Support:** Python 3.8+, Windows/macOS/Linux

## 🚀 API-Übersicht

Die Steam Price Tracker API ist eine professionelle Desktop-Anwendung für automatisches Steam-Preis-Tracking mit Multi-Store-Vergleich. Entwickler können komplette Wishlist-Verwaltung, historische Preisanalysen und erweiterte Analytics implementieren.

**🎯 Hauptfunktionen:**
- 📋 **Steam Wishlist Integration** - Vollständiger Import/Export mit API-Validierung
- 💰 **Multi-Store Preisvergleich** - 6 Major Stores (Steam, GOG, HumbleBundle, etc.)
- 📊 **Steam Charts Tracking** - Automatische Charts-Überwachung mit Ranking-Trends
- 🔍 **Elasticsearch Analytics** - Erweiterte Datenanalyse mit Kibana-Dashboards
- 📈 **Historische Preistrends** - Detaillierte Preisverläufe und Statistiken
- 🤖 **Batch-Processing** - Optimierte Updates für große App-Sammlungen

**Rate Limiting:**
- Steam API: 1 Request/Sekunde (konfigurierbar)
- CheapShark API: 1 Request/1.5 Sekunden (konfigurierbar)
- Max. 1000 Apps pro Batch-Update (Charts + Standard)

---

## 📋 Inhaltsverzeichnis

### 🚀 Einstieg
- [Getting Started Guide](#getting-started-guide) - 5-Minuten Setup
- [Authentifizierung](#authentifizierung) - Steam API Key Management
- [Installation & Setup](#installation--setup) - Lokale Installation + Docker

### 📚 API-Referenz
- [Vollständige Klassen-Referenz](#vollständige-klassen-referenz)
  - [DatabaseManager](#databasemanager) - Datenbank-Operationen
  - [SteamPriceTracker](#steampricetracker) - Haupt-Tracking-Engine
  - [SteamWishlistManager](#steamwishlistmanager) - Steam API Integration
  - [SteamChartsManager](#steamchartsmanager) - Charts-Tracking System
  - [ElasticsearchManager](#elasticsearchmanager) - Analytics Engine
- [CLI-Funktionen Referenz](#cli-funktionen-referenz) - Kommandozeilen-Interface

### 💻 Code-Beispiele & Tutorials
- [Tutorial 1: Vollständiges Wishlist-Setup](#tutorial-1-vollständiges-wishlist-setup)
- [Tutorial 2: Charts-Tracking System](#tutorial-2-charts-tracking-system)
- [Tutorial 3: Elasticsearch Analytics](#tutorial-3-elasticsearch-analytics)

### ⚠️ Fehlerbehandlung & Support
- [Fehlerbehandlung](#fehlerbehandlung) - Error Codes & Debugging
- [Performance-Optimierung](#performance-optimierung) - Best Practices
- [Support & Community](#support--community) - Hilfe & Beitragen

---

## 🏁 Getting Started Guide

**Ziel:** Entwickler in unter 10 Minuten zu ihrem ersten erfolgreichen API-Einsatz führen.

### Voraussetzungen

**Software-Anforderungen:**
- Python 3.8+ installiert ([Download](https://python.org/downloads/))
- Git für Repository-Zugriff
- Internetverbindung für API-Zugriffe

**Accounts benötigt:**
- Steam-Account für API-Key ([Steam Community](https://steamcommunity.com))
- *Optional:* Docker für Elasticsearch-Features

### 1. Installation

```bash
# Repository klonen
git clone <your-repository-url>
cd steam-price-tracker

# Automatisches Setup (installiert alles)
python setup.py setup
```

**Was passiert beim Setup:**
- ✅ Python-Dependencies installieren (`requirements.txt`)
- ✅ Datenbank-Schema initialisieren
- ✅ `.env`-Datei für API-Keys erstellen
- ✅ Standard-Konfiguration anlegen
- ✅ System-Kompatibilität prüfen

### 2. Authentifizierung einrichten

#### Steam API Key beschaffen:
1. **Steam Developer Portal besuchen:** [steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey)
2. **Mit Steam-Account anmelden**
3. **Domain eingeben:** Für lokale Entwicklung: `localhost`
4. **API Key kopieren**

#### API Key konfigurieren:
```bash
# .env-Datei wird automatisch erstellt
# Tragen Sie Ihren API Key ein:
echo "STEAM_API_KEY=YOUR_STEAM_API_KEY_HERE" >> .env

# API Key testen
python setup.py test-api
```

### 3. Erster API-Aufruf

```python
from steam_wishlist_manager import SteamWishlistManager
from price_tracker import SteamPriceTracker

# 1. Steam Manager initialisieren
api_key = "IHRE_STEAM_API_KEY"
steam_manager = SteamWishlistManager(api_key)

# 2. API Key validieren
if steam_manager.validate_api_key():
    print("✅ Steam API Key funktioniert!")
    
    # 3. Price Tracker initialisieren
    tracker = SteamPriceTracker()
    
    # 4. Erste Wishlist laden
    steam_id = "76561198000000000"  # Ihre Steam ID
    wishlist = steam_manager.get_simple_wishlist(steam_id)
    print(f"📋 {len(wishlist)} Spiele in der Wishlist gefunden")
    
    # 5. Erstes Spiel zum Tracking hinzufügen
    if wishlist:
        first_game = wishlist[0]
        success = tracker.add_or_update_app(
            steam_app_id=first_game['steam_app_id'],
            name=first_game['name'],
            target_price=float(first_game.get('price', 0)) * 0.7  # 30% Rabatt-Ziel
        )
        print(f"✅ {first_game['name']} zum Tracking hinzugefügt")
else:
    print("❌ Steam API Key ungültig")
```

**Erwartete Antwort:**
```json
{
  "steam_app_id": "413150",
  "name": "Stardew Valley", 
  "price": "13.79",
  "discount_percent": 0,
  "original_price": "13.79"
}
```

### 4. Troubleshooting häufiger Setup-Probleme

| Problem | Ursache | Lösung |
|---------|---------|--------|
| `403 Forbidden` | API Key ungültig | Neuen Key auf [Steam Dev Portal](https://steamcommunity.com/dev/apikey) generieren |
| `ModuleNotFoundError` | Dependencies fehlen | `python setup.py setup` erneut ausführen |
| `Empty Response` | Steam ID falsch | Steam ID validieren oder Wishlist öffentlich machen |
| `Rate Limit Exceeded` | Zu viele Requests | 1 Sekunde zwischen Requests warten |
| `Database Error` | DB nicht initialisiert | `python setup.py init-db` ausführen |

### 5. Was als nächstes?

- 📚 **[Vollständige API-Referenz](#vollständige-klassen-referenz)** für alle verfügbaren Funktionen
- 🛠️ **[Tutorial 1](#tutorial-1-vollständiges-wishlist-setup)** für komplettes Wishlist-Setup
- 📊 **[Charts-Integration](#tutorial-2-charts-tracking-system)** für Steam Charts-Tracking
- 🔍 **[Elasticsearch-Setup](#tutorial-3-elasticsearch-analytics)** für erweiterte Analytics

---

## 🔑 Authentifizierung

### Steam API Key Management

Die Anwendung nutzt **Steam Web API Keys** für alle Steam-bezogenen Operationen.

#### Request Header Format
```http
GET /ISteamUser/GetPlayerSummaries/v0002/?key=YOUR_API_KEY&steamids=76561198000000000
Host: api.steampowered.com
User-Agent: SteamPriceTracker/1.2
Accept: application/json
```

#### Programmische Verwendung

```python
# Automatisches Laden aus .env
from steam_wishlist_manager import load_api_key_from_env

api_key = load_api_key_from_env()
steam_manager = SteamWishlistManager(api_key)

# Manuell setzen
steam_manager = SteamWishlistManager("YOUR_STEAM_API_KEY")

# API Key validieren
is_valid = steam_manager.validate_api_key()
if not is_valid:
    raise ValueError("Steam API Key ungültig")
```

#### Environment-Konfiguration

```env
# .env Datei
STEAM_API_KEY=your_steam_api_key_here
STEAM_RATE_LIMIT=1.0
STEAM_TIMEOUT=15
CHEAPSHARK_RATE_LIMIT=1.5
```

### Sicherheitsbest-Practices

- 🔒 **Niemals API Keys in Code commiten**
- 📁 **Verwenden Sie `.env` Dateien für lokale Entwicklung**
- 🔄 **Implementieren Sie Token-Rotation für Production**
- 🚫 **API Keys nicht in Frontend-Code verwenden**

### Authentifizierungsfehler

| HTTP Code | Bedeutung | Lösung |
|-----------|-----------|--------|
| `401 Unauthorized` | API Key fehlt | `STEAM_API_KEY` in .env setzen |
| `403 Forbidden` | API Key ungültig | Neuen Key auf Steam generieren |
| `429 Too Many Requests` | Rate Limit erreicht | Request-Frequenz reduzieren |
| `500 Internal Server Error` | Steam API temporär nicht verfügbar | Retry mit exponential backoff |

---

## 📖 CLI-Funktionen Referenz

> **Hinweis:** Steam Price Tracker ist eine Desktop-Anwendung. Die "Endpunkte" repräsentieren CLI-Funktionen.

### Steam Wishlist Management

#### Wishlist Import

**Zweck:** Steam Wishlist für einen Benutzer importieren und in lokaler Datenbank speichern.

**CLI-Aufruf:**
```bash
python main.py
# Option 2: Steam Wishlist importieren
```

**Programmischer Aufruf:**
```python
from steam_wishlist_manager import SteamWishlistManager

manager = SteamWishlistManager(api_key)
wishlist = manager.get_simple_wishlist(steam_id)
```

**Parameter:**

| Parameter | Typ | Erforderlich | Beschreibung | Beispiel |
|-----------|-----|--------------|--------------|----------|
| `steam_id` | String | ✅ | Steam User ID (64-bit) | `"76561198000000000"` |
| `api_key` | String | ✅ | Steam Web API Key | `"ABCD1234..."` |
| `batch_size` | Integer | ❌ | Batch-Größe für Import | `50` (Standard) |

**Response Schema:**
```python
{
    "success": bool,
    "imported": int,
    "skipped": int,
    "errors": int,
    "data": [
        {
            "steam_app_id": str,
            "name": str,
            "price": str,
            "discount_percent": int,
            "original_price": str
        }
    ]
}
```

**Anwendungsbeispiele:**

```python
# Basis-Import
result = manager.get_simple_wishlist("76561198000000000")

# Mit Fehlerbehandlung
try:
    wishlist = manager.get_simple_wishlist(steam_id)
    if not wishlist:
        raise ValueError("Wishlist leer oder privat")
except Exception as e:
    print(f"Fehler beim Wishlist-Import: {e}")

# Batch-Import für große Wishlists
def import_large_wishlist(steam_id, batch_size=100):
    wishlist = manager.get_simple_wishlist(steam_id)
    for i in range(0, len(wishlist), batch_size):
        batch = wishlist[i:i+batch_size]
        process_batch(batch)
```

#### App-Details abrufen

**Zweck:** Detaillierte Informationen zu einer Steam-App abrufen.

**Programmischer Aufruf:**
```python
app_details = manager.get_app_details("413150")
```

**Parameter:**

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `app_id` | String | ✅ | Steam Application ID |

**Response Schema:**
```python
{
    "steam_appid": int,
    "name": str,
    "type": str,
    "is_free": bool,
    "detailed_description": str,
    "supported_languages": str,
    "developers": [str],
    "publishers": [str],
    "price_overview": {
        "currency": str,
        "initial": int,
        "final": int,
        "discount_percent": int
    }
}
```

### Price Tracking Management

#### App zum Tracking hinzufügen

**Zweck:** Steam-App zur Preisverfolgung hinzufügen mit optionalen Zielpreis.

**CLI-Aufruf:**
```bash
python main.py
# Option 1: App manuell zum Tracking hinzufügen
```

**Programmischer Aufruf:**
```python
from price_tracker import SteamPriceTracker

tracker = SteamPriceTracker()
success = tracker.add_or_update_app(
    steam_app_id="413150",
    name="Stardew Valley",
    target_price=10.00,
    notify_on_sale=True
)
```

**Parameter:**

| Parameter | Typ | Erforderlich | Beschreibung | Beispiel |
|-----------|-----|--------------|--------------|----------|
| `steam_app_id` | String | ✅ | Steam Application ID | `"413150"` |
| `name` | String | ✅ | Spielname | `"Stardew Valley"` |
| `target_price` | Float | ❌ | Gewünschter Zielpreis | `10.00` |
| `notify_on_sale` | Boolean | ❌ | Benachrichtigung aktivieren | `True` |

**Response:**
```python
{
    "success": bool,
    "app_id": str,
    "message": str,
    "already_tracked": bool
}
```

#### Preise aktualisieren

**Zweck:** Aktuelle Preise für getrackte Apps von CheapShark API abrufen.

**CLI-Aufruf:**
```bash
python main.py
# Option 6: Preise manuell aktualisieren
```

**Programmischer Aufruf:**
```python
# Einzelne Apps
result = tracker.track_app_prices(["413150", "105600"])

# Alle ausstehenden Apps (optimiert)
result = tracker.process_all_pending_apps_optimized()

# Mit Zeitfilter
result = tracker.process_all_pending_apps_optimized(hours_threshold=24)
```

**Parameter:**

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `app_ids` | List[String] | ✅ | Liste der Steam App IDs |
| `hours_threshold` | Integer | ❌ | Mindestabstand zwischen Updates |
| `force_update` | Boolean | ❌ | Update erzwingen |

**Response Schema:**
```python
{
    "processed": int,
    "successful": int,
    "failed": int,
    "errors": [str],
    "duration": float,
    "total_deals_found": int,
    "apps_updated": [
        {
            "app_id": str,
            "name": str,
            "best_price": float,
            "best_store": str,
            "discount_percent": int,
            "deals_count": int
        }
    ]
}
```

### Charts Tracking System

#### Steam Charts aktivieren

**Zweck:** Automatisches Tracking von Steam Charts für trending Spiele.

**CLI-Aufruf:**
```bash
python main.py
# Option 14: Charts vollständig aktualisieren (BATCH)
```

**Programmischer Aufruf:**
```python
from steam_charts_manager import SteamChartsManager

charts_manager = SteamChartsManager()
result = charts_manager.update_all_charts()
```

**Verfügbare Chart-Typen:**
- `most_played` - Meist gespielte Spiele
- `top_releases` - Top Neuveröffentlichungen  
- `upcoming` - Kommende Veröffentlichungen
- `specials` - Aktuelle Angebote

**Response Schema:**
```python
{
    "total_processed": int,
    "successful_updates": int,
    "failed_updates": int,
    "duration": float,
    "charts_summary": {
        "most_played": int,
        "top_releases": int,
        "upcoming": int,
        "specials": int
    }
}
```

#### Charts-Statistiken abrufen

**Programmischer Aufruf:**
```python
stats = charts_manager.get_charts_statistics()
```

**Response Schema:**
```python
{
    "total_games_tracked": int,
    "games_by_chart_type": {
        "most_played": int,
        "top_releases": int,
        "upcoming": int,
        "specials": int
    },
    "trending_games": [
        {
            "name": str,
            "chart_type": str,
            "current_rank": int,
            "best_rank": int,
            "rank_trend": str
        }
    ]
}
```

### Elasticsearch Analytics

#### Daten zu Elasticsearch exportieren

**Zweck:** Alle Steam Price Tracker Daten für erweiterte Analytics exportieren.

**CLI-Aufruf:**
```bash
python main.py
# Option 19: ES Daten exportieren
```

**Programmischer Aufruf:**
```python
from elasticsearch_manager import ElasticsearchManager

es_manager = ElasticsearchManager()
result = es_manager.export_all_data()
```

**Verfügbare Indizes:**
- `steam-price-snapshots` - Historische Preisdaten
- `steam-tracked-apps` - Getrackte Apps-Informationen
- `steam-charts-tracking` - Charts-Tracking-Daten
- `steam-name-history` - Namen-Update-Historie

**Response Schema:**
```python
{
    "indices_created": int,
    "documents_exported": int,
    "export_duration": float,
    "indices_summary": {
        "steam-price-snapshots": int,
        "steam-tracked-apps": int,
        "steam-charts-tracking": int,
        "steam-name-history": int
    }
}
```

---

## 📚 Vollständige Klassen-Referenz

### DatabaseManager

**Datei:** `database_manager.py`  
**Zweck:** Zentrale SQLite-Datenbank-Verwaltung für alle Steam Price Tracker Operationen.

**Konstruktor:**
```python
DatabaseManager(db_path: str = "steam_price_tracker.db")
```

**Kern-Methoden:**

| Methode | Beschreibung | Parameter | Rückgabe |
|---------|--------------|-----------|----------|
| `get_connection()` | Neue DB-Verbindung erstellen | - | `sqlite3.Connection` |
| `add_tracked_app()` | App zum Tracking hinzufügen | `steam_app_id`, `name`, `target_price` | `bool` |
| `get_tracked_apps()` | Alle getrackte Apps abrufen | `active_only=True` | `List[Dict]` |
| `save_price_snapshot()` | Preis-Snapshot speichern | `steam_app_id`, `price_data` | `bool` |
| `get_price_history()` | Preisverlauf abrufen | `steam_app_id`, `days=30` | `List[Dict]` |
| `cleanup_old_prices()` | Alte Preisdaten bereinigen | `days=90` | `int` |
| `get_database_stats()` | Datenbank-Statistiken | - | `Dict` |
| `backup_database()` | DB-Backup erstellen | `backup_path` | `bool` |
| `vacuum_database()` | Datenbank optimieren | - | `bool` |

**Charts-spezifische Methoden:**
```python
init_charts_tables()                    # Charts-Tabellen initialisieren
add_chart_game()                        # Charts-Spiel hinzufügen
get_active_chart_games()                # Aktive Charts-Spiele abrufen
cleanup_old_chart_games()               # Alte Charts-Daten bereinigen
get_charts_statistics()                 # Charts-Statistiken
```

**Verwendungsbeispiele:**

```python
# Basis-Operationen
db = DatabaseManager()

# App hinzufügen
success = db.add_tracked_app("413150", "Stardew Valley", 10.00)

# Preisverlauf abrufen
history = db.get_price_history("413150", days=30)

# Datenbank-Statistiken
stats = db.get_database_stats()
print(f"Apps getrackt: {stats['total_apps']}")
print(f"Preis-Snapshots: {stats['total_snapshots']}")

# Wartung
cleaned = db.cleanup_old_prices(days=60)
db.vacuum_database()
```

### SteamPriceTracker

**Datei:** `price_tracker.py`  
**Zweck:** Hauptklasse für Preis-Tracking, Scheduler-Management und CheapShark-Integration.

**Konstruktor:**
```python
SteamPriceTracker(db_manager=None, api_key=None, enable_charts=True)
```

**Hauptfunktionalitäten:**

| Methode | Beschreibung | Parameter | Rückgabe |
|---------|--------------|-----------|----------|
| `add_or_update_app()` | App zum Tracking hinzufügen/aktualisieren | `steam_app_id`, `name`, `target_price` | `bool` |
| `track_app_prices()` | Preise für Apps aktualisieren | `app_ids: List[str]` | `Dict` |
| `get_best_deals()` | Beste aktuelle Deals finden | `min_discount_percent`, `limit` | `List[Dict]` |
| `get_price_history()` | Detaillierter Preisverlauf | `steam_app_id`, `days_back` | `List[Dict]` |
| `print_price_summary()` | Preis-Zusammenfassung anzeigen | `steam_app_id` | `None` |
| `export_to_csv()` | CSV-Export mit Historie | `filename`, `include_history` | `str` |

**Batch-Processing:**
```python
process_all_pending_apps_optimized()   # Optimiertes Batch-Update aller Apps
process_app_batch()                     # Batch-Verarbeitung spezifischer Apps
get_apps_needing_update()              # Apps identifizieren die Updates benötigen
```

**Scheduler-Management:**
```python
start_background_scheduler()           # Background-Tracking starten
stop_background_scheduler()            # Background-Tracking stoppen
get_scheduler_status()                 # Aktueller Scheduler-Status
enable_charts_tracking()               # Charts-Tracking aktivieren
disable_charts_tracking()              # Charts-Tracking deaktivieren
```

**Verwendungsbeispiele:**

```python
# Tracker initialisieren
tracker = SteamPriceTracker(enable_charts=True)

# Apps hinzufügen
tracker.add_or_update_app("413150", "Stardew Valley", target_price=10.00)

# Batch-Update aller Apps
result = tracker.process_all_pending_apps_optimized()
print(f"✅ {result['total_successful']}/{result['total_processed']} Apps aktualisiert")

# Beste Deals finden
deals = tracker.get_best_deals(min_discount_percent=50, limit=10)
for deal in deals:
    print(f"{deal['game_title']}: €{deal['best_price']} (-{deal['discount_percent']}%)")

# Automatisches Tracking starten
tracker.start_background_scheduler(interval_hours=6)
```

### SteamWishlistManager

**Datei:** `steam_wishlist_manager.py`  
**Zweck:** Steam Web API Integration für Wishlist-Management und App-Daten.

**Konstruktor:**
```python
SteamWishlistManager(api_key: str)
```

**Hauptmethoden:**

| Methode | Beschreibung | Parameter | Rückgabe |
|---------|--------------|-----------|----------|
| `validate_api_key()` | API Key validieren | - | `bool` |
| `get_simple_wishlist()` | Wishlist abrufen (vereinfacht) | `steam_id` | `List[Dict]` |
| `get_app_details()` | Detaillierte App-Informationen | `app_id` | `Dict` |
| `get_app_name_only()` | Nur App-Name abrufen | `app_id` | `str` |
| `get_multiple_app_names()` | Mehrere App-Namen batch-weise | `app_ids: List[str]` | `Dict[str, str]` |
| `get_user_info()` | Steam-Benutzerinformationen | `steam_id` | `Dict` |

**Utility-Funktionen:**
```python
get_steam_id_64()                      # Steam ID zu 64-bit konvertieren
load_api_key_from_env()                # API Key aus .env laden
validate_steam_api_key()               # Standalone API Key Validierung
```

**Verwendungsbeispiele:**

```python
# Manager initialisieren
manager = SteamWishlistManager("YOUR_API_KEY")

# API Key validieren
if not manager.validate_api_key():
    raise ValueError("Steam API Key ungültig")

# Wishlist importieren
wishlist = manager.get_simple_wishlist("76561198000000000")
print(f"Gefunden: {len(wishlist)} Spiele")

# Batch-Namen abrufen
app_ids = ["413150", "105600", "292030"]
names = manager.get_multiple_app_names(app_ids)
for app_id, name in names.items():
    print(f"{app_id}: {name}")

# Benutzer-Info
user_info = manager.get_user_info("76561198000000000")
print(f"Spieler: {user_info.get('personaname', 'Unbekannt')}")
```

### SteamChartsManager

**Datei:** `steam_charts_manager.py`  
**Zweck:** Automatisches Steam Charts-Tracking mit Ranking-Trends.

**Konstruktor:**
```python
SteamChartsManager(db_manager=None)
```

**Hauptmethoden:**

| Methode | Beschreibung | Parameter | Rückgabe |
|---------|--------------|-----------|----------|
| `update_all_charts()` | Alle Charts aktualisieren | `chart_types=None` | `Dict` |
| `get_charts_statistics()` | Charts-Statistiken abrufen | - | `Dict` |
| `get_trending_games()` | Trending Spiele identifizieren | `chart_type`, `limit=10` | `List[Dict]` |
| `get_chart_history()` | Charts-Verlauf für App | `app_id`, `days=30` | `List[Dict]` |
| `cleanup_old_charts()` | Alte Charts-Daten bereinigen | `days=90` | `int` |

**Charts-Typen:**
- `most_played` - Steam Charts Most Played
- `top_releases` - Top neue Veröffentlichungen
- `upcoming` - Kommende Releases
- `specials` - Aktuelle Steam-Angebote

**Verwendungsbeispiele:**

```python
# Charts Manager initialisieren
charts = SteamChartsManager()

# Alle Charts aktualisieren
result = charts.update_all_charts()
print(f"Charts aktualisiert: {result['total_processed']}")

# Trending Spiele finden
trending = charts.get_trending_games("most_played", limit=5)
for game in trending:
    print(f"{game['name']}: Position #{game['current_rank']}")

# Charts-Statistiken
stats = charts.get_charts_statistics()
print(f"Total getrackte Charts-Spiele: {stats['total_games_tracked']}")
```

### ElasticsearchManager

**Datei:** `elasticsearch_manager.py`  
**Zweck:** Erweiterte Analytics durch Elasticsearch-Integration.

**Konstruktor:**
```python
ElasticsearchManager(host="localhost", port=9200)
```

**Hauptmethoden:**

| Methode | Beschreibung | Parameter | Rückgabe |
|---------|--------------|-----------|----------|
| `setup_elasticsearch()` | Elasticsearch-Umgebung einrichten | `force_recreate=False` | `bool` |
| `export_all_data()` | Alle Daten exportieren | `indices=None` | `Dict` |
| `create_kibana_dashboards()` | Kibana-Dashboards erstellen | `dashboard_types=None` | `bool` |
| `get_analytics_summary()` | Analytics-Übersicht | `days=30` | `Dict` |
| `search_data()` | Erweiterte Datensuche | `index`, `query` | `List[Dict]` |

**Verfügbare Indizes:**
- `steam-price-snapshots` - Historische Preisdaten mit Store-Details
- `steam-tracked-apps` - Getrackte Apps mit Metadaten
- `steam-charts-tracking` - Charts-Ranking-Historie
- `steam-name-history` - App-Namen-Update-Historie

**Verwendungsbeispiele:**

```python
# Elasticsearch Manager initialisieren
es = ElasticsearchManager()

# Setup und Export
es.setup_elasticsearch()
result = es.export_all_data()
print(f"Exportiert: {result['documents_exported']} Dokumente")

# Kibana-Dashboards erstellen
es.create_kibana_dashboards()

# Analytics-Abfragen
summary = es.get_analytics_summary(days=7)
print(f"Beste Deals letzte 7 Tage: {summary['top_deals']}")

# Erweiterte Suche
high_discounts = es.search_data(
    "steam-price-snapshots",
    {"range": {"max_discount": {"gte": 75}}}
)
print(f"Spiele mit >75% Rabatt: {len(high_discounts)}")
```

---

## 💻 Code-Beispiele und Tutorials

### Tutorial 1: Vollständiges Wishlist-Setup

**Ziel:** Komplettes Setup von Steam Wishlist-Import bis automatischem Tracking

**Geschätzte Dauer:** 15 Minuten  
**Schwierigkeitsgrad:** Anfänger  
**Vorkenntnisse:** Python-Grundlagen

**Was werden wir bauen:** Ein vollständiges Preis-Tracking-System basierend auf einer Steam Wishlist

```python
"""
Tutorial 1: Vollständiges Wishlist-Tracking Setup
Importiert Wishlist und startet automatisches Preis-Tracking
"""

from steam_wishlist_manager import SteamWishlistManager, load_api_key_from_env
from price_tracker import SteamPriceTracker
from database_manager import DatabaseManager
import time

def setup_wishlist_tracking(steam_id: str):
    """
    Komplettes Wishlist-Setup mit automatischem Tracking
    
    Args:
        steam_id: Steam User ID (64-bit Format)
    
    Returns:
        bool: True wenn Setup erfolgreich
    """
    
    print("🚀 Starte Wishlist-Tracking Setup...")
    
    # 1. Komponenten initialisieren
    api_key = load_api_key_from_env()
    if not api_key:
        print("❌ Steam API Key nicht gefunden. Prüfen Sie Ihre .env Datei")
        return False
    
    steam_manager = SteamWishlistManager(api_key)
    
    # 2. API Key validieren
    print("🔑 Validiere Steam API Key...")
    if not steam_manager.validate_api_key():
        print("❌ Steam API Key ungültig")
        return False
    print("✅ Steam API Key gültig")
    
    # 3. Price Tracker initialisieren
    tracker = SteamPriceTracker(enable_charts=True)
    
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
        
        # Intelligenter Zielpreis: 50% des aktuellen Preises
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
            print(f"➕ {name[:50]}... (Zielpreis: €{target_price:.2f})")
        
        # Rate Limiting respektieren
        time.sleep(0.5)
    
    print(f"✅ {added_count}/{len(wishlist)} Spiele zum Tracking hinzugefügt")
    
    # 6. Erstes Preis-Update durchführen
    print("🔄 Starte erstes Preis-Update...")
    update_result = tracker.process_all_pending_apps_optimized(hours_threshold=0)
    
    print(f"✅ Setup abgeschlossen!")
    print(f"   📊 {update_result['total_successful']} Apps erfolgreich aktualisiert")
    print(f"   ⏱️ Dauer: {update_result['total_duration']:.1f}s")
    print(f"   💰 {update_result['total_deals_found']} Deals gefunden")
    
    # 7. Automatisches Tracking starten
    tracker.start_background_scheduler(interval_hours=6)
    print("🤖 Automatisches Tracking gestartet (alle 6 Stunden)")
    
    return True

# Verwendung
if __name__ == "__main__":
    # Ihre Steam ID hier eintragen (64-bit Format)
    steam_id = "76561198000000000"
    
    # Setup ausführen
    success = setup_wishlist_tracking(steam_id)
    
    if success:
        print("\n🎉 Wishlist-Tracking erfolgreich eingerichtet!")
        print("   Das System überwacht nun automatisch Ihre Spiele-Preise.")
    else:
        print("\n❌ Setup fehlgeschlagen. Prüfen Sie die Fehlermeldungen oben.")
```

**Erwartetes Ergebnis:**
- ✅ Alle Wishlist-Spiele werden automatisch getrackt
- ✅ Intelligente Zielpreise werden gesetzt (50% des aktuellen Preises)
- ✅ Automatisches Tracking läuft alle 6 Stunden
- ✅ Erste Preisdaten sind sofort verfügbar

### Tutorial 2: Charts-Tracking System

**Ziel:** Steam Charts-Integration für Trending-Spiele einrichten

**Geschätzte Dauer:** 10 Minuten  
**Schwierigkeitsgrad:** Mittel  
**Vorkenntnisse:** Tutorial 1 abgeschlossen

```python
"""
Tutorial 2: Steam Charts-Tracking System
Überwacht Steam Charts und identifiziert trending Spiele
"""

from steam_charts_manager import SteamChartsManager
from price_tracker import SteamPriceTracker
import json

def setup_charts_tracking():
    """
    Charts-Tracking-System einrichten und konfigurieren
    """
    
    print("📈 Initialisiere Steam Charts-Tracking...")
    
    # 1. Charts Manager initialisieren
    charts = SteamChartsManager()
    tracker = SteamPriceTracker(enable_charts=True)
    
    # 2. Alle verfügbaren Charts aktualisieren
    print("🔄 Aktualisiere alle Steam Charts...")
    result = charts.update_all_charts()
    
    print(f"✅ Charts-Update abgeschlossen:")
    print(f"   📊 {result['total_processed']} Charts-Einträge verarbeitet")
    print(f"   ✅ {result['successful_updates']} erfolgreich")
    print(f"   ❌ {result['failed_updates']} fehlgeschlagen")
    
    # 3. Trending Spiele identifizieren
    print("\n🔥 Identifiziere Trending Spiele...")
    
    trending_categories = {
        "most_played": "Meist gespielt",
        "top_releases": "Top Neuveröffentlichungen", 
        "upcoming": "Kommende Releases",
        "specials": "Aktuelle Angebote"
    }
    
    all_trending = {}
    
    for chart_type, description in trending_categories.items():
        trending = charts.get_trending_games(chart_type, limit=5)
        all_trending[chart_type] = trending
        
        print(f"\n📊 {description}:")
        for i, game in enumerate(trending, 1):
            rank_info = f"#{game['current_rank']}"
            if game.get('rank_trend'):
                trend_emoji = "📈" if game['rank_trend'] == "rising" else "📉"
                rank_info += f" {trend_emoji}"
            
            print(f"   {i}. {game['name'][:40]}... - {rank_info}")
    
    # 4. Charts-Spiele automatisch zum Tracking hinzufügen
    print("\n➕ Füge trending Spiele zum Preis-Tracking hinzu...")
    
    added_games = 0
    for chart_type, games in all_trending.items():
        for game in games[:3]:  # Top 3 aus jeder Kategorie
            # Nur hinzufügen wenn noch nicht getrackt
            success = tracker.add_or_update_app(
                steam_app_id=game['steam_app_id'],
                name=game['name'],
                target_price=None,  # Kein spezifischer Zielpreis
                from_charts=True
            )
            
            if success:
                added_games += 1
                print(f"   ✅ {game['name'][:40]}... hinzugefügt")
    
    print(f"\n📊 {added_games} Charts-Spiele zum Tracking hinzugefügt")
    
    # 5. Charts-Statistiken anzeigen
    stats = charts.get_charts_statistics()
    
    print(f"\n📈 Charts-Tracking Übersicht:")
    print(f"   🎯 Gesamt getrackte Charts-Spiele: {stats['total_games_tracked']}")
    
    for chart_type, count in stats['games_by_chart_type'].items():
        print(f"   📊 {trending_categories.get(chart_type, chart_type)}: {count}")
    
    # 6. Charts-Automation aktivieren
    tracker.enable_charts_tracking()
    print("\n🤖 Charts-Automation aktiviert")
    print("   Das System überwacht nun automatisch Steam Charts-Änderungen")
    
    return True

# Deal-Analyzer für Charts-Spiele
def analyze_charts_deals():
    """
    Analysiert Deals für Charts-Spiele
    """
    
    print("💰 Analysiere Deals für Charts-Spiele...")
    
    tracker = SteamPriceTracker()
    charts = SteamChartsManager()
    
    # Beste Deals für Charts-Spiele finden
    deals = tracker.get_best_deals(
        min_discount_percent=25,
        charts_games_only=True,
        limit=10
    )
    
    print(f"\n🎯 Top Deals für Charts-Spiele:")
    
    for i, deal in enumerate(deals, 1):
        chart_info = charts.get_chart_info(deal['steam_app_id'])
        chart_type = chart_info.get('chart_type', 'Unbekannt')
        rank = chart_info.get('current_rank', '?')
        
        print(f"{i}. {deal['game_title'][:40]}...")
        print(f"   💰 €{deal['best_price']:.2f} (-{deal['discount_percent']}%)")
        print(f"   📊 {chart_type} #{rank}")
        print(f"   🏪 {deal['best_store']}")
        print()
    
    return deals

# Verwendung
if __name__ == "__main__":
    # Charts-System einrichten
    setup_charts_tracking()
    
    # Charts-Deals analysieren
    deals = analyze_charts_deals()
    
    print("🎉 Charts-Tracking System erfolgreich eingerichtet!")
```

### Tutorial 3: Elasticsearch Analytics

**Ziel:** Erweiterte Analytics mit Elasticsearch und Kibana einrichten

**Geschätzte Dauer:** 20 Minuten  
**Schwierigkeitsgrad:** Fortgeschritten  
**Vorkenntnisse:** Docker-Grundlagen

```python
"""
Tutorial 3: Elasticsearch Analytics Setup
Erweiterte Datenanalyse mit Elasticsearch und Kibana
"""

from elasticsearch_manager import ElasticsearchManager
from price_tracker import SteamPriceTracker
import json
import webbrowser

def setup_elasticsearch_analytics():
    """
    Komplettes Elasticsearch-Setup für erweiterte Analytics
    """
    
    print("🔍 Elasticsearch Analytics Setup gestartet...")
    
    # 1. Elasticsearch Manager initialisieren
    es = ElasticsearchManager()
    
    # 2. Elasticsearch-Umgebung einrichten
    print("⚙️ Richte Elasticsearch-Umgebung ein...")
    
    setup_success = es.setup_elasticsearch(force_recreate=False)
    if not setup_success:
        print("❌ Elasticsearch-Setup fehlgeschlagen")
        print("   Stellen Sie sicher, dass Docker läuft")
        return False
    
    print("✅ Elasticsearch erfolgreich eingerichtet")
    
    # 3. Alle Daten exportieren
    print("📤 Exportiere Steam Price Tracker Daten...")
    
    export_result = es.export_all_data()
    
    print(f"✅ Datenexport abgeschlossen:")
    print(f"   📊 {export_result['indices_created']} Indizes erstellt")
    print(f"   📄 {export_result['documents_exported']} Dokumente exportiert")
    
    # 4. Index-Übersicht anzeigen
    print(f"\n📋 Erstellte Elasticsearch-Indizes:")
    for index, count in export_result['indices_summary'].items():
        print(f"   📊 {index}: {count:,} Dokumente")
    
    # 5. Kibana-Dashboards erstellen
    print("\n📊 Erstelle Kibana-Dashboards...")
    
    dashboard_success = es.create_kibana_dashboards([
        "price_analytics",
        "app_management", 
        "charts_analytics",
        "deal_discovery"
    ])
    
    if dashboard_success:
        print("✅ Kibana-Dashboards erfolgreich erstellt")
    else:
        print("⚠️ Einige Dashboards konnten nicht erstellt werden")
    
    # 6. Analytics-Übersicht generieren
    print("\n📈 Generiere Analytics-Übersicht...")
    
    analytics = es.get_analytics_summary(days=30)
    
    print(f"\n📊 Analytics-Zusammenfassung (letzte 30 Tage):")
    print(f"   🎯 Getrackte Apps: {analytics['total_apps']:,}")
    print(f"   📄 Preis-Snapshots: {analytics['total_snapshots']:,}")
    print(f"   💰 Durchschnittlicher Rabatt: {analytics['avg_discount']:.1f}%")
    print(f"   🏪 Aktive Stores: {analytics['active_stores']}")
    
    # Top Deals anzeigen
    if analytics.get('top_deals'):
        print(f"\n🔥 Top Deals (letzte 30 Tage):")
        for i, deal in enumerate(analytics['top_deals'][:5], 1):
            print(f"   {i}. {deal['game_title'][:40]}...")
            print(f"      💰 €{deal['price']:.2f} (-{deal['discount']}%)")
    
    # 7. Beispiel-Queries demonstrieren
    print("\n🔍 Beispiel-Analytics-Queries:")
    
    # Query 1: Hohe Rabatte finden
    high_discounts = es.search_data(
        "steam-price-snapshots",
        {
            "query": {
                "range": {
                    "max_discount": {"gte": 75}
                }
            },
            "size": 5
        }
    )
    
    print(f"\n📊 Spiele mit >75% Rabatt: {len(high_discounts)}")
    for deal in high_discounts[:3]:
        print(f"   • {deal['game_title']}: -{deal['max_discount']}%")
    
    # Query 2: Preishistorie-Trends
    trending_prices = es.search_data(
        "steam-price-snapshots",
        {
            "query": {
                "bool": {
                    "must": [
                        {"range": {"timestamp": {"gte": "now-7d"}}},
                        {"range": {"max_discount": {"gte": 30}}}
                    ]
                }
            },
            "size": 3
        }
    )
    
    print(f"\n📈 Kürzlich rabattierte Spiele: {len(trending_prices)}")
    for game in trending_prices:
        print(f"   • {game['game_title']}: -{game['max_discount']}%")
    
    # 8. Kibana-Dashboard öffnen
    print("\n🌐 Öffne Kibana-Dashboard...")
    
    kibana_url = "http://localhost:5601"
    try:
        webbrowser.open(kibana_url)
        print(f"✅ Kibana geöffnet: {kibana_url}")
    except:
        print(f"⚠️ Kibana manuell öffnen: {kibana_url}")
    
    print("\n🎉 Elasticsearch Analytics Setup abgeschlossen!")
    print("\nVerfügbare Dashboards:")
    print("   📊 Price Analytics - Preisentwicklungen und Trends")
    print("   📱 App Management - Getrackte Apps-Übersicht")
    print("   📈 Charts Analytics - Steam Charts-Auswertungen")
    print("   💰 Deal Discovery - Deal-Finder und Alerts")
    
    return True

def create_custom_analytics_dashboard():
    """
    Erstellt ein benutzerdefiniertes Analytics-Dashboard
    """
    
    print("🎨 Erstelle benutzerdefiniertes Analytics-Dashboard...")
    
    es = ElasticsearchManager()
    
    # Custom Dashboard-Konfiguration
    custom_dashboard = {
        "title": "Steam Price Tracker - Custom Analytics",
        "panels": [
            {
                "title": "Preisentwicklung Top 10 Spiele",
                "type": "line_chart",
                "query": "top_games_price_trend"
            },
            {
                "title": "Store-Vergleich nach Rabatten",
                "type": "bar_chart", 
                "query": "store_discount_comparison"
            },
            {
                "title": "Wishlist vs Charts Spiele",
                "type": "pie_chart",
                "query": "source_distribution"
            }
        ]
    }
    
    # Dashboard erstellen
    success = es.create_custom_dashboard(custom_dashboard)
    
    if success:
        print("✅ Custom Dashboard erfolgreich erstellt")
        return True
    else:
        print("❌ Custom Dashboard konnte nicht erstellt werden")
        return False

# Verwendung
if __name__ == "__main__":
    # Haupt-Setup ausführen
    success = setup_elasticsearch_analytics()
    
    if success:
        # Custom Dashboard erstellen
        create_custom_analytics_dashboard()
        
        print("\n🚀 Elasticsearch Analytics vollständig eingerichtet!")
        print("   Sie können nun erweiterte Analysen in Kibana durchführen")
    else:
        print("\n❌ Setup fehlgeschlagen. Prüfen Sie Docker und Elasticsearch")
```

**Erwartetes Ergebnis:**
- ✅ Elasticsearch und Kibana laufen in Docker-Containern
- ✅ Alle Steam Price Tracker Daten sind in Elasticsearch indexiert
- ✅ Kibana-Dashboards für verschiedene Analysen verfügbar
- ✅ Erweiterte Queries und Custom-Dashboards funktionsfähig

---

## ⚠️ Fehlerbehandlung

### HTTP-Statuscodes und Bedeutungen

| Status Code | Bedeutung | Ursache | Lösungsschritte |
|-------------|-----------|---------|-----------------|
| `200 OK` | Erfolgreiche Antwort | - | Normal, keine Aktion nötig |
| `401 Unauthorized` | Authentifizierung fehlgeschlagen | Steam API Key fehlt/ungültig | API Key in .env überprüfen |
| `403 Forbidden` | Zugriff verweigert | Rate Limit oder ungültiger Key | 1-2 Sekunden warten, Key prüfen |
| `404 Not Found` | Resource nicht gefunden | Steam App ID existiert nicht | App ID validieren |
| `429 Too Many Requests` | Rate Limit erreicht | Zu viele API-Calls | Exponential backoff implementieren |
| `500 Internal Server Error` | Server-Fehler | API temporär nicht verfügbar | Retry mit backoff |
| `503 Service Unavailable` | Service nicht verfügbar | Wartung oder Überlastung | Später erneut versuchen |

### Error Response Format

**Standard-Fehlerstruktur:**
```json
{
    "error": true,
    "error_code": "STEAM_API_INVALID",
    "message": "Steam API Key is invalid or expired",
    "details": {
        "api_key_length": 32,
        "validation_endpoint": "ISteamUser/GetPlayerSummaries",
        "suggestion": "Generate a new API key at steamcommunity.com/dev/apikey"
    },
    "timestamp": "2025-07-25T10:30:00Z"
}
```

### Custom Error Codes

| Error Code | Beschreibung | Häufige Ursachen | Lösungsansätze |
|------------|--------------|------------------|----------------|
| `STEAM_API_INVALID` | Steam API Key ungültig | Key falsch, abgelaufen | Neuen Key generieren |
| `WISHLIST_PRIVATE` | Wishlist nicht öffentlich | Steam-Profil privat | Profil öffentlich machen |
| `CHEAPSHARK_RATE_LIMIT` | CheapShark Rate Limit | Zu schnelle Requests | Wartezeit zwischen Requests |
| `DATABASE_CONNECTION` | Datenbank-Verbindungsfehler | DB gesperrt, beschädigt | DB-Pfad prüfen, Backup einspielen |
| `CHARTS_DISABLED` | Charts-Feature deaktiviert | Feature nicht aktiviert | Charts in Config aktivieren |
| `ELASTICSEARCH_UNAVAILABLE` | Elasticsearch nicht erreichbar | Service nicht gestartet | Docker-Container prüfen |

### Debugging-Strategien

**Logging aktivieren:**
```python
import logging

# Debug-Level für alle Steam Price Tracker Module
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('steam_tracker_debug.log'),
        logging.StreamHandler()
    ]
)

# Spezifische Module debuggen
steam_logger = logging.getLogger('steam_wishlist_manager')
steam_logger.setLevel(logging.DEBUG)
```

**API-Requests debuggen:**
```python
from steam_wishlist_manager import SteamWishlistManager

# Debug-Modus aktivieren
manager = SteamWishlistManager(api_key, debug=True)

# Detaillierte Request-Informationen
manager.set_debug_mode(True)
response = manager.get_simple_wishlist(steam_id)
```

**Datenbank-Debugging:**
```python
from database_manager import DatabaseManager

db = DatabaseManager()

# Verbindung testen
try:
    conn = db.get_connection()
    print("✅ Datenbank-Verbindung erfolgreich")
    conn.close()
except Exception as e:
    print(f"❌ DB-Verbindungsfehler: {e}")

# Integritäts-Check
integrity_result = db.check_database_integrity()
if not integrity_result['valid']:
    print("⚠️ Datenbank-Probleme gefunden:")
    for issue in integrity_result['issues']:
        print(f"   - {issue}")
```

### Retry-Strategien

**Exponential Backoff für API-Calls:**
```python
import time
import random

def api_call_with_retry(func, max_retries=3, base_delay=1):
    """
    API-Call mit exponential backoff retry
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            
            # Exponential backoff mit Jitter
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            print(f"⚠️ Attempt {attempt + 1} failed, retrying in {delay:.1f}s...")
            time.sleep(delay)
    
    raise Exception(f"All {max_retries} attempts failed")

# Verwendung
def get_wishlist_safe(steam_id):
    return api_call_with_retry(
        lambda: manager.get_simple_wishlist(steam_id),
        max_retries=3,
        base_delay=2
    )
```

---

## 🔧 Performance-Optimierung

### Batch-Processing Best Practices

**Optimierte App-Updates:**
```python
from price_tracker import SteamPriceTracker

tracker = SteamPriceTracker()

# Optimiertes Batch-Update für große App-Sammlungen
result = tracker.process_all_pending_apps_optimized(
    batch_size=100,           # Apps pro Batch
    hours_threshold=24,       # Mindestabstand zwischen Updates
    parallel_workers=3,       # Parallele Worker (experimentell)
    prioritize_discounts=True # Zuerst Apps mit Rabatten
)

print(f"Batch-Update: {result['total_successful']}/{result['total_processed']}")
print(f"Durchschnittliche Zeit pro App: {result['avg_time_per_app']:.2f}s")
```

**Memory-effiziente Verarbeitung:**
```python
def process_large_wishlist_memory_efficient(steam_id, batch_size=50):
    """
    Memory-effiziente Verarbeitung großer Wishlists
    """
    
    # Generator für lazy loading
    def wishlist_generator():
        manager = SteamWishlistManager(api_key)
        wishlist = manager.get_simple_wishlist(steam_id)
        
        for i in range(0, len(wishlist), batch_size):
            yield wishlist[i:i+batch_size]
    
    # Batch-weise verarbeiten
    total_processed = 0
    for batch in wishlist_generator():
        batch_result = tracker.process_app_batch([app['steam_app_id'] for app in batch])
        total_processed += batch_result['successful']
        
        # Memory cleanup zwischen Batches
        import gc
        gc.collect()
    
    return total_processed
```

### Caching-Strategien

**In-Memory-Caching für häufige Abfragen:**
```python
from functools import lru_cache
import time

class CachedSteamManager:
    def __init__(self, api_key):
        self.manager = SteamWishlistManager(api_key)
    
    @lru_cache(maxsize=1000)
    def get_app_name_cached(self, app_id, ttl_hours=24):
        """
        App-Namen mit TTL-Cache
        """
        cache_key = f"{app_id}_{int(time.time() // (ttl_hours * 3600))}"
        return self.manager.get_app_name_only(app_id)
    
    def clear_cache(self):
        """Cache zurücksetzen"""
        self.get_app_name_cached.cache_clear()
```

**Datenbank-Query-Optimierung:**
```python
class OptimizedDatabaseManager(DatabaseManager):
    
    def get_price_history_optimized(self, steam_app_id, days=30):
        """
        Optimierte Preisverlauf-Abfrage mit Index-Nutzung
        """
        query = """
        SELECT timestamp, best_price, best_store, max_discount
        FROM price_snapshots 
        WHERE steam_app_id = ? 
        AND timestamp >= datetime('now', '-{} days')
        ORDER BY timestamp DESC
        """.format(days)
        
        with self.get_connection() as conn:
            # Index für bessere Performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_app_timestamp ON price_snapshots(steam_app_id, timestamp)")
            return conn.execute(query, (steam_app_id,)).fetchall()
```

### Elasticsearch-Performance

**Bulk-Indexing für große Datenmengen:**
```python
from elasticsearch import helpers

def bulk_index_price_data(es_manager, price_data, chunk_size=1000):
    """
    Bulk-Indexing für bessere Elasticsearch-Performance
    """
    
    def generate_docs():
        for data in price_data:
            yield {
                "_index": "steam-price-snapshots",
                "_source": data
            }
    
    # Bulk-Insert mit optimierten Einstellungen
    success, failed = helpers.bulk(
        es_manager.client,
        generate_docs(),
        chunk_size=chunk_size,
        request_timeout=60,
        max_chunk_bytes=100*1024*1024  # 100MB chunks
    )
    
    return {"successful": success, "failed": len(failed)}
```

---

## 📊 Support und Wartung

### Health Checks

**System-Gesundheits-Check:**
```python
def system_health_check():
    """
    Umfassender System-Gesundheitscheck
    """
    
    health_status = {
        "overall": "healthy",
        "components": {},
        "issues": [],
        "recommendations": []
    }
    
    # 1. Datenbank-Check
    try:
        db = DatabaseManager()
        stats = db.get_database_stats()
        health_status["components"]["database"] = {
            "status": "healthy",
            "apps_tracked": stats.get("total_apps", 0),
            "snapshots": stats.get("total_snapshots", 0)
        }
    except Exception as e:
        health_status["components"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["issues"].append("Datenbank nicht erreichbar")
    
    # 2. Steam API Check
    try:
        api_key = load_api_key_from_env()
        manager = SteamWishlistManager(api_key)
        if manager.validate_api_key():
            health_status["components"]["steam_api"] = {"status": "healthy"}
        else:
            health_status["components"]["steam_api"] = {"status": "unhealthy", "error": "Invalid API key"}
            health_status["issues"].append("Steam API Key ungültig")
    except Exception as e:
        health_status["components"]["steam_api"] = {"status": "unhealthy", "error": str(e)}
    
    # 3. Charts-Check (optional)
    try:
        charts = SteamChartsManager()
        charts_stats = charts.get_charts_statistics()
        health_status["components"]["charts"] = {
            "status": "healthy",
            "games_tracked": charts_stats.get("total_games_tracked", 0)
        }
    except Exception as e:
        health_status["components"]["charts"] = {"status": "disabled", "note": "Charts feature not enabled"}
    
    # 4. Elasticsearch-Check (optional)
    try:
        es = ElasticsearchManager()
        if es.client.ping():
            health_status["components"]["elasticsearch"] = {"status": "healthy"}
        else:
            health_status["components"]["elasticsearch"] = {"status": "unreachable"}
    except:
        health_status["components"]["elasticsearch"] = {"status": "disabled"}
    
    # Overall status bestimmen
    unhealthy_components = [comp for comp, data in health_status["components"].items() 
                           if data.get("status") == "unhealthy"]
    
    if unhealthy_components:
        health_status["overall"] = "unhealthy"
        health_status["recommendations"].append("Kritische Komponenten reparieren")
    elif len(health_status["issues"]) > 0:
        health_status["overall"] = "degraded"
    
    return health_status
```

### Monitoring und Metriken

**Prometheus-Metriken (optional):**
```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Metriken definieren
api_requests_total = Counter('steam_tracker_api_requests_total', 'Total API requests', ['endpoint'])
request_duration = Histogram('steam_tracker_request_duration_seconds', 'Request duration')
tracked_apps_gauge = Gauge('steam_tracker_tracked_apps', 'Number of tracked apps')

class MetricsTracker:
    
    @staticmethod
    def track_api_request(endpoint):
        api_requests_total.labels(endpoint=endpoint).inc()
    
    @staticmethod
    def track_request_duration(duration):
        request_duration.observe(duration)
    
    @staticmethod
    def update_tracked_apps_count(count):
        tracked_apps_gauge.set(count)
    
    @classmethod
    def start_metrics_server(cls, port=8000):
        """Startet Prometheus-Metriken-Server"""
        start_http_server(port)
        print(f"📊 Metrics server gestartet auf Port {port}")
```

### Backup und Recovery

**Automatische Backups:**
```python
import shutil
import datetime
import os

class BackupManager:
    
    def __init__(self, backup_dir="backups"):
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
    
    def create_backup(self, include_config=True):
        """
        Vollständiges System-Backup erstellen
        """
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"steam_tracker_backup_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        os.makedirs(backup_path, exist_ok=True)
        
        backup_info = {
            "timestamp": timestamp,
            "files": [],
            "size_mb": 0
        }
        
        # Datenbank sichern
        if os.path.exists("steam_price_tracker.db"):
            shutil.copy2("steam_price_tracker.db", os.path.join(backup_path, "database.db"))
            backup_info["files"].append("database.db")
        
        # Konfiguration sichern
        if include_config:
            config_files = [".env", "config.json"]
            for config_file in config_files:
                if os.path.exists(config_file):
                    shutil.copy2(config_file, backup_path)
                    backup_info["files"].append(config_file)
        
        # Backup-Größe berechnen
        total_size = sum(os.path.getsize(os.path.join(backup_path, f)) 
                        for f in backup_info["files"])
        backup_info["size_mb"] = round(total_size / 1024 / 1024, 2)
        
        # Backup-Info speichern
        import json
        with open(os.path.join(backup_path, "backup_info.json"), 'w') as f:
            json.dump(backup_info, f, indent=2)
        
        return backup_path, backup_info
    
    def restore_backup(self, backup_path):
        """
        Backup wiederherstellen
        """
        
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup nicht gefunden: {backup_path}")
        
        # Aktuelles System sichern
        emergency_backup, _ = self.create_backup(include_config=False)
        print(f"Notfall-Backup erstellt: {emergency_backup}")
        
        # Backup wiederherstellen
        database_backup = os.path.join(backup_path, "database.db")
        if os.path.exists(database_backup):
            shutil.copy2(database_backup, "steam_price_tracker.db")
            print("✅ Datenbank wiederhergestellt")
        
        config_files = [".env", "config.json"]
        for config_file in config_files:
            config_backup = os.path.join(backup_path, config_file)
            if os.path.exists(config_backup):
                shutil.copy2(config_backup, config_file)
                print(f"✅ {config_file} wiederhergestellt")
        
        return True
```

---

## 🆘 Support und Community

### GitHub Issues und Bug Reports

**Bug Report Template:**
```markdown
## 🐛 Bug Report

**Steam Price Tracker Version:** v1.2-dev
**Python Version:** 3.9.x
**Operating System:** Windows 10 / macOS / Linux

### Beschreibung
Kurze Beschreibung des Problems...

### Reproduktionsschritte
1. Schritt 1
2. Schritt 2
3. Problem tritt auf

### Erwartetes Verhalten
Was sollte passieren...

### Aktuelles Verhalten
Was passiert stattdessen...

### Logs/Screenshots
```python
# Fehler-Log hier einfügen
```

### Zusätzliche Informationen
- Steam API Key funktioniert: ✅/❌
- Erste Installation: ✅/❌
- Charts aktiviert: ✅/❌
- Elasticsearch verwendet: ✅/❌
```

### Feature Requests

**Feature Request Template:**
```markdown
## 💡 Feature Request

### Problemstellung
Welches Problem löst dieses Feature?

### Lösungsvorschlag
Beschreibung der gewünschten Funktionalität...

### Alternativen
Andere Lösungsansätze die Sie in Betracht gezogen haben...

### Zusätzlicher Kontext
Screenshots, Mockups, Links zu ähnlichen Features...
```

### Community Guidelines

**Beitrag zum Projekt:**

1. **Code-Beiträge:**
   ```bash
   # Repository forken
   git fork https://github.com/username/steam-price-tracker
   
   # Feature-Branch erstellen
   git checkout -b feature/awesome-feature
   
   # Änderungen committen
   git commit -m "Add awesome feature"
   
   # Pull Request erstellen
   git push origin feature/awesome-feature
   ```

2. **Code-Standards:**
   - Python PEP 8 Style Guide befolgen
   - Docstrings für alle Funktionen
   - Type Hints verwenden
   - Unit Tests für neue Features

3. **Dokumentation:**
   - README.md bei API-Änderungen aktualisieren
   - Docstrings in deutscher oder englischer Sprache
   - Code-Beispiele für neue Features

### Support-Kanäle

| Kanal | Zweck | Response Time |
|-------|-------|---------------|
| **GitHub Issues** | Bug Reports, Feature Requests | 1-3 Tage |
| **GitHub Discussions** | Allgemeine Fragen, Ideen | 1-7 Tage |
| **Email Support** | Kritische Probleme | 24-48h |
| **Discord Community** | Real-time Chat, Quick Help | Sofort |

### Roadmap und zukünftige Features

**Version 1.2 (In Entwicklung):**
- ✅ Elasticsearch-Integration

**Version 1.3 (Geplant Q4 2025):**
- Vollständige Charts-Funktionen
- Neues Scheduler System: Nutzung der nativen OS-Scheduler

---

*Diese Dokumentation wurde automatisch generiert basierend auf dem Steam Price Tracker v1.2-dev Codebase. Das Programm ist eine lokale Desktop-Anwendung mit optionaler Elasticsearch-Integration. Letzte Aktualisierung: Juli 2025*