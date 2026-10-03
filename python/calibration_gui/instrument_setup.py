# -*- coding: utf-8 -*-
"""Optional operator-triggered TopSpin setup actions (Python 2.7/Jython + 3).

This module neither acquires ZG data nor changes global gradient calibration.
Actions are disabled by default, individually dispatched, and limited to five
documented command forms. No shell, arbitrary command, thread or background
queue is created here. The GUI must call TopSpin functions from a CmdThread
created by EXEC_PYSCRIPT/EXEC_PYFILE, not a Swing listener or generic worker.
Callbacks run on the calling CmdThread; marshal Swing changes onto its EDT.

Documentation inspected, not live instrument validation:
  C:/Bruker/TopSpin3.8.0/prog/docu/English/topspin/pdf/python.pdf
    pp.7-8 EXEC_PYSCRIPT(text,arg), EXEC_PYFILE(path,arg), XCMD and getResult;
    pp.11-12 GETPAR/GETPARSTAT; pp.20-21 CmdThread requirement for GUI callbacks.
  acquisition-reference.pdf (H9775SA3_005), p.37 TE is demand temperature;
    pp.114-116 lock -acqu; pp.199-201 teget/teset (teget writes acqus).
  Atma.pdf (ATM Accessory manual Z4D10872b), pp.19-20: ATMA requires ATM
    hardware and uses the routed nuclei of the current dataset.
  topshim.pdf (H184616 Version009), pp.5-9: probe gradient, compatible
    hardware/firmware and prior setup; default TopShim uses current lock solvent.

Primary Bruker manuals mirrored publicly:
  https://2210pc.chem.uic.edu/nmr/downloads/bruker/en-US/pdf/z31510.pdf
  https://chemistry.beloit.edu/classes/instruments/Manuals/Bruker_acquisition-reference%202017.pdf
Those documents support command syntax, not a claim of running these commands
on TopSpin3.6.4 here. Installed3.8 documentation can differ from a3.6.4 system;
supported_commands and hardware flags must be supplied for the actual system.

Temperature semantics: GETPAR('TE') reads the acquisition demand parameter;
GETPARSTAT('TE') alone reads a stored value. Only a successful, explicit teget
refresh provides a fresh controller readback, and it modifies the current acqus.
It therefore requires a confirmed working copy. A controller readback is not a
calibrated sample temperature, nor evidence of equilibration. teset is a demand
change; it does not establish temperature stability. No nominal probe limits are
invented: set_temperature requires configured temperature_limits_K.
"""
from __future__ import unicode_literals

import math
import os
import time
import hashlib

try:
    string_types = (basestring,)
    integer_types = (int, long)
    text_type = unicode
except NameError:
    string_types = (str,)
    integer_types = (int,)
    text_type = str
try:
    from java.lang import Integer as JavaInteger, Long as JavaLong
    integer_types = integer_types + (JavaInteger, JavaLong)
except ImportError:
    pass
try:
    # Jython does not match java.lang.RuntimeException with Python Exception.
    from java.lang import Throwable as JavaThrowable
except ImportError:
    JavaThrowable = Exception

VERSION = '1.0.0'
COMMANDS = ('lock', 'atma', 'topshim', 'teget', 'teset')
_ACTIONS = (
    ('lock', 'lock', 'Lock con el disolvente actual', 'Lock with current solvent'),
    ('atma', 'atma', 'Tune/match automatico (ATM)', 'Automatic tune/match (ATM)'),
    ('topshim', 'topshim', 'TopShim 1D configurado', 'Configured 1D TopShim'),
    ('read_temperature', 'teget', 'Consultar controlador en copia', 'Refresh controller in working copy'),
    ('set_temperature', 'teset', 'Cambiar consigna de temperatura', 'Change temperature demand'),
)


class SetupError(ValueError):
    def __init__(self, message, report=None):
        ValueError.__init__(self, message)
        self.report = report


def default_setup_config():
    """Return fresh disabled settings; never infer hardware from a probe name."""
    return {
        'enabled': False,
        'supported_commands': [],
        'working_dataset': None,
        'working_dataset_confirmed': False,
        'expected_solvent': '',
        'lock_supported': False,
        'probe_atm_supported': False,
        'topshim_configured': False,
        'lock_confirmed': False,
        'temperature_controller_supported': False,
        'temperature_limits_K': None,
    }


