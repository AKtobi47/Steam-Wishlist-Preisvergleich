#!/usr/bin/env python3
"""
Steam Price Tracker - Master Setup Script
Orchestriert alle Setup-Komponenten und CLI-Tools
Vollständige Installation aller Features mit einem Kommando
"""

import sys
import os
import json
import subprocess
import shutil
import time
from pathlib import Path
from datetime import datetime
import logging

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MasterSetup:
    """Master Setup-Klasse für alle Steam Price Tracker Features"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.backup_dir = self.project_root / "backup_before_master_setup"
        self.setup_log = []
        
        # Feature-Verfügbarkeit prüfen
        self.features = self.check_feature_availability()
    
    def check_feature_availability(self):
        """Prüft welche Features verfügbar sind"""
        features = {
            'core': self.project_root / "price_tracker.py",
            'charts': self.project_root / "steam_charts_manager.py",
            'batch_processor': self.project_root / "batch_processor.py",
            'charts_cli': self.project_root / "charts_cli_manager.py",
            'elasticsearch': self.project_root / "elasticsearch_setup.py",
            'kibana_setup': self.project_root / "setup_kibana_dashboards.py",
            'main_app': self.project_root / "main.py",
            'docker_compose': self.project_root / "docker-compose-elk.yml"
        }
        
        available = {}
        for feature, file_path in features.items():
            available[feature] = file_path.exists()
        
        return available
    
    def log_step(self, step_name, success, details=""):
        """Loggt Setup-Schritte"""
        status = "✅ SUCCESS" if success else "❌ FAILED"
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        log_entry = {
            'timestamp': timestamp,
            'step': step_name,
            'success': success,
            'details': details
        }
        
        self.setup_log.append(log_entry)
        logger.info(f"{status} - {step_name} ({timestamp})")
        if details:
            logger.info(f"         Details: {details}")
    
    def create_master_backup(self):
        """Erstellt Master-Backup vor Setup"""
        logger.info("💾 Erstelle Master-Backup...")
        
        try:
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
            
            self.backup_dir.mkdir(parents=True)
            
            # Wichtige Dateien sichern
            backup_files = [
                "main.py", "price_tracker.py", "database_manager.py",
                "steam_wishlist_manager.py", "config.json", ".env",
                "steam_price_tracker.db", "requirements.txt"
            ]
            
            backed_up = 0
            for file_name in backup_files:
                file_path = self.project_root / file_name
                if file_path.exists():
                    shutil.copy2(file_path, self.backup_dir / file_name)
                    backed_up += 1
            
            # Backup-Info erstellen
            backup_info = {
                'created_at': datetime.now().isoformat(),
                'backed_up_files': backed_up,
                'project_root': str(self.project_root),
                'features_available': self.features
            }
            
            with open(self.backup_dir / "backup_info.json", 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            self.log_step("Master Backup", True, f"{backed_up} Dateien gesichert")
            return True
            
        except Exception as e:
            self.log_step("Master Backup", False, str(e))
            return False
    
    def setup_directory_structure(self):
        """Erstellt vollständige Verzeichnisstruktur"""
        logger.info("📁 Erstelle Verzeichnisstruktur...")
        
        directories = [
            "logs", "exports", "backups", "temp_schedulers", "temp_scripts",
            "elasticsearch", "elasticsearch/config", "elasticsearch/data", "elasticsearch/logs",
            "kibana", "kibana/config", "kibana/data", "kibana/dashboards",
            "logstash", "logstash/config", "logstash/pipeline", "logstash/data",
            "metricbeat", "apm-server"
        ]
        
        try:
            created = 0
            for directory in directories:
                dir_path = self.project_root / directory
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    created += 1
            
            self.log_step("Directory Structure", True, f"{created} Verzeichnisse erstellt")
            return True
            
        except Exception as e:
            self.log_step("Directory Structure", False, str(e))
            return False
    
    def install_python_dependencies(self):
        """Installiert alle Python-Dependencies"""
        logger.info("📦 Installiere Python-Dependencies...")
        
        try:
            # Basis-Requirements
            if (self.project_root / "requirements.txt").exists():
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    raise Exception(f"Requirements Installation fehlgeschlagen: {result.stderr}")
            
            # Elasticsearch-Requirements (optional)
            if (self.project_root / "requirements-elasticsearch.txt").exists():
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", "requirements-elasticsearch.txt"
                ], capture_output=True, text=True)
                
                # Elasticsearch ist optional, daher kein Fehler bei Fehlschlag
                if result.returncode == 0:
                    self.log_step("Elasticsearch Dependencies", True, "Elasticsearch Support aktiviert")
                else:
                    self.log_step("Elasticsearch Dependencies", False, "Optional - nicht kritisch")
            
            self.log_step("Python Dependencies", True, "Alle Dependencies installiert")
            return True
            
        except Exception as e:
            self.log_step("Python Dependencies", False, str(e))
            return False
    
    def setup_configuration_files(self):
        """Erstellt Konfigurationsdateien"""
        logger.info("⚙️ Setup Konfigurationsdateien...")
        
        try:
            # .env-Datei erstellen falls nicht vorhanden
            env_file = self.project_root / ".env"
            if not env_file.exists():
                env_example = self.project_root / ".env.example"
                if env_example.exists():
                    shutil.copy2(env_example, env_file)
                else:
                    # Minimal .env erstellen
                    with open(env_file, 'w') as f:
                        f.write("# Steam Price Tracker Configuration\n")
                        f.write("STEAM_API_KEY=your_steam_api_key_here\n")
                        f.write("CHEAPSHARK_RATE_LIMIT=1.5\n")
                        f.write("TRACKING_INTERVAL_HOURS=6\n")
            
            # config.json erstellen falls nicht vorhanden
            config_file = self.project_root / "config.json"
            if not config_file.exists():
                basic_config = {
                    "database": {"path": "steam_price_tracker.db"},
                    "tracking": {"default_interval_hours": 6},
                    "charts": {"enabled": False},
                    "elasticsearch": {"enabled": False},
                    "logging": {"level": "INFO"}
                }
                
                with open(config_file, 'w') as f:
                    json.dump(basic_config, f, indent=2)
            
            self.log_step("Configuration Files", True, "Konfigurationsdateien erstellt")
            return True
            
        except Exception as e:
            self.log_step("Configuration Files", False, str(e))
            return False
    
    def initialize_database(self):
        """Initialisiert Datenbank"""
        logger.info("🗄️ Initialisiere Datenbank...")
        
        try:
            # Database Manager importieren und initialisieren
            sys.path.insert(0, str(self.project_root))
            from database_manager import DatabaseManager
            
            db = DatabaseManager()
            
            # Charts-Tabellen hinzufügen falls verfügbar
            if hasattr(db, 'init_charts_tables'):
                db.init_charts_tables()
            
            self.log_step("Database Initialization", True, "Datenbank initialisiert")
            return True
            
        except Exception as e:
            self.log_step("Database Initialization", False, str(e))
            return False
    
    def test_core_functionality(self):
        """Testet Kern-Funktionalität"""
        logger.info("🧪 Teste Kern-Funktionalität...")
        
        try:
            sys.path.insert(0, str(self.project_root))
            
            # Price Tracker testen
            from price_tracker import create_price_tracker
            tracker = create_price_tracker(enable_charts=False)
            
            # Basis-Test: Apps abrufen
            apps = tracker.get_tracked_apps()
            
            self.log_step("Core Functionality Test", True, f"Price Tracker funktional")
            return True
            
        except Exception as e:
            self.log_step("Core Functionality Test", False, str(e))
            return False
    
    def setup_charts_integration(self):
        """Setup Charts-Integration"""
        if not self.features['charts']:
            self.log_step("Charts Integration", False, "Charts-Dateien nicht verfügbar")
            return False
        
        logger.info("📊 Setup Charts-Integration...")
        
        try:
            # Charts-Funktionalität testen
            sys.path.insert(0, str(self.project_root))
            from steam_charts_manager import SteamChartsManager
            
            # API Key aus .env laden
            from steam_wishlist_manager import load_api_key_from_env
            api_key = load_api_key_from_env()
            
            if not api_key or api_key == "your_steam_api_key_here":
                self.log_step("Charts Integration", False, "Steam API Key erforderlich")
                return False
            
            # Charts Manager testen
            from database_manager import DatabaseManager
            db = DatabaseManager()
            charts_manager = SteamChartsManager(api_key, db)
            
            self.log_step("Charts Integration", True, "Charts-Integration verfügbar")
            return True
            
        except Exception as e:
            self.log_step("Charts Integration", False, str(e))
            return False
    
    def setup_cli_tools(self):
        """Setup CLI-Tools"""
        logger.info("🛠️ Setup CLI-Tools...")
        
        cli_tools = {
            'batch_processor': self.features['batch_processor'],
            'charts_cli': self.features['charts_cli']
        }
        
        available_tools = 0
        for tool_name, available in cli_tools.items():
            if available:
                available_tools += 1
        
        if available_tools > 0:
            self.log_step("CLI Tools Setup", True, f"{available_tools} CLI-Tools verfügbar")
            return True
        else:
            self.log_step("CLI Tools Setup", False, "Keine CLI-Tools verfügbar")
            return False
    
    def setup_elasticsearch_stack(self):
        """Setup Elasticsearch Stack (optional)"""
        if not self.features['elasticsearch']:
            self.log_step("Elasticsearch Stack", False, "Elasticsearch Setup nicht verfügbar")
            return False
        
        logger.info("🔍 Setup Elasticsearch Stack...")
        
        try:
            # Docker-Verfügbarkeit prüfen
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                self.log_step("Elasticsearch Stack", False, "Docker nicht verfügbar")
                return False
            
            # Elasticsearch Setup ausführen
            elasticsearch_setup = self.project_root / "elasticsearch_setup.py"
            if elasticsearch_setup.exists():
                result = subprocess.run([
                    sys.executable, str(elasticsearch_setup), 'setup'
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.log_step("Elasticsearch Stack", True, "ELK Stack Setup abgeschlossen")
                    return True
                else:
                    self.log_step("Elasticsearch Stack", False, "ELK Setup fehlgeschlagen")
                    return False
            
        except Exception as e:
            self.log_step("Elasticsearch Stack", False, str(e))
            return False
    
    def create_startup_scripts(self):
        """Erstellt Startup-Scripts"""
        logger.info("🚀 Erstelle Startup-Scripts...")
        
        try:
            # Windows Batch-Script
            batch_script = """@echo off
