#!/usr/bin/env python3
"""
Elasticsearch Manager für Steam Price Tracker
Verwaltet Elasticsearch-Verbindungen und Datenoperationen
Unterstützt Docker-Container für Elasticsearch
"""

try:
    from elasticsearch import Elasticsearch
    from elasticsearch.exceptions import ConnectionError, NotFoundError
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

import json
import argparse
import sys
import time
import subprocess
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from database_manager import DatabaseManager

class DockerElasticsearchManager:
    """Manager für Elasticsearch Docker-Container"""
    
    def __init__(self, container_name='elasticsearch-steam-tracker'):
        if not DOCKER_AVAILABLE:
            raise ImportError("Docker Python-Client nicht installiert. Installiere mit: pip install docker")
        
        self.container_name = container_name
        self.client = docker.from_env()
        self.elasticsearch_image = "docker.elastic.co/elasticsearch/elasticsearch:8.11.0"
        self.container_port = 9200
        self.host_port = 9200
    
    def is_container_running(self) -> bool:
        """Prüft ob der Elasticsearch-Container läuft"""
        try:
            container = self.client.containers.get(self.container_name)
            return container.status == 'running'
        except docker.errors.NotFound:
            return False
        except Exception:
            return False
    
    def start_container(self, memory_limit='1g', heap_size='512m') -> Dict[str, Any]:
        """Startet Elasticsearch Docker-Container"""
        try:
            # Prüfen ob Container bereits existiert
            try:
                container = self.client.containers.get(self.container_name)
                if container.status == 'running':
                    return {
                        'success': True,
                        'message': 'Container läuft bereits',
                        'container_id': container.id
                    }
                elif container.status == 'exited':
                    container.start()
                    return {
                        'success': True,
                        'message': 'Existierender Container gestartet',
                        'container_id': container.id
                    }
            except docker.errors.NotFound:
                pass
            
            # Container-Konfiguration
            environment = {
                'discovery.type': 'single-node',
                'xpack.security.enabled': 'false',
                'xpack.security.enrollment.enabled': 'false',
                'xpack.security.http.ssl.enabled': 'false',
                'xpack.security.transport.ssl.enabled': 'false',
                'ES_JAVA_OPTS': f'-Xms{heap_size} -Xmx{heap_size}'
            }
            
            ports = {f'{self.container_port}/tcp': self.host_port}
            
            # Container erstellen und starten
            container = self.client.containers.run(
                self.elasticsearch_image,
                name=self.container_name,
                ports=ports,
                environment=environment,
                mem_limit=memory_limit,
                detach=True,
                remove=False
            )
            
            # Warten bis Elasticsearch bereit ist
            print("⏳ Warte auf Elasticsearch-Start...")
            max_wait = 60  # Maximal 60 Sekunden warten
            wait_time = 0
            
            while wait_time < max_wait:
                try:
                    # Kurze Pause
                    time.sleep(2)
                    wait_time += 2
                    
                    # Gesundheitscheck
                    es = Elasticsearch(
                        hosts=[f"http://localhost:{self.host_port}"],
                        verify_certs=False,
                        request_timeout=5
                    )
                    
                    # Einfacher Ping-Test
                    if es.ping():
                        return {
                            'success': True,
                            'message': f'Container erfolgreich gestartet (nach {wait_time}s)',
                            'container_id': container.id
                        }
                        
                except Exception:
                    continue
            
            return {
                'success': False,
                'message': f'Container gestartet, aber Elasticsearch nicht bereit nach {max_wait}s'
            }
            
        except docker.errors.ImageNotFound:
            return {
                'success': False,
                'message': f'Elasticsearch Image nicht gefunden: {self.elasticsearch_image}'
            }
        except docker.errors.APIError as e:
            return {
                'success': False,
                'message': f'Docker API Fehler: {e}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Unerwarteter Fehler: {e}'
            }
    
    def stop_container(self) -> Dict[str, Any]:
        """Stoppt Elasticsearch Docker-Container"""
        try:
            container = self.client.containers.get(self.container_name)
            container.stop()
            return {
                'success': True,
                'message': 'Container gestoppt'
            }
        except docker.errors.NotFound:
            return {
                'success': False,
                'message': 'Container nicht gefunden'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Fehler beim Stoppen: {e}'
            }
    
    def remove_container(self) -> Dict[str, Any]:
        """Entfernt Elasticsearch Docker-Container"""
        try:
            container = self.client.containers.get(self.container_name)
            if container.status == 'running':
                container.stop()
            container.remove()
            return {
                'success': True,
                'message': 'Container entfernt'
            }
        except docker.errors.NotFound:
            return {
                'success': False,
                'message': 'Container nicht gefunden'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Fehler beim Entfernen: {e}'
            }
    
    def get_container_logs(self, tail=50) -> str:
        """Holt Container-Logs"""
        try:
            container = self.client.containers.get(self.container_name)
            logs = container.logs(tail=tail, timestamps=True)
            return logs.decode('utf-8')
        except docker.errors.NotFound:
            return "Container nicht gefunden"
        except Exception as e:
            return f"Fehler beim Abrufen der Logs: {e}"
    
    def get_container_status(self) -> Dict[str, Any]:
        """Holt Container-Status"""
        try:
            container = self.client.containers.get(self.container_name)
            return {
                'exists': True,
                'status': container.status,
                'image': container.image.tags[0] if container.image.tags else 'unknown',
                'created': container.attrs['Created'],
                'ports': container.attrs['NetworkSettings']['Ports']
            }
        except docker.errors.NotFound:
            return {
                'exists': False,
                'status': 'not_found'
            }
        except Exception as e:
            return {
                'exists': False,
                'status': 'error',
                'error': str(e)
            }


