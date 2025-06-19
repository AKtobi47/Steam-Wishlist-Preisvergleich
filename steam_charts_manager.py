#!/usr/bin/env python3
"""
Steam Charts Manager mit Enhanced Universal Background Scheduler Integration
Automatisches Tracking von Steam Charts (Most Played, Best Sellers, Top Releases)
Vollständig integriert mit price_tracker.py und main.py Menüpunkten 17-18
"""

import requests
import time
import json
import threading
import schedule
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
import logging
from pathlib import Path

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SteamChartsManager:
    """
    Steam Charts Manager mit Enhanced Universal Background Scheduler Integration
    Verwaltet automatisches Tracking von Steam Charts und deren Preise
    """
    
    # Chart-Typen Konfiguration
    CHART_TYPES = {
        'most_played': 'Steam Most Played',
        'best_sellers': 'Steam Best Sellers', 
        'top_releases': 'Steam Top New Releases'
    }
    
    # Steam Store API Endpoints
    STEAM_CHARTS_ENDPOINTS = {
        'most_played': 'https://steamcommunity.com/stats/mostplayed/json',
        'best_sellers': 'https://store.steampowered.com/api/featuredcategories?',
        'top_releases': 'https://store.steampowered.com/api/featured?'
    }
    
    def __init__(self, api_key: str, db_manager, price_tracker=None):
        """
        Initialisiert Steam Charts Manager
        
        Args:
            api_key: Steam API Key
            db_manager: DatabaseManager Instanz
            price_tracker: Optionale PriceTracker Instanz
        """
        self.api_key = api_key
        self.db_manager = db_manager
        self.price_tracker = price_tracker
        
        # HTTP Session für API-Requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SteamPriceTracker-Charts/3.0'
        })
        
        # Rate Limiting für Steam API
        self.last_steam_request = 0
        self.steam_rate_limit = 1.0  # 1 Sekunde zwischen Steam-Requests
        
        # Charts-Konfiguration
        self.charts_config = self._load_charts_config()
        
        # Background Scheduler Integration
        self.charts_scheduler_running = False
        self.charts_scheduler_thread = None
        self.stop_charts_scheduler_event = threading.Event()
        
        # Charts-Tabellen in Datenbank sicherstellen
        if hasattr(self.db_manager, 'init_charts_tables_enhanced'):
            self.db_manager.init_charts_tables_enhanced()
        elif hasattr(self.db_manager, 'init_charts_tables'):
            self.db_manager.init_charts_tables()
        
        logger.info("✅ Steam Charts Manager mit Enhanced Background Scheduler initialisiert")
    
    def set_price_tracker(self, price_tracker):
        """
        Setzt Price Tracker Referenz
        
        Args:
            price_tracker: SteamPriceTracker Instanz
        """
        self.price_tracker = price_tracker
        logger.debug("🔗 Price Tracker Referenz gesetzt")
    
    def _load_charts_config(self) -> Dict:
        """
        Lädt Charts-Konfiguration aus config.json
        
        Returns:
            Charts-Konfiguration Dictionary
        """
        try:
            config_file = Path("config.json")
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    full_config = json.load(f)
                return full_config.get('charts', {})
            else:
                # Standard-Konfiguration
                return {
                    'enabled': False,
                    'chart_types': ['most_played', 'best_sellers'],
                    'chart_counts': {
                        'most_played': 100,
                        'best_sellers': 100,
                        'top_releases': 50
                    },
                    'update_interval_hours': 6,
                    'price_interval_hours': 4,
                    'cleanup_interval_hours': 24,
                    'auto_track_charts': True,
                    'rate_limit_seconds': 1.0
                }
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Charts-Konfiguration: {e}")
            return {}
    
    def _save_charts_config(self, charts_config: Dict):
        """
        Speichert Charts-Konfiguration in config.json
        
        Args:
            charts_config: Charts-Konfiguration
        """
        try:
            config_file = Path("config.json")
            
            # Bestehende Konfiguration laden
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    full_config = json.load(f)
            else:
                full_config = {}
            
            # Charts-Konfiguration aktualisieren
            full_config['charts'] = charts_config
            
            # Zurückschreiben
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(full_config, f, indent=2, ensure_ascii=False)
            
            self.charts_config = charts_config
            logger.debug("💾 Charts-Konfiguration gespeichert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Charts-Konfiguration: {e}")
    
    def _wait_for_steam_rate_limit(self):
        """Wartet für Steam API Rate Limiting"""
        elapsed = time.time() - self.last_steam_request
        rate_limit = self.charts_config.get('rate_limit_seconds', 1.0)
        
        if elapsed < rate_limit:
            wait_time = rate_limit - elapsed
            time.sleep(wait_time)
        
        self.last_steam_request = time.time()
    
    # =====================================================================
    # CHARTS DATA RETRIEVAL FUNKTIONEN
    # =====================================================================
    
    def get_most_played_games(self, count: int = 100) -> List[Dict]:
        """
        Holt Most Played Games von Steam
        
        Args:
            count: Anzahl Spiele (max 100)
            
        Returns:
            Liste mit Spiel-Informationen
        """
        try:
            self._wait_for_steam_rate_limit()
            
            url = self.STEAM_CHARTS_ENDPOINTS['most_played']
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            games = []
            
            if 'response' in data and 'ranks' in data['response']:
                ranks = data['response']['ranks'][:count]
                
                for i, game in enumerate(ranks, 1):
                    app_id = str(game.get('appid', ''))
                    name = game.get('name', f'Unknown Game {app_id}')
                    
                    if app_id:
                        games.append({
                            'steam_app_id': app_id,
                            'name': name,
                            'rank': i,
                            'current_players': game.get('current', 0),
                            'peak_players': game.get('peak_today', 0),
                            'chart_type': 'most_played'
                        })
            
            logger.info(f"📊 {len(games)} Most Played Games abgerufen")
            return games
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Most Played Games: {e}")
            return []
    
    def get_best_sellers_games(self, count: int = 100) -> List[Dict]:
        """
        Holt Best Sellers von Steam Store API
        
        Args:
            count: Anzahl Spiele
            
        Returns:
            Liste mit Spiel-Informationen
        """
        try:
            self._wait_for_steam_rate_limit()
            
            # Steam Featured Categories API
            url = "https://store.steampowered.com/api/featuredcategories"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            games = []
            
            # Top Sellers aus verschiedenen Kategorien sammeln
            categories_to_check = ['top_sellers', 'new_and_trending', 'coming_soon']
            
            for category in categories_to_check:
                if category in data and 'items' in data[category]:
                    items = data[category]['items']
                    
                    for i, item in enumerate(items[:count//len(categories_to_check)]):
                        app_id = str(item.get('id', ''))
                        name = item.get('name', f'Unknown Game {app_id}')
                        
                        if app_id and len(games) < count:
                            # Duplikate vermeiden
                            if not any(g['steam_app_id'] == app_id for g in games):
                                rank = len(games) + 1
                                games.append({
                                    'steam_app_id': app_id,
                                    'name': name,
                                    'rank': rank,
                                    'category': category,
                                    'price': item.get('final_price', 0) / 100 if item.get('final_price') else None,
                                    'chart_type': 'best_sellers'
                                })
            
            logger.info(f"💰 {len(games)} Best Sellers abgerufen")
            return games
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Best Sellers: {e}")
            return []
    
    def get_top_releases_games(self, count: int = 50) -> List[Dict]:
        """
        Holt Top New Releases von Steam
        
        Args:
            count: Anzahl Spiele
            
        Returns:
            Liste mit Spiel-Informationen
        """
        try:
            self._wait_for_steam_rate_limit()
            
            # Steam Featured API für neue Releases
            url = "https://store.steampowered.com/api/featured"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            games = []
            
            # New Releases extrahieren
            if 'large_capsules' in data:
                items = data['large_capsules'][:count]
                
                for i, item in enumerate(items, 1):
                    app_id = str(item.get('id', ''))
                    name = item.get('name', f'Unknown Game {app_id}')
                    
                    if app_id:
                        games.append({
                            'steam_app_id': app_id,
                            'name': name,
                            'rank': i,
                            'price': item.get('final_price', 0) / 100 if item.get('final_price') else None,
                            'discount_percent': item.get('discount_percent', 0),
                            'chart_type': 'top_releases'
                        })
            
            logger.info(f"🆕 {len(games)} Top New Releases abgerufen")
            return games
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Top New Releases: {e}")
            return []
    
    # =====================================================================
    # CHARTS DATABASE INTEGRATION
    # =====================================================================
    
    def save_chart_game(self, game_data: Dict) -> bool:
        """
        Speichert oder aktualisiert ein Charts-Spiel in der Datenbank
        
        Args:
            game_data: Spiel-Informationen
            
        Returns:
            True wenn erfolgreich gespeichert
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                app_id = game_data['steam_app_id']
                chart_type = game_data['chart_type']
                current_rank = game_data.get('rank', 999)
                name = game_data['name']
                
                # Prüfen ob Spiel bereits existiert
                cursor.execute("""
                    SELECT current_rank, best_rank, days_in_charts, first_seen
                    FROM steam_charts_tracking
                    WHERE steam_app_id = ? AND chart_type = ?
                """, (app_id, chart_type))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Existierendes Spiel aktualisieren
                    old_rank = existing['current_rank']
                    best_rank = min(existing['best_rank'] or 999, current_rank)
                    days_in_charts = existing['days_in_charts'] + 1
                    
                    # Trend bestimmen
                    if current_rank < old_rank:
                        rank_trend = 'rising'
                    elif current_rank > old_rank:
                        rank_trend = 'falling'
                    else:
                        rank_trend = 'stable'
                    
                    cursor.execute("""
                        UPDATE steam_charts_tracking
                        SET current_rank = ?, best_rank = ?, last_seen = ?,
                            days_in_charts = ?, rank_trend = ?, updated_at = ?
                        WHERE steam_app_id = ? AND chart_type = ?
                    """, (
                        current_rank, best_rank, datetime.now(),
                        days_in_charts, rank_trend, datetime.now(),
                        app_id, chart_type
                    ))
                    
                    # Rank-Historie speichern
                    cursor.execute("""
                        INSERT INTO steam_charts_rank_history
                        (steam_app_id, chart_type, rank_position)
                        VALUES (?, ?, ?)
                    """, (app_id, chart_type, current_rank))
                    
                else:
                    # Neues Spiel hinzufügen
                    cursor.execute("""
                        INSERT INTO steam_charts_tracking
                        (steam_app_id, name, chart_type, current_rank, best_rank,
                         first_seen, last_seen, days_in_charts, rank_trend)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        app_id, name, chart_type, current_rank, current_rank,
                        datetime.now(), datetime.now(), 1, 'new'
                    ))
                    
                    # Initiale Rank-Historie
                    cursor.execute("""
                        INSERT INTO steam_charts_rank_history
                        (steam_app_id, chart_type, rank_position)
                        VALUES (?, ?, ?)
                    """, (app_id, chart_type, current_rank))
                    
                    # Auch zu tracked_apps hinzufügen (falls noch nicht vorhanden)
                    if self.charts_config.get('auto_track_charts', True):
                        self.db_manager.add_tracked_app(app_id, name, source='charts')
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern des Charts-Spiels {game_data.get('steam_app_id', 'Unknown')}: {e}")
            return False
    
    def save_chart_price(self, app_id: str, chart_type: str, price_data: Dict):
        """
        Speichert Preis-Information für Charts-Spiel
        
        Args:
            app_id: Steam App ID
            chart_type: Chart-Typ
            price_data: Preis-Informationen
        """
        try:
            # Besten Deal aus price_data finden
            best_deal = self._find_best_deal_from_price_data(price_data)
            
            if best_deal:
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        INSERT INTO steam_charts_prices
                        (steam_app_id, chart_type, current_price, original_price,
                         discount_percent, store, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        app_id, chart_type,
                        best_deal['price'], best_deal.get('original_price'),
                        best_deal.get('discount_percent', 0), best_deal['store'],
                        datetime.now()
                    ))
                    
                    conn.commit()
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern des Charts-Preises für {app_id}: {e}")
    
    def _find_best_deal_from_price_data(self, price_data: Dict) -> Optional[Dict]:
        """
        Findet den besten Deal aus Preis-Daten
        
        Args:
            price_data: Dictionary mit Preisinformationen
            
        Returns:
            Bester Deal oder None
        """
        stores = ['steam', 'greenmangaming', 'gog', 'humblestore', 'fanatical', 'gamesplanet']
        best_deal = None
        best_price = float('inf')
        
        for store in stores:
            price_key = f"{store}_price"
            available_key = f"{store}_available"
            
            if (price_key in price_data and available_key in price_data and
                price_data[available_key] and price_data[price_key] is not None):
                
                price = price_data[price_key]
                
                if price < best_price:
                    best_price = price
                    best_deal = {
                        'store': store.title(),
                        'price': price,
                        'original_price': price_data.get(f"{store}_original_price"),
                        'discount_percent': price_data.get(f"{store}_discount_percent", 0)
                    }
        
        return best_deal
    
    # =====================================================================
    # CHARTS UPDATE FUNKTIONEN
    # =====================================================================
    
    def update_single_chart(self, chart_type: str) -> Dict:
        """
        Aktualisiert einen einzelnen Chart-Typ
        
        Args:
            chart_type: Chart-Typ ('most_played', 'best_sellers', 'top_releases')
            
        Returns:
            Update-Ergebnis Dictionary
        """
        try:
            logger.info(f"🔄 Aktualisiere {self.CHART_TYPES.get(chart_type, chart_type)}...")
            
            count = self.charts_config.get('chart_counts', {}).get(chart_type, 100)
            
            # Spiele für Chart-Typ abrufen
            if chart_type == 'most_played':
                games = self.get_most_played_games(count)
            elif chart_type == 'best_sellers':
                games = self.get_best_sellers_games(count)
            elif chart_type == 'top_releases':
                games = self.get_top_releases_games(count)
            else:
                return {'success': False, 'error': f'Unbekannter Chart-Typ: {chart_type}'}
            
            if not games:
                return {'success': False, 'error': f'Keine Spiele für {chart_type} erhalten'}
            
            # Spiele in Datenbank speichern
            new_games = 0
            updated_games = 0
            errors = []
            
            for game in games:
                try:
                    # Prüfen ob Spiel bereits existiert
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT steam_app_id FROM steam_charts_tracking
                            WHERE steam_app_id = ? AND chart_type = ?
                        """, (game['steam_app_id'], chart_type))
                        
                        if cursor.fetchone():
                            updated_games += 1
                        else:
                            new_games += 1
                    
                    # Spiel speichern
                    self.save_chart_game(game)
                    
                except Exception as e:
                    errors.append(f"Fehler bei {game.get('steam_app_id', 'Unknown')}: {str(e)}")
            
            # Update-Statistiken speichern
            self._save_update_statistics(chart_type, len(games), new_games, updated_games)
            
            result = {
                'success': True,
                'chart_type': chart_type,
                'total_games_found': len(games),
                'new_games_added': new_games,
                'existing_games_updated': updated_games,
                'errors': errors
            }
            
            logger.info(f"✅ {chart_type}: {new_games} neu, {updated_games} aktualisiert")
            return result
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren von {chart_type}: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_all_charts(self, chart_types: List[str] = None) -> Dict:
        """
        Aktualisiert alle oder spezifische Chart-Typen
        
        Args:
            chart_types: Spezifische Chart-Typen (optional)
            
        Returns:
            Gesamt-Update-Ergebnis
        """
        start_time = time.time()
        
        if chart_types is None:
            chart_types = self.charts_config.get('chart_types', ['most_played', 'best_sellers'])
        
        total_games_found = 0
        total_new_games = 0
        total_updated_games = 0
        all_errors = []
        
        logger.info(f"🚀 Starte Charts-Update für: {', '.join(chart_types)}")
        
        for chart_type in chart_types:
            try:
                result = self.update_single_chart(chart_type)
                
                if result['success']:
                    total_games_found += result['total_games_found']
                    total_new_games += result['new_games_added']
                    total_updated_games += result['existing_games_updated']
                    all_errors.extend(result['errors'])
                else:
                    all_errors.append(f"{chart_type}: {result['error']}")
                
                # Pause zwischen Chart-Typen
                time.sleep(2.0)
                
            except Exception as e:
                all_errors.append(f"{chart_type}: {str(e)}")
        
        duration = time.time() - start_time
        
        # Gesamt-Statistiken speichern
        self._save_update_statistics('all_charts', total_games_found, total_new_games, total_updated_games, duration)
        
        result = {
            'success': len(all_errors) == 0,
            'chart_types': chart_types,
            'total_games_found': total_games_found,
            'new_games_added': total_new_games,
            'existing_games_updated': total_updated_games,
            'duration': duration,
            'errors': all_errors
        }
        
        logger.info(f"🎉 Charts-Update abgeschlossen: {total_new_games} neu, {total_updated_games} aktualisiert in {duration:.1f}s")
        return result
    
    def _save_update_statistics(self, chart_type: str, total_games: int, new_games: int, updated_games: int, duration: float = 0.0, api_calls: int = 1):
        """
        Speichert Update-Statistiken in Datenbank
        
        Args:
            chart_type: Chart-Typ
            total_games: Gesamt-Anzahl Spiele
            new_games: Neue Spiele
            updated_games: Aktualisierte Spiele
            duration: Update-Dauer in Sekunden
            api_calls: Anzahl API-Calls
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO steam_charts_statistics
                    (chart_type, total_games, new_games, updated_games, 
                     update_duration, api_calls)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (chart_type, total_games, new_games, updated_games, duration, api_calls))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Update-Statistiken: {e}")
    
    # =====================================================================
    # CHARTS CLEANUP FUNKTIONEN
    # =====================================================================
    
    def cleanup_old_chart_games(self, days_threshold: int = 30) -> int:
        """
        Bereinigt alte Charts-Spiele die nicht mehr in Charts sind
        
        Args:
            days_threshold: Spiele älter als X Tage entfernen
            
        Returns:
            Anzahl entfernter Spiele
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Alte Charts-Spiele finden
                cursor.execute("""
                    SELECT steam_app_id, chart_type, name
                    FROM steam_charts_tracking
                    WHERE last_seen < datetime('now', '-{} days')
                """.format(days_threshold))
                
                old_games = cursor.fetchall()
                
                if not old_games:
                    logger.info("✅ Keine alten Charts-Spiele zum Entfernen")
                    return 0
                
                # Alte Spiele entfernen
                removed_count = 0
                for game in old_games:
                    app_id = game['steam_app_id']
                    chart_type = game['chart_type']
                    name = game['name']
                    
                    # Charts-Tracking Eintrag entfernen
                    cursor.execute("""
                        DELETE FROM steam_charts_tracking
                        WHERE steam_app_id = ? AND chart_type = ?
                    """, (app_id, chart_type))
                    
                    # Zugehörige Preis-Einträge entfernen
                    cursor.execute("""
                        DELETE FROM steam_charts_prices
                        WHERE steam_app_id = ? AND chart_type = ?
                    """, (app_id, chart_type))
                    
                    # Zugehörige Rank-Historie entfernen
                    cursor.execute("""
                        DELETE FROM steam_charts_rank_history
                        WHERE steam_app_id = ? AND chart_type = ?
                    """, (app_id, chart_type))
                    
                    removed_count += 1
                    logger.debug(f"🗑️ Entfernt: {name} ({app_id}) aus {chart_type}")
                
                conn.commit()
                logger.info(f"🧹 {removed_count} alte Charts-Spiele entfernt (>{days_threshold} Tage)")
                
                return removed_count
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Bereinigen alter Charts-Spiele: {e}")
            return 0
    
    # =====================================================================
    # CHARTS STATISTICS & INFO FUNKTIONEN
    # =====================================================================
    
    def get_chart_statistics(self) -> Dict:
        """
        Gibt detaillierte Charts-Statistiken zurück
        
        Returns:
            Dictionary mit Charts-Statistiken
        """
        try:
            stats = {}
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Statistiken pro Chart-Typ
                for chart_type in self.CHART_TYPES.keys():
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_games,
                            COUNT(CASE WHEN current_rank <= 10 THEN 1 END) as top_10_games,
                            AVG(current_rank) as avg_rank,
                            MIN(current_rank) as best_rank,
                            MAX(last_seen) as last_update
                        FROM steam_charts_tracking
                        WHERE chart_type = ? AND last_seen >= datetime('now', '-7 days')
                    """, (chart_type,))
                    
                    result = cursor.fetchone()
                    if result:
                        stats[chart_type] = {
                            'chart_name': self.CHART_TYPES[chart_type],
                            'total_games': result['total_games'],
                            'top_10_games': result['top_10_games'],
                            'avg_rank': round(result['avg_rank'] or 0, 1),
                            'best_rank': result['best_rank'],
                            'last_update': result['last_update']
                        }
                
                # Gesamt-Statistiken
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_active_games,
                        COUNT(DISTINCT steam_app_id) as unique_games,
                        COUNT(DISTINCT chart_type) as active_chart_types
                    FROM steam_charts_tracking
                    WHERE last_seen >= datetime('now', '-7 days')
                """)
                
                total_result = cursor.fetchone()
                if total_result:
                    stats['total'] = {
                        'total_active_games': total_result['total_active_games'],
                        'unique_games': total_result['unique_games'],
                        'active_chart_types': total_result['active_chart_types']
                    }
                
                # Update-Performance (letzte 7 Tage)
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_updates,
                        AVG(update_duration) as avg_duration,
                        SUM(new_games) as total_new_games,
                        SUM(updated_games) as total_updated_games
                    FROM steam_charts_statistics
                    WHERE timestamp >= datetime('now', '-7 days')
                """)
                
                perf_result = cursor.fetchone()
                if perf_result:
                    stats['performance'] = {
                        'total_updates': perf_result['total_updates'],
                        'avg_duration': round(perf_result['avg_duration'] or 0, 1),
                        'total_new_games': perf_result['total_new_games'],
                        'total_updated_games': perf_result['total_updated_games']
                    }
                
                return stats
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Charts-Statistiken: {e}")
            return {'error': str(e)}
    
    def get_active_chart_games(self, chart_type: str = None) -> List[Dict]:
        """
        Gibt aktive Charts-Spiele zurück
        
        Args:
            chart_type: Optionale Filterung nach Chart-Typ
            
        Returns:
            Liste aktiver Charts-Spiele
        """
        return self.db_manager.get_active_chart_games(chart_type)
    
    def get_trending_games(self, chart_type: str = None, limit: int = 20) -> List[Dict]:
        """
        Gibt trending Games zurück (steigende Ränge)
        
        Args:
            chart_type: Optionale Filterung nach Chart-Typ
            limit: Maximum Anzahl Spiele
            
        Returns:
            Liste mit trending Games
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT * FROM charts_trending
                    WHERE trend_direction = 'rising'
                """
                params = []
                
                if chart_type:
                    query += " AND chart_type = ?"
                    params.append(chart_type)
                
                query += " ORDER BY current_rank LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der trending Games: {e}")
            return []
    
    def get_charts_deals(self, min_discount: int = 10, limit: int = 20) -> List[Dict]:
        """
        Findet aktuelle Deals in Charts-Spielen
        
        Args:
            min_discount: Mindest-Rabatt in Prozent
            limit: Maximum Anzahl Deals
            
        Returns:
            Liste mit Charts-Deals
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        sct.steam_app_id,
                        sct.name,
                        sct.chart_type,
                        sct.current_rank,
                        scp.current_price,
                        scp.original_price,
                        scp.discount_percent,
                        scp.store,
                        scp.timestamp
                    FROM steam_charts_tracking sct
                    INNER JOIN steam_charts_prices scp ON 
                        sct.steam_app_id = scp.steam_app_id AND 
                        sct.chart_type = scp.chart_type
                    WHERE scp.discount_percent >= ?
                    AND scp.timestamp >= datetime('now', '-24 hours')
                    ORDER BY scp.discount_percent DESC, sct.current_rank ASC
                    LIMIT ?
                """, (min_discount, limit))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Charts-Deals: {e}")
            return []
    
    # =====================================================================
    # BACKGROUND SCHEDULER FUNKTIONEN (Legacy Support)
    # =====================================================================
    
    def start_charts_scheduler(self, 
                              charts_update_hours: int = 6,
                              cleanup_hours: int = 24,
                              price_update_hours: int = 4):
        """
        LEGACY: Startet automatisches Charts-Tracking mit robuster Thread-Verwaltung
        Für Kompatibilität mit älteren Versionen - nutzt Enhanced Background Scheduler
        
        Args:
            charts_update_hours: Intervall für Charts-Updates
            cleanup_hours: Intervall für Cleanup
            price_update_hours: Intervall für Preis-Updates der Charts-Spiele
        """
        logger.warning("⚠️ Legacy Charts-Scheduler wird verwendet - empfohlen: Enhanced Background Scheduler")
        
        if self.charts_scheduler_running:
            logger.warning("⚠️ Charts-Scheduler läuft bereits")
            return
        
        # Bestehende Charts-Jobs löschen
        charts_jobs = [job for job in schedule.jobs if 'charts' in str(job.job_func)]
        for job in charts_jobs:
            schedule.cancel_job(job)
        
        # Charts-Update Job
        schedule.every(charts_update_hours).hours.do(self._scheduled_charts_update)
        
        # Cleanup Job
        schedule.every(cleanup_hours).hours.do(self._scheduled_charts_cleanup)
        
        # Preis-Update Job für Charts-Spiele
        if hasattr(self, 'price_tracker') and self.price_tracker:
            schedule.every(price_update_hours).hours.do(self._scheduled_charts_price_update)
        
        # FIXED: Scheduler-Thread sicher starten
        if self.charts_scheduler_thread is not None and self.charts_scheduler_thread.is_alive():
            logger.info("📊 Charts-Scheduler-Thread läuft bereits")
        else:
            self.stop_charts_scheduler_event.clear()
            self.charts_scheduler_thread = threading.Thread(target=self._run_charts_scheduler, daemon=True)
            self.charts_scheduler_thread.start()
            logger.info("🚀 Charts-Scheduler-Thread gestartet")
        
        self.charts_scheduler_running = True
        logger.info(f"✅ Charts-Scheduler aktiviert:")
        logger.info(f"   📊 Charts-Update alle {charts_update_hours}h")
        logger.info(f"   🧹 Cleanup alle {cleanup_hours}h")
        logger.info(f"   💰 Preis-Updates alle {price_update_hours}h")
    
    def stop_charts_scheduler(self):
        """LEGACY: Stoppt den Charts-Scheduler mit robuster Thread-Verwaltung"""
        if not self.charts_scheduler_running:
            logger.info("ℹ️ Charts-Scheduler war nicht aktiv")
            return
        
        # Signal zum Stoppen setzen
        self.stop_charts_scheduler_event.set()
        
        # Charts-Jobs entfernen
        charts_jobs = [job for job in schedule.jobs if 'charts' in str(job.job_func)]
        for job in charts_jobs:
            schedule.cancel_job(job)
        
        # FIXED: Auf Thread-Ende warten mit Timeout
        if self.charts_scheduler_thread is not None and self.charts_scheduler_thread.is_alive():
            self.charts_scheduler_thread.join(timeout=5)
        
        self.charts_scheduler_running = False
        self.charts_scheduler_thread = None
        
        logger.info("⏹️ Charts-Scheduler gestoppt")
    
    def _run_charts_scheduler(self):
        """Führt Charts-Scheduler in eigenem Thread aus"""
        logger.info("🚀 Charts-Scheduler-Thread gestartet")
        
        while not self.stop_charts_scheduler_event.is_set():
            try:
                schedule.run_pending()
                time.sleep(60)  # Prüfe jede Minute
            except Exception as e:
                logger.error(f"❌ Charts-Scheduler-Fehler: {e}")
                time.sleep(60)
        
        logger.info("⏹️ Charts-Scheduler-Thread beendet")
    
    def _scheduled_charts_update(self):
        """Automatisches Charts-Update"""
        try:
            logger.info("🔄 Automatisches Charts-Update gestartet")
            result = self.update_all_charts()
            logger.info(f"✅ Automatisches Charts-Update: {result['new_games_added']} neue, {result['existing_games_updated']} aktualisiert")
        except Exception as e:
            logger.error(f"❌ Fehler beim automatischen Charts-Update: {e}")
    
    def _scheduled_charts_cleanup(self):
        """Automatisches Charts-Cleanup"""
        try:
            logger.info("🧹 Automatisches Charts-Cleanup gestartet")
            removed = self.cleanup_old_chart_games(days_threshold=30)
            logger.info(f"✅ Automatisches Charts-Cleanup: {removed} alte Spiele entfernt")
        except Exception as e:
            logger.error(f"❌ Fehler beim automatischen Charts-Cleanup: {e}")
    
    def _scheduled_charts_price_update(self):
        """Automatisches Charts-Preis-Update"""
        try:
            if self.price_tracker:
                logger.info("💰 Automatisches Charts-Preis-Update gestartet")
                result = self.price_tracker.update_charts_prices_now()
                logger.info(f"✅ Charts-Preis-Update: {result.get('price_updates', 0)} Preise aktualisiert")
            else:
                logger.warning("⚠️ Price Tracker nicht verfügbar für Charts-Preis-Update")
        except Exception as e:
            logger.error(f"❌ Fehler beim automatischen Charts-Preis-Update: {e}")
    
    def get_charts_scheduler_status(self) -> Dict:
        """
        Gibt Status des Charts-Schedulers zurück
        
        Returns:
            Dictionary mit Scheduler-Status
        """
        return {
            'scheduler_running': self.charts_scheduler_running,
            'thread_alive': self.charts_scheduler_thread is not None and self.charts_scheduler_thread.is_alive(),
            'scheduled_jobs': len([job for job in schedule.jobs if 'charts' in str(job.job_func)]),
            'configuration': self.charts_config
        }

