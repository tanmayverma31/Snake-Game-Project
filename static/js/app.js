/**
 * CyberSnake Arcade - Main Application Coordinator.
 * Connects the Modern UI, Canvas Renderer, Controls, Audio, and Particles
 * directly to the Stage 2 REST APIs and Google Gemini AI services.
 */

import GameAPI from './api.js';
import SoundManager from './audio.js';
import { GameCanvasRenderer } from './canvas.js';
import { ControlsManager } from './controls.js';

class CyberSnakeApp {
  constructor() {
    // Game State
    this.sessionId = null;
    this.playerName = localStorage.getItem('cybersnake_pilot') || 'ViperAce';
    this.difficulty = localStorage.getItem('cybersnake_diff') || 'MEDIUM';
    this.personalBest = parseInt(localStorage.getItem('cybersnake_best') || '0', 10);
    
    this.gameState = null;
    this.gameLoopTimer = null;
    this.isTicking = false;
    this.isPaused = false;
    this.isGameOver = false;

    this.pendingDirection = 'RIGHT';

    // DOM Elements
    this.initDOMElements();

    // Canvas Renderer
    this.renderer = new GameCanvasRenderer(this.dom.gameCanvas);

    // Controls
    this.controls = new ControlsManager({
      onDirectionChange: (dir) => this.handleDirectionInput(dir),
      onPauseToggle: () => this.togglePause(),
      onRestart: () => this.restartGame(),
      onAIHint: () => this.requestAIHint(),
      onSoundToggle: () => this.toggleSound(),
    });

    // Setup Listeners and Initial Data
    this.initEventListeners();
    this.updateInitialUI();
    this.checkAIStatus();
    this.loadDailyChallenge();
  }

  initDOMElements() {
    this.dom = {
      // Views
      homeView: document.getElementById('homeView'),
      gameView: document.getElementById('gameView'),

      // Modals & Overlays
      pauseOverlay: document.getElementById('pauseOverlay'),
      gameOverModal: document.getElementById('gameOverModal'),
      leaderboardModal: document.getElementById('leaderboardModal'),

      // Canvas
      gameCanvas: document.getElementById('gameCanvas'),

      // Inputs & Buttons
      playerNameInput: document.getElementById('playerNameInput'),
      diffCards: document.querySelectorAll('.diff-card'),
      playBtn: document.getElementById('playBtn'),
      homeBestScore: document.getElementById('homeBestScore'),
      openLeaderboardBtn: document.getElementById('openLeaderboardBtn'),
      closeLeaderboardBtn: document.getElementById('closeLeaderboardBtn'),
      soundToggleBtn: document.getElementById('soundToggleBtn'),
      aiStatusBadge: document.getElementById('aiStatusBadge'),

      // HUD Elements
      hudScore: document.getElementById('hudScore'),
      hudBest: document.getElementById('hudBest'),
      hudFoods: document.getElementById('hudFoods'),
      hudDiff: document.getElementById('hudDiff'),
      pauseBtn: document.getElementById('pauseBtn'),
      inGameRestartBtn: document.getElementById('inGameRestartBtn'),
      aiHintBtn: document.getElementById('aiHintBtn'),

      // AI Hint Banner
      aiHintBanner: document.getElementById('aiHintBanner'),
      hintRecDirection: document.getElementById('hintRecDirection'),
      hintDangerLevel: document.getElementById('hintDangerLevel'),
      hintTip: document.getElementById('hintTip'),
      closeHintBtn: document.getElementById('closeHintBtn'),

      // Pause Overlay Buttons
      resumeBtn: document.getElementById('resumeBtn'),
      pauseRestartBtn: document.getElementById('pauseRestartBtn'),
      quitHomeBtn: document.getElementById('quitHomeBtn'),

      // Commentary
      commentaryText: document.getElementById('commentaryText'),

      // Game Over Stats
      gameOverReason: document.getElementById('gameOverReason'),
      finalScoreVal: document.getElementById('finalScoreVal'),
      finalBestVal: document.getElementById('finalBestVal'),
      finalFoodsVal: document.getElementById('finalFoodsVal'),
      finalTimeVal: document.getElementById('finalTimeVal'),
      newHighScoreAlert: document.getElementById('newHighScoreAlert'),
      epitaphTitle: document.getElementById('epitaphTitle'),
      epitaphText: document.getElementById('epitaphText'),
      playAgainBtn: document.getElementById('playAgainBtn'),
      viewLeaderboardFromGameOver: document.getElementById('viewLeaderboardFromGameOver'),
      returnHomeFromGameOver: document.getElementById('returnHomeFromGameOver'),

      // Leaderboard
      leaderboardTabs: document.querySelectorAll('.tab-btn'),
      leaderboardBody: document.getElementById('leaderboardBody'),
      statsPlayerName: document.getElementById('statsPlayerName'),
      statsPersonalBestScore: document.getElementById('statsPersonalBestScore'),

      // Challenge Card
      challengeTitle: document.getElementById('challengeTitle'),
      challengeGoal: document.getElementById('challengeGoal'),
      challengeBonus: document.getElementById('challengeBonus'),
      refreshChallengeBtn: document.getElementById('refreshChallengeBtn'),

      // Toast
      toastContainer: document.getElementById('toastContainer'),
    };
  }

