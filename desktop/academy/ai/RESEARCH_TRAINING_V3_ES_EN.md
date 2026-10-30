# Beatrix Academy 1.3 — actual local mixed LoRA / LoRA mixto local real

## Español

Beatrix usa un único Qwen3-1.7B con un LoRA entrenado realmente en GPU sobre resúmenes docentes propios en español e inglés, explicaciones causales y ejemplos numéricos sintéticos. No se entrenaron textos completos de artículos, espectros experimentales, datos de estudiantes ni calibraciones de hardware. Las veinte derivaciones de los artículos siguen siendo consulta documental literal revisada, sin generación LLM ni inclusión en este entrenamiento. El contexto determinista aporta las cifras; el modelo explica su significado y sus condiciones.

El candidato final R4 se congeló antes de entrenar: **382 ejemplos de entrenamiento, 40 de desarrollo y 36 de prueba**. Semilla **261030**. Los temas `defence`, `measure-next` y `spatial-diffusion` quedaron fuera del entrenamiento; `processing` y `pilot` sólo se usaron en desarrollo. Los módulos originales `pulse-calibration`, `sequence-b`, `spen` y `time-resolved` se reservaron para regresión expuesta. Las preguntas y valores de prueba R4 son distintos de los intentos fallidos previos, que no se reclasificaron como éxitos.

Base: `Qwen/Qwen3-1.7B`, revisión fija `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`, licencia Apache-2.0. Adaptador: rango 16, alpha 32, dropout 0.05, matrices `q_proj` y `v_proj`, **3 211 264 parámetros entrenables**. AdamW: tasa 0.0001, weight decay 0.01; batch 2; tres épocas; pérdida sólo sobre la respuesta, con prompt y padding enmascarados a -100. El checkpoint se eligió por la menor pérdida de desarrollo (época 3: 0.07544880194), sin usar las respuestas de prueba para seleccionarlo. Entorno usado: Python con torch 2.8.0+cu128, transformers 4.57.3, peft 0.17.1, safetensors 0.6.2 y accelerate 1.10.1; NVIDIA RTX PRO 5000 Blackwell. La repetición en otro entorno puede producir pesos distintos.

Evaluación de generación libre GPU, sin gramática de salida: **35/36 (97.22%)** para R4 frente a **14/36 (38.89%)** para la base. Se exigió al menos 85% global y todos los controles numéricos, fuentes, límites de actuación y regresión original: 16/16 numéricos, 6/6 límites, 8/8 regresión y 5/6 preguntas de temas reservados. Controles causales independientes sobre esas respuestas: 16/16. La pregunta inglesa de defensa que faltó al criterio textual sigue marcada FAIL. Los intentos anteriores y el primer gate CPU que falló dos comprobaciones se conservaron; el rechazo numérico anterior de `sequence-b` era correcto porque la respuesta omitía el factor 4. La corrección posterior alinea únicamente el protocolo del prompt del modelo mixto con su entrenamiento para cálculos tipados; no fuerza respuestas ni modifica resultados, guardas o preguntas originales mostradas.

### Reproducción acotada

Los JSONL finales congelados y su plan están en `release-v1.3/training-data/`. Son material propio y sintético, con sus hashes originales. Una vez publicados, estas preguntas quedan expuestas y no sirven como una nueva prueba independiente. Para evaluar otro cambio se necesita reservar nuevos casos antes de entrenarlo.

Desde la carpeta `desktop/academy`, con las dependencias anteriores y la base ya obtenida legalmente en `ai/base-1.7b`, ejecutar:

```powershell
python ai/release-v1.3/training-data/prepare_reproduction.py ai/reproduction-v3
python ai/academy_research_pipeline_v3.py train --work ai/reproduction-v3 --base ai/base-1.7b --epochs 3
python ai/academy_research_pipeline_v3.py evaluate --work ai/reproduction-v3 --base ai/base-1.7b
```

