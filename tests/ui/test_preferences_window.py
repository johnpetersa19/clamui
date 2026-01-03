# ClamUI PreferencesWindow Tests
"""
Unit tests for the PreferencesWindow component.

Tests cover:
- Initialization and setup
- UI page creation (database, scanner, scheduled scans, exclusions, save)
- Configuration loading and population
- Form data collection (freshclam, clamd, scheduled scans)
- Save functionality and validation
- Dialog handling (error/success)
- Folder opening
- Permission indicators
- Preset exclusions
"""

import sys
from unittest import mock

import pytest


@pytest.fixture
def mock_settings_manager():
    """Create a mock SettingsManager."""
    manager = mock.MagicMock()
    manager.get = mock.MagicMock(return_value=None)
    manager.set = mock.MagicMock()
    manager.save = mock.MagicMock(return_value=True)
    return manager


@pytest.fixture
def mock_clamav_config():
    """Create a mock ClamAVConfig."""
    config = mock.MagicMock()
    config.has_key = mock.MagicMock(return_value=True)
    config.get_value = mock.MagicMock(return_value="test_value")
    config.set_value = mock.MagicMock()
    return config


def _clear_src_modules():
    """Clear all cached src.* modules to prevent test pollution."""
    modules_to_remove = [mod for mod in sys.modules.keys() if mod.startswith("src.")]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def preferences_window_class(mock_gi_modules):
    """Get PreferencesWindow class with mocked dependencies."""
    # Create mock modules with proper return values
    mock_clamav_config = mock.MagicMock()
    mock_clamav_config.parse_config = mock.MagicMock(return_value=(mock.MagicMock(), None))
    mock_clamav_config.validate_config = mock.MagicMock(return_value=(True, None))
    mock_clamav_config.backup_config = mock.MagicMock()
    mock_clamav_config.write_config_with_elevation = mock.MagicMock(return_value=(True, None))

    mock_scheduler = mock.MagicMock()
    mock_scanner = mock.MagicMock()

    with mock.patch.dict(sys.modules, {
        'src.core.clamav_config': mock_clamav_config,
        'src.core.scheduler': mock_scheduler,
        'src.core.scanner': mock_scanner,
    }):
        # Clear any cached import
        if "src.ui.preferences_window" in sys.modules:
            del sys.modules["src.ui.preferences_window"]

        from src.ui.preferences_window import PreferencesWindow
        yield PreferencesWindow

    # Critical: Clear all src.* modules after test to prevent pollution
    _clear_src_modules()


@pytest.fixture
def mock_preferences_window(preferences_window_class, mock_settings_manager, mock_clamav_config):
    """Create a mock PreferencesWindow instance for testing."""
    # Create instance without calling __init__
    window = object.__new__(preferences_window_class)

    # Set up required attributes
    window._settings_manager = mock_settings_manager
    window._freshclam_widgets = {}
    window._clamd_widgets = {}
    window._scheduled_widgets = {}
    window._clamd_available = False
    window._freshclam_config = mock_clamav_config
    window._clamd_config = mock_clamav_config
    window._freshclam_conf_path = "/etc/clamav/freshclam.conf"
    window._clamd_conf_path = "/etc/clamav/clamd.conf"
    window._is_saving = False
    window._scheduler_error = None
    window._scheduler = mock.MagicMock()

    # Mock internal methods
    window._setup_ui = mock.MagicMock()
    window._load_configs = mock.MagicMock()
    window._populate_scheduled_fields = mock.MagicMock()
    window.set_title = mock.MagicMock()
    window.set_default_size = mock.MagicMock()
    window.set_modal = mock.MagicMock()
    window.set_search_enabled = mock.MagicMock()
    window.add = mock.MagicMock()
    window.present = mock.MagicMock()

    return window


class TestPreferencesWindowImport:
    """Tests for PreferencesWindow import."""

    def test_import_preferences_window(self, mock_gi_modules):
        """Test that PreferencesWindow can be imported."""
        with mock.patch.dict(sys.modules, {
            'src.core.clamav_config': mock.MagicMock(),
            'src.core.scheduler': mock.MagicMock(),
            'src.core.scanner': mock.MagicMock(),
        }):
            from src.ui.preferences_window import PreferencesWindow
            assert PreferencesWindow is not None

    def test_import_preset_exclusions(self, mock_gi_modules):
        """Test that PRESET_EXCLUSIONS can be imported."""
        with mock.patch.dict(sys.modules, {
            'src.core.clamav_config': mock.MagicMock(),
            'src.core.scheduler': mock.MagicMock(),
            'src.core.scanner': mock.MagicMock(),
        }):
            from src.ui.preferences_window import PRESET_EXCLUSIONS
            assert PRESET_EXCLUSIONS is not None
            assert isinstance(PRESET_EXCLUSIONS, list)
            assert len(PRESET_EXCLUSIONS) > 0

    def test_preset_exclusions_structure(self, mock_gi_modules):
        """Test that PRESET_EXCLUSIONS has correct structure."""
        with mock.patch.dict(sys.modules, {
            'src.core.clamav_config': mock.MagicMock(),
            'src.core.scheduler': mock.MagicMock(),
            'src.core.scanner': mock.MagicMock(),
        }):
            from src.ui.preferences_window import PRESET_EXCLUSIONS
            for exclusion in PRESET_EXCLUSIONS:
                assert "pattern" in exclusion
                assert "type" in exclusion
                assert "enabled" in exclusion
                assert "description" in exclusion

    def test_preset_exclusions_contains_common_patterns(self, mock_gi_modules):
        """Test that PRESET_EXCLUSIONS contains common patterns."""
        with mock.patch.dict(sys.modules, {
            'src.core.clamav_config': mock.MagicMock(),
            'src.core.scheduler': mock.MagicMock(),
            'src.core.scanner': mock.MagicMock(),
        }):
            from src.ui.preferences_window import PRESET_EXCLUSIONS
            patterns = [e["pattern"] for e in PRESET_EXCLUSIONS]
            assert "node_modules" in patterns
            assert ".git" in patterns
            assert "__pycache__" in patterns


class TestPreferencesWindowInitialization:
    """Tests for PreferencesWindow initialization."""

    def test_initial_settings_manager_stored(self, mock_preferences_window, mock_settings_manager):
        """Test that settings manager is stored."""
        assert mock_preferences_window._settings_manager is mock_settings_manager

    def test_initial_clamd_available_is_false(self, mock_preferences_window):
        """Test that clamd available is initially False."""
        assert mock_preferences_window._clamd_available is False

    def test_initial_is_saving_is_false(self, mock_preferences_window):
        """Test that is_saving is initially False."""
        assert mock_preferences_window._is_saving is False

    def test_initial_scheduler_error_is_none(self, mock_preferences_window):
        """Test that scheduler error is initially None."""
        assert mock_preferences_window._scheduler_error is None

    def test_initial_config_paths_set(self, mock_preferences_window):
        """Test that config paths are set correctly."""
        assert mock_preferences_window._freshclam_conf_path == "/etc/clamav/freshclam.conf"
        assert mock_preferences_window._clamd_conf_path == "/etc/clamav/clamd.conf"

    def test_widget_dicts_initialized(self, mock_preferences_window):
        """Test that widget dictionaries are initialized."""
        assert isinstance(mock_preferences_window._freshclam_widgets, dict)
        assert isinstance(mock_preferences_window._clamd_widgets, dict)
        assert isinstance(mock_preferences_window._scheduled_widgets, dict)


class TestPreferencesWindowPermissionIndicator:
    """Tests for permission indicator creation."""

    def test_create_permission_indicator_returns_box(self, preferences_window_class, mock_gi_modules):
        """Test that _create_permission_indicator returns a widget."""
        window = object.__new__(preferences_window_class)

        gtk = mock_gi_modules['gtk']
        gtk.Box.return_value = mock.MagicMock()
        gtk.Image.new_from_icon_name.return_value = mock.MagicMock()

        result = window._create_permission_indicator()

        assert result is not None

    def test_create_permission_indicator_uses_lock_icon(self, preferences_window_class, mock_gi_modules):
        """Test that permission indicator uses lock icon."""
        window = object.__new__(preferences_window_class)

        gtk = mock_gi_modules['gtk']
        mock_icon = mock.MagicMock()
        gtk.Image.new_from_icon_name.return_value = mock_icon
        gtk.Box.return_value = mock.MagicMock()

        window._create_permission_indicator()

        gtk.Image.new_from_icon_name.assert_called_with("system-lock-screen-symbolic")


