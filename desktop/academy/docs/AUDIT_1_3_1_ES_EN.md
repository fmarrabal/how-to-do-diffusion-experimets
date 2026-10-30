# DiffAtOnce Academy 1.3.1 - Audit corrections / Correcciones de auditoría

## Español

Esta corrección revisa los ejemplos y la interpretación de resultados de Academy 1.3 en WPF y web. Los cuatro PDF de uso vigente incluyen un suplemento inicial 1.3.1; el cuerpo 1.3 y sus capturas se conservan como fuente histórica. Sus páginas mantienen la numeración impresa anterior y los enlaces internos se trasladan a la posición nueva. Lee primero el suplemento: sus precisiones prevalecen sobre las instrucciones conservadas.

- **Un intervalo pertenece a un estimador.** El Monte Carlo vuelve a ajustar el modelo monoexponencial de referencia. Su D e intervalo se identifican por separado. Si se selecciona NNLS, Tikhonov o L1, el centroide ILT es otra cantidad: el intervalo mono no cubre el centroide, la forma, los máximos ni el número de componentes. No se calcula incertidumbre de una distribución ILT en ese panel. Un intervalo estrecho no resuelve un modelo inadecuado.
- **La lista de valores singulares puede ser incompleta para las columnas.** Una matriz de 20 observaciones y 64 valores D tiene rango como máximo 20 y al menos 44 direcciones nulas derechas. Aunque sus 20 valores singulares devueltos sean no nulos, no se demuestra una distribución única. El aviso incorpora ese espacio no resuelto; no se interpreta como número de moléculas ni como imposibilidad de cualquier solución positiva.
- **Orden, signo y controles deben ser coherentes.** El procesado por señal y Monte Carlo usan la referencia de menor b. Reordenar las mismas parejas (b, señal) no debe crear o borrar picos por elegir otra fila de referencia. Un control reservado conserva la referencia con signo y el procesado declarado; no sustituye señales por valores absolutos. Cambiar físicamente el orden de adquisición sí puede revelar deriva o cinética.
- **Los datos importados no traen una calibración demostrada.** Importar una serie y sus metadatos no acredita una referencia independiente. La procedencia, la escala aplicada y la evidencia disponible deben permanecer explícitas; una escala introducida por el usuario sigue siendo condicional. No se inventan b cuando faltan.
- **Una entrada inválida no es un cero.** Un gradiente vacío o no numérico y parámetros de referencia/fase no finitos se rechazan con explicación ES/EN. Valores cuyo paso a SI desborde la representación tampoco se aceptan. Ajustar datos a b no nulo usa una referencia desplazada al menor b para estabilidad; si la amplitud extrapolada a b=0 no se puede representar, se informa como no disponible en vez de mostrar NaN como resultado físico.
- **Dos erratas docentes concretas.** En `temperature-standard/factors`, 0.89 x 293/301 = 0.86634551495 se redondea a **0.8663**, en ambos idiomas. La D corregida de 0.33 x 0.86634551495 = **0.2859** (en las unidades 10^-9 m²/s del ejemplo) no cambia. En la nota española de Kuchel 2012, ecuación 38, el texto correcto es **g0=0**, no `g00`; la ecuación matemática no cambia.
- **Validación trazable, con alcance.** Se conservan los originales experimentales, los PDF fuente y los informes históricos. El validador distingue el hash del contenedor PPTX de la coincidencia fresca de sus 81 diapositivas registradas. Las pruebas de interfaz y código verifican contratos y casos simulados; no constituyen calibración física, identificación química ni un estudio de eficacia docente. La disponibilidad de fuentes o manuales tampoco sustituye la evaluación nativa necesaria para usar Beatrix.

### Qué comprobar al aprender

1. Explica el modelo y las unidades antes de ajustar. Usa el mismo subconjunto de datos, fase y referencia al comparar métodos.
2. Lee el nombre del estimador junto al intervalo. Si estudias una distribución, compara regularización, malla, residuos y alternativas compatibles; no le atribuyas el intervalo del ajuste mono.
3. Introduce una entrada inválida y comprueba el rechazo. Invierte el orden de las mismas filas y distingue esa operación de volver a adquirir una rampa invertida.
4. Conserva procedencia y originales al importar, y diseña un control que pueda refutar la interpretación. No confundas un ajuste reproducible con una medida calibrada.

