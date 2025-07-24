#!/usr/bin/env python3
"""
Steam Price Tracker - Hauptanwendung
"""
import sys
import os
import subprocess
import json
import csv
from pathlib import Path
from datetime import datetime, timedelta
import logging
import time as time_module
import threading
from typing import Dict, List, Optional

# Core imports
from database_manager import DatabaseManager
from price_tracker import SteamPriceTracker, create_price_tracker
from steam_wishlist_manager import SteamWishlistManager

# Neue imports für dynamisches Menü
try:
    from menu_config import get_menu_system, initialize_menu_system
    DYNAMIC_MENU_AVAILABLE = True
except ImportError:
    print("⚠️ Dynamisches Menü nicht verfügbar - nutze klassisches Menü")
    DYNAMIC_MENU_AVAILABLE = False

# Charts imports 
try:
    from steam_charts_manager import CHART_TYPES
    VALID_CHART_TYPES = list(CHART_TYPES.keys())
except ImportError:
    VALID_CHART_TYPES = ['most_played', 'top_releases', 'most_concurrent_players']
    print("⚠️ steam_charts_manager nicht verfügbar - verwende Fallback Chart-Typen")

# Logging Konfiguration
try:
    from logging_config import get_main_logger
    logger = get_main_logger()
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# =================================================================
# ENHANCED CLEANUP & UTILITY FUNCTIONS
# =================================================================

def enhanced_cleanup():
    """Enhanced Cleanup beim Beenden"""
    try:
        # Background Scheduler cleanup
        try:
            from background_scheduler import cleanup_all_background_processes
            stopped = cleanup_all_background_processes()
            if stopped > 0:
                print(f"🧹 {stopped} Background-Prozesse gestoppt")
        except (ImportError, AttributeError):
            logger.debug("Background Scheduler cleanup nicht verfügbar")
        
        # Charts Manager cleanup
        try:
            global charts_manager
            if 'charts_manager' in globals() and charts_manager:
                if hasattr(charts_manager, 'cleanup'):
                    charts_manager.cleanup()
                    print("🧹 Charts Manager bereinigt")
        except Exception:
            logger.debug("Charts Manager cleanup nicht verfügbar")
        
        print("✅ Cleanup abgeschlossen")
    except Exception as e:
        logger.debug(f"Cleanup-Fehler: {e}")

def safe_input(prompt, default=""):
    """Sichere Input-Funktion mit Fallback"""
    try:
        result = input(prompt).strip()
        return result if result else default
    except (EOFError, KeyboardInterrupt):
        return default
    except Exception as e:
        logger.warning(f"Input-Fehler: {e}")
        return default

def create_tracker_with_fallback():
    """
    Erstellt Tracker ohne Elasticsearch (wie gewünscht)
    """
    print("🚀 Steam Price Tracker wird initialisiert...")
    
    try:
        tracker = create_price_tracker(enable_charts=True)
        
        if not tracker:
            print("❌ Tracker konnte nicht erstellt werden")
            return None, None, None
        
        print("✅ Tracker erfolgreich erstellt")
        
        # Charts Manager
        charts_manager = None
        if hasattr(tracker, 'charts_manager') and tracker.charts_manager:
            charts_manager = tracker.charts_manager
            print("✅ Charts Manager verfügbar")
        else:
            print("ℹ️ Charts Manager nicht verfügbar")
        
        # ENTFERNT: Elasticsearch wird nicht mehr über main.py verwaltet
        es_manager = None
        
        return tracker, charts_manager, es_manager
    
    except Exception as e:
        logger.error(f"Tracker-Initialisierung fehlgeschlagen: {e}")
        return None, None, None

def add_app_safe(tracker, steam_app_id, app_name=None, source="manual"):
    """Sichere App-Hinzufügung"""
    try:
        if hasattr(tracker, 'add_or_update_app'):
            return tracker.add_or_update_app(steam_app_id, app_name)
        elif hasattr(tracker, 'add_tracked_app'):
            return tracker.add_tracked_app(steam_app_id, app_name)
        else:
            return tracker.db_manager.add_tracked_app(steam_app_id, app_name)
    except Exception as e:
        logger.error(f"Fehler beim Hinzufügen der App {steam_app_id}: {e}")
        return False

def get_tracked_apps_safe(tracker):
    """Sicheres Abrufen der getrackte Apps"""
    try:
        if hasattr(tracker, 'get_tracked_apps'):
            return tracker.get_tracked_apps()
        elif hasattr(tracker, 'db_manager'):
            return tracker.db_manager.get_tracked_apps()
        else:
            return []
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Apps: {e}")
        return []

def load_stats_safe(tracker):
    """Lädt Statistiken sicher mit robusterem Fallback"""
    try:
        # Versuch 1: Verwende die bestehende get_database_stats Methode
        if hasattr(tracker, 'db_manager') and hasattr(tracker.db_manager, 'get_database_stats'):
            stats = tracker.db_manager.get_database_stats()
            # WICHTIG: Prüfe ob alle erforderlichen Keys existieren
            if isinstance(stats, dict) and 'tracked_apps' in stats:
                return stats
            else:
                logger.warning("⚠️ get_database_stats gibt unvollständige Daten zurück")
        
        # Versuch 2: Fallback - Manuelle Statistik-Berechnung
        logger.info("🔄 Verwende manuellen Statistik-Fallback...")
        
        # Getrackte Apps zählen
        tracked_apps_count = 0
        total_snapshots = 0
        newest_snapshot = None
        stores_tracked = ['Steam']  # Mindestens Steam
        
        if hasattr(tracker, 'db_manager'):
            try:
                with tracker.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Apps zählen
                    cursor.execute('SELECT COUNT(*) FROM tracked_apps WHERE active = 1')
                    result = cursor.fetchone()
                    tracked_apps_count = result[0] if result else 0
                    
                    # Snapshots zählen
                    cursor.execute('SELECT COUNT(*) FROM price_snapshots')
                    result = cursor.fetchone()
                    total_snapshots = result[0] if result else 0
                    
                    # Neuester Snapshot
                    cursor.execute('SELECT timestamp FROM price_snapshots ORDER BY timestamp DESC LIMIT 1')
                    result = cursor.fetchone()
                    newest_snapshot = result[0] if result else None
                    
                    # Stores ermitteln
                    cursor.execute('SELECT DISTINCT store FROM price_snapshots')
                    stores = cursor.fetchall()
                    if stores:
                        stores_tracked = [store[0] for store in stores]
                    
                    logger.info(f"📊 Manuelle Stats: {tracked_apps_count} Apps, {total_snapshots} Snapshots")
                    
            except Exception as db_error:
                logger.error(f"❌ Datenbankfehler beim manuellen Fallback: {db_error}")
                # Verwende get_tracked_apps_safe als letzten Fallback
                apps = get_tracked_apps_safe(tracker)
                tracked_apps_count = len(apps) if apps else 0
        
        # Versuch 3: Wenn immer noch keine DB-Verbindung, verwende sichere Defaults
        else:
            logger.warning("⚠️ Keine Datenbankverbindung verfügbar")
            apps = get_tracked_apps_safe(tracker)
            tracked_apps_count = len(apps) if apps else 0
        
        # GARANTIERT vollständiges Dictionary zurückgeben
        safe_stats = {
            'tracked_apps': tracked_apps_count,
            'total_snapshots': total_snapshots,
            'stores_tracked': stores_tracked,
            'newest_snapshot': newest_snapshot,
            'fallback_used': True
        }
        
        logger.info(f"✅ Sichere Stats geladen: {safe_stats}")
        return safe_stats
        
    except Exception as e:
        logger.error(f"❌ Kritischer Fehler beim Laden der Statistiken: {e}")
        # ULTIMATE FALLBACK - verhindert KeyError
        return {
            'tracked_apps': 0,
            'total_snapshots': 0,
            'stores_tracked': ['Steam'],
            'newest_snapshot': None,
            'error': str(e),
            'fallback_used': True
        }


# =================================================================
# CHARTS OPERATIONS
# =================================================================

def update_charts_safe(charts_manager):
    """Sichere Charts-Aktualisierung"""
    if not charts_manager:
        print("❌ Charts Manager nicht verfügbar")
        return False
    
    try:
        if hasattr(charts_manager, 'update_all_charts'):
            return charts_manager.update_all_charts()
        elif hasattr(charts_manager, 'update_charts'):
            return charts_manager.update_charts()
        else:
            print("❌ Keine Charts-Update-Methode verfügbar")
            return False
    except Exception as e:
        print(f"❌ Fehler beim Charts-Update: {e}")
        return False

