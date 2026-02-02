# ClamUI Debug Page
"""
Debug preference page for logging and diagnostic settings.

This module provides the DebugPage class which handles the UI and logic
for managing debug logging configuration, log export, and log clearing.
"""

import logging
import os
import platform
import subprocess

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from ...core.flatpak import is_flatpak
from ...core.logging_config import get_logging_config
from ...core.sanitize import sanitize_path_for_logging
from ..compat import create_toolbar_view
from ..utils import resolve_icon_name
from .base import PreferencesPageMixin, styled_prefix_icon

logger = logging.getLogger(__name__)


class DebugPage(PreferencesPageMixin):
    """
    Debug preference page for logging and diagnostics.

    This class creates and manages the UI for debug logging settings,
    including log level selection, log file location display,
    log export, and log clearing functionality.

    The page includes:
    - Log level setting (DEBUG, INFO, WARNING, ERROR)
    - Log file location display
    - Current log size display
    - Export logs button (creates ZIP archive)
    - Clear logs button (with confirmation)
    """

    # Log level options for ComboRow
    LOG_LEVEL_OPTIONS = ["DEBUG", "INFO", "WARNING", "ERROR"]
    LOG_LEVEL_DESCRIPTIONS = [
        "Verbose debugging information",
        "General operational messages",
        "Warnings and errors only (recommended)",
        "Errors only",
    ]

    def __init__(self, settings_manager=None, parent_window=None):
        """
        Initialize the DebugPage.

        Args:
            settings_manager: Optional SettingsManager instance for storing settings
            parent_window: Parent window for presenting dialogs
        """
        self._settings_manager = settings_manager
        self._parent_window = parent_window
        self._log_level_row = None
        self._log_level_handler_id = None
        self._log_size_row = None
        self._export_button = None
        self._clear_button = None

    def create_page(self) -> Adw.PreferencesPage:
        """
        Create the Debug preference page.

        Returns:
            Configured Adw.PreferencesPage ready to be added to preferences window
        """
        page = Adw.PreferencesPage(
            title="Debug",
            icon_name=resolve_icon_name("applications-system-symbolic"),
        )

        # Logging Settings group
        logging_group = self._create_logging_settings_group()
        page.add(logging_group)

        # Log Management group
        management_group = self._create_log_management_group()
        page.add(management_group)

        # System Information group
        system_group = self._create_system_info_group()
        page.add(system_group)

        return page

    def _create_logging_settings_group(self) -> Adw.PreferencesGroup:
        """
        Create the Logging Settings preferences group.

        Returns:
            Configured Adw.PreferencesGroup for logging settings
        """
        group = Adw.PreferencesGroup()
        group.set_title("Logging Settings")
        group.set_description(
            "Configure debug logging for troubleshooting. "
            "Higher levels produce more detailed logs but use more disk space."
        )

        # Log level combo row
        self._log_level_row = Adw.ComboRow()
        self._log_level_row.set_title("Log Level")
        self._log_level_row.set_subtitle("Set the verbosity of debug logs")
        self._log_level_row.add_prefix(styled_prefix_icon("utilities-terminal-symbolic"))

        # Create string list model for options
        model = Gtk.StringList()
        for level in self.LOG_LEVEL_OPTIONS:
            model.append(level)
        self._log_level_row.set_model(model)

        # Connect signal
        self._log_level_handler_id = self._log_level_row.connect(
            "notify::selected", self._on_log_level_changed
        )

        # Load current value
        self._load_log_level()

        group.add(self._log_level_row)

        # Log file location row
        logging_config = get_logging_config()
        log_dir = logging_config.get_log_dir()
        log_path_display = sanitize_path_for_logging(str(log_dir))

        location_row = Adw.ActionRow()
        location_row.set_title("Log File Location")
        location_row.set_subtitle(log_path_display)

        # Add folder icon as prefix
        location_row.add_prefix(styled_prefix_icon("folder-open-symbolic"))

        # Add "Open Folder" button as suffix
        open_button = Gtk.Button()
        open_button.set_label("Open")
        open_button.set_valign(Gtk.Align.CENTER)
        open_button.add_css_class("flat")
        open_button.set_tooltip_text("Open log folder in file manager")
        open_button.connect("clicked", self._on_open_folder_clicked)
        location_row.add_suffix(open_button)

        group.add(location_row)

        return group

    def _create_log_management_group(self) -> Adw.PreferencesGroup:
        """
        Create the Log Management preferences group.

        Returns:
            Configured Adw.PreferencesGroup for log management
        """
        group = Adw.PreferencesGroup()
        group.set_title("Log Management")
        group.set_description("Export logs for sharing or clear them to free disk space.")

        # Current log size row
        self._log_size_row = Adw.ActionRow()
        self._log_size_row.set_title("Current Log Size")
        self._update_log_size_display()

        # Add size icon as prefix
        self._log_size_row.add_prefix(styled_prefix_icon("drive-harddisk-symbolic"))

        # Add refresh button
        refresh_button = Gtk.Button()
        refresh_button.set_icon_name(resolve_icon_name("view-refresh-symbolic"))
        refresh_button.set_valign(Gtk.Align.CENTER)
        refresh_button.add_css_class("flat")
        refresh_button.set_tooltip_text("Refresh size")
        refresh_button.connect("clicked", lambda _: self._update_log_size_display())
        self._log_size_row.add_suffix(refresh_button)

        group.add(self._log_size_row)

        # Export logs row
        export_row = Adw.ActionRow()
        export_row.set_title("Export Logs")
        export_row.set_subtitle("Save all log files to a ZIP archive for sharing")

        # Add export icon as prefix
        export_row.add_prefix(styled_prefix_icon("document-save-symbolic"))

        # Add export button
        self._export_button = Gtk.Button()
        self._export_button.set_label("Export")
        self._export_button.set_valign(Gtk.Align.CENTER)
        self._export_button.add_css_class("suggested-action")
        self._export_button.set_tooltip_text("Export logs to ZIP file")
        self._export_button.connect("clicked", self._on_export_clicked)
        export_row.add_suffix(self._export_button)

        group.add(export_row)

        # Clear logs row
        clear_row = Adw.ActionRow()
        clear_row.set_title("Clear Logs")
        clear_row.set_subtitle("Delete all log files to free disk space")

        # Add clear icon as prefix
        clear_row.add_prefix(styled_prefix_icon("user-trash-symbolic"))

        # Add clear button
        self._clear_button = Gtk.Button()
        self._clear_button.set_label("Clear")
        self._clear_button.set_valign(Gtk.Align.CENTER)
        self._clear_button.add_css_class("destructive-action")
        self._clear_button.set_tooltip_text("Delete all log files")
        self._clear_button.connect("clicked", self._on_clear_clicked)
        clear_row.add_suffix(self._clear_button)

        group.add(clear_row)

        return group

    def _create_system_info_group(self) -> Adw.PreferencesGroup:
        """
        Create the System Information preferences group.

        Returns:
            Configured Adw.PreferencesGroup for system information
        """
        group = Adw.PreferencesGroup()
        group.set_title("System Information")
        group.set_description("Useful information for troubleshooting and bug reports.")

        # Installation type row
        install_row = Adw.ActionRow()
        install_row.set_title("Installation Type")
        install_row.set_subtitle(self._get_installation_type())

        # Add package icon as prefix
        install_row.add_prefix(styled_prefix_icon("package-x-generic-symbolic"))

        group.add(install_row)

        # Distribution row
        distro_row = Adw.ActionRow()
        distro_row.set_title("Distribution")
        distro_row.set_subtitle(self._get_distro_info())

        # Add computer icon as prefix
        distro_row.add_prefix(styled_prefix_icon("computer-symbolic"))

        group.add(distro_row)

        # Desktop environment row
        desktop_row = Adw.ActionRow()
        desktop_row.set_title("Desktop Environment")
        desktop_row.set_subtitle(self._get_desktop_environment())

        # Add preferences icon as prefix
        desktop_row.add_prefix(styled_prefix_icon("preferences-desktop-symbolic"))

        group.add(desktop_row)

        # Python version row
        python_row = Adw.ActionRow()
        python_row.set_title("Python Version")
        python_row.set_subtitle(platform.python_version())

        # Add code icon as prefix
        python_row.add_prefix(styled_prefix_icon("text-x-script-symbolic"))

        group.add(python_row)

        # GTK version row
        gtk_row = Adw.ActionRow()
        gtk_row.set_title("GTK Version")
        gtk_row.set_subtitle(self._get_gtk_version())

        # Add application icon as prefix
        gtk_row.add_prefix(styled_prefix_icon("applications-graphics-symbolic"))

        group.add(gtk_row)

        # Copy all info button row
        copy_row = Adw.ActionRow()
        copy_row.set_title("Copy System Info")
        copy_row.set_subtitle("Copy all system information to clipboard")

        # Add copy icon as prefix
        copy_row.add_prefix(styled_prefix_icon("edit-copy-symbolic"))

        # Add copy button
        copy_button = Gtk.Button()
        copy_button.set_label("Copy")
        copy_button.set_valign(Gtk.Align.CENTER)
        copy_button.add_css_class("suggested-action")
        copy_button.set_tooltip_text("Copy system information to clipboard")
        copy_button.connect("clicked", self._on_copy_system_info_clicked)
        copy_row.add_suffix(copy_button)

        group.add(copy_row)

        return group

    def _get_installation_type(self) -> str:
        """
        Detect the installation type of ClamUI.

        Returns:
            String describing the installation type
        """
        # Check for Flatpak
        if is_flatpak():
            return "Flatpak"

        # Check for AppImage
        if os.environ.get("APPIMAGE"):
            return "AppImage"

        # Check if running from source (development)
        import sys

        if any("site-packages" not in p and "src" in p for p in sys.path):
            # Check for common development indicators
            script_path = os.path.abspath(sys.argv[0]) if sys.argv else ""
            if "WebstormProjects" in script_path or ".venv" in script_path:
                return "Development (source)"

        # Check for Debian/Ubuntu package
        try:
            result = subprocess.run(
                ["dpkg", "-S", sys.executable],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return "Debian/Ubuntu Package"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Check for RPM package
        try:
            result = subprocess.run(
                ["rpm", "-qf", sys.executable],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return "RPM Package"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return "Native (pip/system)"

    def _get_distro_info(self) -> str:
        """
        Get Linux distribution information.

        Returns:
            String with distribution name and version
        """
        try:
            # Try to read /etc/os-release (standard on most Linux distros)
            if os.path.exists("/etc/os-release"):
                info = {}
                with open("/etc/os-release") as f:
                    for line in f:
                        line = line.strip()
                        if "=" in line:
                            key, value = line.split("=", 1)
                            info[key] = value.strip('"')

                name = info.get("PRETTY_NAME")
                if name:
                    return name

                # Fallback to NAME + VERSION
                name = info.get("NAME", "Unknown")
                version = info.get("VERSION", info.get("VERSION_ID", ""))
                if version:
                    return f"{name} {version}"
                return name

        except (OSError, PermissionError):
            pass

        # Fallback to platform module
        return platform.platform()

    def _get_desktop_environment(self) -> str:
        """
        Detect the current desktop environment.

        Returns:
            String with desktop environment name
        """
        # Check XDG_CURRENT_DESKTOP first (most reliable)
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "")
        if desktop:
            return desktop

        # Check XDG_SESSION_DESKTOP
        desktop = os.environ.get("XDG_SESSION_DESKTOP", "")
        if desktop:
            return desktop.capitalize()

        # Check DESKTOP_SESSION
        desktop = os.environ.get("DESKTOP_SESSION", "")
        if desktop:
            return desktop.capitalize()

        # Check for specific desktop indicators
        if os.environ.get("GNOME_DESKTOP_SESSION_ID"):
            return "GNOME"
        if os.environ.get("KDE_FULL_SESSION"):
            return "KDE"

        return "Unknown"

    def _get_gtk_version(self) -> str:
        """
        Get GTK and libadwaita version information.

        Returns:
            String with GTK and Adwaita versions
        """
        gtk_version = (
            f"{Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}"
        )
        adw_version = (
            f"{Adw.get_major_version()}.{Adw.get_minor_version()}.{Adw.get_micro_version()}"
        )
        return f"GTK {gtk_version}, libadwaita {adw_version}"

    def _on_copy_system_info_clicked(self, _button):
        """Handle Copy System Info button click."""
        info_lines = [
            "ClamUI System Information",
            "=" * 40,
            f"Installation Type: {self._get_installation_type()}",
            f"Distribution: {self._get_distro_info()}",
            f"Desktop Environment: {self._get_desktop_environment()}",
            f"Python Version: {platform.python_version()}",
            f"GTK Version: {self._get_gtk_version()}",
            f"Platform: {platform.platform()}",
            f"Architecture: {platform.machine()}",
        ]

        info_text = "\n".join(info_lines)

        # Copy to clipboard using GTK4 clipboard API
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set(info_text)

        self._show_toast("System information copied to clipboard")

    def _load_log_level(self):
        """Load the current log level setting into the ComboRow."""
        if self._log_level_row is None:
            return

        # Get current log level from settings or logging config
        if self._settings_manager is not None:
            current_level = self._settings_manager.get("debug_log_level", "WARNING")
        else:
            logging_config = get_logging_config()
            current_level = logging_config.get_log_level()

        # Map setting value to ComboRow index
        current_level_upper = current_level.upper()
        if current_level_upper in self.LOG_LEVEL_OPTIONS:
            index = self.LOG_LEVEL_OPTIONS.index(current_level_upper)
        else:
            # Default to WARNING (index 2)
            index = 2

        # Block signal during load to avoid triggering save
        if self._log_level_handler_id is not None:
            self._log_level_row.handler_block(self._log_level_handler_id)
        self._log_level_row.set_selected(index)
        if self._log_level_handler_id is not None:
            self._log_level_row.handler_unblock(self._log_level_handler_id)

    def _on_log_level_changed(self, row, _pspec):
        """
        Handle log level ComboRow changes.

        Updates both the settings and the active logging configuration.

        Args:
            row: The ComboRow that was changed
            pspec: The property specification (unused)
        """
        selected_index = row.get_selected()
        if 0 <= selected_index < len(self.LOG_LEVEL_OPTIONS):
            level = self.LOG_LEVEL_OPTIONS[selected_index]

            # Save to settings
            if self._settings_manager is not None:
                self._settings_manager.set("debug_log_level", level)

            # Apply immediately to running logging config
            logging_config = get_logging_config()
            logging_config.set_log_level(level)

            logger.info("Log level changed to %s", level)

    def _update_log_size_display(self):
        """Update the log size display with current total size."""
        if self._log_size_row is None:
            return

        logging_config = get_logging_config()
        total_bytes = logging_config.get_total_log_size()

        # Format size for display
        if total_bytes < 1024:
            size_str = f"{total_bytes} bytes"
        elif total_bytes < 1024 * 1024:
            size_str = f"{total_bytes / 1024:.1f} KB"
        else:
            size_str = f"{total_bytes / (1024 * 1024):.1f} MB"

        # Count log files
        log_files = logging_config.get_log_files()
        file_count = len(log_files)
        if file_count == 1:
            subtitle = f"{size_str} (1 file)"
        else:
            subtitle = f"{size_str} ({file_count} files)"

        self._log_size_row.set_subtitle(subtitle)

    def _on_open_folder_clicked(self, _button):
        """Handle Open Folder button click."""
        logging_config = get_logging_config()
        log_dir = str(logging_config.get_log_dir())
        self._open_folder_in_file_manager(log_dir)

    def _on_export_clicked(self, _button):
        """Handle Export button click."""
        logging_config = get_logging_config()

        # Check if there are any log files
        log_files = logging_config.get_log_files()
        if not log_files:
            self._show_simple_dialog(
                "No Logs to Export",
                "There are no log files to export. Logs will be created "
                "when debug logging is enabled and the application runs.",
            )
            return

        # Generate default filename
        default_filename = logging_config.generate_export_filename()

        def on_export_success():
            """Called when export succeeds."""
            self._show_toast("Logs exported successfully")
            self._update_log_size_display()

        def on_file_selected(file_path: str):
            """Handle file selection and perform export."""
            success = logging_config.export_logs_zip(file_path)
            if success:
                GLib.idle_add(on_export_success)
            else:
                GLib.idle_add(
                    self._show_simple_dialog,
                    "Export Failed",
                    "Failed to export log files. Check file permissions.",
                )

        # Use custom file chooser since we need ZIP export (not text content)
        self._show_save_dialog(default_filename, on_file_selected)

    def _show_save_dialog(self, default_filename: str, on_save_callback):
        """
        Show a save file dialog for exporting logs.

        Args:
            default_filename: Default filename to suggest
            on_save_callback: Callback with file path when saved
        """
        dialog = Gtk.FileDialog()
        dialog.set_initial_name(default_filename)

        # Set up ZIP filter
        filter_store = Gio.ListStore.new(Gtk.FileFilter)

        zip_filter = Gtk.FileFilter()
        zip_filter.set_name("ZIP Archives")
        zip_filter.add_pattern("*.zip")
        filter_store.append(zip_filter)

        all_filter = Gtk.FileFilter()
        all_filter.set_name("All Files")
        all_filter.add_pattern("*")
        filter_store.append(all_filter)

        dialog.set_filters(filter_store)

        def on_response(dialog, result):
            try:
                file = dialog.save_finish(result)
                if file:
                    file_path = file.get_path()
                    on_save_callback(file_path)
            except GLib.Error as e:
                if e.code != Gtk.DialogError.DISMISSED:
                    logger.error("File dialog error: %s", e)

        dialog.save(self._parent_window, None, on_response)

    def _on_clear_clicked(self, _button):
        """Handle Clear button click - show confirmation dialog."""
        logging_config = get_logging_config()
        log_files = logging_config.get_log_files()

        if not log_files:
            self._show_simple_dialog("No Logs to Clear", "There are no log files to delete.")
            return

        # Show confirmation dialog
        self._show_clear_confirmation_dialog()

    def _show_clear_confirmation_dialog(self):
        """Show a confirmation dialog before clearing logs."""
        dialog = Adw.Window()
        dialog.set_title("Clear Logs")
        dialog.set_default_size(400, -1)
        dialog.set_modal(True)
        dialog.set_deletable(True)
        dialog.set_transient_for(self._parent_window)

        # Create content
        toolbar_view = create_toolbar_view()
        header_bar = Adw.HeaderBar()
        toolbar_view.add_top_bar(header_bar)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(24)

        # Warning icon and message
        icon = Gtk.Image.new_from_icon_name(resolve_icon_name("dialog-warning-symbolic"))
        icon.set_pixel_size(48)
        icon.add_css_class("warning")
        content_box.append(icon)

        # Get size info for message
        logging_config = get_logging_config()
        total_bytes = logging_config.get_total_log_size()
        if total_bytes < 1024 * 1024:
            size_str = f"{total_bytes / 1024:.1f} KB"
        else:
            size_str = f"{total_bytes / (1024 * 1024):.1f} MB"

        file_count = len(logging_config.get_log_files())

        label = Gtk.Label()
        label.set_markup(
            f"<b>Delete all log files?</b>\n\n"
            f"This will permanently delete {file_count} log file(s) "
            f"totaling {size_str}.\n\n"
            f"This action cannot be undone."
        )
        label.set_wrap(True)
        label.set_justify(Gtk.Justification.CENTER)
        content_box.append(label)

        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(12)

        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda _: dialog.close())
        button_box.append(cancel_button)

        delete_button = Gtk.Button(label="Delete Logs")
        delete_button.add_css_class("destructive-action")
        delete_button.connect("clicked", lambda _: self._do_clear_logs(dialog))
        button_box.append(delete_button)

        content_box.append(button_box)
        toolbar_view.set_content(content_box)
        dialog.set_content(toolbar_view)

        dialog.present()

    def _do_clear_logs(self, dialog):
        """
        Actually clear the log files after confirmation.

        Args:
            dialog: The confirmation dialog to close
        """
        dialog.close()

        logging_config = get_logging_config()
        success = logging_config.clear_logs()

        if success:
            self._show_toast("Logs cleared successfully")
        else:
            self._show_simple_dialog(
                "Clear Failed",
                "Some log files could not be deleted. They may be in use or protected.",
            )

        # Update size display
        self._update_log_size_display()

    def _show_toast(self, message: str):
        """
        Show a toast notification if possible.

        Args:
            message: The message to display
        """
        # Try to find the toast overlay in the parent hierarchy
        if self._parent_window is not None and hasattr(self._parent_window, "add_toast"):
            toast = Adw.Toast.new(message)
            self._parent_window.add_toast(toast)
        else:
            # Fallback to simple dialog
            logger.info(message)
