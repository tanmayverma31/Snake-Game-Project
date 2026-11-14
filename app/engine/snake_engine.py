"""
Core Snake Game Engine.
Completely independent of UI, network, and database layers.
"""

from collections import deque
from dataclasses import dataclass, field
import time
from typing import Deque, List, Optional

from app.core.config import settings
from app.core.constants import CollisionType, Difficulty, Direction, GameState
from app.core.exceptions import (
    GameOverError,
    InvalidDirectionError,
    InvalidGameStateError,
)
from app.engine.models import Board, Food, Point, Snake
from app.engine.spawner import FoodSpawner, RandomFoodSpawner


@dataclass
class TickResult:
    """Outcome data returned after each engine tick."""
    event: str  # "NONE", "STEP", "FOOD_EATEN", "GAME_OVER", "VICTORY"
    state: GameState
    collision_type: CollisionType
    score: int
    score_delta: int
    foods_eaten: int
    snake_length: int
    head: Point
    food_position: Optional[Point]
    duration_seconds: float
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "event": self.event,
            "state": self.state.value,
            "collision_type": self.collision_type.value,
            "score": self.score,
            "score_delta": self.score_delta,
            "foods_eaten": self.foods_eaten,
            "snake_length": self.snake_length,
            "head": self.head.to_dict(),
            "food_position": self.food_position.to_dict() if self.food_position else None,
            "duration_seconds": round(self.duration_seconds, 2),
            "message": self.message,
        }


