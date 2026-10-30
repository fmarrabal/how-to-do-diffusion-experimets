"""Build and validate the additive bilingual Academy mathematical supplement.

No frozen course, source PDF, trained model, or experimental calibration is edited.
The builder is intentionally explicit: mathematical prose is reviewed source data,
not an automatic reconstruction of damaged PDF text.
"""
from __future__ import annotations
import argparse, hashlib, json, math, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'content' / 'derivations.json'
REVIEW = ROOT / 'research' / 'papers-20261005'
S, K = 'Sinnaeve2012', 'Kuchel2012'
GAMMA = 267522187.44

def bi(es, en): return {'es': es, 'en': en}
def refs(source, pages, equations):
    if isinstance(pages, int): pages = [pages]
    if isinstance(equations, str): equations = equations.split(',')
    start = 39 if source == S else 205
    return [{'sourceId': source, 'pages': pages, 'journalPages': [start+p-1 for p in pages], 'equations': [str(x) for x in equations]}]
def st(id, title_es, title_en, es, en, latex, plain, assume_es, assume_en, source, pages, equations, literal=None):
    x = {'id': id, 'title': bi(title_es,title_en), 'explanation': bi(es,en), 'equationLatex':latex,
         'equationPlain':plain, 'assumptions':bi(assume_es,assume_en), 'sourceRefs':refs(source,pages,equations)}
    if literal: x['notationNote'] = bi(*literal)
    return x
def ex(id, title_es, title_en, es, en, sol_es, sol_en, latex, parameters, source, pages, equations):
    return {'id':id,'title':bi(title_es,title_en),'problem':bi(es,en),'solution':bi(sol_es,sol_en),
            'equationLatex':latex,'parameters':parameters,'assumptions':bi('Ejercicio sintético; no constituye calibración experimental.','Synthetic exercise; not an experimental calibration.'),'sourceRefs':refs(source,pages,equations)}
def qu(id, es, en, options, correct, why_es, why_en, source, pages, equations):
    return {'id':id,'question':bi(es,en),'options':[bi(*x) for x in options], 'correctIndex':correct,
            'explanation':bi(why_es,why_en),'sourceRefs':refs(source,pages,equations)}
def ch(id, es, en, obj_es, obj_en, pre, steps, examples, pitfalls, questions, module_ids):
    return {'id':id,'title':bi(es,en),'objective':bi(obj_es,obj_en),'prerequisites':pre,
            'steps':steps,'examples':examples,'pitfalls':[bi(*p) for p in pitfalls],
            'questions':questions,'moduleIds':module_ids}

