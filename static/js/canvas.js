/**
 * Canvas Game Board Renderer for CyberSnake Arcade.
 * Renders high-DPI neon grid, pulsating glowing food, stylized snake with eyes, and particles.
 */

import { ParticleEmitter } from './particles.js';

export class GameCanvasRenderer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.particleEmitter = new ParticleEmitter();
    
    // Grid settings
    this.gridWidth = 20;
    this.gridHeight = 20;
    this.cellSize = 30;

    // Pulse animation state
    this.foodPulse = 0;
    this.shakeIntensity = 0;

    // Handle high DPI
    this.resizeCanvas();
    window.addEventListener('resize', () => this.resizeCanvas());
  }

  resizeCanvas() {
    const rect = this.canvas.parentElement.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const size = Math.floor(Math.min(rect.width, rect.height || 600));

    this.canvas.width = size * dpr;
    this.canvas.height = size * dpr;
    this.canvas.style.width = `${size}px`;
    this.canvas.style.height = `${size}px`;

    this.ctx.resetTransform?.();
    this.ctx.scale(dpr, dpr);
    this.displaySize = size;
    this.updateCellSize();
  }

  updateCellSize() {
    if (this.gridWidth > 0 && this.displaySize > 0) {
      this.cellSize = this.displaySize / this.gridWidth;
    }
  }

  setBoardDimensions(width, height) {
    this.gridWidth = width;
    this.gridHeight = height;
    this.updateCellSize();
  }

  triggerScreenShake(intensity = 8) {
    this.shakeIntensity = intensity;
  }

  render(gameState) {
    if (!gameState) return;

    this.foodPulse += 0.08;
    const ctx = this.ctx;
    const size = this.displaySize;
    const cell = this.cellSize;

    ctx.save();

    // 1. Screen Shake if active
    if (this.shakeIntensity > 0) {
      const dx = (Math.random() - 0.5) * this.shakeIntensity;
      const dy = (Math.random() - 0.5) * this.shakeIntensity;
      ctx.translate(dx, dy);
      this.shakeIntensity *= 0.85;
      if (this.shakeIntensity < 0.5) this.shakeIntensity = 0;
    }

    // 2. Clear canvas with dark arcade background
    ctx.fillStyle = '#080a10';
    ctx.fillRect(0, 0, size, size);

    // 3. Draw Cyber Grid
    this.drawGrid(ctx, size, cell);

    // 4. Draw Glowing Food
    if (gameState.food && gameState.food.position) {
      this.drawFood(ctx, gameState.food.position, cell);
    }

    // 5. Draw Neon Snake
    if (gameState.snake && gameState.snake.segments) {
      this.drawSnake(ctx, gameState.snake, cell);
    }

    // 6. Draw Active Particles
    this.particleEmitter.updateAndDraw(ctx);

    ctx.restore();
  }

  drawGrid(ctx, size, cell) {
    ctx.save();
    ctx.strokeStyle = 'rgba(0, 255, 136, 0.035)';
    ctx.lineWidth = 1;

    for (let x = 0; x <= size; x += cell) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, size);
      ctx.stroke();
    }
    for (let y = 0; y <= size; y += cell) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(size, y);
      ctx.stroke();
    }
    ctx.restore();
  }

  drawFood(ctx, pos, cell) {
    const cx = pos.x * cell + cell / 2;
    const cy = pos.y * cell + cell / 2;
    const radius = (cell / 2.6) * (1 + Math.sin(this.foodPulse) * 0.08);

    ctx.save();
    // Multi-layer glowing aura
    ctx.shadowColor = '#ff2a5f';
    ctx.shadowBlur = 16;
    
    // Outer radial glow
    const grad = ctx.createRadialGradient(cx, cy, 2, cx, cy, radius * 1.5);
    grad.addColorStop(0, '#ff6b8b');
    grad.addColorStop(0.5, '#ff2a5f');
    grad.addColorStop(1, 'rgba(255, 42, 95, 0)');

    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(cx, cy, radius * 1.4, 0, Math.PI * 2);
    ctx.fill();

    // Solid core jewel
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(cx, cy, radius * 0.6, 0, Math.PI * 2);
    ctx.fill();

    // Core ruby dot
    ctx.fillStyle = '#ff2a5f';
    ctx.beginPath();
    ctx.arc(cx, cy, radius * 0.4, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();
  }

  drawSnake(ctx, snake, cell) {
    const segments = snake.segments;
    if (!segments || segments.length === 0) return;

    ctx.save();
    ctx.shadowColor = '#00ff88';
    ctx.shadowBlur = 12;

    const len = segments.length;

    // Draw body segments (from tail to 2nd segment)
    for (let i = len - 1; i >= 1; i--) {
      const seg = segments[i];
      const factor = 1 - i / len; // 1 at head, 0.3 at tail
      const alpha = 0.6 + factor * 0.4;
      const segRadius = (cell / 2.3) * (0.8 + factor * 0.2);

      const cx = seg.x * cell + cell / 2;
      const cy = seg.y * cell + cell / 2;

      ctx.fillStyle = `rgba(0, 255, 136, ${alpha})`;
      ctx.beginPath();
      ctx.arc(cx, cy, segRadius, 0, Math.PI * 2);
      ctx.fill();

      // Inner neon spine dot
      ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
      ctx.beginPath();
      ctx.arc(cx, cy, segRadius * 0.35, 0, Math.PI * 2);
      ctx.fill();
    }

    // Draw Head
    const head = segments[0];
    const hx = head.x * cell + cell / 2;
    const hy = head.y * cell + cell / 2;
    const headRadius = cell / 2.1;

    ctx.fillStyle = '#00ff88';
    ctx.shadowBlur = 20;
    ctx.beginPath();
    ctx.arc(hx, hy, headRadius, 0, Math.PI * 2);
    ctx.fill();

    // Draw Eyes facing current direction
    this.drawEyes(ctx, hx, hy, headRadius, snake.direction);

    ctx.restore();
  }

  drawEyes(ctx, hx, hy, radius, direction) {
    let eye1X, eye1Y, eye2X, eye2Y;
    const offset = radius * 0.45;
    const eyeRadius = radius * 0.22;
    const pupilRadius = radius * 0.11;

    switch (direction) {
      case 'UP':
        eye1X = hx - offset; eye1Y = hy - offset * 0.5;
        eye2X = hx + offset; eye2Y = hy - offset * 0.5;
        break;
      case 'DOWN':
        eye1X = hx - offset; eye1Y = hy + offset * 0.5;
        eye2X = hx + offset; eye2Y = hy + offset * 0.5;
        break;
      case 'LEFT':
        eye1X = hx - offset * 0.5; eye1Y = hy - offset;
        eye2X = hx - offset * 0.5; eye2Y = hy + offset;
        break;
      case 'RIGHT':
      default:
        eye1X = hx + offset * 0.5; eye1Y = hy - offset;
        eye2X = hx + offset * 0.5; eye2Y = hy + offset;
        break;
    }

    // Eye Whites
    ctx.shadowBlur = 0;
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(eye1X, eye1Y, eyeRadius, 0, Math.PI * 2);
    ctx.arc(eye2X, eye2Y, eyeRadius, 0, Math.PI * 2);
    ctx.fill();

    // Eye Pupils (Looking forward)
    ctx.fillStyle = '#05140b';
    ctx.beginPath();
    ctx.arc(eye1X, eye1Y, pupilRadius, 0, Math.PI * 2);
    ctx.arc(eye2X, eye2Y, pupilRadius, 0, Math.PI * 2);
    ctx.fill();
  }
}
