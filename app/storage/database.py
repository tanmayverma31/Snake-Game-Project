"""
Database connection and schema setup for SQLite.
"""

from contextlib import contextmanager
import logging
import sqlite3
from typing import Generator

from app.core.config import settings
from app.core.exceptions import StorageError

logger = logging.getLogger("snake.storage")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS high_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 0),
    difficulty TEXT NOT NULL CHECK (difficulty IN ('EASY', 'MEDIUM', 'HARD', 'EXPERT', 'CUSTOM')),
    foods_eaten INTEGER NOT NULL DEFAULT 0 CHECK (foods_eaten >= 0),
    duration_seconds REAL NOT NULL DEFAULT 0.0 CHECK (duration_seconds >= 0.0),
    grid_size TEXT NOT NULL DEFAULT '20x20',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_high_scores_difficulty_score 
ON high_scores (difficulty, score DESC, duration_seconds ASC);

CREATE INDEX IF NOT EXISTS idx_high_scores_player 
ON high_scores (player_name, score DESC);
"""


class DatabaseManager:
    """Manages SQLite database connections and table schemas."""

    def __init__(self, db_path: str = settings.DATABASE_PATH):
        self.db_path = db_path
        self._init_schema()

    def _init_schema(self) -> None:
        """Initializes tables and indexes if they do not exist."""
        try:
            with self.get_connection() as conn:
                conn.executescript(SCHEMA_SQL)
                conn.commit()
            logger.info("Database schema initialized at %s", self.db_path)
        except sqlite3.Error as e:
            raise StorageError(f"Failed to initialize database schema: {e}") from e

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager yielding an SQLite connection with Row factory."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise StorageError(f"Database operation failed: {e}") from e
        finally:
            if conn:
                conn.close()
