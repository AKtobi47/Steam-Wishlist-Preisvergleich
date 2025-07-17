
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    from elasticsearch import Elasticsearch
    from elasticsearch.exceptions import ConnectionError, RequestError
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ElasticsearchConfig:
    """Elasticsearch Konfiguration"""
    host: str = "localhost"
    port: int = 9200
    username: Optional[str] = None
    password: Optional[str] = None
    scheme: str = "http"
    verify_certs: bool = False

class ElasticsearchManager:
    """Elasticsearch Manager für Steam Price Tracker"""
    
    def __init__(self, config: ElasticsearchConfig):
        if not ELASTICSEARCH_AVAILABLE:
            raise ImportError("Elasticsearch nicht installiert. Führe aus: pip install elasticsearch")
        
        self.config = config
        self.client = self._create_client()
        self.indices = {
            'price_snapshots': 'steam_price_snapshots',
            'tracked_apps': 'steam_tracked_apps',
            'name_history': 'steam_name_history',
            'charts_tracking': 'steam_charts_tracking',
            'charts_prices': 'steam_charts_prices',
            'statistics': 'steam_statistics',
            'price_alerts': 'steam_price_alerts',
            'tracking_sessions': 'steam_tracking_sessions',
            'charts_history': 'steam_charts_history',
            'charts_price_snapshots': 'steam_charts_price_snapshots',
            'performance_metrics': 'steam_performance_metrics'
        }
    
    def _create_client(self) -> Elasticsearch:
        """Elasticsearch Client erstellen"""
        auth = None
        if self.config.username and self.config.password:
            auth = (self.config.username, self.config.password)
        
        return Elasticsearch(
            hosts=[{
                'host': self.config.host,
                'port': self.config.port,
                'scheme': self.config.scheme
            }],
            basic_auth=auth,
            verify_certs=self.config.verify_certs,
            request_timeout=30
        )
    
    def health_check(self) -> Dict[str, Any]:
        """Elasticsearch Health Check"""
        try:
            # Cluster Info
            cluster_info = self.client.info()
            cluster_health = self.client.cluster.health()
            
            # Index Statistiken
            indices_stats = {}
            for key, index_name in self.indices.items():
                try:
                    if self.client.indices.exists(index=index_name):
                        count = self.client.count(index=index_name)
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
                        'document_count': 0,
                        'error': str(e)
                    }
            
            # Gesamtanzahl Dokumente
            total_docs = sum(stats['document_count'] for stats in indices_stats.values())
            
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
                'error': f'Verbindung fehlgeschlagen: {str(e)}'
            }
        except Exception as e:
            return {
                'connection_ok': False,
                'error': f'Unerwarteter Fehler: {str(e)}'
            }
    
    def create_indices_and_mappings(self) -> int:
        """Indizes und Mappings erstellen"""
        created_count = 0
        
        mappings = self._get_index_mappings()
        
        for key, index_name in self.indices.items():
            try:
                if not self.client.indices.exists(index=index_name):
                    mapping = mappings.get(key, {})
                    self.client.indices.create(
                        index=index_name,
                        body=mapping
                    )
                    created_count += 1
                    logger.info(f"Index {index_name} erstellt")
                else:
                    logger.info(f"Index {index_name} existiert bereits")
                    
            except RequestError as e:
                logger.error(f"Fehler beim Erstellen von {index_name}: {e}")
            except Exception as e:
                logger.error(f"Unerwarteter Fehler bei {index_name}: {e}")
        
        return created_count
    
    def delete_all_indices(self) -> int:
        """Alle Steam Price Tracker Indizes löschen"""
        deleted_count = 0
        
        for key, index_name in self.indices.items():
            try:
                if self.client.indices.exists(index=index_name):
                    self.client.indices.delete(index=index_name)
                    deleted_count += 1
                    logger.info(f"Index {index_name} gelöscht")
                    
            except Exception as e:
                logger.error(f"Fehler beim Löschen von {index_name}: {e}")
        
        return deleted_count
    
    def export_sqlite_to_elasticsearch(self, db_manager) -> Dict[str, int]:
        """SQLite Daten zu Elasticsearch exportieren"""
        export_stats = {
            'price_snapshots': 0,
            'tracked_apps': 0,
            'name_history': 0,
            'charts_tracking': 0,
            'charts_prices': 0,
            'statistics': 0,
            'price_alerts': 0,
            'tracking_sessions': 0,
            'charts_history': 0,
            'charts_price_snapshots': 0,
            'performance_metrics': 0,
            'total_exported': 0
        }
        
        try:
            # Price Snapshots exportieren
            export_stats['price_snapshots'] = self._export_price_snapshots(db_manager)
            
            # Tracked Apps exportieren
            export_stats['tracked_apps'] = self._export_tracked_apps(db_manager)
            
            # Name History exportieren
            export_stats['name_history'] = self._export_name_history(db_manager)
            
            # Charts Tracking exportieren
            export_stats['charts_tracking'] = self._export_charts_tracking(db_manager)
            
            # Charts Prices exportieren
            export_stats['charts_prices'] = self._export_charts_prices(db_manager)
            
            # Statistics exportieren
            export_stats['statistics'] = self._export_statistics(db_manager)
            
            # Price Alerts exportieren
            export_stats['price_alerts'] = self._export_price_alerts(db_manager)
            
            # Tracking Sessions exportieren
            export_stats['tracking_sessions'] = self._export_tracking_sessions(db_manager)
            
            # Charts History exportieren
            export_stats['charts_history'] = self._export_charts_history(db_manager)
            
            # Charts Price Snapshots exportieren
            export_stats['charts_price_snapshots'] = self._export_charts_price_snapshots(db_manager)
            
            # Performance Metrics exportieren
            export_stats['performance_metrics'] = self._export_performance_metrics(db_manager)
            
            # Gesamtsumme
            export_stats['total_exported'] = sum(export_stats.values()) - export_stats['total_exported']
            
        except Exception as e:
            logger.error(f"Export-Fehler: {e}")
            raise
        
        return export_stats
    
    def _export_price_snapshots(self, db_manager) -> int:
        """Price Snapshots exportieren"""
        try:
            query = """
            SELECT id, steam_app_id, game_title, timestamp, steam_price, steam_original_price, 
                   steam_discount_percent, steam_available, greenmangaming_price, 
                   greenmangaming_original_price, greenmangaming_discount_percent, 
                   greenmangaming_available, gog_price, gog_original_price, 
                   gog_discount_percent, gog_available, humblestore_price, 
                   humblestore_original_price, humblestore_discount_percent, 
                   humblestore_available, fanatical_price, fanatical_original_price, 
                   fanatical_discount_percent, fanatical_available, gamesplanet_price, 
                   gamesplanet_original_price, gamesplanet_discount_percent, 
                   gamesplanet_available
            FROM price_snapshots 
            ORDER BY timestamp DESC LIMIT 10000
            """
            results = db_manager.execute_query(query)
            
            if not results:
                return 0
            
            index_name = self.indices['price_snapshots']
            count = 0
            
            for row in results:
                doc = {
                    'steam_app_id': row.get('steam_app_id'),
                    'game_title': row.get('game_title'),
                    'timestamp': row.get('timestamp'),
                    'steam_price': row.get('steam_price'),
                    'steam_original_price': row.get('steam_original_price'),
                    'steam_discount_percent': row.get('steam_discount_percent'),
                    'steam_available': row.get('steam_available'),
                    'greenmangaming_price': row.get('greenmangaming_price'),
                    'greenmangaming_original_price': row.get('greenmangaming_original_price'),
                    'greenmangaming_discount_percent': row.get('greenmangaming_discount_percent'),
                    'greenmangaming_available': row.get('greenmangaming_available'),
                    'gog_price': row.get('gog_price'),
                    'gog_original_price': row.get('gog_original_price'),
                    'gog_discount_percent': row.get('gog_discount_percent'),
                    'gog_available': row.get('gog_available'),
                    'humblestore_price': row.get('humblestore_price'),
                    'humblestore_original_price': row.get('humblestore_original_price'),
                    'humblestore_discount_percent': row.get('humblestore_discount_percent'),
                    'humblestore_available': row.get('humblestore_available'),
                    'fanatical_price': row.get('fanatical_price'),
                    'fanatical_original_price': row.get('fanatical_original_price'),
                    'fanatical_discount_percent': row.get('fanatical_discount_percent'),
                    'fanatical_available': row.get('fanatical_available'),
                    'gamesplanet_price': row.get('gamesplanet_price'),
                    'gamesplanet_original_price': row.get('gamesplanet_original_price'),
                    'gamesplanet_discount_percent': row.get('gamesplanet_discount_percent'),
                    'gamesplanet_available': row.get('gamesplanet_available'),
                    'exported_at': datetime.now().isoformat()
                }
                
                self.client.index(
                    index=index_name,
                    body=doc,
                    id=row.get('id')
                )
                count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Fehler beim Exportieren von Price Snapshots: {e}")
            return 0
    
    def _export_tracked_apps(self, db_manager) -> int:
        """Tracked Apps exportieren"""
        try:
            query = """
            SELECT steam_app_id, name, added_at, last_price_update, active, 
                   last_name_update, name_update_attempts, source, target_price, notes
            FROM tracked_apps
            """
            results = db_manager.execute_query(query)
            
            if not results:
                return 0
            
            index_name = self.indices['tracked_apps']
            count = 0
            
            for row in results:
                doc = {
                    'steam_app_id': row.get('steam_app_id'),
                    'name': row.get('name'),
                    'added_at': row.get('added_at'),
                    'last_price_update': row.get('last_price_update'),
                    'active': row.get('active'),
                    'last_name_update': row.get('last_name_update'),
                    'name_update_attempts': row.get('name_update_attempts'),
                    'source': row.get('source'),
                    'target_price': row.get('target_price'),
                    'notes': row.get('notes'),
                    'exported_at': datetime.now().isoformat()
                }
                
                self.client.index(
                    index=index_name,
                    body=doc,
                    id=row.get('steam_app_id')
                )
                count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Fehler beim Exportieren von Tracked Apps: {e}")
            return 0
    
    def _export_name_history(self, db_manager) -> int:
        """Name History exportieren"""
        try:
            query = """
            SELECT id, steam_app_id, old_name, new_name, updated_at, update_source
            FROM app_name_history
            ORDER BY updated_at DESC
            """
            results = db_manager.execute_query(query)
            
            if not results:
                return 0
            
            index_name = self.indices['name_history']
            count = 0
            
            for row in results:
                doc = {
                    'steam_app_id': row.get('steam_app_id'),
                    'old_name': row.get('old_name'),
                    'new_name': row.get('new_name'),
                    'updated_at': row.get('updated_at'),
                    'update_source': row.get('update_source'),
                    'exported_at': datetime.now().isoformat()
                }
                
                self.client.index(
                    index=index_name,
                    body=doc,
                    id=row.get('id')
                )
                count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Fehler beim Exportieren von Name History: {e}")
            return 0
    
    def _export_charts_tracking(self, db_manager) -> int:
        """Charts Tracking exportieren"""
        try:
            query = """
            SELECT id, steam_app_id, name, chart_type, current_rank, best_rank, 
                   first_seen, last_seen, total_appearances, active, metadata, 
                   days_in_charts, rank_trend, updated_at, peak_players, current_players
            FROM steam_charts_tracking
            """
            results = db_manager.execute_query(query)
            
            if not results:
                return 0
            
            index_name = self.indices['charts_tracking']
            count = 0
            
            for row in results:
                doc = {
                    'steam_app_id': row.get('steam_app_id'),
                    'name': row.get('name'),
                    'chart_type': row.get('chart_type'),
                    'current_rank': row.get('current_rank'),
                    'best_rank': row.get('best_rank'),
                    'first_seen': row.get('first_seen'),
                    'last_seen': row.get('last_seen'),
                    'total_appearances': row.get('total_appearances'),
                    'active': row.get('active'),
                    'metadata': row.get('metadata'),
                    'days_in_charts': row.get('days_in_charts'),
                    'rank_trend': row.get('rank_trend'),
                    'updated_at': row.get('updated_at'),
                    'peak_players': row.get('peak_players'),
                    'current_players': row.get('current_players'),
                    'exported_at': datetime.now().isoformat()
                }
                
                self.client.index(
                    index=index_name,
                    body=doc,
                    id=row.get('id')
                )
                count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Fehler beim Exportieren von Charts Tracking: {e}")
            return 0
    
    def _export_charts_prices(self, db_manager) -> int:
        """Charts Prices exportieren"""
        try:
            query = """
            SELECT id, steam_app_id, chart_type, current_price, original_price, 
                   discount_percent, store, deal_url, timestamp
            FROM steam_charts_prices
            ORDER BY timestamp DESC
            """
            results = db_manager.execute_query(query)
            
            if not results:
                return 0
            
            index_name = self.indices['charts_prices']
            count = 0
            
            for row in results:
                doc = {
                    'steam_app_id': row.get('steam_app_id'),
                    'chart_type': row.get('chart_type'),
                    'current_price': row.get('current_price'),
                    'original_price': row.get('original_price'),
                    'discount_percent': row.get('discount_percent'),
                    'store': row.get('store'),
                    'deal_url': row.get('deal_url'),
                    'timestamp': row.get('timestamp'),
                    'exported_at': datetime.now().isoformat()
                }
                
                self.client.index(
                    index=index_name,
                    body=doc,
                    id=row.get('id')
                )
                count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Fehler beim Exportieren von Charts Prices: {e}")
            return 0
    
    def _export_statistics(self, db_manager) -> int:
        """Statistics exportieren"""
        try:
            query = """
            SELECT id, metric_name, metric_value, metric_unit, timestamp
            FROM performance_metrics
            ORDER BY timestamp DESC
            """
            results = db_manager.execute_query(query)
            
            if not results:
                return 0
            
            index_name = self.indices['statistics']
            count = 0
            
            for row in results:
                doc = {
                    'metric_name': row.get('metric_name'),
                    'metric_value': row.get('metric_value'),
                    'metric_unit': row.get('metric_unit'),
                    'timestamp': row.get('timestamp'),
                    'exported_at': datetime.now().isoformat()
                }
                
                self.client.index(
                    index=index_name,
                    body=doc,
                    id=row.get('id')
                )
                count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Fehler beim Exportieren von Statistics: {e}")
            return 0
    
    def _export_price_alerts(self, db_manager) -> int:
        """Price Alerts exportieren"""
        try:
            query = """
            SELECT id, steam_app_id, target_price, store_name, active, 
                   created_at, triggered_at
            FROM price_alerts
            """
            results = db_manager.execute_query(query)
            
            if not results:
                return 0
            
            index_name = self.indices['price_alerts']
            count = 0
            
            for row in results:
                doc = {
                    'steam_app_id': row.get('steam_app_id'),
                    'target_price': row.get('target_price'),
                    'store_name': row.get('store_name'),
                    'active': row.get('active'),
                    'created_at': row.get('created_at'),
                    'triggered_at': row.get('triggered_at'),
                    'exported_at': datetime.now().isoformat()
                }
                
                self.client.index(
                    index=index_name,
                    body=doc,
                    id=row.get('id')
                )
                count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Fehler beim Exportieren von Price Alerts: {e}")
            return 0
    
    def _export_tracking_sessions(self, db_manager) -> int:
        """Tracking Sessions exportieren"""
        try:
            query = """
            SELECT id, started_at, completed_at, apps_processed, apps_successful, 
                   errors_count, session_type
            FROM tracking_sessions
            ORDER BY started_at DESC
            """
            results = db_manager.execute_query(query)
            
            if not results:
                return 0
            
            index_name = self.indices['tracking_sessions']
            count = 0
            
            for row in results:
                doc = {
                    'started_at': row.get('started_at'),
                    'completed_at': row.get('completed_at'),
                    'apps_processed': row.get('apps_processed'),
                    'apps_successful': row.get('apps_successful'),
                    'errors_count': row.get('errors_count'),
                    'session_type': row.get('session_type'),
                    'exported_at': datetime.now().isoformat()
                }
                
                self.client.index(
                    index=index_name,
                    body=doc,
                    id=row.get('id')
                )
                count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Fehler beim Exportieren von Tracking Sessions: {e}")
            return 0
    
    def _export_charts_history(self, db_manager) -> int:
        """Charts History exportieren"""
        try:
            query = """
            SELECT id, steam_app_id, chart_type, rank_position, snapshot_timestamp, 
                   additional_data
            FROM charts_history
            ORDER BY snapshot_timestamp DESC
            """
            results = db_manager.execute_query(query)
            
            if not results:
                return 0
            
            index_name = self.indices['charts_history']
            count = 0
            
            for row in results:
                doc = {
                    'steam_app_id': row.get('steam_app_id'),
                    'chart_type': row.get('chart_type'),
                    'rank_position': row.get('rank_position'),
                    'snapshot_timestamp': row.get('snapshot_timestamp'),
                    'additional_data': row.get('additional_data'),
                    'exported_at': datetime.now().isoformat()
                }
                
                self.client.index(
                    index=index_name,
                    body=doc,
                    id=row.get('id')
                )
                count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Fehler beim Exportieren von Charts History: {e}")
            return 0
    
    def _export_charts_price_snapshots(self, db_manager) -> int:
        """Charts Price Snapshots exportieren"""
        try:
            query = """
            SELECT id, steam_app_id, game_title, timestamp, steam_price, steam_original_price, 
                   steam_discount_percent, steam_available, greenmangaming_price, 
                   greenmangaming_original_price, greenmangaming_discount_percent, 
                   greenmangaming_available, gog_price, gog_original_price, 
                   gog_discount_percent, gog_available, humblestore_price, 
                   humblestore_original_price, humblestore_discount_percent, 
                   humblestore_available, fanatical_price, fanatical_original_price, 
                   fanatical_discount_percent, fanatical_available, gamesplanet_price, 
                   gamesplanet_original_price, gamesplanet_discount_percent, 
                   gamesplanet_available, is_chart_game, chart_types
            FROM charts_price_snapshots
            ORDER BY timestamp DESC LIMIT 10000
            """
            results = db_manager.execute_query(query)
            
            if not results:
                return 0
            
            index_name = self.indices['charts_price_snapshots']
            count = 0
            
            for row in results:
                doc = {
                    'steam_app_id': row.get('steam_app_id'),
                    'game_title': row.get('game_title'),
                    'timestamp': row.get('timestamp'),
                    'steam_price': row.get('steam_price'),
                    'steam_original_price': row.get('steam_original_price'),
                    'steam_discount_percent': row.get('steam_discount_percent'),
                    'steam_available': row.get('steam_available'),
                    'greenmangaming_price': row.get('greenmangaming_price'),
                    'greenmangaming_original_price': row.get('greenmangaming_original_price'),
                    'greenmangaming_discount_percent': row.get('greenmangaming_discount_percent'),
                    'greenmangaming_available': row.get('greenmangaming_available'),
                    'gog_price': row.get('gog_price'),
                    'gog_original_price': row.get('gog_original_price'),
                    'gog_discount_percent': row.get('gog_discount_percent'),
                    'gog_available': row.get('gog_available'),
                    'humblestore_price': row.get('humblestore_price'),
                    'humblestore_original_price': row.get('humblestore_original_price'),
                    'humblestore_discount_percent': row.get('humblestore_discount_percent'),
                    'humblestore_available': row.get('humblestore_available'),
                    'fanatical_price': row.get('fanatical_price'),
                    'fanatical_original_price': row.get('fanatical_original_price'),
                    'fanatical_discount_percent': row.get('fanatical_discount_percent'),
                    'fanatical_available': row.get('fanatical_available'),
                    'gamesplanet_price': row.get('gamesplanet_price'),
                    'gamesplanet_original_price': row.get('gamesplanet_original_price'),
                    'gamesplanet_discount_percent': row.get('gamesplanet_discount_percent'),
                    'gamesplanet_available': row.get('gamesplanet_available'),
                    'is_chart_game': row.get('is_chart_game'),
                    'chart_types': row.get('chart_types'),
                    'exported_at': datetime.now().isoformat()
                }
                
                self.client.index(
                    index=index_name,
                    body=doc,
                    id=row.get('id')
                )
                count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Fehler beim Exportieren von Charts Price Snapshots: {e}")
            return 0
    
    def _export_performance_metrics(self, db_manager) -> int:
        """Performance Metrics exportieren"""
        try:
            query = """
            SELECT id, metric_name, metric_value, metric_unit, timestamp
            FROM performance_metrics
            ORDER BY timestamp DESC
            """
            results = db_manager.execute_query(query)
            
            if not results:
                return 0
            
            index_name = self.indices['performance_metrics']
            count = 0
            
            for row in results:
                doc = {
                    'metric_name': row.get('metric_name'),
                    'metric_value': row.get('metric_value'),
                    'metric_unit': row.get('metric_unit'),
                    'timestamp': row.get('timestamp'),
                    'exported_at': datetime.now().isoformat()
                }
                
                self.client.index(
                    index=index_name,
                    body=doc,
                    id=row.get('id')
                )
                count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Fehler beim Exportieren von Performance Metrics: {e}")
            return 0
    
    def _get_index_mappings(self) -> Dict[str, Dict]:
        """Index Mappings definieren"""
        return {
            'price_snapshots': {
                'mappings': {
                    'properties': {
                        'app_id': {'type': 'integer'},
                        'price': {'type': 'double'},
                        'currency': {'type': 'keyword'},
                        'timestamp': {'type': 'date'},
                        'discount': {'type': 'integer'},
                        'original_price': {'type': 'double'},
                        'exported_at': {'type': 'date'}
                    }
                }
            },
            'tracked_apps': {
                'mappings': {
                    'properties': {
                        'app_id': {'type': 'integer'},
                        'name': {'type': 'text', 'analyzer': 'standard'},
                        'added_at': {'type': 'date'},
                        'last_updated': {'type': 'date'},
                        'active': {'type': 'boolean'},
                        'exported_at': {'type': 'date'}
                    }
                }
            },
            'name_history': {
                'mappings': {
                    'properties': {
                        'app_id': {'type': 'integer'},
                        'name': {'type': 'text', 'analyzer': 'standard'},
                        'changed_at': {'type': 'date'},
                        'exported_at': {'type': 'date'}
                    }
                }
            },
            'charts_tracking': {
                'mappings': {
                    'properties': {
                        'app_id': {'type': 'integer'},
                        'chart_data': {'type': 'object'},
                        'last_updated': {'type': 'date'},
                        'exported_at': {'type': 'date'}
                    }
                }
            },
            'charts_prices': {
                'mappings': {
                    'properties': {
                        'app_id': {'type': 'integer'},
                        'price': {'type': 'double'},
                        'date': {'type': 'date'},
                        'source': {'type': 'keyword'},
                        'exported_at': {'type': 'date'}
                    }
                }
            },
            'statistics': {
                'mappings': {
                    'properties': {
                        'metric_name': {'type': 'keyword'},
                        'value': {'type': 'double'},
                        'timestamp': {'type': 'date'},
                        'category': {'type': 'keyword'},
                        'exported_at': {'type': 'date'}
                    }
                }
            }
        }


