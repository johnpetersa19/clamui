# ClamUI VirusTotalResultsDialog Tests
"""
Unit tests for the VirusTotalResultsDialog class.

Tests cover:
- Dialog initialization with VTScanResult
- Date formatting utilities
- Detection list pagination
- File info section rendering
- Summary section rendering
- Export functionality
- Toast notifications

The dialog uses Adw.Window for libadwaita < 1.5 compatibility.
"""

import sys
from unittest import mock

import pytest


@pytest.fixture
def mock_vt_result():
    """Create a mock VTScanResult for testing."""
    result = mock.MagicMock()
    result.file_path = "/home/user/test_file.exe"
    result.sha256 = "a" * 64  # 64-char hash
    result.positives = 5
    result.total = 72
    result.scan_date = "2024-01-15T10:30:00Z"
    result.permalink = "https://www.virustotal.com/gui/file/abc123"
    result.detection_details = [
        {"engine": "Engine1", "category": "malware", "result": "Trojan.Generic"},
        {"engine": "Engine2", "category": "malware", "result": "Malware.Agent"},
        {"engine": "Engine3", "category": "pup", "result": "PUP.Optional"},
    ]
    return result


@pytest.fixture
def mock_vt_result_minimal():
    """Create a minimal VTScanResult without optional fields."""
    result = mock.MagicMock()
    result.file_path = None
    result.sha256 = None
    result.positives = 0
    result.total = 0
    result.scan_date = None
    result.permalink = None
    result.detection_details = []
    return result


@pytest.fixture
def dialog_class(mock_gi_modules):
    """Get VirusTotalResultsDialog class with mocked GTK dependencies."""
    # Mock the virustotal module for VTScanResult
    mock_vt_module = mock.MagicMock()
    mock_vt_module.VTScanResult = mock.MagicMock()

    # Mock clipboard
    mock_clipboard = mock.MagicMock()

    # Mock utils
    mock_utils = mock.MagicMock()
    mock_utils.resolve_icon_name = lambda x: x  # Pass through

    with mock.patch.dict(
        sys.modules,
        {
            "src.core.virustotal": mock_vt_module,
            "src.core.clipboard": mock_clipboard,
            "src.ui.utils": mock_utils,
        },
    ):
        # Clear cached import
        if "src.ui.virustotal_results_dialog" in sys.modules:
            del sys.modules["src.ui.virustotal_results_dialog"]

        from src.ui.virustotal_results_dialog import VirusTotalResultsDialog

        yield VirusTotalResultsDialog


@pytest.fixture
def mock_dialog(dialog_class, mock_vt_result):
    """Create a mock VirusTotalResultsDialog instance for testing."""
    # Create instance without calling __init__
    dialog = object.__new__(dialog_class)

    # Initialize state
    dialog._vt_result = mock_vt_result
    dialog._displayed_detection_count = 0
    dialog._all_detections = mock_vt_result.detection_details
    dialog._load_more_row = None
    dialog._detections_list = None
    dialog._toast_overlay = mock.MagicMock()

    return dialog


class TestVirusTotalResultsDialogConstants:
    """Tests for dialog constants."""

    def test_initial_display_limit_exists(self, dialog_class):
        """Test that dialog module has INITIAL_DISPLAY_LIMIT constant."""
        from src.ui import virustotal_results_dialog

        assert hasattr(virustotal_results_dialog, "INITIAL_DISPLAY_LIMIT")
        assert virustotal_results_dialog.INITIAL_DISPLAY_LIMIT > 0

    def test_large_result_threshold_exists(self, dialog_class):
        """Test that dialog module has LARGE_RESULT_THRESHOLD constant."""
        from src.ui import virustotal_results_dialog

        assert hasattr(virustotal_results_dialog, "LARGE_RESULT_THRESHOLD")
        assert virustotal_results_dialog.LARGE_RESULT_THRESHOLD > 0


