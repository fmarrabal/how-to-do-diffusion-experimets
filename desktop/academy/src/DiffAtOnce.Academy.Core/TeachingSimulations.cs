using System;
using System.Collections.Generic;
using System.Linq;

namespace DiffAtOnce.Academy.Core;

/// <summary>
/// Synthetic teaching calculators. No file access, instrument control, original
/// data, or persisted TBO/KK2 calibration is used. Angular gamma: no extra 2π.
/// Primary sources: Stejskal & Tanner, doi:10.1063/1.1695690;
/// flow/velocity distribution, https://pubmed.ncbi.nlm.nih.gov/12810021/;
/// inverse Laplace conditioning, doi:10.1016/j.jmr.2011.05.014.
/// </summary>
public static class TeachingSimulations
{
    public const double Gamma1H = 2.6752218744e8; // rad s^-1 T^-1
    public const string ScientificStatus = "synthetic-education-only";

    /// <summary>Manual first 180° null / 2 at the same RF power, phase and offset.</summary>
    public static PulseCalibrationResult PulseCalibration(
        double p180Microseconds = 22, double trueP90Microseconds = 11,
        double noisePercent = 0, int seed = 1729)
    {
        Positive(p180Microseconds, nameof(p180Microseconds));
        Positive(trueP90Microseconds, nameof(trueP90Microseconds));
        Noise(noisePercent);
        var max = Computed(4 * trueP90Microseconds, "Pulse display range");
        var random = new SeededNormal(seed);
        var curve = Enumerable.Range(0, 201).Select(i =>
        {
            var pulse = max * i / 200;
            var signal = Math.Sin(Math.PI * pulse / (2 * trueP90Microseconds));
            return new CurvePoint(pulse, signal + noisePercent / 100 * random.Next());
        });
        var firstNull = 2 * trueP90Microseconds;
        return new PulseCalibrationResult(
            new(p180Microseconds, trueP90Microseconds, noisePercent, seed),
            p180Microseconds / 2, trueP90Microseconds, firstNull, max,
            Math.Abs(p180Microseconds - firstNull) <= trueP90Microseconds * 0.01,
            ReadOnly(curve), new(
                "Synthetic signed nutation: the manually selected first non-zero null is assumed to be 180°. At unchanged RF power/offset/phase, P90=P180/2. The next 360° null is not P180. Experiment 1000 is the user's example label, not an acquisition command. No RF inhomogeneity, relaxation or power calibration is modelled.",
                "Nutación sintética con signo: se supone que el primer nulo no trivial seleccionado manualmente es 180°. A la misma potencia RF, frecuencia y fase, P90=P180/2. El siguiente nulo de 360° no es P180. Experimento 1000 es la etiqueta del ejemplo del usuario, no una orden de adquisición. Se omiten inhomogeneidad RF, relajación y calibración de potencia."));
    }

    /// <summary>Ideal rectangular PGSE. Delta is leading-edge separation; lobes may not overlap.</summary>
    public static double PgseB(double gradientTeslaPerMetre, double deltaSeconds, double bigDeltaSeconds)
    {
        Nonnegative(gradientTeslaPerMetre, nameof(gradientTeslaPerMetre));
        Positive(deltaSeconds, nameof(deltaSeconds));
        Positive(bigDeltaSeconds, nameof(bigDeltaSeconds));
        if (bigDeltaSeconds < deltaSeconds)
            throw new ArgumentOutOfRangeException(nameof(bigDeltaSeconds), "PGSE lobes must not overlap: Delta >= delta.");
        var q = Computed(Gamma1H * gradientTeslaPerMetre * deltaSeconds, "Angular q");
        return Computed(q * q * (bigDeltaSeconds - deltaSeconds / 3), "PGSE b");
    }

