"""End-to-end console dialogs with simulated TopSpin and real parameter-copy engine."""
import hashlib
import json
from pathlib import Path
import runpy
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOURCE=ROOT/'python'/'topspin_console'
sys.path.insert(0,str(ROOT/'python'/'ramp_generator'))
sys.path.insert(0,str(ROOT/'tests'/'ramp_generator'))
import generate_ramps as original_generator
from test_ramp_generator import SimulatedTopSpin, verified_delta_config
runpy.run_path(str(SOURCE/'dist'/'dosy_workshop.py'),run_name='console_test')
ui=sys.modules['_dosy_console_ui']
engine=sys.modules['_dosy_ramp_engine']

class DialogTopSpin(SimulatedTopSpin):
    def __init__(self,root,answers,choices):
        super().__init__(root)
        self.answers=list(answers)
        self.choices=list(choices)
        self.messages=[]
        self.views=[]
    def INPUT_DIALOG(self,*args,**kwargs):
        return self.answers.pop(0)
    def SELECT(self,*args,**kwargs):
        return self.choices.pop(0)
    def VIEWTEXT(self,*args):
        self.views.append(args)
    def MSG(self,text):
        self.messages.append(text)

def dialogs(report):
    return [['10','1','100','100','8','96','4','6','16','stebpgp1s1d'],
            ['D20','50,100,150','3',str(report)]]

