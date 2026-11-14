"""
Unit tests for Gemini AI services and safe heuristic fallbacks.
"""

from unittest.mock import MagicMock
from app.ai.gemini_client import GeminiClientWrapper
from app.ai.services import SnakeAIService
from app.core.constants import Direction


def test_ai_service_graceful_fallback_without_api_key():
    """Ensures AI service operates completely safely in fallback mode when no API key is set."""
    client = GeminiClientWrapper(api_key="")
    assert not client.is_available

    service = SnakeAIService(gemini_client=client)

    # Move advice fallback test
    advice = service.get_move_advice(
        board_width=10,
        board_height=10,
        snake_segments=[{"x": 5, "y": 5}, {"x": 4, "y": 5}, {"x": 3, "y": 5}],
        current_direction="RIGHT",
        food_pos={"x": 5, "y": 6},
    )
    assert advice["source"] == "heuristic"
    assert advice["recommended_direction"] in ["UP", "DOWN", "RIGHT"]
    # Direction LEFT is opposite of RIGHT, so it must not be recommended
    assert advice["recommended_direction"] != "LEFT"
    assert "safe_directions" in advice


def test_tactical_move_advisor_avoids_suicidal_wall_crash():
    """
    If snake is at the very right edge (x=9) moving RIGHT,
    advisor must NOT recommend moving into the right wall.
    """
    service = SnakeAIService(gemini_client=GeminiClientWrapper(api_key=""))
    advice = service.get_move_advice(
        board_width=10,
        board_height=10,
        snake_segments=[{"x": 9, "y": 5}, {"x": 8, "y": 5}, {"x": 7, "y": 5}],
        current_direction="RIGHT",
        food_pos={"x": 9, "y": 8},
    )
    # RIGHT is a wall crash, LEFT is 180 reverse, so safe choices are only UP or DOWN
    assert advice["recommended_direction"] in ["UP", "DOWN"]
    assert "RIGHT" not in advice["safe_directions"]
    assert "LEFT" not in advice["safe_directions"]


def test_commentary_procedural_fallback():
    """Verifies procedural commentary generation."""
    service = SnakeAIService(gemini_client=GeminiClientWrapper(api_key=""))
    hype = service.get_commentary(score=100, foods_eaten=8, duration_seconds=45.0, difficulty="HARD", style="hype")
    assert hype["source"] == "procedural"
    assert len(hype["commentary"]) > 5

    roast = service.get_commentary(score=10, foods_eaten=1, duration_seconds=12.0, difficulty="EASY", style="roast")
    assert roast["source"] == "procedural"
    assert len(roast["commentary"]) > 5


def test_epitaph_procedural_fallback():
    """Verifies procedural epitaph generation for fallen snakes."""
    service = SnakeAIService(gemini_client=GeminiClientWrapper(api_key=""))
    epitaph = service.generate_epitaph(
        player_name="TestHero",
        score=250,
        foods_eaten=15,
        duration_seconds=75.0,
        difficulty="HARD",
        collision_type="WALL",
    )
    assert epitaph["source"] == "procedural"
    assert "TestHero" in epitaph["title"] or "Wall" in epitaph["title"]
    assert len(epitaph["epitaph"]) > 10


def test_challenge_generator_fallback():
    """Verifies challenge generation."""
    service = SnakeAIService(gemini_client=GeminiClientWrapper(api_key=""))
    challenge = service.generate_challenge(difficulty="MEDIUM")
    assert challenge["source"] == "procedural"
    assert "challenge_title" in challenge
    assert "goal" in challenge
    assert "bonus_condition" in challenge


def test_mocked_gemini_client_success():
    """Verifies that when Gemini API responds, the response is parsed correctly."""
    mock_client = MagicMock(spec=GeminiClientWrapper)
    mock_client.is_available = True
    mock_client.generate_text.return_value = (
        "RECOMMENDED_DIRECTION: UP\n"
        "DANGER_LEVEL: LOW\n"
        "TACTICAL_TIP: Turning UP paths cleanly towards the apple.\n"
    )

    service = SnakeAIService(gemini_client=mock_client)
    advice = service.get_move_advice(
        board_width=10,
        board_height=10,
        snake_segments=[{"x": 5, "y": 5}, {"x": 4, "y": 5}],
        current_direction="RIGHT",
        food_pos={"x": 5, "y": 3},
    )
    assert advice["source"] == "gemini"
    assert advice["recommended_direction"] == "UP"
    assert advice["danger_level"] == "LOW"
    assert "apple" in advice["tactical_tip"]