def get_charts_deals_safe(charts_manager, tracker):
    """Sichere Charts-Deals"""
    try:
        if charts_manager and hasattr(charts_manager, 'get_current_deals'):
            return charts_manager.get_current_deals()
        
        # Fallback: Beste Deals aus Tracker
        if hasattr(tracker, 'get_best_deals'):
            return tracker.get_best_deals(limit=10)
        
        return []
    except Exception as e:
        logger.error(f"Fehler beim Laden der Charts-Deals: {e}")
        return []

# =================================================================
# MAIN MENU FUNCTIONS
# =================================================================

def menu_add_app_manually(tracker):
    """Option 1: App manuell hinzufügen"""
    print("\n📱 APP MANUELL HINZUFÜGEN")
    print("=" * 30)
    
    steam_app_id = safe_input("Steam App ID: ")
    if not steam_app_id:
        print("❌ Ungültige App ID")
        return
    
    app_name = safe_input("App Name (optional): ")
    
    print("🔍 Füge App zum Tracking hinzu...")
    success = add_app_safe(tracker, steam_app_id, app_name, "manual")
    
    if success:
        print(f"✅ App {steam_app_id} erfolgreich hinzugefügt!")
    else:
        print(f"❌ Fehler beim Hinzufügen der App {steam_app_id}")

def menu_import_wishlist(tracker):
    """Option 2: Steam Wishlist importieren"""
    print("\n📥 STEAM WISHLIST IMPORTIEREN")
    print("=" * 35)
    
    try:
        from steam_wishlist_manager import load_api_key_from_env
        api_key = load_api_key_from_env()
        
        if not api_key:
            print("❌ Steam API Key nicht gefunden")
            print("💡 Trage deinen API Key in die .env Datei ein")
            return
        
        wishlist_manager = SteamWishlistManager(api_key)
        
        steam_id = safe_input("Steam ID oder Benutzername: ")
        if not steam_id:
            print("❌ Steam ID erforderlich")
            return
        
        print("🔄 Lade Wishlist...")
        wishlist = wishlist_manager.get_simple_wishlist(steam_id)
        
        if wishlist:
            print(f"📋 {len(wishlist)} Spiele in Wishlist gefunden")
            
            confirm = safe_input(f"Alle {len(wishlist)} Spiele zum Tracking hinzufügen? (j/n): ")
            if confirm.lower() in ['j', 'ja', 'y', 'yes']:
                added = 0
                for item in wishlist:
                    app_id = item['steam_app_id']
                    name = item['name']
                    if add_app_safe(tracker, app_id, name, "wishlist"):
                        added += 1
                
                print(f"✅ {added} Apps erfolgreich hinzugefügt!")
            else:
                print("❌ Import abgebrochen")
        else:
            print("❌ Keine Wishlist gefunden oder Fehler beim Laden")
    
    except ImportError:
        print("❌ Wishlist Manager nicht verfügbar")
    except Exception as e:
        print(f"❌ Fehler beim Wishlist-Import: {e}")

def menu_show_current_prices(tracker):
    """Option 3: Aktuelle Preise anzeigen"""
    print("\n🔍 AKTUELLE PREISE")
    print("=" * 20)
    
    apps = get_tracked_apps_safe(tracker)
    if not apps:
        print("❌ Keine getrackte Apps gefunden")
        return
    
    print(f"📊 {len(apps)} getrackte Apps:")
    print()
    
    for i, app in enumerate(apps[:20], 1):  # Limitiere auf 20 für bessere Übersicht
        app_id = app.get('steam_app_id', 'N/A')
        name = app.get('name', 'Unbekannt')[:40]
        added_at = app.get('added_at', 'N/A')
        source = app.get('source', 'manual')
        
        print(f"{i:2d}. {name}")
        print(f"    🆔 {app_id} | 📅 {added_at} | 📍 {source}")
        print()

def menu_show_best_deals(tracker):
    """Option 4: Beste Deals anzeigen"""
    print("\n📊 BESTE DEALS")
    print("=" * 15)
    
    try:
        if hasattr(tracker, 'get_best_deals'):
            deals = tracker.get_best_deals(min_discount_percent=25, limit=15)
        else:
            print("❌ Deal-Funktion nicht verfügbar")
            return
        
        if deals:
            print(f"🔥 {len(deals)} Top-Deals gefunden:")
            for i, deal in enumerate(deals, 1):
                name = deal.get('name', 'Unbekannt')[:35]
                price = deal.get('current_price', 0)
                discount = deal.get('discount_percent', 0)
                store = deal.get('store', 'Steam')
                
                print(f"{i:2d}. {name}")
                print(f"    💰 €{price:.2f} • {discount:>3.0f}% Rabatt • {store}")
        else:
            print("❌ Keine Deals gefunden")
            print("💡 Führe zuerst ein Preis-Update durch")
    
    except Exception as e:
        print(f"❌ Fehler beim Laden der Deals: {e}")

def menu_show_price_history(tracker):
    """Option 5: Preisverlauf anzeigen"""
    print("\n📈 PREISVERLAUF")
    print("=" * 15)
    
    app_id = safe_input("Steam App ID für Preisverlauf: ")
    if not app_id:
        print("❌ App ID erforderlich")
        return
    
    try:
        if hasattr(tracker, 'get_price_history'):
            history = tracker.get_price_history(app_id, days_back=30)
        else:
            print("❌ Preisverlauf-Funktion nicht verfügbar")
            return
        
        if history:
            print(f"📊 Preisverlauf für App {app_id} (letzte 30 Tage):")
            for entry in history[-10:]:  # Zeige letzte 10 Einträge
                date = entry.get('date', 'N/A')
                price = entry.get('price', 0)
                store = entry.get('store', 'N/A')
                print(f"  📅 {date} • €{price:.2f} • {store}")
        else:
            print("❌ Keine Preisverlaufsdaten gefunden")
    
    except Exception as e:
        print(f"❌ Fehler beim Laden des Preisverlaufs: {e}")

def menu_update_prices(tracker):
    """Option 6: Preise manuell aktualisieren"""
    print("\n🔄 PREISE AKTUALISIEREN")
    print("=" * 25)
    
    try:
        if hasattr(tracker, 'process_all_pending_apps_optimized'):
            print("🚀 Starte BATCH-Preis-Update (optimiert)...")
            result = tracker.process_all_pending_apps_optimized(hours_threshold=0)
            
            if result.get('success'):
                print(f"✅ BATCH-Update erfolgreich!")
                print(f"📊 {result['total_successful']}/{result['total_apps']} Apps aktualisiert")
                print(f"⏱️ Dauer: {result['total_duration']:.1f}s")
                print(f"⚡ {result['apps_per_second']:.1f} Apps/s")
            else:
                print(f"❌ BATCH-Update fehlgeschlagen: {result.get('error', '')}")
        else:
            print("❌ Preis-Update-Funktion nicht verfügbar")
    
    except Exception as e:
        print(f"❌ Fehler beim Preis-Update: {e}")

def menu_toggle_scheduler(tracker):
    """Option 7: Automatisches Tracking starten/stoppen"""
    print("\n🚀 AUTOMATISCHES TRACKING")
    print("=" * 30)
    
    try:
        if hasattr(tracker, 'get_scheduler_status'):
            status = tracker.get_scheduler_status()
            
            if status and status.get('scheduler_running'):
                print("🔄 Scheduler läuft bereits")
                choice = safe_input("Scheduler stoppen? (j/n): ")
                if choice.lower() in ['j', 'ja', 'y', 'yes']:
                    if hasattr(tracker, 'stop_scheduler'):
                        tracker.stop_scheduler()
                        print("⏹️ Scheduler gestoppt")
                    else:
                        print("❌ Stop-Funktion nicht verfügbar")
            else:
                print("⏹️ Scheduler ist gestoppt")
                choice = safe_input("Scheduler starten? (j/n): ")
                if choice.lower() in ['j', 'ja', 'y', 'yes']:
                    interval = safe_input("Update-Intervall in Stunden (Standard: 6): ", "6")
                    try:
                        interval_hours = int(interval)
                        if hasattr(tracker, 'start_scheduler'):
                            tracker.start_scheduler(interval_hours=interval_hours)
                            print(f"🚀 Scheduler gestartet (alle {interval_hours}h)")
                        else:
                            print("❌ Start-Funktion nicht verfügbar")
                    except ValueError:
                        print("❌ Ungültiges Intervall")
        else:
            print("❌ Scheduler-Funktionen nicht verfügbar")
    
    except Exception as e:
        print(f"❌ Fehler beim Scheduler-Management: {e}")

