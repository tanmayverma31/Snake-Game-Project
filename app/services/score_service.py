"""
Service managing player scores, validations, and leaderboard ranking.
"""

from typing import List, Optional

from app.storage.models import HighScoreRecord
from app.storage.repository import HighScoreRepository


class ScoreService:
    """Business logic for high score validation and retrieval."""

    def __init__(self, repository: HighScoreRepository):
        self.repository = repository

    def submit_score(
        self,
        player_name: str,
        score: int,
        difficulty: str,
        foods_eaten: int,
        duration_seconds: float,
        grid_size: str = "20x20",
    ) -> HighScoreRecord:
        """Validates and records a game score."""
        record = HighScoreRecord(
            player_name=player_name,
            score=score,
            difficulty=difficulty.upper(),
            foods_eaten=foods_eaten,
            duration_seconds=duration_seconds,
            grid_size=grid_size,
        )
        return self.repository.save(record)

    def get_leaderboard(self, limit: int = 10, difficulty: Optional[str] = None) -> List[HighScoreRecord]:
        """Fetches top scores optionally filtered by difficulty."""
        return self.repository.get_top(limit=limit, difficulty=difficulty)

    def get_player_best(self, player_name: str) -> Optional[HighScoreRecord]:
        """Fetches personal best for a player."""
        return self.repository.get_player_best(player_name=player_name)

    def get_player_history(self, player_name: str, limit: int = 10) -> List[HighScoreRecord]:
        """Fetches score history for a player."""
        return self.repository.get_player_history(player_name=player_name, limit=limit)
