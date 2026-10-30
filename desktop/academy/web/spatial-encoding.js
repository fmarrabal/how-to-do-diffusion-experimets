/* Academy 1.3: computed 1-D spatial Bloch / Bloch-Torrey teaching laboratory.
 * A pulse/gradient forward model, not a compiler or a qualified UF-DOSY sequence.
 * SI internally. M+=Mx+iMy; positive offset gives exp(+i omega t).
 * Reflecting finite-volume cells; positivity-preserving subdivided Crank-Nicolson
 * diffusion, exact relaxation and midpoint Rodrigues rotation (Strang splitting).
 */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.AcademySpatialEncoding = api;
})(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';
  const VERSION = '1.3.0', GAMMA = 267.52218744e6, TAU = 2 * Math.PI;
  const sources = Object.freeze([
    {id:'torrey1956', title:'H. C. Torrey, Bloch Equations with Diffusion Terms (1956)', doi:'10.1103/PhysRev.104.563', url:'https://journals.aps.org/pr/abstract/10.1103/PhysRev.104.563'},
    {id:'shrot2004', title:'Y. Shrot, B. Shapira and L. Frydman, Continuous spatial encoding (2004)', doi:'10.1016/j.jmr.2004.08.001', url:'https://pubmed.ncbi.nlm.nih.gov/15504696/'}
  ]);
  const assumptions = Object.freeze({
    es:[
      'Simulación calculada en una dimensión espacial, con difusión escalar uniforme y paredes reflectantes; no incluye convección, intercambio, acoplamientos ni calentamiento.',
      'La fase RF se integra desde la frecuencia barrida. La integral física del gradiente se muestra por separado: durante RF no es una vía de coherencia seleccionada ni un valor b de DOSY.',
      'El protocolo predeterminado es un chirp, evolución y lectura con gradiente. Ilustra ingredientes de codificación espacial; no reproduce ni valida una secuencia ultrafast/SPEN-DOSY concreta.',
      'La lectura es una suma compleja ponderada por la bobina y su espectro DFT. La coordenada f/(gammaHz G) es nominal; requiere un gradiente de lectura constante, resolución y muestreo suficientes. Un offset Deltaf produce un desplazamiento aparente Deltaz=Deltaf/(gammaHz G): no es desplazamiento molecular.',
      'Se conserva el modelo sencillo de Academy como introducción. La convergencia temporal/espacial de este modelo debe revisarse por separado; no acredita calibración instrumental.'
    ],
    en:[
      'Computed one-spatial-dimension simulation with uniform scalar diffusion and reflecting walls; no convection, exchange, couplings or heating.',
      'RF phase is integrated from swept frequency. The physical gradient integral is separate: during RF it is not a selected coherence pathway or a DOSY b value.',
      'The default protocol is a chirp, evolution and gradient readout. It illustrates spatial-encoding ingredients; it does not reproduce or qualify a particular ultrafast/SPEN-DOSY sequence.',
      'Readout is a coil-weighted complex sum and its DFT. The f/(gammaHz G) coordinate is nominal and requires constant readout gradient, adequate resolution and sampling. An offset Deltaf causes apparent position shift Deltaz=Deltaf/(gammaHz G): not molecular displacement.',
      'The simple Academy model remains the introduction. Time/space convergence of this model must be checked separately; it does not establish instrument calibration.'
    ]
  });
  function finite(v, name, lo, hi) {
    if (typeof v !== 'number' || !Number.isFinite(v) || v < lo || v > hi)
      throw new RangeError(name + ' must be finite in [' + lo + ', ' + hi + '].');
    return v;
  }
  function integer(v, name, lo, hi) { finite(v,name,lo,hi); if(!Number.isInteger(v)) throw new RangeError(name+' must be an integer.'); return v; }
  function defaults() { return {
    points:128, lengthMm:12, rfDurationMs:4, rfAmplitudeHz:125,
    chirpBandwidthHz:5000, chirpCenterHz:0, rfPhaseDegrees:0,
    encodingGradientTm:0.012, offResonanceHz:0, diffusionM2s:8e-10,
    evolutionMs:15, evolutionGradientTm:0, readoutGradientTm:0.02,
    readoutMs:2, readoutPoints:64, T1Seconds:1.2, T2Seconds:0.15,
    coilVariation:0.2, timeStepUs:20, boundary:'reflecting', relaxation:true
  }; }
  function options(input) {
    if(input===null || typeof input!=='object' || Array.isArray(input)) throw new TypeError('Options must be an object.');
    const p={...defaults(),...input};
    integer(p.points,'points',8,256); finite(p.lengthMm,'length mm',0.02,100);
    finite(p.rfDurationMs,'RF duration ms',0,100); finite(p.rfAmplitudeHz,'RF amplitude Hz',0,20000);
    finite(p.chirpBandwidthHz,'chirp bandwidth Hz',-100000,100000); finite(p.chirpCenterHz,'chirp centre Hz',-100000,100000);
    finite(p.rfPhaseDegrees,'RF phase degrees',-360000,360000); finite(p.encodingGradientTm,'encoding gradient T/m',-1,1);
    finite(p.offResonanceHz,'offset Hz',-100000,100000); finite(p.diffusionM2s,'D m2/s',0,1e-7);
    finite(p.evolutionMs,'evolution ms',0,200); finite(p.evolutionGradientTm,'evolution gradient T/m',-1,1);
    finite(p.readoutGradientTm,'readout gradient T/m',-1,1); finite(p.readoutMs,'readout ms',0,100);
    integer(p.readoutPoints,'readout samples',8,256); finite(p.T1Seconds,'T1 s',0.001,1000000000);
    finite(p.T2Seconds,'T2 s',0.0001,1000000000); finite(p.coilVariation,'coil variation',0,0.95);
    finite(p.timeStepUs,'time step us',0.1,500);
    if(p.boundary!=='reflecting') throw new RangeError('Only reflecting finite-volume boundaries are implemented.');
    if(typeof p.relaxation!=='boolean') throw new TypeError('relaxation must be boolean.');
    return p;
  }
  function grid(p) {
    const length=p.lengthMm/1000,dz=length/p.points;
    return {length,dz,z:Float64Array.from({length:p.points},(_,i)=>(i+.5)*dz-length/2)};
  }
  function initialState(p,initial) {
    const n=p.points, state={mx:new Float64Array(n),my:new Float64Array(n),mz:new Float64Array(n)};
    if(initial===undefined) initial=[0,0,1];
    if(Array.isArray(initial) && initial.length===3 && initial.every(x=>typeof x==='number')) {
      for(let k=0;k<3;k++) { finite(initial[k],'initial magnetization',-1,1); state[['mx','my','mz'][k]].fill(initial[k]); }
    } else if(initial && typeof initial==='object' && ['mx','my','mz'].every(k=>Array.isArray(initial[k])||ArrayBuffer.isView(initial[k]))) {
      for(const key of ['mx','my','mz']) {
        if(initial[key].length!==n) throw new RangeError('Initial magnetization length differs from points.');
        for(let i=0;i<n;i++) state[key][i]=finite(initial[key][i],'initial '+key,-1,1);
      }
    } else throw new TypeError('Initial magnetization must be a three-vector or three arrays.');
    for(let i=0;i<n;i++) if(Math.hypot(state.mx[i],state.my[i],state.mz[i])>1+1e-10) throw new RangeError('Initial magnetization exceeds the unit Bloch ball.');
    return state;
  }
  function makeDiffuser(n,dz,D) {
    const rhs=new Float64Array(n),upper=new Float64Array(n),diag=new Float64Array(n),out=new Float64Array(n);
    let subdivisions=0,maxAlpha=0;
    function apply(array,time) {
      if(D===0 || time===0) return;
      const alpha=D*time/(dz*dz),steps=Math.max(1,Math.ceil(alpha)),a=alpha/steps;
      if(steps>4096) throw new RangeError('Diffusion grid/time combination exceeds the interactive solver budget.');
      subdivisions+=steps;maxAlpha=Math.max(maxAlpha,a);
      // Each CN RHS is nonnegative for a<=1; its M-matrix inverse is nonnegative.
      // Symmetric reflecting cell-face fluxes preserve total magnetization.
      for(let step=0;step<steps;step++) {
        for(let i=0;i<n;i++) {
          const neighbours=(i>0?1:0)+(i+1<n?1:0);
          rhs[i]=(1-a*neighbours/2)*array[i]+(i>0?a*array[i-1]/2:0)+(i+1<n?a*array[i+1]/2:0);
          diag[i]=1+a*neighbours/2;upper[i]=i+1<n?-a/2:0;
        }
        for(let i=1;i<n;i++) { const w=(-a/2)/diag[i-1];diag[i]-=w*upper[i-1];rhs[i]-=w*rhs[i-1]; }
        out[n-1]=rhs[n-1]/diag[n-1];
        for(let i=n-2;i>=0;i--) out[i]=(rhs[i]-upper[i]*out[i+1])/diag[i];
        array.set(out);
      }
    }
    return {apply,stats:()=>({diffusionSubsteps:subdivisions,maxDiffusionAlpha:maxAlpha})};
  }
  function relax(state,time,p) {
    if(!p.relaxation || time===0)return;
    const e1=Math.exp(-time/p.T1Seconds),e2=Math.exp(-time/p.T2Seconds);
    for(let i=0;i<state.mx.length;i++) {state.mx[i]*=e2;state.my[i]*=e2;state.mz[i]=1+(state.mz[i]-1)*e1;}
  }
  function rotate(state,z,dt,rfHz,phase,gradient,offset) {
    const wx=TAU*rfHz*Math.cos(phase),wy=TAU*rfHz*Math.sin(phase);
    for(let i=0;i<z.length;i++) {
      const wz=GAMMA*gradient*z[i]+TAU*offset,w=Math.hypot(wx,wy,wz);
      if(w===0)continue;
      const ax=wx/w,ay=wy/w,az=wz/w,c=Math.cos(w*dt),s=Math.sin(w*dt),v=1-c;
      const x=state.mx[i],y=state.my[i],zz=state.mz[i],dot=ax*x+ay*y+az*zz;
      state.mx[i]=x*c+(ay*zz-az*y)*s+ax*dot*v;
      state.my[i]=y*c+(az*x-ax*zz)*s+ay*dot*v;
      state.mz[i]=zz*c+(ax*y-ay*x)*s+az*dot*v;
    }
  }
  function cloneState(s) {return {mx:Array.from(s.mx),my:Array.from(s.my),mz:Array.from(s.mz)};}
  function spectrum(re,im,dt,gradient) {
    const n=re.length,real=[],imag=[],magnitude=[],frequencyHz=[],positionMm=[];
    for(let bin=0;bin<n;bin++) {
      const k=bin-Math.floor(n/2);let x=0,y=0;
      for(let j=0;j<n;j++){const a=-TAU*k*j/n,c=Math.cos(a),s=Math.sin(a);x+=re[j]*c-im[j]*s;y+=re[j]*s+im[j]*c;}
      x/=n;y/=n;real.push(x);imag.push(y);magnitude.push(Math.hypot(x,y));
      const f=dt>0?k/(n*dt):0;frequencyHz.push(f);positionMm.push(dt>0&&gradient!==0?1000*f/(GAMMA/TAU*gradient):null);
    }
    return {real,imag,magnitude,frequencyHz,positionMm};
  }
  function segment(input) {
    if(!input || typeof input!=='object')throw new TypeError('A program segment must be an object.');
    const s={kind:'evolve',durationMs:0,gradientTm:0,rfAmplitudeHz:0,rfPhaseDegrees:0,chirpBandwidthHz:0,chirpCenterHz:0,...input};
    if(!['rf','evolve','readout'].includes(s.kind))throw new RangeError('Unknown program segment kind.');
    finite(s.durationMs,'segment duration ms',0,200);finite(s.gradientTm,'segment gradient T/m',-1,1);
    finite(s.rfAmplitudeHz,'segment RF Hz',0,20000);finite(s.rfPhaseDegrees,'segment phase',-360000,360000);
    finite(s.chirpBandwidthHz,'segment sweep Hz',-100000,100000);finite(s.chirpCenterHz,'segment centre Hz',-100000,100000);
    if(s.kind!=='rf' && (s.rfAmplitudeHz!==0 || s.chirpBandwidthHz!==0))throw new RangeError('RF must be in an explicit RF segment.');
    if(s.kind==='readout')s.samples=integer(s.samples??64,'segment samples',8,256);
    return s;
  }
  function run(p,program,initial) {
    if(!Array.isArray(program)||program.length<1||program.length>12)throw new RangeError('One to twelve explicit segments are required.');
    program=program.map(segment);
    if(program.reduce((a,s)=>a+s.durationMs,0)>400)throw new RangeError('The total simulation duration exceeds 400 ms.');
    const geometry=grid(p),state=initialState(p,initial),heat=makeDiffuser(p.points,geometry.dz,p.diffusionM2s),dtMax=p.timeStepUs*1e-6;
    const activeRf=program.filter(s=>s.kind==='rf'&&s.rfAmplitudeHz>0&&s.durationMs>0);
    const appliedEncodingSpan=Math.max(0,...activeRf.map(s=>Math.abs(GAMMA/TAU*s.gradientTm*geometry.length)));
    const appliedSweepBandwidth=Math.max(0,...activeRf.map(s=>Math.abs(s.chirpBandwidthHz)));
    const maxWork=program.reduce((a,s)=>a+Math.ceil(s.durationMs/1000/dtMax)+(s.samples||0),0)*p.points;
    const diffusionWorkFactor=1+6*Math.max(1,Math.ceil(p.diffusionM2s*dtMax/(2*geometry.dz**2)));
    if(maxWork>3000000 || maxWork*diffusionWorkFactor>30000000)throw new RangeError('Choose a coarser grid/time step for an interactive simulation.');
    let t=0,gIntegral=0,bIntegral=0,steps=0,rfPhaseMaxStep=0;
    const waveform={timeMs:[0],gradientTm:[0],rfAmplitudeHz:[0],rfFrequencyHz:[0],rfPhaseRad:[0],gradientIntegralRadPerM:[0]},snapshots=[],readouts=[];
    const coil=Float64Array.from(geometry.z,z=>Math.max(0,1-p.coilVariation*(2*z/geometry.length)**2));
    function step(dt,s,localMid) {
      for(const k of ['mx','my','mz'])heat.apply(state[k],dt/2);relax(state,dt/2,p);
      const duration=s.durationMs/1000,start=s.chirpCenterHz-s.chirpBandwidthHz/2,rate=duration>0?s.chirpBandwidthHz/duration:0;
      const phase=s.rfPhaseDegrees*Math.PI/180+TAU*(start*localMid+rate*localMid*localMid/2);
      const freq=start+rate*localMid,rf=s.kind==='rf'?s.rfAmplitudeHz:0;
      rotate(state,geometry.z,dt,rf,phase,s.gradientTm,p.offResonanceHz);
      relax(state,dt/2,p);for(const k of ['mx','my','mz'])heat.apply(state[k],dt/2);
      const a=GAMMA*s.gradientTm,q0=gIntegral;
      bIntegral+=q0*q0*dt+q0*a*dt*dt+a*a*dt*dt*dt/3;gIntegral+=a*dt;t+=dt;steps++;
      if(rf>0)rfPhaseMaxStep=Math.max(rfPhaseMaxStep,Math.abs(TAU*freq*dt));
      waveform.timeMs.push(t*1000);waveform.gradientTm.push(s.gradientTm);waveform.rfAmplitudeHz.push(rf);waveform.rfFrequencyHz.push(s.kind==='rf'?freq:0);waveform.rfPhaseRad.push(s.kind==='rf'?phase:0);waveform.gradientIntegralRadPerM.push(gIntegral);
    }
    function advance(time,s,startLocal) {
      if(time<=0)return;const n=Math.max(1,Math.ceil(time/dtMax)),dt=time/n;
      for(let j=0;j<n;j++)step(dt,s,startLocal+(j+.5)*dt);
    }
    function receive() {let x=0,y=0;for(let i=0;i<p.points;i++){x+=coil[i]*state.mx[i];y+=coil[i]*state.my[i];}return [x/p.points,y/p.points];}
    for(let index=0;index<program.length;index++) {
      const s=program[index],duration=s.durationMs/1000;
      if(s.kind==='readout') {
        const real=[],imag=[],magnitude=[],timeMs=[],interval=duration/(s.samples-1);
        for(let j=0;j<s.samples;j++){if(j>0)advance(interval,s,(j-1)*interval);const v=receive();real.push(v[0]);imag.push(v[1]);magnitude.push(Math.hypot(...v));timeMs.push(j*interval*1000);}
        const spec=spectrum(real,imag,interval,s.gradientTm);
        readouts.push({segment:index,timeMs,real,imag,magnitude,frequencyHz:spec.frequencyHz,spectrum:spec,gradientTm:s.gradientTm,sampleIntervalSeconds:interval});
      } else advance(duration,s,0);
      snapshots.push({segment:index,kind:s.kind,timeMs:t*1000,...cloneState(state)});
    }
    const profile=Array.from(state.mx,(x,i)=>Math.hypot(x,state.my[i])),phase=Array.from(state.mx,(x,i)=>Math.atan2(state.my[i],x));
    const last=readouts[readouts.length-1]||null,norm=Array.from(state.mx,(x,i)=>Math.hypot(x,state.my[i],state.mz[i]));
    const warnings=[];
    if(rfPhaseMaxStep>.35)warnings.push({id:'rf-time-resolution',es:'El giro de fase RF por paso es grande; comprueba convergencia temporal.',en:'RF phase changes appreciably per step; check time convergence.'});
    const readK=last?Math.abs(GAMMA/TAU*last.gradientTm*(last.timeMs[last.timeMs.length-1]/1000)):0;
    if(readK*geometry.dz>.5)warnings.push({id:'spatial-aliasing',es:'La fase de lectura supera Nyquist en la malla espacial; aumenta puntos o reduce lectura/gradiente.',en:'Readout phase exceeds the spatial-grid Nyquist limit; increase points or reduce duration/gradient.'});
    const absoluteGradientArea=program.reduce((sum,s)=>sum+Math.abs(s.gradientTm)*s.durationMs/1000,0),gradientSamplingRisk=GAMMA/TAU*absoluteGradientArea*geometry.dz;
    if(gradientSamplingRisk>.5)warnings.push({id:'gradient-integral-sampling',es:'La integral absoluta de gradiente indica riesgo de fase espacial submuestreada; no equivale a un q de coherencia durante RF. Comprueba convergencia.',en:'The absolute gradient integral indicates potential spatial phase undersampling; it is not coherence q during RF. Check convergence.'});
    const maxReadoutAbsFrequency=last?Math.abs(p.offResonanceHz)+Math.abs(GAMMA/TAU*last.gradientTm*geometry.length/2):null;
    if(last && last.sampleIntervalSeconds>0 && maxReadoutAbsFrequency>1/(2*last.sampleIntervalSeconds))warnings.push({id:'temporal-aliasing',es:'La lectura no cubre la frecuencia de toda la muestra, incluido el offset, sin aliasing.',en:'Readout sampling does not cover the whole sample frequency, including offset, without aliasing.'});
    if(p.relaxation&&p.T2Seconds>2*p.T1Seconds)warnings.push({id:'relaxation-relation',es:'T2 > 2T1 no corresponde al límite habitual de relajación física de espín 1/2.',en:'T2 > 2T1 is outside the usual physical spin-1/2 relaxation bound.'});
    return {
      version:VERSION,evidence:'computed-teaching-forward-model',options:{...p},program,
      zMm:Array.from(geometry.z,z=>z*1000),...cloneState(state),phase,signalProfile:profile,coilProfile:Array.from(coil),snapshots,waveform,
      readout:last||{timeMs:[],real:[],imag:[],magnitude:[],frequencyHz:[],spectrum:{real:[],imag:[],magnitude:[],frequencyHz:[],positionMm:[]}},
      metrics:{durationMs:t*1000,spatialStepMm:geometry.dz*1000,transverseMean:profile.reduce((a,b)=>a+b,0)/p.points,maxBlochNorm:Math.max(...norm),longitudinalMean:Array.from(state.mz).reduce((a,b)=>a+b,0)/p.points,encodingFrequencySpanHz:appliedEncodingSpan,rfSweepBandwidthHz:appliedSweepBandwidth,activeRfSegments:activeRf.length,gradientIntegralRadPerM:gIntegral,gradientOnlyIntegralSquaredSPerM2:bIntegral,gradientOnlyIntegralIsDOSYb:false,nominalSpatialResolutionMm:last&&last.gradientTm!==0&&last.sampleIntervalSeconds>0?1000/(Math.abs(GAMMA/TAU*last.gradientTm)*last.real.length*last.sampleIntervalSeconds):null,readoutBandwidthHz:last&&last.sampleIntervalSeconds>0?1/last.sampleIntervalSeconds:null,diffusionRmsUm:Math.sqrt(2*p.diffusionM2s*t)*1e6},
      diagnostics:{steps,...heat.stats(),rfMaxPhaseStepRad:rfPhaseMaxStep,gradientIntegralSamplingCyclesPerCell:gradientSamplingRisk,maxReadoutAbsFrequencyHz:maxReadoutAbsFrequency,finite:profile.every(Number.isFinite),warnings},
      assumptions,sources,units:{z:'mm',magnetization:'M/M0',phase:'rad',time:'ms',gradient:'T/m',D:'m2/s',gamma:'rad/(s T)'},
      equation:'dM/dt = Omega(z,t) x M + D d2M/dz2 - (Mx/T2, My/T2, (Mz-1)/T1)',
      phaseConvention:'Mplus=Mx+iMy; dMplus/dt=+i omega Mplus. Reversing the receiver convention conjugates phase.'
    };
  }
  function simulate(input={}) {
    const p=options(input),program=input.program||[
      {kind:'rf',durationMs:p.rfDurationMs,gradientTm:p.encodingGradientTm,rfAmplitudeHz:p.rfAmplitudeHz,rfPhaseDegrees:p.rfPhaseDegrees,chirpBandwidthHz:p.chirpBandwidthHz,chirpCenterHz:p.chirpCenterHz},
      {kind:'evolve',durationMs:p.evolutionMs,gradientTm:p.evolutionGradientTm},
      {kind:'readout',durationMs:p.readoutMs,gradientTm:p.readoutGradientTm,samples:p.readoutPoints}
    ];
    return run(p,program,input.initialMagnetization);
  }
  function propagate(initial,program,input={}) {return run(options(input),program,initial);}
  function relError(reference,candidate) {let e=0,s=0;for(let i=0;i<reference.length;i++){e+=(candidate[i]-reference[i])**2;s+=reference[i]**2;}return Math.sqrt(e/Math.max(s,1e-24));}
  function convergence(input={}) {
    const p=options(input);
    if(p.points>128)throw new RangeError('Convergence doubles the grid; start with at most 128 points.');
    if(p.timeStepUs<.2)throw new RangeError('Convergence halves the step; start with at least 0.2 us.');
    if(input.initialMagnetization!==undefined)throw new RangeError('Convergence uses the common uniform initial state; custom grids need an explicit comparison.');
    const base=simulate(p),timeRefined=simulate({...p,timeStepUs:p.timeStepUs/2}),spaceRefined=simulate({...p,points:p.points*2,timeStepUs:p.timeStepUs/2});
    // Cell averages of the fine grid compare the same physical volumes.
    const coarse={};for(const k of ['mx','my','mz'])coarse[k]=Array.from({length:p.points},(_,i)=>(spaceRefined[k][2*i]+spaceRefined[k][2*i+1])/2);
    const transverseError=(a,b)=>Math.sqrt((relError(a.mx,b.mx)**2+relError(a.my,b.my)**2)/2);
    const errors={timeMagnetizationRelative:transverseError(timeRefined,base),spaceMagnetizationRelative:transverseError(coarse,timeRefined),timeReadoutRelative:base.readout.real.length?Math.sqrt((relError(timeRefined.readout.real,base.readout.real)**2+relError(timeRefined.readout.imag,base.readout.imag)**2)/2):0,spaceReadoutRelative:base.readout.real.length?Math.sqrt((relError(spaceRefined.readout.real,timeRefined.readout.real)**2+relError(spaceRefined.readout.imag,timeRefined.readout.imag)**2)/2):0};
    return {version:VERSION,base,timeRefined,spaceRefined,errors,interpretation:{es:'Comparación de discretizaciones, no cota rigurosa ni validación experimental. Al refinar espacio se mantiene el paso temporal ya refinado. Revisa aliasing y convergencia conjuntamente.',en:'Discretization comparison, not a rigorous error bound or experimental validation. Spatial refinement retains the refined time step. Check aliasing and convergence together.'}};
  }
  return Object.freeze({VERSION,GAMMA,sources,assumptions,defaults,simulate,propagate,convergence});
});