# =====================================================================
# CONVENIENCE FUNCTIONS
# =====================================================================

def create_charts_manager(api_key: str, db_manager) -> SteamChartsManager:
    """
    Erstellt Steam Charts Manager Instanz
    
    Args:
        api_key: Steam API Key
        db_manager: DatabaseManager Instanz
        
    Returns:
        SteamChartsManager Instanz
    """
    return SteamChartsManager(api_key, db_manager)

def setup_charts_automation(charts_manager: SteamChartsManager,
                           update_interval: int = 6,
                           price_interval: int = 4,
                           cleanup_interval: int = 24) -> bool:
    """
    Richtet vollautomatisches Charts-Tracking ein
    
    Args:
        charts_manager: SteamChartsManager Instanz
        update_interval: Charts-Update Intervall (Stunden)
        price_interval: Preis-Update Intervall (Stunden)
        cleanup_interval: Cleanup Intervall (Stunden)
        
    Returns:
        True wenn erfolgreich eingerichtet
    """
    try:
        charts_manager.start_charts_scheduler(
            charts_update_hours=update_interval,
            price_update_hours=price_interval,
            cleanup_hours=cleanup_interval
        )
        
        # Konfiguration speichern
        config = charts_manager.charts_config.copy()
        config.update({
            'enabled': True,
            'update_interval_hours': update_interval,
            'price_interval_hours': price_interval,
            'cleanup_interval_hours': cleanup_interval
        })
        charts_manager._save_charts_config(config)
        
        logger.info("🚀 Charts-Automation erfolgreich eingerichtet!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Einrichten der Charts-Automation: {e}")
        return False

if __name__ == "__main__":
    # Test-Ausführung
    print("🧪 Steam Charts Manager - Test Mode")
    
    try:
        # Mock Database Manager für Test
        class MockDB:
            def init_charts_tables_enhanced(self):
                pass
            def get_connection(self):
                pass
        
        # Charts Manager erstellen
        charts_manager = SteamChartsManager("test_api_key", MockDB())
        
        print("✅ Charts Manager erstellt")
        
        # Test Charts-Abruf
        print("🔄 Teste Most Played Games Abruf...")
        games = charts_manager.get_most_played_games(5)
        print(f"📊 {len(games)} Spiele abgerufen")
        
        # Statistiken anzeigen
        stats = charts_manager.get_chart_statistics()
        print(f"📈 Statistiken: {stats}")
        
    except Exception as e:
        print(f"❌ Test-Fehler: {e}")
