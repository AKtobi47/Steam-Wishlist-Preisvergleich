"""
Steam Wishlist Manager - Offizielle Steam Wishlist API
Verwendet die saubere IWishlistService/GetWishlist API
Basiert auf https://steamapi.xpaw.me/#IWishlistService/GetWishlist
FINALE VERSION für das integrierte System
"""

import requests
import time
import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import logging

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

class SteamWishlistManager:
    """
    Steam Wishlist Manager mit offizieller Steam Wishlist API
    Verwendet IWishlistService/GetWishlist für präzise Ergebnisse
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.steam_base_url = "https://api.steampowered.com"
        
        # Session für Steam API Requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SteamPriceTracker/1.0'
        })
        
        # Rate Limiting
        self.last_steam_api_request = 0
        self.steam_api_rate_limit = 1.0  # 1 Sekunde zwischen Requests
        
        logger.info("✅ Steam Wishlist Manager (offizielle API) initialisiert")
    
    def _wait_for_steam_api_rate_limit(self):
        """Wartet für Steam API Rate Limiting"""
        time_since_last = time.time() - self.last_steam_api_request
        if time_since_last < self.steam_api_rate_limit:
            wait_time = self.steam_api_rate_limit - time_since_last
            logger.debug(f"⏳ Rate Limiting: warte {wait_time:.2f}s für Steam API")
            time.sleep(wait_time)
        self.last_steam_api_request = time.time()
    
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
            
            self._wait_for_steam_api_rate_limit()
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                players = data.get('response', {}).get('players', [])
                
                if players and len(players) > 0:
                    player = players[0]
                    player_info = {
                        'steam_id': player.get('steamid'),
                        'username': player.get('personaname'),
                        'profile_url': player.get('profileurl'),
                        'avatar_url': player.get('avatarfull'),
                        'country_code': player.get('loccountrycode'),
                        'profile_state': player.get('profilestate'),
                        'community_visibility': player.get('communityvisibilitystate')
                    }
                    logger.info(f"✅ Spieler gefunden: {player_info['username']}")
                    return player_info
                else:
                    logger.warning("⚠️ Keine Spielerdaten gefunden")
                    return None
            else:
                logger.error(f"❌ HTTP Error {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"❌ Request Error: {e}")
            return None
    
    def get_wishlist_official(self, steam_id: str) -> List[Dict]:
        """
        Offizielle Steam Wishlist API - Die sauberste Methode
        API: https://api.steampowered.com/IWishlistService/GetWishlist/v1/
        Dokumentation: https://steamapi.xpaw.me/#IWishlistService/GetWishlist
        """
        logger.info("🎯 Verwende offizielle Steam Wishlist API...")
        
        url = f"{self.steam_base_url}/IWishlistService/GetWishlist/v1/"
        
        params = {
            'key': self.api_key,
            'steamid': steam_id,
            'format': 'json'
        }
        
        try:
            self._wait_for_steam_api_rate_limit()
            response = self.session.get(url, params=params, timeout=30)
            
            logger.info(f"📡 Wishlist API Response: {response.status_code}")
            logger.info(f"📏 Response Size: {len(response.content)} bytes")
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"📄 Response Keys: {list(data.keys())}")
                
                # Prüfe Response-Struktur
                if 'response' in data:
                    response_data = data['response']
                    logger.debug(f"📄 Response Data Keys: {list(response_data.keys())}")
                    
                    # Die Wishlist sollte unter 'items' stehen
                    if 'items' in response_data:
                        items_data = response_data['items']
                        logger.info(f"📋 Anzahl Wishlist Items: {len(items_data)}")
                        
                        items = []
                        for item in items_data:
                            # Extrahiere relevante Daten
                            app_id = item.get('appid')
                            name = item.get('name', f'Steam_App_{app_id}')
                            priority = item.get('priority', 0)
                            date_added = item.get('date_added')
                            
                            items.append({
                                'appid': app_id,
                                'name': name,
                                'priority': priority,
                                'date_added': date_added
                            })
                        
                        logger.info(f"✅ {len(items)} Items via offizielle Wishlist API gefunden")
                        return items
                    
                    else:
                        logger.warning("⚠️ Keine 'items' in Response gefunden")
                        logger.debug(f"📄 Verfügbare Keys: {list(response_data.keys())}")
                        
                        # Prüfe alternative Strukturen
                        if 'wishlist' in response_data:
                            wishlist_data = response_data['wishlist']
                            logger.info(f"📋 Alternative Struktur: wishlist mit {len(wishlist_data)} Items")
                            
                            items = []
                            for item in wishlist_data:
                                items.append({
                                    'appid': item.get('appid'),
                                    'name': item.get('name', f'Steam_App_{item.get("appid")}'),
                                    'priority': item.get('priority', 0)
                                })
                            
                            return items
                
                else:
                    logger.warning("⚠️ Keine 'response' in JSON gefunden")
                    logger.debug(f"📄 Verfügbare Top-Level Keys: {list(data.keys())}")
                    
                    # Direkter Zugriff auf Items falls andere Struktur
                    if isinstance(data, list):
                        logger.info(f"📋 Direkte Liste mit {len(data)} Items")
                        
                        items = []
                        for item in data:
                            items.append({
                                'appid': item.get('appid'),
                                'name': item.get('name', f'Steam_App_{item.get("appid")}'),
                                'priority': item.get('priority', 0)
                            })
                        
                        return items
                    
                    elif 'items' in data:
                        items_data = data['items']
                        logger.info(f"📋 Direkte Items mit {len(items_data)} Einträgen")
                        
                        items = []
                        for item in items_data:
                            items.append({
                                'appid': item.get('appid'),
                                'name': item.get('name', f'Steam_App_{item.get("appid")}'),
                                'priority': item.get('priority', 0)
                            })
                        
                        return items
                
                logger.warning("⚠️ Konnte Wishlist-Items in Response nicht finden")
                logger.debug(f"📄 Raw Response: {response.text[:500]}...")
                return []
                
            elif response.status_code == 403:
                logger.error("❌ HTTP 403: Zugriff verweigert - Wishlist möglicherweise privat")
                return []
                
            elif response.status_code == 401:
                logger.error("❌ HTTP 401: Unauthorized - API Key ungültig")
                return []
                
            else:
                logger.error(f"❌ HTTP {response.status_code}")
                logger.debug(f"📄 Response Content: {response.text[:200]}...")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON Parse Error: {e}")
            logger.debug(f"📄 Raw Response: {response.text[:200]}...")
            return []
            
        except requests.RequestException as e:
            logger.error(f"❌ Request Error: {e}")
            return []
    
    def get_simple_wishlist(self, steam_id: str) -> List[Dict]:
        """
        Hauptmethode: Verwendet offizielle Steam Wishlist API
        
        Args:
            steam_id: Steam User ID
            
        Returns:
            Liste von Wishlist-Items mit appid und name
        """
        logger.info(f"🎯 Starte offiziellen Wishlist-Abruf für Steam ID: {steam_id}")
        
        # Spielerinformationen abrufen für Validierung
        player_info = self.get_player_info(steam_id)
        if not player_info:
            logger.error("❌ Konnte Spielerinformationen nicht abrufen - ungültige Steam ID?")
            return []
        
        # Prüfe Profil-Sichtbarkeit
        visibility = player_info.get('community_visibility', 1)
        logger.info(f"👀 Profil-Sichtbarkeit: {visibility} (3=öffentlich)")
        
        if visibility != 3:
            logger.warning("⚠️ Profil ist nicht öffentlich - Wishlist möglicherweise nicht zugänglich")
        
        # Verwende offizielle Wishlist API
        wishlist_items = self.get_wishlist_official(steam_id)
        
        if wishlist_items:
            logger.info(f"🎉 Gesamt: {len(wishlist_items)} Wishlist-Items via offizielle API abgerufen")
            return wishlist_items
        else:
            logger.error("❌ Offizielle Wishlist API fehlgeschlagen")
            logger.info("💡 Lösungsvorschläge:")
            logger.info("   1. Stelle sicher, dass das Profil öffentlich ist")
            logger.info("   2. Stelle sicher, dass die Wishlist öffentlich sichtbar ist")
            logger.info("   3. Prüfe die Steam ID (sollte 17 Ziffern haben)")
            logger.info("   4. Prüfe den API Key auf https://steamcommunity.com/dev/apikey")
            
            return []
    
    def get_app_details(self, app_id: str) -> Optional[Dict]:
        """
        Holt grundlegende App-Details von Steam Store API
        
        Args:
            app_id: Steam App ID
            
        Returns:
            Dict mit App-Details oder None
        """
        url = "https://store.steampowered.com/api/appdetails"
        params = {
            'appids': app_id,
            'filters': 'basic',
            'cc': 'DE'
        }
        
        try:
            # Separates Rate Limiting für Store API
            time.sleep(1.0)
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                app_data = data.get(app_id, {})
                
                if app_data.get('success') and 'data' in app_data:
                    game_data = app_data['data']
                    
                    return {
                        'app_id': app_id,
                        'name': game_data.get('name', ''),
                        'type': game_data.get('type', 'game'),
                        'is_free': game_data.get('is_free', False),
                        'developer': ', '.join(game_data.get('developers', [])),
                        'publisher': ', '.join(game_data.get('publishers', []))
                    }
            
            return None
            
        except requests.RequestException:
            return None
    
    def validate_steam_id(self, steam_id: str) -> bool:
        """Validiert eine Steam ID"""
        if not steam_id or len(steam_id) != 17 or not steam_id.isdigit():
            return False
        
        # Zusätzliche Validierung durch Player Info Abruf
        player_info = self.get_player_info(steam_id)
        return player_info is not None
    
    def search_steam_app(self, app_name: str) -> List[Dict]:
        """
        Sucht nach Steam Apps (vereinfacht)
        Nutzt Steam Store Search API
        
        Args:
            app_name: Name der App zum Suchen
            
        Returns:
            Liste von gefundenen Apps
        """
        url = "https://store.steampowered.com/api/storesearch/"
        params = {
            'term': app_name,
            'l': 'german',
            'cc': 'DE'
        }
        
        try:
            time.sleep(1.0)  # Rate Limiting
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                
                # Vereinfache Ergebnisse
                results = []
                for item in items[:10]:  # Limitiere auf 10 Ergebnisse
                    results.append({
                        'appid': item.get('id'),
                        'name': item.get('name'),
                        'type': item.get('type')
                    })
                
                return results
            
            return []
            
        except requests.RequestException as e:
            logger.error(f"❌ Steam App Suche Fehler: {e}")
            return []
    
    def export_wishlist_simple(self, steam_id: str, output_file: str = None) -> str:
        """
        Exportiert Wishlist als einfache JSON-Datei
        
        Args:
            steam_id: Steam User ID
            output_file: Ausgabedatei (optional)
            
        Returns:
            Pfad zur erstellten Datei
        """
        wishlist_items = self.get_simple_wishlist(steam_id)
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"steam_wishlist_{steam_id}_{timestamp}.json"
        
        output_path = Path("exports") / output_file
        output_path.parent.mkdir(exist_ok=True)
        
        # Export-Daten zusammenstellen
        export_data = {
            'steam_id': steam_id,
            'exported_at': datetime.now().isoformat(),
            'total_items': len(wishlist_items),
            'items': wishlist_items
        }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📄 Wishlist exportiert: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ Export-Fehler: {e}")
            return None