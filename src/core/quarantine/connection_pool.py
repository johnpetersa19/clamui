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
