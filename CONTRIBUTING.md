# Contributing / Colaborar

## English

Use GitHub issues for a reproducible problem, an English/Spanish documentation correction or a methodological suggestion. Include tool/version, operating system, TopSpin version if relevant, the exact command or menu action, expected/observed behaviour, and a minimal **synthetic or authorised anonymised** example. Never upload patient/customer information, passwords, tokens, complete instrument folders or unpublished data without permission.

Run `python python/run_tests.py` before proposing code changes. Keep preparation-only and acquisition modes distinct. Preserve original datasets, units, reference conditions, sequence mapping and provenance. Label simulations and mocked hardware. Report any real-instrument validation separately, including the operator-approved conditions. Do not add automatic acquisition, writes to global calibrations or silent point removal to a documentation-only change.

GitHub Actions workflows are not included or activated. Tests run locally. The maintainer must review scientific changes and any future automation separately.

## Español

Use las incidencias de GitHub para un problema reproducible, una corrección documental EN/ES o una sugerencia metodológica. Indique herramienta/versión, sistema operativo, versión de TopSpin si corresponde, comando o acción del menú, resultado esperado/observado y un ejemplo mínimo **sintético o anonimizado con autorización**. No suba datos personales/de clientes, contraseñas, tokens, carpetas completas del equipo ni datos inéditos sin permiso.

Ejecute `python python/run_tests.py` antes de proponer cambios. Separe preparación y adquisición. Conserve originales, unidades, condiciones de referencia, correspondencia de la secuencia y procedencia. Identifique simulaciones y hardware simulado. Informe por separado de la validación instrumental real y sus condiciones autorizadas por el operador. Un cambio documental no debe introducir adquisición automática, escritura global de calibraciones ni eliminación silenciosa de puntos.

No se incluyen ni activan workflows de GitHub Actions. Las pruebas se ejecutan localmente. Los cambios científicos y cualquier futura automatización requieren revisión independiente del mantenedor.
