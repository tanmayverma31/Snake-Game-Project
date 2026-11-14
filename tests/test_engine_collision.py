"""
Unit tests for collision detection: Wall collisions and Self collisions.
"""

from app.core.constants import CollisionType, Direction, GameState
from app.engine.models import Point, Snake
from app.engine.snake_engine import SnakeGameEngine
from app.engine.spawner import DeterministicFoodSpawner


def test_collision_with_right_wall():
    """Snake moves right until it impacts the board boundary."""
    # 6x6 board, snake starts at (3, 3) facing RIGHT
    spawner = DeterministicFoodSpawner([Point(0, 0)])
    engine = SnakeGameEngine(width=6, height=6, food_spawner=spawner, initial_snake_length=2)
    engine.start()

    # Initial head is at (3, 3)
    # Step 1: head -> (4, 3)
    res1 = engine.tick()
    assert res1.state == GameState.PLAYING

    # Step 2: head -> (5, 3) (boundary edge)
    res2 = engine.tick()
    assert res2.state == GameState.PLAYING

    # Step 3: next_head would be (6, 3) -> OUT OF BOUNDS!
    res3 = engine.tick()
    assert res3.state == GameState.GAME_OVER
    assert res3.collision_type == CollisionType.WALL
    assert engine.state == GameState.GAME_OVER
    assert engine.collision_type == CollisionType.WALL


def test_collision_with_top_wall():
    """Snake turns UP and collides with the top boundary (y < 0)."""
    spawner = DeterministicFoodSpawner([Point(0, 5)])
    engine = SnakeGameEngine(width=6, height=6, food_spawner=spawner, initial_snake_length=2)
    engine.start()

    # Head is at (3, 3). Turn UP.
    engine.change_direction(Direction.UP)
    engine.tick()  # head -> (3, 2)
    engine.tick()  # head -> (3, 1)
    engine.tick()  # head -> (3, 0)
    assert engine.state == GameState.PLAYING

    # Next tick would move head to (3, -1) -> WALL COLLISION
    res = engine.tick()
    assert res.state == GameState.GAME_OVER
    assert res.collision_type == CollisionType.WALL


def test_collision_with_left_wall():
    """Snake turns UP, then LEFT and collides with the left boundary (x < 0)."""
    spawner = DeterministicFoodSpawner([Point(5, 5)])
    engine = SnakeGameEngine(width=6, height=6, food_spawner=spawner, initial_snake_length=2)
    engine.start()

    # Head is at (3, 3). Turn UP, then LEFT.
    engine.change_direction(Direction.UP)
    engine.tick()  # head -> (3, 2)
    engine.change_direction(Direction.LEFT)
    engine.tick()  # head -> (2, 2)
    engine.tick()  # head -> (1, 2)
    engine.tick()  # head -> (0, 2)
    assert engine.state == GameState.PLAYING

    # Next tick moves head to (-1, 2) -> WALL COLLISION
    res = engine.tick()
    assert res.state == GameState.GAME_OVER
    assert res.collision_type == CollisionType.WALL


def test_collision_with_bottom_wall():
    """Snake turns DOWN and collides with bottom boundary (y >= height)."""
    spawner = DeterministicFoodSpawner([Point(0, 0)])
    engine = SnakeGameEngine(width=6, height=6, food_spawner=spawner, initial_snake_length=2)
    engine.start()

    # Head is at (3, 3). Turn DOWN.
    engine.change_direction(Direction.DOWN)
    engine.tick()  # head -> (3, 4)
    engine.tick()  # head -> (3, 5)
    assert engine.state == GameState.PLAYING

    # Next tick moves head to (3, 6) -> WALL COLLISION
    res = engine.tick()
    assert res.state == GameState.GAME_OVER
    assert res.collision_type == CollisionType.WALL


def test_self_collision():
    """Snake grows long enough and turns into its own body."""
    # Construct a snake with body segments in a loop
    # Let snake have 5 segments:
    # Head at (2, 2), body at (2, 1), (1, 1), (1, 2), (1, 3)
    spawner = DeterministicFoodSpawner([Point(0, 0)])
    engine = SnakeGameEngine(width=10, height=10, food_spawner=spawner)
    engine.snake = Snake(
        initial_segments=[
            Point(2, 2),  # head
            Point(2, 1),
            Point(1, 1),
            Point(1, 2),
            Point(1, 3),  # tail
        ],
        initial_direction=Direction.LEFT,
    )
    engine.start()

    # Next head will be (1, 2) when moving LEFT, which is an existing segment of the body!
    res = engine.tick()
    assert res.state == GameState.GAME_OVER
    assert res.collision_type == CollisionType.SELF
    assert "collided with its own body" in res.message


def test_tail_chasing_is_safe_when_not_growing():
    """
    In classic Snake, if the snake is NOT eating food, the tail vacates its position
    on the exact tick the head moves, so moving into the current tail's position is safe.
    """
    spawner = DeterministicFoodSpawner([Point(0, 0)])  # food far away
    engine = SnakeGameEngine(width=10, height=10, food_spawner=spawner)
    # Snake forming a 4-segment loop:
    # Head at (2, 2) facing LEFT, body at (2, 1), (1, 1), tail at (1, 2)
    engine.snake = Snake(
        initial_segments=[
            Point(2, 2),  # head
            Point(2, 1),
            Point(1, 1),
            Point(1, 2),  # tail
        ],
        initial_direction=Direction.LEFT,
    )
    engine.start()

    # If tail didn't vacate, (1, 2) would collide. But since it vacates and no food is eaten, it is safe!
    # Wait: here tail is at (1, 2). If head is at (2, 2) and moves LEFT, next head is (1, 2).
    # Since snake is not eating, tail at (1, 2) vacates.
    res = engine.tick()
    assert res.state == GameState.PLAYING
    assert res.collision_type == CollisionType.NONE
    assert engine.snake.head == Point(1, 2)


def test_subsequent_ticks_after_game_over_are_noop():
    """Verifies that ticks executed after GAME_OVER do not advance or alter state."""
    spawner = DeterministicFoodSpawner([Point(0, 0)])
    engine = SnakeGameEngine(width=4, height=4, food_spawner=spawner, initial_snake_length=2)
    engine.start()

    # Move right into wall
    engine.tick()  # (2, 2) -> (3, 2)
    engine.tick()  # Game Over
    assert engine.state == GameState.GAME_OVER

    head_before = engine.snake.head
    steps_before = engine.steps_count

    # Extra tick
    noop_res = engine.tick()
    assert noop_res.state == GameState.GAME_OVER
    assert noop_res.event == "NONE"
    assert engine.snake.head == head_before
    assert engine.steps_count == steps_before
