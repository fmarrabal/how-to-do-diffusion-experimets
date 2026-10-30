using System.Security.Cryptography;
using System.Text.Json;
using DiffAtOnce.Academy.Core;

var checks = new List<object>(); var failures = new List<string>();
void Check(string id, bool passed, object? evidence = null)
{
    checks.Add(new { id, passed, evidence }); if (!passed) failures.Add(id);
}
bool Near(double? value, double expected, double tolerance = 1e-10) => value is { } actual && double.IsFinite(actual) && Math.Abs(actual - expected) <= tolerance;
void Reject(string id, Action action)
{
    try { action(); Check(id, false, "Invalid input was accepted"); }
    catch (ArgumentException exception) { Check(id, true, exception.Message); }
}
string Json(object value) => JsonSerializer.Serialize(value);

var p = TeachingSimulations.PulseCalibration();
Check("manual_22_over_2_is_11", p.SelectedNullIsFirst180 && p.P90FromSelectedNullMicroseconds == 11 && p.First180NullMicroseconds == 22);
Check("signed_nutation_90_180_270_360", Near(p.Curve[50].Y, 1) && Near(p.Curve[100].Y, 0) && Near(p.Curve[150].Y, -1) && Near(p.Curve[200].Y, 0));
var wrongNull = TeachingSimulations.PulseCalibration(p180Microseconds: 44);
Check("next_null_is_not_180", !wrongNull.SelectedNullIsFirst180 && wrongNull.P90FromSelectedNullMicroseconds == 22, new { wrongNull.P90FromSelectedNullMicroseconds, wrongNull.TrueP90Microseconds });
Check("pulse_noise_reproducible", Json(TeachingSimulations.PulseCalibration(noisePercent: 2, seed: 101)) == Json(TeachingSimulations.PulseCalibration(noisePercent: 2, seed: 101)));
Check("pulse_noise_seed_changes_data", Json(TeachingSimulations.PulseCalibration(noisePercent: 2, seed: 101).Curve) != Json(TeachingSimulations.PulseCalibration(noisePercent: 2, seed: 102).Curve));
Reject("pulse_reject_zero", () => TeachingSimulations.PulseCalibration(p180Microseconds: 0));
Reject("pulse_reject_nan", () => TeachingSimulations.PulseCalibration(trueP90Microseconds: double.NaN));
Reject("noise_reject_outside_percent", () => TeachingSimulations.PulseCalibration(noisePercent: 101));

double NumericPgseB(double g, double delta, double bigDelta)
{
    // Independent trapezoidal integration of the triangular/plateau q(t),
    // without using the production PGSE formula or segment integrator.
    const int n = 200_000; var h = (bigDelta + delta) / n; var sum = 0.0;
    for (var i = 0; i <= n; i++)
    {
        var t = i * h;
        var q = TeachingSimulations.Gamma1H * g * (t < delta ? t : t < bigDelta ? delta : Math.Max(0, bigDelta + delta - t));
        sum += q * q * (i == 0 || i == n ? .5 : 1);
    }
    return sum * h;
}
foreach (var geometry in new[] { (.42, .0014, .08), (.26, .0015, .05), (.1, .005, .005), (.65, .0005, .2) })
{
    var (g, delta, bigDelta) = geometry; var analytic = TeachingSimulations.PgseB(g, delta, bigDelta); var numeric = NumericPgseB(g, delta, bigDelta);
    var segments = new List<EffectiveGradientSegment> { new(delta, g) };
    if (bigDelta > delta) segments.Add(new(bigDelta - delta, 0));
    segments.Add(new(delta, -g));
    var integrated = TeachingSimulations.SequenceB(segments);
    Check($"PGSE_independent_q_integral_{g}_{delta}_{bigDelta}", Math.Abs(analytic - numeric) / analytic < 1e-8 && Math.Abs(integrated.BSi - analytic) / analytic < 1e-12 && integrated.BalancedEcho,
        new { g, delta, bigDelta, analytic, numeric, integrated = integrated.BSi });
}
var b1 = TeachingSimulations.PgseB(.2, .002, .08);
Check("gradient_units_and_square_scaling", Near(TeachingSimulations.PgseB(.4, .002, .08) / b1, 4));
var stored = TeachingSimulations.SequenceB(new[] { new EffectiveGradientSegment(.002, .2), new EffectiveGradientSegment(.1, 0), new EffectiveGradientSegment(.002, -.2) });
var shortStored = TeachingSimulations.SequenceB(new[] { new EffectiveGradientSegment(.002, .2), new EffectiveGradientSegment(.01, 0), new EffectiveGradientSegment(.002, -.2) });
var expectedExtra = Math.Pow(TeachingSimulations.Gamma1H * .2 * .002, 2) * .09;
Check("storage_preserves_accumulated_q", Math.Abs((stored.BSi - shortStored.BSi) / expectedExtra - 1) < 1e-12);
Reject("PGSE_reject_overlapping_lobes", () => TeachingSimulations.PgseB(.42, .08, .02));
Reject("PGSE_reject_nonfinite", () => TeachingSimulations.PgseB(double.PositiveInfinity, .002, .08));
Reject("waveform_reject_unbalanced_echo", () => TeachingSimulations.SequenceB(new[] { new EffectiveGradientSegment(.002, .2) }));
Reject("waveform_reject_zero_duration", () => TeachingSimulations.SequenceB(new[] { new EffectiveGradientSegment(0, .2) }));
var unbalanced = TeachingSimulations.SequenceB(new[] { new EffectiveGradientSegment(.002, .2) }, requireBalancedEcho: false);
Check("waveform_can_report_unbalanced_diagnostic", !unbalanced.BalancedEcho && unbalanced.ResidualAngularQ > 0);
Check("unbalanced_b_not_claimed_echo_prediction", unbalanced.Assumptions.English.Contains("does not predict the echo signal") && unbalanced.Assumptions.Spanish.Contains("no predice el eco"));

