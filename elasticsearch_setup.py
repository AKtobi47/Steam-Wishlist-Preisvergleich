#!/usr/bin/env python3
"""
Elasticsearch Setup Script für Steam Price Tracker
Vollständige Einrichtung von Elasticsearch und Kibana für Datenanalyse
"""

import os
import sys
import json
import argparse
import subprocess
import time
from pathlib import Path
from datetime import datetime
import logging

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ElasticsearchSetup:
    """Setup-Manager für Elasticsearch/Kibana Integration"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.elasticsearch_dir = self.project_root / "elasticsearch"
        self.kibana_dir = self.project_root / "kibana"
        self.docker_compose_file = self.project_root / "docker-compose-elk.yml"
        
    def create_directory_structure(self):
        """Erstellt die erforderliche Verzeichnisstruktur"""
        logger.info("📁 Erstelle Elasticsearch/Kibana Verzeichnisstruktur...")
        
        directories = [
            self.elasticsearch_dir / "config",
            self.elasticsearch_dir / "data",
            self.elasticsearch_dir / "logs",
            self.kibana_dir / "config",
            self.kibana_dir / "data",
            self.kibana_dir / "dashboards"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Erstellt: {directory}")
        
        return True
    
    def create_elasticsearch_config(self):
        """Erstellt Elasticsearch-Konfigurationsdateien"""
        logger.info("⚙️ Erstelle Elasticsearch Konfiguration...")
        
        # elasticsearch.yml
        elasticsearch_config = """# Elasticsearch Konfiguration für Steam Price Tracker
cluster.name: steam-analytics
node.name: steam-elasticsearch-node
path.data: /usr/share/elasticsearch/data
path.logs: /usr/share/elasticsearch/logs
network.host: 0.0.0.0
http.port: 9200
discovery.type: single-node

# Sicherheit deaktiviert für lokale Entwicklung
xpack.security.enabled: false
xpack.security.enrollment.enabled: false
xpack.security.http.ssl.enabled: false
xpack.security.transport.ssl.enabled: false

# Performance-Einstellungen
bootstrap.memory_lock: true
indices.query.bool.max_clause_count: 10000

# Index-Einstellungen
action.auto_create_index: true
action.destructive_requires_name: false

# Monitoring
xpack.monitoring.collection.enabled: true
"""
        
        config_file = self.elasticsearch_dir / "config" / "elasticsearch.yml"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(elasticsearch_config)
        
        logger.info(f"✅ Elasticsearch Config erstellt: {config_file}")
        return True
    
    def create_kibana_config(self):
        """Erstellt Kibana-Konfigurationsdateien"""
        logger.info("⚙️ Erstelle Kibana Konfiguration...")
        
        # kibana.yml
        kibana_config = """# Kibana Konfiguration für Steam Price Tracker
server.name: steam-kibana
server.host: 0.0.0.0
server.port: 5601

elasticsearch.hosts: ["http://elasticsearch:9200"]
elasticsearch.requestTimeout: 60000

# Sicherheit deaktiviert für lokale Entwicklung
xpack.security.enabled: false
xpack.encryptedSavedObjects.encryptionKey: "steam-analytics-encryption-key-32-chars"

# Logging
logging.appenders.file.type: file
logging.appenders.file.fileName: /usr/share/kibana/logs/kibana.log
logging.appenders.file.layout.type: json

logging.root.level: info
logging.root.appenders: [default, file]

# Telemetrie deaktivieren
telemetry.enabled: false
telemetry.optIn: false

# Performance
elasticsearch.shardTimeout: 30000
elasticsearch.requestHeadersWhitelist: ["authorization"]

# Data Views
data.search.aggs.shards.max_buckets: 65536

# Dashboard-Einstellungen
newsfeed.enabled: false
"""
        
        config_file = self.kibana_dir / "config" / "kibana.yml"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(kibana_config)
        
        logger.info(f"✅ Kibana Config erstellt: {config_file}")
        return True
    
    def create_docker_compose_file(self):
        """Erstellt Docker Compose Datei"""
        logger.info("🐳 Erstelle Docker Compose Datei...")
        
        docker_compose_content = """# Docker Compose für Steam Price Tracker Analytics
