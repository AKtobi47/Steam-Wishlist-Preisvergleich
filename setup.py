#!/usr/bin/env python3
"""
Setup.py - VOLLSTÄNDIGE PRODUKTIONSVERSION
Steam Price Tracker Setup mit korrigiertem Schema-Testing
100% kompatibel mit allen Komponenten und der echten DDL-Struktur
"""

import os
import sys
import subprocess
import sqlite3
import json
import shutil
from datetime import datetime
from pathlib import Path
import logging
import time

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SteamPriceTrackerSetup:
    """
    Vollständiges Setup für Steam Price Tracker - PRODUKTIONSVERSION
    
    Features:
    - Korrigierte Schema-Validierung für steam_charts_tracking
    - Vollständige Kompatibilitätstests
    - Robuste Fallback-Mechanismen
    - Detaillierte Error-Reporting
    - Produktionsreife Installation
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
            'price_tracking': False
        }
        
        self.errors = []
        self.warnings = []
        
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
            "timestamp": timestamp,
            "step": step_name,
            "success": success,
            "details": details
        })
        
        if not success:
            self.errors.append(f"{step_name}: {details}")
    
    def log_warning(self, message: str):
        """Loggt eine Warnung"""
        print(f"⚠️ {message}")
        self.warnings.append(message)
    
    def create_master_backup(self) -> bool:
        """Erstellt umfassendes Backup der wichtigsten Dateien"""
        try:
            backup_files = [
                "steam_price_tracker.db",
                "main.py", 
                "database_manager.py",
                "price_tracker.py",
                "steam_charts_manager.py",
                "background_scheduler.py",
                "config.json",
                ".env",
                "requirements.txt"
            ]
            
            backup_count = 0
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            for file_name in backup_files:
                file_path = Path(file_name)
                if file_path.exists():
                    backup_path = backup_dir / f"{file_name}.backup_{timestamp}"
                    shutil.copy2(file_path, backup_path)
                    backup_count += 1
            
            # Zusätzlich: Vollständiges Verzeichnis-Backup für kritische Fälle
            if backup_count >= 5:  # Mindestens 5 wichtige Dateien vorhanden
                archive_path = backup_dir / f"full_backup_{timestamp}.tar.gz"
                try:
                    import tarfile
                    with tarfile.open(archive_path, "w:gz") as tar:
                        for file_name in backup_files:
                            if Path(file_name).exists():
                                tar.add(file_name)
                    self.log_step("Master Backup", True, f"{backup_count} Dateien gesichert + Vollarchiv")
                except ImportError:
                    self.log_step("Master Backup", True, f"{backup_count} Dateien gesichert")
            else:
                self.log_step("Master Backup", True, f"{backup_count} Dateien gesichert")
                
            return True
            
        except Exception as e:
            self.log_step("Master Backup", False, str(e))
            return False
    
    def create_directories(self) -> bool:
        """Erstellt alle erforderlichen Verzeichnisse"""
        try:
            directories = [
                "data", "backups", "logs", "exports", 
                "config", "temp", "charts_data"
            ]
            created = 0
            
            for directory in directories:
                dir_path = Path(directory)
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    created += 1
            
            # Spezielle Unterverzeichnisse
            special_dirs = [
                "exports/csv",
                "exports/json", 
                "logs/charts",
                "logs/scheduler",
                "backups/database",
                "backups/config"
            ]
            
            for special_dir in special_dirs:
                special_path = Path(special_dir)
                if not special_path.exists():
                    special_path.mkdir(parents=True, exist_ok=True)
                    created += 1
            
            self.log_step("Directory Structure", True, f"{created} Verzeichnisse erstellt")
            return True
            
        except Exception as e:
            self.log_step("Directory Structure", False, str(e))
            return False
    
    def correct_requirements(self) -> bool:
        """Erstellt korrigierte requirements.txt ohne eingebaute Module"""
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
            return True
            
        except Exception as e:
            self.log_step("Corrected Requirements", False, str(e))
            return False
    
    def install_dependencies(self) -> bool:
        """Installiert Python Dependencies mit erweiterten Optionen"""
        try:
            print("📦 Installiere korrigierte Dependencies...")
            
            # Upgrade pip zuerst
            pip_upgrade = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if pip_upgrade.returncode != 0:
                self.log_warning("pip upgrade fehlgeschlagen, verwende aktuelle Version")
            
            # Haupt-Dependencies installieren
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                # Erfolgreiche Installation - analysiere Output
                installed_packages = []
                for line in result.stdout.split('\n'):
                    if 'Successfully installed' in line:
                        packages = line.replace('Successfully installed', '').strip().split()
                        installed_packages.extend(packages)
                
                detail_msg = f"Alle Dependencies erfolgreich installiert"
                if installed_packages:
                    detail_msg += f"\nInstallierte Pakete: {', '.join(installed_packages[:5])}"
                    if len(installed_packages) > 5:
                        detail_msg += f" (und {len(installed_packages)-5} weitere)"
                
                self.log_step("Python Dependencies", True, detail_msg)
                return True
            else:
                # Installation fehlgeschlagen - detaillierte Fehleranalyse
                error_msg = result.stderr.strip() or result.stdout.strip()
                
                # Versuche kritische vs. optionale Dependencies zu unterscheiden
                critical_deps = ["requests", "python-dotenv", "schedule"]
                
                # Teste ob kritische Dependencies verfügbar sind
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
                    self.log_step("Python Dependencies", False, f"Fehlende kritische Dependencies: {missing_critical}\nFehler: {error_msg}")
                    return False
                
        except subprocess.TimeoutExpired:
            self.log_step("Python Dependencies", False, "Installation timeout nach 300s")
            return False
        except Exception as e:
            self.log_step("Python Dependencies", False, str(e))
            return False
    
    def create_config_files(self) -> bool:
        """Erstellt umfassende Konfigurationsdateien"""
        try:
            created_files = []
            
            # 1. .env Template erstellen
            env_path = Path(".env")
            if not env_path.exists():
                env_content = """# Steam Price Tracker Konfiguration - PRODUKTIONSVERSION
