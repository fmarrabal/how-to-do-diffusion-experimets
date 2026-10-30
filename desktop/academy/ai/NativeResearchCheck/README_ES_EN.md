# Native research check / Comprobación nativa del tutor

## Español

Este proyecto contiene únicamente fuentes. Ejecuta el servicio C# real con un único modelo GGUF indicado por ruta; no copia pesos al proyecto. Requiere .NET 8 y las dependencias del proyecto Tutor. Desde `desktop/academy`:

```powershell
dotnet run --project ai/NativeResearchCheck/NativeResearchCheck.csproj -- content/research-tutor-knowledge.json ai/release-v1.3 content/course.json qa/native-local-rerun.json native
```

Elegir un archivo de salida nuevo: se rechaza sobrescribir un informe existente. Para comprobar pistas, recuperación y límites sin cargar el modelo, sustituir `native` por `fallback` y usar otra salida. El modo `native` ejecuta guardas negativas y consultas reales ES/EN: P90, escala de b, cociente de D, ruido, identificación de 360 grados (88 us → 22 us y 92 us → 23 us), elección de medición, límite de difusión espacial, cancelación, cuatro módulos originales y las cuarenta entregas documentales de las veinte derivaciones.

El archivo de fuentes no incluye pesos. Si se usa ese archivo, sustituir `ai/release-v1.3` por la carpeta `Models/Beatrix` de la aplicación WPF descargada y descomprimida, que contiene el GGUF y sus informes vinculados. Comprobación de entrega de estas fuentes: compilación sin dependencias mediante un proyecto temporal, sin copiar modelos, cero avisos y errores; modo `fallback`, 48/48 controles. No se repitió toda la inferencia del candidato al publicar este wrapper.

Las opciones `allowPendingNativeEvaluation` y `allowPendingResearchNativeEvaluation` son permisos explícitos de este arnés de evaluación. No se habilitan por capturar diagnósticos ni por la aplicación del estudiante. Los fallos producen código de salida distinto de cero. Los diagnósticos originales se guardan sólo en el informe local de prueba, no en la interfaz del estudiante.

Esta ejecución crea **un nuevo informe** con el protocolo actual; no reconstruye retrospectivamente el agregado histórico de la entrega. El manifiesto vincula los informes originales que conservaron sus fallos y las reevaluaciones acotadas. No se modifica el manifiesto ni se aprueba automáticamente un modelo al ejecutar este proyecto. Los casos publicados quedan expuestos y no constituyen futuras pruebas independientes. No hay control de espectrómetro, red ni modificación de datos experimentales.

## English

This project ships source only. It executes the actual C# services using a single GGUF selected by path; no weights are copied into the project. .NET 8 and the Tutor project's dependencies are required. Run the command above from `desktop/academy`. Choose an absent output file: existing reports are preserved. Use `fallback` instead of `native`, with a different output file, to check documentary hints/retrieval and boundaries without loading the model.

Native mode runs negative guard controls and actual ES/EN queries for pulse calibration, b scaling, D ratio, noise, identified 360-degree crossings (88 us → 22 us and 92 us → 23 us), next-measurement reasoning, spatial diffusion limits, cancellation, four original-course modules and all forty bilingual documentary deliveries of the twenty derivations.

The source archive excludes weights. When using that archive, replace `ai/release-v1.3` with the downloaded unpacked WPF application's `Models/Beatrix` folder, containing its GGUF and hash-linked reports. Source-delivery QA: compilation without dependencies through a temporary build project, no model copies, zero warnings/errors; `fallback` mode, 48/48 checks. Publishing this wrapper did not repeat the candidate's full native generation gate.

Pending-candidate execution is an explicit evaluation-harness permission, independent of diagnostic capture. The student application does not enable it. Failures return a nonzero exit code. Original-course diagnostics are confined to the local evaluation report rather than the student UI.

This creates **a new report** against the current protocol, not a retrospective reconstruction of the release's historical aggregate. The manifest binds the original preserved failures and narrowly affected retests. This program neither modifies a manifest nor automatically approves a model. Published cases are exposed, rather than independent future tests. No spectrometer control, network access or experimental-data modification occurs.