def build():
    chapters = []
    chapters.append(ch('units-probability','Unidades, azar y desplazamiento','Units, randomness and displacement',
      'Distinguir posición, desplazamiento, velocidad, fase y difusión antes de interpretar una atenuación.',
      'Distinguish position, displacement, velocity, phase and diffusion before interpreting attenuation.',[],[
      st('si-units','La ecuación debe ser adimensional','The exponent must be dimensionless',
        'El gradiente g es la pendiente espacial del campo, no un campo: T/m. δ y Δ se convierten de ms a s. γ angular se expresa en rad/(s·T); usar γ/2π en Hz/T sin introducir 2π cambia b en un factor4π². q=γ∫gdt tiene unidades m⁻¹; b=∫q²dt tiene s/m²; por ello Db es adimensional. El porcentaje gpz se transforma en gradiente físico mediante una calibración y la forma real del pulso.',
        'Gradient g is a spatial field slope, not a field: T/m. Convert δ and Δ from ms to s. Angular γ is in rad/(s·T); using γ/2π in Hz/T without 2π changes b by4π². q=γ∫gdt is in m⁻¹; b=∫q²dt is in s/m², so Db is dimensionless. A gpz percentage becomes a physical gradient through calibration and the actual pulse shape.',
        r'[q]=\mathrm{m}^{-1},\quad[b]=\mathrm{s\,m}^{-2},\quad[D]=\mathrm{m^2\,s}^{-1},\quad[Db]=1',
        'q:1/m; b:s/m²; D:m²/s; D*b: dimensionless.',
        'γ angular; gradiente lineal; unidades SI.','Angular γ; linear gradient; SI units.',S,[2,9,10],['1','26','31']),
      st('brownian-moments','Qué significa difusión','What diffusion means',
        'Para difusión libre unidimensional los incrementos tienen media cero, varianza2Ddt y son independientes. Sumar N incrementos da varianza2DNdt=2Dt: D describe dispersión estadística, no una velocidad dirigida. Con deriva uniforme v, la media es vt pero la varianza alrededor de la media sigue siendo2Dt. En tres dimensiones isotrópicas la media del cuadrado de la distancia es6Dt.',
        'For free one-dimensional diffusion, increments have zero mean, variance2Ddt and are independent. Summing N increments gives variance2DNdt=2Dt: D describes statistical spread, not directed speed. Uniform drift v adds mean vt while variance around the mean remains2Dt. Three-dimensional isotropic mean squared displacement is6Dt.',
        r'\langle z(t)-z(0)\rangle=vt,\quad\mathrm{Var}[z(t)-z(0)]=2Dt,\quad r_{\rm rms,3D}=\sqrt{6Dt}',
        'mean displacement=v*t; variance=2*D*t; 1D rms without drift=sqrt(2*D*t).',
        'Browniano libre, D y v constantes; no paredes ni intercambio.','Free Brownian motion; constant D and v; no walls or exchange.',K,7,[])
    ],[ex('rms','¿Cuánto se mueve una molécula?','How far does a molecule move?',
      'Para D=0.8×10⁻⁹m²/s y t=80ms, calcula el desplazamiento RMS sobre z.','For D=0.8×10⁻⁹m²/s and t=80ms, calculate the RMS displacement along z.',
      '√(2×0.8×10⁻⁹×0.080)=11.31µm. No es una distancia recorrida en línea recta ni un radio molecular.',
      '√(2×0.8×10⁻⁹×0.080)=11.31µm. This is neither straight-line path length nor molecular radius.',r'\sqrt{2Dt}=11.31\ \mu\mathrm m',{'D_m2_s':8e-10,'time_s':.08},K,7,[])],
    [('Confundir mT/m con T/m introduce un factor10⁶ en b.','Confusing mT/m with T/m introduces a factor10⁶ in b.'),('La amplitud de un mapaDOSY no determina por sí sola masa absoluta.','DOSY map amplitude alone does not determine absolute mass.')],
    [qu('units-check','Si g se duplica, ¿qué ocurre con b?','If g doubles, what happens to b?', [('Se duplica','It doubles'),('Se cuadruplica','It quadruples'),('No cambia','It stays unchanged')],1,'q es lineal en g y b integra q².','q is linear in g and b integrates q².',S,10,['31'])],['foundations','size-mass']))

    chapters.append(ch('fick-continuity','De conservación a Fick','From conservation to Fick',
      'Derivar la ecuación diferencial de difusión y separar difusión de transporte dirigido.',
      'Derive the diffusion differential equation and separate diffusion from directed transport.',['units-probability'],[
      st('conservation','Contar lo que entra y sale','Count what enters and leaves',
        'En un segmento dz, la diferencia entre el flujo que entra J(z) y el que sale J(z+dz) cambia la concentración c. Dividiendo por dz y tomando el límite se obtiene ∂tc=−∂zJ. La primera ley de Fick J=−D∂zc lleva a ∂tc=∂z(D∂zc); sólo si D es constante se reduce a D∂zzc.',
        'In a segment dz, the difference between incoming J(z) and outgoing J(z+dz) changes concentration c. Divide by dz and take the limit to obtain ∂tc=−∂zJ. Fick’s first law J=−D∂zc gives ∂tc=∂z(D∂zc); only constant D reduces this to D∂zzc.',
        r'\partial_t c=-\partial_zJ,\quad J=-D\partial_zc\quad\Rightarrow\quad\partial_tc=D\partial_z^2c',
        'conservation: dc/dt=−dJ/dz; J=−D*dc/dz; constant D: dc/dt=D*d²c/dz².',
        'Sin fuentes/sumideros; D constante para la última igualdad.','No sources/sinks; constant D for the last equality.',S,[6,7],['14','15']),
      st('advection','Añadir movimiento dirigido','Add directed motion',
        'Un flujo de velocidad v transporta Jadv=vc. Conservación da ∂tc=−∂z(vc). Para v uniforme, ∂tc=−v∂zc y la solución es c(z,t)=c(z−vt,0): el perfil se traslada sin ensancharse. Difusión y deriva juntas producen ∂tc=D∂zzc−v∂zc. Si v depende de z no se puede eliminar el término −c∂zv.',
        'Velocity v transports advective flux Jadv=vc. Conservation gives ∂tc=−∂z(vc). For uniform v, ∂tc=−v∂zc and c(z,t)=c(z−vt,0): the profile shifts without widening. Diffusion and drift together give ∂tc=D∂zzc−v∂zc. If v depends on z, the term −c∂zv cannot be discarded.',
        r'J_{\rm adv}=vc,\quad\partial_tc=D\partial_z^2c-v\partial_zc',
        'Jadv=v*c; dc/dt=D*d²c/dz²−v*dc/dz for constant v.',
        'v constante y flujo localmente laminar para esta forma.','Constant v and locally laminar flow for this form.',S,8,['16','17']),
      st('green-function','Resolver la difusión libre','Solve free diffusion',
        'Para una posición inicial puntual, transformar en Fourier convierte ∂tc=D∂zzc en ∂tĉ=−Dk²ĉ. Separar variables da ĉ=e^(−Dk²t); la transformada inversa es una gaussiana normalizada. Su integral es1 y su varianza2Dt. Con deriva se desplaza su centro a vt. Esta solución deja de valer cerca de fronteras reflectantes o absorbentes.',
        'For a point initial position, Fourier transformation turns ∂tc=D∂zzc into ∂tĉ=−Dk²ĉ. Separation gives ĉ=e^(−Dk²t); inverse transformation is a normalized Gaussian. Its integral is1 and variance2Dt. Drift shifts its center to vt. This solution fails near reflecting or absorbing boundaries.',
        r'P(z,t\mid0)=\frac{e^{-(z-vt)^2/(4Dt)}}{\sqrt{4\pi Dt}}',
        'P(z,t|0)=exp[−(z−v*t)²/(4*D*t)]/sqrt(4*pi*D*t).',
        'Dominio infinito, D>0 constante, condición inicial delta. Extensión docente derivada de Fick.','Infinite domain; constant D>0; delta initial condition. Teaching extension derived from Fick.',S,[7,8],['15','17'])
    ],[ex('conservation-example','Difusión no crea moléculas','Diffusion does not create molecules',
      '¿Por qué se conserva ∫c dz en un dominio cerrado?','Why is ∫c dz conserved in a closed domain?',
      'Integrar conservación da d(∫c dz)/dt=−J(derecha)+J(izquierda). Con flujo cero en ambas fronteras la derivada es cero.',
      'Integrating conservation gives d(∫c dz)/dt=−J(right)+J(left). Zero flux at both boundaries makes the derivative zero.',r'\frac{d}{dt}\int c\,dz=-[J]_{\rm boundaries}',{},S,[6,7],['14','15'])],
    [('No reemplazar ∂z(vc) por v∂zc si v varía espacialmente.','Do not replace ∂z(vc) by v∂zc when v varies in space.')],
    [qu('fick-question','¿Qué ensancha un perfil inicialmente estrecho?','What broadens an initially narrow profile?', [('Sólo deriva uniforme','Uniform drift alone'),('Difusión','Diffusion'),('Rotación RF ideal','Ideal RF rotation')],1,'D∂zzc redistribuye el perfil; −v∂zc uniforme lo traslada.','D∂zzc redistributes the profile; uniform −v∂zc translates it.',S,[7,8],['15','17'])],['foundations','convection']))

    chapters.append(ch('complex-magnetization','Magnetización compleja y precesión','Complex magnetization and precession',
      'Traducir una rotación física a una fase compleja y conservar la diferencia entre fase y módulo.',
      'Translate physical rotation into complex phase and preserve the distinction between phase and magnitude.',['units-probability'],[
      st('euler','Dos componentes, un número complejo','Two components, one complex number',
        'Representar Mx y My mediante M+=Mx+iMy permite escribir una rotación como multiplicación por exp(iφ). Euler separa sus partes cosφ+i sinφ. La relajaciónT2 multiplica por exp(−t/T2), que reduce el módulo; la precesión cambia la fase. Una rotación pura no puede generar por sí sola pérdida de módulo individual.',
        'Represent Mx and My as M+=Mx+iMy to write rotation as multiplication by exp(iφ). Euler separates cosφ+i sinφ. T2 relaxation multiplies by exp(−t/T2), reducing magnitude; precession changes phase. Pure rotation alone cannot reduce an individual spin’s magnitude.',
        r'M_+=M_x+iM_y=M_0e^{i\omega t-t/T_2}',
        'M+=Mx+iMy=M0*(cos(omega*t)+i*sin(omega*t))*exp(−t/T2).',
        'Precesión a ω constante, T2 uniforme y pulsoRF ya terminado.','Constant ω; uniform T2; RF pulse has ended.',K,3,['1','2','3','4']),
      st('rotating-frame','Quitar B0 y mantener la pendiente','Remove B0 and retain the slope',
        'El campo Bz=B0+g·r produce ω=−γBz. En un marco que gira con −γB0 sólo queda −γg·r. Por tanto un gradiente lineal convierte posición en frecuencia y, al integrarla en tiempo, en fase. El signo depende de la coherencia elegida; la atenuación libre depende de q² y permanece igual al invertir toda la codificación.',
        'Field Bz=B0+g·r gives ω=−γBz. A frame rotating with −γB0 leaves −γg·r. A linear gradient therefore converts position into frequency and, after time integration, phase. Sign depends on the selected coherence; free attenuation depends on q² and is unchanged by reversing the entire encoding.',
        r'B_z=B_0+\mathbf g\cdot\mathbf r,\quad\omega_R=-\gamma\mathbf g\cdot\mathbf r',
        'Bz=B0+g·r; rotating-frame omegaR=−gamma*g·r.',
        'Gradiente espacial lineal; marco giratorio; convención M+.','Spatially linear gradient; rotating frame; M+ convention.',K,3,['5','6','7']),
      st('phase-ode','Resolver la fase antes de añadir difusión','Solve phase before adding diffusion',
        'La ecuación local ∂tM=−iγg(t)zM es separable: dM/M=−iγzg(t)dt. Integrar produce M(z,t)=M(z,0)exp(−izq(t)), con q=γ∫gdt si no cambia la coherencia. El módulo es |M(z,0)|; la señal total puede caer por cancelación entre posiciones. En Kuchel[8] se imprimen barras de módulo alrededor de una expresión compleja: Academy usa M complejo y escribe el módulo por separado.',
        'The local equation ∂tM=−iγg(t)zM is separable: dM/M=−iγzg(t)dt. Integration gives M(z,t)=M(z,0)exp(−izq(t)), with q=γ∫gdt when coherence does not change. Magnitude is |M(z,0)|; total signal may fall through cancellation across positions. Kuchel[8] places magnitude bars around a complex expression: Academy keeps M complex and writes magnitude separately.',
        r'\frac{dM}{M}=-i\gamma zg(t)dt\Rightarrow M=M_0e^{-iz\gamma\int_0^tg(s)ds},\quad|M|=|M_0|',
        'dM/M=−i*gamma*z*g(t)*dt; M=M0*exp(−i*z*gamma*integral(g)); |M|=|M0|.',
        'Sin difusión ni RF dentro del intervalo; no confundir |M| con M.','No diffusion or RF within the interval; distinguish |M| from M.',K,3,['8','9','10','11','12','13','14','15'],
        ('[8] se usa como relación de fase, no como igualdad literal para el módulo.','[8] is used as a phase relation, not a literal equality for magnitude.'))
    ],[ex('phase-example','Rotación no es desaparición','Rotation is not disappearance',
      'Un espín adquiere faseπ. ¿Cuál es su módulo normalizado?','A spin acquires phaseπ. What is its normalized magnitude?',
      'exp(−iπ)=−1, cuyo módulo es1. Dos posiciones con fases0 yπ pueden sumar cero aunque cada espín conserve su módulo.',
      'exp(−iπ)=−1, with magnitude1. Two positions with phases0 andπ can sum to zero although each spin retains magnitude.',r'|e^{-i\pi}|=1,\quad1+e^{-i\pi}=0',{},K,3,['3','8','9'])],
    [('No interpretar una señal real negativa como una difusión negativa.','Do not interpret a negative real signal as negative diffusion.')],
    [qu('complex-question','¿Qué reduce |M| en la expresión de precesión conT2?','What reduces |M| in the precession expression withT2?', [('exp(iωt)','exp(iωt)'),('exp(−t/T2)','exp(−t/T2)'),('Cambiar el eje real','Changing the real axis')],1,'El factor de fase tiene módulo1.','The phase factor has unit magnitude.',K,3,['4'])],['phase-encoding','preprocessing']))

    chapters.append(ch('helix-fourier','Hélice de fase, Fourier y eco','Phase helix, Fourier and echo',
      'Entender cómo una señal desaparece por desfase y reaparece cuando se decodifica.',
      'Understand how a signal vanishes through dephasing and returns through decoding.',['complex-magnetization'],[
      st('helix','Posición convertida en vueltas','Position converted into turns',
        'Después de un gradiente constante duranteδ, la fase cambia linealmente con z. Un cambio de fase2π define el paso de la héliceΛ=2π/|q|. En longitudL caben |q|L/(2π) vueltas. Las componentes se mezclan mediante una matriz de rotación, conservando el módulo local. No es una hélice material ni una trayectoria molecular.',
        'After a constant gradient of durationδ, phase changes linearly with z. A2π phase change defines helix pitchΛ=2π/|q|. LengthL contains |q|L/(2π) turns. Components mix through a rotation matrix while local magnitude is conserved. This is neither a material helix nor a molecular path.',
        r'q=\gamma g\delta,\quad\Lambda=\frac{2\pi}{|q|},\quad N=\frac{|q|L}{2\pi}',
        'q=gamma*g*delta; pitch=2*pi/abs(q); turns=abs(q)*L/(2*pi).',
        'Espines inmóviles, gradiente lineal y sin relajación.','Stationary spins; linear gradient; no relaxation.',S,4,['3','4','5']),
      st('coil-integral','La bobina suma fases','The coil sums phases',
        'Para una muestra uniforme entre−L/2 yL/2, S(q) integra M0 exp(−iqz). La parte impar seno desaparece y ∫cos(qz)dz=2sin(qL/2)/q=L sinc(qL/2). Normalizando por S(0)=M0L resulta sinc(qL/2), con sinc(x)=sinx/x. Eq6 del PDF imprime L/2 en el prefactor; la integral escrita y el límite q→0 danL. Aquí se muestra la integral consistente y se registra la discrepancia literal.',
        'For a uniform sample between−L/2 andL/2, S(q) integrates M0 exp(−iqz). The odd sine part cancels and ∫cos(qz)dz=2sin(qL/2)/q=L sinc(qL/2). Normalize by S(0)=M0L to obtain sinc(qL/2), with sinc(x)=sinx/x. PDF Eq6 prints L/2 in the prefactor; the written integral and q→0 limit giveL. This lesson uses the consistent integral and records the literal discrepancy.',
        r'\frac{S(q)}{S(0)}=\frac1L\int_{-L/2}^{L/2}e^{-iqz}dz=\operatorname{sinc}(qL/2)',
        'S(q)/S(0)=sin(q*L/2)/(q*L/2); continuous limit at q=0 is1.',
        'Perfil y sensibilidad uniformes; límite estático. No representa atenuación de difusión en un eco balanceado.','Uniform profile and sensitivity; static limit. This is not diffusion attenuation at a balanced echo.',S,4,['6'],
        ('Prefactor literal de[6]: MyL/2; integral evaluada y normalizada: MyL.','Literal[6] prefactor: MyL/2; evaluated normalized integral: MyL.')),
      st('echo-closure','Deshacer fase estática','Undo static phase',
        'Un segundo gradiente efectivo con área igual y signo contrario deja q(T)=0. Cada posición inmóvil vuelve a su fase inicial: R(−φ)R(φ)=I. Un pulso180 cambia el signo de la coherencia, por lo que dos gradientes físicos del mismo signo pueden tener signos efectivos opuestos. Con movimiento aleatorio entre ellos no se recuperan todas las fases, y queda la atenuación que interesa medir.',
        'A second effective gradient with equal area and opposite sign leaves q(T)=0. Every stationary position returns to its initial phase: R(−φ)R(φ)=I. A180 pulse changes coherence sign, so two same-sign physical gradients may have opposite effective signs. Random motion between them prevents full phase recovery, leaving the attenuation of interest.',
        r'q(T)=0,\quad R(-\phi)R(\phi)=I',
        'balanced effective gradient area gives q(T)=0; inverse rotations recover static spins.',
        'RF ideal y áreas efectivas iguales; no movimiento para el eco completo.','Ideal RF and matched effective areas; no motion for complete echo.',S,[5,7],['7'])
    ],[ex('closure-example','Un desfase residual puede imitar pérdida','Residual dephasing can imitate loss',
      'Si q(T)L/2=π, ¿qué predice la suma estática uniforme?','If q(T)L/2=π, what does the uniform static sum predict?',
      'sinc(π)=0 aunque D=0. Antes de atribuir una pérdida a difusión debe comprobarse cierre de q(T).',
      'sinc(π)=0 even when D=0. Verify q(T) closure before attributing loss to diffusion.',r'\operatorname{sinc}(\pi)=0',{'qT_L_over2':math.pi},S,[4,5],['6','7'])],
    [('Desfase estático reversible, difusión y relajación son mecanismos diferentes.','Reversible static dephasing, diffusion and relaxation are different mechanisms.')],
    [qu('helix-question','¿Qué área debe balancearse para formar eco?','Which area must balance to form an echo?', [('Sólo el gradiente físico','Only physical gradient'),('Gradiente ponderado por coherencia','Coherence-weighted gradient'),('El cuadrado del gradiente','Gradient squared')],1,'RF cambia p; q integra pγg y debe cerrar.','RF changes p; q integrates pγg and must close.',S,9,['26'])],['phase-encoding','sequence-b']))

    chapters.append(ch('propagator','De probabilidad a atenuación','From probability to attenuation',
      'Derivar la exponencial de difusión como promedio de fases, en vez de memorizarla.',
      'Derive diffusion attenuation as a phase average rather than memorizing it.',['fick-continuity','helix-fourier'],[
      st('phase-average','Promediar desplazamientos','Average over displacements',
        'Con pulsos idealmente estrechos, el primer pulso etiqueta z0 y el segundo lee z1. La fase residual es q0(z1−z0), con signo global dependiente de convención. El eco normalizado es la función característica del desplazamiento: E=∫P(ζ,Δ)exp(iq0ζ)dζ. No se promedian valores absolutos de cada espín: se suman sus números complejos.',
        'With ideally narrow pulses, the first labels z0 and the second reads z1. Residual phase is q0(z1−z0), up to a convention-dependent global sign. Normalized echo is the displacement characteristic function E=∫P(ζ,Δ)exp(iq0ζ)dζ. Individual absolute magnitudes are not averaged; complex amplitudes are summed.',
        r'E(q_0,\Delta)=\int P(\zeta,\Delta)e^{iq_0\zeta}d\zeta',
        'E=integral(P(displacement,Delta)*exp(i*q0*displacement)).',
        'Pulsos estrechos; misma población; distribución inicial y sensibilidad adecuadas. Extensión docente.','Narrow pulses; same population; suitable initial distribution and sensitivity. Teaching extension.',K,7,[]),
      st('gaussian-transform','Calcular el promedio gaussiano','Calculate the Gaussian average',
        'Completar el cuadrado en −(ζ−vΔ)²/(4DΔ)+iq0ζ, o usar la transformada de la gaussiana, da E=exp(−Dq0²Δ)exp(ivq0Δ). La media produce fase y la varianza produce atenuación. La mitad de la varianza de fase esDq0²Δ. Un decaimiento gaussiano en g no prueba por sí solo ausencia de convección: otra distribución de velocidades puede añadir un factor parecido.',
        'Complete the square in −(ζ−vΔ)²/(4DΔ)+iq0ζ, or use the Gaussian transform, to obtain E=exp(−Dq0²Δ)exp(ivq0Δ). Mean creates phase and variance creates attenuation. Half of phase variance isDq0²Δ. Gaussian decay in g alone does not prove absence of convection: another velocity distribution may add a similar factor.',
        r'E=e^{-Dq_0^2\Delta}e^{ivq_0\Delta},\quad\operatorname{Var}(\phi)=2Dq_0^2\Delta',
        'E=exp(−D*q0²*Delta)*exp(i*v*q0*Delta); phase variance=2*D*q0²*Delta.',
        'Difusión gaussiana libre; deriva uniforme; límite de pulsos estrechos.','Free Gaussian diffusion; uniform drift; narrow-pulse limit.',S,[10,17],['31','59']),
      st('finite-warning','Por qué δ no desaparece','Why δ does not disappear',
        'El desplazamiento ocurre mientras ambos gradientes están activos. Por ello el valor q no salta instantáneamente a q0: crece, permanece y decrece. Integrar esa historia cambia Δ a una corrección de tiempo dependiente de la forma y de la secuencia. La fórmula de pulsos estrechos es un límite, no una ecuación universal.',
        'Displacement occurs while both gradients are active. Thus q does not jump instantly to q0: it grows, holds and decreases. Integrating this history replaces Δ with a shape- and sequence-dependent timing correction. The narrow-pulse formula is a limit, not a universal equation.',
        r'b=\int_0^Tq(t)^2dt\ne q_0^2\Delta\quad\text{for finite pulses}',
        'For finite pulses integrate q(t)²; do not assume b=q0²*Delta.',
        'Gradientes finitos; forma real conocida.','Finite gradients; actual shape known.',S,[11,12],['36','41','42','43'])
    ],[ex('gaussian-example','Decaimiento por varianza de fase','Decay from phase variance',
      'Si la varianza de fase es2rad² y la media es0, calcula E.','If phase variance is2rad² and mean is0, calculate E.',
      'E=exp(−2/2)=0.3679. No se necesita una pérdida de espines para que el promedio complejo sea menor que1.',
      'E=exp(−2/2)=0.3679. No loss of spins is needed for the complex average to be below1.',r'E=e^{-\operatorname{Var}(\phi)/2}=e^{-1}',{'phaseVariance':2},S,10,['31'])],
    [('El promedio de módulos sería1 en este límite y borraría la información de difusión.','Averaging magnitudes would give1 in this limit and erase diffusion information.')],
    [qu('propagator-question','¿Qué propiedad produce atenuación en el caso gaussiano?','Which property produces attenuation in the Gaussian case?', [('La varianza de fase','Phase variance'),('Sólo la fase media','Only mean phase'),('El color del mapa','Map color')],0,'La media desplaza fase; la varianza reduce el promedio complejo.','Mean shifts phase; variance reduces the complex average.',S,10,['31'])],['foundations','phase-encoding']))

    chapters.append(ch('bloch-torrey','Bloch–Torrey: la ecuación diferencial completa','Bloch–Torrey: the complete differential equation',
      'Construir la ecuación de magnetización a partir de precesión, relajación, difusión y deriva.',
      'Build the magnetization equation from precession, relaxation, diffusion and drift.',['fick-continuity','complex-magnetization'],[
      st('master-equation','Añadir cada mecanismo','Add each mechanism',
        'La magnetización viaja con las moléculas, por lo que hereda D∂zzM−v∂zM. La componente transversal precesa y relaja: (iΩ0−1/T2)M+−iγg(t)zM+. La longitudinal vuelve al equilibrio con (Mz0−Mz)/T1. Entre pulsosRF se suman estos términos lineales. DuranteRF debe incluirse el Hamiltoniano/rotación deRF; no es correcto aplicar sin más la ecuación de evolución libre a un pulso finito.',
        'Magnetization travels with molecules and inherits D∂zzM−v∂zM. Transverse magnetization precesses and relaxes: (iΩ0−1/T2)M+−iγg(t)zM+. Longitudinal magnetization returns to equilibrium through (Mz0−Mz)/T1. Between RF pulses these linear terms add. During RF, include the RF Hamiltonian/rotation; the free-evolution equation cannot simply be applied to a finite RF pulse.',
        r'\partial_tM_+=(i\Omega_0-T_2^{-1})M_+-i\gamma g(t)zM_++D\partial_z^2M_+-v\partial_zM_+;\quad\partial_tM_z=(M_{z0}-M_z)/T_1+D\partial_z^2M_z-v\partial_zM_z',
        'dM+/dt=(i*Omega0−1/T2)*M+−i*gamma*g(t)*z*M++D*d²M+/dz²−v*dM+/dz; dMz/dt=(Mz0−Mz)/T1+D*d²Mz/dz²−v*dMz/dz.',
        'D,v,T1,T2 uniformes; gradiente lineal; evolución libre entreRF; sin paredes/intercambio.','Uniform D,v,T1,T2; linear gradient; free evolution between RF; no walls/exchange.',S,8,['18']),
      st('remove-relaxation','Factorizar lo que no depende de z','Factor out what does not depend on z',
        'Escribir M+=Ψ+exp[(iΩ0−1/T2)t] y Mz=Mz0−(Mz0−Ψz)exp(−t/T1). Sustituir y derivar con regla del producto cancela offset y relajación uniformes. Queda ∂tΨ+=−iγg(t)zΨ++D∂zzΨ+−v∂zΨ+; longitudinalmente no hay fase de gradiente, pero sí difusión de la modulación almacenada. Si T2 o población cambian con el gradiente, normalizar no elimina esa dependencia.',
        'Write M+=Ψ+exp[(iΩ0−1/T2)t] and Mz=Mz0−(Mz0−Ψz)exp(−t/T1). Substitute and differentiate by the product rule to cancel uniform offset and relaxation. The remaining transverse equation is ∂tΨ+=−iγg(t)zΨ++D∂zzΨ+−v∂zΨ+; longitudinally there is no gradient phase but stored modulation still diffuses. If T2 or population changes with gradient, normalization does not remove that dependence.',
        r'M_+=\Psi_+e^{(i\Omega_0-1/T_2)t}\Rightarrow\partial_t\Psi_+=-i\gamma g(t)z\Psi_++D\partial_z^2\Psi_+-v\partial_z\Psi_+',
        'Factor uniform offset/relaxation; remaining PDE contains gradient phase+diffusion+advection.',
        'T1,T2,offset constantes dentro de cada intervalo; tratar cambios de coherencia por separado.','Constant T1,T2,offset within each interval; handle coherence changes separately.',S,9,['19','20']),
      st('three-dimensional','Laplaciano y condiciones iniciales','Laplacian and initial conditions',
        'En tres dimensiones la difusión isotrópica usa D∇²M. Una ecuación diferencial necesita condición inicial y, en dominio finito, condiciones de frontera. La solución exponencial libre supone una modulación inicial uniforme multiplicada por una onda de fase y desplazamientos pequeños frente a las paredes. Un dominio restringido exige resolver otra ecuación de frontera; un tensor de difusión exige ∇·(D∇M).',
        'In three dimensions isotropic diffusion uses D∇²M. A differential equation requires an initial condition and, on a finite domain, boundary conditions. The free exponential solution assumes initially uniform amplitude times a phase wave and displacements small relative to walls. Restricted domains require a different boundary problem; a diffusion tensor requires ∇·(D∇M).',
        r'\partial_t\Psi=-i\gamma\mathbf g(t)\cdot\mathbf r\Psi+D\nabla^2\Psi',
        '3D isotropic: dPsi/dt=−i*gamma*g(t)·r*Psi+D*laplacian(Psi).',
        'Difusión isotrópica libre; ecuación deKuchel sin deriva.','Free isotropic diffusion; Kuchel equation without drift.',K,4,['16','17'])
    ],[ex('bt-static','Desactivar términos para comprobar signos','Switch off terms to check signs',
      'Pon D=v=0 y g constante en la ecuación reducida. ¿Qué solución queda?','Set D=v=0 and constant g in the reduced equation. What solution remains?',
      'Ψ=Ψ0exp(−iγgzt); su derivada temporal reproduce −iγgzΨ. Para g=0 queda la ecuación de difusión/deriva deFick.',
      'Ψ=Ψ0exp(−iγgzt); its time derivative gives −iγgzΨ. For g=0 the Fick diffusion/drift equation remains.',r'\Psi(z,t)=\Psi_0e^{-i\gamma gzt}',{},S,[8,9],['18','20','25'])],
    [('No añadir un gradiente de difusión directamente al parámetroD; es un término de fase.','Do not add a diffusion gradient directly to D; it is a phase term.')],
    [qu('bt-question','¿Qué término describe movimiento aleatorio?','Which term describes random motion?', [('−iγgzΨ','−iγgzΨ'),('D∂zzΨ','D∂zzΨ'),('−Ψ/T2','−Ψ/T2')],1,'El laplaciano genera dispersión espacial; los otros términos son fase y relajación.','The Laplacian generates spatial spreading; the other terms describe phase and relaxation.',S,8,['18'])],['foundations','sequence-b','convection']))

    chapters[0]['steps'].append(st('forward-model','La pregunta inversa empieza por el modelo directo','The inverse question starts with the forward model',
      'El modelo directo predice una señal si D y la secuencia se conocen: E=exp(−Db). En la presentación general E=exp[−Dγeff²δ²σ²g²Δeff], γeff corresponde a las coherencias participantes, σ al área de forma y Δeff a la corrección de tiempo. El problema inverso calcula D a partir de muchas señales y sus b conocidos. Esta factorización sólo sirve si b es proporcional a g²; gradientes adicionales pueden introducir términos cruzados.',
      'The forward model predicts signal when D and sequence are known: E=exp(−Db). In the general presentation E=exp[−Dγeff²δ²σ²g²Δeff], γeff refers to participating coherences, σ to shape area and Δeff to the timing correction. The inverse problem infers D from multiple signals and known b values. This factorization only applies when b is proportional to g²; additional gradients may introduce cross terms.',
      r'E=e^{-Db},\quad b=\gamma_{\rm eff}^2\delta^2\sigma^2g^2\Delta_{\rm eff}',
      'E=exp(−D*b); for a suitable family b=gammaEff²*delta²*sigma²*g²*DeltaEff.',
      'Difusión libre monoexponencial; Δeff deriva de la secuencia, no se identifica sin comprobar con d20.','Free monoexponential diffusion; derive DeltaEff from the sequence, do not identify it with d20 without checking.',S,2,['1']))
    chapters[2]['steps'][1]['sourceRefs'] += refs(S,3,['2'])
    fourier_steps=[
      st('fourier-convention','Definir ambas transformadas','Define both transforms',
        'Usamos Ĉ(k,t)=∫c(z,t)e^(−ikz)dz y c(z,t)=(1/2π)∫Ĉ(k,t)e^(ikz)dk. Con c y ∂zc nulos en los extremos infinitos, integrar por partes dos veces da F[∂zzc]=−k²Ĉ. F[∂zc]=ikĈ. Por tanto Fick con deriva se convierte en ∂tĈ=−(Dk²+ivk)Ĉ. Cada k tiene su propia ecuación diferencial ordinaria.',
        'Use Ĉ(k,t)=∫c(z,t)e^(−ikz)dz and c(z,t)=(1/2π)∫Ĉ(k,t)e^(ikz)dk. When c and ∂zc vanish at infinity, two integrations by parts give F[∂zzc]=−k²Ĉ. F[∂zc]=ikĈ. Fick with drift therefore becomes ∂tĈ=−(Dk²+ivk)Ĉ. Each k has its own ordinary differential equation.',
        r'\widehat c(k,t)=\int c(z,t)e^{-ikz}dz,\quad c=\frac1{2\pi}\int\widehat c e^{ikz}dk;\quad\widehat{\partial_z^2c}=-k^2\widehat c',
        'Forward Fourier exp(−i*k*z), inverse exp(+i*k*z)/(2*pi); derivative→i*k, second derivative→−k².',
        'Funciones integrables, fronteras infinitas sin términos de borde; extensión matemática docente.','Integrable functions; no boundary terms at infinity; mathematical teaching extension.',S,[7,8],['15','17']),
      st('fourier-ode','Separar variables para cada frecuencia espacial','Separate variables for each spatial frequency',
        'Dividir por Ĉ y mantener k fijo: dĈ/Ĉ=−(Dk²+ivk)dt. Integrar entre0 y t da ln[Ĉ(k,t)/Ĉ(k,0)]=−Dk²t−ivkt. Para una delta inicial en z=0, Ĉ(k,0)=1. Así Ĉ=e^(−Dk²t)e^(−ivkt). El signo de la deriva queda comprobado porque la transformada inversa desplaza z a z−vt.',
        'Divide by Ĉ at fixed k: dĈ/Ĉ=−(Dk²+ivk)dt. Integrating from0 to t gives ln[Ĉ(k,t)/Ĉ(k,0)]=−Dk²t−ivkt. A delta initial condition at z=0 has Ĉ(k,0)=1. Thus Ĉ=e^(−Dk²t)e^(−ivkt). Drift sign is checked because inversion shifts z to z−vt.',
        r'\int_{\widehat c_0}^{\widehat c}\frac{dC}{C}=-(Dk^2+ivk)t\Rightarrow\widehat c=\widehat c_0e^{-Dk^2t-ivkt}',
        'At fixed k: dC/C=−(D*k²+i*v*k)*dt; C=C0*exp[−D*k²*t−i*v*k*t].',
        'D y v constantes; solución de cada modo espacial, no ajuste de datos.','Constant D and v; solution of each spatial mode, not a data fit.',S,[7,8],['15','17']),
      st('gaussian-inverse','Evaluar la transformada inversa gaussiana','Evaluate the Gaussian inverse transform',
        'Con x=z−vt, el exponente es−Dtk²+ikx=−Dt[k−ix/(2Dt)]²−x²/(4Dt). La integral gaussiana ∫exp(−a k²)dk=√(π/a), a>0, deja (1/2π)√(π/(Dt))=1/√(4πDt). El desplazamiento del contorno complejo se justifica por el integrando entero y su decaimiento; equivale a la integral real de Fourier de una gaussiana. La densidad final se integra a1.',
        'With x=z−vt, the exponent is−Dtk²+ikx=−Dt[k−ix/(2Dt)]²−x²/(4Dt). The Gaussian integral ∫exp(−a k²)dk=√(π/a), a>0, leaves (1/2π)√(π/(Dt))=1/√(4πDt). The complex contour shift is justified by an entire decaying integrand; equivalently use the real Fourier integral of a Gaussian. The final density integrates to1.',
        r'\frac1{2\pi}\int e^{-Dtk^2+ikx}dk=\frac{e^{-x^2/(4Dt)}}{\sqrt{4\pi Dt}}',
        'Inverse Gaussian integral gives exp[−(z−v*t)²/(4*D*t)]/sqrt(4*pi*D*t).',
        'D>0,t>0; dominio infinito; extensión docente, no ecuación numerada adicional del artículo.','D>0,t>0; infinite domain; teaching extension, not an additional numbered paper equation.',S,[7,8],['15','17'])]
    chapters[1]['steps'][2:2]=fourier_steps
    chapters[4]['steps'].insert(1,st('complete-square','Completar el cuadrado en el promedio de fase','Complete the square in the phase average',
      'Poner r=ζ−vΔ separa exp(ivq0Δ). En la integral restante, −r²/(4DΔ)+iq0r=−[r−2iDΔq0]²/(4DΔ)−DΔq0². El segundo término no depende de r y sale de la integral. La gaussiana desplazada conserva su integral√(4πDΔ), que cancela exactamente la normalización deP. Quedan exp(−DΔq0²) y la fase de la media. Comprobar E(q0=0)=1 y |E|≤1 detecta un signo erróneo.',
      'Set r=ζ−vΔ to separate exp(ivq0Δ). In the remaining integral, −r²/(4DΔ)+iq0r=−[r−2iDΔq0]²/(4DΔ)−DΔq0². The second term is independent of r and leaves the integral. The shifted Gaussian retains integral√(4πDΔ), exactly cancelling P normalization. What remains is exp(−DΔq0²) and the mean phase. Check E(q0=0)=1 and |E|≤1 to catch a wrong sign.',
      r'-\frac{r^2}{4D\Delta}+iq_0r=-\frac{(r-2iD\Delta q_0)^2}{4D\Delta}-D\Delta q_0^2',
      'Complete square: −r²/(4*D*Delta)+i*q0*r=−(r−2*i*D*Delta*q0)²/(4*D*Delta)−D*Delta*q0².',
      'Gaussiana libre; DΔ>0; identidad de integral de Fourier/contorno; extensión docente.','Free Gaussian; DDelta>0; Fourier/contour integral identity; teaching extension.',S,10,['31']))
    chapters[5]['steps'].insert(1,st('relaxation-derivatives','Mostrar la regla del producto','Show the product rule',
      'Definir R(t)=exp[(iΩ0−1/T2)t]. Entonces ∂t(RΨ)=R∂tΨ+(iΩ0−1/T2)RΨ. Como R no depende de z, ∂z(RΨ)=R∂zΨ y ∂zz(RΨ)=R∂zzΨ. Sustituir las tres derivadas en Bloch–Torrey cancela el término (iΩ0−1/T2)RΨ a ambos lados; dividir por R deja la ecuación reducida. Para longitudinal, aplicar lo mismo a Mz−Mz0 con R1=exp(−t/T1) y Mz0 uniforme.',
      'Define R(t)=exp[(iΩ0−1/T2)t]. Then ∂t(RΨ)=R∂tΨ+(iΩ0−1/T2)RΨ. Because R is independent of z, ∂z(RΨ)=R∂zΨ and ∂zz(RΨ)=R∂zzΨ. Substitution into Bloch–Torrey cancels (iΩ0−1/T2)RΨ on both sides; division by R leaves the reduced equation. Longitudinally apply the same method to Mz−Mz0 with R1=exp(−t/T1) and uniform Mz0.',
      r'\partial_t(R\Psi)=R\partial_t\Psi+R(i\Omega_0-T_2^{-1})\Psi,\quad\partial_z(R\Psi)=R\partial_z\Psi,\quad\partial_z^2(R\Psi)=R\partial_z^2\Psi',
      'Time derivative adds Rprime*Psi; spatial derivatives pass through R(t); cancel the uniform relaxation/offset factor.',
      'R espacialmente uniforme y no nulo; evolución entreRF.','Spatially uniform nonzero R; evolution between RF.',S,9,['19','20']))
    # Fragments are source-reviewed teaching prose, never derived by blind PDF OCR.
    for filename in ('chapters-07-13.json','chapters-14-20.json'):
        p=REVIEW/filename
        if p.exists():
            fragment=json.loads(p.read_text(encoding='utf-8-sig'))
            chapters.extend(fragment['chapters'] if isinstance(fragment,dict) else fragment)
    by_id={c['id']:c for c in chapters}
    if 'monopolar-pgse' in by_id:
        by_id['monopolar-pgse']['steps'].insert(1,st('shape-time-substitution','Integrar una forma dentro de cada intervalo','Integrate a shape within each interval',
          'Para un lóbulo no rectangular escribir hδ(t)=h(t/δ) dentro de0≤t≤δ y cero fuera. Cambiar variableε=(s−t0)/δ da ds=δdε y ∫t0..t h((s−t0)/δ)ds=δH((t−t0)/δ). Así q durante el primer pulso esγgδH(t/δ), la mesetaγgδσ y durante el últimoγgδ[σ−H((t−Δ)/δ)]. El cambio de variable produce el factorδ; omitirlo rompe las unidades. Para integrar q² se usan ∫H=σλ y∫H²=σ²κ.',
          'For a nonrectangular lobe write hdelta(t)=h(t/delta) on0≤t≤delta and zero outside. Substitute epsilon=(s−t0)/delta, giving ds=delta depsilon and ∫t0..t h((s−t0)/delta)ds=delta H((t−t0)/delta). Thus q isgamma*g*delta*H(t/delta) during the first pulse, gamma*g*delta*sigma on the plateau, andgamma*g*delta*[sigma−H((t−Delta)/delta)] during the final pulse. The substitution suppliesdelta; omitting it breaks units. Integrate q² using∫H=sigma*lambda and∫H²=sigma²*kappa.',
          r'\int_{t_0}^th[(s-t_0)/\delta]ds=\delta\int_0^{(t-t_0)/\delta}h(\epsilon)d\epsilon=\delta H[(t-t_0)/\delta]',
          'With epsilon=(s−t0)/delta and ds=delta*depsilon, lobe integral=delta*H((t−t0)/delta).',
          'Lóbulos idénticos no solapados; h adimensional, H primitiva.','Identical nonoverlapping lobes; dimensionless h, primitive H.',S,11,['33','34','35','36','38','39']))
    if 'kuchel-full' in by_id:
        by_id['kuchel-full']['steps'].append(st('appendix-consistent-algebra','Aplicar el apéndice con una definición global consistente','Apply the appendix with a consistent global definition',
          'Para implementar en un reloj global, definir a=γpg y q=∫a antes de derivar. UsarΨ=Aexp(−izq): ∂tΨ=(A′−izq′A)exp(−izq), ∂zΨ=−iqΨ, ∂zzΨ=−q²Ψ. Sustituir en la ecuación ponderada por p da A′−izq′A=−izγpgA−Dq²A. q′=γpg cancela la fase; dA/A=−Dq²dt y ln(A/A0)=−D∫q²dt. Estas líneas explican el mecanismo deA3–A8 en notación reescrita, sin multiplicar otra vez por p ni ignorar el saltoRF. El literal A1 externo requiere interpretar su marco/coherencia; la ruta principal F,f,H conserva sus propias condiciones de intervalo.',
          'To implement on a global clock, define a=gamma*p*g and q=∫a before differentiating. UsePsi=A exp(−izq): ∂tPsi=(A′−izq′A)exp(−izq), ∂zPsi=−iqPsi, ∂zzPsi=−q²Psi. Substitute into the p-weighted equation to obtain A′−izq′A=−izgamma*p*g*A−Dq²A. q′=gamma*p*g cancels phase; dA/A=−Dq²dt and ln(A/A0)=−D∫q²dt. These lines explain the mechanism ofA3–A8 in rewritten notation, without multiplying byp again or ignoring the RF jump. Literal externalp inA1 requires frame/coherence interpretation; the mainF,f,H route retains its own interval conditions.',
          r"\partial_t\Psi=(A'-izq'A)e^{-izq},\quad\partial_z\Psi=-iq\Psi,\quad\partial_z^2\Psi=-q^2\Psi;\quad A'=-Dq^2A\Rightarrow\ln(A/A_0)=-D\int q^2dt",
          'Product derivatives give Aprime−i*z*qprime*A; qprime=gamma*p*g cancels phase; Aprime/A=−D*q²; integrate to−D*b.',
          'Notación docente reescrita; RF instantáneo tratado por trayectoria/coherencia; evolución diferencial entreRF; D libre.','Rewritten teaching notation; instantaneous RF handled by pathway/coherence; differential evolution between RF; free D.',K,[7,9],['A1','A2','A3','A4','A5','A6','A7','A8'],
          ('No es una transcripción literal del apéndice: explicita la interpretación coherente para programación en tiempo global.','This is not a literal appendix transcription: it makes a consistent global-time implementation explicit.')))
    if 'bipolar' in by_id:
        by_id['bipolar']['steps'].insert(1,st('seven-interval-algebra','Mostrar las siete áreas cuadráticas','Show all seven squared areas',
          'SeaC=γgδ/2 y H la primitiva de la forma. En los siete intervalos q/C vale−H,−σ,−σ−H,−2σ,−2σ+H,−σ,−σ+H. Los cuatro lóbulos duranδ/2; las dos pausas internasτ y la pausa centralΔ−δ−τ. Integrar cuadrados y usarλ,κ da b/C²=σ²{(δ/2)[κ+(1+2λ+κ)+(4−4λ+κ)+(1−2λ+κ)]+2τ+4(Δ−δ−τ)}. Simplificar dejaσ²[4Δ+(2κ−2λ−1)δ−2τ]. Como C²σ²=q0²/4 se obtiene[53]. Las áreas lineales se simplifican a u/C=−2σΔ, dando[52].',
          'LetC=gamma*g*delta/2 andH be the shape primitive. Across seven intervals q/C equals−H,−sigma,−sigma−H,−2sigma,−2sigma+H,−sigma,−sigma+H. Four lobes lastdelta/2; two internal gaps lasttau and the central gapDelta−delta−tau. Integrating squares withlambda,kappa gives b/C²=sigma²{(delta/2)[kappa+(1+2lambda+kappa)+(4−4lambda+kappa)+(1−2lambda+kappa)]+2tau+4(Delta−delta−tau)}. Simplification leaves sigma²[4Delta+(2kappa−2lambda−1)delta−2tau]. SinceC²sigma²=q0²/4, this gives[53]. Linear areas simplify to u/C=−2sigmaDelta, giving[52].',
          r'\frac b{C^2\sigma^2}=\frac\delta2[\kappa+(1+2\lambda+\kappa)+(4-4\lambda+\kappa)+(1-2\lambda+\kappa)]+2\tau+4(\Delta-\delta-\tau)=4\Delta+(2\kappa-2\lambda-1)\delta-2\tau',
          'Four lobe integrals plus two tau plateaux and central plateau simplify to b/(C²*sigma²)=4*Delta+(2*kappa−2*lambda−1)*delta−2*tau.',
          'Cronología deFig4a; Δ≥δ+τ; forma común; C=γgδ/2, σ área de forma.','Fig4a timeline; Delta≥delta+tau; common shape; C=gamma*g*delta/2, sigma shape area.',S,[13,14],['47','48','49','50','51','52','53'] ))
    if 'oneshot-exchange' in by_id:
        by_id['oneshot-exchange']['steps'].insert(2,st('unbalanced-square-template','Una plantilla integra todos los lóbulos','One template integrates every lobe',
          'Dentro de un lóbulo de anchurah=δ/2, escribir q=Cσ[c+dH(ε)/σ]. Entonces ∫q²dt=(Cσ)²h[c²+2cdλ+d²κ]. Los cuatro pares(c,d) son(0,−1−α), (−1−α,−1+α), (−2,1+mα), (−1+mα,1−mα). Añadir las pausas:(Cσ)²{τ[(1+α)²+(1−mα)²]+4(Δ−δ−τ)}. Expandir la suma y sustituirCσ=q0/2 produce la expresión cerrada[57]. Esta plantilla permite comprobar el álgebra sin memorizar un polinomio largo y muestra cada término cruzado.',
          'Within a lobe of widthh=delta/2, writeq=C sigma[c+dH(epsilon)/sigma]. Then∫q²dt=(C sigma)²h[c²+2cdlambda+d²kappa]. The four(c,d) pairs are(0,−1−alpha), (−1−alpha,−1+alpha), (−2,1+m alpha), (−1+m alpha,1−m alpha). Add plateau terms:(C sigma)²{tau[(1+alpha)²+(1−m alpha)²]+4(Delta−delta−tau)}. Expanding the sum and substitutingC sigma=q0/2 gives[57]. This template checks the algebra without memorizing a long polynomial and exposes every cross term.',
          r'\int_{\rm lobe}q^2dt=(C\sigma)^2\frac\delta2(c^2+2cd\lambda+d^2\kappa);\quad b=(C\sigma)^2\left[\frac\delta2\sum_{i=1}^4(c_i^2+2c_id_i\lambda+d_i^2\kappa)+\tau((1+\alpha)^2+(1-m\alpha)^2)+4(\Delta-\delta-\tau)\right]',
          'For each lobe integrate(c+d*H/sigma)² using lambda and kappa; sum four lobe terms and three plateau terms to derive Eq57.',
          'Misma forma en cuatro lóbulos; h=δ/2; C=γgδ/2; amplitudes de[56] e intervalos deFig4b.','Same shape in four lobes; h=delta/2; C=gamma*g*delta/2; Eq56 amplitudes and Fig4b intervals.',S,16,['56','57'] ))
    if 'gradient-shapes' in by_id:
        by_id['gradient-shapes']['steps'].append(st('table-one-trapezoid','Trapecio con10% de subida y bajada','Trapezoid with10% rise and fall',
          'LaTabla1 defineh=10ε para0≤ε<0.1, h=1 entre0.1 y0.9 y h=10(1−ε) al final. Integrar cada tramo daH=5ε², ε−0.05 y0.9−5(1−ε)². El área total esσ=0.05+0.8+0.05=0.9. La simetría implicaλ=1/2. Paraκ, integrar las tres expresiones deH²: 25ε⁴, (ε−0.05)² y[0.9−5(1−ε)²]². Su suma es8483/30000; dividir porσ²=0.81 daκ=8483/24300. La pendiente y los tramos están especificados: otro tiempo de rampa da otros momentos.',
          'Table1 definesh=10epsilon on0≤epsilon<0.1, h=1 between0.1 and0.9, andh=10(1−epsilon) at the end. Integrating givesH=5epsilon², epsilon−0.05 and0.9−5(1−epsilon)². Total area issigma=0.05+0.8+0.05=0.9. Symmetry giveslambda=1/2. For kappa, integrate the threeH² expressions:25epsilon⁴, (epsilon−0.05)² and[0.9−5(1−epsilon)²]². Their sum is8483/30000; dividing bysigma²=0.81 giveskappa=8483/24300. The slope and intervals are specified: a different rise time gives different moments.',
          r'\sigma=\frac9{10},\quad\lambda=\frac12,\quad\kappa=\frac1{(9/10)^2}\left[\int_0^{.1}25\epsilon^4d\epsilon+\int_{.1}^{.9}(\epsilon-.05)^2d\epsilon+\int_{.9}^1(.9-5(1-\epsilon)^2)^2d\epsilon\right]=\frac{8483}{24300}',
          '10%-ramp trapezoid: sigma=.9, lambda=.5, kappa=8483/24300; primitive H is5*epsilon²,epsilon−.05,.9−5*(1−epsilon)² in its three regions.',
          'Forma exacta deTabla1; alturas unitarias; subida/bajada0.1 de la duración.','Exact Table1 shape; unit peak; rise/fall occupy0.1 of duration.',S,6,['9','10','11','12','13','Table1']))
        by_id['gradient-shapes']['steps'].append(st('table-one-smoothed','Rectángulo suavizado con rampas trigonométricas','Smoothed rectangle with trigonometric ramps',
          'En la forma suavizada deTabla1, h=sin²(5πε) al inicio0..0.1, h=1 en0.1..0.9 y h=cos²[5π(ε−0.9)] al final. La primitiva inicial esH=ε/2−sin(10πε)/(20π); en el centroH=ε−0.05 y al finalH=0.9−H(1−ε), usando la expresión inicial. σ=0.9 yλ=0.5 por simetría. Expandir H² y usar∫sin²(kε)dε=ε/2−sin(2kε)/(4k) y la integral deεsin(kε) por partes daκ=422/1215+23/(1080π²). El cálculo numérico independiente de la forma verifica este valor; suavizar no autoriza usarσ1 niκ1/3.',
          'For Table1’s smoothed shape,h=sin²(5pi epsilon) initially on0..0.1, h=1 on0.1..0.9, andh=cos²[5pi(epsilon−0.9)] at the end. The initial primitive isH=epsilon/2−sin(10pi epsilon)/(20pi); centrallyH=epsilon−0.05 and finallyH=0.9−H(1−epsilon), using the initial expression. Sigma=0.9 andlambda=0.5 by symmetry. ExpandH², use∫sin²(k epsilon)depsilon=epsilon/2−sin(2k epsilon)/(4k), and integrateepsilon*sin(k epsilon) by parts to obtainkappa=422/1215+23/(1080pi²). Independent numerical integration verifies this value; smoothing does not justify usingsigma1 orkappa1/3.',
          r'H_{\rm rise}=\epsilon/2-\sin(10\pi\epsilon)/(20\pi),\quad\sigma=.9,\quad\lambda=.5,\quad\kappa=\frac{422}{1215}+\frac{23}{1080\pi^2}',
          'Smoothed10%-ramp rectangle: Hrise=epsilon/2−sin(10*pi*epsilon)/(20*pi); sigma=.9; lambda=.5; kappa=422/1215+23/(1080*pi²).',
          'Forma trigonométrica exacta deTabla1; expansión deH² por tramos, sin sustituir gradiente ideal por forma nominal.','Exact trigonometric Table1 shape; piecewiseH² expansion, no substitution of nominal shape for actual gradient.',S,6,['9','10','11','12','13','Table1']))
    data = {'schemaVersion':'1.0.0','id':'academy-diffusion-derivations','version':'1.0.0',
      'releaseStatus':'draft-in-progress','title':bi('De Fick a DOSY: derivaciones y controles','From Fick to DOSY: derivations and checks'),
      'pagesConvention':bi('sourceRefs.pages son páginas PDF1-based. journalPages son páginas impresas.','sourceRefs.pages are1-based PDF pages. journalPages are printed journal pages.'),
      'notationPolicy':bi('Ecuaciones docentes reescritas en notación consistente; notas identifican discrepancias literales comprobadas visualmente. No se reproducen páginas de los artículos.','Teaching equations are rewritten in consistent notation; notes identify visually checked literal discrepancies. Article pages are not reproduced.'),
      'evidenceBoundary':bi('Suplemento docente y consulta de fuentes; no calibra hardware, no sustituye datos experimentales y no reentrena el modelo existente.','Teaching/source-retrieval supplement; no hardware calibration, no replacement of experimental data, and no retraining of the existing model.'),
      'sources':[
        {'id':S,'title':'The Stejskal–Tanner Equation Generalized for Any Gradient Shape—An Overview of Most Pulse Sequences Measuring Free Diffusion','authors':['Davy Sinnaeve'],'year':2012,'doi':'10.1002/cmr.a.21223','url':'https://doi.org/10.1002/cmr.a.21223','sha256':'de6907031348e45a7c2bf32a7ba9b2aceae34cad70faa6f93e22bef34b1f8bf8','pages':27,'journalPageStart':39,'journalPageEnd':65},
        {'id':K,'title':'Stejskal–Tanner Equation Derived in Full','authors':['Philip W. Kuchel','Guilhem Pagès','Kaz Nagashima','Sendhil Velan','Vimalan Vijayaragavan','Vijayasarathi Nagarajan','Kai Hsiang Chuang'],'year':2012,'doi':'10.1002/cmr.a.21241','url':'https://doi.org/10.1002/cmr.a.21241','sha256':'72ea97b1e621be1694e264d568000ad792667952d1d429fdc596ef4726feb94f','pages':10,'journalPageStart':205,'journalPageEnd':214}],
      'symbols':[{'symbol':s,'unit':u,'meaning':bi(es,en)} for s,u,es,en in [
        ('D','m²/s','Coeficiente de difusión traslacional','Translational diffusion coefficient'),('g(t)','T/m','Gradiente físico del campo','Physical magnetic-field gradient'),('δ','s','Duración definida según familia de secuencia','Duration defined for the sequence family'),('Δ','s','Separación entre inicios de codificación y decodificación','Encoding/decoding start separation'),('γ','rad/(s·T)','Relación giromagnética angular','Angular gyromagnetic ratio'),('p(t)','1','Orden de coherencia seleccionado','Selected coherence order'),('P(t)','rad/(s·T)','ΣγXpX, ya incluye γ','ΣγXpX, already includes γ'),('q(t)','1/m','Historia acumulada de gradiente efectivo','Cumulative effective-gradient history'),('b','s/m²','Integral temporal q²','Time integral of q²'),('u','s/m','Integral temporal q','Time integral of q'),('v','m/s','Velocidad dirigida uniforme','Uniform directed velocity'),('σ,λ,κ','1','Parámetros de la forma del gradiente','Gradient-shape parameters'),('T1,T2','s','Tiempos de relajación','Relaxation times'),('τ','s','Separación interna bipolar; no universal','Internal bipolar separation; not universal'),('L','m','Longitud efectiva uniforme observada','Uniform effective observed length'),('k','1/m','Variable espacial deFourier','Spatial Fourier variable')]],
      'chapters':chapters,'equationCoverage':[]}
    data['symbols'] += [{'symbol':s,'unit':u,'meaning':bi(es,en)} for s,u,es,en in [
      ('z,r,ζdisplacement','m','Posición/ vector posición/ desplazamiento aleatorio; distinguirlos del conmutadorζ deKuchel','Position/position vector/random displacement; distinguish these from Kuchel’s switchzeta'),
      ('c','amount/m³','Concentración; o densidad de probabilidad tras normalizar','Concentration; or probability density after normalization'),
      ('J','amount/(m²·s)','Flujo de concentración','Concentration flux'),
      ('M+,Mz','magnetization units','Magnetización compleja transversal y magnetización longitudinal','Complex transverse and longitudinal magnetization'),
      ('Ψ,A','normalized amplitude','Magnetización reducida y amplitud temporal uniforme','Reduced magnetization and uniform temporal amplitude'),
      ('Ω0,ω','rad/s','Offset y frecuencia angular; convertirHz con2π','Offset and angular frequency; convertHz using2pi'),
      ('h(ε),H(ε)','1','Forma normalizada y su primitiva; H tiene otro significado en capítuloKuchel','Normalized shape and its primitive; H has another meaning in the Kuchel chapter'),
      ('ε','1','Tiempo local dividido por duración de lóbulo','Local time divided by lobe duration'),
      ('μ','1','Centroide temporal normalizado de la forma','Normalized temporal centroid of the shape'),
      ('q0','1/m','Magnitud de q tras un bloque de codificación','q magnitude after an encoding block'),
      ('T,TE','s','Tiempo total de secuencia e instante de eco','Total sequence time and echo time'),
      ('τRF','s','Instante del pulso180 en la derivación deKuchel; distinto deτ bipolar','180pulse time in Kuchel’s derivation; distinct from bipolar tau'),
      ('F(t),f,Hphase(t)','T·s/m','Integral de gradiente físico; valor enτRF; combinación de fase F+(ζ−1)f','Physical-gradient integral; value at tauRF; phase combination F+(zeta−1)f'),
      ('ζswitch','1','Conmutador+1 antes y−1 después de180 deKuchel','Kuchel switch+1 before and−1 after180'),
      ('α,m','1','Desequilibrio relativo y relación de desequilibrios entre dos pares','Relative imbalance and imbalance ratio between two pairs'),
      ('vmax','m/s','Límite de distribución uniforme de velocidades, noRMS','Uniform velocity distribution bound, not RMS'),
      ('E,Ediff,Econv','1','Señal normalizada compleja y sus factores de difusión/convección','Complex normalized signal and diffusion/convection factors'),
      ('d20,p30,d5','s or µs as stored','Nombres de parámetros de secuencia; sus significados se leen en el programa de pulsos','Sequence parameter names; read their meanings in the pulse program'),
      ('Btensor','s/m²','Tensor de codificación ∫qqᵀdt','Encoding tensor integralqqᵀdt'),
      ('Dtensor','m²/s','Tensor de difusión; forma isotrópica DI','Diffusion tensor; isotropic formDI')]]
    data['tableCoverage']=[
      {'sourceId':S,'table':'Table1','pages':[6],'journalPages':[44],
       'chapterIds':['gradient-shapes'],
       'entries':['rectangle','sine-bell','sine-squared','10%-ramp-trapezoid','10%-ramp-smoothed-rectangle'],
       'notes':bi('Todas las formas del artículo están explicadas porσ,λ,κ; triángulo se etiqueta como extensión docente.','All paper shapes are explained throughsigma,lambda,kappa; triangle is labelled as a teaching extension.')},
      {'sourceId':S,'table':'Table2','pages':[20],'journalPages':[58],
       'chapterIds':['gradient-shapes','monopolar-pgse','bipolar','oneshot-exchange','double-ste'],
       'entries':['monopolar','bipolar','unbalanced-bipolar','double-monopolar','double-bipolar'],
       'notes':bi('Las25combinaciones se obtienen sustituyendo los5conjuntosσ,λ,κ en las5fórmulas de familia; no se selecciona fórmula sólo por nombre.','The25combinations follow by substituting5sigma,lambda,kappa sets into5family formulas; formula selection is not based on name alone.')},
      {'sourceId':S,'table':'Table3','pages':[21,22,23],'journalPages':[59,60,61],
       'chapterIds':['sequence-catalogue','cross-terms','coherence-pathways','stimulated-echo-led'],
       'entries':['LED','BBP-LED','double-STE-LED','CONVEX','PGSTE-WATERGATE','double-echo-PGSTE-WATERGATE','DEPT-spin-echo','INEPT-IDOSY','multi-quantum-PGSTE','J-evolution-removal','one-shot45','pure-shift-DOSY','selective-TOCSY-DOSY','STD-DOSY','double-quantum-filter','J-resolved-DOSY-IDOSY','convection-compensated-J-resolved-IDOSY','COSY-DOSY-IDOSY','convection-compensated-COSY-IDOSY','DQF-COSY-IDOSY','DOSY-NOESY','TOCSY-DOSY','HMQC-DOSY-IDOSY','CT-HSQC-IDOSY-2006','CT-HSQC-IDOSY-2009','DOSY-TROSY'],
       'notes':bi('Catálogo interpretado por trayectoria y términos cruzados. Los parámetros de variantes especiales se definen en referencias originales citadas por el artículo, no completamente en estos dosPDF; no se convierten en recetas/calculadores sin esos programas y definiciones.','Catalogue interpreted through pathways and cross terms. Special-variant parameters are defined in original references cited by the paper, not fully within these twoPDFs; they are not turned into recipes/calculators without those pulse programs and definitions.')}
    ]
    data['equationCoverage']=coverage(data)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'file':str(OUT),'status':data['releaseStatus'],'chapters':len(chapters),'steps':sum(len(c['steps']) for c in chapters)},ensure_ascii=False))
    return data

