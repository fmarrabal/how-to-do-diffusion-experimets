# Bruker DOSY: step-by-step preparation and calibration

[Repository home](../../README.md) · [Troubleshooting](troubleshooting.md) · [References](../../references/README.md) · [Español](../es/bruker-paso-a-paso.md)

This guide accompanies the public, portable edition of the workshop scripts. It is derived from the original workshop implementation; public packaging may remove private provenance paths. Consult the public package's provenance and verification records rather than assuming its bundled files are byte-identical to an earlier private copy.

## 1. Choose the correct route

| Tool | Where it runs | What it can do | Starts acquisition? |
|---|---|---|---|
| `python/ramp_generator/` | External Python 3.8 or later | GUI/CLI plan generation and a TopSpin preparation script | No |
| `python/topspin_console/dist/dosy_workshop.py` | TopSpin's built-in Jython | Prepare 1D ramps; analyse an already acquired reference series; propose a gradient constant | No |
| `python/topspin_console_v3/dist/dosy_workshop_v3.py` | TopSpin's built-in Jython | The preceding assistant plus P1 nutation and reference-ramp acquisition workflows | Only after explicitly choosing acquisition and confirming it |

The bundled dialogs currently use Spanish captions. This English guide gives their literal captions where needed. These tools are not a replacement for your instrument's operating procedure or for training by its operator.

Compatibility is based on reviewed Bruker sources and simulated API tests, including the Jython 2.7.2 environment supplied with TopSpin 3.8.0. **A real acquisition and operation on TopSpin 3.6.4 have not been validated.** Do not interpret successful offline tests as an instrument qualification.

## 2. Review the experiment before creating any copies

Open a valid **1D template** belonging to the intended dataset. Review these items with the instrument operator:

- Sample identity, solvent, nucleus, probe, tuning/matching, lock, shimming and temperature stability.
- Pulse program, RF power, pulse durations, gradient shape/amplitude limits, relaxation delay D1, NS, DS and receiver gain RG.
- Acquisition and processing parameters, phase, baseline and the spectral region of the reference.
- Template EXPNO/PROCNO, destination dataset and **unused** destination EXPNO ranges.

Do not transfer a reference's ppm window or another sample's peak indices without inspecting this sample. Do not run two preparations against the same destination numbers.

The following mapping is specific to the reviewed `stebpgp1s1d` example, not a universal NMR convention:

| Parameter | Meaning in this example | Unit |
|---|---|---|
| D20 | Large diffusion time Δ | seconds |
| P30 | Duration of each bipolar lobe; small δ = 2 × P30 | microseconds |
| GPZ6 | Variable diffusion-gradient amplitude | percent of the calibrated maximum |
| GPZ7 | Spoiler gradient, not the swept diffusion gradient | percent |
| GPNAM6 | Diffusion-gradient shape | shape identifier |
| TE | Recorded instrument temperature; not independent sample thermometry | kelvin |

Inspect your actual pulse program before confirming a D/P mapping. GPZ percentages are not physical gradients or b-values. A 96% endpoint is an editable workshop example, **not** a safe or recommended universal limit.

## 3. Generate a plan outside TopSpin: GUI or CLI

Run these commands from the repository root. The external generator uses Python's standard library; Tkinter is needed only for the GUI.

### GUI

```console
python python/ramp_generator/generate_ramps.py --gui
```

Alternatively, open `python/ramp_generator/abrir_generador.pyw` with Python on Windows.

1. Set template EXPNO/PROCNO, ramp count, first destination, stride and GPZ range/step.
2. Choose diffusion times for your experiment. The GUI accepts milliseconds and converts them to seconds.
3. Use **Previsualizar** to inspect every row without writing a bundle.
4. The initial three-Δ configuration is marked **Es un ejemplo**. Keep that flag while exploring. Remove it only after reviewing the sequence mapping and values; confirm the mapping explicitly.
5. Use **Generar** and choose an output directory that does not already exist.

The GUI preserves the template's P30. A blank diffusion-time list produces repeated ramps with inherited D20; these are repetitions, not different diffusion times.

### CLI: generate a blocked example first

```console
python python/ramp_generator/generate_ramps.py --config python/ramp_generator/config_ejemplo_tres_Delta.json --out my_example
```

This produces an example that cannot be executed in TopSpin while `example_only=true`. With 8–96% in 4% increments there are 23 points per ramp: 100–122, 200–222 and 300–322, or 69 points in total. The example times are 0.05, 0.10 and 0.15 s. They are not prescribed for your sample.

After checking the pulse program and choosing appropriate times and limits, the following shows the **syntax** of an operational plan; replace the example values before use:

