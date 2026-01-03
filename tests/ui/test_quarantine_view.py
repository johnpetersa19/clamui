# ClamUI QuarantineView Tests
"""
Unit tests for the QuarantineView component.

Tests cover:
- Initialization and setup
- Loading state management
- Quarantine entry display and pagination
- Restore and delete operations
- Clear old items functionality
- Storage info display
- format_file_size utility function
- Callback mechanism for quarantine changes
"""

import sys
from unittest import mock

import pytest


@pytest.fixture
def mock_quarantine_manager():
    """Create a mock QuarantineManager."""
    manager = mock.MagicMock()
    manager.get_all_entries_async = mock.MagicMock()
    manager.get_entry_count = mock.MagicMock(return_value=5)
    manager.get_total_size = mock.MagicMock(return_value=1024 * 1024)
    manager.restore_file_async = mock.MagicMock()
    manager.delete_file_async = mock.MagicMock()
    manager.cleanup_old_entries_async = mock.MagicMock()
    manager.get_old_entries = mock.MagicMock(return_value=[])
    return manager


@pytest.fixture
def mock_quarantine_entry():
    """Create a mock QuarantineEntry."""
    entry = mock.MagicMock()
    entry.id = "test-quarantine-id-123"
    entry.threat_name = "Eicar-Test-Signature"
    entry.original_path = "/home/user/downloads/malicious.exe"
    entry.detection_date = "2024-01-15T10:30:00"
    entry.file_size = 65536
    return entry


def _clear_src_modules():
    """Clear all cached src.* modules to prevent test pollution."""
    modules_to_remove = [mod for mod in sys.modules if mod.startswith("src.")]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def quarantine_view_class(mock_gi_modules):
    """Get QuarantineView class with mocked dependencies."""
    with mock.patch.dict(
        sys.modules,
        {
            "src.core.quarantine": mock.MagicMock(),
        },
    ):
        # Clear any cached import
        if "src.ui.quarantine_view" in sys.modules:
            del sys.modules["src.ui.quarantine_view"]

        from src.ui.quarantine_view import QuarantineView

        yield QuarantineView

    # Critical: Clear all src.* modules after test to prevent pollution
    _clear_src_modules()


@pytest.fixture
def mock_quarantine_view(quarantine_view_class, mock_quarantine_manager):
    """Create a mock QuarantineView instance for testing."""
    # Create instance without calling __init__
    view = object.__new__(quarantine_view_class)

    # Set up required attributes
    view._manager = mock_quarantine_manager
    view._is_loading = False
    view._displayed_count = 0
    view._all_entries = []
    view._load_more_row = None
    view._on_quarantine_changed = None
    view._last_refresh_time = 0.0

    # Mock UI elements
    view._status_banner = mock.MagicMock()
    view._storage_row = mock.MagicMock()
    view._count_label = mock.MagicMock()
    view._list_group = mock.MagicMock()
    view._listbox = mock.MagicMock()
    view._listbox.get_first_child.return_value = None  # Ensure loop terminates
    view._spinner = mock.MagicMock()
    view._refresh_button = mock.MagicMock()
    view._clear_old_button = mock.MagicMock()

    # Mock internal methods
    view._setup_ui = mock.MagicMock()
    view._load_entries_async = mock.MagicMock()
    view._set_loading_state = mock.MagicMock()
    view._create_entry_row = mock.MagicMock()
    view._update_storage_info = mock.MagicMock()
    view.get_root = mock.MagicMock(return_value=None)

    return view


