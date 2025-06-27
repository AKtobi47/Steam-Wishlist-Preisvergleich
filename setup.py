#!/usr/bin/env python3
"""
Steam Price Tracker Setup - KORRIGIERT
Behebt alle identifizierten Setup-Probleme:
- Korrigierte requirements.txt ohne eingebaute Module
- Database Schema-Kompatibilität
- Robuste API-Tests
- Vollständige Feature-Validierung
"""

import os
import sys
import json
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
import logging

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SteamPriceTrackerSetup:
    """
    Korrigierte Setup-Klasse für Steam Price Tracker
    Behebt alle identifizierten Probleme aus dem Setup-Report
    """
    
    def __init__(self):
        self.setup_steps = []
        self.features_status = {}
        self.errors = []
        
        # Korrigierte Requirements (ohne eingebaute Module)
        self.corrected_requirements = [
            "requests>=2.31.0",
            "schedule>=1.2.0", 
            "python-dotenv>=1.0.0",
            "colorlog>=6.7.0",
            "tqdm>=4.66.0",
            "python-dateutil>=2.8.0",
            "pandas>=2.1.0",
            "matplotlib>=3.7.0",
            "seaborn>=0.12.0",
            "plotly>=5.17.0",
            "psutil>=5.9.0",
            "memory-profiler>=0.61.0",
            "jsonschema>=4.19.0",
            "pathspec>=0.11.0",
            "rich>=13.6.0",
            "structlog>=23.2.0",
            "dask>=2023.9.0",
            "httpx>=0.25.0",
            "aiohttp>=3.8.0",
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.1.0",
            "mypy>=1.6.0"
        ]
        
        print("🚀 Steam Price Tracker Setup (KORRIGIERT)")
        print("=" * 50)
    
    def log_step(self, step_name: str, success: bool, details: str = ""):
        """Protokolliert einen Setup-Schritt"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        step_info = {
            "timestamp": timestamp,
            "step": step_name,
            "success": success,
            "details": details
        }
        
        self.setup_steps.append(step_info)
        
        status = "✅" if success else "❌"
        print(f"{status} {step_name}")
        if details:
            print(f"   {details}")
        
        if not success:
            self.errors.append(f"{step_name}: {details}")
    
    def create_master_backup(self) -> bool:
        """Erstellt Backup der aktuellen Installation"""
        try:
            backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(backup_dir, exist_ok=True)
            
            files_to_backup = [
                "main.py", "price_tracker.py", "database_manager.py", 
                "requirements.txt", ".env", "setup_report.json"
            ]
            
            backed_up = 0
            for file in files_to_backup:
                if os.path.exists(file):
                    shutil.copy2(file, backup_dir)
                    backed_up += 1
            
            self.log_step("Master Backup", True, f"{backed_up} Dateien gesichert")
            return True
            
        except Exception as e:
            self.log_step("Master Backup", False, str(e))
            return False
    
    def create_corrected_requirements(self) -> bool:
        """Erstellt korrigierte requirements.txt ohne eingebaute Module"""
        try:
            # Backup der alten requirements.txt
            if os.path.exists("requirements.txt"):
                shutil.copy2("requirements.txt", "requirements_old.txt")
            
            # Neue, korrigierte requirements.txt erstellen
            with open("requirements.txt", "w", encoding="utf-8") as f:
                f.write("# requirements.txt - Steam Price Tracker (KORRIGIERT)\n")
                f.write("# Nur externe Dependencies - eingebaute Module entfernt\n\n")
                f.write("# ========================================\n")
                f.write("# KERN-REQUIREMENTS (ZWINGEND ERFORDERLICH)\n")
                f.write("# ========================================\n\n")
                
                core_requirements = [
                    "requests>=2.31.0",
                    "schedule>=1.2.0", 
                    "python-dotenv>=1.0.0",
                    "colorlog>=6.7.0",
                    "tqdm>=4.66.0",
                    "python-dateutil>=2.8.0"
                ]
                
                for req in core_requirements:
                    f.write(f"{req}\n")
                
                f.write("\n# ========================================\n")
                f.write("# OPTIONAL: DATENANALYSE & VISUALISIERUNG\n")
                f.write("# ========================================\n\n")
                
                optional_requirements = [
                    "pandas>=2.1.0",
                    "matplotlib>=3.7.0",
                    "seaborn>=0.12.0",
                    "plotly>=5.17.0",
                    "numpy>=1.24.0",
                    "scipy>=1.11.0"
                ]
                
                for req in optional_requirements:
                    f.write(f"{req}\n")
                
                f.write("\n# ========================================\n")
                f.write("# ENTFERNTE EINGEBAUTE MODULE\n")
                f.write("# ========================================\n")
                f.write("# \n")
                f.write("# Diese Module sind in Python eingebaut und dürfen NICHT in requirements.txt:\n")
                f.write("# - tkinter (GUI - eingebaut in Python)\n")
                f.write("# - argparse (CLI parsing - eingebaut)\n")
                f.write("# - zipfile (ZIP-Verarbeitung - eingebaut)\n")
                f.write("# - csv (CSV-Verarbeitung - eingebaut)\n")
                f.write("# - json (JSON-Verarbeitung - eingebaut)\n")
                f.write("# - sqlite3 (Datenbank - eingebaut)\n")
                f.write("# - threading (Threading - eingebaut)\n")
                f.write("# - datetime (Datum/Zeit - eingebaut)\n")
                f.write("# - os, sys, pathlib (System - eingebaut)\n")
                f.write("# - logging (Logging - eingebaut)\n")
                f.write("# - subprocess (Prozesse - eingebaut)\n")
                f.write("# - urllib (URL-Verarbeitung - eingebaut)\n")
                f.write("#\n")
                f.write("# ========================================\n")
            
            self.log_step("Corrected Requirements", True, "requirements.txt korrigiert ohne eingebaute Module")
            return True
            
        except Exception as e:
            self.log_step("Corrected Requirements", False, str(e))
            return False
    
    def install_dependencies(self) -> bool:
        """Installiert Dependencies mit korrigierter requirements.txt"""
        try:
            print("📦 Installiere korrigierte Dependencies...")
            
            # Verwende korrigierte requirements.txt
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.log_step("Python Dependencies", True, "Alle Dependencies erfolgreich installiert")
                return True
            else:
                error_msg = result.stderr.strip()
                self.log_step("Python Dependencies", False, f"Installation fehlgeschlagen: {error_msg}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_step("Python Dependencies", False, "Installation timeout nach 300s")
            return False
        except Exception as e:
            self.log_step("Python Dependencies", False, str(e))
            return False
    
    def create_directories(self) -> bool:
        """Erstellt erforderliche Verzeichnisse"""
        try:
            directories = ["data", "backups", "logs", "exports"]
            created = 0
            
            for directory in directories:
                if not os.path.exists(directory):
                    os.makedirs(directory)
                    created += 1
            
            self.log_step("Directory Structure", True, f"{created} Verzeichnisse erstellt")
            return True
            
        except Exception as e:
            self.log_step("Directory Structure", False, str(e))
            return False
    
    def test_database_schema(self) -> bool:
        """Testet das korrigierte Database Schema"""
        try:
            # Importiere korrigierte DatabaseManager
            from database_manager import DatabaseManager
            
            # Test-Datenbank erstellen
            test_db = DatabaseManager("test_schema.db")
            
            # Test: add_tracked_app mit source Parameter
            success = test_db.add_tracked_app("123456", "Test Game", "manual")
            if not success:
                raise Exception("add_tracked_app fehlgeschlagen")
            
            # Test: get_tracked_apps
            apps = test_db.get_tracked_apps()
            if not isinstance(apps, list):
                raise Exception("get_tracked_apps gibt keine Liste zurück")
            
            # Test: get_database_stats (korrigierte API)
            stats = test_db.get_database_stats()
            if not isinstance(stats, dict):
                raise Exception("get_database_stats gibt kein Dict zurück")
            
            # Schema-Validierung: prüfe ob 'source' Spalte existiert
            with test_db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(tracked_apps)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'source' not in columns:
                    raise Exception("'source' Spalte fehlt in tracked_apps Tabelle")
            
            # Test-Datenbank bereinigen
            os.remove("test_schema.db")
            
            self.log_step("Database Schema Test", True, "Schema-Kompatibilität bestätigt")
            return True
            
        except Exception as e:
            self.log_step("Database Schema Test", False, str(e))
            return False
    
    def test_core_functionality(self) -> bool:
        """Testet Kern-Funktionalität mit korrigierten APIs"""
        try:
            # Teste Price Tracker Erstellung
            from price_tracker import create_price_tracker
            
            tracker = create_price_tracker(enable_charts=True)
            if not tracker:
                raise Exception("Price Tracker konnte nicht erstellt werden")
            
            # Teste korrigierte APIs
            if not hasattr(tracker, 'db_manager'):
                raise Exception("tracker.db_manager nicht verfügbar")
            
            if not hasattr(tracker.db_manager, 'get_tracked_apps'):
                raise Exception("get_tracked_apps Methode fehlt")
            
            if not hasattr(tracker.db_manager, 'add_tracked_app'):
                raise Exception("add_tracked_app Methode fehlt")
            
            if not hasattr(tracker.db_manager, 'get_database_stats'):
                raise Exception("get_database_stats Methode fehlt")
            
            # Teste add_tracked_app mit korrekten Parametern
            success = tracker.db_manager.add_tracked_app("654321", "Test Game 2", "test")
            if not success:
                raise Exception("add_tracked_app Test fehlgeschlagen")
            
            # Teste get_tracked_apps
            apps = tracker.db_manager.get_tracked_apps()
            if not isinstance(apps, list):
                raise Exception("get_tracked_apps Test fehlgeschlagen")
            
            self.log_step("Core Functionality Test", True, "Alle Kern-APIs funktionieren")
            return True
            
        except Exception as e:
            self.log_step("Core Functionality Test", False, str(e))
            return False
    
    def test_main_py_compatibility(self) -> bool:
        """Testet Kompatibilität mit der korrigierten main.py"""
        try:
            # Prüfe ob main.py existiert und importiert werden kann
            if not os.path.exists("main.py"):
                raise Exception("main.py nicht gefunden")
            
            # Teste kritische Funktionen aus main.py
            # (Ohne main.py auszuführen, um Endlosschleife zu vermeiden)
            
            # Lese main.py und prüfe auf kritische Funktionen
            with open("main.py", "r", encoding="utf-8") as f:
                main_content = f.read()
            
            required_functions = [
                "get_tracked_apps_safe",
                "add_app_safe", 
                "get_statistics_safe",
                "enhanced_cleanup",
                "create_tracker_with_fallback"
            ]
            
            missing_functions = []
            for func in required_functions:
                if f"def {func}" not in main_content:
                    missing_functions.append(func)
            
            if missing_functions:
                raise Exception(f"Fehlende Funktionen in main.py: {missing_functions}")
            
            # Prüfe auf 27 Menüoptionen
            menu_options = []
            for i in range(28):  # 0-27
                if f'choice == "{i}"' in main_content:
                    menu_options.append(i)
            
            if len(menu_options) < 28:  # 0-27 = 28 Optionen
                raise Exception(f"Nur {len(menu_options)} von 28 Menüoptionen gefunden")
            
            self.log_step("Main.py Compatibility Test", True, "Alle 27 Menüoptionen verfügbar")
            return True
            
        except Exception as e:
            self.log_step("Main.py Compatibility Test", False, str(e))
            return False
    
    def test_charts_integration(self) -> bool:
        """Testet Charts-Integration"""
        try:
            try:
                from steam_charts_manager import SteamChartsManager
                charts_manager = SteamChartsManager("test_key", None, None)
                
                # Teste grundlegende Charts-Funktionalität
                if hasattr(charts_manager, 'CHART_TYPES'):
                    chart_types = charts_manager.CHART_TYPES
                    if len(chart_types) > 0:
                        self.features_status['charts'] = True
                        self.log_step("Charts Integration", True, f"{len(chart_types)} Chart-Typen verfügbar")
                        return True
                
            except ImportError:
                self.features_status['charts'] = False
                self.log_step("Charts Integration", False, "SteamChartsManager nicht verfügbar")
                return False
            
        except Exception as e:
            self.features_status['charts'] = False
            self.log_step("Charts Integration", False, str(e))
            return False
    
    def test_cli_tools(self) -> bool:
        """Testet CLI-Tools Verfügbarkeit"""
        try:
            cli_tools = [
                "batch_processor.py",
                "charts_cli_manager.py"
            ]
            
            available_tools = 0
            for tool in cli_tools:
                if os.path.exists(tool):
                    available_tools += 1
            
            if available_tools > 0:
                self.features_status['cli_tools'] = True
                self.log_step("CLI Tools Setup", True, f"{available_tools} CLI-Tools verfügbar")
                return True
            else:
                self.features_status['cli_tools'] = False
                self.log_step("CLI Tools Setup", False, "Keine CLI-Tools gefunden")
                return False
            
        except Exception as e:
            self.features_status['cli_tools'] = False
            self.log_step("CLI Tools Setup", False, str(e))
            return False
    
    def test_elasticsearch_stack(self) -> bool:
        """Testet Elasticsearch-Stack (optional)"""
        try:
            try:
                from elasticsearch_manager import ElasticsearchManager
                es_manager = ElasticsearchManager()
                
                self.features_status['elasticsearch'] = True
                self.log_step("Elasticsearch Stack", True, "Elasticsearch-Integration verfügbar")
                return True
                
            except ImportError:
                self.features_status['elasticsearch'] = False
                self.log_step("Elasticsearch Stack", False, "Elasticsearch-Manager nicht verfügbar (optional)")
                return True  # Nicht kritisch
            
        except Exception as e:
            self.features_status['elasticsearch'] = False
            self.log_step("Elasticsearch Stack", False, f"ES-Test fehlgeschlagen: {e}")
            return True  # Nicht kritisch
    
    def create_startup_scripts(self) -> bool:
        """Erstellt Start-Skripte"""
        try:
            # Windows Batch-Datei
            with open("start.bat", "w", encoding="utf-8") as f:
                f.write("@echo off\n")
                f.write("echo Steam Price Tracker wird gestartet...\n")
                f.write("python main.py\n")
                f.write("pause\n")
            
            # Linux/Mac Shell-Skript
            with open("start.sh", "w", encoding="utf-8") as f:
                f.write("#!/bin/bash\n")
                f.write("echo \"Steam Price Tracker wird gestartet...\"\n")
                f.write("python3 main.py\n")
                f.write("read -p \"Drücke Enter zum Beenden...\"\n")
            
            # Shell-Skript ausführbar machen (Linux/Mac)
            try:
                os.chmod("start.sh", 0o755)
            except:
                pass  # Windows oder Berechtigung fehlgeschlagen
            
            self.log_step("Startup Scripts", True, "start.bat und start.sh erstellt")
            return True
            
        except Exception as e:
            self.log_step("Startup Scripts", False, str(e))
            return False
    
    def create_configuration_files(self) -> bool:
        """Erstellt Konfigurationsdateien"""
        try:
            # .env Template (falls nicht vorhanden)
            if not os.path.exists(".env"):
                with open("env_template.txt", "w", encoding="utf-8") as f:
                    f.write("# Steam Price Tracker Konfiguration\n")
                    f.write("# Kopiere diese Datei zu '.env' und fülle die Werte aus\n\n")
                    f.write("# Steam Web API Key (erforderlich)\n")
                    f.write("STEAM_API_KEY=your_steam_api_key_here\n\n")
                    f.write("# Optional: Steam User ID für Wishlist-Import\n")
                    f.write("STEAM_USER_ID=\n\n")
                    f.write("# Optional: Datenbank-Pfad\n")
                    f.write("DATABASE_PATH=steam_price_tracker.db\n\n")
                    f.write("# Optional: Logging-Level (DEBUG, INFO, WARNING, ERROR)\n")
                    f.write("LOG_LEVEL=INFO\n")
            
            # config.json (Anwendungskonfiguration)
            config = {
                "version": "1.0.0",
                "database": {
                    "path": "steam_price_tracker.db",
                    "backup_interval_hours": 24,
                    "cleanup_days": 90
                },
                "scheduler": {
                    "price_update_interval_hours": 6,
                    "charts_update_interval_hours": 2,
                    "max_concurrent_requests": 5,
                    "request_delay_seconds": 1
                },
                "features": {
                    "charts_enabled": True,
                    "elasticsearch_enabled": False,
                    "auto_backup": True,
                    "performance_monitoring": True
                },
                "api": {
                    "steam_timeout_seconds": 30,
                    "cheapshark_timeout_seconds": 15,
                    "max_retries": 3
                }
            }
            
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            
            self.log_step("Configuration Files", True, "Konfigurationsdateien erstellt")
            return True
            
        except Exception as e:
            self.log_step("Configuration Files", False, str(e))
            return False
    
    def generate_setup_report(self) -> bool:
        """Generiert finalen Setup-Report"""
        try:
            # Feature-Status finalisieren
            self.features_status.update({
                'core': any(step['step'] == 'Core Functionality Test' and step['success'] for step in self.setup_steps),
                'database': any(step['step'] == 'Database Schema Test' and step['success'] for step in self.setup_steps),
                'main_app': any(step['step'] == 'Main.py Compatibility Test' and step['success'] for step in self.setup_steps),
                'batch_processor': os.path.exists('batch_processor.py'),
                'charts_cli': os.path.exists('charts_cli_manager.py'),
                'docker_compose': os.path.exists('docker-compose.yml')
            })
            
            # Erfolgsstatistiken
            total_steps = len(self.setup_steps)
            successful_steps = sum(1 for step in self.setup_steps if step['success'])
            success_rate = (successful_steps / total_steps * 100) if total_steps > 0 else 0
            
            report = {
                "setup_completed_at": datetime.now().isoformat(),
                "features_available": self.features_status,
                "setup_log": self.setup_steps,
                "total_steps": total_steps,
                "successful_steps": successful_steps,
                "failed_steps": total_steps - successful_steps,
                "success_rate": round(success_rate, 1),
                "errors": self.errors
            }
            
            with open("setup_report.json", "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            
            # Konsolne-Zusammenfassung
            print("\n" + "=" * 60)
            print("📊 SETUP-ZUSAMMENFASSUNG")
            print("=" * 60)
            print(f"✅ Erfolgreich: {successful_steps}/{total_steps} ({success_rate:.1f}%)")
            
            if self.errors:
                print(f"❌ Fehler: {len(self.errors)}")
                for error in self.errors:
                    print(f"   • {error}")
            
            print("\n🎯 VERFÜGBARE FEATURES:")
            for feature, available in self.features_status.items():
                status = "✅" if available else "❌"
                print(f"   {status} {feature}")
            
            print(f"\n📄 Detaillierter Report: setup_report.json")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Generieren des Setup-Reports: {e}")
            return False
    
    def run_full_setup(self) -> bool:
        """Führt vollständiges Setup durch"""
        print("🚀 Starte vollständiges Setup...")
        
        # Setup-Schritte in korrekter Reihenfolge
        setup_steps = [
            ("Master Backup", self.create_master_backup),
            ("Directory Structure", self.create_directories),
            ("Corrected Requirements", self.create_corrected_requirements),
            ("Python Dependencies", self.install_dependencies),
            ("Configuration Files", self.create_configuration_files),
            ("Database Schema Test", self.test_database_schema),
            ("Core Functionality Test", self.test_core_functionality),
            ("Main.py Compatibility Test", self.test_main_py_compatibility),
            ("Charts Integration", self.test_charts_integration),
            ("CLI Tools Setup", self.test_cli_tools),
            ("Elasticsearch Stack", self.test_elasticsearch_stack),
            ("Startup Scripts", self.create_startup_scripts)
        ]
        
        for step_name, step_function in setup_steps:
            try:
                step_function()
            except Exception as e:
                self.log_step(step_name, False, f"Unerwarteter Fehler: {e}")
        
        # Setup-Report generieren
        self.generate_setup_report()
        
        # Erfolgsstatus
        successful_steps = sum(1 for step in self.setup_steps if step['success'])
        total_steps = len(self.setup_steps)
        success_rate = (successful_steps / total_steps * 100) if total_steps > 0 else 0
        
        if success_rate >= 80:
            print("\n🎉 Setup erfolgreich abgeschlossen!")
            print("💡 Du kannst jetzt 'python main.py' ausführen")
            return True
        else:
            print(f"\n⚠️ Setup nur teilweise erfolgreich ({success_rate:.1f}%)")
            print("💡 Prüfe den Setup-Report für Details")
            return False

def main():
    """Setup-Hauptfunktion"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        setup = SteamPriceTrackerSetup()
        
        if command == "full":
            setup.run_full_setup()
        elif command == "requirements":
            setup.create_corrected_requirements()
        elif command == "database":
            setup.test_database_schema()
        elif command == "test":
            setup.test_core_functionality()
        else:
            print("❌ Unbekannter Befehl")
            print("💡 Verfügbare Befehle: full, requirements, database, test")
    else:
        # Interaktive Auswahl
        print("🔧 Steam Price Tracker Setup")
        print("1. Vollständiges Setup durchführen")
        print("2. Nur requirements.txt korrigieren") 
        print("3. Nur Database Schema testen")
        print("4. Nur Kern-Funktionalität testen")
        
        choice = input("Auswahl (1-4): ").strip()
        
        setup = SteamPriceTrackerSetup()
        
        if choice == "1":
            setup.run_full_setup()
        elif choice == "2":
            setup.create_corrected_requirements()
        elif choice == "3":
            setup.test_database_schema()
        elif choice == "4":
            setup.test_core_functionality()
        else:
            print("❌ Ungültige Auswahl")

if __name__ == "__main__":
    main()
