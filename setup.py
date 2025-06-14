#!/usr/bin/env python3
"""
Steam Price Tracker - Setup und CLI
Vollständige Implementation mit Setup-Wizard und Diagnose-Tools
"""

import sys
import argparse
import subprocess
import requests
import json
from pathlib import Path
from datetime import datetime
import logging

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """Prüft ob Python-Version kompatibel ist"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 oder höher erforderlich")
        print(f"   Aktuelle Version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} kompatibel")
    return True

def install_dependencies(upgrade=False):
    """Installiert erforderliche Python-Pakete"""
    requirements_file = Path("requirements.txt")
    
    if not requirements_file.exists():
        print("⚠️ requirements.txt nicht gefunden - erstelle minimale Requirements")
        create_minimal_requirements()
    
    try:
        print("📦 Installiere Python-Abhängigkeiten...")
        
        cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        if upgrade:
            cmd.append("--upgrade")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Abhängigkeiten erfolgreich installiert")
            return True
        else:
            print(f"❌ Fehler bei Installation:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        return False

def create_minimal_requirements():
    """Erstellt minimale requirements.txt falls sie fehlt"""
    minimal_requirements = """# Steam Price Tracker - Minimale Dependencies
requests>=2.31.0
schedule>=1.2.0
python-dotenv>=1.0.0
"""
    
    try:
        with open("requirements.txt", "w", encoding="utf-8") as f:
            f.write(minimal_requirements)
        print("✅ Minimale requirements.txt erstellt")
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der requirements.txt: {e}")

def create_env_file():
    """Erstellt .env-Datei falls sie nicht existiert"""
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env-Datei bereits vorhanden")
        
        # Inhalt prüfen
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'STEAM_API_KEY=' in content:
                # Prüfe ob Key gesetzt ist
                for line in content.split('\n'):
                    if line.strip().startswith('STEAM_API_KEY=') and not line.strip().startswith('#'):
                        key_value = line.split('=', 1)[1].strip()
                        if key_value and key_value != 'your_steam_api_key_here':
                            masked_key = key_value[:8] + "..." if len(key_value) > 8 else "***"
                            print(f"✅ Steam API Key konfiguriert: {masked_key}")
                            return True
                
                print("⚠️ Steam API Key noch nicht konfiguriert")
                return False
            else:
                print("⚠️ .env-Datei unvollständig")
                return False
                
        except Exception as e:
            print(f"❌ Fehler beim Lesen der .env-Datei: {e}")
            return False
    
    else:
        try:
            # .env Template erstellen
            env_template = """# Steam Price Tracker Configuration
# Hole deinen Steam API Key von: https://steamcommunity.com/dev/apikey

STEAM_API_KEY=your_steam_api_key_here

# Optional: Datenbank-Konfiguration
TRACKER_DB_PATH=steam_price_tracker.db
DB_CLEANUP_DAYS=90

# Optional: API Rate Limits (Sekunden)
STEAM_RATE_LIMIT=1.0
CHEAPSHARK_RATE_LIMIT=1.5

# Optional: Timeout-Einstellungen (Sekunden)
STEAM_TIMEOUT=15
CHEAPSHARK_TIMEOUT=15

# Optional: Tracking-Konfiguration
TRACKING_INTERVAL_HOURS=6
MAX_APPS_PER_UPDATE=100
ENABLE_AUTOMATIC_TRACKING=false

# Optional: Export-Konfiguration
EXPORT_FORMAT=csv
EXPORT_DIRECTORY=exports

