#!/usr/bin/env python3
"""
Steam Price Tracker - Main Interface
VOLLSTÄNDIG INTEGRIERTE VERSION mit allen Features
Behält bestehende Menüstruktur bei + integriert alle CLI-Tools und Process Management
"""

import sys
import os
import json
import time
import atexit
import subprocess
from pathlib import Path
from datetime import datetime
import logging

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =====================================================================
# ENHANCED CLEANUP & PROCESS MANAGEMENT
# =====================================================================

def enhanced_cleanup():
    """Enhanced Cleanup für alle Background-Prozesse"""
    try:
        logger.info("🧹 Enhanced Cleanup...")
        
        try:
            from background_scheduler import _global_process_manager
            if _global_process_manager:
                stopped = _global_process_manager.cleanup_all_processes()
                logger.info(f"✅ {stopped} Background-Prozesse gestoppt")
        except Exception as e:
            logger.debug(f"Process Manager Cleanup: {e}")
        
        # Temporäre Dateien aufräumen
        temp_dirs = ["temp_schedulers", "temp_scripts"]
        for temp_dir in temp_dirs:
            temp_path = Path(temp_dir)
            if temp_path.exists():
                try:
                    import shutil
                    shutil.rmtree(temp_path)
                    logger.debug(f"🗑️ Temporäre Dateien entfernt: {temp_dir}")
                except Exception as e:
                    logger.debug(f"Temp cleanup error: {e}")
        
        logger.info("✅ Enhanced Cleanup abgeschlossen")
    except Exception as e:
        logger.debug(f"Enhanced Cleanup Fehler: {e}")

atexit.register(enhanced_cleanup)

# =====================================================================
# CHARTS-KONFIGURATION (minimal - wie ursprünglich geplant)
# =====================================================================

def load_charts_config():
    """Lädt Charts-Konfiguration aus config.json"""
    try:
        config_file = Path("config.json")
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            return config.get('charts', {
                'update_interval_hours': 6,
                'price_interval_hours': 4,
                'cleanup_interval_hours': 24,
                'enabled': False,
                'chart_types': ['most_played', 'top_releases', 'best_sellers']
            })
        else:
            return {
                'update_interval_hours': 6,
                'price_interval_hours': 4,
                'cleanup_interval_hours': 24,
                'enabled': False,
                'chart_types': ['most_played', 'top_releases', 'best_sellers']
            }
    except Exception as e:
        logger.error(f"Fehler beim Laden der Charts-Config: {e}")
        return {
            'update_interval_hours': 6,
            'price_interval_hours': 4,
            'cleanup_interval_hours': 24,
            'enabled': False,
            'chart_types': ['most_played', 'top_releases', 'best_sellers']
        }

def save_charts_config(charts_config):
    """Speichert Charts-Konfiguration in config.json"""
    try:
        config_file = Path("config.json")
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}
        
        config['charts'] = charts_config
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Charts-Config: {e}")
        return False

