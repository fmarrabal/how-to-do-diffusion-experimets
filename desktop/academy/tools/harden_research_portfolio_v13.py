from pathlib import Path
P=Path(__file__).resolve().parents[1]/'web/research-studio.js'


def main():
 s=P.read_text(encoding='utf-8')
 a=s.index('   try{const old=JSON.parse(localStorage.getItem(KEY)')
 b=s.index('   function stateBundle()',a)
 s=s[:a]+r'''   let storageWritable=true;
   function validatePortfolio(raw){
     const b=typeof raw==='string'?JSON.parse(raw):raw;
     if(!b||b.version!==VERSION||!b.case||!b.learning)throw Error('Research version or format mismatch');
     const next=J.validateImport(b.case),ls=L.importState(b.learning);
     if(ls.contentSha256!==learningScope)throw Error('Learning content identity differs');
     if(!Array.isArray(b.submissions)||b.submissions.length>20||!Array.isArray(b.reviews)||b.reviews.length>30)throw Error('Portfolio size or structure');
     b.submissions.forEach(v=>L.validateSubmission(v));
     const ids=new Set();for(const sub of b.submissions){if(ids.has(sub.id))throw Error('Duplicate submission');if(sub.parentId&&!ids.has(sub.parentId))throw Error('Missing parent submission');ids.add(sub.id);}
     const checkedReviews=b.reviews.map(r=>{const sub=b.submissions.find(s=>s.id===r.submissionId);if(!sub)throw Error('Review has no retained submission');return L.importReview(r,sub);});
     const safeDraft={};for(const key of Object.keys(draft)){const v=b.draft?.[key]??'';if(typeof v!=='string'||v.length>6000)throw Error('Invalid student note');safeDraft[key]=v;}
     const safePredictions={};for(const [id,value] of Object.entries(b.predictionsByStage||{})){if(!steps.some(s=>s[0]===id)||typeof value!=='string'||value.length>4000)throw Error('Invalid stage prediction');safePredictions[id]=value;}
     if(b.prediction!=null&&(typeof b.prediction!=='string'||b.prediction.length>4000))throw Error('Invalid prediction');
     return{case:next,learning:ls,submissions:clone(b.submissions),reviews:checkedReviews,draft:safeDraft,prediction:b.prediction||'',predictionsByStage:safePredictions};
   }
   let previousRaw=null;
   try{previousRaw=localStorage.getItem(KEY);if(previousRaw){const old=validatePortfolio(previousRaw);caseState=old.case;learning=old.learning;submissions=old.submissions;reviews=old.reviews;draft=old.draft;prediction=old.prediction;predictionsByStage=old.predictionsByStage;}}
   catch(e){if(previousRaw){try{localStorage.setItem(KEY+'.preserved.'+Date.now(),previousRaw);message=t('La copia anterior no es compatible: se ha conservado una copia local antes de iniciar otra sesión.','Previous content is incompatible: a local copy was preserved before starting another session.');}catch{storageWritable=false;message=t('La copia anterior no es legible y no hay espacio para respaldarla. Guardado automático bloqueado; exporta tu nueva sesión antes de cerrar.','Previous content is unreadable and cannot be backed up. Automatic saving is blocked; export your new session before closing.');}}else{storageWritable=false;message=t('Almacenamiento local no disponible; utiliza exportación.','Local storage unavailable; use export.');}}
'''+s[b:]
 old="function save(){try{const data="
 new="function save(){if(!storageWritable){message=t('Guardado automático bloqueado para conservar el archivo anterior. Exporta tu trabajo.','Automatic saving blocked to preserve previous content. Export your work.');return;}try{const data="
 if old not in s:raise ValueError('save anchor')
 s=s.replace(old,new,1)
 a=s.index("const b=JSON.parse(raw);if(b.version!==VERSION)")
 b=s.index("message=t('Investigación importada.",a)
 s=s[:a]+"const loaded=validatePortfolio(raw);caseState=loaded.case;learning=loaded.learning;submissions=loaded.submissions;reviews=loaded.reviews;draft=loaded.draft;prediction=loaded.prediction;predictionsByStage=loaded.predictionsByStage;save();"+s[b:]
 # Preserve the scientific source identity in the parent shell; do not bind
 # student progress to a fabricated checksum.
 P.write_text(s,encoding='utf-8')
 a=P.parent/'academy.js';t=a.read_text(encoding='utf-8');t=t.replace("mount($('view'),language,{embedded,onView:id=>", "mount($('view'),language,{embedded,contentSha256:bundle.researchContentSha256,onView:id=>",1);a.write_text(t,encoding='utf-8')
 print('Portfolio imports, parent references and previous local data protected')


if __name__=='__main__':main()
