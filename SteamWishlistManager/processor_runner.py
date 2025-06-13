#!/usr/bin/env python3
"""
🖥️ UNIVERSAL PROCESSOR RUNNER - Vereint alle Terminal-Modi
Manuelle Verarbeitung + Enhanced Scheduler in separatem Terminal
Ersetzt sowohl processor_runner.py als auch scheduler_runner.py
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
    print("\n\n🛑 RUNNER WIRD BEENDET...")
    print("💾 Speichere Status...")
    sys.exit(0)

def main():
    """Universal Hauptfunktion für alle Terminal-Modi"""
    signal.signal(signal.SIGINT, signal_handler)
    
    # Terminal-Design
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen
    
    print("🖥️ UNIVERSAL PROCESSOR RUNNER - SEPARATES TERMINAL")
    print("=" * 60)
    print(f"⏰ Gestartet: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Parameter aus Kommandozeile
    if len(sys.argv) < 2:
        print("❌ FEHLER: Keine Parameter übergeben!")
        print("💡 Verwendung:")
        print("   Manuelle Verarbeitung:")
        print("     python processor_runner.py all [batch_size]")
        print("     python processor_runner.py limited [max_apps] [batch_size]")
        print("   Enhanced Scheduler:")
        print("     python processor_runner.py scheduler [mapping_batch] [mapping_interval] [releases_interval]")
        input("\nDrücken Sie Enter zum Beenden...")
        return
    
    mode = sys.argv[1].lower()
    
    # ======================
    # MANUELLE VERARBEITUNG
    # ======================
    if mode in ['all', 'limited']:
        handle_manual_processing(mode)
    
    # ======================
    # ENHANCED SCHEDULER
    # ======================
    elif mode == 'scheduler':
        handle_enhanced_scheduler()
    
    else:
        print(f"❌ Unbekannter Modus: {mode}")
        print("💡 Verfügbare Modi: all, limited, scheduler")
        input("\nDrücken Sie Enter zum Beenden...")

def handle_manual_processing(mode):
    """Behandelt manuelle Verarbeitung (all/limited)"""
    
    # Parameter parsen
    max_apps = None
    batch_size = 50
    
    if mode == "all":
        batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    elif mode == "limited":
        max_apps = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
        batch_size = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    
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
        
        # Konfiguration anzeigen
        print(f"⚙️ MANUELLE VERARBEITUNG:")
        print(f"   📊 Modus: {'Alle Apps' if mode == 'all' else f'Limitiert ({max_apps} Apps)'}")
        print(f"   📦 Batch-Größe: {batch_size}")
        
        # Komponenten initialisieren
        print("\n🔧 Initialisiere Komponenten...")
        db_manager = DatabaseManager()
        processor = CheapSharkMappingProcessor(api_key, db_manager)
        
        # Anfangsstatistiken
        initial_stats = db_manager.get_database_stats()
        print(f"📊 ANFANGSSTATISTIKEN:")
        print(f"   📚 Gesamt Apps: {initial_stats['apps']['total']:,}")
        print(f"   ✅ Bereits gemappt: {initial_stats['cheapshark']['mapped']:,}")
        print(f"   📝 Kein Mapping: {initial_stats['cheapshark']['no_mapping_found']:,}")
        print(f"   📅 Zu neu: {initial_stats['cheapshark']['too_new']:,}")
        print(f"   ❔ Noch nicht versucht: {initial_stats['cheapshark']['unmapped']:,}")
        print(f"   📋 Queue: {initial_stats['queue']['pending']:,}")
        
        # Verarbeitung starten
        print(f"\n🚀 STARTE CHEAPSHARK-VERARBEITUNG...")
        print("="*60)
        print("📊 LIVE-STATUS (Updates während Verarbeitung)")
        print("🛑 Drücken Sie Strg+C zum vorzeitigen Beenden")
        print("="*60)
        
        start_time = time.time()
        
        # Manuelle Verarbeitung ausführen
        if mode == "all":
            print("🔄 Starte Verarbeitung ALLER unverarbeiteten Apps...")
            result = processor.process_mapping_manual(batch_size=batch_size)
        else:  # limited
            print(f"⚡ Starte limitierte Verarbeitung für {max_apps} Apps...")
            result = processor.process_mapping_manual(max_apps=max_apps, batch_size=batch_size)
        
        # Endergebnisse
        elapsed_time = time.time() - start_time
        
        print(f"\n🏁 VERARBEITUNG ABGESCHLOSSEN!")
        print("=" * 50)
        print(f"⏱️ Gesamtdauer: {elapsed_time/60:.1f} Minuten")
        print(f"📊 Verarbeitet: {result['processed']:,} Apps")
        print(f"✅ Erfolgreich gemappt: {result['successful']:,}")
        print(f"📝 Kein Mapping verfügbar: {result['not_found']:,}")
        print(f"📅 Zu neu für Mapping: {result['too_new']:,}")
        print(f"❌ Fehlgeschlagen: {result['failed']:,}")
        print(f"📈 Erfolgsrate: {result.get('completion_rate', 0):.1f}%")
        
        if result['processed'] > 0:
            rate = result['processed'] / (elapsed_time / 60)
            print(f"⚡ Durchschnittsrate: {rate:.1f} Apps/Minute")
        
        # Finale Statistiken
        final_stats = db_manager.get_database_stats()
        improvement = final_stats['cheapshark']['mapped'] - initial_stats['cheapshark']['mapped']
        
        print(f"\n📈 FORTSCHRITT:")
        print(f"🎯 Neue Mappings erstellt: +{improvement:,}")
        print(f"📊 Gesamt Coverage: {final_stats['cheapshark']['coverage']:.1f}%")
        
        print(f"\n✨ VERARBEITUNG ERFOLGREICH ABGESCHLOSSEN!")
        
    except KeyboardInterrupt:
        print("\n🛑 Verarbeitung durch Benutzer beendet")
        
    except Exception as e:
        print(f"\n❌ KRITISCHER FEHLER: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n👋 Processor-Terminal wird geschlossen...")
        print("💡 Drücken Sie Enter oder schließen Sie das Fenster")
        try:
            input()
        except:
            pass

def handle_enhanced_scheduler():
    """Behandelt Enhanced Scheduler"""
    
    # Parameter parsen
    mapping_batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    mapping_interval_minutes = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    releases_interval_hours = int(sys.argv[4]) if len(sys.argv) > 4 else 24
    
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
        
        # Konfiguration anzeigen
        print(f"⚙️ ENHANCED SCHEDULER KONFIGURATION:")
        print(f"   📊 CheapShark Batch-Größe: {mapping_batch_size} Apps")
        print(f"   🔄 CheapShark-Mapping: alle {mapping_interval_minutes} Minuten")
        print(f"   🆕 Release-Import: alle {releases_interval_hours} Stunden")
        
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
        print(f"   🆕 Kürzlich veröffentlicht: {initial_stats['apps']['recently_released']:,}")
        
        # Enhanced Scheduler starten
        print(f"\n🚀 STARTE ENHANCED SCHEDULER...")
        processor.start_background_scheduler_enhanced(
            mapping_batch_size=mapping_batch_size,
            mapping_interval_minutes=mapping_interval_minutes,
            releases_interval_hours=releases_interval_hours
        )
        
        print("✅ ENHANCED SCHEDULER GESTARTET!")
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
                print(f"🆕 Kürzlich veröffentlicht: {current_stats['apps']['recently_released']:,}")
                print(f"📅 Zu neu für Mapping: {current_stats['cheapshark']['too_new']:,}")
                
                # Fortschritt seit letztem Update
                if mapped_progress > 0 or queue_progress > 0:
                    print(f"🔄 Letzte Minute: +{mapped_progress} gemappt, -{queue_progress} Queue")
                    
                    # Rate berechnen
                    if mapped_progress > 0:
                        rate_per_hour = mapped_progress * 60
                        print(f"⚡ Geschätzte Rate: ~{rate_per_hour}/Stunde")
                
                # Enhanced Scheduler-Health
                try:
                    enhanced_status = processor.get_enhanced_scheduler_status()
                    print("💚 Enhanced Scheduler: AKTIV")
                    print(f"   📋 {len(enhanced_status['scheduled_jobs'])} aktive Jobs")
                    
                    last_release_import = enhanced_status.get('last_release_import')
                    if last_release_import:
                        print(f"   🆕 Letzter Release-Import: {last_release_import}")
                    
                except Exception:
                    # Fallback auf Standard-Status
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
                
        print("\n🛑 ENHANCED SCHEDULER WURDE GESTOPPT")
        
    except KeyboardInterrupt:
        print("\n🛑 Enhanced Scheduler durch Benutzer beendet")
        
        # Scheduler sauber stoppen
        try:
            if 'processor' in locals() and processor.scheduler_running:
                print("🔄 Stoppe Scheduler...")
                processor.stop_background_scheduler()
                print("✅ Scheduler gestoppt")
        except:
            pass
        
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