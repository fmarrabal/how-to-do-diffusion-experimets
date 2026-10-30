/* DiffAtOnce: deterministic synthetic acquisition and reconstruction models.
 * SI in all calculations. UI values are converted at the model boundary.
 * These are deliberately idealised forward models, not executable SPEN/chirp
 * pulse programs or hardware calibrations. No experimental file is read.
 */
(function () {
  'use strict';
  const gamma1H = 2.6752218744e8, TAU = 2 * Math.PI;
  const caches = { ultrafast: new Map(), spen: new Map(), timeResolved: new Map() };
  const finite = (v, d) => Number.isFinite(Number(v)) ? Number(v) : d;
  const bound = (v, lo, hi, d) => Math.max(lo, Math.min(hi, finite(v, d)));
  function random(seed) { let a = seed >>> 0; return () => { a += 0x6D2B79F5; let t = a; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function normal(r) { return Math.sqrt(-2 * Math.log(Math.max(1e-12, r()))) * Math.cos(TAU * r()); }
  function freeze(value) { if (value && typeof value === 'object' && !Object.isFrozen(value)) { Object.values(value).forEach(freeze); Object.freeze(value); } return value; }
  function cached(name, p, calc) { const key = JSON.stringify(p), cache = caches[name]; if (!cache.has(key)) { if (cache.size >= 48) cache.delete(cache.keys().next().value); cache.set(key, freeze(calc())); } return cache.get(key); }
  function bPGSE(g, delta, Delta) {
    if (![g, delta, Delta].every(Number.isFinite) || delta <= 0 || Delta < delta) return NaN;
    return (gamma1H * g * delta) ** 2 * (Delta - delta / 3);
  }
  // Log-linear least squares with a fitted intercept. Positive points only;
  // the deterministic 1.5% signal threshold is exposed, not a noise estimator.
  function fitExponential(b, y) {
    if (!Array.isArray(b) || !Array.isArray(y) || b.length !== y.length) return { D: null, amplitude: null, rSquared: null, rmse: null, nUsed: 0 };
    const maximum = Math.max(0, ...y.filter(Number.isFinite)), cutoff = maximum * 0.015;
    const excludedNonpositive = y.filter(v => Number.isFinite(v) && v <= 0).length;
    const used = b.map((v, i) => [v, y[i]]).filter(v => Number.isFinite(v[0]) && Number.isFinite(v[1]) && v[1] > Math.max(1e-12, cutoff));
    if (used.length < 3) return { D: null, amplitude: null, rSquared: null, rmse: null, nUsed: used.length, cutoff };
    const x = used.map(v => v[0] * 1e-9), z = used.map(v => Math.log(v[1]));
    const mx = x.reduce((a, v) => a + v, 0) / x.length, mz = z.reduce((a, v) => a + v, 0) / z.length;
    const denominator = x.reduce((a, v) => a + (v - mx) ** 2, 0);
    if (denominator < 1e-16) return { D: null, amplitude: null, rSquared: null, rmse: null, nUsed: used.length, cutoff };
    const slope = x.reduce((a, v, i) => a + (v - mx) * (z[i] - mz), 0) / denominator;
    const rawSignedD = -slope * 1e-9, D = rawSignedD < 0 ? null : rawSignedD, amplitude = Math.exp(mz - slope * mx);
    const meanY = used.reduce((a, v) => a + v[1], 0) / used.length;
    const sse = used.reduce((a, v) => a + (v[1] - amplitude * Math.exp(-v[0] * rawSignedD)) ** 2, 0);
    const sst = used.reduce((a, v) => a + (v[1] - meanY) ** 2, 0);
    return { D, rawSignedD, amplitude, rSquared: sst > 1e-24 ? 1 - sse / sst : null, rmse: Math.sqrt(sse / used.length), nUsed: used.length, cutoff, excludedNonpositive, status: D === null ? 'nonphysical_negative_D' : excludedNonpositive ? 'partial_positive_signal' : 'ok' };
  }
  function dftComplex(re, im, inverse = false) {
    if (!Array.isArray(re) || !Array.isArray(im) || re.length !== im.length) throw new TypeError('Equal-length real and imaginary arrays are required.');
    const n = re.length, outRe = Array(n).fill(0), outIm = Array(n).fill(0), sign = inverse ? 1 : -1, scale = inverse && n ? 1 / n : 1;
    for (let k = 0; k < n; k++) for (let j = 0; j < n; j++) { const angle = sign * TAU * k * j / n, co = Math.cos(angle), si = Math.sin(angle); outRe[k] += (re[j] * co - im[j] * si) * scale; outIm[k] += (re[j] * si + im[j] * co) * scale; }
    return { re: outRe, im: outIm };
  }
  const bias = (fit, truth) => fit.D === null || !Number.isFinite(truth) || truth <= 0 ? null : (fit.D / truth - 1) * 100;
  function ultrafast(input = {}) {
    const p = { g: bound(input.g, 150, 650, 420), delta: bound(input.delta, .5, 3, 1.4), Delta: bound(input.Delta, 30, 200, 80), D: bound(input.D, .2, 2, .8), profile: bound(input.profile, 0, .7, .5), T2: bound(input.T2, 50, 500, 150), readout: bound(input.readout, 10, 150, 60), calibration: bound(input.calibration, .7, 1.3, 1.1), noise: bound(input.noise, 0, 3, 0) };
    return cached('ultrafast', p, () => {
      const g = p.g * 1e-3, deltaMax = p.delta * 1e-3, Delta = p.Delta * 1e-3, D = p.D * 1e-9, T2 = p.T2 * 1e-3, tRead = p.readout * 1e-3, r = random(74191), n = 36;
      const rows = Array.from({ length: n }, (_, i) => {
        const u = i / (n - 1), z = (u - .5) * .01;
        // A slice-selective ideal PGSE surrogate: both local rectangular
        // lobes have duration delta(z); their leading-edge separation is Delta.
        // A real chirp sequence requires b(z)=integral q(z,t)^2 dt instead.
        const delta = deltaMax * (.15 + .85 * u), bNominal = bPGSE(g, delta, Delta), bTrue = bPGSE(g * p.calibration, delta, Delta);
        // All reconstructed positions belong to the same ideal readout echo.
        // T2 changes reference/SNR globally, not an invented spatial TE ramp.
        const receiveProfile = 1 - p.profile * u, echoTime = 2 * deltaMax + tRead;
        const referenceTrue = receiveProfile * Math.exp(-echoTime / T2), signalTrue = referenceTrue * Math.exp(-bTrue * D);
        const reference = referenceTrue + p.noise * .01 * normal(r), signal = signalTrue + p.noise * .01 * normal(r);
        return { z_m: z, local_delta_s: delta, b_nominal_s_per_m2: bNominal, b_true_s_per_m2: bTrue, receive_profile: receiveProfile, echo_time_s: echoTime, reference, signal, normalized: reference > .05 ? signal / reference : null, truth: Math.exp(-bTrue * D) };
      });
      const bNominal = rows.map(v => v.b_nominal_s_per_m2), bTrue = rows.map(v => v.b_true_s_per_m2), normalized = rows.map(v => v.normalized);
      const rawFit = fitExponential(bNominal, rows.map(v => v.signal)), nominalFit = fitExponential(bNominal, normalized), calibratedFit = fitExponential(bTrue, normalized);
      return { params: p, paramsSI: { g_T_per_m: g, delta_max_s: deltaMax, Delta_s: Delta, D_m2_per_s: D, T2_s: T2, readout_s: tRead }, rows, rawFit, nominalFit, calibratedFit,
        diagnostics: { trueD: D, rawD: rawFit.D, nominalD: nominalFit.D, calibratedD: calibratedFit.D, rawBiasPercent: bias(rawFit, D), nominalBiasPercent: bias(nominalFit, D), calibratedBiasPercent: bias(calibratedFit, D), bMaximum: Math.max(...bTrue), calibrationFactorB: p.calibration ** 2, fitR2: calibratedFit.rSquared, pointsUsed: calibratedFit.nUsed } };
    });
  }
  function spen(input = {}) {
    const p = { g: bound(input.g, 150, 650, 420), delta: bound(input.delta, .5, 3, 1.4), Delta: bound(input.Delta, 30, 200, 80), D1: bound(input.D1, .15, 1, .45), D2: bound(input.D2, 1.1, 3, 1.4), fraction: bound(input.fraction, 0, 1, .62), oddPhase: bound(input.oddPhase, 0, 150, 65), profile: bound(input.profile, 0, .7, .35), frequency: bound(input.frequency, -220, 220, -80), noise: bound(input.noise, 0, 3, 0) };
    return cached('spen', p, () => {
      const nz = 24, nt = 64, dt = .0015625, D1 = p.D1 * 1e-9, D2 = p.D2 * 1e-9, g = p.g * 1e-3, deltaMax = p.delta * 1e-3, Delta = p.Delta * 1e-3, oddPhase = p.oddPhase * Math.PI / 180, r = random(91317);
      const z = Array.from({ length: nz }, (_, i) => (i / (nz - 1) - .5) * .01), b = z.map((v, i) => bPGSE(g, deltaMax * (.15 + .85 * i / (nz - 1)), Delta));
      const frequencies = Array.from({ length: nt }, (_, k) => (k - nt / 2) / (nt * dt));
      const selectedIndex = Math.max(0, Math.min(nt - 1, Math.round(p.frequency * nt * dt + nt / 2))), selectedFrequency = frequencies[selectedIndex];
      // Echo-center approximation: each EPSI row has one chemical-evolution
      // time. Within-echo chemical evolution, chirp offset shearing, eddy
      // currents and aliasing are not simulated. The raw row is nevertheless
      // a complex spatial Fourier acquisition, not a drawn target DOSY map.
      function acquire(reference) {
        const raw = [], epsiRows = [];
        for (let n = 0; n < nt; n++) {
          const ti = n * dt, mre = [], mim = [];
          for (let zi = 0; zi < nz; zi++) {
            const profile = 1 - p.profile * zi / (nz - 1), relaxation = Math.exp(-ti / .12), A = p.fraction * Math.exp(reference ? 0 : -b[zi] * D1), B = (1 - p.fraction) * Math.exp(reference ? 0 : -b[zi] * D2);
            mre.push(profile * relaxation * (A * Math.cos(TAU * -80 * ti) + B * Math.cos(TAU * 120 * ti)));
            mim.push(profile * relaxation * (A * Math.sin(TAU * -80 * ti) + B * Math.sin(TAU * 120 * ti)));
          }
          const kspace = dftComplex(mre, mim), row = { re: [], im: [] };
          for (let sample = 0; sample < nz; sample++) {
            const k = n % 2 ? nz - 1 - sample : sample, phase = n % 2 ? oddPhase : 0, co = Math.cos(phase), si = Math.sin(phase);
            const re = kspace.re[k] * co - kspace.im[k] * si + p.noise * .01 * Math.sqrt(nz) * normal(r), im = kspace.re[k] * si + kspace.im[k] * co + p.noise * .01 * Math.sqrt(nz) * normal(r);
            row.re.push(re); row.im.push(im);
            epsiRows.push({ echo: n, sample, time_read_s: ti, k_index: k, polarity: n % 2 ? -1 : 1, re, im });
          }
          raw.push(row);
        }
        return { raw, epsiRows };
      }
      const acquisition = acquire(false), referenceAcquisition = acquire(true);
      function reconstruct(raw, correct) {
        const spatial = raw.map((row, n) => {
          const re = Array(nz), im = Array(nz), phase = correct && n % 2 ? -oddPhase : 0, co = Math.cos(phase), si = Math.sin(phase);
          for (let sample = 0; sample < nz; sample++) { const k = correct && n % 2 ? nz - 1 - sample : sample; re[k] = row.re[sample] * co - row.im[sample] * si; im[k] = row.re[sample] * si + row.im[sample] * co; }
          return dftComplex(re, im, true);
        });
        return Array.from({ length: nz }, (_, zi) => {
          const spectrum = dftComplex(spatial.map(row => row.re[zi]), spatial.map(row => row.im[zi]));
          return { re: frequencies.map((f, k) => spectrum.re[(k + nt / 2) % nt]), im: frequencies.map((f, k) => spectrum.im[(k + nt / 2) % nt]) };
        });
      }
      const corrected = reconstruct(acquisition.raw, true), uncorrected = reconstruct(acquisition.raw, false), reference = reconstruct(referenceAcquisition.raw, true);
      const referenceNaive = reconstruct(referenceAcquisition.raw, false);
      const selected = z.map((value, zi) => {
        const ref = Math.hypot(reference[zi].re[selectedIndex], reference[zi].im[selectedIndex]), naiveRef = Math.hypot(referenceNaive[zi].re[selectedIndex], referenceNaive[zi].im[selectedIndex]);
        return { z_m: value, b_s_per_m2: b[zi], frequency_Hz: selectedFrequency, corrected: ref > .025 ? Math.hypot(corrected[zi].re[selectedIndex], corrected[zi].im[selectedIndex]) / ref : null, uncorrected: naiveRef > .025 ? Math.hypot(uncorrected[zi].re[selectedIndex], uncorrected[zi].im[selectedIndex]) / naiveRef : null, reference_magnitude: ref };
      });
      const correctedFit = fitExponential(b, selected.map(v => v.corrected)), uncorrectedFit = fitExponential(b, selected.map(v => v.uncorrected));
      const nearestPeak = Math.abs(selectedFrequency + 80) < Math.abs(selectedFrequency - 120) ? 0 : 1, peakFrequency = nearestPeak === 0 ? -80 : 120, selectedComponentPresent = nearestPeak === 0 ? p.fraction > 0 : p.fraction < 1, trueD = selectedComponentPresent ? nearestPeak === 0 ? D1 : D2 : null;
      const rows = [];
      for (let zi = 0; zi < nz; zi++) for (let k = 0; k < nt; k++) rows.push({ z_m: z[zi], b_s_per_m2: b[zi], frequency_Hz: frequencies[k], corrected_real: corrected[zi].re[k], corrected_imaginary: corrected[zi].im[k], uncorrected_real: uncorrected[zi].re[k], uncorrected_imaginary: uncorrected[zi].im[k], reference_real: reference[zi].re[k], reference_imaginary: reference[zi].im[k], selected_frequency_Hz: selectedFrequency });
      return { params: p, paramsSI: { g_T_per_m: g, delta_max_s: deltaMax, Delta_s: Delta, D1_m2_per_s: D1, D2_m2_per_s: D2, echo_spacing_s: dt, readout_span_s: (nt - 1) * dt }, rows, epsiRows: acquisition.epsiRows, z, b, frequencies, selectedIndex, corrected, uncorrected, reference, selected, correctedFit, uncorrectedFit,
        diagnostics: { selectedFrequency, nearestPeakFrequency: peakFrequency, selectedComponentPresent, trueD, correctedD: correctedFit.D, uncorrectedD: uncorrectedFit.D, correctedBiasPercent: bias(correctedFit, trueD), uncorrectedBiasPercent: bias(uncorrectedFit, trueD), fitR2: correctedFit.rSquared, offResonance: Math.abs(selectedFrequency - peakFrequency) > 20, pointsUsed: correctedFit.nUsed, spectralResolutionHz: 1 / (nt * dt), bMaximum: Math.max(...b) } };
    });
  }
  function averageA(rate, start, duration) { if (rate === 0) return 1; return Math.exp(-rate * start) * (-Math.expm1(-rate * duration)) / (rate * duration); }
  function timeResolved(input = {}) {
    const p = { D1: bound(input.D1, .15, 1, .45), D2: bound(input.D2, 1.1, 3, 1.4), rate: bound(input.rate, 0, .08, .025), tLab: bound(input.tLab, 0, 120, 20), pointTime: bound(input.pointTime, .2, 4, 2), snapshotTime: bound(input.snapshotTime, .05, 4, .5), frameStep: bound(input.frameStep, 1, 20, 5), order: Math.round(bound(input.order, 0, 2, 0)), Delta: bound(input.Delta, 30, 200, 80), readout: bound(input.readout, 10, 120, 40), noise: bound(input.noise, 0, 3, 0) };
    return cached('timeResolved', p, () => {
      const n = 16, D1 = p.D1 * 1e-9, D2 = p.D2 * 1e-9, Delta = p.Delta * 1e-3, tRead = p.readout * 1e-3, bMax = bPGSE(.42, .0014, Delta), b = Array.from({ length: n }, (_, i) => bMax * i / (n - 1));
      // Permutation is fixed, complete and deterministic; order changes the
      // covariance of process time and b. It does not freeze the chemistry.
      const permuted = [0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15], acquisitionOrder = p.order === 0 ? b.map((v, i) => i) : p.order === 1 ? b.map((v, i) => n - 1 - i) : permuted;
      const slowDuration = n * p.pointTime;
      // One continuous stream, repeated complete gradient permutations.
      // Overlapping frames share the very same acquired points and noise.
      // A requested window starts at the closest actually acquired point.
      const currentStartIndex = Math.round(p.tLab / p.pointTime), historyStartIndices = Array.from({ length: 15 }, (_, i) => Math.round(i * p.frameStep / p.pointTime));
      const streamLength = Math.max(currentStartIndex, ...historyStartIndices) + n, streamRandom = random(43872);
      const stream = Array.from({ length: streamLength }, (_, i) => {
        const bi = acquisitionOrder[i % n], start = i * p.pointTime, fractionA = averageA(p.rate, start, p.pointTime), fractionB = 1 - fractionA;
        return { stream_index: i, b_index: bi, b_s_per_m2: b[bi], sequential_start_t_lab_s: start, sequential_mid_t_lab_s: start + p.pointTime / 2, sequential_window_s: p.pointTime, fraction_A_sequential: fractionA, fraction_B_sequential: fractionB, sequential_A: fractionA * Math.exp(-b[bi] * D1) + p.noise * .01 * normal(streamRandom), sequential_B: fractionB * Math.exp(-b[bi] * D2) + p.noise * .01 * normal(streamRandom), Delta_s: Delta, t_read_s: tRead };
      });
      function frame(startIndex) {
        const start = startIndex * p.pointTime, r = random(91309 + startIndex * 937), snapshotA = averageA(p.rate, start, p.snapshotTime), snapshotB = 1 - snapshotA;
        const rows = stream.slice(startIndex, startIndex + n).map((point, ai) => ({ ...point, acquisition_index: ai, snapshot_start_t_lab_s: start, snapshot_window_s: p.snapshotTime, fraction_A_snapshot: snapshotA, fraction_B_snapshot: snapshotB, snapshot_A: snapshotA * Math.exp(-point.b_s_per_m2 * D1) + p.noise * .01 * normal(r), snapshot_B: snapshotB * Math.exp(-point.b_s_per_m2 * D2) + p.noise * .01 * normal(r) }));
        rows.sort((a, b) => a.b_index - b.b_index);
        const fitSlowA = fitExponential(b, rows.map(v => v.sequential_A)), fitSlowB = fitExponential(b, rows.map(v => v.sequential_B)), fitFastA = fitExponential(b, rows.map(v => v.snapshot_A)), fitFastB = fitExponential(b, rows.map(v => v.snapshot_B));
        return { start, startIndex, rows, fitSlowA, fitSlowB, fitFastA, fitFastB };
      }
      const current = frame(currentStartIndex), history = historyStartIndices.map(frame);
      return { params: p, paramsSI: { D1_m2_per_s: D1, D2_m2_per_s: D2, rate_per_s: p.rate, t_lab_requested_s: p.tLab, t_lab_effective_s: current.start, Delta_s: Delta, t_read_s: tRead, slow_window_s: slowDuration, snapshot_window_s: p.snapshotTime, frame_step_s: p.frameStep }, rows: current.rows, stream, current, history, acquisitionOrder, b,
        diagnostics: { trueD1: D1, trueD2: D2, sequentialD1: current.fitSlowA.D, sequentialD2: current.fitSlowB.D, snapshotD1: current.fitFastA.D, snapshotD2: current.fitFastB.D, sequentialBias1Percent: bias(current.fitSlowA, D1), sequentialBias2Percent: bias(current.fitSlowB, D2), snapshotBias1Percent: bias(current.fitFastA, D1), snapshotBias2Percent: bias(current.fitFastB, D2), slowWindowSec: slowDuration, snapshotWindowSec: p.snapshotTime, cadenceSec: p.frameStep, actualFrameStartSec: current.start, requestedFrameStartSec: p.tLab, overlappingSlowFrames: p.frameStep < slowDuration, fractionChangeSlow: Math.exp(-p.rate * current.start) * (1 - Math.exp(-p.rate * slowDuration)), bMaximum: bMax, DeltaSec: Delta, tReadSec: tRead, inconsistentTiming: p.pointTime < Delta + tRead || p.snapshotTime < Delta + tRead } };
    });
  }
  window.DiffusionModels = { gamma1H, bPGSE, fitExponential, dftComplex, ultrafast, spen, timeResolved };
})();