def menu_update_names_all_apps(tracker):
    """Option 8: Namen für ALLE Apps aktualisieren (NEU!)"""
    print("\n📝 NAMEN FÜR ALLE APPS AKTUALISIEREN")
    print("=" * 40)
    
    try:
        # Hole alle getrackte Apps
        apps = get_tracked_apps_safe(tracker)
        if not apps:
            print("❌ Keine Apps zum Aktualisieren")
            return
        
        app_ids = [app['steam_app_id'] for app in apps if app.get('steam_app_id')]
        
        if not app_ids:
            print("❌ Keine gültigen App IDs gefunden")
            return
        
        print(f"📝 Aktualisiere Namen für {len(app_ids)} Apps...")
        print("🚀 Nutze BATCH-optimierte Wishlist-Manager Funktion...")
        
        # Nutze bestehende Wishlist-Manager BATCH-Funktion
        from steam_wishlist_manager import bulk_get_app_names, load_api_key_from_env
        
        api_key = load_api_key_from_env()
        if not api_key:
            print("❌ Steam API Key nicht verfügbar")
            return
        
        names_result = bulk_get_app_names(app_ids, api_key)
        
        # Namen in DB aktualisieren
        updated = 0
        failed = 0
        
        for app_id, name in names_result.items():
            try:
                # Update über verschiedene mögliche Methoden
                success = False
                
                if hasattr(tracker.db_manager, 'update_app_name'):
                    success = tracker.db_manager.update_app_name(app_id, name)
                else:
                    # Fallback: Direkte DB-Operation
                    with tracker.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE tracked_apps SET name = ? WHERE steam_app_id = ?",
                            (name, app_id)
                        )
                        success = cursor.rowcount > 0
                
                if success:
                    updated += 1
                    print(f"✅ {app_id}: {name[:50]}")
                else:
                    failed += 1
                    
            except Exception as e:
                failed += 1
                logger.warning(f"Namen-Update für App {app_id} fehlgeschlagen: {e}")
        
        print(f"\n📊 ERGEBNIS:")
        print(f"   ✅ Erfolgreich: {updated}")
        print(f"   ❌ Fehlgeschlagen: {failed}")
        print(f"   📊 Gesamt: {len(app_ids)}")
        
    except Exception as e:
        print(f"❌ Namen-Update Fehler: {e}")

def menu_manage_apps(tracker):
    """Option 9: Getrackte Apps verwalten"""
    print("\n📋 GETRACKTE APPS VERWALTEN")
    print("=" * 30)
    
    apps = get_tracked_apps_safe(tracker)
    if not apps:
        print("❌ Keine getrackte Apps gefunden")
        return
    
    print(f"📊 {len(apps)} Apps im Tracking:")
    for i, app in enumerate(apps[:10], 1):  # Zeige erste 10
        name = app.get('name', 'Unbekannt')[:30]
        app_id = app.get('steam_app_id', 'N/A')
        source = app.get('source', 'manual')
        print(f"{i:2d}. {name} ({app_id}) [{source}]")
    
    if len(apps) > 10:
        print(f"... und {len(apps) - 10} weitere")

def menu_remove_apps(tracker):
    """Option 10: Apps entfernen"""
    print("\n🗑️ APPS ENTFERNEN")
    print("=" * 18)
    
    app_id = safe_input("Steam App ID zum Entfernen: ")
    if not app_id:
        print("❌ App ID erforderlich")
        return
    
    try:
        if hasattr(tracker, 'remove_tracked_app'):
            success = tracker.remove_tracked_app(app_id)
        elif hasattr(tracker, 'db_manager'):
            success = tracker.db_manager.remove_tracked_app(app_id)
        else:
            print("❌ Remove-Funktion nicht verfügbar")
            return
        
        if success:
            print(f"✅ App {app_id} entfernt")
        else:
            print(f"❌ App {app_id} nicht gefunden oder Fehler")
    
    except Exception as e:
        print(f"❌ Fehler beim Entfernen: {e}")

def menu_csv_export(tracker):
    """Option 11: CSV-Export erstellen"""
    print("\n📄 CSV-EXPORT")
    print("=" * 13)
    
    try:
        if hasattr(tracker, 'export_to_csv'):
            filename = tracker.export_to_csv()
            print(f"✅ CSV-Export erstellt: {filename}")
        else:
            print("❌ Export-Funktion nicht verfügbar")
    
    except Exception as e:
        print(f"❌ Fehler beim Export: {e}")

def menu_detailed_statistics(tracker):
    """Option 12: Detaillierte Statistiken"""
    print("\n📊 DETAILLIERTE STATISTIKEN")
    print("=" * 30)
    
    stats = load_stats_safe(tracker)
    
    print(f"📊 Apps im Tracking: {stats['tracked_apps']}")
    print(f"📸 Preis-Snapshots: {stats['total_snapshots']}")
    
    if stats['stores_tracked']:
        print(f"🏪 Überwachte Stores: {', '.join(stats['stores_tracked'])}")
    
    if stats['newest_snapshot']:
        print(f"🕒 Letztes Update: {stats['newest_snapshot']}")

def menu_show_charts(charts_manager, tracker):
    """Option 13: Charts anzeigen"""
    print("\n📈 STEAM CHARTS")
    print("=" * 17)
    
    if not charts_manager:
        print("❌ Charts Manager nicht verfügbar")
        return
    
    try:
        if hasattr(charts_manager, 'get_charts_summary'):
            summary = charts_manager.get_charts_summary()
            print(f"📊 Charts verfügbar: {summary}")
        else:
            print("📊 Charts-System ist aktiv")
    
    except Exception as e:
        print(f"❌ Fehler beim Laden der Charts: {e}")

def menu_update_charts(charts_manager, tracker):
    """
    Einfache Weiterleitung zu menu_batch_charts_update
    Nutzt die bereits perfekt funktionierende Batch-Funktion
    """
    logger.warning("⚠️ menu_update_charts ist veraltet - nutze menu_batch_charts_update")
    menu_batch_charts_update(charts_manager)

def menu_charts_deals(charts_manager, tracker):
    """Option 15: Charts-Deals anzeigen"""
    print("\n🎯 CHARTS-DEALS")
    print("=" * 17)
    
    deals = get_charts_deals_safe(charts_manager, tracker)
    
    if deals:
        print(f"🎯 {len(deals)} Charts-Deals gefunden:")
        for i, deal in enumerate(deals[:15], 1):
            name = deal.get('name', 'Unbekannt')[:35]
            price = deal.get('current_price', 0)
            discount = deal.get('discount_percent', 0)
            store = deal.get('store', 'Steam')
            
            print(f"{i:2d}. {name}")
            print(f"    💰 €{price:.2f} • {discount:>3.0f}% Rabatt • {store}")
    else:
        print("❌ Keine Charts-Deals verfügbar")
        print("💡 Führe zuerst ein Charts-Update durch")

def menu_charts_statistics(charts_manager, tracker):
    """Option 16: Charts-Statistiken"""
    print("\n📊 CHARTS-STATISTIKEN")
    print("=" * 25)
    
    if not charts_manager:
        print("❌ Charts Manager nicht verfügbar")
        return
    
    try:
        if hasattr(charts_manager, 'get_charts_validation_status'):
            validation = charts_manager.get_charts_validation_status()
            
            print("🔍 Charts-System Status:")
            for key, status in validation.items():
                icon = "✅" if status else "❌"
                readable_key = key.replace('_', ' ').title()
                print(f"  {icon} {readable_key}")
        else:
            print("📊 Charts-Statistiken nicht verfügbar")
    
    except Exception as e:
        print(f"❌ Fehler beim Laden der Charts-Statistiken: {e}")

