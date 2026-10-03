# -*- coding: utf-8 -*-
"""Backend tests only; no Swing and no real TopCmds/hardware import."""
from __future__ import division, unicode_literals
import io
import json
import os
import shutil
import tempfile
import threading
import unittest

import calibration_workflow as workflow

try:
    from java.lang import RuntimeException as JavaRuntimeException
except ImportError:
    JavaRuntimeException = None


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.root=tempfile.mkdtemp(prefix='dosy_gui_workflow_')
        self.config={'mode':'p1','report_dir':self.root}
        self.controller=workflow.WorkflowController(demo=True)

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_preview_read_only_and_distinct_templates(self):
        first=self.controller.preview(self.config)
        second=self.controller.preview(dict(self.config,mode='gradient'))
        self.assertEqual(first['plan']['template'][1],'1000')
        self.assertEqual(second['plan']['template'][1],'10')
        self.assertEqual(os.listdir(self.root),[])
        self.assertTrue(first['ready'])
        self.assertTrue(first['demo'])

    def test_demo_p1_prepare_then_acquire_uses_real_signed_fit(self):
        prepared=self.controller.run(self.config,'prepare')
        self.assertEqual(prepared['status'],'prepared')
        self.assertFalse(any(call[0]=='ZG_SIMULATED' for call in self.controller.api.calls))
        snapshots=workflow.v3._snapshot_files(os.path.join(prepared['plan']['dataset_dir'],'1000'))
        events=[]
        result=self.controller.run(self.config,'acquire',callback=events.append)
        self.assertEqual(result['status'],'completed')
        self.assertAlmostEqual(result['result']['P90_us'],11,places=7)
        self.assertAlmostEqual(result['result']['P180_us'],22,places=7)
        self.assertTrue(min(result['result']['plot']['observed'])<0)
        self.assertEqual(len(result['result']['plot']['x']),22)
        self.assertTrue(result['result']['demo'])
        self.assertEqual(events[-1]['stage'],'finished')
        self.assertTrue(any(event['stage']=='result' for event in events))
        self.assertEqual(snapshots,workflow.v3._snapshot_files(os.path.join(prepared['plan']['dataset_dir'],'1000')))

    def test_demo_gradient_units_prior_b_and_explicit_html_label(self):
        cfg=dict(self.config,mode='gradient',gradient_b100_override_s_m2=1.8e9)
        response=self.controller.run(cfg,'acquire')
        result=response['result']
        self.assertAlmostEqual(result['fit']['slope_abs'],2.3,places=11)
        self.assertAlmostEqual(result['calibration_profile']['b_at_100_percent_s_m2']/1e9,2,places=11)
        self.assertAlmostEqual(result['prior_b100_comparison']['D_measured_1e9'],2.3/1.8,places=11)
        self.assertIsNone(result['bruker_gradient_proposal'])
        with io.open(os.path.join(response['output_dir'],'informe.html'),'r',encoding='utf-8') as handle:
            html=handle.read()
        self.assertIn('<h1>SYNTHETIC DEMO - NOT EXPERIMENTAL</h1>',html)
        self.assertEqual(html.count('<svg '),2)

    def test_stop_between_points_preserves_partial_data(self):
        stop=threading.Event()
        def observe(event):
            if event['stage']=='point_finished' and event['current']==2:
                stop.set()
        result=self.controller.run(self.config,'acquire',callback=observe,stop_event=stop)
        self.assertEqual(result['status'],'stopped')
        self.assertEqual(len([x for x in self.controller.api.calls if x[0]=='ZG_SIMULATED']),2)
        paths=workflow.v3.paths_for(result['plan'])
        self.assertTrue(os.path.isfile(os.path.join(paths[1],'fid')))
        self.assertFalse(os.path.isfile(os.path.join(paths[2],'fid')))
        self.assertIsNone(result['result'])

    def test_stop_before_start_no_parameter_copy(self):
        stop=threading.Event()
        stop.set()
        result=self.controller.run(self.config,'acquire',stop_event=stop)
        self.assertEqual(result['status'],'stopped')
        self.assertFalse(any(call[0] in ('XCMD','ZG_SIMULATED') for call in self.controller.api.calls))

    def test_prepared_files_changed_block_acquisition(self):
        first=self.controller.run(self.config,'prepare')
        changed=os.path.join(workflow.v3.paths_for(first['plan'])[2],'acqus')
        with io.open(changed,'a',encoding='utf-8') as handle:
            handle.write('\n$$ changed by test\n')
        with self.assertRaises(workflow.WorkflowError):
            self.controller.run(self.config,'acquire')
        self.assertFalse(any(call[0]=='ZG_SIMULATED' for call in self.controller.api.calls))

    def test_collision_does_not_overwrite_existing_series(self):
        first=self.controller.run(self.config,'prepare')
        before=dict((path,workflow.v3._snapshot_files(path)) for path in workflow.v3.paths_for(first['plan']))
        with self.assertRaises(workflow.WorkflowError):
            self.controller.run(self.config,'prepare')
        for path,snapshot in before.items():
            self.assertEqual(snapshot,workflow.v3._snapshot_files(path))

    def test_unknown_acquisition_return_stops_before_second(self):
        self.controller.run(self.config,'prepare')
        normal=self.controller.api.ZG
        def unknown(wait):
            normal(wait)
            return workflow._CommandResult(None)
        self.controller.api.ZG=unknown
        with self.assertRaises(workflow.WorkflowError):
            self.controller.run(self.config,'acquire')
        self.assertEqual(len([call for call in self.controller.api.calls if call[0]=='ZG_SIMULATED']),1)

    def test_apply_p1_review_new_parameters_only_and_power_guard(self):
        result=self.controller.run(self.config,'acquire')
        p90=result['result']['P90_us']
        with self.assertRaises(workflow.WorkflowError):
            self.controller.apply_p1(self.config,p90,1400,reviewed=False)
        calls_before=len([call for call in self.controller.api.calls if call[0]=='ZG_SIMULATED'])
        applied=self.controller.apply_p1(self.config,p90,1400,reviewed=True)
        self.assertTrue(applied['parameters_only'])
        self.assertFalse(applied['global_calibration_modified'])
        self.assertFalse(os.path.exists(os.path.join(applied['target_dir'],'fid')))
        self.assertFalse(os.path.exists(os.path.join(applied['target_dir'],'pdata','1','1r')))
        self.assertAlmostEqual(float(self.controller.api.parameters['1400']['P 1']),11,places=7)
        self.assertEqual(calls_before,len([call for call in self.controller.api.calls if call[0]=='ZG_SIMULATED']))
        self.controller.api.parameters['1000']['PLW 1']='0.2'
        with self.assertRaises(workflow.WorkflowError):
            self.controller.apply_p1(self.config,p90,1401,reviewed=True)
        self.assertFalse(os.path.exists(os.path.join(result['plan']['dataset_dir'],'1401')))

    def test_analyze_existing_points_does_not_acquire_or_modify(self):
        first=self.controller.run(self.config,'acquire')
        paths=workflow.v3.paths_for(first['plan'])
        before=dict((path,workflow.v3._snapshot_files(path)) for path in paths)
        calls=len(self.controller.api.calls)
        config=dict(self.config,analysis_expnos='1100-1121')
        second=self.controller.run(config,'analyze')
        self.assertEqual(second['status'],'analyzed')
        self.assertAlmostEqual(second['result']['P90_us'],11,places=7)
        self.assertFalse(any(call[0]=='ZG_SIMULATED' for call in self.controller.api.calls[calls:]))
        for path,snapshot in before.items():
            self.assertEqual(snapshot,workflow.v3._snapshot_files(path))

    def test_real_api_never_substituted_for_demo(self):
        with self.assertRaises(workflow.WorkflowError):
            workflow.WorkflowController(api=object(),demo=True)
        controller=workflow.WorkflowController()
        self.assertFalse(controller.environment()['api_available'])
        self.assertFalse(controller.context()['available'])

    def test_unicode_reports_and_reference_roundtrip(self):
        config=dict(self.config,mode='gradient',report_dir=os.path.join(self.root,'calibraci\u00f3n'),
                    reference_label='DEMO Patr\u00f3n \u03b1; agua')
        result=self.controller.run(config,'acquire')
        with io.open(os.path.join(result['output_dir'],'result.json'),'r',encoding='utf-8') as handle:
            saved=json.load(handle)
        self.assertEqual(saved['calibration_profile']['reference_label'],config['reference_label'])

    def test_demo_instrument_setup_copy_has_solvent_and_preserves_source(self):
        import instrument_setup
        context=self.controller.ensure_demo_inputs(self.config)
        source=context['current']
        self.assertEqual(source[1],'1000')
        self.assertEqual(float(self.controller.api.GETPAR('P 1')),22.)
        before=workflow.v3._snapshot_files(os.path.join(context['data_root'],context['dataset_name'],'1000'))
        result=instrument_setup.prepare_working_dataset(self.controller.api,source,1050)
        self.assertEqual(result['expected_solvent'],'D2O')
        self.assertTrue(result['parameters_only'])
        self.assertTrue(result['source_unchanged'])
        self.assertEqual(before,workflow.v3._snapshot_files(os.path.join(context['data_root'],context['dataset_name'],'1000')))
        self.assertFalse(any(call[0]=='ZG_SIMULATED' for call in self.controller.api.calls))

    def test_injected_api_gradient_uses_template10_and_restores1000(self):
        root=os.path.join(self.root,'injected_api_stub')
        os.mkdir(root)
        api=workflow._DemoApi(root,{})
        controller=workflow.WorkflowController(api=api,demo=False)
        config=dict(self.config,mode='gradient',ppm_low=4.5,ppm_high=4.9,dref_1e9=1.15,
                    reference_temperature_K=298.15,reference_label='INJECTED API STUB - SYNTHETIC TEST')
        original=api.CURDATA()
        result=controller.run(config,'acquire')
        self.assertEqual(result['plan']['template'][1],'10')
        self.assertEqual(api.CURDATA(),original)
        self.assertEqual(original[1],'1000')
        self.assertAlmostEqual(result['result']['fit']['slope_abs'],2.3,places=11)

    def _java_acquisition_failure(self,prepared,restore_failure=False):
        self.controller.ensure_demo_inputs(self.config)
        if prepared:
            self.controller.run(self.config,'prepare')
        original=self.controller.api.CURDATA()
        template=os.path.join(original[3],original[0],original[1])
        before=workflow.v3._snapshot_files(template)
        normal_zg=self.controller.api.ZG
        normal_re=self.controller.api.RE
        failed=[False]
        def bad_zg(wait):
            normal_zg(wait)
            failed[0]=True
            raise JavaRuntimeException('Injected Java ZG failure after partial FID')
        def guarded_re(dataset,*args,**kwargs):
            if restore_failure and failed[0] and list(dataset)==list(original):
                raise JavaRuntimeException('Injected Java restore failure')
            return normal_re(dataset,*args,**kwargs)
        self.controller.api.ZG=bad_zg
        self.controller.api.RE=guarded_re
        events=[]
        with self.assertRaises(workflow.WorkflowError):
            self.controller.run(self.config,'acquire',callback=events.append)
        output=events[-1]['data']['output_dir']
        receipt=workflow._read_json(os.path.join(output,'workflow.json'))
        execution=workflow._read_json(os.path.join(output,'execution.json'))
        self.assertEqual(receipt['status'],'failed')
        self.assertEqual(execution['state'],'stopped')
        self.assertIn('Injected Java ZG failure',receipt['error'])
        self.assertIn('Injected Java ZG failure',execution['error'])
        self.assertEqual(receipt['original_view_restored'],not restore_failure)
        self.assertEqual(before,workflow.v3._snapshot_files(template))
        self.assertTrue(execution['template_preserved'])
        self.assertEqual(len([x for x in self.controller.api.calls if x[0]=='ZG_SIMULATED']),1)
        self.assertFalse(any(x[0]=='EFP_SIMULATED' for x in self.controller.api.calls))
        dataset_dir=os.path.dirname(template)
        self.assertTrue(os.path.isfile(os.path.join(dataset_dir,'1100','fid')))
        self.assertFalse(os.path.isfile(os.path.join(dataset_dir,'1101','fid')))
        self.assertIsNone(self.controller._prepared)
        if restore_failure:
            self.assertIn('Injected Java restore failure',receipt['restore_error'])
        else:
            self.assertEqual(self.controller.api.CURDATA(),original)

    @unittest.skipIf(JavaRuntimeException is None,'Requires Jython Java exceptions')
    def test_java_failure_fresh_acquisition_retains_receipt_and_partial_fid(self):
        self._java_acquisition_failure(prepared=False)

    @unittest.skipIf(JavaRuntimeException is None,'Requires Jython Java exceptions')
    def test_java_failure_prepared_acquisition_retains_receipt_and_partial_fid(self):
        self._java_acquisition_failure(prepared=True)

    @unittest.skipIf(JavaRuntimeException is None,'Requires Jython Java exceptions')
    def test_java_restore_failure_does_not_hide_command_failure_receipt(self):
        self._java_acquisition_failure(prepared=True,restore_failure=True)

    @unittest.skipIf(JavaRuntimeException is None,'Requires Jython Java exceptions')
    def test_java_failure_applying_p1_retains_copy_and_restores_view(self):
        first=self.controller.run(self.config,'acquire')
        p90=first['result']['P90_us']
        original=self.controller.api.CURDATA()
        template=os.path.join(original[3],original[0],original[1])
        before=workflow.v3._snapshot_files(template)
        original_put=self.controller.api.PUTPAR
        def bad_put(name,value):
            if self.controller.api.CURDATA()[1]=='1400':
                raise JavaRuntimeException('Injected Java P1 parameter failure')
            return original_put(name,value)
        self.controller.api.PUTPAR=bad_put
        events=[]
        with self.assertRaises(workflow.WorkflowError):
            self.controller.apply_p1(self.config,p90,1400,reviewed=True,callback=events.append)
        output=events[-1]['data']['output_dir']
        receipt=workflow._read_json(os.path.join(output,'p1_application.json'))
        self.assertEqual(receipt['status'],'failed')
        self.assertIn('Injected Java P1 parameter failure',receipt['error'])
        self.assertTrue(receipt['source_preserved'])
        self.assertTrue(receipt['original_view_restored'])
        self.assertFalse(receipt['acquisition_started'])
        self.assertEqual(before,workflow.v3._snapshot_files(template))
        self.assertEqual(self.controller.api.CURDATA(),original)
        self.assertTrue(os.path.isfile(os.path.join(receipt['target_dir'],'acqus')))
        self.assertFalse(os.path.isfile(os.path.join(receipt['target_dir'],'fid')))
        self.assertEqual(float(self.controller.api.parameters['1400']['P 1']),22.)


if __name__=='__main__':
    unittest.main(verbosity=2)
