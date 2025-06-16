#!/usr/bin/env python3
"""
Universal Background Scheduler - ENHANCED mit Sign of Life
Universeller Scheduler für alle Background-Tasks in separaten Terminals
ENHANCED: Terminals zeigen kontinuierlich "Sign of Life" mit Ticker, Heartbeat und Fortschrittsbalken
"""

import os
import sys
import time
import subprocess
import threading
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
import logging

logger = logging.getLogger(__name__)

class BackgroundScheduler:
    """
    Universeller Background-Scheduler für separate Terminal-Execution
    ENHANCED: Mit kontinuierlichen Sign of Life Indicators
    """
    
    def __init__(self, scheduler_name: str, base_config: Dict = None):
        """
        Initialisiert universellen Background-Scheduler
        
        Args:
            scheduler_name: Eindeutiger Name für diesen Scheduler
            base_config: Basis-Konfiguration für den Scheduler
        """
        self.scheduler_name = scheduler_name
        self.base_config = base_config or {}
        
        # Scheduler-Status
        self.running_processes = {}  # scheduler_type -> subprocess
        self.scheduler_configs = {}  # scheduler_type -> config
        
        # Basis-Verzeichnisse
        self.temp_dir = Path("temp_schedulers")
        self.temp_dir.mkdir(exist_ok=True)
        
        # Python-Pfad für korrekte Imports
        self.project_root = Path.cwd()
        
        logger.info(f"✅ Universal Background Scheduler '{scheduler_name}' initialisiert")
    
    def register_scheduler(self, 
                          scheduler_type: str,
                          task_function: str,
                          interval_minutes: int,
                          task_config: Dict = None,
                          dependencies: List[str] = None,
                          heartbeat_interval: int = 30,
                          show_progress_bar: bool = True) -> bool:
        """
        Registriert einen neuen Scheduler-Typ
        
        Args:
            scheduler_type: Typ des Schedulers (z.B. 'price_updates', 'name_updates')
            task_function: Python-Funktion die ausgeführt werden soll
            interval_minutes: Intervall in Minuten
            task_config: Konfiguration für die Task
            dependencies: Erforderliche Python-Module
            heartbeat_interval: Heartbeat-Intervall in Sekunden (Standard: 30)
            show_progress_bar: Ob Fortschrittsbalken angezeigt werden soll
            
        Returns:
            True wenn erfolgreich registriert
        """
        try:
            self.scheduler_configs[scheduler_type] = {
                'task_function': task_function,
                'interval_minutes': interval_minutes,
                'task_config': task_config or {},
                'dependencies': dependencies or [],
                'heartbeat_interval': heartbeat_interval,
                'show_progress_bar': show_progress_bar,
                'registered_at': datetime.now().isoformat(),
                'enabled': False
            }
            
            logger.info(f"✅ Scheduler '{scheduler_type}' registriert (Intervall: {interval_minutes}min, Heartbeat: {heartbeat_interval}s)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Registrieren von Scheduler '{scheduler_type}': {e}")
            return False
    
    def start_scheduler(self, scheduler_type: str, **kwargs) -> bool:
        """
        Startet einen registrierten Scheduler in separatem Terminal
        
        Args:
            scheduler_type: Typ des zu startenden Schedulers
            **kwargs: Zusätzliche Parameter für den Scheduler
            
        Returns:
            True wenn erfolgreich gestartet
        """
        if scheduler_type not in self.scheduler_configs:
            logger.error(f"❌ Scheduler-Typ '{scheduler_type}' nicht registriert")
            return False
        
        if scheduler_type in self.running_processes:
            if self.is_scheduler_running(scheduler_type):
                logger.warning(f"⚠️ Scheduler '{scheduler_type}' läuft bereits")
                return True
            else:
                # Aufräumen falls Prozess tot ist
                del self.running_processes[scheduler_type]
        
        try:
            # Scheduler-Script erstellen
            script_path = self._create_enhanced_scheduler_script(scheduler_type, **kwargs)
            
            # Separaten Terminal-Prozess starten
            process = self._start_terminal_process_fixed(script_path, scheduler_type)
            
            if process:
                self.running_processes[scheduler_type] = process
                self.scheduler_configs[scheduler_type]['enabled'] = True
                self.scheduler_configs[scheduler_type]['started_at'] = datetime.now().isoformat()
                
                logger.info(f"✅ Scheduler '{scheduler_type}' in separatem Terminal gestartet")
                return True
            else:
                logger.error(f"❌ Fehler beim Starten des Terminal-Prozesses für '{scheduler_type}'")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten von Scheduler '{scheduler_type}': {e}")
            return False
    
    def stop_scheduler(self, scheduler_type: str) -> bool:
        """
        Stoppt einen laufenden Scheduler
        
        Args:
            scheduler_type: Typ des zu stoppenden Schedulers
            
        Returns:
            True wenn erfolgreich gestoppt
        """
        if scheduler_type not in self.running_processes:
            logger.info(f"ℹ️ Scheduler '{scheduler_type}' war nicht aktiv")
            return True
        
        try:
            process = self.running_processes[scheduler_type]
            
            # Prozess beenden
            process.terminate()
            
            # Auf Beendigung warten (mit Timeout)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill falls nötig
                process.kill()
                process.wait()
            
            # Aus Liste entfernen
            del self.running_processes[scheduler_type]
            
            # Konfiguration aktualisieren
            if scheduler_type in self.scheduler_configs:
                self.scheduler_configs[scheduler_type]['enabled'] = False
                self.scheduler_configs[scheduler_type]['stopped_at'] = datetime.now().isoformat()
            
            # Temporäre Dateien aufräumen
            self._cleanup_scheduler_files(scheduler_type)
            
            logger.info(f"⏹️ Scheduler '{scheduler_type}' gestoppt")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Stoppen von Scheduler '{scheduler_type}': {e}")
            return False
    
    def stop_all_schedulers(self) -> int:
        """
        Stoppt alle laufenden Scheduler
        
        Returns:
            Anzahl gestoppter Scheduler
        """
        stopped_count = 0
        
        for scheduler_type in list(self.running_processes.keys()):
            if self.stop_scheduler(scheduler_type):
                stopped_count += 1
        
        logger.info(f"⏹️ {stopped_count} Scheduler gestoppt")
        return stopped_count
    
    def is_scheduler_running(self, scheduler_type: str) -> bool:
        """
        Prüft ob ein Scheduler läuft
        
        Args:
            scheduler_type: Typ des Schedulers
            
        Returns:
            True wenn Scheduler läuft
        """
        if scheduler_type not in self.running_processes:
            return False
        
        process = self.running_processes[scheduler_type]
        return process.poll() is None
    
    def get_scheduler_status(self, scheduler_type: str = None) -> Dict:
        """
        Gibt Status eines oder aller Scheduler zurück
        
        Args:
            scheduler_type: Spezifischer Scheduler oder None für alle
            
        Returns:
            Status-Dictionary
        """
        if scheduler_type:
            # Status für spezifischen Scheduler
            if scheduler_type not in self.scheduler_configs:
                return {'error': f"Scheduler '{scheduler_type}' nicht registriert"}
            
            config = self.scheduler_configs[scheduler_type]
            
            return {
                'scheduler_type': scheduler_type,
                'registered': True,
                'enabled': config.get('enabled', False),
                'running': self.is_scheduler_running(scheduler_type),
                'interval_minutes': config.get('interval_minutes', 0),
                'heartbeat_interval': config.get('heartbeat_interval', 30),
                'show_progress_bar': config.get('show_progress_bar', True),
                'task_function': config.get('task_function', ''),
                'registered_at': config.get('registered_at', ''),
                'started_at': config.get('started_at', ''),
                'stopped_at': config.get('stopped_at', '')
            }
        else:
            # Status für alle Scheduler
            all_status = {
                'scheduler_name': self.scheduler_name,
                'total_registered': len(self.scheduler_configs),
                'total_running': len([st for st in self.scheduler_configs if self.is_scheduler_running(st)]),
                'schedulers': {}
            }
            
            for st in self.scheduler_configs:
                all_status['schedulers'][st] = self.get_scheduler_status(st)
            
            return all_status
    
    def _create_enhanced_scheduler_script(self, scheduler_type: str, **kwargs) -> str:
        """
        ENHANCED: Erstellt temporäres Python-Script mit Sign of Life Features
        
        Args:
            scheduler_type: Typ des Schedulers
            **kwargs: Zusätzliche Parameter
            
        Returns:
            Pfad zum erstellten Script
        """
        config = self.scheduler_configs[scheduler_type]
        heartbeat_interval = config.get('heartbeat_interval', 30)
        show_progress_bar = config.get('show_progress_bar', True)
        
        # ENHANCED: Script-Inhalt mit Sign of Life Features
        script_content = f'''#!/usr/bin/env python3
"""
ENHANCED Background Scheduler: {scheduler_type}
Auto-generated scheduler script mit Sign of Life Features
Scheduler: {self.scheduler_name}
ENHANCED mit Ticker, Heartbeat und Fortschrittsbalken
"""

import sys
import time
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path

# Aktuelles Verzeichnis zum Python-Pfad hinzufügen
project_root = Path("{self.project_root}")
sys.path.insert(0, str(project_root))

# Konfiguration
SCHEDULER_TYPE = "{scheduler_type}"
SCHEDULER_NAME = "{self.scheduler_name}"
INTERVAL_MINUTES = {config['interval_minutes']}
HEARTBEAT_INTERVAL = {heartbeat_interval}
SHOW_PROGRESS_BAR = {show_progress_bar}
TASK_CONFIG = {json.dumps(config.get('task_config', {}), indent=4)}
BASE_CONFIG = {json.dumps(self.base_config, indent=4)}
KWARGS = {json.dumps(kwargs, indent=4)}

# =====================================================================
# ENHANCED SIGN OF LIFE FUNCTIONS
# =====================================================================

class SignOfLife:
    """Klasse für Sign of Life Indicators"""
    
    def __init__(self):
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.heart_chars = ['💙', '🤍', '💚', '🤍', '💛', '🤍', '❤️', '🤍']
        self.spinner_index = 0
        self.heart_index = 0
        self.running = False
        self.ticker_thread = None
        self.last_heartbeat = time.time()
        
    def start_ticker(self):
        """Startet kontinuierlichen Ticker"""
        self.running = True
        self.ticker_thread = threading.Thread(target=self._ticker_loop, daemon=True)
        self.ticker_thread.start()
        
    def stop_ticker(self):
        """Stoppt Ticker"""
        self.running = False
        if self.ticker_thread and self.ticker_thread.is_alive():
            self.ticker_thread.join(timeout=1)
    
    def _ticker_loop(self):
        """Hauptschleife für Ticker"""
        while self.running:
            current_time = time.time()
            
            # Spinner aktualisieren
            spinner = self.spinner_chars[self.spinner_index]
            self.spinner_index = (self.spinner_index + 1) % len(self.spinner_chars)
            
            # Heartbeat prüfen
            if current_time - self.last_heartbeat >= HEARTBEAT_INTERVAL:
                heart = self.heart_chars[self.heart_index]
                self.heart_index = (self.heart_index + 1) % len(self.heart_chars)
                print(f"\\r{heart} HEARTBEAT - {{SCHEDULER_NAME}}/{SCHEDULER_TYPE} - {{datetime.now().strftime('%H:%M:%S')}} {heart}", flush=True)
                self.last_heartbeat = current_time
            else:
                # Normaler Ticker
                print(f"\\r{spinner} Aktiv - {{datetime.now().strftime('%H:%M:%S')}}", end='', flush=True)
            
            time.sleep(1)  # Update jede Sekunde
    
    def show_progress_bar(self, current_seconds, total_seconds, width=50):
        """Zeigt Fortschrittsbalken für verbleibende Zeit"""
        if not SHOW_PROGRESS_BAR or total_seconds <= 0:
            return
            
        progress = min(current_seconds / total_seconds, 1.0)
        filled_width = int(width * progress)
        
        bar = '█' * filled_width + '░' * (width - filled_width)
        percentage = progress * 100
        
        remaining_seconds = max(0, total_seconds - current_seconds)
        remaining_minutes = remaining_seconds // 60
        remaining_secs = remaining_seconds % 60
        
        print(f"\\r⏳ [{bar}] {{percentage:6.1f}}% - Verbleibend: {{remaining_minutes:02.0f}}:{{remaining_secs:02.0f}}", 
              end='', flush=True)

# Globale Sign of Life Instanz
sign_of_life = SignOfLife()

def enhanced_sleep_with_progress(total_seconds):
    """ENHANCED: Sleep mit Fortschrittsbalken und kontinuierlichem Ticker"""
    if total_seconds <= 0:
        return
    
    print(f"\\n⏳ Warte {{total_seconds//60:.0f}} Minuten bis zur nächsten Ausführung...")
    
    if SHOW_PROGRESS_BAR:
        # Fortschrittsbalken-Modus
        start_time = time.time()
        
        while True:
            current_time = time.time()
            elapsed_seconds = current_time - start_time
            
            if elapsed_seconds >= total_seconds:
                sign_of_life.show_progress_bar(total_seconds, total_seconds)
                print()  # Neue Zeile nach Fortschrittsbalken
                break
            
            sign_of_life.show_progress_bar(elapsed_seconds, total_seconds)
            
            # Heartbeat während Fortschrittsbalken
            if elapsed_seconds > 0 and int(elapsed_seconds) % HEARTBEAT_INTERVAL == 0:
                heart = sign_of_life.heart_chars[sign_of_life.heart_index]
                sign_of_life.heart_index = (sign_of_life.heart_index + 1) % len(sign_of_life.heart_chars)
                print(f"\\n{heart} HEARTBEAT während Wartezeit {heart}")
                sign_of_life.show_progress_bar(elapsed_seconds, total_seconds)
            
            time.sleep(1)
    else:
        # Einfacher Ticker-Modus
        for remaining in range(int(total_seconds), 0, -1):
            minutes = remaining // 60
            seconds = remaining % 60
            spinner = sign_of_life.spinner_chars[sign_of_life.spinner_index]
            sign_of_life.spinner_index = (sign_of_life.spinner_index + 1) % len(sign_of_life.spinner_chars)
            
            print(f"\\r{spinner} Verbleibend: {{minutes:02d}}:{{seconds:02d}}", end='', flush=True)
            time.sleep(1)
        print()  # Neue Zeile

# =====================================================================
# MAIN EXECUTION
# =====================================================================

print("🚀 ENHANCED Background Scheduler gestartet")
print("=" * 60)
print(f"📊 Scheduler: {{SCHEDULER_NAME}}")
print(f"🎯 Task: {{SCHEDULER_TYPE}}")
print(f"⏰ Intervall: {{INTERVAL_MINUTES}} Minuten")
print(f"💓 Heartbeat: {{HEARTBEAT_INTERVAL}} Sekunden")
print(f"📊 Progress Bar: {{'✅' if SHOW_PROGRESS_BAR else '❌'}}")
print(f"🚀 Gestartet: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
print(f"📁 Working Directory: {{project_root}}")
print("⚠️ Drücke Ctrl+C zum Beenden")
print("💡 SIGN OF LIFE: Ticker zeigt kontinuierliche Aktivität")
print()

try:
    # Dependencies importieren mit Fehlerbehandlung
    {self._generate_import_statements_corrected(config.get('dependencies', []))}
    
    print("✅ Alle Module erfolgreich importiert")
    
    # Task-Funktion definieren und ausführen
    def execute_task():
        try:
            print("🔄 Führe Task aus...")
            {self._format_task_function(config['task_function'])}
            return True
        except Exception as e:
            print(f"❌ Task-Fehler: {{e}}")
            import traceback
            traceback.print_exc()
            return False
    
    # Sign of Life starten
    sign_of_life.start_ticker()
    print("💓 Sign of Life Ticker gestartet")
    
    # Hauptschleife mit Enhanced Features
    cycle = 0
    while True:
        cycle += 1
        
        # Sign of Life temporär stoppen für Task-Ausführung
        sign_of_life.stop_ticker()
        
        print(f"\\n🔄 === ZYKLUS {{cycle}} - {{datetime.now().strftime('%H:%M:%S')}} ===")
        
        success = execute_task()
        
        if success:
            print(f"✅ Task erfolgreich ausgeführt")
        else:
            print(f"❌ Task fehlgeschlagen")
        
        print(f"⏳ Nächste Ausführung in {{INTERVAL_MINUTES}} Minuten...")
        
        # Enhanced Sleep mit Progress Bar und kontinuierlichem Ticker
        enhanced_sleep_with_progress(INTERVAL_MINUTES * 60)
        
        # Sign of Life neu starten
        sign_of_life.start_ticker()

except KeyboardInterrupt:
    print("\\n⏹️ Scheduler gestoppt durch Benutzer")
    sign_of_life.stop_ticker()
except ImportError as e:
    print(f"❌ Import-Fehler: {{e}}")
    print("💡 Prüfe ob alle Module verfügbar sind:")
    print(f"   - Arbeitsverzeichnis: {{project_root}}")
    print(f"   - Python-Pfad: {{sys.path[:3]}}")
    print("💡 Starte das Hauptprogramm vom richtigen Verzeichnis")
    sign_of_life.stop_ticker()
except Exception as e:
    print(f"❌ Unerwarteter Fehler: {{e}}")
    import traceback
    traceback.print_exc()
    sign_of_life.stop_ticker()
    sys.exit(1)
finally:
    sign_of_life.stop_ticker()
    print("\\n👋 Background Scheduler beendet")
'''
        
        # Script-Datei erstellen
        script_filename = f"scheduler_{self.scheduler_name}_{scheduler_type}.py"
        script_path = self.temp_dir / script_filename
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        return str(script_path)
    
    def _generate_import_statements_corrected(self, dependencies: List[str]) -> str:
        """
        Generiert robuste Import-Statements
        
        Args:
            dependencies: Liste der erforderlichen Module
            
        Returns:
            Import-Statements als String mit Fehlerbehandlung
        """
        if not dependencies:
            return "    # Keine zusätzlichen Dependencies"
        
        imports = []
        for dep in dependencies:
            if '.' in dep:
                # from module import submodule
                module, submodule = dep.rsplit('.', 1)
                imports.append(f"""    try:
        from {module} import {submodule}
        print(f"✅ Imported {submodule} from {module}")
    except ImportError as e:
        print(f"❌ Failed to import {submodule} from {module}: {{e}}")
        raise""")
            else:
                # import module
                imports.append(f"""    try:
        import {dep}
        print(f"✅ Imported {dep}")
    except ImportError as e:
        print(f"❌ Failed to import {dep}: {{e}}")
        raise""")
        
        return '\n'.join(imports)
    
    def _format_task_function(self, task_function: str) -> str:
        """
        Formatiert Task-Funktion für korrekten Einzug
        
        Args:
            task_function: Task-Funktions-Code
            
        Returns:
            Korrekt eingerückter Code
        """
        # Entferne führende/nachfolgende Leerzeichen
        task_function = task_function.strip()
        
        # Füge korrekten Einzug hinzu (12 Spaces für execute_task Funktion)
        lines = task_function.split('\n')
        indented_lines = []
        
        for line in lines:
            if line.strip():  # Nur nicht-leere Zeilen einrücken
                indented_lines.append('            ' + line.lstrip())
            else:
                indented_lines.append('')
        
        return '\n'.join(indented_lines)
    
    def _start_terminal_process_fixed(self, script_path: str, scheduler_type: str) -> Optional[subprocess.Popen]:
        """
        ENHANCED: Startet Script in separatem Terminal mit Sign of Life Titel
        
        Args:
            script_path: Pfad zum Python-Script
            scheduler_type: Typ des Schedulers (für Terminal-Titel)
            
        Returns:
            Subprocess.Popen Objekt oder None
        """
        # ENHANCED: Terminal-Titel mit Sign of Life Indikator
        terminal_title = f"💓 {self.scheduler_name}_{scheduler_type} - LIVE"
        
        try:
            if os.name == 'nt':  # Windows
                
                # ENHANCED: Batch-Datei für saubere Ausführung mit Sign of Life
                batch_content = f'''@echo off
title {terminal_title}
color 0A
echo 💓 ENHANCED Background Scheduler mit Sign of Life
echo ================================================================
echo 📊 Scheduler: {self.scheduler_name}
echo 🎯 Task: {scheduler_type}
echo 💓 Sign of Life: AKTIVIERT
echo ⏰ Zeit: %date% %time%
echo ================================================================
echo 💡 Dieses Terminal zeigt kontinuierliche Aktivitaet
echo 💡 Ticker, Heartbeat und Fortschrittsbalken inklusive
echo.
cd /d "{self.project_root}"
python "{script_path}"
echo.
echo ⏹️ Enhanced Scheduler beendet - Druecke eine Taste zum Schliessen
pause >nul
'''
                # Temporäre Batch-Datei erstellen
                batch_path = self.temp_dir / f"enhanced_start_{scheduler_type}.bat"
                with open(batch_path, 'w', encoding='utf-8') as f:
                    f.write(batch_content)
                
                # Windows start mit Enhanced Terminal
                try:
                    return subprocess.Popen([
                        'cmd', '/c', 'start', 
                        f'cmd /k "{batch_path}"'
                    ], shell=False, cwd=str(self.project_root), 
                      creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, 'CREATE_NEW_CONSOLE') else 0)
                    
                except Exception as e1:
                    logger.debug(f"Enhanced Option 1 fehlgeschlagen: {e1}")
                    try:
                        return subprocess.Popen([
                            'cmd', '/k', f'"{batch_path}"'
                        ], shell=False, cwd=str(self.project_root),
                          creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, 'CREATE_NEW_CONSOLE') else 0)
                        
                    except Exception as e2:
                        logger.debug(f"Enhanced Option 2 fehlgeschlagen: {e2}")
                        return subprocess.Popen(
                            f'start cmd /k "{batch_path}"',
                            shell=True, cwd=str(self.project_root)
                        )
            
            else:  # Linux/macOS
                terminals = [
                    ('gnome-terminal', [
                        'gnome-terminal', 
                        '--title', terminal_title,
                        '--working-directory', str(self.project_root),
                        '--', 'python3', script_path
                    ]),
                    ('xterm', [
                        'xterm', 
                        '-title', terminal_title,
                        '-e', f'cd "{self.project_root}" && python3 "{script_path}"'
                    ]),
                    ('konsole', [
                        'konsole', 
                        '--title', terminal_title,
                        '--workdir', str(self.project_root),
                        '-e', f'python3 "{script_path}"'
                    ]),
                    ('terminal', [
                        'terminal',
                        '-e', f'cd "{self.project_root}" && python3 "{script_path}"'
                    ]),
                    ('x-terminal-emulator', [
                        'x-terminal-emulator',
                        '-e', f'cd "{self.project_root}" && python3 "{script_path}"'
                    ])
                ]
                
                for terminal_name, cmd in terminals:
                    try:
                        logger.debug(f"Versuche Enhanced Terminal: {terminal_name}")
                        return subprocess.Popen(cmd, cwd=str(self.project_root))
                    except FileNotFoundError:
                        continue
                
                # Fallback: Hintergrund-Prozess
                logger.warning(f"⚠️ Kein GUI-Terminal gefunden - starte Enhanced im Hintergrund")
                return subprocess.Popen([
                    'python3', script_path
                ], cwd=str(self.project_root))
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten des Enhanced Terminal-Prozesses: {e}")
            return None
    
    def _cleanup_scheduler_files(self, scheduler_type: str):
        """
        Räumt temporäre Dateien für einen Scheduler auf
        
        Args:
            scheduler_type: Typ des Schedulers
        """
        try:
            # Python-Script aufräumen
            script_filename = f"scheduler_{self.scheduler_name}_{scheduler_type}.py"
            script_path = self.temp_dir / script_filename
            
            if script_path.exists():
                script_path.unlink()
                logger.debug(f"🧹 Temporäre Datei entfernt: {script_path}")
            
            # Enhanced Batch-Datei aufräumen (Windows)
            batch_filename = f"enhanced_start_{scheduler_type}.bat"
            batch_path = self.temp_dir / batch_filename
            
            if batch_path.exists():
                batch_path.unlink()
                logger.debug(f"🧹 Enhanced Batch-Datei entfernt: {batch_path}")
                
        except Exception as e:
            logger.debug(f"⚠️ Fehler beim Aufräumen von {scheduler_type}: {e}")
    
    def cleanup_all_files(self):
        """Räumt alle temporären Dateien auf"""
        try:
            if self.temp_dir.exists():
                # Python-Scripts aufräumen
                for file in self.temp_dir.glob("scheduler_*.py"):
                    file.unlink()
                
                # Enhanced Batch-Dateien aufräumen (Windows)
                for file in self.temp_dir.glob("enhanced_start_*.bat"):
                    file.unlink()
                
                # Verzeichnis entfernen falls leer
                try:
                    self.temp_dir.rmdir()
                except OSError:
                    pass  # Verzeichnis nicht leer
                    
                logger.info("🧹 Alle temporären Enhanced Scheduler-Dateien entfernt")
                
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Aufräumen: {e}")


