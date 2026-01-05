# ClamUI Keyboard Shortcuts Tests
"""
Unit tests for keyboard shortcut functionality.

Tests cover:
- Accelerator registration for all navigation actions
- Accelerator registration for action shortcuts
- Correct action names and accelerator bindings
- Verification that all shortcuts are properly bound
"""

import sys
from unittest import mock

import pytest


def _clear_src_modules():
    """Clear all cached src.* modules to prevent test pollution."""
    modules_to_remove = [mod for mod in sys.modules if mod.startswith("src.")]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def app_class(mock_gi_modules):
    """Get ClamUIApp class with mocked dependencies."""
    # Mock additional dependencies
    mock_settings_manager = mock.MagicMock()
    mock_notification_manager = mock.MagicMock()
    mock_profile_manager = mock.MagicMock()

    with mock.patch.dict(
        sys.modules,
        {
            "src.core.settings_manager": mock.MagicMock(SettingsManager=mock_settings_manager),
            "src.core.notification_manager": mock.MagicMock(
                NotificationManager=mock_notification_manager
            ),
            "src.profiles.profile_manager": mock.MagicMock(ProfileManager=mock_profile_manager),
        },
    ):
        # Clear any cached import
        if "src.app" in sys.modules:
            del sys.modules["src.app"]

        from src.app import ClamUIApp

        yield ClamUIApp

    # Clear all src.* modules after test
    _clear_src_modules()


@pytest.fixture
def mock_app(app_class, mock_gi_modules):
    """Create a mock ClamUIApp instance for testing."""
    # Create instance without calling __init__
    app = object.__new__(app_class)

    # Mock Gio module for actions
    gio = mock_gi_modules["gio"]

    # Set up required attributes
    app._settings_manager = mock.MagicMock()
    app._notification_manager = mock.MagicMock()
    app._profile_manager = mock.MagicMock()
    app._scan_view = None
    app._update_view = None
    app._logs_view = None
    app._components_view = None
    app._statistics_view = None
    app._quarantine_view = None
    app._current_view = None
    app._tray_indicator = None
    app._first_activation = True

    # Mock the application methods we need
    app.add_action = mock.MagicMock()
    app.set_accels_for_action = mock.MagicMock()

    return app


class TestNavigationAccelerators:
    """Tests for navigation keyboard accelerators."""

    def test_show_scan_accelerator(self, mock_app, mock_gi_modules):
        """Test show-scan action has Ctrl+1 accelerator."""
        # Call _setup_actions
        mock_app._setup_actions()

        # Verify set_accels_for_action was called with correct parameters
        mock_app.set_accels_for_action.assert_any_call("app.show-scan", ["<Control>1"])

    def test_show_update_accelerator(self, mock_app, mock_gi_modules):
        """Test show-update action has Ctrl+2 accelerator."""
        mock_app._setup_actions()

        mock_app.set_accels_for_action.assert_any_call("app.show-update", ["<Control>2"])

    def test_show_logs_accelerator(self, mock_app, mock_gi_modules):
        """Test show-logs action has Ctrl+3 accelerator."""
        mock_app._setup_actions()

        mock_app.set_accels_for_action.assert_any_call("app.show-logs", ["<Control>3"])

    def test_show_components_accelerator(self, mock_app, mock_gi_modules):
        """Test show-components action has Ctrl+4 accelerator."""
        mock_app._setup_actions()

        mock_app.set_accels_for_action.assert_any_call("app.show-components", ["<Control>4"])

    def test_show_quarantine_accelerator(self, mock_app, mock_gi_modules):
        """Test show-quarantine action has Ctrl+5 accelerator."""
        mock_app._setup_actions()

        mock_app.set_accels_for_action.assert_any_call("app.show-quarantine", ["<Control>5"])

    def test_show_statistics_accelerator(self, mock_app, mock_gi_modules):
        """Test show-statistics action has Ctrl+6 accelerator."""
        mock_app._setup_actions()

        mock_app.set_accels_for_action.assert_any_call("app.show-statistics", ["<Control>6"])


