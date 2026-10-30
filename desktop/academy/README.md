# DiffAtOnce Academy 1.3

Formación práctica y doctoral en RMN de difusión, en español e inglés, con el mismo motor de investigación en WPF y en el navegador. / Practical and doctoral diffusion NMR training in Spanish and English, using the same research engine in WPF and the browser.

## Empieza aquí / Start here

En Windows abre **Investigación continua**; en la web selecciona **Investigación**. En inglés, selecciona **Research studio** en WPF y **Research** en la web. Sigue una muestra desde la predicción inicial hasta una conclusión defendible. El curso original, el lector matemático y el laboratorio doctoral siguen disponibles.

In Windows open **Research studio**; in the browser select **Research**. Follow one sample from an initial prediction to a defensible conclusion. The original course, mathematics reader and doctoral laboratory remain available.

| Documento / Document | Español | English |
| --- | --- | --- |
| Manual completo / Complete manual · 68 páginas/pages | [ACADEMY_MANUAL_ES.pdf](docs/ACADEMY_MANUAL_ES.pdf) | [ACADEMY_MANUAL_EN.pdf](docs/ACADEMY_MANUAL_EN.pdf) |
| Investigación 1.3 / Research 1.3 · 22 páginas/pages | [RESEARCH_MANUAL_ES.pdf](docs/RESEARCH_MANUAL_ES.pdf) | [RESEARCH_MANUAL_EN.pdf](docs/RESEARCH_MANUAL_EN.pdf) |
| Inicio rápido bilingüe / Bilingual quick start | [START_HERE_ES_EN.txt](START_HERE_ES_EN.txt) | ES + EN |
| Reconstrucción desde fuentes / Build from source | [SOURCE_BUILD_V13.md](SOURCE_BUILD_V13.md) | ES + EN |

Los manuales completos integran la guía actual y los manuales anteriores identificados como históricos. En el paquete portable están en `Docs/`; en este árbol fuente, en `docs/`. La presencia de un PDF o una compilación local no acredita publicación ni validación experimental.

The complete manuals combine current instructions with clearly labelled historical manuals. Portable packages use `Docs/`; this source tree uses `docs/`. A PDF or local build does not establish publication or experimental validation.

## Un recorrido de 12 etapas / A 12-stage investigation

1. **Pregunta / Brief:** formula una predicción y el control que podría refutarla. / State a prediction and a control that could refute it.
2. **Calibración / Calibration:** comprueba el pulso de 90°, la escala de gradiente y la referencia térmica. / Check the 90° pulse, gradient scale and temperature reference.
3. **Diseño / Design:** elige secuencia, δ/Δ, ventana de atenuación y puntos medibles. / Choose sequence, δ/Δ, attenuation window and measurable points.
4. **Adquisición / Acquire:** conserva el FID de la misma muestra y examina fallos combinados. / Retain the same sample's FID and inspect combined faults.
5. **Procesado / Process:** justifica fase, línea base, ventanas e integración. / Justify phase, baseline, windows and integration.
6. **Interpretación / Inference:** compara ajuste monoexponencial, distribución e hipótesis alternativas. / Compare monoexponential fitting, distributions and alternative explanations.
7. **Incertidumbre / Uncertainty:** propaga errores comunes y ruido sin confundir precisión y exactitud. / Propagate shared errors and noise without confusing precision with accuracy.
8. **Siguiente medida / Next measurement:** diseña una observación que discrimine alternativas. / Design an observation that distinguishes alternatives.
9. **RF + espacio / RF + space:** explora codificación espacial, difusión y lectura bajo supuestos explícitos. / Explore spatial encoding, diffusion and readout under explicit assumptions.
10. **Competencias / Competencies:** identifica dificultades y, de forma voluntaria, ejecuta el protocolo piloto local. / Identify difficulties and optionally run the local pilot protocol.
11. **Defensa y revisión / Defence and review:** exporta una entrega y vincula una devolución docente mediante rúbrica. / Export a submission and link an instructor's rubric-based review.
12. **Datos públicos / Public data:** verifica originales, procesa FIDs e interpreta lo que permiten los metadatos. / Verify originals, process FIDs and interpret what their metadata support.

