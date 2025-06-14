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
        from price_tracker import SteamPriceTracker
        tracker = SteamPriceTracker()
        
        print("🚀 Starte optimiertes Batch-Update...")
        print(f"   ⏱️ Threshold: {args.hours}h")
        
        stats = tracker.process_all_pending_apps_optimized(args.hours)
        
        if stats.get('success'):
            print(f"✅ Batch-Update erfolgreich:")
            print(f"   📊 {stats['total_successful']}/{stats['total_apps']} Apps erfolgreich")
            print(f"   ⏱️ Dauer: {stats['total_duration']}s")
            print(f"   📦 {stats['total_batches']} Batches")
            print(f"   ⚡ {stats['apps_per_second']:.1f} Apps/s")
            
            if stats['total_failed'] > 0:
                print(f"   ⚠️ {stats['total_failed']} Apps fehlgeschlagen")
        else:
            print(f"❌ Batch-Update fehlgeschlagen: {stats.get('error', 'Unbekannter Fehler')}")
            
    except ImportError:
        print("❌ price_tracker Modul nicht gefunden")
        print("💡 Führe zuerst 'python setup.py install' aus")
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")

def cmd_run_specific(args):
    """Führt Update für spezifische Apps aus"""
    try:
        from price_tracker import SteamPriceTracker
        tracker = SteamPriceTracker()
        
        app_ids = [app_id.strip() for app_id in args.app_ids.split(',') if app_id.strip()]
        
        if not app_ids:
            print("❌ Keine App IDs angegeben")
            return
        
        print(f"🎯 Starte Update für {len(app_ids)} spezifische Apps...")
        
        result = tracker.track_app_prices(app_ids)
        
        print(f"✅ Spezifisches Update abgeschlossen:")
        print(f"   📊 {result['successful']}/{result['processed']} Apps erfolgreich")
        
        if result['errors']:
            print(f"   ⚠️ {len(result['errors'])} Fehler:")
            for error in result['errors'][:5]:  # Nur erste 5 anzeigen
                print(f"      - {error}")
            if len(result['errors']) > 5:
                print(f"      ... und {len(result['errors']) - 5} weitere")
                
    except ImportError:
        print("❌ price_tracker Modul nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_update_names(args):
    """Aktualisiert App-Namen von Steam API"""
    try:
        from price_tracker import SteamPriceTracker
        from steam_wishlist_manager import load_api_key_from_env
        
        # API Key laden
        api_key = load_api_key_from_env()
        if not api_key:
            print("❌ Kein Steam API Key in .env gefunden")
            print("💡 Füge STEAM_API_KEY=dein_key zu .env hinzu")
            return
        
        tracker = SteamPriceTracker()
        
        if args.all:
            # Alle Apps
            tracked_apps = tracker.get_tracked_apps()
            if not tracked_apps:
                print("❌ Keine Apps im Tracking")
                return
            
            app_ids = [app['steam_app_id'] for app in tracked_apps]
            print(f"🔤 Aktualisiere Namen für ALLE {len(app_ids)} Apps...")
            
            result = tracker.update_app_names_from_steam(app_ids, api_key)
        
        elif args.generic_only:
            # Nur Apps mit generischen Namen
            print("🔤 Aktualisiere Namen für Apps mit generischen Namen...")
            result = tracker.update_names_for_apps_with_generic_names(api_key)
        
        elif args.app_ids:
            # Spezifische App IDs
            app_ids = [app_id.strip() for app_id in args.app_ids.split(',') if app_id.strip()]
            if not app_ids:
                print("❌ Keine gültigen App IDs angegeben")
                return
            
            print(f"🔤 Aktualisiere Namen für {len(app_ids)} spezifische Apps...")
            result = tracker.update_app_names_from_steam(app_ids, api_key)
        
        else:
            # Standard: nur generische Namen
            print("🔤 Aktualisiere Namen für Apps mit generischen Namen...")
            result = tracker.update_names_for_apps_with_generic_names(api_key)
        
        if result['success']:
            print(f"✅ Namen-Update abgeschlossen:")
            print(f"   📊 {result['updated']}/{result['total']} Apps erfolgreich ({result.get('success_rate', 0):.1f}%)")
            print(f"   ❌ {result['failed']} Apps fehlgeschlagen")
        else:
            print(f"❌ Namen-Update fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")
            
    except ImportError:
        print("❌ Erforderliche Module nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler beim Namen-Update: {e}")

def cmd_show_pending(args):
    """Zeigt Apps die Updates benötigen"""
    try:
        from price_tracker import SteamPriceTracker
        tracker = SteamPriceTracker()
        
        apps = tracker.get_apps_needing_price_update(args.hours)
        
        if not apps:
            print("✅ Alle Apps sind aktuell!")
            return
        
        print(f"⚠️ {len(apps)} Apps benötigen Preis-Update:")
        
        for i, app in enumerate(apps[:20], 1):  # Nur erste 20 anzeigen
            last_update = app.get('last_price_update', 'Nie')
            if last_update and last_update != 'Nie':
                last_update = last_update[:19]
            
            print(f"{i:3d}. {app['name'][:40]:<40} (ID: {app['steam_app_id']}) - {last_update}")
        
        if len(apps) > 20:
            print(f"   ... und {len(apps) - 20} weitere Apps")
            
    except ImportError:
        print("❌ price_tracker Modul nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_show_name_candidates(args):
    """Zeigt Apps die Namen-Updates benötigen"""
    try:
        from price_tracker import SteamPriceTracker
        tracker = SteamPriceTracker()
        
        # Apps mit generischen Namen
        generic_apps = tracker.get_name_update_candidates()
        
        if not generic_apps:
            print("✅ Alle Apps haben korrekte Namen!")
            return
        
        print(f"🔤 {len(generic_apps)} Apps mit generischen Namen:")
        
        for i, app in enumerate(generic_apps, 1):
            attempts = app.get('name_update_attempts', 0)
            last_update = app.get('last_name_update', 'Nie')
            if last_update and last_update != 'Nie':
                last_update = last_update[:19]
            
            status = ""
            if attempts > 3:
                status = " ❌"
            elif attempts > 0:
                status = f" ⚠️({attempts})"
            
            print(f"{i:3d}. {app['name']}{status}")
            print(f"     🆔 {app['steam_app_id']} | Hinzugefügt: {app['added_at'][:10]} | Update: {last_update}")
        
        # Apps die nie Namen-Updates hatten
        if hasattr(tracker.db_manager, 'get_apps_needing_name_update'):
            name_pending = tracker.db_manager.get_apps_needing_name_update(hours_threshold=168)  # 1 Woche
            if name_pending:
                print(f"\n⏰ {len(name_pending)} Apps benötigen Namen-Updates (>1 Woche alt):")
                for app in name_pending[:10]:
                    print(f"   • {app['name']} (ID: {app['steam_app_id']})")
                if len(name_pending) > 10:
                    print(f"   ... und {len(name_pending) - 10} weitere")
            
    except ImportError:
        print("❌ price_tracker Modul nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_show_name_history(args):
    """Zeigt Namen-Update Historie"""
    try:
        from price_tracker import SteamPriceTracker
        tracker = SteamPriceTracker()
        
        if not hasattr(tracker.db_manager, 'get_name_update_history'):
            print("❌ Namen-Update Historie nicht verfügbar")
            print("💡 Aktualisiere auf die neueste Version")
            return
        
        history = tracker.db_manager.get_name_update_history(
            steam_app_id=args.app_id,
            limit=args.limit
        )
        
        if not history:
            if args.app_id:
                print(f"❌ Keine Namen-Historie für App {args.app_id} gefunden")
            else:
                print("❌ Keine Namen-Update Historie gefunden")
            return
        
        if args.app_id:
            print(f"📝 Namen-Historie für App {args.app_id}:")
        else:
            print(f"📝 Letzte {len(history)} Namen-Updates:")
        
        print()
        
        for entry in history:
            date = entry['updated_at'][:19]
            app_id = entry['steam_app_id']
            old_name = entry['old_name'] or 'N/A'
            new_name = entry['new_name']
            source = entry['update_source']
            current_name = entry.get('current_name', new_name)
            
            print(f"📅 {date} | {source}")
            print(f"   🆔 App ID: {app_id}")
            print(f"   📝 {old_name} → {new_name}")
            if current_name != new_name:
                print(f"   🔄 Aktuell: {current_name}")
            print()
            
    except ImportError:
        print("❌ price_tracker Modul nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_test_single(args):
    """Testet Preisabfrage für eine einzelne App"""
    try:
        from price_tracker import SteamPriceTracker
        tracker = SteamPriceTracker()
        
        print(f"🧪 Teste Preisabfrage für App ID: {args.app_id}")
        
        # Verwende die bewährte Einzelabfrage-Methode  
        tracker.print_price_summary(args.app_id)
        
    except ImportError:
        print("❌ price_tracker Modul nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_test_name_fetch(args):
    """Testet Namen-Abruf für eine einzelne App"""
    try:
        from steam_wishlist_manager import load_api_key_from_env, SteamWishlistManager
        
        # API Key laden
        api_key = load_api_key_from_env()
        if not api_key:
            print("❌ Kein Steam API Key in .env gefunden")
            return
        
        print(f"🧪 Teste Namen-Abruf für App ID: {args.app_id}")
        
        steam_manager = SteamWishlistManager(api_key)
        app_name = steam_manager.get_app_name_only(args.app_id)
        
        if app_name:
            print(f"✅ Name gefunden: {app_name}")
            
            # In Datenbank aktualisieren?
            if args.update_db:
                from price_tracker import SteamPriceTracker
                tracker = SteamPriceTracker()
                
                if tracker.db_manager.update_app_name(args.app_id, app_name, 'manual_test'):
                    print(f"✅ Name in Datenbank aktualisiert")
                else:
                    print(f"⚠️ Fehler beim Aktualisieren in Datenbank")
        else:
            print(f"❌ Kein Name für App {args.app_id} gefunden")
            
    except ImportError:
        print("❌ Erforderliche Module nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_maintenance(args):
    """Führt erweiterte Wartungsaufgaben aus"""
    try:
        from price_tracker import SteamPriceTracker
        from database_manager import DatabaseManager
        
        tracker = SteamPriceTracker()
        db = tracker.db_manager
        
        print("🔧 Starte erweiterte Wartungsaufgaben...")
        
        # Alte Snapshots bereinigen
        print("🧹 Bereinige alte Snapshots (>90 Tage)...")
        before_cleanup = db.get_total_price_snapshots()
        deleted_count = db.cleanup_old_prices(days=90)
        after_cleanup = db.get_total_price_snapshots()
        
        print(f"   ✅ {deleted_count} alte Snapshots entfernt")
        
        # Datenbank optimieren
        print("🔧 Optimiere Datenbank...")
        db.vacuum_database()
        print("   ✅ Datenbank optimiert")
        
        # Backup erstellen
        print("💾 Erstelle Backup...")
        backup_file = db.backup_database()
        if backup_file:
            print(f"   ✅ Backup erstellt: {backup_file}")
        else:
            print("   ❌ Backup fehlgeschlagen")
        
        # Erweiterte Statistiken anzeigen
        print("\n📊 Erweiterte Statistiken:")
        stats = db.get_statistics()
        print(f"   📚 Getrackte Apps: {stats['tracked_apps']}")
        print(f"   📈 Gesamt Snapshots: {stats['total_snapshots']:,}")
        print(f"   🏪 Stores: {len(stats['stores_tracked'])}")
        
        # Namen-Update Statistiken
        if 'name_update_stats' in stats:
            name_stats = stats['name_update_stats']
            print(f"\n🔤 Namen-Update Statistiken:")
            print(f"   📝 Apps mit generischen Namen: {name_stats['apps_with_generic_names']}")
            print(f"   ❓ Apps ohne Namen-Update: {name_stats['apps_never_updated']}")
            print(f"   🔄 Gesamt Namen-Updates: {name_stats['total_name_updates']}")
            print(f"   📊 Namen-Updates (24h): {name_stats['updates_last_24h']}")
            print(f"   ❌ Fehlgeschlagene Updates: {name_stats['failed_updates']}")
        
    except ImportError:
        print("❌ Benötigte Module nicht gefunden")
    except Exception as e:
        print(f"❌ Wartung fehlgeschlagen: {e}")

def cmd_export_all(args):
    """Exportiert Daten für alle Apps"""
    try:
        from price_tracker import SteamPriceTracker
        tracker = SteamPriceTracker()
        
        tracked_apps = tracker.get_tracked_apps()
        
        if not tracked_apps:
            print("❌ Keine Apps im Tracking")
            return
        
        print(f"📄 Starte Export für {len(tracked_apps)} Apps...")
        
        # Export-Verzeichnis erstellen
        export_dir = Path("exports") / datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir.mkdir(parents=True, exist_ok=True)
        
        successful_exports = 0
        failed_exports = 0
        
        for i, app in enumerate(tracked_apps, 1):
            app_id = app['steam_app_id']
            app_name = app['name']
            
            print(f"📄 ({i}/{len(tracked_apps)}) Exportiere {app_name}...")
            
            try:
                # Sicherer Dateiname erstellen
                safe_name = "".join(c for c in app_name if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_name = safe_name[:50]  # Kürzen falls zu lang
                
                output_file = export_dir / f"{app_id}_{safe_name}.csv"
                
                csv_file = tracker.export_price_history_csv(app_id, str(output_file))
                
                if csv_file:
                    successful_exports += 1
                else:
                    failed_exports += 1
                    print(f"   ⚠️ Keine Daten für {app_name}")
                    
            except Exception as e:
                failed_exports += 1
                print(f"   ❌ Fehler bei {app_name}: {e}")
        
        print(f"\n✅ Export abgeschlossen:")
        print(f"   📁 Verzeichnis: {export_dir}")
        print(f"   ✅ Erfolgreich: {successful_exports}")
        print(f"   ❌ Fehlgeschlagen: {failed_exports}")
        
    except ImportError:
        print("❌ price_tracker Modul nicht gefunden")
    except Exception as e:
        print(f"❌ Export fehlgeschlagen: {e}")

def cmd_stats(args):
    """Zeigt detaillierte Statistiken"""
    try:
        from price_tracker import SteamPriceTracker
        tracker = SteamPriceTracker()
        
        print("📊 DETAILLIERTE STATISTIKEN")
        print("=" * 30)
        
        # Basis-Statistiken
        stats = tracker.get_statistics()
        print(f"📚 Getrackte Apps: {stats['tracked_apps']}")
        print(f"📈 Gesamt Snapshots: {stats['total_snapshots']:,}")
        print(f"🏪 Stores mit Daten: {len(stats['stores_tracked'])}")
        print(f"   {', '.join(stats['stores_tracked'])}")
        
        if stats.get('oldest_snapshot'):
            print(f"📅 Ältester Snapshot: {stats['oldest_snapshot'][:19]}")
        if stats.get('newest_snapshot'):
            print(f"📅 Neuester Snapshot: {stats['newest_snapshot'][:19]}")
        
        # Apps die Updates benötigen
        pending_apps = tracker.get_apps_needing_price_update(args.hours)
        print(f"\n⏰ Apps die Preis-Updates benötigen (>{args.hours}h): {len(pending_apps)}")
        
        # Namen-Update Statistiken
        if 'name_update_stats' in stats:
            name_stats = stats['name_update_stats']
            print(f"\n🔤 NAMEN-UPDATE STATISTIKEN:")
            print(f"   📝 Apps mit generischen Namen: {name_stats['apps_with_generic_names']}")
            print(f"   ❓ Apps ohne Namen-Update: {name_stats['apps_never_updated']}")
            print(f"   🔄 Gesamt Namen-Updates: {name_stats['total_name_updates']}")
            print(f"   📊 Namen-Updates (24h): {name_stats['updates_last_24h']}")
            print(f"   ❌ Fehlgeschlagene Updates: {name_stats['failed_updates']}")
        
        # Beste Deals
        deals = tracker.get_current_best_deals(limit=5)
        if deals:
            print(f"\n🏆 Top 5 Deals:")
            for i, deal in enumerate(deals, 1):
                print(f"   {i}. {deal['game_title'][:30]:<30} - €{deal['best_price']:.2f} (-{deal['discount_percent']}%)")
        
        # Scheduler Status
        try:
            scheduler_status = tracker.get_scheduler_status()
            print(f"\n🚀 Scheduler Status: {'AKTIV' if scheduler_status['scheduler_running'] else 'INAKTIV'}")
            if scheduler_status['scheduler_running']:
                print(f"   ⏰ Nächster Lauf: {scheduler_status.get('next_run', 'Unbekannt')}")
        except:
            print("\n🚀 Scheduler Status: Unbekannt")
        
    except ImportError:
        print("❌ price_tracker Modul nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler beim Laden der Statistiken: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Enhanced Steam Price Tracker - Batch Processing CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s batch --hours 6           - Batch-Update für Apps älter als 6h
  %(prog)s specific --app-ids "413150,105600"  - Update für spezifische Apps
  %(prog)s pending --hours 12        - Zeige Apps die Updates benötigen
  %(prog)s test --app-id 413150       - Teste Preisabfrage für eine App
  %(prog)s update-names --generic-only - Namen für Apps mit generischen Namen
  %(prog)s update-names --all         - Namen für ALLE Apps aktualisieren
  %(prog)s name-candidates            - Apps mit generischen Namen anzeigen
  %(prog)s name-history --limit 20    - Namen-Update Historie anzeigen
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
    
    # Name Update Commands
    name_parser = subparsers.add_parser('update-names', help='App-Namen von Steam aktualisieren')
    name_group = name_parser.add_mutually_exclusive_group()
    name_group.add_argument('--all', action='store_true', 
                           help='Namen für ALLE Apps aktualisieren')
    name_group.add_argument('--generic-only', action='store_true',
                           help='Nur Apps mit generischen Namen aktualisieren')
    name_group.add_argument('--app-ids', 
                           help='Komma-getrennte Liste von Steam App IDs')
    name_parser.set_defaults(func=cmd_update_names)
    
    # Name Candidates Command
    candidates_parser = subparsers.add_parser('name-candidates', 
                                            help='Apps mit generischen Namen anzeigen')
    candidates_parser.set_defaults(func=cmd_show_name_candidates)
    
    # Name History Command
    history_parser = subparsers.add_parser('name-history', help='Namen-Update Historie anzeigen')
    history_parser.add_argument('--app-id', help='App ID für spezifische Historie')
    history_parser.add_argument('--limit', type=int, default=50,
                               help='Anzahl Einträge (Standard: 50)')
    history_parser.set_defaults(func=cmd_show_name_history)
    
    # Pending Command
    pending_parser = subparsers.add_parser('pending', help='Zeige Apps die Updates benötigen')
    pending_parser.add_argument('--hours', type=int, default=6,
                               help='Apps älter als X Stunden anzeigen (Standard: 6)')
    pending_parser.set_defaults(func=cmd_show_pending)
    
    # Test Command
    test_parser = subparsers.add_parser('test', help='Teste Preisabfrage für eine App')
    test_parser.add_argument('--app-id', required=True,
                           help='Steam App ID zum Testen')
    test_parser.set_defaults(func=cmd_test_single)
    
    # Test Name Command
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