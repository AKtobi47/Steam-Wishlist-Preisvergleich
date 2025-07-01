#!/usr/bin/env python3
"""
Enhanced Logging System für Steam Price Tracker
- Lädt .env Datei korrekt
- Separate Log-Dateien pro Modul  
- Strukturiertes Logging
- Volle Kontrolle über alle Einstellungen
"""

import logging
import logging.handlers
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

class EnhancedLoggingSystem:
    """
    Zentrales Logging-System mit .env Support und separaten Dateien
    """
    
    def __init__(self):
        self.config = {}
        self.loggers = {}
        self.load_env_config()
    
    def load_env_config(self):
        """Lädt .env Datei manuell (ohne python-dotenv Abhängigkeit)"""
        env_file = Path(".env")
        
        if env_file.exists():
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            # Entferne Anführungszeichen falls vorhanden
                            if value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                            elif value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            
                            os.environ[key] = value
                
                print(f"✅ .env Datei geladen: {env_file}")
                
                # Debug: Geladene Logging-Variablen anzeigen
                logging_vars = ['LOG_LEVEL', 'LOG_FILE', 'LOG_TO_CONSOLE', 'LOG_ROTATION', 'LOG_STRUCTURED']
                for var in logging_vars:
                    value = os.getenv(var, 'NICHT_GEFUNDEN')
                    print(f"   {var}={value}")
                    
            except Exception as e:
                print(f"⚠️ Fehler beim Laden der .env: {e}")
        else:
            print(f"⚠️ .env Datei nicht gefunden: {env_file}")
        
        # Konfiguration aus Umgebungsvariablen laden
        self.config = {
            'log_level': os.getenv('LOG_LEVEL', 'INFO').upper(),
            'log_directory': os.getenv('LOG_FILE', 'logs/').rstrip('/'),  # Verzeichnis
            'log_rotation': os.getenv('LOG_ROTATION', 'true').lower() == 'true',
            'log_max_size': int(os.getenv('LOG_MAX_SIZE', '15')),
            'log_backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5')),
            'log_to_console': os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true',
            'log_structured': os.getenv('LOG_STRUCTURED', 'false').lower() == 'true'
        }
        
        print(f"🔧 Logging-Konfiguration geladen:")
        for key, value in self.config.items():
            print(f"   {key}: {value}")
    
    def get_logger(self, module_name: str, log_filename: str = None) -> logging.Logger:
        """
        Erstellt/holt Logger für spezifisches Modul mit separater Log-Datei
        
        Args:
            module_name: Name des Moduls (z.B. "steam_charts", "database", "main")
            log_filename: Optionaler Dateiname (Standard: {module_name}.log)
            
        Returns:
            Konfigurierter Logger
        """
        
        # Bereits existierenden Logger zurückgeben
        if module_name in self.loggers:
            return self.loggers[module_name]
        
        # Dateiname bestimmen
        if not log_filename:
            log_filename = f"{module_name}.log"
        
        # Vollständiger Pfad
        log_directory = Path(self.config['log_directory'])
        log_file = log_directory / log_filename
        
        # Verzeichnis erstellen
        log_directory.mkdir(parents=True, exist_ok=True)
        
        # Logger erstellen
        logger = logging.getLogger(module_name)
        logger.setLevel(getattr(logging, self.config['log_level']))
        
        # Bestehende Handler entfernen
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Formatter je nach Modus
        if self.config['log_structured']:
            formatter = StructuredFormatter(module_name)
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        handlers_added = 0
        
        # Console Handler (falls aktiviert)
        if self.config['log_to_console']:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, self.config['log_level']))
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            handlers_added += 1
        
        # File Handler
        try:
            if self.config['log_rotation']:
                file_handler = logging.handlers.RotatingFileHandler(
                    str(log_file),
                    maxBytes=self.config['log_max_size'] * 1024 * 1024,
                    backupCount=self.config['log_backup_count'],
                    encoding='utf-8'
                )
            else:
                file_handler = logging.FileHandler(str(log_file), encoding='utf-8')
            
            file_handler.setLevel(logging.DEBUG)  # File bekommt immer alle Level
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            handlers_added += 1
            
            print(f"✅ Logger '{module_name}': {log_file} ({handlers_added} Handler)")
            
        except Exception as e:
            print(f"❌ File Handler Fehler für {module_name}: {e}")
        
        # Propagation verhindern
        logger.propagate = False
        
        # Logger cachen
        self.loggers[module_name] = logger
        
        # Test-Nachricht
        logger.info(f"🚀 Logger '{module_name}' initialisiert - Level: {self.config['log_level']}")
        
        return logger

