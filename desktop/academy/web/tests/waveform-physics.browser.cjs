'use strict';
// Isolated browser checks of the real waveform component, not instrument QA.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {chromium}=require(process.env.ACADEMY_PLAYWRIGHT_MODULE||'playwright');
const option=(name,fallback)=>{const i=process.argv.indexOf(name);return i>=0?process.argv[i+1]:fallback;};
const source=path.resolve(option('--source',path.join(__dirname,'../waveform-lab.js'))),out=option('--report',null),checks=[];
function check(name,value,evidence){checks.push({name,passed:!!value,evidence});}
(async()=>{const browser=await chromium.launch({channel:'msedge',headless:true});try{
 for(const lang of ['es','en']){const page=await browser.newPage({viewport:{width:1200,height:900}});const errors=[];page.on('pageerror',e=>errors.push(String(e)));
  await page.setContent('<!doctype html><html><body><div id="waveform"></div></body></html>');await page.addScriptTag({path:source});await page.evaluate(l=>AcademyWaveformLab.mount(document.getElementById('waveform'),l),lang);
  check(lang+'-default-ready',await page.locator('#waveform').getAttribute('data-aw-ready')==='true');
  for(const shape of ['rect','sine','sine2','triangle']){await page.locator('[data-aw=shape]').selectOption(shape);await page.locator('[data-aw=shape]').dispatchEvent('input');const r=await page.evaluate(()=>AcademyWaveformLab.snapshot());check(lang+'-'+shape+'-analytic-quadrature',r&&Number.isFinite(r.bSecondsPerM2)&&Math.abs(r.bSecondsPerM2/r.quadratureBSecondsPerM2-1)<1e-9);}
  await page.locator('[data-aw=D]').fill('0');let message=await page.locator('[data-aw=error]').innerText();check(lang+'-invalid-D-has-local-parameter-error',message===(lang==='es'?'Parámetro fuera del intervalo didáctico: D.':'Parameter outside the teaching range: D.'),{message});
  check(lang+'-invalid-state-clears-result',await page.evaluate(()=>AcademyWaveformLab.snapshot()===null&&document.querySelector('[data-aw=metrics]').childElementCount===0&&document.querySelector('[data-aw=wave]').childElementCount===0));
  await page.locator('[data-aw=D]').fill('1');await page.locator('[data-aw=g]').fill('');message=await page.locator('[data-aw=error]').innerText();check(lang+'-empty-gradient-not-silently-zero',message===(lang==='es'?'Introduce un número para g.':'Enter a number for g.')&&await page.locator('#waveform').getAttribute('data-aw-ready')==='false',{message});
  await page.locator('[data-aw=g]').fill('0.3');await page.locator('[data-aw=Delta]').fill('1');message=await page.locator('[data-aw=error]').innerText();check(lang+'-overlapping-lobes-correct-local-error',message===(lang==='es'?'Δ debe ser mayor o igual que δ.':'Δ must be greater than or equal to δ.'),{message});
  await page.locator('[data-aw=Delta]').fill('80');await page.locator('[data-aw=v]').fill('11');message=await page.locator('[data-aw=error]').innerText();check(lang+'-invalid-velocity-correct-local-error',message===(lang==='es'?'Parámetro fuera del intervalo didáctico: velocidad máxima.':'Parameter outside the teaching range: maximum velocity.'),{message});
  await page.locator('[data-aw=v]').fill('0');check(lang+'-valid-after-error-recovers',await page.locator('#waveform').getAttribute('data-aw-ready')==='true'&&await page.locator('[data-aw=error]').innerText()==='');check(lang+'-no-script-errors',errors.length===0,errors);await page.close();
 }
}finally{await browser.close();}
const report={passed:checks.every(c=>c.passed),checks,sourceSha256:crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex'),scope:'Real Edge DOM controls, calculated four-shape output, localized input failures and recovery in ES/EN. Isolated component QA; no WPF host, hardware or experimental validation.'};if(out){fs.mkdirSync(path.dirname(path.resolve(out)),{recursive:true});fs.writeFileSync(out,JSON.stringify(report,null,2));}console.log(JSON.stringify({passed:report.passed,checks:checks.length,failures:checks.filter(c=>!c.passed)}));process.exitCode=report.passed?0:1;
})().catch(e=>{console.error(e);process.exitCode=1;});