# =====================================================================
# ENHANCED SCHEDULER TASK DEFINITIONS
# =====================================================================

class EnhancedSchedulerTasks:
    """
    Sammlung vordefinierter Task-Funktionen mit Enhanced Logging
    """
    
    @staticmethod
    def enhanced_price_tracking_task():
        """ENHANCED: Task für automatisches Preis-Tracking mit detailliertem Status"""
        return '''
# ENHANCED Preis-Tracking Task
print("💰 === PREIS-TRACKING GESTARTET ===")
from price_tracker import create_price_tracker
from steam_wishlist_manager import load_api_key_from_env

api_key = load_api_key_from_env()
tracker = create_price_tracker(api_key=api_key, enable_charts=False)

# Standard-Apps aktualisieren
print("🔍 Suche Apps die Updates benötigen...")
pending_apps = tracker.get_apps_needing_price_update(hours_threshold=6)

if pending_apps:
    app_ids = [app['steam_app_id'] for app in pending_apps]
    print(f"📊 Aktualisiere {len(app_ids)} Apps...")
    print(f"⏰ Start: {datetime.now().strftime('%H:%M:%S')}")
    
    start_time = time.time()
    result = tracker.track_app_prices(app_ids)
    duration = time.time() - start_time
    
    print(f"✅ {result['successful']}/{result['processed']} Apps erfolgreich aktualisiert")
    print(f"⏱️ Dauer: {duration:.1f} Sekunden ({result['successful']/duration:.1f} Apps/s)")
    
    if result.get('errors'):
        print(f"⚠️ {len(result['errors'])} Fehler aufgetreten")
        for error in result['errors'][:3]:  # Zeige nur erste 3 Fehler
            print(f"   - {error}")
else:
    print("✅ Alle Apps sind aktuell - keine Updates nötig")

print(f"🏁 Preis-Tracking abgeschlossen um {datetime.now().strftime('%H:%M:%S')}")
'''
    
    @staticmethod
    def enhanced_name_update_task():
        """ENHANCED: Task für automatische Namen-Updates mit detailliertem Status"""
        return '''
# ENHANCED Namen-Update Task
print("🔤 === NAMEN-UPDATE GESTARTET ===")
from price_tracker import create_price_tracker
from steam_wishlist_manager import load_api_key_from_env

api_key = load_api_key_from_env()
if not api_key:
    print("❌ Kein Steam API Key - Namen-Updates übersprungen")
    return

tracker = create_price_tracker(api_key=api_key, enable_charts=True)

total_updated = 0
total_checked = 0

# Standard-Apps mit generischen Namen
print("🔍 Suche Standard-Apps mit generischen Namen...")
standard_candidates = tracker.get_name_update_candidates()
standard_updated = 0

if standard_candidates:
    # Nur wenige Apps pro Durchlauf (Rate Limiting)
    batch_size = min(10, len(standard_candidates))
    batch_apps = standard_candidates[:batch_size]
    app_ids = [app['steam_app_id'] for app in batch_apps]
    
    print(f"📝 Aktualisiere {batch_size} Standard-Namen...")
    print(f"⏰ Start: {datetime.now().strftime('%H:%M:%S')}")
    
    result = tracker.update_app_names_from_steam(app_ids, api_key)
    
    if result.get('success'):
        standard_updated = result['updated']
        print(f"✅ {result['updated']}/{batch_size} Standard-Namen aktualisiert")
        total_updated += standard_updated
        total_checked += batch_size
    else:
        print(f"❌ Standard-Namen-Update fehlgeschlagen")

# Charts-Apps mit generischen Namen (falls verfügbar)
charts_updated = 0
if tracker.charts_enabled and hasattr(tracker.db_manager, 'get_active_chart_games'):
    print("🔍 Suche Charts-Apps mit generischen Namen...")
    all_chart_games = tracker.db_manager.get_active_chart_games()
    
    charts_candidates = []
    for game in all_chart_games:
        name = game.get('name', '')
        if (name.startswith('Game ') or name.startswith('Unknown Game') or 
            name.startswith('New Release') or name == '' or name is None):
            charts_candidates.append(game)
    
    if charts_candidates:
        batch_size = min(5, len(charts_candidates))
        batch_games = charts_candidates[:batch_size]
        app_ids = [game['steam_app_id'] for game in batch_games]
        
        print(f"📊 Aktualisiere {batch_size} Charts-Namen...")
        result = tracker.update_app_names_from_steam(app_ids, api_key)
        
        if result.get('success'):
            charts_updated = result['updated']
            print(f"✅ {result['updated']}/{batch_size} Charts-Namen aktualisiert")
            total_updated += charts_updated
            total_checked += batch_size
        else:
            print(f"❌ Charts-Namen-Update fehlgeschlagen")

# Zusammenfassung
if total_updated == 0:
    if total_checked == 0:
        print("✅ Alle Namen sind aktuell - keine Updates nötig")
    else:
        print("⚠️ Namen-Updates fehlgeschlagen oder keine API-Zugriffe möglich")
else:
    print(f"🎉 GESAMT: {total_updated}/{total_checked} Namen erfolgreich aktualisiert")
    print(f"   📝 Standard: {standard_updated}")
    print(f"   📊 Charts: {charts_updated}")

print(f"🏁 Namen-Update abgeschlossen um {datetime.now().strftime('%H:%M:%S')}")
'''
    
    @staticmethod
    def enhanced_charts_update_task():
        """ENHANCED: Task für Charts-Updates mit detailliertem Status"""
        return '''
# ENHANCED Charts-Update Task
print("📊 === CHARTS-UPDATE GESTARTET ===")
from price_tracker import create_price_tracker
from steam_wishlist_manager import load_api_key_from_env

api_key = load_api_key_from_env()
if not api_key:
    print("❌ Kein Steam API Key - Charts-Update übersprungen")
    return

tracker = create_price_tracker(api_key=api_key, enable_charts=True)

if not tracker.charts_enabled:
    print("❌ Charts nicht verfügbar")
    return

# Charts aktualisieren
print("📊 Starte vollständiges Charts-Update...")
print(f"⏰ Start: {datetime.now().strftime('%H:%M:%S')}")

start_time = time.time()
result = tracker.update_charts_now()
duration = time.time() - start_time

if result.get('success', True):
    print(f"✅ Charts-Update erfolgreich abgeschlossen:")
    print(f"   📊 {result.get('total_games_found', 0)} Spiele gefunden")
    print(f"   ➕ {result.get('new_games_added', 0)} neue Spiele hinzugefügt")
    print(f"   🔄 {result.get('existing_games_updated', 0)} bestehende aktualisiert")
    print(f"   ⏱️ Dauer: {duration:.1f} Sekunden")
    
    charts_updated = result.get('charts_updated', [])
    if charts_updated:
        print(f"   📈 Aktualisierte Chart-Typen: {', '.join(charts_updated)}")
    
    if result.get('errors'):
        print(f"   ⚠️ {len(result['errors'])} Fehler aufgetreten")
        for error in result['errors'][:3]:
            print(f"      - {error}")
else:
    print(f"❌ Charts-Update fehlgeschlagen: {result.get('error')}")

print(f"🏁 Charts-Update abgeschlossen um {datetime.now().strftime('%H:%M:%S')}")
'''
    
    @staticmethod
    def enhanced_charts_price_update_task():
        """ENHANCED: Task für Charts-Preis-Updates mit detailliertem Status"""
        return '''
# ENHANCED Charts-Preis-Update Task
print("💰 === CHARTS-PREIS-UPDATE GESTARTET ===")
from price_tracker import create_price_tracker
from steam_wishlist_manager import load_api_key_from_env

api_key = load_api_key_from_env()
tracker = create_price_tracker(api_key=api_key, enable_charts=True)

if not tracker.charts_enabled:
    print("❌ Charts nicht verfügbar")
    return

# Charts-Preise aktualisieren
print("💰 Starte Charts-Preis-Update...")
print(f"⏰ Start: {datetime.now().strftime('%H:%M:%S')}")

start_time = time.time()
result = tracker.update_charts_prices_now()
duration = time.time() - start_time

if result.get('success', True):
    successful = result.get('successful', 0)
    total_games = result.get('total_games', 0)
    
    print(f"✅ Charts-Preise erfolgreich aktualisiert:")
    print(f"   💰 {successful}/{total_games} Spiele aktualisiert")
    print(f"   ⏱️ Dauer: {duration:.1f} Sekunden")
    
    if total_games > 0:
        print(f"   📊 Erfolgsrate: {(successful/total_games)*100:.1f}%")
        if duration > 0:
            print(f"   ⚡ Geschwindigkeit: {successful/duration:.1f} Apps/s")
    
    if result.get('failed', 0) > 0:
        print(f"   ❌ {result['failed']} Spiele fehlgeschlagen")
else:
    print(f"❌ Charts-Preise fehlgeschlagen: {result.get('error')}")

print(f"🏁 Charts-Preis-Update abgeschlossen um {datetime.now().strftime('%H:%M:%S')}")
'''
    
    @staticmethod
    def enhanced_charts_cleanup_task():
        """ENHANCED: Task für Charts-Cleanup mit detailliertem Status"""
        return '''
# ENHANCED Charts-Cleanup Task
print("🧹 === CHARTS-CLEANUP GESTARTET ===")
from price_tracker import create_price_tracker
from steam_wishlist_manager import load_api_key_from_env

api_key = load_api_key_from_env()
tracker = create_price_tracker(api_key=api_key, enable_charts=True)

if not tracker.charts_enabled:
    print("❌ Charts nicht verfügbar")
    return

print("🧹 Starte umfassendes Charts-Cleanup...")
print(f"⏰ Start: {datetime.now().strftime('%H:%M:%S')}")

total_cleaned = 0

# Charts-Spiele Cleanup
if hasattr(tracker, 'charts_manager') and tracker.charts_manager:
    print("🗑️ Bereinige alte Charts-Spiele (>30 Tage)...")
    removed = tracker.charts_manager.cleanup_old_chart_games(days_threshold=30)
    
    if removed > 0:
        print(f"✅ {removed} alte Charts-Spiele entfernt")
        total_cleaned += removed
    else:
        print("✅ Keine alten Charts-Spiele zum Entfernen")
    
    # Zusätzlich: Alte Preis-Snapshots bereinigen
    print("🗑️ Bereinige alte Preis-Snapshots (>90 Tage)...")
    if hasattr(tracker.db_manager, 'cleanup_old_prices'):
        old_snapshots = tracker.db_manager.cleanup_old_prices(days=90)
        if old_snapshots > 0:
            print(f"🧹 {old_snapshots} alte Standard-Preis-Snapshots bereinigt")
            total_cleaned += old_snapshots
        else:
            print("✅ Keine alten Standard-Snapshots zum Bereinigen")
    
    # Datenbank optimieren
    print("🔧 Optimiere Datenbank...")
    if hasattr(tracker.db_manager, 'vacuum_database'):
        tracker.db_manager.vacuum_database()
        print("✅ Datenbank optimiert")
    
else:
    print("❌ Charts-Manager nicht verfügbar")

if total_cleaned > 0:
    print(f"🎉 Cleanup abgeschlossen: {total_cleaned} Einträge bereinigt")
else:
    print("✅ Cleanup abgeschlossen - alles bereits sauber")

print(f"🏁 Charts-Cleanup abgeschlossen um {datetime.now().strftime('%H:%M:%S')}")
'''


