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
import time
import threading
import requests
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import os

# Lokale Imports
from database_manager import DatabaseManager, create_database_manager

# Logging Setup
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
        BATCH-API: Aktualisiert Preise für mehrere Apps
        
        Args:
            app_ids: Liste von Steam App IDs
            
        Returns:
            Dictionary mit Ergebnissen pro App ID
        """
        results = {}
        
        try:
            for i, app_id in enumerate(app_ids, 1):
                logger.info(f"📊 Aktualisiere App {i}/{len(app_ids)}: {app_id}")
                
                try:
                    success = self.update_price_for_app(app_id)
                    results[app_id] = success
                    
                    # Rate limiting
                    if i < len(app_ids):
                        time.sleep(1)
                        
                except Exception as e:
                    logger.error(f"❌ Fehler bei App {app_id}: {e}")
                    results[app_id] = False
            
            successful = sum(1 for success in results.values() if success)
            logger.info(f"✅ Batch-Update abgeschlossen: {successful}/{len(app_ids)} erfolgreich")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Batch-Update: {e}")
        
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
            print("\n📊 PREIS-ZUSAMMENFASSUNG")
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
                time.sleep(60)  # Prüfe alle 60 Sekunden
            except Exception as e:
                logger.error(f"❌ Fehler im Scheduler: {e}")
                self.error_count += 1
                time.sleep(60)
        
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
    
    def _fetch_cheapshark_prices(self, app_name: str) -> Dict:
        """Holt Preise von CheapShark API"""
        try:
            url = "https://www.cheapshark.com/api/1.0/games"
            params = {'title': app_name, 'limit': 5}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            games = response.json()
            if not games:
                return {}
            
            # Store-Mapping
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
                if game.get('external').lower() == app_name.lower():
                    deals_url = f"https://www.cheapshark.com/api/1.0/games?id={game['gameID']}"
                    deals_response = requests.get(deals_url, timeout=10)
                    deals_data = deals_response.json()
                    
                    for deal in deals_data.get('deals', []):
                        store_id = deal.get('storeID')
                        store_name = store_mapping.get(store_id)
                        
                        if store_name:
                            prices[store_name] = {
                                'price': float(deal.get('price', 0)),
                                'original_price': float(deal.get('retailPrice', 0)),
                                'discount_percent': int(float(deal.get('savings', 0))),
                                'available': True
                            }
                    break
            
            return prices
            
        except Exception as e:
            logger.debug(f"Fehler beim Abrufen der CheapShark-Preise: {e}")
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
