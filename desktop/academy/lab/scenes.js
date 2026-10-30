/* DiffAtOnce Motion Lab — deterministic educational Canvas scenes.
 * No remote dependencies. Molecular motion is simulated, never experimental data.
 * PGSE: rectangular pulses; 1H gamma in rad s^-1 T^-1; parameters in SI internally.
 * q(t) is the accumulated effective gradient, including the RF sign change.
 */
(function () {
  'use strict';
  const C = { bg: '#07131f', panel: '#0c2030', line: '#244151', muted: '#92aeba', white: '#edf8fd', blue: '#53d4ff', orange: '#ffba68', red: '#ff748c', green: '#83edd1', purple: '#c9a9ff' };
  const GAMMA = 2.6752218744e8;
  const TAU = Math.PI * 2;
  const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
  const mix = (a, b, x) => a + (b - a) * x;
  const ease = x => { x = clamp(x, 0, 1); return x * x * (3 - 2 * x); };
  const tr = (l, es, en) => l === 'es' ? es : en;
  const fmt = (v, n = 2) => Number(v).toFixed(n);
  const controls = {};
  const defaults = {};
  const ctl = (id, es, en, min, max, step, value, unit) => ({ id, label: { es, en }, min, max, step, value, unit: unit || '' });
  function group(id, list) { controls[id] = list; defaults[id] = Object.fromEntries(list.map(c => [c.id, c.value])); }
  const diffusion = () => [ctl('Dslow', 'D lento', 'Slow D', 0.1, 1, 0.05, 0.45, '10⁻⁹ m²/s'), ctl('Dfast', 'D rápido', 'Fast D', 1.1, 4, 0.05, 1.6, '10⁻⁹ m²/s')];
  const pgse = () => [ctl('g', 'Gradiente g', 'Gradient g', 20, 500, 5, 260, 'mT/m'), ctl('delta', 'Duración δ', 'Duration δ', 0.3, 5, 0.1, 1.5, 'ms'), ctl('Delta', 'Separación Δ', 'Separation Δ', 20, 300, 5, 80, 'ms')];
  group('brownian', [...diffusion(), ctl('Delta', 'Tiempo observado', 'Observation time', 20, 300, 5, 100, 'ms')]);
  group('spin-echo', [...pgse(), ctl('D', 'Difusión D', 'Diffusion D', 0, 3, 0.05, 1.2, '10⁻⁹ m²/s')]);
  group('gradients-b', pgse());
  group('attenuation-mixture', [...diffusion(), ctl('fraction', 'Fracción lenta', 'Slow fraction', 0.05, 0.95, 0.05, 0.6, ''), ctl('bmax', 'b máximo', 'Maximum b', 0.5, 6, 0.1, 3, '10⁹ s/m²'), ctl('noise', 'Ruido de S₀', 'Noise relative to S₀', 0, 5, 0.1, 1, '%')]);
  group('pulse-90', [ctl('p90', 'P90 real del ejemplo', 'True example P90', 5, 25, 0.5, 10, 'µs'), ctl('noise', 'Ruido de S₀', 'Noise relative to S₀', 0, 4, 0.1, 0.5, '%')]);
  group('acquisition-window', [...diffusion(), ctl('delta', 'δ de cada lóbulo', 'δ per lobe', 0.3, 5, 0.1, 1.2, 'ms'), ctl('Delta', 'Δ de la rampa central', 'Middle ramp Δ', 30, 180, 5, 100, 'ms'), ctl('Gmax', 'G máximo del ejemplo', 'Example maximum G', 100, 700, 10, 500, 'mT/m'), ctl('noise', 'Suelo de ruido', 'Noise floor', 0.2, 5, 0.1, 1, '%')]);
  group('convection', [...pgse(), ctl('D', 'Difusión D', 'Diffusion D', 0.1, 3, 0.1, 1, '10⁻⁹ m²/s'), ctl('velocity', 'Velocidad común', 'Common velocity', -100, 100, 5, 35, 'µm/s'), ctl('spread', 'Dispersión de velocidades', 'Velocity spread', 0, 100, 5, 30, 'µm/s')]);
  group('overlap-joint', [...diffusion(), ctl('ppm', 'Frecuencia seleccionada', 'Selected frequency', 0.5, 7.5, 0.05, 5.15, 'ppm'), ctl('bmax', 'b máximo', 'Maximum b', 0.5, 5, 0.1, 2.5, '10⁹ s/m²')]);
  group('ilt', [ctl('separation', 'Separación entre D', 'Separation between D', 0.02, 0.5, 0.01, 0.1, '10⁻⁹ m²/s'), ctl('noise', 'Ruido de S₀', 'Noise relative to S₀', 0.1, 3, 0.1, 1, '%'), ctl('regularization', 'Suavizado ilustrado', 'Illustrative smoothing', 0, 1, 0.01, 0.25, ''), ctl('bmax', 'b máximo', 'Maximum b', 1, 6, 0.1, 3, '10⁹ s/m²')]);
  group('restricted', [ctl('D', 'Difusión libre D₀', 'Free diffusion D₀', 0.2, 3, 0.1, 1.2, '10⁻⁹ m²/s'), ctl('width', 'Anchura del poro a', 'Pore width a', 5, 60, 1, 20, 'µm'), ctl('Delta', 'Tiempo observado', 'Observation time', 20, 300, 5, 150, 'ms')]);
  group('exchange', [...diffusion(), ctl('rate', 'Tasa A ⇄ B simétrica', 'Symmetric A ⇄ B rate', 0, 80, 1, 12, 's⁻¹'), ctl('Delta', 'Tiempo observado', 'Observation time', 20, 300, 5, 100, 'ms')]);
  group('anisotropy', [ctl('Dparallel', 'D paralelo', 'Parallel D', 0.5, 3, 0.05, 1.8, '10⁻⁹ m²/s'), ctl('Dperp', 'D perpendicular', 'Perpendicular D', 0.1, 1.5, 0.05, 0.4, '10⁻⁹ m²/s'), ctl('angle', 'Orientación del gradiente', 'Gradient orientation', 0, 180, 1, 30, '°'), ctl('Delta', 'Tiempo observado', 'Observation time', 20, 300, 5, 100, 'ms')]);
  ['ultrafast', 'dt2', 'spen', 'prototype-1d'].forEach(id => group(id, [ctl('encoding', 'Progreso de codificación', 'Encoding progress', 0, 1, 0.02, 0.5, '')]));

  function rng(seed) { let a = seed >>> 0; return () => { a += 0x6D2B79F5; let z = a; z = Math.imul(z ^ z >>> 15, z | 1); z ^= z + Math.imul(z ^ z >>> 7, z | 61); return ((z ^ z >>> 14) >>> 0) / 4294967296; }; }
  function gaussian(r) { return Math.sqrt(-2 * Math.log(Math.max(r(), 1e-12))) * Math.cos(TAU * r()); }
  const WALK_STEPS = 180;
  const walkerCache = new Map();
  function walkers(seed, count) {
    const key = seed + ':' + count;
    if (walkerCache.has(key)) return walkerCache.get(key);
    const r = rng(seed), out = [];
    for (let i = 0; i < count; i++) {
      const x = [0], y = [0], z = [0];
      for (let k = 1; k <= WALK_STEPS; k++) { x.push(x[k - 1] + gaussian(r) / Math.sqrt(WALK_STEPS)); y.push(y[k - 1] + gaussian(r) / Math.sqrt(WALK_STEPS)); z.push(z[k - 1] + gaussian(r) / Math.sqrt(WALK_STEPS)); }
      out.push({ x, y, z, x0: r(), y0: r(), phase: r() * TAU, r: 2.7 + r() * 1.8 });
    }
    walkerCache.set(key, out); return out;
  }
  function sample(a, u) { const x = clamp(u, 0, 1) * WALK_STEPS, k = Math.floor(x); return mix(a[k], a[Math.min(k + 1, WALK_STEPS)], x - k); }
  function B(p) { const d = p.delta * 1e-3, D = p.Delta * 1e-3, g = p.g * 1e-3; return (GAMMA * g * d) ** 2 * Math.max(0, D - d / 3); }
  function rect(c, x, y, w, h, r = 12, fill, stroke) { c.beginPath(); c.roundRect(x, y, w, h, r); if (fill) { c.fillStyle = fill; c.fill(); } if (stroke) { c.strokeStyle = stroke; c.lineWidth = 1; c.stroke(); } }
  function line(c, x1, y1, x2, y2, color, width = 1, dash) { c.save(); c.beginPath(); c.strokeStyle = color; c.lineWidth = width; if (dash) c.setLineDash(dash); c.moveTo(x1, y1); c.lineTo(x2, y2); c.stroke(); c.restore(); }
  function text(c, s, x, y, size = 16, color = C.white, align = 'left', weight = 400) { c.font = `${weight} ${size}px "Segoe UI", system-ui, sans-serif`; c.fillStyle = color; c.textAlign = align; c.textBaseline = 'middle'; c.fillText(s, x, y); }
  function wrap(c, s, x, y, maxW, size = 14, color = C.muted, maxLines = 3) {
    c.font = `400 ${size}px "Segoe UI", system-ui, sans-serif`; c.textAlign = 'left'; c.textBaseline = 'top'; c.fillStyle = color;
    let words = String(s).split(' '), row = '', lines = [];
    words.forEach(word => { const next = row ? row + ' ' + word : word; if (c.measureText(next).width > maxW && row) { lines.push(row); row = word; } else row = next; });
    if (row) lines.push(row);
    lines.slice(0, maxLines).forEach((s, i) => c.fillText(s, x, y + i * size * 1.35));
    return Math.min(lines.length, maxLines) * size * 1.35;
  }
  function arrow(c, x, y, dx, dy, color = C.blue, width = 2, head = 7) { const a = Math.atan2(dy, dx); line(c, x, y, x + dx, y + dy, color, width); c.beginPath(); c.fillStyle = color; c.moveTo(x + dx, y + dy); c.lineTo(x + dx - head * Math.cos(a - 0.45), y + dy - head * Math.sin(a - 0.45)); c.lineTo(x + dx - head * Math.cos(a + 0.45), y + dy - head * Math.sin(a + 0.45)); c.closePath(); c.fill(); }
  function dot(c, x, y, r, color, glow = false) { c.save(); if (glow) { c.shadowColor = color; c.shadowBlur = 12; } c.beginPath(); c.arc(x, y, r, 0, TAU); c.fillStyle = color; c.fill(); c.restore(); }
  function halo(c, x, y, r, color, alpha = 0.1) { c.save(); c.globalAlpha = alpha; c.beginPath(); c.arc(x, y, r, 0, TAU); c.fillStyle = color; c.fill(); c.restore(); }
  function curve(c, points, color = C.blue, width = 2.5, dash) { if (!points.length) return; c.save(); c.strokeStyle = color; c.lineWidth = width; if (dash) c.setLineDash(dash); c.beginPath(); points.forEach((v, i) => i ? c.lineTo(v[0], v[1]) : c.moveTo(v[0], v[1])); c.stroke(); c.restore(); }
  function frame(c, w, h, l, heading) {
    c.save(); c.fillStyle = C.bg; c.fillRect(0, 0, w, h);
    const grad = c.createRadialGradient(w * .55, h * .4, 20, w * .55, h * .4, w * .7); grad.addColorStop(0, '#113149'); grad.addColorStop(1, C.bg); c.fillStyle = grad; c.fillRect(0, 0, w, h);
    c.globalAlpha = .19; for (let x = 0; x < w; x += 42) line(c, x, 0, x, h, C.line); for (let y = 0; y < h; y += 42) line(c, 0, y, w, y, C.line); c.globalAlpha = 1;
    const fs = w < 600 ? 15 : 21;
    if (w < 600) wrap(c, heading, 17, 10, w - 34, 14, C.white, 2);
    else text(c, heading, 22, 28, fs, C.white, 'left', 650);
    if (w > 720) text(c, tr(l, 'SIMULACIÓN EDUCATIVA', 'EDUCATIONAL SIMULATION'), w - 22, 27, 11, C.muted, 'right', 650);
    c.restore();
  }
  function layout(w, h, columns = 2, ratio = .55) {
    const m = w < 600 ? 14 : 22, gap = w < 600 ? 14 : 20, top = 56, bottom = w < 600 ? 112 : 91, height = Math.max(120, h - top - bottom);
    if (columns === 1) return [{ x: m, y: top, w: w - 2 * m, h: height }];
    if (w < 600) { const ph = (height - gap) / 2; return [{ x: m, y: top, w: w - 2 * m, h: ph }, { x: m, y: top + ph + gap, w: w - 2 * m, h: ph }]; }
    const usable = w - 2 * m - gap, first = usable * ratio;
    return [{ x: m, y: top, w: first, h: height }, { x: m + first + gap, y: top, w: usable - first, h: height }];
  }
  function panel(c, p, heading, sub, l) {
    rect(c, p.x, p.y, p.w, p.h, 14, '#0a1d2ade', C.line);
    const hs = p.w < 420 ? 13 : 17, ss = p.w < 420 ? 10.5 : 12;
    const titleH = wrap(c, heading, p.x + 16, p.y + 15, p.w - 32, hs, C.white, 2);
    const subH = sub ? wrap(c, sub, p.x + 16, p.y + 19 + titleH, p.w - 32, ss, C.muted, 2) : 0;
    const inset = 29 + titleH + subH;
    return { x: p.x + 18, y: p.y + inset, w: p.w - 36, h: p.h - inset - 16 };
  }
  function footer(c, w, h, formula, explanation, l) {
    const fh = w < 600 ? 102 : 77, x = w < 600 ? 14 : 22;
    rect(c, x, h - fh - 4, w - 2 * x, fh, 12, '#102838', '#315568');
    const size = w < 600 ? 13 : 19;
    const formulaH = wrap(c, formula, x + 15, h - fh + 9, w - 2 * x - 30, size, C.green, w < 600 ? 2 : 1);
    wrap(c, explanation, x + 15, h - fh + 15 + formulaH, w - 2 * x - 30, w < 600 ? 11 : 13, C.muted, w < 600 && formulaH > 20 ? 2 : 3);
  }
  function axes(c, p, opt = {}) {
    const left = opt.left || 49, right = 17, top = 15, bottom = opt.bottom || 39;
    const a = { x: p.x + left, y: p.y + top, w: Math.max(40, p.w - left - right), h: Math.max(35, p.h - top - bottom) };
    const xmin = opt.xmin || 0, xmax = opt.xmax || 1, ymin = opt.ymin || 0, ymax = opt.ymax || 1;
    a.X = v => a.x + (v - xmin) / (xmax - xmin) * a.w; a.Y = v => a.y + a.h - (v - ymin) / (ymax - ymin) * a.h;
    const ticks = a.w < 260 ? 3 : 4;
    for (let i = 0; i <= ticks; i++) { const f = i / ticks; line(c, a.x + f * a.w, a.y, a.x + f * a.w, a.y + a.h, '#233e4c'); text(c, opt.xFormat ? opt.xFormat(mix(xmin, xmax, f)) : fmt(mix(xmin, xmax, f), xmax > 10 ? 0 : 1), a.x + f * a.w, a.y + a.h + 14, 10, C.muted, 'center'); }
    for (let i = 0; i <= 4; i++) { const f = i / 4; line(c, a.x, a.y + f * a.h, a.x + a.w, a.y + f * a.h, '#233e4c'); const val = mix(ymax, ymin, f); text(c, opt.yFormat ? opt.yFormat(val) : fmt(val, ymax > 5 ? 0 : 2), a.x - 8, a.y + f * a.h, 10, C.muted, 'right'); }
    line(c, a.x, a.y + a.h, a.x + a.w, a.y + a.h, C.muted, 1.1); line(c, a.x, a.y, a.x, a.y + a.h, C.muted, 1.1);
    if (opt.xlabel) text(c, opt.xlabel, a.x + a.w / 2, p.y + p.h - 5, 11, C.muted, 'center');
    if (opt.ylabel) text(c, opt.ylabel, a.x, a.y - 10, 11, C.muted);
    return a;
  }
  function plotFunction(c, a, fn, xmax, color, fraction = 1, dash) { const out = [], count = 160; for (let i = 0; i <= count * clamp(fraction, 0, 1); i++) { const x = xmax * i / count; out.push([a.X(x), a.Y(fn(x))]); } curve(c, out, color, 2.4, dash); }
  function legend(c, x, y, l, extra) { line(c, x, y, x + 21, y, C.blue, 3); text(c, tr(l, 'Lento', 'Slow'), x + 29, y, 12, C.blue); line(c, x + 111, y, x + 132, y, C.orange, 3); text(c, tr(l, 'Rápido', 'Fast'), x + 140, y, 12, C.orange); if (extra) text(c, extra, x, y + 19, 11, C.muted); }
  function clipped(c, p, fn) { c.save(); c.beginPath(); c.rect(p.x, p.y, p.w, p.h); c.clip(); fn(); c.restore(); }
  function molecule(c, x, y, r, color, angle) { halo(c, x, y, r * 4.2, color, .08); dot(c, x, y, r, color); if (angle !== undefined) { dot(c, x + Math.cos(angle) * r * 1.9, y + Math.sin(angle) * r * 1.9, r * .46, color); line(c, x, y, x + Math.cos(angle) * r * 1.9, y + Math.sin(angle) * r * 1.9, color, 1); } }
  function note(c, p, s, color = C.muted) { wrap(c, s, p.x + 14, p.y + p.h - 39, p.w - 28, p.w < 400 ? 10.5 : 12, color, 2); }

  function brownian(c, t, p, l, w, h) {
    frame(c, w, h, l, tr(l, 'La difusión es aleatoria; la medida es estadística', 'Motion is random; the measurement is statistical'));
    const panels = layout(w, h, 2, .62), arena = panel(c, panels[0], tr(l, 'Mismo tiempo, desplazamientos diferentes', 'Same time, different displacements'), tr(l, 'Proyección 2D · trazas individuales · no flujo dirigido', '2D projection · individual tracks · no directed flow'), l);
    const u = clamp(t / 18, 0, 1), T = p.Delta * 1e-3, data = walkers(8204, 46), physicalScale = Math.min(arena.w * .29, arena.h * .34) / 24;
    const center = [arena.x + arena.w * .5, arena.y + arena.h * .44];
    line(c, center[0] - arena.w * .4, center[1], center[0] + arena.w * .4, center[1], C.line); line(c, center[0], arena.y + 10, center[0], arena.y + arena.h * .87, C.line);
    clipped(c, arena, () => data.forEach((d, i) => {
      const D = (i % 2 ? p.Dfast : p.Dslow) * 1e-9, color = i % 2 ? C.orange : C.blue, sigma = Math.sqrt(2 * D * T) * 1e6 * physicalScale;
      const x0 = center[0] + (d.x0 - .5) * 20, y0 = center[1] + (d.y0 - .5) * 20;
      const trail = []; for (let v = Math.max(0, u - .25); v <= u + 1e-5; v += 1 / 180) trail.push([x0 + sample(d.x, v) * sigma, y0 + sample(d.y, v) * sigma]);
      c.globalAlpha = .42; curve(c, trail, color, 1.1); c.globalAlpha = 1;
      molecule(c, x0 + sample(d.x, u) * sigma, y0 + sample(d.y, u) * sigma, i % 2 ? 2.8 : 4.5, color, d.phase + t * (i % 2 ? 1.5 : .5));
    }));
    const bar = 10 * physicalScale; line(c, arena.x + 10, arena.y + arena.h - 25, arena.x + 10 + bar, arena.y + arena.h - 25, C.white, 2); text(c, '10 µm', arena.x + 10 + bar / 2, arena.y + arena.h - 10, 11, C.muted, 'center');
    legend(c, arena.x + 12, arena.y + arena.h - 51, l);
    const pp = panel(c, panels[1], tr(l, 'El promedio sí sigue una ley', 'The ensemble follows a law'), '⟨x²⟩ / µm²', l);
    const ymax = 2 * Math.max(p.Dslow, p.Dfast) * 1e-9 * T * 1e12 * 1.08;
    const a = axes(c, pp, { xmax: p.Delta, ymax, xlabel: tr(l, 'Tiempo / ms', 'Time / ms'), ylabel: '⟨x²⟩ / µm²' });
    plotFunction(c, a, x => 2 * p.Dslow * x, p.Delta, C.blue, u); plotFunction(c, a, x => 2 * p.Dfast * x, p.Delta, C.orange, u);
    const ms = u * p.Delta; dot(c, a.X(ms), a.Y(2 * p.Dslow * ms), 4, C.blue, true); dot(c, a.X(ms), a.Y(2 * p.Dfast * ms), 4, C.orange, true);
    footer(c, w, h, '⟨x²⟩ = 2Dt   ·   ⟨r²⟩₃ᴅ = 6Dt', tr(l, 'Una molécula no “mide D”. El conjunto de desplazamientos permite estimarlo. El tamaño de las partículas es simbólico; estas trayectorias son simuladas.', 'One molecule does not “measure D”. The ensemble of displacements allows D to be estimated. Particle sizes are symbolic; these paths are simulated.'), l);
  }

  function spinEcho(c, t, p, l, w, h) {
    frame(c, w, h, l, tr(l, 'El gradiente etiqueta posiciones; el movimiento deja fase', 'The gradient tags position; motion leaves phase'));
    const pp = layout(w, h, 2, .52), u = clamp(t / 18, 0, 1), encode = ease(u / .16), motion = ease((u - .16) / .44), invert = u >= .53, read = ease((u - .66) / .22);
    const q = GAMMA * p.g * 1e-3 * p.delta * 1e-3, T = p.Delta * 1e-3, data = walkers(14603, 48), residual = [], phaseStationary = [], phaseMoving = [];
    function drawBox(pos, moving) {
      const a = panel(c, pos, moving ? tr(l, 'Moléculas que difunden', 'Diffusing molecules') : tr(l, 'Moléculas inmóviles', 'Stationary molecules'), moving ? tr(l, 'La segunda etiqueta encuentra otra posición', 'The second tag finds a different position') : tr(l, 'La segunda etiqueta cancela la primera', 'The second tag cancels the first'), l);
      const areaH = Math.max(44, a.h * .55), spinR = Math.min(16, a.w / 28, areaH / 14);
      data.forEach((d, i) => {
        const x = a.x + 15 + (i % 8 + .5) * (a.w - 30) / 8, y = a.y + 12 + (Math.floor(i / 8) + .5) * areaH / 6;
        const z0 = (d.x0 - .5) * 60e-6, dz = moving ? sample(d.z, motion) * Math.sqrt(2 * p.D * 1e-9 * T) : 0;
        const first = q * z0 * encode, phase = (invert ? -first : first) + q * (z0 + dz) * read;
        (moving ? phaseMoving : phaseStationary).push(phase); if (moving) residual.push(dz);
        c.save(); c.globalAlpha = .16; c.strokeStyle = C.white; c.beginPath(); c.arc(x, y, spinR, 0, TAU); c.stroke(); c.restore();
        const color = moving ? C.orange : C.blue; arrow(c, x, y, Math.cos(phase) * spinR * .85, -Math.sin(phase) * spinR * .85, color, 1.7, 4);
        if (moving && motion > .03) { const dx = clamp(dz * 1e6, -15, 15) * .22; dot(c, x + dx, y + spinR + 6, 1.6, color); }
      });
      const phases = moving ? phaseMoving : phaseStationary, re = phases.reduce((v, x) => v + Math.cos(x), 0) / phases.length, im = phases.reduce((v, x) => v + Math.sin(x), 0) / phases.length;
      const cx = a.x + a.w * .22, cy = a.y + areaH + (a.h - areaH) * .57, R = Math.min(44, Math.max(17, (a.h - areaH) * .34));
      c.beginPath(); c.arc(cx, cy, R, 0, TAU); c.strokeStyle = C.line; c.stroke(); arrow(c, cx, cy, re * R, -im * R, moving ? C.orange : C.blue, 3, 7);
      text(c, tr(l, 'Suma de fases', 'Phase sum'), a.x + a.w * .43, cy - 10, 12, C.muted);
      text(c, '|⟨eⁱᵠ⟩| = ' + fmt(Math.hypot(re, im)), a.x + a.w * .43, cy + 13, a.w < 380 ? 13 : 18, moving ? C.orange : C.blue, 'left', 600);
    }
    drawBox(pp[0], false); drawBox(pp[1], true);
    const phase = u < .16 ? tr(l, '01 · Etiquetar con g₁', '01 · Tag with g₁') : u < .53 ? tr(l, '02 · Esperar Δ', '02 · Wait Δ') : u < .66 ? tr(l, '03 · Pulso 180°: invertir fase', '03 · 180° pulse: invert phase') : u < .88 ? tr(l, '04 · Aplicar g₂', '04 · Apply g₂') : tr(l, '05 · Leer el eco', '05 · Read the echo');
    footer(c, w, h, phase, tr(l, 'Aproximación de pulsos estrechos: φ=q(z₂−z₁), b≈q²Δ. La suma finita fluctúa alrededor de e⁻ᵇᴰ. Para pulsos finitos usar Δ−δ/3; se omiten relajación y gradientes auxiliares.', 'Narrow-pulse approximation: φ=q(z₂−z₁), b≈q²Δ. A finite ensemble fluctuates around e⁻ᵇᴰ. For finite pulses use Δ−δ/3; relaxation and auxiliary gradients are omitted.'), l);
  }

  function gradientsB(c, t, p, l, w, h) {
    frame(c, w, h, l, tr(l, 'No basta con conocer la amplitud del gradiente', 'Gradient amplitude is only part of the encoding'));
    const pos = layout(w, h, 1)[0], inner = panel(c, pos, tr(l, 'Del programa de pulsos a b', 'From the pulse program to b'), tr(l, 'PGSE rectangular · el pulso 180° cambia el signo efectivo', 'Rectangular PGSE · the 180° pulse changes the effective sign'), l);
    const total = p.Delta + p.delta + 10, d = p.delta, first = 5, second = 5 + p.Delta, maxQ = GAMMA * p.g * 1e-3 * d * 1e-3, maxQ2 = (maxQ / 1e5) ** 2, progress = t / 18 * total;
    const rowH = Math.max(42, (inner.h - 35) / 3), left = w < 600 ? 43 : 65, rw = inner.w - left - 10;
    const X = ms => inner.x + left + ms / total * rw;
    function gg(ms) { return ((ms >= first && ms <= first + d) || (ms >= second && ms <= second + d)) ? 1 : 0; }
    function qq(ms) { if (ms < first) return 0; if (ms < first + d) return (ms - first) / d; if (ms < second) return 1; if (ms < second + d) return 1 - (ms - second) / d; return 0; }
    for (let row = 0; row < 3; row++) {
      const y = inner.y + row * rowH + 11, height = rowH - 22, baseline = y + height;
      line(c, X(0), baseline, X(total), baseline, C.muted);
      [0, .25, .5, .75, 1].forEach(f => line(c, X(f * total), y, X(f * total), baseline, C.line));
      const fn = row === 0 ? gg : row === 1 ? qq : ms => qq(ms) ** 2;
      const pts = []; for (let i = 0; i <= 500; i++) { const ms = total * i / 500; pts.push([X(ms), baseline - fn(ms) * height * .83]); }
      curve(c, pts, row === 0 ? C.white : row === 1 ? C.blue : C.orange, 2.4);
      if (row === 2) { const shade = pts.filter(v => v[0] <= X(progress)); if (shade.length > 1) { c.beginPath(); c.moveTo(shade[0][0], baseline); shade.forEach(v => c.lineTo(v[0], v[1])); c.lineTo(shade[shade.length - 1][0], baseline); c.closePath(); c.fillStyle = '#ffba682b'; c.fill(); } }
      const name = row === 0 ? 'g(t)' : row === 1 ? 'q(t)' : 'q²(t)'; text(c, name, inner.x + 3, y + height * .5, w < 600 ? 12 : 17, row === 0 ? C.white : row === 1 ? C.blue : C.orange, 'left', 600);
      const unit = row === 0 ? fmt(p.g, 0) + ' mT/m' : row === 1 ? fmt(maxQ / 1e5) + ' ×10⁵ rad/m' : fmt(maxQ2) + ' ×10¹⁰ rad²/m²';
      if (rw > 340) text(c, unit, X(total) - 4, y + 9, 11, C.muted, 'right');
      line(c, X(progress), y, X(progress), baseline, C.green, 1.5);
      const mid = 5 + p.Delta / 2; line(c, X(mid), y, X(mid), baseline, '#c9a9ff65', 1, [3, 4]);
      if (row === 0) text(c, '180°', X(mid), y - 2, 10, C.purple, 'center');
      if (row === 2) text(c, tr(l, 'Área acumulada = b', 'Accumulated area = b'), X(total * .4), baseline - height * .4, w < 600 ? 11 : 15, C.orange);
    }
    const by = inner.y + rowH * 3 + 5;
    text(c, tr(l, 'Tiempo / ms', 'Time / ms'), inner.x + inner.w * .53, by + 6, 11, C.muted, 'center');
    [0, p.Delta / 2, p.Delta].forEach(ms => text(c, fmt(ms, 0), X(ms), by - 12, 10, C.muted, 'center'));
    const b = B(p);
    footer(c, w, h, 'b = γ²g²δ²(Δ−δ/3) = ' + fmt(b / 1e9) + ' ×10⁹ s/m²', tr(l, 'q(t)=γ∫s(t)g(t)dt; b=∫q²(t)dt. Para otra secuencia hay que integrar su gradiente efectivo, incluidos lóbulos y retardos. q no es g instantáneo.', 'q(t)=γ∫s(t)g(t)dt; b=∫q²(t)dt. For another sequence, integrate its effective gradient, including lobes and delays. q is not the instantaneous gradient.'), l);
  }

  function attenuationMixture(c, t, p, l, w, h) {
    frame(c, w, h, l, tr(l, 'La señal cae antes de que aparezca un mapa DOSY', 'Signal attenuation comes before the DOSY map'));
    const panels = layout(w, h, 2, .62), u = clamp(t / 18, 0, 1), f = p.fraction;
    const left = panel(c, panels[0], tr(l, 'Dos poblaciones, una atenuación', 'Two populations, one attenuation'), tr(l, 'Puntos: señal simulada con ruido fijo', 'Points: simulated signal with fixed noise'), l);
    const a = axes(c, left, { xmax: p.bmax, ymax: 1.06, xlabel: 'b / 10⁹ s m⁻²', ylabel: 'S / S₀' });
    const slow = b => Math.exp(-b * p.Dslow), fast = b => Math.exp(-b * p.Dfast), signal = b => f * slow(b) + (1 - f) * fast(b);
    plotFunction(c, a, b => f * slow(b), p.bmax, C.blue, u); plotFunction(c, a, b => (1 - f) * fast(b), p.bmax, C.orange, u); plotFunction(c, a, signal, p.bmax, C.white, u);
    const r = rng(54234); for (let i = 0; i < 24; i++) { const x = p.bmax * (i / 23) ** 2, noise = gaussian(r) * p.noise / 100; if (x <= u * p.bmax) dot(c, a.X(x), a.Y(signal(x) + noise), 3, C.green); }
    line(c, a.X(u * p.bmax), a.y, a.X(u * p.bmax), a.y + a.h, '#83edd16b', 1, [4, 5]);
    const right = panel(c, panels[1], tr(l, 'Composición conocida de la simulación', 'Known composition of the simulation'), tr(l, 'No es una reconstrucción ILT', 'This is not an ILT reconstruction'), l);
    const x0 = right.x + 13, bw = right.w - 26, y0 = right.y + right.h * .18, bh = Math.min(36, right.h * .12);
    rect(c, x0, y0, bw, bh, 5, C.line); rect(c, x0, y0, bw * f, bh, 5, C.blue); rect(c, x0 + bw * f, y0, bw * (1 - f), bh, 5, C.orange);
    text(c, Math.round(f * 100) + '%', x0 + bw * f / 2, y0 + bh / 2, 14, C.bg, 'center', 700); text(c, Math.round((1 - f) * 100) + '%', x0 + bw * (f + (1 - f) / 2), y0 + bh / 2, 14, C.bg, 'center', 700);
    text(c, 'D = ' + fmt(p.Dslow) + ' ×10⁻⁹ m²/s', x0, right.y + right.h * .43, right.w < 380 ? 13 : 18, C.blue);
    text(c, 'D = ' + fmt(p.Dfast) + ' ×10⁻⁹ m²/s', x0, right.y + right.h * .57, right.w < 380 ? 13 : 18, C.orange);
    const by = right.y + right.h * .72;
    text(c, tr(l, 'A b seleccionado:', 'At the selected b:'), x0, by, 13, C.muted);
    text(c, 'S/S₀ = ' + fmt(signal(u * p.bmax), 3), x0, right.y + right.h * .88, right.w < 380 ? 18 : 27, C.white, 'left', 650);
    footer(c, w, h, 'S(b) = A₁e⁻ᵇᴰ¹ + A₂e⁻ᵇᴰ²', tr(l, 'Una señal aislada puede ser monoexponencial. Un solapamiento puede sumar varias atenuaciones; aumentar el número de exponentes no garantiza identificarlos.', 'An isolated resonance may be monoexponential. An overlap can sum multiple attenuations; increasing the number of exponentials does not guarantee identification.'), l);
  }

  function pulse90(c, t, p, l, w, h) {
    frame(c, w, h, l, tr(l, 'Primero calibrar P1: buscar el nulo de 180°', 'Calibrate P1 first: locate the 180° null'));
    const panels = layout(w, h, 2, .64), left = panel(c, panels[0], tr(l, 'Experimento 1000 · amplitud con signo', 'Experiment 1000 · signed amplitude'), tr(l, 'Misma fase, potencia, muestra y recuperación', 'Same phase, power, sample and recovery'), l);
    const xmax = p.p90 * 2.4, a = axes(c, left, { xmax, ymin: -.72, ymax: 1.15, xlabel: 'P1 / µs', ylabel: 'S / S₀' }), u = clamp(t / 18, 0, 1), scan = xmax * Math.min(1, u / .75);
    const signal = x => Math.sin(Math.PI * x / (2 * p.p90));
    plotFunction(c, a, signal, xmax, C.white, Math.min(1, u / .75)); line(c, a.X(0), a.Y(0), a.X(xmax), a.Y(0), '#92aeba88', 1.2);
    const r = rng(28305); for (let i = 0; i <= 24; i++) { const x = i / 24 * xmax, noise = gaussian(r) * p.noise / 100; if (x <= scan) dot(c, a.X(x), a.Y(signal(x) + noise), 2.7, x < p.p90 * 1.5 ? C.blue : C.red); }
    line(c, a.X(p.p90), a.y, a.X(p.p90), a.y + a.h, C.blue, 1.5, [5, 4]); line(c, a.X(2 * p.p90), a.y, a.X(2 * p.p90), a.y + a.h, C.red, 1.5, [5, 4]);
    text(c, '90°', a.X(p.p90), a.y + 12, 12, C.blue, 'center', 650); text(c, '180°', a.X(2 * p.p90), a.y + 12, 12, C.red, 'center', 650);
    if (u < .8) dot(c, a.X(scan), a.Y(signal(scan)), 5, C.green, true); else dot(c, a.X(p.p90), a.Y(1), 7, C.blue, true);
    const right = panel(c, panels[1], tr(l, 'Del nulo al pulso de trabajo', 'From the null to the working pulse'), tr(l, 'Rotación ideal: θ = γB₁P1', 'Ideal rotation: θ = γB₁P1'), l);
    const cx = right.x + right.w / 2, cy = right.y + right.h * .34, R = Math.min(right.w * .29, right.h * .27), use = u < .8 ? scan : p.p90, theta = Math.PI * use / (2 * p.p90);
    c.save(); c.strokeStyle = '#33596a'; c.lineWidth = 1.5; c.beginPath(); c.ellipse(cx, cy, R, R * .24, 0, 0, TAU); c.stroke(); c.beginPath(); c.arc(cx, cy, R, 0, TAU); c.stroke(); c.restore();
    line(c, cx, cy + R * 1.15, cx, cy - R * 1.15, C.muted); text(c, 'M_z', cx + 12, cy - R * 1.1, 12, C.muted);
    arrow(c, cx, cy, Math.sin(theta) * R, -Math.cos(theta) * R, u >= .8 ? C.blue : C.green, 4, 10);
    text(c, fmt(theta * 180 / Math.PI, 0) + '°', cx, cy + R + 23, 16, C.white, 'center', 650);
    text(c, 'P180 = ' + fmt(2 * p.p90, 1) + ' µs', right.x + 10, right.y + right.h * .74, right.w < 380 ? 15 : 21, C.red);
    text(c, 'P90 = P180 / 2 = ' + fmt(p.p90, 1) + ' µs', right.x + 10, right.y + right.h * .87, right.w < 380 ? 14 : 21, C.blue, 'left', 600);
    footer(c, w, h, 'S(P1) ∝ sin(γB₁P1)   ·   P90 = P180 / 2', tr(l, 'Buscar el primer nulo no trivial y comprobar el cambio de signo. Integrar una señal con fase fija; la magnitud pierde el signo. B₁ no uniforme y recuperación insuficiente deforman la curva.', 'Find the first nontrivial null and check the sign reversal. Integrate a resonance at fixed phase; magnitude loses the sign. B₁ inhomogeneity and incomplete recovery distort the curve.'), l);
  }

  function acquisitionWindow(c, t, p, l, w, h) {
    frame(c, w, h, l, tr(l, 'δ y Δ deciden si los datos contienen información', 'δ and Δ determine whether the data are informative'));
    const pos = layout(w, h, 1)[0], inner = panel(c, pos, tr(l, 'Tres rampas de gradiente · 8–96 %', 'Three gradient ramps · 8–96%'), tr(l, 'No elegir parámetros mirando solo el primer espectro', 'Do not select parameters using only the first spectrum'), l);
    const mobile = w < 600, rows = 3, rowH = (inner.h - (mobile ? 46 : 30)) / rows, deltas = [p.Delta * .5, p.Delta, p.Delta * 1.5], u = clamp(t / 18, 0, 1), floor = p.noise / 100;
    deltas.forEach((Delta, i) => {
      const left = mobile ? 40 : 65, right = mobile ? 8 : 205, area = { x: inner.x + left, y: inner.y + i * rowH + 8, w: inner.w - left - right, h: rowH - 28 }, X = pct => area.x + (pct - 8) / 88 * area.w, Y = s => area.y + area.h * (1 - s);
      [0, .25, .5, .75, 1].forEach(s => line(c, area.x, Y(s), area.x + area.w, Y(s), C.line));
      c.fillStyle = '#ff748c22'; c.fillRect(area.x, Y(Math.min(1, floor * 3)), area.w, area.h * Math.min(1, floor * 3));
      const curves = [[], []], full = [[], []];
      for (let g = 8; g <= 96; g += .4) { const b = B({ g: p.Gmax * g / 100, delta: p.delta, Delta }); [p.Dslow, p.Dfast].forEach((D, j) => { const pt = [X(g), Y(Math.exp(-b * D * 1e-9))]; full[j].push(pt); if (g <= 8 + 88 * u) curves[j].push(pt); }); }
      curve(c, full[0], '#53d4ff33', 1.5); curve(c, full[1], '#ffba6833', 1.5); curve(c, curves[0], C.blue, 2.3); curve(c, curves[1], C.orange, 2.3);
      text(c, fmt(Delta, 0) + ' ms', inner.x, area.y + area.h / 2, mobile ? 10 : 13, C.white, 'left', 600);
      const pct = 8 + 88 * u; line(c, X(pct), area.y, X(pct), area.y + area.h, C.green, 1.5);
      if (!mobile) {
        const endb = B({ g: p.Gmax * .96, delta: p.delta, Delta }), slow = Math.exp(-endb * p.Dslow * 1e-9), fast = Math.exp(-endb * p.Dfast * 1e-9);
        const usable = slow < .7 && fast > floor * 3, kind = fast < floor * 3 ? tr(l, 'Rápido bajo el ruido', 'Fast below noise') : slow > .7 ? tr(l, 'Lento poco atenuado', 'Slow barely attenuated') : tr(l, 'Ventana informativa', 'Informative window');
        text(c, 'S(96%)/S₀', area.x + area.w + 18, area.y + 10, 11, C.muted);
        text(c, fmt(slow, 3) + '  /  ' + fmt(fast, 3), area.x + area.w + 18, area.y + 35, 17, C.white, 'left', 600);
        wrap(c, kind, area.x + area.w + 18, area.y + 58, 160, 12, usable ? C.green : C.red, 2);
      }
      [8, 52, 96].forEach(g => text(c, String(g), X(g), area.y + area.h + 11, 10, C.muted, 'center'));
    });
    legend(c, inner.x + 10, inner.y + inner.h - (mobile ? 28 : 8), l);
    text(c, tr(l, 'Gradiente / % del máximo del ejemplo', 'Gradient / % of example maximum'), mobile ? inner.x + inner.w / 2 : inner.x + inner.w - 4, inner.y + inner.h - 7, mobile ? 9 : 11, C.muted, mobile ? 'center' : 'right');
    footer(c, w, h, 'b ∝ δ²(Δ−δ/3)   ·   ↑Δ → ' + tr(l, 'más atenuación y más tiempo', 'more attenuation and more time'), tr(l, 'Rojo: 3σ de ruido. Hay que atenuar la población lenta y conservar la rápida medible. p30 y d20 no equivalen universalmente a δ y Δ: comprobar el programa; LED y doble STE necesitan sus propios tiempos.', 'Red: 3σ noise floor. Attenuate the slow population while keeping the fast one measurable. p30 and d20 do not universally equal δ and Δ: inspect the pulse program; LED and double STE have additional timing.'), l);
  }

  function convection(c, t, p, l, w, h) {
    frame(c, w, h, l, tr(l, 'El flujo puede disfrazarse de difusión', 'Flow can masquerade as diffusion'));
    const pos = layout(w, h, 2, .5), inner = panel(c, pos[0], tr(l, 'Velocidades coherentes y dispersas', 'Coherent and dispersed velocities'), tr(l, 'Proyección de movimiento · campo de velocidades ilustrado', 'Projected motion · illustrative velocity field'), l);
    const cx = inner.x + inner.w / 2, cy = inner.y + inner.h * .42, tubeW = inner.w * .62, tubeH = inner.h * .71, data = walkers(62172, 46), u = clamp(t / 18, 0, 1), T = p.Delta * 1e-3, scale = Math.min(tubeW / 30, tubeH / 35);
    rect(c, cx - tubeW / 2, cy - tubeH / 2, tubeW, tubeH, Math.min(24, tubeW / 6), '#122b3a80', '#5a8092');
    clipped(c, { x: cx - tubeW / 2 + 2, y: cy - tubeH / 2 + 2, w: tubeW - 4, h: tubeH - 4 }, () => data.forEach((d, i) => {
      const x0 = (d.x0 - .5) * tubeW * .8, y0 = (d.y0 - .5) * tubeH * .8, v = p.velocity + p.spread * d.z[WALK_STEPS], sigma = Math.sqrt(2 * p.D * 1e-9 * T) * 1e6 * scale;
      const x = cx + x0 + sample(d.x, u) * sigma * .35, y = cy + y0 - v * T * u * scale + sample(d.y, u) * sigma * .35;
      molecule(c, x, y, 3.3, i % 2 ? C.orange : C.blue, d.phase + t);
    }));
    [-.34, 0, .34].forEach(f => { const v = p.velocity + p.spread * f * Math.sqrt(12); arrow(c, cx + f * tubeW, cy + tubeH * .34, 0, -clamp(v, -100, 100) * .5, C.red, 2.3, 7); });
    text(c, 'v̄ = ' + fmt(p.velocity, 0) + ' µm/s', inner.x + 7, inner.y + inner.h - 37, 14, C.white);
    text(c, 'σᵥ = ' + fmt(p.spread, 0) + ' µm/s', inner.x + 7, inner.y + inner.h - 14, 14, C.red);
    const right = panel(c, pos[1], tr(l, 'La fase y la magnitud cuentan cosas distintas', 'Phase and magnitude tell different stories'), tr(l, 'Modelo de velocidades gaussianas constantes', 'Constant Gaussian velocity model'), l);
    const b = B(p), xmax = Math.max(3, b / 1e9 * 1.06), a = axes(c, right, { xmax, ymax: 1.06, xlabel: 'b / 10⁹ s m⁻²', ylabel: '|S| / S₀' });
    const commonPhase = GAMMA * p.g * .001 * p.delta * .001 * p.velocity * 1e-6 * T;
    const loss = bval => Math.exp(-bval * p.D) * Math.exp(-.5 * bval * 1e9 / Math.max(T - p.delta * .001 / 3, 1e-5) * (T * p.spread * 1e-6) ** 2);
    plotFunction(c, a, x => Math.exp(-x * p.D), xmax, C.blue); plotFunction(c, a, loss, xmax, C.red);
    const bx = b / 1e9; dot(c, a.X(bx), a.Y(loss(bx)), 5, C.red, true);
    text(c, tr(l, 'Solo difusión', 'Diffusion only'), a.x + 12, a.y + 17, 11, C.blue); text(c, tr(l, 'Con dispersión de v', 'With velocity spread'), a.x + 12, a.y + 35, 11, C.red);
    text(c, 'φ(v̄) = ' + fmt(commonPhase) + ' rad', a.x + 12, a.y + a.h - 19, 12, C.white);
    footer(c, w, h, 'S = e⁻ᵇᴰ · ⟨eⁱqᵛΔ⟩   ·   φ = qv̄Δ', tr(l, 'Un flujo uniforme cambia la fase, no la magnitud ideal. Una distribución de velocidades desfasará el conjunto. La compensación de primer momento cancela velocidad constante ideal; no toda convección.', 'Uniform flow changes phase, not ideal magnitude. A velocity distribution dephases the ensemble. First-moment compensation cancels ideal constant velocity; it does not remove all convection.'), l);
  }

  function overlapJoint(c, t, p, l, w, h) {
    frame(c, w, h, l, tr(l, 'Una frecuencia puede mezclar moléculas; varias pueden ayudar', 'One frequency can mix molecules; several can help'));
    const panels = layout(w, h, 2, .61), left = panel(c, panels[0], tr(l, 'Todo el espectro comparte los mismos D', 'The whole spectrum shares the same D values'), tr(l, 'Espectros simulados · alturas relativas', 'Simulated spectra · relative heights'), l);
    const lorentz = (x, m, a, width) => a * width * width / ((x - m) ** 2 + width * width);
    const specA = x => lorentz(x, 5.08, .82, .08) + lorentz(x, 1.28, .68, .048) + lorentz(x, 3.46, .35, .055);
    const specB = x => lorentz(x, 5.25, .8, .085) + lorentz(x, 6.68, .54, .058) + lorentz(x, 2.65, .43, .063);
    const u = clamp(t / 18, 0, 1), currentB = p.bmax * u, X = ppm => left.x + 40 + (8 - ppm) / 8 * (left.w - 52), base = left.y + left.h - 37, height = left.h - 70;
    [0, 2, 4, 6, 8].forEach(ppm => { line(c, X(ppm), left.y + 15, X(ppm), base, C.line); text(c, String(ppm), X(ppm), base + 15, 10, C.muted, 'center'); });
    line(c, X(8), base, X(0), base, C.muted);
    const curves = [[], [], []]; for (let i = 0; i <= 480; i++) { const x = 8 * i / 480, A = specA(x) * Math.exp(-currentB * p.Dslow), BB = specB(x) * Math.exp(-currentB * p.Dfast); curves[0].push([X(x), base - A * height * .63]); curves[1].push([X(x), base - BB * height * .63]); curves[2].push([X(x), base - (A + BB) * height * .63]); }
    [C.blue, C.orange, C.white].forEach((color, j) => curve(c, curves[j], color, j === 2 ? 2.2 : 1.8));
    const px = X(p.ppm); line(c, px, left.y + 8, px, base, C.green, 1.5, [4, 4]); text(c, fmt(p.ppm) + ' ppm', clamp(px, left.x + 50, left.x + left.w - 48), left.y + 6, 12, C.green, 'center');
    text(c, '¹H / ppm', left.x + left.w / 2, left.y + left.h - 4, 11, C.muted, 'center'); text(c, 'b = ' + fmt(currentB) + ' ×10⁹ s/m²', left.x + 45, left.y + 29, 11, C.muted);
    const right = panel(c, panels[1], tr(l, 'Atenuación en la frecuencia elegida', 'Attenuation at the selected frequency'), tr(l, 'La amplitud cambia con ν; D es compartido', 'Amplitude changes with ν; D is shared'), l);
    const A = specA(p.ppm), BB = specB(p.ppm), sum = A + BB, fa = A / Math.max(sum, 1e-12), a = axes(c, right, { xmax: p.bmax, ymax: 1.05, xlabel: 'b / 10⁹ s m⁻²', ylabel: 'S(b,ν) / S(0,ν)' });
    plotFunction(c, a, b => fa * Math.exp(-b * p.Dslow), p.bmax, C.blue); plotFunction(c, a, b => (1 - fa) * Math.exp(-b * p.Dfast), p.bmax, C.orange); plotFunction(c, a, b => fa * Math.exp(-b * p.Dslow) + (1 - fa) * Math.exp(-b * p.Dfast), p.bmax, C.white, u);
    dot(c, a.X(currentB), a.Y(fa * Math.exp(-currentB * p.Dslow) + (1 - fa) * Math.exp(-currentB * p.Dfast)), 4.5, C.green, true);
    text(c, 'A₁(ν): ' + Math.round(fa * 100) + '%', a.x + 10, a.y + 17, 11, C.blue); text(c, 'A₂(ν): ' + Math.round((1 - fa) * 100) + '%', a.x + 10, a.y + 35, 11, C.orange);
    footer(c, w, h, 'Y(b,ν) ≈ Σₖ Aₖ(ν)e⁻ᵇᴰᵏ   ·   Dₖ compartido / shared', tr(l, 'Las correlaciones entre frecuencias aportan restricciones al ajuste conjunto. Son útiles si el modelo se cumple; no convierten resonancias solapadas en identidades químicas por sí solas.', 'Correlations across frequencies constrain a joint fit. They help when the model is valid; they do not by themselves turn overlapping resonances into chemical identities.'), l);
  }

  function ilt(c, t, p, l, w, h) {
    frame(c, w, h, l, tr(l, 'Curvas casi idénticas pueden esconder distribuciones distintas', 'Almost identical curves can hide different distributions'));
    const panels = layout(w, h, 2, .49), D0 = .55, d1 = D0 - p.separation / 2, d2 = D0 + p.separation / 2, left = panel(c, panels[0], tr(l, 'Dos distribuciones candidatas', 'Two candidate distributions'), tr(l, 'La verdad de este ejemplo es conocida', 'The truth of this example is known'), l);
    const a = axes(c, left, { xmax: 1.1, ymax: 1.08, xlabel: 'D / 10⁻⁹ m² s⁻¹', ylabel: tr(l, 'Distribución / u.a.', 'Distribution / a.u.') });
    const width = .014, gauss = (x, mean, sd) => Math.exp(-.5 * ((x - mean) / sd) ** 2), u = clamp(t / 18, 0, 1);
    plotFunction(c, a, x => gauss(x, D0, width), 1.1, C.blue);
    plotFunction(c, a, x => .5 * gauss(x, d1, width) + .5 * gauss(x, d2, width), 1.1, C.orange);
    const smoothedWidth = width + p.regularization * .11;
    const smoothPoints = []; for (let i = 0; i <= 200; i++) { const x = 1.1 * i / 200, v = width / smoothedWidth * .5 * (gauss(x, d1, smoothedWidth) + gauss(x, d2, smoothedWidth)); smoothPoints.push([a.X(x), a.Y(v)]); }
    if (p.regularization > .015) curve(c, smoothPoints, C.green, 2.2, [5, 3]);
    text(c, tr(l, 'A · una población', 'A · one population'), a.x + 9, a.y + 15, 11, C.blue); text(c, tr(l, 'B · dos poblaciones próximas', 'B · two nearby populations'), a.x + 9, a.y + 33, 11, C.orange);
    text(c, tr(l, 'Verde: suavizado esquemático', 'Green: schematic smoothing'), a.x + 9, a.y + 52, 10.5, C.green);
    const right = panel(c, panels[1], tr(l, 'El núcleo exponencial borra diferencias', 'The exponential kernel erases differences'), tr(l, 'Banda gris: ±1σ del ruido indicado', 'Grey band: ±1σ of the selected noise'), l);
    const ar = axes(c, right, { xmax: p.bmax, ymax: 1.05, xlabel: 'b / 10⁹ s m⁻²', ylabel: 'S / S₀' }), sA = b => Math.exp(-b * D0), sB = b => .5 * Math.exp(-b * d1) + .5 * Math.exp(-b * d2);
    const lower = [], upper = []; for (let i = 0; i <= 160; i++) { const b = p.bmax * i / 160; lower.push([ar.X(b), ar.Y(sA(b) - p.noise / 100)]); upper.push([ar.X(b), ar.Y(sA(b) + p.noise / 100)]); }
    c.beginPath(); upper.forEach((v, i) => i ? c.lineTo(v[0], v[1]) : c.moveTo(v[0], v[1])); lower.reverse().forEach(v => c.lineTo(v[0], v[1])); c.closePath(); c.fillStyle = '#edf8fd22'; c.fill();
    plotFunction(c, ar, sA, p.bmax, C.blue, u); plotFunction(c, ar, sB, p.bmax, C.orange, u, [5, 3]);
    let maxDiff = 0; for (let i = 0; i < 400; i++) maxDiff = Math.max(maxDiff, sB(p.bmax * i / 399) - sA(p.bmax * i / 399));
    const r = rng(16784); for (let i = 0; i < 22; i++) { const b = p.bmax * i / 21, noise = gaussian(r) * p.noise / 100; if (i / 21 <= u) dot(c, ar.X(b), ar.Y(sB(b) + noise), 2.5, C.white); }
    text(c, 'max |ΔS| / S₀ = ' + fmt(maxDiff * 100, 2) + '%', ar.x + 10, ar.y + ar.h - 42, ar.w < 250 ? 10.5 : 13, C.white);
    text(c, 'σ / S₀ = ' + fmt(p.noise, 1) + '%', ar.x + 10, ar.y + ar.h - 20, 12, C.muted);
    footer(c, w, h, 'S(b) = ∫f(D)e⁻ᵇᴰdD   ·   datos finitos / finite data', tr(l, 'Invertir amplifica el ruido. La regularización impone una preferencia y cambia la resolución. El control verde ilustra suavizado de candidatos: no ejecuta un solver ILT ni demuestra separación experimental.', 'Inversion amplifies noise. Regularization imposes a preference and changes resolution. The green control illustrates smoothing of candidates: it does not run an ILT solver or demonstrate experimental separation.'), l);
  }

  function reflect(x, a) { const z = ((x + a / 2) % (2 * a) + 2 * a) % (2 * a); return z <= a ? z - a / 2 : 1.5 * a - z; }
  function restricted(c, t, p, l, w, h) {
    frame(c, w, h, l, tr(l, 'Las paredes cambian qué significa “D”', 'Boundaries change what “D” means'));
    const panels = layout(w, h, 2, .5), inner = panel(c, panels[0], tr(l, 'Un poro con paredes reflectantes', 'A pore with reflecting boundaries'), tr(l, 'Modelo 1D de una rendija · equilibrio inicial uniforme', '1D slit model · uniform initial equilibrium'), l);
    const data = walkers(37487, 180), u = clamp(t / 18, 0, 1), T = p.Delta * 1e-3, sigma = Math.sqrt(2 * p.D * 1e-9 * T) * 1e6, cx = inner.x + inner.w / 2, cy = inner.y + inner.h / 2, scale = (inner.w * .72) / p.width, top = inner.y + 20, bottom = inner.y + inner.h - 55, xL = cx - p.width / 2 * scale, xR = cx + p.width / 2 * scale;
    rect(c, xL, top, xR - xL, bottom - top, 0, '#16394b66'); line(c, xL, top, xL, bottom, C.blue, 3); line(c, xR, top, xR, bottom, C.blue, 3);
    clipped(c, { x: xL, y: top, w: xR - xL, h: bottom - top }, () => data.slice(0, 42).forEach((d, i) => {
      const initial = (d.x0 - .5) * p.width, trace = [];
      for (let v = Math.max(0, u - .28); v <= u + 1e-5; v += 1 / 180) trace.push([cx + reflect(initial + sample(d.x, v) * sigma, p.width) * scale, top + (d.y0 * .9 + .05) * (bottom - top)]);
      curve(c, trace, '#53d4ff66', 1.3); molecule(c, cx + reflect(initial + sample(d.x, u) * sigma, p.width) * scale, top + (d.y0 * .9 + .05) * (bottom - top), 3.2, C.blue, d.phase + t);
    }));
    line(c, xL, bottom + 19, xR, bottom + 19, C.white, 1); text(c, 'a = ' + fmt(p.width, 0) + ' µm', cx, bottom + 36, 13, C.white, 'center');
    const right = panel(c, panels[1], tr(l, 'El desplazamiento acaba saturándose', 'Displacement eventually saturates'), tr(l, 'MSD numérico del conjunto y referencia libre', 'Numerical ensemble MSD and free reference'), l);
    const maxMSD = Math.max(2 * p.D * p.Delta, p.width ** 2 / 6) * 1.06, a = axes(c, right, { xmax: p.Delta, ymax: maxMSD, xlabel: tr(l, 'Tiempo / ms', 'Time / ms'), ylabel: '⟨Δx²⟩ / µm²' });
    plotFunction(c, a, ms => 2 * p.D * ms, p.Delta, C.orange, u);
    const points = [];
    for (let k = 0; k <= 60 * u; k++) { const v = k / 60, msd = data.reduce((sum, d) => { const x0 = (d.x0 - .5) * p.width, dx = reflect(x0 + sample(d.x, v) * sigma, p.width) - x0; return sum + dx * dx; }, 0) / data.length; points.push([a.X(v * p.Delta), a.Y(msd)]); }
    curve(c, points, C.blue, 2.5); line(c, a.x, a.Y(p.width ** 2 / 6), a.x + a.w, a.Y(p.width ** 2 / 6), '#53d4ff77', 1, [4, 4]);
    text(c, tr(l, 'Libre', 'Free'), a.x + 9, a.y + 16, 12, C.orange); text(c, tr(l, 'Restringida', 'Restricted'), a.x + 9, a.y + 35, 12, C.blue); text(c, 'a² / 6', a.x + a.w - 8, a.Y(p.width ** 2 / 6) - 10, 10, C.blue, 'right');
    footer(c, w, h, 'Dapp(Δ) ≈ ⟨Δx²⟩ / (2Δ)   ·   régimen de q pequeño / small-q limit', tr(l, 'El D aparente depende del tiempo de observación. La relación MSD–Dapp es de bajo q y pulsos estrechos; una atenuación completa en un poro no tiene por qué ser monoexponencial.', 'Apparent D depends on observation time. The MSD–Dapp relation uses small q and narrow pulses; full attenuation in a pore need not be monoexponential.'), l);
  }

  function exchangeSignal(b, T, k, d1, d2) {
    const q2 = b * 1e9 / Math.max(T, .0001), a = -.5 * q2 * (d1 - d2) * 1e-9, r = Math.hypot(a, k), m = -.5 * q2 * (d1 + d2) * 1e-9 - k;
    if (r < 1e-12) return Math.exp(m * T);
    return .5 * ((1 + k / r) * Math.exp((m + r) * T) + (1 - k / r) * Math.exp((m - r) * T));
  }
  function exchange(c, t, p, l, w, h) {
    frame(c, w, h, l, tr(l, 'Durante Δ, una molécula puede cambiar de entorno', 'During Δ, a molecule may change environment'));
    const panels = layout(w, h, 2, .53), left = panel(c, panels[0], tr(l, 'Dos estados y una tasa de intercambio', 'Two states and an exchange rate'), tr(l, 'Cambio de color = cambio de estado; posiciones esquemáticas', 'Colour change = state change; positions are schematic'), l), u = clamp(t / 18, 0, 1), T = p.Delta * .001;
    const phaseX = left.x + left.w * .5, top = left.y + 14, bottom = left.y + left.h - 42;
    c.fillStyle = '#53d4ff12'; c.fillRect(left.x, top, left.w / 2, bottom - top); c.fillStyle = '#ffba6812'; c.fillRect(phaseX, top, left.w / 2, bottom - top);
    line(c, phaseX, top, phaseX, bottom, C.line, 1, [4, 5]);
    const particleCount = 36, elapsed = u * T;
    for (let i = 0; i < particleCount; i++) {
      const r = rng(749213 + i * 7919), y0 = r(), jitter = r();
      let state = i % 2, previous = state, last = 0, lastSwitch = -1000, event = -Math.log(Math.max(r(), 1e-9)) / Math.max(p.rate, 1e-8);
      while (event < elapsed && p.rate > 0) { previous = state; state = 1 - state; last = event; lastSwitch = event; event += -Math.log(Math.max(r(), 1e-9)) / p.rate; }
      const frac = clamp((elapsed - lastSwitch) / .018, 0, 1), side = lastSwitch < 0 ? state : mix(previous, state, ease(frac)), px = left.x + left.w * (.18 + side * .64) + Math.sin(t * (state ? 1.8 : .7) + i) * left.w * .07, py = top + (.05 + y0 * .89) * (bottom - top) + Math.cos(t * .6 + jitter * TAU) * 5;
      if (frac < 1) halo(c, px, py, 14, C.white, .2 * (1 - frac)); molecule(c, px, py, state ? 3.2 : 4.1, state ? C.orange : C.blue, i + t);
    }
    text(c, tr(l, 'A · lento', 'A · slow'), left.x + left.w * .24, bottom + 23, 14, C.blue, 'center'); text(c, tr(l, 'B · rápido', 'B · fast'), left.x + left.w * .76, bottom + 23, 14, C.orange, 'center');
    const right = panel(c, panels[1], tr(l, 'El intercambio también cambia la atenuación', 'Exchange also changes attenuation'), tr(l, 'Modelo Kärger simétrico · pulsos estrechos', 'Symmetric Kärger model · narrow pulses'), l), a = axes(c, right, { xmax: 4, ymax: 1.05, xlabel: 'b / 10⁹ s m⁻²', ylabel: 'S / S₀' });
    plotFunction(c, a, b => .5 * Math.exp(-b * p.Dslow) + .5 * Math.exp(-b * p.Dfast), 4, C.muted, 1, [4, 4]);
    plotFunction(c, a, b => Math.exp(-b * (p.Dslow + p.Dfast) / 2), 4, C.purple, 1, [2, 4]);
    plotFunction(c, a, b => exchangeSignal(b, T, p.rate, p.Dslow, p.Dfast), 4, C.green, u);
    text(c, 'kΔ = ' + fmt(p.rate * T), a.x + 10, a.y + 18, 13, C.white, 'left', 600); text(c, tr(l, 'Sin intercambio', 'No exchange'), a.x + 10, a.y + 41, 11, C.muted); text(c, tr(l, 'Límite rápido', 'Fast-exchange limit'), a.x + 10, a.y + 59, 11, C.purple); text(c, tr(l, 'Tasa seleccionada', 'Selected rate'), a.x + 10, a.y + 77, 11, C.green);
    footer(c, w, h, 'dM/dt = [ K − q²(t)·diag(D₁,D₂) ]M', tr(l, 'En intercambio lento aparece una suma de atenuaciones. En el límite rápido emerge un D promedio. No interpretar cada pico ILT como una especie si hay intercambio durante la codificación.', 'Slow exchange gives a sum of attenuations. Fast exchange approaches an averaged D. Do not interpret every ILT peak as a species when exchange occurs during encoding.'), l);
  }

  function anisotropy(c, t, p, l, w, h) {
    frame(c, w, h, l, tr(l, 'La dirección del gradiente también es una pregunta física', 'Gradient direction is also a physical question'));
    const panels = layout(w, h, 2, .55), left = panel(c, panels[0], tr(l, 'Una distribución de desplazamientos anisótropa', 'An anisotropic displacement distribution'), tr(l, 'Proyección x–z · medios orientados', 'x–z projection · oriented media'), l), u = clamp(t / 18, 0, 1), theta = p.angle * Math.PI / 180, T = p.Delta * .001, cx = left.x + left.w / 2, cy = left.y + left.h * .47;
    const scale = Math.min(left.w * .28, left.h * .29) / 22, sx = Math.sqrt(2 * p.Dparallel * 1e-9 * T) * 1e6 * scale, sz = Math.sqrt(2 * p.Dperp * 1e-9 * T) * 1e6 * scale;
    c.save(); c.fillStyle = '#edf8fd08'; c.strokeStyle = '#416376'; c.setLineDash([4, 5]); c.beginPath(); c.ellipse(cx, cy, Math.max(2, sx * 1.7), Math.max(2, sz * 1.7), 0, 0, TAU); c.fill(); c.stroke(); c.restore();
    clipped(c, left, () => walkers(625482, 90).forEach((d, i) => molecule(c, cx + sample(d.x, u) * sx, cy + sample(d.z, u) * sz, 2.3, '#cee7ee', d.phase + t)));
    arrow(c, cx, cy, sx * 1.6, 0, C.orange, 2.5, 7); arrow(c, cx, cy, 0, -sz * 1.8, C.blue, 2.5, 7);
    const gr = Math.min(left.w * .36, left.h * .36); arrow(c, cx, cy, Math.cos(theta) * gr, -Math.sin(theta) * gr, C.green, 3.2, 9);
    text(c, 'ĝ', cx + Math.cos(theta) * (gr + 15), cy - Math.sin(theta) * (gr + 15), 18, C.green, 'center', 600);
    text(c, 'D∥ = ' + fmt(p.Dparallel), left.x + 12, left.y + left.h - 35, 13, C.orange); text(c, 'D⊥ = ' + fmt(p.Dperp), left.x + 12, left.y + left.h - 13, 13, C.blue);
    const right = panel(c, panels[1], tr(l, 'D aparente depende de la orientación', 'Apparent D depends on orientation'), tr(l, 'Una dirección no mide todo el tensor', 'One direction does not measure the full tensor'), l), a = axes(c, right, { xmax: 180, ymax: Math.max(p.Dparallel, p.Dperp) * 1.16, xlabel: tr(l, 'Ángulo / grados', 'Angle / degrees'), ylabel: 'Dapp / 10⁻⁹ m² s⁻¹' });
    const dapp = deg => p.Dparallel * Math.cos(deg * Math.PI / 180) ** 2 + p.Dperp * Math.sin(deg * Math.PI / 180) ** 2;
    plotFunction(c, a, dapp, 180, C.green); line(c, a.X(p.angle), a.y, a.X(p.angle), a.y + a.h, '#83edd170', 1, [4, 4]); dot(c, a.X(p.angle), a.Y(dapp(p.angle)), 5.5, C.green, true);
    text(c, 'Dapp = ' + fmt(dapp(p.angle)), a.x + 10, a.y + 18, 15, C.white, 'left', 600);
    footer(c, w, h, 'Dapp = nᵀDn = D∥cos²θ + D⊥sin²θ', tr(l, 'En una disolución isotrópica, la difusión no cambia con la dirección. En medios orientados o confinados hay que considerar el tensor y, para restricciones, el tiempo observado.', 'In an isotropic solution, diffusion is direction-independent. In oriented or confined media, consider the tensor and, for restrictions, observation time.'), l);
  }

  function advancedPlaceholder(c, id, t, p, l, w, h) {
    const names = { ultrafast: ['Ultrafast: codificar espacialmente', 'Ultrafast: spatial encoding'], dt2: ['D–T₂: dos contrastes complementarios', 'D–T₂: two complementary contrasts'], spen: ['SPEN–DOSY: espacio, fase y difusión', 'SPEN–DOSY: space, phase and diffusion'], 'prototype-1d': ['Prototipo 1D: del concepto a la validación', '1D prototype: from concept to validation'] }, name = names[id];
    frame(c, w, h, l, tr(l, name[0], name[1])); const pos = layout(w, h, 1)[0], inner = panel(c, pos, tr(l, 'Codificación y lectura', 'Encoding and readout'), tr(l, 'Animación conceptual', 'Conceptual animation'), l), cx = inner.x + inner.w / 2, cy = inner.y + inner.h / 2, hh = inner.h * .65, ww = Math.min(130, inner.w * .25);
    rect(c, cx - ww / 2, cy - hh / 2, ww, hh, 20, '#15374c', C.line);
    for (let i = 0; i < 24; i++) { const y = cy - hh / 2 + i / 23 * hh, phase = i * .45 + t * .8; line(c, cx - ww * .36, y, cx + ww * .36, y, `hsl(${195 + i * 2},70%,60%)`, 2); arrow(c, cx, y, Math.cos(phase) * ww * .28, Math.sin(phase) * 5, C.white, 1, 4); }
    footer(c, w, h, tr(l, 'Espacio → codificación → señal → reconstrucción', 'Space → encoding → signal → reconstruction'), tr(l, 'Esquema pedagógico. El programa experimental concreto define el núcleo, los factores de relajación y el procesamiento.', 'Educational schematic. The actual experimental program determines the kernel, relaxation factors and processing.'), l);
  }

  const handlers = { brownian, 'spin-echo': spinEcho, 'gradients-b': gradientsB, 'attenuation-mixture': attenuationMixture, 'pulse-90': pulse90, 'acquisition-window': acquisitionWindow, convection, 'overlap-joint': overlapJoint, ilt, restricted, exchange, anisotropy };
  function render(ctx, id, t, p, lang, w, h) {
    if (!ctx || w <= 0 || h <= 0) return;
    p = Object.assign({}, defaults[id] || {}, p || {}); lang = lang === 'es' ? 'es' : 'en';
    ctx.save(); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    if (handlers[id]) handlers[id](ctx, clamp(Number(t) || 0, 0, 18), p, lang, w, h); else advancedPlaceholder(ctx, id in defaults ? id : 'ultrafast', clamp(Number(t) || 0, 0, 18), p, lang, w, h);
    ctx.restore();
  }
  window.MotionScenes = { render, defaults, controls, constants: { gamma1H: GAMMA }, physics: { bPGSE: B, exchangeSignal }, helpers: { C, tr, text, wrap, rect, line, arrow, dot, curve, frame, panel, footer, layout, axes, plotFunction, clipped, rng, gaussian, walkers, sample, clamp, ease, fmt, legend } };
})();