    /// <summary>
    /// Exact integration for piecewise-constant effective gradients. The caller
    /// supplies coherence/RF signs: G_eff is not simply the physical gradient.
    /// A zero G_eff interval preserves accumulated q, including longitudinal storage.
    /// </summary>
    public static GradientWaveformResult SequenceB(IReadOnlyList<EffectiveGradientSegment> segments,
        bool requireBalancedEcho = true)
    {
        ArgumentNullException.ThrowIfNull(segments);
        if (segments.Count == 0) throw new ArgumentException("At least one segment is required.", nameof(segments));
        var q = 0.0; var integral = 0.0; var totalTime = 0.0; var maxQ = 0.0;
        foreach (var segment in segments)
        {
            ArgumentNullException.ThrowIfNull(segment);
            Positive(segment.DurationSeconds, nameof(segment.DurationSeconds));
            Finite(segment.EffectiveGradientTeslaPerMetre, nameof(segment.EffectiveGradientTeslaPerMetre));
            var h = segment.DurationSeconds;
            var rate = Computed(Gamma1H * segment.EffectiveGradientTeslaPerMetre, "Angular q rate");
            integral += q * q * h + q * rate * h * h + rate * rate * h * h * h / 3;
            q = Computed(q + rate * h, "Accumulated angular q");
            maxQ = Math.Max(maxQ, Math.Abs(q)); totalTime += h;
        }
        Computed(integral, "Sequence b"); Computed(totalTime, "Sequence duration");
        var balanced = Math.Abs(q) <= 1e-10 * Math.Max(1, maxQ);
        if (requireBalancedEcho && !balanced)
            throw new ArgumentException("The effective waveform is not balanced at the echo.", nameof(segments));
        var unbalancedEnglish = balanced ? "" : " The waveform is unbalanced: this b integral alone does not predict the echo signal; residual spatial phase must also be treated.";
        var unbalancedSpanish = balanced ? "" : " La forma de gradiente está desequilibrada: esta integral b por sí sola no predice el eco; hay que tratar también la fase espacial residual.";
        return new(integral, q, totalTime, balanced, new(
            "b=integral q(t)^2 dt, q=gamma integral G_eff dt; SI units and angular gamma. Free Gaussian diffusion, ideal instantaneous RF/coherence changes and a balanced echo. Actual sequence timing, RF and auxiliary gradients must be supplied; p30/d20/d5 are not universal delta/Delta aliases." + unbalancedEnglish,
            "b=integral q(t)^2 dt, q=gamma integral G_eff dt; unidades SI y gamma angular. Difusión gaussiana libre, cambios RF/coherencia instantáneos ideales y eco equilibrado. Hay que introducir tiempos, RF y gradientes auxiliares de la secuencia real; p30/d20/d5 no equivalen universalmente a delta/Delta." + unbalancedSpanish));
    }

    public static GradientCalibrationResult GradientCalibration(
        double nominalMaxGradientMilliTeslaPerMetre = 420,
        double deltaMilliseconds = 1.4, double bigDeltaMilliseconds = 80,
        double referenceDiffusion1E9 = 0.8, double actualToNominalGradientRatio = 1.1,
        double noisePercent = 0, int seed = 1730)
    {
        Positive(nominalMaxGradientMilliTeslaPerMetre, nameof(nominalMaxGradientMilliTeslaPerMetre));
        Positive(referenceDiffusion1E9, nameof(referenceDiffusion1E9));
        Positive(actualToNominalGradientRatio, nameof(actualToNominalGradientRatio)); Noise(noisePercent);
        var referenceSi = referenceDiffusion1E9 * 1e-9;
        Positive(referenceSi, nameof(referenceDiffusion1E9));
        var bMax = PgseB(nominalMaxGradientMilliTeslaPerMetre * 1e-3, deltaMilliseconds * 1e-3, bigDeltaMilliseconds * 1e-3);
        var random = new SeededNormal(seed);
        var points = Enumerable.Range(0, 24).Select(i =>
        {
            var fraction = .08 + .88 * i / 23;
            var bNominal = bMax * fraction * fraction;
            var bTrue = Computed(bNominal * actualToNominalGradientRatio * actualToNominalGradientRatio, "True b");
            return new GradientPoint(fraction * 100, bNominal, bTrue,
                Math.Exp(-bTrue * referenceSi) + noisePercent / 100 * random.Next());
        }).ToArray();
        var fit = FitExponential(points.Select(p => p.BNominalSi).ToArray(), points.Select(p => p.Signal).ToArray());
        double? scale = fit.DiffusionSi is { } d ? Math.Sqrt(Computed(d / referenceSi, "Recovered gradient squared scale")) : null;
        return new(new(nominalMaxGradientMilliTeslaPerMetre, deltaMilliseconds, bigDeltaMilliseconds,
                referenceDiffusion1E9, actualToNominalGradientRatio, noisePercent, seed),
            actualToNominalGradientRatio, scale,
            fit.DiffusionSi * 1e9, scale * nominalMaxGradientMilliTeslaPerMetre,
            fit, ReadOnly(points), new(
                "Synthetic standard at a specified reference D. With correct rectangular-PGSE timing, D fitted using nominal b equals Dref*(Gtrue/Gnominal)^2; the gradient scale is sqrt(Dfit/Dref). A 10% gradient-scale error causes 21% apparent-D error. This is not a real calibration: temperature/reference uncertainty, profile, convection and sequence-specific b must be checked separately. Positive-point log fitting can be biased by noise.",
                "Patrón sintético con D de referencia definido. Con tiempos PGSE rectangulares correctos, D ajustado con b nominal es Dref*(Greal/Gnominal)^2; la escala de gradiente es sqrt(Dfit/Dref). Un error del 10% en gradiente causa un error del 21% en D aparente. No es una calibración real: hay que comprobar temperatura/referencia, perfil, convección y b específico de la secuencia. El ajuste logarítmico de puntos positivos puede sesgarse con ruido."));
    }