def _config(given):
    result = default_setup_config()
    if given is not None:
        if not isinstance(given, dict):
            raise SetupError('Setup configuration must be a dictionary.')
        unknown = set(given) - set(result)
        if unknown:
            raise SetupError('Unknown setup fields: ' + ', '.join(sorted(unknown)))
        result.update(given)
    for key in ('enabled', 'working_dataset_confirmed', 'lock_supported',
                'probe_atm_supported', 'topshim_configured', 'lock_confirmed',
                'temperature_controller_supported'):
        if not isinstance(result[key], bool):
            raise SetupError(key + ' must be true or false.')
    commands = result['supported_commands']
    if not isinstance(commands, (list, tuple)) or any(c not in COMMANDS for c in commands):
        raise SetupError('supported_commands allows only lock, atma, topshim, teget, teset.')
    result['supported_commands'] = list(commands)
    if not isinstance(result['expected_solvent'], string_types):
        raise SetupError('expected_solvent must be text.')
    if any(c in result['expected_solvent'] for c in ('\r', '\n', '\x00')):
        raise SetupError('expected_solvent must be a single value.')
    if result['working_dataset'] is not None:
        _dataset_key(result['working_dataset'])
    limits = result['temperature_limits_K']
    if limits is not None:
        if not isinstance(limits, (list, tuple)) or len(limits) != 2:
            raise SetupError('temperature_limits_K must be [minimum, maximum].')
        low, high = [_number(v, 'temperature limit') for v in limits]
        if low <= 0 or low >= high:
            raise SetupError('Require 0 < minimum temperature < maximum temperature.')
        result['temperature_limits_K'] = [low, high]
    return result


def _number(value, label):
    if isinstance(value, bool):
        raise SetupError(label + ' must be a finite number.')
    try:
        number = float(value)
    except (ValueError, TypeError, OverflowError):
        raise SetupError(label + ' must be a finite number.')
    if math.isnan(number) or math.isinf(number):
        raise SetupError(label + ' must be finite.')
    return number


def _utc_now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def _dataset_key(data):
    if not isinstance(data, (list, tuple)) or len(data) != 4:
        raise SetupError('working_dataset must contain name, EXPNO, PROCNO and directory.')
    if any(v is None or not text_type(v).strip() for v in data):
        raise SetupError('Dataset fields must not be empty.')
    return (text_type(data[0]), text_type(data[1]), text_type(data[2]),
            os.path.normcase(os.path.normpath(text_type(data[3]))))


def _positive_integer(value, label):
    if isinstance(value, bool):
        raise SetupError(label + ' must be a positive integer.')
    text = text_type(value)
    if not text.isdigit() or int(text) <= 0:
        raise SetupError(label + ' must be a positive integer.')
    return int(text)


def _dataset_folder(data):
    _dataset_key(data)
    name = text_type(data[0])
    if name in ('.', '..') or any(x in name for x in ('/', '\\', ':', '\x00')):
        raise SetupError('Dataset name must be a single direct-layout folder name.')
    expno = _positive_integer(data[1], 'EXPNO')
    _positive_integer(data[2], 'PROCNO')
    directory = text_type(data[3])
    if not os.path.isabs(directory):
        raise SetupError('Dataset directory must be absolute.')
    root = os.path.realpath(directory)
    return os.path.join(root, name, text_type(expno))


def _source_snapshot(folder):
    if not os.path.isdir(folder):
        raise SetupError('Source experiment directory does not exist: ' + folder)
    if os.path.islink(folder):
        raise SetupError('Linked source experiment folders are not supported.')
    result = {}
    for current, dirs, files in os.walk(folder):
        for name in dirs + files:
            if os.path.islink(os.path.join(current, name)):
                raise SetupError('Linked entries are not supported in a parameter-copy source.')
        for name in sorted(files):
            path = os.path.join(current, name)
            digest = hashlib.sha256()
            with open(path, 'rb') as handle:
                while True:
                    block = handle.read(1024 * 1024)
                    if not block:
                        break
                    digest.update(block)
            result[os.path.relpath(path, folder)] = {'sha256': digest.hexdigest(),
                                                  'bytes': os.path.getsize(path)}
    return result


