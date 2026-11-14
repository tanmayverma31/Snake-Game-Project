"""
Core constants and enumerations for the Snake Game Engine.
"""

from enum import Enum
from typing import Tuple


class Direction(str, Enum):
    """Cardinal movement directions for the snake."""
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"

    @property
    def vector(self) -> Tuple[int, int]:
        """Returns the (dx, dy) vector corresponding to this direction."""
        vectors = {
            Direction.UP: (0, -1),
            Direction.DOWN: (0, 1),
            Direction.LEFT: (-1, 0),
            Direction.RIGHT: (1, 0),
        }
        return vectors[self]

    @property
    def opposite(self) -> "Direction":
        """Returns the opposing 180-degree direction."""
        opposites = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT,
        }
        return opposites[self]

    def is_opposite_of(self, other: "Direction") -> bool:
        """Checks if another direction is the immediate 180-degree reverse."""
        return self.opposite == other


class GameState(str, Enum):
    """Lifecycle states of a snake game session."""
    READY = "READY"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    GAME_OVER = "GAME_OVER"


class CollisionType(str, Enum):
    """Types of terminal collisions."""
    NONE = "NONE"
    WALL = "WALL"
    SELF = "SELF"


class Difficulty(str, Enum):
    """
    Difficulty presets controlling tick interval (speed) and scoring weight.
    """
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    EXPERT = "EXPERT"
    CUSTOM = "CUSTOM"

    @property
    def tick_ms(self) -> int:
        """Default milliseconds per tick for this difficulty preset."""
        ticks = {
            Difficulty.EASY: 200,      # 5 ticks per sec
            Difficulty.MEDIUM: 130,    # ~7.7 ticks per sec
            Difficulty.HARD: 80,       # 12.5 ticks per sec
            Difficulty.EXPERT: 50,     # 20 ticks per sec
            Difficulty.CUSTOM: 130,
        }
        return ticks[self]

    @property
    def score_multiplier(self) -> float:
        """Score multiplier applied to base food points."""
        multipliers = {
            Difficulty.EASY: 1.0,
            Difficulty.MEDIUM: 1.5,
            Difficulty.HARD: 2.0,
            Difficulty.EXPERT: 3.0,
            Difficulty.CUSTOM: 1.0,
        }
        return multipliers[self]
