#!/usr/bin/env python3
"""
Steam Price Tracker - Setup und CLI
Vereinfachtes Setup für das Preis-Tracking System
"""

import sys
import argparse
import subprocess
from pathlib import Path
import json
from typing import Optional

def check_python_version():
    """Prüft ob Python-Version kompatibel ist"""
    if sys.version_info < (3, 8):  # <-- KORRIGIERT: (3, 8) statt (3.8)
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
    
    # Kopiere .env.example falls vorhanden
    env_example = Path(".env.example")
    if env_example.exists():
        try:
            import shutil
            shutil.copy(env_example, env_file)
            print("📝 .env-Datei aus Template erstellt")
        except Exception as e:
            print(f"⚠️ Konnte .env.example nicht kopieren: {e}")
    
    # API Key abfragen
    print("\n🔑 STEAM API KEY KONFIGURATION:")
    print("1. Gehe zu: https://steamcommunity.com/dev/apikey")
    print("2. Erstelle einen neuen API Key")
    print("3. Kopiere den Key hier rein")
    
    api_key = input("\nSteam API Key eingeben (Enter zum Überspringen): ").strip()
    
    if api_key:
        # .env-Datei erstellen/aktualisieren
        env_content = f"""# Steam Price Tracker Konfiguration
STEAM_API_KEY={api_key}

# Optional - Standardwerte
TRACKING_INTERVAL_HOURS=6
CHEAPSHARK_RATE_LIMIT=1.5
STEAM_RATE_LIMIT=1.0
DEBUG_MODE=false
"""
        
        try:
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)
            print("✅ .env-Datei mit API Key erstellt")
            return True
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der .env-Datei: {e}")
            return False
    else:
        print("⚠️ API Key übersprungen - bitte später in .env-Datei eintragen")
        return True

def initialize_database():
    """Initialisiert die Datenbank"""
    try:
        from database_manager import DatabaseManager
        
        print("🗄️ Initialisiere Datenbank...")
        db_manager = DatabaseManager()
        print("✅ Datenbank erfolgreich initialisiert")
        
        # Zeige DB-Pfad
        print(f"   📍 Datenbank: {db_manager.db_path}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Konnte DatabaseManager nicht importieren: {e}")
        return False
    except Exception as e:
        print(f"❌ Datenbank-Initialisierung fehlgeschlagen: {e}")
        return False

def setup_directories():
    """Erstellt notwendige Verzeichnisse"""
    directories = ["exports", "logs", "backups"]
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        try:
            dir_path.mkdir(exist_ok=True)
            print(f"📁 Verzeichnis erstellt: {dir_name}/")
        except Exception as e:
            print(f"⚠️ Konnte Verzeichnis {dir_name} nicht erstellen: {e}")

def test_api_connection():
    """Testet die Steam API Verbindung"""
    try:
        from steam_wishlist_manager import load_api_key_from_env, SteamWishlistManager
        
        api_key = load_api_key_from_env()
        if not api_key:
            print("⚠️ Kein API Key für Test verfügbar")
            return False
        
        print("🔌 Teste Steam API Verbindung...")
        
        # Verwende eine bekannte Steam ID für Test
        test_steam_id = "76561197960435530"  # Gabe Newell
        
        manager = SteamWishlistManager(api_key)
        player_info = manager.get_player_info(test_steam_id)
        
        if player_info:
            print(f"✅ Steam API funktioniert - Test-User: {player_info.get('username', 'Unknown')}")
            return True
        else:
            print("❌ Steam API Test fehlgeschlagen")
            return False
            
    except ImportError as e:
        print(f"⚠️ Steam API Test übersprungen: {e}")
        return False
    except Exception as e:
        print(f"❌ Steam API Test Fehler: {e}")
        return False

