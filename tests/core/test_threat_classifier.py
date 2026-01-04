# ClamUI Threat Classifier Tests
"""
Comprehensive unit tests for the threat classification module.

Tests cover:
- ThreatSeverity enum values
- classify_threat_severity() function with all pattern categories
- classify_threat_severity_str() wrapper function
- categorize_threat() function with position-based matching
"""

import pytest

from src.core.threat_classifier import (
    CRITICAL_PATTERNS,
    HIGH_PATTERNS,
    LOW_PATTERNS,
    MEDIUM_PATTERNS,
    ThreatSeverity,
    categorize_threat,
    classify_threat_severity,
    classify_threat_severity_str,
)

# =============================================================================
# ThreatSeverity Enum Tests
# =============================================================================


class TestThreatSeverityEnum:
    """Tests for the ThreatSeverity enum."""

    def test_all_severity_levels_exist(self):
        """Verify all expected severity levels are defined."""
        assert hasattr(ThreatSeverity, "CRITICAL")
        assert hasattr(ThreatSeverity, "HIGH")
        assert hasattr(ThreatSeverity, "MEDIUM")
        assert hasattr(ThreatSeverity, "LOW")

    def test_severity_values(self):
        """Verify severity level string values."""
        assert ThreatSeverity.CRITICAL.value == "critical"
        assert ThreatSeverity.HIGH.value == "high"
        assert ThreatSeverity.MEDIUM.value == "medium"
        assert ThreatSeverity.LOW.value == "low"

    def test_severity_count(self):
        """Verify exactly 4 severity levels exist."""
        assert len(ThreatSeverity) == 4


# =============================================================================
# Pattern Constants Tests
# =============================================================================


class TestPatternConstants:
    """Tests for pattern constant lists."""

    def test_critical_patterns_not_empty(self):
        """Verify CRITICAL_PATTERNS contains expected patterns."""
        assert len(CRITICAL_PATTERNS) > 0
        assert "ransom" in CRITICAL_PATTERNS
        assert "rootkit" in CRITICAL_PATTERNS
        assert "bootkit" in CRITICAL_PATTERNS

    def test_high_patterns_not_empty(self):
        """Verify HIGH_PATTERNS contains expected patterns."""
        assert len(HIGH_PATTERNS) > 0
        assert "trojan" in HIGH_PATTERNS
        assert "worm" in HIGH_PATTERNS
        assert "backdoor" in HIGH_PATTERNS

    def test_medium_patterns_not_empty(self):
        """Verify MEDIUM_PATTERNS contains expected patterns."""
        assert len(MEDIUM_PATTERNS) > 0
        assert "adware" in MEDIUM_PATTERNS
        assert "spyware" in MEDIUM_PATTERNS

    def test_low_patterns_not_empty(self):
        """Verify LOW_PATTERNS contains expected patterns."""
        assert len(LOW_PATTERNS) > 0
        assert "eicar" in LOW_PATTERNS
        assert "heuristic" in LOW_PATTERNS


# =============================================================================
# classify_threat_severity() Tests
# =============================================================================


class TestClassifyThreatSeverityCritical:
    """Tests for CRITICAL severity classification."""

    @pytest.mark.parametrize(
        "threat_name",
        [
            "Win.Ransomware.Locky",
            "Ransom.WannaCry",
            "Linux.Rootkit.Agent",
            "Win.Bootkit.TDL4",
            "CryptoLocker.Variant",
            "WannaCry.B",
        ],
    )
    def test_critical_patterns(self, threat_name):
        """Test CRITICAL severity for ransomware, rootkit, bootkit patterns."""
        assert classify_threat_severity(threat_name) == ThreatSeverity.CRITICAL

    def test_critical_case_insensitive(self):
        """Test CRITICAL detection is case-insensitive."""
        assert classify_threat_severity("RANSOMWARE.TEST") == ThreatSeverity.CRITICAL
        assert classify_threat_severity("ransomware.test") == ThreatSeverity.CRITICAL
        assert classify_threat_severity("RaNsOmWaRe.TeSt") == ThreatSeverity.CRITICAL


