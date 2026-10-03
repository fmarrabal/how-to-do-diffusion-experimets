"""Repository portability, blocked examples and unchanged calibration inputs.

All acquisition/process calls are simulated by the separately tested stubs.
No TopSpin or network service is imported by this suite.
"""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
PYTHON = ROOT/'python'
sys.path.insert(0, str(PYTHON/'ramp_generator'))
sys.path.insert(0, str(ROOT/'tests'/'ramp_generator'))
sys.path.insert(0, str(ROOT/'tests'/'topspin_console'))
import generate_ramps
from test_ramp_generator import SimulatedTopSpin, runtime_module
from test_calibration import CalibrationTests


def digest_tree(folder):
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in folder.rglob('*') if p.is_file()}


def load_script(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PublicPackageTests(unittest.TestCase):
    def test_both_shipped_configs_block_runtime_creation(self):
        for path in (PYTHON/'ramp_generator').glob('config_*.json'):
            config = json.loads(path.read_text(encoding='utf-8'))
            self.assertTrue(config['example_only'], path.name)
            plan = generate_ramps.build_plan(config)
            self.assertEqual(plan['experiment_count'], 69)
            with tempfile.TemporaryDirectory() as temp:
                api = SimulatedTopSpin(temp)
                with self.assertRaises(RuntimeError):
                    runtime_module(plan)['prepare'](api, plan)
                self.assertEqual(api.calls, [])

    def test_public_model_has_no_sample_calibration_or_private_paths(self):
        profile = json.loads((PYTHON/'sequence_model.json').read_text(encoding='utf-8'))
        for key in ('slope_abs', 'slope_remeasured', 'Dref_1e9', 'temperature_K', 'reference_signal'):
            self.assertNotIn(key, profile)
        for source in profile['sources']:
            self.assertTrue(source['path'].startswith('model_identity/'))
            self.assertEqual(len(source['sha256']), 64)
        self.assertEqual(len(profile['model_source_sha256']), 64)
        for path in (PYTHON/'topspin_console'/'dist'/'dosy_workshop.py',
                     PYTHON/'topspin_console_v3'/'dist'/'dosy_workshop_v3.py'):
            text = path.read_text(encoding='utf-8')
            for private in ('EXPERIMENTOS-RMN', 'Users\\\\fmarr', 'E:\\\\', 'AppData', 'TBO_HDO_20260904_temperature_adjusted_v1'):
                self.assertNotIn(private, text)

    def test_builder_is_byte_reproducible_without_external_workspace(self):
        builder = load_script('_public_bundle_builder', PYTHON/'build_bundles.py')
        files = [PYTHON/'topspin_console'/'dosy_ramp_engine.py',
                 PYTHON/'topspin_console'/'dist'/'dosy_workshop.py',
                 PYTHON/'topspin_console_v3'/'dist'/'dosy_workshop_v3.py',
                 PYTHON/'build_sources_sha256.json']
        before = [p.read_bytes() for p in files]
        with contextlib.redirect_stdout(io.StringIO()):
            builder.main()
        self.assertEqual(before, [p.read_bytes() for p in files])

    def test_manifest_hashes_are_relative_and_match_distributed_sources(self):
        manifest = json.loads((PYTHON/'build_sources_sha256.json').read_text())
        for group in ('sources', 'outputs'):
            for relative, digest in manifest[group].items():
                self.assertFalse(Path(relative).is_absolute())
                self.assertNotIn('..', Path(relative).parts)
                self.assertEqual(hashlib.sha256((ROOT/relative).read_bytes()).hexdigest(), digest)
                self.assertNotIn(b'\r', (ROOT/relative).read_bytes(), 'Build inputs must remain LF on Git checkout')
        provenance = json.loads((PYTHON/'SOURCE_PROVENANCE.json').read_text(encoding='utf-8'))
        for entry in provenance['entries']:
            if entry['public_relative_path'] in ('python/topspin_console/dosy_calibration.py',
                                                 'python/topspin_console_v3/dosy_autorun.py',
                                                 'python/ramp_generator/generate_ramps.py'):
                content = (ROOT/entry['public_relative_path']).read_text(encoding='utf-8').replace('\r\n', '\n').replace('\r', '\n')
                self.assertEqual(hashlib.sha256(content.encode('utf-8')).hexdigest(), entry['original_content_sha256_lf'],
                                 'Original scientific source content changed beyond line endings')

    def test_read_only_cli_exports_calibration_and_preserves_original_bytes(self):
        cli = load_script('_public_calibration_cli', PYTHON/'calibrate_series.py')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            dataset = root/'synthetic_dataset'
            dataset.mkdir()
            fixture = CalibrationTests('test_physics_units_and_read_only_sources')
            fixture.folder = str(dataset)
            fixture.ramp()
            before = digest_tree(dataset)
            argv = ['--dataset', str(dataset), '--expnos', '10-16', '--ppm-low', '4.45', '--ppm-high', '5.55',
                    '--dref', '1.15', '--reference-temperature-k', '298.15', '--reference-name', 'Synthetic standard',
                    '--solvent', 'Synthetic medium', '--reference-source', 'Offline unit-test fixture only',
                    '--confirm-sequence-mapping', '--out', str(root/'new_report')]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(argv), 0)
            self.assertEqual(digest_tree(dataset), before)
            result = json.loads((root/'new_report'/'calibracion.json').read_text(encoding='utf-8'))
            self.assertAlmostEqual(result['fit']['slope_abs'], 2.3, places=12)
            self.assertAlmostEqual(result['calibration_profile']['b_at_100_percent_s_m2']/1e9, 2, places=12)
            self.assertIsNone(result['bruker_gradient_proposal'])
            self.assertTrue(result['sequence_mapping_confirmed_by_user'])
            self.assertTrue((root/'new_report'/'atenuacion_residuos.csv').is_file())
            self.assertIn('<svg ', (root/'new_report'/'informe.html').read_text(encoding='utf-8'))
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                cli.main(argv)
            self.assertEqual(digest_tree(dataset), before)

    def test_cli_rejects_missing_mapping_and_output_inside_dataset(self):
        cli = load_script('_public_cli_guards', PYTHON/'calibrate_series.py')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            argv = ['--dataset', temp, '--expnos', '10-16', '--ppm-low', '4.5', '--ppm-high', '5.5',
                    '--dref', '1.15', '--reference-temperature-k', '298.15', '--reference-name', 'Synthetic',
                    '--solvent', 'Synthetic', '--reference-source', 'Offline fixture', '--out', str(root/'new_report')]
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                cli.main(argv)
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                cli.main(argv + ['--confirm-sequence-mapping'])
            self.assertEqual(list(root.iterdir()), [])

    def test_cli_help_works_from_unrelated_working_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run([sys.executable, str(PYTHON/'calibrate_series.py'), '--help'], cwd=temp,
                                    text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0)
            self.assertIn('--reference-temperature-k', result.stdout)
            self.assertIn('--confirm-sequence-mapping', result.stdout)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PublicPackageTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