def page_map():
    sin={}
    for page, lo, hi in [(2,1,1),(3,2,2),(4,3,6),(5,7,12),(6,13,14),(7,15,15),(8,16,18),(9,19,27),(10,28,31),(11,32,39),(12,40,44),(13,45,48),(14,49,53),(15,54,55),(16,56,58),(17,59,61),(18,62,63),(19,64,65)]:
        sin.update({str(i):page for i in range(lo,hi+1)})
    ku={}
    for page,lo,hi in [(3,1,15),(4,16,23),(5,24,36),(6,37,38)]:
        ku.update({str(i):page for i in range(lo,hi+1)})
    ku.update({f'A{i}':7 if i<=4 else 9 for i in range(1,9)})
    return {S:sin,K:ku}

DISCREPANCIES = {
 (S,'6'):bi('Literal: prefactor MyL/2. Integral escrita: ∫cos(qz)dz=L sinc(qL/2). Academy normaliza S/S0 y comprueba límite1.', 'Literal: prefactor MyL/2. Written integral: ∫cos(qz)dz=L sinc(qL/2). Academy normalizes S/S0 and checks limit1.'),
 (S,'40'):bi('Literal ln(Etransl)=∫qdt. Se llama u a esa integral; ln(Etransl)=iv u según[31].','Literal ln(Etransl)=∫qdt. This integral is named u; ln(Etransl)=iv u according to[31].'),
 (S,'41'):bi('Literal ln(Ediff)=∫q²dt. Se llama b a esa integral; ln(Ediff)=−Db según[31].','Literal ln(Ediff)=∫q²dt. This integral is named b; ln(Ediff)=−Db according to[31].'),
 (S,'52'):bi('Integral u, no logaritmo sin iv; [31] fija el prefactor.','This is integral u, not a logarithm without iv;[31] supplies the prefactor.'),
 (S,'53'):bi('Integral b, no logaritmo sin−D; [31] fija el prefactor.','This is integral b, not a logarithm without−D;[31] supplies the prefactor.'),
 (S,'57'):bi('La expresión positiva es b; para lnEdiff multiplicar por−D.','The positive expression is b; multiply by−D for lnEdiff.'),
 (S,'58'):bi('La expresión es u; para lnEtransl multiplicar por iv. La integral de los cuatro lóbulos[56] da un factor1/2 en la correcciónα(1−m)(δ/2+τ); el literal lo omite. Para m=+1 la corrección se anula.','The expression is u; multiply by iv for lnEtransl. Integrating the four lobes[56] gives factor1/2 in correction alpha(1−m)(delta/2+tau); the literal omits it. For m=+1 the correction vanishes.'),
 (S,'60'):bi('Literal exp(−x²/√6) después de1−x²/6. Academy deriva exp(−x²/6)+O(x⁴) de sincx; no atribuye causa a la discrepancia.','Literal exp(−x²/√6) after1−x²/6. Academy derives exp(−x²/6)+O(x⁴) from sincx; no cause is attributed to the discrepancy.'),
 (S,'61'):bi('Literal √6; Taylor de la distribución uniforme±vmax exige6. Forma general Dapp=D+vmax²Δ²/(6Δeff), límite Δeff≈Δ.','Literal √6; Taylor for uniform distribution±vmax requires6. General form Dapp=D+vmax²Δ²/(6Δeff), with limit DeltaEff≈Delta.'),
 (S,'64'):bi('Corchete literal omiteδ en4κ−4λ. La suma de dos[41] y Tabla2 daΔ+4(κ−λ)δ, dimensionalmente consistente.','Literal bracket omitsδ in4κ−4λ. Summing two[41] and Table2 givesDelta+4(kappa−lambda)*delta, dimensionally consistent.'),
 (S,'65'):bi('Literal coeficiente2κ−2λ−δ; suma de dos[53] y Tabla2 da2κ−2λ−1, multiplicado porδ/2.','Literal coefficient2kappa−2lambda−delta; summing two[53] and Table2 gives2kappa−2lambda−1, multiplied bydelta/2.'),
 (K,'8'):bi('Se imprimen barras de módulo con fase compleja. Academy distingue M complejo y |M|.','Magnitude bars are printed with complex phase. Academy distinguishes complex M from |M|.'),
}
for i in range(1,9):
    DISCREPANCIES[(K,f'A{i}')]=bi(
      'Apéndice usa p fuera de la integral y pF. Su notación debe interpretarse con la transformación instantáneaRF; no sustituye automáticamente q(t)=∫γp(s)g(s)ds en un reloj global ni permite aplicar p dos veces.',
      'The appendix uses p outside the integral and pF. Interpret its notation with the instantaneous RF transformation; it does not automatically replace q(t)=∫gamma*p(s)*g(s)ds on a global clock or permit applying p twice.')