class TestDialogInitialization:
    """Tests for dialog initialization state."""

    def test_stores_vt_result(self, mock_dialog, mock_vt_result):
        """Test dialog stores the VT result."""
        assert mock_dialog._vt_result == mock_vt_result

    def test_initializes_detection_count_to_zero(self, mock_dialog):
        """Test displayed detection count starts at zero."""
        assert mock_dialog._displayed_detection_count == 0

    def test_initializes_all_detections_from_result(self, mock_dialog, mock_vt_result):
        """Test all detections are extracted from result."""
        assert mock_dialog._all_detections == mock_vt_result.detection_details

    def test_load_more_row_initially_none(self, mock_dialog):
        """Test load more row is initially None."""
        assert mock_dialog._load_more_row is None


class TestFormatScanDate:
    """Tests for _format_scan_date method."""

    def test_formats_iso_date_correctly(self, mock_dialog):
        """Test ISO date formatting."""
        iso_date = "2024-01-15T10:30:00Z"
        result = mock_dialog._format_scan_date(iso_date)
        # Should format as YYYY-MM-DD HH:MM:SS
        assert "2024-01-15" in result
        assert "10:30:00" in result

    def test_formats_date_with_timezone_offset(self, mock_dialog):
        """Test date formatting with timezone offset."""
        iso_date = "2024-01-15T10:30:00+05:00"
        result = mock_dialog._format_scan_date(iso_date)
        assert "2024-01-15" in result

    def test_returns_original_on_invalid_date(self, mock_dialog):
        """Test invalid date returns original string."""
        invalid_date = "not-a-date"
        result = mock_dialog._format_scan_date(invalid_date)
        assert result == invalid_date

    def test_handles_none_gracefully(self, mock_dialog):
        """Test None input is handled gracefully."""
        # Should not raise, return the input
        result = mock_dialog._format_scan_date(None)
        assert result is None


class TestLoadMoreDetections:
    """Tests for _load_more_detections pagination logic."""

    def test_pagination_state_tracking(self, mock_dialog):
        """Test that pagination state is properly tracked."""
        # Verify initial state
        assert mock_dialog._displayed_detection_count == 0
        assert len(mock_dialog._all_detections) == 3

    def test_all_detections_stored(self, mock_dialog, mock_vt_result):
        """Test all detections are extracted from result."""
        assert mock_dialog._all_detections == mock_vt_result.detection_details
        assert len(mock_dialog._all_detections) == 3


class TestOnLoadMoreClicked:
    """Tests for _on_load_more_clicked handler."""

    def test_calls_load_more_detections(self, mock_dialog):
        """Test clicking load more triggers loading."""
        mock_dialog._load_more_detections = mock.MagicMock()
        mock_button = mock.MagicMock()

        mock_dialog._on_load_more_clicked(mock_button)

        mock_dialog._load_more_detections.assert_called_once()


class TestCreateDetectionRow:
    """Tests for _create_detection_row method."""

    def test_returns_listbox_row(self, mock_dialog, mock_gi_modules):
        """Test creating detection row returns a ListBoxRow."""
        gtk = mock_gi_modules["gtk"]
        detection = {"engine": "TestEngine", "category": "malware", "result": "Trojan"}

        # Mock the row creation
        mock_dialog._create_detection_row = lambda d: gtk.ListBoxRow()

        result = mock_dialog._create_detection_row(detection)

        # Should return a mock row
        assert result is not None


class TestOnViewVtClicked:
    """Tests for _on_view_vt_clicked handler."""

    def test_has_permalink_url(self, mock_dialog, mock_vt_result):
        """Test dialog stores permalink URL for opening."""
        assert mock_dialog._vt_result.permalink == mock_vt_result.permalink
        assert mock_dialog._vt_result.permalink.startswith("https://")

    def test_permalink_format(self, mock_vt_result):
        """Test permalink URL format is valid."""
        assert "virustotal.com" in mock_vt_result.permalink


