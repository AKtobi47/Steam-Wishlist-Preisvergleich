#!/usr/bin/env python3
"""
Enhanced Universal Background Scheduler v2.0 - COMPLETE PATCHED VERSION
Steam Price Tracker - Separate Terminal-Execution für alle Background-Tasks
Unterstützt Parent-Process-Monitoring, Sign of Life und Process Management Terminal

PATCHES APPLIED:
- ASYNC Terminal Execution (Main blockiert nicht mehr)
- Improved Process Registration (Process Management erkennt Prozesse)
- Working Script Generation (Sichtbarer Progress/Heartbeat)
- Tolerante Heartbeat-Prüfung (Weniger Cleanup-Spam)
- Quiet Cleanup (Reduziertes Logging)
"""

import subprocess
import threading
import time
import logging
import json
import signal
import sys
import os
import atexit
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from queue import Queue, Empty
import psutil

try:
    from steam_charts_manager import CHART_TYPES
    SCHEDULER_CHART_TYPES = list(CHART_TYPES.keys())
except ImportError:
    SCHEDULER_CHART_TYPES = ['most_played', 'top_releases', 'most_concurrent_players']

# Logging Setup
try:
    from logging_config import get_background_scheduler_logger
    logger = get_background_scheduler_logger()
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# =====================================================================
# DATA CLASSES
# =====================================================================

@dataclass
class SchedulerTask:
    """Enhanced Task Definition für Background Scheduler"""
    scheduler_type: str
    task_function: str
    interval_minutes: int
    task_config: Dict = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    heartbeat_interval: int = 60  # Sekunden - PATCHED: Erhöht von 30 auf 60
    show_progress_bar: bool = False
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    running: bool = False
    process: Optional[subprocess.Popen] = None
    heartbeat_file: Optional[Path] = None

# =====================================================================
# GLOBAL PROCESS MANAGER
# =====================================================================

class GlobalProcessManager:
    """
    Globaler Process Manager für Enhanced Background Scheduler
    Verwaltet alle Background-Prozesse zentral
    """
    
    def __init__(self):
        """Initialisiert Global Process Manager"""
        self.tracked_processes: Dict[str, Dict] = {}
        self.lock = threading.Lock()
        self.cleanup_registered = False
        logger.info("✅ Global Process Manager initialisiert")
    
    def register_process(self, scheduler_id: str, process: subprocess.Popen, 
                        scheduler_type: str = "unknown", config: Dict = None) -> bool:
        """
        Registriert einen neuen Prozess
        
        Args:
            scheduler_id: Eindeutige ID für den Scheduler
            process: Subprocess.Popen Objekt
            scheduler_type: Typ des Schedulers
            config: Zusätzliche Konfiguration
            
        Returns:
            True wenn erfolgreich registriert
        """
        try:
            with self.lock:
                self.tracked_processes[scheduler_id] = {
                    'process': process,
                    'pid': process.pid,
                    'scheduler_type': scheduler_type,
                    'started_at': datetime.now().isoformat(),
                    'is_running': True,
                    'config': config or {},
                    'parent_monitoring': True
                }
            
            logger.info(f"✅ Prozess registriert: {scheduler_id} (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Registrieren von Prozess {scheduler_id}: {e}")
            return False
    
    def get_process_status(self) -> Dict:
        """
        Gibt Status aller getrackten Prozesse zurück
        
        Returns:
            Dictionary mit Process-Status Informationen
        """
        try:
            with self.lock:
                running_processes = 0
                dead_processes = 0
                processes_info = {}
                
                for scheduler_id, proc_info in self.tracked_processes.items():
                    try:
                        process = proc_info['process']
                        # Prüfe ob Prozess noch läuft
                        if process.poll() is None:
                            proc_info['is_running'] = True
                            running_processes += 1
                        else:
                            proc_info['is_running'] = False
                            dead_processes += 1
                    except Exception:
                        proc_info['is_running'] = False
                        dead_processes += 1
                    
                    # Copy für Output (ohne Process-Objekt)
                    processes_info[scheduler_id] = {
                        'pid': proc_info['pid'],
                        'scheduler_type': proc_info['scheduler_type'],
                        'started_at': proc_info['started_at'],
                        'is_running': proc_info['is_running'],
                        'parent_monitoring': proc_info.get('parent_monitoring', False)
                    }
                
                return {
                    'total_tracked': len(self.tracked_processes),
                    'running_processes': running_processes,
                    'dead_processes': dead_processes,
                    'processes': processes_info
                }
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen des Process-Status: {e}")
            return {
                'total_tracked': 0,
                'running_processes': 0,
                'dead_processes': 0,
                'processes': {}
            }
    
    def cleanup_all_processes(self) -> int:
        """
        Stoppt alle getrackten Prozesse
        
        Returns:
            Anzahl gestoppter Prozesse
        """
        stopped_count = 0
        
        try:
            with self.lock:
                for scheduler_id, proc_info in self.tracked_processes.items():
                    try:
                        process = proc_info['process']
                        if process.poll() is None:  # Prozess läuft noch
                            process.terminate()
                            # Warte kurz auf saubere Beendigung
                            try:
                                process.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                process.kill()  # Force kill falls nötig
                            
                            stopped_count += 1
                            logger.info(f"⏹️ Prozess gestoppt: {scheduler_id}")
                            
                    except Exception as e:
                        logger.debug(f"Cleanup error für {scheduler_id}: {e}")
                
                # Alle Prozesse als gestoppt markieren
                for proc_info in self.tracked_processes.values():
                    proc_info['is_running'] = False
                
            logger.info(f"✅ Process Cleanup abgeschlossen: {stopped_count} Prozesse gestoppt")
            return stopped_count
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Process Cleanup: {e}")
            return stopped_count
    
    def stop_process(self, scheduler_id: str) -> bool:
        """
        Stoppt einen spezifischen Prozess
        
        Args:
            scheduler_id: ID des zu stoppenden Prozesses
            
        Returns:
            True wenn erfolgreich gestoppt
        """
        try:
            with self.lock:
                if scheduler_id not in self.tracked_processes:
                    logger.warning(f"❌ Prozess {scheduler_id} nicht gefunden")
                    return False
                
                proc_info = self.tracked_processes[scheduler_id]
                process = proc_info['process']
                
                if process.poll() is None:  # Prozess läuft noch
                    process.terminate()
                    
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    
                    proc_info['is_running'] = False
                    logger.info(f"⏹️ Prozess gestoppt: {scheduler_id}")
                    return True
                else:
                    logger.info(f"ℹ️ Prozess {scheduler_id} war bereits beendet")
                    proc_info['is_running'] = False
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Stoppen von Prozess {scheduler_id}: {e}")
            return False

# Globale Instanz erstellen
_global_process_manager = GlobalProcessManager()

# =====================================================================
# ENHANCED SCHEDULER TASKS - UNCHANGED
# =====================================================================

