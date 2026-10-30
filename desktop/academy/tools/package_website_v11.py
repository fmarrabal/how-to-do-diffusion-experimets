"""Create scoped Hostinger upload archives; never includes server credentials.

Private PHP logic and public educational assets are separated. Before replacing
shared PHP, compare the server files with recorded original hashes and preserve
the live version. Creating these packages is not evidence of publication.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[3]
SITE = ROOT / 'website/release'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def read(path):return json.loads(path.read_text('utf-8-sig'))

def package(output,root,files):
    if output.exists():raise FileExistsError(output)
    records=[]
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for p in sorted(files):
            if p.is_symlink():raise ValueError('Symlink excluded')
            name=p.relative_to(root).as_posix()
            if p.suffix.lower()=='.gguf' or '-private.pdf' in p.name or '.private.pdf' in p.name:raise ValueError('Private input/model excluded from web')
            z.write(p,name)
            records.append({'path':name,'bytes':p.stat().st_size,'sha256':sha(p)})
    with zipfile.ZipFile(output) as z:
        if set(z.namelist())!={r['path'] for r in records}:raise ValueError('Archive membership mismatch')
        for r in records:
            h=hashlib.sha256();length=0
            with z.open(r['path']) as f:
                for part in iter(lambda:f.read(1024*1024),b''):h.update(part);length+=len(part)
            if h.hexdigest()!=r['sha256'] or length!=r['bytes']:raise ValueError('ZIP readback failed')
    return {'archive':str(output),'bytes':output.stat().st_size,'sha256':sha(output),'files':records}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,required=True);a=ap.parse_args()
    folder=a.output_dir.resolve()
    if not folder.is_relative_to(ROOT):raise ValueError('Output must remain in workspace')
    assets=SITE/'public_html/assets/academy/v1.1.0'
    manifest=read(assets/'WEB_RELEASE_SHA256.json')
    if 'pending' in manifest['releaseStatus'] or manifest['beatrix'] is not False:raise ValueError('Web bundle is not reviewed')
    for r in manifest['files']:
        p=assets/r['path']
        if sha(p)!=r['sha256'] or p.stat().st_size!=r['bytes']:raise ValueError('Final asset changed after freeze')
    folder.mkdir(parents=True,exist_ok=True)
    public=[SITE/'public_html/index.php']+[p for p in assets.rglob('*') if p.is_file()]
    private=[SITE/'diffatonce-app'/name for name in ['site.php','software-family.php','rest-v2.php','academy-data.php','academy-product.php','academy-home.php']]
    results=[package(folder/'Academy-1.1.0-public_html.zip',SITE/'public_html',public),package(folder/'Academy-1.1.0-diffatonce-app.zip',SITE/'diffatonce-app',private)]
    report={'passed':True,'published':False,'version':'1.1.0','scope':'Scoped upload packages; original server files must be compared/backed up before replacing shared PHP. No credentials, DB, model weights or private article PDFs.','webContentSha256':manifest['derivationsSha256'],'archives':results,'sharedPhpOriginals':read(ROOT/'website/backups/academy-before-20261005-r1/SHA256.json'),'wpfUploadDestination':'diffatonce-app/downloads/academy/DiffAtOnce-Academy-1.1.0-win-x64.zip'}
    target=folder/'upload-manifest.json'
    if target.exists():raise FileExistsError('Preserve existing upload evidence')
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'passed':True,'archives':[{'path':r['archive'],'bytes':r['bytes'],'sha256':r['sha256']} for r in results]}))

if __name__=='__main__':main()
