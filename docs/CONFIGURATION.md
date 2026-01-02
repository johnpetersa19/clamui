# ClamUI Configuration Reference

This document provides comprehensive reference documentation for all configuration options available in ClamUI.

## Table of Contents

1. [Overview](#overview)
2. [File Locations](#file-locations)
3. [Settings Reference](#settings-reference)
   - [General Settings](#general-settings)
   - [Notification Settings](#notification-settings)
   - [Quarantine Settings](#quarantine-settings)
   - [Scheduled Scan Settings](#scheduled-scan-settings)
   - [Scan Backend Settings](#scan-backend-settings)
4. [Scan Profiles](#scan-profiles)
   - [Profile Structure](#profile-structure)
   - [Default Profiles](#default-profiles)
   - [Exclusion Formats](#exclusion-formats)
5. [Configuration Examples](#configuration-examples)

---

## Overview

ClamUI stores user preferences in `settings.json`, a JSON-formatted configuration file located in the XDG-compliant configuration directory. All settings can be modified through the application's Preferences dialog or by directly editing the JSON file.

**Important:** ClamUI automatically creates default settings on first launch. Manual edits to `settings.json` require application restart to take effect.

---

## File Locations

ClamUI follows the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html) for file storage:

| Purpose | Default Location | Environment Variable Override |
|---------|------------------|-------------------------------|
| **Configuration** | `~/.config/clamui/` | `XDG_CONFIG_HOME` |
| **Data Storage** | `~/.local/share/clamui/` | `XDG_DATA_HOME` |

### Specific Files

| File | Location | Description |
|------|----------|-------------|
| `settings.json` | `~/.config/clamui/settings.json` | User preferences and application settings |
| `profiles.json` | `~/.config/clamui/profiles.json` | Scan profile definitions |
| `quarantine.db` | `~/.local/share/clamui/quarantine.db` | Quarantine metadata database (SQLite) |
| Quarantine files | `~/.local/share/clamui/quarantine/` | Quarantined file storage |
| Scan logs | `~/.local/share/clamui/logs/` | Historical scan logs (JSON) |

**Flatpak Note:** When running as a Flatpak, these paths are sandboxed within `~/.var/app/org.clamui.ClamUI/`.

---

## Settings Reference

All settings are stored in `~/.config/clamui/settings.json` as a JSON object. Below is the comprehensive reference for each setting.

### General Settings

#### `start_minimized`

**Type:** Boolean
**Default:** `false`
**Valid Values:** `true`, `false`

Controls whether ClamUI starts minimized to the system tray on application launch.

**Description:**
When enabled, ClamUI will launch in the background without showing the main window. This is useful for users who want ClamUI to run automatically at startup without interrupting their workflow. Requires system tray support to be available.

**Example:**
```json
{
  "start_minimized": true
}
```

---

#### `minimize_to_tray`

**Type:** Boolean
**Default:** `false`
**Valid Values:** `true`, `false`

Controls whether closing the main window minimizes to the system tray instead of quitting.

**Description:**
When enabled, clicking the window close button will hide the window to the system tray instead of exiting the application. The application continues running in the background and can be restored by clicking the tray icon. When disabled, closing the window exits ClamUI completely.

**Example:**
```json
{
  "minimize_to_tray": true
}
```

---

### Notification Settings

#### `notifications_enabled`

**Type:** Boolean
**Default:** `true`
**Valid Values:** `true`, `false`

Controls whether ClamUI displays desktop notifications for scan events.

**Description:**
When enabled, ClamUI sends desktop notifications for important events such as:
- Scan completion (with threat summary)
- Virus definition database updates
- Scheduled scan results
- Quarantine operations

Notifications appear through the system's notification daemon (e.g., GNOME Shell, KDE Plasma notifications).

**Example:**
```json
{
  "notifications_enabled": false
}
```

---

### Quarantine Settings

#### `quarantine_directory`

**Type:** String
**Default:** `""` (empty string = use default location)
**Valid Values:** Any valid absolute directory path, or empty string

Specifies a custom directory for storing quarantined files.

**Description:**
When set to an empty string (default), ClamUI uses the XDG-compliant location `~/.local/share/clamui/quarantine/`. You can override this with a custom path for centralized quarantine storage or to use a separate partition.

The specified directory must be writable by the user running ClamUI. Quarantined files are stored with encrypted names and tracked in a SQLite database.

**Example:**
```json
{
  "quarantine_directory": "/mnt/secure/quarantine"
}
```

**Default Behavior:**
```json
{
  "quarantine_directory": ""
}
```

---

### Scheduled Scan Settings

#### `scheduled_scans_enabled`

**Type:** Boolean
**Default:** `false`
**Valid Values:** `true`, `false`

Master switch to enable or disable scheduled automatic scans.

**Description:**
When enabled, ClamUI creates system timer entries (systemd user timers or cron jobs, depending on system availability) to run automatic scans based on the configured schedule. When disabled, all scheduled scans are deactivated.

**Example:**
```json
{
  "scheduled_scans_enabled": true
}
```

---

#### `schedule_frequency`

**Type:** String
**Default:** `"weekly"`
**Valid Values:** `"daily"`, `"weekly"`, `"monthly"`

Defines how often scheduled scans run.

**Description:**
- **`"daily"`**: Scans run every day at the time specified in `schedule_time`
- **`"weekly"`**: Scans run once per week on the day specified in `schedule_day_of_week`
- **`"monthly"`**: Scans run once per month on the day specified in `schedule_day_of_month`

**Example:**
```json
{
  "schedule_frequency": "daily"
}
```

---

#### `schedule_time`

**Type:** String
**Default:** `"02:00"`
**Valid Values:** 24-hour time in `HH:MM` format (e.g., `"02:00"`, `"14:30"`)

Specifies the time of day when scheduled scans execute.

**Description:**
Uses 24-hour format. For example:
- `"02:00"` = 2:00 AM
- `"14:30"` = 2:30 PM
- `"00:00"` = Midnight

The scan will run at this time according to the system's local timezone. For best performance, schedule scans during off-peak hours (e.g., early morning).

**Example:**
```json
{
  "schedule_time": "03:30"
}
```

---

#### `schedule_targets`

**Type:** Array of Strings
**Default:** `[]` (empty array)
**Valid Values:** List of absolute directory paths

Defines which directories to scan during scheduled scans.

**Description:**
Each element must be an absolute path to a directory. For example:
- `"/home/username"` - Scan entire home directory
- `"/home/username/Documents"` - Scan only Documents
- `"/var/www"` - Scan web server files

If the array is empty, scheduled scans will not run (no targets defined). You can specify multiple directories to scan them all in a single scheduled operation.

**Example:**
```json
{
  "schedule_targets": [
    "/home/username/Documents",
    "/home/username/Downloads"
  ]
}
```

---

#### `schedule_skip_on_battery`

**Type:** Boolean
**Default:** `true`
**Valid Values:** `true`, `false`

Controls whether scheduled scans are skipped when the system is running on battery power.

**Description:**
When enabled, ClamUI checks the system's power status before starting a scheduled scan. If the system is on battery power (not connected to AC), the scan is skipped to preserve battery life. This is especially useful for laptop users.

When disabled, scheduled scans run regardless of power source.

**Example:**
```json
{
  "schedule_skip_on_battery": false
}
```

---

#### `schedule_auto_quarantine`

**Type:** Boolean
**Default:** `false`
**Valid Values:** `true`, `false`

Controls whether infected files discovered during scheduled scans are automatically quarantined.

**Description:**
When enabled, any threats detected during scheduled scans are automatically moved to quarantine without user interaction. This provides automated threat response for unattended scans.

When disabled, infected files are logged but not quarantined. The user must manually review scan results and take action.

**⚠️ Caution:** Auto-quarantine can remove files without confirmation. Use with care and ensure you have backups.

**Example:**
```json
{
  "schedule_auto_quarantine": true
}
```

---

#### `schedule_day_of_week`

**Type:** Integer
**Default:** `0` (Monday)
**Valid Values:** `0` (Monday) through `6` (Sunday)

Specifies which day of the week to run scans when `schedule_frequency` is `"weekly"`.

**Description:**
Day numbering follows ISO 8601:
- `0` = Monday
- `1` = Tuesday
- `2` = Wednesday
- `3` = Thursday
- `4` = Friday
- `5` = Saturday
- `6` = Sunday

This setting only applies when `schedule_frequency` is set to `"weekly"`. It is ignored for daily or monthly schedules.

**Example:**
```json
{
  "schedule_day_of_week": 6
}
```
*Scans run every Sunday*

---

#### `schedule_day_of_month`

**Type:** Integer
**Default:** `1` (first day of month)
**Valid Values:** `1` through `28`

Specifies which day of the month to run scans when `schedule_frequency` is `"monthly"`.

**Description:**
Valid range is 1-28 to ensure the day exists in all months (February has only 28 days in non-leap years). For example:
- `1` = First day of each month
- `15` = Fifteenth day of each month
- `28` = Twenty-eighth day of each month

This setting only applies when `schedule_frequency` is set to `"monthly"`. It is ignored for daily or weekly schedules.

**Example:**
```json
{
  "schedule_day_of_month": 15
}
```
*Scans run on the 15th of each month*

---

#### `exclusion_patterns`

**Type:** Array of Strings
**Default:** `[]` (empty array)
**Valid Values:** List of glob patterns or absolute paths

Defines files and directories to exclude from all scans (manual and scheduled).

**Description:**
Each element can be:
- **Absolute path:** `/home/username/.cache` - Exact directory/file to exclude
- **Glob pattern:** `*.log` - Exclude all files matching pattern
- **Path with wildcard:** `/var/log/*.log` - Exclude logs in specific directory

Exclusions apply globally to all scan operations. This is useful for excluding:
- Cache directories
- Virtual environments
- Build artifacts
- Large archive files

**Example:**
```json
{
  "exclusion_patterns": [
    "/home/username/.cache",
    "/home/username/.venv",
    "*.iso",
    "*.log"
  ]
}
```

---

### Scan Backend Settings

#### `scan_backend`

**Type:** String
**Default:** `"auto"`
**Valid Values:** `"auto"`, `"daemon"`, `"clamscan"`

Selects which ClamAV scanning engine to use.

**Description:**
- **`"auto"`** (Recommended): Automatically selects the best available backend. Prefers the clamd daemon if running, otherwise falls back to clamscan. This provides the best balance of performance and compatibility.

- **`"daemon"`**: Forces use of the clamd daemon (`clamdscan` command). The daemon must be running for scans to work. This is the fastest option for repeated scans since the virus database stays loaded in memory. If clamd is not running, scans will fail.

- **`"clamscan"`**: Forces use of the standalone scanner. This loads the virus database for each scan, making it slower than the daemon but requires no background service. Useful for systems where clamd is not configured or for one-off scans.

**Performance Comparison:**
- **daemon**: ~1-5 seconds per scan (database pre-loaded)
- **clamscan**: ~10-30 seconds per scan (database loaded each time)

**Example:**
```json
{
  "scan_backend": "daemon"
}
```

---

#### `daemon_socket_path`

**Type:** String
**Default:** `""` (empty string = auto-detect)
**Valid Values:** Absolute path to Unix socket file, or empty string

Specifies the path to the clamd Unix domain socket.

**Description:**
When set to an empty string (default), ClamUI automatically detects the socket location by checking common paths:
- `/var/run/clamav/clamd.ctl`
- `/var/run/clamd.scan/clamd.sock`
- `/var/run/clamav/clamd.sock`
- `/run/clamav/clamd.ctl`

You can override auto-detection by specifying a custom socket path. This is necessary if your distribution uses a non-standard location or if you run multiple clamd instances.

This setting only applies when `scan_backend` is `"daemon"` or `"auto"` (and daemon is selected).

**Example:**
```json
{
  "daemon_socket_path": "/custom/path/to/clamd.sock"
}
```

**Default Behavior:**
```json
{
  "daemon_socket_path": ""
}
```

---

## Scan Profiles

ClamUI uses scan profiles to save and reuse common scanning configurations. Profiles define what to scan, what to exclude, and how to scan it. They are stored in `~/.config/clamui/profiles.json` as a JSON array of profile objects.

### Profile Structure

Each scan profile is a JSON object with the following fields:

#### `id`

**Type:** String (UUID)
**Required:** Yes

Unique identifier for the profile, automatically generated when the profile is created. This ID is used internally to reference and manage profiles.

**Example:** `"550e8400-e29b-41d4-a716-446655440000"`

---

#### `name`

**Type:** String
**Required:** Yes
**Length:** 1-50 characters

User-visible name for the profile. Must be unique across all profiles (case-sensitive). Profile names are displayed in the UI for selecting which configuration to use.

**Example:** `"Quick Scan"`, `"Documents Backup"`, `"Weekly System Check"`

---

#### `targets`

**Type:** Array of Strings
**Required:** Yes

List of directories or files to scan. Each element must be a valid path string. Paths can be:
- **Absolute paths:** `/home/username/Documents`
- **Home directory notation:** `~/Downloads` (expands to the user's home directory)
- **Root:** `/` (scans the entire filesystem)

Empty targets array is allowed but will result in no files being scanned.

**Example:**
```json
"targets": [
  "~/Documents",
  "~/Downloads",
  "/var/www"
]
```

---

#### `exclusions`

**Type:** Object (Dictionary)
**Required:** No (defaults to empty object `{}`)

Defines files and directories to exclude from the scan. The exclusions object can contain two optional keys:

##### `exclusions.paths`

**Type:** Array of Strings

List of specific paths to exclude. Each path can be:
- **Absolute path:** `/var/cache` - Excludes this exact directory
- **Home directory notation:** `~/.cache` - Excludes user cache directory
- **Subdirectories:** All subdirectories within an excluded path are also excluded

**Example:**
```json
"exclusions": {
  "paths": [
    "~/.cache",
    "~/.local/share/Trash",
    "/proc",
    "/sys"
  ]
}
```

##### `exclusions.patterns`

**Type:** Array of Strings

List of glob patterns to match filenames for exclusion. Patterns support standard glob syntax:
- `*.log` - All .log files
- `*.tmp` - All temporary files
- `*~` - Backup files (common in text editors)
- `*.iso` - Disk image files

**Example:**
```json
"exclusions": {
  "patterns": [
    "*.log",
    "*.tmp",
    "*.bak",
    "*.iso"
  ]
}
```

##### Combined Example

```json
"exclusions": {
  "paths": [
    "~/.cache",
    "/var/tmp"
  ],
  "patterns": [
    "*.log",
    "*.tmp"
  ]
}
```

---

#### `created_at`

**Type:** String (ISO 8601 timestamp)
**Required:** Yes

Timestamp indicating when the profile was created. Automatically generated in UTC timezone.

**Format:** `YYYY-MM-DDTHH:MM:SS.ssssss+00:00`

**Example:** `"2024-01-15T10:30:45.123456+00:00"`

---

#### `updated_at`

**Type:** String (ISO 8601 timestamp)
**Required:** Yes

Timestamp indicating when the profile was last modified. Automatically updated on any profile change.

**Format:** `YYYY-MM-DDTHH:MM:SS.ssssss+00:00`

**Example:** `"2024-01-15T14:22:10.654321+00:00"`

---

#### `is_default`

**Type:** Boolean
**Required:** Yes
**Default:** `false`

Indicates whether this is a built-in default profile. Default profiles:
- Cannot be deleted through the UI
- Are automatically recreated if missing
- Are marked for special handling in the profile manager

User-created profiles should always have `is_default: false`.

**Example:** `true` (for built-in profiles), `false` (for user profiles)

---

#### `description`

**Type:** String
**Required:** No (defaults to empty string)

Human-readable description explaining the profile's purpose. Displayed in the UI to help users understand what the profile does.

**Example:**
```json
"description": "Fast scan of the Downloads folder for quick threat detection"
```

---

#### `options`

**Type:** Object (Dictionary)
**Required:** No (defaults to empty object `{}`)

Additional scan engine options and configuration. Currently supports custom scan parameters that may be added in future versions. Reserved for future expansion.

**Example:**
```json
"options": {}
```

---

### Default Profiles

ClamUI includes three built-in default profiles that are automatically created on first launch:

#### 1. Quick Scan

**Purpose:** Fast scan of the Downloads folder for quick threat detection

**Configuration:**
```json
{
  "name": "Quick Scan",
  "description": "Fast scan of the Downloads folder for quick threat detection",
  "targets": ["~/Downloads"],
  "exclusions": {},
  "options": {},
  "is_default": true
}
```

**Use Case:** Quickly scan newly downloaded files before opening them. Ideal for daily use when you want to verify new downloads.

---

#### 2. Full Scan

**Purpose:** Comprehensive system-wide scan of all accessible directories

**Configuration:**
```json
{
  "name": "Full Scan",
  "description": "Comprehensive system-wide scan of all accessible directories",
  "targets": ["/"],
  "exclusions": {
    "paths": [
      "/proc",
      "/sys",
      "/dev",
      "/run",
      "/tmp",
      "/var/cache",
      "/var/tmp"
    ]
  },
  "options": {},
  "is_default": true
}
```

**Use Case:** Thorough system-wide malware check. Excludes system virtual filesystems and temporary directories that don't contain persistent threats. Best run periodically (weekly/monthly) or after system updates.

---

#### 3. Home Folder

**Purpose:** Scan of the user's home directory and personal files

**Configuration:**
```json
{
  "name": "Home Folder",
  "description": "Scan of the user's home directory and personal files",
  "targets": ["~"],
  "exclusions": {
    "paths": [
      "~/.cache",
      "~/.local/share/Trash"
    ]
  },
  "options": {},
  "is_default": true
}
```

**Use Case:** Focus on personal documents and files where threats are most likely to impact you. Excludes cache and trash directories. Balances thoroughness with scan time.

---

### Exclusion Formats

Understanding exclusion formats is important for creating effective scan profiles that skip unnecessary files while maintaining security.

#### Path Exclusions (`exclusions.paths`)

Path exclusions work by comparing the full resolved path of each file/directory:

1. **Exact Directory Match**
   ```json
   "paths": ["/var/cache"]
   ```
   - Excludes `/var/cache` and all its contents
   - Does NOT exclude `/var/cache2` or `/var/cache_old`

2. **Home Directory Expansion**
   ```json
   "paths": ["~/.cache"]
   ```
   - Expands to `/home/username/.cache` at scan time
   - Automatically adapts to the current user

3. **Multiple Paths**
   ```json
   "paths": [
     "~/Downloads/archives",
     "~/.local/share/virtualenvs",
     "/opt/backups"
   ]
   ```
   - All specified paths and their contents are excluded

4. **Subdirectory Behavior**
   - If you exclude `/home/user/Documents`, all files and subdirectories within are automatically excluded
   - You don't need to specify both parent and child paths

#### Pattern Exclusions (`exclusions.patterns`)

Pattern exclusions use glob-style matching on filenames:

1. **File Extension Patterns**
   ```json
   "patterns": ["*.log", "*.tmp"]
   ```
   - Excludes all files ending in `.log` or `.tmp` regardless of location
   - Example matches: `system.log`, `/var/log/app.log`, `temp.tmp`

2. **Wildcard Patterns**
   ```json
   "patterns": ["*.iso", "*.img"]
   ```
   - Useful for excluding large disk images or backup files
   - Applies to filename only, not the full path

3. **Multiple Patterns**
   ```json
   "patterns": [
     "*.log",
     "*.tmp",
     "*.bak",
     "*~",
     "*.pyc"
   ]
   ```
   - Common exclusions for development and system files

#### Best Practices for Exclusions

**✅ DO:**
- Exclude cache directories (`.cache`, `Cache`)
- Exclude trash/recycle bins (`Trash`, `.local/share/Trash`)
- Exclude system virtual filesystems (`/proc`, `/sys`, `/dev`)
- Exclude large archives you've already verified (`.iso`, `.img`)
- Exclude build artifacts (`.pyc`, `.o`, `__pycache__`)

**❌ DON'T:**
- Exclude your entire home directory (defeats the purpose)
- Exclude download folders (high-risk areas)
- Exclude document folders without good reason
- Over-exclude to save time (modern scans are fast)

**⚠️ WARNING:** If an exclusion path would exclude ALL target paths, ClamUI will warn you but still allow the configuration. For example:
```json
{
  "targets": ["~/Documents"],
  "exclusions": {
    "paths": ["~"]
  }
}
```
This profile would scan nothing because `~` (home directory) excludes `~/Documents`.

---

### Complete Profile Example

Here's a complete custom profile for scanning a development workspace:

```json
{
  "id": "a1b2c3d4-e5f6-4789-a012-b3c4d5e6f7a8",
  "name": "Dev Projects",
  "description": "Scan development projects excluding build artifacts and dependencies",
  "targets": [
    "~/projects",
    "~/workspace"
  ],
  "exclusions": {
    "paths": [
      "~/projects/node_modules",
      "~/projects/.venv",
      "~/projects/venv",
      "~/workspace/.git",
      "~/workspace/build",
      "~/workspace/dist"
    ],
    "patterns": [
      "*.pyc",
      "*.log",
      "*.tmp",
      "*.swp",
      "*~",
      ".DS_Store"
    ]
  },
  "created_at": "2024-01-15T10:30:45.123456+00:00",
  "updated_at": "2024-01-15T10:30:45.123456+00:00",
  "is_default": false,
  "options": {}
}
```

This profile:
- Scans two development directories
- Excludes dependency folders (node_modules, virtual environments)
- Excludes build output directories
- Excludes common temporary and system files
- Focuses scanning on actual source code where threats matter

---

## Configuration Examples

Below are complete configuration examples for common use cases.

### Example 1: Minimal/Silent Operation

For users who want ClamUI to run quietly in the background without notifications or tray integration:

```json
{
  "notifications_enabled": false,
  "minimize_to_tray": false,
  "start_minimized": false,
  "quarantine_directory": "",
  "scheduled_scans_enabled": false,
  "schedule_frequency": "weekly",
  "schedule_time": "02:00",
  "schedule_targets": [],
  "schedule_skip_on_battery": true,
  "schedule_auto_quarantine": false,
  "schedule_day_of_week": 0,
  "schedule_day_of_month": 1,
  "exclusion_patterns": [],
  "scan_backend": "auto",
  "daemon_socket_path": ""
}
```

---

### Example 2: Daily Scheduled Scans with Auto-Quarantine

For automated protection with daily scans of important directories:

```json
{
  "notifications_enabled": true,
  "minimize_to_tray": true,
  "start_minimized": true,
  "quarantine_directory": "",
  "scheduled_scans_enabled": true,
  "schedule_frequency": "daily",
  "schedule_time": "03:00",
  "schedule_targets": [
    "/home/username/Documents",
    "/home/username/Downloads",
    "/home/username/Desktop"
  ],
  "schedule_skip_on_battery": true,
  "schedule_auto_quarantine": true,
  "schedule_day_of_week": 0,
  "schedule_day_of_month": 1,
  "exclusion_patterns": [
    "/home/username/.cache",
    "/home/username/.local/share/Trash",
    "*.iso"
  ],
  "scan_backend": "daemon",
  "daemon_socket_path": ""
}
```

---

### Example 3: Using Daemon Backend with Custom Socket

For systems with custom clamd configurations:

```json
{
  "notifications_enabled": true,
  "minimize_to_tray": false,
  "start_minimized": false,
  "quarantine_directory": "",
  "scheduled_scans_enabled": false,
  "schedule_frequency": "weekly",
  "schedule_time": "02:00",
  "schedule_targets": [],
  "schedule_skip_on_battery": true,
  "schedule_auto_quarantine": false,
  "schedule_day_of_week": 0,
  "schedule_day_of_month": 1,
  "exclusion_patterns": [],
  "scan_backend": "daemon",
  "daemon_socket_path": "/custom/path/to/clamd.sock"
}
```

---

### Example 4: Enterprise Deployment (Pre-configured)

For deploying ClamUI with centralized quarantine and weekly full system scans:

```json
{
  "notifications_enabled": true,
  "minimize_to_tray": true,
  "start_minimized": true,
  "quarantine_directory": "/opt/clamui/quarantine",
  "scheduled_scans_enabled": true,
  "schedule_frequency": "weekly",
  "schedule_time": "02:00",
  "schedule_targets": [
    "/home",
    "/opt",
    "/var/www"
  ],
  "schedule_skip_on_battery": false,
  "schedule_auto_quarantine": true,
  "schedule_day_of_week": 6,
  "schedule_day_of_month": 1,
  "exclusion_patterns": [
    "/home/*/.cache",
    "/home/*/.local/share/Trash",
    "/var/log",
    "*.bak",
    "*.tmp"
  ],
  "scan_backend": "daemon",
  "daemon_socket_path": ""
}
```

---

## See Also

- [Installation Guide](INSTALL.md) - Installation instructions and system setup
- [Development Guide](DEVELOPMENT.md) - Contributing to ClamUI development
- [README](../README.md) - Project overview and quick start

---

**Note:** All paths in this document use standard Unix home directory notation (`~`). Actual paths will be expanded based on the current user's home directory and XDG environment variables.
