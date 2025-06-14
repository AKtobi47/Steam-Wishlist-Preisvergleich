"""
Steam Price Tracker - Erweiterte Version mit Batch-Processing
Behält die bewährte CheapShark-Logic bei und erweitert um optimiertes Batch-Processing
Basiert auf der funktionierenden price_tracker.py Implementation
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
    Erweitert um intelligentes Batch-Processing bei Beibehaltung der bewährten Preisabfrage-Logic
    """
    
    # Store-Konfiguration basierend auf Projekt_SteamGoG.ipynb (BEWÄHRT)
    STORES = {
        "1": "Steam",
        "3": "GreenManGaming", 
        "7": "GOG",
        "11": "HumbleStore",
        "15": "Fanatical",
        "27": "GamesPlanet"
    }
    
    # Store IDs als String für CheapShark API (BEWÄHRT)
    STORE_IDS = "1,3,7,11,15,27"
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SteamPriceTracker/1.0'
        })
        
        # Rate Limiting für CheapShark API (BEWÄHRT)
        self.last_cheapshark_request = 0
        self.cheapshark_rate_limit = 1.5  # 1.5 Sekunden zwischen Requests
        
        # Scheduler für automatische Preisabfragen
        self.scheduler_running = False
        self.scheduler_thread = None
        self.stop_scheduler = threading.Event()
        
        # NEUE: Batch-Processing Konfiguration
        self.batch_size = 50  # Apps pro Batch
        self.max_retries = 3
        self.retry_delay = 5.0  # Sekunden
        self.processing_active = False
        
        logger.info("✅ Steam Price Tracker initialisiert")
    
    def _wait_for_cheapshark_rate_limit(self):
        """Wartet für CheapShark API Rate Limiting (BEWÄHRT)"""
        time_since_last = time.time() - self.last_cheapshark_request
        if time_since_last < self.cheapshark_rate_limit:
            wait_time = self.cheapshark_rate_limit - time_since_last
            logger.debug(f"⏳ Rate Limiting: warte {wait_time:.2f}s für CheapShark API")
            time.sleep(wait_time)
        self.last_cheapshark_request = time.time()
    
    def get_game_prices_from_cheapshark(self, steam_app_id: str) -> Dict:
        """
        *** BEWÄHRTE PREISABFRAGE-LOGIC - UNVERÄNDERT ***
        Holt aktuelle Preise für Steam App ID von CheapShark
        Basiert direkt auf Projekt_SteamGoG.ipynb Logic
        
        Args:
            steam_app_id: Steam App ID (als String)
            
        Returns:
            Dict mit Preisinformationen pro Store
        """
        # Rate Limiting anwenden
        self._wait_for_cheapshark_rate_limit()
        
        url = f"https://www.cheapshark.com/api/1.0/deals"
        params = {
            'storeID': self.STORE_IDS,
            'steamAppID': steam_app_id
        }
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if not data:
                    logger.debug(f"📭 Keine Preisdaten für Steam App {steam_app_id}")
                    return {
                        'steam_app_id': steam_app_id,
                        'game_title': None,
                        'prices': {},
                        'timestamp': datetime.now().isoformat(),
                        'status': 'no_data'
                    }
                
                # Game Title aus erstem Deal extrahieren
                game_title = data[0].get('title', f'Steam_App_{steam_app_id}')
                
                # Preise pro Store sammeln
                prices = {}
                for store_id, store_name in self.STORES.items():
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
                
                logger.info(f"✅ Preise für {game_title} abgerufen")
                
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
                'status': f'request_error'
            }
    
    # ========================
    # BEWÄHRTE EINZELN-VERARBEITUNG (kompatibel)
    # ========================
    
    def track_app_prices(self, steam_app_ids: List[str]) -> Dict:
        """
        Trackt Preise für mehrere Steam Apps (BEWÄHRT)
        Kann sowohl einzeln als auch in Batches verwendet werden
        
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
                # Verwende die BEWÄHRTE Preisabfrage-Logic
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
        
        result = {
            'processed': processed,
            'successful': successful,
            'failed': failed,
            'errors': errors
        }
        
        logger.info(f"📊 Preis-Tracking abgeschlossen: {successful}/{processed} erfolgreich")
        
        return result
    
    # ========================
    # NEUE: OPTIMIERTES BATCH-PROCESSING
    # ========================
    
    def process_app_batch_optimized(self, app_batch: List[Dict]) -> Dict:
        """
        NEUE: Optimierte Batch-Verarbeitung mit Retry-Logic
        Verwendet die bewährte get_game_prices_from_cheapshark() Methode
        
        Args:
            app_batch: Liste von App-Dicts mit steam_app_id und name
            
        Returns:
            Dict mit Batch-Statistiken
        """
        batch_start = time.time()
        batch_size = len(app_batch)
        
        logger.info(f"📦 Starte optimierte Batch-Verarbeitung: {batch_size} Apps")
        
        successful = 0
        failed = 0
        errors = []
        
        for i, app in enumerate(app_batch, 1):
            app_id = app['steam_app_id']
            app_name = app['name']
            
            logger.info(f"⚙️ [{i}/{batch_size}] Verarbeite: {app_name} (ID: {app_id})")
            
            # Preise abrufen mit Retry-Logic
            price_data = None
            for retry in range(self.max_retries):
                # Verwende die BEWÄHRTE Preisabfrage-Methode
                price_data = self.get_game_prices_from_cheapshark(app_id)
                
                if price_data.get('status') == 'success':
                    break
                elif retry < self.max_retries - 1:
                    logger.warning(f"🔄 Retry {retry + 1}/{self.max_retries} für App {app_id}")
                    time.sleep(self.retry_delay)
            
            if price_data and price_data.get('status') == 'success':
                # Speichere in Datenbank
                if self.db_manager.save_price_snapshot(
                    price_data['steam_app_id'],
                    price_data['game_title'],
                    price_data['prices']
                ):
                    successful += 1
                    
                    # Update last_price_update
                    self.db_manager.update_app_last_price_update(app_id)
                    
                    logger.debug(f"✅ App {app_id} erfolgreich verarbeitet")
                else:
                    failed += 1
                    errors.append(f"Database error for {app_id}")
                    logger.error(f"❌ Datenbank-Fehler für App {app_id}")
            else:
                failed += 1
                error_msg = price_data.get('status', 'Unknown error') if price_data else 'No response'
                errors.append(f"{app_id}: {error_msg}")
                logger.error(f"❌ Preisabruf fehlgeschlagen für App {app_id}: {error_msg}")
        
        batch_duration = time.time() - batch_start
        
        batch_stats = {
            'batch_size': batch_size,
            'successful': successful,
            'failed': failed,
            'errors': errors,
            'duration_seconds': round(batch_duration, 2),
            'apps_per_second': round(batch_size / batch_duration, 2) if batch_duration > 0 else 0
        }
        
        logger.info(f"📦 Batch abgeschlossen: {successful}/{batch_size} erfolgreich in {batch_duration:.1f}s")
        
        return batch_stats
    
    def get_apps_needing_price_update(self, hours_threshold: int = 6) -> List[Dict]:
        """
        NEUE: Holt Apps die ein Preisupdate benötigen
        
        Args:
            hours_threshold: Apps älter als X Stunden
            
        Returns:
            Liste von Apps die Updates benötigen
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_threshold)
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT steam_app_id, name, last_price_update
                FROM tracked_apps 
                WHERE active = 1 
                AND (last_price_update IS NULL OR last_price_update < ?)
                ORDER BY 
                    CASE WHEN last_price_update IS NULL THEN 0 ELSE 1 END,
                    last_price_update ASC
            ''', (cutoff_time.isoformat(),))
            
            apps = [dict(row) for row in cursor.fetchall()]
            
        logger.info(f"📊 {len(apps)} Apps benötigen Preisupdate (älter als {hours_threshold}h)")
        
        return apps
    
    def process_all_pending_apps_optimized(self, hours_threshold: int = 6) -> Dict:
        """
        NEUE: Verarbeitet alle Apps die Updates benötigen - OPTIMIERT
        
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
                    'apps_per_second': 0
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
                
                batch_stats = self.process_app_batch_optimized(batch)
                
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
            logger.info(f"   📊 {total_successful}/{total_apps} Apps erfolgreich")
            logger.info(f"   ⏱️ Dauer: {total_duration:.1f}s ({final_stats['apps_per_second']:.1f} Apps/s)")
            logger.info(f"   📦 {len(batches)} Batches verarbeitet")
            
            if total_failed > 0:
                logger.warning(f"   ⚠️ {total_failed} Apps fehlgeschlagen")
            
            return final_stats
            
        except Exception as e:
            logger.error(f"❌ Optimierte Verarbeitung fehlgeschlagen: {e}")
            return {'success': False, 'error': str(e)}
            
        finally:
            self.processing_active = False
    
    def process_specific_apps_optimized(self, app_ids: List[str]) -> Dict:
        """
        NEUE: Verarbeitet spezifische Apps optimiert
        
        Args:
            app_ids: Liste von Steam App IDs
            
        Returns:
            Dict mit Statistiken
        """
        if self.processing_active:
            logger.warning("⚠️ Processing bereits aktiv")
            return {'error': 'Processing already active'}
        
        self.processing_active = True
        
        try:
            logger.info(f"🎯 Verarbeite {len(app_ids)} spezifische Apps (optimiert)")
            
            # App-Details aus Datenbank holen
            apps = []
            for app_id in app_ids:
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        'SELECT steam_app_id, name FROM tracked_apps WHERE steam_app_id = ? AND active = 1',
                        (app_id,)
                    )
                    result = cursor.fetchone()
                    
                    if result:
                        apps.append(dict(result))
                    else:
                        logger.warning(f"⚠️ App {app_id} nicht in Tracking gefunden")
            
            if not apps:
                logger.warning("❌ Keine gültigen Apps zum Verarbeiten gefunden")
                return {'total_apps': 0, 'total_successful': 0, 'total_failed': 0}
            
            # Verarbeite als optimierten Batch
            return self.process_app_batch_optimized(apps)
            
        except Exception as e:
            logger.error(f"❌ Spezifische Verarbeitung fehlgeschlagen: {e}")
            return {'success': False, 'error': str(e)}
            
        finally:
            self.processing_active = False
    
    # ========================
    # BEWÄHRTE METHODEN (unverändert)
    # ========================
    
    def add_app_to_tracking(self, steam_app_id: str, name: str) -> bool:
        """Fügt eine App zum Tracking hinzu (BEWÄHRT)"""
        return self.db_manager.add_tracked_app(steam_app_id, name)
    
    def remove_app_from_tracking(self, steam_app_id: str) -> bool:
        """Entfernt eine App aus dem Tracking (BEWÄHRT)"""
        return self.db_manager.remove_tracked_app(steam_app_id)
    
    def get_tracked_apps(self) -> List[Dict]:
        """Gibt alle getrackte Apps zurück (BEWÄHRT)"""
        return self.db_manager.get_tracked_apps()
    
    def get_price_history(self, steam_app_id: str, days_back: int = 30) -> List[Dict]:
        """Holt Preisverlauf für eine App (BEWÄHRT)"""
        return self.db_manager.get_price_history(steam_app_id, days_back)
    
    def get_current_best_deals(self, limit: int = 10) -> List[Dict]:
        """Holt aktuelle beste Deals (BEWÄHRT)"""
        return self.db_manager.get_best_current_deals(limit)
    
    def get_statistics(self) -> Dict:
        """Gibt Tracking-Statistiken zurück (ERWEITERT)"""
        tracked_apps = self.get_tracked_apps()
        total_snapshots = self.db_manager.get_total_price_snapshots()
        
        # NEUE: Zusätzliche Statistiken
        processing_stats = self.db_manager.get_tracking_statistics()
        
        return {
            'tracked_apps': len(tracked_apps),
            'total_price_snapshots': total_snapshots,
            'stores_tracked': list(self.STORES.values()),
            'oldest_snapshot': self.db_manager.get_oldest_snapshot_date(),
            'newest_snapshot': self.db_manager.get_newest_snapshot_date(),
            'processing_active': self.processing_active,
            **processing_stats
        }
    
    def import_steam_wishlist(self, steam_id: str, api_key: str) -> Dict:
        """
        Importiert Steam Wishlist OHNE sofortiges Preisfetching (OPTIMIERT)
        Speichert nur Apps in Datenbank für späteres Batch-Processing
        
        Args:
            steam_id: Steam User ID
            api_key: Steam API Key
            
        Returns:
            Dict mit Import-Statistiken
        """
        try:
            logger.info(f"📥 Starte optimierten Wishlist-Import für Steam ID: {steam_id}")
            
            # Verwende offizielle Wishlist API
            from steam_wishlist_manager import SteamWishlistManager
            
            manager = SteamWishlistManager(api_key)
            wishlist_data = manager.get_simple_wishlist(steam_id)
            
            if not wishlist_data:
                return {
                    'success': False,
                    'imported': 0,
                    'total_items': 0,
                    'error': 'Keine Wishlist-Daten erhalten'
                }
            
            logger.info(f"📋 {len(wishlist_data)} Wishlist-Items gefunden")
            
            # Apps in Datenbank speichern (OHNE Preise)
            imported = 0
            skipped_existing = 0
            errors = []
            
            for item in wishlist_data:
                app_id = str(item.get('appid'))
                name = item.get('name', f'Steam_App_{app_id}')
                
                try:
                    # Prüfe ob App bereits getrackt wird
                    if self.db_manager.is_app_tracked(app_id):
                        skipped_existing += 1
                        logger.debug(f"⏭️ App {name} bereits getrackt - überspringe")
                        continue
                    
                    # App zur Datenbank hinzufügen
                    if self.db_manager.add_tracked_app(app_id, name):
                        imported += 1
                        logger.debug(f"✅ App {name} hinzugefügt")
                    else:
                        errors.append(f"Database error for {app_id}: {name}")
                        logger.warning(f"⚠️ Konnte App {name} nicht hinzufügen")
                        
                except Exception as e:
                    errors.append(f"Error processing {app_id}: {str(e)}")
                    logger.error(f"❌ Fehler bei App {app_id}: {e}")
            
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
            
            # WICHTIG: Empfehlung für Preisfetching ausgeben
            if imported > 0:
                logger.info("💡 NÄCHSTE SCHRITTE für Preisfetching:")
                logger.info("   1. Alle neuen Apps: tracker.process_all_pending_apps_optimized()")
                logger.info("   2. Nur neue Apps: tracker.process_specific_apps_optimized([app_ids])")
                logger.info("   3. Via CLI: python processor_runner_cli.py run")
            
            return import_stats
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Wishlist-Import: {e}")
            return {
                'success': False,
                'imported': 0,
                'total_items': 0,
                'error': str(e)
            }
    
    # ========================
    # UTILITY METHODS (BEWÄHRT)
    # ========================
    
    def print_price_summary(self, steam_app_id: str):
        """Zeigt Preis-Zusammenfassung für eine App (BEWÄHRT)"""
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
                original = price_info['original_price']
                discount = price_info['discount_percent']
                
                if discount > 0:
                    print(f"{store_name:15}: €{price:.2f} (war €{original:.2f}, -{discount}%)")
                else:
                    print(f"{store_name:15}: €{price:.2f}")
            else:
                print(f"{store_name:15}: Nicht verfügbar")
        
        print(f"Abgerufen: {price_data['timestamp']}")
    
    def export_price_history_csv(self, steam_app_id: str, output_file: str = None) -> str:
        """Exportiert Preisverlauf als CSV (BEWÄHRT)"""
        import csv
        
        price_history = self.get_price_history(steam_app_id, days_back=365)
        
        if not price_history:
            logger.error(f"❌ Keine Preisdaten für Export von App {steam_app_id}")
            return None
        
        # Filename basierend auf App
        if not output_file:
            app_name = price_history[0]['game_title']
            safe_name = "".join(c for c in app_name if c.isalnum())
            output_file = f"{safe_name}_{steam_app_id}.csv"
        
        output_path = Path("exports") / output_file
        output_path.parent.mkdir(exist_ok=True)
        
        # CSV schreiben (Format wie Projekt_SteamGoG.ipynb)
        with open(output_path, 'w', newline='', encoding='utf-8') as file:
            fieldnames = ['date'] + list(self.STORES.values())
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for snapshot in price_history:
                row = {'date': snapshot['timestamp'][:10]}  # Nur Datum
                
                for store_name in self.STORES.values():
                    price_info = snapshot['prices'].get(store_name, {})
                    row[store_name] = price_info.get('price', '') if price_info.get('available') else ''
                
                writer.writerow(row)
        
        logger.info(f"📄 Preisverlauf exportiert: {output_path}")
        return str(output_path)