def _parameter_only(folder):
    if not os.path.isdir(folder):
        raise SetupError('Parameter-copy target does not exist.')
    if os.path.islink(folder):
        raise SetupError('Linked working experiment folders are not supported.')
    for current, dirs, files in os.walk(folder):
        for name in dirs + files:
            if os.path.islink(os.path.join(current, name)):
                raise SetupError('Linked entries are not allowed in a working copy.')
        for name in files:
            low = name.lower()
            signal = (low in ('fid', 'ser') or
                      (len(low) >= 2 and low[0] in '12345678' and
                       set(low[1:]).issubset(set('ri'))))
            if signal:
                raise SetupError('Unexpected signal file in parameter-only copy: ' +
                                 os.path.join(current, name))


def _strict_command(api, command):
    handle = api.XCMD(command)
    rc = handle.getResult() if hasattr(handle, 'getResult') else handle
    if isinstance(rc, bool) or not isinstance(rc, integer_types) or rc != 0:
        raise SetupError('TopSpin did not confirm integer return code zero for ' + command)
    return rc


def _select_dataset(api, data):
    api.RE(list(data))
    if _dataset_key(api.CURDATA()) != _dataset_key(data):
        raise SetupError('RE did not select the requested dataset.')


def _read_current_dataset(api, action):
    """Normalize a native API failure before a restorable context is known."""
    try:
        return api.CURDATA()
    except (Exception, JavaThrowable) as exc:
        message = 'Could not read the original dataset: ' + text_type(exc)
        report = {'action': action, 'status': 'not_confirmed',
                  'stage': 'read_current_dataset', 'error': message,
                  'command_completed': False, 'physical_validation': False,
                  'original_dataset_restored': None,
                  'utc_finished': _utc_now()}
        raise SetupError(message, report)


def prepare_working_dataset(api, source, target_expno):
    """Create a NEW parameter-only copy with wraparam; preserve the source.

    Must run in a CmdThread. Existing targets, source aliasing, unexpected signal
    files and nonzero/unknown command returns stop the operation. A failed or
    partial target is reported and left intact for inspection; nothing is deleted.
    The originally open dataset is restored even after a failed copy. Returned
    fields can populate default_setup_config, but do not enable hardware actions.
    """
    original = list(_read_current_dataset(api, 'prepare_working_dataset'))
    _dataset_key(original)
    _dataset_key(source)
    source = list(source)
    source_folder = _dataset_folder(source)
    target = _positive_integer(target_expno, 'Target EXPNO')
    source[1] = text_type(_positive_integer(source[1], 'Source EXPNO'))
    source[2] = text_type(_positive_integer(source[2], 'Source PROCNO'))
    destination = list(source)
    destination[1] = text_type(target)
    target_folder = _dataset_folder(destination)
    if os.path.normcase(source_folder) == os.path.normcase(target_folder):
        raise SetupError('Target EXPNO must differ from the original experiment.')
    if os.path.lexists(target_folder):
        raise SetupError('Working-copy target already exists; no command was executed.')
    if not any(os.path.isfile(os.path.join(source_folder, p)) for p in ('acqu','acqus')):
        raise SetupError('Source acquisition parameters are missing.')
    source_proc = os.path.join(source_folder, 'pdata', source[2])
    if not any(os.path.isfile(os.path.join(source_proc, p)) for p in ('proc','procs')):
        raise SetupError('Source processing parameters are missing for this PROCNO.')
    before = _source_snapshot(source_folder)
    report = {'action': 'prepare_working_dataset', 'source': source,
              'working_dataset': destination, 'target_directory': target_folder,
              'working_dataset_confirmed': False, 'parameters_only': False,
              'acquisition_started': False, 'global_calibration_modified': False,
              'source_hashes': before, 'status': 'preparing'}
    problem = None
    try:
        _select_dataset(api, source)
        if os.path.lexists(target_folder):
            raise SetupError('Working-copy target appeared during preparation.')
        _strict_command(api, 'wraparam ' + text_type(target))
        _parameter_only(target_folder)
        target_proc = os.path.join(target_folder, 'pdata', destination[2])
        if not any(os.path.isfile(os.path.join(target_folder, p)) for p in ('acqu','acqus')):
            raise SetupError('Copied acquisition parameters are missing.')
        if not any(os.path.isfile(os.path.join(target_proc, p)) for p in ('proc','procs')):
            raise SetupError('Copied processing parameters are missing.')
        _select_dataset(api, destination)
        report['expected_solvent'] = text_type(api.GETPAR('SOLVENT')).strip().strip('<>')
        report['pulse_program'] = text_type(api.GETPAR('PULPROG')).strip().strip('<>')
        _parameter_only(target_folder)
        report['parameters_only'] = True
    except (Exception, JavaThrowable) as exc:
        problem = text_type(exc)
    finally:
        try:
            _select_dataset(api, original)
            report['original_dataset_restored'] = True
        except (Exception, JavaThrowable) as exc:
            problem = (problem + '; ' if problem else '') + 'Dataset restore failed: ' + text_type(exc)
            report['original_dataset_restored'] = False
        try:
            unchanged = _source_snapshot(source_folder) == before
            report['source_unchanged'] = unchanged
            if not unchanged:
                problem = (problem + '; ' if problem else '') + 'Original source file hashes changed.'
        except Exception as exc:
            problem = (problem + '; ' if problem else '') + 'Source verification failed: ' + text_type(exc)
            report['source_unchanged'] = False
    if problem is not None:
        report['status'] = 'not_confirmed'
        report['target_exists'] = os.path.lexists(target_folder)
        report['error'] = problem
        raise SetupError('Working copy not confirmed: ' + problem, report)
    report['working_dataset_confirmed'] = True
    report['status'] = 'parameters_prepared'
    return report


