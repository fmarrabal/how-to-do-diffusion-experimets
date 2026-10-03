"""Create and verify the portable calibration GUI distribution."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json

HERE = Path(__file__).resolve().parent

def main():
    files = {}
    names = ['README.md', 'run_demo.ps1', 'gui.py', 'calibration_workflow.py',
             'instrument_setup.py', 'build_bundle.py', 'build_manuals.py',
             'build_release.py', 'gui_selftest.py', 'test_workflow.py',
             'test_instrument_setup.py', 'backend_contract.json',
             'manual_content.json', 'GUI_VERIFICATION.json', 'RELEASE_VERIFICATION.json', 'PUBLICATION_PROVENANCE.json']
    for name in names:
        files['calibration_gui/' + name] = HERE / name
    for directory in ['dist', 'screenshots', 'output/pdf']:
        for source in (HERE / directory).glob('*'):
            if source.is_file():
                files['calibration_gui/' + source.relative_to(HERE).as_posix()] = source
    for name in ['native_pilot.json', 'native_gui_pilot.json']:
        source = HERE / 'verification' / name
        if source.is_file():files['calibration_gui/verification/' + name] = source
    source = HERE.parent / 'topspin_console_v3/dist/dosy_workshop_v3.py'
    files['topspin_console_v3/dist/dosy_workshop_v3.py'] = source
    text_extensions = {'.py', '.json', '.md', '.txt', '.ps1'}
    for name, path in files.items():
        if path.suffix.lower() in text_extensions:
            raw = path.read_bytes()
            text = raw.decode('utf-8')
            if b'\r' in raw or any(line != line.rstrip() for line in text.splitlines()) or not text.endswith('\n') or text.endswith('\n\n'):
                raise ValueError('Public text must use LF, no trailing spaces and one final newline: ' + name)
    manifest = {name: hashlib.sha256(path.read_bytes()).hexdigest()
                for name, path in sorted(files.items())}
    target = HERE / 'output/DiffAtOnce_Calibration_GUI_ES_EN_v1_public.zip'
    with ZipFile(target, 'w', ZIP_DEFLATED) as archive:
        for name, path in sorted(files.items()):archive.write(path, name)
        archive.writestr('MANIFEST_SHA256.json', (json.dumps(manifest, indent=2) + '\n').encode('utf-8'))
    with ZipFile(target) as archive:
        assert archive.testzip() is None
        for name, digest in manifest.items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == digest, name
    print(json.dumps({'zip': str(target), 'files': len(manifest),
                      'bytes': target.stat().st_size,
                      'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}, indent=2))

if __name__ == '__main__':main()
