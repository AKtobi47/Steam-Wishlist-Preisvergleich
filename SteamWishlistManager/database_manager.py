"""
Database Manager für Steam Wishlist Manager - ENHANCED
Zentrale Datenbankoperationen für alle Module
ERWEITERT: Explizite Speicherung wenn kein CheapShark-Mapping existiert
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import threading

class DatabaseManager:
    """
    Zentrale Datenbank-Klasse für alle Steam/CheapShark Operationen
    Thread-safe und mit Connection Pooling
    ERWEITERT: Tracking von "kein Mapping gefunden" Status
    """
    
    def __init__(self, db_path: str = "steam_wishlist.db"):
        self.db_path = Path(db_path)
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialisiert alle benötigten Tabellen"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # Apps Tabelle (alle Steam Apps)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS steam_apps (
                        app_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        type TEXT DEFAULT 'game',
                        is_free BOOLEAN DEFAULT 0,
                        release_date TEXT,
                        developer TEXT,
                        publisher TEXT,
                        price_current REAL,
                        price_original REAL,
                        discount_percent INTEGER DEFAULT 0,
                        steam_data_updated TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # CheapShark Mappings - ERWEITERT
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cheapshark_mappings (
                        app_id TEXT PRIMARY KEY,
                        cheapshark_game_id TEXT,
                        thumb_url TEXT,
                        cheapest_price_ever REAL,
                        cheapest_store TEXT,
                        deals_count INTEGER DEFAULT 0,
                        mapping_status TEXT DEFAULT 'unknown',
                        no_mapping_found BOOLEAN DEFAULT 0,
                        mapping_updated TIMESTAMP,
                        mapping_attempts INTEGER DEFAULT 0,
                        last_attempt TIMESTAMP,
                        last_error_message TEXT,
                        FOREIGN KEY (app_id) REFERENCES steam_apps (app_id)
                    )
                ''')
                
                # Wishlist Items
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS wishlist_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        steam_id TEXT NOT NULL,
                        app_id TEXT NOT NULL,
                        priority INTEGER DEFAULT 0,
                        date_added TIMESTAMP,
                        wishlist_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (app_id) REFERENCES steam_apps (app_id),
                        UNIQUE(steam_id, app_id)
                    )
                ''')
                
                # Import Sessions (für Bulk Import Tracking)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS import_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_type TEXT NOT NULL,
                        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        items_processed INTEGER DEFAULT 0,
                        items_successful INTEGER DEFAULT 0,
                        success BOOLEAN DEFAULT 0,
                        error_message TEXT,
                        metadata TEXT
                    )
                ''')
                
                # Mapping Queue (für CheapShark Mapping Scheduler)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS mapping_queue (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        app_id TEXT NOT NULL,
                        priority INTEGER DEFAULT 5,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        processing_started TIMESTAMP,
                        completed_at TIMESTAMP,
                        status TEXT DEFAULT 'pending',
                        error_message TEXT,
                        retry_count INTEGER DEFAULT 0,
                        FOREIGN KEY (app_id) REFERENCES steam_apps (app_id),
                        UNIQUE(app_id)
                    )
                ''')
                
                # Migration: Füge neue Spalten hinzu falls sie nicht existieren
                try:
                    cursor.execute('ALTER TABLE cheapshark_mappings ADD COLUMN mapping_status TEXT DEFAULT "unknown"')
                except sqlite3.OperationalError:
                    pass  # Column already exists
                    
                try:
                    cursor.execute('ALTER TABLE cheapshark_mappings ADD COLUMN no_mapping_found BOOLEAN DEFAULT 0')
                except sqlite3.OperationalError:
                    pass  # Column already exists
                    
                try:
                    cursor.execute('ALTER TABLE cheapshark_mappings ADD COLUMN last_error_message TEXT')
                except sqlite3.OperationalError:
                    pass  # Column already exists
                
                # Indizes für Performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_steam_apps_name ON steam_apps(name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_steam_apps_updated ON steam_apps(updated_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cheapshark_game_id ON cheapshark_mappings(cheapshark_game_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cheapshark_status ON cheapshark_mappings(mapping_status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cheapshark_no_mapping ON cheapshark_mappings(no_mapping_found)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_wishlist_steam_id ON wishlist_items(steam_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_mapping_queue_status ON mapping_queue(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_mapping_queue_priority ON mapping_queue(priority DESC, added_at)')
                
                conn.commit()
                
            except sqlite3.Error as e:
                conn.rollback()
                raise Exception(f"Datenbank-Initialisierung fehlgeschlagen: {e}")
            finally:
                conn.close()
    
    def get_connection(self) -> sqlite3.Connection:
        """Erstellt eine neue Datenbankverbindung mit optimalen Einstellungen"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.row_factory = sqlite3.Row  # Dict-like access
        return conn
    
    # ========================
    # STEAM APPS OPERATIONS
    # ========================
    
    def app_exists(self, app_id: str) -> bool:
        """Prüft ob eine App bereits in der Datenbank existiert"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM steam_apps WHERE app_id = ?", (app_id,))
            return cursor.fetchone() is not None
    
    def get_app(self, app_id: str) -> Optional[Dict]:
        """Holt eine App aus der Datenbank"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM steam_apps WHERE app_id = ?", (app_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def add_app(self, app_data: Dict) -> bool:
        """Fügt eine neue App zur Datenbank hinzu - ENHANCED mit Release Date Parsing"""
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Release Date parsing verbessern
                    release_date = self._parse_release_date(app_data.get('release_date'))
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO steam_apps 
                        (app_id, name, type, is_free, release_date, developer, 
                         publisher, price_current, price_original, discount_percent,
                         steam_data_updated, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (
                        app_data.get('app_id'),
                        app_data.get('name', ''),
                        app_data.get('type', 'game'),
                        app_data.get('is_free', False),
                        release_date,
                        app_data.get('developer'),
                        app_data.get('publisher'),
                        app_data.get('price_current'),
                        app_data.get('price_original'),
                        app_data.get('discount_percent', 0),
                        datetime.now().isoformat()
                    ))
                    
                    conn.commit()
                    return True
                    
            except sqlite3.Error as e:
                print(f"❌ Fehler beim Hinzufügen der App {app_data.get('app_id')}: {e}")
                return False
    
    def _parse_release_date(self, release_date_data) -> Optional[str]:
        """
        NEUE METHODE: Parst Release Date aus verschiedenen Formaten
        Steam gibt manchmal Strings, manchmal Dicts zurück
        """
        if not release_date_data:
            return None
        
        # Wenn es ein Dict ist (von Steam Store API)
        if isinstance(release_date_data, dict):
            date_str = release_date_data.get('date')
            if not date_str:
                return None
        else:
            # Wenn es ein String ist
            date_str = str(release_date_data).strip()
        
        if not date_str or date_str.lower() in ['', 'coming soon', 'to be announced', 'tba']:
            return None
        
        # Verschiedene Datumsformate versuchen zu parsen
        date_formats = [
            '%d %b, %Y',        # "14 Nov, 2023"
            '%b %d, %Y',        # "Nov 14, 2023"  
            '%Y-%m-%d',         # "2023-11-14"
            '%d/%m/%Y',         # "14/11/2023"
            '%m/%d/%Y',         # "11/14/2023"
            '%d.%m.%Y',         # "14.11.2023"
            '%Y',               # "2023" (nur Jahr)
            '%b %Y',            # "Nov 2023"
            '%B %Y'             # "November 2023"
        ]
        
        for date_format in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, date_format)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # Wenn nichts funktioniert, versuche nur das Jahr zu extrahieren
        import re
        year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
        if year_match:
            year = year_match.group()
            return f"{year}-01-01"  # 1. Januar als Default
        
        return None
    
    def get_apps_by_release_age(self, 
                               max_age_days: int = None,
                               min_age_days: int = None,
                               limit: int = 1000) -> List[Dict]:
        """
        NEUE METHODE: Holt Apps basierend auf Release-Alter
        
        Args:
            max_age_days: Nur Apps die maximal X Tage alt sind (für "neue Apps")
            min_age_days: Nur Apps die mindestens X Tage alt sind (für "etablierte Apps")
            limit: Maximale Anzahl Ergebnisse
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            base_query = '''
                SELECT app_id, name, release_date,
                       JULIANDAY('now') - JULIANDAY(release_date) as age_days
                FROM steam_apps
                WHERE release_date IS NOT NULL AND release_date != ''
            '''
            
            params = []
            
            if max_age_days is not None:
                base_query += ' AND JULIANDAY("now") - JULIANDAY(release_date) <= ?'
                params.append(max_age_days)
            
            if min_age_days is not None:
                base_query += ' AND JULIANDAY("now") - JULIANDAY(release_date) >= ?'
                params.append(min_age_days)
            
            base_query += ' ORDER BY release_date DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(base_query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def is_app_recently_released(self, app_id: str, max_age_days: int = 30) -> bool:
        """
        NEUE METHODE: Prüft ob eine App kürzlich veröffentlicht wurde
        
        Args:
            app_id: Steam App ID
            max_age_days: Maximales Alter in Tagen (Standard: 30)
        
        Returns:
            True wenn App innerhalb der letzten X Tage veröffentlicht wurde
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT JULIANDAY('now') - JULIANDAY(release_date) as age_days
                FROM steam_apps
                WHERE app_id = ? AND release_date IS NOT NULL AND release_date != ''
            ''', (app_id,))
            
            row = cursor.fetchone()
            if row and row['age_days'] is not None:
                return row['age_days'] <= max_age_days
            
            return False  # Kein Release-Datum oder zu alt
    
    def get_recently_released_apps_without_mapping(self, 
                                                  max_age_days: int = 30,
                                                  limit: int = 1000) -> List[Dict]:
        """
        NEUE METHODE: Holt kürzlich veröffentlichte Apps ohne CheapShark-Mapping
        Diese sollten anders behandelt werden als etablierte Apps ohne Mapping
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT sa.app_id, sa.name, sa.release_date,
                       JULIANDAY('now') - JULIANDAY(sa.release_date) as age_days
                FROM steam_apps sa
                LEFT JOIN cheapshark_mappings cm ON sa.app_id = cm.app_id
                WHERE sa.release_date IS NOT NULL 
                  AND sa.release_date != ''
                  AND JULIANDAY('now') - JULIANDAY(sa.release_date) <= ?
                  AND cm.app_id IS NULL
                ORDER BY sa.release_date DESC
                LIMIT ?
            ''', (max_age_days, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def add_apps_batch(self, apps_data: List[Dict]) -> int:
        """Fügt mehrere Apps in einem Batch hinzu - ENHANCED mit Release Date Parsing"""
        with self.lock:
            added_count = 0
            
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    for app_data in apps_data:
                        try:
                            # Release Date parsing für Batch-Import
                            release_date = self._parse_release_date(app_data.get('release_date'))
                            
                            cursor.execute('''
                                INSERT OR REPLACE INTO steam_apps 
                                (app_id, name, type, is_free, release_date, steam_data_updated, updated_at)
                                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                            ''', (
                                str(app_data.get('app_id', app_data.get('appid'))),
                                app_data.get('name', ''),
                                app_data.get('type', 'game'),
                                app_data.get('is_free', False),
                                release_date,
                                datetime.now().isoformat()
                            ))
                            added_count += 1
                            
                        except sqlite3.Error as e:
                            print(f"⚠️ Fehler bei App {app_data.get('app_id', 'unknown')}: {e}")
                            continue
                    
                    conn.commit()
                    
            except sqlite3.Error as e:
                print(f"❌ Batch-Insert Fehler: {e}")
            
            return added_count
    
    def get_apps_without_cheapshark_mapping(self, limit: int = 1000) -> List[Dict]:
        """Holt Apps die noch kein CheapShark-Mapping haben (auch keine explizite "not found" Markierung)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT sa.app_id, sa.name 
                FROM steam_apps sa
                LEFT JOIN cheapshark_mappings cm ON sa.app_id = cm.app_id
                WHERE cm.app_id IS NULL
                ORDER BY sa.updated_at DESC
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_apps_without_successful_cheapshark_mapping(self, limit: int = 1000) -> List[Dict]:
        """Holt Apps die kein erfolgreiches CheapShark-Mapping haben (für Retry-Operationen)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT sa.app_id, sa.name 
                FROM steam_apps sa
                LEFT JOIN cheapshark_mappings cm ON sa.app_id = cm.app_id
                WHERE cm.app_id IS NULL OR (cm.mapping_status != 'found' AND cm.mapping_attempts < 3)
                ORDER BY sa.updated_at DESC
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ========================
    # CHEAPSHARK OPERATIONS - ERWEITERT
    # ========================
    
    def get_cheapshark_mapping(self, app_id: str) -> Optional[Dict]:
        """Holt CheapShark-Mapping für eine App"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cheapshark_mappings WHERE app_id = ?", (app_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def add_cheapshark_mapping(self, mapping_data: Dict) -> bool:
        """Fügt erfolgreiches CheapShark-Mapping hinzu"""
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO cheapshark_mappings 
                        (app_id, cheapshark_game_id, thumb_url, cheapest_price_ever,
                         cheapest_store, deals_count, mapping_status, no_mapping_found,
                         mapping_updated, mapping_attempts, last_attempt)
                        VALUES (?, ?, ?, ?, ?, ?, 'found', 0, CURRENT_TIMESTAMP, 
                                COALESCE((SELECT mapping_attempts FROM cheapshark_mappings WHERE app_id = ?), 0) + 1,
                                CURRENT_TIMESTAMP)
                    ''', (
                        mapping_data.get('app_id'),
                        mapping_data.get('cheapshark_game_id'),
                        mapping_data.get('thumb_url'),
                        mapping_data.get('cheapest_price_ever'),
                        mapping_data.get('cheapest_store'),
                        mapping_data.get('deals_count', 0),
                        mapping_data.get('app_id')  # For the subquery
                    ))
                    
                    conn.commit()
                    return True
                    
            except sqlite3.Error as e:
                print(f"❌ Fehler beim CheapShark-Mapping für App {mapping_data.get('app_id')}: {e}")
                return False
    
    def mark_cheapshark_no_mapping_found(self, app_id: str) -> bool:
        """ERWEITERTE METHODE: Markiert dass kein CheapShark-Mapping gefunden wurde - MIT RELEASE DATE LOGIC"""
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Prüfe ob App kürzlich veröffentlicht wurde
                    is_recent = self.is_app_recently_released(app_id, max_age_days=30)
                    
                    if is_recent:
                        # Neue App - markiere als "too_new" statt "not_found"
                        cursor.execute('''
                            INSERT OR REPLACE INTO cheapshark_mappings 
                            (app_id, cheapshark_game_id, thumb_url, cheapest_price_ever,
                             cheapest_store, deals_count, mapping_status, no_mapping_found,
                             mapping_updated, mapping_attempts, last_attempt)
                            VALUES (?, NULL, NULL, NULL, NULL, 0, 'too_new', 0, 
                                    CURRENT_TIMESTAMP,
                                    COALESCE((SELECT mapping_attempts FROM cheapshark_mappings WHERE app_id = ?), 0) + 1,
                                    CURRENT_TIMESTAMP)
                        ''', (app_id, app_id))
                        
                        print(f"📅 App {app_id}: Zu neu für CheapShark-Mapping (< 30 Tage alt)")
                        return True
                    else:
                        # Etablierte App - normales "not_found"
                        cursor.execute('''
                            INSERT OR REPLACE INTO cheapshark_mappings 
                            (app_id, cheapshark_game_id, thumb_url, cheapest_price_ever,
                             cheapest_store, deals_count, mapping_status, no_mapping_found,
                             mapping_updated, mapping_attempts, last_attempt)
                            VALUES (?, NULL, NULL, NULL, NULL, 0, 'not_found', 1, 
                                    CURRENT_TIMESTAMP,
                                    COALESCE((SELECT mapping_attempts FROM cheapshark_mappings WHERE app_id = ?), 0) + 1,
                                    CURRENT_TIMESTAMP)
                        ''', (app_id, app_id))
                        
                        print(f"📝 App {app_id}: Kein CheapShark-Mapping gefunden (gespeichert)")
                        return True
                    
                    conn.commit()
                    
            except sqlite3.Error as e:
                print(f"❌ Fehler beim Markieren 'kein Mapping' für App {app_id}: {e}")
                return False
    
    def get_apps_too_new_for_retry(self, 
                                  min_age_days: int = 60,
                                  limit: int = 1000) -> List[Dict]:
        """
        NEUE METHODE: Holt Apps die als "too_new" markiert sind und jetzt alt genug für Retry
        
        Args:
            min_age_days: Apps müssen mindesten X Tage alt sein für Retry
            limit: Maximale Anzahl Ergebnisse
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT sa.app_id, sa.name, sa.release_date,
                       JULIANDAY('now') - JULIANDAY(sa.release_date) as age_days,
                       cm.mapping_attempts, cm.last_attempt
                FROM steam_apps sa
                JOIN cheapshark_mappings cm ON sa.app_id = cm.app_id
                WHERE cm.mapping_status = 'too_new'
                  AND sa.release_date IS NOT NULL
                  AND JULIANDAY('now') - JULIANDAY(sa.release_date) >= ?
                ORDER BY sa.release_date ASC
                LIMIT ?
            ''', (min_age_days, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_cheapshark_attempt_failed(self, app_id: str, error_message: str = None):
        """Markiert einen fehlgeschlagenen CheapShark-Mapping Versuch (API-Fehler, etc.)"""
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO cheapshark_mappings 
                        (app_id, cheapshark_game_id, thumb_url, cheapest_price_ever,
                         cheapest_store, deals_count, mapping_status, no_mapping_found,
                         mapping_updated, mapping_attempts, last_attempt, last_error_message)
                        VALUES (?, NULL, NULL, NULL, NULL, 0, 'failed', 0,
                                CURRENT_TIMESTAMP,
                                COALESCE((SELECT mapping_attempts FROM cheapshark_mappings WHERE app_id = ?), 0) + 1,
                                CURRENT_TIMESTAMP, ?)
                    ''', (app_id, app_id, error_message))
                    
                    conn.commit()
                    
            except sqlite3.Error as e:
                print(f"❌ Fehler beim Markieren des fehlgeschlagenen Versuchs für App {app_id}: {e}")
    
    def has_cheapshark_mapping_been_attempted(self, app_id: str) -> Dict:
        """Prüft ob für eine App bereits ein CheapShark-Mapping versucht wurde"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT mapping_status, no_mapping_found, mapping_attempts, last_attempt
                FROM cheapshark_mappings 
                WHERE app_id = ?
            ''', (app_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'attempted': True,
                    'status': row['mapping_status'],
                    'no_mapping_found': bool(row['no_mapping_found']),
                    'attempts': row['mapping_attempts'],
                    'last_attempt': row['last_attempt']
                }
            else:
                return {'attempted': False}
    
    def get_apps_by_mapping_status(self, statuses: List[str], limit: int = 1000) -> List[Dict]:
        """
        NEUE METHODE: Holt Apps mit bestimmten CheapShark-Mapping Status
        Args:
            statuses: Liste von Status ['found', 'not_found', 'failed', 'unknown']
            limit: Maximale Anzahl Ergebnisse
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Erstelle Platzhalter für IN-Klausel
            placeholders = ','.join('?' * len(statuses))
            
            cursor.execute(f'''
                SELECT sa.app_id, sa.name, cm.mapping_status, cm.no_mapping_found,
                       cm.mapping_attempts, cm.last_attempt, cm.last_error_message
                FROM steam_apps sa
                JOIN cheapshark_mappings cm ON sa.app_id = cm.app_id
                WHERE cm.mapping_status IN ({placeholders})
                ORDER BY cm.last_attempt DESC
                LIMIT ?
            ''', (*statuses, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_apps_with_no_mapping_found(self, limit: int = 1000, older_than_days: int = None) -> List[Dict]:
        """
        NEUE METHODE: Holt Apps die als 'kein Mapping gefunden' markiert sind
        Args:
            limit: Maximale Anzahl Ergebnisse
            older_than_days: Nur Apps deren letzter Versuch älter als X Tage ist
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            base_query = '''
                SELECT sa.app_id, sa.name, cm.mapping_attempts, cm.last_attempt
                FROM steam_apps sa
                JOIN cheapshark_mappings cm ON sa.app_id = cm.app_id
                WHERE cm.no_mapping_found = 1
            '''
            
            params = []
            
            if older_than_days:
                cutoff_date = datetime.now() - timedelta(days=older_than_days)
                base_query += ' AND cm.last_attempt < ?'
                params.append(cutoff_date.isoformat())
            
            base_query += ' ORDER BY cm.last_attempt ASC LIMIT ?'
            params.append(limit)
            
            cursor.execute(base_query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_apps_by_custom_criteria(self, 
                                   mapping_status: List[str] = None,
                                   no_mapping_found: bool = None,
                                   min_attempts: int = None,
                                   max_attempts: int = None,
                                   older_than_days: int = None,
                                   limit: int = 1000) -> List[Dict]:
        """
        NEUE METHODE: Flexible Suche nach Apps mit benutzerdefinierten Kriterien
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            base_query = '''
                SELECT sa.app_id, sa.name, cm.mapping_status, cm.no_mapping_found,
                       cm.mapping_attempts, cm.last_attempt, cm.last_error_message
                FROM steam_apps sa
                JOIN cheapshark_mappings cm ON sa.app_id = cm.app_id
                WHERE 1=1
            '''
            
            params = []
            
            if mapping_status:
                placeholders = ','.join('?' * len(mapping_status))
                base_query += f' AND cm.mapping_status IN ({placeholders})'
                params.extend(mapping_status)
            
            if no_mapping_found is not None:
                base_query += ' AND cm.no_mapping_found = ?'
                params.append(1 if no_mapping_found else 0)
            
            if min_attempts is not None:
                base_query += ' AND cm.mapping_attempts >= ?'
                params.append(min_attempts)
            
            if max_attempts is not None:
                base_query += ' AND cm.mapping_attempts <= ?'
                params.append(max_attempts)
            
            if older_than_days:
                cutoff_date = datetime.now() - timedelta(days=older_than_days)
                base_query += ' AND cm.last_attempt < ?'
                params.append(cutoff_date.isoformat())
            
            base_query += ' ORDER BY cm.last_attempt ASC LIMIT ?'
            params.append(limit)
            
            cursor.execute(base_query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def reset_cheapshark_mapping_status(self, app_ids: List[str], reason: str = "Manual retry") -> int:
        """
        NEUE METHODE: Setzt CheapShark-Mapping Status für Apps zurück (für Retry)
        Löscht den Mapping-Eintrag, damit die App erneut verarbeitet werden kann
        """
        if not app_ids:
            return 0
        
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    reset_count = 0
                    for app_id in app_ids:
                        cursor.execute('''
                            DELETE FROM cheapshark_mappings 
                            WHERE app_id = ?
                        ''', (app_id,))
                        
                        if cursor.rowcount > 0:
                            reset_count += 1
                    
                    conn.commit()
                    
                    if reset_count > 0:
                        print(f"🔄 {reset_count} CheapShark-Mappings zurückgesetzt für Retry")
                        print(f"   Grund: {reason}")
                    
                    return reset_count
                    
            except sqlite3.Error as e:
                print(f"❌ Fehler beim Zurücksetzen der Mappings: {e}")
                return 0
    
    def bulk_reset_by_criteria(self, 
                              mapping_status: List[str] = None,
                              no_mapping_found: bool = None,
                              older_than_days: int = None,
                              max_attempts: int = None,
                              reason: str = "Bulk retry") -> int:
        """
        NEUE METHODE: Massenweises Zurücksetzen von CheapShark-Mappings nach Kriterien
        """
        # Erstmal die Apps finden die zurückgesetzt werden sollen
        apps_to_reset = self.get_apps_by_custom_criteria(
            mapping_status=mapping_status,
            no_mapping_found=no_mapping_found,
            older_than_days=older_than_days,
            max_attempts=max_attempts,
            limit=50000  # Große Zahl für "alle"
        )
        
        if not apps_to_reset:
            print("📭 Keine Apps gefunden die den Kriterien entsprechen")
            return 0
        
        print(f"🔍 {len(apps_to_reset)} Apps gefunden die den Kriterien entsprechen:")
        if mapping_status:
            print(f"   Status: {', '.join(mapping_status)}")
        if no_mapping_found is not None:
            print(f"   Kein Mapping: {'Ja' if no_mapping_found else 'Nein'}")
        if older_than_days:
            print(f"   Älter als: {older_than_days} Tage")
        if max_attempts:
            print(f"   Max Versuche: {max_attempts}")
        
        # Bestätigung anfordern
        confirm = input(f"\n🤔 {len(apps_to_reset)} Apps für Retry zurücksetzen? (j/n): ").strip().lower()
        if confirm not in ['j', 'ja', 'y', 'yes']:
            print("❌ Abgebrochen")
            return 0
        
        # Apps zurücksetzen
        app_ids = [app['app_id'] for app in apps_to_reset]
        return self.reset_cheapshark_mapping_status(app_ids, reason)
    
    # ========================
    # WISHLIST OPERATIONS  
    # ========================
    
    def add_wishlist_items(self, steam_id: str, wishlist_data: List[Dict]) -> Tuple[int, int]:
        """
        Fügt Wishlist-Items hinzu
        Returns: (added_items, missing_apps)
        """
        with self.lock:
            added_items = 0
            missing_apps = 0
            
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    for item in wishlist_data:
                        app_id = str(item.get('appid'))
                        
                        # Prüfe ob App in steam_apps existiert
                        cursor.execute("SELECT 1 FROM steam_apps WHERE app_id = ?", (app_id,))
                        app_exists = cursor.fetchone() is not None
                        
                        if not app_exists:
                            missing_apps += 1
                            continue
                        
                        try:
                            cursor.execute('''
                                INSERT OR REPLACE INTO wishlist_items 
                                (steam_id, app_id, priority, date_added)
                                VALUES (?, ?, ?, ?)
                            ''', (
                                steam_id,
                                app_id,
                                item.get('priority', 0),
                                item.get('date_added', datetime.now().isoformat())
                            ))
                            added_items += 1
                            
                        except sqlite3.Error as e:
                            print(f"⚠️ Fehler bei Wishlist-Item {app_id}: {e}")
                            continue
                    
                    conn.commit()
                    
            except sqlite3.Error as e:
                print(f"❌ Wishlist-Items Batch-Insert Fehler: {e}")
            
            return added_items, missing_apps
    
    def get_wishlist_items(self, steam_id: str, include_cheapshark: bool = True) -> List[Dict]:
        """Holt alle Wishlist-Items für einen Benutzer"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if include_cheapshark:
                query = '''
                    SELECT wi.*, sa.name, sa.type, sa.is_free, sa.price_current, 
                           sa.price_original, sa.discount_percent,
                           cm.cheapshark_game_id, cm.thumb_url, cm.cheapest_price_ever,
                           cm.cheapest_store, cm.deals_count, cm.mapping_status, 
                           cm.no_mapping_found
                    FROM wishlist_items wi
                    JOIN steam_apps sa ON wi.app_id = sa.app_id
                    LEFT JOIN cheapshark_mappings cm ON wi.app_id = cm.app_id
                    WHERE wi.steam_id = ?
                    ORDER BY wi.priority DESC, wi.date_added ASC
                '''
            else:
                query = '''
                    SELECT wi.*, sa.name, sa.type, sa.is_free, sa.price_current, 
                           sa.price_original, sa.discount_percent
                    FROM wishlist_items wi
                    JOIN steam_apps sa ON wi.app_id = sa.app_id
                    WHERE wi.steam_id = ?
                    ORDER BY wi.priority DESC, wi.date_added ASC
                '''
            
            cursor.execute(query, (steam_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ========================
    # MAPPING QUEUE OPERATIONS
    # ========================
    
    def add_to_mapping_queue(self, app_ids: List[str], priority: int = 5) -> int:
        """Fügt Apps zur CheapShark-Mapping Queue hinzu"""
        with self.lock:
            added_count = 0
            
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    for app_id in app_ids:
                        try:
                            cursor.execute('''
                                INSERT OR IGNORE INTO mapping_queue (app_id, priority)
                                VALUES (?, ?)
                            ''', (app_id, priority))
                            
                            if cursor.rowcount > 0:
                                added_count += 1
                                
                        except sqlite3.Error as e:
                            print(f"⚠️ Fehler beim Hinzufügen zur Mapping Queue {app_id}: {e}")
                            continue
                    
                    conn.commit()
                    
            except sqlite3.Error as e:
                print(f"❌ Mapping Queue Batch-Insert Fehler: {e}")
            
            return added_count
    
    def get_next_mapping_jobs(self, limit: int = 10) -> List[Dict]:
        """Holt die nächsten Jobs aus der Mapping Queue"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT mq.*, sa.name
                FROM mapping_queue mq
                JOIN steam_apps sa ON mq.app_id = sa.app_id
                WHERE mq.status = 'pending' AND mq.retry_count < 3
                ORDER BY mq.priority DESC, mq.added_at ASC
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_mapping_job_status(self, job_id: int, status: str, error_message: str = None):
        """Aktualisiert den Status eines Mapping Jobs"""
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    if status == 'processing':
                        cursor.execute('''
                            UPDATE mapping_queue 
                            SET status = ?, processing_started = CURRENT_TIMESTAMP
                            WHERE id = ?
                        ''', (status, job_id))
                    elif status in ['completed', 'failed']:
                        cursor.execute('''
                            UPDATE mapping_queue 
                            SET status = ?, completed_at = CURRENT_TIMESTAMP, 
                                error_message = ?, 
                                retry_count = retry_count + ?
                            WHERE id = ?
                        ''', (status, error_message, 1 if status == 'failed' else 0, job_id))
                    
                    conn.commit()
                    
            except sqlite3.Error as e:
                print(f"❌ Fehler beim Aktualisieren des Job-Status {job_id}: {e}")
    
    # ========================
    # STATISTICS & REPORTING - ERWEITERT
    # ========================
    
    def get_database_stats(self) -> Dict:
        """Holt umfassende Datenbankstatistiken - ERWEITERT mit Release Date & Too New"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Apps Statistiken
            cursor.execute("SELECT COUNT(*) FROM steam_apps")
            total_apps = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM steam_apps WHERE is_free = 1")
            free_apps = cursor.fetchone()[0]
            
            # Apps mit Release Date
            cursor.execute("SELECT COUNT(*) FROM steam_apps WHERE release_date IS NOT NULL AND release_date != ''")
            apps_with_release_date = cursor.fetchone()[0]
            
            # Kürzlich veröffentlichte Apps (< 30 Tage)
            cursor.execute('''
                SELECT COUNT(*) FROM steam_apps 
                WHERE release_date IS NOT NULL 
                  AND release_date != ''
                  AND JULIANDAY('now') - JULIANDAY(release_date) <= 30
            ''')
            recent_apps = cursor.fetchone()[0]
            
            # CheapShark Statistiken - ERWEITERT
            cursor.execute("SELECT COUNT(*) FROM cheapshark_mappings WHERE mapping_status = 'found'")
            mapped_apps = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM cheapshark_mappings WHERE no_mapping_found = 1")
            no_mapping_apps = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM cheapshark_mappings WHERE mapping_status = 'too_new'")
            too_new_apps = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM cheapshark_mappings WHERE mapping_status = 'failed'")
            failed_mapping_apps = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM cheapshark_mappings WHERE mapping_attempts > 0")
            attempted_apps = cursor.fetchone()[0]
            
            # Wishlist Statistiken
            cursor.execute("SELECT COUNT(*) FROM wishlist_items")
            total_wishlist_items = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT steam_id) FROM wishlist_items")
            unique_users = cursor.fetchone()[0]
            
            # Queue Statistiken
            cursor.execute("SELECT COUNT(*) FROM mapping_queue WHERE status = 'pending'")
            pending_mappings = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM mapping_queue WHERE status = 'failed'")
            failed_mappings = cursor.fetchone()[0]
            
            return {
                'apps': {
                    'total': total_apps,
                    'free': free_apps,
                    'paid': total_apps - free_apps,
                    'with_release_date': apps_with_release_date,
                    'recently_released': recent_apps
                },
                'cheapshark': {
                    'mapped': mapped_apps,
                    'no_mapping_found': no_mapping_apps,
                    'too_new': too_new_apps,
                    'mapping_failed': failed_mapping_apps,
                    'attempted': attempted_apps,
                    'unmapped': total_apps - attempted_apps,
                    'success_rate': (mapped_apps / attempted_apps * 100) if attempted_apps > 0 else 0,
                    'found_rate': (mapped_apps / total_apps * 100) if total_apps > 0 else 0,
                    'coverage': ((mapped_apps + no_mapping_apps + too_new_apps) / total_apps * 100) if total_apps > 0 else 0
                },
                'wishlist': {
                    'total_items': total_wishlist_items,
                    'unique_users': unique_users,
                    'avg_items_per_user': total_wishlist_items / unique_users if unique_users > 0 else 0
                },
                'queue': {
                    'pending': pending_mappings,
                    'failed': failed_mappings
                }
            }
    
    def get_cheapshark_mapping_breakdown(self) -> Dict:
        """NEUE METHODE: Detaillierte Aufschlüsselung der CheapShark-Mappings"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    mapping_status,
                    COUNT(*) as count
                FROM cheapshark_mappings
                GROUP BY mapping_status
            ''')
            
            status_breakdown = {}
            for row in cursor.fetchall():
                status_breakdown[row['mapping_status']] = row['count']
            
            cursor.execute('''
                SELECT 
                    AVG(mapping_attempts) as avg_attempts,
                    MAX(mapping_attempts) as max_attempts,
                    COUNT(CASE WHEN mapping_attempts > 1 THEN 1 END) as retried_count
                FROM cheapshark_mappings
            ''')
            
            attempts_info = cursor.fetchone()
            
            return {
                'status_breakdown': status_breakdown,
                'attempts_info': {
                    'average_attempts': float(attempts_info['avg_attempts']) if attempts_info['avg_attempts'] else 0,
                    'max_attempts': attempts_info['max_attempts'] or 0,
                    'apps_retried': attempts_info['retried_count'] or 0
                }
            }
    
    def cleanup_old_data(self, days: int = 30):
        """Bereinigt alte Daten (fehlgeschlagene Jobs, etc.)"""
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cutoff_date = datetime.now() - timedelta(days=days)
                    
                    # Alte fehlgeschlagene Mapping Jobs löschen
                    cursor.execute('''
                        DELETE FROM mapping_queue 
                        WHERE status = 'failed' AND completed_at < ?
                    ''', (cutoff_date.isoformat(),))
                    
                    deleted_jobs = cursor.rowcount
                    
                    # Alte Import Sessions löschen
                    cursor.execute('''
                        DELETE FROM import_sessions 
                        WHERE started_at < ?
                    ''', (cutoff_date.isoformat(),))
                    
                    deleted_sessions = cursor.rowcount
                    
                    # Optional: Alte fehlgeschlagene CheapShark-Mappings zurücksetzen für Retry
                    reset_failed = input(f"Fehlgeschlagene CheapShark-Mappings (älter als {days} Tage) für Retry zurücksetzen? (j/n): ").strip().lower()
                    reset_count = 0
                    if reset_failed in ['j', 'ja', 'y', 'yes']:
                        cursor.execute('''
                            DELETE FROM cheapshark_mappings 
                            WHERE mapping_status = 'failed' AND last_attempt < ?
                        ''', (cutoff_date.isoformat(),))
                        reset_count = cursor.rowcount
                    
                    conn.commit()
                    
                    print(f"🧹 Bereinigung abgeschlossen:")
                    print(f"   📋 {deleted_jobs} alte Jobs gelöscht")
                    print(f"   📊 {deleted_sessions} alte Sessions gelöscht")
                    if reset_count > 0:
                        print(f"   🔄 {reset_count} fehlgeschlagene Mappings zurückgesetzt")
                    
            except sqlite3.Error as e:
                print(f"❌ Bereinigungsfehler: {e}")
    
    def export_wishlist_data(self, steam_id: str, filepath: str = None) -> str:
        """Exportiert Wishlist-Daten als JSON"""
        if not filepath:
            filepath = f"wishlist_export_{steam_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        wishlist_items = self.get_wishlist_items(steam_id, include_cheapshark=True)
        
        export_data = {
            'steam_id': steam_id,
            'exported_at': datetime.now().isoformat(),
            'total_items': len(wishlist_items),
            'items': wishlist_items
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        return filepath
