# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import json, math, os, re
from decimal import Decimal, InvalidOperation
try:
    string_types = (basestring,)
    text_type = unicode
except NameError:
    string_types = (str,)
    text_type = str

DEFAULT_CONFIG = {
    "schema_version": 1,
    "template_expno": 10,
    "template_procno": 1,
    "expected_dataset_name": "",
    "expected_pulse_program": "",
    "ramp_count": 3,
    "start_expno": 100,
    "experiment_stride": 100,
    "gradient_index": 6,
    "gradient_start_percent": 8,
    "gradient_stop_percent": 96,
    "gradient_step_percent": 4,
    "delay_parameter": None,
    "delay_values_s": None,
    "delay_mapping_confirmed": False,
    "pulse_parameter": None,
    "pulse_value_us": None,
    "pulse_mapping_confirmed": False,
    "dummy_scans": 16,
    "example_only": False,
}


class PlanError(ValueError):
    pass


def integer(value, name, minimum=1, maximum=2147483647):
    if isinstance(value, bool):
        raise PlanError("%s debe ser entero." % name)
    try:
        parsed = int(value)
    except (ValueError, TypeError, OverflowError):
        raise PlanError("%s debe ser entero." % name)
    if text_type(parsed) != text_type(value) and parsed != value:
        raise PlanError("%s debe ser entero." % name)
    if not minimum <= parsed <= maximum:
        raise PlanError("%s debe estar entre %s y %s." % (name, minimum, maximum))
    return parsed


def number(value, name, positive=False):
    if isinstance(value, bool):
        raise PlanError("%s debe ser numérico." % name)
    try:
        parsed = float(value)
    except (ValueError, TypeError, OverflowError):
        raise PlanError("%s debe ser numérico." % name)
    if not (not math.isnan(parsed) and not math.isinf(parsed)) or (positive and parsed <= 0):
        raise PlanError("%s debe ser finito%s." % (name, " y mayor que cero" if positive else ""))
    return parsed


def param_name(value, prefix):
    if not isinstance(value, string_types) or not re.match(prefix + r"\d{1,3}$", value.upper().replace(" ", "")):
        raise PlanError("Parámetro inválido: use %s seguido de un índice, p. ej. %s." % (prefix, "D20" if prefix == "D" else "P30"))
    return value.upper().replace(" ", "")


def format_number(value):
    return format(float(value), ".12g")


def gradient_values(config):
    try:
        first = Decimal(text_type(config["gradient_start_percent"]))
        last = Decimal(text_type(config["gradient_stop_percent"]))
        step = Decimal(text_type(config["gradient_step_percent"]))
    except (InvalidOperation, ValueError):
        raise PlanError("Los gradientes deben ser números.")
    if not all(x.is_finite() for x in (first, last, step)):
        raise PlanError("Los gradientes deben ser finitos.")
    if not 0 <= first < last <= 100 or step <= 0:
        raise PlanError("Requiere 0 <= inicio < final <= 100 y paso positivo.")
    count = (last - first) / step
    if count != count.to_integral_value():
        raise PlanError("El paso no alcanza exactamente el gradiente final.")
    if count + 1 > 10000:
        raise PlanError("Demasiados puntos de gradiente (máximo 10000).")
    return [float(first + i * step) for i in range(int(count) + 1)]


