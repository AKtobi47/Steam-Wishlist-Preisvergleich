#!/usr/bin/env python3
"""
Enhanced Steam Price Tracker - Simplified Main Application
UPDATED: Nutzt Universal Background Scheduler für alle Background-Tasks
Vereinfachtes Interface da Scheduler-Komplexität in background_scheduler.py abstrahiert ist
"""

import sys
import time
from datetime import datetime
from pathlib import Path
import logging

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =====================================================================
# SIMPLIFIED UTILITY-FUNKTIONEN - Reduziert durch Universal Scheduler
# =====================================================================

def get_universal_scheduler_status(price_tracker):
    """Gibt Universal Background Scheduler Status zurück"""
    try:
        return price_tracker.get_enhanced_scheduler_status()
    except Exception as e:
        logger.debug(f"Scheduler-Status Fehler: {e}")
        return {
            'scheduler_type': 'Universal Background Scheduler',
            'total_active_schedulers': 0,
            'price_scheduler_status': None,
            'charts_scheduler_status': None
        }

def show_available_chart_types():
    """FIXED: Zeigt verfügbare Chart-Typen an"""
    try:
        from steam_charts_manager import SteamChartsManager
        chart_types = SteamChartsManager.get_available_chart_types()
        
        print("\n📊 VERFÜGBARE CHART-TYPEN:")
        print("-" * 30)
        for chart_type, description in chart_types.items():
            print(f"• {chart_type} - {description}")
        print()
        
        return list(chart_types.keys())
    except ImportError:
        print("❌ Charts-Funktionalität nicht verfügbar")
        return []
    except Exception as e:
        print(f"❌ Fehler beim Laden der Chart-Typen: {e}")
        return []

def show_enhanced_charts_statistics(price_tracker):
    """Zeigt erweiterte Charts-Statistiken"""
    if not price_tracker.charts_enabled:
        return
    
    try:
        if hasattr(price_tracker.db_manager, 'get_charts_statistics'):
            charts_stats = price_tracker.db_manager.get_charts_statistics()
            
            if charts_stats and charts_stats.get('total_active_charts_games', 0) > 0:
                print(f"\n📊 CHARTS-STATUS:")
                print(f"🎯 Aktive Charts-Spiele: {charts_stats.get('total_active_charts_games', 0)}")
                print(f"🎮 Einzigartige Apps in Charts: {charts_stats.get('unique_apps_in_charts', 0)}")
                print(f"📈 Charts-Preis-Snapshots: {charts_stats.get('total_charts_price_snapshots', 0):,}")
                
                # Pro Chart-Typ
                active_by_chart = charts_stats.get('active_games_by_chart', {})
                if active_by_chart:
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

def show_universal_scheduler_status(price_tracker):
    """Zeigt Universal Background Scheduler Status"""
    try:
        status = get_universal_scheduler_status(price_tracker)
        
        print(f"\n🚀 UNIVERSAL BACKGROUND SCHEDULER:")
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
        print(f"⚠️ Background Scheduler Status nicht verfügbar: {e}")

# =====================================================================
# NEUE FUNKTIONEN FÜR CHARTS-NAMEN-UPDATES
# =====================================================================

