# -*- coding: utf-8 -*-
"""Bilingual Swing GUI for the TopSpin 3 Jython runtime.

The GUI never calls TopCmds from a Swing listener. Instrument jobs are dispatched
back to a TopSpin command thread; Swing updates use the Java event queue.
"""
from __future__ import division, unicode_literals
import io
import json
import math
import os
import sys
import threading
import traceback
import uuid
from java.awt.event import WindowAdapter
from java.awt import BorderLayout, Color, Dimension, Font, FlowLayout, GridLayout, RenderingHints
from java.lang import Runnable, Throwable
from javax.swing import (JFrame, JPanel, JLabel, JButton, JComboBox, JTextField,
    JTextArea, JScrollPane, JTabbedPane, JTable, JCheckBox, JFileChooser,
    JOptionPane, JProgressBar, SwingUtilities, BorderFactory, BoxLayout, UIManager, Timer)
from javax.swing.table import DefaultTableModel
from calibration_workflow import WorkflowController
import instrument_setup

VERSION = '1.0'
NAVY = Color(16, 37, 66)
BLUE = Color(0, 101, 210)
TEAL = Color(0, 130, 120)
BG = Color(240, 244, 249)
WHITE = Color.WHITE
MUTED = Color(84, 99, 116)

# Semantic keys are shared by both languages. Technical parameter names stay
# identical so a printed plan can be compared with the Bruker parameter editor.
TEXT = {
'title': ('Spectrometer Calibration', 'Calibración del espectrómetro'),
'subtitle': ('From instrument preparation to reviewed P1 and DOSY results', 'De la preparación del equipo a resultados revisados de P1 y DOSY'),
'home': ('01  Overview', '01  Inicio'), 'setup': ('02  Instrument', '02  Equipo'),
'p1': ('03  Pulse P1', '03  Pulso P1'), 'dosy': ('04  DOSY gradient', '04  Gradiente DOSY'),
'run': ('05  Run & results', '05  Ejecución y resultados'),
'demo': ('DEMONSTRATION · simulated data · no instrument connection', 'DEMOSTRACIÓN · datos simulados · sin conexión al equipo'),
'live': ('TOPSPIN CONNECTION · commands require an operator start', 'CONEXIÓN TOPSPIN · los comandos requieren inicio del operador'),
'journey': ('One workflow. Every decision recorded.', 'Un flujo de trabajo. Cada decisión registrada.'),
'homebody': ('Prepare the instrument, calibrate the 90° pulse, then measure a reference gradient ramp. Review signed integrals, attenuation and residuals before applying a result.', 'Prepara el equipo, calibra el pulso de 90° y mide una rampa de gradientes del patrón. Revisa las integrales con signo, la atenuación y los residuos antes de aplicar un resultado.'),
'step1': ('Prepare', 'Preparar'), 'step2': ('Calibrate P1', 'Calibrar P1'),
'step3': ('Calibrate DOSY', 'Calibrar DOSY'), 'step4': ('Review & export', 'Revisar y exportar'),
'card1': ('Lock, tune/match, shim and thermal equilibration depend on the installed hardware.', 'Lock, sintonía, ajuste, shim y equilibrio térmico dependen del hardware instalado.'),
'card2': ('A signed nutation series identifies P90. A 22 µs first null gives approximately 11 µs.', 'Una serie de nutación con signo identifica P90. Un primer nulo de 22 µs da aproximadamente 11 µs.'),
'card3': ('Integrate one reference signal and fit its attenuation at fixed sequence and timings.', 'Integra una señal del patrón y ajusta su atenuación con secuencia y tiempos fijos.'),
'card4': ('Inspect residuals. Save the plan, CSV and report. Copy a reviewed P1 to a new EXPNO.', 'Inspecciona los residuos. Guarda plan, CSV e informe. Copia un P1 revisado a un EXPNO nuevo.'),
'scope': ('Scope of this version', 'Alcance de esta versión'),
'scopebody': ('Automates channel-1 P1 and a 1D DOSY reference series. It does not certify every probe/channel or replace service calibration. Hardware-dependent preparation steps are enabled individually. Real-instrument commissioning is still required.', 'Automatiza P1 del canal 1 y una serie 1D del patrón DOSY. No certifica cada sonda o canal ni sustituye la calibración de servicio. Los pasos de preparación dependen del equipo y se habilitan por separado. Falta la puesta en marcha en el espectrómetro.'),
'openp1': ('Configure P1', 'Configurar P1'), 'opendosy': ('Configure DOSY', 'Configurar DOSY'),
'save': ('Save settings', 'Guardar ajustes'), 'load': ('Load settings', 'Cargar ajustes'),
'context': ('Read current dataset', 'Leer dataset actual'), 'ready': ('Ready to configure', 'Listo para configurar'),
'dataset': ('Dataset name', 'Nombre del dataset'), 'root': ('Data directory', 'Directorio de datos'),
'report': ('Reports directory', 'Directorio de informes'), 'procno': ('PROCNO', 'PROCNO'),
'template': ('Template EXPNO', 'EXPNO de plantilla'), 'first': ('First new EXPNO', 'Primer EXPNO nuevo'),
'valuesp1': ('Pulse lengths (µs, comma separated)', 'Duraciones de pulso (µs, separadas por coma)'),
'valuesg': ('GPZ6 (% maximum, comma separated)', 'GPZ6 (% máximo, separados por coma)'),
'low': ('Integration lower limit (ppm)', 'Límite inferior de integración (ppm)'),
'high': ('Integration upper limit (ppm)', 'Límite superior de integración (ppm)'),
'p90min': ('P90 search minimum (µs)', 'Mínimo de búsqueda P90 (µs)'),
'p90max': ('P90 search maximum (µs)', 'Máximo de búsqueda P90 (µs)'),
'dref': ('D reference (10⁻⁹ m²/s)', 'D de referencia (10⁻⁹ m²/s)'),
'tref': ('Reference temperature (K)', 'Temperatura de referencia (K)'),
'ref': ('Reference / solvent / source', 'Patrón / disolvente / fuente'),
'span': ('Maximum recorded TE span (K)', 'Variación máxima de TE registrado (K)'),
'tdiff': ('Maximum TE-to-reference difference (K)', 'Diferencia máxima TE-referencia (K)'),
'program': ('Expected pulse program', 'Secuencia de pulsos esperada'),
'priorb': ('Previous b100 (s/m²; 0 = none)', 'b100 anterior (s/m²; 0 = ninguno)'),
'p1guide': ('Keep the RF power, RG, NS, D1 and phase fixed. Use zg and an isolated signal. Include the positive maximum, first null and negative signal. Do not autophase each spectrum.', 'Mantén fijos potencia RF, RG, NS, D1 y fase. Usa zg y una señal aislada. Incluye máximo positivo, primer nulo y señal negativa. No ajustes automáticamente la fase de cada espectro.'),
'p1example': ('Your example: template 1000 → first null P180 = 22 µs → P90 = 11 µs. The fitted value remains specific to that RF power and channel.', 'Tu ejemplo: plantilla 1000 → primer nulo P180 = 22 µs → P90 = 11 µs. El valor ajustado corresponde a esa potencia RF y a ese canal.'),
'dosyguide': ('Use a known D reference at the stated temperature. The entire series uses one pulse sequence, gradient shape, P30 and D20. The fit calibrates b100 empirically; another Δ requires its own calibration or a verified sequence model.', 'Usa un D conocido del patrón a la temperatura indicada. Toda la serie usa una secuencia, forma de gradiente, P30 y D20. El ajuste calibra b100 empíricamente; otro Δ requiere su calibración o un modelo verificado de la secuencia.'),
'sequence': ('Sequence & timing', 'Secuencia y tiempos'),
'sequencebody': ('P30, D20, D16, D5 and double-stimulated-echo timings are inherited from the reviewed template. Inspect its pulse program. Never substitute the rectangular PGSE equation without checking the sequence.', 'P30, D20, D16, D5 y los tiempos de doble eco estimulado se heredan de la plantilla revisada. Inspecciona su pulse program. No sustituyas la ecuación de PGSE rectangular sin comprobar la secuencia.'),
'preview': ('Preview plan', 'Revisar plan'), 'prepare': ('Prepare series', 'Preparar serie'),
'acquire': ('Acquire and fit', 'Adquirir y ajustar'),
'analyze': ('Analyze series', 'Analizar serie'),
'stop': ('Stop after point', 'Parar tras punto'),
'stopnote': ('Stop is cooperative. A running acquisition is allowed to finish; no new point starts afterwards.', 'La parada es cooperativa. La adquisición en curso termina; después no empieza otro punto.'),
'workflow': ('Active calibration', 'Calibración activa'), 'plan': ('Reviewed experiment plan', 'Plan de experimentos revisado'),
'log': ('Execution journal', 'Registro de ejecución'), 'results': ('Fit and residuals', 'Ajuste y residuos'),
'resultempty': ('Run or analyze a series to see the measured curve and its residuals.', 'Ejecuta o analiza una serie para ver la curva medida y sus residuos.'),
'point': ('Point', 'Punto'), 'parameter': ('Parameter', 'Parámetro'), 'value': ('Value', 'Valor'),
'apply': ('Apply P1 to new EXPNO', 'Aplicar P1 a EXPNO nuevo'),
'review': ('I reviewed spectra, fit, RF power and residuals', 'He revisado espectros, ajuste, potencia RF y residuos'),
'target': ('New destination EXPNO', 'EXPNO nuevo de destino'), 'reports': ('Open reports', 'Abrir informes'),
'instrumenttitle': ('Prepare the measurement conditions first', 'Primero prepara las condiciones de medida'),
'instrumentbody': ('Enable only capabilities present on your spectrometer. Each command is started separately. Command completion does not prove that tuning, shimming or thermal equilibrium is acceptable.', 'Habilita solo capacidades presentes en tu espectrómetro. Cada comando se inicia por separado. Que un comando termine no prueba que sintonía, shim o equilibrio térmico sean adecuados.'),
'enablelock': ('Lock command available; solvent configured', 'Lock disponible; disolvente configurado'),
'enableatma': ('Automatic tune/match hardware available', 'Hardware automático de sintonía y ajuste disponible'),
'enableshim': ('TopShim configured for this probe', 'TopShim configurado para esta sonda'),
'lock': ('Run LOCK', 'Ejecutar LOCK'), 'atma': ('Run ATMA', 'Ejecutar ATMA'),
'shim': ('Run TOPSHIM', 'Ejecutar TOPSHIM'),
'gates': ('Operator checks before acquisition', 'Comprobaciones antes de adquirir'),
'checksample': ('Correct sample, probe, channel and RF power', 'Muestra, sonda, canal y potencia RF correctos'),
'checktemp': ('Temperature equilibrated and reference D(T) reviewed', 'Temperatura equilibrada y D(T) del patrón revisado'),
'checkphase': ('Template phase, integration region and receiver gain reviewed', 'Fase de plantilla, región de integración y ganancia revisadas'),
'checkpilot': ('Command status and template behavior commissioned on this instrument', 'Estado de comandos y plantilla comprobados en este equipo'),
'tempnote': ('TE is saved metadata, not independent sample thermometry. Temperature-controller read/set operations are not issued on original templates.', 'TE es metadato guardado, no termometría independiente de la muestra. No se consulta ni cambia el controlador sobre las plantillas originales.'),
'saved': ('Settings saved.', 'Ajustes guardados.'), 'loaded': ('Settings loaded.', 'Ajustes cargados.'),
'busy': ('A job is already running.', 'Ya hay un trabajo en curso.'),
'checkrequired': ('Complete the four operator checks in Instrument before acquisition.', 'Completa las cuatro comprobaciones de Equipo antes de adquirir.'),
'error': ('Action stopped', 'Acción detenida'), 'success': ('Action completed', 'Acción completada'),
'simulation': ('SIMULATED RESULT', 'RESULTADO SIMULADO'), 'candidate': ('REVIEW CANDIDATE', 'PROPUESTA PARA REVISIÓN'),
'nosource': ('Select a report directory first.', 'Selecciona antes un directorio de informes.'),
'fit': ('Fit', 'Ajuste'), 'residual': ('Residual', 'Residuo'),
'blankref': ('EDIT: standard, solvent and primary D(T) source', 'EDITAR: patrón, disolvente y fuente primaria de D(T)'),
'invalidnumber': ('Enter a finite number for ', 'Introduce un número finito para '),
'nomode': ('Select P1 or DOSY.', 'Selecciona P1 o DOSY.'),
'resultcopied': ('P1 copied to a new parameter-only experiment.', 'P1 copiado a un experimento nuevo solo de parámetros.'),
'working': ('Working…', 'En curso…'), 'stopped': ('Stop requested; finishing current point.', 'Parada solicitada; terminando el punto actual.'),
'workcopy': ('Prepare copy', 'Preparar copia'),
'workexp': ('Preparation copy EXPNO', 'EXPNO de copia de preparación'),
'enabletemp': ('Temperature controller available', 'Controlador de temperatura disponible'),
'readtemp': ('Read temperature', 'Leer temperatura'),
'settemp': ('Set temperature', 'Cambiar consigna'),
'tempvalue': ('New demand temperature (K)', 'Nueva consigna de temperatura (K)'),
'templimits': ('Probe/controller temperature limits (K)', 'Límites térmicos de sonda/controlador (K)'),
'lockvalid': ('Lock established and reviewed before TopShim', 'Lock establecido y revisado antes de TopShim'),
'workfirst': ('Create a preparation copy before running instrument commands.', 'Crea una copia de preparación antes de ejecutar comandos del equipo.'),
'range_to': ('to', 'hasta'),
'signed': ('Signed integral', 'Integral con signo'),
'collision': ('Destination EXPNO already exists. Choose a new range: ', 'Ya existe el EXPNO de destino. Elige otro intervalo: '),
}

