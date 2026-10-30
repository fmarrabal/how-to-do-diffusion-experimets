import {createRequire} from 'node:module';
import fs from 'node:fs/promises';
import path from 'node:path';
const require=createRequire(import.meta.url),{chromium}=require('playwright');
const out=path.resolve(import.meta.dirname,'../../qa/research-1.3/legacy-regression');await fs.mkdir(out,{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage(),errors=[],checks=[];
page.on('pageerror',e=>errors.push(String(e)));
try{
 await page.goto((process.env.ACADEMY_QA_ORIGIN||'http://127.0.0.1:8044')+'/index.html?view=derivations&embedded=1&lang=es',{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.AcademyWeb?.snapshot().ready,{timeout:35000});
 const first=await page.evaluate(()=>window.AcademyWeb.snapshot());checks.push({name:'legacy mathematical reader',passed:first.equationsRendered>0,state:first});
 await page.screenshot({path:path.join(out,'derivations-es.png'),fullPage:false});
 await page.evaluate(()=>window.AcademyWeb.setLanguage('en'));await page.waitForFunction(()=>window.AcademyWeb.snapshot().ready);
 checks.push({name:'mathematical reader English',passed:await page.evaluate(()=>window.AcademyWeb.snapshot().language==='en'&&window.AcademyWeb.snapshot().equationsRendered>0)});
 await page.evaluate(()=>window.AcademyWeb.selectDoctoralView('cases'));await page.waitForFunction(()=>window.AcademyWeb.snapshot().doctoral?.view==='cases');checks.push({name:'legacy doctoral retained',passed:true});
}catch(e){checks.push({name:'legacy regression completion',passed:false,error:String(e),state:await page.evaluate(()=>({snapshot:window.AcademyWeb?.snapshot(),mathjax:typeof window.MathJax?.typesetPromise,body:document.body.innerText.slice(-600)}))});}
finally{checks.push({name:'no JS exceptions',passed:!errors.length,errors});await fs.writeFile(path.join(out,'regression.json'),JSON.stringify({checks,passed:checks.filter(c=>c.passed).length,failed:checks.filter(c=>!c.passed).length},null,2));console.log(JSON.stringify(checks));await browser.close();process.exitCode=checks.some(c=>!c.passed)?1:0;}