  updateInitialUI() {
    this.dom.playerNameInput.value = this.playerName;
    this.dom.homeBestScore.textContent = `${this.personalBest} PTS`;
    this.dom.hudBest.textContent = this.personalBest;

    // Difficulty card active state
    this.dom.diffCards.forEach((card) => {
      if (card.dataset.diff === this.difficulty) {
        card.classList.add('active');
      } else {
        card.classList.remove('active');
      }
    });

    this.updateSoundButtonUI();
  }

  initEventListeners() {
    // Player Name Change
    this.dom.playerNameInput.addEventListener('input', (e) => {
      this.playerName = e.target.value.trim() || 'Player';
      localStorage.setItem('cybersnake_pilot', this.playerName);
    });

    // Difficulty Selection
    this.dom.diffCards.forEach((card) => {
      card.addEventListener('click', () => {
        this.dom.diffCards.forEach((c) => c.classList.remove('active'));
        card.classList.add('active');
        this.difficulty = card.dataset.diff;
        localStorage.setItem('cybersnake_diff', this.difficulty);
      });
    });

    // Play Launch
    this.dom.playBtn.addEventListener('click', () => this.startNewGame());

    // In-game controls
    this.dom.pauseBtn.addEventListener('click', () => this.togglePause());
    this.dom.inGameRestartBtn.addEventListener('click', () => this.restartGame());
    this.dom.aiHintBtn.addEventListener('click', () => this.requestAIHint());
    this.dom.closeHintBtn.addEventListener('click', () => {
      this.dom.aiHintBanner.classList.add('hidden');
    });

    // Pause overlay buttons
    this.dom.resumeBtn.addEventListener('click', () => this.togglePause());
    this.dom.pauseRestartBtn.addEventListener('click', () => {
      this.dom.pauseOverlay.classList.add('hidden');
      this.restartGame();
    });
    this.dom.quitHomeBtn.addEventListener('click', () => this.returnToHome());

    // Game Over buttons
    this.dom.playAgainBtn.addEventListener('click', () => {
      this.dom.gameOverModal.classList.add('hidden');
      this.startNewGame();
    });
    this.dom.viewLeaderboardFromGameOver.addEventListener('click', () => {
      this.dom.gameOverModal.classList.add('hidden');
      this.openLeaderboard();
    });
    this.dom.returnHomeFromGameOver.addEventListener('click', () => {
      this.dom.gameOverModal.classList.add('hidden');
      this.returnToHome();
    });

    // Leaderboard
    this.dom.openLeaderboardBtn.addEventListener('click', () => this.openLeaderboard());
    this.dom.closeLeaderboardBtn.addEventListener('click', () => {
      this.dom.leaderboardModal.classList.add('hidden');
    });

    this.dom.leaderboardTabs.forEach((tab) => {
      tab.addEventListener('click', () => {
        this.dom.leaderboardTabs.forEach((t) => t.classList.remove('active'));
        tab.classList.add('active');
        this.loadLeaderboardData(tab.dataset.tab);
      });
    });

    // Sound Toggle
    this.dom.soundToggleBtn.addEventListener('click', () => this.toggleSound());

    // Refresh Challenge
    this.dom.refreshChallengeBtn.addEventListener('click', () => this.loadDailyChallenge());
  }

