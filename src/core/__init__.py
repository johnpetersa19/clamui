# ClamUI Core Module
"""
Core functionality for ClamUI.
Contains ClamAV integration, scanning logic, and utilities.
"""

from .log_manager import LogEntry, LogManager
from .settings_manager import SettingsManager
from .updater import FreshclamUpdater, UpdateResult, UpdateStatus

__all__ = ["FreshclamUpdater", "UpdateResult", "UpdateStatus", "LogManager", "LogEntry", "SettingsManager"]