def build_plan(given=None):
    config = dict(DEFAULT_CONFIG)
    if given:
        unknown = set(given) - set(config)
        if unknown:
            raise PlanError("Opciones desconocidas: " + ", ".join(sorted(unknown)))
        config.update(given)
    if config["schema_version"] != 1:
        raise PlanError("schema_version debe ser 1.")
    for key in ("example_only", "delay_mapping_confirmed", "pulse_mapping_confirmed"):
        if not isinstance(config[key], bool):
            raise PlanError(key + " debe ser true o false.")
    for key in ("template_expno", "template_procno", "ramp_count", "start_expno", "experiment_stride"):
        config[key] = integer(config[key], key)
    config["gradient_index"] = integer(config["gradient_index"], "gradient_index", 0, 99)
    if config["ramp_count"] > 100:
        raise PlanError("Máximo 100 rampas por plan.")
    for key in ("expected_dataset_name", "expected_pulse_program"):
        if not isinstance(config[key], string_types) or any(c in config[key] for c in ("/", "\\", "\n", "\r", "\0")):
            raise PlanError(key + " debe ser un nombre simple sin rutas.")
    values = gradient_values(config)
    if config["ramp_count"] > 1 and config["experiment_stride"] < len(values):
        raise PlanError("experiment_stride provoca solapamiento entre rampas.")
    delay_values = config["delay_values_s"]
    if delay_values is not None:
        if not isinstance(delay_values, list) or len(delay_values) != config["ramp_count"]:
            raise PlanError("delay_values_s debe contener un valor por rampa.")
        config["delay_parameter"] = param_name(config["delay_parameter"], "D")
        delay_values = [number(v, "delay_values_s", positive=True) for v in delay_values]
        config["delay_values_s"] = delay_values
        if not config["example_only"] and not config["delay_mapping_confirmed"]:
            raise PlanError("Confirme en la secuencia la correspondencia del parámetro D con el tiempo de difusión, o use example_only.")
    elif config["delay_parameter"] is not None:
        raise PlanError("delay_parameter requiere delay_values_s.")
    if config["pulse_value_us"] is not None:
        config["pulse_parameter"] = param_name(config["pulse_parameter"], "P")
        config["pulse_value_us"] = number(config["pulse_value_us"], "pulse_value_us", positive=True)
        if not config["example_only"] and not config["pulse_mapping_confirmed"]:
            raise PlanError("Confirme en la secuencia la función del parámetro P, o use example_only.")
    elif config["pulse_parameter"] is not None:
        raise PlanError("pulse_parameter requiere pulse_value_us.")
    if (delay_values or config["pulse_value_us"] is not None) and not config["expected_pulse_program"] and not config["example_only"]:
        raise PlanError("Para modificar D/P indique expected_pulse_program y verifique su correspondencia.")
    if config["dummy_scans"] is not None:
        config["dummy_scans"] = integer(config["dummy_scans"], "dummy_scans", 0, 1000000)
    rows = []
    for ramp in range(config["ramp_count"]):
        for index, gradient in enumerate(values):
            expno = config["start_expno"] + ramp * config["experiment_stride"] + index
            integer(expno, "EXPNO calculado")
            if expno == config["template_expno"]:
                raise PlanError("La plantilla EXPNO %s coincide con un destino." % expno)
            rows.append({
                "ramp": ramp + 1,
                "point": index + 1,
                "expno": expno,
                "procno": config["template_procno"],
                "gradient_index": config["gradient_index"],
                "gradient_percent": gradient,
                "delay_parameter": config["delay_parameter"],
                "delay_s": None if delay_values is None else delay_values[ramp],
                "pulse_parameter": config["pulse_parameter"],
                "pulse_us": config["pulse_value_us"],
                "dummy_scans": config["dummy_scans"],
            })
    if len(set(row["expno"] for row in rows)) != len(rows):
        raise PlanError("Se han detectado EXPNO duplicados.")
    return {
        "schema_version": 1,
        "generator": "DiffAtOnce workshop offline ramp generator 1.0",
        "example_only": config["example_only"],
        "can_prepare": not config["example_only"],
        "purpose": "Preparación de parámetros; no adquisición, calibración ni cálculo de b.",
        "gradient_unit": "porcentaje GPZ; no G/cm ni T/m",
        "delay_unit": "s (unidad del parámetro TopSpin D)",
        "pulse_unit": "us (unidad del parámetro TopSpin P; no asumir delta=P)",
        "config": config,
        "points_per_ramp": len(values),
        "experiment_count": len(rows),
        "rows": rows,
    }


