import {createRequire} from 'node:module';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
const require=createRequire(import.meta.url),{chromium}=require('playwright');
const root=path.resolve(import.meta.dirname,'../../../..'),out=process.env.ACADEMY_FEEDBACK_QA_OUT||path.join(root,'desktop/academy/qa/research-1.3/ui-feedback-correction-r1/run-r4');
const origin=process.env.ACADEMY_QA_ORIGIN||'http://127.0.0.1:8044';
if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(origin))throw Error('QA origin must be loopback HTTP');
const sourcePath=path.join(root,'desktop/academy/web/research-studio.js'),source=await fs.readFile(sourcePath,'utf8');
const hash=value=>crypto.createHash('sha256').update(value).digest('hex');
await fs.mkdir(out,{recursive:true});
const reportPath=path.join(out,'feedback-browser-report.json');
try{await fs.access(reportPath);throw Error('Preserve existing QA report; select a fresh evidence directory');}catch(e){if(e.code!=='ENOENT')throw e;}
const fixturePrefix=`;(function(){
 const journey=window.AcademyResearchJourney,learning=window.AcademyLearningPath;
 window.AcademyResearchJourney={...journey,
   analyze(...args){const s=journey.analyze(...args);if(window.feedbackForceNonConvergence&&s.analysis.distribution){s.analysis.distribution.converged=false;s.analysis.distribution.projectedGradient=1;s.analysis.distribution.kktTolerance=1e-7;}return s;},
   proposeMeasurement(...args){const s=journey.proposeMeasurement(...args);if(window.feedbackForceNoCompatible){s.measurement.distributions.forEach(v=>{v.compatibleWithObservedAtDeclaredNoise=false;});s.measurement.distributions[0].residualRms=.123456;}return s;}
 };
 window.AcademyLearningPath={...learning,makeDiagnostic(...args){const f=learning.makeDiagnostic(...args);window.feedbackForm=structuredClone(f);return f;}};
})();\n`;
const browser=await chromium.launch({headless:true,channel:'msedge'}),page=await browser.newPage({viewport:{width:1500,height:1000}}),checks=[],errors=[],methodResults=[];
const check=(name,passed,detail)=>{checks.push({name,passed:!!passed,...detail===undefined?{}:{detail}});if(!passed)console.log('FAIL '+name+' '+JSON.stringify(detail));};
page.on('pageerror',e=>errors.push(String(e)));
await page.route('**/research-studio.js',route=>route.fulfill({status:200,contentType:'text/javascript',body:fixturePrefix+source}));
async function stage(id){await page.locator('[data-step="'+id+'"]').click();await page.waitForFunction(id=>AcademyWeb.snapshot().research.view===id,id);}
async function field(name,value){await page.locator('[data-field="'+name+'"]').fill(String(value));}
async function action(name){await page.locator('[data-action="'+name+'"]').click();await page.waitForTimeout(80);const status=page.locator('.rs-status[data-error]');check('action '+name,(await status.getAttribute('data-error'))!=='true',await status.innerText());}
const evidence=()=>page.evaluate(()=>AcademyWeb.researchEvidence().case.caseState);
try{
 await page.goto(origin+'/index.html?view=research&lang=en',{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.AcademyWeb?.snapshot().research?.ready,{timeout:30000});
 await page.locator('[data-field=preset]').selectOption('combined');await field('seed',20261030);await action('new-case');
 const cal=await page.evaluate(()=>{const s=AcademyResearchJourney.validateImport(AcademyWeb.researchEvidence().case),p=s.pilots,f=AcademyDoctoralInquiry.fitMono(p.referenceCurve.map(v=>v.bNominal),p.referenceCurve.map(v=>v.signal));return{p90:p.firstNullUs/2,scale:Math.sqrt(f.D/p.referenceD)};});
 await stage('calibration');await field('p90Us',cal.p90);await field('gradientScale',cal.scale);await action('calibrate');
 await stage('design');await action('design');await stage('acquire');await action('acquire');await stage('process');await action('process');await stage('inference');
 for(const method of ['mono','nnls','tikhonov','l1']){
   await page.locator('[data-field=method]').selectOption(method);await field('regularization',.001);await action('analyze');
   const a=(await evidence()).analysis,f=a.distribution||a.mono,status=await page.locator('[data-fit-convergence]').getAttribute('data-converged');
   methodResults.push({method,converged:f.converged??null,iterations:f.iterations??null,projectedGradient:f.projectedGradient??null,residualRms:a.residualRms});
   check('actual fit method '+method,a.method===method&&Number.isFinite(a.residualRms));
   check('engine convergence rendered '+method,status===(typeof f.converged==='boolean'?String(f.converged):'unreported'));
   check('nonconvergence warning follows engine '+method,(await page.locator('[data-fit-warning]').count())===(f.converged===false?1:0));
   if(method!=='mono')check('KKT and iterations visible '+method,(await page.locator('[data-fit-convergence]').innerText()).includes('KKT:')&&(await page.locator('[data-fit-convergence]').innerText()).includes('Iterations:'));
 }
 await page.evaluate(()=>window.feedbackForceNonConvergence=true);await page.locator('[data-field=method]').selectOption('nnls');await action('analyze');
 check('controlled failed solver is visibly provisional',await page.locator('[data-fit-warning]').innerText().then(v=>v.includes('provisional')&&v.includes('did not reach')));
 await page.locator('[data-fit-warning]').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,'fit-warning-en.png'),fullPage:false});
 await page.evaluate(()=>window.feedbackForceNonConvergence=false);await page.locator('[data-field=method]').selectOption('mono');await action('analyze');
 await stage('next');await action('plan-next');
 const current=(await evidence()).measurement.distributions;
 check('current-data model rows and RMS visible',await page.locator('[data-current-model-compatibility] tbody tr').count()===current.length&&(await page.locator('[data-current-model-compatibility]').innerText()).includes('Current RMS'));
 check('future discrimination has its own section',await page.locator('[data-future-model-separation]').count()===1&&(await page.locator('[data-future-model-separation]').innerText()).includes('Predicted separation / noise'));
 check('current compatibility matches engine flags',await page.locator('[data-current-model-compatibility] tbody tr').evaluateAll((rows,models)=>rows.every((r,i)=>r.cells[2].textContent.trim()===(models[i].compatibleWithObservedAtDeclaredNoise===true?'Yes, under the declared criterion':models[i].compatibleWithObservedAtDeclaredNoise===false?'No':'Not reported')),current));
 await page.evaluate(()=>window.feedbackForceNoCompatible=true);await action('plan-next');
 check('controlled no-compatible-model warning',await page.locator('[data-model-compatibility-warning]').innerText().then(v=>v.includes('None of the proposed models')));
 const rmsLabel=await page.evaluate(()=>(.123456).toLocaleString(undefined,{maximumFractionDigits:5}));
 check('current RMS is not future separation',await page.locator('[data-current-model-compatibility]').innerText().then(v=>v.includes(rmsLabel))&&!(await page.locator('[data-future-model-separation]').innerText()).includes(rmsLabel));
 await page.locator('[data-model-compatibility-warning]').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,'compatibility-warning-en.png'),fullPage:false});
 await page.evaluate(()=>window.feedbackForceNoCompatible=false);await field('prediction','The held-out observation may challenge the proposed free-diffusion distributions and expose a missing effect.');await action('observe-next');
 check('array-shaped held-out observations are drawn',await page.locator('.rs-main .rs-plot path[stroke-width="2"]').count()===(await evidence()).measurement.selected.predictions.length+1);
 await stage('competencies');await action('pretest');
 const form=await page.evaluate(()=>window.feedbackForm),answers={};
 for(const q of form.questions){const value=q.type==='choice'?(q.expected+1)%q.choices.length:q.expected*1.2+1;answers[q.id]=String(value);const el=page.locator('[data-answer="'+q.id+'"]');if(q.type==='choice')await el.selectOption(String(value));else await el.fill(String(value));}
 await action('grade-diagnostic');
 check('submitted controls retain every answer',await page.locator('[data-answer]').evaluateAll((els,answers)=>els.every(e=>e.value===answers[e.dataset.answer]),answers));
 for(const q of form.questions.filter(q=>q.type==='choice')){
   const review=page.locator('[data-diagnostic-review="'+q.id+'"]');
   check('choice reference is text '+q.competencyId,(await review.locator('[data-expected-answer]').innerText())==='Correct choice: '+q.choices[q.expected].en);
   check('submitted choice text visible '+q.competencyId,(await review.locator('[data-given-answer]').innerText())==='Your answer: '+q.choices[Number(answers[q.id])].en);
 }
 await page.evaluate(()=>AcademyWeb.setLanguage('es'));
 check('completed status is localized after switching to Spanish',(await page.locator('.rs-status[data-error]').innerText()).startsWith('Tu trabajo'));
 check('answers survive language render',await page.locator('[data-answer]').evaluateAll((els,answers)=>els.every(e=>e.value===answers[e.dataset.answer]),answers));
 for(const q of form.questions.filter(q=>q.type==='choice'))check('choice reference localized '+q.competencyId,(await page.locator('[data-diagnostic-review="'+q.id+'"] [data-expected-answer]').innerText())==='Opción correcta: '+q.choices[q.expected].es);
 await stage('brief');await stage('competencies');check('answers survive stage navigation',await page.locator('[data-answer]').evaluateAll((els,answers)=>els.every(e=>e.value===answers[e.dataset.answer]),answers));
 const choice=form.questions.find(q=>q.type==='choice');await page.locator('[data-answer="'+choice.id+'"]').selectOption(String(choice.expected));await page.evaluate(()=>AcademyWeb.setLanguage('en'));
 check('completed status is localized after switching to English',(await page.locator('.rs-status[data-error]').innerText()).startsWith('Your work'));
 check('feedback keeps the evaluated answer after draft edits',(await page.locator('[data-diagnostic-review="'+choice.id+'"] [data-given-answer]').innerText())==='Your answer: '+choice.choices[Number(answers[choice.id])].en);
 await page.locator('[data-diagnostic-feedback]').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,'diagnostic-feedback-en.png'),fullPage:false});
 await action('practice');check('new form clears old draft and feedback',await page.locator('[data-diagnostic-feedback]').count()===0&&await page.locator('[data-answer]').evaluateAll(els=>els.every(e=>e.value==='')));
 check('no JavaScript exceptions',errors.length===0,errors);
}catch(e){checks.push({name:'feedback workflow completion',passed:false,detail:String(e.stack||e)});await page.screenshot({path:path.join(out,'feedback-failure.png'),fullPage:false});}
finally{
 await browser.close();const report={passed:checks.every(c=>c.passed),failed:checks.filter(c=>!c.passed).length,checks,errors,methodResults,sourceSha256:hash(source),sources:[{path:'web/research-studio.js',sha256:hash(source)}],fixture:{prefixSha256:hash(fixturePrefix),scope:'Controlled copies of engine return values exercise failed-convergence and none-compatible rendering; the four method fits otherwise use the unchanged real teaching engines.'},scope:'Browser software/UI checks only. No scientific, instrument, model quality or educational efficacy validation.'};
 await fs.writeFile(reportPath,JSON.stringify(report,null,2),{flag:'wx'});console.log(JSON.stringify({passed:report.passed,checks:checks.length,failed:report.failed,methodResults,errors}));process.exitCode=report.passed?0:1;
}