```console
python python/ramp_generator/generate_ramps.py --out my_reviewed_ramps --ramps 3 --template-expno 10 --start-expno 100 --stride 100 --gradient-index 6 --gradient-start 8 --gradient-stop 96 --gradient-step 4 --delay-parameter D20 --delay-s 0.05 0.10 0.15 --pulse-program stebpgp1s1d --confirm-delay-mapping --ds 16
```

CLI `--delay-s` uses **seconds**, not milliseconds. Use a decimal point in numerical fields (`0.05`, `1.902`); commas separate list entries in the native dialogs. To generate three repetitions without changing the inherited D20/P30:

```console
python python/ramp_generator/generate_ramps.py --config python/ramp_generator/config_tres_repeticiones.json --out my_repetitions
```

**Both supplied JSON configurations are blocked examples**, including the repetitions configuration. After reviewing a copy of the configuration, set `example_only=false` only when you intend to create an operational plan; regenerate into a new directory. Repeating inherited timings still requires checking the actual template and instrument limits.

The CLI can explicitly set a pulse parameter with `--pulse-parameter P30 --pulse-us VALUE --confirm-pulse-mapping`; supply your reviewed numeric `VALUE` and expected pulse program. Do not equate P30 with δ without inspecting the sequence. The GUI has no equivalent P30-editing action.

Each new bundle contains `plan.csv`, `plan.json`, `config.json`, `dosy_prepare_ramps.py`, a macro calling that script, and short instructions. The expanded reference macro is labelled **NO_EJECUTAR** and lacks the Python safeguards. Editing a JSON does not change a generated script: regenerate into a new directory and install the new script.

## 4. Transfer the generated preparation to TopSpin

1. Keep an unchanged copy of the plan and configuration.
2. Copy the generated `dosy_prepare_ramps.py` into:

   ```text
   <TopSpin>/exp/stan/nmr/py/user/
   ```

   You can instead use `edpy → File → Import`.
3. Open the correct dataset and review its template again. An optional `expected_dataset_name` in the configuration restricts the intended dataset.
4. In the TopSpin console, run:

   ```text
   xpy dosy_prepare_ramps.py
   ```

5. Check the first and last points, times, DS and RG against `plan.csv` before any acquisition.

The script checks all destinations before copying and checks each one again before use. It uses `wraparam` to copy **parameters**, not `wrpa` or `WR` to copy acquired data. It checks that the new destinations do not contain FID/SER or processed signals, verifies the parameter writes and restores the original dataset view. It does not execute `zg`, `multizg` or `rga`.

If preparation fails part-way through, the partial directories remain. Do not delete or reuse them blindly: record the failure, inspect the cause and choose new unused destinations for another attempt.

## 5. Install and open the native assistant

Copy `python/topspin_console/dist/dosy_workshop.py` into the same TopSpin `py/user` directory, or import it with `edpy`. This file is self-contained; no external Python installation is required inside TopSpin.

On Windows, the optional installer makes this copy and verifies its SHA-256. Run it from the repository root, replacing the placeholder with the real installation directory:

```powershell
& .\python\topspin_console\install_topspin_console.ps1 -TopSpinHome '<YOUR_TOPSPIN_INSTALLATION>'
```

It does not launch TopSpin. An identical existing script is kept; a different existing script is backed up before replacement. If permissions or path checks prevent installation, ask the operator to use the approved manual import procedure.

Open a template in TopSpin and enter:

```text
xpy dosy_workshop.py
```

Choose **Preparar rampas** to create the plan directly in native dialogs. Review the GPZ index and range, unused destinations, DS, expected pulse program and diffusion times. This dialog takes times in **milliseconds**. Leave the time list blank for repeated inherited timings. Inspect the entire plan, then choose **Exportar plan solamente** or **Crear experimentos**. Neither choice starts acquisition.

This assistant's calibration reader is specifically mapped to **GPZ6**, D20, P30, D16 and GPNAM6. Changing the ramp-generation GPZ index does not change the calibration reader. A different sequence requires a separately reviewed mapping/implementation.

## 6. Calibrate from the integrated reference series

Acquire the reference series using an approved procedure, then process each spectrum consistently. The basic assistant analyses those existing files read-only.

1. Inspect the reference identity, solvent, concentration/conditions and suitability of its diffusion reference. Select its actual, isolated ppm region in this sample.
2. Open an experiment in that dataset and select **Calibrar con serie 1D**.
3. Enter EXPNO as a range such as `100-122` or a list, the PROCNO and ppm limits. Include only one constant-timing ramp.
4. Enter the reference identity, solvent and source; Dref in **10⁻⁹ m²/s** at the explicitly entered reference temperature in K. Review the configurable TE tolerances.
5. Inspect every spectrum, the signed integrals, fitted line, residuals, metadata and warnings before accepting a candidate calibration.

