# ClamUI Logging Configuration Module
"""
Centralized logging configuration for ClamUI.

This module provides a configurable logging system with:
- Privacy-aware formatting that replaces home directory paths with ~
- Rotating file handlers to manage disk space
- Thread-safe runtime reconfiguration
- Log export and management utilities

Logging should be configured early in application startup, before
other modules that use logging are imported.
"""

import logging
import os
import threading
import zipfile
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .sanitize import sanitize_path_for_logging

# Default log directory follows XDG specification
DEFAULT_LOG_DIR = (
    Path(os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))) / "clamui" / "debug"
)

# Default log settings
DEFAULT_LOG_LEVEL = "WARNING"
DEFAULT_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
DEFAULT_BACKUP_COUNT = 3  # 3 backup files = 20 MB max total

# Log format with timestamp, level, module, and message
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class PrivacyFormatter(logging.Formatter):
    """
    Custom log formatter that sanitizes paths for privacy.

    Replaces home directory paths with ~ in log messages to prevent
    accidental exposure of usernames when logs are shared or exported.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record with privacy-aware path sanitization.

        Args:
            record: The log record to format

        Returns:
            Formatted log string with sanitized paths
        """
        # Format the message first
        formatted = super().format(record)

        # Sanitize paths in the formatted message
        return sanitize_path_for_logging(formatted)


