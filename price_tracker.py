"""
Steam Price Tracker - Updated Version mit Universal Background Scheduler
KONSOLIDIERT - Vereint Standard Price Tracking mit robuster Charts-Integration
Nutzt universellen BackgroundScheduler für separate Terminal-Execution
"""

import requests
import time
import threading
import schedule
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from pathlib import Path
from database_manager import DatabaseManager

# Universal Background Scheduler importieren
from background_scheduler import BackgroundScheduler, create_price_tracker_scheduler, create_charts_scheduler

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SteamPriceTracker:
    """
    Steam Preis-Tracker mit Universal Background Scheduler
    UPDATED VERSION - Nutzt separaten Terminal-Execution für alle Background-Tasks
    """
    
    # Store-Konfiguration basierend auf Projekt_SteamGoG.ipynb
    STORES = {
        "1": "Steam",
        "3": "GreenManGaming", 
        "7": "GOG",
        "11": "HumbleStore",
        "15": "Fanatical",
        "27": "GamesPlanet"
    }
    
    # Store IDs als String für CheapShark API
    STORE_IDS = "1,3,7,11,15,27"
    
    def __init__(self, db_manager: DatabaseManager = None, api_key: str = None, enable_charts: bool = True):
        """
        Initialisiert Steam Price Tracker mit Universal Background Scheduler
        
        Args:
            db_manager: DatabaseManager Instanz
            api_key: Steam API Key für Charts und erweiterte Features
            enable_charts: Ob Charts-Funktionalität aktiviert werden soll
        """
        self.db_manager = db_manager or DatabaseManager()
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SteamPriceTracker/2.1'
        })
        
        # Rate Limiting für CheapShark API
        self.last_cheapshark_request = 0
        self.cheapshark_rate_limit = 1.5  # 1.5 Sekunden zwischen Requests
        
        # UPDATED: Universal Background Scheduler statt eigenem Threading
        self.price_scheduler = create_price_tracker_scheduler()
        self.charts_scheduler = None
        
        # Batch-Processing Konfiguration
        self.batch_size = 50  # Apps pro Batch
        self.max_retries = 3
        self.retry_delay = 5.0  # Sekunden
        self.processing_active = False
        
        # Charts-Integration (optional) mit robuster Initialisierung
        self.charts_manager = None
        self.charts_enabled = False
        
        if enable_charts and api_key:
            self._initialize_charts_integration_fixed(api_key)
        
        logger.info("✅ Steam Price Tracker mit Universal Background Scheduler initialisiert")
        if self.charts_enabled:
            logger.info("📊 Charts-Integration aktiviert")
        else:
            logger.info("📊 Charts-Integration deaktiviert (kein API Key oder nicht verfügbar)")
    
    def _initialize_charts_integration_fixed(self, api_key: str):
        """
        FIXED: Initialisiert Charts-Integration mit Universal Background Scheduler
        
        Args:
            api_key: Steam API Key
        """
        try:
            from steam_charts_manager import SteamChartsManager
            
            logger.info("🔄 Initialisiere Charts-Integration...")
            
            self.charts_manager = SteamChartsManager(api_key, self.db_manager)
            self.charts_manager.set_price_tracker(self)
            
            # Charts-Tabellen in Datenbank sicherstellen
            if hasattr(self.db_manager, 'init_charts_tables'):
                self.db_manager.init_charts_tables()
            
            # UPDATED: Charts-Scheduler erstellen
            self.charts_scheduler = create_charts_scheduler()
            
            # Test ob Charts-Manager funktioniert
            try:
                self.charts_enabled = True
                logger.info("✅ Charts-Integration mit Universal Scheduler erfolgreich initialisiert")
            except Exception as test_e:
                logger.warning(f"⚠️ Charts-Manager Test fehlgeschlagen: {test_e}")
                self.charts_enabled = False
                self.charts_manager = None
                self.charts_scheduler = None
            
        except ImportError:
            logger.info("ℹ️ Charts-Module nicht verfügbar - Charts-Features deaktiviert")
            self.charts_enabled = False
            self.charts_manager = None
            self.charts_scheduler = None
        except Exception as e:
            logger.warning(f"⚠️ Charts-Integration fehlgeschlagen: {e}")
            self.charts_enabled = False
            self.charts_manager = None
            self.charts_scheduler = None
    
    def _wait_for_cheapshark_rate_limit(self):
        """Wartet für CheapShark API Rate Limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_cheapshark_request
        
        if time_since_last < self.cheapshark_rate_limit:
            wait_time = self.cheapshark_rate_limit - time_since_last
            logger.debug(f"⏳ Rate Limit: Warte {wait_time:.2f}s")
            time.sleep(wait_time)
        
        self.last_cheapshark_request = time.time()
    
    # ========================
    # APP NAME UPDATE FUNCTIONS (Enhanced)
    # ========================
    
    def update_app_names_from_steam(self, app_ids: List[str] = None, api_key: str = None) -> Dict:
        """
        Aktualisiert App-Namen von Steam API
        
        Args:
            app_ids: Liste von Steam App IDs (None = alle Apps mit generischen Namen)
            api_key: Steam API Key
            
        Returns:
            Dict mit Update-Statistiken
        """
        if api_key is None:
            api_key = self.api_key
        
        if not api_key:
            try:
                from steam_wishlist_manager import load_api_key_from_env
                api_key = load_api_key_from_env()
            except ImportError:
                pass
        
        if not api_key:
            logger.error("❌ Kein Steam API Key verfügbar für Namen-Update")
            return {
                'success': False,
                'error': 'No Steam API key available',
                'updated': 0,
                'failed': 0,
                'total': 0
            }
        
        # Apps bestimmen die aktualisiert werden sollen
        if app_ids is None:
            # Hole Apps mit generischen Namen
            apps_to_update = self.get_name_update_candidates()
            app_ids = [app['steam_app_id'] for app in apps_to_update]
            logger.info(f"🔍 Aktualisiere Namen für {len(app_ids)} Apps mit generischen Namen")
        else:
            logger.info(f"🔍 Aktualisiere Namen für {len(app_ids)} spezifische Apps")
        
        if not app_ids:
            logger.info("✅ Keine Apps für Namen-Update gefunden")
            return {
                'success': True,
                'updated': 0,
                'failed': 0,
                'total': 0,
                'message': 'No apps found for name update'
            }
        
        # Steam Wishlist Manager für Namen-Abfrage
        try:
            from steam_wishlist_manager import SteamWishlistManager
            steam_manager = SteamWishlistManager(api_key)
            
            # Namen bulk abrufen
            logger.info(f"📥 Hole Namen von Steam API...")
            name_mapping = steam_manager.get_multiple_app_names(app_ids)
            
            # Namen in Datenbank aktualisieren
            updated = 0
            failed = 0
            
            for app_id in app_ids:
                if app_id in name_mapping:
                    new_name = name_mapping[app_id]
                    
                    if hasattr(self.db_manager, 'update_app_name'):
                        if self.db_manager.update_app_name(app_id, new_name, 'steam_api'):
                            updated += 1
                            logger.debug(f"✅ {app_id}: {new_name}")
                        else:
                            failed += 1
                            logger.warning(f"⚠️ Datenbankfehler für {app_id}")
                    else:
                        # Fallback: Update über SQL
                        try:
                            with self.db_manager.get_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute('UPDATE tracked_apps SET name = ? WHERE steam_app_id = ?', 
                                             (new_name, app_id))
                                conn.commit()
                                updated += 1
                        except Exception:
                            failed += 1
                else:
                    failed += 1
                    logger.warning(f"⚠️ Kein Name gefunden für {app_id}")
            
            success_rate = (updated / len(app_ids)) * 100 if app_ids else 0
            
            logger.info(f"✅ Namen-Update abgeschlossen:")
            logger.info(f"   📊 {updated}/{len(app_ids)} erfolgreich ({success_rate:.1f}%)")
            logger.info(f"   ❌ {failed} fehlgeschlagen")
            
            return {
                'success': True,
                'updated': updated,
                'failed': failed,
                'total': len(app_ids),
                'success_rate': success_rate
            }
            
        except ImportError:
            logger.error("❌ SteamWishlistManager nicht verfügbar")
            return {
                'success': False,
                'error': 'SteamWishlistManager not available',
                'updated': 0,
                'failed': 0,
                'total': len(app_ids)
            }
        except Exception as e:
            logger.error(f"❌ Fehler beim Namen-Update: {e}")
            return {
                'success': False,
                'error': str(e),
                'updated': 0,
                'failed': 0,
                'total': len(app_ids)
            }
    
    def update_single_app_name(self, app_id: str, api_key: str = None) -> bool:
        """
        Aktualisiert Namen einer einzelnen App
        
        Args:
            app_id: Steam App ID
            api_key: Steam API Key
            
        Returns:
            True wenn erfolgreich
        """
        result = self.update_app_names_from_steam([app_id], api_key)
        return result.get('updated', 0) > 0
    
    def update_names_for_apps_with_generic_names(self, api_key: str = None) -> Dict:
        """
        Aktualisiert Namen für alle Apps mit generischen Namen
        
        Args:
            api_key: Steam API Key
            
        Returns:
            Update-Statistiken
        """
        return self.update_app_names_from_steam(None, api_key)
    
    def get_name_update_candidates(self) -> List[Dict]:
        """
        Gibt Apps zurück die Namen-Updates benötigen
        
        Returns:
            Liste von Apps mit generischen Namen
        """
        if hasattr(self.db_manager, 'get_apps_with_generic_names'):
            return self.db_manager.get_apps_with_generic_names()
        
        # Fallback: manuelle Abfrage
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT steam_app_id, name, added_at
                FROM tracked_apps
                WHERE active = 1 
                AND (
                    name LIKE 'Game %'
                    OR name LIKE 'Unknown Game %'
                    OR name = ''
                    OR name IS NULL
                )
                ORDER BY added_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    # ========================
    # ENHANCED WISHLIST IMPORT
    # ========================
    
    def import_steam_wishlist(self, steam_id: str, api_key: str = None, update_names: bool = True) -> Dict:
        """
        Enhanced Steam Wishlist Import mit Namen-Updates
        
        Args:
            steam_id: Steam ID des Benutzers
            api_key: Steam API Key
            update_names: Ob Namen von Steam API aktualisiert werden sollen
            
        Returns:
            Dict mit Import-Statistiken
        """
        if api_key is None:
            api_key = self.api_key
        
        if not api_key:
            try:
                from steam_wishlist_manager import load_api_key_from_env
                api_key = load_api_key_from_env()
            except ImportError:
                pass
        
        if not api_key:
            return {'success': False, 'error': 'No Steam API key available'}
        
        try:
            from steam_wishlist_manager import SteamWishlistManager
            
            wishlist_manager = SteamWishlistManager(api_key)
            wishlist_data = wishlist_manager.get_simple_wishlist(steam_id)
            
            if not wishlist_data:
                return {'success': False, 'error': 'Wishlist konnte nicht abgerufen werden'}
            
            imported = 0
            skipped_existing = 0
            names_updated = 0
            errors = []
            
            for item in wishlist_data:
                try:
                    app_id = item['steam_app_id']
                    name = item['name']
                    
                    # Prüfe ob bereits vorhanden
                    existing_apps = self.get_tracked_apps()
                    existing_app = next((app for app in existing_apps if app['steam_app_id'] == app_id), None)
                    
                    if existing_app:
                        skipped_existing += 1
                        
                        # Namen-Update für bestehende App falls gewünscht
                        if update_names and (
                            existing_app['name'].startswith('Game ') or 
                            existing_app['name'].startswith('Unknown Game') or
                            existing_app['name'] != name
                        ):
                            if hasattr(self.db_manager, 'update_app_name'):
                                if self.db_manager.update_app_name(app_id, name, 'wishlist_import'):
                                    names_updated += 1
                                    logger.debug(f"🔄 Name aktualisiert: {existing_app['name']} → {name}")
                        
                        continue
                    
                    # Zur Datenbank hinzufügen
                    if self.add_app_to_tracking(app_id, name):
                        imported += 1
                        logger.debug(f"✅ App {name} hinzugefügt")
                    else:
                        errors.append(f"Database error for {app_id}: {name}")
                        logger.warning(f"⚠️ Konnte App {name} nicht hinzufügen")
                        
                except Exception as e:
                    errors.append(f"Error processing {item}: {str(e)}")
                    logger.error(f"❌ Fehler bei Wishlist-Item: {e}")
            
            # Import-Statistiken
            import_stats = {
                'success': True,
                'imported': imported,
                'skipped_existing': skipped_existing,
                'names_updated': names_updated,
                'total_items': len(wishlist_data),
                'errors': errors,
                'import_completed_at': datetime.now().isoformat()
            }
            
            logger.info(f"📥 Enhanced Wishlist-Import abgeschlossen:")
            logger.info(f"   ✅ {imported} neue Apps hinzugefügt")
            logger.info(f"   ⏭️ {skipped_existing} bereits vorhanden")
            logger.info(f"   🔄 {names_updated} Namen aktualisiert")
            logger.info(f"   📊 {imported + skipped_existing}/{len(wishlist_data)} Apps verarbeitet")
            
            if errors:
                logger.warning(f"   ⚠️ {len(errors)} Fehler aufgetreten")
            
            return import_stats
            
        except ImportError:
            logger.error("❌ SteamWishlistManager nicht verfügbar")
            return {'success': False, 'error': 'SteamWishlistManager nicht verfügbar'}
        except Exception as e:
            logger.error(f"❌ Fehler beim Enhanced Wishlist-Import: {e}")
            return {
                'success': False,
                'imported': 0,
                'total_items': 0,
                'error': str(e)
            }
    
    # ========================
    # CORE PRICE FETCHING
    # ========================
    
    def get_game_prices_from_cheapshark(self, steam_app_id: str) -> Dict:
        """
        Holt Preise für Steam App von CheapShark API
        
        Args:
            steam_app_id: Steam App ID
            
        Returns:
            Dict mit Preisdaten oder Fehlerstatus
        """
        self._wait_for_cheapshark_rate_limit()
        
        url = "https://www.cheapshark.com/api/1.0/deals"
        params = {
            'steamAppID': steam_app_id,
            'storeID': self.STORE_IDS
        }
        
        try:
            logger.debug(f"🔍 Preisabfrage für Steam App {steam_app_id}")
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if not data:
                    logger.warning(f"⚠️ Keine Deals für App {steam_app_id} gefunden")
                    return {
                        'steam_app_id': steam_app_id,
                        'game_title': f"Unknown Game {steam_app_id}",
                        'prices': {},
                        'timestamp': datetime.now().isoformat(),
                        'status': 'no_deals_found'
                    }
                
                # Game Title aus erstem Deal extrahieren
                game_title = data[0].get('title', f"Game {steam_app_id}")
                
                # Preise für alle Stores initialisieren
                prices = {}
                for store_name in self.STORES.values():
                    prices[store_name] = {
                        'price': None,
                        'original_price': None,
                        'discount_percent': 0,
                        'available': False
                    }
                
                # Deals verarbeiten
                for deal in data:
                    store_id = deal.get('storeID')
                    store_name = self.STORES.get(store_id)
                    
                    if store_name:
                        sale_price = float(deal.get('salePrice', 0))
                        normal_price = float(deal.get('normalPrice', 0))
                        savings = float(deal.get('savings', 0))
                        
                        prices[store_name] = {
                            'price': sale_price,
                            'original_price': normal_price if normal_price > sale_price else sale_price,
                            'discount_percent': round(savings),
                            'available': True
                        }
                
                logger.debug(f"✅ Preise für {game_title} abgerufen")
                
                return {
                    'steam_app_id': steam_app_id,
                    'game_title': game_title,
                    'prices': prices,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'success'
                }
                
            else:
                logger.error(f"❌ CheapShark API Fehler {response.status_code} für App {steam_app_id}")
                return {
                    'steam_app_id': steam_app_id,
                    'game_title': None,
                    'prices': {},
                    'timestamp': datetime.now().isoformat(),
                    'status': f'api_error_{response.status_code}'
                }
                
        except requests.RequestException as e:
            logger.error(f"❌ Request Fehler für App {steam_app_id}: {e}")
            return {
                'steam_app_id': steam_app_id,
                'game_title': None,
                'prices': {},
                'timestamp': datetime.now().isoformat(),
                'status': 'request_error'
            }
    
    # ========================
    # APP MANAGEMENT
    # ========================
    
    def add_app_to_tracking(self, steam_app_id: str, name: str = None) -> bool:
        """Fügt App zum Tracking hinzu"""
        if name is None:
            name = f"Game {steam_app_id}"
        
        return self.db_manager.add_tracked_app(steam_app_id, name)
    
    def remove_app_from_tracking(self, steam_app_id: str) -> bool:
        """Entfernt App aus Tracking"""
        return self.db_manager.remove_tracked_app(steam_app_id)
    
    def get_tracked_apps(self) -> List[Dict]:
        """Gibt alle getrackte Apps zurück"""
        return self.db_manager.get_tracked_apps()
    
    def get_apps_needing_price_update(self, hours_threshold: int = 6) -> List[Dict]:
        """Gibt Apps zurück die ein Preisupdate benötigen"""
        return self.db_manager.get_apps_needing_update(hours_threshold)
    
    # ========================
    # PRICE TRACKING
    # ========================
    
    def track_app_prices(self, steam_app_ids: List[str]) -> Dict:
        """
        Trackt Preise für mehrere Steam Apps
        
        Args:
            steam_app_ids: Liste von Steam App IDs
            
        Returns:
            Dict mit Statistiken
        """
        if not steam_app_ids:
            return {'processed': 0, 'successful': 0, 'failed': 0, 'errors': []}
        
        logger.info(f"🔄 Starte Preis-Tracking für {len(steam_app_ids)} Apps...")
        
        processed = 0
        successful = 0
        failed = 0
        errors = []
        
        for app_id in steam_app_ids:
            try:
                # Preise von CheapShark abrufen
                price_data = self.get_game_prices_from_cheapshark(app_id)
                
                # In Datenbank speichern
                if price_data['status'] == 'success':
                    if self.db_manager.save_price_snapshot(
                        price_data['steam_app_id'],
                        price_data['game_title'],
                        price_data['prices']
                    ):
                        successful += 1
                        # Update last_price_update
                        self.db_manager.update_app_last_price_update(app_id)
                        
                        # FIXED: Auch in Charts-DB speichern falls verfügbar
                        if self.charts_enabled and hasattr(self.db_manager, 'save_charts_price_snapshot'):
                            # Prüfe ob App in Charts ist
                            if hasattr(self.db_manager, 'get_active_chart_games'):
                                chart_games = [g for g in self.db_manager.get_active_chart_games() if g['steam_app_id'] == app_id]
                                if chart_games:
                                    chart_types = [g['chart_type'] for g in chart_games]
                                    self.db_manager.save_charts_price_snapshot(
                                        app_id, 
                                        price_data['game_title'], 
                                        price_data['prices'], 
                                        chart_types
                                    )
                    else:
                        failed += 1
                        errors.append(f"Database error for {app_id}")
                else:
                    failed += 1
                    errors.append(f"{app_id}: {price_data['status']}")
                
                processed += 1
                
                # Fortschrittsanzeige alle 10 Apps
                if processed % 10 == 0:
                    logger.info(f"📊 Fortschritt: {processed}/{len(steam_app_ids)} Apps verarbeitet")
                
            except Exception as e:
                failed += 1
                errors.append(f"{app_id}: {str(e)}")
                logger.error(f"❌ Fehler bei App {app_id}: {e}")
                processed += 1
        
        logger.info(f"✅ Preis-Tracking abgeschlossen: {successful}/{processed} erfolgreich")
        
        return {
            'processed': processed,
            'successful': successful,
            'failed': failed,
            'errors': errors
        }
    
    def track_single_app_price(self, steam_app_id: str) -> bool:
        """Trackt Preis für einzelne App"""
        result = self.track_app_prices([steam_app_id])
        return result['successful'] > 0
    
    # ========================
    # BATCH PROCESSING
    # ========================
    
    def process_all_pending_apps_optimized(self, hours_threshold: int = 6) -> Dict:
        """
        Verarbeitet alle Apps die Updates benötigen - OPTIMIERT
        
        Args:
            hours_threshold: Apps älter als X Stunden
            
        Returns:
            Dict mit Gesamt-Statistiken
        """
        if self.processing_active:
            logger.warning("⚠️ Processing bereits aktiv")
            return {'error': 'Processing already active'}
        
        self.processing_active = True
        
        try:
            logger.info(f"🚀 Starte optimierte Gesamtverarbeitung (Threshold: {hours_threshold}h)")
            
            # Apps holen die Updates benötigen
            pending_apps = self.get_apps_needing_price_update(hours_threshold)
            
            if not pending_apps:
                logger.info("✅ Alle Apps sind aktuell - keine Verarbeitung nötig")
                return {
                    'total_apps': 0,
                    'total_successful': 0,
                    'total_failed': 0,
                    'total_batches': 0,
                    'total_duration': 0,
                    'apps_per_second': 0,
                    'success': True
                }
            
            # Apps in Batches aufteilen
            batches = [
                pending_apps[i:i + self.batch_size] 
                for i in range(0, len(pending_apps), self.batch_size)
            ]
            
            logger.info(f"📦 Aufgeteilt in {len(batches)} Batches à {self.batch_size} Apps")
            
            # Gesamtstatistiken
            total_start = time.time()
            total_successful = 0
            total_failed = 0
            all_errors = []
            
            # Verarbeite jeden Batch
            for batch_num, batch in enumerate(batches, 1):
                logger.info(f"📦 Batch {batch_num}/{len(batches)}")
                
                # App IDs extrahieren
                app_ids = [app['steam_app_id'] for app in batch]
                
                # Batch verarbeiten
                batch_stats = self.track_app_prices(app_ids)
                
                total_successful += batch_stats['successful']
                total_failed += batch_stats['failed']
                all_errors.extend(batch_stats['errors'])
                
                # Kurze Pause zwischen Batches (für Rate Limiting)
                if batch_num < len(batches):
                    logger.info("⏳ Pause zwischen Batches...")
                    time.sleep(2.0)
            
            total_duration = time.time() - total_start
            total_apps = len(pending_apps)
            
            final_stats = {
                'total_apps': total_apps,
                'total_successful': total_successful,
                'total_failed': total_failed,
                'total_batches': len(batches),
                'total_duration': round(total_duration, 2),
                'apps_per_second': round(total_apps / total_duration, 2) if total_duration > 0 else 0,
                'errors': all_errors,
                'success': True
            }
            
            logger.info(f"🎉 Optimierte Verarbeitung abgeschlossen:")
            logger.info(f"   📊 {final_stats['total_successful']}/{final_stats['total_apps']} Apps erfolgreich")
            logger.info(f"   ⏱️ Dauer: {final_stats['total_duration']}s")
            logger.info(f"   ⚡ {final_stats['apps_per_second']:.1f} Apps/s")
            
            return final_stats
            
        except Exception as e:
            logger.error(f"❌ Fehler bei optimierter Verarbeitung: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            self.processing_active = False
    
    # ========================
    # UNIVERSAL BACKGROUND SCHEDULER INTEGRATION - NEW
    # ========================
    
    def start_background_scheduler(self, 
                                  price_interval_hours: int = 6,
                                  name_interval_minutes: int = 30) -> bool:
        """
        UPDATED: Startet Background-Scheduler für Price Tracking in separatem Terminal
        
        Args:
            price_interval_hours: Intervall für Preis-Updates in Stunden
            name_interval_minutes: Intervall für Namen-Updates in Minuten
            
        Returns:
            True wenn erfolgreich gestartet
        """
        try:
            # Price Updates Scheduler starten
            if self.price_scheduler.start_scheduler(
                'price_updates', 
                interval_hours=price_interval_hours
            ):
                logger.info(f"✅ Preis-Update Scheduler gestartet (alle {price_interval_hours}h)")
            
            # Name Updates Scheduler starten
            if self.price_scheduler.start_scheduler(
                'name_updates',
                interval_minutes=name_interval_minutes
            ):
                logger.info(f"✅ Namen-Update Scheduler gestartet (alle {name_interval_minutes}min)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten des Background-Schedulers: {e}")
            return False
    
    def stop_background_scheduler(self) -> bool:
        """
        UPDATED: Stoppt alle Background-Scheduler
        
        Returns:
            True wenn erfolgreich gestoppt
        """
        try:
            stopped_count = self.price_scheduler.stop_all_schedulers()
            logger.info(f"⏹️ {stopped_count} Price Tracker Scheduler gestoppt")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Stoppen der Background-Scheduler: {e}")
            return False
    
    def get_enhanced_scheduler_status(self) -> Dict:
        """
        UPDATED: Gibt erweiterten Scheduler-Status mit Universal Background Scheduler zurück
        
        Returns:
            Dict mit erweiterten Scheduler-Informationen
        """
        status = {
            'scheduler_type': 'Universal Background Scheduler',
            'price_scheduler_status': self.price_scheduler.get_scheduler_status(),
            'charts_scheduler_status': None,
            'total_active_schedulers': 0
        }
        
        # Price Scheduler Status auswerten
        price_status = status['price_scheduler_status']
        if price_status and 'schedulers' in price_status:
            for scheduler_name, scheduler_info in price_status['schedulers'].items():
                if scheduler_info.get('running'):
                    status['total_active_schedulers'] += 1
        
        # Charts Scheduler Status (falls verfügbar)
        if self.charts_enabled and self.charts_scheduler:
            status['charts_scheduler_status'] = self.charts_scheduler.get_scheduler_status()
            
            charts_status = status['charts_scheduler_status']
            if charts_status and 'schedulers' in charts_status:
                for scheduler_name, scheduler_info in charts_status['schedulers'].items():
                    if scheduler_info.get('running'):
                        status['total_active_schedulers'] += 1
        
        # Compatibility-Felder für alte API
        status['standard_scheduler_running'] = any(
            s.get('running', False) 
            for s in price_status.get('schedulers', {}).values()
        ) if price_status else False
        
        status['charts_scheduler_running'] = any(
            s.get('running', False) 
            for s in status['charts_scheduler_status'].get('schedulers', {}).values()
        ) if status['charts_scheduler_status'] else False
        
        return status
    
    def get_scheduler_status(self) -> Dict:
        """
        Kompatibilitäts-Wrapper für get_enhanced_scheduler_status
        
        Returns:
            Dict mit Scheduler-Status
        """
        return self.get_enhanced_scheduler_status()
    
    # Kompatibilitäts-Methoden für alte API
    def start_scheduler(self, interval_hours: int = 6):
        """
        DEPRECATED: Kompatibilitäts-Wrapper für start_background_scheduler
        Nutzt Universal Background Scheduler
        """
        logger.warning("⚠️ start_scheduler() ist deprecated - verwende start_background_scheduler()")
        return self.start_background_scheduler(price_interval_hours=interval_hours)
    
    def stop_scheduler(self):
        """
        DEPRECATED: Kompatibilitäts-Wrapper für stop_background_scheduler
        """
        logger.warning("⚠️ stop_scheduler() ist deprecated - verwende stop_background_scheduler()")
        return self.stop_background_scheduler()
    
    # ========================
    # CHARTS INTEGRATION - UPDATED
    # ========================
    
    def enable_charts_tracking(self, 
                              charts_update_hours: int = 6,
                              price_update_hours: int = 4,
                              cleanup_hours: int = 24) -> bool:
        """
        UPDATED: Aktiviert Charts-Tracking mit Universal Background Scheduler
        
        Args:
            charts_update_hours: Intervall für Charts-Updates
            price_update_hours: Intervall für Charts-Preis-Updates  
            cleanup_hours: Intervall für Charts-Cleanup
            
        Returns:
            True wenn erfolgreich aktiviert
        """
        if not self.charts_enabled:
            logger.warning("⚠️ Charts-Funktionalität nicht verfügbar")
            return False
        
        if not self.charts_scheduler:
            logger.error("❌ Charts-Scheduler nicht verfügbar")
            return False
        
        try:
            # Charts Update Scheduler starten
            if self.charts_scheduler.start_scheduler(
                'charts_updates',
                interval_hours=charts_update_hours
            ):
                logger.info(f"✅ Charts-Update Scheduler gestartet (alle {charts_update_hours}h)")
            
            # Charts Price Update Scheduler starten
            if self.charts_scheduler.start_scheduler(
                'charts_prices',
                interval_hours=price_update_hours
            ):
                logger.info(f"✅ Charts-Preis Scheduler gestartet (alle {price_update_hours}h)")
            
            # Charts Cleanup Scheduler starten
            if self.charts_scheduler.start_scheduler(
                'charts_cleanup',
                interval_hours=cleanup_hours
            ):
                logger.info(f"✅ Charts-Cleanup Scheduler gestartet (alle {cleanup_hours}h)")
            
            logger.info("✅ Charts-Tracking mit Universal Background Scheduler aktiviert")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktivieren des Charts-Trackings: {e}")
            return False
    
    def disable_charts_tracking(self) -> bool:
        """
        UPDATED: Deaktiviert Charts-Tracking sicher
        
        Returns:
            True wenn erfolgreich deaktiviert
        """
        if not self.charts_enabled or not self.charts_scheduler:
            return True
        
        try:
            stopped_count = self.charts_scheduler.stop_all_schedulers()
            logger.info(f"⏹️ {stopped_count} Charts-Scheduler gestoppt")
            return True
        except Exception as e:
            logger.error(f"❌ Fehler beim Deaktivieren des Charts-Trackings: {e}")
            return False
    
    def update_charts_now(self, chart_types: List[str] = None) -> Dict:
        """
        FIXED: Führt sofortiges Charts-Update durch mit Fehlerbehandlung
        
        Args:
            chart_types: Liste der zu aktualisierenden Chart-Typen
            
        Returns:
            Update-Statistiken
        """
        if not self.charts_enabled:
            return {'success': False, 'error': 'Charts not enabled'}
        
        if not self.charts_manager:
            return {'success': False, 'error': 'Charts manager not available'}
        
        try:
            # Standard-Counts für Charts
            counts = {
                'most_played': 100,
                'top_releases': 50,
                'best_sellers': 100,
                'weekly_top_sellers': 75
            }
            
            # Nur spezifische Chart-Typen wenn angegeben
            if chart_types:
                counts = {ct: counts.get(ct, 50) for ct in chart_types if ct in counts}
            
            result = self.charts_manager.update_all_charts(counts)
            return result
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Charts-Update: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_charts_prices_now(self, chart_type: str = None) -> Dict:
        """
        FIXED: Führt sofortiges Preis-Update für Charts-Spiele durch
        
        Args:
            chart_type: Optionale Filterung nach Chart-Typ
            
        Returns:
            Update-Statistiken
        """
        if not self.charts_enabled:
            return {'success': False, 'error': 'Charts not enabled'}
        
        if not self.charts_manager:
            return {'success': False, 'error': 'Charts manager not available'}
        
        try:
            # Charts-Spiele holen die Updates benötigen
            if hasattr(self.db_manager, 'get_chart_games_needing_price_update'):
                pending_games = self.db_manager.get_chart_games_needing_price_update(hours_threshold=0)
            else:
                # Fallback: alle aktiven Charts-Spiele
                if hasattr(self.db_manager, 'get_active_chart_games'):
                    pending_games = self.db_manager.get_active_chart_games(chart_type)
                else:
                    return {'success': False, 'error': 'Charts database functions not available'}
            
            if not pending_games:
                return {'success': True, 'total_updated': 0, 'message': 'All prices current'}
            
            # App IDs extrahieren
            app_ids = list(set(game['steam_app_id'] for game in pending_games))
            
            # Standard Preis-Tracking verwenden
            result = self.track_app_prices(app_ids)
            
            return {
                'success': True,
                'total_games': len(app_ids),
                'successful': result['successful'],
                'failed': result['failed'],
                'errors': result.get('errors', [])
            }
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Charts-Preisupdate: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_best_charts_deals(self, limit: int = 15, chart_type: str = None) -> List[Dict]:
        """
        Gibt beste Deals für Charts-Spiele zurück (falls verfügbar)
        
        Args:
            limit: Anzahl Deals
            chart_type: Optionale Filterung nach Chart-Typ
            
        Returns:
            Liste der besten Charts-Deals
        """
        if not self.charts_enabled:
            return []
        
        try:
            if hasattr(self.db_manager, 'get_charts_best_deals'):
                return self.db_manager.get_charts_best_deals(limit, chart_type)
            else:
                return []
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Charts-Deals: {e}")
            return []
    
    def get_trending_price_drops(self, hours_back: int = 24, min_discount: int = 20) -> List[Dict]:
        """
        Gibt Charts-Spiele mit neuen Preissenkungen zurück (falls verfügbar)
        
        Args:
            hours_back: Stunden zurückblicken
            min_discount: Mindestrabatt in Prozent
            
        Returns:
            Liste der Charts-Spiele mit neuen Deals
        """
        if not self.charts_enabled:
            return []
        
        try:
            # Vereinfachte Implementation - könnte erweitert werden
            trending_deals = []
            
            if hasattr(self.db_manager, 'get_active_chart_games'):
                active_games = self.db_manager.get_active_chart_games()
                
                for game in active_games[:20]:  # Limitiere für Performance
                    app_id = game['steam_app_id']
                    
                    # Aktuelle Preise holen
                    if hasattr(self.db_manager, 'get_charts_price_history'):
                        recent_prices = self.db_manager.get_charts_price_history(app_id, days_back=2)
                        
                        if len(recent_prices) >= 2:
                            latest = recent_prices[0]
                            
                            # Prüfe auf Rabatte
                            stores = ['steam', 'greenmangaming', 'gog', 'humblestore', 'fanatical', 'gamesplanet']
                            
                            for store in stores:
                                latest_discount = latest.get(f'{store}_discount_percent', 0)
                                
                                if latest_discount >= min_discount and latest.get(f'{store}_available'):
                                    trending_deals.append({
                                        'steam_app_id': app_id,
                                        'game_title': latest.get('game_title', game['name']),
                                        'chart_type': game['chart_type'],
                                        'store': store.title(),
                                        'current_price': latest.get(f'{store}_price'),
                                        'discount_percent': latest_discount,
                                        'timestamp': latest['timestamp']
                                    })
                                    break
            
            # Nach Rabatt sortieren
            trending_deals.sort(key=lambda x: x['discount_percent'], reverse=True)
            return trending_deals[:20]
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Trending Price Drops: {e}")
            return []
    
    # ========================
    # ENHANCED STATISTICS
    # ========================
    
    def get_enhanced_statistics(self) -> Dict:
        """
        Gibt erweiterte Statistiken mit Charts-Daten zurück
        
        Returns:
            Dict mit erweiterten Statistiken
        """
        # Basis-Statistiken
        stats = self.get_statistics()
        
        # Universal Background Scheduler Status
        stats['background_scheduler'] = {
            'price_tracker': self.price_scheduler.get_scheduler_status(),
            'charts': self.charts_scheduler.get_scheduler_status() if self.charts_scheduler else None
        }
        
        # Charts-Statistiken hinzufügen falls verfügbar
        if self.charts_enabled and hasattr(self.db_manager, 'get_charts_statistics'):
            try:
                charts_stats = self.db_manager.get_charts_statistics()
                stats['charts'] = charts_stats
                stats['charts']['enabled'] = True
            except Exception as e:
                logger.warning(f"⚠️ Fehler beim Laden der Charts-Statistiken: {e}")
                stats['charts'] = {'enabled': True, 'error': str(e)}
        else:
            stats['charts'] = {
                'enabled': False,
                'message': 'Charts-Funktionalität nicht verfügbar'
            }
        
        return stats
    
    # ========================
    # DATA RETRIEVAL
    # ========================
    
    def get_statistics(self) -> Dict:
        """Gibt erweiterte Tracker-Statistiken zurück"""
        return self.db_manager.get_statistics()
    
    def get_price_history(self, steam_app_id: str, days_back: int = 30) -> List[Dict]:
        """Gibt Preisverlauf für App zurück"""
        return self.db_manager.get_price_history(steam_app_id, days_back)
    
    def get_latest_prices(self, steam_app_id: str) -> Optional[Dict]:
        """Gibt neueste Preise für App zurück"""
        return self.db_manager.get_latest_prices(steam_app_id)
    
    def get_current_best_deals(self, limit: int = 10) -> List[Dict]:
        """Gibt beste aktuelle Deals zurück"""
        return self.db_manager.get_best_deals(limit)
    
    # ========================
    # UTILITY METHODS
    # ========================
    
    def print_price_summary(self, steam_app_id: str):
        """Zeigt Preis-Zusammenfassung für eine App"""
        price_data = self.get_game_prices_from_cheapshark(steam_app_id)
        
        if price_data['status'] != 'success':
            print(f"❌ Keine Preisdaten für App {steam_app_id}")
            return
        
        print(f"\n💰 AKTUELLE PREISE FÜR: {price_data['game_title']}")
        print(f"Steam App ID: {steam_app_id}")
        print(f"=" * 50)
        
        for store_name, price_info in price_data['prices'].items():
            if price_info['available']:
                price = price_info['price']
                discount = price_info['discount_percent']
                
                status = f"€{price:.2f}"
                if discount > 0:
                    status += f" (-{discount}%)"
                
                print(f"{store_name:15}: {status}")
            else:
                print(f"{store_name:15}: Nicht verfügbar")
        
        print()
    
    def export_price_history_csv(self, steam_app_id: str, output_file: str = None) -> str:
        """Exportiert Preisverlauf als CSV"""
        if output_file is None:
            output_file = f"price_history_{steam_app_id}.csv"
        
        history = self.get_price_history(steam_app_id, days_back=90)
        
        if not history:
            logger.warning(f"Keine Preisdaten für Export verfügbar für App {steam_app_id}")
            return None
        
        # CSV Header
        csv_lines = ["date,Steam,GreenManGaming,GOG,HumbleStore,Fanatical,GamesPlanet"]
        
        # Daten verarbeiten
        for snapshot in reversed(history):  # Älteste zuerst
            date = snapshot['timestamp'][:10]  # YYYY-MM-DD
            
            prices = []
            stores = ['steam', 'greenmangaming', 'gog', 'humblestore', 'fanatical', 'gamesplanet']
            
            for store in stores:
                price_col = f"{store}_price"
                available_col = f"{store}_available"
                
                if snapshot.get(available_col) and snapshot.get(price_col) is not None:
                    prices.append(f"{snapshot[price_col]:.2f}")
                else:
                    prices.append("")
            
            csv_lines.append(f"{date},{','.join(prices)}")
        
        # Datei schreiben
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(csv_lines))
        
        logger.info(f"✅ CSV Export erstellt: {output_path}")
        return str(output_path)
    
    def cleanup_scheduler_resources(self):
        """
        UPDATED: Bereinigt alle Scheduler-Ressourcen
        """
        try:
            # Price Tracker Scheduler aufräumen
            self.price_scheduler.cleanup_all_files()
            
            # Charts Scheduler aufräumen (falls verfügbar)
            if self.charts_scheduler:
                self.charts_scheduler.cleanup_all_files()
            
            logger.info("🧹 Alle Scheduler-Ressourcen bereinigt")
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Aufräumen der Scheduler-Ressourcen: {e}")


# ========================
# CONVENIENCE FUNCTIONS - UPDATED
# ========================

def create_price_tracker(api_key: str = None, db_path: str = "steam_price_tracker.db", enable_charts: bool = True):
    """
    Erstellt Steam Price Tracker mit Universal Background Scheduler
    
    Args:
        api_key: Steam API Key (optional, lädt aus .env)
        db_path: Pfad zur Datenbank
        enable_charts: Ob Charts-Funktionalität aktiviert werden soll
        
    Returns:
        SteamPriceTracker Instanz mit Universal Background Scheduler
    """
    if api_key is None and enable_charts:
        try:
            from steam_wishlist_manager import load_api_key_from_env
            api_key = load_api_key_from_env()
        except ImportError:
            logger.info("⚠️ steam_wishlist_manager nicht verfügbar - kein automatisches API Key laden")
    
    # Database Manager
    db_manager = DatabaseManager(db_path)
    
    # Price Tracker erstellen
    tracker = SteamPriceTracker(db_manager, api_key, enable_charts)
    
    return tracker

def setup_full_automation(tracker: SteamPriceTracker,
                         normal_interval: int = 6,
                         charts_interval: int = 6,
                         charts_price_interval: int = 4,
                         name_interval: int = 30) -> bool:
    """
    UPDATED: Richtet vollautomatisches Tracking mit Universal Background Scheduler ein
    
    Args:
        tracker: SteamPriceTracker Instanz
        normal_interval: Intervall für normale Apps (Stunden)
        charts_interval: Intervall für Charts-Updates (Stunden)
        charts_price_interval: Intervall für Charts-Preise (Stunden)
        name_interval: Intervall für Namen-Updates (Minuten)
        
    Returns:
        True wenn erfolgreich eingerichtet
    """
    try:
        # Price Tracker Background Scheduler starten
        tracker.start_background_scheduler(
            price_interval_hours=normal_interval,
            name_interval_minutes=name_interval
        )
        logger.info(f"✅ Price Tracker Automation: Preise alle {normal_interval}h, Namen alle {name_interval}min")
        
        # Charts-Tracking starten (falls verfügbar)
        if tracker.charts_enabled:
            tracker.enable_charts_tracking(
                charts_update_hours=charts_interval,
                price_update_hours=charts_price_interval,
                cleanup_hours=24
            )
            logger.info(f"✅ Charts Automation: Updates alle {charts_interval}h, Preise alle {charts_price_interval}h")
        
        logger.info("🚀 Vollautomatisches Tracking mit Universal Background Scheduler aktiviert!")
        logger.info("💡 Alle Tasks laufen in separaten Terminals!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Setup der Automatisierung: {e}")
        return False

def cleanup_all_background_schedulers():
    """
    Utility-Funktion zum Aufräumen aller Background-Scheduler-Ressourcen
    """
    try:
        from pathlib import Path
        
        # Temporäre Scheduler-Dateien entfernen
        temp_dir = Path("temp_schedulers")
        if temp_dir.exists():
            for file in temp_dir.glob("scheduler_*.py"):
                file.unlink()
            
            try:
                temp_dir.rmdir()
            except OSError:
                pass
        
        logger.info("🧹 Alle Background-Scheduler-Ressourcen bereinigt")
        
    except Exception as e:
        logger.warning(f"⚠️ Fehler beim Aufräumen: {e}")
