#!/usr/bin/env python3
"""
Charts CLI Manager - Steam Charts Management via Kommandozeile
Vollständiges CLI-Tool für Charts-Tracking, Updates und Automatisierung
"""

import sys
import argparse
import time as time_module
from datetime import datetime
from pathlib import Path
import logging

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cmd_status(args):
    """Zeigt Charts-Status an"""
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        
        api_key = load_api_key_from_env()
        tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        
        print("📊 STEAM CHARTS STATUS")
        print("=" * 30)
        
        if not tracker.charts_enabled:
            print("❌ Charts-Funktionalität nicht verfügbar")
            print("💡 Prüfe Steam API Key in .env-Datei")
            return
        
        # Status-Details abrufen
        if hasattr(tracker, 'get_enhanced_scheduler_status'):
            status = tracker.get_enhanced_scheduler_status()
            charts_status = status.get('charts_scheduler_status', {})
            
            print(f"🔧 Charts verfügbar: ✅")
            print(f"🚀 Status: {'✅ AKTIV' if any(s.get('is_running') for s in charts_status.values()) else '❌ INAKTIV'}")
            
            if charts_status:
                print("\n📋 AKTIVE SCHEDULER:")
                for scheduler_type, info in charts_status.items():
                    is_running = info.get('is_running', False)
                    next_run = info.get('next_run', 'Unbekannt')
                    status_emoji = "✅" if is_running else "❌"
                    print(f"   {status_emoji} {scheduler_type}: {next_run}")
            
            # Charts-Statistiken
            if hasattr(tracker, 'charts_manager') and tracker.charts_manager:
                if hasattr(tracker.charts_manager, 'get_chart_statistics'):
                    stats = tracker.charts_manager.get_chart_statistics()
                    if stats:
                        print(f"\n📊 CHARTS-STATISTIKEN:")
                        total_games = sum(stats.values())
                        print(f"   🎯 Gesamt Charts-Spiele: {total_games}")
                        for chart_type, count in stats.items():
                            print(f"   📈 {chart_type}: {count} Spiele")
        else:
            print("⚠️ Enhanced Scheduler Status nicht verfügbar")
            
    except ImportError:
        print("❌ Price Tracker Module nicht gefunden")
        print("💡 Führe 'python setup.py charts' aus")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_enable_charts(args):
    """Aktiviert Charts-Tracking"""
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        
        api_key = load_api_key_from_env()
        tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        
        if not tracker.charts_enabled:
            print("❌ Charts-Funktionalität nicht verfügbar")
            print("💡 Prüfe Steam API Key in .env-Datei")
            return
        
        print("🚀 Aktiviere Charts-Tracking...")
        print(f"   📊 Charts-Updates: alle {args.charts_hours}h")
        print(f"   💰 Preis-Updates: alle {args.price_hours}h")
        print(f"   🧹 Cleanup: alle {args.cleanup_hours}h")
        
        success = tracker.enable_charts_tracking(
            charts_update_hours=args.charts_hours,
            price_update_hours=args.price_hours,
            cleanup_hours=args.cleanup_hours
        )
        
        if success:
            print("✅ Charts-Tracking erfolgreich aktiviert!")
            print()
            print("📋 AKTIVE SCHEDULER:")
            print(f"   📊 Charts-Updates: alle {args.charts_hours}h")
            print(f"   💰 Preis-Updates: alle {args.price_hours}h")  
            print(f"   🧹 Cleanup: alle {args.cleanup_hours}h")
        else:
            print("❌ Fehler beim Aktivieren des Charts-Trackings")
            
    except ImportError as e:
        print(f"❌ Import Fehler: {e}")
        print("💡 Stelle sicher, dass alle Dateien vorhanden sind")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_disable_charts(args):
    """Deaktiviert Charts-Tracking"""
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        
        api_key = load_api_key_from_env()
        tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        
        if not tracker.charts_enabled:
            print("ℹ️ Charts-Tracking ist bereits deaktiviert")
            return
        
        print("⏹️ Deaktiviere Charts-Tracking...")
        
        success = tracker.disable_charts_tracking()
        
        if success:
            print("✅ Charts-Tracking deaktiviert")
        else:
            print("❌ Fehler beim Deaktivieren")
            
    except ImportError:
        print("❌ Price Tracker Module nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_update_charts(args):
    """Führt Charts-Update durch"""
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        
        api_key = load_api_key_from_env()
        tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        
        if not tracker.charts_enabled:
            print("❌ Charts-Funktionalität nicht verfügbar")
            return
        
        # Chart-Typen bestimmen
        chart_types = None
        if args.chart_types:
            chart_types = [ct.strip() for ct in args.chart_types.split(',')]
            print(f"🎯 Aktualisiere spezifische Charts: {', '.join(chart_types)}")
        else:
            print("📊 Aktualisiere alle Charts...")
        
        if hasattr(tracker, 'charts_manager') and tracker.charts_manager:
            if hasattr(tracker.charts_manager, 'update_all_charts'):
                print("🔄 Starte Charts-Update...")
                start_time = time_module.time()
                
                result = tracker.charts_manager.update_all_charts()
                
                end_time = time_module.time()
                duration = end_time - start_time
                
                if result:
                    print(f"✅ Charts-Update erfolgreich abgeschlossen! (Dauer: {duration:.1f}s)")
                    if isinstance(result, dict):
                        print(f"   📊 Neue Spiele hinzugefügt: {result.get('new_games_added', 0)}")
                        print(f"   🔄 Bestehende aktualisiert: {result.get('existing_games_updated', 0)}")
                else:
                    print("❌ Charts-Update fehlgeschlagen")
            else:
                print("❌ Charts-Update-Funktion nicht verfügbar")
        else:
            print("❌ Charts-Manager nicht verfügbar")
            
    except ImportError:
        print("❌ Price Tracker Module nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_update_prices(args):
    """Aktualisiert Charts-Preise"""
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        
        api_key = load_api_key_from_env()
        tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        
        if not tracker.charts_enabled:
            print("❌ Charts-Funktionalität nicht verfügbar")
            return
        
        print("💰 Aktualisiere Charts-Preise...")
        
        if hasattr(tracker, 'charts_manager') and tracker.charts_manager:
            if hasattr(tracker.charts_manager, 'update_charts_prices'):
                start_time = time_module.time()
                result = tracker.charts_manager.update_charts_prices()
                duration = time_module.time() - start_time
                
                if result:
                    print(f"✅ Charts-Preise erfolgreich aktualisiert! (Dauer: {duration:.1f}s)")
                    if isinstance(result, dict):
                        updated = result.get('updated_count', 0)
                        failed = result.get('failed_count', 0)
                        print(f"   ✅ Erfolgreich: {updated}")
                        if failed > 0:
                            print(f"   ❌ Fehlgeschlagen: {failed}")
                else:
                    print("❌ Charts-Preis-Update fehlgeschlagen")
            else:
                print("❌ Charts-Preis-Update-Funktion nicht verfügbar")
        else:
            print("❌ Charts-Manager nicht verfügbar")
            
    except ImportError:
        print("❌ Price Tracker Module nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_charts_deals(args):
    """Zeigt Charts-Deals an"""
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        
        api_key = load_api_key_from_env()
        tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        
        if not tracker.charts_enabled:
            print("❌ Charts-Funktionalität nicht verfügbar")
            return
        
        print(f"🎯 CHARTS-DEALS (Mindestrabatt: {args.min_discount}%)")
        print("=" * 50)
        
        # Charts-Deals abrufen
        if hasattr(tracker, 'get_trending_price_drops'):
            deals = tracker.get_trending_price_drops(
                hours_back=args.hours,
                min_discount=args.min_discount
            )
            
            if deals:
                print(f"📊 Top {len(deals)} Charts-Deals:")
                print()
                
                for i, deal in enumerate(deals[:args.limit], 1):
                    name = deal.get('game_title', 'Unbekannt')[:50]
                    current_price = deal.get('current_price', 0)
                    discount = deal.get('discount_percent', 0)
                    store = deal.get('store', 'Unknown')
                    chart_type = deal.get('chart_type', 'N/A')
                    
                    print(f"{i:2d}. {name}")
                    print(f"    💰 €{current_price:.2f} (-{discount}%) bei {store}")
                    print(f"    📊 Chart: {chart_type}")
                    print()
            else:
                print("😔 Keine Charts-Deals gefunden")
                print("💡 Tipp: Reduziere den Mindestrabatt oder prüfe die Charts-Daten")
        else:
            print("❌ Charts-Deals-Funktion nicht verfügbar")
            
    except ImportError:
        print("❌ Price Tracker Module nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_trending_drops(args):
    """Zeigt Trending Price Drops an"""
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        
        api_key = load_api_key_from_env()
        tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        
        if not tracker.charts_enabled:
            print("❌ Charts-Funktionalität nicht verfügbar")
            return
        
        print(f"📉 TRENDING PRICE DROPS (letzte {args.hours}h)")
        print("=" * 50)
        
        if hasattr(tracker, 'get_trending_price_drops'):
            deals = tracker.get_trending_price_drops(
                hours_back=args.hours,
                min_discount=args.min_discount
            )
            
            if deals:
                print(f"🔥 {len(deals)} neue Price Drops:")
                print()
                
                for i, deal in enumerate(deals[:15], 1):
                    name = deal.get('game_title', 'Unbekannt')[:45]
                    current_price = deal.get('current_price', 0)
                    discount = deal.get('discount_percent', 0)
                    store = deal.get('store', 'Unknown')
                    chart_type = deal.get('chart_type', 'N/A')
                    
                    print(f"{i:2d}. {name}")
                    print(f"    💰 €{current_price:.2f} (-{discount}%) bei {store}")
                    print(f"    📊 {chart_type} | ⏰ Neu in den letzten {args.hours}h")
                    print()
            else:
                print("😔 Keine neuen Price Drops gefunden")
        else:
            print("❌ Trending Price Drops Funktion nicht verfügbar")
            
    except ImportError:
        print("❌ Price Tracker Module nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_charts_list(args):
    """Listet Charts-Spiele auf"""
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        
        api_key = load_api_key_from_env()
        tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        
        if not tracker.charts_enabled:
            print("❌ Charts-Funktionalität nicht verfügbar")
            return
        
        print(f"📋 CHARTS-SPIELE ({args.chart_type})")
        print("=" * 40)
        
        if hasattr(tracker, 'charts_manager') and tracker.charts_manager:
            if hasattr(tracker.charts_manager, 'get_chart_games'):
                games = tracker.charts_manager.get_chart_games(args.chart_type, args.limit)
                
                if games:
                    print(f"🏆 Top {len(games)} {args.chart_type.replace('_', ' ').title()}:")
                    print()
                    
                    for i, game in enumerate(games, 1):
                        name = game.get('name', 'Unbekannt')[:50]
                        position = game.get('position', i)
                        app_id = game.get('steam_app_id', 'N/A')
                        
                        print(f"{position:2d}. {name}")
                        print(f"    🆔 App ID: {app_id}")
                        print()
                else:
                    print(f"😔 Keine Spiele für {args.chart_type} gefunden")
            else:
                print("❌ Charts-Listen-Funktion nicht verfügbar")
        else:
            print("❌ Charts-Manager nicht verfügbar")
            
    except ImportError:
        print("❌ Price Tracker Module nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_charts_cleanup(args):
    """Bereinigt alte Charts-Spiele"""
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        
        api_key = load_api_key_from_env()
        tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        
        if not tracker.charts_enabled:
            print("❌ Charts-Funktionalität nicht verfügbar")
            return
        
        print(f"🧹 Bereinige Charts-Spiele älter als {args.days} Tage...")
        
        if hasattr(tracker, 'charts_manager') and tracker.charts_manager:
            if hasattr(tracker.charts_manager, 'cleanup_old_chart_games'):
                removed = tracker.charts_manager.cleanup_old_chart_games(args.days)
                
                if removed > 0:
                    print(f"✅ {removed} alte Charts-Spiele entfernt")
                else:
                    print("✅ Keine alten Charts-Spiele zum Entfernen gefunden")
            else:
                print("❌ Charts-Cleanup Funktion nicht verfügbar")
        else:
            print("❌ Charts-Manager nicht verfügbar")
            
    except ImportError:
        print("❌ Price Tracker Module nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_charts_export(args):
    """Exportiert Charts-Daten"""
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        
        api_key = load_api_key_from_env()
        tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        
        if not tracker.charts_enabled:
            print("❌ Charts-Funktionalität nicht verfügbar")
            return
        
        print("📄 Starte Charts-Export...")
        
        output_file = args.output
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"exports/charts_export_{timestamp}.csv"
        
        if hasattr(tracker, 'charts_manager') and tracker.charts_manager:
            if hasattr(tracker.charts_manager, 'export_charts_data_csv'):
                csv_file = tracker.charts_manager.export_charts_data_csv(output_file)
                
                if csv_file:
                    print(f"✅ Charts-Export erstellt: {csv_file}")
                else:
                    print("❌ Export fehlgeschlagen (keine Daten?)")
            else:
                print("❌ Charts-Export-Funktion nicht verfügbar")
        else:
            print("❌ Charts-Manager nicht verfügbar")
            
    except ImportError:
        print("❌ Price Tracker Module nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_setup_automation(args):
    """Richtet vollautomatisches Tracking ein"""
    try:
        from price_tracker import create_price_tracker, setup_full_automation
        from steam_wishlist_manager import load_api_key_from_env
        
        api_key = load_api_key_from_env()
        tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        
        print("🤖 CHARTS-AUTOMATISIERUNG EINRICHTEN")
        print("=" * 40)
        
        if not tracker.charts_enabled:
            print("❌ Charts-Funktionalität nicht verfügbar")
            print("💡 Konfiguriere Steam API Key in .env-Datei")
            return
        
        print("🚀 Richte vollautomatisches Tracking ein...")
        print(f"   🎯 Normale Apps: alle {args.normal_hours}h")
        print(f"   📊 Charts-Updates: alle {args.charts_hours}h")
        print(f"   💰 Charts-Preise: alle {args.charts_price_hours}h")
        
        # Vollautomatisierung einrichten
        success = setup_full_automation(
            tracker,
            normal_interval=args.normal_hours,
            charts_interval=args.charts_hours,
            charts_price_interval=args.charts_price_hours,
            name_interval=30  # Namen alle 30 Minuten
        )
        
        if success:
            print("✅ Vollautomatisches Tracking erfolgreich eingerichtet!")
            print()
            print("📋 AKTIVE SCHEDULER:")
            print(f"   🎯 Normale Apps: alle {args.normal_hours}h")
            
            if tracker.charts_enabled:
                print(f"   📊 Charts-Updates: alle {args.charts_hours}h")
                print(f"   💰 Charts-Preise: alle {args.charts_price_hours}h")
                print(f"   🧹 Charts-Cleanup: alle 24h")
            else:
                print("   ⚠️ Charts-Tracking nicht verfügbar (kein API Key)")
            
            print("\n💡 NÄCHSTE SCHRITTE:")
            print("   • Das Programm läuft nun automatisch im Hintergrund")
            print("   • Verwende 'charts-cli status' um den Status zu prüfen")
            print("   • Mit Ctrl+C kannst du das Programm stoppen")
            
            # Endlos-Schleife für kontinuierliches Tracking
            if args.run_continuous:
                print("\n🔄 Starte kontinuierliches Tracking... (Ctrl+C zum Stoppen)")
                try:
                    import time
                    while True:
                        time.sleep(60)  # Überprüfe jede Minute
                except KeyboardInterrupt:
                    print("\n⏹️ Tracking gestoppt durch Benutzer")
                    tracker.stop_background_scheduler()
                    if tracker.charts_enabled:
                        tracker.disable_charts_tracking()
                    print("✅ Alle Scheduler gestoppt")
        else:
            print("❌ Fehler beim Einrichten der Automatisierung")
            
    except ImportError:
        print("❌ Price Tracker Module nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Steam Charts CLI Manager - Automatisches Charts-Tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s enable --charts-hours 6 --price-hours 4    # Charts-Tracking aktivieren
  %(prog)s disable                                     # Charts-Tracking deaktivieren  
  %(prog)s update                                      # Alle Charts aktualisieren
  %(prog)s update --chart-types "most_played,top_releases"  # Spezifische Charts
  %(prog)s update-prices                               # Charts-Preise aktualisieren
  %(prog)s status                                      # Charts-Status anzeigen
  %(prog)s deals --limit 15                           # Beste Charts-Deals
  %(prog)s trending --hours 24 --min-discount 30      # Trending Price Drops
  %(prog)s list --chart-type most_played --limit 50   # Charts-Spiele auflisten
  %(prog)s cleanup --days 30                          # Alte Charts-Spiele entfernen
  %(prog)s export --output charts.csv                 # Charts-Daten exportieren
  %(prog)s setup-automation --run-continuous          # Vollautomatik einrichten
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Verfügbare Kommandos')
    
    # Status Command
    status_parser = subparsers.add_parser('status', help='Charts-Status anzeigen')
    status_parser.set_defaults(func=cmd_status)
    
    # Enable Charts Command
    enable_parser = subparsers.add_parser('enable', help='Charts-Tracking aktivieren')
    enable_parser.add_argument('--charts-hours', type=int, default=6,
                              help='Charts-Update Intervall in Stunden (Standard: 6)')
    enable_parser.add_argument('--price-hours', type=int, default=4,
                              help='Charts-Preis-Update Intervall in Stunden (Standard: 4)')
    enable_parser.add_argument('--cleanup-hours', type=int, default=24,
                              help='Charts-Cleanup Intervall in Stunden (Standard: 24)')
    enable_parser.set_defaults(func=cmd_enable_charts)
    
    # Disable Charts Command
    disable_parser = subparsers.add_parser('disable', help='Charts-Tracking deaktivieren')
    disable_parser.set_defaults(func=cmd_disable_charts)
    
    # Update Charts Command
    update_parser = subparsers.add_parser('update', help='Charts aktualisieren')
    update_parser.add_argument('--chart-types',
                              help='Komma-getrennte Liste der Chart-Typen (Standard: alle)')
    update_parser.set_defaults(func=cmd_update_charts)
    
    # Update Prices Command
    update_prices_parser = subparsers.add_parser('update-prices', help='Charts-Preise aktualisieren')
    update_prices_parser.set_defaults(func=cmd_update_prices)
    
    # Deals Command
    deals_parser = subparsers.add_parser('deals', help='Charts-Deals anzeigen')
    deals_parser.add_argument('--limit', type=int, default=15,
                             help='Anzahl Deals (Standard: 15)')
    deals_parser.add_argument('--min-discount', type=int, default=20,
                             help='Mindestrabatt in Prozent (Standard: 20)')
    deals_parser.add_argument('--hours', type=int, default=24,
                             help='Zeitfenster in Stunden (Standard: 24)')
    deals_parser.set_defaults(func=cmd_charts_deals)
    
    # Trending Command
    trending_parser = subparsers.add_parser('trending', help='Trending Price Drops anzeigen')
    trending_parser.add_argument('--hours', type=int, default=24,
                                help='Zeitfenster in Stunden (Standard: 24)')
    trending_parser.add_argument('--min-discount', type=int, default=30,
                                help='Mindestrabatt in Prozent (Standard: 30)')
    trending_parser.set_defaults(func=cmd_trending_drops)
    
    # List Command
    list_parser = subparsers.add_parser('list', help='Charts-Spiele auflisten')
    list_parser.add_argument('--chart-type', default='most_played',
                            choices=['most_played', 'top_releases', 'best_sellers', 'weekly_top_sellers'],
                            help='Chart-Typ (Standard: most_played)')
    list_parser.add_argument('--limit', type=int, default=20,
                            help='Anzahl Spiele (Standard: 20)')
    list_parser.set_defaults(func=cmd_charts_list)
    
    # Cleanup Command
    cleanup_parser = subparsers.add_parser('cleanup', help='Alte Charts-Spiele entfernen')
    cleanup_parser.add_argument('--days', type=int, default=30,
                               help='Tage ohne Charts-Präsenz (Standard: 30)')
    cleanup_parser.set_defaults(func=cmd_charts_cleanup)
    
    # Export Command
    export_parser = subparsers.add_parser('export', help='Charts-Daten exportieren')
    export_parser.add_argument('--output',
                              help='Ausgabedatei (Standard: automatisch generiert)')
    export_parser.set_defaults(func=cmd_charts_export)
    
    # Setup Automation Command
    setup_parser = subparsers.add_parser('setup-automation', help='Vollautomatisches Tracking einrichten')
    setup_parser.add_argument('--normal-hours', type=int, default=6,
                             help='Intervall für normale Apps in Stunden (Standard: 6)')
    setup_parser.add_argument('--charts-hours', type=int, default=6,
                             help='Intervall für Charts-Updates in Stunden (Standard: 6)')
    setup_parser.add_argument('--charts-price-hours', type=int, default=4,
                             help='Intervall für Charts-Preise in Stunden (Standard: 4)')
    setup_parser.add_argument('--run-continuous', action='store_true',
                             help='Startet kontinuierliches Tracking nach Setup')
    setup_parser.set_defaults(func=cmd_setup_automation)
    
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
        logger.exception("Unerwarteter Fehler in Charts CLI")

if __name__ == "__main__":
    main()