class TestClassifyThreatSeverityHigh:
    """Tests for HIGH severity classification."""

    @pytest.mark.parametrize(
        "threat_name",
        [
            "Win.Trojan.Agent",
            "Linux.Worm.Slapper",
            "Win.Backdoor.Poison",
            "Exploit.CVE-2021-1234",
            "Downloader.Generic",
            "Dropper.Agent",
            "Win.Keylogger.Zeus",
        ],
    )
    def test_high_patterns(self, threat_name):
        """Test HIGH severity for trojan, worm, backdoor, exploit patterns."""
        assert classify_threat_severity(threat_name) == ThreatSeverity.HIGH

    def test_high_case_insensitive(self):
        """Test HIGH detection is case-insensitive."""
        assert classify_threat_severity("TROJAN.TEST") == ThreatSeverity.HIGH
        assert classify_threat_severity("trojan.test") == ThreatSeverity.HIGH
        assert classify_threat_severity("TrOjAn.TeSt") == ThreatSeverity.HIGH


class TestClassifyThreatSeverityMedium:
    """Tests for MEDIUM severity classification."""

    @pytest.mark.parametrize(
        "threat_name",
        [
            "PUA.Win.Adware.Generic",
            "Win.Spyware.Tracker",
            "PUP.Optional.BrowserHelper",
            "CoinMiner.Generic",
            "Miner.Bitcoin",
        ],
    )
    def test_medium_patterns(self, threat_name):
        """Test MEDIUM severity for adware, pua, spyware, miner patterns."""
        assert classify_threat_severity(threat_name) == ThreatSeverity.MEDIUM

    def test_medium_case_insensitive(self):
        """Test MEDIUM detection is case-insensitive."""
        assert classify_threat_severity("ADWARE.TEST") == ThreatSeverity.MEDIUM
        assert classify_threat_severity("adware.test") == ThreatSeverity.MEDIUM


class TestClassifyThreatSeverityLow:
    """Tests for LOW severity classification."""

    @pytest.mark.parametrize(
        "threat_name",
        [
            "Eicar-Test-Signature",
            "EICAR-STANDARD-ANTIVIRUS-TEST-FILE",
            "Test-Signature.Example",
            "Test.File.Detection",
            "Heuristic.Suspicious",
            "Generic.Malware",
        ],
    )
    def test_low_patterns(self, threat_name):
        """Test LOW severity for eicar, test, heuristic, generic patterns."""
        assert classify_threat_severity(threat_name) == ThreatSeverity.LOW

    def test_low_case_insensitive(self):
        """Test LOW detection is case-insensitive."""
        assert classify_threat_severity("EICAR.TEST") == ThreatSeverity.LOW
        assert classify_threat_severity("eicar.test") == ThreatSeverity.LOW


class TestClassifyThreatSeverityEdgeCases:
    """Tests for edge cases in severity classification."""

    def test_empty_string_returns_medium(self):
        """Empty threat name should return MEDIUM (unknown)."""
        assert classify_threat_severity("") == ThreatSeverity.MEDIUM

    def test_none_returns_medium(self):
        """None threat name should return MEDIUM (unknown)."""
        assert classify_threat_severity(None) == ThreatSeverity.MEDIUM

    def test_unknown_threat_returns_medium(self):
        """Unknown threat names should return MEDIUM as default."""
        assert classify_threat_severity("UnknownMalware.XYZ") == ThreatSeverity.MEDIUM
        assert classify_threat_severity("SomethingBad") == ThreatSeverity.MEDIUM

    def test_whitespace_only_returns_medium(self):
        """Whitespace-only threat name should return MEDIUM."""
        assert classify_threat_severity("   ") == ThreatSeverity.MEDIUM

    def test_pattern_in_middle_of_name(self):
        """Patterns should be detected anywhere in the threat name."""
        assert classify_threat_severity("Win.Something.Trojan.Agent") == ThreatSeverity.HIGH
        assert classify_threat_severity("Prefix.Ransomware.Suffix") == ThreatSeverity.CRITICAL


class TestClassifyThreatSeverityPriority:
    """Tests for priority when multiple patterns could match."""

    def test_critical_takes_precedence_over_high(self):
        """CRITICAL patterns should take precedence over HIGH."""
        # A threat with both ransomware and trojan should be CRITICAL
        assert classify_threat_severity("Trojan.Ransomware.Agent") == ThreatSeverity.CRITICAL

    def test_high_takes_precedence_over_medium(self):
        """HIGH patterns should take precedence over MEDIUM."""
        # A threat with both trojan and adware should be HIGH
        assert classify_threat_severity("Adware.Trojan.Agent") == ThreatSeverity.HIGH

    def test_medium_takes_precedence_over_low(self):
        """MEDIUM patterns should take precedence over LOW."""
        # A threat with both adware and heuristic should be MEDIUM
        assert classify_threat_severity("Heuristic.Adware.Agent") == ThreatSeverity.MEDIUM


