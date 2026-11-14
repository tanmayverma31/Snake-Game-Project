"""
FastAPI routes for Game Session management and game engine interactions.
"""

import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status

from app.api.schemas import (
    CreateGameRequest,
    CreateGameResponse,
    DirectionRequest,
    DirectionResponse,
    GameStateResponse,
    TickResponse,
)
from app.core.constants import Direction, GameState
from app.core.exceptions import (
    GameOverError,
    GameNotFoundError,
    InvalidDirectionError,
    InvalidGameStateError,
)
from app.services.game_service import GameService

router = APIRouter(prefix="/game", tags=["Game Engine"])


def get_game_service() -> GameService:
    """Dependency provider for game service singleton."""
    from app.api.server import app_state
    return app_state.game_service


@router.post("/create", response_model=CreateGameResponse, status_code=status.HTTP_201_CREATED)
def create_game(
    req: CreateGameRequest,
    service: GameService = Depends(get_game_service),
):
    """Creates a new game session with specified settings."""
    session = service.create_game(
        player_name=req.player_name,
        width=req.width,
        height=req.height,
        difficulty=req.difficulty,
        custom_tick_ms=req.custom_tick_ms,
    )
    return {
        "session_id": session.session_id,
        "player_name": session.player_name,
        "game_state": session.engine.to_dict(),
    }


@router.get("/{session_id}", response_model=GameStateResponse)
def get_game_state(
    session_id: str,
    service: GameService = Depends(get_game_service),
):
    """Retrieves full snapshot of game state."""
    session = service.get_game(session_id)
    return session.engine.to_dict()


@router.post("/{session_id}/start", response_model=GameStateResponse)
def start_game(
    session_id: str,
    service: GameService = Depends(get_game_service),
):
    """Transitions game state from READY/GAME_OVER to PLAYING."""
    return service.start_game(session_id)


@router.post("/{session_id}/pause", response_model=GameStateResponse)
def pause_game(
    session_id: str,
    service: GameService = Depends(get_game_service),
):
    """Pauses an active game session."""
    return service.pause_game(session_id)


@router.post("/{session_id}/resume", response_model=GameStateResponse)
def resume_game(
    session_id: str,
    service: GameService = Depends(get_game_service),
):
    """Resumes a paused game session."""
    return service.resume_game(session_id)


@router.post("/{session_id}/reset", response_model=GameStateResponse)
def reset_game(
    session_id: str,
    service: GameService = Depends(get_game_service),
):
    """Resets game board and state back to READY."""
    return service.reset_game(session_id)


@router.post("/{session_id}/direction", response_model=DirectionResponse)
def change_direction(
    session_id: str,
    req: DirectionRequest,
    service: GameService = Depends(get_game_service),
):
    """Submits a direction change (UP, DOWN, LEFT, RIGHT)."""
    return service.change_direction(session_id, req.direction)


@router.post("/{session_id}/tick", response_model=TickResponse)
def tick_game(
    session_id: str,
    service: GameService = Depends(get_game_service),
):
    """Executes a single game tick and returns the outcome."""
    result = service.tick_game(session_id)
    return result.to_dict()


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_game(
    session_id: str,
    service: GameService = Depends(get_game_service),
):
    """Destroys an active game session."""
    if not service.delete_game(session_id):
        raise GameNotFoundError(f"Game session '{session_id}' not found.")
    return None


@router.websocket("/{session_id}/ws")
async def game_websocket_stream(
    websocket: WebSocket,
    session_id: str,
    service: GameService = Depends(get_game_service),
):
    """
    WebSocket endpoint for real-time game stream.
    Receives directional inputs: {"direction": "UP"}
    Streams game tick state at engine difficulty tick interval.
    """
    await websocket.accept()
    try:
        session = service.get_game(session_id)
    except GameNotFoundError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Game session not found.")
        return

    # Background task to listen for incoming client commands (e.g. direction change, pause)
    async def receive_commands():
        try:
            while True:
                data = await websocket.receive_json()
                if "direction" in data:
                    try:
                        d = Direction(data["direction"].upper())
                        session.engine.change_direction(d)
                    except (ValueError, InvalidDirectionError):
                        pass
                elif data.get("action") == "pause":
                    session.engine.pause()
                elif data.get("action") == "resume":
                    session.engine.resume()
                elif data.get("action") == "start":
                    session.engine.start()
        except WebSocketDisconnect:
            pass

    cmd_task = asyncio.create_task(receive_commands())

    try:
        while True:
            interval_sec = session.engine.tick_interval_ms / 1000.0
            await asyncio.sleep(interval_sec)

            if session.engine.state == GameState.PLAYING:
                tick_res = session.engine.tick()
                await websocket.send_json({
                    "type": "tick",
                    "tick": tick_res.to_dict(),
                    "state": session.engine.to_dict(),
                })
                if tick_res.state == GameState.GAME_OVER:
                    break
            else:
                # Send heartbeat/state ping if paused or ready
                await websocket.send_json({
                    "type": "state_update",
                    "state": session.engine.to_dict(),
                })
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    finally:
        cmd_task.cancel()
