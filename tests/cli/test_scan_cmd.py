# ClamUI Scan Command Tests
"""
Tests for the scan CLI command's text output.

Focuses on the security-sensitive path where filesystem-derived strings
(threat file paths, quarantine-failure paths/errors) are printed to the
terminal and must be sanitized to prevent ANSI/control-sequence injection.
"""

from src.cli.scan_cmd import _print_text_output
from src.core.scanner_types import ScanResult, ScanStatus, ThreatDetail


def _infected_result(threats: list[ThreatDetail]) -> ScanResult:
    """Build a minimal INFECTED ScanResult carrying the given threats."""
    return ScanResult(
        status=ScanStatus.INFECTED,
        path="/scan/target",
        stdout="",
        stderr="",
        exit_code=1,
        infected_files=[t.file_path for t in threats],
        scanned_files=1,
        scanned_dirs=0,
        infected_count=len(threats),
        error_message=None,
        threat_details=threats,
    )


class TestPrintTextOutputSanitization:
    """The text output must strip terminal escape sequences from paths."""

    def test_threat_file_path_is_sanitized(self, capsys):
        """A malicious file path with ANSI escapes must not reach the terminal raw."""
        threat = ThreatDetail(
            file_path="\x1b[31mevil\x1b[0m/payload",
            threat_name="Test.Threat",
            category="malware",
            severity="high",
        )
        result = _infected_result([threat])

        _print_text_output([result], duration=0.1, quarantine_info=None)

        captured = capsys.readouterr()
        assert "\x1b" not in captured.out
        assert "evil" in captured.out

    def test_quarantine_failure_path_is_sanitized(self, capsys):
        """Quarantine-failure path and error strings must also be sanitized."""
        threat = ThreatDetail(
            file_path="/clean/path",
            threat_name="Test.Threat",
            category="malware",
            severity="high",
        )
        result = _infected_result([threat])
        failures = [("\x1b[31mevil/file", "denied\x1b[2J")]

        _print_text_output([result], duration=0.1, quarantine_info=(0, failures))

        captured = capsys.readouterr()
        assert "\x1b" not in captured.out
        assert "evil/file" in captured.out
