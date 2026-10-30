"""Research Studio 1.3 bilingual guides/PDFs from reviewed text and actual UI captures.

No packages/models/experimental files are copied. Requires all fourteen final UI
captures. The PDF artifact-start marker is a separate, once-only authoring action.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle, Flowable,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[3]
ACADEMY = ROOT / "desktop/academy"
DOCS = ACADEMY / "docs"
QA = ACADEMY / "qa/research-1.3/manuals"
CAPTURES = ACADEMY / "qa/research-1.3/ui"
NODE = os.environ.get("ACADEMY_NODE") or shutil.which("node") or "node"
FIGURES = ["brief", "calibration", "uncertainty", "spatial", "competencies", "defence", "library", "pilot"]
NAV = {
    "es": ["La pregunta", "Calibrar", "Diseñar", "Adquirir", "Procesar", "Interpretar", "Incertidumbre", "Próxima medida", "RF + espacio", "Competencias", "Defensa y revisión", "Datos públicos"],
    "en": ["The question", "Calibrate", "Design", "Acquire", "Process", "Interpret", "Uncertainty", "Next measurement", "RF + space", "Competencies", "Defence and review", "Public data"],
}
BLUE = colors.HexColor("#132f3d")
TEAL = colors.HexColor("#087d78")
LIGHT = colors.HexColor("#eef6f6")
GREY = colors.HexColor("#536a73")


def clean(text):
    value=str(text).replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-").replace("\u2212", "-")
    # Arial embeds Greek and the common unit superscripts, but not U+207B.
    # Spell signed powers explicitly rather than render a missing glyph.
    table=str.maketrans("⁺⁻⁰¹²³⁴⁵⁶⁷⁸⁹", "+-0123456789")
    return re.sub(r"[⁺⁻][⁰¹²³⁴⁵⁶⁷⁸⁹]+",lambda match:"^"+match.group().translate(table),value)


def example_data():
    node = NODE
    script = r"""
