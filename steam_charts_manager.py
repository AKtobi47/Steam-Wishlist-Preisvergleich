"""
Steam Charts Manager - Automatisches Tracking von Steam Charts
Integriert Steam Charts APIs für automatisches Preis-Tracking beliebter Spiele
"""

import requests
import time
import threading
import schedule
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class SteamChartsManager:
    """
    Steam Charts Manager für automatisches Tracking von Charts-Spielen
    Nutzt verschiedene Steam API Endpoints für Charts-Daten
    """
    
    # Chart-Typen die wir unterstützen
    CHART_TYPES = {
        'most_played': 'Meistgespielte Spiele',
        'top_releases': 'Beste neue Releases', 
        'best_sellers': 'Bestseller',
        'weekly_top_sellers': 'Wöchentliche Bestseller',
        'trending': 'Trending Spiele'
    }
    
    def __init__(self, api_key: str, db_manager=None):
        """
        Initialisiert Steam Charts Manager
        
        Args:
            api_key: Steam Web API Key
            db_manager: DatabaseManager Instanz
        """
        self.api_key = api_key
        self.db_manager = db_manager
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SteamPriceTracker-Charts/1.0'
        })
        
        # Rate Limiting
        self.last_request_time = 0
        self.rate_limit = 1.0  # 1 Sekunde zwischen Steam API Requests
        
        # Charts Scheduler
        self.charts_scheduler_running = False
        self.charts_scheduler_thread = None
        self.stop_charts_scheduler_event = threading.Event()
        
        logger.info("✅ Steam Charts Manager initialisiert")
    
    def _wait_for_rate_limit(self):
        """Wartet für Steam API Rate Limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit:
            wait_time = self.rate_limit - time_since_last
            logger.debug(f"⏳ Steam API Rate Limit: Warte {wait_time:.2f}s")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    # ========================
    # STEAM CHARTS API CALLS
    # ========================
    
    def get_most_played_games(self, count: int = 100) -> List[Dict]:
        """
        Holt die meistgespielten Spiele von Steam
        
        Args:
            count: Anzahl Spiele (max 500)
            
        Returns:
            Liste der meistgespielten Spiele
        """
        self._wait_for_rate_limit()
        
        url = "https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/"
        params = {
            'key': self.api_key,
            'count': min(count, 500)
        }
        
        try:
            logger.debug(f"🔍 Hole {count} meistgespielte Spiele...")
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'response' in data and 'ranks' in data['response']:
                    games = []
                    ranks = data['response']['ranks']
                    
                    for rank_data in ranks:
                        game_info = {
                            'steam_app_id': str(rank_data.get('appid', '')),
                            'name': rank_data.get('name', f"Game {rank_data.get('appid', '')}"),
                            'rank': rank_data.get('rank', 0),
                            'peak_players': rank_data.get('peak_in_game', 0),
                            'current_players': rank_data.get('current_players', 0),
                            'chart_type': 'most_played',
                            'retrieved_at': datetime.now().isoformat()
                        }
                        
                        if game_info['steam_app_id']:
                            games.append(game_info)
                    
                    logger.info(f"✅ {len(games)} meistgespielte Spiele abgerufen")
                    return games
                else:
                    logger.warning("⚠️ Keine Charts-Daten in Antwort gefunden")
                    return []
            else:
                logger.error(f"❌ Steam Charts API Fehler: {response.status_code}")
                return []
                
        except requests.RequestException as e:
            logger.error(f"❌ Request Fehler bei meistgespielten Spielen: {e}")
            return []
    
    def get_top_releases(self, count: int = 100) -> List[Dict]:
        """
        Holt die besten neuen Releases von Steam
        
        Args:
            count: Anzahl Spiele
            
        Returns:
            Liste der besten neuen Releases
        """
        self._wait_for_rate_limit()
        
        url = "https://api.steampowered.com/ISteamChartsService/GetTopReleasesPages/v1/"
        params = {
            'key': self.api_key
        }
        
        try:
            logger.debug(f"🔍 Hole beste neue Releases...")
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'response' in data and 'pages' in data['response']:
                    games = []
                    pages = data['response']['pages']
                    
                    collected = 0
                    for page in pages:
                        if 'item_ids' in page:
                            for item_id in page['item_ids']:
                                if collected >= count:
                                    break
                                
                                # Hier müssten wir normalerweise App-Details abrufen
                                # Für Einfachheit verwenden wir die App-ID direkt
                                game_info = {
                                    'steam_app_id': str(item_id),
                                    'name': f"New Release {item_id}",  # Wird später von Steam API geholt
                                    'rank': collected + 1,
                                    'chart_type': 'top_releases',
                                    'retrieved_at': datetime.now().isoformat()
                                }
                                
                                games.append(game_info)
                                collected += 1
                        
                        if collected >= count:
                            break
                    
                    logger.info(f"✅ {len(games)} neue Releases abgerufen")
                    return games
                else:
                    logger.warning("⚠️ Keine Top Releases Daten gefunden")
                    return []
            else:
                logger.error(f"❌ Steam Charts API Fehler für Top Releases: {response.status_code}")
                return []
                
        except requests.RequestException as e:
            logger.error(f"❌ Request Fehler bei Top Releases: {e}")
            return []
    
    def get_best_sellers(self, count: int = 100) -> List[Dict]:
        """
        Holt Bestseller von Steam Store
        
        Args:
            count: Anzahl Spiele
            
        Returns:
            Liste der Bestseller
        """
        # Fallback auf Steam Store API da GetBestSellersPages möglicherweise nicht verfügbar
        try:
            logger.debug(f"🔍 Hole Bestseller...")
            
            # Steam Store Featured Categories API
            url = "https://store.steampowered.com/api/featuredcategories"
            
            self._wait_for_rate_limit()
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                games = []
                
                # Verschiedene Kategorien durchsuchen
                categories_to_check = ['bestsellers', 'top_sellers', 'new_releases']
                
                for category in categories_to_check:
                    if category in data and 'items' in data[category]:
                        for i, item in enumerate(data[category]['items'][:count]):
                            if len(games) >= count:
                                break
                                
                            game_info = {
                                'steam_app_id': str(item.get('id', '')),
                                'name': item.get('name', f"Game {item.get('id', '')}"),
                                'rank': len(games) + 1,
                                'chart_type': 'best_sellers',
                                'retrieved_at': datetime.now().isoformat(),
                                'original_price': item.get('original_price'),
                                'final_price': item.get('final_price'),
                                'discount_percent': item.get('discount_percent', 0)
                            }
                            
                            if game_info['steam_app_id'] and game_info['steam_app_id'] not in [g['steam_app_id'] for g in games]:
                                games.append(game_info)
                
                logger.info(f"✅ {len(games)} Bestseller abgerufen")
                return games
            else:
                logger.error(f"❌ Steam Store API Fehler für Bestseller: {response.status_code}")
                return []
                
        except requests.RequestException as e:
            logger.error(f"❌ Request Fehler bei Bestsellern: {e}")
            return []
    
    def get_weekly_top_sellers(self, count: int = 100) -> List[Dict]:
        """
        Holt wöchentliche Bestseller
        
        Args:
            count: Anzahl Spiele
            
        Returns:
            Liste der wöchentlichen Bestseller
        """
        self._wait_for_rate_limit()
        
        # Verwende Steam Charts Service für wöchentliche Daten
        url = "https://api.steampowered.com/ISteamChartsService/GetWeeklyTopSellers/v1/"
        params = {
            'key': self.api_key
        }
        
        try:
            logger.debug(f"🔍 Hole wöchentliche Bestseller...")
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'response' in data and 'ranks' in data['response']:
                    games = []
                    ranks = data['response']['ranks']
                    
                    for rank_data in ranks[:count]:
                        game_info = {
                            'steam_app_id': str(rank_data.get('item', {}).get('appid', '')),
                            'name': rank_data.get('item', {}).get('name', f"Game {rank_data.get('item', {}).get('appid', '')}"),
                            'rank': rank_data.get('rank', 0),
                            'chart_type': 'weekly_top_sellers',
                            'retrieved_at': datetime.now().isoformat()
                        }
                        
                        if game_info['steam_app_id']:
                            games.append(game_info)
                    
                    logger.info(f"✅ {len(games)} wöchentliche Bestseller abgerufen")
                    return games
                else:
                    logger.warning("⚠️ Keine wöchentliche Bestseller Daten gefunden")
                    return []
            else:
                logger.error(f"❌ Steam Charts API Fehler für wöchentliche Bestseller: {response.status_code}")
                return []
                
        except requests.RequestException as e:
            logger.error(f"❌ Request Fehler bei wöchentlichen Bestsellern: {e}")
            return []
    
    # ========================
    # CHARTS DATA MANAGEMENT
    # ========================
    
    def update_all_charts(self, counts: Dict[str, int] = None) -> Dict:
        """
        Aktualisiert alle Steam Charts
        
        Args:
            counts: Dict mit Chart-Typ -> Anzahl Mapping
            
        Returns:
            Update-Statistiken
        """
        if counts is None:
            counts = {
                'most_played': 100,
                'top_releases': 50,
                'best_sellers': 100,
                'weekly_top_sellers': 75
            }
        
        logger.info("🔄 Starte Charts-Update für alle Kategorien...")
        
        results = {
            'total_games_found': 0,
            'new_games_added': 0,
            'existing_games_updated': 0,
            'charts_updated': [],
            'errors': []
        }
        
        # Charts-Funktionen
        chart_functions = {
            'most_played': self.get_most_played_games,
            'top_releases': self.get_top_releases,
            'best_sellers': self.get_best_sellers,
            'weekly_top_sellers': self.get_weekly_top_sellers
        }
        
        for chart_type, count in counts.items():
            if chart_type not in chart_functions:
                logger.warning(f"⚠️ Unbekannter Chart-Typ: {chart_type}")
                continue
            
            try:
                logger.info(f"📊 Aktualisiere {self.CHART_TYPES.get(chart_type, chart_type)}...")
                
                # Charts-Daten abrufen
                chart_games = chart_functions[chart_type](count)
                
                if not chart_games:
                    logger.warning(f"⚠️ Keine Daten für {chart_type}")
                    continue
                
                # In Datenbank speichern
                new_added, existing_updated = self._save_charts_data(chart_games, chart_type)
                
                results['total_games_found'] += len(chart_games)
                results['new_games_added'] += new_added
                results['existing_games_updated'] += existing_updated
                results['charts_updated'].append(chart_type)
                
                logger.info(f"✅ {chart_type}: {len(chart_games)} Spiele, {new_added} neu, {existing_updated} aktualisiert")
                
                # Kurze Pause zwischen Charts
                time.sleep(2)
                
            except Exception as e:
                error_msg = f"Fehler bei {chart_type}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        logger.info(f"🎉 Charts-Update abgeschlossen:")
        logger.info(f"   📊 {results['total_games_found']} Spiele gefunden")
        logger.info(f"   ➕ {results['new_games_added']} neue Spiele")
        logger.info(f"   🔄 {results['existing_games_updated']} bestehende aktualisiert")
        
        return results
    
    def _save_charts_data(self, chart_games: List[Dict], chart_type: str) -> tuple:
        """
        Speichert Charts-Daten in Datenbank
        
        Args:
            chart_games: Liste der Charts-Spiele
            chart_type: Typ des Charts
            
        Returns:
            Tuple (neue_spiele, aktualisierte_spiele)
        """
        if not self.db_manager:
            logger.error("❌ Kein DatabaseManager verfügbar")
            return 0, 0
        
        new_added = 0
        existing_updated = 0
        
        for game in chart_games:
            try:
                # Prüfe ob Spiel bereits in Charts-Tracking ist
                existing = self.db_manager.get_chart_game(game['steam_app_id'], chart_type)
                
                if existing:
                    # Aktualisiere bestehenden Eintrag
                    if self.db_manager.update_chart_game(
                        game['steam_app_id'],
                        chart_type,
                        game.get('rank', 0),
                        game.get('name', ''),
                        game
                    ):
                        existing_updated += 1
                else:
                    # Füge neues Spiel hinzu
                    if self.db_manager.add_chart_game(
                        game['steam_app_id'],
                        game.get('name', f"Game {game['steam_app_id']}"),
                        chart_type,
                        game.get('rank', 0),
                        game
                    ):
                        new_added += 1
                        
            except Exception as e:
                logger.error(f"❌ Fehler beim Speichern von Spiel {game.get('steam_app_id')}: {e}")
        
        return new_added, existing_updated
    
    def cleanup_old_chart_games(self, days_threshold: int = 30) -> int:
        """
        Entfernt Spiele die zu lange nicht mehr in Charts waren
        
        Args:
            days_threshold: Tage nach denen Spiele entfernt werden
            
        Returns:
            Anzahl entfernter Spiele
        """
        if not self.db_manager:
            logger.error("❌ Kein DatabaseManager verfügbar")
            return 0
        
        logger.info(f"🧹 Bereinige Charts-Spiele älter als {days_threshold} Tage...")
        
        removed_count = self.db_manager.cleanup_old_chart_games(days_threshold)
        
        if removed_count > 0:
            logger.info(f"✅ {removed_count} alte Charts-Spiele entfernt")
        else:
            logger.info("✅ Keine alten Charts-Spiele zum Entfernen gefunden")
        
        return removed_count
    
    def get_active_chart_games(self, chart_type: str = None) -> List[Dict]:
        """
        Gibt aktive Charts-Spiele zurück
        
        Args:
            chart_type: Optionale Filterung nach Chart-Typ
            
        Returns:
            Liste aktiver Charts-Spiele
        """
        if not self.db_manager:
            return []
        
        return self.db_manager.get_active_chart_games(chart_type)
    
    def get_chart_statistics(self) -> Dict:
        """
        Gibt Charts-Statistiken zurück
        
        Returns:
            Dict mit Charts-Statistiken
        """
        if not self.db_manager:
            return {}
        
        stats = {}
        
        # Statistiken pro Chart-Typ
        for chart_type in self.CHART_TYPES.keys():
            chart_games = self.get_active_chart_games(chart_type)
            stats[chart_type] = {
                'active_games': len(chart_games),
                'chart_name': self.CHART_TYPES[chart_type]
            }
        
        # Gesamt-Statistiken
        all_active = self.get_active_chart_games()
        stats['total'] = {
            'total_active_games': len(all_active),
            'unique_games': len(set(game['steam_app_id'] for game in all_active)),
            'total_chart_types': len([ct for ct in stats if ct != 'total' and stats[ct]['active_games'] > 0])
        }
        
        return stats
    
    # ========================
    # SCHEDULER FOR CHARTS
    # ========================
    
    def start_charts_scheduler(self, 
                              charts_update_hours: int = 6,
                              cleanup_hours: int = 24,
                              price_update_hours: int = 4):
        """
        Startet automatisches Charts-Tracking
        
        Args:
            charts_update_hours: Intervall für Charts-Updates
            cleanup_hours: Intervall für Cleanup
            price_update_hours: Intervall für Preis-Updates der Charts-Spiele
        """
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
        
        # Scheduler-Thread starten (falls nicht bereits läuft)
        if not hasattr(self, 'charts_scheduler_thread') or not self.charts_scheduler_thread.is_alive():
            self.stop_charts_scheduler_event.clear()
            self.charts_scheduler_thread = threading.Thread(target=self._run_charts_scheduler, daemon=True)
            self.charts_scheduler_thread.start()
        
        self.charts_scheduler_running = True
        logger.info(f"✅ Charts-Scheduler gestartet:")
        logger.info(f"   📊 Charts-Update alle {charts_update_hours}h")
        logger.info(f"   🧹 Cleanup alle {cleanup_hours}h")
        logger.info(f"   💰 Preis-Updates alle {price_update_hours}h")
    
    def stop_charts_scheduler(self):
        """Stoppt den Charts-Scheduler"""
        if not self.charts_scheduler_running:
            logger.info("ℹ️ Charts-Scheduler war nicht aktiv")
            return
        
        # Signal zum Stoppen setzen
        self.stop_charts_scheduler_event.set()
        
        # Charts-Jobs entfernen
        charts_jobs = [job for job in schedule.jobs if 'charts' in str(job.job_func)]
        for job in charts_jobs:
            schedule.cancel_job(job)
        
        # Auf Thread-Ende warten
        if self.charts_scheduler_thread and self.charts_scheduler_thread.is_alive():
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
            logger.info(f"✅ Automatisches Charts-Cleanup: {removed} Spiele entfernt")
        except Exception as e:
            logger.error(f"❌ Fehler beim automatischen Charts-Cleanup: {e}")
    
    def _scheduled_charts_price_update(self):
        """Automatisches Preis-Update für Charts-Spiele"""
        try:
            if not hasattr(self, 'price_tracker') or not self.price_tracker:
                logger.warning("⚠️ Kein PriceTracker für Charts-Preisupdate verfügbar")
                return
            
            logger.info("💰 Automatisches Charts-Preisupdate gestartet")
            
            # Alle aktiven Charts-Spiele holen
            active_games = self.get_active_chart_games()
            app_ids = list(set(game['steam_app_id'] for game in active_games))
            
            if not app_ids:
                logger.info("ℹ️ Keine Charts-Spiele für Preisupdate gefunden")
                return
            
            # Preise aktualisieren
            result = self.price_tracker.track_app_prices(app_ids)
            logger.info(f"✅ Charts-Preisupdate: {result['successful']}/{len(app_ids)} Spiele aktualisiert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim automatischen Charts-Preisupdate: {e}")
    
    def get_charts_scheduler_status(self) -> Dict:
        """
        Gibt Charts-Scheduler Status zurück
        
        Returns:
            Dict mit Scheduler-Status
        """
        status = {
            'charts_scheduler_running': self.charts_scheduler_running,
            'charts_jobs_count': len([job for job in schedule.jobs if 'charts' in str(job.job_func)]),
            'next_charts_update': None,
            'next_cleanup': None,
            'next_price_update': None
        }
        
        # Nächste geplante Läufe ermitteln
        charts_jobs = [job for job in schedule.jobs if 'charts' in str(job.job_func)]
        
        for job in charts_jobs:
            job_name = str(job.job_func)
            try:
                next_run = job.next_run.strftime('%Y-%m-%d %H:%M:%S')
                
                if 'charts_update' in job_name:
                    status['next_charts_update'] = next_run
                elif 'cleanup' in job_name:
                    status['next_cleanup'] = next_run
                elif 'price_update' in job_name:
                    status['next_price_update'] = next_run
            except:
                pass
        
        return status
    
    # ========================
    # UTILITY METHODS
    # ========================
    
    def set_price_tracker(self, price_tracker):
        """
        Setzt PriceTracker für automatische Preis-Updates
        
        Args:
            price_tracker: SteamPriceTracker Instanz
        """
        self.price_tracker = price_tracker
        logger.info("✅ PriceTracker für Charts-Integration gesetzt")
    
    def export_charts_data_csv(self, output_file: str = None) -> str:
        """
        Exportiert Charts-Daten als CSV
        
        Args:
            output_file: Ausgabedatei
            
        Returns:
            Pfad zur CSV-Datei
        """
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"exports/charts_data_{timestamp}.csv"
        
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        all_games = self.get_active_chart_games()
        
        if not all_games:
            logger.warning("Keine Charts-Daten für Export verfügbar")
            return None
        
        # CSV Header
        csv_lines = ["steam_app_id,name,chart_type,rank,first_seen,last_seen,days_in_charts"]
        
        # Daten verarbeiten
        for game in all_games:
            # Tage in Charts berechnen
            first_seen = datetime.fromisoformat(game['first_seen'])
            last_seen = datetime.fromisoformat(game['last_seen'])
            days_in_charts = (last_seen - first_seen).days + 1
            
            csv_line = f"{game['steam_app_id']},{game['name']},{game['chart_type']},{game.get('current_rank', 0)},{game['first_seen'][:10]},{game['last_seen'][:10]},{days_in_charts}"
            csv_lines.append(csv_line)
        
        # Datei schreiben
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(csv_lines))
        
        logger.info(f"✅ Charts CSV Export erstellt: {output_file}")
        return output_file