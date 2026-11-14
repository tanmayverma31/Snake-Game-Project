/**
 * API Service Client for CyberSnake Arcade.
 * Directly integrates with Stage 2 REST APIs:
 * - POST /api/game/start
 * - GET  /api/game/state
 * - POST /api/game/move
 * - POST /api/game/pause
 * - POST /api/game/resume
 * - POST /api/game/restart
 * - GET  /api/game/leaderboard
 * - POST /api/game/score
 * - GET  /api/game/health
 * - POST /api/game/ai/...
 */

const BASE_URL = window.location.origin;

class GameAPI {
  /**
   * Universal fetch helper with error and timeout handling.
   */
  static async request(endpoint, options = {}) {
    const url = `${BASE_URL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    };

    const config = {
      ...options,
      headers,
    };

   try {
    // 1. Instantly fix the path if it accidentally contains localhost
    url = url.replace("http://localhost:8000", "").replace("http://127.0.0.1:8000", "");

    const response = await fetch(url, config);
    const isJson = (response.headers.get('content-type') || '').includes('application/json');
    const data = isJson ? await response.json() : await response.text();

    if (!response.ok) {
        // 2. Pop up an alert on your screen with the exact missing URL
        alert("Vercel is missing this exact route: " + url);
        
        const errorMsg = (typeof data === 'object' && data.message) ? data.message : response.statusText;
        const err = new Error(errorMsg);
        err.status = response.status;
        err.data = data;
        throw err;
    }
    return data;
    }
     catch (err) {
      console.warn(`[GameAPI] Request error on ${endpoint}:`, err.message);
      throw err;
      }
  }

  // --- Core Game APIs ---

   static async startGame({ playerName = 'Player', difficulty = 'MEDIUM', width = 20, height = 20 } = {}) {
    return this.request('/api/game/start', {
      method: 'POST',
      body: JSON.stringify({
        player_name: playerName,
        difficulty,
        width,
        height,
      }),
    });
  }

  static async getGameState(sessionId) {
    const q = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
    return this.request(`/api/game/state${q}`, {
      method: 'GET',
    });
  }

  static async moveSnake({ direction, sessionId, step = true }) {
    return this.request('/api/game/move', {
      method: 'POST',
      body: JSON.stringify({
        direction,
        session_id: sessionId,
        step,
      }),
    });
  }

  static async pauseGame(sessionId) {
    return this.request('/api/game/pause', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    });
  }

  static async resumeGame(sessionId) {
    return this.request('/api/game/resume', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    });
  }

  static async restartGame(sessionId, difficulty = null) {
    return this.request('/api/game/restart', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        difficulty,
      }),
    });
  }

  // --- Persistence & Leaderboard APIs ---

  static async saveScore({ playerName, score, difficulty, foodsEaten, durationSeconds, gridSize = '20x20', sessionId = null }) {
    return this.request('/api/game/score', {
      method: 'POST',
      body: JSON.stringify({
        player_name: playerName,
        score,
        difficulty,
        foods_eaten: foodsEaten,
        duration_seconds: durationSeconds,
        grid_size: gridSize,
        session_id: sessionId,
      }),
    });
  }

  static async getLeaderboard({ limit = 15, difficulty = null } = {}) {
    let q = `?limit=${limit}`;
    if (difficulty && difficulty !== 'ALL') {
      q += `&difficulty=${encodeURIComponent(difficulty)}`;
    }
    return this.request(`/api/game/leaderboard${q}`, {
      method: 'GET',
    });
  }

  static async getHealth() {
    return this.request('/api/game/health', {
      method: 'GET',
    });
  }

  // --- Google Gemini AI APIs ---

  static async getAIStatus() {
    return this.request('/api/game/ai/status', {
      method: 'GET',
    });
  }

  static async getAIMoveAdvice({ boardWidth, boardHeight, snakeSegments, currentDirection, foodPos }) {
    return this.request('/api/game/ai/advice', {
      method: 'POST',
      body: JSON.stringify({
        board_width: boardWidth,
        board_height: boardHeight,
        snake_segments: snakeSegments,
        current_direction: currentDirection,
        food_pos: foodPos,
      }),
    });
  }

  static async getAICommentary({ score, foodsEaten, durationSeconds, difficulty, style = 'hype', collisionType = null }) {
    return this.request('/api/game/ai/commentary', {
      method: 'POST',
      body: JSON.stringify({
        score,
        foods_eaten: foodsEaten,
        duration_seconds: durationSeconds,
        difficulty,
        style,
        collision_type: collisionType,
      }),
    });
  }

  static async getAIEpitaph({ playerName, score, foodsEaten, durationSeconds, difficulty, collisionType }) {
    return this.request('/api/game/ai/epitaph', {
      method: 'POST',
      body: JSON.stringify({
        player_name: playerName,
        score,
        foods_eaten: foodsEaten,
        duration_seconds: durationSeconds,
        difficulty,
        collision_type: collisionType,
      }),
    });
  }

  static async getAIChallenge(difficulty = 'MEDIUM') {
    return this.request(`/api/game/ai/challenge?difficulty=${encodeURIComponent(difficulty)}`, {
      method: 'GET',
    });
  }
}

export default GameAPI;
