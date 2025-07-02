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
import time

# Core imports (bestehend)
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

# Charts imports (bestehend)
try:
    from steam_charts_manager import CHART_TYPES
    VALID_CHART_TYPES = list(CHART_TYPES.keys())
except ImportError:
    VALID_CHART_TYPES = ['most_played', 'top_releases', 'most_concurrent_players']
    print("⚠️ steam_charts_manager nicht verfügbar - verwende Fallback Chart-Typen")

# Logging Konfiguration (bestehend)
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
    """Erstellt Tracker mit Fallback-Strategien"""
    try:
        tracker = create_price_tracker(enable_charts=True)
        
        # Charts Manager
        charts_manager = None
        if hasattr(tracker, 'charts_manager') and tracker.charts_manager:
            charts_manager = tracker.charts_manager
        
        # Elasticsearch Manager
        es_manager = None
        try:
            from elasticsearch_manager import ElasticsearchManager
            es_manager = ElasticsearchManager()
            if not es_manager.test_connection():
                es_manager = None
        except ImportError:
            pass
        
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
    """Lädt Statistiken sicher"""
    try:
        if hasattr(tracker, 'db_manager') and hasattr(tracker.db_manager, 'get_database_stats'):
            return tracker.db_manager.get_database_stats()
        else:
            return {
                'tracked_apps': len(get_tracked_apps_safe(tracker)),
                'total_snapshots': 0,
                'stores_tracked': [],
                'newest_snapshot': None
            }
    except Exception as e:
        logger.warning(f"⚠️ Fehler beim Laden der Statistiken: {e}")
        return {
            'tracked_apps': 0,
            'total_snapshots': 0,
            'stores_tracked': [],
            'newest_snapshot': None
        }

# =================================================================
# CHARTS OPERATIONS (bestehend, erweitert)
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
# MAIN MENU FUNCTIONS (alle bestehenden + neue)
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
    """Option 14: Charts vollständig aktualisieren (VERBESSERT!)"""
    print("\n🚀 CHARTS VOLLSTÄNDIG AKTUALISIEREN")
    print("=" * 40)
    
    if not charts_manager:
        print("❌ Charts Manager nicht verfügbar")
        return
    
    try:
        # Nutze die neue update_charts_complete Funktion aus steam_charts_manager.py
        if hasattr(charts_manager, 'update_charts_complete'):
            print("🚀 Starte vollständiges Charts-Update...")
            result = charts_manager.update_charts_complete()
            
            if result['overall_success']:
                print("\n🎉 Vollständiges Charts-Update erfolgreich!")
                print("💡 Charts-Deals sind jetzt verfügbar")
            else:
                print("\n⚠️ Update mit Einschränkungen abgeschlossen")
                print("💡 Prüfe die Details oben")
        else:
            # Fallback zu Standard-Update
            print("⚠️ Vollständiges Update nicht verfügbar, nutze Standard-Update...")
            success = update_charts_safe(charts_manager)
            if success:
                print("✅ Standard Charts-Update erfolgreich")
            else:
                print("❌ Charts-Update fehlgeschlagen")
    
    except Exception as e:
        print(f"❌ Fehler beim Charts-Update: {e}")

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
    """Option 17: Charts-Automation"""
    print("\n🤖 CHARTS-AUTOMATION")
    print("=" * 22)
    
    if not charts_manager:
        print("❌ Charts Manager nicht verfügbar")
        return
    
    print("🤖 Charts-Automation Optionen:")
    print("1. Automatisches Charts-Update aktivieren")
    print("2. Charts-Scheduler Status anzeigen")
    print("3. Charts-Automation stoppen")
    
    choice = safe_input("Auswahl (1-3): ")
    
    if choice == "1":
        print("🚀 Aktiviere Charts-Automation...")
        print("💡 Nutze background_scheduler für automatische Updates")
    elif choice == "2":
        print("📊 Charts-Scheduler Status wird angezeigt...")
    elif choice == "3":
        print("⏹️ Charts-Automation wird gestoppt...")
    else:
        print("❌ Ungültige Auswahl")