# Elasticsearch + Kibana Stack für Datenanalyse
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: steam-elasticsearch
    environment:
      - node.name=steam-elasticsearch
      - cluster.name=steam-analytics
      - discovery.type=single-node
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
      - xpack.security.enabled=false
      - xpack.security.enrollment.enabled=false
      - xpack.security.http.ssl.enabled=false
      - xpack.security.transport.ssl.enabled=false
    ulimits:
      memlock:
        soft: -1
        hard: -1
    mem_limit: 3g
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
      - ./elasticsearch/config/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml:ro
      - ./elasticsearch/logs:/usr/share/elasticsearch/logs
    ports:
      - "9200:9200"
      - "9300:9300"
    networks:
      - steam-analytics
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 10
      start_period: 60s

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: steam-kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
      - SERVER_NAME=steam-kibana
      - SERVER_HOST=0.0.0.0
      - xpack.security.enabled=false
      - xpack.encryptedSavedObjects.encryptionKey=steam-analytics-encryption-key-32-chars
    volumes:
      - kibana_data:/usr/share/kibana/data
      - ./kibana/config/kibana.yml:/usr/share/kibana/config/kibana.yml:ro
      - ./kibana/dashboards:/usr/share/kibana/config/dashboards:ro
    ports:
      - "5601:5601"
    networks:
      - steam-analytics
    depends_on:
      elasticsearch:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:5601/api/status || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 10
      start_period: 60s

  # Optional: Elasticsearch Head Plugin für Browser-basierte Administration
  elasticsearch-head:
    image: mobz/elasticsearch-head:5
    container_name: steam-elasticsearch-head
    ports:
      - "9100:9100"
    networks:
      - steam-analytics
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
    driver: local
  kibana_data:
    driver: local

networks:
  steam-analytics:
    driver: bridge
"""
        
        with open(self.docker_compose_file, 'w', encoding='utf-8') as f:
            f.write(docker_compose_content)
        
        logger.info(f"✅ Docker Compose erstellt: {self.docker_compose_file}")
        return True
    
    def create_kibana_dashboards(self):
        """Erstellt Kibana Dashboard-Konfigurationen"""
        logger.info("📊 Erstelle Kibana Dashboard-Konfigurationen...")
        
        # Index Patterns
        index_patterns = {
            "steam-price-snapshots": {
                "title": "steam-price-snapshots*",
                "timeFieldName": "timestamp",
                "fields": "[{\"name\":\"@timestamp\",\"type\":\"date\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"steam_app_id\",\"type\":\"string\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"game_title\",\"type\":\"string\",\"searchable\":true,\"aggregatable\":false},{\"name\":\"game_title.keyword\",\"type\":\"string\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"timestamp\",\"type\":\"date\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"best_price\",\"type\":\"number\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"best_store\",\"type\":\"string\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"max_discount\",\"type\":\"number\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"available_stores_count\",\"type\":\"number\",\"searchable\":true,\"aggregatable\":true}]"
            },
            "steam-tracked-apps": {
                "title": "steam-tracked-apps*",
                "timeFieldName": "added_at",
                "fields": "[{\"name\":\"steam_app_id\",\"type\":\"string\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"name\",\"type\":\"string\",\"searchable\":true,\"aggregatable\":false},{\"name\":\"name.keyword\",\"type\":\"string\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"added_at\",\"type\":\"date\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"last_price_update\",\"type\":\"date\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"active\",\"type\":\"boolean\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"days_tracked\",\"type\":\"number\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"has_generic_name\",\"type\":\"boolean\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"price_update_frequency\",\"type\":\"string\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"total_snapshots\",\"type\":\"number\",\"searchable\":true,\"aggregatable\":true}]"
            },
            "steam-charts-tracking": {
                "title": "steam-charts-tracking*",
                "timeFieldName": "first_seen",
                "fields": "[{\"name\":\"steam_app_id\",\"type\":\"string\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"name\",\"type\":\"string\",\"searchable\":true,\"aggregatable\":false},{\"name\":\"name.keyword\",\"type\":\"string\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"chart_type\",\"type\":\"string\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"current_rank\",\"type\":\"number\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"best_rank\",\"type\":\"number\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"first_seen\",\"type\":\"date\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"last_seen\",\"type\":\"date\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"days_in_charts\",\"type\":\"number\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"rank_trend\",\"type\":\"string\",\"searchable\":true,\"aggregatable\":true},{\"name\":\"popularity_score\",\"type\":\"number\",\"searchable\":true,\"aggregatable\":true}]"
            }
        }
        
        # Index Patterns als JSON speichern
        for pattern_name, pattern_config in index_patterns.items():
            pattern_file = self.kibana_dir / "dashboards" / f"{pattern_name}-index-pattern.json"
            with open(pattern_file, 'w', encoding='utf-8') as f:
                json.dump(pattern_config, f, indent=2)
            logger.info(f"✅ Index Pattern erstellt: {pattern_file}")
        
        # README für Dashboard-Setup
        readme_content = """# Kibana Dashboard Setup für Steam Price Tracker

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
"""
        
        readme_file = self.kibana_dir / "dashboards" / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        logger.info(f"✅ Dashboard README erstellt: {readme_file}")
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
            print(f"📊 Elasticsearch URL: {result['elasticsearch_url']}")
            print(f"🔍 Kibana URL: http://{args.host}:5601")
            print(f"📈 Exportierte Dokumente: {result['export_stats']['total_exported']}")
            
            # Index-Statistiken
            print("\\n📋 Index-Statistiken:")
            for index_name, stats in result['index_stats'].items():
                print(f"   • {index_name}: {stats['document_count']} Dokumente")
        else:
            print(f"❌ Setup fehlgeschlagen: {result['error']}")
            
    except ImportError as e:
        print(f"❌ Import-Fehler: {e}")
        print("💡 Installiere Elasticsearch: pip install elasticsearch")
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
        
        # Ausführbar machen (Unix/Linux)
        try:
            os.chmod(cli_file, 0o755)
        except:
            pass
        
        logger.info(f"✅ Elasticsearch CLI erstellt: {cli_file}")
        return True
    
    def create_requirements_file(self):
        """Erstellt/erweitert requirements.txt für Elasticsearch"""
        logger.info("📦 Erstelle/erweitere requirements.txt...")
        
        elasticsearch_requirements = """
