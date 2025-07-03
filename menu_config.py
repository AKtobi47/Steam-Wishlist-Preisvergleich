"""
Dynamisches Menu-System für Steam Price Tracker
Finale Version - WIRKLICH dynamisch ohne statische Mappings
"""

from dataclasses import dataclass
from typing import Dict, List, Callable, Optional
import logging
import os

logger = logging.getLogger(__name__)

def load_menu_config_from_env():
        """
        Lädt Menü-Konfiguration aus .env
    
        Returns:
            Dict mit Menü-Einstellungen
        """
        return {
            'show_descriptions': os.getenv('SHOW_MENU_DESCRIPTIONS', 'true').lower() in ['true', '1', 'yes', 'on'],
            'menu_style': os.getenv('MENU_STYLE', 'standard').lower(),
            'show_category_descriptions': os.getenv('SHOW_CATEGORY_DESCRIPTIONS', 'true').lower() in ['true', '1', 'yes', 'on'],
            'show_option_descriptions': os.getenv('SHOW_OPTION_DESCRIPTIONS', 'true').lower() in ['true', '1', 'yes', 'on'],
            'description_symbol': os.getenv('MENU_DESCRIPTION_SYMBOL', '⨠'),
            'description_indent': int(os.getenv('MENU_DESCRIPTION_INDENT', '6')),
            'show_debug': os.getenv('SHOW_MENU_DEBUG', 'false').lower() in ['true', '1', 'yes', 'on']
        }

@dataclass
class MenuOption:
    """Einzelne Menüoption"""
    name: str
    description: str
    handler: str  # Funktionsname
    requirements: Optional[List[str]] = None  # z.B. ["charts_enabled", "es_available"]
    icon: str = "🔧"
    
class MenuCategory:
    """Menükategorie mit Optionen"""
    def __init__(self, name: str, icon: str, description: str = ""):
        self.name = name
        self.icon = icon
        self.description = description
        self.options: List[MenuOption] = []
    
    def add_option(self, option: MenuOption) -> None:
        """Fügt Option zur Kategorie hinzu"""
        self.options.append(option)
    
    def get_available_options(self, feature_flags: Dict[str, bool]) -> List[MenuOption]:
        """Gibt verfügbare Optionen basierend auf Feature-Flags zurück"""
        available = []
        for option in self.options:
            if not option.requirements:
                # Keine Requirements = immer verfügbar
                available.append(option)
            else:
                # Prüfe ob alle Requirements erfüllt sind
                if all(feature_flags.get(req, False) for req in option.requirements):
                    available.append(option)
        return available