# Elasticsearch-Funktionen (bestehend)
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

# System-Tools (bestehend)
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
    """Führt das dynamische Menüsystem aus"""
    try:
        # Initialisierung
        print("🚀 Steam Price Tracker wird initialisiert...")
        tracker, charts_manager, es_manager = create_tracker_with_fallback()
        
        if not tracker:
            print("❌ Kritischer Fehler: Price Tracker konnte nicht initialisiert werden")
            return False
        
        # Dynamisches Menü initialisieren
        menu_system = initialize_menu_system(
            charts_enabled=bool(charts_manager),
            es_available=bool(es_manager)
        )
        
        # Startup-Info
        stats = load_stats_safe(tracker)
        print("\n" + "=" * 60)
        print("🎮 STEAM PRICE TRACKER - DYNAMISCHES MENÜ")
        print("=" * 60)
        print(f"📊 Getrackte Apps: {stats['tracked_apps']}")
        print(f"📸 Preis-Snapshots: {stats['total_snapshots']}")
        
        if charts_manager:
            print("📈 Charts: Aktiviert")
        if es_manager:
            print("🔍 Elasticsearch: Verfügbar")
        
        print("=" * 60)
        
        # Hauptschleife
        while True:
            try:
                menu_system.display_menu()
                max_option = menu_system.get_max_option_number()
                choice = input(f"\nWählen Sie eine Option (0-{max_option}): ").strip()
                
                if choice == "0":
                    print("\n👋 Auf Wiedersehen!")
                    print("🧹 Enhanced Cleanup wird ausgeführt...")
                    enhanced_cleanup()
                    break
                
                handler_name = menu_system.get_handler(choice)
                if handler_name:
                    option_info = menu_system.get_option_info(choice)
                    if option_info:
                        _, option_name, _ = option_info
                        print(f"\n➤ {option_name}")
                    
                    # Handler ausführen
                    execute_menu_handler(handler_name, tracker, charts_manager, es_manager)
                else:
                    print(f"❌ Ungültige Auswahl. Bitte wählen Sie zwischen 0-{max_option}")
                
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
    """Führt das klassische Menüsystem aus (27 Optionen)"""
    try:
        # Initialisierung (bestehend)
        print("🎮 STEAM PRICE TRACKER")
        print("=" * 25)
        print("🚀 Initialisiere System...")
        
        tracker, charts_manager, es_manager = create_tracker_with_fallback()
        
        if not tracker:
            print("❌ Kritischer Fehler: Price Tracker konnte nicht initialisiert werden")
            return False
        
        charts_enabled = bool(charts_manager)
        es_available = bool(es_manager)
        
        print(f"✅ System initialisiert!")
        print(f"📊 Charts: {'Aktiviert' if charts_enabled else 'Nicht verfügbar'}")
        print(f"🔍 Elasticsearch: {'Verfügbar' if es_available else 'Nicht verfügbar'}")
        
        # Hauptschleife (bestehend)
        while True:
            try:
                # Menü anzeigen (bestehend)
                print("\n" + "=" * 60)
                print("🎮 STEAM PRICE TRACKER - KLASSISCHES MENÜ")
                print("=" * 60)
                
                # Basis-Funktionen (1-6)
                print("\n🏠 BASIS-FUNKTIONEN")
                print("1.  📱 App manuell hinzufügen")
                print("2.  📥 Steam Wishlist importieren")
                print("3.  🔍 Aktuelle Preise anzeigen")
                print("4.  📊 Beste Deals anzeigen")
                print("5.  📈 Preisverlauf anzeigen")
                print("6.  🔄 Preise manuell aktualisieren")
                
                # Automation (7-8)
                print("\n🚀 AUTOMATION")
                print("7.  🚀 Automatisches Tracking")
                print("8.  📝 Namen für alle Apps aktualisieren")  # NEU!
                
                # Management (9-12)
                print("\n🎮 APP-VERWALTUNG")
                print("9.  📋 Getrackte Apps verwalten")
                print("10. 🗑️ Apps entfernen")
                print("11. 📄 CSV-Export erstellen")
                print("12. 📊 Detaillierte Statistiken")
                
                # Charts (13-17)
                if charts_enabled:
                    print("\n📊 CHARTS & ANALYTICS")
                    print("13. 📈 Charts anzeigen")
                    print("14. 🔄 Charts vollständig aktualisieren")  # VERBESSERT!
                    print("15. 🎯 Charts-Deals anzeigen")
                    print("16. 📊 Charts-Statistiken")
                    print("17. 🤖 Charts-Automation")
                
                # Elasticsearch (18-22)
                if es_available:
                    print("\n🔍 ELASTICSEARCH")
                    print("18. 📤 ES Daten exportieren")
                    print("19. 📊 Kibana Dashboard")
                    print("20. 🔬 ES Analytics")
                    print("21. ⚙️ ES Konfiguration")
                    print("22. 🔄 ES Synchronisierung")
                
                # System-Tools (23-28)
                print("\n🛠️ SYSTEM-TOOLS")
                print("23. 🔧 System-Tools")
                print("24. 🔧 Process Management")
                print("25. 📦 Batch Processing")
                print("26. 🧹 Datenbank-Wartung")
                print("27. 💾 Backup erstellen")
                print("28. ⚙️ Konfiguration bearbeiten")
                
                print("\n0.  👋 Beenden")
                print("=" * 60)
                
                # Eingabe
                choice = safe_input("Wählen Sie eine Option (0-28): ")
                
                # Menu-Handler (bestehend, erweitert)
                if choice == "0":
                    print("\n👋 Auf Wiedersehen!")
                    print("🧹 Enhanced Cleanup wird ausgeführt...")
                    enhanced_cleanup()
                    break
                
                # Basis-Funktionen (1-6)
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
                
                # Automation (7-8)
                elif choice == "7":
                    menu_toggle_scheduler(tracker)
                elif choice == "8":
                    menu_update_names_all_apps(tracker)  # NEU!
                
                # Management (9-12)
                elif choice == "9":
                    menu_manage_apps(tracker)
                elif choice == "10":
                    menu_remove_apps(tracker)
                elif choice == "11":
                    menu_csv_export(tracker)
                elif choice == "12":
                    menu_detailed_statistics(tracker)
                
                # Charts-Funktionen (13-17)
                elif choice == "13":
                    if charts_enabled:
                        menu_show_charts(charts_manager, tracker)
                    else:
                        print("❌ Charts Manager nicht verfügbar")
                elif choice == "14":
                    if charts_enabled:
                        menu_update_charts(charts_manager, tracker)  # VERBESSERT!
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
                
                # Elasticsearch-Funktionen (18-22)
                elif choice == "18":
                    if es_available:
                        menu_elasticsearch_export(es_manager, tracker)
                    else:
                        print("❌ Elasticsearch-Manager nicht verfügbar")
                elif choice == "19":
                    if es_available:
                        menu_elasticsearch_dashboard(es_manager)
                    else:
                        print("❌ Elasticsearch-Manager nicht verfügbar")
                elif choice == "20":
                    if es_available:
                        menu_elasticsearch_analytics(es_manager)
                    else:
                        print("❌ Elasticsearch-Manager nicht verfügbar")
                elif choice == "21":
                    if es_available:
                        menu_elasticsearch_config(es_manager)
                    else:
                        print("❌ Elasticsearch-Manager nicht verfügbar")
                elif choice == "22":
                    if es_available:
                        menu_elasticsearch_sync(es_manager, tracker)
                    else:
                        print("❌ Elasticsearch-Manager nicht verfügbar")
                
                # System-Tools (23-28)
                elif choice == "23":
                    menu_system_tools(tracker)
                elif choice == "24":
                    menu_process_management()
                elif choice == "25":
                    menu_batch_processing(tracker)
                elif choice == "26":
                    menu_database_maintenance(tracker)
                elif choice == "27":
                    menu_create_backup(tracker)
                elif choice == "28":
                    menu_edit_configuration()
                
                else:
                    print("❌ Ungültige Auswahl. Bitte wählen Sie eine Option zwischen 0-28.")
                
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