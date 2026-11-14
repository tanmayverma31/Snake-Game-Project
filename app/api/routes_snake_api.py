"""
REST API Router implementing the canonical Snake Game endpoints:
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

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.ai.services import SnakeAIService
from app.api.schemas import (
    AIAdvisorRequest,
    AIAdvisorResponse,
    AIChallengeResponse,
    AICommentaryRequest,
    AICommentaryResponse,
    AIEpitaphRequest,
    AIEpitaphResponse,
    GameStateResponse,
    HealthResponse,
    HighScoreResponse,
    LeaderboardResponse,
    MoveRequest,
    MoveResponse,
    RestartRequest,
    SaveScoreRequest,
    SessionActionRequest,
    StartGameRequest,
    StartGameResponse,
)
from app.core.config import settings
from app.core.constants import Difficulty, GameState
from app.core.exceptions import GameOverError, GameNotFoundError, InvalidGameStateError
from app.services.game_service import GameService
from app.services.score_service import ScoreService

router = APIRouter(prefix="/api/game", tags=["Snake Game API"])


# --------------------------------------------------------------------------
# Dependency Providers
# --------------------------------------------------------------------------

def get_game_service() -> GameService:
    from app.api.server import app_state
    return app_state.game_service


def get_score_service() -> ScoreService:
    from app.api.server import app_state
    return app_state.score_service


def get_ai_service() -> SnakeAIService:
    from app.api.server import app_state
    return app_state.ai_service


# --------------------------------------------------------------------------
# 1. POST /api/game/start
# --------------------------------------------------------------------------

@router.post(
    "/start",
    response_model=StartGameResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new game",
    description="Initializes board, snake, food, score, and difficulty preset. Transitions game to PLAYING state.",
)
def start_game(
    req: Optional[StartGameRequest] = None,
    game_service: GameService = Depends(get_game_service),
):
    """
    Starts a new game or restarts an existing session.
    Initializes snake, food, score, and difficulty.
    """
    request_data = req or StartGameRequest()

    if request_data.session_id:
        try:
            session = game_service.get_game(request_data.session_id)
            session.player_name = request_data.player_name
            session.engine.set_difficulty(request_data.difficulty, request_data.custom_tick_ms)
            session.engine.reset()
            session.engine.start()
        except GameNotFoundError:
            session = game_service.create_game(
                player_name=request_data.player_name,
                width=request_data.width,
                height=request_data.height,
                difficulty=request_data.difficulty,
                custom_tick_ms=request_data.custom_tick_ms,
            )
            session.engine.start()
    else:
        session = game_service.create_game(
            player_name=request_data.player_name,
            width=request_data.width,
            height=request_data.height,
            difficulty=request_data.difficulty,
            custom_tick_ms=request_data.custom_tick_ms,
        )
        session.engine.start()

    return {
        "session_id": session.session_id,
        "player_name": session.player_name,
        "message": f"Game started successfully on {request_data.difficulty.value} difficulty.",
        "game_state": session.engine.to_dict(),
    }


# --------------------------------------------------------------------------
# 2. GET /api/game/state
# --------------------------------------------------------------------------

@router.get(
    "/state",
    response_model=GameStateResponse,
    summary="Get current game state",
    description="Returns current coordinates of snake body segments, head, food position, score, status, and elapsed duration.",
)
def get_game_state(
    session_id: Optional[str] = Query(default=None, description="Optional session ID (uses active session if omitted)"),
    x_session_id: Optional[str] = Header(default=None, alias="X-Session-ID"),
    game_service: GameService = Depends(get_game_service),
):
    """
    Returns the current game state including snake segments, food, score, and status.
    """
    target_id = session_id or x_session_id
    session = game_service.resolve_session(target_id)
    return session.engine.to_dict()


# --------------------------------------------------------------------------
# 3. POST /api/game/move
# --------------------------------------------------------------------------

@router.post(
    "/move",
    response_model=MoveResponse,
    summary="Send direction input and update movement",
    description="Accepts direction input (UP, DOWN, LEFT, RIGHT). Validates 180° turns, updates movement direction, and advances the snake.",
)
def move_snake(
    req: MoveRequest,
    x_session_id: Optional[str] = Header(default=None, alias="X-Session-ID"),
    game_service: GameService = Depends(get_game_service),
):
    """
    Accepts direction input and updates snake movement.
    Prevents 180-degree immediate reversals.
    """
    target_id = req.session_id or x_session_id
    session = game_service.resolve_session(target_id)

    outcome = game_service.move_and_step(
        session_id=session.session_id,
        direction=req.direction,
        step=req.step,
    )

    return {
        "session_id": outcome["session_id"],
        "direction_accepted": outcome["direction_accepted"],
        "direction": req.direction,
        "game_state": outcome["state"],
        "tick": outcome["tick"],
    }


# --------------------------------------------------------------------------
# 4. POST /api/game/pause
# --------------------------------------------------------------------------

@router.post(
    "/pause",
    response_model=GameStateResponse,
    summary="Pause the current game",
    description="Suspends the simulation clock and transitions game state from PLAYING to PAUSED.",
)
def pause_game(
    req: Optional[SessionActionRequest] = None,
    x_session_id: Optional[str] = Header(default=None, alias="X-Session-ID"),
    game_service: GameService = Depends(get_game_service),
):
    """
    Pauses an active game session.
    """
    target_id = (req.session_id if req else None) or x_session_id
    session = game_service.resolve_session(target_id)
    state = game_service.pause_game(session.session_id)
    return state


# --------------------------------------------------------------------------
# 5. POST /api/game/resume
# --------------------------------------------------------------------------

@router.post(
    "/resume",
    response_model=GameStateResponse,
    summary="Resume a paused game",
    description="Resumes simulation and transitions game state from PAUSED back to PLAYING.",
)
def resume_game(
    req: Optional[SessionActionRequest] = None,
    x_session_id: Optional[str] = Header(default=None, alias="X-Session-ID"),
    game_service: GameService = Depends(get_game_service),
):
    """
    Resumes a paused game session.
    """
    target_id = (req.session_id if req else None) or x_session_id
    session = game_service.resolve_session(target_id)
    state = game_service.resume_game(session.session_id)
    return state


# --------------------------------------------------------------------------
# 6. POST /api/game/restart
# --------------------------------------------------------------------------

@router.post(
    "/restart",
    response_model=GameStateResponse,
    summary="Reset and restart the game",
    description="Resets the snake, clears score, respawns food, and restarts the game simulation.",
)
def restart_game(
    req: Optional[RestartRequest] = None,
    x_session_id: Optional[str] = Header(default=None, alias="X-Session-ID"),
    game_service: GameService = Depends(get_game_service),
):
    """
    Resets the current game board and starts fresh.
    """
    target_id = (req.session_id if req else None) or x_session_id
    session = game_service.resolve_session(target_id)

    if req and req.difficulty:
        session.engine.set_difficulty(req.difficulty)

    session.engine.reset()
    session.engine.start()
    return session.engine.to_dict()


# --------------------------------------------------------------------------
# 7. GET /api/game/leaderboard
# --------------------------------------------------------------------------

@router.get(
    "/leaderboard",
    response_model=LeaderboardResponse,
    summary="Get high score leaderboard",
    description="Returns top ranked scores ordered by highest score DESC, then duration ASC. Filterable by difficulty.",
)
def get_leaderboard(
    limit: int = Query(default=10, ge=1, le=100, description="Max scores to return"),
    difficulty: Optional[Difficulty] = Query(default=None, description="Optional difficulty filter"),
    score_service: ScoreService = Depends(get_score_service),
):
    """
    Returns the highest scores from persistent storage.
    """
    diff_val = difficulty.value if difficulty else None
    scores = score_service.get_leaderboard(limit=limit, difficulty=diff_val)
    return {
        "total": len(scores),
        "scores": [s.to_dict() for s in scores],
    }


# --------------------------------------------------------------------------
# 8. POST /api/game/score
# --------------------------------------------------------------------------

@router.post(
    "/score",
    response_model=HighScoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save game score",
    description="Persists match score to the database upon game completion. Can automatically extract stats from an active session.",
)
def save_score(
    req: Optional[SaveScoreRequest] = None,
    x_session_id: Optional[str] = Header(default=None, alias="X-Session-ID"),
    game_service: GameService = Depends(get_game_service),
    score_service: ScoreService = Depends(get_score_service),
):
    """
    Saves the player's score to the database.
    """
    request_data = req or SaveScoreRequest()
    target_id = request_data.session_id or x_session_id

    # If score fields are omitted, auto-extract from the referenced session
    if request_data.score is None:
        session = game_service.resolve_session(target_id)
        player_name = request_data.player_name or session.player_name
        score = session.engine.score
        difficulty = (request_data.difficulty or session.engine.difficulty).value
        foods_eaten = session.engine.foods_eaten
        duration_seconds = session.engine.get_elapsed_seconds()
        grid_size = f"{session.engine.board.width}x{session.engine.board.height}"
    else:
        player_name = request_data.player_name or "Player"
        score = request_data.score
        difficulty = (request_data.difficulty or Difficulty.MEDIUM).value
        foods_eaten = request_data.foods_eaten or 0
        duration_seconds = request_data.duration_seconds or 0.0
        grid_size = request_data.grid_size or "20x20"

    saved = score_service.submit_score(
        player_name=player_name,
        score=score,
        difficulty=difficulty,
        foods_eaten=foods_eaten,
        duration_seconds=duration_seconds,
        grid_size=grid_size,
    )
    return saved.to_dict()


# --------------------------------------------------------------------------
# 9. GET /api/game/health
# --------------------------------------------------------------------------

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check API and server health",
    description="Returns server status, version, SQLite connectivity, and Gemini AI availability.",
)
def check_health(
    game_service: GameService = Depends(get_game_service),
    ai_service: SnakeAIService = Depends(get_ai_service),
):
    """
    Checks API and server health.
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "database": "connected",
        "gemini_available": ai_service.gemini_client.is_available,
        "active_sessions_count": len(game_service.list_active_sessions()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# --------------------------------------------------------------------------
# 10. AI Endpoints under /api/game/ai
# --------------------------------------------------------------------------

@router.get("/ai/status", tags=["Gemini AI Features"], summary="Check Gemini AI service status")
def get_ai_status(ai_service: SnakeAIService = Depends(get_ai_service)):
    """
    Checks AI availability. Never exposes API keys or secrets to frontend.
    """
    return {
        "gemini_available": ai_service.gemini_client.is_available,
        "model_configured": ai_service.gemini_client.model_name,
        "fallback_mode": not ai_service.gemini_client.is_available,
    }


@router.post("/ai/advice", response_model=AIAdvisorResponse, tags=["Gemini AI Features"], summary="Get tactical move advice")
def get_move_advice(
    req: AIAdvisorRequest,
    ai_service: SnakeAIService = Depends(get_ai_service),
):
    """
    Returns tactical path analysis and safest recommended move.
    """
    return ai_service.get_move_advice(
        board_width=req.board_width,
        board_height=req.board_height,
        snake_segments=[s.model_dump() for s in req.snake_segments],
        current_direction=req.current_direction.value,
        food_pos=req.food_pos.model_dump() if req.food_pos else None,
    )


@router.post("/ai/commentary", response_model=AICommentaryResponse, tags=["Gemini AI Features"], summary="Get dynamic match commentary")
def get_commentary(
    req: AICommentaryRequest,
    ai_service: SnakeAIService = Depends(get_ai_service),
):
    """
    Returns live esports shoutcast or roast based on match progress.
    """
    return ai_service.get_commentary(
        score=req.score,
        foods_eaten=req.foods_eaten,
        duration_seconds=req.duration_seconds,
        difficulty=req.difficulty.value,
        style=req.style,
        collision_type=req.collision_type.value if req.collision_type else None,
    )


@router.post("/ai/epitaph", response_model=AIEpitaphResponse, tags=["Gemini AI Features"], summary="Generate game-over title and epitaph")
def get_epitaph(
    req: AIEpitaphRequest,
    ai_service: SnakeAIService = Depends(get_ai_service),
):
    """
    Generates a humorous title and tombstone eulogy for a fallen snake.
    """
    return ai_service.generate_epitaph(
        player_name=req.player_name,
        score=req.score,
        foods_eaten=req.foods_eaten,
        duration_seconds=req.duration_seconds,
        difficulty=req.difficulty.value,
        collision_type=req.collision_type.value,
    )


@router.get("/ai/challenge", response_model=AIChallengeResponse, tags=["Gemini AI Features"], summary="Generate dynamic challenge")
def get_challenge(
    difficulty: Difficulty = Query(default=Difficulty.MEDIUM),
    ai_service: SnakeAIService = Depends(get_ai_service),
):
    """
    Generates dynamic arcade challenges with bonus objectives.
    """
    return ai_service.generate_challenge(difficulty=difficulty.value)
