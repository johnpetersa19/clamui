# ClamUI StatisticsCalculator Tests
"""Unit tests for the StatisticsCalculator class and caching functionality."""

import time
from datetime import datetime, timedelta
from unittest import mock

import pytest

from src.core.log_manager import LogEntry
from src.core.statistics_calculator import (
    ProtectionLevel,
    ProtectionStatus,
    ScanStatistics,
    StatisticsCalculator,
    Timeframe,
)


@pytest.fixture
def mock_log_manager():
    """
    Create a mock LogManager for testing.

    Returns a MagicMock configured with:
    - get_logs method that returns sample scan log entries
    - Tracking of call count to verify caching behavior
    """
    log_manager = mock.MagicMock()

    # Create sample log entries with different timestamps and statuses
    sample_logs = [
        LogEntry(
            id="log-1",
            timestamp="2024-01-15T10:00:00",
            type="scan",
            status="clean",
            summary="Scanned 100 files - No threats found",
            details="Scan complete",
            path="/home/user/documents",
            duration=60.0,
            scheduled=False,
        ),
        LogEntry(
            id="log-2",
            timestamp="2024-01-14T14:30:00",
            type="scan",
            status="infected",
            summary="Found 2 threats in 50 files",
            details="Infected files detected",
            path="/home/user/downloads",
            duration=45.5,
            scheduled=True,
        ),
        LogEntry(
            id="log-3",
            timestamp="2024-01-13T09:15:00",
            type="scan",
            status="clean",
            summary="Scanned 200 files - No threats found",
            details="Scan complete",
            path="/home/user",
            duration=120.0,
            scheduled=False,
        ),
        LogEntry(
            id="log-4",
            timestamp="2024-01-12T16:45:00",
            type="scan",
            status="error",
            summary="Scan failed - Permission denied",
            details="Error during scan",
            path="/root",
            duration=5.0,
            scheduled=False,
        ),
    ]

    # Configure get_logs to return sample logs
    log_manager.get_logs.return_value = sample_logs

    return log_manager


@pytest.fixture
def statistics_calculator(mock_log_manager):
    """
    Create a StatisticsCalculator instance with a mock LogManager.

    Args:
        mock_log_manager: The mock LogManager fixture

    Returns:
        StatisticsCalculator instance configured for testing
    """
    return StatisticsCalculator(log_manager=mock_log_manager)


@pytest.fixture
def empty_log_manager():
    """
    Create a mock LogManager that returns no logs.

    Useful for testing edge cases with no scan history.
    """
    log_manager = mock.MagicMock()
    log_manager.get_logs.return_value = []
    return log_manager


@pytest.fixture
def large_log_dataset():
    """
    Create a large dataset of log entries for testing performance and caching.

    Returns a list of LogEntry objects spanning multiple days with varied statuses.
    """
    logs = []
    base_time = datetime(2024, 1, 1, 10, 0, 0)

    for i in range(100):
        timestamp = base_time + timedelta(hours=i)
        status = ["clean", "infected", "clean", "clean"][i % 4]  # 75% clean, 25% infected
        logs.append(
            LogEntry(
                id=f"log-{i}",
                timestamp=timestamp.isoformat(),
                type="scan",
                status=status,
                summary=f"Scanned {10 * (i + 1)} files",
                details=f"Details for scan {i}",
                path=f"/test/path/{i}",
                duration=float(30 + (i % 10)),
                scheduled=(i % 2 == 0),  # Alternating scheduled/manual
            )
        )

    return logs


class TestTimeframe:
    """Tests for the Timeframe enum."""

    def test_timeframe_values(self):
        """Test Timeframe enum has expected values."""
        assert Timeframe.DAILY.value == "daily"
        assert Timeframe.WEEKLY.value == "weekly"
        assert Timeframe.MONTHLY.value == "monthly"
        assert Timeframe.ALL.value == "all"


