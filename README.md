# CyberSnake Arcade | Full-Stack Snake Game & Engine

A modern, high-performance arcade Snake Game built with a decoupled Python engine, **FastAPI REST API**, **SQLite persistence**, **Google Gemini AI** enhancements (`google-genai`), and a cyber-arcade frontend interface.

---

## 1. System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        BROWSER FRONTEND (SPA)                          │
│  • Modern Arcade Theme (Dark, Neon Green Snake, Glowing Food)          │
│  • High-DPI Canvas 2D Renderer with Screen Shake & Sparkle Particles    │
│  • Web Audio API Synthesizer (Zero asset dependencies)                 │
│  • Responsive Layouts: Desktop, Tablet, Mobile (Swipes & D-Pad)        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP REST & WebSockets
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        FASTAPI REST API LAYER                          │
│  • /api/game/start, /state, /move, /pause, /resume, /restart           │
│  • /api/game/leaderboard, /score, /health                              │
│  • /api/game/ai/advice, /commentary, /epitaph, /challenge, /status     │
│  • Centralized Exception Handling & CORS                               │
└──────────────┬────────────────────┬────────────────────┬───────────────┘
               │                    │                    │
               ▼                    ▼                    ▼
     ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
     │ PURE GAME ENGINE │ │ SQLITE DATABASE  │ │ GOOGLE GEMINI AI │
     │ • Snake Movement │ │ • Leaderboards   │ │ • Tactical Advice│
     │ • 180° Turn Lock │ │ • Player History │ │ • Live Commentary│
     │ • Wall & Tail Hit│ │ • ACID Storage   │ │ • Death Epitaphs │
     │ • Difficulty/Tick│ │ • Indexed Queries│ │ • Daily Quests   │
     └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## 2. Project Folder Structure

```
practice/
├── app/
│   ├── core/
│   │   ├── config.py              # Configuration & environment variables
│   │   ├── constants.py           # Enums: Direction, GameState, Difficulty, CollisionType
│   │   └── exceptions.py          # Domain exceptions (InvalidDirectionError, GameOverError, etc.)
│   ├── engine/
│   │   ├── models.py              # Point, Snake, Food, Board models
│   │   ├── snake_engine.py        # Pure tick-based SnakeGameEngine
│   │   └── spawner.py             # Random and Deterministic FoodSpawner strategies
│   ├── storage/
│   │   ├── database.py            # SQLite schema manager & connection pool
│   │   ├── models.py              # HighScoreRecord model with validation
│   │   └── repository.py          # HighScoreRepository interface & SQLite implementation
│   ├── ai/
│   │   ├── gemini_client.py       # Wrapper for official google-genai SDK
│   │   ├── prompts.py             # System prompts for commentary, advice, epitaphs
│   │   └── services.py            # AI features with graceful heuristic fallbacks
│   ├── services/
│   │   ├── game_service.py        # In-memory game session manager (multi-session support)
│   │   └── score_service.py       # Leaderboard and score validation service
│   └── api/
│       ├── schemas.py             # Pydantic request & response schemas
│       ├── routes_snake_api.py    # Canonical REST API endpoints (/api/game/...)
│       ├── routes_game.py         # Session & WebSocket routes (/api/v1/game/...)
│       ├── routes_scores.py       # Leaderboard routes (/api/v1/scores/...)
│       ├── routes_ai.py           # AI routes (/api/v1/ai/...)
│       └── server.py              # FastAPI app, static mounting, CORS & exception handlers
├── static/
│   ├── index.html                 # Main Single Page Application interface
│   ├── css/
│   │   ├── style.css              # Cyberpunk theme, variables, typography, glow effects
│   │   └── components.css         # HUD, modals, difficulty cards, D-pad, table styling
│   └── js/
│       ├── api.js                 # API client wrapper connecting to /api/game/...
│       ├── audio.js               # Web Audio API 8-bit arcade synthesizer
│       ├── particles.js           # Particle emitter for neon food sparks and explosions
│       ├── canvas.js              # High-DPI canvas renderer: snake eyes, food glow, grid
│       ├── controls.js            # WASD, Arrow keys, mobile touch/swipe, virtual D-pad
│       └── app.js                 # Main UI controller, game loop, modals & AI triggers
├── tests/
│   ├── test_frontend_routes.py    # Tests for static assets and HTML delivery
│   ├── test_stage2_game_api.py    # Integration tests for /api/game/... REST endpoints
│   ├── test_engine_movement.py    # Unit tests: movement, turns, 180° reverse rejection
│   ├── test_engine_collision.py   # Unit tests: wall collisions, self collision, tail safety
│   ├── test_engine_scoring.py     # Unit tests: food eating, score multipliers, growth
│   ├── test_engine_states.py      # Unit tests: ready, playing, paused, game over, transitions
│   ├── test_repository.py         # Unit tests: SQLite storage, ranking, player history
│   ├── test_ai_service.py         # Unit tests: Gemini client, fallback heuristics, parsing
│   └── test_api_endpoints.py      # Integration tests: FastAPI endpoints with TestClient
├── schema.sql                     # SQLite schema definition and indexes
├── requirements.txt               # Dependencies
├── main.py                        # Server and terminal CLI demo entry point
└── README.md                      # Documentation
```

---

## 3. Frontend UI/UX Design

