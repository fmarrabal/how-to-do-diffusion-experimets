"""Create bilingual Academy manuals from guides and actual QA screenshots.

Run with the bundled Python. Repeat --qa to prefer a newer capture directory.
No screenshot is fabricated or labelled as LLM inference from its appearance.
The optional tutor manifest is checked before claiming its quality gate passed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from html import escape
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                               Table, TableStyle, Image, KeepTogether)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.utils import ImageReader

BASE = Path(__file__).resolve().parents[1]
DOCS = BASE / "docs"
PAGE_W, PAGE_H = A4
INK = colors.HexColor("#15343E")
TEAL = colors.HexColor("#096C67")
PALE = colors.HexColor("#EFF6F6")
ORANGE = colors.HexColor("#DF7848")
WIDTH = PAGE_W - 38 * mm
CAPTURED = []

class ManualDoc(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):return
        if flowable.style.name not in {"H1", "H2"}:return
        text=flowable.getPlainText()
        if text in {"Índice", "Contents"}:return
        level=0 if flowable.style.name=="H1" else 1
        key=f"section-{self.seq.nextf('manual-section')}"
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text,key,level=level,closed=False)
        self.notify("TOCEntry",(level,text,self.page,key))

def sha(path):
    digest=hashlib.sha256()
    with Path(path).open("rb") as f:
        while data:=f.read(1024*1024):digest.update(data)
    return digest.hexdigest()
def normalized(text):
    # Skill requires ASCII hyphens, including in copied teaching prose.
    text = text.replace("\u2010", "-").replace("\u2011", "-").replace("\u2012", "-").replace("\u2013", "-").replace("\u2014", "-").replace("\u2212", "-")
    text = re.sub(r"(?<=\d)(?=(?:µs|ms|min|scans|transitorios|diapositivas|slides|módulos|modules|registros|records)\b)", " ", text)
    text = re.sub(r"\b(progreso|progress|de|with|for|the|sus|Sus|its|Its|to|para|las|the|of|de|Los|los|and|y|Actual|nontrivial|nulo|sesgo)(?=\d)", r"\1 ", text)
    text = text.replace("completo de24", "completo de 24").replace("Complete24-module", "Complete 24-module")
    text = text.replace("Exp.1000", "Exp. 1000").replace("capture.24", "capture. 24").replace("curve.22", "curve. 22")
    return text

def inline(text):
    t = escape(normalized(text))
    t = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.*?)`", r'<font color="#096C67">\1</font>', t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<link href="\2" color="#096C67">\1</link>', t)
    return t

def register_fonts():
    fontroot = Path("C:/Windows/Fonts")
    for name, file in [("Academy", "segoeui.ttf"), ("AcademyBold", "segoeuib.ttf"), ("AcademyItalic", "segoeuii.ttf")]:
        pdfmetrics.registerFont(TTFont(name, str(fontroot / file)))
    pdfmetrics.registerFontFamily("Academy", normal="Academy", bold="AcademyBold", italic="AcademyItalic", boldItalic="AcademyBold")

def styles():
    s = getSampleStyleSheet()
    return {
        "body": ParagraphStyle("Body", fontName="Academy", fontSize=10.2, leading=15.4, textColor=INK, spaceAfter=8.5, allowWidows=False, allowOrphans=False),
        "h1": ParagraphStyle("H1", fontName="AcademyBold", fontSize=23, leading=28, textColor=INK, spaceAfter=15, keepWithNext=True),
        "h2": ParagraphStyle("H2", fontName="AcademyBold", fontSize=17, leading=22, textColor=TEAL, spaceBefore=15, spaceAfter=10, keepWithNext=True),
        "h3": ParagraphStyle("H3", fontName="AcademyBold", fontSize=13.2, leading=18, textColor=INK, spaceBefore=13, spaceAfter=7, keepWithNext=True),
        "cell": ParagraphStyle("Cell", fontName="Academy", fontSize=8.8, leading=12.2, textColor=INK),
        "cellhead": ParagraphStyle("CellHead", fontName="AcademyBold", fontSize=8.8, leading=12.2, textColor=colors.white),
        "caption": ParagraphStyle("Caption", fontName="Academy", fontSize=8.7, leading=12.5, textColor=colors.HexColor("#46616B"), spaceAfter=12),
        "small": ParagraphStyle("Small", fontName="Academy", fontSize=9, leading=13.5, textColor=INK, spaceAfter=8),
        "bullet": ParagraphStyle("Bullet", fontName="Academy", fontSize=10.2, leading=15.4, textColor=INK, leftIndent=12, firstLineIndent=-10, spaceAfter=7, allowWidows=False, allowOrphans=False),
    }

def screenshot(path, lang, title, caption, st, max_height=111*mm):
    p = Path(path)
    if not p.is_file(): return []
    with PILImage.open(p) as i:
        width, height = i.size
        if "A" in i.getbands() and i.getchannel("A").getextrema()[1]==0:
            raise ValueError(f"Fully transparent image is not a usable GUI capture: {p}")
    scale = min(WIDTH/width, max_height/height)
    img = Image(str(p), width=width*scale, height=height*scale, hAlign="CENTER")
    CAPTURED.append({"path": str(p), "sha256": sha(p), "dimensions": [width,height], "manualLanguage": lang,
                     "title": title, "evidence": "Actual application QA capture; not student/experimental validation."})
    return [KeepTogether([Paragraph(inline(title), st["h3"]), img, Spacer(1, 4*mm), Paragraph(inline(caption), st["caption"])])]

def make_table(lines, st):
    raw = [[c.strip() for c in line.strip().strip("|").split("|")] for line in lines]
    raw = [row for row in raw if not all(re.fullmatch(r"[:\- ]+", c) for c in row)]
    if not raw: return []
    n = max(len(row) for row in raw)
    raw = [row + [""]*(n-len(row)) for row in raw]
    if n == 3: widths = [WIDTH*.17, WIDTH*.42, WIDTH*.41]
    elif n == 2: widths = [WIDTH*.32, WIDTH*.68]
    else: widths = [WIDTH/n]*n
    data = [[Paragraph(inline(c), st["cellhead"] if r == 0 else st["cell"]) for c in row] for r,row in enumerate(raw)]
    tab = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    tab.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),TEAL), ("ROWBACKGROUNDS",(0,1),(-1,-1),[PALE, colors.white]),
                            ("VALIGN",(0,0),(-1,-1),"TOP"), ("LEFTPADDING",(0,0),(-1,-1),8),
                            ("RIGHTPADDING",(0,0),(-1,-1),8), ("TOPPADDING",(0,0),(-1,-1),8),
                            ("BOTTOMPADDING",(0,0),(-1,-1),8), ("LINEBELOW",(0,0),(-1,0),.7,TEAL),
                            ("LINEBELOW",(0,1),(-1,-1),.35,colors.HexColor("#DCE7E9"))]))
    return [tab, Spacer(1,5*mm)]

def markdown(text, st, injections=None):
    result=[]; para=[]; lines=text.splitlines(); i=0
    def flush():
        if para: result.append(Paragraph(inline(" ".join(para)),st["body"])); para.clear()
    while i<len(lines):
        line=lines[i].strip()
        if not line: flush(); i+=1; continue
        if line.startswith("|"):
            flush(); block=[]
            while i<len(lines) and lines[i].strip().startswith("|"):block.append(lines[i].strip());i+=1
            result.extend(make_table(block,st));continue
        match=re.match(r"^(#{1,3})\s+(.*)$",line)
        if match:
            flush(); heading=match.group(2);level=len(match.group(1))
            if level==1: result.append(PageBreak())
            header=Paragraph(inline(heading),st["h1" if level==1 else "h2" if level==2 else "h3"])
            figures=list(injections.get(heading,[])) if injections else []
            if figures:
                # Keep the section heading with its first actual capture. ReportLab
                # expands this group before layout, so TOC/bookmarks still see H2.
                first=figures.pop(0)
                children=list(first._content) if isinstance(first,KeepTogether) else [first]
                result.append(KeepTogether([header,*children]))
                result.extend(figures)
            else:result.append(header)
            i+=1;continue
        if line.startswith("- ") or re.match(r"^\d+\. ",line):
            flush(); prefix="• " if line.startswith("- ") else ""
            item=line[2:] if prefix else line
            i+=1
            while i<len(lines) and lines[i].startswith("   ") and not re.match(r"^\s*\d+\. ",lines[i]):item+=" "+lines[i].strip();i+=1
            result.append(Paragraph(inline(prefix+item),st["bullet"]));continue
        para.append(line);i+=1
    flush();return result

def pick(qa_dirs,name):
    for d in reversed(qa_dirs):
        p=d/name
        if p.is_file(): return p
    return None

def pick_language_capture(qa_dirs,name,lang):
    if lang=="en":
        translated=pick(qa_dirs,name.removesuffix(".png")+"-en.png")
        if translated:return translated
    return pick(qa_dirs,name)

def tutor_state(manifest):
    if manifest is None:return "provisional",None
    path=Path(manifest);raw=json.loads(path.read_text(encoding="utf-8"))
    # The application manifest uses PascalCase; accept the earlier camelCase
    # schema without weakening any package provenance or CPU-evaluation gate.
    m={key[0].lower()+key[1:]:value for key,value in raw.items()}
    course_hash=sha(BASE/"content/course.json")
    if not (m.get("fineTuned") is True and m.get("qualityPassed") is True and m.get("courseSha256")==course_hash and m.get("experimentalValidation") is False):
        raise ValueError("Tutor manifest does not establish the declared educational quality gate.")
    if m.get("nativeEvaluationPending") is not False or m.get("nativeEvaluationPassed") is not True:
        raise ValueError("Native CPU tutor evaluation remains pending; keep documentation status provisional.")
    if m.get("answerMode")!="hybrid-reviewed-course-and-local-llm" or m.get("includesLiteralCourseText") is not True:
        raise ValueError("The final teaching package must identify its literal course supplement separately from generation.")
    for name,key in [("training_report.json","trainingReportSha256"),("evaluation_report.json","evaluationReportSha256"),
                     ("native_evaluation_report.json","nativeEvaluationReportSha256")]:
        p=path.parent/name
        if not p.is_file() or sha(p)!=m.get(key):raise ValueError(f"Tutor provenance hash mismatch: {name}")
    native=json.loads((path.parent/"native_evaluation_report.json").read_text(encoding="utf-8"))
    checks=native.get("checks",[])
    if native.get("passed") is not True or not checks or not all(c.get("passed") is True for c in checks):
        raise ValueError("Native evaluation report does not establish a completed hybrid CPU check.")
    model_file=m.get("file", "")
    if not isinstance(model_file,str) or Path(model_file).name!=model_file or not model_file.endswith(".gguf"):
        raise ValueError("Tutor model file is not a scoped GGUF package asset.")
    model=path.parent/model_file
    if not model.is_file() or sha(model)!=m.get("sha256"):
        raise ValueError("Tutor model hash mismatch or missing package model.")
    return "verified",{"manifest":str(path),"sha256":sha(path),"id":m.get("id"),"courseSha256":course_hash,
                       "answerMode":m["answerMode"],"includesLiteralCourseText":True,
                       "nativeReportSha256":m["nativeEvaluationReportSha256"],"nativeChecks":len(checks),
                       "generatedOnlyLimitations":m.get("generatedOnlyLimitations",[]),
                       "note":"Verified hybrid educational package. Generated-only causal omissions are preserved; literal course text is not model generation. Not expert review, measured learning or hardware validation."}

def cover(c,doc,lang,status):
    c.saveState();c.setFillColor(PALE);c.rect(0,0,PAGE_W,PAGE_H,fill=1,stroke=0)
    c.setFillColor(INK);c.rect(0,0,PAGE_W,69*mm,fill=1,stroke=0)
    logo=BASE/"lab/assets/diffatonce-brand.png"
    c.drawImage(ImageReader(str(logo)),19*mm,PAGE_H-65*mm,width=79*mm,height=40*mm,mask="auto",preserveAspectRatio=True)
    c.setFillColor(TEAL);c.setFont("AcademyBold",12);c.drawString(20*mm,PAGE_H-88*mm,"DOSY · ES / EN")
    c.setFillColor(INK);c.setFont("AcademyBold",29);c.drawString(20*mm,PAGE_H-106*mm,"DiffAtOnce Academy")
    c.setFont("Academy",19);c.drawString(20*mm,PAGE_H-121*mm,"Manual de formación" if lang=="es" else "Training manual")
    c.setFont("Academy",13);c.drawString(20*mm,PAGE_H-140*mm,"Aprender a medir. Entender antes de interpretar." if lang=="es" else "Learn to measure. Understand before interpreting.")
    c.setFillColor(ORANGE);c.roundRect(20*mm,PAGE_H-180*mm,169*mm,22*mm,5*mm,fill=1,stroke=0)
    c.setFillColor(colors.white);c.setFont("AcademyBold",12)
    c.drawString(26*mm,PAGE_H-170*mm,"24 módulos · 48 ejemplos · 17 escenas" if lang=="es" else "24 modules · 48 examples · 17 scenes")
    c.setFillColor(colors.white);c.setFont("Academy",11)
    c.drawString(20*mm,49*mm,"Estudiantes y docentes · versión 1.0" if lang=="es" else "Students and teachers · version 1.0")
    c.drawString(20*mm,40*mm,"Simulaciones sintéticas, fuentes y capturas reales de la aplicación." if lang=="es" else "Synthetic simulations, sources and actual application captures.")
    c.setFont("Academy",9)
    label=("Beatrix: paquete local pendiente de verificación" if lang=="es" else "Beatrix: local package pending verification") if status=="provisional" else ("Beatrix: LLM local + texto del curso · paquete híbrido verificado" if lang=="es" else "Beatrix: local LLM + course text · verified hybrid package")
    c.drawString(20*mm,24*mm,label);c.drawString(20*mm,16*mm,"2026-10-05 · diffatonce.com");c.restoreState()

def page(c,doc,lang):
    c.saveState();c.setStrokeColor(colors.HexColor("#D3E2E3"));c.line(19*mm,PAGE_H-16*mm,PAGE_W-19*mm,PAGE_H-16*mm)
    c.setFont("Academy",8.3);c.setFillColor(TEAL);c.drawString(19*mm,PAGE_H-12*mm,"DiffAtOnce Academy")
    c.setFillColor(INK);c.drawRightString(PAGE_W-19*mm,PAGE_H-12*mm,"Manual ES" if lang=="es" else "Manual EN")
    c.setStrokeColor(colors.HexColor("#D3E2E3"));c.line(19*mm,16*mm,PAGE_W-19*mm,16*mm)
    c.setFont("Academy",8);c.drawString(19*mm,11*mm,"Formación · modelos ideales · fuentes verificables" if lang=="es" else "Teaching · ideal models · traceable sources")
    c.drawRightString(PAGE_W-19*mm,11*mm,str(doc.page));c.restoreState()

def build(lang,qa_dirs,status,manifest,st,extra_captures=()):
    guide=DOCS/f"USER_GUIDE_{lang.upper()}.md";text=guide.read_text(encoding="utf-8")
    if status=="verified":
        if lang=="es":
            start=text.index("**Estado de redacción:");end=text.index("Beatrix sirve",start)
            replacement="**Estado del paquete híbrido verificado.** El ajuste local obtuvo 32/32 en el test HF reservado, frente a 21/32 del modelo base. El paquete CPU obtuvo 15/15 en comprobaciones del conjunto **LLM + texto literal del curso**. El modelo CPU solo omitió causas en preguntas abiertas SPEN/TR; esas limitaciones se conservan en sus informes. El bloque literal aporta el mecanismo del curso y no se atribuye al LLM. El manifiesto vincula modelo, informes y versión del curso. Esta evidencia no es validación instrumental, revisión experta independiente ni eficacia educativa medida.\n\nLa aplicación verifica el paquete antes de inferencia. **Guía documental · sin LLM** significa recuperación sin inferencia, incluso ante modelo ausente o fallo; no la presente como generación del modelo.\n\n"
        else:
            start=text.index("**Documentation status,");end=text.index("Beatrix explains",start)
            replacement="**Verified hybrid package status.** Local fine-tuning scored 32/32 on the reserved HF test, compared with 21/32 for the base model. The CPU package passed 15/15 checks of **LLM + literal course text**. Generated-only CPU answers omitted causes in open SPEN/TR questions; those limitations remain in the reports. The literal block supplies the course mechanism and is not attributed to the LLM. Manifest hashes link model, reports and course version. This evidence is not instrument validation, independent expert review or measured educational effectiveness.\n\nThe application verifies the package before inference. **Documentary guide · no LLM** means retrieval without inference, including a missing model or failure; do not present it as model generation.\n\n"
        text=text[:start]+replacement+text[end:]
    toc=TableOfContents();toc.levelStyles=[ParagraphStyle("TOC0",fontName="AcademyBold",fontSize=10.5,leading=16,textColor=INK,spaceBefore=8),
                                        ParagraphStyle("TOC1",fontName="Academy",fontSize=9.8,leading=15,textColor=INK,leftIndent=10,spaceBefore=3)]
    story=[Spacer(1,PAGE_H-60*mm),PageBreak(),Paragraph("Índice" if lang=="es" else "Contents",st["h1"]),toc]
    injections={}
    shots=[
        ("academy-lesson.png",("Cuatro espacios para una misma lección","Four spaces for one lesson"),("La ventana de formación","The learning window"),("Captura real de QA. El progreso24/24 proviene del test automatizado, no de un estudiante evaluado. El panel Beatrix identifica el modo activo; no se ha inventado una respuesta del modelo.","Actual QA capture.24/24 progress comes from an automated test, not an assessed student. The Beatrix panel identifies its active mode; no model answer is fabricated.")),
        ("academy-calibration.png",("1. Pulso de 90°","1. 90° pulse"),("Exp. 1000: 22 / 2 = 11 µs","Exp. 1000: 22 / 2 = 11 µs"),("Captura real del taller nativo P90 con curva firmada: azul marca el máximo de 90° y rojo el primer nulo de 180°. Los 22 µs y 11 µs son valores del ejercicio; no se ha operado el instrumento.","Actual native P90 workshop capture with signed curve: blue marks the 90° maximum and red the first 180° null. 22 µs and 11 µs are exercise values; no instrument was operated.")),
        ("academy-ultrafast.png",("El laboratorio de 17 escenas","The laboratory's 17 scenes"),("Ultrafast en el laboratorio local","Ultrafast in the local laboratory"),("Captura real de la escena calculada. El perfil y las estimaciones provienen de un modelo ideal, no de una adquisición experimental.","Actual computed-scene capture. Profile and estimates come from an ideal model, not an experimental acquisition.")),
        ("academy-source-slides.png",("Consultar diapositivas y métodos","Consult source slides and methods"),("Consulta del workshop original","Original workshop reference viewer"),("Captura real del visor de las81diapositivas aportadas. Imágenes y notas conservan el idioma de la fuente.","Actual viewer capture for the81supplied slides. Images and notes retain their source language.")),
        ("academy-methods.png",("Consultar diapositivas y métodos","Consult source slides and methods"),("Elegir por objetivo y límites","Choose by objective and limits"),("Captura real del catálogo de72registros auditados. Disponibilidad histórica no significa que Academy ejecute todos los métodos.","Actual72-record catalogue capture. Historical availability does not mean Academy executes every method.")),
        ("academy-beatrix.png",("Beatrix: cómo preguntar y leer la respuesta","Beatrix: ask and inspect the response"),("Generación local y texto literal: dos bloques visibles","Local generation and literal text: two visible blocks"),("Captura real de inferencia CPU: la pregunta usa un primer nulo de 18 µs y Beatrix explica P90=9 µs. Es un ejercicio distinto del taller de 22/2=11 µs. El texto LLM y la copia literal del curso aparecen identificados por separado. Las fuentes y el contexto acompañan la respuesta; no se ha calibrado el instrumento.","Actual CPU inference capture: the question uses a first null at 18 µs and Beatrix explains P90=9 µs. This is a different exercise from the 22/2=11 µs workshop. LLM text and the literal course copy are separately labelled. Sources and context accompany the answer; no instrument was calibrated.")),
    ]
    for name,headers,titles,captions in shots:
        path=pick_language_capture(qa_dirs,name,lang)
        if path:
            caption=captions[lang=="en"]
            if "ui-v5" in path.parts:
                caption+=(" La interfaz corresponde a una etapa previa al modelo final; el estado actual del tutor se documenta por separado." if lang=="es" else " This interface comes from a stage before the final model; current tutor status is documented separately.")
            if lang=="en" and name!="academy-ultrafast.png" and not path.name.endswith("-en.png"):
                caption+=" This native UI capture is in Spanish; the course and application also support English."
            injections.setdefault(headers[lang=="en"],[]).extend(screenshot(path,lang,titles[lang=="en"],caption,st))
    story.extend(markdown(text,st,injections))
    story.append(PageBreak());story.append(Paragraph("Recorrido completo de 24 módulos" if lang=="es" else "Complete 24-module learning path",st["h1"]))
    course=json.loads((BASE/"content/course.json").read_text(encoding="utf-8"))
    for m in course["modules"]:
        title=f"{m['order']:02d} · {m['title'][lang]}"
        story.append(KeepTogether([Paragraph(inline(title),st["h3"]),Paragraph(inline(m["objective"][lang]),st["small"]),
                                  Paragraph(inline(("Escena: " if lang=="es" else "Scene: ")+m["scene"]),st["caption"])]))
    # Additional actual final QA captures are included without implying inference.
    extra=[]
    known={row[0] for row in shots}|{row[0].removesuffix(".png")+"-en.png" for row in shots}
    for d in qa_dirs:
        for p in sorted(d.glob("*.png")):
            if p.name in known:continue
            existing=next((i for i,x in enumerate(extra) if x.name==p.name),None)
            if existing is None:extra.append(p)
            else:extra[existing]=p
    for p in extra_captures:
        existing=next((i for i,x in enumerate(extra) if x.name==p.name),None)
        if existing is None:extra.append(p)
        else:extra[existing]=p
    if extra:
        story.append(PageBreak());story.append(Paragraph("Galería de ejemplos y comprobaciones" if lang=="es" else "Example and check gallery",st["h1"]))
        for p in extra:
            title=p.stem.replace("academy-","").replace("-"," ").title()
            caption=("Captura real de QA. Un estado o respuesta visible pertenece a esta ejecución; no implica validación experimental ni prueba de aprendizaje humano." if lang=="es" else "Actual QA capture. Visible state or answer belongs to this run; it does not establish experimental validation or human learning.")
            if p.name=="academy-compact.png":
                title="La misma lección en una ventana compacta" if lang=="es" else "The same lesson in a compact window"
                caption=("Captura real de la ventana compacta. Use las barras de desplazamiento para leer toda la lección; el contexto de Beatrix sigue siendo el módulo activo. El progreso mostrado procede del test de software." if lang=="es" else "Actual compact-window capture in Spanish. Use scrollbars to read the whole lesson; Beatrix retains the active module context. Displayed progress comes from the software test.")
            if p.name=="academy-expanded-lab.png":
                title="Laboratorio ampliado: comparar hipótesis" if lang=="es" else "Expanded laboratory: compare hypotheses"
                caption=("Captura real de WebView2 en la versión final del laboratorio. Los controles permiten variar parámetros, observar la señal y contrastar modelos. Los resultados siguen siendo simulaciones ideales para formación." if lang=="es" else "Actual WebView2 capture from the final laboratory version. Controls let students vary parameters, observe the signal and compare models. Results remain ideal teaching simulations.")
            story.extend(screenshot(p,lang,title,caption,st,145*mm))
            if p.name=="academy-expanded-lab.png":
                explanation=("Cómo leer este ejemplo: el D de entrada es 0.800 ×10⁻⁹ m²/s. El ajuste sin normalización da 1.296; con referencia y b nominal, 0.952; con referencia y b calibrado, 0.787. El sesgo restante es -1.64 %. Compare cada estimación con el valor conocido y explique qué cancela la referencia. La calibración está declarada en la simulación; no ha sido medida en el espectrómetro." if lang=="es" else "How to read this example: input D is 0.800 ×10⁻⁹ m²/s. Fitting without normalization gives 1.296; reference plus nominal b gives 0.952; reference plus calibrated b gives 0.787. Remaining bias is -1.64 %. Compare each estimate with the known value and explain what the reference cancels. Calibration is declared in the simulation; it has not been measured on the spectrometer.")
                story.append(Paragraph(inline(explanation),st["body"]))
    story.append(PageBreak());story.append(Paragraph("Procedencia y reproducibilidad" if lang=="es" else "Provenance and reproducibility",st["h1"]))
    source=json.loads((BASE/"content/source-index.json").read_text(encoding="utf-8"))
    reaudit=json.loads((DOCS/"source-input-reaudit.json").read_text(encoding="utf-8"))
    if not reaudit.get("allTeachingContentChecksPassed") or reaudit["courseSha256"]!=sha(BASE/"content/course.json") or reaudit["sourceIndexSha256"]!=sha(BASE/"content/source-index.json"):
        raise ValueError("The source-content re-audit does not match the frozen teaching artifacts.")
    lines=[("El snapshot extraído y congelado relaciona 81 diapositivas con 24 módulos." if lang=="es" else "The frozen extracted snapshot maps 81 slides to 24 modules."),
           ("PPTX al extraer · SHA-256: " if lang=="es" else "PPTX at extraction · SHA-256: ")+source["input"]["sha256"], "Course SHA-256: "+sha(BASE/"content/course.json"),
           ("PPTX actual · SHA-256: " if lang=="es" else "Current PPTX · SHA-256: ")+reaudit["currentInput"]["sha256"],
           ("El contenedor actual tiene otro hash y 22 bytes más. Las 81 imágenes, notas, texto/descripciones, orden, ocultación y relaciones de medios coinciden con el snapshot. No se atribuye causa ni se afirma identidad binaria. Informe aditivo: source-input-reaudit.json; curso/índice/entrenamiento permanecen congelados." if lang=="es" else "The current container has a different hash and 22 more bytes. All 81 images, notes, text/descriptions, order, hidden flags and media relationships match the snapshot. No cause or binary identity is claimed. Additive report: source-input-reaudit.json; course/index/training remain frozen."),
           ("Las imágenes son capturas reales de aplicación o copias exactas de la fuente. No se inventa una conversación LLM. Los datos históricos siguen atribuidos a su procedencia." if lang=="es" else "Images are actual application captures or exact source copies. No LLM conversation is fabricated. Historical data retain their source attribution."),
           ("Reportes y hashes de las capturas utilizadas: manual-build-manifest.json. Generador: tools/manual_build.py." if lang=="es" else "Capture reports and hashes: manual-build-manifest.json. Generator: tools/manual_build.py."),
           ("Este manual no opera TopSpin, modifica TBO/KK2 ni acredita calibración o identidad. El prototipo UF mantiene NO-GO cuantitativo hasta controles instrumentales." if lang=="es" else "This manual does not operate TopSpin, modify TBO/KK2 or establish calibration or identity. The UF prototype retains quantitative NO-GO pending instrument controls.")]
    if manifest:
        lines.append(("Manifiesto híbrido verificado: " if lang=="es" else "Verified hybrid manifest: ")+manifest["id"]+" · SHA-256: "+manifest["sha256"])
        lines.append(("Informe CPU del conjunto LLM + curso: " if lang=="es" else "CPU report for LLM + course: ")+str(manifest["nativeChecks"])+"/"+str(manifest["nativeChecks"])+" · SHA-256: "+manifest["nativeReportSha256"])
        lines.append("Las omisiones causales del texto generado solo en SPEN/TR permanecen documentadas; el bloque del curso no es generación del modelo." if lang=="es" else "Generated-only causal omissions in SPEN/TR remain documented; the course block is not model generation.")
    for line in lines:story.append(Paragraph(inline(line),st["small"]))
    output=DOCS/f"MANUAL_{lang.upper()}.pdf"
    doc=ManualDoc(str(output),pagesize=A4,rightMargin=19*mm,leftMargin=19*mm,topMargin=23*mm,bottomMargin=23*mm,
                          title="DiffAtOnce Academy - "+("Manual de formación" if lang=="es" else "Training manual"),author="DiffAtOnce Academy",pageCompression=1)
    doc.multiBuild(story,onFirstPage=lambda c,d:cover(c,d,lang,status),onLaterPages=lambda c,d:page(c,d,lang))
    return output

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--qa",action="append",type=Path);parser.add_argument("--manifest",type=Path)
    parser.add_argument("--capture",action="append",type=Path,default=[],help="Add a verified actual PNG without selecting other captures in its directory.")
    args=parser.parse_args();qa_dirs=args.qa or [BASE/"qa/ui-v5"]
    for d in qa_dirs:
        if not d.is_dir():raise FileNotFoundError(d)
    for p in args.capture:
        if not p.is_file() or p.suffix.lower()!=".png":raise ValueError(f"Missing or unsupported actual capture: {p}")
    register_fonts();st=styles();status,manifest=tutor_state(args.manifest)
    outputs=[build(lang,qa_dirs,status,manifest,st,args.capture) for lang in ("es","en")]
    report={"version":"1.0.0","date":"2026-10-05","tutorStatus":status,"tutorManifest":manifest,
            "qaDirectories":[str(p.resolve()) for p in qa_dirs],"screenshots":CAPTURED,
            "explicitCaptures":[str(p.resolve()) for p in args.capture],
            "outputs":[{"path":str(p.resolve()),"bytes":p.stat().st_size,"sha256":sha(p)} for p in outputs],
            "evidenceBoundary":"Actual UI captures and teaching documentation. Not hardware validation, expert review or measured student learning."}
    (DOCS/"manual-build-manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report["outputs"],indent=2))

if __name__=="__main__":main()
