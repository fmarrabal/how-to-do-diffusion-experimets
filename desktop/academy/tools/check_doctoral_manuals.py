"""Read-only PDF structure checks and contact sheets for explicit visual QA."""
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont
from pypdf import PdfReader
from reportlab.pdfbase.ttfonts import TTFont
import hashlib,json
ROOT=Path(__file__).resolve().parents[3];A=ROOT/'desktop'/'academy';Q=A/'qa'/'doctoral-1.2'/'manuals'
font=TTFont('inspection',r'C:/Windows/Fonts/segoeui.ttf');mathfont=TTFont('mathInspection',r'C:/Windows/Fonts/DejaVuSans.ttf');label=ImageFont.truetype(r'C:/Windows/Fonts/segoeuib.ttf',18)
checks=[];outputs=[]
for lang in ('ES','EN'):
 file=A/'docs'/f'DOCTORAL_MANUAL_{lang}.pdf';reader=PdfReader(file);text='\n'.join(p.extract_text() or '' for p in reader.pages)
 checks.append({'id':f'{lang}-22-pages','passed':len(reader.pages)==22})
 checks.append({'id':f'{lang}-every-page-has-text','passed':all(len((p.extract_text() or '').strip())>200 for p in reader.pages)})
 checks.append({'id':f'{lang}-no-pending-capture','passed':'Captura pendiente' not in text and 'capture pending' not in text})
 missing=sorted({c for c in text if ord(c)>32 and not font.face.charToGlyph.get(ord(c)) and not mathfont.face.charToGlyph.get(ord(c))})
 checks.append({'id':f'{lang}-all-glyphs-supported','passed':not missing,'missing':missing})
 checks.append({'id':f'{lang}-no-missing-glyph-null-or-replacement','passed':'\x00' not in text and '\ufffd' not in text})
 urls=[]
 for page in reader.pages:
  for annotation in page.get('/Annots') or []:
   obj=annotation.get_object();action=obj.get('/A')
   if action and action.get('/URI'):urls.append(str(action.get('/URI')))
 checks.append({'id':f'{lang}-source-DOIs-linked','passed':all(any(x in u for u in urls) for x in ('10.26180/33075584.v1','10.1002/cmr.a.21223','10.1002/cmr.a.21241','10.1039/D0CC07757G')),'links':len(urls)})
 checks.append({'id':f'{lang}-actual-final-GUI-captures','passed':all((Q/f'{lang.lower()}-{v}-viewport.png').is_file() for v in ('sync','sequence','guided','campaign','blind','inverse','real-case-processed','advanced','assessment'))})
 pages=sorted(Q.glob(f'{lang}-page-*.png'))
 checks.append({'id':f'{lang}-all-pages-rendered','passed':len(pages)==len(reader.pages)})
 for group in range(0,len(pages),6):
  sheet=Image.new('RGB',(1470,1440),'#dbe5ef');draw=ImageDraw.Draw(sheet)
  for n,file in enumerate(pages[group:group+6]):
   image=Image.open(file).convert('RGB');thumb=ImageOps.contain(image,(470,670));x=15+(n%3)*490;y=45+(n//3)*715;sheet.paste(thumb,(x,y));draw.text((x,y-28),file.stem,fill='#12324a',font=label)
  sheet.save(Q/f'{lang}-contact-{group//6+1}.png')
 outputs.append({'language':lang.lower(),'pages':len(reader.pages),'sha256':hashlib.sha256((A/'docs'/f'DOCTORAL_MANUAL_{lang}.pdf').read_bytes()).hexdigest(),'renderedPages':len(pages),'links':len(urls)})
report={'passed':all(x['passed'] for x in checks),'checks':checks,'outputs':outputs,'allPagesVisuallyReviewed':False,'scope':'PDF structural checks. Visual inspection must be completed separately before promotion.'}
(Q/'manuals-structural-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False,indent=2))
if not report['passed']:raise SystemExit(1)
