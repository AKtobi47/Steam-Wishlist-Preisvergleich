#!/usr/bin/env python3
"""
Elasticsearch Setup für Steam Price Tracker
Vollständige Elasticsearch/Kibana-Integration mit Docker Setup
"""

import sys
import os
import json
import argparse
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import logging

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ElasticsearchSetup:
    """Setup-Klasse für Elasticsearch-Integration"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.elasticsearch_dir = self.project_root / "elasticsearch"
        self.kibana_dir = self.project_root / "kibana"
        
    def check_docker_availability(self):
        """Prüft ob Docker verfügbar ist"""
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Docker verfügbar: {result.stdout.strip()}")
                return True
            else:
                logger.error("❌ Docker nicht verfügbar")
                return False
        except FileNotFoundError:
            logger.error("❌ Docker nicht installiert")
            return False
    
    def check_docker_compose_availability(self):
        """Prüft ob Docker Compose verfügbar ist"""
        try:
            # Teste docker compose (neue Version)
            result = subprocess.run(['docker', 'compose', 'version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Docker Compose verfügbar: {result.stdout.strip()}")
                return "docker compose"
        except:
            pass
        
        try:
            # Teste docker-compose (alte Version)
            result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Docker Compose verfügbar: {result.stdout.strip()}")
                return "docker-compose"
        except:
            pass
        
        logger.error("❌ Docker Compose nicht verfügbar")
        return None
    
    def create_directory_structure(self):
        """Erstellt Verzeichnisstruktur für Elasticsearch"""
        logger.info("📁 Erstelle Verzeichnisstruktur...")
        
        directories = [
            self.elasticsearch_dir,
            self.elasticsearch_dir / "config",
            self.elasticsearch_dir / "data", 
            self.elasticsearch_dir / "logs",
            self.kibana_dir,
            self.kibana_dir / "config",
            self.kibana_dir / "dashboards",
            Path("exports")
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"   📁 {directory}")
        
        return True
    
    def create_elasticsearch_config(self):
        """Erstellt Elasticsearch-Konfiguration"""
        logger.info("⚙️ Erstelle Elasticsearch-Konfiguration...")
        
        es_config = """# Elasticsearch Configuration for Steam Price Tracker
cluster.name: steam-price-tracker
node.name: node-1

# Network
network.host: 0.0.0.0
http.port: 9200

# Discovery
discovery.type: single-node

# Memory
bootstrap.memory_lock: true

# Security (für Development)
xpack.security.enabled: false
xpack.monitoring.collection.enabled: true

# Indices
action.auto_create_index: true
"""
        
        config_file = self.elasticsearch_dir / "config" / "elasticsearch.yml"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(es_config)
        
        logger.info(f"✅ Elasticsearch-Config erstellt: {config_file}")
        return True
    
    def create_kibana_config(self):
        """Erstellt Kibana-Konfiguration"""
        logger.info("⚙️ Erstelle Kibana-Konfiguration...")
        
        kibana_config = """# Kibana Configuration for Steam Price Tracker
server.name: steam-price-tracker-kibana
server.host: 0.0.0.0
server.port: 5601

# Elasticsearch
elasticsearch.hosts: ["http://elasticsearch:9200"]

# Monitoring
monitoring.ui.container.elasticsearch.enabled: true

# Dashboard Settings
kibana.index: ".kibana"

# Logging
logging.appenders:
  file:
    type: file
    fileName: /usr/share/kibana/logs/kibana.log
    layout:
      type: json

logging.root:
  appenders:
    - default
    - file
"""
        
        config_file = self.kibana_dir / "config" / "kibana.yml"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(kibana_config)
        
        logger.info(f"✅ Kibana-Config erstellt: {config_file}")
        return True
    
    def create_docker_compose_file(self):
        """Erstellt Docker Compose Datei"""
        logger.info("🐳 Erstelle Docker Compose Datei...")
        
        docker_compose = """version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: steam-tracker-elasticsearch
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
      - xpack.security.enabled=false
      - xpack.monitoring.collection.enabled=true
    ports:
      - "9200:9200"
      - "9300:9300"
    volumes:
      - ./elasticsearch/data:/usr/share/elasticsearch/data
      - ./elasticsearch/logs:/usr/share/elasticsearch/logs
      - ./elasticsearch/config/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml:ro
    networks:
      - elastic
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: steam-tracker-kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    volumes:
      - ./kibana/config/kibana.yml:/usr/share/kibana/config/kibana.yml:ro
      - ./kibana/dashboards:/usr/share/kibana/dashboards:ro
    networks:
      - elastic
    depends_on:
      elasticsearch:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:5601/api/status || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