class EnhancedSchedulerTasks:
    """
    Sammlung von Enhanced Task-Funktionen für Background Scheduler
    Alle Task-Funktionen sind bereits perfekt eingerückt
    """
    
    @staticmethod
    def enhanced_price_tracking_task() -> str:
        """Enhanced Price Tracking Task - BEREITS KORREKT EINGERÜCKT"""
        return '''def enhanced_price_tracking_task():
    """Enhanced Price Tracking mit Progress Bar und Fehlerbehandlung"""
    print("🚀 Enhanced Price Tracking gestartet")
    
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        from datetime import datetime
        import time
        
        # API Key laden
        api_key = load_api_key_from_env()
        if not api_key:
            print("❌ Kein Steam API Key verfügbar")
            return
        
        tracker = create_price_tracker(api_key=api_key)
        
        # Alle ausstehenden Apps abrufen
        pending_apps = tracker.get_pending_apps(hours_threshold=6)
        
        if not pending_apps:
            print("✅ Keine ausstehenden Price Updates")
            return
        
        print(f"📊 {len(pending_apps)} Apps benötigen Price-Updates")
        
        if progress_available:
            from tqdm import tqdm
            with tqdm(total=len(pending_apps), desc="Price Updates") as pbar:
                for app_id in pending_apps:
                    try:
                        success = tracker.update_single_app_price(app_id)
                        pbar.set_description(f"App {app_id}: {'✅' if success else '❌'}")
                        pbar.update(1)
                        time.sleep(1)  # Rate limiting
                    except Exception as e:
                        print(f"❌ Fehler bei App {app_id}: {e}")
                        pbar.update(1)
        else:
            for i, app_id in enumerate(pending_apps):
                try:
                    success = tracker.update_single_app_price(app_id)
                    print(f"📊 {i+1}/{len(pending_apps)} - App {app_id}: {'✅' if success else '❌'}")
                    time.sleep(1)  # Rate limiting
                except Exception as e:
                    print(f"❌ Fehler bei App {app_id}: {e}")
        
        print("✅ Enhanced Price Tracking abgeschlossen")
        
    except Exception as e:
        print(f"❌ Enhanced Price Tracking Fehler: {e}")
        import traceback
        traceback.print_exc()'''

    @staticmethod
    def enhanced_name_update_task() -> str:
        """Enhanced Name Update Task - BEREITS KORREKT EINGERÜCKT"""
        return '''def enhanced_name_update_task():
    """Enhanced Name Updates mit Steam API"""
    print("🏷️ Enhanced Name Updates gestartet")
    
    try:
        from steam_wishlist_manager import SteamWishlistManager, load_api_key_from_env
        from price_tracker import create_price_tracker
        from datetime import datetime
        import time
        
        # API Key laden
        api_key = load_api_key_from_env()
        if not api_key:
            print("❌ Kein Steam API Key verfügbar")
            return
        
        tracker = create_price_tracker(api_key=api_key)
        steam_manager = SteamWishlistManager()
        
        # Apps ohne Namen finden
        apps_without_names = tracker.get_apps_without_names()
        
        if not apps_without_names:
            print("✅ Alle Apps haben Namen")
            return
        
        print(f"🏷️ {len(apps_without_names)} Apps benötigen Name-Updates")
        
        for i, app_id in enumerate(apps_without_names[:20]):  # Limit für API Rate
            try:
                app_name = steam_manager.get_app_name(app_id)
                if app_name:
                    tracker.update_app_name(app_id, app_name)
                    print(f"✅ {i+1}/20 - {app_id}: {app_name}")
                else:
                    print(f"❌ {i+1}/20 - Name nicht gefunden: {app_id}")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Fehler bei App {app_id}: {e}")
        
        print("✅ Enhanced Name Updates abgeschlossen")
        
    except Exception as e:
        print(f"❌ Enhanced Name Updates Fehler: {e}")
        import traceback
        traceback.print_exc()'''

    @staticmethod
    def enhanced_charts_update_task() -> str:
        """Enhanced Charts Update Task - BEREITS KORREKT EINGERÜCKT"""
        return '''def enhanced_charts_update_task():
    """Enhanced Charts Updates mit SteamCharts Integration"""
    print("📊 Enhanced Charts Updates gestartet")
    
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        from datetime import datetime
        import time
        
        # API Key laden
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
        
        result = tracker.charts_manager.update_all_charts_batch()
        
        if result and result.get('success'):
            print(f"✅ Enhanced Charts-Update abgeschlossen:")
            print(f"   📊 {result.get('updated_charts', 0)} Charts verarbeitet")
            print(f"   🎮 {result.get('new_games', 0)} neue Spiele gefunden")
            print(f"   ⏱️ Dauer: {result.get('duration', 0):.1f}s")
        else:
            print(f"❌ Enhanced Charts-Update fehlgeschlagen: {result.get('error') if result else 'Unbekannter Fehler'}")
        
        print(f"🏁 Enhanced Charts-Update abgeschlossen um {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Enhanced Charts-Update Fehler: {e}")
        import traceback
        traceback.print_exc()'''

    @staticmethod
    def enhanced_charts_price_update_task() -> str:
        """Enhanced Task für Charts-Preise - BEREITS KORREKT EINGERÜCKT"""
        return '''def enhanced_charts_price_update_task():
    """Enhanced Charts Price Update Task"""
    print("💰 Enhanced Charts-Preise Task gestartet...")
    
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        from datetime import datetime
        import time
        
        # API Key laden
        api_key = load_api_key_from_env()
        if not api_key:
            print("❌ Kein Steam API Key verfügbar")
            return
        
        tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        
        if not tracker.charts_enabled:
            print("❌ Charts nicht verfügbar")
            return
        
        print("🔄 Starte Enhanced Charts-Preise Update...")
        print(f"⏰ Start: {datetime.now().strftime('%H:%M:%S')}")
        
        # Charts-Apps abrufen und Preise aktualisieren
        try:
            chart_apps = tracker.charts_manager.get_active_chart_games()
        except:
            # Fallback: verwende getrackte Apps
            chart_apps = tracker.get_tracked_apps()[:50]  # Limit auf 50
        
        if not chart_apps:
            print("💡 Keine Chart-Apps für Preis-Updates gefunden")
            return
        
        print(f"💰 {len(chart_apps)} Chart-Apps für Preis-Updates")
        
        updated_count = 0
        failed_count = 0
        
        if progress_available:
            from tqdm import tqdm
            with tqdm(total=len(chart_apps), desc="Charts Preise") as pbar:
                for app_id in chart_apps:
                    try:
                        success = tracker.update_single_app_price(app_id)
                        if success:
                            updated_count += 1
                        else:
                            failed_count += 1
                        pbar.set_description(f"Preise: {updated_count}✅ {failed_count}❌")
                        pbar.update(1)
                        time.sleep(0.5)  # Rate limiting
                    except Exception as e:
                        failed_count += 1
                        pbar.update(1)
        else:
            for i, app_id in enumerate(chart_apps):
                try:
                    success = tracker.update_single_app_price(app_id)
                    if success:
                        updated_count += 1
                    else:
                        failed_count += 1
                    print(f"💰 {i+1}/{len(chart_apps)} - App {app_id}: {'✅' if success else '❌'}")
                    time.sleep(0.5)  # Rate limiting
                except Exception as e:
                    failed_count += 1
                    print(f"❌ Fehler bei App {app_id}: {e}")
        
        print(f"✅ Enhanced Charts-Preise Update abgeschlossen:")
        print(f"   💰 {updated_count} Preise erfolgreich aktualisiert")
        print(f"   ❌ {failed_count} Fehler")
        print(f"   ⏱️ Abgeschlossen um {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Enhanced Charts-Preise Update Fehler: {e}")
        import traceback
        traceback.print_exc()'''

    @staticmethod
    def enhanced_charts_cleanup_task() -> str:
        """Enhanced Charts Cleanup Task - BEREITS KORREKT EINGERÜCKT"""
        return '''def enhanced_charts_cleanup_task():
    """Enhanced Charts Cleanup - entfernt alte/verwaiste Daten"""
    print("🧹 Enhanced Charts-Cleanup Task gestartet...")
    
    try:
        from price_tracker import create_price_tracker
        from steam_wishlist_manager import load_api_key_from_env
        from datetime import datetime, timedelta
        import time
        
        # API Key laden
        api_key = load_api_key_from_env()
        if not api_key:
            print("❌ Kein Steam API Key verfügbar")
            return
        
        tracker = create_price_tracker(api_key=api_key, enable_charts=True)
        
        if not tracker.charts_enabled:
            print("❌ Charts nicht verfügbar")
            return
        
        print("🧹 Starte umfassendes Charts-Cleanup...")
        print(f"⏰ Start: {datetime.now().strftime('%H:%M:%S')}")
        
        # Cleanup-Operationen
        cleanup_results = {
            'old_data_removed': 0,
            'orphaned_records': 0,
            'duplicate_entries': 0
        }
        
        # Alte Daten entfernen (älter als 90 Tage)
        cutoff_date = datetime.now() - timedelta(days=90)
        if hasattr(tracker.charts_manager, 'cleanup_old_data'):
            old_data_count = tracker.charts_manager.cleanup_old_data(cutoff_date)
            cleanup_results['old_data_removed'] = old_data_count
        
        # Verwaiste Records entfernen
        if hasattr(tracker.charts_manager, 'cleanup_orphaned_records'):
            orphaned_count = tracker.charts_manager.cleanup_orphaned_records()
            cleanup_results['orphaned_records'] = orphaned_count
        
        # Duplikate entfernen
        if hasattr(tracker.charts_manager, 'cleanup_duplicate_entries'):
            duplicate_count = tracker.charts_manager.cleanup_duplicate_entries()
            cleanup_results['duplicate_entries'] = duplicate_count
        
        print(f"✅ Enhanced Charts Cleanup abgeschlossen:")
        print(f"   🗑️ Alte Daten entfernt: {cleanup_results['old_data_removed']}")
        print(f"   🔗 Verwaiste Records: {cleanup_results['orphaned_records']}")
        print(f"   📝 Duplikate entfernt: {cleanup_results['duplicate_entries']}")
        print(f"   ⏱️ Abgeschlossen um {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Enhanced Charts Cleanup Fehler: {e}")
        import traceback
        traceback.print_exc()'''

