import requests
import json
import os
from datetime import datetime
import time
from urllib.parse import quote
import sqlite3
from pathlib import Path

def load_api_key_from_env(env_file=".env"):
    """
    Lädt den Steam API Key aus einer .env-Datei
    
    Args:
        env_file (str): Pfad zur .env-Datei (default: ".env")
        
    Returns:
        str: API Key oder None falls nicht gefunden
    """
    env_path = Path(env_file)
    
    # Prüfe ob .env-Datei existiert
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
            # Fallback: Manuelle .env-Parsing
            pass
        
        # Manuelle .env-Parsing als Fallback
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Überspringe Kommentare und leere Zeilen
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
        print(f"⚠️  Fehler beim Lesen der .env-Datei: {e}")
        return None

def create_env_template(env_file=".env"):
    """
    Erstellt eine .env-Template-Datei falls sie nicht existiert
    
    Args:
        env_file (str): Pfad zur .env-Datei
        
    Returns:
        bool: True wenn Datei erstellt wurde
    """
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
        
        print(f"📝 .env-Template erstellt: {env_file}")
        print("   Bitte trage deinen Steam API Key ein und starte das Programm erneut.")
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der .env-Datei: {e}")
        return False

class SteamWishlistManager:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.steampowered.com"
        self.steam_store_url = "https://store.steampowered.com/api"
        self.cheapshark_base_url = "https://www.cheapshark.com/api/1.0"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SteamWishlistManager/1.0'
        })
        # Cache für Steam Preise
        self.steam_price_cache = {}
        # Lokale Datenbank für CheapShark Matching
        self.db_path = "cheapshark_mapping.db"
        self._init_database()
    
    def _init_database(self):
        """Initialisiert die lokale SQLite-Datenbank für CheapShark-Mappings"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tabelle für CheapShark-Steam Mapping erstellen
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cheapshark_mapping (
                    steam_app_id TEXT PRIMARY KEY,
                    cheapshark_game_id TEXT,
                    game_title TEXT,
                    thumb_url TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Index für bessere Performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cheapshark_id ON cheapshark_mapping(cheapshark_game_id)')
            
            conn.commit()
            conn.close()
            
        except sqlite3.Error as e:
            print(f"⚠️  Datenbank-Initialisierung Fehler: {e}")
    
    def download_cheapshark_catalog(self, force_update=False):
        """
        Lädt den kompletten CheapShark-Katalog herunter und speichert ihn lokal
        VERBESSERTE VERSION mit alternativen Parametern
        """
        # Prüfe ob Update nötig ist
        if not force_update and self._is_catalog_current():
            print("✅ CheapShark-Katalog ist aktuell")
            return True
    
        print("📥 Lade CheapShark-Katalog herunter...")
    
        try:
            # NEUE STRATEGIE: Verwende andere Parameter
            url = f"{self.cheapshark_base_url}/games"
        
            # Versuche verschiedene Parameter-Kombinationen
            param_sets = [
                # Strategie 1: Ohne Limit-Parameter
                {'exact': 0},
                # Strategie 2: Kleineres Limit
                {'limit': 10000, 'exact': 0},
                # Strategie 3: Noch kleineres Limit
                {'limit': 5000},
                # Strategie 4: Minimal
                {}
            ]
        
            for i, params in enumerate(param_sets, 1):
                print(f"🔄 Versuche Strategie {i}: {params}")
            
                response = self.session.get(url, params=params, timeout=120)
            
                if response.status_code == 429:  # Rate limit
                    print("⚠️  Rate limit erreicht, warte 60 Sekunden...")
                    time.sleep(60)
                    response = self.session.get(url, params=params, timeout=120)
            
                if response.status_code == 200:
                    games = response.json()
                    print(f"✅ Strategie {i} erfolgreich! {len(games)} Spiele erhalten")
                    break
                
                elif response.status_code == 400:
                    print(f"❌ Strategie {i} fehlgeschlagen (400): {response.text[:100]}...")
                    continue
                
                else:
                    print(f"❌ Strategie {i} fehlgeschlagen ({response.status_code})")
                    continue
            else:
                # Alle Strategien fehlgeschlagen
                print("❌ Alle CheapShark-Strategien fehlgeschlagen")
                print("💡 Deaktiviere CheapShark-Integration für diese Sitzung")
                return False
        
            # Daten speichern (falls erfolgreich)
            if 'games' in locals() and games:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
            
                # Alte Daten löschen
                cursor.execute('DELETE FROM cheapshark_mapping')
            
                # Neue Daten einfügen
                insert_count = 0
                for game in games:
                    steam_app_id = game.get('steamAppID')
                    if steam_app_id:  # Nur Spiele mit Steam App ID
                        cursor.execute('''
                            INSERT OR REPLACE INTO cheapshark_mapping 
                            (steam_app_id, cheapshark_game_id, game_title, thumb_url)
                            VALUES (?, ?, ?, ?)
                        ''', (
                            steam_app_id,
                            game.get('gameID'),
                            game.get('external'),
                            game.get('thumb')
                        ))
                        insert_count += 1
            
                conn.commit()
                conn.close()
            
                print(f"✅ {insert_count} Steam-Spiele in lokaler Datenbank gespeichert")
                return True
        
            return False
        
        except requests.RequestException as e:
            print(f"❌ CheapShark-Katalog Download Request-Fehler: {e}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ CheapShark-Katalog JSON-Parsing Fehler: {e}")
            return False
        except Exception as e:
            print(f"❌ CheapShark-Katalog Download Unerwarteter Fehler: {e}")
            return False
    
    def _is_catalog_current(self):
        """Prüft ob der Katalog aktuell ist (nicht älter als 7 Tage)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) as count, 
                       MAX(last_updated) as last_update 
                FROM cheapshark_mapping
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            if not result or result[0] == 0:
                return False
            
            # Prüfe Alter der Daten
            if result[1]:
                last_update = datetime.fromisoformat(result[1].replace(' ', 'T'))
                days_old = (datetime.now() - last_update).days
                return days_old < 7
            
            return False
            
        except Exception:
            return False
    
    def get_cheapshark_id_from_db(self, steam_app_id):
        """
        Ruft CheapShark Game ID aus lokaler Datenbank ab
        
        Args:
            steam_app_id (str): Steam App ID
            
        Returns:
            dict: CheapShark-Daten oder None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT cheapshark_game_id, game_title, thumb_url 
                FROM cheapshark_mapping 
                WHERE steam_app_id = ?
            ''', (str(steam_app_id),))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'game_id': result[0],
                    'title': result[1],
                    'thumb': result[2],
                    'found': True
                }
            else:
                return {
                    'game_id': None,
                    'found': False
                }
                
        except sqlite3.Error as e:
            print(f"⚠️  Datenbank-Abfrage Fehler: {e}")
            return {'game_id': None, 'found': False}

    def get_steam_price_info(self, app_ids, country_code="DE"):
        """
        Ruft Steam Preisinformationen für mehrere Apps ab (Batch-Request)
        VERBESSERTE VERSION mit kleineren Batches
        """
        if not app_ids:
            return {}
        
        # Cache prüfen
        uncached_ids = []
        results = {}
        
        for app_id in app_ids:
            cache_key = f"{app_id}_{country_code}"
            if cache_key in self.steam_price_cache:
                results[app_id] = self.steam_price_cache[cache_key]
            else:
                uncached_ids.append(app_id)
        
        if not uncached_ids:
            return results
        
        print(f"🔄 {len(uncached_ids)} neue Spiele zu laden (Cache: {len(results)})")
        
        # Kleinere Batches für besseres Rate Limiting
        batch_size = 10  # Reduziert von 20 auf 10
        for i in range(0, len(uncached_ids), batch_size):
            batch_ids = uncached_ids[i:i+batch_size]
            
            print(f"   🎯 Batch {i//batch_size + 1}/{(len(uncached_ids)-1)//batch_size + 1}: {len(batch_ids)} Spiele")
            
            batch_results = self._fetch_steam_prices_batch(batch_ids, country_code)
            results.update(batch_results)
            
            # Längere Pause zwischen Batches
            if i + batch_size < len(uncached_ids):
                print("   ⏱️  Batch-Pause...")
                time.sleep(2.0)  # Erhöht von 1.0s auf 2.0s
        
        return results
    
    def _fetch_steam_prices_batch(self, app_ids, country_code):
        """
        Fetcht Steam Preise für eine Batch von App IDs
        VERBESSERTE VERSION mit exponential backoff
        """
        results = {}
        consecutive_429_count = 0
    
        for i, app_id in enumerate(app_ids):
            app_id_str = str(app_id)
            url = f"{self.steam_store_url}/appdetails"
        
            params = {
                'appids': app_id_str,
                'filters': 'price_overview,basic',
                'cc': country_code
            }
        
            # Dynamische Pause basierend auf 429-Fehlern
            if consecutive_429_count > 0:
                # Exponential backoff: 1s, 2s, 4s, 8s, max 16s
                wait_time = min(2 ** consecutive_429_count, 16)
                print(f"⏱️  Warte {wait_time}s wegen Rate Limiting...")
                time.sleep(wait_time)
        
            try:
                response = self.session.get(url, params=params, timeout=10)
            
                if response.status_code == 429:  # Rate Limit
                    consecutive_429_count += 1
                    print(f"⚠️  Rate Limit #{consecutive_429_count} für App {app_id}")
                
                    # Bei wiederholten 429ern längere Pause
                    if consecutive_429_count >= 3:
                        print(f"⏸️  Längere Pause nach {consecutive_429_count} Rate Limits...")
                        time.sleep(30)  # 30 Sekunden Pause
                
                    # Leeren Eintrag für dieses Spiel
                    empty_price_info = {
                        'currency': None,
                        'initial_price': None,
                        'final_price': None,
                        'discount_percent': 0,
                        'is_free': False,
                        'formatted_initial': 'Rate Limit',
                        'formatted_final': 'Rate Limit'
                    }
                    results[app_id_str] = empty_price_info
                    continue
            
                elif response.status_code == 200:
                    # Erfolgreicher Request - Reset 429 Counter
                    consecutive_429_count = 0
                
                    data = response.json()
                    app_data = data.get(app_id_str, {})
                
                    if app_data.get('success', False) and 'data' in app_data:
                        game_data = app_data['data']
                        price_overview = game_data.get('price_overview')
                    
                        price_info = {
                            'currency': None,
                            'initial_price': None,
                            'final_price': None,
                            'discount_percent': 0,
                            'is_free': game_data.get('is_free', False),
                            'formatted_initial': None,
                            'formatted_final': None,
                            'steam_name': game_data.get('name', 'Unbekannt')
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
                    
                        results[app_id_str] = price_info
                    
                        # Cache das Ergebnis
                        cache_key = f"{app_id}_{country_code}"
                        self.steam_price_cache[cache_key] = price_info
                    else:
                        # Spiel nicht gefunden
                        empty_price_info = {
                            'currency': None,
                            'initial_price': None,
                            'final_price': None,
                            'discount_percent': 0,
                            'is_free': False,
                            'formatted_initial': 'Nicht verfügbar',
                            'formatted_final': 'Nicht verfügbar'
                        }
                        results[app_id_str] = empty_price_info
                    
                        cache_key = f"{app_id}_{country_code}"
                        self.steam_price_cache[cache_key] = empty_price_info
                else:
                    # Anderer HTTP-Fehler
                    print(f"⚠️  Steam Store API Error {response.status_code} für App {app_id}")
                    empty_price_info = {
                        'currency': None,
                        'initial_price': None,
                        'final_price': None,
                        'discount_percent': 0,
                        'is_free': False,
                        'formatted_initial': 'API Fehler',
                        'formatted_final': 'API Fehler'
                    }
                    results[app_id_str] = empty_price_info
                
            except requests.RequestException as e:
                print(f"⚠️  Steam Store Request Error für App {app_id}: {e}")
                empty_price_info = {
                    'currency': None,
                    'initial_price': None,
                    'final_price': None,
                    'discount_percent': 0,
                    'is_free': False,
                    'formatted_initial': 'Request Fehler',
                    'formatted_final': 'Request Fehler'
                }
                results[app_id_str] = empty_price_info
        
            # Basis-Pause zwischen Requests (reduziert von 0.2s auf 0.5s)
            if i < len(app_ids) - 1:  # Nicht nach dem letzten Request
                time.sleep(0.5)
        
            # Fortschrittsanzeige bei vielen Requests
            if len(app_ids) > 50 and (i + 1) % 25 == 0:
                print(f"   📊 Fortschritt: {i + 1}/{len(app_ids)} ({((i + 1)/len(app_ids))*100:.1f}%)")
    
        return results
    
    def enrich_items_with_steam_prices(self, items, country_code="DE", show_progress=True):
        """
        Reichert Items mit Steam-Preisinformationen an
        
        Args:
            items (list): Liste der Wishlist-Items
            country_code (str): Ländercode für Preise
            show_progress (bool): Zeige Fortschritt an
            
        Returns:
            list: Items mit Steam-Preisinformationen
        """
        if not items:
            return items
        
        # Sammle alle App IDs und konvertiere zu Strings - MOVED UP
        app_ids = [str(item.get('appid')) for item in items if item.get('appid')]
        
        if show_progress:
            print(f"💰 Rufe Steam-Preise für {len(items)} Spiele ab (Land: {country_code})...")
            print(f"⏱️  Geschätzte Zeit: {(len(app_ids) * 0.3) / 60:.1f} Minuten (einzelne Requests)")
        
        # Hole Preisinformationen (in Batches)
        price_data = self.get_steam_price_info(app_ids, country_code)
        
        # Reichere Items an
        enriched_items = []
        found_prices = 0
        
        for item in items:
            app_id = str(item.get('appid', ''))  # Als String für Lookup
            price_info = price_data.get(app_id, {})
            
            enriched_item = {
                **item,
                'steam_price': price_info
            }
            
            if price_info.get('initial_price') is not None:
                found_prices += 1
            
            enriched_items.append(enriched_item)
        
        if show_progress:
            print(f"✅ Steam-Preise geladen: {found_prices}/{len(items)} Spiele ({(found_prices/len(items))*100:.1f}%)")
        
        return enriched_items

    def enrich_items_with_cheapshark(self, items, show_progress=True):
        """
        Reichert Wishlist-Items mit CheapShark-Daten an (aus lokaler DB)
        
        Args:
            items (list): Liste der Wishlist-Items
            show_progress (bool): Zeige Fortschritt an
            
        Returns:
            list: Angereicherte Items mit CheapShark-Daten
        """
        if not items:
            return items
        
        enriched_items = []
        total_items = len(items)
        found_count = 0
        
        if show_progress:
            print(f"🔍 Suche CheapShark-Daten in lokaler Datenbank für {total_items} Spiele...")
        
        for i, item in enumerate(items, 1):
            steam_app_id = item.get('appid')
            
            # CheapShark-Daten aus lokaler Datenbank abrufen
            cheapshark_data = self.get_cheapshark_id_from_db(steam_app_id)
            
            if cheapshark_data['found']:
                found_count += 1
                
                # Zusätzliche Details abrufen falls verfügbar
                if cheapshark_data['game_id']:
                    details = self.get_cheapshark_game_details(cheapshark_data['game_id'])
                    if details:
                        cheapshark_data.update(details)
            
            # Item mit CheapShark-Daten anreichern
            enriched_item = {
                **item,
                'cheapshark': cheapshark_data
            }
            
            enriched_items.append(enriched_item)
        
        if show_progress:
            print(f"✅ CheapShark-Mapping abgeschlossen:")
            print(f"   🎯 Gefunden: {found_count}/{total_items} ({(found_count/total_items)*100:.1f}%)")
        
        return enriched_items

    def get_cheapshark_game_details(self, cheapshark_game_id):
        """
        Ruft detaillierte Informationen zu einem CheapShark Game ab
        
        Args:
            cheapshark_game_id (str): CheapShark Game ID
            
        Returns:
            dict: Game Details oder None
        """
        if not cheapshark_game_id:
            return None
            
        url = f"{self.cheapshark_base_url}/games"
        params = {
            'id': cheapshark_game_id
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'info' in data:
                    game_info = data['info']
                    return {
                        'cheapest_price_ever': data.get('cheapestPriceEver', {}).get('price'),
                        'cheapest_store': data.get('cheapestPriceEver', {}).get('store'),
                        'deals_count': len(data.get('deals', []))
                    }
                return None
            else:
                return None
                
        except requests.RequestException:
            return None

    def get_player_info(self, steam_id):
        """
        Ruft Spielerinformationen ab (Username, etc.)
        
        Args:
            steam_id (str): 64-Bit Steam ID des Benutzers
            
        Returns:
            dict: Spielerinformationen oder None bei Fehler
        """
        url = f"{self.base_url}/ISteamUser/GetPlayerSummaries/v0002/"
        
        params = {
            'key': self.api_key,
            'steamids': steam_id,
            'format': 'json'
        }
        
        try:
            print(f"👤 Rufe Spielerinformationen ab...")
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if 'response' in data and 'players' in data['response']:
                    players = data['response']['players']
                    if players and len(players) > 0:
                        player = players[0]
                        player_info = {
                            'steam_id': player.get('steamid'),
                            'username': player.get('personaname'),
                            'real_name': player.get('realname'),
                            'profile_url': player.get('profileurl'),
                            'avatar_url': player.get('avatarfull'),
                            'country_code': player.get('loccountrycode'),
                            'profile_state': player.get('profilestate'),  # 1 = public
                            'last_logoff': player.get('lastlogoff'),
                            'account_created': player.get('timecreated')
                        }
                        print(f"✅ Spieler gefunden: {player_info['username']}")
                        return player_info
                    else:
                        print(f"⚠️  Keine Spielerdaten gefunden")
                        return None
                else:
                    print(f"⚠️  Unerwartete Response-Struktur: {data}")
                    return None
            else:
                print(f"❌ HTTP Error {response.status_code}: {response.text}")
                return None
                
        except requests.RequestException as e:
            print(f"❌ Request Error: {e}")
            return None

    def get_wishlist_item_count(self, steam_id):
        """
        Ruft die Anzahl der Items in der Wishlist ab
        
        Args:
            steam_id (str): 64-Bit Steam ID des Benutzers
            
        Returns:
            int: Anzahl der Items oder None bei Fehler
        """
        url = f"{self.base_url}/IWishlistService/GetWishlistItemCount/v1/"
        
        params = {
            'key': self.api_key,
            'steamid': steam_id,
            'format': 'json'
        }
        
        try:
            print(f"📊 Rufe Wishlist-Anzahl ab...")
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if 'response' in data:
                    count = data['response'].get('count', 0)
                    print(f"✅ Anzahl Items in Wishlist: {count}")
                    return count
                else:
                    print(f"⚠️  Unerwartete Response-Struktur: {data}")
                    return None
            else:
                print(f"❌ HTTP Error {response.status_code}: {response.text}")
                return None
                
        except requests.RequestException as e:
            print(f"❌ Request Error: {e}")
            return None
    
    def get_wishlist_sorted_filtered(self, steam_id, page_size=100, start_index=0):
        """
        Ruft Wishlist-Items paginiert ab (empfohlene Methode) - VERBESSERT
        
        Args:
            steam_id (str): Steam ID des Benutzers
            page_size (int): Anzahl Items pro Seite (max 100)
            start_index (int): Start-Index für Pagination
            
        Returns:
            dict: Wishlist-Daten oder None bei Fehler
        """
        url = f"{self.base_url}/IWishlistService/GetWishlistSortedFiltered/v1/"
        
        params = {
            'key': self.api_key,  # API Key hinzugefügt
            'steamid': steam_id,
            'sort_order': 'date_added',  # oder 'name', 'price', 'user_order'
            'start_index': start_index,
            'page_size': page_size,
            'format': 'json'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ HTTP Error {response.status_code}: {response.text[:200]}...")
                return None
                
        except requests.RequestException as e:
            print(f"❌ Request Error: {e}")
            return None
    
    def get_complete_wishlist(self, steam_id, include_cheapshark=True, include_steam_prices=True, country_code="DE"):
        """
        Ruft die komplette Wishlist ab (alle Items)
        
        Args:
            steam_id (str): Steam ID des Benutzers
            include_cheapshark (bool): CheapShark-Daten hinzufügen
            include_steam_prices (bool): Steam-Preisinformationen hinzufügen
            country_code (str): Ländercode für Preise
            
        Returns:
            dict: Vollständige Wishlist-Daten
        """
        # Schritt 0: CheapShark-Katalog prüfen/aktualisieren
        if include_cheapshark:
            print("🔍 Prüfe CheapShark-Katalog...")
            if not self.download_cheapshark_catalog():
                print("⚠️  CheapShark-Katalog konnte nicht geladen werden. Verwende direkte API-Calls.")
                include_cheapshark = False
        
        # Schritt 1: Spielerinformationen abrufen
        player_info = self.get_player_info(steam_id)
        
        # Schritt 2: Anzahl der Items abrufen
        total_count = self.get_wishlist_item_count(steam_id)
        
        if total_count is None:
            print("❌ Konnte Wishlist-Anzahl nicht abrufen")
            return None
        
        if total_count == 0:
            print("📭 Wishlist ist leer")
            return {
                'metadata': {
                    'steam_id': steam_id,
                    'username': player_info.get('username') if player_info else 'Unknown',
                    'player_info': player_info,
                    'retrieved_at': datetime.now().isoformat(),
                    'method': 'complete_wishlist',
                    'cheapshark_enabled': include_cheapshark,
                    'steam_prices_enabled': include_steam_prices,
                    'country_code': country_code
                },
                'total_count': 0,
                'items': []
            }
        
        # Schritt 3: Alle Items abrufen (in Blöcken von 100)
        print(f"📥 Rufe {total_count} Wishlist-Items ab...")
        
        all_items = []
        page_size = 100
        start_index = 0
        
        while start_index < total_count:
            print(f"   📄 Seite {start_index//page_size + 1}: Items {start_index+1}-{min(start_index+page_size, total_count)}")
            
            # GetWishlistSortedFiltered für bessere Datenqualität verwenden
            page_data = self.get_wishlist_sorted_filtered(
                steam_id, 
                page_size=page_size, 
                start_index=start_index
            )
            
            if not page_data or 'response' not in page_data:
                print(f"⚠️  Fehler beim Abrufen von Seite {start_index//page_size + 1}")
                break
            
            response = page_data['response']
            page_items = response.get('items', [])
            
            if not page_items:
                print("   📭 Keine weiteren Items gefunden")
                break
            
            all_items.extend(page_items)
            print(f"   ✅ {len(page_items)} Items hinzugefügt")
            
            start_index += page_size
            
            # Rate-Limiting: Kurze Pause zwischen Requests
            if start_index < total_count:
                time.sleep(0.5)
        
        # Schritt 4: Fallback auf einfache GetWishlist falls nötig
        if not all_items:
            print("🔄 Fallback: Verwende GetWishlist...")
            fallback_data = self.get_wishlist_simple(steam_id)
            if fallback_data:
                all_items = fallback_data
        
        # Schritt 5: Steam-Preisinformationen hinzufügen (enthält Spielnamen)
        if include_steam_prices and all_items:
            all_items = self.enrich_items_with_steam_prices(all_items, country_code)
        
        # Schritt 6: CheapShark-Daten hinzufügen (optional)
        if include_cheapshark and all_items:
            all_items = self.enrich_items_with_cheapshark(all_items)
        
        # Schritt 7: Ergebnis zusammenstellen
        result = {
            'metadata': {
                'steam_id': steam_id,
                'username': player_info.get('username') if player_info else 'Unknown',
                'player_info': player_info,
                'retrieved_at': datetime.now().isoformat(),
                'method': 'paginated' if all_items else 'failed',
                'pages_retrieved': (len(all_items) // page_size) + 1,
                'cheapshark_enabled': include_cheapshark,
                'steam_prices_enabled': include_steam_prices,
                'country_code': country_code
            },
            'total_count': total_count,
            'retrieved_count': len(all_items),
            'items': all_items
        }
        
        print(f"✅ Vollständige Wishlist abgerufen: {len(all_items)}/{total_count} Items")
        return result
    
    def get_wishlist_simple(self, steam_id):
        """
        Fallback: Einfache Wishlist-Abfrage
        
        Args:
            steam_id (str): Steam ID des Benutzers
            
        Returns:
            list: Liste der Wishlist-Items
        """
        url = f"{self.base_url}/IWishlistService/GetWishlist/v1/"
        
        params = {
            'key': self.api_key,
            'steamid': steam_id,
            'format': 'json'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if 'response' in data:
                    # Struktur kann variieren
                    response_data = data['response']
                    if 'items' in response_data:
                        return response_data['items']
                    elif isinstance(response_data, list):
                        return response_data
                    else:
                        # Fallback: gesamte Response zurückgeben
                        return [response_data]
                return []
            else:
                print(f"❌ Simple Wishlist Error {response.status_code}: {response.text}")
                return []
                
        except requests.RequestException as e:
            print(f"❌ Simple Wishlist Request Error: {e}")
            return []
    
    def save_wishlist_to_file(self, wishlist_data, filename=None):
        """
        Speichert Wishlist-Daten als JSON-Datei im Output-Unterordner
        
        Args:
            wishlist_data (dict): Wishlist-Daten
            filename (str): Dateiname (optional)
            
        Returns:
            str: Pfad zur gespeicherten Datei
        """
        # Output-Ordner erstellen falls nicht vorhanden
        output_dir = Path("Output")
        output_dir.mkdir(exist_ok=True)
        
        if not filename:
            steam_id = wishlist_data['metadata']['steam_id']
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"steam_wishlist_{steam_id}_{timestamp}.json"
        
        # Vollständigen Pfad erstellen
        filepath = output_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(wishlist_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Wishlist gespeichert: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Fehler beim Speichern: {e}")
            return None
    
    def print_wishlist_summary(self, wishlist_data):
        """
        Gibt eine Zusammenfassung der Wishlist aus
        
        Args:
            wishlist_data (dict): Wishlist-Daten
        """
        if not wishlist_data:
            print("❌ Keine Wishlist-Daten verfügbar")
            return
        
        total = wishlist_data.get('total_count', 0)
        retrieved = wishlist_data.get('retrieved_count', 0)
        items = wishlist_data.get('items', [])
        
        print(f"\n📊 WISHLIST ZUSAMMENFASSUNG")
        print(f"{'='*50}")
        print(f"Steam ID: {wishlist_data['metadata']['steam_id']}")
        print(f"Username: {wishlist_data['metadata']['username']}")
        print(f"Gesamtanzahl: {total}")
        print(f"Abgerufen: {retrieved}")
        print(f"Zeitpunkt: {wishlist_data['metadata']['retrieved_at']}")
        
        if items and len(items) > 0:
            print(f"\n📋 ERSTE 5 SPIELE:")
            for i, item in enumerate(items[:5], 1):
                app_id = item.get('appid', 'N/A')
                
                # Spielname aus Steam-Preisinformationen oder fallback
                name = 'Unbekannt'
                if item.get('steam_price', {}).get('steam_name'):
                    name = item['steam_price']['steam_name']
                elif item.get('name'):
                    name = item['name']
                
                priority = item.get('priority', 'N/A')
                
                # Preisinformationen anzeigen
                price_info = ""
                if item.get('steam_price'):
                    steam_price = item['steam_price']
                    if steam_price.get('final_price') is not None:
                        if steam_price.get('discount_percent', 0) > 0:
                            price_info = f" - {steam_price['formatted_final']} (-{steam_price['discount_percent']}%)"
                        else:
                            price_info = f" - {steam_price['formatted_final']}"
                
                print(f"{i:2d}. {name} (ID: {app_id}){price_info}")
                
                # CheapShark-Info falls verfügbar
                if item.get('cheapshark', {}).get('found'):
                    cheapest = item['cheapshark'].get('cheapest_price_ever')
                    if cheapest:
                        print(f"     💰 Bester Preis jemals: ${cheapest}")
        
        print(f"\n{'='*50}")

def update_cheapshark_catalog(api_key):
    """
    Hilfsfunktion zum manuellen Update des CheapShark-Katalogs
    
    Args:
        api_key (str): Steam Web API Key
        
    Returns:
        bool: True wenn erfolgreich
    """
    manager = SteamWishlistManager(api_key)
    return manager.download_cheapshark_catalog(force_update=True)

def get_user_wishlist(api_key, steam_id, include_cheapshark=True, include_steam_prices=True, country_code="DE"):
    """
    Hauptmethode für die Auswertung - ruft Wishlist ohne Nutzerinteraktion ab
    
    Args:
        api_key (str): Steam Web API Key
        steam_id (str): 64-Bit Steam ID des Benutzers
        include_cheapshark (bool): CheapShark-Daten hinzufügen
        include_steam_prices (bool): Steam-Preisinformationen hinzufügen
        country_code (str): Ländercode für Preise (DE, US, UK, etc.)
        
    Returns:
        dict: Wishlist-Daten oder None bei Fehler
    """
    manager = SteamWishlistManager(api_key)
    return manager.get_complete_wishlist(steam_id, include_cheapshark, include_steam_prices, country_code)

def main():
    """Hauptfunktion für interaktive Nutzung - MIT .env SUPPORT"""
    print("🎮 Steam Wishlist Manager")
    print("=" * 40)
    
    # API Key aus .env laden
    api_key = load_api_key_from_env()
    
    if not api_key:
        print("⚠️  Kein API Key in .env gefunden")
        
        # Template erstellen falls .env nicht existiert
        if create_env_template():
            return
        
        # Fallback: Manuelle Eingabe
        print("💡 Du kannst deinen API Key in die .env-Datei eintragen oder hier eingeben:")
        api_key = input("Steam API Key eingeben: ").strip()
    else:
        print("✅ API Key aus .env geladen")
        # Optional: Zeige ersten/letzten Zeichen zur Bestätigung
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
        print(f"🔑 Key: {masked_key}")
    
    if not api_key:
        print("❌ Kein API Key angegeben")
        return
    
    # Option: CheapShark-Katalog aktualisieren
    update_catalog = input("📦 CheapShark-Katalog aktualisieren? (j/n): ").strip().lower()
    if update_catalog in ['j', 'ja', 'y', 'yes']:
        print("📥 Aktualisiere CheapShark-Katalog...")
        if update_cheapshark_catalog(api_key):
            print("✅ CheapShark-Katalog erfolgreich aktualisiert")
        else:
            print("❌ CheapShark-Katalog Update fehlgeschlagen")
        print()
    
    # Steam ID eingeben
    steam_id = input("Steam ID (17 Ziffern) eingeben: ").strip()
    
    if not steam_id or len(steam_id) != 17 or not steam_id.isdigit():
        print("❌ Ungültige Steam ID")
        return
    
    # Wishlist abrufen über die Auswertungs-Methode
    print(f"\n🚀 Starte Wishlist-Abfrage für Steam ID: {steam_id}")
    
    # Frage nach Steam-Preisen
    steam_prices_choice = input("💰 Steam-Preise hinzufügen? (j/n): ").strip().lower()
    include_steam_prices = steam_prices_choice in ['j', 'ja', 'y', 'yes']
    
    country_code = "DE"
    if include_steam_prices:
        country_input = input("🌍 Ländercode für Preise (DE/US/UK/etc., Enter für DE): ").strip().upper()
        if country_input:
            country_code = country_input
    
    # Frage nach CheapShark-Integration
    cheapshark_choice = input("🔍 CheapShark-Daten hinzufügen? (j/n): ").strip().lower()
    include_cheapshark = cheapshark_choice in ['j', 'ja', 'y', 'yes']
    
    wishlist_data = get_user_wishlist(api_key, steam_id, include_cheapshark, include_steam_prices, country_code)
    
    if wishlist_data:
        # Manager für Hilfsfunktionen erstellen
        manager = SteamWishlistManager(api_key)
        
        # Zusammenfassung anzeigen
        manager.print_wishlist_summary(wishlist_data)
        
        # Fragen ob speichern
        save_choice = input("\n💾 Möchten Sie die Wishlist als JSON speichern? (j/n): ").strip().lower()
        
        if save_choice in ['j', 'ja', 'y', 'yes']:
            filename = manager.save_wishlist_to_file(wishlist_data)
            if filename:
                print(f"✅ Gespeichert als: {filename}")
        
        # JSON ausgeben (optional)
        print_json = input("📄 JSON-Daten in Konsole ausgeben? (j/n): ").strip().lower()
        
        if print_json in ['j', 'ja', 'y', 'yes']:
            print(f"\n📋 JSON-DATEN:")
            print(json.dumps(wishlist_data, indent=2, ensure_ascii=False))
        
    else:
        print("❌ Wishlist konnte nicht abgerufen werden")
        print("\nMögliche Ursachen:")
        print("- API Key ist ungültig")
        print("- Steam ID ist ungültig")
        print("- Wishlist ist privat")
        print("- Steam API ist temporär nicht verfügbar")

if __name__ == "__main__":
    main()