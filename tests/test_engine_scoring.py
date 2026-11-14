"""
Unit tests for scoring calculations, food consumption, and growth mechanics.
"""

from app.core.constants import Difficulty, Direction, GameState
from app.engine.models import Point
from app.engine.snake_engine import SnakeGameEngine
from app.engine.spawner import DeterministicFoodSpawner


def test_eating_food_increases_score_and_length():
    """Verifies that eating food increases score, snake length, and foods_eaten count."""
    # Place food directly in front of the snake's initial head (10, 10) -> (11, 10)
    spawner = DeterministicFoodSpawner([
        Point(11, 10),  # First food
        Point(12, 10),  # Second food
    ])
    engine = SnakeGameEngine(
        width=20,
        height=20,
        difficulty=Difficulty.EASY,  # 1.0 multiplier
        food_spawner=spawner,
        initial_snake_length=3,
    )
    engine.start()

    initial_len = engine.snake.length
    initial_score = engine.score
    initial_foods = engine.foods_eaten

    # First tick moves to (11, 10) where food is placed
    result = engine.tick()

    assert result.event == "FOOD_EATEN"
    assert result.score_delta == 10
    assert engine.score == initial_score + 10
    assert engine.snake.length == initial_len + 1
    assert engine.foods_eaten == initial_foods + 1
    assert engine.snake.head == Point(11, 10)

    # Food should have relocated to the next spawned position (12, 10)
    assert engine.food is not None
    assert engine.food.position == Point(12, 10)

    # Second tick eats second food
    result2 = engine.tick()
    assert result2.event == "FOOD_EATEN"
    assert engine.score == 20
    assert engine.snake.length == 5
    assert engine.foods_eaten == 2


def test_difficulty_score_multipliers():
    """Ensures each difficulty preset applies its appropriate multiplier."""
    test_cases = [
        (Difficulty.EASY, 10),      # 10 * 1.0 = 10
        (Difficulty.MEDIUM, 15),    # 10 * 1.5 = 15
        (Difficulty.HARD, 20),      # 10 * 2.0 = 20
        (Difficulty.EXPERT, 30),    # 10 * 3.0 = 30
    ]

    for diff, expected_pts in test_cases:
        spawner = DeterministicFoodSpawner([Point(11, 10)])
        engine = SnakeGameEngine(width=20, height=20, difficulty=diff, food_spawner=spawner)
        engine.start()
        res = engine.tick()
        assert res.event == "FOOD_EATEN"
        assert res.score == expected_pts
        assert res.score_delta == expected_pts


def test_food_respawns_only_on_unoccupied_positions():
    """Verifies that random spawner never places food on any snake segment."""
    engine = SnakeGameEngine(width=6, height=6)
    engine.start()

    # Verify initial food
    assert not engine.snake.occupies(engine.food.position)

    # Advance and eat multiple foods
    for _ in range(5):
        if engine.state != GameState.PLAYING:
            break
        # Aim towards food
        target = engine.food.position
        head = engine.snake.head
        if target.x > head.x and engine.snake.direction != Direction.LEFT:
            engine.change_direction(Direction.RIGHT)
        elif target.x < head.x and engine.snake.direction != Direction.RIGHT:
            engine.change_direction(Direction.LEFT)
        elif target.y > head.y and engine.snake.direction != Direction.UP:
            engine.change_direction(Direction.DOWN)
        elif target.y < head.y and engine.snake.direction != Direction.DOWN:
            engine.change_direction(Direction.UP)

        engine.tick()
        if engine.food:
            assert not engine.snake.occupies(engine.food.position)
