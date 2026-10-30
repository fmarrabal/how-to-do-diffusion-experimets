using System.Diagnostics;
using System.IO;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using DiffAtOnce.Academy.Core;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.Wpf;

namespace DiffAtOnce.Academy.App;

/// <summary>Offline doctoral activities shared with the browser. New hints are
/// reviewed documents, independent of the existing locally trained model.</summary>
public sealed class DoctoralWindow : Window
{
    const string Host = "doctoral.academy.diffatonce.local";
    static readonly HashSet<string> Activities = new(StringComparer.Ordinal)
        { "home", "sync", "sequence", "guided", "campaign", "blind", "inverse", "cases", "advanced", "assessment" };
    readonly WebView2 view = new();
    readonly TextBlock status = MainWindow.Text("", 12);
    readonly Button manual = new() { Padding = new Thickness(14, 7, 14, 7), Margin = new Thickness(12, 6, 12, 6) };
    readonly string userRoot;
    string language;
    bool closed, initializing;
    readonly TaskCompletionSource<bool> ready = new(TaskCreationOptions.RunContinuationsAsynchronously);
    public Task<bool> Ready => ready.Task;

    public DoctoralWindow(string language, string userRoot)
    {
        this.language = language == "en" ? "en" : "es"; this.userRoot = userRoot;
        Width = Math.Min(1450, SystemParameters.WorkArea.Width); Height = Math.Min(980, SystemParameters.WorkArea.Height);
        MinWidth = Math.Min(820, SystemParameters.WorkArea.Width); MinHeight = Math.Min(680, SystemParameters.WorkArea.Height);
        WindowStartupLocation = WindowStartupLocation.CenterOwner;
        UpdateLabels();
        var root = new DockPanel(); status.Margin = new Thickness(16, 8, 16, 8);
        manual.Click += (_, _) => { var path = Path.Combine(AppContext.BaseDirectory, "Docs", language == "en" ? "ACADEMY_MANUAL_EN.pdf" : "ACADEMY_MANUAL_ES.pdf"); if (File.Exists(path)) Process.Start(new ProcessStartInfo(path) { UseShellExecute = true }); };
        DockPanel.SetDock(manual, Dock.Top); root.Children.Add(manual);
        DockPanel.SetDock(status, Dock.Bottom); root.Children.Add(status); root.Children.Add(view); Content = root;
        view.Loaded += async (_, _) => await Initialize();
        Closed += (_, _) => { closed = true; ready.TrySetResult(false); view.Dispose(); };
    }
    void UpdateLabels()
    {
        Title = "DiffAtOnce Academy · " + (language == "en" ? "Doctoral laboratory" : "Laboratorio doctoral");
        manual.Content = language == "en" ? "Doctoral manual (PDF)" : "Manual doctoral (PDF)";
        status.Text = language == "en" ? "Offline activities · reviewed Beatrix hints without LLM generation · local evidence" : "Actividades sin conexión · pistas revisadas de Beatrix sin generación LLM · evidencias locales";
    }
    static bool Local(string uri) => Uri.TryCreate(uri, UriKind.Absolute, out var u) && u.Scheme == "https" && u.Host == Host;
    static void Reference(string uri)
    {
        if (Uri.TryCreate(uri, UriKind.Absolute, out var u) && u.Scheme == "https" && string.IsNullOrEmpty(u.UserInfo))
            Process.Start(new ProcessStartInfo(u.AbsoluteUri) { UseShellExecute = true });
    }
    async Task Initialize()
    {
        if (initializing || closed) return; initializing = true;
        try
        {
            var environment = await CoreWebView2Environment.CreateAsync(null, Path.Combine(userRoot, "DoctoralWebView")).WaitAsync(TimeSpan.FromSeconds(20));
            if (closed) return;
            await view.EnsureCoreWebView2Async(environment).WaitAsync(TimeSpan.FromSeconds(20));
            if (closed) return;
            var web = view.CoreWebView2 ?? throw new InvalidOperationException("WebView2 did not initialize.");
            web.SetVirtualHostNameToFolderMapping(Host, Path.Combine(AppContext.BaseDirectory, "Web"), CoreWebView2HostResourceAccessKind.DenyCors);
            web.Settings.IsWebMessageEnabled = false; web.Settings.AreDevToolsEnabled = false; web.Settings.AreDefaultContextMenusEnabled = false;
            web.PermissionRequested += (_, e) => e.State = CoreWebView2PermissionState.Deny;
            web.NavigationStarting += (_, e) => { if (!Local(e.Uri)) { e.Cancel = true; if (e.IsUserInitiated) Reference(e.Uri); } };
            web.NewWindowRequested += (_, e) => { e.Handled = true; if (e.IsUserInitiated) Reference(e.Uri); };
            web.WebResourceRequested += (_, e) =>
            {
                if (!Local(e.Request.Uri) && !e.Request.Uri.StartsWith("data:", StringComparison.Ordinal) && !e.Request.Uri.StartsWith("blob:", StringComparison.Ordinal))
                    e.Response = web.Environment.CreateWebResourceResponse(new MemoryStream(), 403, "Offline doctoral activities only", "Content-Type: text/plain");
            };
            web.AddWebResourceRequestedFilter("*", CoreWebView2WebResourceContext.All);
            web.NavigationCompleted += async (_, e) =>
            {
                if (closed) return;
                try
                {
                    if (!e.IsSuccess) { ready.TrySetResult(false); status.Text = language == "en" ? "The doctoral activities could not load." : "No se pudieron cargar las actividades doctorales."; return; }
                    await WaitReady();
                    if (!closed) { await view.ExecuteScriptAsync($"window.AcademyWeb.setLanguage({JsonSerializer.Serialize(language)})"); ready.TrySetResult(true); }
                }
                catch (Exception error) when (error is TimeoutException or InvalidOperationException or System.Runtime.InteropServices.COMException)
                { if (!closed) status.Text = (language == "en" ? "Doctoral activities unavailable: " : "Actividades doctorales no disponibles: ") + error.Message; ready.TrySetResult(false); }
            };
            web.Navigate($"https://{Host}/index.html?view=doctoral&embedded=1&tutorBridge=0&lang={language}");
        }
        catch (Exception error) when (error is WebView2RuntimeNotFoundException or IOException or InvalidOperationException or TimeoutException or System.Runtime.InteropServices.COMException)
        { if (!closed) status.Text = (language == "en" ? "Doctoral activities unavailable: " : "Actividades doctorales no disponibles: ") + error.Message; ready.TrySetResult(false); }
    }
    async Task WaitReady()
    {
        for (var attempt = 0; attempt < 160; attempt++)
        {
            if (closed) return;
            if (await view.ExecuteScriptAsync("Boolean(window.AcademyWeb?.snapshot().ready && window.AcademyWeb.snapshot().doctoral)") == "true") return;
            await Task.Delay(125);
        }
        throw new TimeoutException("Doctoral activities did not finish loading.");
    }
    public async Task SetLanguage(string value)
    {
        if (closed) return;
        if (value is not ("es" or "en")) throw new ArgumentException("ES/EN only.");
        language = value; UpdateLabels();
        try
        {
            if (view.CoreWebView2 is not null) await view.ExecuteScriptAsync($"window.AcademyWeb?.setLanguage({JsonSerializer.Serialize(value)})");
        }
        catch (Exception error) when (error is InvalidOperationException or System.Runtime.InteropServices.COMException)
        { if (!closed) status.Text = (language == "en" ? "Doctoral activities unavailable: " : "Actividades doctorales no disponibles: ") + error.Message; }
    }
    public async Task SelectActivity(string id)
    {
        if (closed) return;
        if (!Activities.Contains(id)) throw new ArgumentException("Unknown doctoral activity.");
        await view.ExecuteScriptAsync($"window.AcademyWeb.selectDoctoralView({JsonSerializer.Serialize(id)})");
    }
    public async Task<JsonElement> Snapshot()
    {
        if (closed) throw new InvalidOperationException("Doctoral window closed.");
        using var json = JsonDocument.Parse(await view.ExecuteScriptAsync("window.AcademyWeb.snapshot()")); return json.RootElement.Clone();
    }
    public async Task Capture(string path)
    {
        if (closed) return;
        using var file = File.Create(path); await view.CoreWebView2.CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Png, file);
    }
}