    public static AttenuationDesignResult AttenuationDesign(
        double gradientMilliTeslaPerMetre = 420, double deltaMilliseconds = 1.4,
        double bigDeltaMilliseconds = 80, double slowDiffusion1E9 = 0.45,
        double fastDiffusion1E9 = 1.4, double noisePercent = 1)
    {
        Positive(slowDiffusion1E9, nameof(slowDiffusion1E9));
        Positive(fastDiffusion1E9, nameof(fastDiffusion1E9)); Noise(noisePercent);
        if (fastDiffusion1E9 < slowDiffusion1E9)
            throw new ArgumentOutOfRangeException(nameof(fastDiffusion1E9), "Fast D must be >= slow D.");
        var b = PgseB(gradientMilliTeslaPerMetre * 1e-3, deltaMilliseconds * 1e-3, bigDeltaMilliseconds * 1e-3);
        var points = Enumerable.Range(0, 33).Select(i =>
        {
            var percent = 100.0 * i / 32; var bi = b * Math.Pow(percent / 100, 2);
            return new AttenuationPoint(percent, bi,
                Math.Exp(-bi * slowDiffusion1E9 * 1e-9), Math.Exp(-bi * fastDiffusion1E9 * 1e-9));
        }).ToArray();
        var end = points[^1]; var sigma = noisePercent / 100;
        return new(new(gradientMilliTeslaPerMetre, deltaMilliseconds, bigDeltaMilliseconds,
                slowDiffusion1E9, fastDiffusion1E9, noisePercent), b,
            end.SlowSignal, end.FastSignal, sigma > 0 ? end.FastSignal / sigma : null,
            end.SlowSignal <= .5, end.FastSignal > Math.Max(3 * sigma, 1e-12),
            ReadOnly(points), new(
                "Ideal rectangular PGSE only, S/S0=exp(-bD). The teaching window checks at least 50% slow-component attenuation and a fast-component signal above 3*noise; it is not an acquisition recommendation or statistical detection guarantee. Relaxation, convection, gradient shape, J and hardware duty cycle are omitted. Physical delta/Delta must be obtained from the actual pulse program.",
                "Sólo PGSE rectangular ideal, S/S0=exp(-bD). La ventana didáctica comprueba al menos 50% de atenuación del componente lento y señal rápida por encima de 3*ruido; no es una recomendación de adquisición ni una garantía estadística de detección. Se omiten relajación, convección, forma del gradiente, J y ciclo de trabajo. Delta/delta físicos deben obtenerse del programa de pulsos real."));
    }