class TestProtectionLevel:
    """Tests for the ProtectionLevel enum."""

    def test_protection_level_values(self):
        """Test ProtectionLevel enum has expected values."""
        assert ProtectionLevel.PROTECTED.value == "protected"
        assert ProtectionLevel.AT_RISK.value == "at_risk"
        assert ProtectionLevel.UNPROTECTED.value == "unprotected"
        assert ProtectionLevel.UNKNOWN.value == "unknown"


class TestScanStatistics:
    """Tests for the ScanStatistics dataclass."""

    def test_scan_statistics_creation(self):
        """Test creating a ScanStatistics instance."""
        stats = ScanStatistics(
            timeframe="daily",
            total_scans=10,
            files_scanned=1000,
            threats_detected=2,
            clean_scans=8,
            infected_scans=1,
            error_scans=1,
            average_duration=60.5,
            total_duration=605.0,
            scheduled_scans=5,
            manual_scans=5,
            start_date="2024-01-01T00:00:00",
            end_date="2024-01-02T00:00:00",
        )

        assert stats.timeframe == "daily"
        assert stats.total_scans == 10
        assert stats.files_scanned == 1000
        assert stats.threats_detected == 2
        assert stats.clean_scans == 8
        assert stats.infected_scans == 1
        assert stats.error_scans == 1
        assert stats.average_duration == 60.5
        assert stats.total_duration == 605.0
        assert stats.scheduled_scans == 5
        assert stats.manual_scans == 5

    def test_scan_statistics_to_dict(self):
        """Test ScanStatistics.to_dict serialization."""
        stats = ScanStatistics(
            timeframe="weekly",
            total_scans=5,
            files_scanned=500,
            threats_detected=1,
            clean_scans=4,
            infected_scans=1,
            error_scans=0,
            average_duration=45.0,
            total_duration=225.0,
            scheduled_scans=3,
            manual_scans=2,
        )

        data = stats.to_dict()

        assert data["timeframe"] == "weekly"
        assert data["total_scans"] == 5
        assert data["files_scanned"] == 500
        assert data["threats_detected"] == 1
        assert data["clean_scans"] == 4
        assert data["infected_scans"] == 1
        assert data["error_scans"] == 0
        assert data["average_duration"] == 45.0
        assert data["total_duration"] == 225.0
        assert data["scheduled_scans"] == 3
        assert data["manual_scans"] == 2


class TestProtectionStatus:
    """Tests for the ProtectionStatus dataclass."""

    def test_protection_status_creation(self):
        """Test creating a ProtectionStatus instance."""
        status = ProtectionStatus(
            level="protected",
            last_scan_timestamp="2024-01-15T10:00:00",
            last_scan_age_hours=2.5,
            last_definition_update="2024-01-15T08:00:00",
            definition_age_hours=4.5,
            message="System is protected",
            is_protected=True,
        )

        assert status.level == "protected"
        assert status.last_scan_timestamp == "2024-01-15T10:00:00"
        assert status.last_scan_age_hours == 2.5
        assert status.last_definition_update == "2024-01-15T08:00:00"
        assert status.definition_age_hours == 4.5
        assert status.message == "System is protected"
        assert status.is_protected is True

    def test_protection_status_to_dict(self):
        """Test ProtectionStatus.to_dict serialization."""
        status = ProtectionStatus(
            level="at_risk",
            last_scan_timestamp="2024-01-10T10:00:00",
            last_scan_age_hours=120.0,
            last_definition_update=None,
            definition_age_hours=None,
            message="Last scan was over a week ago",
            is_protected=False,
        )

        data = status.to_dict()

        assert data["level"] == "at_risk"
        assert data["last_scan_timestamp"] == "2024-01-10T10:00:00"
        assert data["last_scan_age_hours"] == 120.0
        assert data["last_definition_update"] is None
        assert data["definition_age_hours"] is None
        assert data["message"] == "Last scan was over a week ago"
        assert data["is_protected"] is False


