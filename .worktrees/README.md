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
# GTK4 and Adwaita libraries
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 libadwaita-1-dev

# ClamAV antivirus
sudo apt install clamav
```

For other distributions:
- **Fedora**: `sudo dnf install python3-gobject gtk4 libadwaita clamav`
- **Arch**: `sudo pacman -S python-gobject gtk4 libadwaita clamav`

### Python Dependencies

- Python 3.x
- PyGObject >= 3.48.0
- pycairo >= 1.25.0

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/clamui.git
   cd clamui
   ```

2. **Install system dependencies** (see Requirements above)

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify ClamAV installation**:
   ```bash
   which clamscan
   clamscan --version
   ```

## Running the Application

```bash
python src/main.py
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
├── requirements.txt
├── README.md
└── .gitignore
```

## Usage

1. Launch the application with `python src/main.py`
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