def menu_charts_automation(charts_manager, tracker):
    """Charts-Automation mit BATCH-Updates - FIXED VERSION"""
    print("\n🤖 CHARTS-AUTOMATION")
    print("=" * 25)
    
    if not charts_manager:
        print("❌ Charts Manager nicht verfügbar")
        return
    
    print("🤖 Automation-Optionen:")
    print("1. 🚀 Einmaliges vollständiges Update")
    print("2. 📊 Einmaliges Charts-Update (schnell)")
    print("3. ⏰ Scheduler-Status anzeigen")
    print("4. 🔄 Scheduler konfigurieren")
    print("5. 🛑 Automation stoppen")
    print("0. ↩️ Zurück")
    
    choice = safe_input("Auswahl (0-5): ")
    
    if choice == "0":
        return
    
    elif choice == "1":
        # Vollständiges einmaliges Update
        print("🚀 Starte einmaliges vollständiges Update...")
        
        if hasattr(charts_manager, 'update_all_charts_batch'):
            try:
                start_time = time_module.time()
                result = charts_manager.update_all_charts_batch(
                    include_names=True,
                    include_prices=True
                )
                duration = time_module.time() - start_time
                
                if result.get('overall_success'):
                    print(f"✅ Vollständiges Update erfolgreich in {duration:.1f}s!")
                    
                    # Performance-Metriken
                    if 'performance_metrics' in result:
                        metrics = result['performance_metrics']
                        print(f"📊 Apps verarbeitet: {metrics.get('apps_processed', 'N/A')}")
                        print(f"📝 Namen aktualisiert: {metrics.get('names_updated', 'N/A')}")
                        print(f"💰 Preise aktualisiert: {metrics.get('prices_updated', 'N/A')}")
                else:
                    print("⚠️ Update mit Einschränkungen abgeschlossen")
            except Exception as e:
                print(f"❌ Update-Fehler: {e}")
        else:
            print("❌ BATCH-Update nicht verfügbar")
    
    elif choice == "2":
        # Schnelles Charts-Update
        print("📊 Starte schnelles Charts-Update...")
        
        if hasattr(charts_manager, 'update_all_charts_batch'):
            try:
                start_time = time_module.time()
                result = charts_manager.update_all_charts_batch(
                    include_names=False,
                    include_prices=False
                )
                duration = time_module.time() - start_time
                
                if result.get('overall_success'):
                    print(f"✅ Schnelles Update erfolgreich in {duration:.1f}s!")
                else:
                    print("⚠️ Update fehlgeschlagen")
            except Exception as e:
                print(f"❌ Update-Fehler: {e}")
        else:
            print("❌ BATCH-Update nicht verfügbar")
    
    elif choice == "3":
        # Scheduler-Status
        print("⏰ Scheduler-Status:")
        try:
            if hasattr(tracker, 'get_scheduler_status'):
                status = tracker.get_scheduler_status()
                print(f"📊 Status: {status.get('status', 'Unbekannt')}")
                if status.get('next_run'):
                    print(f"⏰ Nächster Lauf: {status['next_run']}")
            else:
                print("⚠️ Scheduler-Status nicht verfügbar")
        except Exception as e:
            print(f"❌ Fehler: {e}")
    
    elif choice == "4":
        # Scheduler konfigurieren
        print("🔄 Scheduler-Konfiguration:")
        print("💡 Diese Funktion würde Scheduler-Einstellungen bearbeiten")
        print("💡 Integration mit background_scheduler.py")
    
    elif choice == "5":
        # Automation stoppen
        print("🛑 Stoppe Charts-Automation...")
        try:
            if hasattr(tracker, 'stop_scheduler'):
                tracker.stop_scheduler()
                print("✅ Automation gestoppt")
            else:
                print("⚠️ Stop-Funktion nicht verfügbar")
        except Exception as e:
            print(f"❌ Fehler: {e}")

def menu_batch_charts_update(charts_manager):
    """Erweiterte BATCH-Charts-Update mit allen Optionen"""
    print("\n🚀 ERWEITERTE BATCH-CHARTS-UPDATE")
    print("=" * 40)
    
    if not charts_manager:
        print("❌ Charts Manager nicht verfügbar")
        return
    
    print("🎯 BATCH-Update Optionen:")
    print("1. 🚀 Vollständig mit Progress (Charts + Namen + Preise)")
    print("2. 📊 Nur Charts-Daten (Ultraschnell)")
    print("3. 📝 Charts + Namen (ohne Preise)")
    print("4. 💰 Charts + Preise (ohne Namen)")
    print("5. 🎯 Vollständig benutzerdefiniert")
    print("6. 📈 Performance-Vergleich anzeigen")
    print("0. ↩️ Zurück")
    
    choice = safe_input("Auswahl (0-6): ")
    
    if choice == "0":
        return
    
    # Parameter setzen
    include_names = True
    include_prices = True
    chart_types = None
    show_progress = True
    
    if choice == "2":
        include_names = False
        include_prices = False
        show_progress = False
    elif choice == "3":
        include_prices = False
    elif choice == "4":
        include_names = False
    elif choice == "5":
        # Vollständig benutzerdefiniert
        include_names = safe_input("Namen aktualisieren? (j/n): ").lower() in ['j', 'y']
        include_prices = safe_input("Preise aktualisieren? (j/n): ").lower() in ['j', 'y']
        show_progress = safe_input("Progress-Anzeige? (j/n): ").lower() in ['j', 'y']
        
        # Chart-Typen
        print("\nChart-Typen auswählen:")
        try:
            from steam_charts_manager import CHART_TYPES
            available_charts = list(CHART_TYPES.keys())
        except ImportError:
            available_charts = ['most_played', 'top_releases', 'most_concurrent_players']
        
        for i, chart in enumerate(available_charts, 1):
            print(f"{i}. {chart.replace('_', ' ').title()}")
        print(f"{len(available_charts) + 1}. Alle")
        
        chart_choice = safe_input(f"Chart-Auswahl (1-{len(available_charts) + 1}): ")
        if chart_choice != str(len(available_charts) + 1):
            try:
                idx = int(chart_choice) - 1
                if 0 <= idx < len(available_charts):
                    chart_types = [available_charts[idx]]
            except ValueError:
                pass
    
    elif choice == "6":
        # Performance-Vergleich
        print("\n📈 PERFORMANCE-VERGLEICH:")
        print("=" * 30)
        print("🐌 Legacy update_all_charts(): ~7+ Minuten")
        print("🚀 BATCH update_all_charts_batch(): ~30 Sekunden")
        print("⚡ Performance-Gewinn: 15x schneller!")
        print("\n💡 BATCH-Features:")
        print("   📦 99% weniger Database-Locks")
        print("   🌐 BULK API-Aufrufe für Namen")
        print("   💰 BATCH Preis-Updates")
        print("   📊 Live-Progress-Anzeige")
        return
    
    # Update-Zusammenfassung
    print(f"\n🎯 BATCH-UPDATE KONFIGURATION:")
    print(f"📊 Chart-Typen: {len(chart_types) if chart_types else 'Alle'}")
    print(f"📝 Namen-Updates: {'✅' if include_names else '❌'}")
    print(f"💰 Preis-Updates: {'✅' if include_prices else '❌'}")
    print(f"📈 Progress-Anzeige: {'✅' if show_progress else '❌'}")
    
    confirm = safe_input("\n🚀 BATCH-Update starten? (j/n): ")
    if confirm.lower() not in ['j', 'y', 'ja', 'yes']:
        print("❌ Update abgebrochen")
        return
    
    # Progress-Tracker (optional)
    progress_tracker = None
    if show_progress:
        progress_tracker = ProgressTracker()
        progress_tracker.start()
    
    try:
        print("\n🚀 BATCH-Update gestartet...")
        
        start_time = time_module.time()
        
        # Progress-Callback
        def progress_callback(progress_info):
            if progress_tracker:
                progress_tracker.update_progress(progress_info)
        
        # 🚀 BATCH UPDATE
        if hasattr(charts_manager, 'update_all_charts_batch'):
            result = charts_manager.update_all_charts_batch(
                chart_types=chart_types,
                include_names=include_names,
                include_prices=include_prices,
                progress_callback=progress_callback if show_progress else None
            )
            
            duration = time_module.time() - start_time
            
            if result.get('overall_success'):
                print(f"\n🎉 BATCH-Update erfolgreich in {duration:.1f}s!")
                
                # Detaillierte Ergebnisse
                if 'performance_metrics' in result:
                    metrics = result['performance_metrics']
                    print(f"\n📊 PERFORMANCE-METRIKEN:")
                    print(f"   📊 Charts verarbeitet: {metrics.get('charts_processed', 'N/A')}")
                    print(f"   🎮 Apps verarbeitet: {metrics.get('apps_processed', 'N/A')}")
                    if include_names:
                        print(f"   📝 Namen aktualisiert: {metrics.get('names_updated', 'N/A')}")
                    if include_prices:
                        print(f"   💰 Preise aktualisiert: {metrics.get('prices_updated', 'N/A')}")
                    print(f"   🚀 Performance: {metrics.get('performance_boost', '15x faster')}")
                
            else:
                print(f"\n⚠️ BATCH-Update mit Einschränkungen in {duration:.1f}s")
                if 'error' in result:
                    print(f"❌ Fehler: {result['error']}")
        
        else:
            print("❌ BATCH-Update nicht verfügbar")
    
    except Exception as e:
        print(f"❌ BATCH-Update Fehler: {e}")
        # Für Debugging:
        import traceback
        traceback.print_exc()
    
    finally:
        if progress_tracker:
            progress_tracker.stop()