class TestStatisticsCalculator:
    """Tests for the StatisticsCalculator class."""

    def test_init_with_log_manager(self, mock_log_manager):
        """Test StatisticsCalculator initialization with provided LogManager."""
        calculator = StatisticsCalculator(log_manager=mock_log_manager)
        assert calculator._log_manager is mock_log_manager

    def test_init_without_log_manager(self):
        """Test StatisticsCalculator initialization creates default LogManager."""
        calculator = StatisticsCalculator()
        assert calculator._log_manager is not None

    def test_cache_initialized(self, statistics_calculator):
        """Test that cache data structures are initialized."""
        assert hasattr(statistics_calculator, "_cache")
        assert hasattr(statistics_calculator, "_cache_timestamp")
        assert hasattr(statistics_calculator, "_lock")
        assert isinstance(statistics_calculator._cache, dict)
        assert statistics_calculator._cache_timestamp is None

    def test_cache_ttl_constant(self):
        """Test that CACHE_TTL_SECONDS constant is defined."""
        assert hasattr(StatisticsCalculator, "CACHE_TTL_SECONDS")
        assert StatisticsCalculator.CACHE_TTL_SECONDS == 30


class TestStatisticsCalculatorBasicFunctionality:
    """Tests for basic StatisticsCalculator functionality without caching focus."""

    def test_get_statistics_returns_scan_statistics(self, statistics_calculator):
        """Test that get_statistics returns a ScanStatistics object."""
        stats = statistics_calculator.get_statistics(timeframe="all")
        assert isinstance(stats, ScanStatistics)

    def test_get_statistics_with_empty_logs(self, empty_log_manager):
        """Test get_statistics with no log entries."""
        calculator = StatisticsCalculator(log_manager=empty_log_manager)
        stats = calculator.get_statistics(timeframe="all")

        assert stats.total_scans == 0
        assert stats.files_scanned == 0
        assert stats.threats_detected == 0
        assert stats.clean_scans == 0
        assert stats.infected_scans == 0
        assert stats.error_scans == 0
        assert stats.average_duration == 0.0

    def test_invalidate_cache_method_exists(self, statistics_calculator):
        """Test that invalidate_cache method exists and is callable."""
        assert hasattr(statistics_calculator, "invalidate_cache")
        assert callable(statistics_calculator.invalidate_cache)

    def test_get_scan_trend_data_returns_list(self, statistics_calculator):
        """Test that get_scan_trend_data returns a list of data points."""
        trend_data = statistics_calculator.get_scan_trend_data(timeframe="weekly", data_points=7)
        assert isinstance(trend_data, list)


