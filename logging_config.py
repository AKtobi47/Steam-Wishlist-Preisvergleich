#!/usr/bin/env python3
"""
Enhanced Logging Configuration für Steam Price Tracker
Liest .env Variablen und konfiguriert Logging entsprechend
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

def load_env_var(key: str, default: str = "") -> str:
    """Lädt Umgebungsvariable oder Fallback"""
    return os.getenv(key, default)

def setup_enhanced_logging(module_name: str = "steam_tracker") -> logging.Logger:
    """
    Konfiguriert Logging basierend auf .env Einstellungen
    
    Args:
        module_name: Name des Moduls für den Logger
        
    Returns:
        Konfigurierter Logger
    """
    
    # .env Variablen laden
    log_level = load_env_var("LOG_LEVEL", "INFO").upper()
    log_file = load_env_var("LOG_FILE", "logs/steam_tracker.log")
    log_rotation = load_env_var("LOG_ROTATION", "true").lower() == "true"
    log_max_size = int(load_env_var("LOG_MAX_SIZE", "10"))
    log_backup_count = int(load_env_var("LOG_BACKUP_COUNT", "5"))
    log_to_console = load_env_var("LOG_TO_CONSOLE", "true").lower() == "true"
    
    # Log-Verzeichnis erstellen
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Logger erstellen
    logger = logging.getLogger(module_name)
    logger.setLevel(getattr(logging, log_level))
    
    # Bestehende Handler entfernen
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # Console Handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File Handler
    if log_rotation:
        # Rotating File Handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=log_max_size * 1024 * 1024,  # MB zu Bytes
            backupCount=log_backup_count
        )
    else:
        # Standard File Handler
        file_handler = logging.FileHandler(log_file)
    
    file_handler.setLevel(logging.DEBUG)  # File bekommt immer DEBUG
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Erfolg loggen
    logger.info(f"✅ Enhanced Logging aktiviert - Level: {log_level}, File: {log_file}")
    
    return logger

# Globale Logger für verschiedene Module
def get_steam_charts_logger():
    """Logger für steam_charts_manager"""
    return setup_enhanced_logging("steam_charts")

def get_database_logger():
    """Logger für database_manager"""
    return setup_enhanced_logging("database")

def get_main_logger():
    """Logger für main.py"""
    return setup_enhanced_logging("main")

def get_batch_logger():
    """Logger für batch_processor"""
    return setup_enhanced_logging("batch_processor")

def get_price_tracker_logger():
    """Logger für price_tracker"""
    return setup_enhanced_logging("price_tracker")

def get_steam_wishlist_logger():
    """Logger für steam_wishlist_manager"""
    return setup_enhanced_logging("steam_wishlist")

def get_scheduler_logger():
    """Logger für background_scheduler"""
    return setup_enhanced_logging("scheduler")