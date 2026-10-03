# -*- coding: utf-8 -*-
"""Native TopSpin Jython 2.7 calibration workflows. Hardware is opt-in in UI.

Use a preconfigured 1D template. Copy parameters to NEW EXPNO only, acquire
sequentially with WAIT_TILL_DONE, process using fixed phase, then analyze.
No global gradient or RF calibration setting is written by this script.
"""
from __future__ import division, unicode_literals
import hashlib
import io
import json
import math
import os
import sys

import _dosy_ramp_engine as engine
import _dosy_calibration as calibration
import _dosy_console_ui as legacy

try:
    text_type = unicode
except NameError:
    text_type = str


def build_plan(current, mode, first_expno, values, expected_program):
    if mode not in ("p1", "gradient"):
        raise ValueError("Mode must be p1 or gradient")
    if len(current) != 4:
        raise ValueError("CURDATA must have four fields")
    current = [text_type(v) for v in current]
    dataset_dir = os.path.realpath(os.path.join(current[3], current[0]))
    if current[0] in (".", "..") or any(c in current[0] for c in ("/", "\\", "\x00")):
        raise ValueError("Invalid dataset name")
    first = engine.integer(first_expno, "First EXPNO")
    template_expno = engine.integer(current[1], "Template EXPNO")
    procno = engine.integer(current[2], "PROCNO")
    if not 4 <= len(values) <= 500:
        raise ValueError("Provide 4..500 calibration points")
    numeric = [engine.number(v, "Sweep value", positive=(mode == "p1")) for v in values]
    if len(set(numeric)) != len(numeric) or sorted(numeric) != numeric:
        raise ValueError("Sweep values must be distinct and increasing")
    if mode == "gradient" and (numeric[0] < 0 or numeric[-1] > 100):
        raise ValueError("GPZ6 range must be inside 0..100 percent")
    if mode == "p1" and expected_program != "zg":
        raise ValueError("The P1 nutation workflow requires the simple zg pulse program")
    if not expected_program or not expected_program.strip():
        raise ValueError("Explicit pulse-program identity is required")
    rows = [{"point": i + 1, "expno": first + i, "procno": procno,
             "parameter": "P 1" if mode == "p1" else "GPZ 6", "value": value}
            for i, value in enumerate(numeric)]
    if any(r["expno"] == template_expno for r in rows):
        raise ValueError("A destination overlaps the template")
    return {"schema_version": 3, "mode": mode, "template": current,
            "dataset_dir": dataset_dir, "expected_program": expected_program,
            "rows": rows, "values": numeric, "unit": "us" if mode == "p1" else "percent",
            "processing": "EFP with inherited PHC0/PHC1, no independent autophase or baseline fitting",
            "hardware_actions": "Only if operator chooses acquire: ZG(wait=WAIT_TILL_DONE), then EFP(wait=WAIT_TILL_DONE)",
            "global_calibration_modified": False}


def paths_for(plan):
    return [os.path.join(plan["dataset_dir"], text_type(row["expno"])) for row in plan["rows"]]


def dataset_for(plan, row):
    original = plan["template"]
    return [original[0], text_type(row["expno"]), text_type(row["procno"]), original[3]]


def assert_dataset(api, expected):
    if not engine.equivalent_dataset(api.CURDATA(), expected):
        raise RuntimeError("Current dataset changed unexpectedly; workflow stopped")


def verify_parameters(api, fixed, identities, row=None):
    for key, value in fixed.items():
        observed = engine.finite_number(api.GETPAR(key))
        if abs(observed - value) > 1e-9 * max(1.0, abs(value)):
            raise RuntimeError("Fixed template parameter changed: " + key)
    for key, value in identities.items():
        observed = text_type(api.GETPAR(key)).strip().strip("<>")
        if observed != value:
            raise RuntimeError("Template identity changed: " + key)
    if row is not None:
        observed = engine.finite_number(api.GETPAR(row["parameter"]))
        if abs(observed - row["value"]) > 1e-8 * max(1.0, abs(row["value"])):
            raise RuntimeError("Sweep value changed before acquisition: " + row["parameter"])


