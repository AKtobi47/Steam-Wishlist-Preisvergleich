"""
Steam Wishlist Manager - Enhanced Version für Preis-Tracking
Fokussiert auf Steam API Integration mit optimierten Namen-Abfragen
"""

import requests
import os
import time
from pathlib import Path
from typing import List, Dict, Optional
import logging

try:
    from logging_config import get_steam_wishlist_logger
    logger = get_steam_wishlist_logger()
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

def load_api_key_from_env(env_file: str = ".env") -> Optional[str]:
    """
    Lädt Steam API Key aus .env-Datei
    
    Args:
        env_file: Pfad zur .env-Datei
        
    Returns:
        Steam API Key oder None
    """
    env_path = Path(env_file)
    
    if not env_path.exists():
        logger.warning(f"⚠️ {env_file} nicht gefunden")
        return None
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key.strip() == 'STEAM_API_KEY':
                        api_key = value.strip().strip('"').strip("'")
                        if api_key and api_key != 'your_steam_api_key_here':
                            return api_key
        
        logger.warning("⚠️ STEAM_API_KEY nicht in .env gefunden oder leer")
        return None
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Lesen der .env-Datei: {e}")
        return None

class SteamWishlistManager:
    """
    Enhanced Steam Wishlist Manager
    Fokussiert auf Steam API Integration für Preis-Tracking und Namen-Updates
    """
    
    def __init__(self, api_key: str):
        """
        Initialisiert Steam Wishlist Manager
        
        Args:
            api_key: Steam Web API Key
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SteamPriceTracker/1.1'
        })
        
        # Rate Limiting für Steam API
        self.last_request_time = 0
        self.rate_limit = 1.0  # 1 Sekunde zwischen Requests
    
    def _wait_for_rate_limit(self):
        """Wartet für Steam API Rate Limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit:
            wait_time = self.rate_limit - time_since_last
            logger.debug(f"⏳ Steam API Rate Limit: Warte {wait_time:.2f}s")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def get_steam_id_64(self, steam_id_input: str) -> Optional[str]:
        """
        Konvertiert verschiedene Steam ID Formate zu SteamID64
        
        Args:
            steam_id_input: Steam ID in verschiedenen Formaten
            
        Returns:
            SteamID64 oder None bei Fehler
        """
        # Wenn bereits SteamID64 Format (17 Ziffern)
        if steam_id_input.isdigit() and len(steam_id_input) == 17:
            return steam_id_input
        
        # Wenn Custom URL
        if not steam_id_input.isdigit():
            return self._resolve_vanity_url(steam_id_input)
        
        # Andere Steam ID Formate -> für Einfachheit direkt verwenden
        return steam_id_input
    
    def _resolve_vanity_url(self, vanity_url: str) -> Optional[str]:
        """
        Löst Custom Steam URL zu SteamID64 auf
        
        Args:
            vanity_url: Custom Steam URL
            
        Returns:
            SteamID64 oder None
        """
        self._wait_for_rate_limit()
        
        url = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/"
        params = {
            'key': self.api_key,
            'vanityurl': vanity_url
        }
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('response', {}).get('success') == 1:
                    steam_id = data['response']['steamid']
                    logger.debug(f"✅ Vanity URL {vanity_url} aufgelöst zu {steam_id}")
                    return steam_id
                else:
                    logger.warning(f"⚠️ Vanity URL {vanity_url} konnte nicht aufgelöst werden")
                    return None
            else:
                logger.error(f"❌ Steam API Fehler bei Vanity URL Auflösung: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"❌ Request Fehler bei Vanity URL Auflösung: {e}")
            return None
    
    def get_simple_wishlist(self, steam_id: str) -> List[Dict]:
        """
        Holt vereinfachte Wishlist von Steam
        
        Args:
            steam_id: Steam ID (verschiedene Formate unterstützt)
            
        Returns:
            Liste von Wishlist-Items mit steam_app_id und name
        """
        # Steam ID normalisieren
        steam_id_64 = self.get_steam_id_64(steam_id)
        
        if not steam_id_64:
            logger.error(f"❌ Ungültige Steam ID: {steam_id}")
            return []
        
        self._wait_for_rate_limit()
        
        # Steam Store API für Wishlist (öffentlich, kein API Key nötig)
        url = f"https://store.steampowered.com/wishlist/profiles/{steam_id_64}/wishlistdata/"
        
        try:
            logger.info(f"🔍 Lade Wishlist für Steam ID: {steam_id_64}")
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    if not data:
                        logger.warning("⚠️ Wishlist ist leer oder privat")
                        return []
                    
                    # Wishlist-Items verarbeiten
                    wishlist_items = []
                    
                    for app_id, item_data in data.items():
                        # Steam App ID und Name extrahieren
                        name = item_data.get('name', f'Unknown Game {app_id}')
                        
                        wishlist_items.append({
                            'steam_app_id': app_id,
                            'name': name,
                            'priority': item_data.get('priority', 0),
                            'added': item_data.get('added', 0)
                        })
                    
                    logger.info(f"✅ {len(wishlist_items)} Wishlist-Items gefunden")
                    
                    # Nach Priorität sortieren (niedrigere Zahl = höhere Priorität)
                    wishlist_items.sort(key=lambda x: x['priority'])
                    
                    return wishlist_items
                    
                except ValueError as e:
                    logger.error(f"❌ JSON Parse Fehler: {e}")
                    return []
                    
            elif response.status_code == 403:
                logger.error("❌ Wishlist ist privat - mache sie öffentlich in Steam Privatsphäre-Einstellungen")
                return []
            else:
                logger.error(f"❌ Steam Store API Fehler: {response.status_code}")
                return []
                
        except requests.RequestException as e:
            logger.error(f"❌ Request Fehler beim Laden der Wishlist: {e}")
            return []
    
    def get_app_details(self, app_id: str) -> Optional[Dict]:
        """
        Holt Details für eine Steam App
        
        Args:
            app_id: Steam App ID
            
        Returns:
            App-Details oder None
        """
        self._wait_for_rate_limit()
        
        url = "https://store.steampowered.com/api/appdetails"
        params = {
            'appids': app_id,
            'cc': 'DE',  # Country Code für deutsche Preise
            'l': 'german'  # Language
        }
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if app_id in data and data[app_id].get('success'):
                    app_data = data[app_id]['data']
                    
                    return {
                        'steam_app_id': app_id,
                        'name': app_data.get('name', ''),
                        'type': app_data.get('type', ''),
                        'is_free': app_data.get('is_free', False),
                        'developers': app_data.get('developers', []),
                        'publishers': app_data.get('publishers', []),
                        'genres': [genre['description'] for genre in app_data.get('genres', [])],
                        'categories': [cat['description'] for cat in app_data.get('categories', [])],
                        'release_date': app_data.get('release_date', {}).get('date', ''),
                        'price_info': app_data.get('price_overview', {}),
                        'platforms': app_data.get('platforms', {}),
                        'metacritic': app_data.get('metacritic', {}),
                        'short_description': app_data.get('short_description', '')
                    }
                else:
                    logger.warning(f"⚠️ App {app_id} nicht gefunden oder privat")
                    return None
            else:
                logger.error(f"❌ Steam Store API Fehler für App {app_id}: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"❌ Request Fehler für App {app_id}: {e}")
            return None
    
    def get_app_name_only(self, app_id: str) -> Optional[str]:
        """
        Holt nur den Namen einer Steam App (optimiert)
        
        Args:
            app_id: Steam App ID
            
        Returns:
            App-Name oder None
        """
        app_details = self.get_app_details(app_id)
        
        if app_details and app_details.get('name'):
            return app_details['name'].strip()
        
        return None
    
    def get_multiple_app_names(self, app_ids: List[str], max_batch_size: int = 100) -> Dict[str, str]:
        """
        Holt Namen für mehrere Apps optimiert
        
        Args:
            app_ids: Liste von Steam App IDs
            max_batch_size: Maximale Anzahl Apps pro Batch (für Rate Limiting)
            
        Returns:
            Dict mit app_id -> name Mapping
        """
        if not app_ids:
            return {}
        
        logger.info(f"🔍 Hole Namen für {len(app_ids)} Apps...")
        
        results = {}
        failed_apps = []
        
        # Apps in Batches verarbeiten
        for i in range(0, len(app_ids), max_batch_size):
            batch = app_ids[i:i + max_batch_size]
            batch_num = (i // max_batch_size) + 1
            total_batches = (len(app_ids) + max_batch_size - 1) // max_batch_size
            
            logger.info(f"📦 Batch {batch_num}/{total_batches}: {len(batch)} Apps")
            
            for app_id in batch:
                try:
                    app_name = self.get_app_name_only(app_id)
                    
                    if app_name:
                        results[app_id] = app_name
                        logger.debug(f"✅ {app_id}: {app_name}")
                    else:
                        failed_apps.append(app_id)
                        logger.warning(f"⚠️ Kein Name für App {app_id}")
                        
                except Exception as e:
                    failed_apps.append(app_id)
                    logger.error(f"❌ Fehler bei App {app_id}: {e}")
            
            # Pause zwischen Batches
            if i + max_batch_size < len(app_ids):
                logger.debug("⏳ Pause zwischen Batches...")
                time.sleep(2)
        
        success_rate = len(results) / len(app_ids) * 100 if app_ids else 0
        logger.info(f"✅ Namen-Abruf abgeschlossen: {len(results)}/{len(app_ids)} erfolgreich ({success_rate:.1f}%)")
        
        if failed_apps:
            logger.warning(f"⚠️ {len(failed_apps)} Apps fehlgeschlagen: {failed_apps[:5]}{'...' if len(failed_apps) > 5 else ''}")
        
        return results
    
    def validate_api_key(self) -> bool:
        """
        Validiert Steam API Key
        
        Returns:
            True wenn API Key gültig ist
        """
        self._wait_for_rate_limit()
        
        # Test mit GetPlayerSummaries
        url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
        params = {
            'key': self.api_key,
            'steamids': '76561197960435530'  # Gabe Newell's SteamID für Test
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'response' in data and 'players' in data['response']:
                    logger.info("✅ Steam API Key ist gültig")
                    return True
                else:
                    logger.error("❌ Steam API Key ungültig oder keine Berechtigung")
                    return False
            elif response.status_code == 403:
                logger.error("❌ Steam API Key ungültig (403 Forbidden)")
                return False
            else:
                logger.error(f"❌ Steam API Fehler bei Validierung: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"❌ Request Fehler bei API Key Validierung: {e}")
            return False
    
    def get_user_info(self, steam_id: str) -> Optional[Dict]:
        """
        Holt Benutzerinformationen für Steam ID
        
        Args:
            steam_id: Steam ID
            
        Returns:
            Benutzerinfo oder None
        """
        steam_id_64 = self.get_steam_id_64(steam_id)
        
        if not steam_id_64:
            return None
        
        self._wait_for_rate_limit()
        
        url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
        params = {
            'key': self.api_key,
            'steamids': steam_id_64
        }
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('response', {}).get('players'):
                    player = data['response']['players'][0]
                    
                    return {
                        'steamid': player.get('steamid'),
                        'personaname': player.get('personaname'),
                        'profileurl': player.get('profileurl'),
                        'avatar': player.get('avatar'),
                        'avatarmedium': player.get('avatarmedium'),
                        'avatarfull': player.get('avatarfull'),
                        'personastate': player.get('personastate'),
                        'communityvisibilitystate': player.get('communityvisibilitystate'),
                        'profilestate': player.get('profilestate'),
                        'lastlogoff': player.get('lastlogoff'),
                        'commentpermission': player.get('commentpermission')
                    }
                else:
                    logger.warning(f"⚠️ Keine Benutzerinformationen für {steam_id} gefunden")
                    return None
            else:
                logger.error(f"❌ Steam API Fehler bei Benutzerinfo: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"❌ Request Fehler bei Benutzerinfo: {e}")
            return None
    
    def get_owned_games(self, steam_id: str, include_appinfo: bool = True) -> List[Dict]:
        """
        Holt Liste der besessenen Spiele für Steam ID
        
        Args:
            steam_id: Steam ID
            include_appinfo: Ob App-Informationen inkludiert werden sollen
            
        Returns:
            Liste der besessenen Spiele
        """
        steam_id_64 = self.get_steam_id_64(steam_id)
        
        if not steam_id_64:
            return []
        
        self._wait_for_rate_limit()
        
        url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
        params = {
            'key': self.api_key,
            'steamid': steam_id_64,
            'include_appinfo': 1 if include_appinfo else 0,
            'format': 'json'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'response' in data and 'games' in data['response']:
                    games = data['response']['games']
                    logger.info(f"✅ {len(games)} besessene Spiele für {steam_id} gefunden")
                    
                    return [{
                        'steam_app_id': str(game['appid']),
                        'name': game.get('name', f'Game {game["appid"]}'),
                        'playtime_forever': game.get('playtime_forever', 0),
                        'playtime_2weeks': game.get('playtime_2weeks', 0)
                    } for game in games]
                else:
                    logger.warning(f"⚠️ Keine Spiele für {steam_id} gefunden oder Profil privat")
                    return []
            else:
                logger.error(f"❌ Steam API Fehler bei besessenen Spielen: {response.status_code}")
                return []
                
        except requests.RequestException as e:
            logger.error(f"❌ Request Fehler bei besessenen Spielen: {e}")
            return []

# ========================
# CONVENIENCE FUNCTIONS
# ========================

def create_env_template(env_file: str = ".env") -> bool:
    """
    Erstellt .env Template falls es nicht existiert
    
    Args:
        env_file: Pfad zur .env-Datei
        
    Returns:
        True wenn erstellt oder bereits vorhanden
    """
    env_path = Path(env_file)
    
    if env_path.exists():
        logger.info(f"✅ {env_file} bereits vorhanden")
        return True
    
    try:
        template_content = """# Steam Price Tracker Configuration
# Hole deinen Steam API Key von: https://steamcommunity.com/dev/apikey

STEAM_API_KEY=your_steam_api_key_here

# Optional: Weitere Konfiguration
TRACKER_DB_PATH=steam_price_tracker.db
TRACKING_INTERVAL_HOURS=6
CHEAPSHARK_RATE_LIMIT=1.5
"""
        
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        logger.info(f"✅ {env_file} Template erstellt")
        logger.info("💡 Bitte trage deinen Steam API Key ein!")
        logger.info("🔗 API Key holen: https://steamcommunity.com/dev/apikey")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen von {env_file}: {e}")
        return False

def quick_wishlist_import(steam_id: str, api_key: str = None) -> List[Dict]:
    """
    Schneller Wishlist-Import
    
    Args:
        steam_id: Steam ID
        api_key: Steam API Key (optional, falls in .env)
        
    Returns:
        Wishlist-Items
    """
    if api_key is None:
        api_key = load_api_key_from_env()
    
    if not api_key:
        logger.error("❌ Kein Steam API Key verfügbar")
        return []
    
    manager = SteamWishlistManager(api_key)
    return manager.get_simple_wishlist(steam_id)

def bulk_get_app_names(app_ids: List[str], api_key: str = None) -> Dict[str, str]:
    """
    Bulk-Abfrage für App-Namen
    
    Args:
        app_ids: Liste von Steam App IDs
        api_key: Steam API Key (optional, falls in .env)
        
    Returns:
        Dict mit app_id -> name Mapping
    """
    if api_key is None:
        api_key = load_api_key_from_env()
    
    if not api_key:
        logger.error("❌ Kein Steam API Key verfügbar")
        return {}
    
    manager = SteamWishlistManager(api_key)
    return manager.get_multiple_app_names(app_ids)

def validate_steam_api_key(api_key: str = None) -> bool:
    """
    Validiert Steam API Key
    
    Args:
        api_key: Steam API Key (optional, falls in .env)
        
    Returns:
        True wenn gültig
    """
    if api_key is None:
        api_key = load_api_key_from_env()
    
    if not api_key:
        logger.error("❌ Kein Steam API Key verfügbar")
        return False
    
    manager = SteamWishlistManager(api_key)
    return manager.validate_api_key()

def get_user_profile(steam_id: str, api_key: str = None) -> Optional[Dict]:
    """
    Holt Steam Benutzerprofil
    
    Args:
        steam_id: Steam ID
        api_key: Steam API Key (optional, falls in .env)
        
    Returns:
        Benutzerinformationen oder None
    """
    if api_key is None:
        api_key = load_api_key_from_env()
    
    if not api_key:
        logger.error("❌ Kein Steam API Key verfügbar")
        return None
    
    manager = SteamWishlistManager(api_key)
    return manager.get_user_info(steam_id)