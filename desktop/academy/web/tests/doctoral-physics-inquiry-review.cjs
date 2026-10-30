/* Independent scientific review of the neighbouring inquiry engine.
   Cross-engine physical checks; no edits to inquiry source and no hardware QA. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const M=require('../doctoral-inquiry.js'),P=require('../doctoral-physics.js'),checks=[];
function near(a,b,relative=1e-9,absolute=1e-12){return Math.abs(a-b)<=Math.max(absolute,relative*Math.max(Math.abs(a),Math.abs(b)));}
function check(id,passed,detail={}){checks.push({id,passed:!!passed,detail});if(!passed)console.error('FAIL',id,detail);}
function hash(file){return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');}
const base={noise:0,gradientScale:1.08,recycleSeconds:30,T1Seconds:10,T2Seconds:5,seed:731};
for(const [name,factor]of [['pgse',1],['ste',.5],['led',.5],['double-ste',.25]]){
 const x=M.campaign({...base,sequence:name}),p=x.parameters,loops=name==='double-ste'?2:1;
 const excitation=1,recovery=1-Math.exp(-p.recycleSeconds/p.T1Seconds),d=p.deltaMs/1000,Delta=p.bigDeltaMs/1000;
 const relaxation=name==='pgse'?Math.exp(-2*Delta/p.T2Seconds):Math.exp(-loops*(Delta-d)/p.T1Seconds-2*loops*d/p.T2Seconds);
 const expected=factor*excitation*recovery*relaxation;
 check('campaign-'+name+'-ideal-selected-pathway-amplitude',near(x.signalEfficiency,expected,1e-10),{actual:x.signalEfficiency,expected,idealTransferFactor:factor,scope:'relaxation remains an explicitly simplified teaching proxy'});
 const raw=P.preset(name==='led'?'ste':name,{deltaMs:p.deltaMs,bigDeltaMs:p.bigDeltaMs,gradientMilliTeslaPerM:p.gradientMax*p.gradientScale*1000});
 const sequence=P.compileSequence(raw);
 check('campaign-'+name+'-b-independent-waveform-integration',near(x.bMax,sequence.bSecondsPerM2,1e-12),{actual:x.bMax,expected:sequence.bSecondsPerM2});
 check('campaign-'+name+'-signal-space-noiseless-D',near(x.fit.D,8e-10,1e-7,1e-17),{fitD:x.fit.D});
 if(name==='double-ste')check('double-ste-flow-first-moment-independent-zero',Math.abs(sequence.uRadSecondsPerM)<1e-6&&sequence.bSecondsPerM2>0);
}
const calibrated=M.campaign({...base,sequence:'ste'}),uncalibrated=M.campaign({...base,gradientScale:1,sequence:'ste'});
check('independent-standard-gradient-scale-square-law',near(uncalibrated.fit.D/calibrated.fit.D,1.08**2,1e-7));
check('standard-calibration-refuses-thermal-reference-mismatch',M.gradientCalibration(2.2e-9,1.9e-9,298.15,293).usable===false);
const flowing=M.campaign({...base,seed:3,sequence:'ste'}),compensated=M.campaign({...base,seed:3,sequence:'double-ste'});
check('same-D-uncompensated-flow-bias-removed-by-mirrored-loops',flowing.fit.D>8e-10&&near(compensated.fit.D,8e-10,1e-7,1e-17),{single:flowing.fit.D,mirrored:compensated.fit.D});
const blind=M.runBlindCase('case-b',[], '', '',5),D=8e-10,maxB=Math.max(...blind.b);
const errors=blind.signal.map((y,i)=>Math.abs(y-Math.exp(-D*blind.b[i])*P.sinc(3*Math.sqrt(blind.b[i]/maxB))));
check('blind-flow-finite-constant-velocity-distribution-phase-proportional-to-sqrt-b',Math.max(...errors)<.020,{maximumSignalDifference:Math.max(...errors),allowedNoiseBound:.020,model:'E=exp(-Db)*sinc(c*sqrt(b)); each scalar noise standard deviation is .004'});
const inv=M.inverse({contrast:4,snr:1000,bootstrap:10,reveal:true});
inv.methods.forEach(method=>{
 check('inverse-'+method.id+'-weights-are-bin-amplitudes-at-b-zero',near(method.prediction[0],method.weights.reduce((a,b)=>a+b,0),1e-12),{firstPrediction:method.prediction[0],area:method.area});
 const k=inv.b.length-1,reconstructed=inv.grid.reduce((s,D,i)=>s+method.weights[i]*Math.exp(-inv.b[k]*D),0);
 check('inverse-'+method.id+'-kernel-reconstructed-independently',near(method.prediction[k],reconstructed,1e-12));
 check('inverse-'+method.id+'-positive-fit-and-convergence-not-species-proof',method.weights.every(w=>w>=0)&&Number.isFinite(method.projectedGradient)&&typeof method.converged==='boolean');
});
check('inverse-apparent-mono-D-not-assigned-to-one-component',inv.mono.D>inv.truth.D[0]&&inv.mono.D<inv.truth.D[1]);
const identical=M.inverse({overlap:1,bootstrap:10}),distinct=M.inverse({overlap:0,bootstrap:10}),overlap=M.inverse({overlap:.99,bootstrap:10});
check('joint-identical-templates-unidentifiable-despite-two-generating-D',identical.joint.identifiable===false&&identical.joint.curveFits.length===0);
check('joint-template-conditioning-worsens-with-overlap',overlap.joint.conditionIndicator>distinct.joint.conditionIndicator*100);
check('residual-bootstrap-misspecification-and-coverage-boundary',inv.bootstrap.coverageValidated===false&&inv.bootstrap.kind==='residual-bootstrap-conditional-on-mono-model');
const adv=M.advanced({snr:1000,reveal:true}),p=adv.parameters;
const reference=adv.b.map(b=>{const f=Math.exp(-p.ratePerSecond*(p.timeSeconds+p.durationSeconds/2));return f*Math.exp(-b*1.2e-9)+(1-f)*Math.exp(-b*3.5e-10);});
check('advanced-reference-normalized-mixture-not-new-diffusion-coefficient',near(reference[0],1)&&reference.every(y=>y>=0&&y<=1));
const method=id=>adv.methods.find(m=>m.id===id);
const midpointError=Math.max(...method('ideal-snapshot').signal.map((y,i)=>Math.abs(y-reference[i])));
check('advanced-midpoint-snapshot-agrees-independent-reaction-mixture',midpointError<.006,{maximumDifference:midpointError,noiseStandardDeviation:.001});
check('advanced-paired-still-not-midpoint-snapshot',method('paired').rmsToMidSnapshot>method('ideal-snapshot').rmsToMidSnapshot);
const stable=M.advanced({ratePerSecond:0,snr:1000,reveal:true});
check('stable-time-control-suppresses-sequential-order-bias',Math.abs(stable.methods[0].fit.D-stable.methods[1].fit.D)<.02*stable.truth.D[0]);
check('spatial-correction-divides-known-profile-no-self-calibration',adv.spatial.profile.every(x=>x>0)&&adv.spatial.readoutAttenuation.every(x=>x>0)&&adv.assumptions.some(s=>s.includes('independently known')));
check('spen-surrogate-scope-not-bloch-or-hardware-validation',adv.assumptions.some(s=>s.includes('not a Bloch/chirp simulation'))&&adv.evidenceStatus==='synthetic-teaching-simulation');
const report={schemaVersion:'1.0',reviewer:'independent-doctoral-physics-agent',version:'1.2.0',evidenceStatus:'synthetic-independent-scientific-code-review',passed:checks.every(c=>c.passed),counts:{total:checks.length,passed:checks.filter(c=>c.passed).length},sourceSha256:{'doctoral-inquiry.js':hash(path.join(__dirname,'../doctoral-inquiry.js')),'doctoral-physics.js':hash(path.join(__dirname,'../doctoral-physics.js'))},checks,reviewLimits:['Analytic and computational teaching-model review, not experimental/hardware validation.','Campaign RF amplitude checked physically; relaxation, steady-state recovery and LED response remain explicit proxies.','Blind-control observation summaries are authored case fixtures, not acquired measurements.','Inverse spectral templates are known; no blind chemical identity claim.','Advanced SPEN/ultrafast models are explicitly spatial surrogates, not pulse-program/Bloch implementations.']};
const output=process.argv[2]?path.resolve(process.argv[2]):path.join(__dirname,'doctoral-physics-inquiry-review.json');if(fs.existsSync(output))throw new Error('Refusing to overwrite scientific review evidence.');fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:report.passed,counts:report.counts,sourceSha256:report.sourceSha256,output}));if(!report.passed)process.exitCode=1;
