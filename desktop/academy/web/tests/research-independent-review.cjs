'use strict';
// Cross-module scientific limits, not duplicates of each solver's unit tests.
const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const S = require('../spatial-encoding.js'), J = require('../research-journey.js'), P = require('../doctoral-pedagogy.js'), I = require('../doctoral-inquiry.js');
const checks = [];
function check(id, test) { try { test(); checks.push({ id, passed: true }); } catch (e) { checks.push({ id, passed: false, error: e.message }); } }
function near(a, b, tol) { assert.ok(Math.abs(a - b) <= tol, `${a} versus ${b}, tolerance ${tol}`); }
const program = [{ kind: 'evolve', durationMs: 2, gradientTm: .2 }, { kind: 'evolve', durationMs: 18, gradientTm: 0 }, { kind: 'evolve', durationMs: 2, gradientTm: -.2 }];
const options = { lengthMm: .5, diffusionM2s: 2e-9, relaxation: false, timeStepUs: 5, coilVariation: 0 };
const b = (S.GAMMA * .2 * .002) ** 2 * (.020 - .002 / 3), analytic = Math.exp(-2e-9 * b);
const solutions = [64, 128, 256].map(points => S.propagate([1, 0, 0], program, { ...options, points }));
function interior(result, key = 'mx') { const ii = result.zMm.map((z, i) => Math.abs(z) < .2 ? i : -1).filter(i => i >= 0); return ii.reduce((a, i) => a + result[key][i], 0) / ii.length; }
check('all-four-engines-share-angular-gamma-SI', () => { near(J.gamma, S.GAMMA, 1e-7); near(P.GAMMA, S.GAMMA, 1e-7); near(I.gamma, S.GAMMA, 1e-7); });
check('saved-TopSpin-unit-adapter-and-journey-have-identical-explicit-rectangular-b', () => {
  const saved = P.nominalBrukerDOSY({ Gamma: S.GAMMA / (2 * Math.PI * 1e4), Glen: 2, Gdist: 20 - 2 / 3 }, [0, 20]);
  const designed = J.design(J.calibrate(J.createCase()), { gradientMax: .2, deltaMs: 2, bigDeltaMs: 20 });
  near(saved.bs[1], designed.design.bNominal.at(-1), 1e-6); near(saved.bs[1], b, 1e-6); assert.equal(saved.absoluteCalibrationValidated, false);
});
check('Bloch-Torrey-bipolar-echo-tends-to-free-diffusion-attenuation', () => {
  const errors = solutions.map(r => Math.abs(interior(r) - analytic)); assert.ok(errors[2] < .0011); assert.ok(errors[1] < errors[0] / 3.8); assert.ok(errors[2] < errors[1] / 3.8);
  for (const r of solutions) assert.ok(Math.abs(interior(r, 'my')) < 2e-6);
});
check('angular-rotation-sign-does-not-change-free-diffusion-echo-magnitude', () => {
  const mirrored = S.propagate([1, 0, 0], program.map(s => ({ ...s, gradientTm: -s.gradientTm })), { ...options, points: 128 });
  near(interior(mirrored), interior(solutions[1]), 1e-11); near(interior(mirrored, 'my'), -interior(solutions[1], 'my'), 1e-11);
});
check('T2-attenuation-commutes-with-the-whole-diffusing-gradient-echo', () => {
  const r = S.propagate([1, 0, 0], program, { ...options, points: 128, relaxation: true, T1Seconds: .3, T2Seconds: .1 });
  near(interior(r), interior(solutions[1]) * Math.exp(-.022 / .1), 1e-10);
});
check('receiver-phase-can-null-the-real-echo-without-changing-diffusion', () => {
  const r = S.propagate([1, 0, 0], program, { ...options, points: 128, offResonanceHz: 1 / (4 * .022) });
  near(interior(r), 0, 1e-8); near(interior(r, 'my'), interior(solutions[1]), 1e-8);
});
check('spatial-solver-data-fit-recovers-D-with-declared-discretization-error', () => {
  const gs = [0, .05, .1, .15, .2], bs = [], ys = [];
  for (const g of gs) {
    const pp = program.map(s => ({ ...s, gradientTm: s.gradientTm === 0 ? 0 : Math.sign(s.gradientTm) * g }));
    const r = S.propagate([1, 0, 0], pp, { ...options, points: 256 });
    bs.push((S.GAMMA * g * .002) ** 2 * (.020 - .002 / 3)); ys.push(interior(r));
  }
  const f = I.fitMono(bs, ys); assert.ok(Math.abs(f.D / options.diffusionM2s - 1) < .006); assert.ok(f.rms < .001);
});
check('nominal-spatial-decoding-has-the-expected-chemical-offset-bias', () => {
  // Negligible signal at both field-of-view boundaries is required here;
  // otherwise a one-bin frequency shift wraps finite Gaussian tails.
  const n = 129, L = .01, G = .01, hz = S.GAMMA / (2 * Math.PI), dt = 1 / (hz * G * L), df = 1 / (n * dt), zero = Array(n).fill(0), density = Array.from({ length: n }, (_, i) => Math.exp(-.5 * (((i - 64) * L / n) / .0005) ** 2));
  const run = off => S.propagate({ mx: density, my: zero, mz: zero }, [{ kind: 'readout', durationMs: (n - 1) * dt * 1000, samples: n, gradientTm: G }], { points: n, lengthMm: 10, diffusionM2s: 0, relaxation: false, timeStepUs: 20, coilVariation: 0, offResonanceHz: off });
  const meanZ = r => { const spec = r.readout.spectrum, total = spec.magnitude.reduce((a, v) => a + v, 0); return spec.magnitude.reduce((a, v, i) => a + v * spec.positionMm[i], 0) / total; };
  const a = run(0), shifted = run(df);
  near(meanZ(a), 0, 1e-10); near(meanZ(shifted), 1000 * df / (hz * G), 1e-10);
  const spec = a.readout.spectrum; for (let i = 0; i < n; i++) near(spec.magnitude[i], density[i] / n, 1e-12);
});
check('custom-program-summary-does-not-invent-an-RF-chirp', () => {
  const r = S.propagate([1, 0, 0], [{ kind: 'evolve', durationMs: 1, gradientTm: .01 }], { points: 16, diffusionM2s: 0, relaxation: false });
  assert.equal(r.metrics.rfSweepBandwidthHz, 0); assert.equal(r.metrics.encodingFrequencySpanHz, 0);
});
check('temporal-aliasing-diagnostic-includes-the-chemical-offset', () => {
  const r = S.propagate([1, 0, 0], [{ kind: 'readout', durationMs: 2, gradientTm: 0, samples: 64 }], { points: 16, diffusionM2s: 0, relaxation: false, offResonanceHz: 100000 });
  assert.ok(100000 > r.metrics.readoutBandwidthHz / 2); assert.ok(r.diagnostics.warnings.some(v => v.id === 'temporal-aliasing'));
});
check('a-good-reserved-prediction-does-not-validate-a-shared-b-calibration', () => {
  let s = J.createCase({ seed: 42, preset: 'gradient' }); s = J.calibrate(s, { nullPulseUs: s.pilots.firstNullUs, gradientScale: 1 }); s = J.design(s, { points: 16, scans: 4 }); s = J.analyze(J.process(J.acquire(s, { noise: 0 })));
  const truth = J.revealCase(s), observed = J.proposeMeasurement(s, { observe: true, noise: 0, prediction: 'The common nominal b scale predicts another internally consistent biased decay.' });
  assert.ok(Math.abs(s.analysis.D_m2_s / truth.components[0].D - 1) > .05); assert.equal(observed.measurement.heldoutRanking[0].id, 'mono'); assert.ok(observed.measurement.heldoutRanking[0].residualRms < 1e-7);
  const interval = J.uncertainty(s, { samples: 60, gradientRelativeSd: .001, temperatureSdK: 0, processingRelativeSd: 0, noiseRelativeSd: 0, sequenceRelativeSd: 0 }).uncertainty;
  assert.ok(truth.components[0].D < interval.interval95[0] || truth.components[0].D > interval.interval95[1]); assert.equal(interval.coverageValidated, false);
});
check('CSV-contract-retains-signed-observations-without-inventing-provenance', () => {
  const csv = 'b_s_m2,signal\n0,1\n200000000,0.8\n700000000,0.4\n1200000000,0.12\n2000000000,-0.01';
  const parsed = P.parseCSV(csv, 'attenuation'); assert.ok(Array.isArray(parsed.rows));
  const s = J.attachExperimental(J.createCase(), { id: 'local-cross-check', source: 'user-local-csv-not-verified', license: 'local user-supplied; permission not independently verified', bs: parsed.rows.map(r => r.b_s_m2), areas: parsed.rows.map(r => r.signal), metadata: { provenanceVerified: false } });
  assert.equal(s.acquisition.areas.at(-1), -.01); const f = P.fitAttenuation(s.acquisition.bs, s.acquisition.areas, { method: 'signal', bootstrap: 0 }); assert.equal(f.retainedNonpositivePoints, 1);
  assert.equal(J.revealCase(s), null); assert.equal(s.acquisition.originalProvenance.metadata.provenanceVerified, false);
});
check('missing-b-prevents-experimental-import-and-D-inference', () => assert.throws(() => J.attachExperimental(J.createCase(), { id: 'missing-b', source: 'public metadata', license: 'CC BY 4.0', bs: [], areas: [1, .8, .5, .3] }), RangeError));
const sources = ['research-journey.js', 'spatial-encoding.js', 'doctoral-pedagogy.js', 'doctoral-inquiry.js'].map(file => ({ file, sha256: crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname, '..', file))).digest('hex') }));
const report = { version: '1.3.0', passed: checks.every(c => c.passed), checks, sources,
  computedEvidence: { b_s_m2: b, analyticFreeDiffusionEcho: analytic, spatialRefinement: solutions.map(r => ({ points: r.options.points, interiorEcho: interior(r), absoluteError: Math.abs(interior(r) - analytic) })) },
  scope: 'Independent cross-module analytic/free-diffusion, phase, unit conversion, decoder and inference checks. The reflecting-wall interior comparison has explicit finite-space error. No hardware calibration, chemical identification or educational-validation claim.' };
const output = process.argv[2]; if (output) { fs.mkdirSync(path.dirname(output), { recursive: true }); fs.writeFileSync(output, JSON.stringify(report, null, 2)); }
console.log(JSON.stringify({ passed: report.passed, checks: checks.length, failures: checks.filter(c => !c.passed), output: output || null })); if (!report.passed) process.exitCode = 1;
