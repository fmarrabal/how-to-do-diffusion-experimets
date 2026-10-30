/* Quantitative synthetic demonstrations. All plotted signals and estimates
 * are produced by diffusion-models.js. Canvas animation time is not t_lab,
 * the diffusion delay Delta, or the physical EPSI readout clock. */
(function () {
  'use strict';
  const ctl = (id, es, en, min, max, step, value, unit = '') => ({ id, label: { es, en }, min, max, step, value, unit });
  const diffusion = [ctl('D1', 'D de A', 'D of A', .15, 1, .05, .45, '10⁻⁹ m²/s'), ctl('D2', 'D de B', 'D of B', 1.1, 3, .1, 1.4, '10⁻⁹ m²/s')];
  const gradient = [ctl('g', 'Gradiente nominal', 'Nominal gradient', 150, 650, 10, 420, 'mT/m'), ctl('delta', 'δ local máxima', 'Maximum local δ', .5, 3, .1, 1.4, 'ms'), ctl('Delta', 'Separación de difusión Δ', 'Diffusion separation Δ', 30, 200, 5, 80, 'ms')];
  const controls = {
    ultrafast: [...gradient, ctl('D', 'D de referencia', 'Reference D', .2, 2, .05, .8, '10⁻⁹ m²/s'), ctl('profile', 'Pendiente de sensibilidad', 'Sensitivity slope', 0, .7, .05, .5, 'rel.'), ctl('T2', 'T₂ del ejemplo', 'Example T₂', 50, 500, 10, 150, 'ms'), ctl('readout', 'Ventana de lectura', 'Readout window', 10, 150, 5, 60, 'ms'), ctl('calibration', 'G real / G nominal', 'Actual G / nominal G', .7, 1.3, .01, 1.1, 'rel.'), ctl('noise', 'Ruido gaussiano fijo', 'Fixed Gaussian noise', 0, 3, .1, 0, '% S₀')],
    spen: [...gradient, ...diffusion, ctl('fraction', 'Fracción de A', 'Fraction of A', 0, 1, .01, .62, 'rel.'), ctl('oddPhase', 'Error de fase impar', 'Odd-polarity phase error', 0, 150, 5, 65, '°'), ctl('profile', 'Pendiente de sensibilidad', 'Sensitivity slope', 0, .7, .05, .35, 'rel.'), ctl('frequency', 'Frecuencia seleccionada', 'Selected frequency', -220, 220, 10, -80, 'Hz'), ctl('noise', 'Ruido gaussiano fijo', 'Fixed Gaussian noise', 0, 3, .1, 0, '% S₀')],
    'time-resolved': [...diffusion, ctl('rate', 'Velocidad A → B', 'A → B reaction rate', 0, .08, .005, .025, 's⁻¹'), ctl('tLab', 'Inicio: tiempo de laboratorio', 'Start: laboratory time', 0, 120, 5, 20, 's'), ctl('pointTime', 'Duración de cada punto', 'Duration of each point', .2, 4, .2, 2, 's'), ctl('snapshotTime', 'Ventana del snapshot', 'Snapshot window', .05, 4, .05, .5, 's'), ctl('frameStep', 'Cadencia solicitada entre frames', 'Requested frame cadence', 1, 20, 1, 5, 's'), ctl('order', 'Orden: ↑ / ↓ / permutado', 'Order: ↑ / ↓ / permuted', 0, 2, 1, 0, '0 / 1 / 2'), ctl('Delta', 'Separación de difusión Δ', 'Diffusion separation Δ', 30, 200, 5, 80, 'ms'), ctl('readout', 'Duración de lectura', 'Readout duration', 10, 120, 5, 40, 'ms'), ctl('noise', 'Ruido gaussiano fijo', 'Fixed Gaussian noise', 0, 3, .1, 0, '% S₀')]
  };
  const defaults = Object.fromEntries(Object.entries(controls).map(([id, list]) => [id, Object.fromEntries(list.map(v => [v.id, v.value]))]));
  const preset = (es, en, params) => ({ label: { es, en }, params });
  const presets = {
    ultrafast: [preset('Ideal: recuperar D', 'Ideal: recover D', { profile: 0, calibration: 1, noise: 0 }), preset('Sesgo de perfil y calibración', 'Profile and calibration bias', { profile: .6, calibration: 1.15, noise: 0 }), preset('Referencia ruidosa', 'Noisy reference', { profile: .6, T2: 70, readout: 120, noise: 1.5 })],
    spen: [preset('Control: A puro, sin ruido', 'Control: pure A, no noise', { fraction: 1, oddPhase: 65, noise: 0, frequency: -80 }), preset('Control: B puro, sin ruido', 'Control: pure B, no noise', { fraction: 0, oddPhase: 65, noise: 0, frequency: 120 }), preset('Reordenar ambas polaridades', 'Reorder both polarities', { fraction: .62, oddPhase: 0, noise: 0, frequency: -80 }), preset('Error de fase de 90°', '90° phase error', { fraction: .62, oddPhase: 90, noise: 0, frequency: -80 }), preset('Seleccionar la señal B', 'Select signal B', { fraction: .62, oddPhase: 65, noise: .5, frequency: 120 })],
    'time-resolved': [preset('Control: sin reacción', 'Control: no reaction', { rate: 0, tLab: 0, pointTime: 2, snapshotTime: .5, order: 0 }), preset('Rampa creciente: falso cambio de D', 'Ascending ramp: false D change', { rate: .04, tLab: 0, pointTime: 3, snapshotTime: .5, order: 0 }), preset('Misma reacción, rampa decreciente', 'Same reaction, descending ramp', { rate: .04, tLab: 0, pointTime: 3, snapshotTime: .5, order: 1 }), preset('Permutar no congela la reacción', 'Permutation does not freeze chemistry', { rate: .04, tLab: 0, pointTime: 3, snapshotTime: .5, order: 2 })]
  };
  const L = (lang, es, en) => lang === 'es' ? es : en;
  const metric = (es, en, value, unit, digits = 3, kind = 'estimate') => ({ label: { es, en }, value: Number.isFinite(value) ? value : null, unit, digits, kind });
  function data(id, p) { const M = window.DiffusionModels; return id === 'ultrafast' ? M.ultrafast(p) : id === 'spen' ? M.spen(p) : id === 'time-resolved' ? M.timeResolved(p) : null; }
  function diagnostics(id, p) {
    const m = data(id, p); if (!m) return null; const d = m.diagnostics, metrics = [], notes = { es: [], en: [] }, add = (es, en) => { notes.es.push(es); notes.en.push(en); };
    if (id === 'ultrafast') {
      metrics.push(metric('D introducido', 'Input D', d.trueD * 1e9, '10⁻⁹ m²/s', 3, 'reference'), metric('D sin normalizar', 'D without normalization', d.rawD === null ? null : d.rawD * 1e9, '10⁻⁹ m²/s'), metric('D: referencia + b nominal', 'D: reference + nominal b', d.nominalD === null ? null : d.nominalD * 1e9, '10⁻⁹ m²/s'), metric('D: referencia + b calibrado', 'D: reference + calibrated b', d.calibratedD === null ? null : d.calibratedD * 1e9, '10⁻⁹ m²/s'), metric('Sesgo después de corregir', 'Bias after correction', d.calibratedBiasPercent, '%', 2), metric('b máximo real', 'Actual maximum b', d.bMaximum * 1e-9, '10⁹ s/m²'));
      add('P(z) y la relajación se cancelan sólo porque la referencia sintética usa el mismo perfil y TE común. La calibración aplicada es conocida en este ejemplo, no medida.', 'P(z) and relaxation cancel only because the synthetic reference uses the same profile and common TE. The applied calibration is known in this example, not measured.');
      add('δ(z) rectangular ideal permite calcular b(z); un chirp real necesita integrar q(z,t)² para su secuencia. No se ha calculado una ILT.', 'Ideal rectangular δ(z) gives a computable b(z); a real chirp requires integrating q(z,t)² for its sequence. No ILT has been computed.');
      if (m.calibratedFit.nUsed < m.rows.length) add(`Ajuste con ${m.calibratedFit.nUsed}/${m.rows.length} puntos positivos por encima del umbral del 1,5%; no es una estimación del ruido.`, `Fit uses ${m.calibratedFit.nUsed}/${m.rows.length} positive points above the 1.5% threshold; this is not a noise estimate.`);
    } else if (id === 'spen') {
      metrics.push(metric('Frecuencia reconstruida', 'Reconstructed frequency', d.selectedFrequency, 'Hz', 0), metric('D del componente cercano', 'Nearest-component D', d.trueD === null ? null : d.trueD * 1e9, '10⁻⁹ m²/s', 3, 'reference'), metric('D sin reordenar/fase', 'D without reorder/phase correction', d.uncorrectedD === null ? null : d.uncorrectedD * 1e9, '10⁻⁹ m²/s'), metric('D después de reconstruir', 'D after reconstruction', d.correctedD === null ? null : d.correctedD * 1e9, '10⁻⁹ m²/s'), metric('Sesgo del ajuste corregido', 'Corrected-fit bias', d.correctedBiasPercent, '%', 2), metric('Resolución digital', 'Digital resolution', d.spectralResolutionHz, 'Hz', 0));
      add('La matriz S(ν,b) procede de señales complejas sintéticas, reordenado de polaridad, corrección de fase conocida, IDFT espacial y DFT espectral. Se ajusta la atenuación seleccionada; no se dibuja un mapa DOSY objetivo.', 'S(ν,b) comes from synthetic complex signals, polarity reordering, known phase correction, spatial IDFT and spectral DFT. The selected attenuation is fitted; no target DOSY map is drawn.');
      add('Aproximación de centro de eco, 24 posiciones y 64 tiempos. Ambas polaridades combinadas: intervalo 1,5625 ms, banda 640 Hz. Sin chirp real, evolución intraeco ni corrección de shear.', 'Echo-center approximation, 24 positions and 64 times. Both polarities combined: 1.5625 ms interval, 640 Hz bandwidth. No real chirp, within-echo evolution or shear correction.');
      add('Los dos componentes aportan colas espectrales; un ajuste monoexponencial lejos de una señal aislada puede dar un D aparente.', 'Both components contribute spectral tails; a monoexponential fit away from an isolated resonance may give an apparent D.');
      if (d.offResonance) add('Frecuencia lejos de las resonancias −80 y +120 Hz: la comparación con un componente puro no valida el ajuste.', 'Frequency is away from the −80 and +120 Hz resonances: comparison with one pure component does not validate the fit.');
      if (!d.selectedComponentPresent) add('El componente cercano no está presente. La señal seleccionada es fuga espectral: no hay un D de referencia válido en esa frecuencia.', 'The nearest component is absent. The selected signal is spectral leakage: there is no valid reference D at that frequency.');
    } else {
      metrics.push(metric('D real de A (constante)', 'True A D (constant)', d.trueD1 * 1e9, '10⁻⁹ m²/s', 3, 'reference'), metric('D de A: serie secuencial', 'A D: sequential series', d.sequentialD1 === null ? null : d.sequentialD1 * 1e9, '10⁻⁹ m²/s'), metric('D de A: snapshot', 'A D: snapshot', d.snapshotD1 === null ? null : d.snapshotD1 * 1e9, '10⁻⁹ m²/s'), metric('D de B: serie secuencial', 'B D: sequential series', d.sequentialD2 === null ? null : d.sequentialD2 * 1e9, '10⁻⁹ m²/s'), metric('D de B: snapshot', 'B D: snapshot', d.snapshotD2 === null ? null : d.snapshotD2 * 1e9, '10⁻⁹ m²/s'), metric('Sesgo de A: secuencial', 'A bias: sequential', d.sequentialBias1Percent, '%', 2), metric('Ventana de la serie', 'Series window', d.slowWindowSec, 's', 1), metric('Ventana del snapshot', 'Snapshot window', d.snapshotWindowSec, 's', 2), metric('Cadencia solicitada de frames', 'Requested frame cadence', d.cadenceSec, 's', 1));
      add('A → B cambia fracciones, con D_A y D_B constantes. Se integran analíticamente las fracciones en cada ventana de adquisición. El ajuste aparente cambia con el orden de b.', 'A → B changes fractions, with constant D_A and D_B. Fractions are analytically integrated over each acquisition window. The apparent fit changes with b ordering.');
      add('t_lab es el reloj de la reacción; Δ es la separación de difusión; t_read es la duración de lectura. La animación de 18 s no representa ninguno de esos relojes.', 't_lab is the reaction clock; Δ is the diffusion separation; t_read is the readout duration. The 18 s animation is none of these clocks.');
      add('Snapshot ideal con puntos simultáneos y señales A/B resueltas. No se modela intercambio durante Δ, T₁/T₂, J ni un hardware ultrafast real.', 'Ideal snapshot with simultaneous points and resolved A/B signals. Exchange during Δ, T₁/T₂, J and real ultrafast hardware are not modelled.');
      if (d.overlappingSlowFrames) add('Cadencia menor que la ventana: los frames secuenciales se solapan y no son independientes.', 'Cadence is shorter than the window: sequential frames overlap and are not independent.');
      add('Los frames usan ventanas de una única serie continua, con el mismo ruido en los puntos compartidos. El inicio se ajusta al punto adquirido más cercano; una ventana puede cruzar ciclos de la rampa.', 'Frames use windows from one continuous series, with identical noise on shared points. The start is aligned to the nearest acquired point; a window can cross ramp cycles.');
      if (m.params.frameStep < m.params.pointTime || Math.abs(m.params.frameStep / m.params.pointTime - Math.round(m.params.frameStep / m.params.pointTime)) > 1e-9) {
        const actualCadences = [...new Set(m.history.slice(1).map((frame, i) => Number((frame.start - m.history[i].start).toFixed(6))))];
        add(`Los inicios están discretizados por puntos: la cadencia real entre estas ventanas es ${actualCadences.join(' / ')} s, aunque se solicitan ${m.params.frameStep} s. Si hay más de un frame solicitado entre puntos, las ventanas pueden repetirse. La cadencia no es la resolución temporal.`, `Starts are discretized by acquired points: actual cadence between these windows is ${actualCadences.join(' / ')} s, although ${m.params.frameStep} s was requested. If multiple frames are requested between acquired points, windows can repeat. Cadence is not temporal resolution.`);
      }
      metrics.push(metric('Inicio efectivo del frame', 'Effective frame start', d.actualFrameStartSec, 's', 2, 'reference'));
      if (d.inconsistentTiming) add('Ventana incompatible con Δ + t_read. La curva es sólo matemática; esa temporización no constituye un experimento ejecutable.', 'Window is shorter than Δ + t_read. The curve is mathematical only; this timing is not an executable experiment.');
    }
    return { metrics, notes, numeric: d, paramsSI: m.paramsSI };
  }
  function cards(w, h) {
    const margin = w < 600 ? 12 : 18, gap = w < 600 ? 14 : 16, top = 47, bottom = 54;
    if (w < 720) { const ph = (h - top - bottom - 2 * gap) / 3; return [0, 1, 2].map(i => ({ x: margin, y: top + i * (ph + gap), w: w - 2 * margin, h: ph })); }
    const pw = (w - 2 * margin - 2 * gap) / 3; return [0, 1, 2].map(i => ({ x: margin + i * (pw + gap), y: top, w: pw, h: h - top - bottom }));
  }
  function title(c, p, heading, H) { H.rect(c, p.x, p.y, p.w, p.h, 15, '#0b2334', '#31576b'); H.wrap(c, heading, p.x + 14, p.y + 15, p.w - 28, p.w < 420 ? 13 : 16, H.C.white, 2); return { x: p.x + 6, y: p.y + 51, w: p.w - 12, h: p.h - 62 }; }
  function plot(c, p, xLabel, yLabel, H, opts = {}) { return H.axes(c, p, { xlabel: xLabel, ylabel: yLabel, left: 45, bottom: 36, ...opts }); }
  function points(c, a, xs, ys, color, H, reveal = 1, connected = true, dashed = false) {
    const pts = xs.map((v, i) => Number.isFinite(ys[i]) ? [a.X(v), a.Y(ys[i])] : null).filter(Boolean);
    if (connected) H.curve(c, pts, color, 2.2, dashed ? [5, 4] : undefined);
    pts.forEach((v, i) => { c.save(); c.globalAlpha = i / Math.max(1, pts.length - 1) <= reveal ? 1 : .22; H.dot(c, v[0], v[1], 2.5, color); c.restore(); });
  }
  function label(c, p, message, color, H, yOffset = 0) { H.wrap(c, message, p.x + 8, p.y + yOffset, p.w - 16, 11, color, 2); }
  function legend(c, p, items, H) { items.forEach((item, i) => { const x = p.x + 12, y = p.y + i * 17; H.line(c, x, y, x + 17, y, item[1], 2, item[2] ? [4, 3] : undefined); H.text(c, item[0], x + 23, y, 10.5, item[1]); }); }
  function fmtD(v) { return v === null || !Number.isFinite(v) ? '—' : (v * 1e9).toFixed(3); }
  function status(c, w, h, l, text, H) { H.wrap(c, text, w < 600 ? 16 : 22, h - 40, w - 36, w < 600 ? 10.5 : 12, H.C.muted, 2); }
  function ultrafast(c, t, m, l, w, h, H) {
    const C = H.C, ps = cards(w, h), a = title(c, ps[0], L(l, '01 / Posición → ponderación b(z)', '01 / Position → weighting b(z)'), H), b = title(c, ps[1], L(l, '02 / Medir señal y referencia', '02 / Measure signal and reference'), H), d = title(c, ps[2], L(l, '03 / Normalizar y estimar D', '03 / Normalize and estimate D'), H), u = H.clamp(t / 18, 0, 1);
    const z = m.rows.map(v => v.z_m * 1e3), bmax = m.diagnostics.bMaximum * 1e-9;
    const compact = a.h < 220, tubeH = compact ? 22 : Math.min(60, a.h * .2), tx = a.x + 23, ty = a.y + 9, tw = a.w - 46;
    H.rect(c, tx, ty, tw, tubeH, tubeH / 2, '#203b50', '#577791');
    for (let i = 0; i < m.rows.length; i++) { const f = i / (m.rows.length - 1), value = m.rows[i].b_true_s_per_m2 / m.diagnostics.bMaximum; c.fillStyle = `hsla(${230 - value * 175},80%,${45 + value * 15}%,.8)`; c.fillRect(tx + 12 + f * (tw - 24), ty + 9, Math.max(2, (tw - 24) / m.rows.length), Math.max(4, tubeH - 18)); }
    H.line(c, tx + 12 + (tw - 24) * u, ty - 5, tx + 12 + (tw - 24) * u, ty + tubeH + 5, C.green, 2);
    const ap = { ...a, y: a.y + tubeH + (compact ? 17 : 34), h: Math.max(60, a.h - tubeH - (compact ? 17 : 70)) }, ax = plot(c, ap, 'z / mm', 'b / 10⁹ s m⁻²', H, { xmin: -5, xmax: 5, ymax: bmax * 1.08 });
    points(c, ax, z, m.rows.map(v => v.b_true_s_per_m2 * 1e-9), C.purple, H, u, true); points(c, ax, z, m.rows.map(v => v.b_nominal_s_per_m2 * 1e-9), C.muted, H, u, true, true);
    if (!compact) label(c, { ...a, y: a.y + a.h - 25 }, L(l, 'Color = b real; línea discontinua = b nominal', 'Color = actual b; dashed line = nominal b'), C.muted, H);
    const bp = { ...b, h: b.h - 60 }, bx = plot(c, bp, 'z / mm', L(l, 'Señal / S₀', 'Signal / S₀'), H, { xmin: -5, xmax: 5, ymax: 1.05 });
    points(c, bx, z, m.rows.map(v => v.reference), C.green, H, H.clamp(t / 8, 0, 1)); points(c, bx, z, m.rows.map(v => v.signal), C.orange, H, H.clamp(t / 8, 0, 1));
    legend(c, { ...b, y: b.y + b.h - 38 }, [[L(l, 'Referencia: P(z) · exp(−TE/T₂)', 'Reference: P(z) · exp(−TE/T₂)'), C.green], [L(l, 'Señal: referencia · exp(−bD)', 'Signal: reference · exp(−bD)'), C.orange]], H);
    const dp = { ...d, h: d.h - 86 }, dx = plot(c, dp, 'b real / 10⁹ s m⁻²', 'S / Sref', H, { xmax: bmax * 1.05, ymax: 1.08 });
    const bTrue = m.rows.map(v => v.b_true_s_per_m2 * 1e-9); points(c, dx, bTrue, m.rows.map(v => v.normalized), C.blue, H, H.clamp((t - 6) / 8, 0, 1));
    H.plotFunction(c, dx, bv => Math.exp(-bv * m.params.D), bmax, C.green, 1, [6, 5]);
    legend(c, { ...d, y: d.y + d.h - 64 }, [[L(l, 'Puntos: señal / referencia', 'Points: signal / reference'), C.blue], [L(l, 'D introducido (control)', 'Input D (control)'), C.green, true]], H);
    H.text(c, `D = ${fmtD(m.calibratedFit.D)} × 10⁻⁹ m²/s`, d.x + 12, d.y + d.h - 18, 12, C.white, 'left', 650);
    status(c, w, h, l, L(l, 'Modelo espacial PGSE rectangular ideal. P(z), TE y b deben coincidir con la referencia y calibración; no representa un chirp real.', 'Ideal rectangular PGSE spatial model. P(z), TE and b must match the reference and calibration; this is not a real chirp.'), H);
  }
  function spen(c, t, m, l, w, h, H) {
    const C = H.C, ps = cards(w, h), a = title(c, ps[0], L(l, '01 / Adquisición compleja EPSI', '01 / Complex EPSI acquisition'), H), b = title(c, ps[1], L(l, '02 / IDFT(z) + DFT(ν) → S(ν,b)', '02 / IDFT(z) + DFT(ν) → S(ν,b)'), H), d = title(c, ps[2], L(l, '03 / Atenuación a ν seleccionada', '03 / Attenuation at selected ν'), H);
    const nr = 8, left = a.x + 24, right = a.x + a.w - 20, height = Math.max(60, a.h - 88), reveal = H.clamp(t / 6, 0, 1);
    for (let n = 0; n < nr; n++) { const yy = a.y + 17 + n * height / (nr - 1), row = m.epsiRows.slice(n * 24, (n + 1) * 24), polarity = n % 2 ? -1 : 1, color = polarity > 0 ? C.blue : C.orange;
      H.line(c, left, yy, right, yy, '#284757'); const maximum = Math.max(1, ...row.map(v => Math.hypot(v.re, v.im)));
      const pts = row.map((v, i) => [left + (right - left) * i / 23, yy - v.re / maximum * Math.min(13, height / 20)]); c.save(); c.globalAlpha = n / nr <= reveal ? 1 : .25; H.curve(c, pts, color, 1.8); c.restore();
      H.arrow(c, polarity > 0 ? left : right, yy + 7, polarity * (right - left), 0, color, 1, 4); H.text(c, n % 2 ? '−G' : '+G', a.x + 1, yy, 10, color);
    }
    label(c, { ...a, y: a.y + a.h - 57 }, L(l, `Fase impar = ${m.params.oddPhase.toFixed(0)}° · 24 k × 64 ecos`, `Odd phase = ${m.params.oddPhase.toFixed(0)}° · 24 k × 64 echoes`), C.muted, H);
    label(c, { ...a, y: a.y + a.h - 27 }, L(l, '−G: invertir índice + deshacer fase conocida', '−G: reverse index + remove known phase'), C.green, H);
    const bp = { ...b, h: b.h - 30 }, bx = plot(c, bp, 'ν / Hz', 'b / 10⁹ s m⁻²', H, { xmin: -320, xmax: 310, ymax: Math.max(...m.b) * 1e-9, xFormat: v => v.toFixed(0), yFormat: v => v.toFixed(1) });
    const maximum = Math.max(...m.corrected.flatMap(row => row.re.map((v, k) => Math.hypot(v, row.im[k]))));
    for (let zi = 0; zi < m.z.length; zi++) for (let fi = 0; fi < m.frequencies.length; fi++) { const mag = Math.hypot(m.corrected[zi].re[fi], m.corrected[zi].im[fi]) / maximum, value = Math.sqrt(Math.max(0, mag)), b0 = m.b[zi] * 1e-9, b1 = (m.b[Math.min(zi + 1, m.b.length - 1)] || m.b[zi]) * 1e-9, ch = Math.max(2, Math.abs(bx.Y(b1) - bx.Y(b0))); c.fillStyle = `rgb(${Math.round(12 + 120 * value)},${Math.round(40 + 195 * value)},${Math.round(70 + 150 * value)})`; c.globalAlpha = zi / m.z.length < H.clamp((t - 4) / 7, 0, 1) ? 1 : .3; c.fillRect(bx.X(m.frequencies[fi]), bx.Y(b0) - ch, Math.max(1, bx.w / 64 + .5), ch + .5); }
    c.globalAlpha = 1; H.line(c, bx.X(m.diagnostics.selectedFrequency), bx.y, bx.X(m.diagnostics.selectedFrequency), bx.y + bx.h, C.orange, 1.4, [4, 4]);
    label(c, { ...b, y: b.y + b.h - 20 }, L(l, '|S complejo| calculado · sin mapa D objetivo', 'Computed |complex S| · no target D map'), C.muted, H);
    const dp = { ...d, h: d.h - 92 }, dx = plot(c, dp, 'b / 10⁹ s m⁻²', 'Sν / Sν,ref', H, { xmax: Math.max(...m.b) * 1e-9 * 1.04, ymax: Math.max(1.08, ...m.selected.map(v => v.uncorrected ?? 0).filter(v => v < 3)) });
    const bValues = m.b.map(v => v * 1e-9); points(c, dx, bValues, m.selected.map(v => v.uncorrected), C.orange, H, 1); points(c, dx, bValues, m.selected.map(v => v.corrected), C.blue, H, H.clamp((t - 10) / 6, 0, 1));
    if (m.correctedFit.D !== null) H.plotFunction(c, dx, bv => m.correctedFit.amplitude * Math.exp(-bv * m.correctedFit.D * 1e9), Math.max(...bValues), C.green, 1, [5, 4]);
    legend(c, { ...d, y: d.y + d.h - 70 }, [[L(l, 'Sin corregir polaridad/fase', 'Without polarity/phase correction'), C.orange], [L(l, 'Reconstrucción corregida', 'Corrected reconstruction'), C.blue], [L(l, 'Ajuste monoexponencial calculado', 'Computed monoexponential fit'), C.green, true]], H);
    H.text(c, `D = ${fmtD(m.correctedFit.D)} × 10⁻⁹ m²/s`, d.x + 12, d.y + d.h - 12, 12, C.white, 'left', 650);
    status(c, w, h, l, L(l, 'EPSI ideal de centros de eco. Corrección de fase conocida; normalización por referencia. La banda elegida puede contener colas de ambas especies.', 'Ideal echo-center EPSI. Known phase correction; reference normalization. The selected band can contain tails from both species.'), H);
  }
  function timeResolved(c, t, m, l, w, h, H) {
    const C = H.C, ps = cards(w, h), a = title(c, ps[0], L(l, '01 / A → B: D fijo, fracción variable', '01 / A → B: fixed D, changing fraction'), H), b = title(c, ps[1], L(l, '02 / Cada b se mide en otro t_lab', '02 / Each b is measured at a new t_lab'), H), d = title(c, ps[2], L(l, '03 / Un cambio químico parece cambiar D', '03 / Chemistry can look like a D change'), H), start = m.current.start, total = Math.max(60, start + m.diagnostics.slowWindowSec + 12, m.history[m.history.length - 1].start + m.diagnostics.slowWindowSec), progress = H.clamp(t / 18, 0, 1);
    const ap = { ...a, h: a.h - 66 }, ax = plot(c, ap, L(l, 't_lab / s · marcas = frames', 't_lab / s · ticks = frames'), L(l, 'Fracción', 'Fraction'), H, { xmax: total, ymax: 1 });
    H.plotFunction(c, ax, ti => Math.exp(-m.params.rate * ti), total, C.blue); H.plotFunction(c, ax, ti => 1 - Math.exp(-m.params.rate * ti), total, C.orange);
    c.save(); c.globalAlpha = .15; c.fillStyle = C.orange; c.fillRect(ax.X(start), ax.y, ax.X(start + m.diagnostics.slowWindowSec) - ax.X(start), ax.h); c.globalAlpha = .4; c.fillStyle = C.green; c.fillRect(ax.X(start), ax.y, Math.max(3, ax.X(start + m.params.snapshotTime) - ax.X(start)), ax.h); c.restore();
    m.history.forEach(frame => { H.line(c, ax.X(frame.start), ax.y - 7, ax.X(frame.start), ax.y + 5, C.purple, 1.5); });
    const cursor = start + progress * m.diagnostics.slowWindowSec; H.line(c, ax.X(cursor), ax.y, ax.X(cursor), ax.y + ax.h, C.white, 1.5, [4, 4]);
    legend(c, { ...a, y: a.y + a.h - 40 }, [[`A · D = ${m.params.D1.toFixed(2)} ×10⁻⁹`, C.blue], [`B · D = ${m.params.D2.toFixed(2)} ×10⁻⁹`, C.orange]], H);
    const bp = { ...b, h: b.h - 65 }, bx = plot(c, bp, 't_lab / s', 'b / 10⁹ s m⁻²', H, { xmin: start, xmax: start + Math.max(m.diagnostics.slowWindowSec, m.params.snapshotTime) * 1.04, ymax: m.diagnostics.bMaximum * 1e-9 * 1.05, xFormat: v => v.toFixed(0) });
    const acquired = [...m.rows].sort((a, b) => a.acquisition_index - b.acquisition_index); points(c, bx, acquired.map(v => v.sequential_mid_t_lab_s), acquired.map(v => v.b_s_per_m2 * 1e-9), C.orange, H, H.clamp(t / 10, 0, 1));
    points(c, bx, m.rows.map(v => v.snapshot_start_t_lab_s + m.params.snapshotTime / 2), m.rows.map(v => v.b_s_per_m2 * 1e-9), C.green, H, 1, false);
    legend(c, { ...b, y: b.y + b.h - 40 }, [[L(l, `Serie: ventana ${m.diagnostics.slowWindowSec.toFixed(1)} s`, `Series: ${m.diagnostics.slowWindowSec.toFixed(1)} s window`), C.orange], [`Snapshot: ${m.params.snapshotTime.toFixed(2)} s`, C.green]], H);
    const dp = { ...d, h: d.h - 87 }, dx = plot(c, dp, 'b / 10⁹ s m⁻²', L(l, 'Señal de A', 'Signal of A'), H, { xmax: m.diagnostics.bMaximum * 1e-9 * 1.03, ymax: Math.max(.08, ...m.rows.map(v => Math.max(v.sequential_A, v.snapshot_A))) * 1.08 });
    const bs = m.rows.map(v => v.b_s_per_m2 * 1e-9); points(c, dx, bs, m.rows.map(v => v.sequential_A), C.orange, H, H.clamp(t / 10, 0, 1)); points(c, dx, bs, m.rows.map(v => v.snapshot_A), C.green, H, H.clamp((t - 5) / 8, 0, 1));
    if (m.current.fitSlowA.D !== null) H.plotFunction(c, dx, bv => m.current.fitSlowA.amplitude * Math.exp(-bv * m.current.fitSlowA.D * 1e9), m.diagnostics.bMaximum * 1e-9, C.orange, 1, [4, 4]);
    legend(c, { ...d, y: d.y + d.h - 66 }, [[L(l, `D serie = ${fmtD(m.current.fitSlowA.D)}`, `Series D = ${fmtD(m.current.fitSlowA.D)}`), C.orange], [`D snapshot = ${fmtD(m.current.fitFastA.D)}`, C.green]], H);
    H.text(c, L(l, `D real fijo = ${m.params.D1.toFixed(3)} ×10⁻⁹`, `Fixed true D = ${m.params.D1.toFixed(3)} ×10⁻⁹`), d.x + 12, d.y + d.h - 13, 12, C.white, 'left', 650);
    status(c, w, h, l, L(l, `t_lab ≠ Δ = ${m.params.Delta} ms ≠ t_read = ${m.params.readout} ms. Ventana = promediado temporal; cadencia = separación solicitada de frames.`, `t_lab ≠ Δ = ${m.params.Delta} ms ≠ t_read = ${m.params.readout} ms. Window = temporal averaging; cadence = requested frame spacing.`), H);
  }
  function render(c, id, t, p, lang, w, h) {
    if (!controls[id]) return false; const H = window.MotionScenes.helpers, m = data(id, p); t = H.clamp(Number.isFinite(t) ? t : 0, 0, 18);
    H.text(c, L(lang, 'SEÑALES SINTÉTICAS → RECONSTRUCCIÓN → AJUSTE', 'SYNTHETIC SIGNALS → RECONSTRUCTION → FIT'), w < 600 ? 14 : 22, 21, w < 600 ? 10.5 : 13, H.C.green, 'left', 650);
    if (id === 'ultrafast') ultrafast(c, t, m, lang, w, h, H); else if (id === 'spen') spen(c, t, m, lang, w, h, H); else timeResolved(c, t, m, lang, w, h, H);
    return true;
  }
  window.QuantitativeScenes = { defaults, controls, presets, render, diagnostics };
})();
