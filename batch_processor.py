#!/usr/bin/env python3
"""
Enhanced Batch Processor CLI - Erweiterte Verwaltung für Steam Price Tracker
Mit App-Namen Updates und erweiterten Wartungsfunktionen
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
import logging

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cmd_run_batch(args):
    """Führt optimiertes Batch-Update aus"""
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        
        api_key = load_api_key_from_env()
        tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        
        print("🚀 Starte optimiertes Batch-Update...")
        print(f"   ⏱️ Threshold: {args.hours}h")
        print(f"   📦 Max. Apps pro Batch: {getattr(args, 'batch_size', 50)}")
        
        if hasattr(tracker, 'process_all_pending_apps_optimized'):
            stats = tracker.process_all_pending_apps_optimized(args.hours)
            
            if stats.get('success'):
                print(f"✅ Batch-Update erfolgreich:")
                print(f"   📊 {stats['total_successful']}/{stats['total_apps']} Apps erfolgreich")
                print(f"   ⏱️ Dauer: {stats['total_duration']:.1f}s")
                print(f"   📦 {stats['total_batches']} Batches")
                print(f"   ⚡ {stats['apps_per_second']:.1f} Apps/s")
                
                if stats['total_failed'] > 0:
                    print(f"   ⚠️ {stats['total_failed']} Apps fehlgeschlagen")
            else:
                print(f"❌ Batch-Update fehlgeschlagen: {stats.get('error', 'Unbekannter Fehler')}")
        else:
            print("❌ Batch-Update-Funktion nicht verfügbar")
            
    except ImportError:
        print("❌ price_tracker Modul nicht gefunden")
        print("💡 Führe zuerst 'python setup.py install' aus")
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")

def cmd_run_specific(args):
    """Führt Update für spezifische Apps aus"""
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        
        api_key = load_api_key_from_env()
        tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        
        app_ids = [app_id.strip() for app_id in args.app_ids.split(',') if app_id.strip()]
        
        if not app_ids:
            print("❌ Keine gültigen App IDs angegeben")
            return
        
        print(f"🎯 Update für {len(app_ids)} spezifische Apps...")
        print(f"   📱 App IDs: {', '.join(app_ids)}")
        
        successful = 0
        failed = 0
        
        for app_id in app_ids:
            print(f"\n🔄 Aktualisiere App {app_id}...")
            
            try:
                success = tracker.update_price_for_app(app_id)
                if success:
                    print(f"   ✅ App {app_id} erfolgreich aktualisiert")
                    successful += 1
                else:
                    print(f"   ❌ App {app_id} Update fehlgeschlagen")
                    failed += 1
            except Exception as e:
                print(f"   ❌ App {app_id} Fehler: {e}")
                failed += 1
        
        print(f"\n📊 ERGEBNIS:")
        print(f"   ✅ Erfolgreich: {successful}")
        print(f"   ❌ Fehlgeschlagen: {failed}")
        print(f"   📈 Gesamt: {len(app_ids)}")
        
    except ImportError:
        print("❌ price_tracker Modul nicht gefunden")
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")

def cmd_show_pending(args):
    """Zeigt Apps die Updates benötigen"""
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        
        api_key = load_api_key_from_env()
        tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        
        print(f"📋 Apps die Updates benötigen (älter als {args.hours}h)")
        print("=" * 50)
        
        # Pending Apps abrufen
        if hasattr(tracker, 'get_apps_needing_update'):
            pending_apps = tracker.get_apps_needing_update(hours_threshold=args.hours)
            
            if pending_apps:
                print(f"⏰ {len(pending_apps)} Apps benötigen Updates:")
                print()
                
                for i, app in enumerate(pending_apps[:args.limit], 1):
                    name = app.get('name', 'Unbekannt')[:50]
                    app_id = app.get('steam_app_id', 'N/A')
                    last_update = app.get('last_price_update', 'Nie')
                    
                    print(f"{i:2d}. {name}")
                    print(f"    🆔 App ID: {app_id}")
                    print(f"    📅 Letztes Update: {last_update}")
                    print()
                    
                if len(pending_apps) > args.limit:
                    remaining = len(pending_apps) - args.limit
                    print(f"... und {remaining} weitere Apps")
            else:
                print("✅ Alle Apps sind aktuell")
        else:
            print("❌ Pending Apps Funktion nicht verfügbar")
            
    except ImportError:
        print("❌ price_tracker Modul nicht gefunden")
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")

def cmd_system_status(args):
    """Zeigt detaillierten System-Status"""
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        from database_manager import DatabaseManager
        
        print("📊 STEAM PRICE TRACKER - SYSTEM STATUS")
        print("=" * 50)
        
        # API Key Status
        try:
            api_key = load_api_key_from_env()
            if api_key:
                masked_key = api_key[:8] + "..." if len(api_key) > 8 else "***"
                print(f"🔑 Steam API Key: {masked_key}")
            else:
                print(f"🔑 Steam API Key: ❌ Nicht konfiguriert")
        except Exception:
            print(f"🔑 Steam API Key: ❌ Fehler beim Laden")
        
        # Price Tracker Status
        try:
            tracker = create_price_tracker(api_key=api_key, enable_charts=True)
            print(f"🚀 Price Tracker: ✅ Verfügbar")
            print(f"📊 Charts-Integration: {'✅ Verfügbar' if tracker.charts_enabled else '❌ Nicht verfügbar'}")
        except Exception as e:
            print(f"🚀 Price Tracker: ❌ Fehler: {e}")
        
        # Datenbank Status
        try:
            db = DatabaseManager()
            tracked_apps = db.get_tracked_apps()
            print(f"🗄️ Datenbank: ✅ Verfügbar")
            print(f"📱 Getrackte Apps: {len(tracked_apps) if tracked_apps else 0}")
            
            # Datenbank-Dateigröße
            db_file = Path("steam_price_tracker.db")
            if db_file.exists():
                size_mb = db_file.stat().st_size / 1024 / 1024
                print(f"💾 Datenbankgröße: {size_mb:.1f} MB")
        except Exception as e:
            print(f"🗄️ Datenbank: ❌ Fehler: {e}")
        
        # Scheduler Status
        try:
            if hasattr(tracker, 'get_enhanced_scheduler_status'):
                status = tracker.get_enhanced_scheduler_status()
                is_running = status.get('scheduler_running', False)
                print(f"⏰ Scheduler: {'✅ AKTIV' if is_running else '❌ INAKTIV'}")
                
                if is_running and status.get('next_run'):
                    print(f"⏰ Nächster Lauf: {status['next_run']}")
                    
                # Charts Scheduler
                charts_status = status.get('charts_scheduler_status', {})
                if charts_status:
                    active_charts = sum(1 for s in charts_status.values() if s.get('is_running'))
                    print(f"📊 Charts-Scheduler: {active_charts} aktiv")
        except Exception as e:
            print(f"⏰ Scheduler: ❌ Fehler: {e}")
        
        # Background Processes
        try:
            from background_scheduler import _global_process_manager
            if _global_process_manager:
                proc_status = _global_process_manager.get_process_status()
                print(f"🔄 Background-Prozesse: {proc_status['running_processes']} aktiv")
                print(f"📊 Getrackte Prozesse: {proc_status['total_tracked']}")
        except Exception as e:
            print(f"🔄 Background-Prozesse: ❌ Fehler: {e}")
        
        # System-Info
        print(f"\n💻 SYSTEM-INFO:")
        print(f"🐍 Python: {sys.version.split()[0]}")
        print(f"📁 Arbeitsverzeichnis: {Path.cwd()}")
        print(f"⏰ Aktuelle Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Status-Fehler: {e}")

def cmd_test_single(args):
    """Testet Update für eine einzelne App"""
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        
        api_key = load_api_key_from_env()
        tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        
        print(f"🧪 Teste Update für App {args.app_id}...")
        print("=" * 40)
        
        # App-Details vor Update
        if hasattr(tracker, 'get_app_details'):
            details = tracker.get_app_details(args.app_id)
            if details:
                print(f"📱 App Name: {details.get('name', 'Unbekannt')}")
                print(f"🆔 App ID: {args.app_id}")
                print(f"📅 Letztes Update: {details.get('last_price_update', 'Nie')}")
        
        # Update durchführen
        print(f"\n🔄 Führe Update durch...")
        start_time = datetime.now()
        
        success = tracker.update_price_for_app(args.app_id)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if success:
            print(f"✅ Update erfolgreich! (Dauer: {duration:.1f}s)")
            
            # Neue Details anzeigen
            if hasattr(tracker, 'get_latest_price_data'):
                price_data = tracker.get_latest_price_data(args.app_id)
                if price_data:
                    print(f"\n💰 AKTUELLE PREISE:")
                    stores = ['steam', 'greenmangaming', 'gog', 'humblestore', 'fanatical', 'gamesplanet']
                    for store in stores:
                        price_col = f"{store}_price"
                        available_col = f"{store}_available"
                        
                        if price_data.get(available_col):
                            price = price_data.get(price_col, 0)
                            print(f"   💰 {store.upper()}: €{price:.2f}")
        else:
            print(f"❌ Update fehlgeschlagen! (Dauer: {duration:.1f}s)")
            
    except ImportError:
        print("❌ price_tracker Modul nicht gefunden")
    except Exception as e:
        print(f"❌ Test-Fehler: {e}")

def cmd_update_names(args):
    """Aktualisiert App-Namen von Steam API"""
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        
        api_key = load_api_key_from_env()
        if not api_key:
            print("❌ Steam API Key erforderlich für Namen-Updates")
            print("💡 Konfiguriere API Key in .env-Datei")
            return
        
        tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        
        print("📝 APP-NAMEN UPDATE")
        print("=" * 25)
        
        if args.all:
            print("🔄 Aktualisiere Namen für ALLE Apps...")
            
            if hasattr(tracker, 'update_all_app_names'):
                result = tracker.update_all_app_names()
                
                if result:
                    print(f"✅ Namen-Update abgeschlossen:")
                    print(f"   📊 {result.get('updated', 0)} Namen aktualisiert")
                    print(f"   ⚠️ {result.get('failed', 0)} fehlgeschlagen")
                    print(f"   ⏱️ Dauer: {result.get('duration', 0):.1f}s")
            else:
                print("❌ Namen-Update-Funktion nicht verfügbar")
                
        elif args.generic_only:
            print("🔄 Aktualisiere nur Apps mit generischen Namen...")
            
            if hasattr(tracker, 'update_generic_app_names'):
                result = tracker.update_generic_app_names()
                
                if result:
                    print(f"✅ Generische Namen aktualisiert:")
                    print(f"   📊 {result.get('updated', 0)} Namen aktualisiert")
                    print(f"   ⏱️ Dauer: {result.get('duration', 0):.1f}s")
            else:
                print("❌ Generische Namen-Update nicht verfügbar")
                
        elif args.app_ids:
            app_ids = [app_id.strip() for app_id in args.app_ids.split(',') if app_id.strip()]
            print(f"🔄 Aktualisiere Namen für {len(app_ids)} spezifische Apps...")
            
            updated = 0
            failed = 0
            
            for app_id in app_ids:
                if hasattr(tracker, 'update_app_name'):
                    success = tracker.update_app_name(app_id)
                    if success:
                        updated += 1
                        print(f"   ✅ App {app_id}: Namen aktualisiert")
                    else:
                        failed += 1
                        print(f"   ❌ App {app_id}: Update fehlgeschlagen")
                        
            print(f"\n📊 ERGEBNIS:")
            print(f"   ✅ Erfolgreich: {updated}")
            print(f"   ❌ Fehlgeschlagen: {failed}")
        else:
            print("❌ Bitte wähle eine Option: --all, --generic-only oder --app-ids")
            
    except ImportError:
        print("❌ price_tracker Modul nicht gefunden")
    except Exception as e:
        print(f"❌ Namen-Update-Fehler: {e}")

def cmd_name_candidates(args):
    """Zeigt Apps mit generischen Namen"""
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        
        api_key = load_api_key_from_env()
        tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        
        print("📝 APPS MIT GENERISCHEN NAMEN")
        print("=" * 35)
        
        if hasattr(tracker, 'get_apps_with_generic_names'):
            candidates = tracker.get_apps_with_generic_names()
            
            if candidates:
                print(f"⚠️ {len(candidates)} Apps mit generischen Namen gefunden:")
                print()
                
                for i, app in enumerate(candidates[:args.limit], 1):
                    name = app.get('name', 'Unbekannt')
                    app_id = app.get('steam_app_id', 'N/A')
                    
                    print(f"{i:2d}. {name}")
                    print(f"    🆔 App ID: {app_id}")
                    print()
                    
                if len(candidates) > args.limit:
                    remaining = len(candidates) - args.limit
                    print(f"... und {remaining} weitere Apps")
                    
                print(f"\n💡 Verwende 'batch-processor update-names --generic-only' um diese zu aktualisieren")
            else:
                print("✅ Keine Apps mit generischen Namen gefunden")
        else:
            print("❌ Generische Namen-Suche nicht verfügbar")
            
    except ImportError:
        print("❌ price_tracker Modul nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_name_history(args):
    """Zeigt Namen-Update-Historie"""
    try:
        from database_manager import DatabaseManager
        
        db = DatabaseManager()
        
        print("📝 NAMEN-UPDATE-HISTORIE")
        print("=" * 30)
        
        if hasattr(db, 'get_name_update_history'):
            history = db.get_name_update_history(limit=args.limit)
            
            if history:
                print(f"📊 Letzte {len(history)} Namen-Updates:")
                print()
                
                for i, entry in enumerate(history, 1):
                    old_name = entry.get('old_name', 'N/A')
                    new_name = entry.get('new_name', 'N/A')
                    app_id = entry.get('steam_app_id', 'N/A')
                    updated_at = entry.get('updated_at', 'N/A')
                    
                    print(f"{i:2d}. App {app_id}")
                    print(f"    📅 {updated_at}")
                    print(f"    📝 '{old_name}' → '{new_name}'")
                    print()
            else:
                print("📭 Keine Namen-Update-Historie verfügbar")
        else:
            print("❌ Namen-Historie-Funktion nicht verfügbar")
            
    except ImportError:
        print("❌ database_manager Modul nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_test_name_fetch(args):
    """Testet Namen-Abruf für eine App"""
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        
        api_key = load_api_key_from_env()
        if not api_key:
            print("❌ Steam API Key erforderlich für Namen-Abruf")
            return
            
        tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        
        print(f"🧪 Teste Namen-Abruf für App {args.app_id}...")
        print("=" * 40)
        
        # Aktueller Name aus Datenbank
        if hasattr(tracker, 'get_app_details'):
            details = tracker.get_app_details(args.app_id)
            if details:
                current_name = details.get('name', 'Unbekannt')
                print(f"📱 Aktueller Name: {current_name}")
        
        # Namen von Steam API abrufen
        if hasattr(tracker, 'fetch_app_name_from_steam'):
            print(f"🔄 Rufe Namen von Steam API ab...")
            
            steam_name = tracker.fetch_app_name_from_steam(args.app_id)
            
            if steam_name:
                print(f"🚀 Steam API Name: {steam_name}")
                
                if args.update_db:
                    print(f"💾 Aktualisiere Namen in Datenbank...")
                    success = tracker.update_app_name(args.app_id, steam_name)
                    
                    if success:
                        print(f"✅ Name erfolgreich aktualisiert!")
                    else:
                        print(f"❌ Datenbank-Update fehlgeschlagen")
            else:
                print(f"❌ Konnte Namen nicht von Steam API abrufen")
        else:
            print("❌ Steam Namen-Abruf-Funktion nicht verfügbar")
            
    except ImportError:
        print("❌ price_tracker Modul nicht gefunden")
    except Exception as e:
        print(f"❌ Test-Fehler: {e}")

def cmd_maintenance(args):
    """Führt erweiterte Wartungsaufgaben aus"""
    try:
        from database_manager import DatabaseManager
        
        print("🔧 ERWEITERTE WARTUNGSAUFGABEN")
        print("=" * 35)
        
        db = DatabaseManager()
        
        print("🧹 Führe Datenbank-Wartung durch...")
        
        # Alte Snapshots bereinigen
        if hasattr(db, 'cleanup_old_prices'):
            deleted = db.cleanup_old_prices(days=90)
            print(f"   ✅ {deleted} alte Preis-Snapshots entfernt")
        
        # Datenbank optimieren
        if hasattr(db, 'vacuum_database'):
            db.vacuum_database()
            print(f"   ✅ Datenbank optimiert")
        
        # Verwaiste Einträge entfernen
        if hasattr(db, 'cleanup_orphaned_entries'):
            orphaned = db.cleanup_orphaned_entries()
            print(f"   ✅ {orphaned} verwaiste Einträge entfernt")
        
        # Statistiken aktualisieren
        if hasattr(db, 'update_statistics'):
            db.update_statistics()
            print(f"   ✅ Statistiken aktualisiert")
        
        print("✅ Wartung abgeschlossen!")
        
    except ImportError:
        print("❌ database_manager Modul nicht gefunden")
    except Exception as e:
        print(f"❌ Wartungs-Fehler: {e}")

def cmd_export_all(args):
    """Exportiert alle Apps als CSV"""
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        
        api_key = load_api_key_from_env()
        tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        
        print("📄 EXPORTIERE ALLE APPS")
        print("=" * 25)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"exports/batch_export_{timestamp}.csv"
        
        print(f"🔄 Erstelle CSV-Export: {output_file}")
        
        if hasattr(tracker, 'export_to_csv'):
            success = tracker.export_to_csv(output_file)
            
            if success:
                print(f"✅ CSV-Export erfolgreich erstellt: {output_file}")
                
                # Datei-Info anzeigen
                export_path = Path(output_file)
                if export_path.exists():
                    size_kb = export_path.stat().st_size / 1024
                    print(f"📁 Dateigröße: {size_kb:.1f} KB")
            else:
                print(f"❌ CSV-Export fehlgeschlagen")
        else:
            print("❌ CSV-Export-Funktion nicht verfügbar")
            
    except ImportError:
        print("❌ price_tracker Modul nicht gefunden")
    except Exception as e:
        print(f"❌ Export-Fehler: {e}")

def cmd_stats(args):
    """Zeigt detaillierte Statistiken"""
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        from database_manager import DatabaseManager
        
        api_key = load_api_key_from_env()
        tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        db = DatabaseManager()
        
        print("📊 DETAILLIERTE STATISTIKEN")
        print("=" * 30)
        
        # Apps Statistiken
        tracked_apps = tracker.get_tracked_apps()
        print(f"📱 APPS:")
        print(f"   🎯 Getrackte Apps: {len(tracked_apps) if tracked_apps else 0}")
        
        # Pending Apps
        if hasattr(tracker, 'get_apps_needing_update'):
            pending = tracker.get_apps_needing_update(hours_threshold=args.hours)
            print(f"   ⏰ Benötigen Update: {len(pending) if pending else 0}")
        
        # Preis-Snapshots
        if hasattr(db, 'get_total_price_snapshots'):
            total_snapshots = db.get_total_price_snapshots()
            print(f"   💾 Preis-Snapshots: {total_snapshots:,}")
        
        # Charts-Statistiken (falls verfügbar)
        if tracker.charts_enabled and hasattr(tracker, 'charts_manager'):
            if hasattr(tracker.charts_manager, 'get_chart_statistics'):
                charts_stats = tracker.charts_manager.get_chart_statistics()
                if charts_stats:
                    total_charts = sum(charts_stats.values())
                    print(f"\n📊 CHARTS:")
                    print(f"   🏆 Charts-Spiele: {total_charts}")
                    for chart_type, count in charts_stats.items():
                        print(f"   📈 {chart_type}: {count}")
        
        # Datenbank-Info
        db_file = Path("steam_price_tracker.db")
        if db_file.exists():
            size_mb = db_file.stat().st_size / 1024 / 1024
            print(f"\n💾 DATENBANK:")
            print(f"   📁 Größe: {size_mb:.1f} MB")
            print(f"   📅 Letzte Änderung: {datetime.fromtimestamp(db_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Scheduler-Info
        if hasattr(tracker, 'get_enhanced_scheduler_status'):
            status = tracker.get_enhanced_scheduler_status()
            print(f"\n⏰ SCHEDULER:")
            print(f"   🔄 Status: {'✅ AKTIV' if status.get('scheduler_running') else '❌ INAKTIV'}")
            
            charts_status = status.get('charts_scheduler_status', {})
            if charts_status:
                active_charts = sum(1 for s in charts_status.values() if s.get('is_running'))
                print(f"   📊 Charts-Scheduler: {active_charts} aktiv")
        
    except Exception as e:
        print(f"❌ Statistik-Fehler: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Enhanced Batch Processor - Steam Price Tracker Verwaltung",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s batch --hours 6           - Batch-Update für Apps älter als 6h
  %(prog)s specific --app-ids "413150,105600" - Update für spezifische Apps
  %(prog)s pending --hours 24        - Zeige Apps die Updates benötigen
  %(prog)s status                    - Detaillierter System-Status
  %(prog)s test-single --app-id 413150 - Teste Update für eine App
  %(prog)s update-names --all        - Aktualisiere alle App-Namen
  %(prog)s update-names --generic-only - Nur generische Namen
  %(prog)s name-candidates            - Apps mit generischen Namen anzeigen
  %(prog)s test-name --app-id 413150  - Teste Namen-Abruf für eine App
  %(prog)s maintenance                - Wartungsaufgaben ausführen
  %(prog)s export-all                 - Alle Apps als CSV exportieren
  %(prog)s stats --hours 24           - Detaillierte Statistiken anzeigen
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Verfügbare Kommandos')
    
    # Batch Command
    batch_parser = subparsers.add_parser('batch', help='Optimiertes Batch-Update')
    batch_parser.add_argument('--hours', type=int, default=6, 
                             help='Apps älter als X Stunden aktualisieren (Standard: 6)')
    batch_parser.set_defaults(func=cmd_run_batch)
    
    # Specific Command
    specific_parser = subparsers.add_parser('specific', help='Update für spezifische Apps')
    specific_parser.add_argument('--app-ids', required=True,
                                help='Komma-getrennte Liste von Steam App IDs')
    specific_parser.set_defaults(func=cmd_run_specific)
    
    # Pending Command
    pending_parser = subparsers.add_parser('pending', help='Apps die Updates benötigen')
    pending_parser.add_argument('--hours', type=int, default=24,
                               help='Threshold in Stunden (Standard: 24)')
    pending_parser.add_argument('--limit', type=int, default=20,
                               help='Anzahl Apps anzeigen (Standard: 20)')
    pending_parser.set_defaults(func=cmd_show_pending)
    
    # Status Command
    status_parser = subparsers.add_parser('status', help='System-Status anzeigen')
    status_parser.set_defaults(func=cmd_system_status)
    
    # Test Single Command
    test_parser = subparsers.add_parser('test-single', help='Teste Update für eine App')
    test_parser.add_argument('--app-id', required=True,
                            help='Steam App ID zum Testen')
    test_parser.set_defaults(func=cmd_test_single)
    
    # Name Update Commands
    name_parser = subparsers.add_parser('update-names', help='App-Namen von Steam aktualisieren')
    name_group = name_parser.add_mutually_exclusive_group()
    name_group.add_argument('--all', action='store_true', 
                           help='Namen für ALLE Apps aktualisieren')
    name_group.add_argument('--generic-only', action='store_true',
                           help='Nur Apps mit generischen Namen aktualisieren')
    name_group.add_argument('--app-ids',
                           help='Komma-getrennte App IDs für Namen-Update')
    name_parser.set_defaults(func=cmd_update_names)
    
    # Name Candidates Command
    candidates_parser = subparsers.add_parser('name-candidates', help='Apps mit generischen Namen anzeigen')
    candidates_parser.add_argument('--limit', type=int, default=20,
                                  help='Anzahl Apps anzeigen (Standard: 20)')
    candidates_parser.set_defaults(func=cmd_name_candidates)
    
    # Name History Command
    history_parser = subparsers.add_parser('name-history', help='Namen-Update-Historie anzeigen')
    history_parser.add_argument('--limit', type=int, default=20,
                               help='Anzahl Einträge anzeigen (Standard: 20)')
    history_parser.set_defaults(func=cmd_name_history)
    
    # Test Name Fetch Command
    test_name_parser = subparsers.add_parser('test-name', help='Teste Namen-Abruf für eine App')
    test_name_parser.add_argument('--app-id', required=True,
                                 help='Steam App ID zum Testen')
    test_name_parser.add_argument('--update-db', action='store_true',
                                 help='Namen in Datenbank aktualisieren')
    test_name_parser.set_defaults(func=cmd_test_name_fetch)
    
    # Maintenance Command
    maintenance_parser = subparsers.add_parser('maintenance', help='Erweiterte Wartungsaufgaben')
    maintenance_parser.set_defaults(func=cmd_maintenance)
    
    # Export Command
    export_parser = subparsers.add_parser('export-all', help='Alle Apps als CSV exportieren')
    export_parser.set_defaults(func=cmd_export_all)
    
    # Stats Command
    stats_parser = subparsers.add_parser('stats', help='Detaillierte Statistiken anzeigen')
    stats_parser.add_argument('--hours', type=int, default=24,
                             help='Threshold für pending Apps (Standard: 24)')
    stats_parser.set_defaults(func=cmd_stats)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Führe den entsprechenden Befehl aus
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n⏹️ Abgebrochen durch Benutzer")
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        logger.exception("Unerwarteter Fehler in enhanced_batch_processor")

if __name__ == "__main__":
    main()