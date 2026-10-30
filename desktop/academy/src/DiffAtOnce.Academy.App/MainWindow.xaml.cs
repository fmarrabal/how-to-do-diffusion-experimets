using System.Diagnostics;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using DiffAtOnce.Academy.Core;
using DiffAtOnce.Academy.Tutor;
using Microsoft.Web.WebView2.Core;
using Microsoft.Win32;

namespace DiffAtOnce.Academy.App;

public partial class MainWindow : Window
{
    readonly CourseRepository repository;
    readonly ProgressStore progress;
    readonly TutorService tutor;
    readonly DerivationCatalogue? derivations;
    readonly string academyUserRoot;
    DerivationWindow? derivationWindow;
    DoctoralWindow? doctoralWindow;
    ResearchWindow? researchWindow;
    string? derivationModuleId;
    readonly Dictionary<string, List<RadioButton>> quiz = [];
    readonly Dictionary<string, Dictionary<string, int>> quizDrafts = [];
    readonly string? selfTestDirectory;
    readonly bool selfTestTutor;
    DiffAtOnce.Academy.Tutor.TutorAnswer? lastTutorResponse;
    string language = "es";
    CourseModule? selected;
    string? simulationContext;
    bool updating, labReady, labInitializing;
    bool nativeTeachingContext;
    CancellationTokenSource? tutorCancellation;
    int bridgeRevision;
    const string Host = "academy.diffatonce.local";