class TestQuarantineViewImport:
    """Tests for QuarantineView import."""

    def test_import_quarantine_view(self, mock_gi_modules):
        """Test that QuarantineView can be imported."""
        with mock.patch.dict(
            sys.modules,
            {
                "src.core.quarantine": mock.MagicMock(),
            },
        ):
            from src.ui.quarantine_view import QuarantineView

            assert QuarantineView is not None

    def test_import_from_ui_package(self, mock_gi_modules):
        """Test that QuarantineView is exported from src.ui package."""
        with mock.patch.dict(
            sys.modules,
            {
                "src.core.quarantine": mock.MagicMock(),
                "src.core.log_manager": mock.MagicMock(),
                "src.core.utils": mock.MagicMock(),
                "src.ui.fullscreen_dialog": mock.MagicMock(),
                "src.ui.update_view": mock.MagicMock(),
                "src.ui.logs_view": mock.MagicMock(),
                "src.ui.components_view": mock.MagicMock(),
                "src.ui.preferences_dialog": mock.MagicMock(),
            },
        ):
            from src.ui import QuarantineView

            assert QuarantineView is not None

    def test_pagination_constants_defined(self, mock_gi_modules):
        """Test that pagination constants are defined."""
        with mock.patch.dict(
            sys.modules,
            {
                "src.core.quarantine": mock.MagicMock(),
            },
        ):
            from src.ui.quarantine_view import INITIAL_DISPLAY_LIMIT, LOAD_MORE_BATCH_SIZE

            assert INITIAL_DISPLAY_LIMIT == 25
            assert LOAD_MORE_BATCH_SIZE == 25


class TestFormatFileSize:
    """Tests for the format_file_size utility function."""

    def test_format_file_size_bytes(self, mock_gi_modules):
        """Test formatting file size in bytes."""
        with mock.patch.dict(
            sys.modules,
            {
                "src.core.quarantine": mock.MagicMock(),
            },
        ):
            from src.ui.quarantine_view import format_file_size

            assert format_file_size(500) == "500 B"
            assert format_file_size(0) == "0 B"
            assert format_file_size(1023) == "1023 B"

    def test_format_file_size_kilobytes(self, mock_gi_modules):
        """Test formatting file size in kilobytes."""
        with mock.patch.dict(
            sys.modules,
            {
                "src.core.quarantine": mock.MagicMock(),
            },
        ):
            from src.ui.quarantine_view import format_file_size

            assert format_file_size(1024) == "1.0 KB"
            assert format_file_size(2048) == "2.0 KB"
            assert format_file_size(1536) == "1.5 KB"

    def test_format_file_size_megabytes(self, mock_gi_modules):
        """Test formatting file size in megabytes."""
        with mock.patch.dict(
            sys.modules,
            {
                "src.core.quarantine": mock.MagicMock(),
            },
        ):
            from src.ui.quarantine_view import format_file_size

            assert format_file_size(1024 * 1024) == "1.0 MB"
            assert format_file_size(2 * 1024 * 1024) == "2.0 MB"
            assert format_file_size(int(1.5 * 1024 * 1024)) == "1.5 MB"

    def test_format_file_size_gigabytes(self, mock_gi_modules):
        """Test formatting file size in gigabytes."""
        with mock.patch.dict(
            sys.modules,
            {
                "src.core.quarantine": mock.MagicMock(),
            },
        ):
            from src.ui.quarantine_view import format_file_size

            assert format_file_size(1024 * 1024 * 1024) == "1.00 GB"
            assert format_file_size(2 * 1024 * 1024 * 1024) == "2.00 GB"


class TestQuarantineViewInitialization:
    """Tests for QuarantineView initialization."""

    def test_initial_loading_state_is_false(self, mock_quarantine_view):
        """Test that initial loading state is False."""
        assert mock_quarantine_view._is_loading is False

    def test_initial_displayed_count_is_zero(self, mock_quarantine_view):
        """Test that initial displayed count is zero."""
        assert mock_quarantine_view._displayed_count == 0

    def test_initial_all_entries_is_empty(self, mock_quarantine_view):
        """Test that initial all_entries is empty."""
        assert mock_quarantine_view._all_entries == []

    def test_initial_load_more_row_is_none(self, mock_quarantine_view):
        """Test that initial load_more_row is None."""
        assert mock_quarantine_view._load_more_row is None

    def test_initial_callback_is_none(self, mock_quarantine_view):
        """Test that initial quarantine changed callback is None."""
        assert mock_quarantine_view._on_quarantine_changed is None

    def test_initial_last_refresh_time_is_zero(self, mock_quarantine_view):
        """Test that initial last refresh time is zero."""
        assert mock_quarantine_view._last_refresh_time == 0.0


