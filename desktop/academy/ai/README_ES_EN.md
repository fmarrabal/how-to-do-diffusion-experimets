# Beatrix Academy · tutor local / local tutor

El tutor explica el curso y las simulaciones con sus fuentes. No ejecuta TopSpin,
no modifica calibraciones y no envía preguntas, datos o espectros a la red.
La ejecución usa LLamaSharp 0.27.0 con un modelo GGUF CPU, hasta cuatro hilos,
contexto de 4096 tokens y generación limitada a 512 tokens. Puede cancelarse
durante la lectura del contexto y durante la generación.

The tutor explains the course and simulations with source references. It does
not operate TopSpin, change calibration or transmit questions/data/spectra.
Inference uses LLamaSharp 0.27.0 and a CPU GGUF model, at most four threads,
a 4096-token context and a 512-token generation limit. Context prefill and
generation can be cancelled.

## Estados verificables / verifiable states

- `Guía documental · sin LLM / Documentary guide · no LLM`: no model inference
  was used. This includes a missing model, failed quality gate or checksum,
  oversized whole-evidence context and generation failures.
- `Beatrix · LLM local + texto del curso · CPU / local LLM + course text · CPU`:
  the local fine-tuned model generated `GeneratedText` after verifying its
  SHA-256, course version and training/evaluation report hashes. A separate
  `CourseQuote` contains the active lesson's literal reviewed WHY and Mechanism;
  `IncludesCourseQuote=true` identifies this hybrid answer. These two parts
  have separately recorded source references. `IsModelAnswer=true` means the
  local model actually ran; it does not mean that the course quote was generated.
- A fluent answer remains teaching guidance, not an experimentally validated
  diffusion coefficient, chemical assignment or approved instrument operation.

## Reproducir / reproduce

Use the existing environment `desktop/training/.venv/Scripts/python.exe` and
the pinned Qwen3-1.7B base in `desktop/academy/ai/base-1.7b` read only. Run from
the repository root; choose a fresh versioned work directory for every candidate.
The upstream revision is `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`;
`base-provenance.json` records the SHA-256 of every downloaded file. The ranged
download verifies exact byte ranges and the full upstream weight hashes, using
normal TLS and no credentials. These commands perform actual training:

```powershell
desktop/training/.venv/Scripts/python.exe desktop/academy/ai/academy_pipeline_v2.py prepare --course desktop/academy/content/course.json --work desktop/academy/ai/work-v2
desktop/training/.venv/Scripts/python.exe desktop/academy/ai/academy_pipeline_v2.py train --work desktop/academy/ai/work-v2 --base desktop/academy/ai/base-1.7b --epochs 3
desktop/training/.venv/Scripts/python.exe desktop/academy/ai/academy_pipeline_v2.py evaluate --work desktop/academy/ai/work-v2 --base desktop/academy/ai/base-1.7b
desktop/training/.venv/Scripts/python.exe desktop/academy/ai/academy_pipeline_v2.py package --work desktop/academy/ai/work-v2 --tools desktop/training/work --release desktop/academy/ai/release
dotnet run --project desktop/academy/ai/NativeCheck -c Release -- desktop/academy/content/course.json desktop/academy/ai/release desktop/academy/ai/native-evaluation-v2-hybrid.json native desktop/academy/qa/ui-final2/spen-context.json
desktop/training/.venv/Scripts/python.exe desktop/academy/ai/finalize_release.py
```

LoRA training applies loss only to answer tokens; prompts and padding are
masked with −100. `completion-loss-verification.json` checks loss and all
gradients against the full causal masked loss on a tiny model with ragged
padding. Four complete modules are excluded from training evidence:
`ramp-design`, `convection`, `algorithm-selection`, `capstone`. Their reviewed
course answers are available only through retrieval at evaluation time; this
measures grounded explanation, not independent domain memorization. Numeric
scenarios use different values across splits and supply a deterministic
`calculation_context`: the model explains the value rather than computing it.
Training has 352 examples, development 90, and the new frozen test 32.
Checkpoint selection uses development loss. The frozen test is generated
once, without output grammar, for both the original base and fine-tuned model.
The quantized CPU runtime is tested separately. Reports distinguish automated
developer fixtures from expert review, measured student learning and hardware
validation. A trained checkpoint failing the declared quality gate remains a
failed candidate and does not become the default tutor.

El ajuste v1 de Qwen3-0.6B se ejecutó y se conserva en `work-v1`: pasó 12/28
casos y falló el umbral declarado, incluyendo dos razonamientos numéricos.
No se publica como tutor aprobado. Su test ya expuesto es desarrollo/regresión;
v2 utiliza módulos y valores nuevos reservados antes de entrenar, sin reducir
el umbral (al menos 85% global y todos los casos numéricos y de límites).

The actual Qwen3-0.6B v1 fine-tune remains preserved in `work-v1`: 12/28 cases
passed; it failed the declared gate, including two numeric explanations. It
is not an approved tutor. Its exposed test is development/regression evidence.
V2 uses newly reserved modules and values, with the same unchanged gate of at
least 85% overall and all numeric/boundary cases passing.

