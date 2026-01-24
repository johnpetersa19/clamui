# ClamUI TrayService Tests
"""
Unit tests for the TrayService class.

Tests cover:
- Class constants and configuration
- Status update handling
- Progress update handling
- Window visibility updates
- Profile management
- Command dispatch (handle_command)
- Helper methods for icon/tooltip/status
- IPC message handling

The TrayService uses D-Bus SNI protocol via GIO. Tests mock the GLib/Gio
dependencies to avoid requiring a running D-Bus session.
"""

import json
import sys
from unittest import mock

import pytest


@pytest.fixture(autouse=True)
def mock_glib_gio(monkeypatch):
    """Mock GLib and Gio modules for all tests."""
    mock_glib = mock.MagicMock()
    mock_gio = mock.MagicMock()

    # GLib.Variant should return a simple mock
    mock_glib.Variant = mock.MagicMock(return_value=mock.MagicMock())
    mock_glib.MainLoop = mock.MagicMock()
    mock_glib.idle_add = mock.MagicMock(side_effect=lambda fn, *args: fn(*args))

    monkeypatch.setitem(sys.modules, "gi", mock.MagicMock())
    monkeypatch.setitem(sys.modules, "gi.repository", mock.MagicMock())
    monkeypatch.setitem(sys.modules, "gi.repository.GLib", mock_glib)
    monkeypatch.setitem(sys.modules, "gi.repository.Gio", mock_gio)

    # Mock Dbusmenu as unavailable by default
    monkeypatch.setitem(sys.modules, "gi.repository.Dbusmenu", None)

    yield {"glib": mock_glib, "gio": mock_gio}


@pytest.fixture
def mock_tray_icons(monkeypatch):
    """Mock tray_icons module."""
    mock_module = mock.MagicMock()
    mock_module.find_clamui_base_icon = mock.MagicMock(return_value=None)
    mock_module.get_tray_icon_cache_dir = mock.MagicMock(return_value="/tmp/test")
    mock_module.TrayIconGenerator = mock.MagicMock()
    mock_module.CUSTOM_ICONS_AVAILABLE = False
    monkeypatch.setitem(sys.modules, "src.ui.tray_icons", mock_module)
    return mock_module


@pytest.fixture
def tray_service_class(mock_glib_gio, mock_tray_icons, monkeypatch):
    """Get TrayService class with mocked dependencies."""
    # Clear any cached import
    if "src.ui.tray_service" in sys.modules:
        del sys.modules["src.ui.tray_service"]

    from src.ui.tray_service import TrayService

    return TrayService


@pytest.fixture
def tray_service(tray_service_class):
    """Create a TrayService instance for testing."""
    service = object.__new__(tray_service_class)

    # Initialize state without calling __init__
    service._loop = None
    service._bus = None
    service._sni_registration_id = 0
    service._bus_name_id = 0
    service._running = True

    # Status state
    service._current_status = "protected"
    service._window_visible = True
    service._progress_label = ""

    # Profile state
    service._profiles = []
    service._current_profile_id = None

    # Icon generator
    service._icon_generator = None
    service._using_custom_icons = False

    # DBusMenu
    service._dbusmenu_server = None
    service._menu_root = None

    return service


class TestTrayServiceConstants:
    """Tests for TrayService class constants."""

    def test_icon_map_has_all_statuses(self, tray_service_class):
        """Test ICON_MAP contains all expected status keys."""
        expected_statuses = ["protected", "warning", "scanning", "threat"]
        for status in expected_statuses:
            assert status in tray_service_class.ICON_MAP
            assert isinstance(tray_service_class.ICON_MAP[status], str)

    def test_sni_status_map_has_all_statuses(self, tray_service_class):
        """Test SNI_STATUS_MAP contains all expected status keys."""
        expected_statuses = ["protected", "warning", "scanning", "threat"]
        for status in expected_statuses:
            assert status in tray_service_class.SNI_STATUS_MAP
            assert tray_service_class.SNI_STATUS_MAP[status] in [
                "Active",
                "NeedsAttention",
                "Passive",
            ]

    def test_dbus_name_format(self, tray_service_class):
        """Test DBUS_NAME follows D-Bus naming conventions."""
        assert tray_service_class.DBUS_NAME.startswith("io.github")
        assert "." in tray_service_class.DBUS_NAME
        # D-Bus names should not have underscores
        assert "ClamUI" in tray_service_class.DBUS_NAME

    def test_sni_path_format(self, tray_service_class):
        """Test SNI_PATH is valid D-Bus object path."""
        assert tray_service_class.SNI_PATH.startswith("/")
        assert tray_service_class.SNI_PATH == "/StatusNotifierItem"

    def test_menu_path_format(self, tray_service_class):
        """Test MENU_PATH is valid D-Bus object path."""
        assert tray_service_class.MENU_PATH.startswith("/")


