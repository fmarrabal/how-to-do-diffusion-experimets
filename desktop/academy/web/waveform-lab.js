/* Independently checked teaching model: finite rectangular, sine, sine-squared
   and triangular PGSE pulses. SI internally; no instrument operation. */
(function(root,factory){'use strict';const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.AcademyWaveformLab=api;})(typeof window!=='undefined'?window:globalThis,function(){
  'use strict';
  const gamma=267.52218744e6;
  const profiles={
    rect:{sigma:1,correction:1/3,f:u=>1,F:u=>u},
    sine:{sigma:2/Math.PI,correction:1/4,f:u=>Math.sin(Math.PI*u),F:u=>(1-Math.cos(Math.PI*u))/Math.PI},
    sine2:{sigma:.5,correction:1/3-5/(4*Math.PI*Math.PI),f:u=>Math.sin(Math.PI*u)**2,F:u=>u/2-Math.sin(2*Math.PI*u)/(4*Math.PI)},
    triangle:{sigma:.5,correction:7/30,f:u=>u<=.5?2*u:2*(1-u),F:u=>u<=.5?u*u:.5-(1-u)**2}
  };
  function finite(v,name,min,max){if(typeof v!=='number'||!Number.isFinite(v)||v<min||v>max)throw new RangeError(name+' is outside its teaching range.');return v;}
  function sinc(x){return Math.abs(x)<1e-5?1-x*x/6+x**4/120:Math.sin(x)/x;}
  function calculate(input={}){
    const p={shape:'rect',gradientTPerM:.3,deltaSeconds:.002,bigDeltaSeconds:.08,diffusionM2PerS:1e-9,vMaxMPerS:0,...input};
    const profile=profiles[p.shape];if(!profile)throw new RangeError('Unknown pulse shape.');
    finite(p.gradientTPerM,'g',0,1);finite(p.deltaSeconds,'delta',1e-5,.02);
    finite(p.bigDeltaSeconds,'Delta',p.deltaSeconds,2);finite(p.diffusionM2PerS,'D',1e-13,1e-8);finite(p.vMaxMPerS,'maximum velocity',0,.01);
    const {gradientTPerM:g,deltaSeconds:d,bigDeltaSeconds:Delta,diffusionM2PerS:D,vMaxMPerS:v}=p;
    const T=Delta+d,rf=T/2,Q=gamma*g*d*profile.sigma,b=Q*Q*(Delta-profile.correction*d),M1=Q*Delta;
    function waveform(t){
      const first=t>=0&&t<d,second=t>=Delta&&t<T;
      const physical=first?g*profile.f(t/d):second?g*profile.f((t-Delta)/d):0;
      const order=t<rf?1:-1;
      const q=first?gamma*g*d*profile.F(t/d):t<Delta?Q:t<T?gamma*g*d*(profile.sigma-profile.F((t-Delta)/d)):0;
      return {t,physical,effective:order*physical,q};
    }
    const trace=[];
    for(let i=0;i<=80;i++)trace.push(waveform(d*i/80));
    for(let i=1;i<25;i++)trace.push(waveform(d+(Delta-d)*i/25));
    for(let i=0;i<=80;i++)trace.push(waveform(Delta+d*i/80));
    // Independent Simpson integration within each pulse, plus the exact plateau.
    // The closed-form correction above is never used by this quadrature.
    const n=1024;let pulseIntegral=0;
    for(let i=0;i<=n;i++){
      const a=gamma*g*d*profile.F(i/n),c=gamma*g*d*(profile.sigma-profile.F(i/n));
      pulseIntegral+=(a*a+c*c)*(i===0||i===n?1:i%2?4:2);
    }
    const quadratureB=pulseIntegral*d/(3*n)+Q*Q*(Delta-d);
    const attenuation=[];
    for(let i=0;i<=120;i++){
      const scale=i/120,bI=b*scale*scale,mI=M1*scale;
      attenuation.push({gradient:g*scale,diffusion:Math.exp(-D*bI),signedEcho:Math.exp(-D*bI)*sinc(v*mI)});
    }
    const E=Math.exp(-D*b),EFlow=E*sinc(v*M1);
    return {evidenceStatus:'synthetic-teaching-simulation',parameters:p,gammaRadPerSecondPerTesla:gamma,
      sigma:profile.sigma,finitePulseCorrection:profile.correction,bSecondsPerM2:b,
      quadratureBSecondsPerM2:quadratureB,qFinalRadPerM:0,qPlateauRadPerM:Q,
      firstMomentRadSecondsPerM:M1,phaseVarianceRad2:2*D*b,freeDisplacementStdMicrometers:Math.sqrt(2*D*Delta)*1e6,
      diffusionEcho:E,signedEchoWithUniformVelocity:EFlow,uniformVelocityArgument:v*M1,
      effectiveDiffusionSeconds:Delta-profile.correction*d,
      nominalRectangularFitBiasRatio:g===0?null:b/(gamma*gamma*g*g*d*d*(Delta-d/3)),
      rf180Seconds:rf,trace,attenuation,
      assumptions:['Free Gaussian diffusion; constant D; instantaneous RF; identical encoding and decoding shapes.',
        'Delta is the interval between leading edges; delta is the entire single PGSE gradient duration.',
        'Convection example is a uniform velocity distribution in [-vMax,+vMax], constant within each trajectory; signed real signal retained.',
        'No relaxation, restriction, exchange, gradient nonuniformity or eddy-current response.']};
  }
  let current=null,mountCount=0;
  function mount(container,language='es'){
    if(!container||typeof document==='undefined')return;
    const en=language==='en',T=(es,eng)=>en?eng:es,id='aw-'+(++mountCount);
    const style=document.getElementById('academy-waveform-style');
    if(!style){const sheet=document.createElement('style');sheet.id='academy-waveform-style';sheet.textContent='.aw-lab{padding:24px;background:#eaf5f5;border:1px solid #cadfe0;border-radius:14px;margin:24px 0}.aw-lab h3{font-size:24px;margin:0 0 10px}.aw-controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin:18px 0}.aw-controls label{display:flex;flex-direction:column;gap:6px;font-size:13px}.aw-controls input,.aw-controls select{width:100%;padding:10px;border:1px solid #b7cbce;border-radius:6px;background:white;box-sizing:border-box}.aw-metrics{display:flex;flex-wrap:wrap;gap:12px}.aw-metric{padding:12px;background:white;flex:1;min-width:150px;border-radius:8px}.aw-metric strong{display:block;font-size:19px;color:#096967}.aw-charts{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:16px}.aw-charts figure{margin:18px 0 0;background:white;padding:12px;border-radius:8px}.aw-charts svg{width:100%;height:210px}.aw-lab p,.aw-lab li{line-height:1.6}.aw-equation{background:#102d39;color:white;border-radius:8px;padding:15px;font-family:monospace;overflow:auto;white-space:pre-wrap}.aw-error{color:#9e3128}.aw-lab small{line-height:1.6}';document.head.append(sheet);}
    container.innerHTML='<section class="aw-lab"><p class="eyebrow">'+T('DE LA ECUACIÓN DIFERENCIAL AL ECO','FROM THE DIFFERENTIAL EQUATION TO THE ECHO')+'</p><h3>'+T('La misma altura de gradiente no significa el mismo b','The same gradient height does not mean the same b')+'</h3><p>'+T('Cambia la forma del pulso. Observa primero el gradiente efectivo, después su integral q(t) y finalmente la atenuación. La selección RF cambia el signo efectivo aunque los dos gradientes físicos tengan el mismo signo.','Change the pulse shape. Observe the effective gradient, then its integral q(t), then attenuation. RF selection changes the effective sign even when the two physical gradients have the same sign.')+'</p><div class="aw-controls">'+
      '<label>'+T('Forma del gradiente','Gradient shape')+'<select data-aw="shape"><option value="rect">'+T('Rectangular','Rectangle')+'</option><option value="sine">'+T('Seno','Sine')+'</option><option value="sine2">'+T('Seno al cuadrado','Sine squared')+'</option><option value="triangle">'+T('Triangular','Triangle')+'</option></select></label>'+
      '<label>g (T/m)<input data-aw="g" type="number" min="0" max="1" step="0.01" value="0.30"></label>'+
      '<label>δ (ms)<input data-aw="delta" type="number" min="0.01" max="20" step="0.1" value="2"></label>'+
      '<label>Δ (ms)<input data-aw="Delta" type="number" min="0.01" max="2000" step="1" value="80"></label>'+
      '<label>D (10⁻⁹ m²/s)<input data-aw="D" type="number" min="0.0001" max="10" step="0.1" value="1"></label>'+
      '<label>'+T('Velocidad máxima (mm/s)','Maximum velocity (mm/s)')+'<input data-aw="v" type="number" min="0" max="10" step="0.05" value="0"></label></div><div data-aw="error" class="aw-error" role="alert"></div><div data-aw="metrics" class="aw-metrics"></div><div class="aw-charts"><figure><svg data-aw="wave" viewBox="0 0 480 210" role="img"></svg><figcaption>'+T('Azul: gradiente físico; coral: gradiente efectivo; verde: q(t) normalizado. El pulso RF de 180° está en la línea vertical.','Blue: physical gradient; coral: effective gradient; green: normalized q(t). The 180° RF pulse is at the vertical line.')+'</figcaption></figure><figure><svg data-aw="echo" viewBox="0 0 480 210" role="img"></svg><figcaption>'+T('Verde: difusión sola; coral: difusión más distribución uniforme de velocidades. Una señal negativa se conserva: no debe ocultarse tomando su valor absoluto.','Green: diffusion alone; coral: diffusion plus a uniform velocity distribution. Negative signal is retained; taking its absolute value hides relevant information.')+'</figcaption></figure></div><p class="aw-equation">∂M/∂t = D ∂²M/∂z² − i γ g_eff(t) z M\nq(t) = γ ∫₀ᵗ g_eff(s) ds ; b = ∫₀ᵀ q(t)² dt\nM(z,T)/M₀ = exp(−Db) · exp(−i q(T) z)\nE_diff = exp(−Db) ; E_flow = E_diff · sinc(v_max ∫₀ᵀ q(t)dt)</p><p>'+T('Objetivo: comprobar el cierre q(T)=0 antes de usar E=exp(−Db), entender de dónde viene q² y distinguir pérdida de señal por difusión de pérdida por convección. σ es el área normalizada de la forma del gradiente; no sustituye al cálculo temporal completo.','Objective: check q(T)=0 before using E=exp(−Db), understand the origin of q², and distinguish diffusion loss from convection loss. σ is the normalized gradient area; it does not replace the complete time calculation.')+'</p><small>'+T('Modelo sintético de PGSE libre: pulsos RF instantáneos, dos gradientes idénticos, Δ entre comienzos, sin relajación ni corrientes parásitas. No usar la δ de este ejemplo como p30 bipolar sin comprobar la secuencia. Fuentes: Kuchel et al., DOI 10.1002/cmr.a.21241; Sinnaeve, DOI 10.1002/cmr.a.21223.','Synthetic free-PGSE model: instantaneous RF, two identical gradient shapes, leading-edge Δ, no relaxation or eddy-current response. Do not substitute this δ for a bipolar p30 without checking the pulse sequence. Sources: Kuchel et al., DOI 10.1002/cmr.a.21241; Sinnaeve, DOI 10.1002/cmr.a.21223.')+'</small></section>';
    const field=n=>container.querySelector('[data-aw="'+n+'"]');
    function draw(svg,curves,xmax,ymin,ymax,xlabel){
      const X=x=>44+420*x/xmax,Y=y=>177-150*(y-ymin)/(ymax-ymin);
      svg.innerHTML='<path d="M44 20V177H464" fill="none" stroke="#7b9298"/><path d="M44 '+Y(0)+'H464" stroke="#d7e2e4"/><text x="44" y="197" fill="#405965" font-size="12">0</text><text x="380" y="197" fill="#405965" font-size="12">'+xmax.toPrecision(3)+' '+xlabel+'</text>'+curves.map(c=>'<path d="'+c.values.map((p,i)=>(i?'L':'M')+X(p[0]).toFixed(2)+' '+Y(p[1]).toFixed(2)).join(' ')+'" stroke="'+c.color+'" stroke-width="2.5" fill="none"/>').join('');
    }
    function refresh(){
      try{
        current=calculate({shape:field('shape').value,gradientTPerM:Number(field('g').value),deltaSeconds:Number(field('delta').value)/1000,bigDeltaSeconds:Number(field('Delta').value)/1000,diffusionM2PerS:Number(field('D').value)*1e-9,vMaxMPerS:Number(field('v').value)/1000});
        field('error').textContent='';const c=current,fmt=n=>n.toLocaleString(en?'en-US':'es-ES',{maximumSignificantDigits:4});
        field('metrics').innerHTML=[['b (s/m²)',c.bSecondsPerM2.toExponential(4)],['σ',fmt(c.sigma)],['E_diff',fmt(c.diffusionEcho)],['E_diff+flow',fmt(c.signedEchoWithUniformVelocity)],[T('Cierre q(T)','Closure q(T)'),c.qFinalRadPerM+' rad/m'],['Var(φ) (rad²)',fmt(c.phaseVarianceRad2)]].map(([label,value])=>'<div class="aw-metric">'+label+'<strong>'+value+'</strong></div>').join('');
        draw(field('wave'),[{color:'#246ab0',values:c.trace.map(t=>[t.t*1000,t.physical/(c.parameters.gradientTPerM||1)])},{color:'#dc775d',values:c.trace.map(t=>[t.t*1000,t.effective/(c.parameters.gradientTPerM||1)])},{color:'#0b8078',values:c.trace.map(t=>[t.t*1000,t.q/(c.qPlateauRadPerM||1)])}],(c.parameters.bigDeltaSeconds+c.parameters.deltaSeconds)*1000,-1.1,1.2,'ms');
        const rfX=44+420*c.rf180Seconds/(c.parameters.bigDeltaSeconds+c.parameters.deltaSeconds);field('wave').innerHTML+='<path d="M'+rfX+' 20V177" stroke="#687987" stroke-dasharray="4 4"/><text x="'+Math.min(rfX+5,425)+'" y="32" fill="#405965" font-size="11">180°</text>';
        draw(field('echo'),[{color:'#0b8078',values:c.attenuation.map(a=>[a.gradient,a.diffusion])},{color:'#dc775d',values:c.attenuation.map(a=>[a.gradient,a.signedEcho])}],c.parameters.gradientTPerM||1,-.25,1.05,'T/m');
        container.dataset.awReady='true';
      }catch(error){current=null;container.dataset.awReady='false';field('error').textContent=T('Revisa los parámetros: Δ debe ser mayor o igual que δ.','Check the parameters: Δ must be greater than or equal to δ.')+' '+error.message;field('metrics').replaceChildren();field('wave').replaceChildren();field('echo').replaceChildren();}
    }
    container.querySelectorAll('input,select').forEach(control=>control.addEventListener('input',refresh));refresh();
    return {refresh,id};
  }
  return {calculate,mount,snapshot:()=>current,gammaRadPerSecondPerTesla:gamma};
});