def checked_command(api, method_name):
    """Conservative completion rule: synchronous documented command and rc=0.

    Unknown/None command status stops the run. An on-instrument pilot must check
    acquisition return semantics for the installed TopSpin version; mere fid
    existence cannot distinguish an aborted acquisition from a completed one.
    """
    command = getattr(api, method_name)
    thread = command(wait=api.WAIT_TILL_DONE)
    if thread is None or not hasattr(thread, "getResult"):
        raise RuntimeError("%s returned no inspectable completion status" % method_name)
    code = thread.getResult()
    if code is None or text_type(code) not in ("0", "0.0"):
        raise RuntimeError("%s completion not confirmed (result=%s); no next experiment started" % (method_name, code))
    return {"command": method_name, "wait": "WAIT_TILL_DONE", "result": text_type(code)}


def _snapshot_files(folder):
    result = {}
    for root, dirs, files in os.walk(folder):
        for name in files:
            path = os.path.join(root, name)
            with open(path, "rb") as handle:
                result[os.path.relpath(path, folder)] = hashlib.sha256(handle.read()).hexdigest()
    return result


def run_plan(api, plan, output_dir, acquire=False):
    """Create a fresh series and optionally acquire/process it. Never resume.

    A stopped run retains partial experiments and its journal. Reruns require new
    EXPNO, so neither acquired nor partially acquired data can be overwritten.
    """
    template = plan["template"]
    assert_dataset(api, template)
    targets = paths_for(plan)
    if not os.path.isdir(plan["dataset_dir"]):
        raise RuntimeError("Dataset directory does not exist")
    collisions = [p for p in targets if os.path.lexists(p)]
    if collisions:
        raise RuntimeError("Existing destinations; no experiment changed: " + ", ".join(collisions))
    if engine.finite_number(api.GETPAR("PARMODE")) != 0:
        raise RuntimeError("Only a 1D acquisition template is supported")
    program = text_type(api.GETPAR("PULPROG")).strip().strip("<>")
    if program != plan["expected_program"]:
        raise RuntimeError("PULPROG differs from the reviewed plan")
    fixed = {}
    for key in ("RG", "NS", "D 1", "PHC0", "PHC1", "LB"):
        fixed[key] = engine.finite_number(api.GETPAR(key))
    if fixed["RG"] <= 0 or fixed["NS"] < 1 or fixed["D 1"] <= 0:
        raise RuntimeError("Template requires positive RG, NS and D1")
    for key in ("P 1", "P 30", "D 20", "D 16"):
        if key != plan["rows"][0]["parameter"]:
            fixed[key] = engine.finite_number(api.GETPAR(key))
    power_keys = []
    for key in ("PL 1", "PLW 1", "PLdB 1", "SFO1", "O1"):
        try:
            value = api.GETPAR(key)
            if value is not None and text_type(value).strip():
                fixed[key] = engine.finite_number(value)
                if key.startswith("PL"):
                    power_keys.append(key)
        except Exception:
            pass
    if plan["mode"] == "p1" and not power_keys:
        raise RuntimeError("P1 calibration requires an inspectable channel-1 RF power parameter")
    identities = {"PULPROG": program}
    for key in ("NUC1", "PROBHD"):
        try:
            value = text_type(api.GETPAR(key)).strip().strip("<>")
            if value:
                identities[key] = value
        except Exception:
            pass
    template_dir = os.path.join(plan["dataset_dir"], template[1])
    before = _snapshot_files(template_dir)
    journal = {"plan": plan, "template_parameters": fixed, "template_identities": identities,
               "state": "preparing", "acquisition_requested": bool(acquire),
               "events": [], "global_calibration_modified": False}
    journal_path = os.path.join(output_dir, "execution.json")
    def save():
        legacy.write_json(journal_path, journal)
    save()
    error = None
    try:
        # Prepare the whole series first, so acquisition never starts after a
        # late destination collision or a failed parameter-copy preflight.
        for row, target in zip(plan["rows"], targets):
            if os.path.lexists(target):
                raise RuntimeError("Destination appeared after review: " + target)
            api.RE(template)
            assert_dataset(api, template)
            command = api.XCMD("wraparam " + text_type(row["expno"]), wait=api.WAIT_TILL_DONE)
            if command is not None and hasattr(command, "getResult") and command.getResult() == -1:
                raise RuntimeError("wraparam failed")
            if not os.path.isdir(target):
                raise RuntimeError("wraparam did not create the expected destination")
            engine.ensure_parameter_only(target)
            destination = dataset_for(plan, row)
            api.RE(destination)
            assert_dataset(api, destination)
            engine.set_and_verify(api, row["parameter"], row["value"])
            verify_parameters(api, fixed, identities, row)
            journal["events"].append({"expno": row["expno"], "stage": "parameters_prepared"})
            save()
        journal["state"] = "prepared"
        save()
        if acquire:
            for row, target in zip(plan["rows"], targets):
                engine.ensure_parameter_only(target)
                destination = dataset_for(plan, row)
                api.RE(destination)
                assert_dataset(api, destination)
                verify_parameters(api, fixed, identities, row)
                journal["state"] = "acquiring"
                journal["events"].append({"expno": row["expno"], "stage": "ZG_started"})
                save()
                result = checked_command(api, "ZG")
                assert_dataset(api, destination)
                fid = os.path.join(target, "fid")
                if not os.path.isfile(fid) or os.path.getsize(fid) == 0:
                    raise RuntimeError("ZG returned success but no nonempty 1D fid was written")
                journal["events"].append({"expno": row["expno"], "stage": "ZG_finished", "command": result})
                save()
                result = checked_command(api, "EFP")
                assert_dataset(api, destination)
                # The reader verifies full 1D layout, scaling and finite points.
                spectrum = calibration.read_processed_1r(target, row["procno"])
                journal["events"].append({"expno": row["expno"], "stage": "EFP_finished",
                                          "command": result, "sources": spectrum["sources"]})
                save()
            journal["state"] = "acquired_and_processed"
    except Exception as exc:
        error = text_type(exc)
        journal["state"] = "stopped"
        journal["error"] = error
    finally:
        try:
            api.RE(template)
            assert_dataset(api, template)
        except Exception as exc:
            error = (error + "; " if error else "") + "Could not restore original view: " + text_type(exc)
            journal["state"], journal["error"] = "stopped", error
        journal["template_preserved"] = _snapshot_files(template_dir) == before
        if not journal["template_preserved"]:
            error = (error + "; " if error else "") + "Template file hashes changed; investigate external writes"
            journal["state"], journal["error"] = "stopped", error
        save()
    if error:
        raise RuntimeError(error + "\nPartial results retained; use NEW EXPNO for a new run.\n" + journal_path)
    return journal


