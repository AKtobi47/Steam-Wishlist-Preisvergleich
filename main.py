"""
Enhanced Steam Price Tracker - Hauptanwendung mit Charts Integration
CLI mit ALLEN ursprünglichen Funktionen plus Charts-Features
UPDATED: Verwendet konsolidierte price_tracker.py mit integrierter Charts-Funktionalität
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_api_key_from_env(env_file: str = ".env") -> str:
    """Lädt Steam API Key aus .env-Datei"""
    env_path = Path(env_file)
    
    if not env_path.exists():
        return None
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key.strip() == 'STEAM_API_KEY':
                        api_key = value.strip().strip('"').strip("'")
                        if api_key and api_key != 'your_steam_api_key_here':
                            return api_key
        return None
    except Exception as e:
        logger.error(f"❌ Fehler beim Lesen der .env-Datei: {e}")
        return None

def create_env_template() -> bool:
    """Erstellt .env Template"""
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env-Datei bereits vorhanden")
        return False
    
    try:
        template_content = """# Steam Price Tracker Configuration
# Hole deinen Steam API Key von: https://steamcommunity.com/dev/apikey

STEAM_API_KEY=your_steam_api_key_here

# Optional: Weitere Konfiguration
TRACKER_DB_PATH=steam_price_tracker.db
TRACKING_INTERVAL_HOURS=6
CHEAPSHARK_RATE_LIMIT=1.5