var calibration = TeachingSimulations.GradientCalibration();
Check("gradient_10_percent_causes_21_percent_D", Near(calibration.NominalApparentDiffusion1E9, .8 * 1.21) && Near(calibration.RecoveredGradientScale, 1.1) && Near(calibration.RecoveredGradientMilliTeslaPerMetre, 462), calibration);
foreach (var referenceD in new[] { .3, .8, 1.9 })
{
    var result = TeachingSimulations.GradientCalibration(referenceDiffusion1E9: referenceD, actualToNominalGradientRatio: .85);
    Check($"gradient_standard_scale_recovery_{referenceD}", Near(result.RecoveredGradientScale, .85) && Near(result.NominalApparentDiffusion1E9, referenceD * .85 * .85), new { referenceD, result.RecoveredGradientScale });
}
Check("gradient_noise_reproducible", Json(TeachingSimulations.GradientCalibration(noisePercent: 1, seed: 31415)) == Json(TeachingSimulations.GradientCalibration(noisePercent: 1, seed: 31415)));
Check("gradient_noise_not_oracle", Math.Abs(TeachingSimulations.GradientCalibration(noisePercent: 1, seed: 31415).RecoveredGradientScale!.Value - 1.1) > 1e-6);
Reject("gradient_reject_nonpositive_standard_D", () => TeachingSimulations.GradientCalibration(referenceDiffusion1E9: 0));
Reject("gradient_reject_reference_SI_underflow", () => TeachingSimulations.GradientCalibration(referenceDiffusion1E9: double.Epsilon));
Reject("gradient_reject_nonfinite_scale", () => TeachingSimulations.GradientCalibration(actualToNominalGradientRatio: double.NaN));
var bs = Enumerable.Range(0, 32).Select(i => 3e9 * i / 31).ToArray();
var baselineSignal = bs.Select(b => Math.Exp(-b * .8e-9) + .03).ToArray();
var baselineFit = TeachingSimulations.FitExponential(bs, baselineSignal);
Check("good_fit_R2_does_not_remove_baseline_bias", baselineFit.R2SignalSpace > .998 && baselineFit.DiffusionSi < .8e-9 * .95 && baselineFit.DiffusionSi > .6e-9, baselineFit);
var exactFit = TeachingSimulations.FitExponential(bs, bs.Select(b => 2.1 * Math.Exp(-b * .75e-9)).ToArray());
Check("exponential_recovers_amplitude_and_D", Near(exactFit.Amplitude, 2.1) && Near(exactFit.DiffusionSi, .75e-9, 1e-20) && exactFit.RmseSignalSpace < 1e-13, exactFit);
var increasingFit = TeachingSimulations.FitExponential(bs, bs.Select(b => Math.Exp(+b * .2e-9)).ToArray());
Check("negative_D_keeps_signed_diagnostic_not_estimate", increasingFit.DiffusionSi is null && Near(increasingFit.SignedDiffusionSi, -.2e-9, 1e-20) && increasingFit.Status == "non_physical_negative_D");
Check("all_zero_signal_not_fit", TeachingSimulations.FitExponential(bs, bs.Select(_ => 0.0).ToArray()).DiffusionSi is null);
Check("no_b_range_not_fit", TeachingSimulations.FitExponential(new[] { 0.0, 0, 0 }, new[] { 1.0, 1, 1 }).Status == "no_b_range");
Reject("fit_reject_nan_signal", () => TeachingSimulations.FitExponential(new[] { 0.0, 1e9, 2e9 }, new[] { 1.0, double.NaN, .2 }));
Check("fit_extreme_finite_input_returns_unestimable_without_nan", TeachingSimulations.FitExponential(new[] { 0.0, 1e300, 2e300 }, new[] { 1.0, .5, .2 }).Status == "numerical_range_exceeded");

