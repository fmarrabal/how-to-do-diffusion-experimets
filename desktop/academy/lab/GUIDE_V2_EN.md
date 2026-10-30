# Diffusion Motion Lab · v2 simulation guide

The laboratory contains 17 scenes in English and Spanish. The three featured scenes calculate synthetic signals, reconstructions and fits. Their known input values provide checks of the implemented model, not validation of a spectrometer or a real sample.

## A five-minute walkthrough

1. Open **SPEN-DOSY** and press **Play**. Follow complex alternating-polarity data, the calculated spectral matrix and the selected-frequency attenuation. Try the 90° phase-error scenario and compare fits before and after correction. Select −80 Hz and then 120 Hz to explore two resonances. Between peaks, apparent D may reflect contributions from both species.
2. Open **Ultrafast**. In the ideal scenario, normalization and calibration recover the input D. Add receive sensitivity and a gradient-scale error. A reference corrects this model’s profile, while correcting b additionally requires knowledge of the gradient scale. A noisy reference increases uncertainty and makes some points unusable.
3. Open **Time-resolved**. A and B have constant D, but A converts to B. Compare the same reaction with ascending and descending ramps: apparent D changes because composition and b are correlated in time. Rapid spatial acquisition shares a temporal window and reduces that bias. Permuting gradients improves time distribution but does not stop chemistry.

## Four clocks

**Δ**, in milliseconds, is diffusion-pulse separation. **t_read** belongs to readout. **t_lab**, in seconds, tracks sample evolution. Frame duration and cadence describe temporal averaging and spacing between results; overlapping frames share points and noise. The 18-second transport bar controls visual animation progress only.

## Results and controls

Cards show known references and calculated estimates. “Not estimable” identifies insufficient usable signal or a slope incompatible with the physical fit. Monoexponential fitting uses positive points above 1.5% of the maximum and estimates an intercept too. This cutoff is a teaching choice, not a noise estimate.

Scenarios restore example defaults before applying their changes. Sliders show the effect of changing a parameter. Gaussian noise has a fixed seed for reproducible comparisons.

Pause, scrub visual progress, switch languages or open full screen. Space and arrow keys control playback and scenes when focus is outside another control. The scene library can be collapsed on mobile.

## Exports

**CSV** exports calculated synthetic signals with units in column names. **PNG** saves the current state. **Record WebM** records 18 seconds with the selected parameters when the browser provides a compatible encoder. Recording has no audio.

The retained 32 MP4 files and four GIFs come from version 1. SPEN/ultrafast links identify them as historical schematics rather than the new calculated reconstructions. Time-resolved uses PNG/WebM and CSV; no nonexistent MP4 link is offered.

## Implemented physics

Ultrafast uses an ideal PGSE surrogate with local rectangular durations δ(z), SI b(z), receive profile and relaxation at a common echo. A real chirp requires integrating the local q(z,t) history from the actual pulse program.

SPEN uses a simplified complex EPSI echo-center acquisition, spatial polarity reordering, known phase correction, spatial IDFT and spectral DFT. It does not simulate finite chirp RF, within-lobe chemical evolution, z–ν shear or every effect of a real sequence. It fits a selected attenuation; no ILT or target DOSY map is calculated.

Time-resolved uses an ideal first-order A→B reaction with separated resonances and constant D. Composition is integrated over acquisition windows and overlapping sequential windows share points. Exchange during Δ and experimental polymerization are not simulated.

The existing D–T₂ scene shows a calculated signal and a schematic target map, explicitly identified; it does not run an ILT. The researcher-supplied historical figure remains separate with its original provenance.

Primary references and their specific support appear in `science-v2-references.json`, scene source lists and `REFERENCES.md`. Originals, earlier videos and experimental calibrations are preserved.