    public static ConvectionResult Convection(
        double gradientMilliTeslaPerMetre = 420, double deltaMilliseconds = 1.4,
        double bigDeltaMilliseconds = 80, double diffusion1E9 = 0.8,
        double meanVelocityMicrometresPerSecond = 35,
        double velocityHalfWidthMicrometresPerSecond = 300,
        double noisePercent = 0, int seed = 1731)
    {
        Positive(diffusion1E9, nameof(diffusion1E9));
        Finite(meanVelocityMicrometresPerSecond, nameof(meanVelocityMicrometresPerSecond));
        Nonnegative(velocityHalfWidthMicrometresPerSecond, nameof(velocityHalfWidthMicrometresPerSecond)); Noise(noisePercent);
        var g = gradientMilliTeslaPerMetre * 1e-3; var delta = deltaMilliseconds * 1e-3; var bigDelta = bigDeltaMilliseconds * 1e-3;
        var bMax = PgseB(g, delta, bigDelta); var random = new SeededNormal(seed); var sigma = noisePercent / 100;
        var points = Enumerable.Range(0, 65).Select(i =>
        {
            var fraction = i / 64.0; var b = bMax * fraction * fraction; var q = Gamma1H * g * delta * fraction;
            var phase = Computed(q * bigDelta * meanVelocityMicrometresPerSecond * 1e-6, "Velocity phase");
            var argument = Computed(q * bigDelta * velocityHalfWidthMicrometresPerSecond * 1e-6, "Velocity-width phase");
            var signal = Math.Exp(-b * diffusion1E9 * 1e-9); var spread = Sinc(argument);
            var commonReal = signal * Math.Cos(phase) + sigma * random.Next();
            var commonImaginary = signal * Math.Sin(phase) + sigma * random.Next();
            var dispersedReal = signal * spread * Math.Cos(phase) + sigma * random.Next();
            var dispersedImaginary = signal * spread * Math.Sin(phase) + sigma * random.Next();
            return new ConvectionPoint(fraction * 100, b, q, signal, commonReal, commonImaginary,
                Math.Sqrt(commonReal * commonReal + commonImaginary * commonImaginary),
                dispersedReal, dispersedImaginary, Math.Sqrt(dispersedReal * dispersedReal + dispersedImaginary * dispersedImaginary));
        }).ToArray();
        var commonFit = FitExponential(points.Select(p => p.BSi).ToArray(), points.Select(p => p.CommonVelocityMagnitude).ToArray());
        var spreadFit = FitExponential(points.Select(p => p.BSi).ToArray(), points.Select(p => p.VelocityDispersionMagnitude).ToArray());
        var nonmonotonic = points.Zip(points.Skip(1)).Any(pair => pair.Second.VelocityDispersionMagnitude > pair.First.VelocityDispersionMagnitude + 1e-10);
        return new(new(gradientMilliTeslaPerMetre, deltaMilliseconds, bigDeltaMilliseconds, diffusion1E9,
                meanVelocityMicrometresPerSecond, velocityHalfWidthMicrometresPerSecond, noisePercent, seed),
            diffusion1E9, commonFit.DiffusionSi * 1e9, spreadFit.DiffusionSi * 1e9,
            nonmonotonic, commonFit, spreadFit, ReadOnly(points), new(
                "Free Gaussian diffusion plus constant velocities during encoding. A common velocity changes phase exp(i*q*v*Delta), not noiseless magnitude. A uniform distribution [mean-a,mean+a] multiplies the complex signal by sinc(q*a*Delta), which can have nodes and side lobes; it is not a Gaussian velocity distribution. Its fitted monoexponential D is apparent, not the true diffusion. Real-channel and magnitude fits are different. Gaussian noise is added to each complex channel; magnitude introduces noise-floor bias. No convection-compensated pulse program is simulated.",
                "Difusión gaussiana libre y velocidades constantes durante la codificación. Una velocidad común cambia la fase exp(i*q*v*Delta), no la magnitud sin ruido. Una distribución uniforme [media-a,media+a] multiplica la señal compleja por sinc(q*a*Delta), con posibles nulos y lóbulos; no es una distribución gaussiana de velocidades. Su D monoexponencial es aparente. Ajustar parte real y magnitud no es equivalente. Se añade ruido gaussiano a cada canal complejo; la magnitud introduce sesgo de suelo de ruido. No se simula una secuencia compensada por convección."));
    }

