#!/usr/bin/env python3
"""
Steam Charts CLI Manager
Command-Line Interface für Steam Charts Tracking
UPDATED: Verwendet konsolidierte price_tracker.py
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
import logging

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cmd_enable_charts(args):
    """Aktiviert Charts-Tracking"""
    try:
        # UPDATED: Verwende konsolidierte price_tracker.py
        from price_tracker import create_price_tracker
        
        tracker = create_price_tracker()
        
        if not tracker.charts_enabled:
            print("❌ Charts-Funktionalität nicht verfügbar")
            print("💡 Prüfe ob STEAM_API_KEY in .env gesetzt ist")
            return
        
        print("🚀 Aktiviere Charts-Tracking...")
        
        success = tracker.enable_charts_tracking(
            charts_update_hours=args.charts_hours,
            price_update_hours=args.price_hours,
            cleanup_hours=args.cleanup_hours
        )
        
        if success:
            print("✅ Charts-Tracking erfolgreich aktiviert!")
            print(f"   📊 Charts-Updates: alle {args.charts_hours}h")
            print(f"   💰 Preis-Updates: alle {args.price_hours}h")  
            print(f"   🧹 Cleanup: alle {args.cleanup_hours}h")
        else:
            print("❌ Fehler beim Aktivieren des Charts-Trackings")
            
    except ImportError:
        print("❌ Price Tracker Module nicht gefunden")
        print("💡 Stelle sicher, dass alle Dateien vorhanden sind")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_disable_charts(args):
    """Deaktiviert Charts-Tracking"""
    try:
        # UPDATED: Verwende konsolidierte price_tracker.py
        from price_tracker import create_price_tracker
        
        tracker = create_price_tracker()
        
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
        # UPDATED: Verwende konsolidierte price_tracker.py
        from price_tracker import create_price_tracker
        
        tracker = create_price_tracker()
        
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
        
        result = tracker.update_charts_now(chart_types)
        
        if result.get('success', True):
            print("✅ Charts-Update abgeschlossen:")
            print(f"   📊 {result.get('total_games_found', 0)} Spiele gefunden")
            print(f"   ➕ {result.get('new_games_added', 0)} neue Spiele")
            print(f"   🔄 {result.get('existing_games_updated', 0)} aktualisiert")
            
            if result.get('errors'):
                print(f"   ⚠️ {len(result['errors'])} Fehler aufgetreten")
        else:
            print(f"❌ Charts-Update fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")
            
    except ImportError:
        print("❌ Price Tracker Module nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_update_charts_prices(args):
    """Führt Preis-Update für Charts durch"""
    try:
        # UPDATED: Verwende konsolidierte price_tracker.py
        from price_tracker import create_price_tracker
        
        tracker = create_price_tracker()
        
        if not tracker.charts_enabled:
            print("❌ Charts-Funktionalität nicht verfügbar")
            return
        
        chart_type = args.chart_type if hasattr(args, 'chart_type') else None
        
        if chart_type:
            print(f"💰 Aktualisiere Preise für {chart_type}...")
        else:
            print("💰 Aktualisiere Preise für alle Charts-Spiele...")
        
        result = tracker.update_charts_prices_now(chart_type)
        
        if result.get('success', True):
            print("✅ Charts-Preisupdate abgeschlossen:")
            print(f"   📊 {result.get('total_games', 0)} Spiele verarbeitet")
            print(f"   💰 {result.get('successful', 0)} erfolgreich aktualisiert")
            
            if result.get('failed', 0) > 0:
                print(f"   ❌ {result['failed']} fehlgeschlagen")
        else:
            print(f"❌ Charts-Preisupdate fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")
            
    except ImportError:
        print("❌ Price Tracker Module nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_charts_status(args):
    """Zeigt Charts-Status an"""
    try:
        # UPDATED: Verwende konsolidierte price_tracker.py
        from price_tracker import create_price_tracker
        
        tracker = create_price_tracker()
        
        print("📊 STEAM CHARTS STATUS")
        print("=" * 30)
        
        if not tracker.charts_enabled:
            print("❌ Charts-Funktionalität nicht verfügbar")
            print("💡 Prüfe STEAM_API_KEY in .env-Datei")
            return
        
        # Charts-Übersicht holen
        if hasattr(tracker, 'get_charts_overview'):
            overview = tracker.get_charts_overview()
        else:
            # Fallback: Basis-Informationen
            overview = {
                'enabled': tracker.charts_enabled,
                'message': 'Charts verfügbar aber get_charts_overview() nicht implementiert'
            }
        
        if overview.get('enabled'):
            print("✅ Charts-Tracking: AKTIVIERT")
            
            # Scheduler Status
            scheduler_status = overview.get('scheduler_status', {})
            if scheduler_status.get('charts_scheduler_running'):
                print("🚀 Scheduler: AKTIV")
                print(f"   ⏰ Nächstes Charts-Update: {scheduler_status.get('next_charts_update', 'N/A')}")
                print(f"   💰 Nächstes Preis-Update: {scheduler_status.get('next_price_update', 'N/A')}")
                print(f"   🧹 Nächstes Cleanup: {scheduler_status.get('next_cleanup', 'N/A')}")
            else:
                print("⏸️ Scheduler: INAKTIV")
            
            # Chart-Typen
            chart_types = overview.get('chart_types', {})
            if chart_types:
                print(f"\n📈 CHART-TYPEN ({len(chart_types)}):")
                for chart_type, info in chart_types.items():
                    print(f"   • {info['description']}: {info['active_games']} Spiele")
                    
                    # Top 3 Spiele anzeigen
                    top_games = info.get('top_games', [])[:3]
                    for game in top_games:
                        print(f"     #{game['rank']}: {game['name']}")
            
            # Letzte Aktivitäten
            activity = overview.get('recent_activity', {})
            if activity:
                print(f"\n📊 AKTIVITÄTS-ÜBERSICHT:")
                print(f"   📚 Aktive Charts-Spiele: {activity.get('total_active_games', 0)}")
                print(f"   🎮 Einzigartige Apps: {activity.get('unique_apps', 0)}")
                print(f"   💰 Preis-Updates heute: {activity.get('price_updates_today', 0)}")
                print(f"   📅 Durchschnitt in Charts: {activity.get('average_days_in_charts', 0):.1f} Tage")
        else:
            print("❌ Charts-Tracking: DEAKTIVIERT")
            if 'error' in overview:
                print(f"   Fehler: {overview['error']}")
            
    except ImportError:
        print("❌ Price Tracker Module nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_charts_deals(args):
    """Zeigt beste Charts-Deals"""
    try:
        # UPDATED: Verwende konsolidierte price_tracker.py
        from price_tracker import create_price_tracker
        
        tracker = create_price_tracker()
        
        if not tracker.charts_enabled:
            print("❌ Charts-Funktionalität nicht verfügbar")
            return
        
        chart_type = args.chart_type if hasattr(args, 'chart_type') else None
        
        if chart_type:
            print(f"🏆 BESTE DEALS: {chart_type.upper()}")
        else:
            print("🏆 BESTE CHARTS-DEALS")
        
        print("=" * 40)
        
        deals = tracker.get_best_charts_deals(limit=args.limit, chart_type=chart_type)
        
        if deals:
            for i, deal in enumerate(deals, 1):
                rank_info = f"#{deal.get('current_rank', '?')}" if deal.get('current_rank') else ""
                chart_info = f"[{deal.get('chart_type', 'Unknown')}]" if not chart_type else ""
                
                print(f"{i:2d}. {deal['game_title'][:40]:<40} {rank_info} {chart_info}")
                print(f"    💰 €{deal['best_price']:.2f} (-{deal['discount_percent']}%) bei {deal['best_store']}")
                print(f"    🆔 App ID: {deal['steam_app_id']}")
                print()
        else:
            print("❌ Keine Charts-Deals gefunden")
            
    except ImportError:
        print("❌ Price Tracker Module nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_charts_trending(args):
    """Zeigt Trending Price Drops"""
    try:
        # UPDATED: Verwende konsolidierte price_tracker.py
        from price_tracker import create_price_tracker
        
        tracker = create_price_tracker()
        
        if not tracker.charts_enabled:
            print("❌ Charts-Funktionalität nicht verfügbar")
            return
        
        print(f"📈 TRENDING PRICE DROPS (letzte {args.hours}h, min. {args.min_discount}%)")
        print("=" * 50)
        
        trending = tracker.get_trending_price_drops(
            hours_back=args.hours,
            min_discount=args.min_discount
        )
        
        if trending:
            for i, item in enumerate(trending, 1):
                chart_badge = f"[{item['chart_type']}]"
                
                print(f"{i:2d}. {item['game_title'][:35]:<35} {chart_badge}")
                print(f"    💰 €{item['current_price']:.2f} (-{item['discount_percent']}%) bei {item['store']}")
                print(f"    📅 {item['timestamp'][:16]}")
                print()
        else:
            print("❌ Keine Trending Price Drops gefunden")
            print("💡 Versuche niedrigeren Mindestrabatt oder längeren Zeitraum")
            
    except ImportError:
        print("❌ Price Tracker Module nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_charts_list(args):
    """Listet Charts-Spiele auf"""
    try:
        # UPDATED: Verwende konsolidierte price_tracker.py
        from price_tracker import create_price_tracker
        
        tracker = create_price_tracker()
        
        if not tracker.charts_enabled:
            print("❌ Charts-Funktionalität nicht verfügbar")
            return
        
        chart_type = args.chart_type if hasattr(args, 'chart_type') else None
        
        if chart_type:
            print(f"📋 CHARTS-SPIELE: {chart_type.upper()}")
        else:
            print("📋 ALLE CHARTS-SPIELE")
        
        print("=" * 40)
        
        # Aktive Charts-Spiele holen
        if hasattr(tracker.db_manager, 'get_active_chart_games'):
            games = tracker.db_manager.get_active_chart_games(chart_type)
            
            if games:
                # Nach Chart-Typ und Rang sortieren
                games.sort(key=lambda x: (x.get('chart_type', ''), x.get('current_rank', 999)))
                
                current_chart = None
                for game in games[:args.limit]:
                    # Chart-Typ Header
                    if game.get('chart_type') != current_chart:
                        current_chart = game.get('chart_type')
                        if not chart_type:  # Nur anzeigen wenn nicht gefiltert
                            print(f"\n📊 {current_chart.upper()}")
                            print("-" * 30)
                    
                    rank = game.get('current_rank', 0)
                    rank_display = f"#{rank:3d}" if rank > 0 else "   -"
                    
                    first_seen = game.get('first_seen', '')[:10]
                    last_seen = game.get('last_seen', '')[:10]
                    
                    print(f"{rank_display} {game['name'][:35]:<35}")
                    print(f"     🆔 {game['steam_app_id']} | 📅 {first_seen} - {last_seen}")
                
                print(f"\n📊 Gesamt: {len(games)} aktive Charts-Spiele")
                if len(games) > args.limit:
                    print(f"   (Zeige erste {args.limit})")
            else:
                print("❌ Keine Charts-Spiele gefunden")
        else:
            print("❌ Charts-Datenbankfunktionen nicht verfügbar")
            
    except ImportError:
        print("❌ Price Tracker Module nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_charts_cleanup(args):
    """Führt Charts-Cleanup durch"""
    try:
        # UPDATED: Verwende konsolidierte price_tracker.py
        from price_tracker import create_price_tracker
        
        tracker = create_price_tracker()
        
        if not tracker.charts_enabled:
            print("❌ Charts-Funktionalität nicht verfügbar")
            return
        
        print(f"🧹 Starte Charts-Cleanup (>{args.days} Tage)...")
        
        if hasattr(tracker.charts_manager, 'cleanup_old_chart_games'):
            removed = tracker.charts_manager.cleanup_old_chart_games(args.days)
            
            if removed > 0:
                print(f"✅ {removed} alte Charts-Spiele entfernt")
            else:
                print("✅ Keine alten Charts-Spiele zum Entfernen gefunden")
        else:
            print("❌ Charts-Cleanup Funktion nicht verfügbar")
            
    except ImportError:
        print("❌ Price Tracker Module nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_charts_export(args):
    """Exportiert Charts-Daten"""
    try:
        # UPDATED: Verwende konsolidierte price_tracker.py
        from price_tracker import create_price_tracker
        
        tracker = create_price_tracker()
        
        if not tracker.charts_enabled:
            print("❌ Charts-Funktionalität nicht verfügbar")
            return
        
        print("📄 Starte Charts-Export...")
        
        output_file = args.output
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"exports/charts_export_{timestamp}.csv"
        
        if hasattr(tracker.charts_manager, 'export_charts_data_csv'):
            csv_file = tracker.charts_manager.export_charts_data_csv(output_file)
            
            if csv_file:
                print(f"✅ Charts-Export erstellt: {csv_file}")
            else:
                print("❌ Export fehlgeschlagen (keine Daten?)")
        else:
            print("❌ Charts-Export Funktion nicht verfügbar")
            
    except ImportError:
        print("❌ Price Tracker Module nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def cmd_setup_automation(args):
    """Richtet vollautomatisches Tracking ein"""
    try:
        # UPDATED: Verwende konsolidierte price_tracker.py
        from price_tracker import create_price_tracker, setup_full_automation
        
        tracker = create_price_tracker()
        
        print("🚀 Richte vollautomatisches Tracking ein...")
        
        success = setup_full_automation(
            tracker,
            normal_interval=args.normal_hours,
            charts_interval=args.charts_hours,
            charts_price_interval=args.charts_price_hours
        )
        
        if success:
            print("✅ Vollautomatisches Tracking erfolgreich eingerichtet!")
            print("\n📋 AKTIVE SCHEDULER:")
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
                    tracker.stop_scheduler()
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
                              help='Komma-getrennte Liste von Chart-Typen (most_played,top_releases,best_sellers,weekly_top_sellers)')
    update_parser.set_defaults(func=cmd_update_charts)
    
    # Update Charts Prices Command
    update_prices_parser = subparsers.add_parser('update-prices', help='Charts-Preise aktualisieren')
    update_prices_parser.add_argument('--chart-type',
                                     help='Spezifischen Chart-Typ aktualisieren')
    update_prices_parser.set_defaults(func=cmd_update_charts_prices)
    
    # Status Command
    status_parser = subparsers.add_parser('status', help='Charts-Status anzeigen')
    status_parser.set_defaults(func=cmd_charts_status)
    
    # Deals Command
    deals_parser = subparsers.add_parser('deals', help='Beste Charts-Deals anzeigen')
    deals_parser.add_argument('--limit', type=int, default=15,
                             help='Anzahl Deals (Standard: 15)')
    deals_parser.add_argument('--chart-type',
                             help='Nach Chart-Typ filtern')
    deals_parser.set_defaults(func=cmd_charts_deals)
    
    # Trending Command
    trending_parser = subparsers.add_parser('trending', help='Trending Price Drops anzeigen')
    trending_parser.add_argument('--hours', type=int, default=24,
                                help='Stunden zurückblicken (Standard: 24)')
    trending_parser.add_argument('--min-discount', type=int, default=20,
                                help='Mindestrabatt in Prozent (Standard: 20)')
    trending_parser.set_defaults(func=cmd_charts_trending)
    
    # List Command
    list_parser = subparsers.add_parser('list', help='Charts-Spiele auflisten')
    list_parser.add_argument('--chart-type',
                            help='Nach Chart-Typ filtern')
    list_parser.add_argument('--limit', type=int, default=100,
                            help='Anzahl Spiele (Standard: 100)')
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
