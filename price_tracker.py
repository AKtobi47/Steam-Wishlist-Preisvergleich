"""
Steam Price Tracker - Vollständige Implementation
CheapShark API Integration mit automatischem Scheduler
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

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SteamPriceTracker:
    """
    Steam Preis-Tracker mit CheapShark API
    Vollständige Implementation mit Scheduler und Batch-Processing
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
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SteamPriceTracker/1.0'
        })
        
        # Rate Limiting für CheapShark API
        self.last_cheapshark_request = 0
        self.cheapshark_rate_limit = 1.5  # 1.5 Sekunden zwischen Requests
        
        # Scheduler für automatische Preisabfragen
        self.scheduler_running = False
        self.scheduler_thread = None
        self.stop_scheduler_event = threading.Event()
        
        # Batch-Processing Konfiguration
        self.batch_size = 50  # Apps pro Batch
        self.max_retries = 3
        self.retry_delay = 5.0  # Sekunden
        self.processing_active = False
        
        logger.info("✅ Steam Price Tracker initialisiert")
    
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
    # SCHEDULER FUNCTIONALITY
    # ========================
    
    def get_scheduler_status(self) -> Dict:
        """
        Gibt den aktuellen Scheduler-Status zurück
        """
        status = {
            'scheduler_running': self.scheduler_running,
            'next_run': None,
            'jobs_count': len(schedule.jobs)
        }
        
        # Nächster geplanter Lauf ermitteln
        if schedule.jobs:
            try:
                next_job = min(schedule.jobs, key=lambda job: job.next_run)
                status['next_run'] = next_job.next_run.strftime('%Y-%m-%d %H:%M:%S')
            except:
                status['next_run'] = 'Unbekannt'
        
        return status
    
    def start_scheduler(self, interval_hours: int = 6):
        """
        Startet den automatischen Preis-Tracker Scheduler
        
        Args:
            interval_hours: Intervall in Stunden zwischen Updates
        """
        if self.scheduler_running:
            logger.warning("⚠️ Scheduler läuft bereits")
            return
        
        # Bestehende Jobs löschen
        schedule.clear()
        
        # Neuen Job planen
        schedule.every(interval_hours).hours.do(self._scheduled_price_update)
        
        # Scheduler-Thread starten
        self.stop_scheduler_event.clear()
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.scheduler_running = True
        logger.info(f"✅ Scheduler gestartet - Updates alle {interval_hours} Stunden")
    
    def stop_scheduler(self):
        """
        Stoppt den automatischen Scheduler
        """
        if not self.scheduler_running:
            logger.info("ℹ️ Scheduler war nicht aktiv")
            return
        
        # Signal zum Stoppen setzen
        self.stop_scheduler_event.set()
        
        # Jobs löschen
        schedule.clear()
        
        # Auf Thread-Ende warten
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        self.scheduler_running = False
        self.scheduler_thread = None
        
        logger.info("⏹️ Scheduler gestoppt")
    
    def _run_scheduler(self):
        """
        Interne Methode: Führt den Scheduler in eigenem Thread aus
        """
        logger.info("🚀 Scheduler-Thread gestartet")
        
        while not self.stop_scheduler_event.is_set():
            try:
                schedule.run_pending()
                time.sleep(60)  # Prüfe jede Minute
            except Exception as e:
                logger.error(f"❌ Scheduler-Fehler: {e}")
                time.sleep(60)
        
        logger.info("⏹️ Scheduler-Thread beendet")
    
    def _scheduled_price_update(self):
        """
        Interne Methode: Wird vom Scheduler automatisch aufgerufen
        """
        try:
            logger.info("🔄 Automatisches Preisupdate gestartet")
            
            # Alle getrackte Apps abrufen
            tracked_apps = self.get_tracked_apps()
            
            if not tracked_apps:
                logger.info("ℹ️ Keine Apps zum Tracken gefunden")
                return
            
            # App-IDs extrahieren
            app_ids = [app['steam_app_id'] for app in tracked_apps]
            
            # Preise aktualisieren
            result = self.track_app_prices(app_ids)
            
            logger.info(f"✅ Automatisches Update abgeschlossen: {result['successful']}/{result['processed']} Apps")
            
            if result['errors']:
                logger.warning(f"⚠️ {len(result['errors'])} Fehler beim automatischen Update")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim automatischen Preisupdate: {e}")
    
    # Kompatibilitäts-Methoden
    def start_price_tracking_scheduler(self, interval_hours: int = 6):
        """Alias für start_scheduler() für Kompatibilität"""
        return self.start_scheduler(interval_hours)
    
    def stop_price_tracking_scheduler(self):
        """Alias für stop_scheduler() für Kompatibilität"""
        return self.stop_scheduler()
    
    # ========================
    # DATA RETRIEVAL
    # ========================
    
    def get_statistics(self) -> Dict:
        """Gibt Tracker-Statistiken zurück"""
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
    
    def import_steam_wishlist(self, steam_id: str, api_key: str) -> Dict:
        """
        Importiert Steam Wishlist (vereinfacht)
        
        Args:
            steam_id: Steam ID des Benutzers
            api_key: Steam API Key
            
        Returns:
            Dict mit Import-Statistiken
        """
        try:
            from steam_wishlist_manager import SteamWishlistManager
            
            wishlist_manager = SteamWishlistManager(api_key)
            wishlist_data = wishlist_manager.get_simple_wishlist(steam_id)
            
            if not wishlist_data:
                return {'success': False, 'error': 'Wishlist konnte nicht abgerufen werden'}
            
            imported = 0
            skipped_existing = 0
            errors = []
            
            for item in wishlist_data:
                try:
                    app_id = item['steam_app_id']
                    name = item['name']
                    
                    # Prüfe ob bereits vorhanden
                    existing_apps = self.get_tracked_apps()
                    if any(app['steam_app_id'] == app_id for app in existing_apps):
                        skipped_existing += 1
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
                'total_items': len(wishlist_data),
                'errors': errors,
                'import_completed_at': datetime.now().isoformat()
            }
            
            logger.info(f"📥 Wishlist-Import abgeschlossen:")
            logger.info(f"   ✅ {imported} neue Apps hinzugefügt")
            logger.info(f"   ⏭️ {skipped_existing} bereits vorhanden")
            logger.info(f"   📊 {imported + skipped_existing}/{len(wishlist_data)} Apps verarbeitet")
            
            if errors:
                logger.warning(f"   ⚠️ {len(errors)} Fehler aufgetreten")
            
            return import_stats
            
        except ImportError:
            logger.error("❌ SteamWishlistManager nicht verfügbar")
            return {'success': False, 'error': 'SteamWishlistManager nicht verfügbar'}
        except Exception as e:
            logger.error(f"❌ Fehler beim Wishlist-Import: {e}")
            return {
                'success': False,
                'imported': 0,
                'total_items': 0,
                'error': str(e)
            }