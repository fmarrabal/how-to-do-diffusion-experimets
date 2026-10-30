using System.Diagnostics;
using System.IO;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using DiffAtOnce.Academy.Tutor;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.Wpf;

namespace DiffAtOnce.Academy.App;

/// <summary>Same research UI and calculations as the browser, with an explicitly
/// requested, local read-only tutor. Browser messages cannot execute commands.</summary>
public sealed class ResearchWindow : Window
{
    const string Host = "research.academy.diffatonce.local";
    static readonly HashSet<string> Stages = new(StringComparer.Ordinal)
    { "brief", "calibration", "design", "acquire", "process", "inference", "uncertainty", "next", "spatial", "competencies", "defence", "library" };
    readonly WebView2 view = new();
    readonly TextBlock status = MainWindow.Text("", 12);
    readonly Button manual = new() { Padding = new Thickness(14, 7, 14, 7), Margin = new Thickness(12, 6, 12, 6) };
    readonly Button cancel = new() { Padding = new Thickness(14, 7, 14, 7), Margin = new Thickness(12, 6, 12, 6), IsEnabled = false };
    readonly string userRoot;
    readonly ResearchTutorService tutor;
    readonly bool testing;
    readonly TaskCompletionSource<bool> ready = new(TaskCreationOptions.RunContinuationsAsynchronously);
    CancellationTokenSource? request;
    string? activeRequestId, activeScopeHash;
    string language;
    bool closed, initializing;
    public Task<bool> Ready => ready.Task;