# =====================================================================
# ENHANCED CONVENIENCE FUNCTIONS
# =====================================================================

def create_enhanced_price_tracker_scheduler() -> BackgroundScheduler:
    """
    Erstellt ENHANCED BackgroundScheduler für Price Tracker mit Sign of Life Features
    
    Returns:
        Konfigurierter BackgroundScheduler mit Enhanced Features
    """
    scheduler = BackgroundScheduler(
        scheduler_name="PriceTracker",
        base_config={
            "rate_limit_seconds": 1.5,
            "batch_size": 50,
            "max_retries": 3,
            "enhanced_features": True
        }
    )
    
    # ENHANCED Tasks registrieren
    scheduler.register_scheduler(
        scheduler_type="price_updates",
        task_function=EnhancedSchedulerTasks.enhanced_price_tracking_task(),
        interval_minutes=360,  # 6 Stunden
        dependencies=["price_tracker", "steam_wishlist_manager"],
        heartbeat_interval=30,  # 30 Sekunden Heartbeat
        show_progress_bar=True
    )
    
    scheduler.register_scheduler(
        scheduler_type="name_updates",
        task_function=EnhancedSchedulerTasks.enhanced_name_update_task(),
        interval_minutes=30,  # 30 Minuten
        dependencies=["price_tracker", "steam_wishlist_manager"],
        heartbeat_interval=20,  # 20 Sekunden Heartbeat (häufiger da kürzer)
        show_progress_bar=True
    )
    
    return scheduler