const J=require('./desktop/academy/web/research-journey.js');
let s=J.createCase({seed:20261030,preset:'combined'});
const p=s.pilots,r=p.referenceCurve.at(-1),fit=-Math.log(r.signal)/r.bNominal,g=Math.sqrt(fit/p.referenceD);
const un=v=>v.state||v;
s=un(J.calibrate(s,{p90Us:p.firstNullUs/2,gradientScale:g,referenceD:p.referenceD,referenceTemperatureK:p.referenceTemperatureK,measuredTemperatureK:298.15}));
s=un(J.design(s,{sequence:'ste',deltaMs:2,bigDeltaMs:80,ledMs:5,gradientMax:.3,points:20,scans:8,repeats:1,recycleSeconds:2,budgetMinutes:15,order:'ascending'}));
s=un(J.acquire(s,{}));
s=un(J.process(s,{phaseDeg:0,baseline:0,lbHz:0,window:'all'}));
s=un(J.analyze(s,{method:'mono',regularization:.02}));
s=un(J.uncertainty(s,{samples:40,gradientRelativeSd:.02,temperatureSdK:.3,processingRelativeSd:.01,noiseRelativeSd:.01,sequenceRelativeSd:.01}));
console.log(JSON.stringify({id:s.id,seed:s.seed,preset:s.preset,firstNullUs:p.firstNullUs,p90Us:s.calibration.p90Us,referenceD:p.referenceD,referenceFitD:s.calibration.referenceFit.D,gradientScale:s.calibration.gradientScale,durationSeconds:s.design.durationSeconds,maxB:Math.max(...s.design.bApplied),D:s.analysis.D_m2_s,residualRms:s.analysis.residualRms,interval95:s.uncertainty.interval95,sourceContributions:s.uncertainty.sourceContributions.map(c=>({id:c.id,relativeSd:c.relativeSd}))}));
"""
    result = subprocess.run([str(node), "-e", script], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8")
    return json.loads(result.stdout)


def chapters(lang, example):
    es = lang == "es"
    def L(a, b): return a if es else b
    def chapter(key, title_es, title_en, goal_es, goal_en, steps_es, steps_en, meaning_es, meaning_en, check_es, check_en, caution_es="", caution_en="", figure=None):
        return {"id":key,"title":L(title_es,title_en),"goal":L(goal_es,goal_en),"steps":L(steps_es,steps_en),"meaning":L(meaning_es,meaning_en),"check":L(check_es,check_en),"caution":L(caution_es,caution_en),"figure":figure}
    f = lambda n: f"{n:.6g}"
    return [
      chapter("use", "Cómo aprender con esta versión", "How to learn with this version",
       "Transformar una pregunta sobre difusión en una conclusión proporcionada a los datos.", "Turn a diffusion question into a conclusion proportional to the evidence.",
       ["Abre Investigación en Academy web o pulsa Investigación continua en WPF y selecciona ES/EN. La misma interfaz y los mismos motores numéricos sustentan ambas ediciones.", "Recorre las doce etapas. Antes de pulsar una acción, escribe una predicción y su motivo en el panel de ayuda.", "Usa las actividades Doctorado, Derivaciones y Animaciones para profundizar y vuelve al mismo caso.", "Exporta la investigación al acabar cada sesión. Practica después con otra semilla y sin consultar el ejemplo resuelto."],
       ["Open Research in Academy web or choose Research studio in WPF, then select ES/EN. Both editions use the same interface and numerical engines.", "Follow the twelve stages. Before an action, enter a prediction and reason in the help panel.", "Use Doctoral, Derivations and Animations for deeper study, then return to the same case.", "Export the investigation after each session. Then practise with another seed without consulting the worked example."],
       "Las siete ampliaciones enlazan muestra, incertidumbre, datos reales, competencias, diseño de controles, codificación espacial y tutoría/revisión.", "The seven extensions connect the sample, uncertainty, real data, competencies, control design, spatial encoding and tutoring/review.",
       "Al terminar debes poder explicar qué mediste, cómo elegiste la ecuación, qué sesgos quedan y qué control podría refutarte.", "At the end you should explain what was measured, why the equation applies, which biases remain and which control could refute your claim.",
       "Completar pantallas o superar pruebas de software no demuestra dominio ni valida un experimento.", "Completing screens or passing software checks does not establish mastery or validate an experiment."),
      chapter("state", "Qué conserva la misma muestra", "What travels with the same sample",
       "Distinguir datos adquiridos, decisiones, supuestos y verdad de una simulación.", "Distinguish acquired data, decisions, assumptions and simulation truth.",
       ["La semilla fija una muestra sintética reproducible; no identifica una molécula real.", "Calibración, diseño, serie compleja, procesado y ajuste permanecen unidos a su identidad e historial.", "Si cambias una decisión anterior, revisa las etapas posteriores y vuelve a calcular. Un resultado previo no prueba el nuevo diseño.", "Al vincular integrales públicas o CSV, la evidencia se declara experimental/importada y su procedencia sigue siendo necesaria."],
       ["The seed fixes a reproducible synthetic sample; it does not identify a real molecule.", "Calibration, design, complex series, processing and fitting stay linked to the sample identity and history.", "After changing an earlier decision, review and recalculate later stages. An earlier result does not establish the new design.", "When public or CSV integrals are attached, evidence is labelled experimental/imported and provenance remains required."],
       "Las unidades internas son SI: D en m²/s, b en s/m² y gradiente en T/m. La interfaz muestra pulsos en µs y tiempos de secuencia en ms.", "Internal units are SI: D in m²/s, b in s/m² and gradient in T/m. The interface displays pulses in µs and sequence times in ms.",
       "Comprueba identidad, unidades y estado del procesado antes de comparar dos resultados.", "Check identity, units and processing state before comparing results.",
       "Los originales experimentales no se modifican. La calibración virtual no recalibra automáticamente datos importados ni el espectrómetro.", "Experimental originals are unchanged. Virtual calibration does not automatically recalibrate imported data or the spectrometer."),
      chapter("brief", "01 - La pregunta", "01 - The question",
       "Formular una hipótesis y un resultado que la pueda contradecir.", "State a hypothesis and a result that could contradict it.",
       ["Selecciona Dificultad oculta e Identidad reproducible; pulsa Crear otro caso sólo cuando quieras iniciar otra muestra.", "Empieza con Señal aislada; después prueba Calibración del gradiente, Convección, Deriva temporal, Solapamiento o Fallos combinados.", "Escribe una pregunta concreta: por ejemplo, si una diferencia de D puede explicarse por orden de rampa y no sólo por dos especies.", "Registra qué observarías bajo cada hipótesis antes de adquirir."],
       ["Select Hidden difficulty and Reproducible identity; use Create another case only to start a different sample.", "Start with Isolated signal, then try Gradient calibration, Convection, Time drift, Overlap or Combined faults.", "Write a concrete question: for example, whether a D difference might follow ramp order rather than only two species.", "Record predictions for each hypothesis before acquiring."],
       "La causa no se revela por acertar una palabra. Las decisiones y los controles deben sostener tu argumento.", "A cause is not established by choosing a word. Decisions and controls must support the argument.",
       "Tu pregunta contiene una observación medible, una alternativa y un control posible.", "Your question includes a measurable observation, an alternative and a possible control.",
       "Elegir un preset informa de la familia del problema. Para evaluar sin esa pista usa casos y preguntas reservados del docente; una práctica guiada no es una prueba completamente ciega.", "Choosing a preset reveals the problem family. For evaluation without that cue, use instructor-reserved cases/questions; guided practice is not a fully blind assessment.", "brief"),
      chapter("calibration", "02 - Calibrar antes de medir", "02 - Calibrate before measuring",
       "Separar calibración RF, escala de gradiente y condiciones del patrón.", "Separate RF calibration, gradient scale and standard conditions.",
       ["Inspecciona la curva de nutación con signo. Identifica el primer nulo de 180° mediante el máximo anterior y el cambio de signo.", "Introduce P90 = P180/2 a potencia y condiciones constantes. Un nulo de 360° se divide entre cuatro; el nulo aislado no identifica su orden.", "Ajusta el decaimiento del patrón frente a b nominal; para una escala común g_real=s·g_nominal usa s=√(D_nominal/D_ref).", "Comprueba temperatura del patrón y referencia; después pulsa Aplicar calibración al caso."],
       ["Inspect the signed nutation curve. Identify the first 180° null using the preceding maximum and sign reversal.", "Enter P90=P180/2 at constant power and conditions. A 360° null is divided by four; a null alone does not establish its order.", "Fit the standard decay against nominal b; for one common scale g_actual=s·g_nominal use s=√(D_nominal/D_ref).", "Check standard and reference temperatures, then press Apply calibration to case."],
       "Si se usa b nominal, un error de escala del gradiente aparece al cuadrado en D. Repetir más scans no elimina ese sesgo.", "With nominal b, a gradient-scale error enters D quadratically. More scans do not remove this bias.",
       "Justifica el nulo elegido, el D de referencia, su temperatura y qué forma de onda cubre la calibración.", "Justify the chosen null, reference D, temperature and waveform covered by calibration.",
       "P90 debe comprobarse para la muestra y potencia adecuadas. p30, d20 y d5 requieren el programa de pulsos concreto; no tienen una traducción universal.", "P90 must be checked for the appropriate sample and power. p30, d20 and d5 require the actual pulse program; no universal translation exists.", "calibration"),
      chapter("design", "03 - Diseñar una medida informativa", "03 - Design an informative measurement",
       "Elegir una ventana de atenuación y controles dentro de un presupuesto.", "Choose an attenuation window and controls within a budget.",
       ["Elige Eco de espín, Eco estimulado, LED o Doble estimulado y documenta por qué.", "Ajusta δ, Δ, d5/LED, gradiente máximo, niveles, NS, réplicas y orden de rampa.", "Pulsa Comprobar diseño y presupuesto; revisa duración, b máximo y restricciones antes de adquirir.", "Predice qué cambiará al aumentar Δ o invertir/intercalar la rampa. Cambia una variable cada vez cuando quieras atribuir una causa."],
       ["Choose Spin echo, Stimulated echo, LED or Double stimulated and explain why.", "Set δ, Δ, d5/LED, maximum gradient, levels, NS, replicates and ramp order.", "Press Check design and budget; inspect duration, maximum b and restrictions before acquiring.", "Predict the effect of longer Δ or reverse/interleaved order. Change one variable at a time for causal comparisons."],
       "Más ponderación puede mejorar contraste y perder señal. LED añade tiempo; las pérdidas y la compensación dependen de la secuencia.", "More weighting can improve contrast while losing signal. LED adds time; losses and compensation depend on sequence.",
       "Puedes explicar qué aporta cada nivel y qué parte de tu presupuesto sirve para controlar errores.", "You can explain the role of each level and the part of the budget used to control errors.",
       "Los tiempos son un modelo docente ideal. Verifica el programa real y los límites del instrumento antes de trasladar una receta al laboratorio.", "Timing is an ideal teaching model. Check the actual program and instrument limits before transferring a recipe to the laboratory."),
      chapter("acquire", "04 - Adquirir la misma muestra", "04 - Acquire the same sample",
       "Relacionar el diseño con una serie compleja y con su orden temporal.", "Connect the design to a complex series and acquisition order.",
       ["Después de calibrar y diseñar, pulsa Adquirir la serie virtual.", "Inspecciona el FID y el número de adquisiciones; conserva la identidad de muestra y semilla.", "Compara una réplica con una adquisición invertida/intercalada. Describe qué debería cambiar si existe deriva.", "Conserva la primera investigación exportada antes de iniciar otra semilla."],
       ["After calibration and design, press Acquire virtual series.", "Inspect the FID and acquisition count; retain sample identity and seed.", "Compare a replicate with reversed/interleaved acquisition. Describe the expected change under drift.", "Export the first investigation before starting another seed."],
       "Los datos sintéticos contienen ruido reproducible y dificultades fijadas por la muestra; el FID no es un gráfico decorativo.", "Synthetic data contain reproducible noise and sample-specific difficulties; the FID is a computed signal.",
       "La señal, el orden temporal y b se mantienen emparejados en tu análisis.", "Signal, temporal order and b remain paired in your analysis.",
       "Esta acción no envía órdenes a TopSpin ni adquiere una muestra física. Los datos experimentales entran por Datos públicos o importación.", "This action does not command TopSpin or acquire a physical sample. Experimental data enter through Public data or import."),
      chapter("process", "05 - Procesar con decisiones explícitas", "05 - Process with explicit decisions",
       "Conservar el signo y comprobar la dependencia de fase, ventana y línea de base.", "Preserve the sign and check phase, window and baseline dependence.",
       ["Ajusta Corrección de fase, Offset sustraído, apodización y Ventana de señal.", "Pulsa Procesar e integrar. Inspecciona el espectro y el decaimiento de las integrales.", "Compara Todo el espectro, Señal 1 y Señal 2 cuando exista solapamiento.", "Explica por qué una ventana o fase distinta puede alterar una atenuación sin que D física haya cambiado."],
       ["Set Phase correction, Subtracted offset, apodization and Signal window.", "Press Process and integrate. Inspect the spectrum and integral decay.", "Compare Whole spectrum, Signal 1 and Signal 2 when overlap exists.", "Explain why a different window or phase may alter decay without changing physical D."],
       "Una integral es una decisión sobre datos complejos. Tomar sólo magnitudes o recortar valores negativos puede cambiar el ruido y sesgar el ajuste.", "An integral is a decision about complex data. Taking only magnitudes or clipping negative values can change noise and bias the fit.",
       "Tu informe permite repetir fase, ventana y tratamiento de línea de base.", "Your report allows phase, window and baseline processing to be reproduced.",
       "Para archivos Bruker reales comprueba filtro digital, referencia, secuencia y metadatos en el flujo experimental. No traslades índices de otra muestra.", "For real Bruker files, inspect digital filtering, reference, sequence and metadata in the experimental workflow. Do not transfer indices from another sample."),
      chapter("inference", "06 - Interpretar sin sobreafirmar", "06 - Interpret without overclaiming",
       "Comparar modelos sobre exactamente las mismas observaciones.", "Compare models on exactly the same observations.",
       ["Selecciona Monoexponencial, NNLS, Tikhonov no negativo o L1 no negativo y pulsa Ajustar los mismos datos.", "En ILT registra λ y la malla; compara residuos, estabilidad y máximos, no sólo el aspecto del mapa.", "Mantén el mismo procesado para atribuir cambios al método. Después estudia por separado la sensibilidad al procesado.", "Vuelve al laboratorio Doctorado para profundizar en el núcleo ILT, correlaciones y análisis conjunto."],
       ["Select Monoexponential, NNLS, Nonnegative Tikhonov or Nonnegative L1, then Fit the same data.", "For ILT, record λ and the grid; compare residuals, stability and peaks rather than only appearance.", "Keep processing fixed to attribute differences to the method. Then examine processing sensitivity separately.", "Return to the Doctoral laboratory for the ILT kernel, correlations and joint analysis."],
       "Una curva bien ajustada no determina una distribución única. La penalización introduce una preferencia y puede fusionar o crear máximos aparentes.", "A well-fitted curve does not determine a unique distribution. A penalty imposes a preference and may merge or create apparent peaks.",
       "Puedes distinguir ajuste numérico, resolución, distribución y asignación química.", "You can distinguish numerical fit, resolution, distribution and chemical assignment.",
       "La D monoexponencial de una mezcla es condicional al modelo. No atribuyas masas absolutas ni especies a partir del mapa por sí solo.", "A mixture's monoexponential D is conditional on the model. Do not assign absolute molar masses or species from the map alone."),
      chapter("uncertainty", "07 - Propagar errores compartidos", "07 - Propagate shared errors",
       "Separar dispersión aleatoria de sesgos y dependencias comunes.", "Separate random variation from biases and common dependencies.",
       ["Introduce Muestras Monte Carlo y las desviaciones de escala g, temperatura, procesado, ruido y modelo b.", "Pulsa Propagar errores compartidos y compara contribuciones e intervalo condicional.", "Repite reduciendo sólo ruido; después reduce la incertidumbre de calibración. Compara la diferencia.", "Describe qué fuentes comparten una misma realización entre gradientes y señales, y cuáles varían por observación."],
       ["Enter Monte Carlo draws and SDs for g scale, temperature, processing, noise and model b.", "Press Propagate shared errors and compare contributions and the conditional interval.", "Repeat after reducing only noise, then after reducing calibration uncertainty. Compare the effects.", "Describe which sources share a draw across gradients/signals and which vary by observation."],
       "La misma calibración puede desplazar juntas varias D. Tratar ese error como ruido independiente fabricaría información que no se adquirió.", "One calibration can shift several D values together. Treating it as independent noise would manufacture information that was not acquired.",
       "Justifica un control que reduzca la fuente dominante y enumera errores que tu intervalo no cuantifica.", "Justify a control that reduces a dominant source and list errors your interval does not quantify.",
       "El intervalo es condicional a los modelos y distribuciones introducidos. No es cobertura experimental validada ni corrige automáticamente un modelo erróneo.", "The interval is conditional on the supplied models and distributions. It is not validated experimental coverage and does not automatically correct a wrong model.", "uncertainty"),
      chapter("next", "08 - Elegir la próxima medida", "08 - Choose the next measurement",
       "Usar la ambigüedad para diseñar un control discriminante.", "Use ambiguity to design a discriminating control.",
       ["Compara Mayor rango b, Repetir el diseño, Invertir el orden, Cambiar Δ y Compensación de flujo.", "Escribe una predicción antes de pulsar Comparar diseños.", "Elige una adquisición y pulsa Observar control reservado. Las observaciones reservadas usan una realización independiente.", "Contrasta tu predicción con los resultados y explica qué alternativas sobreviven."],
       ["Compare Higher b range, Repeat the design, Reverse order, Change Δ and Flow compensation.", "Write a prediction before pressing Compare designs.", "Choose an acquisition and press Observe held-out control. Held-out observations use an independent realization.", "Compare the prediction with results and explain which alternatives remain."],
       "Dos distribuciones pueden predecir casi igual los datos disponibles y divergir en otra región b. La adquisición propuesta explora esa diferencia.", "Two distributions may predict the available data similarly and differ over another b region. The proposed acquisition explores that difference.",
       "Puedes defender por qué este control discrimina mejor que adquirir más puntos equivalentes.", "You can defend why this control discriminates better than more equivalent points.",
       "La selección de diseño y el dato reservado sintético no son validación externa de una muestra real. La compensación de flujo ideal no equivale a cualquier programa doble STE.", "Synthetic design selection and held-out data are not external validation of a real sample. Ideal flow compensation is not equivalent to every double-STE program."),
      chapter("spatial", "09 - RF, gradientes y espacio", "09 - RF, gradients and space",
       "Comprender el origen físico de la codificación espacial y sus límites numéricos.", "Understand the physical origin of spatial encoding and its numerical limits.",
       ["Ajusta celdas espaciales, longitud, duración/amplitud RF, barrido chirp, gradientes, evolución, lectura y perfil de bobina.", "Pulsa Calcular Bloch-Torrey; inspecciona magnetización, fase, perfil transversal y señal de lectura.", "Pulsa Comprobar convergencia para comparar el paso temporal y la malla refinados. Revisa los avisos de aliasing.", "Compara con el modelo introductorio ultrafast/SPEN de Doctorado: explica qué añade el cálculo desde RF y qué continúa siendo ideal."],
       ["Set spatial cells, length, RF duration/amplitude, chirp sweep, gradients, evolution, readout and coil profile.", "Press Calculate Bloch-Torrey; inspect magnetization, phase, transverse profile and readout.", "Press Check convergence to compare refined time step and grid. Review aliasing warnings.", "Compare with the introductory ultrafast/SPEN model under Doctoral: explain what RF-based computation adds and what remains ideal."],
       "El modelo es dM/dt = Ω×M + D·d²M/dz² - (Mx/T2, My/T2, (Mz-1)/T1). Ω contiene RF y gradiente, con fase chirp integrada en el tiempo. Se usan paredes reflectantes, difusión Crank-Nicolson y rotaciones exactas por paso. La lectura suma magnetización compleja ponderada por la bobina.", "The model is dM/dt = Ω×M + D·d²M/dz² - (Mx/T2, My/T2, (Mz-1)/T1). Ω contains RF and gradient with time-integrated chirp phase. Reflecting walls, Crank-Nicolson diffusion and exact per-step rotations are used. Readout sums coil-weighted complex magnetization.",
       "Puedes distinguir fase RF, integral física del gradiente, resolución nominal y error de discretización.", "You can distinguish RF phase, physical gradient integral, nominal resolution and discretization error.",
       "Durante RF, γ∫Gdt no es una vía de coherencia ni un b DOSY. Con lectura lineal, un offset Δf produce Δz_aparente=Δf/(γHz·G): no es movimiento molecular. El protocolo genérico no valida una secuencia UF/SPEN-DOSY concreta.", "During RF, γ∫Gdt is not coherence q or DOSY b. With linear readout, an offset Δf causes Δz_apparent=Δf/(γHz·G): not molecular motion. The generic protocol does not qualify a particular UF/SPEN-DOSY sequence.", "spatial"),
      chapter("competencies", "10 - Comprobar lo aprendido", "10 - Check what you learned",
       "Demostrar transferencia y retención, además de completar actividades.", "Demonstrate transfer and retention as well as activity completion.",
       ["Realiza Diagnóstico inicial antes de consultar pistas. Usa Practicar para trabajar conceptos pendientes y registra la ayuda utilizada.", "Completa Caso de transferencia con parámetros nuevos e inspecciona el estado por competencia. Vuelve a un caso que obligue a usarla.", "El piloto docente voluntario empieza vacío. Si participas, usa un código local opcional, marca el consentimiento y pulsa Consentir y abrir el caso inicial. Pretest y postest contienen siete preguntas con semillas diferentes; declara si respondiste sin ayuda.", "El caso de retención se habilita tras siete días, en la fecha mostrada; no hay un botón para adelantar ese plazo. Usa Comprobar fecha actual y Exportar resultados del piloto. No se precargan alumnos ni resultados."],
       ["Take Initial diagnostic before consulting hints. Use Practice for outstanding concepts and record assistance used.", "Complete Transfer case with new parameters and inspect each competency state. Return to a case that requires it.", "The voluntary teaching pilot starts empty. To participate, use an optional local code, mark consent and press Consent and open the initial case. Pretest and posttest contain seven questions with different seeds; declare whether you answered without assistance.", "The retention case becomes available after seven days, on the displayed date; there is no button to advance that interval. Use Check the current date and Export pilot results. No learners or results are preloaded."],
       "Las comprobaciones automáticas se limitan a elecciones y números explícitos. Un argumento escrito necesita revisión humana.", "Automatic checks are limited to explicit choices and numbers. Written reasoning requires human review.",
       "Resuelve una situación nueva sin pista y explica la regla que aplicaste.", "Solve a new situation without a hint and explain the rule you applied.",
       "La aplicación no certifica formación doctoral ni deduce comprensión de la longitud del texto. La eficacia educativa debe medirse con estudiantes y evaluación independiente.", "The application does not certify doctoral training or infer understanding from text length. Educational efficacy requires students and independent assessment.", "competencies"),
      chapter("defence", "11 - Defender, revisar y mejorar", "11 - Defend, review and improve",
       "Conservar un razonamiento revisable y una segunda versión trazable.", "Keep reviewable reasoning and a traceable second version.",
       ["Completa objetivo, física, diseño, procesado, incertidumbre, controles y conclusión.", "Pulsa Guardar una nueva entrega. Exportar expediente conserva investigación, evidencias y entregas.", "El docente usa los cinco criterios 0-4, cita evidencias, escribe comentarios/preguntas y pulsa Crear y exportar devolución.", "El alumno utiliza Importar devolución, responde a las preguntas y guarda otra entrega sin sustituir la primera."],
       ["Complete objective, physics, design, processing, uncertainty, controls and conclusion.", "Press Save a new submission. Export portfolio preserves the investigation, evidence and submissions.", "The instructor uses five 0-4 criteria, cites evidence, writes comments/questions and presses Create and export feedback.", "The student uses Import feedback, responds to questions and saves another submission without replacing the first."],
       "Las devoluciones se vinculan a una entrega concreta y su identidad; una revisión de otro caso no debe convertirse en su evaluación.", "Feedback is linked to a specific submission and identity; another case's review must not become its assessment.",
       "Tu segunda versión explica qué cambiaste, qué evidencia te convenció y qué permanece sin resolver.", "Your second version explains what changed, which evidence persuaded you and what remains unresolved.",
       "La puntuación y el juicio son del docente. Las verificaciones de integridad no autentican la identidad civil del evaluador ni sustituyen un sistema institucional de notas.", "Scores and judgment are the instructor's. Integrity checks do not authenticate civil identity or replace an institutional grade system.", "defence"),
      chapter("library", "12 - Trabajar con originales públicos", "12 - Work with public originals",
       "Procesar experimentos reales y reconocer cuándo falta información para inferir D.", "Process real experiments and recognize missing information needed for D inference.",
       ["Abre Datos públicos y selecciona una adquisición PMA1, PMA6, PMMA1 o PMMA6. Cada grupo incluye dos adquisiciones del repositorio.", "La carga comprueba bytes y SHA-256 antes de interpretar FID y metadatos. Inspecciona programa, temperatura guardada, filtro digital, NS y RG.", "Ajusta fase, apodización y ventana; pulsa Procesar serie pública. Proporciona un b por adquisición y documenta su procedencia antes de ajustar.", "Pulsa Continuar la investigación con estas integrales para vincularlas al caso. Documenta qué condiciones permiten comparar las dos adquisiciones."],
       ["Open Public data and select a PMA1, PMA6, PMMA1 or PMMA6 acquisition. Each group has two repository acquisitions.", "Loading checks bytes and SHA-256 before interpreting FIDs/metadata. Inspect program, saved temperature, digital filter, NS and RG.", "Set phase, apodization and window; press Process public series. Supply one b per acquisition and its provenance before fitting.", "Press Continue investigation with these integrals to attach them to the case. Document which conditions permit comparison of the two acquisitions."],
       "Los ocho conjuntos proceden del depósito Monash/Figshare de Silva, McKay y Junkers, CC BY 4.0. Las condiciones guardadas no acreditan por sí solas controles de temperatura o convección.", "The eight datasets come from Silva, McKay and Junkers' Monash/Figshare repository, CC BY 4.0. Saved conditions alone do not establish temperature or convection controls.",
       "Distingue ausencia de b verificados, escala nominal, calibración absoluta y una D condicional al procesado.", "Distinguish missing verified b, nominal scale, absolute calibration and a D conditional on processing.",
       "Estos ocho conjuntos no aportan parámetros DOSY guardados suficientes para justificar automáticamente b. No inventes ese eje ni una D verdadera o masa absoluta.", "These eight datasets do not supply sufficient saved DOSY parameters to justify b automatically. Do not invent this axis, a true D or absolute molar mass.", "library"),
      chapter("example1", "Ejemplo continuo - preparar y adquirir", "Continuous example - prepare and acquire",
       "Reproducir una investigación sintética con parámetros y salidas verificables.", "Reproduce a synthetic investigation with checkable parameters and outputs.",
       [f"En La pregunta, selecciona Fallos combinados y semilla {example['seed']}; crea el caso {example['id']}.", f"El primer nulo de 180° es {f(example['firstNullUs'])} µs y el máximo anterior está en {f(example['p90Us'])} µs. Introduce P90={f(example['p90Us'])} µs.", f"Usa D_ref=1.9×10⁻⁹ m²/s a 298.15 K. La curva nominal ajusta D={f(example['referenceFitD'])} m²/s: s=√(D_nominal/D_ref)={f(example['gradientScale'])}.", "Introduce esa escala, ambas temperaturas 298.15 K y aplica la calibración. Diseña STE: δ=2 ms, Δ=80 ms, LED=5 ms, g_max=0.3 T/m, 20 niveles, NS=8, una réplica, reciclado=2 s, orden ascendente y presupuesto=15 min.", f"Comprueba duración aproximada {example['durationSeconds']/60:.3f} min y b_max={f(example['maxB'])} s/m²; adquiere la serie virtual."],
       [f"Under The question, choose Combined faults and seed {example['seed']}; create case {example['id']}.", f"The first 180° null is {f(example['firstNullUs'])} µs and the preceding maximum is at {f(example['p90Us'])} µs. Enter P90={f(example['p90Us'])} µs.", f"Use D_ref=1.9×10⁻⁹ m²/s at 298.15 K. The nominal curve fits D={f(example['referenceFitD'])} m²/s: s=√(D_nominal/D_ref)={f(example['gradientScale'])}.", "Enter this scale, both temperatures 298.15 K, and apply calibration. Design STE: δ=2 ms, Δ=80 ms, LED=5 ms, g_max=0.3 T/m, 20 levels, NS=8, one replicate, recycle=2 s, ascending order and a 15 min budget.", f"Check duration approximately {example['durationSeconds']/60:.3f} min and b_max={f(example['maxB'])} s/m²; acquire the virtual series."],
       "Los valores se calculan con el motor que acompaña a esta edición. Las cifras mostradas están redondeadas; la exportación conserva la precisión disponible.", "Values are computed by the engine shipped with this edition. Displayed figures are rounded; export retains available precision.",
       "Compara el ejemplo con escala g=1 en una copia exportada, manteniendo el resto de decisiones.", "Compare against g scale=1 in an exported copy while keeping other decisions fixed.",
       "Este ejemplo no proporciona parámetros de operación para tu espectrómetro ni un resultado experimental aceptado.", "This example is not an operating prescription for your spectrometer or an accepted experimental result."),
      chapter("example2", "Ejemplo continuo - interpretar y cuestionar", "Continuous example - interpret and challenge",
       "Llegar a un resultado reproducible que todavía exige controles.", "Reach a reproducible result that still needs controls.",
       ["Procesa con fase=0°, offset=0, LB=0 Hz y ventana Todo el espectro. Ajusta Monoexponencial con los mismos datos.", f"El ejemplo devuelve D≈{f(example['D'])} m²/s y RMS residual≈{f(example['residualRms'])}. Una cifra reproducible no convierte la mezcla/fallo combinado en una especie única.", "Propaga 40 muestras Monte Carlo: SD relativa g=0.02, SD T=0.3 K, procesado=0.01, ruido=0.01 y escala b de secuencia=0.01.", f"El intervalo condicional ilustrativo es [{f(example['interval95'][0])}, {f(example['interval95'][1])}] m²/s. Compara las contribuciones antes de decidir qué reducir.", "Predice el efecto de Invertir el orden y observa el control reservado. Escribe qué explica y qué no explica la diferencia, y prepara una entrega."],
       ["Process with phase=0°, offset=0, LB=0 Hz and Whole spectrum window. Fit Monoexponential to the same data.", f"The example returns D≈{f(example['D'])} m²/s and residual RMS≈{f(example['residualRms'])}. A reproducible number does not turn combined faults/a mixture into one species.", "Propagate 40 Monte Carlo draws: relative g SD=0.02, T SD=0.3 K, processing=0.01, noise=0.01 and sequence b-scale=0.01.", f"The illustrative conditional interval is [{f(example['interval95'][0])}, {f(example['interval95'][1])}] m²/s. Compare contributions before choosing what to reduce.", "Predict the effect of Reverse order and observe the held-out control. Write what the difference explains and does not explain, then prepare a submission."],
       "El ejemplo muestra por qué una estimación, su incertidumbre y una explicación causal son objetos distintos.", "The example shows why an estimate, its uncertainty and a causal explanation are different objects.",
       "Prueba otra semilla sin copiar estos valores: la justificación debe sobrevivir al cambio de muestra.", "Try another seed without copying these values: the justification should transfer to the new sample.",
       "Si cambias versión, parámetros, procesado o semilla, no fuerces coincidencia con esta tabla. Guarda y explica la nueva identidad.", "After changing version, settings, processing or seed, do not force agreement with this table. Save and explain the new identity."),
      chapter("tutor", "Beatrix, fuentes y modos de respuesta", "Beatrix, sources and response modes",
       "Utilizar ayuda trazable sin sustituir tu predicción ni el cálculo.", "Use traceable help without replacing your prediction or calculation.",
       ["Escribe primero Predicción y motivo. Pulsa Pista siguiente para recibir ayuda gradual vinculada a la etapa.", "Introduce Tu pregunta y pulsa Consultar fuentes: la recuperación documental presenta pasajes revisados y referencias.", "En WPF, Preguntar al modelo local solicita la inferencia disponible con contexto acotado. Lee siempre la etiqueta de modo y distingue guía documental de texto generado.", "Comprueba cualquier número en el motor de cálculo y contrasta la respuesta con las fuentes citadas."],
       ["Enter Prediction and reason first. Use Next hint for progressive help linked to the stage.", "Enter Your question and press Consult sources: documentary retrieval returns reviewed passages and references.", "In WPF, Ask the local model requests available inference with bounded context. Always read the mode label and distinguish documentary guidance from generated text.", "Check numbers in the calculation engine and compare the answer with cited sources."],
       "La edición web usa guía documental, no ejecuta un LLM en PHP. En Windows sólo se usa un modelo cuyo manifiesto y evaluación CPU estén aprobados; en caso contrario se ofrece guía documental. Un candidato entrenado no se convierte automáticamente en el modelo activo.", "The web edition uses documentary guidance, not an LLM running in PHP. Windows uses a model only when its manifest and CPU evaluation are approved; otherwise documentary guidance is provided. A trained candidate does not automatically become the active model.",
       "Puedes señalar qué parte procede de una fuente, cuál del cálculo y cuál de una generación real.", "You can identify source text, calculated output and any actual generated text.",
       "Recuperación documental, entrenamiento ejecutado y modelo aprobado son estados distintos. La fluidez no valida una ecuación, calibración, asignación ni evaluación del alumno.", "Documentary retrieval, executed training and an approved model are different states. Fluency does not validate an equation, calibration, assignment or student assessment."),
      chapter("teacher", "Protocolo docente y evaluación independiente", "Instructor protocol and independent evaluation",
       "Comprobar si el recorrido mejora decisiones en situaciones nuevas.", "Determine whether the pathway improves decisions in new situations.",
       ["Antes del curso, reserva casos y preguntas de transferencia que no se usen para entrenar al tutor ni para seleccionar parámetros.", "Registra diagnóstico inicial, decisiones, pistas consultadas, predicciones y primera entrega.", "Dos docentes pueden revisar informes con la misma rúbrica, comparar desacuerdos y documentar la segunda versión.", "Realiza caso final diferente y revisión diferida. Compara física, controles, incertidumbre y calidad de la conclusión, no sólo respuestas de opción múltiple."],
       ["Before the course, reserve transfer cases/questions not used to train the tutor or select settings.", "Record the initial diagnostic, decisions, hints, predictions and first submission.", "Two instructors can review reports with the same rubric, compare disagreements and document the second version.", "Use a different final case and delayed review. Compare physics, controls, uncertainty and conclusion quality, not just multiple-choice answers."],
       "El panel de Competencias ejecuta el piloto local con consentimiento, casos inicial/final distintos y retención diferida. La revisión de argumentos es humana. Este manual no presenta resultados de una cohorte que no se ha evaluado.", "The Competencies panel runs the local pilot with consent, different initial/final cases and delayed retention. Argument review is human. This manual does not claim results from a cohort that has not been evaluated.",
       "Define por adelantado qué mejora sería relevante y conserva también fallos y resultados negativos.", "Predefine a meaningful improvement and retain failures and negative results too.",
       "Las pruebas de software verifican comportamiento informático y controles sintéticos. No sustituyen revisión experta ni evaluación educativa independiente.", "Software checks establish computational behavior and synthetic controls. They do not replace expert review or independent educational evaluation.", "pilot"),
      chapter("files", "Guardar, importar y reproducir", "Save, import and reproduce",
       "Conservar evidencia sin confundir estado local, originales y resultados.", "Preserve evidence while distinguishing local state, originals and results.",
       ["Exportar investigación/expediente produce JSON de la versión 1.3: muestra, decisiones, resultados, aprendizaje y entregas. El expediente de interfaz omite los FID brutos: conserva los originales por separado.", "Importar investigación restaura un expediente compatible. Para reprocesar, vuelve a cargar la serie original o readquiere la simulación reproducible. Importar devolución exige una entrega correspondiente y verificación de su identidad.", "La importación CSV requiere pares b/señal finitos y unidades correctas. Una procedencia local sin verificar no adquiere licencia ni calibración por importarse.", "Para reproducir, registra versión, semilla o hashes, parámetros, fuentes b, operaciones de procesado, método y controles. Guarda el expediente fuera de la caché del navegador."],
       ["Export investigation/portfolio produces version 1.3 JSON: sample, decisions, results, learning and submissions. The interface portfolio omits raw FIDs: keep originals separately.", "Import investigation restores a compatible portfolio. To reprocess, reload original series or reacquire the reproducible simulation. Import feedback requires a matching submission and identity checks.", "CSV import requires finite b/signal pairs and correct units. Importing an unverified local source does not create a license or calibration.", "For reproduction, record version, seed or hashes, settings, b sources, processing, method and controls. Keep the portfolio outside browser cache."],
       "El almacenamiento es local. Cambiar de navegador, limpiar caché o usar otro perfil puede cambiar el progreso visible; la exportación es la copia transportable.", "Storage is local. Browser changes, cache clearing or another profile can change visible progress; export is the portable copy.",
       "Abre una exportación en una sesión aislada y comprueba identidad y resultados antes de dar por terminada una entrega.", "Open an export in an isolated session and check identity/results before considering a submission complete.",
       "Los JSON tienen límites de tamaño y compatibilidad. No edites hashes para forzar una importación. La web no sincroniza notas ni datos con una cuenta docente.", "JSON has size/compatibility limits. Do not edit hashes to force import. The web does not synchronize notes/data to an instructor account."),
      chapter("sources", "Fuentes, enlaces y problemas frecuentes", "Sources, links and common problems",
       "Encontrar la ecuación, el dato y la ayuda que corresponden a cada afirmación.", "Find the equation, dataset and support relevant to each claim.",
       ["Sinnaeve (2012), DOI 10.1002/cmr.a.21223, y Kuchel et al. (2012), DOI 10.1002/cmr.a.21241: fuentes del recorrido matemático. Consulta los 20 capítulos de Derivaciones para símbolos, páginas, ecuaciones y supuestos.", "Torrey (1956), DOI 10.1103/PhysRev.104.563: difusión en las ecuaciones de Bloch. Shrot, Shapira y Frydman (2004), DOI 10.1016/j.jmr.2004.08.001: codificación espacial continua.", "Silva, McKay y Junkers, DOI 10.26180/33075584.v1, CC BY 4.0: procedencia de los archivos experimentales públicos; conserva su atribución.", "Si faltan datos públicos, revisa acceso al paquete/versionado. Si falta b, documenta su derivación; si aparece aliasing, revisa malla/lectura. Ante un fallo de guardado, exporta antes de cerrar."],
       ["Sinnaeve (2012), DOI 10.1002/cmr.a.21223, and Kuchel et al. (2012), DOI 10.1002/cmr.a.21241, underpin the mathematical pathway. Use the 20 Derivations chapters for symbols, pages, equations and assumptions.", "Torrey (1956), DOI 10.1103/PhysRev.104.563: diffusion in Bloch equations. Shrot, Shapira and Frydman (2004), DOI 10.1016/j.jmr.2004.08.001: continuous spatial encoding.", "Silva, McKay and Junkers, DOI 10.26180/33075584.v1, CC BY 4.0: source of public experimental files; retain attribution.", "If public data are absent, check package/version access. If b is absent, document its derivation; for aliasing, review grid/readout. If saving fails, export before closing."],
       "Este manual complementa el manual doctoral y el curso original, que se mantienen disponibles con sus fuentes y convenciones explícitas.", "This manual supplements the retained doctoral manual and original course with their explicit sources and conventions.",
       "Toda conclusión final identifica datos, modelo, condiciones, incertidumbre y limitaciones.", "Every final conclusion identifies data, model, conditions, uncertainty and limitations.",
       "Un grupo de archivos, un buen ajuste o una captura atractiva no validan por sí solos una explicación física.", "A file group, good fit or attractive screenshot does not by itself validate a physical explanation."),
    ]


def register_fonts():
    fonts = Path(r"C:\Windows\Fonts")
    for name, file in [("Academy", "arial.ttf"), ("AcademyBold", "arialbd.ttf"), ("AcademyItalic", "ariali.ttf")]:
        pdfmetrics.registerFont(TTFont(name, str(fonts / file)))
    pdfmetrics.registerFontFamily("Academy", normal="Academy", bold="AcademyBold", italic="AcademyItalic", boldItalic="AcademyBold")


def styles():
    s = getSampleStyleSheet()
    for key in s.byName:
        s[key].fontName = "Academy"
    s.add(ParagraphStyle(name="CoverKicker",fontName="AcademyBold",fontSize=11,leading=15,textColor=TEAL,spaceAfter=16))
    s.add(ParagraphStyle(name="CoverTitle",fontName="AcademyBold",fontSize=33,leading=38,textColor=BLUE,spaceAfter=18))
    s.add(ParagraphStyle(name="CoverSub",fontName="Academy",fontSize=14,leading=20,textColor=GREY,spaceAfter=20))
    s.add(ParagraphStyle(name="Chapter",fontName="AcademyBold",fontSize=22,leading=27,textColor=BLUE,spaceAfter=15,keepWithNext=True))
    s.add(ParagraphStyle(name="Lead",fontName="AcademyBold",fontSize=11.4,leading=16,textColor=TEAL,spaceAfter=13))
    s.add(ParagraphStyle(name="Text",fontName="Academy",fontSize=10.2,leading=14.2,textColor=BLUE,spaceAfter=8))
    s.add(ParagraphStyle(name="Small",fontName="Academy",fontSize=8.6,leading=11.5,textColor=GREY,spaceAfter=7))
    s.add(ParagraphStyle(name="Label",fontName="AcademyBold",fontSize=10.2,leading=14,textColor=TEAL,spaceBefore=8,spaceAfter=5,keepWithNext=True))
    s.add(ParagraphStyle(name="TOCLevel",fontName="Academy",fontSize=10.2,leading=18,leftIndent=0,firstLineIndent=0,textColor=BLUE))
    return s


class Pipeline(Flowable):
    def __init__(self, lang):
        Flowable.__init__(self);self.width=170*mm;self.height=70*mm;self.lang=lang
    def draw(self):
        c=self.canv
        words = (["Pregunta", "Calibración", "Adquisición", "Procesado", "Modelo", "Incertidumbre", "Control", "Defensa"] if self.lang=="es" else ["Question", "Calibration", "Acquisition", "Processing", "Model", "Uncertainty", "Control", "Defence"])
        w=39*mm;h=21*mm
        for i,text in enumerate(words):
            row=i//4;col=i%4;x=col*43*mm;y=(1-row)*33*mm
            c.setFillColor(TEAL if i in (0,7) else BLUE);c.roundRect(x,y,w,h,4*mm,stroke=0,fill=1)
            c.setFillColor(colors.white);c.setFont("AcademyBold",9);c.drawCentredString(x+w/2,y+h/2-3,text)
            if col<3:c.setFillColor(GREY);c.setFont("Academy",12);c.drawString(x+w+1*mm,y+h/2-3,">")


class ManualDoc(BaseDocTemplate):
    def __init__(self, filename, lang, **kwargs):
        self.manual_lang=lang
        super().__init__(filename,pagesize=A4,leftMargin=20*mm,rightMargin=20*mm,topMargin=23*mm,bottomMargin=20*mm,lang=lang,**kwargs)
        frame=Frame(self.leftMargin,self.bottomMargin,self.width,self.height,id="normal",leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
        self.addPageTemplates(PageTemplate(id="normal",frames=frame,onPage=self.draw_page))
    def draw_page(self,canvas,doc):
        canvas.saveState();canvas.setFillColor(BLUE);canvas.setFont("AcademyBold",8)
        canvas.drawString(20*mm, A4[1]-13*mm,"DiffAtOnce Academy / RESEARCH 1.3")
        canvas.setFillColor(TEAL);canvas.drawRightString(A4[0]-20*mm,A4[1]-13*mm,self.manual_lang.upper())
        canvas.setStrokeColor(colors.HexColor("#dce7e9"));canvas.line(20*mm,A4[1]-16*mm,A4[0]-20*mm,A4[1]-16*mm)
        canvas.setFont("Academy",8);canvas.setFillColor(GREY)
        canvas.drawString(20*mm,11*mm,"Formación y evidencia / Teaching and evidence")
        canvas.drawRightString(A4[0]-20*mm,11*mm,str(doc.page));canvas.restoreState()
    def afterFlowable(self,flowable):
        if isinstance(flowable,Paragraph) and flowable.style.name=="Chapter":
            text=flowable.getPlainText();key=getattr(flowable,"bookmark",text)
            self.canv.bookmarkPage(key);self.canv.addOutlineEntry(text,key,level=0,closed=False)
            self.notify("TOCEntry",(0,text,self.page,key))


def make_pdf(lang, blocks, example, capture_dir):
    st=styles();p=lambda text,style="Text":Paragraph(escape(clean(text)),st[style]);story=[]
    es=lang=="es";L=lambda a,b:a if es else b
    story.extend([Spacer(1,15*mm),p("DIFFATONCE ACADEMY / 1.3.0","CoverKicker"),p(L("De la pregunta\na la evidencia", "From question\nto evidence").replace("\n"," "),"CoverTitle"),p(L("Manual de investigación continua", "Continuous research manual"),"CoverSub"),p(L("Doce etapas, una misma muestra y decisiones que puedes defender.","Twelve stages, one sample and decisions you can defend."),"Lead"),Spacer(1,15*mm),Pipeline(lang),Spacer(1,10*mm),p(L("Ediciones WPF y web - Español", "WPF and browser editions - English"),"Text"),p("30 / 10 / 2026","Small"),p(L("Simulaciones docentes calculadas, originales públicos atribuidos y revisión humana. Los modelos y las inferencias mantienen sus condiciones explícitas.","Computed teaching simulations, attributed public originals and human review. Models and inferences retain explicit conditions."),"Text"),PageBreak()])
    title=p(L("Contenido y acceso", "Contents and access"),"Chapter");title.bookmark="contents";story.append(title)
    story.append(p(L("Web: abre Academy y selecciona Investigación. WPF: pulsa Investigación continua; cambia ES/EN desde la aplicación.","Web: open Academy and select Research. WPF: choose Research studio; change ES/EN in the application.")))
    story.append(Paragraph('<link href="https://diffatonce.com/academy" color="#087d78">diffatonce.com/academy</link> - <link href="https://diffatonce.com/en/academy" color="#087d78">English product page</link>',st["Small"]))
    story.append(p(L("Las doce etapas de la interfaz", "The twelve interface stages"),"Label"))
    story.append(p(" / ".join(f"{i:02d} {name}" for i,name in enumerate(NAV[lang],1)),"Small"))
    toc=TableOfContents();toc.levelStyles=[st["TOCLevel"]];story.append(toc);story.append(PageBreak())
    for block in blocks:
        heading=p(block["title"],"Chapter");heading.bookmark=block["id"];story.extend([heading,p(block["goal"],"Lead")])
        if block["figure"]:
            path=capture_dir/f"capture-{lang}-{block['figure']}.png"
            with PILImage.open(path) as image:iw,ih=image.size
            ratio=min((170*mm)/iw,(78*mm)/ih)
            story.append(Image(str(path),width=iw*ratio,height=ih*ratio,hAlign="CENTER"))
            story.append(p(L("Captura real de la interfaz compartida. Los pasos siguientes identifican los controles; amplía la imagen si necesitas inspeccionar etiquetas pequeñas.","Actual shared-interface capture. The steps below identify controls; zoom to inspect small labels."),"Small"))
        story.append(p(L("Qué hacer", "What to do"),"Label"))
        for i,text in enumerate(block["steps"],1):story.append(p(f"{i}. {text}"))
        story.extend([p(L("Qué significa", "What it means"),"Label"),p(block["meaning"]),p(L("Antes de continuar", "Before continuing"),"Label"),p(block["check"])])
        if block["caution"]:
            box=Table([[p(L("Límite: ","Limit: ")+block["caution"],"Small")]],colWidths=[166*mm]);box.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),LIGHT),("BOX",(0,0),(-1,-1),.5,colors.HexColor("#c5dfdf")),("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),5)]));story.append(Spacer(1,4*mm));story.append(box)
        if block["id"]=="sources":
            story.append(Spacer(1,5*mm))
            links=[("DOCTORAL_MANUAL_"+lang.upper()+".pdf",L("Manual doctoral conservado", "Retained doctoral manual")),("https://doi.org/10.1002/cmr.a.21223","Sinnaeve 2012"),("https://doi.org/10.1002/cmr.a.21241","Kuchel et al. 2012"),("https://doi.org/10.1103/PhysRev.104.563","Torrey 1956"),("https://doi.org/10.1016/j.jmr.2004.08.001","Shrot et al. 2004"),("https://doi.org/10.26180/33075584.v1","Monash / Figshare"),("https://creativecommons.org/licenses/by/4.0/","CC BY 4.0")]
            for url,label in links:story.append(Paragraph(f'<link href="{escape(url)}" color="#087d78">{escape(label)}</link>',st["Small"]))
        if block is not blocks[-1]:story.append(PageBreak())
    output=DOCS/f"RESEARCH_MANUAL_{lang.upper()}.pdf"
    doc=ManualDoc(str(output),lang,title=L("DiffAtOnce Academy 1.3 - Manual de investigación","DiffAtOnce Academy 1.3 - Research manual"),author="DiffAtOnce Academy",subject="Bilingual diffusion NMR training, research pathway and reproducible examples")
    doc.multiBuild(story)
    return output


def write_markdown(lang, blocks):
    es=lang=="es";L=lambda a,b:a if es else b
    out=[f"# DiffAtOnce Academy 1.3 - {L('Guía de investigación','Research guide')}","",L("Ediciones WPF y web. Esta guía complementa el curso original y el manual doctoral.","WPF and web editions. This guide supplements the original course and doctoral manual."),"",f"[Academy](https://diffatonce.com/{'' if es else 'en/'}academy)",""]
    for b in blocks:
        out += ["## "+b["title"],"",b["goal"],""]
        if b["figure"]:out += [f"[{L('Ver la captura real en el manual PDF','View the actual capture in the PDF manual')}](RESEARCH_MANUAL_{lang.upper()}.pdf)",""]
        out += [f"{i}. {text}" for i,text in enumerate(b["steps"],1)]
        out += ["",b["meaning"],"",f"**{L('Comprobación','Check')}:** {b['check']}",""]
        if b["caution"]:out += [f"**{L('Límite','Limit')}:** {b['caution']}",""]
    out += [f"[{'Manual doctoral' if es else 'Doctoral manual'}](DOCTORAL_MANUAL_{lang.upper()}.pdf)","","https://doi.org/10.1002/cmr.a.21223","https://doi.org/10.1002/cmr.a.21241","https://doi.org/10.1103/PhysRev.104.563","https://doi.org/10.1016/j.jmr.2004.08.001","https://doi.org/10.26180/33075584.v1",""]
    path=DOCS/f"RESEARCH_GUIDE_{lang.upper()}.md";path.write_text(clean("\n".join(out)),encoding="utf-8");return path


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--captures",type=Path,default=CAPTURES);parser.add_argument("--guides-only",action="store_true");args=parser.parse_args()
    QA.mkdir(parents=True,exist_ok=True);DOCS.mkdir(exist_ok=True)
    example=example_data();(QA/"worked-example.json").write_text(json.dumps(example,indent=2,ensure_ascii=False),encoding="utf-8")
    blocks={lang:chapters(lang,example) for lang in ("es","en")}
    for lang in blocks:write_markdown(lang,blocks[lang])
    if args.guides_only:
        print(json.dumps({"guidesWritten":2,"pdfGenerated":False}));return
    missing=[str(args.captures/f"capture-{lang}-{key}.png") for lang in ("es","en") for key in FIGURES if not (args.captures/f"capture-{lang}-{key}.png").is_file()]
    if missing:raise FileNotFoundError("Actual final UI captures required: "+", ".join(missing))
    register_fonts();records=[]
    assert [b["id"] for b in blocks["es"]]==[b["id"] for b in blocks["en"]]
    assert all(len(a["steps"])==len(b["steps"]) for a,b in zip(blocks["es"],blocks["en"]))
    font_characters=pdfmetrics.getFont("Academy").face.charToGlyph
    missing_glyphs=sorted({c for c in clean(str(blocks)) if ord(c)>=32 and ord(c) not in font_characters})
    assert not missing_glyphs,missing_glyphs
    for lang in ("es","en"):
        path=make_pdf(lang,blocks[lang],example,args.captures);reader=PdfReader(path);text="\n".join(page.extract_text() or "" for page in reader.pages)
        assert len(reader.pages)==22,(lang,len(reader.pages))
        assert all(term in text for term in NAV[lang]),lang
        assert len(reader.outline)>=20,lang
        assert str(example["seed"]) in text
        assert "10.26180/33075584.v1" in text
        assert "\ufffd" not in text and "\u25a0" not in text and "\x00" not in text,lang
        assert all(abs(float(page.mediabox.width)-A4[0])<1 and abs(float(page.mediabox.height)-A4[1])<1 for page in reader.pages)
        records.append({"path":str(path.relative_to(ROOT)),"pages":len(reader.pages),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"bytes":path.stat().st_size,"figures":len(FIGURES),"outlineEntries":len(reader.outline),"uriLinks":sum(1 for page in reader.pages for ann in page.get("/Annots",[]) if ann.get_object().get("/A",{}).get("/S")=="/URI")})
    source_files=[ACADEMY/"web"/name for name in ("research-journey.js","research-studio.js","learning-path.js","research-pilot-panel.js","spatial-encoding.js")]
    source_files += [ACADEMY/"content/research-library.json",ACADEMY/"content/research-tutor-knowledge.json"]
    report={"version":"1.3.0","passed":True,"visualReviewPending":True,"parallelChaptersVerified":len(blocks["es"]),"fontCoverageVerified":True,"scope":"PDF structure/text checks only; rendered-page review is separate.","documents":records,"captures":[{"path":str((args.captures/f"capture-{lang}-{key}.png").relative_to(ROOT)),"sha256":hashlib.sha256((args.captures/f"capture-{lang}-{key}.png").read_bytes()).hexdigest()} for lang in ("es","en") for key in FIGURES],"sourceFiles":[{"path":str(p.relative_to(ROOT)),"sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for p in source_files],"example":example}
    (QA/"manual-build-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8");print(json.dumps(records,indent=2))


if __name__=="__main__":main()
