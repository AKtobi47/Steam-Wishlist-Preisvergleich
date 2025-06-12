"""
Steam Bulk Importer - ENHANCED Version mit Release Date Support
Nutzt die zentrale DatabaseManager Klasse
ERWEITERT: Bessere Release Date Verarbeitung für intelligente CheapShark-Mappings
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path
from database_manager import DatabaseManager

class SteamBulkImporter:
    """
    Importiert ALLE verfügbaren Steam-Spiele auf einmal über verschiedene APIs
    Nutzt DatabaseManager für alle Datenbankoperationen
    ERWEITERT: Bessere Release Date Verarbeitung
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
    
    def import_missing_apps_from_list(self, app_ids: list) -> int:
        """
        Importiert fehlende Apps aus einer Liste von App IDs
        Nützlich für Wishlist-Apps die nicht in der DB sind
        ERWEITERT: Bessere Release Date Verarbeitung
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
        NEUE METHODE: Enhanced Import mit Release Date Collection
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
    ERWEITERT: Release Date Features
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
    print("7. ❌ Abbrechen")
    
    choice = input("\nWählen Sie eine Option (1-7): ").strip()
    
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

if __name__ == "__main__":
    bulk_import_main()
