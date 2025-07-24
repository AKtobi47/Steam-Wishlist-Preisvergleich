#!/usr/bin/env python3
"""
Kibana Dashboard Setup für Steam Price Tracker
Erstellt automatisch Dashboards durch NDJSON-Import
"""

import json
import requests
import time
import sys
from pathlib import Path
import logging
import docker

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
        logger.info(" Warte auf Kibana...")
        
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
        
        logger.error(" Kibana nicht verfügbar nach maximaler Wartezeit")
        return False
    
    def import_ndjson_to_kibana(self, ndjson_path):
        """Importiert NDJSON-Datei nach Kibana"""
        logger.info(f" Importiere NDJSON-Datei: {ndjson_path}")
        
        if not Path(ndjson_path).exists():
            logger.error(f" NDJSON-Datei nicht gefunden: {ndjson_path}")
            return False
        
        try:
            with open(ndjson_path, 'rb') as f:
                files = {'file': (ndjson_path, f, 'application/ndjson')}
                headers = {'kbn-xsrf': 'true'}
                response = requests.post(
                    f"{self.kibana_url}/api/saved_objects/_import?overwrite=true",
                    headers=headers,
                    files=files
                )
            
            if response.status_code == 200:
                result = response.json()
                success_count = result.get('successCount', 0)
                logger.info(f" NDJSON erfolgreich importiert! {success_count} Objekte importiert")
                
                # Zeige Details zu importierten Objekten
                if 'successResults' in result:
                    for obj in result['successResults']:
                        obj_type = obj.get('type', 'unknown')
                        obj_title = obj.get('meta', {}).get('title', 'unnamed')
                        logger.info(f"  ✓ {obj_type}: {obj_title}")
                
                return True
            else:
                logger.error(f" Fehler beim Import: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f" Import-Fehler: {e}")
            return False
    
    def refresh_index_patterns(self):
        """Aktualisiert alle Index Patterns"""
        logger.info(" Aktualisiere Index Patterns...")
        
        try:
            # Hole alle Index Patterns
            response = requests.get(
                f"{self.kibana_url}/api/saved_objects/_find?type=index-pattern",
                headers=self.headers
            )
            
            if response.status_code == 200:
                index_patterns = response.json().get('saved_objects', [])
                
                for pattern in index_patterns:
                    pattern_id = pattern['id']
                    pattern_title = pattern['attributes'].get('title', 'unknown')
                    
                    # Refresh das Pattern
                    refresh_response = requests.post(
                        f"{self.kibana_url}/api/index_patterns/index_pattern/{pattern_id}/refresh_fields",
                        headers=self.headers
                    )
                    
                    if refresh_response.status_code == 200:
                        logger.info(f"  ✓ Index Pattern '{pattern_title}' aktualisiert")
                    else:
                        logger.warning(f"   Fehler beim Aktualisieren von '{pattern_title}'")
                
                return True
            else:
                logger.error(f" Fehler beim Abrufen der Index Patterns: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f" Fehler beim Aktualisieren der Index Patterns: {e}")
            return False
    
    def list_dashboards(self):
        """Listet alle verfügbaren Dashboards auf"""
        logger.info(" Verfügbare Dashboards:")
        
        try:
            response = requests.get(
                f"{self.kibana_url}/api/saved_objects/_find?type=dashboard",
                headers=self.headers
            )
            
            if response.status_code == 200:
                dashboards = response.json().get('saved_objects', [])
                
                if not dashboards:
                    logger.info("  Keine Dashboards gefunden")
                    return
                
                for dashboard in dashboards:
                    title = dashboard['attributes'].get('title', 'Untitled')
                    dashboard_id = dashboard['id']
                    logger.info(f"   {title} (ID: {dashboard_id})")
                    logger.info(f"     URL: {self.kibana_url}/app/dashboards#/view/{dashboard_id}")
                
            else:
                logger.error(f" Fehler beim Abrufen der Dashboards: {response.text}")
                
        except Exception as e:
            logger.error(f" Fehler beim Auflisten der Dashboards: {e}")
    
    def export_dashboards(self, output_dir="kibana/dashboards"):
        """Exportiert alle Dashboards als JSON"""
        logger.info(" Exportiere Dashboards...")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Hole alle Dashboards
            response = requests.get(
                f"{self.kibana_url}/api/saved_objects/_find?type=dashboard",
                headers=self.headers
            )
            
            if response.status_code == 200:
                dashboards = response.json().get('saved_objects', [])
                
                for dashboard in dashboards:
                    dashboard_id = dashboard['id']
                    title = dashboard['attributes'].get('title', 'Untitled')
                    
                    # Exportiere Dashboard
                    export_response = requests.get(
                        f"{self.kibana_url}/api/saved_objects/dashboard/{dashboard_id}",
                        headers=self.headers
                    )
                    
                    if export_response.status_code == 200:
                        dashboard_data = export_response.json()
                        
                        # Sichere Dateinamen erstellen
                        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        export_file = output_path / f"{safe_title}_{dashboard_id}.json"
                        
                        with open(export_file, 'w', encoding='utf-8') as f:
                            json.dump(dashboard_data, f, indent=2)
                        
                        logger.info(f" Dashboard exportiert: {export_file}")
                    else:
                        logger.error(f" Fehler beim Exportieren von '{title}': {export_response.text}")
                
            else:
                logger.error(f" Fehler beim Abrufen der Dashboards: {response.text}")
                
        except Exception as e:
            logger.error(f" Export-Fehler: {e}")

def start_kibana_container(container_name='kibana-steam-tracker', elasticsearch_url='http://host.docker.internal:9200', kibana_port=5601):
    """Startet Kibana Docker Container"""
    client = docker.from_env()
    try:
        container = client.containers.get(container_name)
        if container.status != 'running':
            container.start()
            logger.info(f"Kibana-Container '{container_name}' gestartet.")
        else:
            logger.info(f"Kibana-Container '{container_name}' läuft bereits.")
        logger.info(f" Kibana Dashboard erreichbar unter: http://localhost:{kibana_port}")
    except docker.errors.NotFound:
        logger.info(f"Erstelle und starte Kibana-Container '{container_name}'...")
        client.containers.run(
            "docker.elastic.co/kibana/kibana:8.11.0",
            name=container_name,
            ports={f"{kibana_port}/tcp": kibana_port},
            environment={
                "ELASTICSEARCH_HOSTS": elasticsearch_url,
                "SERVER_PUBLICBASEURL": f"http://localhost:{kibana_port}",
                "XPACK_SECURITY_ENABLED": "false"
            },
            detach=True,
            remove=False
        )
        logger.info(f"Kibana-Container '{container_name}' wurde erstellt und gestartet.")
        logger.info(f" Kibana Dashboard erreichbar unter: http://localhost:{kibana_port}")

def main():
    """Hauptfunktion"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Kibana Dashboard Setup für Steam Price Tracker")
    parser.add_argument('--kibana-url', default='http://localhost:5601', 
                       help='Kibana URL (Standard: http://localhost:5601)')
    parser.add_argument('--ndjson', required=True,
                       help='Pfad zur NDJSON-Datei für Dashboard-Import')
    parser.add_argument('--export', action='store_true',
                       help='Exportiere Dashboards nach Setup')
    parser.add_argument('--list', action='store_true',
                       help='Liste alle verfügbaren Dashboards auf')
    parser.add_argument('--refresh-patterns', action='store_true',
                       help='Aktualisiere Index Patterns nach Import')
    
    args = parser.parse_args()
    
    # 1. Kibana-Container starten
    start_kibana_container()
    
    setup = KibanaDashboardSetup(args.kibana_url)
    
    try:
        # 2. Immer auf Kibana warten
        print("Warte auf Kibana, bis es bereit ist...")
        if not setup.wait_for_kibana():
            logger.error(" Kibana nicht verfügbar - Setup abgebrochen")
            sys.exit(1)
        
        # 3. NDJSON importieren
        if not setup.import_ndjson_to_kibana(args.ndjson):
            logger.error(" NDJSON-Import fehlgeschlagen")
            sys.exit(1)
        
        # 4. Index Patterns aktualisieren
        if args.refresh_patterns:
            setup.refresh_index_patterns()
        
        # 5. Dashboards auflisten
        if args.list:
            setup.list_dashboards()
        
        # 6. Export falls gewünscht
        if args.export:
            setup.export_dashboards()
        
        logger.info(" Setup erfolgreich abgeschlossen!")
        logger.info(f" Kibana Dashboard: {args.kibana_url}/app/dashboards")
        
    except KeyboardInterrupt:
        logger.info("\n Setup abgebrochen durch Benutzer")
        sys.exit(1)
    except Exception as e:
        logger.error(f" Unerwarteter Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()