"""
Game session manager coordinating active snake game instances.
"""

from dataclasses import dataclass
import time
from typing import Any, Dict, List, Optional
import uuid

from app.core.constants import Difficulty, Direction, GameState
from app.core.exceptions import GameNotFoundError
from app.engine.snake_engine import SnakeGameEngine, TickResult
from app.engine.spawner import FoodSpawner


@dataclass
class GameSession:
    """Metadata and engine instance for a game session."""
    session_id: str
    engine: SnakeGameEngine
    player_name: str
    created_at: float
    last_active_at: float

    def touch(self) -> None:
        self.last_active_at = time.time()


class GameService:
    """
    Service coordinating active game sessions in memory.
    Thread-safe session storage and cleanup.
    """

    def __init__(self, session_ttl_seconds: float = 3600.0):
        self._sessions: Dict[str, GameSession] = {}
        self.session_ttl_seconds = session_ttl_seconds

    def create_game(
        self,
        player_name: str = "Player",
        width: int = 20,
        height: int = 20,
        difficulty: Difficulty = Difficulty.MEDIUM,
        custom_tick_ms: Optional[int] = None,
        food_spawner: Optional[FoodSpawner] = None,
    ) -> GameSession:
        """Instantiates a new snake game session."""
        self._cleanup_stale_sessions()
        session_id = str(uuid.uuid4())
        engine = SnakeGameEngine(
            width=width,
            height=height,
            difficulty=difficulty,
            custom_tick_ms=custom_tick_ms,
            food_spawner=food_spawner,
        )
        now = time.time()
        session = GameSession(
            session_id=session_id,
            engine=engine,
            player_name=player_name.strip() or "Player",
            created_at=now,
            last_active_at=now,
        )
        self._sessions[session_id] = session
        return session

    def get_game(self, session_id: str) -> GameSession:
        """Retrieves an active game session or raises GameNotFoundError."""
        session = self._sessions.get(session_id)
        if not session:
            raise GameNotFoundError(f"Game session '{session_id}' not found or has expired.")
        session.touch()
        return session

    def start_game(self, session_id: str) -> dict:
        """Starts the specified game session."""
        session = self.get_game(session_id)
        session.engine.start()
        return session.engine.to_dict()

    def pause_game(self, session_id: str) -> dict:
        """Pauses the specified game session."""
        session = self.get_game(session_id)
        session.engine.pause()
        return session.engine.to_dict()

    def resume_game(self, session_id: str) -> dict:
        """Resumes the specified game session."""
        session = self.get_game(session_id)
        session.engine.resume()
        return session.engine.to_dict()

    def reset_game(self, session_id: str) -> dict:
        """Resets the specified game session."""
        session = self.get_game(session_id)
        session.engine.reset()
        return session.engine.to_dict()

    def change_direction(self, session_id: str, direction: Direction) -> dict:
        """Queues a direction change for the specified session."""
        session = self.get_game(session_id)
        accepted = session.engine.change_direction(direction)
        return {
            "accepted": accepted,
            "direction": direction.value,
            "current_engine_direction": session.engine.snake.direction.value,
        }

    def tick_game(self, session_id: str) -> TickResult:
        """Executes a single simulation tick for the specified session."""
        session = self.get_game(session_id)
        return session.engine.tick()

    def get_or_create_default_session(self) -> GameSession:
        """Returns the most recent active session, or creates a default one if none exists."""
        self._cleanup_stale_sessions()
        if self._sessions:
            latest = max(self._sessions.values(), key=lambda s: s.last_active_at)
            latest.touch()
            return latest
        return self.create_game(player_name="Player", difficulty=Difficulty.MEDIUM)

    def resolve_session(self, session_id: Optional[str] = None) -> GameSession:
        """Resolves a session by ID if provided, otherwise falls back to default session."""
        if session_id:
            return self.get_game(session_id)
        return self.get_or_create_default_session()

    def move_and_step(
        self,
        session_id: str,
        direction: Direction,
        step: bool = True,
    ) -> Dict[str, Any]:
        """
        Applies a direction turn, and optionally advances the snake movement.
        Returns the updated game state along with tick outcome details.
        """
        session = self.get_game(session_id)
        # If in READY state, moving automatically starts the game
        if session.engine.state == GameState.READY:
            session.engine.start()

        accepted = session.engine.change_direction(direction)
        tick_result = None
        if step and session.engine.state == GameState.PLAYING:
            tick_result = session.engine.tick()

        state_dict = session.engine.to_dict()
        return {
            "session_id": session.session_id,
            "direction_accepted": accepted,
            "direction": direction.value,
            "state": state_dict,
            "tick": tick_result.to_dict() if tick_result else None,
        }

    def delete_game(self, session_id: str) -> bool:
        """Removes a session from memory."""
        return self._sessions.pop(session_id, None) is not None

    def list_active_sessions(self) -> List[str]:
        """Returns list of currently active session IDs."""
        self._cleanup_stale_sessions()
        return list(self._sessions.keys())

    def _cleanup_stale_sessions(self) -> None:
        """Removes inactive sessions exceeding the TTL."""
        now = time.time()
        expired = [
            sid
            for sid, s in self._sessions.items()
            if (now - s.last_active_at) > self.session_ttl_seconds
        ]
        for sid in expired:
            del self._sessions[sid]