# Optional: Wishlist-Konfiguration
DEFAULT_COUNTRY_CODE=DE
WISHLIST_BATCH_SIZE=50
"""
            
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_template)
            
            print("✅ .env Template erstellt")
            print("💡 WICHTIG: Trage deinen Steam API Key in die .env-Datei ein!")
            print("🔗 API Key holen: https://steamcommunity.com/dev/apikey")
            return False
            
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der .env-Datei: {e}")
            return False

def initialize_database():
    """Initialisiert die Datenbank"""
    try:
        from database_manager import DatabaseManager
        
        print("🗄️ Initialisiere Datenbank...")
        db_manager = DatabaseManager()
        
        # Test-Query um sicherzustellen dass alles funktioniert
        stats = db_manager.get_statistics()
        
        print("✅ Datenbank erfolgreich initialisiert")
        print(f"   📚 Getrackte Apps: {stats['tracked_apps']}")
        print(f"   📈 Snapshots: {stats['total_snapshots']}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import-Fehler: {e}")
        print("💡 Führe zuerst 'python setup.py install' aus")
        return False
    except Exception as e:
        print(f"❌ Datenbank-Initialisierung fehlgeschlagen: {e}")
        return False

def test_api_connection_detailed():
    """Erweiterte API-Verbindungstests"""
    print("🧪 ERWEITERTE API-TESTS")
    print("=" * 25)
    
    # Steam API Key laden
    api_key = None
    env_file = Path(".env")
    
    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('STEAM_API_KEY=') and not line.strip().startswith('#'):
                        api_key = line.split('=', 1)[1].strip().strip('"').strip("'")
                        if api_key == 'your_steam_api_key_here':
                            api_key = None
                        break
        except Exception as e:
            print(f"❌ Fehler beim Lesen der .env: {e}")
    
    # Test 1: CheapShark API (ohne API Key)
    print("\n1️⃣ CheapShark API Test...")
    try:
        response = requests.get(
            "https://www.cheapshark.com/api/1.0/deals", 
            params={'steamAppID': '413150', 'storeID': '1'},  # Stardew Valley
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data:
                print("   ✅ CheapShark API funktioniert")
                print(f"   📊 {len(data)} Deals für Test-App gefunden")
            else:
                print("   ⚠️ CheapShark API antwortet, aber keine Deals gefunden")
        else:
            print(f"   ❌ CheapShark API Fehler: HTTP {response.status_code}")
            
    except requests.RequestException as e:
        print(f"   ❌ CheapShark API Verbindungsfehler: {e}")
    
    # Test 2: Steam API (benötigt API Key)
    print("\n2️⃣ Steam API Test...")
    if api_key:
        try:
            response = requests.get(
                "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/",
                params={
                    'key': api_key,
                    'steamids': '76561197960435530'  # Gabe Newell für Test
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'response' in data and 'players' in data['response']:
                    print("   ✅ Steam API Key funktioniert")
                    players = data['response']['players']
                    if players:
                        print(f"   👤 Test-User: {players[0].get('personaname', 'Unbekannt')}")
                else:
                    print("   ❌ Steam API ungültige Antwort")
            elif response.status_code == 403:
                print("   ❌ Steam API Key ungültig (403 Forbidden)")
            else:
                print(f"   ❌ Steam API Fehler: HTTP {response.status_code}")
                
        except requests.RequestException as e:
            print(f"   ❌ Steam API Verbindungsfehler: {e}")
    else:
        print("   ⚠️ Kein Steam API Key konfiguriert - überspringe Test")
    
    # Test 3: Steam Store API (öffentlich)
    print("\n3️⃣ Steam Store API Test...")
    try:
        response = requests.get(
            "https://store.steampowered.com/api/appdetails",
            params={'appids': '413150'},  # Stardew Valley
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if '413150' in data and data['413150'].get('success'):
                app_data = data['413150']['data']
                print("   ✅ Steam Store API funktioniert")
                print(f"   🎮 Test-App: {app_data.get('name', 'Unbekannt')}")
            else:
                print("   ⚠️ Steam Store API antwortet, aber App nicht gefunden")
        else:
            print(f"   ❌ Steam Store API Fehler: HTTP {response.status_code}")
            
    except requests.RequestException as e:
        print(f"   ❌ Steam Store API Verbindungsfehler: {e}")
    
    # Test 4: Netzwerk-Latenz
    print("\n4️⃣ Netzwerk-Latenz Test...")
    try:
        import time
        start_time = time.time()
        response = requests.get("https://www.cheapshark.com/api/1.0/stores", timeout=5)
        latency = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            print(f"   ✅ Netzwerk-Latenz: {latency:.0f}ms")
            if latency > 2000:
                print("   ⚠️ Hohe Latenz - möglicherweise langsame Internetverbindung")
        else:
            print(f"   ❌ Latenz-Test fehlgeschlagen: HTTP {response.status_code}")
            
    except requests.RequestException as e:
        print(f"   ❌ Latenz-Test Verbindungsfehler: {e}")
    
    print("\n📋 API-Test abgeschlossen")

def create_directory_structure():
    """Erstellt benötigte Verzeichnisse"""
    directories = [
        "exports",
        "backups", 
        "logs",
        "config"
    ]
    
    created = []
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                created.append(directory)
            except Exception as e:
                print(f"❌ Fehler beim Erstellen von {directory}: {e}")
                return False
    
    if created:
        print(f"✅ Verzeichnisse erstellt: {', '.join(created)}")
    else:
        print("✅ Alle Verzeichnisse bereits vorhanden")
    
    return True

def setup_wizard():
    """Vollständiger Setup-Wizard"""
    print("🚀 STEAM PRICE TRACKER - SETUP WIZARD")
    print("=" * 45)
    print("Dieser Wizard führt Sie durch die komplette Einrichtung.")
    print()
    
    steps = [
        ("Python-Version prüfen", check_python_version),
        ("Abhängigkeiten installieren", install_dependencies),
        ("Verzeichnisse erstellen", create_directory_structure),
        (".env-Datei erstellen", create_env_file),
        ("Datenbank initialisieren", initialize_database),
        ("API-Verbindungen testen", test_api_connection_detailed)
    ]
    
    success_steps = 0
    total_steps = len(steps)
    
    for i, (step_name, step_function) in enumerate(steps, 1):
        print(f"\n🔧 SCHRITT {i}/{total_steps}: {step_name}")
        print("-" * 30)
        
        try:
            if step_function():
                success_steps += 1
                print(f"✅ Schritt {i} erfolgreich")
            else:
                print(f"❌ Schritt {i} fehlgeschlagen")
                
                # Bei kritischen Fehlern fragen ob fortgesetzt werden soll
                if i <= 3:  # Kritische erste Schritte
                    continue_setup = input("\n⚠️ Trotzdem fortfahren? (j/n): ").lower().strip()
                    if continue_setup not in ['j', 'ja', 'y', 'yes']:
                        print("⏹️ Setup abgebrochen")
                        return False
        except Exception as e:
            print(f"❌ Unerwarteter Fehler in Schritt {i}: {e}")
    
    print(f"\n🎯 SETUP ABGESCHLOSSEN")
    print("=" * 20)
    print(f"✅ {success_steps}/{total_steps} Schritte erfolgreich")
    
    if success_steps >= 4:
        print("\n💡 NÄCHSTE SCHRITTE:")
        print("1. 🚀 Starte die Hauptanwendung: python main.py")
        print("2. 📥 Importiere deine Steam Wishlist")
        print("3. 🔄 Aktiviere automatisches Preis-Tracking")
        print("4. 📊 Überwache Preisänderungen und Deals")
        
        if success_steps < 6:
            print("\n⚠️ Einige Tests fehlgeschlagen aber Setup funktional!")
            print("💡 Du kannst das Programm trotzdem nutzen")
        
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
        print("💡 Führe 'python setup.py setup' erneut aus")
    
    return success_steps >= 4

def show_system_status():
    """Zeigt detaillierten System-Status an"""
    print("📊 STEAM PRICE TRACKER - SYSTEM STATUS")
    print("=" * 50)
    
    # Python-Version
    print(f"🐍 Python: {sys.version.split()[0]}")
    
    # Dateien prüfen
    required_files = ["main.py", "price_tracker.py", "database_manager.py", "steam_wishlist_manager.py"]
    missing_files = [f for f in required_files if not Path(f).exists()]
    
    if missing_files:
        print(f"❌ Fehlende Dateien: {', '.join(missing_files)}")
    else:
        print("✅ Alle Hauptdateien vorhanden")
    
    # .env-Datei
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env-Datei: Vorhanden")
        
        # API Key prüfen
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'STEAM_API_KEY=' in content and 'your_steam_api_key_here' not in content:
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
        stats = db.get_statistics()
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

def cli_main():
    """CLI-Hauptfunktion"""
    parser = argparse.ArgumentParser(
        description="Steam Price Tracker - Setup und Verwaltung",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s setup                    - Vollständiger Setup-Wizard
  %(prog)s install                  - Nur Abhängigkeiten installieren
  %(prog)s install --upgrade        - Abhängigkeiten aktualisieren
  %(prog)s init-db                  - Nur Datenbank initialisieren
  %(prog)s test-api                 - Nur API-Tests durchführen
  %(prog)s status                   - System-Status anzeigen
  %(prog)s run                      - Hauptanwendung starten
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Verfügbare Kommandos')
    
    # Setup Command
    subparsers.add_parser('setup', help='Vollständiger Setup-Wizard')
    
    # Install Command
    install_parser = subparsers.add_parser('install', help='Abhängigkeiten installieren')
    install_parser.add_argument('--upgrade', action='store_true', help='Packages aktualisieren')
    
    # Database Commands
    subparsers.add_parser('init-db', help='Datenbank initialisieren')
    
    # Test Commands
    subparsers.add_parser('test-api', help='API-Verbindungen testen')
    
    # Status Command
    subparsers.add_parser('status', help='System-Status anzeigen')
    
    # Run Command
    subparsers.add_parser('run', help='Hauptanwendung starten')
    
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
        install_dependencies(upgrade=args.upgrade)
    
    elif args.command == 'init-db':
        initialize_database()
    
    elif args.command == 'test-api':
        test_api_connection_detailed()
    
    elif args.command == 'status':
        show_system_status()
    
    elif args.command == 'run':
        try:
            import main
            main.main()
        except Exception as e:
            print(f"❌ Fehler beim Starten: {e}")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Kein Argument -> Setup-Wizard
        setup_wizard()
    else:
        # CLI-Modus
        cli_main()