using System.Globalization;
using System.IO;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using DiffAtOnce.Academy.Core;

namespace DiffAtOnce.Academy.App;

public abstract class AcademyWindow : Window
{
    protected string CourseLanguage { get; }
    protected string T(string es, string en) => CourseLanguage == "en" ? en : es;
    protected AcademyWindow(string language)
    {
        CourseLanguage = language; Width = 1100; Height = 850; MinWidth = 750; MinHeight = 600;
        WindowStartupLocation = WindowStartupLocation.CenterOwner; Background = Brushes.White; FontFamily = new FontFamily("Segoe UI");
    }
    public void Capture(string path)
    {
        CaptureWindow(this, path);
    }
    public static void CaptureWindow(Window window, string path)
    {
        window.UpdateLayout();
        var content = (FrameworkElement)window.Content;
        var size = new Size(content.ActualWidth, content.ActualHeight); content.Measure(size); content.Arrange(new Rect(size)); content.UpdateLayout();
        var drawing = new DrawingVisual(); using (var dc = drawing.RenderOpen()) { dc.DrawRectangle(window.Background ?? Brushes.White, null, new Rect(size)); dc.DrawRectangle(new VisualBrush(content), null, new Rect(size)); }
        var bitmap = new RenderTargetBitmap((int)size.Width, (int)size.Height, 96, 96, PixelFormats.Pbgra32); bitmap.Render(drawing); bitmap.Freeze();
        var pixelBytes = new byte[bitmap.PixelWidth * bitmap.PixelHeight * 4]; bitmap.CopyPixels(pixelBytes, bitmap.PixelWidth * 4, 0);
        if (!pixelBytes.Where((_, i) => i % 4 == 3).Any(alpha => alpha != 0)) throw new InvalidOperationException("WPF capture is transparent; visual QA did not complete.");
        var encoder = new PngBitmapEncoder(); encoder.Frames.Add(BitmapFrame.Create(bitmap)); using var output = File.Create(path); encoder.Save(output);
    }
}

public sealed class GuideWindow : AcademyWindow
{
    public GuideWindow(string path, string language) : base(language)
    {
        Title = "DiffAtOnce Academy · " + T("Manual", "Manual");
        var panel = new StackPanel { Margin = new Thickness(26) };
        foreach (var line in File.ReadLines(path))
        {
            var heading = line.StartsWith('#'); var text = line.TrimStart('#').Trim().Replace("**", "").Replace("`", "");
            panel.Children.Add(MainWindow.Text(text, heading ? 20 : 14, heading));
        }
        Content = new ScrollViewer { Content = panel, VerticalScrollBarVisibility = ScrollBarVisibility.Auto };
    }
}

