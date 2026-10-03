# -*- coding: utf-8 -*-
"""Read-only DOSY reference calibration, compatible with Jython 2.7 / Python 3.

No TopSpin imports or third-party dependencies. No files are modified here.
The fitted empirical b coefficient applies only to the recorded pulse sequence,
gradient shape, probe and timings. It is NOT a universal gradient constant.
"""
from __future__ import division

import hashlib
import math
import os
import re
import struct

VERSION = "1.0.0"


class CalibrationError(ValueError):
    """Input cannot safely support this calibration workflow."""


def _finite(value, label, positive=False):
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError):
        raise CalibrationError("%s must be a finite number" % label)
    if math.isnan(value) or math.isinf(value) or (positive and value <= 0):
        raise CalibrationError("%s must be %sfinite" %
                               (label, "positive and " if positive else ""))
    return value


def _integer(value, label, minimum=None):
    number = _finite(value, label)
    if number != int(number) or (minimum is not None and number < minimum):
        raise CalibrationError("%s must be an integer >= %s" % (label, minimum))
    return int(number)


def _read_bytes(path):
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except (IOError, OSError) as exc:
        raise CalibrationError("Cannot read %s: %s" % (path, exc))


def _source(path, content):
    return {"path": os.path.abspath(path), "sha256": hashlib.sha256(content).hexdigest(),
            "bytes": len(content)}


def _token(value):
    value = value.strip()
    if value.startswith("<") and value.endswith(">"):
        return value[1:-1]
    if re.match(r"^[+-]?\d+$", value):
        return int(value)
    try:
        return float(value.replace("D", "E").replace("d", "e"))
    except ValueError:
        return value


def parse_jcamp(text):
    """Parse status parameters, including multiline <strings> and indexed arrays.

    Unknown scalar strings are retained. Unsupported array compression or a
    mismatched declared length is rejected, never silently reindexed.
    """
    records = {}
    key = None
    body = []
    # Strip comments only outside angle-bracket strings; '$$' can occur in paths.
    in_string = False
    for raw in text.splitlines():
        clean = []
        pos = 0
        while pos < len(raw):
            char = raw[pos]
            if not in_string and raw[pos:pos + 2] == "$$":
                break
            clean.append(char)
            if char == "<":
                in_string = True
            elif char == ">":
                in_string = False
            pos += 1
        line = "".join(clean)
        match = re.match(r"^##\$([^=]+)=\s*(.*)$", line)
        if match or line.startswith("##"):
            if key is not None:
                records[key] = "\n".join(body).strip()
            key = match.group(1).strip() if match else None
            body = [match.group(2)] if match else []
        elif key is not None:
            body.append(line)
    if key is not None:
        records[key] = "\n".join(body).strip()
    if in_string:
        raise CalibrationError("Unterminated JCAMP angle-bracket string")
    result = {}
    for key, value in records.items():
        array = re.match(r"^\(\s*(\d+)\s*\.\.\s*(\d+)\s*\)\s*(.*)$", value, re.S)
        if array:
            start, end = int(array.group(1)), int(array.group(2))
            if end < start or end > 1000000:
                raise CalibrationError("Invalid JCAMP array bounds: %s" % key)
            tokens = re.findall(r"<[^>]*>|[^\s]+", array.group(3), re.S)
            if len(tokens) != end - start + 1:
                raise CalibrationError("JCAMP array %s has %s values, expected %s" %
                                       (key, len(tokens), end - start + 1))
            result[key] = [None] * start + [_token(item) for item in tokens]
        elif value.startswith("("):
            raise CalibrationError("Unsupported JCAMP array declaration: %s" % key)
        else:
            result[key] = _token(value)
    return result


def read_jcamp(path):
    content = _read_bytes(path)
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("cp1252")
    return parse_jcamp(text), _source(path, content)


def _required(parameters, key, index=None):
    name = key if index is None else "%s%s" % (key, index)
    if index is not None and name in parameters:
        value = parameters[name]
    elif key not in parameters:
        raise CalibrationError("Missing required status parameter %s" % name)
    elif index is None:
        value = parameters[key]
    else:
        array = parameters[key]
        if not isinstance(array, list) or len(array) <= index:
            raise CalibrationError("Missing required indexed parameter %s" % name)
        value = array[index]
    if value is None or value == "":
        raise CalibrationError("Empty required status parameter %s" % name)
    return value