class DynamicMenuSystem:
    """WIRKLICH dynamisches Menüsystem mit automatischer Nummerierung"""
    
    def __init__(self):
        self.categories: List[MenuCategory] = []
        self.option_mapping: Dict[str, tuple] = {}  # "1" -> (category_idx, option_name, handler)
        self.feature_flags: Dict[str, bool] = {}
        self._initialize_menu_structure()
    
    def _initialize_menu_structure(self):
        """
        Initialisiert die komplette Menüstruktur mit allen Optionen
        VOLLSTÄNDIGE VERSION mit menu_batch_charts_update Integration
        """
    
        # 🏠 BASIS-FUNKTIONEN (automatisch nummeriert)
        basic_category = MenuCategory("BASIS-FUNKTIONEN", "🏠", "Grundlegende Tracking-Funktionen")
        basic_category.add_option(MenuOption("App manuell hinzufügen", "App zum Tracking hinzufügen", "menu_add_app_manually", icon="📱"))
        basic_category.add_option(MenuOption("Steam Wishlist importieren", "Wishlist von Steam importieren", "menu_import_wishlist", icon="📥"))
        basic_category.add_option(MenuOption("Aktuelle Preise anzeigen", "Preise der getrackte Apps", "menu_show_current_prices", icon="🔍"))
        basic_category.add_option(MenuOption("Beste Deals anzeigen", "Top-Deals mit Rabatten", "menu_show_best_deals", icon="📊"))
        basic_category.add_option(MenuOption("Preisverlauf anzeigen", "Historische Preisdaten", "menu_show_price_history", icon="📈"))
        basic_category.add_option(MenuOption("Preise manuell aktualisieren", "Sofortiges Preis-Update", "menu_update_prices", icon="🔄"))
    
        # 🚀 AUTOMATION & BATCH (automatisch nummeriert)
        automation_category = MenuCategory("AUTOMATION & BATCH", "🚀", "Automatisierungs-Features")
        automation_category.add_option(MenuOption("Automatisches Tracking", "Scheduler starten/stoppen", "menu_toggle_scheduler", icon="🚀"))
        automation_category.add_option(MenuOption("Namen für alle Apps aktualisieren", "BATCH Namen-Update (Wishlist+Manual+Charts)", "menu_update_names_all_apps", icon="📝"))
    
        # 🎮 APP-VERWALTUNG (automatisch nummeriert)
        management_category = MenuCategory("APP-VERWALTUNG", "🎮", "Verwaltung der getrackte Apps")
        management_category.add_option(MenuOption("Getrackte Apps verwalten", "Apps bearbeiten", "menu_manage_apps", icon="📋"))
        management_category.add_option(MenuOption("Apps entfernen", "Apps aus Tracking entfernen", "menu_remove_apps", icon="🗑️"))
        management_category.add_option(MenuOption("CSV-Export erstellen", "Daten exportieren", "menu_csv_export", icon="📄"))
        management_category.add_option(MenuOption("Detaillierte Statistiken", "System-Analytics", "menu_detailed_statistics", icon="📊"))
    
        # 📊 CHARTS & ANALYTICS (nur wenn charts_enabled=True) - VOLLSTÄNDIG MIT BATCH
        charts_category = MenuCategory("CHARTS & ANALYTICS", "📊", "Steam Charts Integration")
        charts_category.add_option(MenuOption("Charts anzeigen", "Steam Charts-Daten", "menu_show_charts", ["charts_enabled"], "📈"))
        charts_category.add_option(MenuOption("Charts vollständig aktualisieren", "Charts + Namen + Preise (BATCH)", "menu_update_charts_complete", ["charts_enabled"], "🔄"))
        charts_category.add_option(MenuOption("Charts-Deals anzeigen", "Deals aus Charts-Daten", "menu_charts_deals", ["charts_enabled"], "🎯"))
        charts_category.add_option(MenuOption("Charts-Statistiken", "Charts-Analysen", "menu_charts_statistics", ["charts_enabled"], "📊"))
        charts_category.add_option(MenuOption("Charts-Automation", "Automatische Charts", "menu_charts_automation", ["charts_enabled"], "🤖"))
        # 🚀 NEUE ERWEITERTE BATCH-OPTION
        charts_category.add_option(MenuOption("Erweiterte BATCH-Optionen", "Power-User BATCH-Charts-Updates", "menu_batch_charts_update", ["charts_enabled"], "📦"))
    
        # 🔍 ELASTICSEARCH (nur wenn es_available=True)
        es_category = MenuCategory("ELASTICSEARCH", "🔍", "Erweiterte Analytics mit Elasticsearch")
        es_category.add_option(MenuOption("ES Daten exportieren", "Export zu Elasticsearch", "menu_elasticsearch_export", ["es_available"], "📤"))
        es_category.add_option(MenuOption("Kibana Dashboard", "Dashboard öffnen", "menu_elasticsearch_dashboard", ["es_available"], "📊"))
        es_category.add_option(MenuOption("ES Analytics", "Erweiterte Analysen", "menu_elasticsearch_analytics", ["es_available"], "🔬"))
        es_category.add_option(MenuOption("ES Konfiguration", "ES-Einstellungen", "menu_elasticsearch_config", ["es_available"], "⚙️"))
        es_category.add_option(MenuOption("ES Synchronisierung", "Daten sync", "menu_elasticsearch_sync", ["es_available"], "🔄"))
    
        # 🛠️ SYSTEM-TOOLS (automatisch nummeriert)
        system_category = MenuCategory("SYSTEM-TOOLS", "🛠️", "System-Wartung und Konfiguration")
        system_category.add_option(MenuOption("System-Einstellungen", "Konfiguration bearbeiten", "menu_system_settings", icon="⚙️"))
        system_category.add_option(MenuOption("System-Informationen", "System-Status", "menu_system_info", icon="📊"))
        system_category.add_option(MenuOption("Backup erstellen", "Datenbank-Backup", "menu_backup_export", icon="💾"))
        system_category.add_option(MenuOption("Backup importieren", "Datenbank wiederherstellen", "menu_backup_import", icon="📥"))
        system_category.add_option(MenuOption("Health Check", "System-Diagnose", "menu_health_check", icon="🔍"))
        system_category.add_option(MenuOption("Datenbank bereinigen", "DB-Wartung", "menu_clean_database", icon="🧹"))
        system_category.add_option(MenuOption("Developer Tools", "Entwickler-Werkzeuge", "menu_dev_tools", icon="🔧"))
    
        # Kategorien zur Liste hinzufügen
        self.categories = [
            basic_category,
            automation_category, 
            management_category,
            charts_category,        # Wird nur angezeigt wenn charts_enabled=True
            es_category,           # Wird nur angezeigt wenn es_available=True
            system_category
        ]

    def update_feature_flags(self, **flags):
        """
        Aktualisiert Feature-Flags und baut Nummerierung neu auf
        
        Args:
            **flags: Feature-Flags wie charts_enabled=True, es_available=False
        """
        self.feature_flags.update(flags)
        self._rebuild_option_mapping()
        logger.debug(f"Feature-Flags aktualisiert: {self.feature_flags}")
    
    def _rebuild_option_mapping(self):
        """
        KERN-FUNKTION: Baut die Optionsnummerierung dynamisch neu auf
        
        Das ist wo die echte Dynamik passiert:
        - Nur verfügbare Optionen bekommen Nummern
        - Nummerierung erfolgt automatisch von 1 aufwärts
        - Keine Lücken in der Nummerierung
        - Feature-abhängige Kategorien werden übersprungen
        """
        self.option_mapping.clear()
        option_number = 1
        
        for cat_idx, category in enumerate(self.categories):
            # Hole nur verfügbare Optionen für diese Kategorie
            available_options = category.get_available_options(self.feature_flags)
            
            # Überspringe komplett leere Kategorien
            if not available_options:
                continue
            
            # Nummeriere alle verfügbaren Optionen durch
            for option in available_options:
                self.option_mapping[str(option_number)] = (cat_idx, option.name, option.handler)
                option_number += 1
        
        logger.debug(f"Option-Mapping neu erstellt: {len(self.option_mapping)} Optionen")

    def display_menu(self) -> None:
        """
        VOLLSTÄNDIG KONFIGURIERBARE Menü-Anzeige - KORRIGIERTE VERSION
        Alle Aspekte über .env steuerbar + funktionierende Menü-Stile
        """
        config = load_menu_config_from_env()

        print("\n" + "=" * 60)
        print("🎮 STEAM PRICE TRACKER - DYNAMISCHES MENÜ")
        print("=" * 60)

        option_number = 1
        displayed_categories = 0

        for category in self.categories:
            available_options = category.get_available_options(self.feature_flags)

            if not available_options:
                continue
        
            # 🎨 VERSCHIEDENE KATEGORIE-STILE basierend auf menu_style
            if config['menu_style'] == 'compact':
                # COMPACT: Minimaler Stil
                print(f"\n{category.icon} {category.name}")
                if config['show_descriptions'] and config['show_category_descriptions'] and category.description:
                    print(f"   ⨠ {category.description}")
                print("-" * 30)
            
            elif config['menu_style'] == 'detailed':
                # DETAILED: Ausführlicher Stil
                print(f"\n{category.icon} {category.name.upper()}")
                if config['show_descriptions'] and config['show_category_descriptions'] and category.description:
                    print(f"   ⨠ {category.description}")
                print("─" * 50)
            
            else:
                # STANDARD: Gewohnter Stil (default)
                print(f"\n{category.icon} {category.name}")
                if config['show_descriptions'] and config['show_category_descriptions'] and category.description:
                    print(f"   {category.description}")
                print("-" * 40)

            # 🎨 VERSCHIEDENE OPTION-STILE basierend auf menu_style
            for option in available_options:
            
                if config['menu_style'] == 'compact':
                    # COMPACT: Einzeilig, minimale Beschreibungen
                    option_line = f"{option_number:2d}. {option.icon} {option.name}"
                    if (config['show_descriptions'] and 
                        config['show_option_descriptions'] and 
                        option.description and 
                        len(option.description) <= 30):  # Nur kurze Beschreibungen
                        option_line += f" ⨠ {option.description}"
                    print(option_line)
                
                elif config['menu_style'] == 'detailed':
                    # DETAILED: Mehrzeilig mit ausführlichen Informationen
                    print(f" {option_number:2d}. {option.icon} {option.name}")
                    if (config['show_descriptions'] and 
                        config['show_option_descriptions'] and 
                        option.description):
                        indent = " " * config['description_indent']
                        symbol = config['description_symbol']
                        print(f"{indent}{symbol} {option.description}")
                        print()  # Extra Leerzeile zwischen Optionen
                
                else:
                    # STANDARD: Bewährter mehrzeiliger Stil (default)
                    print(f"{option_number:2d}. {option.icon} {option.name}")
                    if (config['show_descriptions'] and 
                        config['show_option_descriptions'] and 
                        option.description):
                        indent = " " * config['description_indent']
                        symbol = config['description_symbol']
                        print(f"{indent}{symbol} {option.description}")

                option_number += 1

            displayed_categories += 1

        print(f"\n 0. 👋 Beenden")
        print("=" * 60)

        # Debug-Info (konfigurierbar)
        if config['show_debug']:
            print(f"📊 {displayed_categories} Kategorien, {len(self.option_mapping)} Optionen")
            print(f"⚙️ Stil: {config['menu_style']}, Beschreibungen: {config['show_descriptions']}")
    
    def get_handler(self, choice: str) -> Optional[str]:
        """
        Gibt Handler-Funktion für Benutzerwahl zurück
        
        Args:
            choice: Benutzereingabe (z.B. "1", "5", "0")
            
        Returns:
            Handler-Funktionsname oder "exit" für 0, None für ungültige Eingabe
        """
        if choice == "0":
            return "exit"
        
        if choice in self.option_mapping:
            _, _, handler = self.option_mapping[choice]
            return handler
        
        return None
    
    def get_max_option_number(self) -> int:
        """
        Gibt die höchste verfügbare Optionsnummer zurück
        
        Returns:
            Maximale Optionsnummer (für Eingabe-Validierung)
        """
        return len(self.option_mapping)
    
    def get_option_info(self, choice: str) -> Optional[tuple]:
        """
        Gibt detaillierte Informationen über gewählte Option zurück
        
        Args:
            choice: Benutzereingabe
            
        Returns:
            Tuple mit (category_idx, option_name, handler) oder None
        """
        if choice in self.option_mapping:
            return self.option_mapping[choice]
        return None
    
    def add_custom_option(self, category_name: str, option: MenuOption) -> bool:
        """
        Fügt zur Laufzeit eine neue Option zu einer Kategorie hinzu
        
        Args:
            category_name: Name der Ziel-Kategorie
            option: MenuOption-Objekt
            
        Returns:
            True wenn erfolgreich hinzugefügt
        """
        for category in self.categories:
            if category.name == category_name:
                category.add_option(option)
                self._rebuild_option_mapping()  # Nummerierung neu aufbauen
                logger.info(f"Option '{option.name}' zu Kategorie '{category_name}' hinzugefügt")
                return True
        
        logger.warning(f"Kategorie '{category_name}' nicht gefunden")
        return False
    
    def get_menu_statistics(self) -> Dict:
        """
        Gibt Statistiken über das aktuelle Menüsystem zurück
        
        Returns:
            Dict mit Menü-Statistiken
        """
        total_options = 0
        available_options = len(self.option_mapping)
        total_categories = len(self.categories)
        available_categories = 0
        
        for category in self.categories:
            total_options += len(category.options)
            if category.get_available_options(self.feature_flags):
                available_categories += 1
        
        return {
            'total_categories': total_categories,
            'available_categories': available_categories,
            'total_options': total_options,
            'available_options': available_options,
            'feature_flags': self.feature_flags.copy(),
            'dynamic_numbering': True,
            'static_mapping': False  # Das ist der wichtige Punkt!
        }