# =====================================================================
# ENHANCED BACKGROUND SCHEDULER - PATCHED VERSION
# =====================================================================

class EnhancedBackgroundScheduler:
    """
    Enhanced Universal Background Scheduler v2.0 - PATCHED VERSION
    Führt alle Tasks in separaten Terminal-Prozessen aus
    Mit Parent-Process-Monitoring und Sign of Life
    
    PATCHES:
    - Async Terminal Execution
    - Improved Process Registration  
    - Working Script Generation
    - Tolerante Heartbeat-Prüfung
    - Quiet Cleanup
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
        
        # Project root für Scripts
        self.project_root = Path.cwd()
        
        logger.info(f"✅ Enhanced Background Scheduler '{scheduler_name}' v2.0 initialisiert")
    
    def register_scheduler(self,
                          scheduler_type: str,
                          task_function: str,
                          interval_minutes: int,
                          task_config: Dict = None,
                          dependencies: List[str] = None,
                          heartbeat_interval: int = 60,  # PATCHED: Erhöht von 30 auf 60
                          show_progress_bar: bool = False) -> bool:
        """
        Registriert einen neuen Scheduler-Task
        
        Args:
            scheduler_type: Typ des Schedulers
            task_function: Python-Code der Task-Funktion
            interval_minutes: Intervall in Minuten
            task_config: Task-spezifische Konfiguration
            dependencies: Liste der benötigten Module
            heartbeat_interval: Heartbeat-Intervall in Sekunden
            show_progress_bar: Ob Progress Bar angezeigt werden soll
            
        Returns:
            True wenn erfolgreich registriert
        """
        try:
            task = SchedulerTask(
                scheduler_type=scheduler_type,
                task_function=task_function,
                interval_minutes=interval_minutes,
                task_config=task_config or {},
                dependencies=dependencies or [],
                heartbeat_interval=heartbeat_interval,
                show_progress_bar=show_progress_bar,
                next_run=datetime.now()  # Startet sofort
            )
            
            # Heartbeat-Datei vorbereiten
            task.heartbeat_file = self.heartbeat_dir / f"{scheduler_type}_heartbeat.json"
            
            self.tasks[scheduler_type] = task
            
            logger.info(f"✅ Task registriert: {scheduler_type} (Intervall: {interval_minutes} min)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Registrieren von Task {scheduler_type}: {e}")
            return False
    
    def start_scheduler(self) -> bool:
        """
        Startet den Enhanced Background Scheduler
        
        Returns:
            True wenn erfolgreich gestartet
        """
        if self.running:
            logger.warning("⚠️ Scheduler läuft bereits")
            return False
        
        try:
            self.running = True
            self.stop_event.clear()
            
            # Scheduler-Thread starten
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            # Parent-Process-Monitoring starten
            self._start_parent_monitoring()
            
            logger.info(f"🚀 Enhanced Background Scheduler '{self.scheduler_name}' gestartet")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten des Schedulers: {e}")
            self.running = False
            return False
    
    def stop_scheduler(self, cleanup: bool = True) -> None:
        """
        Stoppt den Enhanced Background Scheduler
        
        Args:
            cleanup: Ob alle Prozesse gestoppt werden sollen
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
    
    def get_process_status(self) -> Dict:
        """Gibt Status der Scheduler-Prozesse zurück"""
        status = {
            'scheduler_name': self.scheduler_name,
            'running': self.running,
            'total_tasks': len(self.tasks),
            'running_tasks': sum(1 for task in self.tasks.values() if task.running),
            'processes': {}
        }
        
        for task_type, task in self.tasks.items():
            status['processes'][f"{self.scheduler_name}_{task_type}"] = {
                'scheduler_type': task_type,
                'is_running': task.running,
                'pid': task.process.pid if task.process else None,
                'started_at': task.last_run.isoformat() if task.last_run else None,
                'next_run': task.next_run.isoformat() if task.next_run else None,
                'parent_monitoring': True
            }
        
        return status
    
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
                
                # PATCHED: Längeres Intervall (weniger CPU-Last)
                time.sleep(60)  # Prüfe alle 60 Sekunden statt 30
                
            except Exception as e:
                logger.error(f"❌ Scheduler-Fehler: {e}")
                time.sleep(60)
        
        logger.info("⏹️ Scheduler-Thread beendet")
    
    # =====================================================================
    # PATCHED: ASYNC TASK EXECUTION
    # =====================================================================
    
    def _execute_task_in_terminal(self, task: SchedulerTask):
        """
        PATCHED: Verbesserte Task-Ausführung mit Async-Support und Process Registration
        
        Args:
            task: Auszuführender Task
        """
        try:
            logger.info(f"🚀 Starte Task '{task.scheduler_type}' in separatem Terminal")
            
            # Python-Script für Task erstellen
            script_content = self._generate_task_script_fixed(task)
            script_file = Path(f"temp_task_{task.scheduler_type}.py")
            
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            print(f"📄 Script generiert: {script_file}")
            
            # PATCHED: Async Terminal-Prozess starten
            process = self._start_enhanced_terminal_process(str(script_file), task.scheduler_type)
            
            if process:
                # PATCHED: Bessere Process Management
                task.process = process
                task.running = True
                task.last_run = datetime.now()
                task.next_run = datetime.now() + timedelta(minutes=task.interval_minutes)
                
                self.processes[task.scheduler_type] = process
                
                # PATCHED: Process global registrieren MIT DELAY für bessere Erkennung
                def delayed_registration():
                    time.sleep(2)  # Warte bis Prozess stabilisiert ist
                    try:
                        register_background_process(
                            process=process,
                            scheduler_id=f"{self.scheduler_name}_{task.scheduler_type}",
                            scheduler_type=task.scheduler_type,
                            config={'script_file': str(script_file)}
                        )
                        print(f"✅ Prozess registriert: {self.scheduler_name}_{task.scheduler_type}")
                    except Exception as e:
                        print(f"⚠️ Prozess-Registrierung fehlgeschlagen: {e}")
                
                threading.Thread(target=delayed_registration, daemon=True).start()
                
                # Heartbeat initialisieren
                self._init_task_heartbeat(task)
                
                logger.info(f"✅ ASYNC Task '{task.scheduler_type}' gestartet (PID: {process.pid})")
                print(f"💡 Main Terminal bleibt frei - Task läuft asynchron")
            else:
                logger.error(f"❌ Konnte Task '{task.scheduler_type}' nicht starten")
                task.running = False
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten von Task '{task.scheduler_type}': {e}")
            task.running = False
    
    # =====================================================================
    # PATCHED: WORKING SCRIPT GENERATION
    # =====================================================================
    
    def _generate_task_script_fixed(self, task: SchedulerTask) -> str:
        """
        PATCHED: Generiert funktionierendes Script mit sichtbarem Progress/Heartbeat
        
        Args:
            task: Task-Definition
            
        Returns:
            Funktionierendes Python-Script mit Live-Progress und Heartbeat
        """
        dependencies_imports = self._format_dependencies_import(task.dependencies)
        
        # PATCHED: Heartbeat mit Live-Output und verbesserter Fehlerbehandlung
        heartbeat_code = f'''
def update_heartbeat():
    """Aktualisiert Heartbeat mit Live-Output"""
    import json
    import os
    from datetime import datetime
    from pathlib import Path
    
    current_time = datetime.now()
    
    heartbeat_data = {{
        "task_type": "{task.scheduler_type}",
        "scheduler_name": "{self.scheduler_name}",
        "last_heartbeat": current_time.isoformat(),
        "status": "running",
        "parent_pid": {self.parent_pid},
        "process_pid": os.getpid(),
        "heartbeat_count": globals().get('heartbeat_count', 0) + 1
    }}
    
    try:
        # Stelle sicher, dass heartbeats-Verzeichnis existiert
        heartbeat_file = Path("{task.heartbeat_file}")
        heartbeat_file.parent.mkdir(exist_ok=True)
        
        with open(heartbeat_file, "w") as f:
            json.dump(heartbeat_data, f, indent=2)
        
        # PATCHED: LIVE HEARTBEAT OUTPUT
        heartbeat_count = heartbeat_data['heartbeat_count']
        time_str = current_time.strftime('%H:%M:%S')
        print(f"💓 Heartbeat #{heartbeat_count} - {{time_str}} (PID: {{os.getpid()}})")
        
        # Update global counter
        globals()['heartbeat_count'] = heartbeat_count
        
        return True
        
    except Exception as e:
        print(f"❌ Heartbeat-Fehler: {{e}}")
        return False

def start_heartbeat_monitor():
    """Startet sichtbaren Heartbeat-Monitor"""
    import threading
    import time
    
    def heartbeat_worker():
        print(f"💓 Heartbeat-Monitor gestartet (Intervall: {task.heartbeat_interval}s)")
        print(f"👁️ Parent-PID: {self.parent_pid}, Task-PID: {{os.getpid()}}")
        print("=" * 50)
        
        while globals().get('heartbeat_active', True):
            try:
                if not check_parent_process():
                    print("❌ Parent-Prozess beendet - stoppe Heartbeat")
                    break
                
                update_heartbeat()
                
                # PATCHED: Progress-Indikator alle 5 Heartbeats
                heartbeat_count = globals().get('heartbeat_count', 0)
                if heartbeat_count % 5 == 0:  # Alle 5 Heartbeats
                    print(f"🔄 Task läuft seit {{heartbeat_count * {task.heartbeat_interval}}} Sekunden...")
                
                time.sleep({task.heartbeat_interval})
                
            except Exception as e:
                print(f"❌ Heartbeat-Monitor Fehler: {{e}}")
                time.sleep({task.heartbeat_interval})
        
        print("💓 Heartbeat-Monitor gestoppt")
    
    heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
    heartbeat_thread.start()
    return heartbeat_thread
'''
        
        # PATCHED: Progress Bar mit Live-Output für bessere Sichtbarkeit
        progress_code = """
# PATCHED: Working Progress Bar Setup
try:
    from tqdm import tqdm
    progress_available = True
    print("✅ Progress Bar (tqdm) verfügbar")
except ImportError:
    progress_available = False
    print("⚠️ Progress Bar nicht verfügbar - verwende Live-Output")
    
    class LiveTqdm:
        def __init__(self, total=None, desc="Progress", **kwargs):
            self.total = total or 100
            self.desc = desc
            self.current = 0
            self.start_time = time.time()
            print(f"📊 {self.desc}: Gestartet (Total: {self.total})")
        
        def __enter__(self):
            return self
        
        def __exit__(self, *args):
            elapsed = time.time() - self.start_time
            print(f"📊 {self.desc}: Abgeschlossen in {elapsed:.1f}s")
        
        def update(self, n=1):
            self.current += n
            if self.total > 0:
                percent = (self.current / self.total) * 100
                elapsed = time.time() - self.start_time
                rate = self.current / elapsed if elapsed > 0 else 0
                print(f"📊 {self.desc}: {self.current}/{self.total} ({percent:.1f}%) - {rate:.1f}/s")
        
        def set_description(self, desc):
            self.desc = desc
            print(f"📊 Status: {desc}")
    
    tqdm = LiveTqdm
""" if task.show_progress_bar else "progress_available = False"
        
        # Task-Funktion direkt verwenden (bereits korrekt formatiert)
        task_function_code = task.task_function.strip()
        
        script = f'''#!/usr/bin/env python3
"""
Enhanced Background Task: {task.scheduler_type}
PATCHED VERSION - Mit sichtbarem Progress/Heartbeat
"""

import os
import sys
import time
import signal
import threading
from pathlib import Path
from datetime import datetime

# Global Variables
heartbeat_active = True
heartbeat_count = 0

print("🚀 ENHANCED BACKGROUND TASK - PATCHED VERSION")
print("=" * 60)
print(f"📊 Task: {task.scheduler_type}")
print(f"🏷️ Scheduler: {self.scheduler_name}")
print(f"👁️ Parent-PID: {self.parent_pid}")
print(f"🆔 Task-PID: {{os.getpid()}}")
print(f"💓 Heartbeat-Intervall: {task.heartbeat_interval}s")
print(f"📁 Heartbeat-Datei: {task.heartbeat_file}")
print(f"⏰ Gestartet: {{datetime.now().strftime('%H:%M:%S')}}")
print("=" * 60)

# Project root hinzufügen
project_root = Path("{self.project_root}")
sys.path.insert(0, str(project_root))

# Enhanced Imports mit Live-Output
print("📦 Lade Module...")
{dependencies_imports}

{progress_code}

{heartbeat_code}

# Parent-Process-Monitoring mit Live-Output
def check_parent_process():
    """Prüft ob Parent-Prozess noch läuft"""
    try:
        import psutil
        parent_pid = {self.parent_pid}
        if not psutil.pid_exists(parent_pid):
            print(f"❌ Parent-Prozess {{parent_pid}} beendet - stoppe Task")
            return False
        return True
    except Exception as e:
        print(f"⚠️ Parent-Process-Check Fehler: {{e}}")
        return True

# Signal Handler mit Cleanup
def signal_handler(signum, frame):
    global heartbeat_active
    print(f"\\n⏹️ Signal {{signum}} empfangen - beende Task graceful")
    heartbeat_active = False
    
    # Cleanup Heartbeat-Datei
    try:
        heartbeat_file = Path("{task.heartbeat_file}")
        if heartbeat_file.exists():
            heartbeat_file.unlink()
            print("🧹 Heartbeat-Datei entfernt")
    except Exception as e:
        print(f"⚠️ Heartbeat-Cleanup Fehler: {{e}}")
    
    print("👋 Task wird beendet...")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Task-Funktion (BEREITS KORREKT FORMATIERT)
{task_function_code}

# PATCHED: MAIN EXECUTION MIT SICHTBAREM PROGRESS
if __name__ == "__main__":
    try:
        print("\\n💓 Starte Heartbeat-System...")
        
        # Initialer Heartbeat
        if update_heartbeat():
            print("✅ Initialer Heartbeat erfolgreich")
        else:
            print("❌ Initialer Heartbeat fehlgeschlagen")
        
        # Heartbeat-Monitor starten
        print("💓 Starte Heartbeat-Monitor...")
        heartbeat_thread = start_heartbeat_monitor()
        
        print("\\n🚀 STARTE TASK-AUSFÜHRUNG...")
        print("=" * 60)
        
        # Task ausführen mit Live-Progress
        task_start_time = time.time()
        {task.scheduler_type.replace('-', '_')}()
        task_duration = time.time() - task_start_time
        
        print("=" * 60)
        print(f"✅ Enhanced Background Task abgeschlossen")
        print(f"⏱️ Laufzeit: {{task_duration:.1f}} Sekunden")
        print(f"💓 Heartbeats gesendet: {{globals().get('heartbeat_count', 0)}}")
        
    except KeyboardInterrupt:
        print("\\n⏹️ Task durch Benutzer abgebrochen (Ctrl+C)")
    except Exception as e:
        print(f"❌ Task-Fehler: {{e}}")
        import traceback
        print("🔍 Vollständiger Traceback:")
        traceback.print_exc()
    finally:
        # Cleanup
        print("\\n🧹 Task-Cleanup...")
        heartbeat_active = False
        
        try:
            heartbeat_file = Path("{task.heartbeat_file}")
            if heartbeat_file.exists():
                heartbeat_file.unlink()
                print("✅ Heartbeat-Datei entfernt")
        except Exception as e:
            print(f"⚠️ Cleanup-Fehler: {{e}}")
        
        print("👋 Enhanced Background Task beendet")
        print(f"⏰ Beendet um: {{datetime.now().strftime('%H:%M:%S')}}")
        
        # Fenster offen halten für Debugging
        try:
            input("\\n📋 Drücke Enter zum Schließen...")
        except:
            time.sleep(5)  # Fallback
'''
        
        return script
    
    # =====================================================================
    # PATCHED: ASYNC TERMINAL PROCESS EXECUTION
    # =====================================================================
    
    def _start_enhanced_terminal_process(self, script_path: str, scheduler_type: str) -> Optional[subprocess.Popen]:
        """
        PATCHED: Startet Terminal wirklich asynchron ohne Main zu blockieren
        
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
echo 🚀 ENHANCED Background Scheduler v2.0 - ASYNC
echo ================================================================
echo 📊 Scheduler: {self.scheduler_name}
echo 🎯 Task: {scheduler_type}
echo 👁️ Parent-Monitoring: AKTIVIERT
echo 💓 Sign of Life: AKTIVIERT
echo ⏰ Zeit: %date% %time%
echo ================================================================
echo 💡 Läuft asynchron - Main Terminal bleibt frei
echo 💡 Parent-Process-Monitoring für saubere Beendigung
echo.
cd /d "{self.project_root}"
python "{script_path}"
echo.
echo 🏁 Task beendet - Fenster schließt in 10 Sekunden
timeout 10
'''
                batch_path = Path(f"temp_start_{scheduler_type}.bat")
                with open(batch_path, 'w', encoding='utf-8') as f:
                    f.write(batch_content)
                
                # PATCHED: Wirklich asynchron starten mit DETACHED_PROCESS
                process = subprocess.Popen(
                    ['cmd', '/c', 'start', '/min', str(batch_path)],  # /min für minimiert
                    cwd=str(self.project_root),
                    creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.DETACHED_PROCESS,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL
                )
                
            else:  # Unix/Linux/macOS
                shell_content = f'''#!/bin/bash
echo "🔄 {terminal_title}"
echo "================================================================"
echo "📊 Scheduler: {self.scheduler_name}"
echo "🎯 Task: {scheduler_type}"
echo "👁️ Parent-Monitoring: AKTIVIERT"
echo "💓 Sign of Life: AKTIVIERT"
echo "⏰ Zeit: $(date)"
echo "================================================================"
echo "💡 Läuft asynchron - Main Terminal bleibt frei"
echo ""
cd "{self.project_root}"
python3 "{script_path}"
echo ""
echo "🏁 Task beendet - Fenster schließt in 10 Sekunden"
sleep 10
'''
                shell_path = Path(f"temp_start_{scheduler_type}.sh")
                with open(shell_path, 'w', encoding='utf-8') as f:
                    f.write(shell_content)
                
                os.chmod(shell_path, 0o755)
                
                # PATCHED: Wirklich asynchron starten
                terminal_commands = [
                    ['gnome-terminal', '--', 'bash', str(shell_path)],
                    ['xterm', '-e', f'bash {shell_path}'],
                    ['konsole', '-e', f'bash {shell_path}'],
                ]
                
                process = None
                for cmd in terminal_commands:
                    try:
                        process = subprocess.Popen(
                            cmd, 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL,
                            stdin=subprocess.DEVNULL,
                            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
                        )
                        break
                    except (FileNotFoundError, subprocess.SubprocessError):
                        continue
                
                if not process:
                    # Fallback: Hintergrund-Prozess ohne Terminal
                    process = subprocess.Popen(
                        ['python3', script_path], 
                        cwd=str(self.project_root),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        stdin=subprocess.DEVNULL,
                        preexec_fn=os.setsid if hasattr(os, 'setsid') else None
                    )
            
            print(f"🚀 ASYNC Prozess gestartet: {scheduler_type} (PID: {process.pid})")
            return process
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten des ASYNC Terminal-Prozesses: {e}")
            return None
    
    # =====================================================================
    # HELPER METHODS - UNCHANGED
    # =====================================================================
    
    def _format_dependencies_import(self, dependencies: List[str]) -> str:
        """Formatiert Enhanced Import-Statements für Dependencies"""
        if not dependencies:
            return ""
        
        imports = []
        for dep in dependencies:
            if '.' in dep:
                module, submodule = dep.rsplit('.', 1)
                imports.append(f"""try:
    from {module} import {submodule}
    print(f"✅ Enhanced Import: {submodule} from {module}")
