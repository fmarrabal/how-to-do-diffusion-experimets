# -*- coding: utf-8 -*-
"""Swing-independent controller, Python 3 / native TopSpin Jython 2.7.

Real TopCmds calls MUST be scheduled by the GUI on a TopSpin CmdThread, never
on the Swing EDT or an arbitrary Python worker. This module creates no threads.
"""
from __future__ import division, unicode_literals
import io
import json
import math
import os
import platform
import runpy
import shutil
import struct
import sys
import uuid

try:
    text_type = unicode
except NameError:
    text_type = str

try:
    from java.lang import Throwable as JavaThrowable
except ImportError:
    JavaThrowable = Exception
API_ERRORS = (Exception, JavaThrowable)

if '_dosy_autorun' not in sys.modules:
    bundle = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          'topspin_console_v3', 'dist', 'dosy_workshop_v3.py')
    runpy.run_path(bundle, run_name='_gui_v3_dependency')
v3 = sys.modules['_dosy_autorun']
core = sys.modules['_dosy_calibration']
legacy = sys.modules['_dosy_console_ui']
engine = sys.modules['_dosy_ramp_engine']


class WorkflowError(ValueError):
    pass


class StopRequested(RuntimeError):
    pass


def _stopped(event):
    if event is None:
        return False
    for name in ('is_set', 'isSet', 'get'):
        method = getattr(event, name, None)
        if method is not None:
            return bool(method())
    return bool(event() if callable(event) else event)


def _values(value):
    if isinstance(value, (list, tuple)):
        return [engine.number(v, 'sweep value') for v in value]
    return [engine.number(v.strip(), 'sweep value') for v in text_type(value).split(',') if v.strip()]


def _read_json(path):
    with io.open(path, 'r', encoding='utf-8') as handle:
        return json.load(handle)


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':'))


def _signature(plan):
    return _canonical(dict((k, plan[k]) for k in ('mode', 'template', 'expected_program', 'rows')))


def _expnos(value):
    if isinstance(value, (tuple, list)):
        result = [engine.integer(v, 'EXPNO') for v in value]
        if len(result) != len(set(result)):
            raise WorkflowError('Duplicate EXPNO')
        return result
    return legacy.parse_expnos(text_type(value))


class _ObservedApi(object):
    def __init__(self, api, controller, plan, stop_event):
        self.api, self.controller, self.plan, self.stop_event = api, controller, plan, stop_event
        self.rows = dict((text_type(r['expno']), r) for r in plan['rows'])
        self.stop_requested = False

    def __getattr__(self, name):
        return getattr(self.api, name)

    def check_stop(self):
        if _stopped(self.stop_event):
            self.stop_requested = True
            raise StopRequested('Stopped between points at operator request')

    def XCMD(self, command, wait):
        if command.startswith('wraparam '):
            self.check_stop()
            expno = command.split()[1]
            row = self.rows[expno]
            self.controller._emit('preparing', current=row['point'] - 1,
                                  total=len(self.rows), expno=row['expno'])
        return self.api.XCMD(command, wait=wait)

    def ZG(self, wait):
        self.check_stop()
        row = self.rows[text_type(self.api.CURDATA()[1])]
        self.controller._emit('acquiring', current=row['point'] - 1,
                              total=len(self.rows), expno=row['expno'])
        return self.api.ZG(wait=wait)

    def EFP(self, wait):
        row = self.rows[text_type(self.api.CURDATA()[1])]
        self.controller._emit('processing', current=row['point'] - 1,
                              total=len(self.rows), expno=row['expno'])
        result = self.api.EFP(wait=wait)
        if result is not None and hasattr(result, 'getResult') and text_type(result.getResult()) in ('0', '0.0'):
            self.controller._emit('point_finished', current=row['point'],
                                  total=len(self.rows), expno=row['expno'])
        return result


class _CommandResult(object):
    def __init__(self, code=0):
        self.code = code
    def getResult(self):
        return self.code


