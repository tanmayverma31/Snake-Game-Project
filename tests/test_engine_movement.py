"""
Unit tests for Snake movement and directional steering.
"""

import pytest
from app.core.constants import Direction, GameState
from app.core.exceptions import InvalidDirectionError
from app.engine.models import Point, Snake
from app.engine.snake_engine import SnakeGameEngine
from app.engine.spawner import DeterministicFoodSpawner


def test_initial_snake_placement():
    """Verifies that the snake starts centered, facing RIGHT with length 3."""
    engine = SnakeGameEngine(width=20, height=20, initial_snake_length=3)
    assert engine.snake.length == 3
    assert engine.snake.direction == Direction.RIGHT
    assert engine.snake.head == Point(10, 10)
    assert list(engine.snake.body) == [Point(10, 10), Point(9, 10), Point(8, 10)]
    assert engine.state == GameState.READY


def test_linear_movement_in_all_directions():
    """Tests single-step forward movement in all four cardinal directions."""
    # Place food far away so it doesn't interfere with movement testing
    spawner = DeterministicFoodSpawner([Point(0, 0)])

    # 1. Moving RIGHT
    engine = SnakeGameEngine(width=10, height=10, food_spawner=spawner)
    engine.start()
    init_head = engine.snake.head
    engine.tick()
    assert engine.snake.head == Point(init_head.x + 1, init_head.y)
    assert engine.snake.direction == Direction.RIGHT

    # 2. Turn UP
    engine.change_direction(Direction.UP)
    engine.tick()
    assert engine.snake.direction == Direction.UP
    assert engine.snake.head == Point(init_head.x + 1, init_head.y - 1)

    # 3. Turn LEFT
    engine.change_direction(Direction.LEFT)
    engine.tick()
    assert engine.snake.direction == Direction.LEFT
    assert engine.snake.head == Point(init_head.x, init_head.y - 1)

    # 4. Turn DOWN
    engine.change_direction(Direction.DOWN)
    engine.tick()
    assert engine.snake.direction == Direction.DOWN
    assert engine.snake.head == Point(init_head.x, init_head.y)


def test_prevention_of_180_degree_immediate_reverse():
    """Ensures player cannot reverse directly into own body."""
    engine = SnakeGameEngine(width=20, height=20)
    engine.start()

    # Snake is moving RIGHT -> attempting LEFT must be rejected
    assert engine.snake.direction == Direction.RIGHT
    with pytest.raises(InvalidDirectionError) as exc_info:
        engine.change_direction(Direction.LEFT)
    assert "Cannot reverse direction" in str(exc_info.value)
    assert engine.snake.direction == Direction.RIGHT

    # Turn UP
    engine.change_direction(Direction.UP)
    engine.tick()
    assert engine.snake.direction == Direction.UP

    # Moving UP -> attempting DOWN must be rejected
    with pytest.raises(InvalidDirectionError):
        engine.change_direction(Direction.DOWN)
    assert engine.snake.direction == Direction.UP


def test_input_buffering_for_rapid_turns():
    """
    Ensures rapid sequential inputs (e.g. UP then LEFT in one tick while moving RIGHT)
    are queued properly and do not trigger a false 180 reverse rejection.
    """
    engine = SnakeGameEngine(width=20, height=20)
    engine.start()

    # Currently moving RIGHT
    # Queue UP, then queue LEFT within the same tick frame
    accepted1 = engine.change_direction(Direction.UP)
    accepted2 = engine.change_direction(Direction.LEFT)
    assert accepted1 is True
    assert accepted2 is True

    # First tick consumes UP
    engine.tick()
    assert engine.snake.direction == Direction.UP

    # Second tick consumes LEFT
    engine.tick()
    assert engine.snake.direction == Direction.LEFT


def test_step_count_increments_per_tick():
    """Verifies engine steps counter increments on each active tick."""
    engine = SnakeGameEngine(width=20, height=20)
    engine.start()
    assert engine.steps_count == 0

    engine.tick()
    engine.tick()
    engine.tick()
    assert engine.steps_count == 3
