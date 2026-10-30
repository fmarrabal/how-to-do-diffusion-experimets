# DiffAtOnce Academy

**ES.** Una aplicación WPF para aprender DOSY haciendo preguntas, provocando
errores y comparando resultados conocidos con los recuperados. La historia
empieza en la calibración del espectrómetro y continúa hasta la interpretación
del mapa. Cada lección explica el objetivo, por qué aparece el problema, para
qué se hace el paso y qué comprobación permite avanzar.

**EN.** A WPF application for learning DOSY by asking questions, creating errors
and comparing known values with recovered results. The story starts with
spectrometer calibration and continues through map interpretation. Each lesson
explains its objective, why the problem occurs, why the step is needed and which
check permits the next decision.

Start with [USER_GUIDE_ES.md](USER_GUIDE_ES.md) or
[USER_GUIDE_EN.md](USER_GUIDE_EN.md). They include practical instructions,
a 100-minute teaching session and a 20-minute demonstration route.

Illustrated editions: [MANUAL_ES.pdf](MANUAL_ES.pdf) and
[MANUAL_EN.pdf](MANUAL_EN.pdf). The manuals use actual final application captures
and preserve the simulation/experiment boundary.
Rebuilding and capture provenance are documented in
[MANUAL_PROVENANCE.md](MANUAL_PROVENANCE.md).

Package quick start: [PORTABLE_README_ES_EN.md](PORTABLE_README_ES_EN.md).
Formative deliverables and rubric:
[TEACHER_GUIDE_ES_EN.md](TEACHER_GUIDE_ES_EN.md).

## What is included / Qué incluye

| Component / Componente | Contents / Contenido |
|---|---|
| Course / Curso | 24 bilingual modules with purpose, mechanism, practical steps and limitations / 24 módulos bilingües con finalidad, mecanismo, pasos y límites |
| Practice / Práctica | 48 guided examples, including 24 counterexamples; some load numeric presets and others are reasoning exercises / 48 ejemplos guiados, incluidos 24 contraejemplos; unos cargan parámetros y otros son ejercicios de razonamiento |
| Assessment / Evaluación | 48 questions with explained feedback; all answers in a module must be correct to mark it checked / 48 preguntas con explicación; se requieren todas las respuestas correctas para marcar el módulo comprobado |
| Laboratory / Laboratorio | 17 local interactive scenes, including computed UF, SPEN and time-resolved examples / 17 escenas locales, incluidos ejemplos calculados UF, SPEN y resueltos en tiempo |
| Native workshop / Taller nativo | Five calculators: P90, gradient scale, δ/Δ design, convection and ILT conditioning / Cinco calculadoras: P90, escala de gradiente, diseño δ/Δ, convección y condicionamiento ILT |
| Original workshop / Workshop original | 81 source-slide images and original notes, with source hashes and module mapping / 81 imágenes y notas originales, con hashes y relación con los módulos |
| Method catalogue / Catálogo | 72 audited records: 51 library cores, 9 historical Prime routes and 12 context families; not 72 distinct algorithms / 72 registros auditados: 51 cores, 9 rutas históricas Prime y 12 familias; no 72 algoritmos distintos |
| Beatrix | Local LLM plus separately labelled literal course text, with documentary fallback / LLM local más texto literal del curso identificado por separado, con alternativa documental |
| Notebook / Cuaderno | Module notes, quiz results and local JSON export / Notas por módulo, resultados y exportación JSON local |

## Start / Inicio

On Windows, extract the whole supplied application folder and open
`DiffAtOnce.Academy.exe`. Keep `Content`, `Lab` and any supplied `Models` folder
beside the executable. Use **EN/ES** to change language. The original English
slide images and notes retain their source language.

En Windows, extraiga toda la carpeta de la aplicación y abra
`DiffAtOnce.Academy.exe`. Conserve `Content`, `Lab` y, si se incluye, `Models`
junto al ejecutable. Use **EN/ES** para cambiar de idioma. Las diapositivas y
notas originales conservan el inglés de la fuente.

The interactive laboratory uses Microsoft Edge WebView2 Runtime. If it is
missing, the application reports it; lessons, quizzes and the native workshop
can still be used. Follow the package's runtime instructions if it is a
framework-dependent build. The source project targets .NET 8 for Windows.

El laboratorio interactivo utiliza Microsoft Edge WebView2 Runtime. Si falta,
la aplicación lo indica; las lecciones, preguntas y taller nativo siguen
disponibles. Siga las indicaciones del paquete si la compilación depende de un
runtime instalado. El proyecto fuente utiliza .NET 8 para Windows.

## Beatrix status / Estado de Beatrix

**Verified hybrid package, 5 October 2026:** local fine-tuning scored 32/32
on the reserved HF test, compared with 21/32 for the base model. The final CPU
pipeline passed 15/15 checks of **LLM + literal course text**. Generated-only
CPU answers omitted causal detail in open SPEN/TR questions; those limitations
remain in the reports. These are different tests with different scopes.

**Paquete híbrido verificado, 5 de octubre de 2026:** el ajuste local obtuvo
32/32 en el test HF reservado, frente a 21/32 del modelo base. El flujo CPU final
superó 15/15 comprobaciones del conjunto **LLM + texto literal del curso**.
Las respuestas generadas solas omitieron causas en preguntas abiertas SPEN/TR;
los informes conservan esas limitaciones. Son pruebas y alcances distintos.

