"""Apply bounded shell integration; original frozen course stays untouched."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
p = ROOT / 'web/academy.js'
s = p.read_text('utf-8-sig')
def replace(old, new):
    global s
    if s.count(old) != 1: raise ValueError('Unexpected shell source: '+old[:70])
    s = s.replace(old,new)
replace('mathRevision=0;', 'mathRevision=0,doctoralController=null,doctoralCases=null;')
replace("tabs=[['lesson'", "tabs=[['doctoral','Doctorado','Doctoral'],['lesson'")
replace("function header(){const m=module();", "function header(){const m=module();")
replace("text('evidence','SIMULACIÓN EDUCATIVA','EDUCATIONAL SIMULATION');", "if(view==='doctoral'){$('chapter').textContent=l('Recorrido doctoral · 1.2','Doctoral pathway · 1.2');$('title').textContent=l('Del fenómeno a la evidencia','From phenomenon to evidence');$('objective').textContent=l('Predice, diseña una comprobación y defiende una conclusión.','Predict, design a check and defend a conclusion.');}text('evidence',view==='doctoral'?'CASOS Y MODELOS IDENTIFICADOS':'SIMULACIÓN EDUCATIVA',view==='doctoral'?'LABELLED CASES AND MODELS':'EDUCATIONAL SIMULATION');")
replace("function render(){navigation();header();$('module-actions').style.display=view==='derivations'?'none':'';", "function doctoralView(){doctoralController=window.AcademyDoctoralHub.mount($('view'),language,{derivations,cases:doctoralCases,contentSha256:bundle.derivationsSha256,embedded,initialView:query.get('doctoral')||'home',onView:id=>{const u=new URL(location.href);u.searchParams.set('doctoral',id);history.replaceState(null,'',u);}});} function setLanguage(lang){if(!['es','en'].includes(lang))throw new RangeError('ES/EN');rememberLab();language=lang;if(view==='doctoral'&&doctoralController){navigation();header();doctoralController.setLanguage(lang);const u=new URL(location.href);u.searchParams.set('lang',lang);history.replaceState(null,'',u);}else render();} function render(){doctoralController?.destroy();doctoralController=null;navigation();header();$('module-actions').style.display=['derivations','doctoral'].includes(view)?'none':'';")
replace("({lesson,laboratory: laboratory", "({doctoral:doctoralView,lesson,laboratory: laboratory")
replace("view='lab';render();}", "view='lab';render();}")
replace("$('language').onclick=()=>{rememberLab();language=language==='es'?'en':'es';render();};", "$('language').onclick=()=>setLanguage(language==='es'?'en':'es');")
replace("try{derivations=await jsonFetch('content/derivations.json');}catch(err){console.warn(err);}", "try{derivations=await jsonFetch('content/derivations.json');}catch(err){console.warn(err);}try{doctoralCases=await jsonFetch('content/doctoral-cases.json');}catch(err){console.warn('Doctoral real-case catalogue unavailable',err);}")
replace("setLanguage:lang=>{if(!['es','en'].includes(lang))throw new RangeError('ES/EN');rememberLab();language=lang;render();}", "setLanguage")
replace("snapshot:()=>({ready:!!course&&!mathPending,", "selectDoctoralView:id=>{if(view!=='doctoral'){view='doctoral';render();}doctoralController.selectView(id);},doctoralEvidence:()=>doctoralController?.getEvidence()||null,snapshot:()=>({ready:!!course&&!mathPending,doctoral:doctoralController?.snapshot()||null,")
replace("?'/downloads/diffatonce-academy-1.1.0-win-x64'", "?'/downloads/diffatonce-academy-1.1.0-win-x64'") if "?'/downloads/diffatonce-academy-1.1.0-win-x64'" in s else None
s=s.replace('/downloads/diffatonce-academy-1.1.0-win-x64','/downloads/diffatonce-academy-1.2.0-win-x64')
p.write_text(s,'utf-8')
print('Academy shell integrated; frozen course and mathematical corpus unchanged.')