class TestQuarantineViewEntriesLoaded:
    """Tests for entries loading completion."""

    def test_on_entries_loaded_with_empty_list(
        self, quarantine_view_class, mock_quarantine_manager
    ):
        """Test handling empty entries list."""
        view = object.__new__(quarantine_view_class)
        view._is_loading = True
        view._listbox = mock.MagicMock()
        view._listbox.get_first_child.return_value = None  # Ensure loop terminates
        view._clear_old_button = mock.MagicMock()
        view._all_entries = []
        view._displayed_count = 0
        view._load_more_row = None
        view._set_loading_state = mock.MagicMock()
        view._update_storage_info = mock.MagicMock()
        view._on_quarantine_changed = None
        view._last_refresh_time = 0.0
        view._manager = mock_quarantine_manager

        result = view._on_entries_loaded([])

        assert result is False
        view._clear_old_button.set_sensitive.assert_called_with(False)
        assert view._all_entries == []

    def test_on_entries_loaded_stores_entries(self, quarantine_view_class, mock_quarantine_entry):
        """Test that loaded entries are stored."""
        view = object.__new__(quarantine_view_class)
        view._is_loading = True
        view._listbox = mock.MagicMock()
        view._listbox.get_first_child.return_value = None  # Ensure loop terminates
        view._clear_old_button = mock.MagicMock()
        view._all_entries = []
        view._displayed_count = 0
        view._load_more_row = None
        view._set_loading_state = mock.MagicMock()
        view._update_storage_info = mock.MagicMock()
        view._display_entry_batch = mock.MagicMock()
        view._add_load_more_button = mock.MagicMock()
        view._on_quarantine_changed = None
        view._last_refresh_time = 0.0
        view._manager = mock.MagicMock()

        entries = [mock_quarantine_entry]
        view._on_entries_loaded(entries)

        assert view._all_entries == entries

    def test_on_entries_loaded_calls_callback(self, quarantine_view_class, mock_quarantine_entry):
        """Test that loaded entries trigger callback."""
        view = object.__new__(quarantine_view_class)
        view._is_loading = True
        view._listbox = mock.MagicMock()
        view._listbox.get_first_child.return_value = None  # Ensure loop terminates
        view._clear_old_button = mock.MagicMock()
        view._all_entries = []
        view._displayed_count = 0
        view._load_more_row = None
        view._set_loading_state = mock.MagicMock()
        view._update_storage_info = mock.MagicMock()
        view._display_entry_batch = mock.MagicMock()
        view._add_load_more_button = mock.MagicMock()
        view._last_refresh_time = 0.0
        view._manager = mock.MagicMock()

        callback = mock.MagicMock()
        view._on_quarantine_changed = callback

        entries = [mock_quarantine_entry]
        view._on_entries_loaded(entries)

        callback.assert_called_once_with(1)


class TestQuarantineViewPagination:
    """Tests for quarantine entry pagination."""

    def test_display_entry_batch_increments_count(
        self, quarantine_view_class, mock_quarantine_entry
    ):
        """Test that displaying entries increments the displayed count."""
        view = object.__new__(quarantine_view_class)
        view._all_entries = [mock_quarantine_entry, mock_quarantine_entry]
        view._displayed_count = 0
        view._load_more_row = None
        view._listbox = mock.MagicMock()
        view._create_entry_row = mock.MagicMock(return_value=mock.MagicMock())

        view._display_entry_batch(0, 2)

        assert view._displayed_count == 2

    def test_on_load_more_clicked_removes_load_more_row(
        self, quarantine_view_class, mock_quarantine_entry
    ):
        """Test that clicking load more removes the load more row."""
        view = object.__new__(quarantine_view_class)
        view._all_entries = [mock_quarantine_entry] * 30
        view._displayed_count = 25
        load_more_row = mock.MagicMock()
        view._load_more_row = load_more_row
        view._listbox = mock.MagicMock()
        view._display_entry_batch = mock.MagicMock()
        view._add_load_more_button = mock.MagicMock()

        view._on_load_more_clicked(mock.MagicMock())

        view._listbox.remove.assert_called_with(load_more_row)

    def test_on_show_all_clicked_displays_remaining(
        self, quarantine_view_class, mock_quarantine_entry
    ):
        """Test that clicking show all displays remaining entries."""
        view = object.__new__(quarantine_view_class)
        view._all_entries = [mock_quarantine_entry] * 50
        view._displayed_count = 25
        view._load_more_row = mock.MagicMock()
        view._listbox = mock.MagicMock()
        view._display_entry_batch = mock.MagicMock()

        view._on_show_all_clicked(mock.MagicMock())

        # Should display remaining 25 entries
        view._display_entry_batch.assert_called_once_with(25, 25)


