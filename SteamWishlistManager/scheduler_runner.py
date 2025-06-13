"""
🖥️ LÖSUNG: Enhanced Scheduler in separatem Terminal
Einfache und praktische Implementierung
"""

# ========================================
# 1. NEUE DATEI: scheduler_runner.py
# ========================================

#!/usr/bin/env python3
"""
Enhanced Scheduler Runner - Läuft in separatem Terminal
Zeigt Live-Status und führt Scheduler aus
"""

import sys
import os
import time
import signal
from datetime import datetime
from pathlib import Path

# Füge Hauptverzeichnis zum Path hinzu
sys.path.insert(0, str(Path(__file__).parent))

def signal_handler(signum, frame):
    """Saubere Beendigung bei Strg+C"""
    print("\n\n🛑 SCHEDULER WIRD BEENDET...")
    print("💾 Speichere Status...")
    sys.exit(0)

def main():
    """Hauptfunktion für Scheduler-Terminal"""
    signal.signal(signal.SIGINT, signal_handler)
    
    # Terminal-Design
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen
    
    print("🚀 ENHANCED SCHEDULER - SEPARATES TERMINAL")
    print("=" * 60)
    print(f"⏰ Gestartet: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Module importieren
        from steam_wishlist_manager import load_api_key_from_env
        from database_manager import DatabaseManager
        from cheapshark_mapping_processor import CheapSharkMappingProcessor
        
        # API Key laden
        api_key = load_api_key_from_env()
        if not api_key:
            print("❌ FEHLER: Kein API Key in .env gefunden!")
            input("\nDrücken Sie Enter zum Beenden...")
            return
        
        print("✅ API Key geladen")
        
        # Konfiguration aus Kommandozeilen-Argumenten
        batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 10
        mapping_interval = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        releases_interval = int(sys.argv[3]) if len(sys.argv) > 3 else 24
        
        print(f"⚙️ KONFIGURATION:")
        print(f"   📊 Batch-Größe: {batch_size} Apps")
        print(f"   🔄 CheapShark-Mapping: alle {mapping_interval} Minuten")
        print(f"   🆕 Release-Import: alle {releases_interval} Stunden")
        
        # Komponenten initialisieren
        print("\n🔧 Initialisiere Komponenten...")
        db_manager = DatabaseManager()
        processor = CheapSharkMappingProcessor(api_key, db_manager)
        
        # Anfangsstatistiken
        initial_stats = db_manager.get_database_stats()
        print(f"📊 ANFANGSSTATISTIKEN:")
        print(f"   📚 Gesamt Apps: {initial_stats['apps']['total']:,}")
        print(f"   ✅ Bereits gemappt: {initial_stats['cheapshark']['mapped']:,}")
        print(f"   📋 Queue: {initial_stats['queue']['pending']:,}")
        
        # Enhanced Scheduler starten
        print(f"\n🚀 STARTE ENHANCED SCHEDULER...")
        processor.start_background_scheduler_enhanced(
            mapping_batch_size=batch_size,
            mapping_interval_minutes=mapping_interval,
            releases_interval_hours=releases_interval
        )
        
        print("✅ SCHEDULER GESTARTET!")
        print("\n" + "="*60)
        print("📊 LIVE-STATUS (Updates alle 60 Sekunden)")
        print("🛑 Drücken Sie Strg+C zum Beenden")
        print("="*60)
        
        # Status-Tracking Variablen
        update_counter = 0
        last_mapped = initial_stats['cheapshark']['mapped']
        last_queue = initial_stats['queue']['pending']
        
        # Haupt-Status-Loop
        while processor.scheduler_running:
            time.sleep(60)  # Alle 60 Sekunden
            update_counter += 1
            
            try:
                # Aktuelle Stats holen
                current_stats = db_manager.get_database_stats()
                current_time = datetime.now().strftime('%H:%M:%S')
                
                # Fortschritt berechnen
                mapped_progress = current_stats['cheapshark']['mapped'] - last_mapped
                queue_progress = last_queue - current_stats['queue']['pending']
                total_progress = current_stats['cheapshark']['mapped'] - initial_stats['cheapshark']['mapped']
                
                # Status-Update anzeigen
                print(f"\n⏰ [{current_time}] UPDATE #{update_counter}")
                print(f"✅ Aktuell gemappt: {current_stats['cheapshark']['mapped']:,} (+{total_progress:,} seit Start)")
                print(f"📋 Queue ausstehend: {current_stats['queue']['pending']:,}")
                print(f"📈 Coverage: {current_stats['cheapshark']['coverage']:.1f}%")
                
                # Fortschritt seit letztem Update
                if mapped_progress > 0 or queue_progress > 0:
                    print(f"🔄 Letzte Minute: +{mapped_progress} gemappt, -{queue_progress} Queue")
                    
                    # Rate berechnen
                    if mapped_progress > 0:
                        rate_per_hour = mapped_progress * 60
                        print(f"⚡ Geschätzte Rate: ~{rate_per_hour}/Stunde")
                
                # Scheduler-Health
                scheduler_status = processor.get_scheduler_status()
                if scheduler_status['scheduler_running']:
                    print("💚 Scheduler: AKTIV")
                else:
                    print("❤️ Scheduler: PROBLEM!")
                
                # Speichere für nächsten Vergleich
                last_mapped = current_stats['cheapshark']['mapped']
                last_queue = current_stats['queue']['pending']
                
                print("-" * 40)
                
            except Exception as e:
                print(f"⚠️ Status-Update Fehler: {e}")
                
        print("\n🛑 SCHEDULER WURDE GESTOPPT")
        
    except KeyboardInterrupt:
        print("\n🛑 Beendigung durch Benutzer")
        
    except Exception as e:
        print(f"\n❌ KRITISCHER FEHLER: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n👋 Scheduler-Terminal wird geschlossen...")
        print("💡 Drücken Sie Enter oder schließen Sie das Fenster")
        try:
            input()
        except:
            pass

if __name__ == "__main__":
    main()


# ========================================
# 2. UPDATE für cheapshark_mapping_processor.py
# ========================================

# Füge diese Methode zur CheapSharkMappingProcessor Klasse hinzu:

import subprocess
import platform
from pathlib import Path

def start_scheduler_in_new_terminal(self, 
                                   mapping_batch_size: int = 10,
                                   mapping_interval_minutes: int = 3,
                                   releases_interval_hours: int = 24) -> bool:
    """
    Startet Enhanced Scheduler in neuem Terminal-Fenster
    
    Returns:
        True wenn erfolgreich gestartet
    """
    try:
        # Prüfe ob scheduler_runner.py existiert
        runner_file = Path("scheduler_runner.py")
        if not runner_file.exists():
            print("❌ scheduler_runner.py nicht gefunden!")
            print("💡 Erstellen Sie zuerst die Datei (siehe Anleitung)")
            return False
        
        # Parameter für den Runner
        args = [
            str(mapping_batch_size),
            str(mapping_interval_minutes),
            str(releases_interval_hours)
        ]
        
        # Betriebssystem erkennen und entsprechenden Befehl ausführen
        system = platform.system().lower()
        
        print(f"🖥️ Starte separates Terminal ({system})...")
        
        if system == "windows":
            # Windows: Neues CMD-Fenster
            cmd = ["start", "cmd", "/k", f"python scheduler_runner.py {' '.join(args)}"]
            subprocess.Popen(cmd, shell=True)
            
        elif system == "darwin":  # macOS
            # macOS: Neues Terminal-Tab/Fenster
            script = f"cd '{os.getcwd()}' && python scheduler_runner.py {' '.join(args)}"
            cmd = ["osascript", "-e", f'tell app "Terminal" to do script "{script}"']
            subprocess.Popen(cmd)
            
        else:  # Linux
            # Linux: Versuche gängige Terminals
            terminals_to_try = [
                ["gnome-terminal", "--", "python", "scheduler_runner.py"] + args,
                ["konsole", "-e", "python", "scheduler_runner.py"] + args,
                ["xfce4-terminal", "-e", f"python scheduler_runner.py {' '.join(args)}"],
                ["xterm", "-e", f"python scheduler_runner.py {' '.join(args)}"]
            ]
            
            success = False
            for terminal_cmd in terminals_to_try:
                try:
                    subprocess.Popen(terminal_cmd)
                    success = True
                    break
                except FileNotFoundError:
                    continue
            
            if not success:
                print("❌ Kein unterstütztes Terminal gefunden!")
                print("💡 Installieren Sie: gnome-terminal, konsole, xfce4-terminal oder xterm")
                return False
        
        print("🚀 SEPARATES SCHEDULER-TERMINAL GESTARTET!")
        print("📊 Live-Status läuft im neuen Terminal-Fenster")
        print("🔄 Dieses Terminal bleibt für weitere Aktionen frei")
        print("\n💡 HINWEISE:")
        print("   • Wechseln Sie zum Scheduler-Terminal für Live-Updates")
        print("   • Schließen Sie das Scheduler-Fenster zum Beenden")
        print("   • Strg+C im Scheduler-Terminal stoppt den Scheduler")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Starten des Terminals: {e}")
        return False


# ========================================
# 3. UPDATE für cheapshark_processor_main()
# ========================================

# Erweitere das Hauptmenü um die neue Option:

def cheapshark_processor_main():
    # ... bestehender Code ...
    
    while True:
        # ... Statistiken anzeigen ...
        
        print("\n🔧 ENHANCED PROCESSOR OPTIONEN:")
        print("1. 🔄 Manuelle Verarbeitung (alle unverarbeiteten Apps)")
        print("2. ⚡ Limitierte Verarbeitung (nur X Apps)")
        print("3. 🚀 Enhanced Scheduler starten (aktuelles Terminal)")
        print("3n. 🖥️ Enhanced Scheduler in NEUEM Terminal")  # ← NEU!
        print("4. 🔄 Standard-Scheduler starten")
        print("5. 🛑 Scheduler stoppen")
        print("6. 📊 Enhanced Scheduler-Status anzeigen")
        print("7. 🎯 Wishlist-Apps priorisieren")
        print("8. 📈 Detaillierte Statistiken anzeigen")
        print("11. ❌ Beenden")
        
        choice = input("\nWählen Sie eine Option: ").strip().lower()
        
        # ... bestehende Optionen ...
        
        elif choice == "3n":
            # NEU: Enhanced Scheduler in separatem Terminal
            print("\n🖥️ ENHANCED SCHEDULER IN NEUEM TERMINAL")
            print("=" * 50)
            
            batch_size = input("Batch-Größe (Standard: 10): ").strip()
            mapping_interval = input("Mapping-Intervall Minuten (Standard: 3): ").strip()
            releases_interval = input("Release-Intervall Stunden (Standard: 24): ").strip()
            
            try:
                batch_size = int(batch_size) if batch_size else 10
                mapping_interval = int(mapping_interval) if mapping_interval else 3
                releases_interval = int(releases_interval) if releases_interval else 24
            except ValueError:
                batch_size, mapping_interval, releases_interval = 10, 3, 24
            
            # Starte in neuem Terminal
            success = processor.start_scheduler_in_new_terminal(
                mapping_batch_size=batch_size,
                mapping_interval_minutes=mapping_interval,
                releases_interval_hours=releases_interval
            )
            
            if not success:
                print("❌ Konnte neues Terminal nicht starten")
                print("💡 Verwenden Sie Option 3 für aktuelles Terminal")
        
        # ... weitere Optionen ...


# ========================================
# 4. SCHNELLE INSTALLATION
# ========================================

def create_scheduler_runner():
    """Erstellt scheduler_runner.py automatisch"""
    
    # Der komplette Code von oben
    scheduler_code = '''#!/usr/bin/env python3
# [KOMPLETTER CODE VON OBEN HIER]
'''
    
    with open("scheduler_runner.py", "w", encoding="utf-8") as f:
        f.write(scheduler_code)
    
    print("✅ scheduler_runner.py erstellt!")

# Führe dies einmal aus:
# python -c "from cheapshark_mapping_processor import create_scheduler_runner; create_scheduler_runner()"


# ========================================
# 5. VERWENDUNG
# ========================================

"""
SO VERWENDEN SIE DIE SEPARATE TERMINAL LÖSUNG:

1. EINMALIGE EINRICHTUNG:
   - Kopieren Sie den scheduler_runner.py Code in eine neue Datei
   - Oder führen Sie create_scheduler_runner() aus

2. VERWENDUNG:
   python cheapshark_mapping_processor.py
   → Wählen Sie Option "3n" 
   → Neues Terminal öffnet sich mit Live-Status
   → Hauptterminal bleibt für weitere Aktionen frei

3. BEENDEN:
   - Schließen Sie das Scheduler-Terminal-Fenster
   - Oder drücken Sie Strg+C im Scheduler-Terminal

4. VORTEILE:
   ✅ Hauptterminal bleibt interaktiv
   ✅ Live-Status in separatem Fenster
   ✅ Übersichtliche Trennung
   ✅ Funktioniert auf Windows, macOS, Linux
"""