class Task(Runnable):
    def __init__(self, fn): self.fn = fn
    def run(self): self.fn()

class Closing(WindowAdapter):
    def __init__(self,app):self.app=app
    def windowClosing(self,event):
        if self.app.running:self.app.close_pending=True;self.app.stop()
        else:self.app.frame.dispose()

def edt(fn):
    if SwingUtilities.isEventDispatchThread(): fn()
    else: SwingUtilities.invokeLater(Task(fn))

def label(text, size=14, bold=False, color=NAVY):
    c = JLabel(text)
    c.setFont(Font('Segoe UI', Font.BOLD if bold else Font.PLAIN, size))
    c.setForeground(color)
    c.setAlignmentX(0.0)
    return c

def paragraph(text, width=420, color='#546374'):
    c=JTextArea(text)
    c.setEditable(False);c.setLineWrap(True);c.setWrapStyleWord(True)
    c.setFont(Font('Segoe UI',Font.PLAIN,14));c.setForeground(MUTED);c.setOpaque(False)
    c.setAlignmentX(0.0)
    lines=max(2,int(math.ceil(len(text)/(width/7.5))))
    c.setPreferredSize(Dimension(width,lines*22+8));c.setMaximumSize(Dimension(width,lines*22+8))
    return c

def box(axis=BoxLayout.Y_AXIS, background=WHITE, pad=16):
    p = JPanel()
    p.setLayout(BoxLayout(p, axis))
    p.setBackground(background)
    p.setAlignmentX(0.0)
    p.setBorder(BorderFactory.createEmptyBorder(pad, pad, pad, pad))
    return p

