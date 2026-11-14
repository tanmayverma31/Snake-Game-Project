"""
Comprehensive integration tests for the Stage 2 Snake Game REST API endpoints:
- POST /api/game/start
- GET  /api/game/state
- POST /api/game/move
- POST /api/game/pause
- POST /api/game/resume
- POST /api/game/restart
- GET  /api/game/leaderboard
- POST /api/game/score
- GET  /api/game/health
- Plus secure backend Gemini AI endpoints (/api/game/ai/...)
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
def api_client():
    """Initializes TestClient with isolated test database."""
    fd, temp_db = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    app_state.db_manager = DatabaseManager(db_path=temp_db)
    app_state.score_repo = SQLiteHighScoreRepository(db_manager=app_state.db_manager)
    app_state.score_service = ScoreService(repository=app_state.score_repo)
    app_state.game_service = GameService()
    app_state.gemini_client = GeminiClientWrapper(api_key="")
    app_state.ai_service = SnakeAIService(gemini_client=app_state.gemini_client)

    with TestClient(app) as client:
        yield client

    if os.path.exists(temp_db):
        os.remove(temp_db)


# --------------------------------------------------------------------------
# 1. POST /api/game/start
# --------------------------------------------------------------------------

def test_api_start_game(api_client):
    """Verifies starting a new game initializes board, snake, food, score, and difficulty."""
    payload = {
        "player_name": "TestPlayer",
        "difficulty": "HARD",
        "width": 16,
        "height": 16,
    }
    res = api_client.post("/api/game/start", json=payload)
    assert res.status_code == 201

    data = res.json()
    assert "session_id" in data
    assert data["player_name"] == "TestPlayer"
    state = data["game_state"]
    assert state["state"] == "PLAYING"
    assert state["score"] == 0
    assert state["foods_eaten"] == 0
    assert state["difficulty"] == "HARD"
    assert state["board"] == {"width": 16, "height": 16}
    assert state["snake"]["length"] == 3
    assert state["snake"]["direction"] == "RIGHT"
    assert state["food"] is not None
    assert "position" in state["food"]


# --------------------------------------------------------------------------
# 2. GET /api/game/state
# --------------------------------------------------------------------------

def test_api_get_game_state(api_client):
    """Verifies retrieving current game state."""
    # Ensure game has started
    start_res = api_client.post("/api/game/start", json={"player_name": "StateViewer"})
    session_id = start_res.json()["session_id"]

    res = api_client.get(f"/api/game/state?session_id={session_id}")
    assert res.status_code == 200

    state = res.json()
    assert state["state"] == "PLAYING"
    assert len(state["snake"]["segments"]) == 3
    assert "head" in state["snake"]
    assert "food" in state
    assert state["score"] == 0


# --------------------------------------------------------------------------
# 3. POST /api/game/move
# --------------------------------------------------------------------------

def test_api_move_snake_valid_and_invalid(api_client):
    """Verifies sending directional input and updating snake movement."""
    # Start fresh session (snake moving RIGHT initially)
    start_res = api_client.post("/api/game/start", json={"player_name": "Mover"})
    session_id = start_res.json()["session_id"]

    # 1. Turn UP (valid 90° turn)
    move_res = api_client.post(
        "/api/game/move",
        json={"direction": "UP", "session_id": session_id, "step": True},
    )
    assert move_res.status_code == 200
    move_data = move_res.json()
    assert move_data["direction_accepted"] is True
    assert move_data["direction"] == "UP"
    assert move_data["game_state"]["snake"]["direction"] == "UP"

    # 2. Turn DOWN while moving UP -> Invalid 180° reverse -> 400 Bad Request
    invalid_res = api_client.post(
        "/api/game/move",
        json={"direction": "DOWN", "session_id": session_id, "step": True},
    )
    assert invalid_res.status_code == 400
    err_data = invalid_res.json()
    assert err_data["error"] == "InvalidDirection"
    assert "Cannot reverse direction" in err_data["message"]


# --------------------------------------------------------------------------
# 4. POST /api/game/pause
# --------------------------------------------------------------------------

def test_api_pause_game(api_client):
    """Verifies pausing an active game."""
    start_res = api_client.post("/api/game/start")
    session_id = start_res.json()["session_id"]

    pause_res = api_client.post("/api/game/pause", json={"session_id": session_id})
    assert pause_res.status_code == 200
    assert pause_res.json()["state"] == "PAUSED"

    # Repeating pause when already paused raises 409 Conflict
    dup_pause = api_client.post("/api/game/pause", json={"session_id": session_id})
    assert dup_pause.status_code == 409


# --------------------------------------------------------------------------
# 5. POST /api/game/resume
# --------------------------------------------------------------------------

def test_api_resume_game(api_client):
    """Verifies resuming a paused game."""
    start_res = api_client.post("/api/game/start")
    session_id = start_res.json()["session_id"]

    api_client.post("/api/game/pause", json={"session_id": session_id})
    resume_res = api_client.post("/api/game/resume", json={"session_id": session_id})
    assert resume_res.status_code == 200
    assert resume_res.json()["state"] == "PLAYING"


# --------------------------------------------------------------------------
# 6. POST /api/game/restart
# --------------------------------------------------------------------------

def test_api_restart_game(api_client):
    """Verifies resetting and restarting game."""
    start_res = api_client.post("/api/game/start", json={"difficulty": "EASY"})
    session_id = start_res.json()["session_id"]

    restart_res = api_client.post(
        "/api/game/restart",
        json={"session_id": session_id, "difficulty": "HARD"},
    )
    assert restart_res.status_code == 200
    restarted_state = restart_res.json()
    assert restarted_state["state"] == "PLAYING"
    assert restarted_state["difficulty"] == "HARD"
    assert restarted_state["score"] == 0
    assert restarted_state["snake"]["length"] == 3


# --------------------------------------------------------------------------
# 7. POST /api/game/score & GET /api/game/leaderboard
# --------------------------------------------------------------------------

def test_api_score_and_leaderboard(api_client):
    """Verifies saving scores and retrieving the leaderboard."""
    # Submit 2 scores
    score1_res = api_client.post(
        "/api/game/score",
        json={
            "player_name": "AlphaSnake",
            "score": 150,
            "difficulty": "HARD",
            "foods_eaten": 8,
            "duration_seconds": 30.5,
            "grid_size": "20x20",
        },
    )
    assert score1_res.status_code == 201
    assert score1_res.json()["id"] is not None

    score2_res = api_client.post(
        "/api/game/score",
        json={
            "player_name": "BetaSnake",
            "score": 250,
            "difficulty": "HARD",
            "foods_eaten": 12,
            "duration_seconds": 45.0,
            "grid_size": "20x20",
        },
    )
    assert score2_res.status_code == 201

    # Leaderboard test
    lb_res = api_client.get("/api/game/leaderboard?difficulty=HARD")
    assert lb_res.status_code == 200
    data = lb_res.json()
    assert data["total"] >= 2
    # BetaSnake (250) should be ranked higher than AlphaSnake (150)
    scores = [s["player_name"] for s in data["scores"]]
    assert scores.index("BetaSnake") < scores.index("AlphaSnake")


# --------------------------------------------------------------------------
# 8. GET /api/game/health
# --------------------------------------------------------------------------

def test_api_health(api_client):
    """Verifies health endpoint reports status and database connectivity."""
    res = api_client.get("/api/game/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "version" in data
    assert "gemini_available" in data
    assert "timestamp" in data


# --------------------------------------------------------------------------
# 9. Gemini AI Endpoints (/api/game/ai/...)
# --------------------------------------------------------------------------

def test_api_ai_endpoints(api_client):
    """Verifies AI endpoints under /api/game/ai operate cleanly in fallback mode."""
    # AI Status
    status_res = api_client.get("/api/game/ai/status")
    assert status_res.status_code == 200
    assert "gemini_available" in status_res.json()

    # Move Advice
    advice_res = api_client.post(
        "/api/game/ai/advice",
        json={
            "board_width": 20,
            "board_height": 20,
            "snake_segments": [{"x": 10, "y": 10}, {"x": 9, "y": 10}, {"x": 8, "y": 10}],
            "current_direction": "RIGHT",
            "food_pos": {"x": 10, "y": 15},
        },
    )
    assert advice_res.status_code == 200
    assert advice_res.json()["recommended_direction"] in ["UP", "DOWN", "RIGHT"]

    # Commentary
    comm_res = api_client.post(
        "/api/game/ai/commentary",
        json={
            "score": 100,
            "foods_eaten": 6,
            "duration_seconds": 32.0,
            "difficulty": "MEDIUM",
            "style": "hype",
        },
    )
    assert comm_res.status_code == 200
    assert len(comm_res.json()["commentary"]) > 0

    # Epitaph
    epitaph_res = api_client.post(
        "/api/game/ai/epitaph",
        json={
            "player_name": "GhostRider",
            "score": 180,
            "foods_eaten": 10,
            "duration_seconds": 55.0,
            "difficulty": "HARD",
            "collision_type": "SELF",
        },
    )
    assert epitaph_res.status_code == 200
    assert "GhostRider" in epitaph_res.json()["title"]

    # Challenge
    chal_res = api_client.get("/api/game/ai/challenge?difficulty=EXPERT")
    assert chal_res.status_code == 200
    assert "challenge_title" in chal_res.json()
