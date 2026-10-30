"""Preserve licences/notices from the exact resolved NuGet packages."""
from pathlib import Path
import json
import shutil
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
assets = json.loads((root / 'src/DiffAtOnce.Academy.App/obj/project.assets.json').read_text('utf-8'))
output = root / 'THIRD_PARTY'
output.mkdir(exist_ok=True)
mit = '''Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''
records = []
for name, library in sorted(assets['libraries'].items()):
    if library.get('type') != 'package':
        continue
    package = next((Path(folder) / library['path'] for folder in assets['packageFolders']
                    if (Path(folder) / library['path']).is_dir()), None)
    if package is None:
        raise RuntimeError(f'Resolved package is unavailable: {name}')
    nuspec = next(package.glob('*.nuspec'))
    tree = ET.parse(nuspec)
    fields = {e.tag.rsplit('}', 1)[-1]: e for e in tree.iter()}
    destination = output / name.replace('/', '-')
    destination.mkdir(exist_ok=True)
    shutil.copy2(nuspec, destination / nuspec.name)
    copied = []
    for relative in library.get('files', []):
        path = Path(relative)
        if path.name.upper().startswith(('LICENSE', 'NOTICE', 'THIRD-PARTY-NOTICE')) and (package / path).is_file():
            target = destination / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(package / path, target)
            copied.append(path.as_posix())
    licence = fields.get('license')
    expression = licence.text if licence is not None else ''
    if licence is not None and licence.get('type') == 'expression' and expression == 'MIT':
        copyright_field = fields.get('copyright')
        copyright_text = copyright_field.text if copyright_field is not None else ''
        authors = fields.get('authors')
        text = (f'{name}\nMIT License\n\n{copyright_text}\nAuthors: '
                f'{authors.text if authors is not None else "See package metadata"}\n\n{mit}')
        (destination / 'MIT-LICENSE.txt').write_text(text, encoding='utf-8')
        copied.append('MIT-LICENSE.txt')
    if not copied:
        raise RuntimeError(f'No distribution licence preserved: {name} ({expression})')
    records.append({'package': name, 'licence': expression, 'files': copied})
(output / 'NUGET_NOTICES.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
print(json.dumps({'packages': len(records), 'directory': str(output)}))
