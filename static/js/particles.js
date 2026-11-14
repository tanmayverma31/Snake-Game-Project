/**
 * Particle System for Neon Sparks and Explosion Effects.
 */

export class Particle {
  constructor(x, y, color, vx, vy, size, life) {
    this.x = x;
    this.y = y;
    this.color = color;
    this.vx = vx;
    this.vy = vy;
    this.size = size;
    this.life = life;
    this.maxLife = life;
  }

  update() {
    this.x += this.vx;
    this.y += this.vy;
    this.vx *= 0.94;
    this.vy *= 0.94;
    this.life--;
  }

  draw(ctx) {
    const alpha = Math.max(0, this.life / this.maxLife);
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.fillStyle = this.color;
    ctx.shadowColor = this.color;
    ctx.shadowBlur = 8;
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
}

export class ParticleEmitter {
  constructor() {
    this.particles = [];
  }

  /**
   * Spawns neon food sparkle burst.
   */
  emitFoodSparkles(x, y, color = '#00ff88', count = 16) {
    for (let i = 0; i < count; i++) {
      const angle = (Math.PI * 2 * i) / count + (Math.random() - 0.5) * 0.5;
      const speed = 1.5 + Math.random() * 3.5;
      const vx = Math.cos(angle) * speed;
      const vy = Math.sin(angle) * speed;
      const size = 1.5 + Math.random() * 2.5;
      const life = 18 + Math.floor(Math.random() * 14);
      this.particles.push(new Particle(x, y, color, vx, vy, size, life));
    }
  }

  /**
   * Spawns collision shockwave explosion.
   */
  emitCollisionExplosion(x, y, count = 28) {
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = 2.0 + Math.random() * 5.0;
      const vx = Math.cos(angle) * speed;
      const vy = Math.sin(angle) * speed;
      const colors = ['#ff2a5f', '#ffbe0b', '#ffffff'];
      const color = colors[Math.floor(Math.random() * colors.length)];
      const size = 2.0 + Math.random() * 3.0;
      const life = 25 + Math.floor(Math.random() * 20);
      this.particles.push(new Particle(x, y, color, vx, vy, size, life));
    }
  }

  updateAndDraw(ctx) {
    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      p.update();
      if (p.life <= 0) {
        this.particles.splice(i, 1);
      } else {
        p.draw(ctx);
      }
    }
  }

  clear() {
    this.particles = [];
  }
}