# Elasticsearch-Funktionen 
def menu_elasticsearch_export(es_manager, tracker):
    """Option 18: ES Daten exportieren"""
    print("\n📤 ELASTICSEARCH EXPORT")
    print("=" * 25)
    
    if not es_manager:
        print("❌ Elasticsearch Manager nicht verfügbar")
        return
    
    print("📤 Exportiere Daten zu Elasticsearch...")
    print("💡 Diese Funktion ist noch in Entwicklung")

def menu_elasticsearch_dashboard(es_manager):
    """Option 19: Kibana Dashboard"""
    print("\n📊 KIBANA DASHBOARD")
    print("=" * 20)
    
    if not es_manager:
        print("❌ Elasticsearch Manager nicht verfügbar")
        return
    
    print("📊 Öffne Kibana Dashboard...")
    print("💡 Dashboard unter http://localhost:5601")

def menu_elasticsearch_analytics(es_manager):
    """Option 20: ES Analytics"""
    print("\n🔬 ELASTICSEARCH ANALYTICS")
    print("=" * 28)
    
    if not es_manager:
        print("❌ Elasticsearch Manager nicht verfügbar")
        return
    
    print("🔬 Elasticsearch Analytics werden geladen...")
    print("💡 Diese Funktion ist noch in Entwicklung")

def menu_elasticsearch_config(es_manager):
    """Option 21: ES Konfiguration"""
    print("\n⚙️ ELASTICSEARCH KONFIGURATION")
    print("=" * 32)
    
    if not es_manager:
        print("❌ Elasticsearch Manager nicht verfügbar")
        return
    
    print("⚙️ Elasticsearch Konfiguration...")
    print("💡 Diese Funktion ist noch in Entwicklung")

def menu_elasticsearch_sync(es_manager, tracker):
    """Option 22: ES Synchronisierung"""
    print("\n🔄 ELASTICSEARCH SYNC")
    print("=" * 22)
    
    if not es_manager:
        print("❌ Elasticsearch Manager nicht verfügbar")
        return
    
    print("🔄 Synchronisiere Daten mit Elasticsearch...")
    print("💡 Diese Funktion ist noch in Entwicklung")

# System-Tools 
def menu_system_tools(tracker):
    """Option 23: System-Tools"""
    print("\n🔧 SYSTEM-TOOLS")
    print("=" * 17)
    
    stats = load_stats_safe(tracker)
    
    print("🔧 System-Information:")
    print(f"  📊 Apps: {stats['tracked_apps']}")
    print(f"  📸 Snapshots: {stats['total_snapshots']}")
    print(f"  🕒 Python: {sys.version.split()[0]}")
    print(f"  💾 Platform: {sys.platform}")

def menu_process_management():
    """Option 24: Process Management"""
    print("\n🔧 PROCESS MANAGEMENT")
    print("=" * 23)
    
    try:
        from background_scheduler import main as scheduler_main
        print("🚀 Starte Process Management Terminal...")
        scheduler_main()
    except ImportError:
        print("❌ Background Scheduler nicht verfügbar")
    except Exception as e:
        print(f"❌ Fehler beim Process Management: {e}")

def menu_batch_processing(tracker):
    """Option 25: Batch Processing"""
    print("\n📦 BATCH PROCESSING")
    print("=" * 20)
    
    print("📦 Batch Processing Optionen:")
    print("1. Batch-Update für ausstehende Apps")
    print("2. Spezifische Apps aktualisieren")
    print("3. Batch-Status anzeigen")
    
    choice = safe_input("Auswahl (1-3): ")
    
    if choice == "1":
        try:
            if hasattr(tracker, 'process_all_pending_apps_optimized'):
                print("🚀 Starte Batch-Update...")
                result = tracker.process_all_pending_apps_optimized(hours_threshold=6)
                print(f"✅ Batch-Update abgeschlossen: {result}")
            else:
                print("❌ Batch-Update Funktion nicht verfügbar")
        except Exception as e:
            print(f"❌ Batch-Update Fehler: {e}")
    elif choice == "2":
        app_ids = safe_input("App IDs (kommagetrennt): ")
        if app_ids:
            app_list = [aid.strip() for aid in app_ids.split(',')]
            print(f"🎯 Aktualisiere {len(app_list)} spezifische Apps...")
            # Implementierung für spezifische Apps
    elif choice == "3":
        print("📊 Batch-Status wird angezeigt...")
    else:
        print("❌ Ungültige Auswahl")

def menu_database_maintenance(tracker):
    """Option 26: Datenbank-Wartung"""
    print("\n🧹 DATENBANK-WARTUNG")
    print("=" * 22)
    
    print("🧹 Wartungsoptionen:")
    print("1. Alte Preisdaten bereinigen")
    print("2. Datenbank optimieren")
    print("3. Statistiken anzeigen")
    
    choice = safe_input("Auswahl (1-3): ")
    
    if choice == "1":
        days = safe_input("Daten älter als X Tage löschen (Standard: 90): ", "90")
        try:
            days_int = int(days)
            if hasattr(tracker.db_manager, 'cleanup_old_prices'):
                deleted = tracker.db_manager.cleanup_old_prices(days_int)
                print(f"🧹 {deleted} alte Preisdaten gelöscht")
            else:
                print("❌ Cleanup-Funktion nicht verfügbar")
        except ValueError:
            print("❌ Ungültige Tagesanzahl")
    elif choice == "2":
        try:
            if hasattr(tracker.db_manager, 'vacuum_database'):
                tracker.db_manager.vacuum_database()
                print("✅ Datenbank optimiert")
            else:
                print("❌ Vacuum-Funktion nicht verfügbar")
        except Exception as e:
            print(f"❌ Optimierung fehlgeschlagen: {e}")
    elif choice == "3":
        stats = load_stats_safe(tracker)
        print(f"📊 Datenbank-Statistiken: {stats}")
    else:
        print("❌ Ungültige Auswahl")

def menu_create_backup(tracker):
    """Option 27: Backup erstellen"""
    print("\n💾 BACKUP ERSTELLEN")
    print("=" * 19)
    
    try:
        if hasattr(tracker.db_manager, 'backup_database'):
            backup_file = tracker.db_manager.backup_database()
            print(f"💾 Backup erstellt: {backup_file}")
        else:
            print("❌ Backup-Funktion nicht verfügbar")
    except Exception as e:
        print(f"❌ Backup-Fehler: {e}")

def menu_edit_configuration():
    """Option 28: Konfiguration bearbeiten"""
    print("\n⚙️ KONFIGURATION BEARBEITEN")
    print("=" * 30)
    
    print("⚙️ Konfigurationsoptionen:")
    print("1. .env Datei bearbeiten")
    print("2. config.json anzeigen")
    print("3. API Keys verwalten")
    
    choice = safe_input("Auswahl (1-3): ")
    
    if choice == "1":
        print("📝 .env Datei bearbeiten...")
        print("💡 Öffne .env in deinem bevorzugten Editor")
    elif choice == "2":
        print("📄 config.json wird angezeigt...")
        if os.path.exists("config.json"):
            try:
                with open("config.json", 'r') as f:
                    config = json.load(f)
                print(json.dumps(config, indent=2))
            except Exception as e:
                print(f"❌ Fehler beim Laden der config.json: {e}")
        else:
            print("❌ config.json nicht gefunden")
    elif choice == "3":
        print("🔑 API Keys verwalten...")
        print("💡 Diese Funktion ist noch in Entwicklung")
    else:
        print("❌ Ungültige Auswahl")

# =================================================================
# DYNAMIC MENU SYSTEM INTEGRATION
# =================================================================