class TestTrayServiceInitialization:
    """Tests for TrayService initialization state."""

    def test_initial_status_is_protected(self, tray_service):
        """Test initial status is 'protected'."""
        assert tray_service._current_status == "protected"

    def test_initial_window_visible_is_true(self, tray_service):
        """Test window is initially visible."""
        assert tray_service._window_visible is True

    def test_initial_progress_label_is_empty(self, tray_service):
        """Test progress label is initially empty."""
        assert tray_service._progress_label == ""

    def test_initial_profiles_is_empty(self, tray_service):
        """Test profiles list is initially empty."""
        assert tray_service._profiles == []

    def test_initial_current_profile_is_none(self, tray_service):
        """Test current profile ID is initially None."""
        assert tray_service._current_profile_id is None

    def test_running_flag_is_true(self, tray_service):
        """Test running flag is initially True."""
        assert tray_service._running is True


class TestUpdateStatus:
    """Tests for update_status method."""

    def test_update_status_sets_current_status(self, tray_service):
        """Test update_status sets the current status."""
        tray_service._emit_signal = mock.MagicMock()

        tray_service.update_status("scanning")
        assert tray_service._current_status == "scanning"

    def test_update_status_unknown_defaults_to_protected(self, tray_service):
        """Test unknown status defaults to 'protected'."""
        tray_service._emit_signal = mock.MagicMock()

        tray_service.update_status("unknown_status")
        assert tray_service._current_status == "protected"

    def test_update_status_emits_signals(self, tray_service):
        """Test update_status emits required D-Bus signals."""
        tray_service._emit_signal = mock.MagicMock()

        tray_service.update_status("warning")

        # Should emit NewIcon, NewToolTip, and NewStatus signals
        signal_names = [call[0][0] for call in tray_service._emit_signal.call_args_list]
        assert "NewIcon" in signal_names
        assert "NewToolTip" in signal_names
        assert "NewStatus" in signal_names

    def test_update_status_all_valid_statuses(self, tray_service):
        """Test all valid status values are accepted."""
        tray_service._emit_signal = mock.MagicMock()

        for status in ["protected", "warning", "scanning", "threat"]:
            tray_service.update_status(status)
            assert tray_service._current_status == status


class TestUpdateProgress:
    """Tests for update_progress method."""

    def test_update_progress_sets_label(self, tray_service):
        """Test update_progress sets progress label."""
        tray_service._emit_signal = mock.MagicMock()

        tray_service.update_progress(50)
        assert tray_service._progress_label == "50%"

    def test_update_progress_zero_clears_label(self, tray_service):
        """Test progress of 0 clears the label."""
        tray_service._emit_signal = mock.MagicMock()
        tray_service._progress_label = "50%"

        tray_service.update_progress(0)
        assert tray_service._progress_label == ""

    def test_update_progress_over_100_clears_label(self, tray_service):
        """Test progress over 100 clears the label."""
        tray_service._emit_signal = mock.MagicMock()
        tray_service._progress_label = "50%"

        tray_service.update_progress(101)
        assert tray_service._progress_label == ""

    def test_update_progress_100_is_valid(self, tray_service):
        """Test progress of 100 is valid."""
        tray_service._emit_signal = mock.MagicMock()

        tray_service.update_progress(100)
        assert tray_service._progress_label == "100%"

    def test_update_progress_emits_tooltip_signal(self, tray_service):
        """Test update_progress emits NewToolTip signal."""
        tray_service._emit_signal = mock.MagicMock()

        tray_service.update_progress(75)

        tray_service._emit_signal.assert_called_with("NewToolTip")