def update_charts_names_from_steam(price_tracker):
    """
    NEU: Aktualisiert Namen für Charts-Spiele von Steam API
    
    Args:
        price_tracker: SteamPriceTracker Instanz
    """
    print("\n🔤 CHARTS-NAMEN VON STEAM AKTUALISIEREN")
    print("=" * 45)
    
    if not price_tracker.charts_enabled:
        print("❌ Charts-Funktionalität nicht verfügbar")
        return
    
    # API Key prüfen
    api_key = None
    if hasattr(price_tracker, 'api_key'):
        api_key = price_tracker.api_key
    
    if not api_key:
        try:
            from steam_wishlist_manager import load_api_key_from_env
            api_key = load_api_key_from_env()
        except ImportError:
            pass
    
    if not api_key:
        print("❌ Kein Steam API Key verfügbar")
        print("💡 Stelle sicher dass STEAM_API_KEY in .env konfiguriert ist")
        return
    
    # Charts-Spiele mit generischen Namen finden
    try:
        if hasattr(price_tracker.db_manager, 'get_active_chart_games'):
            all_chart_games = price_tracker.db_manager.get_active_chart_games()
            
            # Spiele mit generischen Namen filtern
            generic_names = []
            for game in all_chart_games:
                name = game.get('name', '')
                if (name.startswith('Game ') or 
                    name.startswith('Unknown Game') or 
                    name.startswith('New Release') or
                    name == '' or 
                    name is None):
                    generic_names.append(game)
            
            if not generic_names:
                print("✅ Alle Charts-Spiele haben bereits korrekte Namen!")
                return
            
            print(f"🔍 {len(generic_names)} Charts-Spiele mit generischen Namen gefunden:")
            for game in generic_names[:10]:  # Zeige erste 10
                print(f"   • {game['name']} (ID: {game['steam_app_id']}, Chart: {game['chart_type']})")
            
            if len(generic_names) > 10:
                print(f"   ... und {len(generic_names) - 10} weitere")
            
            # Bestätigung
            confirm = input(f"\nNamen für {len(generic_names)} Charts-Spiele aktualisieren? (j/n): ").lower().strip()
            
            if confirm in ['j', 'ja', 'y', 'yes']:
                # App IDs extrahieren
                app_ids = [game['steam_app_id'] for game in generic_names]
                
                print(f"🔄 Aktualisiere Namen für {len(app_ids)} Charts-Spiele...")
                
                # Verwende die bestehende Namen-Update Funktion
                result = price_tracker.update_app_names_from_steam(app_ids, api_key)
                
                if result.get('success'):
                    print(f"✅ Charts-Namen-Update abgeschlossen:")
                    print(f"   📊 {result['updated']}/{result['total']} erfolgreich ({result.get('success_rate', 0):.1f}%)")
                    print(f"   ❌ {result['failed']} fehlgeschlagen")
                    
                    # Auch Charts-spezifische Namen-Updates in Charts-Tabelle
                    if hasattr(price_tracker.db_manager, 'update_chart_game'):
                        print("🔄 Aktualisiere auch Charts-Tabelle...")
                        charts_updated = 0
                        
                        for game in generic_names:
                            if game['steam_app_id'] in [aid for aid in app_ids if result.get('updated', 0) > 0]:
                                # Hole aktuellen Namen aus tracked_apps
                                tracked_apps = price_tracker.get_tracked_apps()
                                updated_app = next((app for app in tracked_apps if app['steam_app_id'] == game['steam_app_id']), None)
                                
                                if updated_app and updated_app['name'] != game['name']:
                                    try:
                                        if price_tracker.db_manager.update_chart_game(
                                            game['steam_app_id'],
                                            game['chart_type'],
                                            game.get('current_rank', 0),
                                            updated_app['name']
                                        ):
                                            charts_updated += 1
                                    except:
                                        pass
                        
                        if charts_updated > 0:
                            print(f"   📊 {charts_updated} Charts-Einträge aktualisiert")
                else:
                    print(f"❌ Charts-Namen-Update fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")
            else:
                print("⏹️ Namen-Update abgebrochen")
        else:
            print("❌ Charts-Datenbank-Funktionen nicht verfügbar")
            
    except Exception as e:
        print(f"❌ Fehler beim Charts-Namen-Update: {e}")

def show_charts_name_candidates(price_tracker):
    """
    NEU: Zeigt Charts-Spiele mit generischen Namen
    
    Args:
        price_tracker: SteamPriceTracker Instanz
    """
    print("\n🔍 CHARTS-SPIELE MIT GENERISCHEN NAMEN")
    print("=" * 45)
    
    if not price_tracker.charts_enabled:
        print("❌ Charts-Funktionalität nicht verfügbar")
        return
    
    try:
        if hasattr(price_tracker.db_manager, 'get_active_chart_games'):
            all_chart_games = price_tracker.db_manager.get_active_chart_games()
            
            # Spiele mit generischen Namen filtern
            generic_names = []
            for game in all_chart_games:
                name = game.get('name', '')
                if (name.startswith('Game ') or 
                    name.startswith('Unknown Game') or 
                    name.startswith('New Release') or
                    name == '' or 
                    name is None):
                    generic_names.append(game)
            
            if not generic_names:
                print("✅ Alle Charts-Spiele haben korrekte Namen!")
                return
            
            # Gruppiere nach Chart-Typ
            by_chart_type = {}
            for game in generic_names:
                chart_type = game.get('chart_type', 'unknown')
                if chart_type not in by_chart_type:
                    by_chart_type[chart_type] = []
                by_chart_type[chart_type].append(game)
            
            print(f"🔍 {len(generic_names)} Charts-Spiele benötigen Namen-Updates:\n")
            
            for chart_type, games in by_chart_type.items():
                print(f"📊 {chart_type.upper()} ({len(games)} Spiele):")
                
                for game in games[:5]:  # Zeige erste 5 pro Chart-Typ
                    rank = game.get('current_rank', 0)
                    rank_display = f"#{rank}" if rank > 0 else "-"
                    first_seen = game.get('first_seen', '')[:10]
                    
                    print(f"   {rank_display:>4} {game['name']}")
                    print(f"        🆔 {game['steam_app_id']} | 📅 {first_seen}")
                
                if len(games) > 5:
                    print(f"        ... und {len(games) - 5} weitere")
                print()
            
            print("💡 Verwende 'Charts-Namen von Steam aktualisieren' um die Namen zu korrigieren")
        else:
            print("❌ Charts-Datenbank-Funktionen nicht verfügbar")
            
    except Exception as e:
        print(f"❌ Fehler beim Anzeigen der Charts-Namen-Kandidaten: {e}")

# =====================================================================
# MAIN APPLICATION - SIMPLIFIED
# =====================================================================

