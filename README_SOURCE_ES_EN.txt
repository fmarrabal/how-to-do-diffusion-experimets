DiffAtOnce Academy 1.3 - source / codigo fuente

ES: este ZIP preserva desktop/academy con el codigo WPF, el runtime web compartido,
el recorrido de investigacion, el piloto local voluntario, manuales ES/EN y casos
publicos con licencia CC BY 4.0, atribucion y SHA256. No incluye pesos de modelos,
adaptadores, entornos, articulos privados, datos de estudiantes, QA ni compilados.
Las series publicas son datos reales; una agrupacion del deposito no demuestra
controles de conveccion/temperatura ni replicas identicas. Sin b documentados no
se obtiene D. Los datos originales estan intactos; no se incluye el deposito completo.

EN: this archive preserves desktop/academy with WPF source, the shared browser
runtime, research pathway, voluntary local pilot, ES/EN manuals and licensed
CC BY 4.0 public cases with attribution and SHA256. It excludes model weights,
adapters, environments, private papers, learner data, QA outputs and binaries.
Repository grouping does not establish paired convection/temperature controls.
Undocumented b values cannot produce a validated D. Original files remain intact.

From this extracted folder / Desde esta carpeta:
    cd desktop/academy
    python tools/build_research_release_v13.py --prepare
    python -m http.server 8918 --bind 127.0.0.1 --directory web

Browser / Navegador:
    http://127.0.0.1:8918/index.html?view=research&lang=es
    http://127.0.0.1:8918/index.html?view=research&lang=en

Windows x64 + .NET SDK 8 or newer + Microsoft Edge WebView2 Runtime:
    dotnet restore src/DiffAtOnce.Academy.App/DiffAtOnce.Academy.App.csproj --configfile NuGet.Config
    dotnet build src/DiffAtOnce.Academy.App/DiffAtOnce.Academy.App.csproj -c Release --no-restore
    dotnet run --project src/DiffAtOnce.Academy.App -c Release --no-build

ES: sin pesos compatibles, Beatrix identifica honestamente la guia documental.
El paquete fuente no acredita inferencia LLM ni un nuevo ajuste fino. Los metadatos
historicos del tutor conservan sus identidades originales; no son nuevos resultados.
El navegador no ejecuta un LLM. El piloto empieza con cero participantes y requiere
consentimiento explicito; no se incluyen alumnos ni resultados. La retencion exige
siete dias reales. Los argumentos se revisan por separado mediante rubrica humana.

EN: without compatible weights, Beatrix identifies documentary guidance honestly.
Source packaging does not establish LLM inference or a new fine-tune. Historical
tutor metadata remain historical. The browser has no LLM. The pilot starts with
zero participants, requires explicit consent and includes no learners/outcomes.
Delayed retention requires seven real days; prose uses a separate human rubric.

Numerical checks / Pruebas numericas (Node.js 18+):
    node web/tests/research-journey.test.cjs
    node web/tests/spatial-encoding.test.cjs
    node web/tests/learning-path.test.cjs
    node web/tests/research-pilot-panel.test.cjs
    node web/tests/research-independent-review.cjs

Optional browser harnesses require Playwright and Edge/Chromium. Where an original
development harness referenced the author's local Playwright module, this archive
uses require('playwright'); configure/install your own official testing dependency.
No Node/Python/training environment is required to use the released WPF application.

--prepare creates local pending-review metadata only. Public freeze additionally
requires an explicit root review JSON with current engine, QA and final-manual
hashes. Previous final releases are not replaced. Software integrity and analytic
checks are not hardware calibration, chemical identity or educational efficacy.

Read Docs/ACADEMY_MANUAL_ES.pdf and Docs/RESEARCH_MANUAL_ES.pdf in the portable
application, or docs/ACADEMY_MANUAL_EN.pdf and docs/RESEARCH_MANUAL_EN.pdf here.
SOURCE_SHA256.json records exact selected members, transformations and provenance.
The adjacent ZIP .sha256.json verifies the final archive and full member readback.