class TestUpdateWindowVisible:
    """Tests for update_window_visible method."""

    def test_update_window_visible_sets_state(self, tray_service):
        """Test update_window_visible sets visibility state."""
        tray_service._rebuild_menu = mock.MagicMock()

        tray_service.update_window_visible(False)
        assert tray_service._window_visible is False

        tray_service.update_window_visible(True)
        assert tray_service._window_visible is True

    def test_update_window_visible_rebuilds_menu(self, tray_service):
        """Test update_window_visible rebuilds the menu."""
        tray_service._rebuild_menu = mock.MagicMock()

        tray_service.update_window_visible(False)
        tray_service._rebuild_menu.assert_called_once()


class TestUpdateProfiles:
    """Tests for update_profiles method."""

    def test_update_profiles_sets_profiles_list(self, tray_service):
        """Test update_profiles sets the profiles list."""
        profiles = [
            {"id": "1", "name": "Quick Scan"},
            {"id": "2", "name": "Full Scan"},
        ]

        tray_service.update_profiles(profiles)
        assert tray_service._profiles == profiles

    def test_update_profiles_sets_current_profile_id(self, tray_service):
        """Test update_profiles sets current profile ID."""
        profiles = [{"id": "1", "name": "Quick Scan"}]

        tray_service.update_profiles(profiles, current_profile_id="1")
        assert tray_service._current_profile_id == "1"

    def test_update_profiles_without_current_id_preserves_existing(self, tray_service):
        """Test update_profiles without current_id preserves existing ID."""
        tray_service._current_profile_id = "original"
        profiles = [{"id": "1", "name": "Quick Scan"}]

        tray_service.update_profiles(profiles)
        assert tray_service._current_profile_id == "original"


class TestHandleCommand:
    """Tests for handle_command dispatch method."""

    def test_handle_update_status_command(self, tray_service):
        """Test handling update_status command."""
        tray_service.update_status = mock.MagicMock()

        # Patch GLib.idle_add at module level
        with mock.patch(
            "src.ui.tray_service.GLib.idle_add", side_effect=lambda fn, *args: fn(*args)
        ):
            tray_service.handle_command(
                {"action": "update_status", "status": "scanning"}
            )

        tray_service.update_status.assert_called_with("scanning")

    def test_handle_update_progress_command(self, tray_service):
        """Test handling update_progress command."""
        tray_service.update_progress = mock.MagicMock()

        with mock.patch(
            "src.ui.tray_service.GLib.idle_add", side_effect=lambda fn, *args: fn(*args)
        ):
            tray_service.handle_command({"action": "update_progress", "percentage": 75})

        tray_service.update_progress.assert_called_with(75)

    def test_handle_update_window_visible_command(self, tray_service):
        """Test handling update_window_visible command."""
        tray_service.update_window_visible = mock.MagicMock()

        with mock.patch(
            "src.ui.tray_service.GLib.idle_add", side_effect=lambda fn, *args: fn(*args)
        ):
            tray_service.handle_command(
                {"action": "update_window_visible", "visible": False}
            )

        tray_service.update_window_visible.assert_called_with(False)

    def test_handle_update_profiles_command(self, tray_service):
        """Test handling update_profiles command."""
        tray_service.update_profiles = mock.MagicMock()
        profiles = [{"id": "1", "name": "Test"}]

        with mock.patch(
            "src.ui.tray_service.GLib.idle_add", side_effect=lambda fn, *args: fn(*args)
        ):
            tray_service.handle_command(
                {
                    "action": "update_profiles",
                    "profiles": profiles,
                    "current_profile_id": "1",
                }
            )

        tray_service.update_profiles.assert_called_with(profiles, "1")

    def test_handle_quit_command(self, tray_service):
        """Test handling quit command."""
        tray_service._quit = mock.MagicMock()

        with mock.patch(
            "src.ui.tray_service.GLib.idle_add", side_effect=lambda fn, *args: fn(*args)
        ):
            tray_service.handle_command({"action": "quit"})

        tray_service._quit.assert_called_once()

    def test_handle_ping_command(self, tray_service):
        """Test handling ping command sends pong response."""
        tray_service._send_message = mock.MagicMock()

        tray_service.handle_command({"action": "ping"})

        tray_service._send_message.assert_called_with({"event": "pong"})

    def test_handle_unknown_command(self, tray_service):
        """Test handling unknown command logs warning."""
        tray_service._send_message = mock.MagicMock()

        # Should not raise, just log warning
        tray_service.handle_command({"action": "unknown_action"})

    def test_handle_command_missing_action(self, tray_service):
        """Test handling command without action key."""
        # Should handle gracefully
        tray_service.handle_command({})