# Globale Menü-Instanz (Singleton Pattern)
_menu_system = None

def get_menu_system() -> DynamicMenuSystem:
    """
    Gibt die globale Menü-Instanz zurück (Singleton)
    
    Returns:
        DynamicMenuSystem Instanz
    """
    global _menu_system
    if _menu_system is None:
        _menu_system = DynamicMenuSystem()
        logger.debug("Neues DynamicMenuSystem erstellt")
    return _menu_system

def initialize_menu_system(charts_enabled=False, es_available=False, **kwargs):
    """
    Initialisiert Menüsystem mit Feature-Flags
    
    Args:
        charts_enabled: Ob Charts-Funktionen verfügbar sind
        es_available: Ob Elasticsearch verfügbar ist
        **kwargs: Zusätzliche Feature-Flags
        
    Returns:
        Konfiguriertes DynamicMenuSystem
    """
    menu_system = get_menu_system()
    
    # Feature-Flags setzen und Nummerierung neu aufbauen
    menu_system.update_feature_flags(
        charts_enabled=charts_enabled,
        es_available=es_available,
        **kwargs
    )
    
    logger.info(f"Menüsystem initialisiert: {menu_system.get_menu_statistics()}")
    return menu_system

def reset_menu_system():
    """
    Setzt das Menüsystem zurück (für Tests oder Neukonfiguration)
    """
    global _menu_system
    _menu_system = None
    logger.debug("Menüsystem zurückgesetzt")

