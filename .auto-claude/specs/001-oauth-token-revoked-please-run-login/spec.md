# Specification: ClamAV Desktop GUI Application

## Overview

This specification defines the implementation of a Linux desktop application that provides a graphical user interface for the ClamAV antivirus command-line tool. The application will be built using PyGObject with GTK4 and Adwaita for a modern, native Linux appearance. This initial implementation focuses on establishing the project foundation, core UI components, and basic scanning functionality. The goal is to create an attractive, user-friendly interface that wraps ClamAV's CLI capabilities while keeping the scope limited to essential features.

## Workflow Type

**Type**: infrastructure

**Rationale**: This is a greenfield project requiring complete setup from scratch. There is no existing codebase - we need to establish the project structure, dependencies, build configuration, and foundational architecture. This fits the infrastructure workflow as we're creating the base upon which future features will be built.

## Task Scope

### Services Involved
- **clamui** (primary) - Python GTK4/Adwaita desktop application providing GUI for ClamAV
- **ClamAV CLI** (external dependency) - System-installed antivirus tools (`clamscan`, `freshclam`)

### This Task Will:
- [x] Set up Python project structure with proper packaging
- [x] Configure GTK4/Adwaita application skeleton
- [x] Implement main application window with modern styling
- [x] Create folder/file selection component for scan targets
- [x] Implement scan button with visual feedback
- [x] Build results display area for scan output
- [x] Integrate basic `clamscan` execution via subprocess
- [x] Handle async scanning to prevent UI blocking
- [x] Add basic error handling for missing ClamAV installation

### Out of Scope:
- Scheduled/automated scanning
- Quarantine management
- Detailed configuration options
- Real-time protection/monitoring
- `freshclam` database update UI (deferred)
- System tray integration
- Multi-language support
- Application packaging (.deb, .rpm, Flatpak)

## Service Context

### ClamUI Application

**Tech Stack:**
- Language: Python 3.x
- Framework: PyGObject (GTK4 bindings)
- UI Toolkit: GTK4 with libadwaita (Adwaita widgets)
- Key directories: `src/`, `src/ui/`, `src/core/`

**Entry Point:** `src/main.py`

**How to Run:**
```bash
python src/main.py
```

**Port:** N/A (Desktop application)

**Dependencies:**
- PyGObject >= 3.48.0
- pycairo >= 1.25.0
- GTK4 (system library)
- libadwaita-1 (system library)

### ClamAV (External Dependency)

**Required Commands:**
- `clamscan` - Primary scanning utility
- `freshclam` - Database update utility (optional for basic version)

**Installation Check:**
```bash
which clamscan && clamscan --version
```

## Files to Create

| File | Purpose |
|------|---------|
| `src/main.py` | Application entry point and GTK app initialization |
| `src/app.py` | Main Adwaita Application class |
| `src/ui/window.py` | Main application window with UI layout |
| `src/ui/scan_view.py` | Scan interface component (folder picker, scan button, results) |
| `src/core/scanner.py` | ClamAV subprocess integration and output parsing |
| `src/core/utils.py` | Utility functions (ClamAV detection, path validation) |
| `requirements.txt` | Python dependencies |
| `README.md` | Project documentation and setup instructions |
| `.gitignore` | Git ignore patterns for Python projects |

## Files to Reference

These patterns should be followed (from research phase):

| Pattern | Description |
|---------|-------------|
| GTK4/Adwaita Application | Standard GNOME application structure with Adw.Application |
| GLib.idle_add threading | Thread-safe UI updates from background operations |
| Subprocess async execution | Non-blocking CLI command execution |

## Patterns to Follow

### GTK4/Adwaita Application Initialization

```python
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio

class ClamUIApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="com.github.clamui",
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )

    def do_activate(self):
        win = MainWindow(application=self)
        win.present()
```

**Key Points:**
- Version requirements MUST be set before importing from gi.repository
- Application ID must use reverse-DNS format
- Use Adw.Application for modern GNOME styling

### Thread-Safe UI Updates

```python
import threading
from gi.repository import GLib

def run_scan_async(self, path, callback):
    def scan_thread():
        result = self._execute_scan(path)
        GLib.idle_add(callback, result)

    thread = threading.Thread(target=scan_thread)
    thread.daemon = True
    thread.start()
```

**Key Points:**
- Never block GTK main thread with long operations
- Use GLib.idle_add() to safely update UI from background threads
- Set daemon=True so threads don't prevent app exit

### ClamAV Output Parsing

```python
import subprocess

def execute_scan(self, path):
    try:
        result = subprocess.run(
            ['clamscan', '-r', '-i', path],
            capture_output=True,
            text=True
        )
        # Exit codes: 0=clean, 1=virus found, 2=error
        return {
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'infected': result.returncode == 1
        }
    except FileNotFoundError:
        return {'error': 'ClamAV not installed'}
```

**Key Points:**
- Exit code 1 means virus FOUND (not an error)
- Exit code 2 indicates actual error
- Handle FileNotFoundError for missing ClamAV

## Requirements

### Functional Requirements

1. **Application Launch**
   - Description: Application starts and displays main window with Adwaita styling
   - Acceptance: Running `python src/main.py` opens a styled GTK4 window

2. **Folder/File Selection**
   - Description: User can select a folder or file to scan using native file dialog
   - Acceptance: Clicking "Select" opens GTK FileDialog, selection updates UI

