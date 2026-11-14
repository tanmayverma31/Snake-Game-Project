"""
High-level AI services powering in-game commentary, tactical move advice,
game-over epitaphs, and dynamic challenges using Gemini with safe local fallbacks.
"""

import json
import logging
import random
from typing import Any, Dict, List, Optional

from app.ai.gemini_client import GeminiClientWrapper
from app.ai.prompts import (
    CHALLENGE_SYSTEM,
    COMMENTARY_SYSTEM,
    EPITAPH_SYSTEM,
    MOVE_ADVISOR_SYSTEM,
)
from app.core.constants import Direction
from app.engine.models import Board, Point, Snake

logger = logging.getLogger("snake.ai.services")


class SnakeAIService:
    """
    Unified AI service layer offering AI features to the game backend.
    Gracefully degrades to heuristic / procedural methods when Gemini is unavailable.
    """

    def __init__(self, gemini_client: Optional[GeminiClientWrapper] = None):
        self.gemini_client = gemini_client or GeminiClientWrapper()

    # --------------------------------------------------------------------------
    # 1. Tactical Move Advisor
    # --------------------------------------------------------------------------

    def get_move_advice(
        self,
        board_width: int,
        board_height: int,
        snake_segments: List[Dict[str, int]],
        current_direction: str,
        food_pos: Optional[Dict[str, int]],
    ) -> Dict[str, Any]:
        """
        Analyzes the current board state and recommends the optimal next direction.
        """
        # Parse inputs into domain representations
        board = Board(width=board_width, height=board_height)
        points = [Point(s["x"], s["y"]) for s in snake_segments]
        curr_dir = Direction(current_direction)
        snake = Snake(initial_segments=points, initial_direction=curr_dir)
        food_point = Point(food_pos["x"], food_pos["y"]) if food_pos else None

        # Determine immediately safe moves (no 180 reverse, no wall, no self-collision)
        safe_directions = self._get_safe_directions(board, snake, curr_dir)

        # Fallback heuristic recommendation
        heuristic_direction = self._calculate_heuristic_best_direction(
            safe_directions, snake.head, food_point, curr_dir
        )
        danger_level = "CRITICAL" if not safe_directions else ("HIGH" if len(safe_directions) == 1 else "LOW")

        # Attempt Gemini AI analysis if client is ready
        if self.gemini_client.is_available:
            prompt = (
                f"Board: {board_width}x{board_height}\n"
                f"Snake Head: ({snake.head.x}, {snake.head.y})\n"
                f"Snake Length: {snake.length}\n"
                f"Current Direction: {curr_dir.value}\n"
                f"Food Position: ({food_point.x}, {food_point.y}) if food_point else 'None'\n"
                f"Currently Safe Directions: {[d.value for d in safe_directions]}\n"
                f"Body Segments: {[(p.x, p.y) for p in points[:5]]} (showing first 5)\n"
            )

            raw_ai = self.gemini_client.generate_text(prompt, system_instruction=MOVE_ADVISOR_SYSTEM)
            if raw_ai:
                parsed = self._parse_advisor_response(raw_ai, safe_directions, heuristic_direction)
                if parsed:
                    return {**parsed, "source": "gemini"}

        # Heuristic fallback if AI is unavailable or fails
        tip = "Navigate towards the food while preserving open escape corridors."
        if danger_level == "CRITICAL":
            tip = "Trap imminent! No completely safe path detected."
        elif danger_level == "HIGH":
            tip = "Narrow path! Only one safe turning angle remaining."

        return {
            "recommended_direction": heuristic_direction.value if heuristic_direction else curr_dir.value,
            "danger_level": danger_level,
            "tactical_tip": tip,
            "safe_directions": [d.value for d in safe_directions],
            "source": "heuristic",
        }

    def _get_safe_directions(self, board: Board, snake: Snake, curr_dir: Direction) -> List[Direction]:
        safe = []
        for direction in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
            if direction.is_opposite_of(curr_dir):
                continue
            next_head = snake.head.move(direction)
            if not board.is_within_bounds(next_head):
                continue
            if snake.occupies_body_excluding_tail(next_head):
                continue
            safe.append(direction)
        return safe

    def _calculate_heuristic_best_direction(
        self,
        safe_directions: List[Direction],
        head: Point,
        food: Optional[Point],
        curr_dir: Direction,
    ) -> Optional[Direction]:
        if not safe_directions:
            return None
        if not food:
            return safe_directions[0]

        # Prioritize direction minimizing Manhattan distance to food
        def distance_to_food(d: Direction) -> int:
            nh = head.move(d)
            return abs(nh.x - food.x) + abs(nh.y - food.y)

        # Sort safe directions by distance to food
        sorted_dirs = sorted(safe_directions, key=distance_to_food)
        return sorted_dirs[0]

    def _parse_advisor_response(
        self, raw_text: str, safe_directions: List[Direction], fallback_dir: Optional[Direction]
    ) -> Optional[Dict[str, Any]]:
        try:
            lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
            rec_dir = fallback_dir.value if fallback_dir else "UP"
            danger = "LOW"
            tip = "Keep moving strategically."

            for line in lines:
                if line.startswith("RECOMMENDED_DIRECTION:"):
                    candidate = line.split(":", 1)[1].strip().upper()
                    # Validate that AI didn't recommend a suicidal or illegal direction
                    if any(candidate == d.value for d in safe_directions):
                        rec_dir = candidate
                elif line.startswith("DANGER_LEVEL:"):
                    danger = line.split(":", 1)[1].strip().upper()
                elif line.startswith("TACTICAL_TIP:"):
                    tip = line.split(":", 1)[1].strip()

            return {
                "recommended_direction": rec_dir,
                "danger_level": danger,
                "tactical_tip": tip,
                "safe_directions": [d.value for d in safe_directions],
            }
        except Exception:
            return None

    # --------------------------------------------------------------------------
    # 2. Dynamic Commentary / Esports Announcer
    # --------------------------------------------------------------------------

    def get_commentary(
        self,
        score: int,
        foods_eaten: int,
        duration_seconds: float,
        difficulty: str,
        style: str = "hype",
        collision_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates in-game commentary or post-game shoutcasting.
        """
        if self.gemini_client.is_available:
            prompt = (
                f"Style: {style}\n"
                f"Current Score: {score}\n"
                f"Foods Eaten: {foods_eaten}\n"
                f"Time Alive: {duration_seconds:.1f} seconds\n"
                f"Difficulty: {difficulty}\n"
                f"Collision: {collision_type or 'None (Game Active)'}\n"
            )
            raw_ai = self.gemini_client.generate_text(prompt, system_instruction=COMMENTARY_SYSTEM)
            if raw_ai:
                return {
                    "commentary": raw_ai.strip().strip('"'),
                    "style": style,
                    "source": "gemini",
                }

        # Procedural fallback quotes
        procedural_quotes = {
            "hype": [
                f"Incredible rhythm! Score is sitting at {score} with {foods_eaten} snacks swallowed!",
                "Look at those razor-sharp turns! The serpent is in full flow!",
                f"Precision slithering! {duration_seconds:.0f} seconds of absolute mastery!",
            ],
            "roast": [
                "Careful now, that tail looks appetizing even to you!",
                "The walls aren't going to move out of your way, you know!",
                "A little close to comfort on that turn! Sweaty palms already?",
            ],
            "zen": [
                "Breathe. Flow like the river, bend like the bamboo.",
                f"At {score} points, clarity of mind creates boundless space.",
            ],
        }

        quotes = procedural_quotes.get(style, procedural_quotes["hype"])
        selected = random.choice(quotes)
        if collision_type and collision_type != "NONE":
            selected = f"And that's game! Finished with {score} points after a {collision_type.lower()} impact."

        return {
            "commentary": selected,
            "style": style,
            "source": "procedural",
        }

    # --------------------------------------------------------------------------
    # 3. Game-Over Epitaph & Title Generator
    # --------------------------------------------------------------------------

    def generate_epitaph(
        self,
        player_name: str,
        score: int,
        foods_eaten: int,
        duration_seconds: float,
        difficulty: str,
        collision_type: str,
    ) -> Dict[str, str]:
        """
        Generates a humorous title and tombstone eulogy for a fallen snake.
        """
        if self.gemini_client.is_available:
            prompt = (
                f"Player: {player_name}\n"
                f"Final Score: {score}\n"
                f"Snacks Eaten: {foods_eaten}\n"
                f"Duration: {duration_seconds:.1f}s\n"
                f"Difficulty: {difficulty}\n"
                f"Cause of Death: {collision_type}\n"
            )
            raw_ai = self.gemini_client.generate_text(prompt, system_instruction=EPITAPH_SYSTEM)
            if raw_ai:
                title = "The Gallant Slitherer"
                epitaph = f"Fell honourably with {score} points."
                for line in raw_ai.splitlines():
                    if line.startswith("TITLE:"):
                        title = line.split(":", 1)[1].strip()
                    elif line.startswith("EPITAPH:"):
                        epitaph = line.split(":", 1)[1].strip()
                return {"title": title, "epitaph": epitaph, "source": "gemini"}

        # Procedural fallback
        titles = {
            "WALL": [
                f"{player_name} the Wall Enthusiast",
                f"{player_name} the Architectural Inspector",
                f"{player_name} the Concrete Kisser",
            ],
            "SELF": [
                f"{player_name} the Tail Nibbler",
                f"{player_name} the Ouroboros Impostor",
                f"{player_name} the Knot Tier",
            ],
        }
        chosen_title = random.choice(titles.get(collision_type, [f"Sir Slithers of {player_name}"]))
        epitaph = f"Here lies {chosen_title}, who scored {score} points and devoured {foods_eaten} apples before destiny struck."

        return {
            "title": chosen_title,
            "epitaph": epitaph,
            "source": "procedural",
        }

    # --------------------------------------------------------------------------
    # 4. Quest & Challenge Generator
    # --------------------------------------------------------------------------

    def generate_challenge(self, difficulty: str = "MEDIUM") -> Dict[str, Any]:
        """
        Generates dynamic game challenges with specific targets and modifiers.
        """
        if self.gemini_client.is_available:
            prompt = f"Target Difficulty: {difficulty}"
            raw_ai = self.gemini_client.generate_text(prompt, system_instruction=CHALLENGE_SYSTEM)
            if raw_ai:
                title = "Serpent's Trial"
                goal = "Reach 100 points."
                bonus = "No wall bumps."
                for line in raw_ai.splitlines():
                    if line.startswith("CHALLENGE_TITLE:"):
                        title = line.split(":", 1)[1].strip()
                    elif line.startswith("GOAL:"):
                        goal = line.split(":", 1)[1].strip()
                    elif line.startswith("BONUS_CONDITION:"):
                        bonus = line.split(":", 1)[1].strip()
                return {
                    "challenge_title": title,
                    "difficulty": difficulty,
                    "goal": goal,
                    "bonus_condition": bonus,
                    "source": "gemini",
                }

        # Fallback challenges
        fallbacks = [
            {
                "challenge_title": "Speed Demon Trial",
                "difficulty": difficulty,
                "goal": "Score 150 points in under 60 seconds.",
                "bonus_condition": "Never turn twice in the same direction within 2 seconds.",
            },
            {
                "challenge_title": "Perimeter Patrol",
                "difficulty": difficulty,
                "goal": "Eat 10 foods while touching the board perimeter at least once between meals.",
                "bonus_condition": "Maintain speed without pausing.",
            },
        ]
        chosen = random.choice(fallbacks)
        return {**chosen, "source": "procedural"}
