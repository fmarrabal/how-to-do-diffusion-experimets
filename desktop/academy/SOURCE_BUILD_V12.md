# Academy 1.2: compile from source / Compilar desde el código fuente

ES: este paquete preserva el árbol `desktop/academy`. No incluye pesos GGUF,
adaptadores, artículos privados, datos de estudiantes ni el depósito completo
descargado de Figshare. Incluye el curso original, el laboratorio doctoral,
manuales bilingües y un subset DOSY experimental público de 2.12 MB, sin modificar,
con licencia CC BY 4.0, atribución y hashes por archivo. Los 93 pasos guiados
incluyen 79 tareas objetivas y 14 actividades que requieren revisión humana;
ningún argumento escrito recibe nota semántica automática. Las nuevas pistas
son documentales; no se hizo un nuevo ajuste fino de Beatrix.

EN: the archive preserves the `desktop/academy` hierarchy. It excludes GGUF
weights, adapters, private papers, learner data and the full Figshare research
download. It includes the original course, doctoral workbench, bilingual
manuals and an unchanged 2.12 MB public experimental DOSY subset with CC BY 4.0
license, attribution and per-file hashes. The 93 guided steps include 79
objective activities and 14 activities requiring human review; written
arguments are never semantically graded automatically. New hints are
documentary; Beatrix has not received new fine-tuning.

From the extracted `DiffAtOnce-Academy-1.2.0-source` folder:

```powershell
Set-Location desktop/academy
```

Windows x64, .NET SDK 8 or newer, and Microsoft Edge WebView2 Runtime are
required for the full WPF experience. Restore uses the configured official
NuGet source; dependencies are pinned in the projects. Python 3.10+ is needed
only to rebuild the browser bundle; Node.js 18+ is needed for numerical tests.
The application itself does not require Python or Node.js.

```powershell
dotnet restore src/DiffAtOnce.Academy.App/DiffAtOnce.Academy.App.csproj --configfile NuGet.Config
dotnet build src/DiffAtOnce.Academy.App/DiffAtOnce.Academy.App.csproj -c Release --no-restore
dotnet run --project src/DiffAtOnce.Academy.App -c Release --no-build
```

ES: sin GGUF, Beatrix se identifica como guía documental. Las lecciones,
ecuaciones, simulaciones y actividades doctorales funcionan con los archivos
incluidos. WebView2 es necesario para el laboratorio; no controla hardware.
No sustituyas archivos históricos de los informes para aparentar una nueva
evaluación satisfactoria.

EN: without a GGUF, Beatrix identifies itself as a documentary guide. Lessons,
equations, simulations and doctoral activities use included files. WebView2
is needed for the workbench; no hardware is controlled. Never replace
historical evaluation records to make a new result look successful.

The hierarchy lets the browser builder locate the containing source workspace.
From `desktop/academy`, rebuild only the local browser copy:

```powershell
python web/build_web.py --version 1.2.0 --local-assets-only
```

For browser preview, from the same directory:

```powershell
python -m http.server 8918 --bind 127.0.0.1 --directory web
```

Open `http://127.0.0.1:8918/index.html?lang=es` or `?lang=en`.
This localhost preview executes no LLM and needs no PHP server, hosting account
or API key. Public dataset SHA256 validation requires a secure browser context
or localhost. Learner progress is local; selecting Export writes a notebook
without raw FID arrays. Reimport local FIDs after leaving the active session.

For a separate self-contained documentary Windows build, use a fresh directory:

```powershell
if (Test-Path -LiteralPath ../../publish/Academy-1.2-documentary-local) { throw 'Choose a new output directory.' }
dotnet publish src/DiffAtOnce.Academy.App/DiffAtOnce.Academy.App.csproj -c Release -r win-x64 --self-contained true --configfile NuGet.Config -p:PublishTrimmed=false -o ../../publish/Academy-1.2-documentary-local
```

