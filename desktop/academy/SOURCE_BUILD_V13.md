# Academy 1.3: compilar desde fuentes / build from source

## Alcance del paquete / Package scope

**ES.** El árbol `desktop/academy` contiene las fuentes WPF, el runtime web compartido, las doce etapas de investigación, el lector matemático, el laboratorio doctoral, pruebas numéricas, manuales ES/EN y datos públicos con licencia y procedencia. No incluye GGUF, adaptadores/checkpoints, entornos, artículos privados, datos de estudiantes, resultados de QA, compilados anteriores ni el archivo completo descargado de Figshare. No se necesita un modelo para reconstruir el curso y la guía documental.

**EN.** The `desktop/academy` tree contains WPF source, the shared browser runtime, twelve research stages, mathematics reader, doctoral laboratory, numerical tests, ES/EN manuals and licensed public data with provenance. It excludes GGUF weights, adapters/checkpoints, environments, private papers, learner records, QA outputs, previous binaries and the full Figshare download. Rebuilding the course and documentary guide requires no model.

Desde la raíz del ZIP fuente extraído / From the extracted source ZIP root:

```powershell
Set-Location desktop/academy
```

Requisitos de desarrollo / Development requirements:

- Windows x64, .NET SDK 8 o posterior / or newer, Microsoft Edge WebView2 Runtime para / for the WPF research window.
- Python 3.10+ para preparar el bundle web / to prepare the browser bundle.
- Node.js 18+ para pruebas numéricas CommonJS / for CommonJS numerical checks.
- Playwright y Edge/Chromium sólo para controles de navegador opcionales / only for optional browser checks. Configure a compatible Node.js version for those harnesses.

El usuario del paquete WPF publicado no necesita Python, Node.js, herramientas de entrenamiento ni una clave API. El runtime .NET puede incluirse con `dotnet publish`; WebView2 sigue siendo un requisito separado.

Released WPF users need no Python, Node.js, training tools or API key. `dotnet publish` can include the .NET runtime; WebView2 remains a separate prerequisite.

## Preparar y abrir la web / Prepare and preview the browser edition

Desde `desktop/academy` / From `desktop/academy`:

```powershell
python tools/build_research_release_v13.py --inspect
python tools/build_research_release_v13.py --prepare
python -m http.server 8918 --bind 127.0.0.1 --directory web
```

Abre / Open:

```text
http://127.0.0.1:8918/index.html?view=research&lang=es
http://127.0.0.1:8918/index.html?view=research&lang=en
```

**ES.** `--prepare` copia contenido público y manuales, calcula la identidad SHA256 real de investigación y genera metadatos locales con revisión pendiente. No cambia los motores fuente, no publica, no aprueba el tutor ni modifica versiones finales existentes. No uses `web/build_web.py --version 1.2.0` para preparar 1.3. Para comprobar hashes de FID se necesita localhost o un contexto seguro HTTPS. Esta vista previa no requiere PHP, alojamiento ni LLM.

**EN.** `--prepare` copies public content and manuals, computes the actual research SHA256 identity and writes local pending-review metadata. It does not change source engines, publish, approve the tutor or replace existing final versions. Do not use `web/build_web.py --version 1.2.0` to prepare 1.3. FID hash checks require localhost or a secure HTTPS context. Preview needs no PHP, hosting account or LLM.

El progreso se guarda en ese navegador/origen; exporta una copia antes de cambiar de equipo o puerto. Los expedientes compactos no incluyen los FID originales completos: conserva los originales y reimpórtalos cuando se necesiten.

Progress belongs to that browser/origin; export a copy before switching computer or port. Compact portfolios do not embed complete original FIDs: retain originals and re-import when required.

## Compilar y ejecutar WPF / Build and run WPF

```powershell
dotnet restore src/DiffAtOnce.Academy.App/DiffAtOnce.Academy.App.csproj --configfile NuGet.Config
dotnet build src/DiffAtOnce.Academy.App/DiffAtOnce.Academy.App.csproj -c Release --no-restore
dotnet run --project src/DiffAtOnce.Academy.App -c Release --no-build
```