def read_processed_1r(experiment_dir, procno=1):
    """Read one acquired, processed real 1D spectrum and its provenance.

    1i is a normal separate imaginary component and may coexist with 1r.
    Multidimensional spectra, extracted regions and ambiguous layouts reject.
    DTYPP=0: int32 * 2**NC_proc. DTYPP=2: float64 directly (NC_proc ignored).
    """
    procno = _integer(procno, "PROCNO", 1)
    experiment_dir = os.path.abspath(experiment_dir)
    pdata = os.path.join(experiment_dir, "pdata", str(procno))
    acqus, asource = read_jcamp(os.path.join(experiment_dir, "acqus"))
    procs, psource = read_jcamp(os.path.join(pdata, "procs"))
    if _integer(_required(acqus, "PARMODE"), "PARMODE") != 0:
        raise CalibrationError("Only acquired 1D experiments (PARMODE=0) are supported")
    for name in ("proc2s", "proc3s", "2rr", "3rrr", "2ri", "2ir", "2ii"):
        if os.path.exists(os.path.join(pdata, name)):
            raise CalibrationError("Multidimensional/extracted layout is unsupported: %s" % name)
    si = _integer(_required(procs, "SI"), "SI", 2)
    if si > 16777216:
        raise CalibrationError("SI exceeds the supported in-memory 1D size")
    for name in ("STSI", "FTSIZE"):
        if name in procs and _integer(procs[name], name) not in (0, si):
            raise CalibrationError("Extracted/cropped processing layout: %s differs from SI" % name)
    if "STSR" in procs and _integer(procs["STSR"], "STSR") != 0:
        raise CalibrationError("Extracted/cropped processing layout: STSR is not zero")
    if not _same(procs.get("AXLEFT", 0), procs.get("AXRIGHT", 0)):
        raise CalibrationError("Custom AXLEFT/AXRIGHT axis is unsupported; use the frequency ppm axis")
    if "FT_mod" in procs and _integer(procs["FT_mod"], "FT_mod") == 0:
        raise CalibrationError("The spectrum has no Fourier-transform status")
    sf = _finite(_required(procs, "SF"), "SF (MHz)", True)
    sw = _finite(_required(procs, "SW_p"), "SW_p (Hz)", True)
    offset = _finite(_required(procs, "OFFSET"), "OFFSET (ppm)")
    nc = _integer(_required(procs, "NC_proc"), "NC_proc")
    dtype = _integer(_required(procs, "DTYPP"), "DTYPP")
    order = _integer(_required(procs, "BYTORDP"), "BYTORDP")
    if dtype not in (0, 2) or order not in (0, 1):
        raise CalibrationError("Supported layouts: DTYPP=0/2 and BYTORDP=0/1 only")
    try:
        scale = math.ldexp(1.0, nc) if dtype == 0 else 1.0
    except (OverflowError, ValueError):
        raise CalibrationError("Invalid NC_proc scale")
    if scale == 0 or math.isinf(scale):
        raise CalibrationError("NC_proc scale is outside floating-point range")
    itemsize, code = (4, "i") if dtype == 0 else (8, "d")
    path = os.path.join(pdata, "1r")
    content = _read_bytes(path)
    expected = si * itemsize
    if len(content) != expected:
        padded = ((expected + 1023) // 1024) * 1024
        tail = content[expected:]
        if len(content) != padded or len(content) < expected or tail.strip(b"\x00"):
            raise CalibrationError("1r size/layout mismatch: %s bytes, expected %s" %
                                   (len(content), expected))
    endian = "<" if order == 0 else ">"
    # Chunk unpacking avoids a huge struct format and works on Jython 2.7.
    values = []
    for start in range(0, si, 4096):
        count = min(4096, si - start)
        chunk = struct.unpack(endian + str(count) + code,
                              content[start * itemsize:(start + count) * itemsize])
        for value in chunk:
            values.append(_finite(value * scale, "scaled 1r point"))
    step = sw / sf / si
    sources = [asource, psource, _source(path, content)]
    saved_files = {}
    for name in ("pulseprogram", "gpnam6"):
        saved = os.path.join(experiment_dir, name)
        if os.path.isfile(saved):
            entry = _source(saved, _read_bytes(saved))
            saved_files[name] = entry["sha256"]
            sources.append(entry)
    return {"values": values, "ppm_start": offset, "ppm_step": step,
            "ppm_end": offset - (si - 1) * step,
            "acquisition": acqus, "processing": procs, "sources": sources,
            "saved_file_hashes": saved_files}


def integrate_region(spectrum, ppm_low, ppm_high):
    """Signed trapezoidal area in intensity*ppm with exact interpolated bounds."""
    low = _finite(ppm_low, "ppm_low")
    high = _finite(ppm_high, "ppm_high")
    if low >= high:
        raise CalibrationError("ppm_low must be less than ppm_high")
    start, step, end = spectrum["ppm_start"], spectrum["ppm_step"], spectrum["ppm_end"]
    values = spectrum["values"]
    tolerance = 1e-10 * max(1.0, abs(start), abs(end))
    if low < end - tolerance or high > start + tolerance:
        raise CalibrationError("The full %.9g..%.9g ppm window is outside %.9g..%.9g ppm" %
                               (low, high, end, start))
    a = min(len(values) - 1.0, max(0.0, (start - high) / step))
    b = min(len(values) - 1.0, max(0.0, (start - low) / step))
    if b - a < 2:
        raise CalibrationError("Integration window must span at least two spectral intervals")
    def at(index):
        left = int(math.floor(index))
        right = min(left + 1, len(values) - 1)
        return values[left] + (index - left) * (values[right] - values[left])
    previous_x, previous_y = a, at(a)
    areas = []
    for index in range(int(math.floor(a)) + 1, int(math.ceil(b))):
        value = values[index]
        areas.append((index - previous_x) * (previous_y + value) * 0.5)
        previous_x, previous_y = float(index), value
    areas.append((b - previous_x) * (previous_y + at(b)) * 0.5)
    area = _finite(math.fsum(areas) * step, "signed integral", True)
    return {"integral": area, "unit": "scaled_intensity*ppm", "ppm_low": low,
            "ppm_high": high, "intervals": b - a,
            "method": "signed trapezoid with linear boundary interpolation; no abs, baseline or normalization"}


def fit_attenuation(gradient_percent, intensities):
    """Unweighted free-intercept OLS of log(I/Imax) vs (GPZ6/100)^2."""
    if len(gradient_percent) != len(intensities) or len(intensities) < 4:
        raise CalibrationError("At least four paired attenuation points are required")
    gradients = [_finite(v, "gradient percentage") for v in gradient_percent]
    if any(abs(v) > 100 for v in gradients):
        raise CalibrationError("Absolute gradient percentages must not exceed 100")
    values = [_finite(v, "integral", True) for v in intensities]
    x = [(v / 100.0) ** 2 for v in gradients]
    if len(set(round(v, 12) for v in x)) < 4:
        raise CalibrationError("At least four distinct squared gradient amplitudes are required")
    maximum = max(values)
    y = [math.log(v) - math.log(maximum) for v in values]
    n = len(x)
    xmean, ymean = math.fsum(x) / n, math.fsum(y) / n
    sxx = math.fsum((v - xmean) ** 2 for v in x)
    if sxx <= 1e-24:
        raise CalibrationError("Gradient span is too small for stable calibration")
    syy = math.fsum((v - ymean) ** 2 for v in y)
    slope = math.fsum((a - xmean) * (b - ymean) for a, b in zip(x, y)) / sxx
    if slope >= 0 or syy <= 1e-24:
        raise CalibrationError("Calibration requires a nonzero, decreasing attenuation")
    intercept = ymean - slope * xmean
    fitted_log = [intercept + slope * v for v in x]
    residuals = [a - b for a, b in zip(y, fitted_log)]
    sse = math.fsum(v * v for v in residuals)
    stderr = math.sqrt(max(0.0, sse / (n - 2) / sxx))
    try:
        predicted = [math.exp(math.log(maximum) + v) for v in fitted_log]
        zero = math.exp(math.log(maximum) + intercept)
    except OverflowError:
        raise CalibrationError("Extrapolated I(0) or predicted intensity overflows")
    return {"model": "ln(I/Imax) = intercept + slope * (GPZ6/100)^2",
            "weighting": "unweighted ordinary least squares in log intensity",
            "n": n, "distinct_x": len(set(x)), "x": x, "log_relative_intensity": y,
            "slope": slope, "slope_abs": -slope, "slope_SE": stderr,
            "intercept_log_I_over_Imax": intercept, "Imax": maximum,
            "I0_extrapolated": zero, "R2": 1.0 - sse / syy,
            "degrees_of_freedom": n - 2, "residuals_log": residuals,
            "predicted_integrals": predicted, "observed_integrals": values,
            "relative_slope_uncertainty_1sigma": stderr / abs(slope),
            "relative_attenuation_last_over_first": values[-1] / values[0],
            "uncertainty_scope": "Regression standard error only; excludes Dref, temperature, processing and systematic uncertainty"}


def _metadata(spectrum):
    a = spectrum["acquisition"]
    result = {}
    for key in ("PULPROG", "PROBHD", "NUC1"):
        value = _required(a, key)
        if not isinstance(value, type(u"")) and not isinstance(value, str):
            raise CalibrationError("%s must be a string" % key)
        result[key] = value.strip()
    result["GPNAM6"] = _required(a, "GPNAM", 6)
    for key, array, index in (("D20", "D", 20), ("D16", "D", 16),
                              ("P30", "P", 30), ("GPZ6", "GPZ", 6)):
        result[key] = _finite(_required(a, array, index), key)
    for key in ("RG", "NS", "TE"):
        result[key] = _finite(_required(a, key), key, True)
    if result["D20"] <= 0 or result["P30"] <= 0 or result["D16"] < 0:
        raise CalibrationError("D20/P30 must be positive and D16 nonnegative")
    result["NS"] = _integer(result["NS"], "NS", 1)
    # These parameters can affect amplitudes; if supplied require them constant.
    for key in ("DS", "AQ_mod", "TD", "SW_h", "SFO1"):
        if key in a:
            result[key] = a[key]
    for key, index in (("D1", 1),):
        if "D" in a and isinstance(a["D"], list) and len(a["D"]) > index:
            result[key] = a["D"][index]
    # Preserve and compare every saved pulse delay, pulse duration and gradient
    # component/shape. Only the GPZ6 amplitude is allowed to vary in this ramp.
    pulse_gradient = {}
    array_names = ("D", "P", "GPX", "GPY", "GPZ", "GPNAM")
    for key in a:
        if key in array_names:
            if not isinstance(a[key], list):
                raise CalibrationError("Expected indexed parameter array %s" % key)
            items = list(a[key])
            if key == "GPZ" and len(items) > 6:
                items[6] = None
            pulse_gradient[key] = items
        elif re.match(r"^(D|P|GPX|GPY|GPZ|GPNAM)\d+$", key) and key != "GPZ6":
            pulse_gradient[key] = a[key]
    result["pulse_gradient_parameters"] = pulse_gradient
    return result


def _same(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= 1e-10 * max(1.0, abs(a), abs(b))
    return a == b


def analyze_series(dataset_dir, expnos, procno, ppm_low, ppm_high, dref_1e9,
                   reference_temperature_K, reference_label,
                   max_temperature_span_K=0.5,
                   max_reference_temperature_difference_K=0.5):
    """Integrate and calibrate a single constant-timing gradient ramp.

    Dref in 10^-9 m^2/s must refer to the explicitly entered reference temperature.
    TE is recorded spectrometer metadata, not an independent sample thermometer.
    Thresholds may be changed explicitly; temperature is never corrected silently.
    """
    dref = _finite(dref_1e9, "Dref (10^-9 m^2/s)", True)
    tref = _finite(reference_temperature_K, "reference temperature (K)", True)
    tspan = _finite(max_temperature_span_K, "maximum temperature span")
    tdiff = _finite(max_reference_temperature_difference_K, "maximum reference temperature difference")
    if tspan < 0 or tdiff < 0:
        raise CalibrationError("Temperature tolerances must be nonnegative")
    if not reference_label or not reference_label.strip():
        raise CalibrationError("A reference identity/source label is required")
    numbers = [_integer(v, "EXPNO", 1) for v in expnos]
    if len(numbers) < 4 or len(set(numbers)) != len(numbers):
        raise CalibrationError("Provide at least four different experiment numbers")
    rows, sources, warnings = [], [], []
    baseline, processing_baseline, saved_baseline = None, None, None
    processing_keys = ("SI", "FTSIZE", "SF", "SW_p", "OFFSET", "FT_mod", "WDW",
                       "LB", "GB", "SSB", "BC_mod", "PH_mod")
    processing_record = ("PHC0", "PHC1", "ABSF1", "ABSF2", "ABSG", "ABSL", "INTBC",
                         "NC_proc", "DTYPP", "BYTORDP") + processing_keys
    varying_processing = set()
    first_processing = None
    for expno in numbers:
        try:
            spectrum = read_processed_1r(os.path.join(dataset_dir, str(expno)), procno)
            meta = _metadata(spectrum)
            area = integrate_region(spectrum, ppm_low, ppm_high)
        except CalibrationError as exc:
            raise CalibrationError("EXPNO %s: %s" % (expno, exc))
        processing = dict((k, spectrum["processing"].get(k)) for k in processing_record)
        stable = dict((k, v) for k, v in meta.items() if k not in ("GPZ6", "TE", "DS"))
        stable_processing = dict((k, processing[k]) for k in processing_keys)
        saved = spectrum["saved_file_hashes"]
        if baseline is None:
            baseline, processing_baseline, saved_baseline = stable, stable_processing, saved
            first_processing = processing
        else:
            for key in set(baseline) | set(stable):
                if not _same(baseline.get(key), stable.get(key)):
                    raise CalibrationError("EXPNO %s: inconsistent %s across the calibration ramp" % (expno, key))
            for key in processing_keys:
                if not _same(processing_baseline[key], stable_processing[key]):
                    raise CalibrationError("EXPNO %s: inconsistent processing %s; reprocess consistently" % (expno, key))
            if saved != saved_baseline:
                raise CalibrationError("EXPNO %s: saved pulseprogram/gpnam6 provenance differs or is missing" % expno)
            for key in ("PHC0", "PHC1", "ABSF1", "ABSF2", "ABSG", "ABSL", "INTBC"):
                if not _same(first_processing[key], processing[key]):
                    varying_processing.add(key)
        rows.append({"expno": expno, "procno": int(procno), "gradient_percent": meta["GPZ6"],
                     "x_gradient_fraction_squared": (meta["GPZ6"] / 100.0) ** 2,
                     "integral": area["integral"], "integration": area,
                     "acquisition": meta, "processing": processing,
                     "saved_file_hashes": saved})
        sources.extend(spectrum["sources"])
    temperatures = [row["acquisition"]["TE"] for row in rows]
    tmin, tmax = min(temperatures), max(temperatures)
    tmean = math.fsum(temperatures) / len(temperatures)
    if tmax - tmin > tspan + 1e-9:
        raise CalibrationError("TE drift %.6g K exceeds %.6g K; stabilize temperature or explicitly reassess tolerance/reference" %
                               (tmax - tmin, tspan))
    if max(abs(t - tref) for t in temperatures) > tdiff + 1e-9:
        raise CalibrationError("Reference temperature %.6g K differs from recorded TE by more than %.6g K; supply the appropriate Dref(T)" %
                               (tref, tdiff))
    fit = fit_attenuation([r["gradient_percent"] for r in rows], [r["integral"] for r in rows])
    for i, row in enumerate(rows):
        row["log_relative_intensity"] = fit["log_relative_intensity"][i]
        row["predicted_integral"] = fit["predicted_integrals"][i]
        row["residual_log"] = fit["residuals_log"][i]
    coefficient = fit["slope_abs"] / (dref * 1e-9)
    b_se = fit["slope_SE"] / (dref * 1e-9)
    if varying_processing:
        warnings.append("Phase/baseline status varies: %s. Inspect every spectrum before accepting." % ", ".join(sorted(varying_processing)))
    if len(saved_baseline) != 2:
        warnings.append("Saved pulseprogram and/or gpnam6 are absent. Scope uses parameter names; physical gradient conversion is unavailable.")
    if len(set(row["acquisition"].get("DS") for row in rows)) > 1:
        warnings.append("DS differs across the ramp. Verify steady-state preparation; amplitudes were not normalized by dummy scans.")
    if fit["R2"] < 0.98:
        warnings.append("R2 < 0.98: inspect residuals, overlap, baseline, convection and signal-to-noise; no automatic acceptance.")
    if fit["relative_slope_uncertainty_1sigma"] > 0.05:
        warnings.append("Regression slope relative standard error exceeds 5%; review the ramp and reference signal.")
    if tmax - tmin > 0.1:
        warnings.append("Recorded TE varies by %.4g K. A single supplied Dref is used; no thermal correction was inferred." % (tmax - tmin))
    warnings.append("Positive signed area and a good fit do not establish peak purity or signal-to-noise. Inspect spectra and residuals.")
    profile = {"kind": "empirical_b_per_gradient_fraction_squared",
               "b_at_100_percent_s_m2": coefficient, "b_coefficient_SE_s_m2": b_se,
               "definition": "b(g) = b_at_100_percent_s_m2 * (GPZ6/100)^2",
               "Dref_1e9_m2_s": dref, "reference_temperature_K": tref,
               "reference_label": reference_label.strip(),
               "Dref_uncertainty": "not supplied; excluded from reported standard error",
               "scope": dict(baseline), "saved_file_hashes": saved_baseline,
               "transfer_policy": "Same pulse sequence, timings, gradient shape and probe only; not transferable across big Delta or small delta without a verified pulse-sequence model",
               "bruker_gradient_constant": None,
               "status": "candidate requiring spectral and residual review; not written to gradpar"}
    return {"schema_version": 1, "software": "DiffAtOnce TopSpin DOSY calibration " + VERSION,
            "dataset_dir": os.path.abspath(dataset_dir), "procno": int(procno),
            "expnos": numbers, "ppm_region": {"low": float(ppm_low), "high": float(ppm_high)},
            "rows": rows, "fit": fit, "calibration_profile": profile,
            "temperature": {"source": "acqus TE status; not independent sample thermometry",
                            "minimum_K": tmin, "maximum_K": tmax, "mean_K": tmean,
                            "span_K": tmax - tmin, "reference_K": tref,
                            "max_span_allowed_K": tspan, "max_reference_difference_allowed_K": tdiff,
                            "correction_applied": False},
            "warnings": warnings, "sources": sources,
            "provenance_policy": "All inputs read-only; SHA-256 refers to bytes used for this calculation"}


def gradient_correction(old_gradient_constant, measured_diffusion, reference_diffusion,
                        gradient_unit="G/cm", diffusion_unit="10^-9 m^2/s"):
    """Separate ratio correction; Dmeasured and Dref must use the same units.

    Dmeasured must have been fitted using old_gradient_constant. This function
    does not derive Dmeasured from the empirical slope or alter TopSpin settings.
    """
    old = _finite(old_gradient_constant, "old gradient constant", True)
    measured = _finite(measured_diffusion, "measured diffusion", True)
    reference = _finite(reference_diffusion, "reference diffusion", True)
    factor = math.sqrt(measured / reference)
    new = _finite(old * factor, "new gradient constant", True)
    return {"old_gradient_constant": old, "new_gradient_constant": new,
            "gradient_unit": gradient_unit, "measured_diffusion": measured,
            "reference_diffusion": reference, "diffusion_unit": diffusion_unit,
            "factor": factor, "formula": "G_new = G_old * sqrt(D_measured / D_reference)",
            "assumption": "D_measured was evaluated using G_old, matching reference temperature and the correct pulse-sequence b model",
            "written_to_spectrometer": False}