var design = TeachingSimulations.AttenuationDesign();
Check("attenuation_starts_at_unity_and_is_monotonic", design.Points[0].SlowSignal == 1 && design.Points[0].FastSignal == 1 && design.Points.Zip(design.Points.Skip(1)).All(pair => pair.Second.SlowSignal <= pair.First.SlowSignal && pair.Second.FastSignal <= pair.First.FastSignal));
Check("slow_and_fast_signals_have_correct_order", design.Points.All(p => p.SlowSignal >= p.FastSignal && p.FastSignal is >= 0 and <= 1));
Check("SNR_uses_fraction_not_percent", Near(design.FastSignalToNoise, design.FastEndSignal / .01));
Check("longer_delta_can_lose_fast_component", !TeachingSimulations.AttenuationDesign(deltaMilliseconds: 5, bigDeltaMilliseconds: 80).FastAboveNoiseFloor);
var zeroGradient = TeachingSimulations.AttenuationDesign(gradientMilliTeslaPerMetre: 0, noisePercent: 0);
Check("zero_gradient_uninformative_and_noisefree_SNR_not_infinity", zeroGradient.BMaximumSi == 0 && !zeroGradient.SlowAttenuatedEnough && zeroGradient.FastSignalToNoise is null && zeroGradient.Points.All(p => p.SlowSignal == 1));
Reject("design_reject_reversed_diffusion_names", () => TeachingSimulations.AttenuationDesign(slowDiffusion1E9: 2, fastDiffusion1E9: 1));

foreach (var meanVelocity in new[] { -1200.0, 0, 150, 1200 })
{
    var flow = TeachingSimulations.Convection(meanVelocityMicrometresPerSecond: meanVelocity, velocityHalfWidthMicrometresPerSecond: 0);
    Check($"fixed_velocity_preserves_noiseless_magnitude_D_{meanVelocity}", Near(flow.CommonMagnitudeDiffusion1E9, .8) && flow.Points.All(p => Math.Abs(p.CommonVelocityMagnitude - p.DiffusionSignal) < 1e-14), new { meanVelocity, flow.CommonMagnitudeDiffusion1E9 });
    Check($"zero_velocity_width_matches_common_magnitude_{meanVelocity}", flow.Points.All(p => Math.Abs(p.CommonVelocityMagnitude - p.VelocityDispersionMagnitude) < 1e-14));
}
var flowReal = TeachingSimulations.Convection(meanVelocityMicrometresPerSecond: 150, velocityHalfWidthMicrometresPerSecond: 0);
Check("real_channel_can_change_sign_without_magnitude_loss", flowReal.Points.Any(p => p.CommonVelocityReal < 0) && Near(flowReal.CommonMagnitudeDiffusion1E9, .8));
var spreadFlow = TeachingSimulations.Convection();
var last = spreadFlow.Points[^1];
const int velocitySamples = 100_000; var numericReal = 0.0; var numericImaginary = 0.0;
for (var i = 0; i < velocitySamples; i++)
{
    var v = (35 - 300 + 600 * (i + .5) / velocitySamples) * 1e-6;
    var phase = last.AngularQ * .08 * v;
    numericReal += Math.Cos(phase); numericImaginary += Math.Sin(phase);
}
numericReal *= last.DiffusionSignal / velocitySamples; numericImaginary *= last.DiffusionSignal / velocitySamples;
Check("uniform_velocity_characteristic_matches_numeric_quadrature", Math.Abs(numericReal - last.VelocityDispersionReal) < 1e-10 && Math.Abs(numericImaginary - last.VelocityDispersionImaginary) < 1e-10,
    new { numericReal, numericImaginary, last.VelocityDispersionReal, last.VelocityDispersionImaginary });
Check("uniform_velocity_has_nonmonotonic_nodes_and_apparent_D", spreadFlow.DispersionMagnitudeIsNonmonotonic && Math.Abs(spreadFlow.DispersionMagnitudeApparentDiffusion1E9!.Value - spreadFlow.TrueDiffusion1E9) > .1, new { spreadFlow.DispersionMagnitudeApparentDiffusion1E9, spreadFlow.TrueDiffusion1E9 });
Check("convection_noise_reproducible", Json(TeachingSimulations.Convection(noisePercent: 2, seed: 55)) == Json(TeachingSimulations.Convection(noisePercent: 2, seed: 55)));
Reject("convection_reject_negative_width", () => TeachingSimulations.Convection(velocityHalfWidthMicrometresPerSecond: -1));
Reject("convection_reject_nonfinite_velocity", () => TeachingSimulations.Convection(meanVelocityMicrometresPerSecond: double.NaN));

