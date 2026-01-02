# ClamUI

A modern Linux desktop application that provides a graphical user interface for the ClamAV antivirus command-line tool. Built with PyGObject, GTK4, and Adwaita for a native GNOME appearance.

![Main View](./screenshots/main_view.png)

## Features

- **Easy File Scanning**: Select files or directories to scan using the native GTK4 file dialog
- **Async Scanning**: Background scanning keeps the UI responsive
- **Quarantine Management**: Isolate and manage detected threats safely
- **Scan Profiles**: Create custom scan configurations for different use cases
- **Scan History**: Track and review past scan results
- **Statistics Dashboard**: Monitor your scanning activity and threat detection
- **File Manager Integration**: Right-click "Scan with ClamUI" in Nautilus, Dolphin, and Nemo
- **System Tray**: Optional tray icon with quick actions and scan progress
- **Modern UI**: Native Adwaita styling with proper GNOME integration

## Screenshots

<table>
<tr>
<td><img src="./screenshots/main_view_with_scan_result.png" alt="Scan Results" width="400"/></td>
<td><img src="./screenshots/quarantine_view.png" alt="Quarantine View" width="400"/></td>
</tr>
<tr>
<td align="center"><em>Scan Results</em></td>
<td align="center"><em>Quarantine Management</em></td>
</tr>
<tr>
<td><img src="./screenshots/components_view.png" alt="Components View" width="400"/></td>
<td><img src="./screenshots/history_view.png" alt="History View" width="400"/></td>
</tr>
<tr>
<td align="center"><em>ClamAV Components Status</em></td>
<td align="center"><em>Scan History</em></td>
</tr>
<tr>
<td><img src="./screenshots/profile_management.png" alt="Profile Management" width="400"/></td>
<td><img src="./screenshots/config_view.png" alt="Settings" width="400"/></td>
</tr>
<tr>
<td align="center"><em>Scan Profiles</em></td>
<td align="center"><em>Settings</em></td>
</tr>
</table>

## Quick Start

### Flatpak (Recommended)

```bash
flatpak install flathub com.github.clamui
flatpak run com.github.clamui
```

### From Source

```bash
git clone https://github.com/rooki/clamui.git
cd clamui
uv sync
uv run clamui
```

For detailed installation options including .deb packages and system-wide installation, see the [Installation Guide](./docs/INSTALL.md).

## Usage

1. Launch ClamUI from your application menu or terminal
2. Select a file or folder to scan
3. Click "Scan" to start the antivirus scan
4. View results and take action on any threats detected

### Command Line

```bash
# Launch the application
clamui

# Scan specific files directly
clamui /path/to/file1 /path/to/folder
```

## Documentation

| Document | Description |
|----------|-------------|
| [Installation Guide](./docs/INSTALL.md) | Flatpak, .deb, context menu, and tray setup |
| [Development Guide](./docs/DEVELOPMENT.md) | Dev environment, testing, and contributing |
| [Debian Packaging](./DEBIAN_PACKAGING.md) | Building .deb packages |
| [Flatpak Submission](./FLATPAK_SUBMISSION.md) | Flathub submission guide |
| [Security Policy](./SECURITY.txt) | Security contact and reporting |

## Requirements

- **ClamAV**: The `clamscan` command-line tool must be installed
- **GTK4 + libadwaita**: For the graphical interface
- **Python 3.x**: With PyGObject bindings

See the [Installation Guide](./docs/INSTALL.md) for platform-specific dependency installation.

## Contributing

Contributions are welcome! Please see the [Development Guide](./docs/DEVELOPMENT.md) for:

- Setting up the development environment
- Running tests with coverage
- Code style guidelines
- Submitting pull requests

## License

This project is open source. See LICENSE file for details.