El caso conserva muestra, decisiones y procedencia entre etapas. Cambiar una decisión anterior invalida los resultados que dependen de ella. Los fallos simulados incluyen calibración, convección, deriva y solapamiento; se distinguen de los datos experimentales importados.

The case retains sample, decisions and provenance across stages. Changing an upstream decision invalidates dependent results. Simulated faults include calibration, convection, drift and overlap; simulations remain distinct from imported experimental data.

## Incertidumbre, datos y revisión / Uncertainty, data and review

**ES.** El Monte Carlo comparte cada error de gradiente entre todos los valores de b y las frecuencias; la temperatura común tampoco se vuelve independiente al repetir puntos. Separa estas fuentes del ruido y de las hipótesis de procesado/modelo. El intervalo es condicional a esas hipótesis y no demuestra cobertura experimental. La comparación de distribuciones puede admitir soluciones distintas con ajuste parecido: la siguiente medida se evalúa con observaciones reservadas de otra semilla.

**EN.** Monte Carlo draws share each gradient-scale error across all b values and frequencies; common temperature uncertainty does not become independent through repeated points. These sources remain separate from noise and processing/model assumptions. Intervals are conditional on those assumptions and do not establish experimental coverage. Different distributions can fit similarly; proposed measurements are assessed using separately seeded held-out observations.

**ES.** La [biblioteca 1.3](content/research-library.json) añade ocho series experimentales públicas y 72 archivos originales de Monash/Figshare, con CC BY 4.0, atribución y SHA256 por archivo. Su agrupación no demuestra controles pareados de convección o temperatura ni réplicas idénticas. No se inventa b a partir del número de fila o de un gradiente nominal: sin b documentada se bloquea el ajuste de D. Con b aportada por el usuario, D sigue siendo condicional a su procedencia, secuencia y calibración. El caso D₂O histórico de 1.2 se conserva por separado.

**EN.** The [1.3 library](content/research-library.json) adds eight public experimental series and 72 original Monash/Figshare files, with CC BY 4.0, attribution and per-file SHA256. Repository grouping does not establish paired convection/temperature controls or identical replicates. b is never invented from row number or a nominal gradient: undocumented b blocks D fitting. User-supplied b still makes D conditional on provenance, sequence and calibration. The historical 1.2 D₂O case is retained separately.

**ES.** Las comprobaciones numéricas y de elección tienen corrección objetiva; los argumentos escritos requieren revisión humana. El piloto comienza con cero participantes y sólo crea un registro tras consentimiento explícito. Usa pretest, postest con otra forma y retención tras siete días reales; no incluye participantes ni resultados reales, y no demuestra eficacia docente. Los datos y las exportaciones permanecen locales.

**EN.** Numerical and choice questions have objective checks; written arguments require human review. The pilot starts with zero participants and creates a record only after explicit consent. It uses pretest, a different post-test form and retention after seven real days. It includes no real participants or outcomes and establishes no educational efficacy. Data and exports remain local.

## Beatrix y límites / Beatrix and boundaries

**ES.** La web ofrece consulta documental revisada y no ejecuta un LLM. WPF puede ofrecer inferencia local sólo con pesos compatibles, manifiesto, hashes, revisión científica y evaluación nativa CPU aprobados para ese contenido. La disponibilidad de un candidato, de un ajuste fino o de este código no implica aprobación nativa de R4. Mientras falte una condición, se muestra la guía documental. Las preguntas pendientes se vinculan al caso, etapa y cálculo; una respuesta tardía de otro contexto se descarta y nunca modifica cifras.

**EN.** The browser provides reviewed documentary guidance and runs no LLM. WPF may offer local inference only when compatible weights, manifest, hashes, scientific review and native CPU evaluation are approved for that content. A candidate, fine-tune or this source tree does not establish native approval of R4. Until the conditions are met, the documentary guide is used. Pending questions are bound to case, stage and calculation; late replies from another context are discarded and never alter numerical results.

