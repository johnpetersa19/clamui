# ClamUI Tray Indicator Module
"""
Tray indicator module for ClamUI providing system tray integration.

This module provides availability checks and utility functions for the tray
system. The actual tray functionality is implemented via GTK3 AppIndicator
in tray_service.py (subprocess) and managed by tray_manager.py.

The subprocess architecture isolates GTK3 from the main GTK4 application,
allowing us to use AppIndicator (which requires GTK3) without conflicts.
"""

import logging

logger = logging.getLogger(__name__)


def is_available() -> bool:
    """
    Check if the tray indicator functionality is available.

    The tray uses AppIndicator via a subprocess, so it's available
    as long as the subprocess can be started. The actual availability
    of AppIndicator is checked when the subprocess starts.

    Returns:
        True (availability is checked when subprocess starts)
    """
    return True


def get_unavailable_reason() -> str | None:
    """
    Get the reason why tray indicator is unavailable.

    Returns:
        None (actual errors are reported by the subprocess)
    """
    return None
