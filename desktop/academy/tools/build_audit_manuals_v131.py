"""Prepend reviewed Academy 1.3.1 corrections to four preserved 1.3 manuals.

The caller supplies a hash-bound original snapshot and a fresh QA directory.
No source PDF page content is redrawn or relabelled as a current screenshot.
Structural QA is separate from the required raster and visual review.
"""
from __future__ import annotations
import argparse
from datetime import datetime
import hashlib
import json
import logging
from pathlib import Path
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

from pypdf import PdfReader, PdfWriter
from pypdf.annotations import Link
from pypdf.constants import PageLabelStyle
from pypdf.generic import NameObject, TextStringObject
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

from consolidate_academy_manuals_v13 import rebase_source_annotations, verify_links, source_links

ROOT=Path(__file__).resolve().parents[3]
DOCS=ROOT/'desktop/academy/docs'
BLUE=colors.HexColor('#132f3d');TEAL=colors.HexColor('#087d78');GREY=colors.HexColor('#536a73')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def L(lang,es,en):return es if lang=='ES' else en

def blocks(lang):
    return [
      (L(lang,'Intervalos y problema inverso','Intervals and the inverse problem'),[
        (L(lang,'El intervalo pertenece al ajuste mono','The interval belongs to the mono fit'),
         L(lang,'El Monte Carlo vuelve a ajustar el modelo monoexponencial de referencia. La interfaz identifica su D e intervalo por separado. Si eliges NNLS, Tikhonov o L1, el centroide ILT es otro estimador: el intervalo mono no cuantifica ese centroide ni la forma, máximos o número de componentes de la distribución. Aquí no se calcula incertidumbre de una distribución ILT.',
         'Monte Carlo refits the reference monoexponential model. The interface identifies its D and interval separately. With NNLS, Tikhonov or L1 selected, the ILT centroid is a different estimator: the mono interval does not quantify that centroid or distribution shape, peaks or component count. ILT distribution uncertainty is not computed here.')),
        (L(lang,'La lista singular no demuestra unicidad','The singular list does not establish uniqueness'),
         L(lang,'Una matriz de 20 observaciones por 64 valores D tiene rango como máximo 20 y al menos 44 direcciones nulas derechas. Sus 20 valores singulares devueltos pueden ser no nulos y aun así dejar ese espacio sin resolver. El aviso incluye esta limitación; no cuenta moléculas ni demuestra que toda solución positiva sea imposible.',
         'A matrix with 20 observations and 64 D values has rank at most 20 and at least 44 right-nullspace directions. All 20 returned singular values may be nonzero while that space remains unresolved. The warning includes this limit; it neither counts molecules nor proves every positive solution impossible.')),
        (L(lang,'Por qué se hace esta comprobación','Why make this check'),
         L(lang,'Un residuo pequeño y un intervalo estrecho responden a preguntas distintas. Compara regularización, malla, datos reservados y alternativas compatibles. Mantén el mismo procesado y las mismas observaciones para atribuir cambios al método. Un ajuste reproducible no establece identidad química.',
         'Small residuals and narrow intervals answer different questions. Compare regularization, grid, reserved observations and compatible alternatives. Keep processing and observations fixed when attributing differences to a method. A reproducible fit does not establish chemical identity.')),
        (L(lang,'Objetivo del estudiante','Student objective'),
         L(lang,'Antes de citar un intervalo, escribe qué estimador describe, qué errores comparte y qué propiedades no calcula. No asignes al centroide ILT un intervalo obtenido para otro ajuste.',
         'Before quoting an interval, name its estimator, shared errors and uncomputed properties. Do not assign an ILT centroid an interval obtained for a different fit.')),
      ]),
      (L(lang,'Datos, orden, signo y procedencia','Data, order, sign and provenance'),[
        (L(lang,'Una referencia coherente','A consistent reference'),
         L(lang,'El procesado por señal y Monte Carlo usan la referencia de menor b. Reordenar las mismas parejas (b, señal) no debe crear ni borrar picos por cambiar la fila de referencia. Esto no equivale a invertir físicamente una adquisición: una nueva rampa puede exponer deriva o cinética real.',
         'Per-signal processing and Monte Carlo use the minimum-b reference. Reordering the same (b, signal) pairs must not create or erase peaks by changing the reference row. This differs from physically reversing acquisition: a new ramp may expose real drift or kinetics.')),
        (L(lang,'Controles reservados con signo','Signed held-out controls'),
         L(lang,'El control conserva la referencia con signo y el procesado declarado. Tomar valores absolutos o recortar señales negativas cambia el problema. Inspecciona fase, señal y modelo antes de interpretar una diferencia como difusión o separar especies.',
         'The control retains the signed reference and declared processing. Taking absolute values or clipping negative signals changes the problem. Inspect phase, signal and model before interpreting a difference as diffusion or separating species.')),
        (L(lang,'Importar no demuestra calibración','Import does not establish calibration'),
         L(lang,'Una serie importada y sus metadatos no aportan por sí solos una referencia independiente. Se distinguen procedencia, escala aplicada y evidencia disponible. Una escala introducida por el usuario sigue siendo condicional; sin b documentada no se inventa un ajuste D.',
         'An imported series and metadata do not themselves supply an independent reference. Provenance, applied scale and available evidence remain distinct. A user-entered scale remains conditional; undocumented b values do not produce an invented D fit.')),
        (L(lang,'Valores válidos y estabilidad','Valid inputs and stability'),
         L(lang,'Gradientes vacíos/no numéricos, referencias o fases no finitas y conversiones a SI que desborden se rechazan con explicación ES/EN. No se convierten en cero. El ajuste de datos con b no nulo usa una referencia desplazada al menor b; si la amplitud extrapolada a b=0 no es representable, se indica no disponible, no NaN como resultado físico.',
         'Empty/non-numeric gradients, non-finite reference/phase values and overflowing SI conversions are rejected with ES/EN explanations. They are not converted to zero. Nonzero-b fitting uses a minimum-b shifted reference; an unrepresentable extrapolated b=0 amplitude is reported unavailable, not NaN as a physical result.')),
      ]),
      (L(lang,'Correcciones y controles prácticos','Corrections and practical controls'),[
        (L(lang,'Dos erratas concretas','Two specific teaching corrections'),
         L(lang,'Ejemplo temperature-standard/factors: 0.89 x 293/301 = 0.86634551495, que se redondea a 0.8663 en ES/EN. La D corregida, 0.33 x 0.86634551495 = 0.2859 en unidades 10^-9 m²/s, no cambia. La nota española de Kuchel 2012 [38] dice ahora g0=0, no g00; la ecuación matemática no cambia.',
         'Example temperature-standard/factors: 0.89 x 293/301 = 0.86634551495, rounded to 0.8663 in ES/EN. Corrected D, 0.33 x 0.86634551495 = 0.2859 in 10^-9 m²/s units, is unchanged. The Spanish Kuchel 2012 [38] note now says g0=0, replacing g00; the mathematical equation is unchanged.')),
        (L(lang,'Una práctica para detectar errores','A practical error-detection exercise'),
         L(lang,'1. Explica las unidades y conserva signo, fase y referencia. 2. Compara mono e ILT sobre los mismos datos y lee qué estimador cubre el intervalo. 3. Invierte las filas emparejadas y distingue esa prueba de readquirir otra rampa. 4. Introduce un valor inválido y verifica su rechazo. 5. Importa con procedencia y diseña un control que pueda refutar la conclusión.',
         '1. Explain units and retain sign, phase and reference. 2. Compare mono and ILT on the same observations and read which estimator the interval covers. 3. Reverse paired rows and distinguish that test from reacquiring a ramp. 4. Enter an invalid value and verify rejection. 5. Import with provenance and design a control that can refute the conclusion.')),
        (L(lang,'Qué acreditan las comprobaciones','What the checks establish'),
         L(lang,'La auditoría compara ejemplos, límites analíticos, contratos de software e interfaces ES/EN. El validador distingue identidad binaria del PPTX y coincidencia fresca de sus 81 diapositivas registradas. Los originales e informes históricos permanecen conservados. Estas comprobaciones no son calibración física, identificación química ni un estudio de eficacia docente.',
         'The audit compares examples, analytic limits, software contracts and ES/EN interfaces. The validator separates PPTX byte identity from fresh agreement of its 81 recorded slides. Originals and historical reports remain preserved. These checks are not physical calibration, chemical identification or an educational-efficacy study.')),
        (L(lang,'Beatrix, fuentes y alcance','Beatrix, sources and scope'),
         L(lang,'Documentación, entrenamiento ejecutado y evaluación nativa aprobada son evidencias distintas. La consulta matemática conserva sus fuentes Sinnaeve/Kuchel; modelos UF/SPEN simplificados no certifican una secuencia experimental completa. Consulta las notas bilingües y los informes de la entrega para el alcance exacto.',
         'Documentation, executed training and approved native evaluation are distinct evidence. Mathematical guidance retains its Sinnaeve/Kuchel references; simplified UF/SPEN models do not certify a complete experimental sequence. Read bilingual notes and release reports for the exact scope.')),
      ]),
    ]