## English

This patch reviews examples and result interpretation in Academy 1.3 for WPF and the browser. The four current-use PDFs include an opening 1.3.1 supplement; the 1.3 body and screenshots remain an identified historical source. Printed section numbering is retained and internal links are rebased to their new positions. Read the supplement first: its qualifications supersede retained instructions.

- **An interval belongs to an estimator.** Monte Carlo refits the reference monoexponential model. Its D and interval are identified separately. Selecting NNLS, Tikhonov or L1 produces a different ILT centroid: the mono interval does not cover that centroid, distribution shape, peaks or component count. The panel does not compute ILT distribution uncertainty. A narrow interval does not resolve an inadequate model.
- **The returned singular list may not span the columns.** A matrix with 20 observations and 64 D values has rank at most 20 and at least 44 right-nullspace directions. Even if all 20 returned singular values are nonzero, a unique distribution is not established. The warning includes that unresolved space; it is neither a molecule count nor a claim that every positive solution is impossible.
- **Ordering, sign and controls must agree.** Per-signal processing and Monte Carlo use the minimum-b reference. Reordering the same (b, signal) pairs must not create or erase peaks by changing the reference row. A held-out control retains the signed reference and declared processing; signals are not replaced by absolute values. Physically changing acquisition order can still expose drift or kinetics.
- **Imported data do not establish calibration.** Importing a series and metadata does not supply an independent reference. Provenance, applied scale and available evidence remain explicit; a user-entered scale remains conditional. Missing b values are not invented.
- **An invalid input is not zero.** Empty/non-numeric gradients and non-finite reference/phase parameters are rejected with ES/EN explanations. Values overflowing the SI representation are rejected too. Fitting nonzero-b data uses a minimum-b shifted reference for stability; if the extrapolated b=0 amplitude is not representable, it is reported unavailable rather than displaying NaN as a physical result.
- **Two specific teaching corrections.** In `temperature-standard/factors`, 0.89 x 293/301 = 0.86634551495 rounds to **0.8663** in both languages. Corrected D, 0.33 x 0.86634551495 = **0.2859** (in the example's 10^-9 m²/s units), is unchanged. The Spanish note for Kuchel 2012 equation 38 now says **g0=0**, replacing `g00`; the mathematical equation is unchanged.
- **Traceable, bounded verification.** Experimental originals, source PDFs and historical reports are preserved. The validator separates PPTX container hash identity from fresh agreement of its 81 recorded slides. UI/code checks verify contracts and synthetic cases; they are not physical calibration, chemical identification or an educational-efficacy study. Source/manual availability does not replace the native evaluation required for using Beatrix.

### What to check while learning

1. Explain the model and units before fitting. Use the same data subset, phase and reference when comparing methods.
2. Read the estimator name next to an interval. For a distribution, inspect regularization, grid, residuals and compatible alternatives; do not assign it the mono-fit interval.
3. Enter an invalid value and verify rejection. Reverse the same rows and distinguish that operation from acquiring a physically reversed ramp.
4. Preserve provenance and originals on import and design a control that can refute the interpretation. A reproducible fit is not a calibrated measurement.

## References / Referencias

The general diffusion and phase-history derivations retain their source references: [Sinnaeve 2012](https://doi.org/10.1002/cmr.a.21223), [Kuchel et al. 2012](https://doi.org/10.1002/cmr.a.21241) and [Torrey's Bloch diffusion equations](https://journals.aps.org/pr/abstract/10.1103/PhysRev.104.563). The advanced teaching models are bounded illustrations; the [SPEN-DOSY article](https://pubs.rsc.org/en/content/articlehtml/2021/cc/d0cc07757g) and [ultrafast diffusion-exchange article](https://www.nature.com/articles/s41467-020-17079-7) do not make every Academy surrogate a validated implementation of those sequences. No full article or private paper page is redistributed.

Las derivaciones generales conservan esas fuentes. Los modelos avanzados son ilustraciones con supuestos declarados; citar artículos SPEN-DOSY o de intercambio ultrafast no valida automáticamente cada modelo simplificado de Academy como implementación de su secuencia. No se redistribuyen artículos completos ni páginas privadas.
