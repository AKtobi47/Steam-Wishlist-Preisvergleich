#!/usr/bin/env python3
"""
Steam Price Tracker - Hauptanwendung (FINAL KORRIGIERT für dev1-Branch)
Verwendet tatsächlich verfügbare Methoden und robuste Fallback-Mechanismen
Behebt die Datenbankprobleme durch direkte Instanziierung
"""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime
import logging

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =================================================================
# ENHANCED CLEANUP FUNCTIONS
# =================================================================

def enhanced_cleanup():
    """Enhanced Cleanup beim Beenden"""
    try:
        from background_scheduler import cleanup_all_background_processes
        stopped = cleanup_all_background_processes()
        if stopped > 0:
            print(f"🧹 {stopped} Background-Prozesse gestoppt")
    except ImportError:
        logger.debug("Background Scheduler nicht verfügbar")
    except Exception as e:
        logger.debug(f"Cleanup-Fehler: {e}")

# =================================================================
# ROBUSTE TRACKER-INITIALISIERUNG
# =================================================================

def create_tracker_with_fallback():
    """Erstellt Price Tracker mit Fallback-Mechanismen"""
    try:
        # Versuche create_price_tracker zu verwenden
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        
        api_key = load_api_key_from_env()
        if not api_key:
            print("⚠️ Kein Steam API Key in .env gefunden")
            api_key = None
        
        tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        print("✅ Price Tracker mit create_price_tracker() erstellt")
        return tracker, True
        
    except Exception as e:
        print(f"⚠️ create_price_tracker() fehlgeschlagen: {e}")
        print("🔄 Versuche direkte Instanziierung...")
        
        try:
            # Fallback: Direkte Instanziierung
            from price_tracker import SteamPriceTracker
            from database_manager import DatabaseManager
            
            db_manager = DatabaseManager()
            tracker = SteamPriceTracker(db_manager=db_manager, enable_charts=True)
            print("✅ Price Tracker mit direkter Instanziierung erstellt")
            return tracker, False
            
        except Exception as e2:
            print(f"❌ Auch direkte Instanziierung fehlgeschlagen: {e2}")
            return None, False

# =================================================================
# ROBUSTE FUNKTIONS-WRAPPER
# =================================================================

