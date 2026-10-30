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

public sealed record TutorSource(string Id, string Title, string? Url, string? LocalPath, int? Slide,
    string? Doi = null, IReadOnlyList<int>? Pages = null, IReadOnlyList<string>? Equations = null);
public sealed record TutorAnswer(string Text, string EngineLabel, IReadOnlyList<TutorSource> Sources,
    bool IsModelAnswer, string Status, string? ModelSha256, string? PromptSha256, double ElapsedSeconds,
    bool IncludesCourseQuote = false, string? CourseQuote = null, string? GeneratedText = null,
    IReadOnlyList<TutorSource>? CourseQuoteSources = null, IReadOnlyList<TutorSource>? GeneratedSources = null,
    bool IncludesSupplementalEvidence = false, string? SupplementalSha256 = null, bool SupplementalIncludedInTraining = false);

/// <summary>Offline, read-only student tutor. There is no network client or instrument API.
/// Native CPU inference is serialized, bounded to four threads and cancellable
/// between 64-token prefill chunks and every output token. Numeric context is
/// supplied by the teaching simulator; the LLM never changes scientific values.</summary>
public sealed class TutorService : IAsyncDisposable
{
    public const string SystemInstructions = "You are Beatrix, a bilingual NMR diffusion teaching assistant. Explain the selected evidence in the requested language. Use only the supplied course evidence and numeric simulation context. All simulation values are synthetic, never experimental calibration or validation. Cite supplied source_ids only. State missing assumptions, units and limitations. Do not invent pulse-sequence b equations, calibration factors, results, source identifiers or measurements. Do not execute commands, contact a spectrometer, modify files or claim you performed calibration. Distinguish laboratory time t_lab, diffusion delay Delta and readout time t_read. ILT is ill-conditioned; fit quality does not identify a molecule. Never replace experimental TBO calibration by a nominal gradient or rescale KK2 to old mass tables. Reply with a JSON object only: {\"answer\":\"a concise teaching explanation\",\"source_ids\":[\"supplied source id\"],\"status\":\"answer\"}. When evidence is missing use status insufficient_evidence and state what is missing. /no_think";
    private static readonly string GroundedInstructions = SystemInstructions.Replace("Reply with a JSON", "When calculation_context is supplied, explain its deterministic result exactly; never replace it with an LLM calculation. Reviewed course question/answer pairs are supplied evidence. Reply with a JSON", StringComparison.Ordinal);
    private static readonly string ExplanatoryInstructions = GroundedInstructions.Replace("When calculation_context", "Answer the actual student's question directly in two to four sentences: first explain the causal mechanism, then a practical check or limitation. When calculation_context", StringComparison.Ordinal);
    private static readonly JsonSerializerOptions JsonOptions = new() { PropertyNameCaseInsensitive = true };
    private readonly string _knowledgePath;
    private readonly string _modelDirectory;
    private readonly string _derivationsPath;
    private readonly bool _captureEvaluationDiagnostics;
    private readonly bool _allowPendingResearchNativeEvaluation;
    private readonly SemaphoreSlim _gate = new(1, 1);
    private JsonDocument? _course;
    private string? _courseHash;
    private LLamaWeights? _weights;
    private TutorManifest? _manifest;
    private SupplementalKnowledge? _supplemental;
    private bool _disposed;
    public bool IsModelInstalled => File.Exists(Path.Combine(_modelDirectory, "manifest.json"));
    public string ModelStatus { get; private set; } = "not_loaded";
    public string SupplementalStatus { get; private set; } = "not_requested";
    /// <summary>Only populated by an explicitly opted-in local evaluation harness.
    /// Normal student windows do not retain or expose rejected model output.</summary>
    public JsonElement? LastEvaluationDiagnostics { get; private set; }
    public TutorService(string knowledgePath, string modelDirectory, string? derivationsPath = null, bool captureEvaluationDiagnostics = false, bool allowPendingResearchNativeEvaluation = false)
    {
        _knowledgePath = Path.GetFullPath(knowledgePath);
        _modelDirectory = Path.GetFullPath(modelDirectory);
        _derivationsPath = Path.GetFullPath(derivationsPath ?? Path.Combine(Path.GetDirectoryName(_knowledgePath)!, "derivations.json"));
        _captureEvaluationDiagnostics = captureEvaluationDiagnostics;
        _allowPendingResearchNativeEvaluation = allowPendingResearchNativeEvaluation;
    }

    public IReadOnlyList<TutorSource> GetSupplementalSources(string chapterId)
    {
        if (!EnsureSupplemental()) return Array.Empty<TutorSource>();
        try { return _supplemental!.Sources(chapterId.StartsWith("derivation:", StringComparison.Ordinal) ? chapterId[11..] : chapterId); }
        catch (Exception ex) when (ex is InvalidDataException or InvalidOperationException or JsonException or KeyNotFoundException)
        { SupplementalStatus = "supplemental_invalid_references"; Trace.WriteLine(ex.Message, "DiffAtOnce.Academy.Tutor"); return Array.Empty<TutorSource>(); }
    }

    public IReadOnlyList<TutorSource> GetModuleSources(string moduleId)
    {
        EnsureCourse();
        var module = _course!.RootElement.GetProperty("modules").EnumerateArray().FirstOrDefault(m => Id(m) == moduleId);
        return module.ValueKind == JsonValueKind.Object ? Sources(module) : Array.Empty<TutorSource>();
    }

