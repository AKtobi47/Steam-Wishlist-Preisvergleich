#!/usr/bin/env python3
"""
Enhanced Universal Background Scheduler v2.0 mit Process Management
Steam Price Tracker - Separate Terminal-Execution für alle Background-Tasks
Unterstützt Parent-Process-Monitoring, Sign of Life und Process Management Terminal
"""

import subprocess
import threading
import time
import logging
import json
import signal
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from queue import Queue, Empty
import psutil

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SchedulerTask:
    """Enhanced Task Definition für Background Scheduler"""
    scheduler_type: str
    task_function: str
    interval_minutes: int
    task_config: Dict = None
    dependencies: List[str] = None
    heartbeat_interval: int = 60  # Sekunden
    show_progress_bar: bool = False
    last_run: datetime = None
    next_run: datetime = None
    running: bool = False
    process: subprocess.Popen = None
    heartbeat_file: Path = None

class EnhancedBackgroundScheduler:
    """
    Enhanced Universal Background Scheduler v2.0
    Führt alle Tasks in separaten Terminal-Prozessen aus
    Mit Parent-Process-Monitoring und Sign of Life
    """
    
    def __init__(self, scheduler_name: str = "BackgroundScheduler", base_config: Dict = None):
        """
        Initialisiert Enhanced Background Scheduler
        
        Args:
            scheduler_name: Name des Schedulers
            base_config: Basis-Konfiguration für alle Tasks
        """
        self.scheduler_name = scheduler_name
        self.base_config = base_config or {}
        self.tasks: Dict[str, SchedulerTask] = {}
        self.running = False
        self.scheduler_thread = None
        self.stop_event = threading.Event()
        
        # Process Management
        self.processes: Dict[str, subprocess.Popen] = {}
        self.heartbeat_dir = Path("heartbeats")
        self.heartbeat_dir.mkdir(exist_ok=True)
        
        # Sign of Life Monitoring
        self.parent_pid = os.getpid()
        self.monitoring_active = False
        self.monitoring_thread = None
        
        logger.info(f"✅ Enhanced Background Scheduler '{scheduler_name}' v2.0 initialisiert")
    
    def register_scheduler(self,
                          scheduler_type: str,
                          task_function: str,
                          interval_minutes: int,
                          task_config: Dict = None,
                          dependencies: List[str] = None,
                          heartbeat_interval: int = 60,
                          show_progress_bar: bool = False):
        """
        Registriert einen neuen Task im Scheduler
        
        Args:
            scheduler_type: Eindeutiger Task-Typ
            task_function: Task-Funktion als String oder Callable
            interval_minutes: Ausführungsintervall in Minuten
            task_config: Task-spezifische Konfiguration
            dependencies: Erforderliche Module/Bibliotheken
            heartbeat_interval: Herzschlag-Intervall in Sekunden
            show_progress_bar: Ob Progress Bar angezeigt werden soll
        """
        # Heartbeat-Datei für Task
        heartbeat_file = self.heartbeat_dir / f"{scheduler_type}_heartbeat.json"
        
        task = SchedulerTask(
            scheduler_type=scheduler_type,
            task_function=task_function if isinstance(task_function, str) else str(task_function),
            interval_minutes=interval_minutes,
            task_config=task_config or {},
            dependencies=dependencies or [],
            heartbeat_interval=heartbeat_interval,
            show_progress_bar=show_progress_bar,
            heartbeat_file=heartbeat_file
        )
        
        # Nächste Ausführung berechnen
        task.next_run = datetime.now() + timedelta(minutes=interval_minutes)
        
        self.tasks[scheduler_type] = task
        logger.info(f"📋 Task '{scheduler_type}' registriert (Intervall: {interval_minutes}min)")
    
    def start_scheduler(self):
        """Startet den Enhanced Background Scheduler"""
        if self.running:
            logger.warning("⚠️ Scheduler läuft bereits")
            return
        
        self.running = True
        self.stop_event.clear()
        
        # Scheduler-Thread starten
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=False)
        self.scheduler_thread.start()
        
        # Parent-Process-Monitoring starten
        self._start_parent_monitoring()
        
        logger.info(f"🚀 Enhanced Background Scheduler '{self.scheduler_name}' gestartet")
    
    def stop_scheduler(self, cleanup: bool = True):
        """
        Stoppt den Enhanced Background Scheduler
        
        Args:
            cleanup: Ob alle laufenden Prozesse beendet werden sollen
        """
        if not self.running:
            logger.info("ℹ️ Scheduler war nicht aktiv")
            return
        
        logger.info("⏹️ Stoppe Enhanced Background Scheduler...")
        
        # Stop-Event setzen
        self.stop_event.set()
        self.running = False
        
        # Monitoring stoppen
        self.monitoring_active = False
        
        # Alle laufenden Prozesse beenden
        if cleanup:
            self._cleanup_processes()
        
        # Auf Scheduler-Thread warten
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=10)
        
        logger.info("✅ Enhanced Background Scheduler gestoppt")
    
    def _run_scheduler(self):
        """Hauptschleife des Enhanced Schedulers"""
        logger.info(f"🔄 Scheduler-Thread '{self.scheduler_name}' gestartet")
        
        while not self.stop_event.is_set():
            try:
                current_time = datetime.now()
                
                # Prüfe alle registrierten Tasks
                for task_type, task in self.tasks.items():
                    if not task.running and current_time >= task.next_run:
                        self._execute_task_in_terminal(task)
                    
                    # Prüfe Heartbeat
                    self._check_task_heartbeat(task)
                
                # Cleanup beendeter Prozesse
                self._cleanup_finished_processes()
                
                # Kurz warten
                time.sleep(30)  # Prüfe alle 30 Sekunden
                
            except Exception as e:
                logger.error(f"❌ Scheduler-Fehler: {e}")
                time.sleep(60)
        
        logger.info("⏹️ Scheduler-Thread beendet")
    
    def _execute_task_in_terminal(self, task: SchedulerTask):
        """
        Führt einen Task in separatem Terminal-Prozess aus
        
        Args:
            task: Auszuführender Task
        """
        try:
            logger.info(f"🚀 Starte Task '{task.scheduler_type}' in separatem Terminal")
            
            # Python-Script für Task erstellen
            script_content = self._generate_task_script(task)
            script_file = Path(f"temp_task_{task.scheduler_type}.py")
            
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # Separate Terminal-Execution je nach OS
            if os.name == 'nt':  # Windows
                cmd = ['start', 'cmd', '/c', f'python {script_file} && pause']
                process = subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:  # Linux/Mac
                cmd = ['gnome-terminal', '--', 'python3', str(script_file)]
                process = subprocess.Popen(cmd)
            
            # Process Management
            task.process = process
            task.running = True
            task.last_run = datetime.now()
            task.next_run = datetime.now() + timedelta(minutes=task.interval_minutes)
            
            self.processes[task.scheduler_type] = process
            
            # Heartbeat initialisieren
            self._init_task_heartbeat(task)
            
            logger.info(f"✅ Task '{task.scheduler_type}' gestartet (PID: {process.pid})")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten von Task '{task.scheduler_type}': {e}")
            task.running = False
    
    def _generate_task_script(self, task: SchedulerTask) -> str:
        """
        Generiert Python-Script für Task-Ausführung
        
        Args:
            task: Task-Definition
            
        Returns:
            Python-Script als String
        """
        dependencies_import = "\n".join([f"import {dep}" for dep in task.dependencies])
        
        # Heartbeat-Funktion
        heartbeat_code = f'''
def update_heartbeat():
    import json
    from datetime import datetime
    heartbeat_data = {{
        "task_type": "{task.scheduler_type}",
        "last_heartbeat": datetime.now().isoformat(),
        "status": "running",
        "parent_pid": {self.parent_pid}
    }}
    with open("{task.heartbeat_file}", "w") as f:
        json.dump(heartbeat_data, f)
'''
        
        # Progress Bar Code (falls aktiviert)
        progress_code = """
try:
    from tqdm import tqdm
    progress_available = True
except ImportError:
    progress_available = False
    
    class DummyTqdm:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def update(self, *args):
            pass
        def set_description(self, desc):
            print(f"📊 {desc}")
    
    tqdm = DummyTqdm
""" if task.show_progress_bar else ""
        
        script = f'''#!/usr/bin/env python3
"""
Enhanced Background Task: {task.scheduler_type}
Generated by Enhanced Universal Background Scheduler v2.0
"""

import sys
import os
import signal
import time
from datetime import datetime
{dependencies_import}

# Heartbeat und Progress Setup
{heartbeat_code}
{progress_code}

# Signal Handler für sauberen Exit
def signal_handler(sig, frame):
    print("\\n🛑 Task wird beendet...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Task-Konfiguration
TASK_CONFIG = {json.dumps(task.task_config, indent=2)}
BASE_CONFIG = {json.dumps(self.base_config, indent=2)}

print("=" * 60)
print(f"🚀 Enhanced Background Task: {task.scheduler_type}")
print(f"⏰ Gestartet: {{datetime.now().strftime('%H:%M:%S')}}")
print("=" * 60)

# Heartbeat starten
update_heartbeat()

try:
    # Task-Funktion ausführen
{task.task_function}
    
    print("✅ Task erfolgreich abgeschlossen")
    
except Exception as e:
    print(f"❌ Task-Fehler: {{e}}")
    import traceback
    traceback.print_exc()

finally:
    # Abschluss-Heartbeat
    import json
    heartbeat_data = {{
        "task_type": "{task.scheduler_type}",
        "last_heartbeat": datetime.now().isoformat(),
        "status": "completed",
        "parent_pid": {self.parent_pid}
    }}
    with open("{task.heartbeat_file}", "w") as f:
        json.dump(heartbeat_data, f)
    
    print("🏁 Task-Ausführung beendet")
'''
        return script
    
    def _init_task_heartbeat(self, task: SchedulerTask):
        """Initialisiert Heartbeat für Task"""
        heartbeat_data = {
            "task_type": task.scheduler_type,
            "last_heartbeat": datetime.now().isoformat(),
            "status": "starting",
            "parent_pid": self.parent_pid,
            "process_pid": task.process.pid if task.process else None
        }
        
        with open(task.heartbeat_file, 'w') as f:
            json.dump(heartbeat_data, f)
    
    def _check_task_heartbeat(self, task: SchedulerTask):
        """Prüft Heartbeat eines Tasks"""
        if not task.heartbeat_file.exists():
            return
        
        try:
            with open(task.heartbeat_file, 'r') as f:
                heartbeat_data = json.load(f)
            
            last_heartbeat = datetime.fromisoformat(heartbeat_data['last_heartbeat'])
            time_since = (datetime.now() - last_heartbeat).total_seconds()
            
            # Heartbeat-Timeout prüfen
            if time_since > task.heartbeat_interval * 2:  # 2x Intervall als Timeout
                logger.warning(f"⚠️ Task '{task.scheduler_type}' Heartbeat-Timeout ({time_since:.0f}s)")
                
                # Task als nicht laufend markieren
                if task.running:
                    task.running = False
                    if task.scheduler_type in self.processes:
                        del self.processes[task.scheduler_type]
        
        except Exception as e:
            logger.error(f"❌ Fehler beim Prüfen des Heartbeats für '{task.scheduler_type}': {e}")
    
    def _cleanup_finished_processes(self):
        """Bereinigt beendete Prozesse"""
        finished_tasks = []
        
        for task_type, process in self.processes.items():
            if process.poll() is not None:  # Prozess ist beendet
                finished_tasks.append(task_type)
                
                # Task als nicht laufend markieren
                if task_type in self.tasks:
                    self.tasks[task_type].running = False
                
                # Temp-Datei löschen
                temp_file = Path(f"temp_task_{task_type}.py")
                if temp_file.exists():
                    temp_file.unlink()
                
                logger.info(f"🏁 Task '{task_type}' beendet (Exit Code: {process.returncode})")
        
        # Beendete Prozesse aus Dictionary entfernen
        for task_type in finished_tasks:
            del self.processes[task_type]
    
    def _cleanup_processes(self):
        """Beendet alle laufenden Prozesse"""
        for task_type, process in self.processes.items():
            try:
                if process.poll() is None:  # Prozess läuft noch
                    logger.info(f"⏹️ Beende Task-Prozess '{task_type}'")
                    process.terminate()
                    
                    # Warte kurz auf sauberes Beenden
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        logger.warning(f"⚠️ Erzwinge Beendigung von '{task_type}'")
                        process.kill()
            except Exception as e:
                logger.error(f"❌ Fehler beim Beenden von Task '{task_type}': {e}")
        
        self.processes.clear()
    
    def _start_parent_monitoring(self):
        """Startet Parent-Process-Monitoring"""
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitor_parent_process, daemon=True)
        self.monitoring_thread.start()
        logger.info("👁️ Parent-Process-Monitoring gestartet")
    
    def _monitor_parent_process(self):
        """Überwacht Parent-Process und beendet Scheduler bei Parent-Exit"""
        while self.monitoring_active:
            try:
                # Prüfe ob Parent-Process noch existiert
                if not psutil.pid_exists(self.parent_pid):
                    logger.warning(f"⚠️ Parent-Process (PID: {self.parent_pid}) nicht mehr verfügbar")
                    logger.info("🛑 Stoppe Scheduler aufgrund Parent-Exit")
                    self.stop_scheduler(cleanup=True)
                    break
                
                time.sleep(30)  # Prüfe alle 30 Sekunden
                
            except Exception as e:
                logger.error(f"❌ Parent-Monitoring Fehler: {e}")
                time.sleep(60)
    
    def get_process_status(self) -> Dict:
        """
        Gibt detaillierten Status aller Prozesse zurück
        
        Returns:
            Dict mit Process-Status-Informationen
        """
        status = {
            'scheduler_running': self.running,
            'scheduler_name': self.scheduler_name,
            'total_tasks': len(self.tasks),
            'running_processes': len(self.processes),
            'processes': {},
            'heartbeats': {}
        }
        
        # Process-Status
        for task_type, process in self.processes.items():
            try:
                process_info = {
                    'pid': process.pid,
                    'running': process.poll() is None,
                    'command': ' '.join(process.args) if hasattr(process, 'args') else 'N/A'
                }
                status['processes'][task_type] = process_info
            except Exception as e:
                status['processes'][task_type] = {'error': str(e)}
        
        # Heartbeat-Status
        for task_type, task in self.tasks.items():
            if task.heartbeat_file.exists():
                try:
                    with open(task.heartbeat_file, 'r') as f:
                        heartbeat_data = json.load(f)
                    status['heartbeats'][task_type] = heartbeat_data
                except Exception as e:
                    status['heartbeats'][task_type] = {'error': str(e)}
        
        return status
    
    def show_process_management_terminal(self):
        """Zeigt Process Management Terminal"""
        try:
            print("\n" + "=" * 70)
            print("🖥️  ENHANCED BACKGROUND SCHEDULER - PROCESS MANAGEMENT TERMINAL")
            print("=" * 70)
            
            status = self.get_process_status()
            
            print(f"📊 Scheduler: {status['scheduler_name']} ({'🟢 AKTIV' if status['scheduler_running'] else '🔴 INAKTIV'})")
            print(f"📋 Tasks: {status['total_tasks']} registriert, {status['running_processes']} laufend")
            
            print("\n🔄 LAUFENDE PROZESSE:")
            print("-" * 50)
            
            if status['processes']:
                for task_type, process_info in status['processes'].items():
                    if 'error' in process_info:
                        print(f"❌ {task_type}: {process_info['error']}")
                    else:
                        status_icon = "🟢" if process_info['running'] else "🔴"
                        print(f"{status_icon} {task_type} (PID: {process_info['pid']})")
            else:
                print("   Keine aktiven Prozesse")
            
            print("\n💓 HEARTBEAT-STATUS:")
            print("-" * 50)
            
            if status['heartbeats']:
                for task_type, heartbeat in status['heartbeats'].items():
                    if 'error' in heartbeat:
                        print(f"❌ {task_type}: {heartbeat['error']}")
                    else:
                        last_beat = heartbeat.get('last_heartbeat', 'N/A')
                        task_status = heartbeat.get('status', 'unknown')
                        print(f"💓 {task_type}: {task_status} (letzte Aktivität: {last_beat})")
            else:
                print("   Keine Heartbeat-Daten verfügbar")
            
            print("\n" + "=" * 70)
            
        except Exception as e:
            print(f"❌ Fehler im Process Management Terminal: {e}")

