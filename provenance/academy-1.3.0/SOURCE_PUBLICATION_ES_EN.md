# Academy 1.3 source publication / Publicación de fuentes

**EN.** This GitHub distribution derives from the independently verified Academy 1.3 source inventory. WPF/browser teaching engines, model training sources, public original data and all eight PDF manuals retain their frozen bytes. Four source-only publication adjustments are listed in SOURCE_SHA256.json: three manual authoring/QA files now use portable executables; the internal cleanup planner includes the final LF/CRLF parser fix. No teaching calculation or model was changed. The original local frozen archive is preserved and is not this GitHub asset.

**ES.** Esta distribución de GitHub deriva del inventario fuente de Academy 1.3 verificado de forma independiente. Los motores docentes WPF/web, fuentes de entrenamiento, datos públicos originales y los ocho manuales PDF conservan sus bytes congelados. SOURCE_SHA256.json registra cuatro ajustes exclusivos de publicación: tres archivos de autoría/QA de manuales usan ejecutables configurables; el planificador interno de limpieza incorpora la corrección final del lector LF/CRLF. No se cambia ningún cálculo docente ni modelo. El archivo fuente local congelado se conserva; no es este asset de GitHub.

## Runtime and build / Uso y compilación

See desktop/academy/SOURCE_BUILD_V13.md and desktop/academy/README.md. Source builds need no model for documentary guidance; the published Windows package includes the separately verified local Beatrix model. Browser teaching runs without an LLM. Model weights, checkpoints, private papers, learner records, compiled programs and local QA outputs are excluded.

Consulta desktop/academy/SOURCE_BUILD_V13.md y desktop/academy/README.md. Una compilación fuente no necesita pesos para ofrecer guía documental; el paquete Windows publicado incluye el modelo Beatrix local verificado por separado. La web funciona sin LLM. Se excluyen pesos, checkpoints, artículos privados, datos de estudiantes, compilados y resultados locales de QA.

Manual authors: set ACADEMY_NODE to your Node executable, and put Poppler pdftoppm on PATH or set ACADEMY_PDFTOPPM / use --pdftoppm. Existing PDFs are the reviewed final manuals; regeneration requires new screenshots, dependencies and visual review.

Para regenerar manuales, configura ACADEMY_NODE y Poppler mediante PATH, ACADEMY_PDFTOPPM o --pdftoppm. Los PDF incluidos son los manuales finales revisados; su regeneración requiere capturas, dependencias y revisión visual nuevas.

Preserve RIGHTS.md, author credits, third-party notices and public dataset attribution. Numerical/software QA does not establish experimental calibration, chemical identity or educational effectiveness. Public series lacking documented b values cannot be fitted for D.

Conserva RIGHTS.md, créditos, avisos de terceros y atribución de datos públicos. El QA informático/numérico no demuestra calibración física, identidad química ni eficacia docente. Sin b documentada se bloquea el ajuste de D de las series públicas.