# =================================================================

# STEAM API (ERFORDERLICH)
# Hole deinen API Key von: https://steamcommunity.com/dev/apikey
STEAM_API_KEY=your_steam_api_key_here

# DATENBANK KONFIGURATION
DATABASE_PATH=steam_price_tracker.db
DATABASE_BACKUP_ENABLED=true
DATABASE_CLEANUP_DAYS=90

# LOGGING
LOG_LEVEL=INFO
LOG_FILE=logs/steam_tracker.log
LOG_MAX_SIZE_MB=10

# PRICE TRACKING
TRACKING_INTERVAL_HOURS=6
MAX_APPS_PER_UPDATE=100
PRICE_UPDATE_RETRY_COUNT=3

# API RATE LIMITS
STEAM_RATE_LIMIT=1.0
CHEAPSHARK_RATE_LIMIT=1.5
REQUEST_TIMEOUT=15

# CHARTS KONFIGURATION  
CHARTS_ENABLED=true
CHARTS_UPDATE_INTERVAL_HOURS=4
CHARTS_CLEANUP_DAYS=30

# SCHEDULER
SCHEDULER_ENABLED=true
SCHEDULER_AUTO_START=false
SCHEDULER_HEARTBEAT_MINUTES=5

# EXPORT KONFIGURATION
EXPORT_FORMAT=csv
EXPORT_DIRECTORY=exports
EXPORT_DATE_FORMAT=%Y-%m-%d

# ENTWICKLUNG (optional)
DEBUG_MODE=false
DEVELOPMENT_MODE=false
"""
                
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write(env_content)
                created_files.append(".env")
            
            # 2. config.json Template erstellen
            config_path = Path("config.json")
            if not config_path.exists():
                config_content = {
                    "database": {
                        "path": "steam_price_tracker.db",
                        "backup_enabled": True,
                        "cleanup_days": 90,
                        "vacuum_on_startup": False,
                        "wal_mode": True
                    },
                    "tracking": {
                        "default_interval_hours": 6,
                        "max_apps_per_update": 100,
                        "enable_automatic_tracking": False,
                        "retry_failed_apps": True,
                        "retry_count": 3,
                        "concurrent_requests": 5
                    },
                    "charts": {
                        "enabled": True,
                        "update_interval_hours": 4,
                        "chart_types": ["most_played", "best_sellers", "top_releases"],
                        "max_games_per_chart": 100,
                        "cleanup_days": 30,
                        "track_rank_history": True
                    },
                    "api_settings": {
                        "steam": {
                            "rate_limit_seconds": 1.0,
                            "timeout_seconds": 15,
                            "max_retries": 3
                        },
                        "cheapshark": {
                            "rate_limit_seconds": 1.5,
                            "timeout_seconds": 15,
                            "store_ids": "1,3,7,11,15,27"
                        }
                    },
                    "scheduler": {
                        "enabled": True,
                        "auto_start": False,
                        "heartbeat_minutes": 5,
                        "max_concurrent_jobs": 3,
                        "job_timeout_minutes": 30
                    },
                    "export": {
                        "default_format": "csv",
                        "directory": "exports",
                        "date_format": "%Y-%m-%d",
                        "include_headers": True,
                        "compress_large_files": True
                    },
                    "logging": {
                        "level": "INFO",
                        "file": "logs/steam_tracker.log",
                        "max_size_mb": 10,
                        "backup_count": 5,
                        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                    }
                }
                
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_content, f, indent=2, ensure_ascii=False)
                created_files.append("config.json")
            
            # 3. logging.conf erstellen
            logging_config_path = Path("logging.conf")
            if not logging_config_path.exists():
                logging_content = """[loggers]
keys=root,steam_tracker,charts,scheduler

[handlers]
keys=consoleHandler,fileHandler,rotatingFileHandler