except ImportError as e:
    print(f"❌ Enhanced Import Failed: {submodule} from {module}: {{e}}")
    raise""")
            else:
                imports.append(f"""try:
    import {dep}
    print(f"✅ Enhanced Import: {dep}")
except ImportError as e:
    print(f"❌ Enhanced Import Failed: {dep}: {{e}}")
    raise""")
        
        return '\n'.join(imports)
    
    def _init_task_heartbeat(self, task: SchedulerTask):
        """Initialisiert Heartbeat für Task"""
        try:
            heartbeat_data = {
                "task_type": task.scheduler_type,
                "scheduler_name": self.scheduler_name,
                "started_at": datetime.now().isoformat(),
                "last_heartbeat": datetime.now().isoformat(),
                "status": "starting",
                "parent_pid": self.parent_pid,
                "process_pid": task.process.pid if task.process else None
            }
            
            with open(task.heartbeat_file, 'w') as f:
                json.dump(heartbeat_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Initialisieren des Heartbeats: {e}")
    
    # =====================================================================
    # PATCHED: IMPROVED HEARTBEAT CHECKING
    # =====================================================================
    
    def _check_task_heartbeat(self, task: SchedulerTask):
        """
        PATCHED: Verbesserte Heartbeat-Prüfung mit toleranterer Logik
        
        Args:
            task: Task der geprüft werden soll
        """
        try:
            if not task.heartbeat_file or not task.heartbeat_file.exists():
                # Nur warnen wenn Task als laufend markiert ist
                if task.running:
                    logger.debug(f"Task {task.scheduler_type}: Heartbeat-Datei fehlt")
                return
            
            with open(task.heartbeat_file, 'r') as f:
                heartbeat_data = json.load(f)
            
            last_heartbeat = datetime.fromisoformat(heartbeat_data.get('last_heartbeat', ''))
            time_diff = (datetime.now() - last_heartbeat).total_seconds()
            heartbeat_count = heartbeat_data.get('heartbeat_count', 0)
            
            # PATCHED: Viel tolerantere Heartbeat-Prüfung
            max_age = task.heartbeat_interval * 6  # 6x Intervall statt 3x als Maximum
            
            if time_diff > max_age:
                if task.running:  # Nur loggen wenn Status sich ändert
                    logger.warning(f"Task {task.scheduler_type} Heartbeat zu alt ({time_diff:.1f}s) - markiere als gestoppt")
                    task.running = False
            else:
                # Heartbeat ist aktuell
                if not task.running and task.process and task.process.poll() is None:
                    logger.info(f"💚 Task {task.scheduler_type} Heartbeat wiederhergestellt (#{heartbeat_count})")
                    task.running = True
                    
        except Exception as e:
            logger.debug(f"Heartbeat check error für {task.scheduler_type}: {e}")
    
    # =====================================================================
    # PATCHED: QUIET CLEANUP
    # =====================================================================
    
    def _cleanup_finished_processes(self):
        """PATCHED: Räumt beendete Prozesse auf ohne Spam-Logging"""
        finished_tasks = []
        
        for task_type, task in self.tasks.items():
            if task.process and task.process.poll() is not None:
                # Prozess ist beendet
                if task.running:  # Nur loggen wenn Status sich ändert
                    logger.info(f"Task {task_type} beendet")
                    task.running = False
                finished_tasks.append(task_type)
                
                # Cleanup
                if task.heartbeat_file and task.heartbeat_file.exists():
                    try:
                        task.heartbeat_file.unlink()
                    except Exception:
                        pass
        
        for task_type in finished_tasks:
            if task_type in self.processes:
                del self.processes[task_type]
            # PATCHED: Kein Spam-Logging mehr - nur Debug
            logger.debug(f"Task {task_type} cleanup abgeschlossen")
    
    def _cleanup_processes(self):
        """Stoppt alle laufenden Prozesse"""
        for task in self.tasks.values():
            if task.process and task.process.poll() is None:
                try:
                    task.process.terminate()
                    task.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    task.process.kill()
                except Exception as e:
                    logger.debug(f"Process cleanup error: {e}")
                
                task.running = False
    
    def _start_parent_monitoring(self):
        """Startet Parent-Process-Monitoring"""
        self.monitoring_active = True
        
        def monitor_parent():
            while self.monitoring_active:
                try:
                    if not psutil.pid_exists(self.parent_pid):
                        logger.warning("⚠️ Parent-Prozess beendet - stoppe alle Tasks")
                        self.stop_scheduler()
                        break
                    time.sleep(10)
                except Exception as e:
                    logger.debug(f"Parent monitoring error: {e}")
                    time.sleep(10)
        
        self.monitoring_thread = threading.Thread(target=monitor_parent, daemon=True)
        self.monitoring_thread.start()

# =====================================================================
# ENHANCED SCHEDULER FACTORY FUNCTIONS - UNCHANGED
# =====================================================================

def create_enhanced_price_tracker_scheduler() -> EnhancedBackgroundScheduler:
    """Erstellt Enhanced BackgroundScheduler für Price Tracking"""
    scheduler = EnhancedBackgroundScheduler(
        scheduler_name="PriceTracker",
        base_config={
            "steam_api_rate_limit": 1.0,
            "max_concurrent_updates": 5,
            "enhanced_features": True,
            "version": "2.0"
        }
    )
    
    # Enhanced Price Tasks registrieren
    scheduler.register_scheduler(
        scheduler_type="price_updates",
        task_function=EnhancedSchedulerTasks.enhanced_price_tracking_task(),
        interval_minutes=360,  # 6 Stunden
        dependencies=["price_tracker", "steam_wishlist_manager"],
        heartbeat_interval=60,  # PATCHED: Erhöht auf 60s
        show_progress_bar=True
    )
    
    scheduler.register_scheduler(
        scheduler_type="name_updates", 
        task_function=EnhancedSchedulerTasks.enhanced_name_update_task(),
        interval_minutes=30,  # 30 Minuten
        dependencies=["price_tracker", "steam_wishlist_manager"],
        heartbeat_interval=60,  # PATCHED: Erhöht auf 60s
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
        interval_minutes=360,  # 6 Stunden
        dependencies=["price_tracker", "steam_wishlist_manager", "steam_charts_manager"],
        heartbeat_interval=60,  # PATCHED: Erhöht auf 60s
        show_progress_bar=True
    )
    
    # Charts Price Updates Task
    scheduler.register_scheduler(
        scheduler_type="charts_price_updates",
        task_function=EnhancedSchedulerTasks.enhanced_charts_price_update_task(),
        interval_minutes=240,  # 4 Stunden
        dependencies=["price_tracker", "steam_wishlist_manager"],
        heartbeat_interval=60,  # PATCHED: Erhöht auf 60s
        show_progress_bar=True
    )
    
    scheduler.register_scheduler(
        scheduler_type="charts_cleanup",
        task_function=EnhancedSchedulerTasks.enhanced_charts_cleanup_task(),
        interval_minutes=1440,  # 24 Stunden
        dependencies=["price_tracker", "steam_wishlist_manager"],
        heartbeat_interval=60,  # PATCHED: Erhöht auf 60s
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
# HILFSFUNKTIONEN FÜR PROCESS MANAGEMENT - UNCHANGED
# =====================================================================

def register_background_process(process: subprocess.Popen, scheduler_id: str = None, 
                               scheduler_type: str = "unknown", config: Dict = None) -> bool:
    """
    Hilfsfunktion zum Registrieren von Background-Prozessen
    
    Args:
        process: Subprocess.Popen Objekt
        scheduler_id: Eindeutige ID (wird automatisch generiert falls None)
        scheduler_type: Typ des Schedulers
        config: Zusätzliche Konfiguration
        
    Returns:
        True wenn erfolgreich registriert
    """
    if scheduler_id is None:
        scheduler_id = f"{scheduler_type}_{process.pid}_{int(time.time())}"
    
    return _global_process_manager.register_process(
        scheduler_id=scheduler_id,
        process=process,
        scheduler_type=scheduler_type,
        config=config
    )

def get_all_process_status() -> Dict:
    """
    Gibt Status aller Background-Prozesse zurück
    
    Returns:
        Dictionary mit Status-Informationen
    """
    return _global_process_manager.get_process_status()

def cleanup_all_background_processes() -> int:
    """
    Stoppt alle Background-Prozesse
    
    Returns:
        Anzahl gestoppter Prozesse
    """
    return _global_process_manager.cleanup_all_processes()

def stop_background_process(scheduler_id: str) -> bool:
    """
    Stoppt einen spezifischen Background-Prozess
    
    Args:
        scheduler_id: ID des zu stoppenden Prozesses
        
    Returns:
        True wenn erfolgreich gestoppt
    """
    return _global_process_manager.stop_process(scheduler_id)

# =====================================================================
# FIXED PROCESS MANAGEMENT TERMINAL - UNCHANGED
# =====================================================================

def create_process_management_terminal() -> bool:
    """
    Startet Enhanced Process Management Terminal für zentrale Kontrolle
    Mit echter Benutzer-Interaktion
    
    Returns:
        True wenn erfolgreich gestartet
    """
    try:
        terminal_script = '''#!/usr/bin/env python3
"""
Enhanced Process Management Terminal v2.0
Zentrale Kontrolle für alle Background-Scheduler
Mit echter Benutzer-Interaktion
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
        from background_scheduler import get_all_process_status
        
        status = get_all_process_status()
        
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