class ElasticsearchManager:
    """Manager für Elasticsearch-Operationen"""
    
    def __init__(self, host='localhost', port=9200, username=None, password=None):
        if not ELASTICSEARCH_AVAILABLE:
            raise ImportError("Elasticsearch nicht installiert. Installiere mit: pip install elasticsearch")
        
        self.host = host
        self.port = port
        
        # Elasticsearch-Client konfigurieren
        try:
            # Moderne Elasticsearch-Client-Konfiguration
            if username and password:
                self.es = Elasticsearch(
                    hosts=[f"http://{host}:{port}"],
                    basic_auth=(username, password),
                    verify_certs=False,
                    ssl_show_warn=False
                )
            else:
                self.es = Elasticsearch(
                    hosts=[f"http://{host}:{port}"],
                    verify_certs=False,
                    ssl_show_warn=False
                )
        except Exception as e:
            # Fallback für ältere Versionen
            print(f"⚠️  Versuche Fallback-Konfiguration...")
            try:
                if username and password:
                    self.es = Elasticsearch(
                        [{'host': host, 'port': port, 'scheme': 'http'}],
                        http_auth=(username, password),
                        verify_certs=False
                    )
                else:
                    self.es = Elasticsearch(
                        [{'host': host, 'port': port, 'scheme': 'http'}],
                        verify_certs=False
                    )
            except Exception as e2:
                raise Exception(f"Elasticsearch-Client-Konfiguration fehlgeschlagen: {e2}")
        
        # Index-Namen definieren
        self.indices = {
            'price_snapshots': 'steam-price-snapshots',
            'tracked_apps': 'steam-tracked-apps',
            'name_history': 'steam-name-history',
            'charts_snapshots': 'steam-charts-snapshots',
            'charts_prices': 'steam-charts-prices',
            'statistics': 'steam-statistics',
            'tracked_apps_price_history': 'steam-tracked-apps-price-history',
            'tracked_apps_latest_prices': 'steam-tracked-apps-latest-prices'
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Elasticsearch-Gesundheitscheck"""
        try:
            # Cluster-Info
            cluster_info = self.es.info()
            cluster_health = self.es.cluster.health()
            
            # Index-Statistiken
            indices_stats = {}
            for key, index_name in self.indices.items():
                try:
                    exists = self.es.indices.exists(index=index_name)
                    if exists:
                        count = self.es.count(index=index_name)
                        indices_stats[key] = {
                            'index_name': index_name,
                            'exists': True,
                            'document_count': count['count']
                        }
                    else:
                        indices_stats[key] = {
                            'index_name': index_name,
                            'exists': False,
                            'document_count': 0
                        }
                except Exception as e:
                    indices_stats[key] = {
                        'index_name': index_name,
                        'exists': False,
                        'error': str(e)
                    }
            
            # Gesamtdokumente zählen
            total_docs = sum(stats.get('document_count', 0) for stats in indices_stats.values())
            
            return {
                'connection_ok': True,
                'cluster_name': cluster_info['cluster_name'],
                'cluster_status': cluster_health['status'],
                'number_of_nodes': cluster_health['number_of_nodes'],
                'active_shards': cluster_health['active_shards'],
                'total_documents': total_docs,
                'indices': indices_stats
            }
            
        except ConnectionError as e:
            return {
                'connection_ok': False,
                'error': f"Verbindung fehlgeschlagen: {e}"
            }
        except Exception as e:
            return {
                'connection_ok': False,
                'error': f"Unerwarteter Fehler: {e}"
            }
    
    def create_indices_and_mappings(self) -> int:
        """Erstellt alle Indizes mit Mappings"""
        created_count = 0
        
        # Mappings definieren
        mappings = {
            'price_snapshots': {
                'properties': {
                    'id': {'type': 'long'},
                    'steam_app_id': {'type': 'keyword'},
                    'game_title': {
                        'type': 'text',
                        "fields": {
                            "keyword": {
                                "type": "keyword"                            }
                        }
                    },
                    'timestamp': {'type': 'date'},
                    'steam_price': {'type': 'float'},
                    'steam_original_price': {'type': 'float'},
                    'steam_discount_percent': {'type': 'integer'},
                    'steam_available': {'type': 'boolean'},
                    'greenmangaming_price': {'type': 'float'},
                    'greenmangaming_original_price': {'type': 'float'},
                    'greenmangaming_discount_percent': {'type': 'integer'},
                    'greenmangaming_available': {'type': 'boolean'},
                    'gog_price': {'type': 'float'},
                    'gog_original_price': {'type': 'float'},
                    'gog_discount_percent': {'type': 'integer'},
                    'gog_available': {'type': 'boolean'},
                    'humblestore_price': {'type': 'float'},
                    'humblestore_original_price': {'type': 'float'},
                    'humblestore_discount_percent': {'type': 'integer'},
                    'humblestore_available': {'type': 'boolean'},
                    'fanatical_price': {'type': 'float'},
                    'fanatical_original_price': {'type': 'float'},
                    'fanatical_discount_percent': {'type': 'integer'},
                    'fanatical_available': {'type': 'boolean'},
                    'gamesplanet_price': {'type': 'float'},
                    'gamesplanet_original_price': {'type': 'float'},
                    'gamesplanet_discount_percent': {'type': 'integer'},
                    'gamesplanet_available': {'type': 'boolean'}
                }
            },
            'tracked_apps': {
                'properties': {
                    'steam_app_id': {'type': 'keyword'},
                    'game_title': {'type': 'text', 'analyzer': 'standard'},
                    'first_tracked': {'type': 'date'},
                    'last_updated': {'type': 'date'}
                }
            },
            'name_history': {
                'properties': {
                    'steam_app_id': {'type': 'keyword'},
                    'old_name': {'type': 'text', 'analyzer': 'standard'},
                    'new_name': {'type': 'text', 'analyzer': 'standard'},
                    'change_date': {'type': 'date'}
                }
            },
            'charts_snapshots': {
                'properties': {
                    'id': {'type': 'long'},
                    'steam_app_id': {'type': 'keyword'},
                    'game_title': {'type': 'text', 'analyzer': 'standard'},
                    'timestamp': {'type': 'date'},
                    'steam_price': {'type': 'float'},
                    'steam_original_price': {'type': 'float'},
                    'steam_discount_percent': {'type': 'integer'},
                    'steam_available': {'type': 'boolean'},
                    'greenmangaming_price': {'type': 'float'},
                    'greenmangaming_original_price': {'type': 'float'},
                    'greenmangaming_discount_percent': {'type': 'integer'},
                    'greenmangaming_available': {'type': 'boolean'},
                    'gog_price': {'type': 'float'},
                    'gog_original_price': {'type': 'float'},
                    'gog_discount_percent': {'type': 'integer'},
                    'gog_available': {'type': 'boolean'},
                    'humblestore_price': {'type': 'float'},
                    'humblestore_original_price': {'type': 'float'},
                    'humblestore_discount_percent': {'type': 'integer'},
                    'humblestore_available': {'type': 'boolean'},
                    'fanatical_price': {'type': 'float'},
                    'fanatical_original_price': {'type': 'float'},
                    'fanatical_discount_percent': {'type': 'integer'},
                    'fanatical_available': {'type': 'boolean'},
                    'gamesplanet_price': {'type': 'float'},
                    'gamesplanet_original_price': {'type': 'float'},
                    'gamesplanet_discount_percent': {'type': 'integer'},
                    'gamesplanet_available': {'type': 'boolean'},
                    'is_chart_game': {'type': 'boolean'},
                    'chart_types': {'type': 'keyword'}
                }
            },
            'charts_prices': {
                'properties': {
                    'steam_app_id': {'type': 'keyword'},
                    'game_title': {'type': 'text', 'analyzer': 'standard'},
                    'timestamp': {'type': 'date'},
                    'steam_price': {'type': 'float'},
                    'steam_original_price': {'type': 'float'},
                    'steam_discount_percent': {'type': 'integer'},
                    'is_chart_game': {'type': 'boolean'},
                    'chart_types': {'type': 'keyword'}
                }
            },
            'statistics': {
                'properties': {
                    'metric_name': {'type': 'keyword'},
                    'value': {'type': 'float'},
                    'timestamp': {'type': 'date'},
                    'steam_app_id': {'type': 'keyword'},
                    'category': {'type': 'keyword'}
                }
            },
            'tracked_apps_price_history': {
                'properties': {
                    'steam_app_id':         {'type': 'keyword'},
                    "name": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256
                        }
                        }
                    },
                    'target_price':         {'type': 'float'},
                    'timestamp':            {'type': 'date'},
                    'steam_price':          {'type': 'float'},
                    'greenmangaming_price': {'type': 'float'},
                    'gog_price':            {'type': 'float'},
                    'humblestore_price':    {'type': 'float'},
                    'fanatical_price':      {'type': 'float'},
                    'gamesplanet_price':    {'type': 'float'}
                }
            },
            'tracked_apps_latest_prices': {
                'properties': {
                    'steam_app_id': {'type': 'keyword'},
                    "name": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256
                        }
                        }
                    },
                    'app_active': {'type': 'boolean'},
                    'target_price': {'type': 'float'},
                    'app_source': {'type': 'keyword'},
                    'notes': {'type': 'text', 'analyzer': 'standard'},
                    'game_title': {'type': 'text', 'analyzer': 'standard'},
                    'price_timestamp': {'type': 'date'},
                    'steam_price': {'type': 'float'},
                    'steam_original_price': {'type': 'float'},
                    'steam_discount_percent': {'type': 'integer'},
                    'steam_available': {'type': 'boolean'},
                    'greenmangaming_price': {'type': 'float'},
                    'greenmangaming_original_price': {'type': 'float'},
                    'greenmangaming_discount_percent': {'type': 'integer'},
                    'greenmangaming_available': {'type': 'boolean'},
                    'gog_price': {'type': 'float'},
                    'gog_original_price': {'type': 'float'},
                    'gog_discount_percent': {'type': 'integer'},
                    'gog_available': {'type': 'boolean'},
                    'humblestore_price': {'type': 'float'},
                    'humblestore_original_price': {'type': 'float'},
                    'humblestore_discount_percent': {'type': 'integer'},
                    'humblestore_available': {'type': 'boolean'},
                    'fanatical_price': {'type': 'float'},
                    'fanatical_original_price': {'type': 'float'},
                    'fanatical_discount_percent': {'type': 'integer'},
                    'fanatical_available': {'type': 'boolean'},
                    'gamesplanet_price': {'type': 'float'},
                    'gamesplanet_original_price': {'type': 'float'},
                    'gamesplanet_discount_percent': {'type': 'integer'},
                    'gamesplanet_available': {'type': 'boolean'}
                }
            }
        }
        
        # Indizes erstellen
        for key, index_name in self.indices.items():
            try:
                if not self.es.indices.exists(index=index_name):
                    # Moderne API für neuere Elasticsearch-Versionen
                    try:
                        self.es.indices.create(
                            index=index_name,
                            mappings=mappings[key]
                        )
                    except Exception:
                        # Fallback für ältere Versionen
                        self.es.indices.create(
                            index=index_name,
                            body={'mappings': mappings[key]}
                        )
                    created_count += 1
                    print(f" Index erstellt: {index_name}")
                else:
                    print(f"ℹ Index existiert bereits: {index_name}")
            except Exception as e:
                print(f" Fehler beim Erstellen von {index_name}: {e}")
        
        return created_count
    
    def delete_all_indices(self) -> int:
        """Löscht alle Steam Price Tracker Indizes"""
        deleted_count = 0
        
        for key, index_name in self.indices.items():
            try:
                if self.es.indices.exists(index=index_name):
                    self.es.indices.delete(index=index_name)
                    deleted_count += 1
                    print(f" Index gelöscht: {index_name}")
            except Exception as e:
                print(f" Fehler beim Löschen von {index_name}: {e}")
        
        return deleted_count
    
    def export_sqlite_to_elasticsearch(self, db_manager) -> Dict[str, int]:
        """Exportiert Daten aus SQLite zu Elasticsearch mit Bulk-API"""
        stats = {
            'price_snapshots': 0,
            'tracked_apps': 0,
            'name_history': 0,
            'charts_snapshots': 0,
            'charts_prices': 0,
            'statistics': 0,
            'tracked_apps_price_history': 0,
            'tracked_apps_latest_prices': 0,
            'total_exported': 0
        }
        
        def prepare_record_for_elasticsearch(record):
            """Bereitet einen Datensatz für Elasticsearch vor"""
            # Timestamp-Felder ins ISO8601-Format bringen
            for field in ['timestamp', 'first_tracked', 'last_updated', 'change_date']:
                if field in record and isinstance(record[field], str):
                    if ' ' in record[field] and 'T' not in record[field]:
                        record[field] = record[field].replace(' ', 'T')
            
            # *_available Felder in Boolean umwandeln
            for key in record:
                if key.endswith('_available'):
                    if record[key] in [1, '1', True]:
                        record[key] = True
                    else:
                        record[key] = False
            
            return record
        
        def bulk_export_data(data, index_name, batch_size=10000):
            """Exportiert Daten in Batches mit Bulk-API"""
            exported_count = 0
            total_records = len(data)
            
            for i in range(0, total_records, batch_size):
                batch = data[i:i + batch_size]
                bulk_data = []
                
                for record in batch:
                    # Datensatz vorbereiten
                    prepared_record = prepare_record_for_elasticsearch(record.copy())
                    
                    # Bulk-Action hinzufügen
                    bulk_data.append({
                        'index': {
                            '_index': index_name
                        }
                    })
                    bulk_data.append(prepared_record)
                
                try:
                    # Bulk-Request senden
                    response = self.es.bulk(operations=bulk_data, refresh=False)
                    
                    # Erfolgreiche Dokumente zählen
                    if response.get('errors', False):
                        # Einige Fehler aufgetreten
                        for item in response['items']:
                            if 'index' in item and item['index'].get('status', 500) < 400:
                                exported_count += 1
                    else:
                        # Alle erfolgreich
                        exported_count += len(batch)
                    
                    # Fortschritt anzeigen
                    progress = min(100, (i + len(batch)) / total_records * 100)
                    print(f"   Fortschritt: {progress:.1f}% ({i + len(batch)}/{total_records})")
                    
                except Exception as e:
                    print(f" Fehler beim Bulk-Export: {e}")
                    # Fallback: Einzelne Datensätze versuchen
                    for record in batch:
                        try:
                            prepared_record = prepare_record_for_elasticsearch(record.copy())
                            self.es.index(index=index_name, document=prepared_record)
                            exported_count += 1
                        except Exception as e2:
                            print(f" Fehler beim Exportieren: {e2}")
            
            return exported_count
        
        try:
            # Price Snapshots exportieren
            print(" Exportiere Price Snapshots...")
            price_data = db_manager.get_all_price_snapshots()
            stats['price_snapshots'] = bulk_export_data(price_data, self.indices['price_snapshots'])
            
            # Tracked Apps exportieren
            print(" Exportiere Tracked Apps...")
            tracked_data = db_manager.get_all_tracked_apps()
            stats['tracked_apps'] = bulk_export_data(tracked_data, self.indices['tracked_apps'])
            
            # Name History exportieren
            print(" Exportiere Name History...")
            name_data = db_manager.get_all_name_history()
            stats['name_history'] = bulk_export_data(name_data, self.indices['name_history'])
            
            # Charts Snapshots exportieren
            print(" Exportiere Charts Snapshots...")
            charts_data = db_manager.get_all_charts_tracking()
            stats['charts_snapshots'] = bulk_export_data(charts_data, self.indices['charts_snapshots'])
            
            # Charts Prices exportieren
            print(" Exportiere Charts Prices...")
            charts_prices_data = db_manager.get_all_charts_prices()
            stats['charts_prices'] = bulk_export_data(charts_prices_data, self.indices['charts_prices'])
            
            # Statistics exportieren
            print(" Exportiere Statistics...")
            stats_data = db_manager.get_all_statistics()
            stats['statistics'] = bulk_export_data(stats_data, self.indices['statistics'])
            
            # Tracked Apps Price History exportieren
            print(" Exportiere Tracked Apps Price History...")
            price_history_data = db_manager.get_all_tracked_apps_price_history()
            stats['tracked_apps_price_history'] = bulk_export_data(price_history_data, self.indices['tracked_apps_price_history'])
            
            # Tracked Apps Latest Prices exportieren
            print(" Exportiere Tracked Apps Latest Prices...")
            latest_prices_data = db_manager.get_all_tracked_apps_latest_prices()
            stats['tracked_apps_latest_prices'] = bulk_export_data(latest_prices_data, self.indices['tracked_apps_latest_prices'])
            
            # Refresh alle Indizes
            print(" Refreshe Indizes...")
            for index_name in self.indices.values():
                try:
                    self.es.indices.refresh(index=index_name)
                except Exception as e:
                    print(f" Fehler beim Refreshen von {index_name}: {e}")
            
        except Exception as e:
            print(f" Export-Fehler: {e}")
        
        stats['total_exported'] = sum(v for k, v in stats.items() if k != 'total_exported')
        return stats


def create_elasticsearch_manager(host='localhost', port=9200, username=None, password=None) -> Optional[ElasticsearchManager]:
    """Factory-Funktion für ElasticsearchManager"""
    try:
        return ElasticsearchManager(host, port, username, password)
    except ImportError as e:
        print(f" Elasticsearch nicht verfügbar: {e}")
        return None
    except Exception as e:
        print(f" Fehler beim Erstellen des Elasticsearch Managers: {e}")
        return None


def create_docker_manager(container_name='elasticsearch-steam-tracker') -> Optional[DockerElasticsearchManager]:
    """Factory-Funktion für DockerElasticsearchManager"""
    try:
        return DockerElasticsearchManager(container_name)
    except ImportError as e:
        print(f" Docker nicht verfügbar: {e}")
        return None
    except Exception as e:
        print(f" Fehler beim Erstellen des Docker Managers: {e}")
        return None


def setup_elasticsearch_for_steam_tracker(db_manager, host='localhost', port=9200, username=None, password=None) -> Dict[str, Any]:
    """Vollständiges Setup für Steam Price Tracker Elasticsearch"""
    try:
        # Elasticsearch Manager erstellen
        es_manager = create_elasticsearch_manager(host, port, username, password)
        if not es_manager:
            return {'success': False, 'error': 'Elasticsearch Manager konnte nicht erstellt werden'}
        
        # Verbindung testen
        health = es_manager.health_check()
        if not health['connection_ok']:
            return {'success': False, 'error': health['error']}
        
        # Indizes und Mappings erstellen
        created_indices = es_manager.create_indices_and_mappings()
        
        return {
            'success': True,
            'indices_created': created_indices,
            'mappings_applied': created_indices
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def cmd_create_indices(args):
    """Erstellt alle Indizes"""
    print("  Erstelle Elasticsearch-Indizes...")
    
    es_manager = create_elasticsearch_manager(args.host, args.port, args.username, args.password)
    if not es_manager:
        return
    
    created_count = es_manager.create_indices_and_mappings()
    print(f" {created_count} Indizes erstellt")


def cmd_delete_indices(args):
    """Löscht alle Indizes"""
    if not args.confirm:
        print("  WARNUNG: Dies wird alle Steam Price Tracker Indizes löschen!")
        confirm = input("Fortfahren? (ja/nein): ")
        if confirm.lower() not in ['ja', 'j', 'yes', 'y']:
            print(" Abgebrochen")
            return
    
    print("  Lösche Elasticsearch-Indizes...")
    
    es_manager = create_elasticsearch_manager(args.host, args.port, args.username, args.password)
    if not es_manager:
        return
    
    deleted_count = es_manager.delete_all_indices()
    print(f" {deleted_count} Indizes gelöscht")


def cmd_export_data(args):
    """Exportiert Daten aus SQLite zu Elasticsearch"""
    print(" Exportiere Daten von SQLite zu Elasticsearch...")
    
    # Database Manager erstellen
    db_manager = DatabaseManager(args.database)
    db_info = db_manager.get_database_info()
    
    if not db_info['database_exists']:
        print(f" Datenbank nicht gefunden: {args.database}")
        return
    
    print(f" Datenbank: {args.database}")
    print(f" Gesamt-Datensätze: {db_info['total_records']}")
    
    # Elasticsearch Manager erstellen
    es_manager = create_elasticsearch_manager(args.host, args.port, args.username, args.password)
    if not es_manager:
        return
    
    # Export durchführen
    stats = es_manager.export_sqlite_to_elasticsearch(db_manager)
    
    print("\n Export-Statistiken:")
    for key, count in stats.items():
        if key != 'total_exported':
            print(f"  {key}: {count} Datensätze")
    
    print(f"\n Gesamt exportiert: {stats['total_exported']} Datensätze")


def cmd_setup(args):
    """Vollständiges Setup"""
    print(" Vollständiges Elasticsearch-Setup...")
    
    # Database Manager erstellen
    db_manager = DatabaseManager(args.database)
    
    # Setup durchführen
    result = setup_elasticsearch_for_steam_tracker(
        db_manager, args.host, args.port, args.username, args.password
    )
    
    if result['success']:
        print(f" Setup erfolgreich! {result['indices_created']} Indizes erstellt")
    else:
        print(f" Setup fehlgeschlagen: {result['error']}")


def cmd_docker_setup(args):
    """Vollständiges Docker-Setup: Container starten + Elasticsearch konfigurieren"""
    print(" Vollständiges Docker-Setup...")
    
    # Docker Manager erstellen
    docker_manager = create_docker_manager(args.container_name)
    if not docker_manager:
        return
    
    # Container starten
    print(" Starte Elasticsearch Container...")
    start_result = docker_manager.start_container(args.memory, args.heap_size)
    
    if not start_result['success']:
        print(f" Container-Start fehlgeschlagen: {start_result['message']}")
        return
    
    print(f" {start_result['message']}")
    
    # Kurz warten für vollständige Initialisierung
    print(" Warte auf vollständige Elasticsearch-Initialisierung...")
    time.sleep(5)
    
    # Database Manager erstellen
    db_manager = DatabaseManager(args.database)
    
    # Elasticsearch Setup durchführen
    result = setup_elasticsearch_for_steam_tracker(
        db_manager, args.host, args.port, args.username, args.password
    )
    
    if result['success']:
        print(f" Setup erfolgreich! {result['indices_created']} Indizes erstellt")
        print(f" Elasticsearch verfügbar unter: http://localhost:{args.port}")
    else:
        print(f" Setup fehlgeschlagen: {result['error']}")


# Docker CLI-Funktionen
def cmd_docker_start(args):
    """Startet Elasticsearch Docker-Container"""
    print(" Starte Elasticsearch Docker-Container...")
    
    docker_manager = create_docker_manager(args.container_name)
    if not docker_manager:
        return
    
    result = docker_manager.start_container(args.memory, args.heap_size)
    
    if result['success']:
        print(f" {result['message']}")
        if 'container_id' in result:
            print(f" Container ID: {result['container_id'][:12]}")
        print(f" Elasticsearch verfügbar unter: http://localhost:{docker_manager.host_port}")
    else:
        print(f" {result['message']}")


def cmd_docker_stop(args):
    """Stoppt Elasticsearch Docker-Container"""
    print(" Stoppe Elasticsearch Docker-Container...")
    
    docker_manager = create_docker_manager(args.container_name)
    if not docker_manager:
        return
    
    result = docker_manager.stop_container()
    
    if result['success']:
        print(f" {result['message']}")
    else:
        print(f" {result['message']}")


def cmd_docker_remove(args):
    """Entfernt Elasticsearch Docker-Container"""
    if not args.confirm:
        print("  WARNUNG: Dies wird den Elasticsearch-Container entfernen!")
        confirm = input("Fortfahren? (ja/nein): ")
        if confirm.lower() not in ['ja', 'j', 'yes', 'y']:
            print(" Abgebrochen")
            return
    
    print("  Entferne Elasticsearch Docker-Container...")
    
    docker_manager = create_docker_manager(args.container_name)
    if not docker_manager:
        return
    
    result = docker_manager.remove_container()
    
    if result['success']:
        print(f" {result['message']}")
    else:
        print(f" {result['message']}")


def cmd_docker_status(args):
    """Zeigt Docker-Container-Status"""
    print(" Docker-Container-Status...")
    
    docker_manager = create_docker_manager(args.container_name)
    if not docker_manager:
        return
    
    status = docker_manager.get_container_status()
    
    if status['exists']:
        print(f" Container existiert: {args.container_name}")
        print(f" Status: {status['status']}")
        print(f"  Image: {status.get('image', 'unknown')}")
        print(f" Erstellt: {status.get('created', 'unknown')}")
        if 'ports' in status:
            print(f" Ports: {status['ports']}")
    else:
        print(f" Container existiert nicht: {args.container_name}")
        if 'error' in status:
            print(f" Fehler: {status['error']}")


def cmd_docker_logs(args):
    """Zeigt Container-Logs"""
    print(f" Container-Logs ({args.tail} Zeilen)...")
    
    docker_manager = create_docker_manager(args.container_name)
    if not docker_manager:
        return
    
    logs = docker_manager.get_container_logs(args.tail)
    print(logs)


def cmd_docker_restart(args):
    """Startet Container neu"""
    print(" Starte Container neu...")
    
    docker_manager = create_docker_manager(args.container_name)
    if not docker_manager:
        return
    
    # Stoppen
    stop_result = docker_manager.stop_container()
    if stop_result['success']:
        print(" Container gestoppt")
    else:
        print(f"  {stop_result['message']}")
    
    # Starten
    time.sleep(2)
    start_result = docker_manager.start_container(args.memory, args.heap_size)
    
    if start_result['success']:
        print(f" {start_result['message']}")
    else:
        print(f" {start_result['message']}")


# Bestehende CLI-Funktionen
def cmd_health_check(args):
    """Führt einen Gesundheitscheck durch"""
    print(" Elasticsearch Gesundheitscheck...")
    
    es_manager = create_elasticsearch_manager(args.host, args.port, args.username, args.password)
    if not es_manager:
        return
    
    health = es_manager.health_check()
    
    if health['connection_ok']:
        print(" Elasticsearch-Verbindung erfolgreich!")
        print(f"  Cluster: {health['cluster_name']}")
        print(f" Status: {health['cluster_status']}")
        print(f"  Nodes: {health['number_of_nodes']}")
        print(f" Active Shards: {health['active_shards']}")
        print(f" Total Documents: {health['total_documents']}")
        
        print("\n Index-Status:")
        for key, stats in health['indices'].items():
            if stats['exists']:
                print(f"   {key}: {stats['document_count']} Dokumente")
            else:
                print(f"   {key}: Index existiert nicht")
    else:
        print(f" Verbindung fehlgeschlagen: {health['error']}")


def main():
    """Hauptfunktion mit CLI-Argument-Parsing"""
    parser = argparse.ArgumentParser(description='Elasticsearch Manager für Steam Price Tracker')
    
    # Globale Argumente
    parser.add_argument('--host', default='localhost', help='Elasticsearch Host (default: localhost)')
    parser.add_argument('--port', type=int, default=9200, help='Elasticsearch Port (default: 9200)')
    parser.add_argument('--username', help='Elasticsearch Username')
    parser.add_argument('--password', help='Elasticsearch Password')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Verfügbare Kommandos')
    
    # Health Check
    health_parser = subparsers.add_parser('health', help='Elasticsearch Gesundheitscheck')
    health_parser.set_defaults(func=cmd_health_check)
    
    # Create Indices
    create_parser = subparsers.add_parser('create-indices', help='Erstellt alle Indizes')
    create_parser.set_defaults(func=cmd_create_indices)
    
    # Delete Indices
    delete_parser = subparsers.add_parser('delete-indices', help='Löscht alle Indizes')
    delete_parser.add_argument('--confirm', action='store_true', help='Bestätigung überspringen')
    delete_parser.set_defaults(func=cmd_delete_indices)
    
    # Export Data
    export_parser = subparsers.add_parser('export', help='Exportiert Daten von SQLite zu Elasticsearch')
    export_parser.add_argument('--database', default='steam_price_tracker.db', help='Pfad zur SQLite-Datenbank')
    export_parser.set_defaults(func=cmd_export_data)
    
    # Setup
    setup_parser = subparsers.add_parser('setup', help='Vollständiges Setup')
    setup_parser.add_argument('--database', default='steam_price_tracker.db', help='Pfad zur SQLite-Datenbank')
    setup_parser.set_defaults(func=cmd_setup)
    
    # Docker-Kommandos
    docker_parser = subparsers.add_parser('docker', help='Docker-Container-Management')
    docker_subparsers = docker_parser.add_subparsers(dest='docker_command', help='Docker-Kommandos')
    
    # Docker Start
    docker_start_parser = docker_subparsers.add_parser('start', help='Startet Elasticsearch Container')
    docker_start_parser.add_argument('--container-name', default='elasticsearch-steam-tracker', help='Container-Name')
    docker_start_parser.add_argument('--memory', default='1g', help='Memory-Limit (default: 1g)')
    docker_start_parser.add_argument('--heap-size', default='512m', help='JVM Heap-Size (default: 512m)')
    docker_start_parser.set_defaults(func=cmd_docker_start)
    
    # Docker Stop
    docker_stop_parser = docker_subparsers.add_parser('stop', help='Stoppt Elasticsearch Container')
    docker_stop_parser.add_argument('--container-name', default='elasticsearch-steam-tracker', help='Container-Name')
    docker_stop_parser.set_defaults(func=cmd_docker_stop)
    
    # Docker Remove
    docker_remove_parser = docker_subparsers.add_parser('remove', help='Entfernt Elasticsearch Container')
    docker_remove_parser.add_argument('--container-name', default='elasticsearch-steam-tracker', help='Container-Name')
    docker_remove_parser.add_argument('--confirm', action='store_true', help='Bestätigung überspringen')
    docker_remove_parser.set_defaults(func=cmd_docker_remove)
    
    # Docker Status
    docker_status_parser = docker_subparsers.add_parser('status', help='Zeigt Container-Status')
    docker_status_parser.add_argument('--container-name', default='elasticsearch-steam-tracker', help='Container-Name')
    docker_status_parser.set_defaults(func=cmd_docker_status)
    
    # Docker Logs
    docker_logs_parser = docker_subparsers.add_parser('logs', help='Zeigt Container-Logs')
    docker_logs_parser.add_argument('--container-name', default='elasticsearch-steam-tracker', help='Container-Name')
    docker_logs_parser.add_argument('--tail', type=int, default=50, help='Anzahl der letzten Zeilen (default: 50)')
    docker_logs_parser.set_defaults(func=cmd_docker_logs)
    
    # Docker Restart
    docker_restart_parser = docker_subparsers.add_parser('restart', help='Startet Container neu')
    docker_restart_parser.add_argument('--container-name', default='elasticsearch-steam-tracker', help='Container-Name')
    docker_restart_parser.add_argument('--memory', default='1g', help='Memory-Limit (default: 1g)')
    docker_restart_parser.add_argument('--heap-size', default='512m', help='JVM Heap-Size (default: 512m)')
    docker_restart_parser.set_defaults(func=cmd_docker_restart)
    
    # Docker Setup (alles in einem)
    docker_setup_parser = docker_subparsers.add_parser('setup', help='Vollständiges Docker-Setup')
    docker_setup_parser.add_argument('--container-name', default='elasticsearch-steam-tracker', help='Container-Name')
    docker_setup_parser.add_argument('--memory', default='1g', help='Memory-Limit (default: 1g)')
    docker_setup_parser.add_argument('--heap-size', default='512m', help='JVM Heap-Size (default: 512m)')
    docker_setup_parser.add_argument('--database', default='steam_price_tracker.db', help='Pfad zur SQLite-Datenbank')
    docker_setup_parser.set_defaults(func=cmd_docker_setup)
    
    # Help wenn keine Argumente
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    args = parser.parse_args()
    
    # Docker-Subcommand-Handling
    if args.command == 'docker':
        if hasattr(args, 'docker_command') and args.docker_command:
            if hasattr(args, 'func'):
                args.func(args)
            else:
                docker_parser.print_help()
        else:
            docker_parser.print_help()
    elif hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()