class TestStatisticsCalculatorCacheHit:
    """Tests for cache hit behavior - verifying log_manager.get_logs() is only called once."""

    def test_get_statistics_caches_log_data(self, statistics_calculator, mock_log_manager):
        """Test that get_statistics caches log data for subsequent calls."""
        # First call should fetch from log_manager
        stats1 = statistics_calculator.get_statistics(timeframe="all")
        assert mock_log_manager.get_logs.call_count == 1

        # Second call should use cached data (no additional fetch)
        stats2 = statistics_calculator.get_statistics(timeframe="all")
        assert mock_log_manager.get_logs.call_count == 1  # Still 1, not 2

        # Both results should be the same (using same data)
        assert stats1.total_scans == stats2.total_scans
        assert stats1.threats_detected == stats2.threats_detected

    def test_get_scan_trend_data_caches_log_data(self, statistics_calculator, mock_log_manager):
        """Test that get_scan_trend_data caches log data for subsequent calls."""
        # First call should fetch from log_manager
        trend1 = statistics_calculator.get_scan_trend_data(timeframe="weekly", data_points=7)
        assert mock_log_manager.get_logs.call_count == 1

        # Second call should use cached data (no additional fetch)
        trend2 = statistics_calculator.get_scan_trend_data(timeframe="weekly", data_points=7)
        assert mock_log_manager.get_logs.call_count == 1  # Still 1, not 2

        # Both results should be the same
        assert len(trend1) == len(trend2)

    def test_get_statistics_then_get_scan_trend_data_shares_cache(
        self, statistics_calculator, mock_log_manager
    ):
        """
        Test that get_statistics() and get_scan_trend_data() share the same cache.

        This is the key test: when called in succession, log_manager.get_logs()
        should only be called once because both methods use the same cache key
        (limit=10000, log_type='scan').
        """
        # Reset call count to ensure clean state
        mock_log_manager.get_logs.reset_mock()

        # First call to get_statistics should fetch from log_manager
        stats = statistics_calculator.get_statistics(timeframe="all")
        assert mock_log_manager.get_logs.call_count == 1
        assert isinstance(stats, ScanStatistics)

        # Second call to get_scan_trend_data should use cached data (cache hit!)
        trend_data = statistics_calculator.get_scan_trend_data(timeframe="weekly", data_points=7)
        assert mock_log_manager.get_logs.call_count == 1  # Still 1 - cache hit!
        assert isinstance(trend_data, list)

    def test_get_scan_trend_data_then_get_statistics_shares_cache(
        self, statistics_calculator, mock_log_manager
    ):
        """
        Test cache sharing in reverse order (trend data first, then statistics).

        Verifies that the cache works bidirectionally - either method can
        populate the cache for the other.
        """
        # Reset call count to ensure clean state
        mock_log_manager.get_logs.reset_mock()

        # First call to get_scan_trend_data should fetch from log_manager
        trend_data = statistics_calculator.get_scan_trend_data(timeframe="weekly", data_points=7)
        assert mock_log_manager.get_logs.call_count == 1
        assert isinstance(trend_data, list)

        # Second call to get_statistics should use cached data (cache hit!)
        stats = statistics_calculator.get_statistics(timeframe="all")
        assert mock_log_manager.get_logs.call_count == 1  # Still 1 - cache hit!
        assert isinstance(stats, ScanStatistics)

    def test_multiple_successive_calls_all_use_cache(self, statistics_calculator, mock_log_manager):
        """Test that multiple successive calls all use the same cache."""
        # Reset call count
        mock_log_manager.get_logs.reset_mock()

        # First call
        statistics_calculator.get_statistics(timeframe="daily")
        assert mock_log_manager.get_logs.call_count == 1

        # Second call - different timeframe but uses cache
        statistics_calculator.get_statistics(timeframe="weekly")
        assert mock_log_manager.get_logs.call_count == 1

        # Third call - trend data also uses cache
        statistics_calculator.get_scan_trend_data(timeframe="monthly", data_points=4)
        assert mock_log_manager.get_logs.call_count == 1


class TestStatisticsCalculatorCacheExpiry:
    """Tests for cache expiry behavior - verifying cache invalidation after TTL."""

    def test_cache_expires_after_ttl(self, statistics_calculator, mock_log_manager):
        """Test that cache expires after CACHE_TTL_SECONDS."""
        # First call populates cache
        statistics_calculator.get_statistics(timeframe="all")
        assert mock_log_manager.get_logs.call_count == 1

        # Manually expire the cache by going back in time
        statistics_calculator._cache_timestamp = time.time() - 31  # 31 seconds ago

        # Next call should fetch again because cache expired
        statistics_calculator.get_statistics(timeframe="all")
        assert mock_log_manager.get_logs.call_count == 2

    def test_invalidate_cache_clears_all_data(self, statistics_calculator, mock_log_manager):
        """Test that invalidate_cache() clears the cache."""
        # Populate cache
        statistics_calculator.get_statistics(timeframe="all")
        assert mock_log_manager.get_logs.call_count == 1
        assert len(statistics_calculator._cache) > 0

        # Invalidate cache
        statistics_calculator.invalidate_cache()
        assert len(statistics_calculator._cache) == 0
        assert statistics_calculator._cache_timestamp is None

        # Next call should fetch again
        statistics_calculator.get_statistics(timeframe="all")
        assert mock_log_manager.get_logs.call_count == 2

    def test_cache_still_valid_before_expiry(self, statistics_calculator, mock_log_manager):
        """Test that cache is still valid before TTL expires."""
        # First call
        statistics_calculator.get_statistics(timeframe="all")
        assert mock_log_manager.get_logs.call_count == 1

        # Advance time by less than TTL
        statistics_calculator._cache_timestamp = time.time() - 15  # 15 seconds ago

        # Cache should still be valid
        statistics_calculator.get_statistics(timeframe="all")
        assert mock_log_manager.get_logs.call_count == 1  # No additional fetch


