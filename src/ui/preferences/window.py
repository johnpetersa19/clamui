# ClamUI Preferences Window
"""
Main preferences window with sidebar navigation.

This module provides the PreferencesWindow class which composes all
preference page modules into a cohesive preferences interface with
GNOME Settings-style sidebar navigation using Adw.Leaflet.
"""

import logging
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from ...core.clamav_config import parse_config
from ...core.flatpak import (
    ensure_freshclam_config,
    get_freshclam_config_path,
    is_flatpak,
)
from ...core.scheduler import Scheduler
from ..compat import create_toolbar_view
from ..utils import resolve_icon_name

logger = logging.getLogger(__name__)

from .base import PreferencesPageMixin
from .behavior_page import BehaviorPage
from .database_page import DatabasePage
from .debug_page import DebugPage
from .exclusions_page import ExclusionsPage
from .onaccess_page import OnAccessPage
from .save_page import SavePage
from .scanner_page import ScannerPage
from .scheduled_page import ScheduledPage
from .virustotal_page import VirusTotalPage

# Navigation items configuration: (page_id, icon_name, display_label)
NAVIGATION_ITEMS = [
    ("behavior", "preferences-system-symbolic", "Behavior"),
    ("exclusions", "action-unavailable-symbolic", "Exclusions"),
    ("database", "software-update-available-symbolic", "Database"),
    ("scanner", "document-properties-symbolic", "Scanner"),
    ("scheduled", "alarm-symbolic", "Scheduled"),
    ("onaccess", "security-high-symbolic", "On-Access"),
    ("virustotal", "network-server-symbolic", "VirusTotal"),
    ("debug", "applications-system-symbolic", "Debug"),
    ("save", "document-save-symbolic", "Save"),
]


class PreferencesSidebarRow(Gtk.ListBoxRow):
    """
    A navigation sidebar row with icon and label.

    Each row represents a preference page with a consistent
    GNOME Settings-style appearance.
    """

    def __init__(self, page_id: str, icon_name: str, label: str):
        """
        Initialize a sidebar row.

        Args:
            page_id: Identifier for the preference page
            icon_name: Icon name for the row
            label: Display label for the row
        """
        super().__init__()

        self._page_id = page_id

        # Create horizontal box for icon + label
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(8)
        box.set_margin_end(8)

        # Icon
        icon = Gtk.Image.new_from_icon_name(resolve_icon_name(icon_name))
        icon.set_icon_size(Gtk.IconSize.NORMAL)
        box.append(icon)

        # Label
        label_widget = Gtk.Label(label=label)
        label_widget.set_xalign(0)
        label_widget.set_hexpand(True)
        box.append(label_widget)

        self.set_child(box)

    @property
    def page_id(self) -> str:
        """Get the page identifier for this row."""
        return self._page_id


