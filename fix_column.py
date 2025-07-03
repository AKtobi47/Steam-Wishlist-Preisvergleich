#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix für fehlende game_title Spalte in steam_charts_tracking
"""

import sqlite3
from pathlib import Path

def fix_game_title_column():
    """Fügt die fehlende game_title Spalte hinzu oder korrigiert Namen-Updates"""
    
    db_path = "steam_price_tracker.db"
    
    if not Path(db_path).exists():
        print(f"❌ Datenbank {db_path} nicht gefunden!")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Prüfe aktuelle Spalten in steam_charts_tracking
            cursor.execute("PRAGMA table_info(steam_charts_tracking)")
            columns = {row[1] for row in cursor.fetchall()}
            
            print(f"🔍 Aktuelle Spalten in steam_charts_tracking: {sorted(columns)}")
            
            # Prüfe ob game_title fehlt (sollte 'name' heißen)
            if 'game_title' not in columns and 'name' in columns:
                print("✅ Spalte 'name' existiert bereits - Namen-Update-Code muss korrigiert werden")
                return True
            elif 'game_title' not in columns:
                print("➕ Füge game_title Spalte hinzu...")
                cursor.execute("""
                    ALTER TABLE steam_charts_tracking 
                    ADD COLUMN game_title TEXT
                """)
                
                # Kopiere name zu game_title falls name existiert
                if 'name' in columns:
                    cursor.execute("""
                        UPDATE steam_charts_tracking 
                        SET game_title = name 
                        WHERE name IS NOT NULL
                    """)
                    print("✅ Daten von 'name' zu 'game_title' kopiert")
                
                conn.commit()
                print("✅ game_title Spalte erfolgreich hinzugefügt")
                return True
            else:
                print("✅ game_title Spalte existiert bereits")
                return True
                
    except Exception as e:
        print(f"❌ Fehler beim Korrigieren der game_title Spalte: {e}")
        return False

def create_corrected_name_update_query():
    """
    Erstellt korrigierte Namen-Update-Queries die 'name' statt 'game_title' verwenden
    """
    
    # Korrigierte Varianten der problematischen Queries
    corrected_queries = {
        'update_chart_game_name': """
            UPDATE steam_charts_tracking 
            SET name = ? 
            WHERE steam_app_id = ?
        """,
        
        'bulk_update_names': """
            UPDATE steam_charts_tracking 
            SET name = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE steam_app_id = ? AND (name IS NULL OR name = '' OR name LIKE 'App %')
        """,
        
        'safe_name_update': """
            UPDATE steam_charts_tracking 
            SET name = COALESCE(?, name), updated_at = CURRENT_TIMESTAMP 
            WHERE steam_app_id = ?
        """
    }
    
    return corrected_queries

# Monkey-Patch Funktion für steam_charts_manager.py
def patch_name_update_queries(charts_manager):
    """
    Patcht die Namen-Update-Queries im Charts-Manager zur Laufzeit
    """
    
    def safe_update_chart_name(app_id: str, app_name: str) -> bool:
        """Sichere Namen-Update-Methode"""
        try:
            with charts_manager.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Verwende 'name' statt 'game_title'
                cursor.execute("""
                    UPDATE steam_charts_tracking 
                    SET name = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE steam_app_id = ?
                """, (app_name, app_id))
                
                if cursor.rowcount > 0:
                    logger.debug(f"✅ Name aktualisiert: {app_id} -> {app_name}")
                    return True
                else:
                    logger.debug(f"⚠️ Kein Update für {app_id} (nicht in Charts-Tracking)")
                    return False
                    
        except Exception as e:
            logger.warning(f"⚠️ Namen-Update für App {app_id} fehlgeschlagen: {e}")
            return False
    
    # Patche die Methode zur Laufzeit
    charts_manager.safe_update_chart_name = safe_update_chart_name
    return charts_manager

if __name__ == "__main__":
    print("🔧 Steam Charts - game_title Spalten-Fix")
    print("=" * 50)
    
    if fix_game_title_column():
        print("\n✅ game_title Spalten-Fix erfolgreich!")
        print("\n📝 Nächste Schritte:")
        print("1. Charts-Update erneut versuchen")
        print("2. Falls weiter Probleme: Namen-Update-Code in steam_charts_manager.py anpassen")
    else:
        print("\n❌ Fix fehlgeschlagen!")
        print("Bitte manuell überprüfen und 'name' statt 'game_title' in Queries verwenden")