    public static IltConditioningResult InverseLaplaceConditioning(
        double maxB1E9 = 3, int pointCount = 32, int diffusionBins = 40, double noisePercent = 1)
    {
        Nonnegative(maxB1E9, nameof(maxB1E9)); Noise(noisePercent);
        if (pointCount is < 4 or > 128) throw new ArgumentOutOfRangeException(nameof(pointCount), "Use 4-128 observations.");
        if (diffusionBins is < 4 or > 128) throw new ArgumentOutOfRangeException(nameof(diffusionBins), "Use 4-128 diffusion bins.");
        var b = Enumerable.Range(0, pointCount).Select(i => maxB1E9 * i / (pointCount - 1)).ToArray();
        var d = Enumerable.Range(0, diffusionBins).Select(j => .1 * Math.Pow(30, j / (double)(diffusionBins - 1))).ToArray();
        var kernel = new double[pointCount, diffusionBins];
        for (var i = 0; i < pointCount; i++) for (var j = 0; j < diffusionBins; j++)
            kernel[i, j] = Math.Exp(-b[i] * d[j]) / Math.Sqrt(pointCount);
        var gram = new double[diffusionBins, diffusionBins];
        for (var j = 0; j < diffusionBins; j++) for (var k = j; k < diffusionBins; k++)
        {
            var sum = 0.0; for (var i = 0; i < pointCount; i++) sum += kernel[i, j] * kernel[i, k];
            gram[j, k] = gram[k, j] = sum;
        }
        var singular = SymmetricEigenvalues(gram).Select(e => Math.Sqrt(Math.Max(0, e))).OrderByDescending(v => v).Take(Math.Min(pointCount, diffusionBins)).ToArray();
        var relative = singular.Select(s => s / singular[0]).ToArray();
        const double numericalFloor = 1e-7; // Gram matrix cannot resolve the extremely small SVD tail.
        var cutoff = Math.Max(numericalFloor, noisePercent / 100);
        var effectiveRank = relative.Count(s => s > cutoff);
        var reliable = relative.Where(s => s > numericalFloor).ToArray();
        var curves = b.Select(bi => new IltCandidatePoint(bi,
            .5 * Math.Exp(-bi * .8) + .5 * Math.Exp(-bi * .9), Math.Exp(-bi * .85))).ToArray();
        var difference = curves.Max(p => Math.Abs(p.TwoComponentSignal - p.SingleComponentSignal));
        return new(new(maxB1E9, pointCount, diffusionBins, noisePercent), ReadOnly(singular), ReadOnly(relative),
            effectiveRank, diffusionBins - effectiveRank, numericalFloor,
            1 / reliable[^1], relative.Any(s => s <= numericalFloor), difference,
            noisePercent > 0 ? difference / (noisePercent / 100) : null, ReadOnly(curves), new(
                "Discrete point-mass kernel Kij=exp(-b_i*D_j)/sqrt(N), with 0.1-3 x10^-9 m2/s log grid. Singular values are estimated from a Jacobi eigensolve of K^T K. The tail below relative 1e-7 is unresolved: no exact full condition number is claimed. Effective rank uses max(noise fraction,1e-7) as an illustrative cutoff, not a noise-model-based resolution guarantee. Candidate decays compare two equal peaks at D=0.8/0.9 with one at 0.85. No inverse Laplace solver or regularization is performed.",
                "Núcleo discreto de masas puntuales Kij=exp(-b_i*D_j)/sqrt(N), malla logarítmica 0.1-3 x10^-9 m2/s. Valores singulares estimados con autovalores de K^T K mediante Jacobi. La cola relativa inferior a 1e-7 no está resuelta: no se afirma un número de condición completo exacto. El rango efectivo usa max(fracción de ruido,1e-7) como umbral ilustrativo, no como garantía de resolución. Se comparan dos picos iguales D=0.8/0.9 con uno en 0.85. No se ejecuta una ILT ni regularización."));
    }

    public static ExponentialFitResult FitExponential(IReadOnlyList<double> bSi, IReadOnlyList<double> signal)
    {
        ArgumentNullException.ThrowIfNull(bSi); ArgumentNullException.ThrowIfNull(signal);
        if (bSi.Count != signal.Count) throw new ArgumentException("b and signal must have the same number of points.");
        var points = new List<(double X, double Y)>(); var excluded = 0;
        for (var i = 0; i < bSi.Count; i++)
        {
            Nonnegative(bSi[i], nameof(bSi)); Finite(signal[i], nameof(signal));
            if (signal[i] > 0) points.Add((bSi[i] * 1e-9, signal[i])); else excluded++;
        }
        if (points.Count < 3) return new(null, null, null, null, null, points.Count, excluded, "insufficient_positive_points");
        var meanX = points.Average(p => p.X); var meanLogY = points.Average(p => Math.Log(p.Y));
        var xx = points.Sum(p => (p.X - meanX) * (p.X - meanX));
        if (!double.IsFinite(meanX) || !double.IsFinite(meanLogY) || !double.IsFinite(xx))
            return new(null, null, null, null, null, points.Count, excluded, "numerical_range_exceeded");
        if (xx <= 1e-20) return new(null, null, null, null, null, points.Count, excluded, "no_b_range");
        var slope = points.Sum(p => (p.X - meanX) * (Math.Log(p.Y) - meanLogY)) / xx;
        var signedD = -slope * 1e-9; var amplitude = Math.Exp(meanLogY - slope * meanX);
        var meanY = points.Average(p => p.Y);
        var sse = points.Sum(p => Math.Pow(p.Y - amplitude * Math.Exp(slope * p.X), 2));
        var sst = points.Sum(p => Math.Pow(p.Y - meanY, 2));
        if (!double.IsFinite(slope) || !double.IsFinite(amplitude) || amplitude <= 0 || !double.IsFinite(sse) || !double.IsFinite(sst))
            return new(null, null, null, null, null, points.Count, excluded, "numerical_range_exceeded");
        return new(signedD >= 0 ? signedD : null, signedD, amplitude,
            sst > 1e-24 ? 1 - sse / sst : null, Math.Sqrt(sse / points.Count), points.Count, excluded,
            signedD < 0 ? "non_physical_negative_D" : excluded > 0 ? "partial_positive_signal" : "ok");
    }