Academy no controla el espectrómetro ni modifica originales experimentales, TBO, KK2 o el software de producción DiffAtOnce. Las simulaciones, pruebas de software, integridad de paquetes, calibración física y validación educativa son evidencias distintas.

Academy does not control a spectrometer or modify experimental originals, TBO, KK2 or production DiffAtOnce software. Simulations, software checks, package integrity, physical calibration and educational validation are separate forms of evidence.

## Desarrollo y reconstrucción / Development and rebuilding

Consulta [SOURCE_BUILD_V13.md](SOURCE_BUILD_V13.md) para Windows x64/.NET 8, vista previa web local, pruebas, exclusiones del paquete fuente y publicación con revisión por hashes. `--prepare` prepara una copia local con revisión pendiente; no publica ni aprueba un modelo. No se necesitan Python, Node.js ni una clave API para usar el paquete WPF publicado.

See [SOURCE_BUILD_V13.md](SOURCE_BUILD_V13.md) for Windows x64/.NET 8, local browser preview, tests, source-package exclusions and hash-bound release review. `--prepare` prepares a local pending-review copy; it neither publishes nor approves a model. Python, Node.js and an API key are unnecessary for using a released WPF package.

## Archivo histórico: ediciones base, 1.1 y 1.2 / Historical archive: base, 1.1 and 1.2

Las secciones siguientes conservan las instrucciones y límites de aquellas ediciones. Sus rutas de construcción, recuentos y declaraciones de tutor se refieren a esas versiones; para 1.3 utiliza las instrucciones anteriores y SOURCE_BUILD_V13.md.

The following sections preserve those editions' instructions and limits. Their build routes, counts and tutor statements refer to those versions; use the instructions above and SOURCE_BUILD_V13.md for 1.3.

### README original / Original README

Aplicación WPF bilingüe de formación en RMN de difusión. / Bilingual WPF application for diffusion NMR teaching.

Versión1.2 añade un laboratorio doctoral completo: movimiento/fase/eco sincronizados,
constructor de vía de coherencia,93 pasos guiados, campaña experimental virtual,
diagnóstico de causas ocultas, inversión mono/ILT/conjunta, procesado de FID públicos
Bruker, comparación temporal ultrafast/SPEN y rúbrica docente. Nueve actividades
comparten cuaderno y exportación local. El conjunto real CC BY4.0 de Monash
(DOI10.26180/33075584.v1) conserva archivos y hashes; su b y D son nominales y
condicionales, sin atribuir una calibración absoluta. Las nuevas pistas son
documentales revisadas, sin nuevo ajuste fino ni generación LLM.

Version1.2 adds nine doctoral activities linking molecular motion, phase and echo,
coherence-pathway construction,93 guided steps, virtual experimental decisions,
blind diagnostics, inverse/joint analysis, public Bruker FID processing, time-resolved
UF/SPEN comparisons and an instructor rubric. Notebook/evidence exports stay local.
The CC BY4.0 Monash dataset retains original bytes and hashes; nominal b and fitted D
remain conditional. New hints are reviewed documentary content without new LLM training.

- [Manual doctoral ES](docs/DOCTORAL_MANUAL_ES.pdf) · [Doctoral manual EN](docs/DOCTORAL_MANUAL_EN.pdf)
- [Identidad y revisión1.2](content/doctoral-manifest.json) · [Casos y atribución](content/doctoral-cases.json)

En Windows pulse **Laboratorio doctoral**; en la web abra la pestaña **Doctorado**.
In Windows choose **Doctoral laboratory**; in the browser open **Doctoral**.
The previous course, mathematical reference reader, model and frozen releases are retained.

Versión 1.1 añade un recorrido matemático independiente basado en Sinnaeve
(2012, DOI 10.1002/cmr.a.21223) y Kuchel et al. (2012, DOI
10.1002/cmr.a.21241). Derivar ecuaciones abre el mismo lector local que usa la
edición web, con MathJax incluido, ejemplos, supuestos, fuentes por página y
ecuación, y un simulador calculado de formas de gradiente. El modelo original
de Beatrix no se reentrena en esta ampliación. Las consultas de los 20 capítulos
matemáticos muestran una guía revisada sin generación LLM; el modelo local
permanece disponible para las 24 lecciones originales. Las dos pruebas de
generación matemática fallidas se conservan, sin reclasificarlas como éxito.

