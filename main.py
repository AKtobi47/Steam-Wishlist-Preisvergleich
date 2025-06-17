#!/usr/bin/env python3
"""
Enhanced Steam Price Tracker v2.0 - Main Application mit automatischem Process Cleanup
VOLLSTÄNDIG INTEGRIERT: Alle ursprünglichen Features + Enhanced Process Management
Alle Subprozesse werden automatisch beendet wenn das Hauptprogramm geschlossen wird
"""

import sys
import time
import atexit
import signal
from datetime import datetime
from pathlib import Path
import logging

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =====================================================================
# ENHANCED PROCESS CLEANUP SYSTEM
# =====================================================================

def setup_automatic_cleanup(price_tracker):
    """
    Richtet automatisches Cleanup für alle Background-Prozesse ein
    
    Args:
        price_tracker: SteamPriceTracker Instanz
    """
    def cleanup_on_exit():
        """Wird beim Beenden des Hauptprogramms ausgeführt"""
        print("\n🧹 AUTOMATISCHES CLEANUP BEIM BEENDEN")
        print("=" * 45)
        
        try:
            # Background Scheduler stoppen
            print("⏹️ Stoppe Price Tracker Background-Scheduler...")
            if hasattr(price_tracker, 'stop_background_scheduler'):
                price_tracker.stop_background_scheduler()
            
            # Charts Scheduler stoppen
            if hasattr(price_tracker, 'charts_enabled') and price_tracker.charts_enabled:
                print("⏹️ Stoppe Charts Background-Scheduler...")
                if hasattr(price_tracker, 'disable_charts_tracking'):
                    price_tracker.disable_charts_tracking()
            
            # Enhanced Universal Scheduler stoppen
            if hasattr(price_tracker, 'price_scheduler'):
                print("⏹️ Stoppe Enhanced Universal Scheduler...")
                price_tracker.price_scheduler.cleanup_all_processes()
            
            # Charts Scheduler stoppen
            if hasattr(price_tracker, 'charts_scheduler') and price_tracker.charts_scheduler:
                print("⏹️ Stoppe Charts Universal Scheduler...")
                price_tracker.charts_scheduler.cleanup_all_processes()
            
            print("✅ Alle Background-Prozesse gestoppt")
            print("💾 Datenbankverbindungen werden geschlossen...")
            
            # Datenbank sicher schließen
            if hasattr(price_tracker, 'db_manager'):
                price_tracker.db_manager.close()
            
            print("✅ Enhanced Cleanup abgeschlossen")
            
        except Exception as e:
            print(f"⚠️ Fehler beim Cleanup: {e}")
    
    # Cleanup-Handler registrieren
    atexit.register(cleanup_on_exit)
    
    # Signal-Handler für Ctrl+C etc.
    def signal_handler(signum, frame):
        print(f"\n⚠️ Signal {signum} empfangen - führe Cleanup aus...")
        cleanup_on_exit()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("✅ Automatisches Process Cleanup eingerichtet")

# =====================================================================
# ENHANCED PROCESS MANAGEMENT FUNCTIONS
# =====================================================================

def get_enhanced_process_status():
    """Liefert Status aller Enhanced Prozesse"""
    try:
        from background_scheduler import _global_process_manager
        return _global_process_manager.get_process_status()
    except Exception as e:
        logger.warning(f"Process Status nicht verfügbar: {e}")
        return {'total_tracked': 0, 'running_processes': 0, 'dead_processes': 0, 'processes': {}}

def start_process_management_terminal():
    """Startet Process Management Terminal"""
    try:
        from background_scheduler import create_process_management_terminal
        if create_process_management_terminal():
            print("✅ Process Management Terminal gestartet")
            print("💡 Neues Terminal-Fenster sollte sich öffnen")
        else:
            print("❌ Fehler beim Starten des Management Terminals")
    except Exception as e:
        print(f"❌ Process Management Terminal nicht verfügbar: {e}")

def get_universal_scheduler_status(price_tracker):
    """Liefert Status des Universal Scheduler Systems"""
    try:
        status = {
            'total_active_schedulers': 0,
            'price_scheduler_status': None,
            'charts_scheduler_status': None
        }
        
        # Price Scheduler Status
        if hasattr(price_tracker, 'price_scheduler'):
            price_status = price_tracker.price_scheduler.get_scheduler_status()
            status['price_scheduler_status'] = price_status
            status['total_active_schedulers'] += price_status.get('total_running', 0)
        
        # Charts Scheduler Status
        if hasattr(price_tracker, 'charts_scheduler') and price_tracker.charts_scheduler:
            charts_status = price_tracker.charts_scheduler.get_scheduler_status()
            status['charts_scheduler_status'] = charts_status
            status['total_active_schedulers'] += charts_status.get('total_running', 0)
        
        return status
    except Exception as e:
        logger.warning(f"Scheduler Status nicht verfügbar: {e}")
        return {'total_active_schedulers': 0}

