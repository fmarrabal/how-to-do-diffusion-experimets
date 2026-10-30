"""Preserve the editable 1.1 source before doctoral teaching extensions."""
from pathlib import Path
import hashlib, json, zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'qa' / 'doctoral-1.2' / 'baseline-v1.1'
if OUT.exists():
    raise FileExistsError('Preserve the baseline; do not overwrite.')
OUT.mkdir(parents=True)
paths = []
for folder in ['src', 'web', 'tools', 'docs']:
    for p in (ROOT / folder).rglob('*'):
        if p.is_file() and not any(x in {'bin', 'obj', '__pycache__', 'node_modules'} for x in p.parts) and not p.name.startswith('doctoral-'):
            paths.append(p)
paths += [ROOT / 'README.md', ROOT / 'START_HERE_ES_EN.txt', ROOT / 'content/course.json', ROOT / 'content/derivations.json', ROOT / 'ai/release-v1.1/manifest.json']
records = []
with zipfile.ZipFile(OUT / 'source-before-v1.2.zip', 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for p in sorted(set(paths)):
        name = p.relative_to(ROOT).as_posix()
        data = p.read_bytes()
        records.append({'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        z.writestr(name, data)
with zipfile.ZipFile(OUT / 'source-before-v1.2.zip') as z:
    for r in records:
        data = z.read(r['path'])
        assert len(data) == r['bytes'] and hashlib.sha256(data).hexdigest() == r['sha256']
(OUT / 'manifest.json').write_text(json.dumps({'passed': True, 'scope': 'Editable source snapshot only; frozen 1.0/1.1 packages and experimental originals remain untouched', 'files': records}, indent=2), encoding='utf-8')
print(json.dumps({'passed': True, 'files': len(records), 'archive': str(OUT / 'source-before-v1.2.zip')}))