class _DemoApi(object):
    """Labelled synthetic Bruker files; no TopCmds or spectrometer dependency."""
    WAIT_TILL_DONE = 1
    is_demo = True

    def __init__(self, root, config):
        self.root, self.name = root, 'DEMO_DOSY'
        self.folder = os.path.join(root, self.name)
        os.makedirs(self.folder)
        self.parameters, self.calls = {}, []
        self.p1_expno = text_type(int(config.get('p1_template_expno', 1000)))
        self.gradient_expno = text_type(int(config.get('gradient_template_expno', 10)))
        if self.p1_expno == self.gradient_expno:
            raise WorkflowError('Demo templates must be different EXPNO')
        self.procno = text_type(int(config.get('template_procno', 1)))
        for expno, program, pulse in ((self.p1_expno, 'zg', 22.),
                                       (self.gradient_expno, 'stebpgp1s1d', 11.)):
            self.parameters[expno] = {'PARMODE':'0', 'PULPROG':program, 'P 1':text_type(pulse),
                'P 30':'600', 'D 20':'.05', 'D 16':'.001', 'D 1':'5', 'GPZ 6':'8',
                'NS':'8', 'DS':'16', 'RG':'200.44', 'PHC0':'0', 'PHC1':'0', 'LB':'0',
                'PL 1':'0', 'PLW 1':'.1', 'SFO1':'500.13', 'O1':'2000',
                'NUC1':'1H', 'PROBHD':'SYNTHETIC DEMO PROBE', 'SOLVENT':'D2O', 'TE':'298.15'}
            os.makedirs(os.path.join(self.folder, expno, 'pdata', self.procno))
            self._write_parameters(expno)
            self._write_spectrum(expno)
        self.current = [self.name, self.p1_expno, self.procno, root]

    def _write_parameters(self, expno):
        p = self.parameters[expno]
        acquisition = {'PARMODE':0, 'PULPROG':'<'+p['PULPROG']+'>', 'PROBHD':'<'+p['PROBHD']+'>',
            'NUC1':'<1H>', 'GPNAM6':'<SYNTHETIC_DEMO_SHAPE>', 'P1':p['P 1'], 'P30':p['P 30'],
            'D20':p['D 20'], 'D16':p['D 16'], 'D1':p['D 1'], 'GPZ6':p['GPZ 6'], 'NS':p['NS'],
            'DS':p['DS'], 'RG':p['RG'], 'TE':p['TE'], 'SOLVENT':'<'+p['SOLVENT']+'>',
            'PL1':p['PL 1'], 'PLW1':p['PLW 1']}
        processing = {'SI':2048, 'FTSIZE':2048, 'STSI':2048, 'STSR':0, 'SF':500.13,
            'SW_p':2048*.005*500.13, 'OFFSET':8, 'DTYPP':2, 'BYTORDP':0, 'NC_proc':0,
            'FT_mod':6, 'PHC0':p['PHC0'], 'PHC1':p['PHC1'], 'LB':p['LB'], 'BC_mod':0,
            'AXLEFT':0, 'AXRIGHT':0}
        folder = os.path.join(self.folder, expno)
        for values, filenames, location in ((acquisition, ('acqu','acqus'), folder),
                (processing, ('proc','procs'), os.path.join(folder,'pdata',self.procno))):
            text = '##TITLE= SYNTHETIC DEMO - NOT EXPERIMENTAL\n' + '\n'.join(
                '##$%s= %s' % item for item in sorted(values.items())) + '\n##END=\n'
            for name in filenames:
                legacy.write_text(os.path.join(location,name),text)
        legacy.write_text(os.path.join(folder,'pulseprogram'),'; SYNTHETIC DEMO '+p['PULPROG']+'\n')
        legacy.write_text(os.path.join(folder,'gpnam6'),'##TITLE= SYNTHETIC DEMO SHAPE\n')
        legacy.write_text(os.path.join(folder,'pdata',self.procno,'title'),'SYNTHETIC DEMO. P90=11 us; D=1.15e-9 m2/s; b100=2e9 s/m2.\n')

    def _write_spectrum(self, expno):
        p = self.parameters[expno]
        if p['PULPROG'] == 'zg':
            amplitude = math.sin(math.pi*float(p['P 1'])/22.)
        else:
            amplitude = math.exp(-2.3*(float(p['GPZ 6'])/100.)**2)
        # A signed, noiseless Lorentzian reference centered at 4.7 ppm.
        values = [1000000*amplitude/(1+((8-i*.005-4.7)/.03)**2) for i in range(2048)]
        path = os.path.join(self.folder,expno,'pdata',self.procno,'1r')
        with open(path,'wb') as handle:
            handle.write(struct.pack('<2048d',*values))

    def CURDATA(self):
        return list(self.current)
    def RE(self, dataset):
        self.calls.append(('RE',dataset[1]))
        if text_type(dataset[1]) not in self.parameters:
            raise WorkflowError('Demo EXPNO does not exist')
        self.current = [text_type(v) for v in dataset]
    def GETPAR(self, key):
        return self.parameters[self.current[1]][key]
    def GETPARSTAT(self, key):
        return self.GETPAR(key)
    def PUTPAR(self, key, value):
        self.parameters[self.current[1]][key] = text_type(value)
        self._write_parameters(self.current[1])
    def XCMD(self, command, wait=1):
        self.calls.append(('XCMD',command,wait))
        if not command.startswith('wraparam '):
            raise WorkflowError('Demo accepts parameter copy only')
        expno = command.split()[1]
        target = os.path.join(self.folder,expno)
        if os.path.exists(target):
            raise WorkflowError('Demo target collision')
        source = os.path.join(self.folder,self.current[1])
        os.makedirs(os.path.join(target,'pdata',self.procno))
        for filename in ('acqu','acqus','pulseprogram','gpnam6'):
            shutil.copyfile(os.path.join(source,filename),os.path.join(target,filename))
        for filename in ('proc','procs','title'):
            shutil.copyfile(os.path.join(source,'pdata',self.procno,filename),
                            os.path.join(target,'pdata',self.procno,filename))
        self.parameters[expno] = dict(self.parameters[self.current[1]])
        return _CommandResult()
    def ZG(self, wait=1):
        self.calls.append(('ZG_SIMULATED',self.current[1],wait))
        self._write_parameters(self.current[1])
        with open(os.path.join(self.folder,self.current[1],'fid'),'wb') as handle:
            handle.write(b'SYNTHETIC_DEMO_PLACEHOLDER_NOT_AN_ACQUIRED_FID')
        return _CommandResult()
    def EFP(self, wait=1):
        self.calls.append(('EFP_SIMULATED',self.current[1],wait))
        self._write_spectrum(self.current[1])
        return _CommandResult()


