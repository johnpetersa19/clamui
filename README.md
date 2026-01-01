# ClamUI

A modern Linux desktop application that provides a graphical user interface for the ClamAV antivirus command-line tool. Built with PyGObject, GTK4, and Adwaita for a native GNOME appearance.

## Features

- **Folder/File Selection**: Select files or directories to scan using the native GTK4 file dialog
- **Async Scanning**: Scans run in the background, keeping the UI responsive
- **Results Display**: Clear, readable display of scan results
- **ClamAV Detection**: Graceful handling when ClamAV is not installed
- **Modern UI**: Native Adwaita styling with proper GNOME integration
- **File Manager Integration**: Right-click "Scan with ClamUI" option in Nautilus, Dolphin, and Nemo
- **System Tray Integration**: Optional tray icon with quick actions and scan progress (requires AppIndicator)

## File Manager Context Menu Integration

ClamUI provides a right-click context menu option in file managers (Nautilus, Dolphin, Nemo) for quick scanning.

### Installing the Context Menu

#### GNOME (Nautilus) and KDE (Dolphin)

1. **Copy the desktop file to your applications directory**:
   ```bash
   cp com.github.clamui.desktop ~/.local/share/applications/
   ```

2. **Update the desktop database**:
   ```bash
   update-desktop-database ~/.local/share/applications
   ```

3. **Restart your file manager** (to reload the desktop file):
   ```bash
   # For GNOME (Nautilus):
   nautilus -q

   # For KDE (Dolphin):
   killall dolphin
   ```

4. **Verify**: Right-click any file or folder in your file manager. You should see "Scan with ClamUI" in the context menu.

#### Cinnamon (Nemo)

Nemo uses its own action format for context menu extensions.