    private static double[] SymmetricEigenvalues(double[,] original)
    {
        var a = (double[,])original.Clone(); var n = a.GetLength(0);
        for (var sweep = 0; sweep < 80; sweep++)
        {
            var largestOff = 0.0; var largestDiagonal = 0.0;
            for (var p = 0; p < n; p++)
            {
                largestDiagonal = Math.Max(largestDiagonal, Math.Abs(a[p, p]));
                for (var q = p + 1; q < n; q++) largestOff = Math.Max(largestOff, Math.Abs(a[p, q]));
            }
            if (largestOff <= 1e-14 * Math.Max(1, largestDiagonal)) break;
            for (var p = 0; p < n; p++) for (var q = p + 1; q < n; q++)
            {
                var apq = a[p, q]; if (Math.Abs(apq) <= 1e-16 * Math.Max(1, largestDiagonal)) continue;
                var tau = (a[q, q] - a[p, p]) / (2 * apq);
                var t = Math.CopySign(1, tau) / (Math.Abs(tau) + Math.Sqrt(1 + tau * tau));
                var c = 1 / Math.Sqrt(1 + t * t); var s = t * c;
                a[p, p] -= t * apq; a[q, q] += t * apq; a[p, q] = a[q, p] = 0;
                for (var k = 0; k < n; k++)
                {
                    if (k == p || k == q) continue;
                    var akp = a[k, p]; var akq = a[k, q];
                    a[k, p] = a[p, k] = c * akp - s * akq;
                    a[k, q] = a[q, k] = s * akp + c * akq;
                }
            }
        }
        return Enumerable.Range(0, n).Select(i => a[i, i]).ToArray();
    }

    private static double Sinc(double x) => Math.Abs(x) < 1e-4 ? 1 - x * x / 6 + x * x * x * x / 120 : Math.Sin(x) / x;
    private static IReadOnlyList<T> ReadOnly<T>(IEnumerable<T> values) => Array.AsReadOnly(values.ToArray());
    private static void Finite(double value, string name) { if (!double.IsFinite(value)) throw new ArgumentOutOfRangeException(name, "A finite value is required."); }
    private static void Positive(double value, string name) { Finite(value, name); if (value <= 0) throw new ArgumentOutOfRangeException(name, "A positive value is required."); }
    private static void Nonnegative(double value, string name) { Finite(value, name); if (value < 0) throw new ArgumentOutOfRangeException(name, "A nonnegative value is required."); }
    private static void Noise(double value) { Nonnegative(value, "noisePercent"); if (value > 100) throw new ArgumentOutOfRangeException("noisePercent", "Use 0-100 percent."); }
    private static double Computed(double value, string name) { Finite(value, name); return value; }

    private sealed class SeededNormal(int seed)
    {
        private uint state = seed == 0 ? 0x6d2b79f5 : unchecked((uint)seed);
        private double Uniform() { state ^= state << 13; state ^= state >> 17; state ^= state << 5; return (state + 1.0) / 4294967297.0; }
        public double Next() => Math.Sqrt(-2 * Math.Log(Uniform())) * Math.Cos(2 * Math.PI * Uniform());
    }
}