En la ventana principal elige **Investigación continua / Research studio**. WPF incrusta los mismos motores web y permite trabajar sin conexión con fuentes locales. Los resultados y notas de usuario se guardan bajo `%LOCALAPPDATA%/DiffAtOnce/Academy/`; no se deben incluir en paquetes fuente o públicos.

Choose **Research studio / Investigación continua** in the main window. WPF embeds the same browser engines and supports offline work with local sources. User progress and notes are stored under `%LOCALAPPDATA%/DiffAtOnce/Academy/`; exclude them from source and public packages.

Para una carpeta local documental autocontenida, comprueba espacio libre y elige un destino nuevo. Ejemplo explícito; no sustituye un paquete verificado / For a local self-contained documentary folder, check free space and choose a fresh destination. Explicit example; it does not replace a verified release:

```powershell
$academyLocalOutput = '../publish/Academy-1.3-documentary-local'
if (Test-Path -LiteralPath $academyLocalOutput) { throw 'Choose a new output directory; preserve the existing folder.' }
dotnet publish src/DiffAtOnce.Academy.App/DiffAtOnce.Academy.App.csproj -c Release -r win-x64 --self-contained true --configfile NuGet.Config -p:PublishTrimmed=false -o $academyLocalOutput
```

Conserva el directorio completo y verifica el resultado antes de distribuirlo. No copies modelos o runtimes completos a cada arnés de prueba. Consulta la política de retención del proyecto antes de crear otro compilado; nunca borres el vigente sin comprobar su sustituto.

Keep the complete directory and verify it before distribution. Do not copy models or full runtimes into each test harness. Follow project retention policy before creating another build; never remove a current release before checking its replacement.

## Tutor documental y modelo local / Documentary tutor and local model

**ES.** Sin pesos compatibles se muestra **Guía documental**. La web no ejecuta un LLM. La inferencia local WPF necesita un manifiesto con hashes exactos del modelo, contenido, entrenamiento y evaluación, revisión científica y evaluación nativa CPU aprobadas para ese contenido. Un modelo entrenado o una prueba de software aislada no acreditan esas condiciones. Este documento no afirma aprobación nativa de R4. No cambies banderas o informes para saltarte un gate. Los metadatos históricos conservan sus identidades originales y no son evaluaciones nuevas.

**EN.** Without compatible weights, the app shows **Documentary guide**. The browser runs no LLM. Local WPF inference requires a manifest binding exact model, content, training and evaluation hashes, scientific review and an approved native CPU evaluation for that content. Trained weights or an isolated software check do not establish those conditions. This document does not assert native approval of R4. Never change flags or reports to bypass a gate. Historical metadata retain their original identities and are not new evaluations.

Las consultas nativas usan un ID único y un hash del caso/etapa/cálculo. Cambiar de contexto cancela o descarta la respuesta pendiente; las respuestas no escriben resultados numéricos. Un arnés fake-native sólo verifica ese contrato de software: no demuestra inferencia de un modelo.

Native requests carry a unique ID and a case/stage/calculation hash. Context changes cancel or discard pending replies; replies do not write numerical results. A fake-native harness verifies only that software contract, not model inference.

## Verificación reproducible / Reproducible checks

```powershell
dotnet run --project tests/DiffAtOnce.Academy.Tests -c Release
node web/tests/research-journey.test.cjs
node web/tests/spatial-encoding.test.cjs
node web/tests/learning-path.test.cjs
node web/tests/research-pilot-panel.test.cjs
node web/tests/research-independent-review.cjs
```

Las pruebas analíticas y sintéticas comprueban software y supuestos acotados. No prueban calibración física, identidad molecular, cobertura experimental ni eficacia docente. Los arneses de navegador de `web/tests/` requieren instalar/configurar Playwright y Edge/Chromium; los puertos y dependencias de autoría se ajustan para cada equipo. El paquete fuente excluye capturas y resultados de QA; hay que generarlos y revisarlos de nuevo.

