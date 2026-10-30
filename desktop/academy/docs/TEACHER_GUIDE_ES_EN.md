# Evidencias docentes / Teaching evidence

## Propuesta de trabajo / Suggested workflow

**ES.** Antes de mostrar el resultado, pida al estudiante una predicción.
Cambie una variable, pulse **Calcular** cuando corresponda y compare resultado
esperado y observado. Termine con una decisión y un control experimental que
podría refutarla. Use **Mi cuaderno** como registro razonado, no sólo como lista
de respuestas. Los manuales ES/EN proponen una sesión de 100 minutos y una
demostración de 20 minutos.

**EN.** Ask for a prediction before showing the result. Change one variable,
press **Calculate** where required and compare expected and observed outputs.
Finish with a decision and an experimental control that could refute it. Use
**My notebook** as a reasoning record, not just an answer list. The ES/EN
manuals propose a 100-minute session and a 20-minute demonstration.

## Ocho evidencias útiles / Eight useful deliverables

| Ejercicio / Exercise | Evidencia observable / Observable evidence |
|---|---|
| P90 | Identifica 180° y misma potencia; 22/2=11 µs y explica por qué 44/2 falla / Identifies 180° and unchanged power; 22/2=11 µs and explains why 44/2 fails |
| Gradiente / Gradient | Relaciona g² con el sesgo: 10 % en g produce 21 % en D aparente / Links g² to bias: 10% gradient error produces 21% apparent-D error |
| Secuencia y rampa / Sequence and ramp | Distingue parámetros del programa e intervalos físicos; justifica δ/Δ sin invocar PGSE universal / Distinguishes program parameters from physical intervals; justifies δ/Δ without assuming universal PGSE |
| Convección / Convection | Separa fase por velocidad común y pérdida por dispersión; propone un control y reconoce diagnósticos alternativos / Separates common-flow phase from spread-induced loss; proposes a control and acknowledges alternatives |
| Procesamiento / Processing | Conserva extracción comparable; muestra cómo baseline o normalización sesgan una curva aparentemente buena / Preserves comparable extraction; shows how baseline or normalization bias a seemingly good curve |
| ILT y espectro conjunto / ILT and joint spectrum | Compara hipótesis, ruido y estabilidad; no llama resolución a aumentar bins / Compares assumptions, noise and stability; does not call extra bins added resolution |
| UF/SPEN/TR | Declara normalización y b(z), contaminación/fase y relojes de adquisición; reconoce el modelo ideal / States normalization and b(z), contamination/phase and acquisition clocks; acknowledges the ideal model |
| Caso final / Final case | Decide aceptado/exploratorio/bloqueado con fuente, límites y siguiente control / Decides accepted/exploratory/blocked with sources, limits and next control |

Cada entrega debe incluir hipótesis, parámetros con unidades, observación,
explicación causal y límite. Un JSON del taller documenta un resultado sintético;
el JSON de **Exportar** documenta notas y respuestas del estudiante. Pida ambos
cuando sea útil y solicite el envío mediante el procedimiento del centro:
Academy no entrega archivos automáticamente.

Each deliverable should include assumptions, parameters with units, observation,
causal explanation and a limit. Workshop JSON documents a synthetic result;
the **Export** JSON documents student notes and answers. Request both where
useful and use your institution's submission procedure: Academy does not submit
files automatically.

## Rúbrica breve / Short rubric

Puntúe cada criterio 0, 1 o 2: ausente/incorrecto, parcial o justificado.
Score each criterion 0, 1 or 2: absent/incorrect, partial or justified.

| Criterio / Criterion | Para alcanzar 2 / To earn 2 |
|---|---|
| Predicción / Prediction | Indica variable, efecto esperado y por qué / States variable, expected effect and why |
| Evidencia / Evidence | Conserva valores, unidades, procedencia y supuestos / Preserves values, units, provenance and assumptions |
| Razonamiento / Reasoning | Explica mecanismo y distingue una causa alternativa / Explains the mechanism and distinguishes an alternative cause |
| Próximo control / Next control | Propone una comprobación que podría cambiar la conclusión / Proposes a check that could change the conclusion |