1. **Create the Nemo actions directory** (if it doesn't exist):
   ```bash
   mkdir -p ~/.local/share/nemo/actions
   ```

2. **Copy the Nemo action file**:
   ```bash
   cp com.github.clamui.nemo_action ~/.local/share/nemo/actions/
   ```

3. **Restart Nemo** (to reload actions):
   ```bash
   nemo -q
   ```

4. **Verify**: Right-click any file or folder in Nemo. You should see "Scan with ClamUI" in the context menu.

### Using the Context Menu

- **Single file**: Right-click a file and select "Scan with ClamUI" to scan it
- **Folder**: Right-click a folder to recursively scan all its contents
- **Multiple selection**: Select multiple files/folders, right-click, and scan all at once

### Flatpak Users

If you installed ClamUI via Flatpak, the context menu integration is included automatically. The Flatpak manifest includes the necessary filesystem permissions (`--filesystem=host:ro`) to access files for scanning.

## System Tray Integration

ClamUI provides an optional system tray icon for quick access to scanning functions without opening the main window.

### Features

- **Status Indicator**: Tray icon shows current protection status (protected, warning, scanning, threat)
- **Quick Actions**: Right-click menu for Quick Scan, Full Scan, and Update Definitions
- **Scan Progress**: Shows scan progress percentage in the tray during active scans
- **Window Toggle**: Click the tray icon to show/hide the main window
- **Minimize to Tray**: Option to hide to tray instead of taskbar when minimizing

### Requirements

The system tray feature requires the AyatanaAppIndicator3 library:

```bash
# Ubuntu/Debian
sudo apt install gir1.2-ayatanaappindicator3-0.1

# Fedora
sudo dnf install libayatana-appindicator-gtk3

# Arch Linux
sudo pacman -S libayatana-appindicator
```

**GNOME Shell Users**: You also need the [AppIndicator Support](https://extensions.gnome.org/extension/615/appindicator-support/) extension installed and enabled for tray icons to appear.

### Graceful Degradation

If the AppIndicator library is not installed, ClamUI will run normally without the tray icon feature. The application logs a warning message but continues to function with all other features.

## Requirements

### System Dependencies

ClamUI requires the following system packages (Ubuntu/Debian):

```bash
# GTK4 and Adwaita runtime libraries
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 libadwaita-1-dev

# Build dependencies (required for pip install)
sudo apt install libgirepository-2.0-dev libcairo2-dev pkg-config python3-dev
# On Ubuntu < 24.04, use: libgirepository1.0-dev instead of libgirepository-2.0-dev

# ClamAV antivirus
sudo apt install clamav

# System tray support (optional)
sudo apt install gir1.2-ayatanaappindicator3-0.1
```

For other distributions:
- **Fedora**: `sudo dnf install python3-gobject python3-gobject-devel gtk4 libadwaita gobject-introspection-devel cairo-gobject-devel clamav libayatana-appindicator-gtk3`
- **Arch**: `sudo pacman -S python-gobject gtk4 libadwaita clamav libayatana-appindicator`

### Python Dependencies

- Python 3.x
- PyGObject >= 3.48.0
- pycairo >= 1.25.0

## Installation

### Option 1: System Installation (Recommended)

The install script registers ClamUI with your system, including application menu entry and file manager context menu integration.

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/clamui.git
   cd clamui
   ```

2. **Install system dependencies** (see Requirements above)

3. **Run the installer**:
   ```bash
   ./install.sh
   ```

   For system-wide installation (requires root):
   ```bash
   sudo ./install.sh --system
   ```

4. **Verify the installation**:
   ```bash
   # Check if ClamUI is accessible
   which clamui

   # Verify ClamAV is installed
   clamscan --version
   ```

After installation, ClamUI will appear in your application menu and the context menu in supported file managers.

### Option 2: Development Setup

For running from source without system installation:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/clamui.git
   cd clamui
   ```

2. **Install system dependencies** (see Requirements above)

3. **Install Python dependencies with uv**:
   ```bash
   uv sync
   ```

4. **Run from source**:
   ```bash
   uv run clamui
   ```

### Uninstallation

To remove ClamUI from your system:

```bash
# User-local uninstall
./uninstall.sh

# System-wide uninstall (if installed with --system)
sudo ./uninstall.sh --system
```

## Context Menu Integration

ClamUI integrates with file managers to provide a "Scan with ClamUI" option in the right-click context menu.

### Supported File Managers

- **Nemo** (Linux Mint, Cinnamon): Full support via `.nemo_action` file
- **Other file managers**: Desktop entry action provides basic integration

### Using the Context Menu

1. Right-click on any file or folder in your file manager
2. Select **"Scan with ClamUI"** from the context menu
3. ClamUI opens with the selected files queued for scanning
4. Click "Scan" to start the antivirus scan

You can select multiple files or folders before right-clicking to scan them all at once.

### Verifying Context Menu Installation

After running `install.sh`, verify the context menu files are installed:

```bash
# Check desktop entry (application menu)
ls ~/.local/share/applications/com.github.clamui.desktop

# Check icon
ls ~/.local/share/icons/hicolor/scalable/apps/com.github.clamui.svg

# Check Nemo action (context menu)
ls ~/.local/share/nemo/actions/com.github.clamui.nemo_action
```

If files are missing, you may need to:
1. Log out and back in
2. Manually refresh the desktop database:
   ```bash
   update-desktop-database ~/.local/share/applications
   gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor
   ```

### Flatpak vs Native Installation

ClamUI can be installed either as a native application or via Flatpak. Both methods support context menu integration.

| Feature | Native Install | Flatpak |
|---------|---------------|---------|
| Installation | `./install.sh` | `flatpak install` |
| Context Menu Location | `~/.local/share/nemo/actions/` | Sandbox-managed |
| ClamAV Access | Direct system access | Requires permissions |
| Updates | Manual | Via Flatpak |

**Note**: Native and Flatpak installations can coexist. The file manager will show both options if both are installed.

## Running the Application

```bash
# After system installation
clamui

# From source (development)
uv run clamui

# With file arguments (from context menu or command line)
clamui /path/to/file1 /path/to/folder
```

## Project Structure

```
clamui/
├── src/
│   ├── __init__.py           # Package initialization with version
│   ├── main.py               # Application entry point
│   ├── app.py                # Adw.Application class (lifecycle, views, tray)
│   ├── cli/
│   │   ├── __init__.py
│   │   └── scheduled_scan.py # CLI for scheduled scans (systemd/cron)
│   ├── core/                  # Business logic modules
│   │   ├── __init__.py
│   │   ├── scanner.py         # ClamAV scanning (sync/async)
│   │   ├── daemon_scanner.py  # clamd daemon integration
│   │   ├── scheduler.py       # systemd/cron scheduled scans
│   │   ├── quarantine/        # Threat quarantine system
│   │   │   ├── __init__.py
│   │   │   ├── manager.py     # High-level quarantine operations
│   │   │   ├── database.py    # SQLite metadata storage
│   │   │   └── file_handler.py # Secure file operations
│   │   ├── settings_manager.py    # JSON settings persistence
│   │   ├── log_manager.py         # Scan history logging
│   │   ├── notification_manager.py # Desktop notifications
│   │   ├── battery_manager.py     # Battery status for scheduled scans
│   │   ├── updater.py             # freshclam database updates
│   │   ├── clamav_config.py       # ClamAV configuration parsing
│   │   ├── statistics_calculator.py # Scan statistics
│   │   └── utils.py               # Utility functions (Flatpak detection, path validation)
│   ├── profiles/              # Scan profile management
│   │   ├── __init__.py
│   │   ├── profile_manager.py # CRUD operations, validation, import/export
│   │   ├── profile_storage.py # JSON persistence
│   │   └── models.py          # ScanProfile dataclass
│   └── ui/                    # GTK4/Adwaita UI components
│       ├── __init__.py
│       ├── window.py          # Main application window
│       ├── scan_view.py       # Scanning interface
│       ├── update_view.py     # Database update view
│       ├── logs_view.py       # Scan history
│       ├── quarantine_view.py # Quarantine management
│       ├── statistics_view.py # Statistics dashboard
│       ├── components_view.py # ClamAV components status
│       ├── preferences_window.py / preferences_dialog.py
│       ├── profile_dialogs.py # Profile create/edit dialogs
│       ├── tray_manager.py    # System tray subprocess manager
│       ├── tray_indicator.py  # GTK3 tray subprocess
│       └── fullscreen_dialog.py
├── tests/                     # Test suite (mirrors src structure)
│   ├── conftest.py            # Shared fixtures, GTK mocking
│   ├── core/                  # Core module tests
│   ├── ui/                    # UI component tests
│   ├── profiles/              # Profile tests
│   ├── integration/           # Integration tests
│   └── e2e/                   # End-to-end tests
├── scripts/
│   └── clamui-scheduled-scan  # Scheduled scan CLI wrapper
├── debian/                    # Debian packaging
├── icons/                     # Application icons
├── .github/workflows/         # CI: test.yml, lint.yml, build-*.yml
├── pyproject.toml             # Project config, dependencies, tool settings
└── install.sh                 # Installation script
```

## Usage

1. Launch the application with `uv run clamui`
2. Click the folder selection button to choose a file or directory to scan
3. Click the "Scan" button to start the antivirus scan
4. View the results in the results display area

## ClamAV Exit Codes

The application interprets ClamAV exit codes as follows:
- **0**: No viruses found (clean)
- **1**: Virus(es) found
- **2**: Error occurred during scan

## Development

### Tech Stack

- **Language**: Python 3.x
- **Framework**: PyGObject (GTK4 bindings)
- **UI Toolkit**: GTK4 with libadwaita

### Key Patterns

- Uses `Adw.Application` for modern GNOME application structure
- Background scanning with `threading.Thread` and `GLib.idle_add()` for thread-safe UI updates
- Subprocess integration with `clamscan` for antivirus scanning

### Running Tests

ClamUI includes a comprehensive test suite with 80%+ code coverage for core modules.

#### Installing Test Dependencies

```bash
# Install dev dependencies (includes pytest and pytest-cov)
pip install -e ".[dev]"

# Or with uv
uv sync --dev
```

#### Running the Full Test Suite

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_scanner.py -v

# Run tests matching a pattern
pytest -k "test_scanner" -v
```

#### Running Tests with Coverage

```bash
# Run with coverage report in terminal
pytest --cov=src --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in your browser to view

# Run with both terminal and HTML reports
pytest --cov=src --cov-report=term-missing --cov-report=html
```

#### Coverage Requirements

The project enforces a minimum of **50% code coverage** for the `src/` directory, with a target of **80%+** for comprehensive coverage. Coverage is measured with branch coverage enabled. The coverage configuration is defined in `pyproject.toml` and will fail the test run if coverage drops below the threshold.

| Module | Coverage Target |
|--------|----------------|
| `src/core/` | 80%+ (critical business logic) |
| `src/profiles/` | 80%+ (profile management) |
| `src/ui/` | 70%+ (GTK components, some lines untestable) |
| Overall `src/` | 50% minimum, 80% target |

#### Performance Verification

```bash
# Show test execution times (slowest tests first)
pytest --durations=10

# Full suite should complete in under 30 seconds
pytest --durations=0
```

#### Headless/CI Environment Testing

All tests are designed to run in headless CI environments without requiring a display server (X11/Wayland). GTK-dependent tests will skip gracefully when no display is available:

```bash
# Run in headless mode (no DISPLAY set)
unset DISPLAY
pytest

# GTK tests will show as skipped with a clear message
# All other tests will run normally
```

#### Test Organization

Tests are organized to mirror the source code structure:

```
tests/
├── conftest.py                 # Shared fixtures, GTK mocking
├── core/                       # Tests for src/core/ modules
│   ├── test_battery_manager.py
│   ├── test_clamav_config.py
│   ├── test_daemon_scanner.py
│   ├── test_log_manager.py
│   ├── test_notification_manager.py
│   ├── test_quarantine_database.py
│   ├── test_quarantine_manager.py
│   ├── test_scheduler.py
│   ├── test_settings_manager.py
│   └── test_utils.py
├── profiles/                   # Tests for src/profiles/ modules
│   ├── test_models.py
│   ├── test_profile_manager.py
│   └── test_profile_storage.py
├── ui/                         # Tests for src/ui/ components
│   ├── test_fullscreen_dialog.py
│   ├── test_logs_view.py
│   ├── test_preferences_window.py
│   ├── test_profile_dialogs.py
│   ├── test_quarantine_view.py
│   ├── test_scanner_ui.py
│   ├── test_statistics_view.py
│   ├── test_tray_indicator.py
│   └── test_tray_manager.py
├── integration/                # Integration tests
│   ├── test_scanner_integration.py
│   ├── test_scheduled_scan.py
│   └── test_tray_integration.py
├── e2e/                        # End-to-end tests
│   ├── test_profile_lifecycle.py
│   └── test_scheduled_scan_flow.py
├── test_app.py                 # Application tests
├── test_cli.py                 # CLI tests
├── test_scanner.py             # Scanner tests
├── test_scan_view.py           # Scan view tests
├── test_statistics_calculator.py
├── test_updater.py
└── test_quarantine_integration.py
```

#### Writing New Tests

Follow the existing patterns when adding tests:

1. **Use fixtures** for common setup (see `pytest.fixture`)
2. **Mock external dependencies** (ClamAV, system paths, GTK)
3. **Use `tmp_path`** for file I/O tests
4. **Add docstrings** to all test methods
5. **Test error paths** explicitly

Example test structure:

```python
import pytest
from unittest import mock

class TestMyFeature:
    """Tests for MyFeature class."""

    @pytest.fixture
    def my_instance(self, tmp_path):
        """Create instance for testing."""
        return MyFeature(data_dir=str(tmp_path))

    def test_basic_operation(self, my_instance):
        """Test basic operation succeeds."""
        result = my_instance.do_something()
        assert result is not None
```

## License

This project is open source. See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.