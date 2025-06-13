#!/usr/bin/env python3
"""
Steam Wishlist Manager - Setup und CLI
Einfache Einrichtung und Kommandozeilenschnittstelle
Mit automatischem Monthly Release Import
"""

import sys
import argparse
import subprocess
from pathlib import Path
import json
from typing import Optional
from datetime import datetime

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
            # Enhanced Scheduler Features
            enhanced_scheduler = input("Enhanced Scheduler mit Release-Import aktivieren? (j/n): ").lower() in ['j', 'ja', 'y', 'yes']
            
            interval = input("Scheduler-Intervall in Minuten (Standard: 10): ").strip()
            try:
                config_manager.scheduler.interval_minutes = int(interval) if interval else 10
            except ValueError:
                pass
            
            if enhanced_scheduler:
                print("🆕 Enhanced Scheduler wird konfiguriert...")
                print("   - Automatischer Release-Import: täglich")
                print("   - CheapShark-Mapping: alle 10 Minuten")
                print("   - 'Too New' Retry: täglich")
                print("   - Wöchentliche Release-Rückschau")
        
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
    print("🎮 STEAM WISHLIST MANAGER - SETUP WIZARD v2.0 (ENHANCED)")
    print("Mit automatischem Release Discovery und intelligenter Priorisierung")
    print("=" * 80)
    
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
    
    # Schritt 6: NEU - Release Discovery Setup
    setup_release_discovery = input("\n🆕 Release Discovery einrichten? (empfohlen) (j/n): ").lower() in ['j', 'ja', 'y', 'yes']
    if setup_release_discovery:
        print("\n🆕 RELEASE DISCOVERY SETUP")
        print("=" * 30)
        
        # Importiere letzte 3 Monate Releases
        try:
            from steam_bulk_importer import SteamBulkImporter
            from database_manager import DatabaseManager
            from steam_wishlist_manager import load_api_key_from_env
            
            api_key = load_api_key_from_env()
            if api_key:
                db_manager = DatabaseManager()
                importer = SteamBulkImporter(api_key, db_manager)
                
                print("📅 Importiere Releases der letzten 3 Monate...")
                if importer.import_latest_releases_auto(months_back=3):
                    print("✅ Release Discovery Setup erfolgreich")
                else:
                    print("⚠️ Release Discovery Setup fehlgeschlagen (kann später nachgeholt werden)")
            else:
                print("⚠️ Release Discovery übersprungen (kein API Key)")
                
        except Exception as e:
            print(f"⚠️ Release Discovery Fehler: {e}")
    
    print("\n🎉 SETUP ABGESCHLOSSEN!")
    print("💡 Starte den Manager mit: python steam_wishlist_manager.py")
    print("🆕 Oder nutze CLI-Befehle für Release-Import:")
    print("   python setup.py releases-auto")
    print("   python setup.py scheduler start --enhanced")
    
    return True

def load_api_key_from_env(env_file=".env") -> Optional[str]:
    """
    Lädt den Steam API Key aus einer .env-Datei
    """
    env_path = Path(env_file)
    
    if not env_path.exists():
        return None
    
    try:
        # Versuche python-dotenv zu verwenden (falls installiert)
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
            import os
            api_key = os.getenv('STEAM_API_KEY')
            if api_key:
                return api_key.strip()
        except ImportError:
            pass
        
        # Manuelle .env-Parsing als Fallback
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or not line or '=' not in line:
                    continue
                
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Entferne Anführungszeichen falls vorhanden
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                if key == 'STEAM_API_KEY':
                    return value
        
        return None
        
    except Exception as e:
        print(f"⚠️ Fehler beim Lesen der .env-Datei: {e}")
        return None