class StructuredFormatter(logging.Formatter):
    """
    Strukturierter JSON-Formatter für bessere Log-Analyse
    """
    
    def __init__(self, module_name: str):
        super().__init__()
        self.module_name = module_name
    
    def format(self, record):
        """Formatiert Log-Record als JSON"""
        
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "module": self.module_name,
            "level": record.levelname,
            "message": record.getMessage(),
            "function": record.funcName,
            "line": record.lineno,
            "file": record.filename
        }
        
        # Exception-Info hinzufügen falls vorhanden
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Extra-Felder hinzufügen falls vorhanden
        if hasattr(record, 'extra_data'):
            log_entry["extra"] = record.extra_data
        
        return json.dumps(log_entry, ensure_ascii=False)

# Globale Logging-System Instanz
_logging_system = None

def get_logging_system() -> EnhancedLoggingSystem:
    """Singleton für Logging-System"""
    global _logging_system
    if _logging_system is None:
        _logging_system = EnhancedLoggingSystem()
    return _logging_system

# Convenience-Funktionen für verschiedene Module
def get_steam_charts_logger():
    """Logger für steam_charts_manager → logs/steam_charts.log"""
    return get_logging_system().get_logger("steam_charts", "steam_charts.log")

def get_database_logger():
    """Logger für database_manager → logs/database.log"""
    return get_logging_system().get_logger("database", "database.log")

def get_main_logger():
    """Logger für main.py → logs/main.log"""
    return get_logging_system().get_logger("main", "main.log")

def get_batch_processor_logger():
    """Logger für batch_processor → logs/batch_processor.log"""
    return get_logging_system().get_logger("batch_processor", "batch_processor.log")

def get_background_scheduler_logger():
    """Logger für background_scheduler → logs/scheduler.log"""
    return get_logging_system().get_logger("background_scheduler", "scheduler.log")

def get_price_tracker_logger():
    """Logger für price_tracker → logs/price_tracker.log"""
    return get_logging_system().get_logger("price_tracker", "price_tracker.log")

def get_steam_wishlist_logger():
    """Logger für steam_wishlist_manager → logs/steam_wishlist.log"""
    return get_logging_system().get_logger("steam_wishlist", "steam_wishlist.log")#



def setup_module_logger(module_name: str, custom_filename: str = None):
    """
    Generische Funktion für beliebige Module
    
    Args:
        module_name: Name des Moduls
        custom_filename: Optionaler Dateiname
        
    Returns:
        Konfigurierter Logger
    """
    return get_logging_system().get_logger(module_name, custom_filename)

# Test und Debug-Funktionen
def test_all_loggers():
    """Testet alle Logger mit verschiedenen Nachrichten"""
    print("\n🧪 LOGGER-TESTS")
    print("=" * 20)
    
    loggers_to_test = [
        ("steam_charts", get_steam_charts_logger),
        ("database", get_database_logger), 
        ("main", get_main_logger),
        ("batch_processor", get_batch_processor_logger),
        ("scheduler", get_background_scheduler_logger)
    ]
    
    for name, logger_func in loggers_to_test:
        logger = logger_func()
        
        # Test verschiedene Level
        logger.debug(f"🔍 Debug-Test für {name}")
        logger.info(f"ℹ️ Info-Test für {name}")
        logger.warning(f"⚠️ Warning-Test für {name}")
        logger.error(f"❌ Error-Test für {name}")
        
        print(f"✅ {name}: Nachrichten gesendet")
    
    # Log-Dateien anzeigen
    log_dir = Path(get_logging_system().config['log_directory'])
    if log_dir.exists():
        log_files = list(log_dir.glob("*.log"))
        print(f"\n📁 Log-Dateien erstellt ({len(log_files)}):")
        for log_file in log_files:
            size = log_file.stat().st_size
            print(f"   📄 {log_file.name}: {size} Bytes")

def show_log_structure():
    """Zeigt die Log-Verzeichnis-Struktur"""
    log_dir = Path(get_logging_system().config['log_directory'])
    
    print(f"\n📁 LOG-VERZEICHNIS STRUKTUR: {log_dir}")
    print("=" * 40)
    
    if log_dir.exists():
        for item in sorted(log_dir.iterdir()):
            if item.is_file():
                size = item.stat().st_size
                modified = datetime.fromtimestamp(item.stat().st_mtime)
                print(f"📄 {item.name}")
                print(f"   Größe: {size:,} Bytes")
                print(f"   Geändert: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
                print()
    else:
        print("❌ Log-Verzeichnis existiert nicht")

if __name__ == "__main__":
    print("🚀 ENHANCED LOGGING SYSTEM TEST")
    print("=" * 35)
    
    # System initialisieren
    logging_system = get_logging_system()
    
    # Alle Logger testen
    test_all_loggers()
    
    # Struktur anzeigen
    show_log_structure()
    
    print(f"\n💡 VERWENDUNG IN IHREN MODULEN:")
    print(f"   # In steam_charts_manager.py:")
    print(f"   from logging_config import get_steam_charts_logger")
    print(f"   logger = get_steam_charts_logger()")
    print(f"")
    print(f"   # In database_manager.py:")
    print(f"   from logging_config import get_database_logger") 
    print(f"   logger = get_database_logger()")