public sealed class SourceSlidesWindow : AcademyWindow
{
    readonly CourseRepository repository;
    readonly IReadOnlyList<Slide> slides;
    readonly Image image = new() { Stretch = Stretch.Uniform, Margin = new Thickness(0, 0, 0, 12) };
    readonly TextBlock notes = MainWindow.Text("");
    readonly ComboBox select = new() { MinWidth = 350, MaxWidth = 650 };
    readonly TextBlock provenance = MainWindow.Text("", 11);
    public SourceSlidesWindow(CourseRepository repository, string language, int? slide) : base(language)
    {
        this.repository = repository; slides = repository.Slides();
        Title = T("Diapositivas originales · DiffAtOnce Academy", "Original source slides · DiffAtOnce Academy");
        var root = new DockPanel { Margin = new Thickness(22) };
        var header = new StackPanel(); header.Children.Add(MainWindow.Text(T("El workshop original, disponible dentro del curso", "The original workshop, available within the course"), 23, true));
        var nav = new WrapPanel(); var previous = new Button { Content = "←" }; var next = new Button { Content = "→" };
        select.ItemsSource = slides.Select(s => $"{s.SlideNumber:00} · {s.Title}").ToArray();
        select.SelectionChanged += (_, _) => Display(); previous.Click += (_, _) => select.SelectedIndex = Math.Max(0, select.SelectedIndex - 1); next.Click += (_, _) => select.SelectedIndex = Math.Min(slides.Count - 1, select.SelectedIndex + 1);
        nav.Children.Add(previous); nav.Children.Add(select); nav.Children.Add(next); header.Children.Add(nav);
        header.Children.Add(MainWindow.Text(T("Imágenes y notas extraídas del archivo aportado. Las notas conservan el idioma original.", "Images and notes extracted from the supplied file. Notes retain their original language."), 12));
        DockPanel.SetDock(header, Dock.Top); root.Children.Add(header);
        provenance.Text = T("Fuente: DOSY_in_practice_GERMN2026_EN_v6d.pptx · integridad registrada en source-index.json", "Source: DOSY_in_practice_GERMN2026_EN_v6d.pptx · integrity recorded in source-index.json");
        DockPanel.SetDock(provenance, Dock.Bottom); root.Children.Add(provenance);
        var body = new StackPanel(); body.Children.Add(image); body.Children.Add(MainWindow.Text(T("Notas de la diapositiva", "Slide notes"), 17, true)); body.Children.Add(notes);
        root.Children.Add(new ScrollViewer { Content = body, VerticalScrollBarVisibility = ScrollBarVisibility.Auto }); Content = root;
        select.SelectedIndex = Math.Max(0, slides.ToList().FindIndex(s => s.SlideNumber == (slide ?? 1)));
    }
    void Display()
    {
        if (select.SelectedIndex < 0) return;
        var slide = slides[select.SelectedIndex]; var asset = repository.ResolveAsset(slide.Image);
        var bitmap = new BitmapImage(); bitmap.BeginInit(); bitmap.CacheOption = BitmapCacheOption.OnLoad; bitmap.UriSource = new Uri(asset); bitmap.EndInit(); bitmap.Freeze(); image.Source = bitmap;
        notes.Text = string.IsNullOrWhiteSpace(slide.Notes) ? slide.Text : slide.Notes;
    }
}

public sealed class MethodsWindow : AcademyWindow
{
    readonly List<JsonElement> records;
    readonly StackPanel rows = new();
    readonly TextBox search = new() { Margin = new Thickness(0, 8, 0, 12) };
    public MethodsWindow(string contentDirectory, string language) : base(language)
    {
        Title = T("Catálogo práctico de métodos · DiffAtOnce Academy", "Practical methods catalogue · DiffAtOnce Academy");
        using var doc = JsonDocument.Parse(File.ReadAllText(Path.Combine(contentDirectory, "algorithm-catalog.json")));
        records = doc.RootElement.GetProperty("records").EnumerateArray().Select(r => r.Clone()).ToList();
        var root = new DockPanel { Margin = new Thickness(23) }; var header = new StackPanel();
        header.Children.Add(MainWindow.Text(T("Qué resuelve cada método y qué presupone", "What each method solves and assumes"), 25, true));
        header.Children.Add(MainWindow.Text(doc.RootElement.GetProperty(language == "en" ? "scope_en" : "scope_es").GetString() ?? ""));
        search.ToolTip = T("Buscar nombre, uso o limitación", "Search name, use or limitation"); search.TextChanged += (_, _) => Render(); header.Children.Add(search);
        DockPanel.SetDock(header, Dock.Top); root.Children.Add(header); root.Children.Add(new ScrollViewer { Content = rows, VerticalScrollBarVisibility = ScrollBarVisibility.Auto }); Content = root; Render();
    }
    string Get(JsonElement record, string name) => record.TryGetProperty(name, out var p) ? p.ToString() : "";
    void Render()
    {
        rows.Children.Clear(); var term = search.Text.Trim();
        foreach (var record in records.Where(r => term.Length == 0 || r.ToString().Contains(term, StringComparison.CurrentCultureIgnoreCase)))
        {
            var panel = new StackPanel(); panel.Children.Add(MainWindow.Text(Get(record, "name") + " · " + Get(record, "id"), 18, true));
            panel.Children.Add(MainWindow.Text(T("Para qué: ", "Use: ") + Get(record, CourseLanguage == "en" ? "use_en" : "use_es")));
            panel.Children.Add(MainWindow.Text(T("Objetivo: ", "Objective: ") + Get(record, "objective")));
            panel.Children.Add(MainWindow.Text(T("Límite: ", "Limit: ") + Get(record, CourseLanguage == "en" ? "limits_en" : "limits_es")));
            panel.Children.Add(MainWindow.Text(Get(record, CourseLanguage == "en" ? "availability_en" : "availability_es"), 12));
            panel.Children.Add(MainWindow.Text(T("Evidencia: auditoría del catálogo y código; no es una nueva comparación experimental.", "Evidence: source and catalogue audit; this is not a new experimental comparison."), 11));
            rows.Children.Add(MainWindow.Card(panel));
        }
    }
}