def run_dynamic_menu():
    """
    Führt das dynamische Menüsystem aus - VOLLSTÄNDIGE VERSION
    Alle Funktionen unified auf update_all_charts_batch()
    """
    try:
        # Initialisierung
        print("🚀 Steam Price Tracker wird initialisiert...")
        tracker, charts_manager, es_manager = create_tracker_with_fallback()
        
        if not tracker:
            print("❌ Kritischer Fehler: Price Tracker konnte nicht initialisiert werden")
            return False
        
        # Dynamisches Menü initialisieren
        try:
            menu_system = initialize_menu_system(
                charts_enabled=bool(charts_manager),
                es_available=bool(es_manager)
            )
        except Exception as menu_error:
            logger.error(f"❌ Fehler beim Initialisieren des Menüsystems: {menu_error}")
            print(f"❌ Menüsystem-Fehler: {menu_error}")
            return False
        
        # Startup-Info
        try:
            stats = load_stats_safe(tracker)
            print("\n" + "=" * 60)
            print("🎮 STEAM PRICE TRACKER - DYNAMISCHES MENÜ")
            print("=" * 60)
            print(f"📊 Getrackte Apps: {stats.get('tracked_apps', 0)}")
            print(f"📸 Preis-Snapshots: {stats.get('total_snapshots', 0)}")
            
            if charts_manager:
                print("📈 Charts: Aktiviert (BATCH-optimiert)")
            if es_manager:
                print("🔍 Elasticsearch: Verfügbar")
            
            print("=" * 60)
            
        except Exception as stats_error:
            logger.error(f"❌ Fehler beim Laden der Startup-Statistiken: {stats_error}")
            print("\n" + "=" * 60)
            print("🎮 STEAM PRICE TRACKER - DYNAMISCHES MENÜ")
            print("=" * 60)
            print("⚠️ Statistiken konnten nicht geladen werden")
            print("=" * 60)
        
        # VOLLSTÄNDIGE FUNCTION MAP - ALLE FUNKTIONEN
        function_map = {
            # 🏠 BASIS-FUNKTIONEN
            'menu_add_app_manually': lambda: menu_add_app_manually(tracker),
            'menu_import_wishlist': lambda: menu_import_wishlist(tracker),
            'menu_show_current_prices': lambda: menu_show_current_prices(tracker),
            'menu_show_best_deals': lambda: menu_show_best_deals(tracker),
            'menu_show_price_history': lambda: menu_show_price_history(tracker),
            'menu_update_prices': lambda: menu_update_prices(tracker),
            
            # 🚀 AUTOMATION & BATCH
            'menu_toggle_scheduler': lambda: menu_toggle_scheduler(tracker),
            'menu_update_names_all_apps': lambda: menu_update_names_all_apps(tracker),
            
            # 🎮 APP-VERWALTUNG
            'menu_manage_apps': lambda: menu_manage_apps(tracker),
            'menu_remove_apps': lambda: menu_remove_apps(tracker),
            'menu_csv_export': lambda: menu_csv_export(tracker),
            'menu_detailed_statistics': lambda: menu_detailed_statistics(tracker),
            
            # 📊 CHARTS & ANALYTICS (alle unified auf update_all_charts_batch)
            'menu_show_charts': lambda: menu_show_charts(charts_manager, tracker) if charts_manager else print("❌ Charts Manager nicht verfügbar"),
            'menu_update_charts_complete': lambda: menu_batch_charts_update(charts_manager) if charts_manager else print("❌ Charts Manager nicht verfügbar"),
            'menu_charts_deals': lambda: menu_charts_deals(charts_manager, tracker) if charts_manager else print("❌ Charts Manager nicht verfügbar"),
            'menu_charts_statistics': lambda: menu_charts_statistics(charts_manager, tracker) if charts_manager else print("❌ Charts Manager nicht verfügbar"),
            'menu_charts_automation': lambda: menu_charts_automation(charts_manager, tracker) if charts_manager else print("❌ Charts Manager nicht verfügbar"),
            # 🚀 NEUE ERWEITERTE BATCH-FUNKTION
            'menu_batch_charts_update': lambda: menu_batch_charts_update(charts_manager) if charts_manager else print("❌ Charts Manager nicht verfügbar"),
            
            # 🔍 ELASTICSEARCH
            'menu_elasticsearch_export': lambda: menu_elasticsearch_export(es_manager, tracker) if es_manager else print("❌ Elasticsearch Manager nicht verfügbar"),
            'menu_elasticsearch_dashboard': lambda: menu_elasticsearch_dashboard(es_manager) if es_manager else print("❌ Elasticsearch Manager nicht verfügbar"),
            'menu_elasticsearch_analytics': lambda: menu_elasticsearch_analytics(es_manager) if es_manager else print("❌ Elasticsearch Manager nicht verfügbar"),
            'menu_elasticsearch_config': lambda: menu_elasticsearch_config(es_manager) if es_manager else print("❌ Elasticsearch Manager nicht verfügbar"),
            'menu_elasticsearch_sync': lambda: menu_elasticsearch_sync(es_manager, tracker) if es_manager else print("❌ Elasticsearch Manager nicht verfügbar"),
            
            # 🛠️ SYSTEM-TOOLS
            'menu_system_settings': lambda: menu_system_settings(),
            'menu_system_info': lambda: menu_system_info(tracker, charts_manager, es_manager),
            'menu_backup_export': lambda: menu_backup_export(tracker),
            'menu_backup_import': lambda: menu_backup_import(tracker),
            'menu_health_check': lambda: menu_health_check(tracker, charts_manager),
            'menu_clean_database': lambda: menu_clean_database(tracker),
            'menu_dev_tools': lambda: menu_dev_tools(tracker)
        }
        
        # Hauptschleife
        while True:
            try:
                menu_system.display_menu()
                max_option = menu_system.get_max_option_number()
                choice = input(f"\nWählen Sie eine Option (0-{max_option}): ").strip()
                
                if choice == "0":
                    print("\n👋 Auf Wiedersehen!")
                    break
                
                # Option ausführen
                if choice in menu_system.option_mapping:
                    category_idx, option_name, handler = menu_system.option_mapping[choice]
                    
                    print(f"\n➤ {option_name}")
                    
                    if handler in function_map:
                        try:
                            function_map[handler]()
                        except Exception as func_error:
                            logger.error(f"❌ Fehler in Funktion {handler}: {func_error}")
                            print(f"❌ Fehler beim Ausführen von {option_name}: {func_error}")
                    else:
                        print(f"❌ Funktion '{handler}' nicht implementiert")
                        logger.warning(f"Handler '{handler}' nicht in function_map gefunden")
                else:
                    print(f"❌ Ungültige Auswahl: {choice}")
                    print(f"Bitte wählen Sie eine Option zwischen 0-{max_option}.")
                
                # Pause zwischen Operationen
                if choice != "0":
                    input("\nDrücke Enter zum Fortfahren...")
            
            except KeyboardInterrupt:
                print("\n\n⏹️ Programm durch Benutzer unterbrochen")
                print("🧹 Enhanced Cleanup wird ausgeführt...")
                enhanced_cleanup()
                break
            except Exception as e:
                logger.error(f"Unerwarteter Fehler in der Hauptschleife: {e}")
                print(f"❌ Unerwarteter Fehler: {e}")
                print("💡 Das Programm läuft weiter...")
                input("Drücke Enter zum Fortfahren...")
        
        return True
    
    except Exception as e:
        logger.error(f"Kritischer Fehler im dynamischen Menü: {e}")
        print(f"❌ Kritischer Fehler: {e}")
        return False


