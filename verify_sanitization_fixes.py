#!/usr/bin/env python3
"""Quick verification script for the three sanitization fixes."""

import sys
sys.path.insert(0, './src')

from core.sanitize import sanitize_log_line, sanitize_log_text
from core.log_manager import LogEntry

def test_fix_1_newline_count():
    """Verify fix 1: Correct newline count in real-world scan output."""
    scan_output = """/home/user/Downloads/file1.txt: OK
/home/user/Downloads/malware.exe: Win.Trojan.Agent FOUND
/home/user/Downloads/file2.doc: OK

----------- SCAN SUMMARY -----------
Infected files: 1
Time: 5.234 sec"""

    result = sanitize_log_text(scan_output)
    newline_count = result.count("\n")

    print(f"Fix 1 - Newline count test:")
    print(f"  Expected: 6 newlines")
    print(f"  Got: {newline_count} newlines")
    print(f"  Status: {'✅ PASS' if newline_count == 6 else '❌ FAIL'}")
    return newline_count == 6

def test_fix_2_ansi_pattern():
    """Verify fix 2: ANSI pattern handles ? prefix."""
    test_string = "Show\x1b[?25hcursor"
    result = sanitize_log_line(test_string)

    print(f"\nFix 2 - ANSI escape pattern test:")
    print(f"  Input: {repr(test_string)}")
    print(f"  Output: {repr(result)}")
    print(f"  Expected: 'Showcursor'")
    print(f"  Status: {'✅ PASS' if result == 'Showcursor' else '❌ FAIL'}")
    return result == "Showcursor"

def test_fix_3_type_sanitization():
    """Verify fix 3: type field is sanitized in from_dict()."""
    malicious_data = {
        "id": "test-123",
        "timestamp": "2024-01-01T00:00:00",
        "type": "scan\x00malicious",
        "status": "clean",
        "summary": "Test",
        "details": "Test details",
        "path": None,
        "duration": 1.0,
        "scheduled": False,
    }

    entry = LogEntry.from_dict(malicious_data)
    has_null = "\x00" in entry.type

    print(f"\nFix 3 - Type field sanitization test:")
    print(f"  Input type: {repr(malicious_data['type'])}")
    print(f"  Output type: {repr(entry.type)}")
    print(f"  Contains null byte: {has_null}")
    print(f"  Status: {'✅ PASS' if not has_null else '❌ FAIL'}")
    return not has_null

if __name__ == "__main__":
    print("=" * 60)
    print("Sanitization Fixes Verification")
    print("=" * 60)

    results = []
    results.append(test_fix_1_newline_count())
    results.append(test_fix_2_ansi_pattern())
    results.append(test_fix_3_type_sanitization())

    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/3 tests passed")

    if all(results):
        print("✅ All sanitization fixes verified!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
