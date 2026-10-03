# Public-edition provenance / Procedencia de la edición pública

## English

This repository publishes a derivative **public edition of bilingual workshop v8**. Each language retains all 45 slides: 25 main slides and 20 hidden appendices. The seven videos per deck, slide appearance, editable charts/tables and numerical evidence are retained. The two PDF files are unchanged static exports of those slides. Complete slide/notes text is additionally available in GitHub-readable Markdown.

Only local textual paths in PowerPoint speaker notes were mechanically replaced with an installation-relative Bruker document name or a labelled local-source filename. No slide geometry, chart, embedded workbook, image or video bytes were changed. Text/JSON/HTML derivatives omit private paths and the probe serial, and public text uses LF line endings for reproducible Git checkouts. Original snapshots are read-only and remain in the maintainer's workspace. Original raster screenshot labels, sample case IDs and public author/contact credits remain as part of the teaching evidence.

[presentation-manifest.json](presentation-manifest.json) records source archive/member hashes, public hashes, changed note parts and omissions. The repository-wide file manifest can be checked with `python tools/audit_public_repo.py`. It records distribution integrity, not physical validation.

Nested old Python packages and private-environment build/replay scripts are not copied. Their relevant runnable Bruker functionality is supplied as reviewed source in `python/`, with rebuildable standalone bundles, safety guards and mocked tests. The author's historical calibration is described as evidence in the workshop but is **not pre-applied to another instrument**. The public bundle carries only the conditional sequence-model identity needed for reviewed conversions.

Full publisher papers, original FID/SER/pdata datasets, proprietary Bruker code, desktop app binaries, accounts, credentials and private QA logs are excluded. Derived case data and plots are included. Any numerical or experimental limitations stated in the original teaching materials remain in the public edition.

## Español

Este repositorio publica una **edición pública derivada del workshop bilingüe v8**. Cada idioma conserva las 45 diapositivas: 25 principales y 20 apéndices ocultos. Mantiene los siete vídeos por presentación, apariencia, gráficos/tablas editables y evidencia numérica. Los dos PDF son exportaciones estáticas sin cambios. Además, el texto de diapositivas y notas puede leerse completo en GitHub.

Únicamente se sustituyeron mecánicamente las rutas textuales locales de las notas PowerPoint por el nombre del documento Bruker relativo a la instalación o un nombre de fuente local identificado. No cambian geometría, gráficos, libros incrustados, imágenes ni vídeos. Los derivados TXT/JSON/HTML omiten rutas privadas y el serial de la sonda; el texto público usa finales de línea LF para descargas Git reproducibles. Los originales permanecen intactos en el espacio de trabajo del mantenedor. Las etiquetas raster de capturas, identificadores de casos y créditos/contactos públicos forman parte de la evidencia docente y se conservan.

[presentation-manifest.json](presentation-manifest.json) registra hashes del archivo original y sus miembros, hashes públicos, notas modificadas y omisiones. El manifiesto completo se comprueba con `python tools/audit_public_repo.py`. Comprueba integridad de distribución, no validación física.

No se copian ZIP Python antiguos anidados ni constructores/replays dependientes del entorno privado. Las funcionalidades Bruker pertinentes se suministran como fuentes revisadas en `python/`, con bundles reconstruibles, comprobaciones y pruebas simuladas. La calibración histórica del autor se describe como evidencia docente, pero **no se aplica previamente a otro instrumento**. El bundle público incorpora únicamente la identidad del modelo de secuencia condicionado necesaria para revisar las conversiones.

Se excluyen artículos editoriales completos, originales FID/SER/pdata, código propietario Bruker, binarios de aplicaciones, cuentas, credenciales y QA privada. Se incluyen datos y figuras derivados. Se mantienen los límites numéricos y experimentales declarados en el material original.