El máximo de 8 puntos sirve como evidencia formativa. No certifica uso de un
espectrómetro ni reemplaza la evaluación práctica supervisada de su centro.
Los 2/2 del quiz indican respuestas correctas en ese módulo; la rapidez o el
número de módulos comprobados no prueban rigor experimental.

The maximum of 8 points is formative evidence. It does not certify instrument
operation or replace supervised practical assessment. A 2/2 quiz means correct
module answers; speed or checked-module count does not establish experimental
rigour.

## Usar Beatrix sin delegar la conclusión / Use Beatrix without delegating conclusions

Calcule primero. Pida al estudiante que contraste la respuesta con parámetros,
resultado vigente y fuente citada. Seleccionar **Experimentar** restaura el
contexto del laboratorio; editar campos del taller retira resultados antiguos.
Si aparece **Guía documental · sin LLM**, úsela como recuperación de fuentes.
No invente una captura del modelo ni atribuya a inferencia una respuesta
documental. Una fuente identificada no prueba por sí sola una identidad química.

Calculate first. Ask the student to compare the answer with current parameters,
results and cited evidence. Selecting **Experiment** restores laboratory
context; editing workshop fields removes obsolete results. Use **Documentary
guide · no LLM** as source retrieval. Do not fabricate a model screenshot or
attribute documentary retrieval to inference. An identified source alone does
not prove a chemical identity.

El modo **LLM local + texto del curso · CPU** mantiene dos bloques visibles:
texto generado por Beatrix y una copia literal del problema/mecanismo del curso.
Pida distinguir ambos, citar la fuente y explicar la causa con palabras propias.
El 32/32 reservado HF y el 15/15 CPU híbrido son pruebas distintas. El texto
generado CPU omitió causas abiertas SPEN/TR; la copia literal completa el
contexto sin atribuir sus frases al modelo. Esta limitación está documentada.

**Local LLM + course text · CPU** keeps two visible blocks: Beatrix generation
and a literal copy of the course why/mechanism. Ask students to distinguish
them, cite the source and explain the cause in their own words. Reserved HF
32/32 and hybrid CPU 15/15 are different checks. Generated-only CPU text omitted
open SPEN/TR causes; the literal quote completes the context without attributing
its words to the model. This limitation is documented.

## Qué evidencia aporta el software / What software evidence establishes

Los registros de QA de interfaz prueban acciones y estados observados; los
tests numéricos comprueban casos y relaciones del modelo implementado. Los
informes de entrenamiento/evaluación describen el corpus, el test reservado y
el motor realmente usado. Estas evidencias tienen alcances distintos: ninguna
se convierte en calibración real, revisión científica independiente o mejora
educativa medida en estudiantes.

Interface QA records observed actions and states; numerical tests check cases
and relationships in the implemented model. Training/evaluation reports
describe the corpus, reserved test and actual inference engine. These evidence
types have distinct scopes: none becomes actual calibration, independent
scientific review or measured improvement in student learning.

En una práctica real, mantenga los datos originales, revise secuencia y forma de
gradiente, documente temperatura y referencias, y registre correcciones una
sola vez. Los casos TBO/KK2/HDO del curso son históricos atribuidos. No se
transfieren índices de otras muestras ni se fuerzan resultados para reproducir
una tabla anterior. D–T₂ y DOSY químicamente resuelto tienen ejes distintos.

In a real practical, preserve original data, inspect pulse sequence and gradient
shape, document temperature/references and record corrections once. TBO/KK2/HDO
course cases are attributed historical examples. Do not transfer indices from
other samples or force agreement with old tables. D–T₂ and chemically resolved
DOSY have different axes.
