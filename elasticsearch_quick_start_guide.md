# 📊 Elasticsearch/Kibana Quick Start Guide für Steam Price Tracker

## 🚀 Schnelle Einrichtung in 5 Minuten

### Schritt 1: Elasticsearch-Setup
```bash
# 1. Elasticsearch-Umgebung einrichten
python elasticsearch_setup.py setup

# 2. Docker-Container starten
python elasticsearch_setup.py start

# 3. Python-Abhängigkeiten installieren  
pip install -r requirements-elasticsearch.txt
```

### Schritt 2: Daten exportieren
```bash
# Vollständiger Export aller Steam Price Tracker Daten
python elasticsearch_cli.py setup

# Oder nur Daten exportieren (falls bereits eingerichtet)
python elasticsearch_cli.py export
```

### Schritt 3: Kibana öffnen
```bash
# Öffne http://localhost:5601 im Browser
# Oder aus der Hauptanwendung: Option "Kibana Dashboard öffnen"
```

## 📊 Verfügbare Datenindizes

### 🎯 steam-price-snapshots
**Haupt-Preisdaten mit allen Store-Informationen**
- `game_title`: Spielname
- `timestamp`: Zeitpunkt der Preisabfrage
- `best_price`: Bester verfügbarer Preis
- `best_store`: Store mit dem besten Preis
- `max_discount`: Höchster Rabatt in %
- `available_stores_count`: Anzahl Stores mit dem Spiel
- `store_data`: Detaillierte Preisinformationen pro Store

### 📱 steam-tracked-apps  
**Informationen über getrackte Apps**
- `name`: App-Name
- `steam_app_id`: Steam Application ID
- `added_at`: Hinzugefügt am
- `last_price_update`: Letzte Preisabfrage
- `days_tracked`: Tage im Tracking
- `has_generic_name`: Hat generischen Namen
- `total_snapshots`: Anzahl Preis-Snapshots

### 📊 steam-charts-tracking
**Steam Charts-Spiele (falls Charts aktiviert)**
- `name`: Spielname
- `chart_type`: Art des Charts (most_played, top_releases, etc.)
- `current_rank`: Aktuelle Position
- `best_rank`: Beste je erreichte Position
- `days_in_charts`: Tage in den Charts
- `popularity_score`: Popularitätsbewertung

### 🔤 steam-name-history
**Historie der Namen-Updates**
- `old_name`: Alter Name
- `new_name`: Neuer Name
- `update_source`: Quelle des Updates
- `name_change_type`: Art der Namensänderung

## 🔍 Nützliche Kibana-Queries

### Preisanalysen
```
# Hohe Rabatte finden
max_discount:>50

# Beste Steam-Deals
best_store:"steam" AND max_discount:>25

# Preisentwicklung letzte Woche
timestamp:>now-7d

# Apps mit vielen Preis-Updates
available_stores_count:>3
```

### App-Management
```
# Apps mit generischen Namen
has_generic_name:true

# Kürzlich hinzugefügte Apps
added_at:>now-30d

# Apps ohne aktuelle Preisdaten
NOT last_price_update:>now-7d
```

### Charts-Analysen (falls verfügbar)
```
# Trending Spiele
chart_type:"most_played" AND current_rank:[1 TO 10]

# Spiele die in Charts gefallen sind
rank_trend:"declining"

# Lange in Charts
days_in_charts:>30
```

## 📈 Empfohlene Dashboards

### 1. 📊 Preis-Übersicht Dashboard
- **Preise über Zeit**: Line Chart mit `timestamp` vs `best_price`
- **Store-Vergleich**: Bar Chart mit Store-Namen vs Durchschnittspreis
- **Rabatt-Verteilung**: Pie Chart der Rabatt-Bereiche
- **Top-Deals**: Data Table mit höchsten Rabatten

### 2. 📱 App-Management Dashboard
- **App-Status**: Metric mit Anzahl getrackte Apps
- **Hinzufügungen**: Area Chart neue Apps über Zeit
- **Generische Namen**: Metric für Apps mit generischen Namen
- **Update-Frequenz**: Heatmap der letzten Updates

### 3. 📊 Charts-Dashboard (falls Charts aktiv)
- **Charts-Verteilung**: Pie Chart nach Chart-Typen
- **Ranking-Trends**: Line Chart für Ranking-Entwicklung
- **Popularität**: Bar Chart Top-Spiele nach Popularitätsscore
- **Charts-Historie**: Timeline der Charts-Auftritte

## ⚡ Performance-Tipps

### Kibana-Optimierung
1. **Zeitfilter nutzen**: Beschränke Abfragen auf relevante Zeiträume
2. **Index Patterns**: Verwende spezifische Patterns statt Wildcards
3. **Aggregationen**: Nutze Aggregationen statt Rohdaten-Tabellen
4. **Refresh-Intervall**: Stelle längere Refresh-Intervalle ein

### Elasticsearch-Optimierung
```bash
# Index-Status prüfen
python elasticsearch_cli.py status

# Bei Performance-Problemen: Indizes neu aufbauen
python elasticsearch_cli.py reset --force

# Nur aktuelle Daten exportieren (letzte 30 Tage)
#