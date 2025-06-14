#!/usr/bin/env python3
"""
Batch Processor CLI - Einfache Verwaltung für das integrierte System
Verwendet die bewährte price_tracker.py Logic mit neuen Batch-Optimierungen
"""

import sys
import argparse
from datetime import datetime
from price_tracker import SteamPriceTracker
from database_manager import DatabaseManager

def cmd_run_batch(args):
    """Führt optimiertes Batch-Update aus"""
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

def cmd_run_specific(args):
    """Führt Update für spezifische Apps aus"""
    tracker = SteamPriceTracker()
    
    app_ids = args.app_ids.split(',') if args.app_ids else []
    
    if not app_ids:
        print("❌ Keine App IDs angegeben")
        return
    
    print(f"🎯 Starte Update für {len(app_ids)} spezifische Apps...")
    
    stats = tracker.process_specific_apps_optimized(app_ids)
    
    if stats.get('successful') is not None:
        print(f"✅ Spezifisches Update abgeschlossen:")
        print(f"   📊 {stats['successful']}/{stats['batch_size']} Apps erfolgreich")
        print(f"   ⏱️ Dauer: {stats['duration_seconds']}s")
        print(f"   ⚡ {stats['apps_per_second']:.1f} Apps/s")
    else:
        print(f"❌ Update fehlgeschlagen: {stats.get('error', 'Unbekannter Fehler')}")

def cmd_run_classic(args):
    """Führt klassisches Update aus (für Kompatibilität)"""
    tracker = SteamPriceTracker()
    
    # Hole Apps die Updates benötigen
    apps = tracker.get_apps_needing_price_update(args.hours)
    
    if not apps:
        print("✅ Alle Apps sind aktuell!")
        return
    
    app_ids = [app['steam_app_id'] for app in apps]
    
    print(f"🔄 Starte klassisches Update für {len(app_ids)} Apps...")
    
    # Verwende die bewährte track_app_prices Methode
    stats = tracker.track_app_prices(app_ids)
    
    print(f"✅ Klassisches Update abgeschlossen:")
    print(f"   📊 {stats['successful']}/{stats['processed']} Apps erfolgreich")
    
    if stats['failed'] > 0:
        print(f"   ⚠️ {stats['failed']} Apps fehlgeschlagen")

def cmd_status(args):
    """Zeigt System-Status"""
    tracker = SteamPriceTracker()
    stats = tracker.get_statistics()
    
    print("📊 SYSTEM STATUS")
    print("=" * 30)
    
    print(f"📚 Getrackte Apps: {stats['tracked_apps']}")
    print(f"📈 Gesamt Snapshots: {stats.get('total_snapshots', stats.get('total_price_snapshots', 0)):,}")
    print(f"🏪 Stores: {', '.join(stats['stores_tracked'])}")
    
    if stats.get('processing_active'):
        print("⚙️ Processing: AKTIV ✅")
    else:
        print("⚙️ Processing: INAKTIV ❌")
    
    # Apps die Updates benötigen
    apps_needing_update = tracker.get_apps_needing_price_update(6)
    print(f"⚠️ Apps benötigen Update (6h): {len(apps_needing_update)}")
    
    if stats.get('newest_snapshot'):
        print(f"🕐 Letzte Preisabfrage: {stats['newest_snapshot'][:19]}")

def cmd_list_pending(args):
    """Listet Apps die Updates benötigen"""
    tracker = SteamPriceTracker()
    
    apps = tracker.get_apps_needing_price_update(args.hours)
    
    print(f"📋 APPS DIE UPDATE BENÖTIGEN (älter als {args.hours}h)")
    print("=" * 60)
    
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

def cmd_test_single(args):
    """Testet Preisabfrage für eine einzelne App"""
    tracker = SteamPriceTracker()
    
    print(f"🧪 Teste Preisabfrage für App ID: {args.app_id}")
    
    # Verwende die bewährte Einzelabfrage-Methode  
    tracker.print_price_summary(args.app_id)

