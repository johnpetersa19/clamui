# ClamUI TrayIndicator Tests
"""Unit tests for the tray_indicator module.

The tray_indicator module provides availability checks for the tray system.
The actual tray functionality is implemented in tray_service.py (D-Bus SNI)
and managed by tray_manager.py.
"""


class TestTrayIndicatorModuleFunctions:
    """Tests for module-level functions."""

    def test_is_available_returns_boolean(self):
        """Test is_available returns a boolean value."""
        from src.ui import tray_indicator

        result = tray_indicator.is_available()
        assert isinstance(result, bool)

    def test_is_available_returns_true(self):
        """Test is_available returns True (D-Bus SNI is always available)."""
        from src.ui import tray_indicator

        result = tray_indicator.is_available()
        assert result is True

    def test_get_unavailable_reason_returns_none(self):
        """Test get_unavailable_reason returns None (tray is always available)."""
        from src.ui import tray_indicator

        result = tray_indicator.get_unavailable_reason()
        assert result is None
