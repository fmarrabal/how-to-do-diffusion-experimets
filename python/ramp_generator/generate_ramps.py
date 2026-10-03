#!/usr/bin/env python3
"""Generador OFFLINE: planes y preparación TopSpin, nunca adquisición.

Python >= 3.8, biblioteca estándar. Tkinter se importa únicamente con --gui.
"""
import argparse
import csv
import json
import math
import re
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


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
    if str(parsed) != str(value) and parsed != value:
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
    if not math.isfinite(parsed) or (positive and parsed <= 0):
        raise PlanError("%s debe ser finito%s." % (name, " y mayor que cero" if positive else ""))
    return parsed


def param_name(value, prefix):
    if not isinstance(value, str) or not re.fullmatch(prefix + r"\d{1,3}", value.upper().replace(" ", "")):
        raise PlanError("Parámetro inválido: use %s seguido de un índice, p. ej. %s." % (prefix, "D20" if prefix == "D" else "P30"))
    return value.upper().replace(" ", "")


def format_number(value):
    return format(float(value), ".12g")


def gradient_values(config):
    try:
        first = Decimal(str(config["gradient_start_percent"]))
        last = Decimal(str(config["gradient_stop_percent"]))
        step = Decimal(str(config["gradient_step_percent"]))
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
        if not isinstance(config[key], str) or any(c in config[key] for c in ("/", "\\", "\n", "\r", "\0")):
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


def render_macro_reference(plan):
    """Referencia expandida; preflight de colisiones existe en el script seguro."""
    cfg = plan["config"]
    lines = []
    for row in plan["rows"]:
        lines.extend([
            "re %s %s" % (cfg["template_expno"], cfg["template_procno"]),
            "wraparam %s" % row["expno"],
            "re %s %s" % (row["expno"], row["procno"]),
            "gpz%s %s" % (row["gradient_index"], format_number(row["gradient_percent"])),
        ])
        if row["delay_s"] is not None:
            lines.append("%s %s" % (row["delay_parameter"].lower(), format_number(row["delay_s"])))
        if row["pulse_us"] is not None:
            lines.append("%s %s" % (row["pulse_parameter"].lower(), format_number(row["pulse_us"])))
        if row["dummy_scans"] is not None:
            lines.append("ds %s" % row["dummy_scans"])
    lines.append("re %s %s" % (cfg["template_expno"], cfg["template_procno"]))
    return "\n".join(lines) + "\n"


