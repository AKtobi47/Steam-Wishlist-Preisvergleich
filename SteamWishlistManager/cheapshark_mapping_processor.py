"""
CheapShark Mapping Processor - Aktualisierte Version
Mit integriertem Scheduler und DatabaseManager Integration
"""

import requests
import time
import threading
import schedule
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import logging
from database_manager import DatabaseManager

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CheapSharkMappingProcessor:
    """
    Verknüpft Steam Apps mit CheapShark Game IDs
    Mit automatischem Scheduler für kontinuierliche Verarbeitung
    """
    
    def __init__(self, api_key: str, db_manager: DatabaseManager = None):
        self.api_key = api_key
        self.db_manager = db_manager or DatabaseManager()
        self.cheapshark_base_url = "https://www.cheapshark.com/api/1.0"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SteamWishlistManager/2.0'
        })
        self.last_cheapshark_request = 0
        
        # Scheduler
        self.scheduler_running = False
        self.scheduler_thread = None
        self.stop_scheduler = threading.Event()
    
    def get_cheapshark_mapping_for_app_id(self, steam_app_id: str) -> Dict:
        """
        Holt CheapShark-Mapping für eine Steam App ID
        Mit Rate Limiting für CheapShark API
        """
        # Rate Limiting für CheapShark API
        time_since_last = time.time() - self.last_cheapshark_request
        if time_since_last < 1.5:  # 1 Request alle 1.5 Sekunden
            time.sleep(1.5 - time_since_last)
        
        url = f"{self.cheapshark_base_url}/games"
        params = {'steamAppID': str(steam_app_id)}
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            self.last_cheapshark_request = time.time()
            
            if response.status_code == 200:
                games = response.json()
                if games and len(games) > 0:
                    game = games[0]  # Nimm das erste Ergebnis
                    
                    # Zusätzliche Details abrufen falls verfügbar
                    cheapshark_game_id = game.get('gameID')
                    additional_data = self.get_cheapshark_game_details(cheapshark_game_id) if cheapshark_game_id else {}
                    
                    return {
                        'app_id': steam_app_id,
                        'cheapshark_game_id': cheapshark_game_id,
                        'thumb_url': game.get('thumb'),
                        'cheapest_price_ever': additional_data.get('cheapest_price_ever'),
                        'cheapest_store': additional_data.get('cheapest_store'),
                        'deals_count': additional_data.get('deals_count', 0),
                        'found': True
                    }
                else:
                    return {
                        'app_id': steam_app_id,
                        'found': False,
                        'error': 'No mapping found'
                    }
            else:
                return {
                    'app_id': steam_app_id,
                    'found': False,
                    'error': f"HTTP {response.status_code}"
                }
                
        except requests.RequestException as e:
            return {
                'app_id': steam_app_id,
                'found': False,
                'error': str(e)
            }
    
    def get_cheapshark_game_details(self, cheapshark_game_id: str) -> Dict:
        """Ruft detaillierte Informationen zu einem CheapShark Game ab"""
        if not cheapshark_game_id:
            return {}
            
        url = f"{self.cheapshark_base_url}/games"
        params = {'id': cheapshark_game_id}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                cheapest_data = data.get('cheapestPriceEver', {})
                
                return {
                    'cheapest_price_ever': float(cheapest_data.get('price', 0)) if cheapest_data.get('price') else None,
                    'cheapest_store': cheapest_data.get('store'),
                    'deals_count': len(data.get('deals', []))
                }
            
            return {}
                
        except (requests.RequestException, ValueError, TypeError):
            return {}
    
    def process_single_app_mapping(self, app_id: str) -> bool:
        """Verarbeitet CheapShark-Mapping für eine einzelne App"""
        try:
            # CheapShark-Mapping abrufen
            cheapshark_data = self.get_cheapshark_mapping_for_app_id(app_id)
            
            if cheapshark_data.get('found'):
                # Mapping in Datenbank speichern
                success = self.db_manager.add_cheapshark_mapping(cheapshark_data)
                if success:
                    logger.info(f"✅ Mapping für App {app_id} erfolgreich gespeichert")
                    return True
                else:
                    logger.error(f"❌ Fehler beim Speichern des Mappings für App {app_id}")
            else:
                # Fehlschlag markieren
                self.db_manager.mark_cheapshark_attempt_failed(app_id, cheapshark_data.get('error'))
                logger.info(f"❌ Kein Mapping für App {app_id} gefunden: {cheapshark_data.get('error')}")
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Unerwarteter Fehler bei App {app_id}: {e}")
            self.db_manager.mark_cheapshark_attempt_failed(app_id, str(e))
            return False
    
    def process_mapping_queue_batch(self, batch_size: int = 10) -> Dict:
        """
        Verarbeitet eine Batch von Jobs aus der Mapping Queue
        """
        # Nächste Jobs aus Queue holen
        jobs = self.db_manager.get_next_mapping_jobs(batch_size)
        
        if not jobs:
            return {'processed': 0, 'successful': 0, 'failed': 0}
        
        logger.info(f"🔄 Verarbeite {len(jobs)} CheapShark-Mapping Jobs...")
        
        processed = 0
        successful = 0
        failed = 0
        
        for job in jobs:
            job_id = job['id']
            app_id = job['app_id']
            
            # Job als "in Bearbeitung" markieren
            self.db_manager.update_mapping_job_status(job_id, 'processing')
            
            try:
                # Mapping verarbeiten
                if self.process_single_app_mapping(app_id):
                    self.db_manager.update_mapping_job_status(job_id, 'completed')
                    successful += 1
                    logger.info(f"✅ Job {job_id} (App {app_id}) erfolgreich")
                else:
                    self.db_manager.update_mapping_job_status(job_id, 'failed', "Mapping nicht gefunden")
                    failed += 1
                    logger.info(f"❌ Job {job_id} (App {app_id}) fehlgeschlagen")
                
                processed += 1
                
            except Exception as e:
                self.db_manager.update_mapping_job_status(job_id, 'failed', str(e))
                failed += 1
                processed += 1
                logger.error(f"❌ Job {job_id} (App {app_id}) Fehler: {e}")
        
        result = {
            'processed': processed,
            'successful': successful,
            'failed': failed,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"📊 Batch-Verarbeitung abgeschlossen: {successful}/{processed} erfolgreich")
        return result
    
    def add_missing_apps_to_queue(self, app_ids: List[str], priority: int = 5) -> int:
        """
        Fügt fehlende Apps zur CheapShark-Mapping Queue hinzu
        """
        if not app_ids:
            return 0
        
        # Filtere Apps die bereits gemappt sind oder in der Queue stehen
        apps_to_add = []
        for app_id in app_ids:
            if not self.db_manager.get_cheapshark_mapping(app_id):
                apps_to_add.append(app_id)
        
        if not apps_to_add:
            logger.info("📋 Alle Apps sind bereits gemappt oder in der Queue")
            return 0
        
        added_count = self.db_manager.add_to_mapping_queue(apps_to_add, priority)
        logger.info(f"📝 {added_count}/{len(apps_to_add)} Apps zur Mapping Queue hinzugefügt")
        
        return added_count
    
    def process_wishlist_apps_priority(self, steam_id: str) -> int:
        """
        Fügt Wishlist-Apps mit hoher Priorität zur Mapping Queue hinzu
        """
        logger.info(f"🎯 Verarbeite Wishlist-Apps für User {steam_id} mit hoher Priorität...")
        
        # Hole Wishlist-Items ohne CheapShark-Mapping
        wishlist_items = self.db_manager.get_wishlist_items(steam_id, include_cheapshark=True)
        
        apps_to_map = []
        for item in wishlist_items:
            if not item.get('cheapshark_game_id'):
                apps_to_map.append(item['app_id'])
        
        if apps_to_map:
            # Hohe Priorität für Wishlist-Apps
            added_count = self.add_missing_apps_to_queue(apps_to_map, priority=8)
            logger.info(f"🎯 {added_count} Wishlist-Apps zur Priority-Queue hinzugefügt")
            return added_count
        else:
            logger.info("✅ Alle Wishlist-Apps sind bereits gemappt")
            return 0
    
    # ========================
    # SCHEDULER FUNCTIONALITY
    # ========================
    
    def start_background_scheduler(self, 
                                 batch_size: int = 10,
                                 interval_minutes: int = 10,
                                 cleanup_interval_hours: int = 24):
        """
        Startet Background-Scheduler für automatisches CheapShark-Mapping
        """
        if self.scheduler_running:
            logger.warning("⚠️ Scheduler läuft bereits")
            return
        
        logger.info(f"🚀 Starte CheapShark-Mapping Scheduler...")
        logger.info(f"   📊 Batch-Größe: {batch_size}")
        logger.info(f"   ⏱️ Intervall: {interval_minutes} Minuten")
        logger.info(f"   🧹 Bereinigung: alle {cleanup_interval_hours} Stunden")
        
        # Schedule-Konfiguration
        schedule.clear()  # Vorherige Jobs löschen
        
        # Hauptverarbeitung
        schedule.every(interval_minutes).minutes.do(
            lambda: self._scheduled_mapping_job(batch_size)
        )
        
        # Bereinigung
        schedule.every(cleanup_interval_hours).hours.do(self._scheduled_cleanup_job)
        
        # Scheduler-Thread starten
        self.scheduler_running = True
        self.stop_scheduler.clear()
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("✅ Background-Scheduler gestartet")
    
    def stop_background_scheduler(self):
        """Stoppt den Background-Scheduler"""
        if not self.scheduler_running:
            logger.info("ℹ️ Scheduler läuft nicht")
            return
        
        logger.info("🛑 Stoppe Background-Scheduler...")
        self.scheduler_running = False
        self.stop_scheduler.set()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        
        schedule.clear()
        logger.info("✅ Background-Scheduler gestoppt")
    
    def _run_scheduler(self):
        """Haupt-Scheduler Loop (läuft in separatem Thread)"""
        logger.info("🔄 Scheduler-Thread gestartet")
        
        while self.scheduler_running and not self.stop_scheduler.is_set():
            try:
                schedule.run_pending()
                time.sleep(30)  # Prüfe alle 30 Sekunden
                
            except Exception as e:
                logger.error(f"❌ Scheduler-Fehler: {e}")
                time.sleep(60)  # Warte eine Minute bei Fehlern
        
        logger.info("🔄 Scheduler-Thread beendet")
    
    def _scheduled_mapping_job(self, batch_size: int):
        """Geplante Mapping-Verarbeitung"""
        try:
            logger.info("⏰ Starte geplante CheapShark-Mapping Verarbeitung...")
            
            result = self.process_mapping_queue_batch(batch_size)
            
            if result['processed'] > 0:
                logger.info(f"📊 Scheduler-Job abgeschlossen: {result['successful']}/{result['processed']} erfolgreich")
            else:
                logger.info("📭 Keine Jobs in der Queue")
                
        except Exception as e:
            logger.error(f"❌ Scheduler-Job Fehler: {e}")
    
    def _scheduled_cleanup_job(self):
        """Geplante Bereinigung"""
        try:
            logger.info("⏰ Starte geplante Datenbank-Bereinigung...")
            self.db_manager.cleanup_old_data(days=7)
            logger.info("✅ Bereinigung abgeschlossen")
            
        except Exception as e:
            logger.error(f"❌ Bereinigungsfehler: {e}")
    
    def get_scheduler_status(self) -> Dict:
        """Gibt Scheduler-Status zurück"""
        queue_stats = self.db_manager.get_database_stats()['queue']
        
        return {
            'scheduler_running': self.scheduler_running,
            'pending_jobs': queue_stats['pending'],
            'failed_jobs': queue_stats['failed'],
            'next_run': schedule.next_run() if schedule.jobs else None,
            'jobs_count': len(schedule.jobs)
        }
    
    # ========================
    # MANUAL PROCESSING
    # ========================
    
    def process_mapping_manual(self, max_apps: int = None, batch_size: int = 50) -> Dict:
        """
        Manuelle Verarbeitung aller unmapped Apps
        Für einmalige große Verarbeitung
        """
        print("🔄 MANUELLE CHEAPSHARK-MAPPING VERARBEITUNG")
        print("=" * 60)
        
        unmapped_apps = self.db_manager.get_apps_without_cheapshark_mapping(max_apps or 100000)
        total_to_process = len(unmapped_apps)
        
        if total_to_process == 0:
            print("✅ Alle Apps haben bereits CheapShark-Mappings!")
            return {'processed': 0, 'successful': 0, 'failed': 0}
        
        print(f"📊 Apps ohne CheapShark-Mapping: {total_to_process:,}")
        
        if max_apps:
            total_to_process = min(total_to_process, max_apps)
            unmapped_apps = unmapped_apps[:total_to_process]
        
        print(f"🎯 Verarbeite: {total_to_process:,} Apps")
        
        # Erst Apps zur Queue hinzufügen
        app_ids = [app['app_id'] for app in unmapped_apps]
        added_to_queue = self.add_missing_apps_to_queue(app_ids, priority=5)
        
        print(f"📝 {added_to_queue} Apps zur Queue hinzugefügt")
        
        # Dann verarbeiten
        processed = 0
        successful = 0
        failed = 0
        
        start_time = time.time()
        
        while processed < total_to_process:
            # Batch verarbeiten
            result = self.process_mapping_queue_batch(batch_size)
            
            if result['processed'] == 0:
                print("📭 Keine weiteren Jobs in der Queue")
                break
            
            processed += result['processed']
            successful += result['successful']
            failed += result['failed']
            
            # Fortschrittsanzeige
            if processed % 100 == 0:
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                remaining = (total_to_process - processed) / rate if rate > 0 else 0
                
                print(f"📊 {processed}/{total_to_process} "
                      f"({(processed/total_to_process)*100:.1f}%) | "
                      f"Erfolgreich: {successful} | "
                      f"Rate: {rate:.1f}/min | "
                      f"Verbleibend: {remaining/60:.1f}min")
        
        # Abschluss-Statistiken
        elapsed_time = time.time() - start_time
        
        print(f"\n🏁 MANUELLE VERARBEITUNG ABGESCHLOSSEN")
        print(f"⏱️ Dauer: {elapsed_time/60:.1f} Minuten")
        print(f"📊 Verarbeitet: {processed:,} Apps")
        print(f"✅ Erfolgreich: {successful:,} CheapShark-Mappings")
        print(f"❌ Fehlgeschlagen: {failed:,} Apps")
        print(f"📈 Erfolgsrate: {(successful/processed)*100:.1f}%")
        
        return {
            'processed': processed,
            'successful': successful,
            'failed': failed,
            'time_minutes': elapsed_time / 60,
            'success_rate': (successful/processed)*100 if processed > 0 else 0
        }

