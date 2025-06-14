#!/usr/bin/env python3
"""
Batch Processor CLI - Erweiterte Verwaltung für Steam Price Tracker
Bietet spezialisierte Befehle für Batch-Verarbeitung und Wartung
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

def cmd_show_pending(args):
    """Zeigt Apps die Updates benötigen"""
    try:
        from price_tracker import SteamPriceTracker
        tracker = SteamPriceTracker()
        
        apps = tracker.get_apps_needing_price_update(args.hours)
        
        if not apps:
            print("✅ Alle Apps sind aktuell!")
            return
        
        print(f"⚠️ {len(apps)} Apps benötigen Update:")
        
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

def cmd_maintenance(args):
    """Führt Wartungsaufgaben aus"""
    try:
        from price_tracker import SteamPriceTracker
        from database_manager import DatabaseManager
        
        tracker = SteamPriceTracker()
        db = tracker.db_manager
        
        print("🔧 Starte Wartungsaufgaben...")
        
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
        
        # Statistiken anzeigen
        print("\n📊 Aktuelle Statistiken:")
        stats = db.get_statistics()
        print(f"   📚 Getrackte Apps: {stats['tracked_apps']}")
        print(f"   📈 Gesamt Snapshots: {stats['total_snapshots']:,}")
        print(f"   🏪 Stores: {len(stats['stores_tracked'])}")
        
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
        print(f"\n⏰ Apps die Updates benötigen (>{args.hours}h): {len(pending_apps)}")
        
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
        description="Steam Price Tracker - Batch Processing CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s batch --hours 6           - Batch-Update für Apps älter als 6h
  %(prog)s specific --app-ids "413150,105600"  - Update für spezifische Apps
  %(prog)s pending --hours 12        - Zeige Apps die Updates benötigen
  %(prog)s test --app-id 413150       - Teste Preisabfrage für eine App
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
    pending_parser = subparsers.add_parser('pending', help='Zeige Apps die Updates benötigen')
    pending_parser.add_argument('--hours', type=int, default=6,
                               help='Apps älter als X Stunden anzeigen (Standard: 6)')
    pending_parser.set_defaults(func=cmd_show_pending)
    
    # Test Command
    test_parser = subparsers.add_parser('test', help='Teste Preisabfrage für eine App')
    test_parser.add_argument('--app-id', required=True,
                           help='Steam App ID zum Testen')
    test_parser.set_defaults(func=cmd_test_single)
    
    # Maintenance Command
    maintenance_parser = subparsers.add_parser('maintenance', help='Wartungsaufgaben ausführen')
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
        logger.exception("Unerwarteter Fehler in batch_processor")

if __name__ == "__main__":
    main()