"""
FastAPI routes for Google Gemini AI-powered game features.
All requests are routed securely through backend endpoints without leaking API keys.
"""

from fastapi import APIRouter, Depends, Query

from app.ai.services import SnakeAIService
from app.api.schemas import (
    AIAdvisorRequest,
    AIAdvisorResponse,
    AIChallengeResponse,
    AICommentaryRequest,
    AICommentaryResponse,
    AIEpitaphRequest,
    AIEpitaphResponse,
)
from app.core.constants import Difficulty

router = APIRouter(prefix="/ai", tags=["Gemini AI Features"])


def get_ai_service() -> SnakeAIService:
    from app.api.server import app_state
    return app_state.ai_service


@router.get("/status")
def get_ai_status(ai_service: SnakeAIService = Depends(get_ai_service)):
    """
    Checks AI service availability status.
    Never exposes API keys or secrets to the client.
    """
    return {
        "gemini_available": ai_service.gemini_client.is_available,
        "model_configured": ai_service.gemini_client.model_name,
        "fallback_mode": not ai_service.gemini_client.is_available,
    }


@router.post("/advice", response_model=AIAdvisorResponse)
def get_move_advice(
    req: AIAdvisorRequest,
    ai_service: SnakeAIService = Depends(get_ai_service),
):
    """
    Provides real-time tactical advice and recommends the safest next move direction.
    """
    result = ai_service.get_move_advice(
        board_width=req.board_width,
        board_height=req.board_height,
        snake_segments=[s.model_dump() for s in req.snake_segments],
        current_direction=req.current_direction.value,
        food_pos=req.food_pos.model_dump() if req.food_pos else None,
    )
    return result


@router.post("/commentary", response_model=AICommentaryResponse)
def get_commentary(
    req: AICommentaryRequest,
    ai_service: SnakeAIService = Depends(get_ai_service),
):
    """
    Generates dynamic esports commentary or roast based on match progress.
    """
    result = ai_service.get_commentary(
        score=req.score,
        foods_eaten=req.foods_eaten,
        duration_seconds=req.duration_seconds,
        difficulty=req.difficulty.value,
        style=req.style,
        collision_type=req.collision_type.value if req.collision_type else None,
    )
    return result


@router.post("/epitaph", response_model=AIEpitaphResponse)
def get_epitaph(
    req: AIEpitaphRequest,
    ai_service: SnakeAIService = Depends(get_ai_service),
):
    """
    Generates a humorous title and tombstone eulogy for a fallen snake.
    """
    result = ai_service.generate_epitaph(
        player_name=req.player_name,
        score=req.score,
        foods_eaten=req.foods_eaten,
        duration_seconds=req.duration_seconds,
        difficulty=req.difficulty.value,
        collision_type=req.collision_type.value,
    )
    return result


@router.get("/challenge", response_model=AIChallengeResponse)
def get_challenge(
    difficulty: Difficulty = Query(default=Difficulty.MEDIUM),
    ai_service: SnakeAIService = Depends(get_ai_service),
):
    """
    Generates dynamic arcade challenges with bonus modifiers.
    """
    result = ai_service.generate_challenge(difficulty=difficulty.value)
    return result
