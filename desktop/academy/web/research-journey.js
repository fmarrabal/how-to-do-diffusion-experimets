/* Academy 1.3: one reproducible teaching sample from calibration to conclusion.
 * Synthetic truth is regenerated from the seed, never inferred from an imported
 * experiment. No hardware control, absolute calibration or coverage validation.
 * Internally SI. Original experimental arrays are never modified. */
(function (root, factory) {
  'use strict';
  const api = factory(typeof module === 'object' && module.exports ? require('./doctoral-inquiry.js') : root.AcademyDoctoralInquiry,
    typeof module === 'object' && module.exports ? require('./doctoral-pedagogy.js') : root.AcademyDoctoralPedagogy);
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.AcademyResearchJourney = api;
})(typeof window !== 'undefined' ? window : globalThis, function (I, P) {
  'use strict';
  const VERSION = '1.3.0', SCHEMA = 'academy-research-journey@1', GAMMA = 267.52218744e6;
  const MAX_BYTES = 24000000, PRESETS = ['isolated', 'gradient', 'convection', 'drift', 'overlap', 'phase', 'combined'];
  const SEQUENCES = ['pgse', 'ste', 'led', 'double-ste'];
  const SOURCE = [
    { id: 'sinnaeve2012', title: 'The Stejskal–Tanner equation generalized for any gradient shape', doi: '10.1002/cmr.a.21223' },
    { id: 'academy-model', title: 'Academy research journey: declared synthetic model and deterministic numerical checks', version: VERSION }
  ];
  const text = (es, en) => ({ es, en });
  const assumptions = [
    text('Simulación docente reproducible. La semilla conserva la muestra entre actividades; no es un experimento ni una identificación química.', 'Reproducible teaching simulation. The seed preserves the sample across activities; it is not an experiment or chemical identification.'),
    text('Bucles rectangulares ideales e instantáneos de RF. LED añade tiempo; doble STE usa dos bucles reflejados. No existe una conversión universal a p30, d20 o d5.', 'Ideal rectangular loops and instantaneous RF. LED adds time; double STE uses two mirrored loops. There is no universal conversion to p30, d20 or d5.'),
    text('La dependencia térmica exponencial declarada pertenece sólo a esta muestra sintética. No es una corrección universal de temperatura o viscosidad.', 'The declared exponential thermal dependence belongs only to this synthetic sample. It is not a universal temperature or viscosity correction.'),
    text('La incertidumbre es condicional al modelo, a las distribuciones introducidas y a los controles disponibles; su cobertura experimental no se ha validado.', 'Uncertainty is conditional on the model, supplied distributions and available controls; experimental coverage has not been validated.')
  ];
  function finite(v, name, lo = -Number.MAX_VALUE, hi = Number.MAX_VALUE) {
    if (typeof v !== 'number' || !Number.isFinite(v) || v < lo || v > hi) throw new RangeError(name + ' must be finite and within [' + lo + ', ' + hi + '].');
    return v;
  }
  function integer(v, name, lo, hi) { finite(v, name, lo, hi); if (!Number.isInteger(v)) throw new RangeError(name + ' must be an integer.'); return v; }
  function choice(v, allowed, name) { if (!allowed.includes(v)) throw new RangeError('Unknown ' + name + '.'); return v; }
  function string(v, name, max = 4000) { if (typeof v !== 'string' || v.length > max) throw new RangeError(name + ' must be a bounded string.'); return v; }
  function rng(seed) {
    let s = integer(seed, 'seed', 0, 4294967295) >>> 0, spare = null;
    return { uniform() { s = (Math.imul(1664525, s) + 1013904223) >>> 0; return (s + .5) / 4294967296; }, normal() { if (spare !== null) { const z = spare; spare = null; return z; } const r = Math.sqrt(-2 * Math.log(this.uniform())), p = 2 * Math.PI * this.uniform(); spare = r * Math.sin(p); return r * Math.cos(p); } };
  }
  const sum = a => a.reduce((s, x) => s + x, 0), mean = a => sum(a) / a.length;
  const dot = (a, b) => a.reduce((s, x, i) => s + x * b[i], 0);
  const sinc = x => Math.abs(x) < 1e-5 ? 1 - x * x / 6 + x ** 4 / 120 : Math.sin(x) / x;
  const rms = a => Math.sqrt(mean(a.map(v => v * v)));
  function quantile(a, q) { const b = a.slice().sort((x, y) => x - y), p = (b.length - 1) * q, i = Math.floor(p); return b[i] + (b[Math.min(i + 1, b.length - 1)] - b[i]) * (p - i); }
  function covariance(a, b) { const ma = mean(a), mb = mean(b); return mean(a.map((v, i) => (v - ma) * (b[i] - mb))); }
  function correlation(a, b) { const den = Math.sqrt(covariance(a, a) * covariance(b, b)); return den > 1e-36 ? covariance(a, b) / den : null; }
  function checkTree(v, depth = 0) {
    if (depth > 18) throw new RangeError('State exceeds nesting limit.');
    if (typeof v === 'number' && !Number.isFinite(v)) throw new RangeError('Non-finite state number.');
    if (typeof v === 'function' || typeof v === 'bigint' || typeof v === 'symbol') throw new RangeError('Unsupported state value.');
    if (v && typeof v === 'object') {
      if (!Array.isArray(v) && ![Object.prototype, null].includes(Object.getPrototypeOf(v))) throw new RangeError('Plain JSON data required.');
      for (const [k, child] of Object.entries(v)) { if (['__proto__', 'constructor', 'prototype'].includes(k)) throw new RangeError('Reserved state key.'); checkTree(child, depth + 1); }
    }
  }
  function clone(v) { checkTree(v); const raw = JSON.stringify(v); if (new TextEncoder().encode(raw).length > MAX_BYTES) throw new RangeError('State exceeds 24 MB.'); return JSON.parse(raw); }
  function state(s) {
    if (!s || s.schema !== SCHEMA || s.version !== VERSION || !['synthetic', 'experimental'].includes(s.kind)) throw new RangeError('Unsupported research-journey state.');
    integer(s.seed, 'case seed', 0, 4294967295); choice(s.preset, PRESETS, 'case preset');
    if (!Array.isArray(s.history) || s.history.length > 100 || !s.sample || !Array.isArray(s.sources)) throw new RangeError('Malformed research state.');
    if (s.acquisition) {
      if (!Array.isArray(s.acquisition.bs) || s.acquisition.bs.length < 4 || s.acquisition.bs.length > 256) throw new RangeError('Acquisition row limit is 4–256.');
      s.acquisition.bs.forEach(v => finite(v, 'b s/m²', 0, 1e12));
      if (s.acquisition.series && s.acquisition.series.length !== s.acquisition.bs.length) throw new RangeError('FID/b count mismatch.');
      if (s.acquisition.areas && s.acquisition.areas.length !== s.acquisition.bs.length) throw new RangeError('Integral/b count mismatch.');
    }
    return clone(s);
  }
  function step(s, name, input, update) {
    const out = state(s); Object.assign(out, update); out.stage = name;
    out.history.push({ step: name, input: clone(input), index: out.history.length }); out.history = out.history.slice(-100); return out;
  }
  function hidden(s) {
    if (s.kind !== 'synthetic') throw new RangeError('An experimental import has no synthetic truth.');
    const r = rng((s.seed ^ 0x9e3779b9) >>> 0), two = ['overlap', 'combined'].includes(s.preset);
    const D1 = (4.5 + 4 * r.uniform()) * 1e-10, p90Us = 7.5 + 4 * r.uniform();
    const gradientScale = ['gradient', 'combined'].includes(s.preset) ? (r.uniform() > .5 ? 1.06 + .07 * r.uniform() : .87 + .07 * r.uniform()) : 1;
    return { components: [{ id: 'A', D: D1, amplitude: two ? .58 : 1, ppm: 2, t2Seconds: .12 }, ...(two ? [{ id: 'B', D: D1 * (1.7 + 1.2 * r.uniform()), amplitude: .42, ppm: 2.08, t2Seconds: .10 }] : [])],
      gradientScale, p90Us, temperatureK: 298.15, thermalCoefficientPerK: .022, referenceD: 1.9e-9,
      vmax: ['convection', 'combined'].includes(s.preset) ? (3 + 3 * r.uniform()) * 1e-5 : 0,
      driftRatePerSecond: ['drift', 'combined'].includes(s.preset) ? .0003 + .0005 * r.uniform() : 0,
      phase0Deg: ['phase', 'combined'].includes(s.preset) ? 15 + 20 * r.uniform() : 0,
      phaseRampDeg: s.preset === 'phase' ? 25 : 0,
      spectralBaseline: s.preset === 'combined' ? .3 : 0 };
  }
  function bValue(g, delta, Delta, loops = 1) { return loops * (GAMMA * g * delta) ** 2 * (Delta - delta / 3); }
  function fit(b, y) { if (!I || !I.fitMono) throw new Error('AcademyDoctoralInquiry is required.'); return I.fitMono(b, y); }
  function createCase({ seed = 20261030, preset = 'combined' } = {}) {
    integer(seed, 'seed', 0, 4294967295); choice(preset, PRESETS, 'case preset');
    const s = { schema: SCHEMA, version: VERSION, kind: 'synthetic', id: 'RJ-' + preset + '-' + seed, seed, preset, stage: 'brief',
      evidenceStatus: 'synthetic-teaching-simulation', sample: { title: text('Una muestra, todas tus decisiones', 'One sample, all your decisions'), temperatureK: 298.15, sfMHz: 500, carrierPpm: 4, dwell_s: 1 / 4000,
        units: { D: 'm²/s', b: 's/m²', gradient: 'T/m', pulse: 'µs', temperature: 'K' }, description: text('Tu misión es obtener una conclusión defendible y elegir los controles que la sostienen.', 'Your task is to reach a defensible conclusion and select controls that support it.') },
      calibration: null, design: null, acquisition: null, processing: null, analysis: null, uncertainty: null, measurement: null, history: [], sources: SOURCE, assumptions: assumptions.slice() };
    const t = hidden(s), bs = Array.from({ length: 17 }, (_, i) => 1.5e9 * i / 16);
    s.pilots = { pulseCurve: Array.from({ length: 97 }, (_, i) => ({ pulseUs: i * .5, signedIntegral: Math.sin(Math.PI * i * .5 / (2 * t.p90Us)) })),
      firstNullUs: 2 * t.p90Us, nullOrder: 180, precedingMaximumUs: t.p90Us,
      referenceCurve: bs.map(b => ({ bNominal: b, signal: Math.exp(-b * t.gradientScale ** 2 * t.referenceD) })), referenceD: t.referenceD, referenceTemperatureK: t.temperatureK,
      instruction: text('Identifica el primer nulo de 180° a partir del máximo y el cambio de signo. Integra el patrón a la misma temperatura.', 'Identify the first 180° null from the preceding maximum and sign change. Integrate the standard at the same temperature.') };
    return s;
  }
  function calibrate(s, opts = {}) {
    const x = state(s), p = { p90Us: x.calibration?.p90Us ?? 10, gradientScale: x.calibration?.gradientScale ?? 1,
      referenceD: x.calibration?.referenceD ?? 1.9e-9, referenceTemperatureK: x.calibration?.referenceTemperatureK ?? 298.15,
      measuredTemperatureK: x.calibration?.measuredTemperatureK ?? 298.15, useReference: false, ...opts };
    if (opts.nullPulseUs !== undefined) { finite(opts.nullPulseUs, 'identified null µs', .1, 200); choice(opts.nullOrder ?? 180, [180, 360], 'identified null order'); p.p90Us = opts.nullPulseUs / ((opts.nullOrder ?? 180) / 90); }
    finite(p.p90Us, 'P90 µs', .1, 100); finite(p.gradientScale, 'gradient scale', .5, 1.5); finite(p.referenceD, 'reference D m²/s', 1e-13, 1e-8);
    finite(p.referenceTemperatureK, 'reference T K', 250, 350); finite(p.measuredTemperatureK, 'measured T K', 250, 350);
    let referenceFit = null, recommendation = null, usable = Math.abs(p.referenceTemperatureK - p.measuredTemperatureK) <= .2;
    if (x.kind === 'synthetic') {
      referenceFit = fit(x.pilots.referenceCurve.map(v => v.bNominal), x.pilots.referenceCurve.map(v => v.signal));
      recommendation = usable ? Math.sqrt(referenceFit.D / p.referenceD) : null;
      if (p.useReference) { if (!usable) throw new RangeError('Reference and measured temperatures differ; provide an appropriate reference.'); p.gradientScale = recommendation; }
    } else {
      if (p.useReference) throw new RangeError('No automatic calibration from an experimental import. Supply independent calibration evidence.');
      if (opts.applyScale && string(opts.calibrationEvidence || '', 'calibration evidence').trim().length < 20) throw new RangeError('Applying an experimental gradient scale requires independent calibration evidence.');
    }
    // Revising a gradient scale is a reprocessing decision, not a new
    // measurement. Retain acquired FIDs and nominal gradients if P90 is the
    // same. A pulse change requires re-acquisition and invalidates the series.
    const keepSynthetic = x.kind === 'synthetic' && !!x.acquisition && opts.keepAcquisition !== false && Math.abs(p.p90Us - (x.calibration?.p90Us || 0)) < 1e-12;
    let keptDesign = null, keptAcquisition = x.kind === 'experimental' ? x.acquisition : null;
    if (keepSynthetic) {
      keptDesign = clone(x.design); keptDesign.bApplied = keptDesign.bNominal.map(b => b * p.gradientScale ** 2);
      keptAcquisition = clone(x.acquisition); keptAcquisition.bs = keptAcquisition.rows.map(row => row.bNominal * p.gradientScale ** 2);
      keptAcquisition.rows.forEach((row, i) => { row.b = keptAcquisition.bs[i]; });
    }
    return step(x, 'calibration', p, { calibration: { ...p, referenceFit, recommendation, usable, acquisitionRetained: keepSynthetic || x.kind === 'experimental', appliedToImportedB: x.kind === 'experimental' && opts.applyScale === true,
      status: x.kind === 'synthetic' ? 'synthetic-calibration-decision' : 'user-supplied-calibration-evidence', warning: text('Una calibración sólo es transferible a la misma forma de onda y condiciones verificadas.', 'A calibration is transferable only to the same verified waveform and conditions.') }, design: keptDesign, acquisition: keptAcquisition, processing: null, analysis: null, uncertainty: null, measurement: null });
  }
  function design(s, opts = {}) {
    const x = state(s); if (!x.calibration) throw new RangeError('Record the calibration decision first.');
    if (x.kind === 'experimental') throw new RangeError('Imported acquisition metadata are read-only; design a separate control rather than rewriting their history.');
    const p = { sequence: 'ste', deltaMs: 2, bigDeltaMs: 80, ledMs: 5, gradientMax: .35, points: 24, scans: 4, repeats: 1, recycleSeconds: 1.5, acquisitionSeconds: .3, order: 'ascending', budgetMinutes: 12, ...opts };
    choice(p.sequence, SEQUENCES, 'sequence'); choice(p.order, ['ascending', 'descending', 'interleaved'], 'gradient order');
    finite(p.deltaMs, 'delta ms', .05, 20); finite(p.bigDeltaMs, 'Delta ms', p.deltaMs, 1000); finite(p.ledMs, 'LED ms', 0, 100);
    finite(p.gradientMax, 'maximum gradient T/m', .01, .8); integer(p.points, 'gradient points', 6, 64); integer(p.scans, 'scans', 1, 128); integer(p.repeats, 'repeats', 1, 4);
    if (p.points * p.repeats > 256) throw new RangeError('Maximum 256 acquisition rows.');
    finite(p.recycleSeconds, 'recycle seconds', .01, 30); finite(p.acquisitionSeconds, 'acquisition seconds', .01, 10); finite(p.budgetMinutes, 'budget minutes', .1, 240);
    const loops = p.sequence === 'double-ste' ? 2 : 1, delta = p.deltaMs / 1000, Delta = p.bigDeltaMs / 1000;
    const gradients = Array.from({ length: p.points }, (_, i) => p.gradientMax * Math.sqrt(i / (p.points - 1))), nominal = gradients.map(g => bValue(g, delta, Delta, loops));
    const cycle = p.recycleSeconds + p.acquisitionSeconds + loops * (Delta + delta) + (['led', 'double-ste'].includes(p.sequence) ? p.ledMs / 1000 : 0);
    const durationSeconds = p.points * p.repeats * p.scans * cycle;
    return step(x, 'design', p, { design: { parameters: p, gradients, bNominal: nominal, bApplied: nominal.map(b => b * x.calibration.gradientScale ** 2), durationSeconds, withinBudget: durationSeconds <= p.budgetMinutes * 60,
      cycleSeconds: cycle, convention: text('δ es la duración de un lóbulo rectangular; Δ se mide entre bordes iniciales de cada bucle. Doble STE suma dos bucles reflejados.', 'δ is one rectangular-lobe duration; Δ is the leading-edge interval of each loop. Double STE sums two mirrored loops.') }, acquisition: null, processing: null, analysis: null, uncertainty: null, measurement: null });
  }
  function signalAt(s, g, time, params) {
    const t = hidden(s), delta = params.deltaMs / 1000, Delta = params.bigDeltaMs / 1000, loops = params.sequence === 'double-ste' ? 2 : 1;
    const b = bValue(g * t.gradientScale, delta, Delta, loops), moment = params.sequence === 'double-ste' ? 0 : GAMMA * g * t.gradientScale * delta * Delta;
    const thermal = Math.exp(t.thermalCoefficientPerK * ((params.temperatureK ?? t.temperatureK) - t.temperatureK));
    const pulse = Math.sin(Math.PI * s.calibration.p90Us / (2 * t.p90Us)), recovery = 1 - Math.exp(-params.recycleSeconds / 1.2), transfer = params.sequence === 'pgse' ? 1 : loops === 2 ? .25 : .5;
    const relax = params.sequence === 'pgse' ? Math.exp(-2 * Delta / .22) : Math.exp(-loops * Math.max(0, Delta - delta) / 1.2 - 2 * loops * delta / .22);
    return { b, common: pulse * recovery * transfer * relax * Math.exp(-t.driftRatePerSecond * time) * sinc(moment * t.vmax), components: t.components.map(c => ({ ...c, amplitude: c.amplitude * Math.exp(-b * c.D * thermal) })), truth: t };
  }
  function acquire(s, opts = {}) {
    const x = state(s); if (x.kind !== 'synthetic') throw new RangeError('Experimental imports are read-only; the simulator cannot acquire a real control.');
    if (!x.design) throw new RangeError('Design the acquisition first.');
    const noise = finite(opts.noise ?? .003, 'single-scan complex FID noise', 0, .1), seed = integer(opts.seed ?? ((x.seed ^ 0x85ebca6b) >>> 0), 'acquisition seed', 0, 4294967295);
    const pointsFID = integer(opts.pointsFID ?? 256, 'FID points', 128, 2048); if (pointsFID & (pointsFID - 1)) throw new RangeError('FID points must be a power of two.');
    const p = x.design.parameters, r = rng(seed), order = Array.from({ length: p.points }, (_, i) => i);
    if (p.order === 'descending') order.reverse();
    if (p.order === 'interleaved') { const low = order.filter(i => i % 2 === 0), high = order.filter(i => i % 2 === 1).reverse(); order.splice(0, order.length, ...low.flatMap((v, i) => i < high.length ? [v, high[i]] : [v])); }
    const rows = [], series = [];
    for (let rep = 0; rep < p.repeats; rep++) for (const index of order) {
      const time = (rows.length + .5) * p.scans * x.design.cycleSeconds, g = x.design.gradients[index], calc = signalAt(x, g, time, p), real = [], imag = [];
      const phase = (calc.truth.phase0Deg + calc.truth.phaseRampDeg * index / (p.points - 1)) * Math.PI / 180;
      for (let j = 0; j < pointsFID; j++) {
        const tt = j * x.sample.dwell_s; let re = 0, im = 0;
        for (const c of calc.components) { const a = calc.common * c.amplitude * Math.exp(-tt / c.t2Seconds), angle = 2 * Math.PI * (c.ppm - x.sample.carrierPpm) * x.sample.sfMHz * tt + phase; re += a * Math.cos(angle); im += a * Math.sin(angle); }
        real.push(re + r.normal() * noise / Math.sqrt(p.scans) + (j === 0 ? calc.truth.spectralBaseline : 0)); imag.push(im + r.normal() * noise / Math.sqrt(p.scans));
      }
      const fid = { real, imag, dwell_s: x.sample.dwell_s, sfMHz: x.sample.sfMHz, carrierPpm: x.sample.carrierPpm };
      rows.push({ index, repeat: rep, timeSeconds: time, gradientTm: g, bNominal: x.design.bNominal[index], b: x.design.bApplied[index] }); series.push(fid);
    }
    return step(x, 'acquire', { noise, seed, pointsFID }, { acquisition: { kind: 'synthetic-raw-complex-FID', rows, bs: rows.map(v => v.b), series, noise, seed, pointsFID, referenceTemperatureK: x.sample.temperatureK,
      noiseModel: 'Independent Gaussian real/imaginary single-scan noise; scan averaging divides its SD by sqrt(NS). Repeats retain their own acquisition times.' }, processing: null, analysis: null, uncertainty: null, measurement: null });
  }
  function normalize(values, bs) { const i = bs.indexOf(Math.min(...bs)), ref = values[i]; if (Math.abs(ref) < 1e-12) throw new RangeError('The signed reference integral is zero; inspect phase and integration.'); return values.map(v => v / ref); }
  function process(s, opts = {}) {
    const x = state(s); if (!x.acquisition) throw new RangeError('Acquire or attach data first.');
    const p = { phaseDeg: 0, phase1Deg: 0, baseline: 0, window: 'all', lbHz: .3, zeroFill: 1,
      groupDelayPoints: Number(x.acquisition.originalProvenance?.metadata?.GRPDLY || 0), ...opts };
    finite(p.phaseDeg, 'phase degrees', -720, 720); finite(p.baseline, 'spectral constant baseline', -10000, 10000); finite(p.lbHz, 'LB Hz', 0, 1000); choice(p.zeroFill, [1, 2, 4], 'zero filling'); choice(p.window, ['all', 'peak1', 'peak2', 'custom'], 'integration window');
    finite(p.phase1Deg, 'linear phase degrees', -7200, 7200); finite(p.groupDelayPoints, 'digital filter group delay points', 0, 1000);
    const windows = { all: [1.45, 2.65], peak1: [1.82, 2.18], peak2: [2.02, 2.38] };
    if (p.window === 'custom') { if (!Array.isArray(p.windowPpm) || p.windowPpm.length !== 2) throw new RangeError('Custom window requires two ppm bounds.'); p.windowPpm.forEach(v => finite(v, 'ppm bound', -100, 100)); if (p.windowPpm[0] === p.windowPpm[1]) throw new RangeError('Integration window needs width.'); windows.custom = p.windowPpm.slice(); }
    const scale = x.kind === 'experimental' && x.calibration?.appliedToImportedB ? x.calibration.gradientScale ** 2 : 1, bs = x.acquisition.bs.map(b => b * scale);
    let integrals, perPeak = [], firstSpectrum = null, lastSpectrum = null;
    if (x.acquisition.series || x.acquisition.spectra) {
      if (!P || !P.processFID) throw new Error('AcademyDoctoralPedagogy is required for FID processing.');
      const spectra = x.acquisition.series ? x.acquisition.series.map(fid => P.processFID(fid, { phase0Deg: p.phaseDeg, phase1Deg: p.phase1Deg, groupDelayPoints: p.groupDelayPoints, lbHz: p.lbHz, zeroFill: p.zeroFill })) : clone(x.acquisition.spectra);
      if (!x.acquisition.series && (p.phaseDeg || p.phase1Deg)) spectra.forEach(sp => {
        if (sp.imaginaryProvided === false) throw new RangeError('Complex spectra are required to rephase; an imported real-only spectrum has no recoverable imaginary channel.');
        const re = sp.real.slice(), im = sp.imag.slice();
        for (let i = 0; i < re.length; i++) { const a = (p.phaseDeg + p.phase1Deg * (i / (re.length - 1) - .5)) * Math.PI / 180; sp.real[i] = re[i] * Math.cos(a) - im[i] * Math.sin(a); sp.imag[i] = re[i] * Math.sin(a) + im[i] * Math.cos(a); }
      });
      spectra.forEach(sp => { if (p.baseline) sp.real = sp.real.map(v => v - p.baseline); });
      integrals = spectra.map(sp => P.integrate(sp, ...windows[p.window]).area); firstSpectrum = spectra[0]; lastSpectrum = spectra.at(-1);
      const peakWindows = x.kind === 'synthetic' ? ['peak1', 'peak2'].map(id => ({ id, windowPpm: windows[id] })) : [];
      if (opts.additionalWindows !== undefined) {
        if (!Array.isArray(opts.additionalWindows) || opts.additionalWindows.length > 8) throw new RangeError('At most eight explicit additional integration windows.');
        opts.additionalWindows.forEach((w, i) => { if (!Array.isArray(w) || w.length !== 2 || w[0] === w[1]) throw new RangeError('Additional window requires two distinct ppm bounds.'); w.forEach(v => finite(v, 'additional ppm bound', -100, 100)); peakWindows.push({ id: 'window-' + (i + 1), windowPpm: w.slice() }); });
      }
      perPeak = peakWindows.map(w => { const areas = spectra.map(sp => P.integrate(sp, ...w.windowPpm).area); return { ...w, integrals: areas, normalized: Math.abs(areas[bs.indexOf(Math.min(...bs))]) > 1e-12 ? normalize(areas, bs) : null }; });
    } else if (x.acquisition.areas) {
      if (p.phaseDeg !== 0 || p.phase1Deg !== 0 || p.baseline !== 0) throw new RangeError('Phase and spectral baseline cannot be changed after importing integrals only. Import original FIDs/spectra to reprocess.');
      integrals = x.acquisition.areas.slice();
    } else throw new RangeError('Raw FID arrays were omitted; reattach originals or import an export containing them.');
    const normalized = normalize(integrals, bs);
    return step(x, 'process', p, { processing: { parameters: p, bs, integrals, normalized, perPeak, firstSpectrum, lastSpectrum, windowPpm: windows[p.window], signedIntegralsRetained: true,
      appliedOperations: x.acquisition.series ? ['digital-filter-delay', 'apodization', 'FFT', 'complex-phase', 'constant-baseline', 'signed-integration'] : x.acquisition.spectra ? ['complex-phase-if-supplied', 'constant-baseline', 'signed-integration'] : ['retain-imported-signed-integrals'],
      caveat: text('Las ventanas no son componentes puras. El solapamiento puede producir una atenuación efectiva de varias poblaciones.', 'Windows are not pure components. Overlap can produce an effective attenuation containing several populations.') }, analysis: null, uncertainty: null, measurement: null });
  }
  function analyze(s, opts = {}) {
    const x = state(s); if (!x.processing) throw new RangeError('Process the same data first.');
    const p = { method: 'mono', regularization: .03, ...opts }; choice(p.method, ['mono', 'nnls', 'tikhonov', 'l1'], 'analysis method'); finite(p.regularization, 'regularization', 0, 10);
    const { bs, normalized: y } = x.processing, mono = fit(bs, y), grid = Array.from({ length: 48 }, (_, i) => 2e-11 * 10 ** (i / 47 * Math.log10(400))), kernel = bs.map(b => grid.map(D => Math.exp(-b * D)));
    let distribution = null;
    if (p.method !== 'mono') { const f = I.regularizedFit(kernel, y, { smooth: p.method === 'tikhonov' ? p.regularization * bs.length : 0, l1: p.method === 'l1' ? p.regularization * bs.length : 0 }); const total = sum(f.weights); distribution = { grid, ...f, centroid: total > 0 ? dot(grid, f.weights) / total : null, identity: 'nonnegative-distribution-on-declared-log-grid' }; }
    const chosenD = distribution ? distribution.centroid : mono.D;
    const perPeak = x.processing.perPeak.filter(v => v.normalized && Math.abs(v.integrals[0]) > Math.max(...x.processing.integrals.map(Math.abs)) * .02).map(v => ({ id: v.id, fit: fit(bs, v.normalized), windowPpm: v.windowPpm }));
    return step(x, 'inference', p, { analysis: { method: p.method, parameters: p, D_m2_s: chosenD, mono, distribution, perPeak, residualRms: distribution ? distribution.rms : mono.rms,
      reportedQuantity: distribution ? 'conditional grid-weighted D centroid' : 'conditional monoexponential D', absoluteCalibrationValidated: false,
      warning: text('Un residuo pequeño o un máximo estrecho no identifican una especie ni prueban una distribución única. Comprueba controles y datos reservados.', 'A small residual or narrow peak does not identify a species or prove a unique distribution. Check controls and held-out observations.') }, uncertainty: null, measurement: null });
  }
  function uncertainty(s, opts = {}) {
    const x = state(s); if (!x.processing || !x.analysis) throw new RangeError('Analyze processed data before computing uncertainty.');
    const p = { samples: 120, gradientRelativeSd: .02, temperatureSdK: .3, processingRelativeSd: .01, noiseRelativeSd: .015, sequenceRelativeSd: 0, ...opts };
    integer(p.samples, 'Monte Carlo samples', 30, 500); for (const name of ['gradientRelativeSd', 'processingRelativeSd', 'noiseRelativeSd', 'sequenceRelativeSd']) finite(p[name], name, 0, .3); finite(p.temperatureSdK, 'temperature SD K', 0, 5);
    const synthetic = x.kind === 'synthetic', alpha = synthetic ? hidden(x).thermalCoefficientPerK : opts.temperatureCoefficientPerK;
    if (alpha !== undefined && alpha !== null) finite(alpha, 'declared dlnD/dT K^-1', -.3, .3);
    const temperatureUnquantified = !synthetic && p.temperatureSdK > 0 && (alpha === undefined || alpha === null);
    const unquantifiedSources = temperatureUnquantified ? ['temperature: supply a sample/reference-specific dlnD/dT; no universal thermal correction is assumed'] : [];
    if (!synthetic && x.calibration?.status === 'independent-calibration-not-established') unquantifiedSources.push('absolute scale: independent reference calibration is not established; supplied Monte Carlo SDs are assumed sensitivities, not measured calibration uncertainty');
    const usefulPeaks = x.processing.perPeak.filter(v => v.normalized && Math.abs(v.integrals[0]) > Math.max(...x.processing.integrals.map(Math.abs)) * .02);
    const curves = [x.processing.normalized, ...usefulPeaks.map(v => v.normalized)], bs = x.processing.bs;
    // Shared noise in overlapping integration windows is a Gram construction:
    // each window sums the same independent spectral-bin noise. This gives a
    // positive-semidefinite covariance without pretending pure components.
    const curveWindows = [x.processing.windowPpm, ...usefulPeaks.map(v => v.windowPpm)], noiseBins = 64,
      lower = Math.min(...curveWindows.flat()), upper = Math.max(...curveWindows.flat()),
      weights = curveWindows.map(w => { const a = Math.min(...w), b = Math.max(...w), v = Array.from({ length: noiseBins }, (_, i) => { const z = lower + (i + .5) / noiseBins * (upper - lower); return z >= a && z <= b ? 1 : 0; }), n = Math.sqrt(dot(v, v)); return v.map(x => x / Math.max(n, 1)); });
    const noiseCorrelation = weights.map(a => weights.map(b => dot(a, b)));
    const scans = x.design?.parameters.scans || 1, noiseSd = p.noiseRelativeSd / Math.sqrt(scans), drawSeed = (x.seed ^ 0xc2b2ae35) >>> 0;
    function run(enabled) {
      const output = [], common = rng(drawSeed);
      for (let j = 0; j < p.samples; j++) {
        const gradientLogSd = Math.sqrt(Math.log1p(p.gradientRelativeSd ** 2)), sequenceLogSd = Math.sqrt(Math.log1p(p.sequenceRelativeSd ** 2));
        const z = [common.normal(), common.normal(), common.normal(), common.normal()], g = enabled.includes('gradient') ? Math.exp(z[0] * gradientLogSd - .5 * gradientLogSd ** 2) : 1,
          temperatureShift = enabled.includes('temperature') && alpha !== undefined && alpha !== null ? z[1] * p.temperatureSdK : 0,
          sequence = enabled.includes('sequence') ? Math.exp(z[2] * sequenceLogSd - .5 * sequenceLogSd ** 2) : 1,
          baseline = enabled.includes('processing') ? z[3] * p.processingRelativeSd : 0,
          factors = g ** 2 * Math.exp((alpha || 0) * temperatureShift) * sequence, correctedB = bs.map(b => b * factors), nr = rng((drawSeed + Math.imul(j + 1, 2654435761)) >>> 0);
        const windowNoise = curves.map(() => []);
        for (let row = 0; row < bs.length; row++) {
          const bins = enabled.includes('noise') ? Array.from({ length: noiseBins }, () => nr.normal()) : Array(noiseBins).fill(0);
          weights.forEach((w, i) => windowNoise[i].push(noiseSd * dot(w, bins)));
        }
        const fits = curves.map((curve, i) => fit(correctedB, curve.map((y, row) => y + baseline + windowNoise[i][row])));
        output.push({ gradientFactor: g, temperatureShiftK: temperatureShift, sequenceBFactor: sequence, baseline, D: fits.map(f => f.D), atBoundary: fits.map(f => f.atBoundary) });
      }
      return output;
    }
    const full = run(['gradient', 'temperature', 'sequence', 'processing', 'noise']), ds = full.map(v => v.D[0]), centre = x.analysis.mono.D;
    const labels = { gradient: text('Escala de gradiente compartida', 'Shared gradient scale'), temperature: text('Temperatura compartida', 'Shared temperature'), processing: text('Línea de base correlacionada', 'Correlated baseline'), noise: text('Ruido de cada observación', 'Observation noise'), sequence: text('Escala b del modelo de secuencia', 'Sequence-model b scale') };
    const sourceContributions = Object.keys(labels).map(id => { const draws = run([id]).map(v => v.D[0]), sd = Math.sqrt(covariance(draws, draws)); return { id, label: labels[id], Dsd_m2_s: sd, relativeSd: sd / centre, interval95: [quantile(draws, .025), quantile(draws, .975)], quantified: !(id === 'temperature' && temperatureUnquantified), distributionSource: 'user-supplied conditional sensitivity distribution; not independently calibrated uncertainty' }; });
    const matrix = curves.map((_, i) => curves.map((__, j) => correlation(full.map(v => v.D[i]), full.map(v => v.D[j]))));
    return step(x, 'uncertainty', p, { uncertainty: { parameters: p, samples: p.samples, interval95: [quantile(ds, .025), quantile(ds, .975)], medianD: quantile(ds, .5), sourceContributions, correlation: matrix, unquantifiedSources,
      sharedDraws: full.slice(0, 12), noiseCorrelation, boundaryDraws: full.filter(v => v.atBoundary[0]).length,
      intervalReliability: full.some(v => v.atBoundary[0]) ? 'conditional-and-fit-boundary-limited' : 'conditional-model-sensitivity-only',
      perCurveIntervals: curves.map((_, i) => [quantile(full.map(v => v.D[i]), .025), quantile(full.map(v => v.D[i]), .975)]), coverageValidated: false,
      scope: text('Monte Carlo condicional. Cada réplica comparte la misma escala de gradiente, temperatura y sesgo de procesado en todas las filas y ventanas. No incluye todas las posibles fuentes experimentales ni corrige un sesgo desconocido.', 'Conditional Monte Carlo. Each replicate shares one gradient scale, temperature and processing bias across every row and window. It neither includes every possible experimental source nor corrects unknown bias.'),
      noiseModel: 'A shared white-spectral-noise-bin Gram model correlates overlapping window integrals. Relative SD and scan averaging are supplied assumptions, not calibrated experimental noise or bootstrap coverage.',
      distributions: { gradient: 'positive lognormal, mean 1, coefficient of variation gradientRelativeSd; shared across all rows/windows', sequence: 'positive lognormal, mean 1, coefficient of variation sequenceRelativeSd; shared b scale', temperature: 'zero-mean Gaussian with supplied SD K, shared across all rows/windows', processing: 'zero-mean Gaussian common normalized baseline offset', noise: 'zero-mean Gaussian spectral-bin noise; overlapping-window covariance and sqrt(NS) averaging are explicit' },
      thermalModel: alpha === undefined || alpha === null ? null : { coefficientPerK: alpha, convention: 'b_eff = b × g_factor² × exp(alpha ΔT) × sequence_factor; reported D is referred to the declared reference temperature' } } });
  }
  function twoFit(bs, y, d1, d2) {
    const a = bs.map(b => Math.exp(-b * d1)), b = bs.map(v => Math.exp(-v * d2)), aa = dot(a, a), bb = dot(b, b), ab = dot(a, b), det = aa * bb - ab * ab;
    if (det < 1e-16) return null;
    let w1 = (dot(a, y) * bb - dot(b, y) * ab) / det, w2 = (dot(b, y) * aa - dot(a, y) * ab) / det;
    if (w1 < 0 || w2 < 0) return null;
    const predicted = bs.map((v, i) => w1 * a[i] + w2 * b[i]), residual = y.map((v, i) => v - predicted[i]);
    return { Ds: [d1, d2], amplitudes: [w1, w2], predicted, residualRms: rms(residual), sse: dot(residual, residual) };
  }
  function proposeMeasurement(s, opts = {}) {
    const x = state(s); if (!x.analysis || !x.processing) throw new RangeError('Analyze the existing observations first.');
    const candidate = choice(opts.candidate || 'higher-b', ['higher-b', 'replicate', 'reverse', 'delta', 'flow-compensated'], 'next measurement'), points = integer(opts.points ?? 12, 'control points', 6, 64);
    const seed = integer(opts.seed ?? ((x.seed ^ 0x27d4eb2f) >>> 0), 'reserved control seed', 0, 4294967295);
    if (seed === x.acquisition.seed) throw new RangeError('Reserved observations require a seed independent of the original acquisition.');
    const noise = finite(opts.noise ?? .01, 'control normalized noise SD', 0, .2), maxB = finite(opts.maxB ?? Math.min(2e10, Math.max(...x.processing.bs) * 2), 'proposed b maximum', 1e7, 2e10), { bs, normalized: y } = x.processing;
    const mono = x.analysis.mono, distributions = [{ id: 'mono', Ds: [mono.D], amplitudes: [mono.amplitude], predicted: mono.prediction, residualRms: mono.rms, sse: sum(mono.residual.map(v => v * v)) }];
    const alternatives = [];
    for (const low of [.25, .5, .7, .85]) for (const high of [1.2, 1.5, 2, 3, 5, 8]) { const f = twoFit(bs, y, mono.D * low, mono.D * high); if (f) alternatives.push(f); }
    alternatives.sort((a, b) => a.sse - b.sse);
    for (let i = 0; i < Math.min(2, alternatives.length); i++) distributions.push({ id: 'two-component-' + (i + 1), ...alternatives[i] });
    const tolerance = bs.length * noise ** 2; distributions.forEach(v => { v.compatibleWithObservedAtDeclaredNoise = v.sse <= distributions[0].sse + tolerance; });
    const predict = (model, b) => sum(model.Ds.map((D, i) => model.amplitudes[i] * Math.exp(-b * D)));
    const plans = ['higher-b', 'replicate', 'reverse', 'delta', 'flow-compensated'].map(id => {
      const bmax = id === 'higher-b' ? maxB : Math.max(...bs), values = Array.from({ length: points }, (_, i) => bmax * i / (points - 1));
      const predictions = distributions.map(model => ({ id: model.id, signal: values.map(b => predict(model, b)) }));
      const separation = predictions.length > 1 ? Math.max(...predictions.slice(1).map(v => rms(v.signal.map((yy, i) => yy - predictions[0].signal[i])))) : 0;
      return { id, bs: values, predictions, predictedSeparationRms: separation, separationToNoise: noise > 0 ? separation / noise : null,
        purpose: id === 'higher-b' ? 'free-diffusion distribution extrapolation' : id === 'reverse' ? 'drift control: the same b values at reversed acquisition times' : id === 'delta' ? 'time/flow control at matched b; free-diffusion distribution predictions remain equal' : id === 'flow-compensated' ? 'mirrored-loop uniform-velocity control at matched b' : 'precision control; does not remove shared calibration bias' };
    });
    let observations = null, heldoutRanking = null; const selected = plans.find(v => v.id === candidate);
    if (opts.observe) {
      if (string(opts.prediction || '', 'prior prediction', 8000).trim().length < 20) throw new RangeError('Record a prediction of at least 20 characters before revealing reserved observations.');
      if (x.kind === 'synthetic') {
        const p = { ...x.design.parameters }; if (candidate === 'delta') p.bigDeltaMs = Math.min(1000, p.bigDeltaMs * 2); if (candidate === 'flow-compensated') p.sequence = 'double-ste';
        const delta = p.deltaMs / 1000, Delta = p.bigDeltaMs / 1000, loops = p.sequence === 'double-ste' ? 2 : 1, r = rng(seed), v = [];
        for (let i = 0; i < points; i++) {
          const b = selected.bs[i], g = Math.sqrt(b / (loops * (GAMMA * delta * x.calibration.gradientScale) ** 2 * (Delta - delta / 3)));
          if (g > .8) throw new RangeError('The proposed b exceeds the 0.8 T/m teaching limit; change δ/Δ or reduce b.');
          const timeIndex = candidate === 'reverse' ? points - 1 - i : i, time = (timeIndex + .5) * p.scans * x.design.cycleSeconds, calc = signalAt(x, g, time, p);
          // Held-out measurements are declared normalized ideal peak areas. They
          // use the same sample/gradient/flow/drift, but independent noise; they
          // are not silently substituted for the original processed FID data.
          v.push({ b, timeSeconds: time, signal: calc.common * sum(calc.components.map(c => c.amplitude)), gradientTm: g });
        }
        const ref = v[0].signal; observations = v.map(row => ({ ...row, signal: row.signal / Math.max(Math.abs(ref), 1e-12) + r.normal() * noise }));
        heldoutRanking = selected.predictions.map(model => ({ id: model.id, residualRms: rms(observations.map((row, i) => row.signal - model.signal[i])) })).sort((a, b) => a.residualRms - b.residualRms);
      }
    }
    return step(x, 'next-measurement', { candidate, points, seed, noise, maxB, observe: !!opts.observe, prediction: opts.prediction || '' }, { measurement: { distributions, plans, selected, observations, heldoutRanking, reservedSeed: seed, trainingDataUnchanged: true, experimentalControlRequired: x.kind === 'experimental',
      caveat: text('La separación prevista usa modelos de difusión libre ajustados sólo a los datos iniciales. Cambiar Δ u orden también pone a prueba causas fuera de esos modelos. Un control sintético no valida un experimento.', 'Predicted separation uses free-diffusion models fitted only to initial observations. Changing Δ or order also tests causes outside those models. A synthetic control does not validate an experiment.'),
      observationModel: 'Reserved independently seeded normalized ideal peak-area observations; same sample, calibration, flow and drift. Original FID processing remains unchanged.' } });
  }
  function attachExperimental(s, opts) {
    const base = state(s); if (!opts || typeof opts !== 'object') throw new RangeError('Experimental attachment metadata required.');
    string(opts.id, 'dataset id', 200); if (!opts.id) throw new RangeError('Dataset id is required.');
    if (!opts.source || !opts.license) throw new RangeError('Document source and license/permission before attaching data.');
    if (!Array.isArray(opts.bs) || opts.bs.length < 4 || opts.bs.length > 256) throw new RangeError('Import requires 4–256 b values.'); opts.bs.forEach(b => finite(b, 'imported b s/m²', 0, 1e12));
    if (Math.max(...opts.bs) === Math.min(...opts.bs)) throw new RangeError('Distinct b values are required.');
    let series = null, spectra = null, areas = null;
    if (opts.fids) {
      if (!Array.isArray(opts.fids) || opts.fids.length !== opts.bs.length) throw new RangeError('FID/b count mismatch.');
      series = opts.fids.map(fid => { if (!Array.isArray(fid.real) || !Array.isArray(fid.imag) || fid.real.length !== fid.imag.length || fid.real.length < 32 || fid.real.length > 32768) throw new RangeError('Import requires paired 32–32768-point complex FIDs.'); fid.real.forEach(v => finite(v, 'FID real')); fid.imag.forEach(v => finite(v, 'FID imag')); return { real: fid.real.slice(), imag: fid.imag.slice(), dwell_s: finite(fid.dwell_s ?? opts.metadata?.dwell_s, 'dwell s', 1e-7, 1), sfMHz: finite(fid.sfMHz ?? opts.metadata?.sfMHz, 'SF MHz', 1, 2000), carrierPpm: finite(fid.carrierPpm ?? opts.metadata?.carrierPpm ?? 0, 'carrier ppm', -100, 100) }; });
    } else if (opts.spectra) {
      if (!Array.isArray(opts.spectra) || opts.spectra.length !== opts.bs.length) throw new RangeError('Spectrum/b count mismatch.');
      spectra = opts.spectra.map(sp => { if (!Array.isArray(sp.ppm) || !Array.isArray(sp.real) || sp.ppm.length !== sp.real.length || sp.ppm.length < 4 || sp.ppm.length > 32768) throw new RangeError('Paired spectral ppm/intensity arrays required.'); sp.ppm.forEach(v => finite(v, 'spectral ppm', -100, 100)); sp.real.forEach(v => finite(v, 'spectral intensity')); if (sp.imag && (!Array.isArray(sp.imag) || sp.imag.length !== sp.real.length)) throw new RangeError('Imaginary spectrum length mismatch.'); if (sp.imag) sp.imag.forEach(v => finite(v, 'spectral imaginary intensity')); return { ppm: sp.ppm.slice(), real: sp.real.slice(), imag: Array.isArray(sp.imag) ? sp.imag.slice() : sp.real.map(() => 0), imaginaryProvided: !!sp.imag }; });
    } else if (opts.areas) {
      if (!Array.isArray(opts.areas) || opts.areas.length !== opts.bs.length) throw new RangeError('Integral/b count mismatch.'); opts.areas.forEach(v => finite(v, 'signed integral')); areas = opts.areas.slice();
    } else throw new RangeError('Attach FIDs, spectra or signed integrals.');
    const hashes = opts.originalHashes || []; if (!Array.isArray(hashes) || hashes.length > 100) throw new RangeError('Invalid original hash manifest.');
    hashes.forEach(h => { if (!h || typeof h.path !== 'string' || !/^[a-f0-9]{64}$/i.test(h.sha256 || '')) throw new RangeError('Original files require path and SHA256.'); });
    const originalProvenance = clone({ id: opts.id, source: opts.source, license: opts.license, originalHashes: hashes, metadata: opts.metadata || {}, bProvenance: opts.bProvenance || 'user-supplied b values: nominal/conditional until independently verified' });
    return step(base, 'experimental-import', { datasetId: opts.id }, { kind: 'experimental', id: 'EXP-' + opts.id, evidenceStatus: 'experimental-import-conditional-provenance', sample: { ...base.sample, ...clone(opts.metadata || {}), title: text('Datos experimentales: ' + opts.id, 'Experimental data: ' + opts.id) }, pilots: null,
      calibration: { p90Us: null, gradientScale: 1, usable: false, appliedToImportedB: false, status: 'independent-calibration-not-established' }, design: null,
      acquisition: { kind: series ? 'imported-complex-FID' : spectra ? 'imported-processed-spectra' : 'imported-signed-integrals', bs: opts.bs.slice(), series, spectra, areas, rows: opts.bs.map((b, i) => ({ index: i, b })), seed: null, originalProvenance, readOnlyOriginals: true }, processing: null, analysis: null, uncertainty: null, measurement: null,
      assumptions: [text('Importación experimental: no existe verdad sintética. La escala b y D permanecen nominales/condicionales hasta verificar independientemente calibración y secuencia.', 'Experimental import: no synthetic truth exists. b and D remain nominal/conditional until calibration and sequence are independently verified.'), assumptions[3]] });
  }
  function revealCase(s) { const x = state(s); return x.kind === 'synthetic' ? { ...hidden(x), qualification: text('Verdad del generador sintético; no evidencia experimental.', 'Synthetic generator truth; not experimental evidence.') } : null; }
  function canonical(v) { return v && typeof v === 'object' ? Array.isArray(v) ? '[' + v.map(canonical).join(',') + ']' : '{' + Object.keys(v).sort().map(k => JSON.stringify(k) + ':' + canonical(v[k])).join(',') + '}' : JSON.stringify(v); }
  function checksum(v) { let h = 2166136261; for (const byte of new TextEncoder().encode(canonical(v))) { h ^= byte; h = Math.imul(h, 16777619); } return (h >>> 0).toString(16).padStart(8, '0'); }
  function exportCase(s, { includeRaw = false } = {}) {
    const data = state(s);
    if (!includeRaw && data.acquisition) { if (data.acquisition.series) data.acquisition.series = null; if (data.acquisition.spectra) data.acquisition.spectra = null; data.acquisition.rawOmitted = true; if (data.processing) data.acquisition.areas = data.processing.integrals.slice(); }
    return { format: 'DiffAtOnce-Academy-research-case', schema: SCHEMA, version: VERSION, checksum: checksum(data), checksumAlgorithm: 'FNV1a32-accidental-corruption-only-not-authentication', privacy: 'Selected case, student decision inputs and optional raw arrays are included only in this explicit local export. No network transfer.', caseState: data };
  }
  function validateImport(raw) {
    if (typeof raw === 'string') { if (new TextEncoder().encode(raw).length > MAX_BYTES) throw new RangeError('Import exceeds 24 MB.'); raw = JSON.parse(raw); }
    const e = clone(raw);
    if (!e || e.format !== 'DiffAtOnce-Academy-research-case' || e.schema !== SCHEMA || e.version !== VERSION || e.checksumAlgorithm !== 'FNV1a32-accidental-corruption-only-not-authentication' || e.checksum !== checksum(e.caseState)) throw new RangeError('Research export checksum, format or version mismatch.');
    return state(e.caseState);
  }
  return Object.freeze({ version: VERSION, schema: SCHEMA, gamma: GAMMA, presets: PRESETS.slice(), sequences: SEQUENCES.slice(), sources: SOURCE, assumptions, createCase, calibrate, design, acquire, process, analyze, uncertainty, proposeMeasurement, attachExperimental, importExperimental: attachExperimental, exportCase, validateImport, revealCase });
});