    public async Task<TutorAnswer> AskAsync(string language, string question, string moduleId, string? contextJson,
        CancellationToken cancellationToken, IProgress<string>? progress = null)
    {
        language = language == "en" ? "en" : "es";
        if (string.IsNullOrWhiteSpace(question)) throw new ArgumentException("A question is required.", nameof(question));
        if (question.Length > 2000) throw new ArgumentException("Question exceeds the 2000-character teaching limit.", nameof(question));
        if (contextJson is { Length: > 10000 }) throw new ArgumentException("Simulation context exceeds the 10000-character limit.", nameof(contextJson));
        if (!string.IsNullOrWhiteSpace(contextJson)) { using var validContext = JsonDocument.Parse(contextJson); }
        await _gate.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            ObjectDisposedException.ThrowIf(_disposed, this);
            if (_captureEvaluationDiagnostics) LastEvaluationDiagnostics = null;
            EnsureCourse(); cancellationToken.ThrowIfCancellationRequested();
            var timer = Stopwatch.StartNew();
            var evidence = Retrieve(language, question, moduleId);
            if (evidence.Count == 0) return EmptyAnswer(language, timer.Elapsed.TotalSeconds, moduleId.StartsWith("derivation:", StringComparison.Ordinal) ? SupplementalStatus : "insufficient_evidence");
            var sources = evidence.SelectMany(e => e.Sources).DistinctBy(s => s.Id).ToArray();
            // Actual CPU evaluations found unsupported causal claims for the
            // new papers. All supplemental chapters therefore use the exact
            // reviewed guide; this branch never loads or invokes the LLM.
            // Original lesson inference remains independently approved.
            if (evidence[0].IsSupplemental)
            {
                ModelStatus = "supplemental_documentary_only";
                var first = evidence[0];
                var lead = language == "es"
                    ? "Recorrido matemático revisado. Beatrix no genera respuestas sobre estos artículos: dos pruebas CPU produjeron afirmaciones físicas incorrectas. El modelo original sigue disponible en los módulos del curso.\n\n"
                    : "Reviewed mathematical pathway. Beatrix does not generate answers about these papers: two CPU evaluations produced incorrect physical claims. The original model remains available for course modules.\n\n";
                return new TutorAnswer(lead + first.Title + "\n\n" + first.Body,
                    language == "es" ? "Guía matemática revisada · sin LLM" : "Reviewed mathematical guide · no LLM",
                    first.Sources, false, ModelStatus, null, null, timer.Elapsed.TotalSeconds,
                    true, first.ReviewedQuote, null, first.Sources, Array.Empty<TutorSource>(), true, first.SupplementalSha256);
            }
            if (IsTemperatureFlowBoundaryQuestion(moduleId, question))
            {
                // The short model anchor did not answer the flow subquestion.
                // Supply the complete reviewed temperature and convection
                // modules without invoking or claiming an LLM explanation.
                var convection = Retrieve(language, question, "convection");
                var reviewed = evidence.Concat(convection).DistinctBy(e => e.Id).ToArray();
                var reviewedSources = reviewed.SelectMany(e => e.Sources).DistinctBy(s => s.Id).ToArray();
                var quote = string.Join("\n\n", reviewed.Select(e => e.Title + "\n" + e.Body));
                ModelStatus = "temperature_flow_documentary_only";
                var lead = language == "es"
                    ? "Esta pregunta combina escala de difusión y flujo. Se muestran las explicaciones revisadas de ambos módulos; no se genera una respuesta con el LLM. La escala TTMS/temperatura no elimina la convección: revise fase, varios Δ y controles térmicos o una secuencia compensada.\n\n"
                    : "This question combines diffusion scaling and flow. Reviewed explanations from both modules are shown; no LLM answer is generated. TTMS/temperature scaling does not remove convection: inspect phase, several Δ values, and thermal controls or a compensated sequence.\n\n";
                return new TutorAnswer(lead + quote,
                    language == "es" ? "Guía de temperatura y convección · sin LLM" : "Temperature and convection guide · no LLM",
                    reviewedSources, false, ModelStatus, null, null, timer.Elapsed.TotalSeconds,
                    true, quote, null, reviewedSources, Array.Empty<TutorSource>());
            }
            if (!IsModelInstalled) { ModelStatus = "model_not_installed"; return Documentary(language, evidence, sources, timer.Elapsed.TotalSeconds, "model_not_installed"); }
            try
            {
                return await Task.Run(async () =>
                {
                    progress?.Report(language == "es" ? "Beatrix · verificando modelo local…" : "Beatrix · verifying local model…");
                    await EnsureModelAsync(cancellationToken).ConfigureAwait(false);
                    var calculationContext = CalculationContext(moduleId, question);
                    if (_manifest!.ResearchQualityPassed && calculationContext is not null &&
                        ResearchTutorService.IsAmbiguousLegacyCalculation(question, JsonSerializer.SerializeToElement(calculationContext)))
                    {
                        ModelStatus = "ambiguous_typed_calculation";
                        var guide = Documentary(language, evidence, sources, timer.Elapsed.TotalSeconds, ModelStatus);
                        return guide with { Text = (language == "es" ? "La pregunta contiene duraciones ambiguas o no establece δ y Δ fijos. Aclara el cruce o los tiempos antes de asignar un resultado; no se genera una respuesta numérica.\n\n" : "The question has ambiguous durations or does not establish fixed delta and Delta. Clarify the crossing or timings before assigning a result; no numerical answer is generated.\n\n") + guide.Text };
                    }
                    if (_manifest!.ResearchQualityPassed && calculationContext is not null &&
                        ResearchTutorService.IsContradictoryPulseContext(question, JsonSerializer.SerializeToElement(calculationContext)))
                    {
                        ModelStatus = "contradictory_pulse_context";
                        var guide = Documentary(language, evidence, sources, timer.Elapsed.TotalSeconds, ModelStatus);
                        return guide with { Text = (language == "es" ? "La pregunta menciona360° pero el cálculo tipado supone180°. Identifica el cruce antes de elegir divisor; no se genera una respuesta numérica.\n\n" : "The question mentions360 degrees but the typed calculation assumes180 degrees. Identify the crossing before selecting a divisor; no numerical answer is generated.\n\n") + guide.Text };
                    }
                    // Put the actual question and deterministic result last:
                    // long source bodies must not displace the student's task.
                    var evidencePayload = evidence.Select(e => new { id = e.Id, title = e.Title, body = e.Body, source_ids = e.Sources.Select(s => s.Id) });
                    var simulationPayload = contextJson is null ? (JsonElement?)null : JsonSerializer.Deserialize<JsonElement>(contextJson);
                    object payload = calculationContext is not null
                        ? new { language, question = CanonicalCalculationQuestion(language, calculationContext), module_id = moduleId, simulation_context = simulationPayload, calculation_context = calculationContext, evidence = evidencePayload }
                        : new { language, module_id = moduleId, evidence = evidencePayload, simulation_context = simulationPayload, reviewed_course_anchor = TeachingFocus(language, moduleId), question, calculation_context = calculationContext };
                    var instructions = calculationContext is null ? ExplanatoryInstructions : GroundedInstructions;
                    if (evidence[0].IsSupplemental) instructions += " The supplemental papers are newly reviewed retrieval evidence, not part of this model's existing LoRA training. Preserve equation notation, assumptions and supplied DOI/page bounds. Explain differential-equation mechanisms but never invent numerical calibration, undocumented pulse sequences or experimental parameters.";
                    var promptUserJson = TrainingCompatibleJson(payload);
                    var promptProtocol = "legacy-course-protocol";
                    // Preserve the legacy path byte-for-byte for its original
                    // model. The newly trained mixed model has an explicit
                    // result-label/causal-anchor protocol for these two known
                    // deterministic examples; neither results nor sources change.
                    if (_manifest!.ResearchQualityPassed && calculationContext is not null &&
                        ResearchTutorService.TryLegacyNumericPrompt(language, question, moduleId, calculationContext, evidencePayload,
                            out var compatibleSystem, out var compatibleUser, simulationPayload))
                    {
                        instructions = compatibleSystem; promptUserJson = compatibleUser; promptProtocol = "mixed-research-typed-numeric-protocol";
                    }
                    var prompt = ChatPrompt(instructions, promptUserJson);
                    if (_captureEvaluationDiagnostics)
                        LastEvaluationDiagnostics = JsonSerializer.SerializeToElement(new { original_question = question, module_id = moduleId,
                            protocol = promptProtocol, original_calculation_context = calculationContext, prompt_payload = JsonSerializer.Deserialize<JsonElement>(promptUserJson),
                            prompt_sha256 = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(prompt))).ToLowerInvariant(),
                            model_sha256 = _manifest.Sha256, source_ids = sources.Select(s => s.Id).ToArray() });
                    var tokens = _weights!.Tokenize(prompt, false, true, Encoding.UTF8);
                    // Whole evidence documents are retained. A large context is a
                    // documented fallback, not a silently truncated scientific text.
                    if (tokens.Length > 3450) { ModelStatus = "context_too_long"; return Documentary(language, evidence, sources, timer.Elapsed.TotalSeconds, "context_too_long"); }
                    var parameters = Parameters(Path.Combine(_modelDirectory, _manifest!.File));
                    using var native = _weights.CreateContext(parameters);
                    var batch = new LLamaBatch();
                    for (var offset = 0; offset < tokens.Length; offset += 64)
                    {
                        cancellationToken.ThrowIfCancellationRequested(); batch.Clear();
                        for (var p = offset; p < Math.Min(offset + 64, tokens.Length); p++) batch.Add(tokens[p], p, LLamaSeqId.Zero, p == tokens.Length - 1);
                        if (await native.DecodeAsync(batch, cancellationToken).ConfigureAwait(false) != DecodeResult.Ok) throw new InvalidDataException("Native context prefill failed.");
                    }
                    using var sampling = new DefaultSamplingPipeline { Temperature = 0, Seed = 261005, Grammar = new Grammar(OutputGrammar(sources), "root") };
                    var decoder = new StreamingTokenDecoder(native) { DecodeSpecialTokens = false };
                    var output = new StringBuilder();
                    progress?.Report(language == "es" ? "Beatrix · preparando explicación con fuentes…" : "Beatrix · preparing a sourced explanation…");
                    var ended = false;
                    for (var i = 0; i < 512; i++)
                    {
                        cancellationToken.ThrowIfCancellationRequested(); var token = sampling.Sample(native.NativeHandle, batch.TokenCount - 1);
                        if (token.IsEndOfGeneration(_weights.Vocab)) { ended = true; break; }
                        decoder.Add(token); output.Append(decoder.Read());
                        if (output.Length > 10000) throw new InvalidDataException("Oversized tutor answer.");
                        batch.Clear(); batch.Add(token, tokens.Length + i, LLamaSeqId.Zero, true);
                        if (await native.DecodeAsync(batch, cancellationToken).ConfigureAwait(false) != DecodeResult.Ok) throw new InvalidDataException("Native generation failed.");
                    }
                    cancellationToken.ThrowIfCancellationRequested();
                    if (_captureEvaluationDiagnostics)
                        LastEvaluationDiagnostics = JsonSerializer.SerializeToElement(new { prompt = LastEvaluationDiagnostics,
                            raw_generated_output = output.ToString(), ended, diagnostic_only = true, student_ui_exposed = false });
                    using var parsed = JsonDocument.Parse(output.ToString());
                    var root = parsed.RootElement;
                    var text = root.GetProperty("answer").GetString() ?? "";
                    var status = root.GetProperty("status").GetString() ?? "insufficient_evidence";
                    var selectedIds = root.GetProperty("source_ids").EnumerateArray().Select(v => v.GetString()).ToHashSet();
                    var selectedSources = sources.Where(s => selectedIds.Contains(s.Id)).ToArray();
                    if (string.IsNullOrWhiteSpace(text) || selectedSources.Length == 0 && status == "answer") throw new InvalidDataException("Tutor answer is missing supported source identifiers.");
                    if (calculationContext is not null)
                    {
                        var calculated = JsonSerializer.SerializeToElement(calculationContext); var expected = calculated.GetProperty("result").GetDouble();
                        var unsupportedMeasurement = ResearchTutorService.HasUnsupportedSyntheticGradientClaim(text, calculated);
                        var contradictoryScaling = ResearchTutorService.HasContradictorySyntheticGradientScaling(text, calculated);
                        if (unsupportedMeasurement || contradictoryScaling)
                        {
                            ModelStatus = unsupportedMeasurement ? "synthetic_provenance_rejected" : "synthetic_scaling_rejected";
                            var reason = unsupportedMeasurement ? "Synthetic gradient-scaling context does not support a performed gradient measurement or calibration." : "The answer attributes quadratic scaling to the gradient itself rather than to b.";
                            if (_captureEvaluationDiagnostics) LastEvaluationDiagnostics = JsonSerializer.SerializeToElement(new { generation=LastEvaluationDiagnostics, rejection_reason=reason, diagnostic_only=true, student_ui_exposed=false });
                            var doc = Documentary(language, evidence, sources, timer.Elapsed.TotalSeconds, ModelStatus);
                            var lead = unsupportedMeasurement
                                ? language == "es" ? "Se rechazó la respuesta generada porque introducía una medición o calibración no aportada en el ejemplo sintético. Se muestra únicamente la guía revisada:\n\n" : "The generated answer was rejected because it introduced a measurement or calibration not supplied in the synthetic example. Only reviewed guidance is shown:\n\n"
                                : language == "es" ? "Se rechazó la respuesta generada porque atribuía al gradiente la dependencia cuadrática que corresponde a b. Se muestra únicamente la guía revisada:\n\n" : "The generated answer was rejected because it attributed the quadratic dependence of b to the gradient itself. Only reviewed guidance is shown:\n\n";
                            return doc with { Text = lead + string.Join("\n\n", evidence.Select(e => e.Title + "\n" + e.Body)) };
                        }
                        var mentioned = Regex.Matches(text, @"(?<![A-Za-z])[0-9]+(?:[.,][0-9]+)?").Select(v => double.TryParse(v.Value.Replace(',', '.'), NumberStyles.Float, CultureInfo.InvariantCulture, out var n) ? n : double.NaN);
                        var pulseContradiction = calculated.GetProperty("calculation").GetString() == "P90 = P180 / 2" && Regex.IsMatch(text, @"(?:p90|90\s*(?:°|degrees?|grados?)).{0,50}(?:double|twice|doble|dos\s+veces).{0,50}(?:p180|180)", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);
                        var consistentTypedResult = !_manifest.ResearchQualityPassed || ResearchTutorService.HasConsistentLabeledResult(text, calculated);
                        if (pulseContradiction || !consistentTypedResult || !mentioned.Any(n => Math.Abs(n - expected) < Math.Max(1e-9, Math.Abs(expected) * 1e-8)))
                        {
                            ModelStatus = "numeric_guard_rejected";
                            var explanation = (language == "es" ? "Ejemplo calculado de forma determinista: " : "Deterministic worked example: ") + calculated.GetProperty("calculation").GetString() + " → " + expected.ToString("G8", CultureInfo.InvariantCulture) + " " + calculated.GetProperty("unit").GetString() + (language == "es" ? ". Resultado sintético bajo los supuestos indicados; no es una calibración realizada.\n\n" : ". Synthetic result under the stated assumptions; no calibration has been performed.\n\n");
                            var doc = Documentary(language, evidence, sources, timer.Elapsed.TotalSeconds, ModelStatus);
                            return doc with { Text = explanation + doc.Text };
                        }
                    }
                    ModelStatus = ended ? "ready" : "bounded_answer";
                    var quote = evidence[0].ReviewedQuote ?? CourseQuote(language, evidence[0].Id);
                    var quoteSources = evidence[0].Sources;
                    var combinedSources = quoteSources.Concat(selectedSources).DistinctBy(s => s.Id).ToArray();
                    var quoteHeading = evidence[0].IsSupplemental
                        ? language == "es" ? "Texto del recorrido matemático · fuente revisada\n\n" : "Mathematical pathway text · reviewed source\n\n"
                        : language == "es" ? "Texto revisado del curso\n\n" : "Reviewed course text\n\n";
                    var combinedText = quoteHeading + quote + (language == "es" ? "\n\nExplicación generada por Beatrix\n\n" : "\n\nExplanation generated by Beatrix\n\n") + text;
                    var engineLabel = evidence[0].IsSupplemental
                        ? language == "es" ? "Beatrix · LLM local + artículos revisados · CPU · sin nuevo ajuste" : "Beatrix · local LLM + reviewed papers · CPU · no retraining"
                        : language == "es" ? "Beatrix · LLM local + texto del curso · CPU" : "Beatrix · local LLM + course text · CPU";
                    return new TutorAnswer(combinedText, engineLabel, combinedSources, true, ended ? status : "bounded_answer", _manifest.Sha256, Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(prompt))).ToLowerInvariant(), timer.Elapsed.TotalSeconds, true, quote, text, quoteSources, selectedSources, evidence[0].IsSupplemental, evidence[0].IsSupplemental ? _supplemental!.Sha256 : null);
                }, cancellationToken).ConfigureAwait(false);
            }
            catch (OperationCanceledException) { ModelStatus = "cancelled"; throw; }
            catch (Exception ex) when (ex is IOException or InvalidDataException or JsonException or ArgumentException or InvalidOperationException or DllNotFoundException or EntryPointNotFoundException or TypeInitializationException or BadImageFormatException || ex.GetType().Namespace?.StartsWith("LLama", StringComparison.Ordinal) == true)
            {
                ModelStatus = "model_unavailable_or_unapproved";
                Trace.WriteLine(ex.Message, "DiffAtOnce.Academy.Tutor");
                return Documentary(language, evidence, sources, timer.Elapsed.TotalSeconds, ModelStatus);
            }
        }
        finally { _gate.Release(); }
    }

    private void EnsureCourse()
    {
        if (_course is not null) return;
        var bytes = File.ReadAllBytes(_knowledgePath);
        _courseHash = Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
        _course = JsonDocument.Parse(bytes);
        if (!_course.RootElement.TryGetProperty("modules", out var modules) || modules.ValueKind != JsonValueKind.Array) throw new InvalidDataException("Course modules are missing.");
    }
    private bool EnsureSupplemental()
    {
        if (_supplemental is not null) return true;
        try
        {
            var manifestPath = Path.Combine(_modelDirectory, "manifest.json");
            if (!File.Exists(manifestPath)) { SupplementalStatus = "supplemental_manifest_missing"; return false; }
            var manifest = JsonSerializer.Deserialize<TutorManifest>(File.ReadAllText(manifestPath), JsonOptions) ?? throw new InvalidDataException("Supplemental manifest is missing.");
            // A neighboring file is never accepted merely because it exists.
            // The approved release explicitly binds its independent hash and
            // states that existing LoRA training did not include these papers.
            if (manifest.SupplementalContentFile != "derivations.json" || manifest.SupplementalIncludedInTraining != false || manifest.SupplementalContentSha256 is not { Length: 64 } ||
                manifest.SupplementalAnswerMode != "reviewed-documentary-guide" || manifest.SupplementalLLMApproved != false)
            { SupplementalStatus = "supplemental_not_approved"; return false; }
            _supplemental = SupplementalKnowledge.Load(_derivationsPath, manifest.SupplementalContentSha256);
            SupplementalStatus = "reviewed_retrieval_not_training"; return true;
        }
        catch (Exception ex) when (ex is IOException or InvalidDataException or JsonException or ArgumentException or InvalidOperationException)
        { SupplementalStatus = "supplemental_unavailable_or_hash_mismatch"; Trace.WriteLine(ex.Message, "DiffAtOnce.Academy.Tutor"); return false; }
    }
    private async Task EnsureModelAsync(CancellationToken ct)
    {
        if (_weights is not null) return;
        _manifest = JsonSerializer.Deserialize<TutorManifest>(await File.ReadAllTextAsync(Path.Combine(_modelDirectory, "manifest.json"), ct), JsonOptions) ?? throw new InvalidDataException("Model manifest is missing.");
        if (!ResearchNativeReady(_manifest, _allowPendingResearchNativeEvaluation)) throw new InvalidDataException("Mixed research model has not passed its quantized native evaluation.");
        if (string.IsNullOrWhiteSpace(_manifest.File) || Path.GetFileName(_manifest.File) != _manifest.File || !_manifest.File.EndsWith(".gguf", StringComparison.OrdinalIgnoreCase) || _manifest.Sha256 is not { Length: 64 } || !_manifest.FineTuned || !_manifest.QualityPassed || _manifest.CourseSha256 != _courseHash || _manifest.ExperimentalValidation) throw new InvalidDataException("Tutor model is incompatible or has not passed the educational quality gate.");
        var model = Path.Combine(_modelDirectory, _manifest.File);
        await using (var file = File.OpenRead(model)) if (!Convert.ToHexString(await SHA256.HashDataAsync(file, ct)).Equals(_manifest.Sha256, StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException("GGUF SHA-256 mismatch.");
        foreach (var report in new[] { ("training_report.json", _manifest.TrainingReportSha256), ("evaluation_report.json", _manifest.EvaluationReportSha256) })
        {
            await using var file = File.OpenRead(Path.Combine(_modelDirectory, report.Item1));
            if (!Convert.ToHexString(await SHA256.HashDataAsync(file, ct)).Equals(report.Item2, StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException("Tutor provenance report mismatch.");
        }
        _weights = await LLamaWeights.LoadFromFileAsync(Parameters(model), ct).ConfigureAwait(false);
    }
    private static bool ResearchNativeReady(TutorManifest manifest, bool allowPending) => !manifest.ResearchQualityPassed || allowPending ||
        manifest.NativeEvaluationPassed && manifest.NativeResearchEvaluationPassed && !manifest.NativeEvaluationPending;
    private static ModelParams Parameters(string path) => new(path) { ContextSize = 4096, GpuLayerCount = 0, UseMemorymap = true, Threads = Math.Clamp(Environment.ProcessorCount / 2, 1, 4), BatchThreads = Math.Clamp(Environment.ProcessorCount / 2, 1, 4), BatchSize = 128, UBatchSize = 64 };
    public static string ChatPrompt(string system, string user) => $"<|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n";
    private static string TrainingCompatibleJson(object payload)
    {
        // Python training uses ensure_ascii=True: lowercase Unicode escapes,
        // with ASCII punctuation (+, <, >, apostrophe) left literal. This JSON
        // goes only to the local model, never an HTML interpreter.
        var unicode = JsonSerializer.Serialize(payload, new JsonSerializerOptions { Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping });
        var ascii = new StringBuilder();
        foreach (var c in unicode) { if (c > 127) ascii.Append("\\u").Append(((int)c).ToString("x4", CultureInfo.InvariantCulture)); else ascii.Append(c); }
        // Untrusted JSON data must not inject ChatML role delimiters.
        // Prompts without these markers retain the legacy byte sequence.
        return ascii.ToString().Replace("<|", "\\u003c|", StringComparison.Ordinal);
    }
    private static string CanonicalCalculationQuestion(string language, object calculationContext)
    {
        // Intent normalization for the two explicit textbook examples. Inputs,
        // result and assumptions still come solely from the deterministic trace;
        // this does not infer a measurement or rewrite the user's displayed text.
        var trace = JsonSerializer.SerializeToElement(calculationContext);
        if (trace.GetProperty("calculation").GetString() == "P90 = P180 / 2")
        {
            var value = trace.GetProperty("inputs").GetProperty("p180_us").GetDouble().ToString("G8", CultureInfo.InvariantCulture);
            return language == "es" ? $"En una simulación, el mínimo de 180° está en P1={value} µs a potencia fija. ¿Cuál es P90 y qué compruebo?" : $"In a simulation, the 180° minimum is at P1={value} µs at fixed power. What is P90 and what should I check?";
        }
        var ratio = trace.GetProperty("inputs").GetProperty("gradient_scale").GetDouble().ToString("G8", CultureInfo.InvariantCulture);
        return language == "es" ? $"Ejemplo sintético: g se multiplica por {ratio}. δ y Δ no cambian. ¿Por qué factor cambia b?" : $"Synthetic example: g is multiplied by {ratio}. δ and Δ do not change. By what factor does b change?";
    }
    /// <summary>Scoped documentary routing for combined temperature-scaling
    /// and flow questions. Ordinary lesson questions retain their model path.</summary>
    public static bool IsTemperatureFlowBoundaryQuestion(string moduleId, string question)
    {
        if (moduleId != "temperature-standard") return false;
        var text = Regex.Replace(question.Normalize(NormalizationForm.FormD), @"\p{Mn}", "").ToLowerInvariant();
        return Regex.IsMatch(text, @"\b(?:flow|flujo|convection|conveccion)\b", RegexOptions.CultureInvariant)
            && Regex.IsMatch(text, @"\b(?:fttms|ft|temperature|temperatura|scal\w*|escala|correc\w*)\b|293\s*/", RegexOptions.CultureInvariant);
    }
    private sealed record Evidence(string Id, string Title, string Body, IReadOnlyList<TutorSource> Sources, string? ReviewedQuote = null, bool IsSupplemental = false, string? SupplementalSha256 = null);
    private object? TeachingFocus(string language, string moduleId)
    {
        if (moduleId.StartsWith("derivation:", StringComparison.Ordinal))
        {
            return _supplemental is null ? null : new { module_id = moduleId, retrieval_only_not_training = true, supplemental_sha256 = _supplemental.Sha256, limitation = "Only supplied steps, equations and assumptions support the explanation; no experimental data or new LoRA training." };
        }
        var module = _course!.RootElement.GetProperty("modules").EnumerateArray().FirstOrDefault(m => Id(m) == moduleId);
        if (module.ValueKind != JsonValueKind.Object) return null;
        // These are literal reviewed course fields, not an LLM-generated key
        // or a fabricated answer. They remain linked to their source module.
        return new { module_id = moduleId, causal_anchor = Local(module, "why", language), mechanism_anchor = Local(module, "mechanism", language), source_ids = Sources(module).Select(s => s.Id) };
    }
    private string CourseQuote(string language, string moduleId)
    {
        var module = _course!.RootElement.GetProperty("modules").EnumerateArray().First(m => Id(m) == moduleId);
        // Literal course text remains separate from generated prose. It is
        // present for every lesson, not inserted to make selected tests pass.
        return Local(module, "why", language) + "\n\n" + Local(module, "mechanism", language);
    }
    private List<Evidence> Retrieve(string language, string question, string moduleId)
    {
        if (moduleId.StartsWith("derivation:", StringComparison.Ordinal))
        {
            if (!EnsureSupplemental()) return new List<Evidence>();
            try
            {
                var selected = _supplemental!.Retrieve(moduleId[11..], language, question);
                if (selected is null) { SupplementalStatus = "supplemental_chapter_unknown"; return new List<Evidence>(); }
                return new List<Evidence> { new(selected.Id, selected.Title, selected.Body, selected.Sources, selected.Quote, true, _supplemental.Sha256) };
            }
            catch (Exception ex) when (ex is InvalidDataException or InvalidOperationException or JsonException or KeyNotFoundException)
            { SupplementalStatus = "supplemental_invalid_references"; Trace.WriteLine(ex.Message, "DiffAtOnce.Academy.Tutor"); return new List<Evidence>(); }
        }
        var active = _course!.RootElement.GetProperty("modules").EnumerateArray().FirstOrDefault(m => Id(m) == moduleId);
        // Scoped lesson questions use exactly one complete module, matching
        // training. A second unrelated document can displace the causal answer
        // and attach another module's references to a valid-looking response.
        if (active.ValueKind == JsonValueKind.Object)
            return new List<Evidence> { new(Id(active), Local(active, "title", language), ModuleText(active, language), Sources(active)) };
        var terms = Tokens(question).ToHashSet();
        return _course!.RootElement.GetProperty("modules").EnumerateArray().Select(m =>
        {
            var body = ModuleText(m, language); var title = Local(m, "title", language);
            var score = Tokens(title + " " + body).Distinct().Count(terms.Contains);
            return (Score: score, Data: new Evidence(Id(m), title, body, Sources(m)));
        }).Where(v => v.Score > 0).OrderByDescending(v => v.Score).Take(2).Select(v => v.Data).ToList();
    }
    private static string ModuleText(JsonElement m, string language)
    {
        var parts = new List<string>();
        foreach (var name in new[] { "objective", "why", "purpose", "mechanism" }) { var v = Local(m, name, language); if (v.Length > 0) parts.Add(v); }
        if (m.TryGetProperty("steps", out var steps)) parts.AddRange(steps.EnumerateArray().Select(s => Local(s, "title", language) + ": " + Local(s, "body", language)));
        if (m.TryGetProperty("pitfalls", out var pitfalls)) parts.AddRange(pitfalls.EnumerateArray().Select(p => Local(p, language)));
        var takeaway = Local(m, "takeaway", language); if (takeaway.Length > 0) parts.Add(takeaway);
        if (m.TryGetProperty("questions", out var questions)) foreach (var q in questions.EnumerateArray())
        {
            var options = q.GetProperty("options").EnumerateArray().ToArray(); var correct = q.GetProperty("correctIndex").GetInt32();
            if (correct >= 0 && correct < options.Length) parts.Add((language == "es" ? "Pregunta revisada: " : "Reviewed question: ") + Local(q, "question", language) + "\n" + (language == "es" ? "Respuesta revisada: " : "Reviewed answer: ") + Local(options[correct], language) + ". " + Local(q, "explanation", language));
        }
        return string.Join("\n", parts);
    }
    /// <summary>Two explicit textbook worked examples. No measured spectrum or
    /// instrument calibration is inferred. If parsing is uncertain, no result
    /// is supplied; the LLM must stay with the source's general explanation.</summary>
    public static object? CalculationContext(string moduleId, string question)
    {
        if (moduleId == "pulse-calibration" && question.Contains("180", StringComparison.Ordinal))
        {
            var m = Regex.Match(question, @"(?:P1\s*=\s*|at\s+|a\s+|en\s+)([0-9]+(?:[.,][0-9]+)?)\s*(?:µs|μs|us|microseconds|microsegundos)", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);
            if (m.Success && double.TryParse(m.Groups[1].Value.Replace(',', '.'), NumberStyles.Float, CultureInfo.InvariantCulture, out var p180) && double.IsFinite(p180) && p180 > 0)
                return new { kind = "synthetic_worked_example", calculation = "P90 = P180 / 2", inputs = new { p180_us = p180 }, result = p180 / 2, unit = "µs", assumptions = new[] { "Identified 180 degree null", "Unchanged RF power" }, experimental_calibration = false };
        }
        if (moduleId is "sequence-b" or "gradient-calibration")
        {
            const string gradientName = @"(?:g|gradients?|gradientes?)";
            double? ratio = Regex.IsMatch(question, @"\b(?:double|doubling|doblo|doblar|duplico|duplicar|duplicamos)\s+(?:(?:the|el|los)\s+)?" + gradientName + @"\b|\b" + gradientName + @"\s+(?:is\s+)?doubled\b", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant) ? 2 : null;
            var m = Regex.Match(question, @"\b" + gradientName + @"\s+(?:is\s+|se\s+)?multipl(?:ied|ica)\s+(?:by|por)\s+([0-9]+(?:[.,][0-9]+)?)", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);
            if (m.Success && double.TryParse(m.Groups[1].Value.Replace(',', '.'), NumberStyles.Float, CultureInfo.InvariantCulture, out var parsed) && double.IsFinite(parsed) && parsed > 0) ratio = parsed;
            var namesGradient = Regex.IsMatch(question, @"\bg\b|\bgradients?\b|\bgradientes?\b", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);
            var fixedTiming = Regex.IsMatch(question, @"unchanged|do\s+not\s+change|remain\s+fixed|no\s+cambian|sin\s+cambiar|manteniendo|keep.+(?:delta|δ|Δ)", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);
            if (ratio.HasValue && double.IsFinite(ratio.Value * ratio.Value) && namesGradient && fixedTiming)
                return new { kind = "synthetic_worked_example", calculation = "b_scale = gradient_scale^2", inputs = new { gradient_scale = ratio.Value }, result = ratio.Value * ratio.Value, unit = "factor", assumptions = new[] { "Ideal rectangular PGSE", "delta and Delta unchanged" }, experimental_calibration = false };
        }
        return null;
    }
    private static IReadOnlyList<TutorSource> Sources(JsonElement m) => !m.TryGetProperty("sources", out var sources) ? Array.Empty<TutorSource>() : sources.EnumerateArray().Select(s => new TutorSource(Id(s), s.TryGetProperty("title", out var title) ? title.ValueKind == JsonValueKind.String ? title.GetString() ?? "" : title.ToString() : Id(s), Str(s, "url"), Str(s, "localPath"), s.TryGetProperty("slide", out var slide) && slide.ValueKind == JsonValueKind.Number && slide.TryGetInt32(out var i) ? i : null)).ToArray();
    private static string? Str(JsonElement e, string key) => e.TryGetProperty(key, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : null;
    private static string Id(JsonElement m) => Str(m, "id") ?? "";
    private static string Local(JsonElement m, string key, string language) => m.TryGetProperty(key, out var v) ? Local(v, language) : "";
    private static string Local(JsonElement v, string language) => v.ValueKind == JsonValueKind.String ? v.GetString() ?? "" : v.ValueKind == JsonValueKind.Object && v.TryGetProperty(language, out var x) ? x.GetString() ?? "" : "";
    private static IEnumerable<string> Tokens(string value) { var s = string.Concat(value.Normalize(NormalizationForm.FormD).Where(c => CharUnicodeInfo.GetUnicodeCategory(c) != UnicodeCategory.NonSpacingMark)).ToLowerInvariant(); return Regex.Matches(s, "[a-z0-9]{3,}").Select(m => m.Value); }
    private static TutorAnswer Documentary(string language, List<Evidence> evidence, TutorSource[] sources, double seconds, string status)
    {
        var first = evidence[0];
        var lead = language == "es" ? "Guía documental del curso. El modelo local no se ha utilizado en esta respuesta.\n\n" : "Course documentary guide. The local model was not used for this answer.\n\n";
        return new TutorAnswer(lead + first.Title + "\n\n" + first.Body, language == "es" ? "Guía documental · sin LLM" : "Documentary guide · no LLM", first.Sources, false, status, null, null, seconds,
            IncludesSupplementalEvidence: first.IsSupplemental, SupplementalSha256: first.SupplementalSha256);
    }
    private static TutorAnswer EmptyAnswer(string language, double seconds, string status = "insufficient_evidence") => new(language == "es" ? "No encuentro evidencia suficiente y aprobada para esta consulta. Selecciona un módulo o comprueba el suplemento, sus referencias y su manifiesto; describe el experimento y los parámetros que faltan." : "Approved evidence is insufficient for this request. Select a module or check the supplement, references and manifest; describe the experiment and missing parameters.", language == "es" ? "Guía documental · evidencia insuficiente" : "Documentary guide · insufficient evidence", Array.Empty<TutorSource>(), false, status, null, null, seconds);
    private static string OutputGrammar(TutorSource[] sources)
    {
        var ids = sources.Select(s => s.Id).Distinct().Select(s => JsonSerializer.Serialize(JsonSerializer.Serialize(s))).ToArray();
        return "root ::= \"{\" ws \"\\\"answer\\\"\" ws \":\" ws string ws \",\" ws \"\\\"source_ids\\\"\" ws \":\" ws sources ws \",\" ws \"\\\"status\\\"\" ws \":\" ws status ws \"}\"\n" +
            "sources ::= \"[\" ws (id (ws \",\" ws id)*)? ws \"]\"\n" + "id ::= " + (ids.Length > 0 ? string.Join(" | ", ids) : "\"\\\"unavailable\\\"\"") + "\nstatus ::= \"\\\"answer\\\"\" | \"\\\"insufficient_evidence\\\"\"\n" +
            "string ::= \"\\\"\" char* \"\\\"\"\nchar ::= [^\"\\\\\\x7F\\x00-\\x1F] | \"\\\\\" ([\"\\\\/bfnrt] | \"u\" [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F])\nws ::= [ \\t\\n\\r]*\n";
    }
    public async ValueTask DisposeAsync()
    {
        await _gate.WaitAsync().ConfigureAwait(false);
        try { if (_disposed) return; _disposed = true; _weights?.Dispose(); _course?.Dispose(); _supplemental?.Dispose(); _weights = null; _course = null; _supplemental = null; }
        finally { _gate.Release(); }
    }
    private sealed record TutorManifest(string Id, string File, string Sha256, string CourseSha256, bool FineTuned, bool QualityPassed, bool ExperimentalValidation, string TrainingReportSha256, string EvaluationReportSha256,
        string? SupplementalContentFile = null, string? SupplementalContentSha256 = null, bool? SupplementalIncludedInTraining = null,
        string? SupplementalAnswerMode = null, bool? SupplementalLLMApproved = null, bool ResearchQualityPassed = false,
        bool NativeEvaluationPending = false, bool NativeEvaluationPassed = false, bool NativeResearchEvaluationPassed = false);
}
