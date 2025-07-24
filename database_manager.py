#!/usr/bin/env python3
"""
Database Manager für Steam Price Tracker
Verwaltet SQLite-Datenbankoperationen
"""

import sqlite3
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

class DatabaseManager:
    """Manager für SQLite-Datenbankoperationen"""
    
    def __init__(self, db_path: str = 'steam_price_tracker.db'):
        self.db_path = db_path
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """Stellt sicher, dass die Datenbank existiert"""
        if not os.path.exists(self.db_path):
            print(f"⚠️ Datenbank {self.db_path} nicht gefunden")
            print("💡 Erstelle eine leere Datenbank oder gib den korrekten Pfad an")
            # Erstelle eine leere Datenbank
            conn = sqlite3.connect(self.db_path)
            conn.close()
    
    def get_connection(self) -> sqlite3.Connection:
        """Gibt eine Datenbankverbindung zurück"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Ermöglicht Zugriff auf Spalten per Name
        return conn
    
    def get_all_price_snapshots(self) -> List[Dict[str, Any]]:
        """Gibt alle Price Snapshots zurück"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, steam_app_id, game_title, timestamp,
                       steam_price, steam_original_price, steam_discount_percent, steam_available,
                       greenmangaming_price, greenmangaming_original_price, greenmangaming_discount_percent, greenmangaming_available,
                       gog_price, gog_original_price, gog_discount_percent, gog_available,
                       humblestore_price, humblestore_original_price, humblestore_discount_percent, humblestore_available,
                       fanatical_price, fanatical_original_price, fanatical_discount_percent, fanatical_available,
                       gamesplanet_price, gamesplanet_original_price, gamesplanet_discount_percent, gamesplanet_available
                FROM price_snapshots
                ORDER BY timestamp DESC
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except sqlite3.Error as e:
            print(f" Datenbankfehler bei price_snapshots: {e}")
            return []
        except Exception as e:
            print(f" Unerwarteter Fehler: {e}")
            return []
    
    def get_all_tracked_apps(self) -> List[Dict[str, Any]]:
        """Gibt alle getrackte Apps zurück (aus price_snapshots abgeleitet)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT steam_app_id, game_title, 
                       MIN(timestamp) as first_tracked,
                       MAX(timestamp) as last_updated
                FROM price_snapshots
                GROUP BY steam_app_id, game_title
                ORDER BY game_title
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except sqlite3.Error as e:
            print(f" Datenbankfehler bei tracked_apps: {e}")
            return []
        except Exception as e:
            print(f" Unerwarteter Fehler: {e}")
            return []
    
    def get_all_name_history(self) -> List[Dict[str, Any]]:
        """Gibt alle Namensänderungen zurück (aus Preishistorie abgeleitet)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Finde Spiele, die ihren Namen geändert haben
            cursor.execute("""
                SELECT steam_app_id, 
                       LAG(game_title) OVER (PARTITION BY steam_app_id ORDER BY timestamp) as old_name,
                       game_title as new_name,
                       timestamp as change_date
                FROM price_snapshots
                WHERE steam_app_id IS NOT NULL
                ORDER BY steam_app_id, timestamp
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            # Nur Zeilen mit tatsächlichen Namensänderungen zurückgeben
            changes = []
            for row in rows:
                if row['old_name'] and row['old_name'] != row['new_name']:
                    changes.append(dict(row))
            
            return changes
            
        except sqlite3.Error as e:
            print(f" Datenbankfehler bei name_history: {e}")
            return []
        except Exception as e:
            print(f" Unerwarteter Fehler: {e}")
            return []
    
    def get_all_charts_tracking(self) -> List[Dict[str, Any]]:
        """Gibt alle Charts-Tracking-Daten zurück"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, steam_app_id, game_title, timestamp,
                       steam_price, steam_original_price, steam_discount_percent, steam_available,
                       greenmangaming_price, greenmangaming_original_price, greenmangaming_discount_percent, greenmangaming_available,
                       gog_price, gog_original_price, gog_discount_percent, gog_available,
                       humblestore_price, humblestore_original_price, humblestore_discount_percent, humblestore_available,
                       fanatical_price, fanatical_original_price, fanatical_discount_percent, fanatical_available,
                       gamesplanet_price, gamesplanet_original_price, gamesplanet_discount_percent, gamesplanet_available,
                       is_chart_game, chart_types
                FROM charts_price_snapshots
                ORDER BY timestamp DESC
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except sqlite3.Error as e:
            print(f" Datenbankfehler bei charts_price_snapshots: {e}")
            return []
        except Exception as e:
            print(f" Unerwarteter Fehler: {e}")
            return []
    
    def get_all_charts_prices(self) -> List[Dict[str, Any]]:
        """Gibt Charts-spezifische Preisdaten zurück"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT steam_app_id, game_title, timestamp,
                       steam_price, steam_original_price, steam_discount_percent,
                       is_chart_game, chart_types
                FROM charts_price_snapshots
                WHERE is_chart_game = 1
                ORDER BY timestamp DESC
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except sqlite3.Error as e:
            print(f" Datenbankfehler bei charts_prices: {e}")
            return []
        except Exception as e:
            print(f" Unerwarteter Fehler: {e}")
            return []
    
    def get_all_statistics(self) -> List[Dict[str, Any]]:
        """Gibt Statistiken aus den Preisdaten zurück"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    'avg_steam_price' as metric_name,
                    AVG(steam_price) as value,
                    MAX(timestamp) as timestamp,
                    steam_app_id,
                    'price_stats' as category
                FROM price_snapshots
                WHERE steam_price IS NOT NULL
                GROUP BY steam_app_id
                
                UNION ALL
                
                SELECT 
                    'max_discount_percent' as metric_name,
                    MAX(steam_discount_percent) as value,
                    MAX(timestamp) as timestamp,
                    steam_app_id,
                    'discount_stats' as category
                FROM price_snapshots
                WHERE steam_discount_percent IS NOT NULL
                GROUP BY steam_app_id
                
                ORDER BY timestamp DESC
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except sqlite3.Error as e:
            print(f" Datenbankfehler bei statistics: {e}")
            return []
        except Exception as e:
            print(f" Unerwarteter Fehler: {e}")
            return []
    
    def get_all_tracked_apps_price_history(self) -> List[Dict[str, Any]]:
        """Gibt alle Preis-Historien der getrackten Apps zurück"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT steam_app_id, name, target_price, timestamp,
                       steam_price, greenmangaming_price, gog_price,
                       humblestore_price, fanatical_price, gamesplanet_price
                FROM tracked_apps_price_history
                ORDER BY timestamp DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f" Datenbankfehler bei tracked_apps_price_history: {e}")
            return []
        except Exception as e:
            print(f" Unerwarteter Fehler: {e}")
            return []
    
    def get_all_tracked_apps_latest_prices(self) -> List[Dict[str, Any]]:
        """Gibt alle aktuellen Preise der getrackten Apps zurück"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT steam_app_id, name, app_active, target_price, app_source, notes, game_title, price_timestamp,
                       steam_price, steam_original_price, steam_discount_percent, steam_available,
                       greenmangaming_price, greenmangaming_original_price, greenmangaming_discount_percent, greenmangaming_available,
                       gog_price, gog_original_price, gog_discount_percent, gog_available,
                       humblestore_price, humblestore_original_price, humblestore_discount_percent, humblestore_available,
                       fanatical_price, fanatical_original_price, fanatical_discount_percent, fanatical_available,
                       gamesplanet_price, gamesplanet_original_price, gamesplanet_discount_percent, gamesplanet_available
                FROM tracked_apps_latest_prices
                ORDER BY price_timestamp DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f" Datenbankfehler bei tracked_apps_latest_prices: {e}")
            return []
        except Exception as e:
            print(f" Unerwarteter Fehler: {e}")
            return []
    
    def get_database_info(self) -> Dict[str, Any]:
        """Gibt Informationen über die Datenbank zurück"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Tabellen auflisten
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Tabellengröße ermitteln
            table_counts = {}
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    table_counts[table] = count
                except sqlite3.Error:
                    table_counts[table] = 0
            
            conn.close()
            
            return {
                'database_path': self.db_path,
                'database_exists': os.path.exists(self.db_path),
                'database_size': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0,
                'tables': tables,
                'table_counts': table_counts,
                'total_records': sum(table_counts.values())
            }
            
        except Exception as e:
            return {
                'database_path': self.db_path,
                'database_exists': False,
                'error': str(e)
            }