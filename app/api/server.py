"""
FastAPI application setup, lifecycle management, CORS, and centralized exception handling.
"""

from contextlib import asynccontextmanager
import logging
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.ai.gemini_client import GeminiClientWrapper
from app.ai.services import SnakeAIService
from app.api.routes_ai import router as ai_router
from app.api.routes_game import router as game_router
from app.api.routes_scores import router as scores_router
from app.api.routes_snake_api import router as snake_api_router
from app.core.config import settings
from app.core.exceptions import (
    GameOverError,
    GameNotFoundError,
    InvalidDirectionError,
    InvalidGameStateError,
    SnakeGameError,
    StorageError,
)
from app.services.game_service import GameService
from app.services.score_service import ScoreService
from app.storage.database import DatabaseManager
from app.storage.repository import SQLiteHighScoreRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("snake.api")


class ApplicationState:
    """Dependency injection state container."""
    db_manager: DatabaseManager
    score_repo: SQLiteHighScoreRepository
    score_service: ScoreService
    game_service: GameService
    gemini_client: GeminiClientWrapper
    ai_service: SnakeAIService


app_state = ApplicationState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes singletons and resources during startup."""
    logger.info("Initializing Snake Game Backend...")
    app_state.db_manager = DatabaseManager(db_path=settings.DATABASE_PATH)
    app_state.score_repo = SQLiteHighScoreRepository(db_manager=app_state.db_manager)
    app_state.score_service = ScoreService(repository=app_state.score_repo)
    app_state.game_service = GameService()
    app_state.gemini_client = GeminiClientWrapper()
    app_state.ai_service = SnakeAIService(gemini_client=app_state.gemini_client)
    logger.info("All services initialized successfully.")
    yield
    logger.info("Shutting down Snake Game Backend...")


def create_app() -> FastAPI:
    """Application factory for FastAPI."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Modular, high-performance backend game engine and persistence service for classic Snake with Gemini AI enhancements.",
        lifespan=lifespan,
    )

    # Enable CORS for frontend clients
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --------------------------------------------------------------------------
    # Centralized Exception Handlers
    # --------------------------------------------------------------------------

    @app.exception_handler(InvalidDirectionError)
    async def invalid_direction_handler(request: Request, exc: InvalidDirectionError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "InvalidDirection", "message": exc.message},
        )

    @app.exception_handler(InvalidGameStateError)
    async def invalid_game_state_handler(request: Request, exc: InvalidGameStateError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": "InvalidGameState", "message": exc.message},
        )

    @app.exception_handler(GameOverError)
    async def game_over_handler(request: Request, exc: GameOverError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "GameOver", "message": exc.message},
        )

    @app.exception_handler(GameNotFoundError)
    async def game_not_found_handler(request: Request, exc: GameNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "GameNotFound", "message": exc.message},
        )

    @app.exception_handler(StorageError)
    async def storage_error_handler(request: Request, exc: StorageError):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "StorageError", "message": exc.message},
        )

    @app.exception_handler(SnakeGameError)
    async def generic_game_error_handler(request: Request, exc: SnakeGameError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": exc.code, "message": exc.message},
        )

    # --------------------------------------------------------------------------
    # Routers
    # --------------------------------------------------------------------------

    # Static Files and Frontend UI
    static_dir = Path(__file__).parent.parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Canonical Stage 2 Game REST API (/api/game/...)
    app.include_router(snake_api_router)

    # Stage 1 API Routes (/api/v1/...)
    app.include_router(game_router, prefix=settings.API_PREFIX)
    app.include_router(scores_router, prefix=settings.API_PREFIX)
    app.include_router(ai_router, prefix=settings.API_PREFIX)

    @app.get("/play", include_in_schema=False)
    @app.get("/game", include_in_schema=False)
    def play_frontend():
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return JSONResponse({"message": "Frontend UI file not found."})

    @app.get("/health", tags=["Health"])
    def health_check():
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "database": "connected",
            "gemini_available": app_state.gemini_client.is_available if hasattr(app_state, "gemini_client") else False,
        }

    @app.get("/", tags=["Root"])
    def root(request: Request):
        accept_header = request.headers.get("accept", "")
        index_file = static_dir / "index.html"
        # If requested by a web browser, serve the game UI directly
        if "text/html" in accept_header and index_file.exists():
            return FileResponse(str(index_file))
        # Default JSON response for programmatic API consumers and health checks
        return {
            "message": "Snake Game Engine Backend API is running.",
            "docs_url": "/docs",
            "redoc_url": "/redoc",
            "health_url": "/health",
            "api_prefix": settings.API_PREFIX,
            "frontend_url": "/",
        }

    return app


app = create_app()