class TestPreferencesWindowFolderOpening:
    """Tests for folder opening functionality."""

    def test_open_folder_nonexistent_shows_dialog(self, preferences_window_class, mock_gi_modules):
        """Test that opening nonexistent folder shows error dialog."""
        window = object.__new__(preferences_window_class)

        adw = mock_gi_modules['adw']
        mock_dialog = mock.MagicMock()
        adw.AlertDialog.return_value = mock_dialog

        with mock.patch('os.path.exists', return_value=False):
            window._open_folder_in_file_manager("/nonexistent/path")

        adw.AlertDialog.assert_called_once()
        mock_dialog.set_heading.assert_called_with("Folder Not Found")

    def test_open_folder_existing_calls_xdg_open(self, preferences_window_class, mock_gi_modules):
        """Test that opening existing folder calls xdg-open."""
        window = object.__new__(preferences_window_class)

        with mock.patch('os.path.exists', return_value=True):
            with mock.patch('subprocess.Popen') as mock_popen:
                window._open_folder_in_file_manager("/existing/path")

                mock_popen.assert_called_once()
                call_args = mock_popen.call_args[0][0]
                assert call_args[0] == 'xdg-open'
                assert call_args[1] == '/existing/path'

    def test_open_folder_exception_shows_dialog(self, preferences_window_class, mock_gi_modules):
        """Test that folder open exception shows error dialog."""
        window = object.__new__(preferences_window_class)

        adw = mock_gi_modules['adw']
        mock_dialog = mock.MagicMock()
        adw.AlertDialog.return_value = mock_dialog

        with mock.patch('os.path.exists', return_value=True):
            with mock.patch('subprocess.Popen', side_effect=Exception("Test error")):
                window._open_folder_in_file_manager("/existing/path")

        adw.AlertDialog.assert_called_once()
        mock_dialog.set_heading.assert_called_with("Error Opening Folder")


class TestPreferencesWindowCollectFreshclamData:
    """Tests for freshclam data collection."""

    def test_collect_freshclam_data_returns_dict(self, preferences_window_class, mock_gi_modules):
        """Test that _collect_freshclam_data returns a dictionary."""
        window = object.__new__(preferences_window_class)
        window._freshclam_widgets = {
            'DatabaseDirectory': mock.MagicMock(get_text=mock.MagicMock(return_value="/var/lib/clamav")),
            'UpdateLogFile': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'NotifyClamd': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'LogVerbose': mock.MagicMock(get_active=mock.MagicMock(return_value=True)),
            'LogSyslog': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'Checks': mock.MagicMock(get_value=mock.MagicMock(return_value=24)),
            'DatabaseMirror': mock.MagicMock(get_text=mock.MagicMock(return_value="database.clamav.net")),
            'HTTPProxyServer': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'HTTPProxyPort': mock.MagicMock(get_value=mock.MagicMock(return_value=0)),
            'HTTPProxyUsername': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'HTTPProxyPassword': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
        }

        result = window._collect_freshclam_data()

        assert isinstance(result, dict)
        assert result['DatabaseDirectory'] == "/var/lib/clamav"
        assert result['LogVerbose'] == 'yes'
        assert result['LogSyslog'] == 'no'
        assert result['Checks'] == '24'
        assert result['DatabaseMirror'] == "database.clamav.net"

    def test_collect_freshclam_data_excludes_empty_fields(self, preferences_window_class, mock_gi_modules):
        """Test that empty fields are excluded from collection."""
        window = object.__new__(preferences_window_class)
        window._freshclam_widgets = {
            'DatabaseDirectory': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'UpdateLogFile': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'NotifyClamd': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'LogVerbose': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'LogSyslog': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'Checks': mock.MagicMock(get_value=mock.MagicMock(return_value=0)),
            'DatabaseMirror': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'HTTPProxyServer': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'HTTPProxyPort': mock.MagicMock(get_value=mock.MagicMock(return_value=0)),
            'HTTPProxyUsername': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'HTTPProxyPassword': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
        }

        result = window._collect_freshclam_data()

        # Empty paths should not be in result
        assert 'DatabaseDirectory' not in result
        assert 'UpdateLogFile' not in result
        assert 'DatabaseMirror' not in result

    def test_collect_freshclam_data_includes_proxy_when_set(self, preferences_window_class, mock_gi_modules):
        """Test that proxy settings are included when set."""
        window = object.__new__(preferences_window_class)
        window._freshclam_widgets = {
            'DatabaseDirectory': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'UpdateLogFile': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'NotifyClamd': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'LogVerbose': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'LogSyslog': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'Checks': mock.MagicMock(get_value=mock.MagicMock(return_value=0)),
            'DatabaseMirror': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'HTTPProxyServer': mock.MagicMock(get_text=mock.MagicMock(return_value="proxy.example.com")),
            'HTTPProxyPort': mock.MagicMock(get_value=mock.MagicMock(return_value=8080)),
            'HTTPProxyUsername': mock.MagicMock(get_text=mock.MagicMock(return_value="user")),
            'HTTPProxyPassword': mock.MagicMock(get_text=mock.MagicMock(return_value="pass")),
        }

        result = window._collect_freshclam_data()

        assert result['HTTPProxyServer'] == "proxy.example.com"
        assert result['HTTPProxyPort'] == '8080'
        assert result['HTTPProxyUsername'] == "user"
        assert result['HTTPProxyPassword'] == "pass"


class TestPreferencesWindowCollectClamdData:
    """Tests for clamd data collection."""

    def test_collect_clamd_data_returns_empty_when_unavailable(self, preferences_window_class, mock_gi_modules):
        """Test that empty dict is returned when clamd unavailable."""
        window = object.__new__(preferences_window_class)
        window._clamd_available = False

        result = window._collect_clamd_data()

        assert result == {}

    def test_collect_clamd_data_returns_dict_when_available(self, preferences_window_class, mock_gi_modules):
        """Test that dict is returned when clamd available."""
        window = object.__new__(preferences_window_class)
        window._clamd_available = True
        window._clamd_widgets = {
            'ScanPE': mock.MagicMock(get_active=mock.MagicMock(return_value=True)),
            'ScanELF': mock.MagicMock(get_active=mock.MagicMock(return_value=True)),
            'ScanOLE2': mock.MagicMock(get_active=mock.MagicMock(return_value=True)),
            'ScanPDF': mock.MagicMock(get_active=mock.MagicMock(return_value=True)),
            'ScanHTML': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'ScanArchive': mock.MagicMock(get_active=mock.MagicMock(return_value=True)),
            'MaxFileSize': mock.MagicMock(get_value=mock.MagicMock(return_value=100)),
            'MaxScanSize': mock.MagicMock(get_value=mock.MagicMock(return_value=200)),
            'MaxRecursion': mock.MagicMock(get_value=mock.MagicMock(return_value=16)),
            'MaxFiles': mock.MagicMock(get_value=mock.MagicMock(return_value=10000)),
            'LogFile': mock.MagicMock(get_text=mock.MagicMock(return_value="/var/log/clamav/clamd.log")),
            'LogVerbose': mock.MagicMock(get_active=mock.MagicMock(return_value=True)),
            'LogSyslog': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
        }

        result = window._collect_clamd_data()

        assert result['ScanPE'] == 'yes'
        assert result['ScanELF'] == 'yes'
        assert result['ScanHTML'] == 'no'
        assert result['MaxFileSize'] == '100'
        assert result['MaxScanSize'] == '200'
        assert result['MaxRecursion'] == '16'
        assert result['MaxFiles'] == '10000'
        assert result['LogFile'] == '/var/log/clamav/clamd.log'
        assert result['LogVerbose'] == 'yes'
        assert result['LogSyslog'] == 'no'


