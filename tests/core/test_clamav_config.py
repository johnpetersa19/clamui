# ClamUI ClamAV Config Tests
"""Unit tests for the ClamAV configuration module."""

import contextlib
import tempfile
from pathlib import Path

import pytest

from src.core.clamav_config import (
    ClamAVConfig,
    ClamAVConfigValue,
    parse_config,
)


class TestClamAVConfigValue:
    """Tests for the ClamAVConfigValue dataclass."""

    def test_create_default_values(self):
        """Test ClamAVConfigValue with default values."""
        config_value = ClamAVConfigValue(value="test")

        assert config_value.value == "test"
        assert config_value.comment is None
        assert config_value.line_number == 0

    def test_create_with_all_fields(self):
        """Test ClamAVConfigValue with all fields specified."""
        config_value = ClamAVConfigValue(
            value="/var/lib/clamav", comment="Database directory", line_number=5
        )

        assert config_value.value == "/var/lib/clamav"
        assert config_value.comment == "Database directory"
        assert config_value.line_number == 5


class TestClamAVConfig:
    """Tests for the ClamAVConfig dataclass."""

    def test_create_empty_config(self):
        """Test creating an empty ClamAVConfig."""
        config = ClamAVConfig(file_path=Path("/etc/clamav/freshclam.conf"))

        assert config.file_path == Path("/etc/clamav/freshclam.conf")
        assert config.values == {}
        assert config.raw_lines == []

    def test_get_value_existing(self):
        """Test get_value for existing key."""
        config = ClamAVConfig(file_path=Path("/test"))
        config.values["DatabaseDirectory"] = [ClamAVConfigValue(value="/var/lib/clamav")]

        assert config.get_value("DatabaseDirectory") == "/var/lib/clamav"

    def test_get_value_missing(self):
        """Test get_value for missing key."""
        config = ClamAVConfig(file_path=Path("/test"))

        assert config.get_value("NonExistent") is None

    def test_get_values_multiple(self):
        """Test get_values for multi-value option."""
        config = ClamAVConfig(file_path=Path("/test"))
        config.values["DatabaseMirror"] = [
            ClamAVConfigValue(value="database.clamav.net"),
            ClamAVConfigValue(value="db.local.clamav.net"),
        ]

        values = config.get_values("DatabaseMirror")
        assert len(values) == 2
        assert "database.clamav.net" in values
        assert "db.local.clamav.net" in values

    def test_set_value(self):
        """Test set_value replaces existing values."""
        config = ClamAVConfig(file_path=Path("/test"))
        config.values["LogVerbose"] = [ClamAVConfigValue(value="no")]

        config.set_value("LogVerbose", "yes")

        assert config.get_value("LogVerbose") == "yes"
        assert len(config.values["LogVerbose"]) == 1

    def test_add_value(self):
        """Test add_value appends to existing values."""
        config = ClamAVConfig(file_path=Path("/test"))
        config.add_value("DatabaseMirror", "mirror1.clamav.net")
        config.add_value("DatabaseMirror", "mirror2.clamav.net")

        values = config.get_values("DatabaseMirror")
        assert len(values) == 2

    def test_has_key_true(self):
        """Test has_key returns True for existing key."""
        config = ClamAVConfig(file_path=Path("/test"))
        config.set_value("LogVerbose", "yes")

        assert config.has_key("LogVerbose") is True

    def test_has_key_false(self):
        """Test has_key returns False for missing key."""
        config = ClamAVConfig(file_path=Path("/test"))

        assert config.has_key("NonExistent") is False

    def test_get_bool_yes(self):
        """Test get_bool returns True for 'yes'."""
        config = ClamAVConfig(file_path=Path("/test"))
        config.set_value("LogVerbose", "yes")

        assert config.get_bool("LogVerbose") is True

    def test_get_bool_no(self):
        """Test get_bool returns False for 'no'."""
        config = ClamAVConfig(file_path=Path("/test"))
        config.set_value("LogVerbose", "no")

        assert config.get_bool("LogVerbose") is False

    def test_get_bool_missing(self):
        """Test get_bool returns None for missing key."""
        config = ClamAVConfig(file_path=Path("/test"))

        assert config.get_bool("LogVerbose") is None

    def test_get_int_valid(self):
        """Test get_int returns integer for valid value."""
        config = ClamAVConfig(file_path=Path("/test"))
        config.set_value("Checks", "24")

        assert config.get_int("Checks") == 24

    def test_get_int_invalid(self):
        """Test get_int returns None for non-integer value."""
        config = ClamAVConfig(file_path=Path("/test"))
        config.set_value("Checks", "invalid")

        assert config.get_int("Checks") is None


class TestParseConfig:
    """Tests for the parse_config function."""

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file for testing."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".conf", delete=False, encoding="utf-8"
        ) as f:
            f.write("# ClamAV configuration\n")
            f.write("DatabaseDirectory /var/lib/clamav\n")
            f.write("LogVerbose yes\n")
            f.write("\n")
            f.write("Checks 24\n")
            temp_path = f.name
        yield temp_path
        with contextlib.suppress(OSError, PermissionError):
            Path(temp_path).unlink(missing_ok=True)

    def test_parse_valid_config(self, temp_config_file):
        """Test parsing a valid config file."""
        config, error = parse_config(temp_config_file)

        assert error is None
        assert config is not None
        assert config.get_value("DatabaseDirectory") == "/var/lib/clamav"
        assert config.get_value("LogVerbose") == "yes"
        assert config.get_value("Checks") == "24"

    def test_parse_empty_path(self):
        """Test parse_config with empty path."""
        config, error = parse_config("")

        assert config is None
        assert "no configuration file path" in error.lower()

    def test_parse_nonexistent_file(self):
        """Test parse_config with non-existent file."""
        config, error = parse_config("/nonexistent/config.conf")

        assert config is None
        assert "not found" in error.lower()

    def test_parse_directory_fails(self, tmp_path):
        """Test parse_config fails for directory path."""
        config, error = parse_config(str(tmp_path))

        assert config is None
        assert "not a file" in error.lower()

    def test_parse_preserves_raw_lines(self, temp_config_file):
        """Test that parse_config preserves raw lines."""
        config, error = parse_config(temp_config_file)

        assert error is None
        assert len(config.raw_lines) > 0