The tutor supports a local fine-tuned GGUF model. It verifies model checksum,
course version and training/evaluation-report hashes before model use.
The UI labels **Beatrix's explanation · LLM** separately from **Literal course
text · source**. The second block quotes the course's why/mechanism verbatim
and must not be attributed to model generation. The active mode reads
**Beatrix · local LLM + course text · CPU**.
**Documentary guide · no LLM / Guía documental · sin LLM** means no model
inference was used, including an unavailable model, failed verification or a
generation/context failure. This fallback provides course evidence and sources;
it must not be described as a generated LLM answer. Questions can be cancelled.

La tutora admite un modelo GGUF local ajustado al curso. Antes de usarlo verifica
integridad, versión del curso y hashes de los informes. **Guía documental · sin
LLM** significa que no hubo inferencia, también si el modelo falta, la
verificación falla o no puede generar/procesar el contexto. Esa alternativa
ofrece contenido y fuentes del curso; no se presenta como respuesta generada.
La consulta se puede cancelar.

La interfaz separa **Explicación de Beatrix · LLM** y **Texto literal del curso ·
fuente**. El segundo bloque copia el problema y mecanismo del curso; no se
atribuye al modelo. El modo indica **Beatrix · LLM local + texto del curso · CPU**.

Inference and documentary retrieval are local. User-clicked paper/web links
open an external browser. Beatrix does not operate TopSpin, edit calibrations,
modify spectra or establish molecular identity. Fine-tuning does not itself
prove educational effectiveness or scientific accuracy.

The numeric workshop supplies current parameters, calculated results and
assumptions to Beatrix. Editing a field clears old curves/results and requires
**Calculate** again. Returning to **Experiment** restores laboratory context;
changing lessons resets module context.

La inferencia y consulta documental son locales. Los enlaces web que pulsa el
usuario abren un navegador externo. Beatrix no opera TopSpin, cambia
calibraciones, modifica espectros ni establece identidades moleculares. El
fine-tuning por sí mismo no demuestra eficacia educativa ni exactitud científica.

El taller transmite parámetros, resultados calculados y supuestos vigentes.
Editar un campo borra las curvas/resultados anteriores y exige **Calcular**
otra vez. Volver a **Experimentar** restaura el contexto del laboratorio;
cambiar de lección vuelve al contexto del módulo.

## Evidence and source preservation / Evidencia y preservación

The frozen teaching snapshot was extracted read-only from a PPTX with SHA-256
`d54f2a6b7a42dc640a26b199408bf19505cea4dac7615089e5f679d168a63a1d`.
All 81 slides are mapped to the course. Embedded slide images are exact copies;
accessible descriptions and notes are extracted without OCR guesses. See
`Content/source-index.json` and `Content/CURRICULUM_PROVENANCE.md`.

A final read-only recheck found a different current PPTX container: 32,785,972
bytes, SHA-256 `5dfce0b0ec2b6f9bf2ddc1eef5ca04a4d31e053c9e2f051d6542fff63e273975`.
All 81 slide images, notes, text/accessibility descriptions, order and recorded
media relationships still match the frozen extraction. The 22-byte size change
does not establish simple ZIP-footer appending; its cause is undetermined.
See `source-input-reaudit.json`. Course/source-index and training provenance
remain frozen; the current whole container is not claimed to be byte-identical.

La presentación original se lee sin modificarla. Sus 81 diapositivas están
relacionadas con el curso; las imágenes se copian exactamente y las notas y
descripciones accesibles se extraen sin reconstrucciones OCR. Consulte
`Content/source-index.json` y `Content/CURRICULUM_PROVENANCE.md`.

En el cierre, el contenedor PPTX actual tiene otro hash y 22 bytes más. La
reauditoría de lectura compara las 81 imágenes, notas, texto/descripciones,
orden y relaciones de medios: todas coinciden con el snapshot didáctico.
La causa del cambio del contenedor no está determinada. No se modifica el
curso, el índice de procedencia ni el modelo para ocultar esta diferencia.

All new numerical exercises are synthetic. Historical TP194, KK2 and HDO values
are attributed examples, not new measurements. The course preserves the shared
TBO profile and the authorized KK2 factor convention. It does not rewrite
experimental inputs, calibrations or production software. The local UF prototype
retains quantitative NO-GO pending instrument controls. Software tests and tutor
training must not be reported as experimental validation.

Los ejercicios numéricos nuevos son sintéticos. TP194, KK2 y HDO son ejemplos
históricos atribuidos, no mediciones nuevas. Se conservan el perfil TBO y la
convención de factores KK2. No se reescriben datos, calibraciones ni aplicaciones
de producción. El prototipo UF mantiene NO-GO cuantitativo hasta los controles
en instrumento. Los tests y entrenamiento no son validación experimental.

## For maintainers / Para mantenimiento

Build from the repository root:

```powershell
dotnet build desktop/academy/src/DiffAtOnce.Academy.App/DiffAtOnce.Academy.App.csproj -c Release
dotnet run --project desktop/academy/tests/DiffAtOnce.Academy.Tests -c Release
```

Curriculum extraction, generation and contract checks are in
`tools/curriculum_extract.py`, `tools/curriculum_build.py` and
`tools/curriculum_validate.py`. The course is frozen for tutor provenance;
changing it requires explicitly updating the model/course compatibility and
training records. Actual training instructions are in `ai/README_ES_EN.md`.

Progress is saved per Windows user at
`%LOCALAPPDATA%\DiffAtOnce\Academy\progress-v1.json`; the application keeps a
previous copy during saves. The file includes the course hash, answers and
student notes. **Export / Exportar** writes a user-selected JSON file; it does
not submit work to a teacher or generate an experimental report.