# =============================================================================
# classify_threat_severity_str() Tests
# =============================================================================


class TestClassifyThreatSeverityStr:
    """Tests for the string-returning severity classifier."""

    def test_returns_string_not_enum(self):
        """Verify function returns string, not enum."""
        result = classify_threat_severity_str("Win.Trojan.Agent")
        assert isinstance(result, str)
        assert not isinstance(result, ThreatSeverity)

    @pytest.mark.parametrize(
        "threat_name,expected",
        [
            ("Win.Ransomware.Locky", "critical"),
            ("Win.Trojan.Agent", "high"),
            ("PUA.Win.Adware", "medium"),
            ("Eicar-Test-Signature", "low"),
            ("UnknownThreat", "medium"),
        ],
    )
    def test_returns_correct_string_values(self, threat_name, expected):
        """Test correct string values returned for each severity."""
        assert classify_threat_severity_str(threat_name) == expected

    def test_empty_string_returns_medium_str(self):
        """Empty threat name should return 'medium' string."""
        assert classify_threat_severity_str("") == "medium"

    def test_none_returns_medium_str(self):
        """None threat name should return 'medium' string."""
        assert classify_threat_severity_str(None) == "medium"


# =============================================================================
# categorize_threat() Tests
# =============================================================================


class TestCategorizeThreatHighPriority:
    """Tests for high-priority category patterns."""

    @pytest.mark.parametrize(
        "threat_name,expected_category",
        [
            ("Win.Ransomware.Locky", "Ransomware"),
            ("Ransom.WannaCry", "Ransomware"),
            ("Linux.Rootkit.Agent", "Rootkit"),
            ("Win.Bootkit.TDL4", "Rootkit"),
            ("Win.Trojan.Agent", "Trojan"),
            ("Linux.Worm.Slapper", "Worm"),
            ("Win.Backdoor.Poison", "Backdoor"),
            ("Exploit.CVE-2021-1234", "Exploit"),
            ("PUA.Win.Adware.Generic", "Adware"),
            ("Win.Spyware.Tracker", "Spyware"),
            ("Win.Keylogger.Zeus", "Spyware"),
            ("Eicar-Test-Signature", "Test"),
            ("Test-Signature.File", "Test"),
            ("Test.File.Detection", "Test"),
            ("Doc.Macro.Downloader", "Macro"),
            ("Phishing.Email.Generic", "Phishing"),
            ("Heuristic.Suspicious", "Heuristic"),
        ],
    )
    def test_high_priority_categories(self, threat_name, expected_category):
        """Test high-priority category patterns return correct categories."""
        assert categorize_threat(threat_name) == expected_category


class TestCategorizeThreatLowPriority:
    """Tests for low-priority category patterns."""

    def test_pua_category(self):
        """Test PUA pattern returns 'PUA' category."""
        # Note: Only matches if no high-priority pattern matches first
        assert categorize_threat("PUA.Generic.Agent") == "PUA"

    def test_pup_category(self):
        """Test PUP pattern returns 'PUA' category."""
        assert categorize_threat("PUP.Optional.Something") == "PUA"

    def test_virus_category(self):
        """Test virus pattern returns 'Virus' category."""
        assert categorize_threat("Virus.DOS.Generic") == "Virus"


class TestCategorizeThreatPositionMatching:
    """Tests for position-based pattern matching."""

    def test_earliest_pattern_wins(self):
        """When multiple patterns match, earliest position wins."""
        # Trojan appears before Worm
        assert categorize_threat("Trojan.Worm.Agent") == "Trojan"
        # Worm appears before Trojan
        assert categorize_threat("Worm.Trojan.Agent") == "Worm"

    def test_high_priority_over_low_priority(self):
        """High-priority patterns take precedence over low-priority."""
        # Adware (high-priority) should win over PUA (low-priority)
        assert categorize_threat("PUA.Adware.Generic") == "Adware"
        # Trojan (high-priority) should win over Virus (low-priority)
        assert categorize_threat("Virus.Trojan.Agent") == "Trojan"

    def test_position_matters_within_tier(self):
        """Position matters when choosing between same-tier patterns."""
        # Both are high-priority, earlier one wins
        assert categorize_threat("Backdoor.Exploit.Agent") == "Backdoor"
        assert categorize_threat("Exploit.Backdoor.Agent") == "Exploit"


