"""
Application entry point for running the Snake Game Backend Server or CLI Demo.
"""
from fastapi import FastAPI, Request

import argparse
import sys
import time

from app.core.config import settings


def run_server(host: str, port: int, reload: bool):
    """Starts the FastAPI Uvicorn server."""
    import uvicorn
    print(f"Starting Snake Game Backend Server on http://{host}:{port}")
    print(f"Interactive API Docs available at: http://{host}:{port}/docs")
    print(f"Health Check: http://{host}:{port}/health")
    uvicorn.run("app.api.server:app", host=host, port=port, reload=reload)


def run_terminal_demo():
    """
    Runs an interactive terminal game loop using pure backend engine logic.
    Demonstrates independence from any web framework or frontend.
    """
    from app.core.constants import Difficulty, Direction, GameState
    from app.engine.snake_engine import SnakeGameEngine

    print("\n" + "=" * 50)
    print("      CLASSIC SNAKE GAME - TERMINAL ENGINE DEMO")
    print("=" * 50)
    print("Controls: W=Up, S=Down, A=Left, D=Right, P=Pause/Resume, Q=Quit")
    print("Press Enter to advance auto-ticks if in non-interactive mode.\n")

    engine = SnakeGameEngine(width=15, height=10, difficulty=Difficulty.EASY)
    engine.start()

    def render_board(eng: SnakeGameEngine):
        grid = [["." for _ in range(eng.board.width)] for _ in range(eng.board.height)]

        # Render Food
        if eng.food:
            grid[eng.food.position.y][eng.food.position.x] = "★"

        # Render Snake Body
        for segment in list(eng.snake.body)[1:]:
            grid[segment.y][segment.x] = "o"

        # Render Snake Head
        head = eng.snake.head
        grid[head.y][head.x] = "O"

        border = "+" + "-" * (eng.board.width * 2 + 1) + "+"
        print("\n" + border)
        for row in grid:
            print("| " + " ".join(row) + " |")
        print(border)
        print(
            f"State: {eng.state.value} | Score: {eng.score} | "
            f"Foods: {eng.foods_eaten} | Length: {eng.snake.length} | "
            f"Direction: {eng.snake.direction.value}"
        )

    # Simple automatic 10-tick demonstration simulation
    print("Running initial simulation loop (10 ticks forward)...")
    render_board(engine)
    for step in range(1, 11):
        time.sleep(0.15)
        res = engine.tick()
        render_board(engine)
        if res.state == GameState.GAME_OVER:
            print(f"\nGame Over! Reason: {res.collision_type.value} - {res.message}")
            break

    print("\nTerminal demo completed. To launch the full HTTP API server, run:")
    print("    python main.py --serve\n")


def main():
    parser = argparse.ArgumentParser(description="Snake Game Backend Engine & Server")
    parser.add_argument("--serve", action="store_true", help="Launch FastAPI REST & WebSocket server")
    parser.add_argument("--cli", action="store_true", help="Run interactive terminal engine demo")
    parser.add_argument("--host", type=str, default=settings.HOST, help="Server host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=settings.PORT, help="Server port (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")

    args = parser.parse_args()

    if args.cli:
        run_terminal_demo()
    else:
        # Default action is running server
        run_server(host=args.host, port=args.port, reload=args.reload)
import os
import fastapi

# Ensure the variable name is explicitly 'app'
from pathlib import Path

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
app = fastapi.FastAPI()

current_dir = os.path.dirname(os.path.realpath(__file__))
static_dir = os.path.join(current_dir, "static")

app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def read_index():

    html_path = os.path.join(static_dir, "index.html")
    return FileResponse(html_path)

# If the game is just fetching data:
@app.get("/api/scores")
async def get_scores():
    return {"message": "Success", "scores": []}
    
# If the game is trying to send/save a score, add this too:
@app.post("/api/scores")
async def save_score():
    return {"message": "Score saved successfully"}

  
   
@app.post("/api/game/start")
async def start_game_endpoint():
    return {
        "session_id": "dummy-session-123",
        "status": "success",
        "game_state": {
            "board": {"width": 20, "height": 20},
            "snake": {
                "direction": "RIGHT",
                "head": {"x": 10, "y": 10},
                "segments": [{"x": 10, "y": 10}, {"x": 9, "y": 10}, {"x": 8, "y": 10}]
            },
            "food": {"position": {"x": 15, "y": 15}},
            "score": 0,
            "foods_eaten": 0,
            "difficulty": "MEDIUM",
            "duration_seconds": 0.0,
            "tick_interval_ms": 150,
            "state": "PLAYING"
        }
    }
@app.post("/api/game/move")
async def move_game_endpoint():
    # A basic dummy payload to satisfy the frontend's tick loop
    return {
        "tick": {
            "event": "MOVED",
            "head": {"x": 11, "y": 10}
        },
        "game_state": {
            "board": {"width": 20, "height": 20},
            "snake": {
                "direction": "RIGHT",
                "head": {"x": 11, "y": 10},
                "segments": [{"x": 11, "y": 10}, {"x": 10, "y": 10}, {"x": 9, "y": 10}]
            },
            "food": {"position": {"x": 15, "y": 15}},
            "score": 0,
            "foods_eaten": 0,
            "difficulty": "MEDIUM",
            "duration_seconds": 1.0,
            "tick_interval_ms": 150,
            "state": "PLAYING"
        }
    }
@app.get("/api/game/ai/challenge")
async def get_ai_challenge(difficulty: str = "EASY"):
    return {
        "challenge_title": "The First Trial",
        "goal": "Survive for 1 minute.",
        "bonus_condition": "Don't hit the walls",
        "status": "success"
    }

@app.get("/api/game/ai/status")
async def get_ai_status():
    return {"status": "online"}





if __name__ == "__main__":
    main()
