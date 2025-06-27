#!/usr/bin/env python3
"""
Database Manager - KORRIGIERT für Steam Price Tracker
Behebt das Schema-Problem mit der 'source' Spalte und API-Inkompatibilitäten
Vollständig kompatibel mit main.py und allen anderen Komponenten
"""

import sqlite3
import threading
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
import os

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Database Manager mit korrigiertem Schema und robusten Fallback-Mechanismen
    Behebt alle identifizierten Probleme:
    - 'source' Spalte in tracked_apps Tabelle
    - Korrekte Parameter-Reihenfolge für add_tracked_app
    - Robuste get_tracked_apps Implementierung
    - Vollständige API-Kompatibilität
    """
    
    def __init__(self, db_path: str = "steam_price_tracker.db"):
        self.db_path = db_path
        self.lock = threading.RLock()
        
        # Datenbank initialisieren
        self._init_database()
        self._migrate_schema_if_needed()
        
        logger.info(f"✅ DatabaseManager initialisiert: {db_path}")
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Erstellt eine neue Datenbankverbindung mit row_factory
        """
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row  # Ermöglicht dict-ähnlichen Zugriff
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn
    
    def _init_database(self):
        """
        Initialisiert alle erforderlichen Tabellen mit korrektem Schema
        """
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # ===================================================
                # HAUPT-TRACKING-TABELLE (KORRIGIERT)
                # ===================================================
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tracked_apps (
                        steam_app_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        source TEXT DEFAULT 'manual',  -- KORRIGIERT: source Spalte hinzugefügt
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_price_update TIMESTAMP,
                        active BOOLEAN DEFAULT 1,
                        target_price REAL DEFAULT NULL,
                        notes TEXT DEFAULT NULL
                    )
                ''')
                
                # ===================================================
                # PREIS-SNAPSHOTS TABELLE (ERWEITERT)
                # ===================================================
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS price_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        steam_app_id TEXT NOT NULL,
                        game_title TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        
                        -- Steam Store Preise
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
                        
                        -- Humble Store Preise
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
                        gamesplanet_available BOOLEAN DEFAULT 0,
                        
                        FOREIGN KEY (steam_app_id) REFERENCES tracked_apps (steam_app_id)
                    )
                ''')
                
                # ===================================================
                # CHARTS-TABELLEN (FÜR STEAM CHARTS INTEGRATION)
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
                        active BOOLEAN DEFAULT 1
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS chart_price_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        steam_app_id TEXT NOT NULL,
                        chart_type TEXT NOT NULL,
                        current_price REAL,
                        original_price REAL,
                        discount_percent INTEGER DEFAULT 0,
                        store TEXT DEFAULT 'Steam',
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

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
                # SCHEDULER & AUTOMATION TABELLEN
                # ===================================================
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS scheduler_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        message TEXT,
                        start_time TIMESTAMP,
                        end_time TIMESTAMP,
                        execution_time_seconds REAL
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS app_update_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        steam_app_id TEXT NOT NULL,
                        update_type TEXT NOT NULL,
                        success BOOLEAN,
                        error_message TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # ===================================================
                # PERFORMANCE & MONITORING TABELLEN
                # ===================================================
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        metric_unit TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # ===================================================
                # INDIZES FÜR BESSERE PERFORMANCE
                # ===================================================
                indices = [
                    "CREATE INDEX IF NOT EXISTS idx_tracked_apps_active ON tracked_apps(active)",
                    "CREATE INDEX IF NOT EXISTS idx_tracked_apps_source ON tracked_apps(source)",
                    "CREATE INDEX IF NOT EXISTS idx_snapshots_app_id ON price_snapshots(steam_app_id)",
                    "CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON price_snapshots(timestamp)",
                    "CREATE INDEX IF NOT EXISTS idx_snapshots_app_timestamp ON price_snapshots(steam_app_id, timestamp)",
                    "CREATE INDEX IF NOT EXISTS idx_chart_games_type ON chart_games(chart_type)",
                    "CREATE INDEX IF NOT EXISTS idx_chart_games_active ON chart_games(active)",
                    "CREATE INDEX IF NOT EXISTS idx_scheduler_log_task ON scheduler_log(task_name)",
                    "CREATE INDEX IF NOT EXISTS idx_update_history_app ON app_update_history(steam_app_id)"
                ]
                
                for index_sql in indices:
                    try:
                        cursor.execute(index_sql)
                    except sqlite3.Error as e:
                        logger.debug(f"Index bereits vorhanden: {e}")
                
                conn.commit()
                logger.info("✅ Datenbank-Schema initialisiert")
    
    def _migrate_schema_if_needed(self):
        """
        Migriert das Schema falls eine ältere Version ohne 'source' Spalte vorhanden ist
        """
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                try:
                    # Prüfe ob 'source' Spalte existiert
                    cursor.execute("PRAGMA table_info(tracked_apps)")
                    columns = [column[1] for column in cursor.fetchall()]
                    
                    if 'source' not in columns:
                        logger.info("🔄 Migriere tracked_apps Tabelle - füge 'source' Spalte hinzu")
                        
                        # Füge source Spalte hinzu
                        cursor.execute("ALTER TABLE tracked_apps ADD COLUMN source TEXT DEFAULT 'manual'")
                        
                        # Setze 'manual' als default für bestehende Einträge
                        cursor.execute("UPDATE tracked_apps SET source = 'manual' WHERE source IS NULL")
                        
                        conn.commit()
                        logger.info("✅ Schema-Migration abgeschlossen")
                    
                    # Prüfe weitere optionale Spalten
                    if 'target_price' not in columns:
                        cursor.execute("ALTER TABLE tracked_apps ADD COLUMN target_price REAL DEFAULT NULL")
                        logger.info("✅ target_price Spalte hinzugefügt")
                    
                    if 'notes' not in columns:
                        cursor.execute("ALTER TABLE tracked_apps ADD COLUMN notes TEXT DEFAULT NULL")
                        logger.info("✅ notes Spalte hinzugefügt")
                    
                    conn.commit()
                
                except sqlite3.Error as e:
                    logger.error(f"❌ Fehler bei Schema-Migration: {e}")
    
    # =====================================================================
    # KERN-API METHODEN (KORRIGIERT FÜR MAIN.PY KOMPATIBILITÄT)
    # =====================================================================
    
    def add_tracked_app(self, app_id: str, name: str, source: str = "manual", target_price: Optional[float] = None) -> bool:
        """
        Fügt eine App zum Tracking hinzu (KORRIGIERTE API)
        
        Args:
            app_id: Steam App ID
            name: Name der App
            source: Quelle der App (manual, wishlist, charts)
            target_price: Optionaler Zielpreis
            
        Returns:
            True wenn erfolgreich hinzugefügt
        """
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        INSERT OR IGNORE INTO tracked_apps 
                        (steam_app_id, name, source, target_price, added_at, active)
                        VALUES (?, ?, ?, ?, ?, 1)
                    """, (app_id, name, source, target_price, datetime.now()))
                    
                    success = cursor.rowcount > 0
                    conn.commit()
                    
                    if success:
                        logger.info(f"✅ App hinzugefügt: {name} ({app_id}) [Quelle: {source}]")
                    else:
                        logger.debug(f"App bereits vorhanden: {app_id}")
                    
                    return True  # Immer True, da INSERT OR IGNORE verwendet wird
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Hinzufügen der App {app_id}: {e}")
            return False
    
    def get_tracked_apps(self, active_only: bool = True, limit: Optional[int] = None, source_filter: Optional[str] = None) -> List[Dict]:
        """
        Gibt alle getrackte Apps zurück (KORRIGIERTE API)
        
        Args:
            active_only: Nur aktive Apps
            limit: Maximum Anzahl Apps
            source_filter: Filter nach Quelle (manual, wishlist, charts)
            
        Returns:
            Liste mit App-Informationen als Dictionaries
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Query aufbauen
                query = "SELECT * FROM tracked_apps"
                params = []
                conditions = []
                
                if active_only:
                    conditions.append("active = 1")
                
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
                
                # Konvertiere sqlite3.Row zu Dict
                apps = []
                for row in cursor.fetchall():
                    app_dict = dict(row)
                    apps.append(app_dict)
                
                logger.debug(f"📊 {len(apps)} getrackte Apps geladen")
                return apps
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der getrackte Apps: {e}")
            return []
    
    def save_price_snapshot(self, steam_app_id: str, game_title: str, price_data: Dict) -> bool:
        """
        Speichert einen Preis-Snapshot für eine App
        
        Args:
            steam_app_id: Steam App ID
            game_title: Name des Spiels
            price_data: Dictionary mit Preisinformationen pro Store
            
        Returns:
            True wenn erfolgreich gespeichert
        """
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
        """
        Holt den Preisverlauf für eine App
        
        Args:
            steam_app_id: Steam App ID
            days: Anzahl Tage zurück
            limit: Maximum Anzahl Snapshots
            
        Returns:
            Liste mit Preis-Snapshots
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM price_snapshots 
                    WHERE steam_app_id = ? 
                    AND timestamp >= date('now', '-{} days')
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """.format(days), (steam_app_id, limit))
                
                history = []
                for row in cursor.fetchall():
                    history.append(dict(row))
                
                logger.debug(f"📈 {len(history)} Preis-Snapshots für {steam_app_id} geladen")
                return history
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Preisverlaufs für {steam_app_id}: {e}")
            return []
    
    def get_database_stats(self) -> Dict:
        """
        Holt Statistiken über die Datenbank (KORRIGIERTE API-NAME)
        
        Returns:
            Dictionary mit Statistiken
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Getrackte Apps
                cursor.execute('SELECT COUNT(*) FROM tracked_apps WHERE active = 1')
                tracked_apps = cursor.fetchone()[0]
                
                # Apps nach Quelle
                cursor.execute('''
                    SELECT source, COUNT(*) as count 
                    FROM tracked_apps 
                    WHERE active = 1 
                    GROUP BY source
                ''')
                sources = dict(cursor.fetchall())
                
                # Preis-Snapshots
                cursor.execute('SELECT COUNT(*) FROM price_snapshots')
                total_snapshots = cursor.fetchone()[0]
                
                # Neuester Snapshot
                cursor.execute('SELECT timestamp FROM price_snapshots ORDER BY timestamp DESC LIMIT 1')
                newest_result = cursor.fetchone()
                newest_snapshot = newest_result[0] if newest_result else None
                
                # Snapshots der letzten 7 Tage
                cursor.execute('''
                    SELECT COUNT(*) FROM price_snapshots 
                    WHERE timestamp >= date('now', '-7 days')
                ''')
                recent_snapshots = cursor.fetchone()[0]
                
                # Charts-Statistiken (falls verfügbar)
                try:
                    cursor.execute('SELECT COUNT(*) FROM chart_games WHERE active = 1')
                    chart_games = cursor.fetchone()[0]
                except sqlite3.OperationalError:
                    chart_games = 0
                
                stats = {
                    'tracked_apps': tracked_apps,
                    'sources': sources,
                    'total_snapshots': total_snapshots,
                    'recent_snapshots': recent_snapshots,
                    'chart_games': chart_games,
                    'newest_snapshot': newest_snapshot,
                    'stores_tracked': ['Steam', 'GreenManGaming', 'GOG', 'Humble', 'Fanatical', 'Gamesplanet'],
                    'database_size_mb': self._get_database_size()
                }
                
                logger.debug(f"📊 Datenbank-Statistiken geladen: {tracked_apps} Apps, {total_snapshots} Snapshots")
                return stats
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Datenbank-Statistiken: {e}")
            return {
                'tracked_apps': 0,
                'sources': {},
                'total_snapshots': 0,
                'recent_snapshots': 0,
                'chart_games': 0,
                'newest_snapshot': None,
                'stores_tracked': [],
                'database_size_mb': 0
            }
    
    # =====================================================================
    # UTILITY & MAINTENANCE METHODEN
    # =====================================================================
    
    def cleanup_old_prices(self, days: int = 90) -> int:
        """
        Löscht alte Preis-Snapshots
        
        Args:
            days: Snapshots älter als X Tage löschen
            
        Returns:
            Anzahl gelöschte Snapshots
        """
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        DELETE FROM price_snapshots 
                        WHERE timestamp < date('now', '-{} days')
                    """.format(days))
                    
                    removed = cursor.rowcount
                    conn.commit()
                    
                    logger.info(f"🧹 {removed} alte Preis-Snapshots entfernt (älter als {days} Tage)")
                    return removed
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Bereinigen alter Preise: {e}")
            return 0
    
    def backup_database(self, backup_path: str) -> bool:
        """
        Erstellt ein Backup der Datenbank
        
        Args:
            backup_path: Pfad für das Backup
            
        Returns:
            True wenn erfolgreich
        """
        try:
            import shutil
            
            with self.lock:
                # WAL-Modus: Checkpoint vor Backup
                with self.get_connection() as conn:
                    conn.execute("PRAGMA wal_checkpoint(FULL)")
                
                # Datei kopieren
                shutil.copy2(self.db_path, backup_path)
                
                backup_size = os.path.getsize(backup_path) / (1024 * 1024)
                logger.info(f"💾 Datenbank-Backup erstellt: {backup_path} ({backup_size:.2f} MB)")
                return True
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des Backups: {e}")
            return False
    
    def vacuum_database(self) -> bool:
        """
        Optimiert die Datenbank
        
        Returns:
            True wenn erfolgreich
        """
        try:
            with self.lock:
                with self.get_connection() as conn:
                    old_size = os.path.getsize(self.db_path) / (1024 * 1024)
                    
                    conn.execute("VACUUM")
                    conn.execute("ANALYZE")
                    
                    new_size = os.path.getsize(self.db_path) / (1024 * 1024)
                    saved_mb = old_size - new_size
                    
                    logger.info(f"🔧 Datenbank optimiert: {old_size:.2f} MB → {new_size:.2f} MB (gesparte {saved_mb:.2f} MB)")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Fehler bei Datenbank-Optimierung: {e}")
            return False
    
    def _get_database_size(self) -> float:
        """Gibt die Datenbankgröße in MB zurück"""
        try:
            return os.path.getsize(self.db_path) / (1024 * 1024)
        except Exception:
            return 0.0
    
    # =====================================================================
    # CHARTS-SPEZIFISCHE METHODEN
    # =====================================================================
    
    def init_charts_tables(self) -> bool:
        """
        Initialisiert Charts-spezifische Tabellen
        """
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                
                    # ERWEITERT: Erstelle chart_games Tabelle falls nicht vorhanden
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
                
                    # Zusätzliche Charts-spezifische Indizes
                    charts_indices = [
                        "CREATE INDEX IF NOT EXISTS idx_chart_games_app_type ON chart_games(steam_app_id, chart_type)",
                        "CREATE INDEX IF NOT EXISTS idx_chart_games_active ON chart_games(active)",
                        "CREATE INDEX IF NOT EXISTS idx_chart_games_type ON chart_games(chart_type)",
                        "CREATE INDEX IF NOT EXISTS idx_chart_price_snapshots_app ON chart_price_snapshots(steam_app_id)",
                        "CREATE INDEX IF NOT EXISTS idx_chart_price_snapshots_timestamp ON chart_price_snapshots(timestamp)"
                    ]
                
                    for index_sql in charts_indices:
                        try:
                            cursor.execute(index_sql)
                        except sqlite3.Error:
                            pass  # Index bereits vorhanden
                
                    conn.commit()
                    logger.info("✅ Charts-Tabellen und Indizes initialisiert")
                    return True
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Charts-Tabellen-Initialisierung: {e}")
            return False
    
    def add_chart_game(self, steam_app_id: str, chart_type: str, rank_position: int, 
                      current_players: int = None, game_name: str = None) -> bool:
        """
        Fügt ein Spiel zu den Charts hinzu
        """
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO chart_games
                        (steam_app_id, chart_type, rank_position, current_players, game_name, last_updated, active)
                        VALUES (?, ?, ?, ?, ?, ?, 1)
                    """, (steam_app_id, chart_type, rank_position, current_players, game_name, datetime.now()))
                    
                    conn.commit()
                    logger.debug(f"✅ Chart-Spiel hinzugefügt: {game_name} ({steam_app_id}) in {chart_type}")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Hinzufügen des Chart-Spiels: {e}")
            return False
    
    def get_active_chart_games(self, chart_type: Optional[str] = None) -> List[Dict]:
        """
        Holt aktive Chart-Spiele
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if chart_type:
                    cursor.execute("""
                        SELECT * FROM chart_games 
                        WHERE active = 1 AND chart_type = ?
                        ORDER BY rank_position ASC
                    """, (chart_type,))
                else:
                    cursor.execute("""
                        SELECT * FROM chart_games 
                        WHERE active = 1
                        ORDER BY chart_type, rank_position ASC
                    """)
                
                games = []
                for row in cursor.fetchall():
                    games.append(dict(row))
                
                return games
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Chart-Spiele: {e}")
            return []
    
    def get_charts_statistics(self) -> Dict:
        """
        Holt Charts-Statistiken
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Gesamte Chart-Spiele
                cursor.execute('SELECT COUNT(*) FROM chart_games WHERE active = 1')
                total_chart_games = cursor.fetchone()[0]
                
                # Charts nach Typ
                cursor.execute('''
                    SELECT chart_type, COUNT(*) as count 
                    FROM chart_games 
                    WHERE active = 1 
                    GROUP BY chart_type
                ''')
                chart_types = dict(cursor.fetchall())
                
                # Letztes Update
                cursor.execute('SELECT MAX(last_updated) FROM chart_games')
                last_update_result = cursor.fetchone()
                last_update = last_update_result[0] if last_update_result else None
                
                return {
                    'total_chart_games': total_chart_games,
                    'chart_types': list(chart_types.keys()),
                    'chart_type_counts': chart_types,
                    'last_update': last_update
                }
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Charts-Statistiken: {e}")
            return {
                'total_chart_games': 0,
                'chart_types': [],
                'chart_type_counts': {},
                'last_update': None
            }
    
    # =====================================================================
    # APP-MANAGEMENT METHODEN
    # =====================================================================
    
    def deactivate_app(self, steam_app_id: str) -> bool:
        """Deaktiviert eine App ohne sie zu löschen"""
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE tracked_apps SET active = 0 WHERE steam_app_id = ?", (steam_app_id,))
                    success = cursor.rowcount > 0
                    conn.commit()
                    
                    if success:
                        logger.info(f"✅ App deaktiviert: {steam_app_id}")
                    return success
        except Exception as e:
            logger.error(f"❌ Fehler beim Deaktivieren der App: {e}")
            return False
    
    def activate_app(self, steam_app_id: str) -> bool:
        """Aktiviert eine deaktivierte App"""
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE tracked_apps SET active = 1 WHERE steam_app_id = ?", (steam_app_id,))
                    success = cursor.rowcount > 0
                    conn.commit()
                    
                    if success:
                        logger.info(f"✅ App aktiviert: {steam_app_id}")
                    return success
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktivieren der App: {e}")
            return False
    
    def remove_app(self, steam_app_id: str) -> bool:
        """Entfernt eine App komplett aus der Datenbank"""
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # App aus tracked_apps entfernen
                    cursor.execute("DELETE FROM tracked_apps WHERE steam_app_id = ?", (steam_app_id,))
                    removed_apps = cursor.rowcount
                    
                    # Zugehörige Preis-Snapshots entfernen
                    cursor.execute("DELETE FROM price_snapshots WHERE steam_app_id = ?", (steam_app_id,))
                    removed_snapshots = cursor.rowcount
                    
                    # Chart-Daten entfernen (falls vorhanden)
                    cursor.execute("DELETE FROM chart_games WHERE steam_app_id = ?", (steam_app_id,))
                    cursor.execute("DELETE FROM chart_price_snapshots WHERE steam_app_id = ?", (steam_app_id,))
                    
                    conn.commit()
                    
                    if removed_apps > 0:
                        logger.info(f"✅ App komplett entfernt: {steam_app_id} ({removed_snapshots} Snapshots)")
                        return True
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Entfernen der App: {e}")
            return False
    
    def update_app_name(self, steam_app_id: str, new_name: str) -> bool:
        """Aktualisiert den Namen einer App"""
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE tracked_apps SET name = ? WHERE steam_app_id = ?", (new_name, steam_app_id))
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
                    cursor.execute("UPDATE tracked_apps SET target_price = ? WHERE steam_app_id = ?", (target_price, steam_app_id))
                    success = cursor.rowcount > 0
                    conn.commit()
                    
                    if success:
                        logger.info(f"✅ Zielpreis gesetzt: {steam_app_id} → €{target_price:.2f}")
                    return success
        except Exception as e:
            logger.error(f"❌ Fehler beim Setzen des Zielpreises: {e}")
            return False

# =====================================================================
# KOMPATIBILITÄTS-WRAPPER (FÜR ÄLTERE APIs)
# =====================================================================

# Alias für Rückwärtskompatibilität
get_statistics = lambda self: self.get_database_stats()

# Factory-Funktion für einfache Erstellung
def create_database_manager(db_path: str = "steam_price_tracker.db") -> DatabaseManager:
    """
    Factory-Funktion zur Erstellung eines DatabaseManager
    """
    return DatabaseManager(db_path)

if __name__ == "__main__":
    # Test der Database Manager Funktionalität
    print("🧪 TESTING DATABASE MANAGER")
    print("=" * 30)
    
    # Test-DB erstellen
    db = DatabaseManager("test_steam_tracker.db")
    
    # Test: App hinzufügen
    success = db.add_tracked_app("123456", "Test Game", "manual")
    print(f"✅ App hinzugefügt: {success}")
    
    # Test: Apps abrufen
    apps = db.get_tracked_apps()
    print(f"📊 Getrackte Apps: {len(apps)}")
    
    # Test: Statistiken
    stats = db.get_database_stats()
    print(f"📈 Statistiken: {stats}")
    
    print("✅ Database Manager Tests abgeschlossen")
