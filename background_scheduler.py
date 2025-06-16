#!/usr/bin/env python3
"""
Universal Background Scheduler - CORRECTED VERSION
Universeller Scheduler für alle Background-Tasks in separaten Terminals
FIXED: Korrekte Imports und Module-Erkennung
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
    CORRECTED: Korrekte Module-Imports und Pfad-Handling
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
        
        # CORRECTED: Python-Pfad für korrekte Imports
        self.project_root = Path.cwd()
        
        logger.info(f"✅ Universal Background Scheduler '{scheduler_name}' initialisiert")
    
    def register_scheduler(self, 
                          scheduler_type: str,
                          task_function: str,
                          interval_minutes: int,
                          task_config: Dict = None,
                          dependencies: List[str] = None) -> bool:
        """
        Registriert einen neuen Scheduler-Typ
        
        Args:
            scheduler_type: Typ des Schedulers (z.B. 'price_updates', 'name_updates')
            task_function: Python-Funktion die ausgeführt werden soll
            interval_minutes: Intervall in Minuten
            task_config: Konfiguration für die Task
            dependencies: Erforderliche Python-Module
            
        Returns:
            True wenn erfolgreich registriert
        """
        try:
            self.scheduler_configs[scheduler_type] = {
                'task_function': task_function,
                'interval_minutes': interval_minutes,
                'task_config': task_config or {},
                'dependencies': dependencies or [],
                'registered_at': datetime.now().isoformat(),
                'enabled': False
            }
            
            logger.info(f"✅ Scheduler '{scheduler_type}' registriert (Intervall: {interval_minutes}min)")
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
            script_path = self._create_scheduler_script(scheduler_type, **kwargs)
            
            # Separaten Terminal-Prozess starten
            process = self._start_terminal_process(script_path, scheduler_type)
            
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
    
    def _create_scheduler_script(self, scheduler_type: str, **kwargs) -> str:
        """
        CORRECTED: Erstellt temporäres Python-Script mit korrekten Imports
        
        Args:
            scheduler_type: Typ des Schedulers
            **kwargs: Zusätzliche Parameter
            
        Returns:
            Pfad zum erstellten Script
        """
        config = self.scheduler_configs[scheduler_type]
        
        # CORRECTED: Script-Inhalt mit robusten Imports
        script_content = f'''#!/usr/bin/env python3
"""
Background Scheduler: {scheduler_type}
Auto-generated scheduler script für separate Terminal-Ausführung
Scheduler: {self.scheduler_name}
CORRECTED: Robuste Import-Behandlung
"""

import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

# CORRECTED: Aktuelles Verzeichnis zum Python-Pfad hinzufügen
project_root = Path("{self.project_root}")
sys.path.insert(0, str(project_root))

# Konfiguration
SCHEDULER_TYPE = "{scheduler_type}"
INTERVAL_MINUTES = {config['interval_minutes']}
TASK_CONFIG = {json.dumps(config.get('task_config', {}), indent=4)}
BASE_CONFIG = {json.dumps(self.base_config, indent=4)}
KWARGS = {json.dumps(kwargs, indent=4)}

print("🚀 Background Scheduler gestartet")
print("=" * 50)
print(f"📊 Scheduler: {self.scheduler_name}")
print(f"🎯 Task: {scheduler_type}")
print(f"⏰ Intervall: {{INTERVAL_MINUTES}} Minuten")
print(f"🚀 Gestartet: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
print(f"📁 Working Directory: {{project_root}}")
print("⚠️ Drücke Ctrl+C zum Beenden")
print()

try:
    # CORRECTED: Dependencies importieren mit Fehlerbehandlung
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
    
    # Hauptschleife
    cycle = 0
    while True:
        cycle += 1
        print(f"\\n🔄 Zyklus {{cycle}} - {{datetime.now().strftime('%H:%M:%S')}}")
        
        success = execute_task()
        
        if success:
            print(f"✅ Task erfolgreich ausgeführt")
        else:
            print(f"❌ Task fehlgeschlagen")
        
        print(f"⏳ Nächste Ausführung in {{INTERVAL_MINUTES}} Minuten...")
        time.sleep(INTERVAL_MINUTES * 60)

except KeyboardInterrupt:
    print("\\n⏹️ Scheduler gestoppt durch Benutzer")
except ImportError as e:
    print(f"❌ Import-Fehler: {{e}}")
    print("💡 Prüfe ob alle Module verfügbar sind:")
    print(f"   - Arbeitsverzeichnis: {{project_root}}")
    print(f"   - Python-Pfad: {{sys.path[:3]}}")
    print("💡 Starte das Hauptprogramm vom richtigen Verzeichnis")
except Exception as e:
    print(f"❌ Unerwarteter Fehler: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''
        
        # Script-Datei erstellen
        script_filename = f"scheduler_{self.scheduler_name}_{scheduler_type}.py"
        script_path = self.temp_dir / script_filename
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        return str(script_path)
    
    def _generate_import_statements_corrected(self, dependencies: List[str]) -> str:
        """
        CORRECTED: Generiert robuste Import-Statements
        
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
        CORRECTED: Formatiert Task-Funktion für korrekten Einzug
        
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
    
    def _start_terminal_process(self, script_path: str, scheduler_type: str) -> Optional[subprocess.Popen]:
        """
        CORRECTED: Startet Script in separatem Terminal mit robusteren Optionen
        
        Args:
            script_path: Pfad zum Python-Script
            scheduler_type: Typ des Schedulers (für Terminal-Titel)
            
        Returns:
            Subprocess.Popen Objekt oder None
        """
        terminal_title = f"Steam Price Tracker - {self.scheduler_name} - {scheduler_type}"
        
        try:
            if os.name == 'nt':  # Windows
                return subprocess.Popen([
                    'cmd', '/c', 'start', 
                    f'"{terminal_title}"',
                    'cmd', '/k', 
                    f'cd /d "{self.project_root}" && python "{script_path}"'
                ], shell=True)
            
            else:  # Linux/macOS
                # CORRECTED: Robuste Terminal-Erkennung mit Working Directory
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
                        logger.debug(f"Versuche Terminal: {terminal_name}")
                        return subprocess.Popen(cmd, cwd=str(self.project_root))
                    except FileNotFoundError:
                        continue
                
                # CORRECTED: Fallback mit korrektem Working Directory
                logger.warning(f"⚠️ Kein GUI-Terminal gefunden - starte im Hintergrund")
                return subprocess.Popen([
                    'python3', script_path
                ], cwd=str(self.project_root))
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten des Terminal-Prozesses: {e}")
            return None
    
    def _cleanup_scheduler_files(self, scheduler_type: str):
        """
        Räumt temporäre Dateien für einen Scheduler auf
        
        Args:
            scheduler_type: Typ des Schedulers
        """
        try:
            script_filename = f"scheduler_{self.scheduler_name}_{scheduler_type}.py"
            script_path = self.temp_dir / script_filename
            
            if script_path.exists():
                script_path.unlink()
                logger.debug(f"🧹 Temporäre Datei entfernt: {script_path}")
                
        except Exception as e:
            logger.debug(f"⚠️ Fehler beim Aufräumen von {scheduler_type}: {e}")
    
    def cleanup_all_files(self):
        """Räumt alle temporären Dateien auf"""
        try:
            if self.temp_dir.exists():
                for file in self.temp_dir.glob("scheduler_*.py"):
                    file.unlink()
                
                # Verzeichnis entfernen falls leer
                try:
                    self.temp_dir.rmdir()
                except OSError:
                    pass  # Verzeichnis nicht leer
                    
                logger.info("🧹 Alle temporären Scheduler-Dateien entfernt")
                
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Aufräumen: {e}")


