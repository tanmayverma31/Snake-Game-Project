"""
Data models for persistent storage of game scores.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class HighScoreRecord:
    """Represents a persisted game score entry."""
    id: Optional[int] = None
    player_name: str = "Player"
    score: int = 0
    difficulty: str = "MEDIUM"
    foods_eaten: int = 0
    duration_seconds: float = 0.0
    grid_size: str = "20x20"
    created_at: Optional[str] = None

    def __post_init__(self):
        # Validation
        self.player_name = self.player_name.strip() or "Anonymous"
        if len(self.player_name) > 50:
            self.player_name = self.player_name[:50]
        if self.score < 0:
            raise ValueError("Score cannot be negative.")
        if self.foods_eaten < 0:
            raise ValueError("Foods eaten cannot be negative.")
        if self.duration_seconds < 0:
            raise ValueError("Duration cannot be negative.")
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "player_name": self.player_name,
            "score": self.score,
            "difficulty": self.difficulty,
            "foods_eaten": self.foods_eaten,
            "duration_seconds": round(self.duration_seconds, 2),
            "grid_size": self.grid_size,
            "created_at": self.created_at,
        }
