# ClamUI

A modern Linux desktop application that provides a graphical user interface for the ClamAV antivirus command-line tool. Built with PyGObject, GTK4, and Adwaita for a native GNOME appearance.

## Features

- **Folder/File Selection**: Select files or directories to scan using the native GTK4 file dialog
- **Async Scanning**: Scans run in the background, keeping the UI responsive
- **Results Display**: Clear, readable display of scan results
- **ClamAV Detection**: Graceful handling when ClamAV is not installed
- **Modern UI**: Native Adwaita styling with proper GNOME integration

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
```

For other distributions:
- **Fedora**: `sudo dnf install python3-gobject python3-gobject-devel gtk4 libadwaita gobject-introspection-devel cairo-gobject-devel clamav`
- **Arch**: `sudo pacman -S python-gobject gtk4 libadwaita clamav`

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
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── app.py               # Adw.Application class
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── window.py        # Main application window
│   │   └── scan_view.py     # Scan interface component
│   └── core/
│       ├── __init__.py
│       ├── scanner.py       # ClamAV subprocess integration
│       └── utils.py         # Utility functions
├── pyproject.toml
├── uv.lock
├── README.md
└── .gitignore
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

```bash
python -m pytest tests/
```

## License

This project is open source. See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