def signed_integral(spectrum, low, high):
    """Nutation requires negative and zero areas; DOSY core intentionally does not."""
    low, high = engine.number(low, "ppm low"), engine.number(high, "ppm high")
    start, step, end = spectrum["ppm_start"], spectrum["ppm_step"], spectrum["ppm_end"]
    if not end <= low < high <= start:
        raise ValueError("Full integration window must lie inside the 1D spectrum")
    a, b = (start - high) / step, (start - low) / step
    if b - a < 2:
        raise ValueError("Integration region must span at least two intervals")
    values = spectrum["values"]
    def interp(index):
        i = int(math.floor(index))
        j = min(i + 1, len(values) - 1)
        return values[i] + (index - i) * (values[j] - values[i])
    points = [a] + [float(i) for i in range(int(math.floor(a)) + 1, int(math.ceil(b)))] + [b]
    return math.fsum((y - x) * (interp(x) + interp(y)) / 2 for x, y in zip(points[:-1], points[1:])) * step


def fit_nutation(pulse_us, integrals, p90_min_us, p90_max_us):
    """Fit signed A*sin(pi*P1/(2*P90))+offset within an explicit search range."""
    t = [engine.number(v, "P1", positive=True) for v in pulse_us]
    y = [engine.number(v, "signed integral") for v in integrals]
    lo = engine.number(p90_min_us, "minimum P90", positive=True)
    hi = engine.number(p90_max_us, "maximum P90", positive=True)
    if len(t) != len(y) or len(t) < 9 or len(set(t)) < 9 or lo >= hi:
        raise ValueError("Nutation fit needs >=9 distinct pulse lengths and a valid bounded P90 search")
    scale = max(abs(v) for v in y)
    if scale == 0 or min(y) >= -.02 * scale or max(y) <= .1 * scale:
        raise ValueError("Signed nutation must include positive and negative signal; verify fixed phase and sweep span")
    mean_y = math.fsum(y) / len(y)
    def model(p90):
        s = [math.sin(math.pi * value / (2 * p90)) for value in t]
        mean_s = math.fsum(s) / len(s)
        denominator = math.fsum((v - mean_s) ** 2 for v in s)
        if denominator <= 1e-20:
            return float("inf"), 0., 0., []
        amplitude = math.fsum((a - mean_s) * (b - mean_y) for a, b in zip(s, y)) / denominator
        offset = mean_y - amplitude * mean_s
        predicted = [amplitude * a + offset for a in s]
        error = math.fsum((a - b) ** 2 for a, b in zip(y, predicted))
        return (error if amplitude > 0 else float("inf")), amplitude, offset, predicted
    grid = [lo + (hi - lo) * i / 400 for i in range(401)]
    scores = [model(v)[0] for v in grid]
    best = min(range(len(grid)), key=lambda i: scores[i])
    if best in (0, 400) or math.isinf(scores[best]):
        raise ValueError("P90 optimum is at the search boundary or phase is incompatible")
    left, right = grid[best - 1], grid[best + 1]
    golden = (math.sqrt(5.) - 1) / 2
    for unused in range(70):
        a, b = right - golden * (right - left), left + golden * (right - left)
        if model(a)[0] <= model(b)[0]:
            right = b
        else:
            left = a
    p90 = (left + right) / 2
    sse, amplitude, offset, predicted = model(p90)
    if min(t) > .75 * p90 or max(t) < 2.1 * p90:
        raise ValueError("Sweep must sample the initial rise and extend beyond the first inversion")
    sst = math.fsum((v - mean_y) ** 2 for v in y)
    return {"P90_us": p90, "P180_us": 2 * p90, "model": "I(P1)=A*sin(pi*P1/(2*P90))+offset",
            "pulse_us": t, "integrals": y, "predicted_integrals": predicted,
            "residuals": [a - b for a, b in zip(y, predicted)], "R2": 1 - sse / sst,
            "amplitude": amplitude, "offset": offset, "search_range_us": [lo, hi],
            "uncertainty": "Not quantified; RF inhomogeneity, relaxation, off-resonance and integration can bias the ideal sine fit",
            "status": "proposal at the template RF power; inspect nutation and residuals before application",
            "written_to_instrument": False}


