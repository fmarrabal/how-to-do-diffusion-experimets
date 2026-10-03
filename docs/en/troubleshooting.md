# Troubleshooting the Bruker workshop tools

[Repository home](../../README.md) · [Step-by-step guide](bruker-step-by-step.md) · [References](../../references/README.md) · [Español](../es/solucion-de-problemas.md)

These are diagnostic steps, not instructions to bypass instrument safeguards. Keep original spectra, partial directories and logs. Do not start acquisition to see whether a failed setup fixes itself. Real acquisition and TopSpin 3.6.4 compatibility remain unvalidated; simulated tests do not change that boundary.

## The external generator does not start

- Run `python --version`; the generator requires Python 3.8 or later. Run commands from the repository root, using the `python/ramp_generator/` paths in the [guide](bruker-step-by-step.md).
- If `--gui` reports missing Tkinter, use a Python distribution with Tkinter or the CLI. The CLI does not need Tkinter.
- `--gui` is not combined with `--config` or `--out`. Run `python python/ramp_generator/generate_ramps.py --help` for the implemented options.
- An output directory that already exists is rejected even when empty. Choose a new directory; do not overwrite a previous plan.
- The gradient endpoint must be exactly reachable by the chosen step. Review start/stop/step, counts and non-overlapping EXPNO ranges; changing the end to fit a step still requires checking the probe's limits.

## TopSpin cannot find or execute the script

1. Confirm that the intended file is in `<TopSpin>/exp/stan/nmr/py/user/` for the **installation actually running**, or import it through `edpy → File → Import`.
2. Use the matching console command: `xpy dosy_prepare_ramps.py`, `xpy dosy_workshop.py` or `xpy dosy_workshop_v3.py`.
3. `dosy_prepare_ramps.py` comes from a generated plan. The other two come from their respective `dist/` directories. Do not execute an internal template/module or the expanded **NO_EJECUTAR** reference macro.
4. TopSpin uses its native Jython environment; do not try to solve a missing `TopCmds` error by installing an unrelated Python package. External Python runs the generator and simulated tests, not the instrument interface.
5. Installation permissions, unexpected directory links or an old dataset layout need the operator's review. The preparation engine supports the direct four-field `CURDATA` layout and rejects older user-field layouts rather than guessing paths. Do not remove those guards.

## The plan is blocked as an example or has incorrect times

`example_only=true` deliberately blocks TopSpin execution. Verify the pulse program and mapping, then regenerate an operational plan explicitly. In an edited JSON, set `example_only=false` and `delay_mapping_confirmed=true` only after that review. Existing generated scripts do not reread your edited configuration.

Both supplied configurations, including `config_tres_repeticiones.json`, are blocked examples. For inherited-time repetitions no new D20 mapping is introduced; the template and limits still require review before deliberately enabling a copy of the plan.

- GUI/native preparation dialogs: diffusion times in **ms**.
- CLI `--delay-s` and stored D20: **seconds**; 50 ms is 0.05 s, not 50 s.
- P30: **µs**; for the reviewed `stebpgp1s1d`, small δ is **2 × P30**.
- Blank D20 list: inherited-time repetitions, not separate Δ values.
- Use decimal points (`0.05`, `1.902`); a comma is a list separator in native dialogs, not a decimal separator.
- Ramp GPZ index is configurable; the reference calibration reader is **fixed to GPZ6**. Do not use it for another swept index by changing only the plan.

## A destination exists, or preparation stops part-way through

The tools refuse existing EXPNO and check for FID/SER/processed data after parameter copying. They intentionally do not resume or overwrite a prior acquisition.

Inspect the reported paths and `preparacion.json` or `execution.json` when available. Preserve the partial directories as evidence. Resolve dataset, parameter or command failures before choosing an entirely new range. Do not run simultaneous preparations, substitute `wrpa`/`WR` for `wraparam`, or delete original data to make a destination pass.

## No gradient constant G is proposed

The integrated series may still provide an empirical `b100`. Physical-G conversion needs the exact saved pulse-program and gradient-shape hashes documented in `python/sequence_model.json`, plus its sequence/nucleus/shape conditions. That file is a documented model with shape-squared factor 0.81, not an experimental probe calibration or default Dref. A missing source file or a different sequence disables the conversion deliberately.

Do not rename a pulse program or replace a shape file to force a match. Retain the empirical scale with its timing/probe scope, or obtain a separately reviewed model. If you independently have D measured using a known old G, use **Constante Bruker desde D medido** with those actual inputs, not a nominal hardware value.

## The integral or logarithmic calibration is rejected

Inspect the reported EXPNO, PROCNO, actual reference ppm bounds, phase, baseline, file completeness, stored processing parameters and signal-to-noise. This route requires positive finite **signed net integrals**, at least four distinct squared amplitudes and decreasing attenuation.

Do not take absolute values of noisy/negative integrals, assign an arbitrary positive floor, or discard points merely to maximise R². Changing the integration window requires a scientific reason and review of the same region across the entire ramp. Reprocess consistently in a documented processing copy, keeping the original FID/SER and previous processed result.

