#!/usr/bin/env python3
"""
Steam Price Tracker - Beispiele für programmatische Nutzung
Zeigt verschiedene Anwendungsfälle und Workflows
"""

import time
from datetime import datetime, timedelta
from price_tracker import SteamPriceTracker
from database_manager import DatabaseManager
from steam_wishlist_manager import SteamWishlistManager, load_api_key_from_env

def example_basic_usage():
    """Beispiel 1: Grundlegende Nutzung"""
    print("📝 BEISPIEL 1: GRUNDLEGENDE NUTZUNG")
    print("=" * 40)
    
    # API Key laden
    api_key = load_api_key_from_env()
    if not api_key:
        print("❌ Kein API Key in .env gefunden")
        return
    
    # Tracker initialisieren
    tracker = SteamPriceTracker()
    
    # Bekannte Steam App IDs (aus Projekt_SteamGoG.ipynb)
    apps_to_track = [
        ("413150", "Stardew Valley"),
        ("105600", "Terraria"),
        ("892970", "Valheim"),
        ("582010", "Monster Hunter: World"),
        ("2246340", "Monster Hunter Wilds")
    ]
    
    print("📱 Füge Apps zum Tracking hinzu...")
    for app_id, name in apps_to_track:
        if tracker.add_app_to_tracking(app_id, name):
            print(f"   ✅ {name} (ID: {app_id})")
        else:
            print(f"   ❌ {name} (ID: {app_id}) - Fehler")
    
    print("\n🔄 Aktualisiere Preise...")
    app_ids = [app_id for app_id, _ in apps_to_track]
    result = tracker.track_app_prices(app_ids)
    
    print(f"📊 Ergebnis: {result['successful']}/{result['processed']} erfolgreich")
    
    print("\n🏆 Zeige beste aktuelle Deals:")
    deals = tracker.get_current_best_deals(limit=3)
    for i, deal in enumerate(deals, 1):
        print(f"   {i}. {deal['game_title']}: €{deal['price']:.2f} "
              f"(-{deal['discount_percent']}%) bei {deal['store']}")

def example_wishlist_import():
    """Beispiel 2: Steam Wishlist Import"""
    print("\n📝 BEISPIEL 2: STEAM WISHLIST IMPORT")
    print("=" * 40)
    
    # API Key laden
    api_key = load_api_key_from_env()
    if not api_key:
        print("❌ Kein API Key für Wishlist-Import")
        return
    
    # Tracker initialisieren
    tracker = SteamPriceTracker()
    
    # Beispiel Steam ID (muss durch echte ID ersetzt werden)
    # steam_id = "76561197960435530"  # Gabe Newell (öffentlich)
    steam_id = input("Steam ID eingeben (17 Ziffern): ").strip()
    
    if len(steam_id) != 17 or not steam_id.isdigit():
        print("❌ Ungültige Steam ID - Beispiel übersprungen")
        return
    
    print(f"📥 Importiere Wishlist für Steam ID {steam_id}...")
    
    # Wishlist importieren
    result = tracker.import_steam_wishlist(steam_id, api_key)
    
    if result.get('success'):
        print(f"✅ Import erfolgreich:")
        print(f"   📱 {result['imported']}/{result['total_items']} Apps importiert")
        
        # Sofort Preise abrufen
        print("🔄 Rufe aktuelle Preise ab...")
        tracked_apps = tracker.get_tracked_apps()
        if tracked_apps:
            app_ids = [app['steam_app_id'] for app in tracked_apps[-5:]]  # Nur letzte 5
            price_result = tracker.track_app_prices(app_ids)
            print(f"   💰 {price_result['successful']} Preise aktualisiert")
    else:
        print(f"❌ Import fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")

