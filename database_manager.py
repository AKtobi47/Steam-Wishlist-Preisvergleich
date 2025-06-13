"""
Database Manager für Steam Price Tracker
Vereinfacht für Preis-Tracking ohne CheapShark-Mapping Komplexität
Basiert auf steam-wishlist-preisvergleich-branch aber fokussiert auf Preise
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import threading

class DatabaseManager:
    """
    Zentrale Datenbank-Klasse für Steam Price Tracking
    Fokus auf Preis-Tracking ohne CheapShark-Mapping Komplexität
    """
    
    def __init__(self, db_path: str = "steam_price_tracker.db"):
        self.db_path = Path(db_path)
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialisiert alle benötigten Tabellen für Preis-Tracking"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # Tracked Apps Tabelle (Apps die wir verfolgen)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tracked_apps (
                        steam_app_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_price_update TIMESTAMP,
                        active BOOLEAN DEFAULT 1
                    )
                ''')
                
                # Price Snapshots Tabelle (historische Preise)
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
                
                # Price Alerts Tabelle (optional für Zukunft)
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
                
                # Tracking Sessions Tabelle (für Statistiken)
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
                
                # Indizes für Performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_snapshots_app_id ON price_snapshots(steam_app_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_snapshots_timestamp ON price_snapshots(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracked_apps_active ON tracked_apps(active)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_alerts_active ON price_alerts(active)')
                
                conn.commit()
                print("✅ Price Tracker Datenbank initialisiert")
                
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
    # TRACKED APPS OPERATIONS
    # ========================
    
    def add_tracked_app(self, steam_app_id: str, name: str) -> bool:
        """Fügt eine App zum Preis-Tracking hinzu"""
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO tracked_apps 
                        (steam_app_id, name, added_at, active)
                        VALUES (?, ?, CURRENT_TIMESTAMP, 1)
                    ''', (steam_app_id, name))
                    
                    conn.commit()
                    return True
                    
            except sqlite3.Error as e:
                print(f"❌ Fehler beim Hinzufügen der App {steam_app_id}: {e}")
                return False
    
    def remove_tracked_app(self, steam_app_id: str) -> bool:
        """Entfernt eine App aus dem Preis-Tracking (setzt active = 0)"""
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        UPDATE tracked_apps 
                        SET active = 0 
                        WHERE steam_app_id = ?
                    ''', (steam_app_id,))
                    
                    conn.commit()
                    return cursor.rowcount > 0
                    
            except sqlite3.Error as e:
                print(f"❌ Fehler beim Entfernen der App {steam_app_id}: {e}")
                return False
    
    def is_app_tracked(self, steam_app_id: str) -> bool:
        """Prüft ob eine App getrackt wird"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 1 FROM tracked_apps 
                WHERE steam_app_id = ? AND active = 1
            ''', (steam_app_id,))
            return cursor.fetchone() is not None
    
    def get_tracked_apps(self) -> List[Dict]:
        """Holt alle aktiven getrackte Apps"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT steam_app_id, name, added_at, last_price_update
                FROM tracked_apps 
                WHERE active = 1
                ORDER BY name
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def update_app_last_price_update(self, steam_app_id: str):
        """Aktualisiert den Zeitpunkt der letzten Preisabfrage"""
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
                print(f"❌ Fehler beim Aktualisieren der App {steam_app_id}: {e}")
    
    # ========================
    # PRICE SNAPSHOTS OPERATIONS
    # ========================
    
    def save_price_snapshot(self, price_data: Dict) -> bool:
        """
        Speichert einen Preis-Snapshot in die Datenbank
        
        Args:
            price_data: Dict mit Preisinformationen aus SteamPriceTracker
        """
        if price_data.get('status') != 'success':
            return False
        
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    steam_app_id = price_data['steam_app_id']
                    game_title = price_data['game_title']
                    prices = price_data['prices']
                    
                    # Store-Namen zu Spaltennamen mapping
                    store_mapping = {
                        'Steam': 'steam',
                        'GreenManGaming': 'greenmangaming',
                        'GOG': 'gog',
                        'HumbleStore': 'humblestore',
                        'Fanatical': 'fanatical',
                        'GamesPlanet': 'gamesplanet'
                    }
                    
                    # SQL dynamisch aufbauen
                    columns = ['steam_app_id', 'game_title', 'timestamp']
                    values = [steam_app_id, game_title, price_data['timestamp']]
                    placeholders = ['?', '?', '?']
                    
                    for store_name, db_prefix in store_mapping.items():
                        store_data = prices.get(store_name, {})
                        
                        columns.extend([
                            f'{db_prefix}_price',
                            f'{db_prefix}_original_price', 
                            f'{db_prefix}_discount_percent',
                            f'{db_prefix}_available'
                        ])
                        
                        values.extend([
                            store_data.get('price'),
                            store_data.get('original_price'),
                            store_data.get('discount_percent', 0),
                            store_data.get('available', False)
                        ])
                        
                        placeholders.extend(['?', '?', '?', '?'])
                    
                    sql = f'''
                        INSERT INTO price_snapshots ({', '.join(columns)})
                        VALUES ({', '.join(placeholders)})
                    '''
                    
                    cursor.execute(sql, values)
                    conn.commit()
                    
                    # Update last_price_update für App
                    self.update_app_last_price_update(steam_app_id)
                    
                    return True
                    
            except sqlite3.Error as e:
                print(f"❌ Fehler beim Speichern der Preise für {steam_app_id}: {e}")
                return False
    
    def get_price_history(self, steam_app_id: str, days_back: int = 30) -> List[Dict]:
        """
        Holt Preisverlauf für eine App
        
        Args:
            steam_app_id: Steam App ID
            days_back: Wie viele Tage zurück
            
        Returns:
            Liste von Preis-Snapshots
        """
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM price_snapshots
                WHERE steam_app_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            ''', (steam_app_id, cutoff_date.isoformat()))
            
            snapshots = []
            for row in cursor.fetchall():
                snapshot = {
                    'steam_app_id': row['steam_app_id'],
                    'game_title': row['game_title'],
                    'timestamp': row['timestamp'],
                    'prices': {}
                }
                
                # Store-Daten extrahieren
                stores = ['steam', 'greenmangaming', 'gog', 'humblestore', 'fanatical', 'gamesplanet']
                store_display_names = ['Steam', 'GreenManGaming', 'GOG', 'HumbleStore', 'Fanatical', 'GamesPlanet']
                
                for store, display_name in zip(stores, store_display_names):
                    snapshot['prices'][display_name] = {
                        'price': row[f'{store}_price'],
                        'original_price': row[f'{store}_original_price'],
                        'discount_percent': row[f'{store}_discount_percent'],
                        'available': bool(row[f'{store}_available'])
                    }
                
                snapshots.append(snapshot)
            
            return snapshots
    
    def get_latest_prices(self, steam_app_id: str) -> Optional[Dict]:
        """Holt die neuesten Preise für eine App"""
        history = self.get_price_history(steam_app_id, days_back=1)
        return history[0] if history else None
    
    def get_best_current_deals(self, limit: int = 10) -> List[Dict]:
        """
        Holt die aktuell besten Deals (höchste Rabatte)
        
        Args:
            limit: Maximale Anzahl Deals
            
        Returns:
            Liste der besten Deals
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Hole neueste Snapshots für alle Apps
            cursor.execute('''
                SELECT ps.*, ta.name
                FROM price_snapshots ps
                JOIN tracked_apps ta ON ps.steam_app_id = ta.steam_app_id
                WHERE ta.active = 1 
                  AND ps.timestamp = (
                      SELECT MAX(timestamp) 
                      FROM price_snapshots ps2 
                      WHERE ps2.steam_app_id = ps.steam_app_id
                  )
                ORDER BY ps.timestamp DESC
            ''')
            
            deals = []
            stores = ['steam', 'greenmangaming', 'gog', 'humblestore', 'fanatical', 'gamesplanet']
            store_display_names = ['Steam', 'GreenManGaming', 'GOG', 'HumbleStore', 'Fanatical', 'GamesPlanet']
            
            for row in cursor.fetchall():
                # Finde besten Deal für diese App
                best_deal = None
                best_discount = 0
                
                for store, display_name in zip(stores, store_display_names):
                    if row[f'{store}_available'] and row[f'{store}_discount_percent'] > best_discount:
                        best_discount = row[f'{store}_discount_percent']
                        best_deal = {
                            'steam_app_id': row['steam_app_id'],
                            'game_title': row['game_title'],
                            'app_name': row['name'],
                            'store': display_name,
                            'price': row[f'{store}_price'],
                            'original_price': row[f'{store}_original_price'],
                            'discount_percent': row[f'{store}_discount_percent'],
                            'timestamp': row['timestamp']
                        }
                
                if best_deal and best_discount > 0:
                    deals.append(best_deal)
            
            # Sortiere nach Rabatt und begrenze
            deals.sort(key=lambda x: x['discount_percent'], reverse=True)
            return deals[:limit]
    
    # ========================
    # PRICE ALERTS (für Zukunft)
    # ========================
    
    def add_price_alert(self, steam_app_id: str, target_price: float, store_name: str = None) -> bool:
        """Fügt einen Preis-Alert hinzu"""
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO price_alerts 
                        (steam_app_id, target_price, store_name, active)
                        VALUES (?, ?, ?, 1)
                    ''', (steam_app_id, target_price, store_name))
                    
                    conn.commit()
                    return True
                    
            except sqlite3.Error as e:
                print(f"❌ Fehler beim Hinzufügen des Price Alerts: {e}")
                return False
    
    def check_price_alerts(self) -> List[Dict]:
        """Prüft aktive Preis-Alerts und gibt getriggerte zurück"""
        # Implementierung für Zukunft
        return []
    
    # ========================
    # STATISTICS & REPORTING
    # ========================
    
    def get_tracking_statistics(self) -> Dict:
        """Holt umfassende Tracking-Statistiken"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Anzahl getrackte Apps
            cursor.execute("SELECT COUNT(*) FROM tracked_apps WHERE active = 1")
            tracked_apps = cursor.fetchone()[0]
            
            # Gesamtzahl Preis-Snapshots
            cursor.execute("SELECT COUNT(*) FROM price_snapshots")
            total_snapshots = cursor.fetchone()[0]
            
            # Ältester/Neuester Snapshot
            cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM price_snapshots")
            oldest, newest = cursor.fetchone()
            
            # Snapshots letzte 24h
            cutoff_24h = datetime.now() - timedelta(hours=24)
            cursor.execute('''
                SELECT COUNT(*) FROM price_snapshots 
                WHERE timestamp >= ?
            ''', (cutoff_24h.isoformat(),))
            snapshots_24h = cursor.fetchone()[0]
            
            # Aktive Alerts
            cursor.execute("SELECT COUNT(*) FROM price_alerts WHERE active = 1")
            active_alerts = cursor.fetchone()[0]
            
            return {
                'tracked_apps': tracked_apps,
                'total_snapshots': total_snapshots,
                'snapshots_last_24h': snapshots_24h,
                'oldest_snapshot': oldest,
                'newest_snapshot': newest,
                'active_alerts': active_alerts
            }
    
    def get_total_price_snapshots(self) -> int:
        """Gibt Gesamtzahl der Preis-Snapshots zurück"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM price_snapshots")
            return cursor.fetchone()[0]
    
    def get_oldest_snapshot_date(self) -> Optional[str]:
        """Gibt Datum des ältesten Snapshots zurück"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MIN(timestamp) FROM price_snapshots")
            result = cursor.fetchone()[0]
            return result
    
    def get_newest_snapshot_date(self) -> Optional[str]:
        """Gibt Datum des neuesten Snapshots zurück"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(timestamp) FROM price_snapshots")
            result = cursor.fetchone()[0]
            return result
    
    # ========================
    # MAINTENANCE OPERATIONS
    # ========================
    
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
                    
                    print(f"🧹 {deleted_count} alte Preis-Snapshots gelöscht (älter als {days} Tage)")
                    
            except sqlite3.Error as e:
                print(f"❌ Bereinigungsfehler: {e}")
    
    def backup_database(self, backup_path: str = None) -> str:
        """Erstellt ein Backup der Datenbank"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"steam_price_tracker_backup_{timestamp}.db"
        
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            print(f"💾 Datenbank-Backup erstellt: {backup_path}")
            return backup_path
            
        except Exception as e:
            print(f"❌ Backup-Fehler: {e}")
            return None
    
    def vacuum_database(self):
        """Optimiert die Datenbank"""
        with self.lock:
            try:
                with self.get_connection() as conn:
                    conn.execute("VACUUM")
                    print("🔧 Datenbank optimiert (VACUUM)")
                    
            except sqlite3.Error as e:
                print(f"❌ VACUUM-Fehler: {e}")
    
    # ========================
    # EXPORT FUNCTIONALITY
    # ========================
    
    def export_all_price_data(self, output_file: str = None) -> str:
        """Exportiert alle Preis-Daten als JSON"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"price_data_export_{timestamp}.json"
        
        try:
            tracked_apps = self.get_tracked_apps()
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'tracked_apps': tracked_apps,
                'price_history': {}
            }
            
            # Preisverlauf für alle Apps
            for app in tracked_apps:
                app_id = app['steam_app_id']
                history = self.get_price_history(app_id, days_back=365)
                export_data['price_history'][app_id] = history
            
            # Als JSON speichern
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"📄 Preis-Daten exportiert: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Export-Fehler: {e}")
            return None
