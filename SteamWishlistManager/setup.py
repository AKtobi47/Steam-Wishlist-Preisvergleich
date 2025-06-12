#!/usr/bin/env python3
"""
Steam Wishlist Manager - Setup und CLI
Einfache Einrichtung und Kommandozeilenschnittstelle
"""

import sys
import argparse
import subprocess
from pathlib import Path
import json
from typing import Optional

def check_python_version():
    """Prüft ob Python-Version kompatibel ist"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 oder höher erforderlich")
        print(f"   Aktuelle Version: {sys.version}")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]} kompatibel")

def install_dependencies():
    """Installiert erforderliche Python-Pakete"""
    requirements_file = Path("requirements.txt")
    
    if not requirements_file.exists():
        print("⚠️ requirements.txt nicht gefunden")
        return False
    
    try:
        print("📦 Installiere Python-Abhängigkeiten...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Abhängigkeiten erfolgreich installiert")
            return True
        else:
            print(f"❌ Fehler bei Installation: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        return False

def create_env_file():
    """Erstellt .env-Datei falls sie nicht existiert"""
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env-Datei bereits vorhanden")
        return True
    
    api_key = input("🔑 Steam Web API Key eingeben (https://steamcommunity.com/dev/apikey): ").strip()
    
    if not api_key:
        print("⚠️ Kein API Key eingegeben - .env-Template wird erstellt")
        api_key = "your_steam_api_key_here"
    
    env_content = f"""# Steam Wishlist Manager Konfiguration
# Steam Web API Key - erhältlich unter: https://steamcommunity.com/dev/apikey
STEAM_API_KEY={api_key}

