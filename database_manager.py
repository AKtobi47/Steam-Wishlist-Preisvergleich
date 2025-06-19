#!/usr/bin/env python3
"""
Database Manager für Steam Price Tracker
Erweiterte Version mit Charts-Support und detaillierten Statistiken
Unterstützt vollständige Charts-Integration und erweiterte Datenbank-Features
"""

import sqlite3
import threading
import json
import shutil
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import logging

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Erweiterte Database Manager Klasse für Steam Price Tracker
    Mit vollständigem Charts-Support und erweiterten Funktionen
    """
    
    def __init__(self, db_path: str = "steam_price_tracker.db"):
        """
        Initialisiert Database Manager
        
        Args:
            db_path: Pfad zur SQLite-Datenbank
        """
        self.db_path = Path(db_path)
        self.lock = threading.Lock()
        
        # Datenbank initialisieren
        self._init_database()
        
        # Charts-Tabellen prüfen und initialisieren
        if self.check_charts_tables():
            logger.info("✅ Charts-Tabellen verfügbar")
        else:
            logger.warning("⚠️ Charts-Tabellen fehlen - führe init_charts_tables_enhanced() aus")
            self.init_charts_tables_enhanced()
        
        logger.info(f"✅ Database Manager initialisiert: {self.db_path}")
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Erstellt neue Datenbankverbindung mit optimierten Einstellungen
        
        Returns:
            SQLite-Verbindung
        """
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        
        # Performance-Optimierungen
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA mmap_size = 268435456")  # 256MB
        
        return conn
    
    def _init_database(self):
        """Initialisiert die Haupt-Datenbank-Tabellen"""
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Haupt-Tracking-Tabelle
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tracked_apps (
                        steam_app_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_price_update TIMESTAMP,
                        active BOOLEAN DEFAULT 1,
                        source TEXT DEFAULT 'manual'
                    )
                ''')
                
                # Preis-Snapshots Tabelle (erweitert)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS price_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        steam_app_id TEXT NOT NULL,
                        game_title TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        
                        -- Steam Store
                        steam_price REAL,
                        steam_original_price REAL,
                        steam_discount_percent INTEGER DEFAULT 0,
                        steam_available BOOLEAN DEFAULT 0,
                        
                        -- GreenManGaming
                        greenmangaming_price REAL,
                        greenmangaming_original_price REAL,
                        greenmangaming_discount_percent INTEGER DEFAULT 0,
                        greenmangaming_available BOOLEAN DEFAULT 0,
                        
                        -- GOG
                        gog_price REAL,
                        gog_original_price REAL,
                        gog_discount_percent INTEGER DEFAULT 0,
                        gog_available BOOLEAN DEFAULT 0,
                        
                        -- HumbleStore
                        humblestore_price REAL,
                        humblestore_original_price REAL,
                        humblestore_discount_percent INTEGER DEFAULT 0,
                        humblestore_available BOOLEAN DEFAULT 0,
                        
                        -- Fanatical
                        fanatical_price REAL,
                        fanatical_original_price REAL,
                        fanatical_discount_percent INTEGER DEFAULT 0,
                        fanatical_available BOOLEAN DEFAULT 0,
                        
                        -- GamesPlanet
                        gamesplanet_price REAL,
                        gamesplanet_original_price REAL,
                        gamesplanet_discount_percent INTEGER DEFAULT 0,
                        gamesplanet_available BOOLEAN DEFAULT 0,
                        
                        FOREIGN KEY (steam_app_id) REFERENCES tracked_apps (steam_app_id)
                    )
                ''')
                
                # Indizes für Performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracked_apps_active ON tracked_apps(active)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracked_apps_last_update ON tracked_apps(last_price_update)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_snapshots_app_id ON price_snapshots(steam_app_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_snapshots_timestamp ON price_snapshots(timestamp)')
                
                conn.commit()
    
    # =====================================================================
    # ENHANCED CHARTS-TABELLEN INTEGRATION
    # =====================================================================
    
    def init_charts_tables_enhanced(self):
        """
        Erweiterte Initialisierung der Charts-Tabellen
        Diese Methode ersetzt/erweitert die bestehende init_charts_tables-Methode
        """
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                try:
                    # Haupt-Charts-Tracking Tabelle (erweitert)
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS steam_charts_tracking (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            steam_app_id TEXT NOT NULL,
                            name TEXT NOT NULL,
                            chart_type TEXT NOT NULL,
                            current_rank INTEGER,
                            best_rank INTEGER,
                            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            days_in_charts INTEGER DEFAULT 1,
                            rank_trend TEXT DEFAULT 'stable',
                            popularity_score REAL DEFAULT 0.0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(steam_app_id, chart_type)
                        )
                    ''')
                    
                    # Charts-Preis-Historie (für Charts-spezifische Preise)
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS steam_charts_prices (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            steam_app_id TEXT NOT NULL,
                            chart_type TEXT NOT NULL,
                            current_price REAL,
                            original_price REAL,
                            discount_percent INTEGER DEFAULT 0,
                            store TEXT DEFAULT 'Steam',
                            deal_url TEXT,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (steam_app_id, chart_type) 
                            REFERENCES steam_charts_tracking (steam_app_id, chart_type)
                        )
                    ''')
                    
                    # Charts-Rank-Historie (für Trend-Analyse)
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS steam_charts_rank_history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            steam_app_id TEXT NOT NULL,
                            chart_type TEXT NOT NULL,
                            rank_position INTEGER NOT NULL,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (steam_app_id, chart_type) 
                            REFERENCES steam_charts_tracking (steam_app_id, chart_type)
                        )
                    ''')
                    
                    # Charts-Statistiken (für Performance-Tracking)
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS steam_charts_statistics (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            chart_type TEXT NOT NULL,
                            total_games INTEGER DEFAULT 0,
                            new_games INTEGER DEFAULT 0,
                            updated_games INTEGER DEFAULT 0,
                            update_duration REAL DEFAULT 0.0,
                            api_calls INTEGER DEFAULT 0,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    
                    # Charts-Konfiguration
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS steam_charts_config (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            key TEXT UNIQUE NOT NULL,
                            value TEXT NOT NULL,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    
                    # Enhanced Indizes für Charts-Performance
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_tracking_chart_type ON steam_charts_tracking(chart_type)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_tracking_rank ON steam_charts_tracking(current_rank)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_tracking_last_seen ON steam_charts_tracking(last_seen)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_prices_app_chart ON steam_charts_prices(steam_app_id, chart_type)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_prices_timestamp ON steam_charts_prices(timestamp)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_rank_history_app_chart ON steam_charts_rank_history(steam_app_id, chart_type)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_statistics_chart_type ON steam_charts_statistics(chart_type)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_statistics_timestamp ON steam_charts_statistics(timestamp)')
                    
                    # Enhanced Views für Charts-Analyse
                    cursor.execute('''
                        CREATE VIEW IF NOT EXISTS charts_summary AS
                        SELECT 
                            chart_type,
                            COUNT(*) as total_games,
                            COUNT(CASE WHEN current_rank <= 10 THEN 1 END) as top_10_games,
                            AVG(current_rank) as avg_rank,
                            MIN(current_rank) as best_rank,
                            MAX(last_seen) as last_update
                        FROM steam_charts_tracking
                        GROUP BY chart_type
                    ''')
                    
                    cursor.execute('''
                        CREATE VIEW IF NOT EXISTS charts_trending AS
                        SELECT 
                            sct.*,
                            CASE 
                                WHEN sct.current_rank < sct.best_rank THEN 'rising'
                                WHEN sct.current_rank > sct.best_rank THEN 'falling'
                                ELSE 'stable'
                            END as trend_direction
                        FROM steam_charts_tracking sct
                        WHERE sct.last_seen >= datetime('now', '-24 hours')
                    ''')
                    
                    conn.commit()
                    logger.info("✅ Enhanced Charts-Tabellen erfolgreich erstellt")
                    
                except Exception as e:
                    logger.error(f"❌ Fehler beim Erstellen der Charts-Tabellen: {e}")
                    conn.rollback()
                    raise
    
    def check_charts_tables(self) -> bool:
        """
        Prüft ob alle Charts-Tabellen existieren
        
        Returns:
            True wenn alle Charts-Tabellen vorhanden sind
        """
        try:
            required_tables = [
                'steam_charts_tracking',
                'steam_charts_prices', 
                'steam_charts_rank_history',
                'steam_charts_statistics',
                'steam_charts_config'
            ]
            
            required_views = [
                'charts_summary',
                'charts_trending'
            ]
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Tabellen prüfen
                for table in required_tables:
                    cursor.execute("""
                        SELECT COUNT(*) as count 
                        FROM sqlite_master 
                        WHERE type='table' AND name=?
                    """, (table,))
                    
                    if cursor.fetchone()['count'] == 0:
                        logger.warning(f"❌ Charts-Tabelle fehlt: {table}")
                        return False
                
                # Views prüfen
                for view in required_views:
                    cursor.execute("""
                        SELECT COUNT(*) as count 
                        FROM sqlite_master 
                        WHERE type='view' AND name=?
                    """, (view,))
                    
                    if cursor.fetchone()['count'] == 0:
                        logger.warning(f"❌ Charts-View fehlt: {view}")
                        return False
                
                logger.debug("✅ Alle Charts-Tabellen und Views vorhanden")
                return True
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Prüfen der Charts-Tabellen: {e}")
            return False
    
    def get_charts_database_statistics(self) -> Dict:
        """
        Gibt detaillierte Statistiken der Charts-Datenbank zurück
        
        Returns:
            Dict mit Charts-Datenbankstatistiken
        """
        try:
            stats = {
                'tables': {},
                'performance': {},
                'data_quality': {},
                'storage': {}
            }
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Tabellen-Statistiken
                tables = [
                    'steam_charts_tracking',
                    'steam_charts_prices',
                    'steam_charts_rank_history', 
                    'steam_charts_statistics',
                    'steam_charts_config'
                ]
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = cursor.fetchone()['count']
                    stats['tables'][table] = count
                
                # Performance-Statistiken
                cursor.execute("""
                    SELECT 
                        AVG(update_duration) as avg_update_time,
                        MAX(update_duration) as max_update_time,
                        SUM(api_calls) as total_api_calls,
                        COUNT(*) as total_updates
                    FROM steam_charts_statistics
                    WHERE timestamp >= datetime('now', '-30 days')
                """)
                
                perf_row = cursor.fetchone()
                if perf_row:
                    stats['performance'] = {
                        'avg_update_time': perf_row['avg_update_time'] or 0,
                        'max_update_time': perf_row['max_update_time'] or 0,
                        'total_api_calls': perf_row['total_api_calls'] or 0,
                        'total_updates': perf_row['total_updates'] or 0
                    }
                
                # Datenqualität
                cursor.execute("""
                    SELECT 
                        COUNT(CASE WHEN current_rank IS NULL THEN 1 END) as missing_ranks,
                        COUNT(CASE WHEN name LIKE 'App %' THEN 1 END) as generic_names,
                        COUNT(*) as total_entries
                    FROM steam_charts_tracking
                """)
                
                quality_row = cursor.fetchone()
                if quality_row:
                    stats['data_quality'] = {
                        'missing_ranks': quality_row['missing_ranks'],
                        'generic_names': quality_row['generic_names'],
                        'total_entries': quality_row['total_entries'],
                        'data_completeness': (1 - quality_row['missing_ranks'] / max(quality_row['total_entries'], 1)) * 100
                    }
                
                # Storage-Statistiken
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()['size']
                stats['storage']['database_size_bytes'] = db_size
                stats['storage']['database_size_mb'] = round(db_size / (1024 * 1024), 2)
                
                return stats
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Charts-Statistiken: {e}")
            return {'error': str(e)}
    
    def cleanup_orphaned_chart_data(self) -> int:
        """
        Bereinigt verwaiste Charts-Daten
        
        Returns:
            Anzahl bereinigter Einträge
        """
        try:
            cleaned_count = 0
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Verwaiste Preis-Einträge
                cursor.execute("""
                    DELETE FROM steam_charts_prices 
                    WHERE (steam_app_id, chart_type) NOT IN (
                        SELECT steam_app_id, chart_type 
                        FROM steam_charts_tracking
                    )
                """)
                cleaned_count += cursor.rowcount
                
                # Verwaiste Rank-Historie
                cursor.execute("""
                    DELETE FROM steam_charts_rank_history 
                    WHERE (steam_app_id, chart_type) NOT IN (
                        SELECT steam_app_id, chart_type 
                        FROM steam_charts_tracking
                    )
                """)
                cleaned_count += cursor.rowcount
                
                conn.commit()
                
                if cleaned_count > 0:
                    logger.info(f"🧹 {cleaned_count} verwaiste Charts-Einträge bereinigt")
                
                return cleaned_count
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Bereinigen verwaister Charts-Daten: {e}")
            return 0
    
    def optimize_charts_database(self):
        """Optimiert die Charts-Datenbank für bessere Performance"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                logger.info("🔧 Optimiere Charts-Datenbank...")
                
                # Statistiken aktualisieren
                cursor.execute("ANALYZE steam_charts_tracking")
                cursor.execute("ANALYZE steam_charts_prices")
                cursor.execute("ANALYZE steam_charts_rank_history")
                
                # Vacuum für Charts-Tabellen
                conn.execute("VACUUM")
                
                logger.info("✅ Charts-Datenbank optimiert")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Optimieren der Charts-Datenbank: {e}")
    
    def get_charts_data_export(self, chart_type: str = None, days: int = 7) -> List[Dict]:
        """
        Exportiert Charts-Daten für Analyse
        
        Args:
            chart_type: Spezifischer Chart-Typ (optional)
            days: Anzahl Tage zurück (Standard: 7)
            
        Returns:
            Liste mit Charts-Daten
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT 
                        sct.steam_app_id,
                        sct.name,
                        sct.chart_type,
                        sct.current_rank,
                        sct.best_rank,
                        sct.days_in_charts,
                        sct.rank_trend,
                        scp.current_price,
                        scp.discount_percent,
                        sct.last_seen
                    FROM steam_charts_tracking sct
                    LEFT JOIN steam_charts_prices scp ON 
                        sct.steam_app_id = scp.steam_app_id AND 
                        sct.chart_type = scp.chart_type AND
                        scp.timestamp >= datetime('now', '-1 day')
                    WHERE sct.last_seen >= datetime('now', '-{} days')
                """.format(days)
                
                params = []
                if chart_type:
                    query += " AND sct.chart_type = ?"
                    params.append(chart_type)
                
                query += " ORDER BY sct.chart_type, sct.current_rank"
                
                cursor.execute(query, params)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Exportieren der Charts-Daten: {e}")
            return []
    
    def backup_charts_data(self) -> Optional[str]:
        """
        Erstellt Backup der Charts-Daten
        
        Returns:
            Pfad zum Backup-File oder None
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)
            
            backup_file = backup_dir / f"charts_backup_{timestamp}.json"
            
            # Charts-Daten sammeln
            charts_data = {
                'timestamp': timestamp,
                'tracking_data': [],
                'price_data': [],
                'statistics': self.get_charts_database_statistics()
            }
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Tracking-Daten
                cursor.execute("SELECT * FROM steam_charts_tracking")
                charts_data['tracking_data'] = [dict(row) for row in cursor.fetchall()]
                
                # Preis-Daten (letzte 30 Tage)
                cursor.execute("""
                    SELECT * FROM steam_charts_prices 
                    WHERE timestamp >= datetime('now', '-30 days')
                """)
                charts_data['price_data'] = [dict(row) for row in cursor.fetchall()]
            
            # Backup speichern
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(charts_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"💾 Charts-Backup erstellt: {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des Charts-Backups: {e}")
            return None
    
    def restore_charts_data(self, backup_file: str) -> bool:
        """
        Stellt Charts-Daten aus Backup wieder her
        
        Args:
            backup_file: Pfad zum Backup-File
            
        Returns:
            True wenn erfolgreich wiederhergestellt
        """
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                logger.error(f"❌ Backup-Datei nicht gefunden: {backup_file}")
                return False
            
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Tracking-Daten wiederherstellen
                for entry in backup_data.get('tracking_data', []):
                    cursor.execute("""
                        INSERT OR REPLACE INTO steam_charts_tracking 
                        (steam_app_id, name, chart_type, current_rank, best_rank, 
                         first_seen, last_seen, days_in_charts, rank_trend, popularity_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry['steam_app_id'],
                        entry['name'],
                        entry['chart_type'],
                        entry['current_rank'],
                        entry['best_rank'],
                        entry['first_seen'],
                        entry['last_seen'],
                        entry['days_in_charts'],
                        entry['rank_trend'],
                        entry['popularity_score']
                    ))
                
                restored_count = 0
                
                # Preis-Daten wiederherstellen
                for entry in backup_data.get('price_data', []):
                    try:
                        cursor.execute("""
                            INSERT OR IGNORE INTO steam_charts_prices 
                            (steam_app_id, chart_type, current_price, original_price, 
                             discount_percent, store, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            entry['steam_app_id'],
                            entry['chart_type'],
                            entry['current_price'],
                            entry['original_price'],
                            entry['discount_percent'],
                            entry['store'],
                            entry['timestamp']
                        ))
                        
                        restored_count += 1
                    except Exception as e:
                        logger.debug(f"Fehler beim Wiederherstellen eines Preis-Eintrags: {e}")
                
                conn.commit()
                
                logger.info(f"✅ Charts-Daten erfolgreich wiederhergestellt: {restored_count} Einträge")
                return True
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Wiederherstellen der Charts-Daten: {e}")
            return False
    
    # =====================================================================
    # STANDARD DATABASE FUNKTIONEN (ERWEITERT)
    # =====================================================================
    
    def add_tracked_app(self, app_id: str, name: str, source: str = "manual") -> bool:
        """
        Fügt eine App zum Tracking hinzu
        
        Args:
            app_id: Steam App ID
            name: Name der App
            source: Quelle der App (manual, wishlist, charts)
            
        Returns:
            True wenn erfolgreich hinzugefügt
        """
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        INSERT OR IGNORE INTO tracked_apps 
                        (steam_app_id, name, source, added_at)
                        VALUES (?, ?, ?, ?)
                    """, (app_id, name, source, datetime.now()))
                    
                    success = cursor.rowcount > 0
                    conn.commit()
                    
                    if success:
                        logger.info(f"✅ App hinzugefügt: {name} ({app_id})")
                    else:
                        logger.debug(f"App bereits vorhanden: {app_id}")
                    
                    return True  # Immer True, da INSERT OR IGNORE verwendet wird
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Hinzufügen der App {app_id}: {e}")
            return False
    
    def get_tracked_apps(self, active_only: bool = True, limit: int = None) -> List[Dict]:
        """
        Gibt alle getrackte Apps zurück
        
        Args:
            active_only: Nur aktive Apps
            limit: Maximum Anzahl Apps
            
        Returns:
            Liste mit App-Informationen
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM tracked_apps"
                params = []
                
                if active_only:
                    query += " WHERE active = 1"
                
                query += " ORDER BY added_at DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor.execute(query, params)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der getrackte Apps: {e}")
            return []
    
    def save_price_snapshot(self, price_data: Dict) -> bool:
        """
        Speichert einen Preis-Snapshot
        
        Args:
            price_data: Dictionary mit Preisinformationen
            
        Returns:
            True wenn erfolgreich gespeichert
        """
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Alle Store-Preise aus price_data extrahieren
                    stores = ['steam', 'greenmangaming', 'gog', 'humblestore', 'fanatical', 'gamesplanet']
                    
                    # SQL und Parameter für INSERT vorbereiten
                    columns = ['steam_app_id', 'game_title', 'timestamp']
                    values = [price_data['steam_app_id'], price_data['game_title'], price_data['timestamp']]
                    placeholders = ['?', '?', '?']
                    
                    for store in stores:
                        for field in ['price', 'original_price', 'discount_percent', 'available']:
                            key = f"{store}_{field}"
                            columns.append(key)
                            values.append(price_data.get(key))
                            placeholders.append('?')
                    
                    query = f"""
                        INSERT INTO price_snapshots ({', '.join(columns)})
                        VALUES ({', '.join(placeholders)})
                    """
                    
                    cursor.execute(query, values)
                    
                    # Last update timestamp in tracked_apps aktualisieren
                    cursor.execute("""
                        UPDATE tracked_apps 
                        SET last_price_update = ? 
                        WHERE steam_app_id = ?
                    """, (datetime.now(), price_data['steam_app_id']))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern des Preis-Snapshots: {e}")
            return False
    
    def get_latest_prices(self, app_id: str) -> Optional[Dict]:
        """
        Gibt die neuesten Preise für eine App zurück
        
        Args:
            app_id: Steam App ID
            
        Returns:
            Dictionary mit neuesten Preisinformationen oder None
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM price_snapshots 
                    WHERE steam_app_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """, (app_id,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der neuesten Preise für {app_id}: {e}")
            return None
    
    def get_best_deals(self, min_discount: int = 20, limit: int = 20) -> List[Dict]:
        """
        Findet die besten aktuellen Deals
        
        Args:
            min_discount: Mindest-Rabatt in Prozent
            limit: Maximum Anzahl Deals
            
        Returns:
            Liste der besten Deals
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Alle Stores mit Rabatten durchsuchen
                stores = ['steam', 'greenmangaming', 'gog', 'humblestore', 'fanatical', 'gamesplanet']
                
                union_queries = []
                for store in stores:
                    union_queries.append(f"""
                        SELECT 
                            steam_app_id,
                            game_title,
                            '{store}' as store,
                            {store}_price as price,
                            {store}_original_price as original_price,
                            {store}_discount_percent as discount_percent,
                            timestamp
                        FROM price_snapshots 
                        WHERE {store}_discount_percent >= ? 
                        AND {store}_available = 1
                        AND {store}_price IS NOT NULL
                    """)
                
                query = f"""
                    SELECT * FROM (
                        {' UNION ALL '.join(union_queries)}
                    ) deals
                    WHERE deals.steam_app_id IN (
                        SELECT ps.steam_app_id FROM price_snapshots ps
                        INNER JOIN tracked_apps ta ON ps.steam_app_id = ta.steam_app_id
                        WHERE ta.active = 1
                        GROUP BY ps.steam_app_id
                        HAVING ps.timestamp = MAX(ps.timestamp)
                    )
                    ORDER BY discount_percent DESC, price ASC
                    LIMIT ?
                """
                
                params = [min_discount] * len(stores) + [limit]
                cursor.execute(query, params)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der besten Deals: {e}")
            return []
    
    def get_apps_needing_update(self, hours_threshold: int = 6) -> List[Dict]:
        """
        Gibt Apps zurück die ein Update benötigen
        
        Args:
            hours_threshold: Apps älter als X Stunden
            
        Returns:
            Liste mit Apps die Updates benötigen
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT steam_app_id, name, last_price_update
                    FROM tracked_apps
                    WHERE active = 1
                    AND (
                        last_price_update IS NULL 
                        OR last_price_update < datetime('now', '-{} hours')
                    )
                    ORDER BY last_price_update ASC NULLS FIRST
                """.format(hours_threshold))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Apps für Update: {e}")
            return []
    
    def get_apps_with_generic_names(self, limit: int = 50) -> List[Tuple[str, str]]:
        """
        Findet Apps mit generischen Namen
        
        Args:
            limit: Maximum Anzahl Apps
            
        Returns:
            Liste mit (app_id, current_name) Tupeln
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT steam_app_id, name
                    FROM tracked_apps
                    WHERE active = 1
                    AND (
                        name LIKE 'App %'
                        OR name = 'Unknown Game'
                        OR name LIKE '%Unknown%'
                        OR LENGTH(name) < 3
                    )
                    ORDER BY added_at DESC
                    LIMIT ?
                """, (limit,))
                
                return [(row['steam_app_id'], row['name']) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Apps mit generischen Namen: {e}")
            return []
    
    def update_app_name(self, app_id: str, new_name: str) -> bool:
        """
        Aktualisiert den Namen einer App
        
        Args:
            app_id: Steam App ID
            new_name: Neuer Name
            
        Returns:
            True wenn erfolgreich aktualisiert
        """
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        UPDATE tracked_apps 
                        SET name = ? 
                        WHERE steam_app_id = ?
                    """, (new_name, app_id))
                    
                    success = cursor.rowcount > 0
                    conn.commit()
                    
                    return success
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren des App-Namens für {app_id}: {e}")
            return False
    
    def cleanup_old_prices(self, days: int = 90) -> int:
        """
        Bereinigt alte Preis-Snapshots
        
        Args:
            days: Snapshots älter als X Tage löschen
            
        Returns:
            Anzahl gelöschter Snapshots
        """
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        DELETE FROM price_snapshots 
                        WHERE timestamp < datetime('now', '-{} days')
                    """.format(days))
                    
                    deleted_count = cursor.rowcount
                    
                    # Charts-Cleanup ebenfalls durchführen
                    orphaned_count = self.cleanup_orphaned_chart_data()
                    deleted_count += orphaned_count
                    
                    conn.commit()
                    
                    if deleted_count > 0:
                        logger.info(f"🧹 {deleted_count} alte Einträge bereinigt (>{days} Tage)")
                    
                    return deleted_count
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Bereinigen alter Preise: {e}")
            return 0
    
    def vacuum_database(self):
        """Optimiert die Datenbank"""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
            
            # Charts-Optimierung ebenfalls durchführen
            self.optimize_charts_database()
            
            logger.info("✅ Datenbank optimiert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Optimieren der Datenbank: {e}")
    
    def backup_database(self) -> Optional[str]:
        """
        Erstellt ein Backup der gesamten Datenbank
        
        Returns:
            Pfad zum Backup-File oder None
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)
            
            backup_file = backup_dir / f"database_backup_{timestamp}.db"
            
            # Datenbank-Datei kopieren
            shutil.copy2(self.db_path, backup_file)
            
            logger.info(f"💾 Datenbank-Backup erstellt: {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des Datenbank-Backups: {e}")
            return None
    
    def export_to_csv(self, filename: str = None) -> str:
        """
        Exportiert alle Daten als CSV
        
        Args:
            filename: Dateiname (optional)
            
        Returns:
            Pfad zur erstellten CSV-Datei
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"steam_price_tracker_export_{timestamp}.csv"
        
        export_path = Path("exports")
        export_path.mkdir(exist_ok=True)
        full_path = export_path / filename
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Alle Preisdaten mit App-Informationen
                cursor.execute("""
                    SELECT 
                        ps.*,
                        ta.name as app_name,
                        ta.added_at,
                        ta.source
                    FROM price_snapshots ps
                    INNER JOIN tracked_apps ta ON ps.steam_app_id = ta.steam_app_id
                    ORDER BY ps.timestamp DESC
                """)
                
                rows = cursor.fetchall()
                
                if rows:
                    with open(full_path, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=rows[0].keys())
                        writer.writeheader()
                        
                        for row in rows:
                            writer.writerow(dict(row))
                    
                    logger.info(f"📄 CSV-Export erstellt: {full_path} ({len(rows)} Einträge)")
                else:
                    logger.warning("Keine Daten für Export verfügbar")
                
                return str(full_path)
                
        except Exception as e:
            logger.error(f"❌ Fehler beim CSV-Export: {e}")
            return ""
    
    def get_database_statistics(self) -> Dict:
        """
        Gibt detaillierte Datenbank-Statistiken zurück
        
        Returns:
            Dictionary mit Statistiken
        """
        try:
            stats = {}
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Basis-Statistiken
                cursor.execute("SELECT COUNT(*) as count FROM tracked_apps WHERE active = 1")
                stats['total_apps'] = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM price_snapshots")
                stats['total_snapshots'] = cursor.fetchone()['count']
                
                cursor.execute("""
                    SELECT MAX(timestamp) as last_update 
                    FROM price_snapshots
                """)
                result = cursor.fetchone()
                stats['last_update'] = result['last_update'] if result['last_update'] else 'Nie'
                
                # Charts-Statistiken hinzufügen
                if self.check_charts_tables():
                    charts_stats = self.get_charts_database_statistics()
                    if 'error' not in charts_stats:
                        stats['charts'] = charts_stats
                
                # Datenbank-Größe
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()['size']
                stats['database_size_mb'] = round(db_size / (1024 * 1024), 2)
                
                # Aktuelle Deals
                deals = self.get_best_deals(min_discount=10, limit=10)
                stats['current_deals'] = len(deals)
                
                return stats
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Datenbank-Statistiken: {e}")
            return {'error': str(e)}
    
    # =====================================================================
    # CHARTS-SPEZIFISCHE DATENBANKFUNKTIONEN
    # =====================================================================
    
    def get_active_chart_games(self, chart_type: str = None) -> List[Dict]:
        """
        Gibt aktive Charts-Spiele zurück
        
        Args:
            chart_type: Optionale Filterung nach Chart-Typ
            
        Returns:
            Liste aktiver Charts-Spiele
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT * FROM steam_charts_tracking 
                    WHERE last_seen >= datetime('now', '-7 days')
                """
                params = []
                
                if chart_type:
                    query += " AND chart_type = ?"
                    params.append(chart_type)
                
                query += " ORDER BY chart_type, current_rank"
                
                cursor.execute(query, params)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen aktiver Charts-Spiele: {e}")
            return []

if __name__ == "__main__":
    # Test-Ausführung
    print("🧪 Database Manager - Test Mode")
    
    try:
        # Database Manager erstellen
        db = DatabaseManager("test_steam_price_tracker.db")
        
        print("✅ Database Manager erstellt")
        
        # Statistiken anzeigen
        stats = db.get_database_statistics()
        print(f"📊 Statistiken: {stats}")
        
        # Charts-Tabellen prüfen
        charts_ok = db.check_charts_tables()
        print(f"📊 Charts-Tabellen: {'✅' if charts_ok else '❌'}")
        
    except Exception as e:
        print(f"❌ Test-Fehler: {e}")
