"""
Application entry point for running the Snake Game Backend Server or CLI Demo.
"""

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
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
app = fastapi.FastAPI()

current_dir = os.path.dirname(os.path.realpath(__file__))
static_dir = os.path.join(current_dir, "static")

app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def read_index():

    html_path = os.path.join(static_dir, "index.html")
    return FileResponse("static/index.html")

    return FileResponse("static/**")





if __name__ == "__main__":
    main()