# =====================================================================
# SCHEDULER TASK DEFINITIONS - CORRECTED
# =====================================================================

class SchedulerTasks:
    """
    Sammlung vordefinierter Task-Funktionen für verschiedene Scheduler
    CORRECTED: Korrekte Import-Behandlung und Fehlerbehandlung
    """
    
    @staticmethod
    def price_tracking_task():
        """CORRECTED: Task für automatisches Preis-Tracking"""
        return '''
# Preis-Tracking Task - CORRECTED VERSION
from price_tracker import create_price_tracker
from steam_wishlist_manager import load_api_key_from_env

api_key = load_api_key_from_env()
tracker = create_price_tracker(api_key=api_key, enable_charts=True)

if not tracker.charts_enabled:
    print("❌ Charts nicht verfügbar")
    return

# Charts-Preise aktualisieren
print("💰 Starte Charts-Preis-Update...")
result = tracker.update_charts_prices_now()

if result.get('success', True):
    print(f"✅ Charts-Preise erfolgreich:")
    print(f"   💰 {result.get('successful', 0)} Apps aktualisiert")
    
    if result.get('failed', 0) > 0:
        print(f"   ❌ {result['failed']} fehlgeschlagen")
else:
    print(f"❌ Charts-Preise fehlgeschlagen: {result.get('error')}")
'''
    
    @staticmethod
    def name_update_task():
        """CORRECTED: Task für automatische Namen-Updates"""
        return '''
# Namen-Update Task - CORRECTED VERSION
from price_tracker import create_price_tracker
from steam_wishlist_manager import load_api_key_from_env

api_key = load_api_key_from_env()
if not api_key:
    print("❌ Kein Steam API Key - Namen-Updates übersprungen")
    return

tracker = create_price_tracker(api_key=api_key, enable_charts=True)

# Standard-Apps mit generischen Namen
standard_candidates = tracker.get_name_update_candidates()
standard_updated = 0

if standard_candidates:
    # Nur wenige Apps pro Durchlauf (Rate Limiting)
    batch_size = min(10, len(standard_candidates))
    batch_apps = standard_candidates[:batch_size]
    app_ids = [app['steam_app_id'] for app in batch_apps]
    
    print(f"📝 Aktualisiere {batch_size} Standard-Namen...")
    result = tracker.update_app_names_from_steam(app_ids, api_key)
    
    if result.get('success'):
        standard_updated = result['updated']
        print(f"✅ {result['updated']}/{batch_size} Standard-Namen aktualisiert")
    else:
        print(f"❌ Standard-Namen-Update fehlgeschlagen")

# Charts-Apps mit generischen Namen (falls verfügbar)
charts_updated = 0
if tracker.charts_enabled and hasattr(tracker.db_manager, 'get_active_chart_games'):
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
        else:
            print(f"❌ Charts-Namen-Update fehlgeschlagen")

if standard_updated == 0 and charts_updated == 0:
    if not standard_candidates and (not tracker.charts_enabled or not charts_candidates):
        print("✅ Alle Namen sind aktuell")
    else:
        print("⚠️ Namen-Updates fehlgeschlagen oder keine API-Zugriffe möglich")
else:
    print(f"🎉 Gesamt: {standard_updated + charts_updated} Namen aktualisiert")
'''
    
    @staticmethod
    def charts_cleanup_task():
        """CORRECTED: Task für Charts-Cleanup"""
        return '''
# Charts-Cleanup Task - CORRECTED VERSION
from price_tracker import create_price_tracker
from steam_wishlist_manager import load_api_key_from_env

api_key = load_api_key_from_env()
tracker = create_price_tracker(api_key=api_key, enable_charts=True)

if not tracker.charts_enabled:
    print("❌ Charts nicht verfügbar")
    return

print("🧹 Starte Charts-Cleanup...")

# Cleanup ausführen
if hasattr(tracker, 'charts_manager') and tracker.charts_manager:
    removed = tracker.charts_manager.cleanup_old_chart_games(days_threshold=30)
    
    if removed > 0:
        print(f"✅ {removed} alte Charts-Spiele entfernt")
    else:
        print("✅ Keine alten Charts-Spiele zum Entfernen")
    
    # Zusätzlich: Alte Preis-Snapshots bereinigen
    if hasattr(tracker.db_manager, 'cleanup_old_prices'):
        old_snapshots = tracker.db_manager.cleanup_old_prices(days=90)
        if old_snapshots > 0:
            print(f"🧹 {old_snapshots} alte Preis-Snapshots bereinigt")
else:
    print("❌ Charts-Manager nicht verfügbar")
'''


