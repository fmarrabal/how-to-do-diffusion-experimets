# -*- coding: utf-8 -*-
"""Meaningful unit checks using a fake API; no Bruker installation is changed."""
from __future__ import unicode_literals
import unittest
import os
import shutil
import tempfile
import instrument_setup as setup
try:
    from java.lang import RuntimeException as JavaRuntimeException
except ImportError:
    JavaRuntimeException = None


def write_file(path, data):
    with open(path, 'wb') as handle:
        handle.write(data)


class Result(object):
    def __init__(self, value):
        self.value = value
    def getResult(self):
        return self.value


class FakeAPI(object):
    test_directory = None
    def __init__(self, rc=0):
        self.rc = rc
        self.commands = []
        self.data = ['copy', '800', '1', self.test_directory]
        self.selected = []
        self.command_datasets = []
        self.solvent = 'CDCl3'
        self.demand = '298.15'
        self.status = '293.4'
        self.change_dataset = False
    def CURDATA(self):
        return list(self.data)
    def RE(self, data):
        self.selected.append(list(data))
        self.data = list(data)
    def GETPAR(self, name):
        return self.solvent if name == 'SOLVENT' else self.demand
    def GETPARSTAT(self, name):
        return self.status
    def XCMD(self, command):
        self.commands.append(command)
        self.command_datasets.append(list(self.data))
        if command == 'teget':
            self.status = '297.9'
        if self.change_dataset:
            self.data[1] = '801'
        return Result(self.rc)