3. **Scan Execution**
   - Description: User can initiate a scan of selected path
   - Acceptance: Clicking "Scan" runs clamscan on selected path

4. **Progress Indication**
   - Description: UI shows scan is in progress without freezing
   - Acceptance: Scan button changes state, UI remains responsive during scan

5. **Results Display**
   - Description: Scan results are displayed in a readable format
   - Acceptance: After scan completes, results show in text view area

6. **ClamAV Detection**
   - Description: App detects if ClamAV is installed and shows appropriate message
   - Acceptance: Missing ClamAV shows helpful error message, not crash

### Edge Cases

1. **ClamAV Not Installed** - Display clear error message with installation instructions
2. **Empty Folder Selected** - Handle gracefully, show "No files to scan" message
3. **Permission Denied** - Catch and display user-friendly error for inaccessible paths
4. **Scan Cancelled** - (Future) Handle mid-scan cancellation gracefully
5. **Very Large Directory** - Scan runs async, UI stays responsive
6. **Special Characters in Path** - Paths properly escaped for subprocess

## Implementation Notes

### DO
- Follow GTK4/Adwaita patterns for modern GNOME appearance
- Use `Adw.ApplicationWindow` for the main window
- Use `Adw.HeaderBar` for the title bar
- Use `Adw.StatusPage` for empty/error states
- Parse clamscan output line-by-line for potential real-time updates
- Keep UI responsive by running scans in background threads
- Use GLib.idle_add for all UI updates from threads
- Validate paths before passing to clamscan

### DON'T
- Block the main GTK thread with subprocess calls
- Use GTK3 patterns or widgets (GTK4 only)
- Ignore clamscan exit codes (1 = virus found, not error)
- Hard-code paths or make assumptions about ClamAV location
- Create complex abstractions for this basic version
- Add features beyond the defined scope

## Project Structure

```
clamui/
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── app.py               # Adw.Application class
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── window.py        # Main window
│   │   └── scan_view.py     # Scan interface component
│   └── core/
│       ├── __init__.py
│       ├── scanner.py       # ClamAV integration
│       └── utils.py         # Utilities
├── requirements.txt
├── README.md
└── .gitignore
```

## Development Environment

### System Dependencies (Ubuntu/Debian)

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 libadwaita-1-dev
sudo apt install clamav  # For testing
```

### Python Dependencies

```bash
pip install PyGObject pycairo
```

### Start Application

```bash
cd /home/rooki/autoclaudeprojects/clamui
python src/main.py
```

### Verify ClamAV Installation

```bash
which clamscan
clamscan --version
```

### Required Environment Variables
- None required for basic version

## Success Criteria

The task is complete when:

1. [x] Project structure created with all specified files
2. [x] Application launches without errors (`python src/main.py`)
3. [x] Main window displays with Adwaita/GTK4 styling
4. [x] Folder selection dialog works correctly
5. [x] Scan can be initiated on selected folder
6. [x] UI remains responsive during scan (async execution)
7. [x] Scan results display in results area
8. [x] Missing ClamAV handled gracefully with error message
9. [x] No console errors or Python exceptions during normal use
10. [x] Code follows GTK4/Adwaita patterns consistently

## QA Acceptance Criteria

**CRITICAL**: These criteria must be verified by the QA Agent before sign-off.

### Unit Tests
| Test | File | What to Verify |
|------|------|----------------|
| Scanner ClamAV detection | `tests/test_scanner.py` | `check_clamav_installed()` returns correct boolean |
| Output parsing | `tests/test_scanner.py` | Scan results parsed correctly from clamscan output |
| Path validation | `tests/test_utils.py` | Invalid paths handled, special characters escaped |

### Integration Tests
| Test | Services | What to Verify |
|------|----------|----------------|
| Scan execution | clamui ↔ clamscan | Subprocess executes and returns expected structure |
| UI-Scanner integration | window ↔ scanner | Scan results properly passed to UI callback |

### End-to-End Tests
| Flow | Steps | Expected Outcome |
|------|-------|------------------|
| Basic scan flow | 1. Launch app 2. Select folder 3. Click Scan 4. View results | Results displayed, no UI freeze |
| Missing ClamAV | 1. Rename clamscan 2. Launch app 3. Try scan | Error message displayed |
| Empty selection | 1. Launch app 2. Click Scan without selection | Appropriate feedback shown |

### Manual Verification
| Check | Action | Expected |
|-------|--------|----------|
| Window appearance | Launch app | Modern Adwaita styling, proper header bar |
| File dialog | Click folder select | Native GTK4 file chooser opens |
| Scan button states | During scan | Button shows scanning state, disables double-click |
| Results readability | After scan | Results clearly formatted, scrollable |
| Responsive UI | During long scan | Window movable, not frozen |

### Code Quality Checks
| Check | Command | Expected |
|-------|---------|----------|
| Python syntax | `python -m py_compile src/**/*.py` | No syntax errors |
| Import verification | `python -c "from src.app import ClamUIApp"` | No import errors |
| GTK4 version | Check gi.require_version calls | GTK 4.0, Adw 1 specified |

### QA Sign-off Requirements
- [ ] Application launches successfully
- [ ] All manual verification checks pass
- [ ] UI follows Adwaita design patterns
- [ ] Scan functionality works end-to-end
- [ ] Error states handled gracefully
- [ ] No Python exceptions during normal use
- [ ] Code structure matches specification
- [ ] Threading implemented correctly (no UI freezes)
- [ ] ClamAV detection works correctly