def configure_charts_intervals(price_tracker, charts_config):
    """Konfiguriert Charts-Tracking-Intervalle (Menüpunkt 17)"""
    print("\n📊 CHARTS-INTERVALLE KONFIGURIEREN")
    print("=" * 50)
    print("💡 Konfiguriere die Intervalle für automatisches Charts-Tracking")
    print()
    
    # Aktuelle Werte anzeigen
    print("🔧 AKTUELLE EINSTELLUNGEN:")
    print(f"   📈 Charts-Updates: alle {charts_config['update_interval_hours']} Stunden")
    print(f"   💰 Preis-Updates: alle {charts_config['price_interval_hours']} Stunden") 
    print(f"   🧹 Cleanup: alle {charts_config['cleanup_interval_hours']} Stunden")
    print(f"   ✅ Status: {'Aktiviert' if charts_config['enabled'] else 'Deaktiviert'}")
    print()
    
    try:
        print("⚙️ NEUE INTERVALLE EINGEBEN:")
        print("💡 Drücke Enter um aktuelle Werte zu behalten")
        
        # Charts-Update Intervall
        while True:
            update_input = input(f"📈 Charts-Update Intervall (Stunden, aktuell {charts_config['update_interval_hours']}): ").strip()
            if not update_input:
                break
            try:
                update_hours = int(update_input)
                if 1 <= update_hours <= 168:
                    charts_config['update_interval_hours'] = update_hours
                    break
                else:
                    print("❌ Bitte einen Wert zwischen 1 und 168 eingeben")
            except ValueError:
                print("❌ Bitte eine gültige Zahl eingeben")
        
        # Preis-Update Intervall
        while True:
            price_input = input(f"💰 Preis-Update Intervall (Stunden, aktuell {charts_config['price_interval_hours']}): ").strip()
            if not price_input:
                break
            try:
                price_hours = int(price_input)
                if 1 <= price_hours <= 48:
                    charts_config['price_interval_hours'] = price_hours
                    break
                else:
                    print("❌ Bitte einen Wert zwischen 1 und 48 eingeben")
            except ValueError:
                print("❌ Bitte eine gültige Zahl eingeben")
        
        # Cleanup-Intervall
        while True:
            cleanup_input = input(f"🧹 Cleanup Intervall (Stunden, aktuell {charts_config['cleanup_interval_hours']}): ").strip()
            if not cleanup_input:
                break
            try:
                cleanup_hours = int(cleanup_input)
                if 6 <= cleanup_hours <= 168:
                    charts_config['cleanup_interval_hours'] = cleanup_hours
                    break
                else:
                    print("❌ Bitte einen Wert zwischen 6 und 168 eingeben")
            except ValueError:
                print("❌ Bitte eine gültige Zahl eingeben")
        
        print("\n✅ NEUE KONFIGURATION:")
        print(f"   📈 Charts-Updates: alle {charts_config['update_interval_hours']} Stunden")
        print(f"   💰 Preis-Updates: alle {charts_config['price_interval_hours']} Stunden")
        print(f"   🧹 Cleanup: alle {charts_config['cleanup_interval_hours']} Stunden")
        
        # Konfiguration speichern
        if save_charts_config(charts_config):
            print("💾 Konfiguration gespeichert!")
        
        # Charts-Tracking aktivieren/neu starten
        enable_choice = input("\n🚀 Charts-Tracking jetzt aktivieren? (j/n): ").lower().strip()
        if enable_choice in ['j', 'ja', 'y', 'yes']:
            activate_charts_tracking(price_tracker, charts_config)
        
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️ Konfiguration abgebrochen")
        return False
    except Exception as e:
        print(f"❌ Fehler bei der Konfiguration: {e}")
        return False

def configure_charts_advanced(price_tracker, charts_config):
    """Erweiterte Charts-Konfiguration (Menüpunkt 18)"""
    print("\n📊 ERWEITERTE CHARTS-KONFIGURATION")
    print("=" * 50)
    print("💡 Konfiguriere Chart-Typen und -Anzahlen")
    print()
    
    try:
        available_charts = {
            'most_played': 'Meistgespielte Spiele',
            'top_releases': 'Top Neue Releases',
            'best_sellers': 'Bestseller',
            'weekly_top_sellers': 'Wöchentliche Bestseller'
        }
        
        print("📋 VERFÜGBARE CHART-TYPEN:")
        for key, desc in available_charts.items():
            enabled = "✅" if key in charts_config['chart_types'] else "❌"
            print(f"   {enabled} {key}: {desc}")
        print()
        
        print("⚙️ CHART-TYPEN AKTIVIEREN/DEAKTIVIEREN:")
        new_chart_types = []
        
        for key, desc in available_charts.items():
            current = key in charts_config['chart_types']
            default = "j" if current else "n"
            choice = input(f"📊 {desc} aktivieren? (j/n, aktuell: {'✅' if current else '❌'}): ").strip().lower()
            
            if not choice:
                choice = default
            
            if choice in ['j', 'ja', 'y', 'yes']:
                new_chart_types.append(key)
        
        charts_config['chart_types'] = new_chart_types
        print(f"✅ Chart-Typen aktualisiert: {len(new_chart_types)} aktiviert")
        
        # Konfiguration speichern
        if save_charts_config(charts_config):
            print("💾 Erweiterte Konfiguration gespeichert!")
        
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️ Konfiguration abgebrochen")
        return False
    except Exception as e:
        print(f"❌ Fehler bei der erweiterten Konfiguration: {e}")
        return False