def enabled():
    c = setup.default_setup_config()
    c.update({'enabled': True, 'supported_commands': list(setup.COMMANDS),
              'working_dataset': ['copy', '800', '1', FakeAPI.test_directory],
              'working_dataset_confirmed': True, 'expected_solvent': 'CDCl3',
              'lock_supported': True, 'probe_atm_supported': True,
              'topshim_configured': True, 'lock_confirmed': True,
              'temperature_controller_supported': True,
              'temperature_limits_K': [290, 305]})
    return c


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp(prefix='dosy_setup_test_')
        FakeAPI.test_directory = self.directory
        folder = os.path.join(self.directory, 'copy', '800', 'pdata', '1')
        os.makedirs(folder)
        write_file(os.path.join(folder, 'proc'), b'processing parameters')
        write_file(os.path.join(self.directory, 'copy', '800', 'acqu'), b'acquisition parameters')

    def tearDown(self):
        shutil.rmtree(self.directory)
        FakeAPI.test_directory = None

    def test_default_does_not_enable_or_infer_hardware(self):
        self.assertFalse(any(x['available'] for x in setup.describe_setup()))
        api = FakeAPI()
        with self.assertRaises(setup.SetupError):
            setup.run_setup_action(api, 'atma', setup.default_setup_config())
        self.assertEqual(api.commands, [])

    def test_each_button_dispatches_only_its_documented_command(self):
        for action, command in [('lock','lock -acqu'),('atma','atma'),('topshim','topshim')]:
            api = FakeAPI(); events = []
            report = setup.run_setup_action(api, action, enabled(), events.append)
            self.assertEqual(api.commands, [command])
            self.assertEqual([x['event'] for x in events], ['started','completed'])
            self.assertTrue(report['command_completed'])
            self.assertFalse(report['physical_validation'])
            self.assertIsNone(report['equilibrated'])

    def test_only_integer_zero_confirms_completion(self):
        for rc in [None, '0', False, True, 0.0, -1, 1]:
            api = FakeAPI(rc)
            with self.assertRaises(setup.SetupError) as cm:
                setup.run_setup_action(api, 'atma', enabled())
            self.assertFalse(cm.exception.report['command_completed'])
            self.assertEqual(api.commands, ['atma'])

    def test_arbitrary_command_and_unknown_config_rejected(self):
        for cmd in ['zg', 'atma; zg', 'teget\nzg', 'topshim initial']:
            api=FakeAPI(); c=enabled(); c['supported_commands']=[cmd]
            with self.assertRaises(setup.SetupError):
                setup.run_setup_action(api, 'atma', c)
            self.assertEqual(api.commands, [])
        c=enabled();c['shell_command']='anything'
        with self.assertRaises(setup.SetupError):setup.describe_setup(c)

    def test_atma_and_topshim_require_their_own_hardware_configuration(self):
        for action, field in [('atma','probe_atm_supported'),('topshim','topshim_configured'),('topshim','lock_confirmed'),('lock','lock_supported')]:
            api=FakeAPI();c=enabled();c[field]=False
            with self.assertRaises(setup.SetupError):setup.run_setup_action(api,action,c)
            self.assertEqual(api.commands, [])

    def test_solvent_mismatch_stops_lock_and_shim(self):
        for action in ['lock','topshim']:
            api=FakeAPI();api.solvent='D2O'
            with self.assertRaises(setup.SetupError):setup.run_setup_action(api,action,enabled())
            self.assertEqual(api.commands, [])

    def test_action_selects_working_copy_then_restores_original(self):
        api=FakeAPI();api.data[1]='1000'
        events=[]
        def callback(event):events.append((event['event'], api.CURDATA()))
        result=setup.run_setup_action(api,'atma',enabled(),callback)
        self.assertEqual(api.commands,['atma'])
        self.assertEqual(api.command_datasets[0][1],'800')
        self.assertEqual(api.CURDATA()[1],'1000')
        self.assertEqual(events[-1][1][1],'1000')
        self.assertTrue(result['original_dataset_restored'])

    def test_unexpected_dataset_change_during_command_is_not_accepted(self):
        api=FakeAPI();api.change_dataset=True
        with self.assertRaises(setup.SetupError) as cm:setup.run_setup_action(api,'atma',enabled())
        self.assertTrue(cm.exception.report['command_completed'])
        self.assertEqual(cm.exception.report['status'],'not_confirmed')
        self.assertEqual(api.CURDATA()[1],'800')

    def test_acquired_dataset_cannot_be_enabled_as_working_copy(self):
        for name in ['fid','ser','1r','1i','2rr','2ri','3rrr']:
            path=os.path.join(self.directory,'copy','800',name)
            write_file(path,b'original data')
            api=FakeAPI()
            with self.assertRaises(setup.SetupError):setup.run_setup_action(api,'atma',enabled())
            self.assertEqual(api.commands,[])
            self.assertEqual(api.selected,[])
            os.remove(path)

    def test_cached_te_is_never_live_temperature(self):
        api=FakeAPI();r=setup.read_temperature(api)
        self.assertEqual(r['demand_parameter_K'],298.15)
        self.assertEqual(r['stored_status_K'],293.4)
        self.assertIsNone(r['controller_readback_K'])
        self.assertFalse(r['fresh_controller_readback'])
        self.assertEqual(api.commands, [])

    def test_teget_requires_copy_and_reports_only_controller_readback(self):
        api=FakeAPI();c=enabled();c['working_dataset_confirmed']=False
        with self.assertRaises(setup.SetupError):setup.read_temperature(api,c,refresh=True)
        self.assertEqual(api.commands, [])
        r=setup.read_temperature(api,enabled(),refresh=True)
        self.assertEqual(api.commands,['teget'])
        self.assertEqual(r['controller_readback_K'],297.9)
        self.assertFalse(r['sample_temperature_verified'])
        self.assertIsNone(r['equilibrated'])

    def test_refresh_requires_boolean_not_truthy_text(self):
        api=FakeAPI()
        with self.assertRaises(setup.SetupError):setup.read_temperature(api,enabled(),refresh='false')
        self.assertEqual(api.commands,[])

    def test_teset_uses_numeric_argument_and_explicit_limits(self):
        api=FakeAPI();r=setup.run_setup_action(api,'set_temperature',enabled(),temperature_K=300)
        self.assertEqual(api.commands,['teset 300'])
        self.assertEqual(r['target_K'],300)
        self.assertIsNone(r['equilibrated'])
        for target in [0,289,306,float('nan'),float('inf'),'300; zg',True]:
            api=FakeAPI()
            with self.assertRaises(setup.SetupError):setup.run_setup_action(api,'set_temperature',enabled(),temperature_K=target)
            self.assertEqual(api.commands, [])

    def test_missing_temperature_limits_rejects_setting(self):
        api=FakeAPI();c=enabled();c['temperature_limits_K']=None
        with self.assertRaises(setup.SetupError):setup.run_setup_action(api,'set_temperature',c,temperature_K=300)
        self.assertEqual(api.commands, [])

    def test_callback_error_never_repeats_instrument_action(self):
        def broken(event):raise ValueError('closed UI')
        api=FakeAPI();r=setup.run_setup_action(api,'atma',enabled(),broken)
        self.assertEqual(api.commands,['atma'])
        self.assertTrue(r['command_completed'])
        self.assertEqual(len(r['callback_errors']),2)

    def test_unreadable_status_is_not_fresh_readback(self):
        class BrokenRead(FakeAPI):
            def GETPARSTAT(self,name):return 'unavailable'
        api=BrokenRead()
        with self.assertRaises(setup.SetupError) as cm:setup.run_setup_action(api,'read_temperature',enabled())
        self.assertNotIn('temperature',cm.exception.report)
        self.assertEqual(api.commands,['teget'])

    @unittest.skipUnless(JavaRuntimeException is not None, 'requires native Jython Java exceptions')
    def test_java_command_failure_has_receipt_and_restores_original(self):
        class BrokenCommand(FakeAPI):
            def XCMD(self,command):
                FakeAPI.XCMD(self,command)
                self.data[1]='801'
                raise JavaRuntimeException('simulated Java command failure')
        api=BrokenCommand();api.data[1]='1000';events=[]
        with self.assertRaises(setup.SetupError) as cm:
            setup.run_setup_action(api,'atma',enabled(),events.append)
        self.assertEqual(api.commands,['atma'])
        self.assertEqual(api.CURDATA()[1],'1000')
        self.assertTrue(cm.exception.report['original_dataset_restored'])
        self.assertFalse(cm.exception.report['command_completed'])
        self.assertEqual(cm.exception.report['status'],'not_confirmed')
        self.assertIn('simulated Java command failure',cm.exception.report['error'])
        self.assertEqual([event['event'] for event in events],['started','failed'])
        self.assertTrue(events[-1]['report']['original_dataset_restored'])

    @unittest.skipUnless(JavaRuntimeException is not None, 'requires native Jython Java exceptions')
    def test_java_selection_and_restore_failures_are_receipted(self):
        class BrokenSelection(FakeAPI):
            fail_expno='800'
            def RE(self,data):
                FakeAPI.RE(self,data)
                if data[1]==self.fail_expno:
                    raise JavaRuntimeException('simulated Java RE failure')
        for failure_expno in ['800','1000']:
            api=BrokenSelection();api.data[1]='1000';api.fail_expno=failure_expno
            with self.assertRaises(setup.SetupError) as cm:
                setup.run_setup_action(api,'atma',enabled())
            report=cm.exception.report
            self.assertEqual(report['status'],'not_confirmed')
            self.assertEqual(report['original_dataset_restored'],failure_expno=='800')
            self.assertEqual(report['command_completed'],failure_expno=='1000')
            self.assertEqual(api.commands,[] if failure_expno=='800' else ['atma'])

    @unittest.skipUnless(JavaRuntimeException is not None, 'requires native Jython Java exceptions')
    def test_java_callback_failure_does_not_repeat_action(self):
        def broken(event):raise JavaRuntimeException('simulated Java UI callback failure')
        api=FakeAPI();report=setup.run_setup_action(api,'atma',enabled(),broken)
        self.assertEqual(api.commands,['atma'])
        self.assertEqual(len(report['callback_errors']),2)
        self.assertTrue(report['command_completed'])
        self.assertTrue(report['original_dataset_restored'])

    @unittest.skipUnless(JavaRuntimeException is not None, 'requires native Jython Java exceptions')
    def test_java_temperature_read_failure_does_not_report_live_value(self):
        class BrokenRead(FakeAPI):
            def GETPARSTAT(self,name):raise JavaRuntimeException('simulated Java TE read failure')
        api=BrokenRead();metadata=setup.read_temperature(api)
        self.assertIsNone(metadata['stored_status_K'])
        self.assertFalse(metadata['fresh_controller_readback'])
        self.assertIn('simulated Java TE read failure',metadata['read_errors'][0])
        api.data[1]='1000'
        with self.assertRaises(setup.SetupError) as cm:
            setup.run_setup_action(api,'read_temperature',enabled())
        self.assertNotIn('temperature',cm.exception.report)
        self.assertTrue(cm.exception.report['original_dataset_restored'])
        self.assertEqual(api.CURDATA()[1],'1000')

    @unittest.skipUnless(JavaRuntimeException is not None, 'requires native Jython Java exceptions')
    def test_java_initial_context_failure_is_a_receipt_not_an_unhandled_throwable(self):
        class BrokenContext(FakeAPI):
            def CURDATA(self):raise JavaRuntimeException('simulated Java CURDATA failure')
        api=BrokenContext()
        with self.assertRaises(setup.SetupError) as cm:
            setup.run_setup_action(api,'atma',enabled())
        self.assertEqual(cm.exception.report['stage'],'read_current_dataset')
        self.assertEqual(cm.exception.report['status'],'not_confirmed')
        self.assertIsNone(cm.exception.report['original_dataset_restored'])
        self.assertFalse(cm.exception.report['command_completed'])
        self.assertEqual(api.commands,[])
        self.assertEqual(api.selected,[])


