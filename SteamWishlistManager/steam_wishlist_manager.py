"""
Steam Wishlist Manager - Hauptmanager v2.0
Modulare Architektur mit automatischem CheapShark-Mapping
"""

import requests
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

# Module imports
from database_manager import DatabaseManager
from steam_bulk_importer import SteamBulkImporter
from cheapshark_mapping_processor import CheapSharkMappingProcessor

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_api_key_from_env(env_file=".env") -> Optional[str]:
    """
    Lädt den Steam API Key aus einer .env-Datei
    """
    env_path = Path(env_file)
    
    if not env_path.exists():
        return None
    
    try:
        # Versuche python-dotenv zu verwenden (falls installiert)
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
            api_key = os.getenv('STEAM_API_KEY')
            if api_key:
                return api_key.strip()
        except ImportError:
            pass
        
        # Manuelle .env-Parsing als Fallback
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or not line or '=' not in line:
                    continue
                
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Entferne Anführungszeichen falls vorhanden
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                if key == 'STEAM_API_KEY':
                    return value
        
        return None
        
    except Exception as e:
        logger.error(f"⚠️ Fehler beim Lesen der .env-Datei: {e}")
        return None

def create_env_template(env_file=".env") -> bool:
    """Erstellt eine .env-Template-Datei falls sie nicht existiert"""
    env_path = Path(env_file)
    
    if env_path.exists():
        return False
    
    try:
        template_content = """# Steam Wishlist Manager Konfiguration
# Trage hier deinen Steam Web API Key ein
# Erhältlich unter: https://steamcommunity.com/dev/apikey
STEAM_API_KEY=your_steam_api_key_here

# Beispiel:
# STEAM_API_KEY=ABCD1234567890EFGH
"""
        
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        logger.info(f"📝 .env-Template erstellt: {env_file}")
        print("   Bitte trage deinen Steam API Key ein und starte das Programm erneut.")
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen der .env-Datei: {e}")
        return False