networks:
  elastic:
    driver: bridge

volumes:
  elasticsearch_data:
  kibana_data:
"""
        
        compose_file = self.project_root / "docker-compose-elk.yml"
        with open(compose_file, 'w', encoding='utf-8') as f:
            f.write(docker_compose)
        
        logger.info(f"✅ Docker Compose erstellt: {compose_file}")
        return True
    
    def create_kibana_dashboards(self):
        """Erstellt Kibana Dashboard-Konfigurationen"""
        logger.info("📊 Erstelle Kibana Dashboard-Konfigurationen...")
        
        # Steam Price Tracker Overview Dashboard
        overview_dashboard = {
            "version": "8.11.0",
            "objects": [
                {
                    "id": "steam-price-tracker-overview",
                    "type": "dashboard",
                    "attributes": {
                        "title": "Steam Price Tracker - Overview",
                        "description": "Übersicht über Steam Price Tracker Daten",
                        "panelsJSON": json.dumps([
                            {
                                "id": "tracked-apps-count",
                                "type": "metric",
                                "gridData": {"x": 0, "y": 0, "w": 24, "h": 15}
                            },
                            {
                                "id": "price-snapshots-timeline",
                                "type": "line",
                                "gridData": {"x": 0, "y": 15, "w": 48, "h": 15}
                            }
                        ]),
                        "timeRestore": True,
                        "timeTo": "now",
                        "timeFrom": "now-30d",
                        "refreshInterval": {
                            "pause": False,
                            "value": 300000
                        }
                    }
                }
            ]
        }
        
        dashboard_file = self.kibana_dir / "dashboards" / "overview_dashboard.ndjson"
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            json.dump(overview_dashboard, f, indent=2)
        
        # Charts Analytics Dashboard
        charts_dashboard = {
            "version": "8.11.0",
            "objects": [
                {
                    "id": "steam-charts-analytics",
                    "type": "dashboard",
                    "attributes": {
                        "title": "Steam Charts Analytics",
                        "description": "Analyse der Steam Charts Daten",
                        "panelsJSON": json.dumps([
                            {
                                "id": "charts-by-type",
                                "type": "pie",
                                "gridData": {"x": 0, "y": 0, "w": 24, "h": 15}
                            },
                            {
                                "id": "chart-positions-timeline",
                                "type": "line", 
                                "gridData": {"x": 24, "y": 0, "w": 24, "h": 15}
                            }
                        ])
                    }
                }
            ]
        }
        
        charts_file = self.kibana_dir / "dashboards" / "charts_dashboard.ndjson"
        with open(charts_file, 'w', encoding='utf-8') as f:
            json.dump(charts_dashboard, f, indent=2)
        
        # Index Patterns
        index_patterns = {
            "version": "8.11.0",
            "objects": [
                {
                    "id": "steam-price-snapshots",
                    "type": "index-pattern",
                    "attributes": {
                        "title": "steam-price-snapshots*",
                        "timeFieldName": "timestamp"
                    }
                },
                {
                    "id": "steam-tracked-apps",
                    "type": "index-pattern", 
                    "attributes": {
                        "title": "steam-tracked-apps*",
                        "timeFieldName": "added_at"
                    }
                },
                {
                    "id": "steam-charts-tracking",
                    "type": "index-pattern",
                    "attributes": {
                        "title": "steam-charts-tracking*",
                        "timeFieldName": "last_seen"
                    }
                }
            ]
        }
        
        patterns_file = self.kibana_dir / "dashboards" / "index_patterns.ndjson"
        with open(patterns_file, 'w', encoding='utf-8') as f:
            json.dump(index_patterns, f, indent=2)
        
        logger.info(f"✅ Dashboard-Konfigurationen erstellt")
        return True
    
    def create_requirements_file(self):
        """Erstellt Requirements-Datei für Elasticsearch"""
        logger.info("📋 Erstelle Elasticsearch Requirements...")
        
        requirements = """# Elasticsearch Integration für Steam Price Tracker
elasticsearch>=8.11.0
elasticsearch-dsl>=8.11.0