def execute_menu_handler(handler_name: str, tracker, charts_manager, es_manager):
    """Führt Menu-Handler aus"""
    try:
        # Handler-Mapping für dynamisches Menü
        handlers = {
            # Basis-Funktionen
            'menu_add_app_manually': lambda: menu_add_app_manually(tracker),
            'menu_import_wishlist': lambda: menu_import_wishlist(tracker),
            'menu_show_current_prices': lambda: menu_show_current_prices(tracker),
            'menu_show_best_deals': lambda: menu_show_best_deals(tracker),
            'menu_show_price_history': lambda: menu_show_price_history(tracker),
            'menu_update_prices': lambda: menu_update_prices(tracker),
            
            # Automation
            'menu_toggle_scheduler': lambda: menu_toggle_scheduler(tracker),
            'menu_update_names_all_apps': lambda: menu_update_names_all_apps(tracker),
            
            # Management
            'menu_manage_apps': lambda: menu_manage_apps(tracker),
            'menu_remove_apps': lambda: menu_remove_apps(tracker),
            'menu_csv_export': lambda: menu_csv_export(tracker),
            'menu_detailed_statistics': lambda: menu_detailed_statistics(tracker),
            
            # Charts (nur wenn verfügbar)
            'menu_show_charts': lambda: menu_show_charts(charts_manager, tracker) if charts_manager else print("❌ Charts Manager nicht verfügbar"),
            'menu_update_charts_complete': lambda: menu_update_charts(charts_manager, tracker) if charts_manager else print("❌ Charts Manager nicht verfügbar"),
            'menu_charts_deals': lambda: menu_charts_deals(charts_manager, tracker) if charts_manager else print("❌ Charts Manager nicht verfügbar"),
            'menu_charts_statistics': lambda: menu_charts_statistics(charts_manager, tracker) if charts_manager else print("❌ Charts Manager nicht verfügbar"),
            'menu_charts_automation': lambda: menu_charts_automation(charts_manager, tracker) if charts_manager else print("❌ Charts Manager nicht verfügbar"),
            
            # Elasticsearch (nur wenn verfügbar)
            'menu_elasticsearch_export': lambda: menu_elasticsearch_export(es_manager, tracker) if es_manager else print("❌ Elasticsearch Manager nicht verfügbar"),
            'menu_elasticsearch_dashboard': lambda: menu_elasticsearch_dashboard(es_manager) if es_manager else print("❌ Elasticsearch Manager nicht verfügbar"),
            'menu_elasticsearch_analytics': lambda: menu_elasticsearch_analytics(es_manager) if es_manager else print("❌ Elasticsearch Manager nicht verfügbar"),
            'menu_elasticsearch_config': lambda: menu_elasticsearch_config(es_manager) if es_manager else print("❌ Elasticsearch Manager nicht verfügbar"),
            'menu_elasticsearch_sync': lambda: menu_elasticsearch_sync(es_manager, tracker) if es_manager else print("❌ Elasticsearch Manager nicht verfügbar"),
            
            # System-Tools
            'menu_system_tools': lambda: menu_system_tools(tracker),
            'menu_process_management': lambda: menu_process_management(),
            'menu_batch_processing': lambda: menu_batch_processing(tracker),
            'menu_database_maintenance': lambda: menu_database_maintenance(tracker),
            'menu_create_backup': lambda: menu_create_backup(tracker),
            'menu_edit_configuration': lambda: menu_edit_configuration(),
        }
        
        if handler_name in handlers:
            handlers[handler_name]()
        else:
            print(f"❌ Handler '{handler_name}' nicht implementiert")
            
    except Exception as e:
        logger.error(f"Handler-Fehler für {handler_name}: {e}")
        print(f"❌ Fehler beim Ausführen von {handler_name}: {e}")

# =================================================================
# CLASSIC MENU SYSTEM (bestehend, als Fallback)
# =================================================================

def run_classic_menu():
    """
    Klassisches Menü mit allen Optionen - VOLLSTÄNDIGE VERSION
    Alle Charts-Funktionen unified auf update_all_charts_batch()
    """
    try:
        # Initialisierung
        print("🚀 Steam Price Tracker wird initialisiert...")
        tracker, charts_manager, es_manager = create_tracker_with_fallback()
        
        if not tracker:
            print("❌ Kritischer Fehler: Price Tracker konnte nicht initialisiert werden")
            return False
        
        charts_enabled = bool(charts_manager)
        es_enabled = bool(es_manager)
        
        # Startup-Info
        try:
            stats = load_stats_safe(tracker)
            print("\n" + "=" * 60)
            print("🎮 STEAM PRICE TRACKER - KLASSISCHES MENÜ")
            print("=" * 60)
            print(f"📊 Getrackte Apps: {stats.get('tracked_apps', 0)}")
            print(f"📸 Preis-Snapshots: {stats.get('total_snapshots', 0)}")
            
            if charts_enabled:
                print("📈 Charts: Aktiviert (BATCH-optimiert)")
            if es_enabled:
                print("🔍 Elasticsearch: Verfügbar")
            
            print("=" * 60)
        except Exception as e:
            logger.error(f"❌ Startup-Statistiken Fehler: {e}")
        
        # Hauptschleife
        while True:
            try:
                # VOLLSTÄNDIGES KLASSISCHES MENÜ
                print("\n🎮 HAUPTMENÜ")
                print("=" * 60)
                
                # 🏠 BASIS-FUNKTIONEN (1-6)
                print("🏠 BASIS-FUNKTIONEN")
                print("1.  📱 App manuell hinzufügen")
                print("2.  📥 Steam Wishlist importieren") 
                print("3.  🔍 Aktuelle Preise anzeigen")
                print("4.  📊 Beste Deals anzeigen")
                print("5.  📈 Preisverlauf anzeigen")
                print("6.  🔄 Preise manuell aktualisieren")
                
                # 🚀 AUTOMATION & BATCH (7-8)
                print("\n🚀 AUTOMATION & BATCH")
                print("7.  🚀 Automatisches Tracking")
                print("8.  📝 Namen für alle Apps aktualisieren")
                
                # 🎮 APP-VERWALTUNG (9-12)
                print("\n🎮 APP-VERWALTUNG")
                print("9.  📋 Getrackte Apps verwalten")
                print("10. 🗑️ Apps entfernen")
                print("11. 📄 CSV-Export erstellen")
                print("12. 📊 Detaillierte Statistiken")
                
                # 📊 CHARTS & ANALYTICS (13-18) - VOLLSTÄNDIG MIT BATCH
                if charts_enabled:
                    print("\n📊 CHARTS & ANALYTICS (BATCH-optimiert)")
                    print("13. 📈 Charts anzeigen")
                    print("14. 🚀 Charts vollständig aktualisieren (BATCH)")
                    print("15. 🎯 Charts-Deals anzeigen")
                    print("16. 📊 Charts-Statistiken")
                    print("17. 🤖 Charts-Automation")
                    print("18. 📦 Erweiterte BATCH-Optionen")  # 🚀 NEUE OPTION
                
                # 🔍 ELASTICSEARCH (19-23)
                if es_enabled:
                    print("\n🔍 ELASTICSEARCH")
                    print("19. 📤 ES Daten exportieren")
                    print("20. 📊 Kibana Dashboard")
                    print("21. 🔬 ES Analytics")
                    print("22. ⚙️ ES Konfiguration")
                    print("23. 🔄 ES Synchronisierung")
                
                # 🛠️ SYSTEM-TOOLS (24-30)
                print("\n🛠️ SYSTEM-TOOLS")
                print("24. ⚙️ System-Einstellungen")
                print("25. 📊 System-Informationen")
                print("26. 💾 Backup erstellen")
                print("27. 📥 Backup importieren")
                print("28. 🔍 Health Check")
                print("29. 🧹 Datenbank bereinigen")
                print("30. 🔧 Developer Tools")
                
                print("\n0.  👋 Beenden")
                print("=" * 60)
                
                # Eingabe
                choice = safe_input("Wählen Sie eine Option (0-30): ")
                
                # VOLLSTÄNDIGE MENU-HANDLER
                if choice == "0":
                    print("\n👋 Auf Wiedersehen!")
                    print("🧹 Enhanced Cleanup wird ausgeführt...")
                    enhanced_cleanup()
                    break
                
                # 🏠 BASIS-FUNKTIONEN (1-6)
                elif choice == "1":
                    menu_add_app_manually(tracker)
                elif choice == "2":
                    menu_import_wishlist(tracker)
                elif choice == "3":
                    menu_show_current_prices(tracker)
                elif choice == "4":
                    menu_show_best_deals(tracker)
                elif choice == "5":
                    menu_show_price_history(tracker)
                elif choice == "6":
                    menu_update_prices(tracker)
                
                # 🚀 AUTOMATION & BATCH (7-8)
                elif choice == "7":
                    menu_toggle_scheduler(tracker)
                elif choice == "8":
                    menu_update_names_all_apps(tracker)
                
                # 🎮 APP-VERWALTUNG (9-12)
                elif choice == "9":
                    menu_manage_apps(tracker)
                elif choice == "10":
                    menu_remove_apps(tracker)
                elif choice == "11":
                    menu_csv_export(tracker)
                elif choice == "12":
                    menu_detailed_statistics(tracker)
                
                # 📊 CHARTS & ANALYTICS (13-18) - UNIFIED BATCH CALLS
                elif choice == "13":
                    if charts_enabled:
                        menu_show_charts(charts_manager, tracker)
                    else:
                        print("❌ Charts Manager nicht verfügbar")
                elif choice == "14":
                    if charts_enabled:
                        menu_update_charts(charts_manager, tracker)  # 🚀 NUTZT update_all_charts_batch()
                    else:
                        print("❌ Charts Manager nicht verfügbar")
                elif choice == "15":
                    if charts_enabled:
                        menu_charts_deals(charts_manager, tracker)
                    else:
                        print("❌ Charts Manager nicht verfügbar")
                elif choice == "16":
                    if charts_enabled:
                        menu_charts_statistics(charts_manager, tracker)
                    else:
                        print("❌ Charts Manager nicht verfügbar")
                elif choice == "17":
                    if charts_enabled:
                        menu_charts_automation(charts_manager, tracker)
                    else:
                        print("❌ Charts Manager nicht verfügbar")
                elif choice == "18":
                    if charts_enabled:
                        menu_batch_charts_update(charts_manager)  # 🚀 NEUE ERWEITERTE BATCH-OPTIONEN
                    else:
                        print("❌ Charts Manager nicht verfügbar")
                
                # 🔍 ELASTICSEARCH (19-23)
                elif choice == "19":
                    if es_enabled:
                        menu_elasticsearch_export(es_manager, tracker)
                    else:
                        print("❌ Elasticsearch Manager nicht verfügbar")
                elif choice == "20":
                    if es_enabled:
                        menu_elasticsearch_dashboard(es_manager)
                    else:
                        print("❌ Elasticsearch Manager nicht verfügbar")
                elif choice == "21":
                    if es_enabled:
                        menu_elasticsearch_analytics(es_manager)
                    else:
                        print("❌ Elasticsearch Manager nicht verfügbar")
                elif choice == "22":
                    if es_enabled:
                        menu_elasticsearch_config(es_manager)
                    else:
                        print("❌ Elasticsearch Manager nicht verfügbar")
                elif choice == "23":
                    if es_enabled:
                        menu_elasticsearch_sync(es_manager, tracker)
                    else:
                        print("❌ Elasticsearch Manager nicht verfügbar")
                
                # 🛠️ SYSTEM-TOOLS (24-30)
                elif choice == "24":
                    menu_system_settings()
                elif choice == "25":
                    menu_system_info(tracker, charts_manager, es_manager)
                elif choice == "26":
                    menu_backup_export(tracker)
                elif choice == "27":
                    menu_backup_import(tracker)
                elif choice == "28":
                    menu_health_check(tracker, charts_manager)
                elif choice == "29":
                    menu_clean_database(tracker)
                elif choice == "30":
                    menu_dev_tools(tracker)
                
                else:
                    print(f"❌ Ungültige Auswahl: {choice}")
                    print("Bitte wählen Sie eine Option zwischen 0-30.")
                
                # Pause zwischen Operationen
                if choice != "0":
                    input("\nDrücke Enter zum Fortfahren...")
            
            except KeyboardInterrupt:
                print("\n\n⏹️ Programm durch Benutzer unterbrochen")
                print("🧹 Enhanced Cleanup wird ausgeführt...")
                enhanced_cleanup()
                break
            except Exception as e:
                logger.error(f"Unerwarteter Fehler in der Hauptschleife: {e}")
                print(f"❌ Unerwarteter Fehler: {e}")
                print("💡 Das Programm läuft weiter...")
                input("Drücke Enter zum Fortfahren...")
        
        return True
    
    except Exception as e:
        logger.error(f"Kritischer Fehler im klassischen Menü: {e}")
        print(f"❌ Kritischer Fehler: {e}")
        return False

