# DiffAtOnce Academy - portable / portátil

## Inicio rápido

1. Extraiga toda la carpeta `DiffAtOnce-Academy-...-win-x64`.
2. Abra `DiffAtOnce.Academy.exe`. Conserve los DLL y las carpetas `Content`,
   `Lab`, `Docs` y `Models` suministradas junto al ejecutable.
3. Use **EN/ES** para elegir idioma. **Manual** abre el PDF correspondiente.
4. Empiece por **03 · Primero: calibrar P90 en la muestra** y abra
   **Taller numérico**. Localice el primer nulo de 180° a 22 µs y compruebe
   22/2=11 µs; repita seleccionando 44 µs y explique el error.
5. Calcule antes de preguntar a Beatrix. Compruebe su modo, contexto y fuentes.
6. Anote su conclusión en **Mi cuaderno**. **Exportar** guarda un JSON elegido
   por usted; no envía el trabajo al docente.

El paquete de entrega se genera para Windows x64 y contiene el runtime .NET.
Las escenas interactivas necesitan Microsoft Edge WebView2 Runtime. Si falta,
la aplicación lo indica; las lecciones, preguntas y talleres nativos siguen
disponibles. Consulte las instrucciones legítimas de instalación de WebView2
en su centro cuando corresponda. La primera pregunta al modelo local incluye
carga y verificación; prepare una consulta antes de una demostración en clase.

## Quick start

1. Extract the complete `DiffAtOnce-Academy-...-win-x64` folder.
2. Open `DiffAtOnce.Academy.exe`. Keep supplied DLLs and `Content`, `Lab`,
   `Docs` and `Models` folders beside the executable.
3. Use **EN/ES** to choose a language. **Manual** opens the matching PDF.
4. Start with **03 · First: calibrate P90 on the sample** and open
   **Numeric workshop**. Locate the first 180° null at 22 µs and check
   22/2=11 µs; repeat with 44 µs and explain the error.
5. Calculate before asking Beatrix. Check its mode, context and sources.
6. Record a conclusion in **My notebook**. **Export** saves a JSON file you
   select; it does not submit work to a teacher.

The delivered package targets Windows x64 and includes the .NET runtime.
Interactive scenes require Microsoft Edge WebView2 Runtime. If unavailable,
the application reports it; lessons, questions and native workshops remain
usable. Follow your institution's legitimate WebView2 installation procedure
when needed. A first local-model query includes loading and verification;
prepare one before a classroom demonstration.

## Contenido / Contents

| Carpeta o archivo / Folder or file | Función / Purpose |
|---|---|
| `Content` | Curso bilingüe, 81 diapositivas originales, catálogo y procedencia / Bilingual course, 81 original slides, catalogue and provenance |
| `Lab` | 17 escenas locales con ejemplos y modelos ideales / 17 local scenes with examples and ideal models |
| `Docs` | Manuales PDF ES/EN y guías para estudiantes/docentes / ES/EN PDF manuals and student/teacher guides |
| `Models/Beatrix` | Modelo local y manifiesto/informes verificables, si se suministra / Local model and verifiable manifest/reports, when supplied |
| `PACKAGE_SHA256.json` | Inventario de integridad del paquete / Package integrity inventory |

El curso incluye 24 módulos, 48 ejemplos y 48 preguntas explicadas. El catálogo
tiene 72 registros auditados; no son 72 algoritmos distintos. Hay cinco talleres
nativos: P90, gradiente, δ/Δ, convección e ILT. Parte de los ejemplos pide una
decisión escrita: no son 48 motores numéricos diferentes.

The course includes 24 modules, 48 examples and 48 explained questions. Its
catalogue contains 72 audited records, not 72 distinct algorithms. Five native
workshops cover P90, gradients, δ/Δ, convection and ILT. Some examples require
a written decision; they are not 48 independent numerical engines.

## Beatrix y sus límites / Beatrix and its limits

**Guía documental · sin LLM / Documentary guide · no LLM** indica recuperación
del curso sin inferencia. **Beatrix · LLM local + texto del curso · CPU / Beatrix ·
local LLM + course text · CPU** identifica una respuesta híbrida. No convierta
un modo documental en una demostración de generación. El paquete final exige
manifiesto compatible, hashes válidos y comprobación CPU terminada; los informes
incluidos describen la evidencia concreta. **Cancelar / Cancel** detiene la
consulta. Al editar parámetros del taller se borran resultados antiguos y se
exige **Calcular / Calculate** antes de interpretar una nueva salida.

The documentary mode means course retrieval without model inference. The
hybrid CPU mode combines labelled LLM text and a separate literal course quote. Do not present documentary
retrieval as a generation demonstration. The final package requires a compatible
manifest, valid hashes and completed CPU checking; supplied reports describe
the actual evidence. Editing workshop parameters clears obsolete results and
requires recalculation before interpreting a new output.

La interfaz identifica **Explicación de Beatrix · LLM** y **Texto literal del
curso · fuente**. El bloque literal aporta el mecanismo del curso, sin
atribuirlo a generación. El test HF reservado obtuvo 32/32 frente a 21/32 del
modelo base. El flujo CPU híbrido superó 15/15 comprobaciones; no es una
aprobación causal del modelo solo. Sus omisiones abiertas SPEN/TR se conservan
en los informes. Los cálculos del taller provienen del motor numérico.

The UI distinguishes **Beatrix's explanation · LLM** from **Literal course text
· source**. The quote supplies the course mechanism without attributing it to
generation. The reserved HF test scored 32/32 versus 21/32 for the base model.
The hybrid CPU pipeline passed 15/15 checks; this does not approve generated-only
causal answers. Open SPEN/TR omissions remain in the reports. Workshop
calculations come from the numerical engine.

La aplicación y Beatrix enseñan con simulaciones. No operan TopSpin, adquieren
espectros ni escriben calibraciones. Una respuesta correcta, un quiz aprobado o
un test de software no acreditan calibración instrumental, identidad química o
competencia de operación. El prototipo ultrafast conserva NO-GO cuantitativo
hasta controles experimentales. La presentación fuente y los datos históricos
permanecen atribuidos, sin modificar originales.

The application and Beatrix teach through simulations. They do not operate
TopSpin, acquire spectra or write calibrations. A correct response, completed
quiz or software test does not establish instrument calibration, chemical
identity or operator competence. The ultrafast prototype retains quantitative
NO-GO pending experimental controls. Source slides and historical results
retain their provenance; original inputs are preserved.

## Trabajo local / Local work

El progreso por usuario se guarda en
`%LOCALAPPDATA%\DiffAtOnce\Academy\progress-v1.json`. Las notas pertenecen al
estudiante. Use la exportación para una copia que pueda compartir deliberadamente.
Cambiar el hash del archivo no traslada aprobaciones entre versiones del curso.
Los enlaces de artículos se abren en un navegador externo al pulsarlos.

Per-user progress is stored at
`%LOCALAPPDATA%\DiffAtOnce\Academy\progress-v1.json`. Student notes remain local.
Export a copy for intentional sharing. Editing the course hash does not transfer
checked lessons across course versions. Paper links open in an external browser
when clicked.

Para instrucciones ilustradas y rutas de 100/20 minutos, consulte
`MANUAL_ES.pdf`, `MANUAL_EN.pdf` y `TEACHER_GUIDE_ES_EN.md`.
For illustrated instructions and 100/20-minute routes, see the same files.
