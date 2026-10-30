(function(){
  'use strict';
  let last='',moduleId=null,revision=0;
  function context(){
    const s=window.DiffusionMotion?.getState(); if(!s)return null;
    let diagnostic=null;
    try{diagnostic=window.QuantitativeScenes?.diagnostics(s.scene,s.params);}catch(_){ }
    // Only bounded parameters and textual metrics, never the full acquisition matrix.
    return {evidenceStatus:'synthetic-teaching-simulation',moduleId,revision,scene:s.scene,language:s.lang,parameters:s.params,diagnostics:diagnostic?{metrics:diagnostic.metrics,notes:diagnostic.notes}:null};
  }
  function report(){const c=context();if(!c)return;let text=JSON.stringify(c);if(text.length>9000){c.diagnostics=null;text=JSON.stringify(c);}if(text!==last&&window.chrome?.webview){last=text;window.chrome.webview.postMessage({type:'academy-context',context:c});}}
  function apply(input){
    const known=window.DiffusionMotion?.listScenes().some(s=>s.id===input?.scene);
    if(!known)return {ok:false,rejected:['scene']};
    try{window.DiffusionMotion.setScene(input.scene,input.lang==='en'?'en':'es');}catch(error){return{ok:false,rejected:['scene-change'],error:String(error.message)}}
    moduleId=input.moduleId||null;revision=Number.isInteger(input.revision)?input.revision:0;
    const rejected=[];const applied={};
    if(input.preset){const buttons=[...document.querySelectorAll('#scenario-presets button')];const b=buttons.find(b=>b.dataset.preset===input.preset||b.textContent.trim()===input.preset);if(b)b.click();else rejected.push('preset:'+input.preset);}
    for(const [key,value] of Object.entries(input.parameters||{})){
      const control=document.getElementById('param-'+key);
      if(!control||control.tagName!=='INPUT'||!Number.isFinite(value)){rejected.push(key);continue;}
      const lo=Number(control.min),hi=Number(control.max);
      if(value<lo||value>hi){rejected.push(key);continue;}
      control.value=String(value);control.dispatchEvent(new Event('input',{bubbles:true}));applied[key]=Number(control.value);
    }
    window.DiffusionMotion.setTime(0);report();
    return {ok:true,scene:input.scene,applied,rejected};
  }
  window.AcademyBridge={apply,context,version:'1.0'};
  setInterval(report,750);report();
})();
