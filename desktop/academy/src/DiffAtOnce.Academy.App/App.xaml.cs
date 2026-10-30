using System.Windows;
using System.IO;
namespace DiffAtOnce.Academy.App;
public partial class App : Application
{
    static App()
    {
        // Software QA may run without an attached display. This supported WPF
        // switch affects only the application's own --self-test rendering.
        if (Environment.GetCommandLineArgs().Contains("--self-test")) AppContext.SetSwitch("Switch.System.Windows.Media.ShouldRenderEvenWhenNoDisplayDevicesAreAvailable", true);
    }
    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        var index = Array.IndexOf(e.Args, "--self-test");
        var qa = index >= 0 && e.Args.Length > index + 1 ? e.Args[index + 1] : null;
        if (qa is not null) System.Windows.Media.RenderOptions.ProcessRenderMode = System.Windows.Interop.RenderMode.SoftwareOnly;
        void Stage(string stage) { if (qa is not null) { Directory.CreateDirectory(qa); File.AppendAllText(Path.Combine(qa, "startup-stages.txt"), DateTimeOffset.UtcNow + " " + stage + Environment.NewLine); } }
        void Log(Exception exception) { if (qa is not null) { Directory.CreateDirectory(qa); File.AppendAllText(Path.Combine(qa, "application-error.txt"), exception + Environment.NewLine); } }
        DispatcherUnhandledException += (_, error) => { Log(error.Exception); if (qa is null) MessageBox.Show("DiffAtOnce Academy\n" + error.Exception.Message, "Application", MessageBoxButton.OK, MessageBoxImage.Error); error.Handled = true; Shutdown(2); };
        AppDomain.CurrentDomain.UnhandledException += (_, error) => { if (error.ExceptionObject is Exception exception) Log(exception); };
        try { Stage("construct"); var window = new MainWindow(e.Args); Stage("constructed"); MainWindow = window; Stage("show"); window.Show(); Stage("shown"); }
        catch (Exception ex) { Log(ex); if (qa is null) MessageBox.Show("DiffAtOnce Academy\n" + ex.Message, "Startup", MessageBoxButton.OK, MessageBoxImage.Error); Shutdown(1); }
    }
}