var ilt = TeachingSimulations.InverseLaplaceConditioning();
Check("ILT_singular_values_sorted_and_finite", ilt.SingularValues.All(double.IsFinite) && ilt.SingularValues.Zip(ilt.SingularValues.Skip(1)).All(pair => pair.First >= pair.Second) && ilt.RelativeSingularValues[0] == 1);
Check("ILT_effective_rank_lower_than_unknowns", ilt.EffectiveRank < 10 && ilt.UnresolvedDirections == 40 - ilt.EffectiveRank && ilt.HasUnresolvedSingularTail, new { ilt.EffectiveRank, ilt.UnresolvedDirections, ilt.ResolvedSubspaceConditionNumber });
var lowerNoise = TeachingSimulations.InverseLaplaceConditioning(noisePercent: .1);
var higherNoise = TeachingSimulations.InverseLaplaceConditioning(noisePercent: 10);
Check("ILT_noise_threshold_removes_effective_directions", lowerNoise.EffectiveRank > higherNoise.EffectiveRank, new { lowNoiseRank = lowerNoise.EffectiveRank, highNoiseRank = higherNoise.EffectiveRank });
var rankOne = TeachingSimulations.InverseLaplaceConditioning(maxB1E9: 0);
Check("ILT_no_b_range_rank_one_closed_form", rankOne.EffectiveRank == 1 && Near(rankOne.SingularValues[0], Math.Sqrt(40), 1e-10));
var expectedFrobeniusSquared = 0.0;
for (var i = 0; i < 32; i++) for (var j = 0; j < 40; j++)
    expectedFrobeniusSquared += Math.Exp(-2 * (3.0 * i / 31) * (.1 * Math.Pow(30, j / 39.0))) / 32;
Check("ILT_SVD_energy_matches_kernel_Frobenius_norm", Math.Abs(ilt.SingularValues.Sum(s => s * s) / expectedFrobeniusSquared - 1) < 1e-12,
    new { expectedFrobeniusSquared, actual = ilt.SingularValues.Sum(s => s * s) });
using (var fixture = JsonDocument.Parse(File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "ilt-numpy-reference.json"))))
{
    var expected = fixture.RootElement.GetProperty("singular_values").EnumerateArray().Select(v => v.GetDouble()).ToArray();
    var relativeErrors = expected.Select((v, i) => Math.Abs(ilt.SingularValues[i] / v - 1)).ToArray();
    Check("ILT_leading_SVD_values_match_independent_NumPy", relativeErrors.All(e => e < 2e-5), new { expected, actual = ilt.SingularValues.Take(expected.Length), relativeErrors, tail_not_compared = "The production Gram method declares relative <1e-7 unresolved" });
}
Check("ILT_two_distinct_distributions_can_hide_below_noise", ilt.MaxCandidateSignalDifference > 0 && ilt.CandidateDifferenceToNoiseRatio < 1 && ilt.CandidateCurves.All(p => p.TwoComponentSignal >= p.SingleComponentSignal - 1e-15), new { ilt.MaxCandidateSignalDifference, ilt.CandidateDifferenceToNoiseRatio });
Reject("ILT_reject_nonfinite_range", () => TeachingSimulations.InverseLaplaceConditioning(maxB1E9: double.PositiveInfinity));
Reject("ILT_reject_unbounded_grid", () => TeachingSimulations.InverseLaplaceConditioning(diffusionBins: 100_000));
Check("all_synthetic_outputs_serialize_without_nonfinite_values", new object[] { p, calibration, design, spreadFlow, ilt }.All(value => !Json(value).Contains("NaN")));

var sourcePath = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "../../../../../src/DiffAtOnce.Academy.Core/TeachingSimulations.cs"));
var sourceHash = File.Exists(sourcePath) ? Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(sourcePath))).ToLowerInvariant() : null;
var report = new
{
    checked_utc = DateTimeOffset.UtcNow, scientific_status = TeachingSimulations.ScientificStatus,
    scope = "Native C# synthetic teaching models, independent quadrature/closed-form checks; no experimental, WPF GUI, instrument or production validation",
    source = "src/DiffAtOnce.Academy.Core/TeachingSimulations.cs", source_sha256 = sourceHash,
    checks, failures, passed = failures.Count == 0
};
var reportPath = args.Length == 2 && args[0] == "--report" ? Path.GetFullPath(args[1]) : Path.Combine(AppContext.BaseDirectory, "teaching-simulations-qa.json");
Directory.CreateDirectory(Path.GetDirectoryName(reportPath)!);
File.WriteAllText(reportPath, JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }));
Console.WriteLine(JsonSerializer.Serialize(new { passed = failures.Count == 0, checks = checks.Count, failures, report = reportPath, source_sha256 = sourceHash }, new JsonSerializerOptions { WriteIndented = true }));
return failures.Count == 0 ? 0 : 1;
