#!/usr/bin/env python3
"""
Steam Price Tracker - Setup und CLI (Verbessert)
Erweiterte Diagnostik für API Key Probleme
"""

import sys
import argparse
import subprocess
import requests
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
                            print(f"   🔑 API Key: {key_value[:8]}... (Länge: {len(key_value)})")
                            if len(key_value) != 32:
                                print("   ⚠️ Ungewöhnliche Key-Länge (erwartet: 32 Zeichen)")
                        else:
                            print("   ⚠️ API Key ist leer oder Platzhalter")
                        break
            else:
                print("   ⚠️ Kein STEAM_API_KEY in .env gefunden")
                
        except Exception as e:
            print(f"   ⚠️ Konnte .env nicht lesen: {e}")
        
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
    
    # API Key abfragen mit Validierung
    print("\n🔑 STEAM API KEY KONFIGURATION:")
    print("1. Gehe zu: https://steamcommunity.com/dev/apikey")
    print("2. Erstelle einen neuen API Key")
    print("3. Kopiere den Key hier rein")
    print("💡 Der Key sollte 32 Zeichen lang sein (nur Buchstaben und Zahlen)")
    
    api_key = input("\nSteam API Key eingeben (Enter zum Überspringen): ").strip()
    
    if api_key:
        # API Key validieren
        if len(api_key) != 32:
            print(f"⚠️ API Key hat {len(api_key)} Zeichen (erwartet: 32)")
            confirm = input("Trotzdem verwenden? (j/n): ").lower().strip()
            if confirm not in ['j', 'ja', 'y', 'yes']:
                print("❌ API Key abgelehnt")
                return False
        
        if not all(c.isalnum() for c in api_key):
            print("⚠️ API Key enthält Sonderzeichen")
            confirm = input("Trotzdem verwenden? (j/n): ").lower().strip()
            if confirm not in ['j', 'ja', 'y', 'yes']:
                print("❌ API Key abgelehnt")
                return False
        
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

def test_api_connection_detailed():
    """Erweiterte Steam API Verbindung mit detailliertem Debugging"""
    try:
        from steam_wishlist_manager import load_api_key_from_env
        
        api_key = load_api_key_from_env()
        if not api_key:
            print("⚠️ Kein API Key für Test verfügbar")
            return False
        
        print("🔌 Teste Steam API Verbindung...")
        print(f"   🔑 API Key: {api_key[:8]}... (Länge: {len(api_key)})")
        
        # Direkter API Test ohne SteamWishlistManager
        test_steam_id = "76561197960435530"  # Gabe Newell
        url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
        
        params = {
            'key': api_key,
            'steamids': test_steam_id,
            'format': 'json'
        }
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'SteamPriceTracker/1.0'
        })
        
        print(f"   🌐 URL: {url}")
        print(f"   👤 Test Steam ID: {test_steam_id}")
        
        try:
            response = session.get(url, params=params, timeout=30)
            
            print(f"   📊 HTTP Status: {response.status_code}")
            print(f"   📏 Response Size: {len(response.content)} bytes")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    players = data.get('response', {}).get('players', [])
                    
                    if players and len(players) > 0:
                        player = players[0]
                        username = player.get('personaname', 'Unknown')
                        print(f"✅ Steam API funktioniert - Test-User: {username}")
                        return True
                    else:
                        print("❌ Steam API: Keine Spielerdaten erhalten")
                        print(f"   Raw Response: {response.text[:200]}...")
                        return False
                        
                except Exception as e:
                    print(f"❌ JSON Parse Error: {e}")
                    print(f"   Raw Response: {response.text[:200]}...")
                    return False
                    
            elif response.status_code == 401:
                print("❌ HTTP 401: Unauthorized")
                print("   💡 API Key ist ungültig oder falsch")
                print("   🔧 Lösung: Neuen API Key auf https://steamcommunity.com/dev/apikey erstellen")
                return False
                
            elif response.status_code == 403:
                print("❌ HTTP 403: Forbidden")
                print("   💡 API Key hat keine Berechtigung für diesen Endpoint")
                return False
                
            elif response.status_code == 429:
                print("❌ HTTP 429: Too Many Requests")
                print("   💡 Mögliche Ursachen:")
                print("      - Rate Limiting aktiv")
                print("      - API Key ist ungültig (Steam antwortet manchmal mit 429)")
                print("      - Steam Server überlastet")
                
                # Teste einfacheren Endpoint ohne API Key
                print("   🧪 Teste öffentlichen Endpoint...")
                try:
                    test_response = session.get(
                        "https://api.steampowered.com/ISteamApps/GetAppList/v2/",
                        params={'format': 'json'},
                        timeout=15
                    )
                    
                    if test_response.status_code == 200:
                        print("   ✅ Öffentlicher Endpoint funktioniert - Problem liegt am API Key")
                        print("   🔧 Lösung: API Key auf https://steamcommunity.com/dev/apikey überprüfen")
                    else:
                        print(f"   ❌ Auch öffentlicher Endpoint fehlgeschlagen: {test_response.status_code}")
                        print("   💡 Möglicherweise Steam Server Problem")
                        
                except Exception as e:
                    print(f"   ❌ Test des öffentlichen Endpoints fehlgeschlagen: {e}")
                
                return False
                
            else:
                print(f"❌ HTTP {response.status_code}: Unbekannter Fehler")
                try:
                    print(f"   Content: {response.text[:200]}...")
                except:
                    pass
                return False
                
        except requests.exceptions.Timeout:
            print("❌ Request Timeout - Steam API antwortet nicht")
            return False
            
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error - Keine Verbindung zu Steam API")
            return False
            
    except ImportError as e:
        print(f"⚠️ Steam API Test übersprungen: {e}")
        return False
    except Exception as e:
        print(f"❌ Steam API Test Fehler: {e}")
        return False

