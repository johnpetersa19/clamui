# ClamUI Preferences Dialog
"""
Preferences dialog component for ClamUI user settings.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from typing import TYPE_CHECKING

from gi.repository import Adw, Gtk

if TYPE_CHECKING:
    from ..core.settings_manager import SettingsManager


class PreferencesDialog(Adw.Dialog):
    """
    A preferences dialog for configuring ClamUI settings.

    Provides a user interface for toggling application preferences
    such as desktop notifications and window behavior.

    Usage:
        dialog = PreferencesDialog(
            settings_manager=app.settings_manager,
            tray_available=app.tray_indicator is not None
        )
        dialog.present(parent_window)
    """

    # Mapping between close_behavior setting values and ComboRow indices
    CLOSE_BEHAVIOR_OPTIONS = ["minimize", "quit", "ask"]
    CLOSE_BEHAVIOR_LABELS = ["Minimize to tray", "Quit completely", "Always ask"]

    def __init__(
        self,
        settings_manager: "SettingsManager" = None,
        tray_available: bool = False,
        **kwargs,
    ):
        """
        Initialize the preferences dialog.

        Args:
            settings_manager: The SettingsManager instance for reading/writing settings.
                              If None, changes won't be persisted.
            tray_available: Whether the system tray is available.
            **kwargs: Additional arguments passed to parent
        """
        super().__init__(**kwargs)

        self._settings_manager = settings_manager
        self._tray_available = tray_available

        # Configure the dialog
        self._setup_dialog()

        # Set up the UI
        self._setup_ui()

        # Load current settings
        self._load_settings()

    def _setup_dialog(self):
        """Configure the dialog properties."""
        self.set_title("Preferences")
        self.set_content_width(400)
        self.set_content_height(400)
        self.set_can_close(True)

    def _setup_ui(self):
        """Set up the dialog UI layout."""
        # Create main container with toolbar view for header bar
        toolbar_view = Adw.ToolbarView()

        # Create header bar
        header_bar = Adw.HeaderBar()
        toolbar_view.add_top_bar(header_bar)

        # Create scrolled window for content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        # Create preferences page using Adwaita patterns
        preferences_page = Adw.PreferencesPage()

        # Notifications group
        notifications_group = Adw.PreferencesGroup()
        notifications_group.set_title("Notifications")
        notifications_group.set_description("Configure desktop notification behavior")

        # Notifications enabled switch row
        self._notifications_row = Adw.SwitchRow()
        self._notifications_row.set_title("Desktop Notifications")
        self._notifications_row.set_subtitle(
            "Show notifications when scans complete or updates finish"
        )
        self._notifications_row.connect("notify::active", self._on_notifications_toggled)

        notifications_group.add(self._notifications_row)
        preferences_page.add(notifications_group)

        # Window Behavior group (only if tray is available)
        if self._tray_available:
            self._setup_window_behavior_group(preferences_page)

        scrolled.set_child(preferences_page)
        toolbar_view.set_content(scrolled)

        # Set the toolbar view as the dialog child
        self.set_child(toolbar_view)

    def _setup_window_behavior_group(self, preferences_page: Adw.PreferencesPage):
        """
        Set up the Window Behavior preferences group.

        Args:
            preferences_page: The preferences page to add the group to
        """
        window_group = Adw.PreferencesGroup()
        window_group.set_title("Window Behavior")
        window_group.set_description("Configure what happens when closing the window")

        # Close behavior combo row
        self._close_behavior_row = Adw.ComboRow()
        self._close_behavior_row.set_title("When closing window")
        self._close_behavior_row.set_subtitle("Choose what happens when you close the main window")

        # Create string list model for options
        model = Gtk.StringList()
        for label in self.CLOSE_BEHAVIOR_LABELS:
            model.append(label)
        self._close_behavior_row.set_model(model)

        self._close_behavior_row.connect("notify::selected", self._on_close_behavior_changed)

        window_group.add(self._close_behavior_row)
        preferences_page.add(window_group)

    def _load_settings(self):
        """Load current settings into UI widgets."""
        if self._settings_manager is not None:
            # Load notifications setting
            notifications_enabled = self._settings_manager.get("notifications_enabled", True)
            # Block signal during initial load to avoid triggering save
            self._notifications_row.handler_block_by_func(self._on_notifications_toggled)
            self._notifications_row.set_active(notifications_enabled)
            self._notifications_row.handler_unblock_by_func(self._on_notifications_toggled)

            # Load close behavior setting (if tray is available)
            if self._tray_available and hasattr(self, "_close_behavior_row"):
                close_behavior = self._settings_manager.get("close_behavior", None)
                # Map setting value to ComboRow index, default to "ask" if not set
                if close_behavior in self.CLOSE_BEHAVIOR_OPTIONS:
                    index = self.CLOSE_BEHAVIOR_OPTIONS.index(close_behavior)
                else:
                    # Default to "ask" (index 2) for unset or invalid values
                    index = 2

                # Block signal during initial load
                self._close_behavior_row.handler_block_by_func(self._on_close_behavior_changed)
                self._close_behavior_row.set_selected(index)
                self._close_behavior_row.handler_unblock_by_func(self._on_close_behavior_changed)
        else:
            # Default to enabled if no settings manager
            self._notifications_row.set_active(True)

    def _on_notifications_toggled(self, row, pspec):
        """
        Handle notification toggle changes.

        Args:
            row: The SwitchRow that was toggled
            pspec: The property specification (unused)
        """
        if self._settings_manager is not None:
            is_active = row.get_active()
            self._settings_manager.set("notifications_enabled", is_active)

    def get_notifications_enabled(self) -> bool:
        """
        Get the current notifications enabled state.

        Returns:
            True if notifications are enabled, False otherwise
        """
        return self._notifications_row.get_active()

    def set_notifications_enabled(self, enabled: bool) -> None:
        """
        Set the notifications enabled state.

        Args:
            enabled: Whether notifications should be enabled
        """
        self._notifications_row.set_active(enabled)

    def _on_close_behavior_changed(self, row, pspec):
        """
        Handle close behavior ComboRow changes.

        Args:
            row: The ComboRow that was changed
            pspec: The property specification (unused)
        """
        if self._settings_manager is not None:
            selected_index = row.get_selected()
            if 0 <= selected_index < len(self.CLOSE_BEHAVIOR_OPTIONS):
                value = self.CLOSE_BEHAVIOR_OPTIONS[selected_index]
                self._settings_manager.set("close_behavior", value)

    def get_close_behavior(self) -> str | None:
        """
        Get the current close behavior setting.

        Returns:
            "minimize", "quit", "ask", or None if not available
        """
        if not self._tray_available or not hasattr(self, "_close_behavior_row"):
            return None

        selected_index = self._close_behavior_row.get_selected()
        if 0 <= selected_index < len(self.CLOSE_BEHAVIOR_OPTIONS):
            return self.CLOSE_BEHAVIOR_OPTIONS[selected_index]
        return None

    def set_close_behavior(self, behavior: str) -> None:
        """
        Set the close behavior.

        Args:
            behavior: "minimize", "quit", or "ask"
        """
        if not self._tray_available or not hasattr(self, "_close_behavior_row"):
            return

        if behavior in self.CLOSE_BEHAVIOR_OPTIONS:
            index = self.CLOSE_BEHAVIOR_OPTIONS.index(behavior)
            self._close_behavior_row.set_selected(index)