def align_columns(component):
    if isinstance(component,JPanel) and isinstance(component.getLayout(),BoxLayout):
        for child in component.getComponents():
            if hasattr(child,'setAlignmentX'):child.setAlignmentX(0.0)
    if hasattr(component,'getComponents'):
        for child in component.getComponents():align_columns(child)

class CurvePanel(JPanel):
    """Paint the actual backend arrays, with a separate residual strip."""
    def __init__(self, app):
        self.app, self.plot = app, None
        self.setBackground(WHITE)
        self.setPreferredSize(Dimension(650, 260))
    def paintComponent(self, g):
        g.setColor(self.getBackground());g.fillRect(0,0,self.getWidth(),self.getHeight())
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)
        w, h = self.getWidth(), self.getHeight()
        if not self.plot:
            g.setColor(MUTED); g.drawString(self.app.t('resultempty'), 20, 35); return
        p = self.plot
        x, y, fit, res = p['x'], p['observed'], p['fitted'], p['residuals']
        if len(x) < 2: return
        left, right, top, bot = 55, w-30, 18, int(h*.61)
        xmin, xmax = min(x), max(x)
        ymin, ymax = min(y+fit+[0]), max(y+fit+[0])
        if ymax == ymin: ymax = ymin+1
        def xx(v): return int(left+(v-xmin)/(xmax-xmin)*(right-left))
        def yy(v): return int(bot-(v-ymin)/(ymax-ymin)*(bot-top))
        g.setColor(Color(223, 231, 239)); g.drawRect(left, top, right-left, bot-top)
        g.drawLine(left, yy(0), right, yy(0))
        if p.get('p90'):
            g.setColor(Color(210,220,231))
            for multiplier,name in ((1,'P90'),(2,'P180')):
                v=multiplier*p['p90']
                if xmin<v<xmax:
                    g.drawLine(xx(v),top,xx(v),bot);g.setColor(MUTED);g.drawString(name,xx(v)+3,top+12);g.setColor(Color(210,220,231))
        g.setColor(TEAL)
        for i in range(len(x)-1): g.drawLine(xx(x[i]), yy(fit[i]), xx(x[i+1]), yy(fit[i+1]))
        g.setColor(BLUE)
        for a,b in zip(x,y): g.fillOval(xx(a)-4, yy(b)-4, 8, 8)
        g.setFont(Font('Segoe UI', Font.PLAIN, 11)); g.setColor(MUTED)
        g.drawString('%.3g' % ymax, 4, top+5); g.drawString('%.3g' % ymin, 4, bot)
        g.drawString('%.3g' % xmin, left, bot+16); g.drawString('%.3g' % xmax, right-25, bot+16)
        g.drawString(p.get('x_label',''), int(w*.40), bot+16)
        rtop, rbot = bot+37, h-22
        maxr = max([abs(v) for v in res]+[1e-12])*1.15
        zero = int((rtop+rbot)/2)
        g.setColor(Color(223,231,239)); g.drawRect(left,rtop,right-left,rbot-rtop); g.drawLine(left,zero,right,zero)
        g.setColor(MUTED); g.drawString(self.app.t('residual'),4,zero)
        g.drawString('±%.2g' % maxr,left+4,rtop+12)
        g.setColor(BLUE)
        for a,b in zip(x,res): g.fillOval(xx(a)-3, int(zero-b/maxr*(rbot-rtop)/2)-3, 6, 6)

