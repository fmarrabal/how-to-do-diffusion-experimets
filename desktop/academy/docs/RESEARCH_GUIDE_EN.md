# DiffAtOnce Academy 1.3 - Research guide

WPF and web editions. This guide supplements the original course and doctoral manual.

[Academy](https://diffatonce.com/en/academy)

## How to learn with this version

Turn a diffusion question into a conclusion proportional to the evidence.

1. Open Research in Academy web or choose Research studio in WPF, then select ES/EN. Both editions use the same interface and numerical engines.
2. Follow the twelve stages. Before an action, enter a prediction and reason in the help panel.
3. Use Doctoral, Derivations and Animations for deeper study, then return to the same case.
4. Export the investigation after each session. Then practise with another seed without consulting the worked example.

The seven extensions connect the sample, uncertainty, real data, competencies, control design, spatial encoding and tutoring/review.

**Check:** At the end you should explain what was measured, why the equation applies, which biases remain and which control could refute your claim.

**Limit:** Completing screens or passing software checks does not establish mastery or validate an experiment.

## What travels with the same sample

Distinguish acquired data, decisions, assumptions and simulation truth.

1. The seed fixes a reproducible synthetic sample; it does not identify a real molecule.
2. Calibration, design, complex series, processing and fitting stay linked to the sample identity and history.
3. After changing an earlier decision, review and recalculate later stages. An earlier result does not establish the new design.
4. When public or CSV integrals are attached, evidence is labelled experimental/imported and provenance remains required.

Internal units are SI: D in m²/s, b in s/m² and gradient in T/m. The interface displays pulses in µs and sequence times in ms.

**Check:** Check identity, units and processing state before comparing results.

**Limit:** Experimental originals are unchanged. Virtual calibration does not automatically recalibrate imported data or the spectrometer.

## 01 - The question

State a hypothesis and a result that could contradict it.

[View the actual capture in the PDF manual](RESEARCH_MANUAL_EN.pdf)

1. Select Hidden difficulty and Reproducible identity; use Create another case only to start a different sample.
2. Start with Isolated signal, then try Gradient calibration, Convection, Time drift, Overlap or Combined faults.
3. Write a concrete question: for example, whether a D difference might follow ramp order rather than only two species.
4. Record predictions for each hypothesis before acquiring.

A cause is not established by choosing a word. Decisions and controls must support the argument.

**Check:** Your question includes a measurable observation, an alternative and a possible control.

**Limit:** Choosing a preset reveals the problem family. For evaluation without that cue, use instructor-reserved cases/questions; guided practice is not a fully blind assessment.

## 02 - Calibrate before measuring

Separate RF calibration, gradient scale and standard conditions.

[View the actual capture in the PDF manual](RESEARCH_MANUAL_EN.pdf)

1. Inspect the signed nutation curve. Identify the first 180° null using the preceding maximum and sign reversal.
2. Enter P90=P180/2 at constant power and conditions. A 360° null is divided by four; a null alone does not establish its order.
3. Fit the standard decay against nominal b; for one common scale g_actual=s·g_nominal use s=√(D_nominal/D_ref).
4. Check standard and reference temperatures, then press Apply calibration to case.

With nominal b, a gradient-scale error enters D quadratically. More scans do not remove this bias.

**Check:** Justify the chosen null, reference D, temperature and waveform covered by calibration.

**Limit:** P90 must be checked for the appropriate sample and power. p30, d20 and d5 require the actual pulse program; no universal translation exists.

## 03 - Design an informative measurement

Choose an attenuation window and controls within a budget.

1. Choose Spin echo, Stimulated echo, LED or Double stimulated and explain why.
2. Set δ, Δ, d5/LED, maximum gradient, levels, NS, replicates and ramp order.
3. Press Check design and budget; inspect duration, maximum b and restrictions before acquiring.
4. Predict the effect of longer Δ or reverse/interleaved order. Change one variable at a time for causal comparisons.

More weighting can improve contrast while losing signal. LED adds time; losses and compensation depend on sequence.

**Check:** You can explain the role of each level and the part of the budget used to control errors.

**Limit:** Timing is an ideal teaching model. Check the actual program and instrument limits before transferring a recipe to the laboratory.

## 04 - Acquire the same sample

Connect the design to a complex series and acquisition order.

1. After calibration and design, press Acquire virtual series.
2. Inspect the FID and acquisition count; retain sample identity and seed.
3. Compare a replicate with reversed/interleaved acquisition. Describe the expected change under drift.
4. Export the first investigation before starting another seed.

Synthetic data contain reproducible noise and sample-specific difficulties; the FID is a computed signal.

**Check:** Signal, temporal order and b remain paired in your analysis.

**Limit:** This action does not command TopSpin or acquire a physical sample. Experimental data enter through Public data or import.

## 05 - Process with explicit decisions

Preserve the sign and check phase, window and baseline dependence.

1. Set Phase correction, Subtracted offset, apodization and Signal window.
2. Press Process and integrate. Inspect the spectrum and integral decay.
3. Compare Whole spectrum, Signal 1 and Signal 2 when overlap exists.
4. Explain why a different window or phase may alter decay without changing physical D.

An integral is a decision about complex data. Taking only magnitudes or clipping negative values can change noise and bias the fit.

**Check:** Your report allows phase, window and baseline processing to be reproduced.

**Limit:** For real Bruker files, inspect digital filtering, reference, sequence and metadata in the experimental workflow. Do not transfer indices from another sample.

## 06 - Interpret without overclaiming

Compare models on exactly the same observations.

1. Select Monoexponential, NNLS, Nonnegative Tikhonov or Nonnegative L1, then Fit the same data.
2. For ILT, record λ and the grid; compare residuals, stability and peaks rather than only appearance.
3. Keep processing fixed to attribute differences to the method. Then examine processing sensitivity separately.
4. Return to the Doctoral laboratory for the ILT kernel, correlations and joint analysis.

A well-fitted curve does not determine a unique distribution. A penalty imposes a preference and may merge or create apparent peaks.

**Check:** You can distinguish numerical fit, resolution, distribution and chemical assignment.

**Limit:** A mixture's monoexponential D is conditional on the model. Do not assign absolute molar masses or species from the map alone.

## 07 - Propagate shared errors

Separate random variation from biases and common dependencies.

[View the actual capture in the PDF manual](RESEARCH_MANUAL_EN.pdf)

1. Enter Monte Carlo draws and SDs for g scale, temperature, processing, noise and model b.
2. Press Propagate shared errors and compare contributions and the conditional interval.
3. Repeat after reducing only noise, then after reducing calibration uncertainty. Compare the effects.
4. Describe which sources share a draw across gradients/signals and which vary by observation.

One calibration can shift several D values together. Treating it as independent noise would manufacture information that was not acquired.

**Check:** Justify a control that reduces a dominant source and list errors your interval does not quantify.

**Limit:** The interval is conditional on the supplied models and distributions. It is not validated experimental coverage and does not automatically correct a wrong model.

## 08 - Choose the next measurement

Use ambiguity to design a discriminating control.

1. Compare Higher b range, Repeat the design, Reverse order, Change Δ and Flow compensation.
2. Write a prediction before pressing Compare designs.
3. Choose an acquisition and press Observe held-out control. Held-out observations use an independent realization.
4. Compare the prediction with results and explain which alternatives remain.

Two distributions may predict the available data similarly and differ over another b region. The proposed acquisition explores that difference.

**Check:** You can defend why this control discriminates better than more equivalent points.

**Limit:** Synthetic design selection and held-out data are not external validation of a real sample. Ideal flow compensation is not equivalent to every double-STE program.

## 09 - RF, gradients and space

Understand the physical origin of spatial encoding and its numerical limits.

[View the actual capture in the PDF manual](RESEARCH_MANUAL_EN.pdf)

1. Set spatial cells, length, RF duration/amplitude, chirp sweep, gradients, evolution, readout and coil profile.
2. Press Calculate Bloch-Torrey; inspect magnetization, phase, transverse profile and readout.
3. Press Check convergence to compare refined time step and grid. Review aliasing warnings.
4. Compare with the introductory ultrafast/SPEN model under Doctoral: explain what RF-based computation adds and what remains ideal.

The model is dM/dt = Ω×M + D·d²M/dz² - (Mx/T2, My/T2, (Mz-1)/T1). Ω contains RF and gradient with time-integrated chirp phase. Reflecting walls, Crank-Nicolson diffusion and exact per-step rotations are used. Readout sums coil-weighted complex magnetization.

**Check:** You can distinguish RF phase, physical gradient integral, nominal resolution and discretization error.

**Limit:** During RF, γ∫Gdt is not coherence q or DOSY b. With linear readout, an offset Δf causes Δz_apparent=Δf/(γHz·G): not molecular motion. The generic protocol does not qualify a particular UF/SPEN-DOSY sequence.

## 10 - Check what you learned

Demonstrate transfer and retention as well as activity completion.

[View the actual capture in the PDF manual](RESEARCH_MANUAL_EN.pdf)

1. Take Initial diagnostic before consulting hints. Use Practice for outstanding concepts and record assistance used.
2. Complete Transfer case with new parameters and inspect each competency state. Return to a case that requires it.
3. The voluntary teaching pilot starts empty. To participate, use an optional local code, mark consent and press Consent and open the initial case. Pretest and posttest contain seven questions with different seeds; declare whether you answered without assistance.
4. The retention case becomes available after seven days, on the displayed date; there is no button to advance that interval. Use Check the current date and Export pilot results. No learners or results are preloaded.

Automatic checks are limited to explicit choices and numbers. Written reasoning requires human review.

**Check:** Solve a new situation without a hint and explain the rule you applied.

**Limit:** The application does not certify doctoral training or infer understanding from text length. Educational efficacy requires students and independent assessment.

## 11 - Defend, review and improve

Keep reviewable reasoning and a traceable second version.

[View the actual capture in the PDF manual](RESEARCH_MANUAL_EN.pdf)

1. Complete objective, physics, design, processing, uncertainty, controls and conclusion.
2. Press Save a new submission. Export portfolio preserves the investigation, evidence and submissions.
3. The instructor uses five 0-4 criteria, cites evidence, writes comments/questions and presses Create and export feedback.
4. The student uses Import feedback, responds to questions and saves another submission without replacing the first.

Feedback is linked to a specific submission and identity; another case's review must not become its assessment.

**Check:** Your second version explains what changed, which evidence persuaded you and what remains unresolved.

**Limit:** Scores and judgment are the instructor's. Integrity checks do not authenticate civil identity or replace an institutional grade system.

## 12 - Work with public originals

Process real experiments and recognize missing information needed for D inference.

[View the actual capture in the PDF manual](RESEARCH_MANUAL_EN.pdf)

1. Open Public data and select a PMA1, PMA6, PMMA1 or PMMA6 acquisition. Each group has two repository acquisitions.
2. Loading checks bytes and SHA-256 before interpreting FIDs/metadata. Inspect program, saved temperature, digital filter, NS and RG.
3. Set phase, apodization and window; press Process public series. Supply one b per acquisition and its provenance before fitting.
4. Press Continue investigation with these integrals to attach them to the case. Document which conditions permit comparison of the two acquisitions.

The eight datasets come from Silva, McKay and Junkers' Monash/Figshare repository, CC BY 4.0. Saved conditions alone do not establish temperature or convection controls.

**Check:** Distinguish missing verified b, nominal scale, absolute calibration and a D conditional on processing.

**Limit:** These eight datasets do not supply sufficient saved DOSY parameters to justify b automatically. Do not invent this axis, a true D or absolute molar mass.

## Continuous example - prepare and acquire

Reproduce a synthetic investigation with checkable parameters and outputs.

1. Under The question, choose Combined faults and seed 20261030; create case RJ-combined-20261030.
2. The first 180° null is 19.8993 µs and the preceding maximum is at 9.94964 µs. Enter P90=9.94964 µs.
3. Use D_ref=1.9×10^-9 m²/s at 298.15 K. The nominal curve fits D=2.20719e-09 m²/s: s=√(D_nominal/D_ref)=1.07781.
4. Enter this scale, both temperatures 298.15 K, and apply calibration. Design STE: δ=2 ms, Δ=80 ms, LED=5 ms, g_max=0.3 T/m, 20 levels, NS=8, one replicate, recycle=2 s, ascending order and a 15 min budget.
5. Check duration approximately 6.352 min and b_max=2.37445e+09 s/m²; acquire the virtual series.

Values are computed by the engine shipped with this edition. Displayed figures are rounded; export retains available precision.

**Check:** Compare against g scale=1 in an exported copy while keeping other decisions fixed.

**Limit:** This example is not an operating prescription for your spectrometer or an accepted experimental result.

## Continuous example - interpret and challenge

Reach a reproducible result that still needs controls.

1. Process with phase=0°, offset=0, LB=0 Hz and Whole spectrum window. Fit Monoexponential to the same data.
2. The example returns D≈4.92791e-10 m²/s and residual RMS≈0.0198293. A reproducible number does not turn combined faults/a mixture into one species.
3. Propagate 40 Monte Carlo draws: relative g SD=0.02, T SD=0.3 K, processing=0.01, noise=0.01 and sequence b-scale=0.01.
4. The illustrative conditional interval is [4.51375e-10, 5.48915e-10] m²/s. Compare contributions before choosing what to reduce.
5. Predict the effect of Reverse order and observe the held-out control. Write what the difference explains and does not explain, then prepare a submission.

The example shows why an estimate, its uncertainty and a causal explanation are different objects.

**Check:** Try another seed without copying these values: the justification should transfer to the new sample.

**Limit:** After changing version, settings, processing or seed, do not force agreement with this table. Save and explain the new identity.

## Beatrix, sources and response modes

Use traceable help without replacing your prediction or calculation.

1. Enter Prediction and reason first. Use Next hint for progressive help linked to the stage.
2. Enter Your question and press Consult sources: documentary retrieval returns reviewed passages and references.
3. In WPF, Ask the local model requests available inference with bounded context. Always read the mode label and distinguish documentary guidance from generated text.
4. Check numbers in the calculation engine and compare the answer with cited sources.

The web edition uses documentary guidance, not an LLM running in PHP. Windows uses a model only when its manifest and CPU evaluation are approved; otherwise documentary guidance is provided. A trained candidate does not automatically become the active model.

**Check:** You can identify source text, calculated output and any actual generated text.

**Limit:** Documentary retrieval, executed training and an approved model are different states. Fluency does not validate an equation, calibration, assignment or student assessment.

## Instructor protocol and independent evaluation

Determine whether the pathway improves decisions in new situations.

[View the actual capture in the PDF manual](RESEARCH_MANUAL_EN.pdf)

1. Before the course, reserve transfer cases/questions not used to train the tutor or select settings.
2. Record the initial diagnostic, decisions, hints, predictions and first submission.
3. Two instructors can review reports with the same rubric, compare disagreements and document the second version.
4. Use a different final case and delayed review. Compare physics, controls, uncertainty and conclusion quality, not just multiple-choice answers.

The Competencies panel runs the local pilot with consent, different initial/final cases and delayed retention. Argument review is human. This manual does not claim results from a cohort that has not been evaluated.

**Check:** Predefine a meaningful improvement and retain failures and negative results too.

**Limit:** Software checks establish computational behavior and synthetic controls. They do not replace expert review or independent educational evaluation.

## Save, import and reproduce

Preserve evidence while distinguishing local state, originals and results.

1. Export investigation/portfolio produces version 1.3 JSON: sample, decisions, results, learning and submissions. The interface portfolio omits raw FIDs: keep originals separately.
2. Import investigation restores a compatible portfolio. To reprocess, reload original series or reacquire the reproducible simulation. Import feedback requires a matching submission and identity checks.
3. CSV import requires finite b/signal pairs and correct units. Importing an unverified local source does not create a license or calibration.
4. For reproduction, record version, seed or hashes, settings, b sources, processing, method and controls. Keep the portfolio outside browser cache.

Storage is local. Browser changes, cache clearing or another profile can change visible progress; export is the portable copy.

**Check:** Open an export in an isolated session and check identity/results before considering a submission complete.

**Limit:** JSON has size/compatibility limits. Do not edit hashes to force import. The web does not synchronize notes/data to an instructor account.

## Sources, links and common problems

Find the equation, dataset and support relevant to each claim.

1. Sinnaeve (2012), DOI 10.1002/cmr.a.21223, and Kuchel et al. (2012), DOI 10.1002/cmr.a.21241, underpin the mathematical pathway. Use the 20 Derivations chapters for symbols, pages, equations and assumptions.
2. Torrey (1956), DOI 10.1103/PhysRev.104.563: diffusion in Bloch equations. Shrot, Shapira and Frydman (2004), DOI 10.1016/j.jmr.2004.08.001: continuous spatial encoding.
3. Silva, McKay and Junkers, DOI 10.26180/33075584.v1, CC BY 4.0: source of public experimental files; retain attribution.
4. If public data are absent, check package/version access. If b is absent, document its derivation; for aliasing, review grid/readout. If saving fails, export before closing.

This manual supplements the retained doctoral manual and original course with their explicit sources and conventions.

**Check:** Every final conclusion identifies data, model, conditions, uncertainty and limitations.

**Limit:** A file group, good fit or attractive screenshot does not by itself validate a physical explanation.

[Doctoral manual](DOCTORAL_MANUAL_EN.pdf)

https://doi.org/10.1002/cmr.a.21223
https://doi.org/10.1002/cmr.a.21241
https://doi.org/10.1103/PhysRev.104.563
https://doi.org/10.1016/j.jmr.2004.08.001
https://doi.org/10.26180/33075584.v1