# Every numbered equation has a substantive algebraic role and a rewritten
# mathematical counterpart. These are pedagogical paraphrases, not literal
# transcriptions. In piecewise rows, interval definitions are in the chapter.
ROLE_ROWS = {
S:r'''
1|E=e^{-Db},\ b=\gamma_{\rm eff}^2g^2\delta^2\sigma^2\Delta_{\rm eff}|Modelo directo general; Δeff y γeff dependen de secuencia/coherencia.|General forward model; DeltaEff and gammaEff depend on sequence/coherence.
2|\omega_R(z)=-\gamma gz|Restar la frecuencia de B0 convierte la pendiente de campo en frecuencia espacial.|Subtracting the B0 frequency converts field slope into spatial frequency.
3|\binom{M_x'}{M_y'}=R(\gamma gz\delta)\binom{M_x}{M_y}|Rotación de componentes; conserva el módulo local.|Component rotation preserves local magnitude.
4|\Lambda=2\pi/(\gamma g\delta)|Un giro2π define el paso espacial de la hélice de fase.|A2pi turn defines spatial phase-helix pitch.
5|N=\gamma g\delta L/(2\pi)|Dividir longitud observada por paso da el número de vueltas.|Observed length divided by pitch gives the turn count.
6|S/S_0=\operatorname{sinc}(qL/2)|Integrar exp(−iqz) sobre una muestra uniforme y normalizar; límite1 en q0.|Integrate exp(−iqz) over a uniform sample and normalize; limit1 at q0.
7|R(-\phi)R(\phi)=I|Dos rotaciones inversas recuperan magnetización estática.|Two inverse rotations recover static magnetization.
8|\omega_R=-\gamma g h(\epsilon)z|Introducir el perfil temporal h modifica la fase instante a instante.|Introducing temporal shape h changes phase at each instant.
9|\sigma=\int_0^1h(\epsilon)d\epsilon|Área adimensional de la forma; escala q máximo.|Dimensionless shape area; scales peak q.
10|\lambda=\sigma^{-1}\int_0^1H(\epsilon)d\epsilon|Primer momento temporal de la primitiva; aparece en integrales de q.|First temporal moment of the primitive; enters q integrals.
11|\kappa=\sigma^{-2}\int_0^1H(\epsilon)^2d\epsilon|Momento cuadrático de la primitiva; controla difusión durante lóbulos.|Squared primitive moment; controls diffusion during lobes.
12|H(\epsilon)=\int_0^\epsilon h(x)dx|Definir la primitiva de forma para integrar cada gradiente finito.|Define the shape primitive to integrate each finite gradient.
13|\lambda=1-\mu,\quad\mu=\sigma^{-1}\int_0^1\epsilon h(\epsilon)d\epsilon|Integración por partes; simetría de la forma implicaλ1/2.|Integration by parts; shape symmetry implies lambda1/2.
14|J=-D\partial_zc|Flujo de Fick opuesto al gradiente de concentración.|Fick flux opposes the concentration gradient.
15|\partial_tc=D\partial_z^2c|Conservación más Fick con D constante; difusión libre.|Conservation plus Fick with constant D; free diffusion.
16|J_{\rm adv}=vc|Flujo debido a desplazamiento dirigido.|Flux from directed translation.
17|\partial_tc=-v\partial_zc|Conservación con v constante; perfil trasladado sin dispersión.|Conservation with constant v; profile translates without spreading.
18|\partial_tM_+=(i\Omega_0-T_2^{-1})M_+-i\gamma gzM_++D\partial_z^2M_+-v\partial_zM_+|Sumar precesión, relajación, difusión y deriva; longitudinal usa recuperaciónT1.|Add precession, relaxation, diffusion and drift; longitudinal component uses T1 recovery.
19|M_+=\Psi_+e^{(i\Omega_0-1/T_2)t}|Factorizar offset y relajación uniformes, con transformaciónT1 análoga.|Factor uniform offset and relaxation, with analogous T1 transformation.
20|\partial_t\Psi_+=-i\gamma gz\Psi_++D\partial_z^2\Psi_+-v\partial_z\Psi_+|Regla del producto cancela relajación y offset; Ψz no acumula fase de gradiente.|Product rule cancels relaxation and offset; PsiZ accumulates no gradient phase.
21|\partial_t\Psi=-i\gamma p(t)gz\Psi+D\partial_z^2\Psi-v\partial_z\Psi|Incluir el orden de coherencia en la evolución de fase.|Include coherence order in phase evolution.
22|\partial_t\Psi=-iP(t)gz\Psi+D\partial_z^2\Psi-v\partial_z\Psi|Generalizar a coherencias que incluyen varios núcleos.|Generalize to coherences involving several nuclei.
23|P(t)=\sum_X\gamma_Xp_X(t)|La ponderaciónP ya contiene cadaγ: no multiplicarlo otra vez.|Weight P already contains each gamma: do not multiply it again.
24|B_{\rm inh}(t,z)=g(t)z|Hipótesis de campo espacialmente lineal requerida por el ansatz.|Spatially linear field assumption required by the ansatz.
25|\Psi=\Psi_0(z)e^{-izq(t)}|Sin D ni v, integrar la ecuación local de fase.|With D and v absent, integrate the local phase equation.
26|q(t)=\int_0^tP(s)g(s)ds|Historia acumulada de gradiente efectivo: RF dentro de la integral.|Cumulative effective-gradient history: RF belongs inside the integral.
27|\Psi=A(t)e^{-izq(t)}|Separar amplitud uniforme y modulación espacial de fase.|Separate uniform amplitude from spatial phase modulation.
28|A'-izq'A=(-izPg-Dq^2+ivq)A|Mostrar derivadas de producto; q'=Pg cancela términos de fase.|Show product derivatives; q'=Pg cancels phase terms.
29|A'=(-Dq^2+ivq)A|Reducir Bloch–Torrey a una ODE escalar de amplitud.|Reduce Bloch–Torrey to a scalar amplitude ODE.
30|A/A_0=\exp[-D\int q^2dt+iv\int qdt]|Resolver la ODE por separación de variables.|Solve the ODE by separation of variables.
31|E=e^{-Db}e^{ivu},\quad b=\int q^2dt,\ u=\int qdt|Identificar difusión por b y transporte dirigido por u; señal de eco con qT0.|Identify diffusion through b and directed transport through u; echo signal requires qT0.
32|a(t)=\gamma g[h_\delta(t)-h_\delta(t-\Delta)]|Definir dos lóbulos efectivos monopolares de signos opuestos.|Define two opposite-sign effective monopolar lobes.
33|h_\delta(t)=h(t/\delta),\ 0\le t\le\delta|Escalar tiempo local al dominio de forma0..1.|Scale local time to the shape domain0..1.
34|a(t)=\gamma g\{h(t/\delta),0,-h[(t-\Delta)/\delta]\}|Sustituir la forma en los tres intervalos de gradiente efectivo.|Substitute the shape into the three effective-gradient intervals.
35|\int_{t_0}^th[(s-t_0)/\delta]ds=\delta H[(t-t_0)/\delta]|Cambio de variableε=(s−t0)/δ integra un lóbulo.|Variable substitution epsilon=(s−t0)/delta integrates a lobe.
36|q=\gamma g\delta\{H(t/\delta),\sigma,\sigma-H[(t-\Delta)/\delta]\}|Construir crecimiento, meseta y descenso de q; comprobar cierre.|Build q growth, plateau and descent; check closure.
37|q^2=(\gamma g\delta)^2\{H^2,\sigma^2,\sigma^2-2\sigma H+H^2\}|Cuadrar cada tramo sin olvidar el término cruzado−2σH.|Square every segment including cross term−2sigmaH.
38|\int_0^\delta H(t/\delta)dt=\delta\sigma\lambda|Cambiar variable y usar la definiciónλ para la integral lineal.|Change variables and use lambda for the linear integral.
39|\int_0^\delta H(t/\delta)^2dt=\delta\sigma^2\kappa|Cambiar variable y usarκ para el término cuadrático.|Change variables and use kappa for the squared term.
40|u=\gamma g\delta\sigma\Delta|Sumar tres áreas de q; los momentos de forma se cancelan en u.|Sum three q areas; shape moments cancel in u.
41|b=(\gamma g\delta\sigma)^2[\Delta+2(\kappa-\lambda)\delta]|Sumar tres áreas de q²; los momentos de forma permanecen en b.|Sum three q² areas; shape moments remain in b.
42|E=e^{-D(\gamma g\delta)^2(\Delta-\delta/3)}|Rectángulo:σ1,λ1/2,κ1/3; nace la correcciónδ/3.|Rectangle: sigma1,lambda1/2,kappa1/3; produces delta/3 correction.
43|E=e^{-D(\gamma g\delta)^2(4/\pi^2)(\Delta-\delta/4)}|Seno:σ2/π,λ1/2,κ3/8; área y tiempo cambian.|Sine: sigma2/pi,lambda1/2,kappa3/8; both area and timing change.
44|a=\gamma g[-h_{\delta/2}(t)-h_{\delta/2}(t-\delta/2-\tau)+h_{\delta/2}(t-\Delta)+h_{\delta/2}(t-\Delta-\delta/2-\tau)]|Cuatro lóbulos efectivos bipolares;δ es duración total de dos lóbulos por par.|Four effective bipolar lobes;delta is the total two-lobe duration per pair.
45|h_{\delta/2}(t)=h(2t/\delta)|La forma ocupaδ/2; no introducir una anchuraδ por cada lóbulo.|Shape occupies delta/2; do not use widthdelta for every lobe.
46|a=\gamma g\{-h,-h,+h,+h\}\quad\text{on four lobes}|Explicitar cuatro lóbulos y tres intervalos sin gradiente efectivo.|Make four lobes and three zero-effective-gradient intervals explicit.
47|\int_{t_0}^th[2(s-t_0)/\delta]ds=(\delta/2)H[2(t-t_0)/\delta]|Cambio de variable conδ/2 fija el factor1/2 de cada área.|Substitution with delta/2 fixes the factor1/2 in each area.
48|q=(\gamma g\delta/2)\{-H,-\sigma,-\sigma-H,-2\sigma,-2\sigma+H,-\sigma,-\sigma+H\}|Acumular q por siete intervalos; las pausas mantienen el q alcanzado.|Accumulate q through seven intervals; pauses retain attained q.
49|q^2=(\gamma g\delta/2)^2\{H^2,\sigma^2,(\sigma+H)^2,4\sigma^2,(-2\sigma+H)^2,\sigma^2,(-\sigma+H)^2\}|Cuadrar los siete intervalos; las áreas de las pausas contribuyen.|Square all seven intervals; pause areas contribute.
50|\int_0^{\delta/2}H(2t/\delta)dt=(\delta/2)\sigma\lambda|Integral lineal para un lóbulo bipolar de media anchura.|Linear integral for a half-width bipolar lobe.
51|\int_0^{\delta/2}H(2t/\delta)^2dt=(\delta/2)\sigma^2\kappa|Integral cuadrática para un lóbulo bipolar de media anchura.|Squared integral for a half-width bipolar lobe.
52|u=-\gamma g\delta\sigma\Delta|Sumar siete áreas lineales; signo inverso frente al esquema monopolar elegido.|Sum seven linear areas; reversed sign relative to the selected monopolar scheme.
53|b=(\gamma g\delta\sigma)^2[\Delta+(2\kappa-2\lambda-1)\delta/4-\tau/2]|Sumar siete áreas cuadráticas; aparece separación internaτ.|Sum seven squared areas; internal separationtau appears.
54|M_+\longrightarrow M_+e^{-i\omega_1 U}|Evolución de desplazamiento químico durante un intervalo transversalU.|Chemical-shift evolution over transverse intervalU.
55|M_{\rm exchanged}\longrightarrow M_{\rm exchanged}e^{i(\omega_2-\omega_1)U}|El cambio de sitio entre periodos deja fase de intercambio.|Changing site between periods leaves exchange phase.
56|a=\gamma g\{-(1+\alpha)h,-(1-\alpha)h,(1+m\alpha)h,(1-m\alpha)h\}|Definir las cuatro amplitudes de bipolares desequilibrados; su área neta efectiva sigue cero.|Define four unbalanced bipolar amplitudes; net effective area remains zero.
57|b=q_0^2[\Delta+(\kappa-\lambda)(\alpha^2(1+m^2)+2)\delta/4+(\delta+2\tau)(\alpha^2(1+m^2)+2\alpha(1-m)-2)/8]|Integrar el cuadrado del q desequilibrado;α0 debe recuperar[53].|Integrate squared unbalanced q;alpha0 must recover[53].
58|u=-q_0[\Delta+\alpha(1-m)(\delta/2+\tau)/2]|Obtener u por los centroides de los cuatro lóbulos y comparar con el literal.|Obtain u from four lobe centroids and compare with the literal.
59|E_{\rm conv}=\frac1{2v_{\max}}\int_{-v_{\max}}^{v_{\max}}e^{ivu}dv=\operatorname{sinc}(v_{\max}u)|Promediar una distribución uniforme de velocidades; puede cambiar signo.|Average a uniform velocity distribution; the result may change sign.
60|\operatorname{sinc}x=1-x^2/6+O(x^4)\approx e^{-x^2/6}|Taylor cerca de cero explica por qué convección débil parece una exponencial.|Taylor near zero explains why weak convection looks exponential.
61|D_{\rm app}=D+v_{\max}^2\Delta^2/(6\Delta_{\rm eff})|Dividir el exponente de convección débil por b da sesgo aparente; no es corrección universal.|Dividing the weak-convection exponent by b gives apparent bias; not a universal correction.
62|e^{ivu_1}e^{ivu_2}=1\quad(u_1+u_2=0)|Dos codificaciones con momentos lineales opuestos cancelan velocidad constante.|Two encodings with opposite linear moments cancel constant velocity.
63|E=e^{-D(b_1+b_2)}|La difusión no se cancela: los dos b positivos se suman.|Diffusion does not cancel: the two positive b values add.
64|b=(\gamma g\delta\sigma)^2[\Delta+4(\kappa-\lambda)\delta]|Dos bloques monopolares con separaciónΔ/2; sumar correcciones de anchura.|Two monopolar blocks with separationDelta/2; add width corrections.
65|b=(\gamma g\delta\sigma)^2[\Delta+(2\kappa-2\lambda-1)\delta/2-(\tau_1+\tau_2)/2]|Dos bloques bipolares; sumar separaciones internas distintasτ1,τ2.|Two bipolar blocks; add distinct internal separationstau1,tau2.
''',
K:r'''
1|M_+=M_x+iM_y|Definir una variable compleja que almacena dos componentes transversales.|Define a complex variable storing two transverse components.
2|M_+=M_0(\cos\omega t+i\sin\omega t)|Escribir la rotación con componentes seno/coseno.|Write rotation using sine/cosine components.
3|M_+=M_0e^{i\omega t}|Aplicar la identidad de Euler a la rotación.|Apply Euler’s identity to rotation.
4|M_+=M_0e^{(i\omega-1/T_2)t}|Añadir pérdida de amplitudT2 separada de la fase.|Add T2 amplitude loss separately from phase.
5|B_z=B_0+\mathbf g\cdot\mathbf r|Campo lineal en posición; g es pendiente, no campo.|Position-linear field;g is slope, not field.
6|\boldsymbol\omega_R=-\gamma(\mathbf g\cdot\mathbf r)\hat{\mathbf z}|Vector de precesión en el marco giratorio.|Precession vector in the rotating frame.
7|\omega_R=-\gamma\mathbf g\cdot\mathbf r|Reducir a frecuencia escalar para la fase.|Reduce to scalar frequency for phase.
8|M_+=M_0e^{-i\gamma\mathbf g\cdot\mathbf r t},\quad|M_+|=M_0|Distinguir valor complejo de su módulo; fase local pura.|Distinguish complex value from magnitude; pure local phase.
9|\psi=M_0e^{-i\gamma\mathbf g\cdot\mathbf r t}|Renombrar la función compleja para derivarla.|Rename the complex function for differentiation.
10|\partial_t\psi=-i\gamma\mathbf g\cdot\mathbf r M_0e^{-i\gamma\mathbf g\cdot\mathbf r t}|Derivar la exponencial temporal con r fija.|Differentiate the temporal exponential at fixedr.
11|\partial_t\psi=-i\gamma\mathbf g\cdot\mathbf r\psi|Reconocerψ en la derivada para obtener la ODE de fase.|Recognizepsi in the derivative to obtain the phase ODE.
12|\int_{\psi_0}^{\psi}d\psi'/\psi'=-i\gamma\mathbf r\cdot\int_0^t\mathbf g(s)ds|Separar variables y permitir un gradiente temporal.|Separate variables and allow a time-dependent gradient.
13|\ln(\psi/\psi_0)=-i\gamma\mathbf r\cdot\int_0^t\mathbf g(s)ds|Evaluar el logaritmo por integración; rama continua de fase.|Evaluate the logarithm by integration; continuous phase branch.
14|\psi=\psi_0e^{-i\gamma\mathbf r\cdot\mathbf F(t)}|Exponentiar la solución de fase.|Exponentiate the phase solution.
15|\mathbf F(t)=\int_0^t\mathbf g(s)ds|Definir integral del gradiente físico; aún no incorporaRF.|Define physical-gradient integral; RF is not yet included.
16|\partial_t\psi=D\nabla^2\psi|Añadir Fick a la magnetización que viaja con moléculas.|Add Fick to magnetization carried by molecules.
17|\partial_t\psi=-i\gamma\mathbf g\cdot\mathbf r\psi+D\nabla^2\psi|Bloch–Torrey reducido sin relajación ni deriva.|Reduced Bloch–Torrey without relaxation or drift.
18|\psi=A(t)e^{-i\gamma\mathbf r\cdot\mathbf F(t)}|Ansatz de amplitud uniforme por onda espacial antes deRF180.|Uniform-amplitude spatial-wave ansatz before180RF.
19|\psi=A(t)e^{-i\gamma\mathbf r\cdot(\mathbf F(t)-2\mathbf f)}|Después de180 la fase acumulada se invierte; f=F(τRF).|After180 accumulated phase is inverted;f=F(tauRF).
20|\mathbf H=\mathbf F+(\zeta-1)\mathbf f,\quad\psi=Ae^{-i\gamma\mathbf r\cdot\mathbf H}|Unificar intervalos conζ+1 antes y−1 después; aplicar saltoRF explícito.|Unify intervals usingzeta+1 before and−1 after; apply explicit RF jump.
21|\partial_t\psi=(A'-i\gamma\mathbf r\cdot\mathbf H'A)e^{-i\gamma\mathbf r\cdot\mathbf H}|Regla del producto temporal entreRF; no derivar el salto como función suave.|Temporal product rule between RF; do not treat the jump as smooth.
22|\mathbf F'=\mathbf g|Teorema fundamental del cálculo para la integral física.|Fundamental theorem of calculus for the physical integral.
23|\mathbf f'=0,\quad\mathbf f=\mathbf F(\tau_{\rm RF})|El valor fijo en el instanteRF no cambia al derivar t.|Value fixed at RF time does not change when differentiatingt.
24|D\nabla^2\psi=DA\nabla^2e^{-i\gamma\mathbf r\cdot\mathbf H}|A no depende de r y sale del laplaciano.|A is independent ofr and leaves the Laplacian.
25|\nabla e^{-i\gamma\mathbf r\cdot\mathbf H}=-i\gamma\mathbf H e^{-i\gamma\mathbf r\cdot\mathbf H}|Primera derivada espacial de la onda de fase.|First spatial derivative of the phase wave.
26|D\nabla^2\psi=-D\gamma^2|\mathbf H|^2\psi|Segunda derivada aporta signo negativo y cuadrado de frecuencia espacial.|Second derivative gives a negative sign and squared spatial frequency.
27|\partial_t\psi=-i\gamma\mathbf g\cdot\mathbf r\psi-D\gamma^2|\mathbf H|^2\psi|Sustituir el laplaciano en Bloch–Torrey.|Substitute the Laplacian into Bloch–Torrey.
28|A'-i\gamma\mathbf r\cdot\mathbf g A=-i\gamma\mathbf r\cdot\mathbf g A-D\gamma^2|\mathbf H|^2A|Cancelar factores exponenciales y términos idénticos de precesión.|Cancel exponential factors and identical precession terms.
29|A'=-D\gamma^2|\mathbf H|^2A|ODE real de atenuación por difusión.|Real diffusion-attenuation ODE.
30|\ln(A(T)/A_0)=-D\gamma^2\int_0^T|\mathbf H|^2dt|Separar variables e integrar la ODE de amplitud.|Separate variables and integrate the amplitude ODE.
31|\ln(A/A_0)=-D(\gamma g\delta)^2(\Delta-\delta/3)|Resultado rectangular con fondo cero e instante de eco balanceado.|Rectangular result with zero background and balanced echo time.
32|\frac{\ln(A/A_0)}{-D\gamma^2}=\int_0^{\tau}F^2dt+\int_\tau^{2\tau}(F-2f)^2dt|Partir la integral antes y después del pulso180.|Split the integral before and after the180pulse.
33|(F-2f)^2=F^2-4fF+4f^2|Expandir el cuadrado; conservar el término cruzado.|Expand the square; retain the cross term.
34|\int_\tau^{2\tau}(F-2f)^2dt=\int_\tau^{2\tau}F^2dt-4f\int_\tau^{2\tau}Fdt+4f^2\tau|Separar las tres integrales; f es constante.|Separate the three integrals;f is constant.
35|b/\gamma^2=\int_0^{2\tau}F^2dt-4f\int_\tau^{2\tau}Fdt+4f^2\tau|Recombinar términos en una expresión evaluable por intervalos.|Recombine terms into an interval-evaluable expression.
36|g(t)=g_0+g\,\mathbf1_{[t_1,t_1+\delta]}+g\,\mathbf1_{[t_1+\Delta,t_1+\Delta+\delta]}|Definir cinco dominios del gradiente físico, incluido fondo.|Define five physical-gradient domains, including background.
37|F_j(t)=F_j(t_j)+\int_{t_j}^{t}g_j(s)ds|Integrar dominio a dominio manteniendo continuidad deF; RF no reiniciaF físico.|Integrate each domain keepingF continuous; RF does not reset physicalF.
38|b/\gamma^2=\sum_{j=I}^{V}\int_jF_j^2dt-4f\sum_{j=III}^{V}\int_{j\cap[\tau,2\tau]}F_jdt+4f^2\tau|Evaluar las cinco integrales y cruzados con límites correctos, luego fijar g00.|Evaluate five integrals and cross terms with correct bounds, then setg0=0.
A1|q(t)=\gamma\int_0^tp(s)g(s)ds\quad\text{Academy global-clock form}|Comparar p externo del literal con historia ponderada; requiere interpretación de saltosRF.|Compare literal externalp with weighted history; requires RF-jump interpretation.
A2|p(t)=+1\ (t<\tau),\ -1\ (t>\tau)|Especificar trayectoria de coherencia para el pulso180.|Specify coherence pathway for the180pulse.
A3|\partial_t(Ae^{-izq})=(A'-izq'A)e^{-izq}|Versión docente consistente de la derivada temporal entreRF.|Consistent teaching version of the temporal derivative between RF.
A4|D\partial_z^2(Ae^{-izq})=-Dq^2Ae^{-izq}|Versión docente del laplaciano; q ya contiene coherencia yγ.|Teaching Laplacian form;q already contains coherence andgamma.
A5|\partial_t\psi=-i\gamma p(t)g(t)z\psi-Dq^2\psi|Insertar el laplaciano en la ecuación ponderada por coherencia.|Insert the Laplacian into the coherence-weighted equation.
A6|A'-izq'A=-i\gamma pgzA-Dq^2A|Comparar derivada y ecuación, manteniendo q'=γpg.|Compare derivative and equation while retainingq'=gamma*p*g.
A7|A'=-Dq^2A|Cancelar la fase y obtener atenuación; no aplicar p dos veces.|Cancel phase and obtain attenuation; do not applyp twice.
A8|\ln(A/A_0)=-D\int_0^Tq^2dt|Integrar la amplitud; usar q balanceado para recuperarST.|Integrate amplitude; use balancedq to recoverST.
'''}