class PreferencesWindow(Adw.Window, PreferencesPageMixin):
    """
    Preferences window for ClamUI with sidebar navigation.

    Provides a settings interface for ClamAV configuration with:
    - Sidebar navigation with icons and labels
    - Database update settings (freshclam.conf)
    - Scanner settings (clamd.conf)
    - On-Access scanning settings (clamd.conf)
    - Scheduled scans configuration
    - Scan exclusion patterns
    - VirusTotal API configuration
    - Behavior settings (window close, tray)
    - Debug logging settings
    - Save & Apply functionality with permission elevation

    The window is displayed as a modal dialog transient to the main window.
    """

    def __init__(self, settings_manager=None, tray_available: bool = False, **kwargs):
        """
        Initialize the preferences window.

        Args:
            settings_manager: Optional SettingsManager instance for application settings
            tray_available: Whether the system tray is available
            **kwargs: Additional arguments passed to parent, including:
                - transient_for: Parent window to be modal to
                - application: The parent application instance
        """
        super().__init__(**kwargs)

        # Store settings manager reference
        self._settings_manager = settings_manager

        # Store tray availability for behavior page
        self._tray_available = tray_available

        # Set window properties
        self.set_title("Preferences")
        self.set_default_size(850, 600)
        self.set_modal(True)

        # Store references to form widgets for later access
        self._freshclam_widgets = {}
        self._clamd_widgets = {}
        self._scheduled_widgets = {}
        self._onaccess_widgets = {}

        # Track if clamd.conf exists
        self._clamd_available = False

        # Initialize scheduler for scheduled scans
        self._scheduler = Scheduler()

        # Store loaded configurations
        self._freshclam_config = None
        self._clamd_config = None

        # Track config load status for UI feedback
        self._freshclam_load_error = None
        self._clamd_load_error = None

        # Default config file paths - use Flatpak-specific paths when running in Flatpak
        if is_flatpak():
            # In Flatpak, use the generated config in user's config directory
            logger.info("Running in Flatpak, using Flatpak-specific config paths")
            flatpak_config = get_freshclam_config_path()
            if flatpak_config:
                # Ensure the config file exists (generates it if needed)
                generated_path = ensure_freshclam_config()
                if generated_path:
                    logger.info("Flatpak freshclam config generated at: %s", generated_path)
                    self._freshclam_conf_path = str(generated_path)
                else:
                    # Config generation failed - log detailed error
                    logger.error(
                        "Failed to generate Flatpak freshclam config. "
                        "Check disk space and permissions in ~/.var/app/io.github.linx_systems.ClamUI/"
                    )
                    # Use fallback path, but mark that generation failed
                    self._freshclam_conf_path = str(flatpak_config)
                    self._freshclam_load_error = (
                        "Failed to generate Flatpak configuration. "
                        "This may be due to insufficient disk space or permissions."
                    )
            else:
                logger.warning(
                    "Could not determine Flatpak config path, falling back to system path"
                )
                self._freshclam_conf_path = "/etc/clamav/freshclam.conf"
                self._freshclam_load_error = "Could not determine Flatpak configuration path"
            # clamd.conf is typically not used in Flatpak (daemon runs on host)
            self._clamd_conf_path = "/etc/clamav/clamd.conf"
        else:
            self._freshclam_conf_path = "/etc/clamav/freshclam.conf"
            self._clamd_conf_path = "/etc/clamav/clamd.conf"

        # Check if clamd.conf exists
        if Path(self._clamd_conf_path).exists():
            self._clamd_available = True

        # Saving state (used by SavePage)
        self._is_saving = False

        # Scheduler error storage (for thread-safe error passing)
        self._scheduler_error = None

        # Sidebar and stack references
        self._sidebar_rows: dict[str, PreferencesSidebarRow] = {}
        self._stack = None
        self._sidebar_list = None

        # Set up the UI
        self._setup_ui()

        # Load configurations and populate form fields
        self._load_configs()

        # Populate scheduled scan fields from saved settings
        self._populate_scheduled_fields()

    def _setup_ui(self):
        """Set up the preferences window UI layout with sidebar navigation."""
        # Create the header bar
        header_bar = self._create_header_bar()

        # Create the leaflet for adaptive layout
        self._leaflet = Adw.Leaflet()
        self._leaflet.set_transition_type(Adw.LeafletTransitionType.SLIDE)
        self._leaflet.set_can_unfold(True)

        # Create sidebar
        sidebar_box = self._create_sidebar()

        # Add sidebar page to leaflet
        sidebar_page = self._leaflet.append(sidebar_box)
        sidebar_page.set_name("sidebar")

        # Add separator (non-navigable so navigation skips directly to content)
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        separator_page = self._leaflet.append(separator)
        separator_page.set_navigatable(False)

        # Create content area with stack
        content_box = self._create_content_area()

        # Add content page to leaflet
        content_page = self._leaflet.append(content_box)
        content_page.set_name("content")

        # Connect to folded state changes for adaptive header
        self._leaflet.connect("notify::folded", self._on_leaflet_folded_changed)

        # Add toast overlay for in-app notifications
        self._toast_overlay = Adw.ToastOverlay()
        self._toast_overlay.set_child(self._leaflet)

        # Use ToolbarView to properly integrate the HeaderBar as a titlebar
        toolbar_view = create_toolbar_view()
        toolbar_view.add_top_bar(header_bar)
        toolbar_view.set_content(self._toast_overlay)

        self.set_content(toolbar_view)

        # Select the first item by default
        first_row = self._sidebar_list.get_row_at_index(0)
        if first_row:
            self._sidebar_list.select_row(first_row)

    def _create_header_bar(self) -> Adw.HeaderBar:
        """
        Create the preferences header bar.

        Returns:
            Configured Adw.HeaderBar
        """
        header_bar = Adw.HeaderBar()
        header_bar.set_show_start_title_buttons(True)
        header_bar.set_show_end_title_buttons(True)

        # Back button (hidden when not folded)
        self._back_button = Gtk.Button.new_from_icon_name(resolve_icon_name("go-previous-symbolic"))
        self._back_button.set_tooltip_text("Back to navigation")
        self._back_button.connect("clicked", self._on_back_clicked)
        self._back_button.set_visible(False)
        header_bar.pack_start(self._back_button)

        # Title widget
        self._title_label = Gtk.Label(label="Preferences")
        self._title_label.add_css_class("title")
        header_bar.set_title_widget(self._title_label)

        return header_bar

    def _create_sidebar(self) -> Gtk.Box:
        """
        Create the navigation sidebar.

        Returns:
            Configured Gtk.Box containing the sidebar
        """
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar_box.set_size_request(200, -1)

        # Create scrollable container for the list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        sidebar_box.append(scrolled)

        # Create the list box
        self._sidebar_list = Gtk.ListBox()
        self._sidebar_list.add_css_class("navigation-sidebar")
        self._sidebar_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._sidebar_list.connect("row-selected", self._on_sidebar_row_selected)
        scrolled.set_child(self._sidebar_list)

        # Populate with navigation items
        for page_id, icon_name, label in NAVIGATION_ITEMS:
            row = PreferencesSidebarRow(page_id, icon_name, label)
            self._sidebar_rows[page_id] = row
            self._sidebar_list.append(row)

        return sidebar_box

    def _create_content_area(self) -> Gtk.Box:
        """
        Create the content area with stack for pages.

        Returns:
            Configured Gtk.Box containing the content stack
        """
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_vexpand(True)
        content_box.set_hexpand(True)

        # Create scroll wrapper for the stack
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        content_box.append(scrolled)

        # Create stack for pages
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._stack.set_transition_duration(200)
        scrolled.set_child(self._stack)

        # Create and add all pages
        self._create_pages()

        return content_box

    def _create_pages(self):
        """Create and add all preference pages to the stack."""
        # Create Behavior page (window behavior settings) - instance-based
        behavior_page_instance = BehaviorPage(
            self._settings_manager, self._tray_available, parent_window=self
        )
        behavior_page = behavior_page_instance.create_page()
        self._add_page_to_stack("behavior", behavior_page)

        # Create Exclusions page (scan exclusion patterns) - instance-based
        exclusions_page_instance = ExclusionsPage(self._settings_manager)
        exclusions_page = exclusions_page_instance.create_page()
        self._add_page_to_stack("exclusions", exclusions_page)

        # Create Database Updates page (freshclam.conf)
        database_page = DatabasePage.create_page(self._freshclam_conf_path, self._freshclam_widgets)
        self._add_page_to_stack("database", database_page)

        # Create Scanner Settings page (clamd.conf)
        scanner_page = ScannerPage.create_page(
            self._clamd_conf_path,
            self._clamd_widgets,
            self._settings_manager,
            self._clamd_available,
            self,
        )
        self._add_page_to_stack("scanner", scanner_page)

        # Create Scheduled Scans page
        scheduled_page = ScheduledPage.create_page(self._scheduled_widgets)
        self._add_page_to_stack("scheduled", scheduled_page)

        # Create On-Access Scanning page (clamd.conf on-access settings)
        onaccess_page = OnAccessPage.create_page(
            self._clamd_conf_path, self._onaccess_widgets, self._clamd_available, self
        )
        self._add_page_to_stack("onaccess", onaccess_page)

        # Create VirusTotal page (API key and settings)
        virustotal_page = VirusTotalPage.create_page(self._settings_manager, self)
        self._add_page_to_stack("virustotal", virustotal_page)

        # Create Debug page (logging and diagnostics) - instance-based
        debug_page_instance = DebugPage(self._settings_manager, parent_window=self)
        debug_page = debug_page_instance.create_page()
        self._add_page_to_stack("debug", debug_page)

        # Create Save & Apply page - instance-based
        save_page_instance = SavePage(
            self,
            self._freshclam_config,
            self._clamd_config,
            self._freshclam_conf_path,
            self._clamd_conf_path,
            self._clamd_available,
            self._settings_manager,
            self._scheduler,
            self._freshclam_widgets,
            self._clamd_widgets,
            self._onaccess_widgets,
            self._scheduled_widgets,
        )
        save_page = save_page_instance.create_page()
        self._add_page_to_stack("save", save_page)

    def _add_page_to_stack(self, page_id: str, page: Adw.PreferencesPage):
        """
        Add a preference page to the stack with proper wrapping.

        Args:
            page_id: Unique identifier for the page
            page: The Adw.PreferencesPage to add
        """
        # Wrap the PreferencesPage in a Clamp for consistent width
        clamp = Adw.Clamp()
        clamp.set_maximum_size(800)
        clamp.set_tightening_threshold(600)
        clamp.set_child(page)

        # Add margin for visual spacing
        clamp.set_margin_top(12)
        clamp.set_margin_bottom(12)
        clamp.set_margin_start(12)
        clamp.set_margin_end(12)

        self._stack.add_named(clamp, page_id)

    def _on_sidebar_row_selected(self, list_box: Gtk.ListBox, row: PreferencesSidebarRow | None):
        """Handle sidebar row selection."""
        if row is None:
            return

        page_id = row.page_id
        logger.debug("Preferences sidebar: selected page '%s'", page_id)

        # Switch to the selected page
        self._stack.set_visible_child_name(page_id)

        # Update title to reflect current page
        page_label = self._get_page_label(page_id)
        self._title_label.set_label(f"Preferences — {page_label}")

        # If leaflet is folded, navigate to content
        if self._leaflet.get_folded():
            self._leaflet.set_visible_child_name("content")

    def _get_page_label(self, page_id: str) -> str:
        """Get the display label for a page ID."""
        for pid, _, label in NAVIGATION_ITEMS:
            if pid == page_id:
                return label
        return page_id.capitalize()

    def _on_leaflet_folded_changed(self, leaflet, pspec):
        """Handle leaflet folded state changes."""
        folded = leaflet.get_folded()
        self._back_button.set_visible(folded)

        if not folded:
            # When unfolded, ensure title shows current page
            selected_row = self._sidebar_list.get_selected_row()
            if selected_row and isinstance(selected_row, PreferencesSidebarRow):
                page_label = self._get_page_label(selected_row.page_id)
                self._title_label.set_label(f"Preferences — {page_label}")

    def _on_back_clicked(self, button):
        """Handle back button click to return to sidebar."""
        self._leaflet.set_visible_child_name("sidebar")

    def _load_configs(self):
        """
        Load ClamAV configuration files and populate form fields.

        Loads both freshclam.conf and clamd.conf (if available),
        parses them, and updates the UI with current values.
        """
        # Load freshclam.conf
        logger.debug("Loading freshclam config from: %s", self._freshclam_conf_path)
        try:
            self._freshclam_config, error = parse_config(self._freshclam_conf_path)
            if error:
                logger.warning("Failed to load freshclam.conf: %s", error)
                self._freshclam_load_error = error
            elif self._freshclam_config:
                # Log number of options loaded (values is a dict in ClamAVConfig)
                num_options = (
                    len(self._freshclam_config.values)
                    if hasattr(self._freshclam_config, "values")
                    and isinstance(self._freshclam_config.values, dict)
                    else 0
                )
                logger.info("Loaded freshclam.conf with %d options", num_options)
                self._freshclam_load_error = None
            self._populate_freshclam_fields()
        except Exception as e:
            logger.exception("Unexpected error loading freshclam.conf: %s", e)
            self._freshclam_load_error = str(e)

        # Load clamd.conf if available
        if self._clamd_available:
            logger.debug("Loading clamd config from: %s", self._clamd_conf_path)
            try:
                self._clamd_config, error = parse_config(self._clamd_conf_path)
                if error:
                    logger.warning("Failed to load clamd.conf: %s", error)
                    self._clamd_load_error = error
                elif self._clamd_config:
                    # Log number of options loaded (values is a dict in ClamAVConfig)
                    num_options = (
                        len(self._clamd_config.values)
                        if hasattr(self._clamd_config, "values")
                        and isinstance(self._clamd_config.values, dict)
                        else 0
                    )
                    logger.info("Loaded clamd.conf with %d options", num_options)
                    self._clamd_load_error = None
                self._populate_clamd_fields()
                self._populate_onaccess_fields()
            except Exception as e:
                logger.exception("Unexpected error loading clamd.conf: %s", e)
                self._clamd_load_error = str(e)

    def _populate_freshclam_fields(self):
        """
        Populate freshclam configuration fields from loaded config.

        Updates UI widgets with values from the parsed freshclam.conf file.
        """
        if not self._freshclam_config:
            return

        DatabasePage.populate_fields(self._freshclam_config, self._freshclam_widgets)

    def _populate_clamd_fields(self):
        """
        Populate clamd configuration fields from loaded config.

        Updates UI widgets with values from the parsed clamd.conf file.
        """
        if not self._clamd_config:
            return

        ScannerPage.populate_fields(self._clamd_config, self._clamd_widgets)

    def _populate_onaccess_fields(self):
        """
        Populate on-access configuration fields from loaded config.

        Updates UI widgets with values from the parsed clamd.conf file.
        """
        if not self._clamd_config:
            return

        OnAccessPage.populate_fields(self._clamd_config, self._onaccess_widgets)

    def _populate_scheduled_fields(self):
        """
        Populate scheduled scan widgets from saved settings.

        Loads settings from the settings manager and updates the UI widgets.
        """
        if not self._settings_manager:
            return

        ScheduledPage.populate_fields(self._settings_manager, self._scheduled_widgets)

    def add_toast(self, toast: Adw.Toast):
        """
        Add a toast notification to the overlay.

        Args:
            toast: The Adw.Toast to display
        """
        self._toast_overlay.add_toast(toast)

    def select_page(self, page_id: str):
        """
        Programmatically select a page in the sidebar.

        Args:
            page_id: The page identifier to select
        """
        if page_id in self._sidebar_rows:
            row = self._sidebar_rows[page_id]
            self._sidebar_list.select_row(row)
