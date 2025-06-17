#!/usr/bin/env python3
"""
Enhanced Universal Background Scheduler v2.0 - Vollständig integrierte Version
ALLE ORIGINAL FEATURES + Enhanced Process Management mit automatischem Cleanup
Erweitert um vollständiges Process Tracking und automatisches Cleanup
"""

import os
import sys
import time
import subprocess
import threading
import json
import signal
import atexit
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
import logging

logger = logging.getLogger(__name__)

# =====================================================================
# ENHANCED PROCESS MANAGEMENT SYSTEM
# =====================================================================

class ProcessManager:
    """
    Zentrale Process-Verwaltung für automatisches Cleanup
    Verfolgt alle gestarteten Subprozesse und beendet sie automatisch
    """
    
    def __init__(self):
        self.tracked_processes = {}  # scheduler_id -> process_info
        self.process_lock = threading.Lock()
        self.cleanup_registered = False
        
        # Automatisches Cleanup beim Exit registrieren
        self._register_cleanup_handlers()
    
    def _register_cleanup_handlers(self):
        """Registriert Cleanup-Handler für verschiedene Exit-Szenarien"""
        if self.cleanup_registered:
            return
        
        # Normal exit
        atexit.register(self.cleanup_all_processes)
        
        # Signal handlers für Ctrl+C, etc.
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.cleanup_registered = True
        logger.info("✅ Enhanced Process Cleanup Handler registriert")
    
    def _signal_handler(self, signum, frame):
        """Handler für Signals - führt Cleanup aus"""
        logger.info(f"⚠️ Signal {signum} empfangen - führe Process Cleanup aus...")
        self.cleanup_all_processes()
        sys.exit(0)
    
    def register_process(self, scheduler_id: str, process: subprocess.Popen, 
                        scheduler_type: str, script_path: str):
        """
        Registriert einen Process für automatisches Cleanup
        
        Args:
            scheduler_id: Eindeutige ID des Schedulers
            process: Subprocess.Popen Objekt
            scheduler_type: Typ des Schedulers
            script_path: Pfad zum ausgeführten Script
        """
        with self.process_lock:
            self.tracked_processes[scheduler_id] = {
                'process': process,
                'pid': process.pid,
                'scheduler_type': scheduler_type,
                'script_path': script_path,
                'started_at': datetime.now().isoformat(),
                'parent_monitoring': True,
                'is_running': True
            }
        
        logger.info(f"✅ Process registriert: {scheduler_id} (PID: {process.pid})")
    
    def unregister_process(self, scheduler_id: str):
        """Entfernt Process aus Tracking"""
        with self.process_lock:
            if scheduler_id in self.tracked_processes:
                del self.tracked_processes[scheduler_id]
                logger.info(f"📝 Process unregistriert: {scheduler_id}")
    
    def is_process_running(self, scheduler_id: str) -> bool:
        """Prüft ob Process noch läuft"""
        with self.process_lock:
            if scheduler_id not in self.tracked_processes:
                return False
            
            process_info = self.tracked_processes[scheduler_id]
            process = process_info['process']
            
            try:
                # Prüfe Process-Status
                if process.poll() is None:
                    # Process läuft noch
                    process_info['is_running'] = True
                    return True
                else:
                    # Process ist beendet
                    process_info['is_running'] = False
                    return False
            except:
                process_info['is_running'] = False
                return False
    
    def stop_process(self, scheduler_id: str) -> bool:
        """
        Stoppt einen spezifischen Process
        
        Args:
            scheduler_id: ID des zu stoppenden Schedulers
            
        Returns:
            True wenn erfolgreich gestoppt
        """
        with self.process_lock:
            if scheduler_id not in self.tracked_processes:
                return False
            
            process_info = self.tracked_processes[scheduler_id]
            process = process_info['process']
            
            try:
                # Versuche graceful shutdown
                if os.name == 'nt':  # Windows
                    process.terminate()
                else:  # Unix/Linux/Mac
                    process.terminate()
                
                # Warte kurz auf graceful shutdown
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill falls nötig
                    process.kill()
                    process.wait()
                
                process_info['is_running'] = False
                logger.info(f"⏹️ Process gestoppt: {scheduler_id}")
                return True
                
            except Exception as e:
                logger.error(f"❌ Fehler beim Stoppen von Process {scheduler_id}: {e}")
                return False
    
    def cleanup_all_processes(self):
        """Stoppt alle getrackten Prozesse"""
        logger.info("🧹 Enhanced Process Cleanup gestartet...")
        
        with self.process_lock:
            active_processes = list(self.tracked_processes.keys())
        
        if not active_processes:
            logger.info("ℹ️ Keine aktiven Prozesse zu bereinigen")
            return
        
        stopped_count = 0
        for scheduler_id in active_processes:
            if self.stop_process(scheduler_id):
                stopped_count += 1
        
        logger.info(f"✅ Enhanced Process Cleanup abgeschlossen: {stopped_count} Prozesse gestoppt")
    
    def get_process_status(self) -> Dict:
        """Liefert Status aller getrackten Prozesse"""
        with self.process_lock:
            total_tracked = len(self.tracked_processes)
            running_processes = 0
            dead_processes = 0
            
            process_status = {}
            
            for scheduler_id, process_info in self.tracked_processes.items():
                is_running = self.is_process_running(scheduler_id)
                
                if is_running:
                    running_processes += 1
                else:
                    dead_processes += 1
                
                process_status[scheduler_id] = {
                    'pid': process_info['pid'],
                    'scheduler_type': process_info['scheduler_type'],
                    'started_at': process_info['started_at'],
                    'is_running': is_running,
                    'parent_monitoring': process_info.get('parent_monitoring', True)
                }
        
        return {
            'total_tracked': total_tracked,
            'running_processes': running_processes,
            'dead_processes': dead_processes,
            'processes': process_status
        }