def _require_dataset(api, config, required=True):
    current = _read_current_dataset(api, 'read_current_dataset')
    key = _dataset_key(current)
    expected = config['working_dataset']
    if required and expected is None:
        raise SetupError('Select and pin a working dataset before running setup.')
    if expected is not None and key != _dataset_key(expected):
        raise SetupError('The current dataset differs from the pinned working dataset.')
    return list(current)


def _reasons(action, command, c):
    out = []
    if not c['enabled']:
        out.append('Setup actions are disabled by configuration.')
    if command not in c['supported_commands']:
        out.append('This command has not been enabled for the actual TopSpin system.')
    if c['working_dataset'] is None:
        out.append('A pinned working dataset is required.')
    if not c['working_dataset_confirmed']:
        out.append('Prepare and confirm a new parameter-only working copy first.')
    if action == 'lock':
        if not c['lock_supported']:
            out.append('Lock hardware and solvent table have not been confirmed.')
        if not c['expected_solvent'].strip():
            out.append('The sample solvent must be specified and checked.')
    if action == 'atma' and not c['probe_atm_supported']:
        out.append('ATMA requires confirmed ATM-compatible probe hardware.')
    if action == 'topshim':
        if not c['topshim_configured']:
            out.append('TopShim hardware, probe and shim setup have not been confirmed.')
        if not c['lock_confirmed']:
            out.append('Confirm stable lock on the correct solvent before this default TopShim action.')
        if not c['expected_solvent'].strip():
            out.append('The current sample solvent must be specified.')
    if action in ('read_temperature', 'set_temperature'):
        if not c['temperature_controller_supported']:
            out.append('The temperature controller and command support are not confirmed.')
        if not c['working_dataset_confirmed']:
            out.append('Use a confirmed working copy; temperature commands can update metadata.')
    if action == 'set_temperature' and c['temperature_limits_K'] is None:
        out.append('Configure the permitted range for this probe, sample and setup.')
    return out


def describe_setup(config=None):
    """Return five individually gated buttons; this function calls no TopSpin API."""
    c = _config(config)
    rows = []
    for ident, command, es, en in _ACTIONS:
        why = _reasons(ident, command, c)
        rows.append({'id': ident, 'command_id': command,
                     'label_es': es, 'label_en': en,
                     'available': not why, 'reasons': why,
                     'requires_operator_action': True,
                     'requires_cmdthread': True,
                     'modifies_instrument': ident != 'read_temperature',
                     'may_write_current_dataset': ident in ('read_temperature', 'set_temperature'),
                     'completion_is_physical_validation': False})
    return rows


