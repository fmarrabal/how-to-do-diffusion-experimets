using System.Security.Cryptography;
using System.Text.Json;

namespace DiffAtOnce.Academy.Core;

/// <summary>The separately versioned, reviewed mathematical supplement. It does not
/// replace the course used to train the original local tutor.</summary>
public sealed class DerivationCatalogue
{
    public string Sha256 { get; }
    public string Version { get; }
    public JsonElement Document { get; }
    public IReadOnlyList<DerivationChapter> Chapters { get; }
    public int EquationCoverageCount { get; }

    public DerivationCatalogue(string path)
    {
        var bytes = File.ReadAllBytes(path);
        Sha256 = Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
        using var parsed = JsonDocument.Parse(bytes, new JsonDocumentOptions { MaxDepth = 64 });
        Document = parsed.RootElement.Clone();
        Version = Document.GetProperty("version").GetString() ?? throw new InvalidDataException("Supplement version missing.");
        var chapters = new List<DerivationChapter>();
        foreach (var entry in Document.GetProperty("chapters").EnumerateArray())
        {
            var id = entry.GetProperty("id").GetString() ?? "";
            if (id.Length is < 1 or > 100 || id.Any(c => !(char.IsAsciiLetterOrDigit(c) || c == '-')))
                throw new InvalidDataException("Unsafe derivation identifier.");
            var title = entry.GetProperty("title");
            var es = title.GetProperty("es").GetString() ?? "";
            var en = title.GetProperty("en").GetString() ?? "";
            if (string.IsNullOrWhiteSpace(es) || string.IsNullOrWhiteSpace(en) || entry.GetProperty("steps").GetArrayLength() == 0)
                throw new InvalidDataException("Incomplete bilingual mathematical chapter: " + id);
            chapters.Add(new(id, new(es, en), entry.Clone()));
        }
        if (chapters.Count == 0 || chapters.Select(c => c.Id).Distinct().Count() != chapters.Count)
            throw new InvalidDataException("Mathematical chapters must be unique and nonempty.");
        Chapters = chapters;
        EquationCoverageCount = Document.GetProperty("equationCoverage").GetArrayLength();
    }
    public DerivationChapter? Find(string id) => Chapters.FirstOrDefault(c => c.Id == id);
}

public sealed record DerivationChapter(string Id, LocalizedText Title, JsonElement Document);