# Globaler Process Manager
_global_process_manager = ProcessManager()

# =====================================================================
# ENHANCED BACKGROUND SCHEDULER
# =====================================================================

class EnhancedBackgroundScheduler:
    """
    Enhanced Background Scheduler mit automatischem Process Management
    Erweitert um vollständiges Process Tracking und automatisches Cleanup
    ALLE URSPRÜNGLICHEN FEATURES + Enhanced Features
    """
    
    def __init__(self, scheduler_name: str, base_config: Dict = None):
        """
        Initialisiert Enhanced Background Scheduler
        
        Args:
            scheduler_name: Eindeutiger Name für diesen Scheduler
            base_config: Basis-Konfiguration für den Scheduler
        """
        self.scheduler_name = scheduler_name
        self.base_config = base_config or {}
        
        # Scheduler-Status
        self.running_processes = {}  # scheduler_type -> process_info
        self.scheduler_configs = {}  # scheduler_type -> config
        
        # Process Manager Integration
        self.process_manager = _global_process_manager
        
        # Basis-Verzeichnisse
        self.temp_dir = Path("temp_schedulers")
        self.temp_dir.mkdir(exist_ok=True)
        
        # Python-Pfad für korrekte Imports
        self.project_root = Path.cwd()
        
        logger.info(f"✅ Enhanced Background Scheduler '{scheduler_name}' mit Process Management initialisiert")
    
    def register_scheduler(self, 
                          scheduler_type: str,
                          task_function: str,
                          interval_minutes: int,
                          task_config: Dict = None,
                          dependencies: List[str] = None,
                          heartbeat_interval: int = 30,
                          show_progress_bar: bool = True) -> bool:
        """
        Registriert einen neuen Scheduler-Typ mit Enhanced Features
        
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
            
            logger.info(f"✅ Enhanced Scheduler '{scheduler_type}' registriert (Intervall: {interval_minutes}min, Heartbeat: {heartbeat_interval}s)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Registrieren von Enhanced Scheduler '{scheduler_type}': {e}")
            return False
    
    def start_scheduler(self, scheduler_type: str, **kwargs) -> bool:
        """
        ENHANCED: Startet Scheduler mit automatischem Process Tracking
        
        Args:
            scheduler_type: Typ des zu startenden Schedulers
            **kwargs: Zusätzliche Parameter für den Scheduler
            
        Returns:
            True wenn erfolgreich gestartet
        """
        if scheduler_type not in self.scheduler_configs:
            logger.error(f"❌ Scheduler-Typ '{scheduler_type}' nicht registriert")
            return False
        
        scheduler_id = f"{self.scheduler_name}_{scheduler_type}"
        
        if self.process_manager.is_process_running(scheduler_id):
            logger.warning(f"⚠️ Scheduler '{scheduler_type}' läuft bereits")
            return True
        
        try:
            # Enhanced Scheduler-Script erstellen
            script_path = self._create_enhanced_scheduler_script_v2(scheduler_type, **kwargs)
            
            # Separaten Terminal-Prozess starten
            process = self._start_enhanced_terminal_process(script_path, scheduler_type)
            
            if process:
                # Process Manager Registration
                self.process_manager.register_process(
                    scheduler_id, process, scheduler_type, script_path
                )
                
                # Lokale Registration
                self.running_processes[scheduler_type] = {
                    'process': process,
                    'scheduler_id': scheduler_id,
                    'started_at': datetime.now().isoformat()
                }
                
                self.scheduler_configs[scheduler_type]['enabled'] = True
                self.scheduler_configs[scheduler_type]['started_at'] = datetime.now().isoformat()
                
                logger.info(f"✅ Enhanced Scheduler '{scheduler_type}' gestartet (PID: {process.pid})")
                return True
            else:
                logger.error(f"❌ Fehler beim Starten des Enhanced Terminal-Prozesses")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten von Enhanced Scheduler '{scheduler_type}': {e}")
            return False
    
    def stop_scheduler(self, scheduler_type: str) -> bool:
        """
        ENHANCED: Stoppt Scheduler mit automatischem Process Cleanup
        
        Args:
            scheduler_type: Typ des zu stoppenden Schedulers
            
        Returns:
            True wenn erfolgreich gestoppt
        """
        if scheduler_type not in self.scheduler_configs:
            logger.error(f"❌ Scheduler-Typ '{scheduler_type}' nicht registriert")
            return False
        
        scheduler_id = f"{self.scheduler_name}_{scheduler_type}"
        
        try:
            # Process Manager stoppen
            success = self.process_manager.stop_process(scheduler_id)
            
            # Lokale Registrierung aufräumen
            if scheduler_type in self.running_processes:
                del self.running_processes[scheduler_type]
            
            self.scheduler_configs[scheduler_type]['enabled'] = False
            self.scheduler_configs[scheduler_type]['stopped_at'] = datetime.now().isoformat()
            
            if success:
                logger.info(f"⏹️ Enhanced Scheduler '{scheduler_type}' gestoppt")
            else:
                logger.warning(f"⚠️ Enhanced Scheduler '{scheduler_type}' war bereits gestoppt")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Stoppen von Enhanced Scheduler '{scheduler_type}': {e}")
            return False
    
    def is_scheduler_running(self, scheduler_type: str) -> bool:
        """Prüft ob Scheduler läuft"""
        if scheduler_type not in self.scheduler_configs:
            return False
        
        scheduler_id = f"{self.scheduler_name}_{scheduler_type}"
        return self.process_manager.is_process_running(scheduler_id)
    
    def get_scheduler_status(self, scheduler_type: str = None) -> Dict:
        """
        Liefert Enhanced Status der Scheduler
        
        Args:
            scheduler_type: Spezifischer Scheduler oder None für alle
            
        Returns:
            Status-Dictionary mit Enhanced Informationen
        """
        if scheduler_type:
            # Status für spezifischen Scheduler
            if scheduler_type not in self.scheduler_configs:
                return {'error': f"Scheduler '{scheduler_type}' nicht registriert"}
            
            config = self.scheduler_configs[scheduler_type]
            scheduler_id = f"{self.scheduler_name}_{scheduler_type}"
            
            # Process Manager Status
            process_status = self.process_manager.get_process_status()
            process_info = process_status.get('processes', {}).get(scheduler_id, {})
            
            return {
                'scheduler_type': scheduler_type,
                'scheduler_id': scheduler_id,
                'registered': True,
                'enabled': config.get('enabled', False),
                'running': self.is_scheduler_running(scheduler_type),
                'interval_minutes': config.get('interval_minutes', 0),
                'heartbeat_interval': config.get('heartbeat_interval', 30),
                'show_progress_bar': config.get('show_progress_bar', True),
                'task_function': config.get('task_function', ''),
                'registered_at': config.get('registered_at', ''),
                'started_at': config.get('started_at', ''),
                'stopped_at': config.get('stopped_at', ''),
                'process_info': process_info
            }
        else:
            # Status für alle Scheduler
            process_status = self.process_manager.get_process_status()
            
            all_status = {
                'scheduler_name': self.scheduler_name,
                'total_registered': len(self.scheduler_configs),
                'total_running': len([st for st in self.scheduler_configs if self.is_scheduler_running(st)]),
                'process_manager_status': process_status,
                'schedulers': {}
            }
            
            for st in self.scheduler_configs:
                all_status['schedulers'][st] = self.get_scheduler_status(st)
            
            return all_status
    
    def cleanup_all_processes(self):
        """Stoppt alle Scheduler und räumt Prozesse auf"""
        logger.info(f"🧹 Enhanced Cleanup für Scheduler '{self.scheduler_name}'...")
        
        # Alle Scheduler stoppen
        for scheduler_type in list(self.scheduler_configs.keys()):
            if self.is_scheduler_running(scheduler_type):
                self.stop_scheduler(scheduler_type)
        
        # Temporäre Dateien aufräumen
        self.cleanup_all_files()
        
        logger.info(f"✅ Enhanced Cleanup abgeschlossen für '{self.scheduler_name}'")
    
    def cleanup_all_files(self):
        """Räumt temporäre Scheduler-Dateien auf"""
        try:
            if self.temp_dir.exists():
                for file_path in self.temp_dir.glob(f"*{self.scheduler_name}*"):
                    try:
                        file_path.unlink()
                    except:
                        pass  # Ignoriere Fehler beim Löschen
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Aufräumen der Dateien: {e}")
    
    def _create_enhanced_scheduler_script_v2(self, scheduler_type: str, **kwargs) -> str:
        """
        ENHANCED v2: Erstellt Script mit Heartbeat-System für automatisches Cleanup
        
        Args:
            scheduler_type: Typ des Schedulers
            **kwargs: Zusätzliche Parameter
            
        Returns:
            Pfad zum erstellten Enhanced Script
        """
        config = self.scheduler_configs[scheduler_type]
        interval_minutes = config['interval_minutes']
        heartbeat_interval = config.get('heartbeat_interval', 30)
        show_progress_bar = config.get('show_progress_bar', True)
        
        # ENHANCED v2: Script mit Parent-Process-Monitoring
        script_content = f'''#!/usr/bin/env python3
"""
ENHANCED Background Scheduler v2.0: {scheduler_type}
Mit Parent-Process-Monitoring für automatisches Cleanup
Scheduler: {self.scheduler_name}
ENHANCED mit Sign of Life und Auto-Exit wenn Parent stirbt
"""

import sys
import time
import json
import threading
import os
import psutil
from datetime import datetime, timedelta
from pathlib import Path

# Aktuelles Verzeichnis zum Python-Pfad hinzufügen
project_root = Path("{self.project_root}")
sys.path.insert(0, str(project_root))

# Parent Process ID für Monitoring
PARENT_PID = {os.getpid()}

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
# ENHANCED v2: PARENT PROCESS MONITORING
# =====================================================================

class ParentMonitor:
    """Überwacht Parent-Process und beendet sich automatisch falls Parent stirbt"""
    
    def __init__(self, parent_pid):
        self.parent_pid = parent_pid
        self.running = True
        self.monitor_thread = None
        self.check_interval = 5  # Prüfe alle 5 Sekunden
        
    def start_monitoring(self):
        """Startet Parent-Process-Monitoring"""
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print(f"👁️ Parent-Process-Monitoring gestartet (Parent PID: {{self.parent_pid}})")
        
    def stop_monitoring(self):
        """Stoppt Monitoring"""
        self.running = False
        
    def _monitor_loop(self):
        """Hauptschleife für Parent-Monitoring"""
        while self.running:
            try:
                # Prüfe ob Parent-Process noch existiert
                if not psutil.pid_exists(self.parent_pid):
                    print(f"\\n💀 Parent-Process {{self.parent_pid}} ist nicht mehr aktiv!")
                    print("⏹️ Beende Scheduler automatisch...")
                    os._exit(0)  # Forciere Exit
                    
                # Zusätzlich: Prüfe ob Parent-Process ein Python-Prozess ist
                try:
                    parent_proc = psutil.Process(self.parent_pid)
                    if not any('python' in cmd.lower() for cmd in parent_proc.cmdline()):
                        print(f"\\n⚠️ Parent-Process {{self.parent_pid}} ist kein Python-Prozess mehr!")
                        print("⏹️ Beende Scheduler automatisch...")
                        os._exit(0)
                except psutil.NoSuchProcess:
                    print(f"\\n💀 Parent-Process {{self.parent_pid}} nicht gefunden!")
                    print("⏹️ Beende Scheduler automatisch...")
                    os._exit(0)
                    
                time.sleep(self.check_interval)
                
            except Exception as e:
                print(f"\\n❌ Fehler beim Parent-Monitoring: {{e}}")
                time.sleep(self.check_interval)

# =====================================================================
# ENHANCED v2: SIGN OF LIFE SYSTEM
# =====================================================================

class EnhancedSignOfLife:
    """Enhanced Sign of Life mit Ticker und Status-Anzeigen"""
    
    def __init__(self, scheduler_type, heartbeat_interval=30):
        self.scheduler_type = scheduler_type
        self.heartbeat_interval = heartbeat_interval
        self.running = False
        self.ticker_thread = None
        self.last_heartbeat = datetime.now()
        
        # Ticker-Zeichen für Animation
        self.ticker_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.ticker_index = 0
        
    def start_ticker(self):
        """Startet Sign of Life Ticker"""
        self.running = True
        self.ticker_thread = threading.Thread(target=self._ticker_loop, daemon=True)
        self.ticker_thread.start()
        
    def stop_ticker(self):
        """Stoppt Ticker"""
        self.running = False
        
    def _ticker_loop(self):
        """Hauptschleife für Sign of Life Ticker"""
        while self.running:
            try:
                # Ticker-Animation
                ticker = self.ticker_chars[self.ticker_index % len(self.ticker_chars)]
                self.ticker_index += 1
                
                # Status-Info
                now = datetime.now()
                uptime = now - self.last_heartbeat
                uptime_str = f"{{int(uptime.total_seconds())}}s"
                
                # Parent-Status prüfen
                parent_status = "✅" if psutil.pid_exists(PARENT_PID) else "💀"
                
                # Status-Zeile ausgeben (überschreibt vorherige Zeile)
                status_line = f"\\r{{ticker}} {{self.scheduler_type}} | Uptime: {{uptime_str}} | Parent: {{parent_status}} | {{now.strftime('%H:%M:%S')}}"
                print(status_line, end='', flush=True)
                
                time.sleep(1)  # 1 Sekunde Ticker-Intervall
                
            except Exception as e:
                time.sleep(1)

# =====================================================================
# ENHANCED SLEEP FUNCTION
# =====================================================================

def enhanced_sleep_with_monitoring(seconds):
    """Sleep-Funktion mit Parent-Monitoring"""
    sleep_interval = 5  # Prüfe alle 5 Sekunden
    total_slept = 0
    
    while total_slept < seconds:
        # Prüfe Parent-Process
        if not psutil.pid_exists(PARENT_PID):
            print(f"\\n💀 Parent-Process {{PARENT_PID}} gestorben während Sleep!")
            os._exit(0)
        
        # Sleep in kleinen Intervallen
        current_sleep = min(sleep_interval, seconds - total_slept)
        time.sleep(current_sleep)
        total_slept += current_sleep

# =====================================================================
# TASK EXECUTION
# =====================================================================

def execute_enhanced_task():
    """Führt die Enhanced Task aus"""
    try:
        # Task-Function ausführen
{self._format_task_function_enhanced(config['task_function'])}
        
        return True
        
    except Exception as e:
        print(f"\\n❌ Fehler bei Task-Ausführung: {{e}}")
        import traceback
        traceback.print_exc()
        return False

# =====================================================================
# ENHANCED MAIN LOOP
# =====================================================================

print("🚀 ENHANCED BACKGROUND SCHEDULER v2.0")
print(f"📊 Scheduler: {{SCHEDULER_NAME}}")
print(f"🎯 Task: {{SCHEDULER_TYPE}}")
print(f"⏰ Intervall: {{INTERVAL_MINUTES}} Minuten")
print(f"💓 Heartbeat: {{HEARTBEAT_INTERVAL}} Sekunden")
print(f"👁️ Parent-Monitoring: AKTIVIERT")
print("=" * 60)

# Dependencies importieren
{self._generate_import_statements_enhanced(config.get('dependencies', []))}

# Enhanced Parent-Monitor starten
parent_monitor = ParentMonitor(PARENT_PID)
parent_monitor.start_monitoring()

# Enhanced Sign of Life starten
enhanced_sign_of_life = EnhancedSignOfLife(SCHEDULER_TYPE, HEARTBEAT_INTERVAL)
enhanced_sign_of_life.start_ticker()

# Erste Ausführung
print(f"\\n🔄 Erste Ausführung von {{SCHEDULER_TYPE}}...")
execute_enhanced_task()

# Enhanced Scheduler Loop
cycle = 1
try:
    while True:
        # Parent-Process-Check
        if not psutil.pid_exists(PARENT_PID):
            print(f"\\n💀 Parent-Process {{PARENT_PID}} ist gestorben!")
            break
        
        # Sign of Life temporär stoppen für Task-Ausführung
        enhanced_sign_of_life.stop_ticker()
        
        print(f"\\n🔄 === ENHANCED ZYKLUS {{cycle}} - {{datetime.now().strftime('%H:%M:%S')}} ===")
        
        success = execute_enhanced_task()
        
        if success:
            print(f"✅ Enhanced Task erfolgreich ausgeführt")
        else:
            print(f"❌ Enhanced Task fehlgeschlagen")
        
        print(f"⏳ Nächste Ausführung in {{INTERVAL_MINUTES}} Minuten...")
        print(f"👁️ Parent-Process {{PARENT_PID}} Status: {{'AKTIV' if psutil.pid_exists(PARENT_PID) else 'TOT'}}")
        
        # Enhanced Sleep mit Parent-Monitoring
        enhanced_sleep_with_monitoring(INTERVAL_MINUTES * 60)
        
        # Sign of Life neu starten
        enhanced_sign_of_life.start_ticker()
        
        cycle += 1

except KeyboardInterrupt:
    print("\\n⏹️ Enhanced Scheduler gestoppt durch Benutzer")
except ImportError as e:
    print(f"❌ Import-Fehler: {{e}}")
except Exception as e:
    print(f"❌ Unerwarteter Fehler: {{e}}")
    import traceback
    traceback.print_exc()
finally:
    parent_monitor.stop_monitoring()
    enhanced_sign_of_life.stop_ticker()
    print("\\n👋 Enhanced Background Scheduler v2.0 beendet")
'''
        
        # Script-Datei erstellen
        script_filename = f"enhanced_scheduler_{self.scheduler_name}_{scheduler_type}_v2.py"
        script_path = self.temp_dir / script_filename
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        return str(script_path)
    
    def _generate_import_statements_enhanced(self, dependencies: List[str]) -> str:
        """Enhanced Import-Statements mit besserer Fehlerbehandlung"""
        if not dependencies:
            return "    # Keine zusätzlichen Dependencies"
        
        imports = []
        for dep in dependencies:
            if '.' in dep:
                module, submodule = dep.rsplit('.', 1)
                imports.append(f"""    try:
        from {module} import {submodule}
        print(f"✅ Enhanced Import: {submodule} from {module}")
    except ImportError as e:
        print(f"❌ Enhanced Import Failed: {submodule} from {module}: {{e}}")
        raise""")
            else:
                imports.append(f"""    try:
        import {dep}
        print(f"✅ Enhanced Import: {dep}")
    except ImportError as e:
        print(f"❌ Enhanced Import Failed: {dep}: {{e}}")
        raise""")
        
        return '\n'.join(imports)
    
    def _format_task_function_enhanced(self, task_function: str) -> str:
        """Enhanced Task-Funktion Formatierung"""
        task_function = task_function.strip()
        lines = task_function.split('\n')
        indented_lines = []
        
        for line in lines:
            if line.strip():
                indented_lines.append('            ' + line.lstrip())
            else:
                indented_lines.append('')
        
        return '\n'.join(indented_lines)
    
    def _start_enhanced_terminal_process(self, script_path: str, scheduler_type: str) -> Optional[subprocess.Popen]:
        """
        ENHANCED: Startet Terminal mit verbessertem Process Management
        
        Args:
            script_path: Pfad zum Python-Script
            scheduler_type: Typ des Schedulers
            
        Returns:
            Subprocess.Popen Objekt oder None
        """
        terminal_title = f"🔄 {self.scheduler_name}_{scheduler_type} - ENHANCED v2.0"
        
        try:
            if os.name == 'nt':  # Windows
                batch_content = f'''@echo off
title {terminal_title}
color 0A
echo 🚀 ENHANCED Background Scheduler v2.0
echo ================================================================
echo 📊 Scheduler: {self.scheduler_name}
echo 🎯 Task: {scheduler_type}
echo 👁️ Parent-Monitoring: AKTIVIERT
echo 💓 Sign of Life: AKTIVIERT
echo ⏰ Zeit: %date% %time%
echo ================================================================
echo 💡 Automatisches Cleanup wenn Hauptprogramm beendet wird
echo 💡 Parent-Process-Monitoring für saubere Beendigung
echo.
cd /d "{self.project_root}"
python "{script_path}"
echo.
echo 💡 Enhanced Background Scheduler beendet
pause
'''
                
                batch_filename = f"start_{self.scheduler_name}_{scheduler_type}_enhanced.bat"
                batch_path = self.temp_dir / batch_filename
                
                with open(batch_path, 'w', encoding='utf-8') as f:
                    f.write(batch_content)
                
                # Neues Terminal-Fenster starten
                process = subprocess.Popen(
                    ['cmd', '/c', 'start', '/wait', str(batch_path)],
                    cwd=str(self.project_root),
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                
            else:  # Unix/Linux/macOS
                # Unix-Terminal-Script
                shell_content = f'''#!/bin/bash
echo "🚀 ENHANCED Background Scheduler v2.0"
echo "================================================================"
echo "📊 Scheduler: {self.scheduler_name}"
echo "🎯 Task: {scheduler_type}"
echo "👁️ Parent-Monitoring: AKTIVIERT"
echo "💓 Sign of Life: AKTIVIERT"
echo "⏰ Zeit: $(date)"
echo "================================================================"
echo "💡 Automatisches Cleanup wenn Hauptprogramm beendet wird"
echo "💡 Parent-Process-Monitoring für saubere Beendigung"
echo
cd "{self.project_root}"
python3 "{script_path}"
echo
echo "💡 Enhanced Background Scheduler beendet"
read -p "Drücke Enter zum Schließen..."
'''
                
                shell_filename = f"start_{self.scheduler_name}_{scheduler_type}_enhanced.sh"
                shell_path = self.temp_dir / shell_filename
                
                with open(shell_path, 'w', encoding='utf-8') as f:
                    f.write(shell_content)
                
                # Ausführbar machen
                os.chmod(shell_path, 0o755)
                
                # Terminal starten (verschiedene Optionen je nach System)
                terminal_commands = [
                    ['gnome-terminal', '--title', terminal_title, '--', 'bash', str(shell_path)],
                    ['xterm', '-title', terminal_title, '-e', f'bash {shell_path}'],
                    ['konsole', '--title', terminal_title, '-e', f'bash {shell_path}'],
                    ['xfce4-terminal', '--title', terminal_title, '-e', f'bash {shell_path}'],
                    ['mate-terminal', '--title', terminal_title, '-e', f'bash {shell_path}'],
                    ['terminal', '--title', terminal_title, '-e', f'bash {shell_path}'],  # macOS
                ]
                
                process = None
                for cmd in terminal_commands:
                    try:
                        process = subprocess.Popen(
                            cmd,
                            cwd=str(self.project_root),
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        break
                    except (FileNotFoundError, subprocess.SubprocessError):
                        continue
                
                if process is None:
                    logger.warning("⚠️ Kein geeignetes Terminal gefunden, starte im Hintergrund")
                    process = subprocess.Popen(
                        ['python3', str(script_path)],
                        cwd=str(self.project_root)
                    )
            
            # Kurz warten um sicherzustellen dass Prozess gestartet ist
            time.sleep(1)
            
            return process
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten des Enhanced Terminal-Prozesses: {e}")
            return None

# =====================================================================
# ORIGINAL BACKGROUND SCHEDULER (für Kompatibilität)
# =====================================================================

class BackgroundScheduler(EnhancedBackgroundScheduler):
    """
    Kompatibilitäts-Wrapper für ursprüngliche BackgroundScheduler API
    Leitet alle Aufrufe an EnhancedBackgroundScheduler weiter
    """
    
    def __init__(self, scheduler_name: str, base_config: Dict = None):
        """Initialisiert als Enhanced Version"""
        super().__init__(scheduler_name, base_config)
        logger.info(f"✅ BackgroundScheduler '{scheduler_name}' initialisiert (Enhanced Mode)")

# =====================================================================
# ENHANCED SCHEDULER TASKS
# =====================================================================

class EnhancedSchedulerTasks:
    """
    Enhanced Task-Definitionen für alle Background-Operationen
    ALLE URSPRÜNGLICHEN TASKS + Enhanced Features
    """
    
    @staticmethod
    def enhanced_price_tracking_task():
        """Enhanced Task für Preis-Tracking"""
        return '''
# Enhanced Price Tracking Task
print("💰 Enhanced Preis-Tracking Task gestartet...")

from price_tracker import create_price_tracker
from steam_wishlist_manager import load_api_key_from_env

api_key = load_api_key_from_env()
tracker = create_price_tracker(api_key=api_key, enable_charts=False)

print("🔄 Starte Enhanced Batch-Verarbeitung aller Apps...")
print(f"⏰ Start: {datetime.now().strftime('%H:%M:%S')}")

# Nur Apps verarbeiten die älter als 6 Stunden sind
result = tracker.process_all_pending_apps_optimized(hours_threshold=6)

print(f"✅ Enhanced Preis-Update abgeschlossen:")
print(f"   📊 {result['total_successful']}/{result['total_apps']} Apps aktualisiert")
print(f"   ⏱️ Dauer: {result['total_duration']:.1f}s")
print(f"   ⚡ Geschwindigkeit: {result.get('apps_per_second', 0):.1f} Apps/s")
print(f"🏁 Enhanced Task abgeschlossen um {datetime.now().strftime('%H:%M:%S')}")
'''
    
    @staticmethod
    def enhanced_name_update_task():
        """Enhanced Task für Namen-Updates"""
        return '''
# Enhanced Name Update Task
print("🔤 Enhanced Namen-Update Task gestartet...")

from price_tracker import create_price_tracker
from steam_wishlist_manager import load_api_key_from_env

api_key = load_api_key_from_env()
if not api_key:
    print("❌ Kein Steam API Key verfügbar")
    return

tracker = create_price_tracker(api_key=api_key, enable_charts=False)

print("🔄 Suche Apps mit generischen Namen...")
generic_apps = tracker.get_apps_with_generic_names()

if generic_apps:
    app_ids = [app['steam_app_id'] for app in generic_apps[:50]]  # Max 50 pro Durchlauf
    print(f"🔄 Aktualisiere Namen für {len(app_ids)} Apps...")
    
    result = tracker.update_app_names_from_steam(app_ids, api_key)
    
    print(f"✅ Enhanced Namen-Update abgeschlossen:")
    print(f"   🔤 {result['updated']}/{result['total']} Namen aktualisiert")
    print(f"   ⏭️ {result['skipped']} übersprungen")
    print(f"   ❌ {result['failed']} fehlgeschlagen")
else:
    print("✅ Keine Apps mit generischen Namen gefunden")

print(f"🏁 Enhanced Namen-Update abgeschlossen um {datetime.now().strftime('%H:%M:%S')}")
'''
    
    @staticmethod
    def enhanced_charts_update_task():
        """Enhanced Task für Charts-Updates"""
        return '''
# Enhanced Charts Update Task
print("📊 Enhanced Charts-Update Task gestartet...")

from price_tracker import create_price_tracker
from steam_wishlist_manager import load_api_key_from_env

api_key = load_api_key_from_env()
if not api_key:
    print("❌ Kein Steam API Key verfügbar")
    return

tracker = create_price_tracker(api_key=api_key, enable_charts=True)

if not tracker.charts_enabled:
    print("❌ Charts nicht verfügbar")
    return

print("🔄 Starte Enhanced Steam Charts Update...")
print(f"⏰ Start: {datetime.now().strftime('%H:%M:%S')}")

result = tracker.charts_manager.update_all_charts()

if result.get('success'):
    print(f"✅ Enhanced Charts-Update abgeschlossen:")
    print(f"   📊 {result.get('updated_charts', 0)} Charts verarbeitet")
    print(f"   🎮 {result.get('new_games', 0)} neue Spiele gefunden")
    print(f"   ⏱️ Dauer: {result.get('duration', 0):.1f}s")
else:
    print(f"❌ Enhanced Charts-Update fehlgeschlagen: {result.get('error')}")

print(f"🏁 Enhanced Charts-Update abgeschlossen um {datetime.now().strftime('%H:%M:%S')}")
'''
    
    @staticmethod
    def enhanced_charts_price_update_task():
        """Enhanced Task für Charts-Preise"""
        return '''
# Enhanced Charts Price Update Task
print("💰 Enhanced Charts-Preise Task gestartet...")

from price_tracker import create_price_tracker
from steam_wishlist_manager import load_api_key_from_env

api_key = load_api_key_from_env()
tracker = create_price_tracker(api_key=api_key, enable_charts=True)

if not tracker.charts_enabled:
    print("❌ Charts nicht verfügbar")
    return

print("🔄 Starte Enhanced Charts-Preise Update...")
print(f"⏰ Start: {datetime.now().strftime('%H:%M:%S')}")

result = tracker.charts_manager.update_charts_prices()

if result.get('success'):
    print(f"✅ Enhanced Charts-Preise Update abgeschlossen:")
    print(f"   💰 {result.get('updated_prices', 0)} Spiele-Preise aktualisiert")
    print(f"   ⏱️ Dauer: {result.get('duration', 0):.1f}s")
else:
    print(f"❌ Enhanced Charts-Preise Update fehlgeschlagen: {result.get('error')}")

print(f"🏁 Enhanced Charts-Preise Update abgeschlossen um {datetime.now().strftime('%H:%M:%S')}")
'''
    
    @staticmethod
    def enhanced_charts_cleanup_task():
        """Enhanced Task für Charts-Cleanup"""
        return '''
# Enhanced Charts Cleanup Task
print("🧹 Enhanced Charts-Cleanup Task gestartet...")

from price_tracker import create_price_tracker
from steam_wishlist_manager import load_api_key_from_env

api_key = load_api_key_from_env()
tracker = create_price_tracker(api_key=api_key, enable_charts=True)

if not tracker.charts_enabled:
    print("❌ Charts nicht verfügbar")
    return

print("🧹 Starte umfassendes Enhanced Charts-Cleanup...")
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
    print(f"🎉 Enhanced Cleanup abgeschlossen: {total_cleaned} Einträge bereinigt")
else:
    print("✅ Enhanced Cleanup abgeschlossen - alles bereits sauber")

print(f"🏁 Enhanced Charts-Cleanup abgeschlossen um {datetime.now().strftime('%H:%M:%S')}")
'''

# =====================================================================
# ENHANCED CONVENIENCE FUNCTIONS
# =====================================================================

def create_enhanced_price_tracker_scheduler() -> EnhancedBackgroundScheduler:
    """
    Erstellt ENHANCED BackgroundScheduler für Price Tracker mit Sign of Life Features
    
    Returns:
        Konfigurierter EnhancedBackgroundScheduler mit Enhanced Features
    """
    scheduler = EnhancedBackgroundScheduler(
        scheduler_name="PriceTracker",
        base_config={
            "rate_limit_seconds": 1.5,
            "batch_size": 50,
            "max_retries": 3,
            "enhanced_features": True,
            "version": "2.0"
        }
    )
    
    # Enhanced Tasks registrieren
    scheduler.register_scheduler(
        scheduler_type="price_updates",
        task_function=EnhancedSchedulerTasks.enhanced_price_tracking_task(),
        interval_minutes=360,
        dependencies=["price_tracker", "steam_wishlist_manager"],
        heartbeat_interval=30,
        show_progress_bar=True
    )
    
    scheduler.register_scheduler(
        scheduler_type="name_updates", 
        task_function=EnhancedSchedulerTasks.enhanced_name_update_task(),
        interval_minutes=30,
        dependencies=["price_tracker", "steam_wishlist_manager"],
        heartbeat_interval=20,
        show_progress_bar=True
    )
    
    return scheduler

def create_enhanced_charts_scheduler() -> EnhancedBackgroundScheduler:
    """Erstellt Enhanced BackgroundScheduler für Charts"""
    scheduler = EnhancedBackgroundScheduler(
        scheduler_name="Charts",
        base_config={
            "steam_api_rate_limit": 1.0,
            "max_charts_per_update": 100,
            "enhanced_features": True,
            "version": "2.0"
        }
    )
    
    # Enhanced Charts Tasks registrieren
    scheduler.register_scheduler(
        scheduler_type="charts_updates",
        task_function=EnhancedSchedulerTasks.enhanced_charts_update_task(),
        interval_minutes=360,
        dependencies=["price_tracker", "steam_wishlist_manager", "steam_charts_manager"],
        heartbeat_interval=45,
        show_progress_bar=True
    )
    
    scheduler.register_scheduler(
        scheduler_type="charts_prices",
        task_function=EnhancedSchedulerTasks.enhanced_charts_price_update_task(),
        interval_minutes=240,
        dependencies=["price_tracker", "steam_wishlist_manager"],
        heartbeat_interval=30,
        show_progress_bar=True
    )
    
    scheduler.register_scheduler(
        scheduler_type="charts_cleanup",
        task_function=EnhancedSchedulerTasks.enhanced_charts_cleanup_task(),
        interval_minutes=1440,
        dependencies=["price_tracker", "steam_wishlist_manager"],
        heartbeat_interval=60,
        show_progress_bar=True
    )
    
    return scheduler

# Kompatibilitäts-Aliase für ursprünglichen Code
def create_price_tracker_scheduler():
    """Kompatibilitäts-Alias für Enhanced Version"""
    return create_enhanced_price_tracker_scheduler()

def create_charts_scheduler():
    """Kompatibilitäts-Alias für Enhanced Version"""
    return create_enhanced_charts_scheduler()

# =====================================================================
# ENHANCED PROCESS MANAGEMENT TERMINAL
# =====================================================================

def create_process_management_terminal() -> bool:
    """
    Startet Enhanced Process Management Terminal für zentrale Kontrolle
    
    Returns:
        True wenn erfolgreich gestartet
    """
    try:
        terminal_script = '''#!/usr/bin/env python3
"""
Enhanced Process Management Terminal v2.0
Zentrale Kontrolle für alle Background-Scheduler
"""

import os
import sys
import time
import psutil
from datetime import datetime
from pathlib import Path

# Project root hinzufügen
project_root = Path.cwd()
sys.path.insert(0, str(project_root))

def show_process_status():
    """Zeigt aktuellen Process-Status"""
    try:
        from background_scheduler import _global_process_manager
        
        status = _global_process_manager.get_process_status()
        
        print("\\n📊 ENHANCED PROCESS MANAGEMENT TERMINAL v2.0")
        print("=" * 60)
        print(f"⏰ Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 Getrackte Prozesse: {status['total_tracked']}")
        print(f"✅ Laufende Prozesse: {status['running_processes']}")
        print(f"💀 Tote Prozesse: {status['dead_processes']}")
        
        if status['processes']:
            print("\\n📋 AKTIVE ENHANCED PROZESSE:")
            for scheduler_id, proc_info in status['processes'].items():
                status_icon = "✅" if proc_info['is_running'] else "💀"
                print(f"   {status_icon} {scheduler_id}")
                print(f"      PID: {proc_info['pid']}")
                print(f"      Typ: {proc_info['scheduler_type']}")
                print(f"      Gestartet: {proc_info['started_at'][:19]}")
                print(f"      Parent-Monitoring: {'✅' if proc_info.get('parent_monitoring') else '❌'}")
                print()
        else:
            print("\\n💡 Keine aktiven Enhanced Prozesse")
            
        return status
        
    except Exception as e:
        print(f"❌ Fehler beim Laden des Process-Status: {e}")
        return None

def main():
    """Hauptschleife des Process Management Terminals"""
    print("🚀 ENHANCED PROCESS MANAGEMENT TERMINAL")
    print("💡 Drücke Ctrl+C zum Beenden")
    
    try:
        while True:
            # Status anzeigen
            status = show_process_status()
            
            if status and status['processes']:
                print("\\n🔧 VERFÜGBARE AKTIONEN:")
                print("1. Status aktualisieren")
                print("2. Prozess beenden")
                print("3. Alle Prozesse beenden")
                print("4. System-Ressourcen anzeigen")
                print("5. Beenden")
                
                # Automatische Aktualisierung alle 10 Sekunden
                print("\\n⏳ Automatische Aktualisierung in 10 Sekunden...")
                time.sleep(10)
                
                # Clear screen
                os.system('cls' if os.name == 'nt' else 'clear')
            else:
                print("\\n💤 Keine aktiven Prozesse - warte 5 Sekunden...")
                time.sleep(5)
                os.system('cls' if os.name == 'nt' else 'clear')
                
    except KeyboardInterrupt:
        print("\\n👋 Enhanced Process Management Terminal beendet")

if __name__ == "__main__":
    main()
'''
        
        # Script in temporäre Datei schreiben
        temp_dir = Path("temp_schedulers")
        temp_dir.mkdir(exist_ok=True)
        
        script_path = temp_dir / "enhanced_process_management_terminal.py"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(terminal_script)
        
        # Terminal starten
        terminal_title = "🔧 Enhanced Process Management Terminal v2.0"
        
        if os.name == 'nt':  # Windows
            batch_content = f'''@echo off
title {terminal_title}
color 0B
cd /d "{Path.cwd()}"
python "{script_path}"
pause
'''
            batch_path = temp_dir / "start_process_management.bat"
            with open(batch_path, 'w', encoding='utf-8') as f:
                f.write(batch_content)
            
            subprocess.Popen(
                ['cmd', '/c', 'start', str(batch_path)],
                cwd=str(Path.cwd()),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
        else:  # Unix/Linux/macOS
            shell_content = f'''#!/bin/bash
echo "🔧 {terminal_title}"
cd "{Path.cwd()}"
python3 "{script_path}"
read -p "Drücke Enter zum Schließen..."
'''
            shell_path = temp_dir / "start_process_management.sh"
            with open(shell_path, 'w', encoding='utf-8') as f:
                f.write(shell_content)
            
            os.chmod(shell_path, 0o755)
            
            # Terminal-Kommandos versuchen
            terminal_commands = [
                ['gnome-terminal', '--title', terminal_title, '--', 'bash', str(shell_path)],
                ['xterm', '-title', terminal_title, '-e', f'bash {shell_path}'],
                ['konsole', '--title', terminal_title, '-e', f'bash {shell_path}'],
            ]
            
            for cmd in terminal_commands:
                try:
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    break
                except (FileNotFoundError, subprocess.SubprocessError):
                    continue
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Starten des Process Management Terminals: {e}")
        return False

# =====================================================================
# ENHANCED TEST FUNCTIONS
# =====================================================================

def test_enhanced_scheduler_v2():
    """Test-Funktion für Enhanced Scheduler v2.0"""
    print("🧪 TESTE ENHANCED UNIVERSAL BACKGROUND SCHEDULER v2.0")
    print("=" * 70)
    print("💡 Features: Automatisches Cleanup, Parent-Monitoring, Process Management")
    print()
    
    try:
        # Enhanced Scheduler testen
        price_scheduler = create_enhanced_price_tracker_scheduler()
        charts_scheduler = create_enhanced_charts_scheduler()
        
        print("✅ Enhanced Scheduler erstellt")
        
        # Process Manager Status
        process_status = _global_process_manager.get_process_status()
        print(f"📊 Process Manager: {process_status['total_tracked']} getrackte Prozesse")
        
        # Management Terminal starten
        if create_process_management_terminal():
            print("✅ Process Management Terminal gestartet")
        
        print("\n🎉 Enhanced Scheduler v2.0 Test erfolgreich!")
        print("💡 Automatisches Cleanup beim Hauptprogramm-Exit aktiviert!")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced Scheduler v2.0 Test fehlgeschlagen: {e}")
        return False

# Kompatibilitäts-Test-Funktion
def test_enhanced_scheduler():
    """Kompatibilitäts-Alias für Enhanced Test"""
    return test_enhanced_scheduler_v2()

if __name__ == "__main__":
    test_enhanced_scheduler_v2()