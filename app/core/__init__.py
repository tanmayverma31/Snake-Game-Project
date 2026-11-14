"""
Core package initialization.
"""

from app.core.constants import Direction, GameState, Difficulty, CollisionType
from app.core.exceptions import (
    SnakeGameError,
    InvalidDirectionError,
    InvalidGameStateError,
    GameOverError,
    GameNotFoundError,
    StorageError,
    GeminiServiceError,
)
from app.core.config import settings

__all__ = [
    "Direction",
    "GameState",
    "Difficulty",
    "CollisionType",
    "SnakeGameError",
    "InvalidDirectionError",
    "InvalidGameStateError",
    "GameOverError",
    "GameNotFoundError",
    "StorageError",
    "GeminiServiceError",
    "settings",
]
