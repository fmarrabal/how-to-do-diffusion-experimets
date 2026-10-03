"""Pruebas offline: límites del plan, salida y simulación del flujo TopSpin."""
import copy
import csv
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parents[2] / 'python' / 'ramp_generator'
sys.path.insert(0, str(SOURCE))

import generate_ramps as generator


HERE = SOURCE


def runtime_module(plan):
    source = (HERE / "topspin_prepare_template.py").read_text(encoding="utf-8")
    source = source.replace("PLAN = json.loads(__PLAN_JSON_LITERAL__)", "PLAN = json.loads(" + repr(json.dumps(plan)) + ")")
    namespace = {"__name__": "test_runtime"}
    exec(compile(source, "generated_topspin.py", "exec"), namespace)
    return namespace


def verified_delta_config():
    return {
        "expected_pulse_program": "stebpgp1s1d",
        "delay_parameter": "D20",
        "delay_values_s": [0.05, 0.1, 0.15],
        "delay_mapping_confirmed": True,
        "dummy_scans": 16,
    }


class SimulatedTopSpin:
    """Simula solo APIs usadas; no valida el espectrómetro ni TopSpin real."""
    WAIT_TILL_DONE = 99

    def __init__(self, root):
        self.root = Path(root)
        self.current = ["sample", "10", "1", str(self.root)]
        self.calls = []
        self.parameters = {"10": {"PULPROG": "stebpgp1s1d", "PARMODE": "0", "D 20": "0.05", "P 30": "600", "GPZ 6": "3", "DS": "4"}}
        self.template = self.root / "sample" / "10"
        (self.template / "pdata" / "1").mkdir(parents=True)
        (self.template / "acqu").write_text("MASTER ACQU MUST NOT CHANGE")
        (self.template / "acqus").write_text("MASTER ACQUS MUST NOT CHANGE")
        (self.template / "fid").write_bytes(b"ORIGINAL RAW DATA\x00\xff")
        (self.template / "pdata" / "1" / "proc").write_text("MASTER PROC MUST NOT CHANGE")
        (self.template / "pdata" / "1" / "1r").write_bytes(b"ORIGINAL PROCESSED DATA")

    def CURDATA(self):
        return list(self.current)

    def RE(self, dataset):
        self.calls.append(("RE", list(dataset)))
        if not (self.root / dataset[0] / str(dataset[1])).is_dir():
            raise RuntimeError("dataset does not exist")
        self.current = list(dataset)

    def GETPAR(self, name):
        return self.parameters[str(self.current[1])][name]

    def PUTPAR(self, name, value):
        self.calls.append(("PUTPAR", self.current[1], name, value))
        self.parameters[str(self.current[1])][name] = value

    def XCMD(self, command, wait):
        self.calls.append(("XCMD", command, wait))
        assert wait == self.WAIT_TILL_DONE
        verb, expno = command.split()
        assert verb == "wraparam"
        target = self.root / self.current[0] / expno
        target.mkdir(exist_ok=False)
        (target / "pdata" / self.current[2]).mkdir(parents=True)
        for filename in ("acqu", "acqus"):
            shutil.copyfile(self.template / filename, target / filename)
        shutil.copyfile(self.template / "pdata" / "1" / "proc", target / "pdata" / self.current[2] / "proc")
        self.parameters[expno] = copy.deepcopy(self.parameters[str(self.current[1])])