class SnakeGameEngine:
    """
    Pure Snake Game Engine implementing movement, collision detection,
    scoring, food spawning, difficulty levels, and state management.
    """

    def __init__(
        self,
        width: int = settings.DEFAULT_BOARD_WIDTH,
        height: int = settings.DEFAULT_BOARD_HEIGHT,
        difficulty: Difficulty = Difficulty.MEDIUM,
        custom_tick_ms: Optional[int] = None,
        food_spawner: Optional[FoodSpawner] = None,
        initial_snake_length: int = 3,
    ):
        self.board: Board = Board(width=width, height=height)
        self.difficulty: Difficulty = difficulty
        self._custom_tick_ms: Optional[int] = custom_tick_ms
        self.food_spawner: FoodSpawner = food_spawner or RandomFoodSpawner()
        self.initial_snake_length: int = initial_snake_length

        # State tracking
        self.state: GameState = GameState.READY
        self.collision_type: CollisionType = CollisionType.NONE
        self.score: int = 0
        self.foods_eaten: int = 0
        self.steps_count: int = 0
        self.start_timestamp: Optional[float] = None
        self.total_elapsed_seconds: float = 0.0

        # Input buffer to handle rapid direction requests smoothly (max 3 queued)
        self._input_queue: Deque[Direction] = deque(maxlen=3)

        # Initialize snake and food
        self.snake: Snake = self._create_initial_snake()
        self.food: Optional[Food] = None
        self._spawn_initial_food()

    # --------------------------------------------------------------------------
    # Initialization Helpers
    # --------------------------------------------------------------------------

    def _create_initial_snake(self) -> Snake:
        """Positions snake centered on the board, facing RIGHT."""
        mid_y = self.board.height // 2
        mid_x = self.board.width // 2

        # Create segments trailing to the left from the head
        segments: List[Point] = []
        for i in range(self.initial_snake_length):
            x = mid_x - i
            # Clamp or wrap just in case board is small
            segments.append(Point(max(0, x), mid_y))

        return Snake(initial_segments=segments, initial_direction=Direction.RIGHT)

    def _spawn_initial_food(self) -> None:
        """Spawns first food item on the board."""
        self.food = self.food_spawner.spawn(self.board, self.snake, points=settings.BASE_FOOD_POINTS)

    # --------------------------------------------------------------------------
    # Configuration & Timing
    # --------------------------------------------------------------------------

    @property
    def tick_interval_ms(self) -> int:
        """Returns the current tick speed in milliseconds."""
        if self.difficulty == Difficulty.CUSTOM and self._custom_tick_ms is not None:
            return self._custom_tick_ms
        return self.difficulty.tick_ms

    def set_difficulty(self, difficulty: Difficulty, custom_tick_ms: Optional[int] = None) -> None:
        """Sets game difficulty and adjusts tick rate."""
        self.difficulty = difficulty
        if difficulty == Difficulty.CUSTOM and custom_tick_ms is not None:
            if custom_tick_ms < 10 or custom_tick_ms > 2000:
                raise ValueError("custom_tick_ms must be between 10ms and 2000ms.")
            self._custom_tick_ms = custom_tick_ms

    # --------------------------------------------------------------------------
    # Lifecycle & State Controls
    # --------------------------------------------------------------------------

    def start(self) -> None:
        """Starts or restarts the game."""
        if self.state == GameState.GAME_OVER:
            self.reset()
        self.state = GameState.PLAYING
        if self.start_timestamp is None:
            self.start_timestamp = time.monotonic()

    def pause(self) -> None:
        """Pauses an active game."""
        if self.state != GameState.PLAYING:
            raise InvalidGameStateError(f"Cannot pause game when in state {self.state.value}.")
        self.state = GameState.PAUSED
        if self.start_timestamp is not None:
            self.total_elapsed_seconds += time.monotonic() - self.start_timestamp
            self.start_timestamp = None

    def resume(self) -> None:
        """Resumes a paused game."""
        if self.state != GameState.PAUSED:
            raise InvalidGameStateError(f"Cannot resume game when in state {self.state.value}.")
        self.state = GameState.PLAYING
        self.start_timestamp = time.monotonic()

    def reset(self) -> None:
        """Resets engine to fresh READY state."""
        self.state = GameState.READY
        self.collision_type = CollisionType.NONE
        self.score = 0
        self.foods_eaten = 0
        self.steps_count = 0
        self.start_timestamp = None
        self.total_elapsed_seconds = 0.0
        self._input_queue.clear()
        self.snake = self._create_initial_snake()
        self.food = None
        self._spawn_initial_food()

    # --------------------------------------------------------------------------
    # Direction Control
    # --------------------------------------------------------------------------

    def change_direction(self, new_direction: Direction) -> bool:
        """
        Requests a direction change.
        Rejects immediate 180-degree reverse turns (e.g. RIGHT -> LEFT).
        Queues valid turns into the input buffer.
        """
        if self.state == GameState.GAME_OVER:
            raise GameOverError("Cannot change direction: game is already GAME_OVER.")

        # Determine reference direction (either the last queued direction or current snake direction)
        reference_dir = self._input_queue[-1] if self._input_queue else self.snake.direction

        # Disallow 180 reverse
        if new_direction.is_opposite_of(reference_dir):
            raise InvalidDirectionError(
                f"Cannot reverse direction from {reference_dir.value} to {new_direction.value}."
            )

        # Ignore redundant consecutive commands
        if new_direction == reference_dir:
            return False

        self._input_queue.append(new_direction)
        return True

    # --------------------------------------------------------------------------
    # Engine Heartbeat (Tick)
    # --------------------------------------------------------------------------

    def tick(self) -> TickResult:
        """
        Advances the game simulation by one tick:
        1. Consumes the next queued direction (if any).
        2. Computes the next head position.
        3. Detects wall and self collisions.
        4. If collision: sets GAME_OVER and terminates.
        5. If safe: checks for food consumption, grows snake, increments score,
           spawns next food, or advances snake normally.
        """
        # If not playing, tick is a no-op
        if self.state != GameState.PLAYING:
            return TickResult(
                event="NONE",
                state=self.state,
                collision_type=self.collision_type,
                score=self.score,
                score_delta=0,
                foods_eaten=self.foods_eaten,
                snake_length=self.snake.length,
                head=self.snake.head,
                food_position=self.food.position if self.food else None,
                duration_seconds=self.get_elapsed_seconds(),
                message=f"Game is not playing (current state: {self.state.value}).",
            )

        self.steps_count += 1

        # 1. Update direction from queue if available
        if self._input_queue:
            next_dir = self._input_queue.popleft()
            if not next_dir.is_opposite_of(self.snake.direction):
                self.snake.direction = next_dir

        # 2. Compute next head position
        next_head = self.snake.head.move(self.snake.direction)

        # 3. Collision Detection
        # 3a. Wall Collision
        if not self.board.is_within_bounds(next_head):
            return self._handle_game_over(CollisionType.WALL, "Snake hit a wall.")

        # 3b. Food Eating Check (determines whether snake will grow on this tick)
        will_eat_food = self.food is not None and next_head == self.food.position

        # 3c. Self Collision Check
        # If snake will eat food, the tail does NOT move forward, so entire current body is an obstacle.
        # If snake will NOT eat food, the tail will vacate its cell this tick, so tail position is safe to enter.
        is_self_collision = (
            self.snake.occupies(next_head)
            if will_eat_food
            else self.snake.occupies_body_excluding_tail(next_head)
        )

        if is_self_collision:
            return self._handle_game_over(CollisionType.SELF, "Snake collided with its own body.")

        # 4. Movement & Scoring
        score_delta = 0
        event = "STEP"
        message = "Snake moved forward."

        if will_eat_food:
            # Snake eats food and grows
            self.snake.move(next_head, grow=True)
            self.foods_eaten += 1

            # Score calculation: base points * difficulty multiplier
            base_points = self.food.points if self.food else settings.BASE_FOOD_POINTS
            score_delta = int(base_points * self.difficulty.score_multiplier)
            self.score += score_delta

            event = "FOOD_EATEN"
            message = f"Food eaten! +{score_delta} points."

            # Spawn new food
            self.food = self.food_spawner.spawn(self.board, self.snake, points=settings.BASE_FOOD_POINTS)
            if self.food is None:
                # Victory! All board cells occupied by the snake
                self.state = GameState.GAME_OVER
                event = "VICTORY"
                message = "Perfection! Snake completely filled the board."
        else:
            # Normal movement without growing
            self.snake.move(next_head, grow=False)

        return TickResult(
            event=event,
            state=self.state,
            collision_type=self.collision_type,
            score=self.score,
            score_delta=score_delta,
            foods_eaten=self.foods_eaten,
            snake_length=self.snake.length,
            head=self.snake.head,
            food_position=self.food.position if self.food else None,
            duration_seconds=self.get_elapsed_seconds(),
            message=message,
        )

    def _handle_game_over(self, collision_type: CollisionType, message: str) -> TickResult:
        """Transitions state to GAME_OVER upon collision."""
        self.state = GameState.GAME_OVER
        self.collision_type = collision_type
        if self.start_timestamp is not None:
            self.total_elapsed_seconds += time.monotonic() - self.start_timestamp
            self.start_timestamp = None

        return TickResult(
            event="GAME_OVER",
            state=self.state,
            collision_type=self.collision_type,
            score=self.score,
            score_delta=0,
            foods_eaten=self.foods_eaten,
            snake_length=self.snake.length,
            head=self.snake.head,
            food_position=self.food.position if self.food else None,
            duration_seconds=self.get_elapsed_seconds(),
            message=message,
        )

    def get_elapsed_seconds(self) -> float:
        """Returns total active playing time in seconds."""
        current = self.total_elapsed_seconds
        if self.state == GameState.PLAYING and self.start_timestamp is not None:
            current += time.monotonic() - self.start_timestamp
        return current

    # --------------------------------------------------------------------------
    # Serialization
    # --------------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Full serializable representation of engine state."""
        return {
            "state": self.state.value,
            "collision_type": self.collision_type.value,
            "score": self.score,
            "foods_eaten": self.foods_eaten,
            "steps_count": self.steps_count,
            "difficulty": self.difficulty.value,
            "tick_interval_ms": self.tick_interval_ms,
            "duration_seconds": round(self.get_elapsed_seconds(), 2),
            "board": self.board.to_dict(),
            "snake": {
                "head": self.snake.head.to_dict(),
                "length": self.snake.length,
                "direction": self.snake.direction.value,
                "segments": self.snake.to_list(),
            },
            "food": self.food.to_dict() if self.food else None,
        }
