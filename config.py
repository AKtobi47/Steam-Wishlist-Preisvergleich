"""
Configuration Manager für Steam Price Tracker
Vollständige Implementation für alle Konfigurationseinstellungen
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Datenbank-Konfiguration für Preis-Tracking"""
    path: str = "steam_price_tracker.db"
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    cleanup_days: int = 90
    auto_vacuum: bool = True

@dataclass
class SteamAPIConfig:
    """Steam API Konfiguration"""
    base_url: str = "https://api.steampowered.com"
    store_url: str = "https://store.steampowered.com/api"
    rate_limit_seconds: float = 1.0
    timeout_seconds: int = 15
    retry_attempts: int = 3

@dataclass
class CheapSharkConfig:
    """CheapShark API Konfiguration - Basiert auf Projekt_SteamGoG.ipynb"""
    base_url: str = "https://www.cheapshark.com/api/1.0"
    rate_limit_seconds: float = 1.5
    timeout_seconds: int = 15
    retry_attempts: int = 3
    store_ids: str = "1,3,7,11,15,27"
    
    def __post_init__(self):
        if not hasattr(self, 'stores'):
            self.stores = {
                "1": "Steam",
                "3": "GreenManGaming", 
                "7": "GOG",
                "11": "HumbleStore",
                "15": "Fanatical",
                "27": "GamesPlanet"
            }

@dataclass
class TrackingConfig:
    """Preis-Tracking Konfiguration"""
    default_interval_hours: int = 6
    max_apps_per_update: int = 100
    enable_automatic_tracking: bool = False
    scheduler_enabled: bool = False
    scheduler_max_workers: int = 1
    cleanup_interval_hours: int = 168  # Wöchentlich
    enable_price_alerts: bool = True
    alert_check_interval_hours: int = 1

@dataclass
class ExportConfig:
    """Export-Konfiguration"""
    default_format: str = "csv"
    output_directory: str = "exports"
    include_metadata: bool = True
    date_format: str = "%Y-%m-%d"
    price_precision: int = 2
    csv_delimiter: str = ","
    csv_encoding: str = "utf-8"

@dataclass
class WishlistConfig:
    """Steam Wishlist Import Konfiguration"""
    default_country_code: str = "DE"
    auto_add_to_tracking: bool = True
    import_batch_size: int = 50
    include_dlc: bool = False
    include_software: bool = False

