# ClamUI Scanner Base Tests
"""Unit tests for the scanner_base module."""

import subprocess
from unittest.mock import MagicMock, patch

from src.core.scanner_base import (
    KILL_WAIT_TIMEOUT,
    STREAM_POLL_TIMEOUT,
    TERMINATE_GRACE_TIMEOUT,
    cleanup_process,
    communicate_with_cancel_check,
    create_cancelled_result,
    create_error_result,
    stream_process_output,
    terminate_process_gracefully,
)
from src.core.scanner_types import ScanStatus


class TestCommunicateWithCancelCheck:
    """Tests for communicate_with_cancel_check function."""

    def test_communicate_without_cancellation(self):
        """Test communication completes normally without cancellation."""
        # Create a mock process
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("stdout output", "stderr output")

        stdout, stderr, cancelled = communicate_with_cancel_check(mock_process, lambda: False)

        assert stdout == "stdout output"
        assert stderr == "stderr output"
        assert cancelled is False

    def test_communicate_with_cancellation(self):
        """Test communication stops when cancelled."""
        mock_process = MagicMock()
        # Simulate the first communicate timing out, then cancel flag set
        mock_process.communicate.side_effect = [
            subprocess.TimeoutExpired("cmd", 0.5),
            ("remaining", ""),
        ]

        cancel_flag = False

        def is_cancelled():
            return cancel_flag

        # Start in a thread, then set cancel flag
        result = []

        def run_communicate():
            nonlocal cancel_flag
            # After first timeout, set cancel flag
            cancel_flag = True
            stdout, stderr, was_cancelled = communicate_with_cancel_check(
                mock_process, is_cancelled
            )
            result.extend([stdout, stderr, was_cancelled])

        run_communicate()

        assert result[2] is True  # was_cancelled
        mock_process.terminate.assert_called()

    def test_communicate_handles_timeout_expired_on_terminate(self):
        """Test handling when terminate doesn't stop process quickly."""
        mock_process = MagicMock()
        mock_process.communicate.side_effect = [
            subprocess.TimeoutExpired("cmd", 2.0),
        ]
        mock_process.wait.return_value = None

        stdout, stderr, cancelled = communicate_with_cancel_check(
            mock_process,
            lambda: True,  # Always cancelled
        )

        assert cancelled is True
        mock_process.terminate.assert_called()
        mock_process.kill.assert_called()


class TestStreamProcessOutput:
    """Tests for stream_process_output function."""

    def test_stream_output_basic(self):
        """Test basic streaming of process output."""
        mock_process = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()

        # Simulate process finishing immediately
        mock_process.poll.side_effect = [None, 0]  # First check running, second done
        mock_process.stdout = mock_stdout
        mock_process.stderr = mock_stderr
        mock_stdout.fileno.return_value = 1
        mock_stdout.read.side_effect = ["line1\nline2\n", ""]
        mock_stderr.read.return_value = ""

        lines_received = []

        def on_line(line):
            lines_received.append(line)

        with patch("src.core.scanner_base.select.select", return_value=([1], [], [])):
            _stdout, _stderr, cancelled = stream_process_output(
                mock_process, lambda: False, on_line
            )

        assert cancelled is False
        assert "line1" in lines_received
        assert "line2" in lines_received

    def test_stream_output_cancellation(self):
        """Test streaming stops on cancellation."""
        mock_process = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()

        mock_process.poll.return_value = None  # Process still running
        mock_process.stdout = mock_stdout
        mock_process.stderr = mock_stderr
        mock_stdout.fileno.return_value = 1
        mock_process.communicate.return_value = ("remaining", "")

        lines_received = []
        cancel_flag = True  # Start cancelled

        with patch("src.core.scanner_base.select.select", return_value=([], [], [])):
            _stdout, _stderr, cancelled = stream_process_output(
                mock_process, lambda: cancel_flag, lambda ln: lines_received.append(ln)
            )

        assert cancelled is True
        mock_process.terminate.assert_called()

    def test_stream_output_without_pipes_fallback(self):
        """Test fallback when stdout/stderr pipes not available."""
        mock_process = MagicMock()
        mock_process.stdout = None
        mock_process.stderr = None
        mock_process.communicate.return_value = ("output", "error")

        with patch(
            "src.core.scanner_base.communicate_with_cancel_check",
            return_value=("output", "error", False),
        ) as mock_comm:
            stdout, stderr, cancelled = stream_process_output(
                mock_process, lambda: False, lambda line: None
            )

        mock_comm.assert_called_once()
        assert stdout == "output"
        assert stderr == "error"

    def test_stream_output_handles_os_error(self):
        """Test graceful handling of OSError during streaming."""
        mock_process = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()

        mock_process.poll.return_value = None
        mock_process.stdout = mock_stdout
        mock_process.stderr = mock_stderr
        mock_stdout.fileno.return_value = 1
        mock_process.communicate.return_value = ("final", "")

        with patch(
            "src.core.scanner_base.select.select",
            side_effect=OSError("IO Error"),
        ):
            _stdout, _stderr, cancelled = stream_process_output(
                mock_process, lambda: False, lambda _: None
            )

        # Should recover gracefully
        assert cancelled is False
        assert _stdout == "final"

    def test_stream_output_line_callback_called_for_each_line(self):
        """Test that on_line callback is called for each complete line."""
        mock_process = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()

        mock_process.poll.side_effect = [None, None, 0]
        mock_process.stdout = mock_stdout
        mock_process.stderr = mock_stderr
        mock_stdout.fileno.return_value = 1

        # Simulate chunked output
        mock_stdout.read.side_effect = [
            "/path/file1.txt: OK\n/path/file2.txt: OK\n",
            "/path/file3.txt: FOUND\n",
            "",
        ]
        mock_stderr.read.return_value = ""

        lines = []

        def on_line(line):
            lines.append(line)

        with patch("src.core.scanner_base.select.select", return_value=([1], [], [])):
            _stdout, _stderr, _cancelled = stream_process_output(
                mock_process, lambda: False, on_line
            )

        assert "/path/file1.txt: OK" in lines
        assert "/path/file2.txt: OK" in lines
        assert "/path/file3.txt: FOUND" in lines


