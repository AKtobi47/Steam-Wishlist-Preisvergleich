"""
Enhanced Steam Price Tracker mit Charts Integration
Erweitert den bestehenden SteamPriceTracker um automatisches Charts-Tracking
"""

import threading
import schedule
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class EnhancedSteamPriceTracker:
    """
    Enhanced Steam Price Tracker mit automatischem Charts-Tracking
    Erweitert die bestehende SteamPriceTracker Klasse um Charts-Funktionalität
    """
    
    def __init__(self, db_manager=None, api_key: str = None):
        """
        Initialisiert Enhanced Steam Price Tracker
        
        Args:
            db_manager: DatabaseManager Instanz
            api_key: Steam API Key für Charts
        """
        # Importiere und initialisiere bestehende Komponenten
        from price_tracker import SteamPriceTracker
        from steam_charts_manager import SteamChartsManager
        
        # Basis Price Tracker
        self.price_tracker = SteamPriceTracker(db_manager)
        self.db_manager = self.price_tracker.db_manager
        
        # Charts Manager (falls API Key verfügbar)
        self.charts_manager = None
        self.charts_enabled = False
        
        if api_key:
            try:
                self.charts_manager = SteamChartsManager(api_key, self.db_manager)
                self.charts_manager.set_price_tracker(self.price_tracker)
                self.charts_enabled = True
                logger.info("✅ Enhanced Price Tracker mit Charts-Integration initialisiert")
            except Exception as e:
                logger.warning(f"⚠️ Charts-Integration nicht verfügbar: {e}")
                logger.info("ℹ️ Verwende Standard Price Tracker ohne Charts")
        else:
            logger.info("ℹ️ Kein Steam API Key - Charts-Funktionen deaktiviert")
        
        # Erweiterte Scheduler-Konfiguration
        self.enhanced_scheduler_running = False
        self.enhanced_scheduler_thread = None
        self.stop_enhanced_scheduler_event = threading.Event()
        
        # Charts-spezifische Konfiguration
        self.charts_update_interval = 6  # Stunden
        self.charts_price_update_interval = 4  # Stunden
        self.charts_cleanup_interval = 24  # Stunden
        
        # Initialisiere Charts-Tabellen
        if hasattr(self.db_manager, 'init_charts_tables'):
            self.db_manager.init_charts_tables()
        else:
            logger.warning("⚠️ Charts-Tabellen nicht verfügbar - erweitere database_manager.py")
    
    # ========================
    # CHARTS MANAGEMENT METHODS
    # ========================
    
    def enable_charts_tracking(self, 
                              charts_update_hours: int = 6,
                              price_update_hours: int = 4,
                              cleanup_hours: int = 24) -> bool:
        """
        Aktiviert automatisches Charts-Tracking
        
        Args:
            charts_update_hours: Intervall für Charts-Updates
            price_update_hours: Intervall für Charts-Preis-Updates
            cleanup_hours: Intervall für Charts-Cleanup
            
        Returns:
            True wenn erfolgreich aktiviert
        """
        if not self.charts_enabled:
            logger.error("❌ Charts-Funktionalität nicht verfügbar (kein API Key)")
            return False
        
        try:
            # Konfiguration setzen
            self.charts_update_interval = charts_update_hours
            self.charts_price_update_interval = price_update_hours
            self.charts_cleanup_interval = cleanup_hours
            
            # Charts-Scheduler starten
            self.charts_manager.start_charts_scheduler(
                charts_update_hours=charts_update_hours,
                cleanup_hours=cleanup_hours,
                price_update_hours=price_update_hours
            )
            
            logger.info("✅ Charts-Tracking aktiviert")
            logger.info(f"   📊 Charts-Updates: alle {charts_update_hours}h")
            logger.info(f"   💰 Preis-Updates: alle {price_update_hours}h")
            logger.info(f"   🧹 Cleanup: alle {cleanup_hours}h")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktivieren des Charts-Trackings: {e}")
            return False
    
    def disable_charts_tracking(self) -> bool:
        """
        Deaktiviert Charts-Tracking
        
        Returns:
            True wenn erfolgreich deaktiviert
        """
        if not self.charts_enabled:
            logger.info("ℹ️ Charts-Tracking war nicht aktiv")
            return True
        
        try:
            self.charts_manager.stop_charts_scheduler()
            logger.info("⏹️ Charts-Tracking deaktiviert")
            return True
        except Exception as e:
            logger.error(f"❌ Fehler beim Deaktivieren des Charts-Trackings: {e}")
            return False
    
    def update_charts_now(self, chart_types: List[str] = None) -> Dict:
        """
        Führt sofortiges Charts-Update durch
        
        Args:
            chart_types: Liste der zu aktualisierenden Chart-Typen
            
        Returns:
            Update-Statistiken
        """
        if not self.charts_enabled:
            return {'success': False, 'error': 'Charts not enabled'}
        
        try:
            logger.info("🔄 Starte manuelles Charts-Update...")
            
            # Standard-Counts für Charts
            counts = {
                'most_played': 100,
                'top_releases': 50,
                'best_sellers': 100,
                'weekly_top_sellers': 75
            }
            
            # Nur spezifische Chart-Typen wenn angegeben
            if chart_types:
                counts = {ct: counts.get(ct, 50) for ct in chart_types if ct in counts}
            
            result = self.charts_manager.update_all_charts(counts)
            
            logger.info(f"✅ Manuelles Charts-Update abgeschlossen:")
            logger.info(f"   📊 {result['total_games_found']} Spiele gefunden")
            logger.info(f"   ➕ {result['new_games_added']} neue Spiele")
            logger.info(f"   🔄 {result['existing_games_updated']} aktualisiert")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Fehler beim manuellen Charts-Update: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_charts_prices_now(self, chart_type: str = None) -> Dict:
        """
        Führt sofortiges Preis-Update für Charts-Spiele durch
        
        Args:
            chart_type: Optionale Filterung nach Chart-Typ
            
        Returns:
            Update-Statistiken
        """
        try:
            logger.info("💰 Starte manuelles Charts-Preisupdate...")
            
            # Charts-Spiele holen die Updates benötigen
            if hasattr(self.db_manager, 'get_chart_games_needing_price_update'):
                pending_games = self.db_manager.get_chart_games_needing_price_update(hours_threshold=0)
            else:
                # Fallback: alle aktiven Charts-Spiele
                if hasattr(self.db_manager, 'get_active_chart_games'):
                    pending_games = self.db_manager.get_active_chart_games(chart_type)
                else:
                    logger.error("❌ Charts-Datenbankfunktionen nicht verfügbar")
                    return {'success': False, 'error': 'Database functions not available'}
            
            if not pending_games:
                logger.info("✅ Alle Charts-Spiele haben aktuelle Preise")
                return {'success': True, 'total_updated': 0, 'message': 'All prices current'}
            
            # App IDs extrahieren
            app_ids = list(set(game['steam_app_id'] for game in pending_games))
            
            logger.info(f"🔄 Aktualisiere Preise für {len(app_ids)} Charts-Spiele...")
            
            # Standard Preis-Tracking verwenden
            result = self.price_tracker.track_app_prices(app_ids)
            
            # Für Charts-Spiele auch in Charts-Tabelle speichern
            if hasattr(self.db_manager, 'save_charts_price_snapshot'):
                charts_saved = 0
                for app_id in app_ids:
                    if app_id in [aid for aid in app_ids if result['successful'] > 0]:
                        # Hole aktuelle Preisdaten
                        latest_prices = self.price_tracker.get_latest_prices(app_id)
                        if latest_prices:
                            # Chart-Typen für dieses Spiel ermitteln
                            app_chart_types = []
                            for game in pending_games:
                                if game['steam_app_id'] == app_id:
                                    app_chart_types.append(game.get('chart_type', 'unknown'))
                            
                            # Preise in Charts-Format konvertieren
                            charts_prices = self._convert_prices_for_charts(latest_prices)
                            
                            if self.db_manager.save_charts_price_snapshot(
                                app_id,
                                latest_prices.get('game_title', f'Game {app_id}'),
                                charts_prices,
                                list(set(app_chart_types))
                            ):
                                charts_saved += 1
                
                logger.info(f"📊 {charts_saved} Charts-Preis-Snapshots gespeichert")
            
            logger.info(f"✅ Charts-Preisupdate abgeschlossen:")
            logger.info(f"   💰 {result['successful']}/{len(app_ids)} Spiele erfolgreich")
            
            return {
                'success': True,
                'total_games': len(app_ids),
                'successful': result['successful'],
                'failed': result['failed'],
                'errors': result.get('errors', [])
            }
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Charts-Preisupdate: {e}")
            return {'success': False, 'error': str(e)}
    
    def _convert_prices_for_charts(self, latest_prices: Dict) -> Dict:
        """
        Konvertiert Preisdaten in Charts-Format
        
        Args:
            latest_prices: Preisdaten aus price_snapshots
            
        Returns:
            Preisdaten in Charts-Format
        """
        stores = ['Steam', 'GreenManGaming', 'GOG', 'HumbleStore', 'Fanatical', 'GamesPlanet']
        store_prefixes = ['steam', 'greenmangaming', 'gog', 'humblestore', 'fanatical', 'gamesplanet']
        
        charts_prices = {}
        
        for store, prefix in zip(stores, store_prefixes):
            if latest_prices.get(f'{prefix}_available'):
                charts_prices[store] = {
                    'price': latest_prices.get(f'{prefix}_price'),
                    'original_price': latest_prices.get(f'{prefix}_original_price'),
                    'discount_percent': latest_prices.get(f'{prefix}_discount_percent', 0),
                    'available': True
                }
            else:
                charts_prices[store] = {
                    'price': None,
                    'original_price': None,
                    'discount_percent': 0,
                    'available': False
                }
        
        return charts_prices
    
    # ========================
    # ENHANCED STATISTICS
    # ========================
    
    def get_enhanced_statistics(self) -> Dict:
        """
        Gibt erweiterte Statistiken mit Charts-Daten zurück
        
        Returns:
            Dict mit erweiterten Statistiken
        """
        # Basis-Statistiken
        stats = self.price_tracker.get_statistics()
        
        # Charts-Statistiken hinzufügen
        if self.charts_enabled and hasattr(self.db_manager, 'get_charts_statistics'):
            charts_stats = self.db_manager.get_charts_statistics()
            stats['charts'] = charts_stats
            
            # Charts-Scheduler Status
            if self.charts_manager:
                scheduler_status = self.charts_manager.get_charts_scheduler_status()
                stats['charts']['scheduler_status'] = scheduler_status
        else:
            stats['charts'] = {
                'enabled': False,
                'message': 'Charts-Funktionalität nicht verfügbar'
            }
        
        return stats
    
    def get_charts_overview(self) -> Dict:
        """
        Gibt Charts-Übersicht zurück
        
        Returns:
            Dict mit Charts-Übersicht
        """
        if not self.charts_enabled:
            return {'enabled': False, 'message': 'Charts not enabled'}
        
        try:
            overview = {
                'enabled': True,
                'chart_types': {},
                'scheduler_status': {},
                'recent_activity': {}
            }
            
            # Chart-Typen Übersicht
            if hasattr(self.charts_manager, 'CHART_TYPES'):
                for chart_type, description in self.charts_manager.CHART_TYPES.items():
                    if hasattr(self.db_manager, 'get_active_chart_games'):
                        games = self.db_manager.get_active_chart_games(chart_type)
                        overview['chart_types'][chart_type] = {
                            'description': description,
                            'active_games': len(games),
                            'top_games': [
                                {'name': game['name'], 'rank': game.get('current_rank', 0)}
                                for game in games[:5]
                            ]
                        }
            
            # Scheduler Status
            if self.charts_manager:
                overview['scheduler_status'] = self.charts_manager.get_charts_scheduler_status()
            
            # Letzte Aktivitäten
            if hasattr(self.db_manager, 'get_charts_statistics'):
                charts_stats = self.db_manager.get_charts_statistics()
                overview['recent_activity'] = {
                    'total_active_games': charts_stats.get('total_active_charts_games', 0),
                    'unique_apps': charts_stats.get('unique_apps_in_charts', 0),
                    'price_updates_today': charts_stats.get('apps_with_price_updates_today', 0),
                    'average_days_in_charts': charts_stats.get('average_days_in_charts', 0)
                }
            
            return overview
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der Charts-Übersicht: {e}")
            return {'enabled': True, 'error': str(e)}
    
    # ========================
    # ENHANCED DEALS
    # ========================
    
    def get_best_charts_deals(self, limit: int = 15, chart_type: str = None) -> List[Dict]:
        """
        Gibt beste Deals für Charts-Spiele zurück
        
        Args:
            limit: Anzahl Deals
            chart_type: Optionale Filterung nach Chart-Typ
            
        Returns:
            Liste der besten Charts-Deals
        """
        if not self.charts_enabled:
            return []
        
        try:
            if hasattr(self.db_manager, 'get_charts_best_deals'):
                return self.db_manager.get_charts_best_deals(limit, chart_type)
            else:
                logger.warning("⚠️ Charts-Deals Funktion nicht verfügbar")
                return []
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Charts-Deals: {e}")
            return []
    
    def get_trending_price_drops(self, hours_back: int = 24, min_discount: int = 20) -> List[Dict]:
        """
        Gibt Charts-Spiele mit neuen Preissenkungen zurück
        
        Args:
            hours_back: Stunden zurückblicken
            min_discount: Mindestrabatt in Prozent
            
        Returns:
            Liste der Charts-Spiele mit neuen Deals
        """
        if not self.charts_enabled:
            return []
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            # Diese Funktionalität würde eine komplexere Datenbankabfrage erfordern
            # die Preisänderungen über Zeit verfolgt - vereinfacht implementiert
            
            trending_deals = []
            
            if hasattr(self.db_manager, 'get_active_chart_games'):
                active_games = self.db_manager.get_active_chart_games()
                
                for game in active_games[:50]:  # Limitiere für Performance
                    app_id = game['steam_app_id']
                    
                    # Aktuelle Preise holen
                    if hasattr(self.db_manager, 'get_charts_price_history'):
                        recent_prices = self.db_manager.get_charts_price_history(app_id, days_back=2)
                        
                        if len(recent_prices) >= 2:
                            latest = recent_prices[0]
                            previous = recent_prices[-1]
                            
                            # Prüfe auf neue Rabatte
                            stores = ['steam', 'greenmangaming', 'gog', 'humblestore', 'fanatical', 'gamesplanet']
                            
                            for store in stores:
                                latest_discount = latest.get(f'{store}_discount_percent', 0)
                                previous_discount = previous.get(f'{store}_discount_percent', 0)
                                
                                if (latest_discount >= min_discount and 
                                    latest_discount > previous_discount and
                                    latest.get(f'{store}_available')):
                                    
                                    trending_deals.append({
                                        'steam_app_id': app_id,
                                        'game_title': latest.get('game_title', game['name']),
                                        'chart_type': game['chart_type'],
                                        'store': store.title(),
                                        'current_price': latest.get(f'{store}_price'),
                                        'discount_percent': latest_discount,
                                        'price_drop_detected': True,
                                        'timestamp': latest['timestamp']
                                    })
                                    break
            
            # Nach Rabatt sortieren
            trending_deals.sort(key=lambda x: x['discount_percent'], reverse=True)
            
            return trending_deals[:20]
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Trending Price Drops: {e}")
            return []
    
    # ========================
    # DELEGATE METHODS
    # ========================
    
    # Alle Standard-Methoden an den basis price_tracker delegieren
    def __getattr__(self, name):
        """Delegiert unbekannte Methoden an den basis price_tracker"""
        if hasattr(self.price_tracker, name):
            return getattr(self.price_tracker, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    # Explizit wichtige Methoden delegieren für bessere IDE-Unterstützung
    def add_app_to_tracking(self, steam_app_id: str, name: str = None) -> bool:
        """Fügt App zum normalen Tracking hinzu"""
        return self.price_tracker.add_app_to_tracking(steam_app_id, name)
    
    def track_app_prices(self, steam_app_ids: List[str]) -> Dict:
        """Trackt Preise für Apps"""
        return self.price_tracker.track_app_prices(steam_app_ids)
    
    def get_tracked_apps(self) -> List[Dict]:
        """Gibt getrackte Apps zurück"""
        return self.price_tracker.get_tracked_apps()
    
    def get_current_best_deals(self, limit: int = 10) -> List[Dict]:
        """Gibt beste normale Deals zurück"""
        return self.price_tracker.get_current_best_deals(limit)
    
    def start_scheduler(self, interval_hours: int = 6):
        """Startet normalen Preis-Scheduler"""
        return self.price_tracker.start_scheduler(interval_hours)
    
    def stop_scheduler(self):
        """Stoppt normalen Preis-Scheduler"""
        return self.price_tracker.stop_scheduler()
    
    def get_scheduler_status(self) -> Dict:
        """Gibt Status des normalen Schedulers zurück"""
        return self.price_tracker.get_scheduler_status()


# ========================
# CONVENIENCE FUNCTIONS
# ========================

def create_enhanced_tracker(api_key: str = None, db_path: str = "steam_price_tracker.db"):
    """
    Erstellt Enhanced Price Tracker mit automatischer Konfiguration
    
    Args:
        api_key: Steam API Key (optional, lädt aus .env)
        db_path: Pfad zur Datenbank
        
    Returns:
        EnhancedSteamPriceTracker Instanz
    """
    if api_key is None:
        from steam_wishlist_manager import load_api_key_from_env
        api_key = load_api_key_from_env()
    
    # Database Manager mit Charts-Erweiterungen
    from database_manager import DatabaseManager
    db_manager = DatabaseManager(db_path)
    
    # Enhanced Tracker erstellen
    tracker = EnhancedSteamPriceTracker(db_manager, api_key)
    
    return tracker

def setup_full_automation(tracker: EnhancedSteamPriceTracker,
                         normal_interval: int = 6,
                         charts_interval: int = 6,
                         charts_price_interval: int = 4) -> bool:
    """
    Richtet vollautomatisches Tracking ein
    
    Args:
        tracker: Enhanced Tracker Instanz
        normal_interval: Intervall für normale Apps (Stunden)
        charts_interval: Intervall für Charts-Updates (Stunden)
        charts_price_interval: Intervall für Charts-Preise (Stunden)
        
    Returns:
        True wenn erfolgreich eingerichtet
    """
    try:
        # Normales Tracking starten
        tracker.start_scheduler(normal_interval)
        logger.info(f"✅ Normales Tracking: alle {normal_interval}h")
        
        # Charts-Tracking starten (falls verfügbar)
        if tracker.charts_enabled:
            tracker.enable_charts_tracking(
                charts_update_hours=charts_interval,
                price_update_hours=charts_price_interval,
                cleanup_hours=24
            )
            logger.info(f"✅ Charts-Tracking: Updates alle {charts_interval}h, Preise alle {charts_price_interval}h")
        
        logger.info("🚀 Vollautomatisches Tracking aktiviert!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Setup der Automatisierung: {e}")
        return False