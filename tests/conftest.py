# ClamUI Test Configuration
"""
Pytest configuration and shared fixtures for ClamUI tests.

This file provides common test configuration. GTK/GI mocking is handled
by individual test files as needed since different tests require different
mocking strategies.
"""

import os
import tempfile
from pathlib import Path

import pytest


# EICAR standard test string - recognized by antivirus software as a test file
# This string MUST be exact (any modification breaks detection)
# See: https://www.eicar.org/download-anti-malware-testfile/
EICAR_STRING = r"X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"


@pytest.fixture
def eicar_file(tmp_path: Path) -> Path:
    """
    Create a temporary EICAR test file for antivirus testing.

    The EICAR test file is a standard test file used to verify antivirus
    detection without using real malware. ClamAV classifies EICAR as:
    - Category: "Test"
    - Severity: "low"

    The file is automatically cleaned up after the test completes.

    Args:
        tmp_path: pytest's built-in temporary directory fixture

    Yields:
        Path: Path to the temporary EICAR test file
    """
    eicar_path = tmp_path / "eicar_test_file.txt"
    try:
        eicar_path.write_text(EICAR_STRING)
        yield eicar_path
    finally:
        # Ensure cleanup even if test fails
        if eicar_path.exists():
            eicar_path.unlink()


@pytest.fixture
def eicar_directory(tmp_path: Path) -> Path:
    """
    Create a temporary directory containing an EICAR test file.

    Useful for testing directory scanning with infected files.
    The directory structure is:
        tmp_path/
            eicar_dir/
                eicar_test_file.txt (EICAR content)
                clean_file.txt (clean content)

    Args:
        tmp_path: pytest's built-in temporary directory fixture

    Yields:
        Path: Path to the temporary directory containing test files
    """
    eicar_dir = tmp_path / "eicar_dir"
    eicar_dir.mkdir()
    eicar_file_path = eicar_dir / "eicar_test_file.txt"
    clean_file_path = eicar_dir / "clean_file.txt"

    try:
        eicar_file_path.write_text(EICAR_STRING)
        clean_file_path.write_text("This is a clean file with no threats.")
        yield eicar_dir
    finally:
        # Ensure cleanup even if test fails
        if eicar_file_path.exists():
            eicar_file_path.unlink()
        if clean_file_path.exists():
            clean_file_path.unlink()
        if eicar_dir.exists():
            eicar_dir.rmdir()


@pytest.fixture
def clean_test_file(tmp_path: Path) -> Path:
    """
    Create a temporary clean test file for scanning.

    Useful for testing clean scan results.

    Args:
        tmp_path: pytest's built-in temporary directory fixture

    Yields:
        Path: Path to the temporary clean test file
    """
    clean_path = tmp_path / "clean_test_file.txt"
    try:
        clean_path.write_text("This is a clean file with no malicious content.")
        yield clean_path
    finally:
        if clean_path.exists():
            clean_path.unlink()
