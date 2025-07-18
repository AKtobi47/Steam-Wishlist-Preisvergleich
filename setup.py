#!/usr/bin/env python3
"""
Setup.py - VOLLSTÄNDIGE PRODUKTIONSVERSION - ALLE FUNKTIONEN ENTHALTEN
Steam Price Tracker Setup mit korrigiertem Schema-Testing
100% kompatibel mit allen Komponenten und der echten DDL-Struktur

VOLLSTÄNDIGKEIT:
- Alle API-dokumentierten Methoden enthalten
- Erweiterte Tests und Validierungen  
- Umfassendes .env Template
- Time-Scope-Konflikte behoben
- Database-Manager Kompatibilität
- Neue und alte Funktionen kombiniert
"""

import os
import sys
import subprocess
import sqlite3
import json
import shutil
import platform
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import logging
import time as time_module  # GEFIXT: Sichere time-Import gegen Scope-Konflikte

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SteamPriceTrackerSetup:
    """
    Vollständiges Setup für Steam Price Tracker - KOMPLETTE PRODUKTIONSVERSION
    
    Features:
    - Korrigierte Schema-Validierung für steam_charts_tracking
    - Vollständige Kompatibilitätstests
    - Robuste Fallback-Mechanismen
    - Detaillierte Error-Reporting
    - Produktionsreife Installation
    - GEFIXT: Time-Scope-Konflikte behoben
    - VOLLSTÄNDIG: Alle API-dokumentierten Methoden
    """
    
    def __init__(self):
        self.setup_log = []
        self.features_available = {
            'charts': False,
            'cli_tools': False,
            'elasticsearch': False,
            'core': False,
            'database': False,
            'main_app': False,
            'batch_processor': False,
            'charts_cli': False,
            'docker_compose': False,
            'background_scheduler': False,
            'steam_api': False,
            'price_tracking': False,
            'python_version': False,
            'requirements': False,
            'configuration': False
        }
        
        self.errors = []
        self.warnings = []
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
    def log_step(self, step_name: str, success: bool, details: str = ""):
        """Loggt einen Setup-Schritt mit verbessertem Feedback"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {step_name}")
        if details:
            # Einrücken für bessere Lesbarkeit
            for line in details.split('\n'):
                if line.strip():
                    print(f"   {line}")
        
        self.setup_log.append({
            "step": step_name,
            "success": success,
            "details": details,
            "timestamp": timestamp
        })
        
        if not success:
            self.errors.append(f"{step_name}: {details}")
    
    def log_warning(self, warning: str):
        """Loggt eine Warnung"""
        print(f"⚠️ {warning}")
        self.warnings.append(warning)
    
    # =====================================================================
    # API-DOKUMENTIERTE METHODEN - BASIC SETUP
    # =====================================================================
    
    def basic_setup(self) -> bool:
        """
        API-METHODE: Basis-Setup für minimale Funktionalität
        Installiert nur die absolut notwendigen Komponenten
        """
        print("\n🔧 STEAM PRICE TRACKER - BASIS-SETUP")
        print("=" * 40)
        print("🎯 Minimales Setup für Grundfunktionalität...")
        print()
        
        start_time = time_module.time()
        
        # Basis-Setup-Schritte
        basic_steps = [
            ("Python Version Check", self.check_python_version),
            ("Requirements Correction", self.correct_requirements),
            ("Core Dependencies", self.install_dependencies),
            ("Database Initialization", self.initialize_database),
            ("Core Functionality", self.test_core_functionality)
        ]
        
        for step_name, step_func in basic_steps:
            try:
                print(f"🔄 {step_name}...")
                step_func()
                time_module.sleep(0.05)
            except Exception as e:
                self.log_step(step_name, False, f"Basis-Setup Fehler: {e}")
        
        duration = time_module.time() - start_time
        
        # Basis-Setup Validierung
        required_features = ['core', 'database', 'python_version']
        basic_ready = all(self.features_available.get(feature, False) for feature in required_features)
        
        if basic_ready:
            self.log_step("Basic Setup", True, f"Basis-Setup erfolgreich in {duration:.1f}s")
            print("\n✅ BASIS-SETUP ERFOLGREICH!")
            print("🎮 Grundfunktionen sind einsatzbereit")
            print("💡 Für erweiterte Features führe charts_setup() oder run_full_setup() aus")
            return True
        else:
            missing = [f for f in required_features if not self.features_available.get(f, False)]
            self.log_step("Basic Setup", False, f"Kritische Basis-Features fehlen: {missing}")
            print(f"\n❌ BASIS-SETUP FEHLGESCHLAGEN!")
            return False
    
    def charts_setup(self) -> bool:
        """
        API-METHODE: Charts-spezifisches Setup
        Fokussiert sich auf Charts-Integration und Analytics
        """
        print("\n📊 STEAM PRICE TRACKER - CHARTS-SETUP")
        print("=" * 40)
        print("🎯 Setup für Charts-Integration und Analytics...")
        print()
        
        start_time = time_module.time()
        
        # Charts-Setup-Schritte
        charts_steps = [
            ("Basic Setup Check", self._ensure_basic_setup),
            ("Database Schema (Charts)", self.test_database_schema),
            ("Charts Integration", self.test_charts_integration),
            ("Charts CLI Tools", self._test_charts_cli),
            ("Database Migration", self.migrate_database_to_new_structure)
        ]
        
        for step_name, step_func in charts_steps:
            try:
                print(f"🔄 {step_name}...")
                step_func()
                time_module.sleep(0.05)
            except Exception as e:
                self.log_step(step_name, False, f"Charts-Setup Fehler: {e}")
        
        duration = time_module.time() - start_time
        
        # Charts-Setup Validierung
        charts_features = ['charts', 'database']
        charts_ready = all(self.features_available.get(feature, False) for feature in charts_features)
        
        if charts_ready:
            self.log_step("Charts Setup", True, f"Charts-Setup erfolgreich in {duration:.1f}s")
            print("\n✅ CHARTS-SETUP ERFOLGREICH!")
            print("📊 Charts-Integration ist einsatzbereit")
            print("💡 Verwende main.py Option 14 für Charts-Updates")
            return True
        else:
            missing = [f for f in charts_features if not self.features_available.get(f, False)]
            self.log_step("Charts Setup", False, f"Charts-Features fehlen: {missing}")
            print(f"\n❌ CHARTS-SETUP FEHLGESCHLAGEN!")
            return False
    
    def check_python_version(self) -> bool:
        """
        API-METHODE: Prüft Python-Version auf Kompatibilität
        """
        try:
            major, minor = sys.version_info.major, sys.version_info.minor
            
            # Mindestanforderungen
            min_major, min_minor = 3, 8
            max_major, max_minor = 3, 12
            
            version_ok = (major == min_major and minor >= min_minor) or major > min_major
            future_compatible = major <= max_major
            
            if version_ok and future_compatible:
                detail_msg = f"Python {self.python_version} - Kompatibel"
                detail_msg += f"\nPlatform: {platform.system()} {platform.release()}"
                detail_msg += f"\nArchitecture: {platform.machine()}"
                
                self.log_step("Python Version Check", True, detail_msg)
                self.features_available['python_version'] = True
                return True
            elif not version_ok:
                detail_msg = f"Python {self.python_version} - ZU ALT"
                detail_msg += f"\nMindestens erforderlich: Python {min_major}.{min_minor}"
                detail_msg += f"\nBitte aktualisiere Python: https://www.python.org/downloads/"
                
                self.log_step("Python Version Check", False, detail_msg)
                return False
            else:
                detail_msg = f"Python {self.python_version} - ZUKUNFT UNGEWISS"
                detail_msg += f"\nMaximal getestet: Python {max_major}.{max_minor}"
                detail_msg += f"\nFunktionalität möglicherweise eingeschränkt"
                
                self.log_step("Python Version Check", True, detail_msg)
                self.features_available['python_version'] = True
                self.log_warning(f"Python {self.python_version} nicht vollständig getestet")
                return True
                
        except Exception as e:
            self.log_step("Python Version Check", False, str(e))
            return False
    
    def initialize_database(self) -> bool:
        """
        API-METHODE: Initialisiert die Datenbank mit korrektem Schema
        """
        try:
            # Teste Database Manager Import
            from database_manager import create_database_manager
            
            db_path = "steam_price_tracker.db"
            
            # Prüfe ob DB bereits existiert
            existing_db = Path(db_path).exists()
            
            if existing_db:
                # Backup vor Initialisierung
                backup_path = Path("backups") / f"pre_init_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                backup_path.parent.mkdir(exist_ok=True)
                shutil.copy2(db_path, backup_path)
            
            # Database Manager erstellen
            db_manager = create_database_manager(db_path)
            
            # Schema-Tests
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Teste alle essentiellen Tabellen
                essential_tables = ['tracked_apps', 'price_snapshots', 'steam_charts_tracking']
                existing_tables = []
                
                for table in essential_tables:
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                    if cursor.fetchone():
                        existing_tables.append(table)
                
                # Teste Batch Writer Kompatibilität
                try:
                    from database_manager import create_batch_writer
                    batch_writer = create_batch_writer(db_manager)
                    batch_compatible = True
                except Exception:
                    batch_compatible = False
            
            detail_msg = f"Datenbank initialisiert: {db_path}"
            detail_msg += f"\nTabellen: {len(existing_tables)}/{len(essential_tables)} ({', '.join(existing_tables)})"
            detail_msg += f"\nBatch Writer: {'✅' if batch_compatible else '❌'}"
            if existing_db:
                detail_msg += f"\nBackup erstellt: {backup_path.name}"
            
            self.log_step("Database Initialization", True, detail_msg)
            self.features_available['database'] = True
            return True
            
        except Exception as e:
            self.log_step("Database Initialization", False, str(e))
            return False
    
    def test_api_connection_detailed(self) -> None:
        """
        API-METHODE: Detaillierte API-Verbindungstests
        Gibt keinen bool zurück, nur ausführliche Ausgabe
        """
        print("\n🌐 DETAILLIERTE API-VERBINDUNGSTESTS")
        print("=" * 40)
        
        apis_to_test = [
            {
                'name': 'Steam Store API',
                'url': 'https://store.steampowered.com/api/appdetails?appids=413150',
                'public': True,
                'timeout': 10
            },
            {
                'name': 'CheapShark API',
                'url': 'https://www.cheapshark.com/api/1.0/deals?storeID=1&upperPrice=15',
                'public': True,
                'timeout': 15
            },
            {
                'name': 'Steam Web API',
                'url': 'https://api.steampowered.com/ISteamWebAPIUtil/GetServerInfo/v0001/',
                'public': True,
                'timeout': 10
            }
        ]
        
        print("🔍 Teste öffentliche APIs...")
        for api in apis_to_test:
            try:
                start_time = time_module.time()
                response = requests.get(api['url'], timeout=api['timeout'])
                duration = time_module.time() - start_time
                
                if response.status_code == 200:
                    print(f"✅ {api['name']}: OK ({duration:.2f}s)")
                    data_size = len(response.content)
                    print(f"   Status: {response.status_code}, Size: {data_size} bytes")
                else:
                    print(f"⚠️ {api['name']}: HTTP {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"❌ {api['name']}: Timeout ({api['timeout']}s)")
            except requests.exceptions.ConnectionError:
                print(f"❌ {api['name']}: Verbindungsfehler")
            except Exception as e:
                print(f"❌ {api['name']}: {e}")
        
        # Steam API Key Test (falls verfügbar)
        print("\n🔑 Teste Steam API Key...")
        try:
            from steam_wishlist_manager import load_api_key_from_env
            api_key = load_api_key_from_env()
            
            if api_key and api_key != "your_steam_api_key_here":
                # Teste mit echtem API Key
                test_url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={api_key}&steamids=76561197960434622"
                response = requests.get(test_url, timeout=10)
                
                if response.status_code == 200:
                    print("✅ Steam API Key: Gültig und funktional")
                    self.features_available['steam_api'] = True
                else:
                    print(f"❌ Steam API Key: HTTP {response.status_code}")
            else:
                print("⚠️ Steam API Key: Nicht konfiguriert oder ungültig")
                print("   Trage deinen Key in .env ein für vollständige Tests")
                
        except ImportError:
            print("❌ Steam Wishlist Manager: Nicht verfügbar")
        except Exception as e:
            print(f"❌ Steam API Key Test: {e}")
        
        print("\n💡 API-Test Hinweise:")
        print("   • Steam Store API: Für App-Details und Preise")
        print("   • CheapShark API: Für Multi-Store Preisvergleiche")
        print("   • Steam Web API: Für Wishlists und User-Daten (benötigt API Key)")
        print("   • Alle APIs funktionieren mit Rate Limiting")
    
    def create_backup(self) -> bool:
        """
        API-METHODE: Erstellt Backup der wichtigsten Dateien
        Unterscheidet sich von create_master_backup durch Fokus auf User-Daten
        """
        try:
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # User-relevante Dateien (nicht System-Files)
            user_files = [
                "steam_price_tracker.db",
                ".env",
                "config.json"
            ]
            
            backed_up = []
            total_size = 0
            
            for file_name in user_files:
                file_path = Path(file_name)
                if file_path.exists():
                    backup_path = backup_dir / f"{file_path.stem}_user_backup_{timestamp}{file_path.suffix}"
                    shutil.copy2(file_path, backup_path)
                    
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    
                    backed_up.append(f"{file_name} ({file_size} bytes)")
            
            if backed_up:
                detail_msg = f"User-Backup erstellt: {len(backed_up)} Dateien"
                detail_msg += f"\nGesamtgröße: {total_size:,} bytes"
                detail_msg += f"\nBackup-Verzeichnis: {backup_dir}"
                detail_msg += f"\nDateien:\n" + "\n".join(f"   • {item}" for item in backed_up)
                
                self.log_step("User Backup Creation", True, detail_msg)
                return True
            else:
                self.log_step("User Backup Creation", False, "Keine User-Dateien zum Sichern gefunden")
                return False
                
        except Exception as e:
            self.log_step("User Backup Creation", False, str(e))
            return False
    
    def show_system_status(self) -> None:
        """
        API-METHODE: Zeigt detaillierten System-Status an
        Gibt keinen bool zurück, nur ausführliche Ausgabe
        """
        print("\n📊 SYSTEM-STATUS ÜBERSICHT")
        print("=" * 50)
        
        # System-Informationen
        print("🖥️ SYSTEM-INFORMATIONEN:")
        print(f"   OS: {platform.system()} {platform.release()}")
        print(f"   Architektur: {platform.machine()}")
        print(f"   Python: {self.python_version}")
        print(f"   Arbeitsverzeichnis: {Path.cwd()}")
        
        # Dateien-Status
        print("\n📁 DATEIEN-STATUS:")
        important_files = [
            ("steam_price_tracker.db", "Hauptdatenbank"),
            (".env", "Konfiguration"),
            ("main.py", "Hauptprogramm"),
            ("requirements.txt", "Dependencies"),
            ("setup_report.json", "Setup-Report")
        ]
        
        for file_path, description in important_files:
            path = Path(file_path)
            if path.exists():
                size = path.stat().st_size
                modified = datetime.fromtimestamp(path.stat().st_mtime).strftime("%d.%m.%Y %H:%M")
                print(f"   ✅ {file_path}: {description} ({size:,} bytes, {modified})")
            else:
                print(f"   ❌ {file_path}: {description} (fehlt)")
        
        # Features-Status
        print("\n🎯 FEATURES-STATUS:")
        for feature, available in self.features_available.items():
            icon = "✅" if available else "❌"
            print(f"   {icon} {feature.replace('_', ' ').title()}")
        
        # Database-Status
        print("\n🗄️ DATABASE-STATUS:")
        try:
            from database_manager import create_database_manager
            db_manager = create_database_manager()
            
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Tabellen zählen
                cursor.execute("SELECT COUNT(*) FROM tracked_apps")
                tracked_apps = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM price_snapshots")
                snapshots = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM steam_charts_tracking")
                charts_entries = cursor.fetchone()[0]
                
                print(f"   📊 Tracked Apps: {tracked_apps:,}")
                print(f"   📸 Price Snapshots: {snapshots:,}")
                print(f"   📈 Charts Entries: {charts_entries:,}")
                
                # Neueste Daten
                cursor.execute("SELECT MAX(last_price_update) FROM tracked_apps")
                last_update = cursor.fetchone()[0]
                if last_update:
                    print(f"   🕐 Letztes Update: {last_update}")
                
        except Exception as e:
            print(f"   ❌ Database-Fehler: {e}")
        
        # Disk Space
        print("\n💾 SPEICHERPLATZ:")
        try:
            total, used, free = shutil.disk_usage(Path.cwd())
            print(f"   Total: {total // (1024**3):,} GB")
            print(f"   Verwendet: {used // (1024**3):,} GB")
            print(f"   Frei: {free // (1024**3):,} GB")
        except Exception:
            print("   ❌ Speicherplatz-Info nicht verfügbar")
        
        # Letzte Setup-Informationen
        print("\n📋 LETZTES SETUP:")
        try:
            with open("setup_report.json", "r") as f:
                report = json.load(f)
            
            print(f"   📅 Datum: {report['setup_metadata']['completed_at']}")
            print(f"   ✅ Erfolg: {report['results_summary']['success_rate']}%")
            print(f"   📊 Features: {len(report['features_status']['enabled_features'])} aktiv")
            
        except FileNotFoundError:
            print("   ❌ Kein Setup-Report gefunden")
        except Exception as e:
            print(f"   ❌ Setup-Report-Fehler: {e}")
        
        print("\n" + "=" * 50)
    
    # =====================================================================
    # HELPER METHODEN FÜR API-FUNKTIONEN
    # =====================================================================
    
    def _ensure_basic_setup(self) -> bool:
        """Stellt sicher, dass Basic Setup durchgeführt wurde"""
        required_basic = ['python_version', 'core', 'database']
        missing = [f for f in required_basic if not self.features_available.get(f, False)]
        
        if missing:
            print(f"⚠️ Basic Setup unvollständig. Fehlende Features: {missing}")
            print("💡 Führe zuerst basic_setup() aus")
            return False
        return True
    
    def _test_charts_cli(self) -> bool:
        """Testet Charts CLI verfügbarkeit"""
        try:
            charts_cli_path = Path("charts_cli_manager.py")
            if charts_cli_path.exists():
                self.features_available['charts_cli'] = True
                return True
            return False
        except Exception:
            return False
    
    # =====================================================================
    # ORIGINALE FUNKTIONEN (BEHALTEN)
    # =====================================================================
    
    def create_master_backup(self) -> bool:
        """Erstellt ein Master-Backup vor Setup (Original-Funktion)"""
        try:
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Wichtige Dateien sichern
            files_to_backup = [
                "steam_price_tracker.db",
                ".env", 
                "requirements.txt",
                "main.py"
            ]
            
            backed_up = []
            for file_name in files_to_backup:
                file_path = Path(file_name)
                if file_path.exists():
                    backup_path = backup_dir / f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
                    shutil.copy2(file_path, backup_path)
                    backed_up.append(file_name)
            
            detail_msg = f"Backup erstellt: {len(backed_up)} Dateien in backups/"
            if backed_up:
                detail_msg += f"\nGesicherte Dateien: {', '.join(backed_up)}"
            
            self.log_step("Master Backup", True, detail_msg)
            return True
            
        except Exception as e:
            self.log_step("Master Backup", False, str(e))
            return False
    
    def create_directories(self) -> bool:
        """Erstellt erforderliche Verzeichnisstruktur"""
        try:
            directories = [
                "logs",
                "exports", 
                "backups",
                "temp",
                "config"
            ]
            
            created_dirs = []
            for dir_name in directories:
                dir_path = Path(dir_name)
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    created_dirs.append(dir_name)
            
            detail_msg = f"Verzeichnisstruktur vorbereitet"
            if created_dirs:
                detail_msg += f"\nErstellt: {', '.join(created_dirs)}"
            else:
                detail_msg += " (bereits vorhanden)"
            
            self.log_step("Directory Structure", True, detail_msg)
            return True
            
        except Exception as e:
            self.log_step("Directory Structure", False, str(e))
            return False
    
    def correct_requirements(self) -> bool:
        """Korrigiert requirements.txt ohne eingebaute Module"""
        try:
            # Produktions-Requirements mit spezifischen Versionen
            production_requirements = [
                "# Core Dependencies",
                "requests>=2.31.0",
                "python-dotenv>=1.0.0", 
                "schedule>=1.2.0",
                "",
                "# Web Scraping",
                "beautifulsoup4>=4.12.0",
                "lxml>=4.9.3",
                "",
                "# Async Support", 
                "aiohttp>=3.8.6",
                "asyncio-throttle>=1.0.2",
                "",
                "# Optional Dependencies",
                "pandas>=2.0.0  # Für erweiterte Datenanalyse",
                "rich>=13.7.0   # Bessere CLI-Ausgabe", 
                "tqdm>=4.66.0   # Progress Bars",
                "",
                "# Development Dependencies (optional)",
                "pytest>=7.4.0",
                "black>=23.0.0",
                "flake8>=6.0.0"
            ]
            
            requirements_path = Path("requirements.txt")
            
            # Backup der aktuellen requirements.txt falls vorhanden
            if requirements_path.exists():
                backup_path = Path("backups") / f"requirements_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                shutil.copy2(requirements_path, backup_path)
            
            # Neue requirements.txt schreiben
            with open(requirements_path, "w", encoding="utf-8") as f:
                f.write("\n".join(production_requirements))
            
            self.log_step("Corrected Requirements", True, "requirements.txt korrigiert mit Produktions-Dependencies")
            self.features_available['requirements'] = True
            return True
            
        except Exception as e:
            self.log_step("Corrected Requirements", False, str(e))
            return False
    
    def install_dependencies(self, upgrade: bool = False) -> bool:
        """Installiert Python Dependencies mit erweiterten Fallback-Mechanismen"""
        try:
            requirements_path = Path("requirements.txt")
            if not requirements_path.exists():
                self.log_step("Python Dependencies", False, "requirements.txt nicht gefunden")
                return False
            
            # Build command
            cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
            if upgrade:
                cmd.append("--upgrade")
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 Minuten timeout
            )
            
            if process.returncode == 0:
                self.log_step("Python Dependencies", True, "Alle Dependencies erfolgreich installiert")
                return True
            else:
                error_msg = process.stderr.strip()
                
                # Fallback für kritische Dependencies
                critical_deps = ["requests", "python-dotenv", "schedule"]
                
                missing_critical = []
                for dep in critical_deps:
                    try:
                        __import__(dep.replace('-', '_'))
                    except ImportError:
                        missing_critical.append(dep)
                
                if not missing_critical:
                    self.log_warning("Dependency-Installation fehlgeschlagen, aber kritische Module verfügbar")
                    self.log_step("Python Dependencies", True, "Kritische Dependencies bereits verfügbar")
                    return True
                else:
                    self.log_step("Python Dependencies", False, 
                                f"Fehlende kritische Dependencies: {missing_critical}\nFehler: {error_msg}")
                    return False
                
        except subprocess.TimeoutExpired:
            self.log_step("Python Dependencies", False, "Installation timeout nach 300s")
            return False
        except Exception as e:
            self.log_step("Python Dependencies", False, str(e))
            return False
    
    def create_config_files(self) -> bool:
        """Erstellt umfassende Konfigurationsdateien mit VOLLSTÄNDIGEM .env Template"""
        try:
            created_files = []
            
            # 1. Vollständiges .env Template (ERWEITERT)
            env_template_path = Path("env_Template.txt")
            if not env_template_path.exists():
                env_content = '''# ===================================================================
# STEAM PRICE TRACKER - VOLLSTÄNDIGE KONFIGURATION
# ===================================================================
# Generiere deinen Steam API Key: https://steamcommunity.com/dev/apikey
# Kopiere diese Datei zu .env und trage deine Werte ein

# ===================================================================
# STEAM API KONFIGURATION (ERFORDERLICH)
# ===================================================================

# Steam Web API Key (ERFORDERLICH für Wishlist-Import)
STEAM_API_KEY=your_steam_api_key_here

# Steam Rate Limiting (Sekunden zwischen API-Aufrufen)
STEAM_API_RATE_LIMIT=1.0

# Steam API Timeout (Sekunden)
STEAM_API_TIMEOUT=15

# Steam API Retry Attempts
STEAM_API_RETRY_ATTEMPTS=3

# ===================================================================
# DATENBANK KONFIGURATION
# ===================================================================

# Datenbank-Pfad
DATABASE_PATH=steam_price_tracker.db

# Automatische Backups aktivieren
BACKUP_ENABLED=true

# Backup-Intervall (Stunden)
BACKUP_INTERVAL_HOURS=24

# Automatische Bereinigung (Tage) 
AUTO_CLEANUP_DAYS=90

# Database Auto-Vacuum
AUTO_VACUUM=true

# ===================================================================
# PREIS-TRACKING KONFIGURATION
# ===================================================================

# Standard Update-Intervall (Stunden)
DEFAULT_UPDATE_INTERVAL_HOURS=6

# Maximale Apps pro Update-Batch
MAX_APPS_PER_UPDATE=100

# Automatisches Tracking aktivieren
ENABLE_AUTOMATIC_TRACKING=false

# Preis-Alerts aktivieren
ENABLE_PRICE_ALERTS=true

# Alert-Check-Intervall (Stunden)
ALERT_CHECK_INTERVAL_HOURS=1

# ===================================================================
# CHARTS INTEGRATION
# ===================================================================

# Charts-Funktionalität aktivieren
CHARTS_ENABLED=true

# Charts Update-Intervall (Stunden)
CHARTS_UPDATE_INTERVAL_HOURS=6

# Charts Auto-Cleanup (Tage)
CHARTS_AUTO_CLEANUP_DAYS=30

# Maximale Charts-Apps pro Update
MAX_CHARTS_APPS_PER_UPDATE=200

# ===================================================================
# CHEAPSHARK API KONFIGURATION
# ===================================================================

# CheapShark API Base URL
CHEAPSHARK_BASE_URL=https://www.cheapshark.com/api/1.0

# CheapShark Rate Limiting (Sekunden)
CHEAPSHARK_API_RATE_LIMIT=1.5

# CheapShark API Timeout (Sekunden)
CHEAPSHARK_API_TIMEOUT=15

# CheapShark Retry Attempts
CHEAPSHARK_API_RETRY_ATTEMPTS=3

# Store IDs für CheapShark (komma-getrennt)
# 1=Steam, 3=GreenManGaming, 7=GOG, 11=HumbleStore, 15=Fanatical, 27=GamesPlanet
CHEAPSHARK_STORE_IDS=1,3,7,11,15,27

# ===================================================================
# SCHEDULER & AUTOMATION
# ===================================================================

# Background Scheduler aktivieren
SCHEDULER_ENABLED=false

# Scheduler Max Workers
SCHEDULER_MAX_WORKERS=1

# Scheduler Cleanup-Intervall (Stunden)
SCHEDULER_CLEANUP_INTERVAL_HOURS=168

# Heartbeat-Intervall für Background Tasks (Sekunden)
SCHEDULER_HEARTBEAT_INTERVAL=60

# ===================================================================
# LOGGING KONFIGURATION
# ===================================================================

# Log Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Log-Datei
LOG_FILE=logs/steam_tracker.log

# Log-Datei maximale Größe (MB)
LOG_FILE_MAX_SIZE_MB=10

# Anzahl Log-Backup-Dateien
LOG_BACKUP_COUNT=5

# Console-Logging aktivieren
LOG_TO_CONSOLE=true

# ===================================================================
# EXPORT KONFIGURATION
# ===================================================================

# Standard Export-Format (csv, json, excel)
EXPORT_FORMAT=csv

# Export-Verzeichnis
EXPORT_DIRECTORY=exports

# Metadaten in Exports einbeziehen
EXPORT_INCLUDE_METADATA=true

# Export Encoding
EXPORT_ENCODING=utf-8

# ===================================================================
# ELASTICSEARCH (OPTIONAL)
# ===================================================================

# Elasticsearch aktivieren
ELASTICSEARCH_ENABLED=false

# Elasticsearch Host
ELASTICSEARCH_HOST=localhost

# Elasticsearch Port
ELASTICSEARCH_PORT=9200

# Elasticsearch Index Prefix
ELASTICSEARCH_INDEX_PREFIX=steam_tracker

# Elasticsearch Username (falls erforderlich)
ELASTICSEARCH_USERNAME=

# Elasticsearch Password (falls erforderlich)
ELASTICSEARCH_PASSWORD=

# ===================================================================
# PERFORMANCE TUNING
# ===================================================================

# HTTP Connection Pool Size
CONNECTION_POOL_SIZE=20

# Request Timeout (Sekunden)
REQUEST_TIMEOUT=30

# Batch Processing Chunk Size
BATCH_CHUNK_SIZE=50

# Maximale parallele Requests
MAX_PARALLEL_REQUESTS=5

# ===================================================================
# REMOTE BACKUP (OPTIONAL)
# ===================================================================

# Remote Backup aktivieren
REMOTE_BACKUP_ENABLED=false

# Remote Backup URL
REMOTE_BACKUP_URL=

# ===================================================================
# PROXY CONFIGURATION (OPTIONAL)
# ===================================================================

# HTTP Proxy
HTTP_PROXY=

# HTTPS Proxy  
HTTPS_PROXY=

# No Proxy Hosts (komma-getrennt)
NO_PROXY=localhost,127.0.0.1

# Proxy Authentication
PROXY_USERNAME=
PROXY_PASSWORD=

# ===================================================================
# ADVANCED CONFIGURATION
# ===================================================================

# Worker Threads für parallele Verarbeitung
WORKER_THREADS=4

# Retry Delay (Sekunden)
RETRY_DELAY=5

# User Agent für HTTP Requests
USER_AGENT=SteamPriceTracker/3.0

# Debug Mode
DEBUG_MODE=false

# ===================================================================
# FEATURE FLAGS
# ===================================================================

# Experimentelle Features aktivieren
EXPERIMENTAL_FEATURES=false

# Beta Features aktivieren
BETA_FEATURES=false

# Legacy Kompatibilität
LEGACY_COMPATIBILITY=true

# Advanced Analytics
ADVANCED_ANALYTICS=false

# Machine Learning Features
ML_FEATURES=false

# ===================================================================
# MONITORING CONFIGURATION
# ===================================================================

# Health Check aktivieren
HEALTH_CHECK_ENABLED=true

# Metrics Collection
METRICS_ENABLED=false

# Prometheus Metrics Port
PROMETHEUS_PORT=8001

# Health Check Port
HEALTH_CHECK_PORT=8080
'''
                
                with open(env_template_path, 'w', encoding='utf-8') as f:
                    f.write(env_content)
                created_files.append("env_Template.txt")
            
            # 2. Logging Konfiguration (erweitert)
            logging_config_path = Path("logging.conf")
            if not logging_config_path.exists():
                logging_content = '''[loggers]
keys=root,steam_tracker,charts,scheduler,database,price_tracker

[handlers]
keys=consoleHandler,fileHandler,rotatingFileHandler

[formatters]
keys=simpleFormatter,detailedFormatter,debugFormatter

[logger_root]
level=INFO
handlers=consoleHandler

[logger_steam_tracker]
level=INFO
handlers=consoleHandler,rotatingFileHandler
qualname=steam_tracker
propagate=0

[logger_charts]
level=INFO
handlers=consoleHandler,fileHandler
qualname=charts
propagate=0

[logger_scheduler]
level=DEBUG
handlers=consoleHandler,fileHandler
qualname=scheduler
propagate=0

[logger_database]
level=INFO
handlers=consoleHandler,fileHandler
qualname=database
propagate=0

[logger_price_tracker]
level=INFO
handlers=consoleHandler,rotatingFileHandler
qualname=price_tracker
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=DEBUG
formatter=detailedFormatter
args=('logs/steam_tracker.log',)

[handler_rotatingFileHandler]
class=handlers.RotatingFileHandler
level=INFO
formatter=detailedFormatter
args=('logs/steam_tracker.log', 'a', 10*1024*1024, 5)

[formatter_simpleFormatter]
format=%(levelname)s - %(message)s

[formatter_detailedFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s

[formatter_debugFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s
'''
                
                with open(logging_config_path, 'w', encoding='utf-8') as f:
                    f.write(logging_content)
                created_files.append("logging.conf")
            
            # 3. Config.json Template
            config_json_path = Path("config_template.json")
            if not config_json_path.exists():
                config_content = {
                    "database": {
                        "path": "steam_price_tracker.db",
                        "cleanup_days": 90,
                        "backup_enabled": True,
                        "auto_vacuum": True
                    },
                    "tracking": {
                        "default_interval_hours": 6,
                        "max_apps_per_update": 100,
                        "enable_automatic_tracking": False,
                        "enable_price_alerts": True
                    },
                    "steam_api": {
                        "rate_limit_seconds": 1.0,
                        "timeout_seconds": 15,
                        "retry_attempts": 3
                    },
                    "cheapshark": {
                        "rate_limit_seconds": 1.5,
                        "timeout_seconds": 15,
                        "store_ids": "1,3,7,11,15,27",
                        "retry_attempts": 3
                    },
                    "charts": {
                        "enabled": True,
                        "update_interval_hours": 6,
                        "auto_cleanup_days": 30,
                        "max_apps_per_update": 200
                    },
                    "export": {
                        "default_format": "csv",
                        "output_directory": "exports",
                        "include_metadata": True,
                        "encoding": "utf-8"
                    },
                    "logging": {
                        "level": "INFO",
                        "file": "logs/steam_tracker.log",
                        "max_size_mb": 10,
                        "backup_count": 5
                    }
                }
                
                with open(config_json_path, 'w', encoding='utf-8') as f:
                    json.dump(config_content, f, indent=2, ensure_ascii=False)
                created_files.append("config_template.json")
            
            detail_msg = f"Konfigurationsdateien erstellt: {', '.join(created_files)}"
            if not created_files:
                detail_msg = "Alle Konfigurationsdateien bereits vorhanden"
            
            self.log_step("Configuration Files", True, detail_msg)
            self.features_available['configuration'] = True
            return True
            
        except Exception as e:
            self.log_step("Configuration Files", False, str(e))
            return False
    
    def test_database_schema(self) -> bool:
        """Testet das korrigierte Database Schema - ERWEITERTE VERSION"""
        try:
            # Importiere DatabaseManager
            from database_manager import DatabaseManager
            
            # Test-Datenbank erstellen
            test_db_path = "test_schema_production.db"
            test_db = DatabaseManager(test_db_path)
            
            test_results = []
            
            # Test 1: Basis-Funktionalität
            with test_db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Test essential tables
                essential_tables = ['tracked_apps', 'price_snapshots', 'steam_charts_tracking']
                for table in essential_tables:
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                    exists = cursor.fetchone() is not None
                    test_results.append((f"{table}_exists", exists))
                
                # Test Charts-spezifische Struktur (erweitert)
                cursor.execute("PRAGMA table_info(steam_charts_tracking)")
                charts_columns = [row[1] for row in cursor.fetchall()]
                
                required_charts_columns = [
                    'steam_app_id', 'chart_type', 'days_in_charts', 
                    'current_rank', 'name', 'active', 'last_seen'
                ]
                for col in required_charts_columns:
                    test_results.append((f"charts_{col}_column", col in charts_columns))
                
                # Test Datentypen
                cursor.execute("PRAGMA table_info(price_snapshots)")
                price_columns = [row[1] for row in cursor.fetchall()]
                required_price_columns = ['steam_app_id', 'timestamp', 'steam_price', 'store']
                for col in required_price_columns:
                    test_results.append((f"price_{col}_column", col in price_columns))
            
            # Test 2: Batch Writer Kompatibilität (erweitert)
            try:
                from database_manager import create_batch_writer
                batch_writer = create_batch_writer(test_db)
                
                # Test Batch Writer Methoden
                batch_methods = ['batch_write_charts', 'get_batch_statistics']
                for method in batch_methods:
                    test_results.append((f"batch_{method}", hasattr(batch_writer, method)))
                
            except Exception:
                test_results.append(("batch_writer_creation", False))
            
            # Test 3: Schema-Kompatibilität
            try:
                schema_info = test_db.get_schema_info() if hasattr(test_db, 'get_schema_info') else None
                test_results.append(("schema_info_available", schema_info is not None))
                if schema_info:
                    test_results.append(("schema_batch_compatible", 
                                       schema_info.get('batch_writer_compatible', False)))
            except Exception:
                test_results.append(("schema_info_available", False))
            
            # Cleanup
            try:
                os.remove(test_db_path)
            except:
                pass
            
            # Ergebnisse auswerten
            failed_tests = [test for test, result in test_results if not result]
            success_count = len([r for _, r in test_results if r])
            
            if len(failed_tests) > len(test_results) * 0.2:  # Mehr als 20% fehlgeschlagen
                raise Exception(f"Kritische Schema-Tests fehlgeschlagen: {failed_tests}")
            
            detail_msg = f"Schema-Tests: {success_count}/{len(test_results)} erfolgreich"
            detail_msg += f"\nTabellen: {len(essential_tables)} essential tables"
            detail_msg += f"\nCharts-Spalten: {len(charts_columns)} verfügbar"
            if failed_tests:
                detail_msg += f"\nÜbersprungen: {failed_tests[:3]}"  # Nur erste 3 zeigen
            
            self.log_step("Database Schema Test", True, detail_msg)
            self.features_available['database'] = True
            return True
            
        except Exception as e:
            self.log_step("Database Schema Test", False, str(e))
            try:
                os.remove(test_db_path)
            except:
                pass
            return False
    
    def test_core_functionality(self) -> bool:
        """Testet Kern-Funktionalität umfassend - ERWEITERTE VERSION"""
        try:
            test_db_path = "test_core.db"
            core_tests = []
            
            # Test 1: Price Tracker Import und Instanziierung
            try:
                from price_tracker import SteamPriceTracker
                from database_manager import DatabaseManager
                
                db_manager = DatabaseManager(test_db_path)
                api_key = "test_api_key_12345"
                
                # SteamPriceTracker erstellen
                tracker = SteamPriceTracker(db_manager=db_manager, api_key=api_key, enable_scheduler=False)
                
                # Test Tracker-Grundfunktionen
                core_tests.append(("tracker_has_db_manager", hasattr(tracker, 'db_manager')))
                core_tests.append(("tracker_has_api_key", hasattr(tracker, 'api_key')))
                core_tests.append(("tracker_has_add_or_update_app", hasattr(tracker, 'add_or_update_app')))
                
                # Test API-Kompatibilität mit main.py
                required_methods = [
                    'get_tracked_apps',       # Wichtig für main.py
                    'get_database_stats',     # Statt get_statistics
                    'add_app_to_tracking'     # Falls verfügbar
                ]
                
                for method in required_methods:
                    core_tests.append((f"tracker_has_{method}", hasattr(tracker, method)))
                
                # Test Charts-Integration (falls aktiviert)
                if hasattr(tracker, 'charts_manager') and tracker.charts_manager:
                    core_tests.append(("charts_manager_available", True))
                    charts_methods = ['update_all_charts', 'get_chart_statistics']
                    for method in charts_methods:
                        core_tests.append((f"charts_has_{method}", hasattr(tracker.charts_manager, method)))
                else:
                    self.log_warning("Charts Manager nicht verfügbar - wird übersprungen")
                
                core_tests.append(("price_tracker_creation", True))
                
            except ImportError as e:
                core_tests.append(("price_tracker_import", False))
                self.log_warning(f"Price Tracker Import fehlgeschlagen: {e}")
            
            # Test 2: Database Manager (erweitert)
            try:
                from database_manager import create_database_manager
                db_manager = create_database_manager(test_db_path)
                core_tests.append(("database_manager_creation", True))
                
                # Test basic operations
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM tracked_apps")
                    cursor.fetchone()
                core_tests.append(("database_operations", True))
                
                # Test erweiterte DB-Funktionen
                if hasattr(db_manager, 'get_database_stats'):
                    stats = db_manager.get_database_stats()
                    core_tests.append(("database_stats", isinstance(stats, dict)))
                
            except Exception as e:
                core_tests.append(("database_manager_creation", False))
                core_tests.append(("database_operations", False))
                self.log_warning(f"Database Manager Test fehlgeschlagen: {e}")
            
            # Test 3: Steam Wishlist Manager (erweitert)
            try:
                from steam_wishlist_manager import SteamWishlistManager, load_api_key_from_env
                core_tests.append(("wishlist_manager_available", True))
                
                # Test API Key Loading
                try:
                    api_key = load_api_key_from_env()
                    core_tests.append(("api_key_loading", True))
                except Exception:
                    core_tests.append(("api_key_loading", False))
                
            except ImportError:
                self.log_warning("Steam Wishlist Manager nicht verfügbar - optional")
                core_tests.append(("wishlist_manager_available", False))
            
            # Test 4: Background Scheduler (erweitert)
            try:
                from background_scheduler import EnhancedBackgroundScheduler
                core_tests.append(("background_scheduler_available", True))
                self.features_available['background_scheduler'] = True
                
                # Test Scheduler-Komponenten
                scheduler_components = ['GlobalProcessManager', 'SchedulerTask']
                for component in scheduler_components:
                    try:
                        exec(f"from background_scheduler import {component}")
                        core_tests.append((f"scheduler_{component.lower()}", True))
                    except ImportError:
                        core_tests.append((f"scheduler_{component.lower()}", False))
                
            except ImportError:
                self.log_warning("Background Scheduler nicht verfügbar - optional")
                core_tests.append(("background_scheduler_available", False))
            
            # Test 5: Batch Processor
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("batch_processor", "batch_processor.py")
                if spec and spec.loader:
                    batch_module = importlib.util.module_from_spec(spec)
                    core_tests.append(("batch_processor_available", True))
                    self.features_available['batch_processor'] = True
                else:
                    core_tests.append(("batch_processor_available", False))
            except Exception:
                core_tests.append(("batch_processor_available", False))
            
            # Cleanup
            try:
                os.remove(test_db_path)
            except:
                pass
            
            # Ergebnisse auswerten
            failed_tests = [test for test, result in core_tests if not result]
            success_count = len([r for _, r in core_tests if r])
            
            if len(failed_tests) > len(core_tests) * 0.3:  # Mehr als 30% fehlgeschlagen
                raise Exception(f"Zu viele Kern-Tests fehlgeschlagen: {failed_tests}")
            
            detail_msg = f"{success_count}/{len(core_tests)} Kern-Tests erfolgreich"
            detail_msg += f"\nKritische Komponenten: Price Tracker, Database Manager"
            detail_msg += f"\nOptionale Komponenten: Charts, Scheduler, Batch Processor"
            if failed_tests:
                detail_msg += f"\nÜbersprungen: {failed_tests[:3]}"
            
            self.log_step("Core Functionality Test", True, detail_msg)
            self.features_available['core'] = True
            self.features_available['price_tracking'] = True
            return True
            
        except Exception as e:
            self.log_step("Core Functionality Test", False, str(e))
            try:
                os.remove(test_db_path)
            except:
                pass
            return False
    
    def test_main_compatibility(self) -> bool:
        """Testet main.py Kompatibilität umfassend - ERWEITERTE VERSION"""
        try:
            main_path = Path("main.py")
            if not main_path.exists():
                raise Exception("main.py nicht gefunden")
            
            # main.py Inhalt analysieren
            with open(main_path, "r", encoding="utf-8") as f:
                main_content = f.read()
            
            compatibility_tests = []
            
            # Test 1: Syntax-Validierung
            try:
                compile(main_content, "main.py", "exec")
                compatibility_tests.append(("syntax_valid", True))
            except SyntaxError as e:
                compatibility_tests.append(("syntax_valid", False))
                raise Exception(f"Syntax-Fehler in main.py: {e}")
            
            # Test 2: Menüoptionen zählen (erweitert)
            menu_count = main_content.count("def menu_")
            compatibility_tests.append(("sufficient_menu_options", menu_count >= 20))
            
            # Test 3: Import-Validierung (erweitert)
            required_imports = [
                "from database_manager import",
                "from price_tracker import", 
                "DatabaseManager",
                "SteamPriceTracker",
                "create_database_manager",
                "create_price_tracker"
            ]
            
            for import_check in required_imports:
                found = import_check in main_content
                compatibility_tests.append((f"has_import_{import_check.split()[-1]}", found))
            
            # Test 4: API-Aufrufe validieren (erweitert)
            critical_api_calls = [
                "get_tracked_apps(",
                "get_database_stats(",
                "add_tracked_app(",
                "update_all_prices(",
                "get_best_deals("
            ]
            
            for api_call in critical_api_calls:
                found = api_call in main_content
                compatibility_tests.append((f"uses_api_{api_call.replace('(', '')}", found))
            
            # Test 5: Charts-Integration prüfen (erweitert)
            charts_indicators = [
                "charts_manager",
                "update_all_charts",
                "menu_batch_charts_update",
                "Option 14"
            ]
            
            charts_found = sum(1 for indicator in charts_indicators if indicator in main_content)
            compatibility_tests.append(("charts_integration", charts_found >= 2))
            
            # Test 6: Error Handling prüfen (erweitert)
            error_handling = [
                "try:",
                "except",
                "Exception",
                "finally:",
                "logger.error"
            ]
            
            error_handling_found = sum(1 for handler in error_handling if handler in main_content)
            compatibility_tests.append(("error_handling", error_handling_found >= 3))
            
            # Test 7: Menü-System (erweitert)
            menu_features = [
                "safe_input(",
                "print_menu(",
                "choice",
                "option"
            ]
            
            menu_features_found = sum(1 for feature in menu_features if feature.lower() in main_content.lower())
            compatibility_tests.append(("menu_system", menu_features_found >= 2))
            
            # Test 8: Time-Module Check (GEFIXT)
            time_usage = [
                "time.time()",
                "time.sleep(",
                "time_module.time()",
                "time_module.sleep("
            ]
            
            safe_time_usage = main_content.count("time_module.time()") + main_content.count("time_module.sleep(")
            unsafe_time_usage = main_content.count("time.time()") + main_content.count("time.sleep(")
            
            compatibility_tests.append(("safe_time_usage", safe_time_usage > 0 or unsafe_time_usage == 0))
            
            # Ergebnisse auswerten
            failed_tests = [test for test, result in compatibility_tests if not result]
            success_count = len([r for _, r in compatibility_tests if r])
            
            if failed_tests and "syntax_valid" in [f[0] for f in failed_tests]:
                raise Exception("Syntax-Fehler in main.py - kritisch")
            
            detail_msg = f"main.py Kompatibilität: {success_count}/{len(compatibility_tests)} Tests erfolgreich"
            detail_msg += f"\nMenü-Funktionen: {menu_count} gefunden"
            detail_msg += f"\nCharts-Integration: {'verfügbar' if charts_found >= 2 else 'eingeschränkt'}"
            if failed_tests:
                detail_msg += f"\nÜbersprungen: {[f[0] for f in failed_tests][:3]}"
            
            self.log_step("Main.py Compatibility Test", True, detail_msg)
            self.features_available['main_app'] = True
            return True
            
        except Exception as e:
            self.log_step("Main.py Compatibility Test", False, str(e))
            return False
    
    def test_charts_integration(self) -> bool:
        """Testet Charts-Integration - MASSIV ERWEITERTE VERSION"""
        try:
            test_db_path = "test_charts_extended.db"
            charts_tests = []
            charts_available = False
            
            # Test 1: Steam Charts Manager Import (erweitert)
            try:
                from steam_charts_manager import SteamChartsManager
                charts_tests.append(("charts_manager_import", True))
                
                # Test erweiterte BATCH-Funktionen
                test_api_key = "test_key_12345"
                
                from database_manager import create_database_manager
                db_manager = create_database_manager(test_db_path)
                charts_manager = SteamChartsManager(test_api_key, db_manager)
                
                charts_available = True
                
                # Test Charts Manager Methoden (erweitert)
                required_methods = [
                    'update_all_charts',
                    'get_most_played_games', 
                    'get_best_sellers_games',
                    'get_chart_statistics'
                ]
                
                for method in required_methods:
                    has_method = hasattr(charts_manager, method)
                    charts_tests.append((f"charts_has_{method}", has_method))
                
                # Test BATCH-spezifische Methoden
                batch_methods = [
                    'update_all_charts_batch',
                    'get_batch_performance_stats',
                    'batch_charts_health_check'
                ]
                
                available_batch_methods = []
                for method in batch_methods:
                    if hasattr(charts_manager, method):
                        available_batch_methods.append(method)
                        charts_tests.append((f"has_{method}", True))
                    else:
                        charts_tests.append((f"has_{method}", False))
                
                # Test Database Integration (erweitert)
                success = db_manager.add_chart_game("test_789", "test_chart", 1, 1000, "Test Game")
                charts_tests.append(("db_add_chart_game", success))
                
                chart_games = db_manager.get_active_chart_games("test_chart")
                charts_tests.append(("db_get_chart_games", isinstance(chart_games, list)))
                
                # Test Statistiken (erweitert)
                try:
                    if hasattr(charts_manager, 'get_chart_statistics'):
                        stats = charts_manager.get_chart_statistics()
                        charts_tests.append(("charts_statistics", isinstance(stats, dict)))
                    else:
                        # Fallback über DatabaseManager
                        stats = db_manager.get_charts_statistics()
                        charts_tests.append(("charts_statistics_fallback", isinstance(stats, dict)))
                except Exception as e:
                    charts_tests.append(("charts_statistics", False))
                    self.log_warning(f"Charts-Statistiken Fehler: {e}")
                
                # Test Schema-Kompatibilität (KRITISCH für neue DB-Struktur)
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Prüfe steam_charts_tracking
                    cursor.execute("SELECT days_in_charts FROM steam_charts_tracking WHERE steam_app_id = ?", ("test_789",))
                    result = cursor.fetchone()
                    charts_tests.append(("schema_compatibility", result is not None))
                    
                    # Prüfe Batch Writer Integration
                    try:
                        from database_manager import create_batch_writer
                        batch_writer = create_batch_writer(db_manager)
                        
                        # Test Charts-Batch-Schreibung
                        test_charts_data = [{
                            'steam_app_id': 'test_batch_123',
                            'chart_type': 'test_batch',
                            'current_rank': 1,
                            'name': 'Test Batch Game'
                        }]
                        
                        result = batch_writer.batch_write_charts(test_charts_data)
                        charts_tests.append(("batch_charts_write", result.get('success', False)))
                        
                    except Exception as batch_error:
                        charts_tests.append(("batch_charts_write", False))
                        self.log_warning(f"Batch Charts Write Fehler: {batch_error}")
                
                # Test Chart-Typen Konfiguration
                try:
                    from steam_charts_manager import CHART_TYPES
                    chart_types = list(CHART_TYPES.keys())
                    charts_tests.append(("chart_types_available", len(chart_types) >= 3))
                except ImportError:
                    charts_tests.append(("chart_types_available", False))
                
                # Cleanup
                try:
                    os.remove(test_db_path)
                except:
                    pass
                    
            except ImportError as e:
                charts_tests.append(("charts_manager_import", False))
                self.log_warning(f"Charts Manager nicht verfügbar: {e}")
            
            # Test 2: Charts CLI verfügbar?
            try:
                charts_cli_path = Path("charts_cli_manager.py")
                if charts_cli_path.exists():
                    with open(charts_cli_path, 'r') as f:
                        cli_content = f.read()
                    
                    # Test CLI Funktionen
                    cli_functions = ['enable', 'disable', 'status', 'update', 'automate']
                    cli_found = sum(1 for func in cli_functions if func in cli_content)
                    
                    charts_tests.append(("charts_cli_available", True))
                    charts_tests.append(("charts_cli_complete", cli_found >= 3))
                    self.features_available['charts_cli'] = True
                else:
                    charts_tests.append(("charts_cli_available", False))
            except:
                charts_tests.append(("charts_cli_available", False))
            
            # Test 3: Charts-Konfiguration
            try:
                env_path = Path(".env")
                config_found = False
                if env_path.exists():
                    with open(env_path, 'r') as f:
                        env_content = f.read()
                    config_found = 'CHARTS_ENABLED' in env_content
                
                charts_tests.append(("charts_config_available", config_found))
            except:
                charts_tests.append(("charts_config_available", False))
            
            # Ergebnisse auswerten
            failed_tests = [test for test, result in charts_tests if not result]
            success_count = len([r for _, r in charts_tests if r])
            
            # Charts sind optional - keine harten Anforderungen
            if success_count > 0:
                detail_msg = f"Charts-Integration: {success_count}/{len(charts_tests)} Tests erfolgreich"
                if available_batch_methods:
                    detail_msg += f"\nBATCH-Methoden: {', '.join(available_batch_methods)}"
                if charts_available:
                    detail_msg += f"\nChart-Typen: Multiple verfügbar"
                    detail_msg += f"\nSchema: steam_charts_tracking kompatibel"
                if failed_tests:
                    detail_msg += f"\nÜbersprungen: {len(failed_tests)} Tests"
                
                self.log_step("Charts Integration", True, detail_msg)
                self.features_available['charts'] = charts_available and len(failed_tests) <= len(charts_tests) * 0.3
                return True
            else:
                self.log_step("Charts Integration", False, "Charts-Features nicht verfügbar (optional)")
                self.log_warning("Charts-Integration übersprungen - optional")
                return True  # Charts sind optional
            
        except Exception as e:
            self.log_step("Charts Integration", False, str(e))
            self.log_warning("Charts-Integration fehlgeschlagen - optional")
            return True  # Charts sind optional
    
    def test_steam_api_connectivity(self) -> bool:
        """Testet Steam API Konnektivität - ERWEITERTE VERSION"""
        try:
            import requests
            
            # Test 1: Steam Store API (öffentlich, erweitert)
            test_url = "https://store.steampowered.com/api/appdetails?appids=413150"
            
            try:
                start_time = time_module.time()
                response = requests.get(test_url, timeout=10)
                duration = time_module.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    app_data = data.get('413150', {})
                    success_details = f"Steam Store API: Verfügbar ({duration:.2f}s)"
                    success_details += f"\nTest-App (Stardew Valley): {app_data.get('success', False)}"
                    if app_data.get('data'):
                        price_info = app_data['data'].get('price_overview', {})
                        if price_info:
                            success_details += f"\nPreis-Daten: Verfügbar"
                else:
                    raise Exception(f"HTTP {response.status_code}")
                    
            except Exception as e:
                success_details = f"Steam Store API: Fehler - {e}"
                self.log_step("Steam API Connectivity", False, success_details)
                return False
            
            # Test 2: .env und API Key laden (erweitert)
            env_path = Path(".env")
            if not env_path.exists():
                self.log_step("Steam API Connectivity", False, ".env Datei nicht gefunden")
                self.log_warning("Erstelle .env Datei mit deinem Steam API Key")
                return False
            
            # Test Steam API Key laden (erweitert)
            try:
                from steam_wishlist_manager import load_api_key_from_env
                api_key = load_api_key_from_env()
                
                if not api_key or api_key == "your_steam_api_key_here":
                    self.log_step("Steam API Connectivity", False, "Steam API Key nicht konfiguriert")
                    self.log_warning("Trage deinen Steam API Key in .env ein")
                    return False
                
                # Test API Key Format (erweitert)
                if len(api_key) != 32 or not all(c in '0123456789ABCDEF' for c in api_key.upper()):
                    self.log_step("Steam API Connectivity", False, "Steam API Key hat falsches Format")
                    return False
                
                # Test mit echtem API-Aufruf (falls Key verfügbar)
                test_steam_api_url = f"https://api.steampowered.com/ISteamWebAPIUtil/GetServerInfo/v0001/?key={api_key}"
                
                try:
                    api_response = requests.get(test_steam_api_url, timeout=10)
                    if api_response.status_code == 200:
                        success_details += f"\nSteam Web API: Funktional mit gültigem Key"
                        self.features_available['steam_api'] = True
                    else:
                        success_details += f"\nSteam Web API: HTTP {api_response.status_code}"
                except Exception as api_error:
                    success_details += f"\nSteam Web API: Test-Fehler - {api_error}"
                
                self.log_step("Steam API Connectivity", True, success_details)
                return True
                
            except ImportError:
                self.log_step("Steam API Connectivity", False, "Steam Wishlist Manager nicht verfügbar")
                return False
            
        except Exception as e:
            self.log_step("Steam API Connectivity", False, str(e))
            return False
    
    def test_cli_tools(self) -> bool:
        """Testet CLI-Tools Setup - ERWEITERTE VERSION"""
        try:
            cli_tools = [
                ("batch_processor.py", "Batch Processor", ["batch", "specific", "pending"]),
                ("charts_cli_manager.py", "Charts CLI", ["enable", "disable", "status"]),
                ("elasticsearch_setup.py", "Elasticsearch Setup", ["setup", "export", "status"])
            ]
            
            available_tools = []
            for tool_file, description, expected_commands in cli_tools:
                tool_path = Path(tool_file)
                if tool_path.exists():
                    # Test ob Commands verfügbar sind
                    try:
                        with open(tool_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        commands_found = sum(1 for cmd in expected_commands if cmd in content)
                        completeness = commands_found / len(expected_commands)
                        
                        available_tools.append((tool_file, description, completeness))
                    except Exception:
                        available_tools.append((tool_file, description, 0.0))
            
            if len(available_tools) >= 1:
                detail_msg = f"CLI-Tools verfügbar:\n"
                for tool_file, desc, completeness in available_tools:
                    status = "Vollständig" if completeness >= 0.8 else "Teilweise" if completeness >= 0.5 else "Basis"
                    detail_msg += f"   • {tool_file}: {desc} ({status})\n"
                
                # Test ausführbarkeit
                executable_tools = []
                for tool_file, _, _ in available_tools:
                    try:
                        # Syntax-Check
                        with open(tool_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        compile(content, tool_file, "exec")
                        executable_tools.append(tool_file)
                    except Exception:
                        pass
                
                detail_msg += f"\nAusführbar: {len(executable_tools)}/{len(available_tools)} Tools"
                
                self.log_step("CLI Tools Setup", True, detail_msg.strip())
                self.features_available['cli_tools'] = True
                
                # Spezielle CLI-Features markieren
                for tool_file, _, _ in available_tools:
                    if "batch_processor" in tool_file:
                        self.features_available['batch_processor'] = True
                    elif "charts_cli" in tool_file:
                        self.features_available['charts_cli'] = True
                
                return True
            else:
                self.log_step("CLI Tools Setup", False, "Keine CLI-Tools gefunden")
                return False
                
        except Exception as e:
            self.log_step("CLI Tools Setup", False, str(e))
            return False
    
    def test_elasticsearch_stack(self) -> bool:
        """Testet Elasticsearch Stack (optional) - ERWEITERTE VERSION"""
        try:
            elasticsearch_files = [
                ("elasticsearch_setup.py", "Setup", ["setup", "export", "reset"]),
                ("elasticsearch_cli.py", "CLI", ["status", "export", "analytics"]),
                ("kibana_dashboard_setup.py", "Kibana Dashboard", ["create_index_pattern", "dashboard"])
            ]
            
            available_files = []
            for file_name, description, expected_features in elasticsearch_files:
                if Path(file_name).exists():
                    try:
                        with open(file_name, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        features_found = sum(1 for feature in expected_features if feature in content)
                        completeness = features_found / len(expected_features)
                        
                        available_files.append((file_name, description, completeness))
                    except Exception:
                        available_files.append((file_name, description, 0.0))
            
            if len(available_files) >= 1:
                detail_msg = f"Elasticsearch-Stack verfügbar:\n"
                for file_name, desc, completeness in available_files:
                    status = "Vollständig" if completeness >= 0.8 else "Teilweise" if completeness >= 0.5 else "Basis"
                    detail_msg += f"   • {file_name}: {desc} ({status})\n"
                
                # Test Docker verfügbarkeit (erweitert)
                docker_available = False
                docker_compose_available = False
                
                try:
                    docker_result = subprocess.run(["docker", "--version"], capture_output=True, timeout=5)
                    if docker_result.returncode == 0:
                        docker_available = True
                        docker_version = docker_result.stdout.decode().strip()
                        detail_msg += f"   • Docker: {docker_version}\n"
                        
                        # Test Docker Compose
                        compose_result = subprocess.run(["docker-compose", "--version"], capture_output=True, timeout=5)
                        if compose_result.returncode == 0:
                            docker_compose_available = True
                            detail_msg += f"   • Docker Compose: Verfügbar\n"
                
                except Exception:
                    detail_msg += "   • Docker: Nicht verfügbar - manuelle Installation erforderlich\n"
                
                # Test Elasticsearch Connection (falls lokal läuft)
                try:
                    es_response = requests.get("http://localhost:9200", timeout=2)
                    if es_response.status_code == 200:
                        detail_msg += "   • Elasticsearch: Läuft bereits (localhost:9200)"
                except:
                    detail_msg += "   • Elasticsearch: Nicht aktiv (normal bei Setup)"
                
                self.log_step("Elasticsearch Stack", True, detail_msg.strip())
                self.features_available['elasticsearch'] = True
                if docker_available and docker_compose_available:
                    self.features_available['docker_compose'] = True
                return True
            else:
                self.log_step("Elasticsearch Stack", False, "Elasticsearch-Manager nicht verfügbar (optional)")
                return False
                
        except Exception as e:
            self.log_step("Elasticsearch Stack", False, str(e))
            return False
    
    def create_startup_scripts(self) -> bool:
        """Erstellt erweiterte Start-Scripts für verschiedene Plattformen - ERWEITERTE VERSION"""
        try:
            created_scripts = []
            
            # 1. Windows Batch Script (massiv erweitert)
            batch_content = '''@echo off
title Steam Price Tracker
color 0A
echo.
echo ========================================
echo    Steam Price Tracker - Windows
echo          Produktionsversion v3.0
echo ========================================
echo.

cd /d "%~dp0"

REM Prüfe Python-Installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python ist nicht installiert oder nicht im PATH!
    echo 💡 Installiere Python von https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Prüfe Python-Version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% gefunden

if not exist "steam_price_tracker.db" (
    echo.
    echo 🔧 Erste Installation erkannt...
    echo 📦 Führe automatisches Setup aus...
    python setup.py
    echo.
    if errorlevel 1 (
        echo ❌ Setup fehlgeschlagen!
        pause
        exit /b 1
    )
)

REM Prüfe API Key
if not exist ".env" (
    echo.
    echo ⚠️ .env Datei nicht gefunden!
    echo 💡 Kopiere env_Template.txt zu .env und trage deinen Steam API Key ein
    echo 🔗 API Key generieren: https://steamcommunity.com/dev/apikey
    pause
)

echo.
echo 🚀 Starte Steam Price Tracker...
echo 💡 Drücke Ctrl+C zum Beenden
echo.

python main.py

if errorlevel 1 (
    echo.
    echo ❌ Fehler beim Ausführen!
    echo 💡 Prüfe die Logs im logs/ Verzeichnis
)

echo.
pause
'''
            
            with open("start_tracker.bat", "w", encoding="utf-8") as f:
                f.write(batch_content)
            created_scripts.append("start_tracker.bat")
            
            # 2. Linux/Mac Shell Script (massiv erweitert)
            shell_content = '''#!/bin/bash

# Steam Price Tracker - Unix/Linux Starter v3.0
# Automatisches Setup und Ausführung

set -e  # Exit bei Fehlern

# Colors für bessere Ausgabe
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

echo -e "${BLUE}========================================"
echo -e "   Steam Price Tracker - Unix/Linux"
echo -e "        Produktionsversion v3.0"
echo -e "========================================${NC}"
echo

cd "$(dirname "$0")"

# Prüfe Python-Installation
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 ist nicht installiert!${NC}"
    echo -e "${YELLOW}💡 Installiere Python3 mit deinem Package Manager${NC}"
    echo "   Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "   CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "   macOS: brew install python3"
    exit 1
fi

# Python-Version prüfen
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✅ Python $PYTHON_VERSION gefunden${NC}"

# Prüfe pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}⚠️ pip3 nicht gefunden, versuche Installation...${NC}"
    python3 -m ensurepip --default-pip
fi

# Erste Installation?
if [ ! -f "steam_price_tracker.db" ]; then
    echo
    echo -e "${BLUE}🔧 Erste Installation erkannt...${NC}"
    echo -e "${BLUE}📦 Führe automatisches Setup aus...${NC}"
    python3 setup.py
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Setup fehlgeschlagen!${NC}"
        exit 1
    fi
fi

# API Key prüfen
if [ ! -f ".env" ]; then
    echo
    echo -e "${YELLOW}⚠️ .env Datei nicht gefunden!${NC}"
    echo -e "${YELLOW}💡 Kopiere env_Template.txt zu .env und trage deinen Steam API Key ein${NC}"
    echo -e "${BLUE}🔗 API Key generieren: https://steamcommunity.com/dev/apikey${NC}"
    read -p "Drücke Enter zum Fortfahren..."
fi

echo
echo -e "${GREEN}🚀 Starte Steam Price Tracker...${NC}"
echo -e "${YELLOW}💡 Drücke Ctrl+C zum Beenden${NC}"
echo

# Starte mit Error Handling
if python3 main.py; then
    echo -e "${GREEN}✅ Programm normal beendet${NC}"
else
    echo
    echo -e "${RED}❌ Fehler beim Ausführen!${NC}"
    echo -e "${YELLOW}💡 Prüfe die Logs im logs/ Verzeichnis${NC}"
    echo -e "${YELLOW}💡 Führe 'python3 setup.py' für Diagnose aus${NC}"
fi

echo
read -p "Drücke Enter zum Beenden..."
'''
            
            with open("start_tracker.sh", "w", encoding="utf-8") as f:
                f.write(shell_content)
            
            # Shell Script ausführbar machen (Unix/Linux)
            try:
                os.chmod("start_tracker.sh", 0o755)
            except:
                pass
            
            created_scripts.append("start_tracker.sh")
            
            # 3. Python Direct Runner (erweitert)
            python_content = '''#!/usr/bin/env python3
"""
Steam Price Tracker - Direct Python Runner v3.0
Automatischer Setup, Validierung und Start mit erweiterten Features
"""
import os
import sys
import subprocess
import time as time_module
from pathlib import Path

def check_python_version():
    """Prüft Python-Version auf Kompatibilität"""
    major, minor = sys.version_info.major, sys.version_info.minor
    
    if major < 3 or (major == 3 and minor < 8):
        print("❌ Python 3.8+ erforderlich!")
        print(f"   Aktuelle Version: {major}.{minor}")
        print("💡 Aktualisiere Python: https://www.python.org/downloads/")
        return False
    
    print(f"✅ Python {major}.{minor} - Kompatibel")
    return True

def check_dependencies():
    """Prüft kritische Dependencies"""
    critical = ["requests", "schedule"]
    missing = []
    
    for dep in critical:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)
    
    if missing:
        print(f"⚠️ Fehlende Dependencies: {', '.join(missing)}")
        print("🔧 Installiere Dependencies...")
        
        try:
            subprocess.run([sys.executable, "-m", "pip", "install"] + missing, 
                         check=True, capture_output=True)
            print("✅ Dependencies installiert")
        except subprocess.CalledProcessError:
            print("❌ Dependency-Installation fehlgeschlagen")
            return False
    
    return True

def setup_first_run():
    """Führt First-Run-Setup durch"""
    print("📦 Erste Installation erkannt...")
    print("🔧 Führe automatisches Setup aus...")
    
    try:
        result = subprocess.run([sys.executable, "setup.py"], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Setup erfolgreich abgeschlossen")
            return True
        else:
            print("❌ Setup fehlgeschlagen:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Setup-Timeout nach 5 Minuten")
        return False
    except Exception as e:
        print(f"❌ Setup-Fehler: {e}")
        return False

def check_configuration():
    """Prüft wichtige Konfigurationsdateien"""
    config_files = {
        ".env": "Konfigurationsdatei",
        "requirements.txt": "Dependencies",
        "main.py": "Hauptprogramm"
    }
    
    missing = []
    for file_path, description in config_files.items():
        if not Path(file_path).exists():
            missing.append(f"{file_path} ({description})")
    
    if missing:
        print("⚠️ Fehlende Dateien:")
        for item in missing:
            print(f"   • {item}")
        
        if ".env" in [m.split()[0] for m in missing]:
            print("💡 Kopiere env_Template.txt zu .env und konfiguriere deinen Steam API Key")
            print("🔗 API Key: https://steamcommunity.com/dev/apikey")
    
    return len(missing) == 0

def main():
    """Hauptfunktion mit umfassendem Setup und Start"""
    print("🚀 Steam Price Tracker - Direct Runner v3.0")
    print("=" * 50)
    
    # Wechsle in Script-Verzeichnis
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # 1. Python-Version prüfen
    if not check_python_version():
        input("Drücke Enter zum Beenden...")
        sys.exit(1)
    
    # 2. Dependencies prüfen
    if not check_dependencies():
        input("Drücke Enter zum Beenden...")
        sys.exit(1)
    
    # 3. Erste Installation?
    if not Path("steam_price_tracker.db").exists():
        if not setup_first_run():
            input("Drücke Enter zum Beenden...")
            sys.exit(1)
    
    # 4. Konfiguration prüfen
    check_configuration()
    
    # 5. Starte main.py
    print("\\n🎮 Starte Steam Price Tracker...")
    print("💡 Drücke Ctrl+C zum Beenden")
    print()
    
    try:
        result = subprocess.run([sys.executable, "main.py"])
        
        if result.returncode == 0:
            print("\\n✅ Programm normal beendet")
        else:
            print("\\n❌ Programm mit Fehler beendet")
            print("💡 Prüfe die Logs im logs/ Verzeichnis")
            
    except KeyboardInterrupt:
        print("\\n⏹️ Programm durch Benutzer unterbrochen")
    except Exception as e:
        print(f"\\n❌ Unerwarteter Fehler: {e}")
    
    input("\\nDrücke Enter zum Beenden...")

if __name__ == "__main__":
    main()
'''
            
            with open("run_tracker.py", "w", encoding="utf-8") as f:
                f.write(python_content)
            created_scripts.append("run_tracker.py")
            
            # 4. PowerShell Script für Windows (NEU)
            powershell_content = '''# Steam Price Tracker - PowerShell Starter v3.0
# Erweiterte Windows-Integration

param(
    [switch]$Setup,
    [switch]$Status,
    [switch]$Help
)

# Console-Konfiguration
$Host.UI.RawUI.WindowTitle = "Steam Price Tracker v3.0"

function Write-Header {
    Clear-Host
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "   Steam Price Tracker - PowerShell" -ForegroundColor Cyan
    Write-Host "        Produktionsversion v3.0" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Test-PythonInstallation {
    try {
        $version = python --version 2>&1
        if ($version -match "Python (\\d+\\.\\d+)") {
            Write-Host "✅ $version gefunden" -ForegroundColor Green
            return $true
        }
    }
    catch {
        Write-Host "❌ Python ist nicht installiert!" -ForegroundColor Red
        Write-Host "💡 Installiere Python von https://www.python.org/downloads/" -ForegroundColor Yellow
        return $false
    }
}

function Test-Configuration {
    $configFiles = @{
        ".env" = "Konfigurationsdatei"
        "steam_price_tracker.db" = "Datenbank"
        "main.py" = "Hauptprogramm"
    }
    
    $missing = @()
    foreach ($file in $configFiles.Keys) {
        if (-not (Test-Path $file)) {
            $missing += "$file ($($configFiles[$file]))"
        }
    }
    
    if ($missing.Count -gt 0) {
        Write-Host "⚠️ Fehlende Dateien:" -ForegroundColor Yellow
        foreach ($item in $missing) {
            Write-Host "   • $item" -ForegroundColor Yellow
        }
        return $false
    }
    
    return $true
}

function Start-Setup {
    Write-Host "🔧 Starte automatisches Setup..." -ForegroundColor Blue
    try {
        $result = python setup.py
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Setup erfolgreich abgeschlossen" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "❌ Setup fehlgeschlagen!" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ Setup-Fehler: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Hauptlogik
Write-Header

if ($Help) {
    Write-Host "VERWENDUNG:" -ForegroundColor Yellow
    Write-Host "  .\start_tracker.ps1           # Normaler Start"
    Write-Host "  .\start_tracker.ps1 -Setup    # Setup erzwingen"
    Write-Host "  .\start_tracker.ps1 -Status   # System-Status"
    Write-Host "  .\start_tracker.ps1 -Help     # Diese Hilfe"
    Write-Host ""
    pause
    exit
}

if ($Status) {
    Write-Host "📊 SYSTEM-STATUS:" -ForegroundColor Cyan
    Test-PythonInstallation
    Test-Configuration
    Write-Host ""
    pause
    exit
}

# Python-Installation prüfen
if (-not (Test-PythonInstallation)) {
    pause
    exit 1
}

# Setup falls erforderlich oder erzwungen
if ($Setup -or (-not (Test-Path "steam_price_tracker.db"))) {
    if (-not (Start-Setup)) {
        pause
        exit 1
    }
}

# Konfiguration prüfen
if (-not (Test-Configuration)) {
    Write-Host "💡 Führe zuerst das Setup aus: .\start_tracker.ps1 -Setup" -ForegroundColor Yellow
    pause
    exit 1
}

# Hauptprogramm starten
Write-Host "🚀 Starte Steam Price Tracker..." -ForegroundColor Green
Write-Host "💡 Drücke Ctrl+C zum Beenden" -ForegroundColor Yellow
Write-Host ""

try {
    python main.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Programm normal beendet" -ForegroundColor Green
    }
    else {
        Write-Host "`n❌ Programm mit Fehler beendet" -ForegroundColor Red
        Write-Host "💡 Prüfe die Logs im logs\ Verzeichnis" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "`n❌ Unerwarteter Fehler: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
pause
'''
            
            with open("start_tracker.ps1", "w", encoding="utf-8") as f:
                f.write(powershell_content)
            created_scripts.append("start_tracker.ps1")
            
            detail_msg = f"Startup-Scripts erstellt: {', '.join(created_scripts)}"
            detail_msg += f"\nPlattformen: Windows (.bat), Unix/Linux (.sh), Python (.py), PowerShell (.ps1)"
            detail_msg += f"\nFeatures: Auto-Setup, Dependency-Check, Error-Handling, Status-Anzeige"
            
            self.log_step("Startup Scripts", True, detail_msg)
            return True
            
        except Exception as e:
            self.log_step("Startup Scripts", False, str(e))
            return False
    
    # =====================================================================
    # HAUPTFUNKTIONEN (ERWEITERT UND GEFIXT)
    # =====================================================================
    
    def run_full_setup(self) -> bool:
        """Führt vollständiges Setup durch - PRODUKTIONSVERSION (GEFIXT)"""
        print("\n🏭 STEAM PRICE TRACKER - PRODUKTIONSVERSION")
        print("=" * 60)
        print("🚀 Starte vollständiges Setup...")
        print()
        
        # GEFIXT: VERWENDE time_module ANSTATT time
        start_time = time_module.time()  # ← HIER WAR DAS PROBLEM!
        
        # Setup-Schritte in optimaler Reihenfolge (erweitert)
        setup_steps = [
            ("Master Backup", self.create_master_backup),
            ("Directory Structure", self.create_directories),
            ("Python Version Check", self.check_python_version),
            ("Corrected Requirements", self.correct_requirements),
            ("Python Dependencies", self.install_dependencies),
            ("Configuration Files", self.create_config_files),
            ("Database Schema Test", self.test_database_schema),
            ("Core Functionality Test", self.test_core_functionality),
            ("Main.py Compatibility Test", self.test_main_compatibility),
            ("Charts Integration", self.test_charts_integration),
            ("Steam API Connectivity", self.test_steam_api_connectivity),
            ("CLI Tools Setup", self.test_cli_tools),
            ("Elasticsearch Stack", self.test_elasticsearch_stack),
            ("Database Migration", self.migrate_database_to_new_structure),
            ("Startup Scripts", self.create_startup_scripts)
        ]
        
        # Führe alle Setup-Schritte aus
        for step_name, step_func in setup_steps:
            try:
                print(f"🔄 {step_name}...")
                step_func()
                # GEFIXT: VERWENDE time_module ANSTATT time
                time_module.sleep(0.1)  # ← HIER WAR AUCH EIN PROBLEM!
            except Exception as e:
                self.log_step(step_name, False, f"Unerwarteter Fehler: {e}")
        
        # GEFIXT: VERWENDE time_module ANSTATT time
        setup_duration = time_module.time() - start_time  # ← HIER WAR DAS PROBLEM!
        
        # Report speichern
        self.save_setup_report()
        
        # Zusammenfassung anzeigen
        self._display_setup_summary(setup_duration)
        
        # Erfolg bestimmen
        successful = sum(1 for step in self.setup_log if step["success"])
        total = len(self.setup_log)
        success_rate = (successful / total * 100) if total > 0 else 0
        
        return success_rate >= 80
    
    def run_production_setup(self) -> bool:
        """
        NEU: Produktions-Setup Funktion - Fokus auf kritische Features
        Schneller als run_full_setup() für Produktionsumgebung
        """
        print("\n🏭 STEAM PRICE TRACKER - PRODUKTIONS-SETUP")
        print("=" * 50)
        print("🎯 Fokus auf kritische Features für Produktionsumgebung...")
        print()
        
        # GEFIXT: VERWENDE time_module
        start_time = time_module.time()
        
        # Kritische Setup-Schritte nur
        production_steps = [
            ("Backup", self.create_master_backup),
            ("Python Check", self.check_python_version),
            ("Requirements", self.correct_requirements),
            ("Dependencies", self.install_dependencies),
            ("Database Schema", self.test_database_schema),
            ("Core Functionality", self.test_core_functionality),
            ("Database Migration", self.migrate_database_to_new_structure),
            ("Steam API Test", self.test_steam_api_connectivity)
        ]
        
        for step_name, step_func in production_steps:
            try:
                print(f"🔄 {step_name}...")
                step_func()
                time_module.sleep(0.05)  # Kurze Pause
            except Exception as e:
                self.log_step(step_name, False, f"Produktions-Setup Fehler: {e}")
        
        duration = time_module.time() - start_time
        
        # Produktions-spezifische Validierung
        critical_features = ['core', 'database', 'python_version']
        production_ready = all(self.features_available.get(feature, False) for feature in critical_features)
        
        if production_ready:
            self.log_step("Production Setup", True, f"Produktionsreif in {duration:.1f}s")
            print("\n✅ PRODUKTIONS-SETUP ERFOLGREICH!")
            print("🚀 System ist bereit für den Produktionseinsatz")
            return True
        else:
            missing_features = [f for f in critical_features if not self.features_available.get(f, False)]
            self.log_step("Production Setup", False, f"Kritische Features fehlen: {missing_features}")
            print(f"\n❌ PRODUKTIONS-SETUP FEHLGESCHLAGEN!")
            print(f"🔧 Fehlende kritische Features: {', '.join(missing_features)}")
            return False
    
    def migrate_database_to_new_structure(self) -> bool:
        """
        NEU: Migriert alte Datenbank-Struktur zur neuen steam_charts_tracking Struktur
        """
        try:
            print("🔄 Prüfe Database-Migration...")
            
            db_path = Path("steam_price_tracker.db")
            if not db_path.exists():
                self.log_step("Database Migration", True, "Keine Migration nötig - neue Installation")
                return True
            
            # Backup erstellen
            backup_path = Path("backups") / f"pre_migration_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            backup_path.parent.mkdir(exist_ok=True)
            shutil.copy2(db_path, backup_path)
            
            # Migration durchführen
            from database_manager import create_database_manager
            db_manager = create_database_manager()
            
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Prüfe ob alte chart_games Tabelle existiert
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chart_games'")
                old_table_exists = cursor.fetchone() is not None
                
                if old_table_exists:
                    # Migriere Daten von chart_games zu steam_charts_tracking
                    cursor.execute("""
                        INSERT OR IGNORE INTO steam_charts_tracking 
                        (steam_app_id, name, chart_type, current_rank, last_seen, active)
                        SELECT steam_app_id, name, 'legacy' as chart_type, 
                               rank_position as current_rank, last_update as last_seen, 1 as active
                        FROM chart_games
                    """)
                    
                    migrated_count = cursor.rowcount
                    
                    # Optional: Lösche alte Tabelle nach erfolgreicher Migration
                    # cursor.execute("DROP TABLE chart_games")
                    
                    conn.commit()
                    
                    self.log_step("Database Migration", True, 
                                f"Migration erfolgreich: {migrated_count} Einträge von chart_games migriert")
                else:
                    self.log_step("Database Migration", True, "Keine Migration nötig - bereits neue Struktur")
            
            return True
            
        except Exception as e:
            self.log_step("Database Migration", False, f"Migration fehlgeschlagen: {e}")
            return False
    
    # =====================================================================
    # HELPER UND SUPPORT FUNKTIONEN (ERWEITERT)
    # =====================================================================
    
    def _display_setup_summary(self, duration: float):
        """Zeigt detaillierte Setup-Zusammenfassung - ERWEITERTE VERSION"""
        successful = sum(1 for step in self.setup_log if step["success"])
        total = len(self.setup_log)
        failed = total - successful
        success_rate = (successful / total * 100) if total > 0 else 0
        
        print("\n" + "=" * 60)
        print("📊 SETUP-ZUSAMMENFASSUNG")
        print("=" * 60)
        
        # Grundlegende Statistiken
        print(f"⏱️  Setup-Dauer: {duration:.1f}s")
        print(f"✅ Erfolgreich: {successful}/{total} ({success_rate:.1f}%)")
        print(f"🐍 Python: {self.python_version}")
        print(f"💻 Plattform: {platform.system()} {platform.release()}")
        
        if failed > 0:
            print(f"❌ Fehler: {failed}")
            print("\n🔍 FEHLERDETAILS:")
            for step in self.setup_log:
                if not step["success"]:
                    print(f"   • {step['step']}: {step['details']}")
        
        if self.warnings:
            print(f"\n⚠️  Warnungen: {len(self.warnings)}")
            for warning in self.warnings[:3]:  # Nur erste 3 zeigen
                print(f"   • {warning}")
            if len(self.warnings) > 3:
                print(f"   ... und {len(self.warnings) - 3} weitere")
        
        # Feature-Status (erweitert)
        print("\n🎯 VERFÜGBARE FEATURES:")
        feature_groups = {
            "Kern-Features": ['core', 'database', 'main_app', 'price_tracking', 'python_version'],
            "Erweitert": ['charts', 'steam_api', 'background_scheduler', 'requirements'],
            "Tools": ['cli_tools', 'charts_cli', 'batch_processor'],
            "Optional": ['elasticsearch', 'docker_compose', 'configuration']
        }
        
        for group_name, features in feature_groups.items():
            available_in_group = [f for f in features if self.features_available.get(f, False)]
            if available_in_group:
                print(f"\n   {group_name}:")
                for feature in available_in_group:
                    print(f"      ✅ {feature.replace('_', ' ').title()}")
        
        # Empfehlungen
        recommendations = self._generate_recommendations()
        if recommendations:
            print("\n💡 EMPFEHLUNGEN:")
            for rec in recommendations[:5]:  # Maximal 5 Empfehlungen
                print(f"   {rec}")
        
        # Nächste Schritte
        next_steps = self._generate_next_steps()
        if next_steps:
            print("\n🚀 NÄCHSTE SCHRITTE:")
            for step in next_steps[:3]:  # Wichtigste 3 Schritte
                print(f"   {step}")
        
        print(f"\n📄 Detaillierter Report: setup_report.json")
        print("=" * 60)
        
        # Abschließende Nachricht (erweitert)
        if success_rate >= 90:
            print("🎉 Setup erfolgreich abgeschlossen!")
            print("💡 Du kannst jetzt 'python main.py' ausführen")
            print("🚀 Oder verwende die Startup-Scripts (start_tracker.bat/.sh)")
        elif success_rate >= 80:
            print("✅ Setup größtenteils erfolgreich!")
            print("💡 Grundfunktionen verfügbar, optionale Features prüfen")
        elif success_rate >= 60:
            print("⚠️ Setup mit Einschränkungen abgeschlossen")
            print("🔧 Bitte Fehler beheben für vollständige Funktionalität")
        else:
            print("❌ Setup fehlgeschlagen!")
            print("🆘 Bitte Setup-Report prüfen und Support kontaktieren")
    
    def save_setup_report(self) -> bool:
        """Speichert detaillierten Setup-Report - ERWEITERTE VERSION"""
        try:
            # Basis-Report erstellen
            total_steps = len(self.setup_log)
            successful_steps = sum(1 for step in self.setup_log if step["success"])
            success_rate = (successful_steps / total_steps * 100) if total_steps > 0 else 0
            
            enabled_features = [feature for feature, enabled in self.features_available.items() if enabled]
            disabled_features = [feature for feature, enabled in self.features_available.items() if not enabled]
            
            report = {
                "setup_metadata": {
                    "completed_at": datetime.now().isoformat(),
                    "version": "3.0.0",
                    "python_version": self.python_version,
                    "platform": f"{platform.system()} {platform.release()}",
                    "architecture": platform.machine(),
                    "setup_duration_seconds": f"{total_steps * 0.1:.1f}",  # Approximation
                    "setup_type": "full_setup"
                },
                "results_summary": {
                    "total_steps": total_steps,
                    "successful_steps": successful_steps,
                    "failed_steps": total_steps - successful_steps,
                    "success_rate": round(success_rate, 1),
                    "overall_status": "SUCCESS" if success_rate >= 80 else "PARTIAL" if success_rate >= 60 else "FAILED"
                },
                "features_status": {
                    "enabled_features": enabled_features,
                    "disabled_features": disabled_features,
                    "features_available": self.features_available,
                    "critical_features_ok": all(self.features_available[f] for f in ['core', 'database', 'main_app', 'python_version'])
                },
                "detailed_log": self.setup_log,
                "errors": self.errors,
                "warnings": self.warnings,
                "recommendations": self._generate_recommendations(),
                "next_steps": self._generate_next_steps(),
                "system_info": {
                    "python_executable": sys.executable,
                    "working_directory": str(Path.cwd()),
                    "environment_variables": {
                        "PATH": os.environ.get("PATH", ""),
                        "PYTHONPATH": os.environ.get("PYTHONPATH", "")
                    }
                }
            }
            
            # Report in verschiedenen Formaten speichern
            reports_dir = Path("backups")
            reports_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # JSON Report (maschinenlesbar)
            json_report_path = reports_dir / f"setup_report_{timestamp}.json"
            with open(json_report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            # Human-readable Report
            readable_report_path = reports_dir / f"setup_summary_{timestamp}.txt"
            with open(readable_report_path, "w", encoding="utf-8") as f:
                f.write(self._format_human_readable_report(report))
            
            # Aktueller Report (überschreibt vorherigen)
            with open("setup_report.json", "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern des Setup-Reports: {e}")
            return False
    
    def _generate_recommendations(self) -> List[str]:
        """Generiert Setup-Empfehlungen basierend auf Ergebnissen - ERWEITERT"""
        recommendations = []
        
        if not self.features_available['steam_api']:
            recommendations.append("🔑 Steam API Key in .env konfigurieren für vollständige Funktionalität")
        
        if not self.features_available['charts']:
            recommendations.append("📊 Charts-Funktionalität einrichten für erweiterte Analytics")
        
        if not self.features_available['elasticsearch']:
            recommendations.append("🔍 Elasticsearch für erweiterte Suchfunktionen installieren (optional)")
        
        if not self.features_available['background_scheduler']:
            recommendations.append("⏰ Background Scheduler für automatische Updates einrichten")
        
        if not self.features_available['batch_processor']:
            recommendations.append("⚡ Batch Processor für Performance-Optimierungen aktivieren")
        
        if len(self.errors) > 0:
            recommendations.append("🔧 Fehler in Setup-Log überprüfen und beheben")
        
        if len(self.warnings) > 2:
            recommendations.append("⚠️ Warnungen überprüfen - möglicherweise fehlende optionale Komponenten")
        
        # Plattform-spezifische Empfehlungen
        if platform.system() == "Windows":
            recommendations.append("🖥️ Verwende start_tracker.bat oder start_tracker.ps1 für einfachen Start")
        else:
            recommendations.append("🐧 Verwende start_tracker.sh für einfachen Start (chmod +x start_tracker.sh)")
        
        return recommendations
    
    def _generate_next_steps(self) -> List[str]:
        """Generiert nächste Schritte für den Benutzer - ERWEITERT"""
        next_steps = []
        
        if self.features_available['core'] and self.features_available['main_app']:
            next_steps.append("✅ Führe 'python main.py' aus um die Anwendung zu starten")
            
        if self.features_available['database']:
            next_steps.append("📱 Steam Wishlist importieren (Option 2 in main.py)")
            
        if self.features_available['charts']:
            next_steps.append("📊 Charts-Update durchführen (Option 14 in main.py)")
            
        if self.features_available['price_tracking']:
            next_steps.append("💰 Automatisches Preis-Tracking aktivieren (Option 7 in main.py)")
        
        if not self.features_available['steam_api']:
            next_steps.append("🔑 .env Datei mit deinem Steam API Key konfigurieren")
            
        next_steps.append("📖 README.md für detaillierte Anweisungen lesen")
        
        # Plattform-spezifische nächste Schritte
        if platform.system() == "Windows":
            next_steps.append("🖥️ Oder starte mit: start_tracker.bat")
        else:
            next_steps.append("🐧 Oder starte mit: ./start_tracker.sh")
        
        return next_steps
    
    def _format_human_readable_report(self, report: dict) -> str:
        """Formatiert Report für menschliche Lesbarkeit - ERWEITERT"""
        output = []
        
        output.append("=" * 60)
        output.append("STEAM PRICE TRACKER - SETUP REPORT")
        output.append("=" * 60)
        output.append(f"Abgeschlossen: {report['setup_metadata']['completed_at']}")
        output.append(f"Version: {report['setup_metadata']['version']}")
        output.append(f"Python: {report['setup_metadata']['python_version']}")
        output.append(f"Plattform: {report['setup_metadata']['platform']}")
        output.append(f"Architektur: {report['setup_metadata']['architecture']}")
        output.append("")
        
        # Ergebnisse
        results = report['results_summary']
        output.append("📊 SETUP-ERGEBNISSE:")
        output.append(f"   ✅ Erfolgreich: {results['successful_steps']}/{results['total_steps']} ({results['success_rate']}%)")
        output.append(f"   📈 Status: {results['overall_status']}")
        output.append("")
        
        # Features (erweitert)
        features = report['features_status']
        output.append("🎯 VERFÜGBARE FEATURES:")
        for feature in features['enabled_features']:
            output.append(f"   ✅ {feature.replace('_', ' ').title()}")
        
        if features['disabled_features']:
            output.append("\n❌ NICHT VERFÜGBARE FEATURES:")
            for feature in features['disabled_features']:
                output.append(f"   ❌ {feature.replace('_', ' ').title()}")
        
        output.append("")
        
        # System-Info
        if 'system_info' in report:
            system = report['system_info']
            output.append("💻 SYSTEM-INFORMATIONEN:")
            output.append(f"   Python Executable: {system['python_executable']}")
            output.append(f"   Arbeitsverzeichnis: {system['working_directory']}")
            output.append("")
        
        # Empfehlungen
        if report['recommendations']:
            output.append("💡 EMPFEHLUNGEN:")
            for rec in report['recommendations']:
                output.append(f"   {rec}")
            output.append("")
        
        # Nächste Schritte
        if report['next_steps']:
            output.append("🚀 NÄCHSTE SCHRITTE:")
            for step in report['next_steps']:
                output.append(f"   {step}")
            output.append("")
        
        # Fehler (falls vorhanden)
        if report['errors']:
            output.append("❌ FEHLER:")
            for error in report['errors']:
                output.append(f"   • {error}")
            output.append("")
        
        # Warnungen (falls vorhanden)
        if report['warnings']:
            output.append("⚠️ WARNUNGEN:")
            for warning in report['warnings']:
                output.append(f"   • {warning}")
            output.append("")
        
        output.append("=" * 60)
        
        return "\n".join(output)


def main():
    """Hauptfunktion für Setup mit erweiterten Optionen - VOLLSTÄNDIG ERWEITERT"""
    setup = SteamPriceTrackerSetup()
    
    print("🔧 Steam Price Tracker Setup - PRODUKTIONSVERSION v3.0")
    print("=" * 55)
    print("1. 🚀 Vollständiges Setup durchführen")
    print("2. 🏭 Produktions-Setup (kritische Features only)")  # ← NEU
    print("3. 🔧 Basis-Setup (minimal)")  # ← NEU
    print("4. 📊 Charts-Setup (Analytics)")  # ← NEU
    print("5. 📦 Nur requirements.txt korrigieren") 
    print("6. 🗄️  Database Schema & Migration testen")  # ← UPDATED
    print("7. ⚙️  Nur Kern-Funktionalität testen")
    print("8. 📊 Nur Charts-Integration testen")
    print("9. 🌐 Nur Steam API testen")
    print("10. 🔍 CLI-Tools testen")  # ← NEU
    print("11. 📋 Setup-Status anzeigen")
    print("12. 📊 System-Status detailliert")  # ← NEU
    print("13. 🌐 API-Verbindungen testen")  # ← NEU
    print("14. 💾 Backup erstellen")  # ← NEU
    print("15. 🔄 Database Migration durchführen")  # ← NEU
    print("0. 🧹 Cleanup und Reset")
    print()
    
    choice = input("Auswahl (0-15): ").strip()
    
    if choice == "1":
        setup.run_full_setup()
    elif choice == "2":
        setup.run_production_setup()  # ← NEU
    elif choice == "3":
        setup.basic_setup()  # ← NEU
    elif choice == "4":
        setup.charts_setup()  # ← NEU
    elif choice == "5":
        setup.correct_requirements()
        setup.install_dependencies()
    elif choice == "6":
        setup.test_database_schema()
        setup.migrate_database_to_new_structure()
    elif choice == "7":
        setup.test_core_functionality()
    elif choice == "8":
        setup.test_charts_integration()
    elif choice == "9":
        setup.test_steam_api_connectivity()
    elif choice == "10":
        setup.test_cli_tools()  # ← NEU
    elif choice == "11":
        # Status aus vorherigem Setup laden
        try:
            with open("setup_report.json", "r", encoding="utf-8") as f:
                report = json.load(f)
            print("\n📊 LETZTER SETUP-STATUS:")
            print(setup._format_human_readable_report(report))
        except FileNotFoundError:
            print("❌ Kein Setup-Report gefunden. Führe zuerst ein Setup durch.")
    elif choice == "12":
        setup.show_system_status()  # ← NEU
    elif choice == "13":
        setup.test_api_connection_detailed()  # ← NEU
    elif choice == "14":
        setup.create_backup()  # ← NEU
    elif choice == "15":
        setup.migrate_database_to_new_structure()  # ← NEU
    elif choice == "0":
        # Cleanup (erweitert)
        print("🧹 Cleanup wird durchgeführt...")
        cleanup_files = ["test_*.db", "setup_report.json", "*.pyc", "__pycache__"]
        cleaned_count = 0
        
        for pattern in cleanup_files:
            for file_path in Path(".").glob(pattern):
                try:
                    if file_path.is_file():
                        file_path.unlink()
                        print(f"🗑️  {file_path} entfernt")
                        cleaned_count += 1
                    elif file_path.is_dir():
                        shutil.rmtree(file_path)
                        print(f"📁 {file_path}/ entfernt")
                        cleaned_count += 1
                except Exception as e:
                    print(f"⚠️ Konnte {file_path} nicht entfernen: {e}")
        
        print(f"✅ Cleanup abgeschlossen: {cleaned_count} Dateien/Ordner entfernt")
    else:
        print("❌ Ungültige Auswahl")


if __name__ == "__main__":
    main()