# Charts-Konfiguration
CHARTS_UPDATE_INTERVAL_HOURS=6
CHARTS_PRICE_INTERVAL_HOURS=4
CHARTS_CLEANUP_DAYS=30
"""
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        print("✅ .env Template erstellt")
        print("💡 WICHTIG: Trage deinen Steam API Key in die .env-Datei ein!")
        print("🔗 API Key holen: https://steamcommunity.com/dev/apikey")
        print("📝 Dann starte das Programm erneut")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der .env-Datei: {e}")
        return False

def safe_get_scheduler_status(price_tracker):
    """Sichere Scheduler-Status Abfrage mit Fallback"""
    try:
        return price_tracker.get_scheduler_status()
    except AttributeError:
        # Fallback falls Methode nicht existiert
        return {
            'scheduler_running': getattr(price_tracker, 'scheduler_running', False),
            'next_run': 'N/A',
            'jobs_count': 0
        }

def safe_start_scheduler(price_tracker, interval_hours=6):
    """Sicherer Scheduler-Start mit Fallback"""
    try:
        if hasattr(price_tracker, 'start_scheduler'):
            price_tracker.start_scheduler(interval_hours)
        elif hasattr(price_tracker, 'start_price_tracking_scheduler'):
            price_tracker.start_price_tracking_scheduler(interval_hours=interval_hours)
        else:
            raise AttributeError("Keine Scheduler-Start-Methode gefunden")
        return True
    except Exception as e:
        print(f"❌ Fehler beim Starten des Schedulers: {e}")
        return False

def safe_stop_scheduler(price_tracker):
    """Sicherer Scheduler-Stop mit Fallback"""
    try:
        if hasattr(price_tracker, 'stop_scheduler'):
            price_tracker.stop_scheduler()
        elif hasattr(price_tracker, 'stop_price_tracking_scheduler'):
            price_tracker.stop_price_tracking_scheduler()
        else:
            raise AttributeError("Keine Scheduler-Stop-Methode gefunden")
        return True
    except Exception as e:
        print(f"❌ Fehler beim Stoppen des Schedulers: {e}")
        return False

def check_charts_functionality():
    """Prüft ob Charts-Funktionalität verfügbar ist"""
    try:
        # UPDATED: Verwende konsolidierte price_tracker.py
        from database_manager import DatabaseManager
        from price_tracker import SteamPriceTracker
        
        # API Key für Test laden
        api_key = load_api_key_from_env()
        
        # Teste mit temporärem Tracker
        db = DatabaseManager()
        tracker = SteamPriceTracker(db, api_key, enable_charts=True)
        
        # Prüfe ob Charts-Funktionalität verfügbar ist
        charts_available = tracker.charts_enabled
        
        return {
            'available': charts_available,
            'charts_enabled': charts_available,
            'has_api_key': api_key is not None,
            'message': '✅ Charts-Funktionalität verfügbar' if charts_available else f'⚠️ Charts nicht verfügbar ({"kein API Key" if not api_key else "Charts-Module fehlen"})'
        }
        
    except ImportError as e:
        return {
            'available': False,
            'charts_enabled': False,
            'has_api_key': False,
            'message': f'❌ Module nicht gefunden: {e}'
        }
    except Exception as e:
        return {
            'available': False,
            'charts_enabled': False,
            'has_api_key': False,
            'message': f'❌ Fehler: {e}'
        }

def main():
    """Enhanced Hauptfunktion für Steam Price Tracker mit Charts"""
    print("💰 STEAM PRICE TRACKER v2.0 - ENHANCED WITH CHARTS")
    print("Mit Steam Charts Integration und erweiterten Funktionen")
    print("=" * 75)
    
    # API Key laden
    api_key = load_api_key_from_env()
    
    if not api_key:
        print("⚠️ Kein API Key in .env gefunden")
        
        if create_env_template():
            return
        
        api_key = input("Steam API Key eingeben (für Charts-Funktionen): ").strip()
    
    if api_key:
        print("✅ API Key geladen")
    else:
        print("⚠️ Kein API Key - Charts-Funktionen deaktiviert")
    
    # Charts-Funktionalität prüfen
    charts_status = check_charts_functionality()
    print(f"📊 Charts-Status: {charts_status['message']}")
    
    # Komponenten initialisieren
    try:
        # UPDATED: Verwende konsolidierte price_tracker.py
        from database_manager import DatabaseManager
        from price_tracker import SteamPriceTracker
        
        # Database Manager mit Charts-Erweiterungen
        db_manager = DatabaseManager()
        
        # Erstelle Price Tracker mit API Key für Charts-Integration
        price_tracker = SteamPriceTracker(db_manager, api_key, enable_charts=True)
        
        # Prüfe ob Charts-Integration erfolgreich war
        charts_enabled = price_tracker.charts_enabled
        if charts_enabled:
            print("✅ Charts-Integration aktiviert")
        elif api_key:
            print("⚠️ Charts-Integration fehlgeschlagen (Module fehlen?)")
        else:
            print("ℹ️ Charts-Integration deaktiviert (kein API Key)")
        
        print("✅ Steam Price Tracker initialisiert")
            
        # Wishlist Manager
        if api_key:
            from steam_wishlist_manager import SteamWishlistManager
            wishlist_manager = SteamWishlistManager(api_key)
        else:
            wishlist_manager = None
            
    except Exception as e:
        print(f"❌ Fehler beim Initialisieren: {e}")
        print("\n💡 FEHLERBEHEBUNG:")
        print("1. Führe zuerst 'python setup.py setup' aus")
        print("2. Stelle sicher, dass alle neuen Dateien vorhanden sind")
        print("3. Prüfe ob die requirements.txt installiert ist")
        print("4. Für Charts: Stelle sicher dass die Datenbank-Erweiterungen integriert sind")
        return
    
    # Hauptmenü
    while True:
        # Aktuelle Statistiken anzeigen
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
                try:
                    # Verwende get_enhanced_statistics() oder get_statistics() mit Charts-Erweiterungen
                    if hasattr(price_tracker, 'get_enhanced_statistics'):
                        enhanced_stats = price_tracker.get_enhanced_statistics()
                        charts_stats = enhanced_stats.get('charts', {})
                    elif hasattr(price_tracker.db_manager, 'get_charts_statistics'):
                        charts_stats = price_tracker.db_manager.get_charts_statistics()
                    else:
                        charts_stats = None
                    
                    if charts_stats and charts_stats.get('total_active_charts_games', 0) > 0:
                        print(f"\n📊 CHARTS-STATUS:")
                        print(f"🎯 Aktive Charts-Spiele: {charts_stats.get('total_active_charts_games', 0)}")
                        print(f"🎮 Einzigartige Apps in Charts: {charts_stats.get('unique_apps_in_charts', 0)}")
                        print(f"📈 Charts-Preis-Snapshots: {charts_stats.get('total_charts_price_snapshots', 0):,}")
                        
                        # Scheduler Status
                        if hasattr(price_tracker, 'charts_manager') and price_tracker.charts_manager:
                            scheduler_status = price_tracker.charts_manager.get_charts_scheduler_status()
                            if scheduler_status.get('charts_scheduler_running'):
                                print(f"🚀 Charts-Scheduler: AKTIV ✅")
                                next_update = scheduler_status.get('next_charts_update', 'N/A')
                                if next_update and next_update != 'N/A':
                                    print(f"   ⏰ Nächstes Charts-Update: {next_update}")
                            else:
                                print(f"🚀 Charts-Scheduler: INAKTIV ❌")
                    else:
                        print(f"\n📊 CHARTS-STATUS:")
                        print(f"🎯 Charts verfügbar aber noch keine Daten")
                        print(f"💡 Führe 'Charts sofort aktualisieren' aus um zu starten")
                except Exception as e:
                    print(f"⚠️ Charts-Statistiken nicht verfügbar: {e}")
            
            # Standard Scheduler Status
            scheduler_status = safe_get_scheduler_status(price_tracker)
            if scheduler_status['scheduler_running']:
                print(f"🔄 Standard Tracking: AKTIV ✅")
                print(f"   ⏰ Nächster Lauf: {scheduler_status.get('next_run', 'N/A')}")
            else:
                print(f"🔄 Standard Tracking: INAKTIV ❌")
            
            newest_snapshot = stats.get('newest_snapshot')
            if newest_snapshot:
                print(f"🕐 Letzte Preisabfrage: {newest_snapshot[:19]}")
            
        except Exception as e:
            print(f"⚠️ Fehler beim Laden der Statistiken: {e}")
            print("\n📊 AKTUELLER STATUS:")
            print("📚 Getrackte Apps: ❓")
            print("📈 Gesamt Preis-Snapshots: ❓")
        
        # Menüoptionen anzeigen
        print("\n🔧 VERFÜGBARE AKTIONEN:")
        print("=" * 50)
        
        # Standard-Funktionen (ALLE ursprünglichen aus GitHub)
        print("📱 STANDARD TRACKING:")
        print("1. 📱 App manuell zum Tracking hinzufügen")
        print("2. 📥 Steam Wishlist importieren")
        print("3. 🔍 Preise für App anzeigen")
        print("4. 📊 Beste aktuelle Deals anzeigen")
        print("5. 📈 Preisverlauf für App anzeigen")
        print("6. 🔄 Preise manuell aktualisieren")
        print("7. 🚀 Automatisches Tracking starten/stoppen")
        print("8. 📋 Alle getrackte Apps anzeigen")
        print("9. 🗑️ App aus Tracking entfernen")
        print("10. 📄 CSV-Export für App erstellen")
        print("11. 📊 Detaillierte Statistiken")
        print("12. 🔤 App-Namen von Steam aktualisieren")
        print("13. 📝 Namen-Update Historie anzeigen")
        print("14. 🔍 Apps mit generischen Namen finden")
        
        # Charts-Funktionen (falls verfügbar)
        if charts_enabled:
            print("\n📊 CHARTS TRACKING:")
            print("15. 🎯 Charts-Tracking aktivieren/deaktivieren")
            print("16. 📊 Charts sofort aktualisieren")
            print("17. 💰 Charts-Preise aktualisieren")
            print("18. 🏆 Beste Charts-Deals anzeigen")
            print("19. 📈 Trending Charts Price Drops")
            print("20. 📋 Charts-Spiele anzeigen")
            print("21. 🧹 Charts-Spiele bereinigen")
            print("22. 🚀 Vollautomatik einrichten")
            print("23. 👋 Beenden")
        else:
            print("15. 👋 Beenden")
        
        if charts_enabled:
            choice = input("\nWählen Sie eine Aktion (1-23): ").strip()
            max_choice = 23
        else:
            choice = input("\nWählen Sie eine Aktion (1-15): ").strip()
            max_choice = 15
        
        # =====================================================================
        # STANDARD FUNKTIONEN (1-14) - ALLE URSPRÜNGLICHEN AUS GITHUB
        # =====================================================================
        
        if choice == "1":
            # App manuell hinzufügen
            print("\n📱 APP MANUELL HINZUFÜGEN")
            print("=" * 30)
            
            app_id = input("Steam App ID eingeben: ").strip()
            if not app_id:
                print("❌ Keine App ID angegeben")
                continue
            
            name = input("App Name (optional): ").strip()
            if not name:
                name = f"Game {app_id}"
            
            if price_tracker.add_app_to_tracking(app_id, name):
                print(f"✅ {name} ({app_id}) zum Tracking hinzugefügt")
                
                # Namen von Steam abrufen?
                if name.startswith("Game ") and api_key:
                    fetch_name = input("Namen von Steam API abrufen? (j/n): ").lower().strip()
                    if fetch_name in ['j', 'ja', 'y', 'yes']:
                        if hasattr(price_tracker, 'update_single_app_name'):
                            if price_tracker.update_single_app_name(app_id, api_key):
                                print("✅ Name von Steam API aktualisiert")
                            else:
                                print("⚠️ Name konnte nicht von Steam abgerufen werden")
                
                # Sofort Preise abrufen?
                fetch_now = input("Preise sofort abrufen? (j/n): ").lower().strip()
                if fetch_now in ['j', 'ja', 'y', 'yes']:
                    if price_tracker.track_single_app_price(app_id):
                        print("✅ Preise erfolgreich abgerufen")
                    else:
                        print("❌ Preisabruf fehlgeschlagen")
            else:
                print("❌ Fehler beim Hinzufügen der App")
        
        elif choice == "2":
            # Steam Wishlist importieren
            print("\n📥 STEAM WISHLIST IMPORTIEREN")
            print("=" * 35)
            
            steam_id = input("Steam ID oder Custom URL eingeben: ").strip()
            if not steam_id:
                print("❌ Keine Steam ID angegeben")
                continue
            
            print("🔍 Importiere Wishlist...")
            
            if hasattr(price_tracker, 'import_steam_wishlist'):
                # Enhanced Version mit Namen-Updates
                result = price_tracker.import_steam_wishlist(steam_id, api_key, update_names=True)
            else:
                # Standard Wishlist Import
                if not wishlist_manager:
                    print("❌ Kein Steam API Key für Wishlist-Import")
                    continue
                    
                try:
                    wishlist_data = wishlist_manager.get_simple_wishlist(steam_id)
                    
                    if not wishlist_data:
                        print("❌ Wishlist konnte nicht abgerufen werden")
                        continue
                    
                    imported = 0
                    for item in wishlist_data:
                        app_id = item['steam_app_id']
                        name = item['name']
                        
                        if price_tracker.add_app_to_tracking(app_id, name):
                            imported += 1
                    
                    result = {
                        'success': True,
                        'imported': imported,
                        'total_items': len(wishlist_data)
                    }
                except Exception as e:
                    result = {'success': False, 'error': str(e)}
            
            if result['success']:
                print(f"✅ Wishlist-Import erfolgreich:")
                print(f"   📥 {result['imported']} neue Apps hinzugefügt")
                print(f"   ⏭️ {result.get('skipped_existing', 0)} bereits vorhanden")
                if 'names_updated' in result:
                    print(f"   🔄 {result['names_updated']} Namen aktualisiert")
                print(f"   📊 {result['total_items']} Apps insgesamt")
                
                if result.get('errors'):
                    print(f"   ⚠️ {len(result['errors'])} Fehler aufgetreten")
                
                if result['imported'] > 0:
                    fetch_all = input("Preise für alle neuen Apps abrufen? (j/n): ").lower().strip()
                    if fetch_all in ['j', 'ja', 'y', 'yes']:
                        print("🔄 Hole Preise für alle neuen Apps...")
                        if hasattr(price_tracker, 'process_all_pending_apps_optimized'):
                            batch_result = price_tracker.process_all_pending_apps_optimized(hours_threshold=999)
                            if batch_result.get('success'):
                                print(f"✅ Preise für {batch_result['total_successful']} Apps abgerufen")
                            else:
                                print("❌ Fehler beim Abrufen der Preise")
                        else:
                            # Fallback: normale Preisabfrage
                            tracked_apps = price_tracker.get_tracked_apps()
                            recent_apps = [app['steam_app_id'] for app in tracked_apps[-result['imported']:]]
                            if recent_apps:
                                result = price_tracker.track_app_prices(recent_apps)
                                print(f"✅ Preise für {result['successful']} Apps abgerufen")
            else:
                print(f"❌ Wishlist-Import fehlgeschlagen: {result.get('error')}")
        
        elif choice == "3":
            # Preise für App anzeigen
            print("\n🔍 PREISE FÜR APP ANZEIGEN")
            print("=" * 30)
            
            tracked_apps = price_tracker.get_tracked_apps()
            
            if not tracked_apps:
                print("❌ Keine Apps im Tracking")
                continue
            
            print(f"\n📋 GETRACKTE APPS ({len(tracked_apps)}):")
            for i, app in enumerate(tracked_apps[:20], 1):
                print(f"{i:2d}. {app['name']} (ID: {app['steam_app_id']})")
            
            if len(tracked_apps) > 20:
                print(f"    ... und {len(tracked_apps) - 20} weitere")
            
            try:
                choice_idx = int(input("App auswählen (Nummer): ").strip()) - 1
                if 0 <= choice_idx < len(tracked_apps):
                    selected_app = tracked_apps[choice_idx]
                    app_id = selected_app['steam_app_id']
                    
                    # Aktuelle Preise anzeigen
                    latest_prices = price_tracker.get_latest_prices(app_id)
                    
                    if latest_prices:
                        print(f"\n💰 AKTUELLE PREISE: {selected_app['name']}")
                        print(f"Letzte Aktualisierung: {latest_prices['timestamp'][:19]}")
                        print("=" * 50)
                        
                        stores = ['steam', 'greenmangaming', 'gog', 'humblestore', 'fanatical', 'gamesplanet']
                        store_names = ['Steam', 'GreenManGaming', 'GOG', 'HumbleStore', 'Fanatical', 'GamesPlanet']
                        
                        for store, store_name in zip(stores, store_names):
                            price_col = f"{store}_price"
                            available_col = f"{store}_available"
                            discount_col = f"{store}_discount_percent"
                            
                            if latest_prices.get(available_col):
                                price = latest_prices.get(price_col, 0)
                                discount = latest_prices.get(discount_col, 0)
                                
                                status = f"€{price:.2f}"
                                if discount > 0:
                                    status += f" (-{discount}%)"
                                
                                print(f"{store_name:15}: {status}")
                            else:
                                print(f"{store_name:15}: Nicht verfügbar")
                    else:
                        print("❌ Keine Preisdaten verfügbar")
                        
                        # Preise jetzt abrufen?
                        fetch_now = input("Preise jetzt abrufen? (j/n): ").lower().strip()
                        if fetch_now in ['j', 'ja', 'y', 'yes']:
                            if price_tracker.track_single_app_price(app_id):
                                print("✅ Preise erfolgreich abgerufen")
                            else:
                                print("❌ Preisabruf fehlgeschlagen")
                else:
                    print("❌ Ungültige Auswahl")
            except ValueError:
                print("❌ Ungültige Eingabe")
        
        elif choice == "4":
            # Beste aktuelle Deals anzeigen
            print("\n📊 BESTE AKTUELLE DEALS")
            print("=" * 25)
            
            deals = price_tracker.get_current_best_deals(limit=15)
            
            if deals:
                print(f"🏆 Top {len(deals)} Deals:")
                print()
                
                for i, deal in enumerate(deals, 1):
                    print(f"{i:2d}. {deal['game_title']}")
                    print(f"    💰 €{deal['best_price']:.2f} (-{deal['discount_percent']}%) bei {deal['best_store']}")
                    print(f"    🆔 App ID: {deal['steam_app_id']}")
                    print()
            else:
                print("❌ Keine Deals gefunden")
                print("💡 Führe zuerst Preisabfragen durch")
        
        elif choice == "5":
            # Preisverlauf für App anzeigen
            print("\n📈 PREISVERLAUF FÜR APP")
            print("=" * 25)
            
            tracked_apps = price_tracker.get_tracked_apps()
            
            if not tracked_apps:
                print("❌ Keine Apps im Tracking")
                continue
            
            print(f"\n📋 GETRACKTE APPS ({len(tracked_apps)}):")
            for i, app in enumerate(tracked_apps[:10], 1):
                print(f"{i:2d}. {app['name']} (ID: {app['steam_app_id']})")
            
            try:
                choice_idx = int(input("App auswählen (Nummer): ").strip()) - 1
                if 0 <= choice_idx < len(tracked_apps):
                    selected_app = tracked_apps[choice_idx]
                    app_id = selected_app['steam_app_id']
                    
                    days = input("Zeitraum in Tagen (Standard: 30): ").strip()
                    try:
                        days = int(days) if days else 30
                    except ValueError:
                        days = 30
                    
                    history = price_tracker.get_price_history(app_id, days_back=days)
                    
                    if history:
                        print(f"\n📈 PREISVERLAUF: {selected_app['name']} (letzte {days} Tage)")
                        print("=" * 60)
                        
                        # Zeige nur die letzten 10 Einträge
                        for snapshot in history[:10]:
                            date = snapshot['timestamp'][:10]
                            time = snapshot['timestamp'][11:16]
                            
                            print(f"\n📅 {date} {time}:")
                            
                            stores = ['steam', 'greenmangaming', 'gog', 'humblestore', 'fanatical', 'gamesplanet']
                            store_names = ['Steam', 'GreenManGaming', 'GOG', 'HumbleStore', 'Fanatical', 'GamesPlanet']
                            
                            for store, store_name in zip(stores, store_names):
                                price_col = f"{store}_price"
                                available_col = f"{store}_available"
                                discount_col = f"{store}_discount_percent"
                                
                                if snapshot.get(available_col):
                                    price = snapshot.get(price_col, 0)
                                    discount = snapshot.get(discount_col, 0)
                                    
                                    status = f"€{price:.2f}"
                                    if discount > 0:
                                        status += f" (-{discount}%)"
                                    
                                    print(f"  {store_name:15}: {status}")
                        
                        if len(history) > 10:
                            print(f"\n... und {len(history) - 10} weitere Einträge")
                    else:
                        print("❌ Keine Preisverlauf-Daten verfügbar")
                else:
                    print("❌ Ungültige Auswahl")
            except ValueError:
                print("❌ Ungültige Eingabe")
        
        elif choice == "6":
            # Preise manuell aktualisieren
            print("\n🔄 PREISE MANUELL AKTUALISIEREN")
            print("=" * 35)
            
            tracked_apps = price_tracker.get_tracked_apps()
            
            if not tracked_apps:
                print("❌ Keine Apps im Tracking")
                continue
            
            print(f"📚 {len(tracked_apps)} Apps im Tracking")
            update_all = input("Alle Apps aktualisieren? (j/n): ").lower().strip()
            
            if update_all in ['j', 'ja', 'y', 'yes']:
                app_ids = [app['steam_app_id'] for app in tracked_apps]
                print(f"🔄 Aktualisiere Preise für {len(app_ids)} Apps...")
                
                result = price_tracker.track_app_prices(app_ids)
                print(f"✅ {result['successful']}/{result['processed']} Apps erfolgreich aktualisiert")
                
                if result['errors']:
                    print(f"⚠️ {len(result['errors'])} Fehler aufgetreten")
            else:
                # Einzelne App auswählen
                print("\n📋 GETRACKTE APPS:")
                for i, app in enumerate(tracked_apps[:10], 1):
                    print(f"{i:2d}. {app['name']} (ID: {app['steam_app_id']})")
                
                try:
                    choice_idx = int(input("App auswählen (Nummer): ").strip()) - 1
                    if 0 <= choice_idx < len(tracked_apps):
                        selected_app = tracked_apps[choice_idx]
                        app_id = selected_app['steam_app_id']
                        
                        print(f"🔄 Aktualisiere Preise für {selected_app['name']}...")
                        result = price_tracker.track_app_prices([app_id])
                        
                        if result['successful'] > 0:
                            print("✅ Preise erfolgreich aktualisiert")
                        else:
                            print("❌ Preisupdate fehlgeschlagen")
                    else:
                        print("❌ Ungültige Auswahl")
                except ValueError:
                    print("❌ Ungültige Eingabe")
        
        elif choice == "7":
            # Automatisches Tracking starten/stoppen
            print("\n🚀 AUTOMATISCHES TRACKING")
            print("=" * 30)
            
            scheduler_status = safe_get_scheduler_status(price_tracker)
            
            if scheduler_status['scheduler_running']:
                print("🔄 Automatisches Tracking läuft bereits")
                print(f"   ⏰ Nächster Lauf: {scheduler_status.get('next_run', 'N/A')}")
                stop = input("Tracking stoppen? (j/n): ").lower().strip()
                
                if stop in ['j', 'ja', 'y', 'yes']:
                    if safe_stop_scheduler(price_tracker):
                        print("⏹️ Automatisches Tracking gestoppt")
            else:
                print("⏸️ Automatisches Tracking ist inaktiv")
                start = input("Tracking starten? (j/n): ").lower().strip()
                
                if start in ['j', 'ja', 'y', 'yes']:
                    interval_hours = input("Tracking-Intervall in Stunden (Standard: 6): ").strip()
                    try:
                        interval_hours = int(interval_hours) if interval_hours else 6
                    except ValueError:
                        interval_hours = 6
                    
                    if safe_start_scheduler(price_tracker, interval_hours):
                        print(f"▶️ Automatisches Tracking gestartet (alle {interval_hours}h)")
        
        elif choice == "8":
            # Alle getrackte Apps anzeigen
            print("\n📋 ALLE GETRACKTE APPS")
            print("=" * 25)
            
            tracked_apps = price_tracker.get_tracked_apps()
            
            if tracked_apps:
                print(f"📚 {len(tracked_apps)} Apps im Tracking:")
                
                for i, app in enumerate(tracked_apps, 1):
                    last_update = app.get('last_price_update', 'Nie')
                    if last_update and last_update != 'Nie':
                        last_update = last_update[:19]
                    
                    last_name_update = app.get('last_name_update', 'Nie')
                    if last_name_update and last_name_update != 'Nie':
                        last_name_update = last_name_update[:19]
                    
                    name_marker = ""
                    if app['name'].startswith('Game ') or app['name'].startswith('Unknown Game'):
                        name_marker = " 🔤"
                    
                    print(f"{i:3d}. {app['name']}{name_marker}")
                    print(f"      ID: {app['steam_app_id']} | Hinzugefügt: {app['added_at'][:10]}")
                    print(f"      Preisupdate: {last_update} | Namensupdate: {last_name_update}")
            else:
                print("❌ Keine Apps im Tracking")
        
        elif choice == "9":
            # App aus Tracking entfernen
            print("\n🗑️ APP AUS TRACKING ENTFERNEN")
            print("=" * 35)
            
            tracked_apps = price_tracker.get_tracked_apps()
            
            if not tracked_apps:
                print("❌ Keine Apps im Tracking")
                continue
            
            print(f"📋 GETRACKTE APPS ({len(tracked_apps)}):")
            for i, app in enumerate(tracked_apps, 1):
                print(f"{i:2d}. {app['name']} (ID: {app['steam_app_id']})")
            
            try:
                choice_idx = int(input("App zum Entfernen auswählen (Nummer): ").strip()) - 1
                if 0 <= choice_idx < len(tracked_apps):
                    selected_app = tracked_apps[choice_idx]
                    
                    confirm = input(f"'{selected_app['name']}' wirklich entfernen? (j/n): ").lower().strip()
                    if confirm in ['j', 'ja', 'y', 'yes']:
                        if price_tracker.remove_app_from_tracking(selected_app['steam_app_id']):
                            print(f"✅ {selected_app['name']} aus Tracking entfernt")
                        else:
                            print("❌ Fehler beim Entfernen")
                else:
                    print("❌ Ungültige Auswahl")
            except ValueError:
                print("❌ Ungültige Eingabe")
        
        elif choice == "10":
            # CSV-Export für App erstellen
            print("\n📄 CSV-EXPORT FÜR APP")
            print("=" * 25)
            
            tracked_apps = price_tracker.get_tracked_apps()
            
            if not tracked_apps:
                print("❌ Keine Apps im Tracking")
                continue
            
            print(f"\n📋 GETRACKTE APPS ({len(tracked_apps)}):")
            for i, app in enumerate(tracked_apps[:10], 1):
                print(f"{i:2d}. {app['name']} (ID: {app['steam_app_id']})")
            
            try:
                choice_idx = int(input("App für Export auswählen (Nummer): ").strip()) - 1
                if 0 <= choice_idx < len(tracked_apps):
                    selected_app = tracked_apps[choice_idx]
                    app_id = selected_app['steam_app_id']
                    
                    print(f"📄 Erstelle CSV-Export für {selected_app['name']}...")
                    
                    # Erstelle exports Verzeichnis falls nicht vorhanden
                    Path("exports").mkdir(exist_ok=True)
                    
                    output_file = f"exports/price_history_{app_id}_{datetime.now().strftime('%Y%m%d')}.csv"
                    
                    if hasattr(price_tracker, 'export_price_history_csv'):
                        csv_file = price_tracker.export_price_history_csv(app_id, output_file)
                    else:
                        # Fallback: manuelle CSV-Erstellung
                        history = price_tracker.get_price_history(app_id, days_back=90)
                        if history:
                            csv_lines = ["date,Steam,GreenManGaming,GOG,HumbleStore,Fanatical,GamesPlanet"]
                            
                            for snapshot in reversed(history):
                                date = snapshot['timestamp'][:10]
                                prices = []
                                stores = ['steam', 'greenmangaming', 'gog', 'humblestore', 'fanatical', 'gamesplanet']
                                
                                for store in stores:
                                    price_col = f"{store}_price"
                                    available_col = f"{store}_available"
                                    
                                    if snapshot.get(available_col) and snapshot.get(price_col) is not None:
                                        prices.append(f"{snapshot[price_col]:.2f}")
                                    else:
                                        prices.append("")
                                
                                csv_lines.append(f"{date},{','.join(prices)}")
                            
                            with open(output_file, 'w', encoding='utf-8') as f:
                                f.write('\n'.join(csv_lines))
                            
                            csv_file = output_file
                        else:
                            csv_file = None
                    
                    if csv_file:
                        print(f"✅ CSV-Export erstellt: {csv_file}")
                    else:
                        print("❌ CSV-Export fehlgeschlagen (keine Daten?)")
                else:
                    print("❌ Ungültige Auswahl")
            except ValueError:
                print("❌ Ungültige Eingabe")
        
        elif choice == "11":
            # Detaillierte Statistiken
            print("\n📊 DETAILLIERTE STATISTIKEN")
            print("=" * 30)
            
            try:
                stats = price_tracker.get_statistics()
                
                print(f"📚 Getrackte Apps: {stats['tracked_apps']}")
                print(f"📈 Gesamt Preis-Snapshots: {stats.get('total_snapshots', 0):,}")
                print(f"🏪 Getrackte Stores: {len(stats['stores_tracked'])}")
                print(f"    {', '.join(stats['stores_tracked'])}")
                
                if stats.get('oldest_snapshot'):
                    print(f"📅 Ältester Snapshot: {stats['oldest_snapshot'][:19]}")
                else:
                    print("📅 Ältester Snapshot: N/A")
                
                if stats.get('newest_snapshot'):
                    print(f"📅 Neuester Snapshot: {stats['newest_snapshot'][:19]}")
                else:
                    print("📅 Neuester Snapshot: N/A")
                
                # Namen-Update Statistiken
                if 'name_update_stats' in stats:
                    name_stats = stats['name_update_stats']
                    print(f"\n🔤 NAMEN-UPDATE STATISTIKEN:")
                    print(f"📝 Apps mit generischen Namen: {name_stats['apps_with_generic_names']}")
                    print(f"❓ Apps ohne Namen-Update: {name_stats['apps_never_updated']}")
                    print(f"🔄 Gesamt Namen-Updates: {name_stats['total_name_updates']}")
                    print(f"📊 Namen-Updates (24h): {name_stats['updates_last_24h']}")
                    print(f"❌ Fehlgeschlagene Updates: {name_stats['failed_updates']}")
                
                # Charts-Statistiken (falls verfügbar)
                if charts_enabled:
                    try:
                        # Verwende get_enhanced_statistics() oder direkt Charts-Statistiken
                        if hasattr(price_tracker, 'get_enhanced_statistics'):
                            enhanced_stats = price_tracker.get_enhanced_statistics()
                            charts_stats = enhanced_stats.get('charts', {})
                        elif hasattr(price_tracker.db_manager, 'get_charts_statistics'):
                            charts_stats = price_tracker.db_manager.get_charts_statistics()
                        else:
                            charts_stats = None
                            
                        if charts_stats and 'total_active_charts_games' in charts_stats:
                            print(f"\n📊 CHARTS-STATISTIKEN:")
                            print(f"🎯 Aktive Charts-Spiele: {charts_stats['total_active_charts_games']}")
                            print(f"🎮 Einzigartige Apps in Charts: {charts_stats['unique_apps_in_charts']}")
                            print(f"📈 Charts-Preis-Snapshots: {charts_stats['total_charts_price_snapshots']:,}")
                            print(f"📅 Durchschnitt in Charts: {charts_stats.get('average_days_in_charts', 0):.1f} Tage")
                    except Exception as e:
                        print(f"⚠️ Charts-Statistiken nicht verfügbar: {e}")
                
                # Weitere Details aus Datenbank
                if hasattr(price_tracker.db_manager, 'get_total_price_snapshots'):
                    total_snapshots = price_tracker.db_manager.get_total_price_snapshots()
                    print(f"\n🗄️ Datenbank Snapshots: {total_snapshots:,}")
                
            except Exception as e:
                print(f"❌ Fehler beim Laden der Statistiken: {e}")
        
        elif choice == "12":
            # App-Namen von Steam aktualisieren
            print("\n🔤 APP-NAMEN VON STEAM AKTUALISIEREN")
            print("=" * 40)
            
            if not api_key:
                print("❌ Kein Steam API Key verfügbar für Namen-Updates")
                continue
            
            print("Welche Apps sollen aktualisiert werden?")
            print("1. Alle Apps mit generischen Namen (Game XXXXX, Unknown Game)")
            print("2. Alle Apps (kann lange dauern)")
            print("3. Spezifische Apps auswählen")
            print("4. Zurück zum Hauptmenü")
            
            name_choice = input("Auswahl (1-4): ").strip()
            
            if name_choice == "1":
                # Apps mit generischen Namen
                if hasattr(price_tracker, 'get_name_update_candidates'):
                    candidates = price_tracker.get_name_update_candidates()
                else:
                    # Fallback: hole Apps mit generischen Namen
                    all_apps = price_tracker.get_tracked_apps()
                    candidates = [app for app in all_apps if 
                                app['name'].startswith('Game ') or 
                                app['name'].startswith('Unknown Game')]
                
                if not candidates:
                    print("✅ Alle Apps haben bereits korrekte Namen")
                    continue
                
                print(f"🔍 {len(candidates)} Apps mit generischen Namen gefunden:")
                for i, app in enumerate(candidates[:10], 1):
                    print(f"   {i}. {app['name']} (ID: {app['steam_app_id']})")
                
                if len(candidates) > 10:
                    print(f"   ... und {len(candidates) - 10} weitere")
                
                update_generic = input(f"Namen für {len(candidates)} Apps aktualisieren? (j/n): ").lower().strip()
                if update_generic in ['j', 'ja', 'y', 'yes']:
                    print("🔄 Aktualisiere Namen von Steam API...")
                    
                    if hasattr(price_tracker, 'update_names_for_apps_with_generic_names'):
                        result = price_tracker.update_names_for_apps_with_generic_names(api_key)
                    else:
                        # Fallback: manuelle Namen-Updates
                        from steam_wishlist_manager import SteamWishlistManager
                        steam_manager = SteamWishlistManager(api_key)
                        
                        updated = 0
                        failed = 0
                        
                        for app in candidates:
                            try:
                                app_name = steam_manager.get_app_name_only(app['steam_app_id'])
                                if app_name and hasattr(price_tracker.db_manager, 'update_app_name'):
                                    if price_tracker.db_manager.update_app_name(app['steam_app_id'], app_name, 'manual_update'):
                                        updated += 1
                                    else:
                                        failed += 1
                                else:
                                    failed += 1
                            except:
                                failed += 1
                        
                        result = {
                            'success': True,
                            'updated': updated,
                            'failed': failed,
                            'total': len(candidates)
                        }
                    
                    if result['success']:
                        print(f"✅ Namen-Update abgeschlossen:")
                        print(f"   📊 {result['updated']}/{result['total']} Apps erfolgreich")
                        print(f"   ❌ {result['failed']} Apps fehlgeschlagen")
                    else:
                        print(f"❌ Namen-Update fehlgeschlagen: {result.get('error')}")
            
            elif name_choice == "2":
                # Alle Apps
                tracked_apps = price_tracker.get_tracked_apps()
                
                if not tracked_apps:
                    print("❌ Keine Apps im Tracking")
                    continue
                
                print(f"⚠️ Namen für ALLE {len(tracked_apps)} Apps aktualisieren?")
                print("   Das kann bei vielen Apps mehrere Minuten dauern.")
                
                update_all = input("Fortfahren? (j/n): ").lower().strip()
                if update_all in ['j', 'ja', 'y', 'yes']:
                    app_ids = [app['steam_app_id'] for app in tracked_apps]
                    print(f"🔄 Aktualisiere Namen für {len(app_ids)} Apps von Steam API...")
                    
                    if hasattr(price_tracker, 'update_app_names_from_steam'):
                        result = price_tracker.update_app_names_from_steam(app_ids, api_key)
                    else:
                        print("❌ Namen-Update Funktion nicht verfügbar")
                        print("💡 Verwende Enhanced Version für diese Funktionalität")
                        continue
                    
                    if result['success']:
                        print(f"✅ Namen-Update abgeschlossen:")
                        print(f"   📊 {result['updated']}/{result['total']} Apps erfolgreich")
                        print(f"   ❌ {result['failed']} Apps fehlgeschlagen")
                    else:
                        print(f"❌ Namen-Update fehlgeschlagen: {result.get('error')}")
            
            elif name_choice == "3":
                # Spezifische Apps
                tracked_apps = price_tracker.get_tracked_apps()
                
                if not tracked_apps:
                    print("❌ Keine Apps im Tracking")
                    continue
                
                print(f"\n📋 GETRACKTE APPS ({len(tracked_apps)}):")
                for i, app in enumerate(tracked_apps[:20], 1):
                    marker = " 🔤" if app['name'].startswith('Game ') else ""
                    print(f"{i:2d}. {app['name']}{marker} (ID: {app['steam_app_id']})")
                
                if len(tracked_apps) > 20:
                    print(f"    ... und {len(tracked_apps) - 20} weitere")
                
                try:
                    indices = input("App-Nummern eingeben (komma-getrennt): ").strip()
                    if indices:
                        selected_indices = [int(i.strip()) - 1 for i in indices.split(',')]
                        selected_apps = [tracked_apps[i] for i in selected_indices if 0 <= i < len(tracked_apps)]
                        
                        if selected_apps:
                            app_ids = [app['steam_app_id'] for app in selected_apps]
                            print(f"🔄 Aktualisiere Namen für {len(app_ids)} ausgewählte Apps...")
                            
                            if hasattr(price_tracker, 'update_app_names_from_steam'):
                                result = price_tracker.update_app_names_from_steam(app_ids, api_key)
                                
                                if result['success']:
                                    print(f"✅ Namen-Update abgeschlossen:")
                                    print(f"   📊 {result['updated']}/{result['total']} Apps erfolgreich")
                                    print(f"   ❌ {result['failed']} Apps fehlgeschlagen")
                                else:
                                    print(f"❌ Namen-Update fehlgeschlagen: {result.get('error')}")
                            else:
                                print("❌ Namen-Update Funktion nicht verfügbar")
                        else:
                            print("❌ Keine gültigen Apps ausgewählt")
                except ValueError:
                    print("❌ Ungültige Eingabe")
            
            elif name_choice == "4":
                continue
            else:
                print("❌ Ungültige Auswahl")
        
        elif choice == "13":
            # Namen-Update Historie anzeigen
            print("\n📝 NAMEN-UPDATE HISTORIE")
            print("=" * 30)
            
            if hasattr(price_tracker.db_manager, 'get_name_update_history'):
                history = price_tracker.db_manager.get_name_update_history(limit=20)
                
                if history:
                    print(f"📋 Letzte {len(history)} Namen-Updates:")
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
                else:
                    print("❌ Keine Namen-Update Historie gefunden")
            else:
                print("❌ Namen-Update Historie Funktion nicht verfügbar")
                print("💡 Verwende Enhanced Version für diese Funktionalität")
        
        elif choice == "14":
            # Apps mit generischen Namen finden
            print("\n🔍 APPS MIT GENERISCHEN NAMEN")
            print("=" * 35)
            
            if hasattr(price_tracker, 'get_name_update_candidates'):
                generic_apps = price_tracker.get_name_update_candidates()
            else:
                # Fallback: manuelle Suche
                all_apps = price_tracker.get_tracked_apps()
                generic_apps = [app for app in all_apps if 
                              app['name'].startswith('Game ') or 
                              app['name'].startswith('Unknown Game') or
                              app['name'] == '']
            
            if generic_apps:
                print(f"🔤 {len(generic_apps)} Apps mit generischen Namen gefunden:")
                print()
                
                for i, app in enumerate(generic_apps, 1):
                    update_attempts = app.get('name_update_attempts', 0)
                    last_name_update = app.get('last_name_update', 'Nie')
                    if last_name_update and last_name_update != 'Nie':
                        last_name_update = last_name_update[:19]
                    
                    status = ""
                    if update_attempts > 3:
                        status = " ❌ (mehrfach fehlgeschlagen)"
                    elif update_attempts > 0:
                        status = f" ⚠️ ({update_attempts} Versuche)"
                    
                    print(f"{i:3d}. {app['name']}{status}")
                    print(f"     🆔 App ID: {app['steam_app_id']}")
                    print(f"     📅 Hinzugefügt: {app['added_at'][:10]} | Letztes Update: {last_name_update}")
                    print()
                
                # Angebot zur sofortigen Aktualisierung
                if api_key:
                    update_now = input("Namen jetzt von Steam abrufen? (j/n): ").lower().strip()
                    if update_now in ['j', 'ja', 'y', 'yes']:
                        print("🔄 Aktualisiere Namen von Steam API...")
                        
                        if hasattr(price_tracker, 'update_names_for_apps_with_generic_names'):
                            result = price_tracker.update_names_for_apps_with_generic_names(api_key)
                            
                            if result['success']:
                                print(f"✅ Namen-Update abgeschlossen:")
                                print(f"   📊 {result['updated']}/{result['total']} Apps erfolgreich")
                                print(f"   ❌ {result['failed']} Apps fehlgeschlagen")
                            else:
                                print(f"❌ Namen-Update fehlgeschlagen: {result.get('error')}")
                        else:
                            print("❌ Namen-Update Funktion nicht verfügbar")
                else:
                    print("💡 Steam API Key erforderlich für Namen-Updates")
            else:
                print("✅ Alle Apps haben korrekte Namen!")
                print("💡 Keine Apps mit generischen Namen (Game XXXXX) gefunden")
        
        # =====================================================================
        # CHARTS FUNKTIONEN (15-22) - NUR WENN CHARTS VERFÜGBAR
        # =====================================================================
        
        elif charts_enabled and choice == "15":
            # Charts-Tracking aktivieren/deaktivieren
            print("\n🎯 CHARTS-TRACKING VERWALTEN")
            print("=" * 35)
            
            if hasattr(price_tracker, 'charts_manager') and price_tracker.charts_manager:
                try:
                    scheduler_status = price_tracker.charts_manager.get_charts_scheduler_status()
                    
                    if scheduler_status.get('charts_scheduler_running'):
                        print("🔄 Charts-Tracking läuft bereits")
                        print(f"   ⏰ Nächstes Charts-Update: {scheduler_status.get('next_charts_update', 'N/A')}")
                        print(f"   💰 Nächstes Preis-Update: {scheduler_status.get('next_price_update', 'N/A')}")
                        
                        stop = input("Charts-Tracking stoppen? (j/n): ").lower().strip()
                        if stop in ['j', 'ja', 'y', 'yes']:
                            if hasattr(price_tracker, 'disable_charts_tracking'):
                                if price_tracker.disable_charts_tracking():
                                    print("⏹️ Charts-Tracking gestoppt")
                            else:
                                print("❌ disable_charts_tracking Methode nicht verfügbar")
                    else:
                        print("⏸️ Charts-Tracking ist inaktiv")
                        start = input("Charts-Tracking starten? (j/n): ").lower().strip()
                        
                        if start in ['j', 'ja', 'y', 'yes']:
                            charts_hours = input("Charts-Update Intervall in Stunden (Standard: 6): ").strip()
                            price_hours = input("Preis-Update Intervall in Stunden (Standard: 4): ").strip()
                            cleanup_hours = input("Cleanup Intervall in Stunden (Standard: 24): ").strip()
                            
                            try:
                                charts_hours = int(charts_hours) if charts_hours else 6
                                price_hours = int(price_hours) if price_hours else 4
                                cleanup_hours = int(cleanup_hours) if cleanup_hours else 24
                            except ValueError:
                                charts_hours, price_hours, cleanup_hours = 6, 4, 24
                            
                            if hasattr(price_tracker, 'enable_charts_tracking'):
                                if price_tracker.enable_charts_tracking(charts_hours, price_hours, cleanup_hours):
                                    print(f"▶️ Charts-Tracking gestartet")
                                    print(f"   📊 Charts-Updates: alle {charts_hours}h")
                                    print(f"   💰 Preis-Updates: alle {price_hours}h")
                            else:
                                print("❌ enable_charts_tracking Methode nicht verfügbar")
                except Exception as e:
                    print(f"❌ Charts-Scheduler Fehler: {e}")
            else:
                print("❌ Charts-Manager nicht verfügbar")
        
        elif charts_enabled and choice == "16":
            # Charts sofort aktualisieren
            print("\n📊 CHARTS AKTUALISIEREN")
            print("=" * 25)
            
            print("Welche Charts sollen aktualisiert werden?")
            print("1. Alle Charts")
            print("2. Meistgespielte Spiele")
            print("3. Beste neue Releases")
            print("4. Bestseller")
            print("5. Wöchentliche Bestseller")
            
            chart_choice = input("Auswahl (1-5): ").strip()
            
            chart_types = None
            if chart_choice == "2":
                chart_types = ["most_played"]
            elif chart_choice == "3":
                chart_types = ["top_releases"]
            elif chart_choice == "4":
                chart_types = ["best_sellers"]
            elif chart_choice == "5":
                chart_types = ["weekly_top_sellers"]
            
            print("🔄 Starte Charts-Update...")
            
            if hasattr(price_tracker, 'update_charts_now'):
                result = price_tracker.update_charts_now(chart_types)
                
                if result.get('success', True):
                    print("✅ Charts-Update abgeschlossen:")
                    print(f"   📊 {result.get('total_games_found', 0)} Spiele gefunden")
                    print(f"   ➕ {result.get('new_games_added', 0)} neue Spiele")
                    print(f"   🔄 {result.get('existing_games_updated', 0)} aktualisiert")
                else:
                    print(f"❌ Charts-Update fehlgeschlagen: {result.get('error')}")
            else:
                print("❌ Charts-Update Funktion nicht verfügbar")
        
        elif charts_enabled and choice == "17":
            # Charts-Preise aktualisieren
            print("\n💰 CHARTS-PREISE AKTUALISIEREN")
            print("=" * 35)
            
            print("🔄 Aktualisiere Preise für alle Charts-Spiele...")
            
            if hasattr(price_tracker, 'update_charts_prices_now'):
                result = price_tracker.update_charts_prices_now()
                
                if result.get('success'):
                    print("✅ Charts-Preisupdate abgeschlossen:")
                    print(f"   📊 {result.get('total_games', 0)} Spiele verarbeitet")
                    print(f"   💰 {result.get('successful', 0)} erfolgreich aktualisiert")
                    
                    if result.get('failed', 0) > 0:
                        print(f"   ❌ {result['failed']} fehlgeschlagen")
                else:
                    print(f"❌ Charts-Preisupdate fehlgeschlagen: {result.get('error')}")
            else:
                print("❌ Charts-Preisupdate Funktion nicht verfügbar")
        
        elif charts_enabled and choice == "18":
            # Beste Charts-Deals anzeigen
            print("\n🏆 BESTE CHARTS-DEALS")
            print("=" * 25)
            
            chart_type_filter = input("Chart-Typ Filter (Enter für alle): ").strip()
            if not chart_type_filter:
                chart_type_filter = None
            
            if hasattr(price_tracker, 'get_best_charts_deals'):
                deals = price_tracker.get_best_charts_deals(limit=15, chart_type=chart_type_filter)
                
                if deals:
                    print(f"🏆 Top {len(deals)} Charts-Deals:")
                    print()
                    
                    for i, deal in enumerate(deals, 1):
                        rank_info = f"#{deal.get('current_rank', '?')}" if deal.get('current_rank') else ""
                        chart_info = f"[{deal.get('chart_type', 'Unknown')}]"
                        
                        print(f"{i:2d}. {deal['game_title'][:35]:<35} {rank_info} {chart_info}")
                        print(f"    💰 €{deal['best_price']:.2f} (-{deal['discount_percent']}%) bei {deal['best_store']}")
                        print(f"    🆔 App ID: {deal['steam_app_id']}")
                        print()
                else:
                    print("❌ Keine Charts-Deals gefunden")
                    print("💡 Führe zuerst Charts-Updates und Preisabfragen durch")
            else:
                print("❌ Charts-Deals Funktion nicht verfügbar")
        
        elif charts_enabled and choice == "19":
            # Trending Charts Price Drops
            print("\n📈 TRENDING CHARTS PRICE DROPS")
            print("=" * 35)
            
            hours = input("Stunden zurückblicken (Standard: 24): ").strip()
            min_discount = input("Mindestrabatt in % (Standard: 20): ").strip()
            
            try:
                hours = int(hours) if hours else 24
                min_discount = int(min_discount) if min_discount else 20
            except ValueError:
                hours, min_discount = 24, 20
            
            if hasattr(price_tracker, 'get_trending_price_drops'):
                trending = price_tracker.get_trending_price_drops(hours_back=hours, min_discount=min_discount)
                
                if trending:
                    print(f"📈 Trending Price Drops (letzte {hours}h, min. {min_discount}%):")
                    print()
                    
                    for i, item in enumerate(trending, 1):
                        chart_badge = f"[{item['chart_type']}]"
                        
                        print(f"{i:2d}. {item['game_title'][:35]:<35} {chart_badge}")
                        print(f"    💰 €{item['current_price']:.2f} (-{item['discount_percent']}%) bei {item['store']}")
                        print(f"    📅 {item['timestamp'][:16]}")
                        print()
                else:
                    print("❌ Keine Trending Price Drops gefunden")
                    print("💡 Versuche niedrigeren Mindestrabatt oder längeren Zeitraum")
            else:
                print("❌ Trending Price Drops Funktion nicht verfügbar")
        
        elif charts_enabled and choice == "20":
            # Charts-Spiele anzeigen
            print("\n📋 CHARTS-SPIELE ANZEIGEN")
            print("=" * 30)
            
            chart_type_filter = input("Chart-Typ Filter (Enter für alle): ").strip()
            if not chart_type_filter:
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
                else:
                    print("❌ Keine Charts-Spiele gefunden")
                    print("💡 Führe zuerst ein Charts-Update durch")
            else:
                print("❌ Charts-Spiele Funktion nicht verfügbar")
        
        elif charts_enabled and choice == "21":
            # Charts-Spiele bereinigen
            print("\n🧹 CHARTS-SPIELE BEREINIGEN")
            print("=" * 30)
            
            days = input("Spiele entfernen die länger als X Tage nicht in Charts waren (Standard: 30): ").strip()
            try:
                days = int(days) if days else 30
            except ValueError:
                days = 30
            
            print(f"🧹 Starte Charts-Cleanup (>{days} Tage)...")
            
            if hasattr(price_tracker, 'charts_manager') and price_tracker.charts_manager:
                if hasattr(price_tracker.charts_manager, 'cleanup_old_chart_games'):
                    removed = price_tracker.charts_manager.cleanup_old_chart_games(days)
                    
                    if removed > 0:
                        print(f"✅ {removed} alte Charts-Spiele entfernt")
                    else:
                        print("✅ Keine alten Charts-Spiele zum Entfernen gefunden")
                else:
                    print("❌ cleanup_old_chart_games Methode nicht verfügbar")
            else:
                print("❌ Charts-Manager nicht verfügbar")
        
        elif charts_enabled and choice == "22":
            # Vollautomatik einrichten
            print("\n🚀 VOLLAUTOMATIK EINRICHTEN")
            print("=" * 35)
            
            print("Diese Funktion richtet vollautomatisches Tracking ein für:")
            print("• Standard Apps (Wishlist, manuell hinzugefügte)")
            print("• Steam Charts (automatisch erkannte beliebte Spiele)")
            print("• Automatische Preisabfragen für beide Kategorien")
            print("• Automatisches Cleanup alter Charts-Spiele")
            print()
            
            confirm = input("Vollautomatik einrichten? (j/n): ").lower().strip()
            if confirm in ['j', 'ja', 'y', 'yes']:
                normal_hours = input("Intervall normale Apps (Stunden, Standard: 6): ").strip()
                charts_hours = input("Intervall Charts-Updates (Stunden, Standard: 6): ").strip()
                charts_price_hours = input("Intervall Charts-Preise (Stunden, Standard: 4): ").strip()
                
                try:
                    normal_hours = int(normal_hours) if normal_hours else 6
                    charts_hours = int(charts_hours) if charts_hours else 6
                    charts_price_hours = int(charts_price_hours) if charts_price_hours else 4
                except ValueError:
                    normal_hours, charts_hours, charts_price_hours = 6, 6, 4
                
                # Setup Vollautomatik
                try:
                    # Normales Tracking starten
                    if safe_start_scheduler(price_tracker, normal_hours):
                        print(f"✅ Standard-Tracking gestartet (alle {normal_hours}h)")
                    
                    # Charts-Tracking starten (falls verfügbar)
                    if hasattr(price_tracker, 'enable_charts_tracking'):
                        if price_tracker.enable_charts_tracking(charts_hours, charts_price_hours, 24):
                            print(f"✅ Charts-Tracking gestartet")
                            print(f"   📊 Charts-Updates: alle {charts_hours}h")
                            print(f"   💰 Charts-Preise: alle {charts_price_hours}h")
                            print(f"   🧹 Charts-Cleanup: alle 24h")
                    
                    print("\n✅ Vollautomatik erfolgreich eingerichtet!")
                    print("\n💡 Alle Scheduler laufen nun automatisch im Hintergrund!")
                        
                except Exception as e:
                    print(f"❌ Fehler beim Einrichten der Vollautomatik: {e}")
        
        # =====================================================================
        # BEENDEN
        # =====================================================================
        
        elif (not charts_enabled and choice == "15") or (charts_enabled and choice == "23"):
            # Beenden
            print("\n👋 BEENDEN")
            print("=" * 10)
            
            # Standard-Scheduler stoppen falls aktiv
            scheduler_status = safe_get_scheduler_status(price_tracker)
            if scheduler_status['scheduler_running']:
                print("⏹️ Stoppe Standard-Tracking...")
                safe_stop_scheduler(price_tracker)
            
            # Charts-Scheduler stoppen falls aktiv
            if charts_enabled and hasattr(price_tracker, 'charts_manager') and price_tracker.charts_manager:
                try:
                    scheduler_status = price_tracker.charts_manager.get_charts_scheduler_status()
                    if scheduler_status.get('charts_scheduler_running'):
                        print("⏹️ Stoppe Charts-Tracking...")
                        if hasattr(price_tracker, 'disable_charts_tracking'):
                            price_tracker.disable_charts_tracking()
                except Exception as e:
                    print(f"⚠️ Charts-Scheduler konnte nicht gestoppt werden: {e}")
            
            print("💾 Datenbankverbindungen werden automatisch geschlossen...")
            print("✅ Enhanced Steam Price Tracker beendet. Auf Wiedersehen!")
            break
        
        else:
            print("❌ Ungültige Auswahl - bitte versuchen Sie es erneut")
        
        # Kleine Pause zwischen Aktionen
        if choice not in [str(max_choice)]:  # Nicht bei "Beenden"
            print("\n" + "="*50)
            input("💡 Drücken Sie Enter um zum Hauptmenü zurückzukehren...")

if __name__ == "__main__":
    main()
