using System.Globalization;
using System.IO;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using DiffAtOnce.Academy.Core;
using Microsoft.Win32;

namespace DiffAtOnce.Academy.App;

public sealed class CalibrationWorkshopWindow : AcademyWindow
{
    readonly TabControl tabs = new();
    public event Action<string, string?>? TeachingContextChanged;
    public void PublishActiveContext()
    {
        if (tabs.SelectedItem is not TabItem { Tag: WorkshopPage p }) return;
        var moduleIds = new[] { "pulse-calibration", "gradient-calibration", "ramp-design", "convection", "ilt-conditioning" };
        var moduleId = moduleIds[tabs.SelectedIndex];
        if (p.Result is null) { TeachingContextChanged?.Invoke(moduleId, null); return; }
        var properties = p.Result.GetType().GetProperties();
        var result = properties.Where(x => x.Name != "Parameters" && x.Name != "Assumptions" && (x.PropertyType == typeof(string) || !typeof(System.Collections.IEnumerable).IsAssignableFrom(x.PropertyType))).ToDictionary(x => x.Name, x => x.GetValue(p.Result));
        var assumptions = properties.First(x => x.Name == "Assumptions").GetValue(p.Result) as ScientificAssumptions;
        var context = JsonSerializer.Serialize(new { evidenceStatus = "synthetic-teaching-simulation", origin = "native-workshop", moduleId, parameters = properties.First(x => x.Name == "Parameters").GetValue(p.Result), calculatedResults = result, assumptions = CourseLanguage == "en" ? assumptions?.English : assumptions?.Spanish });
        TeachingContextChanged?.Invoke(moduleId, context);
    }
    public CalibrationWorkshopWindow(string language) : base(language)
    {
        Title = T("Taller numérico · DiffAtOnce Academy", "Numeric workshop · DiffAtOnce Academy");
        var root = new DockPanel { Margin = new Thickness(23) }; var heading = new StackPanel();
        heading.Children.Add(MainWindow.Text(T("Provoca el error. Observa su consecuencia.", "Create the error. Observe its consequence."), 26, true));
        heading.Children.Add(MainWindow.Text(T("Simulaciones con parámetros conocidos y resultados calculados. Cada ejemplo indica la ecuación y sus supuestos.", "Simulations with known parameters and calculated results. Each example states its equation and assumptions.")));
        DockPanel.SetDock(heading, Dock.Top); root.Children.Add(heading); root.Children.Add(tabs); Content = root;
        Pulse(); Gradient(); Design(); Flow(); Ilt();
        tabs.SelectionChanged += (_, e) => { if (ReferenceEquals(e.Source, tabs)) PublishActiveContext(); };
    }
    sealed class WorkshopPage
    {
        public StackPanel Body { get; } = new() { Margin = new Thickness(20) };
        public WrapPanel Inputs { get; } = new();
        public StackPanel Results { get; } = new();
        public CurvePlot Plot { get; } = new();
        public TextBlock Assumptions { get; } = MainWindow.Text("", 12);
        public Dictionary<string, TextBox> Fields { get; } = [];
        public object? Result { get; set; }
        public double N(string key)
        {
            if (!double.TryParse(Fields[key].Text.Trim().Replace(',', '.'), NumberStyles.Float, CultureInfo.InvariantCulture, out var value) || !double.IsFinite(value)) throw new ArgumentException($"Invalid number: {key}");
            return value;
        }
        public int Integer(string key) { var value = N(key); if (value != Math.Truncate(value) || value < int.MinValue || value > int.MaxValue) throw new ArgumentException($"An integer is required: {key}"); return (int)value; }
    }
    WorkshopPage Page(string title, string objective, string why)
    {
        var p = new WorkshopPage(); p.Body.Children.Add(MainWindow.Text(objective, 19, true)); p.Body.Children.Add(MainWindow.Card(MainWindow.Text(why), "#FFF3E7"));
        p.Body.Children.Add(p.Inputs); p.Body.Children.Add(p.Plot); p.Body.Children.Add(p.Results); p.Body.Children.Add(p.Assumptions);
        tabs.Items.Add(new TabItem { Header = title, Tag = p, Content = new ScrollViewer { Content = p.Body, VerticalScrollBarVisibility = ScrollBarVisibility.Auto } }); return p;
    }
    void Field(WorkshopPage p, string key, string label, double value)
    {
        var panel = new StackPanel { Width = 184, Margin = new Thickness(0, 0, 17, 12) }; panel.Children.Add(MainWindow.Text(label, 12));
        var box = new TextBox { Text = value.ToString(CultureInfo.InvariantCulture), ToolTip = label }; p.Fields[key] = box; panel.Children.Add(box); p.Inputs.Children.Add(panel);
    }
    void Controls(WorkshopPage p, Action evaluate)
    {
        var actions = new WrapPanel(); var calculate = new Button { Content = T("Calcular", "Calculate") }; var export = new Button { Content = T("Exportar resultado JSON", "Export result JSON") };
        void Run() { try { p.Results.Children.Clear(); evaluate(); p.Plot.InvalidateVisual(); } catch (Exception e) when (e is ArgumentException or ArithmeticException) { p.Results.Children.Clear(); p.Results.Children.Add(MainWindow.Text(T("Revisa los parámetros: ", "Check the parameters: ") + e.Message)); p.Result = null; p.Plot.Curves = []; p.Plot.InvalidateVisual(); p.Assumptions.Text = ""; } PublishActiveContext(); }
        calculate.Click += (_, _) => Run(); export.Click += (_, _) =>
        {
            if (p.Result is null) return; var dialog = new SaveFileDialog { FileName = "Academy-synthetic-example.json", Filter = "JSON|*.json", OverwritePrompt = true };
            if (dialog.ShowDialog(this) == true) try { File.WriteAllText(dialog.FileName, JsonSerializer.Serialize(new { evidenceStatus = "synthetic-teaching-simulation", application = "DiffAtOnce Academy", result = p.Result }, CourseRepository.Json)); } catch (IOException e) { MessageBox.Show(this, e.Message); }
        };
        actions.Children.Add(calculate); actions.Children.Add(export); p.Body.Children.Insert(3, actions); Run();
        foreach (var box in p.Fields.Values) box.TextChanged += (_, _) => { p.Result = null; p.Results.Children.Clear(); p.Results.Children.Add(MainWindow.Text(T("Parámetros modificados: pulsa Calcular para obtener un nuevo resultado.", "Parameters changed: press Calculate for a new result."))); p.Plot.Curves = []; p.Plot.InvalidateVisual(); p.Assumptions.Text = ""; PublishActiveContext(); };
    }
    void Outcome(WorkshopPage p, string text, bool? pass = null) => p.Results.Children.Add(MainWindow.Card(MainWindow.Text(text, 15, true), pass == false ? "#FFF3E7" : "#E7F4F0"));
    void Assumptions(WorkshopPage p, ScientificAssumptions assumptions) => p.Assumptions.Text = T("Supuestos: ", "Assumptions: ") + (CourseLanguage == "en" ? assumptions.English : assumptions.Spanish);
    string F(double? value, string format = "G5") => value?.ToString(format, CultureInfo.CurrentCulture) ?? T("no recuperable", "not recoverable");
    void Pulse()
    {
        var p = Page(T("1 · Pulso de 90°", "1 · 90° pulse"), T("Encontrar el primer nulo de 180° y comprobar P90 = P180 / 2.", "Find the first 180° null and check P90 = P180 / 2."), T("Un nulo incorrecto o un espectro sin fase puede producir un P1 erróneo. En el ejemplo del experimento 1000: 22 µs / 2 = 11 µs. Después se comprueba el máximo de 90° a la misma potencia RF.", "An incorrect null or an unphased spectrum can give the wrong P1. In the experiment 1000 example: 22 µs / 2 = 11 µs. Then verify the 90° maximum at the same RF power."));
        Field(p, "selected", T("Nulo seleccionado P180 / µs", "Selected P180 null / µs"), 22); Field(p, "truth", T("P90 conocido / µs", "Known P90 / µs"), 11); Field(p, "noise", T("Ruido / %", "Noise / %"), 0);
        Controls(p, () => { var r = TeachingSimulations.PulseCalibration(p.N("selected"), p.N("truth"), p.N("noise")); p.Result = r; p.Plot.XLabel = T("Duración del pulso / µs", "Pulse duration / µs"); p.Plot.Curves = [new(T("Nutación con signo", "Signed nutation"), r.Curve, "#086C69")]; p.Plot.Markers = [new(r.TrueP90Microseconds, "90°", "#296FCE"), new(r.First180NullMicroseconds, "180°", "#DB433B")]; Outcome(p, $"P90 = {F(r.P90FromSelectedNullMicroseconds)} µs · " + T($"primer nulo = {F(r.First180NullMicroseconds)} µs · segundo nulo = {F(r.Next360NullMicroseconds)} µs", $"first null = {F(r.First180NullMicroseconds)} µs · second null = {F(r.Next360NullMicroseconds)} µs"), r.SelectedNullIsFirst180); Outcome(p, r.SelectedNullIsFirst180 ? T("Has seleccionado el primer nulo de 180°.", "You selected the first 180° null.") : T("El nulo seleccionado no coincide con el primer 180°. Prueba 44 µs y observa por qué dividir entre dos falla.", "The selected null does not match the first 180°. Try 44 µs and see why halving fails."), r.SelectedNullIsFirst180); Assumptions(p, r.Assumptions); });
    }
    void Gradient()
    {
        var p = Page(T("2 · Gradiente", "2 · Gradient"), T("Recuperar la escala del gradiente a partir de una señal del patrón.", "Recover the gradient scale from a standard signal."), T("Si b se calcula con un gradiente nominal erróneo, todo el eje D queda sesgado aunque el ajuste sea perfecto. Se ajusta la atenuación del patrón con D de referencia a temperatura conocida; la escala es √(Dajustado/Dref).", "If b uses the wrong nominal gradient, the whole D axis is biased even when the fit is perfect. Fit a standard attenuation with reference D at known temperature; the scale is √(Dfitted/Dref)."));
        Field(p, "g", "Gnom / mT m⁻¹", 420); Field(p, "delta", "δ / ms", 1.4); Field(p, "Delta", "Δ / ms", 80); Field(p, "d", "Dref / 10⁻⁹ m² s⁻¹", .8); Field(p, "scale", T("Greal / Gnom", "Gtrue / Gnom"), 1.1); Field(p, "noise", T("Ruido / %", "Noise / %"), 0);
        Controls(p, () => { var r = TeachingSimulations.GradientCalibration(p.N("g"), p.N("delta"), p.N("Delta"), p.N("d"), p.N("scale"), p.N("noise")); p.Result = r; p.Plot.XLabel = "bnom / 10⁹ s m⁻²"; p.Plot.Curves = [new(T("Señal del patrón", "Standard signal"), r.Points.Select(x => new CurvePoint(x.BNominalSi * 1e-9, x.Signal)).ToArray(), "#086C69")]; Outcome(p, T($"Escala recuperada = {F(r.RecoveredGradientScale)} · G recuperado = {F(r.RecoveredGradientMilliTeslaPerMetre)} mT/m", $"Recovered scale = {F(r.RecoveredGradientScale)} · recovered G = {F(r.RecoveredGradientMilliTeslaPerMetre)} mT/m")); Outcome(p, T($"D aparente con b nominal = {F(r.NominalApparentDiffusion1E9)} ×10⁻⁹ m²/s · R² = {F(r.Fit.R2SignalSpace)}", $"Apparent D with nominal b = {F(r.NominalApparentDiffusion1E9)} ×10⁻⁹ m²/s · R² = {F(r.Fit.R2SignalSpace)}")); Assumptions(p, r.Assumptions); });
    }
    void Design()
    {
        var p = Page(T("3 · δ y Δ", "3 · δ and Δ"), T("Encontrar una ventana de atenuación que conserve información útil.", "Find an attenuation window that retains useful information."), T("δ o Δ demasiado pequeños dejan una curva casi plana. Demasiado grandes hacen desaparecer el componente rápido bajo el ruido. Los nombres p30/d20 dependen del programa de pulsos; aquí usamos tiempos físicos PGSE ideales.", "Small δ or Δ gives an almost flat curve. Large values erase the fast component below noise. The p30/d20 meanings depend on the pulse program; here we use ideal physical PGSE times."));
        Field(p, "g", "Gmax / mT m⁻¹", 420); Field(p, "delta", "δ / ms", 1.4); Field(p, "Delta", "Δ / ms", 80); Field(p, "slow", T("D lento / 10⁻⁹ m² s⁻¹", "Slow D / 10⁻⁹ m² s⁻¹"), .45); Field(p, "fast", T("D rápido / 10⁻⁹ m² s⁻¹", "Fast D / 10⁻⁹ m² s⁻¹"), 1.4); Field(p, "noise", T("Ruido / %", "Noise / %"), 1);
        Controls(p, () => { var r = TeachingSimulations.AttenuationDesign(p.N("g"), p.N("delta"), p.N("Delta"), p.N("slow"), p.N("fast"), p.N("noise")); p.Result = r; p.Plot.XLabel = "G / %"; p.Plot.Curves = [new(T("Lento", "Slow"), r.Points.Select(x => new CurvePoint(x.GradientPercent, x.SlowSignal)).ToArray(), "#086C69"), new(T("Rápido", "Fast"), r.Points.Select(x => new CurvePoint(x.GradientPercent, x.FastSignal)).ToArray(), "#DF7142")]; Outcome(p, $"bmax = {F(r.BMaximumSi * 1e-9)} ×10⁹ s/m² · " + T($"señal lenta final = {F(r.SlowEndSignal)} · rápida = {F(r.FastEndSignal)}", $"final slow signal = {F(r.SlowEndSignal)} · fast = {F(r.FastEndSignal)}")); Outcome(p, T($"Ventana didáctica: lento ≤ 50 %: {r.SlowAttenuatedEnough}; rápido > 3σ: {r.FastAboveNoiseFloor}; S/σ rápido = {F(r.FastSignalToNoise)}", $"Teaching window: slow ≤ 50%: {r.SlowAttenuatedEnough}; fast > 3σ: {r.FastAboveNoiseFloor}; fast S/σ = {F(r.FastSignalToNoise)}"), r.SlowAttenuatedEnough && r.FastAboveNoiseFloor); Assumptions(p, r.Assumptions); });
    }
    void Flow()
    {
        var p = Page(T("4 · Convección", "4 · Convection"), T("Separar difusión, fase por flujo común y pérdida por dispersión de velocidades.", "Separate diffusion, common-flow phase and velocity-dispersion loss."), T("La velocidad común rota la señal compleja y puede mantener su magnitud. Una distribución de velocidades produce desfase, nulos y lóbulos; un ajuste exponencial entonces devuelve un D aparente que no es difusión pura.", "A common velocity rotates the complex signal and may preserve magnitude. A velocity distribution causes dephasing, nulls and lobes; an exponential fit then gives an apparent D that is not pure diffusion."));
        Field(p, "g", "Gmax / mT m⁻¹", 420); Field(p, "delta", "δ / ms", 1.4); Field(p, "Delta", "Δ / ms", 80); Field(p, "d", "D / 10⁻⁹ m² s⁻¹", .8); Field(p, "mean", T("Velocidad común / µm s⁻¹", "Common velocity / µm s⁻¹"), 35); Field(p, "width", T("Semiancho velocidad / µm s⁻¹", "Velocity half-width / µm s⁻¹"), 300);
        Controls(p, () => { var r = TeachingSimulations.Convection(p.N("g"), p.N("delta"), p.N("Delta"), p.N("d"), p.N("mean"), p.N("width")); p.Result = r; p.Plot.XLabel = "G / %"; p.Plot.Curves = [new(T("Difusión", "Diffusion"), r.Points.Select(x => new CurvePoint(x.GradientPercent, x.DiffusionSignal)).ToArray(), "#086C69"), new(T("Flujo: real", "Flow: real"), r.Points.Select(x => new CurvePoint(x.GradientPercent, x.CommonVelocityReal)).ToArray(), "#6894D1"), new(T("Dispersión: |S|", "Dispersion: |S|"), r.Points.Select(x => new CurvePoint(x.GradientPercent, x.VelocityDispersionMagnitude)).ToArray(), "#DF7142")]; Outcome(p, T($"D verdadero = {F(r.TrueDiffusion1E9)} · D con |flujo común| = {F(r.CommonMagnitudeDiffusion1E9)} · D aparente con dispersión = {F(r.DispersionMagnitudeApparentDiffusion1E9)}", $"True D = {F(r.TrueDiffusion1E9)} · D from |common flow| = {F(r.CommonMagnitudeDiffusion1E9)} · apparent D with dispersion = {F(r.DispersionMagnitudeApparentDiffusion1E9)}")); Outcome(p, T($"¿Magnitud no monótona? {r.DispersionMagnitudeIsNonmonotonic}. Cambia Δ o el semiancho y compara; una dependencia con Δ por sí sola no demuestra convección.", $"Nonmonotonic magnitude? {r.DispersionMagnitudeIsNonmonotonic}. Change Δ or half-width and compare; Δ dependence alone does not prove convection.")); Assumptions(p, r.Assumptions); });
    }
    void Ilt()
    {
        var p = Page("5 · ILT", T("Ver por qué dos distribuciones diferentes pueden explicar casi la misma señal.", "See why two different distributions can explain almost the same signal."), T("Las columnas exponenciales del núcleo se parecen mucho. Las direcciones con valores singulares pequeños amplifican el ruido; una curva bien ajustada no garantiza especies separadas. El ruido define qué parte del problema es resoluble.", "Exponential kernel columns look alike. Small singular values amplify noise; a well-fitted curve does not guarantee separated species. Noise determines what part of the problem can be resolved."));
        Field(p, "b", "bmax / 10⁹ s m⁻²", 3); Field(p, "points", T("Puntos adquiridos", "Acquired points"), 32); Field(p, "bins", T("Bins de difusión", "Diffusion bins"), 40); Field(p, "noise", T("Ruido / %", "Noise / %"), 1);
        Controls(p, () => { var r = TeachingSimulations.InverseLaplaceConditioning(p.N("b"), p.Integer("points"), p.Integer("bins"), p.N("noise")); p.Result = r; p.Plot.XLabel = "b / 10⁹ s m⁻²"; p.Plot.Curves = [new(T("Dos componentes", "Two components"), r.CandidateCurves.Select(x => new CurvePoint(x.B1E9, x.TwoComponentSignal)).ToArray(), "#086C69"), new(T("Un componente", "One component"), r.CandidateCurves.Select(x => new CurvePoint(x.B1E9, x.SingleComponentSignal)).ToArray(), "#DF7142")]; Outcome(p, T($"Rango efectivo = {r.EffectiveRank} · direcciones no resueltas = {r.UnresolvedDirections} · condición del subespacio resuelto = {F(r.ResolvedSubspaceConditionNumber)}", $"Effective rank = {r.EffectiveRank} · unresolved directions = {r.UnresolvedDirections} · resolved-subspace condition = {F(r.ResolvedSubspaceConditionNumber)}")); Outcome(p, T($"Diferencia máxima entre señales = {F(r.MaxCandidateSignalDifference)} · diferencia / ruido = {F(r.CandidateDifferenceToNoiseRatio)}. La regularización aporta hipótesis; no crea información medida.", $"Maximum signal difference = {F(r.MaxCandidateSignalDifference)} · difference / noise = {F(r.CandidateDifferenceToNoiseRatio)}. Regularization adds assumptions; it does not create measured information.")); var singularPlot = new CurvePlot { XLabel = T("Índice singular", "Singular index"), YLabel = "log₁₀(σᵢ/σ₁)", Curves = [new(T("Espectro singular", "Singular spectrum"), r.RelativeSingularValues.Select((x, i) => new CurvePoint(i + 1, Math.Log10(Math.Max(x, 1e-16)))).ToArray(), "#6894D1")] }; p.Results.Children.Add(singularPlot); Assumptions(p, r.Assumptions); });
    }
}


