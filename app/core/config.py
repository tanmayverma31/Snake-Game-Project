"""
Application configuration loaded from environment variables with safe defaults.
"""

import os
from pathlib import Path
from pydantic import BaseModel, Field


class Settings(BaseModel):
    # Application Info
    APP_NAME: str = "Classic Snake Game Backend Engine"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = Field(default=False)

    # Server Host / Port
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Game Engine Defaults
    DEFAULT_BOARD_WIDTH: int = 20
    DEFAULT_BOARD_HEIGHT: int = 20
    MIN_BOARD_DIMENSION: int = 8
    MAX_BOARD_DIMENSION: int = 100
    BASE_FOOD_POINTS: int = 10

    # Persistence
    DATABASE_PATH: str = Field(
        default_factory=lambda: os.getenv("SNAKE_DB_PATH", str(Path(__file__).parent.parent.parent / "snake_scores.db"))
    )

    # Gemini AI Integration
    # Read API key securely from environment variable (never hardcoded, never exposed to frontend)
    GEMINI_API_KEY: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    GEMINI_MODEL: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-4-hydrogen"))
    GEMINI_TIMEOUT_SECONDS: float = Field(default=8.0)
    AI_ENABLED: bool = Field(default_factory=lambda: bool(os.getenv("GEMINI_API_KEY", "")))


# Global singleton settings instance
settings = Settings()
