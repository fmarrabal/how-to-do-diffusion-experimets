using System.Diagnostics;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using LLama;
using LLama.Common;
using LLama.Native;
using LLama.Sampling;

namespace DiffAtOnce.Academy.Tutor;

/// <summary>
/// Source-grounded research tutor. Reads local knowledge and an explicitly
/// qualified mixed model. No network, instrument API, file mutation or automatic
/// semantic grading is provided. Literal guidance and generated prose remain
/// separately identified in TutorAnswer.
/// </summary>
public sealed class ResearchTutorService : IAsyncDisposable
{
    public const string SystemInstructions = "You are Beatrix, a bilingual NMR diffusion teaching assistant. Use only supplied reviewed evidence, reviewed_causal_anchor and calculation_context to answer the student's actual question. Give the supplied result with its exact result_label and unit, then explain the causal link, its required conditions and one practical check or limitation. Keep two to four clear sentences. Do not replace a waveform/timing condition with an unrelated sample-state claim. Never invent or recalculate numerical results. A ratio of diffusion coefficients is dimensionless, not a diffusion coefficient itself. Cite supplied source_ids only. Synthetic examples are not experimental calibration or validation. A correct fit does not identify a chemical species. Shared calibration bias does not disappear by repeating scans. A local integrity hash is not proof of a teacher's identity. Never control a spectrometer, execute commands, modify originals or claim completed experimental or teaching validation. If evidence is empty or missing, do not echo the question or system instructions. Give a direct refusal in the requested language, explain what independent evidence is needed, set source_ids to [] and status to insufficient_evidence. Never repeat an unsupported claim as your own answer. Reply with a JSON object only: {\"answer\":\"a concise sourced explanation\",\"source_ids\":[\"supplied source id\"],\"status\":\"answer\"}. /no_think";
    private readonly string _knowledgePath, _modelDirectory;
    private readonly bool _allowPendingNativeEvaluation;
    private readonly SemaphoreSlim _gate = new(1, 1);
    private JsonDocument? _knowledge, _manifest;
    private string? _knowledgeSha256, _modelSha256;
    private LLamaWeights? _weights;
    private bool _disposed;
    public bool IsModelInstalled => File.Exists(Path.Combine(_modelDirectory, "manifest.json"));
    public string ModelStatus { get; private set; } = "not_loaded";
    private readonly bool _captureEvaluationDiagnostics;
    public JsonElement? LastEvaluationDiagnostics { get; private set; }

    public ResearchTutorService(string knowledgePath, string modelDirectory, bool allowPendingNativeEvaluation = false, bool captureEvaluationDiagnostics = false)
    {
        _knowledgePath = Path.GetFullPath(knowledgePath);
        _modelDirectory = Path.GetFullPath(modelDirectory);
        _allowPendingNativeEvaluation = allowPendingNativeEvaluation;
        _captureEvaluationDiagnostics = captureEvaluationDiagnostics;
    }

    public IReadOnlyList<TutorSource> GetTopicSources(string topic)
    {
        EnsureKnowledge();
        var chunk = Topic(topic);
        return chunk.ValueKind == JsonValueKind.Object ? Sources(chunk) : Array.Empty<TutorSource>();
    }