def activate_charts_tracking(price_tracker, charts_config):
    """Aktiviert Charts-Tracking mit konfigurierten Intervallen"""
    try:
        if not price_tracker.charts_enabled:
            print("❌ Charts-Funktionalität nicht verfügbar")
            print("💡 Stelle sicher, dass ein Steam API Key konfiguriert ist")
            return False
        
        print("\n🚀 Aktiviere Charts-Tracking...")
        
        # Charts-Tracking mit neuen Intervallen aktivieren
        success = price_tracker.enable_charts_tracking(
            charts_update_hours=charts_config['update_interval_hours'],
            price_update_hours=charts_config['price_interval_hours'],
            cleanup_hours=charts_config['cleanup_interval_hours']
        )
        
        if success:
            charts_config['enabled'] = True
            save_charts_config(charts_config)
            
            print("✅ Charts-Tracking erfolgreich aktiviert!")
            print()
            print("📋 AKTIVE SCHEDULER:")
            print(f"   📊 Charts-Updates: alle {charts_config['update_interval_hours']} Stunden")
            print(f"   💰 Preis-Updates: alle {charts_config['price_interval_hours']} Stunden")
            print(f"   🧹 Cleanup: alle {charts_config['cleanup_interval_hours']} Stunden")
            print()
            print("💡 Das Charts-Tracking läuft nun automatisch im Hintergrund!")
            
            return True
        else:
            print("❌ Fehler beim Aktivieren des Charts-Trackings")
            return False
            
    except Exception as e:
        print(f"❌ Fehler beim Aktivieren: {e}")
        return False

# =====================================================================
# PROCESS MANAGEMENT TERMINAL (neu integriert)
# =====================================================================

def start_process_management_terminal():
    """Startet Enhanced Process Management Terminal"""
    try:
        print("\n🔧 PROCESS MANAGEMENT TERMINAL")
        print("=" * 40)
        print("💡 Startet separates Terminal für Prozess-Überwachung...")
        
        from background_scheduler import create_process_management_terminal
        
        if create_process_management_terminal():
            print("✅ Process Management Terminal gestartet!")
            print("💡 Ein separates Terminal-Fenster wurde geöffnet")
            print("💡 Dort kannst du alle Background-Prozesse überwachen")
            return True
        else:
            print("❌ Fehler beim Starten des Process Management Terminals")
            return False
            
    except ImportError:
        print("❌ Background Scheduler Module nicht gefunden")
        return False
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False

# =====================================================================
# CLI-TOOLS INTEGRATION (neu)
# =====================================================================

def show_available_cli_tools():
    """Zeigt verfügbare CLI-Tools an"""
    print("\n🛠️ VERFÜGBARE CLI-TOOLS")
    print("=" * 40)
    
    cli_tools = [
        ("batch_processor.py", "Batch-Processing Tools", [
            "python batch_processor.py status",
            "python batch_processor.py batch --hours 6",
            "python batch_processor.py update-names"
        ]),
        ("charts_cli_manager.py", "Charts-Management CLI", [
            "python charts_cli_manager.py status",
            "python charts_cli_manager.py enable",
            "python charts_cli_manager.py update"
        ]),
        ("elasticsearch_setup.py", "Elasticsearch-Integration", [
            "python elasticsearch_setup.py status",
            "python elasticsearch_setup.py export",
            "python elasticsearch_setup.py setup"
        ])
    ]
    
    for tool_file, description, commands in cli_tools:
        tool_path = Path(tool_file)
        if tool_path.exists():
            print(f"✅ {description}")
            print(f"   📁 Datei: {tool_file}")
            print("   🚀 Beispiele:")
            for cmd in commands:
                print(f"      {cmd}")
            print()
        else:
            print(f"❌ {description}")
            print(f"   📁 Datei fehlt: {tool_file}")
            print("   💡 Führe 'python setup.py full' aus um alle Tools zu installieren")
            print()