El preparador rechaza una carpeta existente y comprueba los hashes de los tres splits y de los dos corpus. El pipeline v3 reutiliza `academy_pipeline_v2.py` en modo lectura. No usar `prepare-r4` para esta receta pública: esa función conserva la historia interna de intentos previos; los splits finales publicados evitan depender de ella. `train` crea un adaptador y pesos fusionados en la carpeta nueva. `evaluate` conserva el informe de generación y rechaza sobrescribirlo. Convertir los pesos fusionados con `llama.cpp/convert_hf_to_gguf.py --outtype f16` y `llama-quantize ... Q8_0` requiere disponer de esas herramientas y registrar sus versiones/hashes. Aprobar GPU no autoriza desplegar: también se necesita comprobar la inferencia CPU cuantizada real, las guardas, las fuentes, el curso original y la aplicación que se empaquete.

El proyecto público [NativeResearchCheck](NativeResearchCheck/README_ES_EN.md) permite ejecutar esas comprobaciones con el servicio C# real y un GGUF indicado por ruta. Incluye sólo fuentes, sin depender de `work-v3`; crea un informe nuevo y conserva los históricos. Su publicación se comprobó mediante compilación y 48 controles documentales/de guardas, sin otra generación completa del modelo.

Los resultados son QA de software y de respuestas docentes redactado por desarrolladores, con revisión científica interna de ejemplos reales. **No miden eficacia educativa, cobertura experimental de intervalos ni exactitud en una muestra desconocida**. El asistente no controla espectrómetros, no accede a red y no cambia los datos originales. Una cita, un ajuste o un hash no identifica una molécula ni autentica a un docente.

## English

Beatrix uses one Qwen3-1.7B with an actual GPU-trained mixed LoRA on original Spanish/English teaching summaries, causal explanations and synthetic numerical examples. No full article text, experimental spectra, student records or hardware calibrations were trained. The twenty paper derivations remain literal reviewed documentary retrieval, without LLM generation or inclusion in this training. Deterministic context supplies numbers; the model explains their meaning and conditions.

Final candidate R4 was frozen before training: **382 training, 40 development and 36 test examples**, seed **261030**. `defence`, `measure-next` and `spatial-diffusion` were held out of training; `processing` and `pilot` were development-only. Original modules `pulse-calibration`, `sequence-b`, `spen` and `time-resolved` were exposed regression. Fresh R4 test questions and numerical values differ from preceding failed trials, whose results remain failed.

The pinned Apache-2.0 base revision is `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`. LoRA uses rank 16, alpha 32, dropout 0.05 on `q_proj`/`v_proj`: **3,211,264 trainable parameters**. AdamW learning rate 0.0001, weight decay 0.01; batch 2; three epochs; completion-only loss with prompt/padding labels -100. Development loss selected epoch 3 (0.07544880194), without using test outputs to select the checkpoint. Actual software versions and hardware are stated above; a different environment need not reproduce identical weights.

Unconstrained GPU generation scored **35/36 (97.22%)**, versus **14/36 (38.89%)** for the base. The gate requires at least 85% overall plus every numerical, supported-source, behavior-limit and original regression check: 16/16 numerical, 6/6 limits, 8/8 regression and 5/6 held-topic cases. Independent causal fixtures passed 16/16. The English defence answer that missed its textual criterion remains FAIL. Earlier trials and the first CPU gate with two failures were preserved. The earlier `sequence-b` numerical rejection was correct: its response omitted factor 4. The subsequent narrowly scoped compatibility change aligns the mixed model's prompt protocol for recognized typed examples; it does not force generated answers, change deterministic results or weaken guards.

Use the three commands above from `desktop/academy`, with the pinned base already available locally and the stated Python dependencies. The preparation script validates frozen split/source hashes and refuses an existing scratch directory. Published test questions are now exposed: any future independent evaluation needs fresh cases frozen before training. v3 imports the existing v2 trainer read-only; the final public splits remove any need to reconstruct failed internal trial directories. Quantization uses the llama.cpp converter and Q8_0 quantizer, whose exact release hashes are recorded in the manifest. GPU success alone is insufficient for deployment; actual quantized CPU inference and the packaged application's guards/course behavior must also pass.