class PlanTests(unittest.TestCase):
    def test_default_has_complete_three_ramps_without_92_overwrite(self):
        plan = generator.build_plan()
        self.assertEqual(plan["experiment_count"], 69)
        self.assertEqual(plan["points_per_ramp"], 23)
        for ramp, first in ((1, 100), (2, 200), (3, 300)):
            rows = [row for row in plan["rows"] if row["ramp"] == ramp]
            self.assertEqual([r["expno"] for r in rows], list(range(first, first + 23)))
            self.assertEqual([r["gradient_percent"] for r in rows], list(range(8, 97, 4)))
            self.assertEqual(rows[-2]["gradient_percent"], 92)
            self.assertEqual(rows[-1]["gradient_percent"], 96)
            self.assertTrue(all(r["dummy_scans"] == 16 for r in rows))
            self.assertTrue(all(r["delay_s"] is None for r in rows))
        self.assertEqual(len({r["expno"] for r in plan["rows"]}), 69)

    def test_colliding_ranges_and_template_are_rejected(self):
        for cfg in ({"experiment_stride": 22}, {"start_expno": 10}, {"template_expno": 211}):
            with self.subTest(cfg=cfg), self.assertRaises(generator.PlanError):
                generator.build_plan(cfg)

    def test_invalid_gradients_and_nonfinite_values(self):
        for cfg in ({"gradient_step_percent": 0}, {"gradient_step_percent": 3}, {"gradient_stop_percent": 101}, {"gradient_start_percent": -1}, {"gradient_start_percent": float("nan")}, {"gradient_step_percent": float("inf")}, {"gradient_step_percent": 0.00001}):
            with self.subTest(cfg=cfg), self.assertRaises(generator.PlanError):
                generator.build_plan(cfg)

    def test_decimal_steps_do_not_accumulate_roundoff(self):
        plan = generator.build_plan({"gradient_start_percent": 0.1, "gradient_stop_percent": 0.5, "gradient_step_percent": 0.1})
        self.assertEqual([r["gradient_percent"] for r in plan["rows"][:5]], [0.1, 0.2, 0.3, 0.4, 0.5])

    def test_explicit_delay_mapping_and_sequence_required(self):
        cfg = {"delay_parameter": "D20", "delay_values_s": [0.05, 0.1, 0.15]}
        with self.assertRaises(generator.PlanError):
            generator.build_plan(cfg)
        cfg["delay_mapping_confirmed"] = True
        with self.assertRaises(generator.PlanError):
            generator.build_plan(cfg)
        cfg["expected_pulse_program"] = "stebpgp1s1d"
        plan = generator.build_plan(cfg)
        self.assertEqual([plan["rows"][i]["delay_s"] for i in (0, 23, 46)], [0.05, 0.1, 0.15])
        self.assertTrue(all(row["pulse_us"] is None for row in plan["rows"]))

    def test_delay_length_units_and_pulse_mapping(self):
        for patch in ({"delay_values_s": [0.05]}, {"delay_values_s": [0.05, 0, 0.15]}, {"delay_parameter": "P30"}, {"pulse_parameter": "P30", "pulse_value_us": 600}):
            cfg = verified_delta_config()
            cfg.update(patch)
            with self.subTest(patch=patch), self.assertRaises(generator.PlanError):
                generator.build_plan(cfg)
        cfg = verified_delta_config()
        cfg.update({"pulse_parameter": "p30", "pulse_value_us": 600, "pulse_mapping_confirmed": True})
        self.assertEqual(generator.build_plan(cfg)["rows"][0]["pulse_us"], 600)

    def test_example_is_reviewable_but_runtime_blocked(self):
        plan = generator.build_plan({"example_only": True, "delay_parameter": "D20", "delay_values_s": [0.05, 0.1, 0.15]})
        self.assertFalse(plan["can_prepare"])
        with tempfile.TemporaryDirectory() as tmp:
            api = SimulatedTopSpin(tmp)
            with self.assertRaisesRegex(RuntimeError, "EJEMPLO"):
                runtime_module(plan)["prepare"](api, plan)
            self.assertEqual(api.calls, [])

    def test_bundle_is_reviewable_and_never_overwrites_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "bundle"
            plan = generator.write_bundle(verified_delta_config(), output)
            stored = json.loads((output / "plan.json").read_text(encoding="utf-8"))
            self.assertEqual(stored["rows"], plan["rows"])
            with (output / "plan.csv").open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 69)
            self.assertEqual(rows[46]["delay_s"], "0.15")
            generated = (output / "dosy_prepare_ramps.py").read_text(encoding="utf-8")
            compile(generated, "dosy_prepare_ramps.py", "exec")
            self.assertEqual((output / "dosy_prepare_ramps").read_text(), "xpy dosy_prepare_ramps.py\n")
            macro = (output / "macro_expandida_REFERENCIA_NO_EJECUTAR.txt").read_text()
            self.assertEqual(sum(line.startswith("wraparam ") for line in macro.splitlines()), 69)
            self.assertEqual(sum(line == "ds 16" for line in macro.splitlines()), 69)
            self.assertIn("re 122 1\ngpz6 96\nd20 0.05\nds 16", macro)
            self.assertNotIn("zg", macro)
            self.assertNotIn("rga", macro)
            with self.assertRaises(FileExistsError):
                generator.write_bundle(verified_delta_config(), output)