def launch_cli_tool():
    """Ermöglicht das Starten von CLI-Tools"""
    print("\n🚀 CLI-TOOL STARTEN")
    print("=" * 30)
    
    available_tools = []
    cli_tools = [
        ("batch_processor.py", "Batch Processing"),
        ("charts_cli_manager.py", "Charts CLI"),
        ("elasticsearch_setup.py", "Elasticsearch Setup")
    ]
    
    print("📋 VERFÜGBARE TOOLS:")
    for i, (tool_file, description) in enumerate(cli_tools, 1):
        if Path(tool_file).exists():
            print(f"{i}. ✅ {description} ({tool_file})")
            available_tools.append((i, tool_file, description))
        else:
            print(f"{i}. ❌ {description} ({tool_file}) - nicht verfügbar")
    
    if not available_tools:
        print("\n❌ Keine CLI-Tools verfügbar")
        print("💡 Führe 'python setup.py full' aus um alle Tools zu installieren")
        return
    
    print()
    try:
        choice = input("Wähle ein Tool (Nummer) oder Enter zum Abbrechen: ").strip()
        if not choice:
            return
        
        choice_num = int(choice)
        selected_tool = None
        
        for num, tool_file, description in available_tools:
            if num == choice_num:
                selected_tool = (tool_file, description)
                break
        
        if not selected_tool:
            print("❌ Ungültige Auswahl")
            return
        
        tool_file, description = selected_tool
        command = input(f"🚀 Kommando für {description} (z.B. 'status'): ").strip()
        
        if command:
            full_command = f"python {tool_file} {command}"
            print(f"\n🔄 Führe aus: {full_command}")
            
            try:
                result = subprocess.run(full_command.split(), capture_output=True, text=True, cwd=Path.cwd())
                
                print("\n📤 OUTPUT:")
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print("❌ ERRORS:")
                    print(result.stderr)
                
                print(f"\n✅ Beendet mit Exit-Code: {result.returncode}")
                
            except Exception as e:
                print(f"❌ Fehler beim Ausführen: {e}")
        
    except ValueError:
        print("❌ Bitte eine gültige Nummer eingeben")
    except KeyboardInterrupt:
        print("\n⏹️ Abgebrochen")

# =====================================================================
# SYSTEM STATUS & TOOLS (erweitert)
# =====================================================================

def show_extended_system_status():
    """Zeigt erweiterten System-Status mit allen verfügbaren Features"""
    print("\n📊 ERWEITERTE SYSTEM-ÜBERSICHT")
    print("=" * 50)
    
    # Python & System
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"📁 Arbeitsverzeichnis: {Path.cwd()}")
    print()
    
    # Kern-Module
    print("🔧 KERN-MODULE:")
    core_modules = [
        ("price_tracker.py", "Price Tracker Core"),
        ("database_manager.py", "Database Manager"),
        ("steam_wishlist_manager.py", "Steam Wishlist"),
        ("background_scheduler.py", "Background Scheduler")
    ]
    
    for module_file, description in core_modules:
        status = "✅" if Path(module_file).exists() else "❌"
        print(f"   {status} {description}")
    
    print()
    
    # Erweiterte Module
    print("📊 ERWEITERTE MODULE:")
    extended_modules = [
        ("steam_charts_manager.py", "Steam Charts Manager"),
        ("charts_cli_manager.py", "Charts CLI Tools"),
        ("batch_processor.py", "Batch Processing"),
        ("elasticsearch_manager.py", "Elasticsearch Integration")
    ]
    
    for module_file, description in extended_modules:
        status = "✅" if Path(module_file).exists() else "❌"
        print(f"   {status} {description}")
    
    print()
    
    # Konfiguration
    print("⚙️ KONFIGURATION:")
    env_file = Path(".env")
    config_file = Path("config.json")
    
    print(f"   {'✅' if env_file.exists() else '❌'} .env-Datei")
    print(f"   {'✅' if config_file.exists() else '❌'} config.json")
    
    # API Key Status
    try:
        from steam_wishlist_manager import load_api_key_from_env
        api_key = load_api_key_from_env()
        if api_key:
            masked_key = api_key[:8] + "..." if len(api_key) > 8 else "***"
            print(f"   🔑 Steam API Key: {masked_key}")
        else:
            print(f"   🔑 Steam API Key: ❌ Nicht konfiguriert")
    except Exception:
        print(f"   🔑 Steam API Key: ❌ Fehler beim Laden")
    
    print()
    
    # Background Processes
    print("🔄 BACKGROUND PROCESSES:")
    try:
        from background_scheduler import _global_process_manager
        if _global_process_manager:
            status = _global_process_manager.get_process_status()
            print(f"   📊 Getrackte Prozesse: {status['total_tracked']}")
            print(f"   ✅ Laufende Prozesse: {status['running_processes']}")
            print(f"   💀 Gestoppte Prozesse: {status['dead_processes']}")
        else:
            print("   ⚠️ Process Manager nicht initialisiert")
    except Exception as e:
        print(f"   ❌ Process Manager Fehler: {e}")

# =====================================================================
# MAIN PROGRAM - BEHÄLT STRUKTUR BEI + INTEGRIERT ALLE FEATURES
# =====================================================================