def parameter_key(name):
    # TopSpin Python usa "D 20" / "P 30" / "GPZ 6".
    return name[0] + " " + name[1:]


def finite_number(value):
    result = float(value)
    if math.isnan(result) or math.isinf(result):
        raise RuntimeError("Valor numerico no finito.")
    return result


def format_value(value):
    return "%.12g" % float(value)


def equivalent_dataset(left, right):
    return (text_type(left[0]) == text_type(right[0]) and
            text_type(left[1]) == text_type(right[1]) and
            text_type(left[2]) == text_type(right[2]) and
            os.path.normcase(os.path.realpath(text_type(left[3]))) ==
            os.path.normcase(os.path.realpath(text_type(right[3]))))


def is_signal_file(name):
    if name in ("fid", "ser"):
        return True
    # Nombres Bruker de datos numericos procesados 1r/1i, 2rr/2ri, 3rrr...
    return len(name) >= 2 and name[0] in "12345678" and set(name[1:]).issubset(set("ri"))


def ensure_parameter_only(path):
    for folder, dirs, files in os.walk(path):
        for name in files:
            if is_signal_file(name):
                raise RuntimeError("Se encontro un archivo de senal inesperado: " + os.path.join(folder, name) +
                                   ". No se ha borrado nada; revise la copia y detenga este flujo.")


def preflight(api, plan):
    if plan.get("example_only") or not plan.get("can_prepare"):
        raise RuntimeError("Este plan esta marcado como EJEMPLO. Edite config.json, confirme la correspondencia de la secuencia y regenere con example_only=false.")
    cfg = plan["config"]
    current = api.CURDATA()
    if not current or len(current) != 4:
        raise RuntimeError("Abra un dataset con CURDATA de cuatro campos [nombre, expno, procno, directorio]. No se admite el layout antiguo con usuario adicional.")
    current = list(current)
    if cfg["expected_dataset_name"] and text_type(current[0]) != cfg["expected_dataset_name"]:
        raise RuntimeError("Dataset inesperado. Se esperaba " + cfg["expected_dataset_name"] + "; actual: " + text_type(current[0]))
    dataset_name = text_type(current[0])
    if dataset_name in (".", "..") or any(c in dataset_name for c in ("/", "\\", "\0")):
        raise RuntimeError("Nombre de dataset no valido para el layout directo.")
    root = os.path.realpath(text_type(current[3]))
    dataset_dir = os.path.join(root, dataset_name)
    if not os.path.isdir(dataset_dir):
        raise RuntimeError("No existe la ruta directa del dataset: " + dataset_dir)
    template = [dataset_name, text_type(cfg["template_expno"]), text_type(cfg["template_procno"]), root]
    template_dir = os.path.join(dataset_dir, template[1])
    template_proc_dir = os.path.join(template_dir, "pdata", template[2])
    if not (os.path.isfile(os.path.join(template_dir, "acqu")) or os.path.isfile(os.path.join(template_dir, "acqus"))):
        raise RuntimeError("La plantilla no tiene parametros de adquisicion: " + template_dir)
    if not (os.path.isfile(os.path.join(template_proc_dir, "proc")) or os.path.isfile(os.path.join(template_proc_dir, "procs"))):
        raise RuntimeError("La plantilla no tiene parametros de procesado en PROCNO esperado: " + template_proc_dir)
    destinations = []
    seen = set()
    for row in plan["rows"]:
        expno = text_type(row["expno"])
        if not expno.isdigit() or int(expno) <= 0 or expno in seen or expno == template[1]:
            raise RuntimeError("EXPNO invalido, duplicado o igual a plantilla: " + expno)
        seen.add(expno)
        path = os.path.join(dataset_dir, expno)
        destinations.append(path)
    # TODAS las colisiones se comprueban antes de RE / wraparam / PUTPAR.
    collisions = [p for p in destinations if os.path.lexists(p)]
    if collisions:
        raise RuntimeError("Los destinos ya existen. No se escribe ningun experimento:\n" + "\n".join(collisions))
    if cfg["delay_values_s"] is not None and not cfg["delay_mapping_confirmed"]:
        raise RuntimeError("Falta verificar la correspondencia del parametro D en esta secuencia.")
    if cfg["pulse_value_us"] is not None and not cfg["pulse_mapping_confirmed"]:
        raise RuntimeError("Falta verificar la correspondencia del parametro P en esta secuencia.")
    return current, template, destinations