def cheapshark_processor_main():
    """
    Hauptfunktion für CheapShark-Mapping Processor
    """
    print("🔗 CHEAPSHARK MAPPING PROCESSOR v2.0")
    print("Mit Background-Scheduler und DatabaseManager Integration")
    print("=" * 70)
    
    # API Key laden
    try:
        from steam_wishlist_manager import load_api_key_from_env
        api_key = load_api_key_from_env()
    except ImportError:
        api_key = input("Steam API Key eingeben: ").strip()
    
    if not api_key:
        print("❌ Kein Steam API Key gefunden")
        return
    
    print("✅ API Key geladen")
    
    # Database Manager und Processor erstellen
    db_manager = DatabaseManager()
    processor = CheapSharkMappingProcessor(api_key, db_manager)
    
    # Aktuelle Statistiken zeigen
    print("\n📊 AKTUELLE MAPPING-STATISTIKEN:")
    stats = db_manager.get_database_stats()
    
    print(f"📚 Gesamt Apps: {stats['apps']['total']:,}")
    print(f"✅ Mit CheapShark-Mapping: {stats['cheapshark']['mapped']:,}")
    print(f"❌ Ohne Mapping: {stats['cheapshark']['unmapped']:,}")
    print(f"📈 Erfolgsrate: {stats['cheapshark']['success_rate']:.1f}%")
    print(f"📋 Queue - Ausstehend: {stats['queue']['pending']:,}")
    print(f"📋 Queue - Fehlgeschlagen: {stats['queue']['failed']:,}")
    
    print("\n🔧 PROCESSOR OPTIONEN:")
    print("1. 🔄 Manuelle Verarbeitung (alle unmapped Apps)")
    print("2. ⚡ Limitierte Verarbeitung (nur X Apps)")
    print("3. 🚀 Background-Scheduler starten")
    print("4. 🛑 Background-Scheduler stoppen")
    print("5. 📊 Scheduler-Status anzeigen")
    print("6. 🎯 Wishlist-Apps priorisieren (Steam ID eingeben)")
    print("7. ❌ Beenden")
    
    choice = input("\nWählen Sie eine Option (1-7): ").strip()
    
    if choice == "1":
        print("\n🔄 Starte manuelle Verarbeitung aller Apps...")
        processor.process_mapping_manual()
        
    elif choice == "2":
        max_apps = input("Wie viele Apps verarbeiten? (Standard: 1000): ").strip()
        try:
            max_apps = int(max_apps) if max_apps else 1000
        except ValueError:
            max_apps = 1000
        
        print(f"\n🔄 Starte limitierte Verarbeitung für {max_apps} Apps...")
        processor.process_mapping_manual(max_apps=max_apps)
        
    elif choice == "3":
        batch_size = input("Batch-Größe (Standard: 10): ").strip()
        interval = input("Intervall in Minuten (Standard: 10): ").strip()
        
        try:
            batch_size = int(batch_size) if batch_size else 10
            interval = int(interval) if interval else 10
        except ValueError:
            batch_size, interval = 10, 10
        
        processor.start_background_scheduler(batch_size=batch_size, interval_minutes=interval)
        
        print("🚀 Background-Scheduler gestartet!")
        print("💡 Drücken Sie Enter um zur Hauptauswahl zurückzukehren...")
        input()
        
    elif choice == "4":
        processor.stop_background_scheduler()
        
    elif choice == "5":
        status = processor.get_scheduler_status()
        print(f"\n📊 SCHEDULER STATUS:")
        print(f"🔄 Läuft: {'Ja' if status['scheduler_running'] else 'Nein'}")
        print(f"📋 Ausstehende Jobs: {status['pending_jobs']:,}")
        print(f"❌ Fehlgeschlagene Jobs: {status['failed_jobs']:,}")
        print(f"⏰ Nächster Lauf: {status['next_run']}")
        print(f"📅 Geplante Jobs: {status['jobs_count']}")
        
    elif choice == "6":
        steam_id = input("Steam ID eingeben: ").strip()
        if steam_id:
            added_count = processor.process_wishlist_apps_priority(steam_id)
            print(f"🎯 {added_count} Wishlist-Apps zur Priority-Queue hinzugefügt")
        else:
            print("❌ Ungültige Steam ID")
            
    elif choice == "7":
        if processor.scheduler_running:
            processor.stop_background_scheduler()
        print("👋 Processor beendet")
        return
        
    else:
        print("❌ Ungültige Auswahl")
        return
    
    # Finale Statistiken
    print("\n📊 AKTUELLE STATISTIKEN:")
    final_stats = db_manager.get_database_stats()
    print(f"✅ Mit CheapShark-Mapping: {final_stats['cheapshark']['mapped']:,}")
    print(f"📈 Erfolgsrate: {final_stats['cheapshark']['success_rate']:.1f}%")

if __name__ == "__main__":
    cheapshark_processor_main()