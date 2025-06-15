#!/usr/bin/env python3
"""
Steam Price Tracker - Konsolidiertes Setup System
Vollständige Installation mit optionaler Charts-Integration
Kombiniert alle Setup-Funktionen in einer einzigen Datei
"""

import sys
import argparse
import subprocess
import requests
import json
import os
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
import logging

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SteamPriceTrackerSetup:
    """
    Konsolidiertes Setup-System für Steam Price Tracker
    Vereint Basic Setup und Charts-Integration
    """
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.backup_dir = self.project_root / "backup_before_setup"
        
        # Erforderliche Dateien für verschiedene Modi
        self.basic_files = [
            "main.py",
            "database_manager.py", 
            "price_tracker.py",
            "steam_wishlist_manager.py",
            "config.json",
            "requirements.txt"
        ]
        
        self.charts_files = [
            "steam_charts_manager.py",
            "charts_cli_manager.py"
        ]
        
        self.optional_files = [
            "batch_processor.py"
        ]
    
    # ========================
    # BASIC SETUP FUNCTIONS
    # ========================
    
    def check_python_version(self):
        """Prüft ob Python-Version kompatibel ist"""
        if sys.version_info < (3, 8):
            print("❌ Python 3.8 oder höher erforderlich")
            print(f"   Aktuelle Version: {sys.version}")
            return False
        
        print(f"✅ Python {sys.version.split()[0]} kompatibel")
        return True
    
    def install_dependencies(self, upgrade=False):
        """Installiert erforderliche Python-Pakete"""
        requirements_file = Path("requirements.txt")
        
        if not requirements_file.exists():
            print("⚠️ requirements.txt nicht gefunden - erstelle minimale Requirements")
            self.create_minimal_requirements()
        
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
    
    def create_minimal_requirements(self):
        """Erstellt minimale requirements.txt falls sie fehlt"""
        minimal_requirements = """# Steam Price Tracker - Dependencies
requests>=2.31.0
schedule>=1.2.0
python-dotenv>=1.0.0

# Optional: Enhanced Features
colorlog>=6.7.0
rich>=13.7.0
tqdm>=4.66.0
pandas>=2.0.0
jsonschema>=4.17.0

# Development (optional)
pytest>=7.4.0
black>=23.0.0
flake8>=6.0.0
"""
        
        try:
            with open("requirements.txt", "w", encoding="utf-8") as f:
                f.write(minimal_requirements)
            print("✅ Minimale requirements.txt erstellt")
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der requirements.txt: {e}")
    
    def create_env_file(self):
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

