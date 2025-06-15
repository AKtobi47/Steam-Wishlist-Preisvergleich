# =====================================================================
# NEUE UTILITY-FUNKTIONEN - Am Anfang der Datei nach den Imports einfügen
# =====================================================================

def safe_get_scheduler_status(price_tracker):
    """FIXED: Sichere Scheduler-Status Abfrage mit Fallback"""
    try:
        if hasattr(price_tracker, 'get_enhanced_scheduler_status'):
            return price_tracker.get_enhanced_scheduler_status()
        elif hasattr(price_tracker, 'get_scheduler_status'):
            return price_tracker.get_scheduler_status()
        else:
            # Fallback falls Methode nicht existiert
            return {
                'standard_scheduler_running': getattr(price_tracker, 'scheduler_running', False),
                'charts_scheduler_running': False,
                'standard_next_run': 'N/A',
                'charts_next_update': 'N/A',
                'standard_jobs_count': 0,
                'charts_jobs_count': 0
            }
    except Exception as e:
        logger.debug(f"Scheduler-Status Fehler: {e}")
        return {
            'standard_scheduler_running': False,
            'charts_scheduler_running': False,
            'standard_next_run': 'Fehler',
            'charts_next_update': 'Fehler'
        }

def show_available_chart_types():
    """FIXED: Zeigt verfügbare Chart-Typen an"""
    try:
        from steam_charts_manager import SteamChartsManager
        chart_types = SteamChartsManager.get_available_chart_types()
        
        print("\n📊 VERFÜGBARE CHART-TYPEN:")
        print("-" * 30)
        for chart_type, description in chart_types.items():
            print(f"• {chart_type} - {description}")
        print()
        
        return list(chart_types.keys())
    except ImportError:
        print("❌ Charts-Funktionalität nicht verfügbar")
        return []
    except Exception as e:
        print(f"❌ Fehler beim Laden der Chart-Typen: {e}")
        return []

def safe_enable_charts_tracking(price_tracker, charts_hours=6, price_hours=4, cleanup_hours=24):
    """FIXED: Sichere Charts-Tracking Aktivierung mit besserer Fehlerbehandlung"""
    try:
        if hasattr(price_tracker, 'enable_charts_tracking'):
            success = price_tracker.enable_charts_tracking(
                charts_update_hours=charts_hours,
                price_update_hours=price_hours,
                cleanup_hours=cleanup_hours
            )
            
            if success:
                print(f"✅ Charts-Tracking erfolgreich aktiviert!")
                print(f"   📊 Charts-Updates: alle {charts_hours}h")
                print(f"   💰 Preis-Updates: alle {price_hours}h")
                print(f"   🧹 Cleanup: alle {cleanup_hours}h")
                return True
            else:
                print("❌ Charts-Tracking konnte nicht aktiviert werden")
                print("💡 Prüfe die Logs für weitere Details")
                return False
        else:
            print("❌ enable_charts_tracking Methode nicht verfügbar")
            print("💡 Charts-Funktionalität ist möglicherweise nicht installiert")
            return False
            
    except Exception as e:
        print(f"❌ Fehler beim Aktivieren des Charts-Trackings: {e}")
        print("💡 Mögliche Lösungen:")
        print("   • Prüfe Steam API Key in .env")
        print("   • Stelle sicher dass Charts-Module verfügbar sind")
        print("   • Starte das Programm neu")
        return False

def safe_disable_charts_tracking(price_tracker):
    """FIXED: Sichere Charts-Tracking Deaktivierung"""
    try:
        if hasattr(price_tracker, 'disable_charts_tracking'):
            success = price_tracker.disable_charts_tracking()
            
            if success:
                print("⏹️ Charts-Tracking erfolgreich deaktiviert")
                return True
            else:
                print("❌ Charts-Tracking konnte nicht deaktiviert werden")
                return False
        else:
            print("❌ disable_charts_tracking Methode nicht verfügbar")
            return False
            
    except Exception as e:
        print(f"❌ Fehler beim Deaktivieren des Charts-Trackings: {e}")
        return False