def main():
    """Hauptfunktion - erweitert um alle verfügbaren Features"""
    print("🚀 ENHANCED STEAM PRICE TRACKER v3.0")
    print("=" * 60)
    print("⚡ Initialisiere System mit vollständiger Integration...")
    print()
    
    # Price Tracker laden
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        
        # API Key laden
        api_key = load_api_key_from_env()
        if not api_key:
            print("⚠️ Kein Steam API Key in .env gefunden")
            print("💡 Einige Features (Charts, Namen-Updates) sind nicht verfügbar")
            api_key = None
        
        # Price Tracker erstellen
        price_tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        charts_enabled = price_tracker.charts_enabled
        
        print(f"✅ Price Tracker initialisiert")
        if charts_enabled:
            print(f"📊 Charts-Integration: VERFÜGBAR")
        else:
            print(f"📊 Charts-Integration: NICHT VERFÜGBAR")
            
    except Exception as e:
        print(f"❌ Fehler beim Initialisieren des Price Trackers: {e}")
        return
    
    # Charts-Konfiguration laden
    charts_config = load_charts_config()
    
    print("🔧 System bereit!")
    print()
    time.sleep(2)
    
    # ===========================
    # HAUPT-MENÜ-SCHLEIFE (ORIGINAL + ERWEITERT)
    # ===========================
    
    while True:
        try:
            # Clear screen
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # Header
            print("🚀 ENHANCED STEAM PRICE TRACKER v3.0")
            print("=" * 60)
            print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Status anzeigen (SAFE VERSION)
            try:
                from database_manager import DatabaseManager
                db = DatabaseManager()
                
                # SAFE Statistiken
                tracked_apps = price_tracker.get_tracked_apps()
                print(f"\n📊 AKTUELLER STATUS:")
                print(f"🎯 Getrackte Apps: {len(tracked_apps) if tracked_apps else 0}")
                
                # Scheduler Status (safe)
                try:
                    if hasattr(price_tracker, 'get_enhanced_scheduler_status'):
                        scheduler_status = price_tracker.get_enhanced_scheduler_status()
                        if scheduler_status.get('scheduler_running'):
                            print(f"🔄 Automatisches Tracking: AKTIV")
                        else:
                            print(f"⏸️ Automatisches Tracking: INAKTIV")
                    elif hasattr(price_tracker, 'is_scheduler_running'):
                        if price_tracker.is_scheduler_running():
                            print(f"🔄 Automatisches Tracking: AKTIV")
                        else:
                            print(f"⏸️ Automatisches Tracking: INAKTIV")
                except Exception:
                    print(f"⏸️ Automatisches Tracking: STATUS UNBEKANNT")
                
                # Charts-Status
                if charts_enabled and charts_config['enabled']:
                    print(f"📊 Charts-Tracking: AKTIV")
                
                # Background Processes Status
                try:
                    from background_scheduler import _global_process_manager
                    if _global_process_manager:
                        status = _global_process_manager.get_process_status()
                        if status['running_processes'] > 0:
                            print(f"🔄 Background-Prozesse: {status['running_processes']} aktiv")
                except Exception:
                    pass
                
            except Exception as e:
                print(f"⚠️ Fehler beim Laden der Statistiken: {e}")
            
            # ORIGINALES HAUPTMENÜ (1-12 unverändert)
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
            
            # CHARTS-FEATURES (13-18)
            if charts_enabled:
                print("\n📊 CHARTS-FEATURES:")
                print("13. 🏆 Steam Charts anzeigen")
                print("14. 📈 Charts sofort aktualisieren")
                print("15. 🎯 Charts-Deals anzeigen")
                print("16. 📊 Charts-Status anzeigen")
                print("17. ⚙️ Charts-Intervalle konfigurieren")    # NEU
                print("18. 🔧 Erweiterte Charts-Konfiguration")   # NEU
            
            # NEUE ERWEITERTE FEATURES (19-23)
            print("\n🔧 ERWEITERTE FEATURES:")
            print("19. 🖥️ Process Management Terminal starten")    # NEU
            print("20. 🛠️ CLI-Tools anzeigen")                   # NEU  
            print("21. 🚀 CLI-Tool starten")                     # NEU
            print("22. 📊 Erweiterte System-Übersicht")          # NEU
            print("23. 🔧 Setup-Wizard starten")                 # NEU
            
            print("\n0.  🚪 Beenden")
            print("=" * 60)
            
            # User Input
            choice = input("Wähle eine Option: ").strip()
            
            # ===========================
            # MENU-HANDLING (ORIGINAL + NEUE FEATURES)
            # ===========================
            
            if choice == "0":
                print("\n👋 Auf Wiedersehen!")
                enhanced_cleanup()
                break
            
            elif choice in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]:
                # PLACEHOLDER für bestehende Funktionen (1-12)
                print(f"\n💡 Menüpunkt {choice} - Bestehende Funktion")
                print("💡 Diese Funktionen bleiben unverändert aus deiner originalen main.py")
                print("💡 Füge hier deine bestehenden Funktionen ein!")
                
                # Beispiel für eine der Funktionen (4 - Beste Deals):
                if choice == "4":
                    print("\n📊 BESTE DEALS")
                    print("=" * 15)
                    
                    try:
                        deals = price_tracker.get_best_deals(limit=10)
                        if deals:
                            print(f"\n🎯 Top {len(deals)} Deals:")
                            for i, deal in enumerate(deals, 1):
                                name = deal.get('name', 'Unbekannt')[:40]
                                current_price = deal.get('current_price', 0)
                                discount = deal.get('discount_percent', 0)
                                store = deal.get('store', 'Steam')
                                
                                print(f"{i:2d}. {name}")
                                print(f"    💰 €{current_price:.2f} (-{discount}%) bei {store}")
                                print()
                        else:
                            print("😔 Keine Deals gefunden")
                    except Exception as e:
                        print(f"❌ Fehler beim Laden der Deals: {e}")
                
                input("Drücke Enter zum Fortfahren...")
            
            # CHARTS-FUNKTIONEN (17-18 neu)
            elif choice == "17" and charts_enabled:
                # Charts-Intervalle konfigurieren
                configure_charts_intervals(price_tracker, charts_config)
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "18" and charts_enabled:
                # Erweiterte Charts-Konfiguration
                configure_charts_advanced(price_tracker, charts_config)
                input("Drücke Enter zum Fortfahren...")
            
            elif choice in ["13", "14", "15", "16"] and charts_enabled:
                # Andere Charts-Funktionen (bereits implementiert)
                print(f"\n📊 Charts-Funktion {choice}")
                print("💡 Diese Charts-Funktionen sind bereits in deinem System verfügbar")
                
                if choice == "14":
                    # Charts Update
                    if hasattr(price_tracker.charts_manager, 'update_all_charts'):
                        print("🔄 Führe Charts-Update durch...")
                        result = price_tracker.charts_manager.update_all_charts()
                        if result:
                            print("✅ Charts-Update erfolgreich abgeschlossen!")
                        else:
                            print("❌ Fehler beim Charts-Update")
                    else:
                        print("❌ Charts-Update-Funktion nicht verfügbar")
                
                input("Drücke Enter zum Fortfahren...")
            
            # NEUE ERWEITERTE FEATURES (19-23)
            elif choice == "19":
                # Process Management Terminal starten
                start_process_management_terminal()
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "20":
                # CLI-Tools anzeigen
                show_available_cli_tools()
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "21":
                # CLI-Tool starten
                launch_cli_tool()
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "22":
                # Erweiterte System-Übersicht
                show_extended_system_status()
                input("Drücke Enter zum Fortfahren...")
            
            elif choice == "23":
                # Setup-Wizard starten
                print("\n🔧 SETUP-WIZARD")
                print("=" * 20)
                print("🚀 Startet Setup-Wizard...")
                
                try:
                    result = subprocess.run(['python', 'setup.py', 'setup'], 
                                          capture_output=True, text=True, cwd=Path.cwd())
                    
                    print("📤 SETUP OUTPUT:")
                    if result.stdout:
                        print(result.stdout)
                    if result.stderr:
                        print("❌ ERRORS:")
                        print(result.stderr)
                    
                    print(f"✅ Setup beendet mit Exit-Code: {result.returncode}")
                    
                except Exception as e:
                    print(f"❌ Fehler beim Starten des Setup-Wizards: {e}")
                    print("💡 Führe manuell aus: python setup.py setup")
                
                input("Drücke Enter zum Fortfahren...")
            
            else:
                print("❌ Ungültige Auswahl!")
                time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n⏹️ Beende Steam Price Tracker...")
            enhanced_cleanup()
            break
        except Exception as e:
            print(f"\n❌ Unerwarteter Fehler: {e}")
            logger.exception("Unerwarteter Fehler in main loop")
            input("Drücke Enter zum Fortfahren...")

if __name__ == "__main__":
    main()