public sealed record ScientificAssumptions(string English, string Spanish);
public sealed record CurvePoint(double X, double Y);
public sealed record EffectiveGradientSegment(double DurationSeconds, double EffectiveGradientTeslaPerMetre);
public sealed record GradientWaveformResult(double BSi, double ResidualAngularQ, double TotalDurationSeconds, bool BalancedEcho, ScientificAssumptions Assumptions);
public sealed record ExponentialFitResult(double? DiffusionSi, double? SignedDiffusionSi, double? Amplitude, double? R2SignalSpace, double? RmseSignalSpace, int PointsUsed, int ExcludedNonPositivePoints, string Status);
public sealed record PulseCalibrationParameters(double P180Microseconds, double TrueP90Microseconds, double NoisePercent, int Seed);
public sealed record PulseCalibrationResult(PulseCalibrationParameters Parameters, double P90FromSelectedNullMicroseconds, double TrueP90Microseconds, double First180NullMicroseconds, double Next360NullMicroseconds, bool SelectedNullIsFirst180, IReadOnlyList<CurvePoint> Curve, ScientificAssumptions Assumptions);
public sealed record GradientCalibrationParameters(double NominalMaxGradientMilliTeslaPerMetre, double DeltaMilliseconds, double BigDeltaMilliseconds, double ReferenceDiffusion1E9, double ActualToNominalGradientRatio, double NoisePercent, int Seed);
public sealed record GradientPoint(double GradientPercent, double BNominalSi, double BTrueSi, double Signal);
public sealed record GradientCalibrationResult(GradientCalibrationParameters Parameters, double TrueGradientScale, double? RecoveredGradientScale, double? NominalApparentDiffusion1E9, double? RecoveredGradientMilliTeslaPerMetre, ExponentialFitResult Fit, IReadOnlyList<GradientPoint> Points, ScientificAssumptions Assumptions);
public sealed record AttenuationDesignParameters(double GradientMilliTeslaPerMetre, double DeltaMilliseconds, double BigDeltaMilliseconds, double SlowDiffusion1E9, double FastDiffusion1E9, double NoisePercent);
public sealed record AttenuationPoint(double GradientPercent, double BSi, double SlowSignal, double FastSignal);
public sealed record AttenuationDesignResult(AttenuationDesignParameters Parameters, double BMaximumSi, double SlowEndSignal, double FastEndSignal, double? FastSignalToNoise, bool SlowAttenuatedEnough, bool FastAboveNoiseFloor, IReadOnlyList<AttenuationPoint> Points, ScientificAssumptions Assumptions);
public sealed record ConvectionParameters(double GradientMilliTeslaPerMetre, double DeltaMilliseconds, double BigDeltaMilliseconds, double Diffusion1E9, double MeanVelocityMicrometresPerSecond, double VelocityHalfWidthMicrometresPerSecond, double NoisePercent, int Seed);
public sealed record ConvectionPoint(double GradientPercent, double BSi, double AngularQ, double DiffusionSignal, double CommonVelocityReal, double CommonVelocityImaginary, double CommonVelocityMagnitude, double VelocityDispersionReal, double VelocityDispersionImaginary, double VelocityDispersionMagnitude);
public sealed record ConvectionResult(ConvectionParameters Parameters, double TrueDiffusion1E9, double? CommonMagnitudeDiffusion1E9, double? DispersionMagnitudeApparentDiffusion1E9, bool DispersionMagnitudeIsNonmonotonic, ExponentialFitResult CommonMagnitudeFit, ExponentialFitResult DispersionMagnitudeFit, IReadOnlyList<ConvectionPoint> Points, ScientificAssumptions Assumptions);
public sealed record IltConditioningParameters(double MaxB1E9, int PointCount, int DiffusionBins, double NoisePercent);
public sealed record IltCandidatePoint(double B1E9, double TwoComponentSignal, double SingleComponentSignal);
public sealed record IltConditioningResult(IltConditioningParameters Parameters, IReadOnlyList<double> SingularValues, IReadOnlyList<double> RelativeSingularValues, int EffectiveRank, int UnresolvedDirections, double NumericalRelativeFloor, double ResolvedSubspaceConditionNumber, bool HasUnresolvedSingularTail, double MaxCandidateSignalDifference, double? CandidateDifferenceToNoiseRatio, IReadOnlyList<IltCandidatePoint> CandidateCurves, ScientificAssumptions Assumptions);