def register_fonts(folder):
    for name,file in [('Audit','arial.ttf'),('AuditBold','arialbd.ttf')]:
        pdfmetrics.registerFont(TTFont(name,str(folder/file)))

def paragraph(c,text,y,*,size=10.4,bold=False,color=BLUE,leading=15.2):
    p=Paragraph(escape(text),ParagraphStyle('audit',fontName='AuditBold' if bold else 'Audit',fontSize=size,leading=leading,textColor=color))
    _,height=p.wrap(170*mm,A4[1])
    if y-height < 23*mm:raise ValueError('Addendum page overflow')
    p.drawOn(c,20*mm,y-height)
    return y-height

def frame(c,lang,page,total,kind):
    c.setFont('AuditBold',8);c.setFillColor(BLUE)
    c.drawString(20*mm,A4[1]-13*mm,'DIFFATONCE ACADEMY / 1.3.1')
    kind_label=L(lang,'MANUAL COMPLETO' if kind=='complete' else 'INVESTIGACIÓN','COMPLETE MANUAL' if kind=='complete' else 'RESEARCH GUIDE')
    c.setFillColor(TEAL);c.drawRightString(A4[0]-20*mm,A4[1]-13*mm,lang+' / '+kind_label)
    c.setStrokeColor(colors.HexColor('#dce7e9'));c.line(20*mm,A4[1]-16*mm,A4[0]-20*mm,A4[1]-16*mm)
    c.setFont('Audit',8);c.setFillColor(GREY)
    c.drawString(20*mm,11*mm,L(lang,'Correcciones vigentes; cuerpo 1.3 conservado','Current corrections; 1.3 body retained'))
    c.drawRightString(A4[0]-20*mm,11*mm,f'PDF {page} / {total}')

