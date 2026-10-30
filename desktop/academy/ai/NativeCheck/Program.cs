using System.Text.Json;
using System.Diagnostics;
using DiffAtOnce.Academy.Tutor;

if (args.Length < 3) throw new ArgumentException("Usage: NativeCheck COURSE_JSON MODEL_DIRECTORY OUTPUT_JSON [smoke|native] [SPEN_CONTEXT_JSON]");
var course = Path.GetFullPath(args[0]); var model = Path.GetFullPath(args[1]); var report = Path.GetFullPath(args[2]);
if (File.Exists(report)) throw new IOException("Refuse to overwrite a completed native report.");
var mode = args.Length > 3 ? args[3] : "smoke";
var checks = new List<object>(); var passed = true;
await using var tutor = new TutorService(course, model);
void Add(string id, bool success, object? detail = null) { checks.Add(new { id, passed = success, detail }); passed &= success; Console.WriteLine($"{id}: {(success ? "PASS" : "FAIL")}"); }
var sources = tutor.GetModuleSources("sequence-b"); Add("module_sources_present", sources.Count > 0, sources.Count);
var pulseTrace = JsonSerializer.SerializeToElement(TutorService.CalculationContext("pulse-calibration", "Synthetic 180 degree minimum at 18 µs, same power."));
Add("pulse_worked_example_not_llm_math", pulseTrace.GetProperty("result").GetDouble() == 9 && !pulseTrace.GetProperty("experimental_calibration").GetBoolean(), pulseTrace);
var gradientTrace = JsonSerializer.SerializeToElement(TutorService.CalculationContext("sequence-b", "Synthetic g is multiplied by 0.8, delta and Delta unchanged."));
Add("gradient_square_worked_example", Math.Abs(gradientTrace.GetProperty("result").GetDouble() - .64) < 1e-12, gradientTrace);
Add("doubling_delta_is_not_gradient_scaling", TutorService.CalculationContext("sequence-b", "I double delta and keep everything else unchanged.") is null);
Add("named_gradient_does_not_change_doubled_parameter", TutorService.CalculationContext("sequence-b", "I double delta and keep g unchanged.") is null);
var englishTrace = JsonSerializer.SerializeToElement(TutorService.CalculationContext("sequence-b", "Synthetic example: g is multiplied by 1.2. δ and Δ do not change."));
Add("explicit_fixed_timing_english", Math.Abs(englishTrace.GetProperty("result").GetDouble() - 1.44) < 1e-12, englishTrace);
Add("missing_fixed_timing_no_numeric_invention", TutorService.CalculationContext("sequence-b", "I double g, and also change delta.") is null);
using (var cancelled = new CancellationTokenSource())
{
    cancelled.Cancel();
    try { await tutor.AskAsync("en", "Explain the gradient.", "sequence-b", null, cancelled.Token); Add("pre_cancelled_request", false); }
    catch (OperationCanceledException) { Add("pre_cancelled_request", true); }
}
try { await tutor.AskAsync("es", "Question", "sequence-b", "not-json", CancellationToken.None); Add("invalid_context_rejected", false); }
catch (JsonException) { Add("invalid_context_rejected", true); }
if (mode == "native")
{
    var questions = new[] {
        (Language:"es",Module:"pulse-calibration",Question:"En un ejemplo sintético el mínimo de 180° aparece a 18 µs. ¿Cuánto vale el pulso de 90° y qué debería comprobar?",Expected:"9"),
        (Language:"en",Module:"sequence-b",Question:"In an ideal rectangular PGSE example, if I double g and keep delta and Delta unchanged, what happens to b?",Expected:"4"),
        (Language:"es",Module:"spen",Question:"¿Qué hay que hacer con las dos polaridades EPSI para reconstruir la frecuencia y la difusión?",Expected:""),
        (Language:"en",Module:"time-resolved",Question:"Why does changing fractions during a sequential ramp bias D even when each species has a constant diffusion coefficient?",Expected:"")
    };
    foreach (var q in questions)
    {
        using var timeout = new CancellationTokenSource(TimeSpan.FromMinutes(4));
        var answer = await tutor.AskAsync(q.Language, q.Question, q.Module, null, timeout.Token, new Progress<string>(Console.WriteLine));
        var success = answer.IsModelAnswer && answer.Sources.Count > 0 && answer.Text.Length > 25 && (q.Expected.Length == 0 || answer.Text.Contains(q.Expected, StringComparison.Ordinal));
        // Additional runtime-regression criteria were added after the first
        // native probe exposed shallow explanations. They are separate from
        // the frozen, one-time HF held-out test and never relabel its outputs.
        var words = answer.Text.ToLowerInvariant();
        success &= answer.IncludesCourseQuote && !string.IsNullOrWhiteSpace(answer.CourseQuote) && !string.IsNullOrWhiteSpace(answer.GeneratedText) && answer.Text.Contains(answer.CourseQuote, StringComparison.Ordinal) && answer.Text.Contains(answer.GeneratedText, StringComparison.Ordinal);
        if (q.Module == "spen") success &= (words.Contains("reorden") || words.Contains("índice") || words.Contains("indice")) && words.Contains("fase") && (words.Contains("dft") || words.Contains("fourier"));
        if (q.Module == "time-resolved") success &= (words.Contains("fraction") || words.Contains("concentration") || words.Contains("population")) && (words.Contains("attenuation") || words.Contains("signal"));
        Add("native_" + q.Language + "_" + q.Module, success, answer);
    }
    if (args.Length > 4)
    {
        var capturedPath = Path.GetFullPath(args[4]);
        var capturedText = await File.ReadAllTextAsync(capturedPath);
        using var captured = JsonDocument.Parse(capturedText);
        var context = JsonSerializer.Serialize(new { evidenceStatus = "synthetic-teaching-simulation", moduleId = "spen", simulation = captured.RootElement });
        using var timeout = new CancellationTokenSource(TimeSpan.FromMinutes(4));
        var answer = await tutor.AskAsync("en", "The selected A resonance is absent (fraction A=0), but the synthetic corrected fit gives D=1.4. Can I report this as A's diffusion coefficient? Explain the spectral-leakage issue using the captured context.", "spen", context, timeout.Token, new Progress<string>(Console.WriteLine));
        var text = answer.Text.ToLowerInvariant();
        Add("native_spen_real_webview_context", answer.IsModelAnswer && answer.Sources.Count > 0 && (text.Contains("leak") || text.Contains("absent")) && (text.Contains("not") || text.Contains("no ")),
            new { answer, context_path = capturedPath, context_sha256 = Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(System.Text.Encoding.UTF8.GetBytes(capturedText))).ToLowerInvariant(), context_characters = context.Length });
    }
    // The weights are loaded here. Cancel only after prefill has completed,
    // so this exercises real native generation rather than a cancelled queue.
    using var generationCancel = new CancellationTokenSource(TimeSpan.FromMinutes(4));
    var cancellationTriggered = false; var cancellationLatency = Stopwatch.StartNew();
    var cancellationProgress = new InlineProgress(message =>
    {
        if (message.Contains("preparing a sourced", StringComparison.Ordinal))
        {
            cancellationTriggered = true; cancellationLatency.Restart(); generationCancel.CancelAfter(100);
        }
    });
    try
    {
        await tutor.AskAsync("en", "Explain the practical limits of the selected diffusion sequence.", "sequence-b", null, generationCancel.Token, cancellationProgress);
        Add("native_generation_cancellable", false, new { cancellationTriggered });
    }
    catch (OperationCanceledException)
    {
        Add("native_generation_cancellable", cancellationTriggered && cancellationLatency.Elapsed.TotalSeconds < 10,
            new { cancellationTriggered, elapsed_seconds = cancellationLatency.Elapsed.TotalSeconds });
    }
}
else
{
    var answer = await tutor.AskAsync("es", "Explica cómo se calcula b.", "sequence-b", null, CancellationToken.None);
    Add("documentary_fallback_honest", !answer.IsModelAnswer && answer.Sources.Count > 0 && answer.EngineLabel.Contains("documental"), answer);
}
Directory.CreateDirectory(Path.GetDirectoryName(report)!);
await File.WriteAllTextAsync(report, JsonSerializer.Serialize(new { passed, mode, checks, experimental_validation = false, scope = "Actual C# hybrid tutor runtime regression. Native mode executes the quantized GGUF CPU model. The final answer visibly separates literal reviewed course why/mechanism and GeneratedText; combined causal coverage is not claimed as free LLM generation. Earlier open SPEN/TR generated-only omissions and failed probes remain preserved. Smoke mode verifies documentary/cancellation/input boundaries only. These checks do not replace or relabel the one-time frozen HF evaluation." }, new JsonSerializerOptions { WriteIndented = true }));
return passed ? 0 : 1;

sealed class InlineProgress(Action<string> action) : IProgress<string>
{
    public void Report(string value) => action(value);
}
