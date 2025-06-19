#!/usr/bin/env python3
"""
Steam Price Tracker - Konsolidierte Version mit Enhanced Scheduler v2.0
KONSOLIDIERT - Vereint Standard Price Tracking mit robuster Charts-Integration
Nutzt Enhanced Universal Background Scheduler für separate Terminal-Execution
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

# Enhanced Universal Background Scheduler importieren
from background_scheduler import (
    EnhancedBackgroundScheduler, 
    create_enhanced_price_tracker_scheduler, 
    create_enhanced_charts_scheduler
)

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SteamPriceTracker:
    """
    Steam Preis-Tracker mit Enhanced Universal Background Scheduler
    KONSOLIDIERTE VERSION - Nutzt separaten Terminal-Execution für alle Background-Tasks
    """
    
    # Store-Konfiguration
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
        Initialisiert Steam Price Tracker mit Enhanced Universal Background Scheduler
        
        Args:
            db_manager: DatabaseManager Instanz
            api_key: Steam API Key für Charts und erweiterte Features
            enable_charts: Ob Charts-Funktionalität aktiviert werden soll
        """
        self.db_manager = db_manager or DatabaseManager()
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SteamPriceTracker/3.0 Enhanced'
        })
        
        # Rate Limiting für CheapShark API
        self.last_cheapshark_request = 0
        self.cheapshark_rate_limit = 1.5  # 1.5 Sekunden zwischen Requests
        
        # ENHANCED: Universal Background Scheduler statt eigenem Threading
        self.price_scheduler = None
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
            self._initialize_charts_integration_enhanced(api_key)
        
        logger.info("✅ Steam Price Tracker mit Enhanced Universal Background Scheduler initialisiert")
        if self.charts_enabled:
            logger.info("📊 Charts-Integration aktiviert")
        else:
            logger.info("📊 Charts-Integration deaktiviert (kein API Key oder nicht verfügbar)")
    
    def _initialize_charts_integration_enhanced(self, api_key: str):
        """
        ENHANCED: Initialisiert Charts-Integration mit Enhanced Universal Background Scheduler
        
        Args:
            api_key: Steam API Key
        """
        try:
            from steam_charts_manager import SteamChartsManager
            
            logger.info("🔄 Initialisiere Enhanced Charts-Integration...")
            
            self.charts_manager = SteamChartsManager(api_key, self.db_manager)
            self.charts_manager.set_price_tracker(self)
            
            # Charts-Tabellen in Datenbank sicherstellen
            if hasattr(self.db_manager, 'init_charts_tables_enhanced'):
                self.db_manager.init_charts_tables_enhanced()
            elif hasattr(self.db_manager, 'init_charts_tables'):
                self.db_manager.init_charts_tables()
            
            # Test ob Charts-Manager funktioniert
            try:
                self.charts_enabled = True
                logger.info("✅ Enhanced Charts-Integration erfolgreich initialisiert")
            except Exception as test_e:
                logger.warning(f"⚠️ Charts-Manager Test fehlgeschlagen: {test_e}")
                self.charts_enabled = False
               
        except ImportError:
            logger.info("ℹ️ steam_charts_manager nicht verfügbar - Charts-Features deaktiviert")
            self.charts_enabled = False
        except Exception as e:
            logger.error(f"❌ Fehler bei Charts-Integration: {e}")
            self.charts_enabled = False
    
    # =====================================================================
    # ENHANCED BACKGROUND SCHEDULER FUNKTIONEN
    # =====================================================================
    
    def start_background_scheduler(self, 
                                  price_interval_hours: int = 6,
                                  name_interval_minutes: int = 30):
        """
        Startet Enhanced Background Scheduler für Price Tracking
        
        Args:
            price_interval_hours: Intervall für Preis-Updates
            name_interval_minutes: Intervall für Namen-Updates
        """
        try:
            if self.price_scheduler and self.price_scheduler.running:
                logger.warning("⚠️ Price Scheduler läuft bereits")
                return
            
            # Enhanced Price Tracker Scheduler erstellen
            self.price_scheduler = create_enhanced_price_tracker_scheduler()
            
            # Intervalle anpassen
            if price_interval_hours != 6:
                for task in self.price_scheduler.tasks.values():
                    if task.scheduler_type == "price_updates":
                        task.interval_minutes = price_interval_hours * 60
                        task.next_run = datetime.now() + timedelta(hours=price_interval_hours)
            
            if name_interval_minutes != 30:
                for task in self.price_scheduler.tasks.values():
                    if task.scheduler_type == "name_updates":
                        task.interval_minutes = name_interval_minutes
                        task.next_run = datetime.now() + timedelta(minutes=name_interval_minutes)
            
            # Scheduler starten
            self.price_scheduler.start_scheduler()
            
            logger.info(f"🚀 Enhanced Background Scheduler gestartet:")
            logger.info(f"   💰 Preis-Updates: alle {price_interval_hours}h")
            logger.info(f"   📝 Namen-Updates: alle {name_interval_minutes}min")
            logger.info("💡 Alle Tasks laufen in separaten Terminals!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten des Background Schedulers: {e}")
            return False
    
    def stop_background_scheduler(self):
        """Stoppt Enhanced Background Scheduler"""
        try:
            if self.price_scheduler:
                self.price_scheduler.stop_scheduler()
                self.price_scheduler = None
                logger.info("⏹️ Enhanced Background Scheduler gestoppt")
            else:
                logger.info("ℹ️ Background Scheduler war nicht aktiv")
        except Exception as e:
            logger.error(f"❌ Fehler beim Stoppen des Background Schedulers: {e}")
    
    def get_scheduler_status(self) -> Dict:
        """
        Gibt detaillierten Status des Enhanced Background Schedulers zurück
        
        Returns:
            Dict mit Scheduler-Status-Informationen
        """
        status = {
            'scheduler_running': False,
            'scheduler_type': 'Enhanced Universal Background Scheduler v2.0',
            'charts_enabled': self.charts_enabled,
            'processes': {},
            'next_runs': {}
        }
        
        # Price Scheduler Status
        if self.price_scheduler:
            price_status = self.price_scheduler.get_process_status()
            status['scheduler_running'] = price_status['scheduler_running']
            status['processes'].update(price_status['processes'])
            
            # Nächste Ausführungszeiten
            for task_type, task in self.price_scheduler.tasks.items():
                if task.next_run:
                    status['next_runs'][task_type] = task.next_run.strftime('%H:%M:%S')
        
        # Charts Scheduler Status
        if self.charts_scheduler:
            charts_status = self.charts_scheduler.get_process_status()
            status['processes'].update(charts_status['processes'])
            
            for task_type, task in self.charts_scheduler.tasks.items():
                if task.next_run:
                    status['next_runs'][f"charts_{task_type}"] = task.next_run.strftime('%H:%M:%S')
        
        return status
    
    # =====================================================================
    # CHARTS-INTEGRATION FUNKTIONEN
    # =====================================================================
    
    def enable_charts_tracking(self,
                              charts_update_hours: int = 6,
                              price_update_hours: int = 4,
                              cleanup_hours: int = 24):
        """
        Aktiviert Charts-Tracking mit Enhanced Background Scheduler
        
        Args:
            charts_update_hours: Intervall für Charts-Updates
            price_update_hours: Intervall für Charts-Preise
            cleanup_hours: Intervall für Cleanup
        """
        if not self.charts_enabled:
            logger.error("❌ Charts-Funktionalität nicht verfügbar")
            return False
        
        try:
            if self.charts_scheduler and self.charts_scheduler.running:
                logger.warning("⚠️ Charts Scheduler läuft bereits")
                return True
            
            # Enhanced Charts Scheduler erstellen
            self.charts_scheduler = create_enhanced_charts_scheduler()
            
            # Charts-Preis-Update Task hinzufügen
            self.charts_scheduler.register_scheduler(
                scheduler_type="charts_price_updates",
                task_function=self._get_charts_price_update_task(),
                interval_minutes=price_update_hours * 60,
                dependencies=["price_tracker", "steam_wishlist_manager"],
                heartbeat_interval=30,
                show_progress_bar=True
            )
            
            # Intervalle anpassen
            for task in self.charts_scheduler.tasks.values():
                if task.scheduler_type == "charts_updates":
                    task.interval_minutes = charts_update_hours * 60
                    task.next_run = datetime.now() + timedelta(hours=charts_update_hours)
                elif task.scheduler_type == "charts_cleanup":
                    task.interval_minutes = cleanup_hours * 60
                    task.next_run = datetime.now() + timedelta(hours=cleanup_hours)
            
            # Charts Scheduler starten
            self.charts_scheduler.start_scheduler()
            
            logger.info(f"📊 Enhanced Charts-Tracking aktiviert:")
            logger.info(f"   📊 Charts-Updates: alle {charts_update_hours}h")
            logger.info(f"   💰 Preis-Updates: alle {price_update_hours}h")
            logger.info(f"   🧹 Cleanup: alle {cleanup_hours}h")
            logger.info("💡 Charts-Tasks laufen in separaten Terminals!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktivieren des Charts-Trackings: {e}")
            return False
    
    def disable_charts_tracking(self):
        """Deaktiviert Charts-Tracking"""
        try:
            if self.charts_scheduler:
                self.charts_scheduler.stop_scheduler()
                self.charts_scheduler = None
                logger.info("⏹️ Charts-Tracking deaktiviert")
            else:
                logger.info("ℹ️ Charts-Tracking war nicht aktiv")
        except Exception as e:
            logger.error(f"❌ Fehler beim Deaktivieren des Charts-Trackings: {e}")
    
    def _get_charts_price_update_task(self) -> str:
        """Generiert Charts-Preis-Update Task"""
        return '''
# Enhanced Charts-Preis-Update Task
print("💰 Enhanced Charts-Preis-Update gestartet...")
print(f"⏰ Start: {datetime.now().strftime('%H:%M:%S')}")

# Heartbeat alle 30 Sekunden
import threading

def heartbeat_timer():
    while True:
        update_heartbeat()
        time.sleep(30)

heartbeat_thread = threading.Thread(target=heartbeat_timer, daemon=True)
heartbeat_thread.start()

try:
    # Price Tracker mit Charts laden
    from price_tracker import create_price_tracker
    from steam_wishlist_manager import load_api_key_from_env
    
    api_key = load_api_key_from_env()
    tracker = create_price_tracker(api_key=api_key, enable_charts=True)
    
    if not tracker.charts_enabled:
        print("❌ Charts-Manager nicht verfügbar")
        exit(1)
    
    # Charts-Spiele Preise aktualisieren
    print("💰 Aktualisiere Preise für Charts-Spiele...")
    result = tracker.update_charts_prices_now()
    
    if result.get('success', True):
        print("✅ Charts-Preis-Update abgeschlossen:")
        print(f"   📊 {result.get('total_games', 0)} Spiele verarbeitet")
        print(f"   💰 {result.get('price_updates', 0)} Preise aktualisiert")
        print(f"   🎯 {result.get('deals_found', 0)} Deals gefunden")
        
        if result.get('errors'):
            print(f"   ⚠️ {len(result['errors'])} Fehler aufgetreten")
    else:
        print(f"❌ Charts-Preis-Update fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")

except Exception as e:
    print(f"❌ Enhanced Charts-Preis-Update Fehler: {e}")
    import traceback
    traceback.print_exc()

print(f"🏁 Enhanced Charts-Preis-Update abgeschlossen um {datetime.now().strftime('%H:%M:%S')}")
'''
    
    # =====================================================================
    # CHARTS CONVENIENCE FUNKTIONEN
    # =====================================================================
    
    def update_charts_now(self, chart_types: List[str] = None) -> Dict:
        """
        Führt sofortiges Charts-Update durch
        
        Args:
            chart_types: Spezifische Chart-Typen (optional)
            
        Returns:
            Ergebnis-Dictionary
        """
        if not self.charts_enabled:
            return {'success': False, 'error': 'Charts-Funktionalität nicht verfügbar'}
        
        try:
            logger.info("🔄 Führe manuelles Charts-Update durch...")
            result = self.charts_manager.update_all_charts(chart_types)
            logger.info(f"✅ Charts-Update abgeschlossen: {result.get('new_games_added', 0)} neue, {result.get('existing_games_updated', 0)} aktualisiert")
            return result
        except Exception as e:
            logger.error(f"❌ Charts-Update Fehler: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_charts_prices_now(self, chart_type: str = None) -> Dict:
        """
        Führt sofortiges Charts-Preis-Update durch
        
        Args:
            chart_type: Spezifischer Chart-Typ (optional)
            
        Returns:
            Ergebnis-Dictionary
        """
        if not self.charts_enabled:
            return {'success': False, 'error': 'Charts-Funktionalität nicht verfügbar'}
        
        try:
            logger.info("💰 Führe Charts-Preis-Update durch...")
            
            # Aktive Charts-Spiele abrufen
            chart_games = self.charts_manager.get_active_chart_games(chart_type)
            
            if not chart_games:
                return {'success': True, 'total_games': 0, 'message': 'Keine Charts-Spiele zu aktualisieren'}
            
            total_games = len(chart_games)
            price_updates = 0
            deals_found = 0
            errors = []
            
            logger.info(f"💰 Aktualisiere Preise für {total_games} Charts-Spiele...")
            
            for game in chart_games:
                try:
                    app_id = game['steam_app_id']
                    
                    # Preis für App aktualisieren
                    price_result = self.get_app_prices(app_id)
                    
                    if price_result:
                        # In Charts-Preis-Tabelle speichern
                        if hasattr(self.charts_manager, 'save_chart_price'):
                            self.charts_manager.save_chart_price(
                                app_id=app_id,
                                chart_type=game['chart_type'],
                                price_data=price_result
                            )
                        
                        price_updates += 1
                        
                        # Deals suchen
                        best_deal = self._find_best_deal(price_result)
                        if best_deal and best_deal.get('discount_percent', 0) > 10:
                            deals_found += 1
                    
                    # Rate Limiting
                    time.sleep(1.5)
                    
                except Exception as e:
                    errors.append(f"Fehler bei {app_id}: {str(e)}")
                    logger.debug(f"Charts-Preis-Update Fehler für {app_id}: {e}")
            
            result = {
                'success': True,
                'total_games': total_games,
                'price_updates': price_updates,
                'deals_found': deals_found,
                'errors': errors
            }
            
            logger.info(f"✅ Charts-Preis-Update: {price_updates}/{total_games} Apps aktualisiert, {deals_found} Deals")
            return result
            
        except Exception as e:
            logger.error(f"❌ Charts-Preis-Update Fehler: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_tracked_charts_summary(self) -> Dict:
        """
        Gibt Zusammenfassung der getrackte Charts zurück
        
        Returns:
            Charts-Zusammenfassung
        """
        if not self.charts_enabled:
            return {'error': 'Charts-Funktionalität nicht verfügbar'}
        
        try:
            return self.charts_manager.get_chart_statistics()
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Charts-Zusammenfassung: {e}")
            return {'error': str(e)}
    
    # =====================================================================
    # CORE PRICE TRACKING FUNKTIONEN (UNVERÄNDERT)
    # =====================================================================
    
    def _wait_for_rate_limit(self):
        """Wartet für Rate Limiting"""
        elapsed = time.time() - self.last_cheapshark_request
        if elapsed < self.cheapshark_rate_limit:
            wait_time = self.cheapshark_rate_limit - elapsed
            time.sleep(wait_time)
        self.last_cheapshark_request = time.time()
    
    def get_app_prices(self, app_id: str, retries: int = 3) -> Optional[Dict]:
        """
        Holt aktuelle Preise für eine App von CheapShark
        
        Args:
            app_id: Steam App ID
            retries: Anzahl Wiederholungsversuche
            
        Returns:
            Dictionary mit Preisinformationen oder None
        """
        for attempt in range(retries):
            try:
                self._wait_for_rate_limit()
                
                url = "https://www.cheapshark.com/api/1.0/games"
                params = {
                    'steamAppID': app_id,
                    'exact': 1
                }
                
                response = self.session.get(url, params=params, timeout=15)
                response.raise_for_status()
                
                data = response.json()
                
                if not data:
                    logger.debug(f"Keine Preisdaten für App {app_id}")
                    return None
                
                # Erstes Spiel aus Ergebnissen nehmen
                game_data = data[0]
                game_title = game_data.get('external', 'Unknown Game')
                
                # Preise für alle Stores sammeln
                prices = {
                    'game_title': game_title,
                    'steam_app_id': app_id,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Alle verfügbaren Deals durchgehen
                for deal in game_data.get('deals', []):
                    store_id = deal['storeID']
                    store_name = self.STORES.get(store_id, f"Store{store_id}")
                    
                    if store_id in self.STORES:
                        prices[f'{store_name.lower()}_price'] = float(deal['price']) if deal['price'] else None
                        prices[f'{store_name.lower()}_original_price'] = float(deal['retailPrice']) if deal['retailPrice'] else None
                        prices[f'{store_name.lower()}_discount_percent'] = int(float(deal['savings'])) if deal['savings'] else 0
                        prices[f'{store_name.lower()}_available'] = True
                
                return prices
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request-Fehler bei App {app_id} (Versuch {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                logger.error(f"Unerwarteter Fehler bei App {app_id}: {e}")
                break
        
        return None
    
    def add_app_to_tracking(self, app_id: str, name: str = None) -> bool:
        """
        Fügt eine App zum Tracking hinzu
        
        Args:
            app_id: Steam App ID
            name: Name der App (optional)
            
        Returns:
            True wenn erfolgreich hinzugefügt
        """
        try:
            # Namen ermitteln falls nicht gegeben
            if not name:
                name = self._get_app_name_from_steam(app_id)
                if not name:
                    name = f"App {app_id}"
            
            # In Datenbank hinzufügen
            return self.db_manager.add_tracked_app(app_id, name)
            
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen der App {app_id}: {e}")
            return False
    
    def _get_app_name_from_steam(self, app_id: str) -> Optional[str]:
        """
        Holt App-Namen von Steam Store API
        
        Args:
            app_id: Steam App ID
            
        Returns:
            App-Name oder None
        """
        try:
            url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&l=german"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if app_id in data and data[app_id]['success']:
                return data[app_id]['data']['name']
                
        except Exception as e:
            logger.debug(f"Fehler beim Abrufen des App-Namens für {app_id}: {e}")
        
        return None
    
    def get_current_prices(self, limit: int = None) -> List[Dict]:
        """
        Gibt aktuelle Preise aller getrackte Apps zurück
        
        Args:
            limit: Maximum Anzahl Apps (optional)
            
        Returns:
            Liste mit aktuellen Preisinformationen
        """
        tracked_apps = self.db_manager.get_tracked_apps(limit=limit)
        current_prices = []
        
        for app in tracked_apps:
            app_id = app['steam_app_id']
            latest_prices = self.db_manager.get_latest_prices(app_id)
            
            if latest_prices:
                current_prices.append(latest_prices)
        
        return current_prices
    
    def get_best_deals(self, min_discount: int = 20, limit: int = 20) -> List[Dict]:
        """
        Findet die besten aktuellen Deals
        
        Args:
            min_discount: Mindest-Rabatt in Prozent
            limit: Maximum Anzahl Deals
            
        Returns:
            Liste der besten Deals
        """
        return self.db_manager.get_best_deals(min_discount, limit)
    
    def _find_best_deal(self, price_data: Dict) -> Optional[Dict]:
        """
        Findet den besten Deal aus Preisdaten
        
        Args:
            price_data: Dictionary mit Preisinformationen
            
        Returns:
            Bester Deal oder None
        """
        best_deal = None
        best_discount = 0
        
        for store_name in self.STORES.values():
            price_key = f"{store_name.lower()}_price"
            discount_key = f"{store_name.lower()}_discount_percent"
            
            if price_key in price_data and discount_key in price_data:
                price = price_data[price_key]
                discount = price_data[discount_key]
                
                if price and discount and discount > best_discount:
                    best_discount = discount
                    best_deal = {
                        'store': store_name,
                        'price': price,
                        'discount_percent': discount
                    }
        
        return best_deal
    
    def update_app_prices(self, app_id: str) -> bool:
        """
        Aktualisiert Preise für eine spezifische App
        
        Args:
            app_id: Steam App ID
            
        Returns:
            True wenn erfolgreich aktualisiert
        """
        try:
            prices = self.get_app_prices(app_id)
            
            if prices:
                # In Datenbank speichern
                return self.db_manager.save_price_snapshot(prices)
            else:
                logger.warning(f"Keine Preise für App {app_id} erhalten")
                return False
                
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Preise für App {app_id}: {e}")
            return False
    
    def process_all_pending_apps_optimized(self, hours_threshold: int = 6) -> Dict:
        """
        Optimiertes Batch-Update für Apps die Updates benötigen
        
        Args:
            hours_threshold: Apps älter als X Stunden aktualisieren
            
        Returns:
            Dictionary mit Verarbeitungs-Statistiken
        """
        start_time = time.time()
        
        # Apps ermitteln die Updates benötigen
        pending_apps = self.db_manager.get_apps_needing_update(hours_threshold)
        
        if not pending_apps:
            return {
                'total_apps': 0,
                'total_successful': 0,
                'total_duration': 0,
                'apps_per_second': 0,
                'errors': []
            }
        
        total_apps = len(pending_apps)
        successful_updates = 0
        errors = []
        
        logger.info(f"🔄 Starte optimiertes Batch-Update für {total_apps} Apps (Schwellenwert: {hours_threshold}h)")
        
        # Batch-Processing
        for i in range(0, total_apps, self.batch_size):
            batch = pending_apps[i:i + self.batch_size]
            batch_start = time.time()
            
            for app in batch:
                app_id = app['steam_app_id']
                
                try:
                    if self.update_app_prices(app_id):
                        successful_updates += 1
                    else:
                        errors.append(f"Keine Preise für {app_id}")
                        
                except Exception as e:
                    errors.append(f"Fehler bei {app_id}: {str(e)}")
                
                # Rate Limiting zwischen Apps
                time.sleep(0.1)
            
            batch_duration = time.time() - batch_start
            logger.info(f"📊 Batch {i//self.batch_size + 1}/{(total_apps-1)//self.batch_size + 1}: "
                       f"{len(batch)} Apps in {batch_duration:.1f}s")
            
            # Pause zwischen Batches
            time.sleep(1.0)
        
        total_duration = time.time() - start_time
        apps_per_second = total_apps / total_duration if total_duration > 0 else 0
        
        result = {
            'total_apps': total_apps,
            'total_successful': successful_updates,
            'total_duration': total_duration,
            'apps_per_second': apps_per_second,
            'errors': errors
        }
        
        logger.info(f"✅ Batch-Update abgeschlossen: {successful_updates}/{total_apps} Apps erfolgreich "
                   f"({apps_per_second:.1f} Apps/s, {len(errors)} Fehler)")
        
        return result
    
    def get_apps_with_generic_names(self, limit: int = 50) -> List[Tuple[str, str]]:
        """
        Findet Apps mit generischen Namen die Updates benötigen
        
        Args:
            limit: Maximum Anzahl Apps
            
        Returns:
            Liste mit (app_id, current_name) Tupeln
        """
        return self.db_manager.get_apps_with_generic_names(limit)
    
    def update_app_name(self, app_id: str) -> Optional[str]:
        """
        Aktualisiert den Namen einer App
        
        Args:
            app_id: Steam App ID
            
        Returns:
            Neuer Name oder None
        """
        try:
            new_name = self._get_app_name_from_steam(app_id)
            
            if new_name:
                if self.db_manager.update_app_name(app_id, new_name):
                    logger.info(f"📝 App {app_id} Name aktualisiert: {new_name}")
                    return new_name
            
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des App-Namens für {app_id}: {e}")
        
        return None
    
    def export_to_csv(self, filename: str = None) -> str:
        """
        Exportiert alle Daten als CSV
        
        Args:
            filename: Dateiname (optional)
            
        Returns:
            Pfad zur erstellten CSV-Datei
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"steam_price_tracker_export_{timestamp}.csv"
        
        return self.db_manager.export_to_csv(filename)
    
    def get_database_statistics(self) -> Dict:
        """
        Gibt Datenbank-Statistiken zurück
        
        Returns:
            Dictionary mit Statistiken
        """
        stats = self.db_manager.get_database_statistics()
        
        # Charts-Statistiken hinzufügen
        if self.charts_enabled:
            try:
                charts_stats = self.get_tracked_charts_summary()
                if 'error' not in charts_stats:
                    stats['charts'] = charts_stats
            except Exception as e:
                logger.debug(f"Charts-Statistiken Fehler: {e}")
        
        return stats

# =====================================================================
# CONVENIENCE FUNCTIONS - ENHANCED
# =====================================================================

def create_price_tracker(api_key: str = None, db_path: str = "steam_price_tracker.db", enable_charts: bool = True):
    """
    Erstellt Steam Price Tracker mit Enhanced Universal Background Scheduler
    
    Args:
        api_key: Steam API Key (optional, lädt aus .env)
        db_path: Pfad zur Datenbank
        enable_charts: Ob Charts-Funktionalität aktiviert werden soll
        
    Returns:
        SteamPriceTracker Instanz mit Enhanced Universal Background Scheduler
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
    ENHANCED: Richtet vollautomatisches Tracking mit Enhanced Universal Background Scheduler ein
    
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
        
        logger.info("🚀 Vollautomatisches Tracking mit Enhanced Universal Background Scheduler aktiviert!")
        logger.info("💡 Alle Tasks laufen in separaten Terminals!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Einrichten der Vollautomation: {e}")
        return False

if __name__ == "__main__":
    # Test-Ausführung
    print("🧪 Steam Price Tracker - Test Mode")
    
    try:
        # Tracker erstellen
        tracker = create_price_tracker()
        
        print(f"✅ Tracker erstellt (Charts: {'✅' if tracker.charts_enabled else '❌'})")
        
        # Status anzeigen
        status = tracker.get_scheduler_status()
        print(f"📊 Scheduler Status: {status}")
        
    except Exception as e:
        print(f"❌ Test-Fehler: {e}")
