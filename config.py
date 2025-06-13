"""
Configuration Manager für Steam Price Tracker
Vereinfachte Konfiguration fokussiert auf Preis-Tracking
Basiert auf Projekt_SteamGoG.ipynb Store-Integration
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    """Datenbank-Konfiguration für Preis-Tracking"""
    path: str = "steam_price_tracker.db"
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    cleanup_days: int = 90  # Länger als Original da Preisdaten wertvoll sind
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
    
    # Store IDs aus Projekt_SteamGoG.ipynb
    store_ids: str = "1,3,7,11,15,27"
    stores: Dict[str, str] = None
    
    def __post_init__(self):
        if self.stores is None:
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
    
    # Scheduler-Einstellungen
    scheduler_enabled: bool = False
    scheduler_max_workers: int = 1
    cleanup_interval_hours: int = 168  # Wöchentlich
    
    # Preis-Alert Einstellungen (für Zukunft)
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
    
    # CSV-Export Kompatibilität mit Projekt_SteamGoG.ipynb
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
    Vereinfachte Konfigurationsverwaltung für Steam Price Tracker
    Fokussiert auf Preis-Tracking ohne CheapShark-Mapping Komplexität
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
                self.database = DatabaseConfig(
                    path=db_config.get('path', self.database.path),
                    backup_enabled=db_config.get('backup_enabled', self.database.backup_enabled),
                    backup_interval_hours=db_config.get('backup_interval_hours', self.database.backup_interval_hours),
                    cleanup_days=db_config.get('cleanup_days', self.database.cleanup_days),
                    auto_vacuum=db_config.get('auto_vacuum', self.database.auto_vacuum)
                )
            
            # Steam API Config
            if 'steam_api' in config_data:
                steam_config = config_data['steam_api']
                self.steam_api = SteamAPIConfig(
                    base_url=steam_config.get('base_url', self.steam_api.base_url),
                    store_url=steam_config.get('store_url', self.steam_api.store_url),
                    rate_limit_seconds=steam_config.get('rate_limit_seconds', self.steam_api.rate_limit_seconds),
                    timeout_seconds=steam_config.get('timeout_seconds', self.steam_api.timeout_seconds),
                    retry_attempts=steam_config.get('retry_attempts', self.steam_api.retry_attempts)
                )
            
            # CheapShark Config
            if 'cheapshark' in config_data:
                cs_config = config_data['cheapshark']
                self.cheapshark = CheapSharkConfig(
                    base_url=cs_config.get('base_url', self.cheapshark.base_url),
                    rate_limit_seconds=cs_config.get('rate_limit_seconds', self.cheapshark.rate_limit_seconds),
                    timeout_seconds=cs_config.get('timeout_seconds', self.cheapshark.timeout_seconds),
                    retry_attempts=cs_config.get('retry_attempts', self.cheapshark.retry_attempts),
                    store_ids=cs_config.get('store_ids', self.cheapshark.store_ids),
                    stores=cs_config.get('stores', self.cheapshark.stores)
                )
            
            # Tracking Config
            if 'tracking' in config_data:
                track_config = config_data['tracking']
                self.tracking = TrackingConfig(
                    default_interval_hours=track_config.get('default_interval_hours', self.tracking.default_interval_hours),
                    max_apps_per_update=track_config.get('max_apps_per_update', self.tracking.max_apps_per_update),
                    enable_automatic_tracking=track_config.get('enable_automatic_tracking', self.tracking.enable_automatic_tracking),
                    scheduler_enabled=track_config.get('scheduler_enabled', self.tracking.scheduler_enabled),
                    scheduler_max_workers=track_config.get('scheduler_max_workers', self.tracking.scheduler_max_workers),
                    cleanup_interval_hours=track_config.get('cleanup_interval_hours', self.tracking.cleanup_interval_hours),
                    enable_price_alerts=track_config.get('enable_price_alerts', self.tracking.enable_price_alerts),
                    alert_check_interval_hours=track_config.get('alert_check_interval_hours', self.tracking.alert_check_interval_hours)
                )
            
            # Export Config
            if 'export' in config_data:
                export_config = config_data['export']
                self.export = ExportConfig(
                    default_format=export_config.get('default_format', self.export.default_format),
                    output_directory=export_config.get('output_directory', self.export.output_directory),
                    include_metadata=export_config.get('include_metadata', self.export.include_metadata),
                    date_format=export_config.get('date_format', self.export.date_format),
                    price_precision=export_config.get('price_precision', self.export.price_precision),
                    csv_delimiter=export_config.get('csv_delimiter', self.export.csv_delimiter),
                    csv_encoding=export_config.get('csv_encoding', self.export.csv_encoding)
                )
            
            # Wishlist Config
            if 'wishlist' in config_data:
                wish_config = config_data['wishlist']
                self.wishlist = WishlistConfig(
                    default_country_code=wish_config.get('default_country_code', self.wishlist.default_country_code),
                    auto_add_to_tracking=wish_config.get('auto_add_to_tracking', self.wishlist.auto_add_to_tracking),
                    import_batch_size=wish_config.get('import_batch_size', self.wishlist.import_batch_size),
                    include_dlc=wish_config.get('include_dlc', self.wishlist.include_dlc),
                    include_software=wish_config.get('include_software', self.wishlist.include_software)
                )
            
            print(f"✅ Konfiguration geladen aus {self.config_path}")
            
        except Exception as e:
            print(f"⚠️ Fehler beim Laden der Konfiguration: {e}")
            print("📝 Verwende Standard-Konfiguration")
    
    def load_from_environment(self):
        """Lädt Konfiguration aus Umgebungsvariablen (überschreibt JSON)"""
        
        # Database
        if os.getenv('TRACKER_DB_PATH'):
            self.database.path = os.getenv('TRACKER_DB_PATH')
        
        # Steam API
        if os.getenv('STEAM_RATE_LIMIT'):
            try:
                self.steam_api.rate_limit_seconds = float(os.getenv('STEAM_RATE_LIMIT'))
            except ValueError:
                pass
        
        # CheapShark
        if os.getenv('CHEAPSHARK_RATE_LIMIT'):
            try:
                self.cheapshark.rate_limit_seconds = float(os.getenv('CHEAPSHARK_RATE_LIMIT'))
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
        
        # Scheduler
        if os.getenv('SCHEDULER_ENABLED'):
            self.tracking.scheduler_enabled = os.getenv('SCHEDULER_ENABLED').lower() in ['true', '1', 'yes']
        
        # Export
        if os.getenv('EXPORT_DIR'):
            self.export.output_directory = os.getenv('EXPORT_DIR')
        
        # Wishlist
        if os.getenv('DEFAULT_COUNTRY'):
            self.wishlist.default_country_code = os.getenv('DEFAULT_COUNTRY')
        
        # Debug Mode
        if os.getenv('DEBUG_MODE'):
            debug_mode = os.getenv('DEBUG_MODE').lower() in ['true', '1', 'yes']
            if debug_mode:
                # Reduziere Rate Limits für Debug
                self.steam_api.rate_limit_seconds = max(0.5, self.steam_api.rate_limit_seconds)
                self.cheapshark.rate_limit_seconds = max(1.0, self.cheapshark.rate_limit_seconds)
    
    def create_default_config(self):
        """Erstellt eine Standard-Konfigurationsdatei"""
        default_config = {
            "database": {
                "path": self.database.path,
                "backup_enabled": self.database.backup_enabled,
                "backup_interval_hours": self.database.backup_interval_hours,
                "cleanup_days": self.database.cleanup_days,
                "auto_vacuum": self.database.auto_vacuum
            },
            "steam_api": {
                "base_url": self.steam_api.base_url,
                "store_url": self.steam_api.store_url,
                "rate_limit_seconds": self.steam_api.rate_limit_seconds,
                "timeout_seconds": self.steam_api.timeout_seconds,
                "retry_attempts": self.steam_api.retry_attempts
            },
            "cheapshark": {
                "base_url": self.cheapshark.base_url,
                "rate_limit_seconds": self.cheapshark.rate_limit_seconds,
                "timeout_seconds": self.cheapshark.timeout_seconds,
                "retry_attempts": self.cheapshark.retry_attempts,
                "store_ids": self.cheapshark.store_ids,
                "stores": self.cheapshark.stores
            },
            "tracking": {
                "default_interval_hours": self.tracking.default_interval_hours,
                "max_apps_per_update": self.tracking.max_apps_per_update,
                "enable_automatic_tracking": self.tracking.enable_automatic_tracking,
                "scheduler_enabled": self.tracking.scheduler_enabled,
                "scheduler_max_workers": self.tracking.scheduler_max_workers,
                "cleanup_interval_hours": self.tracking.cleanup_interval_hours,
                "enable_price_alerts": self.tracking.enable_price_alerts,
                "alert_check_interval_hours": self.tracking.alert_check_interval_hours
            },
            "export": {
                "default_format": self.export.default_format,
                "output_directory": self.export.output_directory,
                "include_metadata": self.export.include_metadata,
                "date_format": self.export.date_format,
                "price_precision": self.export.price_precision,
                "csv_delimiter": self.export.csv_delimiter,
                "csv_encoding": self.export.csv_encoding
            },
            "wishlist": {
                "default_country_code": self.wishlist.default_country_code,
                "auto_add_to_tracking": self.wishlist.auto_add_to_tracking,
                "import_batch_size": self.wishlist.import_batch_size,
                "include_dlc": self.wishlist.include_dlc,
                "include_software": self.wishlist.include_software
            }
        }
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            print(f"📝 Standard-Konfiguration erstellt: {self.config_path}")
            
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der Konfigurationsdatei: {e}")
    
    def save_config(self):
        """Speichert aktuelle Konfiguration in JSON-Datei"""
        config_data = {
            "database": {
                "path": self.database.path,
                "backup_enabled": self.database.backup_enabled,
                "backup_interval_hours": self.database.backup_interval_hours,
                "cleanup_days": self.database.cleanup_days,
                "auto_vacuum": self.database.auto_vacuum
            },
            "steam_api": {
                "base_url": self.steam_api.base_url,
                "store_url": self.steam_api.store_url,
                "rate_limit_seconds": self.steam_api.rate_limit_seconds,
                "timeout_seconds": self.steam_api.timeout_seconds,
                "retry_attempts": self.steam_api.retry_attempts
            },
            "cheapshark": {
                "base_url": self.cheapshark.base_url,
                "rate_limit_seconds": self.cheapshark.rate_limit_seconds,
                "timeout_seconds": self.cheapshark.timeout_seconds,
                "retry_attempts": self.cheapshark.retry_attempts,
                "store_ids": self.cheapshark.store_ids,
                "stores": self.cheapshark.stores
            },
            "tracking": {
                "default_interval_hours": self.tracking.default_interval_hours,
                "max_apps_per_update": self.tracking.max_apps_per_update,
                "enable_automatic_tracking": self.tracking.enable_automatic_tracking,
                "scheduler_enabled": self.tracking.scheduler_enabled,
                "scheduler_max_workers": self.tracking.scheduler_max_workers,
                "cleanup_interval_hours": self.tracking.cleanup_interval_hours,
                "enable_price_alerts": self.tracking.enable_price_alerts,
                "alert_check_interval_hours": self.tracking.alert_check_interval_hours
            },
            "export": {
                "default_format": self.export.default_format,
                "output_directory": self.export.output_directory,
                "include_metadata": self.export.include_metadata,
                "date_format": self.export.date_format,
                "price_precision": self.export.price_precision,
                "csv_delimiter": self.export.csv_delimiter,
                "csv_encoding": self.export.csv_encoding
            },
            "wishlist": {
                "default_country_code": self.wishlist.default_country_code,
                "auto_add_to_tracking": self.wishlist.auto_add_to_tracking,
                "import_batch_size": self.wishlist.import_batch_size,
                "include_dlc": self.wishlist.include_dlc,
                "include_software": self.wishlist.include_software
            }
        }
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Konfiguration gespeichert: {self.config_path}")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Speichern der Konfiguration: {e}")
            return False
    
    def get_config_summary(self) -> str:
        """Gibt eine Zusammenfassung der aktuellen Konfiguration zurück"""
        return f"""