def analyze_p1(plan, low, high, p90_min, p90_max):
    if plan["mode"] != "p1":
        raise ValueError("Expected P1 plan")
    areas, sources, baseline, temperatures = [], [], None, []
    for row, folder in zip(plan["rows"], paths_for(plan)):
        spectrum = calibration.read_processed_1r(folder, row["procno"])
        acquisition = spectrum["acquisition"]
        actual = float(calibration._required(acquisition, "P", 1))
        if abs(actual - row["value"]) > 1e-8 * max(1, row["value"]):
            raise ValueError("Acquired P1 does not match the sweep plan")
        if calibration._required(acquisition, "PULPROG") != "zg":
            raise ValueError("Acquired P1 series does not use zg")
        stable = dict((key, calibration._required(acquisition, key)) for key in
                      ("PULPROG", "PROBHD", "NUC1", "RG", "NS"))
        for key in ("D", "P", "PL", "PLW", "PLdB", "GPX", "GPY", "GPZ", "GPNAM"):
            if key in acquisition:
                stable[key] = list(acquisition[key])
                if key == "P" and len(stable[key]) > 1:
                    stable[key][1] = None
        # Native files use arrays; test fixtures or exported JCAMP may also use
        # scalar aliases. Capture those without excluding any RF power field.
        for key in acquisition:
            if key != "P1" and (key.startswith("PL") or
                    (key[:1] in ("P", "D") and key[1:].isdigit())):
                stable[key] = acquisition[key]
        stable["processing"] = dict((key, spectrum["processing"].get(key)) for key in
                                    ("SI", "SF", "SW_p", "OFFSET", "PHC0", "PHC1", "LB", "BC_mod"))
        if baseline is None:
            baseline = stable
        elif baseline != stable:
            raise ValueError("P1 series changed RF power, delays, acquisition or fixed processing parameters")
        temperatures.append(engine.number(calibration._required(acquisition, "TE"), "TE", positive=True))
        areas.append(signed_integral(spectrum, float(low), float(high)))
        sources.extend(spectrum["sources"])
    result = fit_nutation(plan["values"], areas, p90_min, p90_max)
    result.update({"sources": sources, "ppm_region": [float(low), float(high)], "plan": plan,
                   "scope": baseline, "TE_min_K": min(temperatures), "TE_max_K": max(temperatures)})
    return result


