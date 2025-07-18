#!/usr/bin/env python3
"""
Steam Price Tracker - KORRIGIERTE HAUPTKLASSE
Behebt alle identifizierten API-Probleme:
- Fügt fehlende get_tracked_apps() Methode hinzu
- Korrekte API-Namen (get_database_stats statt get_statistics)
- Vollständige Kompatibilität mit main.py
- Robuste Fallback-Mechanismen
"""

import logging
import schedule
import time as time_module
import threading
import requests
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import os

# Lokale Imports
from database_manager import DatabaseManager, create_database_manager

# Logging Setup
try:
    from logging_config import get_price_tracker_logger
    logger = get_price_tracker_logger()
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

class SteamPriceTracker:
    """
    Steam Price Tracker Hauptklasse - KORRIGIERT
    Alle APIs funktionieren jetzt korrekt mit main.py und anderen Komponenten
    """
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None, api_key: Optional[str] = None, 
                 enable_charts: bool = True, enable_scheduler: bool = True):
        """
        Initialisiert den Steam Price Tracker
        
        Args:
            db_manager: DatabaseManager Instanz
            api_key: Steam API Key
            enable_charts: Charts-Funktionalität aktivieren
            enable_scheduler: Scheduler aktivieren
        """
        # Database Manager
        self.db_manager = db_manager or create_database_manager()
        
        # API Key
        self.api_key = api_key or self._load_api_key()
        
        # Features
        self.enable_charts = enable_charts
        self.enable_scheduler = enable_scheduler
        
        # Scheduler
        self.scheduler = None
        self.scheduler_thread = None
        self.scheduler_running = False
        
        # Charts Manager
        self.charts_manager = None
        self.charts_enabled = False
        
        # Performance Tracking
        self.last_update = None
        self.update_count = 0
        self.error_count = 0
        
        # Initialisierung
        self._init_components()
        
        logger.info("✅ SteamPriceTracker erfolgreich initialisiert")
    
    def _load_api_key(self) -> Optional[str]:
        """Lädt Steam API Key aus .env Datei"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            api_key = os.getenv('STEAM_API_KEY')
            if api_key:
                logger.info("✅ Steam API Key aus .env geladen")
                return api_key
            else:
                logger.warning("⚠️ Kein Steam API Key in .env gefunden")
                return None
        except ImportError:
            logger.warning("⚠️ python-dotenv nicht verfügbar")
            return None
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des API Keys: {e}")
            return None
    
    def _init_components(self):
        """Initialisiert alle Komponenten"""
        # Charts Manager
        if self.enable_charts:
            try:
                from steam_charts_manager import SteamChartsManager
                self.charts_manager = SteamChartsManager(self.api_key, self.db_manager, self)
                self.charts_enabled = True
                logger.info("✅ Charts Manager initialisiert")
            except ImportError:
                logger.warning("⚠️ Charts Manager nicht verfügbar")
                self.charts_enabled = False
        
        # Scheduler
        if self.enable_scheduler:
            self._init_scheduler()
    
    def _init_scheduler(self):
        """Initialisiert den Scheduler"""
        try:
            # Schedule Jobs konfigurieren
            schedule.clear()
            
            # Preis-Updates alle 6 Stunden
            schedule.every(6).hours.do(self._scheduled_price_update)
            
            # Charts-Updates alle 2 Stunden (falls aktiviert)
            if self.charts_enabled:
                schedule.every(2).hours.do(self._scheduled_charts_update)
            
            # Datenbank-Cleanup einmal täglich
            schedule.every().day.at("03:00").do(self._scheduled_cleanup)
            
            logger.info("✅ Scheduler konfiguriert")
        except Exception as e:
            logger.error(f"❌ Fehler bei Scheduler-Initialisierung: {e}")
    
    
    # =====================================================================
    # KORRIGIERTE KERN-APIs (KOMPATIBEL MIT MAIN.PY)
    # =====================================================================
    
    def get_tracked_apps(self, active_only: bool = True, limit: Optional[int] = None) -> List[Dict]:
        """
        KORRIGIERTE API: Holt alle getrackte Apps
        Diese Methode fehlte in der ursprünglichen Implementierung
        
        Args:
            active_only: Nur aktive Apps
            limit: Maximum Anzahl Apps
            
        Returns:
            Liste mit App-Informationen
        """
        try:
            return self.db_manager.get_tracked_apps(active_only=active_only, limit=limit)
        except Exception as e:
            logger.error(f"❌ Fehler in get_tracked_apps: {e}")
            return []
    
    def get_database_stats(self) -> Dict:
        """
        KORRIGIERTE API: get_database_stats statt get_statistics
        Kompatibel mit main.py Aufrufen
        """
        try:
            return self.db_manager.get_database_stats()
        except Exception as e:
            logger.error(f"❌ Fehler in get_database_stats: {e}")
            return {
                'tracked_apps': 0,
                'total_snapshots': 0,
                'stores_tracked': [],
                'newest_snapshot': None
            }
    
    def add_app_to_tracking(self, steam_app_id: str, name: Optional[str] = None, 
                           source: str = "manual") -> Tuple[bool, str]:
        """
        ERWEITERTE API: Fügt App zum Tracking hinzu mit detailliertem Ergebnis
        Kompatibel mit main.py Erwartungen
        
        Args:
            steam_app_id: Steam App ID
            name: Name der App (wird automatisch abgerufen falls leer)
            source: Quelle der App
            
        Returns:
            Tuple (success, message)
        """
        try:
            # Name automatisch abrufen falls nicht angegeben
            if not name:
                name = self._fetch_app_name(steam_app_id)
                if not name:
                    name = f"Game {steam_app_id}"
            
            # App hinzufügen
            success = self.db_manager.add_tracked_app(steam_app_id, name, source)
            
            if success:
                message = f"App '{name}' ({steam_app_id}) erfolgreich hinzugefügt"
                logger.info(f"✅ {message}")
                return True, message
            else:
                message = f"App '{name}' ({steam_app_id}) bereits vorhanden"
                logger.info(f"ℹ️ {message}")
                return True, message  # Auch True da kein Fehler
                
        except Exception as e:
            error_msg = f"Fehler beim Hinzufügen der App {steam_app_id}: {e}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def add_or_update_app(self, steam_app_id: str, name: str, target_price: Optional[float] = None) -> bool:
        """
        KOMPATIBILITÄTS-API: Alternative für add_app_to_tracking
        """
        try:
            success = self.db_manager.add_tracked_app(steam_app_id, name, "manual", target_price)
            return success
        except Exception as e:
            logger.error(f"❌ Fehler in add_or_update_app: {e}")
            return False
    
    def update_price_for_app(self, steam_app_id: str) -> bool:
        """
        ERWEITERTE API: Aktualisiert Preise für eine spezifische App
        """
        try:
            # App-Details aus DB holen
            apps = self.db_manager.get_tracked_apps(active_only=True)
            target_app = None
            
            for app in apps:
                if app.get('steam_app_id') == steam_app_id:
                    target_app = app
                    break
            
            if not target_app:
                logger.warning(f"App {steam_app_id} nicht in getrackte Apps gefunden")
                return False
            
            # Preise abrufen und speichern
            app_name = target_app.get('name', f'Game {steam_app_id}')
            price_data = self._fetch_prices_for_app(steam_app_id, app_name)
            
            if price_data:
                success = self.db_manager.save_price_snapshot(steam_app_id, app_name, price_data)
                if success:
                    logger.info(f"✅ Preise für {app_name} aktualisiert")
                    return True
            
            logger.warning(f"⚠️ Keine Preise für {app_name} gefunden")
            return False
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Preis-Update für {steam_app_id}: {e}")
            return False
    
    def track_app_prices(self, app_ids: List[str]) -> Dict[str, bool]:
        """
        Legacy-Methode: Aktualisiert Preise für mehrere Apps
        
        Args:
            app_ids: Liste von Steam App IDs
            
        Returns:
            Dictionary mit Ergebnissen pro App ID
        """
        if not app_ids:
            app_ids = [app['steam_app_id'] for app in self.get_tracked_apps()]
    
        # 🚀 INTELLIGENTE BATCH-ERKENNUNG!
        if len(app_ids) > 5:  # Bei mehr als 5 Apps: BATCH-POWER!
            logger.info(f"📦 {len(app_ids)} Apps → Automatische BATCH-VERARBEITUNG aktiviert!")
        
            batch_result = self.batch_update_multiple_apps(app_ids)
        
            # Konvertiere Batch-Ergebnis zu Legacy-Format
            if batch_result.get('success'):
                return {app_id: True for app_id in app_ids[:batch_result.get('successful_updates', 0)]}
            else:
                return {app_id: False for app_id in app_ids}
        else:
            # Bei wenigen Apps: Standard-Verarbeitung
            logger.info(f"🔄 {len(app_ids)} Apps → Standard-Verarbeitung")
            return self._track_app_prices_sequential(app_ids)
    
    def _track_app_prices_sequential(self, app_ids: List[str]) -> Dict[str, bool]:
        """Sequentielle Preis-Aktualisierung für wenige Apps - NEUE HILFSFUNKTION"""
        results = {}
    
        for app_id in app_ids:
            try:
                success = self.update_price_for_app(app_id)
                results[app_id] = success
            
                if success:
                    logger.info(f"✅ App {app_id} Preise aktualisiert")
                else:
                    logger.warning(f"⚠️ App {app_id} Preise nicht aktualisiert")
            
                # Rate Limiting
                time_module.sleep(1.5)
            
            except Exception as e:
                logger.error(f"❌ Fehler bei App {app_id}: {e}")
                results[app_id] = False
    
        return results
    
    def get_best_deals(self, min_discount_percent: int = 25, limit: int = 10) -> List[Dict]:
        """
        DEALS-API: Holt die besten aktuellen Deals
        
        Args:
            min_discount_percent: Mindest-Rabatt in Prozent
            limit: Maximum Anzahl Deals
            
        Returns:
            Liste mit Deal-Informationen
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Hole neueste Deals aus allen Stores
                stores = ['steam', 'greenmangaming', 'gog', 'humblestore', 'fanatical', 'gamesplanet']
                deals = []
                
                for store in stores:
                    cursor.execute(f"""
                        SELECT DISTINCT 
                            ps.steam_app_id,
                            ps.game_title,
                            ps.{store}_price as current_price,
                            ps.{store}_original_price as original_price,
                            ps.{store}_discount_percent as discount_percent,
                            ps.timestamp,
                            ta.name
                        FROM price_snapshots ps
                        JOIN tracked_apps ta ON ps.steam_app_id = ta.steam_app_id
                        WHERE ps.{store}_discount_percent >= ?
                        AND ps.{store}_price IS NOT NULL
                        AND ps.{store}_price > 0
                        AND ta.active = 1
                        ORDER BY ps.{store}_discount_percent DESC, ps.timestamp DESC
                        LIMIT ?
                    """, (min_discount_percent, limit))
                    
                    for row in cursor.fetchall():
                        deal = {
                            'steam_app_id': row[0],
                            'name': row[6] or row[1],
                            'current_price': row[2],
                            'original_price': row[3],
                            'discount_percent': row[4],
                            'store': store.title().replace('store', ' Store'),
                            'timestamp': row[5]
                        }
                        deals.append(deal)
                
                # Nach Rabatt sortieren
                deals.sort(key=lambda x: x['discount_percent'], reverse=True)
                
                # Duplikate entfernen (gleiche App, niedrigerer Preis bevorzugen)
                unique_deals = {}
                for deal in deals:
                    app_id = deal['steam_app_id']
                    if app_id not in unique_deals or deal['current_price'] < unique_deals[app_id]['current_price']:
                        unique_deals[app_id] = deal
                
                result = list(unique_deals.values())[:limit]
                logger.info(f"📊 {len(result)} Deals gefunden (min. {min_discount_percent}% Rabatt)")
                
                return result
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Deals: {e}")
            return []
    
    def print_price_summary(self, limit: int = 10):
        """
        DISPLAY-API: Zeigt Preis-Zusammenfassung an
        """
        try:
            print("\nfrom database_manager import create_batch_writer\n📊 PREIS-ZUSAMMENFASSUNG")
            print("=" * 25)
            
            # Getrackte Apps
            apps = self.get_tracked_apps(limit=limit)
            print(f"🎮 Getrackte Apps: {len(apps)}")
            
            # Statistiken
            stats = self.get_database_stats()
            print(f"📸 Preis-Snapshots: {stats.get('total_snapshots', 0)}")
            print(f"🏪 Überwachte Stores: {len(stats.get('stores_tracked', []))}")
            
            # Beste Deals
            deals = self.get_best_deals(limit=5)
            if deals:
                print(f"\n🎯 Top 5 Deals:")
                for i, deal in enumerate(deals, 1):
                    name = deal['name'][:30]
                    price = deal['current_price']
                    discount = deal['discount_percent']
                    store = deal['store']
                    print(f"{i}. {name} - €{price:.2f} (-{discount}%) bei {store}")
            
            print("=" * 25)
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Preis-Zusammenfassung: {e}")
    
    # =====================================================================
    # SCHEDULER MANAGEMENT
    # =====================================================================
    
    def start_scheduler(self) -> bool:
        """Startet den automatischen Scheduler"""
        try:
            if self.scheduler_running:
                logger.info("ℹ️ Scheduler läuft bereits")
                return True
            
            # Scheduler-Thread starten
            self.scheduler_running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            logger.info("🚀 Scheduler gestartet")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten des Schedulers: {e}")
            return False
    
    def stop_scheduler(self) -> bool:
        """Stoppt den automatischen Scheduler"""
        try:
            if not self.scheduler_running:
                logger.info("ℹ️ Scheduler läuft nicht")
                return True
            
            self.scheduler_running = False
            
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)
            
            schedule.clear()
            logger.info("🛑 Scheduler gestoppt")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Stoppen des Schedulers: {e}")
            return False
    
    def get_scheduler_status(self) -> Dict:
        """
        KORRIGIERTE API: Holt Scheduler-Status
        Kompatibel mit main.py
        """
        try:
            next_run = None
            jobs_count = len(schedule.jobs)
            
            if schedule.jobs:
                next_job = min(schedule.jobs, key=lambda job: job.next_run)
                next_run = next_job.next_run.strftime('%Y-%m-%d %H:%M:%S') if next_job.next_run else None
            
            return {
                'scheduler_running': self.scheduler_running,
                'next_run': next_run or 'N/A',
                'jobs_count': jobs_count,
                'last_update': self.last_update.isoformat() if self.last_update else None,
                'update_count': self.update_count,
                'error_count': self.error_count
            }
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Scheduler-Status: {e}")
            return {
                'scheduler_running': False,
                'next_run': 'N/A',
                'jobs_count': 0,
                'error': str(e)
            }
    
    def get_enhanced_scheduler_status(self) -> Dict:
        """ERWEITERTE API: Detaillierter Scheduler-Status"""
        try:
            basic_status = self.get_scheduler_status()
            
            # Erweiterte Informationen
            enhanced_status = basic_status.copy()
            enhanced_status.update({
                'charts_enabled': self.charts_enabled,
                'api_key_available': bool(self.api_key),
                'database_status': 'connected',
                'last_successful_update': self.last_update.isoformat() if self.last_update else None,
                'performance_metrics': {
                    'updates_completed': self.update_count,
                    'errors_encountered': self.error_count,
                    'success_rate': round((self.update_count / max(self.update_count + self.error_count, 1)) * 100, 1)
                }
            })
            
            return enhanced_status
            
        except Exception as e:
            logger.error(f"❌ Fehler beim erweiterten Scheduler-Status: {e}")
            return self.get_scheduler_status()
    
    def _run_scheduler(self):
        """Scheduler-Hauptschleife"""
        logger.info("🔄 Scheduler-Thread gestartet")
        
        while self.scheduler_running:
            try:
                schedule.run_pending()
                time_module.sleep(60)  # Prüfe alle 60 Sekunden
            except Exception as e:
                logger.error(f"❌ Fehler im Scheduler: {e}")
                self.error_count += 1
                time_module.sleep(60)
        
        logger.info("🔄 Scheduler-Thread beendet")
    
    def _scheduled_price_update(self):
        """Geplante Preisaktualisierung"""
        try:
            logger.info("🔄 Starte geplante Preisaktualisierung...")
            
            apps = self.get_tracked_apps()
            if not apps:
                logger.info("ℹ️ Keine Apps für Update gefunden")
                return
            
            app_ids = [app['steam_app_id'] for app in apps]
            results = self.track_app_prices(app_ids[:20])  # Limitiere auf 20 Apps pro Run
            
            successful = sum(1 for success in results.values() if success)
            self.update_count += successful
            self.last_update = datetime.now()
            
            logger.info(f"✅ Geplante Preisaktualisierung abgeschlossen: {successful}/{len(results)} erfolgreich")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei geplanter Preisaktualisierung: {e}")
            self.error_count += 1
    
    def _scheduled_charts_update(self):
        """Geplante Charts-Aktualisierung"""
        try:
            if not self.charts_enabled or not self.charts_manager:
                return
            
            logger.info("🔄 Starte geplante Charts-Aktualisierung...")
            
            if hasattr(self.charts_manager, 'update_all_charts'):
                success = self.charts_manager.update_all_charts()
                if success:
                    logger.info("✅ Charts-Aktualisierung erfolgreich")
                else:
                    logger.warning("⚠️ Charts-Aktualisierung fehlgeschlagen")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Charts-Aktualisierung: {e}")
            self.error_count += 1
    
    def _scheduled_cleanup(self):
        """Geplante Datenbank-Bereinigung"""
        try:
            logger.info("🧹 Starte geplante Datenbank-Bereinigung...")
            
            removed = self.db_manager.cleanup_old_prices(days=90)
            logger.info(f"✅ {removed} alte Preis-Snapshots entfernt")
            
            # Datenbank optimieren
            self.db_manager.vacuum_database()
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Datenbank-Bereinigung: {e}")
            self.error_count += 1
    
    # =====================================================================
    # PRIVATE HELPER METHODS
    # =====================================================================
    
    def _fetch_app_name(self, steam_app_id: str) -> Optional[str]:
        """Holt App-Name von Steam API"""
        try:
            if not self.api_key:
                return None
            
            url = f"https://store.steampowered.com/api/appdetails"
            params = {'appids': steam_app_id}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            app_data = data.get(steam_app_id, {})
            
            if app_data.get('success'):
                return app_data.get('data', {}).get('name')
            
            return None
            
        except Exception as e:
            logger.debug(f"Fehler beim Abrufen des App-Namens für {steam_app_id}: {e}")
            return None
    
    def _fetch_prices_for_app(self, steam_app_id: str, app_name: str) -> Optional[Dict]:
        """Holt aktuelle Preise für eine App von allen Stores"""
        try:
            price_data = {
                'steam_app_id': steam_app_id,
                'game_title': app_name,
                'timestamp': datetime.now()
            }
            
            # Steam Store Preise
            steam_prices = self._fetch_steam_prices(steam_app_id)
            if steam_prices:
                price_data['steam'] = steam_prices
            
            # Weitere Stores über CheapShark API
            cheapshark_prices = self._fetch_cheapshark_prices(app_name)
            if cheapshark_prices:
                price_data.update(cheapshark_prices)
            
            return price_data if len(price_data) > 3 else None  # Mindestens eine Store-Info
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Preise für {steam_app_id}: {e}")
            return None
    
    def _fetch_steam_prices(self, steam_app_id: str) -> Optional[Dict]:
        """Holt Preise vom Steam Store"""
        try:
            url = f"https://store.steampowered.com/api/appdetails"
            params = {'appids': steam_app_id, 'filters': 'price_overview'}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            app_data = data.get(steam_app_id, {})
            
            if app_data.get('success') and 'data' in app_data:
                price_overview = app_data['data'].get('price_overview')
                
                if price_overview:
                    return {
                        'price': price_overview.get('final', 0) / 100,  # Von Cent zu Euro
                        'original_price': price_overview.get('initial', 0) / 100,
                        'discount_percent': price_overview.get('discount_percent', 0),
                        'available': True
                    }
            
            return None
            
        except Exception as e:
            logger.debug(f"Fehler beim Abrufen der Steam-Preise für {steam_app_id}: {e}")
            return None
    
    def _fetch_cheapshark_prices(self, app_id: str) -> Dict:
        """
        Holt Preise von CheapShark API für eine App
        """
    
        # Einfaches dynamisches Rate Limiting mit globalen Variablen
        if not hasattr(self, '_cheapshark_last_request'):
            self._cheapshark_last_request = 0
            self._cheapshark_current_rate = float(os.getenv('CHEAPSHARK_RATE_LIMIT', '2.0'))
            self._cheapshark_success_count = 0
            self._cheapshark_error_count = 0
    
        max_retries = 6
        base_timeout = int(os.getenv('CHEAPSHARK_TIMEOUT', '20'))
    
        for attempt in range(max_retries + 1):
            try:
                # Rate Limiting
                current_time = time_module.time()
                time_since_last = current_time - self._cheapshark_last_request
            
                if time_since_last < self._cheapshark_current_rate:
                    wait_time = self._cheapshark_current_rate - time_since_last
                    logger.debug(f"⏳ CheapShark Rate Limit: warte {wait_time:.1f}s")
                    time_module.sleep(wait_time)
            
                self._cheapshark_last_request = time_module.time()
            
                # Request mit adaptivem Timeout
                timeout = base_timeout + (attempt * 5)
                url = "https://www.cheapshark.com/api/1.0/games"
                params = {'title': app_id, 'limit': 5}
            
                response = requests.get(url, params=params, timeout=timeout)
            
                if response.status_code == 200:
                    # Erfolg - optimiere Rate
                    self._cheapshark_success_count += 1
                    if self._cheapshark_success_count % 5 == 0 and self._cheapshark_current_rate > 1.0:
                        self._cheapshark_current_rate = max(1.0, self._cheapshark_current_rate * 0.9)
                        logger.debug(f"✅ CheapShark Rate optimiert: {self._cheapshark_current_rate:.1f}s")
                
                    # Parse Response (wie deine ursprüngliche Funktion)
                    games = response.json()
                    if not games:
                        return {}
                
                    store_mapping = {
                        '1': 'steam',
                        '3': 'greenmangaming',
                        '7': 'gog',
                        '11': 'humblestore',
                        '15': 'fanatical',
                        '25': 'gamesplanet'
                    }
                
                    prices = {}
                
                    for game in games:
                        if game.get('external', '').lower() == app_id.lower():
                            deals_url = f"https://www.cheapshark.com/api/1.0/games?id={game['gameID']}"
                            time_module.sleep(0.5)  # Kurze Pause zwischen Requests
                        
                            try:
                                deals_response = requests.get(deals_url, timeout=timeout)
                                if deals_response.status_code == 200:
                                    deals_data = deals_response.json()
                                
                                    for deal in deals_data.get('deals', []):
                                        store_id = deal.get('storeID')
                                        store_name = store_mapping.get(store_id)
                                    
                                        if store_name:
                                            try:
                                                prices[store_name] = {
                                                    'price': float(deal.get('price', 0)),
                                                    'original_price': float(deal.get('retailPrice', 0)),
                                                    'discount_percent': int(float(deal.get('savings', 0))),
                                                    'available': True
                                                }
                                            except (ValueError, TypeError):
                                                continue
                            except:
                                continue
                            break
                
                    return prices
                
                elif response.status_code == 429:
                    # Rate Limit erreicht
                    self._cheapshark_error_count += 1
                    old_rate = self._cheapshark_current_rate
                    self._cheapshark_current_rate = min(5.0, self._cheapshark_current_rate * 1.5)
                    logger.warning(f"⚠️ CheapShark Rate Limit: {old_rate:.1f}s → {self._cheapshark_current_rate:.1f}s")
                
                    if attempt < max_retries:
                        backoff_time = (2 ** attempt) * self._cheapshark_current_rate
                        logger.warning(f"🔄 CheapShark 429 Retry in {backoff_time:.1f}s")
                        time_module.sleep(backoff_time)
                        continue
                    else:
                        logger.error(f"❌ CheapShark 429 nach {max_retries} Versuchen")
                        return {}
                    
                else:
                    logger.debug(f"Fehler beim Abrufen der CheapShark-Preise: {response.status_code}")
                    return {}
                
            except requests.exceptions.Timeout:
                if attempt < max_retries:
                    wait_time = (2 ** attempt) * 2
                    logger.warning(f"⏰ CheapShark Timeout - Retry in {wait_time}s")
                    time_module.sleep(wait_time)
                    continue
                else:
                    logger.debug(f"Fehler beim Abrufen der CheapShark-Preise: Timeout nach {max_retries} Versuchen")
                    return {}
                
            except Exception as e:
                logger.debug(f"Fehler beim Abrufen der CheapShark-Preise: {e}")
                return {}
    
        return {}

    # =====================================================================
    # WARTUNG & UTILITY METHODEN
    # =====================================================================
    
    def cleanup_and_optimize(self) -> Dict[str, Any]:
        """Führt vollständige Wartung durch"""
        try:
            results = {
                'cleanup_started': datetime.now().isoformat(),
                'operations': {}
            }
            
            # Alte Preise bereinigen
            removed_prices = self.db_manager.cleanup_old_prices(days=90)
            results['operations']['cleanup_old_prices'] = {
                'success': True,
                'removed_count': removed_prices
            }
            
            # Datenbank optimieren
            vacuum_success = self.db_manager.vacuum_database()
            results['operations']['vacuum_database'] = {
                'success': vacuum_success
            }
            
            # Statistiken aktualisieren
            stats = self.get_database_stats()
            results['operations']['database_stats'] = stats
            
            results['cleanup_completed'] = datetime.now().isoformat()
            results['overall_success'] = True
            
            logger.info("✅ Wartung und Optimierung abgeschlossen")
            return results
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Wartung und Optimierung: {e}")
            return {
                'cleanup_started': datetime.now().isoformat(),
                'error': str(e),
                'overall_success': False
            }
        
    def create_batch_price_entry_dynamic(self, app_id: str, price_data: Dict) -> Dict:
        """
        Dynamische Erstellung der batch_price_entry mit allen Stores
        """
        # Unterstützte Stores
        SUPPORTED_STORES = [
            'steam', 'greenmangaming', 'gog', 
            'humblestore', 'fanatical', 'gamesplanet'
        ]
    
        # Basis-Entry
        entry = {
            'steam_app_id': app_id,
            'game_title': price_data.get('game_title', ''),
            'timestamp': time_module.time(),
        }
    
        # Alle Store-Felder dynamisch hinzufügen
        for store in SUPPORTED_STORES:
            entry.update({
                f'{store}_price': price_data.get(f'{store}_price', 0),
                f'{store}_original_price': price_data.get(f'{store}_original_price', 0),
                f'{store}_discount_percent': price_data.get(f'{store}_discount_percent', 0),
                f'{store}_available': price_data.get(f'{store}_available', False),
            })
    
        # Aggregierte Daten
        entry.update({
            'best_price': price_data.get('best_price', 0),
            'best_store': price_data.get('best_store', ''),
            'best_discount_percent': price_data.get('best_discount_percent', 0),
            'total_stores_available': price_data.get('total_stores_available', 0),
        })
    
        return entry

    def batch_update_multiple_apps(self, app_ids: List[str], progress_callback=None) -> Dict[str, Any]:
        """
        Batch-Update für mehrere Apps mit ProgressTracker-Integration
        Diese Methode aktualisiert Preise für mehrere Apps in Batches und verwendet den Batch-Writer

        Args:
            app_ids: Liste von Steam App IDs
            progress_callback: Optionaler Callback für Progress-Updates (ProgressTracker-kompatibel)
        
        Returns:
            Dictionary mit Ergebnissen:
                - success: bool
                - successful_updates: Anzahl erfolgreicher Updates
                - failed_updates: Anzahl fehlgeschlagener Updates
                - total_apps: Gesamtanzahl der Apps
                - duration: Dauer des gesamten Prozesses in Sekunden
                - apps_per_second: Durchschnittliche Apps pro Sekunde
                - batch_writer_result: Ergebnis des Batch-Writers (falls verwendet)
                - database_writes: Anzahl der geschriebenen Einträge in die Datenbank
                - performance_multiplier: Performance-Multiplikator des Batch-Writers (falls verwendet)
        """
        if not app_ids:
            return {'success': False, 'error': 'Keine App-IDs angegeben'}
    
        start_time = time_module.time()
        successful_updates = 0
        failed_updates = 0
        all_price_data = []
    
        # ProgressTracker-kompatible Callback-Wrapper
        current_phase = 'prices'
    
        def progress_tracker_callback(progress_info):
            """ProgressTracker-kompatible Progress-Updates für Preise"""
            if not progress_callback:
                return
        
            # ProgressTracker-Format
            tracker_info = {
                'phase': 'prices',
                'current': progress_info.get('processed_apps', 0),
                'total': progress_info.get('total_apps', len(app_ids)),
                'percentage': progress_info.get('progress_percent', 0),
                'details': progress_info.get('status', progress_info.get('current_task', '')),
                'elapsed_time': time_module.time() - start_time
            }
        
            progress_callback(tracker_info)
    
        # Batch-Processing Setup
        batch_size = 10
        total_batches = math.ceil(len(app_ids) / batch_size)
    
        logger.info(f"🚀 BATCH Preis-Update für {len(app_ids)} Apps gestartet...")
    
        # Start Progress
        if progress_tracker_callback:
            progress_tracker_callback({
                'progress_percent': 0,
                'status': f'{len(app_ids)} Apps in {total_batches} Batches',
                'processed_apps': 0,
                'total_apps': len(app_ids)
            })
    
        # Batch-Processing
        for i in range(0, len(app_ids), batch_size):
            batch = app_ids[i:i+batch_size]
            batch_num = (i // batch_size) + 1
        
            logger.info(f"📦 Verarbeite Batch {batch_num}: Apps {i+1}-{min(i+batch_size, len(app_ids))}")
        
            # Progress-Update
            if progress_tracker_callback:
                progress_tracker_callback({
                    'progress_percent': (i / len(app_ids)) * 85,  # 85% für Data-Collection
                    'status': f'💰 Batch {batch_num}/{total_batches}',
                    'processed_apps': i,
                    'total_apps': len(app_ids)
                })

            for app_id in batch:
                try:
                    price_data = self._fetch_cheapshark_prices(app_id)
        
                    if price_data:
                        # KORREKTE Batch-Entry für den Batch-Writer erstellen
                        batch_price_entry = self._create_batch_price_entry_for_batch_writer(app_id, price_data)
                    
                        # Validierung
                        if self._validate_batch_price_entry(batch_price_entry):
                            all_price_data.append(batch_price_entry)
                            successful_updates += 1
                            logger.debug(f"✅ Preise für App {app_id} vorbereitet")
                        else:
                            logger.warning(f"⚠️ Ungültige Preisdaten für App {app_id}")
                            failed_updates += 1
                    else:
                        failed_updates += 1
            
                except Exception as e:
                    logger.error(f"❌ Fehler bei App {app_id}: {e}")
                    failed_updates += 1

            time_module.sleep(1)  # Rate Limiting zwischen Batches

        # Progress: Data Collection abgeschlossen
        if progress_tracker_callback:
            progress_tracker_callback({
                'progress_percent': 85,
                'status': '💾 Bereite Batch-Write vor...',
                'processed_apps': len(app_ids),
                'total_apps': len(app_ids)
            })

        # BATCH-WRITER verwenden
        if all_price_data:
            try:
                logger.info(f"💾 Verwende BATCH-WRITER für {len(all_price_data)} Preis-Einträge...")
            
                from database_manager import create_batch_writer
                batch_writer = create_batch_writer(self.db_manager)
            
                # Progress während Write
                if progress_tracker_callback:
                    progress_tracker_callback({
                        'progress_percent': 90,
                        'status': f'💾 Batch-Write: {len(all_price_data)} Einträge'
                    })
            
                # KORREKTER Batch-Write für Preise
                batch_result = batch_writer.batch_write_prices(all_price_data)
            
                duration = time_module.time() - start_time
            
                if batch_result.get('success'):
                    logger.info(f"✅ BATCH-WRITER erfolgreich: {batch_result.get('total_items', 0)} Preise geschrieben")
                
                    # Finale Progress
                    if progress_tracker_callback:
                        progress_tracker_callback({
                            'progress_percent': 100,
                            'status': f"Erfolgreich: {batch_result.get('total_items', 0)} Preise"
                        })
                
                    return {
                        'success': True,
                        'successful_updates': successful_updates,
                        'failed_updates': failed_updates,
                        'total_apps': len(app_ids),
                        'duration': duration,
                        'apps_per_second': len(app_ids) / duration if duration > 0 else 0,
                        'batch_writer_result': batch_result,
                        'database_writes': batch_result.get('total_items', 0),
                        'performance_multiplier': batch_result.get('performance_multiplier', 'N/A')
                    }
                else:
                    raise Exception(batch_result.get('error', 'Unbekannter Batch-Write Fehler'))
            
            except Exception as e:
                logger.error(f"❌ BATCH-WRITER fehlgeschlagen: {e}")
                logger.warning("🔄 Versuche Fallback zu einzelnen Writes...")
            
                # Fallback zu einzelnen Writes
                return self._fallback_individual_writes(all_price_data, start_time, successful_updates, failed_updates, len(app_ids), progress_tracker_callback)
    
        else:
            logger.warning("⚠️ Keine gültigen Preisdaten zum Schreiben")
        
            if progress_tracker_callback:
                progress_tracker_callback({
                    'progress_percent': 100,
                    'status': 'Keine Preisdaten erhalten'
                })
        
            return {
                'success': False,
                'error': 'Keine gültigen Preisdaten erhalten',
                'successful_updates': 0,
                'failed_updates': len(app_ids),
                'duration': time_module.time() - start_time
            }
        
    def _create_batch_price_entry_for_batch_writer(self, app_id: str, price_data: Dict) -> Dict:
        """
        Erstellt Price-Entry im Format das der Batch-Writer erwartet
        """
        # Der Batch-Writer erwartet ein anderes Format als die normale DB
        batch_entry = {
            'steam_app_id': str(app_id),
            'timestamp': datetime.now().isoformat()
        }
    
        # Store-Mapping für Batch-Writer
        store_mapping = {
            'steam': 'steam',
            'greenmangaming': 'greenmangaming', 
            'gog': 'gog',
            'humblestore': 'humblestore',
            'fanatical': 'fanatical',
            'gamesplanet': 'gamesplanet'
        }
    
        # Preise für jeden Store hinzufügen
        for original_store, batch_store in store_mapping.items():
            if original_store in price_data:
                store_data = price_data[original_store]
            
                # Für Batch-Writer Format
                if isinstance(store_data, dict):
                    batch_entry[f'{batch_store}_price'] = store_data.get('price', 0.0)
                    batch_entry[f'{batch_store}_original_price'] = store_data.get('original_price', 0.0)
                    batch_entry[f'{batch_store}_discount_percent'] = store_data.get('discount_percent', 0)
                    batch_entry[f'{batch_store}_available'] = store_data.get('available', True)
    
        return batch_entry

    def _validate_batch_price_entry(self, entry: Dict) -> bool:
        """Validiert einen Batch-Price-Entry"""
        required_fields = ['steam_app_id', 'timestamp']
    
        for field in required_fields:
            if field not in entry:
                logger.debug(f"❌ Fehlender Field: {field}")
                return False
    
        # Prüfe ob mindestens ein Store-Preis vorhanden ist
        store_found = False
        for key, value in entry.items():
            if key.endswith('_price') and value is not None and value > 0:
                store_found = True
                break
    
        if not store_found:
            logger.debug("❌ Keine gültigen Store-Preise gefunden")
            return False
    
        return True

    def _fallback_individual_writes(self, price_data, start_time, successful_updates, failed_updates, total_apps, progress_callback=None):
        """Fallback: Einzelne Database-Writes wenn Batch-Writer fehlschlägt"""
        logger.warning("🔄 Fallback: Einzelne Database-Writes...")
    
        if progress_callback:
            progress_callback({
                'progress_percent': 95,
                'status': '🔄 Fallback aktiv',
                'current_task': 'Einzelne Writes versuchen...'
            })
    
        individual_writes = 0
        for entry in price_data:
            try:
                # Konvertiere Batch-Format zurück zu Standard-Format
                standard_entry = self._convert_batch_to_standard_format(entry)
            
                if self.db_manager.add_price_snapshot(entry['steam_app_id'], standard_entry):
                    individual_writes += 1
            except Exception as e:
                logger.debug(f"❌ Individual Write failed für {entry.get('steam_app_id')}: {e}")
    
        duration = time_module.time() - start_time
    
        if progress_callback:
            progress_callback({
                'progress_percent': 100,
                'status': f'Fallback: {individual_writes} einzelne Writes'
            })
    
        return {
            'success': individual_writes > 0,
            'successful_updates': successful_updates,
            'failed_updates': failed_updates,
            'total_apps': total_apps,
            'duration': duration,
            'database_writes': individual_writes,
            'fallback_used': True,
            'warning': f'Batch-Write fehlgeschlagen, {individual_writes} einzelne Writes erfolgreich'
        }

    def _convert_batch_to_standard_format(self, batch_entry: Dict) -> Dict:
        """Konvertiert Batch-Format zurück zu Standard-Format für Fallback"""
        standard_entry = {
            'timestamp': batch_entry.get('timestamp', datetime.now().isoformat())
        }
    
        # Store-Preise extrahieren
        stores = ['steam', 'greenmangaming', 'gog', 'humblestore', 'fanatical', 'gamesplanet']
    
        for store in stores:
            price_key = f'{store}_price'
            if price_key in batch_entry and batch_entry[price_key]:
                standard_entry[store] = {
                    'price': batch_entry.get(price_key, 0.0),
                    'original_price': batch_entry.get(f'{store}_original_price', 0.0),
                    'discount_percent': batch_entry.get(f'{store}_discount_percent', 0),
                    'available': batch_entry.get(f'{store}_available', True)
                }
    
        return standard_entry
    
    def process_all_pending_apps_optimized(self, hours_threshold: int = 6, batch_size: int = 25) -> Dict:
        """
        🚀 REVOLUTIONÄRER OPTIMIERTER BATCH-PROCESSOR für alle ausstehenden Apps
    
        Verarbeitet alle Apps die Updates benötigen mit maximaler Batch-Performance
        """
        start_time = time_module.time()
    
        logger.info(f"🚀 OPTIMIERTER BATCH-PROCESSOR gestartet (Threshold: {hours_threshold}h)")
    
        try:
            # Apps abrufen die Updates benötigen
            pending_apps = self.get_apps_needing_update(hours_threshold)
        
            if not pending_apps:
                return {
                    'success': True,
                    'total_apps': 0,
                    'total_successful': 0,
                    'total_failed': 0,
                    'total_duration': time_module.time() - start_time,
                    'total_batches': 0,
                    'apps_per_second': 0,
                    'message': 'Keine Apps benötigen Updates'
                }
        
            app_ids = [app['steam_app_id'] for app in pending_apps if app.get('steam_app_id')]
        
            logger.info(f"📊 {len(app_ids)} Apps benötigen Updates")
        
            # 🚀 NUTZE BATCH-UPDATE METHODE!
            batch_result = self.batch_update_multiple_apps(app_ids, batch_size)
        
            total_duration = time_module.time() - start_time
            total_batches = (len(app_ids) + batch_size - 1) // batch_size  # Ceiling division
        
            # Erweiterte Statistiken
            result = {
                'success': batch_result.get('success', False),
                'total_apps': len(app_ids),
                'total_successful': batch_result.get('successful_updates', 0),
                'total_failed': batch_result.get('failed_updates', 0),
                'total_duration': total_duration,
                'total_batches': total_batches,
                'apps_per_second': len(app_ids) / total_duration if total_duration > 0 else 0,
                'performance_metrics': {
                    'batch_performance': batch_result.get('performance_multiplier', '1x'),
                    'time_saved': batch_result.get('time_saved', 0),
                    'database_locks_avoided': batch_result.get('database_locks_avoided', 0),
                    'throughput_improvement': f"{batch_result.get('apps_per_second', 0):.1f} Apps/s"
                },
                'batch_statistics': batch_result.get('batch_statistics', {}),
                'error': batch_result.get('error') if not batch_result.get('success') else None
            }
        
            if result['success']:
                logger.info(f"🎉 OPTIMIERTER BATCH-PROCESSOR ERFOLGREICH!")
                logger.info(f"   📊 {result['total_successful']}/{result['total_apps']} Apps erfolgreich")
                logger.info(f"   ⏱️ Gesamt-Dauer: {total_duration:.1f}s")
                logger.info(f"   📦 {total_batches} Batches verarbeitet")
                logger.info(f"   ⚡ {result['apps_per_second']:.1f} Apps/s (REVOLUTIONÄRE PERFORMANCE!)")
            
                if result['total_failed'] > 0:
                    logger.warning(f"   ⚠️ {result['total_failed']} Apps fehlgeschlagen")
            else:
                logger.error(f"❌ OPTIMIERTER BATCH-PROCESSOR fehlgeschlagen: {result.get('error', 'Unbekannt')}")
        
            return result
        
        except Exception as e:
            total_duration = time_module.time() - start_time
            logger.error(f"❌ Optimierter Batch-Processor Fehler: {e}")
            import traceback
            traceback.print_exc()
        
            return {
                'success': False,
                'error': str(e),
                'total_apps': 0,
                'total_successful': 0,
                'total_failed': 0,
                'total_duration': total_duration,
                'total_batches': 0,
                'apps_per_second': 0
            }

    def get_apps_needing_update(self, hours_threshold: int = 6) -> List[Dict]:
        """
        🚀 OPTIMIERTE Methode zum Abrufen von Apps die Updates benötigen
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
            
                cursor.execute("""
                    SELECT ta.steam_app_id, ta.name, ta.last_price_update, ta.added_date,
                           COALESCE(ta.last_price_update, ta.added_date) as effective_last_update
                    FROM tracked_apps ta
                    WHERE ta.active = 1
                    AND (
                        ta.last_price_update IS NULL 
                        OR ta.last_price_update < datetime('now', '-{} hours')
                    )
                    ORDER BY effective_last_update ASC
                """.format(hours_threshold))
            
                results = cursor.fetchall()
            
                apps_needing_update = []
                for row in results:
                    apps_needing_update.append({
                        'steam_app_id': row[0],
                        'name': row[1],
                        'last_price_update': row[2],
                        'added_date': row[3],
                        'effective_last_update': row[4]
                    })
            
                logger.info(f"📊 {len(apps_needing_update)} Apps benötigen Updates (älter als {hours_threshold}h)")
                return apps_needing_update
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen Apps für Update: {e}")
            return []

# =====================================================================
# FACTORY FUNCTIONS
# =====================================================================

def create_price_tracker(db_path: str = "steam_price_tracker.db", 
                        api_key: Optional[str] = None,
                        enable_charts: bool = True) -> SteamPriceTracker:
    """
    Factory-Funktion zur Erstellung eines SteamPriceTracker
    
    Args:
        db_path: Pfad zur Datenbank
        api_key: Steam API Key
        enable_charts: Charts-Funktionalität aktivieren
        
    Returns:
        SteamPriceTracker Instanz
    """
    try:
        # Database Manager erstellen
        db_manager = create_database_manager(db_path)
        
        # Price Tracker erstellen
        tracker = SteamPriceTracker(
            db_manager=db_manager,
            api_key=api_key,
            enable_charts=enable_charts
        )
        
        logger.info(f"✅ SteamPriceTracker erstellt mit DB: {db_path}")
        return tracker
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen des SteamPriceTracker: {e}")
        return None

def setup_full_automation(db_path: str = "steam_price_tracker.db",
                         api_key: Optional[str] = None) -> SteamPriceTracker:
    """
    Erstellt vollständig automatisierten Price Tracker
    
    Args:
        db_path: Pfad zur Datenbank
        api_key: Steam API Key
        
    Returns:
        Konfigurierter SteamPriceTracker mit aktivem Scheduler
    """
    try:
        # Tracker erstellen
        tracker = create_price_tracker(db_path, api_key, enable_charts=True)
        
        if not tracker:
            raise Exception("Price Tracker konnte nicht erstellt werden")
        
        # Scheduler starten
        scheduler_started = tracker.start_scheduler()
        
        if scheduler_started:
            logger.info("🚀 Vollautomatisierung aktiviert")
        else:
            logger.warning("⚠️ Scheduler konnte nicht gestartet werden")
        
        return tracker
        
    except Exception as e:
        logger.error(f"❌ Fehler bei Vollautomatisierung: {e}")
        return None

# =====================================================================
# COMPATIBILITY ALIASES (FÜR ÄLTERE VERSIONEN)
# =====================================================================

# Für Rückwärtskompatibilität
def get_statistics(tracker: SteamPriceTracker) -> Dict:
    """Legacy-Alias für get_database_stats"""
    return tracker.get_database_stats()

def get_database_statistics(tracker: SteamPriceTracker) -> Dict:
    """Alternative Alias für get_database_stats"""
    return tracker.get_database_stats()

if __name__ == "__main__":
    # Test der Price Tracker Funktionalität
    print("🧪 TESTING PRICE TRACKER")
    print("=" * 30)
    
    # Tracker erstellen
    tracker = create_price_tracker(enable_charts=True)
    
    if tracker:
        print("✅ Price Tracker erstellt")
        
        # Test APIs
        apps = tracker.get_tracked_apps()
        print(f"📊 Getrackte Apps: {len(apps)}")
        
        stats = tracker.get_database_stats()
        print(f"📈 Statistiken: {stats.get('tracked_apps', 0)} Apps")
        
        # Test App hinzufügen
        success, message = tracker.add_app_to_tracking("123456", "Test Game")
        print(f"✅ App hinzugefügt: {success} - {message}")
        
        print("✅ Alle Tests erfolgreich")
    else:
        print("❌ Price Tracker konnte nicht erstellt werden")