For each spectrum the reader restores stored intensity scaling: int32 data use `2**NC_proc`; float64 data are read directly. It integrates by a signed trapezoidal rule with interpolated boundaries, not absolute values. This log-calibration route requires positive finite net integrals and at least four distinct squared gradient amplitudes; it does not silently discard invalid points to improve R².

The fitted model is:

```text
x = (GPZ6 / 100)^2
ln(I / Imax) = intercept - s*x, with s > 0
b100 = s / (Dref * 10^-9)       [s/m^2]
b(g) = b100 * (GPZ6 / 100)^2
```

The intercept is free. The first acquired point at 8% is **not** a zero-gradient measurement. Imax is a normalization scale; the model's I(0) is extrapolated. A good R² does not prove reference purity, sufficient signal-to-noise or absence of convection.

The output directory contains `calibracion.json`, `atenuacion_residuos.csv` and `informe.html`, with input hashes and scope. `b100` is an experimental scale for the same probe, sequence, shape and timing conditions. **Each Δ needs its own scale**, unless transfer is supported by an independently reviewed pulse-sequence model. Do not pool 50/100/150 ms as one constant-timing calibration.

TE is instrument metadata, not independent sample temperature. The software checks the explicitly configured temperature tolerances; it does not infer or silently apply a temperature correction. The literal HDO/D2O reference D = 1.902 × 10⁻⁹ m²/s belongs to 298.15 K, not every temperature or solvent. **The public package does not contain an experimental TBO probe-calibration profile or a default reference D.** It includes only the documented sequence model described in section 7; you must supply a suitable reference and its temperature.

### Alternative: analyse existing spectra with external Python

The read-only offline wrapper uses the **same calibration core** as the TopSpin assistant; it is not a new scientific algorithm. It needs Python 3.8 or later and the standard library, not TopSpin or its hardware API. First inspect its implemented options:

```console
python python/calibrate_series.py --help
```

The following is a command template, **not a ready-to-run calibration**. Replace every uppercase placeholder with the reviewed dataset, actual ppm limits, positive numeric Dref at your stated reference temperature, and documented identity/source. The output directory must be new and **outside** the experimental input directory:

```console
python python/calibrate_series.py --dataset "DATASET_DIRECTORY" --expnos "100-122" --procno 1 --ppm-low PPM_LOW --ppm-high PPM_HIGH --dref DREF --reference-temperature-k TREF --reference-name "REFERENCE_NAME" --solvent "SOLVENT" --reference-source "DOI_OR_DOCUMENTED_SOURCE" --confirm-sequence-mapping --out "NEW_REPORT_DIRECTORY_OUTSIDE_DATASET"
```

Use `--confirm-sequence-mapping` only after verifying GPZ6, D20, P30, D16 and GPNAM6 against the saved pulse program. Temperature is mandatory with Dref; no value is guessed. The explicit `--max-temperature-span-k` and `--max-reference-temperature-difference-k` options control the same checks as the native workflow (both default to 0.5 K); do not relax them simply to obtain a fit.

The wrapper writes `calibracion.json`, `atenuacion_residuos.csv` and `informe.html` in the new directory. It does not import vendor `TopCmds`, connect to the instrument, acquire, automatically align spectra, infer drift corrections, overwrite input spectra or apply a proposal. Review the output using the same spectral/reference/residual checks as above.

## 7. Propose and review the physical gradient constant G

There are two distinct routes; do not mix their inputs.

### A. Conditional proposal from the integrated series

A physical G proposal is available only when the saved `pulseprogram` and `gpnam6` bytes match the identities recorded in [`python/sequence_model.json`](../../python/sequence_model.json) and the required `stebpgp1s1d` / `SMSQ10.100` / ¹H conditions are met. This public file contains a sequence-model identity, source hashes, an expression and the squared shape factor 0.81, **not an experimental probe calibration**. The **Ver modelo de secuencia** menu opens that model, not a private calibration profile.

For the exact documented model only:

```text
delta = 2 * P30 * 10^-6                 [s, P30 entered in microseconds]
t_effective = D20 - 0.32525*delta - D16/2
b100 = (gamma * Gmax * delta)^2 * 0.81 * t_effective
gamma = 267.52218744 * 10^6             [rad/s/T, 1H]
Gmax = sqrt(b100 / ((gamma*delta)^2 * 0.81 * t_effective))   [T/m]
```