class TestPreferencesWindowCollectOnAccessData:
    """Tests for on-access data collection."""

    def test_collect_onaccess_data_returns_empty_when_unavailable(self, preferences_window_class, mock_gi_modules):
        """Test that empty dict is returned when clamd unavailable."""
        window = object.__new__(preferences_window_class)
        window._clamd_available = False

        result = window._collect_onaccess_data()

        assert result == {}

    def test_collect_onaccess_data_returns_dict_when_available(self, preferences_window_class, mock_gi_modules):
        """Test that dict is returned when clamd available with all settings."""
        window = object.__new__(preferences_window_class)
        window._clamd_available = True
        window._onaccess_widgets = {
            'OnAccessIncludePath': mock.MagicMock(get_text=mock.MagicMock(return_value="/home, /var")),
            'OnAccessExcludePath': mock.MagicMock(get_text=mock.MagicMock(return_value="/tmp, /proc")),
            'OnAccessPrevention': mock.MagicMock(get_active=mock.MagicMock(return_value=True)),
            'OnAccessExtraScanning': mock.MagicMock(get_active=mock.MagicMock(return_value=True)),
            'OnAccessDenyOnError': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessDisableDDD': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessMaxThreads': mock.MagicMock(get_value=mock.MagicMock(return_value=5)),
            'OnAccessMaxFileSize': mock.MagicMock(get_value=mock.MagicMock(return_value=100)),
            'OnAccessCurlTimeout': mock.MagicMock(get_value=mock.MagicMock(return_value=30)),
            'OnAccessRetryAttempts': mock.MagicMock(get_value=mock.MagicMock(return_value=3)),
            'OnAccessExcludeUname': mock.MagicMock(get_text=mock.MagicMock(return_value="clamav")),
            'OnAccessExcludeUID': mock.MagicMock(get_value=mock.MagicMock(return_value=1000)),
            'OnAccessExcludeRootUID': mock.MagicMock(get_active=mock.MagicMock(return_value=True)),
        }

        result = window._collect_onaccess_data()

        assert result['OnAccessIncludePath'] == ['/home', '/var']
        assert result['OnAccessExcludePath'] == ['/tmp', '/proc']
        assert result['OnAccessPrevention'] == 'yes'
        assert result['OnAccessExtraScanning'] == 'yes'
        assert result['OnAccessDenyOnError'] == 'no'
        assert result['OnAccessDisableDDD'] == 'no'
        assert result['OnAccessMaxThreads'] == '5'
        assert result['OnAccessMaxFileSize'] == '100'
        assert result['OnAccessCurlTimeout'] == '30'
        assert result['OnAccessRetryAttempts'] == '3'
        assert result['OnAccessExcludeUname'] == 'clamav'
        assert result['OnAccessExcludeUID'] == '1000'
        assert result['OnAccessExcludeRootUID'] == 'yes'

    def test_collect_onaccess_data_parses_include_paths(self, preferences_window_class, mock_gi_modules):
        """Test that include paths are parsed from comma-separated values."""
        window = object.__new__(preferences_window_class)
        window._clamd_available = True
        window._onaccess_widgets = {
            'OnAccessIncludePath': mock.MagicMock(get_text=mock.MagicMock(return_value="/home/user, /var/data, /opt")),
            'OnAccessExcludePath': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'OnAccessPrevention': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessExtraScanning': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessDenyOnError': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessDisableDDD': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessMaxThreads': mock.MagicMock(get_value=mock.MagicMock(return_value=5)),
            'OnAccessMaxFileSize': mock.MagicMock(get_value=mock.MagicMock(return_value=100)),
            'OnAccessCurlTimeout': mock.MagicMock(get_value=mock.MagicMock(return_value=30)),
            'OnAccessRetryAttempts': mock.MagicMock(get_value=mock.MagicMock(return_value=3)),
            'OnAccessExcludeUname': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'OnAccessExcludeUID': mock.MagicMock(get_value=mock.MagicMock(return_value=0)),
            'OnAccessExcludeRootUID': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
        }

        result = window._collect_onaccess_data()

        assert result['OnAccessIncludePath'] == ['/home/user', '/var/data', '/opt']

    def test_collect_onaccess_data_excludes_empty_paths(self, preferences_window_class, mock_gi_modules):
        """Test that empty paths are not included in result."""
        window = object.__new__(preferences_window_class)
        window._clamd_available = True
        window._onaccess_widgets = {
            'OnAccessIncludePath': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'OnAccessExcludePath': mock.MagicMock(get_text=mock.MagicMock(return_value="   ")),
            'OnAccessPrevention': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessExtraScanning': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessDenyOnError': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessDisableDDD': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessMaxThreads': mock.MagicMock(get_value=mock.MagicMock(return_value=5)),
            'OnAccessMaxFileSize': mock.MagicMock(get_value=mock.MagicMock(return_value=100)),
            'OnAccessCurlTimeout': mock.MagicMock(get_value=mock.MagicMock(return_value=30)),
            'OnAccessRetryAttempts': mock.MagicMock(get_value=mock.MagicMock(return_value=3)),
            'OnAccessExcludeUname': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'OnAccessExcludeUID': mock.MagicMock(get_value=mock.MagicMock(return_value=0)),
            'OnAccessExcludeRootUID': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
        }

        result = window._collect_onaccess_data()

        assert 'OnAccessIncludePath' not in result
        assert 'OnAccessExcludePath' not in result

    def test_collect_onaccess_data_behavior_switches_yes_no(self, preferences_window_class, mock_gi_modules):
        """Test that behavior switches correctly return 'yes' and 'no' values."""
        window = object.__new__(preferences_window_class)
        window._clamd_available = True
        window._onaccess_widgets = {
            'OnAccessIncludePath': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'OnAccessExcludePath': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'OnAccessPrevention': mock.MagicMock(get_active=mock.MagicMock(return_value=True)),
            'OnAccessExtraScanning': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessDenyOnError': mock.MagicMock(get_active=mock.MagicMock(return_value=True)),
            'OnAccessDisableDDD': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessMaxThreads': mock.MagicMock(get_value=mock.MagicMock(return_value=5)),
            'OnAccessMaxFileSize': mock.MagicMock(get_value=mock.MagicMock(return_value=100)),
            'OnAccessCurlTimeout': mock.MagicMock(get_value=mock.MagicMock(return_value=30)),
            'OnAccessRetryAttempts': mock.MagicMock(get_value=mock.MagicMock(return_value=3)),
            'OnAccessExcludeUname': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'OnAccessExcludeUID': mock.MagicMock(get_value=mock.MagicMock(return_value=0)),
            'OnAccessExcludeRootUID': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
        }

        result = window._collect_onaccess_data()

        assert result['OnAccessPrevention'] == 'yes'
        assert result['OnAccessExtraScanning'] == 'no'
        assert result['OnAccessDenyOnError'] == 'yes'
        assert result['OnAccessDisableDDD'] == 'no'

    def test_collect_onaccess_data_performance_settings_as_strings(self, preferences_window_class, mock_gi_modules):
        """Test that performance settings are returned as string numbers."""
        window = object.__new__(preferences_window_class)
        window._clamd_available = True
        window._onaccess_widgets = {
            'OnAccessIncludePath': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'OnAccessExcludePath': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'OnAccessPrevention': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessExtraScanning': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessDenyOnError': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessDisableDDD': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessMaxThreads': mock.MagicMock(get_value=mock.MagicMock(return_value=10)),
            'OnAccessMaxFileSize': mock.MagicMock(get_value=mock.MagicMock(return_value=250)),
            'OnAccessCurlTimeout': mock.MagicMock(get_value=mock.MagicMock(return_value=60)),
            'OnAccessRetryAttempts': mock.MagicMock(get_value=mock.MagicMock(return_value=5)),
            'OnAccessExcludeUname': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'OnAccessExcludeUID': mock.MagicMock(get_value=mock.MagicMock(return_value=0)),
            'OnAccessExcludeRootUID': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
        }

        result = window._collect_onaccess_data()

        assert result['OnAccessMaxThreads'] == '10'
        assert result['OnAccessMaxFileSize'] == '250'
        assert result['OnAccessCurlTimeout'] == '60'
        assert result['OnAccessRetryAttempts'] == '5'
        # Verify they're strings
        assert isinstance(result['OnAccessMaxThreads'], str)
        assert isinstance(result['OnAccessMaxFileSize'], str)

    def test_collect_onaccess_data_excludes_empty_username(self, preferences_window_class, mock_gi_modules):
        """Test that empty username is not included in result."""
        window = object.__new__(preferences_window_class)
        window._clamd_available = True
        window._onaccess_widgets = {
            'OnAccessIncludePath': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'OnAccessExcludePath': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'OnAccessPrevention': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessExtraScanning': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessDenyOnError': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessDisableDDD': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessMaxThreads': mock.MagicMock(get_value=mock.MagicMock(return_value=5)),
            'OnAccessMaxFileSize': mock.MagicMock(get_value=mock.MagicMock(return_value=100)),
            'OnAccessCurlTimeout': mock.MagicMock(get_value=mock.MagicMock(return_value=30)),
            'OnAccessRetryAttempts': mock.MagicMock(get_value=mock.MagicMock(return_value=3)),
            'OnAccessExcludeUname': mock.MagicMock(get_text=mock.MagicMock(return_value="   ")),
            'OnAccessExcludeUID': mock.MagicMock(get_value=mock.MagicMock(return_value=0)),
            'OnAccessExcludeRootUID': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
        }

        result = window._collect_onaccess_data()

        assert 'OnAccessExcludeUname' not in result

    def test_collect_onaccess_data_exclude_uid_as_string(self, preferences_window_class, mock_gi_modules):
        """Test that ExcludeUID is always included as a string number."""
        window = object.__new__(preferences_window_class)
        window._clamd_available = True
        window._onaccess_widgets = {
            'OnAccessIncludePath': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'OnAccessExcludePath': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'OnAccessPrevention': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessExtraScanning': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessDenyOnError': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessDisableDDD': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessMaxThreads': mock.MagicMock(get_value=mock.MagicMock(return_value=5)),
            'OnAccessMaxFileSize': mock.MagicMock(get_value=mock.MagicMock(return_value=100)),
            'OnAccessCurlTimeout': mock.MagicMock(get_value=mock.MagicMock(return_value=30)),
            'OnAccessRetryAttempts': mock.MagicMock(get_value=mock.MagicMock(return_value=3)),
            'OnAccessExcludeUname': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'OnAccessExcludeUID': mock.MagicMock(get_value=mock.MagicMock(return_value=1001)),
            'OnAccessExcludeRootUID': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
        }

        result = window._collect_onaccess_data()

        assert result['OnAccessExcludeUID'] == '1001'
        assert isinstance(result['OnAccessExcludeUID'], str)

    def test_collect_onaccess_data_exclude_root_uid_yes_no(self, preferences_window_class, mock_gi_modules):
        """Test that ExcludeRootUID returns 'yes' or 'no'."""
        window = object.__new__(preferences_window_class)
        window._clamd_available = True
        window._onaccess_widgets = {
            'OnAccessIncludePath': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'OnAccessExcludePath': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'OnAccessPrevention': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessExtraScanning': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessDenyOnError': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessDisableDDD': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'OnAccessMaxThreads': mock.MagicMock(get_value=mock.MagicMock(return_value=5)),
            'OnAccessMaxFileSize': mock.MagicMock(get_value=mock.MagicMock(return_value=100)),
            'OnAccessCurlTimeout': mock.MagicMock(get_value=mock.MagicMock(return_value=30)),
            'OnAccessRetryAttempts': mock.MagicMock(get_value=mock.MagicMock(return_value=3)),
            'OnAccessExcludeUname': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'OnAccessExcludeUID': mock.MagicMock(get_value=mock.MagicMock(return_value=0)),
            'OnAccessExcludeRootUID': mock.MagicMock(get_active=mock.MagicMock(return_value=True)),
        }

        result = window._collect_onaccess_data()
        assert result['OnAccessExcludeRootUID'] == 'yes'

        # Test with False
        window._onaccess_widgets['OnAccessExcludeRootUID'].get_active.return_value = False
        result = window._collect_onaccess_data()
        assert result['OnAccessExcludeRootUID'] == 'no'