📋 STEAM PRICE TRACKER KONFIGURATION
{'='*50}
🗄️  Datenbank: {self.database.path}
⏱️  Steam API Rate Limit: {self.steam_api.rate_limit_seconds}s
🛒 CheapShark Rate Limit: {self.cheapshark.rate_limit_seconds}s
🏪 Stores: {', '.join(self.cheapshark.stores.values())}
📊 Tracking-Intervall: {self.tracking.default_interval_hours} Stunden
🚀 Scheduler: {'Aktiviert' if self.tracking.scheduler_enabled else 'Deaktiviert'}
   └─ Max Apps pro Update: {self.tracking.max_apps_per_update}
📄 Export-Format: {self.export.default_format.upper()}
   └─ Ausgabe-Verzeichnis: {self.export.output_directory}
🌍 Standard-Land: {self.wishlist.default_country_code}
🧹 Datenbank-Bereinigung: {self.database.cleanup_days} Tage
💾 Auto-Backup: {'Ja' if self.database.backup_enabled else 'Nein'}
🚨 Preis-Alerts: {'Aktiviert' if self.tracking.enable_price_alerts else 'Deaktiviert'}
"""
    
    def get_store_config(self) -> Dict[str, str]:
        """Gibt Store-Konfiguration zurück (für price_tracker.py)"""
        return self.cheapshark.stores.copy()
    
    def get_store_ids_string(self) -> str:
        """Gibt Store-IDs als String zurück (für CheapShark API)"""
        return self.cheapshark.store_ids
    
    def update_tracking_config(self, **kwargs):
        """Aktualisiert Tracking-Konfiguration"""
        for key, value in kwargs.items():
            if hasattr(self.tracking, key):
                setattr(self.tracking, key, value)
                print(f"✅ {key} auf {value} gesetzt")
            else:
                print(f"⚠️ Unbekannte Tracking-Option: {key}")
    
    def reset_to_defaults(self):
        """Setzt Konfiguration auf Standardwerte zurück"""
        self.database = DatabaseConfig()
        self.steam_api = SteamAPIConfig()
        self.cheapshark = CheapSharkConfig()
        self.tracking = TrackingConfig()
        self.export = ExportConfig()
        self.wishlist = WishlistConfig()
        print("🔄 Konfiguration auf Standardwerte zurückgesetzt")

# Globale Konfigurationsinstanz
config = ConfigManager()

def get_config() -> ConfigManager:
    """Gibt die globale Konfigurationsinstanz zurück"""
    return config

def reload_config():
    """Lädt die Konfiguration neu"""
    global config
    config = ConfigManager()
    return config

def get_store_config() -> Dict[str, str]:
    """Convenience-Funktion für Store-Konfiguration"""
    return config.get_store_config()

def get_store_ids() -> str:
    """Convenience-Funktion für Store-IDs"""
    return config.get_store_ids_string()
