"""
Steam Price Tracker - Hauptanwendung
Vereinfachtes System für direktes CheapShark-Preis-Tracking
Basiert auf Steam-Wishlist-Manager aber fokussiert auf Preise
"""

import sys
import time
from datetime import datetime
from pathlib import Path
from price_tracker import SteamPriceTracker
from database_manager import DatabaseManager
from steam_wishlist_manager import SteamWishlistManager, load_api_key_from_env

def create_env_template(env_file=".env") -> bool:
    """Erstellt eine .env-Template-Datei falls sie nicht existiert"""
    env_path = Path(env_file)
    
    if env_path.exists():
        return False
    
    try:
        template_content = """# Steam Price Tracker Konfiguration
# Trage hier deinen Steam Web API Key ein
# Erhältlich unter: https://steamcommunity.com/dev/apikey
STEAM_API_KEY=your_steam_api_key_here

# Beispiel:
# STEAM_API_KEY=ABCD1234567890EFGH
"""
        
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        print(f"📝 .env-Template erstellt: {env_file}")
        print("   Bitte trage deinen Steam API Key ein und starte das Programm erneut.")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der .env-Datei: {e}")
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
            scheduler_status = price_tracker.get_scheduler_status()
            
            print(f"\n📊 AKTUELLER STATUS:")
            print(f"📚 Getrackte Apps: {stats['tracked_apps']}")
            # Korrigiert: verwende den richtigen Key
            total_snapshots = stats.get('total_snapshots', stats.get('total_price_snapshots', 0))
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
        print("10. 📄 Preisverlauf als CSV exportieren")
        print("11. 🔧 Datenbank-Wartung")
        print("12. ❌ Beenden")
        
        choice = input("\nWählen Sie eine Aktion (1-12): ").strip()
        
        if choice == "1":
            # App manuell hinzufügen
            print("\n📱 APP MANUELL HINZUFÜGEN")
            print("=" * 30)
            
            # Option 1: Steam App ID direkt
            print("Option 1: Steam App ID direkt eingeben")
            app_id = input("Steam App ID eingeben (oder Enter für Suche): ").strip()
            
            if app_id and app_id.isdigit():
                app_name = input("App Name eingeben (optional): ").strip()
                if not app_name:
                    app_name = f"App_{app_id}"
                
                if price_tracker.add_app_to_tracking(app_id, app_name):
                    print(f"✅ App {app_name} zum Tracking hinzugefügt")
                else:
                    print(f"❌ Konnte App nicht hinzufügen")
            else:
                # Option 2: Steam App suchen
                print("\nOption 2: Nach Steam App suchen")
                search_term = input("App Name zum Suchen eingeben: ").strip()
                
                if search_term:
                    search_results = wishlist_manager.search_steam_app(search_term)
                    
                    if search_results:
                        print(f"\n🔍 Gefundene Apps ({len(search_results)}):")
                        for i, app in enumerate(search_results, 1):
                            print(f"{i:2d}. {app['name']} (ID: {app['appid']})")
                        
                        try:
                            choice_idx = int(input("Wählen Sie eine App (Nummer): ").strip()) - 1
                            if 0 <= choice_idx < len(search_results):
                                selected_app = search_results[choice_idx]
                                
                                if price_tracker.add_app_to_tracking(str(selected_app['appid']), selected_app['name']):
                                    print(f"✅ App {selected_app['name']} zum Tracking hinzugefügt")
                                else:
                                    print(f"❌ Konnte App nicht hinzufügen")
                            else:
                                print("❌ Ungültige Auswahl")
                        except ValueError:
                            print("❌ Ungültige Eingabe")
                    else:
                        print("❌ Keine Apps gefunden")
        
        elif choice == "2":
            # Steam Wishlist importieren
            print("\n📥 STEAM WISHLIST IMPORTIEREN")
            print("=" * 35)
            
            steam_id = input("Steam ID (17 Ziffern) eingeben: ").strip()
            
            if not steam_id or len(steam_id) != 17 or not steam_id.isdigit():
                print("❌ Ungültige Steam ID")
                continue
            
            print(f"🔄 Importiere Wishlist für Steam ID {steam_id}...")
            result = price_tracker.import_steam_wishlist(steam_id, api_key)
            
            if result.get('success'):
                print(f"✅ {result['imported']}/{result['total_items']} Apps importiert")
            else:
                print(f"❌ Import fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")
        
        elif choice == "3":
            # Preise für App anzeigen
            print("\n🔍 AKTUELLE PREISE ANZEIGEN")
            print("=" * 30)
            
            app_id = input("Steam App ID eingeben: ").strip()
            
            if app_id.isdigit():
                price_tracker.print_price_summary(app_id)
            else:
                print("❌ Ungültige App ID")
        
        elif choice == "4":
            # Beste aktuelle Deals
            print("\n📊 BESTE AKTUELLE DEALS")
            print("=" * 25)
            
            limit = input("Wie viele Deals anzeigen? (Standard: 10): ").strip()
            try:
                limit = int(limit) if limit else 10
            except ValueError:
                limit = 10
            
            deals = price_tracker.get_current_best_deals(limit)
            
            if deals:
                print(f"\n🏆 TOP {len(deals)} DEALS:")
                for i, deal in enumerate(deals, 1):
                    print(f"{i:2d}. {deal['game_title']}: €{deal['price']:.2f} "
                          f"(-{deal['discount_percent']}%) bei {deal['store']}")
            else:
                print("❌ Keine Deals gefunden")
        
        elif choice == "5":
            # Preisverlauf anzeigen
            print("\n📈 PREISVERLAUF ANZEIGEN")
            print("=" * 25)
            
            app_id = input("Steam App ID eingeben: ").strip()
            
            if app_id.isdigit():
                days = input("Anzahl Tage zurück (Standard: 30): ").strip()
                try:
                    days = int(days) if days else 30
                except ValueError:
                    days = 30
                
                history = price_tracker.get_price_history(app_id, days_back=days)
                
                if history:
                    app_name = history[0]['game_title']
                    print(f"\n📈 PREISVERLAUF: {app_name}")
                    print(f"📊 {len(history)} Snapshots in den letzten {days} Tagen")
                    
                    # Zeige die letzten 5 Snapshots
                    for snapshot in history[:5]:
                        date = snapshot['timestamp'][:10]
                        print(f"\n📅 {date}:")
                        
                        for store, price_info in snapshot['prices'].items():
                            if price_info['available'] and price_info['price']:
                                price = price_info['price']
                                discount = price_info['discount_percent']
                                
                                if discount > 0:
                                    print(f"   {store:15}: €{price:.2f} (-{discount}%)")
                                else:
                                    print(f"   {store:15}: €{price:.2f}")
                else:
                    print("❌ Keine Preisdaten gefunden")
            else:
                print("❌ Ungültige App ID")
        
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
            
            scheduler_status = price_tracker.get_scheduler_status()
            
            if scheduler_status['scheduler_running']:
                print("🔄 Automatisches Tracking läuft bereits")
                stop = input("Tracking stoppen? (j/n): ").lower().strip()
                
                if stop in ['j', 'ja', 'y', 'yes']:
                    price_tracker.stop_scheduler()
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
                    
                    price_tracker.start_scheduler(interval_hours)
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
                            print(f"✅ App {selected_app['name']} entfernt")
                        else:
                            print("❌ Fehler beim Entfernen")
                else:
                    print("❌ Ungültige Auswahl")
            except ValueError:
                print("❌ Ungültige Eingabe")
        
        elif choice == "10":
            # CSV Export
            print("\n📄 PREISVERLAUF CSV EXPORT")
            print("=" * 30)
            
            tracked_apps = price_tracker.get_tracked_apps()
            
            if not tracked_apps:
                print("❌ Keine Apps im Tracking")
                continue
            
            print(f"📋 GETRACKTE APPS ({len(tracked_apps)}):")
            for i, app in enumerate(tracked_apps, 1):
                print(f"{i:2d}. {app['name']} (ID: {app['steam_app_id']})")
            
            try:
                choice_idx = int(input("App für Export auswählen (Nummer): ").strip()) - 1
                if 0 <= choice_idx < len(tracked_apps):
                    selected_app = tracked_apps[choice_idx]
                    app_id = selected_app['steam_app_id']
                    
                    print(f"📄 Exportiere Preisverlauf für {selected_app['name']}...")
                    csv_file = price_tracker.export_price_history_csv(app_id)
                    
                    if csv_file:
                        print(f"✅ CSV exportiert: {csv_file}")
                    else:
                        print("❌ Export fehlgeschlagen")
                else:
                    print("❌ Ungültige Auswahl")
            except ValueError:
                print("❌ Ungültige Eingabe")
        
        elif choice == "11":
            # Datenbank-Wartung
            print("\n🔧 DATENBANK-WARTUNG")
            print("=" * 20)
            
            print("1. 🧹 Alte Preisdaten bereinigen (>90 Tage)")
            print("2. 💾 Datenbank-Backup erstellen")
            print("3. 🔧 Datenbank optimieren (VACUUM)")
            print("4. 📄 Alle Daten als JSON exportieren")
            print("5. 📊 Detaillierte Statistiken")
            
            maintenance_choice = input("Wartungsoption wählen (1-5): ").strip()
            
            if maintenance_choice == "1":
                print("🧹 Bereinige alte Preisdaten...")
                db_manager.cleanup_old_prices(days=90)
                print("✅ Bereinigung abgeschlossen")
            
            elif maintenance_choice == "2":
                print("💾 Erstelle Datenbank-Backup...")
                backup_file = db_manager.backup_database()
                if backup_file:
                    print(f"✅ Backup erstellt: {backup_file}")
                else:
                    print("❌ Backup fehlgeschlagen")
            
            elif maintenance_choice == "3":
                print("🔧 Optimiere Datenbank...")
                db_manager.vacuum_database()
                print("✅ Optimierung abgeschlossen")
            
            elif maintenance_choice == "4":
                print("📄 Exportiere alle Daten...")
                export_file = db_manager.export_all_price_data()
                if export_file:
                    print(f"✅ Export erstellt: {export_file}")
                else:
                    print("❌ Export fehlgeschlagen")
            
            elif maintenance_choice == "5":
                # Detaillierte Statistiken
                try:
                    detailed_stats = db_manager.get_tracking_statistics()
                    
                    print(f"\n📊 DETAILLIERTE STATISTIKEN:")
                    print(f"=" * 30)
                    print(f"📚 Getrackte Apps: {detailed_stats['tracked_apps']}")
                    print(f"📈 Gesamt Snapshots: {detailed_stats['total_snapshots']:,}")
                    print(f"📊 Snapshots (24h): {detailed_stats['snapshots_last_24h']}")
                    
                    if detailed_stats['oldest_snapshot']:
                        print(f"📅 Ältester Snapshot: {detailed_stats['oldest_snapshot'][:19]}")
                    else:
                        print("📅 Ältester Snapshot: N/A")
                        
                    if detailed_stats['newest_snapshot']:
                        print(f"📅 Neuester Snapshot: {detailed_stats['newest_snapshot'][:19]}")
                    else:
                        print("📅 Neuester Snapshot: N/A")
                        
                    print(f"🚨 Aktive Alerts: {detailed_stats['active_alerts']}")
                    
                except Exception as e:
                    print(f"❌ Fehler beim Laden der Statistiken: {e}")
            
            else:
                print("❌ Ungültige Auswahl")
        
        elif choice == "12":
            # Beenden
            print("\n👋 BEENDEN")
            print("=" * 10)
            
            # Scheduler stoppen falls aktiv
            scheduler_status = price_tracker.get_scheduler_status()
            if scheduler_status['scheduler_running']:
                print("⏹️ Stoppe automatisches Tracking...")
                price_tracker.stop_scheduler()
            
            print("💾 Datenbankverbindungen werden automatisch geschlossen...")
            # Hinweis: SQLite-Verbindungen werden über Context Manager automatisch geschlossen
            
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