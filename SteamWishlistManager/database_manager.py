"""
Database Manager für Steam Wishlist Manager
Zentrale Datenbankoperationen für alle Module
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
                
                # CheapShark Mappings
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cheapshark_mappings (
                        app_id TEXT PRIMARY KEY,
                        cheapshark_game_id TEXT,
                        thumb_url TEXT,
                        cheapest_price_ever REAL,
                        cheapest_store TEXT,
                        deals_count INTEGER DEFAULT 0,
                        mapping_updated TIMESTAMP,
                        mapping_attempts INTEGER DEFAULT 0,
                        last_attempt TIMESTAMP,
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
                
                # Indizes für Performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_steam_apps_name ON steam_apps(name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_steam_apps_updated ON steam_apps(updated_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cheapshark_game_id ON cheapshark_mappings(cheapshark_game_id)')
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
        """Fügt eine neue App zur Datenbank hinzu"""
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
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
                        app_data.get('release_date'),
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
    
    def add_apps_batch(self, apps_data: List[Dict]) -> int:
        """Fügt mehrere Apps in einem Batch hinzu"""
        with self.lock:
            added_count = 0
            
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    for app_data in apps_data:
                        try:
                            cursor.execute('''
                                INSERT OR REPLACE INTO steam_apps 
                                (app_id, name, type, is_free, steam_data_updated, updated_at)
                                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                            ''', (
                                str(app_data.get('app_id', app_data.get('appid'))),
                                app_data.get('name', ''),
                                app_data.get('type', 'game'),
                                app_data.get('is_free', False),
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
        """Holt Apps die noch kein CheapShark-Mapping haben"""
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
    
    # ========================
    # CHEAPSHARK OPERATIONS
    # ========================
    
    def get_cheapshark_mapping(self, app_id: str) -> Optional[Dict]:
        """Holt CheapShark-Mapping für eine App"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cheapshark_mappings WHERE app_id = ?", (app_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def add_cheapshark_mapping(self, mapping_data: Dict) -> bool:
        """Fügt CheapShark-Mapping hinzu"""
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO cheapshark_mappings 
                        (app_id, cheapshark_game_id, thumb_url, cheapest_price_ever,
                         cheapest_store, deals_count, mapping_updated, mapping_attempts, last_attempt)
                        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 
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
    
    def mark_cheapshark_attempt_failed(self, app_id: str, error_message: str = None):
        """Markiert einen fehlgeschlagenen CheapShark-Mapping Versuch"""
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO cheapshark_mappings 
                        (app_id, mapping_attempts, last_attempt)
                        VALUES (?, 
                                COALESCE((SELECT mapping_attempts FROM cheapshark_mappings WHERE app_id = ?), 0) + 1,
                                CURRENT_TIMESTAMP)
                    ''', (app_id, app_id))
                    
                    conn.commit()
                    
            except sqlite3.Error as e:
                print(f"❌ Fehler beim Markieren des fehlgeschlagenen Versuchs für App {app_id}: {e}")
    
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
                           cm.cheapest_store, cm.deals_count
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
    # STATISTICS & REPORTING
    # ========================
    
    def get_database_stats(self) -> Dict:
        """Holt umfassende Datenbankstatistiken"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Apps Statistiken
            cursor.execute("SELECT COUNT(*) FROM steam_apps")
            total_apps = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM steam_apps WHERE is_free = 1")
            free_apps = cursor.fetchone()[0]
            
            # CheapShark Statistiken
            cursor.execute("SELECT COUNT(*) FROM cheapshark_mappings WHERE cheapshark_game_id IS NOT NULL")
            mapped_apps = cursor.fetchone()[0]
            
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
                    'paid': total_apps - free_apps
                },
                'cheapshark': {
                    'mapped': mapped_apps,
                    'attempted': attempted_apps,
                    'unmapped': total_apps - attempted_apps,
                    'success_rate': (mapped_apps / attempted_apps * 100) if attempted_apps > 0 else 0
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
                    
                    conn.commit()
                    
                    print(f"🧹 Bereinigung abgeschlossen: {deleted_jobs} Jobs, {deleted_sessions} Sessions gelöscht")
                    
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