def cmd_maintenance(args):
    """Führt Wartungsaufgaben aus"""
    tracker = SteamPriceTracker()
    
    print("🔧 Starte Wartungsaufgaben...")
    
    # Alte Snapshots bereinigen
    print("🧹 Bereinige alte Snapshots (>90 Tage)...")
    before_cleanup = tracker.db_manager.get_total_price_snapshots()
    tracker.db_manager.cleanup_old_prices(days=90)
    after_cleanup = tracker.db_manager.get_total_price_snapshots()
    
    cleaned = before_cleanup - after_cleanup
    print(f"   ✅ {cleaned} alte Snapshots entfernt")
    
    # Datenbank optimieren
    print("🔧 Optimiere Datenbank...")
    tracker.db_manager.vacuum_database()
    print("   ✅ Datenbank optimiert")
    
    # Backup erstellen
    print("💾 Erstelle Backup...")
    backup_file = tracker.db_manager.backup_database()
    if backup_file:
        print(f"   ✅ Backup erstellt: {backup_file}")
    else:
        print("   ❌ Backup fehlgeschlagen")

def main():
    parser = argparse.ArgumentParser(
        description="Steam Price Tracker - Batch Processing CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s batch                       - Alle Apps batch-verarbeiten (6h)
  %(prog)s batch --hours 12            - Apps älter als 12h batch-verarbeiten
  %(prog)s specific --apps 123,456     - Spezifische Apps verarbeiten
  %(prog)s classic --hours 6           - Klassische Verarbeitung (kompatibel)
  %(prog)s test --app-id 413150        - Einzelne App testen
  %(prog)s status                      - System-Status anzeigen
  %(prog)s list --hours 24             - Apps die Updates benötigen
  %(prog)s maintenance                 - Wartungsaufgaben ausführen

BEWÄHRTE vs NEUE Methoden:
  batch    - NEUE optimierte Batch-Verarbeitung (empfohlen)
  classic  - BEWÄHRTE Einzelverarbeitung (100% kompatibel)
  specific - NEUE optimierte Verarbeitung für ausgewählte Apps
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Verfügbare Kommandos')
    
    # Batch Command (NEU, optimiert)
    batch_parser = subparsers.add_parser('batch', help='Optimierte Batch-Verarbeitung')
    batch_parser.add_argument('--hours', type=int, default=6, 
                             help='Apps älter als X Stunden verarbeiten (default: 6)')
    batch_parser.set_defaults(func=cmd_run_batch)
    
    # Specific Command (NEU)
    specific_parser = subparsers.add_parser('specific', help='Spezifische Apps verarbeiten')
    specific_parser.add_argument('--apps', dest='app_ids', required=True,
                                help='Komma-getrennte Liste von App IDs')
    specific_parser.set_defaults(func=cmd_run_specific)
    
    # Classic Command (BEWÄHRT)
    classic_parser = subparsers.add_parser('classic', help='Klassische Verarbeitung')
    classic_parser.add_argument('--hours', type=int, default=6,
                               help='Apps älter als X Stunden verarbeiten (default: 6)')
    classic_parser.set_defaults(func=cmd_run_classic)
    
    # Test Command
    test_parser = subparsers.add_parser('test', help='Einzelne App testen')
    test_parser.add_argument('--app-id', required=True,
                           help='Steam App ID zum Testen')
    test_parser.set_defaults(func=cmd_test_single)
    
    # Status Command
    status_parser = subparsers.add_parser('status', help='System-Status anzeigen')
    status_parser.set_defaults(func=cmd_status)
    
    # List Command
    list_parser = subparsers.add_parser('list', help='Apps die Updates benötigen')
    list_parser.add_argument('--hours', type=int, default=6,
                           help='Apps älter als X Stunden (default: 6)')
    list_parser.set_defaults(func=cmd_list_pending)
    
    # Maintenance Command
    maintenance_parser = subparsers.add_parser('maintenance', help='Wartungsaufgaben')
    maintenance_parser.set_defaults(func=cmd_maintenance)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n⚠️ Abgebrochen durch Benutzer")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()