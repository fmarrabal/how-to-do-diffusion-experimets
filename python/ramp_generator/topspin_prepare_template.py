# -*- coding: utf-8 -*-
"""Plantilla interna Jython 2.7 / TopSpin. No ejecutar este archivo sin generar.

El generador sustituye __PLAN_JSON_LITERAL__ por el plan revisable.
Preparacion sin adquisicion: no contiene zg, rga ni acceso de escritura a FID.
"""
from __future__ import print_function
import json
import math
import os

PLAN = json.loads(__PLAN_JSON_LITERAL__)


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
    return (str(left[0]) == str(right[0]) and
            str(left[1]) == str(right[1]) and
            str(left[2]) == str(right[2]) and
            os.path.normcase(os.path.realpath(str(left[3]))) ==
            os.path.normcase(os.path.realpath(str(right[3]))))


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
    if cfg["expected_dataset_name"] and str(current[0]) != cfg["expected_dataset_name"]:
        raise RuntimeError("Dataset inesperado. Se esperaba " + cfg["expected_dataset_name"] + "; actual: " + str(current[0]))
    dataset_name = str(current[0])
    if dataset_name in (".", "..") or any(c in dataset_name for c in ("/", "\\", "\0")):
        raise RuntimeError("Nombre de dataset no valido para el layout directo.")
    root = os.path.realpath(str(current[3]))
    dataset_dir = os.path.join(root, dataset_name)
    if not os.path.isdir(dataset_dir):
        raise RuntimeError("No existe la ruta directa del dataset: " + dataset_dir)
    template = [dataset_name, str(cfg["template_expno"]), str(cfg["template_procno"]), root]
    template_dir = os.path.join(dataset_dir, template[1])
    template_proc_dir = os.path.join(template_dir, "pdata", template[2])
    if not (os.path.isfile(os.path.join(template_dir, "acqu")) or os.path.isfile(os.path.join(template_dir, "acqus"))):
        raise RuntimeError("La plantilla no tiene parametros de adquisicion: " + template_dir)
    if not (os.path.isfile(os.path.join(template_proc_dir, "proc")) or os.path.isfile(os.path.join(template_proc_dir, "procs"))):
        raise RuntimeError("La plantilla no tiene parametros de procesado en PROCNO esperado: " + template_proc_dir)
    destinations = []
    seen = set()
    for row in plan["rows"]:
        expno = str(row["expno"])
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
        raise RuntimeError("No se ha confirmado " + key + ": esperado " + format_value(value) + ", leido " + str(observed))


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
        actual_program = str(api.GETPAR("PULPROG")).strip().strip("<>")
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
            api.XCMD("wraparam " + str(row["expno"]), wait=api.WAIT_TILL_DONE)
            if not os.path.isdir(path):
                raise RuntimeError("wraparam no creo el destino: " + path)
            created.append(path)
            ensure_parameter_only(path)
            destination = [template[0], str(row["expno"]), str(row["procno"]), template[3]]
            api.RE(destination)
            if not equivalent_dataset(api.CURDATA(), destination):
                raise RuntimeError("RE no abrio el destino previsto: " + path)
            set_and_verify(api, "GPZ " + str(row["gradient_index"]), row["gradient_percent"])
            if row["delay_s"] is not None:
                set_and_verify(api, parameter_key(row["delay_parameter"]), row["delay_s"])
            if row["pulse_us"] is not None:
                set_and_verify(api, parameter_key(row["pulse_parameter"]), row["pulse_us"])
            if row["dummy_scans"] is not None:
                set_and_verify(api, "DS", row["dummy_scans"])
    except Exception as error:
        problem = str(error)
    finally:
        try:
            api.RE(original)
            if not equivalent_dataset(api.CURDATA(), original):
                raise RuntimeError("RE no restauro el dataset original.")
        except Exception as restore_error:
            restore_message = "No se ha podido restaurar el dataset original: " + str(restore_error)
            problem = restore_message if problem is None else problem + "\n" + restore_message
    if problem is not None:
        # Un comando puede crear el directorio y fallar antes de devolver el control.
        present = [p for p in paths if os.path.lexists(p)]
        raise RuntimeError(problem + "\nPreparacion detenida. Directorios nuevos ya creados: " + str(len(present)) +
                           ". No se ha adquirido ni borrado ningun dato.\n" + "\n".join(present))
    return created


def main():
    import TopCmds as api
    try:
        created = prepare(api, PLAN)
    except Exception as error:
        api.MSG("Preparacion DOSY detenida:\n" + str(error))
        return
    api.MSG("Preparados " + str(len(created)) + " experimentos de parametros. No se ha iniciado ninguna adquisicion.\n"
            "Revise el plan, la secuencia, GPZ, D/P, DS/NS/RG y temperatura antes de adquirir.\n"
            "Se ha restaurado el dataset que estaba abierto.")


if __name__ == "__main__":
    main()