class TestStatisticsCalculatorCacheConcurrency:
    """Tests for thread safety of cache operations."""

    def test_cache_uses_lock_for_thread_safety(self, statistics_calculator):
        """Test that cache operations use a lock for thread safety."""
        assert hasattr(statistics_calculator, "_lock")
        import threading

        assert isinstance(statistics_calculator._lock, type(threading.Lock()))


class TestStatisticsCalculatorEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_get_statistics_with_different_timeframes(self, statistics_calculator):
        """Test get_statistics with different timeframe values."""
        for timeframe in ["daily", "weekly", "monthly", "all"]:
            stats = statistics_calculator.get_statistics(timeframe=timeframe)
            assert isinstance(stats, ScanStatistics)
            assert stats.timeframe == timeframe

    def test_get_scan_trend_data_with_different_data_points(self, statistics_calculator):
        """Test get_scan_trend_data with different data_points values."""
        for data_points in [1, 7, 30, 100]:
            trend_data = statistics_calculator.get_scan_trend_data(
                timeframe="daily", data_points=data_points
            )
            assert isinstance(trend_data, list)

    def test_large_dataset_performance(self, large_log_dataset):
        """Test StatisticsCalculator performance with large dataset."""
        log_manager = mock.MagicMock()
        log_manager.get_logs.return_value = large_log_dataset
        calculator = StatisticsCalculator(log_manager=log_manager)

        # Should complete without timeout
        stats = calculator.get_statistics(timeframe="all")
        assert isinstance(stats, ScanStatistics)
        assert stats.total_scans == 100

    def test_cache_with_large_dataset(self, large_log_dataset):
        """Test caching works correctly with large dataset."""
        log_manager = mock.MagicMock()
        log_manager.get_logs.return_value = large_log_dataset
        calculator = StatisticsCalculator(log_manager=log_manager)

        # First call
        stats1 = calculator.get_statistics(timeframe="all")
        assert log_manager.get_logs.call_count == 1

        # Second call should use cache
        stats2 = calculator.get_statistics(timeframe="all")
        assert log_manager.get_logs.call_count == 1
        assert stats1.total_scans == stats2.total_scans