# Optionale Umgebungsvariablen
# STEAM_WL_DB_PATH=steam_wishlist.db
# STEAM_WL_DEFAULT_COUNTRY=DE
# STEAM_WL_SCHEDULER_ENABLED=false
# STEAM_WL_SCHEDULER_INTERVAL=10
# STEAM_WL_RATE_LIMIT=0.5
# CHEAPSHARK_RATE_LIMIT=1.5
"""
    
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        if api_key == "your_steam_api_key_here":
            print("📝 .env-Template erstellt")
            print("   ⚠️ Bitte trage einen gültigen Steam API Key ein!")
        else:
            print("✅ .env-Datei mit API Key erstellt")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der .env-Datei: {e}")
        return False

def setup_initial_config():
    """Richtet initiale Konfiguration ein"""
    try:
        from config import ConfigManager
        
        print("⚙️ Erstelle Standard-Konfiguration...")
        config_manager = ConfigManager()
        
        # Interaktive Konfiguration
        print("\n🔧 KONFIGURATION ANPASSEN:")
        
        # Scheduler
        enable_scheduler = input("Background-Scheduler aktivieren? (j/n): ").lower() in ['j', 'ja', 'y', 'yes']
        config_manager.scheduler.enabled = enable_scheduler
        
        if enable_scheduler:
            interval = input("Scheduler-Intervall in Minuten (Standard: 10): ").strip()
            try:
                config_manager.scheduler.interval_minutes = int(interval) if interval else 10
            except ValueError:
                pass
        
        # Land
        country = input("Standard-Ländercode für Preise (Standard: DE): ").strip().upper()
        if country:
            config_manager.wishlist.default_country_code = country
        
        # Bulk Import Methode
        print("\nBulk Import Methode wählen:")
        print("1. steam_store_service (nur Spiele, empfohlen)")
        print("2. steam_api_v2 (alle Apps)")
        print("3. steamspy (mit Statistiken, langsam)")
        
        method_choice = input("Wählen Sie (1-3, Standard: 1): ").strip()
        method_map = {
            '1': 'steam_store_service',
            '2': 'steam_api_v2',
            '3': 'steamspy'
        }
        config_manager.bulk_import.preferred_method = method_map.get(method_choice, 'steam_store_service')
        
        # Konfiguration speichern
        if config_manager.save_config():
            print("✅ Konfiguration gespeichert")
        
        return True
        
    except ImportError:
        print("⚠️ Konfigurationsmodul nicht verfügbar - überspringe")
        return False
    except Exception as e:
        print(f"❌ Fehler bei Konfiguration: {e}")
        return False

def run_initial_bulk_import():
    """Führt initialen Bulk Import durch"""
    run_import = input("\n📥 Initialen Bulk Import durchführen? (empfohlen) (j/n): ").lower()
    
    if run_import in ['j', 'ja', 'y', 'yes']:
        try:
            from steam_bulk_importer import bulk_import_main
            
            print("🚀 Starte Bulk Import...")
            bulk_import_main()
            
        except ImportError:
            print("❌ Bulk Import Modul nicht verfügbar")
            return False
        except Exception as e:
            print(f"❌ Fehler beim Bulk Import: {e}")
            return False
    
    return True

def setup_wizard():
    """Vollständiger Setup-Wizard"""
    print("🎮 STEAM WISHLIST MANAGER - SETUP WIZARD")
    print("=" * 60)
    
    # Schritt 1: Python-Version prüfen
    check_python_version()
    
    # Schritt 2: Abhängigkeiten installieren
    if not install_dependencies():
        print("❌ Setup abgebrochen wegen Abhängigkeitsfehlern")
        return False
    
    # Schritt 3: .env-Datei erstellen
    if not create_env_file():
        print("❌ Setup abgebrochen wegen .env-Fehler")
        return False
    
    # Schritt 4: Konfiguration einrichten
    if not setup_initial_config():
        print("⚠️ Konfiguration übersprungen")
    
    # Schritt 5: Initialer Bulk Import
    if not run_initial_bulk_import():
        print("⚠️ Bulk Import übersprungen")
    
    print("\n🎉 SETUP ABGESCHLOSSEN!")
    print("💡 Starte den Manager mit: python steam_wishlist_manager.py")
    
    return True

def cli_main():
    """CLI-Hauptfunktion mit Argumenten"""
    parser = argparse.ArgumentParser(
        description="Steam Wishlist Manager - CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s setup                    - Setup-Wizard ausführen
  %(prog)s wishlist 76561197960435530  - Wishlist für Steam ID abrufen
  %(prog)s bulk-import              - Bulk Import durchführen
  %(prog)s scheduler start          - Background-Scheduler starten
  %(prog)s status                   - System-Status anzeigen
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Verfügbare Kommandos')
    
    # Setup Command
    setup_parser = subparsers.add_parser('setup', help='Setup-Wizard ausführen')
    setup_parser.add_argument('--skip-dependencies', action='store_true', 
                             help='Abhängigkeitsinstallation überspringen')
    setup_parser.add_argument('--skip-import', action='store_true',
                             help='Initialen Bulk Import überspringen')
    
    # Wishlist Command
    wishlist_parser = subparsers.add_parser('wishlist', help='Wishlist abrufen')
    wishlist_parser.add_argument('steam_id', help='Steam ID (17 Ziffern)')
    wishlist_parser.add_argument('--country', default='DE', help='Ländercode für Preise')
    wishlist_parser.add_argument('--no-prices', action='store_true', help='Keine Steam-Preise')
    wishlist_parser.add_argument('--no-cheapshark', action='store_true', help='Keine CheapShark-Daten')
    wishlist_parser.add_argument('--output', help='Ausgabedatei für JSON')
    
    # Bulk Import Command
    bulk_parser = subparsers.add_parser('bulk-import', help='Bulk Import durchführen')
    bulk_parser.add_argument('--method', choices=['steam_api_v2', 'steam_store_service', 'steamspy'],
                            help='Import-Methode')
    
    # Scheduler Commands
    scheduler_parser = subparsers.add_parser('scheduler', help='Scheduler verwalten')
    scheduler_subparsers = scheduler_parser.add_subparsers(dest='scheduler_action')
    scheduler_subparsers.add_parser('start', help='Scheduler starten')
    scheduler_subparsers.add_parser('stop', help='Scheduler stoppen')
    scheduler_subparsers.add_parser('status', help='Scheduler-Status')
    
    # Status Command
    status_parser = subparsers.add_parser('status', help='System-Status anzeigen')
    
    # Config Command
    config_parser = subparsers.add_parser('config', help='Konfiguration verwalten')
    config_subparsers = config_parser.add_subparsers(dest='config_action')
    config_subparsers.add_parser('show', help='Konfiguration anzeigen')
    config_subparsers.add_parser('edit', help='Konfiguration bearbeiten')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Commands ausführen
    if args.command == 'setup':
        handle_setup_command(args)
    elif args.command == 'wishlist':
        handle_wishlist_command(args)
    elif args.command == 'bulk-import':
        handle_bulk_import_command(args)
    elif args.command == 'scheduler':
        handle_scheduler_command(args)
    elif args.command == 'status':
        handle_status_command(args)
    elif args.command == 'config':
        handle_config_command(args)

def handle_setup_command(args):
    """Behandelt Setup-Command"""
    if args.skip_dependencies:
        print("⏭️ Überspringe Abhängigkeitsinstallation")
    else:
        install_dependencies()
    
    create_env_file()
    setup_initial_config()
    
    if not args.skip_import:
        run_initial_bulk_import()

def handle_wishlist_command(args):
    """Behandelt Wishlist-Command"""
    try:
        from steam_wishlist_manager import SteamWishlistManager, load_api_key_from_env
        
        api_key = load_api_key_from_env()
        if not api_key:
            print("❌ Kein API Key gefunden. Führe 'setup' aus.")
            return
        
        manager = SteamWishlistManager(api_key)
        
        print(f"🎯 Rufe Wishlist für Steam ID {args.steam_id} ab...")
        
        wishlist_data = manager.process_complete_wishlist(
            args.steam_id,
            include_cheapshark=not args.no_cheapshark,
            include_steam_prices=not args.no_prices,
            country_code=args.country
        )
        
        if wishlist_data:
            manager.print_wishlist_summary(wishlist_data)
            
            if args.output:
                filepath = manager.save_wishlist_to_file(wishlist_data, args.output)
                print(f"💾 Gespeichert: {filepath}")
        else:
            print("❌ Wishlist konnte nicht abgerufen werden")
            
    except ImportError as e:
        print(f"❌ Modul-Import Fehler: {e}")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def handle_bulk_import_command(args):
    """Behandelt Bulk Import Command"""
    try:
        from steam_bulk_importer import bulk_import_main
        
        print("📥 Starte Bulk Import...")
        bulk_import_main()
        
    except ImportError as e:
        print(f"❌ Modul-Import Fehler: {e}")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def handle_scheduler_command(args):
    """Behandelt Scheduler-Commands"""
    try:
        from steam_wishlist_manager import SteamWishlistManager, load_api_key_from_env
        
        api_key = load_api_key_from_env()
        if not api_key:
            print("❌ Kein API Key gefunden")
            return
        
        manager = SteamWishlistManager(api_key)
        processor = manager.cheapshark_processor
        
        if args.scheduler_action == 'start':
            processor.start_background_scheduler()
            print("🚀 Scheduler gestartet")
        elif args.scheduler_action == 'stop':
            processor.stop_background_scheduler()
            print("🛑 Scheduler gestoppt")
        elif args.scheduler_action == 'status':
            status = processor.get_scheduler_status()
            print(f"🔄 Läuft: {'Ja' if status['scheduler_running'] else 'Nein'}")
            print(f"📋 Ausstehende Jobs: {status['pending_jobs']}")
            print(f"❌ Fehlgeschlagene Jobs: {status['failed_jobs']}")
            
    except ImportError as e:
        print(f"❌ Modul-Import Fehler: {e}")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def handle_status_command(args):
    """Behandelt Status-Command"""
    try:
        from steam_wishlist_manager import SteamWishlistManager, load_api_key_from_env
        
        api_key = load_api_key_from_env()
        if not api_key:
            print("❌ Kein API Key gefunden")
            return
        
        manager = SteamWishlistManager(api_key)
        status = manager.get_manager_status()
        
        print("📊 STEAM WISHLIST MANAGER STATUS")
        print("=" * 40)
        
        # Datenbank
        db = status['database']
        print(f"📚 Apps in DB: {db['apps']['total']:,}")
        print(f"🎯 CheapShark gemappt: {db['cheapshark']['mapped']:,}")
        print(f"📈 Mapping-Rate: {db['cheapshark']['success_rate']:.1f}%")
        print(f"📋 Wishlist Items: {db['wishlist']['total_items']:,}")
        print(f"👥 Unique Users: {db['wishlist']['unique_users']:,}")
        
        # Scheduler
        scheduler = status['scheduler']
        print(f"🚀 Scheduler: {'Läuft' if scheduler['scheduler_running'] else 'Gestoppt'}")
        print(f"📋 Queue: {scheduler['pending_jobs']:,} ausstehend")
        
        # Cache
        print(f"💾 Preis-Cache: {status['cache_size']} Einträge")
        
    except ImportError as e:
        print(f"❌ Modul-Import Fehler: {e}")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def handle_config_command(args):
    """Behandelt Config-Commands"""
    try:
        from config import get_config
        
        config_manager = get_config()
        
        if args.config_action == 'show':
            print(config_manager.get_config_summary())
        elif args.config_action == 'edit':
            print("⚙️ Interaktive Konfiguration noch nicht implementiert")
            print("💡 Bearbeite config.json manuell")
            
    except ImportError as e:
        print(f"❌ Modul-Import Fehler: {e}")
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Kein Argument -> Setup-Wizard
        print("Kein Kommando angegeben - starte Setup-Wizard")
        setup_wizard()
    else:
        # CLI-Modus
        cli_main()