def roles():
    out={}
    for source,body in ROLE_ROWS.items():
        for line in body.strip().splitlines():
            # Equation text uses norm bars. Split last two separators first.
            head,es,en=line.rsplit('|',2)
            equation,latex=head.split('|',1)
            out[(source,equation)]=(latex,bi(es,en))
    return out

def coverage(data):
    rows=[]
    detail=roles()
    for source,items in page_map().items():
        for eq,page in items.items():
            matches=[]
            for c in data['chapters']:
                for step in c['steps']:
                    if any(r['sourceId']==source and eq in [str(v) for v in r['equations']] for r in step['sourceRefs']):
                        matches.append((c['id'],step['id']))
            latex,note=detail[(source,eq)]
            if (source,eq) in DISCREPANCIES:
                note=bi(note['es']+' '+DISCREPANCIES[(source,eq)]['es'],note['en']+' '+DISCREPANCIES[(source,eq)]['en'])
            rows.append({'sourceId':source,'paperEquation':eq,'pages':[page],
              'journalPages':[page+(38 if source==S else 204)],
              'chapterIds':list(dict.fromkeys(x[0] for x in matches)),
              'stepIds':[x[0]+':'+x[1] for x in matches],
              'rewrittenEquationLatex':latex,'notes':note})
    return rows

