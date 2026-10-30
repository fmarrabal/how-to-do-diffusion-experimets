'use strict';
// Independently specified input/physics contracts found during the 1.3 audit.
const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path');
const J = require('../research-journey.js'), I = require('../doctoral-inquiry.js'), P = require('../doctoral-pedagogy.js');
const checks=[];
function check(name,test){try{test();checks.push({name,passed:true});}catch(error){checks.push({name,passed:false,error:error.message});}}
function prepared({negative=false,weak=false}={}){
  let s=J.createCase({seed:6,preset:'isolated'}),truth=J.revealCase(s);
  s=J.calibrate(s,{p90Us:(negative?3:1)*truth.p90Us,gradientScale:1});
  s=J.design(s,weak?{gradientMax:.01,deltaMs:.05,bigDeltaMs:.05,points:16}:{gradientMax:.25,deltaMs:2,bigDeltaMs:80,points:16});
  s=J.acquire(s,{noise:0});s=J.process(s,{lbHz:0});return J.analyze(s,{method:'mono'});
}
check('reserved-control-retains-signed-normalization',()=>{
  const s=prepared({negative:true});assert.ok(s.processing.integrals[0]<0);
  const out=J.proposeMeasurement(s,{candidate:'replicate',noise:0,observe:true,prediction:'The same sample should reproduce the normalized attenuation.'});
  assert.equal(out.measurement.observations[0].signal,1);
  assert.ok(out.measurement.observations.every(r=>r.signal>0));
});
check('weak-encoding-still-allows-planning-a-replicate',()=>{
  const s=prepared({weak:true});assert.ok(Math.max(...s.processing.bs)<1e7);
  const out=J.proposeMeasurement(s,{candidate:'replicate'});assert.equal(out.measurement.selected.id,'replicate');
});
check('nonzero-large-b-fit-has-finite-predictions-and-identified-reference-amplitude',()=>{
  const b=Array.from({length:16},(_,i)=>9.9e11+i*4e9/15),D=1e-9,y=b.map(v=>Math.exp(-(v-b[0])*D)),f=I.fitMono(b,y);
  assert.ok(Number.isFinite(f.D));assert.ok(Math.abs(f.D/D-1)<1e-6);assert.ok(f.prediction.every(Number.isFinite));
  assert.ok(Math.abs(f.referenceAmplitude-1)<1e-6);assert.equal(f.referenceB,b[0]);
  assert.equal(f.amplitude,null);assert.equal(f.extrapolatedAmplitudeFinite,false);
});
check('unrepresentable-b0-extrapolation-cannot-be-used-to-plan-a-zero-b-control',()=>{
  const bs=Array.from({length:16},(_,i)=>9.9e11+i*4e9/15),areas=bs.map(v=>Math.exp(-(v-bs[0])*1e-9));
  let s=J.attachExperimental(J.createCase(),{id:'shifted-reference-fixture',bs,areas,source:'independent mathematical fixture',license:'synthetic test fixture'});
  s=J.process(s);s=J.analyze(s);assert.throws(()=>J.proposeMeasurement(s,{candidate:'replicate'}),/extrapolat|reference|zero/i);
});
for(const method of ['log','signal'])check('imported-'+method+'-fit-retains-finite-observed-range-and-identifies-unrepresentable-b0',()=>{
  const bs=Array.from({length:16},(_,i)=>9.9e11+i*4e9/15),ys=bs.map(b=>Math.exp(-(b-bs[0])*1e-9)),f=P.fitAttenuation(bs,ys,{method,bootstrap:30});
  assert.equal(f.status,'conditional-monoexponential-fit');assert.ok(Math.abs(f.d/1e-9-1)<1e-6);
  assert.ok(f.predicted.every(Number.isFinite));assert.ok(f.rmse<1e-8);assert.equal(f.referenceB,bs[0]);
  assert.ok(Math.abs(f.referenceAmplitude-1)<1e-6);assert.equal(f.amplitude,null);assert.equal(f.extrapolatedAmplitudeFinite,false);
  assert.ok(f.uncertainty.interval95.every(Number.isFinite));
});
for(const method of ['nnls','tikhonov','l1'])check('MC-explicitly-identifies-mono-estimator-when-selected-'+method,()=>{
  let s=prepared();s=J.analyze(s,{method});s=J.uncertainty(s,{samples:30,gradientRelativeSd:0,temperatureSdK:0,processingRelativeSd:0,noiseRelativeSd:0});
  assert.equal(s.uncertainty.estimator.method,'mono');assert.equal(s.uncertainty.estimator.pointEstimateD_m2_s,s.analysis.mono.D);
  assert.equal(s.uncertainty.estimator.selectedMethod,method);assert.equal(s.uncertainty.estimator.selectedEstimatorCovered,false);
  assert.equal(s.uncertainty.estimator.distributionUncertaintyComputed,false);
});
check('mono-MC-identifies-its-own-covered-estimator',()=>{
  const s=J.uncertainty(prepared(),{samples:30,gradientRelativeSd:0,temperatureSdK:0,processingRelativeSd:0,noiseRelativeSd:0});
  assert.equal(s.uncertainty.estimator.method,'mono');assert.equal(s.uncertainty.estimator.selectedEstimatorCovered,true);
});
check('recording-imported-calibration-defaults-does-not-establish-independent-evidence',()=>{
  const bs=Array.from({length:12},(_,i)=>4e9*i/11),areas=bs.map(b=>Math.exp(-b*8e-10));
  let s=J.attachExperimental(J.createCase(),{id:'calibration-evidence-fixture',bs,areas,source:'independent mathematical fixture',license:'synthetic test fixture'});
  s=J.calibrate(s,{});s=J.process(s);s=J.analyze(s);s=J.uncertainty(s,{samples:30,temperatureSdK:0});
  assert.equal(s.calibration.status,'independent-calibration-not-established');
  assert.ok(s.uncertainty.unquantifiedSources.some(x=>/absolute scale/.test(x)));
});
check('peak-selection-and-correlated-curves-use-minimum-b-not-acquisition-first-row',()=>{
  function ordered(order){let s=J.createCase({seed:6,preset:'isolated'});s=J.calibrate(s,{p90Us:J.revealCase(s).p90Us});s=J.design(s,{gradientMax:.8,deltaMs:2,bigDeltaMs:80,points:16,order});s=J.acquire(s,{noise:0});s=J.process(s,{lbHz:0});s=J.analyze(s);return J.uncertainty(s,{samples:30,gradientRelativeSd:0,temperatureSdK:0,processingRelativeSd:0,noiseRelativeSd:0});}
  const a=ordered('ascending'),b=ordered('descending');assert.ok(a.analysis.perPeak.length>0);
  assert.deepEqual(b.analysis.perPeak.map(x=>x.id),a.analysis.perPeak.map(x=>x.id));
  assert.equal(b.uncertainty.correlation.length,a.uncertainty.correlation.length);
});
const acqus={TD:64,SW_h:4000,SFO1:500,O1:2000,BYTORDA:0,DTYPA:0},buffer=new ArrayBuffer(256);
check('invalid-acquisition-carrier-is-rejected-before-axis-creation',()=>assert.throws(()=>P.readFID(buffer,{...acqus,O1:'bad'}),/O1|carrier|finite/i));
check('invalid-processed-offset-is-rejected-before-axis-creation',()=>assert.throws(()=>P.readProcessed(buffer,{SI:64,SF:500,SW_p:4000,OFFSET:'bad',BYTORDP:0,DTYPP:0,NC_proc:0}),/OFFSET|finite/i));
const fid={real:Array.from({length:64},(_,i)=>Math.cos(i)),imag:Array.from({length:64},(_,i)=>Math.sin(i)),dwell_s:1/4000,sfMHz:500,carrierPpm:4};
for(const p of ['phase0Deg','phase1Deg'])check('nonfinite-'+p+'-does-not-generate-a-NaN-spectrum',()=>assert.throws(()=>P.processFID(fid,{[p]:NaN}),/phase|finite/i));
check('nonfinite-carrier-is-not-silently-replaced-by-zero',()=>assert.throws(()=>P.processFID({...fid,carrierPpm:NaN}),/carrier|finite/i));
check('finite-extreme-phase-is-rejected-before-NaN-spectrum',()=>assert.throws(()=>P.processFID(fid,{phase0Deg:1e308}),/phase|finite|range/i));
check('finite-extreme-O1-to-SFO1-ratio-is-rejected-at-import',()=>assert.throws(()=>P.readFID(buffer,{...acqus,O1:1e308,SFO1:1e-308}),/carrier|finite|range/i));
check('finite-tiny-SF-cannot-generate-infinite-ppm-axis',()=>assert.throws(()=>P.processFID({...fid,sfMHz:1e-308}),/axis|finite|range/i));
check('finite-extreme-processed-metadata-cannot-generate-nonfinite-axis',()=>assert.throws(()=>P.readProcessed(buffer,{SI:64,SF:1e-308,SW_p:1e308,OFFSET:1e308,BYTORDP:0,DTYPP:0,NC_proc:0}),/axis|finite|range/i));
const report={passed:checks.every(x=>x.passed),checks,scope:'Independent signed-control, parameter-estimator and invalid-metadata contracts; mathematical/synthetic software evidence only.'};
const output=process.argv[2];if(output){fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');}
console.log(JSON.stringify({passed:report.passed,checks:checks.length,failures:checks.filter(x=>!x.passed)}));
process.exitCode=report.passed?0:1;