# Utility-Funktionen für Menu-Validierung
def validate_menu_consistency() -> Dict[str, bool]:
    """
    Validiert dass das Menüsystem konsistent konfiguriert ist
    
    Returns:
        Dict mit Validierungsergebnissen
    """
    menu_system = get_menu_system()
    
    # Teste verschiedene Feature-Flag Kombinationen
    test_results = {}
    
    # Test 1: Keine Features aktiviert
    menu_system.update_feature_flags(charts_enabled=False, es_available=False)
    test_results['no_features'] = len(menu_system.option_mapping) >= 12  # Mindestens BASIS + AUTOMATION + MANAGEMENT + SYSTEM
    
    # Test 2: Nur Charts aktiviert
    menu_system.update_feature_flags(charts_enabled=True, es_available=False)
    test_results['charts_only'] = len(menu_system.option_mapping) >= 17  # + Charts-Optionen
    
    # Test 3: Alle Features aktiviert
    menu_system.update_feature_flags(charts_enabled=True, es_available=True)
    test_results['all_features'] = len(menu_system.option_mapping) >= 22  # + Elasticsearch-Optionen
    
    # Test 4: Nummerierung ohne Lücken
    option_numbers = [int(key) for key in menu_system.option_mapping.keys()]
    if option_numbers:
        expected_numbers = list(range(1, max(option_numbers) + 1))
        test_results['no_gaps'] = option_numbers == expected_numbers
    else:
        test_results['no_gaps'] = False
    
    test_results['overall_valid'] = all(test_results.values())
    
    return test_results