class TestPreferencesWindowCollectScheduledData:
    """Tests for scheduled scan data collection."""

    def test_collect_scheduled_data_returns_dict(self, preferences_window_class, mock_gi_modules):
        """Test that _collect_scheduled_data returns a dictionary."""
        window = object.__new__(preferences_window_class)
        window._scheduled_widgets = {
            'enabled': mock.MagicMock(get_active=mock.MagicMock(return_value=True)),
            'frequency': mock.MagicMock(get_selected=mock.MagicMock(return_value=1)),
            'time': mock.MagicMock(get_text=mock.MagicMock(return_value="02:00")),
            'targets': mock.MagicMock(get_text=mock.MagicMock(return_value="/home/user")),
            'day_of_week': mock.MagicMock(get_selected=mock.MagicMock(return_value=0)),
            'day_of_month': mock.MagicMock(get_value=mock.MagicMock(return_value=1)),
            'skip_on_battery': mock.MagicMock(get_active=mock.MagicMock(return_value=True)),
            'auto_quarantine': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
        }

        result = window._collect_scheduled_data()

        assert result['scheduled_scans_enabled'] is True
        assert result['schedule_frequency'] == 'daily'
        assert result['schedule_time'] == '02:00'
        assert result['schedule_targets'] == ['/home/user']
        assert result['schedule_day_of_week'] == 0
        assert result['schedule_day_of_month'] == 1
        assert result['schedule_skip_on_battery'] is True
        assert result['schedule_auto_quarantine'] is False

    def test_collect_scheduled_data_parses_multiple_targets(self, preferences_window_class, mock_gi_modules):
        """Test that multiple targets are parsed correctly."""
        window = object.__new__(preferences_window_class)
        window._scheduled_widgets = {
            'enabled': mock.MagicMock(get_active=mock.MagicMock(return_value=True)),
            'frequency': mock.MagicMock(get_selected=mock.MagicMock(return_value=0)),
            'time': mock.MagicMock(get_text=mock.MagicMock(return_value="03:00")),
            'targets': mock.MagicMock(get_text=mock.MagicMock(return_value="/home/user, /var/data, /opt")),
            'day_of_week': mock.MagicMock(get_selected=mock.MagicMock(return_value=0)),
            'day_of_month': mock.MagicMock(get_value=mock.MagicMock(return_value=1)),
            'skip_on_battery': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'auto_quarantine': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
        }

        result = window._collect_scheduled_data()

        assert result['schedule_targets'] == ['/home/user', '/var/data', '/opt']

    def test_collect_scheduled_data_frequency_mapping(self, preferences_window_class, mock_gi_modules):
        """Test that frequency is correctly mapped."""
        window = object.__new__(preferences_window_class)

        frequencies = [
            (0, 'hourly'),
            (1, 'daily'),
            (2, 'weekly'),
            (3, 'monthly'),
        ]

        for selected, expected in frequencies:
            window._scheduled_widgets = {
                'enabled': mock.MagicMock(get_active=mock.MagicMock(return_value=True)),
                'frequency': mock.MagicMock(get_selected=mock.MagicMock(return_value=selected)),
                'time': mock.MagicMock(get_text=mock.MagicMock(return_value="02:00")),
                'targets': mock.MagicMock(get_text=mock.MagicMock(return_value="/home")),
                'day_of_week': mock.MagicMock(get_selected=mock.MagicMock(return_value=0)),
                'day_of_month': mock.MagicMock(get_value=mock.MagicMock(return_value=1)),
                'skip_on_battery': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
                'auto_quarantine': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            }

            result = window._collect_scheduled_data()
            assert result['schedule_frequency'] == expected

    def test_collect_scheduled_data_empty_time_defaults(self, preferences_window_class, mock_gi_modules):
        """Test that empty time defaults to 02:00."""
        window = object.__new__(preferences_window_class)
        window._scheduled_widgets = {
            'enabled': mock.MagicMock(get_active=mock.MagicMock(return_value=True)),
            'frequency': mock.MagicMock(get_selected=mock.MagicMock(return_value=1)),
            'time': mock.MagicMock(get_text=mock.MagicMock(return_value="   ")),
            'targets': mock.MagicMock(get_text=mock.MagicMock(return_value="/home")),
            'day_of_week': mock.MagicMock(get_selected=mock.MagicMock(return_value=0)),
            'day_of_month': mock.MagicMock(get_value=mock.MagicMock(return_value=1)),
            'skip_on_battery': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'auto_quarantine': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
        }

        result = window._collect_scheduled_data()

        assert result['schedule_time'] == '02:00'


class TestPreferencesWindowPopulateFreshclamFields:
    """Tests for freshclam field population."""

    def test_populate_freshclam_fields_returns_when_no_config(self, preferences_window_class, mock_gi_modules):
        """Test that population returns early when no config."""
        window = object.__new__(preferences_window_class)
        window._freshclam_config = None
        window._freshclam_widgets = {}

        # Should not raise
        window._populate_freshclam_fields()

    def test_populate_freshclam_fields_sets_database_directory(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that DatabaseDirectory is populated."""
        window = object.__new__(preferences_window_class)
        window._freshclam_config = mock_clamav_config
        mock_clamav_config.get_value.return_value = "/var/lib/clamav"
        # Only return True for the key we're testing
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'DatabaseDirectory')

        mock_widget = mock.MagicMock()
        window._freshclam_widgets = {'DatabaseDirectory': mock_widget}

        window._populate_freshclam_fields()

        mock_widget.set_text.assert_called_with("/var/lib/clamav")

    def test_populate_freshclam_fields_sets_log_verbose_true(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that LogVerbose is set to True when config says 'yes'."""
        window = object.__new__(preferences_window_class)
        window._freshclam_config = mock_clamav_config
        mock_clamav_config.get_value.return_value = "yes"
        # Only return True for the key we're testing
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'LogVerbose')

        mock_widget = mock.MagicMock()
        window._freshclam_widgets = {'LogVerbose': mock_widget}

        window._populate_freshclam_fields()

        mock_widget.set_active.assert_called_with(True)

    def test_populate_freshclam_fields_sets_log_verbose_false(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that LogVerbose is set to False when config says 'no'."""
        window = object.__new__(preferences_window_class)
        window._freshclam_config = mock_clamav_config
        mock_clamav_config.get_value.return_value = "no"
        # Only return True for the key we're testing
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'LogVerbose')

        mock_widget = mock.MagicMock()
        window._freshclam_widgets = {'LogVerbose': mock_widget}

        window._populate_freshclam_fields()

        mock_widget.set_active.assert_called_with(False)

    def test_populate_freshclam_fields_handles_invalid_checks(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that invalid Checks value is handled."""
        window = object.__new__(preferences_window_class)
        window._freshclam_config = mock_clamav_config
        mock_clamav_config.get_value.return_value = "not_a_number"
        # Only return True for the key we're testing
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'Checks')

        mock_widget = mock.MagicMock()
        window._freshclam_widgets = {'Checks': mock_widget}

        # Should not raise
        window._populate_freshclam_fields()

        # set_value should not be called with invalid value
        mock_widget.set_value.assert_not_called()