title Steam Price Tracker v3.0
echo 🚀 Steam Price Tracker v3.0 wird gestartet...
echo ===============================================
echo.

cd /d "%~dp0"

echo 📊 Prüfe Python Installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python nicht gefunden!
    echo Installiere Python von https://python.org
    pause
    exit /b 1
)

echo ✅ Python gefunden
echo.

echo 🔄 Starte Steam Price Tracker...
python main.py

echo.
echo 👋 Steam Price Tracker beendet
pause
"""
            
            with open(self.project_root / "start.bat", 'w', encoding='utf-8') as f:
                f.write(batch_script)
            
            # Linux/macOS Shell-Script
            shell_script = """#!/bin/bash
echo "🚀 Steam Price Tracker v3.0 wird gestartet..."
echo "==============================================="
echo

cd "$(dirname "$0")"

echo "📊 Prüfe Python Installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 nicht gefunden!"
    echo "Installiere Python3 über deinen Package Manager"
    exit 1
fi

echo "✅ Python gefunden"
echo

echo "🔄 Starte Steam Price Tracker..."
python3 main.py

echo
echo "👋 Steam Price Tracker beendet"
"""
            
            shell_path = self.project_root / "start.sh"
            with open(shell_path, 'w', encoding='utf-8') as f:
                f.write(shell_script)
            
            # Ausführbar machen
            os.chmod(shell_path, 0o755)
            
            self.log_step("Startup Scripts", True, "start.bat und start.sh erstellt")
            return True
            
        except Exception as e:
            self.log_step("Startup Scripts", False, str(e))
            return False
    
    def create_completion_report(self):
        """Erstellt Abschluss-Bericht"""
        logger.info("📋 Erstelle Abschluss-Bericht...")
        
        try:
            report = {
                'setup_completed_at': datetime.now().isoformat(),
                'features_available': self.features,
                'setup_log': self.setup_log,
                'total_steps': len(self.setup_log),
                'successful_steps': sum(1 for step in self.setup_log if step['success']),
                'failed_steps': sum(1 for step in self.setup_log if not step['success']),
                'success_rate': round(sum(1 for step in self.setup_log if step['success']) / len(self.setup_log) * 100, 1) if self.setup_log else 0
            }
            
            report_file = self.project_root / "setup_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.log_step("Completion Report", True, f"Bericht erstellt: {report_file}")
            return report
            
        except Exception as e:
            self.log_step("Completion Report", False, str(e))
            return None
    
    def show_final_summary(self, report):
        """Zeigt finalen Setup-Zusammenfassung"""
        print("\n🎉 STEAM PRICE TRACKER - MASTER SETUP ABGESCHLOSSEN")
        print("=" * 60)
        
        if report:
            print(f"📊 Setup-Erfolg: {report['success_rate']}%")
            print(f"✅ Erfolgreich: {report['successful_steps']}/{report['total_steps']} Schritte")
            
            if report['failed_steps'] > 0:
                print(f"❌ Fehlgeschlagen: {report['failed_steps']} Schritte")
        
        print(f"\n📁 VERFÜGBARE FEATURES:")
        for feature, available in self.features.items():
            status = "✅" if available else "❌"
            print(f"   {status} {feature.replace('_', ' ').title()}")
        
        print(f"\n🚀 NÄCHSTE SCHRITTE:")
        print(f"1. Konfiguriere deinen Steam API Key in .env:")
        print(f"   STEAM_API_KEY=dein_echter_api_key")
        print(f"")
        print(f"2. Starte die Anwendung:")
        print(f"   Windows: Doppelklick auf start.bat")
        print(f"   Linux/macOS: ./start.sh")
        print(f"   Oder: python main.py")
        print(f"")
        print(f"3. CLI-Tools verwenden:")
        if self.features['batch_processor']:
            print(f"   python batch_processor.py status")
        if self.features['charts_cli']:
            print(f"   python charts_cli_manager.py status")
        if self.features['elasticsearch']:
            print(f"   python elasticsearch_setup.py status")
        
        print(f"\n💾 BACKUP:")
        print(f"   Deine originalen Dateien sind gesichert in:")
        print(f"   {self.backup_dir}/")
        
        print(f"\n📋 DETAILLIERTER BERICHT:")
        print(f"   {self.project_root}/setup_report.json")
        
        print(f"\n💡 HILFE:")
        print(f"   Bei Problemen schaue in die Logs oder starte das Setup erneut")
        print(f"   Backup kann wiederhergestellt werden falls nötig")
    
    def run_master_setup(self):
        """Führt komplettes Master-Setup durch"""
        logger.info("🚀 STEAM PRICE TRACKER - MASTER SETUP")
        logger.info("=" * 50)
        logger.info("Startet vollständiges Setup aller Features...")
        
        setup_steps = [
            ("Master Backup erstellen", self.create_master_backup),
            ("Verzeichnisstruktur", self.setup_directory_structure),
            ("Python Dependencies", self.install_python_dependencies),
            ("Konfigurationsdateien", self.setup_configuration_files),
            ("Datenbank initialisieren", self.initialize_database),
            ("Kern-Funktionalität testen", self.test_core_functionality),
            ("Charts-Integration", self.setup_charts_integration),
            ("CLI-Tools", self.setup_cli_tools),
            ("Elasticsearch Stack", self.setup_elasticsearch_stack),
            ("Startup-Scripts", self.create_startup_scripts)
        ]
        
        logger.info(f"📋 {len(setup_steps)} Setup-Schritte geplant")
        logger.info("")
        
        # Setup-Schritte ausführen
        for step_name, step_function in setup_steps:
            logger.info(f"🔧 {step_name}...")
            try:
                success = step_function()
            except Exception as e:
                logger.error(f"❌ Kritischer Fehler in {step_name}: {e}")
                success = False
            
            if not success:
                logger.warning(f"⚠️ {step_name} nicht erfolgreich - Setup wird fortgesetzt")
        
        # Abschluss-Bericht
        report = self.create_completion_report()
        
        # Zusammenfassung anzeigen
        self.show_final_summary(report)
        
        return report

def main():
    """Hauptfunktion"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Steam Price Tracker - Master Setup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s                    - Vollständiges Master Setup
  %(prog)s --quick           - Schnelles Setup (nur Kern-Features)
  %(prog)s --elasticsearch   - Mit Elasticsearch Setup
  %(prog)s --backup-only     - Nur Backup erstellen
        """
    )
    
    parser.add_argument('--quick', action='store_true',
                       help='Schnelles Setup ohne optionale Features')
    parser.add_argument('--elasticsearch', action='store_true',
                       help='Elasticsearch Setup erzwingen')
    parser.add_argument('--backup-only', action='store_true',
                       help='Nur Backup erstellen')
    parser.add_argument('--no-backup', action='store_true',
                       help='Kein Backup erstellen')
    
    args = parser.parse_args()
    
    setup = MasterSetup()
    
    try:
        if args.backup_only:
            logger.info("💾 Erstelle nur Backup...")
            setup.create_master_backup()
            logger.info("✅ Backup abgeschlossen")
        else:
            logger.info("🚀 Starte Master Setup...")
            report = setup.run_master_setup()
            
            if report and report['success_rate'] >= 80:
                logger.info("✅ Master Setup erfolgreich abgeschlossen!")
                sys.exit(0)
            else:
                logger.warning("⚠️ Master Setup mit Problemen abgeschlossen")
                sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("\n⏹️ Master Setup abgebrochen durch Benutzer")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Kritischer Fehler im Master Setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()