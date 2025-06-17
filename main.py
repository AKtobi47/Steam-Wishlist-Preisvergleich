#!/usr/bin/env python3
"""
Steam Price Tracker - Enhanced Main Application v3.0
Vollständige Integration aller Features mit Elasticsearch-Support
"""

import os
import sys
import time
import atexit
import signal
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# =====================================================================
# SIGNAL HANDLER AND CLEANUP SETUP
# =====================================================================

cleanup_tasks = []
background_processes = []

def register_cleanup_task(task_function):
    """Registriert eine Cleanup-Aufgabe"""
    cleanup_tasks.append(task_function)

def register_background_process(process):
    """Registriert einen Background-Prozess für Cleanup"""
    if process and process.poll() is None:
        background_processes.append(process)

def cleanup_handler(*args):
    """Enhanced Cleanup Handler"""
    try:
        print("\n🧹 Enhanced Cleanup wird ausgeführt...")
        
        # Background Processes beenden
        for process in background_processes:
            try:
                if process.poll() is None:
                    print(f"   🔄 Beende Prozess {process.pid}")
                    process.terminate()
                    process.wait(timeout=5)
            except Exception as e:
                print(f"   ⚠️ Fehler beim Beenden von Prozess: {e}")
        
        # Cleanup Tasks ausführen
        for task in cleanup_tasks:
            try:
                task()
            except Exception as e:
                print(f"   ⚠️ Cleanup Task Fehler: {e}")
        
        print("✅ Enhanced Cleanup abgeschlossen")
        
    except Exception as e:
        print(f"❌ Cleanup Fehler: {e}")

# Cleanup Handler registrieren
atexit.register(cleanup_handler)
signal.signal(signal.SIGINT, cleanup_handler)
signal.signal(signal.SIGTERM, cleanup_handler)

# =====================================================================
# ELASTICSEARCH INTEGRATION CHECK
# =====================================================================

def check_elasticsearch_availability():
    """Prüft ob Elasticsearch-Integration verfügbar ist"""
    try:
        # Prüfe ob ElasticsearchManager verfügbar ist
        elasticsearch_manager_path = Path("elasticsearch_manager.py")
        docker_compose_path = Path("docker-compose-elk.yml")
        
        elasticsearch_available = elasticsearch_manager_path.exists()
        elk_stack_available = docker_compose_path.exists()
        
        if elasticsearch_available:
            try:
                from elasticsearch_manager import ElasticsearchManager
                return True, "full"
            except ImportError as e:
                return False, f"import_error: {e}"
        
        return False, "not_installed"
        
    except Exception as e:
        return False, f"error: {e}"

def load_elasticsearch_manager():
    """Lädt ElasticsearchManager falls verfügbar"""
    try:
        from elasticsearch_manager import ElasticsearchManager
        return ElasticsearchManager()
    except ImportError:
        return None
    except Exception as e:
        print(f"⚠️ Fehler beim Laden des ElasticsearchManagers: {e}")
        return None

# =====================================================================
# CHARTS STATISTICS DISPLAY
# =====================================================================

def display_charts_statistics(price_tracker):
    """Zeigt Charts-Statistiken an"""
    try:
        # Prüfe Charts-Verfügbarkeit
        if not hasattr(price_tracker, 'charts_enabled') or not price_tracker.charts_enabled:
            return
        
        from database_manager import DatabaseManager
        db = DatabaseManager()
        
        if hasattr(db, 'get_charts_statistics'):
            stats = db.get_charts_statistics()
            
            if stats and stats.get('total_active_charts_games', 0) > 0:
                print(f"\n📊 CHARTS-STATUS:")
                print(f"🎯 Aktive Charts-Games: {stats['total_active_charts_games']}")
                print(f"📈 Letzte Charts-Aktualisierung: {stats.get('last_charts_update', 'Nie')}")
                
                # Charts nach Typ aufteilen
                if 'active_by_chart_type' in stats:
                    active_by_chart = stats['active_by_chart_type']
                    chart_info = []
                    for chart_type, count in active_by_chart.items():
                        chart_info.append(f"{chart_type}: {count}")
                    print(f"🏆 " + " | ".join(chart_info))
            else:
                print(f"\n📊 CHARTS-STATUS:")
                print(f"🎯 Charts verfügbar aber noch keine Daten")
                print(f"💡 Führe 'Charts sofort aktualisieren' aus um zu starten")
        
    except Exception as e:
        print(f"⚠️ Fehler beim Laden der Charts-Statistiken: {e}")

# =====================================================================
# ELASTICSEARCH STATISTICS DISPLAY
# =====================================================================

def display_elasticsearch_statistics(es_manager):
    """Zeigt Elasticsearch-Statistiken an"""
    if not es_manager:
        return
    
    try:
        if es_manager.check_connection():
            stats = es_manager.get_cluster_stats()
            if stats:
                print(f"\n🔍 ELASTICSEARCH-STATUS:")
                print(f"📊 Cluster Status: {stats.get('status', 'unknown')}")
                print(f"📈 Dokumente: {stats.get('docs_count', 0):,}")
                print(f"🗄️ Index-Größe: {stats.get('store_size', 'unknown')}")
                print(f"⚡ Aktive Shards: {stats.get('active_shards', 0)}")
        else:
            print(f"\n🔍 ELASTICSEARCH-STATUS:")
            print(f"❌ Elasticsearch nicht erreichbar")
            print(f"💡 Starte ELK Stack mit: docker-compose -f docker-compose-elk.yml up")
            
    except Exception as e:
        print(f"⚠️ Fehler beim Laden der Elasticsearch-Statistiken: {e}")

# =====================================================================
# PROCESS MANAGEMENT TERMINAL
# =====================================================================

