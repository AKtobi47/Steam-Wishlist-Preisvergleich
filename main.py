"""
Steam Price Tracker - Hauptanwendung
Vollständige CLI-Implementation mit allen Funktionen
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

def main():
    """Hauptfunktion für Steam Price Tracker"""
    print("💰 STEAM PRICE TRACKER v1.0")
    print("Direktes CheapShark-Preis-Tracking ohne Mapping-Komplexität")
    print("=" * 70)
    
    # API Key laden
    api_key = load_api_key_from_env()
    
    if not api_key:
        print("⚠️ Kein API Key in .env gefunden")
        
        if create_env_template():
            return
        
        api_key = input("Steam API Key eingeben: ").strip()
    
    if not api_key:
        print("❌ Kein API Key angegeben")
        return
    
    print("✅ API Key geladen")
    
    # Komponenten initialisieren
    try:
        from database_manager import DatabaseManager
        from price_tracker import SteamPriceTracker
        from steam_wishlist_manager import SteamWishlistManager
        
        db_manager = DatabaseManager()
        price_tracker = SteamPriceTracker(db_manager)
        wishlist_manager = SteamWishlistManager(api_key)
        print("✅ Steam Price Tracker initialisiert")
    except Exception as e:
        print(f"❌ Fehler beim Initialisieren: {e}")
        return
    
    # Hauptmenü
    while True:
        # Aktuelle Statistiken anzeigen
        try:
            stats = price_tracker.get_statistics()
            scheduler_status = safe_get_scheduler_status(price_tracker)
            
            print(f"\n📊 AKTUELLER STATUS:")
            print(f"📚 Getrackte Apps: {stats['tracked_apps']}")
            total_snapshots = stats.get('total_snapshots', 0)
            print(f"📈 Gesamt Preis-Snapshots: {total_snapshots:,}")
            print(f"🏪 Stores: {', '.join(stats['stores_tracked'])}")
            
            if scheduler_status['scheduler_running']:
                print(f"🚀 Automatisches Tracking: AKTIV ✅")
                print(f"   ⏰ Nächster Lauf: {scheduler_status.get('next_run', 'N/A')}")
            else:
                print(f"🚀 Automatisches Tracking: INAKTIV ❌")
            
            newest_snapshot = stats.get('newest_snapshot')
            if newest_snapshot:
                print(f"🕐 Letzte Preisabfrage: {newest_snapshot[:19]}")
            
        except Exception as e:
            print(f"⚠️ Fehler beim Laden der Statistiken: {e}")
            print("\n📊 AKTUELLER STATUS:")
            print("📚 Getrackte Apps: ❓")
            print("📈 Gesamt Preis-Snapshots: ❓")
            print("🚀 Automatisches Tracking: ❓")
        
        print("\n🔧 VERFÜGBARE AKTIONEN:")
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
        print("12. 👋 Beenden")
        
        choice = input("\nWählen Sie eine Aktion (1-12): ").strip()
        
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
            result = price_tracker.import_steam_wishlist(steam_id, api_key)
            
            if result['success']:
                print(f"✅ Wishlist-Import erfolgreich:")
                print(f"   📥 {result['imported']} neue Apps hinzugefügt")
                print(f"   ⏭️ {result.get('skipped_existing', 0)} bereits vorhanden")
                print(f"   📊 {result['total_items']} Apps insgesamt")
                
                if result.get('errors'):
                    print(f"   ⚠️ {len(result['errors'])} Fehler aufgetreten")
                
                if result['imported'] > 0:
                    fetch_all = input("Preise für alle neuen Apps abrufen? (j/n): ").lower().strip()
                    if fetch_all in ['j', 'ja', 'y', 'yes']:
                        print("🔄 Hole Preise für alle neuen Apps...")
                        # Dies könnte eine Weile dauern
                        batch_result = price_tracker.process_all_pending_apps_optimized(hours_threshold=999)  # Alle Apps
                        if batch_result.get('success'):
                            print(f"✅ Preise für {batch_result['total_successful']} Apps abgerufen")
                        else:
                            print("❌ Fehler beim Abrufen der Preise")
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
                    
                    print(f"{i:3d}. {app['name']}")
                    print(f"      ID: {app['steam_app_id']} | Hinzugefügt: {app['added_at'][:10]} | Letztes Update: {last_update}")
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
                    csv_file = price_tracker.export_price_history_csv(app_id, output_file)
                    
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
                
                # Weitere Details aus Datenbank
                total_snapshots = price_tracker.db_manager.get_total_price_snapshots()
                print(f"🗄️ Datenbank Snapshots: {total_snapshots:,}")
                
            except Exception as e:
                print(f"❌ Fehler beim Laden der Statistiken: {e}")
        
        elif choice == "12":
            # Beenden
            print("\n👋 BEENDEN")
            print("=" * 10)
            
            # Scheduler stoppen falls aktiv
            scheduler_status = safe_get_scheduler_status(price_tracker)
            if scheduler_status['scheduler_running']:
                print("⏹️ Stoppe automatisches Tracking...")
                safe_stop_scheduler(price_tracker)
            
            print("💾 Datenbankverbindungen werden automatisch geschlossen...")
            
            print("✅ Steam Price Tracker beendet. Auf Wiedersehen!")
            break
        
        else:
            print("❌ Ungültige Auswahl - bitte versuchen Sie es erneut")
        
        # Kleine Pause zwischen Aktionen
        if choice != "12":
            print("\n" + "="*50)
            input("💡 Drücken Sie Enter um zum Hauptmenü zurückzukehren...")

if __name__ == "__main__":
    main()