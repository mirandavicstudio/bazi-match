/**
 * particles.js - 宇宙星空粒子系统
 * 特性：星点闪烁、鼠标互动排斥、粒子连线、流星
 */

(function () {
  'use strict';

  const canvas = document.getElementById('star-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let width, height;
  let particles = [];
  let shootingStar = null;
  let animationId;
  let mouse = { x: -9999, y: -9999, radius: 150 };

  // ---- 配置 ----
  const CONFIG = {
    starCount: 260,           // 星点数量
    starMinSize: 0.4,
    starMaxSize: 2.2,
    connectionDist: 120,     // 粒子连线距离
    connectionAlpha: 0.12,
    mouseRepelRadius: 160,   // 鼠标排斥半径
    mouseRepelForce: 0.6,
    shootingStarIntervalMin: 4000,
    shootingStarIntervalMax: 9000,
    twinkleSpeed: 0.008,
    // 颜色：白、淡蓝、淡紫、淡金
    starColors: [
      'rgba(255,255,255,',
      'rgba(180,200,255,',
      'rgba(220,190,255,',
      'rgba(255,230,180,',
    ],
  };

  // ---- Particle 类 ----
  class Particle {
    constructor() {
      this.reset(true);
    }

    reset(initial) {
      this.x = Math.random() * width;
      this.y = Math.random() * height;
      this.size = CONFIG.starMinSize + Math.random() * (CONFIG.starMaxSize - CONFIG.starMinSize);
      this.baseAlpha = 0.3 + Math.random() * 0.7;
      this.alpha = this.baseAlpha;
      this.twinkleSpeed = 0.003 + Math.random() * CONFIG.twinkleSpeed;
      this.twinkleOffset = Math.random() * Math.PI * 2;
      this.color = CONFIG.starColors[Math.floor(Math.random() * CONFIG.starColors.length)];
      // 极慢漂移
      this.vx = (Math.random() - 0.5) * 0.15;
      this.vy = (Math.random() - 0.5) * 0.1;
      if (initial) {
        this.alpha = this.baseAlpha * (0.5 + Math.random() * 0.5);
      }
    }

    update(time) {
      // 闪烁
      this.alpha = this.baseAlpha * (0.5 + 0.5 * Math.sin(time * this.twinkleSpeed + this.twinkleOffset));
      this.alpha = Math.max(0.08, Math.min(1, this.alpha));

      // 漂移
      this.x += this.vx;
      this.y += this.vy;

      // 鼠标排斥
      const dx = this.x - mouse.x;
      const dy = this.y - mouse.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < mouse.radius) {
        const force = (1 - dist / mouse.radius) * CONFIG.mouseRepelForce;
        this.x += dx / dist * force * 3;
        this.y += dy / dist * force * 3;
      }

      // 边界环绕
      if (this.x < -10) this.x = width + 10;
      if (this.x > width + 10) this.x = -10;
      if (this.y < -10) this.y = height + 10;
      if (this.y > height + 10) this.y = -10;
    }

    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
      ctx.fillStyle = this.color + this.alpha.toFixed(2) + ')';
      ctx.fill();

      // 大星点加光晕
      if (this.size > 1.5 && this.alpha > 0.5) {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size * 3, 0, Math.PI * 2);
        const glow = this.color + (this.alpha * 0.12).toFixed(2) + ')';
        ctx.fillStyle = glow;
        ctx.fill();
      }
    }
  }

  // ---- 流星 ----
  class ShootingStar {
    constructor() {
      this.reset();
    }

    reset() {
      this.x = Math.random() * width * 0.8;
      this.y = 0;
      const angle = Math.PI / 4 + (Math.random() - 0.5) * 0.3;
      const speed = 6 + Math.random() * 5;
      this.vx = Math.cos(angle) * speed;
      this.vy = Math.sin(angle) * speed;
      this.length = 60 + Math.random() * 80;
      this.life = 1;
      this.decay = 0.012 + Math.random() * 0.01;
      this.active = true;
    }

    update() {
      if (!this.active) return;
      this.x += this.vx;
      this.y += this.vy;
      this.life -= this.decay;
      if (this.life <= 0 || this.x > width + 100 || this.y > height + 100) {
        this.active = false;
      }
    }

    draw() {
      if (!this.active) return;
      const tailX = this.x - (this.vx / Math.sqrt(this.vx * this.vx + this.vy * this.vy)) * this.length;
      const tailY = this.y - (this.vy / Math.sqrt(this.vx * this.vx + this.vy * this.vy)) * this.length;

      const grad = ctx.createLinearGradient(tailX, tailY, this.x, this.y);
      grad.addColorStop(0, `rgba(255,255,255,0)`);
      grad.addColorStop(0.4, `rgba(200,220,255,${this.life * 0.5})`);
      grad.addColorStop(1, `rgba(255,255,255,${this.life * 0.9})`);

      ctx.beginPath();
      ctx.moveTo(tailX, tailY);
      ctx.lineTo(this.x, this.y);
      ctx.strokeStyle = grad;
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // 流星头部光晕
      ctx.beginPath();
      ctx.arc(this.x, this.y, 2, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255,255,255,${this.life * 0.8})`;
      ctx.fill();
    }
  }

  // ---- 初始化 ----
  function init() {
    resize();
    particles = [];
    for (let i = 0; i < CONFIG.starCount; i++) {
      particles.push(new Particle());
    }
    shootingStar = new ShootingStar();
    shootingStar.active = false;
    scheduleShootingStar();
    animate();
  }

  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function scheduleShootingStar() {
    const delay = CONFIG.shootingStarIntervalMin +
      Math.random() * (CONFIG.shootingStarIntervalMax - CONFIG.shootingStarIntervalMin);
    setTimeout(() => {
      if (shootingStar) shootingStar.active = false;
      shootingStar = new ShootingStar();
      scheduleShootingStar();
    }, delay);
  }

  // ---- 绘制粒子连线 ----
  function drawConnections() {
    const maxDist = CONFIG.connectionDist;
    const maxDist2 = maxDist * maxDist;
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist2 = dx * dx + dy * dy;
        if (dist2 < maxDist2) {
          const alpha = (1 - Math.sqrt(dist2) / maxDist) * CONFIG.connectionAlpha;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(140,160,255,${alpha})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
  }

  // ---- 动画循环 ----
  let lastTime = 0;
  function animate(time) {
    animationId = requestAnimationFrame(animate);
    const t = time * 0.001;

    // 清除画布（带残影效果）
    ctx.fillStyle = 'rgba(7,7,26,0.25)';
    ctx.fillRect(0, 0, width, height);

    // 绘制连线
    drawConnections();

    // 更新并绘制粒子
    for (const p of particles) {
      p.update(t);
      p.draw();
    }

    // 绘制流星
    shootingStar.update();
    shootingStar.draw();

    lastTime = t;
  }

  // ---- 事件监听 ----
  window.addEventListener('resize', () => {
    resize();
  });

  window.addEventListener('mousemove', (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
  });

  window.addEventListener('mouseleave', () => {
    mouse.x = -9999;
    mouse.y = -9999;
  });

  // 触摸支持
  window.addEventListener('touchmove', (e) => {
    if (e.touches.length > 0) {
      mouse.x = e.touches[0].clientX;
      mouse.y = e.touches[0].clientY;
    }
  }, { passive: true });

  window.addEventListener('touchend', () => {
    mouse.x = -9999;
    mouse.y = -9999;
  });

  // 启动
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