def flow(api, mode):
    current, folder = legacy.current_dataset(api)
    program = text_type(api.GETPAR("PULPROG")).strip().strip("<>")
    if mode == "p1" and program != "zg":
        raise ValueError("Abra una plantilla 1D zg, ajustada y con fase correcta, para calibrar P1.")
    if mode == "p1":
        nominal = legacy.positive(api.GETPAR("P 1"), "P1 de plantilla")
        values_default = ",".join("%.6g" % (nominal * (.2 + .2 * i)) for i in range(22))
    else:
        nominal = None
        values_default = ",".join(text_type(v) for v in range(8, 97, 4))
    dialog = legacy.ask(api, "DOSY v3: " + ("nutacion P1" if mode == "p1" else "calibracion de gradientes"),
        ["Primer EXPNO NUEVO", "P1 en us, separados por coma" if mode == "p1" else "GPZ6 en %, separados por coma",
         "Limite ppm inferior", "Limite ppm superior", "Carpeta de informes"],
        ["500" if mode == "p1" else "600", values_default, "", "", legacy.report_base()],
        "Plantilla actual: " + program + ". Potencia RF, RG, NS, D1 y fase se heredan. Revise la relajacion y los limites de la sonda.")
    if dialog is None:
        return
    values = [engine.number(v.strip(), "Valor") for v in dialog[1].split(",")]
    plan = build_plan(current, mode, int(dialog[0]), values, program)
    low, high = engine.number(dialog[2], "ppm inferior"), engine.number(dialog[3], "ppm superior")
    if low >= high:
        raise ValueError("Limites ppm no validos")
    if mode == "p1":
        details = legacy.ask(api, "P1: intervalo del ajuste",
            ["P90 minimo (us)", "P90 maximo (us)"], [nominal * .25, nominal * 1.5],
            "El P1 actual puede ser 180 grados: NO se supone que sea P90. Edite el intervalo. Fase fija, sin APK por punto.")
    else:
        details = legacy.ask(api, "DOSY: referencia del patron",
            ["Patron, disolvente y fuente", "Dref a esa T (10^-9 m2/s)", "T referencia (K)",
             "Maximo intervalo TE (K)", "Maxima diferencia TE frente Tref (K)"], ["", "", "", ".5", ".5"],
            "D20/P30 se conservan. Esta adquisicion calibra UNA condicion de tiempos.")
    if details is None:
        return
    if mode == "p1":
        pmin, pmax = legacy.positive(details[0], "P90 minimo"), legacy.positive(details[1], "P90 maximo")
        if pmin >= pmax or len(values) < 9:
            raise ValueError("Se requieren >=9 puntos y P90 minimo < P90 maximo")
    else:
        if not details[0].strip():
            raise ValueError("Indique patron, disolvente y fuente")
        for index, label in ((1, "Dref"), (2, "Tref"), (3, "Variacion TE"), (4, "Diferencia TE")):
            legacy.positive(details[index], label)
    plan["analysis"] = {"ppm_low": low, "ppm_high": high, "reference_fields": details}
    summary = json.dumps(plan, ensure_ascii=True, indent=2)
    api.VIEWTEXT("Plan de calibracion v3", "Destinos nuevos; no se modifican originales ni constantes globales", summary)
    choice = api.SELECT("Accion", "Revise la sonda, muestra, potencia RF, temperatura, D1, RG y fase antes de adquirir.",
                        ["Exportar plan", "Preparar sin adquirir", "Preparar, adquirir y analizar", "Cancelar"])
    if choice not in (0, 1, 2):
        return
    if choice == 2 and api.SELECT("Iniciar adquisicion ahora",
            "Se ejecutaran %s adquisiciones ZG en EXPNO nuevos y EFP con fase fija.\n"
            "Confirme que la muestra, sonda, potencia RF, limites del barrido, relajacion y temperatura estan preparados." % len(plan["rows"]),
            ["Iniciar serie", "Cancelar"]) != 0:
        return
    output = legacy.new_report_dir(dialog[4], "v3_" + mode)
    legacy.write_json(os.path.join(output, "plan.json"), plan)
    if choice == 0:
        api.MSG("Plan exportado: " + output)
        return
    run_plan(api, plan, output, acquire=(choice == 2))
    if choice == 1:
        api.MSG("Parametros preparados. No se ha iniciado adquisicion.\n" + output)
        return
    if mode == "p1":
        result = analyze_p1(plan, low, high, float(details[0]), float(details[1]))
        legacy.write_json(os.path.join(output, "p1_propuesta.json"), result)
        legacy.write_text(os.path.join(output, "nutacion.csv"), legacy.csv_text(
            [{"P1_us": t, "integral": y, "predicha": p, "residuo": r} for t, y, p, r in
             zip(result["pulse_us"], result["integrals"], result["predicted_integrals"], result["residuals"])],
            ["P1_us", "integral", "predicha", "residuo"]))
        api.VIEWTEXT("Propuesta P1", "Potencia RF heredada; revisar antes de aplicar",
                     "P90 = %.7g us; P180 = %.7g us; R2 = %.7g\n%s" % (result["P90_us"], result["P180_us"], result["R2"], output))
    else:
        result = calibration.analyze_series(folder, [r["expno"] for r in plan["rows"]], current[2],
            low, high, float(details[1]), float(details[2]), details[0], float(details[3]), float(details[4]))
        result["bruker_gradient_proposal"] = legacy.known_sequence_gradient(result)
        legacy.write_json(os.path.join(output, "calibracion.json"), result)
        legacy.write_text(os.path.join(output, "informe.html"), legacy.make_report(result))
        keys = ["expno", "gradient_percent", "integral", "predicted_integral", "residual_log"]
        legacy.write_text(os.path.join(output, "atenuacion_residuos.csv"), legacy.csv_text(result["rows"], keys))
        api.VIEWTEXT("Calibracion DOSY v3", "Ajuste y residuos", legacy.calibration_summary(result) + "\n" + output)


def main(api):
    try:
        action = api.SELECT("DiffAtOnce DOSY v3", "Automatizacion desde TopSpin",
            ["Calibrar P1: barrido de nutacion", "Calibrar DOSY: adquirir rampa del patron", "Asistente anterior: rampas y analisis", "Salir"])
        if action in (0, 1):
            flow(api, "p1" if action == 0 else "gradient")
        elif action == 2:
            legacy.main(api)
    except Exception as exc:
        api.MSG("Calibracion detenida: " + text_type(exc))
