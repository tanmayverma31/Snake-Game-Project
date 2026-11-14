"""
Unit tests for high score persistent storage (SQLite repository).
"""

import tempfile
import os
import pytest

from app.storage.database import DatabaseManager
from app.storage.models import HighScoreRecord
from app.storage.repository import SQLiteHighScoreRepository


@pytest.fixture
def repo():
    """Provides a fresh isolated SQLite database repository for testing."""
    fd, temp_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_manager = DatabaseManager(db_path=temp_path)
    repository = SQLiteHighScoreRepository(db_manager=db_manager)
    yield repository
    if os.path.exists(temp_path):
        os.remove(temp_path)


def test_save_and_retrieve_score(repo):
    """Verifies that scores can be persisted and returned with generated IDs."""
    record = HighScoreRecord(
        player_name="Alice",
        score=150,
        difficulty="HARD",
        foods_eaten=10,
        duration_seconds=32.5,
    )
    saved = repo.save(record)
    assert saved.id is not None
    assert saved.id > 0
    assert saved.player_name == "Alice"
    assert saved.score == 150


def test_leaderboard_ordering(repo):
    """Verifies leaderboard orders primarily by score DESC and secondarily by duration ASC."""
    repo.save(HighScoreRecord(player_name="PlayerLow", score=50, difficulty="EASY", duration_seconds=10.0))
    repo.save(HighScoreRecord(player_name="PlayerHigh", score=200, difficulty="EASY", duration_seconds=40.0))
    repo.save(HighScoreRecord(player_name="PlayerFast", score=200, difficulty="EASY", duration_seconds=25.0))

    top = repo.get_top(limit=10)
    assert len(top) == 3
    # Top score 200 with shorter duration 25.0 should be first
    assert top[0].player_name == "PlayerFast"
    assert top[0].score == 200
    assert top[1].player_name == "PlayerHigh"
    assert top[1].score == 200
    assert top[2].player_name == "PlayerLow"
    assert top[2].score == 50


def test_leaderboard_difficulty_filter(repo):
    """Verifies filtering by difficulty preset."""
    repo.save(HighScoreRecord(player_name="EasyPlayer", score=100, difficulty="EASY"))
    repo.save(HighScoreRecord(player_name="HardPlayer", score=100, difficulty="HARD"))

    easy_scores = repo.get_top(limit=10, difficulty="EASY")
    assert len(easy_scores) == 1
    assert easy_scores[0].player_name == "EasyPlayer"

    hard_scores = repo.get_top(limit=10, difficulty="HARD")
    assert len(hard_scores) == 1
    assert hard_scores[0].player_name == "HardPlayer"


def test_player_best_and_history(repo):
    """Verifies personal best retrieval."""
    repo.save(HighScoreRecord(player_name="Bob", score=40, difficulty="MEDIUM"))
    repo.save(HighScoreRecord(player_name="Bob", score=180, difficulty="MEDIUM"))
    repo.save(HighScoreRecord(player_name="Bob", score=90, difficulty="MEDIUM"))
    repo.save(HighScoreRecord(player_name="Charlie", score=300, difficulty="MEDIUM"))

    best = repo.get_player_best("Bob")
    assert best is not None
    assert best.score == 180

    history = repo.get_player_history("Bob", limit=5)
    assert len(history) == 3

    non_existent = repo.get_player_best("Ghost")
    assert non_existent is None


def test_invalid_score_record_validation():
    """Ensures negative values are rejected by the data model."""
    with pytest.raises(ValueError):
        HighScoreRecord(player_name="Bad", score=-10)

    with pytest.raises(ValueError):
        HighScoreRecord(player_name="Bad", score=10, foods_eaten=-1)

    with pytest.raises(ValueError):
        HighScoreRecord(player_name="Bad", score=10, duration_seconds=-5.0)
