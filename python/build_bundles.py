#!/usr/bin/env python3
"""Rebuild self-contained Jython 2.7 scripts using public, local sources only.

This is a CPython 3.8+ development tool. It neither imports TopCmds nor starts
TopSpin. No vendor implementation or sample calibration is embedded.
"""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def write_lf(path, content):
    """Stable Git/distribution bytes on Windows and Unix, also Python 3.8."""
    with path.open('w', encoding='utf-8', newline='\n') as handle:
        handle.write(content)


def ramp_source():
    original = (HERE/'ramp_generator'/'generate_ramps.py').read_text(encoding='utf-8')
    plan = original[original.index('DEFAULT_CONFIG ='):original.index('\ndef render_macro_reference')]
    plan = plan.replace('math.isfinite(parsed)', '(not math.isnan(parsed) and not math.isinf(parsed))')
    plan = plan.replace('re.fullmatch(prefix + r"\\d{1,3}",', 're.match(prefix + r"\\d{1,3}$",')
    plan = plan.replace('isinstance(value, str)', 'isinstance(value, string_types)')
    plan = plan.replace('isinstance(config[key], str)', 'isinstance(config[key], string_types)')
    original = (HERE/'ramp_generator'/'topspin_prepare_template.py').read_text(encoding='utf-8')
    prepare = original[original.index('\ndef parameter_key'):original.index('\ndef main():')]
    content = (plan + prepare).replace('str(', 'text_type(')
    return ('# -*- coding: utf-8 -*-\nfrom __future__ import print_function, unicode_literals\n'
            'import json, math, os, re\nfrom decimal import Decimal, InvalidOperation\n'
            'try:\n    string_types = (basestring,)\n    text_type = unicode\nexcept NameError:\n'
            '    string_types = (str,)\n    text_type = str\n\n' + content)


def main():
    engine = ramp_source()
    console = HERE/'topspin_console'
    write_lf(console/'dosy_ramp_engine.py', engine)
    profile = json.loads((HERE/'sequence_model.json').read_text(encoding='utf-8'))
    model_sha = profile['model_source_sha256']
    if len(model_sha) != 64 or any(c not in '0123456789abcdef' for c in model_sha):
        raise ValueError('A documented model-source SHA-256 is required')
    modules = [('_dosy_ramp_engine', engine),
               ('_dosy_calibration', (console/'dosy_calibration.py').read_text(encoding='utf-8')),
               ('_dosy_console_ui', (console/'dosy_console_ui.py').read_text(encoding='utf-8'))]
    parts = ['# -*- coding: utf-8 -*-',
             '"""Public DOSY console, Jython 2.7. See docs/en/bruker-step-by-step.md for scope."""',
             'from __future__ import print_function, unicode_literals', 'import sys, types, json',
             'def _load_module(name, source):', '    module = types.ModuleType(name)',
             '    sys.modules[name] = module',
             '    exec(compile(source.encode("utf-8"), name + ".py", "exec"), module.__dict__)',
             '    return module']
    for name, source in modules:
        parts.append('_load_module(%r, %s)' % (name, ascii(source)))
    parts += ['_ui = sys.modules["_dosy_console_ui"]',
              '_ui.TBO_PROFILE = json.loads(%s)' % ascii(json.dumps(profile, ensure_ascii=True)),
              '_ui.TBO_MODEL_SOURCE_SHA256 = %r' % model_sha,
              'if __name__ == "__main__":', '    import TopCmds', '    _ui.main(TopCmds)', '']
    dist = console/'dist'
    dist.mkdir(exist_ok=True)
    base = dist/'dosy_workshop.py'
    write_lf(base, '\n'.join(parts))
    autorun = HERE/'topspin_console_v3'/'dosy_autorun.py'
    parts = ['# -*- coding: utf-8 -*-',
             '"""Public DOSY v3: acquisition only after explicit user confirmation."""',
             'from __future__ import unicode_literals', 'import sys, types',
             '_base = {"__name__": "_dosy_v2_embedded"}',
             'exec(compile(%s.encode("utf-8"), "dosy_v2.py", "exec"), _base)' % ascii(base.read_text(encoding='utf-8')),
             '_auto = types.ModuleType("_dosy_autorun")', 'sys.modules["_dosy_autorun"] = _auto',
             'exec(compile(%s.encode("utf-8"), "dosy_autorun.py", "exec"), _auto.__dict__)' % ascii(autorun.read_text(encoding='utf-8')),
             'if __name__ == "__main__":', '    import TopCmds', '    _auto.main(TopCmds)', '']
    v3 = HERE/'topspin_console_v3'/'dist'
    v3.mkdir(exist_ok=True)
    target = v3/'dosy_workshop_v3.py'
    write_lf(target, '\n'.join(parts))
    sources = [HERE/'ramp_generator'/'generate_ramps.py', HERE/'ramp_generator'/'topspin_prepare_template.py',
               HERE/'sequence_model.json', console/'dosy_calibration.py', console/'dosy_console_ui.py', autorun]
    outputs = [console/'dosy_ramp_engine.py', base, target]
    manifest = {'schema_version': 1, 'builder': 'python/build_bundles.py',
                'scope': 'Public sources only; no raw sample data, no experimental calibration, no instrument execution',
                'sources': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                'outputs': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs}}
    write_lf(HERE/'build_sources_sha256.json', json.dumps(manifest, indent=2) + '\n')
    for path in (base, target):
        print(path.relative_to(ROOT).as_posix())


if __name__ == '__main__':
    main()
