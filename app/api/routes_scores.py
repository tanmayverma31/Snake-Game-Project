"""
FastAPI routes for High Score storage and leaderboard retrieval.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.api.schemas import HighScoreResponse, LeaderboardResponse, SubmitScoreRequest
from app.core.constants import Difficulty
from app.services.score_service import ScoreService

router = APIRouter(prefix="/scores", tags=["High Scores & Leaderboard"])


def get_score_service() -> ScoreService:
    from app.api.server import app_state
    return app_state.score_service


@router.post("", response_model=HighScoreResponse, status_code=status.HTTP_201_CREATED)
def submit_score(
    req: SubmitScoreRequest,
    service: ScoreService = Depends(get_score_service),
):
    """Submits and persists a completed game score."""
    record = service.submit_score(
        player_name=req.player_name,
        score=req.score,
        difficulty=req.difficulty.value,
        foods_eaten=req.foods_eaten,
        duration_seconds=req.duration_seconds,
        grid_size=req.grid_size,
    )
    return record.to_dict()


@router.get("/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(
    limit: int = Query(default=10, ge=1, le=100),
    difficulty: Optional[Difficulty] = Query(default=None),
    service: ScoreService = Depends(get_score_service),
):
    """Retrieves top scores, optionally filtered by difficulty preset."""
    diff_val = difficulty.value if difficulty else None
    scores = service.get_leaderboard(limit=limit, difficulty=diff_val)
    return {
        "total": len(scores),
        "scores": [s.to_dict() for s in scores],
    }


@router.get("/player/{player_name}")
def get_player_stats(
    player_name: str,
    service: ScoreService = Depends(get_score_service),
):
    """Retrieves personal best and recent match history for a given player."""
    best = service.get_player_best(player_name)
    history = service.get_player_history(player_name, limit=5)
    return {
        "player_name": player_name,
        "personal_best": best.to_dict() if best else None,
        "recent_history": [h.to_dict() for h in history],
    }