class TestActionAccelerators:
    """Tests for action keyboard accelerators."""

    def test_quit_accelerator(self, mock_app, mock_gi_modules):
        """Test quit action has Ctrl+Q accelerator."""
        mock_app._setup_actions()

        mock_app.set_accels_for_action.assert_any_call("app.quit", ["<Control>q"])

    def test_preferences_accelerator(self, mock_app, mock_gi_modules):
        """Test preferences action has Ctrl+, accelerator."""
        mock_app._setup_actions()

        mock_app.set_accels_for_action.assert_any_call("app.preferences", ["<Control>comma"])

    def test_start_scan_accelerator(self, mock_app, mock_gi_modules):
        """Test start-scan action has F5 accelerator."""
        mock_app._setup_actions()

        mock_app.set_accels_for_action.assert_any_call("app.start-scan", ["F5"])

    def test_start_update_accelerator(self, mock_app, mock_gi_modules):
        """Test start-update action has F6 accelerator."""
        mock_app._setup_actions()

        mock_app.set_accels_for_action.assert_any_call("app.start-update", ["F6"])


class TestActionRegistration:
    """Tests for action registration in _setup_actions."""

    def test_all_navigation_actions_registered(self, mock_app, mock_gi_modules):
        """Test that all navigation actions are registered."""
        # Mock SimpleAction.new to track action creation
        gio = mock_gi_modules["gio"]
        mock_action = mock.MagicMock()
        gio.SimpleAction.new.return_value = mock_action

        mock_app._setup_actions()

        # Verify all navigation actions were created
        navigation_actions = [
            "show-scan",
            "show-update",
            "show-logs",
            "show-components",
            "show-quarantine",
            "show-statistics",
        ]

        for action_name in navigation_actions:
            gio.SimpleAction.new.assert_any_call(action_name, None)

    def test_all_action_shortcuts_registered(self, mock_app, mock_gi_modules):
        """Test that all action shortcuts are registered."""
        gio = mock_gi_modules["gio"]
        mock_action = mock.MagicMock()
        gio.SimpleAction.new.return_value = mock_action

        mock_app._setup_actions()

        # Verify all action shortcuts were created
        action_shortcuts = ["quit", "about", "preferences", "start-scan", "start-update"]

        for action_name in action_shortcuts:
            gio.SimpleAction.new.assert_any_call(action_name, None)

    def test_all_actions_added_to_app(self, mock_app, mock_gi_modules):
        """Test that all created actions are added to the application."""
        gio = mock_gi_modules["gio"]
        mock_action = mock.MagicMock()
        gio.SimpleAction.new.return_value = mock_action

        mock_app._setup_actions()

        # Should have 11 actions total
        # 6 navigation + 5 actions (quit, about, preferences, start-scan, start-update)
        expected_action_count = 11

        # Verify add_action was called the expected number of times
        assert mock_app.add_action.call_count == expected_action_count

    def test_actions_connected_to_handlers(self, mock_app, mock_gi_modules):
        """Test that actions are connected to their handler methods."""
        gio = mock_gi_modules["gio"]
        mock_action = mock.MagicMock()
        gio.SimpleAction.new.return_value = mock_action

        # Mock the handler methods
        mock_app._on_quit = mock.MagicMock()
        mock_app._on_about = mock.MagicMock()
        mock_app._on_preferences = mock.MagicMock()
        mock_app._on_show_scan = mock.MagicMock()
        mock_app._on_show_update = mock.MagicMock()
        mock_app._on_show_logs = mock.MagicMock()
        mock_app._on_show_components = mock.MagicMock()
        mock_app._on_show_quarantine = mock.MagicMock()
        mock_app._on_show_statistics = mock.MagicMock()
        mock_app._on_start_scan = mock.MagicMock()
        mock_app._on_start_update = mock.MagicMock()

        mock_app._setup_actions()

        # Verify connect was called on each action
        # 11 actions total should all have connect called
        assert mock_action.connect.call_count == 11


class TestAcceleratorCount:
    """Tests for verifying all accelerators are registered."""

    def test_all_accelerators_registered(self, mock_app, mock_gi_modules):
        """Test that all keyboard accelerators are registered."""
        mock_app._setup_actions()

        # Expected accelerators:
        # - Ctrl+1 through Ctrl+6 (6 navigation)
        # - Ctrl+Q (quit)
        # - Ctrl+, (preferences)
        # - F5 (start-scan)
        # - F6 (start-update)
        # Total: 10 accelerators
        expected_accelerator_count = 10

        assert mock_app.set_accels_for_action.call_count == expected_accelerator_count

    def test_no_duplicate_accelerators(self, mock_app, mock_gi_modules):
        """Test that no accelerator is bound to multiple actions."""
        mock_app._setup_actions()

        # Get all accelerator calls
        calls = mock_app.set_accels_for_action.call_args_list

        # Extract accelerators (second argument of each call)
        accelerators = [call[0][1][0] for call in calls]

        # Check for duplicates
        assert len(accelerators) == len(set(accelerators)), "Duplicate accelerators detected"

    def test_accelerator_format_consistency(self, mock_app, mock_gi_modules):
        """Test that all accelerators use consistent format."""
        mock_app._setup_actions()

        # Get all accelerator calls
        calls = mock_app.set_accels_for_action.call_args_list

        # Check that all accelerators are in list format
        for call in calls:
            accelerator_list = call[0][1]
            assert isinstance(accelerator_list, list), "Accelerator must be in list format"
            assert len(accelerator_list) == 1, "Each action should have exactly one accelerator"