def _emit(callback, event, report):
    if callback is None:
        return
    try:
        callback(dict(event=event, report=dict(report)))
    except (Exception, JavaThrowable) as exc:
        # A GUI notification failure cannot relabel or repeat an instrument action.
        report.setdefault('callback_errors', []).append(text_type(exc))


def _read_value(api, method, name):
    try:
        raw = getattr(api, method)(name)
        value = _number(raw, name)
        if value <= 0:
            raise SetupError(name + ' is not a positive Kelvin value.')
        return {'value_K': value, 'raw': text_type(raw), 'error': None}
    except (Exception, JavaThrowable) as exc:
        return {'value_K': None, 'raw': None, 'error': text_type(exc)}


def read_temperature(api, config=None, refresh=False, on_event=None):
    """Read metadata only unless refresh=True explicitly requests gated teget.

    Even a fresh controller value is not a calibrated sample temperature. A
    previously acquired TE record is never labelled as live temperature.
    """
    if not isinstance(refresh, bool):
        raise SetupError('refresh must be true or false; no implicit instrument query.')
    c = _config(config)
    if refresh:
        result = run_setup_action(api, 'read_temperature', c, on_event=on_event)
        return result['temperature']
    current = _require_dataset(api, c, required=False)
    demand = _read_value(api, 'GETPAR', 'TE')
    status = _read_value(api, 'GETPARSTAT', 'TE')
    return {'dataset': current, 'demand_parameter_K': demand['value_K'],
            'stored_status_K': status['value_K'], 'controller_readback_K': None,
            'fresh_controller_readback': False,
            'sample_temperature_verified': False, 'equilibrated': None,
            'read_errors': [d['error'] for d in (demand, status) if d['error']],
            'meaning': 'GETPAR TE is demand metadata; GETPARSTAT TE is stored status, not a live sensor query.'}


def _run_setup_on_selected(api, action_id, config, on_event=None, temperature_K=None):
    """Execute ONE configured action from a TopSpin CmdThread.

    The GUI's separate button press is the operator's explicit selection; this
    method does not ask extra confirmations or infer permission for other steps.
    Nonzero, None, string, float and boolean results do not confirm completion.
    SetupError.report contains a receipt when dispatch was attempted.
    """
    c = _config(config)
    choices = dict((row['id'], row) for row in describe_setup(c))
    if action_id not in choices:
        raise SetupError('Unknown setup action; arbitrary commands are not supported.')
    choice = choices[action_id]
    if not choice['available']:
        raise SetupError('; '.join(choice['reasons']))
    if on_event is not None and not callable(on_event):
        raise SetupError('on_event must be callable.')
    current = _require_dataset(api, c)
    if action_id in ('lock', 'topshim'):
        actual = text_type(api.GETPAR('SOLVENT')).strip().strip('<>')
        expected = c['expected_solvent'].strip().strip('<>')
        if actual != expected:
            raise SetupError('Dataset SOLVENT does not match the explicitly configured sample solvent.')
    command = {'lock': 'lock -acqu', 'atma': 'atma', 'topshim': 'topshim',
               'read_temperature': 'teget', 'set_temperature': 'teset'}[action_id]
    target = None
    if action_id == 'set_temperature':
        target = _number(temperature_K, 'temperature_K')
        low, high = c['temperature_limits_K']
        if not low <= target <= high:
            raise SetupError('Requested temperature is outside the configured range.')
        command += ' ' + format(target, '.12g')
    elif temperature_K is not None:
        raise SetupError('temperature_K applies only to set_temperature.')
    report = {'action': action_id, 'command': command, 'dataset': current,
              'utc_started': _utc_now(),
              'status': 'dispatching', 'return_code': None,
              'physical_validation': False, 'equilibrated': None,
              'target_K': target, 'command_completed': False}
    _emit(on_event, 'started', report)
    try:
        # Default wait is WAIT_TILL_DONE, documented in python.pdf p.8. Do not
        # pass NO_WAIT here: its result is undefined and cannot establish rc=0.
        handle = api.XCMD(command)
        rc = handle.getResult() if hasattr(handle, 'getResult') else handle
        report['return_code'] = rc if isinstance(rc, (bool, int, float)) or rc is None else text_type(rc)
        if isinstance(rc, bool) or not isinstance(rc, integer_types) or rc != 0:
            raise SetupError('TopSpin did not confirm integer return code zero.')
        report['command_completed'] = True
        report['status'] = 'command_returned_zero'
        _require_dataset(api, c)
        if action_id == 'read_temperature':
            temperature = read_temperature(api, c, refresh=False)
            if temperature['stored_status_K'] is None:
                raise SetupError('teget returned zero, but TE status could not be read.')
            temperature['controller_readback_K'] = temperature['stored_status_K']
            temperature['fresh_controller_readback'] = True
            temperature['queried_utc'] = _utc_now()
            temperature['meaning'] = 'Controller readback after teget; not independently calibrated sample temperature or evidence of equilibrium.'
            report['temperature'] = temperature
        report['operator_check'] = {
            'lock': 'Inspect lock stability; return code alone does not establish a stable lock.',
            'atma': 'Inspect tuning/matching; this is not a 90-degree RF pulse calibration.',
            'topshim': 'Inspect the TopShim report and line shape; command completion does not certify spectral quality.',
            'read_temperature': 'Inspect controller and sample-temperature calibration; no equilibrium is asserted.',
            'set_temperature': 'Demand was submitted; independently observe controller readback and equilibration.'}[action_id]
        report['utc_finished'] = _utc_now()
        return report
    except (Exception, JavaThrowable) as exc:
        report['status'] = 'not_confirmed'
        report['error'] = text_type(exc)
        report['utc_finished'] = _utc_now()
        raise SetupError('Setup action not confirmed: ' + text_type(exc), report)