def example_automated_tracking():
    """Beispiel 3: Automatisches Preis-Tracking"""
    print("\n📝 BEISPIEL 3: AUTOMATISCHES PREIS-TRACKING")
    print("=" * 50)
    
    # Tracker initialisieren
    tracker = SteamPriceTracker()
    
    # Prüfe ob Apps getrackt werden
    tracked_apps = tracker.get_tracked_apps()
    
    if not tracked_apps:
        print("❌ Keine Apps für Tracking konfiguriert")
        print("💡 Führe zuerst Beispiel 1 oder 2 aus")
        return
    
    print(f"📚 {len(tracked_apps)} Apps werden getrackt")
    
    # Scheduler-Status prüfen
    scheduler_status = tracker.get_scheduler_status()
    
    if scheduler_status['scheduler_running']:
        print("🚀 Automatisches Tracking läuft bereits")
        print(f"   ⏰ Nächster Lauf: {scheduler_status.get('next_run', 'Unbekannt')}")
    else:
        print("🚀 Starte automatisches Tracking...")
        
        # Kurzes Intervall für Demo (normalerweise 6+ Stunden)
        demo_interval = 0.1  # 6 Minuten für Demo
        tracker.start_price_tracking_scheduler(interval_hours=demo_interval)
        
        print(f"✅ Scheduler gestartet (alle {demo_interval * 60:.0f} Minuten für Demo)")
        print("💡 In Produktion: Verwende 6+ Stunden Intervall")
        
        # Kurz warten für Demo
        print("⏳ Warte auf ersten Scheduler-Lauf...")
        time.sleep(30)  # 30 Sekunden warten
        
        # Status prüfen
        new_status = tracker.get_scheduler_status()
        print(f"📊 Scheduler läuft: {new_status['scheduler_running']}")
        
        # Scheduler wieder stoppen für Demo
        print("🛑 Stoppe Scheduler (Demo)")
        tracker.stop_price_tracking_scheduler()

def example_price_analysis():
    """Beispiel 4: Preisverlauf-Analyse"""
    print("\n📝 BEISPIEL 4: PREISVERLAUF-ANALYSE")
    print("=" * 40)
    
    # Tracker initialisieren
    tracker = SteamPriceTracker()
    
    # App für Analyse wählen
    tracked_apps = tracker.get_tracked_apps()
    
    if not tracked_apps:
        print("❌ Keine Apps für Analyse verfügbar")
        return
    
    # Erste App für Demo
    demo_app = tracked_apps[0]
    app_id = demo_app['steam_app_id']
    app_name = demo_app['name']
    
    print(f"📊 Analysiere Preise für: {app_name} (ID: {app_id})")
    
    # Preisverlauf abrufen
    history = tracker.get_price_history(app_id, days_back=30)
    
    if not history:
        print("❌ Keine Preisdaten verfügbar")
        return
    
    print(f"📈 {len(history)} Preis-Snapshots in den letzten 30 Tagen")
    
    # Aktuelle Preise anzeigen
    if history:
        latest = history[0]
        print(f"\n💰 AKTUELLE PREISE ({latest['timestamp'][:10]}):")
        
        for store, price_info in latest['prices'].items():
            if price_info['available'] and price_info['price']:
                price = price_info['price']
                discount = price_info['discount_percent']
                
                if discount > 0:
                    original = price_info['original_price']
                    print(f"   {store:15}: €{price:.2f} (war €{original:.2f}, -{discount}%)")
                else:
                    print(f"   {store:15}: €{price:.2f}")
            else:
                print(f"   {store:15}: Nicht verfügbar")
    
    # Preis-Trends berechnen (vereinfacht)
    if len(history) >= 2:
        print(f"\n📈 PREIS-TRENDS (vereinfacht):")
        
        for store in ['Steam', 'GreenManGaming', 'GOG']:
            prices = []
            for snapshot in reversed(history):  # Chronologisch
                price_info = snapshot['prices'].get(store, {})
                if price_info.get('available') and price_info.get('price'):
                    prices.append(price_info['price'])
            
            if len(prices) >= 2:
                trend = "📈 steigend" if prices[-1] > prices[0] else "📉 fallend" if prices[-1] < prices[0] else "➡️ stabil"
                min_price = min(prices)
                max_price = max(prices)
                
                print(f"   {store:15}: {trend} (€{min_price:.2f} - €{max_price:.2f})")

def example_export_functionality():
    """Beispiel 5: Export-Funktionalität"""
    print("\n📝 BEISPIEL 5: EXPORT-FUNKTIONALITÄT")
    print("=" * 40)
    
    # Tracker initialisieren
    tracker = SteamPriceTracker()
    
    # Apps für Export
    tracked_apps = tracker.get_tracked_apps()
    
    if not tracked_apps:
        print("❌ Keine Apps für Export verfügbar")
        return
    
    # Erste App exportieren
    demo_app = tracked_apps[0]
    app_id = demo_app['steam_app_id']
    app_name = demo_app['name']
    
    print(f"📄 Exportiere Preisverlauf für: {app_name}")
    
    # CSV-Export (kompatibel mit Projekt_SteamGoG.ipynb)
    csv_file = tracker.export_price_history_csv(app_id)
    
    if csv_file:
        print(f"✅ CSV-Export erstellt: {csv_file}")
        
        # Erste paar Zeilen anzeigen
        try:
            with open(csv_file, 'r') as f:
                lines = f.readlines()[:5]
            
            print("📋 Erste Zeilen:")
            for line in lines:
                print(f"   {line.strip()}")
            
            if len(lines) == 5:
                print("   ...")
        
        except Exception as e:
            print(f"⚠️ Konnte Datei nicht lesen: {e}")
    else:
        print("❌ Export fehlgeschlagen")
    
    # Vollständiger Daten-Export
    print("\n📦 Erstelle vollständigen JSON-Export...")
    json_file = tracker.db_manager.export_all_price_data()
    
    if json_file:
        print(f"✅ JSON-Export erstellt: {json_file}")
    else:
        print("❌ JSON-Export fehlgeschlagen")