def create_elasticsearch_manager(host: str = "localhost", port: int = 9200, 
                               username: Optional[str] = None, 
                               password: Optional[str] = None) -> Optional[ElasticsearchManager]:
    """Elasticsearch Manager erstellen"""
    try:
        config = ElasticsearchConfig(
            host=host,
            port=port,
            username=username,
            password=password
        )
        return ElasticsearchManager(config)
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Elasticsearch Managers: {e}")
        return None


def setup_elasticsearch_for_steam_tracker(db_manager, host: str = "localhost", 
                                        port: int = 9200, username: Optional[str] = None,
                                        password: Optional[str] = None) -> Dict[str, Any]:
    """Vollständiges Elasticsearch Setup für Steam Price Tracker"""
    try:
        # Elasticsearch Manager erstellen
        es_manager = create_elasticsearch_manager(host, port, username, password)
        if not es_manager:
            return {'success': False, 'error': 'Elasticsearch Manager konnte nicht erstellt werden'}
        
        # Health Check
        health = es_manager.health_check()
        if not health['connection_ok']:
            return {'success': False, 'error': health['error']}
        
        # Indizes erstellen
        created_indices = es_manager.create_indices_and_mappings()
        
        return {
            'success': True,
            'indices_created': created_indices,
            'mappings_applied': created_indices
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}