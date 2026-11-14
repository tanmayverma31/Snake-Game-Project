"""
Pydantic schemas for API request validation and response models.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.core.constants import Difficulty, Direction, GameState, CollisionType


class PointSchema(BaseModel):
    x: int = Field(description="X coordinate on grid (0 = left)")
    y: int = Field(description="Y coordinate on grid (0 = top)")


class FoodSchema(BaseModel):
    position: PointSchema
    points: int = 10
    kind: str = "apple"


class SnakeSchema(BaseModel):
    head: PointSchema
    length: int
    direction: Direction
    segments: List[PointSchema]


class BoardSchema(BaseModel):
    width: int
    height: int


class GameStateResponse(BaseModel):
    state: GameState
    collision_type: CollisionType
    score: int
    foods_eaten: int
    steps_count: int
    difficulty: Difficulty
    tick_interval_ms: int
    duration_seconds: float
    board: BoardSchema
    snake: SnakeSchema
    food: Optional[FoodSchema] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "state": "PLAYING",
                "collision_type": "NONE",
                "score": 30,
                "foods_eaten": 2,
                "steps_count": 14,
                "difficulty": "MEDIUM",
                "tick_interval_ms": 130,
                "duration_seconds": 1.82,
                "board": {"width": 20, "height": 20},
                "snake": {
                    "head": {"x": 12, "y": 10},
                    "length": 5,
                    "direction": "RIGHT",
                    "segments": [
                        {"x": 12, "y": 10},
                        {"x": 11, "y": 10},
                        {"x": 10, "y": 10},
                        {"x": 9, "y": 10},
                        {"x": 8, "y": 10}
                    ]
                },
                "food": {"position": {"x": 15, "y": 10}, "points": 10, "kind": "apple"}
            }
        }
    }


class CreateGameRequest(BaseModel):
    player_name: str = Field(default="Player", min_length=1, max_length=50)
    width: int = Field(default=20, ge=6, le=100)
    height: int = Field(default=20, ge=6, le=100)
    difficulty: Difficulty = Field(default=Difficulty.MEDIUM)
    custom_tick_ms: Optional[int] = Field(default=None, ge=10, le=2000)


class CreateGameResponse(BaseModel):
    session_id: str
    player_name: str
    game_state: GameStateResponse


class StartGameRequest(BaseModel):
    player_name: str = Field(default="Player", min_length=1, max_length=50, description="Player identifier")
    difficulty: Difficulty = Field(default=Difficulty.MEDIUM, description="Speed and multiplier difficulty preset")
    width: int = Field(default=20, ge=6, le=100, description="Board width in units")
    height: int = Field(default=20, ge=6, le=100, description="Board height in units")
    custom_tick_ms: Optional[int] = Field(default=None, ge=10, le=2000, description="Custom tick ms interval")
    session_id: Optional[str] = Field(default=None, description="Optional session ID to reset/start")

    model_config = {
        "json_schema_extra": {
            "example": {
                "player_name": "ViperAce",
                "difficulty": "MEDIUM",
                "width": 20,
                "height": 20
            }
        }
    }


class StartGameResponse(BaseModel):
    session_id: str
    player_name: str
    message: str
    game_state: GameStateResponse


class DirectionRequest(BaseModel):
    direction: Direction


class DirectionResponse(BaseModel):
    accepted: bool
    direction: Direction
    current_engine_direction: Direction


class MoveRequest(BaseModel):
    direction: Direction = Field(description="Desired direction: UP, DOWN, LEFT, RIGHT")
    session_id: Optional[str] = Field(default=None, description="Target game session ID (or active session if omitted)")
    step: bool = Field(default=True, description="Whether to advance the snake by one step immediately")

    model_config = {
        "json_schema_extra": {
            "example": {
                "direction": "UP",
                "step": True
            }
        }
    }


class TickResponse(BaseModel):
    event: str
    state: GameState
    collision_type: CollisionType
    score: int
    score_delta: int
    foods_eaten: int
    snake_length: int
    head: PointSchema
    food_position: Optional[PointSchema] = None
    duration_seconds: float
    message: str


class MoveResponse(BaseModel):
    session_id: str
    direction_accepted: bool
    direction: Direction
    game_state: GameStateResponse
    tick: Optional[TickResponse] = None


class SessionActionRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="Target game session ID (or active session if omitted)")


class RestartRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="Target game session ID (or active session if omitted)")
    difficulty: Optional[Difficulty] = Field(default=None, description="Optional new difficulty setting")


class SubmitScoreRequest(BaseModel):
    player_name: str = Field(min_length=1, max_length=50)
    score: int = Field(ge=0)
    difficulty: Difficulty
    foods_eaten: int = Field(default=0, ge=0)
    duration_seconds: float = Field(default=0.0, ge=0.0)
    grid_size: str = Field(default="20x20", max_length=20)


class SaveScoreRequest(BaseModel):
    player_name: Optional[str] = Field(default=None, max_length=50, description="Player name (auto-detected if omitted)")
    score: Optional[int] = Field(default=None, ge=0, description="Score achieved (auto-detected from session if omitted)")
    difficulty: Optional[Difficulty] = Field(default=None, description="Difficulty played")
    foods_eaten: Optional[int] = Field(default=None, ge=0, description="Foods eaten")
    duration_seconds: Optional[float] = Field(default=None, ge=0.0, description="Survival duration in seconds")
    grid_size: Optional[str] = Field(default="20x20", max_length=20, description="Grid dimensions")
    session_id: Optional[str] = Field(default=None, description="Game session ID to retrieve score from")

    model_config = {
        "json_schema_extra": {
            "example": {
                "player_name": "ViperAce",
                "score": 150,
                "difficulty": "HARD",
                "foods_eaten": 8,
                "duration_seconds": 28.5,
                "grid_size": "20x20"
            }
        }
    }


class HighScoreResponse(BaseModel):
    id: Optional[int]
    player_name: str
    score: int
    difficulty: str
    foods_eaten: int
    duration_seconds: float
    grid_size: str
    created_at: Optional[str]


class LeaderboardResponse(BaseModel):
    total: int
    scores: List[HighScoreResponse]


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    gemini_available: bool
    active_sessions_count: int
    timestamp: str


# AI Request and Response schemas
class AIAdvisorRequest(BaseModel):
    board_width: int = Field(default=20, ge=4, le=100)
    board_height: int = Field(default=20, ge=4, le=100)
    snake_segments: List[PointSchema]
    current_direction: Direction
    food_pos: Optional[PointSchema] = None


class AIAdvisorResponse(BaseModel):
    recommended_direction: Direction
    danger_level: str
    tactical_tip: str
    safe_directions: List[Direction]
    source: str


class AICommentaryRequest(BaseModel):
    score: int = Field(ge=0)
    foods_eaten: int = Field(default=0, ge=0)
    duration_seconds: float = Field(default=0.0, ge=0.0)
    difficulty: Difficulty = Field(default=Difficulty.MEDIUM)
    style: str = Field(default="hype")
    collision_type: Optional[CollisionType] = None


class AICommentaryResponse(BaseModel):
    commentary: str
    style: str
    source: str


class AIEpitaphRequest(BaseModel):
    player_name: str = Field(min_length=1, max_length=50)
    score: int = Field(ge=0)
    foods_eaten: int = Field(default=0, ge=0)
    duration_seconds: float = Field(default=0.0, ge=0.0)
    difficulty: Difficulty = Field(default=Difficulty.MEDIUM)
    collision_type: CollisionType


class AIEpitaphResponse(BaseModel):
    title: str
    epitaph: str
    source: str


class AIChallengeResponse(BaseModel):
    challenge_title: str
    difficulty: str
    goal: str
    bonus_condition: str
    source: str
