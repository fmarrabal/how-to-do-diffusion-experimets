"""Consolidate Academy 1.3 guides without altering the six source PDFs.

The four-page wrapper is new. Appended source page content, section numbering
and historical labels remain unchanged. A separate raster/visual gate closes QA.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from xml.sax.saxutils import escape

from pypdf import PdfReader, PdfWriter
from pypdf.annotations import Link
from pypdf.constants import PageLabelStyle
from pypdf.generic import ArrayObject, NameObject, TextStringObject
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

from build_research_manuals_v13 import register_fonts, clean, BLUE, TEAL, GREY

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "desktop/academy/docs"
QA = ROOT / "desktop/academy/qa/research-1.3/manuals"
REPORT = QA / "complete-manual-build-report.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def label(lang, es, en):
    return es if lang == "ES" else en


def paragraph(c, text, y, *, size=11, leading=16, bold=False, color=BLUE, width=170*mm):
    style = ParagraphStyle("wrapper", fontName="AcademyBold" if bold else "Academy", fontSize=size, leading=leading, textColor=color)
    p = Paragraph(escape(clean(text)), style)
    _, h = p.wrap(width, A4[1])
    if y-h < 22*mm:
        raise ValueError("Wrapper content exceeds its page")
    p.drawOn(c,20*mm,y-h)
    return y-h


def page_frame(c, lang, number, total):
    c.setFillColor(BLUE);c.setFont("AcademyBold",8)
    c.drawString(20*mm,A4[1]-13*mm,label(lang,"DiffAtOnce Academy / MANUAL COMPLETO 1.3","DiffAtOnce Academy / COMPLETE MANUAL 1.3"))
    c.setFillColor(TEAL);c.drawRightString(A4[0]-20*mm,A4[1]-13*mm,lang)
    c.setStrokeColor(colors.HexColor("#dce7e9"));c.line(20*mm,A4[1]-16*mm,A4[0]-20*mm,A4[1]-16*mm)
    c.setFont("Academy",8);c.setFillColor(GREY)
    c.drawString(20*mm,11*mm,label(lang,"Fuentes y numeración original conservadas","Sources and original section numbering retained"))
    c.drawRightString(A4[0]-20*mm,11*mm,f"PDF {number} / {total}")


def wrapper(lang, counts):
    research,doctoral,base = counts
    first_a = 2+research
    first_b = first_a+1+doctoral
    total = first_b+1+base
    path=QA/f"complete-wrapper-{lang.lower()}.pdf"
    c=canvas.Canvas(str(path),pagesize=A4,pageCompression=1)
    links=[]
    page_frame(c,lang,1,total)
    y=A4[1]-43*mm
    y=paragraph(c,"DIFFATONCE ACADEMY / 1.3.0",y,size=11,leading=15,bold=True,color=TEAL)-14*mm
    y=paragraph(c,label(lang,"Manual completo","Complete manual"),y,size=34,leading=40,bold=True)-6*mm
    y=paragraph(c,label(lang,"Aprender a medir, interpretar y defender la difusión por RMN.","Learn to measure, interpret and defend diffusion NMR."),y,size=17,leading=24)-11*mm
    y=paragraph(c,label(lang,"WPF y web / Español / 30 de octubre de 2026","WPF and browser / English / 30 October 2026"),y,size=11,leading=16,color=GREY)-13*mm
    parts=[
      (label(lang,"PARTE I - Investigación continua 1.3","PART I - Continuous research 1.3"),label(lang,"Instrucciones actuales: doce etapas, misma muestra, incertidumbre compartida, controles, competencias, piloto y revisión.","Current instructions: twelve stages, one sample, shared uncertainty, controls, competencies, pilot and review."),2),
      (label(lang,"APÉNDICE A - Laboratorio doctoral 1.2","APPENDIX A - Doctoral laboratory 1.2"),label(lang,"Material conservado de las nueve actividades y sus derivaciones, datos y límites. Conserva su rotulado histórico.","Retained nine-activity material, derivations, data and limits. Historical labels are preserved."),first_a),
      (label(lang,"APÉNDICE B - Curso original 1.0","APPENDIX B - Original course 1.0"),label(lang,"24 lecciones, ejemplos y herramientas del curso original. Profundización y referencia de la interfaz histórica.","24 lessons, examples and tools from the original course. Deeper study and historical-interface reference."),first_b),
    ]
    for title,body,target in parts:
        top=y
        y=paragraph(c,title,y,size=11,leading=16,bold=True,color=TEAL)-3*mm
        y=paragraph(c,body,y,size=10.3,leading=15)-9*mm
        links.append((0,(20*mm,y+4*mm,A4[0]-20*mm,top+2*mm),target))
    y=paragraph(c,label(lang,"Las instrucciones nuevas de la parte I son la referencia vigente. Los apéndices no se reescriben ni convierten capturas antiguas en interfaz actual. La guía documental, el entrenamiento ejecutado y un modelo aprobado son estados distintos.","Part I is the current instruction reference. Appendices are not rewritten or relabelled as current screenshots. Documentary guidance, executed training and an approved model are different states."),y,size=10.3,leading=15)
    c.showPage()

    page_frame(c,lang,2,total)
    y=A4[1]-29*mm
    y=paragraph(c,label(lang,"Índice del volumen y navegación","Volume contents and navigation"),y,size=23,leading=29,bold=True)-4*mm
    y=paragraph(c,label(lang,"Los números de este índice son páginas PDF del volumen. Dentro de cada parte se conserva la numeración impresa del documento fuente. Usa los enlaces o los marcadores para cambiar de parte.","Numbers below are PDF pages in this volume. Each part keeps the source document's printed numbering. Use links or bookmarks to move between parts."),y,size=10.3,leading=14)-7*mm
    entries=[
      (label(lang,"Parte I - Investigación continua 1.3","Part I - Continuous research 1.3"),2,True),
      (label(lang,"Cómo aprender y conservar la misma muestra","How to learn and retain one sample"),4,False),
    ]
    es=["01 La pregunta","02 Calibrar","03 Diseñar","04 Adquirir","05 Procesar","06 Interpretar","07 Incertidumbre","08 Próxima medida","09 RF y espacio","10 Competencias y piloto","11 Defensa y revisión","12 Datos públicos"]
    en=["01 The question","02 Calibrate","03 Design","04 Acquire","05 Process","06 Interpret","07 Uncertainty","08 Next measurement","09 RF and space","10 Competencies and pilot","11 Defence and review","12 Public data"]
    entries += [(name,6+i,False) for i,name in enumerate(es if lang=="ES" else en)]
    entries += [
      (label(lang,"Ejemplo continuo reproducible","Reproducible continuous example"),18,False),
      (label(lang,"Beatrix y modos de respuesta","Beatrix and response modes"),20,False),
      (label(lang,"Protocolo docente y retención","Instructor protocol and retention"),21,False),
      (label(lang,"Guardar, importar y fuentes","Save, import and sources"),22,False),
      (label(lang,"Apéndice A - Doctorado 1.2 / separador","Appendix A - Doctoral 1.2 / divider"),first_a,True),
      (label(lang,"Apéndice B - Curso 1.0 / separador","Appendix B - Course 1.0 / divider"),first_b,True),
    ]
    for text,target,bold in entries:
        c.setFillColor(TEAL if bold else BLUE);c.setFont("AcademyBold" if bold else "Academy",10.2)
        c.drawString(20*mm,y,text);c.drawRightString(A4[0]-20*mm,y,str(target+1))
        links.append((1,(20*mm,y-4,A4[0]-20*mm,y+11),target))
        y-=19
    paragraph(c,label(lang,"Cada capítulo mantiene su procedencia. Los enlaces web de los apéndices reflejan la fecha original; para instalación y acceso actuales usa la parte I y la página de Academy.","Each chapter retains provenance. Appendix web links reflect their original date; use Part I and the Academy product page for current installation/access."),y-8*mm,size=9.4,leading=13,color=GREY)
    c.showPage()

    for which,start,version in [("A",first_a,"1.2"),("B",first_b,"1.0")]:
        page_frame(c,lang,start+1,total);y=A4[1]-45*mm
        y=paragraph(c,("APÉNDICE " if lang=="ES" else "APPENDIX ")+which,y,size=12,leading=16,bold=True,color=TEAL)-12*mm
        title=(label(lang,"Laboratorio doctoral","Doctoral laboratory") if which=="A" else label(lang,"Curso original y herramientas","Original course and tools"))
        y=paragraph(c,title,y,size=30,leading=37,bold=True)-6*mm
        y=paragraph(c,label(lang,"Documento fuente conservado - versión ","Retained source document - version ")+version,y,size=15,leading=21,color=GREY)-14*mm
        if which=="A":
            texts=[
              label(lang,"Las siguientes 22 páginas corresponden al manual doctoral 1.2, de 5 de octubre de 2026. Las nueve actividades permanecen disponibles en Doctorado.","The next 22 pages are the doctoral manual 1.2, dated 5 October 2026. Its nine activities remain available under Doctoral."),
              label(lang,"Profundiza en movimiento, fase/eco, q(t), derivaciones, campaña, casos ciegos, ILT, correlaciones, FID públicos y modelos introductorios UF/SPEN.","Deepen movement, phase/echo, q(t), derivations, campaigns, blind cases, ILT, correlations, public FIDs and introductory UF/SPEN models."),
            ]
        else:
            texts=[
              label(lang,"Las siguientes 20 páginas conservan el manual de formación original 1.0. Sirven como referencia de las 24 lecciones, ejemplos, taller y funcionamiento histórico de Beatrix.","The next 20 pages retain the original training manual 1.0. They reference the 24 lessons, examples, workshop and historical Beatrix behavior."),
              label(lang,"Las capturas y los nombres de versión se mantienen intencionadamente. La edición 1.3 añade Investigación continua sin convertir esos documentos históricos en una descripción de sus nuevas pantallas.","Screenshots and version names are intentionally retained. Edition 1.3 adds Research studio without turning historical documents into descriptions of its new screens."),
            ]
        texts += [
          label(lang,"Las páginas se anexan sin cambiar el contenido, las ecuaciones, las figuras ni sus límites científicos. La página impresa vuelve a empezar en el documento fuente; la barra del lector y los marcadores identifican la posición en este volumen.","Pages are appended without changing content, equations, figures or scientific boundaries. Printed numbering restarts in the source document; the reader toolbar and bookmarks locate pages in this volume."),
          label(lang,"Para instrucciones actuales, exportación, nuevo piloto y reglas de selección del modelo usa la parte I. Sólo se utiliza un modelo cuyo manifiesto y evaluación CPU estén aprobados; en caso contrario, guía documental.","For current instructions, export, the new pilot and model-selection rules use Part I. A model is used only with an approved manifest and CPU evaluation; otherwise documentary guidance is provided."),
        ]
        for text in texts:y=paragraph(c,text,y,size=11,leading=16)-7*mm
        c.setFillColor(TEAL);c.setFont("AcademyBold",11)
        c.drawString(20*mm,y,label(lang,"Ir al documento conservado >","Open retained source document >"))
        links.append((2 if which=="A" else 3,(20*mm,y-5,160*mm,y+12),start+1))
        y-=14*mm
        c.setFillColor(TEAL);c.drawString(20*mm,y,label(lang,"Volver a las instrucciones actuales >","Return to current instructions >"))
        links.append((2 if which=="A" else 3,(20*mm,y-5,160*mm,y+12),2))
        c.showPage()
    c.save()
    return path,links,{0:0,1:1,2:first_a,3:first_b},total


def source_links(page):
    result=[]
    for annotation in page.get("/Annots",[]):
        ann=annotation.get_object();action=ann.get("/A")
        if action:
            action=action.get_object()
            if action.get("/S")=="/URI":result.append(str(action.get("/URI")))
    return result


def verify_links(reader):
    known={page.indirect_reference.idnum:i for i,page in enumerate(reader.pages)}
    internal=[];uris=[]
    for index,page in enumerate(reader.pages):
        uris.extend(source_links(page))
        for annotation in page.get("/Annots",[]):
            ann=annotation.get_object();dest=ann.get("/Dest");action=ann.get("/A")
            if action and action.get_object().get("/S")=="/GoTo":dest=action.get_object().get("/D")
            if not dest:continue
            if isinstance(dest,str):
                if dest not in reader.named_destinations:raise AssertionError((index,"Unknown named destination",dest))
            else:
                dest=dest.get_object()
                assert hasattr(dest[0],"idnum") and dest[0].idnum in known,(index,dest)
                internal.append({"fromPage":index+1,"toPage":known[dest[0].idnum]+1})
    return internal,uris


def rebase_source_annotations(writer, reader, start):
    """Explicitly retain page-target identity rather than a library page number.

    This bundled pypdf's Link helper serializes numeric targets, and repeated
    append operations can warn about deferred source links. Every local source
    link is therefore mapped from its original page reference and checked again
    after writing. Graphics/streams and external URI actions are untouched.
    """
    source_ids={page.indirect_reference.idnum:i for i,page in enumerate(reader.pages)}
    count=0
    for i,page in enumerate(reader.pages):
        old_annotations=page.get("/Annots",[])
        new_annotations=writer.pages[start+i].get("/Annots",[])
        assert len(old_annotations)==len(new_annotations),(start+i,"Annotation count changed")
        for old,new in zip(old_annotations,new_annotations):
            old=old.get_object();new=new.get_object()
            action=old.get("/A");destination=old.get("/Dest");kind="dest"
            if action and action.get_object().get("/S")=="/GoTo":
                destination=action.get_object().get("/D");kind="action"
            if not destination:continue
            assert not isinstance(destination,str),"Unexpected named link requires explicit handling"
            destination=destination.get_object();ref=destination[0]
            target=source_ids[ref.idnum] if hasattr(ref,"idnum") else int(ref)
            assert 0<=target<len(reader.pages)
            tail=list(destination[1:]);assert not any(hasattr(value,"idnum") for value in tail)
            array=ArrayObject([writer.pages[start+target].indirect_reference]+tail)
            if kind=="action":new["/A"].get_object()[NameObject("/D")]=array
            else:new[NameObject("/Dest")]=array
            count+=1
    return count


def consolidate(lang):
    source_paths=[DOCS/f"{prefix}{lang}.pdf" for prefix in ("RESEARCH_MANUAL_","DOCTORAL_MANUAL_","MANUAL_")]
    original_hashes={str(p.relative_to(ROOT)):sha(p) for p in source_paths}
    readers=[PdfReader(path) for path in source_paths];counts=[len(r.pages) for r in readers]
    assert counts==[22,22,20],(lang,counts)
    wrapper_path,links,wrapper_map,total=wrapper(lang,counts);wrap=PdfReader(wrapper_path)
    writer=PdfWriter();writer.append(wrap,pages=[0,1],import_outline=False)
    research_start=len(writer.pages)
    writer.append(readers[0],outline_item=label(lang,"Parte I - Investigación continua 1.3","Part I - Continuous research 1.3"),import_outline=True)
    a_divider=len(writer.pages);writer.append(wrap,pages=[2],import_outline=False)
    a_parent=writer.add_outline_item(label(lang,"Apéndice A - Manual doctoral 1.2 (fuente conservada)","Appendix A - Doctoral manual 1.2 (retained source)"),a_divider)
    a_start=len(writer.pages);writer.append(readers[1],import_outline=False)
    writer.add_outline_item(label(lang,"Portada de la fuente 1.2","Source 1.2 cover"),a_start,parent=a_parent)
    for i,page in enumerate(readers[1].pages[1:],1):
        lines=[s.strip() for s in (page.extract_text() or "").splitlines() if s.strip()]
        heading=lines[1]
        if len(lines)>2 and not lines[2].startswith("Manual "):heading+=" "+lines[2]
        writer.add_outline_item(heading,a_start+i,parent=a_parent)
    b_divider=len(writer.pages);writer.append(wrap,pages=[3],import_outline=False)
    b_parent=writer.add_outline_item(label(lang,"Apéndice B - Curso original 1.0 (fuente conservada)","Appendix B - Original course 1.0 (retained source)"),b_divider)
    b_start=len(writer.pages);writer.append(readers[2],import_outline=False)
    writer.add_outline_item(label(lang,"Portada de la fuente 1.0","Source 1.0 cover"),b_start,parent=b_parent)
    for entry in readers[2].outline:
        if isinstance(entry,list):continue
        writer.add_outline_item(entry.title,b_start+readers[2].get_destination_page_number(entry),parent=b_parent)
    rebased=sum(rebase_source_annotations(writer,reader,start) for reader,start in zip(readers,[research_start,a_start,b_start]))
    for local_page,rect,target in links:
        annotation=writer.add_annotation(wrapper_map[local_page],Link(rect=rect,target_page_index=target))
        annotation["/Dest"][0]=writer.pages[target].indirect_reference
    created=datetime.now(ZoneInfo("Europe/Madrid"));offset=created.strftime("%z");pdf_date="D:"+created.strftime("%Y%m%d%H%M%S")+offset[:3]+"'"+offset[3:]+"'"
    writer.add_metadata({"/Title":label(lang,"DiffAtOnce Academy 1.3 - Manual completo","DiffAtOnce Academy 1.3 - Complete manual"),"/Author":"DiffAtOnce Academy","/Subject":label(lang,"Investigación continua 1.3 e históricos identificados 1.2/1.0; 30 de octubre de 2026","Continuous research 1.3 and labelled historical 1.2/1.0 sources; 30 October 2026"),"/CreationDate":pdf_date,"/ModDate":pdf_date})
    writer._root_object.update({NameObject("/Lang"):TextStringObject(lang.lower())})
    writer.page_mode="/UseOutlines"
    for begin,end,prefix in [(0,1,"1.3 Intro - "),(research_start,a_divider-1,"1.3 Research - "),(a_divider,a_divider,"Appendix A - "),(a_start,b_divider-1,"1.2 Doctoral - "),(b_divider,b_divider,"Appendix B - "),(b_start,total-1,"1.0 Course - ")]:
        writer.set_page_label(begin,end,style=PageLabelStyle.DECIMAL,prefix=prefix,start=1)
    path=DOCS/f"ACADEMY_MANUAL_{lang}.pdf"
    with path.open("wb") as stream:writer.write(stream)
    writer.close();out=PdfReader(path)
    assert len(out.pages)==total==68
    assert out.trailer["/Root"]["/Lang"]==lang.lower()
    assert ("Manual completo" if lang=="ES" else "Complete manual") in out.metadata.title
    mappings=[]
    for source,reader,start in zip(source_paths,readers,[research_start,a_start,b_start]):
        for i,page in enumerate(reader.pages):
            target=out.pages[start+i]
            assert page.extract_text()==target.extract_text(),(source,i,"Source text changed")
            assert list(page.mediabox)==list(target.mediabox)
            assert source_links(page)==source_links(target),(source,i,"Source URI links changed")
            mappings.append({"source":str(source.relative_to(ROOT)),"sourcePage":i+1,"outputPage":start+i+1})
    internal,uris=verify_links(out)
    assert len(internal)>=len(links)
    for rel,digest in original_hashes.items():assert sha(ROOT/rel)==digest,rel
    for item in out.outline:
        if not isinstance(item,list):assert 0<=out.get_destination_page_number(item)<total
    return {"path":str(path),"relativePath":str(path.relative_to(ROOT)),"sha256":sha(path),"bytes":path.stat().st_size,"pages":total,"language":lang.lower(),"wrapperPath":str(wrapper_path.relative_to(ROOT)),"wrapperPageMap":{str(k+1):v+1 for k,v in wrapper_map.items()},"sourceHashes":original_hashes,"sourcePageMap":mappings,"sourceInternalLinksExplicitlyRebased":rebased,"internalLinksVerified":len(internal),"uriLinksPreserved":len(uris),"sectionOffsets":{"research":research_start+1,"doctoralDivider":a_divider+1,"doctoralSource":a_start+1,"baseDivider":b_divider+1,"baseSource":b_start+1}}


def main():
    QA.mkdir(parents=True,exist_ok=True);register_fonts()
    log=logging.getLogger("pypdf.generic._link");log.addHandler(logging.FileHandler(QA/"consolidation-link-library-warnings.log",mode="w",encoding="utf-8"));log.propagate=False
    outputs=[consolidate(lang) for lang in ("ES","EN")]
    report={"version":"1.3.0","passed":False,"structurePassed":True,"allPagesVisuallyReviewed":False,"rasterInvariantPending":True,"visualReviewPending":True,"scope":"Consolidation of current teaching instructions with unchanged labelled historical source manuals; not instrument or educational-efficacy validation.","outputs":outputs}
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"structurePassed":True,"visualReviewPending":True,"outputs":[{k:o[k] for k in ("path","pages","sha256","bytes","internalLinksVerified")} for o in outputs]},indent=2))


if __name__=="__main__":main()