class WorkflowController(object):
    def __init__(self, api=None, demo=False):
        if demo and api is not None:
            raise WorkflowError('Demo must not be given a real TopCmds API')
        self.api, self.demo = api, bool(demo)
        self.events, self.callback_errors, self._callback = [], [], None
        self._prepared = None
        self.last_results = {}

    def environment(self):
        return {'python_version':platform.python_version(), 'is_jython':platform.python_implementation()=='Jython',
                'api_available':self.api is not None, 'demo':self.demo,
                'capabilities':['preview','prepare','acquire','analyze','apply_p1_to_new_experiment'],
                'limitations':['Real TopCmds calls require a TopSpin CmdThread',
                    'No real hardware validation in TopSpin 3.6.4', 'No global gradient/RF calibration writes',
                    'Stop is honored between points, never aborts an active acquisition']}

    def context(self):
        try:
            current = list(self.api.CURDATA()) if self.api is not None else None
        except API_ERRORS as exc:
            raise WorkflowError('Could not read current dataset: '+text_type(exc))
        return {'available':self.api is not None or self.demo, 'demo':self.demo, 'current':current,
                'dataset_name':text_type(current[0]) if current else ('DEMO_DOSY' if self.demo else ''),
                'data_root':text_type(current[3]) if current else '',
                'current_expno':text_type(current[1]) if current else '',
                'current_procno':text_type(current[2]) if current else '1',
                'p1_template_expno':1000, 'gradient_template_expno':10}

    def _emit(self, stage, message='', current=0, total=0, expno=None, data=None):
        event = {'stage':stage, 'message':message or stage, 'current':current,
                 'total':total, 'demo':self.demo}
        if expno is not None:
            event['expno'] = expno
        if data is not None:
            event['data'] = data
        self.events.append(event)
        if self._callback is not None:
            try:
                self._callback(event)
            except API_ERRORS as exc:
                self.callback_errors.append(text_type(exc))

    def _config(self, config):
        c = dict(config)
        mode = c.get('mode','p1')
        if mode not in ('p1','gradient'):
            raise WorkflowError('mode must be p1 or gradient')
        c['mode'] = mode
        defaults = {'template_procno':1, 'p1_template_expno':1000, 'gradient_template_expno':10,
            'p1_start_expno':1100, 'gradient_start_expno':1200,
            'p1_values_us':[2.2*(i+1) for i in range(22)],
            'gradient_values_percent':list(range(8,97,4)), 'gradient_program':'stebpgp1s1d',
            'p90_min_us':5.5, 'p90_max_us':33., 'max_temperature_span_K':.5,
            'max_reference_temperature_difference_K':.5, 'gradient_b100_override_s_m2':0.,
            'report_dir':legacy.report_base()}
        if self.demo:
            defaults.update({'ppm_low':4.5, 'ppm_high':4.9, 'dref_1e9':1.15,
                'reference_temperature_K':298.15, 'reference_label':'SYNTHETIC DEMO: known D=1.15e-9 m2/s'})
        for key,value in defaults.items():
            if key not in c or c[key] is None or c[key]=='':
                c[key]=value
        return c

    def _ensure_demo(self, config):
        if self.demo and self.api is None:
            base = os.path.join(os.path.abspath(os.path.expanduser(config['report_dir'])),'demo_inputs')
            if not os.path.isdir(base):
                os.makedirs(base)
            root = os.path.join(base,'session_'+uuid.uuid4().hex[:12])
            os.mkdir(root)
            self.api = _DemoApi(root,config)

    def ensure_demo_inputs(self, config):
        """Explicit setup action to seed fixtures; preview itself remains read-only."""
        if not self.demo:
            raise WorkflowError('Synthetic fixture creation is available only in explicit demo mode')
        self._ensure_demo(self._config(config))
        return self.context()

    def _plan(self, config, analysis=False):
        c = self._config(config)
        context = self.context() if (self.api is not None or not c.get('dataset_name') or not c.get('data_root')) else {}
        if self.demo and self.api is not None:
            name, root = context['dataset_name'], context['data_root']
        else:
            name = text_type(c.get('dataset_name') or context.get('dataset_name',''))
            root = text_type(c.get('data_root') or context.get('data_root',''))
        if self.demo and not root:
            root = os.path.join(os.path.abspath(c['report_dir']),'demo_inputs','PREVIEW_ONLY')
            name = 'DEMO_DOSY'
        if not name or not root:
            raise WorkflowError('Select a dataset or provide dataset_name and data_root')
        prefix = c['mode']
        template = [name,text_type(engine.integer(c[prefix+'_template_expno'],'template EXPNO')),
                    text_type(engine.integer(c['template_procno'],'PROCNO')),os.path.abspath(root)]
        values = _values(c['p1_values_us'] if prefix=='p1' else c['gradient_values_percent'])
        expected = 'zg' if prefix=='p1' else c['gradient_program']
        plan = v3.build_plan(template,prefix,c[prefix+'_start_expno'],values,expected)
        if analysis and c.get('analysis_expnos'):
            numbers = _expnos(c['analysis_expnos'])
            if len(numbers)!=len(values):
                raise WorkflowError('analysis_expnos count must match configured sweep values')
            for row,number in zip(plan['rows'],numbers):
                row['expno']=number
        return c,plan

    def preview(self, config):
        c,plan = self._plan(config,analysis=bool(config.get('analysis_expnos')))
        paths = v3.paths_for(plan)
        recognized = self._prepared is not None and _signature(self._prepared['plan'])==_signature(plan)
        collisions = [p for p in paths if os.path.lexists(p)]
        warnings = ['SYNTHETIC DEMO: outputs are not experimental measurements'] if self.demo else []
        template = os.path.join(plan['dataset_dir'],plan['template'][1])
        template_exists = os.path.isdir(template)
        if not template_exists and not self.demo:
            warnings.append('Template directory not found')
        if collisions and not recognized:
            warnings.append('Destinations already exist: preparation/acquisition will be blocked')
        return {'plan':plan, 'rows':plan['rows'], 'collisions':collisions, 'warnings':warnings,
                'recognized_prepared':recognized, 'template_exists':template_exists,
                'ready':bool((self.api is not None or self.demo) and (template_exists or self.demo) and (not collisions or recognized)),
                'demo':self.demo}

    def _validate_analysis(self,c):
        low,high = engine.number(c.get('ppm_low'),'ppm_low'),engine.number(c.get('ppm_high'),'ppm_high')
        if low>=high:
            raise WorkflowError('ppm_low must be less than ppm_high')
        if c['mode']=='p1':
            lo,hi = legacy.positive(c['p90_min_us'],'P90 min'),legacy.positive(c['p90_max_us'],'P90 max')
            if lo>=hi or len(_values(c['p1_values_us']))<9:
                raise WorkflowError('P1 fit requires >=9 values and a valid bounded P90 interval')
        else:
            legacy.positive(c.get('dref_1e9'),'Dref')
            legacy.positive(c.get('reference_temperature_K'),'reference temperature')
            if not text_type(c.get('reference_label','')).strip():
                raise WorkflowError('Reference identity/source is required')
            for key in ('max_temperature_span_K','max_reference_temperature_difference_K','gradient_b100_override_s_m2'):
                if engine.number(c[key],key)<0:
                    raise WorkflowError(key+' must be nonnegative')

    def _prepared_acquisition(self, observed, plan, output, stop_event):
        prepared=self._prepared
        journal=prepared['journal']
        fixed,identities=journal['template_parameters'],journal['template_identities']
        for folder in v3.paths_for(plan):
            engine.ensure_parameter_only(folder)
            if v3._snapshot_files(folder)!=prepared['target_hashes'][folder]:
                raise WorkflowError('Prepared parameter files changed since preparation: '+folder)
        template_folder=os.path.join(plan['dataset_dir'],plan['template'][1])
        before=v3._snapshot_files(template_folder)
        journal=dict(journal)
        journal['events']=list(journal['events'])
        journal['acquisition_requested']=True
        path=os.path.join(output,'execution.json')
        try:
            for row,folder in zip(plan['rows'],v3.paths_for(plan)):
                observed.check_stop()
                engine.ensure_parameter_only(folder)
                destination=v3.dataset_for(plan,row)
                observed.RE(destination)
                v3.assert_dataset(observed,destination)
                v3.verify_parameters(observed,fixed,identities,row)
                journal['state']='acquiring'
                journal['events'].append({'stage':'ZG_started','expno':row['expno']})
                legacy.write_json(path,journal)
                v3.checked_command(observed,'ZG')
                v3.assert_dataset(observed,destination)
                fid=os.path.join(folder,'fid')
                if not os.path.isfile(fid) or not os.path.getsize(fid):
                    raise WorkflowError('ZG success without nonempty fid')
                v3.checked_command(observed,'EFP')
                v3.assert_dataset(observed,destination)
                spectrum=core.read_processed_1r(folder,row['procno'])
                journal['events'].append({'stage':'point_finished','expno':row['expno'],'sources':spectrum['sources']})
                legacy.write_json(path,journal)
            journal['state']='acquired_and_processed'
        except API_ERRORS as exc:
            journal['state']='stopped'
            journal['error']=text_type(exc)
            raise
        finally:
            try:
                observed.RE(plan['template'])
                v3.assert_dataset(observed,plan['template'])
            except API_ERRORS as exc:
                journal['state']='stopped'
                journal['restore_error']=text_type(exc)
                journal['error']=journal.get('error','')+'; Could not restore template view: '+text_type(exc)
            journal['template_preserved']=v3._snapshot_files(template_folder)==before
            if not journal['template_preserved']:
                journal['state']='stopped'
                journal['error']='Template hashes changed'
            legacy.write_json(path,journal)
        if journal['state']=='stopped':
            raise WorkflowError(journal.get('error','Stopped'))
        return journal

    def _analyze(self,c,plan,output,journal=None):
        self._emit('analyzing',total=len(plan['rows']))
        if c['mode']=='p1':
            result=v3.analyze_p1(plan,c['ppm_low'],c['ppm_high'],c['p90_min_us'],c['p90_max_us'])
            if journal:
                result['calibration_power_parameters']=dict((k,v) for k,v in journal['template_parameters'].items() if k.startswith('PL'))
            else:
                scope=result.get('scope',{})
                power={}
                for base in ('PL','PLW','PLdB'):
                    if isinstance(scope.get(base),list) and len(scope[base])>1:
                        power[base+' 1']=float(scope[base][1])
                    elif base+'1' in scope:
                        power[base+' 1']=float(scope[base+'1'])
                result['calibration_power_parameters']=power
            plot={'kind':'p1','x':result['pulse_us'],'observed':result['integrals'],
                'fitted':result['predicted_integrals'],'residuals':result['residuals'],
                'x_label':'P1 (us)','y_label':'Signed integral'}
            rows=[{'P1_us':x,'integral':y,'fitted':p,'residual':r} for x,y,p,r in
                zip(plot['x'],plot['observed'],plot['fitted'],plot['residuals'])]
            csv=legacy.csv_text(rows,['P1_us','integral','fitted','residual'])
        else:
            result=core.analyze_series(plan['dataset_dir'],[r['expno'] for r in plan['rows']],plan['template'][2],
                c['ppm_low'],c['ppm_high'],c['dref_1e9'],c['reference_temperature_K'],c['reference_label'],
                c['max_temperature_span_K'],c['max_reference_temperature_difference_K'])
            result['bruker_gradient_proposal']=legacy.known_sequence_gradient(result)
            prior=float(c['gradient_b100_override_s_m2'])
            if prior>0:
                dmeasured=result['fit']['slope_abs']/prior
                result['prior_b100_comparison']={'provided_b100_s_m2':prior,'D_measured_1e9':dmeasured/1e-9,
                    'gradient_ratio_sqrt_Dmeasured_over_Dref':math.sqrt(dmeasured/(float(c['dref_1e9'])*1e-9)),
                    'meaning':'Explicit previous b coefficient only; does not replace calibrated b100'}
            fit=result['fit']
            plot={'kind':'gradient','x':fit['x'],'observed':fit['log_relative_intensity'],
                'fitted':[fit['intercept_log_I_over_Imax']+fit['slope']*x for x in fit['x']],
                'residuals':fit['residuals_log'],'x_label':'(GPZ6 / 100)^2','y_label':'ln(I / Imax)'}
            csv=legacy.csv_text(result['rows'],['expno','gradient_percent','integral','predicted_integral','residual_log'])
            html=legacy.make_report(result)
            if self.demo:
                html=html.replace('<h1>Calibracion DOSY del patron</h1>',
                    '<h1>SYNTHETIC DEMO - NOT EXPERIMENTAL</h1><p>Ideal noiseless model for software demonstration.</p>')
            legacy.write_text(os.path.join(output,'informe.html'),html)
        result['demo']=self.demo
        result['evidence_type']='SYNTHETIC DEMONSTRATION - NOT EXPERIMENTAL' if self.demo else 'acquired spectrum analysis; review required'
        result['plot']=plot
        legacy.write_json(os.path.join(output,'result.json'),result)
        legacy.write_text(os.path.join(output,'curve.csv'),csv)
        self.last_results[c['mode']]={'result':result,'plan':plan,'output_dir':output}
        self._emit('result',current=len(plan['rows']),total=len(plan['rows']),data=result)
        return result

    def run(self, config, action='prepare', callback=None, stop_event=None):
        if action not in ('prepare','acquire','analyze'):
            raise WorkflowError('action must be prepare, acquire or analyze')
        self.events,self.callback_errors,self._callback=[],[],callback
        c=self._config(config)
        if action in ('acquire','analyze'):
            self._validate_analysis(c)
        self._ensure_demo(c)
        c,plan=self._plan(c,analysis=(action=='analyze'))
        if self.api is None and action!='analyze':
            raise WorkflowError('A native TopSpin API is required; choose explicit demo otherwise')
        output=legacy.new_report_dir(c['report_dir'],'gui_'+c['mode']+('_DEMO' if self.demo else ''))
        legacy.write_json(os.path.join(output,'config.json'),c)
        legacy.write_json(os.path.join(output,'plan.json'),plan)
        self._emit('started',message=action,total=len(plan['rows']))
        original=None
        result,journal,status=None,None,None
        error,restore_error=None,None
        original_view_restored=self.api is None
        observed=_ObservedApi(self.api,self,plan,stop_event) if self.api is not None else None
        try:
            original=list(self.api.CURDATA()) if self.api is not None else None
            if _stopped(stop_event):
                raise StopRequested('Stopped before starting')
            if action=='analyze':
                result=self._analyze(c,plan,output)
                status='analyzed'
            else:
                self.api.RE(plan['template'])
                v3.assert_dataset(self.api,plan['template'])
                if action=='acquire' and self._prepared and _signature(self._prepared['plan'])==_signature(plan):
                    journal=self._prepared_acquisition(observed,plan,output,stop_event)
                else:
                    journal=v3.run_plan(observed,plan,output,acquire=(action=='acquire'))
                if action=='prepare':
                    self._prepared={'plan':plan,'journal':journal,'output_dir':output,
                        'target_hashes':dict((p,v3._snapshot_files(p)) for p in v3.paths_for(plan))}
                    status='prepared'
                    self._emit('prepared',current=len(plan['rows']),total=len(plan['rows']))
                else:
                    self._prepared=None
                    if _stopped(stop_event):
                        raise StopRequested('Acquisition complete; analysis skipped at operator request')
                    result=self._analyze(c,plan,output,journal)
                    status='completed'
        except API_ERRORS as exc:
            stopped=isinstance(exc,StopRequested) or (observed and observed.stop_requested)
            status='stopped' if stopped else 'failed'
            error=text_type(exc)
            self._emit(status,message=error,total=len(plan['rows']))
        finally:
            if original is not None:
                try:
                    self.api.RE(original)
                    v3.assert_dataset(self.api,original)
                    original_view_restored=True
                except API_ERRORS as exc:
                    restore_error=text_type(exc)
                    error=(error+'; ' if error else '')+'Could not restore original view: '+restore_error
                    status='failed'
                    self._emit('failed',message=error,total=len(plan['rows']))
        if status in ('failed','stopped'):
            self._prepared=None
            # The immutable v3 dependency catches Python exceptions only. A Java
            # failure can escape its try block after a journal was saved; mark
            # that receipt as stopped without dropping any completed-point data.
            execution_path=os.path.join(output,'execution.json')
            if os.path.isfile(execution_path):
                execution=_read_json(execution_path)
                execution.update({'state':'stopped','error':error,
                    'original_view_restored':original_view_restored})
                if restore_error is not None:
                    execution['restore_error']=restore_error
                legacy.write_json(execution_path,execution)
        self._emit('finished',message=status or '',current=len(plan['rows']) if status in ('completed','analyzed','prepared') else 0,
                   total=len(plan['rows']),data={'status':status,'output_dir':output})
        response={'status':status,'plan':plan,'output_dir':output,'result':result,
                  'events':list(self.events),'demo':self.demo,'callback_errors':list(self.callback_errors),
                  'original_view_restored':original_view_restored}
        if error is not None:
            response['error']=error
        if restore_error is not None:
            response['restore_error']=restore_error
        legacy.write_json(os.path.join(output,'workflow.json'),response)
        if status=='failed':
            raise WorkflowError(error+'\n'+output)
        return response

    def apply_p1(self, config, p90_us, target_expno, reviewed=False, callback=None):
        if reviewed is not True:
            raise WorkflowError('Explicit review of the P1 result is required')
        previous=self.last_results.get('p1')
        if previous is None:
            raise WorkflowError('Analyze P1 in this session before applying its proposal')
        proposed=legacy.positive(p90_us,'P90')
        fitted=float(previous['result']['P90_us'])
        if abs(proposed-fitted)>1e-6*max(1.,abs(fitted)):
            raise WorkflowError('P90 differs from the reviewed fit result')
        c=self._config(config)
        self._ensure_demo(c)
        if self.api is None:
            raise WorkflowError('Native TopSpin API required')
        self.events,self.callback_errors,self._callback=[],[],callback
        original=None
        plan=previous['plan']
        if c.get('dataset_name') and c['dataset_name']!=plan['template'][0] and not self.demo:
            raise WorkflowError('Selected dataset differs from the reviewed P1 calibration dataset')
        source=list(plan['template'])
        source[1]=text_type(engine.integer(c.get('apply_source_expno',c['p1_template_expno']),'source EXPNO'))
        target=engine.integer(target_expno,'target EXPNO')
        folder=os.path.join(plan['dataset_dir'],text_type(target))
        if os.path.lexists(folder):
            raise WorkflowError('Application target already exists')
        source_folder=os.path.join(plan['dataset_dir'],source[1])
        source_hash=v3._snapshot_files(source_folder)
        powers=previous['result'].get('calibration_power_parameters',{})
        if not powers:
            raise WorkflowError('RF power provenance is unavailable; cannot apply this P90')
        output=legacy.new_report_dir(c['report_dir'],'gui_P1_application'+('_DEMO' if self.demo else ''))
        result={'status':'applying','P1_us':proposed,'source':source,'target_expno':target,
                'target_dir':folder,'output_dir':output,'demo':self.demo,'parameters_only':True,
                'acquisition_started':False,'global_calibration_modified':False,
                'source_hashes':source_hash,'rf_power_parameters':powers,
                'reviewed_result':previous['output_dir'],'original_view_restored':False}
        legacy.write_json(os.path.join(output,'p1_application.json'),result)
        error=None
        try:
            original=list(self.api.CURDATA())
            self.api.RE(source)
            v3.assert_dataset(self.api,source)
            if float(self.api.GETPAR('PARMODE'))!=0:
                raise WorkflowError('Application source must be 1D')
            v3.verify_parameters(self.api,powers,{})
            # Nucleus and probe must match the calibrated series when recorded.
            for key in ('NUC1','PROBHD'):
                expected=previous['result'].get('scope',{}).get(key)
                if expected is not None and text_type(self.api.GETPAR(key)).strip().strip('<>')!=expected:
                    raise WorkflowError('P90 application would change '+key)
            if os.path.lexists(folder):
                raise WorkflowError('Application target appeared after review')
            command=self.api.XCMD('wraparam '+text_type(target),wait=self.api.WAIT_TILL_DONE)
            if command is not None and hasattr(command,'getResult') and command.getResult()==-1:
                raise WorkflowError('Parameter copy failed')
            if not os.path.isdir(folder):
                raise WorkflowError('Parameter copy target missing')
            engine.ensure_parameter_only(folder)
            destination=list(source)
            destination[1]=text_type(target)
            self.api.RE(destination)
            v3.assert_dataset(self.api,destination)
            engine.set_and_verify(self.api,'P 1',proposed)
            v3.verify_parameters(self.api,powers,{})
            engine.ensure_parameter_only(folder)
        except API_ERRORS as exc:
            error=text_type(exc)
        finally:
            if original is not None:
                try:
                    self.api.RE(original)
                    v3.assert_dataset(self.api,original)
                    result['original_view_restored']=True
                except API_ERRORS as exc:
                    result['restore_error']=text_type(exc)
                    error=(error+'; ' if error else '')+'Could not restore original view: '+text_type(exc)
            result['source_preserved']=v3._snapshot_files(source_folder)==source_hash
            if not result['source_preserved']:
                error=(error+'; ' if error else '')+'Application source hashes changed'
        result['status']='failed' if error is not None else 'applied'
        if error is not None:
            result['error']=error
        legacy.write_json(os.path.join(output,'p1_application.json'),result)
        if error is not None:
            self._emit('failed',message=error,expno=target,data=result)
            raise WorkflowError(error+'\n'+output)
        self._emit('p1_applied',expno=target,data=result)
        return result