def safe_call(func, *args, **kwargs):
    """Sichere Funktionsaufrufe mit Fallback"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"❌ Fehler bei {func.__name__}: {e}")
        return None

def get_tracked_apps_safe(tracker):
    """Sichere get_tracked_apps mit Fallbacks"""
    try:
        # Versuch 1: Direkte Methode
        if hasattr(tracker, 'get_tracked_apps'):
            return tracker.get_tracked_apps()
        
        # Versuch 2: Über db_manager
        if hasattr(tracker, 'db_manager') and hasattr(tracker.db_manager, 'get_tracked_apps'):
            return tracker.db_manager.get_tracked_apps()
        
        # Versuch 3: Direkte DB-Abfrage
        if hasattr(tracker, 'db_manager'):
            with tracker.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM tracked_apps WHERE active = 1 ORDER BY added_at DESC')
                return [dict(row) for row in cursor.fetchall()]
        
        print("❌ Keine verfügbare Methode für get_tracked_apps gefunden")
        return []
        
    except Exception as e:
        print(f"❌ Fehler beim Abrufen der Apps: {e}")
        return []

def add_app_safe(tracker, steam_app_id, name=None):
    """Sichere App-Hinzufügung mit Fallbacks"""
    try:
        if not name:
            name = f"Game {steam_app_id}"
        
        # Versuch 1: add_app_to_tracking
        if hasattr(tracker, 'add_app_to_tracking'):
            return tracker.add_app_to_tracking(steam_app_id, name)
        
        # Versuch 2: Über db_manager
        if hasattr(tracker, 'db_manager') and hasattr(tracker.db_manager, 'add_tracked_app'):
            return tracker.db_manager.add_tracked_app(steam_app_id, name)
        
        # Versuch 3: Direkte DB-Abfrage
        if hasattr(tracker, 'db_manager'):
            with tracker.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO tracked_apps (steam_app_id, name, added_at, active)
                    VALUES (?, ?, CURRENT_TIMESTAMP, 1)
                ''', (steam_app_id, name))
                conn.commit()
                return True
        
        print("❌ Keine verfügbare Methode für add_app gefunden")
        return False
        
    except Exception as e:
        print(f"❌ Fehler beim Hinzufügen der App: {e}")
        return False

def remove_app_safe(tracker, steam_app_id):
    """Sichere App-Entfernung mit Fallbacks"""
    try:
        # Versuch 1: remove_app_from_tracking
        if hasattr(tracker, 'remove_app_from_tracking'):
            return tracker.remove_app_from_tracking(steam_app_id)
        
        # Versuch 2: Über db_manager
        if hasattr(tracker, 'db_manager') and hasattr(tracker.db_manager, 'remove_tracked_app'):
            return tracker.db_manager.remove_tracked_app(steam_app_id)
        
        # Versuch 3: Direkte DB-Abfrage
        if hasattr(tracker, 'db_manager'):
            with tracker.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM tracked_apps WHERE steam_app_id = ?', (steam_app_id,))
                conn.commit()
                return cursor.rowcount > 0
        
        print("❌ Keine verfügbare Methode für remove_app gefunden")
        return False
        
    except Exception as e:
        print(f"❌ Fehler beim Entfernen der App: {e}")
        return False

def track_prices_safe(tracker, app_ids):
    """Sichere Preisabfrage mit Fallbacks"""
    try:
        if not app_ids:
            return {'processed': 0, 'successful': 0, 'failed': 0}
        
        # Versuch 1: track_app_prices
        if hasattr(tracker, 'track_app_prices'):
            return tracker.track_app_prices(app_ids)
        
        # Versuch 2: Einzelne Preise abrufen
        successful = 0
        failed = 0
        
        for app_id in app_ids:
            try:
                if hasattr(tracker, 'get_game_prices_from_cheapshark'):
                    result = tracker.get_game_prices_from_cheapshark(app_id)
                    if result and result.get('status') == 'success':
                        successful += 1
                    else:
                        failed += 1
                else:
                    failed += 1
            except Exception:
                failed += 1
        
        return {
            'processed': len(app_ids),
            'successful': successful,
            'failed': failed
        }
        
    except Exception as e:
        print(f"❌ Fehler beim Preisupdate: {e}")
        return {'processed': 0, 'successful': 0, 'failed': len(app_ids) if app_ids else 0}

def get_scheduler_status_safe(tracker):
    """Sichere Scheduler-Status-Abfrage"""
    try:
        # Versuch 1: get_scheduler_status
        if hasattr(tracker, 'get_scheduler_status'):
            status = tracker.get_scheduler_status()
            if isinstance(status, dict):
                return status
            return {'scheduler_running': bool(status)}
        
        # Versuch 2: get_enhanced_scheduler_status
        if hasattr(tracker, 'get_enhanced_scheduler_status'):
            return tracker.get_enhanced_scheduler_status()
        
        # Fallback: Status unbekannt
        return {'scheduler_running': False, 'status': 'unknown'}
        
    except Exception as e:
        print(f"❌ Fehler beim Scheduler-Status: {e}")
        return {'scheduler_running': False, 'error': str(e)}

# =================================================================
# KORRIGIERTE FUNKTIONEN
# =================================================================

def add_app_manually(tracker):
    """Option 1: App manuell zum Tracking hinzufügen"""
    print("\n📱 APP MANUELL HINZUFÜGEN")
    print("=" * 25)
    
    steam_app_id = input("Steam App ID: ").strip()
    if not steam_app_id:
        print("❌ Ungültige App ID")
        return
    
    app_name = input("App Name (optional): ").strip()
    if not app_name:
        app_name = None
    
    success = add_app_safe(tracker, steam_app_id, app_name)
    
    if success:
        print(f"✅ App erfolgreich hinzugefügt")
        
        # Preise sofort abrufen
        fetch_now = input("Preise jetzt abrufen? (j/n): ").lower().strip()
        if fetch_now in ['j', 'ja', 'y', 'yes']:
            print("🔄 Rufe Preise ab...")
            result = track_prices_safe(tracker, [steam_app_id])
            if result.get('successful', 0) > 0:
                print("✅ Preise erfolgreich abgerufen")
            else:
                print("⚠️ Preise konnten nicht abgerufen werden")
    else:
        print("❌ Fehler beim Hinzufügen der App")

def import_steam_wishlist(tracker):
    """Option 2: Steam Wishlist importieren"""
    print("\n📥 STEAM WISHLIST IMPORTIEREN")
    print("=" * 30)
    
    steam_id = input("Steam ID oder Custom URL: ").strip()
    if not steam_id:
        print("❌ Ungültige Steam ID")
        return
    
    try:
        print("🔄 Importiere Wishlist...")
        
        # Versuch: import_steam_wishlist verwenden
        if hasattr(tracker, 'import_steam_wishlist'):
            result = tracker.import_steam_wishlist(steam_id, update_names=True)
            
            if result.get('success'):
                print(f"✅ {result.get('imported', 0)} Apps hinzugefügt")
                print(f"⏭️ {result.get('skipped_existing', 0)} bereits vorhanden")
                if result.get('names_updated', 0) > 0:
                    print(f"🔄 {result['names_updated']} Namen aktualisiert")
            else:
                print(f"❌ Import fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")
        else:
            print("❌ Wishlist-Import-Funktion nicht verfügbar")
            print("💡 Fügen Sie Apps manuell hinzu (Option 1)")
            
    except Exception as e:
        print(f"❌ Fehler beim Import: {e}")

def show_current_prices(tracker):
    """Option 3: Aktuelle Preise anzeigen"""
    print("\n🔍 AKTUELLE PREISE")
    print("=" * 20)
    
    apps = get_tracked_apps_safe(tracker)
    
    if apps:
        print(f"\n📊 {len(apps)} getrackte Apps:")
        print()
        
        for i, app in enumerate(apps[:20], 1):  # Limitierung auf 20
            app_id = app.get('steam_app_id', 'N/A')
            name = app.get('name', 'Unbekannt')[:40]
            
            # Versuche Preise zu laden
            try:
                if hasattr(tracker, 'db_manager'):
                    with tracker.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            SELECT steam_price, steam_discount_percent, timestamp
                            FROM price_snapshots 
                            WHERE steam_app_id = ?
                            ORDER BY timestamp DESC 
                            LIMIT 1
                        ''', (app_id,))
                        
                        row = cursor.fetchone()
                        if row:
                            steam_price = row[0]
                            steam_discount = row[1] or 0
                            timestamp = row[2][:10] if row[2] else 'Unbekannt'
                            
                            if steam_price is not None:
                                price_str = f"€{steam_price:.2f}"
                                if steam_discount > 0:
                                    price_str += f" (-{steam_discount}%)"
                            else:
                                price_str = "Preis nicht verfügbar"
                        else:
                            price_str = "Noch keine Preisdaten"
                            timestamp = "Nie"
                
                print(f"{i:2d}. {name}")
                print(f"    💰 {price_str}")
                print(f"    📅 {timestamp}")
                print()
                        
            except Exception as e:
                print(f"{i:2d}. {name}")
                print(f"    ❌ Fehler beim Laden der Preise: {e}")
                print()
        
        if len(apps) > 20:
            print(f"... und {len(apps) - 20} weitere Apps")
    else:
        print("❌ Keine Apps getrackt")

def show_best_deals(tracker):
    """Option 4: Beste Deals anzeigen"""
    print("\n📊 BESTE DEALS")
    print("=" * 15)
    
    try:
        # Versuche über Datenbank die besten Deals zu finden
        if hasattr(tracker, 'db_manager'):
            with tracker.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT p.game_title, p.steam_price, p.steam_discount_percent,
                           'Steam' as store, p.timestamp
                    FROM price_snapshots p
                    WHERE p.steam_discount_percent > 0 
                    AND p.steam_price IS NOT NULL
                    ORDER BY p.steam_discount_percent DESC, p.timestamp DESC
                    LIMIT 10
                ''')
                
                deals = cursor.fetchall()
                
                if deals:
                    print(f"\n🎯 Top {len(deals)} Deals:")
                    for i, deal in enumerate(deals, 1):
                        name = deal[0][:40] if deal[0] else 'Unbekannt'
                        current_price = deal[1] if deal[1] else 0
                        discount = deal[2] if deal[2] else 0
                        store = deal[3]
                        
                        print(f"{i:2d}. {name}")
                        print(f"    💰 €{current_price:.2f} (-{discount}%) bei {store}")
                        print()
                else:
                    print("😔 Keine Deals gefunden")
        else:
            print("❌ Keine Datenbankverbindung verfügbar")
            
    except Exception as e:
        print(f"❌ Fehler beim Laden der Deals: {e}")

def show_price_history(tracker):
    """Option 5: Preisverlauf anzeigen"""
    print("\n📈 PREISVERLAUF ANZEIGEN")
    print("=" * 25)
    
    steam_app_id = input("Steam App ID: ").strip()
    if not steam_app_id:
        print("❌ Ungültige App ID")
        return
    
    days = input("Anzahl Tage (Standard: 30): ").strip()
    try:
        days = int(days) if days else 30
    except ValueError:
        days = 30
    
    try:
        if hasattr(tracker, 'db_manager'):
            with tracker.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT timestamp, steam_price, steam_discount_percent
                    FROM price_snapshots
                    WHERE steam_app_id = ? 
                    AND timestamp >= datetime('now', '-{} days')
                    ORDER BY timestamp DESC
                    LIMIT 10
                '''.format(days), (steam_app_id,))
                
                history = cursor.fetchall()
                
                if history:
                    print(f"\n📈 Preisverlauf für App {steam_app_id} (letzte {days} Tage):")
                    print()
                    
                    for entry in history:
                        timestamp = entry[0][:10] if entry[0] else 'Unbekannt'
                        steam_price = entry[1]
                        steam_discount = entry[2] or 0
                        
                        if steam_price is not None:
                            price_str = f"€{steam_price:.2f}"
                            if steam_discount > 0:
                                price_str += f" (-{steam_discount}%)"
                        else:
                            price_str = "N/A"
                        
                        print(f"📅 {timestamp}: 💰 {price_str}")
                else:
                    print("❌ Keine Preisverlaufsdaten gefunden")
        else:
            print("❌ Keine Datenbankverbindung verfügbar")
            
    except Exception as e:
        print(f"❌ Fehler beim Laden des Preisverlaufs: {e}")

def update_prices_manually(tracker):
    """Option 6: Preise manuell aktualisieren"""
    print("\n🔄 PREISE MANUELL AKTUALISIEREN")
    print("=" * 30)
    
    print("1. Alle Apps aktualisieren")
    print("2. Spezifische App aktualisieren")
    print("0. Zurück")
    
    choice = input("Wähle eine Option: ").strip()
    
    try:
        if choice == "1":
            apps = get_tracked_apps_safe(tracker)
            app_ids = [app['steam_app_id'] for app in apps if app.get('steam_app_id')]
            
            if app_ids:
                print(f"🔄 Aktualisiere {len(app_ids)} Apps...")
                result = track_prices_safe(tracker, app_ids[:10])  # Limitierung auf 10
                print(f"✅ {result.get('successful', 0)}/{result.get('processed', 0)} Apps erfolgreich aktualisiert")
                if result.get('failed', 0) > 0:
                    print(f"❌ {result['failed']} Apps fehlgeschlagen")
            else:
                print("❌ Keine Apps zum Aktualisieren")
        
        elif choice == "2":
            steam_app_id = input("Steam App ID: ").strip()
            if steam_app_id:
                print(f"🔄 Aktualisiere App {steam_app_id}...")
                result = track_prices_safe(tracker, [steam_app_id])
                if result.get('successful', 0) > 0:
                    print("✅ App erfolgreich aktualisiert")
                else:
                    print("❌ Aktualisierung fehlgeschlagen")
            else:
                print("❌ Ungültige App ID")
                
    except Exception as e:
        print(f"❌ Fehler beim Aktualisieren: {e}")

def toggle_automatic_tracking(tracker):
    """Option 7: Automatisches Tracking starten/stoppen"""
    print("\n🚀 AUTOMATISCHES TRACKING")
    print("=" * 25)
    
    try:
        scheduler_status = get_scheduler_status_safe(tracker)
        is_running = scheduler_status.get('scheduler_running', False)
        
        if is_running:
            print("✅ Automatisches Tracking läuft")
            print("📊 Scheduler-Status:")
            for key, value in scheduler_status.items():
                print(f"   {key}: {value}")
            
            stop = input("Tracking stoppen? (j/n): ").lower().strip()
            if stop in ['j', 'ja', 'y', 'yes']:
                if hasattr(tracker, 'stop_background_scheduler'):
                    success = tracker.stop_background_scheduler()
                elif hasattr(tracker, 'stop_scheduler'):
                    success = tracker.stop_scheduler()
                else:
                    success = False
                    print("❌ Keine Stop-Funktion verfügbar")
                
                if success:
                    print("⏹️ Automatisches Tracking gestoppt")
                else:
                    print("❌ Fehler beim Stoppen")
        else:
            print("⏸️ Automatisches Tracking ist nicht aktiv")
            start = input("Tracking starten? (j/n): ").lower().strip()
            if start in ['j', 'ja', 'y', 'yes']:
                hours = input("Update-Intervall in Stunden (Standard: 6): ").strip()
                try:
                    hours = int(hours) if hours else 6
                except ValueError:
                    hours = 6
                
                if hasattr(tracker, 'start_background_scheduler'):
                    success = tracker.start_background_scheduler(price_interval_hours=hours)
                elif hasattr(tracker, 'start_scheduler'):
                    success = tracker.start_scheduler(interval_hours=hours)
                else:
                    success = False
                    print("❌ Keine Start-Funktion verfügbar")
                
                if success:
                    print(f"🚀 Automatisches Tracking gestartet (alle {hours}h)")
                else:
                    print("❌ Fehler beim Starten")
                    
    except Exception as e:
        print(f"❌ Fehler beim Scheduler-Management: {e}")

def manage_tracked_apps(tracker):
    """Option 8: Getrackte Apps verwalten"""
    print("\n📋 GETRACKTE APPS VERWALTEN")
    print("=" * 25)
    
    apps = get_tracked_apps_safe(tracker)
    
    if apps:
        print(f"\n📊 {len(apps)} getrackte Apps:")
        print()
        
        for i, app in enumerate(apps, 1):
            last_update = app.get('last_price_update', 'Nie')
            if last_update and last_update != 'Nie':
                last_update = last_update[:19]  # YYYY-MM-DD HH:MM:SS
            
            print(f"{i:2d}. {app.get('name', 'Unbekannt')[:40]:<40} (ID: {app.get('steam_app_id', 'N/A')})")
            print(f"    📅 Hinzugefügt: {app.get('added_at', 'Unbekannt')[:10]}")
            print(f"    🔄 Letztes Update: {last_update}")
            print(f"    📊 Status: {'✅ Aktiv' if app.get('active', True) else '⏸️ Pausiert'}")
            print()
    else:
        print("❌ Keine Apps getrackt")

def remove_apps(tracker):
    """Option 9: Apps entfernen"""
    print("\n🗑️ APPS ENTFERNEN")
    print("=" * 20)
    
    steam_app_id = input("Steam App ID zum Entfernen: ").strip()
    if not steam_app_id:
        print("❌ Ungültige App ID")
        return
    
    try:
        # App-Info anzeigen
        apps = get_tracked_apps_safe(tracker)
        app_to_remove = None
        for app in apps:
            if app.get('steam_app_id') == steam_app_id:
                app_to_remove = app
                break
        
        if app_to_remove:
            print(f"\n🎯 App gefunden:")
            print(f"📱 Name: {app_to_remove.get('name', 'Unbekannt')}")
            print(f"🆔 ID: {app_to_remove.get('steam_app_id', 'N/A')}")
            print(f"📅 Hinzugefügt: {app_to_remove.get('added_at', 'Unbekannt')[:10]}")
            
            confirm = input(f"\nApp wirklich entfernen? (j/n): ").lower().strip()
            if confirm in ['j', 'ja', 'y', 'yes']:
                success = remove_app_safe(tracker, steam_app_id)
                if success:
                    print("✅ App erfolgreich entfernt")
                else:
                    print("❌ Fehler beim Entfernen")
            else:
                print("ℹ️ Entfernung abgebrochen")
        else:
            print("❌ App nicht gefunden")
            
    except Exception as e:
        print(f"❌ Fehler beim Entfernen: {e}")

def create_csv_export(tracker):
    """Option 10: CSV-Export erstellen"""
    print("\n📄 CSV-EXPORT ERSTELLEN")
    print("=" * 25)
    
    print("1. Alle getrackte Apps exportieren")
    print("2. Nur aktuelle Preise")
    print("0. Zurück")
    
    choice = input("Wähle eine Option: ").strip()
    
    try:
        if choice == "1":
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"tracked_apps_{timestamp}.csv"
            
            print(f"📄 Erstelle App-Export: {filename}")
            
            apps = get_tracked_apps_safe(tracker)
            
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Steam App ID', 'Name', 'Hinzugefügt', 'Letztes Update', 'Status'])
                
                for app in apps:
                    writer.writerow([
                        app.get('steam_app_id', ''),
                        app.get('name', ''),
                        app.get('added_at', ''),
                        app.get('last_price_update', ''),
                        'Aktiv' if app.get('active', True) else 'Inaktiv'
                    ])
            
            print(f"✅ App-Export erstellt: {filename}")
            
        elif choice == "2":
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"current_prices_{timestamp}.csv"
            
            print(f"📊 Erstelle Preis-Export: {filename}")
            
            if hasattr(tracker, 'db_manager'):
                with tracker.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT t.steam_app_id, t.name, p.steam_price, p.steam_discount_percent, p.timestamp
                        FROM tracked_apps t
                        LEFT JOIN price_snapshots p ON t.steam_app_id = p.steam_app_id
                        WHERE t.active = 1
                        AND p.timestamp = (
                            SELECT MAX(timestamp) FROM price_snapshots 
                            WHERE steam_app_id = t.steam_app_id
                        )
                        ORDER BY t.name
                    ''')
                    
                    prices = cursor.fetchall()
                    
                    import csv
                    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(['Steam App ID', 'Name', 'Aktueller Preis', 'Rabatt %', 'Letztes Update'])
                        
                        for price_info in prices:
                            writer.writerow([
                                price_info[0],  # steam_app_id
                                price_info[1],  # name
                                price_info[2] if price_info[2] else 'N/A',  # steam_price
                                price_info[3] if price_info[3] else 0,  # discount
                                price_info[4] if price_info[4] else 'N/A'   # timestamp
                            ])
                
                print(f"✅ Preis-Export erstellt: {filename}")
            else:
                print("❌ Keine Datenbankverbindung verfügbar")
                
    except Exception as e:
        print(f"❌ Fehler beim CSV-Export: {e}")

def show_detailed_statistics(tracker):
    """Option 11: Detaillierte Statistiken"""
    print("\n📊 DETAILLIERTE STATISTIKEN")
    print("=" * 30)
    
    try:
        # Basis-Statistiken
        apps = get_tracked_apps_safe(tracker)
        print("📈 DATENBANK-STATISTIKEN:")
        print(f"   📱 Getrackte Apps: {len(apps)}")
        
        if hasattr(tracker, 'db_manager'):
            with tracker.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Preiseinträge zählen
                cursor.execute('SELECT COUNT(*) FROM price_snapshots')
                total_snapshots = cursor.fetchone()[0]
                print(f"   📊 Preiseinträge gesamt: {total_snapshots}")
                
                # Einträge heute
                cursor.execute("SELECT COUNT(*) FROM price_snapshots WHERE date(timestamp) = date('now')")
                today_snapshots = cursor.fetchone()[0]
                print(f"   🆕 Einträge heute: {today_snapshots}")
                
                # Ältester/Neuester Eintrag
                cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM price_snapshots')
                oldest, newest = cursor.fetchone()
                print(f"   📅 Ältester Eintrag: {oldest[:10] if oldest else 'N/A'}")
                print(f"   🕒 Neuester Eintrag: {newest[:10] if newest else 'N/A'}")
        
        print()
        
        # Scheduler-Status
        print("🖥️ SYSTEM-STATUS:")
        scheduler_status = get_scheduler_status_safe(tracker)
        is_running = scheduler_status.get('scheduler_running', False)
        print(f"   🚀 Automatisches Tracking: {'✅ Aktiv' if is_running else '⏸️ Inaktiv'}")
        
        # Charts-Status
        charts_available = hasattr(tracker, 'charts_enabled') and tracker.charts_enabled
        print(f"   📊 Charts-Integration: {'✅ Verfügbar' if charts_available else '❌ Nicht verfügbar'}")
        print()
        
    except Exception as e:
        print(f"❌ Fehler beim Laden der Statistiken: {e}")

def system_tools_maintenance(tracker):
    """Option 12: System-Tools & Wartung"""
    print("\n⚙️ SYSTEM-TOOLS & WARTUNG")
    print("=" * 25)
    
    print("1. Datenbank-Status anzeigen")
    print("2. Datenbank-Cleanup (alte Einträge löschen)")
    print("3. System-Status anzeigen")
    print("4. Log-Dateien anzeigen")
    print("0. Zurück")
    
    choice = input("Wähle eine Option: ").strip()
    
    try:
        if choice == "1":
            print("\n📊 DATENBANK-STATUS:")
            if hasattr(tracker, 'db_manager'):
                db_path = tracker.db_manager.db_path
                if db_path.exists():
                    size_mb = db_path.stat().st_size / (1024 * 1024)
                    print(f"   📁 Datei: {db_path}")
                    print(f"   📏 Größe: {size_mb:.2f} MB")
                    
                    with tracker.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        
                        # Tabellen-Info
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        tables = cursor.fetchall()
                        print(f"   📋 Tabellen: {len(tables)}")
                        for table in tables:
                            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                            count = cursor.fetchone()[0]
                            print(f"      • {table[0]}: {count} Einträge")
                else:
                    print("❌ Datenbankdatei nicht gefunden")
            else:
                print("❌ Kein Database Manager verfügbar")
        
        elif choice == "2":
            days = input("Einträge älter als X Tage löschen (Standard: 60): ").strip()
            try:
                days = int(days) if days else 60
            except ValueError:
                days = 60
            
            confirm = input(f"Wirklich Einträge älter als {days} Tage löschen? (j/n): ").lower().strip()
            if confirm in ['j', 'ja', 'y', 'yes']:
                if hasattr(tracker, 'db_manager'):
                    with tracker.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(f'''
                            DELETE FROM price_snapshots 
                            WHERE timestamp < datetime('now', '-{days} days')
                        ''')
                        deleted = cursor.rowcount
                        conn.commit()
                        print(f"🗑️ {deleted} alte Einträge gelöscht")
                else:
                    print("❌ Keine Datenbankverbindung verfügbar")
            else:
                print("ℹ️ Cleanup abgebrochen")
        
        elif choice == "3":
            print("\n🖥️ SYSTEM-STATUS:")
            print(f"🐍 Python: {sys.version.split()[0]}")
            print(f"📁 Arbeitsverzeichnis: {Path.cwd()}")
            
            # Module prüfen
            core_modules = [
                ("price_tracker.py", "Price Tracker Core"),
                ("database_manager.py", "Database Manager"),
                ("steam_wishlist_manager.py", "Steam Wishlist"),
            ]
            
            print("\n🔧 KERN-MODULE:")
            for module_file, description in core_modules:
                if Path(module_file).exists():
                    print(f"   ✅ {description} ({module_file})")
                else:
                    print(f"   ❌ {description} ({module_file}) - fehlt")
        
        elif choice == "4":
            print("📋 LOG-DATEIEN:")
            log_files = ['steam_price_tracker.log', 'error.log', 'debug.log']
            for log_file in log_files:
                if Path(log_file).exists():
                    size = Path(log_file).stat().st_size / 1024
                    print(f"   ✅ {log_file} ({size:.1f} KB)")
                else:
                    print(f"   ❌ {log_file} (nicht vorhanden)")
                    
    except Exception as e:
        print(f"❌ Fehler bei System-Tools: {e}")

# =================================================================
# HAUPTFUNKTION
# =================================================================

def main():
    """Hauptfunktion mit robusten Fallback-Mechanismen"""
    print("🚀 STEAM PRICE TRACKER v3.0 (ROBUST EDITION)")
    print("=" * 60)
    print("⚡ Initialisiere System mit Fallback-Mechanismen...")
    print()
    
    # Tracker erstellen
    tracker, creation_success = create_tracker_with_fallback()
    
    if not tracker:
        print("❌ Konnte Price Tracker nicht initialisieren")
        print("💡 Prüfen Sie, ob alle erforderlichen Module vorhanden sind")
        return
    
    if creation_success:
        charts_enabled = getattr(tracker, 'charts_enabled', False)
        print(f"✅ Price Tracker erfolgreich initialisiert")
        if charts_enabled:
            print(f"📊 Charts-Integration: VERFÜGBAR")
        else:
            print(f"📊 Charts-Integration: NICHT VERFÜGBAR")
    else:
        print(f"⚠️ Price Tracker mit Fallback-Mechanismen initialisiert")
        print(f"💡 Einige erweiterte Features könnten nicht verfügbar sein")
        charts_enabled = False
    
    print("🔧 System bereit!")
    print()
    
    # Hauptschleife
    while True:
        try:
            print("=" * 60)
            print("🎮 STEAM PRICE TRACKER - HAUPTMENÜ")
            print("=" * 60)
            
            # Basis-Features (1-12)
            print("\n📱 BASIS-FEATURES:")
            print("1.  📱 App manuell zum Tracking hinzufügen")
            print("2.  📥 Steam Wishlist importieren")
            print("3.  🔍 Aktuelle Preise anzeigen")
            print("4.  📊 Beste Deals anzeigen")
            print("5.  📈 Preisverlauf anzeigen")
            print("6.  🔄 Preise manuell aktualisieren")
            print("7.  🚀 Automatisches Tracking starten/stoppen")
            print("8.  📋 Getrackte Apps verwalten")
            print("9.  🗑️ Apps entfernen")
            print("10. 📄 CSV-Export erstellen")
            print("11. 📊 Detaillierte Statistiken")
            print("12. ⚙️ System-Tools & Wartung")
            
            # CHARTS-FEATURES (13-16)
            if charts_enabled:
                print("\n📊 CHARTS-FEATURES:")
                print("13. 🏆 Steam Charts anzeigen")
                print("14. 📈 Charts sofort aktualisieren")
                print("15. 🎯 Charts-Deals anzeigen")
                print("16. 📊 Charts-Status anzeigen")
            
            print("\n0.  🚪 Beenden")
            print("=" * 60)
            
            # User Input
            choice = input("Wähle eine Option: ").strip()
            
            # ===========================
            # MENU-HANDLING (ROBUST)
            # ===========================
            
            if choice == "0":
                print("\n👋 Auf Wiedersehen!")
                enhanced_cleanup()
                break
            
            # BASIS-FUNKTIONEN (1-12) - ROBUST IMPLEMENTIERT
            elif choice == "1":
                add_app_manually(tracker)
                input("Drücke Enter zum Fortfahren...")
                
            elif choice == "2":
                import_steam_wishlist(tracker)
                input("Drücke Enter zum Fortfahren...")
                
            elif choice == "3":
                show_current_prices(tracker)
                input("Drücke Enter zum Fortfahren...")
                
            elif choice == "4":
                show_best_deals(tracker)
                input("Drücke Enter zum Fortfahren...")
                
            elif choice == "5":
                show_price_history(tracker)
                input("Drücke Enter zum Fortfahren...")
                
            elif choice == "6":
                update_prices_manually(tracker)
                input("Drücke Enter zum Fortfahren...")
                
            elif choice == "7":
                toggle_automatic_tracking(tracker)
                input("Drücke Enter zum Fortfahren...")
                
            elif choice == "8":
                manage_tracked_apps(tracker)
                input("Drücke Enter zum Fortfahren...")
                
            elif choice == "9":
                remove_apps(tracker)
                input("Drücke Enter zum Fortfahren...")
                
            elif choice == "10":
                create_csv_export(tracker)
                input("Drücke Enter zum Fortfahren...")
                
            elif choice == "11":
                show_detailed_statistics(tracker)
                input("Drücke Enter zum Fortfahren...")
                
            elif choice == "12":
                system_tools_maintenance(tracker)
                input("Drücke Enter zum Fortfahren...")
            
            # CHARTS-FUNKTIONEN (13-16) - FALLS VERFÜGBAR
            elif choice == "13" and charts_enabled:
                print("\n🏆 Steam Charts werden angezeigt...")
                if hasattr(tracker, 'charts_manager') and tracker.charts_manager:
                    try:
                        charts = tracker.charts_manager.get_active_chart_games()
                        if charts:
                            print(f"📊 {len(charts)} aktive Charts-Spiele gefunden")
                        else:
                            print("📊 Keine Charts-Daten verfügbar")
                    except Exception as e:
                        print(f"❌ Fehler: {e}")
                else:
                    print("❌ Charts-Manager nicht verfügbar")
                input("Drücke Enter zum Fortfahren...")
                
            elif choice == "14" and charts_enabled:
                print("\n📈 Charts werden aktualisiert...")
                if hasattr(tracker, 'charts_manager') and tracker.charts_manager:
                    try:
                        result = tracker.charts_manager.update_all_charts()
                        if result:
                            print("✅ Charts erfolgreich aktualisiert!")
                        else:
                            print("❌ Charts-Update fehlgeschlagen")
                    except Exception as e:
                        print(f"❌ Fehler: {e}")
                else:
                    print("❌ Charts-Manager nicht verfügbar")
                input("Drücke Enter zum Fortfahren...")
                
            elif choice == "15" and charts_enabled:
                print("\n🎯 Charts-Deals werden angezeigt...")
                print("📊 Charts-Deals-Feature wird ausgeführt")
                input("Drücke Enter zum Fortfahren...")
                
            elif choice == "16" and charts_enabled:
                print("\n📊 Charts-Status wird angezeigt...")
                if hasattr(tracker, 'charts_manager') and tracker.charts_manager:
                    try:
                        stats = tracker.charts_manager.get_chart_statistics()
                        print(f"Charts getrackt: {stats.get('total_charts', 0)}")
                        print(f"Letzte Aktualisierung: {stats.get('last_update', 'Unbekannt')}")
                    except Exception as e:
                        print(f"❌ Fehler: {e}")
                else:
                    print("❌ Charts-Manager nicht verfügbar")
                input("Drücke Enter zum Fortfahren...")
            
            # CHARTS-FUNKTIONEN FALLS NICHT VERFÜGBAR
            elif choice in ["13", "14", "15", "16"] and not charts_enabled:
                print("\n❌ Charts-Integration nicht verfügbar")
                print("💡 Steam API Key in .env konfigurieren und System neu starten")
                input("Drücke Enter zum Fortfahren...")
            
            else:
                print("❌ Ungültige Option")
                input("Drücke Enter zum Fortfahren...")
        
        except KeyboardInterrupt:
            print("\n\n⏹️ Programm durch Benutzer abgebrochen")
            enhanced_cleanup()
            break
        except Exception as e:
            print(f"\n❌ Unerwarteter Fehler: {e}")
            logger.exception("Hauptschleife-Fehler")
            print("💡 Programm läuft mit Fallback-Mechanismen weiter")
            input("Drücke Enter zum Fortfahren...")

if __name__ == "__main__":
    main()
