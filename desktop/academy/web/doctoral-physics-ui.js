/* Offline bilingual interface for the auditable doctoral physics model.
   No network, instrument access, LLM calls or hidden experimental data. */
(function(root,factory){'use strict';const api=factory(root);if(typeof module==='object'&&module.exports)module.exports=api;else root.AcademyDoctoralPhysicsUI=api;})(typeof window!=='undefined'?window:globalThis,function(root){
  'use strict';
  function mount(container,language='es',options={}) {
    if(!container||typeof document==='undefined')throw new TypeError('A DOM container is required.');
    const P=root.AcademyDoctoralPhysics;if(!P)throw new Error('Load doctoral-physics.js first.');
    let lang=language==='en'?'en':'es',destroyed=false,raf=0,playing=false,lastStamp=0;
    const FRAMES=240;
    let sequence,ensemble,current,history=[],comparison=null,error='',assessment=null,frameIndex=0,playAccumulator=0;
    const start=options.initialState&&typeof options.initialState==='object'?options.initialState:{};
    const defaults=P.preset('pgse');
    let state={view:options.view==='sequence'?'sequence':'sync',preset:'pgse',segments:defaults.segments.map(s=>({...s})),
      sim:{diffusionM2PerS:1e-9,sampleLengthMeters:240e-6,velocityMode:'none',velocityMPerS:200e-6,velocitySpreadMPerS:400e-6},
      seed:20261005,count:512,selectedParticle:0,timeFraction:0,revealed:false,predictions:[],assessment:null,comparison:null};
    if(start.version==='1.2.0'){
      try {
        const test=P.compileSequence({segments:start.segments});
        P.signal(test,start.sim||{});
        if(!Number.isInteger(start.seed)||start.seed<0||start.seed>4294967295)throw new Error('Invalid stored seed.');
        if(![128,512,2048].includes(start.count))throw new Error('Invalid stored ensemble size.');
        state={...state,preset:['pgse','ste','double-ste','custom'].includes(start.preset)?start.preset:'custom',segments:start.segments.map(s=>({...s})),
          sim:{...state.sim,...start.sim},seed:start.seed,count:start.count,
          selectedParticle:Number.isInteger(start.selectedParticle)?Math.max(0,Math.min(start.count-1,start.selectedParticle)):0,
          timeFraction:Number.isFinite(start.timeFraction)?Math.max(0,Math.min(1,start.timeFraction)):0,
          revealed:start.revealed===true,predictions:Array.isArray(start.predictions)?start.predictions.slice(0,64):[]};
      }catch(_) {error='stored-state-invalid';}
    }
    const T=(es,en)=>lang==='en'?en:es;
    const escape=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const f=(x,d=3)=>Number(x).toLocaleString(lang==='en'?'en-US':'es-ES',{maximumSignificantDigits:d});
    const el=key=>container.querySelector('[data-dp="'+key+'"]');
    function notify(kind,decision,status,evidence) {
      if(typeof options.onProgress==='function')options.onProgress({activityId:state.view==='sequence'?'sequence-builder':'molecules-to-echo',kind,
        parameters:{preset:state.preset,segments:state.segments.map(s=>({...s})),...state.sim,count:state.count,seed:state.seed},
        decision,evidence,status,evidenceStatus:'synthetic-teaching-simulation'});
    }
    function sequenceInput() {
      if(state.preset!=='custom'){
        const base=P.preset(state.preset);
        return {...base,segments:state.segments};
      }
      return {segments:state.segments,preset:'custom'};
    }
    function advanceToFrame(target) {
      const end=Math.max(frameIndex,Math.min(FRAMES,target));
      while(frameIndex<end){frameIndex++;const t=sequence.totalSeconds*frameIndex/FRAMES;current=ensemble.advance(t);history.push({t,real:current.real,imag:current.imag,magnitude:current.magnitude});}
      state.timeFraction=frameIndex/FRAMES;
    }
    function rebuild(preserveTime=false) {
      playing=false;cancelAnimationFrame(raf);
      try {
        sequence=P.compileSequence(sequenceInput());
        ensemble=P.createEnsemble(sequence,{...state.sim,count:state.count,seed:state.seed});
        const target=preserveTime?Math.round(state.timeFraction*FRAMES):0;
        current=ensemble.snapshot();frameIndex=0;history=[{t:0,real:1,imag:0,magnitude:1}];playAccumulator=0;
        advanceToFrame(target);
        if(error!=='stored-state-invalid')error='';
        comparison=null;assessment=null;state.comparison=null;
      }catch(e){error=e.message;sequence=null;ensemble=null;current=null;}
    }
    function segmentRows() {
      return state.segments.map((s,i)=>'<tr data-row="'+i+'"><th scope="row">'+(i+1)+'</th><td><input data-field="durationMs" data-testid="segment-duration-'+i+'" type="number" min="0.001" max="10000" step="0.1" value="'+s.durationMs+'" aria-label="'+T('Duración del tramo ','Segment duration ')+(i+1)+'"></td><td><input data-field="gradientMilliTeslaPerM" data-testid="segment-gradient-'+i+'" type="number" min="-2000" max="2000" step="10" value="'+s.gradientMilliTeslaPerM+'" aria-label="'+T('Gradiente del tramo ','Segment gradient ')+(i+1)+'"></td><td><select data-field="coherence" data-testid="segment-coherence-'+i+'" aria-label="'+T('Coherencia del tramo ','Segment coherence ')+(i+1)+'">'+[1,0,-1].map(p=>'<option value="'+p+'"'+(p===s.coherence?' selected':'')+'>'+ (p===1?'+1':p===-1?'−1':'0 · '+T('almacenado','stored'))+'</option>').join('')+'</select></td><td><div class="dp-row-actions"><button type="button" data-action="row-up" data-index="'+i+'" '+(i===0?'disabled':'')+' aria-label="'+T('Subir tramo','Move segment up')+'">↑</button><button type="button" data-action="row-down" data-index="'+i+'" '+(i===state.segments.length-1?'disabled':'')+' aria-label="'+T('Bajar tramo','Move segment down')+'">↓</button><button type="button" data-action="row-remove" data-index="'+i+'" '+(state.segments.length===1?'disabled':'')+' aria-label="'+T('Eliminar tramo','Remove segment')+'">×</button></div></td></tr>').join('');
    }
    function predictionRows() {
      return state.segments.map((_,i)=>'<label><span>q'+(i+1)+' / 10⁴ rad·m⁻¹</span><input data-prediction="'+i+'" type="number" step="0.1" value="'+(state.predictions[i]===undefined?'':escape(state.predictions[i]))+'" aria-label="'+T('Predicción q al final del tramo ','Predicted q at end of segment ')+(i+1)+'"></label>').join('');
    }
    function markup() {
      const sync=state.view==='sync';
      container.innerHTML='<section class="dp-root" data-testid="doctoral-physics" data-view="'+state.view+'" lang="'+lang+'"><header class="dp-header"><div><p class="dp-eyebrow">'+T('DOCTORADO · DE LA MOLÉCULA A LA MEDIDA','DOCTORAL LAB · FROM MOLECULE TO MEASUREMENT')+'</p><h2>'+T(sync?'Las moléculas se mueven. El eco recuerda cómo.':'Diseña la historia de gradiente; justifica la ecuación.',sync?'Molecules move. The echo remembers how.':'Design the gradient history; justify the equation.')+'</h2><p>'+T('Predice primero, cambia una condición y observa la evidencia. Cada panel muestra el mismo experimento sintético y el mismo instante.','Predict first, change one condition and observe the evidence. Every panel shows the same synthetic experiment at the same instant.')+'</p></div><span class="dp-badge">'+T('Simulación · sin control instrumental','Simulation · no instrument control')+'</span></header>'+
        '<div class="dp-principle"><strong>'+T('Autodifusión sin transporte neto','Self-diffusion without net transport')+'</strong><p>'+T('En equilibrio, cada molécula cambia de posición aunque el desplazamiento medio del conjunto sea aproximadamente cero. Un gradiente etiqueta posiciones con fase; el eco prueba cuánto se conserva esa etiqueta. En este modelo el gradiente no ejerce una fuerza que impulse las moléculas: codifica su posición.','At equilibrium each molecule changes position although the ensemble mean displacement is approximately zero. A gradient labels position with phase; the echo tests how well that label survives. In this model the gradient does not exert a force driving molecules: it encodes their position.')+'</p></div>'+
        '<div class="dp-error" data-dp="error" role="alert" hidden></div>'+
        '<div class="dp-controls"><label>'+T('Secuencia ideal','Ideal sequence')+'<select data-dp="preset" data-testid="physics-preset"><option value="pgse"'+(state.preset==='pgse'?' selected':'')+'>PGSE</option><option value="ste"'+(state.preset==='ste'?' selected':'')+'>'+T('Eco estimulado (STE)','Stimulated echo (STE)')+'</option><option value="double-ste"'+(state.preset==='double-ste'?' selected':'')+'>'+T('Doble STE · compensación','Double STE · compensation')+'</option><option value="custom"'+(state.preset==='custom'?' selected':'')+'>'+T('Mi diseño','My design')+'</option></select></label><label>D (10⁻⁹ m²/s)<input data-dp="D" type="number" min="0" max="1000" step="0.1" value="'+state.sim.diffusionM2PerS/1e-9+'"></label><label>'+T('Ventana inicial (µm)','Initial slab (µm)')+'<input data-dp="L" type="number" min="0.001" max="100000" step="20" value="'+state.sim.sampleLengthMeters*1e6+'"></label><label>'+T('Movimiento de traslación','Translation motion')+'<select data-dp="velocityMode"><option value="none"'+(state.sim.velocityMode==='none'?' selected':'')+'>'+T('Sin flujo','No flow')+'</option><option value="uniform"'+(state.sim.velocityMode==='uniform'?' selected':'')+'>'+T('Una velocidad común','One common velocity')+'</option><option value="distribution"'+(state.sim.velocityMode==='distribution'?' selected':'')+'>'+T('Distribución de velocidades','Velocity distribution')+'</option></select></label><label>'+T('Velocidad media (µm/s)','Mean velocity (µm/s)')+'<input data-dp="v" type="number" min="-100000" max="100000" step="10" value="'+state.sim.velocityMPerS*1e6+'"></label><label>'+T('Semianchura uniforme (µm/s)','Uniform half-width (µm/s)')+'<input data-dp="vmax" type="number" min="0" max="100000" step="10" value="'+state.sim.velocitySpreadMPerS*1e6+'"></label><label>'+T('Moléculas del conjunto','Ensemble molecules')+'<select data-dp="count">'+[128,512,2048].map(n=>'<option'+(state.count===n?' selected':'')+'>'+n+'</option>').join('')+'</select></label><label>'+T('Semilla reproducible','Reproducible seed')+'<input data-dp="seed" type="number" min="0" max="4294967295" step="1" value="'+state.seed+'"></label></div>'+
        '<p class="dp-small">'+T('Presets: δ=1,5 ms, g=200 mT/m y Δ=60 ms entre comienzos de cada bloque; edita esos tiempos y amplitudes en la tabla. En doble STE, Δ=60 ms en cada uno de los dos bloques: no es el Δ total de la figura del artículo.','Presets: δ=1.5 ms, g=200 mT/m and leading-edge Δ=60 ms per block; edit those timings and amplitudes in the table. In double STE, Δ=60 ms in each of two blocks: it is not the article figure’s total Δ.')+'</p>'+
        '<div class="dp-sync"'+(!sync?' hidden':'')+'><div class="dp-flow-labels"><span>01 '+T('Posiciones','Positions')+'</span><span>02 '+T('Fase individual','Individual phase')+'</span><span>03 '+T('Suma compleja','Complex sum')+'</span><span>04 '+T('Eco observado','Observed echo')+'</span></div><div class="dp-panels">'+
        '<figure class="dp-panel"><figcaption><b>01 · '+T('El movimiento es aleatorio','Motion is random')+'</b><span>'+T('Cada punto es una trayectoria; el color sigue su fase.','Each dot is a trajectory; its color follows its phase.')+'</span></figcaption><canvas data-dp="molecules" width="480" height="230" role="img" aria-label="'+T('Trayectorias moleculares sobre el eje z','Molecular trajectories along z')+'"></canvas><p data-dp="displacement" class="dp-caption"></p></figure>'+
        '<figure class="dp-panel"><figcaption><b>02 · '+T('La etiqueta de fase se dispersa','The phase label spreads')+'</b><span>'+T('Se muestra φ módulo 2π; fase acumulada en la ficha.','Shown: φ modulo 2π; accumulated phase in the particle card.')+'</span></figcaption><canvas data-dp="phase" width="480" height="230" role="img" aria-label="'+T('Fase de cada molécula frente a posición','Each molecule’s phase versus position')+'"></canvas><p data-dp="particle" class="dp-caption"></p></figure>'+
        '<figure class="dp-panel"><figcaption><b>03 · '+T('Los vectores se suman con signo','Vectors add with sign')+'</b><span>'+T('Flecha gruesa: promedio de todos los vectores, no promedio de módulos.','Thick arrow: mean of all vectors, not mean of their magnitudes.')+'</span></figcaption><canvas data-dp="vectors" width="480" height="230" role="img" aria-label="'+T('Vectores unitarios y señal compleja media','Unit phasors and mean complex signal')+'"></canvas><p data-dp="storage" class="dp-caption"></p></figure>'+
        '<figure class="dp-panel"><figcaption><b>04 · '+T('Refocar posición no deshace el movimiento','Refocusing position does not undo motion')+'</b><span>'+T('Azul: Re E; coral: Im E; verde: |E|. Línea fina: predicción analítica.','Blue: Re E; coral: Im E; green: |E|. Thin line: analytic prediction.')+'</span></figcaption><canvas data-dp="echo" width="480" height="230" role="img" aria-label="'+T('Historia temporal del eco complejo','Complex-echo time history')+'"></canvas><p data-dp="echo-note" class="dp-caption"></p></figure></div></div>'+
        '<div class="dp-transport"'+(!sync?' hidden':'')+'><div class="dp-buttons"><button data-action="play" data-testid="physics-play" type="button">▶ '+T('Reproducir','Play')+'</button><button data-action="reset" type="button">↺ '+T('Reiniciar la misma semilla','Reset the same seed')+'</button><button data-action="finish" type="button">'+T('Ir al eco final','Go to final echo')+' →</button></div><label class="dp-time-label">'+T('Instante de la secuencia','Sequence time')+'<input data-dp="time" data-testid="physics-time" type="range" min="0" max="1000" step="1" value="'+Math.round(state.timeFraction*1000)+'"></label><div class="dp-time" data-dp="time-label"></div><label class="dp-follow">'+T('Seguir molécula','Follow molecule')+'<input data-dp="selected" type="number" min="0" max="'+(state.count-1)+'" step="1" value="'+state.selectedParticle+'"></label></div>'+
        '<div class="dp-metrics" data-dp="metrics" aria-live="polite"></div>'+
        '<details class="dp-editor"'+(!sync?' open':'')+'><summary>'+T('Constructor: gradiente físico × vía de coherencia','Builder: physical gradient × coherence pathway')+'</summary><p>'+T('Edita intervalos rectangulares. Cada frontera con cambio de p representa una transferencia RF ideal de la vía seleccionada; el diagrama marca 90° o 180° ilustrativos. p=0 almacena una modulación: q no vuelve a cero.','Edit rectangular intervals. Every boundary with changed p represents an ideal RF transfer of the selected pathway; the diagram marks illustrative 90° or 180° pulses. p=0 stores a modulation: q does not return to zero.')+'</p><div class="dp-table-scroll"><table class="dp-segment-table"><thead><tr><th>#</th><th>'+T('Duración (ms)','Duration (ms)')+'</th><th>g (mT/m)</th><th>p</th><th>'+T('Orden','Order')+'</th></tr></thead><tbody data-dp="segments">'+segmentRows()+'</tbody></table></div><div class="dp-buttons"><button data-action="row-add" type="button">+ '+T('Añadir intervalo','Add interval')+'</button><button data-action="mistake" type="button">'+T('Reto: eliminar la inversión de coherencia','Challenge: remove coherence inversion')+'</button><button data-action="restore" type="button">'+T('Restaurar preset','Restore preset')+'</button></div><p class="dp-small">'+T('El reto modifica realmente la secuencia y lo señala. No se inserta un error oculto en los resultados. Se calculan q, b y u de tus intervalos, sin fórmulas universales para p30, d20 o d5.','The challenge actually changes the sequence and labels it. No hidden error is inserted into results. q, b and u are calculated from your intervals, with no universal formula for p30, d20 or d5.')+'</p></details>'+
        '<section class="dp-prediction"><div><p class="dp-eyebrow">'+T('PREDICE ANTES DE REVELAR','PREDICT BEFORE REVEALING')+'</p><h3>'+T('¿Dónde termina q después de cada intervalo?','Where does q end after each interval?')+'</h3><p>qₖ₊₁ = qₖ + γ pₖ gₖ hₖ · '+T('Convierte primero ms y mT/m a SI.','Convert ms and mT/m to SI first.')+'</p></div><div class="dp-prediction-fields" data-dp="predictions">'+predictionRows()+'</div><div class="dp-buttons"><button data-action="check-prediction" data-testid="physics-check-q" type="button">'+T('Comprobar mi predicción','Check my prediction')+'</button><button data-action="reveal" data-testid="physics-reveal" class="dp-secondary" type="button">'+T('Revelar con explicación','Reveal with explanation')+'</button><button data-action="hide" class="dp-secondary" type="button">'+T('Volver a predecir','Predict again')+'</button></div><div class="dp-feedback" data-dp="prediction-feedback" role="status"></div></section>'+
        '<figure class="dp-sequence-figure"><svg data-dp="sequence-chart" data-testid="physics-sequence-chart" viewBox="0 0 900 410" role="img" aria-label="'+T('RF, gradiente físico, coherencia, q y b en el tiempo','RF, physical gradient, coherence, q and b over time')+'"></svg><figcaption>'+T('Azul: g físico. Coral: p. Verde: q acumulado. Violeta: b acumulado. Las zonas sombreadas son almacenamiento p=0.','Blue: physical g. Coral: p. Green: cumulative q. Violet: cumulative b. Shaded regions are storage p=0.')+'</figcaption></figure>'+
        '<section class="dp-comparison"><h3>'+T('Una velocidad común cambia fase. Una distribución puede cancelar señal.','A common velocity changes phase. A distribution can cancel signal.')+'</h3><p>'+T('Compara el mismo D, la misma secuencia y las mismas trayectorias brownianas. Conserva Re E, Im E y |E| para distinguir rotación de pérdida de módulo.','Compare the same D, the same sequence and the same Brownian trajectories. Retain Re E, Im E and |E| to distinguish rotation from magnitude loss.')+'</p><button data-action="compare" data-testid="physics-compare" type="button">'+T('Comparar los tres modelos al eco final','Compare all three models at the final echo')+'</button><div data-dp="comparison"></div></section>'+
        '<details class="dp-model"><summary>'+T('Qué se calcula, por qué y qué no demuestra','What is calculated, why, and what it does not establish')+'</summary><div class="dp-equations">a = γ p g ; q(t) = ∫₀ᵗ a(s) ds<br>Δb = h(q₀² + q₀q₁ + q₁²)/3 ; Δu = h(q₀ + q₁)/2<br>q(T)=0 ⇒ E = exp(−Db) · exp(iv u)<br>'+T('Distribución uniforme de velocidades','Uniform velocity distribution')+': E = exp(−Db + iv̄u) · sinc(vmax u)</div><p>'+T('Convención: Ψ∝exp(−iqz), γ angular. b tiene unidades s/m²; u tiene s/m; q tiene rad/m. La velocidad constante común añade fase; una distribución añade su función característica. sinc(x)=sin(x)/x puede ser negativa.','Convention: Ψ∝exp(−iqz), angular γ. b has units s/m²; u has s/m; q has rad/m. One constant shared velocity adds phase; a velocity distribution adds its characteristic function. sinc(x)=sin(x)/x can be negative.')+'</p><p>'+T('La ecuación de Fick también describe la probabilidad de desplazamiento de etiquetas en este modelo libre ideal. PFG-RMN mide autodifusión de moléculas seleccionadas por resonancia; el coeficiente de difusión colectiva o mutua obtenido de un gradiente de concentración puede ser distinto en mezclas con interacciones. No se igualan por defecto.','Fick’s equation also describes label displacement probability in this ideal free model. PFG-NMR measures self-diffusion of molecules selected by resonance; a collective or mutual diffusion coefficient measured from a concentration gradient can differ in interacting mixtures. They are not equated by default.')+'</p><p>'+T('La simulación selecciona un conjunto inicialmente uniforme en una ventana finita de una muestra en equilibrio, lo sigue en difusión libre y detecta todas esas moléculas con el mismo peso aunque salgan de la ventana. No modela una muestra física confinada ni un perfil de bobina real. No hay paredes reflectantes. Cuando q(t)≠0, la selección espacial importa: E(t)=sinc[q(t)L/2] exp{−D∫₀ᵗ[q(t)−q(s)]²ds} exp{iv[u(t)−q(t)t]}, multiplicado por la función característica de la distribución de velocidades. No se usa exp(−Db) fuera de su condición de eco balanceado.','The simulation selects a cohort initially uniform within a finite slab of an equilibrium sample, follows its free diffusion, and equally detects all those molecules even after they leave the slab. It does not model a physically confined sample or a real coil profile. There are no reflecting walls. When q(t)≠0 spatial selection matters: E(t)=sinc[q(t)L/2] exp{−D∫₀ᵗ[q(t)−q(s)]²ds} exp{iv[u(t)−q(t)t]}, multiplied by the velocity-distribution characteristic function. exp(−Db) is not used outside its balanced-echo condition.')+'</p><p>'+T('La fase se integra mediante el área browniana gaussiana exacta dentro de cada tramo constante, conjuntamente con su desplazamiento. El color y los vectores siguen la componente Fourier de la vía seleccionada. Durante p=0, Mz físico es real: los vectores representan coeficientes de la modulación, no magnetización longitudinal compleja.','Phase is integrated using the exact Gaussian Brownian area within each constant segment jointly with displacement. Color and vectors follow the selected pathway’s Fourier coefficient. During p=0 physical Mz is real: vectors represent modulation coefficients, not complex longitudinal magnetization.')+'</p><p>'+T('Se muestra eco normalizado a la vía seleccionada. STE y doble STE ideales conservan respectivamente 1/2 y 1/4 de la amplitud inicial antes de relajación; se indica ese coste por separado. No se modelan T1/T2, restricciones, intercambio, turbulencia, calentamiento ni respuesta real del gradiente.','Echo is normalized to the selected pathway. Ideal STE and double STE retain respectively 1/2 and 1/4 of initial amplitude before relaxation; this cost is reported separately. T1/T2, restriction, exchange, turbulence, heating and real gradient response are not modeled.')+'</p><p>'+T('Objetivo: justificar por qué b acumula q² aunque el gradiente esté apagado, qué cambia al almacenar en z, y qué control separa difusión de flujo. Una simulación o un buen ajuste no calibran el espectrómetro.','Objective: explain why b accumulates q² even with the gradient off, what changes during z storage, and which control separates diffusion from flow. A simulation or a good fit does not calibrate a spectrometer.')+'</p><p class="dp-small">'+T('Fuentes: Sinnaeve (2012), ecuaciones 26–31 y 62–65; Kuchel et al. (2012), derivación completa de Stejskal–Tanner. Derivaciones revisadas de Academy: coherence-pathways, arbitrary-waveform, convection y double-ste.','Sources: Sinnaeve (2012), equations 26–31 and 62–65; Kuchel et al. (2012), complete Stejskal–Tanner derivation. Academy reviewed derivations: coherence-pathways, arbitrary-waveform, convection and double-ste.')+' <a href="https://doi.org/10.1002/cmr.a.21223" target="_blank" rel="noopener">10.1002/cmr.a.21223</a> · <a href="https://doi.org/10.1002/cmr.a.21241" target="_blank" rel="noopener">10.1002/cmr.a.21241</a></p></details></section>';
    }
    function canvas(key) {
      const node=el(key),ctx=node.getContext('2d');
      ctx.clearRect(0,0,node.width,node.height);ctx.font='12px Segoe UI, system-ui';ctx.lineWidth=1;return {ctx,w:node.width,h:node.height};
    }
    const color=phase=>'hsl('+(((phase/(2*Math.PI)*360)%360+360)%360)+',62%,48%)';
    const wrap=phase=>Math.atan2(Math.sin(phase),Math.cos(phase));
    function drawMolecules() {
      const {ctx,w,h}=canvas('molecules'),range=state.sim.sampleLengthMeters/2+4*Math.sqrt(2*state.sim.diffusionM2PerS*sequence.totalSeconds)+(Math.abs(state.sim.velocityMPerS)+state.sim.velocitySpreadMPerS)*sequence.totalSeconds;
      const X=z=>30+(w-60)*(z+range)/(2*range);
      ctx.fillStyle='#edf5f6';ctx.fillRect(30,35,w-60,135);ctx.strokeStyle='#a7c1cc';ctx.strokeRect(30,35,w-60,135);
      ctx.strokeStyle='#d5e4e8';ctx.setLineDash([3,3]);ctx.beginPath();ctx.moveTo(X(0),35);ctx.lineTo(X(0),170);ctx.stroke();ctx.setLineDash([]);
      const particles=current.particles.slice(0,Math.min(current.particles.length,160));
      particles.forEach(p=>{const y=102+p.transverse*57;ctx.strokeStyle='#c1d5d9';ctx.beginPath();ctx.moveTo(X(p.initialZMeters),y);ctx.lineTo(X(p.zMeters),y);ctx.stroke();ctx.fillStyle=color(p.phaseRad);ctx.beginPath();ctx.arc(X(p.zMeters),y,p.index===state.selectedParticle?6:3.3,0,Math.PI*2);ctx.fill();});
      const selected=current.particles[state.selectedParticle];
      if(selected){const y=102+selected.transverse*57;ctx.strokeStyle='#163a4f';ctx.lineWidth=2;ctx.beginPath();ctx.arc(X(selected.zMeters),y,9,0,Math.PI*2);ctx.stroke();}
      ctx.fillStyle='#536d7a';ctx.fillText('z ('+'µm'+')',w-77,h-21);ctx.fillText(f(-range*1e6),30,195);ctx.fillText('0',X(0)-4,195);ctx.fillText(f(range*1e6),w-73,195);
      el('displacement').textContent=T('⟨Δz⟩ = ','⟨Δz⟩ = ')+f(current.meanDisplacementMeters*1e6)+' µm · '+T('RMS desplazamiento','RMS displacement')+' = '+f(Math.sqrt(current.meanSquaredDisplacementMeters2)*1e6)+' µm';
    }
    function drawPhase() {
      const {ctx,w,h}=canvas('phase'),range=state.sim.sampleLengthMeters/2+4*Math.sqrt(2*state.sim.diffusionM2PerS*sequence.totalSeconds)+(Math.abs(state.sim.velocityMPerS)+state.sim.velocitySpreadMPerS)*sequence.totalSeconds;
      const X=z=>44+(w-70)*(z+range)/(2*range),Y=phi=>110-phi*25;
      ctx.strokeStyle='#b8cbd2';ctx.beginPath();ctx.moveTo(44,30);ctx.lineTo(44,191);ctx.lineTo(w-26,191);ctx.stroke();ctx.fillStyle='#536d7a';ctx.fillText('π',20,35);ctx.fillText('0',22,114);ctx.fillText('−π',13,192);ctx.fillText('z (µm)',w-83,212);
      ctx.strokeStyle='#e0e9ec';ctx.beginPath();ctx.moveTo(44,110);ctx.lineTo(w-26,110);ctx.stroke();
      current.particles.slice(0,256).forEach(p=>{ctx.fillStyle=color(p.phaseRad);ctx.beginPath();ctx.arc(X(p.zMeters),Y(wrap(p.phaseRad)),p.index===state.selectedParticle?6:2.6,0,Math.PI*2);ctx.fill();});
      const p=current.particles[state.selectedParticle];
      if(p&&state.selectedParticle>=256){ctx.fillStyle=color(p.phaseRad);ctx.beginPath();ctx.arc(X(p.zMeters),Y(wrap(p.phaseRad)),6,0,Math.PI*2);ctx.fill();}
      el('particle').textContent=p?T('Molécula ','Molecule ')+p.index+': Δz = '+f((p.zMeters-p.initialZMeters)*1e6)+' µm · φ = '+f(p.phaseRad)+' rad':'';
    }
    function drawVectors() {
      const {ctx,w,h}=canvas('vectors'),cx=150,cy=112,r=82;
      ctx.strokeStyle='#c6d7dd';ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);ctx.stroke();ctx.beginPath();ctx.moveTo(cx-r-9,cy);ctx.lineTo(cx+r+9,cy);ctx.moveTo(cx,cy-r-9);ctx.lineTo(cx,cy+r+9);ctx.stroke();
      ctx.globalAlpha=.2;current.particles.slice(0,96).forEach(p=>{ctx.strokeStyle=color(p.phaseRad);ctx.beginPath();ctx.moveTo(cx,cy);ctx.lineTo(cx+r*Math.cos(p.phaseRad),cy-r*Math.sin(p.phaseRad));ctx.stroke();});ctx.globalAlpha=1;
      const selected=current.particles[state.selectedParticle];if(selected){ctx.lineWidth=2;ctx.strokeStyle=color(selected.phaseRad);ctx.beginPath();ctx.moveTo(cx,cy);ctx.lineTo(cx+r*Math.cos(selected.phaseRad),cy-r*Math.sin(selected.phaseRad));ctx.stroke();}
      const x=cx+r*current.real,y=cy-r*current.imag;ctx.lineWidth=4;ctx.strokeStyle='#185b87';ctx.beginPath();ctx.moveTo(cx,cy);ctx.lineTo(x,y);ctx.stroke();ctx.fillStyle='#185b87';ctx.beginPath();ctx.arc(x,y,5,0,Math.PI*2);ctx.fill();
      ctx.fillStyle='#536d7a';ctx.font='12px Segoe UI, system-ui';ctx.fillText('Re E',250,115);ctx.fillText('Im E',134,17);ctx.fillStyle='#173d50';ctx.font='bold 15px Segoe UI';ctx.fillText('Re E = '+f(current.real),296,74);ctx.fillText('Im E = '+f(current.imag),296,103);ctx.fillText('|E| = '+f(current.magnitude),296,132);ctx.font='11px Segoe UI';ctx.fillStyle='#68828e';ctx.fillText(T('Todos los '+state.count+' vectores','All '+state.count+' phasors'),296,167);
      el('storage').textContent=current.analytic.coherence===0?T('p=0: se representan coeficientes de la modulación almacenada; Mz físico es real.','p=0: displayed vectors are stored-modulation coefficients; physical Mz is real.'):T('p≠0: componente transversal de la vía seleccionada.','p≠0: transverse component of the selected pathway.');
    }
    function drawEcho() {
      const {ctx,w,h}=canvas('echo'),X=t=>42+(w-67)*t/sequence.totalSeconds,Y=y=>185-(y+1.05)*75;
      ctx.strokeStyle='#b8cbd2';ctx.beginPath();ctx.moveTo(42,23);ctx.lineTo(42,185);ctx.lineTo(w-25,185);ctx.stroke();ctx.strokeStyle='#e4ebee';ctx.beginPath();ctx.moveTo(42,Y(0));ctx.lineTo(w-25,Y(0));ctx.stroke();ctx.fillStyle='#536d7a';ctx.fillText('1',24,Y(1)+4);ctx.fillText('0',24,Y(0)+4);ctx.fillText('−1',17,Y(-1)+4);ctx.fillText('t (ms)',w-83,210);
      const fine=[];for(let i=0;i<=220;i++){const t=sequence.totalSeconds*i/220,a=P.signal(sequence,state.sim,t);fine.push({t,...a});}
      [['real','#276b9c'],['imag','#da7865'],['magnitude','#148d79']].forEach(([key,c])=>{
        ctx.lineWidth=1;ctx.globalAlpha=.43;ctx.strokeStyle=c;ctx.beginPath();fine.forEach((p,i)=>i?ctx.lineTo(X(p.t),Y(p[key])):ctx.moveTo(X(p.t),Y(p[key])));ctx.stroke();ctx.globalAlpha=1;ctx.lineWidth=2.4;ctx.beginPath();history.forEach((p,i)=>i?ctx.lineTo(X(p.t),Y(p[key])):ctx.moveTo(X(p.t),Y(p[key])));ctx.stroke();
      });
      ctx.strokeStyle='#536d7a';ctx.setLineDash([3,3]);ctx.beginPath();ctx.moveTo(X(current.timeSeconds),23);ctx.lineTo(X(current.timeSeconds),185);ctx.stroke();ctx.setLineDash([]);
      el('echo-note').textContent=T('Monte Carlo: SE(Re) = ','Monte Carlo: SE(Re) = ')+f(current.standardErrorReal)+'; SE(Im) = '+f(current.standardErrorImag)+'. '+(current.analytic.coherence===0?T('p=0: no hay señal transversal detectable; se sigue el coeficiente de la vía almacenada.','p=0: there is no detectable transverse signal; the stored-pathway coefficient is followed.'):T('La dispersión disminuye al aumentar N.','Scatter decreases as N increases.'));
    }
    function sequenceChart() {
      if(!sequence){el('sequence-chart').replaceChildren();return;}
      const X=t=>78+790*t/sequence.totalSeconds,rows={g:92,p:158,q:238,b:322},maxG=Math.max(1,...sequence.segments.map(s=>Math.abs(s.gradientMilliTeslaPerM))),maxQ=Math.max(1,...sequence.segments.map(s=>Math.abs(s.qStartRadPerM)),...sequence.segments.map(s=>Math.abs(s.qEndRadPerM))),maxB=Math.max(1,sequence.bSecondsPerM2);
      let svg='<rect width="900" height="410" fill="#fff"/>';
      sequence.segments.filter(s=>s.coherence===0).forEach(s=>{svg+='<rect x="'+X(s.startSeconds)+'" y="45" width="'+(X(s.endSeconds)-X(s.startSeconds))+'" height="318" fill="#eff3fa"/>';});
      [['g',T('g físico','physical g')],['p','p'],['q','q(t)'],['b','b(t)']].forEach(([key,name])=>{svg+='<path d="M78 '+rows[key]+'H868" stroke="#d8e4e8"/><text x="10" y="'+(rows[key]+4)+'" fill="#416575" font-size="13">'+name+'</text>';});
      const G=v=>rows.g-27*v/maxG,Co=v=>rows.p-19*v;
      let gpath='',ppath='';sequence.segments.forEach((s,i)=>{gpath+=(i?'L':'M')+X(s.startSeconds)+' '+G(s.gradientMilliTeslaPerM)+'L'+X(s.endSeconds)+' '+G(s.gradientMilliTeslaPerM);ppath+=(i?'L':'M')+X(s.startSeconds)+' '+Co(s.coherence)+'L'+X(s.endSeconds)+' '+Co(s.coherence);});
      svg+='<path d="'+gpath+'" stroke="#286e9f" stroke-width="3" fill="none"/><path d="'+ppath+'" stroke="#d78065" stroke-width="3" fill="none"/>';
      sequence.rfEvents.forEach(event=>{const x=X(event.timeSeconds),angle=event.angleDegrees===undefined?event.suggestedAngleDegrees:event.angleDegrees;svg+='<path d="M'+x+' 46V24" stroke="#344d69" stroke-width="2"/><text x="'+Math.min(850,x+4)+'" y="19" fill="#344d69" font-size="11">'+angle+'°</text>';});
      if(state.revealed){const trace=P.trace(sequence,12);svg+='<path d="'+trace.map((p,i)=>(i?'L':'M')+X(p.timeSeconds)+' '+(rows.q-35*p.qRadPerM/maxQ)).join('')+'" stroke="#148d79" stroke-width="3" fill="none"/><path d="'+trace.map((p,i)=>(i?'L':'M')+X(p.timeSeconds)+' '+(rows.b-52*p.bSecondsPerM2/maxB)).join('')+'" stroke="#8c75b7" stroke-width="3" fill="none"/><text x="79" y="282" fill="#148d79" font-size="11">q '+T('escala','scale')+': '+f(maxQ/1e4)+' ×10⁴ rad/m</text><text x="79" y="348" fill="#8c75b7" font-size="11">b '+T('escala','scale')+': '+f(maxB/1e9)+' ×10⁹ s/m²</text>';}else{svg+='<text x="100" y="239" fill="#69818b" font-size="14">'+T('Predice las fronteras de q y revela el resultado.','Predict q at segment boundaries, then reveal the result.')+'</text><text x="100" y="325" fill="#69818b" font-size="13">'+T('b acumula q²; u acumula q con signo.','b accumulates q²; u accumulates signed q.')+'</text>';}
      for(let i=0;i<=4;i++){const t=sequence.totalSeconds*i/4;svg+='<text x="'+X(t)+'" y="387" text-anchor="middle" fill="#536d7a" font-size="12">'+f(t*1000)+' ms</text>';}
      if(current)svg+='<path d="M'+X(current.timeSeconds)+' 42V362" stroke="#183b50" stroke-dasharray="5 5"/>';
      el('sequence-chart').innerHTML=svg;
    }
    function renderComparison() {
      if(!comparison){el('comparison').replaceChildren();return;}
      el('comparison').innerHTML='<div class="dp-comparison-grid">'+comparison.map(c=>'<div class="dp-comparison-card"><strong>'+T(c.velocityMode==='none'?'Sin flujo':c.velocityMode==='uniform'?'Velocidad común':'Distribución uniforme',c.velocityMode==='none'?'No flow':c.velocityMode==='uniform'?'Common velocity':'Uniform distribution')+'</strong><div>Re E: '+f(c.real)+' · Im E: '+f(c.imag)+'</div><div>|E|: <b>'+f(c.magnitude)+'</b></div><small>'+T('Analítico','Analytic')+': '+f(c.analytic.real)+' + i '+f(c.analytic.imag)+'</small></div>').join('')+'</div><p class="dp-small">'+T('Misma semilla para posiciones y Browniano; la velocidad se genera con una corriente aleatoria independiente.','The same seed drives positions and Brownian motion; velocity uses an independent random stream.')+' '+(sequence.balanced?T('Eco balanceado: una velocidad común conserva el módulo analítico.','Balanced echo: a common velocity preserves analytic magnitude.'):T('q(T)≠0: interpreta también el perfil espacial inicial.','q(T)≠0: also account for the initial spatial profile.'))+'</p>';
    }
    function renderMetrics() {
      if(!sequence||!current){el('metrics').replaceChildren();return;}
      const a=current.analytic,s=sequence;
      const values=[['t / T',f(a.timeSeconds*1000)+' / '+f(s.totalSeconds*1000)+' ms'],
        ['p',String(a.coherence)],['q(t)',state.revealed?f(a.qRadPerM/1e4)+' ×10⁴ rad/m':T('Predice → revela','Predict → reveal')],
        ['b(T)',state.revealed?f(s.bSecondsPerM2/1e9)+' ×10⁹ s/m²':T('Integra q²','Integrate q²')],
        ['u(T)',state.revealed?f(s.uRadSecondsPerM)+' s/m':T('Integra q con signo','Integrate signed q')],
        [T('Eco final','Final echo'),s.balanced?T('q(T)=0 · balanceado','q(T)=0 · balanced'):T('q(T)≠0 · sin balance','q(T)≠0 · unbalanced')],
        [T('Transferencia RF ideal','Ideal RF transfer'),s.selectedPathwayAmplitude===null?T('No determinada sólo por p','Not determined by p alone'):f(s.selectedPathwayAmplitude)+' × S₀']];
      el('metrics').innerHTML=values.map(([key,value])=>'<div class="dp-metric"><span>'+key+'</span><strong>'+value+'</strong></div>').join('');
    }
    function render() {
      const warning=error==='stored-state-invalid'?T('Se descartó un estado guardado inválido; se ha cargado el preset seguro.','Invalid saved state was discarded; the safe preset was loaded.'):error;
      el('error').hidden=!warning;el('error').textContent=warning;
      el('time-label').textContent=current?f(current.timeSeconds*1000)+' ms / '+f(sequence.totalSeconds*1000)+' ms':'';
      el('time').value=Math.round(state.timeFraction*1000);el('play')&& (el('play').textContent=playing?'Ⅱ': '▶');
      const play=container.querySelector('[data-action="play"]');play.textContent=(playing?'Ⅱ ':'▶ ')+T(playing?'Pausar':'Reproducir',playing?'Pause':'Play');
      play.setAttribute('aria-pressed',String(playing));
      ['play','finish','compare','reveal','check-prediction'].forEach(action=>{container.querySelector('[data-action="'+action+'"]').disabled=!sequence;});
      if(current&&sequence){drawMolecules();drawPhase();drawVectors();drawEcho();}else{['molecules','phase','vectors','echo'].forEach(key=>canvas(key));['displacement','particle','storage','echo-note'].forEach(key=>{el(key).textContent='';});}
      renderMetrics();sequenceChart();renderComparison();
      if(state.assessment){el('prediction-feedback').textContent=state.assessment.correct+'/'+state.assessment.total+' '+T('fronteras correctas. ','correct boundaries. ')+(state.assessment.passed?T('Las áreas efectivas y los intervalos de almacenamiento son coherentes.','Effective areas and storage intervals are consistent.'):T('Revisa el signo p×g; q conserva su historia en p=0 o g=0.','Check the sign of p×g; q retains its history at p=0 or g=0.'));el('prediction-feedback').dataset.correct=String(state.assessment.passed);}
      container.dataset.physicsReady=sequence?'true':'false';
    }
    function updateEditor() {
      state.revealed=false;state.predictions=[];state.assessment=null;
      el('segments').innerHTML=segmentRows();el('predictions').innerHTML=predictionRows();el('preset').value=state.preset;
      el('prediction-feedback').textContent='';
      rebuild();render();
    }
    function seek(fraction) {
      if(!ensemble)return;
      playing=false;cancelAnimationFrame(raf);
      const target=Math.round(Math.max(0,Math.min(1,fraction))*FRAMES);
      current=ensemble.reset();frameIndex=0;playAccumulator=0;history=[{t:0,real:1,imag:0,magnitude:1}];
      advanceToFrame(target);render();
    }
    function tick(stamp) {
      if(!playing||destroyed||!ensemble)return;
      const dt=Math.min(.12,(stamp-lastStamp)/1000);lastStamp=stamp;
      playAccumulator+=dt;const steps=Math.floor(playAccumulator*FRAMES/12);playAccumulator-=steps*12/FRAMES;
      advanceToFrame(frameIndex+steps);
      if(frameIndex>=FRAMES){playing=false;notify('experiment-completed','observed-final-echo','completed',{real:current.real,imag:current.imag,magnitude:current.magnitude,standardErrorReal:current.standardErrorReal,standardErrorImag:current.standardErrorImag,analytic:current.analytic.real,balanced:sequence.balanced});}
      render();if(playing)raf=requestAnimationFrame(tick);
    }
    function simulationFields() {
      const number=key=>{const value=el(key).value;if(value==='')throw new RangeError(T('Completa todos los valores.','Complete every value.'));return Number(value);};
      state.sim={diffusionM2PerS:number('D')*1e-9,sampleLengthMeters:number('L')*1e-6,velocityMode:el('velocityMode').value,velocityMPerS:number('v')*1e-6,velocitySpreadMPerS:number('vmax')*1e-6};
      state.seed=number('seed');state.count=number('count');state.selectedParticle=Math.min(state.selectedParticle,state.count-1);
    }
    function change(event) {
      const node=event.target;
      try {
        if(node.matches('[data-prediction]')){state.predictions[Number(node.dataset.prediction)]=node.value;return;}
        if(node.dataset.field){const i=Number(node.closest('[data-row]').dataset.row);if(node.value==='')throw new RangeError(T('El intervalo necesita un valor numérico.','The interval needs a numeric value.'));state.segments[i][node.dataset.field]=Number(node.value);state.preset='custom';state.revealed=false;state.timeFraction=0;state.predictions=[];state.assessment=null;rebuild();el('preset').value='custom';el('predictions').innerHTML=predictionRows();el('prediction-feedback').textContent='';render();return;}
        if(node===el('preset')){if(node.value==='custom'){state.preset='custom';return;}state.preset=node.value;state.segments=P.preset(state.preset).segments.map(s=>({...s}));updateEditor();return;}
        if(node===el('time')){seek(Number(node.value)/1000);return;}
        if(node===el('selected')){state.selectedParticle=Math.max(0,Math.min(state.count-1,Math.floor(Number(node.value)||0)));render();return;}
        if(node.closest('.dp-controls')){simulationFields();state.timeFraction=0;rebuild();render();}
      }catch(e){error=e.message;render();}
    }
    function click(event) {
      const button=event.target.closest('[data-action]');if(!button||!container.contains(button))return;
      const action=button.dataset.action;
      try {
        error='';
        if(action==='play') {if(!ensemble)return;if(playing){playing=false;cancelAnimationFrame(raf);render();return;}if(current.timeSeconds>=sequence.totalSeconds)seek(0);playing=true;lastStamp=performance.now();render();raf=requestAnimationFrame(tick);return;}
        if(action==='reset'){seek(0);notify('experiment-reset','same-seed','reset',{});return;}
        if(action==='finish'){seek(1);notify('experiment-completed','observed-final-echo','completed',{real:current.real,imag:current.imag,magnitude:current.magnitude,balanced:sequence.balanced});return;}
        if(action==='restore'){state.preset=state.preset==='custom'?'pgse':state.preset;state.segments=P.preset(state.preset).segments.map(s=>({...s}));updateEditor();return;}
        if(action==='row-add'){if(state.segments.length>=64)throw new RangeError(T('Máximo 64 intervalos.','Maximum 64 intervals.'));state.segments.push({durationMs:10,gradientMilliTeslaPerM:0,coherence:0,label:'Custom'});state.preset='custom';updateEditor();return;}
        if(action.startsWith('row-')){const i=Number(button.dataset.index);if(action==='row-remove'&&state.segments.length>1)state.segments.splice(i,1);if(action==='row-up'&&i>0)[state.segments[i],state.segments[i-1]]=[state.segments[i-1],state.segments[i]];if(action==='row-down'&&i<state.segments.length-1)[state.segments[i],state.segments[i+1]]=[state.segments[i+1],state.segments[i]];state.preset='custom';updateEditor();return;}
        if(action==='mistake'){state.preset='custom';state.segments=state.segments.map(s=>({...s,coherence:s.coherence===-1?1:s.coherence}));updateEditor();el('prediction-feedback').textContent=T('Reto activo: p=−1 se ha sustituido por p=+1. Diagnostica el cierre y corrige los intervalos.','Challenge active: p=−1 was replaced by p=+1. Diagnose closure and correct the intervals.');notify('sequence-challenge','remove-inversion','started',{intentionalMutation:'minus-one-to-plus-one'});return;}
        if(action==='hide'){state.revealed=false;assessment=null;state.assessment=null;el('prediction-feedback').textContent='';render();return;}
        if(action==='check-prediction') {
          const fields=[...container.querySelectorAll('[data-prediction]')];if(fields.some(n=>n.value===''))throw new RangeError(T('Predice q al final de todos los intervalos.','Predict q at the end of every interval.'));
          state.predictions=fields.map(n=>n.value);assessment=P.assessPrediction(sequence,state.predictions.map(n=>Number(n)*1e4));state.assessment=assessment;state.revealed=true;
          const failed=assessment.checks.find(c=>!c.passed);
          let hint='';if(failed){hint=failed.hint==='storage-keeps-q'?T('Al almacenar (p=0), q conserva el valor anterior; b sigue creciendo.','During storage (p=0), q retains its previous value; b keeps growing.'):failed.hint==='gradient-off-keeps-q'?T('Si g=0, q es constante; no lo reinicies.','If g=0, q is constant; do not reset it.'):T('Revisa el signo de p×g y convierte ms/mT a s/T.','Check the sign of p×g and convert ms/mT to s/T.');}
          el('prediction-feedback').textContent=assessment.correct+'/'+assessment.total+' '+T('fronteras correctas. ','correct boundaries. ')+hint;
          el('prediction-feedback').dataset.correct=String(assessment.passed);notify('q-prediction',state.predictions.map(Number),assessment.passed?'passed':'needs-review',{checks:assessment.checks});render();return;
        }
        if(action==='reveal'){state.revealed=true;el('prediction-feedback').textContent=T('q integra áreas efectivas con signo. En g=0 o p=0 queda constante; b integra su cuadrado positivo. Consulta las escalas del diagrama.','q integrates signed effective areas. At g=0 or p=0 it remains constant; b integrates its nonnegative square. Check the diagram scales.');notify('q-reveal','requested-explanation','reviewed',{balanced:sequence.balanced,b:sequence.bSecondsPerM2,u:sequence.uRadSecondsPerM});render();return;}
        if(action==='compare'){comparison=['none','uniform','distribution'].map(velocityMode=>{const e=P.createEnsemble(sequence,{...state.sim,velocityMode,count:state.count,seed:state.seed});let final;for(let i=1;i<=FRAMES;i++)final=e.advance(sequence.totalSeconds*i/FRAMES);return {velocityMode,...final,particles:undefined};});state.comparison=comparison.map(c=>({velocityMode:c.velocityMode,real:c.real,imag:c.imag,magnitude:c.magnitude}));notify('flow-comparison','complex-signal-retained','completed',{comparison:state.comparison});renderComparison();return;}
      }catch(e){error=e.message;render();}
    }
    function snapshot() {
      return {version:'1.2.0',evidenceStatus:'synthetic-teaching-simulation',view:state.view,language:lang,preset:state.preset,
        segments:state.segments.map(s=>({...s})),sim:{...state.sim},seed:state.seed,count:state.count,selectedParticle:state.selectedParticle,
        timeFraction:state.timeFraction,revealed:state.revealed,predictions:state.predictions.slice(),assessment:state.assessment,comparison:state.comparison,
        sequence:sequence?{balanced:sequence.balanced,qFinalRadPerM:sequence.qFinalRadPerM,bSecondsPerM2:sequence.bSecondsPerM2,uRadSecondsPerM:sequence.uRadSecondsPerM,totalSeconds:sequence.totalSeconds}:null,
        ensemble:current?{real:current.real,imag:current.imag,magnitude:current.magnitude,standardErrorReal:current.standardErrorReal,standardErrorImag:current.standardErrorImag,timeSeconds:current.timeSeconds}:null};
    }
    function setLanguage(value) {if(destroyed)return;lang=value==='en'?'en':'es';playing=false;cancelAnimationFrame(raf);markup();render();}
    function destroy(){destroyed=true;playing=false;cancelAnimationFrame(raf);container.removeEventListener('click',click);container.removeEventListener('change',change);container.removeEventListener('input',rangeInput);container.removeAttribute('data-physics-ready');container.replaceChildren();}
    function rangeInput(event){if(event.target===el('time'))change(event);}
    rebuild(true);
    if(sequence&&start.assessment&&state.predictions.length===sequence.segments.length&&state.predictions.every(n=>n!==''&&Number.isFinite(Number(n)))){assessment=P.assessPrediction(sequence,state.predictions.map(n=>Number(n)*1e4));state.assessment=assessment;}
    markup();render();container.addEventListener('click',click);container.addEventListener('change',change);container.addEventListener('input',rangeInput);
    return {snapshot,destroy,setLanguage};
  }
  return Object.freeze({version:'1.2.0',mount});
});
