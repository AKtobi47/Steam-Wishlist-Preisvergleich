# Kibana Dashboard Setup für Steam Price Tracker

## Automatische Index Pattern Erstellung

Nach dem Start von Elasticsearch und Kibana:

1. Öffne Kibana: http://localhost:5601
2. Navigiere zu Stack Management > Index Patterns
3. Erstelle folgende Index Patterns:

### Index Patterns:
- `steam-price-snapshots*` (Time field: timestamp)
- `steam-tracked-apps*` (Time field: added_at)
- `steam-charts-tracking*` (Time field: first_seen)
- `steam-name-history*` (Time field: updated_at)
- `steam-charts-prices*` (Time field: timestamp)
- `steam-statistics*` (Time field: timestamp)

### Dashboard Import:
1. Navigiere zu Stack Management > Saved Objects
2. Importiere die Dashboard-Konfigurationen aus diesem Verzeichnis
3. Die Dashboards sind dann unter Analytics > Dashboard verfügbar

### Verfügbare Dashboards:
1. **Steam Price Tracker - Overview**: Allgemeine Übersicht
2. **Steam Charts Analytics**: Charts-spezifische Analysen
3. **Price Analysis**: Detaillierte Preisanalysen

### Kibana Query Beispiele:

```
# Alle Apps mit hohen Rabatten
max_discount:>50

# Spiele in Steam Charts
chart_type:*

# Apps mit generischen Namen
has_generic_name:true

# Preise der letzten 7 Tage
timestamp:>now-7d

# Beste Deals nach Store
best_store:"steam" AND max_discount:>25
```

### Alerting Setup:
1. Navigiere zu Stack Management > Rules and Connectors
2. Erstelle Alerts für:
   - Neue hohe Rabatte (>50%)
   - Charts-Position Änderungen
   - Preis-Drops bei verfolgten Spielen

### Performance-Tipps:
- Verwende Zeitfilter für große Datenmengen
- Nutze Aggregationen statt Rohdaten
- Begrenze Tabellen-Ansichten auf relevante Felder
