"""Archive the complete WPF release and verify every member on readback."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

BLOCK = 1024 * 1024
WORKSPACE = Path(__file__).resolve().parents[3]

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(BLOCK), b''):
            h.update(chunk)
    return h.hexdigest()

def read_json(path):
    return json.loads(path.read_text('utf-8-sig'))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    folder, output = args.folder.resolve(), args.output.resolve()
    if not folder.is_relative_to(WORKSPACE) or not output.is_relative_to(WORKSPACE):
        raise ValueError('Release input and output must remain inside the workspace.')
    report = output.with_suffix('.verification.json')
    partial = output.with_suffix('.zip.partial')
    if output.exists() or report.exists() or partial.exists():
        raise FileExistsError('Preserve existing archives/reports; choose a fresh output.')
    manifest = {k.lower(): v for k, v in read_json(folder / 'Models/Beatrix/manifest.json').items()}
    if (not manifest['finetuned'] or not manifest['qualitypassed']
            or manifest['nativeevaluationpending'] is not False
            or not manifest['nativeevaluationpassed'] or manifest['experimentalvalidation']):
        raise ValueError('The local educational tutor release is not approved.')
    if sha(folder / 'Content/course.json') != manifest['coursesha256']:
        raise ValueError('Course/model mismatch.')
    records = read_json(folder / 'PACKAGE_SHA256.json')
    expected = {record['path']: record for record in records}
    actual = {path.relative_to(folder).as_posix(): path for path in folder.rglob('*') if path.is_file()}
    if set(actual) != set(expected) | {'PACKAGE_SHA256.json'}:
        raise ValueError('Files changed since the package manifest was generated.')
    for name, record in expected.items():
        if actual[name].is_symlink() or actual[name].stat().st_size != record['bytes'] or sha(actual[name]) != record['sha256']:
            raise ValueError(f'Package member identity mismatch: {name}')
    model_name = 'Models/Beatrix/' + manifest['file']
    if expected[model_name]['sha256'] != manifest['sha256']:
        raise ValueError('Packaged model identity mismatch.')
    expected['PACKAGE_SHA256.json'] = {'path': 'PACKAGE_SHA256.json', 'bytes': actual['PACKAGE_SHA256.json'].stat().st_size,
                                     'sha256': sha(actual['PACKAGE_SHA256.json'])}
    with zipfile.ZipFile(partial, 'w', allowZip64=True, compresslevel=6) as archive:
        for name, path in sorted(actual.items()):
            info = zipfile.ZipInfo(folder.name + '/' + name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED if path.suffix.lower() in {'.gguf', '.mp4', '.png'} else zipfile.ZIP_DEFLATED
            with path.open('rb') as source, archive.open(info, 'w', force_zip64=True) as target:
                for chunk in iter(lambda: source.read(BLOCK), b''):
                    target.write(chunk)
    with zipfile.ZipFile(partial) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != {folder.name + '/' + name for name in expected}:
            raise ValueError('Archive membership mismatch.')
        for name, record in sorted(expected.items()):
            h, size = hashlib.sha256(), 0
            # Reading through EOF checks the ZIP CRC as well as SHA-256.
            with archive.open(folder.name + '/' + name) as member:
                for chunk in iter(lambda: member.read(BLOCK), b''):
                    size += len(chunk)
                    h.update(chunk)
            if size != record['bytes'] or h.hexdigest() != record['sha256']:
                raise ValueError(f'Archive readback mismatch: {name}')
    partial.rename(output)
    verification = {'passed': True, 'scope': 'Complete archive membership, byte count, CRC and SHA-256 readback; software package integrity only.',
                    'archive': str(output), 'bytes': output.stat().st_size, 'sha256': sha(output), 'files': len(expected),
                    'uncompressed_bytes': sum(item['bytes'] for item in expected.values()), 'model_sha256': manifest['sha256'],
                    'course_sha256': manifest['coursesha256'], 'experimental_validation': False}
    report.write_text(json.dumps(verification, indent=2), encoding='utf-8')
    print(json.dumps(verification))

if __name__ == '__main__':
    main()