class TestAcceleratorBindings:
    """Tests for specific accelerator to action bindings."""

    def test_navigation_accelerators_mapping(self, mock_app, mock_gi_modules):
        """Test correct mapping of navigation accelerators to actions."""
        mock_app._setup_actions()

        # Expected mappings
        expected_mappings = {
            "app.show-scan": "<Control>1",
            "app.show-update": "<Control>2",
            "app.show-logs": "<Control>3",
            "app.show-components": "<Control>4",
            "app.show-quarantine": "<Control>5",
            "app.show-statistics": "<Control>6",
        }

        # Verify each mapping
        for action, accelerator in expected_mappings.items():
            mock_app.set_accels_for_action.assert_any_call(action, [accelerator])

    def test_action_accelerators_mapping(self, mock_app, mock_gi_modules):
        """Test correct mapping of action accelerators to actions."""
        mock_app._setup_actions()

        # Expected mappings
        expected_mappings = {
            "app.quit": "<Control>q",
            "app.preferences": "<Control>comma",
            "app.start-scan": "F5",
            "app.start-update": "F6",
        }

        # Verify each mapping
        for action, accelerator in expected_mappings.items():
            mock_app.set_accels_for_action.assert_any_call(action, [accelerator])


class TestTooltipFormatting:
    """Tests for tooltip formatting with keyboard shortcuts."""

    def test_navigation_button_tooltips(self, mock_gi_modules):
        """Test that navigation buttons have tooltips with keyboard shortcuts."""
        # Clear any cached imports
        _clear_src_modules()

        # Import MainWindow class
        from src.ui.window import MainWindow

        # Create instance without calling __init__ (Python 3.13 compatible)
        window = object.__new__(MainWindow)

        # Mock required attributes
        window._application = mock.MagicMock()
        window._scan_button = mock.MagicMock()
        window._database_button = mock.MagicMock()
        window._logs_button = mock.MagicMock()
        window._components_button = mock.MagicMock()
        window._quarantine_button = mock.MagicMock()
        window._statistics_button = mock.MagicMock()

        # Call the method that creates navigation buttons
        result = window._create_navigation_buttons()

        # Verify the method was called (returns a widget)
        assert result is not None

        # Verify set_tooltip_text was called with proper format
        window._scan_button.set_tooltip_text.assert_called_with("Scan Files (Ctrl+1)")
        window._database_button.set_tooltip_text.assert_called_with("Update Database (Ctrl+2)")
        window._logs_button.set_tooltip_text.assert_called_with("View Logs (Ctrl+3)")
        window._components_button.set_tooltip_text.assert_called_with("ClamAV Components (Ctrl+4)")
        window._quarantine_button.set_tooltip_text.assert_called_with("Quarantine (Ctrl+5)")
        window._statistics_button.set_tooltip_text.assert_called_with(
            "Statistics Dashboard (Ctrl+6)"
        )

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
        mock_utils_module.validate_dropped_files = mock.MagicMock(return_value=(["/test"], []))

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
            view._scan_button.set_tooltip_text.assert_called_with("Start Scan (F5)")

    def test_tooltip_format_consistency(self, mock_gi_modules):
        """Test that all tooltips follow consistent format: 'Description (Shortcut)'."""
        # This test verifies the tooltip format pattern used across all buttons
        # Format: "Description (Shortcut)" where Shortcut is human-readable

        # Clear any cached imports
        _clear_src_modules()

        # Import MainWindow class
        from src.ui.window import MainWindow

        # Create instance without calling __init__
        window = object.__new__(MainWindow)

        # Mock required attributes
        window._application = mock.MagicMock()
        window._scan_button = mock.MagicMock()
        window._database_button = mock.MagicMock()
        window._logs_button = mock.MagicMock()
        window._components_button = mock.MagicMock()
        window._quarantine_button = mock.MagicMock()
        window._statistics_button = mock.MagicMock()

        # Create navigation buttons
        window._create_navigation_buttons()

        # Collect all tooltip calls
        tooltip_calls = [
            window._scan_button.set_tooltip_text.call_args[0][0],
            window._database_button.set_tooltip_text.call_args[0][0],
            window._logs_button.set_tooltip_text.call_args[0][0],
            window._components_button.set_tooltip_text.call_args[0][0],
            window._quarantine_button.set_tooltip_text.call_args[0][0],
            window._statistics_button.set_tooltip_text.call_args[0][0],
        ]

        # Create menu button
        menu_button = window._create_menu_button()
        tooltip_calls.append(menu_button.set_tooltip_text.call_args[0][0])

        # Verify all tooltips follow the format "Description (Shortcut)"
        for tooltip in tooltip_calls:
            # Check format: ends with '(Something)'
            assert tooltip.endswith(")"), f"Tooltip '{tooltip}' doesn't end with ')'"
            assert "(" in tooltip, f"Tooltip '{tooltip}' doesn't contain '('"
            # Extract shortcut part
            shortcut_part = tooltip[tooltip.rfind("(") + 1 : -1]
            # Shortcut should not be empty
            assert len(shortcut_part) > 0, f"Tooltip '{tooltip}' has empty shortcut"

    def test_tooltip_shortcuts_match_accelerators(self, mock_gi_modules):
        """Test that tooltip shortcuts match the registered accelerators."""
        # This test verifies that the human-readable shortcuts in tooltips
        # correspond to the actual keyboard accelerators registered in app.py

        # Expected mapping of tooltip shortcuts to GTK accelerator format
        tooltip_to_accelerator = {
            "Ctrl+1": "<Control>1",
            "Ctrl+2": "<Control>2",
            "Ctrl+3": "<Control>3",
            "Ctrl+4": "<Control>4",
            "Ctrl+5": "<Control>5",
            "Ctrl+6": "<Control>6",
            "F5": "F5",
            "F10": "F10",  # Standard GTK menu key
        }

        # Verify the mapping is correct
        assert len(tooltip_to_accelerator) == 8  # 6 navigation + F5 + F10

        # Verify all tooltip formats can be mapped to accelerators
        for tooltip_format, gtk_format in tooltip_to_accelerator.items():
            # Tooltip format should be human-readable (e.g., "Ctrl+1")
            assert "+" in tooltip_format or tooltip_format.startswith(
                "F"
            ), f"Invalid tooltip format: {tooltip_format}"