class SteamWishlistManager:
    """
    Hauptmanager für Steam Wishlist Operationen
    Koordiniert alle Module: Database, Bulk Import, CheapShark Mapping
    """
    
    def __init__(self, api_key: str, db_path: str = "steam_wishlist.db"):
        self.api_key = api_key
        self.steam_base_url = "https://api.steampowered.com"
        self.steam_store_url = "https://store.steampowered.com/api"
        
        # Session für Steam API Requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SteamWishlistManager/2.0'
        })
        
        # Module initialisieren
        self.db_manager = DatabaseManager(db_path)
        self.bulk_importer = SteamBulkImporter(api_key, self.db_manager)
        self.cheapshark_processor = CheapSharkMappingProcessor(api_key, self.db_manager)
        
        # Cache für Steam Preise
        self.steam_price_cache = {}
        
        logger.info("✅ Steam Wishlist Manager initialisiert")
    
    # ========================
    # CORE WISHLIST OPERATIONS
    # ========================
    
    def get_player_info(self, steam_id: str) -> Optional[Dict]:
        """Ruft Spielerinformationen ab"""
        url = f"{self.steam_base_url}/ISteamUser/GetPlayerSummaries/v0002/"
        
        params = {
            'key': self.api_key,
            'steamids': steam_id,
            'format': 'json'
        }
        
        try:
            logger.info(f"👤 Rufe Spielerinformationen für {steam_id} ab...")
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                players = data.get('response', {}).get('players', [])
                
                if players and len(players) > 0:
                    player = players[0]
                    player_info = {
                        'steam_id': player.get('steamid'),
                        'username': player.get('personaname'),
                        'real_name': player.get('realname'),
                        'profile_url': player.get('profileurl'),
                        'avatar_url': player.get('avatarfull'),
                        'country_code': player.get('loccountrycode'),
                        'profile_state': player.get('profilestate'),
                        'last_logoff': player.get('lastlogoff'),
                        'account_created': player.get('timecreated')
                    }
                    logger.info(f"✅ Spieler gefunden: {player_info['username']}")
                    return player_info
                else:
                    logger.warning("⚠️ Keine Spielerdaten gefunden")
                    return None
            else:
                logger.error(f"❌ HTTP Error {response.status_code}: {response.text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"❌ Request Error: {e}")
            return None
    
    def get_wishlist_from_steam(self, steam_id: str) -> List[Dict]:
        """
        Ruft Wishlist direkt von Steam ab
        Verwendet GetWishlistSortedFiltered für bessere Datenqualität
        """
        url = f"{self.steam_base_url}/IWishlistService/GetWishlistSortedFiltered/v1/"
        
        all_items = []
        page_size = 100
        start_index = 0
        
        while True:
            params = {
                'key': self.api_key,
                'steamid': steam_id,
                'sort_order': 'date_added',
                'start_index': start_index,
                'page_size': page_size,
                'format': 'json'
            }
            
            try:
                response = self.session.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    response_data = data.get('response', {})
                    page_items = response_data.get('items', [])
                    
                    if not page_items:
                        break
                    
                    all_items.extend(page_items)
                    logger.info(f"📄 Seite {start_index//page_size + 1}: {len(page_items)} Items geladen (Gesamt: {len(all_items)})")
                    
                    start_index += page_size
                    
                    # Rate Limiting
                    time.sleep(0.5)
                    
                else:
                    logger.error(f"❌ Wishlist API Error: {response.status_code}")
                    break
                    
            except requests.RequestException as e:
                logger.error(f"❌ Wishlist Request Error: {e}")
                break
        
        logger.info(f"✅ {len(all_items)} Wishlist-Items von Steam abgerufen")
        return all_items
    
    def check_and_add_missing_apps(self, wishlist_items: List[Dict]) -> Tuple[int, List[str]]:
        """
        Prüft welche Wishlist-Apps in der Datenbank fehlen und fügt sie hinzu
        Returns: (added_count, missing_app_ids)
        """
        if not wishlist_items:
            return 0, []
        
        app_ids = [str(item.get('appid')) for item in wishlist_items if item.get('appid')]
        missing_apps = []
        
        logger.info(f"🔍 Prüfe {len(app_ids)} Apps in Wishlist...")
        
        # Prüfe welche Apps fehlen
        for app_id in app_ids:
            if not self.db_manager.app_exists(app_id):
                missing_apps.append(app_id)
        
        if not missing_apps:
            logger.info("✅ Alle Wishlist-Apps sind bereits in der Datenbank")
            return 0, []
        
        logger.info(f"📥 {len(missing_apps)} fehlende Apps gefunden - importiere...")
        
        # Fehlende Apps importieren
        added_count = self.bulk_importer.import_missing_apps_from_list(missing_apps)
        
        logger.info(f"✅ {added_count}/{len(missing_apps)} fehlende Apps importiert")
        
        return added_count, missing_apps
    
    def process_complete_wishlist(self, steam_id: str, 
                                include_cheapshark: bool = True,
                                include_steam_prices: bool = True,
                                auto_schedule_mapping: bool = True,
                                country_code: str = "DE") -> Optional[Dict]:
        """
        Vollständige Wishlist-Verarbeitung mit automatischem Missing-Apps Import
        """
        logger.info(f"🎯 Starte vollständige Wishlist-Verarbeitung für {steam_id}")
        
        # Schritt 1: Spielerinformationen abrufen
        player_info = self.get_player_info(steam_id)
        if not player_info:
            logger.error("❌ Konnte Spielerinformationen nicht abrufen")
            return None
        
        # Schritt 2: Wishlist von Steam abrufen
        steam_wishlist_items = self.get_wishlist_from_steam(steam_id)
        if not steam_wishlist_items:
            logger.warning("📭 Wishlist ist leer oder konnte nicht abgerufen werden")
            return {
                'metadata': self._create_metadata(steam_id, player_info, country_code),
                'total_count': 0,
                'items': []
            }
        
        # Schritt 3: Fehlende Apps zur Datenbank hinzufügen
        added_apps, missing_app_ids = self.check_and_add_missing_apps(steam_wishlist_items)
        
        if added_apps > 0:
            logger.info(f"📥 {added_apps} neue Apps zur Datenbank hinzugefügt")
        
        # Schritt 4: Wishlist-Items in Datenbank speichern
        added_items, still_missing = self.db_manager.add_wishlist_items(steam_id, steam_wishlist_items)
        
        if still_missing > 0:
            logger.warning(f"⚠️ {still_missing} Apps konnten nicht zur Wishlist hinzugefügt werden (fehlen in DB)")
        
        logger.info(f"📝 {added_items} Wishlist-Items in Datenbank gespeichert")
        
        # Schritt 5: CheapShark-Mapping für neue Apps schedulen
        if auto_schedule_mapping and missing_app_ids:
            scheduled_count = self.cheapshark_processor.add_missing_apps_to_queue(missing_app_ids, priority=8)
            logger.info(f"📅 {scheduled_count} Apps für CheapShark-Mapping geplant")
        
        # Schritt 6: Vollständige Wishlist aus Datenbank abrufen
        complete_wishlist = self.db_manager.get_wishlist_items(steam_id, include_cheapshark=include_cheapshark)
        
        # Schritt 7: Steam-Preisinformationen hinzufügen (falls gewünscht)
        if include_steam_prices:
            complete_wishlist = self.enrich_with_steam_prices(complete_wishlist, country_code)
        
        # Ergebnis zusammenstellen
        result = {
            'metadata': self._create_metadata(steam_id, player_info, country_code, 
                                            added_apps=added_apps, added_items=added_items),
            'total_count': len(complete_wishlist),
            'items': complete_wishlist
        }
        
        logger.info(f"✅ Wishlist-Verarbeitung abgeschlossen: {len(complete_wishlist)} Items")
        
        return result
    
    def _create_metadata(self, steam_id: str, player_info: Dict, country_code: str, 
                        added_apps: int = 0, added_items: int = 0) -> Dict:
        """Erstellt Metadata für Wishlist-Ergebnis"""
        return {
            'steam_id': steam_id,
            'username': player_info.get('username', 'Unknown'),
            'player_info': player_info,
            'retrieved_at': datetime.now().isoformat(),
            'country_code': country_code,
            'processing_stats': {
                'added_apps_to_db': added_apps,
                'added_wishlist_items': added_items
            }
        }
    
    # ========================
    # STEAM PRICE INTEGRATION
    # ========================
    
    def enrich_with_steam_prices(self, wishlist_items: List[Dict], country_code: str = "DE") -> List[Dict]:
        """Reichert Wishlist-Items mit aktuellen Steam-Preisen an"""
        if not wishlist_items:
            return wishlist_items
        
        app_ids = [item['app_id'] for item in wishlist_items]
        logger.info(f"💰 Rufe Steam-Preise für {len(app_ids)} Apps ab...")
        
        # Hole Preisinformationen
        price_data = self.get_steam_price_info(app_ids, country_code)
        
        # Reichere Items an
        enriched_items = []
        found_prices = 0
        
        for item in wishlist_items:
            app_id = item['app_id']
            price_info = price_data.get(app_id, {})
            
            # Füge Preisinformationen hinzu
            enriched_item = dict(item)
            enriched_item['current_steam_price'] = price_info
            
            if price_info.get('final_price') is not None:
                found_prices += 1
            
            enriched_items.append(enriched_item)
        
        logger.info(f"✅ Steam-Preise geladen: {found_prices}/{len(wishlist_items)} Apps")
        return enriched_items
    
    def get_steam_price_info(self, app_ids: List[str], country_code: str = "DE") -> Dict:
        """Holt Steam-Preisinformationen für mehrere Apps"""
        if not app_ids:
            return {}
        
        # Cache prüfen
        results = {}
        uncached_ids = []
        
        for app_id in app_ids:
            cache_key = f"{app_id}_{country_code}"
            if cache_key in self.steam_price_cache:
                results[app_id] = self.steam_price_cache[cache_key]
            else:
                uncached_ids.append(app_id)
        
        if not uncached_ids:
            return results
        
        logger.info(f"🔄 {len(uncached_ids)} neue Preis-Anfragen (Cache: {len(results)})")
        
        # Batch-Verarbeitung für neue Preise
        batch_size = 10
        for i in range(0, len(uncached_ids), batch_size):
            batch_ids = uncached_ids[i:i+batch_size]
            
            for app_id in batch_ids:
                price_info = self._fetch_single_app_price(app_id, country_code)
                results[app_id] = price_info
                
                # Cache das Ergebnis
                cache_key = f"{app_id}_{country_code}"
                self.steam_price_cache[cache_key] = price_info
                
                # Rate Limiting
                time.sleep(0.5)
        
        return results
    
    def _fetch_single_app_price(self, app_id: str, country_code: str) -> Dict:
        """Holt Preisinformationen für eine einzelne App"""
        url = f"{self.steam_store_url}/appdetails"
        params = {
            'appids': app_id,
            'filters': 'price_overview,basic',
            'cc': country_code
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                app_data = data.get(app_id, {})
                
                if app_data.get('success') and 'data' in app_data:
                    game_data = app_data['data']
                    price_overview = game_data.get('price_overview')
                    
                    price_info = {
                        'currency': None,
                        'initial_price': None,
                        'final_price': None,
                        'discount_percent': 0,
                        'is_free': game_data.get('is_free', False),
                        'formatted_initial': None,
                        'formatted_final': None
                    }
                    
                    if price_overview:
                        initial = price_overview.get('initial', 0)
                        final = price_overview.get('final', 0)
                        
                        price_info.update({
                            'currency': price_overview.get('currency', 'EUR'),
                            'initial_price': initial / 100 if initial else 0,
                            'final_price': final / 100 if final else 0,
                            'discount_percent': price_overview.get('discount_percent', 0),
                            'formatted_initial': price_overview.get('initial_formatted', ''),
                            'formatted_final': price_overview.get('final_formatted', '')
                        })
                    elif game_data.get('is_free'):
                        price_info.update({
                            'currency': 'EUR',
                            'initial_price': 0.0,
                            'final_price': 0.0,
                            'formatted_initial': 'Kostenlos',
                            'formatted_final': 'Kostenlos'
                        })
                    
                    return price_info
            
            # Fallback für Fehler/nicht verfügbare Apps
            return {
                'currency': None,
                'initial_price': None,
                'final_price': None,
                'discount_percent': 0,
                'is_free': False,
                'formatted_initial': 'Nicht verfügbar',
                'formatted_final': 'Nicht verfügbar',
                'error': f"HTTP {response.status_code}"
            }
            
        except requests.RequestException as e:
            return {
                'currency': None,
                'initial_price': None,
                'final_price': None,
                'discount_percent': 0,
                'is_free': False,
                'formatted_initial': 'Request Fehler',
                'formatted_final': 'Request Fehler',
                'error': str(e)
            }
    
    # ========================
    # UTILITY METHODS
    # ========================
    
    def save_wishlist_to_file(self, wishlist_data: Dict, filename: str = None) -> str:
        """Speichert Wishlist-Daten als JSON-Datei"""
        output_dir = Path("Output")
        output_dir.mkdir(exist_ok=True)
        
        if not filename:
            steam_id = wishlist_data['metadata']['steam_id']
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"steam_wishlist_{steam_id}_{timestamp}.json"
        
        filepath = output_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(wishlist_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"💾 Wishlist gespeichert: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
            return None
    
    def print_wishlist_summary(self, wishlist_data: Dict):
        """Gibt eine Zusammenfassung der Wishlist aus"""
        if not wishlist_data:
            print("❌ Keine Wishlist-Daten verfügbar")
            return
        
        total = wishlist_data.get('total_count', 0)
        items = wishlist_data.get('items', [])
        metadata = wishlist_data.get('metadata', {})
        
        print(f"\n📊 WISHLIST ZUSAMMENFASSUNG")
        print(f"{'='*50}")
        print(f"Steam ID: {metadata.get('steam_id')}")
        print(f"Username: {metadata.get('username')}")
        print(f"Gesamtanzahl: {total}")
        print(f"Zeitpunkt: {metadata.get('retrieved_at')}")
        
        # Processing Stats
        processing_stats = metadata.get('processing_stats', {})
        if processing_stats.get('added_apps_to_db', 0) > 0:
            print(f"Neue Apps hinzugefügt: {processing_stats['added_apps_to_db']}")
        
        if items and len(items) > 0:
            print(f"\n📋 ERSTE 5 SPIELE:")
            
            # Sortiere nach Priorität und Datum
            sorted_items = sorted(items, key=lambda x: (x.get('priority', 0), x.get('date_added', '')), reverse=True)
            
            for i, item in enumerate(sorted_items[:5], 1):
                app_id = item.get('app_id', 'N/A')
                name = item.get('name', 'Unbekannt')
                
                # Preisinformationen anzeigen
                price_info = ""
                
                # Aktueller Steam-Preis
                current_price = item.get('current_steam_price')
                if current_price and current_price.get('final_price') is not None:
                    if current_price.get('discount_percent', 0) > 0:
                        price_info = f" - {current_price['formatted_final']} (-{current_price['discount_percent']}%)"
                    else:
                        price_info = f" - {current_price['formatted_final']}"
                
                # DB-Preis als Fallback
                elif item.get('price_current') is not None:
                    price_info = f" - €{item['price_current']:.2f}"
                
                print(f"{i:2d}. {name} (ID: {app_id}){price_info}")
                
                # CheapShark-Info falls verfügbar
                if item.get('cheapshark_game_id'):
                    cheapest = item.get('cheapest_price_ever')
                    if cheapest:
                        print(f"     💰 Bester Preis jemals: ${cheapest}")
        
        # Statistiken
        with_cheapshark = sum(1 for item in items if item.get('cheapshark_game_id'))
        with_current_price = sum(1 for item in items if item.get('current_steam_price', {}).get('final_price') is not None)
        
        print(f"\n📈 STATISTIKEN:")
        print(f"CheapShark-Mappings: {with_cheapshark}/{total} ({(with_cheapshark/total)*100:.1f}%)")
        print(f"Aktuelle Preise: {with_current_price}/{total} ({(with_current_price/total)*100:.1f}%)")
        
        print(f"\n{'='*50}")
    
    def get_manager_status(self) -> Dict:
        """Gibt umfassenden Status des Managers zurück"""
        db_stats = self.db_manager.get_database_stats()
        scheduler_status = self.cheapshark_processor.get_scheduler_status()
        
        return {
            'database': db_stats,
            'scheduler': scheduler_status,
            'cache_size': len(self.steam_price_cache)
        }

def main():
    """Hauptfunktion für interaktive Nutzung"""
    print("🎮 STEAM WISHLIST MANAGER v2.0")
    print("Modulare Architektur mit automatischem Mapping")
    print("=" * 60)
    
    # API Key laden
    api_key = load_api_key_from_env()
    
    if not api_key:
        print("⚠️ Kein API Key in .env gefunden")
        
        if create_env_template():
            return
        
        api_key = input("Steam API Key eingeben: ").strip()
    
    if not api_key:
        print("❌ Kein API Key angegeben")
        return
    
    print("✅ API Key geladen")
    
    # Manager erstellen
    try:
        manager = SteamWishlistManager(api_key)
        print("✅ Steam Wishlist Manager initialisiert")
    except Exception as e:
        print(f"❌ Fehler beim Initialisieren: {e}")
        return
    
    # Hauptmenü
    while True:
        print("\n🔧 VERFÜGBARE AKTIONEN:")
        print("1. 🎯 Wishlist abrufen und verarbeiten")
        print("2. 📊 Manager-Status anzeigen")
        print("3. 📥 Bulk Import durchführen")
        print("4. 🔗 CheapShark-Mapping verwalten")
        print("5. 🚀 Background-Scheduler starten/stoppen")
        print("6. 🧹 Datenbank bereinigen")
        print("7. ❌ Beenden")
        
        choice = input("\nWählen Sie eine Aktion (1-7): ").strip()
        
        if choice == "1":
            # Wishlist abrufen und verarbeiten
            steam_id = input("Steam ID (17 Ziffern) eingeben: ").strip()
            
            if not steam_id or len(steam_id) != 17 or not steam_id.isdigit():
                print("❌ Ungültige Steam ID")
                continue
            
            # Optionen abfragen
            print("\n🛠️ Verarbeitungsoptionen:")
            include_prices = input("Aktuelle Steam-Preise hinzufügen? (j/n): ").lower() in ['j', 'ja', 'y', 'yes']
            include_cheapshark = input("CheapShark-Daten hinzufügen? (j/n): ").lower() in ['j', 'ja', 'y', 'yes']
            auto_schedule = input("Automatisches CheapShark-Mapping für neue Apps? (j/n): ").lower() in ['j', 'ja', 'y', 'yes']
            
            country_code = "DE"
            if include_prices:
                country_input = input("Ländercode (DE/US/UK, Enter für DE): ").strip().upper()
                if country_input:
                    country_code = country_input
            
            # Wishlist verarbeiten
            print(f"\n🚀 Starte Wishlist-Verarbeitung...")
            wishlist_data = manager.process_complete_wishlist(
                steam_id,
                include_cheapshark=include_cheapshark,
                include_steam_prices=include_prices,
                auto_schedule_mapping=auto_schedule,
                country_code=country_code
            )
            
            if wishlist_data:
                manager.print_wishlist_summary(wishlist_data)
                
                # Speichern anbieten
                if input("\nAls JSON speichern? (j/n): ").lower() in ['j', 'ja', 'y', 'yes']:
                    filepath = manager.save_wishlist_to_file(wishlist_data)
                    if filepath:
                        print(f"✅ Gespeichert: {filepath}")
            else:
                print("❌ Wishlist konnte nicht verarbeitet werden")
        
        elif choice == "2":
            # Manager-Status anzeigen
            status = manager.get_manager_status()
            
            print(f"\n📊 MANAGER STATUS:")
            print(f"=" * 40)
            
            # Datenbank
            db = status['database']
            print(f"📚 Apps in DB: {db['apps']['total']:,}")
            print(f"🎯 CheapShark gemappt: {db['cheapshark']['mapped']:,} ({db['cheapshark']['success_rate']:.1f}%)")
            print(f"📋 Wishlist Items: {db['wishlist']['total_items']:,}")
            print(f"👥 Unique Users: {db['wishlist']['unique_users']:,}")
            
            # Scheduler
            scheduler = status['scheduler']
            print(f"🚀 Scheduler: {'Läuft' if scheduler['scheduler_running'] else 'Gestoppt'}")
            print(f"📋 Queue: {scheduler['pending_jobs']:,} ausstehend, {scheduler['failed_jobs']:,} fehlgeschlagen")
            
            # Cache
            print(f"💾 Preis-Cache: {status['cache_size']} Einträge")
        
        elif choice == "3":
            # Bulk Import
            print("\n📥 Führe Bulk Import durch...")
            if manager.bulk_importer.full_import_recommended():
                print("✅ Bulk Import erfolgreich abgeschlossen")
            else:
                print("❌ Bulk Import fehlgeschlagen")
        
        elif choice == "4":
            # CheapShark-Mapping verwalten
            print("\n🔗 CheapShark-Mapping Optionen:")
            print("1. Manuelle Verarbeitung starten")
            print("2. Wishlist-Apps priorisieren")
            print("3. Queue-Status anzeigen")
            
            mapping_choice = input("Wählen Sie (1-3): ").strip()
            
            if mapping_choice == "1":
                max_apps = input("Wie viele Apps verarbeiten? (Standard: 1000): ").strip()
                try:
                    max_apps = int(max_apps) if max_apps else 1000
                except ValueError:
                    max_apps = 1000
                
                manager.cheapshark_processor.process_mapping_manual(max_apps=max_apps)
            
            elif mapping_choice == "2":
                steam_id = input("Steam ID für Priorisierung: ").strip()
                if steam_id:
                    count = manager.cheapshark_processor.process_wishlist_apps_priority(steam_id)
                    print(f"🎯 {count} Wishlist-Apps priorisiert")
            
            elif mapping_choice == "3":
                queue_stats = manager.db_manager.get_database_stats()['queue']
                print(f"📋 Ausstehend: {queue_stats['pending']}")
                print(f"❌ Fehlgeschlagen: {queue_stats['failed']}")
        
        elif choice == "5":
            # Scheduler starten/stoppen
            scheduler_status = manager.cheapshark_processor.get_scheduler_status()
            
            if scheduler_status['scheduler_running']:
                print("🛑 Stoppe Background-Scheduler...")
                manager.cheapshark_processor.stop_background_scheduler()
                print("✅ Scheduler gestoppt")
            else:
                print("🚀 Starte Background-Scheduler...")
                manager.cheapshark_processor.start_background_scheduler()
                print("✅ Scheduler gestartet")
        
        elif choice == "6":
            # Datenbank bereinigen
            days = input("Daten älter als X Tage löschen (Standard: 30): ").strip()
            try:
                days = int(days) if days else 30
            except ValueError:
                days = 30
            
            manager.db_manager.cleanup_old_data(days)
            print(f"✅ Bereinigung abgeschlossen")
        
        elif choice == "7":
            # Beenden
            print("🛑 Stoppe alle Services...")
            
            if manager.cheapshark_processor.scheduler_running:
                manager.cheapshark_processor.stop_background_scheduler()
            
            print("👋 Steam Wishlist Manager beendet")
            break
        
        else:
            print("❌ Ungültige Auswahl")

if __name__ == "__main__":
    main()