def show_universal_scheduler_status_enhanced(price_tracker):
    """Zeigt Enhanced Universal Scheduler Status"""
    try:
        status = get_universal_scheduler_status(price_tracker)
        
        print(f"\n🚀 ENHANCED UNIVERSAL BACKGROUND SCHEDULER:")
        print(f"   📊 Aktive Scheduler: {status.get('total_active_schedulers', 0)}")
        
        # Price Tracker Scheduler
        price_status = status.get('price_scheduler_status')
        if price_status and 'schedulers' in price_status:
            print(f"   💰 Price Tracker:")
            for scheduler_name, scheduler_info in price_status['schedulers'].items():
                running = "✅" if scheduler_info.get('running') else "❌"
                interval = scheduler_info.get('interval_minutes', 0)
                if interval >= 60:
                    interval_str = f"{interval // 60}h"
                else:
                    interval_str = f"{interval}min"
                print(f"      • {scheduler_name}: {running} (alle {interval_str})")
        
        # Charts Scheduler (falls verfügbar)
        charts_status = status.get('charts_scheduler_status')
        if charts_status and 'schedulers' in charts_status:
            print(f"   📊 Charts:")
            for scheduler_name, scheduler_info in charts_status['schedulers'].items():
                running = "✅" if scheduler_info.get('running') else "❌"
                interval = scheduler_info.get('interval_minutes', 0)
                if interval >= 60:
                    interval_str = f"{interval // 60}h"
                else:
                    interval_str = f"{interval}min"
                print(f"      • {scheduler_name}: {running} (alle {interval_str})")
        
    except Exception as e:
        print(f"⚠️ Enhanced Background Scheduler Status nicht verfügbar: {e}")

def show_enhanced_charts_statistics(price_tracker):
    """Zeigt Enhanced Charts-Statistiken"""
    try:
        if not hasattr(price_tracker, 'charts_enabled') or not price_tracker.charts_enabled:
            return
        
        if hasattr(price_tracker, 'charts_manager') and price_tracker.charts_manager:
            charts_stats = price_tracker.charts_manager.get_charts_statistics()
            
            if charts_stats and charts_stats.get('total_tracked_charts', 0) > 0:
                print(f"\n📊 ENHANCED CHARTS-STATISTIKEN:")
                print(f"🎯 Getrackte Charts: {charts_stats['total_tracked_charts']}")
                print(f"📈 Charts-Snapshots: {charts_stats.get('total_chart_snapshots', 0):,}")
                print(f"🎮 Charts-Spiele: {charts_stats.get('total_chart_games', 0)}")
                
                # Verteilung nach Chart-Typ
                if 'chart_type_distribution' in charts_stats:
                    active_by_chart = {k: v for k, v in charts_stats['chart_type_distribution'].items() if v > 0}
                    print(f"📈 Verteilung: ", end="")
                    chart_info = []
                    for chart_type, count in active_by_chart.items():
                        chart_info.append(f"{chart_type}: {count}")
                    print(" | ".join(chart_info))
            else:
                print(f"\n📊 CHARTS-STATUS:")
                print(f"🎯 Charts verfügbar aber noch keine Daten")
                print(f"💡 Führe 'Charts sofort aktualisieren' aus um zu starten")
        else:
            print("\n📊 Charts-Statistiken nicht verfügbar")
            
    except Exception as e:
        print(f"⚠️ Fehler beim Laden der Charts-Statistiken: {e}")

# =====================================================================
# ENHANCED MAIN APPLICATION
# =====================================================================

