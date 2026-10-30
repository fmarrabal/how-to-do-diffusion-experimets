# Academy 1.3.1 source / codigo fuente

ES: parche auditado del curso y los motores WPF/web. Consulte los manuales ES/EN
en desktop/academy/docs y las notas de auditoria incluidas. Las fuentes originales
de entrenamiento y sus identidades se conservan: este paquete no realiza un nuevo
ajuste fino ni acredita inferencia por si solo. Los pesos se excluyen; una
compilacion sin pesos compatibles usa guia documental. La web no ejecuta un LLM.

EN: audited curriculum and WPF/browser-engine patch. Read the ES/EN manuals in
desktop/academy/docs and the included audit notes. Original training sources
and identities are retained: source packaging neither retrains a model nor
establishes inference. Weights are excluded; a build without compatible weights
uses documentary guidance. The browser does not run an LLM.

From the extracted root / Desde la raiz extraida:
    cd desktop/academy
    python tools/build_audit_release_v131.py --prepare
    python -m http.server 8918 --bind 127.0.0.1 --directory web

Open / Abrir:
    http://127.0.0.1:8918/index.html?view=research&lang=es
    http://127.0.0.1:8918/index.html?view=research&lang=en

Windows x64, .NET SDK 8 or newer, Microsoft Edge WebView2 Runtime:
    dotnet restore src/DiffAtOnce.Academy.App/DiffAtOnce.Academy.App.csproj --configfile NuGet.Config
    dotnet build src/DiffAtOnce.Academy.App/DiffAtOnce.Academy.App.csproj -c Release --no-restore
    dotnet run --project src/DiffAtOnce.Academy.App -c Release --no-build

Read SOURCE_BUILD_V13.md as the base build guide together with the 1.3.1 audit
notes. --prepare creates pending local metadata only. It is not a public freeze,
model qualification or deployment. Final packaging requires a separate reviewed
web freeze and current root-review hash. Original 1.3.0 artifacts are preserved.
The original public 1.3.0 WEB_RELEASE_SHA256.json is retained verbatim at its
workspace-relative path so the 1.3.1 builder can check its immutability guard.
It is provenance metadata; the former runtime and private QA are not included.

Numerical regression / Regresion numerica (Node.js 18+):
    node web/tests/research-audit-regressions.test.cjs
    node web/tests/research-journey.test.cjs
    node web/tests/spatial-encoding.test.cjs
    node web/tests/research-independent-review.cjs

Optional browser tests require your own Playwright and Edge/Chromium. Manual
authors may set ACADEMY_NODE and ACADEMY_PDFTOPPM, or place node/pdftoppm on PATH.
manual_verify.py also accepts --pdftoppm. Regenerating a manual requires reviewed
captures and a new complete visual review; the final PDFs are supplied directly.

Three authoring-only path transformations are recorded in SOURCE_SHA256.json:
manual provenance commands, research manual Node discovery and Poppler discovery.
The teaching engines, original experimental values and final PDF bytes are not
changed by those transformations. Public data retain their deposition attribution,
license metadata and upstream third-party rights. No blanket reuse license is
created by this archive.

No GGUF/base model, adapters/checkpoints, runtime environments, private papers,
learner records, raw local exports, private QA or compiled binaries are included.
Public-series D fitting remains blocked without documented b. Monte Carlo
intervals identify the monoexponential estimator; they do not quantify ILT peaks
or centroids. Written arguments require human review. The voluntary local pilot
starts without participants and does not establish educational effectiveness.

SOURCE_SHA256.json records exact members and publication transformations. Its
self-hash is excluded; the outer ZIP SHA256 binds it. Every ZIP member is read
back for CRC, size and SHA256. Software/reference checks are not physical
calibration, molecular identity or measured learning outcomes.