Only original course summaries and synthetic teaching examples are trained.
Literature is linked as retrieval metadata; third-party paper text, spectra,
private sample labels and production model weights are excluded.

Original inputs, checkpoints and production Beatrix/Prime packages are preserved.
Academy output is isolated here. The GGUF package contains its license and
SHA-256 provenance; no training environment or unquantized checkpoint belongs
in the student application bundle.

## Evidencia v2 / v2 evidence

El entrenamiento real duró 196,65 s en RTX PRO 5000 Blackwell (torch
2.8.0+cu128). Actualizó 3.211.264 parámetros LoRA; tres épocas, batch 2 y
checkpointing, pico 5.475.623.936 bytes de memoria CUDA asignada. La pérdida
dev pasó de 1,57660 a 0,01048; se eligió la época 3 por dev. La evaluación
de generación libre, realizada una vez sin gramática, pasó 32/32 frente a
21/32 del base: 12/12 ejemplos numéricos, 4/4 límites y 16/16 preguntas de
los cuatro módulos reservados. Esto es QA de escenarios escritos por el
desarrollador; no una evaluación docente independiente.

Actual v2 training took 196.65 s on RTX PRO 5000 Blackwell with torch
2.8.0+cu128: 3,211,264 updated LoRA parameters, three epochs, batch 2,
gradient checkpointing, 5,475,623,936-byte peak CUDA allocation. Development
loss fell from 1.57660 to 0.01048; epoch 3 was selected by development loss.
One-time unconstrained free generation passed 32/32 versus 21/32 for the
base: 12/12 numeric explanations, 4/4 behavior limits, 16/16 held-module
questions. These are developer-authored teaching fixtures, not independent
educational validation. Base generation took 380.03 s; fine-tuned generation
took 132.17 s for the same 32 cases.

GGUF Q8_0: 1,834,425,984 bytes; SHA-256
`b01668cced4c2ec9f28dba333769f0ec2b728e6a18ec7d5eeddb16485fc72fd9`.
The final package passed 15/15 native hybrid CPU checks and is closed with
`NativeEvaluationPending=false`. `NativeCheck` records actual answers,
literal source text, generated text and their references; it is not a
simulated conversation.
Its advanced test reads the genuine WebView SPEN context: A is absent,
its nearest-component reference is null, and a fitted D from spectral leakage
must not be reported as A's diffusion. Native generation cancellation is
also exercised after context prefill.

Las respuestas abiertas generadas sobre SPEN y difusión resuelta en tiempo
pueden omitir detalles causales, aunque describan operaciones correctas. Por
eso la entrega separa texto literal revisado del curso de texto generado; no
atribuye al LLM la cita ni convierte esos probes fallidos en aprobados. Las
guardas rechazan números ausentes o una contradicción «P90 doble de P180» y
entregan guía documental honesta con la traza correcta. Los dos ejemplos
numéricos normalizan su intención a una pregunta sintética explícita con
supuestos, usando la traza determinista; no infieren una calibración real.

Open generated-only SPEN/time-resolved explanations can omit causal details
despite describing correct operations. The release therefore visibly separates
reviewed course quotations from actual model output. The quote is not claimed
as LLM generation, and earlier failed probes remain unchanged. Numeric guards
reject missing results or an inverted P90/P180 relationship and return an
honest documentary explanation with the correct deterministic trace. The two
worked examples normalize the parsed intent into an explicit synthetic
question with assumptions; no real calibration is inferred.

The final CPU run returned actual generated P90=9 µs at unchanged power and
b×4 under rectangular PGSE with unchanged δ/Δ. It correctly refused to assign
the leakage fit to an absent A component. Five replies took 20.72–39.00 s
(initial reply 34.41 s) on this computer with four CPU threads. Cancellation
after prefill returned in 0.177 s. These timings are measurements on this
machine, not guarantees for all student computers.

`prompt-parity-report.json` proves 32/32 byte-identical C# training-profile
JSON/ChatML prompts versus Python. Native numeric examples also normalize
the question to the explicit teaching template. Runtime retrieval uses one
complete active module; explanatory prompts may add literal causal anchors.
HF free-generation testing and native grammar-constrained hybrid regression
are separate evidence. `native-probe-history.json` retains hashes and limits
of the previous probes. `environment_report.json` records actual versions;
`environment_git_provenance_normalized.json` shows that the converter's
working-file hash differs from Git only by Windows CRLF, with normalized
content matching commit `b22572e97dc51757d3ebe917a5a283385010ec68`.

Final model: `release/model.gguf`.
Native report SHA-256:
`3dd224a85bc67219fe39d57f2e53e70cc532894c1defc1f18ffbf2378d11dbb3`.
Training report SHA-256:
`e67242492126f9a2a3c151238ca214d406fbb58de62ee46ea9549e688e351e83`.
One-time free-generation report SHA-256:
`79962e41fcd7e990d96cdc9c7fa8505710af3e4d68e1546658511d78e748c06f`.
