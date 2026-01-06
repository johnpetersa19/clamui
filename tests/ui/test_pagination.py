# ClamUI Pagination Controller Tests
"""
Unit tests for the PaginatedListController component.

Tests cover:
- Initialization with default and custom parameters
- State management and reset functionality
- Property access (displayed_count, all_entries, load_more_row, entries_to_display)
- Configuration validation
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
def pagination_controller_class(mock_gi_modules):
    """Get PaginatedListController class with mocked dependencies."""
    # Clear any cached import of pagination module
    if "src.ui.pagination" in sys.modules:
        del sys.modules["src.ui.pagination"]

    from src.ui.pagination import PaginatedListController

    yield PaginatedListController

    # Critical: Clear all src.* modules after test to prevent pollution
    _clear_src_modules()


@pytest.fixture
def mock_listbox(mock_gi_modules):
    """Create a mock GTK ListBox."""
    return mock.MagicMock()


@pytest.fixture
def mock_scrolled_window(mock_gi_modules):
    """Create a mock GTK ScrolledWindow."""
    return mock.MagicMock()


@pytest.fixture
def mock_row_factory():
    """Create a mock row factory callback."""
    return mock.MagicMock(return_value=mock.MagicMock())


@pytest.fixture
def pagination_controller(
    pagination_controller_class, mock_listbox, mock_scrolled_window, mock_row_factory
):
    """Create a PaginatedListController instance with default parameters."""
    return pagination_controller_class(
        listbox=mock_listbox,
        scrolled_window=mock_scrolled_window,
        row_factory=mock_row_factory,
    )


class TestPaginationControllerImport:
    """Tests for PaginatedListController import."""

    def test_import_pagination_controller(self, mock_gi_modules):
        """Test that PaginatedListController can be imported."""
        from src.ui.pagination import PaginatedListController

        assert PaginatedListController is not None

    def test_default_constants_defined(self, mock_gi_modules):
        """Test that default pagination constants are defined."""
        from src.ui.pagination import PaginatedListController

        assert PaginatedListController.DEFAULT_INITIAL_LIMIT == 25
        assert PaginatedListController.DEFAULT_BATCH_SIZE == 25


class TestPaginationControllerInitialization:
    """Tests for PaginatedListController initialization."""

    def test_initialization_with_default_limits(
        self, pagination_controller_class, mock_listbox, mock_scrolled_window, mock_row_factory
    ):
        """Test initialization with default initial_limit and batch_size."""
        controller = pagination_controller_class(
            listbox=mock_listbox,
            scrolled_window=mock_scrolled_window,
            row_factory=mock_row_factory,
        )

        assert controller._initial_limit == 25
        assert controller._batch_size == 25
        assert controller._listbox is mock_listbox
        assert controller._scrolled_window is mock_scrolled_window
        assert controller._row_factory is mock_row_factory

    def test_initialization_with_custom_limits(
        self, pagination_controller_class, mock_listbox, mock_scrolled_window, mock_row_factory
    ):
        """Test initialization with custom initial_limit and batch_size."""
        controller = pagination_controller_class(
            listbox=mock_listbox,
            scrolled_window=mock_scrolled_window,
            row_factory=mock_row_factory,
            initial_limit=50,
            batch_size=20,
        )

        assert controller._initial_limit == 50
        assert controller._batch_size == 20

    def test_initial_state_is_empty(self, pagination_controller):
        """Test that initial pagination state is empty."""
        assert pagination_controller._displayed_count == 0
        assert pagination_controller._all_entries == []
        assert pagination_controller._load_more_row is None

    def test_initial_displayed_count_is_zero(self, pagination_controller):
        """Test that initial displayed count is zero."""
        assert pagination_controller.displayed_count == 0

    def test_initial_all_entries_is_empty(self, pagination_controller):
        """Test that initial all_entries is empty list."""
        assert pagination_controller.all_entries == []

    def test_initial_load_more_row_is_none(self, pagination_controller):
        """Test that initial load_more_row is None."""
        assert pagination_controller.load_more_row is None


class TestPaginationControllerStateManagement:
    """Tests for state management and reset functionality."""

    def test_reset_state_clears_displayed_count(self, pagination_controller):
        """Test that reset_state clears displayed_count."""
        pagination_controller._displayed_count = 25
        pagination_controller.reset_state()

        assert pagination_controller._displayed_count == 0

    def test_reset_state_clears_all_entries(self, pagination_controller):
        """Test that reset_state clears all_entries."""
        pagination_controller._all_entries = ["entry1", "entry2", "entry3"]
        pagination_controller.reset_state()

        assert pagination_controller._all_entries == []

    def test_reset_state_clears_load_more_row(self, pagination_controller):
        """Test that reset_state clears load_more_row."""
        pagination_controller._load_more_row = mock.MagicMock()
        pagination_controller.reset_state()

        assert pagination_controller._load_more_row is None

    def test_reset_state_clears_all_state_together(self, pagination_controller):
        """Test that reset_state clears all pagination state in one call."""
        pagination_controller._displayed_count = 50
        pagination_controller._all_entries = ["entry1", "entry2"]
        pagination_controller._load_more_row = mock.MagicMock()

        pagination_controller.reset_state()

        assert pagination_controller._displayed_count == 0
        assert pagination_controller._all_entries == []
        assert pagination_controller._load_more_row is None

    def test_reset_state_does_not_modify_listbox(
        self, pagination_controller, mock_listbox
    ):
        """Test that reset_state does not modify the listbox."""
        pagination_controller._displayed_count = 10
        pagination_controller._all_entries = ["entry1"]

        pagination_controller.reset_state()

        # Listbox should not be touched during reset_state
        mock_listbox.remove.assert_not_called()
        mock_listbox.append.assert_not_called()

    def test_reset_state_multiple_times(self, pagination_controller):
        """Test that reset_state can be called multiple times safely."""
        pagination_controller._displayed_count = 10
        pagination_controller._all_entries = ["entry1"]
        pagination_controller._load_more_row = mock.MagicMock()

        pagination_controller.reset_state()
        pagination_controller.reset_state()  # Second call

        assert pagination_controller._displayed_count == 0
        assert pagination_controller._all_entries == []
        assert pagination_controller._load_more_row is None


class TestPaginationControllerProperties:
    """Tests for property access methods."""

    def test_displayed_count_property_returns_count(self, pagination_controller):
        """Test that displayed_count property returns the internal count."""
        pagination_controller._displayed_count = 42
        assert pagination_controller.displayed_count == 42

    def test_displayed_count_property_reflects_changes(self, pagination_controller):
        """Test that displayed_count property reflects state changes."""
        assert pagination_controller.displayed_count == 0

        pagination_controller._displayed_count = 10
        assert pagination_controller.displayed_count == 10

        pagination_controller._displayed_count = 25
        assert pagination_controller.displayed_count == 25

    def test_all_entries_property_returns_entries(self, pagination_controller):
        """Test that all_entries property returns the internal entries list."""
        entries = ["entry1", "entry2", "entry3"]
        pagination_controller._all_entries = entries
        assert pagination_controller.all_entries == entries

    def test_all_entries_property_returns_same_reference(self, pagination_controller):
        """Test that all_entries property returns the same list reference."""
        entries = ["entry1", "entry2"]
        pagination_controller._all_entries = entries
        assert pagination_controller.all_entries is entries

    def test_load_more_row_property_returns_row(self, pagination_controller):
        """Test that load_more_row property returns the internal row."""
        mock_row = mock.MagicMock()
        pagination_controller._load_more_row = mock_row
        assert pagination_controller.load_more_row is mock_row

    def test_load_more_row_property_returns_none(self, pagination_controller):
        """Test that load_more_row property returns None when not set."""
        assert pagination_controller.load_more_row is None

    def test_entries_to_display_returns_all_entries(self, pagination_controller):
        """Test that entries_to_display property returns all_entries by default."""
        entries = ["entry1", "entry2", "entry3"]
        pagination_controller._all_entries = entries
        assert pagination_controller.entries_to_display == entries

    def test_entries_to_display_returns_same_reference(self, pagination_controller):
        """Test that entries_to_display returns the same reference as all_entries."""
        entries = ["entry1", "entry2"]
        pagination_controller._all_entries = entries
        assert pagination_controller.entries_to_display is entries

    def test_entries_to_display_empty_list(self, pagination_controller):
        """Test that entries_to_display returns empty list when no entries."""
        assert pagination_controller.entries_to_display == []

    def test_entries_to_display_reflects_changes(self, pagination_controller):
        """Test that entries_to_display reflects changes to all_entries."""
        assert pagination_controller.entries_to_display == []

        pagination_controller._all_entries = ["entry1"]
        assert pagination_controller.entries_to_display == ["entry1"]

        pagination_controller._all_entries = ["entry1", "entry2", "entry3"]
        assert pagination_controller.entries_to_display == ["entry1", "entry2", "entry3"]


class TestPaginationControllerConfiguration:
    """Tests for configuration parameters."""

    def test_custom_initial_limit_stored(
        self, pagination_controller_class, mock_listbox, mock_scrolled_window, mock_row_factory
    ):
        """Test that custom initial_limit is stored correctly."""
        controller = pagination_controller_class(
            listbox=mock_listbox,
            scrolled_window=mock_scrolled_window,
            row_factory=mock_row_factory,
            initial_limit=100,
        )

        assert controller._initial_limit == 100

    def test_custom_batch_size_stored(
        self, pagination_controller_class, mock_listbox, mock_scrolled_window, mock_row_factory
    ):
        """Test that custom batch_size is stored correctly."""
        controller = pagination_controller_class(
            listbox=mock_listbox,
            scrolled_window=mock_scrolled_window,
            row_factory=mock_row_factory,
            batch_size=50,
        )

        assert controller._batch_size == 50

    def test_all_custom_parameters_together(
        self, pagination_controller_class, mock_listbox, mock_scrolled_window, mock_row_factory
    ):
        """Test initialization with all custom parameters."""
        controller = pagination_controller_class(
            listbox=mock_listbox,
            scrolled_window=mock_scrolled_window,
            row_factory=mock_row_factory,
            initial_limit=75,
            batch_size=30,
        )

        assert controller._initial_limit == 75
        assert controller._batch_size == 30
        assert controller._listbox is mock_listbox
        assert controller._scrolled_window is mock_scrolled_window
        assert controller._row_factory is mock_row_factory

    def test_row_factory_is_callable(self, pagination_controller):
        """Test that row_factory can be called."""
        mock_entry = {"id": "test"}
        result = pagination_controller._row_factory(mock_entry)

        pagination_controller._row_factory.assert_called_once_with(mock_entry)
        assert result is not None


# Module-level test function for verification
def test_pagination_basic(mock_gi_modules):
    """
    Basic test function for pytest verification command.

    This test verifies the core PaginatedListController functionality
    using the centralized mock setup.
    """
    from src.ui.pagination import PaginatedListController

    # Test 1: Class can be imported
    assert PaginatedListController is not None

    # Test 2: Default constants are correct
    assert PaginatedListController.DEFAULT_INITIAL_LIMIT == 25
    assert PaginatedListController.DEFAULT_BATCH_SIZE == 25

    # Test 3: Create instance with default parameters
    mock_listbox = mock.MagicMock()
    mock_scrolled = mock.MagicMock()
    mock_factory = mock.MagicMock()

    controller = PaginatedListController(
        listbox=mock_listbox,
        scrolled_window=mock_scrolled,
        row_factory=mock_factory,
    )

    # Test 4: Initial state is correct
    assert controller.displayed_count == 0
    assert controller.all_entries == []
    assert controller.load_more_row is None
    assert controller.entries_to_display == []

    # Test 5: Reset state works
    controller._displayed_count = 10
    controller._all_entries = ["test1", "test2"]
    controller._load_more_row = mock.MagicMock()

    controller.reset_state()

    assert controller.displayed_count == 0
    assert controller.all_entries == []
    assert controller.load_more_row is None

    # All tests passed
