"""
Database Manager für Steam Price Tracker
Vollständige Implementation für Preis-Tracking mit App-Namen Updates und Charts-Funktionalität
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
    Vollständige Implementation mit allen benötigten Methoden inkl. Charts-Funktionalität
    """
    
    def __init__(self, db_path: str = "steam_price_tracker.db"):
        self.db_path = Path(db_path)
        self.lock = threading.Lock()
        self._init_database()
        self.init_charts_tables()  # Charts-Tabellen initialisieren
    
    def get_connection(self):
        """Erstellt eine neue Datenbankverbindung"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """Initialisiert alle benötigten Standard-Tabellen"""
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
                            last_name_update TIMESTAMP,
                            name_update_attempts INTEGER DEFAULT 0,
                            active BOOLEAN DEFAULT 1
                        )
                    ''')
                    
                    # Name Update History für Tracking
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS app_name_history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            steam_app_id TEXT NOT NULL,
                            old_name TEXT,
                            new_name TEXT NOT NULL,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            update_source TEXT DEFAULT 'manual',
                            FOREIGN KEY (steam_app_id) REFERENCES tracked_apps (steam_app_id)
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
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_name_history_app_id ON app_name_history(steam_app_id)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracked_apps_name_update ON tracked_apps(last_name_update)')
                    
                    # Upgrade bestehende Tabelle falls neue Spalten fehlen
                    try:
                        cursor.execute('ALTER TABLE tracked_apps ADD COLUMN last_name_update TIMESTAMP')
                    except sqlite3.OperationalError:
                        pass
                    
                    try:
                        cursor.execute('ALTER TABLE tracked_apps ADD COLUMN name_update_attempts INTEGER DEFAULT 0')
                    except sqlite3.OperationalError:
                        pass
                    
                    conn.commit()
                    logger.info("✅ Price Tracker Datenbank initialisiert")
                    
                except sqlite3.Error as e:
                    conn.rollback()
                    raise Exception(f"Datenbank-Initialisierung fehlgeschlagen: {e}")

    def init_charts_tables(self):
        """Initialisiert Charts-Tracking Tabellen"""
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                try:
                    # Steam Charts Tracking Tabelle
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
                            UNIQUE(steam_app_id, chart_type)
                        )
                    ''')
                    
                    # Charts History für detaillierte Tracking-Historie
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS charts_history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            steam_app_id TEXT NOT NULL,
                            chart_type TEXT NOT NULL,
                            rank_position INTEGER NOT NULL,
                            snapshot_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            additional_data TEXT,
                            FOREIGN KEY (steam_app_id) REFERENCES steam_charts_tracking (steam_app_id)
                        )
                    ''')
                    
                    # Charts Price Snapshots (separate von normalen Snapshots für bessere Performance)
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS charts_price_snapshots (
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
                            is_chart_game BOOLEAN DEFAULT 1,
                            chart_types TEXT,
                            FOREIGN KEY (steam_app_id) REFERENCES steam_charts_tracking (steam_app_id)
                        )
                    ''')
                    
                    # Indizes für Charts-Performance
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_tracking_app_id ON steam_charts_tracking(steam_app_id)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_tracking_chart_type ON steam_charts_tracking(chart_type)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_tracking_active ON steam_charts_tracking(active)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_tracking_last_seen ON steam_charts_tracking(last_seen)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_history_app_id ON charts_history(steam_app_id)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_history_timestamp ON charts_history(snapshot_timestamp)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_price_snapshots_app_id ON charts_price_snapshots(steam_app_id)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_price_snapshots_timestamp ON charts_price_snapshots(timestamp)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_price_snapshots_chart_game ON charts_price_snapshots(is_chart_game)')
                    
                    conn.commit()
                    logger.info("✅ Steam Charts Tabellen initialisiert")
                    
                except sqlite3.Error as e:
                    conn.rollback()
                    logger.warning(f"⚠️ Charts-Tabellen Initialisierung: {e}")
                    # Nicht kritisch - Charts-Funktionen werden einfach deaktiviert

    # ========================
    # APP NAME UPDATE FUNCTIONS
    # ========================
    
    def update_app_name(self, steam_app_id: str, new_name: str, update_source: str = 'manual') -> bool:
        """
        Aktualisiert den Namen einer App in der Datenbank
        
        Args:
            steam_app_id: Steam App ID
            new_name: Neuer Name der App
            update_source: Quelle des Updates (manual, steam_api, wishlist, etc.)
            
        Returns:
            True wenn erfolgreich aktualisiert
        """
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Aktuellen Namen abrufen
                    cursor.execute('SELECT name FROM tracked_apps WHERE steam_app_id = ?', (steam_app_id,))
                    result = cursor.fetchone()
                    
                    if not result:
                        logger.warning(f"⚠️ App {steam_app_id} nicht in Datenbank gefunden")
                        return False
                    
                    old_name = result['name']
                    
                    # Nur aktualisieren wenn Name wirklich unterschiedlich ist
                    if old_name.strip() == new_name.strip():
                        logger.debug(f"ℹ️ Name für {steam_app_id} unverändert: {new_name}")
                        return True
                    
                    # App-Namen aktualisieren
                    cursor.execute('''
                        UPDATE tracked_apps 
                        SET name = ?, 
                            last_name_update = CURRENT_TIMESTAMP,
                            name_update_attempts = name_update_attempts + 1
                        WHERE steam_app_id = ?
                    ''', (new_name, steam_app_id))
                    
                    # Historie-Eintrag erstellen
                    cursor.execute('''
                        INSERT INTO app_name_history (steam_app_id, old_name, new_name, update_source)
                        VALUES (?, ?, ?, ?)
                    ''', (steam_app_id, old_name, new_name, update_source))
                    
                    conn.commit()
                    logger.info(f"✅ Name aktualisiert für {steam_app_id}: '{old_name}' → '{new_name}'")
                    return True
                    
            except sqlite3.Error as e:
                logger.error(f"❌ Fehler beim Aktualisieren des App-Namens {steam_app_id}: {e}")
                return False
    
    def get_apps_needing_name_update(self, hours_threshold: int = 168) -> List[Dict]:
        """
        Gibt Apps zurück die ein Namen-Update benötigen
        
        Args:
            hours_threshold: Apps älter als X Stunden (Standard: 1 Woche)
            
        Returns:
            Liste von Apps die Namen-Updates benötigen
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_threshold)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT steam_app_id, name, added_at, last_name_update, name_update_attempts
                FROM tracked_apps
                WHERE active = 1 
                AND (
                    last_name_update IS NULL 
                    OR last_name_update < ?
                    OR name LIKE 'Game %'
                    OR name LIKE 'Unknown Game %'
                    OR name = ''
                )
                ORDER BY 
                    CASE 
                        WHEN name LIKE 'Game %' OR name LIKE 'Unknown Game %' OR name = '' THEN 0
                        WHEN last_name_update IS NULL THEN 1 
                        ELSE 2 
                    END,
                    last_name_update ASC
            ''', (cutoff_time.isoformat(),))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_apps_with_generic_names(self) -> List[Dict]:
        """
        Gibt Apps mit generischen Namen zurück (Game XXXXX, Unknown Game, etc.)
        
        Returns:
            Liste von Apps mit generischen Namen
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT steam_app_id, name, added_at, last_name_update, name_update_attempts
                FROM tracked_apps
                WHERE active = 1 
                AND (
                    name LIKE 'Game %'
                    OR name LIKE 'Unknown Game %'
                    OR name = ''
                    OR name IS NULL
                )
                ORDER BY added_at DESC
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_name_update_history(self, steam_app_id: str = None, limit: int = 50) -> List[Dict]:
        """
        Gibt Historie der Namen-Updates zurück
        
        Args:
            steam_app_id: Optionale Filterung nach App ID
            limit: Maximale Anzahl Ergebnisse
            
        Returns:
            Liste von Namen-Update Einträgen
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if steam_app_id:
                cursor.execute('''
                    SELECT anh.*, ta.name as current_name
                    FROM app_name_history anh
                    LEFT JOIN tracked_apps ta ON anh.steam_app_id = ta.steam_app_id
                    WHERE anh.steam_app_id = ?
                    ORDER BY anh.updated_at DESC
                    LIMIT ?
                ''', (steam_app_id, limit))
            else:
                cursor.execute('''
                    SELECT anh.*, ta.name as current_name
                    FROM app_name_history anh
                    LEFT JOIN tracked_apps ta ON anh.steam_app_id = ta.steam_app_id
                    ORDER BY anh.updated_at DESC
                    LIMIT ?
                ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_name_update_statistics(self) -> Dict:
        """
        Gibt Statistiken zu Namen-Updates zurück
        
        Returns:
            Dict mit Namen-Update Statistiken
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Apps mit generischen Namen
            cursor.execute('''
                SELECT COUNT(*) FROM tracked_apps 
                WHERE active = 1 AND (
                    name LIKE 'Game %' OR 
                    name LIKE 'Unknown Game %' OR 
                    name = '' OR 
                    name IS NULL
                )
            ''')
            apps_with_generic_names = cursor.fetchone()[0]
            
            # Apps die noch nie Namen-Update hatten
            cursor.execute('''
                SELECT COUNT(*) FROM tracked_apps 
                WHERE active = 1 AND last_name_update IS NULL
            ''')
            apps_never_updated = cursor.fetchone()[0]
            
            # Gesamt Namen-Updates
            cursor.execute('SELECT COUNT(*) FROM app_name_history')
            total_name_updates = cursor.fetchone()[0]
            
            # Namen-Updates letzte 24h
            yesterday = datetime.now() - timedelta(hours=24)
            cursor.execute('''
                SELECT COUNT(*) FROM app_name_history 
                WHERE updated_at >= ?
            ''', (yesterday.isoformat(),))
            updates_last_24h = cursor.fetchone()[0]
            
            # Apps mit fehlgeschlagenen Updates (>3 Versuche)
            cursor.execute('''
                SELECT COUNT(*) FROM tracked_apps 
                WHERE active = 1 AND name_update_attempts > 3
                AND (name LIKE 'Game %' OR name LIKE 'Unknown Game %')
            ''')
            failed_updates = cursor.fetchone()[0]
            
            return {
                'apps_with_generic_names': apps_with_generic_names,
                'apps_never_updated': apps_never_updated,
                'total_name_updates': total_name_updates,
                'updates_last_24h': updates_last_24h,
                'failed_updates': failed_updates
            }

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
                SELECT steam_app_id, name, added_at, last_price_update, last_name_update, name_update_attempts, active
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
    # CHARTS EXTENSION METHODS
    # ========================

    def add_chart_game(self, steam_app_id: str, name: str, chart_type: str, rank: int = 0, metadata: dict = None) -> bool:
        """
        Fügt Spiel zum Charts-Tracking hinzu
        
        Args:
            steam_app_id: Steam App ID
            name: Name des Spiels
            chart_type: Typ des Charts (most_played, top_releases, etc.)
            rank: Aktuelle Position im Chart
            metadata: Zusätzliche Metadaten als Dict
            
        Returns:
            True wenn erfolgreich hinzugefügt
        """
        with self.lock:
            try:
                metadata_json = json.dumps(metadata) if metadata else None
                
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT OR IGNORE INTO steam_charts_tracking 
                        (steam_app_id, name, chart_type, current_rank, best_rank, metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (steam_app_id, name, chart_type, rank, rank, metadata_json))
                    
                    # Charts History Eintrag
                    cursor.execute('''
                        INSERT INTO charts_history 
                        (steam_app_id, chart_type, rank_position, additional_data)
                        VALUES (?, ?, ?, ?)
                    ''', (steam_app_id, chart_type, rank, metadata_json))
                    
                    conn.commit()
                    
                    if cursor.rowcount > 0:
                        logger.debug(f"✅ Charts-Spiel {name} ({steam_app_id}) zu {chart_type} hinzugefügt")
                        return True
                    else:
                        logger.debug(f"ℹ️ Charts-Spiel {steam_app_id} bereits in {chart_type}")
                        return True
                        
            except sqlite3.Error as e:
                logger.error(f"❌ Fehler beim Hinzufügen des Charts-Spiels {steam_app_id}: {e}")
                return False

    def update_chart_game(self, steam_app_id: str, chart_type: str, rank: int, name: str = None, metadata: dict = None) -> bool:
        """
        Aktualisiert Charts-Spiel Eintrag
        
        Args:
            steam_app_id: Steam App ID
            chart_type: Chart-Typ
            rank: Neue Position
            name: Neuer Name (optional)
            metadata: Neue Metadaten (optional)
            
        Returns:
            True wenn erfolgreich aktualisiert
        """
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Aktuellen Eintrag holen für best_rank Vergleich
                    cursor.execute('''
                        SELECT best_rank, name FROM steam_charts_tracking 
                        WHERE steam_app_id = ? AND chart_type = ?
                    ''', (steam_app_id, chart_type))
                    
                    result = cursor.fetchone()
                    if not result:
                        logger.warning(f"⚠️ Charts-Spiel {steam_app_id} in {chart_type} nicht gefunden")
                        return False
                    
                    current_best_rank = result['best_rank']
                    current_name = result['name']
                    
                    # Neuen best_rank berechnen
                    new_best_rank = min(current_best_rank, rank) if rank > 0 else current_best_rank
                    
                    # Name aktualisieren falls angegeben
                    update_name = name if name else current_name
                    
                    # Metadaten als JSON
                    metadata_json = json.dumps(metadata) if metadata else None
                    
                    # Eintrag aktualisieren
                    cursor.execute('''
                        UPDATE steam_charts_tracking 
                        SET current_rank = ?, 
                            best_rank = ?, 
                            name = ?,
                            last_seen = CURRENT_TIMESTAMP,
                            total_appearances = total_appearances + 1,
                            metadata = COALESCE(?, metadata)
                        WHERE steam_app_id = ? AND chart_type = ?
                    ''', (rank, new_best_rank, update_name, metadata_json, steam_app_id, chart_type))
                    
                    # Charts History Eintrag
                    cursor.execute('''
                        INSERT INTO charts_history 
                        (steam_app_id, chart_type, rank_position, additional_data)
                        VALUES (?, ?, ?, ?)
                    ''', (steam_app_id, chart_type, rank, metadata_json))
                    
                    conn.commit()
                    logger.debug(f"✅ Charts-Spiel {steam_app_id} in {chart_type} aktualisiert (Rang: {rank})")
                    return True
                    
            except sqlite3.Error as e:
                logger.error(f"❌ Fehler beim Aktualisieren des Charts-Spiels {steam_app_id}: {e}")
                return False

    def get_chart_game(self, steam_app_id: str, chart_type: str) -> Optional[Dict]:
        """
        Holt Charts-Spiel Eintrag
        
        Args:
            steam_app_id: Steam App ID
            chart_type: Chart-Typ
            
        Returns:
            Charts-Spiel Dict oder None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM steam_charts_tracking
                WHERE steam_app_id = ? AND chart_type = ? AND active = 1
            ''', (steam_app_id, chart_type))
            
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_active_chart_games(self, chart_type: str = None) -> List[Dict]:
        """
        Gibt aktive Charts-Spiele zurück
        
        Args:
            chart_type: Optionale Filterung nach Chart-Typ
            
        Returns:
            Liste der aktiven Charts-Spiele
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if chart_type:
                cursor.execute('''
                    SELECT * FROM steam_charts_tracking
                    WHERE chart_type = ? AND active = 1
                    ORDER BY current_rank ASC, last_seen DESC
                ''', (chart_type,))
            else:
                cursor.execute('''
                    SELECT * FROM steam_charts_tracking
                    WHERE active = 1
                    ORDER BY chart_type, current_rank ASC
                ''')
            
            return [dict(row) for row in cursor.fetchall()]

    def get_chart_games_needing_price_update(self, hours_threshold: int = 4) -> List[Dict]:
        """
        Gibt Charts-Spiele zurück die Preis-Updates benötigen
        
        Args:
            hours_threshold: Stunden-Schwelle für veraltete Preise
            
        Returns:
            Liste der Charts-Spiele die Updates benötigen
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_threshold)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT sct.steam_app_id, sct.name, sct.chart_type
                FROM steam_charts_tracking sct
                LEFT JOIN charts_price_snapshots cps ON sct.steam_app_id = cps.steam_app_id
                WHERE sct.active = 1 
                AND (cps.timestamp IS NULL OR cps.timestamp < ?)
                ORDER BY 
                    CASE WHEN cps.timestamp IS NULL THEN 0 ELSE 1 END,
                    cps.timestamp ASC
            ''', (cutoff_time.isoformat(),))
            
            return [dict(row) for row in cursor.fetchall()]

    def save_charts_price_snapshot(self, steam_app_id: str, game_title: str, prices: Dict, chart_types: List[str] = None) -> bool:
        """
        Speichert Preis-Snapshot für Charts-Spiel
        
        Args:
            steam_app_id: Steam App ID
            game_title: Spielname
            prices: Preisdaten Dictionary
            chart_types: Liste der Chart-Typen für dieses Spiel
            
        Returns:
            True wenn erfolgreich gespeichert
        """
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
                columns = ['steam_app_id', 'game_title', 'timestamp', 'is_chart_game']
                values = [steam_app_id, game_title, datetime.now().isoformat(), 1]
                placeholders = ['?', '?', '?', '?']
                
                # Chart-Typen als JSON speichern
                if chart_types:
                    columns.append('chart_types')
                    values.append(json.dumps(chart_types))
                    placeholders.append('?')
                
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
                    INSERT INTO charts_price_snapshots ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                '''
                
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, values)
                    conn.commit()
                    
                logger.debug(f"✅ Charts-Preis-Snapshot für {game_title} gespeichert")
                return True
                
            except sqlite3.Error as e:
                logger.error(f"❌ Fehler beim Speichern des Charts-Preis-Snapshots: {e}")
                return False

    def get_charts_price_history(self, steam_app_id: str, days_back: int = 30) -> List[Dict]:
        """
        Gibt Charts-Preisverlauf zurück
        
        Args:
            steam_app_id: Steam App ID
            days_back: Tage zurück
            
        Returns:
            Liste der Charts-Preis-Snapshots
        """
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM charts_price_snapshots
                WHERE steam_app_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            ''', (steam_app_id, cutoff_date.isoformat()))
            
            return [dict(row) for row in cursor.fetchall()]

    def get_charts_best_deals(self, limit: int = 20, chart_type: str = None) -> List[Dict]:
        """
        Gibt beste Charts-Deals zurück
        
        Args:
            limit: Anzahl Deals
            chart_type: Optionale Filterung nach Chart-Typ
            
        Returns:
            Liste der besten Charts-Deals
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Basis-Query für Charts-Deals
            base_query = '''
                WITH latest_charts_snapshots AS (
                    SELECT steam_app_id, MAX(timestamp) as latest_timestamp
                    FROM charts_price_snapshots
                    WHERE is_chart_game = 1
                    GROUP BY steam_app_id
                ),
                latest_charts_prices AS (
                    SELECT cps.*, sct.chart_type, sct.current_rank
                    FROM charts_price_snapshots cps
                    INNER JOIN latest_charts_snapshots lcs ON 
                        cps.steam_app_id = lcs.steam_app_id AND 
                        cps.timestamp = lcs.latest_timestamp
                    INNER JOIN steam_charts_tracking sct ON cps.steam_app_id = sct.steam_app_id
                    WHERE sct.active = 1
            '''
            
            if chart_type:
                base_query += " AND sct.chart_type = ?"
                params = [chart_type]
            else:
                params = []
            
            base_query += '''
                )
                SELECT 
                    steam_app_id, game_title, chart_type, current_rank,
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
                FROM latest_charts_prices
                WHERE best_store IS NOT NULL
                ORDER BY discount_percent DESC, current_rank ASC
                LIMIT ?
            '''
            
            params.append(limit)
            cursor.execute(base_query, params)
            
            return [dict(row) for row in cursor.fetchall()]

    def cleanup_old_chart_games(self, days_threshold: int = 30) -> int:
        """
        Entfernt Charts-Spiele die zu lange nicht mehr in Charts waren
        
        Args:
            days_threshold: Tage nach denen Spiele deaktiviert werden
            
        Returns:
            Anzahl deaktivierter Spiele
        """
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Charts-Spiele deaktivieren (nicht löschen für Historie)
                    cursor.execute('''
                        UPDATE steam_charts_tracking 
                        SET active = 0 
                        WHERE last_seen < ? AND active = 1
                    ''', (cutoff_date.isoformat(),))
                    
                    deactivated_count = cursor.rowcount
                    
                    # Alte Charts-Preis-Snapshots löschen (älter als 90 Tage)
                    old_price_cutoff = datetime.now() - timedelta(days=90)
                    cursor.execute('''
                        DELETE FROM charts_price_snapshots 
                        WHERE timestamp < ?
                    ''', (old_price_cutoff.isoformat(),))
                    
                    deleted_snapshots = cursor.rowcount
                    
                    # Alte Charts-Historie bereinigen (älter als 180 Tage)
                    old_history_cutoff = datetime.now() - timedelta(days=180)
                    cursor.execute('''
                        DELETE FROM charts_history 
                        WHERE snapshot_timestamp < ?
                    ''', (old_history_cutoff.isoformat(),))
                    
                    deleted_history = cursor.rowcount
                    
                    conn.commit()
                    
                    logger.info(f"✅ Charts-Cleanup: {deactivated_count} Spiele deaktiviert, {deleted_snapshots} Snapshots gelöscht, {deleted_history} Historie-Einträge entfernt")
                    return deactivated_count
                    
            except sqlite3.Error as e:
                logger.error(f"❌ Fehler beim Charts-Cleanup: {e}")
                return 0

    def get_charts_statistics(self) -> Dict:
        """
        Gibt Charts-Tracking Statistiken zurück
        
        Returns:
            Dict mit Charts-Statistiken
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Aktive Charts-Spiele pro Typ
            cursor.execute('''
                SELECT chart_type, COUNT(*) as count
                FROM steam_charts_tracking
                WHERE active = 1
                GROUP BY chart_type
            ''')
            
            chart_type_stats = {}
            for row in cursor.fetchall():
                chart_type_stats[row['chart_type']] = row['count']
            
            stats['active_games_by_chart'] = chart_type_stats
            
            # Gesamt aktive Spiele
            cursor.execute('SELECT COUNT(*) FROM steam_charts_tracking WHERE active = 1')
            stats['total_active_charts_games'] = cursor.fetchone()[0]
            
            # Unique Apps in Charts
            cursor.execute('SELECT COUNT(DISTINCT steam_app_id) FROM steam_charts_tracking WHERE active = 1')
            stats['unique_apps_in_charts'] = cursor.fetchone()[0]
            
            # Charts-Preis-Snapshots
            cursor.execute('SELECT COUNT(*) FROM charts_price_snapshots')
            stats['total_charts_price_snapshots'] = cursor.fetchone()[0]
            
            # Neuester/Ältester Charts-Snapshot
            cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM charts_price_snapshots')
            oldest_snapshot, newest_snapshot = cursor.fetchone()
            stats['oldest_charts_snapshot'] = oldest_snapshot
            stats['newest_charts_snapshot'] = newest_snapshot
            
            # Apps mit Charts-Preisdaten heute
            today = datetime.now().date().isoformat()
            cursor.execute('''
                SELECT COUNT(DISTINCT steam_app_id) 
                FROM charts_price_snapshots 
                WHERE date(timestamp) = ?
            ''', (today,))
            stats['apps_with_price_updates_today'] = cursor.fetchone()[0]
            
            # Durchschnittliche Tage in Charts
            cursor.execute('''
                SELECT AVG(julianday('now') - julianday(first_seen)) as avg_days
                FROM steam_charts_tracking
                WHERE active = 1
            ''')
            avg_days = cursor.fetchone()[0]
            stats['average_days_in_charts'] = round(avg_days, 1) if avg_days else 0
            
            return stats

    # ========================
    # STATISTICS AND MAINTENANCE
    # ========================
    
    def get_statistics(self) -> Dict:
        """Gibt erweiterte Tracker-Statistiken zurück"""
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
            
            # Namen-Update Statistiken
            name_stats = self.get_name_update_statistics()
            
            # Charts-Statistiken (falls verfügbar)
            try:
                charts_stats = self.get_charts_statistics()
            except sqlite3.OperationalError:
                # Charts-Tabellen existieren nicht
                charts_stats = None
            
            base_stats = {
                'tracked_apps': tracked_apps,
                'total_snapshots': total_snapshots,
                'stores_tracked': stores_with_data,
                'oldest_snapshot': oldest,
                'newest_snapshot': newest,
                'name_update_stats': name_stats
            }
            
            if charts_stats:
                base_stats['charts_stats'] = charts_stats
            
            return base_stats
    
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
    
    def export_all_price_data(self, output_file: str = None) -> Optional[str]:
        """Exportiert alle Preisdaten als JSON"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"exports/all_price_data_{timestamp}.json"
        
        try:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Alle Daten sammeln
                export_data = {
                    'export_timestamp': datetime.now().isoformat(),
                    'tracked_apps': [],
                    'price_snapshots': [],
                    'name_history': []
                }
                
                # Tracked Apps
                cursor.execute('SELECT * FROM tracked_apps WHERE active = 1')
                export_data['tracked_apps'] = [dict(row) for row in cursor.fetchall()]
                
                # Price Snapshots (nur letzte 90 Tage)
                cutoff_date = datetime.now() - timedelta(days=90)
                cursor.execute('SELECT * FROM price_snapshots WHERE timestamp >= ? ORDER BY timestamp DESC', 
                              (cutoff_date.isoformat(),))
                export_data['price_snapshots'] = [dict(row) for row in cursor.fetchall()]
                
                # Name History
                cursor.execute('SELECT * FROM app_name_history ORDER BY updated_at DESC LIMIT 1000')
                export_data['name_history'] = [dict(row) for row in cursor.fetchall()]
                
                # Charts-Daten (falls verfügbar)
                try:
                    cursor.execute('SELECT * FROM steam_charts_tracking WHERE active = 1')
                    export_data['charts_games'] = [dict(row) for row in cursor.fetchall()]
                    
                    cursor.execute('SELECT * FROM charts_price_snapshots WHERE timestamp >= ? ORDER BY timestamp DESC', 
                                  (cutoff_date.isoformat(),))
                    export_data['charts_price_snapshots'] = [dict(row) for row in cursor.fetchall()]
                except sqlite3.OperationalError:
                    # Charts-Tabellen existieren nicht
                    pass
            
            # JSON Export schreiben
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Vollständiger Datenexport erstellt: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"❌ Export fehlgeschlagen: {e}")
            return None