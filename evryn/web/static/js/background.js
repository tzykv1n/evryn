/**
 * EVRYN Generative Black-Line Background
 * Procedural mathematical line networks that evolve, branch, intersect, and fade quietly.
 */
(function () {
  const canvas = document.getElementById("bg-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  let width = 0;
  let height = 0;
  let animId = null;
  let isDimmed = false;

  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Node count
  const NUM_POINTS = 14;
  const MAX_CONNECT_DIST = 260;
  const points = [];

  class Point {
    constructor(w, h, seed) {
      this.x = Math.random() * w;
      this.y = Math.random() * h;
      this.vx = (Math.random() - 0.5) * 0.45;
      this.vy = (Math.random() - 0.5) * 0.45;
      this.baseRadius = 1.0;
      this.seed = seed;
      this.phase = Math.random() * Math.PI * 2;
    }

    update(w, h, time) {
      this.phase += 0.005;
      // Low-frequency subtle sinusoidal drift
      this.x += this.vx + Math.sin(this.phase) * 0.15;
      this.y += this.vy + Math.cos(this.phase) * 0.15;

      // Wrap boundaries smoothly
      if (this.x < -40) this.x = w + 40;
      if (this.x > w + 40) this.x = -40;
      if (this.y < -40) this.y = h + 40;
      if (this.y > h + 40) this.y = -40;
    }
  }

  function resize() {
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = width * window.devicePixelRatio;
    canvas.height = height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    if (points.length === 0) {
      for (let i = 0; i < NUM_POINTS; i++) {
        points.push(new Point(width, height, i));
      }
    }
    draw(0);
  }

  function draw(time) {
    ctx.clearRect(0, 0, width, height);

    const baseAlpha = isDimmed ? 0.03 : 0.12;

    // 1. Draw connecting line network
    for (let i = 0; i < points.length; i++) {
      const p1 = points[i];
      for (let j = i + 1; j < points.length; j++) {
        const p2 = points[j];
        const dx = p1.x - p2.x;
        const dy = p1.y - p2.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < MAX_CONNECT_DIST) {
          const ratio = 1 - dist / MAX_CONNECT_DIST;
          const alpha = ratio * baseAlpha;

          ctx.beginPath();
          ctx.strokeStyle = `rgba(0, 0, 0, ${alpha.toFixed(4)})`;
          ctx.lineWidth = 0.8;

          // Gentle curved midpoint to evoke mathematical graphs
          const midX = (p1.x + p2.x) / 2 + Math.sin(p1.phase) * 12;
          const midY = (p1.y + p2.y) / 2 + Math.cos(p2.phase) * 12;

          ctx.moveTo(p1.x, p1.y);
          ctx.quadraticCurveTo(midX, midY, p2.x, p2.y);
          ctx.stroke();

          // Subtle branching line from midpoint
          if (ratio > 0.65) {
            const branchLen = ratio * 35;
            const bX = midX + Math.cos(p1.phase * 2) * branchLen;
            const bY = midY + Math.sin(p2.phase * 2) * branchLen;

            ctx.beginPath();
            ctx.strokeStyle = `rgba(0, 0, 0, ${(alpha * 0.5).toFixed(4)})`;
            ctx.lineWidth = 0.5;
            ctx.moveTo(midX, midY);
            ctx.lineTo(bX, bY);
            ctx.stroke();
          }
        }
      }
    }

    // 2. Draw subtle point vertices
    for (let i = 0; i < points.length; i++) {
      const p = points[i];
      ctx.beginPath();
      ctx.fillStyle = `rgba(0, 0, 0, ${(baseAlpha * 1.5).toFixed(4)})`;
      ctx.arc(p.x, p.y, p.baseRadius, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function loop(time) {
    if (document.hidden) {
      animId = null;
      return;
    }

    for (let i = 0; i < points.length; i++) {
      points[i].update(width, height, time);
    }
    draw(time);

    if (!prefersReducedMotion) {
      animId = requestAnimationFrame(loop);
    }
  }

  window.addEventListener("resize", resize);
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden && !animId && !prefersReducedMotion) {
      animId = requestAnimationFrame(loop);
    }
  });

  resize();
  if (!prefersReducedMotion) {
    animId = requestAnimationFrame(loop);
  }

  window.EVRYN_BG = {
    setDimmed: function (dim) {
      isDimmed = !!dim;
      if (dim) {
        canvas.classList.add("dimmed");
      } else {
        canvas.classList.remove("dimmed");
      }
    },
  };
})();
