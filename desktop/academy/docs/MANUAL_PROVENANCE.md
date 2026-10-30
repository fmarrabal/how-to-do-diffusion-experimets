# Illustrated manual provenance / Procedencia del manual ilustrado

The PDF manuals are generated from `USER_GUIDE_ES.md`, `USER_GUIDE_EN.md`, the
frozen `Content/course.json` and exact actual GUI captures. No original
presentation, calibration or experimental file is edited. Images that show
Spanish controls remain Spanish in the English manual and are labelled.

Los manuales PDF proceden de las guías ES/EN, del curso congelado y de capturas
reales verificadas en `qa/ui-release-final`. La figura ampliada procede de WebView2;
las ventanas y talleres se capturaron en WPF. No se utilizan las capturas
transparentes de las etapas intermedias. Un panel con alternativa documental
identificada se conserva como ese modo, nunca como una respuesta del LLM. Las
figuras principales de lección y P90 del manual inglés usan las capturas
inglesas reales `academy-lesson-en.png` y `academy-calibration-en.png`.
La captura `academy-beatrix.png` muestra una consulta CPU auténtica con texto
generado y una copia literal del curso identificados en bloques separados.
La pregunta de esa figura usa 18/2=9 µs; no es el ejercicio del taller 22/2=11 µs.

## Rebuild / Regenerar

Run from the repository root with Python and the required PDF libraries. Install Poppler on PATH, or set ACADEMY_PDFTOPPM / pass --pdftoppm to manual_verify.py:

```powershell
python desktop/academy/tools/manual_build.py --qa desktop/academy/qa/ui-release-final --manifest desktop/academy/ai/release/manifest.json
python desktop/academy/tools/manual_verify.py
```

The `--capture` option selects one actual PNG without importing unrelated
screenshots in its directory. Repeated `--qa` directories prefer later files
with the same name; use that option only for directories whose images have
been inspected and approved as genuine captures. The generator does not create
or reconstruct a tutor conversation.

`--manifest PATH` can update the PDF's tutor status only after the local
fine-tuned package passes its declared educational gate. The generator checks
`fineTuned`, `qualityPassed`, the course hash, `experimentalValidation=false`,
the actual training/evaluation/native-CPU report hashes and the complete GGUF model hash.
It also requires `NativeEvaluationPending=false`, `NativeEvaluationPassed=true`,
an all-passed native report and the explicit hybrid answer mode with literal
course text. A passed GPU generation gate
does not silently stand in for the native CPU package check. Both PascalCase
application manifests and earlier camelCase field names are supported.
A compatible manifest documents package provenance; it does not establish
expert review, instrument validation or measured student learning.

The frozen extraction records PPTX SHA `d54f2a6b7a42dc640a26b199408bf19505cea4dac7615089e5f679d168a63a1d`.
Final read-only rechecking found current container SHA
`5dfce0b0ec2b6f9bf2ddc1eef5ca04a4d31e053c9e2f051d6542fff63e273975`, with 22 more
bytes. All 81 recorded slide images, descriptions/text, notes, order, hidden
flags and image/video relationships match. `source-input-reaudit.json` keeps
the evidence and archive-entry hashes; `tools/manual_source_reaudit.py` repeats
the read-only comparison. The container change's cause is not assigned.
Course, source-index and training provenance remain frozen; whole-container
byte identity is not claimed.

The reserved HF result is 32/32 versus 21/32 for the base model. The native CPU
result is 15/15 for the hybrid workflow. Generated-only causal SPEN/TR omissions
remain recorded: the separately labelled quote supplies the course mechanism
without attributing that wording to model generation.

La opción `--manifest` exige un paquete verificable antes de cambiar el estado
de Beatrix. Sin manifiesto, el manual conserva el estado provisional. No use
una captura de la alternativa documental como evidencia de inferencia LLM.

## Verification / Verificación

`manual-build-manifest.json` records input image paths, dimensions and hashes,
selected capture directories, tutor provenance and PDF hashes.
`manual-verification.json` records structural/text-bound checks and complete
Poppler rendering. `manual-visual-review.json` records the human-readable
review of all rendered pages for the stated PDF hashes.

The `docs/qa/manual-pages` PNGs and contact sheets are verification
intermediates. Deliver `MANUAL_ES.pdf` and `MANUAL_EN.pdf` with the useful guide
and provenance files; omit large render intermediates from the portable app.
After any rebuild, repeat rendering and review before reusing a prior approval.