def wrapper(lang,kind,source_pages,qa):
    path=qa/f'addendum-{kind}-{lang.lower()}.pdf'
    total=source_pages+4
    c=canvas.Canvas(str(path),pagesize=A4,pageCompression=1)
    frame(c,lang,1,total,kind)
    y=A4[1]-39*mm
    y=paragraph(c,L(lang,'AUDITORÍA / 1.3.1','AUDIT / 1.3.1'),y,size=12,bold=True,color=TEAL)-10*mm
    title=L(lang,'Manual completo' if kind=='complete' else 'Guía de investigación','Complete manual' if kind=='complete' else 'Research guide')
    y=paragraph(c,title,y,size=30,bold=True,leading=37)-5*mm
    y=paragraph(c,L(lang,'Interpretar cada resultado con el estimador y la evidencia correctos.','Interpret every result with the correct estimator and evidence.'),y,size=17,leading=24)-12*mm
    y=paragraph(c,L(lang,'WPF y web / Español / 30 de octubre de 2026','WPF and browser / English / 30 October 2026'),y,color=GREY)-10*mm
    for text in [
      L(lang,'Este suplemento de cuatro páginas contiene las correcciones vigentes de la auditoría 1.3.1. Léelo antes del manual conservado, especialmente si comparas distribuciones ILT e intervalos Monte Carlo.','This four-page supplement contains current 1.3.1 audit corrections. Read it before the retained manual, especially when comparing ILT distributions and Monte Carlo intervals.'),
      L(lang,'A partir de la página PDF 5 se conserva intacto el documento 1.3. Sus pantallas, títulos y numeración son históricos; no se presentan como nuevas capturas 1.3.1. Las precisiones de este suplemento prevalecen sobre las instrucciones conservadas.','The unchanged 1.3 document begins on PDF page 5. Its screens, titles and printed numbering are historical; they are not new 1.3.1 captures. Qualifications in this supplement supersede retained instructions.'),
    ]:y=paragraph(c,text,y)-7*mm
    links=[]
    entries=[(L(lang,'02 Intervalos y problema inverso','02 Intervals and the inverse problem'),1),
             (L(lang,'03 Datos, orden, signo y procedencia','03 Data, order, sign and provenance'),2),
             (L(lang,'04 Correcciones y controles prácticos','04 Corrections and practical controls'),3),
             (L(lang,'05 Abrir el manual 1.3 conservado','05 Open the retained 1.3 manual'),4)]
    for text,target in entries:
        y-=1*mm;c.setFillColor(TEAL);c.setFont('AuditBold',10.4);c.drawString(20*mm,y,text+'  >')
        links.append((0,(20*mm,y-4,190*mm,y+12),target));y-=8*mm
    c.showPage()
    for index,(heading,sections) in enumerate(blocks(lang),1):
        frame(c,lang,index+1,total,kind);y=A4[1]-29*mm
        y=paragraph(c,heading,y,size=23,bold=True,leading=29)-7*mm
        for title,text in sections:
            y=paragraph(c,title,y,size=11.1,bold=True,color=TEAL,leading=16)-2.5*mm
            y=paragraph(c,text,y)-6*mm
        if index==3:
            c.linkURL('https://diffatonce.com/academy' if lang=='ES' else 'https://diffatonce.com/en/academy',(20*mm,20*mm,115*mm,26*mm),relative=0)
            c.setFont('AuditBold',9.5);c.setFillColor(TEAL);c.drawString(20*mm,22*mm,L(lang,'Academy y notas de la entrega >','Academy and release notes >'))
        c.showPage()
    c.save();return path,links

