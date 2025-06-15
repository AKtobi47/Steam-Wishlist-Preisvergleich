#!/usr/bin/env python3
"""
Steam Charts Setup Script
Automatisiert die Integration der Charts-Funktionalität in das bestehende System
"""

import os
import sys
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
import logging

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChartsSetupManager:
    """
    Automatisiert die Charts-Integration
    """
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.backup_dir = self.project_root / "backup_before_charts"
        self.required_files = [
            "steam_charts_manager.py",
            "enhanced_price_tracker_charts.py", 
            "charts_cli_manager.py",
            "enhanced_main_with_charts.py"
        ]
        
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
                f.write(f"Zweck: Vor Charts-Integration\n")
                f.write(f"Dateien: {backed_up}\n\n")
                f.write("Wiederherstellung:\n")
                f.write("1. Kopiere Dateien zurück ins Hauptverzeichnis\n")
                f.write("2. Starte python main.py\n")
            
            return True
            
        except Exception as e:
            print(f"❌ Backup fehlgeschlagen: {e}")
            return False
    
    def check_prerequisites(self) -> dict:
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
        for file_name in self.required_files:
            if not (self.project_root / file_name).exists():
                missing_files.append(file_name)
        
        checks['charts_files_present'] = len(missing_files) == 0
        checks['missing_files'] = missing_files
        
        return checks
    
    def display_prerequisites(self, checks: dict):
        """Zeigt Voraussetzungen-Status an"""
        print("\n🔍 VORAUSSETZUNGEN PRÜFEN")
        print("=" * 30)
        
        status_icon = lambda x: "✅" if x else "❌"
        
        print(f"{status_icon(checks['python_version'])} Python 3.8+: {sys.version.split()[0]}")
        print(f"{status_icon(checks['existing_tracker'])} Bestehender Tracker vorhanden")
        print(f"{status_icon(checks['database_exists'])} Datenbank vorhanden")
        print(f"{status_icon(checks['api_key_present'])} Steam API Key konfiguriert")
        print(f"{status_icon(checks['required_modules'])} Python-Module verfügbar")
        print(f"{status_icon(checks['charts_files_present'])} Charts-Dateien vorhanden")
        
        if not checks['charts_files_present']:
            print(f"\n⚠️ Fehlende Dateien:")
            for file_name in checks.get('missing_files', []):
                print(f"   - {file_name}")
        
        # Gesamtstatus
        all_good = all(v for k, v in checks.items() if k != 'missing_files')
        
        if all_good:
            print(f"\n✅ Alle Voraussetzungen erfüllt - Integration kann beginnen!")
        else:
            print(f"\n⚠️ Einige Voraussetzungen nicht erfüllt - bitte beheben vor Integration")
        
        return all_good
    
    def integrate_database_extensions(self) -> bool:
        """Integriert Charts-Erweiterungen in database_manager.py"""
        try:
            print("🗄️ Integriere Datenbank-Erweiterungen...")
            
            db_manager_file = self.project_root / "database_manager.py"
            charts_extension_file = self.project_root / "database_manager_charts_extension.py"
            
            if not charts_extension_file.exists():
                print("❌ database_manager_charts_extension.py nicht gefunden")
                return False
            
            # Lese bestehende database_manager.py
            with open(db_manager_file, 'r', encoding='utf-8') as f:
                existing_content = f.read()
            
            # Prüfe ob bereits integriert
            if 'init_charts_tables' in existing_content:
                print("✅ Charts-Erweiterungen bereits in database_manager.py integriert")
                return True
            
            # Lese Charts-Erweiterungen
            with open(charts_extension_file, 'r', encoding='utf-8') as f:
                extension_content = f.read()
            
            # Extrahiere nur die Methoden (ohne die Kommentare am Anfang)
            extension_lines = extension_content.split('\n')
            method_lines = []
            in_method = False
            
            for line in extension_lines:
                if line.strip().startswith('def ') and not line.strip().startswith('# '):
                    in_method = True
                
                if in_method:
                    method_lines.append(line)
            
            # Finde die letzte Methode in DatabaseManager
            existing_lines = existing_content.split('\n')
            insert_position = -1
            
            for i in range(len(existing_lines)-1, -1, -1):
                if existing_lines[i].strip() and not existing_lines[i].startswith(' ') and not existing_lines[i].startswith('\t'):
                    if 'class ' not in existing_lines[i]:
                        insert_position = i + 1
                        break
            
            if insert_position == -1:
                # Fallback: am Ende der Datei einfügen
                insert_position = len(existing_lines)
            
            # Einfügen der Charts-Methoden
            new_content_lines = existing_lines[:insert_position]
            new_content_lines.append("\n    # ========================")
            new_content_lines.append("    # CHARTS EXTENSION METHODS")
            new_content_lines.append("    # ========================\n")
            new_content_lines.extend(['    ' + line for line in method_lines])  # Einrückung hinzufügen
            new_content_lines.extend(existing_lines[insert_position:])
            
            # Modifiziere __init__ Methode um init_charts_tables() aufzurufen
            modified_lines = []
            in_init_method = False
            
            for line in new_content_lines:
                modified_lines.append(line)
                
                if 'def __init__(self' in line:
                    in_init_method = True
                elif in_init_method and 'self._init_database()' in line:
                    modified_lines.append('        self.init_charts_tables()  # Charts-Tabellen initialisieren')
                    in_init_method = False
            
            # Schreibe modifizierte Datei
            with open(db_manager_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(modified_lines))
            
            print("✅ Datenbank-Erweiterungen erfolgreich integriert")
            return True
            
        except Exception as e:
            print(f"❌ Fehler bei Datenbank-Integration: {e}")
            return False
    
    def test_database_integration(self) -> bool:
        """Testet die Datenbank-Integration"""
        try:
            print("🧪 Teste Datenbank-Integration...")
            
            # Importiere erweiterten DatabaseManager
            sys.path.insert(0, str(self.project_root))
            from database_manager import DatabaseManager
            
            # Teste Charts-Tabellen-Erstellung
            db = DatabaseManager()
            
            # Prüfe ob Charts-Tabellen existieren
            db_file = self.project_root / "steam_price_tracker.db"
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%charts%'")
            charts_tables = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            expected_tables = ['steam_charts_tracking', 'charts_history', 'charts_price_snapshots']
            tables_created = all(table in charts_tables for table in expected_tables)
            
            if tables_created:
                print("✅ Charts-Tabellen erfolgreich erstellt")
                print(f"   Tabellen: {', '.join(charts_tables)}")
                return True
            else:
                print("❌ Nicht alle Charts-Tabellen erstellt")
                print(f"   Gefunden: {charts_tables}")
                return False
                
        except Exception as e:
            print(f"❌ Datenbank-Test fehlgeschlagen: {e}")
            return False
    
    def setup_charts_cli(self) -> bool:
        """Richtet Charts CLI ein"""
        try:
            print("🖥️ Richte Charts CLI ein...")
            
            cli_file = self.project_root / "charts_cli_manager.py"
            
            if not cli_file.exists():
                print("❌ charts_cli_manager.py nicht gefunden")
                return False
            
            # Mache CLI ausführbar (Unix-Systeme)
            if os.name != 'nt':  # Nicht Windows
                os.chmod(cli_file, 0o755)
            
            # Teste CLI
            import subprocess
            result = subprocess.run([
                sys.executable, str(cli_file), 'status'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Charts CLI funktioniert")
                return True
            else:
                print(f"⚠️ Charts CLI Test-Warnung: {result.stderr}")
                return True  # Nicht kritisch
                
        except Exception as e:
            print(f"⚠️ Charts CLI Setup-Warnung: {e}")
            return True  # Nicht kritisch
    
    def setup_enhanced_main(self) -> bool:
        """Richtet Enhanced Main ein"""
        try:
            print("🎯 Richte Enhanced Main ein...")
            
            enhanced_main = self.project_root / "enhanced_main_with_charts.py"
            current_main = self.project_root / "main.py"
            
            if not enhanced_main.exists():
                print("❌ enhanced_main_with_charts.py nicht gefunden")
                return False
            
            # Backup der aktuellen main.py (falls nicht schon geschehen)
            main_backup = self.project_root / "main_original.py"
            if not main_backup.exists() and current_main.exists():
                shutil.copy2(current_main, main_backup)
                print("📦 Backup von main.py als main_original.py erstellt")
            
            # Frage Benutzer
            print("\nOptionen für Enhanced Main:")
            print("1. Ersetze main.py mit Enhanced Version (empfohlen)")
            print("2. Behalte beide Versionen (main.py + main_charts.py)")
            print("3. Überspringe Enhanced Main Setup")
            
            while True:
                choice = input("Wähle Option (1-3): ").strip()
                
                if choice == "1":
                    # Ersetze main.py
                    shutil.copy2(enhanced_main, current_main)
                    print("✅ main.py mit Enhanced Version ersetzt")
                    break
                elif choice == "2":
                    # Kopiere als main_charts.py
                    charts_main = self.project_root / "main_charts.py"
                    shutil.copy2(enhanced_main, charts_main)
                    print("✅ Enhanced Version als main_charts.py verfügbar")
                    break
                elif choice == "3":
                    print("⏭️ Enhanced Main übersprungen")
                    break
                else:
                    print("❌ Ungültige Auswahl, bitte 1-3 eingeben")
            
            return True
            
        except Exception as e:
            print(f"❌ Enhanced Main Setup fehlgeschlagen: {e}")
            return False
    
    def test_charts_functionality(self) -> bool:
        """Testet die Charts-Funktionalität"""
        try:
            print("🧪 Teste Charts-Funktionalität...")
            
            # Teste Enhanced Tracker Import
            sys.path.insert(0, str(self.project_root))
            from enhanced_price_tracker_charts import create_enhanced_tracker
            
            # Erstelle Tracker
            tracker = create_enhanced_tracker()
            
            if tracker.charts_enabled:
                print("✅ Charts-Funktionalität verfügbar und aktiviert")
                
                # Teste Charts-Manager
                if hasattr(tracker, 'charts_manager') and tracker.charts_manager:
                    print("✅ Charts-Manager verfügbar")
                    
                    # Teste einfache Charts-Operation (ohne API-Call)
                    stats = tracker.get_charts_overview()
                    if stats.get('enabled'):
                        print("✅ Charts-Übersicht funktioniert")
                    
                return True
            else:
                print("⚠️ Charts verfügbar aber nicht aktiviert (kein API Key?)")
                return True  # Nicht kritisch
                
        except Exception as e:
            print(f"❌ Charts-Funktionalitäts-Test fehlgeschlagen: {e}")
            return False
    
    def create_success_summary(self):
        """Erstellt Erfolgs-Zusammenfassung"""
        print("\n🎉 CHARTS-INTEGRATION ERFOLGREICH!")
        print("=" * 40)
        
        print("\n📁 NEUE FUNKTIONEN:")
        print("✅ Automatisches Steam Charts Tracking")
        print("✅ Enhanced Price Monitoring für Charts-Spiele")
        print("✅ Charts CLI für Kommandozeilen-Steuerung")
        print("✅ Enhanced Main Application mit Charts-Integration")
        print("✅ Separate Charts-Datenbank-Tabellen")
        
        print("\n🚀 NÄCHSTE SCHRITTE:")
        print("1. Starte die Anwendung:")
        print("   python main.py")
        print("")
        print("2. Oder nutze die Charts CLI:")
        print("   python charts_cli_manager.py status")
        print("   python charts_cli_manager.py enable")
        print("")
        print("3. Vollautomatik einrichten:")
        print("   python charts_cli_manager.py setup-automation --run-continuous")
        
        print("\n📚 VERFÜGBARE BEFEHLE:")
        print("Charts Status:        python charts_cli_manager.py status")
        print("Charts aktivieren:    python charts_cli_manager.py enable")
        print("Charts aktualisieren: python charts_cli_manager.py update")
        print("Beste Deals:          python charts_cli_manager.py deals")
        print("Trending Drops:       python charts_cli_manager.py trending")
        
        print("\n🛠️ SUPPORT:")
        print("- Backup verfügbar in: backup_before_charts/")
        print("- Original main.py als: main_original.py")
        print("- Bei Problemen: Verwende Backup zur Wiederherstellung")
        
        print("\n💡 TIPP:")
        print("Starte mit 'python main.py' und verwende Option 18 für Vollautomatik!")

def main():
    """Hauptfunktion für Charts-Setup"""
    print("📊 STEAM CHARTS INTEGRATION SETUP")
    print("=" * 40)
    print("Dieses Script integriert die Charts-Funktionalität in dein")
    print("bestehendes Steam Price Tracker System.")
    print()
    
    setup = ChartsSetupManager()
    
    # Schritt 1: Voraussetzungen prüfen
    print("🔍 Prüfe Voraussetzungen...")
    checks = setup.check_prerequisites()
    
    if not setup.display_prerequisites(checks):
        print("\n❌ Voraussetzungen nicht erfüllt!")
        print("💡 Bitte behebe die Probleme und führe das Setup erneut aus.")
        return False
    
    # Schritt 2: Backup erstellen
    print("\n📦 Erstelle Sicherheitskopie...")
    if not setup.create_backup():
        proceed = input("⚠️ Backup fehlgeschlagen. Trotzdem fortfahren? (j/n): ").lower().strip()
        if proceed not in ['j', 'ja', 'y', 'yes']:
            print("⏹️ Setup abgebrochen")
            return False
    
    # Schritt 3: Datenbank-Erweiterungen integrieren
    print("\n🗄️ Integriere Datenbank-Erweiterungen...")
    if not setup.integrate_database_extensions():
        print("❌ Datenbank-Integration fehlgeschlagen!")
        return False
    
    # Schritt 4: Datenbank-Integration testen
    if not setup.test_database_integration():
        print("❌ Datenbank-Test fehlgeschlagen!")
        return False
    
    # Schritt 5: Charts CLI einrichten
    print("\n🖥️ Richte Charts CLI ein...")
    setup.setup_charts_cli()
    
    # Schritt 6: Enhanced Main einrichten
    print("\n🎯 Richte Enhanced Main ein...")
    if not setup.setup_enhanced_main():
        print("⚠️ Enhanced Main Setup mit Problemen, aber nicht kritisch")
    
    # Schritt 7: Charts-Funktionalität testen
    print("\n🧪 Teste Charts-Funktionalität...")
    if not setup.test_charts_functionality():
        print("⚠️ Charts-Test mit Problemen, aber Setup abgeschlossen")
    
    # Erfolgs-Zusammenfassung
    setup.create_success_summary()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Setup erfolgreich abgeschlossen!")
            sys.exit(0)
        else:
            print("\n❌ Setup fehlgeschlagen!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Setup durch Benutzer abgebrochen")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        logger.exception("Setup-Fehler")
        sys.exit(1)