def source_hashes(api):
    return {str(p.relative_to(api.template)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in api.template.rglob('*') if p.is_file()}

class ConsoleTests(unittest.TestCase):
    def test_native_plan_matches_existing_generator(self):
        for cfg in ({},verified_delta_config(),{'gradient_start_percent':0.1,'gradient_stop_percent':0.5,'gradient_step_percent':0.1}):
            self.assertEqual(engine.build_plan(cfg),original_generator.build_plan(cfg))

    def test_native_create_69_explicit_destinations_preserves_template(self):
        with tempfile.TemporaryDirectory() as temp:
            api=DialogTopSpin(temp,dialogs(Path(temp)/'reports'),[0])
            before=source_hashes(api)
            ui.ramp_flow(api)
            self.assertEqual(source_hashes(api),before)
            self.assertEqual(api.CURDATA(),['sample','10','1',temp])
            for first,d in ((100,.05),(200,.1),(300,.15)):
                self.assertEqual(float(api.parameters[str(first+21)]['GPZ 6']),92)
                self.assertEqual(float(api.parameters[str(first+22)]['GPZ 6']),96)
                for e in range(first,first+23):
                    self.assertEqual(float(api.parameters[str(e)]['D 20']),d)
                    self.assertEqual(float(api.parameters[str(e)]['DS']),16)
                    self.assertEqual(api.parameters[str(e)]['P 30'],'600')
                    self.assertFalse((Path(temp)/'sample'/str(e)/'fid').exists())
            files=list((Path(temp)/'reports').glob('*/preparacion.json'))
            self.assertEqual(len(files),1)
            self.assertFalse(json.loads(files[0].read_text())['acquisition_started'])

    def test_cancel_does_not_write(self):
        with tempfile.TemporaryDirectory() as temp:
            api=DialogTopSpin(temp,[None],[])
            before=source_hashes(api)
            ui.ramp_flow(api)
            self.assertEqual(api.calls,[])
            self.assertEqual(source_hashes(api),before)
            self.assertEqual(sorted(api.parameters),['10'])

    def test_export_only_leaves_all_experiments_untouched(self):
        with tempfile.TemporaryDirectory() as temp:
            api=DialogTopSpin(temp,dialogs(Path(temp)/'reports'),[1])
            before=source_hashes(api)
            ui.ramp_flow(api)
            self.assertEqual(api.calls,[])
            self.assertEqual(source_hashes(api),before)
            saved=list((Path(temp)/'reports').glob('*/plan.json'))
            self.assertEqual(len(saved),1)
            self.assertEqual(json.loads(saved[0].read_text())['experiment_count'],69)

    def test_last_destination_collision_blocks_every_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            api=DialogTopSpin(temp,dialogs(Path(temp)/'reports'),[0])
            (Path(temp)/'sample'/'322').mkdir()
            with self.assertRaisesRegex(RuntimeError,'destinos ya existen'):
                ui.ramp_flow(api)
            self.assertEqual(api.calls,[])
            self.assertFalse((Path(temp)/'sample'/'100').exists())

    def test_ambiguous_ranges_and_duplicate_expnos_fail(self):
        self.assertEqual(ui.parse_expnos('10-12,15'),[10,11,12,15])
        for text in ('10-12,12','5-1','0','1;2','1.5','1-100000'):
            with self.assertRaises(ValueError):
                ui.parse_expnos(text)

    def test_bundle_requires_no_python3_only_runtime_imports(self):
        source=(SOURCE/'dist'/'dosy_workshop.py').read_text()
        self.assertNotIn('import tkinter',source)
        self.assertNotIn('import numpy',source)
        self.assertNotIn('from pathlib',source)

    def test_gradient_calculation_does_not_write_global_configuration(self):
        with tempfile.TemporaryDirectory() as temp:
            api=DialogTopSpin(temp,[['40','G/cm','2','1','298.15','test reference',temp]],[1])
            before=source_hashes(api)
            ui.gradient_flow(api)
            self.assertEqual(api.calls,[])
            self.assertEqual(source_hashes(api),before)
            report=next(Path(temp).glob('constante_gradiente_*/constante_propuesta.json'))
            data=json.loads(report.read_text())
            self.assertAlmostEqual(data['G_new'],40*2**.5)
            self.assertFalse(data['instrument_calibration_modified'])

    def test_primary_calibration_flow_reads_series_and_exports_graphs_without_edits(self):
        from test_calibration import CalibrationTests
        with tempfile.TemporaryDirectory() as temp:
            fixture=CalibrationTests()
            fixture.folder=str(Path(temp)/'sample')
            Path(fixture.folder).mkdir()
            fixture.ramp()
            class CalibrationDialogs:
                def __init__(self):
                    self.answers=[['10-16','1','4.5','5.5',str(Path(temp)/'reports')],
                                  ['Synthetic test standard','1.5','298.15','0.5','0.5']]
                    self.messages=[]
                def CURDATA(self): return ['sample','10','1',temp]
                def INPUT_DIALOG(self,*args): return self.answers.pop(0)
                def VIEWTEXT(self,*args): self.messages.append(args)
                def SELECT(self,*args): return 1
            def hashes():
                return {str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in Path(fixture.folder).rglob('*') if p.is_file()}
            before=hashes()
            ui.calibration_flow(CalibrationDialogs())
            self.assertEqual(hashes(),before)
            output=next((Path(temp)/'reports').glob('calibracion_*'))
            result=json.loads((output/'calibracion.json').read_text())
            self.assertAlmostEqual(result['fit']['slope_abs'],2.3,places=9)
            self.assertAlmostEqual(result['calibration_profile']['b_at_100_percent_s_m2']/1e9,2.3/1.5,places=9)
            html=(output/'informe.html').read_text()
            self.assertEqual(html.count('<svg '),2)
            self.assertIn('Residuos del ajuste',html)
            self.assertTrue((output/'atenuacion_residuos.csv').is_file())

    def test_physical_gradient_units_and_strict_model_identity(self):
        import copy
        identity={name: next(x['sha256'] for x in ui.TBO_PROFILE['sources']
                           if x['path'].replace('\\','/').endswith('/'+name))
                  for name in ('pulseprogram','gpnam6')}
        b=(267.52218744e6*0.4*0.0012)**2*0.81*(.05-.32525*.0012-.001/2)
        result={'fit':{'relative_slope_uncertainty_1sigma':.02},
                'calibration_profile':{'b_at_100_percent_s_m2':b,'saved_file_hashes':identity,
                  'scope':{'PULPROG':'stebpgp1s1d','NUC1':'1H','GPNAM6':'SMSQ10.100',
                           'P30':600,'D20':.05,'D16':.001}}}
        estimate=ui.known_sequence_gradient(result)
        self.assertAlmostEqual(estimate['G_max_T_m'],.4)
        self.assertAlmostEqual(estimate['G_max_G_cm'],40)
        self.assertAlmostEqual(estimate['G_max_G_mm'],4)
        self.assertAlmostEqual(estimate['G_relative_SE_regression_only'],.01)
        for key in ('pulseprogram','gpnam6'):
            changed=copy.deepcopy(result)
            changed['calibration_profile']['saved_file_hashes'][key]='different bytes'
            self.assertIsNone(ui.known_sequence_gradient(changed))
        changed=copy.deepcopy(result)
        changed['calibration_profile']['scope']['NUC1']='13C'
        self.assertIsNone(ui.known_sequence_gradient(changed))

if __name__=='__main__':
    unittest.main()