# Optional: Für erweiterte Funktionen
pandas>=2.0.0
numpy>=1.24.0
"""
        
        req_file = self.project_root / "requirements-elasticsearch.txt"
        with open(req_file, 'w', encoding='utf-8') as f:
            f.write(requirements)
        
        logger.info(f"✅ Requirements erstellt: {req_file}")
        return True
    
    def create_elasticsearch_cli_script(self):
        """Erstellt CLI-Script für Elasticsearch-Management"""
        logger.info("🔧 Erstelle Elasticsearch CLI-Script...")
        
        cli_script = '''#!/usr/bin/env python3
"""
Elasticsearch CLI für Steam Price Tracker
Kommandozeilen-Tool für Elasticsearch-Management
"""

import argparse
import sys
from pathlib import Path

# Steam Price Tracker Module importieren
sys.path.insert(0, str(Path.cwd()))

def cmd_setup(args):
    """Elasticsearch Setup ausführen"""
    try:
        from elasticsearch_manager import setup_elasticsearch_for_steam_tracker
        from database_manager import DatabaseManager
        
        # Database Manager
        db_manager = DatabaseManager(args.db_path)
        
        # Elasticsearch Setup
        result = setup_elasticsearch_for_steam_tracker(
            db_manager, 
            host=args.host, 
            port=args.port,
            username=args.username,
            password=args.password
        )
        
        if result['success']:
            print("✅ Elasticsearch Setup erfolgreich!")
            print(f"   📊 {result['indices_created']} Indizes erstellt")
            print(f"   📋 {result['mappings_applied']} Mappings angewendet")
        else:
            print(f"❌ Setup fehlgeschlagen: {result['error']}")
            
    except ImportError:
        print("❌ elasticsearch_manager Modul nicht gefunden")
        print("💡 Installiere Elasticsearch: pip install -r requirements-elasticsearch.txt")
    except Exception as e:
        print(f"❌ Setup-Fehler: {e}")

def cmd_export(args):
    """Daten zu Elasticsearch exportieren"""
    try:
        from elasticsearch_manager import create_elasticsearch_manager
        from database_manager import DatabaseManager
        
        # Elasticsearch Manager
        es_manager = create_elasticsearch_manager(args.host, args.port, args.username, args.password)
        if not es_manager:
            print("❌ Elasticsearch-Verbindung fehlgeschlagen")
            return
        
        # Database Manager
        db_manager = DatabaseManager(args.db_path)
        
        # Export
        print("🚀 Starte Datenexport...")
        export_stats = es_manager.export_sqlite_to_elasticsearch(db_manager)
        
        print(f"✅ Export abgeschlossen:")
        print(f"   📊 Price Snapshots: {export_stats['price_snapshots']}")
        print(f"   📱 Tracked Apps: {export_stats['tracked_apps']}")
        print(f"   🔤 Name History: {export_stats['name_history']}")
        print(f"   📈 Charts: {export_stats['charts_tracking']}")
        print(f"   💰 Charts Prices: {export_stats['charts_prices']}")
        print(f"   📊 Statistiken: {export_stats['statistics']}")
        print(f"   🎯 Gesamt: {export_stats['total_exported']}")
        
    except Exception as e:
        print(f"❌ Export-Fehler: {e}")

def cmd_status(args):
    """Elasticsearch-Status anzeigen"""
    try:
        from elasticsearch_manager import create_elasticsearch_manager
        
        es_manager = create_elasticsearch_manager(args.host, args.port, args.username, args.password)
        if not es_manager:
            print("❌ Elasticsearch-Verbindung fehlgeschlagen")
            return
        
        # Health Check
        health = es_manager.health_check()
        
        if health['connection_ok']:
            print("✅ Elasticsearch-Status:")
            print(f"   🔗 Cluster: {health['cluster_name']}")
            print(f"   📊 Status: {health['cluster_status']}")
            print(f"   🖥️ Nodes: {health['number_of_nodes']}")
            print(f"   📁 Shards: {health['active_shards']}")
            print(f"   📄 Dokumente: {health['total_documents']}")
            
            print("\\n📋 Index-Details:")
            for name, stats in health['indices'].items():
                if stats['exists']:
                    print(f"   • {stats['index_name']}: {stats['document_count']} Dokumente")
                else:
                    print(f"   • {stats['index_name']}: nicht vorhanden")
        else:
            print(f"❌ Elasticsearch nicht erreichbar: {health['error']}")
            
    except Exception as e:
        print(f"❌ Status-Fehler: {e}")

def cmd_reset(args):
    """Elasticsearch-Indizes zurücksetzen"""
    try:
        from elasticsearch_manager import create_elasticsearch_manager
        
        es_manager = create_elasticsearch_manager(args.host, args.port, args.username, args.password)
        if not es_manager:
            print("❌ Elasticsearch-Verbindung fehlgeschlagen")
            return
        
        if not args.force:
            confirm = input("⚠️ WARNUNG: Alle Steam Price Tracker Indizes werden gelöscht! Fortfahren? (ja/nein): ")
            if confirm.lower() not in ['ja', 'j', 'yes', 'y']:
                print("❌ Abgebrochen")
                return
        
        # Indizes löschen
        deleted = es_manager.delete_all_indices()
        print(f"🗑️ {deleted} Indizes gelöscht")
        
        # Neue Indizes erstellen
        created = es_manager.create_indices_and_mappings()
        print(f"✅ {created} neue Indizes erstellt")
        
    except Exception as e:
        print(f"❌ Reset-Fehler: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Elasticsearch CLI für Steam Price Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Globale Argumente
    parser.add_argument('--host', default='localhost', help='Elasticsearch Host')
    parser.add_argument('--port', type=int, default=9200, help='Elasticsearch Port')
    parser.add_argument('--username', help='Elasticsearch Username')
    parser.add_argument('--password', help='Elasticsearch Password')
    parser.add_argument('--db-path', default='steam_price_tracker.db', help='SQLite Datenbank Pfad')
    
    subparsers = parser.add_subparsers(dest='command', help='Kommandos')
    
    # Setup Command
    setup_parser = subparsers.add_parser('setup', help='Vollständiges Elasticsearch Setup')
    setup_parser.set_defaults(func=cmd_setup)
    
    # Export Command
    export_parser = subparsers.add_parser('export', help='Daten zu Elasticsearch exportieren')
    export_parser.set_defaults(func=cmd_export)
    
    # Status Command
    status_parser = subparsers.add_parser('status', help='Elasticsearch-Status anzeigen')
    status_parser.set_defaults(func=cmd_status)
    
    # Reset Command
    reset_parser = subparsers.add_parser('reset', help='Elasticsearch-Indizes zurücksetzen')
    reset_parser.add_argument('--force', action='store_true', help='Ohne Bestätigung ausführen')
    reset_parser.set_defaults(func=cmd_reset)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\\n⏹️ Abgebrochen durch Benutzer")
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")

if __name__ == "__main__":
    main()
'''
        
        cli_file = self.project_root / "elasticsearch_cli.py"
        with open(cli_file, 'w', encoding='utf-8') as f:
            f.write(cli_script)
        
        logger.info(f"✅ Elasticsearch CLI erstellt: {cli_file}")
        return True
    
    def start_stack(self):
        """Startet Elasticsearch/Kibana Stack"""
        logger.info("🚀 Starte Elasticsearch/Kibana Stack...")
        
        compose_cmd = self.check_docker_compose_availability()
        if not compose_cmd:
            logger.error("❌ Docker Compose nicht verfügbar")
            return False
        
        try:
            # Docker Compose Up
            cmd = compose_cmd.split() + ["-f", "docker-compose-elk.yml", "up", "-d"]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                logger.info("✅ Elasticsearch/Kibana Stack gestartet")
                logger.info("📊 Elasticsearch: http://localhost:9200")
                logger.info("📈 Kibana: http://localhost:5601")
                return True
            else:
                logger.error(f"❌ Fehler beim Starten: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten: {e}")
            return False
    
    def stop_stack(self):
        """Stoppt Elasticsearch/Kibana Stack"""
        logger.info("⏹️ Stoppe Elasticsearch/Kibana Stack...")
        
        compose_cmd = self.check_docker_compose_availability()
        if not compose_cmd:
            logger.error("❌ Docker Compose nicht verfügbar")
            return False
        
        try:
            # Docker Compose Down
            cmd = compose_cmd.split() + ["-f", "docker-compose-elk.yml", "down"]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                logger.info("✅ Elasticsearch/Kibana Stack gestoppt")
                return True
            else:
                logger.error("❌ Fehler beim Stoppen des Stacks")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Stoppen: {e}")
            return False
    
    def full_setup(self):
        """Führt komplettes Setup durch"""
        logger.info("🚀 ELASTICSEARCH/KIBANA SETUP FÜR STEAM PRICE TRACKER")
        logger.info("=" * 60)
        
        steps = [
            ("Verzeichnisstruktur erstellen", self.create_directory_structure),
            ("Elasticsearch Konfiguration", self.create_elasticsearch_config),
            ("Kibana Konfiguration", self.create_kibana_config),
            ("Docker Compose Datei", self.create_docker_compose_file),
            ("Kibana Dashboards", self.create_kibana_dashboards),
            ("Elasticsearch CLI", self.create_elasticsearch_cli_script),
            ("Requirements erstellen", self.create_requirements_file)
        ]
        
        success_count = 0
        for step_name, step_function in steps:
            logger.info(f"🔧 {step_name}...")
            try:
                if step_function():
                    success_count += 1
                    logger.info(f"✅ {step_name} erfolgreich")
                else:
                    logger.error(f"❌ {step_name} fehlgeschlagen")
            except Exception as e:
                logger.error(f"❌ {step_name} Fehler: {e}")
        
        logger.info(f"\n🎉 Setup abgeschlossen: {success_count}/{len(steps)} Schritte erfolgreich")
        
        # Docker-Verfügbarkeit prüfen
        docker_available = self.check_docker_availability()
        compose_available = self.check_docker_compose_availability()
        
        if docker_available and compose_available:
            logger.info("\n📋 NÄCHSTE SCHRITTE:")
            logger.info("1. Installiere Elasticsearch Python Library:")
            logger.info("   pip install -r requirements-elasticsearch.txt")
            logger.info("")
            logger.info("2. Starte Elasticsearch/Kibana Stack:")
            logger.info("   python elasticsearch_setup.py start")
            logger.info("   ODER")
            logger.info(f"   {compose_available} -f docker-compose-elk.yml up -d")
            logger.info("")
            logger.info("3. Setup und Datenexport:")
            logger.info("   python elasticsearch_cli.py setup")
            logger.info("")
            logger.info("4. Kibana Dashboard öffnen:")
            logger.info("   http://localhost:5601")
        else:
            logger.warning("\n⚠️ Docker/Docker Compose nicht verfügbar")
            logger.info("📋 Installiere Docker um die ELK Stack zu nutzen")
        
        return success_count >= len(steps) * 0.8

def cmd_setup(args):
    """Setup-Kommando"""
    setup = ElasticsearchSetup()
    return setup.full_setup()

def cmd_start(args):
    """Start-Kommando"""
    setup = ElasticsearchSetup()
    return setup.start_stack()

def cmd_stop(args):
    """Stop-Kommando"""
    setup = ElasticsearchSetup()
    return setup.stop_stack()

def cmd_status(args):
    """Status-Kommando"""
    setup = ElasticsearchSetup()
    
    # Docker-Status prüfen
    docker_available = setup.check_docker_availability()
    compose_available = setup.check_docker_compose_availability()
    
    print("📊 ELASTICSEARCH SETUP STATUS")
    print("=" * 40)
    print(f"🐳 Docker: {'✅ Verfügbar' if docker_available else '❌ Nicht verfügbar'}")
    print(f"🐙 Docker Compose: {'✅ Verfügbar' if compose_available else '❌ Nicht verfügbar'}")
    
    # Dateien prüfen
    files_to_check = [
        "docker-compose-elk.yml",
        "elasticsearch_cli.py", 
        "requirements-elasticsearch.txt",
        "elasticsearch/config/elasticsearch.yml",
        "kibana/config/kibana.yml"
    ]
    
    print(f"\n📁 DATEIEN:")
    for file_path in files_to_check:
        file_exists = Path(file_path).exists()
        print(f"   {'✅' if file_exists else '❌'} {file_path}")
    
    # Container-Status (falls Docker verfügbar)
    if docker_available:
        try:
            result = subprocess.run(['docker', 'ps', '--filter', 'name=steam-tracker'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and 'steam-tracker' in result.stdout:
                print(f"\n🐳 CONTAINER:")
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # Skip header
                    if 'steam-tracker' in line:
                        print(f"   ✅ {line.split()[-1]} läuft")
            else:
                print(f"\n🐳 CONTAINER: ❌ Keine Steam Tracker Container laufen")
        except Exception as e:
            print(f"\n🐳 CONTAINER: ❌ Fehler beim Prüfen: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Elasticsearch Setup für Steam Price Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s setup     - Vollständiges Setup durchführen
  %(prog)s start     - Elasticsearch/Kibana Stack starten
  %(prog)s stop      - Elasticsearch/Kibana Stack stoppen
  %(prog)s status    - Setup-Status anzeigen
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Verfügbare Kommandos')
    
    # Setup Command
    setup_parser = subparsers.add_parser('setup', help='Vollständiges Elasticsearch Setup')
    setup_parser.set_defaults(func=cmd_setup)
    
    # Start Command
    start_parser = subparsers.add_parser('start', help='Elasticsearch/Kibana Stack starten')
    start_parser.set_defaults(func=cmd_start)
    
    # Stop Command
    stop_parser = subparsers.add_parser('stop', help='Elasticsearch/Kibana Stack stoppen')
    stop_parser.set_defaults(func=cmd_stop)
    
    # Status Command
    status_parser = subparsers.add_parser('status', help='Setup-Status anzeigen')
    status_parser.set_defaults(func=cmd_status)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        success = args.func(args)
        if success:
            logger.info("✅ Kommando erfolgreich ausgeführt")
        else:
            logger.error("❌ Kommando fehlgeschlagen")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Abgebrochen durch Benutzer")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unerwarteter Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()