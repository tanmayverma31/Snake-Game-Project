"""
Unit tests for Game State lifecycle and transitions: Ready, Playing, Paused, Game Over.
"""

import time
import pytest

from app.core.constants import Difficulty, Direction, GameState
from app.core.exceptions import GameOverError, InvalidGameStateError
from app.engine.models import Point
from app.engine.snake_engine import SnakeGameEngine
from app.engine.spawner import DeterministicFoodSpawner


def test_initial_state_is_ready():
    """Engine must initialize in READY state."""
    engine = SnakeGameEngine(width=10, height=10)
    assert engine.state == GameState.READY
    assert engine.score == 0
    assert engine.foods_eaten == 0
    assert engine.get_elapsed_seconds() == 0.0


def test_state_transition_ready_to_playing():
    """Calling start() transitions READY to PLAYING."""
    engine = SnakeGameEngine(width=10, height=10)
    engine.start()
    assert engine.state == GameState.PLAYING
    assert engine.start_timestamp is not None


def test_pause_and_resume_lifecycle():
    """Tests PLAYING -> PAUSED -> PLAYING lifecycle transitions."""
    engine = SnakeGameEngine(width=10, height=10)
    engine.start()
    assert engine.state == GameState.PLAYING

    time.sleep(0.05)
    engine.pause()
    assert engine.state == GameState.PAUSED
    elapsed_after_pause = engine.get_elapsed_seconds()
    assert elapsed_after_pause > 0.0

    # While paused, ticks should be no-ops
    head_before = engine.snake.head
    res = engine.tick()
    assert res.event == "NONE"
    assert engine.snake.head == head_before

    # Resume game
    engine.resume()
    assert engine.state == GameState.PLAYING
    engine.tick()
    assert engine.snake.head != head_before


def test_invalid_state_transition_errors():
    """Verifies that invalid transitions raise proper domain exceptions."""
    engine = SnakeGameEngine(width=10, height=10)

    # Cannot pause while in READY
    with pytest.raises(InvalidGameStateError):
        engine.pause()

    # Cannot resume while in READY
    with pytest.raises(InvalidGameStateError):
        engine.resume()

    engine.start()
    # Cannot resume while already PLAYING
    with pytest.raises(InvalidGameStateError):
        engine.resume()


def test_game_over_state_and_direction_rejection():
    """Verifies behavior when state transitions to GAME_OVER."""
    # Force collision
    spawner = DeterministicFoodSpawner([Point(0, 0)])
    engine = SnakeGameEngine(width=4, height=4, food_spawner=spawner, initial_snake_length=2)
    engine.start()
    engine.tick()
    engine.tick()  # Hit wall -> GAME_OVER
    assert engine.state == GameState.GAME_OVER

    # Cannot pause when game over
    with pytest.raises(InvalidGameStateError):
        engine.pause()

    # Cannot change direction when game over
    with pytest.raises(GameOverError):
        engine.change_direction(Direction.UP)


def test_reset_restores_ready_state():
    """Verifies reset returns engine to initial state."""
    spawner = DeterministicFoodSpawner([Point(11, 10)])
    engine = SnakeGameEngine(width=20, height=20, food_spawner=spawner)
    engine.start()
    engine.tick()  # eats food
    assert engine.score > 0
    assert engine.foods_eaten > 0

    engine.reset()
    assert engine.state == GameState.READY
    assert engine.score == 0
    assert engine.foods_eaten == 0
    assert engine.snake.length == 3


def test_difficulty_adjustment():
    """Verifies difficulty presets and custom tick rate adjustments."""
    engine = SnakeGameEngine()
    assert engine.difficulty == Difficulty.MEDIUM
    assert engine.tick_interval_ms == 130

    engine.set_difficulty(Difficulty.HARD)
    assert engine.tick_interval_ms == 80

    engine.set_difficulty(Difficulty.EASY)
    assert engine.tick_interval_ms == 200

    # Custom speed
    engine.set_difficulty(Difficulty.CUSTOM, custom_tick_ms=65)
    assert engine.tick_interval_ms == 65

    # Out of range custom speed raises ValueError
    with pytest.raises(ValueError):
        engine.set_difficulty(Difficulty.CUSTOM, custom_tick_ms=5)