def create_enhanced_charts_scheduler() -> BackgroundScheduler:
    """
    Erstellt ENHANCED BackgroundScheduler für Charts mit Sign of Life Features
    
    Returns:
        Konfigurierter BackgroundScheduler mit Enhanced Features
    """
    scheduler = BackgroundScheduler(
        scheduler_name="Charts",
        base_config={
            "steam_api_rate_limit": 1.0,
            "max_charts_per_update": 100,
            "enhanced_features": True
        }
    )
    
    # ENHANCED Charts Tasks registrieren
    scheduler.register_scheduler(
        scheduler_type="charts_updates",
        task_function=EnhancedSchedulerTasks.enhanced_charts_update_task(),
        interval_minutes=360,  # 6 Stunden
        dependencies=["price_tracker", "steam_wishlist_manager", "steam_charts_manager"],
        heartbeat_interval=45,  # 45 Sekunden (längere Tasks)
        show_progress_bar=True
    )
    
    scheduler.register_scheduler(
        scheduler_type="charts_prices",
        task_function=EnhancedSchedulerTasks.enhanced_charts_price_update_task(),
        interval_minutes=240,  # 4 Stunden
        dependencies=["price_tracker", "steam_wishlist_manager"],
        heartbeat_interval=30,
        show_progress_bar=True
    )
    
    scheduler.register_scheduler(
        scheduler_type="charts_cleanup",
        task_function=EnhancedSchedulerTasks.enhanced_charts_cleanup_task(),
        interval_minutes=1440,  # 24 Stunden
        dependencies=["price_tracker", "steam_wishlist_manager"],
        heartbeat_interval=60,  # 1 Minute (Cleanup Task)
        show_progress_bar=True
    )
    
    return scheduler