Analytical and synthetic tests check software and bounded assumptions. They do not establish physical calibration, molecular identity, experimental coverage or educational efficacy. Browser harnesses in `web/tests/` require configured Playwright and Edge/Chromium; adapt authoring ports/dependencies for your machine. Source packages exclude QA captures and results, which must be generated and reviewed anew.

## Datos públicos, incertidumbre y piloto / Public data, uncertainty and pilot

La [biblioteca 1.3](content/research-library.json) identifica ocho series, 72 archivos originales, CC BY 4.0, atribución y SHA256. Véase un [manifiesto por serie](content/research-data/monash-pma1-10/provenance.json). Fuente: Igor Silva, Alasdair McKay y Tanja Junkers, *Comparison of Oligomer to Polymer Molar Mass Calibrations in Diffusion-Ordered Spectroscopy (DOSY) – Repository*, Monash/Figshare, DOI `10.26180/33075584.v1`. El caso histórico [D₂O 1.2](content/doctoral-data/monash-d2o-10/provenance.json) se conserva aparte.

The [1.3 library](content/research-library.json) identifies eight series, 72 original files, CC BY 4.0, attribution and SHA256. A [per-series manifest](content/research-data/monash-pma1-10/provenance.json) records provenance. Source: Igor Silva, Alasdair McKay and Tanja Junkers, the Monash/Figshare repository named above, DOI `10.26180/33075584.v1`. The historical [1.2 D₂O case](content/doctoral-data/monash-d2o-10/provenance.json) remains separate.

**ES.** No inventes b usando el índice de fila o un gradiente nominal. Sin b documentada se bloquea D; con b aportada, D es condicional a su procedencia, secuencia y calibración. La agrupación del repositorio no demuestra controles pareados de temperatura/convección. El Monte Carlo conserva el error de gradiente compartido entre b/frecuencias y la temperatura correlacionada, separándolos de ruido, procesado y modelo; no atribuye cobertura experimental. El piloto local sólo registra un participante tras consentimiento explícito. Pretest, postest y retención usan formas distintas; la retención exige siete días reales. Los argumentos requieren rúbrica humana. El software no incluye un estudio real ni demuestra eficacia.

**EN.** Never invent b from row number or a nominal gradient. Undocumented b blocks D; user-supplied b makes D conditional on provenance, sequence and calibration. Repository grouping does not establish paired temperature/convection controls. Monte Carlo retains gradient errors shared across b/frequencies and correlated temperature, separately from noise, processing and model assumptions; it establishes no experimental coverage. The local pilot records a participant only after explicit consent. Pretest, post-test and retention use distinct forms; retention requires seven real days. Arguments use a human rubric. The software includes no real study and establishes no efficacy.

## Manuales / Manuals

Los PDF finales se leen directamente / Read the final PDFs directly:

- Manual completo, 68 páginas / Complete manual, 68 pages: [ES](docs/ACADEMY_MANUAL_ES.pdf) · [EN](docs/ACADEMY_MANUAL_EN.pdf).
- Investigación, 22 páginas / Research, 22 pages: [ES](docs/RESEARCH_MANUAL_ES.pdf) · [EN](docs/RESEARCH_MANUAL_EN.pdf).
- Históricos / Historical: [doctoral ES](docs/DOCTORAL_MANUAL_ES.pdf) · [doctoral EN](docs/DOCTORAL_MANUAL_EN.pdf) · [base ES](docs/MANUAL_ES.pdf) · [base EN](docs/MANUAL_EN.pdf).