def main():
    print("🚀 ENHANCED STEAM PRICE TRACKER v2.0")
    print("=" * 55)
    print("Vollständiges Preis-Tracking mit automatischem Process Cleanup")
    print("Alle Background-Tasks werden beim Beenden automatisch gestoppt")
    print()
    
    # Price Tracker erstellen
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        
        # API Key laden
        api_key = load_api_key_from_env()
        if not api_key:
            print("⚠️ Kein Steam API Key in .env gefunden")
            print("💡 Einige Features (Charts, Namen-Updates) sind nicht verfügbar")
            api_key = None
        
        # Enhanced Price Tracker erstellen
        price_tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        charts_enabled = price_tracker.charts_enabled
        
        print(f"✅ Enhanced Price Tracker initialisiert")
        if charts_enabled:
            print(f"📊 Charts-Integration: VERFÜGBAR")
        else:
            print(f"📊 Charts-Integration: NICHT VERFÜGBAR (kein API Key)")
        
        # ENHANCED: Automatisches Cleanup einrichten
        setup_automatic_cleanup(price_tracker)
        
    except ImportError as e:
        print(f"❌ Import-Fehler: {e}")
        print("💡 Führe zuerst 'python setup.py install' aus")
        return
    except Exception as e:
        print(f"❌ Initialisierung fehlgeschlagen: {e}")
        return
    
    # Hauptschleife
    while True:
        try:
            # Enhanced Statistiken anzeigen
            try:
                stats = price_tracker.get_statistics()
                
                # Standard Statistiken
                print(f"\n📊 AKTUELLER STATUS:")
                print(f"📚 Getrackte Apps: {stats['tracked_apps']}")
                total_snapshots = stats.get('total_snapshots', 0)
                print(f"📈 Gesamt Preis-Snapshots: {total_snapshots:,}")
                print(f"🏪 Stores: {', '.join(stats['stores_tracked'])}")
                
                # Charts-Statistiken
                if charts_enabled:
                    show_enhanced_charts_statistics(price_tracker)
                
                # Enhanced Universal Background Scheduler Status
                show_universal_scheduler_status_enhanced(price_tracker)
                
                newest_snapshot = stats.get('newest_snapshot')
                if newest_snapshot:
                    print(f"🕐 Letzte Preisabfrage: {newest_snapshot[:19]}")
                
            except Exception as e:
                print(f"⚠️ Fehler beim Laden der Statistiken: {e}")
                print("\n📊 AKTUELLER STATUS:")
                print("📚 Getrackte Apps: ❓")
                print("📈 Gesamt Preis-Snapshots: ❓")
            
            # ENHANCED MENÜ-OPTIONEN
            print(f"\n🎯 WAS MÖCHTEN SIE TUN?")
            print("=" * 30)
            
            # Standard-Optionen
            print("📱 APP-VERWALTUNG:")
            print("1. App manuell zum Tracking hinzufügen")
            print("2. Steam Wishlist importieren")
            print("3. Aktuelle Preise anzeigen")
            print("4. Beste Deals anzeigen")
            print("5. Preisverlauf anzeigen")
            
            print("\n🔄 PREISE & UPDATES:")
            print("6. Preise manuell aktualisieren")
            print("7. Background-Tracking verwalten")
            print("8. Getrackte Apps verwalten")
            print("9. Apps entfernen")
            
            print("\n📄 EXPORT & DATEN:")
            print("10. CSV-Export erstellen")
            print("11. Detaillierte Statistiken")
            
            # Namen-Update Optionen
            print("\n🔤 NAMEN-UPDATES:")
            print("12. App-Namen von Steam aktualisieren")
            print("13. Apps mit generischen Namen anzeigen")
            
            # ENHANCED: Process Management
            print("\n🔧 ENHANCED PROCESS MANAGEMENT:")
            print("14. Process Management Terminal starten")
            print("15. Enhanced Process Status anzeigen")
            
            # Charts-Optionen (falls verfügbar)
            if charts_enabled:
                print("\n📊 CHARTS & ERWEITERTE FEATURES:")
                print("16. Charts sofort aktualisieren")
                print("17. Charts-Preise aktualisieren")
                print("18. Charts-Spiele anzeigen")
                print("19. Charts-Trends anzeigen")
                print("20. Charts-Cleanup ausführen")
                print("21. Charts-Management")
                print("22. Charts-Background-Tracking")
                print("23. Enhanced Vollautomatik einrichten")
                print("\n24. Enhanced Steam Price Tracker beenden")
            else:
                print("\n16. Enhanced Steam Price Tracker beenden")
            
            # Eingabe
            max_choice = 24 if charts_enabled else 16
            choice = input(f"\nWählen Sie eine Option (1-{max_choice}): ").strip()
            
            # Standard-Funktionen (1-13)
            if choice == "1":
                # App manuell hinzufügen
                print("\n➕ APP ZUM TRACKING HINZUFÜGEN")
                print("=" * 35)
                
                steam_app_id = input("Steam App ID: ").strip()
                if not steam_app_id:
                    print("❌ Ungültige App ID")
                    continue
                
                print(f"🔄 Füge App {steam_app_id} hinzu...")
                success = price_tracker.add_app_to_tracking(steam_app_id)
                
                if success:
                    print("✅ App erfolgreich hinzugefügt")
                    
                    # Namen von Steam aktualisieren (falls API Key verfügbar)
                    if api_key:
                        update_name = input("Namen von Steam API aktualisieren? (j/n): ").lower().strip()
                        if update_name in ['j', 'ja', 'y', 'yes']:
                            result = price_tracker.update_app_names_from_steam([steam_app_id], api_key)
                            if result.get('updated', 0) > 0:
                                print("✅ Name von Steam aktualisiert")
                else:
                    print("❌ Fehler beim Hinzufügen der App")
            
            elif choice == "2":
                # Steam Wishlist importieren
                print("\n📥 STEAM WISHLIST IMPORTIEREN")
                print("=" * 35)
                
                if not api_key:
                    print("❌ Steam API Key erforderlich für Wishlist-Import")
                    continue
                
                steam_id = input("Steam ID oder Custom URL: ").strip()
                if not steam_id:
                    print("❌ Ungültige Steam ID")
                    continue
                
                print("🔄 Importiere Wishlist...")
                result = price_tracker.import_steam_wishlist(steam_id, api_key, update_names=True)
                
                if result['success']:
                    print(f"✅ Wishlist-Import erfolgreich:")
                    print(f"   ➕ {result['imported']} neue Apps hinzugefügt")
                    print(f"   ⏭️ {result['skipped_existing']} bereits vorhanden")
                    print(f"   🔄 {result.get('names_updated', 0)} Namen aktualisiert")
                else:
                    print(f"❌ Wishlist-Import fehlgeschlagen: {result.get('error')}")
            
            elif choice == "3":
                # Aktuelle Preise anzeigen
                print("\n💰 AKTUELLE PREISE")
                print("=" * 20)
                
                steam_app_id = input("Steam App ID: ").strip()
                if steam_app_id:
                    price_tracker.print_price_summary(steam_app_id)
                else:
                    print("❌ Ungültige App ID")
            
            elif choice == "4":
                # Beste Deals anzeigen
                print("\n🏆 BESTE AKTUELLE DEALS")
                print("=" * 25)
                
                deals = price_tracker.get_current_best_deals(limit=15)
                
                if deals:
                    for i, deal in enumerate(deals, 1):
                        print(f"{i:2d}. {deal['game_title'][:40]:<40}")
                        print(f"    💰 €{deal['best_price']:.2f} (-{deal['discount_percent']}%) bei {deal['best_store']}")
                        print(f"    🆔 App ID: {deal['steam_app_id']}")
                        print()
                else:
                    print("❌ Keine Deals gefunden")
            
            elif choice == "5":
                # Preisverlauf anzeigen
                print("\n📈 PREISVERLAUF")
                print("=" * 15)
                
                steam_app_id = input("Steam App ID: ").strip()
                if not steam_app_id:
                    print("❌ Ungültige App ID")
                    continue
                
                days = input("Tage zurück (Standard: 30): ").strip()
                try:
                    days = int(days) if days else 30
                except ValueError:
                    days = 30
                
                history = price_tracker.get_price_history(steam_app_id, days)
                
                if history:
                    print(f"\n📊 Preisverlauf für {history[0]['game_title']} (letzte {len(history)} Einträge):")
                    print()
                    
                    for snapshot in history[:10]:
                        date = snapshot['timestamp'][:10]
                        print(f"📅 {date}:")
                        
                        stores = ['steam', 'greenmangaming', 'gog', 'humblestore', 'fanatical', 'gamesplanet']
                        for store in stores:
                            price_col = f"{store}_price"
                            available_col = f"{store}_available"
                            discount_col = f"{store}_discount_percent"
                            
                            if snapshot.get(available_col) and snapshot.get(price_col) is not None:
                                price = snapshot[price_col]
                                discount = snapshot.get(discount_col, 0)
                                discount_text = f" (-{discount}%)" if discount > 0 else ""
                                print(f"   💰 {store.upper():12}: €{price:.2f}{discount_text}")
                        print()
                else:
                    print("❌ Kein Preisverlauf gefunden")
            
            elif choice == "6":
                # Preise manuell aktualisieren
                print("\n🔄 PREISE MANUELL AKTUALISIEREN")
                print("=" * 35)
                
                print("1. Alle Apps aktualisieren")
                print("2. Nur veraltete Apps (älter als 6h)")
                print("3. Spezifische App")
                
                update_choice = input("Auswahl (1-3): ").strip()
                
                if update_choice == "1":
                    # Alle Apps
                    print("🔄 Aktualisiere alle Apps...")
                    result = price_tracker.process_all_apps_optimized()
                    print(f"✅ {result['total_successful']}/{result['total_apps']} Apps aktualisiert")
                    print(f"⏱️ Dauer: {result['total_duration']:.1f}s")
                    
                elif update_choice == "2":
                    # Nur veraltete Apps
                    print("🔄 Aktualisiere veraltete Apps...")
                    result = price_tracker.process_all_pending_apps_optimized(hours_threshold=6)
                    print(f"✅ {result['total_successful']}/{result['total_apps']} Apps aktualisiert")
                    print(f"⏱️ Dauer: {result['total_duration']:.1f}s")
                    
                elif update_choice == "3":
                    # Spezifische App
                    steam_app_id = input("Steam App ID: ").strip()
                    if steam_app_id:
                        print(f"🔄 Aktualisiere App {steam_app_id}...")
                        if price_tracker.track_single_app_price(steam_app_id):
                            print("✅ App erfolgreich aktualisiert")
                        else:
                            print("❌ Fehler beim Aktualisieren")
                    else:
                        print("❌ Ungültige App ID")
            
            elif choice == "7":
                # Background-Tracking verwalten
                print("\n🚀 ENHANCED BACKGROUND-TRACKING VERWALTEN")
                print("=" * 50)
                
                status = get_universal_scheduler_status(price_tracker)
                total_active = status.get('total_active_schedulers', 0)
                
                if total_active > 0:
                    print(f"🔄 Enhanced Background-Tracking läuft: {total_active} aktive Scheduler")
                    show_universal_scheduler_status_enhanced(price_tracker)
                    
                    stop = input("\nAlle Enhanced Background-Scheduler stoppen? (j/n): ").lower().strip()
                    if stop in ['j', 'ja', 'y', 'yes']:
                        if price_tracker.stop_background_scheduler():
                            print("⏹️ Price Tracker Background-Scheduler gestoppt")
                        
                        if charts_enabled and price_tracker.disable_charts_tracking():
                            print("⏹️ Charts Background-Scheduler gestoppt")
                else:
                    print("⏸️ Enhanced Background-Tracking ist inaktiv")
                    start = input("Enhanced Background-Tracking starten? (j/n): ").lower().strip()
                    
                    if start in ['j', 'ja', 'y', 'yes']:
                        # Enhanced Konfiguration
                        price_hours = input("Preis-Update Intervall in Stunden (Standard: 6): ").strip()
                        name_minutes = input("Namen-Update Intervall in Minuten (Standard: 30): ").strip()
                        
                        try:
                            price_hours = int(price_hours) if price_hours else 6
                            name_minutes = int(name_minutes) if name_minutes else 30
                        except ValueError:
                            price_hours, name_minutes = 6, 30
                        
                        if price_tracker.start_background_scheduler(
                            price_interval_hours=price_hours,
                            name_interval_minutes=name_minutes
                        ):
                            print(f"✅ Enhanced Background-Tracking gestartet!")
                            print(f"   💰 Preise: alle {price_hours}h")
                            print(f"   🔤 Namen: alle {name_minutes}min")
                            print("   💡 Läuft in separaten Terminals mit automatischem Cleanup!")
            
            elif choice == "8":
                # Getrackte Apps verwalten
                print("\n📋 GETRACKTE APPS VERWALTEN")
                print("=" * 30)
                
                apps = price_tracker.get_all_tracked_apps()
                
                if apps:
                    print(f"\n{len(apps)} getrackte Apps:")
                    for i, app in enumerate(apps[:20], 1):  # Erste 20 anzeigen
                        name = app.get('name', 'Unbekannt')[:40]
                        print(f"{i:2d}. {app['steam_app_id']:10} - {name}")
                    
                    if len(apps) > 20:
                        print(f"... und {len(apps) - 20} weitere")
                else:
                    print("❌ Keine Apps getrackt")
            
            elif choice == "9":
                # Apps entfernen
                print("\n🗑️ APPS ENTFERNEN")
                print("=" * 18)
                
                steam_app_id = input("Steam App ID zum Entfernen: ").strip()
                if not steam_app_id:
                    print("❌ Ungültige App ID")
                    continue
                
                confirm = input(f"App {steam_app_id} wirklich entfernen? (j/n): ").lower().strip()
                if confirm in ['j', 'ja', 'y', 'yes']:
                    if price_tracker.remove_app_from_tracking(steam_app_id):
                        print("✅ App erfolgreich entfernt")
                    else:
                        print("❌ Fehler beim Entfernen")
            
            elif choice == "10":
                # CSV-Export
                print("\n📄 CSV-EXPORT ERSTELLEN")
                print("=" * 25)
                
                steam_app_id = input("Steam App ID (oder Enter für alle): ").strip()
                
                if steam_app_id:
                    csv_file = price_tracker.export_price_history_csv(steam_app_id)
                    if csv_file:
                        print(f"✅ CSV-Export erstellt: {csv_file}")
                    else:
                        print("❌ Fehler beim Export")
                else:
                    print("🔄 Exportiere alle Apps...")
                    exports_created = 0
                    apps = price_tracker.get_all_tracked_apps()
                    
                    for app in apps[:10]:  # Erste 10 Apps
                        csv_file = price_tracker.export_price_history_csv(app['steam_app_id'])
                        if csv_file:
                            exports_created += 1
                    
                    print(f"✅ {exports_created} CSV-Exports erstellt")
            
            elif choice == "11":
                # Detaillierte Statistiken
                print("\n📊 DETAILLIERTE STATISTIKEN")
                print("=" * 30)
                
                stats = price_tracker.get_detailed_statistics()
                
                print(f"📚 Getrackte Apps: {stats['tracked_apps']}")
                print(f"📈 Preis-Snapshots: {stats['total_snapshots']:,}")
                print(f"🏪 Aktive Stores: {len(stats['stores_tracked'])}")
                print(f"🕐 Zeitraum: {stats.get('date_range', 'N/A')}")
                
                if 'app_statistics' in stats:
                    app_stats = stats['app_statistics']
                    print(f"\n📊 APP-VERTEILUNG:")
                    print(f"   🔄 Kürzlich aktualisiert: {app_stats.get('recently_updated', 0)}")
                    print(f"   ⏰ Veraltet (>6h): {app_stats.get('outdated', 0)}")
                    print(f"   ❌ Noch nie aktualisiert: {app_stats.get('never_updated', 0)}")
            
            elif choice == "12":
                # App-Namen von Steam aktualisieren
                print("\n🔤 APP-NAMEN VON STEAM AKTUALISIEREN")
                print("=" * 40)
                
                if not api_key:
                    print("❌ Steam API Key erforderlich")
                    continue
                
                print("1. Alle Apps")
                print("2. Nur Apps mit generischen Namen")
                print("3. Spezifische App")
                
                name_choice = input("Auswahl (1-3): ").strip()
                
                if name_choice == "1":
                    # Alle Apps
                    apps = price_tracker.get_all_tracked_apps()
                    app_ids = [app['steam_app_id'] for app in apps]
                    
                    print(f"🔄 Aktualisiere Namen für {len(app_ids)} Apps...")
                    result = price_tracker.update_app_names_from_steam(app_ids, api_key)
                    print(f"✅ {result['updated']}/{result['total']} Namen aktualisiert")
                    
                elif name_choice == "2":
                    # Nur generische Namen
                    generic_apps = price_tracker.get_apps_with_generic_names()
                    app_ids = [app['steam_app_id'] for app in generic_apps]
                    
                    if app_ids:
                        print(f"🔄 Aktualisiere {len(app_ids)} Apps mit generischen Namen...")
                        result = price_tracker.update_app_names_from_steam(app_ids, api_key)
                        print(f"✅ {result['updated']}/{result['total']} Namen aktualisiert")
                    else:
                        print("✅ Keine Apps mit generischen Namen gefunden")
                        
                elif name_choice == "3":
                    # Spezifische App
                    steam_app_id = input("Steam App ID: ").strip()
                    if steam_app_id:
                        result = price_tracker.update_app_names_from_steam([steam_app_id], api_key)
                        if result['updated'] > 0:
                            print("✅ Name aktualisiert")
                        else:
                            print("❌ Name konnte nicht aktualisiert werden")
            
            elif choice == "13":
                # Apps mit generischen Namen anzeigen
                print("\n🔤 APPS MIT GENERISCHEN NAMEN")
                print("=" * 35)
                
                generic_apps = price_tracker.get_apps_with_generic_names()
                
                if generic_apps:
                    print(f"🔍 {len(generic_apps)} Apps mit generischen Namen gefunden:")
                    for app in generic_apps[:15]:
                        print(f"   🆔 {app['steam_app_id']} - {app['name']}")
                    
                    if len(generic_apps) > 15:
                        print(f"   ... und {len(generic_apps) - 15} weitere")
                        
                    if api_key:
                        update_all = input("\nAlle Namen jetzt von Steam aktualisieren? (j/n): ").lower().strip()
                        if update_all in ['j', 'ja', 'y', 'yes']:
                            app_ids = [app['steam_app_id'] for app in generic_apps]
                            result = price_tracker.update_app_names_from_steam(app_ids, api_key)
                            print(f"✅ {result['updated']}/{result['total']} Namen aktualisiert")
                else:
                    print("✅ Keine Apps mit generischen Namen gefunden")
            
            # ========================
            # ENHANCED: PROCESS MANAGEMENT OPTIONEN (14-15)
            # ========================
            
            elif choice == "14":
                # ENHANCED: Process Management Terminal starten
                print("\n🔧 PROCESS MANAGEMENT TERMINAL STARTEN")
                print("=" * 45)
                
                print("Das Enhanced Process Management Terminal bietet:")
                print("• Übersicht aller aktiven Background-Prozesse")
                print("• Kontrolle und Beendigung einzelner Prozesse")
                print("• System-Ressourcen Monitoring")
                print("• Zentrale Kontrolle aller Enhanced Scheduler")
                print("• Parent-Process-Monitoring Status")
                print()
                
                start_mgmt = input("Enhanced Process Management Terminal starten? (j/n): ").lower().strip()
                if start_mgmt in ['j', 'ja', 'y', 'yes']:
                    start_process_management_terminal()
            
            elif choice == "15":
                # ENHANCED: Process Status anzeigen
                print("\n📊 ENHANCED PROCESS STATUS")
                print("=" * 35)
                
                try:
                    process_status = get_enhanced_process_status()
                    
                    print(f"🔧 Enhanced Process Manager Status:")
                    print(f"   📊 Getrackte Prozesse: {process_status['total_tracked']}")
                    print(f"   ✅ Laufende Prozesse: {process_status['running_processes']}")
                    print(f"   💀 Tote Prozesse: {process_status['dead_processes']}")
                    
                    if process_status['processes']:
                        print(f"\n📋 AKTIVE ENHANCED PROZESSE:")
                        for scheduler_id, proc_info in process_status['processes'].items():
                            if proc_info['is_running']:
                                print(f"   ✅ {scheduler_id}")
                                print(f"      PID: {proc_info['pid']}")
                                print(f"      Gestartet: {proc_info['started_at'][:19]}")
                                print(f"      Parent-Monitoring: {'✅' if proc_info.get('parent_monitoring') else '❌'}")
                            else:
                                print(f"   💀 {scheduler_id} (tot)")
                    else:
                        print("\n💡 Keine aktiven Enhanced Prozesse")
                        
                except Exception as e:
                    print(f"❌ Enhanced Process Status nicht verfügbar: {e}")
            
            # ========================
            # CHARTS-OPTIONEN (16-23) - nur wenn Charts verfügbar
            # ========================
            
            elif charts_enabled and choice == "16":
                # Charts sofort aktualisieren
                print("\n📊 CHARTS SOFORT AKTUALISIEREN")
                print("=" * 35)
                
                if hasattr(price_tracker, 'charts_manager') and price_tracker.charts_manager:
                    print("🔄 Aktualisiere Steam Charts...")
                    result = price_tracker.charts_manager.update_all_charts()
                    
                    if result.get('success'):
                        print(f"✅ Charts aktualisiert:")
                        print(f"   📊 {result.get('updated_charts', 0)} Charts verarbeitet")
                        print(f"   🎮 {result.get('new_games', 0)} neue Spiele gefunden")
                        print(f"   ⏱️ Dauer: {result.get('duration', 0):.1f}s")
                    else:
                        print(f"❌ Charts-Update fehlgeschlagen: {result.get('error')}")
                else:
                    print("❌ Charts-Manager nicht verfügbar")
            
            elif charts_enabled and choice == "17":
                # Charts-Preise aktualisieren
                print("\n💰 CHARTS-PREISE AKTUALISIEREN")
                print("=" * 35)
                
                if hasattr(price_tracker, 'charts_manager') and price_tracker.charts_manager:
                    print("🔄 Aktualisiere Preise für Charts-Spiele...")
                    result = price_tracker.charts_manager.update_charts_prices()
                    
                    if result.get('success'):
                        print(f"✅ Charts-Preise aktualisiert:")
                        print(f"   💰 {result.get('updated_prices', 0)} Spiele-Preise aktualisiert")
                        print(f"   ⏱️ Dauer: {result.get('duration', 0):.1f}s")
                    else:
                        print(f"❌ Charts-Preis-Update fehlgeschlagen: {result.get('error')}")
                else:
                    print("❌ Charts-Manager nicht verfügbar")
            
            elif charts_enabled and choice == "18":
                # Charts-Spiele anzeigen
                print("\n🎮 CHARTS-SPIELE ANZEIGEN")
                print("=" * 28)
                
                if hasattr(price_tracker, 'charts_manager') and price_tracker.charts_manager:
                    games = price_tracker.charts_manager.get_chart_games_summary()
                    
                    if games:
                        print(f"📊 {len(games)} Charts-Spiele:")
                        for i, game in enumerate(games[:15], 1):
                            chart_types = game.get('chart_types', 'N/A')
                            rank = game.get('current_rank', 'N/A')
                            print(f"{i:2d}. {game['name'][:35]:<35} | Charts: {chart_types} | Rang: {rank}")
                        
                        if len(games) > 15:
                            print(f"... und {len(games) - 15} weitere")
                    else:
                        print("❌ Keine Charts-Spiele gefunden")
                else:
                    print("❌ Charts-Manager nicht verfügbar")
            
            elif charts_enabled and choice == "19":
                # Charts-Trends anzeigen
                print("\n📈 CHARTS-TRENDS ANZEIGEN")
                print("=" * 28)
                
                if hasattr(price_tracker, 'charts_manager') and price_tracker.charts_manager:
                    trends = price_tracker.charts_manager.get_trending_games()
                    
                    if trends:
                        print("🔥 Trending Steam Charts Games:")
                        for i, trend in enumerate(trends[:10], 1):
                            direction = "📈" if trend.get('rank_change', 0) > 0 else "📉" if trend.get('rank_change', 0) < 0 else "➡️"
                            print(f"{i:2d}. {direction} {trend['name'][:30]:<30} | Rang: #{trend.get('current_rank', 'N/A')}")
                    else:
                        print("❌ Keine Trend-Daten verfügbar")
                else:
                    print("❌ Charts-Manager nicht verfügbar")
            
            elif charts_enabled and choice == "20":
                # Charts-Cleanup
                print("\n🧹 CHARTS-CLEANUP AUSFÜHREN")
                print("=" * 32)
                
                if hasattr(price_tracker, 'charts_manager') and price_tracker.charts_manager:
                    print("🗑️ Bereinige alte Charts-Daten...")
                    
                    # Alte Charts-Spiele entfernen (>30 Tage)
                    removed = price_tracker.charts_manager.cleanup_old_chart_games(days_threshold=30)
                    
                    if removed > 0:
                        print(f"✅ {removed} alte Charts-Einträge entfernt")
                    else:
                        print("✅ Keine alten Einträge zum Entfernen")
                        
                    # Datenbank optimieren
                    print("🔧 Optimiere Datenbank...")
                    if hasattr(price_tracker.db_manager, 'vacuum_database'):
                        price_tracker.db_manager.vacuum_database()
                        print("✅ Datenbank optimiert")
                else:
                    print("❌ Charts-Manager nicht verfügbar")
            
            elif charts_enabled and choice == "21":
                # Charts-Management
                print("\n🔧 CHARTS-MANAGEMENT")
                print("=" * 25)
                
                print("1. Charts-Statistiken anzeigen")
                print("2. Spezifische Charts abrufen")
                print("3. Charts-Konfiguration")
                
                charts_choice = input("Auswahl (1-3): ").strip()
                
                if charts_choice == "1":
                    # Charts-Statistiken
                    show_enhanced_charts_statistics(price_tracker)
                    
                elif charts_choice == "2":
                    # Spezifische Charts abrufen
                    print("\nVerfügbare Chart-Typen:")
                    print("• topsellers")
                    print("• toprated") 
                    print("• trending")
                    print("• new")
                    print("• upcoming")
                    
                    chart_type = input("\nChart-Typ: ").strip().lower()
                    if chart_type:
                        if hasattr(price_tracker, 'charts_manager') and price_tracker.charts_manager:
                            result = price_tracker.charts_manager.fetch_specific_chart(chart_type)
                            if result.get('success'):
                                print(f"✅ {chart_type} Chart aktualisiert")
                            else:
                                print(f"❌ Fehler: {result.get('error')}")
                        else:
                            print("❌ Charts-Manager nicht verfügbar")
                    
                elif charts_choice == "3":
                    # Charts-Konfiguration
                    print("\nAktuelle Charts-Konfiguration:")
                    print("• Rate Limit: 1.0s zwischen Requests")
                    print("• Max Charts pro Update: 100")
                    print("• Cleanup-Intervall: 30 Tage")
            
            elif charts_enabled and choice == "22":
                # Charts-Background-Tracking
                print("\n📊 CHARTS-BACKGROUND-TRACKING")
                print("=" * 37)
                
                # Status prüfen
                charts_status = None
                if hasattr(price_tracker, 'charts_scheduler'):
                    charts_status = price_tracker.charts_scheduler.get_scheduler_status()
                
                if charts_status and charts_status.get('total_running', 0) > 0:
                    print("✅ Charts-Background-Tracking läuft")
                    print(f"   📊 Aktive Scheduler: {charts_status['total_running']}")
                    
                    for name, info in charts_status.get('schedulers', {}).items():
                        if info.get('running'):
                            interval = info.get('interval_minutes', 0)
                            interval_str = f"{interval // 60}h" if interval >= 60 else f"{interval}min"
                            print(f"   • {name}: alle {interval_str}")
                    
                    stop_charts = input("\nCharts-Background-Tracking stoppen? (j/n): ").lower().strip()
                    if stop_charts in ['j', 'ja', 'y', 'yes']:
                        if price_tracker.disable_charts_tracking():
                            print("⏹️ Charts-Background-Tracking gestoppt")
                else:
                    print("⏸️ Charts-Background-Tracking ist inaktiv")
                    start_charts = input("Charts-Background-Tracking starten? (j/n): ").lower().strip()
                    
                    if start_charts in ['j', 'ja', 'y', 'yes']:
                        update_hours = input("Charts-Update Intervall in Stunden (Standard: 6): ").strip()
                        price_hours = input("Charts-Preise Intervall in Stunden (Standard: 4): ").strip()
                        
                        try:
                            update_hours = int(update_hours) if update_hours else 6
                            price_hours = int(price_hours) if price_hours else 4
                        except ValueError:
                            update_hours, price_hours = 6, 4
                        
                        if price_tracker.enable_charts_tracking(
                            charts_interval_hours=update_hours,
                            charts_price_interval_hours=price_hours
                        ):
                            print("✅ Charts-Background-Tracking gestartet!")
                            print(f"   📊 Charts-Updates: alle {update_hours}h")
                            print(f"   💰 Charts-Preise: alle {price_hours}h")
            
            elif charts_enabled and choice == "23":
                # Enhanced Vollautomatik einrichten
                print("\n🚀 ENHANCED VOLLAUTOMATIK EINRICHTEN")
                print("=" * 45)
                
                print("Enhanced Vollautomatik umfasst:")
                print("• 💰 Automatische Preis-Updates für alle Apps")
                print("• 📊 Automatische Charts-Updates")
                print("• 💰 Automatische Charts-Preise Updates")
                print("• 🔤 Automatische Namen-Updates")
                print("• 🧹 Automatisches Charts-Cleanup")
                print("• 🔧 Automatisches Process-Cleanup beim Exit")
                print("• 👁️ Parent-Process-Monitoring in allen Terminals")
                print("• 💓 Sign of Life mit Status-Anzeigen")
                print("• ALLE Tasks laufen in separaten Enhanced Terminals!")
                print()
                
                confirm = input("Enhanced Vollautomatik einrichten? (j/n): ").lower().strip()
                if confirm in ['j', 'ja', 'y', 'yes']:
                    print("\n⚙️ ENHANCED KONFIGURATION:")
                    normal_hours = input("Intervall normale Apps (Stunden, Standard: 6): ").strip()
                    charts_hours = input("Intervall Charts-Updates (Stunden, Standard: 6): ").strip()
                    charts_price_hours = input("Intervall Charts-Preise (Stunden, Standard: 4): ").strip()
                    name_minutes = input("Intervall Namen-Updates (Minuten, Standard: 30): ").strip()
                    
                    try:
                        normal_hours = int(normal_hours) if normal_hours else 6
                        charts_hours = int(charts_hours) if charts_hours else 6
                        charts_price_hours = int(charts_price_hours) if charts_price_hours else 4
                        name_minutes = int(name_minutes) if name_minutes else 30
                    except ValueError:
                        normal_hours, charts_hours, charts_price_hours, name_minutes = 6, 6, 4, 30
                    
                    try:
                        from price_tracker import setup_full_automation
                        
                        if setup_full_automation(
                            price_tracker,
                            normal_interval=normal_hours,
                            charts_interval=charts_hours,
                            charts_price_interval=charts_price_hours,
                            name_interval=name_minutes
                        ):
                            print("\n✅ ENHANCED VOLLAUTOMATIK ERFOLGREICH EINGERICHTET!")
                            print("\n📋 AKTIVE ENHANCED AUTOMATION:")
                            print(f"   💰 Standard-Preise: alle {normal_hours}h")
                            print(f"   📊 Charts-Updates: alle {charts_hours}h")
                            print(f"   💰 Charts-Preise: alle {charts_price_hours}h")
                            print(f"   🔤 Namen-Updates: alle {name_minutes}min")
                            print(f"   🧹 Charts-Cleanup: alle 24h")
                            print("\n💡 ENHANCED FEATURES:")
                            print("   🔧 Automatisches Process-Cleanup aktiviert")
                            print("   👁️ Parent-Process-Monitoring in allen Terminals")
                            print("   💓 Sign of Life mit Status-Anzeigen")
                            print("   📊 Process Management Terminal verfügbar")
                        else:
                            print("❌ Fehler beim Einrichten der Enhanced Vollautomatik")
                            
                    except Exception as e:
                        print(f"❌ Fehler beim Einrichten: {e}")
            
            # Beenden
            elif (not charts_enabled and choice == "16") or (charts_enabled and choice == "24"):
                print("\n👋 ENHANCED STEAM PRICE TRACKER BEENDEN")
                print("=" * 45)
                
                # Enhanced Process Status anzeigen
                process_status = get_enhanced_process_status()
                total_active = process_status.get('running_processes', 0)
                
                if total_active > 0:
                    print(f"⏹️ Stoppe {total_active} aktive Enhanced Background-Prozesse...")
                    print("💡 Automatisches Cleanup wird beim Exit ausgeführt...")
                else:
                    print("ℹ️ Keine aktiven Enhanced Background-Prozesse")
                
                print("💾 Datenbankverbindungen werden automatisch geschlossen...")
                print("🧹 Enhanced Process-Cleanup wird ausgeführt...")
                print("✅ Enhanced Steam Price Tracker v2.0 wird beendet...")
                print("\n💡 Alle Subprozesse werden automatisch gestoppt!")
                print("👋 Auf Wiedersehen!")
                break
            
            else:
                print("❌ Ungültige Auswahl")
                
        except KeyboardInterrupt:
            print("\n⏹️ Abgebrochen durch Benutzer")
            print("🧹 Automatisches Enhanced Cleanup wird ausgeführt...")
            break
        except Exception as e:
            print(f"❌ Unerwarteter Fehler: {e}")
            logger.exception("Unerwarteter Fehler in Enhanced main()")

if __name__ == "__main__":
    main()