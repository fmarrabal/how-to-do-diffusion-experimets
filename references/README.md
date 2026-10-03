# References / Referencias

The complete bilingual bibliography is preserved in [REFERENCIAS_ES_EN.txt](../materials/presenter/REFERENCIAS_ES_EN.txt), [the 45-slide content](../docs/en/presentation-content.md), [Spanish slide content](../docs/es/presentation-content.md), and [the method catalogue](../materials/catalogo/ilt_algorithm_catalog_bilingual.json). References are attached to the relevant claims and examples in speaker notes.

La bibliografía bilingüe completa se conserva en esos documentos. Las notas vinculan las fuentes con las afirmaciones y ejemplos pertinentes. Los registros del catálogo se solapan; no representan algoritmos DOSY independientes en todos los casos.

`[local-source: filename]` in historical notes identifies a source originally consulted in the research workspace, not a downloadable file or a runnable path. Supplied repository files have actual relative links. / Esa etiqueta identifica una fuente histórica del espacio de investigación, no un archivo descargable ni una ruta ejecutable; los archivos incluidos tienen enlaces relativos reales.

## Primary documentation and foundational sources

- Bruker, [TopSpin Python Interface](https://www.bruker.com/en/products-and-solutions/mr/nmr-software/topspin/topspin-python-interface.html). Consulted 2026-10-03. Distinguishes integrated Jython 2.7 from the newer external Python 3 API. The repository targets the former. / Distingue Jython integrado de la API externa moderna; este repositorio utiliza el primero.
- E. O. Stejskal and J. E. Tanner, *Spin Diffusion Measurements: Spin Echoes in the Presence of a Time-Dependent Field Gradient* (1965), [DOI](https://doi.org/10.1063/1.1695690).
- D. Sinnaeve, *The Stejskal–Tanner Equation Generalized for Any Gradient Shape* (2012), [DOI](https://doi.org/10.1002/cmr.a.21223). The slide timing expressions are sequence-dependent. / Las expresiones de tiempos dependen de la secuencia.
- R. Mills, *Self-Diffusion in Normal and Heavy Water in the Range 1–45°* (1973), [DOI](https://doi.org/10.1021/j100624a025). Reference conditions and approximate thermal interpolation must remain explicit. / Mantener explícitas las condiciones de referencia y las aproximaciones térmicas.

## Instrument documentation

The workshop consulted the Python manual, DOSY/Diffusion tutorial, acquisition/processing references, data-format documentation and the relevant AU/pulse-program files supplied with TopSpin 3.8.0. Obtain them from your licensed installation. Their installation-relative names remain in the notes; full proprietary copies are not included. Their presence in one installation does not validate a live acquisition in another version.

El workshop consultó esos manuales y fuentes de TopSpin 3.8.0. Obtenga los documentos en su instalación autorizada. Las notas conservan sus nombres relativos; no se incluyen copias completas propietarias. La revisión documental de una instalación no valida una adquisición real en otra versión.

## SPEN, ultrafast and method-specific sources

Use the full [advanced diffusion source list](../materials/simulaciones/v5/advanced_uf.sources.json), the [catalogue](../materials/catalogo/ilt_algorithm_catalog_bilingual.json) and the notes of slides 23–24 and their appendices. The cited literature predates the current prototype. Historical data and published methods are distinguished from the unvalidated new development.

Consulte esas listas completas y las notas. La literatura citada es previa al prototipo actual. Se distinguen los datos históricos y métodos publicados del desarrollo nuevo sin validar. No se redistribuyen artículos completos.