def run_setup_action(api, action_id, config, on_event=None, temperature_K=None):
    """Select the confirmed work copy, perform one action, then restore context.

    Run from a CmdThread. No input dataset is used implicitly for an instrument
    action. A completed callback is emitted only after restoring the caller's
    original dataset; rc0 still does not certify physical calibration.
    """
    c = _config(config)
    options = dict((row['id'], row) for row in describe_setup(c))
    if action_id not in options:
        raise SetupError('Unknown setup action; arbitrary commands are not supported.')
    if not options[action_id]['available']:
        raise SetupError('; '.join(options[action_id]['reasons']))
    if on_event is not None and not callable(on_event):
        raise SetupError('on_event must be callable.')
    # A stale GUI flag cannot turn an acquired experiment into a work template.
    # Recheck on every explicit action, before selecting or updating anything.
    _parameter_only(_dataset_folder(c['working_dataset']))
    original = list(_read_current_dataset(api, action_id))
    _dataset_key(original)
    report = None
    problem = None
    try:
        if _dataset_key(original) != _dataset_key(c['working_dataset']):
            _select_dataset(api, c['working_dataset'])
        report = _run_setup_on_selected(api, action_id, c, on_event, temperature_K)
    except (Exception, JavaThrowable) as exc:
        report = getattr(exc, 'report', None)
        if report is None:
            report = {'action': action_id, 'status': 'not_confirmed',
                      'dataset': list(c['working_dataset']),
                      'error': text_type(exc), 'command_completed': False,
                      'physical_validation': False, 'utc_finished': _utc_now()}
        problem = SetupError(text_type(exc), report)
    finally:
        try:
            try:
                needs_restore = _dataset_key(api.CURDATA()) != _dataset_key(original)
            except (Exception, JavaThrowable):
                # The original is known: attempt RE even if querying CURDATA fails.
                needs_restore = True
            if needs_restore:
                _select_dataset(api, original)
            if report is not None:
                report['original_dataset_restored'] = True
        except (Exception, JavaThrowable) as exc:
            message = (text_type(problem) + '; ' if problem else '') + 'Dataset restore failed: ' + text_type(exc)
            report = report or {'action': action_id, 'physical_validation': False}
            report.update(status='not_confirmed', original_dataset_restored=False, error=message)
            problem = SetupError(message, report)
    if problem is not None:
        _emit(on_event, 'failed', report)
        raise problem
    _emit(on_event, 'completed', report)
    return report