def integrate_segments(segments):
    """Exact integrals for the piecewise-constant effective gradient supplied.
    This independently integrates q, not a sequence-specific b formula.
    """
    q=b=u=0.0
    for duration,a in segments:
        assert duration>=0
        b+=q*q*duration+q*a*duration**2+a*a*duration**3/3
        u+=q*duration+a*duration**2/2
        q+=a*duration
    return q,b,u

def waveform(family,shape,delta,Delta,g=0.42,tau=0.0002,alpha=0.0,m=1.0,n=8000):
    segments=[]
    def lobe(duration,amplitude):
        h=duration/n
        segments.extend((h,GAMMA*g*amplitude*shape((j+.5)/n)) for j in range(n))
    if family=='mono':
        lobe(delta,1);segments.append((Delta-delta,0));lobe(delta,-1)
    elif family=='bipolar':
        lobe(delta/2,-(1+alpha));segments.append((tau,0));lobe(delta/2,-(1-alpha))
        segments.append((Delta-delta-tau,0))
        lobe(delta/2,1+m*alpha);segments.append((tau,0));lobe(delta/2,1-m*alpha)
    else: raise ValueError(family)
    return integrate_segments(segments)

def numerical_review():
    cases=[]
    def check(name,actual,expected,rtol=2e-7,atol=1e-6):
        ok=abs(actual-expected)<=max(atol,rtol*abs(expected))
        cases.append({'id':name,'actual':actual,'expected':expected,'rtol':rtol,'atol':atol,'passed':ok})
        if not ok: raise AssertionError(f'{name}: {actual} != {expected}')
    shapes=[('rectangle',lambda x:1.0,1.0,.5,1/3),
            ('sine',lambda x:math.sin(math.pi*x),2/math.pi,.5,3/8),
            ('sine-squared',lambda x:math.sin(math.pi*x)**2,.5,.5,1/3+5/(8*math.pi**2)),
            ('trapezoid',lambda x:10*x if x<.1 else 10*(1-x) if x>.9 else 1.,.9,.5,8483/24300),
            ('smoothed-rectangle',lambda x:math.sin(5*math.pi*x)**2 if x<.1 else math.cos(5*math.pi*(x-.9))**2 if x>.9 else 1.,.9,.5,422/1215+23/(1080*math.pi**2))]
    delta,Delta,g=.0014,.080,.42
    for name,shape,sigma,lam,kappa in shapes:
        # Independent shape moments by midpoint bins and exact primitive moments
        # on each constant bin. This does not use the sequence b formulas.
        nshape=20000;h=1/nshape;H=area=intH=intH2=0.0
        for j in range(nshape):
            a=shape((j+.5)/nshape)
            intH+=H*h+a*h*h/2
            intH2+=H*H*h+H*a*h*h+a*a*h**3/3
            H+=a*h;area+=a*h
        check(name+'-shape-sigma',area,sigma,rtol=2e-8)
        check(name+'-shape-lambda',intH/area,lam,rtol=2e-8)
        check(name+'-shape-kappa',intH2/(area*area),kappa,rtol=2e-8)
        q0=GAMMA*g*delta*sigma
        q,b,u=waveform('mono',shape,delta,Delta,g)
        check(name+'-mono-closure',q,0,atol=1e-7)
        check(name+'-mono-b',b,q0*q0*(Delta+2*(kappa-lam)*delta))
        check(name+'-mono-u',u,q0*Delta)
        tau=.0002
        q,b,u=waveform('bipolar',shape,delta,Delta,g,tau=tau)
        check(name+'-bipolar-closure',q,0,atol=1e-7)
        check(name+'-bipolar-b',b,q0*q0*(Delta+(2*kappa-2*lam-1)*delta/4-tau/2))
        check(name+'-bipolar-u',u,-q0*Delta)
        for alpha,m in [(.2,1),(.2,-1),(.4,.3)]:
            q,b,u=waveform('bipolar',shape,delta,Delta,g,tau=tau,alpha=alpha,m=m)
            theory=q0*q0*(Delta+(kappa-lam)*(alpha*alpha*(1+m*m)+2)*delta/4+(delta+2*tau)*(alpha*alpha*(1+m*m)+2*alpha*(1-m)-2)/8)
            check(f'{name}-oneshot-{alpha}-{m}-b',b,theory)
            check(f'{name}-oneshot-{alpha}-{m}-u',u,-q0*(Delta+alpha*(1-m)*(delta/2+tau)/2))
            check(f'{name}-oneshot-{alpha}-{m}-closure',q,0,atol=1e-7)
        qa,b1,u1=waveform('mono',shape,delta,Delta/2,g)
        check(name+'-double-mono-b',2*b1,q0*q0*(Delta+4*(kappa-lam)*delta))
        q,b1,u1=waveform('bipolar',shape,delta,Delta/2,g,tau=.0002)
        q,b2,u2=waveform('bipolar',shape,delta,Delta/2,g,tau=.0003)
        check(name+'-double-bipolar-b',b1+b2,q0*q0*(Delta+(2*kappa-2*lam-1)*delta/2-(.0002+.0003)/2))
        check(name+'-double-flow-u-cancel',u1-u2,0,atol=1e-7)
    q0=GAMMA*g*delta
    b=q0*q0*(Delta-delta/3)
    check('synthetic-pgse-b',b,1967992551.978492,rtol=1e-12)
    check('rms-1D',math.sqrt(2*8e-10*.08)*1e6,11.313708498984761,rtol=1e-12)
    check('echo-reversal-even-b',waveform('mono',shapes[0][1],delta,Delta,-g)[1],b)
    check('gamma-Hz-mistake-ratio',b/(b/(2*math.pi)**2),4*math.pi**2)
    check('sinc-static-q-zero-limit',math.sin(1e-7)/(1e-7),1,atol=1e-12)
    check('RF-outside-integral-counterexample',-GAMMA*2*g*delta,-2*q0,rtol=1e-12)
    for x in [.001,.01,.1]:
        sinc=math.sin(x)/x
        check(f'sinc-Taylor-{x}',sinc,1-x*x/6,rtol=1e-6,atol=1e-6)
        check(f'sinc-exp-small-{x}',sinc,math.exp(-x*x/6),rtol=1e-6,atol=1e-6)
    check('flow-uniform-not-sqrt6',((1-math.sin(.001)/.001)/(.001**2)),1/6,rtol=1e-6)
    return {'method':'Independent piecewise effective-gradient integration; finite pulse shape quadrature; not experimental validation.',
            'checkCount':len(cases),'passed':all(x['passed'] for x in cases),'cases':cases}