def show_enhanced_charts_statistics(price_tracker):
    """FIXED: Zeigt erweiterte Charts-Statistiken"""
    if not price_tracker.charts_enabled:
        return
    
    try:
        # Basic Charts-Statistiken
        if hasattr(price_tracker.db_manager, 'get_charts_statistics'):
            charts_stats = price_tracker.db_manager.get_charts_statistics()
            
            if charts_stats and charts_stats.get('total_active_charts_games', 0) > 0:
                print(f"\n📊 CHARTS-STATUS:")
                print(f"🎯 Aktive Charts-Spiele: {charts_stats.get('total_active_charts_games', 0)}")
                print(f"🎮 Einzigartige Apps in Charts: {charts_stats.get('unique_apps_in_charts', 0)}")
                print(f"📈 Charts-Preis-Snapshots: {charts_stats.get('total_charts_price_snapshots', 0):,}")
                
                # Pro Chart-Typ
                active_by_chart = charts_stats.get('active_games_by_chart', {})
                if active_by_chart:
                    print(f"📈 Verteilung: ", end="")
                    chart_info = []
                    for chart_type, count in active_by_chart.items():
                        chart_info.append(f"{chart_type}: {count}")
                    print(" | ".join(chart_info))
            else:
                print(f"\n📊 CHARTS-STATUS:")
                print(f"🎯 Charts verfügbar aber noch keine Daten")
                print(f"💡 Führe 'Charts sofort aktualisieren' aus um zu starten")
        else:
            print("\n📊 Charts-Statistiken nicht verfügbar")
            
    except Exception as e:
        print(f"⚠️ Fehler beim Laden der Charts-Statistiken: {e}")

def show_charts_scheduler_status_detailed(price_tracker):
    """FIXED: Zeigt detaillierten Charts-Scheduler Status"""
    if not price_tracker.charts_enabled:
        return
    
    try:
        scheduler_status = safe_get_scheduler_status(price_tracker)
        
        if scheduler_status.get('charts_scheduler_running'):
            print(f"🚀 Charts-Scheduler: AKTIV ✅")
            next_update = scheduler_status.get('charts_next_update', 'N/A')
            if next_update and next_update != 'N/A':
                print(f"   ⏰ Nächstes Charts-Update: {next_update}")
        else:
            print(f"🚀 Charts-Scheduler: INAKTIV ❌")
            
    except Exception as e:
        print(f"⚠️ Charts-Scheduler Status nicht verfügbar: {e}")

# =====================================================================
# ERWEITERTE STATISTIKEN-ANZEIGE - Ersetze den entsprechenden Bereich im main()
# =====================================================================

# FIXED: Erweiterte Statistiken anzeigen (ersetze den try-Block in main())
try:
    stats = price_tracker.get_statistics()
    
    # Standard Statistiken
    print(f"\n📊 AKTUELLER STATUS:")
    print(f"📚 Getrackte Apps: {stats['tracked_apps']}")
    total_snapshots = stats.get('total_snapshots', 0)
    print(f"📈 Gesamt Preis-Snapshots: {total_snapshots:,}")
    print(f"🏪 Stores: {', '.join(stats['stores_tracked'])}")
    
    # FIXED: Charts-Statistiken (falls verfügbar)
    if charts_enabled:
        show_enhanced_charts_statistics(price_tracker)
        show_charts_scheduler_status_detailed(price_tracker)
    
    # FIXED: Standard Scheduler Status
    scheduler_status = safe_get_scheduler_status(price_tracker)
    if scheduler_status.get('standard_scheduler_running'):
        print(f"🔄 Standard Tracking: AKTIV ✅")
        next_run = scheduler_status.get('standard_next_run', 'N/A')
        if next_run and next_run != 'N/A':
            print(f"   ⏰ Nächster Lauf: {next_run}")
    else:
        print(f"🔄 Standard Tracking: INAKTIV ❌")
    
    newest_snapshot = stats.get('newest_snapshot')
    if newest_snapshot:
        print(f"🕐 Letzte Preisabfrage: {newest_snapshot[:19]}")
    
except Exception as e:
    print(f"⚠️ Fehler beim Laden der Statistiken: {e}")
    print("\n📊 AKTUELLER STATUS:")
    print("📚 Getrackte Apps: ❓")
    print("📈 Gesamt Preis-Snapshots: ❓")

# =====================================================================
# OPTION 15 - CHARTS-TRACKING VERWALTEN (FIXED)
# =====================================================================

