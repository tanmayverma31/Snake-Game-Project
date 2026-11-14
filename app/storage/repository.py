"""
High Score Repository for persisting and retrieving player scores.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.exceptions import StorageError
from app.storage.database import DatabaseManager
from app.storage.models import HighScoreRecord


class HighScoreRepository(ABC):
    """Abstract repository interface for score persistence."""

    @abstractmethod
    def save(self, record: HighScoreRecord) -> HighScoreRecord:
        """Persists a new score entry and returns the record with assigned ID."""
        pass

    @abstractmethod
    def get_top(self, limit: int = 10, difficulty: Optional[str] = None) -> List[HighScoreRecord]:
        """Retrieves top leaderboard entries ordered by highest score."""
        pass

    @abstractmethod
    def get_player_best(self, player_name: str) -> Optional[HighScoreRecord]:
        """Retrieves the highest score achieved by a specific player."""
        pass

    @abstractmethod
    def get_player_history(self, player_name: str, limit: int = 10) -> List[HighScoreRecord]:
        """Retrieves past scores for a specific player."""
        pass

    @abstractmethod
    def clear_all(self) -> None:
        """Clears all records (useful for test environments)."""
        pass


class SQLiteHighScoreRepository(HighScoreRepository):
    """SQLite implementation of HighScoreRepository."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def save(self, record: HighScoreRecord) -> HighScoreRecord:
        query = """
        INSERT INTO high_scores (player_name, score, difficulty, foods_eaten, duration_seconds, grid_size, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            record.player_name,
            record.score,
            record.difficulty,
            record.foods_eaten,
            record.duration_seconds,
            record.grid_size,
            record.created_at,
        )
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                record.id = cursor.lastrowid
                conn.commit()
                return record
        except Exception as e:
            raise StorageError(f"Failed to save high score: {e}") from e

    def get_top(self, limit: int = 10, difficulty: Optional[str] = None) -> List[HighScoreRecord]:
        if difficulty:
            query = """
            SELECT id, player_name, score, difficulty, foods_eaten, duration_seconds, grid_size, created_at
            FROM high_scores
            WHERE difficulty = ?
            ORDER BY score DESC, duration_seconds ASC
            LIMIT ?
            """
            params = (difficulty.upper(), max(1, limit))
        else:
            query = """
            SELECT id, player_name, score, difficulty, foods_eaten, duration_seconds, grid_size, created_at
            FROM high_scores
            ORDER BY score DESC, duration_seconds ASC
            LIMIT ?
            """
            params = (max(1, limit),)

        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [
                    HighScoreRecord(
                        id=row["id"],
                        player_name=row["player_name"],
                        score=row["score"],
                        difficulty=row["difficulty"],
                        foods_eaten=row["foods_eaten"],
                        duration_seconds=row["duration_seconds"],
                        grid_size=row["grid_size"],
                        created_at=row["created_at"],
                    )
                    for row in rows
                ]
        except Exception as e:
            raise StorageError(f"Failed to retrieve top scores: {e}") from e

    def get_player_best(self, player_name: str) -> Optional[HighScoreRecord]:
        query = """
        SELECT id, player_name, score, difficulty, foods_eaten, duration_seconds, grid_size, created_at
        FROM high_scores
        WHERE LOWER(player_name) = LOWER(?)
        ORDER BY score DESC, duration_seconds ASC
        LIMIT 1
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (player_name.strip(),))
                row = cursor.fetchone()
                if not row:
                    return None
                return HighScoreRecord(
                    id=row["id"],
                    player_name=row["player_name"],
                    score=row["score"],
                    difficulty=row["difficulty"],
                    foods_eaten=row["foods_eaten"],
                    duration_seconds=row["duration_seconds"],
                    grid_size=row["grid_size"],
                    created_at=row["created_at"],
                )
        except Exception as e:
            raise StorageError(f"Failed to retrieve player best score: {e}") from e

    def get_player_history(self, player_name: str, limit: int = 10) -> List[HighScoreRecord]:
        query = """
        SELECT id, player_name, score, difficulty, foods_eaten, duration_seconds, grid_size, created_at
        FROM high_scores
        WHERE LOWER(player_name) = LOWER(?)
        ORDER BY created_at DESC
        LIMIT ?
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (player_name.strip(), max(1, limit)))
                rows = cursor.fetchall()
                return [
                    HighScoreRecord(
                        id=row["id"],
                        player_name=row["player_name"],
                        score=row["score"],
                        difficulty=row["difficulty"],
                        foods_eaten=row["foods_eaten"],
                        duration_seconds=row["duration_seconds"],
                        grid_size=row["grid_size"],
                        created_at=row["created_at"],
                    )
                    for row in rows
                ]
        except Exception as e:
            raise StorageError(f"Failed to retrieve player history: {e}") from e

    def clear_all(self) -> None:
        query = "DELETE FROM high_scores"
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute(query)
                conn.commit()
        except Exception as e:
            raise StorageError(f"Failed to clear high scores: {e}") from e
