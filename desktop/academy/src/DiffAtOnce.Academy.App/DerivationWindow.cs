using System.Diagnostics;
using System.IO;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using DiffAtOnce.Academy.Core;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.Wpf;

namespace DiffAtOnce.Academy.App;

/// <summary>Offline mathematical reader shared with the browser edition. Only
/// allowlisted chapter identifiers can change the local tutor's context.</summary>
public sealed class DerivationWindow : Window
{
    const string Host = "papers.academy.diffatonce.local";
    readonly WebView2 view = new();
    readonly TextBlock status = MainWindow.Text("", 12);
    readonly DerivationCatalogue catalogue;
    readonly string userRoot;
    string language;
    bool closed;
    readonly TaskCompletionSource<bool> ready = new(TaskCreationOptions.RunContinuationsAsynchronously);
    public Task<bool> Ready => ready.Task;
    public event Action<string, string, bool>? ChapterSelected;

    public DerivationWindow(DerivationCatalogue catalogue, string language, string userRoot)
    {
        this.catalogue = catalogue; this.language = language; this.userRoot = userRoot;
        Title = "DiffAtOnce Academy · " + (language == "en" ? "Derive the equations" : "Derivar las ecuaciones");
        Width = Math.Min(1400, SystemParameters.WorkArea.Width); Height = Math.Min(960, SystemParameters.WorkArea.Height);
        MinWidth = Math.Min(800, SystemParameters.WorkArea.Width); MinHeight = Math.Min(650, SystemParameters.WorkArea.Height);
        WindowStartupLocation = WindowStartupLocation.CenterOwner;
        var root = new DockPanel();
        status.Text = language == "en" ? "Preparing the reviewed mathematical course…" : "Preparando el recorrido matemático revisado…";
        status.Margin = new Thickness(16, 8, 16, 8); DockPanel.SetDock(status, Dock.Bottom); root.Children.Add(status);
        root.Children.Add(view); Content = root;
        view.Loaded += async (_, _) => await Initialize();
        Closed += (_, _) => { closed = true; ready.TrySetResult(false); view.Dispose(); };
    }
    static bool Local(string uri) => Uri.TryCreate(uri, UriKind.Absolute, out var parsed) && parsed.Scheme == "https" && parsed.Host == Host;
    static void OpenReference(string uri)
    {
        if (Uri.TryCreate(uri, UriKind.Absolute, out var parsed) && parsed.Scheme == "https")
            Process.Start(new ProcessStartInfo(parsed.AbsoluteUri) { UseShellExecute = true });
    }
    async Task Initialize()
    {
        if (view.CoreWebView2 is not null) return;
        try
        {
            var environment = await CoreWebView2Environment.CreateAsync(null, Path.Combine(userRoot, "PapersWebView")).WaitAsync(TimeSpan.FromSeconds(20));
            if (closed) return;
            await view.EnsureCoreWebView2Async(environment).WaitAsync(TimeSpan.FromSeconds(20));
            if (closed) return;
            var web = view.CoreWebView2 ?? throw new InvalidOperationException("WebView2 did not initialize.");
            web.SetVirtualHostNameToFolderMapping(Host, Path.Combine(AppContext.BaseDirectory, "Web"), CoreWebView2HostResourceAccessKind.DenyCors);
            web.Settings.IsWebMessageEnabled = true; web.Settings.AreDevToolsEnabled = false; web.Settings.AreDefaultContextMenusEnabled = false;
            web.PermissionRequested += (_, e) => e.State = CoreWebView2PermissionState.Deny;
            web.NavigationStarting += (_, e) => { if (!Local(e.Uri)) { e.Cancel = true; if (e.IsUserInitiated) OpenReference(e.Uri); } };
            web.NewWindowRequested += (_, e) => { e.Handled = true; if (e.IsUserInitiated) OpenReference(e.Uri); };
            web.WebResourceRequested += (_, e) =>
            {
                if (!Local(e.Request.Uri) && !e.Request.Uri.StartsWith("data:") && !e.Request.Uri.StartsWith("blob:"))
                    e.Response = web.Environment.CreateWebResourceResponse(new MemoryStream(), 403, "Offline course only", "Content-Type: text/plain");
            };
            web.AddWebResourceRequestedFilter("*", CoreWebView2WebResourceContext.All);
            web.WebMessageReceived += (_, e) =>
            {
                if (!Local(e.Source) || e.WebMessageAsJson.Length > 4000) return;
                try
                {
                    using var message = JsonDocument.Parse(e.WebMessageAsJson);
                    var data = message.RootElement;
                    if (data.GetProperty("type").GetString() != "academy-derivation") return;
                    var chapter = catalogue.Find(data.GetProperty("chapterId").GetString() ?? "");
                    if (chapter is null || data.GetProperty("language").GetString() != language) return;
                    if (data.GetProperty("contentSha256").GetString() != catalogue.Sha256 || data.GetProperty("version").GetString() != catalogue.Version) return;
                    var ask = data.TryGetProperty("askBeatrix", out var askValue) && askValue.ValueKind == JsonValueKind.True;
                    ChapterSelected?.Invoke(chapter.Id, chapter.Title.In(language), ask);
                }
                catch (Exception error) when (error is JsonException or KeyNotFoundException or InvalidOperationException) { }
            };
            web.NavigationCompleted += async (_, e) =>
            {
                try
                {
                    if (closed) return;
                    if (!e.IsSuccess) { status.Text = language == "en" ? "The mathematical reader could not be loaded." : "No se ha podido cargar el recorrido matemático."; ready.TrySetResult(false); return; }
                    for (var i = 0; i < 160; i++)
                    {
                        if (closed) return;
                        var state = await view.ExecuteScriptAsync("Boolean(window.AcademyWeb && window.AcademyWeb.snapshot().ready)");
                        if (closed) return;
                        if (state == "true")
                        {
                            status.Text = language == "en" ? "Reviewed derivations · select a chapter to ask Beatrix in the main window." : "Derivaciones revisadas · selecciona un capítulo para preguntar a Beatrix en la ventana principal.";
                            ready.TrySetResult(true); return;
                        }
                        await Task.Delay(150);
                    }
                    status.Text = language == "en" ? "Mathematical typesetting did not finish." : "La composición de las ecuaciones no ha terminado.";
                    ready.TrySetResult(false);
                }
                catch (Exception error) when (error is InvalidOperationException or System.Runtime.InteropServices.COMException)
                {
                    if (!closed) status.Text = (language == "en" ? "Mathematical reader unavailable: " : "Recorrido matemático no disponible: ") + error.Message;
                    ready.TrySetResult(false);
                }
            };
            web.Navigate($"https://{Host}/index.html?view=derivations&embedded=1&lang={language}");
        }
        catch (Exception error) when (error is WebView2RuntimeNotFoundException or IOException or InvalidOperationException or TimeoutException or System.Runtime.InteropServices.COMException)
        { status.Text = (language == "en" ? "Mathematical reader unavailable: " : "Recorrido matemático no disponible: ") + error.Message; ready.TrySetResult(false); }
    }
    public async Task SetLanguage(string value)
    {
        if (closed) return;
        language = value == "en" ? "en" : "es";
        Title = "DiffAtOnce Academy · " + (language == "en" ? "Derive the equations" : "Derivar las ecuaciones");
        status.Text = language == "en" ? "Reviewed derivations · select a chapter to ask Beatrix in the main window." : "Derivaciones revisadas · selecciona un capítulo para preguntar a Beatrix en la ventana principal.";
        try
        {
            if (view.CoreWebView2 is not null) { await view.ExecuteScriptAsync($"window.AcademyWeb.setLanguage({JsonSerializer.Serialize(language)})"); await WaitForMath(); }
        }
        catch (Exception error) when (error is InvalidOperationException or TimeoutException or System.Runtime.InteropServices.COMException)
        {
            if (!closed) status.Text = (language == "en" ? "Mathematical reader unavailable: " : "Recorrido matemático no disponible: ") + error.Message;
        }
    }
    public async Task SelectChapter(string id)
    {
        if (catalogue.Find(id) is null) throw new ArgumentException("Unknown mathematical chapter.");
        await view.ExecuteScriptAsync($"window.AcademyWeb.selectChapter({JsonSerializer.Serialize(id)})");
        await WaitForMath();
    }
    async Task WaitForMath()
    {
        for (var attempt = 0; attempt < 100; attempt++)
        {
            if (closed) return;
            if (await view.ExecuteScriptAsync("Boolean(window.AcademyWeb && window.AcademyWeb.snapshot().ready)") == "true") return;
            await Task.Delay(100);
        }
        throw new TimeoutException("Mathematical typesetting did not finish.");
    }
    public async Task<JsonElement> Snapshot()
    {
        var json = await view.ExecuteScriptAsync("window.AcademyWeb.snapshot()");
        using var parsed = JsonDocument.Parse(json); return parsed.RootElement.Clone();
    }
    public async Task<JsonElement> Diagnostic()
    {
        var json = await view.ExecuteScriptAsync("({snapshot:window.AcademyWeb?.snapshot()||null,mathjax:typeof window.MathJax?.typesetPromise,documentReady:document.readyState,text:document.body.innerText.slice(-800)})");
        using var parsed = JsonDocument.Parse(json);
        return JsonSerializer.SerializeToElement(new { status = status.Text, page = parsed.RootElement.Clone() });
    }
    public async Task CaptureReader(string path)
    {
        using var image = File.Create(path); await view.CoreWebView2.CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Png, image);
    }
}