class RuntimeSimulationTests(unittest.TestCase):
    def test_complete_preparation_preserves_master_and_raw(self):
        plan = generator.build_plan(verified_delta_config())
        with tempfile.TemporaryDirectory() as tmp:
            api = SimulatedTopSpin(tmp)
            original_bytes = {str(p.relative_to(api.template)): p.read_bytes() for p in api.template.rglob("*") if p.is_file()}
            original_parameters = copy.deepcopy(api.parameters["10"])
            original_dataset = api.CURDATA()
            created = runtime_module(plan)["prepare"](api, plan)
            self.assertEqual(len(created), 69)
            self.assertEqual(api.CURDATA(), original_dataset)
            self.assertEqual(api.parameters["10"], original_parameters)
            self.assertEqual(original_bytes, {str(p.relative_to(api.template)): p.read_bytes() for p in api.template.rglob("*") if p.is_file()})
            for row in plan["rows"]:
                pars = api.parameters[str(row["expno"])]
                self.assertEqual(float(pars["GPZ 6"]), row["gradient_percent"])
                self.assertEqual(float(pars["D 20"]), row["delay_s"])
                self.assertEqual(pars["P 30"], "600")
                self.assertEqual(pars["DS"], "16")
            self.assertFalse(any(p.name in ("fid", "1r") for directory in created for p in Path(directory).rglob("*")))
            self.assertTrue(all(call[1].startswith("wraparam ") for call in api.calls if call[0] == "XCMD"))

    def test_collision_at_last_destination_prevents_all_mutations(self):
        plan = generator.build_plan(verified_delta_config())
        with tempfile.TemporaryDirectory() as tmp:
            api = SimulatedTopSpin(tmp)
            occupied = Path(tmp) / "sample" / "322"
            occupied.mkdir()
            sentinel = occupied / "fid"
            sentinel.write_bytes(b"PROTECT THIS")
            with self.assertRaisesRegex(RuntimeError, "ya existen"):
                runtime_module(plan)["prepare"](api, plan)
            self.assertEqual(api.calls, [])
            self.assertFalse((Path(tmp) / "sample" / "100").exists())
            self.assertEqual(sentinel.read_bytes(), b"PROTECT THIS")

    def test_wrong_program_and_2d_template_stop_before_write(self):
        plan = generator.build_plan(verified_delta_config())
        for key, value in (("PULPROG", "ledbpgp2s"), ("PARMODE", "1")):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                api = SimulatedTopSpin(tmp)
                api.parameters["10"][key] = value
                with self.assertRaises(RuntimeError):
                    runtime_module(plan)["prepare"](api, plan)
                self.assertFalse(any(call[0] in ("XCMD", "PUTPAR") for call in api.calls))
                self.assertEqual(api.CURDATA()[1], "10")

    def test_unknown_layout_and_dataset_name_do_not_write(self):
        plan = generator.build_plan(verified_delta_config())
        with tempfile.TemporaryDirectory() as tmp:
            api = SimulatedTopSpin(tmp)
            api.current.append("old_user")
            with self.assertRaisesRegex(RuntimeError, "cuatro campos"):
                runtime_module(plan)["prepare"](api, plan)
            self.assertEqual(api.calls, [])
            api.current.pop()
            plan["config"]["expected_dataset_name"] = "another_sample"
            with self.assertRaisesRegex(RuntimeError, "Dataset inesperado"):
                runtime_module(plan)["prepare"](api, plan)
            self.assertEqual(api.calls, [])

    def test_write_failure_stops_and_restores_original(self):
        plan = generator.build_plan(verified_delta_config())
        with tempfile.TemporaryDirectory() as tmp:
            api = SimulatedTopSpin(tmp)
            normal_putpar = api.PUTPAR
            def fail_at_second(name, value):
                if api.current[1] == "101":
                    raise RuntimeError("simulated write failure")
                normal_putpar(name, value)
            api.PUTPAR = fail_at_second
            with self.assertRaisesRegex(RuntimeError, "Directorios nuevos ya creados: 2"):
                runtime_module(plan)["prepare"](api, plan)
            self.assertFalse((Path(tmp) / "sample" / "102").exists())
            self.assertEqual(api.CURDATA()[1], "10")
            self.assertTrue((Path(tmp) / "sample" / "100").exists())

    def test_raw_copied_unexpectedly_causes_stop_before_parameters(self):
        plan = generator.build_plan(verified_delta_config())
        with tempfile.TemporaryDirectory() as tmp:
            api = SimulatedTopSpin(tmp)
            normal_xcmd = api.XCMD
            def bad_copy(command, wait):
                normal_xcmd(command, wait)
                (Path(tmp) / "sample" / command.split()[1] / "fid").write_bytes(b"UNEXPECTED")
            api.XCMD = bad_copy
            with self.assertRaisesRegex(RuntimeError, "archivo de senal inesperado"):
                runtime_module(plan)["prepare"](api, plan)
            self.assertFalse(any(call[0] == "PUTPAR" for call in api.calls))
            self.assertTrue((Path(tmp) / "sample" / "100" / "fid").exists())

    def test_silent_restore_failure_is_reported(self):
        plan = generator.build_plan(verified_delta_config())
        with tempfile.TemporaryDirectory() as tmp:
            api = SimulatedTopSpin(tmp)
            normal_re = api.RE
            def silent_restore_failure(dataset):
                if str(dataset[1]) == "10" and api.current[1] == "322":
                    return
                normal_re(dataset)
            api.RE = silent_restore_failure
            with self.assertRaisesRegex(RuntimeError, "No se ha podido restaurar"):
                runtime_module(plan)["prepare"](api, plan)

    def test_copy_then_exception_counts_partial_directory(self):
        plan = generator.build_plan(verified_delta_config())
        with tempfile.TemporaryDirectory() as tmp:
            api = SimulatedTopSpin(tmp)
            normal_xcmd = api.XCMD
            def create_then_fail(command, wait):
                normal_xcmd(command, wait)
                raise RuntimeError("simulated command failed after mkdir")
            api.XCMD = create_then_fail
            with self.assertRaisesRegex(RuntimeError, "Directorios nuevos ya creados: 1"):
                runtime_module(plan)["prepare"](api, plan)
            self.assertEqual(api.CURDATA()[1], "10")


if __name__ == "__main__":
    unittest.main(verbosity=2)