def validate(data):
    assert data['schemaVersion']=='1.0.0'
    ids={c['id'] for c in data['chapters']}
    assert len(ids)==len(data['chapters'])
    for c in data['chapters']:
        assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',c['id'])
        assert len({s['id'] for s in c['steps']})==len(c['steps'])
        missing=set(c['prerequisites'])-ids
        if missing and (data['releaseStatus']=='reviewed' or len(ids)>=20):
            raise AssertionError('Unresolved prerequisites in '+c['id']+': '+str(sorted(missing)))
        assert c['steps'] and c['examples'] and c['questions']
        for s in c['steps']:
            assert s['equationPlain'] and s['equationLatex']
            assert all(s['explanation'].get(l) and s['assumptions'].get(l) for l in ['es','en'])
            for r in s['sourceRefs']:
                source=next(x for x in data['sources'] if x['id']==r['sourceId'])
                assert all(1<=p<=source['pages'] for p in r['pages'])
        for q in c['questions']:
            assert 0<=q['correctIndex']<len(q['options'])
    print('Structure passed; release gate requires reviewed coverage and numerical checks.')

def freeze(data):
    validate(data)
    assert len(data['chapters'])==20, 'All20 chapters are required.'
    data['equationCoverage']=coverage(data)
    assert len(data['equationCoverage'])==111
    uncovered=[x for x in data['equationCoverage'] if not x['chapterIds']]
    assert not uncovered, 'Uncovered numbered equations: '+str([(x['sourceId'],x['paperEquation']) for x in uncovered])
    numbers=numerical_review()
    data['releaseStatus']='reviewed'
    data['validationBoundary']=bi('Cobertura y comprobaciones matemáticas docentes; no validación experimental ni ejecución de hardware.','Teaching mathematical coverage and checks; no experimental validation or hardware execution.')
    OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report={'schemaVersion':'1.0.0','status':'reviewed','contentFile':'content/derivations.json',
      'contentSha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),
      'counts':{'chapters':len(data['chapters']),'steps':sum(len(c['steps']) for c in data['chapters']),
                'examples':sum(len(c['examples']) for c in data['chapters']),'questions':sum(len(c['questions']) for c in data['chapters']),
                'numberedEquations':111,'SinnaeveEquations':65,'KuchelEquations':46},
      'sourceImagesPrivateOnly':True,'pagesConvention':data['pagesConvention'],
      'literalDiscrepancies':[{'sourceId':s,'paperEquation':e,'pages':[page_map()[s][e]],'notes':note} for (s,e),note in DISCREPANCIES.items()],
      'numericalReview':numbers,'trainingBoundary':'RAG/source supplement only; existing trained model and frozen course unchanged.',
      'independentReview':'Root visually checked source discrepancies; chapter fragments reviewed separately by contributing agents; mathematical assertions are testable, not experimental claims.'}
    (REVIEW/'scientific-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'review':str(REVIEW/'scientific-review.json'),'sha256':report['contentSha256'],'counts':report['counts'],'numericalChecks':numbers['checkCount']}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--build',action='store_true');parser.add_argument('--freeze',action='store_true');parser.add_argument('--numerical-only',action='store_true');args=parser.parse_args()
    if args.numerical_only:
        print(json.dumps(numerical_review(),ensure_ascii=False,indent=2));raise SystemExit(0)
    doc=build() if args.build else json.loads(OUT.read_text(encoding='utf-8'))
    freeze(doc) if args.freeze else validate(doc)