  showToast(message, duration = 3000) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    this.dom.toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.remove();
    }, duration);
  }

  toggleSound() {
    const isMuted = SoundManager.toggleMute();
    this.updateSoundButtonUI();
    this.showToast(isMuted ? '🔇 Audio Muted' : '🔊 Audio Active');
  }

  updateSoundButtonUI() {
    const isMuted = SoundManager.isMuted();
    this.dom.soundToggleBtn.querySelector('.icon').textContent = isMuted ? '🔇' : '🔊';
  }

  switchView(viewName) {
    if (viewName === 'game') {
      this.dom.homeView.classList.remove('active-view');
      this.dom.gameView.classList.add('active-view');
      this.renderer.resizeCanvas();
    } else {
      this.dom.gameView.classList.remove('active-view');
      this.dom.homeView.classList.add('active-view');
    }
  }

  // ==========================================================================
  // Core Game Flow (REST API Integration)
  // ==========================================================================

  async startNewGame() {
    this.switchView('game');
    this.isPaused = false;
    this.isGameOver = false;
    this.dom.pauseOverlay.classList.add('hidden');
    this.dom.gameOverModal.classList.add('hidden');
    this.dom.aiHintBanner.classList.add('hidden');
    this.dom.commentaryText.textContent = `Simulation initialized on ${this.difficulty} speed. Good luck.`;

    try {
      const resp = await GameAPI.startGame({
        playerName: this.playerName,
        difficulty: this.difficulty,
        width: 20,
        height: 20,
      });

      this.sessionId = resp.session_id;
      this.gameState = resp.game_state;
      this.pendingDirection = this.gameState.snake.direction;
      this.controls.setDirection(this.pendingDirection);

      this.renderer.setBoardDimensions(this.gameState.board.width, this.gameState.board.height);
      this.updateHUD(this.gameState);
      this.renderer.render(this.gameState);

      this.startTickLoop(this.gameState.tick_interval_ms);
      SoundManager.playTurn();
    } catch (err) {
      this.showToast(`Failed to initialize game: ${err.message}`);
      this.returnToHome();
    }
  }

  startTickLoop(intervalMs) {
    this.stopTickLoop();
    this.gameLoopTimer = setInterval(() => this.tick(), intervalMs);
  }

  stopTickLoop() {
    if (this.gameLoopTimer) {
      clearInterval(this.gameLoopTimer);
      this.gameLoopTimer = null;
    }
  }

  handleDirectionInput(newDirection) {
    if (this.isPaused || this.isGameOver) return;
    this.pendingDirection = newDirection;
    SoundManager.playTurn();
  }

  async tick() {
    if (this.isTicking || this.isPaused || this.isGameOver || !this.sessionId) return;
    this.isTicking = true;

    try {
      // Send move to Stage 2 REST API: POST /api/game/move
      const outcome = await GameAPI.moveSnake({
        direction: this.pendingDirection,
        sessionId: this.sessionId,
        step: true,
      });

      const previousScore = this.gameState ? this.gameState.score : 0;
      this.gameState = outcome.game_state;
      this.controls.setDirection(this.gameState.snake.direction);

      // 1. Food Consumption Check
      if (outcome.tick && outcome.tick.event === 'FOOD_EATEN') {
        SoundManager.playEat();
        if (this.gameState.food) {
          const cell = this.renderer.cellSize;
          const fx = outcome.tick.head.x * cell + cell / 2;
          const fy = outcome.tick.head.y * cell + cell / 2;
          this.renderer.particleEmitter.emitFoodSparkles(fx, fy, '#00ff88', 16);
        }

        // Trigger score pop animation
        this.dom.hudScore.classList.add('pop-score');
        setTimeout(() => this.dom.hudScore.classList.remove('pop-score'), 300);

        // Fetch occasional commentary every 2 foods
        if (this.gameState.foods_eaten % 2 === 0) {
          this.fetchLiveCommentary();
        }
      }

      // 2. Collision / Game Over Check
      if (this.gameState.state === 'GAME_OVER') {
        this.handleGameOver(outcome.tick);
      }

      this.updateHUD(this.gameState);
      this.renderer.render(this.gameState);
    } catch (err) {
      console.error('Tick execution error:', err);
    } finally {
      this.isTicking = false;
    }
  }

  async togglePause() {
    if (this.isGameOver || !this.sessionId) return;

    if (this.isPaused) {
      // Resume
      try {
        const state = await GameAPI.resumeGame(this.sessionId);
        this.gameState = state;
        this.isPaused = false;
        this.dom.pauseOverlay.classList.add('hidden');
        this.startTickLoop(this.gameState.tick_interval_ms);
        SoundManager.playTurn();
        this.showToast('Game Resumed');
      } catch (err) {
        this.showToast(`Resume failed: ${err.message}`);
      }
    } else {
      // Pause
      try {
        const state = await GameAPI.pauseGame(this.sessionId);
        this.gameState = state;
        this.isPaused = true;
        this.stopTickLoop();
        this.dom.pauseOverlay.classList.remove('hidden');
        SoundManager.playTurn();
        this.showToast('Game Paused');
      } catch (err) {
        this.showToast(`Pause failed: ${err.message}`);
      }
    }
  }

  async restartGame() {
    if (!this.sessionId) return;
    this.stopTickLoop();
    this.dom.pauseOverlay.classList.add('hidden');
    this.dom.gameOverModal.classList.add('hidden');
    this.dom.aiHintBanner.classList.add('hidden');

    try {
      const state = await GameAPI.restartGame(this.sessionId, this.difficulty);
      this.gameState = state;
      this.isPaused = false;
      this.isGameOver = false;
      this.pendingDirection = this.gameState.snake.direction;
      this.controls.setDirection(this.pendingDirection);

      this.updateHUD(this.gameState);
      this.renderer.render(this.gameState);
      this.startTickLoop(this.gameState.tick_interval_ms);
      SoundManager.playTurn();
      this.showToast('Game Restarted');
    } catch (err) {
      this.showToast(`Restart failed: ${err.message}`);
    }
  }

  async handleGameOver(tickData) {
    this.isGameOver = true;
    this.stopTickLoop();

    SoundManager.playGameOver();
    this.renderer.triggerScreenShake(12);

    // Spawn explosion particles at snake head
    if (this.gameState && this.gameState.snake && this.gameState.snake.head) {
      const cell = this.renderer.cellSize;
      const hx = this.gameState.snake.head.x * cell + cell / 2;
      const hy = this.gameState.snake.head.y * cell + cell / 2;
      this.renderer.particleEmitter.emitCollisionExplosion(hx, hy, 28);
    }

    const finalScore = this.gameState.score;
    const isNewBest = finalScore > this.personalBest;

    if (isNewBest) {
      this.personalBest = finalScore;
      localStorage.setItem('cybersnake_best', this.personalBest);
      this.dom.homeBestScore.textContent = `${this.personalBest} PTS`;
      this.dom.hudBest.textContent = this.personalBest;
      this.dom.newHighScoreAlert.classList.remove('hidden');
      SoundManager.playHighscoreFanfare();
    } else {
      this.dom.newHighScoreAlert.classList.add('hidden');
    }

    // Populate Game Over Modal
    const reasonText = tickData ? tickData.message : 'Snake encountered a lethal collision.';
    this.dom.gameOverReason.textContent = reasonText;
    this.dom.finalScoreVal.textContent = finalScore;
    this.dom.finalBestVal.textContent = this.personalBest;
    this.dom.finalFoodsVal.textContent = this.gameState.foods_eaten;
    this.dom.finalTimeVal.textContent = `${this.gameState.duration_seconds.toFixed(1)}s`;

    this.dom.gameOverModal.classList.remove('hidden');

    // Automatically persist score to SQLite: POST /api/game/score
    try {
      await GameAPI.saveScore({
        playerName: this.playerName,
        score: finalScore,
        difficulty: this.gameState.difficulty,
        foodsEaten: this.gameState.foods_eaten,
        durationSeconds: this.gameState.duration_seconds,
        sessionId: this.sessionId,
      });
    } catch (err) {
      console.warn('Score persistence warning:', err);
    }

    // Request AI Epitaph & Eulogy: POST /api/game/ai/epitaph
    this.fetchAIEpitaph(reasonText);
  }

  returnToHome() {
    this.stopTickLoop();
    this.isPaused = false;
    this.isGameOver = false;
    this.dom.pauseOverlay.classList.add('hidden');
    this.dom.gameOverModal.classList.add('hidden');
    this.switchView('home');
  }

  updateHUD(state) {
    if (!state) return;
    this.dom.hudScore.textContent = state.score;
    this.dom.hudFoods.textContent = state.foods_eaten;
    this.dom.hudDiff.textContent = state.difficulty.substring(0, 3);
  }

  // ==========================================================================
  // AI Integrations (Tactical Hints, Commentary, Epitaph, Challenge)
  // ==========================================================================

  async checkAIStatus() {
    try {
      const status = await GameAPI.getAIStatus();
      this.dom.aiStatusBadge.className = 'ai-badge ' + (status.gemini_available ? 'connected' : 'fallback');
      this.dom.aiStatusBadge.querySelector('.ai-label').textContent = status.gemini_available ? 'Gemini 4: Ready' : 'AI: Heuristic';
    } catch {
      this.dom.aiStatusBadge.className = 'ai-badge fallback';
      this.dom.aiStatusBadge.querySelector('.ai-label').textContent = 'AI: Local Mode';
    }
  }

  async requestAIHint() {
    if (!this.gameState || this.isGameOver) return;
    this.showToast('🧠 Consulting Grandmaster AI...');

    try {
      const advice = await GameAPI.getAIMoveAdvice({
        boardWidth: this.gameState.board.width,
        boardHeight: this.gameState.board.height,
        snakeSegments: this.gameState.snake.segments,
        currentDirection: this.gameState.snake.direction,
        foodPos: this.gameState.food ? this.gameState.food.position : null,
      });

      this.dom.hintRecDirection.textContent = `REC: ${advice.recommended_direction}`;
      this.dom.hintDangerLevel.textContent = `DANGER: ${advice.danger_level}`;
      this.dom.hintTip.textContent = advice.tactical_tip;
      this.dom.aiHintBanner.classList.remove('hidden');
    } catch (err) {
      this.showToast('AI Hint currently unavailable');
    }
  }

  async fetchLiveCommentary() {
    try {
      const comm = await GameAPI.getAICommentary({
        score: this.gameState.score,
        foodsEaten: this.gameState.foods_eaten,
        durationSeconds: this.gameState.duration_seconds,
        difficulty: this.gameState.difficulty,
        style: 'hype',
      });
      if (comm && comm.commentary) {
        this.dom.commentaryText.textContent = comm.commentary;
      }
    } catch {}
  }

  async fetchAIEpitaph(reason) {
    this.dom.epitaphTitle.textContent = 'Generating Serpent Eulogy...';
    this.dom.epitaphText.textContent = 'Connecting with the Chronicle of Serpents...';

    try {
      const epitaph = await GameAPI.getAIEpitaph({
        playerName: this.playerName,
        score: this.gameState.score,
        foodsEaten: this.gameState.foods_eaten,
        durationSeconds: this.gameState.duration_seconds,
        difficulty: this.gameState.difficulty,
        collisionType: this.gameState.collision_type,
      });

      this.dom.epitaphTitle.textContent = epitaph.title;
      this.dom.epitaphText.textContent = `"${epitaph.epitaph}"`;
    } catch {
      this.dom.epitaphTitle.textContent = `${this.playerName} the Bold Slitherer`;
      this.dom.epitaphText.textContent = `"Fell honorably in battle with ${this.gameState.score} points."`;
    }
  }

  async loadDailyChallenge() {
    this.dom.challengeTitle.textContent = 'Contacting Questmaster...';
    try {
      const ch = await GameAPI.getAIChallenge(this.difficulty);
      this.dom.challengeTitle.textContent = ch.challenge_title;
      this.dom.challengeGoal.textContent = ch.goal;
      this.dom.challengeBonus.textContent = `Bonus: ${ch.bonus_condition}`;
    } catch {
      this.dom.challengeTitle.textContent = 'The Speed Demon Trial';
      this.dom.challengeGoal.textContent = 'Score 120 points on Hard difficulty.';
      this.dom.challengeBonus.textContent = 'Bonus: Never turn left more than 6 times.';
    }
  }

  // ==========================================================================
  // Leaderboard Display
  // ==========================================================================

  async openLeaderboard() {
    this.dom.leaderboardModal.classList.remove('hidden');
    this.dom.statsPlayerName.textContent = this.playerName;
    this.dom.statsPersonalBestScore.textContent = `${this.personalBest} PTS`;
    this.loadLeaderboardData('ALL');
  }

  async loadLeaderboardData(difficulty) {
    this.dom.leaderboardBody.innerHTML = `<tr><td colspan="6" class="table-empty">Retrieving top scores...</td></tr>`;

    try {
      const resp = await GameAPI.getLeaderboard({
        limit: 15,
        difficulty: difficulty === 'ALL' ? null : difficulty,
      });

      if (!resp.scores || resp.scores.length === 0) {
        this.dom.leaderboardBody.innerHTML = `<tr><td colspan="6" class="table-empty">No scores recorded yet for this tier. Be the first!</td></tr>`;
        return;
      }

      this.dom.leaderboardBody.innerHTML = resp.scores
        .map((item, idx) => {
          const rank = idx + 1;
          let rankDisplay = rank;
          let rankClass = `rank-${rank}`;
          if (rank === 1) rankDisplay = '🥇 1';
          else if (rank === 2) rankDisplay = '🥈 2';
          else if (rank === 3) rankDisplay = '🥉 3';

          return `
            <tr>
              <td class="table-rank ${rankClass}">${rankDisplay}</td>
              <td class="table-player">${this.escapeHTML(item.player_name)}</td>
              <td class="table-score">${item.score}</td>
              <td class="table-diff">${item.difficulty}</td>
              <td>${item.foods_eaten}</td>
              <td>${item.duration_seconds.toFixed(1)}s</td>
            </tr>
          `;
        })
        .join('');
    } catch (err) {
      this.dom.leaderboardBody.innerHTML = `<tr><td colspan="6" class="table-empty">Failed to load leaderboard.</td></tr>`;
    }
  }

  escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
      tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
    );
  }
}

// Instantiate on DOM load
window.addEventListener('DOMContentLoaded', () => {
  window.cybersnake = new CyberSnakeApp();
});
