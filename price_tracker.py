"""
Steam Price Tracker - Hauptklasse für CheapShark-Preis-Tracking
Direkter Zugriff auf CheapShark API ohne Mapping-Komplexität
Basiert auf Projekt_SteamGoG.ipynb Logic
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
    Direkter Zugriff ohne Steam-zu-CheapShark-Mapping
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
        self.stop_scheduler = threading.Event()
        
        logger.info("✅ Steam Price Tracker initialisiert")
    
    def _wait_for_cheapshark_rate_limit(self):
        """Wartet für CheapShark API Rate Limiting"""
        time_since_last = time.time() - self.last_cheapshark_request
        if time_since_last < self.cheapshark_rate_limit:
            wait_time = self.cheapshark_rate_limit - time_since_last
            logger.debug(f"⏳ Rate Limiting: warte {wait_time:.2f}s für CheapShark API")
            time.sleep(wait_time)
        self.last_cheapshark_request = time.time()
    
    def get_game_prices_from_cheapshark(self, steam_app_id: str) -> Dict:
        """
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
    
    def track_app_prices(self, steam_app_ids: List[str]) -> Dict:
        """
        Trackt Preise für mehrere Steam Apps und speichert in Datenbank
        
        Args:
            steam_app_ids: Liste von Steam App IDs
            
        Returns:
            Dict mit Statistiken
        """
        if not steam_app_ids:
            return {'processed': 0, 'successful': 0, 'failed': 0}
        
        logger.info(f"🔄 Starte Preis-Tracking für {len(steam_app_ids)} Apps...")
        
        processed = 0
        successful = 0
        failed = 0
        
        for app_id in steam_app_ids:
            try:
                # Preise von CheapShark abrufen
                price_data = self.get_game_prices_from_cheapshark(app_id)
                
                # In Datenbank speichern
                if price_data['status'] == 'success':
                    if self.db_manager.save_price_snapshot(price_data):
                        successful += 1
                    else:
                        failed += 1
                else:
                    failed += 1
                
                processed += 1
                
                # Fortschrittsanzeige alle 10 Apps
                if processed % 10 == 0:
                    logger.info(f"📊 Fortschritt: {processed}/{len(steam_app_ids)} "
                               f"(✅ {successful}, ❌ {failed})")
                
            except Exception as e:
                logger.error(f"❌ Fehler bei App {app_id}: {e}")
                failed += 1
                processed += 1
        
        logger.info(f"🏁 Preis-Tracking abgeschlossen: {successful}/{processed} erfolgreich")
        
        return {
            'processed': processed,
            'successful': successful,
            'failed': failed,
            'timestamp': datetime.now().isoformat()
        }
    
    def add_app_to_tracking(self, steam_app_id: str, name: str = None) -> bool:
        """
        Fügt eine Steam App zum Preis-Tracking hinzu
        
        Args:
            steam_app_id: Steam App ID
            name: Optionaler Name (wird von CheapShark geholt falls None)
            
        Returns:
            True wenn erfolgreich hinzugefügt
        """
        # Prüfe ob App bereits getrackt wird
        if self.db_manager.is_app_tracked(steam_app_id):
            logger.info(f"ℹ️ App {steam_app_id} wird bereits getrackt")
            return True
        
        # Hole aktuellen Namen von CheapShark falls nicht angegeben
        if not name:
            price_data = self.get_game_prices_from_cheapshark(steam_app_id)
            name = price_data.get('game_title', f'Steam_App_{steam_app_id}')
        
        # Füge zu Tracking-Liste hinzu
        success = self.db_manager.add_tracked_app(steam_app_id, name)
        
        if success:
            logger.info(f"✅ App {name} ({steam_app_id}) zum Tracking hinzugefügt")
            
            # Hole sofort erste Preise
            price_data = self.get_game_prices_from_cheapshark(steam_app_id)
            if price_data['status'] == 'success':
                self.db_manager.save_price_snapshot(price_data)
                logger.info(f"📊 Erste Preise für {name} gespeichert")
        else:
            logger.error(f"❌ Konnte App {steam_app_id} nicht zum Tracking hinzufügen")
        
        return success
    
    def remove_app_from_tracking(self, steam_app_id: str) -> bool:
        """Entfernt eine App aus dem Preis-Tracking"""
        success = self.db_manager.remove_tracked_app(steam_app_id)
        
        if success:
            logger.info(f"✅ App {steam_app_id} aus Tracking entfernt")
        else:
            logger.error(f"❌ Konnte App {steam_app_id} nicht aus Tracking entfernen")
        
        return success
    
    def get_tracked_apps(self) -> List[Dict]:
        """Gibt alle getrackte Apps zurück"""
        return self.db_manager.get_tracked_apps()
    
    def get_price_history(self, steam_app_id: str, days_back: int = 30) -> List[Dict]:
        """
        Holt Preisverlauf für eine App
        
        Args:
            steam_app_id: Steam App ID
            days_back: Wie viele Tage zurück
            
        Returns:
            Liste von Preis-Snapshots
        """
        return self.db_manager.get_price_history(steam_app_id, days_back)
    
    def get_current_best_deals(self, limit: int = 10) -> List[Dict]:
        """
        Holt aktuelle beste Deals (höchste Rabatte)
        
        Args:
            limit: Maximale Anzahl Deals
            
        Returns:
            Liste der besten Deals
        """
        return self.db_manager.get_best_current_deals(limit)
    
    def import_steam_wishlist(self, steam_id: str, api_key: str) -> Dict:
        """
        Importiert Steam Wishlist für Preis-Tracking
        
        Args:
            steam_id: Steam User ID
            api_key: Steam API Key
            
        Returns:
            Dict mit Import-Statistiken
        """
        try:
            # Verwende vereinfachte Wishlist-Import Logic
            from steam_wishlist_manager import SteamWishlistManager
            
            manager = SteamWishlistManager(api_key)
            wishlist_data = manager.get_simple_wishlist(steam_id)
            
            if not wishlist_data:
                return {'imported': 0, 'error': 'Keine Wishlist-Daten erhalten'}
            
            imported = 0
            for item in wishlist_data:
                app_id = str(item.get('appid'))
                name = item.get('name', f'Steam_App_{app_id}')
                
                if self.add_app_to_tracking(app_id, name):
                    imported += 1
            
            logger.info(f"📥 {imported} Apps aus Steam Wishlist importiert")
            
            return {
                'imported': imported,
                'total_items': len(wishlist_data),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Wishlist-Import: {e}")
            return {'imported': 0, 'error': str(e)}
    
    # ========================
    # SCHEDULER FÜR AUTOMATISCHE PREISABFRAGEN
    # ========================
    
    def start_price_tracking_scheduler(self, interval_hours: int = 6):
        """
        Startet automatisches Preis-Tracking
        
        Args:
            interval_hours: Intervall in Stunden zwischen Preisabfragen
        """
        if self.scheduler_running:
            logger.warning("⚠️ Scheduler läuft bereits")
            return
        
        logger.info(f"🚀 Starte automatisches Preis-Tracking (alle {interval_hours}h)")
        
        # Schedule-Konfiguration
        schedule.clear()
        schedule.every(interval_hours).hours.do(self._scheduled_price_update)
        
        # Scheduler-Thread starten
        self.scheduler_running = True
        self.stop_scheduler.clear()
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("✅ Preis-Tracking Scheduler gestartet")
    
    def stop_price_tracking_scheduler(self):
        """Stoppt den automatischen Preis-Tracking Scheduler"""
        if not self.scheduler_running:
            logger.info("ℹ️ Scheduler läuft nicht")
            return
        
        logger.info("🛑 Stoppe Preis-Tracking Scheduler...")
        self.scheduler_running = False
        self.stop_scheduler.set()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        
        schedule.clear()
        logger.info("✅ Preis-Tracking Scheduler gestoppt")
    
    def _run_scheduler(self):
        """Haupt-Scheduler Loop (läuft in separatem Thread)"""
        logger.info("🔄 Preis-Tracking Scheduler-Thread gestartet")
        
        while self.scheduler_running and not self.stop_scheduler.is_set():
            try:
                schedule.run_pending()
                time.sleep(60)  # Prüfe alle 60 Sekunden
                
            except Exception as e:
                logger.error(f"❌ Scheduler-Fehler: {e}")
                time.sleep(300)  # Warte 5 Minuten bei Fehlern
        
        logger.info("🔄 Preis-Tracking Scheduler-Thread beendet")
    
    def _scheduled_price_update(self):
        """Geplante Preisabfrage für alle getrackte Apps"""
        try:
            logger.info("⏰ Starte geplante Preisabfrage...")
            
            tracked_apps = self.get_tracked_apps()
            if not tracked_apps:
                logger.info("📭 Keine Apps für Preis-Tracking konfiguriert")
                return
            
            app_ids = [app['steam_app_id'] for app in tracked_apps]
            result = self.track_app_prices(app_ids)
            
            logger.info(f"📊 Geplante Preisabfrage abgeschlossen:")
            logger.info(f"   ✅ {result['successful']} erfolgreich")
            logger.info(f"   ❌ {result['failed']} fehlgeschlagen")
            
            # Bereinige alte Preisdaten (> 90 Tage)
            self.db_manager.cleanup_old_prices(days=90)
            
        except Exception as e:
            logger.error(f"❌ Geplante Preisabfrage Fehler: {e}")
    
    def get_scheduler_status(self) -> Dict:
        """Gibt Scheduler-Status zurück"""
        tracked_count = len(self.get_tracked_apps())
        
        return {
            'scheduler_running': self.scheduler_running,
            'tracked_apps_count': tracked_count,
            'next_run': schedule.next_run() if schedule.jobs else None,
            'jobs_count': len(schedule.jobs)
        }
    
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
        """
        Exportiert Preisverlauf als CSV (Kompatibilität zu Projekt_SteamGoG.ipynb)
        
        Args:
            steam_app_id: Steam App ID
            output_file: Ausgabedatei (optional)
            
        Returns:
            Pfad zur erstellten CSV-Datei
        """
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
    
    def get_statistics(self) -> Dict:
        """Gibt Tracking-Statistiken zurück"""
        tracked_apps = self.get_tracked_apps()
        total_snapshots = self.db_manager.get_total_price_snapshots()
        
        return {
            'tracked_apps': len(tracked_apps),
            'total_price_snapshots': total_snapshots,
            'stores_tracked': list(self.STORES.values()),
            'oldest_snapshot': self.db_manager.get_oldest_snapshot_date(),
            'newest_snapshot': self.db_manager.get_newest_snapshot_date()
        }