class TestExtractDirectoriesScanned:
    """Tests for _extract_directories_scanned method."""

    def test_extract_directories_scanned_pattern_1(self, statistics_calculator):
        """Test extraction with '5 directories scanned' pattern."""
        entry = LogEntry(
            id="test-1",
            timestamp="2024-01-15T10:00:00",
            type="scan",
            status="clean",
            summary="Scan complete",
            details="Scanned: 100 files, 5 directories",
            path="/home/user",
            duration=30.0,
            scheduled=False,
        )
        result = statistics_calculator._extract_directories_scanned(entry)
        assert result == 5

    def test_extract_directories_scanned_pattern_2(self, statistics_calculator):
        """Test extraction with 'scanned 3 directories' pattern."""
        entry = LogEntry(
            id="test-2",
            timestamp="2024-01-15T10:00:00",
            type="scan",
            status="clean",
            summary="Scanned 3 directories successfully",
            details="Operation complete",
            path="/home/user",
            duration=30.0,
            scheduled=False,
        )
        result = statistics_calculator._extract_directories_scanned(entry)
        assert result == 3

    def test_extract_directories_scanned_pattern_3(self, statistics_calculator):
        """Test extraction with 'directories: 10' pattern."""
        entry = LogEntry(
            id="test-3",
            timestamp="2024-01-15T10:00:00",
            type="scan",
            status="clean",
            summary="Scan report",
            details="Files: 200, Directories: 10",
            path="/home/user",
            duration=30.0,
            scheduled=False,
        )
        result = statistics_calculator._extract_directories_scanned(entry)
        assert result == 10

    def test_extract_directories_scanned_pattern_4(self, statistics_calculator):
        """Test extraction with '20 directories' pattern."""
        entry = LogEntry(
            id="test-4",
            timestamp="2024-01-15T10:00:00",
            type="scan",
            status="clean",
            summary="20 directories processed",
            details="Scan completed successfully",
            path="/home/user",
            duration=30.0,
            scheduled=False,
        )
        result = statistics_calculator._extract_directories_scanned(entry)
        assert result == 20

    def test_extract_directories_scanned_case_insensitive(self, statistics_calculator):
        """Test extraction is case insensitive."""
        entry = LogEntry(
            id="test-5",
            timestamp="2024-01-15T10:00:00",
            type="scan",
            status="clean",
            summary="15 DIRECTORIES SCANNED",
            details="Operation complete",
            path="/home/user",
            duration=30.0,
            scheduled=False,
        )
        result = statistics_calculator._extract_directories_scanned(entry)
        assert result == 15

    def test_extract_directories_scanned_singular_form(self, statistics_calculator):
        """Test extraction with singular 'directory'."""
        entry = LogEntry(
            id="test-6",
            timestamp="2024-01-15T10:00:00",
            type="scan",
            status="clean",
            summary="1 directory scanned",
            details="Operation complete",
            path="/home/user",
            duration=30.0,
            scheduled=False,
        )
        result = statistics_calculator._extract_directories_scanned(entry)
        assert result == 1

    def test_extract_directories_scanned_not_found(self, statistics_calculator):
        """Test extraction returns 0 when no directory count found."""
        entry = LogEntry(
            id="test-7",
            timestamp="2024-01-15T10:00:00",
            type="scan",
            status="clean",
            summary="Scan complete",
            details="No directory information available",
            path="/home/user",
            duration=30.0,
            scheduled=False,
        )
        result = statistics_calculator._extract_directories_scanned(entry)
        assert result == 0

    def test_extract_directories_scanned_empty_details(self, statistics_calculator):
        """Test extraction with empty details."""
        entry = LogEntry(
            id="test-8",
            timestamp="2024-01-15T10:00:00",
            type="scan",
            status="clean",
            summary="",
            details="",
            path="/home/user",
            duration=30.0,
            scheduled=False,
        )
        result = statistics_calculator._extract_directories_scanned(entry)
        assert result == 0

    def test_extract_directories_scanned_large_number(self, statistics_calculator):
        """Test extraction with large directory count."""
        entry = LogEntry(
            id="test-9",
            timestamp="2024-01-15T10:00:00",
            type="scan",
            status="clean",
            summary="Scanned 9999 directories",
            details="Large scan operation",
            path="/home/user",
            duration=30.0,
            scheduled=False,
        )
        result = statistics_calculator._extract_directories_scanned(entry)
        assert result == 9999

    def test_extract_directories_scanned_zero_count(self, statistics_calculator):
        """Test extraction with zero directories."""
        entry = LogEntry(
            id="test-10",
            timestamp="2024-01-15T10:00:00",
            type="scan",
            status="clean",
            summary="0 directories scanned",
            details="File-only scan",
            path="/home/user/file.txt",
            duration=30.0,
            scheduled=False,
        )
        result = statistics_calculator._extract_directories_scanned(entry)
        assert result == 0

    def test_extract_directories_scanned_mixed_content(self, statistics_calculator):
        """Test extraction from mixed content with files and directories."""
        entry = LogEntry(
            id="test-11",
            timestamp="2024-01-15T10:00:00",
            type="scan",
            status="clean",
            summary="Scan complete",
            details="Scanned 250 files and 12 directories in /home/user",
            path="/home/user",
            duration=30.0,
            scheduled=False,
        )
        result = statistics_calculator._extract_directories_scanned(entry)
        assert result == 12

    def test_extract_directories_scanned_from_summary_only(self, statistics_calculator):
        """Test extraction when directory count is only in summary."""
        entry = LogEntry(
            id="test-12",
            timestamp="2024-01-15T10:00:00",
            type="scan",
            status="clean",
            summary="Processed 8 directories",
            details="",
            path="/home/user",
            duration=30.0,
            scheduled=False,
        )
        result = statistics_calculator._extract_directories_scanned(entry)
        assert result == 8

    def test_extract_directories_scanned_from_details_only(self, statistics_calculator):
        """Test extraction when directory count is only in details."""
        entry = LogEntry(
            id="test-13",
            timestamp="2024-01-15T10:00:00",
            type="scan",
            status="clean",
            summary="",
            details="Total directories scanned: 25",
            path="/home/user",
            duration=30.0,
            scheduled=False,
        )
        result = statistics_calculator._extract_directories_scanned(entry)
        assert result == 25


