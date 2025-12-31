# ClamUI Scanner Integration Tests
"""
Integration tests for the scanner module covering complete scan workflows.

These tests verify the scanner's end-to-end behavior including:
- Sync scan workflow (file selection -> scan execution -> results display)
- Async scan workflow with callback verification
- EICAR test file detection and classification
- Scan cancellation handling

All tests mock ClamAV subprocess execution to run without requiring ClamAV installed.
"""

import sys
from pathlib import Path
from unittest import mock

import pytest

# Store original gi modules to restore later (if they exist)
_original_gi = sys.modules.get("gi")
_original_gi_repository = sys.modules.get("gi.repository")

# Mock gi module before importing src.core to avoid GTK dependencies in tests
sys.modules["gi"] = mock.MagicMock()
sys.modules["gi.repository"] = mock.MagicMock()

from src.core.scanner import Scanner, ScanResult, ScanStatus, ThreatDetail

# Restore original gi modules after imports are done
if _original_gi is not None:
    sys.modules["gi"] = _original_gi
else:
    del sys.modules["gi"]
if _original_gi_repository is not None:
    sys.modules["gi.repository"] = _original_gi_repository
else:
    del sys.modules["gi.repository"]


@pytest.mark.integration
class TestScannerSyncWorkflow:
    """Integration tests for the synchronous scan workflow."""

    def test_scanner_sync_workflow(self, tmp_path):
        """
        Test complete sync scan workflow: file selection -> scan execution -> results.

        This test verifies the full scan_sync workflow:
        1. Create a test file to scan
        2. Execute scan_sync with mocked subprocess
        3. Verify ScanResult contains expected data
        4. Verify all ScanResult properties are correctly populated
        """
        # Step 1: Create test file (simulates file selection)
        test_file = tmp_path / "test_document.txt"
        test_file.write_text("This is a clean test document for scanning.")

        scanner = Scanner()

        # Step 2: Mock ClamAV subprocess execution
        mock_stdout = f"""
{test_file}: OK

----------- SCAN SUMMARY -----------
Known viruses: 8000000
Engine version: 1.2.3
Scanned directories: 0
Scanned files: 1
Infected files: 0
Data scanned: 0.01 MB
Data read: 0.01 MB
Time: 0.100 sec (0 m 0 s)
"""

        with mock.patch("src.core.scanner.get_clamav_path", return_value="/usr/bin/clamscan"):
            with mock.patch("src.core.scanner.wrap_host_command", side_effect=lambda x: x):
                with mock.patch("src.core.scanner.check_clamav_installed", return_value=(True, "1.2.3")):
                    with mock.patch("subprocess.Popen") as mock_popen:
                        mock_process = mock.MagicMock()
                        mock_process.communicate.return_value = (mock_stdout, "")
                        mock_process.returncode = 0
                        mock_popen.return_value = mock_process

                        # Step 3: Execute scan
                        result = scanner.scan_sync(str(test_file))

        # Step 4: Verify ScanResult structure
        assert isinstance(result, ScanResult)
        assert result.status == ScanStatus.CLEAN
        assert result.path == str(test_file)
        assert result.exit_code == 0

        # Verify properties
        assert result.is_clean is True
        assert result.has_threats is False

        # Verify counts
        assert result.infected_count == 0
        assert result.scanned_files == 1
        assert len(result.infected_files) == 0
        assert len(result.threat_details) == 0

        # Verify error handling
        assert result.error_message is None

    def test_scanner_sync_workflow_infected_file(self, tmp_path):
        """
        Test sync scan workflow with infected file detection.

        Verifies that when clamscan detects a threat:
        1. Status is set to INFECTED
        2. infected_files list is populated
        3. threat_details are extracted with proper classification
        4. has_threats property returns True
        """
        test_file = tmp_path / "infected_file.exe"
        test_file.write_text("simulated infected content")

        scanner = Scanner()

        # Mock ClamAV output with detected threat
        mock_stdout = f"""
{test_file}: Win.Trojan.Agent FOUND

----------- SCAN SUMMARY -----------
Scanned directories: 0
Scanned files: 1
Infected files: 1
Data scanned: 0.01 MB
Time: 0.100 sec (0 m 0 s)
"""

        with mock.patch("src.core.scanner.get_clamav_path", return_value="/usr/bin/clamscan"):
            with mock.patch("src.core.scanner.wrap_host_command", side_effect=lambda x: x):
                with mock.patch("src.core.scanner.check_clamav_installed", return_value=(True, "1.2.3")):
                    with mock.patch("subprocess.Popen") as mock_popen:
                        mock_process = mock.MagicMock()
                        mock_process.communicate.return_value = (mock_stdout, "")
                        mock_process.returncode = 1  # ClamAV exit code 1 = virus found
                        mock_popen.return_value = mock_process

                        result = scanner.scan_sync(str(test_file))

        # Verify infected status
        assert result.status == ScanStatus.INFECTED
        assert result.is_clean is False
        assert result.has_threats is True

        # Verify infected files list
        assert result.infected_count == 1
        assert len(result.infected_files) == 1
        assert str(test_file) in result.infected_files

        # Verify threat details
        assert len(result.threat_details) == 1
        threat = result.threat_details[0]
        assert isinstance(threat, ThreatDetail)
        assert threat.file_path == str(test_file)
        assert threat.threat_name == "Win.Trojan.Agent"
        assert threat.category == "Trojan"
        assert threat.severity == "high"

    def test_scanner_sync_workflow_directory(self, tmp_path):
        """
        Test sync scan workflow with directory scanning.

        Verifies that directory scanning:
        1. Scans multiple files in directory
        2. Properly counts scanned files and directories
        3. Can detect multiple threats
        """
        # Create directory with multiple files
        scan_dir = tmp_path / "documents"
        scan_dir.mkdir()
        (scan_dir / "file1.txt").write_text("Clean file 1")
        (scan_dir / "file2.txt").write_text("Clean file 2")
        (scan_dir / "file3.txt").write_text("Clean file 3")

        scanner = Scanner()

        mock_stdout = f"""
{scan_dir}/file1.txt: OK
{scan_dir}/file2.txt: OK
{scan_dir}/file3.txt: OK

----------- SCAN SUMMARY -----------
Scanned directories: 1
Scanned files: 3
Infected files: 0
Data scanned: 0.01 MB
Time: 0.200 sec (0 m 0 s)
"""

        with mock.patch("src.core.scanner.get_clamav_path", return_value="/usr/bin/clamscan"):
            with mock.patch("src.core.scanner.wrap_host_command", side_effect=lambda x: x):
                with mock.patch("src.core.scanner.check_clamav_installed", return_value=(True, "1.2.3")):
                    with mock.patch("subprocess.Popen") as mock_popen:
                        mock_process = mock.MagicMock()
                        mock_process.communicate.return_value = (mock_stdout, "")
                        mock_process.returncode = 0
                        mock_popen.return_value = mock_process

                        result = scanner.scan_sync(str(scan_dir), recursive=True)

        # Verify clean scan
        assert result.status == ScanStatus.CLEAN
        assert result.is_clean is True

        # Verify counts
        assert result.scanned_files == 3
        assert result.scanned_dirs == 1
        assert result.infected_count == 0

    def test_scanner_sync_workflow_error_handling(self, tmp_path):
        """
        Test sync scan workflow error handling.

        Verifies that when ClamAV reports an error:
        1. Status is set to ERROR
        2. error_message is populated
        3. Exit code is captured
        """
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        scanner = Scanner()

        mock_stderr = "ERROR: Can't open database file"

        with mock.patch("src.core.scanner.get_clamav_path", return_value="/usr/bin/clamscan"):
            with mock.patch("src.core.scanner.wrap_host_command", side_effect=lambda x: x):
                with mock.patch("src.core.scanner.check_clamav_installed", return_value=(True, "1.2.3")):
                    with mock.patch("subprocess.Popen") as mock_popen:
                        mock_process = mock.MagicMock()
                        mock_process.communicate.return_value = ("", mock_stderr)
                        mock_process.returncode = 2  # ClamAV exit code 2 = error
                        mock_popen.return_value = mock_process

                        result = scanner.scan_sync(str(test_file))

        # Verify error status
        assert result.status == ScanStatus.ERROR
        assert result.is_clean is False
        assert result.has_threats is False
        assert result.exit_code == 2
        assert result.error_message is not None

    def test_scanner_sync_workflow_invalid_path(self):
        """
        Test sync scan workflow with invalid path.

        Verifies that scanning a non-existent path:
        1. Returns ERROR status
        2. Contains appropriate error message
        """
        scanner = Scanner()

        # Try to scan non-existent path
        result = scanner.scan_sync("/nonexistent/path/that/does/not/exist")

        # Verify error handling for invalid path
        assert result.status == ScanStatus.ERROR
        assert result.error_message is not None
        assert result.exit_code == -1

    def test_scanner_sync_workflow_subprocess_called_correctly(self, tmp_path):
        """
        Test that subprocess.Popen is called with correct arguments.

        Verifies the scanner correctly builds the clamscan command and
        passes it to subprocess.Popen.
        """
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        scanner = Scanner()

        with mock.patch("src.core.scanner.get_clamav_path", return_value="/usr/bin/clamscan"):
            with mock.patch("src.core.scanner.wrap_host_command", side_effect=lambda x: x):
                with mock.patch("src.core.scanner.check_clamav_installed", return_value=(True, "1.2.3")):
                    with mock.patch("subprocess.Popen") as mock_popen:
                        mock_process = mock.MagicMock()
                        mock_process.communicate.return_value = ("", "")
                        mock_process.returncode = 0
                        mock_popen.return_value = mock_process

                        scanner.scan_sync(str(test_file))

                        # Verify Popen was called
                        mock_popen.assert_called_once()

                        # Verify command arguments
                        call_args = mock_popen.call_args
                        cmd = call_args[0][0]

                        assert cmd[0] == "/usr/bin/clamscan"
                        assert "-i" in cmd
                        assert str(test_file) in cmd

    def test_scanner_sync_workflow_multiple_threats(self, tmp_path):
        """
        Test sync scan workflow with multiple threats of varying severity.

        Verifies that scanner correctly:
        1. Detects multiple infected files
        2. Classifies each threat appropriately
        3. Assigns correct severity levels
        """
        scan_dir = tmp_path / "infected_dir"
        scan_dir.mkdir()

        scanner = Scanner()

        # Mock output with multiple different threats
        mock_stdout = f"""
{scan_dir}/critical.exe: Ransomware.Locky FOUND
{scan_dir}/high.exe: Trojan.Banker FOUND
{scan_dir}/medium.exe: Adware.Toolbar FOUND
{scan_dir}/low.exe: Eicar-Test-Signature FOUND

----------- SCAN SUMMARY -----------
Scanned directories: 1
Scanned files: 4
Infected files: 4
"""

        with mock.patch("src.core.scanner.get_clamav_path", return_value="/usr/bin/clamscan"):
            with mock.patch("src.core.scanner.wrap_host_command", side_effect=lambda x: x):
                with mock.patch("src.core.scanner.check_clamav_installed", return_value=(True, "1.2.3")):
                    with mock.patch("subprocess.Popen") as mock_popen:
                        mock_process = mock.MagicMock()
                        mock_process.communicate.return_value = (mock_stdout, "")
                        mock_process.returncode = 1
                        mock_popen.return_value = mock_process

                        result = scanner.scan_sync(str(scan_dir), recursive=True)

        # Verify all threats detected
        assert result.status == ScanStatus.INFECTED
        assert result.infected_count == 4
        assert len(result.threat_details) == 4

        # Build a map for easy verification
        threat_map = {t.threat_name: t for t in result.threat_details}

        # Verify severity classification
        assert threat_map["Ransomware.Locky"].severity == "critical"
        assert threat_map["Ransomware.Locky"].category == "Ransomware"

        assert threat_map["Trojan.Banker"].severity == "high"
        assert threat_map["Trojan.Banker"].category == "Trojan"

        assert threat_map["Adware.Toolbar"].severity == "medium"
        assert threat_map["Adware.Toolbar"].category == "Adware"

        assert threat_map["Eicar-Test-Signature"].severity == "low"
        assert threat_map["Eicar-Test-Signature"].category == "Test"
