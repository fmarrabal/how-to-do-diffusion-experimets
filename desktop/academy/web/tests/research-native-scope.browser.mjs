import {createRequire} from 'node:module';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
const require=createRequire(import.meta.url),{chromium}=require('playwright');
const root=path.resolve(import.meta.dirname,'../../../..'),out=path.join(root,'desktop/academy/qa/research-1.3/native-scope-ui');
const origin=process.env.ACADEMY_QA_ORIGIN||'http://127.0.0.1:8044';
if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(origin))throw Error('QA server must be loopback HTTP');
await fs.mkdir(out,{recursive:true});
const browser=await chromium.launch({headless:true,channel:'msedge'}),page=await browser.newPage({viewport:{width:1500,height:1000}}),checks=[],errors=[];
page.on('pageerror',e=>errors.push(String(e)));
const check=(name,passed,detail)=>{checks.push({name,passed:!!passed,...detail===undefined?{}:{detail}});if(!passed)console.log('FAIL '+name+' '+JSON.stringify(detail));};
const snap=()=>page.evaluate(()=>window.AcademyWeb.snapshot().research);
const caseHash=()=>page.evaluate(()=>AcademyLearningPath.sha256(AcademyWeb.researchEvidence().case));
const packet=()=>page.evaluate(()=>window.nativePackets.filter(p=>p.type==='research-tutor').at(-1));
async function stage(id){await page.locator('[data-step="'+id+'"]').click();}
async function ask(){const pred=page.locator('[data-field="prediction"]');if(await pred.count())await pred.fill('I predict a model-conditional result and require an independent control before interpreting D.');await page.locator('[data-field="question"]').fill('Why does the current case need an independent calibration control?');await page.locator('[data-action="native-tutor"]').click();await page.waitForFunction(()=>AcademyWeb.snapshot().research.nativeTutor.pending);return packet();}
function response(p,extra={}){return{requestId:p.requestId,scopeHash:p.scopeHash,scope:p.scope,label:'QA controlled documentary reply',text:'This is a controlled fake-native QA reply, not actual model inference.',sources:[{Id:'torrey-fixture',Title:'Torrey source fixture',Doi:'10.1103/PhysRev.104.563'}],isModelAnswer:false,status:'answer',...extra};}
const receive=answer=>page.evaluate(a=>AcademyWeb.receiveResearchTutor(a),answer);
try{
 await page.addInitScript(()=>{window.nativePackets=[];window.chrome=window.chrome||{};window.chrome.webview={postMessage:value=>window.nativePackets.push(structuredClone(value))};});
 await page.goto(origin+'/index.html?view=research&lang=es&embedded=1',{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.AcademyWeb?.snapshot().research?.ready,{timeout:30000});
 const baseline=await caseHash(),p1=await ask();
 check('unique-bounded-request-id',typeof p1.requestId==='string'&&p1.requestId.length>=8&&p1.requestId.length<=100);
 check('scope-hash-is-exact-SHA256',await page.evaluate(p=>AcademyLearningPath.sha256(p.scope)===p.scopeHash,p1));
 check('scope-binds-visible-case-stage-and-parameters',p1.scope.caseId===(await snap()).caseId&&p1.scope.stage==='brief'&&p1.scope.parameters!==undefined&&'analysisD'in p1.scope&&'residual'in p1.scope);
 check('pending-disables-only-local-model-button',await page.locator('[data-action="native-tutor"]').isDisabled()&&await page.locator('[data-action="hint"]').isEnabled()&&await page.locator('[data-step="design"]').isEnabled());
 check('pending-does-not-claim-model-inference',(await snap()).beatrixMode==='native-request-pending');
 check('bound-case-and-short-hash-are-visible',(await page.locator('[data-native-scope]').innerText()).includes(p1.scopeHash.slice(0,12)));
 check('matching-documentary-reply-is-accepted',await receive(response(p1))===true);
 check('PascalCase-native-sources-normalize-with-working-DOI-link',await page.locator('[data-tutor-answer] a[href="https://doi.org/10.1103/PhysRev.104.563"]').count()===1&&(await snap()).nativeTutor.sourcesCount===1);
 check('documentary-mode-reflects-actual-flag',(await snap()).beatrixMode==='reviewed-source-guidance');
 check('reply-does-not-change-scientific-case',await caseHash()===baseline);
 const p2=await ask();check('second-request-has-a-new-id',p2.requestId!==p1.requestId);
 check('older-id-is-rejected-without-clearing-new-pending',await receive(response(p1,{text:'STALE_REPLY_MUST_NOT_APPEAR'}))===false&&(await snap()).nativeTutor.requestId===p2.requestId);
 check('rejected-text-is-not-rendered',!(await page.locator('[data-tutor-answer]').innerText()).includes('STALE_REPLY_MUST_NOT_APPEAR'));
 check('matching-model-flag-is-preserved',await receive(response(p2,{isModelAnswer:true,label:'QA fake-native model flag'}))===true&&(await snap()).beatrixMode==='local-model-with-reviewed-evidence');
 check('model-mode-eyebrow-is-explicit',(await page.locator('.rs-context').innerText()).includes('LLM LOCAL + FUENTES REVISADAS'));
 const p3=await ask();await stage('calibration');
 check('stage-change-invalidates-pending',!(await snap()).nativeTutor.pending);
 check('stage-change-sends-matching-native-cancel',await page.evaluate(p=>nativePackets.some(v=>v.type==='research-tutor-cancel'&&v.requestId===p.requestId&&v.scopeHash===p.scopeHash),p3));
 check('late-stage-reply-is-rejected',await receive(response(p3))===false);
 const p4=await ask();await page.locator('[data-action="calibrate"]').click();
 check('same-case-calculation-invalidates-request',!(await snap()).nativeTutor.pending&&(await snap()).nativeTutor.revision>p4.scope.revision);
 const calibrated=await caseHash();check('late-calculation-reply-never-modifies-data',await receive(response(p4,{text:'Wrong old calibration response'}))===false&&await caseHash()===calibrated);
 const p5=await ask();await page.locator('[data-action="calibrate"]').click();
 check('identical-numeric-recalculation-still-changes-revision',(await snap()).nativeTutor.revision>p5.scope.revision&&!((await snap()).nativeTutor.pending));
 for(const status of ['cancelled','error','busy']){
   const p=await ask(),before=await caseHash();await receive(response(p,{status,isModelAnswer:false}));
   check(status+'-clears-pending-and-reenables-model',!(await snap()).nativeTutor.pending&&await page.locator('[data-action="native-tutor"]').isEnabled());
   check(status+'-does-not-change-results',await caseHash()===before);
 }
 const wrong=await ask();check('wrong-scope-is-rejected-and-pending-cleared',await receive(response(wrong,{scopeHash:'0'.repeat(64)}))===false&&!(await snap()).nativeTutor.pending);
 const translated=await ask();await page.evaluate(()=>AcademyWeb.setLanguage('en'));await receive(response(translated));
 check('language-change-discards-old-response-in-current-language',!(await snap()).nativeTutor.pending&&(await page.locator('[data-native-status]').innerText()).includes('discarded'));
 const edited=await ask();await page.locator('[data-field="question"]').fill('A different question written while the earlier request was running.');
 check('changed-question-invalidates-the-earlier-scope-at-receive',await receive(response(edited))===false&&!(await snap()).nativeTutor.pending);
 await stage('brief');const oldCase=await ask(),oldId=(await snap()).caseId;await page.locator('[data-field="seed"]').fill('123456');await page.locator('[data-action="new-case"]').click();
 check('new-sample-discards-in-flight-response',(await snap()).caseId!==oldId&&await receive(response(oldCase))===false);
 const current=await ask();check('current-error-does-not-fake-a-model-answer',await receive(response(current,{status:'error',isModelAnswer:true}))===false&&(await snap()).beatrixMode==='reviewed-source-guidance');
 const closing=await ask();await page.evaluate(()=>AcademyWeb.selectView('lesson'));
 check('destroy-sends-cancel-without-retaining-a-pending-controller',await page.evaluate(p=>nativePackets.some(v=>v.type==='research-tutor-cancel'&&v.requestId===p.requestId),closing));
 await page.evaluate(()=>AcademyWeb.selectView('research'));await page.waitForFunction(()=>AcademyWeb.snapshot().research.ready);const reopened=await ask();
 check('new-controller-session-cannot-accept-old-replies',reopened.requestId!==closing.requestId&&await receive(response(closing))===false&&(await snap()).nativeTutor.requestId===reopened.requestId);
 await receive(response(reopened));await page.screenshot({path:path.join(out,'native-scope-controlled-qa-en.png'),fullPage:true});
 check('no-browser-JavaScript-errors',errors.length===0,errors);
 const cs=await fs.readFile(path.join(root,'desktop/academy/src/DiffAtOnce.Academy.App/ResearchWindow.cs'),'utf8');
 check('CSharp-response-source-contract-echoes-IDs-and-normalized-sources',cs.includes('requestId, scopeHash, scope')&&cs.includes('id = source.Id, title = source.Title, doi = source.Doi')&&cs.includes('isModelAnswer'));
 check('CSharp-retains-origin-and-size-gates',cs.includes('!Local(e.Source)')&&cs.includes('e.WebMessageAsJson.Length > 64000'));
}catch(e){check('fake-native-browser-harness-completion',false,{error:String(e.stack||e),diagnostic:await page.evaluate(()=>({snapshot:window.AcademyWeb?.snapshot(),ready:document.readyState,body:document.body.innerText.slice(0,2200)}))});}
await browser.close();
const sourcePaths=['desktop/academy/web/research-studio.js','desktop/academy/src/DiffAtOnce.Academy.App/ResearchWindow.cs'],sources=[];
for(const p of sourcePaths)sources.push({path:p.replace('desktop/academy/',''),sha256:crypto.createHash('sha256').update(await fs.readFile(path.join(root,p))).digest('hex')});
const report={version:'1.3.0',passed:checks.every(c=>c.passed),checks,errors,sources,scope:'Controlled fake-native browser bridge verifies request identity, current-context binding, source normalization, cancellation/error cleanup and scientific-state preservation. It is NOT actual model inference, native WPF execution or CSharp compilation; source contracts were inspected and final native build remains required.'};
await fs.writeFile(path.join(out,'browser-qa.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({passed:report.passed,checks:checks.length,failures:checks.filter(c=>!c.passed),out}));if(!report.passed)process.exitCode=1;