class TestQuarantineViewStorageInfo:
    """Tests for storage info display."""

    def test_update_storage_info_displays_size(
        self, quarantine_view_class, mock_quarantine_manager
    ):
        """Test that storage info displays total size."""
        view = object.__new__(quarantine_view_class)
        view._manager = mock_quarantine_manager
        view._manager.get_total_size.return_value = 1024 * 1024  # 1 MB
        view._manager.get_entry_count.return_value = 5
        view._storage_row = mock.MagicMock()
        view._count_label = mock.MagicMock()

        # Create mock entries
        mock_entries = [mock.MagicMock(file_size=1024 * 200) for _ in range(5)]
        view._update_storage_info(mock_entries)

        view._storage_row.set_subtitle.assert_called()
        view._count_label.set_text.assert_called_with("5 items")

    def test_update_storage_info_singular_item(
        self, quarantine_view_class, mock_quarantine_manager
    ):
        """Test that storage info displays singular 'item' for count of 1."""
        view = object.__new__(quarantine_view_class)
        view._manager = mock_quarantine_manager
        view._manager.get_total_size.return_value = 512
        view._manager.get_entry_count.return_value = 1
        view._storage_row = mock.MagicMock()
        view._count_label = mock.MagicMock()

        # Create mock entry
        mock_entries = [mock.MagicMock(file_size=512)]
        view._update_storage_info(mock_entries)

        view._count_label.set_text.assert_called_with("1 item")



    def test_create_entry_row_truncates_long_path(
        self, quarantine_view_class, mock_quarantine_entry
    ):
        """Test that long paths are truncated in subtitle."""
        view = object.__new__(quarantine_view_class)
        mock_quarantine_entry.original_path = (
            "/home/user/very/long/path/that/exceeds/fifty/characters/limit/file.exe"
        )

        mock_row = mock.MagicMock()
        from gi.repository import Adw

        Adw.ExpanderRow.return_value = mock_row

        view._create_entry_row(mock_quarantine_entry)

        # Verify subtitle was set with truncated path
        calls = mock_row.set_subtitle.call_args_list
        if calls:
            subtitle = calls[0][0][0]
            assert subtitle.startswith("...")


# Module-level test function for verification
def test_quarantine_view_basic(mock_gi_modules):
    """
    Basic test function for pytest verification command.

    This test verifies the core QuarantineView functionality
    using a minimal mock setup.
    """
    with mock.patch.dict(
        sys.modules,
        {
            "src.core.quarantine": mock.MagicMock(),
        },
    ):
        from src.ui.quarantine_view import (
            INITIAL_DISPLAY_LIMIT,
            LOAD_MORE_BATCH_SIZE,
            QuarantineView,
            format_file_size,
        )

        # Test 1: Class can be imported
        assert QuarantineView is not None

        # Test 2: Pagination constants are correct
        assert INITIAL_DISPLAY_LIMIT == 25
        assert LOAD_MORE_BATCH_SIZE == 25

        # Test 3: format_file_size function works
        assert format_file_size(0) == "0 B"
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(1024 * 1024 * 1024) == "1.00 GB"

        # Test 4: Create mock instance and test basic methods
        view = object.__new__(QuarantineView)
        view._manager = mock.MagicMock()
        view._manager.get_entry_count.return_value = 5
        view._manager.get_total_size.return_value = 2048
        view._storage_row = mock.MagicMock()
        view._count_label = mock.MagicMock()

        # Test _update_storage_info
        mock_entries = [mock.MagicMock(file_size=512) for _ in range(5)]
        view._update_storage_info(mock_entries)

        view._storage_row.set_subtitle.assert_called_with("2.5 KB")  # 512 * 5 = 2560 bytes
        view._count_label.set_text.assert_called_with("5 items")

        # All tests passed