class ConfigManager:
    """
    Vollständige Konfigurationsverwaltung für Steam Price Tracker
    """
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        
        # Default-Konfiguration
        self.database = DatabaseConfig()
        self.steam_api = SteamAPIConfig()
        self.cheapshark = CheapSharkConfig()
        self.tracking = TrackingConfig()
        self.export = ExportConfig()
        self.wishlist = WishlistConfig()
        
        # Lade Konfiguration
        self.load_config()
        self.load_from_environment()
        
        logger.info("✅ Konfiguration geladen")
    
    def load_config(self):
        """Lädt Konfiguration aus JSON-Datei"""
        if not self.config_path.exists():
            self.create_default_config()
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Database Config
            if 'database' in config_data:
                db_config = config_data['database']
                self.database = DatabaseConfig(**{
                    k: v for k, v in db_config.items() 
                    if k in DatabaseConfig.__dataclass_fields__
                })
            
            # Steam API Config
            if 'steam_api' in config_data:
                steam_config = config_data['steam_api']
                self.steam_api = SteamAPIConfig(**{
                    k: v for k, v in steam_config.items() 
                    if k in SteamAPIConfig.__dataclass_fields__
                })
            
            # CheapShark Config
            if 'cheapshark' in config_data:
                cs_config = config_data['cheapshark']
                self.cheapshark = CheapSharkConfig(**{
                    k: v for k, v in cs_config.items() 
                    if k in CheapSharkConfig.__dataclass_fields__
                })
            
            # Tracking Config
            if 'tracking' in config_data:
                track_config = config_data['tracking']
                self.tracking = TrackingConfig(**{
                    k: v for k, v in track_config.items() 
                    if k in TrackingConfig.__dataclass_fields__
                })
            
            # Export Config
            if 'export' in config_data:
                export_config = config_data['export']
                self.export = ExportConfig(**{
                    k: v for k, v in export_config.items() 
                    if k in ExportConfig.__dataclass_fields__
                })
            
            # Wishlist Config
            if 'wishlist' in config_data:
                wish_config = config_data['wishlist']
                self.wishlist = WishlistConfig(**{
                    k: v for k, v in wish_config.items() 
                    if k in WishlistConfig.__dataclass_fields__
                })
            
            logger.info(f"✅ Konfiguration geladen aus {self.config_path}")
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Laden der Konfiguration: {e}")
            logger.info("📝 Verwende Standard-Konfiguration")
    
    def load_from_environment(self):
        """Lädt Konfiguration aus Umgebungsvariablen (überschreibt JSON)"""
        
        # Database
        if os.getenv('TRACKER_DB_PATH'):
            self.database.path = os.getenv('TRACKER_DB_PATH')
        
        if os.getenv('DB_CLEANUP_DAYS'):
            try:
                self.database.cleanup_days = int(os.getenv('DB_CLEANUP_DAYS'))
            except ValueError:
                pass
        
        # Steam API
        if os.getenv('STEAM_RATE_LIMIT'):
            try:
                self.steam_api.rate_limit_seconds = float(os.getenv('STEAM_RATE_LIMIT'))
            except ValueError:
                pass
        
        if os.getenv('STEAM_TIMEOUT'):
            try:
                self.steam_api.timeout_seconds = int(os.getenv('STEAM_TIMEOUT'))
            except ValueError:
                pass
        
        # CheapShark
        if os.getenv('CHEAPSHARK_RATE_LIMIT'):
            try:
                self.cheapshark.rate_limit_seconds = float(os.getenv('CHEAPSHARK_RATE_LIMIT'))
            except ValueError:
                pass
        
        if os.getenv('CHEAPSHARK_TIMEOUT'):
            try:
                self.cheapshark.timeout_seconds = int(os.getenv('CHEAPSHARK_TIMEOUT'))
            except ValueError:
                pass
        
        # Tracking
        if os.getenv('TRACKING_INTERVAL_HOURS'):
            try:
                self.tracking.default_interval_hours = int(os.getenv('TRACKING_INTERVAL_HOURS'))
            except ValueError:
                pass
        
        if os.getenv('MAX_APPS_PER_UPDATE'):
            try:
                self.tracking.max_apps_per_update = int(os.getenv('MAX_APPS_PER_UPDATE'))
            except ValueError:
                pass
        
        if os.getenv('ENABLE_AUTOMATIC_TRACKING'):
            self.tracking.enable_automatic_tracking = os.getenv('ENABLE_AUTOMATIC_TRACKING').lower() in ['true', '1', 'yes']
        
        # Export
        if os.getenv('EXPORT_FORMAT'):
            self.export.default_format = os.getenv('EXPORT_FORMAT')
        
        if os.getenv('EXPORT_DIRECTORY'):
            self.export.output_directory = os.getenv('EXPORT_DIRECTORY')
        
        # Wishlist
        if os.getenv('DEFAULT_COUNTRY_CODE'):
            self.wishlist.default_country_code = os.getenv('DEFAULT_COUNTRY_CODE')
        
        if os.getenv('WISHLIST_BATCH_SIZE'):
            try:
                self.wishlist.import_batch_size = int(os.getenv('WISHLIST_BATCH_SIZE'))
            except ValueError:
                pass
        
        logger.debug("🔄 Umgebungsvariablen geladen")
    
    def create_default_config(self):
        """Erstellt Standard-Konfigurationsdatei"""
        default_config = {
            "database": asdict(self.database),
            "steam_api": asdict(self.steam_api),
            "cheapshark": asdict(self.cheapshark),
            "tracking": asdict(self.tracking),
            "export": asdict(self.export),
            "wishlist": asdict(self.wishlist)
        }
        
        # CheapShark stores hinzufügen
        default_config["cheapshark"]["stores"] = {
            "1": "Steam",
            "3": "GreenManGaming", 
            "7": "GOG",
            "11": "HumbleStore",
            "15": "Fanatical",
            "27": "GamesPlanet"
        }
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Standard-Konfiguration erstellt: {self.config_path}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der Standard-Konfiguration: {e}")
    
    def save_config(self):
        """Speichert aktuelle Konfiguration in JSON-Datei"""
        config_data = {
            "database": asdict(self.database),
            "steam_api": asdict(self.steam_api),
            "cheapshark": asdict(self.cheapshark),
            "tracking": asdict(self.tracking),
            "export": asdict(self.export),
            "wishlist": asdict(self.wishlist)
        }
        
        # CheapShark stores hinzufügen
        config_data["cheapshark"]["stores"] = {
            "1": "Steam",
            "3": "GreenManGaming", 
            "7": "GOG",
            "11": "HumbleStore",
            "15": "Fanatical",
            "27": "GamesPlanet"
        }
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Konfiguration gespeichert: {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Konfiguration: {e}")
            return False
    
    def get_config_summary(self) -> str:
        """Gibt eine Zusammenfassung der aktuellen Konfiguration zurück"""
        return f"""
📋 STEAM PRICE TRACKER KONFIGURATION
=====================================

🗄️ DATENBANK:
   Path: {self.database.path}
   Backup: {'✅' if self.database.backup_enabled else '❌'}
   Cleanup: {self.database.cleanup_days} Tage
   Auto-Vacuum: {'✅' if self.database.auto_vacuum else '❌'}

🌐 STEAM API:
   Rate Limit: {self.steam_api.rate_limit_seconds}s
   Timeout: {self.steam_api.timeout_seconds}s
   Retry: {self.steam_api.retry_attempts}x

🦈 CHEAPSHARK API:
   Rate Limit: {self.cheapshark.rate_limit_seconds}s
   Timeout: {self.cheapshark.timeout_seconds}s
   Stores: {len(getattr(self.cheapshark, 'stores', {}))}

📊 TRACKING:
   Intervall: {self.tracking.default_interval_hours}h
   Max Apps: {self.tracking.max_apps_per_update}
   Auto-Tracking: {'✅' if self.tracking.enable_automatic_tracking else '❌'}
   Scheduler: {'✅' if self.tracking.scheduler_enabled else '❌'}

📄 EXPORT:
   Format: {self.export.default_format}
   Verzeichnis: {self.export.output_directory}
   Encoding: {self.export.csv_encoding}

📥 WISHLIST:
   Land: {self.wishlist.default_country_code}
   Batch Size: {self.wishlist.import_batch_size}
   Auto-Add: {'✅' if self.wishlist.auto_add_to_tracking else '❌'}
"""
    
    def update_setting(self, section: str, key: str, value: Any) -> bool:
        """
        Aktualisiert eine spezifische Einstellung
        
        Args:
            section: Konfigurationsbereich (database, steam_api, etc.)
            key: Einstellungsname
            value: Neuer Wert
            
        Returns:
            True wenn erfolgreich aktualisiert
        """
        try:
            if section == "database" and hasattr(self.database, key):
                setattr(self.database, key, value)
            elif section == "steam_api" and hasattr(self.steam_api, key):
                setattr(self.steam_api, key, value)
            elif section == "cheapshark" and hasattr(self.cheapshark, key):
                setattr(self.cheapshark, key, value)
            elif section == "tracking" and hasattr(self.tracking, key):
                setattr(self.tracking, key, value)
            elif section == "export" and hasattr(self.export, key):
                setattr(self.export, key, value)
            elif section == "wishlist" and hasattr(self.wishlist, key):
                setattr(self.wishlist, key, value)
            else:
                logger.error(f"❌ Unbekannte Einstellung: {section}.{key}")
                return False
            
            logger.info(f"✅ Einstellung aktualisiert: {section}.{key} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren von {section}.{key}: {e}")
            return False
    
    def get_setting(self, section: str, key: str) -> Any:
        """
        Holt eine spezifische Einstellung
        
        Args:
            section: Konfigurationsbereich
            key: Einstellungsname
            
        Returns:
            Wert der Einstellung oder None
        """
        try:
            if section == "database":
                return getattr(self.database, key, None)
            elif section == "steam_api":
                return getattr(self.steam_api, key, None)
            elif section == "cheapshark":
                return getattr(self.cheapshark, key, None)
            elif section == "tracking":
                return getattr(self.tracking, key, None)
            elif section == "export":
                return getattr(self.export, key, None)
            elif section == "wishlist":
                return getattr(self.wishlist, key, None)
            else:
                return None
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen von {section}.{key}: {e}")
            return None
    
    def validate_config(self) -> Dict[str, bool]:
        """
        Validiert die aktuelle Konfiguration
        
        Returns:
            Dict mit Validierungsergebnissen
        """
        validation_results = {}
        
        # Database Validation
        validation_results['database_path_writable'] = True
        try:
            db_path = Path(self.database.path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            # Test ob schreibbar
            test_file = db_path.parent / "test_write.tmp"
            test_file.touch()
            test_file.unlink()
        except Exception:
            validation_results['database_path_writable'] = False
        
        # Rate Limits Validation
        validation_results['steam_rate_limit_valid'] = 0 < self.steam_api.rate_limit_seconds <= 10
        validation_results['cheapshark_rate_limit_valid'] = 0 < self.cheapshark.rate_limit_seconds <= 10
        
        # Timeout Validation
        validation_results['steam_timeout_valid'] = 5 <= self.steam_api.timeout_seconds <= 60
        validation_results['cheapshark_timeout_valid'] = 5 <= self.cheapshark.timeout_seconds <= 60
        
        # Tracking Validation
        validation_results['tracking_interval_valid'] = 1 <= self.tracking.default_interval_hours <= 168
        validation_results['max_apps_valid'] = 1 <= self.tracking.max_apps_per_update <= 1000
        
        # Export Validation
        export_dir = Path(self.export.output_directory)
        validation_results['export_dir_valid'] = True
        try:
            export_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            validation_results['export_dir_valid'] = False
        
        # Wishlist Validation
        validation_results['country_code_valid'] = len(self.wishlist.default_country_code) == 2
        validation_results['batch_size_valid'] = 1 <= self.wishlist.import_batch_size <= 200
        
        return validation_results
    
    def get_validation_summary(self) -> str:
        """Gibt Validierungszusammenfassung als String zurück"""
        results = self.validate_config()
        
        summary = "🔍 KONFIGURATION VALIDIERUNG\n"
        summary += "=" * 30 + "\n\n"
        
        for key, is_valid in results.items():
            status = "✅" if is_valid else "❌"
            readable_key = key.replace('_', ' ').title()
            summary += f"{status} {readable_key}\n"
        
        total_valid = sum(results.values())
        total_checks = len(results)
        
        summary += f"\n📊 Ergebnis: {total_valid}/{total_checks} Checks bestanden"
        
        if total_valid == total_checks:
            summary += " 🎉"
        elif total_valid >= total_checks * 0.8:
            summary += " ⚠️"
        else:
            summary += " ❌"
        
        return summary

# Globale Konfigurationsinstanz
_config_instance = None

def get_config(config_path: str = "config.json") -> ConfigManager:
    """
    Gibt die globale Konfigurationsinstanz zurück
    
    Args:
        config_path: Pfad zur Konfigurationsdatei
        
    Returns:
        ConfigManager Instanz
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = ConfigManager(config_path)
    
    return _config_instance

def reload_config(config_path: str = "config.json") -> ConfigManager:
    """
    Lädt die Konfiguration neu
    
    Args:
        config_path: Pfad zur Konfigurationsdatei
        
    Returns:
        Neue ConfigManager Instanz
    """
    global _config_instance
    _config_instance = ConfigManager(config_path)
    return _config_instance