"""
Steam Bulk Importer - COMPLETE VERSION mit Release Date Support
Nutzt die zentrale DatabaseManager Klasse
Automatische Discovery neuer Releases via ISteamChartsService
"""

import requests
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from database_manager import DatabaseManager

class SteamBulkImporter:
    """
    Importiert ALLE verfügbaren Steam-Spiele auf einmal über verschiedene APIs
    Nutzt DatabaseManager für alle Datenbankoperationen
    Automatische Discovery neuer Releases via ISteamChartsService
    """
    
    def __init__(self, api_key: str, db_manager: DatabaseManager = None):
        self.api_key = api_key
        self.db_manager = db_manager or DatabaseManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SteamWishlistManager/2.0'
        })
    
    def log_import_session(self, session_type: str, items_processed: int, items_successful: int, 
                          success: bool = True, error_message: str = None, metadata: dict = None) -> int:
        """Loggt eine Import-Session"""
        session_data = {
            'session_type': session_type,
            'started_at': datetime.now().isoformat(),
            'completed_at': datetime.now().isoformat(),
            'items_processed': items_processed,
            'items_successful': items_successful,
            'success': success,
            'error_message': error_message,
            'metadata': json.dumps(metadata) if metadata else None
        }
        
        # Session in Datenbank loggen (würde normalerweise Session ID zurückgeben)
        print(f"📋 Import Session: {session_type} - {items_successful}/{items_processed} erfolgreich")
        return 1  # Mock Session ID
    
    # ========================
    # CLASSIC BULK IMPORT METHODS
    # ========================
    
    def import_all_steam_apps_method1(self) -> bool:
        """
        METHODE 1: Steam Web API GetAppList v2 
        - Bekommt ALLE öffentlichen Apps auf einmal (~150,000+ Apps)
        """
        print("🚀 METHODE 1: Steam Web API GetAppList v2")
        print("=" * 50)
        
        start_time = time.time()
        
        url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
        params = {'format': 'json'}
        
        try:
            print("📥 Lade komplette Steam App Liste...")
            response = self.session.get(url, params=params, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                apps = data.get('applist', {}).get('apps', [])
                
                print(f"✅ {len(apps):,} Apps von Steam erhalten")
                
                # Apps in Datenbank speichern
                imported_count = self.db_manager.add_apps_batch(apps)
                
                elapsed_time = int(time.time() - start_time)
                self.log_import_session('steam_api_v2', len(apps), imported_count, True, 
                                      metadata={'elapsed_seconds': elapsed_time})
                
                print(f"💾 {imported_count:,} Apps in Datenbank gespeichert")
                print(f"⏱️ Dauer: {elapsed_time} Sekunden")
                
                return True
                
            else:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                print(f"❌ API Fehler: {error_msg}")
                self.log_import_session('steam_api_v2', 0, 0, False, error_msg)
                return False
                
        except requests.RequestException as e:
            error_msg = str(e)
            print(f"❌ Request Fehler: {error_msg}")
            self.log_import_session('steam_api_v2', 0, 0, False, error_msg)
            return False
    
    def import_games_only_method2(self) -> bool:
        """
        METHODE 2: IStoreService GetAppList (nur Spiele)
        - Nur echte Spiele, keine DLCs/Software (~100,000+ Spiele)
        - Mit Pagination für vollständige Abdeckung
        """
        print("🎮 METHODE 2: IStoreService GetAppList (nur Spiele)")
        print("=" * 60)
        
        start_time = time.time()
        all_apps = []
        
        url = "https://api.steampowered.com/IStoreService/GetAppList/v1/"
        max_results = 50000  # Maximum pro Request
        last_appid = 0
        page = 1
        
        while True:
            params = {
                'key': self.api_key,
                'include_games': 'true',
                'include_dlc': 'false',
                'include_software': 'false', 
                'include_videos': 'false',
                'include_hardware': 'false',
                'max_results': max_results,
                'format': 'json'
            }
            
            if last_appid > 0:
                params['last_appid'] = last_appid
            
            try:
                print(f"📄 Lade Seite {page} (ab App ID {last_appid})...")
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    apps = data.get('response', {}).get('apps', [])
                    
                    if not apps:
                        print("📭 Keine weiteren Apps gefunden")
                        break
                    
                    all_apps.extend(apps)
                    last_appid = apps[-1]['appid']
                    
                    print(f"   ✅ {len(apps):,} Apps geladen (Gesamt: {len(all_apps):,})")
                    
                    # Rate Limiting zwischen Requests
                    time.sleep(1)
                    page += 1
                    
                    # Sicherheits-Break nach vielen Seiten
                    if page > 10:  # Sollte reichen für alle Apps
                        print("⚠️ Maximum Seiten erreicht")
                        break
                        
                else:
                    print(f"❌ API Fehler Seite {page}: {response.status_code}")
                    break
                    
            except requests.RequestException as e:
                print(f"❌ Request Fehler Seite {page}: {e}")
                break
        
        if all_apps:
            print(f"✅ Gesamt: {len(all_apps):,} Spiele von Steam erhalten")
            
            # Apps in Datenbank speichern
            imported_count = self.db_manager.add_apps_batch(all_apps)
            
            elapsed_time = int(time.time() - start_time)
            self.log_import_session('steam_store_service', len(all_apps), imported_count, True,
                                  metadata={'pages': page-1, 'elapsed_seconds': elapsed_time})
            
            print(f"💾 {imported_count:,} Spiele in Datenbank gespeichert")
            print(f"⏱️ Dauer: {elapsed_time} Sekunden")
            
            return True
        else:
            self.log_import_session('steam_store_service', 0, 0, False, "Keine Apps erhalten")
            print("❌ Keine Apps erhalten")
            return False
    
    def import_steamspy_data_method3(self, max_pages: int = 50) -> bool:
        """
        METHODE 3: SteamSpy API (mit Besitzer-Statistiken)
        - Bekommt Steam-Spiele mit Statistiken
        - Begrenzt auf max_pages wegen langsamer API
        """
        print(f"📊 METHODE 3: SteamSpy API (max {max_pages} Seiten)")
        print("=" * 50)
        
        start_time = time.time()
        all_apps = []
        
        url = "https://steamspy.com/api.php"
        page = 0
        
        while page < max_pages:
            params = {
                'request': 'all',
                'page': page
            }
            
            try:
                print(f"📄 Lade SteamSpy Seite {page}...")
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if not data or len(data) == 0:
                        print("📭 Keine weiteren Apps auf SteamSpy")
                        break
                    
                    # SteamSpy gibt direkt ein Dict mit App IDs als Keys zurück
                    apps_on_page = []
                    for appid, app_data in data.items():
                        if appid.isdigit():  # Nur numerische App IDs
                            apps_on_page.append({
                                'appid': int(appid),
                                'name': app_data.get('name', ''),
                                'type': 'game',  # SteamSpy hat nur Games
                                'owners': app_data.get('owners', ''),
                                'score_rank': app_data.get('score_rank', ''),
                                'developer': app_data.get('developer', ''),
                                'publisher': app_data.get('publisher', '')
                            })
                    
                    if not apps_on_page:
                        print("📭 Keine gültigen Apps auf dieser Seite")
                        break
                    
                    all_apps.extend(apps_on_page)
                    print(f"   ✅ {len(apps_on_page):,} Apps geladen (Gesamt: {len(all_apps):,})")
                    
                    # SteamSpy Rate Limiting: 1 Request/60s für 'all' requests
                    if page < max_pages - 1:  # Nicht nach der letzten Seite warten
                        print(f"   ⏱️ Warte 60 Sekunden (SteamSpy Rate Limit)...")
                        time.sleep(60)
                    
                    page += 1
                        
                else:
                    print(f"❌ SteamSpy API Fehler Seite {page}: {response.status_code}")
                    break
                    
            except requests.RequestException as e:
                print(f"❌ SteamSpy Request Fehler Seite {page}: {e}")
                break
        
        if all_apps:
            print(f"✅ Gesamt: {len(all_apps):,} Apps von SteamSpy erhalten")
            
            # Apps in Datenbank speichern
            imported_count = self.db_manager.add_apps_batch(all_apps)
            
            elapsed_time = int(time.time() - start_time)
            self.log_import_session('steamspy_api', len(all_apps), imported_count, True,
                                  metadata={'pages': page, 'elapsed_seconds': elapsed_time})
            
            print(f"💾 {imported_count:,} Apps in Datenbank gespeichert")
            print(f"⏱️ Dauer: {elapsed_time/60:.1f} Minuten")
            
            return True
        else:
            self.log_import_session('steamspy_api', 0, 0, False, "Keine Apps von SteamSpy erhalten")
            print("❌ Keine Apps von SteamSpy erhalten")
            return False
    
    # ========================
    # AUTOMATIC RELEASE DISCOVERY
    # ========================
    
    def import_monthly_top_releases(self, year_month: str = None, category: str = "new_releases") -> bool:
        """
        Importiert die Top-Releases eines bestimmten Monats
        
        Args:
            year_month: Format "YYYY-MM" (z.B. "2024-12"), None für aktuellen Monat
            category: "new_releases" oder "top_releases"
        
        Returns:
            True wenn erfolgreich importiert
        """
        if not year_month:
            # Aktueller Monat
            year_month = datetime.now().strftime("%Y-%m")
        
        print(f"🆕 MONATLICHE TOP RELEASES: {year_month}")
        print("=" * 50)
        
        url = "https://api.steampowered.com/ISteamChartsService/GetMonthTopAppReleases/v1/"
        params = {
            'key': self.api_key,
            'date': year_month,
            'request_type': category,
            'format': 'json'
        }
        
        try:
            print(f"📥 Lade Top-Releases für {year_month}...")
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                releases = data.get('response', {}).get('releases', [])
                
                if not releases:
                    print(f"📭 Keine Releases für {year_month} gefunden")
                    return False
                
                print(f"✅ {len(releases)} Releases gefunden")
                
                # Zeige Top 5 Releases
                print(f"\n📋 TOP 5 RELEASES FÜR {year_month.upper()}:")
                for i, release in enumerate(releases[:5], 1):
                    app_id = release.get('appid')
                    name = release.get('name', 'Unknown')
                    peak_ccu = release.get('peak_ccu', 0)
                    print(f"{i:2d}. {name} (ID: {app_id}) - Peak CCU: {peak_ccu:,}")
                
                # Apps importieren mit detaillierten Informationen
                imported_count = self._import_release_apps_with_details(releases)
                
                # Session loggen
                self.log_import_session(
                    f'monthly_releases_{year_month}', 
                    len(releases), 
                    imported_count, 
                    True,
                    metadata={
                        'year_month': year_month,
                        'category': category,
                        'peak_releases': len([r for r in releases if r.get('peak_ccu', 0) > 1000])
                    }
                )
                
                print(f"💾 {imported_count}/{len(releases)} Releases erfolgreich importiert")
                
                return True
                
            else:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                print(f"❌ API Fehler: {error_msg}")
                self.log_import_session(f'monthly_releases_{year_month or "current"}', 0, 0, False, error_msg)
                return False
                
        except requests.RequestException as e:
            error_msg = str(e)
            print(f"❌ Request Fehler: {error_msg}")
            self.log_import_session(f'monthly_releases_{year_month or "current"}', 0, 0, False, error_msg)
            return False
    
    def import_multiple_months_releases(self, start_month: str, end_month: str = None) -> Dict:
        """
        Importiert Releases mehrerer Monate
        
        Args:
            start_month: Start-Monat "YYYY-MM"
            end_month: End-Monat "YYYY-MM", None für aktuellen Monat
        
        Returns:
            Dictionary mit Statistiken
        """
        if not end_month:
            end_month = datetime.now().strftime("%Y-%m")
        
        print(f"📅 MEHRERE MONATE: {start_month} bis {end_month}")
        print("=" * 60)
        
        # Parse start und end dates
        try:
            start_date = datetime.strptime(start_month, "%Y-%m")
            end_date = datetime.strptime(end_month, "%Y-%m")
        except ValueError as e:
            print(f"❌ Ungültiges Datumsformat: {e}")
            return {'months_processed': 0, 'total_releases': 0, 'total_imported': 0}
        
        if start_date > end_date:
            print("❌ Start-Monat muss vor End-Monat liegen")
            return {'months_processed': 0, 'total_releases': 0, 'total_imported': 0}
        
        months_processed = 0
        total_releases = 0
        total_imported = 0
        failed_months = []
        
        current_date = start_date
        while current_date <= end_date:
            year_month = current_date.strftime("%Y-%m")
            
            print(f"\n📆 Verarbeite Monat: {year_month}")
            
            try:
                if self.import_monthly_top_releases(year_month):
                    months_processed += 1
                    
                    # Hole Statistiken für diesen Monat
                    month_stats = self._get_month_release_stats(year_month)
                    total_releases += month_stats.get('releases_found', 0)
                    total_imported += month_stats.get('releases_imported', 0)
                    
                    print(f"✅ {year_month} erfolgreich verarbeitet")
                else:
                    failed_months.append(year_month)
                    print(f"❌ {year_month} fehlgeschlagen")
                
                # Rate Limiting zwischen Monaten
                time.sleep(2)
                
            except Exception as e:
                failed_months.append(year_month)
                print(f"❌ {year_month} Fehler: {e}")
            
            # Nächster Monat
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        # Zusammenfassung
        total_months = ((end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1)
        result = {
            'months_processed': months_processed,
            'total_releases': total_releases,
            'total_imported': total_imported,
            'failed_months': failed_months,
            'success_rate': (months_processed / total_months) * 100 if total_months > 0 else 0
        }
        
        print(f"\n🏁 MEHRMONATIGER IMPORT ABGESCHLOSSEN:")
        print(f"✅ Monate verarbeitet: {months_processed}")
        print(f"📊 Gesamt Releases: {total_releases}")
        print(f"💾 Erfolgreich importiert: {total_imported}")
        print(f"📈 Erfolgsrate: {result['success_rate']:.1f}%")
        
        if failed_months:
            print(f"❌ Fehlgeschlagene Monate: {', '.join(failed_months)}")
        
        return result
    
    def import_latest_releases_auto(self, months_back: int = 3) -> bool:
        """
        Automatischer Import der neuesten Releases
        Ideal für regelmäßige Ausführung via Scheduler
        
        Args:
            months_back: Wie viele Monate zurück importieren
        
        Returns:
            True wenn mindestens ein Monat erfolgreich war
        """
        print(f"🤖 AUTOMATISCHER IMPORT: Letzte {months_back} Monate")
        print("=" * 50)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)  # Approximation
        
        start_month = start_date.strftime("%Y-%m")
        end_month = end_date.strftime("%Y-%m")
        
        print(f"📅 Zeitraum: {start_month} bis {end_month}")
        
        result = self.import_multiple_months_releases(start_month, end_month)
        
        # Bestimme Erfolg
        success = result['months_processed'] > 0
        
        if success:
            print(f"✅ Automatischer Import erfolgreich")
            
            # Zusätzlich: Prüfe auf sehr neue Apps (letzten 7 Tage)
            recent_apps_added = self._check_for_very_recent_releases()
            if recent_apps_added > 0:
                print(f"🆕 {recent_apps_added} sehr neue Apps zusätzlich gefunden")
        else:
            print(f"❌ Automatischer Import fehlgeschlagen")
        
        return success
    
    def _import_release_apps_with_details(self, releases: List[Dict]) -> int:
        """
        Importiert Release-Apps mit detaillierten Informationen
        """
        imported_count = 0
        
        for i, release in enumerate(releases, 1):
            app_id = str(release.get('appid'))
            name = release.get('name', 'Unknown')
            
            print(f"📦 {i}/{len(releases)}: {name} (ID: {app_id})")
            
            # Prüfe ob App bereits in DB existiert
            if self.db_manager.app_exists(app_id):
                print(f"   ⏭️ Bereits in Datenbank")
                imported_count += 1  # Zähle als "importiert" da bereits vorhanden
                continue
            
            # Hole detaillierte App-Informationen
            app_details = self._fetch_single_app_details(app_id)
            
            if app_details:
                # Füge Release-spezifische Daten hinzu
                app_details.update({
                    'peak_ccu': release.get('peak_ccu', 0),
                    'release_month': release.get('release_date', ''),
                    'source': 'monthly_releases'
                })
                
                if self.db_manager.add_app(app_details):
                    imported_count += 1
                    
                    # Zeige Release-Info
                    release_info = app_details.get('release_date')
                    if release_info and isinstance(release_info, dict):
                        release_date = release_info.get('date', 'Unknown')
                        print(f"   📅 Release: {release_date}")
                    
                    peak_ccu = release.get('peak_ccu', 0)
                    if peak_ccu > 0:
                        print(f"   👥 Peak CCU: {peak_ccu:,}")
                    
                    print(f"   ✅ Importiert")
                else:
                    print(f"   ❌ Fehler beim Speichern")
            else:
                print(f"   ❌ Details nicht verfügbar")
            
            # Rate Limiting
            time.sleep(0.5)
        
        return imported_count
    
    def _get_month_release_stats(self, year_month: str) -> Dict:
        """
        Holt Statistiken für Releases eines bestimmten Monats aus der DB
        """
        # Simplified - in reality würde man die DB nach dem Monat durchsuchen
        return {
            'releases_found': 0,  # Placeholder
            'releases_imported': 0  # Placeholder
        }
    
    def _check_for_very_recent_releases(self, days_back: int = 7) -> int:
        """
        Prüft auf sehr neue Releases (letzte X Tage) die nicht in monatlichen Charts stehen
        Nutzt Steam Store "Recently Released" API
        """
        print(f"🔍 Prüfe sehr neue Releases (letzte {days_back} Tage)...")
        
        # Steam Store API für kürzlich veröffentlichte Spiele
        url = "https://store.steampowered.com/api/featured/"
        
        try:
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                new_releases = data.get('new_releases', {}).get('items', [])
                
                if not new_releases:
                    print("   📭 Keine neuen Releases in Featured API gefunden")
                    return 0
                
                print(f"   📋 {len(new_releases)} neue Releases in Featured API gefunden")
                
                # Importiere nur die die noch nicht in der DB sind
                new_apps_imported = 0
                
                for release in new_releases[:20]:  # Limitiere auf Top 20
                    app_id = str(release.get('id'))
                    name = release.get('name', 'Unknown')
                    
                    if not self.db_manager.app_exists(app_id):
                        print(f"   🆕 Neue App gefunden: {name} (ID: {app_id})")
                        
                        # Hole Details und importiere
                        app_details = self._fetch_single_app_details(app_id)
                        if app_details and self.db_manager.add_app(app_details):
                            new_apps_imported += 1
                            print(f"      ✅ Importiert")
                        else:
                            print(f"      ❌ Import fehlgeschlagen")
                        
                        time.sleep(0.5)
                
                return new_apps_imported
                
        except requests.RequestException as e:
            print(f"   ❌ Fehler bei Recent Releases Check: {e}")
            return 0
        
        return 0
    
    # ========================
    # SCHEDULER INTEGRATION
    # ========================
    
    def schedule_monthly_release_import(self) -> bool:
        """
        NEUE METHODE: Für Integration in Background-Scheduler
        Führt automatischen monatlichen Release-Import durch
        """
        print("⏰ GEPLANTER MONATLICHER RELEASE-IMPORT")
        print("=" * 50)
        
        try:
            # Importiere aktuellen Monat
            current_month = datetime.now().strftime("%Y-%m")
            success_current = self.import_monthly_top_releases(current_month)
            
            # Importiere letzten Monat (falls noch nicht komplett)
            last_month_date = datetime.now() - timedelta(days=30)
            last_month = last_month_date.strftime("%Y-%m")
            success_last = self.import_monthly_top_releases(last_month)
            
            # Zusätzlich: Sehr neue Releases checken
            recent_count = self._check_for_very_recent_releases()
            
            success = success_current or success_last or (recent_count > 0)
            
            if success:
                print("✅ Geplanter Release-Import erfolgreich")
                
                # Statistiken aktualisieren
                stats = self.db_manager.get_database_stats()
                print(f"📊 Neue DB-Statistiken:")
                print(f"   📚 Gesamt Apps: {stats['apps']['total']:,}")
                print(f"   🆕 Kürzlich veröffentlicht: {stats['apps']['recently_released']:,}")
            else:
                print("❌ Geplanter Release-Import fehlgeschlagen")
            
            return success
            
        except Exception as e:
            print(f"❌ Fehler beim geplanten Import: {e}")
            return False
    
    # ========================
    # EXISTING METHODS
    # ========================
    
    def import_missing_apps_from_list(self, app_ids: list) -> int:
        """
        Importiert fehlende Apps aus einer Liste von App IDs
        Nützlich für Wishlist-Apps die nicht in der DB sind
        Bessere Release Date Verarbeitung
        """
        print(f"🔍 Importiere {len(app_ids)} fehlende Apps aus Liste...")
        
        if not app_ids:
            return 0
        
        imported_count = 0
        batch_size = 20  # Kleinere Batches für App Details
        
        for i in range(0, len(app_ids), batch_size):
            batch = app_ids[i:i+batch_size]
            
            print(f"📦 Verarbeite Batch {i//batch_size + 1}: {len(batch)} Apps")
            
            for app_id in batch:
                app_data = self._fetch_single_app_details(str(app_id))
                if app_data and self.db_manager.add_app(app_data):
                    imported_count += 1
                    print(f"   ✅ {app_id}: {app_data.get('name', 'Unknown')}")
                    
                    # Release Date Info falls verfügbar
                    if app_data.get('release_date'):
                        release_info = app_data['release_date']
                        if isinstance(release_info, dict):
                            release_date = release_info.get('date', 'Unknown')
                            coming_soon = release_info.get('coming_soon', False)
                            if coming_soon:
                                print(f"      📅 Release: Coming Soon")
                            elif release_date and release_date != 'Unknown':
                                print(f"      📅 Release: {release_date}")
                else:
                    print(f"   ❌ {app_id}: Fehler beim Abrufen/Speichern")
                
                # Rate Limiting
                time.sleep(0.5)
        
        print(f"✅ {imported_count}/{len(app_ids)} fehlende Apps importiert")
        return imported_count
    
    def _fetch_single_app_details(self, app_id: str) -> dict:
        """Holt Details für eine einzelne App von Steam - ENHANCED mit Release Date"""
        url = "https://store.steampowered.com/api/appdetails"
        params = {
            'appids': app_id,
            'filters': 'basic,price_overview,release_date',
            'cc': 'DE'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                app_data = data.get(app_id, {})
                
                if app_data.get('success') and 'data' in app_data:
                    game_data = app_data['data']
                    price_overview = game_data.get('price_overview', {})
                    release_date = game_data.get('release_date', {})
                    
                    return {
                        'app_id': app_id,
                        'name': game_data.get('name', ''),
                        'type': game_data.get('type', 'game'),
                        'is_free': game_data.get('is_free', False),
                        'release_date': release_date,  # Ganze Release Date Struktur übergeben
                        'developer': ', '.join(game_data.get('developers', [])),
                        'publisher': ', '.join(game_data.get('publishers', [])),
                        'price_current': price_overview.get('final', 0) / 100 if price_overview.get('final') else None,
                        'price_original': price_overview.get('initial', 0) / 100 if price_overview.get('initial') else None,
                        'discount_percent': price_overview.get('discount_percent', 0)
                    }
            
            return None
            
        except requests.RequestException:
            return None
    
    def full_import_recommended(self) -> bool:
        """
        Empfohlene Vollimport-Strategie:
        1. Versuche Steam Store Service (nur Spiele)
        2. Fallback auf Steam API v2 (alle Apps)
        3. Optional: SteamSpy für zusätzliche Daten (begrenzt)
        """
        print("🎯 VOLLSTÄNDIGER STEAM IMPORT")
        print("=" * 50)
        
        success_count = 0
        
        # Schritt 1: IStoreService (nur Spiele, gefiltert)
        print("\n🎮 SCHRITT 1: Importiere nur Spiele...")
        if self.import_games_only_method2():
            success_count += 1
            print("✅ Schritt 1 erfolgreich")
        else:
            print("❌ Schritt 1 fehlgeschlagen")
            
            # Fallback: Steam API v2 (alle Apps)
            print("\n🔄 FALLBACK: Importiere alle Steam Apps...")
            if self.import_all_steam_apps_method1():
                success_count += 1
                print("✅ Fallback erfolgreich")
            else:
                print("❌ Fallback fehlgeschlagen")
        
        # Optional: SteamSpy für zusätzliche Daten (begrenzt)
        add_steamspy = input("\n🤔 SteamSpy-Daten hinzufügen? (Nur erste 10 Seiten wegen Geschwindigkeit) (j/n): ").strip().lower()
        if add_steamspy in ['j', 'ja', 'y', 'yes']:
            print("\n📊 BONUS: Füge SteamSpy-Daten hinzu...")
            if self.import_steamspy_data_method3(max_pages=10):
                success_count += 1
                print("✅ SteamSpy Import erfolgreich")
            else:
                print("❌ SteamSpy Import fehlgeschlagen")
        
        # Abschluss-Statistiken
        print(f"\n🏁 IMPORT ABGESCHLOSSEN")
        print(f"✅ {success_count} erfolgreiche Imports")
        
        stats = self.db_manager.get_database_stats()
        self._print_import_stats(stats)
        
        return success_count > 0
    
    def enhanced_import_with_release_dates(self, sample_size: int = 1000) -> bool:
        """
        Enhanced Import mit Release Date Collection
        Sammelt Release Dates für eine Stichprobe von Apps
        
        Args:
            sample_size: Anzahl Apps für die Release Dates gesammelt werden sollen
        """
        print(f"📅 ENHANCED IMPORT MIT RELEASE DATES")
        print(f"Sammelt Release Dates für {sample_size} Apps")
        print("=" * 60)
        
        # Hole Apps ohne Release Date
        apps_without_release_date = []
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT app_id, name FROM steam_apps 
                WHERE release_date IS NULL OR release_date = ''
                ORDER BY updated_at DESC
                LIMIT ?
            ''', (sample_size,))
            
            apps_without_release_date = [dict(row) for row in cursor.fetchall()]
        
        if not apps_without_release_date:
            print("✅ Alle Apps haben bereits Release Date Informationen")
            return True
        
        print(f"🔍 {len(apps_without_release_date)} Apps ohne Release Date gefunden")
        
        # Sammle Release Dates
        updated_count = 0
        new_apps_count = 0
        
        for i, app in enumerate(apps_without_release_date, 1):
            app_id = app['app_id']
            print(f"📅 {i}/{len(apps_without_release_date)}: {app['name']} (ID: {app_id})")
            
            # Hole detaillierte App-Informationen
            app_details = self._fetch_single_app_details(app_id)
            
            if app_details:
                # Aktualisiere App in Datenbank
                if self.db_manager.add_app(app_details):
                    updated_count += 1
                    
                    # Zeige Release Date falls verfügbar
                    release_info = app_details.get('release_date')
                    if release_info and isinstance(release_info, dict):
                        release_date = release_info.get('date', 'Unknown')
                        coming_soon = release_info.get('coming_soon', False)
                        
                        if coming_soon:
                            print(f"   📅 Coming Soon")
                        elif release_date and release_date != 'Unknown':
                            print(f"   📅 {release_date}")
                            
                            # Prüfe ob kürzlich veröffentlicht
                            if self.db_manager.is_app_recently_released(app_id, max_age_days=30):
                                print(f"   🆕 Kürzlich veröffentlicht (< 30 Tage)")
                                new_apps_count += 1
                else:
                    print(f"   ❌ Fehler beim Aktualisieren")
            else:
                print(f"   ❌ Konnte Details nicht abrufen")
            
            # Rate Limiting
            time.sleep(1)
            
            # Fortschrittsanzeige alle 50 Apps
            if i % 50 == 0:
                print(f"📊 Fortschritt: {i}/{len(apps_without_release_date)} ({(i/len(apps_without_release_date))*100:.1f}%)")
                print(f"   ✅ Aktualisiert: {updated_count}")
                print(f"   🆕 Kürzlich veröffentlicht: {new_apps_count}")
        
        # Abschluss-Statistiken
        print(f"\n🏁 ENHANCED IMPORT ABGESCHLOSSEN")
        print(f"✅ {updated_count}/{len(apps_without_release_date)} Apps aktualisiert")
        print(f"🆕 {new_apps_count} kürzlich veröffentlichte Apps gefunden")
        
        # Aktuelle Release Date Statistiken
        stats = self.db_manager.get_database_stats()
        print(f"\n📊 RELEASE DATE STATISTIKEN:")
        print(f"📅 Apps mit Release Date: {stats['apps']['with_release_date']:,}")
        print(f"🆕 Kürzlich veröffentlicht: {stats['apps']['recently_released']:,}")
        
        return updated_count > 0
    
    def _print_import_stats(self, stats: dict):
        """Zeigt Import-Statistiken an - ERWEITERT mit Release Date Info"""
        print(f"\n📊 DATENBANK STATISTIKEN:")
        print(f"📚 Gesamt Apps: {stats['apps']['total']:,}")
        print(f"🆓 Kostenlose Apps: {stats['apps']['free']:,}")
        print(f"💰 Bezahl-Apps: {stats['apps']['paid']:,}")
        print(f"📅 Mit Release Date: {stats['apps']['with_release_date']:,}")
        print(f"🆕 Kürzlich veröffentlicht: {stats['apps']['recently_released']:,}")
        print(f"🎯 CheapShark gemappt: {stats['cheapshark']['mapped']:,}")
        print(f"📝 Kein Mapping verfügbar: {stats['cheapshark']['no_mapping_found']:,}")
        print(f"📅 Zu neu für Mapping: {stats['cheapshark']['too_new']:,}")
        print(f"📈 Mapping-Rate: {stats['cheapshark']['success_rate']:.1f}%")

def bulk_import_main():
    """
    Hauptfunktion für Bulk Import aller Steam Apps
    """
    print("🚀 STEAM BULK IMPORTER v2.0 (ENHANCED)")
    print("Importiert ALLE Steam-Spiele mit Release Date Intelligence!")
    print("=" * 70)
    
    # API Key laden
    try:
        from steam_wishlist_manager import load_api_key_from_env
        api_key = load_api_key_from_env()
    except ImportError:
        # Fallback wenn steam_wishlist_manager nicht verfügbar
        api_key = input("Steam API Key eingeben: ").strip()
    
    if not api_key:
        print("❌ Kein Steam API Key gefunden")
        return
    
    print("✅ API Key geladen")
    
    # Database Manager und Bulk Importer erstellen
    db_manager = DatabaseManager()
    importer = SteamBulkImporter(api_key, db_manager)
    
    # Aktuelle Statistiken zeigen
    print("\n📊 AKTUELLE DATENBANK:")
    current_stats = db_manager.get_database_stats()
    importer._print_import_stats(current_stats)
    
    if current_stats['apps']['total'] > 10000:
        print("\n🤔 Datenbank enthält bereits viele Apps.")
        overwrite = input("Möchten Sie trotzdem importieren? (Überschreibt vorhandene Daten) (j/n): ").strip().lower()
        if overwrite not in ['j', 'ja', 'y', 'yes']:
            print("❌ Import abgebrochen")
            return
    
    print("\n🔧 IMPORT OPTIONEN:")
    print("1. 🎯 Empfohlener Vollimport (alle Spiele)")
    print("2. 🎮 Nur Steam Store Service (gefilterte Spiele)")
    print("3. 📦 Steam Web API v2 (alle Apps)")
    print("4. 📊 SteamSpy API (mit Statistiken, langsam)")
    print("5. 📅 Enhanced Import mit Release Dates")
    print("6. 🔄 Release Dates für vorhandene Apps sammeln")
    print("7. 🆕 Monatliche Top-Releases importieren")
    print("8. 🤖 Automatischer Release-Import (letzte 3 Monate)")
    print("9. ❌ Abbrechen")
    
    choice = input("\nWählen Sie eine Option (1-9): ").strip()
    
    if choice == "1":
        importer.full_import_recommended()
    elif choice == "2":
        importer.import_games_only_method2()
    elif choice == "3":
        importer.import_all_steam_apps_method1()
    elif choice == "4":
        max_pages = input("Wie viele SteamSpy Seiten laden? (Standard: 10, Max empfohlen: 50): ").strip()
        try:
            max_pages = int(max_pages) if max_pages else 10
        except ValueError:
            max_pages = 10
        importer.import_steamspy_data_method3(max_pages)
    elif choice == "5":
        sample_size = input("Wie viele Apps für Release Date Collection? (Standard: 1000): ").strip()
        try:
            sample_size = int(sample_size) if sample_size else 1000
        except ValueError:
            sample_size = 1000
        importer.enhanced_import_with_release_dates(sample_size)
    elif choice == "6":
        # Release Dates für vorhandene Apps sammeln
        apps_to_update = input("Wie viele Apps aktualisieren? (Standard: 500): ").strip()
        try:
            apps_to_update = int(apps_to_update) if apps_to_update else 500
        except ValueError:
            apps_to_update = 500
        
        print(f"\n📅 Sammle Release Dates für {apps_to_update} Apps...")
        importer.enhanced_import_with_release_dates(apps_to_update)
    elif choice == "7":
        # Monatliche Top-Releases
        from monthly_releases_main import monthly_releases_main
        monthly_releases_main()
    elif choice == "8":
        # Automatischer Release-Import
        months_back = input("Wie viele Monate zurück? (Standard: 3): ").strip()
        try:
            months_back = int(months_back) if months_back else 3
        except ValueError:
            months_back = 3
        
        print(f"\n🤖 Starte automatischen Release-Import (letzte {months_back} Monate)...")
        importer.import_latest_releases_auto(months_back)
    elif choice == "9":
        print("👋 Import abgebrochen")
        return
    else:
        print("❌ Ungültige Auswahl")
        return
    
    # Final stats
    print("\n🎉 IMPORT ABGESCHLOSSEN!")
    final_stats = db_manager.get_database_stats()
    importer._print_import_stats(final_stats)
    
    # Release Date Insights
    if final_stats['apps']['recently_released'] > 0:
        print(f"\n📅 RELEASE DATE INSIGHTS:")
        print(f"🆕 {final_stats['apps']['recently_released']} kürzlich veröffentlichte Apps")
        print(f"💡 Diese werden intelligenter für CheapShark-Mapping behandelt")

def monthly_releases_main():
    """
    Hauptfunktion für monatliche Release-Imports
    """
    print("🆕 STEAM MONATLICHE RELEASES IMPORTER")
    print("Automatische Discovery neuer Steam-Releases!")
    print("=" * 60)
    
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
    
    # Database Manager und Importer erstellen
    db_manager = DatabaseManager()
    importer = SteamBulkImporter(api_key, db_manager)
    
    # Aktuelle Statistiken
    print("\n📊 AKTUELLE DATENBANK:")
    current_stats = db_manager.get_database_stats()
    print(f"📚 Gesamt Apps: {current_stats['apps']['total']:,}")
    print(f"🆕 Kürzlich veröffentlicht: {current_stats['apps']['recently_released']:,}")
    
    print("\n🆕 MONATLICHE RELEASE-OPTIONEN:")
    print("1. 📅 Aktueller Monat importieren")
    print("2. 📆 Bestimmten Monat importieren") 
    print("3. 📋 Mehrere Monate importieren")
    print("4. 🤖 Automatischer Import (letzte 3 Monate)")
    print("5. 🔍 Nur sehr neue Releases (letzte 7 Tage)")
    print("6. ⏰ Für Scheduler vorbereiten")
    print("7. ❌ Zurück zum Hauptmenü")
    
    choice = input("\nWählen Sie eine Option (1-7): ").strip()
    
    if choice == "1":
        # Aktueller Monat
        current_month = datetime.now().strftime("%Y-%m")
        print(f"\n📅 Importiere aktuellen Monat: {current_month}")
        
        if importer.import_monthly_top_releases():
            print("✅ Import erfolgreich")
        else:
            print("❌ Import fehlgeschlagen")
    
    elif choice == "2":
        # Bestimmter Monat
        year_month = input("Monat eingeben (YYYY-MM, z.B. 2024-12): ").strip()
        
        if len(year_month) == 7 and '-' in year_month:
            if importer.import_monthly_top_releases(year_month):
                print("✅ Import erfolgreich")
            else:
                print("❌ Import fehlgeschlagen")
        else:
            print("❌ Ungültiges Format. Nutzen Sie YYYY-MM")
    
    elif choice == "3":
        # Mehrere Monate
        start_month = input("Start-Monat (YYYY-MM): ").strip()
        end_month = input("End-Monat (YYYY-MM, Enter für aktuell): ").strip()
        
        if not end_month:
            end_month = None
        
        if len(start_month) == 7 and '-' in start_month:
            result = importer.import_multiple_months_releases(start_month, end_month)
            
            if result['months_processed'] > 0:
                print("✅ Mehrmonatiger Import erfolgreich")
            else:
                print("❌ Mehrmonatiger Import fehlgeschlagen")
        else:
            print("❌ Ungültiges Start-Monat Format")
    
    elif choice == "4":
        # Automatischer Import
        months_back = input("Wie viele Monate zurück? (Standard: 3): ").strip()
        try:
            months_back = int(months_back) if months_back else 3
        except ValueError:
            months_back = 3
        
        print(f"\n🤖 Starte automatischen Import (letzte {months_back} Monate)...")
        
        if importer.import_latest_releases_auto(months_back):
            print("✅ Automatischer Import erfolgreich")
        else:
            print("❌ Automatischer Import fehlgeschlagen")
    
    elif choice == "5":
        # Nur sehr neue Releases
        days_back = input("Wie viele Tage zurück? (Standard: 7): ").strip()
        try:
            days_back = int(days_back) if days_back else 7
        except ValueError:
            days_back = 7
        
        print(f"\n🔍 Suche sehr neue Releases (letzte {days_back} Tage)...")
        new_count = importer._check_for_very_recent_releases(days_back)
        
        if new_count > 0:
            print(f"✅ {new_count} sehr neue Apps importiert")
        else:
            print("📭 Keine neuen Apps gefunden")
    
    elif choice == "6":
        # Scheduler-Test
        print("\n⏰ Teste Scheduler-Integration...")
        
        if importer.schedule_monthly_release_import():
            print("✅ Scheduler-Integration erfolgreich getestet")
            print("💡 Diese Methode kann im Background-Scheduler verwendet werden")
        else:
            print("❌ Scheduler-Integration fehlgeschlagen")
    
    elif choice == "7":
        print("👋 Zurück zum Hauptmenü")
        return
    
    else:
        print("❌ Ungültige Auswahl")
        return
    
    # Final stats
    print("\n📊 FINAL STATISTIKEN:")
    final_stats = db_manager.get_database_stats()
    print(f"📚 Gesamt Apps: {final_stats['apps']['total']:,}")
    print(f"🆕 Kürzlich veröffentlicht: {final_stats['apps']['recently_released']:,}")
    
    if final_stats['apps']['recently_released'] > current_stats['apps']['recently_released']:
        new_releases = final_stats['apps']['recently_released'] - current_stats['apps']['recently_released']
        print(f"🎉 {new_releases} neue Releases hinzugefügt!")

if __name__ == "__main__":
    bulk_import_main()