RG, NS, diffusion times, gradient shape and pertinent pulse/acquisition parameters must remain consistent within the series. Different Δ blocks need separate calibrations. Recorded phase/baseline variations can produce warnings even when structural processing settings match; inspect those spectra, not just the fitted line. The reader corrects stored `NC_proc` scaling; manual per-spectrum normalization would change the evidence.

## Temperature checks fail, or the fit looks deceptively good

Check TE for every experiment and the temperature associated with the supplied Dref. Stabilise the sample and use a documented Dref at the relevant conditions. Do not enlarge tolerances simply to make a calibration pass. TE metadata is not an independent measurement of actual sample temperature.

Dref = 1.902 × 10⁻⁹ m²/s for the cited HDO/D2O example is associated with 298.15 K. It must not be applied automatically at 293 K, to another solvent or to a polymer. No silent thermal correction is performed here.

R² and the slope's standard error describe the regression, not peak purity, absence of convection or full calibration uncertainty. Inspect residual structure, overlap, attenuation span, noise and reference applicability. If the last points are mostly noise, design a revised ramp rather than hiding them. An 8% first point is not I(0); the intercept is fitted freely.

## v3 does not start, or stops after ZG/EFP

The acquisition option is **Preparar, adquirir y analizar**, followed by the separate **Iniciar serie** confirmation. **Exportar plan** and **Preparar sin adquirir** never acquire. A range already prepared by a previous attempt cannot be reused automatically: arrange an operator-controlled manual procedure or choose new destinations for a new autorun attempt.

During an authorised run, v3 requires confirmed command completion (`CmdThread.getResult() == 0`) for ZG and EFP. `None`, a nonzero code, changed RF/RG/timing/phase settings or incomplete spectrum files stop the workflow. Do not change the code to treat an existing FID as success. Read `execution.json`, preserve acquired points and review your TopSpin version's API behaviour with the operator before repeating. The script does not diagnose hardware failures or tune/shim the probe.

## P1 nutation fails or gives an implausible P90

Use the reviewed 1D `zg` template and check fixed RF power, phase, D1, sample, channel and ppm window. The current P1 may be a 180° pulse, not P90. Set a justified P90 search interval and a sweep of at least nine distinct durations covering positive and negative signal and the first inversion, within the instrument's RF limits.

Do not run independent APK on each point or replace signed areas with absolute values. A boundary optimum is rejected instead of reported as a calibration. RF inhomogeneity, relaxation or off-resonance can invalidate the ideal sine model even with an attractive fit. A proposal does not update other samples' P1 or the global RF calibration.

## G/cm, G/mm and recalculated DOSY lists do not agree

Check the unit and the old constant actually used to obtain D measured. `1 G/mm = 10 G/cm`; `1 G/cm = 0.01 T/m`. The implemented proposal is `G_new = G_old * sqrt(D_measured / D_reference)`, not its reciprocal.

Only after reviewing the proposal should the operator edit `gradpar` and save with `setpre → File → Write`. If needed, `xau dosy restore` regenerates `difflist` in a documented **analysis copy**. Do not apply an extra reference/thermal factor silently or rewrite the historical list without recording the previous value.

## The external read-only calibration wrapper fails

Use `python python/calibrate_series.py --help`. It requires an existing dataset with processed 1D spectra, explicit EXPNO/ppm bounds, Dref, its reference temperature, reference name, solvent and source, plus your reviewed `--confirm-sequence-mapping`. It uses the same GPZ6-mapped core as the native assistant; it does not auto-align or correct drift/temperature to force a result.

`--out` must be a new directory **outside** the experimental dataset; do not put reports among the input spectra. If the self-contained bundle is absent, `python python/build_bundles.py` rebuilds it from public local sources without instrument access. The other integration, metadata, reference and temperature checks remain applicable. Never add a fictitious Dref or clear an input guard merely to obtain a report.

## Reproduce a software problem without hardware

From the repository root, the following run **simulated tests**, not acquisitions:

```console
python python/run_tests.py
```

The launcher runs the included simulated groups in `tests/ramp_generator/test_ramp_generator.py`, `tests/topspin_console/test_calibration.py`, `tests/topspin_console/test_console.py`, `tests/topspin_console/test_jython_bundle.py`, `tests/topspin_console_v3/test_autorun.py` and the public-package checks. It uses stubs rather than vendor `TopCmds`. It does not establish operational compatibility with your spectrometer. Use the public package's verification records for the results of its actual test run.

For a useful report, include tool/version or commit, exact action/command, TopSpin/Jython version, relevant pulse/gradient mapping and units, error text, the expected versus observed behaviour, a minimal non-sensitive configuration, and redacted plan/execution logs. Include input hashes when appropriate, but **do not publish raw research data, sample identities, private filesystem paths, credentials or licensed Bruker manuals/source files without permission**. Hardware-related failures belong first with the instrument operator.

[Return to the step-by-step guide](bruker-step-by-step.md) · [Repository home](../../README.md)
