"""
Configuration Manager für Steam Wishlist Manager
Zentrale Konfiguration für alle Module
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    """Datenbank-Konfiguration"""
    path: str = "steam_wishlist.db"
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    cleanup_days: int = 30
    
@dataclass
class SteamAPIConfig:
    """Steam API Konfiguration"""
    base_url: str = "https://api.steampowered.com"
    store_url: str = "https://store.steampowered.com/api"
    rate_limit_seconds: float = 0.5
    timeout_seconds: int = 15
    retry_attempts: int = 3
    
@dataclass
class CheapSharkConfig:
    """CheapShark API Konfiguration"""
    base_url: str = "https://www.cheapshark.com/api/1.0"
    rate_limit_seconds: float = 1.5
    timeout_seconds: int = 15
    retry_attempts: int = 2
    max_consecutive_failures: int = 5
    
@dataclass
class SchedulerConfig:
    """Background Scheduler Konfiguration"""
    enabled: bool = False
    batch_size: int = 10
    interval_minutes: int = 10
    cleanup_interval_hours: int = 24
    max_workers: int = 3
    priority_boost_for_wishlist: int = 3
    
@dataclass
class BulkImportConfig:
    """Bulk Import Konfiguration"""
    preferred_method: str = "steam_store_service"  # steam_api_v2, steam_store_service, steamspy
    batch_size: int = 1000
    enable_steamspy: bool = False
    steamspy_max_pages: int = 10
    
@dataclass
class WishlistConfig:
    """Wishlist Verarbeitung Konfiguration"""
    default_country_code: str = "DE"
    include_steam_prices_default: bool = True
    include_cheapshark_default: bool = True
    auto_schedule_mapping_default: bool = True
    cache_prices: bool = True
    cache_expiry_hours: int = 6

class ConfigManager:
    """
    Zentrale Konfigurationsverwaltung
    Lädt Konfiguration aus JSON-Datei und Umgebungsvariablen
    """
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        
        # Default-Konfiguration
        self.database = DatabaseConfig()
        self.steam_api = SteamAPIConfig()
        self.cheapshark = CheapSharkConfig()
        self.scheduler = SchedulerConfig()
        self.bulk_import = BulkImportConfig()
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
                    cleanup_days=db_config.get('cleanup_days', self.database.cleanup_days)
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
                    max_consecutive_failures=cs_config.get('max_consecutive_failures', self.cheapshark.max_consecutive_failures)
                )
            
            # Scheduler Config
            if 'scheduler' in config_data:
                sched_config = config_data['scheduler']
                self.scheduler = SchedulerConfig(
                    enabled=sched_config.get('enabled', self.scheduler.enabled),
                    batch_size=sched_config.get('batch_size', self.scheduler.batch_size),
                    interval_minutes=sched_config.get('interval_minutes', self.scheduler.interval_minutes),
                    cleanup_interval_hours=sched_config.get('cleanup_interval_hours', self.scheduler.cleanup_interval_hours),
                    max_workers=sched_config.get('max_workers', self.scheduler.max_workers),
                    priority_boost_for_wishlist=sched_config.get('priority_boost_for_wishlist', self.scheduler.priority_boost_for_wishlist)
                )
            
            # Bulk Import Config
            if 'bulk_import' in config_data:
                bulk_config = config_data['bulk_import']
                self.bulk_import = BulkImportConfig(
                    preferred_method=bulk_config.get('preferred_method', self.bulk_import.preferred_method),
                    batch_size=bulk_config.get('batch_size', self.bulk_import.batch_size),
                    enable_steamspy=bulk_config.get('enable_steamspy', self.bulk_import.enable_steamspy),
                    steamspy_max_pages=bulk_config.get('steamspy_max_pages', self.bulk_import.steamspy_max_pages)
                )
            
            # Wishlist Config
            if 'wishlist' in config_data:
                wish_config = config_data['wishlist']
                self.wishlist = WishlistConfig(
                    default_country_code=wish_config.get('default_country_code', self.wishlist.default_country_code),
                    include_steam_prices_default=wish_config.get('include_steam_prices_default', self.wishlist.include_steam_prices_default),
                    include_cheapshark_default=wish_config.get('include_cheapshark_default', self.wishlist.include_cheapshark_default),
                    auto_schedule_mapping_default=wish_config.get('auto_schedule_mapping_default', self.wishlist.auto_schedule_mapping_default),
                    cache_prices=wish_config.get('cache_prices', self.wishlist.cache_prices),
                    cache_expiry_hours=wish_config.get('cache_expiry_hours', self.wishlist.cache_expiry_hours)
                )
            
            print(f"✅ Konfiguration geladen aus {self.config_path}")
            
        except Exception as e:
            print(f"⚠️ Fehler beim Laden der Konfiguration: {e}")
            print("📝 Verwende Standard-Konfiguration")
    
    def load_from_environment(self):
        """Lädt Konfiguration aus Umgebungsvariablen (überschreibt JSON)"""
        # Database
        if os.getenv('STEAM_WL_DB_PATH'):
            self.database.path = os.getenv('STEAM_WL_DB_PATH')
        
        # Steam API
        if os.getenv('STEAM_WL_RATE_LIMIT'):
            try:
                self.steam_api.rate_limit_seconds = float(os.getenv('STEAM_WL_RATE_LIMIT'))
            except ValueError:
                pass
        
        # CheapShark
        if os.getenv('CHEAPSHARK_RATE_LIMIT'):
            try:
                self.cheapshark.rate_limit_seconds = float(os.getenv('CHEAPSHARK_RATE_LIMIT'))
            except ValueError:
                pass
        
        # Scheduler
        if os.getenv('STEAM_WL_SCHEDULER_ENABLED'):
            self.scheduler.enabled = os.getenv('STEAM_WL_SCHEDULER_ENABLED').lower() in ['true', '1', 'yes']
        
        if os.getenv('STEAM_WL_SCHEDULER_INTERVAL'):
            try:
                self.scheduler.interval_minutes = int(os.getenv('STEAM_WL_SCHEDULER_INTERVAL'))
            except ValueError:
                pass
        
        # Wishlist
        if os.getenv('STEAM_WL_DEFAULT_COUNTRY'):
            self.wishlist.default_country_code = os.getenv('STEAM_WL_DEFAULT_COUNTRY')
    
    def create_default_config(self):
        """Erstellt eine Standard-Konfigurationsdatei"""
        default_config = {
            "database": {
                "path": self.database.path,
                "backup_enabled": self.database.backup_enabled,
                "backup_interval_hours": self.database.backup_interval_hours,
                "cleanup_days": self.database.cleanup_days
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
                "max_consecutive_failures": self.cheapshark.max_consecutive_failures
            },
            "scheduler": {
                "enabled": self.scheduler.enabled,
                "batch_size": self.scheduler.batch_size,
                "interval_minutes": self.scheduler.interval_minutes,
                "cleanup_interval_hours": self.scheduler.cleanup_interval_hours,
                "max_workers": self.scheduler.max_workers,
                "priority_boost_for_wishlist": self.scheduler.priority_boost_for_wishlist
            },
            "bulk_import": {
                "preferred_method": self.bulk_import.preferred_method,
                "batch_size": self.bulk_import.batch_size,
                "enable_steamspy": self.bulk_import.enable_steamspy,
                "steamspy_max_pages": self.bulk_import.steamspy_max_pages
            },
            "wishlist": {
                "default_country_code": self.wishlist.default_country_code,
                "include_steam_prices_default": self.wishlist.include_steam_prices_default,
                "include_cheapshark_default": self.wishlist.include_cheapshark_default,
                "auto_schedule_mapping_default": self.wishlist.auto_schedule_mapping_default,
                "cache_prices": self.wishlist.cache_prices,
                "cache_expiry_hours": self.wishlist.cache_expiry_hours
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
                "cleanup_days": self.database.cleanup_days
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
                "max_consecutive_failures": self.cheapshark.max_consecutive_failures
            },
            "scheduler": {
                "enabled": self.scheduler.enabled,
                "batch_size": self.scheduler.batch_size,
                "interval_minutes": self.scheduler.interval_minutes,
                "cleanup_interval_hours": self.scheduler.cleanup_interval_hours,
                "max_workers": self.scheduler.max_workers,
                "priority_boost_for_wishlist": self.scheduler.priority_boost_for_wishlist
            },
            "bulk_import": {
                "preferred_method": self.bulk_import.preferred_method,
                "batch_size": self.bulk_import.batch_size,
                "enable_steamspy": self.bulk_import.enable_steamspy,
                "steamspy_max_pages": self.bulk_import.steamspy_max_pages
            },
            "wishlist": {
                "default_country_code": self.wishlist.default_country_code,
                "include_steam_prices_default": self.wishlist.include_steam_prices_default,
                "include_cheapshark_default": self.wishlist.include_cheapshark_default,
                "auto_schedule_mapping_default": self.wishlist.auto_schedule_mapping_default,
                "cache_prices": self.wishlist.cache_prices,
                "cache_expiry_hours": self.wishlist.cache_expiry_hours
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
📋 STEAM WISHLIST MANAGER KONFIGURATION
={'='*50}
🗄️  Datenbank: {self.database.path}
⏱️  Steam API Rate Limit: {self.steam_api.rate_limit_seconds}s
🛒 CheapShark Rate Limit: {self.cheapshark.rate_limit_seconds}s
🚀 Scheduler: {'Aktiviert' if self.scheduler.enabled else 'Deaktiviert'}
   └─ Intervall: {self.scheduler.interval_minutes} Minuten
   └─ Batch-Größe: {self.scheduler.batch_size}
📥 Bulk Import Methode: {self.bulk_import.preferred_method}
🌍 Standard-Land: {self.wishlist.default_country_code}
💰 Preise cachen: {'Ja' if self.wishlist.cache_prices else 'Nein'}
🎯 Auto CheapShark-Mapping: {'Ja' if self.wishlist.auto_schedule_mapping_default else 'Nein'}
"""

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