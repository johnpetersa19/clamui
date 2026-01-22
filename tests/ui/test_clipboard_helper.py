# ClamUI Clipboard Helper Tests
"""Unit tests for the ClipboardHelper class."""

from unittest.mock import MagicMock, patch


class TestClipboardHelper:
    """Tests for the ClipboardHelper class."""

    def test_copy_small_content_uses_sync(self, mock_gi_modules):
        """Test small content uses synchronous copy."""
        # Import after mocking
        from src.ui.clipboard_helper import ClipboardHelper

        # Create mock parent widget
        mock_widget = MagicMock()
        mock_window = MagicMock()
        mock_widget.get_root.return_value = mock_window

        helper = ClipboardHelper(parent_widget=mock_widget)

        # Mock the sync copy function
        with patch(
            "src.ui.clipboard_helper.copy_to_clipboard_with_result"
        ) as mock_copy:
            from src.core.clipboard import ClipboardOperationResult, ClipboardResult

            mock_copy.return_value = ClipboardOperationResult(
                status=ClipboardResult.SUCCESS,
                message="Copied",
                size_bytes=10,
            )

            helper.copy_with_feedback(text="small text")

            # Should use sync copy for small content
            mock_copy.assert_called_once()

    def test_copy_empty_content_shows_error(self, mock_gi_modules):
        """Test empty content shows error toast."""
        from src.ui.clipboard_helper import ClipboardHelper

        mock_widget = MagicMock()
        mock_window = MagicMock()
        mock_widget.get_root.return_value = mock_window

        helper = ClipboardHelper(parent_widget=mock_widget)

        helper.copy_with_feedback(text="", error_message="No content")

        # Should show error toast
        mock_gi_modules["adw"].Toast.new.assert_called_with("No content")

    def test_copy_with_explicit_toast_manager(self, mock_gi_modules):
        """Test toast is added to explicit toast manager."""
        from src.ui.clipboard_helper import ClipboardHelper

        mock_widget = MagicMock()
        mock_toast_overlay = MagicMock()

        helper = ClipboardHelper(
            parent_widget=mock_widget,
            toast_manager=mock_toast_overlay,
        )

        with patch(
            "src.ui.clipboard_helper.copy_to_clipboard_with_result"
        ) as mock_copy:
            from src.core.clipboard import ClipboardOperationResult, ClipboardResult

            mock_copy.return_value = ClipboardOperationResult(
                status=ClipboardResult.SUCCESS,
                message="Copied",
                size_bytes=5,
            )

            helper.copy_with_feedback(text="hello", success_message="Done!")

            # Toast should be added to the explicit toast manager
            mock_toast_overlay.add_toast.assert_called()

    def test_copy_too_large_calls_callback(self, mock_gi_modules):
        """Test too large content calls on_too_large callback."""
        from src.ui.clipboard_helper import ClipboardHelper

        mock_widget = MagicMock()
        mock_window = MagicMock()
        mock_widget.get_root.return_value = mock_window

        on_too_large_called = []

        def on_too_large():
            on_too_large_called.append(True)

        helper = ClipboardHelper(parent_widget=mock_widget)

        # Mock get_text_size to return a value over the threshold
        with patch("src.ui.clipboard_helper.get_text_size") as mock_size:
            mock_size.return_value = 15 * 1024 * 1024  # 15 MB

            helper.copy_with_feedback(
                text="large content",
                on_too_large=on_too_large,
            )

            # on_too_large callback should have been called
            assert len(on_too_large_called) == 1

    def test_copy_too_large_shows_toast(self, mock_gi_modules):
        """Test too large content shows informative toast."""
        from src.ui.clipboard_helper import ClipboardHelper

        mock_widget = MagicMock()
        mock_window = MagicMock()
        mock_widget.get_root.return_value = mock_window

        helper = ClipboardHelper(parent_widget=mock_widget)

        with patch("src.ui.clipboard_helper.get_text_size") as mock_size:
            mock_size.return_value = 15 * 1024 * 1024  # 15 MB

            helper.copy_with_feedback(
                text="large content",
                too_large_message="File is too big!",
            )

            # Should show the custom too_large_message
            mock_gi_modules["adw"].Toast.new.assert_called_with("File is too big!")

    def test_copy_medium_content_uses_async(self, mock_gi_modules):
        """Test medium-sized content uses async copy."""
        from src.ui.clipboard_helper import ClipboardHelper

        mock_widget = MagicMock()
        mock_window = MagicMock()
        mock_widget.get_root.return_value = mock_window

        helper = ClipboardHelper(parent_widget=mock_widget)

        # Mock get_text_size to return a value in the async range (1-10 MB)
        with patch("src.ui.clipboard_helper.get_text_size") as mock_size:
            mock_size.return_value = 5 * 1024 * 1024  # 5 MB

            with patch("src.ui.clipboard_helper.copy_to_clipboard_async") as mock_async:
                helper.copy_with_feedback(text="medium content")

                # Should use async copy for medium content
                mock_async.assert_called_once()

    def test_copy_success_shows_custom_message(self, mock_gi_modules):
        """Test successful copy shows custom success message."""
        from src.ui.clipboard_helper import ClipboardHelper

        mock_widget = MagicMock()
        mock_window = MagicMock()
        mock_widget.get_root.return_value = mock_window

        helper = ClipboardHelper(parent_widget=mock_widget)

        with patch(
            "src.ui.clipboard_helper.copy_to_clipboard_with_result"
        ) as mock_copy:
            from src.core.clipboard import ClipboardOperationResult, ClipboardResult

            mock_copy.return_value = ClipboardOperationResult(
                status=ClipboardResult.SUCCESS,
                message="Copied",
                size_bytes=5,
            )

            helper.copy_with_feedback(
                text="hello",
                success_message="Custom success!",
            )

            mock_gi_modules["adw"].Toast.new.assert_called_with("Custom success!")

    def test_copy_failure_shows_error_message(self, mock_gi_modules):
        """Test failed copy shows error message."""
        from src.ui.clipboard_helper import ClipboardHelper

        mock_widget = MagicMock()
        mock_window = MagicMock()
        mock_widget.get_root.return_value = mock_window

        helper = ClipboardHelper(parent_widget=mock_widget)

        with patch(
            "src.ui.clipboard_helper.copy_to_clipboard_with_result"
        ) as mock_copy:
            from src.core.clipboard import ClipboardOperationResult, ClipboardResult

            mock_copy.return_value = ClipboardOperationResult(
                status=ClipboardResult.ERROR,
                message="Failed",
                size_bytes=5,
            )

            helper.copy_with_feedback(
                text="hello",
                error_message="Custom error!",
            )

            mock_gi_modules["adw"].Toast.new.assert_called_with("Custom error!")

    def test_async_copy_shows_copying_toast(self, mock_gi_modules):
        """Test async copy shows 'Copying...' toast."""
        from src.ui.clipboard_helper import ClipboardHelper

        mock_widget = MagicMock()
        mock_toast_overlay = MagicMock()

        helper = ClipboardHelper(
            parent_widget=mock_widget,
            toast_manager=mock_toast_overlay,
        )

        with patch("src.ui.clipboard_helper.get_text_size") as mock_size:
            mock_size.return_value = 5 * 1024 * 1024  # 5 MB (async range)

            with patch("src.ui.clipboard_helper.copy_to_clipboard_async"):
                helper.copy_with_feedback(
                    text="medium content",
                    copying_message="Working...",
                )

                # Should show the copying toast
                mock_gi_modules["adw"].Toast.new.assert_called_with("Working...")