# =====================================================================
# ENHANCED SCHEDULER TASKS v2.0
# =====================================================================

class EnhancedSchedulerTasks:
    """Enhanced Task-Definitionen für Background Scheduler v2.0"""
    
    @staticmethod
    def enhanced_price_tracking_task():
        """Enhanced Task für Price Tracking mit Sign of Life"""
        return '''
# Enhanced Price Tracking Task v2.0
print("💰 Enhanced Price Tracking gestartet...")
print(f"⏰ Start: {datetime.now().strftime('%H:%M:%S')}")

# Heartbeat alle 30 Sekunden
import threading

def heartbeat_timer():
    while True:
        update_heartbeat()
        time.sleep(30)

heartbeat_thread = threading.Thread(target=heartbeat_timer, daemon=True)
heartbeat_thread.start()

try:
    # Price Tracker laden
    from price_tracker import create_price_tracker
    from steam_wishlist_manager import load_api_key_from_env
    
    api_key = load_api_key_from_env()
    tracker = create_price_tracker(api_key=api_key)
    
    # Batch-Update durchführen
    print("🔄 Führe optimiertes Batch-Update durch...")
    result = tracker.process_all_pending_apps_optimized(hours_threshold=6)
    
    print(f"✅ Price Tracking abgeschlossen:")
    print(f"   📊 {result['total_successful']}/{result['total_apps']} Apps erfolgreich")
    print(f"   ⏱️ Dauer: {result['total_duration']:.1f}s")
    print(f"   ⚡ {result['apps_per_second']:.1f} Apps/s")
    
    if result['errors']:
        print(f"   ⚠️ {len(result['errors'])} Fehler aufgetreten")

except Exception as e:
    print(f"❌ Enhanced Price Tracking Fehler: {e}")
    import traceback
    traceback.print_exc()

print(f"🏁 Enhanced Price Tracking abgeschlossen um {datetime.now().strftime('%H:%M:%S')}")
'''
    
    @staticmethod
    def enhanced_name_update_task():
        """Enhanced Task für Namen-Updates"""
        return '''
# Enhanced Name Update Task v2.0
print("📝 Enhanced Name Update gestartet...")
print(f"⏰ Start: {datetime.now().strftime('%H:%M:%S')}")

# Heartbeat alle 20 Sekunden
import threading

def heartbeat_timer():
    while True:
        update_heartbeat()
        time.sleep(20)

heartbeat_thread = threading.Thread(target=heartbeat_timer, daemon=True)
heartbeat_thread.start()

try:
    # Price Tracker laden
    from price_tracker import create_price_tracker
    from steam_wishlist_manager import load_api_key_from_env
    
    api_key = load_api_key_from_env()
    tracker = create_price_tracker(api_key=api_key)
    
    # Namen-Updates durchführen
    print("🔄 Suche Apps mit generischen Namen...")
    apps_to_update = tracker.get_apps_with_generic_names(limit=20)
    
    if apps_to_update:
        print(f"📝 Aktualisiere Namen für {len(apps_to_update)} Apps...")
        updated_count = 0
        
        for app_id, current_name in apps_to_update:
            try:
                new_name = tracker.update_app_name(app_id)
                if new_name and new_name != current_name:
                    print(f"✅ {app_id}: '{current_name}' → '{new_name}'")
                    updated_count += 1
                time.sleep(1)  # Rate Limiting
            except Exception as e:
                print(f"❌ Fehler bei {app_id}: {e}")
        
        print(f"✅ {updated_count} Namen erfolgreich aktualisiert")
    else:
        print("✅ Alle App-Namen sind bereits aktuell")

except Exception as e:
    print(f"❌ Enhanced Name Update Fehler: {e}")
    import traceback
    traceback.print_exc()

print(f"🏁 Enhanced Name Update abgeschlossen um {datetime.now().strftime('%H:%M:%S')}")
'''
    
    @staticmethod
    def enhanced_charts_update_task():
        """Enhanced Task für Charts-Updates"""
        return '''
# Enhanced Charts Update Task v2.0
print("📊 Enhanced Charts Update gestartet...")
print(f"⏰ Start: {datetime.now().strftime('%H:%M:%S')}")

# Heartbeat alle 45 Sekunden
import threading

def heartbeat_timer():
    while True:
        update_heartbeat()
        time.sleep(45)

heartbeat_thread = threading.Thread(target=heartbeat_timer, daemon=True)
heartbeat_thread.start()

try:
    # Price Tracker mit Charts laden
    from price_tracker import create_price_tracker
    from steam_wishlist_manager import load_api_key_from_env
    
    api_key = load_api_key_from_env()
    tracker = create_price_tracker(api_key=api_key, enable_charts=True)
    
    if not tracker.charts_enabled:
        print("❌ Charts-Manager nicht verfügbar")
        exit(1)
    
    # Charts aktualisieren
    print("📊 Aktualisiere Steam Charts...")
    result = tracker.update_charts_now()
    
    if result.get('success', True):
        print("✅ Charts-Update abgeschlossen:")
        print(f"   📊 {result.get('total_games_found', 0)} Spiele gefunden")
        print(f"   ➕ {result.get('new_games_added', 0)} neue Spiele")
        print(f"   🔄 {result.get('existing_games_updated', 0)} aktualisiert")
        
        if result.get('errors'):
            print(f"   ⚠️ {len(result['errors'])} Fehler aufgetreten")
    else:
        print(f"❌ Charts-Update fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")

except Exception as e:
    print(f"❌ Enhanced Charts Update Fehler: {e}")
    import traceback
    traceback.print_exc()

print(f"🏁 Enhanced Charts Update abgeschlossen um {datetime.now().strftime('%H:%M:%S')}")
'''
    
    @staticmethod
    def enhanced_charts_cleanup_task():
        """Enhanced Task für Charts-Cleanup"""
        return '''
# Enhanced Charts Cleanup Task v2.0
print("🧹 Enhanced Charts Cleanup gestartet...")
print(f"⏰ Start: {datetime.now().strftime('%H:%M:%S')}")

try:
    # Price Tracker mit Charts laden
    from price_tracker import create_price_tracker
    from steam_wishlist_manager import load_api_key_from_env
    
    api_key = load_api_key_from_env()
    tracker = create_price_tracker(api_key=api_key, enable_charts=True)
    
    if not tracker.charts_enabled:
        print("❌ Charts-Manager nicht verfügbar")
        exit(1)
    
    total_cleaned = 0
    
    # Charts-Spiele Cleanup
    print("🗑️ Bereinige alte Charts-Spiele (>30 Tage)...")
    removed = tracker.charts_manager.cleanup_old_chart_games(days_threshold=30)
    
    if removed > 0:
        print(f"✅ {removed} alte Charts-Spiele entfernt")
        total_cleaned += removed
    else:
        print("✅ Keine alten Charts-Spiele zum Entfernen")
    
    # Alte Preis-Snapshots bereinigen
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
    
    if total_cleaned > 0:
        print(f"🎉 Enhanced Cleanup abgeschlossen: {total_cleaned} Einträge bereinigt")
    else:
        print("✅ Enhanced Cleanup abgeschlossen - alles bereits sauber")

except Exception as e:
    print(f"❌ Enhanced Charts Cleanup Fehler: {e}")
    import traceback
    traceback.print_exc()

print(f"🏁 Enhanced Charts Cleanup abgeschlossen um {datetime.now().strftime('%H:%M:%S')}")
'''