En el portable se copian a `Docs/`. El manual completo identifica las secciones históricas y sus límites. Los scripts de autoría [build_research_manuals_v13.py](tools/build_research_manuals_v13.py) y [consolidate_academy_manuals_v13.py](tools/consolidate_academy_manuals_v13.py) requieren capturas nuevas revisadas y sus dependencias Python (ReportLab, Pillow, pypdf y fuentes de autoría). Las capturas no vienen en el ZIP fuente; consulta los argumentos y rutas de cada script. Reconstruir exige volver a revisar estructura, enlaces y todas las páginas renderizadas: un script que termina no sustituye la revisión visual.

Portable packages copy them to `Docs/`. The complete manual identifies historical sections and their limits. The authoring scripts linked above require newly reviewed captures and Python dependencies (ReportLab, Pillow, pypdf and authoring fonts). Captures are absent from the source ZIP; inspect each script's arguments and paths. A rebuild requires fresh structural, link and rendered-page review: successful script execution does not replace visual review.

## Congelar y empaquetar una entrega / Freeze and package a release

Sólo para mantenedores después de la revisión / Maintainers only, after review:

```powershell
python tools/build_research_release_v13.py --inspect
python tools/package_research_source_v13.py --inspect
```

**ES.** La congelación web exige un JSON de revisión real con `passed:true`, hashes actuales de motores, controles QA concretos aprobados y los cuatro manuales finales. El hash SHA256 de ese JSON se pasa de forma explícita. El script comprueba contenido y hashes; no basta una bandera arbitraria. Después se puede generar el ZIP fuente contra esa web congelada, con lectura completa de miembros/CRC/SHA y recibo adyacente. Los destinos finales existentes se conservan. No se ejecuta despliegue desde estos comandos.

**EN.** Web freeze requires a genuine review JSON with `passed:true`, current engine hashes, concrete passing QA checks and all four final manuals. Pass that JSON's SHA256 explicitly. The script checks content and hashes; an arbitrary flag is insufficient. Source packaging then uses that frozen web tree, with full member/CRC/SHA readback and an adjacent receipt. Existing final targets are preserved. These commands do not deploy.

Ejemplo de forma de invocación; usa la ruta de una revisión ya aceptada / Invocation pattern; use an already accepted review file:

```powershell
$academyReviewPath = 'path/to/accepted-review.json'
$academyReviewSha = (Get-FileHash -LiteralPath $academyReviewPath -Algorithm SHA256).Hash.ToLowerInvariant()
python tools/build_research_release_v13.py --freeze --review $academyReviewPath --review-sha256 $academyReviewSha
python tools/package_research_source_v13.py --output ../publish/DiffAtOnce-Academy-1.3.0-source.zip --review $academyReviewPath --review-sha256 $academyReviewSha
```

El destino web predeterminado es `website/release/public_html/assets/academy/v1.3.0/` dentro del workspace, fuera de estas fuentes. `WEB_RELEASE_SHA256.json` registra la copia pública exacta; `researchContentSha256` vincula la identidad de investigación al ámbito de aprendizaje. El ZIP contiene `SOURCE_SHA256.json`; su recibo `.sha256.json` registra el archivo final y la verificación completa. Estos manifiestos prueban integridad de software, no publicación pública, aprobación de R4 ni validación científica/educativa.

The default web target is `website/release/public_html/assets/academy/v1.3.0/` inside the workspace and outside these sources. `WEB_RELEASE_SHA256.json` records exact public membership; `researchContentSha256` binds research identity to the learning scope. The ZIP contains `SOURCE_SHA256.json`; its adjacent `.sha256.json` receipt records the final archive and full readback. These manifests establish software integrity, not public deployment, R4 approval or scientific/educational validation.

Las instrucciones anteriores de [SOURCE_BUILD_V12.md](SOURCE_BUILD_V12.md) son históricas. Conservar datos originales, atribución y calibraciones del usuario es obligatorio; TBO, KK2 y el software de producción están fuera del alcance de esta reconstrucción.

The earlier [SOURCE_BUILD_V12.md](SOURCE_BUILD_V12.md) instructions are historical. Retain experimental originals, attribution and user calibrations; TBO, KK2 and production software remain outside this rebuild.