class TestPreferencesWindowPopulateClamdFields:
    """Tests for clamd field population."""

    def test_populate_clamd_fields_returns_when_no_config(self, preferences_window_class, mock_gi_modules):
        """Test that population returns early when no config."""
        window = object.__new__(preferences_window_class)
        window._clamd_config = None
        window._clamd_widgets = {}

        # Should not raise
        window._populate_clamd_fields()

    def test_populate_clamd_fields_sets_scan_pe(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that ScanPE is populated."""
        window = object.__new__(preferences_window_class)
        window._clamd_config = mock_clamav_config
        mock_clamav_config.get_value.return_value = "yes"
        # Only return True for the key we're testing
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'ScanPE')

        mock_widget = mock.MagicMock()
        window._clamd_widgets = {'ScanPE': mock_widget}

        window._populate_clamd_fields()

        mock_widget.set_active.assert_called_with(True)

    def test_populate_clamd_fields_sets_max_file_size(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that MaxFileSize is populated."""
        window = object.__new__(preferences_window_class)
        window._clamd_config = mock_clamav_config
        mock_clamav_config.get_value.return_value = "100"
        # Only return True for the key we're testing
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'MaxFileSize')

        mock_widget = mock.MagicMock()
        window._clamd_widgets = {'MaxFileSize': mock_widget}

        window._populate_clamd_fields()

        mock_widget.set_value.assert_called_with(100)

    def test_populate_clamd_fields_handles_invalid_max_file_size(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that invalid MaxFileSize is handled."""
        window = object.__new__(preferences_window_class)
        window._clamd_config = mock_clamav_config
        mock_clamav_config.get_value.return_value = "invalid"
        # Only return True for the key we're testing
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'MaxFileSize')

        mock_widget = mock.MagicMock()
        window._clamd_widgets = {'MaxFileSize': mock_widget}

        # Should not raise
        window._populate_clamd_fields()

        mock_widget.set_value.assert_not_called()


class TestPreferencesWindowPopulateOnAccessFields:
    """Tests for on-access field population."""

    def test_populate_onaccess_fields_returns_when_no_config(self, preferences_window_class, mock_gi_modules):
        """Test that population returns early when no config."""
        window = object.__new__(preferences_window_class)
        window._clamd_config = None
        window._onaccess_widgets = {}

        # Should not raise
        window._populate_onaccess_fields()

    def test_populate_onaccess_fields_sets_include_path(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that OnAccessIncludePath is populated from multiple values."""
        window = object.__new__(preferences_window_class)
        window._clamd_config = mock_clamav_config
        mock_clamav_config.get_values = mock.MagicMock(return_value=["/home", "/var"])
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'OnAccessIncludePath')

        mock_widget = mock.MagicMock()
        window._onaccess_widgets = {'OnAccessIncludePath': mock_widget}

        window._populate_onaccess_fields()

        mock_widget.set_text.assert_called_with("/home, /var")

    def test_populate_onaccess_fields_sets_exclude_path(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that OnAccessExcludePath is populated from multiple values."""
        window = object.__new__(preferences_window_class)
        window._clamd_config = mock_clamav_config
        mock_clamav_config.get_values = mock.MagicMock(return_value=["/tmp", "/proc"])
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'OnAccessExcludePath')

        mock_widget = mock.MagicMock()
        window._onaccess_widgets = {'OnAccessExcludePath': mock_widget}

        window._populate_onaccess_fields()

        mock_widget.set_text.assert_called_with("/tmp, /proc")

    def test_populate_onaccess_fields_sets_prevention_true(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that OnAccessPrevention is set to True when config says 'yes'."""
        window = object.__new__(preferences_window_class)
        window._clamd_config = mock_clamav_config
        mock_clamav_config.get_value.return_value = "yes"
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'OnAccessPrevention')

        mock_widget = mock.MagicMock()
        window._onaccess_widgets = {'OnAccessPrevention': mock_widget}

        window._populate_onaccess_fields()

        mock_widget.set_active.assert_called_with(True)

    def test_populate_onaccess_fields_sets_prevention_false(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that OnAccessPrevention is set to False when config says 'no'."""
        window = object.__new__(preferences_window_class)
        window._clamd_config = mock_clamav_config
        mock_clamav_config.get_value.return_value = "no"
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'OnAccessPrevention')

        mock_widget = mock.MagicMock()
        window._onaccess_widgets = {'OnAccessPrevention': mock_widget}

        window._populate_onaccess_fields()

        mock_widget.set_active.assert_called_with(False)

    def test_populate_onaccess_fields_sets_extra_scanning(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that OnAccessExtraScanning is populated."""
        window = object.__new__(preferences_window_class)
        window._clamd_config = mock_clamav_config
        mock_clamav_config.get_value.return_value = "yes"
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'OnAccessExtraScanning')

        mock_widget = mock.MagicMock()
        window._onaccess_widgets = {'OnAccessExtraScanning': mock_widget}

        window._populate_onaccess_fields()

        mock_widget.set_active.assert_called_with(True)

    def test_populate_onaccess_fields_sets_deny_on_error(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that OnAccessDenyOnError is populated."""
        window = object.__new__(preferences_window_class)
        window._clamd_config = mock_clamav_config
        mock_clamav_config.get_value.return_value = "yes"
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'OnAccessDenyOnError')

        mock_widget = mock.MagicMock()
        window._onaccess_widgets = {'OnAccessDenyOnError': mock_widget}

        window._populate_onaccess_fields()

        mock_widget.set_active.assert_called_with(True)

    def test_populate_onaccess_fields_sets_disable_ddd(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that OnAccessDisableDDD is populated."""
        window = object.__new__(preferences_window_class)
        window._clamd_config = mock_clamav_config
        mock_clamav_config.get_value.return_value = "no"
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'OnAccessDisableDDD')

        mock_widget = mock.MagicMock()
        window._onaccess_widgets = {'OnAccessDisableDDD': mock_widget}

        window._populate_onaccess_fields()

        mock_widget.set_active.assert_called_with(False)

    def test_populate_onaccess_fields_sets_max_threads(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that OnAccessMaxThreads is populated."""
        window = object.__new__(preferences_window_class)
        window._clamd_config = mock_clamav_config
        mock_clamav_config.get_value.return_value = "5"
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'OnAccessMaxThreads')

        mock_widget = mock.MagicMock()
        window._onaccess_widgets = {'OnAccessMaxThreads': mock_widget}

        window._populate_onaccess_fields()

        mock_widget.set_value.assert_called_with(5)

    def test_populate_onaccess_fields_handles_invalid_max_threads(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that invalid OnAccessMaxThreads is handled."""
        window = object.__new__(preferences_window_class)
        window._clamd_config = mock_clamav_config
        mock_clamav_config.get_value.return_value = "invalid"
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'OnAccessMaxThreads')

        mock_widget = mock.MagicMock()
        window._onaccess_widgets = {'OnAccessMaxThreads': mock_widget}

        # Should not raise
        window._populate_onaccess_fields()

        mock_widget.set_value.assert_not_called()

    def test_populate_onaccess_fields_sets_max_file_size(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that OnAccessMaxFileSize is populated."""
        window = object.__new__(preferences_window_class)
        window._clamd_config = mock_clamav_config
        mock_clamav_config.get_value.return_value = "100"
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'OnAccessMaxFileSize')

        mock_widget = mock.MagicMock()
        window._onaccess_widgets = {'OnAccessMaxFileSize': mock_widget}

        window._populate_onaccess_fields()

        mock_widget.set_value.assert_called_with(100)

    def test_populate_onaccess_fields_handles_invalid_max_file_size(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that invalid OnAccessMaxFileSize is handled."""
        window = object.__new__(preferences_window_class)
        window._clamd_config = mock_clamav_config
        mock_clamav_config.get_value.return_value = "not_a_number"
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'OnAccessMaxFileSize')

        mock_widget = mock.MagicMock()
        window._onaccess_widgets = {'OnAccessMaxFileSize': mock_widget}

        # Should not raise
        window._populate_onaccess_fields()

        mock_widget.set_value.assert_not_called()

    def test_populate_onaccess_fields_sets_curl_timeout(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that OnAccessCurlTimeout is populated."""
        window = object.__new__(preferences_window_class)
        window._clamd_config = mock_clamav_config
        mock_clamav_config.get_value.return_value = "30"
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'OnAccessCurlTimeout')

        mock_widget = mock.MagicMock()
        window._onaccess_widgets = {'OnAccessCurlTimeout': mock_widget}

        window._populate_onaccess_fields()

        mock_widget.set_value.assert_called_with(30)

    def test_populate_onaccess_fields_sets_retry_attempts(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that OnAccessRetryAttempts is populated."""
        window = object.__new__(preferences_window_class)
        window._clamd_config = mock_clamav_config
        mock_clamav_config.get_value.return_value = "3"
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'OnAccessRetryAttempts')

        mock_widget = mock.MagicMock()
        window._onaccess_widgets = {'OnAccessRetryAttempts': mock_widget}

        window._populate_onaccess_fields()

        mock_widget.set_value.assert_called_with(3)

    def test_populate_onaccess_fields_sets_exclude_uname(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that OnAccessExcludeUname is populated."""
        window = object.__new__(preferences_window_class)
        window._clamd_config = mock_clamav_config
        mock_clamav_config.get_value.return_value = "clamav"
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'OnAccessExcludeUname')

        mock_widget = mock.MagicMock()
        window._onaccess_widgets = {'OnAccessExcludeUname': mock_widget}

        window._populate_onaccess_fields()

        mock_widget.set_text.assert_called_with("clamav")

    def test_populate_onaccess_fields_sets_exclude_uid(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that OnAccessExcludeUID is populated."""
        window = object.__new__(preferences_window_class)
        window._clamd_config = mock_clamav_config
        mock_clamav_config.get_value.return_value = "1000"
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'OnAccessExcludeUID')

        mock_widget = mock.MagicMock()
        window._onaccess_widgets = {'OnAccessExcludeUID': mock_widget}

        window._populate_onaccess_fields()

        mock_widget.set_value.assert_called_with(1000)

    def test_populate_onaccess_fields_handles_invalid_exclude_uid(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that invalid OnAccessExcludeUID is handled."""
        window = object.__new__(preferences_window_class)
        window._clamd_config = mock_clamav_config
        mock_clamav_config.get_value.return_value = "invalid_uid"
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'OnAccessExcludeUID')

        mock_widget = mock.MagicMock()
        window._onaccess_widgets = {'OnAccessExcludeUID': mock_widget}

        # Should not raise
        window._populate_onaccess_fields()

        mock_widget.set_value.assert_not_called()

    def test_populate_onaccess_fields_sets_exclude_root_uid(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that OnAccessExcludeRootUID is populated."""
        window = object.__new__(preferences_window_class)
        window._clamd_config = mock_clamav_config
        mock_clamav_config.get_value.return_value = "yes"
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'OnAccessExcludeRootUID')

        mock_widget = mock.MagicMock()
        window._onaccess_widgets = {'OnAccessExcludeRootUID': mock_widget}

        window._populate_onaccess_fields()

        mock_widget.set_active.assert_called_with(True)

    def test_populate_onaccess_fields_empty_paths_not_set(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that empty path lists do not trigger set_text."""
        window = object.__new__(preferences_window_class)
        window._clamd_config = mock_clamav_config
        mock_clamav_config.get_values = mock.MagicMock(return_value=[])
        mock_clamav_config.has_key = mock.MagicMock(side_effect=lambda k: k == 'OnAccessIncludePath')

        mock_widget = mock.MagicMock()
        window._onaccess_widgets = {'OnAccessIncludePath': mock_widget}

        window._populate_onaccess_fields()

        mock_widget.set_text.assert_not_called()


class TestPreferencesWindowPopulateScheduledFields:
    """Tests for scheduled fields population."""

    def test_populate_scheduled_fields_sets_enabled(self, preferences_window_class, mock_settings_manager, mock_gi_modules):
        """Test that enabled switch is populated."""
        window = object.__new__(preferences_window_class)
        window._settings_manager = mock_settings_manager
        # Return appropriate values for different settings keys
        def mock_get(key, default=None):
            settings = {
                "scheduled_scans_enabled": True,
                "schedule_frequency": "daily",
                "schedule_time": "02:00",
                "schedule_targets": [],
                "schedule_day_of_week": 0,
                "schedule_day_of_month": 1,
                "schedule_skip_on_battery": True,
                "schedule_auto_quarantine": False,
            }
            return settings.get(key, default)
        mock_settings_manager.get.side_effect = mock_get

        mock_widget = mock.MagicMock()
        window._scheduled_widgets = {
            'enabled': mock_widget,
            'frequency': mock.MagicMock(),
            'time': mock.MagicMock(),
            'targets': mock.MagicMock(),
            'day_of_week': mock.MagicMock(),
            'day_of_month': mock.MagicMock(),
            'skip_on_battery': mock.MagicMock(),
            'auto_quarantine': mock.MagicMock(),
        }

        window._populate_scheduled_fields()

        mock_widget.set_active.assert_called_with(True)

    def test_populate_scheduled_fields_sets_frequency(self, preferences_window_class, mock_settings_manager, mock_gi_modules):
        """Test that frequency dropdown is populated."""
        window = object.__new__(preferences_window_class)
        window._settings_manager = mock_settings_manager

        def mock_get(key, default=None):
            if key == "schedule_frequency":
                return "weekly"
            return default

        mock_settings_manager.get.side_effect = mock_get

        mock_frequency_widget = mock.MagicMock()
        window._scheduled_widgets = {
            'enabled': mock.MagicMock(),
            'frequency': mock_frequency_widget,
            'time': mock.MagicMock(),
            'targets': mock.MagicMock(),
            'day_of_week': mock.MagicMock(),
            'day_of_month': mock.MagicMock(),
            'skip_on_battery': mock.MagicMock(),
            'auto_quarantine': mock.MagicMock(),
        }

        window._populate_scheduled_fields()

        mock_frequency_widget.set_selected.assert_called_with(2)  # weekly = 2

    def test_populate_scheduled_fields_sets_targets_from_list(self, preferences_window_class, mock_settings_manager, mock_gi_modules):
        """Test that targets are populated from list."""
        window = object.__new__(preferences_window_class)
        window._settings_manager = mock_settings_manager

        def mock_get(key, default=None):
            if key == "schedule_targets":
                return ["/home", "/var"]
            return default

        mock_settings_manager.get.side_effect = mock_get

        mock_targets_widget = mock.MagicMock()
        window._scheduled_widgets = {
            'enabled': mock.MagicMock(),
            'frequency': mock.MagicMock(),
            'time': mock.MagicMock(),
            'targets': mock_targets_widget,
            'day_of_week': mock.MagicMock(),
            'day_of_month': mock.MagicMock(),
            'skip_on_battery': mock.MagicMock(),
            'auto_quarantine': mock.MagicMock(),
        }

        window._populate_scheduled_fields()

        mock_targets_widget.set_text.assert_called_with("/home, /var")


class TestPreferencesWindowSaveClicked:
    """Tests for save button click handling."""

    def test_on_save_clicked_returns_when_already_saving(self, preferences_window_class, mock_gi_modules):
        """Test that save returns early when already saving."""
        window = object.__new__(preferences_window_class)
        window._is_saving = True
        window._collect_freshclam_data = mock.MagicMock()

        mock_button = mock.MagicMock()
        window._on_save_clicked(mock_button)

        window._collect_freshclam_data.assert_not_called()

    def test_on_save_clicked_sets_saving_state(self, preferences_window_class, mock_gi_modules):
        """Test that save sets saving state."""
        with mock.patch('threading.Thread'):
            window = object.__new__(preferences_window_class)
            window._is_saving = False
            window._freshclam_config = None
            window._clamd_config = None
            window._clamd_available = False
            window._collect_freshclam_data = mock.MagicMock(return_value={})
            window._collect_clamd_data = mock.MagicMock(return_value={})
            window._collect_scheduled_data = mock.MagicMock(return_value={})

            mock_button = mock.MagicMock()
            window._on_save_clicked(mock_button)

            assert window._is_saving is True
            mock_button.set_sensitive.assert_called_with(False)

    def test_on_save_clicked_validates_freshclam_config(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that save validates freshclam config."""
        with mock.patch('src.ui.preferences_window.validate_config', return_value=(False, "Validation error")):
            window = object.__new__(preferences_window_class)
            window._is_saving = False
            window._freshclam_config = mock_clamav_config
            window._clamd_config = None
            window._clamd_available = False
            window._collect_freshclam_data = mock.MagicMock(return_value={'key': 'value'})
            window._collect_clamd_data = mock.MagicMock(return_value={})
            window._collect_scheduled_data = mock.MagicMock(return_value={})
            window._show_error_dialog = mock.MagicMock()

            mock_button = mock.MagicMock()
            window._on_save_clicked(mock_button)

            window._show_error_dialog.assert_called_once_with("Validation Error", "Validation error")
            assert window._is_saving is False
            mock_button.set_sensitive.assert_called_with(True)


class TestPreferencesWindowShowDialogs:
    """Tests for dialog display."""

    def test_show_error_dialog_creates_dialog(self, preferences_window_class, mock_gi_modules):
        """Test that error dialog is created correctly."""
        adw = mock_gi_modules['adw']
        mock_dialog = mock.MagicMock()
        adw.AlertDialog.return_value = mock_dialog

        window = object.__new__(preferences_window_class)

        window._show_error_dialog("Error Title", "Error message")

        mock_dialog.set_heading.assert_called_with("Error Title")
        mock_dialog.set_body.assert_called_with("Error message")
        mock_dialog.add_response.assert_called_with("ok", "OK")
        mock_dialog.set_default_response.assert_called_with("ok")
        mock_dialog.present.assert_called_once()

    def test_show_success_dialog_creates_dialog(self, preferences_window_class, mock_gi_modules):
        """Test that success dialog is created correctly."""
        adw = mock_gi_modules['adw']
        mock_dialog = mock.MagicMock()
        adw.AlertDialog.return_value = mock_dialog

        window = object.__new__(preferences_window_class)

        window._show_success_dialog("Success Title", "Success message")

        mock_dialog.set_heading.assert_called_with("Success Title")
        mock_dialog.set_body.assert_called_with("Success message")
        mock_dialog.add_response.assert_called_with("ok", "OK")
        mock_dialog.present.assert_called_once()


class TestPreferencesWindowUISetup:
    """Tests for UI setup methods."""

    def test_setup_ui_creates_all_pages(self, preferences_window_class, mock_gi_modules):
        """Test that _setup_ui creates all required pages."""
        window = object.__new__(preferences_window_class)
        window._create_database_page = mock.MagicMock()
        window._create_scanner_page = mock.MagicMock()
        window._create_scheduled_scans_page = mock.MagicMock()
        window._create_onaccess_page = mock.MagicMock()
        window._create_exclusions_page = mock.MagicMock()
        window._create_save_page = mock.MagicMock()

        window._setup_ui()

        window._create_database_page.assert_called_once()
        window._create_scanner_page.assert_called_once()
        window._create_scheduled_scans_page.assert_called_once()
        window._create_onaccess_page.assert_called_once()
        window._create_exclusions_page.assert_called_once()
        window._create_save_page.assert_called_once()


class TestPreferencesWindowOnAccessPage:
    """Tests for On-Access page creation."""

    def test_create_onaccess_page_sets_title_and_icon(self, preferences_window_class, mock_gi_modules):
        """Test that _create_onaccess_page creates page with correct title and icon."""
        adw = mock_gi_modules['adw']
        mock_page = mock.MagicMock()
        adw.PreferencesPage.return_value = mock_page

        window = object.__new__(preferences_window_class)
        window._clamd_available = False
        window._onaccess_widgets = {}
        window.add = mock.MagicMock()
        window._create_permission_indicator = mock.MagicMock()

        window._create_onaccess_page()

        mock_page.set_title.assert_called_with("On Access")
        mock_page.set_icon_name.assert_called_with("security-high-symbolic")

    def test_create_onaccess_page_adds_page_to_window(self, preferences_window_class, mock_gi_modules):
        """Test that _create_onaccess_page adds the page to the window."""
        adw = mock_gi_modules['adw']
        mock_page = mock.MagicMock()
        adw.PreferencesPage.return_value = mock_page

        window = object.__new__(preferences_window_class)
        window._clamd_available = False
        window._onaccess_widgets = {}
        window.add = mock.MagicMock()
        window._create_permission_indicator = mock.MagicMock()

        window._create_onaccess_page()

        window.add.assert_called_once_with(mock_page)

    def test_create_onaccess_page_creates_groups_when_clamd_available(self, preferences_window_class, mock_gi_modules):
        """Test that _create_onaccess_page creates all groups when clamd is available."""
        adw = mock_gi_modules['adw']
        mock_page = mock.MagicMock()
        adw.PreferencesPage.return_value = mock_page

        window = object.__new__(preferences_window_class)
        window._clamd_available = True
        window._onaccess_widgets = {}
        window.add = mock.MagicMock()
        window._create_permission_indicator = mock.MagicMock()
        window._create_onaccess_paths_group = mock.MagicMock()
        window._create_onaccess_behavior_group = mock.MagicMock()
        window._create_onaccess_performance_group = mock.MagicMock()
        window._create_onaccess_exclusions_group = mock.MagicMock()

        window._create_onaccess_page()

        window._create_onaccess_paths_group.assert_called_once_with(mock_page)
        window._create_onaccess_behavior_group.assert_called_once_with(mock_page)
        window._create_onaccess_performance_group.assert_called_once_with(mock_page)
        window._create_onaccess_exclusions_group.assert_called_once_with(mock_page)

    def test_create_onaccess_page_shows_unavailable_when_clamd_missing(self, preferences_window_class, mock_gi_modules):
        """Test that _create_onaccess_page shows status message when clamd unavailable."""
        adw = mock_gi_modules['adw']
        mock_page = mock.MagicMock()
        mock_group = mock.MagicMock()
        mock_row = mock.MagicMock()
        adw.PreferencesPage.return_value = mock_page
        adw.PreferencesGroup.return_value = mock_group
        adw.ActionRow.return_value = mock_row

        window = object.__new__(preferences_window_class)
        window._clamd_available = False
        window._onaccess_widgets = {}
        window.add = mock.MagicMock()
        window._create_permission_indicator = mock.MagicMock()

        window._create_onaccess_page()

        # Should create a status group
        mock_group.set_title.assert_called_with("Configuration Status")
        mock_row.set_title.assert_called_with("On Access Configuration")
        mock_row.set_subtitle.assert_called_with("clamd.conf not found - On Access settings unavailable")

    def test_create_onaccess_page_does_not_create_groups_when_clamd_missing(self, preferences_window_class, mock_gi_modules):
        """Test that _create_onaccess_page doesn't create groups when clamd unavailable."""
        adw = mock_gi_modules['adw']
        mock_page = mock.MagicMock()
        adw.PreferencesPage.return_value = mock_page

        window = object.__new__(preferences_window_class)
        window._clamd_available = False
        window._onaccess_widgets = {}
        window.add = mock.MagicMock()
        window._create_permission_indicator = mock.MagicMock()
        window._create_onaccess_paths_group = mock.MagicMock()
        window._create_onaccess_behavior_group = mock.MagicMock()
        window._create_onaccess_performance_group = mock.MagicMock()
        window._create_onaccess_exclusions_group = mock.MagicMock()

        window._create_onaccess_page()

        window._create_onaccess_paths_group.assert_not_called()
        window._create_onaccess_behavior_group.assert_not_called()
        window._create_onaccess_performance_group.assert_not_called()
        window._create_onaccess_exclusions_group.assert_not_called()

    def test_create_onaccess_paths_group_creates_widgets(self, preferences_window_class, mock_gi_modules):
        """Test that _create_onaccess_paths_group creates path entry widgets."""
        adw = mock_gi_modules['adw']
        gtk = mock_gi_modules['gtk']
        mock_page = mock.MagicMock()
        mock_group = mock.MagicMock()
        mock_entry_row = mock.MagicMock()
        mock_image = mock.MagicMock()

        adw.PreferencesGroup.return_value = mock_group
        adw.EntryRow.return_value = mock_entry_row
        gtk.Image.new_from_icon_name.return_value = mock_image

        window = object.__new__(preferences_window_class)
        window._onaccess_widgets = {}
        window._create_permission_indicator = mock.MagicMock(return_value=mock.MagicMock())

        window._create_onaccess_paths_group(mock_page)

        # Should create include and exclude path widgets
        assert 'OnAccessIncludePath' in window._onaccess_widgets
        assert 'OnAccessExcludePath' in window._onaccess_widgets
        mock_page.add.assert_called_once_with(mock_group)

    def test_create_onaccess_behavior_group_creates_switches(self, preferences_window_class, mock_gi_modules):
        """Test that _create_onaccess_behavior_group creates behavior switch widgets."""
        adw = mock_gi_modules['adw']
        mock_page = mock.MagicMock()
        mock_group = mock.MagicMock()
        mock_switch_row = mock.MagicMock()

        adw.PreferencesGroup.return_value = mock_group
        adw.SwitchRow.return_value = mock_switch_row

        window = object.__new__(preferences_window_class)
        window._onaccess_widgets = {}
        window._create_permission_indicator = mock.MagicMock(return_value=mock.MagicMock())

        window._create_onaccess_behavior_group(mock_page)

        # Should create behavior switch widgets
        assert 'OnAccessPrevention' in window._onaccess_widgets
        assert 'OnAccessExtraScanning' in window._onaccess_widgets
        assert 'OnAccessDenyOnError' in window._onaccess_widgets
        assert 'OnAccessDisableDDD' in window._onaccess_widgets
        mock_page.add.assert_called_once_with(mock_group)

    def test_create_onaccess_performance_group_creates_spin_rows(self, preferences_window_class, mock_gi_modules):
        """Test that _create_onaccess_performance_group creates spin row widgets."""
        adw = mock_gi_modules['adw']
        mock_page = mock.MagicMock()
        mock_group = mock.MagicMock()
        mock_spin_row = mock.MagicMock()

        adw.PreferencesGroup.return_value = mock_group
        adw.SpinRow.new_with_range.return_value = mock_spin_row

        window = object.__new__(preferences_window_class)
        window._onaccess_widgets = {}
        window._create_permission_indicator = mock.MagicMock(return_value=mock.MagicMock())

        window._create_onaccess_performance_group(mock_page)

        # Should create performance spin widgets
        assert 'OnAccessMaxThreads' in window._onaccess_widgets
        assert 'OnAccessMaxFileSize' in window._onaccess_widgets
        assert 'OnAccessCurlTimeout' in window._onaccess_widgets
        assert 'OnAccessRetryAttempts' in window._onaccess_widgets
        mock_page.add.assert_called_once_with(mock_group)

    def test_create_onaccess_exclusions_group_creates_widgets(self, preferences_window_class, mock_gi_modules):
        """Test that _create_onaccess_exclusions_group creates exclusion widgets."""
        adw = mock_gi_modules['adw']
        gtk = mock_gi_modules['gtk']
        mock_page = mock.MagicMock()
        mock_group = mock.MagicMock()
        mock_entry_row = mock.MagicMock()
        mock_switch_row = mock.MagicMock()
        mock_spin_row = mock.MagicMock()
        mock_action_row = mock.MagicMock()
        mock_image = mock.MagicMock()

        adw.PreferencesGroup.return_value = mock_group
        adw.EntryRow.return_value = mock_entry_row
        adw.SwitchRow.return_value = mock_switch_row
        adw.SpinRow.new_with_range.return_value = mock_spin_row
        adw.ActionRow.return_value = mock_action_row
        gtk.Image.new_from_icon_name.return_value = mock_image

        window = object.__new__(preferences_window_class)
        window._onaccess_widgets = {}
        window._create_permission_indicator = mock.MagicMock(return_value=mock.MagicMock())

        window._create_onaccess_exclusions_group(mock_page)

        # Should create exclusion widgets
        assert 'OnAccessExcludeUname' in window._onaccess_widgets
        assert 'OnAccessExcludeUID' in window._onaccess_widgets
        assert 'OnAccessExcludeRootUID' in window._onaccess_widgets
        mock_page.add.assert_called_once_with(mock_group)


class TestPreferencesWindowLoadConfigs:
    """Tests for configuration loading."""

    def test_load_configs_handles_parse_error(self, preferences_window_class, mock_gi_modules):
        """Test that load_configs handles parse errors gracefully."""
        with mock.patch.dict(sys.modules, {
            'src.core.clamav_config': mock.MagicMock(),
        }):
            from src.core import clamav_config
            clamav_config.parse_config = mock.MagicMock(side_effect=Exception("Parse error"))

            window = object.__new__(preferences_window_class)
            window._freshclam_conf_path = "/etc/clamav/freshclam.conf"
            window._clamd_conf_path = "/etc/clamav/clamd.conf"
            window._clamd_available = False
            window._populate_freshclam_fields = mock.MagicMock()
            window._populate_clamd_fields = mock.MagicMock()

            # Should not raise
            window._load_configs()

    def test_load_configs_loads_clamd_when_available(self, preferences_window_class, mock_clamav_config, mock_gi_modules):
        """Test that clamd config is loaded when available."""
        mock_parse = mock.MagicMock(return_value=(mock_clamav_config, None))

        with mock.patch('src.ui.preferences_window.parse_config', mock_parse):
            window = object.__new__(preferences_window_class)
            window._freshclam_conf_path = "/etc/clamav/freshclam.conf"
            window._clamd_conf_path = "/etc/clamav/clamd.conf"
            window._clamd_available = True
            window._freshclam_config = None
            window._clamd_config = None
            window._populate_freshclam_fields = mock.MagicMock()
            window._populate_clamd_fields = mock.MagicMock()

            window._load_configs()

            # Should be called twice (freshclam and clamd)
            assert mock_parse.call_count == 2
            window._populate_freshclam_fields.assert_called_once()
            window._populate_clamd_fields.assert_called_once()


class TestPreferencesWindowSaveConfigsThread:
    """Tests for save configs thread functionality."""

    def test_save_configs_thread_backs_up_configs(self, preferences_window_class, mock_clamav_config, mock_settings_manager, mock_gi_modules):
        """Test that configs are backed up before saving."""
        mock_backup = mock.MagicMock()
        mock_write = mock.MagicMock(return_value=(True, None))

        with mock.patch('src.ui.preferences_window.backup_config', mock_backup), \
             mock.patch('src.ui.preferences_window.write_config_with_elevation', mock_write):
            glib = mock_gi_modules['glib']
            glib.idle_add = mock.MagicMock(side_effect=lambda f, *args: f(*args) if args else f())

            window = object.__new__(preferences_window_class)
            window._freshclam_conf_path = "/etc/clamav/freshclam.conf"
            window._clamd_conf_path = "/etc/clamav/clamd.conf"
            window._clamd_available = False
            window._freshclam_config = mock_clamav_config
            window._clamd_config = None
            window._settings_manager = mock_settings_manager
            window._scheduler = mock.MagicMock()
            window._is_saving = True
            window._show_success_dialog = mock.MagicMock()

            mock_button = mock.MagicMock()
            window._save_configs_thread({}, {}, {}, {}, mock_button)

            mock_backup.assert_called_with("/etc/clamav/freshclam.conf")

    def test_save_configs_thread_handles_save_error(self, preferences_window_class, mock_clamav_config, mock_settings_manager, mock_gi_modules):
        """Test that save errors are handled."""
        mock_backup = mock.MagicMock()
        mock_write = mock.MagicMock(return_value=(False, "Permission denied"))

        with mock.patch('src.ui.preferences_window.backup_config', mock_backup), \
             mock.patch('src.ui.preferences_window.write_config_with_elevation', mock_write):
            glib = mock_gi_modules['glib']
            glib.idle_add = mock.MagicMock(side_effect=lambda f, *args: f(*args) if args else f())

            window = object.__new__(preferences_window_class)
            window._freshclam_conf_path = "/etc/clamav/freshclam.conf"
            window._clamd_conf_path = "/etc/clamav/clamd.conf"
            window._clamd_available = False
            window._freshclam_config = mock_clamav_config
            window._clamd_config = None
            window._settings_manager = mock_settings_manager
            window._scheduler = mock.MagicMock()
            window._is_saving = True
            window._scheduler_error = None
            window._show_error_dialog = mock.MagicMock()

            mock_button = mock.MagicMock()
            window._save_configs_thread({'key': 'value'}, {}, {}, {}, mock_button)

            window._show_error_dialog.assert_called_once()
            assert "Permission denied" in str(window._show_error_dialog.call_args)


# Module-level test function for verification
def test_preferences_window_basic(mock_gi_modules):
    """
    Basic test function for pytest verification command.

    This test verifies the core PreferencesWindow functionality
    using a minimal mock setup.
    """
    with mock.patch.dict(sys.modules, {
        'src.core.clamav_config': mock.MagicMock(),
        'src.core.scheduler': mock.MagicMock(),
        'src.core.scanner': mock.MagicMock(),
    }):
        from src.ui.preferences_window import PreferencesWindow, PRESET_EXCLUSIONS

        # Test 1: Class can be imported
        assert PreferencesWindow is not None

        # Test 2: PRESET_EXCLUSIONS is a non-empty list
        assert isinstance(PRESET_EXCLUSIONS, list)
        assert len(PRESET_EXCLUSIONS) > 0

        # Test 3: PRESET_EXCLUSIONS contains expected patterns
        patterns = [e["pattern"] for e in PRESET_EXCLUSIONS]
        assert "node_modules" in patterns
        assert ".git" in patterns

        # Test 4: Each preset has required fields
        for preset in PRESET_EXCLUSIONS:
            assert "pattern" in preset
            assert "type" in preset
            assert "enabled" in preset
            assert "description" in preset

        # Test 5: Create mock instance and test data collection
        window = object.__new__(PreferencesWindow)

        # Test _collect_freshclam_data
        window._freshclam_widgets = {
            'DatabaseDirectory': mock.MagicMock(get_text=mock.MagicMock(return_value="/var/lib/clamav")),
            'UpdateLogFile': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'NotifyClamd': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'LogVerbose': mock.MagicMock(get_active=mock.MagicMock(return_value=True)),
            'LogSyslog': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
            'Checks': mock.MagicMock(get_value=mock.MagicMock(return_value=12)),
            'DatabaseMirror': mock.MagicMock(get_text=mock.MagicMock(return_value="db.clamav.net")),
            'HTTPProxyServer': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'HTTPProxyPort': mock.MagicMock(get_value=mock.MagicMock(return_value=0)),
            'HTTPProxyUsername': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
            'HTTPProxyPassword': mock.MagicMock(get_text=mock.MagicMock(return_value="")),
        }

        result = window._collect_freshclam_data()
        assert result['DatabaseDirectory'] == "/var/lib/clamav"
        assert result['LogVerbose'] == 'yes'
        assert result['Checks'] == '12'

        # Test _collect_scheduled_data
        window._scheduled_widgets = {
            'enabled': mock.MagicMock(get_active=mock.MagicMock(return_value=True)),
            'frequency': mock.MagicMock(get_selected=mock.MagicMock(return_value=1)),
            'time': mock.MagicMock(get_text=mock.MagicMock(return_value="02:00")),
            'targets': mock.MagicMock(get_text=mock.MagicMock(return_value="/home, /var")),
            'day_of_week': mock.MagicMock(get_selected=mock.MagicMock(return_value=0)),
            'day_of_month': mock.MagicMock(get_value=mock.MagicMock(return_value=1)),
            'skip_on_battery': mock.MagicMock(get_active=mock.MagicMock(return_value=True)),
            'auto_quarantine': mock.MagicMock(get_active=mock.MagicMock(return_value=False)),
        }

        scheduled_result = window._collect_scheduled_data()
        assert scheduled_result['scheduled_scans_enabled'] is True
        assert scheduled_result['schedule_frequency'] == 'daily'
        assert scheduled_result['schedule_targets'] == ['/home', '/var']

        # All tests passed