def demo_dynamic_behavior():
    """
    Demonstriert das dynamische Verhalten des Menüsystems
    """
    print("🎯 DEMO: Dynamisches Menüverhalten")
    print("=" * 40)
    
    menu_system = get_menu_system()
    
    scenarios = [
        ("Keine Features", {'charts_enabled': False, 'es_available': False}),
        ("Nur Charts", {'charts_enabled': True, 'es_available': False}),
        ("Nur Elasticsearch", {'charts_enabled': False, 'es_available': True}),
        ("Alle Features", {'charts_enabled': True, 'es_available': True}),
    ]
    
    for name, flags in scenarios:
        print(f"\n📋 Szenario: {name}")
        menu_system.update_feature_flags(**flags)
        stats = menu_system.get_menu_statistics()
        print(f"   Verfügbare Optionen: {stats['available_options']}")
        print(f"   Sichtbare Kategorien: {stats['available_categories']}")

if __name__ == "__main__":
    # Test-Code wenn menu_config.py direkt ausgeführt wird
    print("🧪 Teste dynamisches Menüsystem...")
    
    # Validierung durchführen
    validation = validate_menu_consistency()
    print(f"Validierung: {validation}")
    
    # Demo zeigen
    demo_dynamic_behavior()
    
    print("✅ Test abgeschlossen")