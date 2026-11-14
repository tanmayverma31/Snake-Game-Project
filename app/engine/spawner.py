"""
Food spawning strategies for the Snake game.
"""

from abc import ABC, abstractmethod
import random
from typing import List, Optional, Set

from app.core.config import settings
from app.engine.models import Board, Food, Point, Snake


class FoodSpawner(ABC):
    """Abstract base class for spawning food on the board."""

    @abstractmethod
    def spawn(self, board: Board, snake: Snake, points: int = settings.BASE_FOOD_POINTS) -> Optional[Food]:
        """Spawns food on an unoccupied cell of the board."""
        pass


class RandomFoodSpawner(FoodSpawner):
    """
    Standard random spawner: selects uniformly from all unoccupied board cells.
    """

    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random()

    def spawn(self, board: Board, snake: Snake, points: int = settings.BASE_FOOD_POINTS) -> Optional[Food]:
        occupied: Set[Point] = set(snake.body)
        available = list(board.unoccupied_points(occupied))

        if not available:
            # Board is completely filled by snake body (Win condition)
            return None

        pos = self.rng.choice(available)
        return Food(position=pos, points=points)


class DeterministicFoodSpawner(FoodSpawner):
    """
    Deterministic food spawner for reproducible unit testing.
    Picks coordinates from a predefined list sequentially.
    """

    def __init__(self, sequence: List[Point]):
        self.sequence = list(sequence)
        self.index = 0

    def spawn(self, board: Board, snake: Snake, points: int = settings.BASE_FOOD_POINTS) -> Optional[Food]:
        if not self.sequence:
            return None

        # Return next point in sequence, cycling or capping
        if self.index < len(self.sequence):
            pos = self.sequence[self.index]
            self.index += 1
        else:
            pos = self.sequence[-1]

        # Ensure point is in bounds
        if not board.is_within_bounds(pos):
            raise ValueError(f"Deterministic spawn point {pos} is outside board bounds.")

        return Food(position=pos, points=points)
