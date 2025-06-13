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
        stats = price_tracker.get_statistics()
        scheduler_status = price_tracker.get_scheduler_status()
        
        print(f"\n📊 AKTUELLER STATUS:")
        print(f"📚 Getrackte Apps: {stats['tracked_apps']}")
        print(f"📈 Gesamt Preis-Snapshots: {stats['total_snapshots']:,}")
        print(f"🏪 Stores: {', '.join(stats['stores_tracked'])}")
        
        if scheduler_status['scheduler_running']:
            print(f"🚀 Automatisches Tracking: AKTIV ✅")
            print(f"   ⏰ Nächster Lauf: {scheduler_status.get('next_run', 'N/A')}")
        else:
            print(f"🚀 Automatisches Tracking: INAKTIV ❌")
        
        if stats['newest_snapshot']:
            print(f"🕐 Letzte Preisabfrage: {stats['newest_snapshot'][:19]}")
        
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
        
        if choice == "12":
            # Scheduler stoppen falls läuft
            if price_tracker.scheduler_running:
                print("🛑 Stoppe automatisches Tracking...")
                price_tracker.stop_price_tracking_scheduler()
            print("👋 Steam Price Tracker beendet")
            break
        
        elif choice == "1":
            # App manuell hinzufügen
            print("\n📱 APP MANUELL HINZUFÜGEN")
            print("=" * 30)
            
            app_input = input("Steam App ID oder App-Name eingeben: ").strip()
            
            if app_input.isdigit():
                # App ID direkt eingegeben
                app_id = app_input
                name = input("App-Name (Enter für automatische Erkennung): ").strip() or None
                
                if price_tracker.add_app_to_tracking(app_id, name):
                    print(f"✅ App {app_id} zum Tracking hinzugefügt")
                else:
                    print(f"❌ Konnte App {app_id} nicht hinzufügen")
            else:
                # App-Name - suche zuerst
                print(f"🔍 Suche nach '{app_input}'...")
                search_results = wishlist_manager.search_steam_app(app_input)
                
                if not search_results:
                    print("❌ Keine Apps gefunden")
                    continue
                
                print("\n📋 Suchergebnisse:")
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
                    print(f"{i:2d}. {deal['game_title']}")
                    print(f"     💰 {deal['store']}: €{deal['price']:.2f} (war €{deal['original_price']:.2f}, -{deal['discount_percent']}%)")
            else:
                print("📭 Keine aktuellen Deals gefunden")
        
        elif choice == "5":
            # Preisverlauf anzeigen
            print("\n📈 PREISVERLAUF ANZEIGEN")
            print("=" * 25)
            
            app_id = input("Steam App ID eingeben: ").strip()
            days = input("Wie viele Tage zurück? (Standard: 30): ").strip()
            
            try:
                days = int(days) if days else 30
            except ValueError:
                days = 30
            
            if app_id.isdigit():
                history = price_tracker.get_price_history(app_id, days)
                
                if history:
                    print(f"\n📊 PREISVERLAUF FÜR: {history[0]['game_title']}")
                    print(f"Letzte {days} Tage ({len(history)} Snapshots)")
                    print("=" * 50)
                    
                    for snapshot in history[:10]:  # Zeige nur die letzten 10
                        date = snapshot['timestamp'][:10]
                        print(f"\n📅 {date}:")
                        
                        for store, price_info in snapshot['prices'].items():
                            if price_info['available'] and price_info['price']:
                                discount = f" (-{price_info['discount_percent']}%)" if price_info['discount_percent'] > 0 else ""
                                print(f"   {store:15}: €{price_info['price']:.2f}{discount}")
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
                print("❌ Keine Apps für Tracking konfiguriert")
                continue
            
            print(f"🔄 Aktualisiere Preise für {len(tracked_apps)} Apps...")
            
            app_ids = [app['steam_app_id'] for app in tracked_apps]
            result = price_tracker.track_app_prices(app_ids)
            
            print(f"✅ Preise aktualisiert:")
            print(f"   📊 Verarbeitet: {result['processed']}")
            print(f"   ✅ Erfolgreich: {result['successful']}")
            print(f"   ❌ Fehlgeschlagen: {result['failed']}")
        
        elif choice == "7":
            # Automatisches Tracking starten/stoppen
            if price_tracker.scheduler_running:
                print("🛑 Stoppe automatisches Tracking...")
                price_tracker.stop_price_tracking_scheduler()
                print("✅ Automatisches Tracking gestoppt")
            else:
                print("\n🚀 AUTOMATISCHES TRACKING STARTEN")
                print("=" * 35)
                
                interval = input("Intervall in Stunden (Standard: 6): ").strip()
                try:
                    interval = int(interval) if interval else 6
                except ValueError:
                    interval = 6
                
                price_tracker.start_price_tracking_scheduler(interval_hours=interval)
                print(f"✅ Automatisches Tracking gestartet (alle {interval}h)")
        
        elif choice == "8":
            # Alle getrackte Apps anzeigen
            print("\n📋 ALLE GETRACKTE APPS")
            print("=" * 25)
            
            tracked_apps = price_tracker.get_tracked_apps()
            
            if tracked_apps:
                print(f"\n📚 {len(tracked_apps)} getrackte Apps:")
                for i, app in enumerate(tracked_apps, 1):
                    last_update = app['last_price_update'][:19] if app['last_price_update'] else "Nie"
                    print(f"{i:2d}. {app['name']} (ID: {app['steam_app_id']})")
                    print(f"     📅 Hinzugefügt: {app['added_at'][:10]}")
                    print(f"     🔄 Letzte Preisabfrage: {last_update}")
            else:
                print("📭 Keine Apps für Tracking konfiguriert")
        
        elif choice == "9":
            # App aus Tracking entfernen
            print("\n🗑️ APP AUS TRACKING ENTFERNEN")
            print("=" * 30)
            
            tracked_apps = price_tracker.get_tracked_apps()
            
            if not tracked_apps:
                print("❌ Keine Apps für Tracking konfiguriert")
                continue
            
            print("\n📋 Getrackte Apps:")
            for i, app in enumerate(tracked_apps, 1):
                print(f"{i:2d}. {app['name']} (ID: {app['steam_app_id']})")
            
            try:
                choice_idx = int(input("Welche App entfernen? (Nummer): ").strip()) - 1
                if 0 <= choice_idx < len(tracked_apps):
                    app_to_remove = tracked_apps[choice_idx]
                    
                    confirm = input(f"🤔 '{app_to_remove['name']}' wirklich entfernen? (j/n): ").strip().lower()
                    if confirm in ['j', 'ja', 'y', 'yes']:
                        if price_tracker.remove_app_from_tracking(app_to_remove['steam_app_id']):
                            print(f"✅ App '{app_to_remove['name']}' aus Tracking entfernt")
                        else:
                            print("❌ Fehler beim Entfernen")
                    else:
                        print("❌ Abgebrochen")
                else:
                    print("❌ Ungültige Auswahl")
            except ValueError:
                print("❌ Ungültige Eingabe")
        
        elif choice == "10":
            # Preisverlauf als CSV exportieren
            print("\n📄 PREISVERLAUF ALS CSV EXPORTIEREN")
            print("=" * 40)
            
            app_id = input("Steam App ID eingeben: ").strip()
            
            if app_id.isdigit():
                csv_file = price_tracker.export_price_history_csv(app_id)
                if csv_file:
                    print(f"✅ CSV-Export erfolgreich: {csv_file}")
                else:
                    print("❌ Export fehlgeschlagen")
            else:
                print("❌ Ungültige App ID")
        
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
                detailed_stats = db_manager.get_tracking_statistics()
                
                print(f"\n📊 DETAILLIERTE STATISTIKEN:")
                print(f"=" * 30)
                print(f"📚 Getrackte Apps: {detailed_stats['tracked_apps']}")
                print(f"📈 Gesamt Snapshots: {detailed_stats['total_snapshots']:,}")
                print(f"📊 Snapshots (24h): {detailed_stats['snapshots_last_24h']}")
                print(f"📅 Ältester Snapshot: {detailed_stats['oldest_snapshot'][:19] if detailed_stats['oldest_snapshot'] else 'N/A'}")
                print(f"📅 Neuester Snapshot: {detailed_stats['newest_snapshot'][:19] if detailed_stats['newest_snapshot'] else 'N/A'}")
                print(f"🚨 Aktive Alerts: {detailed_stats['active_alerts']}")
            
            else:
                print("❌ Ungültige Auswahl")
        
        else:
            print("❌ Ungültige Auswahl - bitte versuchen Sie es erneut")
        
        # Kleine Pause zwischen Aktionen
        print("\n" + "="*50)
        input("💡 Drücken Sie Enter um zum Hauptmenü zurückzukehren...")

if __name__ == "__main__":
    main()