def setup_wizard():
    """Vollständiger Setup-Wizard"""
    print("💰 STEAM PRICE TRACKER - SETUP WIZARD v1.1")
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
    print("\n6️⃣ STEAM API TESTEN (ERWEITERT)")
    if test_api_connection_detailed():
        success_steps += 1
    else:
        print("\n💡 API TEST FEHLGESCHLAGEN - NÄCHSTE SCHRITTE:")
        print("1. 🔗 Besuche: https://steamcommunity.com/dev/apikey")
        print("2. 📝 Erstelle einen neuen API Key")
        print("3. 📋 Kopiere den Key in deine .env-Datei")
        print("4. 🔄 Führe 'python setup.py test-api' erneut aus")
    
    # Zusammenfassung
    print(f"\n🎉 SETUP ABGESCHLOSSEN!")
    print(f"✅ {success_steps}/{total_steps} Schritte erfolgreich")
    
    if success_steps >= 4:
        print("\n💡 NÄCHSTE SCHRITTE:")
        print("1. 🚀 Starte die Hauptanwendung: python main.py")
        print("2. 📥 Importiere deine Steam Wishlist")
        print("3. 🔄 Aktiviere automatisches Preis-Tracking")
        print("4. 📊 Überwache Preisänderungen und Deals")
        
        if success_steps < 6:
            print("\n⚠️ API Test fehlgeschlagen aber Setup funktional!")
            print("💡 Du kannst das Programm trotzdem nutzen - API Problem später lösen")
        
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
  %(prog)s test-api                 - Nur Steam API testen (erweitert)
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
    subparsers.add_parser('test-api', help='Steam API testen (erweitert)')
    
    # Debug Command
    subparsers.add_parser('debug', help='Vollständige API Diagnostik')
    
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
        test_api_connection_detailed()
    
    elif args.command == 'debug':
        # Führe das externe Debug-Tool aus
        print("🔍 Starte erweiterte API Diagnostik...")
        try:
            exec(open('debug_steam_api.py').read())
        except FileNotFoundError:
            print("❌ debug_steam_api.py nicht gefunden")
            print("💡 Führe stattdessen erweiterten API Test aus:")
            test_api_connection_detailed()
    
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
                print(f"✅ Steam API Key: Konfiguriert ({api_key[:8]}...)")
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