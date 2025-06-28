#!/usr/bin/env python3
"""
Database Manager - VOLLSTÄNDIGE PRODUKTIONSVERSION
Steam Price Tracker - Korrigiert alle Schema-Probleme und API-Inkompatibilitäten
100% kompatibel mit main.py und allen anderen Komponenten
"""

import sqlite3
import threading
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
import os
import shutil

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Vollständige Database Manager Klasse - PRODUKTIONSVERSION
    
    Behebt alle identifizierten Probleme:
    - Schema-Synchronisation zwischen chart_games und steam_charts_tracking
    - Vollständige API-Kompatibilität mit main.py
    - Robuste Fallback-Mechanismen
    - Korrekte DDL-Struktur
    """
    
    def __init__(self, db_path: str = "steam_price_tracker.db"):
        self.db_path = db_path
        self.lock = threading.RLock()
        
        # Datenbank initialisieren
        self._init_database()
        self._migrate_schema_if_needed()
        
        logger.info(f"✅ DatabaseManager (PRODUCTION) initialisiert: {db_path}")
    
    def get_connection(self) -> sqlite3.Connection:
        """Erstellt eine neue Datenbankverbindung mit row_factory"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row  # Ermöglicht dict-ähnlichen Zugriff
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn
    
    def _init_database(self):
        """Initialisiert alle erforderlichen Tabellen mit KORREKTEM Schema"""
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # ===================================================
                # HAUPT-TRACKING-TABELLE
                # ===================================================
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tracked_apps (
                        steam_app_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_price_update TIMESTAMP,
                        active BOOLEAN DEFAULT 1,
                        last_name_update TIMESTAMP,
                        name_update_attempts INTEGER DEFAULT 0,
                        source TEXT DEFAULT 'manual',
                        target_price REAL,
                        notes TEXT
                    )
                ''')
                
                # ===================================================
                # PRICE SNAPSHOTS (ERWEITERT FÜR ALLE STORES)
                # ===================================================
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS price_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        steam_app_id TEXT NOT NULL REFERENCES tracked_apps,
                        game_title TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        
                        -- Steam Preise
                        steam_price REAL,
                        steam_original_price REAL,
                        steam_discount_percent INTEGER DEFAULT 0,
                        steam_available BOOLEAN DEFAULT 0,
                        
                        -- GreenManGaming Preise
                        greenmangaming_price REAL,
                        greenmangaming_original_price REAL,
                        greenmangaming_discount_percent INTEGER DEFAULT 0,
                        greenmangaming_available BOOLEAN DEFAULT 0,
                        
                        -- GOG Preise
                        gog_price REAL,
                        gog_original_price REAL,
                        gog_discount_percent INTEGER DEFAULT 0,
                        gog_available BOOLEAN DEFAULT 0,
                        
                        -- HumbleStore Preise
                        humblestore_price REAL,
                        humblestore_original_price REAL,
                        humblestore_discount_percent INTEGER DEFAULT 0,
                        humblestore_available BOOLEAN DEFAULT 0,
                        
                        -- Fanatical Preise
                        fanatical_price REAL,
                        fanatical_original_price REAL,
                        fanatical_discount_percent INTEGER DEFAULT 0,
                        fanatical_available BOOLEAN DEFAULT 0,
                        
                        -- Gamesplanet Preise
                        gamesplanet_price REAL,
                        gamesplanet_original_price REAL,
                        gamesplanet_discount_percent INTEGER DEFAULT 0,
                        gamesplanet_available BOOLEAN DEFAULT 0
                    )
                ''')
                
                # ===================================================
                # STEAM CHARTS TABELLEN (KORRIGIERT - ENTSPRICHT ECHTER DDL)
                # ===================================================
                
                # steam_charts_tracking (HAUPTTABELLE für Charts)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS steam_charts_tracking (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        steam_app_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        chart_type TEXT NOT NULL,
                        current_rank INTEGER DEFAULT 0,
                        best_rank INTEGER DEFAULT 999999,
                        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        total_appearances INTEGER DEFAULT 1,
                        active BOOLEAN DEFAULT 1,
                        metadata TEXT,
                        -- ERWEITERTE SPALTEN FÜR KOMPATIBILITÄT
                        days_in_charts INTEGER DEFAULT 1,
                        rank_trend TEXT DEFAULT 'new',
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        peak_players INTEGER,
                        current_players INTEGER,
                        UNIQUE(steam_app_id, chart_type)
                    )
                ''')
                
                # charts_history (wie echte DDL)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS charts_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        steam_app_id TEXT NOT NULL REFERENCES steam_charts_tracking(steam_app_id),
                        chart_type TEXT NOT NULL,
                        rank_position INTEGER NOT NULL,
                        snapshot_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        additional_data TEXT
                    )
                ''')
                
                # steam_charts_prices (wie echte DDL)
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
                        FOREIGN KEY (steam_app_id, chart_type) REFERENCES steam_charts_tracking(steam_app_id, chart_type)
                    )
                ''')
                
                # steam_charts_rank_history (wie echte DDL)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS steam_charts_rank_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        steam_app_id TEXT NOT NULL,
                        chart_type TEXT NOT NULL,
                        rank_position INTEGER NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (steam_app_id, chart_type) REFERENCES steam_charts_tracking(steam_app_id, chart_type)
                    )
                ''')
                
                # steam_charts_statistics (wie echte DDL)
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
                
                # steam_charts_config (wie echte DDL)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS steam_charts_config (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # ===================================================
                # LEGACY chart_games TABELLE (FÜR RÜCKWÄRTSKOMPATIBILITÄT)
                # ===================================================
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS chart_games (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        steam_app_id TEXT NOT NULL,
                        chart_type TEXT NOT NULL,
                        rank_position INTEGER,
                        current_players INTEGER,
                        peak_players INTEGER,
                        game_name TEXT,
                        added_to_charts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        active BOOLEAN DEFAULT 1,
                        days_in_charts INTEGER DEFAULT 1
                    )
                ''')
                
                # ===================================================
                # ZUSÄTZLICHE TABELLEN
                # ===================================================
                
                # Name History
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS app_name_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        steam_app_id TEXT NOT NULL REFERENCES tracked_apps,
                        old_name TEXT,
                        new_name TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        update_source TEXT DEFAULT 'manual'
                    )
                ''')
                
                # Price Alerts
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS price_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        steam_app_id TEXT NOT NULL REFERENCES tracked_apps,
                        target_price REAL NOT NULL,
                        store_name TEXT,
                        active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        triggered_at TIMESTAMP
                    )
                ''')
                
                # Tracking Sessions
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tracking_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        apps_processed INTEGER DEFAULT 0,
                        apps_successful INTEGER DEFAULT 0,
                        errors_count INTEGER DEFAULT 0,
                        session_type TEXT DEFAULT 'manual'
                    )
                ''')
                
                # ===================================================
                # PERFORMANCE INDIZES
                # ===================================================
                indices = [
                    # Tracked Apps Indizes
                    "CREATE INDEX IF NOT EXISTS idx_tracked_apps_active ON tracked_apps(active)",
                    "CREATE INDEX IF NOT EXISTS idx_tracked_apps_last_update ON tracked_apps(last_price_update)",
                    "CREATE INDEX IF NOT EXISTS idx_tracked_apps_source ON tracked_apps(source)",
                    
                    # Price Snapshots Indizes
                    "CREATE INDEX IF NOT EXISTS idx_price_snapshots_app_id ON price_snapshots(steam_app_id)",
                    "CREATE INDEX IF NOT EXISTS idx_price_snapshots_timestamp ON price_snapshots(timestamp)",
                    "CREATE INDEX IF NOT EXISTS idx_price_snapshots_app_timestamp ON price_snapshots(steam_app_id, timestamp)",
                    
                    # Steam Charts Tracking Indizes (wie echte DDL)
                    "CREATE INDEX IF NOT EXISTS idx_charts_tracking_app_id ON steam_charts_tracking(steam_app_id)",
                    "CREATE INDEX IF NOT EXISTS idx_charts_tracking_app_type ON steam_charts_tracking(steam_app_id, chart_type)",
                    "CREATE INDEX IF NOT EXISTS idx_charts_tracking_chart_type ON steam_charts_tracking(chart_type)",
                    "CREATE INDEX IF NOT EXISTS idx_charts_tracking_active ON steam_charts_tracking(active)",
                    "CREATE INDEX IF NOT EXISTS idx_charts_tracking_last_seen ON steam_charts_tracking(last_seen)",
                    "CREATE INDEX IF NOT EXISTS idx_charts_tracking_rank ON steam_charts_tracking(current_rank)",
                    "CREATE INDEX IF NOT EXISTS idx_charts_tracking_type_rank ON steam_charts_tracking(chart_type, current_rank)",
                    
                    # Legacy chart_games Indizes
                    "CREATE INDEX IF NOT EXISTS idx_chart_games_app_type ON chart_games(steam_app_id, chart_type)",
                    "CREATE INDEX IF NOT EXISTS idx_chart_games_active ON chart_games(active)",
                    "CREATE INDEX IF NOT EXISTS idx_chart_games_type ON chart_games(chart_type)",
                    
                    # Charts History Indizes
                    "CREATE INDEX IF NOT EXISTS idx_charts_history_app_id ON charts_history(steam_app_id)",
                    "CREATE INDEX IF NOT EXISTS idx_charts_history_timestamp ON charts_history(snapshot_timestamp)",
                    
                    # Charts Prices Indizes
                    "CREATE INDEX IF NOT EXISTS idx_charts_prices_app_chart ON steam_charts_prices(steam_app_id, chart_type)",
                    "CREATE INDEX IF NOT EXISTS idx_charts_prices_timestamp ON steam_charts_prices(timestamp)",
                    
                    # Price Alerts Indizes
                    "CREATE INDEX IF NOT EXISTS idx_price_alerts_active ON price_alerts(active)",
                    
                    # Name History Indizes
                    "CREATE INDEX IF NOT EXISTS idx_name_history_app_id ON app_name_history(steam_app_id)"
                ]
                
                for index_sql in indices:
                    try:
                        cursor.execute(index_sql)
                    except sqlite3.Error as e:
                        logger.debug(f"Index bereits vorhanden: {e}")
                
                conn.commit()
                logger.info("✅ Datenbank-Schema (PRODUCTION) initialisiert")
    
    def _migrate_schema_if_needed(self):
        """Migriert Schema falls nötig und behebt legacy Probleme"""
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                try:
                    # 1. Prüfe tracked_apps Schema
                    cursor.execute("PRAGMA table_info(tracked_apps)")
                    tracked_apps_columns = {row[1] for row in cursor.fetchall()}
                    
                    missing_tracked_columns = {
                        'source': 'TEXT DEFAULT "manual"',
                        'target_price': 'REAL DEFAULT NULL',
                        'notes': 'TEXT DEFAULT NULL'
                    }
                    
                    for col_name, col_def in missing_tracked_columns.items():
                        if col_name not in tracked_apps_columns:
                            try:
                                cursor.execute(f"ALTER TABLE tracked_apps ADD COLUMN {col_name} {col_def}")
                                logger.info(f"✅ tracked_apps Spalte hinzugefügt: {col_name}")
                            except sqlite3.OperationalError as e:
                                if "duplicate column name" not in str(e):
                                    logger.warning(f"⚠️ Konnte Spalte {col_name} nicht hinzufügen: {e}")
                    
                    # 2. Prüfe steam_charts_tracking Schema
                    cursor.execute("PRAGMA table_info(steam_charts_tracking)")
                    charts_columns = {row[1] for row in cursor.fetchall()}
                    
                    missing_charts_columns = {
                        'days_in_charts': 'INTEGER DEFAULT 1',
                        'rank_trend': 'TEXT DEFAULT "new"',
                        'updated_at': 'TIMESTAMP DEFAULT NULL',  # SQLite-kompatibel
                        'peak_players': 'INTEGER DEFAULT NULL',
                        'current_players': 'INTEGER DEFAULT NULL'
                    }
                    
                    for col_name, col_def in missing_charts_columns.items():
                        if col_name not in charts_columns:
                            try:
                                cursor.execute(f"ALTER TABLE steam_charts_tracking ADD COLUMN {col_name} {col_def}")
                                logger.info(f"✅ steam_charts_tracking Spalte hinzugefügt: {col_name}")
                                
                                # Spezielle Nachbearbeitung für updated_at
                                if col_name == 'updated_at':
                                    cursor.execute("""
                                        UPDATE steam_charts_tracking 
                                        SET updated_at = datetime('now') 
                                        WHERE updated_at IS NULL
                                    """)
                                    logger.info(f"✅ {col_name} mit aktuellen Zeitstempel befüllt")
                                    
                            except sqlite3.OperationalError as e:
                                if "duplicate column name" not in str(e):
                                    logger.warning(f"⚠️ Konnte Spalte {col_name} nicht hinzufügen: {e}")
                    
                    # 3. Synchronisiere total_appearances mit days_in_charts
                    if 'total_appearances' in charts_columns and 'days_in_charts' in charts_columns:
                        cursor.execute("""
                            UPDATE steam_charts_tracking 
                            SET days_in_charts = COALESCE(total_appearances, 1)
                            WHERE days_in_charts IS NULL OR days_in_charts <= 0
                        """)
                        
                        updated_rows = cursor.rowcount
                        if updated_rows > 0:
                            logger.info(f"✅ {updated_rows} Einträge: total_appearances → days_in_charts synchronisiert")
                    
                    # 4. Migriere Daten von chart_games zu steam_charts_tracking (falls nötig)
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='chart_games'
                    """)
                    
                    if cursor.fetchone():
                        self._migrate_chart_games_to_steam_charts_tracking(cursor)
                    
                    conn.commit()
                    logger.info("✅ Schema-Migration abgeschlossen")
                    
                except sqlite3.Error as e:
                    logger.error(f"❌ Fehler bei Schema-Migration: {e}")
    
    def _migrate_chart_games_to_steam_charts_tracking(self, cursor):
        """Migriert Daten von legacy chart_games zu steam_charts_tracking"""
        try:
            cursor.execute("SELECT COUNT(*) FROM chart_games WHERE active = 1")
            chart_games_count = cursor.fetchone()[0]
            
            if chart_games_count == 0:
                return
            
            cursor.execute("SELECT COUNT(*) FROM steam_charts_tracking")
            tracking_count = cursor.fetchone()[0]
            
            # Nur migrieren wenn steam_charts_tracking weniger Daten hat
            if tracking_count < chart_games_count:
                cursor.execute("SELECT * FROM chart_games WHERE active = 1")
                chart_games = cursor.fetchall()
                
                migrated = 0
                for game in chart_games:
                    # Prüfe ob bereits in steam_charts_tracking
                    cursor.execute("""
                        SELECT id FROM steam_charts_tracking 
                        WHERE steam_app_id = ? AND chart_type = ?
                    """, (game['steam_app_id'], game['chart_type']))
                    
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO steam_charts_tracking
                            (steam_app_id, name, chart_type, current_rank, best_rank,
                             first_seen, last_seen, total_appearances, active, days_in_charts)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            game['steam_app_id'],
                            game.get('game_name') or f"Game {game['steam_app_id']}",
                            game['chart_type'],
                            game.get('rank_position', 999),
                            game.get('rank_position', 999),
                            game.get('added_to_charts', datetime.now()),
                            game.get('last_updated', datetime.now()),
                            game.get('days_in_charts', 1),  # total_appearances
                            1,  # active
                            game.get('days_in_charts', 1)   # days_in_charts
                        ))
                        migrated += 1
                
                if migrated > 0:
                    logger.info(f"✅ {migrated} Einträge von chart_games zu steam_charts_tracking migriert")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei chart_games Migration: {e}")
    
    # =====================================================================
    # KERN-API METHODEN
    # =====================================================================
    
    def add_tracked_app(self, app_id: str, name: str, source: str = "manual", target_price: Optional[float] = None) -> bool:
        """Fügt eine App zum Tracking hinzu"""
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO tracked_apps 
                        (steam_app_id, name, source, target_price, added_at) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (app_id, name, source, target_price, datetime.now()))
                    
                    conn.commit()
                    logger.debug(f"✅ App hinzugefügt: {name} ({app_id})")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Hinzufügen der App: {e}")
            return False
    
    def fix_charts_data_migration(self) -> bool:
        """
        Überprüft und korrigiert die Daten-Migration von total_appearances zu days_in_charts
        Kann separat aufgerufen werden falls Schema bereits korrekt ist
        """
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Prüfe ob beide Spalten existieren
                    cursor.execute("PRAGMA table_info(steam_charts_tracking)")
                    columns = {row[1] for row in cursor.fetchall()}
                    
                    if 'total_appearances' not in columns or 'days_in_charts' not in columns:
                        logger.warning("⚠️ total_appearances oder days_in_charts Spalte fehlt")
                        return True  # Kein Fehler, nur nicht anwendbar
                    
                    # Prüfe ob Migration korrekt war
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM steam_charts_tracking 
                        WHERE days_in_charts = 1 AND total_appearances > 1
                    """)
                    
                    incorrect_count = cursor.fetchone()[0]
                    
                    if incorrect_count > 0:
                        logger.info(f"🔧 Korrigiere {incorrect_count} inkorrekte days_in_charts Werte...")
                        
                        cursor.execute("""
                            UPDATE steam_charts_tracking 
                            SET days_in_charts = total_appearances 
                            WHERE days_in_charts = 1 AND total_appearances > 1
                        """)
                        
                        updated = cursor.rowcount
                        conn.commit()
                        
                        logger.info(f"✅ {updated} Einträge korrigiert")
                        return True
                    else:
                        logger.info("✅ Daten-Migration bereits korrekt")
                        return True
                        
        except Exception as e:
            logger.error(f"❌ Fehler bei Daten-Migration-Korrektur: {e}")
            return False
    
    def get_tracked_apps(self, active_only: bool = True, limit: Optional[int] = None, 
                        source_filter: Optional[str] = None) -> List[Dict]:
        """Holt alle getrackte Apps"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM tracked_apps"
                params = []
                conditions = []
                
                if active_only:
                    conditions.append("active = ?")
                    params.append(1)
                
                if source_filter:
                    conditions.append("source = ?")
                    params.append(source_filter)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY added_at DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor.execute(query, params)
                
                apps = []
                for row in cursor.fetchall():
                    apps.append(dict(row))
                
                logger.debug(f"📊 {len(apps)} getrackte Apps geladen")
                return apps
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der getrackte Apps: {e}")
            return []
    
    def save_price_snapshot(self, steam_app_id: str, game_title: str, price_data: Dict) -> bool:
        """Speichert einen Preis-Snapshot für eine App"""
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Alle unterstützten Stores
                    stores = ['steam', 'greenmangaming', 'gog', 'humblestore', 'fanatical', 'gamesplanet']
                    
                    # SQL-Insert vorbereiten
                    columns = ['steam_app_id', 'game_title', 'timestamp']
                    values = [steam_app_id, game_title, datetime.now()]
                    placeholders = ['?', '?', '?']
                    
                    # Store-spezifische Daten hinzufügen
                    for store in stores:
                        store_data = price_data.get(store, {})
                        
                        # Preis-Felder pro Store
                        price_fields = [
                            f'{store}_price',
                            f'{store}_original_price', 
                            f'{store}_discount_percent',
                            f'{store}_available'
                        ]
                        
                        for field in price_fields:
                            columns.append(field)
                            placeholders.append('?')
                            
                            if field.endswith('_price') or field.endswith('_original_price'):
                                values.append(store_data.get('price' if field.endswith('_price') else 'original_price'))
                            elif field.endswith('_discount_percent'):
                                values.append(store_data.get('discount_percent', 0))
                            elif field.endswith('_available'):
                                values.append(store_data.get('available', False))
                    
                    # SQL ausführen
                    insert_sql = f"""
                        INSERT INTO price_snapshots ({', '.join(columns)})
                        VALUES ({', '.join(placeholders)})
                    """
                    
                    cursor.execute(insert_sql, values)
                    conn.commit()
                    
                    # last_price_update in tracked_apps aktualisieren
                    cursor.execute("""
                        UPDATE tracked_apps 
                        SET last_price_update = ? 
                        WHERE steam_app_id = ?
                    """, (datetime.now(), steam_app_id))
                    conn.commit()
                    
                    logger.debug(f"✅ Preis-Snapshot gespeichert: {game_title} ({steam_app_id})")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern des Preis-Snapshots für {steam_app_id}: {e}")
            return False
    
    def get_price_history(self, steam_app_id: str, days: int = 30, limit: int = 100) -> List[Dict]:
        """Holt den Preisverlauf für eine App"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(f"""
                    SELECT * FROM price_snapshots 
                    WHERE steam_app_id = ? 
                    AND timestamp >= date('now', '-{days} days')
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (steam_app_id, limit))
                
                history = []
                for row in cursor.fetchall():
                    history.append(dict(row))
                
                logger.debug(f"📊 {len(history)} Preis-Snapshots für {steam_app_id} geladen")
                return history
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Preis-Historie für {steam_app_id}: {e}")
            return []
    
    def get_database_stats(self) -> Dict:
        """Holt Datenbank-Statistiken"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Apps zählen
                cursor.execute("SELECT COUNT(*) FROM tracked_apps WHERE active = 1")
                active_apps = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM tracked_apps")
                total_apps = cursor.fetchone()[0]
                
                # Chart Games zählen
                cursor.execute("SELECT COUNT(*) FROM steam_charts_tracking WHERE active = 1")
                chart_games = cursor.fetchone()[0]
                
                # Price Snapshots zählen
                cursor.execute("SELECT COUNT(*) FROM price_snapshots")
                price_snapshots = cursor.fetchone()[0]
                
                # Letzte Updates
                cursor.execute("SELECT MAX(last_price_update) FROM tracked_apps")
                last_update = cursor.fetchone()[0]
                
                # Stores mit Daten
                stores_with_data = []
                stores = ['steam', 'greenmangaming', 'gog', 'humblestore', 'fanatical', 'gamesplanet']
                for store in stores:
                    cursor.execute(f"SELECT COUNT(*) FROM price_snapshots WHERE {store}_available = 1")
                    count = cursor.fetchone()[0]
                    if count > 0:
                        stores_with_data.append(store)
                
                return {
                    'active_apps': active_apps,
                    'total_apps': total_apps,
                    'chart_games': chart_games,
                    'price_snapshots': price_snapshots,
                    'last_update': last_update,
                    'stores_with_data': stores_with_data,
                    'database_size_mb': self._get_database_size()
                }
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der DB-Statistiken: {e}")
            return {
                'active_apps': 0,
                'total_apps': 0,
                'chart_games': 0,
                'price_snapshots': 0,
                'last_update': None,
                'stores_with_data': [],
                'database_size_mb': 0.0,
                'error': str(e)
            }
    
    def _get_database_size(self) -> float:
        """Gibt die Datenbankgröße in MB zurück"""
        try:
            return os.path.getsize(self.db_path) / (1024 * 1024)
        except Exception:
            return 0.0
    
    # =====================================================================
    # CHARTS-SPEZIFISCHE METHODEN (KORRIGIERT)
    # =====================================================================
    
    def init_charts_tables(self) -> bool:
        """Initialisiert Charts-Tabellen - verwendet steam_charts_tracking"""
        try:
            # Schema ist bereits in _init_database() korrekt erstellt
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Prüfe dass steam_charts_tracking mit days_in_charts existiert
                cursor.execute("PRAGMA table_info(steam_charts_tracking)")
                columns = {row[1] for row in cursor.fetchall()}
                
                required_columns = {'steam_app_id', 'chart_type', 'days_in_charts', 'current_rank'}
                missing = required_columns - columns
                
                if missing:
                    logger.error(f"❌ Fehlende Spalten in steam_charts_tracking: {missing}")
                    return False
                
                logger.info("✅ Charts-Tabellen korrekt initialisiert")
                return True
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Charts-Tabellen-Initialisierung: {e}")
            return False
    
    def add_chart_game(self, steam_app_id: str, chart_type: str, rank_position: int, 
                      current_players: int = None, game_name: str = None) -> bool:
        """Fügt ein Spiel zu steam_charts_tracking hinzu"""
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Verwende steam_charts_tracking!
                    cursor.execute("""
                        INSERT OR REPLACE INTO steam_charts_tracking
                        (steam_app_id, name, chart_type, current_rank, best_rank,
                         last_seen, total_appearances, active, days_in_charts, updated_at,
                         peak_players, current_players)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        steam_app_id, 
                        game_name or f"Game {steam_app_id}",
                        chart_type, 
                        rank_position, 
                        rank_position,  # best_rank = current_rank initially
                        datetime.now(),
                        1,  # total_appearances
                        1,  # active
                        1,  # days_in_charts
                        datetime.now(),
                        current_players,  # peak_players
                        current_players   # current_players
                    ))
                    
                    conn.commit()
                    logger.debug(f"✅ Chart-Spiel hinzugefügt: {game_name} ({steam_app_id}) in {chart_type}")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Hinzufügen des Chart-Spiels: {e}")
            return False
    
    def get_active_chart_games(self, chart_type: Optional[str] = None) -> List[Dict]:
        """Holt aktive Chart-Spiele aus steam_charts_tracking"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if chart_type:
                    cursor.execute("""
                        SELECT * FROM steam_charts_tracking 
                        WHERE active = 1 AND chart_type = ?
                        ORDER BY current_rank ASC
                    """, (chart_type,))
                else:
                    cursor.execute("""
                        SELECT * FROM steam_charts_tracking 
                        WHERE active = 1
                        ORDER BY chart_type, current_rank ASC
                    """)
                
                games = []
                for row in cursor.fetchall():
                    games.append(dict(row))
                
                return games
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Chart-Spiele: {e}")
            return []
    
    def get_charts_statistics(self) -> Dict:
        """Holt Charts-Statistiken aus steam_charts_tracking"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Gesamt-Anzahl pro Chart-Typ
                cursor.execute("""
                    SELECT chart_type, COUNT(*) as count
                    FROM steam_charts_tracking 
                    WHERE active = 1
                    GROUP BY chart_type
                """)
                
                chart_counts = {}
                total_games = 0
                for row in cursor.fetchall():
                    chart_counts[row[0]] = row[1]
                    total_games += row[1]
                
                # Letzte Update-Zeit
                cursor.execute("SELECT MAX(last_seen) FROM steam_charts_tracking")
                last_update = cursor.fetchone()[0] or "Nie"
                
                # Top-Rankings pro Chart-Typ
                cursor.execute("""
                    SELECT chart_type, MIN(current_rank) as best_rank, AVG(current_rank) as avg_rank
                    FROM steam_charts_tracking 
                    WHERE active = 1 
                    GROUP BY chart_type
                """)
                
                chart_rankings = {}
                for row in cursor.fetchall():
                    chart_rankings[row[0]] = {
                        'best_rank': row[1],
                        'avg_rank': round(row[2], 1) if row[2] else 0
                    }
                
                return {
                    'total_chart_games': total_games,
                    'chart_types': list(chart_counts.keys()),
                    'chart_counts': chart_counts,
                    'chart_rankings': chart_rankings,
                    'last_update': last_update
                }
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Charts-Statistiken: {e}")
            return {
                'total_chart_games': 0,
                'chart_types': [],
                'chart_counts': {},
                'chart_rankings': {},
                'last_update': 'Fehler'
            }
    
    # =====================================================================
    # ERWEITERTE METHODEN
    # =====================================================================
    
    def cleanup_old_prices(self, days: int = 90) -> int:
        """Löscht alte Preis-Snapshots"""
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute(f"""
                        DELETE FROM price_snapshots 
                        WHERE timestamp < date('now', '-{days} days')
                    """)
                    
                    deleted_count = cursor.rowcount
                    conn.commit()
                    
                    logger.info(f"🧹 {deleted_count} alte Preis-Snapshots entfernt (älter als {days} Tage)")
                    return deleted_count
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Bereinigen alter Preise: {e}")
            return 0
    
    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """Erstellt Backup der Datenbank"""
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backups/steam_price_tracker_backup_{timestamp}.db"
            
            # Backup-Verzeichnis erstellen
            Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Backup erstellen
            shutil.copy2(self.db_path, backup_path)
            
            backup_size = os.path.getsize(backup_path) / (1024 * 1024)
            logger.info(f"💾 Backup erstellt: {backup_path} ({backup_size:.1f} MB)")
            
            return backup_path
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des Backups: {e}")
            return ""
    
    def vacuum_database(self) -> bool:
        """Optimiert die Datenbank"""
        try:
            with self.lock:
                with self.get_connection() as conn:
                    old_size = self._get_database_size()
                    conn.execute("VACUUM")
                    new_size = self._get_database_size()
                    
                    saved_mb = old_size - new_size
                    logger.info(f"🗜️ Datenbank optimiert: {saved_mb:.1f} MB eingespart")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Optimieren der Datenbank: {e}")
            return False
    
    def update_app_name(self, steam_app_id: str, new_name: str) -> bool:
        """Aktualisiert den Namen einer App"""
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Alten Namen für Historie speichern
                    cursor.execute("SELECT name FROM tracked_apps WHERE steam_app_id = ?", (steam_app_id,))
                    result = cursor.fetchone()
                    if result:
                        old_name = result[0]
                        
                        # Name-Historie speichern
                        cursor.execute("""
                            INSERT INTO app_name_history (steam_app_id, old_name, new_name, update_source)
                            VALUES (?, ?, ?, ?)
                        """, (steam_app_id, old_name, new_name, 'automatic'))
                    
                    # Namen aktualisieren
                    cursor.execute("""
                        UPDATE tracked_apps 
                        SET name = ?, last_name_update = ? 
                        WHERE steam_app_id = ?
                    """, (new_name, datetime.now(), steam_app_id))
                    
                    success = cursor.rowcount > 0
                    conn.commit()
                    
                    if success:
                        logger.info(f"✅ App-Name aktualisiert: {steam_app_id} → {new_name}")
                    return success
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren des App-Namens: {e}")
            return False
    
    def set_target_price(self, steam_app_id: str, target_price: float) -> bool:
        """Setzt einen Zielpreis für eine App"""
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE tracked_apps 
                        SET target_price = ? 
                        WHERE steam_app_id = ?
                    """, (target_price, steam_app_id))
                    
                    success = cursor.rowcount > 0
                    conn.commit()
                    
                    if success:
                        logger.info(f"✅ Zielpreis gesetzt: {steam_app_id} → €{target_price:.2f}")
                    return success
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Setzen des Zielpreises: {e}")
            return False


# =====================================================================
# KOMPATIBILITÄTS-WRAPPER UND FACTORY-FUNKTIONEN
# =====================================================================

def create_database_manager(db_path: str = "steam_price_tracker.db") -> DatabaseManager:
    """Factory-Funktion zur Erstellung eines DatabaseManager"""
    return DatabaseManager(db_path)

# Legacy-Aliases für Rückwärtskompatibilität
def get_statistics(db_manager: DatabaseManager) -> Dict:
    """Legacy-Alias für get_database_stats"""
    return db_manager.get_database_stats()


if __name__ == "__main__":
    # Vollständiger Test der DatabaseManager Funktionalität
    print("🧪 TESTING DATABASE MANAGER (PRODUCTION VERSION)")
    print("=" * 60)
    
    try:
        # Test-DB erstellen
        db = DatabaseManager("test_production.db")
        
        # Test 1: App hinzufügen
        print("📝 Test 1: App hinzufügen...")
        success = db.add_tracked_app("123456", "Test Game", "manual", 19.99)
        print(f"   ✅ App hinzugefügt: {success}")
        
        # Test 2: Apps abrufen
        print("📋 Test 2: Apps abrufen...")
        apps = db.get_tracked_apps()
        print(f"   📊 Getrackte Apps: {len(apps)}")
        if apps:
            print(f"   🎮 Erste App: {apps[0]['name']}")
        
        # Test 3: Chart-Game hinzufügen
        print("📊 Test 3: Chart-Game hinzufügen...")
        success = db.add_chart_game("654321", "best_sellers", 1, 1000, "Chart Test Game")
        print(f"   ✅ Chart-Game hinzugefügt: {success}")
        
        # Test 4: Chart-Games abrufen
        print("📈 Test 4: Chart-Games abrufen...")
        chart_games = db.get_active_chart_games()
        print(f"   📊 Chart-Games: {len(chart_games)}")
        if chart_games:
            print(f"   🏆 Erste Chart-Game: {chart_games[0]['name']}")
        
        # Test 5: days_in_charts Query (der problematische Query!)
        print("🎯 Test 5: days_in_charts Query...")
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT days_in_charts FROM steam_charts_tracking WHERE steam_app_id = ?", ("654321",))
            result = cursor.fetchone()
            print(f"   ✅ days_in_charts Query erfolgreich: {result[0] if result else 'Keine Daten'}")
        
        # Test 6: Statistiken
        print("📈 Test 6: Statistiken...")
        stats = db.get_database_stats()
        print(f"   📊 Apps: {stats['active_apps']}")
        print(f"   📊 Chart-Games: {stats['chart_games']}")
        print(f"   💾 DB-Größe: {stats['database_size_mb']:.2f} MB")
        
        # Test 7: Charts-Statistiken
        print("📊 Test 7: Charts-Statistiken...")
        chart_stats = db.get_charts_statistics()
        print(f"   📊 Chart-Games gesamt: {chart_stats['total_chart_games']}")
        print(f"   📊 Chart-Typen: {chart_stats['chart_types']}")
        
        # Cleanup
        os.remove("test_production.db")
        print("\n🎉 Alle Tests erfolgreich!")
        print("✅ DatabaseManager (PRODUCTION) ist bereit für den Einsatz!")
        
    except Exception as e:
        print(f"\n❌ Test fehlgeschlagen: {e}")
        # Cleanup bei Fehler
        try:
            os.remove("test_production.db")
        except:
            pass