class CopyAPI(FakeAPI):
    """Filesystem-backed wraparam substitute, never an instrument connection."""
    def __init__(self, source, rc=0):
        FakeAPI.__init__(self, rc)
        self.source = list(source)
        self.data = ['previous', '9', '1', source[3]]
        self.inject_signal = None
        self.mutate_source = False
        self.skip_target = False
        self.fail_restore = False
        self.create_collision_on_re = False

    def GETPAR(self, name):
        return {'SOLVENT':'<CDCl3>', 'PULPROG':'<zg>'}.get(name, '298.15')

    def RE(self, data):
        if self.fail_restore and data[0] == 'previous':
            raise RuntimeError('simulated context restore failure')
        FakeAPI.RE(self, data)
        if self.create_collision_on_re and list(data) == self.source:
            path = os.path.join(self.source[3], self.source[0], '1050')
            if not os.path.isdir(path):os.makedirs(path)

    def XCMD(self, command):
        self.commands.append(command)
        self.command_datasets.append(list(self.data))
        if not command.startswith('wraparam '):
            raise AssertionError('Copy helper dispatched an instrument command')
        target = command.split(' ')[1]
        origin = os.path.join(self.source[3], self.source[0], self.source[1])
        destination = os.path.join(self.source[3], self.source[0], target)
        if not self.skip_target:
            processing = os.path.join(destination, 'pdata', self.source[2])
            os.makedirs(processing)
            for name in ['acqu','acqus']:
                shutil.copyfile(os.path.join(origin,name),os.path.join(destination,name))
            for name in ['proc','procs']:
                shutil.copyfile(os.path.join(origin,'pdata',self.source[2],name),
                                os.path.join(processing,name))
            if self.inject_signal:
                write_file(os.path.join(processing,self.inject_signal),b'unexpected acquired signal')
        if self.mutate_source:
            write_file(os.path.join(origin,'fid'),b'changed by simulated external actor')
        return Result(self.rc)


class WorkingCopyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp(prefix='dosy_copy_test_')
        self.source = ['real_sample','1000','2',self.directory]
        self.origin = os.path.join(self.directory,'real_sample','1000')
        processing = os.path.join(self.origin,'pdata','2')
        os.makedirs(processing)
        for name in ['acqu','acqus','fid','pulseprogram']:
            write_file(os.path.join(self.origin,name),('original '+name).encode('ascii'))
        for name in ['proc','procs','1r']:
            write_file(os.path.join(processing,name),('original '+name).encode('ascii'))
        self.target = os.path.join(self.directory,'real_sample','1050')

    def tearDown(self):
        shutil.rmtree(self.directory)

    def test_wraparam_creates_parameter_only_copy_and_verifies_source_hashes(self):
        api=CopyAPI(self.source); original=api.CURDATA()
        before=setup._source_snapshot(self.origin)
        report=setup.prepare_working_dataset(api,self.source,1050)
        self.assertEqual(api.commands,['wraparam 1050'])
        self.assertEqual(api.command_datasets,[self.source])
        self.assertEqual(report['working_dataset'],['real_sample','1050','2',self.directory])
        self.assertTrue(report['working_dataset_confirmed'])
        self.assertTrue(report['parameters_only'])
        self.assertTrue(report['source_unchanged'])
        self.assertEqual(report['source_hashes'],before)
        self.assertEqual(setup._source_snapshot(self.origin),before)
        self.assertEqual(report['expected_solvent'],'CDCl3')
        self.assertEqual(report['pulse_program'],'zg')
        self.assertEqual(api.CURDATA(),original)
        self.assertFalse(report['acquisition_started'])
        self.assertFalse(report['global_calibration_modified'])
        self.assertFalse(os.path.exists(os.path.join(self.target,'fid')))
        self.assertFalse(os.path.exists(os.path.join(self.target,'pdata','2','1r')))

    def test_existing_target_is_rejected_without_selecting_or_command(self):
        os.makedirs(self.target)
        write_file(os.path.join(self.target,'sentinel'),b'preserve')
        api=CopyAPI(self.source)
        with self.assertRaises(setup.SetupError):setup.prepare_working_dataset(api,self.source,1050)
        self.assertEqual(api.commands,[])
        self.assertEqual(api.selected,[])
        with open(os.path.join(self.target,'sentinel'),'rb') as handle:self.assertEqual(handle.read(),b'preserve')

    def test_source_alias_and_non_numeric_target_never_dispatch(self):
        for target in [1000,'01000',0,-1,True,1050.0,'1050; zg','1050\nzg','../1050']:
            api=CopyAPI(self.source)
            with self.assertRaises(setup.SetupError):setup.prepare_working_dataset(api,self.source,target)
            self.assertEqual(api.commands,[])
            self.assertEqual(api.selected,[])

    def test_rechecks_collision_after_source_selection(self):
        api=CopyAPI(self.source);api.create_collision_on_re=True;original=api.CURDATA()
        with self.assertRaises(setup.SetupError) as cm:setup.prepare_working_dataset(api,self.source,1050)
        self.assertEqual(api.commands,[])
        self.assertEqual(api.CURDATA(),original)
        self.assertFalse(cm.exception.report['working_dataset_confirmed'])

    def test_signal_copy_is_rejected_and_left_for_inspection(self):
        api=CopyAPI(self.source);api.inject_signal='1r';original=api.CURDATA()
        with self.assertRaises(setup.SetupError) as cm:setup.prepare_working_dataset(api,self.source,1050)
        self.assertFalse(cm.exception.report['working_dataset_confirmed'])
        self.assertTrue(cm.exception.report['target_exists'])
        self.assertTrue(os.path.isfile(os.path.join(self.target,'pdata','2','1r')))
        self.assertEqual(api.CURDATA(),original)
        self.assertTrue(cm.exception.report['source_unchanged'])

    def test_unknown_or_failed_wraparam_result_never_confirms_partial_target(self):
        for rc in [None,'0',False,0.0,-1,1]:
            api=CopyAPI(self.source,rc);original=api.CURDATA()
            with self.assertRaises(setup.SetupError) as cm:setup.prepare_working_dataset(api,self.source,1050)
            self.assertFalse(cm.exception.report['working_dataset_confirmed'])
            self.assertTrue(cm.exception.report['target_exists'])
            self.assertEqual(api.CURDATA(),original)
            shutil.rmtree(self.target)

    def test_missing_target_after_zero_result_is_not_success(self):
        api=CopyAPI(self.source);api.skip_target=True
        with self.assertRaises(setup.SetupError) as cm:setup.prepare_working_dataset(api,self.source,1050)
        self.assertFalse(cm.exception.report['target_exists'])
        self.assertFalse(cm.exception.report['working_dataset_confirmed'])

    def test_source_mutation_is_detected_without_overwriting_the_evidence(self):
        before=setup._source_snapshot(self.origin)
        api=CopyAPI(self.source);api.mutate_source=True
        with self.assertRaises(setup.SetupError) as cm:setup.prepare_working_dataset(api,self.source,1050)
        self.assertFalse(cm.exception.report['source_unchanged'])
        self.assertFalse(cm.exception.report['working_dataset_confirmed'])
        self.assertEqual(cm.exception.report['source_hashes'],before)
        with open(os.path.join(self.origin,'fid'),'rb') as handle:
            self.assertEqual(handle.read(),b'changed by simulated external actor')

    def test_missing_source_parameters_stops_before_re(self):
        os.remove(os.path.join(self.origin,'pdata','2','proc'))
        os.remove(os.path.join(self.origin,'pdata','2','procs'))
        api=CopyAPI(self.source)
        with self.assertRaises(setup.SetupError):setup.prepare_working_dataset(api,self.source,1050)
        self.assertEqual(api.commands,[])
        self.assertEqual(api.selected,[])

    def test_restore_failure_is_explicit_not_confirmed_success(self):
        api=CopyAPI(self.source);api.fail_restore=True
        with self.assertRaises(setup.SetupError) as cm:setup.prepare_working_dataset(api,self.source,1050)
        self.assertFalse(cm.exception.report['original_dataset_restored'])
        self.assertFalse(cm.exception.report['working_dataset_confirmed'])
        self.assertTrue(cm.exception.report['source_unchanged'])

    def test_invalid_dataset_layout_is_rejected(self):
        for name, directory in [('..',self.directory),('C:escape',self.directory),('real_sample','relative')]:
            source=[name,'1000','2',directory];api=CopyAPI(self.source)
            with self.assertRaises(setup.SetupError):setup.prepare_working_dataset(api,source,1050)
            self.assertEqual(api.commands,[])

    @unittest.skipUnless(JavaRuntimeException is not None, 'requires native Jython Java exceptions')
    def test_java_wraparam_failure_preserves_source_and_restores_original(self):
        class BrokenCopy(CopyAPI):
            def XCMD(self,command):
                CopyAPI.XCMD(self,command)
                raise JavaRuntimeException('simulated Java wraparam failure')
        api=BrokenCopy(self.source);original=api.CURDATA()
        before=setup._source_snapshot(self.origin)
        with self.assertRaises(setup.SetupError) as cm:
            setup.prepare_working_dataset(api,self.source,1050)
        report=cm.exception.report
        self.assertFalse(report['working_dataset_confirmed'])
        self.assertEqual(report['status'],'not_confirmed')
        self.assertIn('simulated Java wraparam failure',report['error'])
        self.assertTrue(report['original_dataset_restored'])
        self.assertTrue(report['source_unchanged'])
        self.assertTrue(report['target_exists'])
        self.assertEqual(api.CURDATA(),original)
        self.assertEqual(setup._source_snapshot(self.origin),before)


if __name__ == '__main__':
    unittest.main()