def stop_all_processes():
    """Stoppt alle getrackten Prozesse"""
    try:
        from background_scheduler import cleanup_all_background_processes
        stopped = cleanup_all_background_processes()
        print(f"✅ {stopped} Prozesse gestoppt")
        return True
    except Exception as e:
        print(f"❌ Fehler beim Stoppen der Prozesse: {e}")
        return False

def show_system_resources():
    """Zeigt System-Ressourcen"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        print("\\n💻 SYSTEM-RESSOURCEN:")
        print(f"   🖥️ CPU: {cpu_percent:.1f}%")
        print(f"   🧠 RAM: {memory.percent:.1f}% ({memory.used // (1024**3):.1f}GB / {memory.total // (1024**3):.1f}GB)")
        print(f"   💾 Disk: {disk.percent:.1f}% ({disk.used // (1024**3):.1f}GB / {disk.total // (1024**3):.1f}GB)")
        
    except Exception as e:
        print(f"❌ Fehler beim Laden der System-Ressourcen: {e}")

def show_heartbeats():
    """Zeigt Heartbeat-Status der Tasks"""
    try:
        heartbeat_dir = Path("heartbeats")
        if not heartbeat_dir.exists():
            print("\\n💓 Keine Heartbeat-Dateien gefunden")
            return
        
        heartbeat_files = list(heartbeat_dir.glob("*_heartbeat.json"))
        if not heartbeat_files:
            print("\\n💓 Keine aktiven Heartbeats")
            return
        
        print("\\n💓 HEARTBEAT STATUS:")
        import json
        for heartbeat_file in heartbeat_files:
            try:
                with open(heartbeat_file, 'r') as f:
                    data = json.load(f)
                
                last_heartbeat = datetime.fromisoformat(data['last_heartbeat'])
                age = (datetime.now() - last_heartbeat).total_seconds()
                status_icon = "💚" if age < 60 else "💛" if age < 180 else "❤️"
                heartbeat_count = data.get('heartbeat_count', 0)
                
                print(f"   {status_icon} {data['task_type']}: #{heartbeat_count} - {age:.0f}s alt")
                
            except Exception as e:
                print(f"   ❌ Fehler beim Lesen von {heartbeat_file.name}: {e}")
        
    except Exception as e:
        print(f"❌ Fehler beim Laden der Heartbeats: {e}")

def main():
    """Hauptschleife des Process Management Terminals mit echter Interaktion"""
    print("🚀 ENHANCED PROCESS MANAGEMENT TERMINAL v2.0")
    print("💡 Mit echter Benutzer-Interaktion")
    print("=" * 60)
    
    try:
        while True:
            # Status anzeigen
            status = show_process_status()
            
            print("\\n🔧 VERFÜGBARE AKTIONEN:")
            print("1. 🔄 Status aktualisieren")
            print("2. ⏹️ Alle Prozesse beenden")
            print("3. 💻 System-Ressourcen anzeigen")
            print("4. 💓 Heartbeat-Status anzeigen")
            print("5. 🧹 Heartbeat-Dateien bereinigen")
            print("0. ❌ Beenden")
            
            try:
                choice = input("\\n👉 Wähle eine Option (0-5): ").strip()
                
                if choice == "1":
                    # Status wird automatisch beim nächsten Loop angezeigt
                    print("🔄 Status wird aktualisiert...")
                    time.sleep(1)
                    
                elif choice == "2":
                    print("\\n⚠️ Alle Prozesse beenden? (j/N): ", end="")
                    confirm = input().strip().lower()
                    if confirm in ['j', 'ja', 'y', 'yes']:
                        stop_all_processes()
                    else:
                        print("❌ Abgebrochen")
                    input("\\nDrücke Enter um fortzufahren...")
                    
                elif choice == "3":
                    show_system_resources()
                    input("\\nDrücke Enter um fortzufahren...")
                    
                elif choice == "4":
                    show_heartbeats()
                    input("\\nDrücke Enter um fortzufahren...")
                    
                elif choice == "5":
                    heartbeat_dir = Path("heartbeats")
                    if heartbeat_dir.exists():
                        heartbeat_files = list(heartbeat_dir.glob("*.json"))
                        for file in heartbeat_files:
                            try:
                                file.unlink()
                            except Exception:
                                pass
                        print(f"🧹 {len(heartbeat_files)} Heartbeat-Dateien bereinigt")
                    else:
                        print("💡 Keine Heartbeat-Dateien gefunden")
                    input("\\nDrücke Enter um fortzufahren...")
                    
                elif choice == "0":
                    print("\\n👋 Process Management Terminal wird beendet...")
                    break
                    
                else:
                    print("❌ Ungültige Option. Bitte 0-5 eingeben.")
                    time.sleep(1)
                
                # Clear screen für bessere Übersicht
                os.system('cls' if os.name == 'nt' else 'clear')
                
            except KeyboardInterrupt:
                print("\\n\\n⏹️ Strg+C erkannt - beende Terminal...")
                break
            except EOFError:
                print("\\n\\n⏹️ EOF erkannt - beende Terminal...")
                break
                
    except KeyboardInterrupt:
        print("\\n⏹️ Stoppe alle Prozesse vor dem Beenden...")
        stop_all_processes()
        print("👋 Enhanced Process Management Terminal beendet")

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
            
            process = subprocess.Popen(
                ['cmd', '/c', 'start', str(batch_path)],
                cwd=str(Path.cwd()),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            # Process registrieren
            register_background_process(
                process=process,
                scheduler_id="process_management_terminal",
                scheduler_type="management_terminal"
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
            
            process = None
            for cmd in terminal_commands:
                try:
                    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    break
                except (FileNotFoundError, subprocess.SubprocessError):
                    continue
            
            if process:
                register_background_process(
                    process=process,
                    scheduler_id="process_management_terminal",
                    scheduler_type="management_terminal"
                )
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Starten des Process Management Terminals: {e}")
        return False

# =====================================================================
# ATEXIT HANDLER FÜR AUTOMATISCHES CLEANUP - UNCHANGED
# =====================================================================

def register_atexit_cleanup():
    """Registriert automatisches Cleanup beim Programm-Exit"""
    if _global_process_manager.cleanup_registered:
        return
    
    def cleanup_handler():
        try:
            stopped = cleanup_all_background_processes()
            if stopped > 0:
                print(f"\n🧹 Automatisches Cleanup: {stopped} Background-Prozesse gestoppt")
        except Exception as e:
            logger.debug(f"Atexit cleanup error: {e}")
    
    atexit.register(cleanup_handler)
    _global_process_manager.cleanup_registered = True
    logger.info("✅ Automatisches Cleanup registriert")

# Automatisches Cleanup aktivieren
register_atexit_cleanup()

# =====================================================================
# ENHANCED MAIN & TEST FUNCTIONS - UNCHANGED
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
        print("5. 🔧 Process Management Terminal starten")
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
                    status = get_all_process_status()
                    print(f"\n📊 SCHEDULER-STATUS:")
                    print(f"   🔧 Getrackte Prozesse: {status['total_tracked']}")
                    print(f"   ✅ Laufende Prozesse: {status['running_processes']}")
                    print(f"   💀 Tote Prozesse: {status['dead_processes']}")
                    
                    if status['processes']:
                        print("\n📋 AKTIVE PROZESSE:")
                        for scheduler_id, proc_info in status['processes'].items():
                            status_icon = "✅" if proc_info['is_running'] else "💀"
                            print(f"   {status_icon} {scheduler_id} (PID: {proc_info['pid']})")
                
                elif choice == "4":
                    for name, scheduler in schedulers.items():
                        print(f"⏹️ Stoppe {name} Scheduler...")
                        scheduler.stop_scheduler()
                    schedulers.clear()
                    stopped = cleanup_all_background_processes()
                    print(f"✅ Alle Scheduler gestoppt ({stopped} Prozesse)")
                
                elif choice == "5":
                    if create_process_management_terminal():
                        print("✅ Process Management Terminal gestartet")
                    else:
                        print("❌ Fehler beim Starten des Process Management Terminals")
                
                elif choice == "0":
                    # Cleanup
                    for scheduler in schedulers.values():
                        scheduler.stop_scheduler()
                    cleanup_all_background_processes()
                    print("👋 Auf Wiedersehen!")
                    break
                
                else:
                    print("❌ Ungültige Option")
                    
            except KeyboardInterrupt:
                print("\n🛑 Beende Process Management Terminal...")
                for scheduler in schedulers.values():
                    scheduler.stop_scheduler()
                cleanup_all_background_processes()
                break
            except Exception as e:
                print(f"❌ Fehler: {e}")
                
    except Exception as e:
        print(f"❌ Kritischer Fehler im Process Management Terminal: {e}")

def test_enhanced_scheduler_v2():
    """Test-Funktion für Enhanced Scheduler v2.0"""
    print("🧪 TESTE ENHANCED UNIVERSAL BACKGROUND SCHEDULER v2.0 - PATCHED")
    print("=" * 70)
    print("💡 Features: Automatisches Cleanup, Parent-Monitoring, Process Management")
    print("🔧 PATCHES: Async Execution, Improved Registration, Working Scripts, Tolerant Heartbeat")
    print()
    
    try:
        # Enhanced Scheduler testen
        price_scheduler = create_enhanced_price_tracker_scheduler()
        charts_scheduler = create_enhanced_charts_scheduler()
        
        print("✅ Enhanced Scheduler erstellt")
        
        # Process Manager Status
        process_status = get_all_process_status()
        print(f"📊 Process Manager: {process_status['total_tracked']} getrackte Prozesse")
        
        # Management Terminal starten
        if create_process_management_terminal():
            print("✅ Process Management Terminal gestartet")
        
        print("\n🎉 Enhanced Scheduler v2.0 Test erfolgreich!")
        print("💡 Automatisches Cleanup beim Hauptprogramm-Exit aktiviert!")
        print("🔧 Alle PATCHES implementiert!")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced Scheduler v2.0 Test fehlgeschlagen: {e}")
        return False

# Kompatibilitäts-Test-Funktion
def test_enhanced_scheduler():
    """Kompatibilitäts-Alias für Enhanced Test"""
    return test_enhanced_scheduler_v2()

def test_process_manager():
    """Test-Funktion für Process Manager"""
    print("🧪 TESTE GLOBAL PROCESS MANAGER - PATCHED VERSION")
    print("=" * 40)
    
    try:
        # Status abrufen
        status = get_all_process_status()
        print(f"📊 Getrackte Prozesse: {status['total_tracked']}")
        print(f"✅ Laufende Prozesse: {status['running_processes']}")
        
        # Test Terminal starten
        if create_process_management_terminal():
            print("✅ Process Management Terminal Test erfolgreich")
        else:
            print("❌ Process Management Terminal Test fehlgeschlagen")
            
        return True
        
    except Exception as e:
        print(f"❌ Process Manager Test fehlgeschlagen: {e}")
        return False

# =====================================================================
# STARTUP MESSAGE
# =====================================================================

logger.info("🚀 Enhanced Universal Background Scheduler v2.0 - COMPLETE PATCHED VERSION geladen")
logger.info("✅ Alle Features verfügbar: Process Management, Parent-Monitoring, Auto-Cleanup")
logger.info("🔧 PATCHES: Async Execution, Improved Registration, Working Scripts, Tolerant Heartbeat, Quiet Cleanup")

if __name__ == "__main__":
    main()