Version 1.1 adds a separately versioned mathematical course based on the two
2012 papers. Derive equations opens the same offline reader as the browser
edition, including local MathJax, worked examples, assumptions, page/equation
citations and a computed gradient-shape laboratory. The existing Beatrix
weights are unchanged. Questions on the 20 mathematical chapters show the
reviewed documentary guide without LLM generation; the local model remains
available for the original 24 lessons. Both failed mathematical generation
runs are preserved, without relabelling them as successes.

The complete PHP-hosted browser edition has local progress, notebook and
exports, and runs without an LLM. The Windows download includes local Beatrix.
Hosting and smaller-model evidence is in `ai/web-feasibility/FEASIBILITY_ES_EN.md`.

La aplicación usa un curso trazable a las 81 diapositivas del archivo aportado, 24 módulos, 48 ejemplos, 48 preguntas y 17 escenas del laboratorio local. Las lecciones explican el objetivo, por qué aparece cada dificultad, cómo hacer la comprobación y cómo interpretar sus límites. Un taller WPF calcula nutación, calibración de gradientes, ventana δ/Δ, convección y condicionamiento ILT.

The application follows 81 source slides through 24 modules, 48 practical examples, 48 graded questions and 17 offline laboratory scenes. Each lesson explains the objective, the difficulty, the procedure and its limits. A native WPF workshop computes nutation, gradient calibration, the δ/Δ acquisition window, convection and ILT conditioning.

- [Guía ES](docs/USER_GUIDE_ES.md) · [English guide](docs/USER_GUIDE_EN.md)
- [Manual ES PDF](docs/MANUAL_ES.pdf) · [English PDF manual](docs/MANUAL_EN.pdf)
- [Procedencia del curso / Course provenance](content/CURRICULUM_PROVENANCE.md)

### Build

Version1.2 source packages use [SOURCE_BUILD_V12.md](SOURCE_BUILD_V12.md).
They include the shared browser runtime and public subset, without model weights.
The Windows portable release includes the original local Beatrix model.

Windows x64, .NET SDK 8 or newer, Microsoft Edge WebView2 Runtime. The portable release includes the .NET runtime. WebView2 remains a prerequisite; it is already installed on the development computer.

```powershell
dotnet restore src/DiffAtOnce.Academy.App/DiffAtOnce.Academy.App.csproj --configfile NuGet.Config
dotnet build src/DiffAtOnce.Academy.App/DiffAtOnce.Academy.App.csproj -c Release --no-restore
dotnet run --project tests/DiffAtOnce.Academy.Tests -c Release
```

`tools/build_package.ps1` publishes a self-contained Windows folder only when the local fine-tuned model's manifest passes its release gate. Preserve the complete folder; do not move the executable alone.

### Learning and provenance

Quiz results and student notes are stored per user under `%LOCALAPPDATA%/DiffAtOnce/Academy/`. No instrument is controlled. Academy reads the source PowerPoint; the final read-only recheck matches all 81 slide images, texts, notes and recorded relationships to the frozen extraction. The current ZIP container has a different hash from the initial read; both identities and the comparison are recorded in `docs/source-input-reaudit.json`. The course/training snapshot is unchanged. Experimental data, TBO calibration and production DiffAtOnce software are not modified. The isolated `lab` copy reuses the reviewed browser models; `lab-source-hashes.json` records their starting versions. Desktop embedding changes only `index.html` and adds `academy-shell.css` / `academy-bridge.js`.

Beatrix runs locally, cites supplied course evidence and receives bounded simulation context. A separate documentary mode is explicitly labelled when a model is absent, incompatible or fails its gate. Training and evaluation artifacts, model identity and reproducibility are documented under `ai/`. Educational checks are software evidence; they do not validate a spectrometer, an experiment or molecular identity.

The algorithm catalogue contains 72 records: 51 pinned-library entries, 9 native Prime routes and 12 context families. They are not 72 distinct algorithms or an exhaustive literature list.
