# ClamUI Log Manager Module
"""
Log manager module for ClamUI providing log persistence and retrieval.
Stores scan/update operation logs and provides daemon log access.
"""

import json
import os
import subprocess
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

from gi.repository import GLib

from .utils import which_host_command, wrap_host_command


class LogType(Enum):
    """Type of log entry."""
    SCAN = "scan"
    UPDATE = "update"


class DaemonStatus(Enum):
    """Status of the clamd daemon."""
    RUNNING = "running"
    STOPPED = "stopped"
    NOT_INSTALLED = "not_installed"
    UNKNOWN = "unknown"


@dataclass
class LogEntry:
    """A single log entry for a scan or update operation."""
    id: str
    timestamp: str  # ISO format string for JSON serialization
    type: str  # "scan" or "update"
    status: str  # e.g., "clean", "infected", "success", "error"
    summary: str
    details: str
    path: Optional[str] = None  # Scanned path (for scans)
    duration: float = 0.0  # Operation duration in seconds

    @classmethod
    def create(
        cls,
        log_type: str,
        status: str,
        summary: str,
        details: str,
        path: Optional[str] = None,
        duration: float = 0.0
    ) -> "LogEntry":
        """
        Create a new LogEntry with auto-generated id and timestamp.

        Args:
            log_type: Type of operation ("scan" or "update")
            status: Status of the operation
            summary: Brief description of the operation
            details: Full output/details
            path: Scanned path (for scan operations)
            duration: Operation duration in seconds

        Returns:
            New LogEntry instance
        """
        return cls(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            type=log_type,
            status=status,
            summary=summary,
            details=details,
            path=path,
            duration=duration
        )

    def to_dict(self) -> dict:
        """Convert LogEntry to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "LogEntry":
        """Create LogEntry from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            type=data.get("type", "unknown"),
            status=data.get("status", "unknown"),
            summary=data.get("summary", ""),
            details=data.get("details", ""),
            path=data.get("path"),
            duration=data.get("duration", 0.0)
        )


# Common locations for clamd log files
CLAMD_LOG_PATHS = [
    "/var/log/clamav/clamd.log",
    "/var/log/clamd.log",
]