def setup_wizard():
    """Vollständiger Setup-Wizard"""
    print("💰 STEAM PRICE TRACKER - SETUP WIZARD v1.0")
    print("=" * 60)
    
    success_steps = 0
    total_steps = 6
    
    # Schritt 1: Python-Version prüfen
    print("\n1️⃣ PYTHON-VERSION PRÜFEN")
    check_python_version()
    success_steps += 1
    
    # Schritt 2: Abhängigkeiten installieren
    print("\n2️⃣ ABHÄNGIGKEITEN INSTALLIEREN")
    if install_dependencies():
        success_steps += 1
    else:
        print("⚠️ Installation teilweise fehlgeschlagen - Programm könnte trotzdem funktionieren")
    
    # Schritt 3: Verzeichnisse erstellen
    print("\n3️⃣ VERZEICHNISSE ERSTELLEN")
    setup_directories()
    success_steps += 1
    
    # Schritt 4: .env-Datei erstellen
    print("\n4️⃣ UMGEBUNGSVARIABLEN KONFIGURIEREN")
    if create_env_file():
        success_steps += 1
    
    # Schritt 5: Datenbank initialisieren
    print("\n5️⃣ DATENBANK INITIALISIEREN")
    if initialize_database():
        success_steps += 1
    
    # Schritt 6: API-Verbindung testen
    print("\n6️⃣ STEAM API TESTEN")
    if test_api_connection():
        success_steps += 1
    
    # Zusammenfassung
    print(f"\n🎉 SETUP ABGESCHLOSSEN!")
    print(f"✅ {success_steps}/{total_steps} Schritte erfolgreich")
    
    if success_steps >= 4:
        print("\n💡 NÄCHSTE SCHRITTE:")
        print("1. 🚀 Starte die Hauptanwendung: python main.py")
        print("2. 📥 Importiere deine Steam Wishlist")
        print("3. 🔄 Aktiviere automatisches Preis-Tracking")
        print("4. 📊 Überwache Preisänderungen und Deals")
        
        # Frage ob Hauptanwendung gestartet werden soll
        start_main = input("\nHauptanwendung jetzt starten? (j/n): ").lower().strip()
        if start_main in ['j', 'ja', 'y', 'yes']:
            try:
                import main
                main.main()
            except Exception as e:
                print(f"❌ Fehler beim Starten der Hauptanwendung: {e}")
                print("💡 Versuche manuell: python main.py")
    else:
        print("\n⚠️ Setup nicht vollständig - bitte Fehler beheben")
        print("💡 Hilfe: https://github.com/your-repo/issues")
    
    return success_steps >= 4

def cli_main():
    """CLI-Hauptfunktion"""
    parser = argparse.ArgumentParser(
        description="Steam Price Tracker - Setup und Verwaltung",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s setup                    - Vollständiger Setup-Wizard
  %(prog)s install                  - Nur Abhängigkeiten installieren
  %(prog)s init-db                  - Nur Datenbank initialisieren
  %(prog)s test-api                 - Nur Steam API testen
  %(prog)s run                      - Hauptanwendung starten
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Verfügbare Kommandos')
    
    # Setup Command
    subparsers.add_parser('setup', help='Vollständiger Setup-Wizard')
    
    # Install Command
    subparsers.add_parser('install', help='Abhängigkeiten installieren')
    
    # Database Commands
    subparsers.add_parser('init-db', help='Datenbank initialisieren')
    
    # Test Commands
    subparsers.add_parser('test-api', help='Steam API testen')
    
    # Run Command
    subparsers.add_parser('run', help='Hauptanwendung starten')
    
    # Status Command
    subparsers.add_parser('status', help='System-Status anzeigen')
    
    args = parser.parse_args()
    
    if not args.command:
        # Kein Argument -> Setup-Wizard
        print("Kein Kommando angegeben - starte Setup-Wizard")
        setup_wizard()
        return
    
    # Commands ausführen
    if args.command == 'setup':
        setup_wizard()
    
    elif args.command == 'install':
        check_python_version()
        install_dependencies()
    
    elif args.command == 'init-db':
        initialize_database()
    
    elif args.command == 'test-api':
        test_api_connection()
    
    elif args.command == 'run':
        try:
            import main
            main.main()
        except Exception as e:
            print(f"❌ Fehler beim Starten: {e}")
    
    elif args.command == 'status':
        show_system_status()

def show_system_status():
    """Zeigt System-Status an"""
    print("📊 STEAM PRICE TRACKER - SYSTEM STATUS")
    print("=" * 50)
    
    # Python-Version
    print(f"🐍 Python: {sys.version.split()[0]}")
    
    # .env-Datei
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env-Datei: Vorhanden")
        
        # API Key prüfen
        try:
            from steam_wishlist_manager import load_api_key_from_env
            api_key = load_api_key_from_env()
            if api_key and api_key != "your_steam_api_key_here":
                print("✅ Steam API Key: Konfiguriert")
            else:
                print("❌ Steam API Key: Nicht konfiguriert")
        except:
            print("⚠️ Steam API Key: Unbekannt")
    else:
        print("❌ .env-Datei: Nicht vorhanden")
    
    # Datenbank
    try:
        from database_manager import DatabaseManager
        db = DatabaseManager()
        stats = db.get_tracking_statistics()
        print(f"✅ Datenbank: Funktionsfähig ({stats['tracked_apps']} Apps getrackt)")
    except Exception as e:
        print(f"❌ Datenbank: Fehler - {e}")
    
    # Abhängigkeiten
    required_modules = ['requests', 'schedule']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"❌ Abhängigkeiten: {', '.join(missing_modules)} fehlen")
    else:
        print("✅ Abhängigkeiten: Vollständig")
    
    # Verzeichnisse
    directories = ["exports", "logs", "backups"]
    missing_dirs = [d for d in directories if not Path(d).exists()]
    
    if missing_dirs:
        print(f"⚠️ Verzeichnisse: {', '.join(missing_dirs)} fehlen")
    else:
        print("✅ Verzeichnisse: Vollständig")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Kein Argument -> Setup-Wizard
        setup_wizard()
    else:
        # CLI-Modus
        cli_main()