def start_process_management_terminal():
    """Startet Enhanced Process Management Terminal"""
    try:
        from background_scheduler import EnhancedBackgroundScheduler
        
        # Terminal Script erstellen
        terminal_script = '''#!/usr/bin/env python3
"""Enhanced Process Management Terminal v2.0"""

import os
import sys
import time
import psutil
from pathlib import Path

def show_active_processes():
    """Zeigt aktive Price Tracker Prozesse"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
        try:
            cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
            
            # Steam Price Tracker Prozesse identifizieren
            if any(keyword in cmdline.lower() for keyword in [
                'main.py', 'price_tracker', 'steam_charts', 'background_scheduler', 
                'batch_processor', 'elasticsearch_manager'
            ]):
                memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cmdline': cmdline[:80] + '...' if len(cmdline) > 80 else cmdline,
                    'memory_mb': memory_mb,
                    'cpu_percent': proc.info['cpu_percent']
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return processes

def main():
    """Hauptschleife des Process Management Terminals"""
    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print("🔧 ENHANCED PROCESS MANAGEMENT TERMINAL v2.0")
            print("=" * 60)
            print(f"⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
            processes = show_active_processes()
            
            if processes:
                print("🔄 AKTIVE STEAM PRICE TRACKER PROZESSE:")
                print("-" * 60)
                print(f"{'PID':>8} {'Prozess':20} {'CPU%':>6} {'RAM(MB)':>8} {'Kommando'}")
                print("-" * 60)
                
                for proc in processes:
                    print(f"{proc['pid']:>8} {proc['name'][:20]:20} {proc['cpu_percent']:>6.1f} {proc['memory_mb']:>8.1f} {proc['cmdline']}")
                
                print()
                print("📊 AKTIONEN:")
                print("1. Status aktualisieren")
                print("2. Prozess beenden")
                print("3. Alle Prozesse beenden")
                print("4. System-Ressourcen anzeigen")
                print("5. Beenden")
                
                # Automatische Aktualisierung alle 10 Sekunden
                print("\\n⏳ Automatische Aktualisierung in 10 Sekunden...")
                time.sleep(10)
                
                # Clear screen
                os.system('cls' if os.name == 'nt' else 'clear')
            else:
                print("\\n💤 Keine aktiven Prozesse - warte 5 Sekunden...")
                time.sleep(5)
                os.system('cls' if os.name == 'nt' else 'clear')
                
    except KeyboardInterrupt:
        print("\\n👋 Enhanced Process Management Terminal beendet")

if __name__ == "__main__":
    main()
'''
        
        # Script in temporäre Datei schreiben
        temp_dir = Path("temp_schedulers")
        temp_dir.mkdir(exist_ok=True)
        
        script_path = temp_dir / "enhanced_process_management_terminal.py"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(terminal_script)
        
        # Terminal starten
        terminal_title = "🔧 Enhanced Process Management Terminal v2.0"
        
        if os.name == 'nt':  # Windows
            batch_content = f'''@echo off
title {terminal_title}
color 0B
cd /d "{Path.cwd()}"
python "{script_path}"
pause
'''
            batch_path = temp_dir / "start_process_management.bat"
            with open(batch_path, 'w', encoding='utf-8') as f:
                f.write(batch_content)
            
            process = subprocess.Popen(
                ['cmd', '/c', 'start', str(batch_path)],
                cwd=str(Path.cwd()),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
        else:  # Unix/Linux/macOS
            shell_content = f'''#!/bin/bash
echo "🔧 {terminal_title}"
cd "{Path.cwd()}"
python3 "{script_path}"
read -p "Drücke Enter zum Schließen..."
'''
            shell_path = temp_dir / "start_process_management.sh"
            with open(shell_path, 'w', encoding='utf-8') as f:
                f.write(shell_content)
            
            os.chmod(shell_path, 0o755)
            
            # Terminal-Kommandos versuchen
            terminal_commands = [
                ['gnome-terminal', '--title', terminal_title, '--', 'bash', str(shell_path)],
                ['xterm', '-title', terminal_title, '-e', f'bash {shell_path}'],
                ['konsole', '--title', terminal_title, '-e', f'bash {shell_path}'],
            ]
            
            process = None
            for cmd in terminal_commands:
                try:
                    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    break
                except (FileNotFoundError, subprocess.SubprocessError):
                    continue
        
        if process:
            register_background_process(process)
            print("✅ Enhanced Process Management Terminal gestartet")
        else:
            print("⚠️ Konnte Process Management Terminal nicht starten")
            
    except Exception as e:
        print(f"❌ Fehler beim Starten des Process Management Terminals: {e}")

# =====================================================================
# ENHANCED MAIN APPLICATION
# =====================================================================

def main():
    print("🚀 ENHANCED STEAM PRICE TRACKER v3.0")
    print("=" * 60)
    print("Vollständiges Preis-Tracking mit Elasticsearch & Charts Integration")
    print("Alle Background-Tasks werden beim Beenden automatisch gestoppt")
    print()
    
    # ===========================
    # INITIALISIERUNG
    # ===========================
    
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
        
        # Enhanced Price Tracker erstellen
        price_tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        charts_enabled = price_tracker.charts_enabled
        
        print(f"✅ Enhanced Price Tracker initialisiert")
        if charts_enabled:
            print(f"📊 Charts-Integration: VERFÜGBAR")
        else:
            print(f"📊 Charts-Integration: NICHT VERFÜGBAR")
            
    except Exception as e:
        print(f"❌ Fehler beim Initialisieren des Price Trackers: {e}")
        return
    
    # Elasticsearch Manager laden
    es_available, es_status = check_elasticsearch_availability()
    es_manager = None
    
    if es_available:
        es_manager = load_elasticsearch_manager()
        if es_manager:
            print(f"🔍 Elasticsearch-Integration: VERFÜGBAR")
        else:
            print(f"🔍 Elasticsearch-Integration: FEHLER beim Laden")
    else:
        print(f"🔍 Elasticsearch-Integration: NICHT VERFÜGBAR ({es_status})")
    
    # Process Cleanup registrieren
    def cleanup_price_tracker():
        try:
            if hasattr(price_tracker, 'stop_scheduler'):
                price_tracker.stop_scheduler()
            print("   ✅ Price Tracker Scheduler gestoppt")
        except Exception as e:
            print(f"   ⚠️ Fehler beim Stoppen des Price Tracker Schedulers: {e}")
    
    register_cleanup_task(cleanup_price_tracker)
    
    # ===========================
    # HAUPT-MENÜ-SCHLEIFE
    # ===========================
    
    while True:
        try:
            # Clear screen
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # Header
            print("🚀 ENHANCED STEAM PRICE TRACKER v3.0")
            print("=" * 60)
            print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Status anzeigen
            try:
                from database_manager import DatabaseManager
                db = DatabaseManager()
                stats = db.get_statistics()
                
                print(f"\n📊 AKTUELLER STATUS:")
                print(f"🎯 Getrackte Apps: {stats['tracked_apps']}")
                print(f"💾 Preis-Snapshots: {stats['total_snapshots']:,}")
                print(f"📅 Letzte Aktualisierung: {stats.get('last_update', 'Nie')}")
                
                # Scheduler Status
                scheduler_status = price_tracker.get_scheduler_status()
                if scheduler_status['scheduler_running']:
                    print(f"🔄 Automatisches Tracking: AKTIV")
                    if scheduler_status.get('next_run'):
                        print(f"⏰ Nächster Lauf: {scheduler_status['next_run']}")
                else:
                    print(f"⏸️ Automatisches Tracking: INAKTIV")
                
                # Charts-Statistiken
                display_charts_statistics(price_tracker)
                
                # Elasticsearch-Statistiken
                display_elasticsearch_statistics(es_manager)
                
            except Exception as e:
                print(f"⚠️ Fehler beim Laden der Statistiken: {e}")
            
            # Hauptmenü
            print(f"\n🎯 HAUPTMENÜ:")
            print("=" * 25)
            print("1.  📱 App manuell zum Tracking hinzufügen")
            print("2.  📥 Steam Wishlist importieren")
            print("3.  🔍 Aktuelle Preise anzeigen")
            print("4.  📊 Beste Deals anzeigen")
            print("5.  📈 Preisverlauf anzeigen")
            print("6.  🔄 Preise manuell aktualisieren")
            print("7.  🚀 Automatisches Tracking starten/stoppen")
            print("8.  📋 Getrackte Apps verwalten")
            print("9.  🗑️ Apps entfernen")
            print("10. 📄 CSV-Export erstellen")
            print("11. 📊 Detaillierte Statistiken")
            print("12. ⚙️ System-Tools & Wartung")
            
            # Charts-Menü (falls verfügbar)
            if charts_enabled:
                print("\n📊 CHARTS-FEATURES:")
                print("13. 🏆 Steam Charts anzeigen")
                print("14. 📈 Charts sofort aktualisieren")
                print("15. 🎯 Charts-Deals anzeigen")
                print("16. 📊 Charts-Statistiken")
                print("17. 🔄 Charts automatisch tracken")
            
            # Elasticsearch-Menü (falls verfügbar)
            if es_available and es_manager:
                print("\n🔍 ELASTICSEARCH-FEATURES:")
                print("18. 📊 Daten zu Elasticsearch exportieren")
                print("19. 🔍 Elasticsearch-Dashboard öffnen")
                print("20. 📈 Elasticsearch-Analytics")
                print("21. ⚙️ Elasticsearch-Konfiguration")
                print("22. 🔄 Automatische ES-Synchronisation")
            
            # System-Menü
            print("\n🛠️ SYSTEM & TOOLS:")
            print("23. 🔧 Process Management Terminal")
            print("24. 📦 Batch Processing")
            print("25. 🧹 Datenbank-Wartung")
            print("26. 💾 Backup erstellen")
            print("27. ⚙️ Konfiguration bearbeiten")
            print("0.  👋 Beenden")
            
            # Eingabe
            choice = input(f"\nWählen Sie eine Option (0-27): ").strip()
            
            # ===========================
            # MENU OPTION HANDLERS
            # ===========================
            
            if choice == "0":
                print("\n👋 Auf Wiedersehen!")
                print("🧹 Enhanced Cleanup wird automatisch ausgeführt...")
                break
            
            elif choice == "1":
                # App manuell hinzufügen
                print("\n📱 APP MANUELL HINZUFÜGEN")
                print("=" * 30)
                
                steam_app_id = input("Steam App ID: ").strip()
                if not steam_app_id:
                    print("❌ Ungültige App ID")
                    input("Drücke Enter zum Fortfahren...")
                    continue
                
                print("🔍 Füge App zum Tracking hinzu...")
                success, message = price_tracker.add_app_to_tracking(steam_app_id)
                
                if success:
                    print(f"✅ {message}")
                    
                    # Sofortige Preisaktualisierung anbieten
                    update_now = input("Preise sofort abrufen? (j/n): ").lower().strip()
                    if update_now in ['j', 'ja', 'y', 'yes']:
                        print("🔄 Aktualisiere Preise...")
                        price_tracker.update_price_for_app(steam_app_id)
                        print("✅ Preise aktualisiert!")
                else:
                    print(f"❌ {message}")
                
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "2":
                # Steam Wishlist importieren
                print("\n📥 STEAM WISHLIST IMPORTIEREN")
                print("=" * 35)
                
                if not api_key:
                    print("❌ Steam API Key erforderlich")
                    print("💡 Konfiguriere deinen API Key in der .env-Datei")
                    input("Drücke Enter zum Fortfahren...")
                    continue
                
                steam_id = input("Steam ID oder Profil-URL: ").strip()
                if not steam_id:
                    print("❌ Ungültige Steam ID")
                    input("Drücke Enter zum Fortfahren...")
                    continue
                
                print("🔄 Importiere Wishlist...")
                try:
                    count = price_tracker.import_steam_wishlist(steam_id)
                    if count > 0:
                        print(f"✅ {count} Apps aus Wishlist importiert!")
                        
                        # Sofortige Preisaktualisierung anbieten
                        update_now = input("Preise für alle neuen Apps abrufen? (j/n): ").lower().strip()
                        if update_now in ['j', 'ja', 'y', 'yes']:
                            print("🔄 Aktualisiere alle Preise...")
                            result = price_tracker.update_all_prices()
                            print(f"✅ {result['successful']}/{result['total']} Apps aktualisiert")
                    else:
                        print("ℹ️ Keine neuen Apps gefunden")
                        
                except Exception as e:
                    print(f"❌ Fehler beim Import: {e}")
                
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "3":
                # Aktuelle Preise anzeigen
                print("\n🔍 AKTUELLE PREISE")
                print("=" * 20)
                
                deals = price_tracker.get_current_deals(limit=20)
                
                if deals:
                    print(f"📊 Top {len(deals)} günstigste Apps:")
                    print()
                    
                    for i, deal in enumerate(deals, 1):
                        print(f"{i:2d}. {deal['game_title'][:50]:<50}")
                        print(f"    💰 €{deal['best_price']:.2f} (-{deal['discount_percent']}%) bei {deal['best_store']}")
                        print(f"    🆔 App ID: {deal['steam_app_id']}")
                        print()
                else:
                    print("❌ Keine Deals gefunden")
                    print("💡 Führe zuerst eine Preisaktualisierung durch")
                
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "4":
                # Beste Deals anzeigen
                print("\n📊 BESTE DEALS")
                print("=" * 15)
                
                min_discount = input("Mindest-Rabatt % (Standard: 20): ").strip()
                try:
                    min_discount = int(min_discount) if min_discount else 20
                except ValueError:
                    min_discount = 20
                
                deals = price_tracker.get_best_deals(min_discount_percent=min_discount, limit=20)
                
                if deals:
                    print(f"🎯 Top Deals mit mindestens {min_discount}% Rabatt:")
                    print()
                    
                    for i, deal in enumerate(deals, 1):
                        print(f"{i:2d}. {deal['game_title'][:40]:<40}")
                        print(f"    💰 €{deal['best_price']:.2f} (-{deal['discount_percent']}%) bei {deal['best_store']}")
                        print(f"    🆔 App ID: {deal['steam_app_id']}")
                        print()
                else:
                    print("❌ Keine Deals gefunden")
                
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "5":
                # Preisverlauf anzeigen
                print("\n📈 PREISVERLAUF")
                print("=" * 15)
                
                steam_app_id = input("Steam App ID: ").strip()
                if not steam_app_id:
                    print("❌ Ungültige App ID")
                    input("Drücke Enter zum Fortfahren...")
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
                    
                    for snapshot in history[:10]:
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
                                discount_text = f" (-{discount}%)" if discount > 0 else ""
                                print(f"   💰 {store.upper():12}: €{price:.2f}{discount_text}")
                        print()
                else:
                    print("❌ Kein Preisverlauf gefunden")
                
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "6":
                # Preise manuell aktualisieren
                print("\n🔄 PREISE MANUELL AKTUALISIEREN")
                print("=" * 35)
                
                print("1. Alle Apps aktualisieren")
                print("2. Nur veraltete Apps (älter als 6h)")
                print("3. Einzelne App aktualisieren")
                print("4. Top 50 Apps aktualisieren")
                
                update_choice = input("Wählen Sie eine Option (1-4): ").strip()
                
                if update_choice == "1":
                    print("🔄 Aktualisiere alle Apps...")
                    result = price_tracker.update_all_prices()
                    print(f"✅ {result['successful']}/{result['total']} Apps erfolgreich aktualisiert")
                    
                elif update_choice == "2":
                    print("🔄 Aktualisiere veraltete Apps...")
                    result = price_tracker.process_all_pending_apps_optimized(hours_threshold=6)
                    print(f"✅ {result['total_successful']}/{result['total_apps']} Apps aktualisiert")
                    print(f"⏱️ Dauer: {result['total_duration']:.1f}s")
                    
                elif update_choice == "3":
                    steam_app_id = input("Steam App ID: ").strip()
                    if steam_app_id:
                        print(f"🔄 Aktualisiere App {steam_app_id}...")
                        success = price_tracker.update_price_for_app(steam_app_id)
                        if success:
                            print("✅ App erfolgreich aktualisiert")
                        else:
                            print("❌ Fehler bei der Aktualisierung")
                    
                elif update_choice == "4":
                    print("🔄 Aktualisiere Top 50 Apps...")
                    tracked_apps = price_tracker.get_tracked_apps(limit=50)
                    updated = 0
                    for app in tracked_apps:
                        if price_tracker.update_price_for_app(app['steam_app_id']):
                            updated += 1
                    print(f"✅ {updated}/{len(tracked_apps)} Apps erfolgreich aktualisiert")
                
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "7":
                # Automatisches Tracking starten/stoppen
                print("\n🚀 AUTOMATISCHES TRACKING")
                print("=" * 30)
                
                status = price_tracker.get_scheduler_status()
                
                if status['scheduler_running']:
                    print("✅ Automatisches Tracking ist aktiv")
                    if status.get('next_run'):
                        print(f"⏰ Nächster Lauf: {status['next_run']}")
                    
                    stop = input("Automatisches Tracking stoppen? (j/n): ").lower().strip()
                    if stop in ['j', 'ja', 'y', 'yes']:
                        price_tracker.stop_scheduler()
                        print("⏸️ Automatisches Tracking gestoppt")
                else:
                    print("⏸️ Automatisches Tracking ist inaktiv")
                    
                    start = input("Automatisches Tracking starten? (j/n): ").lower().strip()
                    if start in ['j', 'ja', 'y', 'yes']:
                        interval = input("Intervall in Stunden (Standard: 6): ").strip()
                        try:
                            interval = int(interval) if interval else 6
                        except ValueError:
                            interval = 6
                        
                        print(f"🚀 Starte automatisches Tracking (alle {interval}h)...")
                        price_tracker.start_scheduler(interval_hours=interval)
                        print("✅ Automatisches Tracking gestartet")
                
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "8":
                # Getrackte Apps verwalten
                print("\n📋 GETRACKTE APPS VERWALTEN")
                print("=" * 30)
                
                apps = price_tracker.get_tracked_apps(limit=50)
                
                if apps:
                    print(f"📊 {len(apps)} getrackte Apps (erste 50):")
                    print()
                    
                    for i, app in enumerate(apps, 1):
                        last_update = app.get('last_price_update', 'Nie')
                        if last_update and last_update != 'Nie':
                            last_update = last_update[:16]
                        
                        print(f"{i:2d}. {app['name'][:40]:<40} (ID: {app['steam_app_id']})")
                        print(f"    📅 Hinzugefügt: {app['added_at'][:10]}")
                        print(f"    🔄 Letztes Update: {last_update}")
                        print(f"    📊 Status: {'✅ Aktiv' if app.get('active', True) else '⏸️ Pausiert'}")
                        print()
                else:
                    print("❌ Keine Apps getrackt")
                
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "9":
                # Apps entfernen
                print("\n🗑️ APPS ENTFERNEN")
                print("=" * 20)
                
                steam_app_id = input("Steam App ID zum Entfernen: ").strip()
                if not steam_app_id:
                    print("❌ Ungültige App ID")
                    input("Drücke Enter zum Fortfahren...")
                    continue
                
                # App-Info anzeigen
                apps = price_tracker.get_tracked_apps()
                app_to_remove = None
                for app in apps:
                    if app['steam_app_id'] == steam_app_id:
                        app_to_remove = app
                        break
                
                if app_to_remove:
                    print(f"\n🎯 App gefunden:")
                    print(f"📱 Name: {app_to_remove['name']}")
                    print(f"🆔 ID: {app_to_remove['steam_app_id']}")
                    print(f"📅 Hinzugefügt: {app_to_remove['added_at'][:10]}")
                    
                    confirm = input(f"\nApp wirklich entfernen? (j/n): ").lower().strip()
                    if confirm in ['j', 'ja', 'y', 'yes']:
                        success = price_tracker.remove_app_from_tracking(steam_app_id)
                        if success:
                            print("✅ App erfolgreich entfernt")
                        else:
                            print("❌ Fehler beim Entfernen")
                    else:
                        print("ℹ️ Entfernung abgebrochen")
                else:
                    print("❌ App nicht gefunden")
                
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "10":
                # CSV-Export
                print("\n📄 CSV-EXPORT ERSTELLEN")
                print("=" * 25)
                
                print("1. Einzelne App exportieren")
                print("2. Alle Apps exportieren")
                print("3. Beste Deals exportieren")
                
                export_choice = input("Wählen Sie eine Option (1-3): ").strip()
                
                if export_choice == "1":
                    steam_app_id = input("Steam App ID: ").strip()
                    if steam_app_id:
                        csv_file = price_tracker.export_price_history_csv(steam_app_id)
                        if csv_file:
                            print(f"✅ CSV erstellt: {csv_file}")
                        else:
                            print("❌ Export fehlgeschlagen")
                
                elif export_choice == "2":
                    print("🔄 Exportiere alle Apps...")
                    # Implementierung für Alle-Apps-Export
                    print("💡 Feature in Entwicklung")
                
                elif export_choice == "3":
                    min_discount = input("Mindest-Rabatt % (Standard: 20): ").strip()
                    try:
                        min_discount = int(min_discount) if min_discount else 20
                    except ValueError:
                        min_discount = 20
                    
                    print(f"🔄 Exportiere Deals mit mindestens {min_discount}% Rabatt...")
                    # Implementierung für Deals-Export
                    print("💡 Feature in Entwicklung")
                
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "11":
                # Detaillierte Statistiken
                print("\n📊 DETAILLIERTE STATISTIKEN")
                print("=" * 30)
                
                try:
                    from database_manager import DatabaseManager
                    db = DatabaseManager()
                    stats = db.get_detailed_statistics()
                    
                    print("📈 TRACKING STATISTIKEN:")
                    print(f"🎯 Getrackte Apps: {stats['tracked_apps']}")
                    print(f"💾 Preis-Snapshots: {stats['total_snapshots']:,}")
                    print(f"📅 Letzte Aktualisierung: {stats.get('last_update', 'Nie')}")
                    print(f"🔄 Updates heute: {stats.get('updates_today', 0)}")
                    
                    print(f"\n💰 PREIS STATISTIKEN:")
                    print(f"🏆 Beste Rabatte heute: {stats.get('best_discount_today', 0)}%")
                    print(f"💸 Durchschnittlicher Preis: €{stats.get('average_price', 0):.2f}")
                    print(f"🛒 Apps mit aktiven Rabatten: {stats.get('apps_on_sale', 0)}")
                    
                    if charts_enabled:
                        charts_stats = db.get_charts_statistics()
                        if charts_stats:
                            print(f"\n📊 CHARTS STATISTIKEN:")
                            print(f"🎯 Charts-Apps: {charts_stats.get('total_active_charts_games', 0)}")
                            print(f"📈 Letzte Charts-Update: {charts_stats.get('last_charts_update', 'Nie')}")
                    
                except Exception as e:
                    print(f"❌ Fehler beim Laden der Statistiken: {e}")
                
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "12":
                # System-Tools & Wartung
                print("\n⚙️ SYSTEM-TOOLS & WARTUNG")
                print("=" * 30)
                
                print("1. Datenbank-Statistiken anzeigen")
                print("2. Alte Preisdaten bereinigen")
                print("3. Datenbank optimieren")
                print("4. Backup erstellen")
                print("5. System-Status prüfen")
                print("6. Logs anzeigen")
                
                tool_choice = input("Wählen Sie eine Option (1-6): ").strip()
                
                if tool_choice == "1":
                    # DB-Statistiken
                    try:
                        from database_manager import DatabaseManager
                        db = DatabaseManager()
                        
                        # Tabellen-Größen
                        cursor = db.conn.cursor()
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        tables = cursor.fetchall()
                        
                        print("\n📊 DATENBANK-STATISTIKEN:")
                        for table in tables:
                            table_name = table[0]
                            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                            count = cursor.fetchone()[0]
                            print(f"📋 {table_name}: {count:,} Einträge")
                        
                        # Datenbankgröße
                        db_file = Path("steam_price_tracker.db")
                        if db_file.exists():
                            size_mb = db_file.stat().st_size / 1024 / 1024
                            print(f"💾 Dateigröße: {size_mb:.1f} MB")
                            
                    except Exception as e:
                        print(f"❌ Fehler: {e}")
                
                elif tool_choice == "2":
                    # Alte Daten bereinigen
                    days = input("Bereinige Daten älter als (Tage, Standard: 90): ").strip()
                    try:
                        days = int(days) if days else 90
                    except ValueError:
                        days = 90
                    
                    print(f"🧹 Bereinige Daten älter als {days} Tage...")
                    try:
                        from database_manager import DatabaseManager
                        db = DatabaseManager()
                        deleted = db.cleanup_old_prices(days=days)
                        print(f"✅ {deleted} alte Snapshots entfernt")
                    except Exception as e:
                        print(f"❌ Fehler: {e}")
                
                elif tool_choice == "3":
                    # DB optimieren
                    print("⚡ Optimiere Datenbank...")
                    try:
                        from database_manager import DatabaseManager
                        db = DatabaseManager()
                        db.vacuum_database()
                        print("✅ Datenbank optimiert")
                    except Exception as e:
                        print(f"❌ Fehler: {e}")
                
                elif tool_choice == "4":
                    # Backup
                    print("💾 Erstelle Backup...")
                    try:
                        from database_manager import DatabaseManager
                        db = DatabaseManager()
                        backup_file = db.backup_database()
                        print(f"✅ Backup erstellt: {backup_file}")
                    except Exception as e:
                        print(f"❌ Fehler: {e}")
                
                elif tool_choice == "5":
                    # System-Status
                    print("🔍 SYSTEM-STATUS:")
                    print(f"🐍 Python: {sys.version.split()[0]}")
                    print(f"💻 OS: {os.name}")
                    print(f"📁 Arbeitsverzeichnis: {Path.cwd()}")
                    
                    # Wichtige Dateien prüfen
                    important_files = [
                        "price_tracker.py", "database_manager.py", 
                        "steam_wishlist_manager.py", ".env"
                    ]
                    
                    for file_name in important_files:
                        if Path(file_name).exists():
                            print(f"✅ {file_name}")
                        else:
                            print(f"❌ {file_name} fehlt")
                
                input("Drücke Enter zum Fortfahren...")
            
            # ===========================
            # CHARTS-FEATURES (13-17)
            # ===========================
            
            elif choice == "13" and charts_enabled:
                # Steam Charts anzeigen
                print("\n🏆 STEAM CHARTS")
                print("=" * 15)
                
                print("1. Top Seller")
                print("2. New Releases")
                print("3. Top Played")
                print("4. Alle Charts")
                
                charts_choice = input("Wählen Sie eine Option (1-4): ").strip()
                
                try:
                    if charts_choice == "1":
                        games = price_tracker.get_chart_games("top_sellers", limit=20)
                    elif charts_choice == "2":
                        games = price_tracker.get_chart_games("new_releases", limit=20)
                    elif charts_choice == "3":
                        games = price_tracker.get_chart_games("top_played", limit=20)
                    elif charts_choice == "4":
                        games = price_tracker.get_all_active_chart_games(limit=50)
                    else:
                        games = []
                    
                    if games:
                        print(f"\n📊 {len(games)} Charts-Games:")
                        for i, game in enumerate(games, 1):
                            chart_type = game.get('chart_type', 'Unknown')
                            rank = game.get('current_rank', 'N/A')
                            print(f"{i:2d}. {game['name'][:40]:<40} [{chart_type}] Rang {rank}")
                            print(f"    🆔 App ID: {game['steam_app_id']}")
                    else:
                        print("❌ Keine Charts-Daten gefunden")
                        print("💡 Führe zuerst 'Charts sofort aktualisieren' aus")
                        
                except Exception as e:
                    print(f"❌ Fehler: {e}")
                
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "14" and charts_enabled:
                # Charts sofort aktualisieren
                print("\n📈 CHARTS AKTUALISIEREN")
                print("=" * 25)
                
                print("🔄 Aktualisiere Steam Charts...")
                try:
                    result = price_tracker.update_charts_immediately()
                    if result:
                        print(f"✅ Charts erfolgreich aktualisiert")
                        print(f"📊 {result.get('total_games', 0)} Games verarbeitet")
                        
                        # Automatisch zu Tracking hinzufügen?
                        add_to_tracking = input("Charts-Games automatisch zu Tracking hinzufügen? (j/n): ").lower().strip()
                        if add_to_tracking in ['j', 'ja', 'y', 'yes']:
                            added = price_tracker.add_charts_games_to_tracking()
                            print(f"✅ {added} Charts-Games zu Tracking hinzugefügt")
                    else:
                        print("❌ Charts-Update fehlgeschlagen")
                        
                except Exception as e:
                    print(f"❌ Fehler beim Charts-Update: {e}")
                
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "15" and charts_enabled:
                # Charts-Deals anzeigen
                print("\n🎯 CHARTS-DEALS")
                print("=" * 20)
                
                min_discount = input("Mindest-Rabatt % (Standard: 15): ").strip()
                try:
                    min_discount = int(min_discount) if min_discount else 15
                except ValueError:
                    min_discount = 15
                
                try:
                    deals = price_tracker.get_charts_deals(min_discount_percent=min_discount, limit=20)
                    
                    if deals:
                        print(f"🏆 Charts-Deals mit mindestens {min_discount}% Rabatt:")
                        print()
                        
                        for i, deal in enumerate(deals, 1):
                            rank_info = f"Rang {deal['current_rank']}" if deal.get('current_rank') else ""
                            chart_info = f"[{deal.get('chart_type', 'Unknown')}]"
                            
                            print(f"{i:2d}. {deal['game_title'][:40]:<40} {rank_info} {chart_info}")
                            print(f"    💰 €{deal['best_price']:.2f} (-{deal['discount_percent']}%) bei {deal['best_store']}")
                            print(f"    🆔 App ID: {deal['steam_app_id']}")
                            print()
                    else:
                        print("❌ Keine Charts-Deals gefunden")
                        print("💡 Führe zuerst Charts-Updates und Preisabfragen durch")
                        
                except Exception as e:
                    print(f"❌ Fehler: {e}")
                
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "16" and charts_enabled:
                # Charts-Statistiken
                print("\n📊 CHARTS-STATISTIKEN")
                print("=" * 25)
                
                try:
                    from database_manager import DatabaseManager
                    db = DatabaseManager()
                    
                    if hasattr(db, 'get_charts_statistics'):
                        stats = db.get_charts_statistics()
                        
                        if stats:
                            print("📈 CHARTS ÜBERSICHT:")
                            print(f"🎯 Aktive Charts-Games: {stats.get('total_active_charts_games', 0)}")
                            print(f"📅 Letzte Aktualisierung: {stats.get('last_charts_update', 'Nie')}")
                            
                            if 'active_by_chart_type' in stats:
                                print(f"\n🏆 NACH CHART-TYP:")
                                for chart_type, count in stats['active_by_chart_type'].items():
                                    print(f"📊 {chart_type}: {count} Games")
                            
                            if 'chart_summary' in stats:
                                summary = stats['chart_summary']
                                print(f"\n💰 PREIS-STATISTIKEN:")
                                print(f"💸 Durchschnittspreis: €{summary.get('avg_price', 0):.2f}")
                                print(f"🏆 Bester Rabatt: {summary.get('max_discount', 0)}%")
                                print(f"🛒 Apps im Sale: {summary.get('apps_on_sale', 0)}")
                        else:
                            print("❌ Keine Charts-Statistiken verfügbar")
                    else:
                        print("❌ Charts-Funktionalität nicht verfügbar")
                        
                except Exception as e:
                    print(f"❌ Fehler: {e}")
                
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "17" and charts_enabled:
                # Charts automatisch tracken
                print("\n🔄 CHARTS AUTOMATISCH TRACKEN")
                print("=" * 35)
                
                print("Startet automatisches Charts-Tracking:")
                print("• Alle 4 Stunden Charts-Update")
                print("• Automatische Preisaktualisierung")
                print("• Neue Charts-Games zu Tracking hinzufügen")
                
                start_auto = input("Charts-Autotracking starten? (j/n): ").lower().strip()
                if start_auto in ['j', 'ja', 'y', 'yes']:
                    try:
                        # Implementierung für automatisches Charts-Tracking
                        print("🚀 Startet Charts-Autotracking...")
                        print("💡 Feature in Entwicklung - verwende vorerst Scheduler")
                    except Exception as e:
                        print(f"❌ Fehler: {e}")
                
                input("Drücke Enter zum Fortfahren...")
            
            # ===========================
            # ELASTICSEARCH-FEATURES (18-22)
            # ===========================
            
            elif choice == "18" and es_available and es_manager:
                # Daten zu Elasticsearch exportieren
                print("\n📊 DATEN ZU ELASTICSEARCH EXPORTIEREN")
                print("=" * 45)
                
                if not es_manager.check_connection():
                    print("❌ Elasticsearch nicht erreichbar")
                    print("💡 Starte ELK Stack mit: docker-compose -f docker-compose-elk.yml up")
                    input("Drücke Enter zum Fortfahren...")
                    continue
                
                print("Wählen Sie Daten zum Export:")
                print("1. Alle aktuellen Preise")
                print("2. Preisverlauf (letzte 30 Tage)")
                print("3. Tracking-Apps Metadaten")
                print("4. Charts-Daten (falls verfügbar)")
                print("5. Vollständiger Export")
                
                export_choice = input("Wählen Sie eine Option (1-5): ").strip()
                
                try:
                    if export_choice == "1":
                        print("📊 Exportiere aktuelle Preise...")
                        result = es_manager.export_current_prices()
                        
                    elif export_choice == "2":
                        print("📈 Exportiere Preisverlauf...")
                        result = es_manager.export_price_history(days=30)
                        
                    elif export_choice == "3":
                        print("📋 Exportiere App-Metadaten...")
                        result = es_manager.export_app_metadata()
                        
                    elif export_choice == "4" and charts_enabled:
                        print("🏆 Exportiere Charts-Daten...")
                        result = es_manager.export_charts_data()
                        
                    elif export_choice == "5":
                        print("🔄 Vollständiger Export...")
                        print("⚠️ Dies kann einige Minuten dauern...")
                        result = es_manager.full_export()
                        
                    else:
                        print("❌ Ungültige Auswahl")
                        result = None
                    
                    if result:
                        print(f"✅ Export erfolgreich!")
                        print(f"📊 {result.get('exported_documents', 0)} Dokumente exportiert")
                        print(f"⏱️ Dauer: {result.get('duration', 0):.2f}s")
                    
                except Exception as e:
                    print(f"❌ Export-Fehler: {e}")
                
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "19" and es_available and es_manager:
                # Elasticsearch-Dashboard öffnen
                print("\n🔍 ELASTICSEARCH-DASHBOARD")
                print("=" * 35)
                
                print("Verfügbare Dashboards:")
                print("1. Kibana Dashboard (http://localhost:5601)")
                print("2. Elasticsearch Head (Plugin)")
                print("3. Custom Analytics Dashboard")
                
                dashboard_choice = input("Wählen Sie eine Option (1-3): ").strip()
                
                if dashboard_choice == "1":
                    print("🌐 Öffne Kibana Dashboard...")
                    try:
                        import webbrowser
                        webbrowser.open("http://localhost:5601")
                        print("✅ Kibana sollte sich in Ihrem Browser öffnen")
                        print("💡 Falls nicht: http://localhost:5601")
                    except Exception as e:
                        print(f"❌ Fehler beim Öffnen: {e}")
                        print("💡 Öffnen Sie manuell: http://localhost:5601")
                
                elif dashboard_choice == "2":
                    print("🔌 Elasticsearch Head Plugin...")
                    print("💡 Installieren Sie das Head Plugin für erweiterte Funktionen")
                
                elif dashboard_choice == "3":
                    print("📊 Custom Analytics Dashboard...")
                    print("💡 Feature in Entwicklung")
                
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "20" and es_available and es_manager:
                # Elasticsearch-Analytics
                print("\n📈 ELASTICSEARCH-ANALYTICS")
                print("=" * 35)
                
                if not es_manager.check_connection():
                    print("❌ Elasticsearch nicht erreichbar")
                    input("Drücke Enter zum Fortfahren...")
                    continue
                
                print("Verfügbare Analytics:")
                print("1. Preis-Trends Analyse")
                print("2. Store-Vergleich")
                print("3. Rabatt-Patterns")
                print("4. Top-Spiele Analytics")
                
                analytics_choice = input("Wählen Sie eine Option (1-4): ").strip()
                
                try:
                    if analytics_choice == "1":
                        print("📈 Analysiere Preis-Trends...")
                        analysis = es_manager.analyze_price_trends()
                        
                    elif analytics_choice == "2":
                        print("🏪 Analysiere Store-Vergleich...")
                        analysis = es_manager.analyze_store_comparison()
                        
                    elif analytics_choice == "3":
                        print("💰 Analysiere Rabatt-Patterns...")
                        analysis = es_manager.analyze_discount_patterns()
                        
                    elif analytics_choice == "4":
                        print("🏆 Analysiere Top-Spiele...")
                        analysis = es_manager.analyze_top_games()
                        
                    else:
                        print("❌ Ungültige Auswahl")
                        analysis = None
                    
                    if analysis:
                        print("✅ Analyse abgeschlossen!")
                        print("📊 Ergebnisse verfügbar in Kibana")
                    
                except Exception as e:
                    print(f"❌ Analytics-Fehler: {e}")
                
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "21" and es_available and es_manager:
                # Elasticsearch-Konfiguration
                print("\n⚙️ ELASTICSEARCH-KONFIGURATION")
                print("=" * 40)
                
                print("Konfigurationsoptionen:")
                print("1. Verbindung testen")
                print("2. Indices verwalten")
                print("3. Mappings anzeigen")
                print("4. Cluster-Informationen")
                print("5. Index-Templates erstellen")
                
                config_choice = input("Wählen Sie eine Option (1-5): ").strip()
                
                try:
                    if config_choice == "1":
                        print("🔍 Teste Elasticsearch-Verbindung...")
                        if es_manager.check_connection():
                            stats = es_manager.get_cluster_stats()
                            print("✅ Verbindung erfolgreich!")
                            print(f"📊 Cluster: {stats.get('cluster_name', 'unknown')}")
                            print(f"📈 Status: {stats.get('status', 'unknown')}")
                        else:
                            print("❌ Verbindung fehlgeschlagen")
                    
                    elif config_choice == "2":
                        print("📋 Index-Management...")
                        indices = es_manager.list_indices()
                        if indices:
                            print("Verfügbare Indices:")
                            for index in indices:
                                print(f"  📊 {index}")
                        else:
                            print("❌ Keine Indices gefunden")
                    
                    elif config_choice == "3":
                        print("🗺️ Index-Mappings...")
                        mappings = es_manager.get_mappings()
                        print("💡 Mappings verfügbar in Kibana Dev Tools")
                    
                    elif config_choice == "4":
                        print("ℹ️ Cluster-Informationen...")
                        info = es_manager.get_cluster_info()
                        if info:
                            print(f"📊 Cluster: {info.get('cluster_name', 'unknown')}")
                            print(f"🆔 UUID: {info.get('cluster_uuid', 'unknown')}")
                            print(f"📈 Version: {info.get('version', {}).get('number', 'unknown')}")
                    
                    elif config_choice == "5":
                        print("📋 Erstelle Index-Templates...")
                        es_manager.create_templates()
                        print("✅ Templates erstellt!")
                
                except Exception as e:
                    print(f"❌ Konfigurations-Fehler: {e}")
                
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "22" and es_available and es_manager:
                # Automatische ES-Synchronisation
                print("\n🔄 AUTOMATISCHE ELASTICSEARCH-SYNCHRONISATION")
                print("=" * 55)
                
                print("Konfiguriere automatische Synchronisation:")
                print("• Regelmäßiger Export zu Elasticsearch")
                print("• Automatische Index-Wartung")
                print("• Real-time Data Streaming")
                
                print("\n1. Synchronisation starten")
                print("2. Synchronisation stoppen")
                print("3. Sync-Status anzeigen")
                print("4. Sync-Einstellungen")
                
                sync_choice = input("Wählen Sie eine Option (1-4): ").strip()
                
                try:
                    if sync_choice == "1":
                        interval = input("Sync-Intervall in Minuten (Standard: 30): ").strip()
                        try:
                            interval = int(interval) if interval else 30
                        except ValueError:
                            interval = 30
                        
                        print(f"🚀 Starte automatische Sync (alle {interval} Min)...")
                        es_manager.start_auto_sync(interval_minutes=interval)
                        print("✅ Automatische Synchronisation gestartet")
                        
                    elif sync_choice == "2":
                        print("⏸️ Stoppe automatische Synchronisation...")
                        es_manager.stop_auto_sync()
                        print("✅ Synchronisation gestoppt")
                        
                    elif sync_choice == "3":
                        print("📊 Sync-Status...")
                        status = es_manager.get_sync_status()
                        if status:
                            print(f"🔄 Status: {status.get('running', 'Unbekannt')}")
                            print(f"⏰ Letzter Sync: {status.get('last_sync', 'Nie')}")
                            print(f"📊 Synced Docs: {status.get('synced_docs', 0)}")
                        
                    elif sync_choice == "4":
                        print("⚙️ Sync-Einstellungen...")
                        print("💡 Konfiguration über elasticsearch_manager.py")
                
                except Exception as e:
                    print(f"❌ Sync-Fehler: {e}")
                
                input("Drücke Enter zum Fortfahren...")
            
            # ===========================
            # SYSTEM & TOOLS (23-27)
            # ===========================
            
            elif choice == "23":
                # Process Management Terminal
                print("\n🔧 PROCESS MANAGEMENT TERMINAL")
                print("=" * 40)
                
                print("Startet Enhanced Process Management Terminal...")
                print("• Überwacht alle Steam Price Tracker Prozesse")
                print("• Zeigt Ressourcenverbrauch in Echtzeit")
                print("• Ermöglicht kontrollierten Prozess-Stop")
                print()
                
                start_terminal = input("Process Management Terminal starten? (j/n): ").lower().strip()
                if start_terminal in ['j', 'ja', 'y', 'yes']:
                    start_process_management_terminal()
                
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "24":
                # Batch Processing
                print("\n📦 BATCH PROCESSING")
                print("=" * 25)
                
                print("Verfügbare Batch-Operationen:")
                print("1. Batch-Preisaktualisierung (optimiert)")
                print("2. Batch-App-Import aus CSV")
                print("3. Batch-CSV-Export")
                print("4. Batch-Datenbereinigung")
                
                batch_choice = input("Wählen Sie eine Option (1-4): ").strip()
                
                if batch_choice == "1":
                    print("\n🔄 BATCH-PREISAKTUALISIERUNG")
                    hours_old = input("Apps älter als Stunden (Standard: 6): ").strip()
                    try:
                        hours_old = int(hours_old) if hours_old else 6
                    except ValueError:
                        hours_old = 6
                    
                    print(f"🚀 Starte optimierte Batch-Aktualisierung...")
                    result = price_tracker.process_all_pending_apps_optimized(hours_threshold=hours_old)
                    
                    print(f"\n📊 BATCH-ERGEBNIS:")
                    print(f"✅ Erfolgreich: {result['total_successful']}")
                    print(f"❌ Fehlgeschlagen: {result['total_failed']}")
                    print(f"📈 Gesamt: {result['total_apps']}")
                    print(f"⏱️ Dauer: {result['total_duration']:.1f}s")
                    print(f"⚡ Apps/Sekunde: {result['apps_per_second']:.1f}")
                
                elif batch_choice == "2":
                    print("\n📥 BATCH-APP-IMPORT")
                    csv_file = input("CSV-Datei Pfad: ").strip()
                    if csv_file and Path(csv_file).exists():
                        print(f"🔄 Importiere Apps aus {csv_file}...")
                        print("💡 Feature in Entwicklung")
                    else:
                        print("❌ CSV-Datei nicht gefunden")
                
                elif batch_choice == "3":
                    print("\n📄 BATCH-CSV-EXPORT")
                    print("🔄 Exportiere alle getrackte Apps...")
                    print("💡 Feature in Entwicklung")
                
                elif batch_choice == "4":
                    print("\n🧹 BATCH-DATENBEREINIGUNG")
                    days = input("Bereinige Daten älter als Tage (Standard: 90): ").strip()
                    try:
                        days = int(days) if days else 90
                    except ValueError:
                        days = 90
                    
                    print(f"🧹 Starte Batch-Bereinigung...")
                    try:
                        from database_manager import DatabaseManager
                        db = DatabaseManager()
                        deleted = db.cleanup_old_prices(days=days)
                        db.vacuum_database()
                        print(f"✅ {deleted} alte Einträge entfernt")
                        print("✅ Datenbank optimiert")
                    except Exception as e:
                        print(f"❌ Fehler: {e}")
                
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "25":
                # Datenbank-Wartung
                print("\n🧹 DATENBANK-WARTUNG")
                print("=" * 25)
                
                print("Verfügbare Wartungsoptionen:")
                print("1. Datenbank-Integrität prüfen")
                print("2. Indizes neu erstellen")
                print("3. Verwaiste Einträge bereinigen")
                print("4. Datenbank-Analyse")
                print("5. Vollständige Optimierung")
                
                maintenance_choice = input("Wählen Sie eine Option (1-5): ").strip()
                
                try:
                    from database_manager import DatabaseManager
                    db = DatabaseManager()
                    
                    if maintenance_choice == "1":
                        print("🔍 Prüfe Datenbank-Integrität...")
                        print("💡 SQLite PRAGMA integrity_check")
                        cursor = db.conn.cursor()
                        cursor.execute("PRAGMA integrity_check")
                        result = cursor.fetchone()[0]
                        if result == "ok":
                            print("✅ Datenbank-Integrität: OK")
                        else:
                            print(f"⚠️ Integrität: {result}")
                    
                    elif maintenance_choice == "2":
                        print("🔄 Erstelle Indizes neu...")
                        cursor = db.conn.cursor()
                        cursor.execute("REINDEX")
                        print("✅ Indizes neu erstellt")
                    
                    elif maintenance_choice == "3":
                        print("🧹 Bereinige verwaiste Einträge...")
                        # Implementierung für Orphan Cleanup
                        print("💡 Feature in Entwicklung")
                    
                    elif maintenance_choice == "4":
                        print("📊 Datenbank-Analyse...")
                        cursor = db.conn.cursor()
                        cursor.execute("PRAGMA table_info(tracked_apps)")
                        print("📋 tracked_apps Schema:")
                        for row in cursor.fetchall():
                            print(f"  {row[1]} ({row[2]})")
                    
                    elif maintenance_choice == "5":
                        print("⚡ Vollständige Optimierung...")
                        print("1. Bereinigung alter Daten...")
                        deleted = db.cleanup_old_prices(days=90)
                        print(f"   ✅ {deleted} alte Einträge entfernt")
                        
                        print("2. Vacuum-Operation...")
                        db.vacuum_database()
                        print("   ✅ Vacuum abgeschlossen")
                        
                        print("3. Index-Optimierung...")
                        cursor = db.conn.cursor()
                        cursor.execute("REINDEX")
                        print("   ✅ Indizes optimiert")
                        
                        print("✅ Vollständige Optimierung abgeschlossen")
                
                except Exception as e:
                    print(f"❌ Wartungs-Fehler: {e}")
                
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "26":
                # Backup erstellen
                print("\n💾 BACKUP ERSTELLEN")
                print("=" * 20)
                
                print("Backup-Optionen:")
                print("1. Datenbank-Backup")
                print("2. Vollständiges System-Backup")
                print("3. Konfiguration-Backup")
                print("4. Elasticsearch-Backup (falls verfügbar)")
                
                backup_choice = input("Wählen Sie eine Option (1-4): ").strip()
                
                try:
                    if backup_choice == "1":
                        print("💾 Erstelle Datenbank-Backup...")
                        from database_manager import DatabaseManager
                        db = DatabaseManager()
                        backup_file = db.backup_database()
                        print(f"✅ Datenbank-Backup: {backup_file}")
                    
                    elif backup_choice == "2":
                        print("💾 Erstelle vollständiges System-Backup...")
                        backup_dir = Path(f"backups/full_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                        backup_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Wichtige Dateien kopieren
                        important_files = [
                            "steam_price_tracker.db", ".env", "config.json",
                            "price_tracker.py", "database_manager.py", 
                            "steam_wishlist_manager.py"
                        ]
                        
                        backed_up = 0
                        for file_name in important_files:
                            file_path = Path(file_name)
                            if file_path.exists():
                                import shutil
                                shutil.copy2(file_path, backup_dir / file_name)
                                backed_up += 1
                        
                        print(f"✅ System-Backup: {backup_dir}")
                        print(f"📁 {backed_up} Dateien gesichert")
                    
                    elif backup_choice == "3":
                        print("💾 Erstelle Konfiguration-Backup...")
                        config_backup_dir = Path(f"backups/config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                        config_backup_dir.mkdir(parents=True, exist_ok=True)
                        
                        config_files = [".env", "config.json"]
                        for file_name in config_files:
                            file_path = Path(file_name)
                            if file_path.exists():
                                import shutil
                                shutil.copy2(file_path, config_backup_dir / file_name)
                        
                        print(f"✅ Konfigurations-Backup: {config_backup_dir}")
                    
                    elif backup_choice == "4" and es_available and es_manager:
                        print("💾 Erstelle Elasticsearch-Backup...")
                        if es_manager.check_connection():
                            snapshot_name = f"steam_tracker_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            result = es_manager.create_snapshot(snapshot_name)
                            if result:
                                print(f"✅ Elasticsearch-Backup: {snapshot_name}")
                            else:
                                print("❌ Elasticsearch-Backup fehlgeschlagen")
                        else:
                            print("❌ Elasticsearch nicht erreichbar")
                
                except Exception as e:
                    print(f"❌ Backup-Fehler: {e}")
                
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "27":
                # Konfiguration bearbeiten
                print("\n⚙️ KONFIGURATION BEARBEITEN")
                print("=" * 30)
                
                print("Konfigurationsdateien:")
                print("1. .env-Datei bearbeiten")
                print("2. config.json bearbeiten")
                print("3. Elasticsearch-Config")
                print("4. Konfiguration anzeigen")
                
                config_choice = input("Wählen Sie eine Option (1-4): ").strip()
                
                if config_choice == "1":
                    print("\n📝 .ENV-DATEI:")
                    env_file = Path(".env")
                    if env_file.exists():
                        print("Aktuelle .env-Konfiguration:")
                        with open(env_file, 'r', encoding='utf-8') as f:
                            for line_num, line in enumerate(f, 1):
                                if not line.strip().startswith('#') and '=' in line:
                                    key, value = line.strip().split('=', 1)
                                    # API Key maskieren
                                    if 'API_KEY' in key and value and value != 'your_steam_api_key_here':
                                        value = value[:8] + "..." if len(value) > 8 else "***"
                                    print(f"  {line_num}. {key}={value}")
                        
                        print("\n💡 Bearbeite .env-Datei manuell für Änderungen")
                    else:
                        print("❌ .env-Datei nicht gefunden")
                
                elif config_choice == "2":
                    print("\n📝 CONFIG.JSON:")
                    config_file = Path("config.json")
                    if config_file.exists():
                        try:
                            import json
                            with open(config_file, 'r', encoding='utf-8') as f:
                                config = json.load(f)
                            
                            print("Aktuelle Konfiguration:")
                            print(json.dumps(config, indent=2, ensure_ascii=False))
                        except Exception as e:
                            print(f"❌ Fehler beim Lesen: {e}")
                    else:
                        print("❌ config.json nicht gefunden")
                
                elif config_choice == "3" and es_available:
                    print("\n📝 ELASTICSEARCH-CONFIG:")
                    print("💡 Elasticsearch-Konfiguration über docker-compose-elk.yml")
                    
                elif config_choice == "4":
                    print("\n📊 AKTUELLE KONFIGURATION:")
                    print(f"🐍 Python: {sys.version.split()[0]}")
                    print(f"📁 Arbeitsverzeichnis: {Path.cwd()}")
                    print(f"📊 Charts: {'✅ Verfügbar' if charts_enabled else '❌ Nicht verfügbar'}")
                    print(f"🔍 Elasticsearch: {'✅ Verfügbar' if es_available else '❌ Nicht verfügbar'}")
                    
                    # API Key Status
                    if api_key:
                        masked_key = api_key[:8] + "..." if len(api_key) > 8 else "***"
                        print(f"🔑 Steam API Key: {masked_key}")
                    else:
                        print(f"🔑 Steam API Key: ❌ Nicht konfiguriert")
                
                input("Drücke Enter zum Fortfahren...")
            
            else:
                print("❌ Ungültige Auswahl. Bitte wählen Sie eine Option zwischen 0-27.")
                input("Drücke Enter zum Fortfahren...")
                continue
                
        except KeyboardInterrupt:
            print("\n\n🛑 Strg+C erkannt - Enhanced Cleanup wird ausgeführt...")
            break
        except Exception as e:
            print(f"\n❌ Unerwarteter Fehler: {e}")
            print("💡 Das Programm wird fortgesetzt...")
            input("Drücke Enter zum Fortfahren...")
            continue

    # Enhanced Cleanup wird automatisch durch atexit aufgerufen
    print("🏁 Enhanced Steam Price Tracker v3.0 beendet")

if __name__ == "__main__":
    main()