def main():
    print("🚀 ENHANCED STEAM PRICE TRACKER v2.1")
    print("=" * 50)
    print("Vollständiges Preis-Tracking mit Universal Background Scheduler")
    print("Alle Background-Tasks laufen in separaten Terminals")
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
        
        # Price Tracker mit Charts-Integration und Universal Background Scheduler
        price_tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        charts_enabled = price_tracker.charts_enabled
        
        print(f"✅ Price Tracker mit Universal Background Scheduler initialisiert")
        if charts_enabled:
            print(f"📊 Charts-Integration: VERFÜGBAR")
        else:
            print(f"📊 Charts-Integration: NICHT VERFÜGBAR (kein API Key)")
        
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
            # Erweiterte Statistiken anzeigen
            try:
                stats = price_tracker.get_statistics()
                
                # Standard Statistiken
                print(f"\n📊 AKTUELLER STATUS:")
                print(f"📚 Getrackte Apps: {stats['tracked_apps']}")
                total_snapshots = stats.get('total_snapshots', 0)
                print(f"📈 Gesamt Preis-Snapshots: {total_snapshots:,}")
                print(f"🏪 Stores: {', '.join(stats['stores_tracked'])}")
                
                # Charts-Statistiken (falls verfügbar)
                if charts_enabled:
                    show_enhanced_charts_statistics(price_tracker)
                
                # Universal Background Scheduler Status
                show_universal_scheduler_status(price_tracker)
                
                newest_snapshot = stats.get('newest_snapshot')
                if newest_snapshot:
                    print(f"🕐 Letzte Preisabfrage: {newest_snapshot[:19]}")
                
            except Exception as e:
                print(f"⚠️ Fehler beim Laden der Statistiken: {e}")
                print("\n📊 AKTUELLER STATUS:")
                print("📚 Getrackte Apps: ❓")
                print("📈 Gesamt Preis-Snapshots: ❓")
            
            # VEREINFACHTE MENÜ-OPTIONEN - Universal Scheduler abstrahiert Komplexität
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
            print("7. Background-Tracking verwalten")  # VEREINFACHT
            print("8. Getrackte Apps verwalten")
            print("9. Apps entfernen")
            
            print("\n📄 EXPORT & DATEN:")
            print("10. CSV-Export erstellen")
            print("11. Detaillierte Statistiken")
            
            # Namen-Update Optionen
            print("\n🔤 NAMEN-UPDATES:")
            print("12. App-Namen von Steam aktualisieren")
            print("13. Apps mit generischen Namen anzeigen")
            
            # Charts-spezifische Optionen (falls verfügbar)
            if charts_enabled:
                print("\n📊 CHARTS-FUNKTIONEN:")
                print("14. Charts-Tracking verwalten")  # VEREINFACHT
                print("15. Charts sofort aktualisieren")
                print("16. Charts-Preise aktualisieren")
                print("17. Beste Charts-Deals")
                print("18. Charts-Namen von Steam aktualisieren")  # NEU
                print("19. Charts-Spiele mit generischen Namen")    # NEU
                print("20. Charts-Spiele anzeigen")
                print("21. Vollautomatik einrichten")  # VEREINFACHT
                print("22. Beenden")
                max_option = 22
            else:
                print("14. Beenden")
                max_option = 14
            
            # User Input
            choice = input(f"\nWählen Sie eine Option (1-{max_option}): ").strip()
            
            # ========================
            # STANDARD-OPTIONEN (unverändert)
            # ========================
            
            if choice == "1":
                # App manuell hinzufügen
                print("\n📱 APP MANUELL HINZUFÜGEN")
                print("=" * 30)
                
                steam_app_id = input("Steam App ID: ").strip()
                if not steam_app_id:
                    print("❌ Ungültige App ID")
                    continue
                
                app_name = input("App Name (optional): ").strip()
                if not app_name:
                    app_name = f"Game {steam_app_id}"
                
                if price_tracker.add_app_to_tracking(steam_app_id, app_name):
                    print(f"✅ App '{app_name}' hinzugefügt")
                    
                    # Sofortiges Namen-Update anbieten falls API Key verfügbar
                    if api_key and app_name.startswith('Game '):
                        update_name = input("Namen von Steam API abrufen? (j/n): ").lower().strip()
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
                    print("💡 Konfiguriere STEAM_API_KEY in .env")
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
                    print(f"   📊 {result['imported'] + result['skipped_existing']}/{result['total_items']} Apps verarbeitet")
                else:
                    print(f"❌ Wishlist-Import fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")
            
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
                    print("💡 Führe zuerst Preisabfragen durch")
            
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
                    
                    for snapshot in history[:10]:  # Zeige nur erste 10
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
                                status = f"€{price:.2f}"
                                if discount > 0:
                                    status += f" (-{discount}%)"
                                print(f"   {store.title():15}: {status}")
                        print()
                    
                    if len(history) > 10:
                        print(f"... und {len(history) - 10} weitere Einträge")
                else:
                    print("❌ Kein Preisverlauf gefunden")
            
            elif choice == "6":
                # Preise manuell aktualisieren
                print("\n🔄 PREISE MANUELL AKTUALISIEREN")
                print("=" * 35)
                
                tracked_apps = price_tracker.get_tracked_apps()
                
                if not tracked_apps:
                    print("❌ Keine Apps im Tracking")
                    continue
                
                print(f"📊 {len(tracked_apps)} Apps getrackt")
                
                # Optionen anbieten
                print("1. Alle Apps aktualisieren")
                print("2. Nur veraltete Apps aktualisieren")
                print("3. Spezifische App aktualisieren")
                
                update_choice = input("Wählen Sie eine Option (1-3): ").strip()
                
                if update_choice == "1":
                    # Alle Apps
                    app_ids = [app['steam_app_id'] for app in tracked_apps]
                    print(f"🔄 Aktualisiere alle {len(app_ids)} Apps...")
                    
                    result = price_tracker.track_app_prices(app_ids)
                    print(f"✅ Update abgeschlossen: {result['successful']}/{result['processed']} Apps erfolgreich")
                
                elif update_choice == "2":
                    # Nur veraltete Apps
                    hours = input("Apps älter als wie viele Stunden? (Standard: 6): ").strip()
                    try:
                        hours = int(hours) if hours else 6
                    except ValueError:
                        hours = 6
                    
                    pending_apps = price_tracker.get_apps_needing_price_update(hours)
                    
                    if pending_apps:
                        app_ids = [app['steam_app_id'] for app in pending_apps]
                        print(f"🔄 Aktualisiere {len(app_ids)} veraltete Apps...")
                        
                        result = price_tracker.track_app_prices(app_ids)
                        print(f"✅ Update abgeschlossen: {result['successful']}/{result['processed']} Apps erfolgreich")
                    else:
                        print("✅ Alle Apps sind aktuell!")
                
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
                # VEREINFACHT: Background-Tracking verwalten
                print("\n🚀 BACKGROUND-TRACKING VERWALTEN")
                print("=" * 40)
                
                status = get_universal_scheduler_status(price_tracker)
                total_active = status.get('total_active_schedulers', 0)
                
                if total_active > 0:
                    print(f"🔄 Background-Tracking läuft: {total_active} aktive Scheduler")
                    show_universal_scheduler_status(price_tracker)
                    
                    stop = input("\nAlle Background-Scheduler stoppen? (j/n): ").lower().strip()
                    if stop in ['j', 'ja', 'y', 'yes']:
                        if price_tracker.stop_background_scheduler():
                            print("⏹️ Price Tracker Background-Scheduler gestoppt")
                        
                        if charts_enabled and price_tracker.disable_charts_tracking():
                            print("⏹️ Charts Background-Scheduler gestoppt")
                else:
                    print("⏸️ Background-Tracking ist inaktiv")
                    start = input("Background-Tracking starten? (j/n): ").lower().strip()
                    
                    if start in ['j', 'ja', 'y', 'yes']:
                        # Einfache Konfiguration
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
                            print(f"✅ Background-Tracking gestartet!")
                            print(f"   💰 Preise: alle {price_hours}h")
                            print(f"   🔤 Namen: alle {name_minutes}min")
                            print("   💡 Läuft in separaten Terminals!")
            
            elif choice == "8":
                # Getrackte Apps verwalten
                print("\n📋 GETRACKTE APPS VERWALTEN")
                print("=" * 30)
                
                tracked_apps = price_tracker.get_tracked_apps()
                
                if not tracked_apps:
                    print("❌ Keine Apps im Tracking")
                    continue
                
                print(f"📊 {len(tracked_apps)} Apps getrackt:")
                print()
                
                for i, app in enumerate(tracked_apps[:20], 1):  # Zeige nur erste 20
                    last_update = app.get('last_price_update', 'Nie')
                    if last_update and last_update != 'Nie':
                        last_update = last_update[:19]
                    
                    print(f"{i:3d}. {app['name'][:40]:<40} (ID: {app['steam_app_id']})")
                    print(f"     📅 Hinzugefügt: {app['added_at'][:10]} | Letztes Update: {last_update}")
                
                if len(tracked_apps) > 20:
                    print(f"\n... und {len(tracked_apps) - 20} weitere Apps")
                
                print(f"\n💡 Verwende Option 9 um Apps zu entfernen")
            
            elif choice == "9":
                # Apps entfernen
                print("\n🗑️ APPS ENTFERNEN")
                print("=" * 15)
                
                steam_app_id = input("Steam App ID zum Entfernen: ").strip()
                if not steam_app_id:
                    print("❌ Ungültige App ID")
                    continue
                
                # App-Details zeigen
                tracked_apps = price_tracker.get_tracked_apps()
                app_to_remove = next((app for app in tracked_apps if app['steam_app_id'] == steam_app_id), None)
                
                if not app_to_remove:
                    print(f"❌ App {steam_app_id} nicht im Tracking gefunden")
                    continue
                
                print(f"🎮 App: {app_to_remove['name']}")
                print(f"🆔 ID: {steam_app_id}")
                print(f"📅 Hinzugefügt: {app_to_remove['added_at'][:19]}")
                
                confirm = input("\nApp wirklich entfernen? (j/n): ").lower().strip()
                if confirm in ['j', 'ja', 'y', 'yes']:
                    if price_tracker.remove_app_from_tracking(steam_app_id):
                        print(f"✅ App '{app_to_remove['name']}' entfernt")
                    else:
                        print("❌ Fehler beim Entfernen der App")
                else:
                    print("⏹️ Entfernen abgebrochen")
            
            elif choice == "10":
                # CSV-Export erstellen
                print("\n📄 CSV-EXPORT ERSTELLEN")
                print("=" * 25)
                
                steam_app_id = input("Steam App ID (oder Enter für alle): ").strip()
                
                if steam_app_id:
                    # Einzelne App exportieren
                    output_file = input("Ausgabedatei (optional): ").strip()
                    csv_file = price_tracker.export_price_history_csv(steam_app_id, output_file)
                    
                    if csv_file:
                        print(f"✅ CSV-Export erstellt: {csv_file}")
                    else:
                        print("❌ Export fehlgeschlagen")
                else:
                    # Alle Apps exportieren
                    print("🔄 Exportiere alle Apps...")
                    tracked_apps = price_tracker.get_tracked_apps()
                    
                    if not tracked_apps:
                        print("❌ Keine Apps zum Exportieren")
                        continue
                    
                    successful = 0
                    for app in tracked_apps:
                        try:
                            csv_file = price_tracker.export_price_history_csv(app['steam_app_id'])
                            if csv_file:
                                successful += 1
                        except:
                            pass
                    
                    print(f"✅ {successful}/{len(tracked_apps)} Apps exportiert")
            
            elif choice == "11":
                # Detaillierte Statistiken
                print("\n📊 DETAILLIERTE STATISTIKEN")
                print("=" * 30)
                
                stats = price_tracker.get_statistics()
                
                print(f"📚 Getrackte Apps: {stats['tracked_apps']}")
                print(f"📈 Gesamt Snapshots: {stats['total_snapshots']:,}")
                print(f"🏪 Stores mit Daten: {len(stats['stores_tracked'])}")
                print(f"   {', '.join(stats['stores_tracked'])}")
                
                if stats.get('oldest_snapshot'):
                    print(f"📅 Ältester Snapshot: {stats['oldest_snapshot'][:19]}")
                if stats.get('newest_snapshot'):
                    print(f"📅 Neuester Snapshot: {stats['newest_snapshot'][:19]}")
                
                # Namen-Update Statistiken
                if 'name_update_stats' in stats:
                    name_stats = stats['name_update_stats']
                    print(f"\n🔤 NAMEN-UPDATE STATISTIKEN:")
                    print(f"📝 Apps mit generischen Namen: {name_stats['apps_with_generic_names']}")
                    print(f"❓ Apps ohne Namen-Update: {name_stats['apps_never_updated']}")
                    print(f"🔄 Gesamt Namen-Updates: {name_stats['total_name_updates']}")
                    print(f"📊 Namen-Updates (24h): {name_stats['updates_last_24h']}")
                    print(f"❌ Fehlgeschlagene Updates: {name_stats['failed_updates']}")
                
                # Apps die Updates benötigen
                pending_apps = price_tracker.get_apps_needing_price_update(24)
                print(f"\n⏰ Apps die Preis-Updates benötigen (>24h): {len(pending_apps)}")
                
                # Charts-Statistiken (falls verfügbar)
                if charts_enabled:
                    show_enhanced_charts_statistics(price_tracker)
                
                # Universal Background Scheduler Status
                show_universal_scheduler_status(price_tracker)
            
            # ========================
            # NAMEN-UPDATE OPTIONEN
            # ========================
            
            elif choice == "12":
                # App-Namen von Steam aktualisieren
                print("\n🔤 APP-NAMEN VON STEAM AKTUALISIEREN")
                print("=" * 40)
                
                if not api_key:
                    print("❌ Steam API Key erforderlich für Namen-Updates")
                    print("💡 Konfiguriere STEAM_API_KEY in .env")
                    continue
                
                print("Optionen:")
                print("1. Alle Apps mit generischen Namen aktualisieren")
                print("2. Spezifische App-ID(s) aktualisieren")
                print("3. Alle getrackte Apps aktualisieren")
                
                name_choice = input("Wählen Sie eine Option (1-3): ").strip()
                
                if name_choice == "1":
                    # Apps mit generischen Namen
                    candidates = price_tracker.get_name_update_candidates()
                    
                    if not candidates:
                        print("✅ Alle Apps haben bereits korrekte Namen!")
                        continue
                    
                    print(f"🔍 {len(candidates)} Apps mit generischen Namen gefunden")
                    for candidate in candidates[:10]:
                        print(f"   • {candidate['name']} (ID: {candidate['steam_app_id']})")
                    
                    if len(candidates) > 10:
                        print(f"   ... und {len(candidates) - 10} weitere")
                    
                    confirm = input(f"\nNamen für {len(candidates)} Apps aktualisieren? (j/n): ").lower().strip()
                    if confirm in ['j', 'ja', 'y', 'yes']:
                        result = price_tracker.update_names_for_apps_with_generic_names(api_key)
                        
                        if result.get('success'):
                            print(f"✅ Namen-Update abgeschlossen:")
                            print(f"   📊 {result['updated']}/{result['total']} erfolgreich ({result.get('success_rate', 0):.1f}%)")
                            print(f"   ❌ {result['failed']} fehlgeschlagen")
                        else:
                            print(f"❌ Namen-Update fehlgeschlagen: {result.get('error')}")
                
                elif name_choice == "2":
                    # Spezifische App-IDs
                    app_ids_input = input("App-IDs (komma-getrennt): ").strip()
                    if app_ids_input:
                        app_ids = [app_id.strip() for app_id in app_ids_input.split(',') if app_id.strip()]
                        
                        print(f"🔄 Aktualisiere Namen für {len(app_ids)} Apps...")
                        result = price_tracker.update_app_names_from_steam(app_ids, api_key)
                        
                        if result.get('success'):
                            print(f"✅ Namen-Update abgeschlossen:")
                            print(f"   📊 {result['updated']}/{result['total']} erfolgreich")
                            print(f"   ❌ {result['failed']} fehlgeschlagen")
                        else:
                            print(f"❌ Namen-Update fehlgeschlagen: {result.get('error')}")
                
                elif name_choice == "3":
                    # Alle getrackte Apps
                    tracked_apps = price_tracker.get_tracked_apps()
                    
                    if not tracked_apps:
                        print("❌ Keine Apps zum Aktualisieren")
                        continue
                    
                    print(f"⚠️ Dies wird Namen für ALLE {len(tracked_apps)} Apps aktualisieren")
                    confirm = input("Fortfahren? (j/n): ").lower().strip()
                    
                    if confirm in ['j', 'ja', 'y', 'yes']:
                        app_ids = [app['steam_app_id'] for app in tracked_apps]
                        
                        print(f"🔄 Aktualisiere Namen für alle {len(app_ids)} Apps...")
                        result = price_tracker.update_app_names_from_steam(app_ids, api_key)
                        
                        if result.get('success'):
                            print(f"✅ Namen-Update abgeschlossen:")
                            print(f"   📊 {result['updated']}/{result['total']} erfolgreich ({result.get('success_rate', 0):.1f}%)")
                            print(f"   ❌ {result['failed']} fehlgeschlagen")
                        else:
                            print(f"❌ Namen-Update fehlgeschlagen: {result.get('error')}")
            
            elif choice == "13":
                # Apps mit generischen Namen anzeigen
                print("\n🔍 APPS MIT GENERISCHEN NAMEN")
                print("=" * 35)
                
                candidates = price_tracker.get_name_update_candidates()
                
                if not candidates:
                    print("✅ Alle Apps haben korrekte Namen!")
                    continue
                
                print(f"🔍 {len(candidates)} Apps mit generischen Namen:")
                print()
                
                for i, app in enumerate(candidates, 1):
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
                
                print(f"\n💡 Verwende Option 12 um Namen von Steam zu aktualisieren")
            
            # ========================
            # CHARTS-SPEZIFISCHE OPTIONEN - VEREINFACHT
            # ========================
            
            elif charts_enabled and choice == "14":
                # VEREINFACHT: Charts-Tracking verwalten
                print("\n🎯 CHARTS-TRACKING VERWALTEN")
                print("=" * 35)
                
                status = get_universal_scheduler_status(price_tracker)
                charts_status = status.get('charts_scheduler_status')
                
                charts_running = charts_status and any(
                    s.get('running', False) 
                    for s in charts_status.get('schedulers', {}).values()
                )
                
                if charts_running:
                    print("🔄 Charts-Tracking läuft bereits")
                    
                    # Zeige aktive Charts-Scheduler
                    for scheduler_name, scheduler_info in charts_status.get('schedulers', {}).items():
                        if scheduler_info.get('running'):
                            interval = scheduler_info.get('interval_minutes', 0)
                            interval_str = f"{interval // 60}h" if interval >= 60 else f"{interval}min"
                            print(f"   ✅ {scheduler_name}: alle {interval_str}")
                    
                    stop = input("\nCharts-Tracking stoppen? (j/n): ").lower().strip()
                    if stop in ['j', 'ja', 'y', 'yes']:
                        if price_tracker.disable_charts_tracking():
                            print("⏹️ Charts-Tracking gestoppt")
                else:
                    print("⏸️ Charts-Tracking ist inaktiv")
                    start = input("Charts-Tracking starten? (j/n): ").lower().strip()
                    
                    if start in ['j', 'ja', 'y', 'yes']:
                        charts_hours = input("Charts-Update Intervall in Stunden (Standard: 6): ").strip()
                        price_hours = input("Charts-Preis-Update Intervall in Stunden (Standard: 4): ").strip()
                        
                        try:
                            charts_hours = int(charts_hours) if charts_hours else 6
                            price_hours = int(price_hours) if price_hours else 4
                        except ValueError:
                            charts_hours, price_hours = 6, 4
                        
                        if price_tracker.enable_charts_tracking(
                            charts_update_hours=charts_hours,
                            price_update_hours=price_hours,
                            cleanup_hours=24
                        ):
                            print(f"✅ Charts-Tracking gestartet!")
                            print(f"   📊 Charts-Updates: alle {charts_hours}h")
                            print(f"   💰 Preis-Updates: alle {price_hours}h")
                            print(f"   🧹 Cleanup: alle 24h")
                            print("   💡 Läuft in separaten Terminals!")
            
            elif charts_enabled and choice == "15":
                # Charts sofort aktualisieren
                print("\n📊 CHARTS SOFORT AKTUALISIEREN")
                print("=" * 35)
                
                available_types = show_available_chart_types()
                
                chart_types_input = input("Chart-Typen (komma-getrennt) oder Enter für alle: ").strip()
                
                if chart_types_input:
                    chart_types = [ct.strip() for ct in chart_types_input.split(',') if ct.strip() in available_types]
                    if not chart_types:
                        print("❌ Ungültige Chart-Typen")
                        continue
                else:
                    chart_types = None
                
                print("🔄 Starte Charts-Update...")
                result = price_tracker.update_charts_now(chart_types)
                
                if result.get('success', True):
                    print("✅ Charts-Update abgeschlossen:")
                    print(f"   📊 {result.get('total_games_found', 0)} Spiele gefunden")
                    print(f"   ➕ {result.get('new_games_added', 0)} neue Spiele")
                    print(f"   🔄 {result.get('existing_games_updated', 0)} aktualisiert")
                    
                    if result.get('errors'):
                        print(f"   ⚠️ {len(result['errors'])} Fehler aufgetreten")
                else:
                    print(f"❌ Charts-Update fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")
            
            elif charts_enabled and choice == "16":
                # Charts-Preise aktualisieren
                print("\n💰 CHARTS-PREISE AKTUALISIEREN")
                print("=" * 35)
                
                chart_type = input("Chart-Typ (oder Enter für alle): ").strip()
                if chart_type and chart_type not in show_available_chart_types():
                    print("❌ Ungültiger Chart-Typ")
                    continue
                
                print("🔄 Aktualisiere Charts-Preise...")
                result = price_tracker.update_charts_prices_now(chart_type)
                
                if result.get('success', True):
                    print("✅ Charts-Preisupdate abgeschlossen:")
                    print(f"   📊 {result.get('total_games', 0)} Spiele verarbeitet")
                    print(f"   💰 {result.get('successful', 0)} erfolgreich aktualisiert")
                    
                    if result.get('failed', 0) > 0:
                        print(f"   ❌ {result['failed']} fehlgeschlagen")
                else:
                    print(f"❌ Charts-Preisupdate fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")
            
            elif charts_enabled and choice == "17":
                # Beste Charts-Deals
                print("\n🏆 BESTE CHARTS-DEALS")
                print("=" * 25)
                
                available_types = show_available_chart_types()
                
                if available_types:
                    print("💡 Verfügbare Filter:")
                    for i, chart_type in enumerate(available_types, 1):
                        print(f"   {i}. {chart_type}")
                    print(f"   {len(available_types) + 1}. alle (kein Filter)")
                
                chart_type_filter = input("Chart-Typ eingeben oder Enter für alle: ").strip()
                
                if chart_type_filter and chart_type_filter not in available_types:
                    print(f"⚠️ Unbekannter Chart-Typ '{chart_type_filter}' - verwende alle Charts")
                    chart_type_filter = None
                elif not chart_type_filter:
                    chart_type_filter = None
                
                deals = price_tracker.get_best_charts_deals(limit=15, chart_type=chart_type_filter)
                
                if deals:
                    if chart_type_filter:
                        print(f"🏆 Top {len(deals)} Deals für {chart_type_filter.upper()}:")
                    else:
                        print(f"🏆 Top {len(deals)} Charts-Deals (alle Typen):")
                    print()
                    
                    for i, deal in enumerate(deals, 1):
                        rank_info = f"#{deal.get('current_rank', '?')}" if deal.get('current_rank') else ""
                        chart_info = f"[{deal.get('chart_type', 'Unknown')}]" if not chart_type_filter else ""
                        
                        print(f"{i:2d}. {deal['game_title'][:35]:<35} {rank_info} {chart_info}")
                        print(f"    💰 €{deal['best_price']:.2f} (-{deal['discount_percent']}%) bei {deal['best_store']}")
                        print(f"    🆔 App ID: {deal['steam_app_id']}")
                        print()
                else:
                    print("❌ Keine Charts-Deals gefunden")
                    print("💡 Führe zuerst Charts-Updates und Preisabfragen durch")
            
            elif charts_enabled and choice == "18":
                # NEU: Charts-Namen von Steam aktualisieren
                update_charts_names_from_steam(price_tracker)
            
            elif charts_enabled and choice == "19":
                # NEU: Charts-Spiele mit generischen Namen
                show_charts_name_candidates(price_tracker)
            
            elif charts_enabled and choice == "20":
                # Charts-Spiele anzeigen
                print("\n📋 CHARTS-SPIELE ANZEIGEN")
                print("=" * 30)
                
                available_types = show_available_chart_types()
                
                if available_types:
                    print("💡 Verfügbare Filter:")
                    for i, chart_type in enumerate(available_types, 1):
                        print(f"   {i}. {chart_type}")
                    print(f"   {len(available_types) + 1}. alle (kein Filter)")
                
                chart_type_filter = input("Chart-Typ eingeben oder Enter für alle: ").strip()
                
                if chart_type_filter and chart_type_filter not in available_types:
                    print(f"⚠️ Unbekannter Chart-Typ '{chart_type_filter}' - verwende alle Charts")
                    chart_type_filter = None
                elif not chart_type_filter:
                    chart_type_filter = None
                
                if hasattr(price_tracker.db_manager, 'get_active_chart_games'):
                    active_games = price_tracker.db_manager.get_active_chart_games(chart_type_filter)
                    
                    if active_games:
                        if chart_type_filter:
                            print(f"📊 {chart_type_filter.upper()} SPIELE ({len(active_games)}):")
                        else:
                            print(f"📊 ALLE CHARTS-SPIELE ({len(active_games)}):")
                        print()
                        
                        current_chart = None
                        for i, game in enumerate(active_games[:50], 1):  # Limitiere auf 50
                            # Chart-Typ Header
                            if game.get('chart_type') != current_chart and not chart_type_filter:
                                current_chart = game.get('chart_type')
                                print(f"\n📈 {current_chart.upper()}")
                                print("-" * 30)
                            
                            rank = game.get('current_rank', 0)
                            rank_display = f"#{rank:3d}" if rank > 0 else "   -"
                            
                            first_seen = game.get('first_seen', '')[:10]
                            last_seen = game.get('last_seen', '')[:10]
                            
                            print(f"{rank_display} {game['name'][:40]:<40}")
                            print(f"     🆔 {game['steam_app_id']} | 📅 {first_seen} - {last_seen}")
                        
                        if len(active_games) > 50:
                            print(f"\n... und {len(active_games) - 50} weitere Spiele")
                            print("💡 Verwende Chart-Typ Filter um spezifische Listen zu sehen")
                    else:
                        print("❌ Keine Charts-Spiele gefunden")
                        if chart_type_filter:
                            print(f"💡 Für Chart-Typ '{chart_type_filter}' keine Spiele vorhanden")
                        print("💡 Führe zuerst ein Charts-Update durch")
                else:
                    print("❌ Charts-Spiele Funktion nicht verfügbar")
            
            elif charts_enabled and choice == "21":
                # VEREINFACHT: Vollautomatik einrichten
                print("\n🚀 VOLLAUTOMATIK EINRICHTEN")
                print("=" * 35)
                
                print("Diese Funktion richtet vollautomatisches Tracking ein für:")
                print("• Standard Apps (Wishlist, manuell hinzugefügte)")
                print("• Steam Charts (automatisch erkannte beliebte Spiele)")
                print("• Automatische Preisabfragen für beide Kategorien")
                print("• Automatisches Cleanup alter Charts-Spiele")
                print("• Automatische Namen-Updates bei Downtime")
                print("• ALLE Tasks laufen in separaten Terminals!")
                print()
                
                confirm = input("Vollautomatik einrichten? (j/n): ").lower().strip()
                if confirm in ['j', 'ja', 'y', 'yes']:
                    print("\n⚙️ KONFIGURATION:")
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
                    
                    # VEREINFACHT: Setup mit Universal Background Scheduler
                    try:
                        from price_tracker import setup_full_automation
                        
                        if setup_full_automation(
                            price_tracker,
                            normal_interval=normal_hours,
                            charts_interval=charts_hours,
                            charts_price_interval=charts_price_hours,
                            name_interval=name_minutes
                        ):
                            print("\n✅ VOLLAUTOMATIK ERFOLGREICH EINGERICHTET!")
                            print("\n📋 AKTIVE AUTOMATION:")
                            print(f"   💰 Standard-Preise: alle {normal_hours}h")
                            print(f"   📊 Charts-Updates: alle {charts_hours}h")
                            print(f"   💰 Charts-Preise: alle {charts_price_hours}h")
                            print(f"   🔤 Namen-Updates: alle {name_minutes}min")
                            print(f"   🧹 Charts-Cleanup: alle 24h")
                            print("\n💡 ALLE TASKS LAUFEN IN SEPARATEN TERMINALS!")
                            print("💡 Überprüfe die Terminal-Fenster für Live-Status!")
                        else:
                            print("❌ Fehler beim Einrichten der Vollautomatik")
                            
                    except Exception as e:
                        print(f"❌ Fehler beim Einrichten der Vollautomatik: {e}")
            
            # Beenden
            elif (not charts_enabled and choice == "14") or (charts_enabled and choice == "22"):
                print("\n👋 BEENDEN")
                print("=" * 10)
                
                # Alle Background-Scheduler stoppen
                status = get_universal_scheduler_status(price_tracker)
                total_active = status.get('total_active_schedulers', 0)
                
                if total_active > 0:
                    print(f"⏹️ Stoppe {total_active} aktive Background-Scheduler...")
                    
                    # Price Tracker Scheduler stoppen
                    price_tracker.stop_background_scheduler()
                    
                    # Charts Scheduler stoppen (falls aktiv)
                    if charts_enabled:
                        price_tracker.disable_charts_tracking()
                
                # Scheduler-Ressourcen aufräumen
                try:
                    price_tracker.cleanup_scheduler_resources()
                except:
                    pass
                
                print("💾 Datenbankverbindungen werden automatisch geschlossen...")
                print("✅ Enhanced Steam Price Tracker beendet. Auf Wiedersehen!")
                break
            
            else:
                print("❌ Ungültige Auswahl")
                
        except KeyboardInterrupt:
            print("\n⏹️ Abgebrochen durch Benutzer")
        except Exception as e:
            print(f"❌ Unerwarteter Fehler: {e}")
            logger.exception("Unerwarteter Fehler in main()")

if __name__ == "__main__":
    main()
