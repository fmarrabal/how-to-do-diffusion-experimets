using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace DiffAtOnce.Academy.Tutor;

/// <summary>Reviewed paper derivations, loaded only against their independently
/// approved hash. This retrieval corpus is not part of the existing LoRA
/// training. It supplies literal equations, explanation, assumptions and page
/// references without evaluating equations or inferring experimental values.</summary>
internal sealed class SupplementalKnowledge : IDisposable
{
    private readonly JsonDocument _document;
    private readonly Dictionary<string, JsonElement> _sources;
    internal string Sha256 { get; }
    internal sealed record Excerpt(string Id, string Title, string Body, string Quote, IReadOnlyList<TutorSource> Sources);
    private SupplementalKnowledge(JsonDocument document, string sha256)
    {
        _document = document; Sha256 = sha256;
        if (!document.RootElement.TryGetProperty("chapters", out var chapters) || chapters.ValueKind != JsonValueKind.Array ||
            !document.RootElement.TryGetProperty("sources", out var sources) || sources.ValueKind != JsonValueKind.Array)
            throw new InvalidDataException("Supplemental chapters and sources are required.");
        _sources = sources.EnumerateArray().ToDictionary(s => Text(s, "id"), s => s, StringComparer.Ordinal);
        if (_sources.Count == 0 || _sources.ContainsKey("") || chapters.EnumerateArray().Any(c => Text(c, "id").Length == 0))
            throw new InvalidDataException("Supplemental source and chapter identifiers are required.");
        if (chapters.EnumerateArray().Select(c => Text(c, "id")).Distinct(StringComparer.Ordinal).Count() != chapters.GetArrayLength())
            throw new InvalidDataException("Supplemental chapter identifiers must be unique.");
        foreach (var source in _sources.Values)
            if (Text(source, "title").Length == 0 || Text(source, "doi").Length == 0 || !source.TryGetProperty("pages", out var pages) || !pages.TryGetInt32(out var count) || count < 1)
                throw new InvalidDataException("Each paper requires a title, DOI and positive PDF page count.");
    }
    internal static SupplementalKnowledge Load(string path, string expectedSha256)
    {
        if (expectedSha256.Length != 64 || !expectedSha256.All(Uri.IsHexDigit)) throw new InvalidDataException("Approved supplemental SHA-256 is required.");
        var file = new FileInfo(path);
        if (!file.Exists || file.Length is <= 0 or > 2_000_000) throw new InvalidDataException("Supplemental file is absent or exceeds its 2 MB teaching limit.");
        var bytes = File.ReadAllBytes(path);
        var hash = Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
        if (!hash.Equals(expectedSha256, StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException("Supplemental derivations SHA-256 mismatch.");
        var document = JsonDocument.Parse(bytes);
        try { return new SupplementalKnowledge(document, hash); }
        catch { document.Dispose(); throw; }
    }
    internal IReadOnlyList<TutorSource> Sources(string chapterId)
    {
        var chapter = Chapter(chapterId);
        return chapter.ValueKind == JsonValueKind.Object && chapter.TryGetProperty("steps", out var steps)
            ? References(steps.EnumerateArray()) : Array.Empty<TutorSource>();
    }
    internal Excerpt? Retrieve(string chapterId, string language, string question)
    {
        var chapter = Chapter(chapterId);
        if (chapter.ValueKind != JsonValueKind.Object || !chapter.TryGetProperty("steps", out var steps)) return null;
        // An explicitly selected chapter is an ordered proof, not independent
        // snippets. Retain every step and its notation/assumption boundaries.
        // TutorService applies the native token limit and documentary fallback
        // without silently dropping the derivative or integration that causally
        // connects a student's question to the final equation.
        var selected = steps.EnumerateArray().ToArray();
        if (selected.Length == 0) return null;
        var sources = References(selected);
        if (sources.Count == 0) throw new InvalidDataException("Selected paper derivation lacks supported page references.");
        var quoteParts = selected.Select(step => Local(step, "title", language) + "\n" + Text(step, "equationPlain") + "\n" +
            Local(step, "explanation", language) + "\n" + (language == "es" ? "Supuestos: " : "Assumptions: ") + Local(step, "assumptions", language) +
            (Local(step, "notationNote", language) is { Length: > 0 } note ? "\n" + (language == "es" ? "Nota sobre la impresión original: " : "Original printed notation note: ") + note : ""));
        var quote = string.Join("\n\n", quoteParts);
        var provenance = language == "es" ? "Suplemento revisado de artículos: consulta documental. Estos artículos no formaron parte del ajuste LoRA existente. Las ecuaciones no constituyen una calibración experimental." :
            "Reviewed paper supplement: document retrieval. These papers were not included in the existing LoRA fine-tuning. The equations do not constitute experimental calibration.";
        var citations = string.Join("\n", sources.Select(s => s.Id + ": " + s.Title + "; DOI " + s.Doi));
        return new Excerpt("derivation:" + chapterId, Local(chapter, "title", language), provenance + "\n" + Local(chapter, "objective", language) + "\n\n" + quote + "\n\n" + citations, quote, sources);
    }
    private JsonElement Chapter(string id) => _document.RootElement.GetProperty("chapters").EnumerateArray().FirstOrDefault(c => Text(c, "id") == id);
    private IReadOnlyList<TutorSource> References(IEnumerable<JsonElement> steps)
    {
        var selectedSteps = steps.ToArray();
        if (selectedSteps.Any(s => !s.TryGetProperty("sourceRefs", out var refsForStep) || refsForStep.ValueKind != JsonValueKind.Array || refsForStep.GetArrayLength() == 0))
            throw new InvalidDataException("Each quoted derivation step requires its own source references.");
        var refs = selectedSteps.SelectMany(s => s.GetProperty("sourceRefs").EnumerateArray()).ToArray();
        foreach (var reference in refs)
        {
            if (!_sources.TryGetValue(Text(reference, "sourceId"), out var source)) throw new InvalidDataException("Unrecognized supplemental source identifier.");
            if (!reference.TryGetProperty("pages", out var pagesForReference) || pagesForReference.ValueKind != JsonValueKind.Array || pagesForReference.GetArrayLength() == 0 ||
                pagesForReference.EnumerateArray().Any(p => !p.TryGetInt32(out var page) || page < 1 || page > source.GetProperty("pages").GetInt32()))
                throw new InvalidDataException("Every source reference requires its own valid PDF pages.");
        }
        return refs.GroupBy(r => Text(r, "sourceId"), StringComparer.Ordinal).Select(group => {
            if (!_sources.TryGetValue(group.Key, out var source)) throw new InvalidDataException("Unrecognized supplemental source identifier.");
            var pages = group.SelectMany(r => r.TryGetProperty("pages", out var p) ? p.EnumerateArray().Select(n => n.GetInt32()) : Array.Empty<int>()).Distinct().Order().ToArray();
            var count = source.GetProperty("pages").GetInt32();
            if (pages.Length == 0 || pages.Any(p => p < 1 || p > count)) throw new InvalidDataException("Supplemental page reference is missing or outside the source.");
            var equations = group.SelectMany(r => r.TryGetProperty("equations", out var e) ? e.EnumerateArray().Select(n => n.GetString() ?? "") : Array.Empty<string>()).Where(e => e.Length > 0).Distinct().ToArray();
            var title = Text(source, "title") + " — PDF pp. " + string.Join(", ", pages);
            if (equations.Length > 0) title += "; eqs. " + string.Join(", ", equations);
            return new TutorSource(group.Key, title, NullableText(source, "url"), null, null, NullableText(source, "doi"), pages, equations);
        }).ToArray();
    }
    private static string Text(JsonElement e, string key) => e.TryGetProperty(key, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() ?? "" : "";
    private static string? NullableText(JsonElement e, string key) => Text(e, key) is { Length: > 0 } text ? text : null;
    private static string Local(JsonElement e, string key, string language) => e.TryGetProperty(key, out var v) && v.ValueKind == JsonValueKind.Object && v.TryGetProperty(language, out var x) && x.ValueKind == JsonValueKind.String ? x.GetString() ?? "" : Text(e, key);
    private static IEnumerable<string> Tokens(string value)
    {
        var plain = string.Concat(value.Normalize(NormalizationForm.FormD).Where(c => CharUnicodeInfo.GetUnicodeCategory(c) != UnicodeCategory.NonSpacingMark)).ToLowerInvariant();
        var stop = new HashSet<string>(new[] { "the", "and", "why", "how", "para", "como", "por", "que", "una", "del", "los", "las", "con", "what", "does", "this", "from", "with", "explain", "explica" });
        return Regex.Matches(plain, "[a-z0-9]{3,}").Select(m => m.Value).Where(t => !stop.Contains(t));
    }
    public void Dispose() => _document.Dispose();
}
