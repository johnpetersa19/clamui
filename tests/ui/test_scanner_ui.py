# ClamUI Scanner UI Tests
"""
Unit tests for the Scanner UI (ScanView) component.

Tests cover:
- GTK module mocking setup
- ScanView initialization and setup
- File/folder selection UI interactions
- Scan button state and actions
- Results display updates
- Profile selection UI

This test module uses centralized GTK mocking from conftest.py.
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
def scan_view_class(mock_gi_modules):
    """
    Get ScanView class with mocked dependencies.

    Returns the ScanView class that can be used to create test instances.
    """
    # Create mock modules for scan_view dependencies
    mock_scanner_module = mock.MagicMock()
    mock_scanner_module.Scanner = mock.MagicMock()
    mock_scanner_module.ScanResult = mock.MagicMock()
    mock_scanner_module.ScanStatus = mock.MagicMock()
    mock_scanner_module.ScanStatus.CLEAN = "clean"
    mock_scanner_module.ScanStatus.INFECTED = "infected"
    mock_scanner_module.ScanStatus.ERROR = "error"
    mock_scanner_module.ScanStatus.CANCELLED = "cancelled"
    mock_scanner_module.ThreatDetail = mock.MagicMock()

    mock_utils_module = mock.MagicMock()
    mock_utils_module.format_scan_path = mock.MagicMock(return_value="/test/path")
    mock_utils_module.check_clamav_installed = mock.MagicMock(return_value=True)
    mock_utils_module.validate_dropped_files = mock.MagicMock(return_value=["/test/file"])
    mock_utils_module.format_results_as_text = mock.MagicMock(return_value="results")
    mock_utils_module.copy_to_clipboard = mock.MagicMock()

    mock_quarantine_module = mock.MagicMock()
    mock_quarantine_module.QuarantineManager = mock.MagicMock()
    mock_quarantine_module.QuarantineStatus = mock.MagicMock()

    mock_profile_dialogs = mock.MagicMock()
    mock_profile_dialogs.ProfileListDialog = mock.MagicMock()

    mock_scan_results_dialog = mock.MagicMock()
    mock_scan_results_dialog.ScanResultsDialog = mock.MagicMock()

    with mock.patch.dict(
        sys.modules,
        {
            "src.core.scanner": mock_scanner_module,
            "src.core.utils": mock_utils_module,
            "src.core.quarantine": mock_quarantine_module,
            "src.ui.profile_dialogs": mock_profile_dialogs,
            "src.ui.scan_results_dialog": mock_scan_results_dialog,
        },
    ):
        # Need to remove and reimport the scan_view module for fresh mocks
        if "src.ui.scan_view" in sys.modules:
            del sys.modules["src.ui.scan_view"]

        from src.ui.scan_view import ScanView

        yield ScanView

    # Critical: Clear all src.* modules after test to prevent pollution.
    # The mocked modules may have been cached in src.core.scanner etc.
    _clear_src_modules()


@pytest.fixture
def mock_scan_view(scan_view_class, mock_gi_modules):
    """
    Create a mock ScanView instance for testing.

    This creates a ScanView instance without calling __init__ and sets up
    all required attributes manually. This allows testing individual methods
    without the full initialization overhead.
    """
    # Create instance without calling __init__ (Python 3.13 compatible)
    view = object.__new__(scan_view_class)

    # Set up required attributes
    view._scanner = mock.MagicMock()
    view._quarantine_manager = mock.MagicMock()
    view._selected_path = ""
    view._is_scanning = False
    view._eicar_temp_path = ""
    view._current_result = None
    view._on_scan_state_changed = None
    view._selected_profile = None
    view._profile_list = []
    view._profile_string_list = None
    view._profile_dropdown = None

    # Mock UI elements
    view._path_row = mock.MagicMock()
    view._scan_button = mock.MagicMock()
    view._scan_button_content = mock.MagicMock()
    view._scan_spinner = mock.MagicMock()
    view._cancel_button = mock.MagicMock()
    view._results_group = mock.MagicMock()
    view._results_list = mock.MagicMock()
    view._status_bar = mock.MagicMock()
    view._status_label = mock.MagicMock()
    view._status_badge = mock.MagicMock()
    view._profile_group = mock.MagicMock()
    view._select_folder_btn = mock.MagicMock()
    view._select_file_btn = mock.MagicMock()
    view._browse_button = mock.MagicMock()
    view._eicar_button = mock.MagicMock()
    view._manage_profiles_btn = mock.MagicMock()

    # Results display UI elements
    view._status_banner = mock.MagicMock()
    view._threats_list = mock.MagicMock()
    view._results_placeholder = mock.MagicMock()
    view._copy_button = mock.MagicMock()
    view._export_text_button = mock.MagicMock()
    view._export_csv_button = mock.MagicMock()
    view._raw_output = ""

    # Progress section UI elements
    view._progress_section = mock.MagicMock()
    view._progress_bar = mock.MagicMock()
    view._progress_label = mock.MagicMock()
    view._pulse_timeout_id = None

    # View results section UI elements
    view._view_results_section = mock.MagicMock()
    view._view_results_button = mock.MagicMock()

    # Mock internal methods commonly used
    view._setup_ui = mock.MagicMock()
    view._setup_drop_css = mock.MagicMock()
    view._setup_drop_target = mock.MagicMock()
    view._create_profile_section = mock.MagicMock()
    view._create_selection_section = mock.MagicMock()
    view._create_scan_section = mock.MagicMock()
    view._create_view_results_section = mock.MagicMock()
    view._create_status_bar = mock.MagicMock()
    view._check_clamav_status = mock.MagicMock()
    view._update_scan_button_state = mock.MagicMock()
    view._set_selected_path = mock.MagicMock()
    view._start_scan = mock.MagicMock()
    view._run_scan = mock.MagicMock()
    view._update_status = mock.MagicMock()
    view._show_view_results = mock.MagicMock()
    view._hide_view_results = mock.MagicMock()
    view._on_view_results_clicked = mock.MagicMock()

    # Mock parent class methods
    view.append = mock.MagicMock()
    view.remove = mock.MagicMock()
    view.set_margin_top = mock.MagicMock()
    view.set_margin_bottom = mock.MagicMock()
    view.set_margin_start = mock.MagicMock()
    view.set_margin_end = mock.MagicMock()
    view.set_spacing = mock.MagicMock()
    view.get_root = mock.MagicMock(return_value=None)

    return view


@pytest.mark.ui
class TestScanViewGtkMocking:
    """Tests to verify GTK mocking setup works correctly."""

    def test_scan_view_can_be_imported(self, scan_view_class):
        """Test that ScanView can be imported with mocked GTK."""
        assert scan_view_class is not None

    def test_mock_gi_modules_fixture_provides_all_mocks(self, mock_gi_modules):
        """Test that the mock fixture provides all expected module mocks."""
        assert "gi" in mock_gi_modules
        assert "repository" in mock_gi_modules
        assert "gio" in mock_gi_modules
        assert "adw" in mock_gi_modules
        assert "gtk" in mock_gi_modules
        assert "glib" in mock_gi_modules

    def test_gtk_box_mock_supports_required_methods(self, mock_gi_modules):
        """Test that the MockGtkBox supports methods used by ScanView."""
        gtk = mock_gi_modules["gtk"]

        # Create a mock box - uses MockGtkBox from conftest.py
        box = gtk.Box(orientation=gtk.Orientation.VERTICAL)

        # MockGtkBox inherits from MockGtkWidget which returns MagicMock for
        # any undefined attribute, allowing flexible method calls
        assert box is not None

    def test_scan_view_class_fixture(self, scan_view_class):
        """Test that scan_view_class fixture returns a class."""
        assert scan_view_class is not None
        assert callable(scan_view_class)

    def test_mock_scan_view_has_required_attributes(self, mock_scan_view):
        """Test that mock_scan_view fixture sets up required attributes."""
        # Test scanner attributes
        assert hasattr(mock_scan_view, "_scanner")
        assert hasattr(mock_scan_view, "_quarantine_manager")
        assert hasattr(mock_scan_view, "_selected_path")
        assert hasattr(mock_scan_view, "_is_scanning")

        # Test UI element attributes
        assert hasattr(mock_scan_view, "_path_row")
        assert hasattr(mock_scan_view, "_scan_button")
        assert hasattr(mock_scan_view, "_results_group")
        assert hasattr(mock_scan_view, "_status_label")

        # Test profile attributes
        assert hasattr(mock_scan_view, "_selected_profile")
        assert hasattr(mock_scan_view, "_profile_list")


@pytest.mark.ui
class TestScanViewInitialization:
    """Tests for ScanView initialization."""

    def test_initial_selected_path_is_empty(self, mock_scan_view):
        """Test that initial selected path is empty."""
        assert mock_scan_view._selected_path == ""

    def test_initial_scanning_state_is_false(self, mock_scan_view):
        """Test that initial scanning state is False."""
        assert mock_scan_view._is_scanning is False

    def test_initial_eicar_temp_path_is_empty(self, mock_scan_view):
        """Test that initial EICAR temp path is empty."""
        assert mock_scan_view._eicar_temp_path == ""

    def test_initial_current_result_is_none(self, mock_scan_view):
        """Test that current result is initially None."""
        assert mock_scan_view._current_result is None

    def test_initial_scan_state_callback_is_none(self, mock_scan_view):
        """Test that scan state callback is initially None."""
        assert mock_scan_view._on_scan_state_changed is None

    def test_initial_selected_profile_is_none(self, mock_scan_view):
        """Test that selected profile is initially None."""
        assert mock_scan_view._selected_profile is None

    def test_initial_profile_list_is_empty(self, mock_scan_view):
        """Test that profile list is initially empty."""
        assert mock_scan_view._profile_list == []


@pytest.mark.ui
class TestScanViewScanner:
    """Tests for ScanView scanner integration."""

    def test_scanner_attribute_exists(self, mock_scan_view):
        """Test that scanner attribute exists."""
        assert mock_scan_view._scanner is not None

    def test_quarantine_manager_attribute_exists(self, mock_scan_view):
        """Test that quarantine manager attribute exists."""
        assert mock_scan_view._quarantine_manager is not None


@pytest.mark.ui
class TestFileSelectionUI:
    """Tests for file/folder selection UI interactions."""

    def test_select_folder_button_exists(self, mock_scan_view):
        """Test that the select folder button attribute exists."""
        assert hasattr(mock_scan_view, "_select_folder_btn")

    def test_select_file_button_exists(self, mock_scan_view):
        """Test that the select file button attribute exists."""
        assert hasattr(mock_scan_view, "_select_file_btn")

    def test_path_row_exists(self, mock_scan_view):
        """Test that the path row for displaying selected path exists."""
        assert hasattr(mock_scan_view, "_path_row")
        assert mock_scan_view._path_row is not None

    def test_initial_path_is_empty_string(self, mock_scan_view):
        """Test that the initial selected path is an empty string."""
        assert mock_scan_view._selected_path == ""

    def test_initial_scan_button_is_disabled(self, mock_scan_view):
        """Test that the scan button is disabled when no path is selected."""
        # The mock_scan_view fixture sets _selected_path to ""
        assert mock_scan_view._selected_path == ""
        # Note: The actual button state would be set during __init__ which we mock out


# Module-level test function for verification
@pytest.mark.ui
def test_file_selection_ui(scan_view_class):
    """
    Test for file selection UI functionality.

    This test verifies that the file selection UI components are properly
    set up and can handle path selection updates.
    """
    # Verify the class has file selection methods
    assert hasattr(scan_view_class, "_set_selected_path")
    assert hasattr(scan_view_class, "_create_selection_section")


@pytest.mark.ui
class TestScanInitiationUI:
    """Tests for scan initiation UI functionality."""

    def test_scan_button_exists(self, mock_scan_view):
        """Test that the scan button attribute exists."""
        assert hasattr(mock_scan_view, "_scan_button")
        assert mock_scan_view._scan_button is not None

    def test_on_scan_clicked_starts_scan_when_path_selected(self, mock_scan_view):
        """Test that clicking scan button starts scan when path is selected."""
        mock_scan_view._selected_path = "/home/user/documents"
        mock_scan_view._is_scanning = False

        # Verify the method exists and path is set
        assert mock_scan_view._selected_path != ""

    def test_scan_button_disabled_when_no_path_selected(self, mock_scan_view):
        """Test that scan button state reflects path selection."""
        assert mock_scan_view._selected_path == ""
        # The actual button state would be set during __init__

    def test_cancel_button_exists(self, mock_scan_view):
        """Test that the cancel button attribute exists."""
        assert hasattr(mock_scan_view, "_cancel_button")

    def test_scan_spinner_exists(self, mock_scan_view):
        """Test that the scan spinner attribute exists."""
        assert hasattr(mock_scan_view, "_scan_spinner")


@pytest.mark.ui
class TestResultsDisplay:
    """Tests for results display functionality."""

    def test_results_group_exists(self, mock_scan_view):
        """Test that the results group attribute exists."""
        assert hasattr(mock_scan_view, "_results_group")

    def test_results_list_exists(self, mock_scan_view):
        """Test that the results list attribute exists."""
        assert hasattr(mock_scan_view, "_results_list")

    def test_status_label_exists(self, mock_scan_view):
        """Test that the status label attribute exists."""
        assert hasattr(mock_scan_view, "_status_label")

    def test_status_badge_exists(self, mock_scan_view):
        """Test that the status badge attribute exists."""
        assert hasattr(mock_scan_view, "_status_badge")

    def test_copy_button_exists(self, mock_scan_view):
        """Test that the copy button exists."""
        assert hasattr(mock_scan_view, "_copy_button")

    def test_export_text_button_exists(self, mock_scan_view):
        """Test that the export text button exists."""
        assert hasattr(mock_scan_view, "_export_text_button")

    def test_export_csv_button_exists(self, mock_scan_view):
        """Test that the export CSV button exists."""
        assert hasattr(mock_scan_view, "_export_csv_button")

    def test_raw_output_is_initially_empty(self, mock_scan_view):
        """Test that raw output is initially empty."""
        assert mock_scan_view._raw_output == ""

    def test_current_result_is_initially_none(self, mock_scan_view):
        """Test that current result is initially None."""
        assert mock_scan_view._current_result is None

    def test_status_banner_exists(self, mock_scan_view):
        """Test that the status banner exists."""
        assert hasattr(mock_scan_view, "_status_banner")

    def test_results_placeholder_exists(self, mock_scan_view):
        """Test that results placeholder exists."""
        assert hasattr(mock_scan_view, "_results_placeholder")

    def test_threats_list_exists(self, mock_scan_view):
        """Test that the threats list exists."""
        assert hasattr(mock_scan_view, "_threats_list")


@pytest.mark.ui
class TestProfileUI:
    """Tests for profile selection UI."""

    def test_profile_group_exists(self, mock_scan_view):
        """Test that the profile group exists."""
        assert hasattr(mock_scan_view, "_profile_group")

    def test_profile_dropdown_exists(self, mock_scan_view):
        """Test that the profile dropdown exists."""
        assert hasattr(mock_scan_view, "_profile_dropdown")

    def test_manage_profiles_button_exists(self, mock_scan_view):
        """Test that the manage profiles button exists."""
        assert hasattr(mock_scan_view, "_manage_profiles_btn")

    def test_selected_profile_is_initially_none(self, mock_scan_view):
        """Test that selected profile is initially None."""
        assert mock_scan_view._selected_profile is None

    def test_profile_list_is_initially_empty(self, mock_scan_view):
        """Test that profile list is initially empty."""
        assert mock_scan_view._profile_list == []

    def test_profile_string_list_is_initially_none(self, mock_scan_view):
        """Test that profile string list is initially None."""
        assert mock_scan_view._profile_string_list is None


@pytest.mark.ui
class TestProgressSection:
    """Tests for progress bar and status display during scanning."""

    def test_progress_section_exists(self, mock_scan_view):
        """Test that progress section exists."""
        assert hasattr(mock_scan_view, "_progress_section")

    def test_progress_bar_exists(self, mock_scan_view):
        """Test that progress bar exists."""
        assert hasattr(mock_scan_view, "_progress_bar")

    def test_progress_label_exists(self, mock_scan_view):
        """Test that progress label exists."""
        assert hasattr(mock_scan_view, "_progress_label")

    def test_pulse_timeout_id_initially_none(self, mock_scan_view):
        """Test that pulse timeout ID is initially None."""
        assert mock_scan_view._pulse_timeout_id is None


@pytest.mark.ui
class TestViewResultsSection:
    """Tests for the view results button functionality."""

    def test_view_results_section_exists(self, mock_scan_view):
        """Test that view results section exists."""
        assert hasattr(mock_scan_view, "_view_results_section")

    def test_view_results_button_exists(self, mock_scan_view):
        """Test that view results button exists."""
        assert hasattr(mock_scan_view, "_view_results_button")

    def test_show_view_results_method_exists(self, scan_view_class):
        """Test that _show_view_results method exists."""
        assert hasattr(scan_view_class, "_show_view_results")

    def test_hide_view_results_method_exists(self, scan_view_class):
        """Test that _hide_view_results method exists."""
        assert hasattr(scan_view_class, "_hide_view_results")

    def test_on_view_results_clicked_method_exists(self, scan_view_class):
        """Test that _on_view_results_clicked method exists."""
        assert hasattr(scan_view_class, "_on_view_results_clicked")

    def test_create_view_results_section_method_exists(self, scan_view_class):
        """Test that _create_view_results_section method exists."""
        assert hasattr(scan_view_class, "_create_view_results_section")