The public [NativeResearchCheck](NativeResearchCheck/README_ES_EN.md) project runs those checks against the actual C# services and a GGUF selected by path. It ships source only, without a `work-v3` dependency, and creates a new report while preserving historical evidence. Publication QA compiled its sources and passed 48 documentary/guard checks, without another complete model-generation run.

These are developer-authored software/model QA results with internal scientific review of real generated examples. **They do not measure teaching effectiveness, experimental interval coverage or accuracy on an unknown sample**. The assistant performs no instrument control, network access or original-data changes. A citation, fit or integrity hash does not identify a molecule or authenticate a teacher.

## Frozen provenance / Procedencia congelada

| Artifact / Artefacto | SHA-256 |
|---|---|
| Training split | `443e2ad5f43ee4481283e132d961d838dea02586b10df1e23841f3b8567ca06e` |
| Development split | `2cc11ce3fc9b9e9467182b184f2dc087e2e28bb1525a27e2cb08e85fa213d084` |
| Test split | `64ec8a91b27f6cf34c12824f74263f9256fe88f772fd55a7da16cc568c71ae03` |
| Training report | `9230e13e8e8799f4eeadc4c9305e7ed87f51cca3e6574af6dcc2bfb950500726` |
| GPU generation report | `378034b7e050d186138d42cb6a9a5d58af08168e9652215263709294ab2db3fa` |
| Causal report | `48d1d33eba58e493a088f031aa736be743264aaa4d456b0cfd8c07b2f6758547` |
| Original course | `f9a17df9645b541abc70907e5d04cd38c213293443ce1d37c2c0d94f8aea0cb9` |
| Research knowledge | `a04ae8bcfa523c4f49981d562ec67baae7b4ab74cb452d6fc59a4cd4c6356717` |
| Documentary derivations | `e07920a25ae8642ffa55a83a75a4db7eb8a6ead09a5c8195ae23ef91d6c9b02e` |
| Final Q8_0 model, 1,834,425,984 bytes | `24bcf29032b1d4e19c08d69fa71bf562276b6999d22887b1f6aa344dfd58481a` |

The final manifest binds the current native evaluation and literal documentary-preservation reports. Their checks do not change the scope above. / El manifiesto final vincula la evaluación nativa actual y la preservación documental literal; esas comprobaciones no amplían el alcance anterior.

The final native closure combines 73 unchanged passing CPU checks, two new bilingual 360-degree cases (88 us → 22 us and 92 us → 23 us), and a separate final-guard replay check: 76 aggregate checks. The earlier response that omitted the explicit 360-degree label remains failed in its original report. The final guard replay passes 33/33 controls, including small physical values, inconsistent repeated assignments, units, ambiguous prose parsing, preserved scene/question data, ChatML data escaping and native manifest approval. Replay rechecks captured text; it is not a new generation. All 40 literal documentary chapter/language deliveries pass.

El cierre nativo combina 73 comprobaciones CPU anteriores sin cambios, dos casos nuevos de 360 grados ES/EN (88 us → 22 us y 92 us → 23 us) y una comprobación separada del replay final de guardas: 76 controles agregados. La salida anterior que omitió la etiqueta explícita de 360 grados conserva su FAIL original. El replay final pasa 33/33 controles, incluidos valores físicos pequeños, asignaciones contradictorias, unidades, parseo ambiguo, conservación de escena/pregunta, escape ChatML y aprobación del manifiesto nativo. El replay comprueba texto capturado; no es nueva generación. Las 40 entregas documentales literales pasan.

| Final report / Informe final | SHA-256 |
|---|---|
| Native aggregate | `e67ec46530b98c4d7cf4eb1a608509cc0f5d079dfcfc7fe471f30505424b9ec5` |
| Final C# guard replay | `4501ce89ae2640b42e7fcc47a641bc9e65ca1724abf603b907c2a1a80fecaefc` |
| New documentary native delivery | `9a9668cc50e1d236ce645bd643f65ef8af6f2e5eb1f91d83c17fc75ae46cc985` |
| Literal semantic preservation | `f45e231f159266b611f3324672538076ac680b370e55f33d30e0be9a5462aafa` |
