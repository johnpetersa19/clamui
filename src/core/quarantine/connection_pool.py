# ClamUI SQLite Connection Pool Module
"""
SQLite connection pool for the quarantine database.

Manages a pool of SQLite connections to reduce connection overhead for
batch operations and UI updates that make multiple quick queries.
"""

import queue
import sqlite3
import threading
from pathlib import Path
from typing import Optional


class ConnectionPool:
    """
    Thread-safe connection pool for SQLite database connections.

    Manages a pool of SQLite connections to reduce the overhead of creating
    and configuring new connections for each database operation. Connections
    are stored in a queue and reused across operations.

    Attributes:
        _db_path: Path to the SQLite database file
        _pool_size: Maximum number of connections in the pool
        _pool: Queue storing available connections
        _lock: Thread lock for thread-safe operations
        _total_connections: Total number of connections created
        _closed: Flag indicating if the pool has been closed
    """

    def __init__(self, db_path: str, pool_size: int = 5):
        """
        Initialize the connection pool.

        Args:
            db_path: Path to the SQLite database file
            pool_size: Maximum number of connections to maintain in the pool (default: 5)

        Raises:
            ValueError: If pool_size is less than 1
        """
        if pool_size < 1:
            raise ValueError("pool_size must be at least 1")

        self._db_path = Path(db_path)
        self._pool_size = pool_size
        self._pool: queue.Queue = queue.Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        self._total_connections = 0  # Track total connections created
        self._closed = False  # Track if pool has been closed

    def _create_connection(self) -> sqlite3.Connection:
        """
        Create a new SQLite connection with WAL mode and foreign keys enabled.

        This method creates a connection with the same configuration as used
        in QuarantineDatabase._get_connection() to ensure consistency.

        Returns:
            Configured SQLite connection object

        Raises:
            sqlite3.Error: If connection creation or configuration fails
        """
        conn = sqlite3.connect(str(self._db_path), timeout=30.0)
        try:
            # Enable WAL mode for better concurrency and corruption prevention
            conn.execute("PRAGMA journal_mode=WAL")
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys=ON")
            return conn
        except sqlite3.Error:
            # Close connection on configuration failure
            conn.close()
            raise

    def acquire(self, timeout: Optional[float] = None) -> sqlite3.Connection:
        """
        Acquire a connection from the pool.

        Returns a connection from the pool if available, or creates a new one
        if the pool is empty and the maximum pool size has not been reached.

        Args:
            timeout: Maximum time in seconds to wait for a connection.
                    None means wait indefinitely (default).

        Returns:
            A configured SQLite connection

        Raises:
            queue.Empty: If timeout expires while waiting for a connection
            RuntimeError: If the pool has been closed
        """
        # Check if pool is closed
        if self._closed:
            raise RuntimeError("Connection pool has been closed")

        try:
            # Try to get an existing connection from the pool
            return self._pool.get(block=True, timeout=timeout)
        except queue.Empty:
            # Pool is empty - try to create a new connection if we're below max size
            with self._lock:
                if self._total_connections < self._pool_size:
                    # We can create a new connection
                    conn = self._create_connection()
                    self._total_connections += 1
                    return conn
                else:
                    # Pool is exhausted and we're at max size - re-raise the timeout exception
                    raise