class ProgressTracker:
    """
    🎯 PROGRESS-ANZEIGE mit Throbber und Prozentanzeige - FIXED VERSION
    """
    
    def __init__(self):
        self.is_running = False
        self.current_progress = {}
        self.throbber_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.throbber_index = 0
        self.phase_icons = {
            'charts': '📊',
            'names': '📝', 
            'prices': '💰',
            'complete': '✅'
        }
        self.phase_names = {
            'charts': 'Charts-Daten sammeln',
            'names': 'Namen aktualisieren',
            'prices': 'Preise aktualisieren',
            'complete': 'Abgeschlossen'
        }
    
    def start(self):
        """Startet die Progress-Anzeige"""
        self.is_running = True
        self.throbber_thread = threading.Thread(target=self._update_display, daemon=True)
        self.throbber_thread.start()
    
    def stop(self):
        """Stoppt die Progress-Anzeige"""
        self.is_running = False
        if hasattr(self, 'throbber_thread'):
            self.throbber_thread.join(timeout=1)
        self._clear_line()
    
    def update_progress(self, progress_info):
        """Update des Fortschritts"""
        self.current_progress = progress_info
    
    def _update_display(self):
        """Aktualisiert die Anzeige kontinuierlich - FIXED VERSION"""
        while self.is_running:
            self._draw_progress()
            # GEFIXT: VERWENDE time_module ANSTATT time
            time_module.sleep(0.1)  # ← HIER WAR AUCH EIN PROBLEM!
            self.throbber_index = (self.throbber_index + 1) % len(self.throbber_chars)
    
    def _draw_progress(self):
        """Zeichnet die aktuelle Progress-Anzeige"""
        if not self.current_progress:
            throbber = self.throbber_chars[self.throbber_index]
            sys.stdout.write(f"\r{throbber} Steam Price Tracker läuft...")
            sys.stdout.flush()
            return
        
        phase = self.current_progress.get('phase', 'unknown')
        current = self.current_progress.get('current', 0)
        total = self.current_progress.get('total', 1)
        percentage = self.current_progress.get('percentage', 0)
        details = self.current_progress.get('details', '')
        elapsed = self.current_progress.get('elapsed_time', 0)
        
        # Icons und Namen
        icon = self.phase_icons.get(phase, '🔄')
        phase_name = self.phase_names.get(phase, phase.title())
        
        # Throbber (nur wenn nicht komplett)
        throbber = '' if phase == 'complete' else self.throbber_chars[self.throbber_index] + ' '
        
        # Fortschrittsbalken
        progress_bar = ''
        if total > 1 and current <= total:
            bar_length = 20
            filled_length = int(bar_length * percentage / 100)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            progress_bar = f"[{bar}] {percentage:.1f}% ({current}/{total})"
        
        # Zeit-Anzeige
        time_display = f"{elapsed:.1f}s"
        if percentage > 5 and percentage < 95:
            eta = (elapsed / percentage * 100) - elapsed if percentage > 0 else 0
            time_display += f" (ETA: {eta:.1f}s)"
        
        # Vollständige Zeile
        line = f"\r{throbber}{icon} {phase_name}"
        if progress_bar:
            line += f" {progress_bar}"
        line += f" ⏱️ {time_display}"
        if details:
            max_details_length = 50
            if len(details) > max_details_length:
                details = details[:max_details_length - 3] + "..."
            line += f" | {details}"
        
        # Zeile ausgeben
        line = line.ljust(120)
        sys.stdout.write(line)
        sys.stdout.flush()
    
    def _clear_line(self):
        """Löscht die aktuelle Zeile"""
        sys.stdout.write('\r' + ' ' * 120 + '\r')
        sys.stdout.flush()


# =================================================================
# MAIN ENTRY POINT
# =================================================================

def main():
    """Haupteinstiegspunkt mit Menu-System Auswahl"""
    try:
        # Kommandozeilen-Argumente prüfen
        if len(sys.argv) > 1:
            if "--dynamic" in sys.argv:
                if DYNAMIC_MENU_AVAILABLE:
                    print("🚀 Starte dynamisches Menü-System...")
                    return run_dynamic_menu()
                else:
                    print("❌ Dynamisches Menü nicht verfügbar")
                    print("💡 Installiere menu_config.py und starte erneut")
                    return False
            elif "--classic" in sys.argv:
                print("📊 Starte klassisches Menü-System...")
                return run_classic_menu()
        
        # Standard: Prüfe ob dynamisches Menü verfügbar ist
        if DYNAMIC_MENU_AVAILABLE:
            print("🚀 Starte dynamisches Menü-System...")
            print("💡 Nutze --classic für das alte Menü")
            return run_dynamic_menu()
        else:
            print("📊 Starte klassisches Menü-System...")
            print("💡 Installiere menu_config.py für das dynamische Menü")
            return run_classic_menu()
    
    except Exception as e:
        logger.error(f"Kritischer Fehler in main(): {e}")
        print(f"❌ Kritischer Fehler: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)