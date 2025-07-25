# 💰 Steam Price Tracker v1.2-dev

**Professionelles System für automatisches Steam-Preis-Tracking mit erweiterten Analytics**

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)
![Version](https://img.shields.io/badge/version-1.2--dev-orange.svg)

## ✨ Highlights

- 🎯 **Direktes CheapShark-Tracking** mit Steam App IDs (kein komplexes Mapping nötig)
- 📊 **Multi-Store Preisvergleich** für 6 major Stores (Steam, GOG, HumbleBundle, etc.)
- 📥 **Steam Wishlist Import** mit vollständiger API-Integration
- 📈 **Steam Charts Tracking** für automatische Trending-Spiele-Überwachung
- 🔍 **Elasticsearch Analytics** mit Kibana-Dashboards für erweiterte Datenanalyse
- ⚡ **Intelligentes Batch-Processing** mit optimierter Performance
- 🗄️ **SQLite-Datenbank** für historische Preisdaten und Trends
- 📄 **CSV/JSON-Export** kompatibel mit Excel, Pandas und Power BI
- 🤖 **Background-Scheduler** für vollautomatisches Tracking
- 🛡️ **Robuste Fehlerbehandlung** mit Rate Limiting und Retry-Logic
- 📦 **Ein-Klick-Setup** mit automatischem Setup-Wizard

## 🚀 5-Minuten Schnellstart

### 1. Installation
```bash
# Repository klonen
git clone <repository-url>
cd steam-price-tracker

# Ein-Klick-Setup (installiert alles automatisch)
python setup.py setup
```

### 2. Steam API Key einrichten
1. **Steam API Key holen:** [steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey)
2. **Domain eingeben:** `localhost` (für lokale Nutzung)
3. **Key in .env eintragen:** Der Setup-Wizard erstellt automatisch die Datei

```env
STEAM_API_KEY=dein_api_key_hier
```

### 3. Erste Nutzung
```bash
# Hauptanwendung starten
python main.py

# Empfohlener Workflow:
# 1. Option 2: Steam Wishlist importieren
# 2. Option 7: Automatisches Tracking starten
# 3. Option 4: Beste Deals anzeigen
```

**Das war's!** 🎉 Ihr Preis-Tracking-System läuft jetzt vollautomatisch.

## 📦 System-Architektur

### Hauptkomponenten

```
steam-price-tracker/
├── 🎯 main.py                      # Interaktive CLI mit 30+ Funktionen
├── 💰 price_tracker.py             # Kern-Engine für CheapShark Integration
├── 🗄️ database_manager.py          # SQLite-Datenbank
├Charts-Support (in Entwicklung)
├── 📥 steam_wishlist_manager.py    # Steam Web API Integration
├── 📈 steam_charts_manager.py      # Steam Charts Tracking System
├Konfigurationsverwaltung
├── 🚀 setup.py                     # Setup-Wizard und System-Tools
├── 📋 requirements.txt             # Python-Dependencies
├Elasticsearch
├── 🔍 elasticsearch_manager.py     # Analytics-Engine für Kibana
├── 📊 elasticsearch_cli.py         # CLI für Elasticsearch-Operationen
├── 🐳 docker-compose.yml           # Elasticsearch/Kibana Container
├── 📋 requirements-elasticsearch.txt # Elasticsearch-Dependencies
└── 🌐 kibana_dashboards/           # Vorkonfigurierte Analytics-Dashboards
```

### Unterstützte Stores & APIs

| Store | Unterstützung | 
|-------|----------------|
| **Steam** | ✅ Native API und via Cheapshark| 
| **GOG** | ✅ via CheapShark | 
| **HumbleStore** | ✅ via CheapShark | 
| **GreenManGaming** | ✅ via CheapShark |
| **Fanatical** | ✅ via CheapShark | 
| **GamesPlanet** | ✅ via CheapShark |

### Datenbank-Schema (v1.2)

**tracked_apps** - Basis-Tracking
```sql
steam_app_id TEXT PRIMARY KEY
name TEXT NOT NULL
added_at TIMESTAMP
last_price_update TIMESTAMP
target_price REAL
active BOOLEAN DEFAULT 1
source TEXT DEFAULT 'manual'  -- 'wishlist', 'charts', 'manual'
```

**price_snapshots** - Multi-Store Preisdaten
```sql
steam_app_id TEXT
game_title TEXT
timestamp TIMESTAMP
best_price REAL, best_store TEXT, max_discount INTEGER
-- 6 Stores: steam_*, greenmangaming_*, gog_*, humble_*, fanatical_*, gamesplanet_*
-- Jeweils: price, original_price, discount_percent, available
```

**steam_charts_tracking** ⭐ NEU in v1.1 (In Entwicklung)
```sql
steam_app_id TEXT
name TEXT
chart_type TEXT  -- 'most_played', 'top_releases', 'upcoming', 'specials'
current_rank INTEGER
best_rank INTEGER
first_seen TIMESTAMP
last_seen TIMESTAMP
popularity_score REAL
```

## 🎯 Erweiterte Nutzung

### CLI-Interface mit 30+ Funktionen

```bash
python main.py
```

**🎮 SPIELE-MANAGEMENT (1-12)**
1. 📱 App manuell hinzufügen
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

**📊 CHARTS & ANALYTICS (13-18) [In Entwicklung]** ⭐ NEU
13. 📈 Steam Charts anzeigen
14. 🚀 Charts vollständig aktualisieren (BATCH)
15. 🎯 Charts-Deals anzeigen
16. 📊 Charts-Statistiken  
17. 🤖 Charts-Automation
18. 📦 Erweiterte BATCH-Optionen

**🛠️ SYSTEM-TOOLS (24-30)**
24. ⚙️ System-Einstellungen
25. 📊 System-Informationen
26. 💾 Backup erstellen
27. 📥 Backup importieren
28. 🔍 Health Check
29. 🧹 Datenbank bereinigen
30. 🔧 Developer Tools

### Programmische API-Nutzung

**Basis-Setup:**
```python
from price_tracker import SteamPriceTracker
from steam_wishlist_manager import SteamWishlistManager
from steam_charts_manager import SteamChartsManager

# System initialisieren
tracker = SteamPriceTracker(enable_charts=True)
steam_manager = SteamWishlistManager("YOUR_API_KEY")
charts_manager = SteamChartsManager()
```

**Wishlist-Import mit intelligentem Zielpreis:**
```python
# Wishlist importieren
steam_id = "76561198000000000"
wishlist = steam_manager.get_simple_wishlist(steam_id)

# Apps mit intelligenten Zielpreisen hinzufügen
for game in wishlist:
    current_price = float(game.get('price', '0') or '0')
    # Zielpreis: 50% des aktuellen Preises
    target_price = current_price * 0.5 if current_price > 0 else None
    
    tracker.add_or_update_app(
        steam_app_id=game['steam_app_id'],
        name=game['name'],
        target_price=target_price
    )

print(f"✅ {len(wishlist)} Spiele zum Tracking hinzugefügt")
```

**Optimiertes Batch-Processing:**
```python
# Alle Apps aktualisieren (intelligent optimiert)
result = tracker.process_all_pending_apps_optimized(
    hours_threshold=24,       # Mindestabstand zwischen Updates
    prioritize_discounts=True # Zuerst Apps mit aktuellen Rabatten
)

print(f"📊 Batch-Update: {result['total_successful']}/{result['total_processed']}")
print(f"💰 Deals gefunden: {result['total_deals_found']}")
print(f"⏱️ Durchschnitt pro App: {result['avg_time_per_app']:.2f}s")
```

**Steam Charts Integration:**
```python
# Alle Charts aktualisieren
charts_result = charts_manager.update_all_charts()
print(f"📈 Charts aktualisiert: {charts_result['total_processed']}")

# Trending Spiele automatisch zum Tracking hinzufügen
trending = charts_manager.get_trending_games("most_played", limit=10)
for game in trending:
    tracker.add_or_update_app(
        steam_app_id=game['steam_app_id'],
        name=game['name'],
        source="charts"
    )
```

**Automatisches Background-Tracking:**
```python
# Background-Scheduler starten
tracker.start_background_scheduler(
    interval_hours=6,         # Alle 6 Stunden
    enable_charts=True,       # Charts-Updates einschließen
    max_apps_per_run=100     # Max. Apps pro Durchlauf
)

# Status abrufen
status = tracker.get_scheduler_status()
print(f"Scheduler läuft: {status['running']}")
print(f"Nächste Ausführung: {status['next_run']}")
```

## 🔍 Elasticsearch Analytics ⭐ NEU

### Schnell-Setup

```bash
# Elasticsearch/Kibana mit Docker starten
python elasticsearch_setup.py setup
python elasticsearch_setup.py start

# Alle Daten exportieren
python elasticsearch_cli.py setup

# Kibana-Dashboard öffnen
http://localhost:5601
```

### Verfügbare Analytics-Dashboards

**📊 Price Analytics Dashboard**
- Preisentwicklung über Zeit (Line Charts)
- Store-Vergleich nach Rabatten (Bar Charts)
- Rabatt-Verteilung (Pie Charts)
- Best Deals Timeline (Area Charts)

**📱 App Management Dashboard**
- Getrackte Apps-Übersicht (Metrics)
- Hinzufügungen über Zeit (Line Charts)
- Source-Verteilung (Wishlist vs Charts) (Pie Chart)
- Update-Frequenz-Heatmap


### Erweiterte Analytics-Queries

```python
from elasticsearch_manager import ElasticsearchManager

es = ElasticsearchManager()

# Beispiel 1: Hohe Rabatte der letzten 7 Tage
high_discounts = es.search_data(
    "steam-price-snapshots",
    {
        "query": {
            "bool": {
                "must": [
                    {"range": {"timestamp": {"gte": "now-7d"}}},
                    {"range": {"max_discount": {"gte": 75}}}
                ]
            }
        }
    }
)

# Beispiel 2: Preistrend-Analyse für spezifisches Spiel
price_trend = es.search_data(
    "steam-price-snapshots", 
    {
        "query": {"match": {"game_title": "Stardew Valley"}},
        "sort": [{"timestamp": {"order": "desc"}}],
        "size": 30
    }
)

# Beispiel 3: Charts-Spiele-Performance
charts_performance = es.search_data(
    "steam-charts-tracking",
    {
        "query": {"match": {"chart_type": "most_played"}},
        "aggs": {
            "avg_rank": {"avg": {"field": "current_rank"}},
            "rank_distribution": {"histogram": {"field": "current_rank", "interval": 10}}
        }
    }
)
```

## ⚙️ Konfiguration & Anpassung

### Environment Variables (.env)

```env
# Steam API
STEAM_API_KEY=dein_steam_api_key_hier
STEAM_RATE_LIMIT=1.0                    # Sekunden zwischen Steam API Calls
STEAM_TIMEOUT=15                        # Timeout für Steam API Requests

# CheapShark API  
CHEAPSHARK_RATE_LIMIT=1.5              # Sekunden zwischen CheapShark Calls
CHEAPSHARK_TIMEOUT=20                   # Timeout für CheapShark Requests

# Features
ENABLE_CHARTS=true                      # Steam Charts Tracking aktivieren
ENABLE_ELASTICSEARCH=false              # Elasticsearch Integration

# Background Scheduler
SCHEDULER_INTERVAL_HOURS=6              # Standard-Intervall für Auto-Updates
SCHEDULER_MAX_APPS_PER_RUN=200         # Max. Apps pro Scheduler-Durchlauf

# Performance
BATCH_SIZE=50                          # Apps pro Batch bei großen Updates
PARALLEL_WORKERS=3                     # Parallele Worker (experimentell)
```

### Erweiterte Konfiguration (config.json)

```json
{
  "database": {
    "path": "steam_price_tracker.db",
    "backup_interval_days": 7,
    "cleanup_old_data_days": 90
  },
  "tracking": {
    "default_target_discount": 50,
    "auto_add_wishlist_games": true,
    "auto_add_trending_charts": true,
    "prioritize_discount_updates": true
  },
  "charts": {
    "enabled_charts": ["most_played", "top_releases", "specials"],
    "update_interval_hours": 12,
    "max_rank_tracking": 100,
    "auto_track_top_games": 20
  },
  "elasticsearch": {
    "host": "localhost",
    "port": 9200,
    "auto_export": false,
    "retention_days": 365
  },
  "notifications": {
    "enable_console_alerts": true,
    "price_drop_threshold": 0.75,
    "new_discount_threshold": 30
  }
}
```

## 🛠️ Wartung & Troubleshooting

### Häufige Probleme und Lösungen

| Problem | Lösung |
|---------|--------|
| **Steam API Key Fehler** | `python setup.py test-api` → Neuen Key auf [Steam Dev Portal](https://steamcommunity.com/dev/apikey) |
| **Leere Wishlist** | Steam-Profil auf "Öffentlich" stellen |
| **CheapShark Rate Limit** | `CHEAPSHARK_RATE_LIMIT=2.0` in .env erhöhen |
| **Datenbank-Fehler** | `python setup.py init-db` für Datenbank-Reset |
| **Elasticsearch nicht erreichbar** | `python elasticsearch_setup.py start` für Docker-Container |
| **Charts nicht verfügbar** | `ENABLE_CHARTS=true` in .env setzen |

### System-Health-Check

```bash
# Umfassender System-Check
python setup.py status

# Einzelne Komponenten testen
python setup.py test-api          # Steam API Key
python setup.py test-db           # Datenbank-Integrität  
python setup.py test-elasticsearch # Elasticsearch-Verbindung
```

### Performance-Monitoring

```python
# Detaillierte Performance-Statistiken
from price_tracker import SteamPriceTracker

tracker = SteamPriceTracker()
performance = tracker.get_performance_stats()

print(f"📊 Performance-Übersicht:")
print(f"   Durchschnittliche Update-Zeit: {performance['avg_update_time']:.2f}s")
print(f"   Successful Rate: {performance['success_rate']:.1f}%")
print(f"   Cache Hit Rate: {performance['cache_hit_rate']:.1f}%")
```

### Backup-System

```bash
# Automatisches Backup erstellen
python main.py  # Option 26: Backup erstellen

# Backup wiederherstellen
python main.py  # Option 27: Backup importieren

# Backup-Verzeichnis: ./backups/steam_tracker_backup_YYYYMMDD_HHMMSS/
```

## 🚀 Erweiterte Features

### Web Dashboard

```bash
# Flask-basiertes Web-Dashboard

python web_dashboard.py
# Dashboard verfügbar unter: http://localhost:5000
```

## 📊 Statistiken & Erfolgsmessung

### Beispiel-Ausgabe nach 30 Tagen Nutzung

```
🎉 Steam Price Tracker - 30-Tage-Bericht

📊 TRACKING-STATISTIKEN
   🎯 Apps getrackt: 847 (234 aus Wishlist, 156 aus Charts, 457 manuell)
   📊 Preis-Updates: 15,234 (durchschnittlich 508 pro Tag)
   💰 Deals entdeckt: 1,891 (durchschnittlich 63 pro Tag)
   📈 Beste Ersparnis: €47.99 für "Cyberpunk 2077" (-78%)

📈 CHARTS-INTEGRATION
   🔥 Trending Spiele getrackt: 156 
   🎯 Neu entdeckte Hits: 23
   📊 Charts-Updates: 2,134

🔍 ELASTICSEARCH-ANALYTICS
   📄 Dokumente indexiert: 67,891
   📊 Dashboards erstellt: 4
   🔍 Erweiterte Queries: 234

⏱️ PERFORMANCE
   🚀 Durchschnittliche Update-Zeit: 1.3s pro App
   ✅ Success Rate: 97.8%
   🏃 Background-Scheduler läuft seit: 29 Tage

💡 EMPFEHLUNGEN
   • 23 Spiele unter Ihrem Zielpreis verfügbar
   • 5 neue Charts-Hits zur Überwachung empfohlen
   • Nächstes Backup-Fenster: in 3 Tagen
```

## 🤝 Community & Beitragen

### Entwicklung

```bash
# Repository für Entwicklung klonen
git clone <repository-url>
cd steam-price-tracker

# Development-Environment einrichten
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Development-Dependencies installieren
pip install -r requirements-dev.txt

# Pre-commit hooks einrichten
pre-commit install

# Tests ausführen
python -m pytest tests/ -v

# Code-Quality prüfen
flake8 .
mypy price_tracker.py
```


### Code-Standards

- 🐍 **Python 3.8+** Kompatibilität
- 📝 **Type Hints** für alle Funktionen
- 📚 **Docstrings** im Google-Stil
- ✅ **Unit Tests** für neue Features
- 🎨 **PEP 8** Code-Stil


---

[⬆ Zurück zum Anfang](#-steam-price-tracker-v12-dev)

</div>