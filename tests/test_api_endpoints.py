"""
Integration tests for FastAPI REST endpoints.
"""

import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from app.api.server import app, app_state
from app.storage.database import DatabaseManager
from app.storage.repository import SQLiteHighScoreRepository
from app.services.score_service import ScoreService
from app.services.game_service import GameService
from app.ai.gemini_client import GeminiClientWrapper
from app.ai.services import SnakeAIService


@pytest.fixture(scope="module")
def client():
    """Initializes TestClient with temporary database."""
    fd, temp_db = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    app_state.db_manager = DatabaseManager(db_path=temp_db)
    app_state.score_repo = SQLiteHighScoreRepository(db_manager=app_state.db_manager)
    app_state.score_service = ScoreService(repository=app_state.score_repo)
    app_state.game_service = GameService()
    app_state.gemini_client = GeminiClientWrapper(api_key="")
    app_state.ai_service = SnakeAIService(gemini_client=app_state.gemini_client)

    with TestClient(app) as test_client:
        yield test_client

    if os.path.exists(temp_db):
        os.remove(temp_db)


def test_health_and_root(client):
    """Verifies health and root endpoints."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

    root_res = client.get("/")
    assert root_res.status_code == 200
    assert "docs_url" in root_res.json()


def test_game_lifecycle_flow(client):
    """Creates game, starts it, changes direction, advances ticks, and pauses."""
    # 1. Create game
    create_res = client.post(
        "/api/v1/game/create",
        json={"player_name": "HeroSnake", "width": 15, "height": 15, "difficulty": "MEDIUM"},
    )
    assert create_res.status_code == 201
    session_id = create_res.json()["session_id"]
    assert session_id is not None
    assert create_res.json()["game_state"]["state"] == "READY"

    # 2. Get state
    get_res = client.get(f"/api/v1/game/{session_id}")
    assert get_res.status_code == 200
    assert get_res.json()["snake"]["length"] == 3

    # 3. Start game
    start_res = client.post(f"/api/v1/game/{session_id}/start")
    assert start_res.status_code == 200
    assert start_res.json()["state"] == "PLAYING"

    # 4. Turn UP
    dir_res = client.post(f"/api/v1/game/{session_id}/direction", json={"direction": "UP"})
    assert dir_res.status_code == 200
    assert dir_res.json()["accepted"] is True

    # 5. Advance tick
    tick_res = client.post(f"/api/v1/game/{session_id}/tick")
    assert tick_res.status_code == 200
    assert tick_res.json()["state"] == "PLAYING"

    # 6. Attempt illegal 180 reverse (moving UP, turning DOWN) -> 400 Bad Request
    illegal_res = client.post(f"/api/v1/game/{session_id}/direction", json={"direction": "DOWN"})
    assert illegal_res.status_code == 400
    assert "Cannot reverse direction" in illegal_res.json()["message"]

    # 7. Pause and Resume
    pause_res = client.post(f"/api/v1/game/{session_id}/pause")
    assert pause_res.status_code == 200
    assert pause_res.json()["state"] == "PAUSED"

    resume_res = client.post(f"/api/v1/game/{session_id}/resume")
    assert resume_res.status_code == 200
    assert resume_res.json()["state"] == "PLAYING"


def test_high_scores_flow(client):
    """Submits scores and verifies leaderboard filtering and player stats."""
    # Submit scores
    client.post(
        "/api/v1/scores",
        json={
            "player_name": "Viper",
            "score": 120,
            "difficulty": "HARD",
            "foods_eaten": 6,
            "duration_seconds": 22.0,
            "grid_size": "20x20",
        },
    )
    client.post(
        "/api/v1/scores",
        json={
            "player_name": "Cobra",
            "score": 80,
            "difficulty": "MEDIUM",
            "foods_eaten": 4,
            "duration_seconds": 30.0,
            "grid_size": "20x20",
        },
    )

    # Leaderboard
    lb_res = client.get("/api/v1/scores/leaderboard")
    assert lb_res.status_code == 200
    scores = lb_res.json()["scores"]
    assert len(scores) >= 2
    assert scores[0]["score"] >= scores[1]["score"]

    # Filter by difficulty
    filtered_res = client.get("/api/v1/scores/leaderboard?difficulty=HARD")
    assert filtered_res.status_code == 200
    for s in filtered_res.json()["scores"]:
        assert s["difficulty"] == "HARD"

    # Player stats
    player_res = client.get("/api/v1/scores/player/Viper")
    assert player_res.status_code == 200
    assert player_res.json()["personal_best"]["score"] == 120


def test_ai_endpoints_without_crashing(client):
    """Verifies that all AI endpoints respond properly via fallback when no Gemini key is provided."""
    # AI Status
    status_res = client.get("/api/v1/ai/status")
    assert status_res.status_code == 200
    assert "gemini_available" in status_res.json()

    # AI Move Advice
    advice_res = client.post(
        "/api/v1/ai/advice",
        json={
            "board_width": 20,
            "board_height": 20,
            "snake_segments": [{"x": 10, "y": 10}, {"x": 9, "y": 10}],
            "current_direction": "RIGHT",
            "food_pos": {"x": 15, "y": 10},
        },
    )
    assert advice_res.status_code == 200
    assert advice_res.json()["recommended_direction"] in ["UP", "DOWN", "RIGHT"]

    # AI Commentary
    comm_res = client.post(
        "/api/v1/ai/commentary",
        json={
            "score": 50,
            "foods_eaten": 5,
            "duration_seconds": 25.0,
            "difficulty": "EASY",
            "style": "hype",
        },
    )
    assert comm_res.status_code == 200
    assert len(comm_res.json()["commentary"]) > 0

    # AI Epitaph
    epitaph_res = client.post(
        "/api/v1/ai/epitaph",
        json={
            "player_name": "Slick",
            "score": 90,
            "foods_eaten": 6,
            "duration_seconds": 40.0,
            "difficulty": "MEDIUM",
            "collision_type": "WALL",
        },
    )
    assert epitaph_res.status_code == 200
    assert "title" in epitaph_res.json()
    assert "epitaph" in epitaph_res.json()

    # AI Challenge
    chal_res = client.get("/api/v1/ai/challenge?difficulty=HARD")
    assert chal_res.status_code == 200
    assert "challenge_title" in chal_res.json()
