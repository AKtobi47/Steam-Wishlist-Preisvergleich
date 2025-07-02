#!/usr/bin/env python3
"""
Enhanced Logging System Debugger
Testet das neue Enhanced Logging System mit separaten Dateien und .env Support
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
import sys

def test_env_loading():
    """Test 1: .env Datei Loading"""
    print("🔍 TEST 1: .env DATEI LOADING")
    print("=" * 35)
    
    env_file = Path(".env")
    if not env_file.exists():
        print(f"❌ .env Datei nicht gefunden: {env_file}")
        return False
    
    print(f"✅ .env Datei gefunden: {env_file}")
    
    # .env Inhalt anzeigen (nur Logging-Variablen)
    logging_vars_found = {}
    
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key.startswith('LOG_'):
                        logging_vars_found[key] = value
                        print(f"   📝 Zeile {line_num}: {key}={value}")
    
    except Exception as e:
        print(f"❌ Fehler beim Lesen der .env: {e}")
        return False
    
    required_vars = ['LOG_LEVEL', 'LOG_FILE', 'LOG_TO_CONSOLE', 'LOG_STRUCTURED']
    missing_vars = [var for var in required_vars if var not in logging_vars_found]
    
    if missing_vars:
        print(f"⚠️ Fehlende Variablen: {missing_vars}")
    else:
        print(f"✅ Alle erforderlichen Variablen gefunden")
    
    return len(missing_vars) == 0

def test_enhanced_logging_import():
    """Test 2: Enhanced Logging System Import"""
    print("\n🔍 TEST 2: ENHANCED LOGGING IMPORT")
    print("=" * 35)
    
    try:
        # Versuche Enhanced Logging System zu importieren
        from logging_config import get_logging_system, EnhancedLoggingSystem
        print("✅ Enhanced Logging System importiert")
        
        # System initialisieren
        logging_system = get_logging_system()
        print("✅ Logging System initialisiert")
        
        # Konfiguration anzeigen
        config = logging_system.config
        print(f"\n📋 GELADENE KONFIGURATION:")
        for key, value in config.items():
            print(f"   {key}: {value}")
        
        return True, logging_system
        
    except ImportError as e:
        print(f"❌ Import-Fehler: {e}")
        print("💡 Stellen Sie sicher, dass logging_config.py existiert")
        return False, None
    except Exception as e:
        print(f"❌ Initialisierungsfehler: {e}")
        return False, None

def test_separate_loggers(logging_system):
    """Test 3: Separate Logger für verschiedene Module"""
    print("\n🔍 TEST 3: SEPARATE LOGGER")
    print("=" * 30)
    
    test_modules = [
        ("steam_charts", "Steam Charts API Aufrufe"),
        ("database", "Datenbank-Operationen"),
        ("main", "Hauptmenü-Aktionen"),
        ("batch_processor", "Batch-Updates"),
        ("scheduler", "Background-Tasks")
    ]
    
    created_loggers = {}
    
    for module_name, description in test_modules:
        try:
            logger = logging_system.get_logger(module_name)
            created_loggers[module_name] = logger
            
            # Test-Nachrichten senden
            logger.info(f"🧪 Test-Nachricht für {description}")
            logger.debug(f"🔍 Debug-Nachricht für {module_name}")
            logger.warning(f"⚠️ Warning-Test für {module_name}")
            
            print(f"✅ {module_name}: Logger erstellt und getestet")
            
        except Exception as e:
            print(f"❌ {module_name}: Fehler - {e}")
    
    return created_loggers

def test_log_files(logging_system):
    """Test 4: Log-Dateien Validierung"""
    print("\n🔍 TEST 4: LOG-DATEIEN VALIDIERUNG")
    print("=" * 35)
    
    log_directory = Path(logging_system.config['log_directory'])
    
    if not log_directory.exists():
        print(f"❌ Log-Verzeichnis existiert nicht: {log_directory}")
        return False
    
    print(f"✅ Log-Verzeichnis: {log_directory}")
    
    # Log-Dateien finden
    log_files = list(log_directory.glob("*.log"))
    
    if not log_files:
        print("❌ Keine Log-Dateien gefunden")
        return False
    
    print(f"📁 Gefundene Log-Dateien ({len(log_files)}):")
    
    total_size = 0
    for log_file in sorted(log_files):
        try:
            size = log_file.stat().st_size
            modified = datetime.fromtimestamp(log_file.stat().st_mtime)
            total_size += size
            
            print(f"   📄 {log_file.name}")
            print(f"      Größe: {size:,} Bytes")
            print(f"      Geändert: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Datei-Inhalt prüfen (erste/letzte Zeilen)
            if size > 0:
                try:
                    content = log_file.read_text(encoding='utf-8')
                    lines = content.strip().split('\n')
                    print(f"      Zeilen: {len(lines)}")
                    if lines and lines[0]:
                        print(f"      Erste: {lines[0][:80]}...")
                    if len(lines) > 1 and lines[-1]:
                        print(f"      Letzte: {lines[-1][:80]}...")
                except Exception as e:
                    print(f"      ⚠️ Kann Inhalt nicht lesen: {e}")
            else:
                print(f"      ⚠️ Datei ist leer")
            
            print()
            
        except Exception as e:
            print(f"   ❌ {log_file.name}: Fehler - {e}")
    
    print(f"📊 Gesamt-Log-Größe: {total_size:,} Bytes")
    return len(log_files) > 0

def test_structured_logging(logging_system):
    """Test 5: Strukturiertes Logging (JSON)"""
    print("\n🔍 TEST 5: STRUKTURIERTES LOGGING")
    print("=" * 35)
    
    if not logging_system.config['log_structured']:
        print("ℹ️ Strukturiertes Logging ist deaktiviert (LOG_STRUCTURED=false)")
        return True
    
    print("📝 Teste JSON-Logging...")
    
    # Test-Logger mit strukturiertem Format
    test_logger = logging_system.get_logger("json_test", "json_test.log")
    
    # Test-Nachrichten mit extra Daten
    test_messages = [
        ("info", "JSON Test Nachricht 1"),
        ("debug", "JSON Debug mit Details"),
        ("warning", "JSON Warning Test"),
        ("error", "JSON Error Test")
    ]
    
    for level, message in test_messages:
        getattr(test_logger, level)(message)
    
    # JSON-Log-Datei prüfen
    json_log_file = Path(logging_system.config['log_directory']) / "json_test.log"
    
    if json_log_file.exists():
        try:
            content = json_log_file.read_text(encoding='utf-8')
            lines = content.strip().split('\n')
            
            print(f"✅ JSON-Log erstellt: {len(lines)} Zeilen")
            
            # Erste Zeile als JSON parsen
            if lines:
                try:
                    first_json = json.loads(lines[0])
                    print(f"✅ JSON-Format validiert:")
                    for key, value in first_json.items():
                        print(f"   {key}: {value}")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON-Parse-Fehler: {e}")
                    print(f"   Inhalt: {lines[0][:100]}...")
            
        except Exception as e:
            print(f"❌ Fehler beim Lesen der JSON-Log: {e}")
            return False
    else:
        print(f"❌ JSON-Log-Datei nicht erstellt: {json_log_file}")
        return False
    
    return True

def test_environment_variables():
    """Test 6: Umgebungsvariablen nach Import"""
    print("\n🔍 TEST 6: UMGEBUNGSVARIABLEN")
    print("=" * 30)
    
    # Prüfe ob Umgebungsvariablen gesetzt sind
    logging_env_vars = [
        'LOG_LEVEL', 'LOG_FILE', 'LOG_TO_CONSOLE', 'LOG_ROTATION',
        'LOG_MAX_SIZE', 'LOG_BACKUP_COUNT', 'LOG_STRUCTURED'
    ]
    
    found_vars = {}
    missing_vars = []
    
    for var in logging_env_vars:
        value = os.getenv(var)
        if value is not None:
            found_vars[var] = value
            print(f"✅ {var}={value}")
        else:
            missing_vars.append(var)
            print(f"❌ {var}=NICHT_GESETZT")
    
    print(f"\n📊 Zusammenfassung:")
    print(f"   Gefunden: {len(found_vars)}/{len(logging_env_vars)}")
    
    if missing_vars:
        print(f"   Fehlend: {missing_vars}")
        return False
    
    return True

def run_complete_test():
    """Führt alle Tests durch"""
    print("🚀 ENHANCED LOGGING SYSTEM - VOLLSTÄNDIGER TEST")
    print("=" * 50)
    print(f"🕐 Gestartet: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = {}
    
    # Test 1: .env Loading
    test_results['env_loading'] = test_env_loading()
    
    # Test 2: System Import
    import_success, logging_system = test_enhanced_logging_import()
    test_results['system_import'] = import_success
    
    if not import_success:
        print("\n❌ KRITISCHER FEHLER: System konnte nicht initialisiert werden")
        return test_results
    
    # Test 3: Separate Logger
    created_loggers = test_separate_loggers(logging_system)
    test_results['separate_loggers'] = len(created_loggers) > 0
    
    # Test 4: Log-Dateien
    test_results['log_files'] = test_log_files(logging_system)
    
    # Test 5: Strukturiertes Logging
    test_results['structured_logging'] = test_structured_logging(logging_system)
    
    # Test 6: Umgebungsvariablen
    test_results['environment_vars'] = test_environment_variables()
    
    # Gesamt-Ergebnis
    print("\n🏆 TEST-ERGEBNISSE")
    print("=" * 20)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed in test_results.items():
        status = "✅ BESTANDEN" if passed else "❌ FEHLGESCHLAGEN"
        print(f"{status} {test_name.replace('_', ' ').title()}")
        if passed:
            passed_tests += 1
    
    print(f"\n📊 GESAMT: {passed_tests}/{total_tests} Tests bestanden")
    
    if passed_tests == total_tests:
        print("🎉 ALLE TESTS BESTANDEN - Logging System ist vollständig funktional!")
    elif passed_tests >= total_tests * 0.8:
        print("⚠️ MEISTE TESTS BESTANDEN - Kleinere Probleme vorhanden")
    else:
        print("❌ KRITISCHE PROBLEME - System benötigt Fehlerbehebung")
    
    return test_results

if __name__ == "__main__":
    # Vollständigen Test durchführen
    results = run_complete_test()
    
    # Exit-Code setzen basierend auf Ergebnissen
    passed = sum(results.values())
    total = len(results)
    
    if passed == total:
        sys.exit(0)  # Erfolg
    else:
        sys.exit(1)  # Fehler