# Optional: Charts-Konfiguration
CHARTS_UPDATE_INTERVAL_HOURS=6
CHARTS_PRICE_INTERVAL_HOURS=4
CHARTS_CLEANUP_DAYS=30

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
    
    def initialize_database(self):
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
    
    def test_api_connection_detailed(self):
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
        
        # Test 4: Charts API (falls verfügbar)
        print("\n4️⃣ Steam Charts API Test...")
        if api_key:
            try:
                response = requests.get(
                    "https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/",
                    params={'key': api_key, 'count': 5},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'response' in data and 'ranks' in data['response']:
                        print("   ✅ Steam Charts API funktioniert")
                        print(f"   📊 {len(data['response']['ranks'])} Charts-Einträge abgerufen")
                    else:
                        print("   ⚠️ Steam Charts API antwortet, aber keine Charts-Daten")
                else:
                    print(f"   ❌ Steam Charts API Fehler: HTTP {response.status_code}")
                    
            except requests.RequestException as e:
                print(f"   ❌ Steam Charts API Verbindungsfehler: {e}")
        else:
            print("   ⚠️ Kein Steam API Key - Charts API Test übersprungen")
        
        print("\n📋 API-Test abgeschlossen")
    
    def create_directory_structure(self):
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
    
    # ========================
    # CHARTS INTEGRATION
    # ========================
    
    def create_backup(self) -> bool:
        """Erstellt Backup der bestehenden Dateien"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / timestamp
            backup_path.mkdir(parents=True, exist_ok=True)
            
            print(f"📦 Erstelle Backup in {backup_path}...")
            
            # Wichtige Dateien sichern
            files_to_backup = [
                "main.py",
                "database_manager.py",
                "price_tracker.py",
                "steam_price_tracker.db",
                ".env"
            ]
            
            backed_up = 0
            for file_name in files_to_backup:
                file_path = self.project_root / file_name
                if file_path.exists():
                    shutil.copy2(file_path, backup_path / file_name)
                    backed_up += 1
            
            print(f"✅ {backed_up} Dateien gesichert")
            
            # Backup-Info erstellen
            info_file = backup_path / "backup_info.txt"
            with open(info_file, 'w', encoding='utf-8') as f:
                f.write(f"Steam Price Tracker Backup\n")
                f.write(f"Erstellt: {datetime.now().isoformat()}\n")
                f.write(f"Zweck: Setup-Backup\n")
                f.write(f"Dateien: {backed_up}\n\n")
                f.write("Wiederherstellung:\n")
                f.write("1. Kopiere Dateien zurück ins Hauptverzeichnis\n")
                f.write("2. Starte python main.py\n")
            
            return True
            
        except Exception as e:
            print(f"❌ Backup fehlgeschlagen: {e}")
            return False
    
    def check_charts_prerequisites(self) -> dict:
        """Prüft Voraussetzungen für Charts-Integration"""
        checks = {
            'python_version': sys.version_info >= (3, 8),
            'existing_tracker': False,
            'database_exists': False,
            'api_key_present': False,
            'required_modules': True,
            'charts_files_present': True
        }
        
        # Bestehender Tracker prüfen
        main_py = self.project_root / "main.py"
        db_manager_py = self.project_root / "database_manager.py"
        checks['existing_tracker'] = main_py.exists() and db_manager_py.exists()
        
        # Datenbank prüfen
        db_file = self.project_root / "steam_price_tracker.db"
        checks['database_exists'] = db_file.exists()
        
        # API Key prüfen
        env_file = self.project_root / ".env"
        if env_file.exists():
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    checks['api_key_present'] = 'STEAM_API_KEY=' in content and 'your_steam_api_key_here' not in content
            except:
                pass
        
        # Erforderliche Module prüfen
        try:
            import requests
            import schedule
        except ImportError:
            checks['required_modules'] = False
        
        # Charts-Dateien prüfen
        missing_files = []
        for file_name in self.charts_files:
            if not (self.project_root / file_name).exists():
                missing_files.append(file_name)
        
        checks['charts_files_present'] = len(missing_files) == 0
        checks['missing_files'] = missing_files
        
        return checks
    
    def integrate_charts_in_database(self) -> bool:
        """Integriert Charts-Funktionalität in existierende Datenbank"""
        try:
            print("🗄️ Integriere Charts-Funktionalität in Datenbank...")
            
            # Teste ob Charts-Tabellen bereits existieren
            db_file = self.project_root / "steam_price_tracker.db"
            if not db_file.exists():
                print("❌ Datenbank nicht gefunden - führe zuerst Basic Setup durch")
                return False
            
            # Teste Charts-Tabellen
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            try:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%charts%'")
                charts_tables = [row[0] for row in cursor.fetchall()]
                
                if charts_tables:
                    print("✅ Charts-Tabellen bereits vorhanden")
                    conn.close()
                    return True
                
                # Charts-Tabellen erstellen
                print("📊 Erstelle Charts-Tabellen...")
                
                # Steam Charts Tracking Tabelle
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS steam_charts_tracking (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        steam_app_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        chart_type TEXT NOT NULL,
                        current_rank INTEGER DEFAULT 0,
                        best_rank INTEGER DEFAULT 999999,
                        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        total_appearances INTEGER DEFAULT 1,
                        active BOOLEAN DEFAULT 1,
                        metadata TEXT,
                        UNIQUE(steam_app_id, chart_type)
                    )
                ''')
                
                # Charts History
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS charts_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        steam_app_id TEXT NOT NULL,
                        chart_type TEXT NOT NULL,
                        rank_position INTEGER NOT NULL,
                        snapshot_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        additional_data TEXT,
                        FOREIGN KEY (steam_app_id) REFERENCES steam_charts_tracking (steam_app_id)
                    )
                ''')
                
                # Charts Price Snapshots
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS charts_price_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        steam_app_id TEXT NOT NULL,
                        game_title TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        steam_price REAL,
                        steam_original_price REAL,
                        steam_discount_percent INTEGER DEFAULT 0,
                        steam_available BOOLEAN DEFAULT 0,
                        greenmangaming_price REAL,
                        greenmangaming_original_price REAL,
                        greenmangaming_discount_percent INTEGER DEFAULT 0,
                        greenmangaming_available BOOLEAN DEFAULT 0,
                        gog_price REAL,
                        gog_original_price REAL,
                        gog_discount_percent INTEGER DEFAULT 0,
                        gog_available BOOLEAN DEFAULT 0,
                        humblestore_price REAL,
                        humblestore_original_price REAL,
                        humblestore_discount_percent INTEGER DEFAULT 0,
                        humblestore_available BOOLEAN DEFAULT 0,
                        fanatical_price REAL,
                        fanatical_original_price REAL,
                        fanatical_discount_percent INTEGER DEFAULT 0,
                        fanatical_available BOOLEAN DEFAULT 0,
                        gamesplanet_price REAL,
                        gamesplanet_original_price REAL,
                        gamesplanet_discount_percent INTEGER DEFAULT 0,
                        gamesplanet_available BOOLEAN DEFAULT 0,
                        is_chart_game BOOLEAN DEFAULT 1,
                        chart_types TEXT,
                        FOREIGN KEY (steam_app_id) REFERENCES steam_charts_tracking (steam_app_id)
                    )
                ''')
                
                # Indizes erstellen
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_tracking_app_id ON steam_charts_tracking(steam_app_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_tracking_chart_type ON steam_charts_tracking(chart_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_tracking_active ON steam_charts_tracking(active)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_history_app_id ON charts_history(steam_app_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_price_snapshots_app_id ON charts_price_snapshots(steam_app_id)')
                
                conn.commit()
                conn.close()
                
                print("✅ Charts-Tabellen erfolgreich erstellt")
                return True
                
            except sqlite3.Error as e:
                conn.rollback()
                conn.close()
                print(f"❌ Fehler beim Erstellen der Charts-Tabellen: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Fehler bei Charts-Datenbank-Integration: {e}")
            return False
    
    def test_charts_functionality(self) -> bool:
        """Testet die Charts-Funktionalität"""
        try:
            print("🧪 Teste Charts-Funktionalität...")
            
            # Teste ob Charts-Module importiert werden können
            try:
                from steam_charts_manager import SteamChartsManager
                print("✅ SteamChartsManager verfügbar")
            except ImportError as e:
                print(f"❌ SteamChartsManager nicht verfügbar: {e}")
                return False
            
            # Teste Charts CLI
            charts_cli = self.project_root / "charts_cli_manager.py"
            if charts_cli.exists():
                print("✅ Charts CLI verfügbar")
            else:
                print("⚠️ Charts CLI nicht gefunden")
            
            # Teste Integration mit Price Tracker
            try:
                from price_tracker import SteamPriceTracker
                from database_manager import DatabaseManager
                
                db = DatabaseManager()
                
                # Prüfe ob Charts-Methoden verfügbar sind
                if hasattr(db, 'init_charts_tables'):
                    print("✅ Charts-Datenbank-Integration verfügbar")
                else:
                    print("⚠️ Charts-Datenbank-Integration nicht verfügbar")
                
                return True
                
            except Exception as e:
                print(f"❌ Fehler beim Testen der Charts-Integration: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Charts-Funktionalitäts-Test fehlgeschlagen: {e}")
            return False
    
    # ========================
    # SETUP WORKFLOWS
    # ========================
    
    def basic_setup(self):
        """Führt Basic Setup durch"""
        print("🚀 BASIC SETUP - STEAM PRICE TRACKER")
        print("=" * 45)
        
        steps = [
            ("Python-Version prüfen", self.check_python_version),
            ("Abhängigkeiten installieren", self.install_dependencies),
            ("Verzeichnisse erstellen", self.create_directory_structure),
            (".env-Datei erstellen", self.create_env_file),
            ("Datenbank initialisieren", self.initialize_database),
            ("API-Verbindungen testen", self.test_api_connection_detailed)
        ]
        
        return self._execute_setup_steps(steps, "Basic Setup")
    
    def charts_setup(self):
        """Führt Charts-Integration durch"""
        print("📊 CHARTS SETUP - STEAM CHARTS INTEGRATION")
        print("=" * 50)
        
        # Prüfe Voraussetzungen
        print("🔍 Prüfe Charts-Voraussetzungen...")
        checks = self.check_charts_prerequisites()
        
        if not checks['existing_tracker']:
            print("❌ Basic Steam Price Tracker nicht gefunden")
            print("💡 Führe zuerst 'python setup.py basic' aus")
            return False
        
        steps = [
            ("Backup erstellen", self.create_backup),
            ("Charts-Datenbank integrieren", self.integrate_charts_in_database),
            ("Charts-Funktionalität testen", self.test_charts_functionality)
        ]
        
        return self._execute_setup_steps(steps, "Charts Setup")
    
    def full_setup(self):
        """Führt vollständiges Setup durch"""
        print("🌟 FULL SETUP - COMPLETE STEAM PRICE TRACKER")
        print("=" * 55)
        
        print("Dieses Setup installiert alles:")
        print("• Basic Steam Price Tracker")
        print("• Charts-Integration")
        print("• Alle optionalen Features")
        print()
        
        # Basic Setup
        print("\n📦 PHASE 1: BASIC SETUP")
        print("-" * 25)
        if not self.basic_setup():
            print("❌ Basic Setup fehlgeschlagen")
            return False
        
        # Charts Setup
        print("\n📊 PHASE 2: CHARTS SETUP") 
        print("-" * 25)
        if not self.charts_setup():
            print("⚠️ Charts Setup fehlgeschlagen, aber Basic funktioniert")
        
        # Abschluss
        self._show_completion_summary()
        return True
    
    def _execute_setup_steps(self, steps, setup_name):
        """Führt Setup-Schritte aus"""
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
                    if i <= 3:
                        continue_setup = input("\n⚠️ Trotzdem fortfahren? (j/n): ").lower().strip()
                        if continue_setup not in ['j', 'ja', 'y', 'yes']:
                            print("⏹️ Setup abgebrochen")
                            return False
                            
            except Exception as e:
                print(f"❌ Unerwarteter Fehler in Schritt {i}: {e}")
        
        print(f"\n🎯 {setup_name.upper()} ABGESCHLOSSEN")
        print("=" * 30)
        print(f"✅ {success_steps}/{total_steps} Schritte erfolgreich")
        
        return success_steps >= (total_steps * 0.8)  # 80% Erfolgsrate
    
    def _show_completion_summary(self):
        """Zeigt Abschluss-Zusammenfassung"""
        print(f"\n🎉 SETUP VOLLSTÄNDIG ABGESCHLOSSEN!")
        print("=" * 50)
        
        print("\n📁 INSTALLIERTE KOMPONENTEN:")
        print("✅ Steam Price Tracker (Core)")
        print("✅ Database Manager mit Charts-Support")
        print("✅ Steam Wishlist Integration")
        print("✅ CheapShark API Integration") 
        print("✅ Automatisches Scheduling")
        print("✅ CSV Export Funktionalität")
        
        # Prüfe optionale Komponenten
        if (self.project_root / "steam_charts_manager.py").exists():
            print("✅ Steam Charts Manager")
        if (self.project_root / "charts_cli_manager.py").exists():
            print("✅ Charts CLI Tools")
        if (self.project_root / "batch_processor.py").exists():
            print("✅ Batch Processing Tools")
        
        print("\n🚀 NÄCHSTE SCHRITTE:")
        print("1. Starte die Hauptanwendung:")
        print("   python main.py")
        print("")
        print("2. Oder nutze CLI-Tools:")
        print("   python batch_processor.py stats")
        if (self.project_root / "charts_cli_manager.py").exists():
            print("   python charts_cli_manager.py status")
        print("")
        print("3. Automatisches Tracking einrichten:")
        print("   • Starte main.py")
        print("   • Importiere deine Steam Wishlist")
        print("   • Aktiviere automatisches Tracking")
        
        print("\n💡 HILFE & DOKUMENTATION:")
        print("• README.md - Vollständige Dokumentation")
        print("• .env - Konfigurationseinstellungen")
        print("• python main.py - Interaktive Benutzeroberfläche")
        
        print("\n🛠️ SUPPORT:")
        print(f"• Backup verfügbar in: {self.backup_dir}/")
        print("• Bei Problemen: Verwende Backup zur Wiederherstellung")
        print("• Logs verfügbar in: logs/")
    
    def show_system_status(self):
        """Zeigt detaillierten System-Status an"""
        print("📊 STEAM PRICE TRACKER - SYSTEM STATUS")
        print("=" * 50)
        
        # Python-Version
        print(f"🐍 Python: {sys.version.split()[0]}")
        
        # Dateien prüfen
        all_files = self.basic_files + self.charts_files + self.optional_files
        existing_files = [f for f in all_files if (self.project_root / f).exists()]
        missing_files = [f for f in self.basic_files if not (self.project_root / f).exists()]
        
        print(f"📁 Dateien: {len(existing_files)}/{len(all_files)} vorhanden")
        if missing_files:
            print(f"❌ Fehlende kritische Dateien: {', '.join(missing_files)}")
        else:
            print("✅ Alle kritischen Dateien vorhanden")
        
        # .env-Datei
        env_file = self.project_root / ".env"
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
            
            # Charts-Funktionalität
            if hasattr(db, 'get_charts_statistics'):
                charts_stats = db.get_charts_statistics()
                if charts_stats:
                    print(f"📊 Charts: Verfügbar ({charts_stats.get('total_active_charts_games', 0)} Charts-Apps)")
                else:
                    print("📊 Charts: Verfügbar aber nicht aktiv")
            else:
                print("📊 Charts: Nicht verfügbar")
                
        except Exception as e:
            print(f"❌ Datenbank: Fehler - {e}")
        
        # Abhängigkeiten
        required_modules = ['requests', 'schedule', 'sqlite3']
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
        missing_dirs = [d for d in directories if not (self.project_root / d).exists()]
        
        if missing_dirs:
            print(f"⚠️ Verzeichnisse: {', '.join(missing_dirs)} fehlen")
        else:
            print("✅ Verzeichnisse: Vollständig")
        
        # Empfehlungen
        print(f"\n💡 EMPFEHLUNGEN:")
        if missing_files:
            print("• Führe 'python setup.py basic' aus")
        if not env_file.exists() or 'your_steam_api_key_here' in (env_file.read_text() if env_file.exists() else ''):
            print("• Konfiguriere Steam API Key in .env")
        if not (self.project_root / "steam_charts_manager.py").exists():
            print("• Für Charts: 'python setup.py charts' ausführen")

def main():
    """Hauptfunktion für konsolidiertes Setup"""
    setup = SteamPriceTrackerSetup()
    
    parser = argparse.ArgumentParser(
        description="Steam Price Tracker - Konsolidiertes Setup System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Setup-Modi:
  basic                     - Grundinstallation (empfohlen für Einsteiger)
  charts                    - Charts-Integration (erfordert Basic Setup)
  full                      - Vollständiges Setup (Basic + Charts)
  status                    - System-Status anzeigen

Wartungs-Kommandos:
  install [--upgrade]       - Nur Abhängigkeiten installieren
  init-db                   - Nur Datenbank initialisieren
  test-api                  - Nur API-Tests durchführen
  backup                    - Backup erstellen

Beispiele:
  %(prog)s basic            - Grundinstallation
  %(prog)s full             - Alles installieren
  %(prog)s status           - Status prüfen
  %(prog)s install --upgrade - Pakete aktualisieren
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Setup-Modus')
    
    # Setup Modes
    subparsers.add_parser('basic', help='Grundinstallation')
    subparsers.add_parser('charts', help='Charts-Integration')
    subparsers.add_parser('full', help='Vollständiges Setup')
    subparsers.add_parser('status', help='System-Status anzeigen')
    
    # Maintenance Commands
    install_parser = subparsers.add_parser('install', help='Abhängigkeiten installieren')
    install_parser.add_argument('--upgrade', action='store_true', help='Packages aktualisieren')
    
    subparsers.add_parser('init-db', help='Datenbank initialisieren')
    subparsers.add_parser('test-api', help='API-Tests durchführen')
    subparsers.add_parser('backup', help='Backup erstellen')
    
    args = parser.parse_args()
    
    if not args.command:
        # Kein Argument -> Interaktives Setup
        print("Kein Setup-Modus angegeben - zeige interaktives Menü\n")
        
        print("🚀 STEAM PRICE TRACKER SETUP")
        print("=" * 35)
        print("1. Basic Setup (empfohlen für Einsteiger)")
        print("2. Charts Setup (erweiterte Features)")
        print("3. Full Setup (alles installieren)")
        print("4. System Status anzeigen")
        print("5. Beenden")
        
        while True:
            choice = input("\nWählen Sie eine Option (1-5): ").strip()
            
            if choice == "1":
                setup.basic_setup()
                break
            elif choice == "2":
                setup.charts_setup()
                break
            elif choice == "3":
                setup.full_setup()
                break
            elif choice == "4":
                setup.show_system_status()
                break
            elif choice == "5":
                print("👋 Setup beendet")
                break
            else:
                print("❌ Ungültige Auswahl")
        return
    
    # Führe entsprechendes Kommando aus
    try:
        if args.command == 'basic':
            setup.basic_setup()
        elif args.command == 'charts':
            setup.charts_setup()
        elif args.command == 'full':
            setup.full_setup()
        elif args.command == 'status':
            setup.show_system_status()
        elif args.command == 'install':
            setup.check_python_version()
            setup.install_dependencies(upgrade=args.upgrade)
        elif args.command == 'init-db':
            setup.initialize_database()
        elif args.command == 'test-api':
            setup.test_api_connection_detailed()
        elif args.command == 'backup':
            setup.create_backup()
            
    except KeyboardInterrupt:
        print("\n⏹️ Setup abgebrochen durch Benutzer")
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        logger.exception("Setup-Fehler")

if __name__ == "__main__":
    main()
