# ClamUI Updater Module
"""
Updater module for ClamUI providing freshclam subprocess execution and async database updates.
"""

import subprocess
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from gi.repository import GLib

from .utils import check_freshclam_installed, get_freshclam_path


class UpdateStatus(Enum):
    """Status of a database update operation."""
    SUCCESS = "success"       # Database updated successfully (exit code 0)
    UP_TO_DATE = "up_to_date" # Database already current (exit code 0, no updates)
    ERROR = "error"           # Error occurred (exit code 1 or exception)
    CANCELLED = "cancelled"   # Update was cancelled


@dataclass
class UpdateResult:
    """Result of a database update operation."""
    status: UpdateStatus
    stdout: str
    stderr: str
    exit_code: int
    databases_updated: int
    error_message: Optional[str]

    @property
    def is_success(self) -> bool:
        """Check if update completed successfully."""
        return self.status in (UpdateStatus.SUCCESS, UpdateStatus.UP_TO_DATE)

    @property
    def has_error(self) -> bool:
        """Check if update encountered an error."""
        return self.status == UpdateStatus.ERROR


class FreshclamUpdater:
    """
    ClamAV database updater with async execution support.

    Provides methods for running freshclam in a background thread
    while safely updating the UI via GLib.idle_add.
    """

    def __init__(self):
        """Initialize the updater."""
        self._current_process: Optional[subprocess.Popen] = None
        self._update_cancelled = False

    def check_available(self) -> tuple[bool, Optional[str]]:
        """
        Check if freshclam is available for database updates.

        Returns:
            Tuple of (is_available, version_or_error)
        """
        return check_freshclam_installed()

    def update_sync(self) -> UpdateResult:
        """
        Execute a synchronous database update.

        WARNING: This will block the calling thread. For UI applications,
        use update_async() instead.

        Returns:
            UpdateResult with update details
        """
        # Check freshclam is available
        is_installed, version_or_error = check_freshclam_installed()
        if not is_installed:
            return UpdateResult(
                status=UpdateStatus.ERROR,
                stdout="",
                stderr=version_or_error or "freshclam not installed",
                exit_code=-1,
                databases_updated=0,
                error_message=version_or_error
            )

        # Build freshclam command
        cmd = self._build_command()

        try:
            self._update_cancelled = False
            self._current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = self._current_process.communicate()
            exit_code = self._current_process.returncode
            self._current_process = None

            # Check if cancelled during execution
            if self._update_cancelled:
                return UpdateResult(
                    status=UpdateStatus.CANCELLED,
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=exit_code,
                    databases_updated=0,
                    error_message="Update cancelled by user"
                )

            # Parse the results
            return self._parse_results(stdout, stderr, exit_code)

        except FileNotFoundError:
            return UpdateResult(
                status=UpdateStatus.ERROR,
                stdout="",
                stderr="freshclam executable not found",
                exit_code=-1,
                databases_updated=0,
                error_message="freshclam executable not found"
            )
        except PermissionError as e:
            return UpdateResult(
                status=UpdateStatus.ERROR,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                databases_updated=0,
                error_message=f"Permission denied: {e}"
            )
        except Exception as e:
            return UpdateResult(
                status=UpdateStatus.ERROR,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                databases_updated=0,
                error_message=f"Update failed: {e}"
            )

    def update_async(
        self,
        callback: Callable[[UpdateResult], None]
    ) -> None:
        """
        Execute an asynchronous database update.

        The update runs in a background thread and the callback is invoked
        on the main GTK thread via GLib.idle_add when complete.

        Args:
            callback: Function to call with UpdateResult when update completes
        """
        def update_thread():
            result = self.update_sync()
            # Schedule callback on main thread
            GLib.idle_add(callback, result)

        thread = threading.Thread(target=update_thread)
        thread.daemon = True
        thread.start()

    def cancel(self) -> None:
        """
        Cancel the current update operation.

        If an update is in progress, it will be terminated.
        """
        self._update_cancelled = True
        if self._current_process is not None:
            try:
                self._current_process.terminate()
            except (OSError, ProcessLookupError):
                pass

    def _build_command(self) -> list[str]:
        """
        Build the freshclam command arguments.

        Returns:
            List of command arguments
        """
        freshclam = get_freshclam_path() or "freshclam"
        cmd = [freshclam]

        # Add verbose flag for more detailed output
        cmd.append("--verbose")

        return cmd

    def _parse_results(
        self,
        stdout: str,
        stderr: str,
        exit_code: int
    ) -> UpdateResult:
        """
        Parse freshclam output into an UpdateResult.

        freshclam exit codes:
        - 0: Success (updates downloaded or already current)
        - 1: Error occurred

        Args:
            stdout: Standard output from freshclam
            stderr: Standard error from freshclam
            exit_code: Process exit code

        Returns:
            Parsed UpdateResult
        """
        databases_updated = 0
        is_up_to_date = False

        # Combine stdout and stderr for parsing (freshclam uses both)
        output = stdout + stderr

        # Parse output line by line
        for line in output.splitlines():
            line = line.strip()

            # Check for database update messages
            # Format: "daily.cvd updated (version: XXXXX, ..."
            # or "main.cvd updated (version: XXXXX, ..."
            if "updated (version:" in line.lower():
                databases_updated += 1

            # Check if already up to date
            # Format: "daily.cvd database is up-to-date"
            if "is up-to-date" in line.lower() or "is up to date" in line.lower():
                is_up_to_date = True

        # Determine status from exit code and parsed info
        if exit_code == 0:
            if databases_updated > 0:
                status = UpdateStatus.SUCCESS
            else:
                status = UpdateStatus.UP_TO_DATE
            error_message = None
        else:
            status = UpdateStatus.ERROR
            # Try to extract a meaningful error message
            error_message = self._extract_error_message(stdout, stderr)

        return UpdateResult(
            status=status,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            databases_updated=databases_updated,
            error_message=error_message
        )

    def _extract_error_message(self, stdout: str, stderr: str) -> str:
        """
        Extract a meaningful error message from freshclam output.

        Args:
            stdout: Standard output from freshclam
            stderr: Standard error from freshclam

        Returns:
            Extracted error message
        """
        # Check for common error patterns
        output = stdout + stderr

        # Check for lock file error (another freshclam running)
        if "locked" in output.lower() or "lock" in output.lower():
            return "Database is locked. Another freshclam instance may be running."

        # Check for permission errors
        if "permission denied" in output.lower():
            return "Permission denied. You may need elevated privileges to update the database."

        # Check for network errors
        if "can't connect" in output.lower() or "connection" in output.lower():
            return "Connection error. Please check your network connection."

        # Check for DNS errors
        if "can't resolve" in output.lower() or "host not found" in output.lower():
            return "DNS resolution failed. Please check your network settings."

        # Default to stderr content if available
        if stderr.strip():
            return stderr.strip()

        return "Update failed with an unknown error"