def test_enhanced_scheduler():
    """
    ENHANCED Test-Funktion für Scheduler mit Sign of Life Features
    """
    print("🧪 TESTE ENHANCED UNIVERSAL BACKGROUND SCHEDULER")
    print("=" * 60)
    print("💓 Mit Sign of Life: Ticker, Heartbeat, Fortschrittsbalken")
    print()
    
    try:
        # Enhanced Price Tracker Scheduler erstellen
        price_scheduler = create_enhanced_price_tracker_scheduler()
        print(f"✅ Enhanced Price Tracker Scheduler erstellt")
        
        # Enhanced Charts Scheduler erstellen
        charts_scheduler = create_enhanced_charts_scheduler()
        print(f"✅ Enhanced Charts Scheduler erstellt")
        
        # Status anzeigen
        price_status = price_scheduler.get_scheduler_status()
        charts_status = charts_scheduler.get_scheduler_status()
        
        print(f"\n📊 ENHANCED PRICE TRACKER STATUS:")
        print(f"   📝 Registrierte Scheduler: {price_status['total_registered']}")
        print(f"   🏃 Laufende Scheduler: {price_status['total_running']}")
        print(f"   💓 Sign of Life Features: Aktiviert")
        
        for name, scheduler_info in price_status['schedulers'].items():
            heartbeat = scheduler_info.get('heartbeat_interval', 30)
            progress = scheduler_info.get('show_progress_bar', True)
            print(f"      • {name}: Heartbeat {heartbeat}s, Progress Bar {'✅' if progress else '❌'}")
        
        print(f"\n📊 ENHANCED CHARTS STATUS:")
        print(f"   📝 Registrierte Scheduler: {charts_status['total_registered']}")
        print(f"   🏃 Laufende Scheduler: {charts_status['total_running']}")
        print(f"   💓 Sign of Life Features: Aktiviert")
        
        for name, scheduler_info in charts_status['schedulers'].items():
            heartbeat = scheduler_info.get('heartbeat_interval', 30)
            progress = scheduler_info.get('show_progress_bar', True)
            print(f"      • {name}: Heartbeat {heartbeat}s, Progress Bar {'✅' if progress else '❌'}")
        
        # Aufräumen
        price_scheduler.cleanup_all_files()
        charts_scheduler.cleanup_all_files()
        
        print(f"\n✅ Enhanced Scheduler-Test erfolgreich!")
        print("💡 Terminals zeigen jetzt kontinuierliche Aktivität!")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced Scheduler-Test fehlgeschlagen: {e}")
        return False

# Kompatibilitäts-Aliase für bestehenden Code
def create_price_tracker_scheduler():
    """Kompatibilitäts-Alias für Enhanced Version"""
    return create_enhanced_price_tracker_scheduler()

def create_charts_scheduler():
    """Kompatibilitäts-Alias für Enhanced Version"""
    return create_enhanced_charts_scheduler()

if __name__ == "__main__":
    # ENHANCED Test-Modus
    test_enhanced_scheduler()
