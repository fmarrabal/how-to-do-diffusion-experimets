# -*- coding: utf-8 -*-
"""No hardware: complete TopCmds stubs under CPython and Bruker Jython 2.7."""
from __future__ import division, unicode_literals
import io
import json
import math
import os
import runpy
import shutil
import struct
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'tests', 'topspin_console'))
from test_calibration import CalibrationTests
runpy.run_path(os.path.join(ROOT, 'python', 'topspin_console_v3', 'dist', 'dosy_workshop_v3.py'), run_name='v3_test')
auto = sys.modules['_dosy_autorun']
core = sys.modules['_dosy_calibration']


class Thread(object):
    def __init__(self, code=0):
        self.code = code
    def getResult(self):
        return self.code


class StubTopSpin(object):
    WAIT_TILL_DONE = 1
    def __init__(self, root, mode='p1', fail_command=None, fail_code=-1):
        self.root = root
        self.name = 'synthetic'
        self.folder = os.path.join(root, self.name)
        os.mkdir(self.folder)
        self.fixture = CalibrationTests('test_physics_units_and_read_only_sources')
        self.fixture.folder = self.folder
        self.mode = mode
        self.true_p90_us = 10.
        program = 'zg' if mode == 'p1' else 'stebpgp1s1d'
        self.fixture.experiment(10, overrides={'PULPROG':'<'+program+'>', 'P1':10})
        self.current = [self.name,'10','1',root]
        self.parameters = {'10':{'PARMODE':'0','PULPROG':program,'P 1':'10','P 30':'600',
                           'D 20':'.05','D 16':'.001','D 1':'5','GPZ 6':'8','NS':'8','RG':'200.44',
                           'PHC0':'0','PHC1':'0','LB':'0','PL 1':'0','PLW 1':'0.1',
                           'SFO1':'500.13','O1':'2000','NUC1':'1H','PROBHD':'test probe'}}
        self.fail_command, self.fail_code = fail_command, fail_code
        self.calls, self.messages, self.views, self.answers, self.choices = [], [], [], [], []

    def CURDATA(self):
        return list(self.current)
    def GETPAR(self, name):
        return self.parameters[self.current[1]][name]
    def PUTPAR(self, name, value):
        self.calls.append(('PUTPAR',self.current[1],name,value))
        self.parameters[self.current[1]][name] = value
    def RE(self, data):
        self.calls.append(('RE', data[1]))
        self.current = list(data)
    def INPUT_DIALOG(self, *args):
        return self.answers.pop(0)
    def SELECT(self, *args):
        return self.choices.pop(0)
    def MSG(self, text):
        self.messages.append(text)
    def VIEWTEXT(self, *args):
        self.views.append(args)
    def XCMD(self, command, wait):
        self.calls.append(('XCMD',command,wait))
        if not command.startswith('wraparam '):
            raise AssertionError('Unexpected hardware command ' + command)
        expno = command.split()[1]
        target = os.path.join(self.folder, expno)
        source = os.path.join(self.folder, self.current[1])
        os.makedirs(os.path.join(target, 'pdata', '1'))
        for path in ('acqus','pulseprogram','gpnam6',os.path.join('pdata','1','procs')):
            shutil.copyfile(os.path.join(source,path),os.path.join(target,path))
        self.parameters[expno] = dict(self.parameters[self.current[1]])
        return Thread()
    def ZG(self, wait):
        self.calls.append(('ZG',self.current[1],wait))
        target = os.path.join(self.folder,self.current[1])
        with open(os.path.join(target,'fid'),'wb') as handle:
            handle.write(b'partial_or_complete_synthetic_fid')
        with io.open(os.path.join(target,'acqus'),'a',encoding='utf-8') as handle:
            handle.write('\n##$P1= '+str(self.GETPAR('P 1'))+'\n##$GPZ6= '+str(self.GETPAR('GPZ 6'))+'\n')
        return Thread(self.fail_code if self.fail_command == 'ZG' else 0)
    def EFP(self, wait):
        self.calls.append(('EFP',self.current[1],wait))
        if self.fail_command == 'EFP':
            return Thread(self.fail_code)
        amplitude = math.sin(math.pi*float(self.GETPAR('P 1'))/(2*self.true_p90_us)) if self.mode=='p1' else math.exp(-2.3*(float(self.GETPAR('GPZ 6'))/100.)**2)
        values = [1000000*amplitude*max(0,1-abs(10-i*.01-5)/.4) for i in range(1024)]
        with open(os.path.join(self.folder,self.current[1],'pdata','1','1r'),'wb') as handle:
            handle.write(struct.pack('<1024d',*values))
        return Thread()


class AutorunTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='dosy_v3_test_')
        self.report = os.path.join(self.root, 'report')
        os.mkdir(self.report)
    def tearDown(self):
        shutil.rmtree(self.root)
    def plan(self, api):
        values = list(range(2,45,2)) if api.mode=='p1' else [8,24,40,56,72,88,96]
        return auto.build_plan(api.CURDATA(),api.mode,500,values,api.GETPAR('PULPROG'))

    def test_prepare_only_no_hardware_preserves_template(self):
        api = StubTopSpin(self.root)
        before = auto._snapshot_files(os.path.join(api.folder,'10'))
        result = auto.run_plan(api,self.plan(api),self.report,False)
        self.assertEqual(result['state'],'prepared')
        self.assertEqual(before,auto._snapshot_files(os.path.join(api.folder,'10')))
        self.assertFalse(any(call[0] in ('ZG','EFP') for call in api.calls))
        self.assertEqual(api.current[1],'10')

    def test_full_p1_acquire_process_fit_fixed_phase(self):
        api = StubTopSpin(self.root)
        plan = self.plan(api)
        result = auto.run_plan(api,plan,self.report,True)
        self.assertEqual(result['state'],'acquired_and_processed')
        self.assertTrue(result['template_preserved'])
        sequence = [call for call in api.calls if call[0] in ('ZG','EFP')]
        self.assertEqual([call[0] for call in sequence],['ZG','EFP']*22)
        self.assertTrue(all(call[2] == 1 for call in sequence))
        fit = auto.analyze_p1(plan,4.4,5.6,5,15)
        self.assertAlmostEqual(fit['P90_us'],10,places=7)
        self.assertAlmostEqual(fit['P180_us'],20,places=7)
        self.assertAlmostEqual(fit['R2'],1,places=12)
        self.assertFalse(fit['written_to_instrument'])
        self.assertFalse(any('APK' in str(call) for call in api.calls))

    def test_full_gradient_acquire_process_and_calibrate(self):
        api = StubTopSpin(self.root,'gradient')
        plan = self.plan(api)
        auto.run_plan(api,plan,self.report,True)
        fit = core.analyze_series(api.folder,[r['expno'] for r in plan['rows']],1,4.4,5.6,
                                  1.15,298.15,'synthetic reference')
        self.assertAlmostEqual(fit['fit']['slope_abs'],2.3,places=12)
        self.assertAlmostEqual(fit['calibration_profile']['b_at_100_percent_s_m2']/1e9,2,places=12)

    def test_current_p1_22_can_be_180_and_p90_11_is_interior(self):
        api = StubTopSpin(self.root)
        api.parameters['10']['P 1'] = '22'
        api.true_p90_us = 11.
        values = [22*(.2+.2*i) for i in range(22)]
        plan = auto.build_plan(api.CURDATA(),'p1',500,values,'zg')
        auto.run_plan(api,plan,self.report,True)
        fit = auto.analyze_p1(plan,4.4,5.6,22*.25,22*1.5)
        self.assertAlmostEqual(fit['P90_us'],11,places=7)
        self.assertTrue(fit['search_range_us'][0] < fit['P90_us'] < fit['search_range_us'][1])

    def test_last_destination_collision_blocks_all_mutation(self):
        api = StubTopSpin(self.root)
        plan = self.plan(api)
        os.mkdir(auto.paths_for(plan)[-1])
        with self.assertRaises(RuntimeError):
            auto.run_plan(api,plan,self.report,True)
        self.assertEqual(api.calls,[])
        self.assertFalse(os.path.exists(auto.paths_for(plan)[0]))

    def test_failed_or_ambiguous_acquisition_stops_before_next_and_keeps_partial(self):
        for code in (-1,None):
            case = os.path.join(self.root,'case_'+str(code))
            os.mkdir(case)
            api = StubTopSpin(case,fail_command='ZG',fail_code=code)
            plan = self.plan(api)
            with self.assertRaises(RuntimeError):
                auto.run_plan(api,plan,self.report,True)
            self.assertEqual(len([c for c in api.calls if c[0]=='ZG']),1)
            self.assertFalse(any(c[0]=='EFP' for c in api.calls))
            self.assertTrue(os.path.isfile(os.path.join(auto.paths_for(plan)[0],'fid')))
            self.assertFalse(os.path.exists(os.path.join(auto.paths_for(plan)[1],'fid')))
            self.assertEqual(api.current[1],'10')
            with io.open(os.path.join(self.report,'execution.json'),'r',encoding='utf-8') as handle:
                journal=json.load(handle)
            self.assertEqual(journal['state'],'stopped')

    def test_processing_failure_stops_before_next_acquisition(self):
        api = StubTopSpin(self.root,fail_command='EFP')
        with self.assertRaises(RuntimeError):
            auto.run_plan(api,self.plan(api),self.report,True)
        self.assertEqual(len([c for c in api.calls if c[0]=='ZG']),1)

    def test_manual_rg_change_before_second_point_stops_before_its_zg(self):
        api = StubTopSpin(self.root)
        plan = self.plan(api)
        original_efp = api.EFP
        def change_next(wait):
            result = original_efp(wait)
            api.parameters['501']['RG'] = '100'
            return result
        api.EFP = change_next
        with self.assertRaises(RuntimeError):
            auto.run_plan(api,plan,self.report,True)
        self.assertEqual(len([c for c in api.calls if c[0]=='ZG']),1)
        self.assertFalse(os.path.exists(os.path.join(api.folder,'501','fid')))

    def test_nutation_no_negative_or_out_of_bounds_reject(self):
        pulses = list(range(2,45,2))
        signed = [math.sin(math.pi*t/20.) for t in pulses]
        with self.assertRaises(ValueError):
            auto.fit_nutation(pulses,[abs(v) for v in signed],5,15)
        with self.assertRaises(ValueError):
            auto.fit_nutation(pulses,signed,11,15)

    def test_nutation_and_plan_reject_nonfinite_values_and_invalid_time_limits(self):
        pulses = list(range(2,45,2))
        signed = [math.sin(math.pi*t/20.) for t in pulses]
        for value in (float('nan'), float('inf'), -float('inf')):
            changed = list(pulses)
            changed[3] = value
            with self.assertRaises(ValueError):
                auto.fit_nutation(changed, signed, 5, 15)
            changed = list(signed)
            changed[3] = value
            with self.assertRaises(ValueError):
                auto.fit_nutation(pulses, changed, 5, 15)
            with self.assertRaises(ValueError):
                auto.fit_nutation(pulses, signed, value, 15)
        for low, high in ((0,15), (-1,15), (15,5), (5,5)):
            with self.assertRaises(ValueError):
                auto.fit_nutation(pulses, signed, low, high)
        api = StubTopSpin(self.root)
        with self.assertRaises(ValueError):
            auto.build_plan(api.CURDATA(), 'p1', 500, [2,4,float('nan'),8], 'zg')

    def test_p1_processing_phase_change_reject(self):
        api = StubTopSpin(self.root)
        plan = self.plan(api)
        auto.run_plan(api,plan,self.report,True)
        path = os.path.join(auto.paths_for(plan)[2],'pdata','1','procs')
        with io.open(path,'a',encoding='utf-8') as handle:
            handle.write('\n##$PHC0= 180\n')
        with self.assertRaises(ValueError):
            auto.analyze_p1(plan,4.4,5.6,5,15)

    def test_main_cancel_no_files_or_hardware(self):
        api = StubTopSpin(self.root)
        api.choices = [3]
        auto.main(api)
        self.assertEqual(api.calls,[])
        self.assertEqual(api.messages,[])


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(AutorunTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