def set_and_verify(api, key, value):
    api.PUTPAR(key, format_value(value))
    observed = finite_number(api.GETPAR(key))
    if abs(observed - float(value)) > max(1e-9, abs(float(value)) * 1e-7):
        raise RuntimeError("No se ha confirmado " + key + ": esperado " + format_value(value) + ", leido " + text_type(observed))


def prepare(api, plan):
    original, template, paths = preflight(api, plan)
    created = []
    problem = None
    try:
        api.RE(template)
        if not equivalent_dataset(api.CURDATA(), template):
            raise RuntimeError("RE no ha abierto la plantilla prevista.")
        if finite_number(api.GETPAR("PARMODE")) != 0:
            raise RuntimeError("La plantilla debe ser 1D (PARMODE=0) para estas rampas de EXPNO independientes.")
        actual_program = text_type(api.GETPAR("PULPROG")).strip().strip("<>")
        expected = plan["config"]["expected_pulse_program"]
        if expected and actual_program != expected:
            raise RuntimeError("PULPROG de plantilla no coincide: " + actual_program + "; esperado: " + expected)
        for row, path in zip(plan["rows"], paths):
            # Repetir la comprobacion protege frente a un destino creado desde otro proceso.
            if os.path.lexists(path):
                raise RuntimeError("El destino aparecio durante la preparacion: " + path)
            api.RE(template)
            if not equivalent_dataset(api.CURDATA(), template):
                raise RuntimeError("Se perdio la plantilla antes de copiar parametros.")
            # wraparam: copia solo parametros; NO usar wrpa/WR (copian datos).
            api.XCMD("wraparam " + text_type(row["expno"]), wait=api.WAIT_TILL_DONE)
            if not os.path.isdir(path):
                raise RuntimeError("wraparam no creo el destino: " + path)
            created.append(path)
            ensure_parameter_only(path)
            destination = [template[0], text_type(row["expno"]), text_type(row["procno"]), template[3]]
            api.RE(destination)
            if not equivalent_dataset(api.CURDATA(), destination):
                raise RuntimeError("RE no abrio el destino previsto: " + path)
            set_and_verify(api, "GPZ " + text_type(row["gradient_index"]), row["gradient_percent"])
            if row["delay_s"] is not None:
                set_and_verify(api, parameter_key(row["delay_parameter"]), row["delay_s"])
            if row["pulse_us"] is not None:
                set_and_verify(api, parameter_key(row["pulse_parameter"]), row["pulse_us"])
            if row["dummy_scans"] is not None:
                set_and_verify(api, "DS", row["dummy_scans"])
    except Exception as error:
        problem = text_type(error)
    finally:
        try:
            api.RE(original)
            if not equivalent_dataset(api.CURDATA(), original):
                raise RuntimeError("RE no restauro el dataset original.")
        except Exception as restore_error:
            restore_message = "No se ha podido restaurar el dataset original: " + text_type(restore_error)
            problem = restore_message if problem is None else problem + "\n" + restore_message
    if problem is not None:
        # Un comando puede crear el directorio y fallar antes de devolver el control.
        present = [p for p in paths if os.path.lexists(p)]
        raise RuntimeError(problem + "\nPreparacion detenida. Directorios nuevos ya creados: " + text_type(len(present)) +
                           ". No se ha adquirido ni borrado ningun dato.\n" + "\n".join(present))
    return created