ES: esta compilación no añade un LLM ni equivale a la distribución verificada
con Beatrix. Para disponer del modelo entrenado original, usa el paquete
Windows oficial de Academy 1.2. Conserva `Models/Beatrix` y compara el GGUF con
el SHA256 del manifiesto. El modelo original sirve las 24 lecciones; los
artículos y actividades doctorales nuevos mantienen guías revisadas sin LLM.

EN: this build adds no LLM and does not equal the verified Beatrix distribution.
For the original trained model use the official Academy 1.2 Windows package.
Keep `Models/Beatrix` intact and compare its GGUF with the manifest SHA256.
The original model serves the 24 lessons; new papers and doctoral activities
retain reviewed guides without LLM generation.

Expected original GGUF SHA256:
`b01668cced4c2ec9f28dba333769f0ec2b728e6a18ec7d5eeddb16485fc72fd9`.
Model/training evaluation provenance is included as small metadata in
`ai/release-v1.1/`; its historical version is intentional and unchanged.
No raw model download is necessary to compile this source.

## Read-only experimental case / Caso experimental de sólo lectura

The public subset in `content/doctoral-data/monash-d2o-10` contains the original
`ser.ser`, acquisition metadata, pulse program, gradient shape and saved DOSY
processing parameters. `provenance.json` records every original archive path,
size and SHA256. The repository is Igor Silva, Alasdair McKay and Tanja Junkers,
*Comparison of Oligomer to Polymer Molar Mass Calibrations in Diffusion-Ordered
Spectroscopy (DOSY) – Repository*, Figshare/Monash,
[DOI 10.26180/33075584.v1](https://doi.org/10.26180/33075584.v1),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

The case processes 16 FIDs acquired with `dstegp3s` (double stimulated echo plus
LED). b is explicitly nominal and conditional on the saved TopSpin
`Gamma/Glen/Gdist/difflist`; the nominal gradient value, thermal accuracy and
original sequence correction are not independently validated. Numerical
processing QA is distinct from absolute diffusion/calibration validation.
The student can conclude that data are insufficient for an absolute D.
Retain attribution and the unchanged file hashes when redistributing this subset.

## Verification / Verificación

`SOURCE_SHA256.json` at the extracted root records every selected source file.
The adjacent ZIP `.sha256.json` records the final archive hash and full
CRC/SHA/membership readback. These are software integrity checks, not student
learning or experimental validation.

From `desktop/academy`, numerical tests use only Node.js:

```powershell
node web/tests/doctoral-pedagogy.test.cjs ../../publish/pedagogy-qa.json
```

The test runner resolves the content relative to itself and preserves original
data. The browser QA harnesses are developer tools: configure their documented
Playwright/Chrome paths for your environment. They are not runtime dependencies.
For further scientific and operational limits read the doctoral manual and
the manifests included with the source.

## Rebuild PDF manuals / Reconstruir manuales PDF

ES: los PDF finales se incluyen y se pueden leer directamente. Sus scripts
de autoría también se incluyen, pero las capturas de QA se excluyen del ZIP.
Para reconstruir los manuales, primero genera y revisa nuevas capturas con
`web/doctoral-integrated-test.mjs` y los controles de navegador de `web/tests/`,
configurando Playwright y Chrome para tu equipo. Conserva los nombres y las
rutas que espera `tools/build_doctoral_manuals.py`. Ese script usa Python con
ReportLab, Pillow y las fuentes Segoe UI y DejaVu Sans de Windows. La revisión
estructural requiere pypdf y la visual requiere renderizar e inspeccionar
todas las páginas. La nueva compilación debe verificarse por separado.

EN: the final PDFs are included and readable directly. Authoring scripts are
included, while QA screenshots are excluded from the ZIP. To rebuild the
manuals, first generate and review fresh captures with
`web/doctoral-integrated-test.mjs` and browser checks in `web/tests/`, configuring
Playwright and Chrome for your machine. Retain the filenames and paths expected
by `tools/build_doctoral_manuals.py`. That script requires Python with ReportLab,
Pillow and Windows Segoe UI/DejaVu Sans fonts. Structural review requires pypdf;
visual review requires rendering and inspecting every page. Verify the newly
authored PDFs separately.
