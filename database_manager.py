"""
Database Manager für Steam Price Tracker
Vollständige Implementation für Preis-Tracking
"""

import sqlite3
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import threading
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Zentrale Datenbank-Klasse für Steam Price Tracking
    Vollständige Implementation mit allen benötigten Methoden
    """
    
    def __init__(self, db_path: str = "steam_price_tracker.db"):
        self.db_path = Path(db_path)
        self.lock = threading.Lock()
        self._init_database()
    
    def get_connection(self):
        """Erstellt eine neue Datenbankverbindung"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """Initialisiert alle benötigten Tabellen"""
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                try:
                    # Tracked Apps Tabelle
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS tracked_apps (
                            steam_app_id TEXT PRIMARY KEY,
                            name TEXT NOT NULL,
                            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_price_update TIMESTAMP,
                            active BOOLEAN DEFAULT 1
                        )
                    ''')
                    
                    # Price Snapshots Tabelle
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS price_snapshots (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            steam_app_id TEXT NOT NULL,
                            game_title TEXT,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            steam_price REAL,
                            steam_original_price REAL,
                            steam_discount_percent INTEGER DEFAULT 0,
                            steam_available BOOLEAN DEFAULT 0,
                            greenmangaming_price REAL,
                            greenmangaming_original_price REAL,
                            greenmangaming_discount_percent INTEGER DEFAULT 0,
                            greenmangaming_available BOOLEAN DEFAULT 0,
                            gog_price REAL,
                            gog_original_price REAL,
                            gog_discount_percent INTEGER DEFAULT 0,
                            gog_available BOOLEAN DEFAULT 0,
                            humblestore_price REAL,
                            humblestore_original_price REAL,
                            humblestore_discount_percent INTEGER DEFAULT 0,
                            humblestore_available BOOLEAN DEFAULT 0,
                            fanatical_price REAL,
                            fanatical_original_price REAL,
                            fanatical_discount_percent INTEGER DEFAULT 0,
                            fanatical_available BOOLEAN DEFAULT 0,
                            gamesplanet_price REAL,
                            gamesplanet_original_price REAL,
                            gamesplanet_discount_percent INTEGER DEFAULT 0,
                            gamesplanet_available BOOLEAN DEFAULT 0,
                            FOREIGN KEY (steam_app_id) REFERENCES tracked_apps (steam_app_id)
                        )
                    ''')
                    
                    # Price Alerts Tabelle
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS price_alerts (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            steam_app_id TEXT NOT NULL,
                            target_price REAL NOT NULL,
                            store_name TEXT,
                            active BOOLEAN DEFAULT 1,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            triggered_at TIMESTAMP,
                            FOREIGN KEY (steam_app_id) REFERENCES tracked_apps (steam_app_id)
                        )
                    ''')
                    
                    # Indizes für Performance
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_snapshots_app_id ON price_snapshots(steam_app_id)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_snapshots_timestamp ON price_snapshots(timestamp)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracked_apps_active ON tracked_apps(active)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_alerts_active ON price_alerts(active)')
                    
                    conn.commit()
                    logger.info("✅ Price Tracker Datenbank initialisiert")
                    
                except sqlite3.Error as e:
                    conn.rollback()
                    raise Exception(f"Datenbank-Initialisierung fehlgeschlagen: {e}")
    
    # ========================
    # TRACKED APPS OPERATIONS
    # ========================
    
    def add_tracked_app(self, steam_app_id: str, name: str) -> bool:
        """Fügt App zum Tracking hinzu"""
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO tracked_apps (steam_app_id, name, added_at, active)
                        VALUES (?, ?, CURRENT_TIMESTAMP, 1)
                    ''', (steam_app_id, name))
                    conn.commit()
                    logger.debug(f"✅ App {name} ({steam_app_id}) zum Tracking hinzugefügt")
                    return True
            except sqlite3.Error as e:
                logger.error(f"❌ Fehler beim Hinzufügen der App {steam_app_id}: {e}")
                return False
    
    def remove_tracked_app(self, steam_app_id: str) -> bool:
        """Entfernt App aus Tracking"""
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM tracked_apps WHERE steam_app_id = ?', (steam_app_id,))
                    conn.commit()
                    logger.info(f"✅ App {steam_app_id} aus Tracking entfernt")
                    return True
            except sqlite3.Error as e:
                logger.error(f"❌ Fehler beim Entfernen der App {steam_app_id}: {e}")
                return False
    
    def get_tracked_apps(self) -> List[Dict]:
        """Gibt alle getrackte Apps zurück"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT steam_app_id, name, added_at, last_price_update, active
                FROM tracked_apps
                WHERE active = 1
                ORDER BY added_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def update_app_last_price_update(self, steam_app_id: str):
        """Aktualisiert last_price_update für App"""
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE tracked_apps 
                        SET last_price_update = CURRENT_TIMESTAMP 
                        WHERE steam_app_id = ?
                    ''', (steam_app_id,))
                    conn.commit()
            except sqlite3.Error as e:
                logger.error(f"❌ Fehler beim Update von last_price_update für {steam_app_id}: {e}")
    
    def get_apps_needing_update(self, hours_threshold: int = 6) -> List[Dict]:
        """Gibt Apps zurück die ein Update benötigen"""
        cutoff_time = datetime.now() - timedelta(hours=hours_threshold)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT steam_app_id, name, added_at, last_price_update
                FROM tracked_apps
                WHERE active = 1 
                AND (last_price_update IS NULL OR last_price_update < ?)
                ORDER BY 
                    CASE WHEN last_price_update IS NULL THEN 0 ELSE 1 END,
                    last_price_update ASC
            ''', (cutoff_time.isoformat(),))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ========================
    # PRICE SNAPSHOTS OPERATIONS
    # ========================
    
    def save_price_snapshot(self, steam_app_id: str, game_title: str, prices: Dict) -> bool:
        """Speichert Preis-Snapshot in Datenbank"""
        with self.lock:
            try:
                # Store mapping für Datenbankfelder
                store_mapping = {
                    'Steam': 'steam',
                    'GreenManGaming': 'greenmangaming',
                    'GOG': 'gog',
                    'HumbleStore': 'humblestore',
                    'Fanatical': 'fanatical',
                    'GamesPlanet': 'gamesplanet'
                }
                
                # SQL Query dynamisch aufbauen
                columns = ['steam_app_id', 'game_title', 'timestamp']
                values = [steam_app_id, game_title, datetime.now().isoformat()]
                placeholders = ['?', '?', '?']
                
                # Preise für alle Stores hinzufügen
                for store_name, db_prefix in store_mapping.items():
                    if store_name in prices:
                        price_info = prices[store_name]
                        
                        # Preis
                        columns.append(f'{db_prefix}_price')
                        values.append(price_info.get('price'))
                        placeholders.append('?')
                        
                        # Original Preis
                        columns.append(f'{db_prefix}_original_price')
                        values.append(price_info.get('original_price'))
                        placeholders.append('?')
                        
                        # Rabatt
                        columns.append(f'{db_prefix}_discount_percent')
                        values.append(price_info.get('discount_percent', 0))
                        placeholders.append('?')
                        
                        # Verfügbarkeit
                        columns.append(f'{db_prefix}_available')
                        values.append(1 if price_info.get('available', False) else 0)
                        placeholders.append('?')
                
                query = f'''
                    INSERT INTO price_snapshots ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                '''
                
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, values)
                    conn.commit()
                    
                logger.debug(f"✅ Preis-Snapshot für {game_title} gespeichert")
                return True
                
            except sqlite3.Error as e:
                logger.error(f"❌ Fehler beim Speichern des Preis-Snapshots: {e}")
                return False
    
    def get_price_history(self, steam_app_id: str, days_back: int = 30) -> List[Dict]:
        """Gibt Preisverlauf für App zurück"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM price_snapshots
                WHERE steam_app_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            ''', (steam_app_id, cutoff_date.isoformat()))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_latest_prices(self, steam_app_id: str) -> Optional[Dict]:
        """Gibt neueste Preise für App zurück"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM price_snapshots
                WHERE steam_app_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (steam_app_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_best_deals(self, limit: int = 10) -> List[Dict]:
        """Gibt beste aktuelle Deals zurück"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Subquery für neueste Snapshots pro App
            cursor.execute('''
                WITH latest_snapshots AS (
                    SELECT steam_app_id, MAX(timestamp) as latest_timestamp
                    FROM price_snapshots
                    GROUP BY steam_app_id
                ),
                latest_prices AS (
                    SELECT ps.*
                    FROM price_snapshots ps
                    INNER JOIN latest_snapshots ls ON 
                        ps.steam_app_id = ls.steam_app_id AND 
                        ps.timestamp = ls.latest_timestamp
                )
                SELECT 
                    steam_app_id, game_title,
                    CASE 
                        WHEN steam_available = 1 AND steam_discount_percent > 0 THEN 'Steam'
                        WHEN greenmangaming_available = 1 AND greenmangaming_discount_percent > 0 THEN 'GreenManGaming'
                        WHEN gog_available = 1 AND gog_discount_percent > 0 THEN 'GOG'
                        WHEN humblestore_available = 1 AND humblestore_discount_percent > 0 THEN 'HumbleStore'
                        WHEN fanatical_available = 1 AND fanatical_discount_percent > 0 THEN 'Fanatical'
                        WHEN gamesplanet_available = 1 AND gamesplanet_discount_percent > 0 THEN 'GamesPlanet'
                    END as best_store,
                    CASE 
                        WHEN steam_available = 1 AND steam_discount_percent > 0 THEN steam_price
                        WHEN greenmangaming_available = 1 AND greenmangaming_discount_percent > 0 THEN greenmangaming_price
                        WHEN gog_available = 1 AND gog_discount_percent > 0 THEN gog_price
                        WHEN humblestore_available = 1 AND humblestore_discount_percent > 0 THEN humblestore_price
                        WHEN fanatical_available = 1 AND fanatical_discount_percent > 0 THEN fanatical_price
                        WHEN gamesplanet_available = 1 AND gamesplanet_discount_percent > 0 THEN gamesplanet_price
                    END as best_price,
                    CASE 
                        WHEN steam_available = 1 AND steam_discount_percent > 0 THEN steam_discount_percent
                        WHEN greenmangaming_available = 1 AND greenmangaming_discount_percent > 0 THEN greenmangaming_discount_percent
                        WHEN gog_available = 1 AND gog_discount_percent > 0 THEN gog_discount_percent
                        WHEN humblestore_available = 1 AND humblestore_discount_percent > 0 THEN humblestore_discount_percent
                        WHEN fanatical_available = 1 AND fanatical_discount_percent > 0 THEN fanatical_discount_percent
                        WHEN gamesplanet_available = 1 AND gamesplanet_discount_percent > 0 THEN gamesplanet_discount_percent
                    END as discount_percent
                FROM latest_prices
                WHERE best_store IS NOT NULL
                ORDER BY discount_percent DESC
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ========================
    # STATISTICS AND MAINTENANCE
    # ========================
    
    def get_statistics(self) -> Dict:
        """Gibt Tracker-Statistiken zurück"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tracked Apps
            cursor.execute("SELECT COUNT(*) FROM tracked_apps WHERE active = 1")
            tracked_apps = cursor.fetchone()[0]
            
            # Total Snapshots
            cursor.execute("SELECT COUNT(*) FROM price_snapshots")
            total_snapshots = cursor.fetchone()[0]
            
            # Stores die Daten haben
            stores_with_data = []
            store_columns = ['steam', 'greenmangaming', 'gog', 'humblestore', 'fanatical', 'gamesplanet']
            for store in store_columns:
                cursor.execute(f"SELECT COUNT(*) FROM price_snapshots WHERE {store}_available = 1")
                if cursor.fetchone()[0] > 0:
                    stores_with_data.append(store.title())
            
            # Ältester/Neuester Snapshot
            cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM price_snapshots")
            oldest, newest = cursor.fetchone()
            
            return {
                'tracked_apps': tracked_apps,
                'total_snapshots': total_snapshots,
                'stores_tracked': stores_with_data,
                'oldest_snapshot': oldest,
                'newest_snapshot': newest
            }
    
    def get_total_price_snapshots(self) -> int:
        """Gibt Gesamtzahl der Preis-Snapshots zurück"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM price_snapshots")
            return cursor.fetchone()[0]
    
    def cleanup_old_prices(self, days: int = 90):
        """Bereinigt alte Preis-Snapshots"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        DELETE FROM price_snapshots 
                        WHERE timestamp < ?
                    ''', (cutoff_date.isoformat(),))
                    
                    deleted_count = cursor.rowcount
                    conn.commit()
                    
                    logger.info(f"✅ {deleted_count} alte Preis-Snapshots bereinigt (älter als {days} Tage)")
                    return deleted_count
                    
            except sqlite3.Error as e:
                logger.error(f"❌ Fehler beim Bereinigen alter Preise: {e}")
                return 0
    
    def vacuum_database(self):
        """Optimiert die Datenbank"""
        with self.lock:
            try:
                with self.get_connection() as conn:
                    conn.execute("VACUUM")
                    logger.info("✅ Datenbank optimiert (VACUUM)")
            except sqlite3.Error as e:
                logger.error(f"❌ Fehler beim VACUUM: {e}")
    
    def backup_database(self, backup_dir: str = "backups") -> Optional[str]:
        """Erstellt Datenbank-Backup"""
        try:
            backup_path = Path(backup_dir)
            backup_path.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_path / f"steam_price_tracker_backup_{timestamp}.db"
            
            shutil.copy2(self.db_path, backup_file)
            logger.info(f"✅ Datenbank-Backup erstellt: {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            logger.error(f"❌ Backup fehlgeschlagen: {e}")
            return None