# =====================================================================
# CONVENIENCE FUNCTIONS
# =====================================================================

def create_enhanced_price_tracker_scheduler() -> EnhancedBackgroundScheduler:
    """
    Erstellt Enhanced BackgroundScheduler für Price Tracker
    
    Returns:
        Konfigurierter EnhancedBackgroundScheduler
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

def main():
    """Process Management Terminal für Enhanced Background Scheduler"""
    try:
        print("🖥️  ENHANCED BACKGROUND SCHEDULER - PROCESS MANAGEMENT TERMINAL")
        print("=" * 70)
        print("Verfügbare Scheduler:")
        print("1. 🚀 Price Tracker Scheduler erstellen und starten")
        print("2. 📊 Charts Scheduler erstellen und starten") 
        print("3. 📋 Scheduler-Status anzeigen")
        print("4. ⏹️ Alle Scheduler stoppen")
        print("0. ❌ Beenden")
        
        schedulers = {}
        
        while True:
            try:
                choice = input("\nWählen Sie eine Option: ").strip()
                
                if choice == "1":
                    if "price_tracker" not in schedulers:
                        schedulers["price_tracker"] = create_enhanced_price_tracker_scheduler()
                        schedulers["price_tracker"].start_scheduler()
                        print("✅ Price Tracker Scheduler gestartet")
                    else:
                        print("⚠️ Price Tracker Scheduler läuft bereits")
                
                elif choice == "2":
                    if "charts" not in schedulers:
                        schedulers["charts"] = create_enhanced_charts_scheduler()
                        schedulers["charts"].start_scheduler()
                        print("✅ Charts Scheduler gestartet")
                    else:
                        print("⚠️ Charts Scheduler läuft bereits")
                
                elif choice == "3":
                    for name, scheduler in schedulers.items():
                        print(f"\n📊 {name.upper()} SCHEDULER:")
                        scheduler.show_process_management_terminal()
                
                elif choice == "4":
                    for name, scheduler in schedulers.items():
                        print(f"⏹️ Stoppe {name} Scheduler...")
                        scheduler.stop_scheduler()
                    schedulers.clear()
                    print("✅ Alle Scheduler gestoppt")
                
                elif choice == "0":
                    # Cleanup
                    for scheduler in schedulers.values():
                        scheduler.stop_scheduler()
                    print("👋 Auf Wiedersehen!")
                    break
                
                else:
                    print("❌ Ungültige Option")
                    
            except KeyboardInterrupt:
                print("\n🛑 Beende Process Management Terminal...")
                for scheduler in schedulers.values():
                    scheduler.stop_scheduler()
                break
            except Exception as e:
                print(f"❌ Fehler: {e}")
                
    except Exception as e:
        print(f"❌ Kritischer Fehler im Process Management Terminal: {e}")

if __name__ == "__main__":
    main()