class LogManager:
    """
    Manager for log persistence and retrieval.

    Provides methods for saving scan/update logs, retrieving historical logs,
    and accessing clamd daemon logs.
    """

    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialize the LogManager.

        Args:
            log_dir: Optional custom log directory. Defaults to XDG_DATA_HOME/clamui/logs
        """
        if log_dir:
            self._log_dir = Path(log_dir)
        else:
            xdg_data_home = os.environ.get("XDG_DATA_HOME", "~/.local/share")
            self._log_dir = Path(xdg_data_home).expanduser() / "clamui" / "logs"

        # Thread lock for safe concurrent access
        self._lock = threading.Lock()

        # Ensure log directory exists
        self._ensure_log_dir()

    def _ensure_log_dir(self) -> None:
        """Ensure the log directory exists."""
        try:
            self._log_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError):
            # Handle silently - will fail on write operations
            pass

    def save_log(self, entry: LogEntry) -> bool:
        """
        Save a log entry to storage.

        Args:
            entry: The LogEntry to save

        Returns:
            True if saved successfully, False otherwise
        """
        with self._lock:
            try:
                self._ensure_log_dir()
                log_file = self._log_dir / f"{entry.id}.json"
                with open(log_file, "w", encoding="utf-8") as f:
                    json.dump(entry.to_dict(), f, indent=2)
                return True
            except (OSError, PermissionError, json.JSONDecodeError):
                return False

    def get_logs(self, limit: int = 100, log_type: Optional[str] = None) -> list[LogEntry]:
        """
        Retrieve stored log entries, sorted by timestamp (newest first).

        Args:
            limit: Maximum number of entries to return
            log_type: Optional filter by type ("scan" or "update")

        Returns:
            List of LogEntry objects
        """
        entries = []

        with self._lock:
            try:
                if not self._log_dir.exists():
                    return entries

                for log_file in self._log_dir.glob("*.json"):
                    try:
                        with open(log_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            entry = LogEntry.from_dict(data)

                            # Apply type filter if specified
                            if log_type is None or entry.type == log_type:
                                entries.append(entry)
                    except (OSError, json.JSONDecodeError):
                        # Skip corrupted files
                        continue

            except OSError:
                return entries

        # Sort by timestamp (newest first) and apply limit
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        return entries[:limit]

    def get_logs_async(
        self,
        callback: Callable[[list["LogEntry"]], None],
        limit: int = 100,
        log_type: Optional[str] = None
    ) -> None:
        """
        Retrieve stored log entries asynchronously.

        The log retrieval runs in a background thread and the callback is invoked
        on the main GTK thread via GLib.idle_add when complete.

        Args:
            callback: Function to call with list of LogEntry objects when loading completes
            limit: Maximum number of entries to return
            log_type: Optional filter by type ("scan" or "update")
        """
        def _load_logs_thread():
            entries = self.get_logs(limit=limit, log_type=log_type)
            # Schedule callback on main thread
            GLib.idle_add(callback, entries)

        thread = threading.Thread(target=_load_logs_thread)
        thread.daemon = True
        thread.start()

    def get_log_by_id(self, log_id: str) -> Optional[LogEntry]:
        """
        Retrieve a specific log entry by ID.

        Args:
            log_id: The UUID of the log entry

        Returns:
            LogEntry if found, None otherwise
        """
        with self._lock:
            try:
                log_file = self._log_dir / f"{log_id}.json"
                if log_file.exists():
                    with open(log_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        return LogEntry.from_dict(data)
            except (OSError, json.JSONDecodeError):
                pass
        return None

    def delete_log(self, log_id: str) -> bool:
        """
        Delete a specific log entry.

        Args:
            log_id: The UUID of the log entry to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        with self._lock:
            try:
                log_file = self._log_dir / f"{log_id}.json"
                if log_file.exists():
                    log_file.unlink()
                    return True
            except OSError:
                pass
        return False

    def clear_logs(self) -> bool:
        """
        Clear all stored log entries.

        Returns:
            True if cleared successfully, False otherwise
        """
        with self._lock:
            try:
                if self._log_dir.exists():
                    for log_file in self._log_dir.glob("*.json"):
                        try:
                            log_file.unlink()
                        except OSError:
                            pass
                return True
            except OSError:
                return False

    def get_log_count(self) -> int:
        """
        Get the total number of stored logs.

        Returns:
            Number of log entries
        """
        with self._lock:
            try:
                if not self._log_dir.exists():
                    return 0
                return len(list(self._log_dir.glob("*.json")))
            except OSError:
                return 0

    def get_daemon_status(self) -> tuple[DaemonStatus, Optional[str]]:
        """
        Check the status of the clamd daemon.

        Returns:
            Tuple of (DaemonStatus, optional_message)
        """
        # Check if clamd is installed (checking host if in Flatpak)
        clamd_path = which_host_command("clamd")
        if clamd_path is None:
            return (DaemonStatus.NOT_INSTALLED, "clamd is not installed")

        # Check if clamd process is running (on host if in Flatpak)
        try:
            result = subprocess.run(
                wrap_host_command(["pgrep", "-x", "clamd"]),
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return (DaemonStatus.RUNNING, "clamd daemon is running")
            else:
                return (DaemonStatus.STOPPED, "clamd daemon is not running")
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            return (DaemonStatus.UNKNOWN, "Unable to determine daemon status")

    def get_daemon_log_path(self) -> Optional[str]:
        """
        Find the clamd log file path.

        Checks common locations for the clamd log file.

        Returns:
            Path to the log file if found, None otherwise
        """
        for log_path in CLAMD_LOG_PATHS:
            if Path(log_path).exists():
                return log_path

        # Also try to get from clamd.conf if it exists
        clamd_conf_paths = [
            "/etc/clamav/clamd.conf",
            "/etc/clamd.conf",
            "/etc/clamd.d/scan.conf",
        ]

        for conf_path in clamd_conf_paths:
            conf_file = Path(conf_path)
            if conf_file.exists():
                try:
                    with open(conf_file, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("LogFile"):
                                parts = line.split(None, 1)
                                if len(parts) == 2:
                                    log_file = parts[1].strip()
                                    if Path(log_file).exists():
                                        return log_file
                except (OSError, PermissionError):
                    continue

        return None

    def read_daemon_logs(self, num_lines: int = 100) -> tuple[bool, str]:
        """
        Read the last N lines from the clamd daemon log.

        Uses tail-like behavior to read only the end of the file,
        avoiding loading large log files into memory.

        Args:
            num_lines: Number of lines to read from the end of the log

        Returns:
            Tuple of (success, log_content_or_error_message)
        """
        log_path = self.get_daemon_log_path()

        if log_path is None:
            return (False, "Daemon log file not found")

        try:
            # Use tail command for efficient reading of large files
            result = subprocess.run(
                ["tail", "-n", str(num_lines), log_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                content = result.stdout
                if not content.strip():
                    return (True, "(Log file is empty)")
                return (True, content)
            else:
                # Try direct read as fallback
                return self._read_file_tail(log_path, num_lines)

        except subprocess.TimeoutExpired:
            return (False, "Timeout reading log file")
        except FileNotFoundError:
            # tail command not found, use direct read
            return self._read_file_tail(log_path, num_lines)
        except PermissionError:
            return (False, "Permission denied reading log file")
        except OSError as e:
            return (False, f"Error reading log file: {e}")

    def _read_file_tail(self, file_path: str, num_lines: int) -> tuple[bool, str]:
        """
        Read the last N lines from a file directly (fallback method).

        Args:
            file_path: Path to the file
            num_lines: Number of lines to read

        Returns:
            Tuple of (success, content_or_error)
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                # For small files, read all and return last N lines
                lines = f.readlines()
                tail_lines = lines[-num_lines:] if len(lines) > num_lines else lines
                content = "".join(tail_lines)
                if not content.strip():
                    return (True, "(Log file is empty)")
                return (True, content)
        except PermissionError:
            return (False, "Permission denied reading log file")
        except OSError as e:
            return (False, f"Error reading log file: {e}")
