# -*- coding: utf-8 -*-
"""Portable, meaningful core tests: python test_calibration.py (also Jython)."""
from __future__ import division
import hashlib
import math
import os
import shutil
import struct
import tempfile
import unittest
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'python', 'topspin_console'))

import dosy_calibration as dc


class CalibrationTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="dosy_calibration_test_")

    def tearDown(self):
        shutil.rmtree(self.folder)

    def write(self, path, content):
        parent = os.path.dirname(path)
        if not os.path.isdir(parent):
            os.makedirs(parent)
        with open(path, "wb") as handle:
            handle.write(content.encode("utf-8") if not isinstance(content, bytes) else content)

    def experiment(self, number, gradient=10, scale=1.0, dtype=2, endian=0, nc=0,
                   overrides=None, proc_overrides=None, values=None):
        # A triangular reference peak on an exact 0.01 ppm grid, with known area.
        si = 1024
        offset, step = 10.0, 0.01
        if values is None:
            values = [1000000.0 * scale * max(0.0, 1 - abs(offset - i * step - 5) / .4)
                      for i in range(si)]
        parameters = {"PARMODE": 0, "PULPROG": "<stebpgp1s1d>",
                      "PROBHD": "<test probe>", "NUC1": "<1H>", "GPNAM6": "<SMSQ10.100>",
                      "D20": .05, "D16": .001, "P30": 600,
                      "GPZ6": gradient, "NS": 8, "RG": 200.44, "TE": 298.15}
        parameters.update(overrides or {})
        processing = {"SI": si, "SF": 500, "SW_p": step * si * 500,
                      "OFFSET": offset, "DTYPP": dtype, "BYTORDP": endian,
                      "NC_proc": nc, "STSI": si, "STSR": 0, "FTSIZE": si,
                      "FT_mod": 6, "PHC0": 0, "PHC1": 0, "BC_mod": 0,
                      "AXLEFT": 0, "AXRIGHT": 0}
        processing.update(proc_overrides or {})
        path = os.path.join(self.folder, str(number))
        self.write(os.path.join(path, "acqus"), "\n".join("##$%s= %s" % item for item in sorted(parameters.items())) + "\n##END=\n")
        self.write(os.path.join(path, "pdata", "1", "procs"), "\n".join("##$%s= %s" % item for item in sorted(processing.items())) + "\n##END=\n")
        if dtype == 0:
            stored = [int(round(v / (2.0 ** nc))) for v in values]
            code = "i"
        else:
            stored, code = values, "d"
        binary = struct.pack(("<" if endian == 0 else ">") + str(len(stored)) + code, *stored)
        self.write(os.path.join(path, "pdata", "1", "1r"), binary)
        self.write(os.path.join(path, "pulseprogram"), "; same test pulse program\n")
        self.write(os.path.join(path, "gpnam6"), "##TITLE= test shape\n")
        return path

    def ramp(self, **kwargs):
        for i, g in enumerate((8, 24, 40, 56, 72, 88, 96)):
            self.experiment(10 + i, gradient=g, scale=math.exp(-2.3 * (g / 100.0) ** 2), **kwargs)

    def analyze(self, **kwargs):
        args = {"dataset_dir": self.folder, "expnos": list(range(10, 17)), "procno": 1,
                "ppm_low": 4.45, "ppm_high": 5.55, "dref_1e9": 1.15,
                "reference_temperature_K": 298.15, "reference_label": "synthetic reference, D=1.15e-9"}
        args.update(kwargs)
        return dc.analyze_series(**args)

    def test_physics_units_and_read_only_sources(self):
        self.ramp()
        before = {}
        for root, dirs, files in os.walk(self.folder):
            for name in files:
                path = os.path.join(root, name)
                before[path] = hashlib.sha256(dc._read_bytes(path)).hexdigest()
        result = self.analyze()
        self.assertAlmostEqual(result["fit"]["slope_abs"], 2.3, places=12)
        self.assertAlmostEqual(result["fit"]["R2"], 1, places=12)
        self.assertAlmostEqual(result["calibration_profile"]["b_at_100_percent_s_m2"] / 1e9, 2.0, places=12)
        self.assertTrue(result["fit"]["I0_extrapolated"] > result["fit"]["Imax"])
        self.assertAlmostEqual(result["fit"]["I0_extrapolated"], 400000, places=7)
        self.assertEqual(len(result["sources"]), 35)
        for path, digest in before.items():
            self.assertEqual(hashlib.sha256(dc._read_bytes(path)).hexdigest(), digest)

    def test_endian_int32_nc_positive_and_negative(self):
        areas = []
        for number, endian, nc in ((1, 0, 2), (2, 1, 2), (3, 0, -2), (4, 1, -2)):
            spectrum = dc.read_processed_1r(self.experiment(number, dtype=0, endian=endian, nc=nc))
            areas.append(dc.integrate_region(spectrum, 4.4, 5.6)["integral"])
        for area in areas:
            self.assertAlmostEqual(area, 400000, places=7)

    def test_float64_is_direct_even_with_nonzero_nc(self):
        for endian in (0, 1):
            spectrum = dc.read_processed_1r(self.experiment(endian + 1, dtype=2, endian=endian, nc=-6))
            self.assertAlmostEqual(dc.integrate_region(spectrum, 4.4, 5.6)["integral"], 400000, places=7)

    def test_exact_ppm_boundaries_and_signed_area(self):
        spectrum = {"values": [1., 2., 3., 4., 5.], "ppm_start": 4., "ppm_step": 1., "ppm_end": 0.}
        # y(ppm)=5-ppm, integral from0.5 to3.5 equals9 exactly.
        self.assertAlmostEqual(dc.integrate_region(spectrum, .5, 3.5)["integral"], 9)
        with self.assertRaises(dc.CalibrationError):
            dc.integrate_region(spectrum, -.01, 3.5)
        with self.assertRaises(dc.CalibrationError):
            dc.integrate_region(spectrum, 1, 1)
        spectrum["values"] = [-1, -2, -3, -4, -5]
        with self.assertRaises(dc.CalibrationError):
            dc.integrate_region(spectrum, .5, 3.5)

    def test_jcamp_arrays_angle_brackets_and_comments(self):
        parsed = dc.parse_jcamp("##$D= (0..2)\n1 .05 1D-3 $$ ignored\n##$NAMES= (1..2)\n<a name with spaces> <b>\n##$PROBHD= <some\nprobe $$ text>\n##$EMPTY= <>\n##END=\n")
        self.assertEqual(parsed["D"], [1, .05, .001])
        self.assertEqual(parsed["NAMES"], [None, "a name with spaces", "b"])
        self.assertEqual(parsed["PROBHD"], "some\nprobe $$ text")
        self.assertEqual(parsed["EMPTY"], "")
        with self.assertRaises(dc.CalibrationError):
            dc.parse_jcamp("##$D= (0..3)\n1 2\n")

    def test_sequence_timing_shape_probe_rg_ns_drift_reject(self):
        for key, value in (("PULPROG", "<other>"), ("D20", .1), ("P30", 650),
                           ("D16", .002), ("GPNAM6", "<other>"), ("PROBHD", "<other>"),
                           ("RG", 100), ("NS", 16), ("NUC1", "<13C>")):
            self.ramp()
            self.experiment(13, gradient=56, scale=.5, overrides={key: value})
            with self.assertRaises(dc.CalibrationError):
                self.analyze()

    def test_temperature_drift_and_reference_mismatch(self):
        self.ramp()
        self.experiment(13, gradient=56, scale=.5, overrides={"TE": 300.0})
        with self.assertRaises(dc.CalibrationError):
            self.analyze()
        self.ramp()
        with self.assertRaises(dc.CalibrationError):
            self.analyze(reference_temperature_K=293.15)
        result = self.analyze(reference_temperature_K=293.15, max_reference_temperature_difference_K=6)
        self.assertFalse(result["temperature"]["correction_applied"])

    def test_zero_flat_growth_noise_and_distinct_gradient_reject(self):
        for gradients, values in (([0, 20, 40, 60], [1, 0, .4, .2]),
                                  ([0, 20, 40, 60], [1, 1, 1, 1]),
                                  ([0, 20, 40, 60], [1, 2, 3, 4]),
                                  ([10, -10, 20, -20], [4, 3, 2, 1]),
                                  ([0, 20, 40, 110], [4, 3, 2, 1])):
            with self.assertRaises(dc.CalibrationError):
                dc.fit_attenuation(gradients, values)
        spectrum = {"values": [1., -1., 1., -1., 1.], "ppm_start": 4., "ppm_step": 1., "ppm_end": 0.}
        with self.assertRaises(dc.CalibrationError):
            dc.integrate_region(spectrum, 0, 4)

    def test_truncated_nonfinite_2d_axis_and_unknown_layout_reject(self):
        for number, params, pparams in ((1, {"PARMODE": 1}, {}),
                                       (2, {}, {"STSR": 10}),
                                       (3, {}, {"STSI": 512}),
                                       (4, {}, {"DTYPP": 1}),
                                       (5, {}, {"BYTORDP": 2}),
                                       (6, {}, {"AXLEFT": 1, "AXRIGHT": 2})):
            path = self.experiment(number, overrides=params, proc_overrides=pparams)
            with self.assertRaises(dc.CalibrationError):
                dc.read_processed_1r(path)
        path = self.experiment(8)
        self.write(os.path.join(path, "pdata", "1", "1r"), b"short")
        with self.assertRaises(dc.CalibrationError):
            dc.read_processed_1r(path)
        path = self.experiment(9, values=[float("nan")] * 1024)
        with self.assertRaises(dc.CalibrationError):
            dc.read_processed_1r(path)
        path = self.experiment(10)
        self.write(os.path.join(path, "pdata", "1", "proc2s"), "##$SI= 1\n")
        with self.assertRaises(dc.CalibrationError):
            dc.read_processed_1r(path)

    def test_free_intercept_and_uncertainty(self):
        g = [10, 25, 40, 55, 70, 85]
        errors = [.02, -.01, .01, -.03, .02, -.01]
        values = [17 * math.exp(-3 * (p / 100.) ** 2 + e) for p, e in zip(g, errors)]
        fit = dc.fit_attenuation(g, values)
        self.assertTrue(2.9 < fit["slope_abs"] < 3.1)
        self.assertTrue(fit["slope_SE"] > 0)
        self.assertTrue(abs(sum(fit["residuals_log"])) < 1e-12)
        self.assertTrue(abs(sum(x * r for x, r in zip(fit["x"], fit["residuals_log"]))) < 1e-12)

    def test_gradient_ratio_direction_and_units(self):
        correction = dc.gradient_correction(50, 2, 1.6, "G/cm")
        self.assertAlmostEqual(correction["new_gradient_constant"], 50 * math.sqrt(1.25))
        self.assertFalse(correction["written_to_spectrometer"])
        with self.assertRaises(dc.CalibrationError):
            dc.gradient_correction(50, -1, 1.6)

    def test_mixed_processing_or_saved_sequence_reject(self):
        self.ramp()
        self.experiment(13, gradient=56, scale=.5, proc_overrides={"OFFSET": 10.1})
        with self.assertRaises(dc.CalibrationError):
            self.analyze()
        self.ramp()
        self.write(os.path.join(self.folder, "13", "pulseprogram"), "; modified sequence\n")
        with self.assertRaises(dc.CalibrationError):
            self.analyze()

    def test_other_delays_pulses_and_spoilers_must_match(self):
        for key, initial, changed in (("GPZ7", 30, 40), ("GPX7", 0, 2),
                                      ("GPY7", 0, 2), ("P1", 12, 15),
                                      ("D2", .002, .004), ("GPNAM7", "<SINE.100>", "<SMSQ10.100>")):
            self.ramp(overrides={key: initial})
            self.experiment(13, gradient=56, scale=.5, overrides={key: changed})
            with self.assertRaises(dc.CalibrationError):
                self.analyze()
        # The same guard applies to native JCAMP indexed arrays, not just aliases.
        self.ramp()
        for number in range(10, 17):
            path = os.path.join(self.folder, str(number), "acqus")
            content = dc._read_bytes(path).decode("utf-8")
            content += "##$GPZ= (0..7)\n0 0 0 0 0 0 %s %s\n" % (8 + (number - 10) * 4, 40 if number == 13 else 30)
            self.write(path, content)
        with self.assertRaises(dc.CalibrationError):
            self.analyze()

    def test_nonpositive_integral_at_series_level_reject(self):
        self.ramp()
        self.experiment(13, gradient=56, values=[0.] * 1024)
        with self.assertRaises(dc.CalibrationError):
            self.analyze()


if __name__ == "__main__":
    unittest.main(verbosity=2)