class TestExtractEntryStatistics:
    """Tests for extract_entry_statistics method."""

    def test_extract_entry_statistics_complete_data(self, statistics_calculator):
        """Test extraction with complete statistics data."""
        entry = LogEntry(
            id="test-1",
            timestamp="2024-01-15T10:00:00",
            type="scan",
            status="clean",
            summary="Scan complete",
            details="Scanned: 100 files, 5 directories",
            path="/home/user",
            duration=45.5,
            scheduled=False,
        )
        result = statistics_calculator.extract_entry_statistics(entry)

        assert isinstance(result, dict)
        assert "files_scanned" in result
        assert "directories_scanned" in result
        assert "duration" in result
        assert result["files_scanned"] == 100
        assert result["directories_scanned"] == 5
        assert result["duration"] == 45.5

    def test_extract_entry_statistics_partial_data(self, statistics_calculator):
        """Test extraction when only some statistics are available."""
        entry = LogEntry(
            id="test-2",
            timestamp="2024-01-15T10:00:00",
            type="scan",
            status="clean",
            summary="50 files scanned",
            details="No directory information",
            path="/home/user",
            duration=20.0,
            scheduled=False,
        )
        result = statistics_calculator.extract_entry_statistics(entry)

        assert result["files_scanned"] == 50
        assert result["directories_scanned"] == 0
        assert result["duration"] == 20.0

    def test_extract_entry_statistics_no_scan_data(self, statistics_calculator):
        """Test extraction when no scan statistics are found."""
        entry = LogEntry(
            id="test-3",
            timestamp="2024-01-15T10:00:00",
            type="scan",
            status="error",
            summary="Scan failed",
            details="Permission denied",
            path="/home/user",
            duration=1.5,
            scheduled=False,
        )
        result = statistics_calculator.extract_entry_statistics(entry)

        assert result["files_scanned"] == 0
        assert result["directories_scanned"] == 0
        assert result["duration"] == 1.5

    def test_extract_entry_statistics_zero_duration(self, statistics_calculator):
        """Test extraction with zero duration."""
        entry = LogEntry(
            id="test-4",
            timestamp="2024-01-15T10:00:00",
            type="scan",
            status="clean",
            summary="Quick scan: 10 files, 2 directories",
            details="Instant scan completed",
            path="/home/user/file.txt",
            duration=0.0,
            scheduled=False,
        )
        result = statistics_calculator.extract_entry_statistics(entry)

        assert result["files_scanned"] == 10
        assert result["directories_scanned"] == 2
        assert result["duration"] == 0.0

    def test_extract_entry_statistics_large_numbers(self, statistics_calculator):
        """Test extraction with large file and directory counts."""
        entry = LogEntry(
            id="test-5",
            timestamp="2024-01-15T10:00:00",
            type="scan",
            status="clean",
            summary="Large scan completed",
            details="Scanned 50000 files in 999 directories",
            path="/home",
            duration=3600.5,
            scheduled=True,
        )
        result = statistics_calculator.extract_entry_statistics(entry)

        assert result["files_scanned"] == 50000
        assert result["directories_scanned"] == 999
        assert result["duration"] == 3600.5

    def test_extract_entry_statistics_infected_scan(self, statistics_calculator):
        """Test extraction from infected scan log."""
        entry = LogEntry(
            id="test-6",
            timestamp="2024-01-15T10:00:00",
            type="scan",
            status="infected",
            summary="Found 3 threats",
            details="Scanned: 75 files, 8 directories. Detected 3 infected files.",
            path="/home/user/downloads",
            duration=60.0,
            scheduled=False,
        )
        result = statistics_calculator.extract_entry_statistics(entry)

        assert result["files_scanned"] == 75
        assert result["directories_scanned"] == 8
        assert result["duration"] == 60.0

    def test_extract_entry_statistics_update_log(self, statistics_calculator):
        """Test extraction from update log (should return zeros for scan stats)."""
        entry = LogEntry(
            id="test-7",
            timestamp="2024-01-15T10:00:00",
            type="update",
            status="success",
            summary="Database updated successfully",
            details="Updated to version 12345",
            path=None,
            duration=120.0,
            scheduled=True,
        )
        result = statistics_calculator.extract_entry_statistics(entry)

        # Update logs won't have file/directory scan information
        assert result["files_scanned"] == 0
        assert result["directories_scanned"] == 0
        assert result["duration"] == 120.0

    def test_extract_entry_statistics_empty_entry(self, statistics_calculator):
        """Test extraction from entry with empty strings."""
        entry = LogEntry(
            id="test-8",
            timestamp="2024-01-15T10:00:00",
            type="scan",
            status="clean",
            summary="",
            details="",
            path="",
            duration=0.0,
            scheduled=False,
        )
        result = statistics_calculator.extract_entry_statistics(entry)

        assert result["files_scanned"] == 0
        assert result["directories_scanned"] == 0
        assert result["duration"] == 0.0

    def test_extract_entry_statistics_return_type(self, statistics_calculator):
        """Test that return value is always a dictionary with expected keys."""
        entry = LogEntry(
            id="test-9",
            timestamp="2024-01-15T10:00:00",
            type="scan",
            status="clean",
            summary="Test scan",
            details="Test details",
            path="/test",
            duration=10.0,
            scheduled=False,
        )
        result = statistics_calculator.extract_entry_statistics(entry)

        assert isinstance(result, dict)
        assert len(result) == 3
        assert set(result.keys()) == {"files_scanned", "directories_scanned", "duration"}
        assert isinstance(result["files_scanned"], int)
        assert isinstance(result["directories_scanned"], int)
        assert isinstance(result["duration"], float)

    def test_extract_entry_statistics_scheduled_scan(self, statistics_calculator):
        """Test extraction from scheduled scan."""
        entry = LogEntry(
            id="test-10",
            timestamp="2024-01-15T10:00:00",
            type="scan",
            status="clean",
            summary="Scheduled scan completed",
            details="Scanned 300 files and 15 directories",
            path="/home/user",
            duration=90.25,
            scheduled=True,
        )
        result = statistics_calculator.extract_entry_statistics(entry)

        assert result["files_scanned"] == 300
        assert result["directories_scanned"] == 15
        assert result["duration"] == 90.25
