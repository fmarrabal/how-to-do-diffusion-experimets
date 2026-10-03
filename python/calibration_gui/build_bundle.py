"""Package the GUI and calibrated core into one TopSpin/Jython script."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent

def write_lf(path, text):
    """Stable UTF-8/LF bytes on Windows and Unix, including Python 3.8."""
    normalized = "\n".join(line.rstrip() for line in text.splitlines()).rstrip() + "\n"
    path.write_bytes(normalized.encode("utf-8"))


def main():
    parts = ['# -*- coding: utf-8 -*-', 'from __future__ import unicode_literals', 'import sys, types',
        '_source_path=globals().get("__file__",sys.argv[0] if sys.argv else "spectrometer_calibration_gui.py")']
    base = (HERE.parent / 'topspin_console_v3/dist/dosy_workshop_v3.py').read_text(encoding='utf-8')
    parts += ['_base={"__name__":"_gui_core"}',
              'exec(compile(%s.encode("utf-8"),"calibration_core.py","exec"),_base)' % ascii(base)]
    for module, file in [('instrument_setup','instrument_setup.py'),('calibration_workflow','calibration_workflow.py'),('_cal_gui','gui.py')]:
        source = (HERE / file).read_text(encoding='utf-8')
        parts += ['_m=types.ModuleType(%r)' % module, 'sys.modules[%r]=_m' % module,
                  '_m.__file__=_source_path',
                  'exec(compile(%s.encode("utf-8"),%r,"exec"),_m.__dict__)' % (ascii(source),file)]
    parts += ['if __name__=="__main__":',
              '    _demo="--demo" in sys.argv',
              '    if not _demo:',
              '        import TopCmds as _api',
              '    else:',
              '        _api=None',
              '    def _dispatch():',
              '        _app=sys.modules["_cal_gui"].APP',
              '        _fn=_app.job',
              '        def _callback():',
              '            _app.job_started=True',
              '            _fn()',
              '        _app.command_thread=_api.EXEC_PYSCRIPT("CMDTHREAD.getArgList()()",_callback)',
              '        if _app.command_thread is None: raise ValueError("TopSpin returned no command thread")',
              '    _app=sys.modules["_cal_gui"].main(api=_api,demo=_demo,dispatch=None if _demo else _dispatch)',
              '    _app.bundle_revision="calgui.1.0.callback1"',
              '']
    # Reopening xpy focuses the existing window. An older idle GUI can be
    # replaced, but a running job must keep its modules and callback intact.
    guard=['_reuse=None',
        'if __name__=="__main__" and "--demo" not in sys.argv:',
        '    _previous=sys.modules.get("_cal_gui")',
        '    _old=getattr(_previous,"APP",None)',
        '    if _old is not None and _old.frame.isDisplayable():',
        '        from javax.swing import SwingUtilities',
        '        if _old.running or getattr(_old,"bundle_revision",None)=="calgui.1.0.callback1":',
        '            _reuse=_old',
        '            SwingUtilities.invokeAndWait(_previous.Task(lambda:(_old.show(),_old.frame.toFront())))',
        '        else:',
        '            SwingUtilities.invokeAndWait(_previous.Task(lambda:_old.frame.dispose()))']
    parts=parts[:4]+guard+['if _reuse is None:']+['    '+line for line in parts[4:]]
    out=HERE / 'dist'; out.mkdir(exist_ok=True)
    target=out / 'spectrometer_calibration_gui.py'; write_lf(target, '\n'.join(parts))
    sources=[HERE/'gui.py',HERE/'calibration_workflow.py',HERE/'instrument_setup.py',HERE.parent/'topspin_console_v3/dist/dosy_workshop_v3.py',target]
    write_lf(out/'sources_sha256.json', json.dumps({p.relative_to(HERE.parent).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2) + '\n')
    print(target)

if __name__=='__main__':main()
