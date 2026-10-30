/* DiffAtOnce Academy 1.2 — auditable free-diffusion teaching models.
   Angular gamma, SI internally; effective gradient a=gamma*p*g.
   A selected coherence-pathway coefficient is followed across ideal RF.
   This is not a pulse-program compiler and never operates an instrument. */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.AcademyDoctoralPhysics = api;
})(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';
  const GAMMA = 267.52218744e6;
  const EVIDENCE = 'synthetic-teaching-simulation';
  function finite(value, name, min, max) {
    if (typeof value !== 'number' || !Number.isFinite(value) || value < min || value > max)
      throw new RangeError(name + ' must be finite and in [' + min + ', ' + max + '].');
    return value;
  }
  function sinc(x) { return Math.abs(x) < 1e-5 ? 1 - x*x/6 + x**4/120 : Math.sin(x)/x; }
  function compileSequence(input) {
    if (!input || !Array.isArray(input.segments) || !input.segments.length || input.segments.length > 64)
      throw new RangeError('Provide 1–64 constant-gradient/coherence segments.');
    let t=0, q=0, b=0, u=0, absArea=0;
    const gamma = input.gammaRadPerSecondPerTesla === undefined ? GAMMA : finite(input.gammaRadPerSecondPerTesla, 'gamma', 1e6, 1e9);
    const segments = input.segments.map((row, index) => {
      if (!row || typeof row !== 'object') throw new TypeError('Invalid segment.');
      const durationMs=finite(row.durationMs, 'durationMs', .001, 10000);
      const gradientMilliTeslaPerM=finite(row.gradientMilliTeslaPerM, 'gradientMilliTeslaPerM', -2000, 2000);
      if (![ -1, 0, 1 ].includes(row.coherence)) throw new RangeError('Coherence must be -1, 0 or +1.');
      const h=durationMs/1000, g=gradientMilliTeslaPerM/1000, a=gamma*row.coherence*g, q1=q+a*h;
      // Endpoint form is algebraically exact and remains nonnegative without
      // catastrophic subtraction near balanced/negative-q intervals.
      const db=h*(q*q+q*q1+q1*q1)/3, du=h*(q+q1)/2;
      const result={index, label:typeof row.label==='string'?row.label.slice(0,120):'', durationMs,
        gradientMilliTeslaPerM, coherence:row.coherence, hSeconds:h, physicalGradientTPerM:g,
        effectiveRateRadPerMPerS:a, startSeconds:t, endSeconds:t+h,
        qStartRadPerM:q, qEndRadPerM:q1, bStartSecondsPerM2:b, bEndSecondsPerM2:b+db,
        uStartRadSecondsPerM:u, uEndRadSecondsPerM:u+du};
      t+=h; q=q1; b+=db; u+=du; absArea+=Math.abs(a*h);
      return Object.freeze(result);
    });
    if (t>20) throw new RangeError('Total teaching sequence must be at most 20 s.');
    const tolerance=Math.max(1e-8, absArea*1e-10);
    let previous=0;
    const rfEvents=[];
    segments.forEach((s,index)=>{
      if(s.coherence!==previous) {
        const from=previous,to=s.coherence;
        rfEvents.push({timeSeconds:s.startSeconds, from, to,
          suggestedAngleDegrees:from===0||to===0?90:180,
          kind:'ideal-selected-pathway-transition', atSegment:index});
        previous=to;
      }
    });
    // Exact pulse angle/phase cycling cannot be inferred from p alone.
    // Explicit preset events supply one ideal pathway, not all RF branches.
    if(input.rfEvents!==undefined) {
      if(!Array.isArray(input.rfEvents)||input.rfEvents.length>128)throw new RangeError('Invalid RF events.');
      input.rfEvents.forEach(e=>{
        finite(e.timeSeconds,'RF event time',0,t);
        finite(e.angleDegrees,'RF angle',0,360);
        if(typeof e.label!=='string'||e.label.length>160)throw new RangeError('Invalid RF label.');
      });
    }
    const output={evidenceStatus:EVIDENCE, convention:'Psi ∝ exp(-i q z); qdot=gamma*p*g; balanced E=exp(-D*b+i*v*u).',
      gammaRadPerSecondPerTesla:gamma, totalSeconds:t, qFinalRadPerM:q,
      bSecondsPerM2:b, uRadSecondsPerM:u, firstMomentRadSecondsPerM:u,
      balanced:Math.abs(q)<=tolerance, balanceToleranceRadPerM:tolerance,
      selectedPathwayAmplitude:input.selectedPathwayAmplitude===undefined||input.selectedPathwayAmplitude===null?null:finite(input.selectedPathwayAmplitude,'selectedPathwayAmplitude',0,1),
      preset:typeof input.preset==='string'?input.preset:'custom',segments:Object.freeze(segments),
      rfEvents:Object.freeze(input.rfEvents ? input.rfEvents.map(e=>Object.freeze({...e})) : rfEvents.map(e=>Object.freeze(e))),
      assumptions:Object.freeze(['One selected single-spin coherence pathway; ideal instantaneous RF; spatially linear rectangular gradient segments.',
        'Free 1D Gaussian diffusion with constant D; no restriction, exchange, relaxation, eddy currents or RF imperfections.',
        'p=0 freezes q but does not reset it; the stored Fourier coefficient is complex whereas physical Mz is real.',
        'RF transition labels from p alone are illustrative; actual pulse angles, phases, pathway selection and Bruker mappings require the pulse program.'])};
    return Object.freeze(output);
  }
  function preset(name, parameters={}) {
    const d=parameters.deltaMs===undefined?1.5:finite(parameters.deltaMs,'deltaMs',.001,1000);
    const Delta=parameters.bigDeltaMs===undefined?60:finite(parameters.bigDeltaMs,'bigDeltaMs',d,5000);
    const g=parameters.gradientMilliTeslaPerM===undefined?200:finite(parameters.gradientMilliTeslaPerM,'gradientMilliTeslaPerM',-2000,2000);
    const transverseGap=parameters.transverseGapMs===undefined?2:finite(parameters.transverseGapMs,'transverseGapMs',0,1000);
    const rows=[];const rf=[];
    const add=(h,grad,p,label)=>{if(h>0)rows.push({durationMs:h,gradientMilliTeslaPerM:grad,coherence:p,label});};
    const event=(ms,angle,label)=>rf.push({timeSeconds:ms/1000,angleDegrees:angle,label});
    if(name==='pgse') {
      event(0,90,'90°: 0 → +1');
      add(d,g,1,'Encode / Codificar');
      add((Delta-d)/2,0,1,'Transverse / Transversal');
      event((Delta+d)/2,180,'180°: +1 → −1');
      add((Delta-d)/2,0,-1,'Transverse / Transversal');
      add(d,g,-1,'Decode / Descodificar');
      return {preset:name,segments:rows,rfEvents:rf,selectedPathwayAmplitude:1};
    }
    if(name==='ste'||name==='double-ste') {
      if(Delta-d<2*transverseGap)throw new RangeError('STE requires Delta−delta ≥ 2*transverseGap.');
      let cursor=0;
      function steBlock(sign,block) {
        // The second block begins on the transverse pathway recovered by the
        // first: do not invent an extra excitation pulse at their boundary.
        if(block===1)event(cursor,90,'90°: 0 → '+(sign>0?'+1':'−1')+' (block '+block+')');
        add(d,g,sign,'Encode '+block);cursor+=d;
        add(transverseGap,0,sign,'Transverse');cursor+=transverseGap;
        event(cursor,90,'90°: '+(sign>0?'+1':'−1')+' → 0');
        add(Delta-d-2*transverseGap,0,0,'Storage / Almacenamiento');cursor+=Delta-d-2*transverseGap;
        event(cursor,90,'90°: 0 → '+(sign>0?'−1':'+1'));
        add(transverseGap,0,-sign,'Transverse');cursor+=transverseGap;
        add(d,g,-sign,'Decode '+block);cursor+=d;
      }
      steBlock(1,1);
      if(name==='double-ste')steBlock(-1,2);
      return {preset:name,segments:rows,rfEvents:rf,selectedPathwayAmplitude:name==='ste'?.5:.25};
    }
    throw new RangeError('Unknown preset. Use pgse, ste or double-ste.');
  }
  function atTime(sequence, seconds) {
    if(!sequence||!Array.isArray(sequence.segments))throw new TypeError('Compile a sequence first.');
    finite(seconds,'time',0,sequence.totalSeconds);
    let s=sequence.segments.find(row=>seconds<row.endSeconds-1e-15)||sequence.segments[sequence.segments.length-1];
    const h=Math.max(0,Math.min(s.hSeconds,seconds-s.startSeconds)),q0=s.qStartRadPerM,q1=q0+s.effectiveRateRadPerMPerS*h;
    const b=s.bStartSecondsPerM2+h*(q0*q0+q0*q1+q1*q1)/3, u=s.uStartRadSecondsPerM+h*(q0+q1)/2;
    const backwardB=Math.max(0,b-2*q1*u+q1*q1*seconds);
    return {timeSeconds:seconds, segmentIndex:s.index, coherence:s.coherence,
      physicalGradientTPerM:s.physicalGradientTPerM,effectiveRateRadPerMPerS:s.effectiveRateRadPerMPerS,
      qRadPerM:q1,bSecondsPerM2:b,uRadSecondsPerM:u,backwardBSecondsPerM2:backwardB,
      velocityCoefficientRadSecondsPerM:u-q1*seconds,
      balanced:Math.abs(q1)<=sequence.balanceToleranceRadPerM};
  }
  function parameters(options={}) {
    const p={diffusionM2PerS:1e-9,sampleLengthMeters:240e-6,velocityMode:'none',velocityMPerS:20e-6,velocitySpreadMPerS:50e-6,...options};
    finite(p.diffusionM2PerS,'diffusionM2PerS',0,1e-6);
    finite(p.sampleLengthMeters,'sampleLengthMeters',1e-9,.1);
    finite(p.velocityMPerS,'velocityMPerS',-.1,.1);
    finite(p.velocitySpreadMPerS,'velocitySpreadMPerS',0,.1);
    if(!['none','uniform','distribution'].includes(p.velocityMode))throw new RangeError('velocityMode must be none, uniform or distribution.');
    return p;
  }
  function signal(sequence, options={}, seconds=sequence.totalSeconds) {
    const p=parameters(options),a=atTime(sequence,seconds);
    // Pathwise signal for an initially uniform finite slab with unbounded free
    // trajectories and equal detection weight on every tracked molecule.
    // For an unbalanced endpoint it is NOT exp(-D*integral(q²)).
    const spatial=sinc(a.qRadPerM*p.sampleLengthMeters/2);
    const diffusion=Math.exp(-p.diffusionM2PerS*a.backwardBSecondsPerM2);
    const meanVelocity=p.velocityMode==='none'?0:p.velocityMPerS;
    const velocitySpread=p.velocityMode==='distribution'?sinc(p.velocitySpreadMPerS*a.velocityCoefficientRadSecondsPerM):1;
    const phase=meanVelocity*a.velocityCoefficientRadSecondsPerM,amplitude=spatial*diffusion*velocitySpread;
    return {...a,evidenceStatus:EVIDENCE,real:amplitude*Math.cos(phase),imag:amplitude*Math.sin(phase),
      magnitude:Math.abs(amplitude),signedAmplitude:amplitude,commonPhaseRad:phase,
      initialSpatialFactor:spatial,diffusionFactor:diffusion,velocityDistributionFactor:velocitySpread,
      forwardBSecondsPerM2:a.bSecondsPerM2,
      model:'Initially uniform finite slab; free trajectories; equal detection of all tracked particles. At q(T)=0 this reduces to exp(-Db)*velocity characteristic function.',
      parameters:p};
  }
  function rng(seed) {
    if(!Number.isInteger(seed)||seed<0||seed>0xffffffff)throw new RangeError('Seed must be a uint32.');
    let value=seed>>>0;
    return function(){value=(value+0x6D2B79F5)>>>0;let t=value;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return ((t^(t>>>14))>>>0)/4294967296;};
  }
  function gaussian(random) {
    let spare=null;
    return function(){if(spare!==null){const value=spare;spare=null;return value;}const r=Math.sqrt(-2*Math.log(Math.max(Number.MIN_VALUE,random()))),a=2*Math.PI*random();spare=r*Math.sin(a);return r*Math.cos(a);};
  }
  function createEnsemble(sequence, options={}) {
    const p=parameters(options),count=options.count===undefined?192:finite(options.count,'count',8,200000);
    if(!Number.isInteger(count))throw new RangeError('count must be an integer.');
    const seed=options.seed===undefined?20261005:options.seed;
    rng(seed);
    let time=0,index=0,positions,initialPositions,phase,velocity,transverse,normal;
    function reset() {
      const spatialRandom=rng((seed^0x9e3779b9)>>>0),velocityRandom=rng((seed^0x85ebca6b)>>>0);
      normal=gaussian(rng(seed));positions=new Float64Array(count);initialPositions=new Float64Array(count);
      phase=new Float64Array(count);velocity=new Float64Array(count);transverse=new Float64Array(count);
      for(let i=0;i<count;i++) {
        positions[i]=(spatialRandom()-.5)*p.sampleLengthMeters;initialPositions[i]=positions[i];
        transverse[i]=spatialRandom()*2-1;
        velocity[i]=p.velocityMode==='none'?0:p.velocityMPerS+(p.velocityMode==='distribution'?(velocityRandom()*2-1)*p.velocitySpreadMPerS:0);
      }
      time=0;index=0;return snapshot();
    }
    function advance(targetSeconds) {
      finite(targetSeconds,'target time',time,sequence.totalSeconds);
      while(time<targetSeconds-1e-14) {
        const segment=sequence.segments[index];
        const h=Math.min(targetSeconds,segment.endSeconds)-time;
        if(h<=1e-14){index=Math.min(index+1,sequence.segments.length-1);continue;}
        const a=segment.effectiveRateRadPerMPerS,sqrt2D=Math.sqrt(2*p.diffusionM2PerS),sqrtH=Math.sqrt(h);
        for(let i=0;i<count;i++) {
          const n1=normal(),n2=normal();
          // Brownian area conditional on its endpoint: exact joint Gaussian.
          // This avoids Euler phase bias while remaining genuinely stochastic.
          const integratedPosition=positions[i]*h+velocity[i]*h*h/2+sqrt2D*h*sqrtH*(n1/2+n2/Math.sqrt(12));
          phase[i]-=a*integratedPosition;
          positions[i]+=velocity[i]*h+sqrt2D*sqrtH*n1;
        }
        time+=h;
        if(time>=segment.endSeconds-1e-14&&index<sequence.segments.length-1)index++;
      }
      time=targetSeconds;return snapshot();
    }
    function snapshot(sampleCount=count) {
      if(!Number.isInteger(sampleCount)||sampleCount<0||sampleCount>count)throw new RangeError('Invalid snapshot sample count.');
      let re=0,im=0,re2=0,im2=0,displacementMean=0,displacement2=0;
      for(let i=0;i<count;i++) {const r=Math.cos(phase[i]),j=Math.sin(phase[i]),dz=positions[i]-initialPositions[i];re+=r;im+=j;re2+=r*r;im2+=j*j;displacementMean+=dz;displacement2+=dz*dz;}
      re/=count;im/=count;displacementMean/=count;displacement2/=count;
      const varianceRe=Math.max(0,(re2-count*re*re)/(count-1)),varianceIm=Math.max(0,(im2-count*im*im)/(count-1));
      const particles=[];
      for(let i=0;i<sampleCount;i++)particles.push({index:i,initialZMeters:initialPositions[i],zMeters:positions[i],phaseRad:phase[i],velocityMPerS:velocity[i],transverse:transverse[i]});
      return {evidenceStatus:EVIDENCE,timeSeconds:time,count,seed,parameters:{...p},
        real:re,imag:im,magnitude:Math.hypot(re,im),standardErrorReal:Math.sqrt(varianceRe/count),standardErrorImag:Math.sqrt(varianceIm/count),
        meanDisplacementMeters:displacementMean,meanSquaredDisplacementMeters2:displacement2,
        analytic:signal(sequence,p,time),particles};
    }
    reset();
    return {advance,reset,snapshot,sequence,parameters:Object.freeze({...p}),count,seed};
  }
  function trace(sequence, samplesPerSegment=8) {
    if(!Number.isInteger(samplesPerSegment)||samplesPerSegment<1||samplesPerSegment>1000)throw new RangeError('Invalid trace resolution.');
    const points=[];
    sequence.segments.forEach(s=>{for(let i=0;i<=samplesPerSegment;i++)points.push(atTime(sequence,s.startSeconds+s.hSeconds*i/samplesPerSegment));});
    return points;
  }
  function compareVelocityModels(sequence,options={}) {
    return ['none','uniform','distribution'].map(velocityMode=>({velocityMode,...signal(sequence,{...options,velocityMode})}));
  }
  function assessPrediction(sequence,predictedBoundaryQ) {
    if(!Array.isArray(predictedBoundaryQ)||predictedBoundaryQ.length!==sequence.segments.length)throw new RangeError('Predict q at every segment end.');
    const scale=Math.max(1,...sequence.segments.map(s=>Math.abs(s.qEndRadPerM))),tolerance=Math.max(.01,scale*.02);
    const checks=sequence.segments.map((s,i)=>{
      finite(predictedBoundaryQ[i],'predicted q',-1e12,1e12);
      return {segmentIndex:i,predictedRadPerM:predictedBoundaryQ[i],expectedRadPerM:s.qEndRadPerM,
        absoluteErrorRadPerM:Math.abs(predictedBoundaryQ[i]-s.qEndRadPerM),toleranceRadPerM:tolerance,
        passed:Math.abs(predictedBoundaryQ[i]-s.qEndRadPerM)<=tolerance,
        hint:s.coherence===0?'storage-keeps-q':s.gradientMilliTeslaPerM===0?'gradient-off-keeps-q':'integrate-signed-effective-area'};
    });
    return {passed:checks.every(c=>c.passed),correct:checks.filter(c=>c.passed).length,total:checks.length,checks};
  }
  return Object.freeze({version:'1.2.0',gammaRadPerSecondPerTesla:GAMMA,compileSequence,preset,atTime,signal,createEnsemble,trace,compareVelocityModels,assessPrediction,sinc});
});