elif charts_enabled and choice == "15":
    # FIXED: Charts-Tracking aktivieren/deaktivieren
    print("\n🎯 CHARTS-TRACKING VERWALTEN")
    print("=" * 35)
    
    scheduler_status = safe_get_scheduler_status(price_tracker)
    
    if scheduler_status.get('charts_scheduler_running'):
        print("🔄 Charts-Tracking läuft bereits")
        next_update = scheduler_status.get('charts_next_update', 'N/A')
        if next_update and next_update != 'N/A':
            print(f"   ⏰ Nächstes Charts-Update: {next_update}")
        
        stop = input("Charts-Tracking stoppen? (j/n): ").lower().strip()
        if stop in ['j', 'ja', 'y', 'yes']:
            safe_disable_charts_tracking(price_tracker)
    else:
        print("⏸️ Charts-Tracking ist inaktiv")
        start = input("Charts-Tracking starten? (j/n): ").lower().strip()
        
        if start in ['j', 'ja', 'y', 'yes']:
            charts_hours = input("Charts-Update Intervall in Stunden (Standard: 6): ").strip()
            price_hours = input("Preis-Update Intervall in Stunden (Standard: 4): ").strip()
            cleanup_hours = input("Cleanup Intervall in Stunden (Standard: 24): ").strip()
            
            try:
                charts_hours = int(charts_hours) if charts_hours else 6
                price_hours = int(price_hours) if price_hours else 4
                cleanup_hours = int(cleanup_hours) if cleanup_hours else 24
            except ValueError:
                charts_hours, price_hours, cleanup_hours = 6, 4, 24
            
            safe_enable_charts_tracking(price_tracker, charts_hours, price_hours, cleanup_hours)

# =====================================================================
# OPTION 18 - BESTE CHARTS-DEALS (FIXED)
# =====================================================================

elif charts_enabled and choice == "18":
    # FIXED: Beste Charts-Deals anzeigen
    print("\n🏆 BESTE CHARTS-DEALS")
    print("=" * 25)
    
    # FIXED: Zeige verfügbare Chart-Typen
    available_types = show_available_chart_types()
    
    if available_types:
        print("💡 Verfügbare Filter:")
        for i, chart_type in enumerate(available_types, 1):
            print(f"   {i}. {chart_type}")
        print(f"   {len(available_types) + 1}. alle (kein Filter)")
    
    chart_type_filter = input("Chart-Typ eingeben oder Enter für alle: ").strip()
    
    # Validierung
    if chart_type_filter and chart_type_filter not in available_types:
        print(f"⚠️ Unbekannter Chart-Typ '{chart_type_filter}' - verwende alle Charts")
        chart_type_filter = None
    elif not chart_type_filter:
        chart_type_filter = None
    
    if hasattr(price_tracker, 'get_best_charts_deals'):
        deals = price_tracker.get_best_charts_deals(limit=15, chart_type=chart_type_filter)
        
        if deals:
            if chart_type_filter:
                print(f"🏆 Top {len(deals)} Deals für {chart_type_filter.upper()}:")
            else:
                print(f"🏆 Top {len(deals)} Charts-Deals (alle Typen):")
            print()
            
            for i, deal in enumerate(deals, 1):
                rank_info = f"#{deal.get('current_rank', '?')}" if deal.get('current_rank') else ""
                chart_info = f"[{deal.get('chart_type', 'Unknown')}]" if not chart_type_filter else ""
                
                print(f"{i:2d}. {deal['game_title'][:35]:<35} {rank_info} {chart_info}")
                print(f"    💰 €{deal['best_price']:.2f} (-{deal['discount_percent']}%) bei {deal['best_store']}")
                print(f"    🆔 App ID: {deal['steam_app_id']}")
                print()
        else:
            print("❌ Keine Charts-Deals gefunden")
            print("💡 Führe zuerst Charts-Updates und Preisabfragen durch")
    else:
        print("❌ Charts-Deals Funktion nicht verfügbar")

# =====================================================================
# OPTION 20 - CHARTS-SPIELE ANZEIGEN (FIXED)
# =====================================================================

elif charts_enabled and choice == "20":
    # FIXED: Charts-Spiele anzeigen
    print("\n📋 CHARTS-SPIELE ANZEIGEN")
    print("=" * 30)
    
    # FIXED: Zeige verfügbare Chart-Typen
    available_types = show_available_chart_types()
    
    if available_types:
        print("💡 Verfügbare Filter:")
        for i, chart_type in enumerate(available_types, 1):
            print(f"   {i}. {chart_type}")
        print(f"   {len(available_types) + 1}. alle (kein Filter)")
    
    chart_type_filter = input("Chart-Typ eingeben oder Enter für alle: ").strip()
    
    # Validierung
    if chart_type_filter and chart_type_filter not in available_types:
        print(f"⚠️ Unbekannter Chart-Typ '{chart_type_filter}' - verwende alle Charts")
        chart_type_filter = None
    elif not chart_type_filter:
        chart_type_filter = None
    
    if hasattr(price_tracker.db_manager, 'get_active_chart_games'):
        active_games = price_tracker.db_manager.get_active_chart_games(chart_type_filter)
        
        if active_games:
            if chart_type_filter:
                print(f"📊 {chart_type_filter.upper()} SPIELE ({len(active_games)}):")
            else:
                print(f"📊 ALLE CHARTS-SPIELE ({len(active_games)}):")
            print()
            
            current_chart = None
            for i, game in enumerate(active_games[:50], 1):  # Limitiere auf 50
                # Chart-Typ Header
                if game.get('chart_type') != current_chart and not chart_type_filter:
                    current_chart = game.get('chart_type')
                    print(f"\n📈 {current_chart.upper()}")
                    print("-" * 30)
                
                rank = game.get('current_rank', 0)
                rank_display = f"#{rank:3d}" if rank > 0 else "   -"
                
                first_seen = game.get('first_seen', '')[:10]
                last_seen = game.get('last_seen', '')[:10]
                
                print(f"{rank_display} {game['name'][:40]:<40}")
                print(f"     🆔 {game['steam_app_id']} | 📅 {first_seen} - {last_seen}")
            
            if len(active_games) > 50:
                print(f"\n... und {len(active_games) - 50} weitere Spiele")
                print("💡 Verwende Chart-Typ Filter um spezifische Listen zu sehen")
        else:
            print("❌ Keine Charts-Spiele gefunden")
            if chart_type_filter:
                print(f"💡 Für Chart-Typ '{chart_type_filter}' keine Spiele vorhanden")
            print("💡 Führe zuerst ein Charts-Update durch")
    else:
        print("❌ Charts-Spiele Funktion nicht verfügbar")