    public MainWindow(string[] args)
    {
        InitializeComponent();
        Width = Math.Min(1570, SystemParameters.WorkArea.Width); Height = Math.Min(990, SystemParameters.WorkArea.Height);
        MinWidth = Math.Min(1080, SystemParameters.WorkArea.Width); MinHeight = Math.Min(720, SystemParameters.WorkArea.Height);
        var index = Array.IndexOf(args, "--self-test");
        if (index >= 0 && args.Length > index + 1) selfTestDirectory = Path.GetFullPath(args[index + 1]);
        selfTestTutor = args.Contains("--tutor-test");
        repository = new CourseRepository(Path.Combine(AppContext.BaseDirectory, "Content"));
        var userRoot = selfTestDirectory ?? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "DiffAtOnce", "Academy");
        academyUserRoot = userRoot;
        progress = new ProgressStore(Path.Combine(userRoot, "progress-v1.json"), repository.Sha256);
        language = progress.Progress.Language == "en" ? "en" : "es";
        var derivationsPath = Path.Combine(repository.ContentDirectory, "derivations.json");
        derivations = File.Exists(derivationsPath) ? new DerivationCatalogue(derivationsPath) : null;
        tutor = new TutorService(Path.Combine(repository.ContentDirectory, "course.json"), Path.Combine(AppContext.BaseDirectory, "Models", "Beatrix"), derivationsPath);
        Localize();
        RefreshNavigation(progress.Progress.SelectedModule);
        if (progress.RecoveryNotice is not null) { StatusText.Text = T("Se ha conservado una copia del progreso anterior y se inicia un registro nuevo.", "A recovery copy of previous progress was preserved; a new record has been started."); StatusText.ToolTip = progress.RecoveryPath; }
        Loaded += async (_, _) =>
        {
            if (selfTestDirectory is not null) { File.AppendAllText(Path.Combine(selfTestDirectory, "startup-stages.txt"), "loaded" + Environment.NewLine); LearningTabs.SelectedItem = SimulationTab; await SelfTest(); }
        };
        // A WebView2 in an unselected WPF tab is not loaded. Initialize it
        // when the simulation tab enters the visual tree, without stalling startup.
        LabView.Loaded += async (_, _) => { if (!labReady && !labInitializing) { labInitializing = true; await InitializeLab(userRoot); } };
        LearningTabs.SelectionChanged += (_, e) => { if (ReferenceEquals(e.Source, LearningTabs) && LearningTabs.SelectedItem == SimulationTab) { derivationModuleId = null; nativeTeachingContext = false; simulationContext = null; if (selected is not null) TutorContext.Text = T("Contexto: ", "Context: ") + selected.Title.In(language); } };
        Closing += (_, _) => { tutorCancellation?.Cancel(); SaveNotes(); };
        Closed += async (_, _) => await tutor.DisposeAsync();
    }

    string T(string es, string en) => language == "en" ? en : es;
    void Localize()
    {
        Subtitle.Text = T("Aprender a medir. Entender antes de interpretar.", "Learn to measure. Understand before interpreting.");
        LanguageButton.Content = language == "es" ? "EN" : "ES";
        WorkshopButton.Content = T("Taller numérico", "Numeric workshop");
        DerivationsButton.Content = T("Derivar ecuaciones", "Derive equations"); DerivationsButton.IsEnabled = derivations is not null;
        DoctoralButton.Content = T("Laboratorio doctoral", "Doctoral laboratory");
        ResearchButton.Content = T("Investigación continua", "Research studio");
        SlidesButton.Content = T("81 diapositivas", "81 source slides");
        MethodsButton.Content = T("Métodos", "Methods");
        ExportButton.Content = T("Exportar", "Export");
        HelpButton.Content = T("Manual", "Manual"); ExpandLabButton.Content = T("Ampliar laboratorio ↗", "Expand laboratory ↗");
        CourseHeading.Text = T("RECORRIDO DE APRENDIZAJE", "LEARNING PATH");
        SearchBox.ToolTip = T("Buscar una lección", "Search lessons");
        LessonTab.Header = T("Comprender", "Understand"); SimulationTab.Header = T("Experimentar", "Experiment");
        PracticeTab.Header = T("Comprobar", "Check yourself"); NotebookTab.Header = T("Mi cuaderno", "My notebook");
        NotebookHint.Text = T("Anota tu hipótesis, qué cambiaste y qué aprendiste. Se guarda en este ordenador.", "Record your hypothesis, what you changed and what you learned. Saved on this computer.");
        TutorSubtitle.Text = T("Tu tutor de RMN de difusión", "Your diffusion NMR tutor");
        TutorGeneratedHeading.Text = T("Explicación de Beatrix · LLM", "Beatrix's explanation · LLM");
        TutorQuoteHeading.Text = T("Texto literal del curso · fuente", "Literal course text · source");
        TutorMode.Text = derivationModuleId is not null ? T("Guía matemática revisada · sin LLM", "Reviewed mathematical guide · no LLM") : DefaultTutorMode();
        WhyButton.Content = T("¿Por qué sucede?", "Why does this happen?"); NextButton.Content = T("¿Qué compruebo?", "What should I check?");
        AskButton.Content = new TextBlock { Text = T("Preguntar", "Ask Beatrix"), Foreground = Brushes.White }; CancelButton.Content = T("Cancelar", "Cancel");
        StatusText.Text = T("Formación · simulaciones sintéticas · progreso guardado localmente", "Teaching · synthetic simulations · progress saved locally");
        if (selected is null) TutorAnswer.Text = T("Selecciona una lección y pregunta. Puedo usar el contenido del curso y el contexto de tu simulación.", "Select a lesson and ask. I can use the course evidence and your simulation context.");
        UpdateProgress();
    }

    record NavigationItem(CourseModule Module, string Number, string Title, string State);
    string DefaultTutorMode() => tutor.IsModelInstalled ? T("LLM local · verificación al preguntar", "Local LLM · verified when you ask") : T("Guía documental · modelo no instalado", "Documentary guide · model not installed");
    void RefreshNavigation(string? id = null)
    {
        if (repository is null) return;
        var term = SearchBox.Text.Trim();
        var list = repository.Course.Modules.OrderBy(m => m.Order)
            .Where(m => term.Length == 0 || (m.Title.In(language) + " " + m.Chapter.In(language) + " " + m.Why.In(language)).Contains(term, StringComparison.CurrentCultureIgnoreCase))
            .Select(m => new NavigationItem(m, m.Order.ToString("00"), m.Title.In(language), progress.Progress.Attempts.TryGetValue(m.Id, out var result) && result.Passed ? T("✓ Comprobado", "✓ Checked") : m.Chapter.In(language))).ToArray();
        updating = true; ModuleList.ItemsSource = list;
        ModuleList.SelectedItem = list.FirstOrDefault(n => n.Module.Id == (id ?? selected?.Id)) ?? list.FirstOrDefault();
        updating = false;
        if (ModuleList.SelectedItem is NavigationItem item && selected?.Id != item.Module.Id) SelectModule(item.Module);
        if (list.Length == 0) StatusText.Text = T("No hay lecciones que coincidan con la búsqueda.", "No lessons match the search.");
    }
    void UpdateProgress()
    {
        if (progress is null) return;
        var passed = repository.Course.Modules.Count(m => progress.Progress.Attempts.TryGetValue(m.Id, out var q) && q.Passed);
        ProgressText.Text = T($"{passed} / {repository.Course.Modules.Length} lecciones comprobadas", $"{passed} / {repository.Course.Modules.Length} lessons checked");
        CourseProgress.Maximum = repository.Course.Modules.Length; CourseProgress.Value = passed;
    }
    void Search_Changed(object sender, TextChangedEventArgs e) { if (!updating && repository is not null) RefreshNavigation(); }
    void Module_Changed(object sender, SelectionChangedEventArgs e) { if (!updating && ModuleList.SelectedItem is NavigationItem item) SelectModule(item.Module); }
    void SelectModule(CourseModule module)
    {
        SaveNotes(); PreserveQuizDraft(); tutorCancellation?.Cancel();
        selected = module; derivationModuleId = null; simulationContext = null; nativeTeachingContext = false;
        TutorMode.Text = DefaultTutorMode();
        progress.Progress.SelectedModule = module.Id; progress.Progress.Visited.Add(module.Id);
        ChapterText.Text = module.Chapter.In(language).ToUpperInvariant(); ModuleTitle.Text = module.Title.In(language);
        ModuleOverview.Text = module.Objective.In(language);
        NotesBox.Text = progress.Progress.Notes.GetValueOrDefault(module.Id, "");
        TutorContext.Text = T("Contexto: ", "Context: ") + module.Title.In(language);
        TutorAnswer.Text = T("Pregunta por qué ocurre el problema, qué comprobar o cómo interpretar el ejemplo. Las respuestas mostrarán sus fuentes.", "Ask why the problem occurs, what to check or how to interpret the example. Answers will show their sources.");
        TutorSources.Children.Clear(); TutorStatus.Text = "";
        TutorCourseQuoteCard.Visibility = TutorGeneratedHeading.Visibility = Visibility.Collapsed;
        RenderLesson(); RenderQuiz(); SafeSave();
        if (labReady) _ = ApplyExample(null);
    }
    void Language_Click(object sender, RoutedEventArgs e)
    {
        SaveNotes(); PreserveQuizDraft(); tutorCancellation?.Cancel(); derivationModuleId = null; nativeTeachingContext = false; simulationContext = null; language = language == "es" ? "en" : "es";
        progress.Progress.Language = language; Localize(); RefreshNavigation();
        if (selected is not null) { ChapterText.Text = selected.Chapter.In(language).ToUpperInvariant(); ModuleTitle.Text = selected.Title.In(language); ModuleOverview.Text = selected.Objective.In(language); RenderLesson(); RenderQuiz(); TutorContext.Text = T("Contexto: ", "Context: ") + selected.Title.In(language); }
        TutorAnswer.Text = T("Pregunta por qué ocurre el problema, qué comprobar o cómo interpretar el ejemplo. Las respuestas mostrarán sus fuentes.", "Ask why the problem occurs, what to check or how to interpret the example. Answers will show their sources."); TutorSources.Children.Clear(); TutorStatus.Text = "";
        TutorCourseQuoteCard.Visibility = TutorGeneratedHeading.Visibility = Visibility.Collapsed;
        SafeSave(); if (labReady) _ = ApplyExample(null);
        if (derivationWindow is not null) _ = derivationWindow.SetLanguage(language);
        if (doctoralWindow is not null) _ = doctoralWindow.SetLanguage(language);
        if (researchWindow is not null) _ = researchWindow.SetLanguage(language);
    }
    void SafeSave()
    {
        try { progress.Save(); }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException) { StatusText.Text = T("No se ha podido guardar el progreso: ", "Progress could not be saved: ") + e.Message; }
    }
    void SaveNotes() { if (selected is null || progress is null) return; progress.Progress.Notes[selected.Id] = NotesBox.Text; SafeSave(); }
    void Notes_LostFocus(object sender, RoutedEventArgs e) => SaveNotes();

    internal static TextBlock Text(string value, double size = 14, bool bold = false) => new() { Text = value, FontSize = size, FontWeight = bold ? FontWeights.SemiBold : FontWeights.Normal, TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 0, 0, 9), LineHeight = size * 1.5 };
    internal static Border Card(UIElement child, string color = "#F1F7F7") => new() { Child = child, Background = (Brush)new BrushConverter().ConvertFromString(color)!, Padding = new Thickness(17), CornerRadius = new CornerRadius(9), Margin = new Thickness(0, 0, 0, 17) };
    void Section(string heading, string body, string color = "#F1F7F7") { var panel = new StackPanel(); panel.Children.Add(Text(heading, 17, true)); panel.Children.Add(Text(body)); LessonPanel.Children.Add(Card(panel, color)); }
    void RenderLesson()
    {
        if (selected is null) return;
        LessonPanel.Children.Clear();
        Section(T("El objetivo", "The objective"), selected.Objective.In(language));
        Section(T("El problema: por qué sucede", "The problem: why it happens"), selected.Why.In(language), "#FFF3E7");
        Section(T("Para qué hacemos este paso", "Why we do this step"), selected.Purpose.In(language));
        Section(T("Qué está ocurriendo físicamente", "What happens physically"), selected.Mechanism.In(language), "#EFF3FA");
        LessonPanel.Children.Add(Text(T("Cómo se hace", "How to do it"), 21, true));
        for (var i = 0; i < selected.Steps.Length; i++) { var step = selected.Steps[i]; LessonPanel.Children.Add(Text($"{i + 1}. {step.Title.In(language)}", 16, true)); LessonPanel.Children.Add(Text(step.Body.In(language))); }
        LessonPanel.Children.Add(Text(T("Ejemplos prácticos", "Practical examples"), 21, true));
        foreach (var example in selected.Examples)
        {
            var panel = new StackPanel(); panel.Children.Add(Text(example.Title.In(language), 16, true)); panel.Children.Add(Text(example.Instruction.In(language)));
            var button = new Button { Content = T("Abrir este experimento →", "Open this experiment →"), HorizontalAlignment = HorizontalAlignment.Left };
            button.Click += async (_, _) => { LearningTabs.SelectedItem = SimulationTab; await ApplyExample(example); }; panel.Children.Add(button); LessonPanel.Children.Add(Card(panel));
        }
        LessonPanel.Children.Add(Text(T("Errores que debes detectar", "Errors to detect"), 21, true));
        foreach (var pitfall in selected.Pitfalls) LessonPanel.Children.Add(Text("• " + pitfall.In(language)));
        Section(T("Qué debes llevarte", "What to remember"), selected.Takeaway.In(language), "#E3F3ED");
        LessonPanel.Children.Add(Text(T("Fuentes y material del workshop", "Sources and workshop material"), 17, true));
        foreach (var source in selected.Sources) LessonPanel.Children.Add(SourceButton(source.Title, source.Url, source.Slide));
    }
    UIElement SourceButton(string title, string? url, int? slide)
    {
        var button = new Button { Content = Text(title + (slide is not null ? T($" · diapositiva {slide}", $" · slide {slide}") : ""), 12), HorizontalContentAlignment = HorizontalAlignment.Left, ToolTip = url ?? title };
        button.Click += (_, _) => { if (slide is not null) OpenSlides(slide); else if (Uri.TryCreate(url, UriKind.Absolute, out var uri) && uri.Scheme is "https" or "http") Process.Start(new ProcessStartInfo(uri.AbsoluteUri) { UseShellExecute = true }); };
        if (slide is null && string.IsNullOrWhiteSpace(url)) button.IsEnabled = false;
        return button;
    }
    void RenderQuiz()
    {
        if (selected is null) return;
        PracticePanel.Children.Clear(); quiz.Clear();
        PracticePanel.Children.Add(Text(T("Decide antes de mirar la explicación", "Decide before reading the explanation"), 21, true));
        PracticePanel.Children.Add(Text(T("Responde todas las preguntas. Puedes repetir el ejercicio después de experimentar.", "Answer every question. You can try again after experimenting.")));
        var existing = progress.Progress.Attempts.GetValueOrDefault(selected.Id);
        foreach (var q in selected.Questions)
        {
            PracticePanel.Children.Add(Text(q.Question.In(language), 16, true));
            var options = new List<RadioButton>();
            var draft = quizDrafts.GetValueOrDefault(selected.Id)?.GetValueOrDefault(q.Id, -1) ?? existing?.Answers.GetValueOrDefault(q.Id, -1) ?? -1;
            for (var i = 0; i < q.Options.Length; i++) { var option = new RadioButton { GroupName = selected.Id + "/" + q.Id, Content = Text(q.Options[i].In(language)), IsChecked = draft == i }; options.Add(option); }
            // Shuffle only the visual order. The list used for grading retains
            // original option indices and is stable across language switches.
            var seed = BitConverter.ToInt32(System.Security.Cryptography.SHA256.HashData(Encoding.UTF8.GetBytes(selected.Id + q.Id)), 0);
            var random = new Random(seed); foreach (var option in options.OrderBy(_ => random.Next())) PracticePanel.Children.Add(option);
            quiz[q.Id] = options;
        }
        var feedback = new StackPanel(); var check = new Button { Content = T("Comprobar y aprender", "Check and learn"), HorizontalAlignment = HorizontalAlignment.Left, Margin = new Thickness(0, 15, 0, 15) };
        check.Click += (_, _) =>
        {
            feedback.Children.Clear(); var answers = quiz.ToDictionary(p => p.Key, p => p.Value.FindIndex(r => r.IsChecked == true));
            if (answers.Values.Any(i => i < 0)) { feedback.Children.Add(Text(T("Falta responder alguna pregunta.", "Please answer every question."))); return; }
            try
            {
                var result = progress.Grade(selected, answers); feedback.Children.Add(Text(T($"Resultado: {result.Correct}/{result.Total}. ", $"Result: {result.Correct}/{result.Total}. ") + (result.Passed ? T("Has comprobado esta lección.", "You have checked this lesson.") : T("Revisa las explicaciones y vuelve a intentarlo.", "Review the explanations and try again.")), 17, true));
                foreach (var q in selected.Questions) feedback.Children.Add(Card(Text((answers[q.Id] == q.CorrectIndex ? "✓ " : "↺ ") + q.Explanation.In(language)), answers[q.Id] == q.CorrectIndex ? "#E3F3ED" : "#FFF3E7"));
                UpdateProgress(); RefreshNavigation(selected.Id);
            }
            catch (IOException e) { feedback.Children.Add(Text(e.Message)); }
        };
        PracticePanel.Children.Add(check); PracticePanel.Children.Add(feedback);
    }
    void PreserveQuizDraft() { if (selected is not null && quiz.Count > 0) quizDrafts[selected.Id] = quiz.ToDictionary(p => p.Key, p => p.Value.FindIndex(r => r.IsChecked == true)); }

    async Task InitializeLab(string userRoot)
    {
        try
        {
            var environment = await CoreWebView2Environment.CreateAsync(null, Path.Combine(userRoot, "WebView")).WaitAsync(TimeSpan.FromSeconds(20));
            await LabView.EnsureCoreWebView2Async(environment).WaitAsync(TimeSpan.FromSeconds(20));
            var web = LabView.CoreWebView2;
            web.SetVirtualHostNameToFolderMapping(Host, Path.Combine(AppContext.BaseDirectory, "Lab"), CoreWebView2HostResourceAccessKind.DenyCors);
            web.Settings.IsWebMessageEnabled = true; web.Settings.AreDevToolsEnabled = selfTestDirectory is not null;
            web.Settings.AreDefaultContextMenusEnabled = false;
            web.NavigationStarting += (_, e) => { if (!AllowedNavigation(e.Uri)) { e.Cancel = true; if (e.IsUserInitiated) OpenReference(e.Uri); } };
            web.NewWindowRequested += (_, e) => { e.Handled = true; if (e.IsUserInitiated) OpenReference(e.Uri); };
            web.PermissionRequested += (_, e) => e.State = CoreWebView2PermissionState.Deny;
            web.WebResourceRequested += (_, e) =>
            {
                if (!AllowedNavigation(e.Request.Uri) && !e.Request.Uri.StartsWith("data:") && !e.Request.Uri.StartsWith("blob:")) e.Response = web.Environment.CreateWebResourceResponse(new MemoryStream(), 403, "Offline teaching content only", "Content-Type: text/plain");
            };
            web.AddWebResourceRequestedFilter("*", CoreWebView2WebResourceContext.All);
            web.WebMessageReceived += (_, e) =>
            {
                if (!AllowedNavigation(e.Source) || e.WebMessageAsJson.Length > 64000) return;
                try
                {
                    using var doc = JsonDocument.Parse(e.WebMessageAsJson); var root = doc.RootElement;
                    if (root.TryGetProperty("type", out var kind) && kind.GetString() == "academy-context" && root.TryGetProperty("context", out var context))
                    {
                        var current = selected is not null && context.TryGetProperty("scene", out var scene) && scene.GetString() == selected.Scene && context.TryGetProperty("language", out var lang) && lang.GetString() == language && context.TryGetProperty("moduleId", out var module) && module.GetString() == selected.Id && context.TryGetProperty("revision", out var revision) && revision.GetInt32() == bridgeRevision;
                        var text = context.GetRawText(); if (!nativeTeachingContext && current && text.Length < 10000) simulationContext = text;
                        else if (!nativeTeachingContext && context.TryGetProperty("revision", out var currentRevision) && currentRevision.GetInt32() == bridgeRevision) simulationContext = null;
                    }
                }
                catch (JsonException) { }
            };
            web.NavigationCompleted += async (_, e) =>
            {
                if (!e.IsSuccess) { LabLoading.Text = T("No se ha podido abrir el laboratorio local.", "The local lab could not be opened."); return; }
                labReady = true; LabLoading.Visibility = Visibility.Collapsed; await ApplyExample(null);
            };
            web.DownloadStarting += (_, e) =>
            {
                var name = Path.GetFileName(e.ResultFilePath); var dialog = new SaveFileDialog { FileName = name, Title = T("Guardar simulación", "Save simulation"), OverwritePrompt = true };
                if (dialog.ShowDialog(this) == true) e.ResultFilePath = dialog.FileName; else e.Cancel = true;
                e.Handled = true;
            };
            web.Navigate($"https://{Host}/index.html?scene={selected?.Scene ?? "pulse-90"}&lang={language}");
        }
        catch (Exception e) when (e is WebView2RuntimeNotFoundException or InvalidOperationException or IOException or TimeoutException or System.Runtime.InteropServices.COMException)
        {
            LabLoading.Text = T("El laboratorio requiere Microsoft Edge WebView2 Runtime. Puedes seguir usando las lecciones y el taller numérico. Detalle: ", "The lab requires Microsoft Edge WebView2 Runtime. Lessons and the numeric workshop remain available. Details: ") + e.Message;
            if (selfTestDirectory is not null) File.WriteAllText(Path.Combine(selfTestDirectory, "lab-initialization-error.txt"), e.ToString());
        }
    }
    static bool AllowedNavigation(string url) => Uri.TryCreate(url, UriKind.Absolute, out var uri) && uri.Scheme == "https" && uri.Host == Host;
    static void OpenReference(string url) { if (Uri.TryCreate(url, UriKind.Absolute, out var uri) && uri.Scheme is "https" or "http") Process.Start(new ProcessStartInfo(uri.AbsoluteUri) { UseShellExecute = true }); }
    async Task ApplyExample(LessonExample? example)
    {
        if (!labReady || selected is null) return;
        var scene = selected.Scene; var payload = JsonSerializer.Serialize(new { scene, lang = language, moduleId = selected.Id, revision = ++bridgeRevision, parameters = example?.Params, preset = example?.Preset });
        try
        {
            var result = await LabView.ExecuteScriptAsync($"window.AcademyBridge?.apply({payload})");
            using var parsed = JsonDocument.Parse(result);
            var root = parsed.RootElement;
            if (root.ValueKind != JsonValueKind.Object || !root.TryGetProperty("ok", out var ok) || !ok.GetBoolean()) { simulationContext = null; StatusText.Text = T("No se ha podido cargar el ejemplo. Termina cualquier grabación y vuelve a abrirlo.", "The example could not be loaded. Finish any recording and try again."); return; }
            if (example is not null)
            {
                var rejected = root.ValueKind == JsonValueKind.Object && root.TryGetProperty("rejected", out var items) && items.GetArrayLength() > 0;
                StatusText.Text = T("Ejemplo cargado: ", "Example loaded: ") + example.Title.In(language) + (rejected ? T(" · revisa los parámetros no disponibles", " · review unavailable parameters") : "");
            }
        }
        catch (Exception e) when (e is InvalidOperationException or JsonException) { simulationContext = null; StatusText.Text = e.Message; }
    }

    void Research_Click(object sender, RoutedEventArgs e)
    {
        if (researchWindow is not null) { researchWindow.WindowState = WindowState.Normal; researchWindow.Activate(); return; }
        researchWindow = new ResearchWindow(language, academyUserRoot, selfTestDirectory is not null) { Owner = this };
        researchWindow.Closed += (_, _) => researchWindow = null;
        researchWindow.Show();
    }
    void Doctoral_Click(object sender, RoutedEventArgs e)
    {
        if (doctoralWindow is not null) { doctoralWindow.WindowState = WindowState.Normal; doctoralWindow.Activate(); return; }
        doctoralWindow = new DoctoralWindow(language, academyUserRoot) { Owner = this };
        doctoralWindow.Closed += (_, _) => doctoralWindow = null;
        doctoralWindow.Show();
    }
    async void Ask_Click(object sender, RoutedEventArgs e) => await Ask();
    async Task Ask()
    {
        if (selected is null || string.IsNullOrWhiteSpace(QuestionBox.Text)) { TutorStatus.Text = T("Escribe tu pregunta.", "Enter your question."); return; }
        var moduleId = derivationModuleId ?? selected.Id; var lang = language;
        tutorCancellation?.Cancel(); var requestCancellation = new CancellationTokenSource(); tutorCancellation = requestCancellation; var token = requestCancellation.Token;
        bool Current() => ReferenceEquals(tutorCancellation, requestCancellation) && (derivationModuleId ?? selected?.Id) == moduleId && language == lang;
        AskButton.IsEnabled = false; WhyButton.IsEnabled = false; NextButton.IsEnabled = false; CancelButton.IsEnabled = true;
        try
        {
            var context = simulationContext is null ? null : JsonSerializer.Serialize(new { evidenceStatus = "synthetic-teaching-simulation", moduleId, simulation = JsonSerializer.Deserialize<JsonElement>(simulationContext) });
            var answer = await tutor.AskAsync(lang, QuestionBox.Text.Trim(), moduleId, context, token, new Progress<string>(value => { if (Current()) TutorStatus.Text = value; }));
            if (token.IsCancellationRequested || !Current()) return;
            lastTutorResponse = answer;
            TutorAnswer.Text = answer.Status == "supplemental_documentary_only"
                ? T("Consulta los pasos, ecuaciones y supuestos revisados que aparecen a continuación. Este recorrido matemático se muestra sin generación LLM.", "Consult the reviewed steps, equations and assumptions below. This mathematical pathway is shown without LLM generation.")
                : answer.GeneratedText ?? answer.Text;
            TutorMode.Text = answer.EngineLabel;
            TutorCourseQuoteText.Text = answer.CourseQuote ?? "";
            TutorQuoteHeading.Text = answer.IncludesSupplementalEvidence ? T("Texto del recorrido matemático · fuente revisada", "Mathematical course text · reviewed source") : T("Texto literal del curso · fuente", "Literal course text · source");
            TutorCourseQuoteCard.Visibility = answer.IncludesCourseQuote ? Visibility.Visible : Visibility.Collapsed;
            TutorGeneratedHeading.Visibility = answer.IsModelAnswer ? Visibility.Visible : Visibility.Collapsed;
            TutorSources.Children.Clear(); foreach (var source in answer.Sources) TutorSources.Children.Add(SourceButton(source.Title + (source.Pages is { Count: > 0 } ? T(" · PDF pág. ", " · PDF p. ") + string.Join(", ", source.Pages) : ""), source.Url, source.Slide));
            var meaning = answer.Status switch
            {
                "answer" => T("Respuesta con fuentes", "Sourced answer"),
                "insufficient_evidence" => T("Faltan datos", "More evidence needed"),
                "bounded_answer" => T("Respuesta limitada en longitud", "Length-limited answer"),
                "context_too_long" => T("Consulta extensa: se muestran las fuentes", "Long query: showing course evidence"),
                "model_not_installed" => T("Modelo no instalado: se muestra el curso", "Model not installed: showing course evidence"),
                "supplemental_documentary_only" => T("Guía matemática revisada · sin LLM", "Reviewed mathematical guide · no LLM"),
                _ => T("Se muestran las fuentes del curso", "Showing course evidence")
            };
            TutorStatus.Text = $"{answer.ElapsedSeconds:F1} s · {meaning}";
        }
        catch (OperationCanceledException) { if (Current()) TutorStatus.Text = T("Pregunta cancelada.", "Question cancelled."); }
        catch (Exception e) when (e is ArgumentException or IOException or JsonException or InvalidOperationException) { if (Current()) TutorStatus.Text = e.Message; }
        finally { if (ReferenceEquals(tutorCancellation, requestCancellation)) { AskButton.IsEnabled = true; WhyButton.IsEnabled = true; NextButton.IsEnabled = true; CancelButton.IsEnabled = false; tutorCancellation = null; } requestCancellation.Dispose(); }
    }
    void Cancel_Click(object sender, RoutedEventArgs e) => tutorCancellation?.Cancel();
    async void Why_Click(object sender, RoutedEventArgs e) { QuestionBox.Text = T("¿Por qué sucede el problema de esta lección y qué objetivo tiene resolverlo?", "Why does the problem in this lesson occur, and what is the objective of solving it?"); await Ask(); }
    async void Next_Click(object sender, RoutedEventArgs e) { QuestionBox.Text = T("¿Qué debo comprobar primero en este ejemplo y cómo sé si el resultado es fiable?", "What should I check first in this example, and how can I assess whether the result is reliable?"); await Ask(); }
    void Workshop_Click(object sender, RoutedEventArgs e)
    {
        var window = new CalibrationWorkshopWindow(language) { Owner = this };
        window.TeachingContextChanged += (moduleId, context) =>
        {
            var module = repository.Course.Modules.FirstOrDefault(m => m.Id == moduleId); if (module is null) return;
            if (selected?.Id != moduleId) { updating = true; SearchBox.Clear(); updating = false; RefreshNavigation(moduleId); if (selected?.Id != moduleId) SelectModule(module); }
            derivationModuleId = null; nativeTeachingContext = true; simulationContext = context;
            TutorMode.Text = DefaultTutorMode();
            TutorContext.Text = T("Contexto: taller numérico · ", "Context: numeric workshop · ") + module.Title.In(language);
        };
        window.Show(); window.PublishActiveContext();
    }
    void Derivations_Click(object sender, RoutedEventArgs e)
    {
        if (derivations is null) return;
        if (derivationWindow is not null) { derivationWindow.WindowState = WindowState.Normal; derivationWindow.Activate(); return; }
        derivationWindow = new DerivationWindow(derivations, language, academyUserRoot) { Owner = this };
        derivationWindow.ChapterSelected += SetDerivationContext;
        derivationWindow.Closed += (_, _) => { derivationWindow = null; if (derivationModuleId is not null) { tutorCancellation?.Cancel(); derivationModuleId = null; simulationContext = null; nativeTeachingContext = false; TutorContext.Text = T("Contexto: ", "Context: ") + selected?.Title.In(language); TutorMode.Text = DefaultTutorMode(); TutorSources.Children.Clear(); TutorCourseQuoteCard.Visibility = TutorGeneratedHeading.Visibility = Visibility.Collapsed; TutorAnswer.Text = T("Selecciona una lección y pregunta por sus objetivos, causas o comprobaciones.", "Select a lesson and ask about its objectives, causes or checks."); } };
        derivationWindow.Show();
    }
    void SetDerivationContext(string chapterId, string title, bool askBeatrix)
    {
        if (derivations?.Find(chapterId) is null) return;
        tutorCancellation?.Cancel(); derivationModuleId = "derivation:" + chapterId; nativeTeachingContext = true; simulationContext = null;
        TutorContext.Text = T("Contexto: derivación · ", "Context: derivation · ") + title;
        TutorMode.Text = T("Guía matemática revisada · sin LLM", "Reviewed mathematical guide · no LLM");
        TutorAnswer.Text = T("Consulta un paso, su ecuación diferencial, sus unidades o sus supuestos. Se mostrará la guía matemática revisada, sin generación LLM. Beatrix conserva el modelo local para las lecciones originales; estos artículos no formaron parte de su ajuste fino.", "Consult a step, its differential equation, units or assumptions. The reviewed mathematical guide is shown without LLM generation. Beatrix retains its local model for the original lessons; these papers were not included in its fine-tuning.");
        TutorSources.Children.Clear(); TutorCourseQuoteCard.Visibility = TutorGeneratedHeading.Visibility = Visibility.Collapsed;
        if (askBeatrix)
        {
            if (derivationWindow is not null) derivationWindow.WindowState = WindowState.Minimized;
            Activate(); QuestionBox.Focus();
        }
    }
    void Slides_Click(object sender, RoutedEventArgs e) => OpenSlides(selected?.Sources.FirstOrDefault(s => s.Slide is not null)?.Slide);
    void OpenSlides(int? slide) => new SourceSlidesWindow(repository, language, slide) { Owner = this }.Show();
    void Methods_Click(object sender, RoutedEventArgs e) => new MethodsWindow(repository.ContentDirectory, language) { Owner = this }.Show();
    void Help_Click(object sender, RoutedEventArgs e)
    {
        var guide = Path.Combine(AppContext.BaseDirectory, "Docs", "ACADEMY_MANUAL_" + language.ToUpperInvariant() + ".pdf");
        if (File.Exists(guide)) Process.Start(new ProcessStartInfo(guide) { UseShellExecute = true });
        else new GuideWindow(Path.Combine(AppContext.BaseDirectory, "Docs", "USER_GUIDE_" + language.ToUpperInvariant() + ".md"), language) { Owner = this }.Show();
    }
    void ExpandLab_Click(object sender, RoutedEventArgs e)
    {
        if (!labReady) return;
        LabHost.Children.Remove(LabView);
        var window = new Window { Title = "DiffAtOnce Academy · " + T("Laboratorio", "Laboratory"), Width = Math.Min(1440, SystemParameters.WorkArea.Width), Height = Math.Min(970, SystemParameters.WorkArea.Height), WindowStartupLocation = WindowStartupLocation.CenterScreen, Content = LabView, Owner = this };
        ExpandLabButton.IsEnabled = false;
        window.Closed += (_, _) => { window.Content = null; LabHost.Children.Insert(0, LabView); ExpandLabButton.IsEnabled = true; };
        window.Show();
    }
    void Export_Click(object sender, RoutedEventArgs e)
    {
        SaveNotes(); var dialog = new SaveFileDialog { FileName = "DiffAtOnce-Academy-progress.json", Filter = "JSON (*.json)|*.json", OverwritePrompt = true };
        if (dialog.ShowDialog(this) != true) return;
        try { File.WriteAllText(dialog.FileName, JsonSerializer.Serialize(new { application = "DiffAtOnce Academy 1.1", courseSha256 = repository.Sha256, supplementalSha256 = derivations?.Sha256, evidenceStatus = "student-learning-progress", progress = progress.Progress }, CourseRepository.Json)); StatusText.Text = T("Progreso exportado.", "Progress exported."); }
        catch (IOException error) { StatusText.Text = error.Message; }
    }

    async Task SelfTest()
    {
        Directory.CreateDirectory(selfTestDirectory!);
        var checks = new List<object>();
        var selfTestPassed = false;
        try
        {
            for (var i = 0; i < 120 && !labReady; i++) await Task.Delay(250);
            checks.Add(new { check = "course", passed = repository.Course.Modules.Length >= 24, modules = repository.Course.Modules.Length, slides = repository.Slides().Count });
            foreach (var module in repository.Course.Modules) { SelectModule(module); progress.Grade(module, module.Questions.ToDictionary(q => q.Id, q => q.CorrectIndex)); }
            checks.Add(new { check = "all_quizzes", passed = progress.Progress.Attempts.Count == repository.Course.Modules.Length });
            SelectModule(repository.Course.Modules.First()); NotesBox.Text = "Self-test notebook: hypothesis / observation / conclusion."; SaveNotes();
            var reload = new ProgressStore(progress.PathName, repository.Sha256);
            checks.Add(new { check = "progress_roundtrip", passed = reload.Progress.Notes.GetValueOrDefault(selected!.Id) == NotesBox.Text });
            var draftQuestion = selected!.Questions[0].Id; quiz[draftQuestion][0].IsChecked = true;
            Language_Click(this, new RoutedEventArgs()); checks.Add(new { check = "english", passed = ModuleTitle.Text == selected!.Title.En });
            checks.Add(new { check = "quiz_draft_survives_translation", passed = quiz[draftQuestion][0].IsChecked == true });
            LearningTabs.SelectedItem = LessonTab; await Task.Delay(350); AcademyWindow.CaptureWindow(this, Path.Combine(selfTestDirectory!, "academy-lesson-en.png"));
            var englishWorkshop = new CalibrationWorkshopWindow("en"); englishWorkshop.Show(); await Task.Delay(350); englishWorkshop.Capture(Path.Combine(selfTestDirectory!, "academy-calibration-en.png")); englishWorkshop.Close();
            Language_Click(this, new RoutedEventArgs());
            LearningTabs.SelectedItem = LessonTab;
            UpdateProgress(); RefreshNavigation(selected?.Id);
            await Dispatcher.InvokeAsync(() => { }, System.Windows.Threading.DispatcherPriority.ApplicationIdle);
            AcademyWindow.CaptureWindow(this, Path.Combine(selfTestDirectory!, "academy-lesson.png"));
            Width = 1080; Height = 720; LearningTabs.SelectedItem = LessonTab; SelectModule(repository.Course.Modules.First());
            foreach (var compactLanguage in new[] { "es", "en" })
            {
                if (language != compactLanguage) Language_Click(this, new RoutedEventArgs());
                await Dispatcher.InvokeAsync(() => { }, System.Windows.Threading.DispatcherPriority.ApplicationIdle); await Task.Delay(350);
                var actionBounds = HeaderActions.Children.OfType<Button>().Select(button => new Rect(button.TransformToAncestor(HeaderRoot).Transform(new Point()), button.RenderSize)).ToArray();
                checks.Add(new { check = "compact_header_and_content_" + compactLanguage,
                    passed = HeaderTitle.ActualHeight < 60 && HeaderBrand.ActualWidth > 300 && HeaderRoot.ActualHeight < 220 && LearningTabs.ActualHeight >= 200 && TutorResponseScroll.ActualHeight >= 150 && actionBounds.All(bounds => bounds.Left >= -1 && bounds.Right <= HeaderRoot.ActualWidth + 1 && bounds.Top >= -1 && bounds.Bottom <= HeaderRoot.ActualHeight + 1),
                    headerHeight = HeaderRoot.ActualHeight, titleHeight = HeaderTitle.ActualHeight, contentHeight = LearningTabs.ActualHeight, tutorResponseHeight = TutorResponseScroll.ActualHeight, actionBounds });
                TutorPaneScroll.ScrollToTop(); await Task.Delay(150);
                AcademyWindow.CaptureWindow(this, Path.Combine(selfTestDirectory!, "academy-compact-" + compactLanguage + ".png"));
                TutorPaneScroll.ScrollToEnd(); await Dispatcher.InvokeAsync(() => { }, System.Windows.Threading.DispatcherPriority.ApplicationIdle); await Task.Delay(150);
                var inputBounds = new Rect(QuestionBox.TransformToAncestor(TutorPaneScroll).Transform(new Point()), QuestionBox.RenderSize);
                var askBounds = new Rect(AskButton.TransformToAncestor(TutorPaneScroll).Transform(new Point()), AskButton.RenderSize);
                var cancelBounds = new Rect(CancelButton.TransformToAncestor(TutorPaneScroll).Transform(new Point()), CancelButton.RenderSize);
                checks.Add(new { check = "compact_tutor_input_reachable_" + compactLanguage,
                    passed = new[] { inputBounds, askBounds, cancelBounds }.All(bounds => bounds.Top >= -1 && bounds.Bottom <= TutorPaneScroll.ViewportHeight + 1),
                    viewport = TutorPaneScroll.ViewportHeight, inputBounds, askBounds, cancelBounds });
                AcademyWindow.CaptureWindow(this, Path.Combine(selfTestDirectory!, "academy-compact-input-" + compactLanguage + ".png"));
                TutorPaneScroll.ScrollToTop();
            }
            if (language != "es") Language_Click(this, new RoutedEventArgs());
            Width = 1560; Height = 990;

            if (labReady)
            {
                LearningTabs.SelectedItem = SimulationTab; await Task.Delay(800);
                foreach (var exampleLanguage in new[] { "es", "en" })
                {
                    if (language != exampleLanguage) Language_Click(this, new RoutedEventArgs());
                    foreach (var module in repository.Course.Modules)
                    {
                        SelectModule(module);
                        checks.Add(new { check = "lesson_" + exampleLanguage + "_" + module.Id, passed = ModuleTitle.Text == module.Title.In(exampleLanguage) });
                        foreach (var example in module.Examples)
                        {
                            var input = JsonSerializer.Serialize(new { scene = module.Scene, lang = language, moduleId = module.Id, revision = ++bridgeRevision, parameters = example.Params, preset = example.Preset });
                            var actual = await LabView.ExecuteScriptAsync($"window.AcademyBridge.apply({input})");
                            using var json = JsonDocument.Parse(actual); var root = json.RootElement;
                            checks.Add(new { check = "example_" + exampleLanguage + "_" + module.Id + "_" + example.Id, passed = root.GetProperty("ok").GetBoolean() && root.GetProperty("rejected").GetArrayLength() == 0, actual });
                        }
                    }
                }
                if (language != "es") Language_Click(this, new RoutedEventArgs());
                foreach (var sceneLanguage in new[] { "es", "en" })
                foreach (var scene in new[] { "brownian", "spin-echo", "gradients-b", "attenuation-mixture", "pulse-90", "acquisition-window", "convection", "overlap-joint", "ilt", "dt2", "spen", "time-resolved", "restricted", "exchange", "anisotropy", "prototype-1d", "ultrafast" })
                {
                    var input = JsonSerializer.Serialize(new { scene, lang = sceneLanguage, parameters = new { } });
                    var state = await LabView.ExecuteScriptAsync($"window.AcademyBridge.apply({input})");
                    using var parsedScene = JsonDocument.Parse(state);
                    checks.Add(new { check = "scene_" + scene + "_" + sceneLanguage,
                        passed = parsedScene.RootElement.GetProperty("ok").GetBoolean() && parsedScene.RootElement.GetProperty("rejected").GetArrayLength() == 0, state });
                    if (scene == "spen") { var context = await LabView.ExecuteScriptAsync("window.AcademyBridge.context()"); File.WriteAllText(Path.Combine(selfTestDirectory!, "spen-context-" + sceneLanguage + ".json"), context); }
                }
                await LabView.ExecuteScriptAsync("window.DiffusionMotion.setTime(8)");
                using (var image = File.Create(Path.Combine(selfTestDirectory!, "academy-ultrafast.png"))) await LabView.CoreWebView2.CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Png, image);
                ExpandLab_Click(this, new RoutedEventArgs()); await Task.Delay(500);
                using (var image = File.Create(Path.Combine(selfTestDirectory!, "academy-expanded-lab.png"))) await LabView.CoreWebView2.CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Png, image);
                var expanded = OwnedWindows.Cast<Window>().Single(w => ReferenceEquals(w.Content, LabView)); expanded.Close();
                checks.Add(new { check = "expanded_lab_reattaches", passed = LabHost.Children.Contains(LabView) });
                checks.Add(new { check = "webview_ready", passed = true });
            }
            else checks.Add(new { check = "webview_ready", passed = false });
            var slides = new SourceSlidesWindow(repository, language, 6); slides.Show(); await Task.Delay(350); slides.Capture(Path.Combine(selfTestDirectory!, "academy-source-slides.png")); slides.Close();
            var workshop = new CalibrationWorkshopWindow(language); string? nativeContext = null; workshop.TeachingContextChanged += (_, context) => nativeContext = context; workshop.Show(); workshop.PublishActiveContext(); await Task.Delay(350); workshop.Capture(Path.Combine(selfTestDirectory!, "academy-calibration.png")); workshop.Close();
            using (var context = JsonDocument.Parse(nativeContext ?? "null")) checks.Add(new { check = "native_workshop_context", passed = context.RootElement.ValueKind == JsonValueKind.Object && context.RootElement.GetProperty("calculatedResults").GetProperty("P90FromSelectedNullMicroseconds").GetDouble() == 11 });
            var methods = new MethodsWindow(repository.ContentDirectory, language); methods.Show(); await Task.Delay(350); methods.Capture(Path.Combine(selfTestDirectory!, "academy-methods.png")); methods.Close();
            checks.Add(new { check = "reviewed_mathematical_supplement", passed = derivations is { EquationCoverageCount: 111 }, chapters = derivations?.Chapters.Count, equations = derivations?.EquationCoverageCount, sha256 = derivations?.Sha256 });
            if (derivations is not null)
            {
                var closingReader = new DerivationWindow(derivations, language, academyUserRoot) { Owner = this };
                closingReader.Show();
                closingReader.Close();
                await Task.Delay(250);
                checks.Add(new { check = "mathematical_reader_close_during_startup", passed = closingReader.Ready.IsCompleted });
                Derivations_Click(this, new RoutedEventArgs());
                var reader = derivationWindow!;
                var readerReady = await reader.Ready.WaitAsync(TimeSpan.FromSeconds(35));
                checks.Add(new { check = "offline_mathematical_reader", passed = readerReady, diagnostic = await reader.Diagnostic() });
                if (readerReady)
                {
                    await reader.SelectChapter(derivations.Chapters.First().Id); await Task.Delay(400);
                    var first = await reader.Snapshot();
                    checks.Add(new { check = "mathematical_reader_spanish", passed = first.GetProperty("language").GetString() == "es" && first.GetProperty("coverageCount").GetInt32() == 111 && first.GetProperty("chapters").GetInt32() == derivations.Chapters.Count, state = first });
                    await reader.CaptureReader(Path.Combine(selfTestDirectory!, "academy-derivations-es.png"));
                    await reader.SetLanguage("en"); await reader.SelectChapter(derivations.Chapters.Last().Id); await Task.Delay(400);
                    var last = await reader.Snapshot();
                    checks.Add(new { check = "mathematical_reader_english", passed = last.GetProperty("language").GetString() == "en" && last.GetProperty("chapterId").GetString() == derivations.Chapters.Last().Id, state = last });
                    await reader.CaptureReader(Path.Combine(selfTestDirectory!, "academy-derivations-en.png"));
                    foreach (var readerLanguage in new[] { "es", "en" })
                    {
                        await reader.SetLanguage(readerLanguage);
                        foreach (var chapter in derivations.Chapters)
                        {
                            await reader.SelectChapter(chapter.Id);
                            var chapterState = await reader.Snapshot();
                            checks.Add(new { check = "mathematical_chapter_" + chapter.Id + "_" + readerLanguage,
                                passed = chapterState.GetProperty("ready").GetBoolean() && chapterState.GetProperty("language").GetString() == readerLanguage && chapterState.GetProperty("chapterId").GetString() == chapter.Id,
                                state = chapterState });
                        }
                    }
                    // Restore the parent language before checking the trusted bridge.
                    var tutorChapter = derivations.Find("arbitrary-waveform") ?? derivations.Chapters.First();
                    await reader.SetLanguage(language); await reader.SelectChapter(tutorChapter.Id); await Task.Delay(150);
                    checks.Add(new { check = "mathematical_tutor_context", passed = derivationModuleId == "derivation:" + tutorChapter.Id && simulationContext is null });
                    if (selfTestTutor)
                    {
                        QuestionBox.Text = "¿Por qué aparece q(t) al cuadrado al resolver la ecuación diferencial de Bloch-Torrey, y cuáles son los supuestos?";
                        lastTutorResponse = null; await Ask();
                        checks.Add(new { check = "beatrix_reviewed_math_documentary_wpf", passed = lastTutorResponse is { IsModelAnswer: false, IncludesSupplementalEvidence: true, SupplementalIncludedInTraining: false, Status: "supplemental_documentary_only", GeneratedText: null } && lastTutorResponse.Sources.Any(s => s.Doi is not null), answer = lastTutorResponse });
                        await Task.Delay(200); AcademyWindow.CaptureWindow(this, Path.Combine(selfTestDirectory!, "academy-beatrix-math.png"));
                    }
                }
                reader.Close();
            }
            var closingDoctoral = new DoctoralWindow(language, academyUserRoot) { Owner = this };
            closingDoctoral.Show(); closingDoctoral.Close(); await Task.Delay(200);
            checks.Add(new { check = "doctoral_close_during_startup", passed = closingDoctoral.Ready.IsCompleted });
            Doctoral_Click(this, new RoutedEventArgs());
            var doctoral = doctoralWindow!;
            var doctoralReady = await doctoral.Ready.WaitAsync(TimeSpan.FromSeconds(35));
            checks.Add(new { check = "doctoral_offline_ready", passed = doctoralReady });
            if (doctoralReady)
            {
                await doctoral.Capture(Path.Combine(selfTestDirectory!, "academy-doctoral-home.png"));
                foreach (var activity in new[] { "sync", "sequence", "guided", "campaign", "blind", "inverse", "cases", "advanced", "assessment" })
                {
                    await doctoral.SelectActivity(activity); await Task.Delay(400);
                    var state = await doctoral.Snapshot();
                    var doc = state.GetProperty("doctoral");
                    checks.Add(new { check = "doctoral_activity_" + activity, passed = doc.GetProperty("view").GetString() == activity && doc.GetProperty("activities").GetInt32() == 9 && !doc.GetProperty("hasLLM").GetBoolean() && doc.GetProperty("activity").ValueKind == JsonValueKind.Object, state });
                    await doctoral.Capture(Path.Combine(selfTestDirectory!, "academy-doctoral-" + activity + ".png"));
                }
                await doctoral.SetLanguage("en"); await doctoral.SelectActivity("home");
                var englishDoctoral = await doctoral.Snapshot();
                checks.Add(new { check = "doctoral_english", passed = englishDoctoral.GetProperty("doctoral").GetProperty("language").GetString() == "en" });
                await doctoral.Capture(Path.Combine(selfTestDirectory!, "academy-doctoral-home-en.png"));
                var invalidRejected = false; try { await doctoral.SelectActivity("../private"); } catch (ArgumentException) { invalidRejected = true; }
                checks.Add(new { check = "doctoral_activity_allowlist", passed = invalidRejected });
            }
            doctoral.Close();
            Research_Click(this, new RoutedEventArgs());
            var research = researchWindow!;
            var researchReady = await research.Ready.WaitAsync(TimeSpan.FromSeconds(40));
            checks.Add(new { check = "research_offline_ready", passed = researchReady });
            if (researchReady)
            {
                foreach (var item in new (string stage, string action, string flag)[] { ("calibration", "calibrate", "stage"), ("design", "design", "stage"), ("acquire", "acquire", "hasAcquisition"), ("process", "process", "hasProcessing"), ("inference", "analyze", "hasAnalysis"), ("uncertainty", "uncertainty", "hasUncertainty") })
                {
                    await research.SelectStage(item.stage);
                    await research.EvaluateForQa($"document.querySelector('[data-action={item.action}]').click()"); await Task.Delay(100);
                    var state = (await research.Snapshot()).GetProperty("research");
                    var flag = item.flag == "stage" || state.GetProperty(item.flag).GetBoolean();
                    var noError = await research.EvaluateForQa("document.querySelector('.rs-status[data-error]').dataset.error === 'false'") == "true";
                    checks.Add(new { check = "research_native_workflow_" + item.stage, passed = flag && noError });
                }
                await research.SelectStage("spatial"); await research.EvaluateForQa("document.querySelector('[data-action=spatial]').click()");
                for (var attempt = 0; attempt < 100; attempt++) { if ((await research.Snapshot()).GetProperty("research").GetProperty("spatialCalculated").GetBoolean()) break; await Task.Delay(100); }
                checks.Add(new { check = "research_native_spatial_worker", passed = (await research.Snapshot()).GetProperty("research").GetProperty("spatialCalculated").GetBoolean() });
                await research.SelectStage("library"); await research.EvaluateForQa("document.querySelector('[data-load-public]').click()");
                var publicLoaded = false; for (var attempt = 0; attempt < 100; attempt++) { publicLoaded = await research.EvaluateForQa("Boolean(document.querySelector('[data-field=public-phase0]'))") == "true"; if (publicLoaded) break; await Task.Delay(100); }
                checks.Add(new { check = "research_native_public_sha_and_fid", passed = publicLoaded });
                if (publicLoaded)
                {
                    await research.EvaluateForQa("document.querySelector('[data-action=process-public]').click()"); await Task.Delay(150);
                    var state = (await research.Snapshot()).GetProperty("research");
                    checks.Add(new { check = "research_native_public_processing_and_missing_b", passed = state.GetProperty("publicProcessedRows").GetInt32() > 0 && state.GetProperty("publicFitBlocked").GetBoolean() });
                }
                foreach (var researchLanguage in new[] { "es", "en" })
                {
                    await research.SetLanguage(researchLanguage);
                    foreach (var stage in new[] { "brief", "calibration", "design", "acquire", "process", "inference", "uncertainty", "next", "spatial", "competencies", "defence", "library" })
                    {
                        await research.SelectStage(stage); await Task.Delay(80);
                        var state = await research.Snapshot(); var studio = state.GetProperty("research");
                        checks.Add(new { check = "research_" + researchLanguage + "_" + stage, passed = studio.GetProperty("view").GetString() == stage && studio.GetProperty("language").GetString() == researchLanguage && studio.GetProperty("publicCases").GetInt32() == 8 });
                        if (stage is "brief" or "calibration" or "spatial" or "library") await research.Capture(Path.Combine(selfTestDirectory!, "academy-research-" + researchLanguage + "-" + stage + ".png"));
                    }
                }
                if (selfTestTutor)
                {
                    foreach (var tutorLanguage in new[] { "es", "en" })
                    {
                        await research.SetLanguage(tutorLanguage); await research.SelectStage("uncertainty");
                        var caseBeforeTutor = await research.EvaluateForQa("AcademyLearningPath.sha256(AcademyWeb.researchEvidence().case)");
                        var question = tutorLanguage == "es"
                            ? "¿Por qué la incertidumbre de escala del gradiente se comparte entre toda la rampa? Explica el mecanismo, un supuesto y un control."
                            : "Why is gradient scale uncertainty shared across the entire ramp? Explain the mechanism, one assumption and one control.";
                        var questionJson = JsonSerializer.Serialize(question);
                        await research.EvaluateForQa("document.querySelector('[data-field=prediction]').value='A shared calibration error should remain after independent repeats; compare a separate standard.';document.querySelector('[data-field=question]').value=" + questionJson + ";document.querySelector('[data-action=native-tutor]').click()");
                        var modelReply = false; JsonElement tutorStudio = default;
                        for (var attempt = 0; attempt < 1200; attempt++)
                        {
                            tutorStudio = (await research.Snapshot()).GetProperty("research");
                            if (!tutorStudio.GetProperty("nativeTutor").GetProperty("pending").GetBoolean())
                            {
                                modelReply = tutorStudio.GetProperty("beatrixMode").GetString() == "local-model-with-reviewed-evidence"; break;
                            }
                            await Task.Delay(150);
                        }
                        var caseAfterTutor = await research.EvaluateForQa("AcademyLearningPath.sha256(AcademyWeb.researchEvidence().case)");
                        var retainedTutorAnswer = await research.EvaluateForQa("JSON.stringify({text:document.querySelector('[data-tutor-answer]')?.innerText||'',sources:[...document.querySelectorAll('[data-tutor-answer] a')].map(a=>({text:a.innerText,href:a.getAttribute('href')}))})");
                        checks.Add(new { check = "research_beatrix_native_bridge_" + tutorLanguage, passed = modelReply && caseBeforeTutor == caseAfterTutor, nativeState = tutorStudio, unchangedCase = caseBeforeTutor == caseAfterTutor, retainedTutorAnswer });
                        await research.EvaluateForQa("document.querySelector('[data-tutor-answer]').scrollIntoView({block:'center'})");
                        await research.Capture(Path.Combine(selfTestDirectory!, "academy-research-beatrix-" + tutorLanguage + ".png"));
                    }
                }
                var invalidStageRejected = false; try { await research.SelectStage("../private"); } catch (ArgumentException) { invalidStageRejected = true; }
                checks.Add(new { check = "research_stage_allowlist", passed = invalidStageRejected });
            }
            research.Close();
            if (selfTestTutor)
            {
                Width = 1560; Height = 990;
                RefreshNavigation("pulse-calibration");
                QuestionBox.Text = "El primer nulo de 180 grados aparece a 18 microsegundos. ¿Qué p1 de 90 grados debo usar y qué compruebo después?";
                lastTutorResponse = null;
                await Ask();
                checks.Add(new { check = "beatrix_native_wpf", passed = lastTutorResponse is { IsModelAnswer: true } && lastTutorResponse.Sources.Count > 0 && lastTutorResponse.Text.Contains('9'), answer = lastTutorResponse });
                await Task.Delay(350);
                AcademyWindow.CaptureWindow(this, Path.Combine(selfTestDirectory!, "academy-beatrix.png"));
            }
            File.WriteAllText(Path.Combine(selfTestDirectory!, "ui-self-test.json"), JsonSerializer.Serialize(new { applicationVersion = typeof(MainWindow).Assembly.GetName().Version!.ToString(3), softwareQaOnly = true, courseSha256 = repository.Sha256, supplementalSha256 = derivations?.Sha256, checks }, CourseRepository.Json));
            selfTestPassed = checks.All(item => JsonSerializer.SerializeToElement(item).GetProperty("passed").GetBoolean());
        }
        catch (Exception e) { File.WriteAllText(Path.Combine(selfTestDirectory!, "ui-self-test-error.txt"), e.ToString()); }
        finally { System.Windows.Application.Current.Shutdown(selfTestPassed ? 0 : 1); }
    }
}