def write_bundle(config, output):
    plan = build_plan(config)
    output = Path(output).resolve()
    # Rechazar una carpeta existente, incluso vacía: nunca sobrescribir una entrega.
    output.mkdir(parents=True, exist_ok=False)
    json_text = json.dumps(plan, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    (output / "plan.json").write_text(json_text, encoding="utf-8")
    (output / "config.json").write_text(json.dumps(plan["config"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (output / "plan.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(plan["rows"][0]))
        writer.writeheader()
        writer.writerows(plan["rows"])
    template = Path(__file__).with_name("topspin_prepare_template.py").read_text(encoding="utf-8")
    embedded_json_literal = repr(json.dumps(plan, ensure_ascii=True, allow_nan=False))
    script = template.replace("PLAN = json.loads(__PLAN_JSON_LITERAL__)", "PLAN = json.loads(" + embedded_json_literal + ")")
    (output / "dosy_prepare_ramps.py").write_text(script, encoding="utf-8")
    (output / "dosy_prepare_ramps").write_text("xpy dosy_prepare_ramps.py\n", encoding="ascii")
    (output / "macro_expandida_REFERENCIA_NO_EJECUTAR.txt").write_text(render_macro_reference(plan), encoding="ascii")
    summaries = []
    for ramp in range(1, plan["config"]["ramp_count"] + 1):
        points = [r for r in plan["rows"] if r["ramp"] == ramp]
        delay = "heredado" if points[0]["delay_s"] is None else "%s = %s s" % (points[0]["delay_parameter"], format_number(points[0]["delay_s"]))
        summaries.append("Rampa %s: EXPNO %s-%s, %s puntos, %s" % (ramp, points[0]["expno"], points[-1]["expno"], len(points), delay))
    notice = "EJEMPLO: ejecución bloqueada hasta regenerar con example_only=false y correspondencias verificadas.\n" if plan["example_only"] else "El script preparará parámetros al ejecutarlo en TopSpin. No adquiere.\n"
    (output / "LEEME.txt").write_text(
        notice + "\n" + "\n".join(summaries) + "\n\n"
        "1. Revise plan.csv, config.json y README.md del generador.\n"
        "2. Copie dosy_prepare_ramps.py al directorio de scripts Python de usuario de TopSpin.\n"
        "3. Abra el dataset correcto y ejecute: xpy dosy_prepare_ramps.py\n"
        "4. Alternativamente instale dosy_prepare_ramps (sin extensión) como macro de usuario; llama al mismo script.\n"
        "5. El script comprueba los destinos antes de escribir y utiliza wraparam (solo parámetros).\n"
        "6. No ejecute la macro expandida directamente: carece del preflight del script.\n"
        "7. Revise PULPROG, GPZ6, forma de gradiente, D20/P30, temperatura, bloqueo, ajuste, DS/NS/RG antes de adquirir.\n"
        "\nVerificación local: sintaxis y simulación; pendiente prueba en TopSpin 3.6.4/espectrómetro.\n",
        encoding="utf-8")
    return plan


def launch_gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title("DOSY · generador offline de rampas TopSpin")
    root.geometry("960x760")
    body = ttk.Frame(root, padding=14)
    body.pack(fill="both", expand=True)
    ttk.Label(body, text="Planifique las rampas y genere los archivos de preparación", font=("Segoe UI", 16, "bold")).pack(anchor="w")
    ttk.Label(body, text="No conecta al espectrómetro ni adquiere. Los porcentajes GPZ no son un gradiente físico calibrado.").pack(anchor="w", pady=(4, 12))
    grid = ttk.Frame(body)
    grid.pack(fill="x")
    fields = {}
    definitions = [
        ("template_expno", "EXPNO plantilla", "10"),
        ("start_expno", "Primer EXPNO destino", "100"),
        ("ramp_count", "Número de rampas", "3"),
        ("experiment_stride", "Salto entre rampas", "100"),
        ("gradient_index", "Índice GPZ", "6"),
        ("gradient_start_percent", "Gradiente inicial (%)", "8"),
        ("gradient_stop_percent", "Gradiente final (%)", "96"),
        ("gradient_step_percent", "Paso (%)", "4"),
        ("delay_ms", "D20 por rampa (ms; vacío = heredar)", "50, 100, 150"),
        ("expected_pulse_program", "PULPROG esperado", "stebpgp1s1d"),
        ("expected_dataset_name", "Nombre dataset (opcional)", ""),
        ("dummy_scans", "DS (vacío = heredar)", "16"),
    ]
    for i, (key, label, default) in enumerate(definitions):
        row, group = divmod(i, 2)
        column = group * 2
        ttk.Label(grid, text=label).grid(row=row, column=column, sticky="w", padx=(0, 6), pady=4)
        fields[key] = tk.StringVar(value=default)
        ttk.Entry(grid, textvariable=fields[key], width=23).grid(row=row, column=column + 1, sticky="ew", padx=(0, 18), pady=4)
    grid.columnconfigure(1, weight=1)
    grid.columnconfigure(3, weight=1)
    example = tk.BooleanVar(value=True)
    confirmed = tk.BooleanVar(value=False)
    ttk.Checkbutton(body, text="Es un ejemplo; bloquear su ejecución en TopSpin", variable=example).pack(anchor="w", pady=(10, 0))
    ttk.Checkbutton(body, text="He comprobado en esta secuencia que D20 representa el tiempo de difusión solicitado", variable=confirmed).pack(anchor="w")
    ttk.Label(body, text="P30 y el resto de los parámetros se heredan de la plantilla. D20 se guarda en segundos.").pack(anchor="w", pady=7)
    frame = ttk.Frame(body)
    frame.pack(fill="both", expand=True)
    preview = tk.Text(frame, font=("Consolas", 10), wrap="none", height=15)
    scroll = ttk.Scrollbar(frame, command=preview.yview)
    preview.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    preview.pack(fill="both", expand=True)

    def configuration():
        cfg = dict(DEFAULT_CONFIG)
        for key in ("template_expno", "start_expno", "ramp_count", "experiment_stride", "gradient_index"):
            cfg[key] = integer(fields[key].get(), key, minimum=0 if key == "gradient_index" else 1)
        for key in ("gradient_start_percent", "gradient_stop_percent", "gradient_step_percent"):
            cfg[key] = number(fields[key].get(), key)
        for key in ("expected_pulse_program", "expected_dataset_name"):
            cfg[key] = fields[key].get().strip()
        delay = fields["delay_ms"].get().strip()
        if delay:
            cfg["delay_parameter"] = "D20"
            cfg["delay_values_s"] = [number(v.strip(), "D20 en ms", positive=True) / 1000 for v in delay.split(",")]
        cfg["dummy_scans"] = None if not fields["dummy_scans"].get().strip() else integer(fields["dummy_scans"].get(), "DS", 0)
        cfg["example_only"] = example.get()
        cfg["delay_mapping_confirmed"] = confirmed.get()
        return cfg

    def show_plan():
        try:
            plan = build_plan(configuration())
        except (PlanError, ValueError) as error:
            messagebox.showerror("Revise la configuración", str(error))
            return None
        preview.delete("1.0", "end")
        preview.insert("end", "%s experimentos; %s puntos/rampa. %s\n\n" % (plan["experiment_count"], plan["points_per_ramp"], "EJEMPLO BLOQUEADO" if plan["example_only"] else "PREPARACIÓN HABILITADA"))
        preview.insert("end", "Rampa  Punto  EXPNO    GPZ (%)    D20 (s)\n")
        for row in plan["rows"]:
            delay = "heredado" if row["delay_s"] is None else format_number(row["delay_s"])
            preview.insert("end", "%5s  %5s  %5s  %9s  %10s\n" % (row["ramp"], row["point"], row["expno"], format_number(row["gradient_percent"]), delay))
        return plan

    def save():
        plan = show_plan()
        if plan is None:
            return
        parent = filedialog.askdirectory(title="Seleccione dónde crear una NUEVA carpeta de salida")
        if not parent:
            return
        output = Path(parent) / datetime.now().strftime("rampas_DOSY_%Y%m%d_%H%M%S_%f")
        try:
            write_bundle(plan["config"], output)
        except Exception as error:
            messagebox.showerror("No se ha completado la generación", str(error))
            return
        messagebox.showinfo("Archivos generados", "%s\n\nRevise LEEME.txt y plan.csv antes de llevarlos a TopSpin." % output)

    buttons = ttk.Frame(body)
    buttons.pack(fill="x", pady=(12, 0))
    ttk.Button(buttons, text="Previsualizar", command=show_plan).pack(side="left")
    ttk.Button(buttons, text="Generar archivos en carpeta nueva", command=save).pack(side="right")
    show_plan()
    root.mainloop()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gui", action="store_true", help="Abrir interfaz Tkinter")
    parser.add_argument("--config", type=Path, help="Configuración JSON")
    parser.add_argument("--out", type=Path, help="Nueva carpeta de salida (no debe existir)")
    parser.add_argument("--ramps", type=int)
    parser.add_argument("--start-expno", type=int)
    parser.add_argument("--stride", type=int)
    parser.add_argument("--template-expno", type=int)
    parser.add_argument("--gradient-index", type=int)
    parser.add_argument("--gradient-start", type=float)
    parser.add_argument("--gradient-stop", type=float)
    parser.add_argument("--gradient-step", type=float)
    parser.add_argument("--delay-s", type=float, nargs="+", help="Un valor del parámetro D por rampa, en segundos")
    parser.add_argument("--delay-parameter", help="P. ej. D20; comprobar primero en la secuencia")
    parser.add_argument("--confirm-delay-mapping", action="store_true")
    parser.add_argument("--pulse-us", type=float, help="Valor del parámetro P en microsegundos; no asumir que sea delta")
    parser.add_argument("--pulse-parameter")
    parser.add_argument("--confirm-pulse-mapping", action="store_true")
    parser.add_argument("--pulse-program")
    parser.add_argument("--dataset-name")
    parser.add_argument("--ds", type=int)
    parser.add_argument("--example-only", action="store_true")
    args = parser.parse_args(argv)
    if args.gui:
        if args.config or args.out:
            parser.error("--gui no se combina con --config o --out.")
        launch_gui()
        return 0
    if args.out is None:
        parser.error("Use --out CARPETA_NUEVA o --gui.")
    try:
        cfg = {} if args.config is None else json.loads(args.config.read_text(encoding="utf-8-sig"))
        if not isinstance(cfg, dict):
            raise PlanError("El JSON de configuración debe ser un objeto.")
        mapping = {
            "ramps": "ramp_count", "start_expno": "start_expno", "stride": "experiment_stride",
            "template_expno": "template_expno", "gradient_index": "gradient_index",
            "gradient_start": "gradient_start_percent", "gradient_stop": "gradient_stop_percent",
            "gradient_step": "gradient_step_percent", "delay_s": "delay_values_s",
            "delay_parameter": "delay_parameter", "pulse_us": "pulse_value_us",
            "pulse_parameter": "pulse_parameter", "pulse_program": "expected_pulse_program",
            "dataset_name": "expected_dataset_name", "ds": "dummy_scans",
        }
        for source, target in mapping.items():
            value = getattr(args, source)
            if value is not None:
                cfg[target] = value
        if args.confirm_delay_mapping:
            cfg["delay_mapping_confirmed"] = True
        if args.confirm_pulse_mapping:
            cfg["pulse_mapping_confirmed"] = True
        if args.example_only:
            cfg["example_only"] = True
        plan = write_bundle(cfg, args.out)
    except (PlanError, OSError, ValueError) as error:
        parser.exit(2, "Error: %s\n" % error)
    print("Generados %s experimentos (%s rampas x %s puntos) en %s" % (plan["experiment_count"], plan["config"]["ramp_count"], plan["points_per_ramp"], args.out.resolve()))
    print("Ejemplo: ejecución bloqueada." if plan["example_only"] else "Solo preparación; adquisición no incluida.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