def cli_main():
    """CLI-Hauptfunktion mit erweiterten Argumenten"""
    parser = argparse.ArgumentParser(
        description="Steam Wishlist Manager - CLI v2.0 (Enhanced)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s setup                         - Setup-Wizard ausführen
  %(prog)s wishlist 76561197960435530     - Wishlist für Steam ID abrufen
  %(prog)s bulk-import                   - Bulk Import durchführen
  %(prog)s releases-import               - Neue Releases importieren
  %(prog)s releases-import --month 2024-12  - Bestimmten Monat importieren
  %(prog)s releases-auto                 - Automatischer Release-Import
  %(prog)s scheduler start --enhanced    - Enhanced Scheduler starten
  %(prog)s status --detailed             - Detaillierter Status
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
    
    # NEU: Releases Import Commands
    releases_parser = subparsers.add_parser('releases-import', help='Neue Releases importieren')
    releases_parser.add_argument('--month', help='Bestimmter Monat (YYYY-MM)')
    releases_parser.add_argument('--start-month', help='Start-Monat für mehrere Monate (YYYY-MM)')
    releases_parser.add_argument('--end-month', help='End-Monat für mehrere Monate (YYYY-MM)')
    releases_parser.add_argument('--category', choices=['new_releases', 'top_releases'], 
                                default='new_releases', help='Kategorie der Releases')
    
    # NEU: Automatischer Release Import
    releases_auto_parser = subparsers.add_parser('releases-auto', help='Automatischer Release-Import')
    releases_auto_parser.add_argument('--months-back', type=int, default=3,
                                     help='Wie viele Monate zurück (Standard: 3)')
    
    # NEU: Recent Releases Check
    recent_parser = subparsers.add_parser('recent-releases', help='Sehr neue Releases prüfen')
    recent_parser.add_argument('--days-back', type=int, default=7,
                              help='Wie viele Tage zurück (Standard: 7)')
    
    # Erweiterte Scheduler Commands
    scheduler_parser = subparsers.add_parser('scheduler', help='Scheduler verwalten')
    scheduler_subparsers = scheduler_parser.add_subparsers(dest='scheduler_action')
    
    # Standard Scheduler
    start_parser = scheduler_subparsers.add_parser('start', help='Scheduler starten')
    start_parser.add_argument('--enhanced', action='store_true', 
                             help='Enhanced Scheduler mit Release-Import starten')
    start_parser.add_argument('--mapping-interval', type=int, default=10,
                             help='CheapShark-Mapping Intervall (Minuten)')
    start_parser.add_argument('--mapping-batch', type=int, default=10,
                             help='CheapShark-Mapping Batch-Größe')
    start_parser.add_argument('--releases-interval', type=int, default=24,
                             help='Release-Import Intervall (Stunden)')
    
    scheduler_subparsers.add_parser('stop', help='Scheduler stoppen')
    scheduler_subparsers.add_parser('status', help='Scheduler-Status')
    
    # Erweiterte Status Commands
    status_parser = subparsers.add_parser('status', help='System-Status anzeigen')
    status_parser.add_argument('--detailed', action='store_true',
                              help='Detaillierte Statistiken mit Release-Info')
    status_parser.add_argument('--releases', action='store_true',
                              help='Nur Release-Statistiken anzeigen')
    
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
    elif args.command == 'releases-import':
        handle_releases_import_command(args)
    elif args.command == 'releases-auto':
        handle_releases_auto_command(args)
    elif args.command == 'recent-releases':
        handle_recent_releases_command(args)
    elif args.command == 'scheduler':
        handle_scheduler_command_enhanced(args)
    elif args.command == 'status':
        handle_status_command_enhanced(args)
    elif args.command == 'config':
        handle_config_command(args)

# ========================
# COMMAND HANDLERS
# ========================

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

def handle_releases_import_command(args):
    """Behandelt releases-import Command"""
    try:
        from steam_bulk_importer import SteamBulkImporter
        from database_manager import DatabaseManager
        
        api_key = load_api_key_from_env()
        if not api_key:
            print("❌ Kein API Key gefunden. Führe 'setup' aus.")
            return
        
        db_manager = DatabaseManager()
        importer = SteamBulkImporter(api_key, db_manager)
        
        if args.start_month and args.end_month:
            # Mehrere Monate
            print(f"📅 Importiere Releases: {args.start_month} bis {args.end_month}")
            result = importer.import_multiple_months_releases(args.start_month, args.end_month)
            
            if result['months_processed'] > 0:
                print(f"✅ {result['months_processed']} Monate erfolgreich verarbeitet")
                print(f"📊 {result['total_imported']} Releases importiert")
            else:
                print("❌ Kein Monat erfolgreich verarbeitet")
                
        elif args.month:
            # Bestimmter Monat
            print(f"📅 Importiere Releases für: {args.month}")
            
            if importer.import_monthly_top_releases(args.month, args.category):
                print("✅ Release-Import erfolgreich")
            else:
                print("❌ Release-Import fehlgeschlagen")
                
        else:
            # Aktueller Monat
            current_month = datetime.now().strftime("%Y-%m")
            print(f"📅 Importiere Releases für aktuellen Monat: {current_month}")
            
            if importer.import_monthly_top_releases(current_month, args.category):
                print("✅ Release-Import erfolgreich")
            else:
                print("❌ Release-Import fehlgeschlagen")
        
        # Statistiken anzeigen
        stats = db_manager.get_database_stats()
        print(f"\n📊 Aktuelle Statistiken:")
        print(f"📚 Gesamt Apps: {stats['apps']['total']:,}")
        print(f"🆕 Kürzlich veröffentlicht: {stats['apps']['recently_released']:,}")
        
    except ImportError as e:
        print(f"❌ Modul-Import Fehler: {e}")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def handle_releases_auto_command(args):
    """Behandelt releases-auto Command"""
    try:
        from steam_bulk_importer import SteamBulkImporter
        from database_manager import DatabaseManager
        
        api_key = load_api_key_from_env()
        if not api_key:
            print("❌ Kein API Key gefunden. Führe 'setup' aus.")
            return
        
        db_manager = DatabaseManager()
        importer = SteamBulkImporter(api_key, db_manager)
        
        print(f"🤖 Starte automatischen Release-Import (letzte {args.months_back} Monate)...")
        
        if importer.import_latest_releases_auto(args.months_back):
            print("✅ Automatischer Release-Import erfolgreich")
            
            # Zeige was neu hinzugefügt wurde
            stats = db_manager.get_database_stats()
            print(f"📊 Aktuelle Statistiken:")
            print(f"🆕 Kürzlich veröffentlicht: {stats['apps']['recently_released']:,}")
        else:
            print("❌ Automatischer Release-Import fehlgeschlagen")
        
    except ImportError as e:
        print(f"❌ Modul-Import Fehler: {e}")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def handle_recent_releases_command(args):
    """Behandelt recent-releases Command"""
    try:
        from steam_bulk_importer import SteamBulkImporter
        from database_manager import DatabaseManager
        
        api_key = load_api_key_from_env()
        if not api_key:
            print("❌ Kein API Key gefunden. Führe 'setup' aus.")
            return
        
        db_manager = DatabaseManager()
        importer = SteamBulkImporter(api_key, db_manager)
        
        print(f"🔍 Prüfe sehr neue Releases (letzte {args.days_back} Tage)...")
        
        new_count = importer._check_for_very_recent_releases(args.days_back)
        
        if new_count > 0:
            print(f"✅ {new_count} sehr neue Apps gefunden und importiert")
        else:
            print("📭 Keine sehr neuen Apps gefunden")
        
    except ImportError as e:
        print(f"❌ Modul-Import Fehler: {e}")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def handle_scheduler_command_enhanced(args):
    """Behandelt erweiterte Scheduler-Commands"""
    try:
        from steam_wishlist_manager import SteamWishlistManager
        
        api_key = load_api_key_from_env()
        if not api_key:
            print("❌ Kein API Key gefunden")
            return
        
        manager = SteamWishlistManager(api_key)
        processor = manager.cheapshark_processor
        
        if args.scheduler_action == 'start':
            if args.enhanced:
                # Enhanced Scheduler starten
                print("🚀 Starte Enhanced Scheduler mit Release-Import...")
                
                try:
                    # Versuche Enhanced Scheduler zu starten
                    if hasattr(processor, 'start_background_scheduler_enhanced'):
                        processor.start_background_scheduler_enhanced(
                            mapping_batch_size=args.mapping_batch,
                            mapping_interval_minutes=args.mapping_interval,
                            releases_interval_hours=args.releases_interval
                        )
                        
                        print("✅ Enhanced Scheduler gestartet")
                        print(f"🔗 CheapShark-Mapping: alle {args.mapping_interval} Minuten")
                        print(f"🆕 Release-Import: alle {args.releases_interval} Stunden")
                    else:
                        print("⚠️ Enhanced Scheduler nicht verfügbar, starte Standard-Scheduler...")
                        processor.start_background_scheduler()
                        print("✅ Standard-Scheduler gestartet")
                        
                except Exception as e:
                    print(f"⚠️ Enhanced Scheduler Fehler: {e}")
                    print("🔄 Fallback auf Standard-Scheduler...")
                    processor.start_background_scheduler()
                    print("✅ Standard-Scheduler gestartet")
            else:
                # Standard Scheduler
                processor.start_background_scheduler()
                print("✅ Standard-Scheduler gestartet")
                
        elif args.scheduler_action == 'stop':
            processor.stop_background_scheduler()
            print("🛑 Scheduler gestoppt")
            
        elif args.scheduler_action == 'status':
            try:
                # Versuche Enhanced Status zu holen
                if hasattr(processor, 'get_enhanced_scheduler_status'):
                    status = processor.get_enhanced_scheduler_status()
                    
                    print("📊 ENHANCED SCHEDULER STATUS")
                    print("=" * 40)
                    print(f"🔄 Läuft: {'Ja' if status['scheduler_running'] else 'Nein'}")
                    print(f"📋 Ausstehende Jobs: {status['pending_jobs']:,}")
                    print(f"❌ Fehlgeschlagene Jobs: {status['failed_jobs']:,}")
                    print(f"🆕 Kürzlich veröffentlichte Apps: {status.get('recent_apps', 'N/A'):,}")
                    print(f"📅 'Zu neue' Apps: {status.get('too_new_apps', 'N/A'):,}")
                    print(f"⏰ Letzter Release-Import: {status.get('last_release_import', 'Nie')}")
                else:
                    raise AttributeError("Enhanced status not available")
                    
            except (AttributeError, KeyError):
                # Fallback auf Standard-Status
                status = processor.get_scheduler_status()
                print("📊 SCHEDULER STATUS")
                print("=" * 30)
                print(f"🔄 Läuft: {'Ja' if status['scheduler_running'] else 'Nein'}")
                print(f"📋 Ausstehende Jobs: {status['pending_jobs']:,}")
                print(f"❌ Fehlgeschlagene Jobs: {status['failed_jobs']:,}")
                print(f"⏰ Nächster Lauf: {status['next_run']}")
            
    except ImportError as e:
        print(f"❌ Modul-Import Fehler: {e}")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def handle_status_command_enhanced(args):
    """Behandelt erweiterte Status-Commands"""
    try:
        from steam_wishlist_manager import SteamWishlistManager
        
        api_key = load_api_key_from_env()
        if not api_key:
            print("❌ Kein API Key gefunden")
            return
        
        manager = SteamWishlistManager(api_key)
        status = manager.get_manager_status()
        
        if args.releases:
            # Nur Release-Statistiken
            print("🆕 RELEASE-STATISTIKEN")
            print("=" * 30)
            
            db = status['database']
            print(f"📅 Apps mit Release Date: {db['apps']['with_release_date']:,}")
            print(f"🆕 Kürzlich veröffentlicht: {db['apps']['recently_released']:,}")
            print(f"📅 Zu neu für CheapShark: {db['cheapshark']['too_new']:,}")
            
            # Zusätzliche Release-Insights
            try:
                from cheapshark_mapping_processor import CheapSharkMappingProcessor
                processor = CheapSharkMappingProcessor(api_key, manager.db_manager)
                if hasattr(processor, 'get_recently_released_apps_status'):
                    recent_status = processor.get_recently_released_apps_status()
                    
                    print(f"\n📊 RELEASE DATE INSIGHTS:")
                    print(f"🆕 Ohne Mapping (< 30 Tage): {recent_status['recent_without_mapping']:,}")
                    print(f"🔄 Bereit für Age-Based Retry: {recent_status['ready_for_retry']:,}")
                
            except (ImportError, AttributeError):
                pass
                
        elif args.detailed:
            # Detaillierte Statistiken
            print("📊 DETAILLIERTER SYSTEM-STATUS")
            print("=" * 50)
            
            # Standard-Statistiken
            db = status['database']
            print(f"📚 Apps in DB: {db['apps']['total']:,}")
            print(f"   🆓 Kostenlos: {db['apps']['free']:,}")
            print(f"   💰 Kostenpflichtig: {db['apps']['paid']:,}")
            print(f"   📅 Mit Release Date: {db['apps']['with_release_date']:,}")
            print(f"   🆕 Kürzlich veröffentlicht: {db['apps']['recently_released']:,}")
            
            print(f"\n🔗 CheapShark Status:")
            cs = db['cheapshark']
            print(f"✅ Erfolgreich gemappt: {cs['mapped']:,} ({cs['found_rate']:.1f}%)")
            print(f"📝 Kein Mapping verfügbar: {cs['no_mapping_found']:,}")
            print(f"📅 Zu neu für Mapping: {cs['too_new']:,}")
            print(f"❌ Mapping fehlgeschlagen: {cs['mapping_failed']:,}")
            print(f"❔ Noch nicht versucht: {cs['unmapped']:,}")
            print(f"🎯 Coverage (verarbeitet): {cs['coverage']:.1f}%")
            print(f"📈 Erfolgsrate: {cs['success_rate']:.1f}%")
            
            print(f"\n👥 Wishlist:")
            wl = db['wishlist']
            print(f"📋 Gesamt Items: {wl['total_items']:,}")
            print(f"👤 Unique Users: {wl['unique_users']:,}")
            print(f"📊 Ø Items/User: {wl['avg_items_per_user']:.1f}")
            
            # Scheduler
            scheduler = status['scheduler']
            print(f"\n🚀 Scheduler: {'Läuft' if scheduler['scheduler_running'] else 'Gestoppt'}")
            print(f"📋 Queue: {scheduler['pending_jobs']:,} ausstehend, {scheduler['failed_jobs']:,} fehlgeschlagen")
            
            # Cache
            print(f"\n💾 Preis-Cache: {status['cache_size']} Einträge")
            
        else:
            # Standard-Status
            handle_status_command(args)
        
    except ImportError as e:
        print(f"❌ Modul-Import Fehler: {e}")
    except Exception as e:
        print(f"❌ Fehler: {e}")

def handle_status_command(args):
    """Behandelt Status-Command (Standard)"""
    try:
        from steam_wishlist_manager import SteamWishlistManager
        
        api_key = load_api_key_from_env()
        if not api_key:
            print("❌ Kein API Key gefunden")
            return
        
        manager = SteamWishlistManager(api_key)
        status = manager.get_manager_status()
        
        print(f"\n📊 MANAGER STATUS:")
        print(f"=" * 40)
        
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