# Elasticsearch und Analytics
elasticsearch>=8.11.0
elasticsearch-dsl>=8.11.0

# Optional: Elasticsearch Helpers
elasticsearch-curator>=5.8.4

# Optional: Pandas für erweiterte Datenanalyse
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
seaborn>=0.12.0
"""
        
        requirements_file = self.project_root / "requirements-elasticsearch.txt"
        with open(requirements_file, 'w', encoding='utf-8') as f:
            f.write(elasticsearch_requirements.strip())
        
        logger.info(f"✅ Elasticsearch Requirements erstellt: {requirements_file}")
        
        # Auch zur Haupt-requirements.txt hinzufügen falls sie existiert
        main_requirements = self.project_root / "requirements.txt"
        if main_requirements.exists():
            with open(main_requirements, 'a', encoding='utf-8') as f:
                f.write(f"\n# Elasticsearch Integration (siehe auch requirements-elasticsearch.txt)")
                f.write(f"\nelasticsearch>=8.11.0")
            logger.info("✅ Elasticsearch zu main requirements.txt hinzugefügt")
        
        return True
    
    def check_docker_availability(self):
        """Prüft ob Docker verfügbar ist"""
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Docker verfügbar: {result.stdout.strip()}")
                return True
            else:
                logger.warning("⚠️ Docker nicht verfügbar")
                return False
        except FileNotFoundError:
            logger.warning("⚠️ Docker nicht installiert")
            return False
    
    def check_docker_compose_availability(self):
        """Prüft ob Docker Compose verfügbar ist"""
        try:
            # Versuche docker compose (neue Version)
            result = subprocess.run(['docker', 'compose', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Docker Compose verfügbar: {result.stdout.strip()}")
                return 'docker compose'
            
            # Fallback auf docker-compose (alte Version)
            result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Docker Compose verfügbar: {result.stdout.strip()}")
                return 'docker-compose'
            
            logger.warning("⚠️ Docker Compose nicht verfügbar")
            return None
            
        except FileNotFoundError:
            logger.warning("⚠️ Docker Compose nicht installiert")
            return None
    
    def start_elasticsearch_stack(self, detached=True):
        """Startet Elasticsearch/Kibana Stack mit Docker Compose"""
        compose_cmd = self.check_docker_compose_availability()
        if not compose_cmd:
            logger.error("❌ Docker Compose nicht verfügbar")
            return False
        
        logger.info("🚀 Starte Elasticsearch/Kibana Stack...")
        
        cmd = compose_cmd.split() + ['-f', str(self.docker_compose_file), 'up']
        if detached:
            cmd.append('-d')
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root)
            
            if result.returncode == 0:
                logger.info("✅ Elasticsearch/Kibana Stack gestartet")
                
                if detached:
                    logger.info("⏳ Warte auf Dienste...")
                    time.sleep(30)  # Warte bis Services bereit sind
                    
                    logger.info("🔗 URLs:")
                    logger.info("   📊 Elasticsearch: http://localhost:9200")
                    logger.info("   🔍 Kibana: http://localhost:5601")
                    logger.info("   🌐 Elasticsearch Head: http://localhost:9100")
                
                return True
            else:
                logger.error("❌ Fehler beim Starten des Stacks")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten: {e}")
            return False
    
    def stop_elasticsearch_stack(self):
        """Stoppt Elasticsearch/Kibana Stack"""
        compose_cmd = self.check_docker_compose_availability()
        if not compose_cmd:
            logger.error("❌ Docker Compose nicht verfügbar")
            return False
        
        logger.info("⏹️ Stoppe Elasticsearch/Kibana Stack...")
        
        cmd = compose_cmd.split() + ['-f', str(self.docker_compose_file), 'down']
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root)
            
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
            logger.info("4. Öffne Kibana für Datenanalyse:")
            logger.info("   http://localhost:5601")
        else:
            logger.warning("\n⚠️ Docker/Docker Compose nicht verfügbar")
            logger.info("Installiere Docker und Docker Compose für automatisches Setup")
        
        return success_count == len(steps)


def main():
    parser = argparse.ArgumentParser(
        description="Elasticsearch Setup für Steam Price Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s setup                    # Komplettes Setup durchführen
  %(prog)s start                    # Elasticsearch/Kibana Stack starten
  %(prog)s stop                     # Stack stoppen
  %(prog)s install-requirements     # Python Requirements installieren
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Kommandos')
    
    # Setup Command
    setup_parser = subparsers.add_parser('setup', help='Komplettes Setup durchführen')
    
    # Start Command
    start_parser = subparsers.add_parser('start', help='Elasticsearch/Kibana Stack starten')
    start_parser.add_argument('--foreground', action='store_true', help='Im Vordergrund ausführen')
    
    # Stop Command
    stop_parser = subparsers.add_parser('stop', help='Stack stoppen')
    
    # Install Requirements Command
    install_parser = subparsers.add_parser('install-requirements', help='Python Requirements installieren')
    
    args = parser.parse_args()
    
    setup_manager = ElasticsearchSetup()
    
    try:
        if args.command == 'setup':
            setup_manager.full_setup()
            
        elif args.command == 'start':
            if not setup_manager.docker_compose_file.exists():
                logger.error("❌ Docker Compose Datei nicht gefunden. Führe zuerst 'setup' aus.")
                return
            
            setup_manager.start_elasticsearch_stack(detached=not args.foreground)
            
        elif args.command == 'stop':
            setup_manager.stop_elasticsearch_stack()
            
        elif args.command == 'install-requirements':
            requirements_file = Path("requirements-elasticsearch.txt")
            if requirements_file.exists():
                logger.info("📦 Installiere Elasticsearch Requirements...")
                result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)])
                if result.returncode == 0:
                    logger.info("✅ Requirements erfolgreich installiert")
                else:
                    logger.error("❌ Installation fehlgeschlagen")
            else:
                logger.error("❌ requirements-elasticsearch.txt nicht gefunden")
                
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        logger.info("\n⏹️ Setup abgebrochen durch Benutzer")
    except Exception as e:
        logger.error(f"❌ Unerwarteter Fehler: {e}")

if __name__ == "__main__":
    main()