class TestClipboardHelperIntegration:
    """Integration tests for ClipboardHelper with real clipboard module."""

    def test_size_threshold_detection(self, mock_gi_modules):
        """Test that size thresholds are correctly applied."""
        from src.ui.clipboard_helper import ClipboardHelper

        mock_widget = MagicMock()
        mock_window = MagicMock()
        mock_widget.get_root.return_value = mock_window

        helper = ClipboardHelper(parent_widget=mock_widget)

        # Test sync range (< 1 MB)
        with patch(
            "src.ui.clipboard_helper.copy_to_clipboard_with_result"
        ) as mock_sync:
            from src.core.clipboard import ClipboardOperationResult, ClipboardResult

            mock_sync.return_value = ClipboardOperationResult(
                status=ClipboardResult.SUCCESS,
                message="OK",
                size_bytes=100,
            )

            small_text = "x" * 100
            helper.copy_with_feedback(text=small_text)
            mock_sync.assert_called_once()

    def test_too_large_without_callback(self, mock_gi_modules):
        """Test too large content without on_too_large callback still shows toast."""
        from src.ui.clipboard_helper import ClipboardHelper

        mock_widget = MagicMock()
        mock_window = MagicMock()
        mock_widget.get_root.return_value = mock_window

        helper = ClipboardHelper(parent_widget=mock_widget)

        with patch("src.ui.clipboard_helper.get_text_size") as mock_size:
            mock_size.return_value = 15 * 1024 * 1024  # 15 MB

            # No on_too_large callback - should still work
            helper.copy_with_feedback(text="large content")

            # Should show a toast (auto-generated message)
            mock_gi_modules["adw"].Toast.new.assert_called()