### Visual Design
- **Dark Theme**: Charcoal/black `#07080d` background with subtle ambient cyan and green radial glow blobs and a 40px cyberpunk grid overlay.
- **Neon Green Snake**: Vibrant lime `#00ff88` with radiant drop-shadow blur. Body segments have a gradient spine dot, and the head features stylized forward-facing eyes with directional pupils.
- **Glowing Ruby Food**: Pulsating ruby `#ff2a5f` jewel with multi-ring radiant aura and an animated breath pulse.
- **Arcade Typography**: Google Fonts `Orbitron` for headings and scores; `Inter` for crisp, readable UI text and leaderboards.
- **Particle System**: Burst of neon sparkle particles when food is eaten; shockwave and spark fragments upon collision.
- **Web Audio API Synth**: Authentic retro 8-bit audio synthesized via JavaScript with zero external audio assets. Mute/unmute preferences persist in `localStorage`.

### Main UI Screens & Components
1. **Home Screen**:
   - Pilot codename input.
   - Interactive difficulty cards:
     - `EASY` (200ms / 1.0x score)
     - `MEDIUM` (130ms / 1.5x score — recommended)
     - `HARD` (80ms / 2.0x score)
     - `EXPERT` (50ms / 3.0x score)
   - Personal best score readout.
   - AI Daily Challenge trial card (fetched live from `/api/game/ai/challenge`).
   - "LAUNCH MISSION" primary action button.
2. **Game Screen**:
   - Glassmorphic HUD: Live Score, Personal Best, Food Eaten, Difficulty badge.
   - Score pop animation on food consumption.
   - AI Tactical Hint button (`H` / click): Opens live tactical recommendation and danger meter.
   - Pause button (`Space` / `P`) and In-Game Restart button (`R`).
   - Live Commentary Ticker: Dynamic esports commentary powered by Gemini.
   - Responsive Canvas: Auto-fits desktop monitors, tablets, and phones.
   - Virtual D-Pad: Tactile touch controls for mobile screens.
3. **Game Over Screen**:
   - Terminal status and exact collision reason.
   - Stats grid: Final Score, Personal Best, Foods Eaten, Survival Time.
   - New High Score celebration banner with audio fanfare.
   - AI Eulogy Card: Generates an epitaph and title for the fallen serpent (e.g. *"ViperAce the Concrete Kisser"*).
   - Instant persistence to SQLite database via `POST /api/game/score`.
   - Play Again, Leaderboard, and Home buttons.
4. **Leaderboard Modal**:
   - Global ranking table with medals (🥇, 🥈, 🥉).
   - Filter tabs: `ALL`, `EASY`, `MEDIUM`, `HARD`, `EXPERT`.
   - Displays Player Name, Score, Difficulty, Foods, and Duration.
   - Pilot's personal best footer.

---

## 4. Gameplay Controls

| Control Method | Action |
|---|---|
| **Arrow Keys** | Move `UP`, `DOWN`, `LEFT`, `RIGHT` |
| **WASD Keys** | Move `W` (Up), `S` (Down), `A` (Left), `D` (Right) |
| **Mobile Touch** | Swipe in any direction on the canvas |
| **Virtual D-Pad** | Tap on-screen directional buttons (visible on mobile) |
| **Spacebar / P** | Pause / Resume game |
| **Key R** | Quick Restart |
| **Key H** | Request Gemini AI Tactical Move Hint |
| **Key M** | Mute / Unmute Arcade Sound |

*180-degree reverse turns into the snake's own body are filtered client-side for zero latency and validated authoritatively by the backend.*

---

## 5. Google Gemini AI Features

- **Dedicated Service Layer**: Integrated via the official `google-genai` SDK in [app/ai/gemini_client.py](file:///f:/practice/app/ai/gemini_client.py).
- **Security**: The API key is read strictly from `GEMINI_API_KEY` in backend environment variables. No secrets are ever exposed to the client.
- **Resilience**: If Gemini is unconfigured or rate-limited, all AI endpoints automatically fall back to deterministic local algorithms (obstacle-avoidance pathfinding and procedural text) without interrupting gameplay.
- **Endpoints**:
  - `POST /api/game/ai/advice`: Tactical path analysis and recommended direction.
  - `POST /api/game/ai/commentary`: Live esports shoutcasts or roasts.
  - `POST /api/game/ai/epitaph`: Game-over epitaph and title generation.
  - `GET /api/game/ai/challenge`: Daily arcade challenges with bonus constraints.
  - `GET /api/game/ai/status`: Health check for AI capabilities.

---

## 6. Setup & Execution Instructions

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Modern web browser (Chrome, Firefox, Safari, Edge)

### 1. Installation
Install backend dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
To enable Google Gemini AI features:
```powershell
# Windows PowerShell
$env:GEMINI_API_KEY="your-gemini-api-key"

# Linux / macOS
export GEMINI_API_KEY="your-gemini-api-key"
```
*(If omitted, all features operate normally in heuristic fallback mode).*

### 3. Run Automated Tests
Execute the complete test suite (49 tests across engine mechanics, repository, REST endpoints, and frontend delivery):
```bash
python -m pytest -v
```

### 4. Run the Full Application
Start the server:
```bash
python main.py --serve --port 8000
```

Open your browser and navigate to:
- **Play the Game**: [http://localhost:8000/](http://localhost:8000/) or [http://localhost:8000/play](http://localhost:8000/play)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/api/game/health](http://localhost:8000/api/game/health)
