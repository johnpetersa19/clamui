# ClamUI Debian Package Guide

This document provides comprehensive instructions for building, installing, and understanding the Debian packaging for ClamUI.

## Table of Contents

1. [Overview](#overview)
2. [Debian Package Structure](#debian-package-structure)
3. [Control File Reference](#control-file-reference)
4. [Maintainer Scripts](#maintainer-scripts)
5. [Prerequisites](#prerequisites)
6. [Building the Package](#building-the-package)
7. [Installing and Removing](#installing-and-removing)
8. [Verification Commands](#verification-commands)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Topics](#advanced-topics)

---

## Overview

ClamUI is distributed as a Debian `.deb` package for easy installation on Debian, Ubuntu, and derivative Linux distributions. The package follows the Filesystem Hierarchy Standard (FHS) and Debian Policy for proper system integration.

### Package Information

| Field | Value |
|-------|-------|
| Package Name | `clamui` |
| Architecture | `all` (pure Python, platform-independent) |
| Section | `utils` |
| Priority | `optional` |

### What Gets Installed

When you install the ClamUI package, the following files are placed on your system:

| Path | Description |
|------|-------------|
| `/usr/bin/clamui` | Launcher script (executable) |
| `/usr/lib/python3/dist-packages/clamui/` | Python application modules |
| `/usr/share/applications/com.github.rooki.ClamUI.desktop` | Desktop entry file |
| `/usr/share/icons/hicolor/scalable/apps/com.github.rooki.ClamUI.svg` | Application icon |
| `/usr/share/metainfo/com.github.rooki.ClamUI.metainfo.xml` | AppStream metadata |

---

## Debian Package Structure

A `.deb` package is essentially an `ar` archive containing control information and file data. The ClamUI package follows this standard structure:

```
clamui_0.1.0_all.deb
└── (archive contents)
    ├── debian-binary          # Package format version ("2.0")
    ├── control.tar.xz         # Control files archive
    │   ├── control            # Package metadata
    │   ├── postinst           # Post-installation script
    │   ├── prerm              # Pre-removal script
    │   └── postrm             # Post-removal script
    └── data.tar.xz            # Installed files archive
        └── usr/
            ├── bin/
            │   └── clamui     # Launcher script
            ├── lib/
            │   └── python3/
            │       └── dist-packages/
            │           └── clamui/
            │               ├── __init__.py
            │               ├── main.py
            │               ├── app.py
            │               ├── core/
            │               └── ui/
            └── share/
                ├── applications/
                │   └── com.github.rooki.ClamUI.desktop
                ├── icons/
                │   └── hicolor/
                │       └── scalable/
                │           └── apps/
                │               └── com.github.rooki.ClamUI.svg
                └── metainfo/
                    └── com.github.rooki.ClamUI.metainfo.xml
```

### Directory Purposes

| Directory | Purpose |
|-----------|---------|
| `DEBIAN/` | Contains package control files and maintainer scripts |
| `usr/bin/` | User-executable programs |
| `usr/lib/python3/dist-packages/` | System-wide Python modules |
| `usr/share/applications/` | Desktop entry files for application menus |
| `usr/share/icons/hicolor/` | Theme-compatible icons (follows freedesktop.org spec) |
| `usr/share/metainfo/` | AppStream application metadata |

---

## Control File Reference

The control file (`debian/DEBIAN/control`) defines package metadata that `dpkg` uses for installation and dependency resolution.

### Control File Format

```
Package: clamui
Version: 0.1.0
Section: utils
Priority: optional
Architecture: all
Depends: python3 (>= 3.10), python3-gi, python3-cairo, gir1.2-gtk-4.0, gir1.2-adw-1, clamav
Maintainer: ClamUI Contributors <clamui@example.com>
Homepage: https://github.com/yourusername/clamui
Description: Modern graphical interface for ClamAV antivirus scanner
 ClamUI is a modern Linux desktop application that provides a graphical
 user interface for the ClamAV antivirus command-line tool.
 .
 Features:
  - Easy-to-use GTK4/libadwaita interface
  - Scan files and directories for malware
  - View and manage scan results
  - Desktop integration with notifications
 .
 This package requires ClamAV to be installed for scanning functionality.
```

### Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| `Package` | Yes | Package name (lowercase, alphanumeric, hyphens allowed) |
| `Version` | Yes | Version number (typically `major.minor.patch`) |
| `Section` | No | Category in the archive (`utils`, `admin`, `net`, etc.) |
| `Priority` | No | Installation priority (`required`, `important`, `standard`, `optional`) |
| `Architecture` | Yes | Target architecture (`all` for platform-independent, `amd64`, `arm64`, etc.) |
| `Depends` | No | Packages required for this package to function |
| `Maintainer` | Yes | Name and email of package maintainer |
| `Homepage` | No | Project website URL |
| `Description` | Yes | Short description (first line) and long description (subsequent lines, indented with space) |

### Dependency Explanation

ClamUI depends on the following system packages:

| Dependency | Purpose |
|------------|---------|
| `python3 (>= 3.10)` | Python interpreter (version 3.10 or higher required) |
| `python3-gi` | PyGObject bindings for GLib/GTK |
| `python3-cairo` | Python bindings for Cairo graphics library |
| `gir1.2-gtk-4.0` | GTK 4 introspection data |
| `gir1.2-adw-1` | libadwaita introspection data |
| `clamav` | ClamAV antivirus engine |

---

## Maintainer Scripts

Maintainer scripts are shell scripts that run at various points during package installation and removal. ClamUI uses three maintainer scripts.

### Script Execution Order

**During Installation (`dpkg -i`):**
1. `preinst` (not used by ClamUI)
2. Files are unpacked
3. `postinst configure`

**During Removal (`dpkg -r`):**
1. `prerm remove`
2. Files are removed
3. `postrm remove`

**During Purge (`dpkg -P`):**
1. Same as removal
2. `postrm purge` (removes configuration files)

### postinst Script

The `postinst` script runs after package files are installed. ClamUI's postinst:

- Updates the desktop file database (`update-desktop-database`)
- Refreshes the GTK icon cache (`gtk-update-icon-cache`)

```bash
#!/bin/bash
set -e

case "$1" in
    configure)
        # Update desktop file database
        if command -v update-desktop-database > /dev/null 2>&1; then
            update-desktop-database -q /usr/share/applications || true
        fi

        # Update GTK icon cache
        if command -v gtk-update-icon-cache > /dev/null 2>&1; then
            gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
        fi
        ;;
esac

exit 0
```

### prerm Script

The `prerm` script runs before package files are removed. ClamUI's prerm is minimal since there are no background services to stop:

```bash
#!/bin/bash
set -e

case "$1" in
    remove|upgrade|deconfigure)
        # No services to stop for GUI application
        ;;
esac

exit 0
```

### postrm Script

The `postrm` script runs after package files are removed. ClamUI's postrm:

- Updates the desktop file database to remove the application entry
- Refreshes the icon cache to remove the application icon

```bash
#!/bin/bash
set -e

case "$1" in
    remove|purge)
        if command -v update-desktop-database > /dev/null 2>&1; then
            update-desktop-database -q /usr/share/applications || true
        fi
        if command -v gtk-update-icon-cache > /dev/null 2>&1; then
            gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
        fi
        ;;
esac

exit 0
```

### Script Best Practices

All ClamUI maintainer scripts follow Debian best practices:

1. **Idempotent**: Scripts can be run multiple times without side effects
2. **Error Tolerant**: Commands use `|| true` to prevent failures from aborting
3. **Command Checks**: `command -v` verifies tools exist before use
4. **Proper Exit**: Scripts exit with code 0 on success

---

## Prerequisites

Before building the ClamUI Debian package, install the required build tools:

```bash
# Install Debian packaging tools
sudo apt install dpkg-dev fakeroot

# Verify installation
dpkg-deb --version
fakeroot --version
```

### Tool Descriptions

| Tool | Package | Purpose |
|------|---------|---------|
| `dpkg-deb` | `dpkg-dev` | Creates and extracts `.deb` archives |
| `fakeroot` | `fakeroot` | Simulates root privileges for file ownership |

---

## Building the Package

### Quick Build

From the project root directory:

```bash
# Make the script executable (if needed)
chmod +x debian/build-deb.sh

# Build the package
./debian/build-deb.sh
```

This creates `clamui_VERSION_all.deb` in the project root (e.g., `clamui_0.1.0_all.deb`).

### What the Build Script Does

1. **Checks Prerequisites**: Verifies `dpkg-deb` and `fakeroot` are available
2. **Extracts Version**: Reads version from `pyproject.toml`
3. **Creates Build Directory**: Sets up FHS-compliant directory structure
4. **Copies Python Source**: Installs source to `dist-packages` (excluding `__pycache__`)
5. **Creates Launcher**: Generates `/usr/bin/clamui` executable script
6. **Copies Desktop Files**: Installs `.desktop`, icon, and metainfo files
7. **Processes Control Files**: Copies DEBIAN files with version substitution
8. **Builds Package**: Uses `fakeroot dpkg-deb --build`
9. **Cleans Up**: Removes temporary build directory

### Build Options

```bash
# Show help
./debian/build-deb.sh --help
```

---

## Installing and Removing

### Install the Package

```bash
# Install the package
sudo dpkg -i clamui_0.1.0_all.deb

# If there are missing dependencies, fix them with:
sudo apt install -f
```

### Run the Application

After installation:

```bash
# From command line
clamui

# Or find "ClamUI" in your application menu
```

### Remove the Package

```bash
# Remove (keeps configuration files)
sudo dpkg -r clamui

# Purge (removes everything including config)
sudo dpkg -P clamui
```

---

## Verification Commands

This section provides comprehensive commands for verifying the package at every stage.

### Package Integrity Checks

```bash
# Verify package file exists and show size
ls -la clamui_*.deb

# Check file type (should show "Debian binary package")
file clamui_0.1.0_all.deb

# Verify archive integrity
ar -t clamui_0.1.0_all.deb
# Expected output:
# debian-binary
# control.tar.xz (or .gz)
# data.tar.xz (or .gz)

# Calculate checksum for distribution
sha256sum clamui_0.1.0_all.deb
md5sum clamui_0.1.0_all.deb
```

### Before Installation

```bash
# Show package information (name, version, dependencies, description)
dpkg -I clamui_0.1.0_all.deb

# List package contents with full paths
dpkg -c clamui_0.1.0_all.deb

# Extract package without installing (for inspection)
mkdir -p ./extract-test/
dpkg-deb -x clamui_0.1.0_all.deb ./extract-test/
dpkg-deb -e clamui_0.1.0_all.deb ./extract-test/DEBIAN/

# Inspect extracted control file
cat ./extract-test/DEBIAN/control

# Inspect extracted maintainer scripts
cat ./extract-test/DEBIAN/postinst
cat ./extract-test/DEBIAN/prerm
cat ./extract-test/DEBIAN/postrm

# Clean up extraction directory
rm -rf ./extract-test/

# Verify dependencies are available (dry-run)
apt-cache show python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 clamav > /dev/null && echo "All dependencies available"
```

### After Installation

```bash
# Check if package is installed (shows status, version, description)
dpkg -l clamui

# Show installed package details (full metadata)
dpkg -s clamui

# List all files installed by the package
dpkg -L clamui

# Find which package owns a file
dpkg -S /usr/bin/clamui

# Verify binary is in PATH and executable
which clamui
test -x "$(which clamui)" && echo "Executable OK"

# Check binary permissions
ls -la /usr/bin/clamui

# Verify Python modules are installed
ls -la /usr/lib/python3/dist-packages/clamui/

# Test Python import (non-GUI test)
python3 -c "from clamui.main import main; print('Import OK')"

# Verify desktop file is installed
ls -la /usr/share/applications/com.github.rooki.ClamUI.desktop

# Validate desktop file
desktop-file-validate /usr/share/applications/com.github.rooki.ClamUI.desktop 2>&1 || echo "Note: desktop-file-validate not installed (install desktop-file-utils)"

# Verify icon is installed
ls -la /usr/share/icons/hicolor/scalable/apps/com.github.rooki.ClamUI.svg

# Verify metainfo is installed
ls -la /usr/share/metainfo/com.github.rooki.ClamUI.metainfo.xml

# Validate AppStream metadata
appstreamcli validate /usr/share/metainfo/com.github.rooki.ClamUI.metainfo.xml 2>&1 || echo "Note: appstreamcli not installed (install appstream)"
```

### Application Launch Verification

```bash
# Basic launch test (will show GUI if display available)
clamui

# Launch with environment debugging
G_MESSAGES_DEBUG=all clamui

# Check for GTK/GLib warnings
clamui 2>&1 | head -50

# Verify display requirements are met (for headless servers)
echo $DISPLAY  # Should not be empty for GUI apps
```

### Complete Verification Workflow

Run this complete verification sequence after building:

```bash
#!/bin/bash
# complete-verification.sh

echo "=== Package Verification ==="
PKG="clamui_0.1.0_all.deb"

# 1. Check package exists
echo "1. Checking package exists..."
test -f "$PKG" || { echo "FAIL: Package not found"; exit 1; }
echo "   OK: $PKG exists ($(du -h "$PKG" | cut -f1))"

# 2. Verify package metadata
echo "2. Verifying package metadata..."
dpkg -I "$PKG" | grep -q "Package: clamui" || { echo "FAIL: Wrong package name"; exit 1; }
echo "   OK: Package metadata valid"

# 3. Check expected files
echo "3. Checking package contents..."
dpkg -c "$PKG" | grep -q "usr/bin/clamui" || { echo "FAIL: Missing /usr/bin/clamui"; exit 1; }
dpkg -c "$PKG" | grep -q "dist-packages/clamui" || { echo "FAIL: Missing Python modules"; exit 1; }
echo "   OK: Expected files present"

# 4. Verify dependencies are satisfiable
echo "4. Checking dependencies..."
DEPS=$(dpkg -I "$PKG" | grep "Depends:" | sed 's/Depends://')
echo "   Dependencies: $DEPS"
echo "   (Run: sudo apt install -f after dpkg -i to resolve)"

echo ""
echo "=== Verification Complete ==="
echo "Install with: sudo dpkg -i $PKG"
```

---

## Troubleshooting

This section covers common issues encountered during building, installation, and running ClamUI from the Debian package.

### Quick Diagnostics

Run these commands first to gather diagnostic information:

```bash
# System information
lsb_release -a
uname -a
python3 --version

# Check if package is installed
dpkg -l clamui 2>/dev/null || echo "Package not installed"

# Check GTK/libadwaita availability
python3 -c "import gi; gi.require_version('Gtk', '4.0'); gi.require_version('Adw', '1'); print('GTK4/libadwaita OK')" 2>&1

# Check ClamAV availability
which clamscan && clamscan --version
```

### Build Errors

#### "dpkg-deb not found"

**Symptom:** Build script fails with "dpkg-deb: command not found"

**Solution:**
```bash
# Install dpkg-dev package
sudo apt install dpkg-dev

# Verify installation
dpkg-deb --version
```

#### "fakeroot not found"

**Symptom:** Build script fails with "fakeroot: command not found"

**Solution:**
```bash
# Install fakeroot package
sudo apt install fakeroot

# Verify installation
fakeroot --version
```

#### "pyproject.toml not found"

**Symptom:** Build script fails with "pyproject.toml not found"

**Cause:** Running the build script from the wrong directory.

**Solution:**
```bash
# Navigate to project root first
cd /path/to/clamui
ls pyproject.toml  # Verify file exists

# Now run build script
./debian/build-deb.sh
```

#### "Could not extract version"

**Symptom:** Build script fails with "Could not extract version from pyproject.toml"

**Cause:** Missing or malformed version field in pyproject.toml.

**Solution:**
```bash
# Check version field exists
grep 'version' pyproject.toml

# Ensure format is correct (must be under [project] section)
# Example:
# [project]
# version = "0.1.0"
```

#### "src/ directory not found"

**Symptom:** Build script fails with "Source directory not found"

**Cause:** Missing source code or incorrect project structure.

**Solution:**
```bash
# Verify project structure
ls -la src/
ls -la src/main.py

# Ensure you have the complete source
git status
```

#### "Permission denied" during build

**Symptom:** Build fails with permission errors when creating directories or files

**Cause:** Build directory has incorrect permissions or is on a read-only filesystem.

**Solution:**
```bash
# Check current directory is writable
touch test-write && rm test-write || echo "Directory not writable"

# Clean up any previous build with wrong permissions
sudo rm -rf build-deb/
rm -rf build-deb/

# Retry build
./debian/build-deb.sh
```

#### "dpkg-deb: error: control directory has bad permissions"

**Symptom:** dpkg-deb fails with permissions error

**Cause:** DEBIAN directory or control files have incorrect permissions.

**Solution:**
```bash
# This is handled by the build script, but if building manually:
chmod 755 build-deb/DEBIAN
chmod 644 build-deb/DEBIAN/control
chmod 755 build-deb/DEBIAN/postinst
chmod 755 build-deb/DEBIAN/prerm
chmod 755 build-deb/DEBIAN/postrm
```

### Installation Errors

#### "Dependency is not satisfiable"

**Symptom:** dpkg fails with "dependency problems prevent configuration"

**Solution:**
```bash
# Method 1: Let apt resolve dependencies
sudo dpkg -i clamui_0.1.0_all.deb
sudo apt install -f

# Method 2: Install dependencies first
sudo apt install python3-gi python3-cairo gir1.2-gtk-4.0 gir1.2-adw-1 clamav
sudo dpkg -i clamui_0.1.0_all.deb

# Method 3: Use apt directly (if package is in current directory)
sudo apt install ./clamui_0.1.0_all.deb
```

#### "Package architecture does not match"

**Symptom:** dpkg refuses to install package

**Cause:** Corrupted package or wrong package for system.

**Solution:**
```bash
# Verify package integrity
file clamui_0.1.0_all.deb  # Should say "Debian binary package"
ar -t clamui_0.1.0_all.deb  # Should list debian-binary, control.tar.*, data.tar.*

# Check package architecture (should be 'all' for ClamUI)
dpkg -I clamui_0.1.0_all.deb | grep Architecture

# Rebuild package if corrupted
./debian/build-deb.sh
```

#### "Trying to overwrite file from package"

**Symptom:** Conflict with existing files on the system

**Solution:**
```bash
# Check which package owns the conflicting file
dpkg -S /path/to/conflicting/file

# Force overwrite (use with caution)
sudo dpkg -i --force-overwrite clamui_0.1.0_all.deb
```

#### "Package is in a very bad inconsistent state"

**Symptom:** dpkg refuses to operate on package

**Cause:** Previous installation/removal was interrupted.

**Solution:**
```bash
# Force remove broken package
sudo dpkg --remove --force-remove-reinstreq clamui

# Clean up
sudo apt autoremove
sudo apt clean

# Reinstall
sudo dpkg -i clamui_0.1.0_all.deb
```

#### Old version not upgrading

**Symptom:** Installing new version but old version remains

**Solution:**
```bash
# Check installed version
dpkg -s clamui | grep Version

# Remove old version first
sudo dpkg -r clamui

# Install new version
sudo dpkg -i clamui_0.1.0_all.deb
```

### Runtime Errors

#### "ModuleNotFoundError: No module named 'clamui'"

**Symptom:** Python cannot find the clamui module

**Cause:** Python path doesn't include system packages directory.

**Solution:**
```bash
# Verify module is installed
ls /usr/lib/python3/dist-packages/clamui/

# Check Python path
python3 -c "import sys; print('\n'.join(sys.path))"

# Temporary fix: Run with explicit path
PYTHONPATH=/usr/lib/python3/dist-packages python3 -m clamui.main

# Permanent fix: Reinstall package
sudo dpkg -r clamui
sudo dpkg -i clamui_0.1.0_all.deb
```

#### "No module named 'gi'"

**Symptom:** PyGObject bindings not found

**Solution:**
```bash
sudo apt install python3-gi python3-cairo

# Verify installation
python3 -c "import gi; print('gi module OK')"
```

#### "Namespace Gtk not available" / "Gtk-4.0"

**Symptom:** GTK 4 typelib not found

**Solution:**
```bash
sudo apt install gir1.2-gtk-4.0

# Verify
python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk; print('GTK4 OK')"
```

#### "Namespace Adw not available" / "Adw-1"

**Symptom:** libadwaita typelib not found

**Solution:**
```bash
sudo apt install gir1.2-adw-1

# Verify
python3 -c "import gi; gi.require_version('Adw', '1'); from gi.repository import Adw; print('libadwaita OK')"
```

#### "cannot open display"

**Symptom:** Application fails to start with display error

**Cause:** No graphical display available (common in SSH or headless servers).

**Solution:**
```bash
# Check if display is set
echo $DISPLAY

# If empty, set display (if X server is running)
export DISPLAY=:0

# For SSH, use X forwarding
ssh -X user@host
clamui

# For testing without display, use Xvfb (virtual framebuffer)
sudo apt install xvfb
xvfb-run clamui
```

#### "Gtk-WARNING: cannot open display"

**Symptom:** GTK cannot connect to display server

**Solution:**
```bash
# Check Wayland vs X11
echo $XDG_SESSION_TYPE

# For Wayland
GDK_BACKEND=wayland clamui

# For X11
GDK_BACKEND=x11 clamui

# With debugging
GTK_DEBUG=interactive clamui
```

#### ClamAV integration not working

**Symptom:** Scans fail or ClamAV not detected

**Solution:**
```bash
# Check ClamAV installation
which clamscan freshclam

# Install if missing
sudo apt install clamav clamav-daemon

# Update virus definitions
sudo freshclam

# Test scan manually
clamscan --version
echo "EICAR-STANDARD-ANTIVIRUS-TEST-FILE" > /tmp/test.txt
clamscan /tmp/test.txt
rm /tmp/test.txt
```

### Desktop Integration Issues

#### Application icon not showing

**Symptom:** ClamUI icon missing from application menu or launcher

**Solution:**
```bash
# Force icon cache refresh
sudo gtk-update-icon-cache -f /usr/share/icons/hicolor

# Verify icon exists
ls -la /usr/share/icons/hicolor/scalable/apps/com.github.rooki.ClamUI.svg

# Check icon cache timestamp
ls -la /usr/share/icons/hicolor/icon-theme.cache
```

#### Application not appearing in menu

**Symptom:** ClamUI not visible in applications menu

**Solution:**
```bash
# Update desktop database
sudo update-desktop-database /usr/share/applications/

# Verify desktop file exists and is valid
ls -la /usr/share/applications/com.github.rooki.ClamUI.desktop
desktop-file-validate /usr/share/applications/com.github.rooki.ClamUI.desktop

# Check for syntax errors in desktop file
cat /usr/share/applications/com.github.rooki.ClamUI.desktop

# Log out and log back in for menu to refresh
```

#### Desktop file validation errors

**Symptom:** `desktop-file-validate` reports errors

**Solution:**
```bash
# Check specific errors
desktop-file-validate /usr/share/applications/com.github.rooki.ClamUI.desktop

# Common fixes:
# - Ensure Exec= points to valid binary
# - Ensure Icon= name matches installed icon (without extension for system icons)
# - Ensure Categories= uses valid categories
```

### Package Removal Issues

#### Files left behind after removal

**Symptom:** Some ClamUI files remain after `dpkg -r`

**Cause:** Configuration files are kept during removal (use purge instead).

**Solution:**
```bash
# Full removal including config
sudo dpkg -P clamui

# Manually remove any leftovers
sudo rm -rf /usr/lib/python3/dist-packages/clamui/
sudo rm -f /usr/bin/clamui
sudo rm -f /usr/share/applications/com.github.rooki.ClamUI.desktop

# Refresh caches
sudo update-desktop-database
sudo gtk-update-icon-cache -f /usr/share/icons/hicolor
```

#### "Package is not installed"

**Symptom:** Trying to remove but package shows as not installed

**Solution:**
```bash
# Check actual status
dpkg -l clamui

# If partially installed
sudo dpkg --configure -a
sudo apt install -f

# Force removal of residual config
sudo dpkg --purge --force-remove-reinstreq clamui
```

### Upgrade Issues

#### Configuration preserved unexpectedly

**Symptom:** Old settings persist after upgrade

**Cause:** User configuration in home directory is not managed by package.

**Solution:**
```bash
# ClamUI stores user config in ~/.config/clamui/ (not managed by dpkg)
# To reset, remove user config
rm -rf ~/.config/clamui/

# Then restart application
clamui
```

#### Version mismatch after upgrade

**Symptom:** Application shows old version after installing newer package

**Solution:**
```bash
# Check installed version
dpkg -s clamui | grep Version

# Verify you installed the correct package
dpkg -I clamui_0.1.0_all.deb | grep Version

# Remove and reinstall
sudo dpkg -P clamui
sudo dpkg -i clamui_0.1.0_all.deb
```

### Debugging Tips

#### Enable verbose GTK debugging

```bash
# General debugging
G_MESSAGES_DEBUG=all clamui 2>&1 | tee clamui-debug.log

# GTK-specific debugging
GTK_DEBUG=actions,gestures,keybindings clamui

# GLib debugging
G_DEBUG=fatal-warnings clamui
```

#### Check system logs

```bash
# Recent journal entries
journalctl --since "5 minutes ago" | grep -i clamui

# Syslog entries
grep clamui /var/log/syslog
```

#### Verify package integrity after installation

```bash
# Compare installed files against package
dpkg -V clamui

# Empty output means all files match package
# Any output indicates modified/missing files
```

#### Test in isolated environment

```bash
# Use Docker for clean environment testing
docker run -it --rm -v $(pwd):/pkg debian:bookworm bash

# Inside container:
apt update
apt install -y /pkg/clamui_0.1.0_all.deb
apt install -f
# Note: GUI testing requires display passthrough
```

---

## Advanced Topics

### Manual Package Building

If you need to build the package manually without the build script:

```bash
# Create build directory structure
mkdir -p build-deb/DEBIAN
mkdir -p build-deb/usr/bin
mkdir -p build-deb/usr/lib/python3/dist-packages/clamui
mkdir -p build-deb/usr/share/applications
mkdir -p build-deb/usr/share/icons/hicolor/scalable/apps
mkdir -p build-deb/usr/share/metainfo

# Copy Python source (excluding __pycache__)
rsync -a --exclude='__pycache__' src/ build-deb/usr/lib/python3/dist-packages/clamui/

# Create launcher script
cat > build-deb/usr/bin/clamui << 'EOF'
#!/usr/bin/env python3
import sys
from clamui.main import main
sys.exit(main())
EOF
chmod 755 build-deb/usr/bin/clamui

# Copy desktop files
cp com.github.rooki.ClamUI.desktop build-deb/usr/share/applications/
cp icons/com.github.rooki.ClamUI.svg build-deb/usr/share/icons/hicolor/scalable/apps/
cp com.github.rooki.ClamUI.metainfo.xml build-deb/usr/share/metainfo/

# Copy and modify control file
sed 's/^Version: VERSION$/Version: 0.1.0/' debian/DEBIAN/control > build-deb/DEBIAN/control
cp debian/DEBIAN/post* debian/DEBIAN/prerm build-deb/DEBIAN/
chmod 755 build-deb/DEBIAN/postinst build-deb/DEBIAN/prerm build-deb/DEBIAN/postrm

# Set proper permissions
chmod 644 build-deb/DEBIAN/control
find build-deb/usr -type f -name '*.py' -exec chmod 644 {} +
find build-deb/usr/share -type f -exec chmod 644 {} +

# Build package
fakeroot dpkg-deb --build build-deb clamui_0.1.0_all.deb

# Clean up
rm -rf build-deb
```

### Inspecting an Existing Package

```bash
# Extract control files
ar x clamui_0.1.0_all.deb
tar xf control.tar.xz
cat control

# View all metadata
dpkg -I clamui_0.1.0_all.deb

# View file listing
dpkg -c clamui_0.1.0_all.deb
```

### Version Numbering

ClamUI follows semantic versioning (`MAJOR.MINOR.PATCH`):

- **MAJOR**: Incompatible API changes
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes, backwards compatible

The version is sourced from `pyproject.toml` and automatically substituted into the control file during build.

### Testing Package Installation in a Clean Environment

Use Docker to test package installation:

```bash
# Build test image
docker run -it --rm -v $(pwd):/pkg ubuntu:22.04 bash

# Inside container
apt update
apt install /pkg/clamui_0.1.0_all.deb
apt install -f
clamui --version  # Verify installation
```

### Lintian (Package Quality Checker)

For thorough package validation, use lintian:

```bash
# Install lintian
sudo apt install lintian

# Check package
lintian clamui_0.1.0_all.deb

# Verbose output with explanations
lintian -i -I clamui_0.1.0_all.deb
```

---

## Additional Resources

- [Debian Policy Manual](https://www.debian.org/doc/debian-policy/)
- [Debian New Maintainers' Guide](https://www.debian.org/doc/manuals/maint-guide/)
- [dpkg Manual Page](https://man7.org/linux/man-pages/man1/dpkg.1.html)
- [Filesystem Hierarchy Standard](https://refspecs.linuxfoundation.org/fhs.shtml)
- [Desktop Entry Specification](https://specifications.freedesktop.org/desktop-entry-spec/latest/)
- [AppStream Specification](https://www.freedesktop.org/software/appstream/docs/)
