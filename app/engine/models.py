"""
Domain models for the Snake game engine: Point, Snake, Food, Board.
"""

from collections import deque
from dataclasses import dataclass
from typing import Deque, List, Optional, Set

from app.core.constants import Direction


@dataclass(frozen=True)
class Point:
    """Immutable 2D coordinate on the game grid."""
    x: int
    y: int

    def translate(self, dx: int, dy: int) -> "Point":
        """Returns a new Point translated by (dx, dy)."""
        return Point(self.x + dx, self.y + dy)

    def move(self, direction: Direction) -> "Point":
        """Returns a new Point translated in the given direction vector."""
        dx, dy = direction.vector
        return Point(self.x + dx, self.y + dy)

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y}


@dataclass
class Food:
    """Represents a food item on the board."""
    position: Point
    points: int = 10
    kind: str = "apple"

    def to_dict(self) -> dict:
        return {
            "position": self.position.to_dict(),
            "points": self.points,
            "kind": self.kind,
        }


class Snake:
    """
    Snake entity maintaining body segments and movement direction.
    Head is body[0], tail is body[-1].
    """

    def __init__(self, initial_segments: List[Point], initial_direction: Direction = Direction.RIGHT):
        if not initial_segments:
            raise ValueError("Snake must have at least one body segment.")
        self.body: Deque[Point] = deque(initial_segments)
        self.direction: Direction = initial_direction

    @property
    def head(self) -> Point:
        """Returns the current head position."""
        return self.body[0]

    @property
    def tail(self) -> Point:
        """Returns the current tail position."""
        return self.body[-1]

    @property
    def length(self) -> int:
        """Returns the current length of the snake."""
        return len(self.body)

    def occupies(self, point: Point) -> bool:
        """Checks if a point is currently occupied by any segment of the snake."""
        return point in self.body

    def occupies_body_excluding_tail(self, point: Point) -> bool:
        """
        Checks if a point is occupied by any segment other than the tail.
        Used to accurately detect self-collision on ticks when the snake doesn't grow.
        """
        if len(self.body) <= 1:
            return False
        # Body excluding tail is body[0:-1]
        for i in range(len(self.body) - 1):
            if self.body[i] == point:
                return True
        return False

    def move(self, next_head: Point, grow: bool = False) -> None:
        """
        Advances the snake by adding next_head.
        Pops the tail if grow is False, or keeps it if grow is True.
        """
        self.body.appendleft(next_head)
        if not grow:
            self.body.pop()

    def to_list(self) -> List[dict]:
        """Serializes snake segments to a list of dicts."""
        return [segment.to_dict() for segment in self.body]


class Board:
    """
    Grid boundaries and boundary validation.
    """

    def __init__(self, width: int = 20, height: int = 20):
        if width < 4 or height < 4:
            raise ValueError("Board dimensions must be at least 4x4.")
        self.width: int = width
        self.height: int = height

    def is_within_bounds(self, point: Point) -> bool:
        """Checks if a point is within the board limits [0, width) and [0, height)."""
        return 0 <= point.x < self.width and 0 <= point.y < self.height

    def all_points(self) -> Set[Point]:
        """Returns all coordinates on the board."""
        return {Point(x, y) for x in range(self.width) for y in range(self.height)}

    def unoccupied_points(self, occupied: Set[Point]) -> Set[Point]:
        """Returns set of all board points not in occupied."""
        return self.all_points() - occupied

    def to_dict(self) -> dict:
        return {"width": self.width, "height": self.height}
