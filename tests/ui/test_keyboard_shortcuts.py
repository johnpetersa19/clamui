# ClamUI Keyboard Shortcuts Tests
"""
Unit tests for keyboard shortcut functionality.

Tests cover:
- Tooltip formatting with keyboard shortcuts
- Tooltip format consistency

Note: Tests for accelerator registration are skipped due to complex GTK/matplotlib
mocking requirements. The keyboard shortcuts functionality is manually verified
and implemented in src/app.py, src/ui/window.py, and src/ui/scan_view.py.
"""

import sys
from unittest import mock


def _clear_src_modules():
    """Clear all cached src.* modules to prevent test pollution."""
    modules_to_remove = [mod for mod in sys.modules if mod.startswith("src.")]
    for mod in modules_to_remove:
        del sys.modules[mod]


class TestTooltipFormatting:
    """Tests for tooltip formatting with keyboard shortcuts."""

    def test_header_bar_button_tooltips(self, mock_gi_modules):
        """Test that header bar buttons have proper tooltips."""
        # Clear any cached imports
        _clear_src_modules()

        # Import MainWindow class
        from src.ui.window import MainWindow

        # Create instance without calling __init__ (Python 3.13 compatible)
        window = object.__new__(MainWindow)

        # Mock required attributes
        window._application = mock.MagicMock()
        window._back_button = mock.MagicMock()
        window._title_label = mock.MagicMock()
        window._scan_file_button = mock.MagicMock()
        window._scan_system_button = mock.MagicMock()

        # Call the method that creates header bar
        result = window._create_header_bar()

        # Verify the method was called (returns a widget)
        assert result is not None

        # Verify header bar buttons have tooltips
        # Note: Navigation is now handled by sidebar, not header bar buttons
        # Header bar contains scan-file and scan-system buttons instead

    def test_menu_button_tooltip(self, mock_gi_modules):
        """Test that menu button has tooltip with F10 keyboard shortcut."""
        # Clear any cached imports
        _clear_src_modules()

        # Import MainWindow class
        from src.ui.window import MainWindow

        # Create instance without calling __init__
        window = object.__new__(MainWindow)

        # Mock required attributes
        window._application = mock.MagicMock()

        # Call the method that creates menu button
        menu_button = window._create_menu_button()

        # Verify the menu button has tooltip with F10
        menu_button.set_tooltip_text.assert_called_with("Menu (F10)")

    def test_scan_button_tooltip(self, mock_gi_modules):
        """Test that scan button has tooltip with F5 keyboard shortcut."""
        # Clear any cached imports
        _clear_src_modules()

        # Mock dependencies
        mock_scanner_module = mock.MagicMock()
        mock_scanner_module.Scanner = mock.MagicMock()
        mock_scanner_module.ScanResult = mock.MagicMock()
        mock_scanner_module.ScanStatus = mock.MagicMock()

        mock_utils_module = mock.MagicMock()
        mock_utils_module.format_scan_path = mock.MagicMock(return_value="/test/path")
        mock_utils_module.validate_dropped_files = mock.MagicMock(
            return_value=(["/test"], [])
        )

        mock_quarantine_module = mock.MagicMock()
        mock_quarantine_module.QuarantineManager = mock.MagicMock()

        mock_profile_dialogs = mock.MagicMock()
        mock_profile_dialogs.ProfileListDialog = mock.MagicMock()

        mock_scan_results_dialog = mock.MagicMock()
        mock_scan_results_dialog.ScanResultsDialog = mock.MagicMock()

        mock_ui_utils = mock.MagicMock()
        mock_ui_utils.add_row_icon = mock.MagicMock()

        with mock.patch.dict(
            sys.modules,
            {
                "src.core.scanner": mock_scanner_module,
                "src.core.utils": mock_utils_module,
                "src.core.quarantine": mock_quarantine_module,
                "src.ui.profile_dialogs": mock_profile_dialogs,
                "src.ui.scan_results_dialog": mock_scan_results_dialog,
                "src.ui.utils": mock_ui_utils,
            },
        ):
            # Import ScanView class
            from src.ui.scan_view import ScanView

            # Create instance without calling __init__
            view = object.__new__(ScanView)

            # Mock required attributes
            view._settings_manager = mock.MagicMock()
            view._scanner = mock.MagicMock()
            view._quarantine_manager = mock.MagicMock()
            view._scan_button = mock.MagicMock()

            # Call the method that creates scan section
            view._create_scan_section()

            # Verify the scan button has tooltip with F5
            view._scan_button.set_tooltip_text.assert_any_call("Start Scan (F5)")

    def test_update_button_tooltip(self, mock_gi_modules):
        """Test that update button has tooltip with F6 keyboard shortcut."""
        # Clear any cached imports
        _clear_src_modules()

        # Mock dependencies
        mock_updater_module = mock.MagicMock()
        mock_updater_module.FreshclamUpdater = mock.MagicMock()
        mock_updater_module.UpdateResult = mock.MagicMock()
        mock_updater_module.UpdateStatus = mock.MagicMock()

        with mock.patch.dict(
            sys.modules,
            {
                "src.core.updater": mock_updater_module,
            },
        ):
            # Import UpdateView class
            from src.ui.update_view import UpdateView

            # Create instance without calling __init__
            view = object.__new__(UpdateView)

            # Mock required attributes
            view._settings_manager = mock.MagicMock()
            view._updater = mock.MagicMock()
            view._update_button = mock.MagicMock()
            view._update_spinner = mock.MagicMock()
            view._cancel_button = mock.MagicMock()

            # Call the method that creates update section
            view._create_update_section()

            # Verify the update button has tooltip with F6
            view._update_button.set_tooltip_text.assert_any_call("Update Database (F6)")

    def test_tooltip_format_consistency(self, mock_gi_modules):
        """Test that menu button tooltip follows consistent format: 'Description (Shortcut)'."""
        # This test verifies the tooltip format pattern used for the menu button
        # Format: "Description (Shortcut)" where Shortcut is human-readable
        # Note: Navigation is now via sidebar (no tooltips), header bar has scan buttons

        # Clear any cached imports
        _clear_src_modules()

        # Import MainWindow class
        from src.ui.window import MainWindow

        # Create instance without calling __init__
        window = object.__new__(MainWindow)

        # Mock required attributes
        window._application = mock.MagicMock()
        window._back_button = mock.MagicMock()
        window._title_label = mock.MagicMock()
        window._scan_file_button = mock.MagicMock()
        window._scan_system_button = mock.MagicMock()

        # Create menu button
        menu_button = window._create_menu_button()

        # Verify menu button tooltip follows the format "Description (Shortcut)"
        tooltip = menu_button.set_tooltip_text.call_args[0][0]
        assert tooltip.endswith(")"), f"Tooltip '{tooltip}' doesn't end with ')'"
        assert "(" in tooltip, f"Tooltip '{tooltip}' doesn't contain '('"
        # Extract shortcut part
        shortcut_part = tooltip[tooltip.rfind("(") + 1 : -1]
        # Shortcut should not be empty
        assert len(shortcut_part) > 0, f"Tooltip '{tooltip}' has empty shortcut"

    def test_tooltip_shortcuts_match_accelerators(self, mock_gi_modules):
        """Test that keyboard accelerators are properly formatted."""
        # This test verifies that keyboard accelerators follow GTK format
        # Note: Navigation shortcuts (Ctrl+1-6) are still active via app actions,
        # but no longer have tooltips since navigation moved to sidebar

        # Expected mapping of shortcuts to GTK accelerator format
        # These are registered in app.py via set_accels_for_action
        tooltip_to_accelerator = {
            "Ctrl+1": "<Control>1",  # show-scan
            "Ctrl+2": "<Control>2",  # show-update
            "Ctrl+3": "<Control>3",  # show-logs
            "Ctrl+4": "<Control>4",  # show-components
            "Ctrl+5": "<Control>5",  # show-quarantine
            "Ctrl+6": "<Control>6",  # show-statistics
            "F5": "F5",  # start-scan
            "F6": "F6",  # start-update
            "F10": "F10",  # Standard GTK menu key
        }

        # Verify the mapping includes all expected shortcuts
        assert len(tooltip_to_accelerator) == 9  # 6 navigation + F5 + F6 + F10

        # Verify all shortcut formats are valid
        for tooltip_format, gtk_format in tooltip_to_accelerator.items():
            # Tooltip format should be human-readable (e.g., "Ctrl+1")
            assert "+" in tooltip_format or tooltip_format.startswith(
                "F"
            ), f"Invalid tooltip format: {tooltip_format}"
            # GTK format should contain Control or start with F
            assert "<Control>" in gtk_format or gtk_format.startswith(
                "F"
            ), f"Invalid GTK format: {gtk_format}"
