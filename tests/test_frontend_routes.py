"""
Integration tests for frontend serving and static asset delivery.
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
def web_client():
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


def test_serve_html_on_browser_root(web_client):
    """Verifies that requesting / with text/html Accept header returns the HTML app."""
    res = web_client.get("/", headers={"Accept": "text/html,application/xhtml+xml"})
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "CYBER" in res.text
    assert "gameCanvas" in res.text
    assert "homeView" in res.text
    assert "gameOverModal" in res.text


def test_serve_html_on_play_route(web_client):
    """Verifies that /play returns index.html."""
    res = web_client.get("/play")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "gameCanvas" in res.text


def test_serve_static_assets(web_client):
    """Verifies that CSS and JS static assets are accessible."""
    css_res = web_client.get("/static/css/style.css")
    assert css_res.status_code == 200
    assert "--neon-green" in css_res.text

    comp_css_res = web_client.get("/static/css/components.css")
    assert comp_css_res.status_code == 200
    assert ".canvas-wrapper" in comp_css_res.text

    js_res = web_client.get("/static/js/app.js")
    assert js_res.status_code == 200
    assert "CyberSnakeApp" in js_res.text

    api_js_res = web_client.get("/static/js/api.js")
    assert api_js_res.status_code == 200
    assert "GameAPI" in api_js_res.text