# =====================================================================
# OPTION 22 - VOLLAUTOMATIK EINRICHTEN (FIXED)
# =====================================================================

elif charts_enabled and choice == "22":
    # FIXED: Vollautomatik einrichten
    print("\n🚀 VOLLAUTOMATIK EINRICHTEN")
    print("=" * 35)
    
    print("Diese Funktion richtet vollautomatisches Tracking ein für:")
    print("• Standard Apps (Wishlist, manuell hinzugefügte)")
    print("• Steam Charts (automatisch erkannte beliebte Spiele)")
    print("• Automatische Preisabfragen für beide Kategorien")
    print("• Automatisches Cleanup alter Charts-Spiele")
    print()
    
    confirm = input("Vollautomatik einrichten? (j/n): ").lower().strip()
    if confirm in ['j', 'ja', 'y', 'yes']:
        normal_hours = input("Intervall normale Apps (Stunden, Standard: 6): ").strip()
        charts_hours = input("Intervall Charts-Updates (Stunden, Standard: 6): ").strip()
        charts_price_hours = input("Intervall Charts-Preise (Stunden, Standard: 4): ").strip()
        
        try:
            normal_hours = int(normal_hours) if normal_hours else 6
            charts_hours = int(charts_hours) if charts_hours else 6
            charts_price_hours = int(charts_price_hours) if charts_price_hours else 4
        except ValueError:
            normal_hours, charts_hours, charts_price_hours = 6, 6, 4
        
        # Setup Vollautomatik
        try:
            # Normales Tracking starten
            if safe_start_scheduler(price_tracker, normal_hours):
                print(f"✅ Standard-Tracking gestartet (alle {normal_hours}h)")
            
            # Charts-Tracking starten (falls verfügbar)
            if safe_enable_charts_tracking(price_tracker, charts_hours, charts_price_hours, 24):
                print(f"✅ Charts-Tracking gestartet")
                print(f"   📊 Charts-Updates: alle {charts_hours}h")
                print(f"   💰 Charts-Preise: alle {charts_price_hours}h")
                print(f"   🧹 Charts-Cleanup: alle 24h")
            
            print("\n✅ Vollautomatik erfolgreich eingerichtet!")
            print("\n💡 Alle Scheduler laufen nun automatisch im Hintergrund!")
                
        except Exception as e:
            print(f"❌ Fehler beim Einrichten der Vollautomatik: {e}")

# =====================================================================
# BEENDEN-OPTION (FIXED)
# =====================================================================

elif (not charts_enabled and choice == "15") or (charts_enabled and choice == "23"):
    # Beenden
    print("\n👋 BEENDEN")
    print("=" * 10)
    
    # Standard-Scheduler stoppen falls aktiv
    scheduler_status = safe_get_scheduler_status(price_tracker)
    if scheduler_status.get('standard_scheduler_running'):
        print("⏹️ Stoppe Standard-Tracking...")
        safe_stop_scheduler(price_tracker)
    
    # Charts-Scheduler stoppen falls aktiv
    if charts_enabled and scheduler_status.get('charts_scheduler_running'):
        print("⏹️ Stoppe Charts-Tracking...")
        safe_disable_charts_tracking(price_tracker)
    
    print("💾 Datenbankverbindungen werden automatisch geschlossen...")
    print("✅ Enhanced Steam Price Tracker beendet. Auf Wiedersehen!")
    break