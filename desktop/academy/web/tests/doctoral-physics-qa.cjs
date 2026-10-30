/* Independent numerical and stochastic QA, not experimental validation.
   Run: node doctoral-physics-qa.cjs [--output fresh-report.json] */
'use strict';
const fs=require('node:fs'),path=require('node:path');
const P=require('../doctoral-physics.js');
const checks=[];
function check(id,passed,detail={}){checks.push({id,passed:!!passed,detail});if(!passed)console.error('FAIL:',id,detail);}
function near(a,b,relative=1e-10,absolute=1e-7){return Math.abs(a-b)<=Math.max(absolute,relative*Math.max(Math.abs(a),Math.abs(b)));}
function throws(id,fn){try{fn();check(id,false,{reason:'did not reject'});}catch(e){check(id,e instanceof RangeError||e instanceof TypeError,{error:e.message});}}
const gamma=267.52218744e6,g=.2,d=.0015,Delta=.06,Q=gamma*g*d;
const pg=P.compileSequence(P.preset('pgse'));
const expectedB=(gamma*g*d)**2*(Delta-d/3),expectedU=Q*Delta;
check('pgse-b-independent-stejskal-tanner',near(pg.bSecondsPerM2,expectedB),{actual:pg.bSecondsPerM2,expected:expectedB});
check('pgse-first-moment-independent',near(pg.uRadSecondsPerM,expectedU),{actual:pg.uRadSecondsPerM,expected:expectedU});
check('pgse-balanced',pg.balanced&&near(pg.qFinalRadPerM,0));
check('pgse-rf-events-explicit',pg.rfEvents.length===2&&pg.rfEvents[0].angleDegrees===90&&pg.rfEvents[1].angleDegrees===180);
const ste=P.compileSequence(P.preset('ste')),double=P.compileSequence(P.preset('double-ste'));
check('ste-b-identical-ideal-waveform',near(ste.bSecondsPerM2,expectedB));
check('ste-storage-q-preserved',ste.segments.filter(s=>s.coherence===0).every(s=>near(s.qStartRadPerM,Q)&&near(s.qEndRadPerM,Q)&&s.bEndSecondsPerM2>s.bStartSecondsPerM2));
check('ste-rf-three-events',ste.rfEvents.length===3);
check('double-ste-five-rf-events-no-fictional-excitation',double.rfEvents.length===5&&double.rfEvents.every(e=>e.angleDegrees===90));
check('double-ste-b-positive-adds',near(double.bSecondsPerM2,2*expectedB));
check('double-ste-first-moment-cancels',near(double.uRadSecondsPerM,0,1e-9,1e-6)&&double.balanced);
check('ideal-rf-transfer-cost-separate',[pg.selectedPathwayAmplitude,ste.selectedPathwayAmplitude,double.selectedPathwayAmplitude].join(',')==='1,0.5,0.25');
check('custom-coherence-does-not-imply-known-rf-amplitude',P.compileSequence({segments:[{durationMs:1,gradientMilliTeslaPerM:0,coherence:0}]}).selectedPathwayAmplitude===null);
const third=P.compileSequence({segments:[{durationMs:1,gradientMilliTeslaPerM:100,coherence:1},{durationMs:40,gradientMilliTeslaPerM:300,coherence:0},{durationMs:1,gradientMilliTeslaPerM:100,coherence:-1}]});
const middle=third.segments[1];
check('nonzero-spoiler-p0-no-new-encoding',near(middle.qEndRadPerM,middle.qStartRadPerM)&&near(middle.bEndSecondsPerM2-middle.bStartSecondsPerM2,middle.qStartRadPerM**2*.04));
const arbitrary=P.compileSequence({segments:[{durationMs:2.1,gradientMilliTeslaPerM:124,coherence:1},{durationMs:7.3,gradientMilliTeslaPerM:-40,coherence:-1},{durationMs:11.4,gradientMilliTeslaPerM:180,coherence:0},{durationMs:3.8,gradientMilliTeslaPerM:270,coherence:-1}]});
// Independent dense midpoint reconstruction uses raw input g,p,h rather than
// the compiled cumulative q,b,u or atTime implementation.
let t=0,q=0,bN=0,uN=0,tailN=0;const raw=[];
arbitrary.segments.forEach(s=>{const n=20000,h=s.durationMs/1000/n,a=gamma*s.coherence*s.gradientMilliTeslaPerM/1000;for(let i=0;i<n;i++){const midpointQ=q+a*h/2;raw.push({midpointQ,h});bN+=midpointQ*midpointQ*h;uN+=midpointQ*h;q+=a*h;t+=h;}});
raw.forEach(s=>{tailN+=(q-s.midpointQ)**2*s.h;});
check('arbitrary-b-independent-midpoint-quadrature',near(arbitrary.bSecondsPerM2,bN,1e-8));
check('arbitrary-u-independent-midpoint-quadrature',near(arbitrary.uRadSecondsPerM,uN,1e-8));
check('arbitrary-q-independent-midpoint-integration',near(arbitrary.qFinalRadPerM,q,1e-8));
check('unbalanced-backward-b-independent',near(P.atTime(arbitrary,t).backwardBSecondsPerM2,tailN,1e-8));
const inverted=P.compileSequence({segments:pg.segments.map(s=>({durationMs:s.durationMs,gradientMilliTeslaPerM:-s.gradientMilliTeslaPerM,coherence:s.coherence}))});
check('gradient-sign-reversal-preserves-b',near(inverted.bSecondsPerM2,pg.bSecondsPerM2));
check('gradient-sign-reversal-reverses-u',near(inverted.uRadSecondsPerM,-pg.uRadSecondsPerM));
const scaled=P.compileSequence({segments:pg.segments.map(s=>({durationMs:s.durationMs,gradientMilliTeslaPerM:2*s.gradientMilliTeslaPerM,coherence:s.coherence}))});
check('whole-waveform-scaling-b-square',near(scaled.bSecondsPerM2,4*pg.bSecondsPerM2));
check('whole-waveform-scaling-u-linear',near(scaled.uRadSecondsPerM,2*pg.uRadSecondsPerM));
const uniform=P.signal(pg,{velocityMode:'uniform',velocityMPerS:.0002}),none=P.signal(pg),spread=P.signal(pg,{velocityMode:'distribution',velocityMPerS:0,velocitySpreadMPerS:4.5/pg.uRadSecondsPerM});
check('uniform-velocity-rotates-no-magnitude-loss',near(uniform.magnitude,none.magnitude));
check('uniform-velocity-correct-complex-phase',near(uniform.real,none.real*Math.cos(.0002*expectedU))&&near(uniform.imag,none.real*Math.sin(.0002*expectedU)));
check('velocity-distribution-preserves-negative-real',spread.real<0&&near(spread.real,none.real*Math.sin(4.5)/4.5));
check('double-ste-constant-velocity-compensated',near(P.signal(double,{velocityMode:'uniform',velocityMPerS:.005}).real,P.signal(double).real)&&near(P.signal(double,{velocityMode:'uniform',velocityMPerS:.005}).imag,0));
const stored=P.compileSequence({segments:[{durationMs:2,gradientMilliTeslaPerM:100,coherence:1},{durationMs:40,gradientMilliTeslaPerM:0,coherence:0}]});
const before=P.signal(stored,{},.002),after=P.signal(stored);
check('unbalanced-storage-forward-b-grows',after.forwardBSecondsPerM2>before.forwardBSecondsPerM2);
check('unbalanced-storage-pathwise-signal-not-forward-b',near(after.backwardBSecondsPerM2,before.backwardBSecondsPerM2,1e-9)&&near(after.real,before.real,1e-9));
check('unbalanced-reports-spatial-model',after.model.includes('finite slab')&&!after.balanced);
const rigid=P.compileSequence({segments:[{durationMs:20,gradientMilliTeslaPerM:5,coherence:1}]});
const rigidSignal=P.signal(rigid,{diffusionM2PerS:0,velocityMode:'uniform',velocityMPerS:.0001,sampleLengthMeters:100e-6});
const qRigid=gamma*.005*.02,phaseRigid=-gamma*.005*.0001*.02**2/2,spatialRigid=Math.sin(qRigid*100e-6/2)/(qRigid*100e-6/2);
check('unbalanced-constant-gradient-independent-phase',near(rigidSignal.real,spatialRigid*Math.cos(phaseRigid))&&near(rigidSignal.imag,spatialRigid*Math.sin(phaseRigid)));
const prediction=P.assessPrediction(ste,ste.segments.map(s=>s.qEndRadPerM));
check('correct-boundary-prediction',prediction.passed&&prediction.correct===ste.segments.length);
const wrong=ste.segments.map(s=>s.coherence===0?0:s.qEndRadPerM),mistake=P.assessPrediction(ste,wrong);
check('storage-reset-misconception-identified',!mistake.passed&&mistake.checks.some(c=>!c.passed&&c.hint==='storage-keeps-q'));
const duplicate=P.createEnsemble(pg,{count:128,seed:42}),a=duplicate.advance(pg.totalSeconds);duplicate.reset();const aReset=duplicate.advance(pg.totalSeconds);
check('seeded-replay-exact',a.real===aReset.real&&a.imag===aReset.imag&&a.particles[17].zMeters===aReset.particles[17].zMeters);
const zero=P.createEnsemble(pg,{count:512,seed:7,diffusionM2PerS:0}).advance(pg.totalSeconds);
check('stationary-balanced-all-phases-refocus',near(zero.real,1)&&near(zero.imag,0)&&zero.particles.every(p=>Math.abs(p.phaseRad)<1e-9));
const storedMC=P.createEnsemble(stored,{count:128,seed:8});const midMC=storedMC.advance(.002),endMC=storedMC.advance(stored.totalSeconds);
check('p0-brownian-motion-continues-without-new-local-phase',midMC.particles.every((p,i)=>p.phaseRad===endMC.particles[i].phaseRad)&&midMC.particles.some((p,i)=>p.zMeters!==endMC.particles[i].zMeters));
// Six-standard-error bounds are preregistered component-wise; no tuning of
// seeds or silently taking |E|. Reference PGSE expression is independently
// analytic. Finite N cannot establish experimental validity.
for(const [id,sequence,opts,ref] of [
  ['pgse-free',pg,{velocityMode:'none'}, {real:Math.exp(-1e-9*expectedB),imag:0}],
  ['pgse-uniform-flow',pg,{velocityMode:'uniform',velocityMPerS:.0002}, {real:Math.exp(-1e-9*expectedB)*Math.cos(.0002*expectedU),imag:Math.exp(-1e-9*expectedB)*Math.sin(.0002*expectedU)}],
  ['pgse-velocity-distribution',pg,{velocityMode:'distribution',velocityMPerS:0,velocitySpreadMPerS:4.5/expectedU},{real:Math.exp(-1e-9*expectedB)*Math.sin(4.5)/4.5,imag:0}],
  ['double-ste-compensated',double,{velocityMode:'distribution',velocityMPerS:.001,velocitySpreadMPerS:.005},{real:Math.exp(-2e-9*expectedB),imag:0}]
]){
  const mc=P.createEnsemble(sequence,{count:80000,seed:12648430,...opts}).advance(sequence.totalSeconds);
  const zRe=Math.abs(mc.real-ref.real)/Math.max(mc.standardErrorReal,1e-10),zIm=Math.abs(mc.imag-ref.imag)/Math.max(mc.standardErrorImag,1e-10);
  check('monte-carlo-'+id,zRe<6&&zIm<6,{N:mc.count,real:mc.real,imag:mc.imag,expectedReal:ref.real,expectedImag:ref.imag,standardErrorReal:mc.standardErrorReal,standardErrorImag:mc.standardErrorImag,zReal:zRe,zImaginary:zIm,bound:6});
}
const brownian=P.compileSequence({segments:[{durationMs:100,gradientMilliTeslaPerM:0,coherence:1}]}),walk=P.createEnsemble(brownian,{count:80000,seed:314159}).advance(.1),expectedMSD=2e-9*.1;
const msdSE=expectedMSD*Math.sqrt(2/walk.count),meanSE=Math.sqrt(expectedMSD/walk.count);
check('equilibrium-self-diffusion-zero-mean',Math.abs(walk.meanDisplacementMeters)<6*meanSE,{mean:walk.meanDisplacementMeters,standardError:meanSE});
check('brownian-mean-square-displacement-2Dt',Math.abs(walk.meanSquaredDisplacementMeters2-expectedMSD)<6*msdSE,{actual:walk.meanSquaredDisplacementMeters2,expected:expectedMSD,standardError:msdSE});
throws('reject-empty-sequence',()=>P.compileSequence({segments:[]}));
throws('reject-missing-segments',()=>P.compileSequence({}));
throws('reject-nan-gradient',()=>P.compileSequence({segments:[{durationMs:1,gradientMilliTeslaPerM:NaN,coherence:1}]}));
throws('reject-zero-duration',()=>P.compileSequence({segments:[{durationMs:0,gradientMilliTeslaPerM:0,coherence:1}]}));
throws('reject-invalid-coherence',()=>P.compileSequence({segments:[{durationMs:1,gradientMilliTeslaPerM:0,coherence:2}]}));
throws('reject-overlong-sequence',()=>P.compileSequence({segments:[{durationMs:10000,gradientMilliTeslaPerM:0,coherence:1},{durationMs:10000,gradientMilliTeslaPerM:0,coherence:0},{durationMs:1,gradientMilliTeslaPerM:0,coherence:-1}]}));
throws('reject-invalid-ste-timing',()=>P.preset('ste',{bigDeltaMs:2,deltaMs:1.5}));
throws('reject-negative-diffusion',()=>P.signal(pg,{diffusionM2PerS:-1e-9}));
throws('reject-negative-seed',()=>P.createEnsemble(pg,{seed:-1}));
throws('reject-fractional-count',()=>P.createEnsemble(pg,{count:100.5}));
throws('reject-time-reversal',()=>{const e=P.createEnsemble(pg,{count:8});e.advance(.01);e.advance(.001);});
throws('reject-time-after-sequence',()=>P.atTime(pg,pg.totalSeconds+.001));
throws('reject-unbounded-prediction',()=>P.assessPrediction(pg,pg.segments.map(()=>Infinity)));
check('all-b-increments-nonnegative',[pg,ste,double,arbitrary,inverted].every(s=>s.segments.every(r=>r.bEndSecondsPerM2>=r.bStartSecondsPerM2)));
check('trace-b-monotone',P.trace(arbitrary,20).every((p,i,all)=>i===0||p.bSecondsPerM2>=all[i-1].bSecondsPerM2-1e-4));
const report={schemaVersion:'1.0',version:P.version,evidenceStatus:'synthetic-software-qa-only',passed:checks.every(c=>c.passed),counts:{total:checks.length,passed:checks.filter(c=>c.passed).length},checks};
const arg=process.argv.indexOf('--output');if(arg>=0){const out=path.resolve(process.argv[arg+1]);if(fs.existsSync(out))throw new Error('Refusing to overwrite existing QA report.');fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n');}
console.log(JSON.stringify({passed:report.passed,...report.counts}));process.exitCode=report.passed?0:1;