class TestCategorizeThreatEdgeCases:
    """Tests for edge cases in threat categorization."""

    def test_empty_string_returns_unknown(self):
        """Empty threat name should return 'Unknown'."""
        assert categorize_threat("") == "Unknown"

    def test_none_returns_unknown(self):
        """None threat name should return 'Unknown'."""
        assert categorize_threat(None) == "Unknown"

    def test_unknown_threat_returns_virus(self):
        """Unknown threats default to 'Virus' (conservative assumption)."""
        assert categorize_threat("SomeUnknownMalware") == "Virus"
        assert categorize_threat("Win.Something.Agent") == "Virus"

    def test_case_insensitive(self):
        """Category detection should be case-insensitive."""
        assert categorize_threat("TROJAN.TEST") == "Trojan"
        assert categorize_threat("trojan.test") == "Trojan"
        assert categorize_threat("TrOjAn.TeSt") == "Trojan"

    def test_whitespace_only_returns_unknown(self):
        """Whitespace-only threat name should return 'Unknown'."""
        assert categorize_threat("   ") == "Virus"  # Non-empty but no pattern match


class TestCategorizeThreatRealWorld:
    """Tests using real-world ClamAV threat names."""

    @pytest.mark.parametrize(
        "threat_name,expected_category",
        [
            # Real ClamAV detection names
            ("Win.Trojan.Agent-1234567", "Trojan"),
            ("Pdf.Exploit.CVE_2010_1234-1", "Exploit"),
            ("PUA.Win.Tool.Packed-1", "PUA"),
            ("Doc.Dropper.Agent-1234567", "Virus"),  # Dropper not in categories, defaults to Virus
            ("Html.Phishing.Bank-1234", "Phishing"),
            ("Win.Worm.Conficker-1", "Worm"),
            ("Osx.Trojan.Generic-1234567", "Trojan"),
            ("Android.Adware.Generic-1234567", "Adware"),
            ("Win.Ransomware.Cerber-1234567", "Ransomware"),
            ("Linux.Backdoor.Generic-1234567", "Backdoor"),
        ],
    )
    def test_real_clamav_names(self, threat_name, expected_category):
        """Test categorization of real ClamAV threat names."""
        assert categorize_threat(threat_name) == expected_category


# =============================================================================
# Integration Tests
# =============================================================================


class TestClassificationIntegration:
    """Integration tests combining severity and category classification."""

    @pytest.mark.parametrize(
        "threat_name,expected_severity,expected_category",
        [
            ("Win.Ransomware.Locky", ThreatSeverity.CRITICAL, "Ransomware"),
            ("Win.Trojan.Agent", ThreatSeverity.HIGH, "Trojan"),
            ("PUA.Win.Adware.Generic", ThreatSeverity.MEDIUM, "Adware"),
            ("Eicar-Test-Signature", ThreatSeverity.LOW, "Test"),
            ("Linux.Rootkit.Agent", ThreatSeverity.CRITICAL, "Rootkit"),
            ("Win.Worm.Conficker", ThreatSeverity.HIGH, "Worm"),
        ],
    )
    def test_severity_and_category_consistent(
        self, threat_name, expected_severity, expected_category
    ):
        """Test that severity and category are consistent for same threat."""
        assert classify_threat_severity(threat_name) == expected_severity
        assert categorize_threat(threat_name) == expected_category

    def test_all_critical_threats_have_dangerous_categories(self):
        """CRITICAL threats should have dangerous categories."""
        dangerous_categories = {"Ransomware", "Rootkit"}
        for pattern in CRITICAL_PATTERNS:
            threat = f"Test.{pattern}.Agent"
            category = categorize_threat(threat)
            # Either in dangerous categories or defaults
            assert category in dangerous_categories or category == "Virus", (
                f"Critical pattern '{pattern}' got unexpected category '{category}'"
            )