    public async Task<TutorAnswer> AskAsync(string language, string question, string topic, string? contextJson,
        CancellationToken cancellationToken, IProgress<string>? progress = null, int hintLevel = 2)
    {
        language = language == "en" ? "en" : "es";
        if (string.IsNullOrWhiteSpace(question) || question.Length > 2000) throw new ArgumentException("A bounded question is required.", nameof(question));
        if (hintLevel is < 0 or > 2) throw new ArgumentOutOfRangeException(nameof(hintLevel));
        if (contextJson is { Length: > 16000 }) throw new ArgumentException("Research context exceeds the local limit.", nameof(contextJson));
        JsonElement? context = null;
        if (!string.IsNullOrWhiteSpace(contextJson))
        {
            using var parsed = JsonDocument.Parse(contextJson);
            if (parsed.RootElement.ValueKind != JsonValueKind.Object) throw new ArgumentException("Research context must be an object.", nameof(contextJson));
            RejectHiddenTruth(parsed.RootElement);
            context = parsed.RootElement.Clone();
        }
        await _gate.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            ObjectDisposedException.ThrowIf(_disposed, this);
            if (_captureEvaluationDiagnostics) LastEvaluationDiagnostics = null;
            cancellationToken.ThrowIfCancellationRequested();
            var timer = Stopwatch.StartNew();
            EnsureKnowledge();
            var chunk = Topic(topic);
            if (chunk.ValueKind != JsonValueKind.Object)
            {
                ModelStatus = "research_topic_unknown";
                return new TutorAnswer(language == "es" ? "No hay una fuente revisada para este tema. Selecciona un bloque del recorrido de investigación." : "No reviewed source is available for this topic. Select a research-pathway block.",
                    language == "es" ? "Guía documental · sin LLM" : "Documentary guide · no LLM", Array.Empty<TutorSource>(), false, ModelStatus, null, null, timer.Elapsed.TotalSeconds);
            }
            var sources = Sources(chunk);
            if (IsContradictoryPulseContext(question, CalculationContext(context)))
            {
                ModelStatus = "contradictory_pulse_context";
                var guide = Documentary(language, chunk, sources, hintLevel, timer.Elapsed.TotalSeconds, ModelStatus);
                return guide with { Text = (language == "es" ? "La pregunta menciona360° pero el cálculo aportado supone180°. Identifica el cruce antes de usar un divisor; no se genera una respuesta numérica.\n\n" : "The question mentions360 degrees but the supplied calculation assumes180 degrees. Identify the crossing before choosing a divisor; no numerical answer is generated.\n\n") + guide.Text };
            }
            if (hintLevel < 2)
            {
                ModelStatus = "reviewed_socratic_hint";
                return Documentary(language, chunk, sources, hintLevel, timer.Elapsed.TotalSeconds, ModelStatus);
            }
            if (!IsModelInstalled)
            {
                ModelStatus = "research_model_not_installed";
                return Documentary(language, chunk, sources, hintLevel, timer.Elapsed.TotalSeconds, ModelStatus);
            }
            try
            {
                return await Task.Run(async () =>
                {
                    progress?.Report(language == "es" ? "Beatrix · verificando candidato y fuentes locales…" : "Beatrix · verifying local model and sources…");
                    await EnsureModelAsync(cancellationToken).ConfigureAwait(false);
                    var body = EvidenceText(chunk, language);
                    var calculationContext = CalculationContext(context);
                    var causalAnchor = CausalAnchor(chunk, language, calculationContext);
                    var payload = new
                    {
                        language,
                        module_id = topic,
                        evidence = new[] { new { id = topic, title = Local(chunk, "title", language), body, source_ids = sources.Select(s => s.Id).ToArray() } },
                        simulation_context = context,
                        calculation_context = calculationContext,
                        original_question = question,
                        question = CanonicalPulseQuestion(language, question, calculationContext),
                        reviewed_causal_anchor = causalAnchor
                    };
                    var prompt = TutorService.ChatPrompt(SystemInstructions, AsciiJson(payload));
                    var promptSha = ShaText(prompt);
                    if (_captureEvaluationDiagnostics) LastEvaluationDiagnostics = JsonSerializer.SerializeToElement(new { original_question=question, prompt_payload=payload, prompt_sha256=promptSha, model_sha256=_modelSha256 });
                    var tokens = _weights!.Tokenize(prompt, false, true, Encoding.UTF8);
                    if (tokens.Length > 3450)
                    {
                        ModelStatus = "research_context_too_long";
                        return Documentary(language, chunk, sources, hintLevel, timer.Elapsed.TotalSeconds, ModelStatus);
                    }
                    using var native = _weights.CreateContext(Parameters(Path.Combine(_modelDirectory, RequiredText(_manifest!.RootElement, "File"))));
                    var batch = new LLamaBatch();
                    for (var offset = 0; offset < tokens.Length; offset += 64)
                    {
                        cancellationToken.ThrowIfCancellationRequested();
                        batch.Clear();
                        for (var i = offset; i < Math.Min(offset + 64, tokens.Length); i++) batch.Add(tokens[i], i, LLamaSeqId.Zero, i == tokens.Length - 1);
                        if (await native.DecodeAsync(batch, cancellationToken).ConfigureAwait(false) != DecodeResult.Ok) throw new InvalidDataException("Research prefill failed.");
                    }
                    // Free generation mirrors the frozen HF evaluation. A JSON
                    // parser and source/numeric guards inspect the actual answer.
                    using var sampling = new DefaultSamplingPipeline { Temperature = 0, Seed = 261030 };
                    var decoder = new StreamingTokenDecoder(native) { DecodeSpecialTokens = false };
                    var output = new StringBuilder();
                    progress?.Report(language == "es" ? "Beatrix · preparando explicación con fuentes…" : "Beatrix · preparing a sourced explanation…");
                    var ended = false;
                    for (var i = 0; i < 384; i++)
                    {
                        cancellationToken.ThrowIfCancellationRequested();
                        var token = sampling.Sample(native.NativeHandle, batch.TokenCount - 1);
                        if (token.IsEndOfGeneration(_weights.Vocab)) { ended = true; break; }
                        decoder.Add(token); output.Append(decoder.Read());
                        batch.Clear(); batch.Add(token, tokens.Length + i, LLamaSeqId.Zero, true);
                        if (await native.DecodeAsync(batch, cancellationToken).ConfigureAwait(false) != DecodeResult.Ok) throw new InvalidDataException("Research generation failed.");
                    }
                    if (!ended) throw new InvalidDataException("Research generation exceeded its bounded output.");
                    if (_captureEvaluationDiagnostics) LastEvaluationDiagnostics = JsonSerializer.SerializeToElement(new { prompt=LastEvaluationDiagnostics, raw_generated_output=output.ToString(), ended, diagnostic_only=true, student_ui_exposed=false });
                    using var result = JsonDocument.Parse(output.ToString());
                    var response = result.RootElement;
                    var answer = RequiredText(response, "answer");
                    var status = RequiredText(response, "status");
                    if (status != "answer" || answer.Length is < 15 or > 10000) throw new InvalidDataException("Research answer has insufficient supplied evidence.");
                    if (!response.TryGetProperty("source_ids", out var ids) || ids.ValueKind != JsonValueKind.Array) throw new InvalidDataException("Research answer lacks source IDs.");
                    var used = ids.EnumerateArray().Select(i => i.GetString() ?? "").ToArray();
                    var allowed = sources.Select(s => s.Id).ToHashSet(StringComparer.Ordinal);
                    if (used.Length == 0 || used.Any(i => !allowed.Contains(i))) throw new InvalidDataException("Research answer contains an unsupported source.");
                    if (!SupportedNumbers(answer, body + "\n" + AsciiJson(causalAnchor) + "\n" + (contextJson ?? ""), calculationContext)) throw new InvalidDataException("Research answer changed or invented a numerical result.");
                    var generatedSources = sources.Where(s => used.Contains(s.Id, StringComparer.Ordinal)).ToArray();
                    var quote = Local(chunk, "why", language) + "\n\n" + Local(chunk, "body", language);
                    ModelStatus = _allowPendingNativeEvaluation ? "research_candidate_native_evaluation" : "research_local_llm_with_reviewed_guidance";
                    var lead = language == "es" ? "Explicación generada localmente:\n" : "Locally generated explanation:\n";
                    var quoteLead = language == "es" ? "\n\nGuía revisada, citada literalmente:\n" : "\n\nReviewed guidance, quoted literally:\n";
                    var trainedTopics = _manifest.RootElement.TryGetProperty("ResearchTopicsIncludedInTraining", out var topics) && topics.ValueKind == JsonValueKind.Array
                        && topics.EnumerateArray().Any(t => t.GetString() == topic);
                    return new TutorAnswer(lead + answer + quoteLead + quote,
                        language == "es" ? "Beatrix · LLM local + guía revisada" : "Beatrix · local LLM + reviewed guidance",
                        sources, true, ModelStatus, _modelSha256, promptSha, timer.Elapsed.TotalSeconds,
                        true, quote, answer, sources, generatedSources, true, _knowledgeSha256, trainedTopics);
                }, cancellationToken).ConfigureAwait(false);
            }
            catch (OperationCanceledException) { throw; }
            catch (Exception ex) when (ex is JsonException or InvalidDataException or IOException or InvalidOperationException or DllNotFoundException or EntryPointNotFoundException or NotSupportedException)
            {
                Trace.WriteLine(ex.Message, "DiffAtOnce.Academy.ResearchTutor");
                if (_captureEvaluationDiagnostics) LastEvaluationDiagnostics = JsonSerializer.SerializeToElement(new { generation=LastEvaluationDiagnostics, rejection_reason=ex.Message, diagnostic_only=true, student_ui_exposed=false });
                ModelStatus = "research_documentary_fallback";
                return Documentary(language, chunk, sources, hintLevel, timer.Elapsed.TotalSeconds, ModelStatus);
            }
        }
        finally { _gate.Release(); }
    }

    private void EnsureKnowledge()
    {
        if (_knowledge is not null) return;
        var file = new FileInfo(_knowledgePath);
        if (!file.Exists || file.Length is < 100 or > 2000000) throw new InvalidDataException("Research knowledge is missing or outside the local limit.");
        var bytes = File.ReadAllBytes(_knowledgePath);
        var document = JsonDocument.Parse(bytes);
        var root = document.RootElement;
        if (RequiredText(root, "version") != "1.3.0" || !root.TryGetProperty("chunks", out var chunks) || chunks.ValueKind != JsonValueKind.Array || chunks.GetArrayLength() is < 1 or > 100)
        { document.Dispose(); throw new InvalidDataException("Research knowledge version is invalid."); }
        var ids = new HashSet<string>(StringComparer.Ordinal);
        foreach (var chunk in chunks.EnumerateArray())
        {
            if (!ids.Add(RequiredText(chunk, "id"))) throw new InvalidDataException("Duplicate research topic.");
            foreach (var language in new[] { "es", "en" }) foreach (var field in new[] { "title", "question", "objective", "why", "body" })
                if (Local(chunk, field, language).Length == 0) throw new InvalidDataException("Research knowledge lacks a bilingual field.");
            if (!chunk.TryGetProperty("sources", out var sources) || sources.ValueKind != JsonValueKind.Array || sources.GetArrayLength() == 0) throw new InvalidDataException("Research topic lacks sources.");
            foreach (var source in sources.EnumerateArray()) { RequiredText(source, "id"); RequiredText(source, "title"); RequiredText(source, "path"); }
        }
        _knowledgeSha256 = Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
        _knowledge = document;
    }

    private async Task EnsureModelAsync(CancellationToken cancellationToken)
    {
        if (_weights is not null) return;
        _manifest?.Dispose();
        _manifest = JsonDocument.Parse(await File.ReadAllTextAsync(Path.Combine(_modelDirectory, "manifest.json"), cancellationToken).ConfigureAwait(false));
        var manifest = _manifest.RootElement;
        var file = RequiredText(manifest, "File");
        if (Path.GetFileName(file) != file || !file.EndsWith(".gguf", StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException("Research model filename is invalid.");
        if (!True(manifest, "FineTuned") || !True(manifest, "QualityPassed") || !True(manifest, "ResearchQualityPassed") || !True(manifest, "LocalOnly") || True(manifest, "ExperimentalValidation")
            || RequiredText(manifest, "ResearchKnowledgeSha256") != _knowledgeSha256) throw new InvalidDataException("Research model has not passed its source-bound quality gate.");
        if (!_allowPendingNativeEvaluation && (!True(manifest, "NativeEvaluationPassed") || !True(manifest, "NativeResearchEvaluationPassed") || True(manifest, "NativeEvaluationPending")))
            throw new InvalidDataException("Quantized native research qualification is incomplete.");
        _modelSha256 = RequiredText(manifest, "Sha256");
        await CheckHashAsync(Path.Combine(_modelDirectory, file), _modelSha256, cancellationToken).ConfigureAwait(false);
        await CheckHashAsync(Path.Combine(_modelDirectory, "training_report.json"), RequiredText(manifest, "TrainingReportSha256"), cancellationToken).ConfigureAwait(false);
        await CheckHashAsync(Path.Combine(_modelDirectory, "evaluation_report.json"), RequiredText(manifest, "EvaluationReportSha256"), cancellationToken).ConfigureAwait(false);
        if (!_allowPendingNativeEvaluation)
            await CheckHashAsync(Path.Combine(_modelDirectory, "native_evaluation_report.json"), RequiredText(manifest, "NativeEvaluationReportSha256"), cancellationToken).ConfigureAwait(false);
        _weights = await LLamaWeights.LoadFromFileAsync(Parameters(Path.Combine(_modelDirectory, file)), cancellationToken).ConfigureAwait(false);
    }

    private TutorAnswer Documentary(string language, JsonElement chunk, IReadOnlyList<TutorSource> sources, int hintLevel, double elapsed, string status)
    {
        var field = hintLevel == 0 ? "question" : hintLevel == 1 ? "why" : "body";
        var quote = Local(chunk, field, language);
        var lead = hintLevel < 2
            ? language == "es" ? "Pista progresiva revisada:\n" : "Reviewed progressive hint:\n"
            : language == "es" ? "Guía documental revisada. No se ha generado una respuesta con el LLM.\n\n" : "Reviewed documentary guidance. No LLM answer was generated.\n\n";
        return new TutorAnswer(lead + quote, language == "es" ? "Guía de investigación · sin LLM" : "Research guide · no LLM",
            sources, false, status, null, null, elapsed, true, quote, null, sources, Array.Empty<TutorSource>(), true, _knowledgeSha256, false);
    }

    private JsonElement Topic(string topic) => _knowledge!.RootElement.GetProperty("chunks").EnumerateArray().FirstOrDefault(c => c.GetProperty("id").GetString() == topic);
    private IReadOnlyList<TutorSource> Sources(JsonElement chunk) => chunk.GetProperty("sources").EnumerateArray().Select(s =>
    {
        var doi = s.TryGetProperty("doi", out var d) ? d.GetString() : null;
        var title = RequiredText(s, "title") + " [" + RequiredText(s, "path") + "]";
        return new TutorSource(RequiredText(s, "id"), title, doi is null ? null : "https://doi.org/" + doi, doi is null ? _knowledgePath : null, null, doi);
    }).DistinctBy(s => s.Id).ToArray();
    private static string Local(JsonElement value, string field, string language) => value.TryGetProperty(field, out var text) && text.ValueKind == JsonValueKind.Object && text.TryGetProperty(language, out var localized) ? localized.GetString() ?? "" : "";
    private static string RequiredText(JsonElement value, string field) => value.TryGetProperty(field, out var text) && text.ValueKind == JsonValueKind.String && !string.IsNullOrWhiteSpace(text.GetString()) ? text.GetString()! : throw new InvalidDataException("Required field missing: " + field);
    private static bool True(JsonElement value, string field) => value.TryGetProperty(field, out var v) && v.ValueKind == JsonValueKind.True;
    private static string EvidenceText(JsonElement chunk, string language) => string.Join("\n", new[] { Local(chunk, "objective", language), Local(chunk, "why", language), Local(chunk, "body", language), "Equation: " + RequiredText(chunk, "equation"), "Units: " + RequiredText(chunk, "units"), "Assumptions: " + string.Join("; ", chunk.GetProperty("assumptions").EnumerateArray().Select(s => s.GetString())) });
    private static ModelParams Parameters(string path) => new(path) { ContextSize = 4096, GpuLayerCount = 0, UseMemorymap = true, Threads = Math.Clamp(Environment.ProcessorCount / 2, 1, 4), BatchThreads = Math.Clamp(Environment.ProcessorCount / 2, 1, 4), BatchSize = 128, UBatchSize = 64 };
    private static string ShaText(string value) => Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(value))).ToLowerInvariant();
    private static async Task CheckHashAsync(string path, string expected, CancellationToken token)
    {
        if (!Regex.IsMatch(expected, "^[a-f0-9]{64}$", RegexOptions.CultureInvariant)) throw new InvalidDataException("Malformed research provenance hash.");
        await using var stream = File.OpenRead(path);
        if (!Convert.ToHexString(await SHA256.HashDataAsync(stream, token).ConfigureAwait(false)).Equals(expected, StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException("Research model or provenance hash mismatch.");
    }
    private static string AsciiJson(object value)
    {
        var json = JsonSerializer.Serialize(value, new JsonSerializerOptions { Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping });
        var result = new StringBuilder();
        foreach (var c in json) { if (c > 127) result.Append("\\u").Append(((int)c).ToString("x4", CultureInfo.InvariantCulture)); else result.Append(c); }
        // User/evidence text is JSON data, never a ChatML role delimiter.
        // Normal teaching prompts retain the trained byte sequence.
        return result.ToString().Replace("<|", "\\u003c|", StringComparison.Ordinal);
    }
    private static JsonElement? CalculationContext(JsonElement? context)
    {
        if (context is null) return null;
        if (context.Value.TryGetProperty("calculation_context", out var value) || context.Value.TryGetProperty("calculationContext", out value)) return value.ValueKind == JsonValueKind.Object ? value.Clone() : null;
        return null;
    }
    private static object CausalAnchor(JsonElement chunk, string language, JsonElement? calculation)
    {
        var formula = calculation is { ValueKind: JsonValueKind.Object } && calculation.Value.TryGetProperty("calculation", out var v) && v.ValueKind == JsonValueKind.String ? (v.GetString() ?? "").Replace(" ", "", StringComparison.Ordinal) : "";
        if (formula == "P90=P180/2")
            return new
            {
                principle = language == "es" ? "El ángulo RF es proporcional a la duración a potencia fija; dividir entre dos exige un cruce180° identificado." : "RF flip angle is proportional to duration at fixed power; division by two requires an identified180-degree crossing.",
                conditions = language == "es" ? "Identificar el primer180 mediante máximo anterior y cambio de polaridad; misma potencia RF." : "Identify the first180 crossing using the preceding maximum and polarity change; unchanged RF power.",
                scope = language == "es" ? "Ejemplo sintético; no es una calibración realizada." : "Synthetic example; not a performed calibration."
            };
        if (formula == "P90=P360/4")
            return new
            {
                principle = language == "es" ? "A B1/potencia fija, theta=gamma*B1*t. Un cruce de 360° identificado requiere un cuarto de su duración para 90°, no la mitad." : "At fixed B1/power, theta=gamma*B1*t. An identified 360-degree crossing requires one quarter of its duration for 90 degrees, not one half.",
                conditions = language == "es" ? "Identificar el orden del cruce por la trayectoria y polaridad de la nutación; mantener potencia RF fija." : "Identify crossing order from the nutation trajectory and polarity; keep RF power fixed.",
                scope = language == "es" ? "Ejemplo sintético; no es una calibración realizada." : "Synthetic example; not a performed calibration."
            };
        if (formula == "b_scale=gradient_scale^2")
            return new
            {
                principle = language == "es" ? "q es lineal en el gradiente y b=integral(q² dt); por eso escala cuadráticamente." : "q is linear in gradient and b=integral(q squared dt), so b scales quadratically.",
                conditions = language == "es" ? "Escalar toda la forma efectiva de gradiente; mantener forma, delta, Delta y todos los tiempos." : "Scale the entire effective gradient waveform; preserve shape, delta, Delta and all timings.",
                scope = language == "es" ? "Un factor calculado no calibra un gradiente experimental." : "A computed factor does not calibrate an experimental gradient."
            };
        if (formula == "D_ratio=gradient_scale^2")
            return new
            {
                principle = language == "es" ? "D_ratio significa D_nominal/D_reference, no D absoluta. Si la forma completa escala por s, b y ese cociente escalan por s²." : "D_ratio means D_nominal/D_reference, not absolute D. If the complete waveform scales by s, b and that ratio scale by s squared.",
                conditions = language == "es" ? "Misma forma y tiempos; error de calibración compartido entre réplicas." : "Same waveform and timings; calibration error shared by replicates.",
                scope = language == "es" ? "Repetir puede reducir ruido, pero no elimina el sesgo compartido." : "Repeating may reduce noise but does not remove shared bias."
            };
        if (formula == "noise_ratio=1/sqrt(replicates)")
            return new
            {
                principle = language == "es" ? "Para ruido independiente, la desviación estándar del promedio escala como1/sqrt(N)." : "For independent noise, the standard deviation of the average scales as1/sqrt(N).",
                conditions = language == "es" ? "Réplicas independientes del mismo estado de muestra; calibración compartida." : "Independent replicates of the same sample state; shared calibration.",
                scope = language == "es" ? "El sesgo común de calibración permanece; son supuestos del ejemplo sintético." : "Common calibration bias remains; these are assumptions of the synthetic example."
            };
        return new
        {
            principle = Local(chunk, "why", language),
            conditions = chunk.GetProperty("assumptions").EnumerateArray().Select(a => a.GetString()).ToArray(),
            scope = language == "es" ? "Guía revisada; no validación experimental ni evaluación semántica automática." : "Reviewed guidance; not experimental validation or automatic semantic grading."
        };
    }
    private static string CanonicalPulseQuestion(string language, string original, JsonElement? calculation)
    {
        if (calculation is { ValueKind: JsonValueKind.Object } && calculation.Value.TryGetProperty("calculation", out var formula) && formula.ValueKind == JsonValueKind.String &&
            formula.GetString()?.Replace(" ", "", StringComparison.Ordinal) == "P90=P360/4" && Regex.IsMatch(original, @"(?<![0-9])360(?![0-9])", RegexOptions.CultureInvariant) &&
            calculation.Value.TryGetProperty("inputs", out var source) && source.TryGetProperty("p360_us", out var pulse360) && pulse360.TryGetDouble(out var p360) && double.IsFinite(p360) && p360 > 0)
        {
            var duration = p360.ToString("G8", CultureInfo.InvariantCulture);
            return language == "es" ? $"Ejemplo sintético: el cruce360 identificado está en {duration} us a potencia fija. Da el resultado P90 y su unidad del contexto; explica explícitamente por qué el cruce360 exige dividir entre cuatro y qué se comprueba en original_question."
                : $"Synthetic example: the identified360 crossing is at {duration} us at fixed power. Give the supplied P90 result and unit; explicitly explain why the360 crossing requires division by four and address the checks in original_question.";
        }
        if (calculation is not { ValueKind: JsonValueKind.Object } || !calculation.Value.TryGetProperty("calculation", out var c) || c.ValueKind != JsonValueKind.String
            || c.GetString()?.Replace(" ", "", StringComparison.Ordinal) != "P90=P180/2"
            || !Regex.IsMatch(original, @"P90|90\s*(?:°|degrees?|grados?)", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant)
            || IsContradictoryPulseContext(original, calculation)
            || !calculation.Value.TryGetProperty("inputs", out var inputs) || !inputs.TryGetProperty("p180_us", out var pulse) || !pulse.TryGetDouble(out var value) || !double.IsFinite(value) || value <= 0) return original;
        var p180 = value.ToString("G8", CultureInfo.InvariantCulture);
        var first = Regex.IsMatch(original, @"\b(?:first|primer(?:o)?)\b", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);
        return language == "es" ? $"Ejemplo sintético: el {(first ? "primer " : "")}cruce180 identificado está en {p180} us a potencia fija. Explica P90, la condición y una comprobación."
            : $"Synthetic example: the {(first ? "first " : "")}identified180 crossing is at {p180} us at fixed power. Explain P90, its condition and one check.";
    }

    public static bool IsContradictoryPulseContext(string question, JsonElement? calculation) =>
        calculation is { ValueKind: JsonValueKind.Object } && calculation.Value.TryGetProperty("calculation", out var c) && c.ValueKind == JsonValueKind.String &&
        c.GetString()?.Replace(" ", "", StringComparison.Ordinal) == "P90=P180/2" && Regex.IsMatch(question, @"(?<![0-9])360(?![0-9])", RegexOptions.CultureInvariant);

    /// <summary>The legacy prose parser recognizes only textbook examples.
    /// Reject ambiguous pulse durations or incomplete/changing diffusion
    /// timings before the mixed model receives a canonical numerical task.</summary>
    public static bool IsAmbiguousLegacyCalculation(string question, JsonElement calculation)
    {
        var formula = calculation.GetProperty("calculation").GetString()?.Replace(" ", "", StringComparison.Ordinal);
        if (formula == "P90=P180/2")
        {
            var durations = Regex.Matches(question, @"(?<![A-Za-z0-9_])([0-9]+(?:[.,][0-9]+)?)\s*(?:µs|μs|us|microseconds|microsegundos)\b", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant)
                .Select(m => double.Parse(m.Groups[1].Value.Replace(',', '.'), CultureInfo.InvariantCulture)).Distinct().ToArray();
            return durations.Length != 1;
        }
        if (formula == "b_scale=gradient_scale^2")
        {
            var namedPair = Regex.IsMatch(question, @"\bdelta\s*(?:and|y|,|/)\s*delta\b", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant) || question.Contains('δ') && question.Contains('Δ');
            var fixedPair = namedPair && Regex.IsMatch(question, @"(?:delta|δ|Δ).{0,45}(?:unchanged|remain\s+fixed|are\s+fixed|no\s+cambian|fijos|constantes)|(?:fixed|keep|manteniendo).{0,25}(?:delta|δ|Δ)", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);
            var changedTiming = Regex.IsMatch(question, @"(?:\bdelta\b|δ|Δ).{0,12}\b(?:doubles?|changes?|increases?|decreases?|cambia|duplica|aumenta|disminuye)\b", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);
            return !fixedPair || changedTiming;
        }
        return true;
    }

    /// <summary>Compatibility for two explicitly typed legacy worked examples.
    /// It preserves supplied results/evidence, while using the mixed model's
    /// actually trained result-label and causal-anchor protocol. No result is
    /// inferred from the student's prose or substituted by the model.</summary>
    public static bool TryLegacyNumericPrompt(string language, string question, string moduleId, object calculationContext,
        object evidencePayload, out string system, out string userJson, JsonElement? simulationContext = null)
    {
        system = ""; userJson = "";
        var trace = JsonSerializer.SerializeToElement(calculationContext);
        if (!trace.TryGetProperty("calculation", out var computation) || computation.ValueKind != JsonValueKind.String
            || !trace.TryGetProperty("inputs", out var inputs) || !trace.TryGetProperty("result", out var numeric)
            || !numeric.TryGetDouble(out var value) || !double.IsFinite(value) || value <= 0) return false;
        var formula = (computation.GetString() ?? "").Replace(" ", "", StringComparison.Ordinal);
        var pulse = formula == "P90=P180/2" && moduleId == "pulse-calibration";
        var gradient = formula == "b_scale=gradient_scale^2" && moduleId is "sequence-b" or "gradient-calibration";
        if ((!pulse && !gradient) || IsContradictoryPulseContext(question, trace) || IsAmbiguousLegacyCalculation(question, trace)) return false;
        var normalized = JsonSerializer.SerializeToElement(new
        {
            kind = "synthetic-worked-example", calculation = formula, inputs, result = value,
            result_label = pulse ? "P90" : "b_scale", unit = pulse ? "us" : "factor", experimental_calibration = false,
            assumptions = trace.TryGetProperty("assumptions", out var assumptions) ? assumptions.Clone() : (JsonElement?)null
        });
        var canonical = CanonicalPulseQuestion(language, question, normalized);
        if (gradient)
        {
            if (!inputs.TryGetProperty("gradient_scale", out var scale) || !scale.TryGetDouble(out var g) || !double.IsFinite(g) || g <= 0) return false;
            var factor = g.ToString("G8", CultureInfo.InvariantCulture);
            canonical = language == "es" ? $"Ejemplo sintético: multiplicas toda la forma efectiva de gradiente por {factor}, con delta y Delta fijos. Explica b_scale y el mecanismo."
                : $"Synthetic example: multiply the entire effective gradient waveform by {factor}, with fixed delta and Delta. Explain b_scale and its mechanism.";
        }
        var payload = new { language, module_id = moduleId, evidence = evidencePayload, simulation_context = simulationContext,
            calculation_context = normalized, original_question = question, question = canonical, reviewed_causal_anchor = CausalAnchor(default, language, normalized) };
        system = SystemInstructions; userJson = AsciiJson(payload); return true;
    }
    private static void RejectHiddenTruth(JsonElement value)
    {
        if (value.ValueKind == JsonValueKind.Object)
            foreach (var property in value.EnumerateObject())
            {
                var key = property.Name.Replace("_", "", StringComparison.Ordinal).ToLowerInvariant();
                if (key.Contains("hiddentruth", StringComparison.Ordinal) || key is "truth" or "answerkey") throw new ArgumentException("Do not supply hidden case truth to the student tutor; pass visible observations and calculation results.");
                RejectHiddenTruth(property.Value);
            }
        else if (value.ValueKind == JsonValueKind.Array) foreach (var item in value.EnumerateArray()) RejectHiddenTruth(item);
    }
    private static IEnumerable<double> Numbers(string value)
    {
        foreach (Match match in Regex.Matches(value, @"(?<![A-Za-z0-9_])[-+]?(?:[0-9]+(?:[.,][0-9]+)?)(?:[eE][-+]?[0-9]+)?", RegexOptions.CultureInvariant))
            if (double.TryParse(match.Value.Replace(',', '.'), NumberStyles.Float, CultureInfo.InvariantCulture, out var number) && double.IsFinite(number)) yield return number;
    }
    private static bool SupportedNumbers(string answer, string evidence, JsonElement? calculation)
    {
        var allowed = Numbers(evidence).ToArray();
        if (Numbers(answer).Any(n => !allowed.Any(a => NumericClose(n, a)))) return false;
        if (calculation is not { ValueKind: JsonValueKind.Object } || !calculation.Value.TryGetProperty("result", out var result)) return true;
        return HasConsistentLabeledResult(answer, calculation.Value);
    }

    private static bool NumericClose(double actual, double expected) => double.IsFinite(actual) && double.IsFinite(expected) &&
        Math.Abs(actual - expected) <= Math.Max(double.Epsilon * 8, Math.Max(Math.Abs(actual), Math.Abs(expected)) * 1e-6);

    /// <summary>Check every explicit result assignment, with a tolerance that
    /// scales to small physical quantities. A number mentioned elsewhere does
    /// not show that the answer assigns the correct result.</summary>
    public static bool HasConsistentLabeledResult(string answer, JsonElement calculation)
    {
        if (!calculation.TryGetProperty("result", out var result) || !result.TryGetDouble(out var expected) || !double.IsFinite(expected)) return false;
        var label = calculation.TryGetProperty("result_label", out var l) && l.ValueKind == JsonValueKind.String ? l.GetString() : null;
        if (string.IsNullOrWhiteSpace(label) && calculation.TryGetProperty("calculation", out var c) && c.ValueKind == JsonValueKind.String)
            label = c.GetString()?.Replace(" ", "", StringComparison.Ordinal) switch { "P90=P180/2" or "P90=P360/4" => "P90", "b_scale=gradient_scale^2" => "b_scale", _ => null };
        if (string.IsNullOrWhiteSpace(label)) return false;
        var matches = Regex.Matches(answer, @"(?<![A-Za-z0-9_])" + Regex.Escape(label) + @"\s*[=:]\s*([-+]?[0-9]+(?:[.,][0-9]+)?(?:[eE][-+]?[0-9]+)?)(?:\s*([A-Za-zµμ²0-9^/]+))?", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);
        var expectedUnit = calculation.TryGetProperty("unit", out var u) && u.ValueKind == JsonValueKind.String ? NormalizeUnit(u.GetString() ?? "") : "";
        return expectedUnit.Length > 0 && matches.Count > 0 && matches.All(match => double.TryParse(match.Groups[1].Value.Replace(',', '.'), NumberStyles.Float, CultureInfo.InvariantCulture, out var actual) && NumericClose(actual, expected) && NormalizeUnit(match.Groups[2].Value) == expectedUnit);
    }

    private static string NormalizeUnit(string unit) => unit.Trim().ToLowerInvariant().Replace("²", "2", StringComparison.Ordinal).Replace("^", "", StringComparison.Ordinal) switch
    {
        "us" or "µs" or "μs" or "microsecond" or "microseconds" or "microsegundo" or "microsegundos" => "us",
        "factor" or "ratio" or "dimensionless" or "adimensional" => "factor",
        var value => value
    };

    public async ValueTask DisposeAsync()
    {
        await _gate.WaitAsync().ConfigureAwait(false);
        try { if (_disposed) return; _disposed = true; _weights?.Dispose(); _knowledge?.Dispose(); _manifest?.Dispose(); _weights = null; _knowledge = null; _manifest = null; }
        finally { _gate.Release(); }
    }
}