The effective time must be positive. This is the retained, sequence-specific model, not a universal Stejskal–Tanner equation or a new validated algorithm. For different source bytes, sequences or shapes the empirical b-scale is retained **without inventing G**. Exact source matching is necessary for this route, not proof of instrument or model validation.

### B. Proposal from D measured with a known previous G

Select **Constante Bruker desde D medido**. Enter the old G actually used in the D calculation, its unit, D measured, D reference at the applicable temperature, and reference identity/solvent/source:

```text
G_new = G_old * sqrt(D_measured / D_reference)
```

Both D values must refer to the same conditions and coherent sequence/shape model. Do not substitute a nominal hardware maximum for the constant actually used.

| Gradient unit | Conversion |
|---|---|
| 1 G/cm | 0.01 T/m |
| 1 G/mm | 0.1 T/m = 10 G/cm |

The proposal is saved in `constante_propuesta.json` for route B; route A records it in `calibracion.json`. Neither route writes the global instrument calibration automatically. After review with the operator, use **`gradpar`** (or `setpre → Edit → Gradient parameters`) and save the probe configuration through **`setpre → File → Write`**. The quoted uncertainty covers regression only, not the reference, temperature or sequence-model uncertainty.

If an existing DOSY gradient list was generated using a different G, `xau dosy restore` can regenerate `difflist`. Do that in a documented **analysis copy**, preserving the original data and original list.

## 8. Optional v3: preparation versus acquisition

Install `python/topspin_console_v3/dist/dosy_workshop_v3.py` by the same copy/import method and open:

```text
xpy dosy_workshop_v3.py
```

The previous assistant remains accessible through **Asistente anterior: rampas y analisis**. v3 offers **Calibrar P1: barrido de nutacion** and **Calibrar DOSY: adquirir rampa del patron**.

Start by choosing **Exportar plan** or **Preparar sin adquirir**. Before selecting **Preparar, adquirir y analizar**, obtain the operator's approval of the sample, probe, RF limits, sweep range, relaxation, RG, phase, temperature and unused destinations. A second dialog requires **Iniciar serie**; otherwise the workflow returns without acquiring.

For each authorised point, v3 rechecks the preserved parameters, waits for `ZG`, waits for `EFP`, then reads the processed spectrum. It requires `CmdThread.getResult()` to equal 0 for both commands. A missing/ambiguous status, changed parameters or incomplete data stops the series; existence of a FID alone is not proof of successful completion. `execution.json` records the steps and partial results are retained. The script does not resume an earlier run: a new attempt requires unused EXPNO. A previously prepared range cannot be silently reused by the autorun route.

P1 nutation requires a reviewed 1D `zg` template, fixed RF power and phase, at least nine distinct pulse durations, positive and negative signed areas, and a sweep covering the rise and first inversion. Do not run APK independently on each point. The fit is `I(P1) = A*sin(pi*P1/(2*P90)) + offset` within explicit bounds; a boundary optimum is rejected. The current P1 is not assumed to be P90. Proposed P90/P180 apply only to the recorded power, sample, channel and conditions; v3 does not tune, shim, choose RF power or measure T1 automatically.

The DOSY autorun varies GPZ6 at fixed timing and uses the same integral calibration described above. v3 never writes a global gradient calibration, applies P1 to other samples or changes the documented sequence model. Review its outputs before any manual adoption.

## 9. Keep evidence and understand the alternative Bruker route

Retain the original spectra, template, plan/configuration, processing choices, reference source and temperature, input hashes, residuals, output reports, operator's decision and any version-specific command failure. Keep acquisition, calibration and later analysis as separately documented steps.

The standard Bruker AU command `xau dosy 8 96 23 l n` prepares a gradient list for an appropriate **pseudo-2D** dataset. It is not equivalent to this generator's 69 separate 1D EXPNO, does not acquire by itself and does not measure a diffusion reference. Consult the correct pulse program and Bruker documentation before choosing that alternative.

Primary reading: the [repository's reference index](../../references/README.md) links the complete workshop bibliography. [Bruker TopSpin Python Interface](https://www.bruker.com/en/products-and-solutions/mr/nmr-software/topspin/topspin-python-interface.html) distinguishes built-in Jython from the later external Python API. The [Bruker DOSY tutorial](https://2210pc.chem.uic.edu/nmr/downloads/dosy_ts13.pdf), particularly the gradient-calibration discussion, supports the distinction between calibration and preparing a gradient list. The installed Bruker Python, acquisition/processing, diffusion and data-format manuals and actual pulse-program source remain the reference for your instrument version; they are not redistributed here.

[Continue to troubleshooting](troubleshooting.md) · [Repository home](../../README.md)
