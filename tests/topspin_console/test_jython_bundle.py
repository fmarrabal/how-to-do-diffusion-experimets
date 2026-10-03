# -*- coding: utf-8 -*-
"""Portable end-to-end native console smoke tests, including Jython 2.7.

TopCmds is simulated: no spectrometer acquisition or settings are touched.
The bundled distribution is loaded, rather than substituting source modules.
"""
from __future__ import unicode_literals
import hashlib
import io
import json
import os
import runpy
import shutil
import sys
import tempfile
import unittest

from test_calibration import CalibrationTests

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
runpy.run_path(os.path.join(ROOT, "python", "topspin_console", "dist", "dosy_workshop.py"), run_name="bundle_integration_test")
ui = sys.modules["_dosy_console_ui"]
calibration = sys.modules["_dosy_calibration"]


class FakeTopCmds(object):
    """Only read-only dataset inspection and native dialog functions are exposed."""
    def __init__(self, root, name, answers=None, choices=None):
        self.current = [name, "10", "1", root]
        self.answers = list(answers or [])
        self.choices = list(choices or [])
        self.views, self.messages, self.calls = [], [], []

    def CURDATA(self):
        self.calls.append("CURDATA")
        return list(self.current)

    def GETPAR(self, name):
        self.calls.append("GETPAR " + name)
        if name != "PULPROG":
            raise AssertionError("Unexpected GETPAR " + name)
        return "stebpgp1s1d"

    def INPUT_DIALOG(self, *args, **kwargs):
        self.calls.append("INPUT_DIALOG")
        return self.answers.pop(0)

    def SELECT(self, *args, **kwargs):
        self.calls.append("SELECT")
        return self.choices.pop(0)

    def VIEWTEXT(self, *args):
        self.views.append(args)

    def MSG(self, message):
        self.messages.append(message)

    def assert_consumed(self):
        if self.answers or self.choices:
            raise AssertionError("Unused simulated dialogs: %r / %r" % (self.answers, self.choices))