class LoggingConfig:
    """
    Singleton manager for ClamUI logging configuration.

    Provides thread-safe methods for configuring logging, changing
    log levels at runtime, and managing log files (export, clear).
    """

    _instance: "LoggingConfig | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "LoggingConfig":
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the logging configuration (only runs once)."""
        if self._initialized:
            return

        self._file_handler: RotatingFileHandler | None = None
        self._log_dir: Path = DEFAULT_LOG_DIR
        self._log_file: Path | None = None
        self._config_lock = threading.Lock()
        self._initialized = True

    def configure(
        self,
        log_dir: Path | str | None = None,
        log_level: str = DEFAULT_LOG_LEVEL,
        max_bytes: int = DEFAULT_MAX_BYTES,
        backup_count: int = DEFAULT_BACKUP_COUNT,
    ) -> bool:
        """
        Configure the logging system.

        Sets up a rotating file handler with privacy-aware formatting.
        Should be called early in application startup.

        Args:
            log_dir: Directory for log files (default: ~/.local/share/clamui/debug/)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            max_bytes: Maximum size per log file in bytes
            backup_count: Number of backup files to keep

        Returns:
            True if configuration succeeded, False otherwise
        """
        with self._config_lock:
            try:
                # Set up log directory
                if log_dir is not None:
                    self._log_dir = Path(log_dir)
                else:
                    self._log_dir = DEFAULT_LOG_DIR

                # Create log directory with restricted permissions
                self._log_dir.mkdir(parents=True, exist_ok=True)
                # Secure the directory (owner only)
                self._log_dir.chmod(0o700)

                # Set up log file path
                self._log_file = self._log_dir / "clamui.log"

                # Remove existing handler if reconfiguring
                root_logger = logging.getLogger("src")
                if self._file_handler is not None:
                    root_logger.removeHandler(self._file_handler)
                    self._file_handler.close()

                # Create rotating file handler
                self._file_handler = RotatingFileHandler(
                    self._log_file,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding="utf-8",
                )

                # Set file permissions (owner read/write only)
                if self._log_file.exists():
                    self._log_file.chmod(0o600)

                # Configure formatter with privacy sanitization
                formatter = PrivacyFormatter(LOG_FORMAT, DATE_FORMAT)
                self._file_handler.setFormatter(formatter)

                # Set log level
                level = getattr(logging, log_level.upper(), logging.WARNING)
                self._file_handler.setLevel(level)

                # Configure the root logger for "src" package
                root_logger.setLevel(level)
                root_logger.addHandler(self._file_handler)

                # Log successful initialization
                root_logger.info(
                    "Logging configured: level=%s, max_size=%d bytes, backups=%d",
                    log_level,
                    max_bytes,
                    backup_count,
                )

                return True

            except (OSError, PermissionError) as e:
                # Log to stderr if file logging fails
                import sys

                print(f"Failed to configure logging: {e}", file=sys.stderr)
                return False

    def set_log_level(self, level: str) -> bool:
        """
        Change the log level at runtime.

        Args:
            level: New log level (DEBUG, INFO, WARNING, ERROR)

        Returns:
            True if level was changed successfully
        """
        with self._config_lock:
            try:
                log_level = getattr(logging, level.upper(), None)
                if log_level is None:
                    return False

                if self._file_handler is not None:
                    self._file_handler.setLevel(log_level)

                # Also update the root logger
                root_logger = logging.getLogger("src")
                root_logger.setLevel(log_level)

                root_logger.info("Log level changed to %s", level)
                return True

            except Exception:
                return False

    def get_log_level(self) -> str:
        """
        Get the current log level name.

        Returns:
            Current log level as string (e.g., "WARNING")
        """
        with self._config_lock:
            if self._file_handler is not None:
                level = self._file_handler.level
                return logging.getLevelName(level)
            return DEFAULT_LOG_LEVEL

    def _get_log_files_unlocked(self) -> list[Path]:
        """
        Get list of all log files without acquiring lock.

        Internal method for use within methods that already hold the lock.

        Returns:
            List of Path objects for all log files, sorted by name
        """
        if self._log_dir is None or not self._log_dir.exists():
            return []

        # Match main log file and rotated backups (e.g., clamui.log.1)
        log_files = list(self._log_dir.glob("clamui.log*"))
        return sorted(log_files)

    def get_log_files(self) -> list[Path]:
        """
        Get list of all log files (current + rotated backups).

        Returns:
            List of Path objects for all log files, sorted by name
        """
        with self._config_lock:
            return self._get_log_files_unlocked()

    def get_log_dir(self) -> Path:
        """
        Get the log directory path.

        Returns:
            Path to the log directory
        """
        return self._log_dir

    def get_total_log_size(self) -> int:
        """
        Get total size of all log files in bytes.

        Returns:
            Total size in bytes
        """
        total = 0
        for log_file in self.get_log_files():
            try:
                total += log_file.stat().st_size
            except (OSError, FileNotFoundError):
                pass
        return total

    def clear_logs(self) -> bool:
        """
        Delete all log files.

        Returns:
            True if all files were deleted successfully
        """
        with self._config_lock:
            try:
                # Close the current handler to release file locks
                if self._file_handler is not None:
                    root_logger = logging.getLogger("src")
                    root_logger.removeHandler(self._file_handler)
                    self._file_handler.close()
                    self._file_handler = None

                # Delete all log files
                success = True
                for log_file in self._get_log_files_unlocked():
                    try:
                        log_file.unlink()
                    except (OSError, PermissionError):
                        success = False

                # Reconfigure logging with a fresh handler
                # (This will create a new empty log file)
                if self._log_file is not None:
                    self._file_handler = RotatingFileHandler(
                        self._log_file,
                        maxBytes=DEFAULT_MAX_BYTES,
                        backupCount=DEFAULT_BACKUP_COUNT,
                        encoding="utf-8",
                    )
                    formatter = PrivacyFormatter(LOG_FORMAT, DATE_FORMAT)
                    self._file_handler.setFormatter(formatter)

                    root_logger = logging.getLogger("src")
                    current_level = root_logger.level or logging.WARNING
                    self._file_handler.setLevel(current_level)
                    root_logger.addHandler(self._file_handler)

                    root_logger.info("Log files cleared")

                return success

            except Exception:
                return False

    def export_logs_zip(self, output_path: Path | str) -> bool:
        """
        Export all log files to a ZIP archive.

        Args:
            output_path: Path for the output ZIP file

        Returns:
            True if export succeeded
        """
        with self._config_lock:
            try:
                output_path = Path(output_path)
                log_files = self._get_log_files_unlocked()

                if not log_files:
                    return False

                # Create ZIP archive
                with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    for log_file in log_files:
                        # Use just the filename in the archive
                        zf.write(log_file, log_file.name)

                # Log the export
                logger = logging.getLogger("src")
                logger.info(
                    "Exported %d log file(s) to %s",
                    len(log_files),
                    sanitize_path_for_logging(str(output_path)),
                )

                return True

            except (OSError, zipfile.BadZipFile) as e:
                logger = logging.getLogger("src")
                logger.error("Failed to export logs: %s", e)
                return False

    def generate_export_filename(self) -> str:
        """
        Generate a timestamped filename for log export.

        Returns:
            Filename like "clamui-logs-2024-01-15-143052.zip"
        """
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        return f"clamui-logs-{timestamp}.zip"


# Module-level singleton instance
_config = LoggingConfig()


def configure_logging(
    log_level: str = DEFAULT_LOG_LEVEL,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
    log_dir: Path | str | None = None,
) -> bool:
    """
    Configure the ClamUI logging system.

    This is the main entry point for setting up logging. Should be called
    early in application startup, before importing modules that use logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        max_bytes: Maximum size per log file in bytes
        backup_count: Number of backup files to keep
        log_dir: Optional custom log directory

    Returns:
        True if configuration succeeded
    """
    return _config.configure(
        log_dir=log_dir,
        log_level=log_level,
        max_bytes=max_bytes,
        backup_count=backup_count,
    )


def get_logging_config() -> LoggingConfig:
    """
    Get the LoggingConfig singleton instance.

    Returns:
        The LoggingConfig instance for managing logs
    """
    return _config
