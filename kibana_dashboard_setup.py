#!/usr/bin/env python3
"""
Kibana Dashboard Setup für Steam Price Tracker
Erstellt automatisch Index Patterns, Dashboards und Visualisierungen
"""

import json
import requests
import time
import sys
from pathlib import Path
import logging

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KibanaDashboardSetup:
    """Setup-Klasse für Kibana Dashboards"""
    
    def __init__(self, kibana_url="http://localhost:5601"):
        self.kibana_url = kibana_url
        self.headers = {
            'Content-Type': 'application/json',
            'kbn-xsrf': 'true'
        }
    
    def wait_for_kibana(self, max_retries=30, retry_interval=10):
        """Wartet bis Kibana verfügbar ist"""
        logger.info("🔄 Warte auf Kibana...")
        
        for attempt in range(max_retries):
            try:
                response = requests.get(f"{self.kibana_url}/api/status", timeout=5)
                if response.status_code == 200:
                    logger.info("✅ Kibana ist verfügbar")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            logger.info(f"⏳ Versuch {attempt + 1}/{max_retries} - warte {retry_interval}s...")
            time.sleep(retry_interval)
        
        logger.error("❌ Kibana nicht verfügbar nach maximaler Wartezeit")
        return False
    
    def create_index_pattern(self, pattern_id, title, time_field=None):
        """Erstellt ein Index Pattern"""
        logger.info(f"📋 Erstelle Index Pattern: {title}")
        
        pattern_data = {
            "attributes": {
                "title": title,
                "timeFieldName": time_field if time_field else ""
            }
        }
        
        try:
            response = requests.post(
                f"{self.kibana_url}/api/saved_objects/index-pattern/{pattern_id}",
                headers=self.headers,
                json=pattern_data
            )
            
            if response.status_code in [200, 409]:  # 409 = already exists
                logger.info(f"✅ Index Pattern '{title}' erstellt/aktualisiert")
                return True
            else:
                logger.error(f"❌ Fehler beim Erstellen des Index Patterns: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Verbindungsfehler: {e}")
            return False
    
    def create_visualization(self, viz_id, title, viz_type, source_id):
        """Erstellt eine Visualisierung"""
        logger.info(f"📊 Erstelle Visualisierung: {title}")
        
        # Basis-Visualisierung je nach Typ
        if viz_type == "metric":
            viz_state = {
                "title": title,
                "type": "metric",
                "params": {
                    "addTooltip": True,
                    "addLegend": False,
                    "type": "metric",
                    "metric": {
                        "percentageMode": False,
                        "useRanges": False,
                        "colorSchema": "Green to Red",
                        "metricColorMode": "None",
                        "colorsRange": [{"from": 0, "to": 10000}],
                        "labels": {"show": True},
                        "invertColors": False,
                        "style": {
                            "bgFill": "#000",
                            "bgColor": False,
                            "labelColor": False,
                            "subText": "",
                            "fontSize": 60
                        }
                    }
                },
                "aggs": [
                    {
                        "id": "1",
                        "enabled": True,
                        "type": "count",
                        "schema": "metric",
                        "params": {}
                    }
                ]
            }
        elif viz_type == "line":
            viz_state = {
                "title": title,
                "type": "line",
                "params": {
                    "grid": {"categoryLines": False, "style": {"color": "#eee"}},
                    "categoryAxes": [
                        {
                            "id": "CategoryAxis-1",
                            "type": "category",
                            "position": "bottom",
                            "show": True,
                            "style": {},
                            "scale": {"type": "linear"},
                            "labels": {"show": True, "truncate": 100},
                            "title": {}
                        }
                    ],
                    "valueAxes": [
                        {
                            "id": "ValueAxis-1",
                            "name": "LeftAxis-1",
                            "type": "value",
                            "position": "left",
                            "show": True,
                            "style": {},
                            "scale": {"type": "linear", "mode": "normal"},
                            "labels": {"show": True, "rotate": 0, "filter": False, "truncate": 100},
                            "title": {"text": "Count"}
                        }
                    ],
                    "seriesParams": [
                        {
                            "show": "true",
                            "type": "line",
                            "mode": "normal",
                            "data": {"label": "Count", "id": "1"},
                            "valueAxis": "ValueAxis-1",
                            "drawLinesBetweenPoints": True,
                            "showCircles": True
                        }
                    ],
                    "addTooltip": True,
                    "addLegend": True,
                    "legendPosition": "right",
                    "times": [],
                    "addTimeMarker": False
                },
                "aggs": [
                    {
                        "id": "1",
                        "enabled": True,
                        "type": "count",
                        "schema": "metric",
                        "params": {}
                    },
                    {
                        "id": "2",
                        "enabled": True,
                        "type": "date_histogram",
                        "schema": "segment",
                        "params": {
                            "field": "timestamp",
                            "interval": "auto",
                            "customInterval": "2h",
                            "min_doc_count": 1,
                            "extended_bounds": {}
                        }
                    }
                ]
            }
        elif viz_type == "pie":
            viz_state = {
                "title": title,
                "type": "pie",
                "params": {
                    "addTooltip": True,
                    "addLegend": True,
                    "legendPosition": "right",
                    "isDonut": True
                },
                "aggs": [
                    {
                        "id": "1",
                        "enabled": True,
                        "type": "count",
                        "schema": "metric",
                        "params": {}
                    },
                    {
                        "id": "2",
                        "enabled": True,
                        "type": "terms",
                        "schema": "segment",
                        "params": {
                            "field": "chart_type.keyword",
                            "size": 10,
                            "order": "desc",
                            "orderBy": "1"
                        }
                    }
                ]
            }
        else:
            viz_state = {"title": title, "type": viz_type}
        
        viz_data = {
            "attributes": {
                "title": title,
                "visState": json.dumps(viz_state),
                "uiStateJSON": "{}",
                "description": "",
                "version": 1,
                "kibanaSavedObjectMeta": {
                    "searchSourceJSON": json.dumps({
                        "index": source_id,
                        "query": {"match_all": {}},
                        "filter": []
                    })
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.kibana_url}/api/saved_objects/visualization/{viz_id}",
                headers=self.headers,
                json=viz_data
            )
            
            if response.status_code in [200, 409]:
                logger.info(f"✅ Visualisierung '{title}' erstellt/aktualisiert")
                return True
            else:
                logger.error(f"❌ Fehler beim Erstellen der Visualisierung: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Verbindungsfehler: {e}")
            return False
    
    def create_dashboard(self, dashboard_id, title, panel_configs):
        """Erstellt ein Dashboard mit Panels"""
        logger.info(f"📊 Erstelle Dashboard: {title}")
        
        panels = []
        for i, panel in enumerate(panel_configs):
            panels.append({
                "version": "8.11.0",
                "type": panel["type"],
                "gridData": {
                    "x": panel.get("x", 0),
                    "y": panel.get("y", 0),
                    "w": panel.get("w", 24),
                    "h": panel.get("h", 15),
                    "i": str(i)
                },
                "panelIndex": str(i),
                "embeddableConfig": {},
                "panelRefName": f"panel_{i}"
            })
        
        dashboard_data = {
            "attributes": {
                "title": title,
                "hits": 0,
                "description": f"Dashboard für {title}",
                "panelsJSON": json.dumps(panels),
                "optionsJSON": json.dumps({
                    "useMargins": True,
                    "syncColors": False,
                    "hidePanelTitles": False
                }),
                "version": 1,
                "timeRestore": True,
                "timeTo": "now",
                "timeFrom": "now-30d",
                "refreshInterval": {
                    "pause": False,
                    "value": 300000
                },
                "kibanaSavedObjectMeta": {
                    "searchSourceJSON": json.dumps({
                        "query": {"match_all": {}},
                        "filter": []
                    })
                }
            },
            "references": []
        }
        
        # References für Panels hinzufügen
        for i, panel in enumerate(panel_configs):
            dashboard_data["references"].append({
                "name": f"panel_{i}",
                "type": "visualization",
                "id": panel["viz_id"]
            })
        
        try:
            response = requests.post(
                f"{self.kibana_url}/api/saved_objects/dashboard/{dashboard_id}",
                headers=self.headers,
                json=dashboard_data
            )
            
            if response.status_code in [200, 409]:
                logger.info(f"✅ Dashboard '{title}' erstellt/aktualisiert")
                return True
            else:
                logger.error(f"❌ Fehler beim Erstellen des Dashboards: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Verbindungsfehler: {e}")
            return False
    
    def setup_steam_price_tracker_dashboards(self):
        """Erstellt alle Steam Price Tracker Dashboards"""
        logger.info("🚀 Setup Steam Price Tracker Dashboards")
        logger.info("=" * 50)
        
        # 1. Index Patterns erstellen
        logger.info("📋 Erstelle Index Patterns...")
        index_patterns = [
            ("steam-price-snapshots", "steam-price-snapshots*", "timestamp"),
            ("steam-tracked-apps", "steam-tracked-apps*", "added_at"),
            ("steam-charts-tracking", "steam-charts-tracking*", "last_seen"),
            ("steam-charts-prices", "steam-charts-prices*", "timestamp"),
            ("steam-name-history", "steam-name-history*", "updated_at")
        ]
        
        for pattern_id, title, time_field in index_patterns:
            self.create_index_pattern(pattern_id, title, time_field)
        
        # 2. Visualisierungen erstellen
        logger.info("📊 Erstelle Visualisierungen...")
        
        # Tracked Apps Count
        self.create_visualization(
            "tracked-apps-count",
            "Anzahl getrackte Apps",
            "metric",
            "steam-tracked-apps"
        )
        
        # Price Snapshots Timeline
        self.create_visualization(
            "price-snapshots-timeline",
            "Preis-Snapshots über Zeit",
            "line",
            "steam-price-snapshots"
        )
        
        # Charts by Type
        self.create_visualization(
            "charts-by-type",
            "Charts nach Typ",
            "pie",
            "steam-charts-tracking"
        )
        
        # Best Deals
        self.create_visualization(
            "best-deals-table",
            "Beste aktuelle Deals",
            "table",
            "steam-price-snapshots"
        )
        
        # Store Distribution
        self.create_visualization(
            "store-distribution",
            "Verteilung nach Stores",
            "pie",
            "steam-price-snapshots"
        )
        
        # Price Timeline
        self.create_visualization(
            "price-timeline",
            "Preisentwicklung",
            "line",
            "steam-price-snapshots"
        )
        
        # 3. Dashboards erstellen
        logger.info("📊 Erstelle Dashboards...")
        
        # Overview Dashboard
        overview_panels = [
            {"viz_id": "tracked-apps-count", "type": "visualization", "x": 0, "y": 0, "w": 12, "h": 8},
            {"viz_id": "price-snapshots-timeline", "type": "visualization", "x": 12, "y": 0, "w": 36, "h": 8},
            {"viz_id": "store-distribution", "type": "visualization", "x": 0, "y": 8, "w": 24, "h": 16},
            {"viz_id": "best-deals-table", "type": "visualization", "x": 24, "y": 8, "w": 24, "h": 16}
        ]
        
        self.create_dashboard(
            "steam-price-tracker-overview",
            "Steam Price Tracker - Overview",
            overview_panels
        )
        
        # Charts Dashboard
        charts_panels = [
            {"viz_id": "charts-by-type", "type": "visualization", "x": 0, "y": 0, "w": 24, "h": 15},
            {"viz_id": "price-timeline", "type": "visualization", "x": 24, "y": 0, "w": 24, "h": 15}
        ]
        
        self.create_dashboard(
            "steam-charts-analytics",
            "Steam Charts Analytics",
            charts_panels
        )
        
        logger.info("✅ Dashboard Setup abgeschlossen!")
        logger.info(f"🌐 Kibana Dashboard: {self.kibana_url}/app/dashboards")
    
    def export_dashboards(self, output_dir="kibana/dashboards"):
        """Exportiert alle Dashboards als JSON"""
        logger.info("📤 Exportiere Dashboards...")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Dashboard IDs
        dashboard_ids = [
            "steam-price-tracker-overview",
            "steam-charts-analytics"
        ]
        
        for dashboard_id in dashboard_ids:
            try:
                response = requests.get(
                    f"{self.kibana_url}/api/saved_objects/dashboard/{dashboard_id}",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    dashboard_data = response.json()
                    
                    export_file = output_path / f"{dashboard_id}.json"
                    with open(export_file, 'w', encoding='utf-8') as f:
                        json.dump(dashboard_data, f, indent=2)
                    
                    logger.info(f"✅ Dashboard exportiert: {export_file}")
                else:
                    logger.error(f"❌ Fehler beim Exportieren von {dashboard_id}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Export-Fehler für {dashboard_id}: {e}")

def main():
    """Hauptfunktion"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Kibana Dashboard Setup für Steam Price Tracker")
    parser.add_argument('--kibana-url', default='http://localhost:5601', 
                       help='Kibana URL (Standard: http://localhost:5601)')
    parser.add_argument('--wait', action='store_true',
                       help='Warte auf Kibana bevor Setup startet')
    parser.add_argument('--export', action='store_true',
                       help='Exportiere Dashboards nach Setup')
    
    args = parser.parse_args()
    
    setup = KibanaDashboardSetup(args.kibana_url)
    
    try:
        # Warte auf Kibana falls gewünscht
        if args.wait:
            if not setup.wait_for_kibana():
                logger.error("❌ Kibana nicht verfügbar - Setup abgebrochen")
                sys.exit(1)
        
        # Dashboard Setup
        setup.setup_steam_price_tracker_dashboards()
        
        # Export falls gewünscht
        if args.export:
            setup.export_dashboards()
        
        logger.info("🎉 Setup erfolgreich abgeschlossen!")
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ Setup abgebrochen durch Benutzer")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unerwarteter Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()