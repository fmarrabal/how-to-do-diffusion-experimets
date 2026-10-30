using System.Security.Cryptography;
using System.Text.Json;

namespace DiffAtOnce.Academy.Core;

public sealed record LocalizedText(string Es = "", string En = "")
{
    public string In(string language) => language == "en" ? En : Es;
}
public sealed record LessonStep(LocalizedText Title, LocalizedText Body);
public sealed record LessonExample(string Id, LocalizedText Title, LocalizedText Instruction, string? Preset = null, Dictionary<string, double>? Params = null);
public sealed record LessonQuestion(string Id, LocalizedText Question, LocalizedText[] Options, int CorrectIndex, LocalizedText Explanation);
public sealed record LessonSource(string Id, string Title, string? Url = null, string? LocalPath = null, int? Slide = null);
public sealed record CourseModule(string Id, string Scene, int Order, LocalizedText Chapter, LocalizedText Title, LocalizedText Objective, LocalizedText Why, LocalizedText Purpose, LocalizedText Mechanism, LessonStep[] Steps, LessonExample[] Examples, LessonQuestion[] Questions, LocalizedText[] Pitfalls, LocalizedText Takeaway, LessonSource[] Sources);
public sealed record Course(string Version, LocalizedText Title, CourseModule[] Modules);
public sealed record Slide(int SlideNumber, string Title, string Text, string Notes, string Image, string[] ModuleIds);
public sealed class CourseRepository
{
    public static readonly JsonSerializerOptions Json = new() { PropertyNameCaseInsensitive = true, WriteIndented = true };
    public Course Course { get; }
    public string Sha256 { get; }
    public string ContentDirectory { get; }
    public CourseRepository(string contentDirectory)
    {
        ContentDirectory = Path.GetFullPath(contentDirectory);
        var bytes = File.ReadAllBytes(Path.Combine(ContentDirectory, "course.json"));
        Sha256 = Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
        Course = JsonSerializer.Deserialize<Course>(bytes, Json) ?? throw new InvalidDataException("Course file is empty.");
        Validate(Course);
    }
    public static void Validate(Course course)
    {
        if (course.Modules.Length == 0 || course.Modules.Select(m => m.Id).Distinct().Count() != course.Modules.Length) throw new InvalidDataException("Course modules must be unique and nonempty.");
        foreach (var m in course.Modules)
        {
            if (string.IsNullOrWhiteSpace(m.Id) || string.IsNullOrWhiteSpace(m.Scene)) throw new InvalidDataException("Module identifiers are required.");
            foreach (var t in new[] { m.Title, m.Objective, m.Why, m.Purpose, m.Mechanism, m.Takeaway })
                if (string.IsNullOrWhiteSpace(t.Es) || string.IsNullOrWhiteSpace(t.En)) throw new InvalidDataException($"Missing bilingual explanation: {m.Id}");
            if (m.Questions.Length < 2 || m.Steps.Length == 0 || m.Examples.Length == 0 || m.Sources.Length == 0) throw new InvalidDataException($"Incomplete lesson: {m.Id}");
            if (m.Questions.Select(q => q.Id).Distinct().Count() != m.Questions.Length) throw new InvalidDataException($"Duplicate question IDs: {m.Id}");
            foreach (var q in m.Questions)
                if (q.Options.Length < 2 || q.CorrectIndex < 0 || q.CorrectIndex >= q.Options.Length) throw new InvalidDataException($"Invalid quiz: {m.Id}/{q.Id}");
            if (m.Examples.Any(e => e.Params?.Values.Any(v => !double.IsFinite(v)) == true)) throw new InvalidDataException($"Invalid example parameters: {m.Id}");
        }
    }
    public IReadOnlyList<Slide> Slides()
    {
        using var doc = JsonDocument.Parse(File.ReadAllBytes(Path.Combine(ContentDirectory, "source-index.json")));
        return doc.RootElement.GetProperty("slides").EnumerateArray().Select(s => new Slide(s.GetProperty("slide").GetInt32(), s.GetProperty("title").GetString() ?? "", s.GetProperty("text").GetString() ?? "", s.GetProperty("notes").GetString() ?? "", s.GetProperty("image").GetString() ?? "", s.TryGetProperty("moduleIds", out var ids) ? ids.EnumerateArray().Select(i => i.GetString() ?? "").ToArray() : [])).ToArray();
    }
    public string ResolveAsset(string relativePath)
    {
        if (Path.IsPathRooted(relativePath)) throw new InvalidDataException("Course assets must be relative.");
        var full = Path.GetFullPath(Path.Combine(ContentDirectory, relativePath));
        if (!full.StartsWith(ContentDirectory + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException("Asset is outside the course.");
        return full;
    }
}

public sealed record QuizResult(string ModuleId, int Correct, int Total, DateTimeOffset AttemptedAt, Dictionary<string, int> Answers)
{
    public bool Passed => Correct == Total && Total > 0;
}
public sealed class LearningProgress
{
    public string CourseSha256 { get; set; } = "";
    public string Language { get; set; } = "es";
    public string SelectedModule { get; set; } = "";
    public Dictionary<string, QuizResult> Attempts { get; set; } = [];
    public Dictionary<string, string> Notes { get; set; } = [];
    public HashSet<string> Visited { get; set; } = [];
    public DateTimeOffset UpdatedAt { get; set; }
}
public sealed class ProgressStore
{
    readonly string path;
    public string PathName => path;
    public LearningProgress Progress { get; private set; }
    public string? RecoveryNotice { get; }
    public string? RecoveryPath { get; }
    public ProgressStore(string path, string courseSha)
    {
        this.path = Path.GetFullPath(path);
        var progress = new LearningProgress { CourseSha256 = courseSha };
        if (File.Exists(path))
        {
            try
            {
                var loaded = JsonSerializer.Deserialize<LearningProgress>(File.ReadAllBytes(path), CourseRepository.Json) ?? throw new InvalidDataException("Empty progress.");
                if (loaded.Attempts is null || loaded.Notes is null || loaded.Visited is null || loaded.Attempts.Any(pair => pair.Value is null || pair.Value.Answers is null || pair.Value.ModuleId != pair.Key || pair.Value.Total <= 0 || pair.Value.Total != pair.Value.Answers.Count || pair.Value.Correct < 0 || pair.Value.Correct > pair.Value.Total || pair.Value.Answers.Values.Any(i => i < 0)) || loaded.Notes.Any(pair => pair.Value is null)) throw new InvalidDataException("Invalid learning-progress collections or scores.");
                if (loaded.CourseSha256 == courseSha) progress = loaded;
                else RecoveryNotice = "course_changed";
            }
            catch (Exception e) when (e is JsonException or InvalidDataException) { RecoveryNotice = "invalid_progress_preserved"; }
            if (RecoveryNotice is not null)
            {
                RecoveryPath = this.path + ".recovery-" + DateTimeOffset.UtcNow.ToString("yyyyMMddTHHmmssfff") + "-" + Guid.NewGuid().ToString("N")[..8] + ".json";
                File.Copy(this.path, RecoveryPath, false);
            }
        }
        Progress = progress;
    }
    public void Save()
    {
        Directory.CreateDirectory(System.IO.Path.GetDirectoryName(path)!);
        if (File.Exists(path)) File.Copy(path, path + ".previous", true);
        Progress.UpdatedAt = DateTimeOffset.UtcNow;
        var temp = path + ".tmp";
        File.WriteAllBytes(temp, JsonSerializer.SerializeToUtf8Bytes(Progress, CourseRepository.Json));
        File.Move(temp, path, true);
    }
    public QuizResult Grade(CourseModule module, IReadOnlyDictionary<string, int> answers)
    {
        var complete = module.Questions.All(q => answers.TryGetValue(q.Id, out var index) && index >= 0 && index < q.Options.Length);
        if (!complete) throw new ArgumentException("Answer every question before checking the lesson.");
        var correct = module.Questions.Count(q => answers[q.Id] == q.CorrectIndex);
        var result = new QuizResult(module.Id, correct, module.Questions.Length, DateTimeOffset.UtcNow, new Dictionary<string, int>(answers));
        Progress.Attempts[module.Id] = result;
        Save();
        return result;
    }
}