def outline_count(reader):
    def visit(items):
        count=0
        for item in items:
            if isinstance(item,list):count+=visit(item)
            else:
                page=reader.get_destination_page_number(item)
                assert 0<=page<len(reader.pages),(item.title,page)
                count+=1
        return count
    return visit(reader.outline)

def build_one(name,before,qa,expected):
    original=before/name
    assert sha(original)==expected['sha256'] and original.stat().st_size==expected['bytes']
    lang='ES' if '_ES.' in name else 'EN';kind='complete' if name.startswith('ACADEMY_') else 'research'
    reader=PdfReader(original);assert len(reader.pages)==(68 if kind=='complete' else 22)
    wrap,links=wrapper(lang,kind,len(reader.pages),qa);wrap_reader=PdfReader(wrap)
    writer=PdfWriter();writer.append(wrap_reader,import_outline=False)
    audit_parent=writer.add_outline_item(L(lang,'Actualización 1.3.1','Update 1.3.1'),0)
    for i,(heading,_) in enumerate(blocks(lang),1):writer.add_outline_item(heading,i,parent=audit_parent)
    writer.append(reader,outline_item=L(lang,'Manual 1.3 conservado - capturas históricas','Retained 1.3 manual - historical screenshots'),import_outline=True)
    rebased=rebase_source_annotations(writer,reader,4)
    for page,rect,target in links:
        annotation=writer.add_annotation(page,Link(rect=rect,target_page_index=target))
        annotation['/Dest'][0]=writer.pages[target].indirect_reference
    writer.set_page_label(0,3,style=PageLabelStyle.DECIMAL,prefix='1.3.1 Audit - ',start=1)
    old_labels=reader.page_labels
    for i,text in enumerate(old_labels):writer.set_page_label(i+4,i+4,style=None,prefix=text)
    created=datetime.now(ZoneInfo('Europe/Madrid'));offset=created.strftime('%z')
    date='D:'+created.strftime('%Y%m%d%H%M%S')+offset[:3]+"'"+offset[3:]+"'"
    title='DiffAtOnce Academy 1.3.1 - '+L(lang,'Manual completo' if kind=='complete' else 'Guía de investigación','Complete manual' if kind=='complete' else 'Research guide')
    writer.add_metadata({'/Title':title,'/Author':'DiffAtOnce Academy','/Subject':L(lang,'Correcciones vigentes e instrucciones 1.3 conservadas sin modificar','Current corrections and unchanged retained 1.3 instructions'),'/CreationDate':date,'/ModDate':date})
    writer._root_object[NameObject('/Lang')]=TextStringObject(lang.lower());writer.page_mode='/UseOutlines'
    output=DOCS/name
    if output.exists() and sha(output)!=expected['sha256']:
        assert '1.3.1' in (PdfReader(output).metadata.title or ''),'Preserve unrelated PDF changes'
    with output.open('wb') as stream:writer.write(stream)
    writer.close();current=PdfReader(output)
    assert len(current.pages)==len(reader.pages)+4 and '1.3.1' in current.metadata.title
    assert current.page_labels[4:]==old_labels
    for i,page in enumerate(reader.pages):
        assert page.extract_text()==current.pages[i+4].extract_text(),(name,i,'Text changed')
        assert list(page.mediabox)==list(current.pages[i+4].mediabox)
        assert source_links(page)==source_links(current.pages[i+4]),(name,i,'URI changed')
    old_internal,old_uri=verify_links(reader);internal,uri=verify_links(current)
    assert [(x['fromPage']+4,x['toPage']+4) for x in old_internal] == [(x['fromPage'],x['toPage']) for x in internal if x['fromPage']>4]
    assert len(internal)==len(old_internal)+len(links)
    count=outline_count(current)
    assert sha(original)==expected['sha256'],'Original snapshot changed'
    return {'path':str(output.relative_to(ROOT)),'bytes':output.stat().st_size,'sha256':sha(output),'pages':len(current.pages),'language':lang.lower(),'originalSha256':expected['sha256'],'originalPages':len(reader.pages),'addendumPages':4,'sourcePageOffset':4,'internalLinksVerified':len(internal),'sourceLinksRebased':rebased,'outlineDestinationsVerified':count,'externalUrisRetained':len(old_uri),'sourcePageTextAndBoxesIdentical':True,'pageLabelsRetained':True}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before',type=Path,required=True)
    parser.add_argument('--qa',type=Path,required=True)
    parser.add_argument('--fonts',type=Path,default=Path('C:/Windows/Fonts'))
    args=parser.parse_args();args.qa.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((args.before/'SHA256.json').read_text())
    baseline={Path(r['path']).name:r for r in manifest['files']}
    register_fonts(args.fonts)
    log=logging.getLogger('pypdf.generic._link');log.addHandler(logging.FileHandler(args.qa/'library-link-warnings.log',mode='w',encoding='utf-8'));log.propagate=False
    outputs=[build_one(prefix+lang+'.pdf',args.before,args.qa,baseline[prefix+lang+'.pdf']) for prefix in ('ACADEMY_MANUAL_','RESEARCH_MANUAL_') for lang in ('ES','EN')]
    result={'version':'1.3.1','passed':False,'structurePassed':True,'visualReviewPending':True,'rasterInvariantPending':True,'originalPagesRetained':sum(o['originalPages'] for o in outputs),'newAddendumPages':16,'outputs':outputs,'sourceManualSnapshotsPreserved':True,'scope':'Four reviewed-documentation addenda; old 1.3 source pages and screenshots retained as historical. Structural checks are not visual, scientific/hardware or teaching-efficacy validation.'}
    (args.qa/'manual-build-report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
