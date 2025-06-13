"""
Steam Wishlist Manager - Vereinfacht für Preis-Tracking
Nur Wishlist-Abruf ohne CheapShark-Mapping Komplexität
Basiert auf dem funktionierenden steam_wishlist_manager.py
"""

import requests
import time
import os
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
    Vereinfachter Steam Wishlist Manager nur für Wishlist-Abruf
    Ohne CheapShark-Mapping Komplexität
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
        
        logger.info("✅ Steam Wishlist Manager (vereinfacht) initialisiert")
    
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
                        'profile_state': player.get('profilestate')
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
    
    def get_wishlist_item_count(self, steam_id: str) -> Optional[int]:
        """Ruft die Anzahl der Items in der Wishlist ab"""
        url = f"{self.steam_base_url}/IWishlistService/GetWishlistItemCount/v1/"
        
        params = {
            'key': self.api_key,
            'steamid': steam_id,
            'format': 'json'
        }
        
        try:
            logger.info("📊 Rufe Wishlist-Anzahl ab...")
            
            self._wait_for_steam_api_rate_limit()
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if 'response' in data:
                    count = data['response'].get('count', 0)
                    logger.info(f"✅ Anzahl Items in Wishlist: {count}")
                    return count
                else:
                    logger.warning(f"⚠️ Unerwartete Response-Struktur")
                    return None
            else:
                logger.error(f"❌ HTTP Error {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"❌ Request Error: {e}")
            return None
    
    def get_wishlist_page(self, steam_id: str, page_size: int = 100, start_index: int = 0) -> Optional[List[Dict]]:
        """Ruft eine Seite der Wishlist ab"""
        url = f"{self.steam_base_url}/IWishlistService/GetWishlistSortedFiltered/v1/"
        
        params = {
            'key': self.api_key,
            'steamid': steam_id,
            'start_index': start_index,
            'page_size': page_size,
            'format': 'json'
        }
        
        try:
            self._wait_for_steam_api_rate_limit()
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                response_data = data.get('response', {})
                items = response_data.get('items', [])
                return items
            else:
                logger.error(f"❌ HTTP Error {response.status_code} bei Seite {start_index//page_size + 1}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"❌ Request Error bei Seite {start_index//page_size + 1}: {e}")
            return None
    
    def get_simple_wishlist(self, steam_id: str) -> List[Dict]:
        """
        Ruft die komplette Wishlist ab (vereinfacht)
        
        Args:
            steam_id: Steam User ID
            
        Returns:
            Liste von Wishlist-Items mit appid und name
        """
        logger.info(f"🎯 Starte vereinfachten Wishlist-Abruf für Steam ID: {steam_id}")
        
        # Spielerinformationen abrufen (optional)
        player_info = self.get_player_info(steam_id)
        if not player_info:
            logger.warning("⚠️ Konnte Spielerinformationen nicht abrufen - versuche trotzdem Wishlist")
        
        # Anzahl der Items abrufen
        total_count = self.get_wishlist_item_count(steam_id)
        
        if total_count is None:
            logger.error("❌ Konnte Wishlist-Anzahl nicht abrufen")
            return []
        
        if total_count == 0:
            logger.warning("📭 Wishlist ist leer")
            return []
        
        logger.info(f"📊 Wishlist-Anzahl: {total_count} Items")
        
        # Alle Items in Blöcken abrufen
        all_items = []
        page_size = 100
        start_index = 0
        
        while start_index < total_count:
            logger.info(f"📄 Seite {start_index//page_size + 1}: Items {start_index+1}-{min(start_index+page_size, total_count)}")
            
            page_items = self.get_wishlist_page(steam_id, page_size, start_index)
            
            if not page_items:
                logger.warning(f"⚠️ Keine Items auf Seite {start_index//page_size + 1} erhalten")
                break
            
            # Vereinfache Items (nur appid und name extrahieren)
            simplified_items = []
            for item in page_items:
                simplified_items.append({
                    'appid': item.get('appid'),
                    'name': item.get('name', f'App_{item.get("appid")}'),
                    'priority': item.get('priority', 0)
                })
            
            all_items.extend(simplified_items)
            logger.info(f"✅ {len(simplified_items)} Items hinzugefügt (Gesamt: {len(all_items)})")
            
            start_index += page_size
            
            # Kurze Pause zwischen Seiten
            if start_index < total_count:
                time.sleep(0.5)
        
        logger.info(f"🎉 Gesamt: {len(all_items)} Wishlist-Items abgerufen")
        return all_items
    
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
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📄 Wishlist exportiert: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ Export-Fehler: {e}")
            return None
