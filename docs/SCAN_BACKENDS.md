# ClamUI Scan Backend Options

This document explains the three scan backend options available in ClamUI and helps you choose the right one for your use case.

## Table of Contents

1. [Overview](#overview)
2. [Scan Backend Options](#scan-backend-options)
   - [Auto Mode (Recommended)](#auto-mode-recommended)
   - [Daemon Backend](#daemon-backend)
   - [Clamscan Backend](#clamscan-backend)
3. [Performance Comparison](#performance-comparison)
4. [How to Choose](#how-to-choose)
5. [Setup & Configuration](#setup--configuration)
6. [Troubleshooting](#troubleshooting)
7. [Technical Details](#technical-details)

---

## Overview

ClamUI supports three different scan backends for running ClamAV virus scans. Each backend has different performance characteristics and requirements:

- **Auto Mode**: Intelligently chooses the best available backend (recommended for most users)
- **Daemon Backend**: Uses the ClamAV daemon (clamd) for fast scanning with in-memory database
- **Clamscan Backend**: Uses the standalone clamscan command-line tool

### What is a Scan Backend?

A scan backend determines how ClamUI communicates with ClamAV to perform virus scans. The choice of backend affects:

- **Scan Speed**: How quickly scans complete, especially scan startup time
- **Memory Usage**: How much RAM is consumed during scanning
- **Setup Requirements**: Whether you need to configure additional services
- **Availability**: Whether the backend works in all situations

### Default Configuration

By default, ClamUI uses **Auto Mode**, which automatically selects the daemon backend if available and falls back to clamscan otherwise. This provides the best experience for most users without requiring manual configuration.

You can change the scan backend in **Preferences → General Settings → Scan Backend**.

---

## Scan Backend Options

### Auto Mode (Recommended)

**Description**: Automatically detects and uses the best available backend.

**How It Works**:
1. First checks if the ClamAV daemon (clamd) is running and accessible
2. If daemon is available, uses it for faster scanning
3. If daemon is not available, automatically falls back to clamscan
4. Decision is made at scan time, adapting to current system state

**Advantages**:
- ✅ No manual configuration needed
- ✅ Automatically gets performance benefits of daemon when available
- ✅ Gracefully degrades to clamscan when daemon is unavailable
- ✅ Best choice for most users and use cases

**Disadvantages**:
- ⚠️ Backend selection is automatic - no manual control
- ⚠️ Performance may vary if daemon availability changes

**When to Use**:
- Default choice for most users
- When you want the best performance without manual setup
- When daemon availability may change over time
- Desktop installations where convenience matters

---

### Daemon Backend

**Description**: Uses the ClamAV daemon (clamd) exclusively for all scanning operations.

**How It Works**:
- Communicates with the clamd background service via `clamdscan` command
- The daemon runs continuously as a system service (systemd or init.d)
- Keeps the entire virus database loaded in memory at all times for instant access
- Each scan reuses the pre-loaded database without any reload time
- Supports advanced features like parallel scanning (`--multiscan`) and file descriptor passing (`--fdpass`)
- Daemon automatically reloads database when freshclam updates signatures

**Advantages**:
- ✅ **Instant scan startup**: Database is already loaded in memory, eliminating 3-10 second load time
- ✅ **Superior performance for frequent scans**: No database reload between consecutive scans
- ✅ **Parallel scanning support**: Can scan multiple files simultaneously with `--multiscan` flag, utilizing all CPU cores
- ✅ **Lower per-scan overhead**: Daemon process stays resident, avoiding process creation/teardown costs
- ✅ **Advanced optimizations**: Supports `--fdpass` for improved performance on large files by passing file descriptors
- ✅ **Consistent performance**: Predictable scan times without database loading variability
- ✅ **Ideal for automation**: Perfect for scheduled scans, real-time monitoring, and server deployments
- ✅ **Efficient for batch operations**: Scanning multiple locations in sequence is much faster

**Disadvantages**:
- ❌ **Requires clamd to be running**: Scans fail completely if daemon is not available or crashes
- ❌ **Additional setup required**: Must install `clamav-daemon` package and configure systemd service
- ❌ **Higher baseline memory usage**: Daemon keeps database in RAM constantly (typically 500MB-1GB idle)
- ❌ **Service management overhead**: Must ensure daemon starts on boot, stays running, and restarts after crashes
- ❌ **Dependency on system service**: Requires root/sudo access for initial setup and configuration
- ❌ **Socket permission issues**: Can encounter permission problems with daemon socket access
- ❌ **Distribution-specific configuration**: Socket paths and service names vary across Linux distributions

**When to Use**:
- **Frequent or scheduled scans**: Running daily, hourly, or on-demand scans multiple times per day
- **Performance-critical environments**: When scan speed and responsiveness are paramount
- **Server deployments**: Mail servers, file servers, web servers with always-on scanning requirements
- **Real-time monitoring**: Systems that need continuous or near-continuous scanning capability
- **Maximum scan throughput**: When you need to scan large volumes of files as quickly as possible
- **Systems with clamd already configured**: Mail servers (Postfix/Exim), file sharing servers, or any system already using clamd
- **Development/testing environments**: Where repeated scanning of the same codebase is common
- **Dedicated security appliances**: Systems whose primary purpose is malware scanning

**Setup Requirements**:
See [Daemon Setup Instructions](#daemon-setup) below.

---

### Clamscan Backend

**Description**: Uses the standalone `clamscan` command-line tool directly without requiring any background services.

**How It Works**:
- Executes the `clamscan` command as a separate process for each scan operation
- Loads the entire virus database from disk at the start of every scan
- Scans files using the loaded database, then reports results
- Process terminates after completing the scan, freeing all resources
- No background services or daemons required - completely self-contained

**Advantages**:
- ✅ **No daemon required**: Works out-of-the-box with basic ClamAV installation
- ✅ **Simpler setup**: Just requires `clamscan` command to be installed (part of standard ClamAV package)
- ✅ **Lower baseline memory usage**: No resident daemon consuming RAM (~50MB idle vs 500MB-1GB for daemon)
- ✅ **Guaranteed to work**: Most reliable fallback option - works on any system with ClamAV installed
- ✅ **Easier troubleshooting**: Simpler architecture with fewer moving parts and dependencies
- ✅ **Maximum compatibility**: Works in restricted environments where daemon services cannot run
- ✅ **Clean resource usage**: Memory is freed immediately after each scan completes
- ✅ **No service management**: No need to worry about daemon crashes, restarts, or startup configuration

**Disadvantages**:
- ❌ **Slower startup time**: Must load database from disk for every scan (typically 3-10 seconds depending on disk speed)
- ❌ **Higher disk I/O**: Reads entire virus database (200-400MB) from disk each scan, increasing wear on storage
- ❌ **No parallel scanning**: Scans files sequentially, cannot take advantage of multi-core processors for scanning
- ❌ **Repeated overhead**: Database loading time is repeated for each scan operation, even consecutive scans
- ❌ **Higher total memory during scan**: Loads fresh database copy each time (500MB-1GB during scan)
- ❌ **Cache unfriendly**: Cannot benefit from filesystem cache as effectively as daemon for frequent scans

**When to Use**:
- **Infrequent, one-off scans**: When you only scan occasionally (weekly or less)
- **Systems where daemon setup is not feasible**: Embedded systems, minimal containers, or restricted environments
- **Testing or troubleshooting**: When debugging ClamAV issues or verifying scan behavior without daemon complexity
- **Minimal installations**: When memory is constrained and you can't afford 500MB-1GB for a resident daemon
- **Fallback scenario**: When daemon becomes unavailable or has configuration issues
- **Portable installations**: USB-based or portable ClamAV installations without system service access
- **Shared/multi-user systems**: Where you don't have permissions to configure system services
- **Battery-conscious mobile setups**: Laptops where you want to minimize background processes when not actively scanning

---

## Performance Comparison

| Aspect | Auto Mode | Daemon Backend | Clamscan Backend |
|--------|-----------|----------------|------------------|
| **First Scan Startup** | 3-10 sec* | <1 sec | 3-10 sec |
| **Subsequent Scans** | 3-10 sec* | <1 sec | 3-10 sec |
| **Scan Speed** | Fast* | Fast | Fast |
| **Memory Usage (Baseline)** | Variable | 500MB-1GB | ~50MB |
| **Memory Usage (During Scan)** | Variable | 500MB-1GB | 500MB-1GB |
| **Setup Complexity** | None | Moderate | None |
| **Reliability** | High | Medium** | High |

*Auto mode performance matches daemon if available, otherwise matches clamscan
**Daemon reliability depends on clamd service being properly configured and running

### Real-World Performance Examples

**Scanning a 1GB directory with 1000 files**:
- **Daemon**: 30 seconds total (instant startup + 30 sec scan)
- **Clamscan**: 40 seconds total (10 sec database load + 30 sec scan)
- **Improvement**: Daemon is ~25% faster, more noticeable with multiple scans

**Running 5 consecutive scans**:
- **Daemon**: 150 seconds total (5× 30 sec scans)
- **Clamscan**: 200 seconds total (5× 40 sec scans including startup)
- **Improvement**: Daemon saves 50 seconds over 5 scans

---

## How to Choose

Use this decision tree to select the best backend:

```
Do you run scans frequently (multiple times per day)?
  ├─ YES → Use Daemon Backend (after setup)
  └─ NO → Continue...

Is clamd already installed and running on your system?
  ├─ YES → Use Auto Mode (will use daemon automatically)
  └─ NO → Continue...

Are you willing to set up and maintain clamd daemon?
  ├─ YES → Use Daemon Backend (see setup instructions)
  └─ NO → Continue...

Do you only scan occasionally?
  ├─ YES → Use Auto Mode or Clamscan Backend
  └─ NO → Use Auto Mode (recommended default)
```

### Quick Recommendations

| Use Case | Recommended Backend | Rationale |
|----------|-------------------|-----------|
| Desktop user, occasional scans | Auto Mode | Best default, adapts automatically |
| Desktop user, daily scheduled scans | Daemon Backend | Worth the setup for better performance |
| Server with mail scanning | Daemon Backend | Likely already has clamd configured |
| Minimal installation / embedded | Clamscan Backend | Lower resource footprint |
| Testing / troubleshooting | Clamscan Backend | Simpler, fewer dependencies |
| Not sure | Auto Mode | Safe default that adapts to your system |

---

## Setup & Configuration

### Changing the Scan Backend

1. Open ClamUI
2. Click the menu button (≡) and select **Preferences**
3. Navigate to **General Settings**
4. Find **Scan Backend** dropdown
5. Select your preferred backend: Auto, Daemon, or Clamscan
6. Close preferences - changes take effect immediately

### Daemon Setup

To use the daemon backend, you need to install and configure clamd:

#### Ubuntu/Debian

```bash
# Install ClamAV daemon
sudo apt install clamav-daemon

# Enable and start the daemon service
sudo systemctl enable clamav-daemon
sudo systemctl start clamav-daemon

# Verify daemon is running
sudo systemctl status clamav-daemon

# Test daemon connection
clamdscan --version
```

#### Fedora

```bash
# Install ClamAV daemon
sudo dnf install clamd

# Enable and start the daemon service (note: service name may be clamd@scan)
sudo systemctl enable clamd@scan
sudo systemctl start clamd@scan

# Verify daemon is running
sudo systemctl status clamd@scan

# Test daemon connection
clamdscan --version
```

#### Arch Linux

```bash
# Install ClamAV (includes daemon)
sudo pacman -S clamav

# Enable and start the daemon service
sudo systemctl enable clamav-daemon
sudo systemctl start clamav-daemon

# Verify daemon is running
sudo systemctl status clamav-daemon

# Test daemon connection
clamdscan --version
```

#### Flatpak Users

If you're running ClamUI as a Flatpak, the daemon must be installed on the **host system** (not inside Flatpak). Follow the instructions above for your distribution, then ClamUI will automatically detect and use the host system's clamd daemon.

---

## Troubleshooting

### Checking Which Backend is Active

To see which backend ClamUI is currently using:

1. Run a scan with any file/folder
2. Check the scan results or logs - backend information is displayed
3. Alternatively, check Components View for daemon status

### Common Issues

#### "Daemon not available" error when using daemon backend

**Symptoms**: Scans fail with "clamd not accessible" message.

**Solutions**:
1. Verify clamd is installed: `which clamdscan`
2. Check daemon is running: `sudo systemctl status clamav-daemon`
3. Check daemon socket exists: `ls -l /var/run/clamav/clamd.ctl` (location may vary)
4. Review daemon logs: `sudo journalctl -u clamav-daemon`
5. Try manual connection: `clamdscan --version`
6. Switch to Auto or Clamscan mode as temporary workaround

#### Slow scan startup with auto/clamscan mode

**Symptoms**: 5-10 second delay before scan begins showing progress.

**Explanation**: This is normal - clamscan must load the virus database from disk (typically 200-400MB). This is not a bug.

**Solutions**:
- Switch to daemon backend for instant startup
- Use auto mode and set up clamd to get automatic fast scanning
- Accept the delay as normal for clamscan backend

#### Daemon uses too much memory

**Symptoms**: clamd process consuming 500MB-1GB RAM constantly.

**Explanation**: This is normal - the daemon keeps the entire virus database loaded in memory for fast scanning. This is the trade-off for performance.

**Solutions**:
- Switch to clamscan backend if memory is more important than speed
- Use auto mode and only run clamd when needed
- Configure clamd to use on-access scanning limits if available

#### Auto mode not using daemon

**Symptoms**: Auto mode always falls back to clamscan even though clamd is installed.

**Solutions**:
1. Verify daemon is actually running: `sudo systemctl status clamav-daemon`
2. Test manual connection: `clamdscan --version`
3. Check socket permissions (clamd socket must be readable)
4. Review ClamUI logs for connection errors
5. Try explicitly selecting daemon backend to see specific error

### Getting Help

If you encounter issues not covered here:

1. Check ClamUI logs in **Preferences → Logs View**
2. Check system logs: `sudo journalctl -u clamav-daemon`
3. Verify ClamAV installation: `clamscan --version` and `clamdscan --version`
4. File an issue on GitHub: https://github.com/rooki/clamui/issues

---

## Technical Details

### Backend Selection Algorithm (Auto Mode)

When using auto mode, ClamUI determines the backend at scan time:

1. Check if `clamdscan` command is available on the system
2. Attempt to connect to clamd socket (typically `/var/run/clamav/clamd.ctl`)
3. If connection succeeds: Use daemon backend
4. If connection fails: Fall back to clamscan backend

This check happens before each scan, so auto mode adapts if daemon becomes available or unavailable.

### Exit Codes

Both backends return the same ClamAV exit codes:

- **0**: No virus found (clean)
- **1**: Virus found (infected)
- **2**: Error occurred during scanning

ClamUI interprets these codes consistently across all backends.

### Command-Line Examples

**Clamscan Backend** executes commands like:
```bash
clamscan --recursive --infected --no-summary /path/to/scan
```

**Daemon Backend** executes commands like:
```bash
clamdscan --multiscan --infected --no-summary /path/to/scan
```

Note the different command names and options available.

### Exclusion Patterns

Both backends support exclusion patterns configured in ClamUI preferences. ClamUI filters excluded files before passing paths to ClamAV, ensuring consistent behavior across backends.

### Daemon Socket Locations

Clamd socket location varies by distribution:

- Ubuntu/Debian: `/var/run/clamav/clamd.ctl`
- Fedora: `/var/run/clamd.scan/clamd.sock`
- Arch: `/var/lib/clamav/clamd.socket`
- Custom: Check `/etc/clamav/clamd.conf` for `LocalSocket` setting

ClamUI automatically detects the socket location using ClamAV's configuration.

---

## Additional Resources

- [ClamAV Official Documentation](https://docs.clamav.net/)
- [ClamAV Daemon Configuration](https://docs.clamav.net/manual/Usage/Configuration.html)
- [ClamUI Installation Guide](./INSTALL.md)
- [ClamUI Development Guide](./DEVELOPMENT.md)
- [ClamUI GitHub Repository](https://github.com/rooki/clamui)

---

*Last updated: January 2026*