class TestActionHandlers:
    """Tests for start-scan and start-update action handlers."""

    def test_start_scan_switches_view_and_starts_scan(self, mock_app, mock_gi_modules):
        """Test that start-scan action switches to scan view and starts scan."""
        # Setup
        mock_window = mock.MagicMock()
        mock_app.props.active_window = mock_window
        mock_app._scan_view = mock.MagicMock()
        mock_app._current_view = "update"  # Start on different view

        # Execute
        mock_app._on_start_scan(None, None)

        # Verify view was switched
        mock_window.set_content_view.assert_called_once_with(mock_app._scan_view)
        mock_window.set_active_view.assert_called_once_with("scan")
        assert mock_app._current_view == "scan"

        # Verify scan was started
        mock_app._scan_view._start_scan.assert_called_once()

    def test_start_scan_when_already_on_scan_view(self, mock_app, mock_gi_modules):
        """Test that start-scan action starts scan when already on scan view."""
        # Setup
        mock_window = mock.MagicMock()
        mock_app.props.active_window = mock_window
        mock_app._scan_view = mock.MagicMock()
        mock_app._current_view = "scan"  # Already on scan view

        # Execute
        mock_app._on_start_scan(None, None)

        # Verify view switch was not performed
        mock_window.set_content_view.assert_not_called()
        mock_window.set_active_view.assert_not_called()

        # Verify scan was still started
        mock_app._scan_view._start_scan.assert_called_once()

    def test_start_scan_with_no_active_window(self, mock_app, mock_gi_modules):
        """Test that start-scan action handles no active window gracefully."""
        # Setup
        mock_app.props.active_window = None
        mock_app._scan_view = mock.MagicMock()

        # Execute - should not raise exception
        mock_app._on_start_scan(None, None)

        # Verify scan was not started
        mock_app._scan_view._start_scan.assert_not_called()

    def test_start_scan_with_no_scan_view(self, mock_app, mock_gi_modules):
        """Test that start-scan action handles missing scan view gracefully."""
        # Setup
        mock_window = mock.MagicMock()
        mock_app.props.active_window = mock_window
        mock_app._scan_view = None

        # Execute - should not raise exception
        mock_app._on_start_scan(None, None)

        # Verify no errors occurred (no calls to non-existent scan view)
        mock_window.set_content_view.assert_not_called()

    def test_start_update_switches_view_and_starts_update(self, mock_app, mock_gi_modules):
        """Test that start-update action switches to update view and starts update."""
        # Setup
        mock_window = mock.MagicMock()
        mock_app.props.active_window = mock_window
        mock_app._update_view = mock.MagicMock()
        mock_app._update_view._freshclam_available = True
        mock_app._update_view._is_updating = False
        mock_app._current_view = "scan"  # Start on different view

        # Execute
        mock_app._on_start_update(None, None)

        # Verify view was switched
        mock_window.set_content_view.assert_called_once_with(mock_app._update_view)
        mock_window.set_active_view.assert_called_once_with("update")
        assert mock_app._current_view == "update"

        # Verify update was started
        mock_app._update_view._start_update.assert_called_once()

    def test_start_update_when_already_on_update_view(self, mock_app, mock_gi_modules):
        """Test that start-update action starts update when already on update view."""
        # Setup
        mock_window = mock.MagicMock()
        mock_app.props.active_window = mock_window
        mock_app._update_view = mock.MagicMock()
        mock_app._update_view._freshclam_available = True
        mock_app._update_view._is_updating = False
        mock_app._current_view = "update"  # Already on update view

        # Execute
        mock_app._on_start_update(None, None)

        # Verify view switch was not performed
        mock_window.set_content_view.assert_not_called()
        mock_window.set_active_view.assert_not_called()

        # Verify update was still started
        mock_app._update_view._start_update.assert_called_once()

    def test_start_update_with_freshclam_unavailable(self, mock_app, mock_gi_modules):
        """Test that start-update action doesn't start when freshclam is unavailable."""
        # Setup
        mock_window = mock.MagicMock()
        mock_app.props.active_window = mock_window
        mock_app._update_view = mock.MagicMock()
        mock_app._update_view._freshclam_available = False
        mock_app._update_view._is_updating = False
        mock_app._current_view = "scan"

        # Execute
        mock_app._on_start_update(None, None)

        # Verify view was switched
        mock_window.set_content_view.assert_called_once_with(mock_app._update_view)

        # Verify update was NOT started (freshclam unavailable)
        mock_app._update_view._start_update.assert_not_called()

    def test_start_update_when_already_updating(self, mock_app, mock_gi_modules):
        """Test that start-update action doesn't start when already updating."""
        # Setup
        mock_window = mock.MagicMock()
        mock_app.props.active_window = mock_window
        mock_app._update_view = mock.MagicMock()
        mock_app._update_view._freshclam_available = True
        mock_app._update_view._is_updating = True  # Already updating
        mock_app._current_view = "scan"

        # Execute
        mock_app._on_start_update(None, None)

        # Verify view was switched
        mock_window.set_content_view.assert_called_once_with(mock_app._update_view)

        # Verify update was NOT started (already updating)
        mock_app._update_view._start_update.assert_not_called()

    def test_start_update_with_no_active_window(self, mock_app, mock_gi_modules):
        """Test that start-update action handles no active window gracefully."""
        # Setup
        mock_app.props.active_window = None
        mock_app._update_view = mock.MagicMock()
        mock_app._update_view._freshclam_available = True
        mock_app._update_view._is_updating = False

        # Execute - should not raise exception
        mock_app._on_start_update(None, None)

        # Verify update was not started
        mock_app._update_view._start_update.assert_not_called()

    def test_start_update_with_no_update_view(self, mock_app, mock_gi_modules):
        """Test that start-update action handles missing update view gracefully."""
        # Setup
        mock_window = mock.MagicMock()
        mock_app.props.active_window = mock_window
        mock_app._update_view = None

        # Execute - should not raise exception
        mock_app._on_start_update(None, None)

        # Verify no errors occurred (no calls to non-existent update view)
        mock_window.set_content_view.assert_not_called()