# =====================================================================
# CONVENIENCE FUNCTIONS - CORRECTED
# =====================================================================

def create_price_tracker_scheduler() -> BackgroundScheduler:
    """
    CORRECTED: Erstellt BackgroundScheduler für Price Tracker mit vordefinierten Tasks
    
    Returns:
        Konfigurierter BackgroundScheduler
    """
    scheduler = BackgroundScheduler(
        scheduler_name="PriceTracker",
        base_config={
            "rate_limit_seconds": 1.5,
            "batch_size": 50,
            "max_retries": 3
        }
    )
    
    # Standard Tasks registrieren
    scheduler.register_scheduler(
        scheduler_type="price_updates",
        task_function=SchedulerTasks.price_tracking_task(),
        interval_minutes=360,  # 6 Stunden
        dependencies=["price_tracker", "steam_wishlist_manager"]
    )
    
    scheduler.register_scheduler(
        scheduler_type="name_updates",
        task_function=SchedulerTasks.name_update_task(),
        interval_minutes=30,  # 30 Minuten
        dependencies=["price_tracker", "steam_wishlist_manager"]
    )
    
    return scheduler

def create_charts_scheduler() -> BackgroundScheduler:
    """
    CORRECTED: Erstellt BackgroundScheduler für Charts mit vordefinierten Tasks
    
    Returns:
        Konfigurierter BackgroundScheduler
    """
    scheduler = BackgroundScheduler(
        scheduler_name="Charts",
        base_config={
            "steam_api_rate_limit": 1.0,
            "max_charts_per_update": 100
        }
    )
    
    # Charts Tasks registrieren
    scheduler.register_scheduler(
        scheduler_type="charts_updates",
        task_function=SchedulerTasks.charts_update_task(),
        interval_minutes=360,  # 6 Stunden
        dependencies=["price_tracker", "steam_wishlist_manager", "steam_charts_manager"]
    )
    
    scheduler.register_scheduler(
        scheduler_type="charts_prices",
        task_function=SchedulerTasks.charts_price_update_task(),
        interval_minutes=240,  # 4 Stunden
        dependencies=["price_tracker", "steam_wishlist_manager"]
    )
    
    scheduler.register_scheduler(
        scheduler_type="charts_cleanup",
        task_function=SchedulerTasks.charts_cleanup_task(),
        interval_minutes=1440,  # 24 Stunden
        dependencies=["price_tracker", "steam_wishlist_manager"]
    )
    
    return scheduler