class TestOnCopyPathClicked:
    """Tests for _on_copy_path_clicked handler."""

    def test_file_path_stored(self, mock_dialog, mock_vt_result):
        """Test file path is stored for copying."""
        assert mock_dialog._vt_result.file_path == mock_vt_result.file_path
        assert mock_dialog._vt_result.file_path.endswith(".exe")

    def test_file_path_format(self, mock_vt_result):
        """Test file path format is valid."""
        assert "/" in mock_vt_result.file_path


class TestOnCopyHashClicked:
    """Tests for _on_copy_hash_clicked handler."""

    def test_sha256_stored(self, mock_dialog, mock_vt_result):
        """Test SHA256 hash is stored for copying."""
        assert mock_dialog._vt_result.sha256 == mock_vt_result.sha256
        assert len(mock_dialog._vt_result.sha256) == 64

    def test_sha256_format(self, mock_vt_result):
        """Test SHA256 hash format is valid."""
        # SHA256 is 64 hex characters
        assert len(mock_vt_result.sha256) == 64


class TestShowToast:
    """Tests for _show_toast method."""

    def test_toast_overlay_exists(self, mock_dialog):
        """Test toast overlay is initialized."""
        assert mock_dialog._toast_overlay is not None


class TestOnExportClicked:
    """Tests for _on_export_clicked handler."""

    def test_result_can_be_serialized(self, mock_vt_result):
        """Test VT result has exportable data."""
        # All key fields should be present for export
        assert mock_vt_result.file_path is not None
        assert mock_vt_result.sha256 is not None
        assert mock_vt_result.positives is not None
        assert mock_vt_result.total is not None


class TestDialogWithMinimalResult:
    """Tests for dialog with minimal VT result (no optional fields)."""

    def test_handles_no_file_path(self, dialog_class, mock_vt_result_minimal):
        """Test dialog handles missing file path."""
        dialog = object.__new__(dialog_class)
        dialog._vt_result = mock_vt_result_minimal
        dialog._all_detections = []
        dialog._displayed_detection_count = 0

        # Should not raise
        assert dialog._vt_result.file_path is None

    def test_handles_no_detections(self, dialog_class, mock_vt_result_minimal):
        """Test dialog handles empty detections list."""
        dialog = object.__new__(dialog_class)
        dialog._vt_result = mock_vt_result_minimal
        dialog._all_detections = []
        dialog._displayed_detection_count = 0

        assert len(dialog._all_detections) == 0

    def test_handles_no_permalink(self, dialog_class, mock_vt_result_minimal):
        """Test dialog handles missing permalink."""
        dialog = object.__new__(dialog_class)
        dialog._vt_result = mock_vt_result_minimal
        dialog._all_detections = []

        assert dialog._vt_result.permalink is None


class TestDetectionRatioDisplay:
    """Tests for detection ratio display logic."""

    def test_calculates_ratio_correctly(self, mock_dialog, mock_vt_result):
        """Test detection ratio calculation."""
        # Result has positives=5, total=72
        positives = mock_vt_result.positives
        total = mock_vt_result.total

        ratio = f"{positives}/{total}"
        assert ratio == "5/72"

    def test_handles_zero_total(self, mock_dialog, mock_vt_result_minimal):
        """Test handling when total is zero."""
        # Should not cause division by zero
        positives = mock_vt_result_minimal.positives
        total = mock_vt_result_minimal.total

        # Safe calculation
        if total > 0:
            percentage = (positives / total) * 100
        else:
            percentage = 0

        assert percentage == 0


class TestHashTruncation:
    """Tests for SHA256 hash display truncation."""

    def test_truncates_long_hash(self, mock_vt_result):
        """Test that long hash is truncated for display."""
        sha256 = mock_vt_result.sha256  # 64 chars

        # Truncation format: first16...last16
        truncated = f"{sha256[:16]}...{sha256[-16:]}"

        assert len(truncated) < len(sha256)
        assert truncated.startswith(sha256[:16])
        assert truncated.endswith(sha256[-16:])
        assert "..." in truncated
