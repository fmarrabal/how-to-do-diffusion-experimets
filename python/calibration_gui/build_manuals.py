"""Create bilingual, illustrated PDF manuals from verified GUI view renders."""
from pathlib import Path
import json, re
from html import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, A3, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
    Spacer, PageBreak, NextPageTemplate, Image, KeepTogether, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents
from PIL import Image as PILImage

HERE=Path(__file__).resolve().parent
OUTPUT=HERE/'output'/'pdf'
BLUE=colors.HexColor('#0065d2'); NAVY=colors.HexColor('#102542'); GRAY=colors.HexColor('#546374')
FONTS=Path('C:/Windows/Fonts')
for name,file in [('Body','segoeui.ttf'),('Bold','segoeuib.ttf'),('Mono','consola.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONTS/file)))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Body',boldItalic='Bold')

STYLES={
'body':ParagraphStyle('body',fontName='Body',fontSize=10.6,leading=15,textColor=NAVY,spaceAfter=9),
'lead':ParagraphStyle('lead',fontName='Body',fontSize=11.5,leading=16.5,textColor=GRAY,spaceAfter=16),
'title':ParagraphStyle('title',fontName='Bold',fontSize=23,leading=28,textColor=NAVY,spaceAfter=18),
'heading':ParagraphStyle('heading',fontName='Bold',fontSize=19,leading=23,textColor=NAVY,spaceAfter=15),
'small':ParagraphStyle('small',fontName='Body',fontSize=8.5,leading=12,textColor=GRAY,spaceAfter=8),
'note':ParagraphStyle('note',fontName='Body',fontSize=10,leading=14,textColor=GRAY,backColor=colors.HexColor('#edf4fc'),borderPadding=10,spaceBefore=6,spaceAfter=13),
'code':ParagraphStyle('code',fontName='Mono',fontSize=8.7,leading=13,textColor=BLUE,spaceAfter=12),
'figure':ParagraphStyle('figure',fontName='Bold',fontSize=20,leading=25,textColor=NAVY,spaceAfter=14),
}

def clean(text):
    return text.replace('\u2011','-').replace('\u2013','-').replace('\u2014',' - ')
def para(text,style='body'):
    return Paragraph(escape(clean(text)).replace('\n','<br/>'),STYLES[style])

class Manual(BaseDocTemplate):
    def __init__(self,path,lang):
        self.manual_language=lang;self.bookmarks=[]
        super().__init__(str(path),pagesize=A4,leftMargin=44,rightMargin=44,topMargin=56,bottomMargin=44,
            title='DiffAtOnce - '+('Manual de calibración' if lang=='es' else 'Calibration manual'),author='Francisco Manuel Arrabal-Campos',
            subject='Bilingual Python/Jython GUI for TopSpin P1 and DOSY calibration',pageCompression=1)
        portrait=Frame(44,44,A4[0]-88,A4[1]-100,id='text',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
        sz=landscape(A3)
        screen=Frame(36,40,sz[0]-72,sz[1]-96,id='screen',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
        self.addPageTemplates([PageTemplate(id='portrait',frames=[portrait],pagesize=A4,onPage=self.decorate),
            PageTemplate(id='screen',frames=[screen],pagesize=sz,onPage=self.decorate)])
    def decorate(self,canvas,doc):
        w,h=canvas._pagesize
        canvas.saveState();canvas.setFillColor(NAVY);canvas.rect(0,h-33,w,33,fill=1,stroke=0)
        canvas.setFont('Bold',9);canvas.setFillColor(colors.white);canvas.drawString(36,h-21,'DiffAtOnce  |  '+('CALIBRACIÓN DEL ESPECTRÓMETRO' if self.manual_language=='es' else 'SPECTROMETER CALIBRATION'))
        canvas.setFont('Body',8);canvas.setFillColor(GRAY);canvas.drawString(36,23,'2026-10-03  |  v1.0  |  '+('Español' if self.manual_language=='es' else 'English'))
        canvas.drawRightString(w-36,23,str(doc.page));canvas.restoreState()
    def afterFlowable(self,flowable):
        if getattr(flowable,'toc_title',None):
            key='section_'+flowable.toc_key
            self.canv.bookmarkPage(key);self.canv.addOutlineEntry(flowable.toc_title,key,0,False)
            self.notify('TOCEntry',(0,flowable.toc_title,self.page,key));self.bookmarks.append(key)

def screenshot_flow(section,lang):
    ident=section['screenshot']['id'];path=HERE/'screenshots'/(ident+'_'+lang+'.png')
    if not path.is_file():raise FileNotFoundError(path)
    w,h=PILImage.open(path).size
    area=landscape(A3)
    width=min(area[0]-84,(area[1]-240)*w/h);height=width*h/w
    return [NextPageTemplate('screen'),PageBreak(),para(section['title'][lang],'figure'),
        Image(str(path),width=width,height=height),Spacer(1,12),
        para(section['screenshot']['caption'][lang],'body'),
        para('Render de la interfaz Swing real en modo Demo; datos sintéticos y sin adquisición experimental.' if lang=='es' else
             'Render of the real Swing interface in Demo mode; synthetic data and no experimental acquisition.','small'),
        NextPageTemplate('portrait'),PageBreak()]

def build(lang,content):
    path=OUTPUT/('Manual_Calibracion_Espectrometro_ES.pdf' if lang=='es' else 'Spectrometer_Calibration_Manual_EN.pdf')
    doc=Manual(path,lang);story=[]
    meta=content['metadata']
    story += [Spacer(1,28),para('DiffAtOnce','heading'),para(meta['title'][lang],'title'),para(meta['subtitle'][lang],'lead'),
        Image(str(HERE/'screenshots'/('overview_'+lang+'.png')),width=A4[0]-88,height=(A4[0]-88)*881/1364),Spacer(1,17),
        para(meta['scope'][lang]),para(meta['screenshot_policy'][lang],'note'),
        para('Python / Jython 2.7 + Swing · TopSpin 3 · English / Español','small'),PageBreak()]
    story += [para('Contenido' if lang=='es' else 'Contents','heading')]
    toc=TableOfContents();toc.levelStyles=[ParagraphStyle('toc',fontName='Body',fontSize=11,leading=22,textColor=NAVY,leftIndent=0)]
    story += [toc,Spacer(1,30),para('Lectura recomendada' if lang=='es' else 'Recommended reading','heading'),
        para('Primero sigue Preparación y P1. Después revisa el patrón DOSY, los parámetros de la secuencia y la atenuación. Las páginas grandes de figuras permiten ampliar la interfaz sin perder legibilidad.' if lang=='es' else
             'Start with Preparation and P1. Then review the DOSY reference, sequence parameters and attenuation. Large figure pages let you zoom into the interface while keeping it readable.'),
        para('Inicio en TopSpin' if lang=='es' else 'TopSpin launch','body'),para('xpy spectrometer_calibration_gui.py','code'),
        para('Demostración local' if lang=='es' else 'Local demonstration','body'),para('.\\run_demo.ps1 -TopSpinRoot C:\\Bruker\\TopSpin3.8.0','code'),PageBreak()]
    for number,section in enumerate(content['sections'],1):
        heading=para('%02d  %s'%(number,section['title'][lang]),'heading');heading.toc_title=section['title'][lang];heading.toc_key=section['id']
        story += [heading,para(section['lead'][lang],'lead')]
        for i,text in enumerate(section['steps'][lang],1):story.append(para('%d.  %s'%(i,text)))
        for note in section.get('notes',{}).get(lang,[]):story.append(para(note,'note'))
        story += screenshot_flow(section,lang)
    story += [para('Instalación y comprobación final' if lang=='es' else 'Installation and final check','heading')]
    extra_es=[
        'El ZIP contiene un script autónomo para TopSpin: dist/spectrometer_calibration_gui.py. Copia ese archivo a <TopSpin>/exp/stan/nmr/py/user usando el procedimiento del laboratorio; conserva las versiones anteriores. Después ejecuta xpy spectrometer_calibration_gui.py.',
        'También puedes abrir la copia del workspace usando xpy seguido de su ruta absoluta, si tu instalación admite rutas en xpy. No cambies a un intérprete Python 3 externo esperando que importe TopCmds.',
        'run_demo.ps1 usa Java y Jython de una instalación existente. Para TopSpin 3.6.4 cambia -TopSpinRoot. El lanzador busca el archivo jython*.jar instalado; no descarga ni instala dependencias.',
        'La GUI devuelve el trabajo a un CmdThread mediante EXEC_PYSCRIPT. Si el despachador no alcanza la instancia de la GUI, se detiene. Verifica esta comunicación con Leer dataset actual antes de usar cualquier adquisición.',
        'Pruebas de software: 51 casos aprobados en Jython 2.7.2 (18 del controlador y 33 de preparación instrumental); CPython aprobó 41 y omitió los 10 específicos de Java. Se utilizó una API simulada. Las capturas se generaron en la interfaz Swing real leyendo y ajustando archivos Bruker sintéticos. P90 = 11 µs y b100 = 2 × 10^9 s/m².',
        'En la GUI fuente anterior a esta edición pública se verificaron el lanzamiento y una lectura CURDATA mediante callback en CmdThread dentro de TopSpin 3.8.0, sin comandos de hardware ni cambios de parámetros. Estas comprobaciones no validan adquisición real ni TopSpin 3.6.4. El piloto debe confirmar comunicación, rc de ZG/EFP y cada comando de preparación habilitado, preservación de plantillas, fase fija, límites RF y calidad experimental.',
    ]
    extra_en=[
        'The ZIP includes one self-contained TopSpin script: dist/spectrometer_calibration_gui.py. Copy it to <TopSpin>/exp/stan/nmr/py/user using the laboratory procedure, retaining earlier versions. Then run xpy spectrometer_calibration_gui.py.',
        'You can also launch the workspace copy using xpy followed by its absolute path, if your installation accepts paths in xpy. Do not switch to an external Python 3 interpreter expecting it to import TopCmds.',
        'run_demo.ps1 uses Java and Jython from an existing installation. Set -TopSpinRoot for TopSpin 3.6.4. The launcher locates the installed jython*.jar; it downloads and installs no dependencies.',
        'The GUI dispatches work to a CmdThread through EXEC_PYSCRIPT. If the dispatcher cannot reach the GUI instance, it stops. Verify this communication using Read current dataset before any acquisition.',
        'Software tests: 51 cases passed in Jython 2.7.2 (18 controller and 33 instrument-preparation cases); CPython passed 41 and skipped the 10 Java-specific cases. Tests used a simulated API. Figures were rendered by the real Swing interface while reading and fitting synthetic Bruker files. P90 = 11 µs and b100 = 2 × 10^9 s/m².',
        'In the source GUI before this public edition, launch and a CURDATA read through a callback on CmdThread were verified inside TopSpin 3.8.0, with no hardware commands or parameter writes. These checks do not validate real acquisition or TopSpin 3.6.4. Commissioning must confirm communication, ZG/EFP return status and each enabled preparation command, template preservation, fixed phase, RF limits and experimental quality.',
    ]
    extra_es.append('Edición pública: las vistas se han vuelto a renderizar con la GUI real y rutas de visualización públicas. Los datos sintéticos y los ajustes no cambian. Los recibos nativos eliminan nombres y rutas privados. El bundle público reconstruido no se ha validado en un instrumento.')
    extra_en.append('Public edition: views were rerendered from the actual GUI using public display paths. Synthetic data and fits are unchanged. Native receipts redact private names and paths. The rebuilt public bundle has not been validated on an instrument.')
    for text in (extra_es if lang=='es' else extra_en):story.append(para(text))
    story += [PageBreak(),para('Fuentes y archivos de referencia' if lang=='es' else 'Sources and reference files','heading')]
    for source in content['sources']:
        if source['id']=='gui_contract':continue
        title=source.get('title_es',source['title']) if lang=='es' else source['title'];link=source.get('url') or source.get('path') or source.get('local_path')
        story.append(para(title,'body'))
        if link:story.append(para(link,'small'))
    story += [para('Documentación instrumental adicional' if lang=='es' else 'Additional instrument documentation','body'),
        para('Bruker python.pdf pp. 7-8, 20-21; acquisition-reference.pdf pp. 114-116, 199-201; Atma.pdf pp. 19-20; topshim.pdf pp. 5-9. Documentación local consultada en TopSpin 3.8.0. Comprueba comandos y hardware en el sistema de destino.' if lang=='es' else 'Bruker python.pdf pp. 7-8, 20-21; acquisition-reference.pdf pp. 114-116, 199-201; Atma.pdf pp. 19-20; topshim.pdf pp. 5-9. Local documentation inspected from TopSpin 3.8.0. Confirm commands and hardware on the target system.','small')]
    doc.multiBuild(story)
    return path

def main():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    content=json.loads((HERE/'manual_content.json').read_text(encoding='utf-8'))
    for lang in ('es','en'):print(build(lang,content))

if __name__=='__main__':main()