def setup_all_schedulers(enable_charts: bool = True) -> Dict[str, BackgroundScheduler]:
    """
    CORRECTED: Richtet alle Scheduler ein
    
    Args:
        enable_charts: Ob Charts-Scheduler erstellt werden soll
        
    Returns:
        Dict mit allen erstellten Schedulern
    """
    schedulers = {}
    
    # Price Tracker Scheduler
    schedulers['price_tracker'] = create_price_tracker_scheduler()
    
    # Charts Scheduler (optional)
    if enable_charts:
        schedulers['charts'] = create_charts_scheduler()
    
    logger.info(f"✅ {len(schedulers)} Scheduler eingerichtet")
    return schedulers

def test_scheduler_setup():
    """
    CORRECTED: Test-Funktion für Scheduler-Setup
    """
    print("🧪 TESTE UNIVERSAL BACKGROUND SCHEDULER")
    print("=" * 45)
    
    try:
        # Price Tracker Scheduler erstellen
        price_scheduler = create_price_tracker_scheduler()
        print(f"✅ Price Tracker Scheduler erstellt")
        
        # Charts Scheduler erstellen
        charts_scheduler = create_charts_scheduler()
        print(f"✅ Charts Scheduler erstellt")
        
        # Status anzeigen
        price_status = price_scheduler.get_scheduler_status()
        charts_status = charts_scheduler.get_scheduler_status()
        
        print(f"\n📊 PRICE TRACKER STATUS:")
        print(f"   📝 Registrierte Scheduler: {price_status['total_registered']}")
        print(f"   🏃 Laufende Scheduler: {price_status['total_running']}")
        
        print(f"\n📊 CHARTS STATUS:")
        print(f"   📝 Registrierte Scheduler: {charts_status['total_registered']}")
        print(f"   🏃 Laufende Scheduler: {charts_status['total_running']}")
        
        # Aufräumen
        price_scheduler.cleanup_all_files()
        charts_scheduler.cleanup_all_files()
        
        print(f"\n✅ Scheduler-Test erfolgreich!")
        return True
        
    except Exception as e:
        print(f"❌ Scheduler-Test fehlgeschlagen: {e}")
        return False

if __name__ == "__main__":
    # Test-Modus
    test_scheduler_setup(), enable_charts=False)

# Apps holen die Updates benötigen
pending_apps = tracker.get_apps_needing_price_update(hours_threshold=6)

if pending_apps:
    app_ids = [app['steam_app_id'] for app in pending_apps]
    print(f"📊 Aktualisiere {len(app_ids)} Apps...")
    
    result = tracker.track_app_prices(app_ids)
    print(f"✅ {result['successful']}/{result['processed']} Apps erfolgreich aktualisiert")
    
    if result.get('errors'):
        print(f"⚠️ {len(result['errors'])} Fehler aufgetreten")
        for error in result['errors'][:3]:  # Zeige nur erste 3 Fehler
            print(f"   - {error}")
else:
    print("✅ Alle Apps sind aktuell")
'''
    
    @staticmethod
    def charts_update_task():
        """CORRECTED: Task für Charts-Updates"""
        return '''
# Charts-Update Task - CORRECTED VERSION
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
print("📊 Starte Charts-Update...")
result = tracker.update_charts_now()

if result.get('success', True):
    print(f"✅ Charts-Update erfolgreich:")
    print(f"   📊 {result.get('total_games_found', 0)} Spiele gefunden")
    print(f"   ➕ {result.get('new_games_added', 0)} neue Spiele")
    print(f"   🔄 {result.get('existing_games_updated', 0)} aktualisiert")
    
    if result.get('errors'):
        print(f"   ⚠️ {len(result['errors'])} Fehler")
else:
    print(f"❌ Charts-Update fehlgeschlagen: {result.get('error')}")
'''
    
    @staticmethod
    def charts_price_update_task():
        """CORRECTED: Task für Charts-Preis-Updates"""
        return '''
# Charts-Preis-Update Task - CORRECTED VERSION
from price_tracker import create_price_tracker
from steam_wishlist_manager import load_api_key_from_env

api_key = load_api_key_from_env()
if not api_key:
    print("❌ Kein Steam API Key - Charts-Preise übersprungen")
    return

tracker = create_price_tracker(api_key=api_key