public sealed class CurvePlot : FrameworkElement
{
    public record Series(string Label, IReadOnlyList<CurvePoint> Points, string Color);
    public record Marker(double X, string Label, string Color);
    public IReadOnlyList<Series> Curves { get; set; } = [];
    public IReadOnlyList<Marker> Markers { get; set; } = [];
    public string XLabel { get; set; } = "";
    public string YLabel { get; set; } = "S/S₀";
    public CurvePlot() { Height = 285; MinWidth = 320; Margin = new Thickness(0, 13, 0, 13); }
    protected override void OnRender(DrawingContext dc)
    {
        base.OnRender(dc); var w = ActualWidth; var h = ActualHeight; if (w < 100 || h < 100 || Curves.Count == 0) return;
        var all = Curves.SelectMany(c => c.Points).Where(p => double.IsFinite(p.X) && double.IsFinite(p.Y)).ToArray(); if (all.Length == 0) return;
        var x0 = all.Min(p => p.X); var x1 = all.Max(p => p.X); var y0 = Math.Min(0, all.Min(p => p.Y)); var y1 = all.Max(p => p.Y); if (x1 == x0) x1++; if (y1 == y0) y1++;
        var left = 64.0; var top = 42.0; var right = w - 20; var bottom = h - 47;
        Point P(CurvePoint p) => new(left + (p.X - x0) / (x1 - x0) * (right - left), bottom - (p.Y - y0) / (y1 - y0) * (bottom - top));
        FormattedText Ft(string text, double size = 12) => new(text, CultureInfo.CurrentCulture, FlowDirection.LeftToRight, new Typeface("Segoe UI"), size, Brushes.DarkSlateGray, VisualTreeHelper.GetDpi(this).PixelsPerDip);
        var grid = new Pen(new SolidColorBrush(Color.FromRgb(221, 232, 235)), 1);
        dc.DrawRectangle(new SolidColorBrush(Color.FromRgb(248, 251, 252)), null, new Rect(0, 0, w, h));
        for (var i = 0; i <= 4; i++) { var x = left + i * (right - left) / 4; var y = bottom - i * (bottom - top) / 4; dc.DrawLine(grid, new Point(x, top), new Point(x, bottom)); dc.DrawLine(grid, new Point(left, y), new Point(right, y)); dc.DrawText(Ft((x0 + i * (x1 - x0) / 4).ToString("G3")), new Point(x - 12, bottom + 8)); dc.DrawText(Ft((y0 + i * (y1 - y0) / 4).ToString("G3")), new Point(6, y - 8)); }
        dc.DrawText(Ft(XLabel), new Point(left + (right - left) * .35, bottom + 28)); dc.DrawText(Ft(YLabel), new Point(8, 8));
        foreach (var marker in Markers.Where(m => m.X >= x0 && m.X <= x1))
        {
            var x = P(new CurvePoint(marker.X, 0)).X; var color = (Color)ColorConverter.ConvertFromString(marker.Color);
            var pen = new Pen(new SolidColorBrush(color), 1.5) { DashStyle = DashStyles.Dash }; dc.DrawLine(pen, new Point(x, top), new Point(x, bottom));
            var label = Ft(marker.Label, 13); label.SetForegroundBrush(new SolidColorBrush(color)); dc.DrawText(label, new Point(Math.Min(right - label.Width, x + 5), top + 6));
        }
        var legendX = left;
        foreach (var series in Curves)
        {
            var color = (Color)ColorConverter.ConvertFromString(series.Color); var pen = new Pen(new SolidColorBrush(color), 2);
            var points = series.Points.Where(p => double.IsFinite(p.X) && double.IsFinite(p.Y)).ToArray();
            for (var i = 1; i < points.Length; i++) dc.DrawLine(pen, P(points[i - 1]), P(points[i]));
            dc.DrawLine(pen, new Point(legendX, 19), new Point(legendX + 18, 19)); var label = Ft(series.Label); dc.DrawText(label, new Point(legendX + 23, 10)); legendX += label.Width + 50;
        }
    }
}