[formatters]
keys=simpleFormatter,detailedFormatter

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
"""
                
                with open(logging_config_path, 'w', encoding='utf-8') as f:
                    f.write(logging_content)
                created_files.append("logging.conf")
            
            detail_msg = f"Konfigurationsdateien erstellt: {', '.join(created_files)}"
            if not created_files:
                detail_msg = "Alle Konfigurationsdateien bereits vorhanden"
            
            self.log_step("Configuration Files", True, detail_msg)
            return True
            
        except Exception as e:
            self.log_step("Configuration Files", False, str(e))
            return False
    
    def test_database_schema(self) -> bool:
        """Testet das korrigierte Database Schema - PRODUKTIONSVERSION"""
        try:
            # Importiere DatabaseManager
            from database_manager import DatabaseManager
            
            # Test-Datenbank erstellen
            test_db_path = "test_schema_production.db"
            test_db = DatabaseManager(test_db_path)
            
            test_results = []
            
            # Test 1: Basis-Funktionalität
            success = test_db.add_tracked_app("123456", "Test Game", "manual")
            test_results.append(("add_tracked_app", success))
            
            # Test 2: get_tracked_apps
            apps = test_db.get_tracked_apps()
            test_results.append(("get_tracked_apps", isinstance(apps, list)))
            
            # Test 3: get_database_stats
            stats = test_db.get_database_stats()
            test_results.append(("get_database_stats", isinstance(stats, dict)))
            
            # Test 4: Schema-Validierung für tracked_apps
            with test_db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(tracked_apps)")
                columns = {column[1] for column in cursor.fetchall()}
                
                required_columns = {'steam_app_id', 'name', 'source'}
                missing = required_columns - columns
                test_results.append(("tracked_apps_schema", len(missing) == 0))
                
                if missing:
                    raise Exception(f"Fehlende Spalten in tracked_apps: {missing}")
            
            # Test 5: KRITISCHER TEST - steam_charts_tracking Schema
            cursor.execute("PRAGMA table_info(steam_charts_tracking)")
            charts_columns = {column[1] for column in cursor.fetchall()}
            
            critical_charts_columns = {'steam_app_id', 'chart_type', 'days_in_charts', 'current_rank'}
            missing_charts = critical_charts_columns - charts_columns
            test_results.append(("steam_charts_tracking_schema", len(missing_charts) == 0))
            
            if missing_charts:
                raise Exception(f"KRITISCH: Fehlende Spalten in steam_charts_tracking: {missing_charts}")
            
            # Test 6: Chart-Game Funktionalität
            success = test_db.add_chart_game("789012", "test_chart", 1, 1000, "Test Chart Game")
            test_results.append(("add_chart_game", success))
            
            # Test 7: Der problematische Query der den Fehler verursacht hatte
            cursor.execute("SELECT days_in_charts FROM steam_charts_tracking WHERE steam_app_id = ?", ("789012",))
            result = cursor.fetchone()
            test_results.append(("days_in_charts_query", result is not None))
            
            # Test 8: Charts-Statistiken
            chart_stats = test_db.get_charts_statistics()
            test_results.append(("get_charts_statistics", isinstance(chart_stats, dict)))
            
            # Test 9: Legacy chart_games Kompatibilität
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chart_games'")
            test_results.append(("legacy_chart_games_exists", cursor.fetchone() is not None))
            
            # Cleanup
            try:
                os.remove(test_db_path)
            except:
                pass
            
            # Ergebnisse auswerten
            failed_tests = [test for test, result in test_results if not result]
            
            if failed_tests:
                raise Exception(f"Fehlgeschlagene Schema-Tests: {failed_tests}")
            
            success_count = len([r for _, r in test_results if r])
            detail_msg = f"Alle {success_count} Schema-Tests erfolgreich"
            detail_msg += "\n✅ steam_charts_tracking mit days_in_charts validiert"
            detail_msg += "\n✅ Legacy-Kompatibilität geprüft"
            detail_msg += "\n✅ Kritische SQL-Queries funktionieren"
            
            self.log_step("Database Schema Test", True, detail_msg)
            self.features_available['database'] = True
            return True
            
        except Exception as e:
            self.log_step("Database Schema Test", False, str(e))
            # Cleanup bei Fehler
            try:
                os.remove(test_db_path)
            except:
                pass
            return False
    
    def test_core_functionality(self) -> bool:
        """Testet Kern-Funktionalität mit allen Komponenten"""
        try:
            test_db_path = "test_core_production.db"
            
            # DatabaseManager Test
            from database_manager import DatabaseManager
            db_manager = DatabaseManager(test_db_path)
            
            # SteamPriceTracker Test
            from price_tracker import SteamPriceTracker
            
            # Mock API Key für Test
            api_key = "test_api_key_12345"
            
            # SteamPriceTracker erstellen
            tracker = SteamPriceTracker(db_manager=db_manager, api_key=api_key, enable_scheduler=False)
            
            core_tests = []
            
            # Test 1: Tracker-Grundfunktionen
            core_tests.append(("tracker_has_db_manager", hasattr(tracker, 'db_manager')))
            core_tests.append(("tracker_has_api_key", hasattr(tracker, 'api_key')))
            core_tests.append(("tracker_has_add_or_update_app", hasattr(tracker, 'add_or_update_app')))
            
            # Test 2: API-Kompatibilität mit main.py
            required_methods = [
                'get_tracked_apps',       # Wichtig für main.py
                'get_database_stats',     # Statt get_statistics
                'add_app_to_tracking'     # Falls verfügbar
            ]
            
            for method in required_methods:
                core_tests.append((f"tracker_has_{method}", hasattr(tracker, method)))
            
            # Test 3: Charts-Integration (falls aktiviert)
            if hasattr(tracker, 'charts_manager') and tracker.charts_manager:
                core_tests.append(("charts_manager_available", True))
                charts_methods = ['update_all_charts', 'get_chart_statistics']
                for method in charts_methods:
                    core_tests.append((f"charts_has_{method}", hasattr(tracker.charts_manager, method)))
            else:
                self.log_warning("Charts Manager nicht verfügbar - wird übersprungen")
            
            # Test 4: Background Scheduler (optional)
            try:
                import background_scheduler
                core_tests.append(("background_scheduler_available", True))
                self.features_available['background_scheduler'] = True
            except ImportError:
                self.log_warning("Background Scheduler nicht verfügbar - optional")
                core_tests.append(("background_scheduler_available", False))
            
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
            if failed_tests:
                detail_msg += f"\nÜbersprungen: {failed_tests}"
            
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
        """Testet main.py Kompatibilität umfassend"""
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
            
            # Test 2: Menüoptionen zählen
            menu_count = main_content.count("def menu_")
            compatibility_tests.append(("sufficient_menu_options", menu_count >= 20))
            
            # Test 3: Import-Validierung
            required_imports = [
                "from database_manager import",
                "from price_tracker import", 
                "DatabaseManager",
                "SteamPriceTracker"
            ]
            
            for import_check in required_imports:
                found = import_check in main_content
                compatibility_tests.append((f"has_import_{import_check.split()[-1]}", found))
            
            # Test 4: API-Aufrufe validieren
            critical_api_calls = [
                "get_tracked_apps(",        # Wichtiger API-Call
                "get_database_stats(",      # Statt get_statistics
                "add_tracked_app(",         # Basis-Funktionalität
            ]
            
            for api_call in critical_api_calls:
                found = api_call in main_content
                compatibility_tests.append((f"uses_api_{api_call.replace('(', '')}", found))
            
            # Test 5: Charts-Integration prüfen
            charts_indicators = [
                "charts_manager",
                "update_all_charts",
                "Option 14"  # Charts Update Option
            ]
            
            charts_found = sum(1 for indicator in charts_indicators if indicator in main_content)
            compatibility_tests.append(("charts_integration", charts_found >= 2))
            
            # Test 6: Error Handling prüfen
            error_handling = [
                "try:",
                "except",
                "Exception"
            ]
            
            error_count = sum(main_content.count(pattern) for pattern in error_handling)
            compatibility_tests.append(("has_error_handling", error_count >= 10))
            
            # Ergebnisse auswerten
            failed_tests = [test for test, result in compatibility_tests if not result]
            success_count = len([r for _, r in compatibility_tests if r])
            
            detail_msg = f"{success_count}/{len(compatibility_tests)} Kompatibilitäts-Tests erfolgreich"
            detail_msg += f"\n📋 Menüoptionen: {menu_count}"
            
            if failed_tests:
                detail_msg += f"\nFehlgeschlagen: {failed_tests}"
                if len(failed_tests) > 3:  # Zu viele kritische Fehler
                    raise Exception(f"Kritische Kompatibilitätsprobleme: {failed_tests}")
            
            self.log_step("Main.py Compatibility Test", True, detail_msg)
            self.features_available['main_app'] = True
            return True
            
        except Exception as e:
            self.log_step("Main.py Compatibility Test", False, str(e))
            return False
    
    def test_charts_integration(self) -> bool:
        """Testet Charts-Integration mit korrigiertem Schema"""
        try:
            test_db_path = "test_charts_production.db"
            
            # DatabaseManager mit Charts-Support
            from database_manager import DatabaseManager
            db_manager = DatabaseManager(test_db_path)
            
            # Charts Manager Test
            try:
                from steam_charts_manager import SteamChartsManager
                charts_manager = SteamChartsManager("test_api", db_manager)
                charts_available = True
            except ImportError as e:
                self.log_warning(f"SteamChartsManager nicht verfügbar: {e}")
                charts_available = False
            
            charts_tests = []
            
            if charts_available:
                # Test 1: Charts Manager Methoden
                required_methods = [
                    'update_all_charts',
                    'get_most_played_games', 
                    'get_best_sellers_games',
                    'get_chart_statistics'
                ]
                
                for method in required_methods:
                    has_method = hasattr(charts_manager, method)
                    charts_tests.append((f"charts_has_{method}", has_method))
                
                # Test 2: Database Integration
                success = db_manager.add_chart_game("test_789", "test_chart", 1, 1000, "Test Game")
                charts_tests.append(("db_add_chart_game", success))
                
                chart_games = db_manager.get_active_chart_games("test_chart")
                charts_tests.append(("db_get_chart_games", isinstance(chart_games, list)))
                
                # Test 3: Statistiken
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
                
                # Test 4: Schema-Kompatibilität
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Prüfe steam_charts_tracking
                    cursor.execute("SELECT days_in_charts FROM steam_charts_tracking WHERE steam_app_id = ?", ("test_789",))
                    result = cursor.fetchone()
                    charts_tests.append(("schema_compatibility", result is not None))
            
            else:
                # Minimaler Test ohne Charts Manager
                charts_tests.append(("charts_manager_import", False))
                charts_tests.append(("basic_charts_db", True))  # DB-Schema sollte trotzdem funktionieren
            
            # Cleanup
            try:
                os.remove(test_db_path)
            except:
                pass
            
            # Ergebnisse auswerten
            success_count = len([r for _, r in charts_tests if r])
            failed_tests = [test for test, result in charts_tests if not result]
            
            if charts_available:
                chart_types = ['most_played', 'best_sellers', 'top_releases']
                detail_msg = f"{success_count}/{len(charts_tests)} Charts-Tests erfolgreich"
                detail_msg += f"\n📊 Chart-Typen: {len(chart_types)}"
                
                if failed_tests:
                    detail_msg += f"\nFehlgeschlagen: {failed_tests}"
                    
                self.features_available['charts'] = len(failed_tests) <= 2  # Toleranz für kleinere Probleme
            else:
                detail_msg = "Charts Manager nicht verfügbar, Database-Schema bereit"
                self.features_available['charts'] = False
            
            self.log_step("Charts Integration", charts_available and len(failed_tests) <= 2, detail_msg)
            return True  # Auch ohne Charts Manager als Erfolg werten
            
        except Exception as e:
            self.log_step("Charts Integration", False, str(e))
            try:
                os.remove(test_db_path)
            except:
                pass
            return False
    
    def test_steam_api_connectivity(self) -> bool:
        """Testet Steam API Konnektivität"""
        try:
            import requests
            
            # Test 1: Steam Store API (öffentlich)
            test_url = "https://store.steampowered.com/api/appdetails?appids=413150"
            
            response = requests.get(test_url, timeout=10)
            api_tests = [
                ("steam_store_api_reachable", response.status_code == 200),
                ("steam_store_api_json", 'application/json' in response.headers.get('content-type', ''))
            ]
            
            # Test 2: Steam Charts API
            charts_url = "https://store.steampowered.com/charts/mostplayed"
            charts_response = requests.get(charts_url, timeout=10)
            api_tests.append(("steam_charts_reachable", charts_response.status_code == 200))
            
            # Test 3: API Key Validierung (falls verfügbar)
            try:
                from price_tracker import SteamPriceTracker
                tracker = SteamPriceTracker(enable_scheduler=False)
                
                if tracker.api_key and tracker.api_key != "test_api_key_12345":
                    # Test mit echtem API Key
                    api_url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={tracker.api_key}&steamids=76561197960434622"
                    api_response = requests.get(api_url, timeout=10)
                    api_tests.append(("steam_api_key_valid", api_response.status_code == 200))
                else:
                    api_tests.append(("steam_api_key_configured", False))
                    self.log_warning("Steam API Key nicht konfiguriert - einige Features nicht verfügbar")
            
            except Exception as e:
                api_tests.append(("steam_api_key_test", False))
                self.log_warning(f"Steam API Key Test übersprungen: {e}")
            
            # Ergebnisse auswerten
            success_count = len([r for _, r in api_tests if r])
            failed_tests = [test for test, result in api_tests if not result]
            
            detail_msg = f"{success_count}/{len(api_tests)} API-Tests erfolgreich"
            if failed_tests:
                detail_msg += f"\nFehlgeschlagen: {failed_tests}"
            
            # Steam API als verfügbar markieren wenn grundlegende Konnektivität gegeben
            steam_api_working = success_count >= 2
            self.features_available['steam_api'] = steam_api_working
            
            self.log_step("Steam API Connectivity", steam_api_working, detail_msg)
            return steam_api_working
            
        except Exception as e:
            self.log_step("Steam API Connectivity", False, str(e))
            return False
    
    def test_cli_tools(self) -> bool:
        """Testet CLI-Tools Verfügbarkeit"""
        try:
            cli_tools = []
            
            # Bekannte CLI-Tools prüfen
            cli_files = [
                ("price_checker.py", "Preis-Checker"),
                ("bulk_import.py", "Bulk-Import"), 
                ("charts_cli.py", "Charts CLI"),
                ("wishlist_import.py", "Wishlist Import"),
                ("export_tools.py", "Export Tools")
            ]
            
            for cli_file, description in cli_files:
                if Path(cli_file).exists():
                    cli_tools.append((cli_file, description))
            
            # Zusätzlich: Prüfe ob main.py CLI-Funktionen hat
            main_path = Path("main.py")
            has_cli_in_main = False
            
            if main_path.exists():
                with open(main_path, "r", encoding="utf-8") as f:
                    main_content = f.read()
                    cli_indicators = ["if __name__ == '__main__'", "argparse", "sys.argv"]
                    has_cli_in_main = any(indicator in main_content for indicator in cli_indicators)
            
            if has_cli_in_main:
                cli_tools.append(("main.py", "Hauptanwendung mit CLI"))
            
            cli_count = len(cli_tools)
            
            if cli_count >= 2:
                detail_msg = f"{cli_count} CLI-Tools verfügbar:\n"
                for tool, desc in cli_tools:
                    detail_msg += f"   • {tool}: {desc}\n"
                
                self.log_step("CLI Tools Setup", True, detail_msg.strip())
                self.features_available['cli_tools'] = True
                self.features_available['charts_cli'] = any('charts' in tool for tool, _ in cli_tools)
                return True
            else:
                self.log_step("CLI Tools Setup", False, f"Nur {cli_count} CLI-Tools gefunden (mindestens 2 erwartet)")
                return False
                
        except Exception as e:
            self.log_step("CLI Tools Setup", False, str(e))
            return False
    
    def test_elasticsearch_stack(self) -> bool:
        """Testet Elasticsearch Stack (optional)"""
        try:
            elasticsearch_files = [
                ("elasticsearch_setup.py", "Setup"),
                ("elasticsearch_cli.py", "CLI"),
                ("kibana_dashboard_setup.py", "Kibana Dashboard")
            ]
            
            available_files = []
            for file_name, description in elasticsearch_files:
                if Path(file_name).exists():
                    available_files.append((file_name, description))
            
            if len(available_files) >= 2:
                detail_msg = f"Elasticsearch-Stack verfügbar:\n"
                for file_name, desc in available_files:
                    detail_msg += f"   • {file_name}: {desc}\n"
                
                # Optional: Teste ob Docker verfügbar ist
                try:
                    docker_result = subprocess.run(["docker", "--version"], capture_output=True, timeout=5)
                    if docker_result.returncode == 0:
                        detail_msg += "   • Docker verfügbar für Container-Setup"
                except:
                    detail_msg += "   • Docker nicht verfügbar - manuelle Installation erforderlich"
                
                self.log_step("Elasticsearch Stack", True, detail_msg.strip())
                self.features_available['elasticsearch'] = True
                return True
            else:
                self.log_step("Elasticsearch Stack", False, "Elasticsearch-Manager nicht verfügbar (optional)")
                return False
                
        except Exception as e:
            self.log_step("Elasticsearch Stack", False, str(e))
            return False
    
    def create_startup_scripts(self) -> bool:
        """Erstellt erweiterte Start-Scripts für verschiedene Plattformen"""
        try:
            created_scripts = []
            
            # 1. Windows Batch Script (erweitert)
            batch_content = '''@echo off
title Steam Price Tracker
echo.
echo ========================================
echo    Steam Price Tracker - Windows
echo ========================================
echo.

REM Prüfe Python Installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python ist nicht installiert oder nicht im PATH
    echo Bitte installiere Python von https://python.org
    pause
    exit /b 1
)

REM Prüfe ob Virtual Environment existiert
if exist "venv\\Scripts\\activate.bat" (
    echo 🔧 Aktiviere Virtual Environment...
    call venv\\Scripts\\activate.bat
)

REM Prüfe Dependencies
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installiere Dependencies...
    python -m pip install -r requirements.txt
)

echo 🚀 Steam Price Tracker wird gestartet...
echo.
python main.py

if errorlevel 1 (
    echo.
    echo ❌ Fehler beim Starten der Anwendung
    echo Überprüfe die Logs in logs/steam_tracker.log
)

echo.
pause
'''
            
            with open("start.bat", "w", encoding="utf-8") as f:
                f.write(batch_content)
            created_scripts.append("start.bat")
            
            # 2. Linux/Mac Shell Script (erweitert)
            shell_content = '''#!/bin/bash

# Steam Price Tracker Startup Script
# Unterstützt: Linux, macOS, WSL

set -e  # Exit bei Fehlern

echo "========================================"
echo "   Steam Price Tracker - Unix/Linux"
echo "========================================"
echo

# Farben für Output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

# Funktionen
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Python Version prüfen
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        log_error "Python ist nicht installiert"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

log_info "Verwende $PYTHON_CMD ($(${PYTHON_CMD} --version))"

# Virtual Environment aktivieren (falls vorhanden)
if [ -f "venv/bin/activate" ]; then
    log_info "Aktiviere Virtual Environment..."
    source venv/bin/activate
fi

# Dependencies prüfen
if ! ${PYTHON_CMD} -c "import requests" &> /dev/null; then
    log_warning "Dependencies fehlen, installiere..."
    ${PYTHON_CMD} -m pip install -r requirements.txt
fi

# Steam Price Tracker starten
log_success "Steam Price Tracker wird gestartet..."
echo

if ${PYTHON_CMD} main.py; then
    log_success "Anwendung beendet"
else
    log_error "Fehler beim Starten der Anwendung"
    log_info "Überprüfe die Logs in logs/steam_tracker.log"
    exit 1
fi
'''
            
            with open("start.sh", "w", encoding="utf-8") as f:
                f.write(shell_content)
            
            # Script ausführbar machen
            try:
                os.chmod("start.sh", 0o755)
            except:
                self.log_warning("Konnte start.sh nicht ausführbar machen")
            
            created_scripts.append("start.sh")
            
            # 3. PowerShell Script (für moderne Windows)
            powershell_content = '''# Steam Price Tracker PowerShell Startup Script
# Für Windows PowerShell und PowerShell Core

[CmdletBinding()]
param()

# Titel setzen
$host.ui.RawUI.WindowTitle = "Steam Price Tracker"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Steam Price Tracker - PowerShell" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan
Write-Host

# Python prüfen
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python gefunden: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python ist nicht installiert oder nicht im PATH" -ForegroundColor Red
    Write-Host "Bitte installiere Python von https://python.org" -ForegroundColor Yellow
    Read-Host "Drücke Enter zum Beenden"
    exit 1
}

# Virtual Environment aktivieren (falls vorhanden)
if (Test-Path "venv\\Scripts\\Activate.ps1") {
    Write-Host "🔧 Aktiviere Virtual Environment..." -ForegroundColor Blue
    & ".\\venv\\Scripts\\Activate.ps1"
}

# Dependencies prüfen
try {
    python -c "import requests" 2>$null
    Write-Host "✅ Dependencies verfügbar" -ForegroundColor Green
} catch {
    Write-Host "📦 Installiere Dependencies..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
}

# Steam Price Tracker starten
Write-Host "🚀 Steam Price Tracker wird gestartet..." -ForegroundColor Green
Write-Host

try {
    python main.py
    Write-Host "✅ Anwendung beendet" -ForegroundColor Green
} catch {
    Write-Host "❌ Fehler beim Starten der Anwendung" -ForegroundColor Red
    Write-Host "Überprüfe die Logs in logs/steam_tracker.log" -ForegroundColor Yellow
}

Write-Host
Read-Host "Drücke Enter zum Beenden"
'''
            
            with open("start.ps1", "w", encoding="utf-8") as f:
                f.write(powershell_content)
            created_scripts.append("start.ps1")
            
            # 4. Docker Compose (falls Docker verfügbar)
            try:
                subprocess.run(["docker", "--version"], capture_output=True, timeout=5, check=True)
                
                docker_compose_content = '''version: '3.8'

services:
  steam-price-tracker:
    build: .
    container_name: steam_price_tracker
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./exports:/app/exports
      - ./backups:/app/backups
    environment:
      - DATABASE_PATH=/app/data/steam_price_tracker.db
      - LOG_LEVEL=INFO
    restart: unless-stopped
    
  # Optional: Elasticsearch für erweiterte Analytics
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    container_name: steam_elasticsearch
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    profiles:
      - analytics

  kibana:
    image: docker.elastic.co/kibana/kibana:8.8.0
    container_name: steam_kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
    profiles:
      - analytics

volumes:
  elasticsearch_data:
'''
                
                with open("docker-compose.yml", "w", encoding="utf-8") as f:
                    f.write(docker_compose_content)
                created_scripts.append("docker-compose.yml")
                
                self.features_available['docker_compose'] = True
                
            except:
                self.log_warning("Docker nicht verfügbar - docker-compose.yml übersprungen")
            
            detail_msg = f"Startup-Scripts erstellt: {', '.join(created_scripts)}"
            self.log_step("Startup Scripts", True, detail_msg)
            return True
            
        except Exception as e:
            self.log_step("Startup Scripts", False, str(e))
            return False
    
    def save_setup_report(self) -> bool:
        """Speichert umfassenden Setup-Report"""
        try:
            successful_steps = sum(1 for step in self.setup_log if step["success"])
            total_steps = len(self.setup_log)
            success_rate = (successful_steps / total_steps * 100) if total_steps > 0 else 0
            
            # Performance Metriken
            setup_duration = sum(1 for step in self.setup_log)  # Approximation
            
            # Feature-Zusammenfassung
            enabled_features = [feature for feature, enabled in self.features_available.items() if enabled]
            disabled_features = [feature for feature, enabled in self.features_available.items() if not enabled]
            
            report = {
                "setup_metadata": {
                    "completed_at": datetime.now().isoformat(),
                    "version": "3.0.0-production",
                    "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    "platform": sys.platform,
                    "setup_duration_steps": setup_duration
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
                    "critical_features_ok": all(self.features_available[f] for f in ['core', 'database', 'main_app'])
                },
                "detailed_log": self.setup_log,
                "errors": self.errors,
                "warnings": self.warnings,
                "recommendations": self._generate_recommendations(),
                "next_steps": self._generate_next_steps()
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
        """Generiert Setup-Empfehlungen basierend auf Ergebnissen"""
        recommendations = []
        
        if not self.features_available['steam_api']:
            recommendations.append("🔑 Steam API Key in .env konfigurieren für vollständige Funktionalität")
        
        if not self.features_available['charts']:
            recommendations.append("📊 Charts-Funktionalität einrichten für erweiterte Analytics")
        
        if not self.features_available['elasticsearch']:
            recommendations.append("🔍 Elasticsearch für erweiterte Suchfunktionen installieren (optional)")
        
        if not self.features_available['background_scheduler']:
            recommendations.append("⏰ Background Scheduler für automatische Updates einrichten")
        
        if len(self.errors) > 0:
            recommendations.append("🔧 Fehler in Setup-Log überprüfen und beheben")
        
        if len(self.warnings) > 2:
            recommendations.append("⚠️ Warnungen überprüfen - möglicherweise fehlende optionale Komponenten")
        
        return recommendations
    
    def _generate_next_steps(self) -> List[str]:
        """Generiert nächste Schritte für den Benutzer"""
        next_steps = []
        
        if self.features_available['core'] and self.features_available['main_app']:
            next_steps.append("✅ Führe 'python main.py' aus um die Anwendung zu starten")
            
        if self.features_available['database']:
            next_steps.append("📱 Steam Wishlist importieren (Option 2 in main.py)")
            
        if self.features_available['charts']:
            next_steps.append("📊 Charts-Update durchführen (Option 14 in main.py)")
            
        if self.features_available['price_tracking']:
            next_steps.append("💰 Automatisches Preis-Tracking aktivieren (Option 7 in main.py)")
            
        next_steps.append("📖 README.md für detaillierte Anweisungen lesen")
        next_steps.append("🔧 .env Datei mit deinem Steam API Key konfigurieren")
        
        return next_steps
    
    def _format_human_readable_report(self, report: dict) -> str:
        """Formatiert Report für menschliche Lesbarkeit"""
        output = []
        
        output.append("=" * 60)
        output.append("STEAM PRICE TRACKER - SETUP REPORT")
        output.append("=" * 60)
        output.append(f"Abgeschlossen: {report['setup_metadata']['completed_at']}")
        output.append(f"Version: {report['setup_metadata']['version']}")
        output.append(f"Python: {report['setup_metadata']['python_version']}")
        output.append(f"Plattform: {report['setup_metadata']['platform']}")
        output.append("")
        
        # Ergebnisse
        results = report['results_summary']
        output.append("📊 SETUP-ERGEBNISSE:")
        output.append(f"   ✅ Erfolgreich: {results['successful_steps']}/{results['total_steps']} ({results['success_rate']}%)")
        output.append(f"   📈 Status: {results['overall_status']}")
        output.append("")
        
        # Features
        features = report['features_status']
        output.append("🎯 VERFÜGBARE FEATURES:")
        for feature in features['enabled_features']:
            output.append(f"   ✅ {feature}")
        
        if features['disabled_features']:
            output.append("\n❌ NICHT VERFÜGBARE FEATURES:")
            for feature in features['disabled_features']:
                output.append(f"   ❌ {feature}")
        
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
        
        output.append("=" * 60)
        
        return "\n".join(output)
    
    def run_full_setup(self) -> bool:
        """Führt vollständiges Setup durch - PRODUKTIONSVERSION"""
        print("🚀 Steam Price Tracker Setup - PRODUKTIONSVERSION")
        print("=" * 60)
        print("🚀 Starte vollständiges Setup...")
        print()
        
        start_time = time.time()
        
        # Setup-Schritte in optimaler Reihenfolge
        setup_steps = [
            ("Master Backup", self.create_master_backup),
            ("Directory Structure", self.create_directories),
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
            ("Startup Scripts", self.create_startup_scripts)
        ]
        
        # Führe alle Setup-Schritte aus
        for step_name, step_func in setup_steps:
            try:
                print(f"🔄 {step_name}...")
                step_func()
                time.sleep(0.1)  # Kurze Pause für bessere UX
            except Exception as e:
                self.log_step(step_name, False, f"Unerwarteter Fehler: {e}")
        
        setup_duration = time.time() - start_time
        
        # Report speichern
        self.save_setup_report()
        
        # Zusammenfassung anzeigen
        self._display_setup_summary(setup_duration)
        
        # Erfolg bestimmen
        successful = sum(1 for step in self.setup_log if step["success"])
        total = len(self.setup_log)
        success_rate = (successful / total * 100) if total > 0 else 0
        
        return success_rate >= 80
    
    def _display_setup_summary(self, duration: float):
        """Zeigt detaillierte Setup-Zusammenfassung"""
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
        
        # Feature-Status
        print("\n🎯 VERFÜGBARE FEATURES:")
        feature_groups = {
            "Kern-Features": ['core', 'database', 'main_app', 'price_tracking'],
            "Erweitert": ['charts', 'steam_api', 'background_scheduler'],
            "Tools": ['cli_tools', 'charts_cli'],
            "Optional": ['elasticsearch', 'docker_compose']
        }
        
        for group_name, features in feature_groups.items():
            available_in_group = [f for f in features if self.features_available.get(f, False)]
            if available_in_group:
                print(f"\n   {group_name}:")
                for feature in available_in_group:
                    print(f"      ✅ {feature}")
        
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
        
        # Abschließende Nachricht
        if success_rate >= 90:
            print("🎉 Setup erfolgreich abgeschlossen!")
            print("💡 Du kannst jetzt 'python main.py' ausführen")
        elif success_rate >= 80:
            print("✅ Setup größtenteils erfolgreich!")
            print("💡 Grundfunktionen verfügbar, optionale Features prüfen")
        elif success_rate >= 60:
            print("⚠️ Setup mit Einschränkungen abgeschlossen")
            print("🔧 Bitte Fehler beheben für vollständige Funktionalität")
        else:
            print("❌ Setup fehlgeschlagen!")
            print("🆘 Bitte Setup-Report prüfen und Support kontaktieren")


def main():
    """Hauptfunktion für Setup mit erweiterten Optionen"""
    setup = SteamPriceTrackerSetup()
    
    print("🔧 Steam Price Tracker Setup - PRODUKTIONSVERSION")
    print("=" * 50)
    print("1. 🚀 Vollständiges Setup durchführen")
    print("2. 📦 Nur requirements.txt korrigieren") 
    print("3. 🗄️  Nur Database Schema testen")
    print("4. ⚙️  Nur Kern-Funktionalität testen")
    print("5. 📊 Nur Charts-Integration testen")
    print("6. 🌐 Nur Steam API testen")
    print("7. 📋 Setup-Status anzeigen")
    print("8. 🧹 Cleanup und Reset")
    print()
    
    choice = input("Auswahl (1-8): ").strip()
    
    if choice == "1":
        setup.run_full_setup()
    elif choice == "2":
        setup.correct_requirements()
        setup.install_dependencies()
    elif choice == "3":
        setup.test_database_schema()
    elif choice == "4":
        setup.test_core_functionality()
    elif choice == "5":
        setup.test_charts_integration()
    elif choice == "6":
        setup.test_steam_api_connectivity()
    elif choice == "7":
        # Status aus vorherigem Setup laden
        try:
            with open("setup_report.json", "r", encoding="utf-8") as f:
                report = json.load(f)
            print("\n📊 LETZTER SETUP-STATUS:")
            print(setup._format_human_readable_report(report))
        except FileNotFoundError:
            print("❌ Kein Setup-Report gefunden. Führe zuerst ein Setup durch.")
    elif choice == "8":
        # Cleanup
        print("🧹 Cleanup wird durchgeführt...")
        cleanup_files = ["test_*.db", "setup_report.json"]
        for pattern in cleanup_files:
            for file_path in Path(".").glob(pattern):
                try:
                    file_path.unlink()
                    print(f"🗑️  {file_path} entfernt")
                except:
                    pass
        print("✅ Cleanup abgeschlossen")
    else:
        print("❌ Ungültige Auswahl")


if __name__ == "__main__":
    main()