class CalibrationApp(object):
    def __init__(self, api=None, demo=False):
        self.api, self.demo, self.lang = api, bool(demo), 'en'
        self.controller = WorkflowController(api=api, demo=demo)
        self.fields, self.bindings, self.pages, self.checks = {}, [], [], {}
        self.mode, self.result, self.job, self.running = 'p1', None, None, False
        self.outputs={};self.close_pending=False
        self.stop_event = threading.Event()
        self.setup_config = instrument_setup.default_setup_config()
        self.frame = JFrame('DiffAtOnce | Spectrometer Calibration')
        self.frame.setDefaultCloseOperation(JFrame.DO_NOTHING_ON_CLOSE)
        self.frame.addWindowListener(Closing(self))
        self.frame.setMinimumSize(Dimension(1100, 760))
        self.frame.setSize(1380, 920)
        self.frame.setLocationRelativeTo(None)
        outer = JPanel(BorderLayout(0, 0)); outer.setBackground(BG)
        header = JPanel(BorderLayout()); header.setBackground(NAVY)
        header.setBorder(BorderFactory.createEmptyBorder(18,24,18,24))
        headings = box(background=NAVY,pad=0)
        headings.add(label('DiffAtOnce',26,True,WHITE))
        self.subtitle = label('',14,False,Color(194,211,233)); headings.add(self.subtitle)
        header.add(headings,BorderLayout.CENTER)
        self.language = JComboBox(['English','Español'])
        self.language.setPreferredSize(Dimension(130,34))
        self.language.addActionListener(lambda e:self.change_language())
        header.add(self.language,BorderLayout.EAST)
        outer.add(header,BorderLayout.NORTH)
        content = JPanel(BorderLayout(12,12)); content.setBackground(BG)
        content.setBorder(BorderFactory.createEmptyBorder(12,18,12,18))
        banner = JPanel(FlowLayout(FlowLayout.LEFT,12,8)); banner.setBackground(Color(224,242,239) if demo else Color(229,239,253))
        self.banner = label('',13,True,TEAL if demo else BLUE); banner.add(self.banner)
        content.add(banner,BorderLayout.NORTH)
        self.tabs = JTabbedPane(); self.tabs.setFont(Font('Segoe UI',Font.BOLD,14))
        content.add(self.tabs,BorderLayout.CENTER)
        self.home_page(); self.setup_page(); self.p1_page(); self.dosy_page(); self.run_page()
        for key,p in self.pages:
            align_columns(p)
            pane=JScrollPane(p);pane.setHorizontalScrollBarPolicy(JScrollPane.HORIZONTAL_SCROLLBAR_NEVER)
            self.tabs.addTab(self.t(key),pane)
        self.tabs.addChangeListener(lambda e:self.tab_changed())
        outer.add(content,BorderLayout.CENTER)
        footer = JPanel(BorderLayout()); footer.setBackground(WHITE)
        footer.setBorder(BorderFactory.createEmptyBorder(8,22,8,22))
        self.status = label('',12,False,MUTED); footer.add(self.status,BorderLayout.CENTER)
        footbuttons = JPanel(FlowLayout(FlowLayout.RIGHT,8,0)); footbuttons.setBackground(WHITE)
        footbuttons.add(self.button('load',self.load_config)); footbuttons.add(self.button('save',self.save_config))
        footer.add(footbuttons,BorderLayout.EAST); outer.add(footer,BorderLayout.SOUTH)
        self.frame.setContentPane(outer)
        self.refresh_language()
        self.status.setText(self.t('ready')+' | Jython 2.7 / TopSpin 3 | v'+VERSION)
    def t(self,key): return TEXT[key][1 if self.lang=='es' else 0]
    def bind(self,component,key,method='setText'):
        self.bindings.append((component,key,method)); getattr(component,method)(self.t(key)); return component
    def button(self,key,fn,primary=False):
        b=self.bind(JButton(),key); b.setFont(Font('Segoe UI',Font.BOLD,13));b.setToolTipText(self.t(key))
        b.setFocusPainted(False); b.setPreferredSize(Dimension(max(150,b.getFontMetrics(b.getFont()).stringWidth(self.t(key))+40),34))
        if primary: b.setBackground(BLUE); b.setForeground(WHITE)
        b.addActionListener(lambda e:fn()); return b
    def text(self,key,size=14,bold=False): return self.bind(label('',size,bold),key)
    def para(self,key,width=430):
        c=paragraph(self.t(key),width); self.bindings.append((c,key,'paragraph:'+str(width))); return c
    def addfield(self,parent,key,name,value):
        row=JPanel(BorderLayout(0,2)); row.setBackground(WHITE);row.setAlignmentX(0.0)
        row.setBorder(BorderFactory.createEmptyBorder(0,0,6,0))
        row.setMaximumSize(Dimension(435,51))
        row.add(self.text(key,12,True),BorderLayout.NORTH)
        f=JTextField(str(value)); f.setFont(Font('Segoe UI',Font.PLAIN,14)); f.setPreferredSize(Dimension(435,28))
        if name in self.fields:f.setDocument(self.fields[name].getDocument())
        row.add(f,BorderLayout.CENTER); parent.add(row); self.fields[name]=f; return f
    def home_page(self):
        p=box(background=BG,pad=16)
        p.add(self.text('journey',25,True)); p.add(self.para('homebody',1040))
        cards=JPanel(GridLayout(1,4,14,0)); cards.setBackground(BG)
        cards.setBorder(BorderFactory.createEmptyBorder(24,0,20,0))
        for i in range(1,5):
            c=box(pad=18); c.add(label('0'+str(i),36,True,BLUE)); c.add(self.text('step'+str(i),17,True)); c.add(self.para('card'+str(i),200)); cards.add(c)
        cards.setMaximumSize(Dimension(3000,250)); p.add(cards)
        actions=JPanel(FlowLayout(FlowLayout.LEFT)); actions.setBackground(BG)
        actions.add(self.button('openp1',lambda:self.tabs.setSelectedIndex(2),True)); actions.add(self.button('opendosy',lambda:self.tabs.setSelectedIndex(3)))
        p.add(actions)
        scope=box(pad=18); scope.add(self.text('scope',16,True)); scope.add(self.para('scopebody',1030)); p.add(scope)
        self.pages.append(('home',p))
    def setup_page(self):
        p=box(pad=22); p.add(self.text('instrumenttitle',23,True)); p.add(self.para('instrumentbody',1040))
        work=JPanel(FlowLayout(FlowLayout.LEFT,10,4)); work.setBackground(WHITE)
        work.add(self.text('workexp',12,True)); self.workexp=JTextField('1050',6); work.add(self.workexp)
        work.add(self.button('workcopy',self.prepare_setup)); p.add(work)
        rows=JPanel(GridLayout(3,2,16,16)); rows.setBackground(WHITE); rows.setMaximumSize(Dimension(1120,180))
        rows.setBorder(BorderFactory.createEmptyBorder(22,0,20,0))
        self.capabilities={}
        for aid,checkkey,butkey in [('lock','enablelock','lock'),('atma','enableatma','atma'),('topshim','enableshim','shim')]:
            c=self.bind(JCheckBox(),checkkey); c.setBackground(WHITE); c.setFont(Font('Segoe UI',Font.PLAIN,14)); self.capabilities[aid]=c
            rows.add(c); b=self.button(butkey,lambda aid=aid:self.start_setup(aid)); rows.add(b)
        p.add(rows)
        self.lockvalid=self.bind(JCheckBox(),'lockvalid'); self.lockvalid.setBackground(WHITE); p.add(self.lockvalid)
        trow=JPanel(FlowLayout(FlowLayout.LEFT,10,4)); trow.setBackground(WHITE)
        self.tempcap=self.bind(JCheckBox(),'enabletemp'); self.tempcap.setBackground(WHITE); trow.add(self.tempcap)
        trow.add(self.button('readtemp',lambda:self.start_setup('read_temperature'))); p.add(trow)
        tset=JPanel(FlowLayout(FlowLayout.LEFT,8,4)); tset.setBackground(WHITE)
        tset.add(self.text('tempvalue',12,True)); self.tempvalue=JTextField('298.15',7); tset.add(self.tempvalue)
        tset.add(self.text('templimits',12,True)); self.templow=JTextField('',5); self.temphigh=JTextField('',5); tset.add(self.templow); tset.add(self.text('range_to')); tset.add(self.temphigh)
        tset.add(self.button('settemp',lambda:self.start_setup('set_temperature'))); p.add(tset)
        p.add(self.para('tempnote',1040)); p.add(self.text('gates',18,True))
        for key in ['checksample','checktemp','checkphase','checkpilot']:
            c=self.bind(JCheckBox(),key); c.setBackground(WHITE); c.setFont(Font('Segoe UI',Font.PLAIN,15)); c.setBorder(BorderFactory.createEmptyBorder(10,0,10,0)); self.checks[key]=c; p.add(c)
        p.add(self.button('context',self.read_context)); self.pages.append(('setup',p))
    def form_page(self,mode,guide):
        p=JPanel(BorderLayout(24,0)); p.setBackground(WHITE); p.setBorder(BorderFactory.createEmptyBorder(22,22,22,22))
        form=box(pad=0); right=box(pad=6); right.add(self.text('p1' if mode=='p1' else 'dosy',23,True)); right.add(self.para(guide,520))
        p.add(form,BorderLayout.WEST); p.add(right,BorderLayout.CENTER)
        self.pages.append((mode if mode=='p1' else 'dosy',p)); return form,right
    def common_fields(self,form,mode):
        # Common settings are shown on P1 and reused by DOSY.
        if mode=='p1':
            self.addfield(form,'dataset','dataset_name','calibration_demo' if self.demo else '')
            self.addfield(form,'root','data_root',os.path.join(os.getcwd(),'calibration_demo_data') if self.demo else '')
            self.addfield(form,'report','report_dir',os.path.join(os.path.expanduser('~'),'Documents','DiffAtOnce','calibration_reports'))
            self.addfield(form,'procno','template_procno','1')
        self.addfield(form,'template',mode+'_template_expno','1000' if mode=='p1' else '10')
        self.addfield(form,'first',mode+'_start_expno','1100' if mode=='p1' else '1200')
    def p1_page(self):
        f,r=self.form_page('p1','p1guide'); self.common_fields(f,'p1')
        self.addfield(f,'valuesp1','p1_values_us',','.join(str(2*i) for i in range(1,25)))
        self.addfield(f,'p90min','p90_min_us','5.5'); self.addfield(f,'p90max','p90_max_us','18')
        self.addfield(f,'low','ppm_low','4.6'); self.addfield(f,'high','ppm_high','5.0')
        r.add(self.para('p1example',520)); r.add(self.button('preview',lambda:self.preview('p1'),True))
    def dosy_page(self):
        f,r=self.form_page('gradient','dosyguide'); self.common_fields(f,'gradient')
        self.addfield(f,'program','gradient_program','stebpgp1s1d')
        self.addfield(f,'valuesg','gradient_values_percent',','.join(str(i) for i in range(8,97,4)))
        self.addfield(f,'dref','dref_1e9','1.15' if self.demo else '0'); self.addfield(f,'tref','reference_temperature_K','298.15')
        self.addfield(f,'ref','reference_label','DEMO reference / water / synthetic fixture' if self.demo else '')
        self.addfield(f,'span','max_temperature_span_K','0.5'); self.addfield(f,'tdiff','max_reference_temperature_difference_K','0.5')
        self.addfield(f,'priorb','gradient_b100_override_s_m2','0')
        self.addfield(f,'low','ppm_low','4.6');self.addfield(f,'high','ppm_high','5.0')
        r.add(self.text('sequence',18,True)); r.add(self.para('sequencebody',520))
        r.add(self.para('checkphase',520))
        r.add(self.button('preview',lambda:self.preview('gradient'),True)); self.dosycontext=paragraph('',520); r.add(self.dosycontext)
    def run_page(self):
        p=box(pad=16)
        actions=JPanel(FlowLayout(FlowLayout.LEFT,8,0)); actions.setBackground(WHITE)
        actions.add(self.text('workflow',13,True)); self.modechoice=JComboBox(['P1','DOSY']); actions.add(self.modechoice)
        self.modechoice.addActionListener(lambda e:self.restore_result())
        self.workbuttons=[]
        for key,fn in [('preview',lambda:self.preview()),('prepare',lambda:self.start_run('prepare')),('acquire',lambda:self.start_run('acquire')),('analyze',lambda:self.start_run('analyze'))]:
            b=self.button(key,fn,key=='acquire'); self.workbuttons.append(b); actions.add(b)
        p.add(actions)
        self.progress=JProgressBar(0,100); self.progress.setStringPainted(True); self.progress.setMaximumSize(Dimension(3000,24)); p.add(self.progress)
        stoptop=JPanel(FlowLayout(FlowLayout.LEFT,8,6)); stoptop.setBackground(WHITE); self.stopbutton=self.button('stop',self.stop); self.stopbutton.setEnabled(False); stoptop.add(self.stopbutton); stoptop.add(self.text('stopnote',11)); p.add(stoptop)
        body=JPanel(GridLayout(1,2,16,0)); body.setBackground(WHITE)
        left=box(pad=0); left.add(self.text('plan',16,True)); self.tablemodel=DefaultTableModel([],['Point','EXPNO','Parameter','Value']); self.table=JTable(self.tablemodel); self.table.setRowHeight(25); self.table.setFont(Font('Segoe UI',Font.PLAIN,12)); left.add(JScrollPane(self.table))
        left.add(self.text('log',16,True)); self.log=JTextArea(7,40); self.log.setEditable(False); self.log.setFont(Font('Consolas',Font.PLAIN,11)); left.add(JScrollPane(self.log))
        right=box(pad=0); right.add(self.text('results',16,True)); self.resultsummary=label('',18,True); right.add(self.resultsummary); self.curve=CurvePanel(self); right.add(self.curve)
        self.resultdetails=JTextArea(7,45); self.resultdetails.setEditable(False); self.resultdetails.setLineWrap(True); self.resultdetails.setWrapStyleWord(True); self.resultdetails.setFont(Font('Segoe UI',Font.PLAIN,12)); right.add(JScrollPane(self.resultdetails))
        body.add(left); body.add(right); body.setPreferredSize(Dimension(1120,380));body.setMaximumSize(Dimension(3000,380)); p.add(body)
        applypanel=JPanel(FlowLayout(FlowLayout.LEFT,10,8)); applypanel.setBackground(BG)
        self.reviewbox=self.bind(JCheckBox(), 'review'); self.reviewbox.setBackground(BG); p.add(self.reviewbox)
        applypanel.add(self.text('target',12,True)); self.applytarget=JTextField('1300',6); applypanel.add(self.applytarget); self.applybutton=self.button('apply',self.apply_result); applypanel.add(self.applybutton); applypanel.add(self.button('reports',self.open_reports)); p.add(applypanel)
        self.applybutton.setEnabled(False); self.pages.append(('run',p))
    def refresh_language(self):
        self.subtitle.setText(self.t('title')+'  /  '+self.t('subtitle'))
        self.banner.setText(self.t('demo' if self.demo else 'live'))
        for c,k,m in self.bindings:
            if m.startswith('paragraph:'):
                width=int(m.split(':')[1]);c.setText(self.t(k));size=paragraph(self.t(k),width).getPreferredSize();c.setPreferredSize(size);c.setMaximumSize(size)
            else: getattr(c,m)(self.t(k))
            if isinstance(c,JButton):c.setPreferredSize(Dimension(max(150,c.getFontMetrics(c.getFont()).stringWidth(self.t(k))+40),34));c.setToolTipText(self.t(k))
        for i,(key,p) in enumerate(self.pages): self.tabs.setTitleAt(i,self.t(key))
        for i,key in enumerate(['point',None,'parameter','value']):
            self.table.getColumnModel().getColumn(i).setHeaderValue(self.t(key) if key else 'EXPNO')
        self.table.getTableHeader().repaint(); self.curve.repaint(); self.frame.revalidate(); self.frame.repaint()
        if not self.running:self.status.setText(self.t('ready')+' | Jython 2.7 / TopSpin 3 | v'+VERSION)
        if self.result: self.show_result(self.result)
    def change_language(self):
        self.lang='es' if self.language.getSelectedIndex()==1 else 'en'
        if hasattr(self,'curve'): self.refresh_language()
    def tab_changed(self):
        i=self.tabs.getSelectedIndex()
        if i==2: self.mode='p1'; self.modechoice.setSelectedIndex(0)
        elif i==3: self.mode='gradient'; self.modechoice.setSelectedIndex(1)
    def config(self):
        config={key:unicode(field.getText()).strip() for key,field in self.fields.items()}
        config['mode']='p1' if self.modechoice.getSelectedIndex()==0 else 'gradient'
        for key in ['template_procno','p1_template_expno','gradient_template_expno','p1_start_expno','gradient_start_expno']:
            config[key]=int(config[key])
        for key in ['ppm_low','ppm_high','p90_min_us','p90_max_us','dref_1e9','reference_temperature_K','max_temperature_span_K','max_reference_temperature_difference_K','gradient_b100_override_s_m2']:
            config[key]=float(config[key])
            if math.isnan(config[key]) or math.isinf(config[key]): raise ValueError(self.t('invalidnumber')+key)
        for key in ['p1_values_us','gradient_values_percent']:
            config[key]=[float(v.strip()) for v in config[key].split(',') if v.strip()]
        config['operator_checks']={k:bool(v.isSelected()) for k,v in self.checks.items()}
        config['language']=self.lang
        return config
    def populate(self,config):
        for key,field in self.fields.items():
            if key in config: field.setText(','.join(str(v) for v in config[key]) if isinstance(config[key],list) else str(config[key]))
        # A saved configuration cannot establish current sample conditions or
        # reuse a reviewed fit from another dataset or instrument session.
        for v in self.checks.values():v.setSelected(False)
        for v in self.capabilities.values():v.setSelected(False)
        self.tempcap.setSelected(False);self.lockvalid.setSelected(False)
        self.reviewbox.setSelected(False);self.applybutton.setEnabled(False)
        self.setup_config=instrument_setup.default_setup_config()
        self.outputs.clear();self.result=None;self.curve.plot=None
        self.resultsummary.setText('');self.resultdetails.setText('');self.curve.repaint()
        self.language.setSelectedIndex(1 if config.get('language')=='es' else 0)
    def error(self,error):
        self.status.setText(self.t('error')+': '+unicode(error))
        self.log.append('\n'+unicode(error)+'\n')
        JOptionPane.showMessageDialog(self.frame,unicode(error),self.t('error'),JOptionPane.ERROR_MESSAGE)
    def dispatch(self,fn):
        if self.running: self.error(self.t('busy')); return
        self.running=True; self.stop_event.clear(); self.job_started=False
        for b in self.workbuttons: b.setEnabled(False)
        self.stopbutton.setEnabled(True); self.applybutton.setEnabled(False)
        self.status.setText(self.t('working'))
        def worker():
            try:
                result=fn()
                if result is not None: edt(lambda:self.job_finished(result))
            except (Exception, Throwable) as exc:
                message=unicode(exc); self.last_traceback=traceback.format_exc(); edt(lambda:self.error(message))
            finally: edt(self.idle)
        if self.demo:
            th=threading.Thread(target=worker); th.setDaemon(True); th.start()
        else:
            self.job=worker
            # Replaced by the documented TopSpin command-thread dispatcher in
            # the built bundle. It must never fall back to a generic thread.
            if not hasattr(self,'topspin_dispatch'):
                self.idle(); self.error('TopSpin command-thread dispatcher unavailable'); return
            try:
                self.topspin_dispatch()
                self.dispatch_timer=Timer(500,lambda e:self.check_dispatch())
                self.dispatch_timer.start()
            except (Exception, Throwable) as exc: self.idle(); self.error(exc)
    def check_dispatch(self):
        if not self.running or self.job_started:
            self.dispatch_timer.stop(); return
        thread=getattr(self,'command_thread',None)
        if thread is not None and hasattr(thread,'isAlive') and not thread.isAlive():
            self.dispatch_timer.stop(); self.idle(); self.error('TopSpin dispatcher did not invoke the GUI callback. Verify the read-only command-thread pilot.')
    def idle(self):
        self.running=False; self.job=None
        for b in self.workbuttons: b.setEnabled(True)
        self.stopbutton.setEnabled(False); self.applybutton.setEnabled(bool(self.result and self.result.get('mode')=='p1'))
        if self.close_pending:self.frame.dispose()
    def event(self,event):
        def update():
            total,current=event.get('total',0),event.get('current',0)
            if total: self.progress.setValue(int(100*current/total))
            self.log.append('[%s] %s\n'%(event.get('stage',''),event.get('message','')))
            self.log.setCaretPosition(self.log.getDocument().getLength())
        edt(update)
    def setplan(self,preview,clear_log=True,select_tab=True):
        self.tablemodel.setRowCount(0)
        rows=preview.get('rows',preview.get('plan',{}).get('rows',[]))
        for row in rows: self.tablemodel.addRow([row.get('point'),row.get('expno'),row.get('parameter'),row.get('value')])
        if clear_log:self.log.setText('\n'.join(preview.get('warnings',[])))
        if preview.get('collisions'): self.log.setText(self.t('collision')+', '.join(os.path.basename(p) for p in preview['collisions'])+'\n'+self.log.getText())
        self.log.setCaretPosition(0)
        if select_tab:self.tabs.setSelectedIndex(4)
    def preview(self,mode=None):
        try:
            if mode: self.modechoice.setSelectedIndex(0 if mode=='p1' else 1)
            cfg=self.config()
            self.dispatch(lambda:self.preview_job(cfg))
        except Exception as exc:self.error(exc)
    def preview_job(self,cfg):
        preview=self.controller.preview(cfg); edt(lambda:self.setplan(preview)); return {'status':'previewed','preview':preview}
    def start_run(self,action):
        try:
            cfg=self.config()
            if action=='acquire' and not all(cfg['operator_checks'].values()): raise ValueError(self.t('checkrequired'))
            if self.running:raise ValueError(self.t('busy'))
            self.result=None;self.curve.plot=None;self.curve.repaint();self.resultsummary.setText(self.t('working'));self.resultdetails.setText('');self.log.setText('')
            self.dispatch(lambda:self.controller.run(cfg,action,callback=self.event,stop_event=self.stop_event))
        except Exception as exc:self.error(exc)
    def stop(self): self.stop_event.set(); self.status.setText(self.t('stopped'))
    def job_finished(self,output):
        self.status.setText(self.t('success')+' | '+unicode(output.get('status','')))
        if output.get('plan'): self.setplan({'plan':output['plan']},clear_log=False)
        if output.get('result'):
            self.result=output; self.show_result(output)
            self.outputs[output.get('plan',{}).get('mode','p1')]=output
        if output.get('output_dir'): self.last_output=output['output_dir']
        if output.get('status')=='applied':self.status.setText(self.t('resultcopied')+' | EXPNO '+str(output.get('target_expno')))
        if output.get('status') not in ('previewed','stopped'): self.progress.setValue(100)
    def restore_result(self):
        if not hasattr(self,'curve') or self.running:return
        mode='p1' if self.modechoice.getSelectedIndex()==0 else 'gradient'
        if mode in self.outputs:
            self.result=self.outputs[mode];self.show_result(self.result);self.setplan({'plan':self.result['plan']},clear_log=False,select_tab=False)
            self.last_output=self.result.get('output_dir')
            self.log.setText('\n'.join('[%s] %s %s'%(e['stage'],e.get('expno',''),e['message']) for e in self.result.get('events',[])))
            self.applybutton.setEnabled(mode=='p1')
    def show_result(self,output):
        result=output.get('result',{})
        mode=output.get('mode',output.get('plan',{}).get('mode','p1'))
        output['mode']=mode
        badge=self.t('simulation' if output.get('demo',self.demo) else 'candidate')
        if mode=='p1':
            p90=result.get('P90_us',0); p180=result.get('P180_us',0)
            self.resultsummary.setText('%s  |  P90 %.3f µs  /  P180 %.3f µs'%(badge,p90,p180))
            details='R² = %.6f\n'%(result.get('R2',0)) + self.t('p1guide')+'\n'+self.t('p1example')
        else:
            profile=result.get('calibration_profile',{})
            b100=profile.get('b_at_100_percent_s_m2',0)
            self.resultsummary.setText('%s  |  b100 = %.4g s/m²'%(badge,b100))
            details='R² = %.6f\n'%(result.get('fit',{}).get('R2',0))+self.t('dosyguide')
        self.resultdetails.setText(details); self.curve.plot=output.get('plot') or result.get('plot')
        if self.curve.plot and mode=='p1':self.curve.plot['p90']=result.get('P90_us')
        self.curve.repaint()
    def apply_result(self):
        try:
            if not self.result or self.result.get('mode')!='p1':raise ValueError('No reviewed P1 candidate')
            cfg=self.config(); cfg['mode']='p1'; value=self.result['result']['P90_us']; target=int(self.applytarget.getText())
            if not self.reviewbox.isSelected(): raise ValueError(self.t('review'))
            self.dispatch(lambda:self.controller.apply_p1(cfg,value,target,reviewed=True,callback=self.event))
        except Exception as exc:self.error(exc)
    def read_context(self):
        def work():
            context=self.controller.context(); edt(lambda:self.update_context(context)); return {'status':'context read'}
        self.dispatch(work)
    def update_context(self,context):
        self.last_context=context
        data=context.get('dataset',context.get('current',context.get('curdata',[])))
        if isinstance(data,list) and len(data)==4:
            self.fields['dataset_name'].setText(str(data[0])); self.fields['data_root'].setText(str(data[3])); self.fields['template_procno'].setText(str(data[2]))
        self.dosycontext.setText('Dataset: '+context.get('dataset_name','')+'\nP1 template: '+str(context.get('p1_template_expno',1000))+' | DOSY template: '+str(context.get('gradient_template_expno',10)))
        self.log.append(json.dumps(context,ensure_ascii=False,indent=2)+'\n')
    def start_setup(self,action):
        if action in self.capabilities and not self.capabilities[action].isSelected(): self.error(self.t({'lock':'enablelock','atma':'enableatma','topshim':'enableshim'}[action])); return
        if action in ('read_temperature','set_temperature') and not self.tempcap.isSelected():self.error(self.t('enabletemp'));return
        if not self.setup_config.get('working_dataset_confirmed'):self.error(self.t('workfirst'));return
        config=dict(self.setup_config)
        config.update({'enabled':True,'supported_commands':['lock','atma','topshim','teget','teset'],
            'lock_supported':bool(self.capabilities['lock'].isSelected()),
            'probe_atm_supported':bool(self.capabilities['atma'].isSelected()),
            'topshim_configured':bool(self.capabilities['topshim'].isSelected()),
            'lock_confirmed':bool(self.lockvalid.isSelected()),
            'temperature_controller_supported':bool(self.tempcap.isSelected())})
        demand=None
        try:
            if action=='set_temperature':
                config['temperature_limits_K']=[float(self.templow.getText()),float(self.temphigh.getText())]
                demand=float(self.tempvalue.getText())
                if not config['temperature_limits_K'][0] <= demand <= config['temperature_limits_K'][1]:raise ValueError('Temperature outside configured probe/controller limits')
        except Exception as exc:self.error(exc);return
        def work():
            if self.demo:
                self.event({'stage':'DEMO','message':'Simulated '+action.upper()+': no hardware command sent','current':1,'total':1})
                return {'status':'simulated preparation'}
            try:
                result=instrument_setup.run_setup_action(self.api,action,config,on_event=self.setup_event,temperature_K=demand)
            except Exception as exc:
                if getattr(exc,'report',None):self.persist_setup(exc.report)
                raise
            result['output_dir']=self.persist_setup(result)
            self.event({'stage':'setup_result','message':json.dumps(result,ensure_ascii=False),'current':1,'total':1})
            return result
        self.dispatch(work)
    def prepare_setup(self):
        try:
            cfg=self.config(); target=int(self.workexp.getText())
            def work():
                if self.demo:
                    # Demo controller seeds its synthetic templates during preview.
                    self.controller.ensure_demo_inputs(cfg)
                    current=self.controller.context()['current']
                    source=[current[0],str(cfg['p1_template_expno']),str(cfg['template_procno']),current[3]]
                    result=instrument_setup.prepare_working_dataset(self.controller.api,source,target)
                else:
                    source=[cfg['dataset_name'],str(cfg['p1_template_expno']),str(cfg['template_procno']),cfg['data_root']]
                    result=instrument_setup.prepare_working_dataset(self.api,source,target)
                self.setup_config.update({'working_dataset':result['working_dataset'], 'working_dataset_confirmed':True,'expected_solvent':result['expected_solvent']})
                result['output_dir']=self.persist_setup(result)
                self.event({'stage':'working_copy','message':json.dumps(result,ensure_ascii=False),'current':1,'total':1})
                return result
            self.dispatch(work)
        except Exception as exc:self.error(exc)
    def setup_event(self,event):
        report=event.get('report',{})
        self.event({'stage':event.get('event','setup'),'message':report.get('command','')+' '+report.get('status',''),'current':0,'total':0})
    def persist_setup(self,receipt):
        folder=os.path.join(unicode(self.fields['report_dir'].getText()),'instrument_setup_'+uuid.uuid4().hex[:12])
        os.makedirs(folder)
        saved=dict(receipt);saved['demo']=self.demo;saved['evidence_type']='simulated software demonstration' if self.demo else 'command receipt; physical review required'
        with io.open(os.path.join(folder,'receipt.json'),'w',encoding='utf-8',newline='\n') as f:f.write(unicode(json.dumps(saved,ensure_ascii=False,indent=2,separators=(',', ': '))) + '\n')
        return folder
    def chooser(self,save=False):
        c=JFileChooser(); c.setSelectedFile(__import__('java.io',fromlist=['File']).File('calibration_settings.json'))
        return unicode(c.getSelectedFile().getAbsolutePath()) if (c.showSaveDialog(self.frame) if save else c.showOpenDialog(self.frame))==JFileChooser.APPROVE_OPTION else None
    def save_config(self):
        try:
            path=self.chooser(True)
            if path:
                with io.open(path,'w',encoding='utf-8',newline='\n') as f:f.write(unicode(json.dumps(self.config(),ensure_ascii=False,indent=2,separators=(',', ': '))) + '\n')
                self.status.setText(self.t('saved'))
        except Exception as exc:self.error(exc)
    def load_config(self):
        try:
            if self.running:raise ValueError(self.t('busy'))
            path=self.chooser(False)
            if path:
                with io.open(path,'r',encoding='utf-8') as f:self.populate(json.load(f))
                self.status.setText(self.t('loaded'))
        except Exception as exc:self.error(exc)
    def open_reports(self):
        from java.awt import Desktop
        from java.io import File
        path=getattr(self,'last_output',self.fields['report_dir'].getText())
        if os.path.isdir(path): Desktop.getDesktop().open(File(path))
        else:self.error(self.t('nosource'))
    def show(self): self.frame.setVisible(True)

APP=None

def main(api=None,demo=False,dispatch=None):
    global APP
    def create():
        global APP
        APP=CalibrationApp(api=api,demo=demo)
        if dispatch: APP.topspin_dispatch=dispatch
        APP.show()
    if SwingUtilities.isEventDispatchThread():create()
    else:SwingUtilities.invokeAndWait(Task(create))
    return APP

if __name__=='__main__': main(demo=True)