class TestHelperMethods:
    """Tests for helper methods."""

    def test_get_icon_name_returns_mapped_icon(self, tray_service, tray_service_class):
        """Test _get_icon_name returns correct icon for status."""
        tray_service._current_status = "protected"

        result = tray_service._get_icon_name()
        assert result == tray_service_class.ICON_MAP["protected"]

    def test_get_icon_name_with_custom_icons(self, tray_service):
        """Test _get_icon_name with custom icon generator."""
        mock_generator = mock.MagicMock()
        mock_generator.get_icon_name.return_value = "clamui-tray-protected"

        tray_service._using_custom_icons = True
        tray_service._icon_generator = mock_generator
        tray_service._current_status = "protected"

        result = tray_service._get_icon_name()
        assert result == "clamui-tray-protected"

    def test_get_tooltip_shows_status(self, tray_service):
        """Test _get_tooltip includes status information."""
        tray_service._current_status = "protected"
        tray_service._progress_label = ""

        result = tray_service._get_tooltip()
        assert "ClamUI" in result

    def test_get_tooltip_includes_progress(self, tray_service):
        """Test _get_tooltip includes progress when scanning."""
        tray_service._current_status = "scanning"
        tray_service._progress_label = "75%"

        result = tray_service._get_tooltip()
        assert "75%" in result

    def test_get_sni_status_returns_mapped_status(
        self, tray_service, tray_service_class
    ):
        """Test _get_sni_status returns correct SNI status."""
        tray_service._current_status = "threat"

        result = tray_service._get_sni_status()
        assert result == tray_service_class.SNI_STATUS_MAP["threat"]


class TestSendMessage:
    """Tests for IPC message sending."""

    def test_send_message_outputs_json(self, tray_service, capsys):
        """Test _send_message outputs valid JSON to stdout."""
        message = {"event": "test", "data": "value"}

        tray_service._send_message(message)

        captured = capsys.readouterr()
        assert json.loads(captured.out.strip()) == message

    def test_send_action_creates_action_message(self, tray_service):
        """Test _send_action creates properly formatted action message."""
        tray_service._send_message = mock.MagicMock()

        tray_service._send_action("toggle_window")

        tray_service._send_message.assert_called_once()
        message = tray_service._send_message.call_args[0][0]
        assert message["event"] == "menu_action"  # SNI uses menu_action
        assert message["action"] == "toggle_window"


class TestQuit:
    """Tests for quit behavior."""

    def test_quit_sets_running_to_false(self, tray_service):
        """Test _quit sets running flag to False."""
        tray_service._running = True

        tray_service._quit()

        assert tray_service._running is False

    def test_quit_quits_main_loop(self, tray_service):
        """Test _quit quits the GLib main loop."""
        mock_loop = mock.MagicMock()
        tray_service._loop = mock_loop

        tray_service._quit()

        mock_loop.quit.assert_called_once()

    def test_quit_unregisters_dbus_objects(self, tray_service):
        """Test _quit unregisters D-Bus objects."""
        mock_bus = mock.MagicMock()
        tray_service._bus = mock_bus
        tray_service._sni_registration_id = 123

        tray_service._quit()

        mock_bus.unregister_object.assert_called_with(123)
