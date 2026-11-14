"""
Domain and system exceptions for the Snake Game backend.
"""

from typing import Optional


class SnakeGameError(Exception):
    """Base exception for all domain errors in Snake Game."""
    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__


class InvalidDirectionError(SnakeGameError):
    """Raised when an illegal direction turn is requested (e.g. 180 reverse)."""
    pass


class InvalidGameStateError(SnakeGameError):
    """Raised when an operation is invalid for current game state (e.g. pause when not playing)."""
    pass


class GameOverError(SnakeGameError):
    """Raised when attempting an action on a terminated game."""
    pass


class GameNotFoundError(SnakeGameError):
    """Raised when a referenced game session ID does not exist."""
    pass


class StorageError(SnakeGameError):
    """Raised when database operations encounter an error."""
    pass


class GeminiServiceError(SnakeGameError):
    """Raised when an AI integration call fails (safely handled as non-blocking)."""
    pass
