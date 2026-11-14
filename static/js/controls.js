/**
 * Controls & Input Management for CyberSnake Arcade.
 * Supports:
 * - Keyboard (WASD & Arrow Keys)
 * - Mobile Touch Swipes on Canvas
 * - On-Screen Virtual D-Pad buttons
 * - Immediate client-side 180° reversal filtering
 */

export class ControlsManager {
  constructor({ onDirectionChange, onPauseToggle, onRestart, onAIHint, onSoundToggle }) {
    this.onDirectionChange = onDirectionChange;
    this.onPauseToggle = onPauseToggle;
    this.onRestart = onRestart;
    this.onAIHint = onAIHint;
    this.onSoundToggle = onSoundToggle;

    this.currentDirection = 'RIGHT';
    this.pendingDirection = 'RIGHT';

    // Touch tracking
    this.touchStartX = 0;
    this.touchStartY = 0;
    this.minSwipeDistance = 25; // pixels

    this.initKeyboard();
    this.initTouch();
    this.initDPad();
  }

  setDirection(direction) {
    this.currentDirection = direction;
    this.pendingDirection = direction;
  }

  _isOpposite(dir1, dir2) {
    return (
      (dir1 === 'UP' && dir2 === 'DOWN') ||
      (dir1 === 'DOWN' && dir2 === 'UP') ||
      (dir1 === 'LEFT' && dir2 === 'RIGHT') ||
      (dir1 === 'RIGHT' && dir2 === 'LEFT')
    );
  }

  handleDirectionInput(newDirection) {
    if (!newDirection) return;
    if (this._isOpposite(newDirection, this.pendingDirection)) {
      // Reject 180-degree reverse
      return;
    }
    this.pendingDirection = newDirection;
    if (this.onDirectionChange) {
      this.onDirectionChange(newDirection);
    }
  }

  initKeyboard() {
    window.addEventListener('keydown', (e) => {
      // Don't intercept typing in inputs
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return;
      }

      switch (e.code) {
        case 'ArrowUp':
        case 'KeyW':
          e.preventDefault();
          this.handleDirectionInput('UP');
          break;
        case 'ArrowDown':
        case 'KeyS':
          e.preventDefault();
          this.handleDirectionInput('DOWN');
          break;
        case 'ArrowLeft':
        case 'KeyA':
          e.preventDefault();
          this.handleDirectionInput('LEFT');
          break;
        case 'ArrowRight':
        case 'KeyD':
          e.preventDefault();
          this.handleDirectionInput('RIGHT');
          break;
        case 'Space':
        case 'KeyP':
          e.preventDefault();
          if (this.onPauseToggle) this.onPauseToggle();
          break;
        case 'KeyR':
          e.preventDefault();
          if (this.onRestart) this.onRestart();
          break;
        case 'KeyH':
          e.preventDefault();
          if (this.onAIHint) this.onAIHint();
          break;
        case 'KeyM':
          e.preventDefault();
          if (this.onSoundToggle) this.onSoundToggle();
          break;
      }
    });
  }

  initTouch() {
    const canvas = document.getElementById('gameCanvas');
    if (!canvas) return;

    canvas.addEventListener('touchstart', (e) => {
      if (e.touches.length > 0) {
        this.touchStartX = e.touches[0].clientX;
        this.touchStartY = e.touches[0].clientY;
      }
    }, { passive: true });

    canvas.addEventListener('touchmove', (e) => {
      // Prevent browser pull-to-refresh while swiping
      e.preventDefault();
    }, { passive: false });

    canvas.addEventListener('touchend', (e) => {
      if (e.changedTouches.length === 0) return;
      const touchEndX = e.changedTouches[0].clientX;
      const touchEndY = e.changedTouches[0].clientY;

      const dx = touchEndX - this.touchStartX;
      const dy = touchEndY - this.touchStartY;

      if (Math.abs(dx) < this.minSwipeDistance && Math.abs(dy) < this.minSwipeDistance) {
        return; // tap, not swipe
      }

      if (Math.abs(dx) > Math.abs(dy)) {
        // Horizontal swipe
        if (dx > 0) {
          this.handleDirectionInput('RIGHT');
        } else {
          this.handleDirectionInput('LEFT');
        }
      } else {
        // Vertical swipe
        if (dy > 0) {
          this.handleDirectionInput('DOWN');
        } else {
          this.handleDirectionInput('UP');
        }
      }
    }, { passive: true });
  }

  initDPad() {
    const buttons = document.querySelectorAll('.dpad-btn');
    buttons.forEach((btn) => {
      const dir = btn.getAttribute('data-dir');
      const trigger = (e) => {
        e.preventDefault();
        this.handleDirectionInput(dir);
      };
      btn.addEventListener('touchstart', trigger, { passive: false });
      btn.addEventListener('click', trigger);
    });
  }
}
