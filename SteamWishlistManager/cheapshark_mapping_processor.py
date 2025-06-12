"""
CheapShark Mapping Processor - ENHANCED Version
Mit integriertem Scheduler und DatabaseManager Integration
ERWEITERT: Explizite Speicherung wenn kein CheapShark-Mapping existiert
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
    ERWEITERT: Unterscheidet zwischen "kein Mapping" und "API-Fehler"
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
        ERWEITERT: Bessere Unterscheidung zwischen "nicht gefunden" und "Fehler"
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
                
                # ERWEITERT: Explizite Prüfung auf leere Antwort
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
                        'result_type': 'found'
                    }
                else:
                    # ERWEITERT: Explizit "kein Mapping gefunden" (leere API-Antwort)
                    return {
                        'app_id': steam_app_id,
                        'result_type': 'not_found',
                        'message': 'Keine CheapShark-Daten für diese Steam App ID verfügbar'
                    }
            else:
                # API-Fehler (HTTP != 200)
                return {
                    'app_id': steam_app_id,
                    'result_type': 'api_error',
                    'error': f"HTTP {response.status_code}",
                    'message': f"CheapShark API Fehler: {response.status_code}"
                }
                
        except requests.RequestException as e:
            # Request-Fehler (Timeout, Netzwerk, etc.)
            return {
                'app_id': steam_app_id,
                'result_type': 'request_error', 
                'error': str(e),
                'message': f"Request Fehler: {str(e)}"
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
        """
        Verarbeitet CheapShark-Mapping für eine einzelne App
        ERWEITERT: Release Date Awareness für neue Apps
        """
        try:
            # Prüfe zuerst ob bereits versucht wurde
            attempt_info = self.db_manager.has_cheapshark_mapping_been_attempted(app_id)
            
            if attempt_info['attempted']:
                if attempt_info['status'] == 'found':
                    logger.debug(f"✅ App {app_id} bereits erfolgreich gemappt")
                    return True
                elif attempt_info['no_mapping_found']:
                    logger.debug(f"📝 App {app_id} bereits als 'kein Mapping' markiert")
                    return False
                elif attempt_info['status'] == 'too_new':
                    # Prüfe ob App inzwischen alt genug ist
                    if not self.db_manager.is_app_recently_released(app_id, max_age_days=60):
                        logger.info(f"📅 App {app_id} ist jetzt alt genug für Retry (war 'too_new')")
                        # Setze Status zurück für erneuten Versuch
                        self.db_manager.reset_cheapshark_mapping_status([app_id], "Age-based retry")
                    else:
                        logger.debug(f"📅 App {app_id} noch zu neu für CheapShark")
                        return False
                elif attempt_info['attempts'] >= 3:
                    logger.debug(f"⚠️ App {app_id} bereits {attempt_info['attempts']}x versucht")
                    return False
            
            # CheapShark-Mapping abrufen
            cheapshark_data = self.get_cheapshark_mapping_for_app_id(app_id)
            result_type = cheapshark_data.get('result_type')
            
            if result_type == 'found':
                # Erfolgreiches Mapping gefunden
                success = self.db_manager.add_cheapshark_mapping(cheapshark_data)
                if success:
                    logger.info(f"✅ Mapping für App {app_id} erfolgreich gespeichert")
                    return True
                else:
                    logger.error(f"❌ Fehler beim Speichern des Mappings für App {app_id}")
                    return False
                    
            elif result_type == 'not_found':
                # ERWEITERT: Kein Mapping gefunden - prüfe Release Date
                is_recent = self.db_manager.is_app_recently_released(app_id, max_age_days=30)
                
                if is_recent:
                    # Neue App - behandle anders
                    success = self.db_manager.mark_cheapshark_no_mapping_found(app_id)  # Nutzt interne Release Date Logic
                    if success:
                        logger.info(f"📅 App {app_id}: Zu neu für CheapShark (wird später erneut geprüft)")
                        return False  # Kein Mapping, aber erfolgreich als "too_new" dokumentiert
                else:
                    # Etablierte App - normales "not found"
                    success = self.db_manager.mark_cheapshark_no_mapping_found(app_id)
                    if success:
                        logger.info(f"📝 App {app_id}: Kein CheapShark-Mapping verfügbar (dokumentiert)")
                        return False
                
                if not success:
                    logger.error(f"❌ Fehler beim Dokumentieren des Mapping-Status für App {app_id}")
                    return False
                    
            else:
                # API-Fehler oder Request-Fehler
                error_message = cheapshark_data.get('message', cheapshark_data.get('error', 'Unbekannter Fehler'))
                self.db_manager.mark_cheapshark_attempt_failed(app_id, error_message)
                logger.warning(f"⚠️ CheapShark-Fehler für App {app_id}: {error_message}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Unerwarteter Fehler bei App {app_id}: {e}")
            self.db_manager.mark_cheapshark_attempt_failed(app_id, str(e))
            return False
    
    def process_mapping_queue_batch(self, batch_size: int = 10) -> Dict:
        """
        Verarbeitet eine Batch von Jobs aus der Mapping Queue
        ERWEITERT: Bessere Statistiken inkl. "too_new" Status
        """
        # Nächste Jobs aus Queue holen
        jobs = self.db_manager.get_next_mapping_jobs(batch_size)
        
        if not jobs:
            return {
                'processed': 0, 
                'successful': 0, 
                'failed': 0, 
                'not_found': 0,
                'too_new': 0,
                'api_errors': 0
            }
        
        logger.info(f"🔄 Verarbeite {len(jobs)} CheapShark-Mapping Jobs...")
        
        processed = 0
        successful = 0  # Erfolgreich gemappt
        failed = 0      # API/Request Fehler
        not_found = 0   # Explizit kein Mapping verfügbar
        too_new = 0     # Zu neu für Mapping
        api_errors = 0  # Davon API-Fehler
        
        for job in jobs:
            job_id = job['id']
            app_id = job['app_id']
            
            # Job als "in Bearbeitung" markieren
            self.db_manager.update_mapping_job_status(job_id, 'processing')
            
            try:
                # CheapShark-Mapping abrufen
                cheapshark_data = self.get_cheapshark_mapping_for_app_id(app_id)
                result_type = cheapshark_data.get('result_type')
                
                if result_type == 'found':
                    # Erfolgreiches Mapping
                    if self.db_manager.add_cheapshark_mapping(cheapshark_data):
                        self.db_manager.update_mapping_job_status(job_id, 'completed')
                        successful += 1
                        logger.info(f"✅ Job {job_id} (App {app_id}) erfolgreich gemappt")
                    else:
                        self.db_manager.update_mapping_job_status(job_id, 'failed', "DB-Speicherfehler")
                        failed += 1
                        
                elif result_type == 'not_found':
                    # Kein Mapping verfügbar - prüfe Release Date
                    is_recent = self.db_manager.is_app_recently_released(app_id, max_age_days=30)
                    
                    if is_recent:
                        # Neue App - als "too_new" behandeln
                        self.db_manager.mark_cheapshark_no_mapping_found(app_id)  # Nutzt interne Logic
                        self.db_manager.update_mapping_job_status(job_id, 'completed')
                        too_new += 1
                        logger.info(f"📅 Job {job_id} (App {app_id}) - zu neu für Mapping")
                    else:
                        # Etablierte App - normales "not found"
                        self.db_manager.mark_cheapshark_no_mapping_found(app_id)
                        self.db_manager.update_mapping_job_status(job_id, 'completed')
                        not_found += 1
                        logger.info(f"📝 Job {job_id} (App {app_id}) - kein Mapping verfügbar")
                    
                else:
                    # API/Request Fehler
                    error_message = cheapshark_data.get('message', 'Unbekannter Fehler')
                    self.db_manager.mark_cheapshark_attempt_failed(app_id, error_message)
                    self.db_manager.update_mapping_job_status(job_id, 'failed', error_message)
                    failed += 1
                    
                    if result_type == 'api_error':
                        api_errors += 1
                    
                    logger.warning(f"⚠️ Job {job_id} (App {app_id}) fehlgeschlagen: {error_message}")
                
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
            'not_found': not_found,
            'too_new': too_new,
            'api_errors': api_errors,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"📊 Batch-Verarbeitung abgeschlossen:")
        logger.info(f"   ✅ {successful} erfolgreich gemappt")
        logger.info(f"   📝 {not_found} ohne Mapping")
        logger.info(f"   📅 {too_new} zu neu für Mapping")
        logger.info(f"   ❌ {failed} fehlgeschlagen ({api_errors} API-Fehler)")
        
        return result
    
    def retry_too_new_apps(self, min_age_days: int = 60, max_apps: int = 1000, priority: int = 6) -> int:
        """
        NEUE METHODE: Plant Apps die als "too_new" markiert sind für erneute Prüfung
        
        Args:
            min_age_days: Apps müssen mindestens X Tage alt sein
            max_apps: Maximale Anzahl Apps
            priority: Queue-Priorität
        """
        logger.info(f"📅 Plane Retry für Apps die als 'zu neu' markiert sind (jetzt >= {min_age_days} Tage alt)...")
        
        # Apps finden die als "too_new" markiert sind aber jetzt alt genug
        apps_to_retry = self.db_manager.get_apps_too_new_for_retry(
            min_age_days=min_age_days,
            limit=max_apps
        )
        
        if not apps_to_retry:
            logger.info("📭 Keine 'zu neue' Apps gefunden die jetzt alt genug sind")
            return 0
        
        logger.info(f"📋 {len(apps_to_retry)} 'zu neue' Apps gefunden die jetzt alt genug sind")
        
        # Zeige Beispiele
        print(f"\n📅 Gefundene Apps (zu neu → jetzt bereit):")
        for i, app in enumerate(apps_to_retry[:5], 1):
            age_days = int(app['age_days'])
            print(f"{i}. {app['name']} (ID: {app['app_id']}) - {age_days} Tage alt")
        
        if len(apps_to_retry) > 5:
            print(f"   ... und {len(apps_to_retry) - 5} weitere")
        
        # Bestätigung anfordern
        confirm = input(f"\n🤔 {len(apps_to_retry)} Apps für Age-Based Retry? (j/n): ").strip().lower()
        
        if confirm not in ['j', 'ja', 'y', 'yes']:
            logger.info("❌ Age-Based Retry abgebrochen")
            return 0
        
        # Apps zurücksetzen und zur Queue hinzufügen
        app_ids = [app['app_id'] for app in apps_to_retry]
        reset_count = self.db_manager.reset_cheapshark_mapping_status(
            app_ids,
            reason=f"Age-based retry - apps now >= {min_age_days} days old"
        )
        
        if reset_count > 0:
            added_count = self.add_missing_apps_to_queue(app_ids, priority)
            logger.info(f"📝 {added_count} 'zu neue' Apps zur Age-Based Retry-Queue hinzugefügt")
            return added_count
        else:
            logger.warning("⚠️ Keine Apps konnten zurückgesetzt werden")
            return 0
    
    def get_recently_released_apps_status(self, max_age_days: int = 30) -> Dict:
        """
        NEUE METHODE: Gibt Status für kürzlich veröffentlichte Apps zurück
        """
        # Apps ohne Mapping die kürzlich veröffentlicht wurden
        recent_without_mapping = self.db_manager.get_recently_released_apps_without_mapping(
            max_age_days=max_age_days,
            limit=10000
        )
        
        # Apps mit "too_new" Status
        too_new_apps = self.db_manager.get_apps_by_mapping_status(['too_new'], limit=10000)
        
        # Apps die alt genug für Retry sind
        ready_for_retry = self.db_manager.get_apps_too_new_for_retry(
            min_age_days=max_age_days * 2,  # Doppelt so alt
            limit=10000
        )
        
        return {
            'recent_without_mapping': len(recent_without_mapping),
            'marked_too_new': len(too_new_apps),
            'ready_for_retry': len(ready_for_retry),
            'max_age_days': max_age_days,
            'examples': {
                'recent_without_mapping': recent_without_mapping[:3],
                'ready_for_retry': ready_for_retry[:3]
            }
        }
    
    def add_missing_apps_to_queue(self, app_ids: List[str], priority: int = 5) -> int:
        """
        Fügt fehlende Apps zur CheapShark-Mapping Queue hinzu
        ERWEITERT: Filtert Apps die bereits "no mapping found" haben
        """
        if not app_ids:
            return 0
        
        # Filtere Apps die bereits verarbeitet wurden
        apps_to_add = []
        already_processed = 0
        
        for app_id in app_ids:
            attempt_info = self.db_manager.has_cheapshark_mapping_been_attempted(app_id)
            
            if not attempt_info['attempted']:
                # Noch nie versucht
                apps_to_add.append(app_id)
            elif attempt_info['status'] == 'failed' and attempt_info['attempts'] < 3:
                # Fehlgeschlagen aber noch Retry-Versuche übrig
                apps_to_add.append(app_id)
            else:
                # Bereits erfolgreich verarbeitet oder zu oft fehlgeschlagen
                already_processed += 1
        
        if not apps_to_add:
            logger.info(f"📋 Alle {len(app_ids)} Apps bereits verarbeitet")
            return 0
        
        added_count = self.db_manager.add_to_mapping_queue(apps_to_add, priority)
        logger.info(f"📝 {added_count}/{len(apps_to_add)} Apps zur Mapping Queue hinzugefügt")
        
        if already_processed > 0:
            logger.info(f"⏭️ {already_processed} Apps bereits verarbeitet (übersprungen)")
        
        return added_count
    
    def process_wishlist_apps_priority(self, steam_id: str) -> int:
        """
        Fügt Wishlist-Apps mit hoher Priorität zur Mapping Queue hinzu
        ERWEITERT: Bessere Filterung
        """
        logger.info(f"🎯 Verarbeite Wishlist-Apps für User {steam_id} mit hoher Priorität...")
        
        # Hole Wishlist-Items ohne erfolgreiches CheapShark-Mapping
        wishlist_items = self.db_manager.get_wishlist_items(steam_id, include_cheapshark=True)
        
        apps_to_map = []
        for item in wishlist_items:
            # Nur Apps ohne erfolgreiches Mapping oder explizites "not found"
            if not item.get('cheapshark_game_id') and not item.get('no_mapping_found'):
                apps_to_map.append(item['app_id'])
        
        if apps_to_map:
            # Hohe Priorität für Wishlist-Apps
            added_count = self.add_missing_apps_to_queue(apps_to_map, priority=8)
            logger.info(f"🎯 {added_count} Wishlist-Apps zur Priority-Queue hinzugefügt")
            return added_count
        else:
            logger.info("✅ Alle Wishlist-Apps sind bereits verarbeitet")
            return 0
    
    def retry_apps_with_status(self, statuses: List[str], max_apps: int = 1000, 
                              older_than_days: int = None, priority: int = 5) -> int:
        """
        NEUE METHODE: Plant Apps mit bestimmten Status für erneute Verarbeitung
        
        Args:
            statuses: Liste der Status ['found', 'not_found', 'failed', 'unknown']
            max_apps: Maximale Anzahl Apps
            older_than_days: Nur Apps deren letzter Versuch älter als X Tage ist
            priority: Queue-Priorität
        """
        logger.info(f"🔄 Plane Retry für Apps mit Status: {', '.join(statuses)}")
        
        # Apps mit den gewünschten Status finden
        if older_than_days:
            apps_to_retry = self.db_manager.get_apps_by_custom_criteria(
                mapping_status=statuses,
                older_than_days=older_than_days,
                limit=max_apps
            )
            logger.info(f"🔍 Suche Apps mit Status {statuses} älter als {older_than_days} Tage...")
        else:
            apps_to_retry = self.db_manager.get_apps_by_mapping_status(statuses, max_apps)
            logger.info(f"🔍 Suche Apps mit Status {statuses}...")
        
        if not apps_to_retry:
            logger.info("📭 Keine Apps mit den gewünschten Kriterien gefunden")
            return 0
        
        logger.info(f"📋 {len(apps_to_retry)} Apps gefunden für Retry")
        
        # Apps für Retry zurücksetzen
        app_ids = [app['app_id'] for app in apps_to_retry]
        reset_count = self.db_manager.reset_cheapshark_mapping_status(
            app_ids, 
            reason=f"Retry for status: {', '.join(statuses)}"
        )
        
        if reset_count > 0:
            # Zur Queue hinzufügen
            added_count = self.add_missing_apps_to_queue(app_ids, priority)
            logger.info(f"📝 {added_count} Apps zur Retry-Queue hinzugefügt (Priorität: {priority})")
            return added_count
        else:
            logger.warning("⚠️ Keine Apps konnten zurückgesetzt werden")
            return 0
    
    def retry_no_mapping_found_apps(self, max_apps: int = 1000, 
                                   older_than_days: int = 30, priority: int = 6) -> int:
        """
        NEUE METHODE: Plant Apps mit 'kein Mapping gefunden' für erneute Prüfung
        
        Args:
            max_apps: Maximale Anzahl Apps
            older_than_days: Nur Apps deren letzter Versuch älter als X Tage ist
            priority: Queue-Priorität
        """
        logger.info(f"📝 Plane Retry für Apps ohne CheapShark-Mapping (älter als {older_than_days} Tage)...")
        
        # Apps finden die als "kein Mapping" markiert sind
        apps_to_retry = self.db_manager.get_apps_with_no_mapping_found(
            limit=max_apps,
            older_than_days=older_than_days
        )
        
        if not apps_to_retry:
            logger.info("📭 Keine 'kein Mapping' Apps gefunden die älter sind")
            return 0
        
        logger.info(f"📋 {len(apps_to_retry)} Apps ohne Mapping gefunden (für Retry)")
        
        # Bestätigung anfordern
        print(f"\n🤔 Möchten Sie {len(apps_to_retry)} Apps ohne CheapShark-Mapping erneut prüfen?")
        print("   Grund: CheapShark könnte neue Spiele hinzugefügt haben")
        confirm = input("   Fortfahren? (j/n): ").strip().lower()
        
        if confirm not in ['j', 'ja', 'y', 'yes']:
            logger.info("❌ Retry abgebrochen")
            return 0
        
        # Apps zurücksetzen und zur Queue hinzufügen
        app_ids = [app['app_id'] for app in apps_to_retry]
        reset_count = self.db_manager.reset_cheapshark_mapping_status(
            app_ids,
            reason=f"Retry 'no mapping found' apps older than {older_than_days} days"
        )
        
        if reset_count > 0:
            added_count = self.add_missing_apps_to_queue(app_ids, priority)
            logger.info(f"📝 {added_count} 'kein Mapping' Apps zur Retry-Queue hinzugefügt")
            return added_count
        else:
            logger.warning("⚠️ Keine Apps konnten zurückgesetzt werden")
            return 0
    
    def retry_failed_mappings(self, max_apps: int = 1000, 
                             older_than_days: int = 7, max_attempts: int = 3, 
                             priority: int = 4) -> int:
        """
        NEUE METHODE: Plant fehlgeschlagene Mappings für erneute Verarbeitung
        
        Args:
            max_apps: Maximale Anzahl Apps
            older_than_days: Nur Apps deren letzter Versuch älter als X Tage ist
            max_attempts: Nur Apps mit weniger als X Versuchen
            priority: Queue-Priorität
        """
        logger.info(f"❌ Plane Retry für fehlgeschlagene Mappings...")
        
        # Fehlgeschlagene Apps finden
        apps_to_retry = self.db_manager.get_apps_by_custom_criteria(
            mapping_status=['failed'],
            older_than_days=older_than_days,
            max_attempts=max_attempts,
            limit=max_apps
        )
        
        if not apps_to_retry:
            logger.info("📭 Keine fehlgeschlagenen Apps für Retry gefunden")
            return 0
        
        logger.info(f"📋 {len(apps_to_retry)} fehlgeschlagene Apps gefunden für Retry")
        
        # Apps zurücksetzen und zur Queue hinzufügen
        app_ids = [app['app_id'] for app in apps_to_retry]
        reset_count = self.db_manager.reset_cheapshark_mapping_status(
            app_ids,
            reason=f"Retry failed mappings older than {older_than_days} days"
        )
        
        if reset_count > 0:
            added_count = self.add_missing_apps_to_queue(app_ids, priority)
            logger.info(f"📝 {added_count} fehlgeschlagene Apps zur Retry-Queue hinzugefügt")
            return added_count
        else:
            logger.warning("⚠️ Keine Apps konnten zurückgesetzt werden")
            return 0
    
    def schedule_retry_by_criteria(self, 
                                  mapping_status: List[str] = None,
                                  no_mapping_found: bool = None,
                                  older_than_days: int = None,
                                  max_attempts: int = None,
                                  max_apps: int = 1000,
                                  priority: int = 5) -> int:
        """
        NEUE METHODE: Flexible Retry-Planung nach benutzerdefinierten Kriterien
        
        Args:
            mapping_status: Liste der Status zum Retry
            no_mapping_found: True=nur "kein Mapping", False=nur "mit Mapping", None=alle
            older_than_days: Nur Apps deren letzter Versuch älter ist
            max_attempts: Nur Apps mit max. X Versuchen
            max_apps: Maximale Anzahl Apps
            priority: Queue-Priorität
        """
        criteria_desc = []
        if mapping_status:
            criteria_desc.append(f"Status: {', '.join(mapping_status)}")
        if no_mapping_found is not None:
            criteria_desc.append(f"Kein Mapping: {'Ja' if no_mapping_found else 'Nein'}")
        if older_than_days:
            criteria_desc.append(f"Älter als: {older_than_days} Tage")
        if max_attempts:
            criteria_desc.append(f"Max Versuche: {max_attempts}")
        
        criteria_str = ", ".join(criteria_desc) if criteria_desc else "Alle"
        logger.info(f"🔧 Plane flexiblen Retry - Kriterien: {criteria_str}")
        
        # Apps nach Kriterien finden
        apps_to_retry = self.db_manager.get_apps_by_custom_criteria(
            mapping_status=mapping_status,
            no_mapping_found=no_mapping_found,
            older_than_days=older_than_days,
            max_attempts=max_attempts,
            limit=max_apps
        )
        
        if not apps_to_retry:
            logger.info("📭 Keine Apps mit den gewünschten Kriterien gefunden")
            return 0
        
        logger.info(f"📋 {len(apps_to_retry)} Apps gefunden für flexiblen Retry")
        
        # Bestätigung anfordern
        print(f"\n🤔 {len(apps_to_retry)} Apps für Retry gefunden:")
        print(f"   Kriterien: {criteria_str}")
        confirm = input("   Fortfahren mit Retry? (j/n): ").strip().lower()
        
        if confirm not in ['j', 'ja', 'y', 'yes']:
            logger.info("❌ Flexibler Retry abgebrochen")
            return 0
        
        # Apps zurücksetzen und zur Queue hinzufügen
        app_ids = [app['app_id'] for app in apps_to_retry]
        reset_count = self.db_manager.reset_cheapshark_mapping_status(
            app_ids,
            reason=f"Flexible retry - {criteria_str}"
        )
        
        if reset_count > 0:
            added_count = self.add_missing_apps_to_queue(app_ids, priority)
            logger.info(f"📝 {added_count} Apps zur flexiblen Retry-Queue hinzugefügt")
            return added_count
        else:
            logger.warning("⚠️ Keine Apps konnten zurückgesetzt werden")
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
        """Geplante Mapping-Verarbeitung - ERWEITERT"""
        try:
            logger.info("⏰ Starte geplante CheapShark-Mapping Verarbeitung...")
            
            result = self.process_mapping_queue_batch(batch_size)
            
            if result['processed'] > 0:
                logger.info(f"📊 Scheduler-Job abgeschlossen:")
                logger.info(f"   ✅ {result['successful']} erfolgreich")
                logger.info(f"   📝 {result['not_found']} ohne Mapping")
                logger.info(f"   ❌ {result['failed']} fehlgeschlagen")
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
    # MANUAL PROCESSING - ERWEITERT
    # ========================
    
    def process_mapping_manual(self, max_apps: int = None, batch_size: int = 50) -> Dict:
        """
        Manuelle Verarbeitung aller unmapped Apps
        ERWEITERT: Bessere Statistiken und Filterung
        """
        print("🔄 MANUELLE CHEAPSHARK-MAPPING VERARBEITUNG")
        print("=" * 60)
        
        # Hole Apps ohne erfolgreiches Mapping (aber mit möglichen Retry-Versuchen)
        unmapped_apps = self.db_manager.get_apps_without_successful_cheapshark_mapping(max_apps or 100000)
        total_to_process = len(unmapped_apps)
        
        if total_to_process == 0:
            print("✅ Alle Apps haben CheapShark-Status (gefunden oder nicht verfügbar)!")
            return {'processed': 0, 'successful': 0, 'failed': 0, 'not_found': 0}
        
        print(f"📊 Apps ohne erfolgreichen CheapShark-Status: {total_to_process:,}")
        
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
        not_found = 0
        api_errors = 0
        
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
            not_found += result['not_found']
            api_errors += result['api_errors']
            
            # Fortschrittsanzeige
            if processed % 100 == 0:
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                remaining = (total_to_process - processed) / rate if rate > 0 else 0
                
                print(f"📊 {processed}/{total_to_process} "
                      f"({(processed/total_to_process)*100:.1f}%) | "
                      f"✅ {successful} | 📝 {not_found} | ❌ {failed} | "
                      f"Rate: {rate:.1f}/min | "
                      f"Verbleibend: {remaining/60:.1f}min")
        
        # Abschluss-Statistiken
        elapsed_time = time.time() - start_time
        
        print(f"\n🏁 MANUELLE VERARBEITUNG ABGESCHLOSSEN")
        print(f"⏱️ Dauer: {elapsed_time/60:.1f} Minuten")
        print(f"📊 Verarbeitet: {processed:,} Apps")
        print(f"✅ Erfolgreich gemappt: {successful:,}")
        print(f"📝 Kein Mapping verfügbar: {not_found:,}")
        print(f"❌ Fehlgeschlagen: {failed:,} (davon {api_errors} API-Fehler)")
        
        completed_successfully = successful + not_found  # Beide sind "erfolgreich verarbeitet"
        if processed > 0:
            print(f"📈 Verarbeitungsrate: {(completed_successfully/processed)*100:.1f}%")
        
        return {
            'processed': processed,
            'successful': successful,
            'failed': failed,
            'not_found': not_found,
            'api_errors': api_errors,
            'time_minutes': elapsed_time / 60,
            'completion_rate': (completed_successfully/processed)*100 if processed > 0 else 0
        }

def cheapshark_processor_main():
    """
    Hauptfunktion für CheapShark-Mapping Processor
    ERWEITERT: Bessere Statistiken-Anzeige
    """
    print("🔗 CHEAPSHARK MAPPING PROCESSOR v2.0 (ENHANCED)")
    print("Mit Background-Scheduler und explizitem 'Kein Mapping' Tracking")
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
    
    # Aktuelle Statistiken zeigen - ERWEITERT
    print("\n📊 AKTUELLE MAPPING-STATISTIKEN:")
    stats = db_manager.get_database_stats()
    breakdown = db_manager.get_cheapshark_mapping_breakdown()
    
    print(f"📚 Gesamt Apps: {stats['apps']['total']:,}")
    print(f"   📅 Mit Release Date: {stats['apps']['with_release_date']:,}")
    print(f"   🆕 Kürzlich veröffentlicht (< 30 Tage): {stats['apps']['recently_released']:,}")
    
    print(f"\n🔗 CheapShark Mapping Status:")
    print(f"✅ Mit CheapShark-Mapping: {stats['cheapshark']['mapped']:,}")
    print(f"📝 Kein Mapping verfügbar: {stats['cheapshark']['no_mapping_found']:,}")
    print(f"📅 Zu neu für Mapping: {stats['cheapshark']['too_new']:,}")
    print(f"❌ Mapping fehlgeschlagen: {stats['cheapshark']['mapping_failed']:,}")
    print(f"❔ Noch nicht versucht: {stats['cheapshark']['unmapped']:,}")
    print(f"📈 Erfolgsrate: {stats['cheapshark']['success_rate']:.1f}%")
    print(f"🎯 Coverage (verarbeitet): {stats['cheapshark']['coverage']:.1f}%")
    print(f"📋 Queue - Ausstehend: {stats['queue']['pending']:,}")
    
    # Release Date Status für kürzlich veröffentlichte Apps
    recent_status = processor.get_recently_released_apps_status()
    if recent_status['recent_without_mapping'] > 0 or recent_status['marked_too_new'] > 0:
        print(f"\n📅 KÜRZLICH VERÖFFENTLICHTE APPS:")
        print(f"🆕 Ohne Mapping (< 30 Tage): {recent_status['recent_without_mapping']:,}")
        print(f"📝 Als 'zu neu' markiert: {recent_status['marked_too_new']:,}")
        print(f"🔄 Bereit für Age-Based Retry: {recent_status['ready_for_retry']:,}")
    
    # Detaillierte Aufschlüsselung
    print(f"\n🔍 DETAILLIERTE AUFSCHLÜSSELUNG:")
    status_breakdown = breakdown['status_breakdown']
    for status, count in status_breakdown.items():
        status_names = {
            'found': '✅ Erfolgreich gemappt',
            'not_found': '📝 Kein Mapping verfügbar', 
            'too_new': '📅 Zu neu für Mapping',
            'failed': '❌ Fehlgeschlagen',
            'unknown': '❔ Status unbekannt'
        }
        print(f"{status_names.get(status, status)}: {count:,}")
    
    attempts_info = breakdown['attempts_info']
    if attempts_info['average_attempts'] > 0:
        print(f"\n📊 Versuche-Statistiken:")
        print(f"📊 Durchschnittliche Versuche: {attempts_info['average_attempts']:.1f}")
        print(f"🔄 Apps mit Retry: {attempts_info['apps_retried']:,}")
    
    print("\n🔧 PROCESSOR OPTIONEN:")
    print("1. 🔄 Manuelle Verarbeitung (alle unverarbeiteten Apps)")
    print("2. ⚡ Limitierte Verarbeitung (nur X Apps)")
    print("3. 🚀 Background-Scheduler starten")
    print("4. 🛑 Background-Scheduler stoppen")
    print("5. 📊 Scheduler-Status anzeigen")
    print("6. 🎯 Wishlist-Apps priorisieren (Steam ID eingeben)")
    print("7. 📈 Detaillierte Statistiken anzeigen")
    print("8. 🔄 RETRY-OPTIONEN:")
    print("   8a. 📝 Apps ohne Mapping erneut prüfen")
    print("   8b. ❌ Fehlgeschlagene Mappings wiederholen")
    print("   8c. 📅 'Zu neue' Apps für Age-Based Retry")
    print("   8d. 🔧 Benutzerdefinierte Retry-Kriterien")
    print("   8e. 📋 Status-basierte Retry")
    print("9. 📅 RELEASE DATE FEATURES:")
    print("   9a. 🆕 Kürzlich veröffentlichte Apps anzeigen")
    print("   9b. 📊 Release Date Statistiken")
    print("10. ❌ Beenden")
    
    choice = input("\nWählen Sie eine Option (1-10, 8a-8e, 9a-9b): ").strip().lower()
    
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
        batch_size = input("Batch-Größе (Standard: 10): ").strip()
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
        # Detaillierte Statistiken
        print(f"\n📈 DETAILLIERTE CHEAPSHARK-STATISTIKEN:")
        print("=" * 50)
        
        final_stats = db_manager.get_database_stats()
        final_breakdown = db_manager.get_cheapshark_mapping_breakdown()
        
        print(f"📚 Gesamt Steam Apps: {final_stats['apps']['total']:,}")
        print(f"🆓 Davon kostenlos: {final_stats['apps']['free']:,}")
        print(f"💰 Davon kostenpflichtig: {final_stats['apps']['paid']:,}")
        
        print(f"\n🔗 CheapShark Mapping Status:")
        cs_stats = final_stats['cheapshark']
        print(f"✅ Erfolgreich gemappt: {cs_stats['mapped']:,} ({cs_stats['found_rate']:.1f}%)")
        print(f"📝 Kein Mapping verfügbar: {cs_stats['no_mapping_found']:,}")
        print(f"❌ Mapping fehlgeschlagen: {cs_stats['mapping_failed']:,}")
        print(f"❔ Noch nicht versucht: {cs_stats['unmapped']:,}")
        print(f"📊 Gesamt verarbeitet: {cs_stats['attempted']:,} ({cs_stats['coverage']:.1f}%)")
        print(f"📈 Erfolgsrate (von verarbeiteten): {cs_stats['success_rate']:.1f}%")
        
        print(f"\n👥 Wishlist Statistiken:")
        wl_stats = final_stats['wishlist'] 
        print(f"📋 Gesamt Wishlist-Items: {wl_stats['total_items']:,}")
        print(f"👤 Unique Benutzer: {wl_stats['unique_users']:,}")
        print(f"📊 Durchschnitt pro Benutzer: {wl_stats['avg_items_per_user']:.1f}")
        
    elif choice == "8a":
        # Apps ohne Mapping erneut prüfen
        print("\n📝 APPS OHNE MAPPING ERNEUT PRÜFEN")
        print("=" * 40)
        
        max_apps = input("Wie viele Apps maximal? (Standard: 1000): ").strip()
        older_days = input("Nur Apps älter als X Tage? (Standard: 30): ").strip()
        
        try:
            max_apps = int(max_apps) if max_apps else 1000
            older_days = int(older_days) if older_days else 30
        except ValueError:
            max_apps, older_days = 1000, 30
        
        added_count = processor.retry_no_mapping_found_apps(
            max_apps=max_apps, 
            older_than_days=older_days
        )
        print(f"✅ {added_count} Apps ohne Mapping zur Retry-Queue hinzugefügt")
        
    elif choice == "8b":
        # Fehlgeschlagene Mappings wiederholen
        print("\n❌ FEHLGESCHLAGENE MAPPINGS WIEDERHOLEN")
        print("=" * 40)
        
        max_apps = input("Wie viele Apps maximal? (Standard: 1000): ").strip()
        older_days = input("Nur Apps älter als X Tage? (Standard: 7): ").strip()
        max_attempts = input("Nur Apps mit max. X Versuchen? (Standard: 3): ").strip()
        
        try:
            max_apps = int(max_apps) if max_apps else 1000
            older_days = int(older_days) if older_days else 7
            max_attempts = int(max_attempts) if max_attempts else 3
        except ValueError:
            max_apps, older_days, max_attempts = 1000, 7, 3
        
        added_count = processor.retry_failed_mappings(
            max_apps=max_apps,
            older_than_days=older_days,
            max_attempts=max_attempts
        )
        print(f"✅ {added_count} fehlgeschlagene Apps zur Retry-Queue hinzugefügt")
        
    elif choice == "8c":
        # 'Zu neue' Apps für Age-Based Retry
        print("\n📅 'ZU NEUE' APPS FÜR AGE-BASED RETRY")
        print("=" * 40)
        
        min_age = input("Apps müssen mindestens X Tage alt sein? (Standard: 60): ").strip()
        max_apps = input("Maximal wie viele Apps? (Standard: 1000): ").strip()
        
        try:
            min_age = int(min_age) if min_age else 60
            max_apps = int(max_apps) if max_apps else 1000
        except ValueError:
            min_age, max_apps = 60, 1000
        
        added_count = processor.retry_too_new_apps(
            min_age_days=min_age,
            max_apps=max_apps
        )
        print(f"✅ {added_count} 'zu neue' Apps zur Age-Based Retry-Queue hinzugefügt")
        
    elif choice == "8d":
        # Benutzerdefinierte Retry-Kriterien
        print("\n🔧 BENUTZERDEFINIERTE RETRY-KRITERIEN")
        print("=" * 40)
        
        print("Verfügbare Status: found, not_found, too_new, failed, unknown")
        status_input = input("Status zum Retry (kommagetrennt, leer für alle): ").strip()
        statuses = [s.strip() for s in status_input.split(',')] if status_input else None
        
        mapping_input = input("Nur 'kein Mapping' Apps? (j/n/leer für alle): ").strip().lower()
        no_mapping = None
        if mapping_input in ['j', 'ja', 'y', 'yes']:
            no_mapping = True
        elif mapping_input in ['n', 'no', 'nein']:
            no_mapping = False
        
        older_days = input("Nur Apps älter als X Tage? (leer für alle): ").strip()
        older_days = int(older_days) if older_days else None
        
        max_attempts = input("Nur Apps mit max. X Versuchen? (leer für alle): ").strip()
        max_attempts = int(max_attempts) if max_attempts else None
        
        max_apps = input("Maximale Anzahl Apps? (Standard: 1000): ").strip()
        max_apps = int(max_apps) if max_apps else 1000
        
        priority = input("Queue-Priorität? (1-10, Standard: 5): ").strip()
        priority = int(priority) if priority else 5
        
        added_count = processor.schedule_retry_by_criteria(
            mapping_status=statuses,
            no_mapping_found=no_mapping,
            older_than_days=older_days,
            max_attempts=max_attempts,
            max_apps=max_apps,
            priority=priority
        )
        print(f"✅ {added_count} Apps zur benutzerdefinierten Retry-Queue hinzugefügt")
        
    elif choice == "8e":
        # Status-basierte Retry
        print("\n📋 STATUS-BASIERTE RETRY")
        print("=" * 30)
        
        print("Verfügbare Status:")
        print("1. not_found (kein Mapping gefunden)")
        print("2. too_new (zu neu für Mapping)")
        print("3. failed (fehlgeschlagen)")
        print("4. found (erfolgreich) - für Re-Check")
        print("5. unknown (unbekannter Status)")
        
        status_choice = input("Status wählen (1-5): ").strip()
        status_map = {
            '1': ['not_found'],
            '2': ['too_new'],
            '3': ['failed'], 
            '4': ['found'],
            '5': ['unknown']
        }
        
        if status_choice not in status_map:
            print("❌ Ungültige Auswahl")
            return
        
        statuses = status_map[status_choice]
        
        max_apps = input("Wie viele Apps maximal? (Standard: 1000): ").strip()
        older_days = input("Nur Apps älter als X Tage? (leer für alle): ").strip()
        
        try:
            max_apps = int(max_apps) if max_apps else 1000
            older_days = int(older_days) if older_days else None
        except ValueError:
            max_apps = 1000
            older_days = None
        
        added_count = processor.retry_apps_with_status(
            statuses=statuses,
            max_apps=max_apps,
            older_than_days=older_days
        )
        print(f"✅ {added_count} Apps mit Status '{statuses[0]}' zur Retry-Queue hinzugefügt")
        
    elif choice == "9a":
        # Kürzlich veröffentlichte Apps anzeigen
        print("\n🆕 KÜRZLICH VERÖFFENTLICHTE APPS")
        print("=" * 40)
        
        max_age = input("Apps maximal X Tage alt? (Standard: 30): ").strip()
        limit = input("Wie viele Apps anzeigen? (Standard: 20): ").strip()
        
        try:
            max_age = int(max_age) if max_age else 30
            limit = int(limit) if limit else 20
        except ValueError:
            max_age, limit = 30, 20
        
        recent_apps = db_manager.get_recently_released_apps_without_mapping(
            max_age_days=max_age,
            limit=limit
        )
        
        if recent_apps:
            print(f"\n📋 {len(recent_apps)} kürzlich veröffentlichte Apps ohne CheapShark-Mapping:")
            for i, app in enumerate(recent_apps, 1):
                age_days = int(app['age_days'])
                print(f"{i:2d}. {app['name']} (ID: {app['app_id']}) - {age_days} Tage alt")
        else:
            print(f"📭 Keine kürzlich veröffentlichten Apps ohne Mapping gefunden")
            
    elif choice == "9b":
        # Release Date Statistiken
        print("\n📊 RELEASE DATE STATISTIKEN")
        print("=" * 40)
        
        # Verschiedene Altersgruppen
        age_groups = [7, 14, 30, 60, 90, 180, 365]
        
        print("📅 Apps nach Veröffentlichungsalter (ohne CheapShark-Mapping):")
        for age_days in age_groups:
            apps_in_group = db_manager.get_recently_released_apps_without_mapping(
                max_age_days=age_days,
                limit=10000
            )
            print(f"   <= {age_days:3d} Tage: {len(apps_in_group):,} Apps")
        
        # Status-Übersicht für neue Apps
        recent_status = processor.get_recently_released_apps_status()
        print(f"\n📈 Status-Übersicht (< 30 Tage):")
        print(f"🆕 Ohne Mapping: {recent_status['recent_without_mapping']:,}")
        print(f"📝 Als 'zu neu' markiert: {recent_status['marked_too_new']:,}")
        print(f"🔄 Bereit für Retry: {recent_status['ready_for_retry']:,}")
        
        # Beispiele zeigen
        if recent_status['examples']['recent_without_mapping']:
            print(f"\n📄 Beispiele kürzlich veröffentlichter Apps ohne Mapping:")
            for app in recent_status['examples']['recent_without_mapping']:
                age_days = int(app['age_days'])
                print(f"   • {app['name']} - {age_days} Tage alt")
        
    elif choice == "10":
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
    print(f"📝 Kein Mapping verfügbar: {final_stats['cheapshark']['no_mapping_found']:,}")
    print(f"📈 Coverage: {final_stats['cheapshark']['coverage']:.1f}%")

if __name__ == "__main__":
    cheapshark_processor_main()