    public ResearchWindow(string language, string userRoot, bool testing = false)
    {
        this.language = language == "en" ? "en" : "es"; this.userRoot = userRoot; this.testing = testing;
        tutor = new ResearchTutorService(Path.Combine(AppContext.BaseDirectory, "Content", "research-tutor-knowledge.json"), Path.Combine(AppContext.BaseDirectory, "Models", "Beatrix"));
        Width = Math.Min(1510, SystemParameters.WorkArea.Width); Height = Math.Min(1000, SystemParameters.WorkArea.Height);
        MinWidth = Math.Min(800, SystemParameters.WorkArea.Width); MinHeight = Math.Min(660, SystemParameters.WorkArea.Height);
        WindowStartupLocation = WindowStartupLocation.CenterOwner;
        var root = new DockPanel(); var tools = new WrapPanel(); tools.Children.Add(manual); tools.Children.Add(cancel);
        manual.Click += (_, _) => { var file = Path.Combine(AppContext.BaseDirectory, "Docs", language == "en" ? "ACADEMY_MANUAL_EN.pdf" : "ACADEMY_MANUAL_ES.pdf"); if (File.Exists(file)) Process.Start(new ProcessStartInfo(file) { UseShellExecute = true }); };
        cancel.Click += (_, _) => request?.Cancel();
        status.Margin = new Thickness(15, 7, 15, 7); DockPanel.SetDock(tools, Dock.Top); DockPanel.SetDock(status, Dock.Bottom);
        root.Children.Add(tools); root.Children.Add(status); root.Children.Add(view); Content = root; Labels();
        view.Loaded += async (_, _) => await Initialize();
        Closed += async (_, _) => { closed = true; request?.Cancel(); ready.TrySetResult(false); view.Dispose(); await tutor.DisposeAsync(); };
    }
    void Labels()
    {
        Title = "DiffAtOnce Academy 1.3 · " + (language == "en" ? "Research studio" : "Investigación continua");
        manual.Content = language == "en" ? "Complete manual (PDF)" : "Manual completo (PDF)";
        cancel.Content = language == "en" ? "Cancel local tutor" : "Cancelar tutor local";
        status.Text = language == "en" ? "Offline research · shared numerical engine · local evidence and human review" : "Investigación sin conexión · motor numérico compartido · evidencias locales y revisión humana";
    }
    static bool Local(string uri) => Uri.TryCreate(uri, UriKind.Absolute, out var u) && u.Scheme == "https" && u.Host == Host;
    static void Reference(string uri) { if (Uri.TryCreate(uri, UriKind.Absolute, out var u) && u.Scheme == "https" && string.IsNullOrEmpty(u.UserInfo)) Process.Start(new ProcessStartInfo(u.AbsoluteUri) { UseShellExecute = true }); }
    async Task Initialize()
    {
        if (closed || initializing) return; initializing = true;
        try
        {
            var environment = await CoreWebView2Environment.CreateAsync(null, Path.Combine(userRoot, "ResearchWebView")).WaitAsync(TimeSpan.FromSeconds(20));
            if (closed) return;
            await view.EnsureCoreWebView2Async(environment).WaitAsync(TimeSpan.FromSeconds(20)); if (closed) return;
            var web = view.CoreWebView2;
            web.SetVirtualHostNameToFolderMapping(Host, Path.Combine(AppContext.BaseDirectory, "Web"), CoreWebView2HostResourceAccessKind.DenyCors);
            web.Settings.IsWebMessageEnabled = true; web.Settings.AreDevToolsEnabled = false; web.Settings.AreDefaultContextMenusEnabled = false;
            web.PermissionRequested += (_, e) => e.State = CoreWebView2PermissionState.Deny;
            web.NavigationStarting += (_, e) => { if (!Local(e.Uri)) { e.Cancel = true; if (e.IsUserInitiated) Reference(e.Uri); } };
            web.NewWindowRequested += (_, e) => { e.Handled = true; if (e.IsUserInitiated) Reference(e.Uri); };
            web.WebResourceRequested += (_, e) => { if (!Local(e.Request.Uri) && !e.Request.Uri.StartsWith("data:", StringComparison.Ordinal) && !e.Request.Uri.StartsWith("blob:", StringComparison.Ordinal)) e.Response = web.Environment.CreateWebResourceResponse(new MemoryStream(), 403, "Offline research only", "Content-Type: text/plain"); };
            web.AddWebResourceRequestedFilter("*", CoreWebView2WebResourceContext.All);
            web.WebMessageReceived += async (_, e) => await TutorMessage(e);
            web.NavigationCompleted += async (_, e) =>
            {
                if (closed) return;
                try { if (!e.IsSuccess) throw new InvalidOperationException("Research page navigation failed."); await WaitReady(); if (!closed) ready.TrySetResult(true); }
                catch (Exception error) when (error is TimeoutException or InvalidOperationException or System.Runtime.InteropServices.COMException) { if (!closed) status.Text = error.Message; ready.TrySetResult(false); }
            };
            web.Navigate($"https://{Host}/index.html?view=research&embedded=1&lang={language}");
        }
        catch (Exception error) when (error is WebView2RuntimeNotFoundException or IOException or InvalidOperationException or TimeoutException or System.Runtime.InteropServices.COMException) { if (!closed) status.Text = error.Message; ready.TrySetResult(false); }
    }
    async Task TutorMessage(CoreWebView2WebMessageReceivedEventArgs e)
    {
        if (closed || !Local(e.Source) || e.WebMessageAsJson.Length > 64000) return;
        string? requestId = null, scopeHash = null;
        JsonElement? scope = null;
        var requestLanguage = language;
        CancellationTokenSource? ownRequest = null;
        try
        {
            using var document = JsonDocument.Parse(e.WebMessageAsJson); var message = document.RootElement;
            var type = message.GetProperty("type").GetString();
            if (type is not ("research-tutor" or "research-tutor-cancel")) return;
            requestId = message.GetProperty("requestId").GetString();
            scopeHash = message.GetProperty("scopeHash").GetString();
            if (!ValidRequestId(requestId) || !ValidScopeHash(scopeHash)) return;
            if (type == "research-tutor-cancel")
            {
                if (requestId == activeRequestId && scopeHash == activeScopeHash) request?.Cancel();
                return;
            }
            requestLanguage = message.GetProperty("language").GetString() == "en" ? "en" : "es";
            scope = message.GetProperty("scope").Clone();
            if (scope.Value.ValueKind != JsonValueKind.Object || scope.Value.GetRawText().Length > 16000)
            {
                await Reply(requestId!, scopeHash!, scope, requestLanguage, "invalid-request"); return;
            }
            if (request is not null)
            {
                // Retransmitting one ID is idempotent. A different request gets
                // an explicit busy reply instead of leaving the page pending.
                if (requestId != activeRequestId || scopeHash != activeScopeHash)
                    await Reply(requestId!, scopeHash!, scope, requestLanguage, "busy");
                return;
            }
            var question = message.GetProperty("question").GetString() ?? ""; var topic = message.GetProperty("topic").GetString() ?? "journey";
            if (string.IsNullOrWhiteSpace(question) || question.Length > 2000 || topic.Length > 80)
            {
                await Reply(requestId!, scopeHash!, scope, requestLanguage, "invalid-request"); return;
            }
            var level = message.TryGetProperty("level", out var levelValue) ? Math.Clamp(levelValue.GetInt32(), 0, 2) : 2;
            ownRequest = new CancellationTokenSource(); request = ownRequest;
            activeRequestId = requestId; activeScopeHash = scopeHash; cancel.IsEnabled = true;
            var progress = new Progress<string>(text => { if (!closed && ReferenceEquals(request, ownRequest) && !ownRequest.IsCancellationRequested) status.Text = text; });
            var answer = await tutor.AskAsync(requestLanguage, question, topic, message.GetProperty("context").GetRawText(), ownRequest.Token, progress, Math.Max(2, level));
            ownRequest.Token.ThrowIfCancellationRequested();
            if (!closed) { await Reply(requestId!, scopeHash!, scope, requestLanguage, answer.Status, answer); status.Text = answer.EngineLabel; }
        }
        catch (OperationCanceledException)
        {
            if (!closed)
            {
                status.Text = language == "en" ? "Local tutor cancelled." : "Tutor local cancelado.";
                if (ValidRequestId(requestId) && ValidScopeHash(scopeHash)) await Reply(requestId!, scopeHash!, scope, requestLanguage, "cancelled");
            }
        }
        catch (Exception error) when (error is JsonException or KeyNotFoundException or InvalidOperationException or ArgumentException or IOException or System.Runtime.InteropServices.COMException)
        {
            if (!closed)
            {
                status.Text = error.Message;
                if (ValidRequestId(requestId) && ValidScopeHash(scopeHash)) await Reply(requestId!, scopeHash!, scope, requestLanguage, "error", detail: error.Message);
            }
        }
        finally
        {
            if (ownRequest is not null)
            {
                if (ReferenceEquals(request, ownRequest)) { request = null; activeRequestId = null; activeScopeHash = null; if (!closed) cancel.IsEnabled = false; }
                ownRequest.Dispose();
            }
        }
    }
    static bool ValidRequestId(string? id) => id is { Length: >= 8 and <= 100 } && id.All(c => char.IsAsciiLetterOrDigit(c) || c is '-' or '_' or '.' or ':');
    static bool ValidScopeHash(string? hash) => hash is { Length: 64 } && hash.All(c => c is >= '0' and <= '9' or >= 'a' and <= 'f');
    async Task Reply(string requestId, string scopeHash, JsonElement? scope, string lang, string resultStatus, TutorAnswer? answer = null, string? detail = null)
    {
        if (closed || view.CoreWebView2 is null) return;
        var isModelAnswer = answer?.IsModelAnswer == true;
        var fallback = resultStatus switch
        {
            "cancelled" => lang == "en" ? "Local tutor cancelled." : "Tutor local cancelado.",
            "busy" => lang == "en" ? "The local tutor is finishing another request. Try again." : "El tutor local está terminando otra consulta. Vuelve a intentarlo.",
            "invalid-request" => lang == "en" ? "The local tutor request is incomplete or exceeds its limit." : "La consulta del tutor local está incompleta o supera su límite.",
            _ => lang == "en" ? "The local tutor could not complete this request." : "El tutor local no pudo completar esta consulta."
        };
        object[] sources = answer is null ? Array.Empty<object>() : answer.Sources.Take(20).Select(source => (object)new
        {
            id = source.Id, title = source.Title, doi = source.Doi, url = source.Url,
            pages = source.Pages, equations = source.Equations, slide = source.Slide
        }).ToArray();
        var json = JsonSerializer.Serialize(new
        {
            requestId, scopeHash, scope, label = answer?.EngineLabel ?? fallback,
            text = answer?.Text ?? (detail is { Length: > 2000 } ? detail[..2000] : detail ?? fallback),
            sources, isModelAnswer,
            mode = isModelAnswer ? "local-model-with-reviewed-evidence" : "reviewed-source-guidance",
            status = resultStatus
        });
        try { await view.ExecuteScriptAsync("window.AcademyWeb?.receiveResearchTutor?.(" + json + ")"); }
        catch (Exception error) when (error is InvalidOperationException or System.Runtime.InteropServices.COMException) { if (!closed) status.Text = error.Message; }
    }
    async Task WaitReady()
    {
        for (var attempt = 0; attempt < 200; attempt++) { if (closed) return; if (await view.ExecuteScriptAsync("Boolean(window.AcademyWeb?.snapshot().research?.ready)") == "true") return; await Task.Delay(125); }
        throw new TimeoutException("Research sources and interface did not finish loading.");
    }
    public async Task SetLanguage(string value) { if (closed) return; if (value is not ("es" or "en")) throw new ArgumentException("ES/EN"); language = value; Labels(); if (view.CoreWebView2 is not null) await view.ExecuteScriptAsync($"window.AcademyWeb?.setLanguage({JsonSerializer.Serialize(value)})"); }
    public async Task SelectStage(string id) { if (closed) return; if (!Stages.Contains(id)) throw new ArgumentException("Research stage"); await view.ExecuteScriptAsync($"window.AcademyWeb.selectResearchView({JsonSerializer.Serialize(id)})"); }
    public async Task<JsonElement> Snapshot() { if (closed) throw new InvalidOperationException("Research closed"); using var json = JsonDocument.Parse(await view.ExecuteScriptAsync("window.AcademyWeb.snapshot()")); return json.RootElement.Clone(); }
    internal Task<string> EvaluateForQa(string script) { if (!testing || closed) throw new InvalidOperationException("Research instrumentation requires the explicit self-test launch."); return view.ExecuteScriptAsync(script); }
    public async Task Capture(string path) { if (closed) return; using var file = File.Create(path); await view.CoreWebView2.CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Png, file); }
}