def read_text(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def hashes(folder):
    result = {}
    for root, dirs, files in os.walk(folder):
        for name in files:
            path = os.path.join(root, name)
            with open(path, "rb") as handle:
                result[os.path.relpath(path, folder)] = hashlib.sha256(handle.read()).hexdigest()
    return result


class JythonBundleTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="dosy_native_bundle_")
        self.name = "muestra_\u00e1_DOSY"
        self.dataset = os.path.join(self.root, self.name)
        os.mkdir(self.dataset)
        self.reports = os.path.join(self.root, "informes_\u00f1")
        self.fixture = CalibrationTests("test_physics_units_and_read_only_sources")
        self.fixture.folder = self.dataset
        self.fixture.ramp(overrides={"PROBHD": "<sonda_\u00e1>"})
        self.originals = hashes(self.dataset)

    def tearDown(self):
        self.assertEqual(hashes(self.dataset), self.originals, "Experimental input changed")
        shutil.rmtree(self.root)

    def answers(self):
        return [["10-16", "1", "4.45", "5.55", self.reports],
                ["Patr\u00f3n \u03b1 / agua, D sint\u00e9tico", "1.15", "298.15", "0.5", "0.5"]]

    def test_calibration_main_writes_json_csv_html_with_unicode(self):
        api = FakeTopCmds(self.root, self.name, self.answers(), [1, 1])
        ui.main(api)
        api.assert_consumed()
        self.assertEqual(api.messages, [], "UI reported an exception: %r" % api.messages)
        outputs = os.listdir(self.reports)
        self.assertEqual(len(outputs), 1)
        folder = os.path.join(self.reports, outputs[0])
        result = json.loads(read_text(os.path.join(folder, "calibracion.json")))
        self.assertEqual(result["calibration_profile"]["reference_label"], self.answers()[1][0])
        self.assertAlmostEqual(result["fit"]["slope_abs"], 2.3, places=12)
        self.assertAlmostEqual(result["calibration_profile"]["b_at_100_percent_s_m2"] / 1e9, 2, places=12)
        self.assertEqual(len(result["sources"]), 35)
        self.assertTrue(all(row["acquisition"]["PROBHD"] == "sonda_\u00e1" for row in result["rows"]))
        csv = read_text(os.path.join(folder, "atenuacion_residuos.csv"))
        self.assertEqual(len(csv.splitlines()), 8)
        self.assertIn('"residual_log"', csv)
        self.assertIn("sonda_", csv)
        html = read_text(os.path.join(folder, "informe.html"))
        self.assertEqual(html.count("<svg "), 2)
        self.assertEqual(html.count("<circle "), 14)
        self.assertIn("Residuos del ajuste", html)
        self.assertIn("Atenuacion e intercepto libre", html)
        self.assertIn("ln(I / Imax)", html)
        self.assertTrue(api.views)
        qa = os.path.join(self.root, ".qa")
        if not os.path.isdir(qa):
            os.makedirs(qa)
        # Exercise export using temporary synthetic-only output. No generated
        # report or paths are retained in the public source tree.
        shutil.copyfile(os.path.join(folder, "informe.html"), os.path.join(qa, "informe_simulado.html"))
        shutil.copyfile(os.path.join(folder, "calibracion.json"), os.path.join(qa, "calibracion_simulada.json"))
        # Exercise raw non-ASCII text and CSV values, beyond JSON's escaped output.
        raw = os.path.join(folder, "unicode_roundtrip.txt")
        ui.write_text(raw, "Calibraci\u00f3n: \u03b1, \u0394, se\u00f1al")
        self.assertEqual(read_text(raw), "Calibraci\u00f3n: \u03b1, \u0394, se\u00f1al")
        text_csv = ui.csv_text([{"autor": "Ignacio Fern\u00e1ndez"}], ["autor"])
        ui.write_text(os.path.join(folder, "unicode.csv"), text_csv)
        self.assertIn("Ignacio Fern\u00e1ndez", read_text(os.path.join(folder, "unicode.csv")))

    def test_main_cancel_and_calibration_dialog_cancel_do_not_write(self):
        api = FakeTopCmds(self.root, self.name, [], [-1])
        ui.main(api)
        api.assert_consumed()
        self.assertFalse(os.path.exists(self.reports))
        api = FakeTopCmds(self.root, self.name, [None], [1])
        ui.main(api)
        api.assert_consumed()
        self.assertFalse(os.path.exists(self.reports))
        self.assertEqual(api.messages, [])

    def ramp_answers(self):
        return [["10", "1", "100", "100", "8", "96", "4", "6", "16", "stebpgp1s1d"],
                ["D20", "50,100,150", "3", self.reports]]

    def test_ramp_export_and_final_cancel(self):
        api = FakeTopCmds(self.root, self.name, self.ramp_answers(), [2])
        ui.ramp_flow(api)
        api.assert_consumed()
        self.assertFalse(os.path.exists(self.reports))
        api = FakeTopCmds(self.root, self.name, self.ramp_answers(), [1])
        ui.ramp_flow(api)
        api.assert_consumed()
        folders = os.listdir(self.reports)
        self.assertEqual(len(folders), 1)
        folder = os.path.join(self.reports, folders[0])
        plan = json.loads(read_text(os.path.join(folder, "plan.json")))
        self.assertEqual(plan["experiment_count"], 69)
        self.assertEqual(len(plan["rows"]), 69)
        self.assertEqual([plan["rows"][i]["expno"] for i in (0, 22, 23, 45, 46, 68)], [100, 122, 200, 222, 300, 322])
        self.assertEqual(len(read_text(os.path.join(folder, "plan.csv")).splitlines()), 70)
        self.assertFalse(os.path.exists(os.path.join(self.dataset, "100")))
        self.assertFalse(os.path.exists(os.path.join(folder, "preparacion.json")))

    def test_bundled_core_rejects_p1_and_spoiler_changes(self):
        for key in ("P1", "GPZ7"):
            self.fixture.ramp(overrides={"PROBHD": "<sonda_\u00e1>", key: 12})
            self.fixture.experiment(13, gradient=56, scale=.5, overrides={"PROBHD": "<sonda_\u00e1>", key: 24})
            with self.assertRaises(calibration.CalibrationError):
                calibration.analyze_series(self.dataset, list(range(10, 17)), 1, 4.45, 5.55,
                                           1.15, 298.15, "test")
        # Restore fixture bytes before the read-only tearDown check.
        self.fixture.ramp(overrides={"PROBHD": "<sonda_\u00e1>"})


if __name__ == "__main__":
    # Do not collect the imported fixture's TestCase as another suite here.
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(JythonBundleTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