class TestCleanupProcess:
    """Tests for cleanup_process function."""

    def test_cleanup_none_process(self):
        """Test cleanup_process handles None gracefully."""
        # Should not raise
        cleanup_process(None)

    def test_cleanup_already_finished_process(self):
        """Test cleanup of already finished process."""
        mock_process = MagicMock()
        mock_process.poll.return_value = 0  # Already finished

        cleanup_process(mock_process)

        mock_process.kill.assert_not_called()

    def test_cleanup_running_process(self):
        """Test cleanup kills running process."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Still running
        mock_process.wait.return_value = None

        cleanup_process(mock_process)

        mock_process.kill.assert_called_once()
        mock_process.wait.assert_called_once()

    def test_cleanup_handles_os_error(self):
        """Test cleanup handles OSError gracefully."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.kill.side_effect = OSError("No such process")

        # Should not raise
        cleanup_process(mock_process)

    def test_cleanup_handles_process_lookup_error(self):
        """Test cleanup handles ProcessLookupError gracefully."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.kill.side_effect = ProcessLookupError("No such process")

        # Should not raise
        cleanup_process(mock_process)


class TestTerminateProcessGracefully:
    """Tests for terminate_process_gracefully function."""

    def test_terminate_none_process(self):
        """Test terminate handles None gracefully."""
        # Should not raise
        terminate_process_gracefully(None)

    def test_terminate_graceful_success(self):
        """Test process terminates gracefully with SIGTERM."""
        mock_process = MagicMock()
        mock_process.wait.return_value = None  # Terminates within timeout

        terminate_process_gracefully(mock_process)

        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_not_called()

    def test_terminate_escalates_to_kill(self):
        """Test process escalates to SIGKILL when SIGTERM times out."""
        mock_process = MagicMock()
        mock_process.wait.side_effect = [
            subprocess.TimeoutExpired("cmd", TERMINATE_GRACE_TIMEOUT),
            None,
        ]

        terminate_process_gracefully(mock_process)

        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()

    def test_terminate_handles_already_gone_on_terminate(self):
        """Test handling when process exits before SIGTERM."""
        mock_process = MagicMock()
        mock_process.terminate.side_effect = ProcessLookupError("No such process")

        # Should not raise
        terminate_process_gracefully(mock_process)

    def test_terminate_handles_os_error_on_kill(self):
        """Test handling OSError during SIGKILL."""
        mock_process = MagicMock()
        mock_process.wait.side_effect = subprocess.TimeoutExpired("cmd", 5)
        mock_process.kill.side_effect = OSError("Error")

        # Should not raise
        terminate_process_gracefully(mock_process)


class TestCreateErrorResult:
    """Tests for create_error_result function."""

    def test_create_error_result_basic(self):
        """Test creating a basic error result."""
        result = create_error_result("/path/to/scan", "ClamAV not found")

        assert result.status == ScanStatus.ERROR
        assert result.path == "/path/to/scan"
        assert result.error_message == "ClamAV not found"
        assert result.exit_code == -1
        assert result.infected_files == []
        assert result.threat_details == []

    def test_create_error_result_with_stderr(self):
        """Test error result includes stderr."""
        result = create_error_result("/path/to/scan", "Command failed", stderr="Permission denied")

        assert result.stderr == "Permission denied"

    def test_create_error_result_stderr_defaults_to_error_message(self):
        """Test stderr defaults to error message when not provided."""
        result = create_error_result("/path/to/scan", "Some error")

        assert result.stderr == "Some error"


class TestCreateCancelledResult:
    """Tests for create_cancelled_result function."""

    def test_create_cancelled_result_basic(self):
        """Test creating a basic cancelled result."""
        result = create_cancelled_result("/path/to/scan")

        assert result.status == ScanStatus.CANCELLED
        assert result.path == "/path/to/scan"
        assert result.error_message == "Scan cancelled by user"
        assert result.infected_files == []
        assert result.threat_details == []

    def test_create_cancelled_result_with_partial_progress(self):
        """Test cancelled result preserves partial scan progress."""
        result = create_cancelled_result(
            "/path/to/scan",
            stdout="Partial output",
            stderr="",
            exit_code=-15,
            scanned_files=50,
            scanned_dirs=10,
        )

        assert result.stdout == "Partial output"
        assert result.exit_code == -15
        assert result.scanned_files == 50
        assert result.scanned_dirs == 10


class TestConstants:
    """Tests for module constants."""

    def test_timeout_constants_are_reasonable(self):
        """Test timeout constants have reasonable values."""
        assert TERMINATE_GRACE_TIMEOUT > 0
        assert TERMINATE_GRACE_TIMEOUT <= 10  # Not too long

        assert KILL_WAIT_TIMEOUT > 0
        assert KILL_WAIT_TIMEOUT <= 5  # Not too long

        assert STREAM_POLL_TIMEOUT > 0
        assert STREAM_POLL_TIMEOUT <= 1  # Should be responsive