def example_maintenance_tasks():
    """Beispiel 6: Wartungs-Aufgaben"""
    print("\n📝 BEISPIEL 6: WARTUNGS-AUFGABEN")
    print("=" * 35)
    
    # Database Manager initialisieren
    db_manager = DatabaseManager()
    
    # Aktuelle Statistiken
    stats = db_manager.get_tracking_statistics()
    
    print("📊 AKTUELLE STATISTIKEN:")
    print(f"   📚 Getrackte Apps: {stats['tracked_apps']}")
    print(f"   📈 Gesamt Snapshots: {stats['total_snapshots']:,}")
    print(f"   📊 Snapshots (24h): {stats['snapshots_last_24h']}")
    
    if stats['oldest_snapshot']:
        print(f"   📅 Ältester Snapshot: {stats['oldest_snapshot'][:10]}")
    if stats['newest_snapshot']:
        print(f"   📅 Neuester Snapshot: {stats['newest_snapshot'][:10]}")
    
    # Backup erstellen
    print("\n💾 Erstelle Datenbank-Backup...")
    backup_file = db_manager.backup_database()
    
    if backup_file:
        print(f"✅ Backup erstellt: {backup_file}")
    else:
        print("❌ Backup fehlgeschlagen")
    
    # Datenbank optimieren
    print("\n🔧 Optimiere Datenbank...")
    db_manager.vacuum_database()
    
    # Alte Daten bereinigen (Demo: nur sehr alte Daten)
    cutoff_days = 365  # 1 Jahr
    print(f"\n🧹 Bereinige Daten älter als {cutoff_days} Tage...")
    db_manager.cleanup_old_prices(days=cutoff_days)
    
    print("✅ Wartung abgeschlossen")

def main():
    """Hauptfunktion für Beispiele"""
    print("🎯 STEAM PRICE TRACKER - BEISPIELE")
    print("Verschiedene Anwendungsfälle und Workflows")
    print("=" * 60)
    
    examples = [
        ("1", "Grundlegende Nutzung", example_basic_usage),
        ("2", "Steam Wishlist Import", example_wishlist_import),
        ("3", "Automatisches Tracking", example_automated_tracking),
        ("4", "Preisverlauf-Analyse", example_price_analysis),
        ("5", "Export-Funktionalität", example_export_functionality),
        ("6", "Wartungs-Aufgaben", example_maintenance_tasks)
    ]
    
    print("\n📋 VERFÜGBARE BEISPIELE:")
    for num, title, _ in examples:
        print(f"   {num}. {title}")
    
    print("   a. Alle Beispiele nacheinander ausführen")
    print("   x. Beenden")
    
    while True:
        choice = input("\nBeispiel wählen (1-6, a, x): ").strip().lower()
        
        if choice == 'x':
            print("👋 Beispiele beendet")
            break
        
        elif choice == 'a':
            print("🚀 Führe alle Beispiele aus...\n")
            for num, title, func in examples:
                try:
                    func()
                    time.sleep(2)  # Kurze Pause zwischen Beispielen
                except KeyboardInterrupt:
                    print("\n⏹️ Abgebrochen durch Benutzer")
                    break
                except Exception as e:
                    print(f"❌ Fehler in Beispiel {num}: {e}")
            print("\n🏁 Alle Beispiele abgeschlossen")
            break
        
        else:
            # Einzelnes Beispiel
            example_found = False
            for num, title, func in examples:
                if choice == num:
                    try:
                        func()
                        example_found = True
                    except KeyboardInterrupt:
                        print("\n⏹️ Abgebrochen durch Benutzer")
                    except Exception as e:
                        print(f"❌ Fehler: {e}")
                        import traceback
                        traceback.print_exc()
                    break
            
            if not example_found:
                print("❌ Ungültige Auswahl")
        
        print("\n" + "="*50)

if __name__ == "__main__":
    main()
