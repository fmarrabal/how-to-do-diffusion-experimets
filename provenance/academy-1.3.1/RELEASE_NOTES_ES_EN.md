# DiffAtOnce Academy 1.3.1 / Auditoría y correcciones

## Español

Academy 1.3.1 corrige problemas reproducibles detectados al auditar los ejemplos,
las simulaciones, los cálculos y los recorridos de formación en inglés y español.
Mantiene el curso compartido entre WPF y la web y conserva los datos originales.

- Las integrales conservan su signo; las curvas correlacionadas y la selección de
  picos usan la fila con menor b, también al adquirir rampas descendentes.
- La incertidumbre Monte Carlo identifica explícitamente el ajuste monoexponencial
  de referencia. Su intervalo no describe el centroide ni los picos de una ILT.
- Los ajustes permanecen estables en el intervalo medido cuando falta b=0. Una
  amplitud extrapolada no representable se identifica; no genera curvas NaN.
- Los lectores y el procesado rechazan metadatos, fases o ejes que producirían
  resultados no finitos. Los valores por defecto de calibración no se presentan
  como calibraciones experimentales independientes.
- Se revisan unidades, factores de forma, convenciones de secuencia, flujo,
  convección y controles de pulso. Se corrigen dos redondeos/notaciones del curso.
- La interfaz muestra convergencia, residuos y límites del modelo, conserva las
  respuestas del estudiante y traduce correctamente las explicaciones revisadas.

Incluye código WPF/web, contenido ES/EN, fuentes de reproducción, atribución y
licencias de los datos públicos y los manuales actualizados: 72 páginas por idioma
en el manual completo y 26 en la guía de investigación. Las fuentes de entrenamiento
conservan su procedencia original. **No se ha realizado un nuevo ajuste fino.**
La web utiliza guía documental. La inferencia Beatrix de Windows requiere el
paquete y las comprobaciones nativas de compatibilidad correspondientes.

Los controles analíticos, sintéticos, de interfaz y de integridad verifican
software y supuestos acotados. No acreditan calibración física, identidad molecular,
cobertura experimental de intervalos ni eficacia educativa medida. Las series
públicas sin b documentada bloquean el cálculo de D. Los argumentos abiertos
requieren revisión humana. Se conservan el tag y los assets de Academy 1.3.0.

## English

Academy 1.3.1 fixes reproducible issues found while auditing the English/Spanish
teaching examples, simulations, calculations and learning workflows. WPF and the
browser retain their shared course; original experimental data remain unchanged.

- Signed integrals retain polarity; peak selection and correlated attenuation
  curves use the minimum-b row, including descending acquisition orders.
- Monte Carlo uncertainty explicitly identifies the reference monoexponential
  estimator. Its interval does not quantify an ILT centroid or distribution peaks.
- Fits remain stable over the measured range without b=0; unrepresentable
  reference extrapolation is explicit and cannot silently create NaN curves.
- Import/processing guards reject metadata, phases and axes that would produce
  nonfinite results. Recorded calibration defaults do not establish independent
  experimental calibration evidence.
- Units, gradient shapes, sequence conventions, flow, convection and RF controls
  receive numerical checks; two course rounding/notation issues are corrected.
- The interface exposes convergence, residuals and model limitations, retains
  submitted student answers and localizes the reviewed feedback correctly.

The release includes WPF/browser source, bilingual content, reproduction sources,
public-data attribution/licenses and updated manuals: 72 pages per language in
the complete manual and 26 in the research guide. Original training provenance
is retained. **No new fine-tuning was performed.** The web uses documentary
guidance; Windows Beatrix inference requires the corresponding package and
source-bound native compatibility checks.

Analytical, synthetic, UI and integrity checks verify software and bounded
assumptions. They do not establish physical calibration, molecular identification,
experimental interval coverage or measured educational effectiveness. Public
series without documented b values cannot yield D. Open written arguments need
human review. The Academy 1.3.0 tag and release assets remain preserved.

Source asset / fuentes: `DiffAtOnce-Academy-1.3.1-source.zip`, 151,138,394 bytes,
740 source members plus the self-excluding source manifest. SHA256:
`b696b9e67edb237a2d0ff32cf1d6514f4a292939181da1180a4ce00d2c518662`.
[Full audit / auditoría](https://github.com/fmarrabal/how-to-do-diffusion-experimets/blob/academy-v1.3.1/desktop/academy/docs/AUDIT_1_3_1_ES_EN.md).

Model weights, adapters/checkpoints, private papers, learner records, runtime
environments and private QA trees are excluded from the source release.

## Downloads / Descargas

[Academy ES](https://diffatonce.com/academy) · [Academy EN](https://diffatonce.com/en/academy) · [Windows + Beatrix](https://diffatonce.com/downloads/diffatonce-academy-1.3.1-win-x64) · [Source / fuentes](https://diffatonce.com/downloads/diffatonce-academy-1.3.1-source).

Windows ZIP: 2,094,896,943 bytes; 1,196 files verified by complete archive CRC/SHA256 readback. SHA256: `5628eaae3db7f8443b6f08e3c673347c0e7608cfde0b937dd4333d5c662aa713`. Integrity evidence is distinct from native UI/model evaluation and experimental validation.

ZIP Windows: 2.094.896.943 bytes; 1.196 archivos comprobados mediante lectura completa CRC/SHA256. La integridad se distingue de la evaluación de interfaz/modelo nativo y de la validación experimental.

[SHA256SUMS](https://diffatonce.com/assets/academy/releases/1.3.1/SHA256SUMS.txt) · [Release asset metadata / metadatos](https://diffatonce.com/assets/academy/releases/1.3.1/RELEASE_ASSETS_SHA256.json).

Compact WPF layout / Diseño WPF compacto: the title and actions use separate rows. The tutor retains a readable answer viewport (at least 150 pixels); an outer scroll area makes the question/input, Ask and Cancel controls reachable. Los títulos y acciones usan filas separadas. El tutor conserva un área de respuesta legible (al menos 150 píxeles); el desplazamiento exterior permite acceder a la pregunta/entrada y a los controles Preguntar y Cancelar. These UI fixes do not change teaching equations, tutor services or model weights. Estas correcciones de interfaz no cambian ecuaciones, servicios del tutor ni pesos del modelo.
