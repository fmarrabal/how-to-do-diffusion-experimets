"""Render all 1.3.1 manual pages and compare every retained 1.3 page pixelwise."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os
from pathlib import Path
import shutil,subprocess

from PIL import Image, ImageDraw
import pdfplumber
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def check_one(item,before,qa,poppler):
    name=Path(item['path']).name
    original=before/name;current=ROOT/item['path']
    assert sha(original)==item['originalSha256'] and sha(current)==item['sha256']
    dest=qa/name.removesuffix('.pdf').lower();old=dest/'before';new=dest/'current'
    old.mkdir(parents=True,exist_ok=True);new.mkdir(parents=True,exist_ok=True)
    for p,out in [(original,old),(current,new)]:
        subprocess.run([poppler,'-r','100','-png',str(p),str(out/'page')],check=True,capture_output=True)
    def pages(folder):return sorted(folder.glob('page-*.png'),key=lambda p:int(p.stem.rsplit('-',1)[1]))
    old_pages,new_pages=pages(old),pages(new)
    assert len(old_pages)==item['originalPages'] and len(new_pages)==item['pages']
    invariants=[]
    for i,p in enumerate(old_pages):
        with Image.open(p) as a,Image.open(new_pages[i+4]) as b:
            same=a.size==b.size and a.convert('RGB').tobytes()==b.convert('RGB').tobytes()
        assert same,(name,i+1,'Retained page pixels differ')
        invariants.append({'sourcePage':i+1,'outputPage':i+5,'pixelsIdentical':same})
    bounds=[]
    with pdfplumber.open(current) as pdf:
        for i,page in enumerate(pdf.pages[:4]):
            for word in page.extract_words():
                if word['x0']<10 or word['x1']>page.width-10 or word['top']<8 or word['bottom']>page.height-8:
                    bounds.append({'page':i+1,'word':word['text']})
    assert not bounds,(name,bounds)
    reader=PdfReader(current)
    text='\n'.join(p.extract_text() or '' for p in reader.pages[:4])
    assert all(s in text for s in ['1.3.1','mono','ILT','0.8663','g0=0'])
    assert not any(c in text for c in ['\ufffd','\u25a0'])
    sheet=Image.new('RGB',(2*827,2*1200),'#dce7e9');draw=ImageDraw.Draw(sheet)
    for i,p in enumerate(new_pages[:4]):
        with Image.open(p) as im:sheet.paste(im.convert('RGB'),((i%2)*827,30+(i//2)*1200))
        draw.text(((i%2)*827+10,(i//2)*1200+8),f'{name} / PDF {i+1}',fill='#132f3d')
    contact=qa/(name.removesuffix('.pdf').lower()+'-addendum-contact.png');sheet.save(contact)
    return {'path':item['path'],'sha256':sha(current),'renderedPages':len(new_pages),'sourceRenderedPages':len(old_pages),
        'retainedPageChecks':invariants,'newPageTextBoundsPassed':True,'newPageRequiredContentPassed':True,
        'contactSheet':str(contact.relative_to(ROOT)),'contactSheetSha256':sha(contact),
        'newPageImages':[str(p.relative_to(ROOT)) for p in new_pages[:4]]}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before',type=Path,required=True);parser.add_argument('--qa',type=Path,required=True)
    parser.add_argument('--pdftoppm',default=os.environ.get('ACADEMY_PDFTOPPM') or shutil.which('pdftoppm') or 'pdftoppm')
    args=parser.parse_args();args.qa=args.qa.resolve();args.before=args.before.resolve()
    report_path=args.qa/'manual-build-report.json';report=json.loads(report_path.read_text())
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda item:check_one(item,args.before,args.qa,args.pdftoppm),report['outputs']))
    result={'version':'1.3.1','passed':True,'allCurrentPagesRendered':sum(x['renderedPages'] for x in results),
        'allOriginalPagesRendered':sum(x['sourceRenderedPages'] for x in results),'all180RetainedPagesPixelsIdentical':all(c['pixelsIdentical'] for x in results for c in x['retainedPageChecks']),
        'newAddendumPages':16,'visualReviewPending':True,'outputs':results,
        'scope':'Complete Poppler rasterization and exact retained-page RGB comparison; new-page text/bounds checks. Manual visual inspection of all new addendum pages is still required.'}
    (args.qa/'raster-invariants.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('passed','allCurrentPagesRendered','allOriginalPagesRendered','all180RetainedPagesPixelsIdentical','newAddendumPages','visualReviewPending')}))

if __name__=='__main__':main()
