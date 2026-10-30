/* Academy 1.3: local, transparent learning evidence. A completed screen is not
   mastery; objective checks are not a semantic grade or a teacher signature. */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.AcademyLearningPath = api;
})(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';
  const VERSION = '1.3.0', SCHEMA = 'academy-learning-path/1', DAY = 86400000;
  const MAX_BYTES = 4000000, MAX_ATTEMPTS = 2000;
  const bilingual = (es, en) => ({ es, en });
  const competencies = [
    ['physics', 'Movimiento, fase y eco', 'Motion, phase and echo'],
    ['units', 'Unidades y escalado', 'Units and scaling'],
    ['calibration', 'Calibración e incertidumbre', 'Calibration and uncertainty'],
    ['sequences', 'Secuencia y gradiente efectivo', 'Sequence and effective gradient'],
    ['processing', 'Procesado reproducible', 'Reproducible processing'],
    ['ilt', 'Inversión e identificabilidad', 'Inversion and identifiability'],
    ['evidence', 'Controles y conclusión defendible', 'Controls and defensible conclusion']
  ].map(([id, es, en]) => ({ id, title: bilingual(es, en) }));
  const rubricCriteria = [
    ['physics', 'Física y ecuación apropiada', 'Physics and appropriate equation'],
    ['experimental-design', 'Diseño y controles discriminantes', 'Design and discriminating controls'],
    ['processing-reproducibility', 'Procedencia y procesado reproducible', 'Provenance and reproducible processing'],
    ['uncertainty', 'Incertidumbre y estabilidad', 'Uncertainty and stability'],
    ['defensible-conclusion', 'Conclusión proporcionada a la evidencia', 'Conclusion proportional to evidence']
  ].map(([id, es, en]) => ({ id, title: bilingual(es, en) }));
  const intervalDays = [1, 3, 7, 21];
  const knownCompetency = id => competencies.some(c => c.id === id);
  const object = v => v !== null && typeof v === 'object' && !Array.isArray(v);
  function finite(value, name, lo = -Infinity, hi = Infinity) {
    if (typeof value !== 'number' || !Number.isFinite(value) || value < lo || value > hi)
      throw new RangeError(name + ' must be finite and in range.');
    return value;
  }
  function integer(value, name, lo, hi) {
    finite(value, name, lo, hi);
    if (!Number.isInteger(value)) throw new RangeError(name + ' must be an integer.');
    return value;
  }
  function text(value, name, max = 8000, min = 0) {
    if (typeof value !== 'string' || value.length < min || value.length > max)
      throw new RangeError(name + ' has invalid text length.');
    return value;
  }
  function timestamp(value = Date.now()) {
    const n = typeof value === 'string' ? Date.parse(value) : value;
    finite(n, 'Clock time', 0, 8640000000000000);
    return new Date(n).toISOString();
  }
  function safeTree(value, depth = 0) {
    if (depth > 30) throw new RangeError('Object nesting exceeds the local limit.');
    if (value === null || typeof value === 'string' || typeof value === 'boolean') return;
    if (typeof value === 'number') { finite(value, 'JSON number'); return; }
    if (Array.isArray(value)) { if (value.length > 20000) throw new RangeError('Array exceeds the local limit.'); value.forEach(v => safeTree(v, depth + 1)); return; }
    if (!object(value) || ![Object.prototype, null].includes(Object.getPrototypeOf(value))) throw new TypeError('Only plain JSON objects are allowed.');
    for (const [key, v] of Object.entries(value)) {
      if (['__proto__', 'prototype', 'constructor'].includes(key)) throw new TypeError('Reserved JSON key.');
      safeTree(v, depth + 1);
    }
  }
  function canonical(value) {
    safeTree(value);
    const write = v => Array.isArray(v) ? '[' + v.map(write).join(',') + ']' : object(v) ? '{' + Object.keys(v).sort().map(k => JSON.stringify(k) + ':' + write(v[k])).join(',') + '}' : JSON.stringify(v);
    return write(value);
  }
  function copy(value) { return JSON.parse(canonical(value)); }
  // Standard SHA-256, synchronous in both the offline WebView and browser.
  function sha256(value) {
    const bytes = new TextEncoder().encode(typeof value === 'string' ? value : canonical(value));
    const size = Math.ceil((bytes.length + 9) / 64) * 64, data = new Uint8Array(size);
    data.set(bytes); data[bytes.length] = 128;
    const view = new DataView(data.buffer), bitLength = bytes.length * 8;
    view.setUint32(size - 8, Math.floor(bitLength / 4294967296), false);
    view.setUint32(size - 4, bitLength >>> 0, false);
    const K = [0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
    const H = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19], w = new Uint32Array(64), rr = (x,n) => (x >>> n) | (x << (32-n));
    for (let off = 0; off < size; off += 64) {
      for (let i = 0; i < 16; i++) w[i] = view.getUint32(off + i*4, false);
      for (let i = 16; i < 64; i++) { const a=w[i-15], b=w[i-2]; w[i]=(w[i-16]+(rr(a,7)^rr(a,18)^(a>>>3))+w[i-7]+(rr(b,17)^rr(b,19)^(b>>>10)))>>>0; }
      let [a,b,c,d,e,f,g,h] = H;
      for (let i=0;i<64;i++) { const t1=(h+(rr(e,6)^rr(e,11)^rr(e,25))+((e&f)^(~e&g))+K[i]+w[i])>>>0, t2=((rr(a,2)^rr(a,13)^rr(a,22))+((a&b)^(a&c)^(b&c)))>>>0; h=g;g=f;f=e;e=(d+t1)>>>0;d=c;c=b;b=a;a=(t1+t2)>>>0; }
      [a,b,c,d,e,f,g,h].forEach((v,i)=>{H[i]=(H[i]+v)>>>0;});
    }
    return H.map(v=>v.toString(16).padStart(8,'0')).join('');
  }
  const MODULE_SCOPE = sha256('Academy learning-path ' + VERSION);
  function hash(value, name = 'SHA256') { if (typeof value !== 'string' || !/^[a-f0-9]{64}$/.test(value)) throw new RangeError(name + ' must be a lowercase SHA256.'); return value; }
  function signed(payload) { return { ...copy(payload), digestSha256: sha256(payload) }; }
  function verifySigned(value, name) { safeTree(value); const { digestSha256, ...payload } = value; hash(digestSha256); if (sha256(payload) !== digestSha256) throw new Error(name + ' integrity mismatch.'); return payload; }
  function rng(seed) { let s=integer(seed,'Seed',0,4294967295)>>>0; return()=>{s=(Math.imul(1664525,s)+1013904223)>>>0;return(s+.5)/4294967296;}; }

  function createState(options = {}) {
    const now = timestamp(options.now), scope = options.contentSha256 === undefined ? MODULE_SCOPE : hash(options.contentSha256, 'Content SHA256');
    return { schema: SCHEMA, version: VERSION, contentSha256: scope, scopeSource: options.contentSha256 === undefined ? 'learning-module-only' : 'caller-supplied-content-snapshot', createdAt: now, updatedAt: now, attempts: [], hints: [], completed: {}, submissions: [], reviews: [], pilot: null };
  }
  function validateState(state) {
    safeTree(state);
    if (!object(state) || state.schema !== SCHEMA || state.version !== VERSION) throw new Error('Learning state version/schema mismatch.');
    hash(state.contentSha256); timestamp(state.createdAt); timestamp(state.updatedAt);
    const start=Date.parse(state.createdAt),end=Date.parse(state.updatedAt);
    if(end<start)throw new Error('State clock precedes creation.');
    const inStateTime=at=>{const n=Date.parse(timestamp(at));if(n<start||n>end)throw new Error('Evidence time falls outside the recorded state.');return n;};
    if (!Array.isArray(state.attempts) || state.attempts.length > MAX_ATTEMPTS || !Array.isArray(state.hints) || state.hints.length > MAX_ATTEMPTS || !object(state.completed) || !Array.isArray(state.submissions) || !Array.isArray(state.reviews)) throw new Error('Invalid learning state collections.');
    const attemptIds=new Set();let previousAttemptTime=start;
    for (const a of state.attempts) {
      if (!object(a) || !knownCompetency(a.competencyId) || typeof a.correct !== 'boolean' || typeof a.unaided !== 'boolean') throw new Error('Invalid objective attempt.');
      integer(a.hintCount,'Hint count',0,20); timestamp(a.at); text(a.caseId,'Case ID',160,1); text(a.formId,'Form ID',160,1); text(a.questionId,'Question ID',200,1);
      if (!['pre','practice','post','delayed'].includes(a.phase) || a.unaided !== (a.hintCount === 0)) throw new Error('Invalid attempt phase or support classification.');
      text(a.id,'Attempt ID',100,1);if(attemptIds.has(a.id))throw new Error('Duplicate attempt ID.');attemptIds.add(a.id);
      const attemptTime=inStateTime(a.at);if(attemptTime<previousAttemptTime)throw new Error('Attempts are out of chronological order.');previousAttemptTime=attemptTime;
    }
    for (const h of state.hints) { if (!knownCompetency(h.competencyId)) throw new Error('Unknown hint competency.'); integer(h.level,'Hint level',0,2); inStateTime(h.at); text(h.caseId,'Case ID',160,1); }
    for (const [id, at] of Object.entries(state.completed)) { text(id,'Activity ID',120,1); inStateTime(at); }
    const submissionIds=new Set(),reviewIds=new Set();
    for (let i=0;i<state.submissions.length;i++) { const s=state.submissions[i]; validateSubmission(s); inStateTime(s.createdAt);if(submissionIds.has(s.id))throw new Error('Duplicate submission ID.');submissionIds.add(s.id);if (s.parentId && !state.submissions.slice(0,i).some(p=>p.id===s.parentId && p.caseId===s.caseId && p.caseSha256===s.caseSha256 && p.revision===s.revision-1)) throw new Error('Submission parent is absent or invalid.'); }
    for (const r of state.reviews) { const s=state.submissions.find(s=>s.id===r.submissionId); if (!s) throw new Error('Review submission is absent.'); importReview(r,s);inStateTime(r.reviewedAt);if(reviewIds.has(r.digestSha256))throw new Error('Duplicate review digest.');reviewIds.add(r.digestSha256); }
    if (state.pilot !== null) validatePilot(state.pilot);
    if (new TextEncoder().encode(canonical(state)).length > MAX_BYTES) throw new RangeError('Learning evidence exceeds the local size limit.');
    return state;
  }
  function mutable(state, now) { validateState(state); const next=copy(state), at=timestamp(now); if (Date.parse(at)<Date.parse(state.updatedAt)) throw new Error('Clock moved backwards; preserve chronology.'); next.updatedAt=at; return next; }
  function question(competencyId, variant, random, id) {
    const n=Math.floor(random()*8)+2, d=(Math.floor(random()*8)+2)*1e-10, t=(Math.floor(random()*8)+1)/20;
    let q;
    if (competencyId==='physics') q={type:'number',prompt:bilingual(`Sin flujo, D=${d.toExponential(1)} m²/s y t=${t.toFixed(2)} s. Calcula la varianza 1D.`,`Without flow, D=${d.toExponential(1)} m²/s and t=${t.toFixed(2)} s. Calculate the 1D variance.`),unit:'m2',expected:2*d*t,tolerance:Math.max(1e-15,2*d*t*.005),explanation:bilingual('Para autodifusión libre 1D, Var[z(t)−z(0)]=2Dt. Una concentración uniforme no implica moléculas inmóviles.','For free 1D self-diffusion, Var[z(t)−z(0)]=2Dt. Uniform concentration does not imply immobile molecules.')};
    else if (competencyId==='units' && variant%2===0) q={type:'number',prompt:bilingual(`Multiplicas toda la forma efectiva de gradiente por ${n}, sin cambiar tiempos ni añadir gradientes fijos. ¿Por qué factor cambia b?`,`You multiply the entire effective gradient waveform by ${n}, with unchanged timings and no fixed gradients. By what factor does b change?`),unit:'dimensionless',expected:n*n,tolerance:1e-9,explanation:bilingual('q es lineal en el gradiente, y b=∫q²dt. El escalado cuadrático requiere escalar toda la forma efectiva.','q is linear in gradient, and b=∫q²dt. Quadratic scaling requires scaling the entire effective waveform.')};
    else if (competencyId==='units') q={type:'choice',prompt:bilingual('¿Qué unidades necesita b en exp(−bD), si D está en m²/s?','Which units must b have in exp(−bD), when D is in m²/s?'),choices:[bilingual('s/m²','s/m²'),bilingual('m²/s','m²/s'),bilingual('T/m','T/m')],expected:0,explanation:bilingual('El producto bD debe ser adimensional.','The product bD must be dimensionless.')};
    else if (competencyId==='calibration') { const p180=2*(n+4); q={type:'number',prompt:bilingual(`Se ha identificado el primer cruce de 180° a ${p180} µs, con potencia y fase constantes. ¿Cuál es P90?`,`The first 180° crossing has been identified at ${p180} µs, with constant power and phase. What is P90?`),unit:'us',expected:p180/2,tolerance:.01,explanation:bilingual('P90=P180/2 sólo tras identificar el orden del cruce. Un cero a 360° requiere dividir entre cuatro.','P90=P180/2 only after identifying the crossing order. A 360° zero requires division by four.')}; }
    else if (competencyId==='sequences') q={type:'choice',prompt:bilingual('Durante un intervalo de almacenamiento longitudinal con gradiente efectivo nulo, ¿qué ocurre con q ya acumulado?','During longitudinal storage with zero effective gradient, what happens to previously accumulated q?'),choices:[bilingual('Permanece constante; puede seguir contribuyendo a b','It remains constant; it can still contribute to b'),bilingual('Se reinicia automáticamente a cero','It automatically resets to zero'),bilingual('b pasa a ser negativo','b becomes negative')],expected:0,explanation:bilingual('dq/dt=γG_eff. Si G_eff=0, q no cambia; b acumula q²dt. La vía de coherencia y los signos deben verificarse.','dq/dt=γG_eff. If G_eff=0, q is unchanged; b accumulates q²dt. The coherence pathway and signs must be verified.')};
    else if (competencyId==='processing') q={type:'choice',prompt:bilingual('Una fila tiene integral negativa tras el procesado. ¿Qué acción conserva la información para investigar la causa?','A row has negative integral after processing. Which action preserves information for investigating the cause?'),choices:[bilingual('Conservarla con signo, revisar fase/baseline y ajustar un modelo apropiado','Retain its sign, inspect phase/baseline and fit an appropriate model'),bilingual('Convertirla a su valor absoluto antes de ajustar log(I)','Take its absolute value before fitting log(I)'),bilingual('Borrarla siempre como punto atípico','Always delete it as an outlier')],expected:0,explanation:bilingual('Cambiar el signo o eliminar puntos sin justificación altera los datos. El ajuste logarítmico no admite intensidades no positivas; existen ajustes directos con signo.','Changing the sign or deleting points without justification changes the data. Log fits do not accept nonpositive intensities; direct signed fits are available.')};
    else if (competencyId==='ilt') q={type:'choice',prompt:bilingual('Dos distribuciones producen atenuaciones compatibles con el ruido medido. ¿Qué conclusión es defendible?','Two distributions produce attenuations compatible with the measured noise. Which conclusion is defensible?'),choices:[bilingual('La distribución no está identificada de forma única; proponer un control discriminante','The distribution is not uniquely identified; propose a discriminating control'),bilingual('Elegir la más estrecha y declarar dos especies','Choose the narrower one and declare two species'),bilingual('El mayor R² demuestra la distribución verdadera','The highest R² proves the true distribution')],expected:0,explanation:bilingual('La regularización expresa supuestos. Un buen residuo y estabilidad interna no prueban una distribución única ni una identidad química.','Regularization expresses assumptions. A good residual and internal stability do not prove a unique distribution or chemical identity.')};
    else q={type:'choice',prompt:bilingual('Una rampa repetida reduce ruido, pero ambas usan el mismo gradiente mal calibrado. ¿Qué cambia al promediar?','A repeated ramp reduces noise, but both use the same miscalibrated gradient. What changes when averaging?'),choices:[bilingual('Puede reducir la dispersión; el sesgo compartido permanece','Scatter may decrease; the shared bias remains'),bilingual('La calibración absoluta se corrige automáticamente','Absolute calibration automatically corrects itself'),bilingual('Se demuestra la identidad química','Chemical identity is demonstrated')],expected:0,explanation:bilingual('El error de escala compartido no se promedia como ruido independiente. Hay que medir un patrón apropiado o aportar un control independiente.','A shared scale error does not average like independent noise. An appropriate standard or independent control is needed.')};
    // Shuffle objective choices deterministically; position is not the answer cue.
    if(q.type==='choice') { const tagged=q.choices.map((v,i)=>({v,correct:i===q.expected})); for(let i=tagged.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[tagged[i],tagged[j]]=[tagged[j],tagged[i]];} q.choices=tagged.map(v=>v.v);q.expected=tagged.findIndex(v=>v.correct); }
    return {id,competencyId,variant,...q};
  }
  function makeDiagnostic(options={}) {
    const seed=options.seed===undefined?130:integer(options.seed,'Seed',0,4294967295), phase=options.phase||'practice', count=options.count===undefined?14:integer(options.count,'Question count',1,28);
    if(!['pre','practice','post','delayed'].includes(phase))throw new Error('Unknown learning phase.');
    // The same seed is the same scenario even if somebody changes the phase.
    // Relabelling a pre form as post must not count as unseen transfer.
    const random=rng(seed), caseId='objective-'+seed, questions=[];
    for(let i=0;i<count;i++){const c=competencies[i%competencies.length];questions.push(question(c.id,Math.floor(i/competencies.length),random,caseId+'/'+i));}
    const payload={schema:'academy-objective-form/1',version:VERSION,seed,phase,caseId,questions,automaticAssessment:'explicit-numeric-or-choice-only',secureExam:false};
    return {...payload,id:'form-'+sha256(payload).slice(0,20),digestSha256:sha256(payload)};
  }
  function validForm(form) { const expected=makeDiagnostic({seed:form.seed,phase:form.phase,count:form.questions?.length}); if(canonical(form)!==canonical(expected))throw new Error('Objective form integrity mismatch.'); return form; }
  function gradeQuestion(q,answer) {
    let correct=false;
    if(q.type==='number'){const n=typeof answer==='number'?answer:typeof answer==='string'&&answer.trim()!==''?Number(answer):NaN;correct=Number.isFinite(n)&&Math.abs(n-q.expected)<=q.tolerance;}
    else { const n=typeof answer==='number'?answer:typeof answer==='string'&&answer.trim()!==''?Number(answer):NaN;correct=Number.isInteger(n)&&n===q.expected; }
    return {questionId:q.id,competencyId:q.competencyId,correct,expected:q.expected,unit:q.unit||null,tolerance:q.tolerance||0,explanation:copy(q.explanation),semanticGrading:false};
  }
  function gradeDiagnostic(form,answers={}) {validForm(form);safeTree(answers);if(!object(answers))throw new Error('Answers must be keyed by question ID.');const results=form.questions.map(q=>gradeQuestion(q,answers[q.id]));return {formId:form.id,caseId:form.caseId,phase:form.phase,score:results.filter(v=>v.correct).length,total:results.length,results,semanticGrading:false,masteryAssigned:false};}
  function recordAttempt(state,options) {
    const next=mutable(state,options.now);validForm(options.form);
    const q=options.form.questions.find(q=>q.id===options.questionId);if(!q)throw new Error('Question does not belong to this form.');
    const recordedHints=Math.min(20,next.hints.filter(h=>h.competencyId===q.competencyId&&h.caseId===options.form.caseId).length);
    const at=next.updatedAt, hintCount=Math.max(recordedHints,options.hintCount===undefined?0:integer(options.hintCount,'Hint count',0,20));
    const answer=options.answer===undefined?null:options.answer;
    if(answer!==null){if(typeof answer==='number')finite(answer,'Objective answer');else if(typeof answer==='string')text(answer,'Objective answer',200);else throw new Error('Objective answer must be a number, bounded string or null.');}
    const r=gradeQuestion(q,answer);
    next.attempts.push({id:'attempt-'+(next.attempts.length+1),questionId:q.id,formId:options.form.id,caseId:options.form.caseId,phase:options.form.phase,competencyId:q.competencyId,answer,correct:r.correct,hintCount,unaided:hintCount===0,at});
    if(next.attempts.length>MAX_ATTEMPTS)throw new RangeError('Export your evidence before adding more attempts.');
    validateState(next);
    return next;
  }
  function recordHint(state,options) {const next=mutable(state,options.now);if(!knownCompetency(options.competencyId))throw new Error('Unknown competency.');next.hints.push({competencyId:options.competencyId,caseId:text(options.caseId,'Case ID',160,1),level:integer(options.level,'Hint level',0,2),at:next.updatedAt});if(next.hints.length>MAX_ATTEMPTS)throw new RangeError('Export your evidence before adding more hints.');return next;}
  function completeActivity(state,id,options={}) {const next=mutable(state,options.now);next.completed[text(id,'Activity ID',120,1)]=next.updatedAt;return next;}
  function competencyProgress(state,c,now) {
    const all=state.attempts.filter(a=>a.competencyId===c.id), unaided=all.filter(a=>a.unaided), successful=unaided.filter(a=>a.correct);
    let streak=0;for(let i=unaided.length-1;i>=0&&unaided[i].correct;i--)streak++;
    const cases=[...new Set(successful.map(a=>a.caseId))], first=successful[0], later=successful.filter(a=>first&&Date.parse(a.at)-Date.parse(first.at)>=3*DAY), transfer=successful.some(a=>['post','delayed'].includes(a.phase)&&successful.some(b=>b.caseId!==a.caseId));
    const delayed=later.some(a=>a.phase==='delayed'), last=all[all.length-1], mastered=cases.length>=2&&transfer&&delayed&&streak>=2;
    const dueAt=last?new Date(Date.parse(last.at)+DAY*intervalDays[Math.min(Math.max(streak-1,0),intervalDays.length-1)]).toISOString():null;
    return {id:c.id,title:copy(c.title),status:mastered?'demonstrated':all.length?'practising':'not-started',attempts:all.length,correct:all.filter(a=>a.correct).length,unaidedCorrect:successful.length,distinctSuccessfulCases:cases.length,transferDemonstrated:transfer,delayedRetentionDemonstrated:delayed,consecutiveUnaidedCorrect:streak,dueAt,due:!!dueAt&&Date.parse(dueAt)<=Date.parse(now),evidenceScope:'objective-authored-variants; not independent experimental qualification',humanGrade:null};
  }
  function progress(state,options={}) {validateState(state);const now=timestamp(options.now);if(Date.parse(now)<Date.parse(state.updatedAt))throw new Error('Progress clock precedes the recorded evidence.');const list=competencies.map(c=>competencyProgress(state,c,now));return {at:now,competencies:list,attemptsCount:state.attempts.length,completedCount:Object.keys(state.completed).length,masteredCount:list.filter(c=>c.status==='demonstrated').length,navigationLocked:false,semanticGrading:false};}
  function dueReviews(state,options={}) {return progress(state,options).competencies.filter(c=>c.due).map(c=>({competencyId:c.id,title:c.title,dueAt:c.dueAt,recommendedPhase:'delayed',reason:bilingual('Comprueba transferencia y retención con un caso y valores nuevos.','Check transfer and retention with a new case and values.')}));}

  const submissionFields=['question','prediction','processing','controls','conclusion'];
  function evidenceRefs(values,name='Evidence references') {if(!Array.isArray(values)||values.length>100)throw new RangeError(name+' must be a bounded array.');const ids=new Set();return values.map(v=>{if(!object(v))throw new Error('Evidence reference must be an object.');const id=text(v.id,'Evidence ID',160,1);if(ids.has(id))throw new Error('Duplicate evidence ID.');ids.add(id);return{id,label:text(v.label||id,'Evidence label',500,1),sha256:v.sha256===undefined||v.sha256===null?null:hash(v.sha256,'Evidence SHA256'),kind:text(v.kind||'student-record','Evidence kind',80,1)};});}
  function createSubmission(options) {
    if(!object(options.fields))throw new Error('Five submission fields are required.');
    const fields={};for(const f of submissionFields)fields[f]=text(options.fields[f]||'',f,8000);
    const caseId=text(options.caseId,'Case ID',160,1),caseSha256=hash(options.caseSha256,'Case SHA256'), parent=options.parentSubmission||null;
    if(parent){validateSubmission(parent);if(parent.caseId!==caseId||parent.caseSha256!==caseSha256)throw new Error('A revision must retain the same case and snapshot.');}
    const payload={schema:'academy-submission/1',version:VERSION,caseId,caseSha256,revision:parent?parent.revision+1:1,parentId:parent?parent.id:null,createdAt:timestamp(options.now),fields,evidenceReferences:evidenceRefs(options.evidenceReferences||[]),humanReviewRequired:true,automaticGrade:null};
    if(parent&&Date.parse(payload.createdAt)<Date.parse(parent.createdAt))throw new Error('A revision cannot precede its parent.');
    const value=signed(payload);value.id='submission-'+value.digestSha256;return value;
  }
  function validateSubmission(value) {
    if(!object(value))throw new Error('Submission object required.');const {id,...signedValue}=value,p=verifySigned(signedValue,'Submission');
    if(p.schema!=='academy-submission/1'||p.version!==VERSION||id!=='submission-'+signedValue.digestSha256)throw new Error('Submission identity mismatch.');
    hash(p.caseSha256);text(p.caseId,'Case ID',160,1);integer(p.revision,'Revision',1,1000);timestamp(p.createdAt);
    if(p.parentId!==null)text(p.parentId,'Parent ID',100,1);
    if((p.revision===1)!==(p.parentId===null))throw new Error('Invalid revision parent.');
    if(!object(p.fields)||Object.keys(p.fields).sort().join('|')!==submissionFields.slice().sort().join('|'))throw new Error('Invalid submission fields.');
    for(const f of submissionFields)text(p.fields[f],f,8000);
    evidenceRefs(p.evidenceReferences);if(p.humanReviewRequired!==true||p.automaticGrade!==null)throw new Error('Submission must retain human assessment.');
    return value;
  }
  function createReview(submission,options) {
    validateSubmission(submission);if(!object(options.scores)||!object(options.comments))throw new Error('Five scores and comments are required.');
    const scores={},comments={},refs={},allowed=new Set(submission.evidenceReferences.map(r=>r.id));
    for(const c of rubricCriteria){scores[c.id]=integer(options.scores[c.id],'Rubric '+c.id,0,4);comments[c.id]=text(options.comments[c.id],'Comment '+c.id,4000,1);const a=options.evidenceReferences?.[c.id]||[];if(!Array.isArray(a)||!a.length||a.length>20||a.some(id=>typeof id!=='string'||!allowed.has(id)))throw new Error('Each criterion must cite evidence present in the submission.');refs[c.id]=[...new Set(a)];}
    const questions=options.questions||[];if(!Array.isArray(questions)||questions.length>20)throw new Error('Review questions exceed limit.');questions.forEach(q=>text(q,'Review question',2000,1));
    const at=timestamp(options.now);if(Date.parse(at)<Date.parse(submission.createdAt))throw new Error('A review cannot precede its submission.');
    return signed({schema:'academy-teacher-review/1',version:VERSION,submissionId:submission.id,submissionRevision:submission.revision,caseId:submission.caseId,caseSha256:submission.caseSha256,reviewer:text(options.reviewer||'Local instructor','Reviewer label',160,1),reviewedAt:at,scores,comments,evidenceReferences:refs,questions:copy(questions),total:Object.values(scores).reduce((a,b)=>a+b,0),maximum:20,assessment:'human-entered-rubric',authentication:'local-integrity-only; not a digital signature or proof of reviewer identity'});
  }
  function importReview(raw,submission) {
    const value=typeof raw==='string'?JSON.parse(raw):copy(raw);validateSubmission(submission);const p=verifySigned(value,'Teacher review');
    if(p.schema!=='academy-teacher-review/1'||p.version!==VERSION||p.submissionId!==submission.id||p.submissionRevision!==submission.revision||p.caseId!==submission.caseId||p.caseSha256!==submission.caseSha256)throw new Error('Review belongs to a different case, snapshot or revision.');
    const checked=createReview(submission,{scores:p.scores,comments:p.comments,evidenceReferences:p.evidenceReferences,questions:p.questions,reviewer:p.reviewer,now:p.reviewedAt});
    if(canonical(value)!==canonical(checked))throw new Error('Review fields or total were altered.');return checked;
  }
  function addSubmission(state,submission,options={}) {const next=mutable(state,options.now);validateSubmission(submission);if(next.submissions.some(s=>s.id===submission.id))throw new Error('This submission is already recorded.');if(submission.parentId&&!next.submissions.some(s=>s.id===submission.parentId))throw new Error('Record the parent before its revision.');if(Date.parse(submission.createdAt)>Date.parse(next.updatedAt))throw new Error('Submission is newer than the supplied clock.');next.submissions.push(copy(submission));validateState(next);return next;}
  function addReview(state,raw,options={}) {const next=mutable(state,options.now),value=typeof raw==='string'?JSON.parse(raw):raw,submission=next.submissions.find(s=>s.id===value.submissionId);if(!submission)throw new Error('Review has no recorded submission.');const review=importReview(value,submission);if(next.reviews.some(r=>r.digestSha256===review.digestSha256))throw new Error('This review is already recorded.');if(Date.parse(review.reviewedAt)>Date.parse(next.updatedAt))throw new Error('Review is newer than the supplied clock.');next.reviews.push(review);return next;}
  function revisionComparison(previous,next) {validateSubmission(previous);validateSubmission(next);if(next.parentId!==previous.id||next.caseSha256!==previous.caseSha256)throw new Error('Submissions are not consecutive revisions.');return {from:previous.revision,to:next.revision,changedFields:submissionFields.filter(f=>previous.fields[f]!==next.fields[f]),automaticQualityJudgement:null,humanReviewRequired:true};}
  function exportState(state) {validateState(state);return JSON.stringify(signed({schema:'academy-learning-export/1',version:VERSION,state:copy(state)}));}
  function importState(raw,options={}) {if(typeof raw==='string'&&new TextEncoder().encode(raw).length>MAX_BYTES+10000)throw new RangeError('Import exceeds local size limit.');const value=typeof raw==='string'?JSON.parse(raw):copy(raw),p=verifySigned(value,'Learning export');if(p.schema!=='academy-learning-export/1'||p.version!==VERSION)throw new Error('Export version/schema mismatch.');validateState(p.state);if(options.contentSha256&&p.state.contentSha256!==hash(options.contentSha256))throw new Error('Content snapshot mismatch; preserve this export separately.');return copy(p.state);}

  const pilotProtocol={id:'academy-pilot-transfer-retention/1',version:VERSION,language:['es','en'],consent:bilingual('Piloto docente voluntario; los datos quedan locales. El consentimiento y la revisión institucional se gestionan por el docente antes de recoger datos identificables.','Voluntary teaching pilot; data stay local. Consent and institutional review are managed by the instructor before collecting identifiable data.'),stages:[{id:'pre',title:bilingual('Caso inicial sin ayuda','Unaided initial case'),delayDays:0},{id:'post',title:bilingual('Caso final distinto, sin ayuda','Different unaided final case'),delayDays:0},{id:'delayed',title:bilingual('Caso nuevo de retención diferida','New delayed-retention case'),delayDays:7}],outcomes:[bilingual('Predicción y controles justificados en una muestra nueva','Justified prediction and controls on a new sample'),bilingual('Reconocimiento de sesgo, incertidumbre y no identificabilidad','Recognition of bias, uncertainty and non-identifiability'),bilingual('Concordancia entre dos evaluadores independientes de la rúbrica','Agreement between two independent rubric reviewers')],interpretation:bilingual('Las pruebas del software no acreditan eficacia docente. Informar participación, abandonos, ayudas y diferencias entre casos. No fabricar alumnos, resultados ni fechas.','Software checks do not establish teaching efficacy. Report participation, attrition, assistance and differences between cases. Do not fabricate learners, outcomes or dates.'),automaticSemanticGrade:false};
  function createPilot(options={}) {if(options.consentConfirmed!==true)throw new Error('Record voluntary consent before starting a local pilot.');return {schema:'academy-local-pilot/1',protocolId:pilotProtocol.id,createdAt:timestamp(options.now),consentConfirmed:true,participantCode:text(options.participantCode||'anonymous-local','Local participant code',80,1),records:[]};}
  function validatePilot(pilot) {
    if(!object(pilot)||pilot.schema!=='academy-local-pilot/1'||pilot.protocolId!==pilotProtocol.id||pilot.consentConfirmed!==true||!Array.isArray(pilot.records)||pilot.records.length>3)throw new Error('Invalid pilot record.');
    timestamp(pilot.createdAt);text(pilot.participantCode,'Participant code',80,1);
    const forms=new Set(),cases=new Set(),stages=['pre','post','delayed'];let previous=Date.parse(pilot.createdAt);
    for(let i=0;i<pilot.records.length;i++){
      const r=pilot.records[i];if(r.stage!==stages[i])throw new Error('Pilot stages must follow pre, post, delayed order.');
      const at=Date.parse(timestamp(r.at));if(at<previous)throw new Error('Pilot records are out of chronological order.');
      if(r.stage==='delayed'&&at-previous<7*DAY)throw new Error('Delayed pilot record precedes the retention interval.');previous=at;
      text(r.formId,'Form ID',160,1);text(r.caseId,'Case ID',160,1);integer(r.total,'Question total',1,28);integer(r.seed,'Pilot form seed',0,4294967295);
      const form=makeDiagnostic({seed:r.seed,phase:r.stage,count:r.total});
      if(form.id!==r.formId||form.caseId!==r.caseId)throw new Error('Pilot form identity mismatch.');
      if(forms.has(r.formId)||cases.has(r.caseId))throw new Error('Pilot transfer case or form was reused.');forms.add(r.formId);cases.add(r.caseId);
      integer(r.score,'Objective score',0,r.total);if(gradeDiagnostic(form,r.answers).score!==r.score)throw new Error('Pilot score does not match the retained objective answers.');
      if(r.unaided!==true||r.semanticGrade!==null)throw new Error('Unaided pilot outcomes must be explicitly unaided and have no semantic grade.');
    }
    return pilot;
  }
  function recordPilot(pilot,{form,answers,now,unaided}) {validatePilot(pilot);validForm(form);if(!['pre','post','delayed'].includes(form.phase))throw new Error('Practice forms are not pilot outcomes.');if(unaided!==true)throw new Error('Assisted practice must not be labelled as an unaided outcome.');const at=timestamp(now),next=copy(pilot),previous=next.records[next.records.length-1];if(Date.parse(at)<Date.parse(previous?.at||pilot.createdAt))throw new Error('Pilot clock moved backwards.');if(form.phase==='pre'&&next.records.length||form.phase==='post'&&!next.records.some(r=>r.stage==='pre')||form.phase==='delayed'&&!next.records.some(r=>r.stage==='post'))throw new Error('Pilot stages must follow pre, post, delayed order.');if(next.records.some(r=>r.stage===form.phase))throw new Error('Pilot stage already recorded.');if(form.phase==='delayed'&&Date.parse(at)-Date.parse(next.records.find(r=>r.stage==='post').at)<7*DAY)throw new Error('The delayed pilot case is not due yet.');const result=gradeDiagnostic(form,answers);next.records.push({stage:form.phase,seed:form.seed,formId:form.id,caseId:form.caseId,at,score:result.score,total:result.total,answers:copy(answers),unaided:true,semanticGrade:null});validatePilot(next);return next;}

  function validateKnowledge(knowledge) {safeTree(knowledge);if(!object(knowledge)||knowledge.version!==VERSION||!Array.isArray(knowledge.chunks)||knowledge.chunks.length>100)throw new Error('Invalid research tutor knowledge.');const ids=new Set();for(const chunk of knowledge.chunks){text(chunk.id,'Chunk ID',100,1);if(ids.has(chunk.id))throw new Error('Duplicate knowledge chunk.');ids.add(chunk.id);for(const field of ['title','question','objective','why','body'])for(const lang of ['es','en'])text(chunk[field]?.[lang],field+' '+lang,20000,1);if(!Array.isArray(chunk.sources)||!chunk.sources.length||chunk.sources.length>20)throw new Error('A reviewed chunk needs bounded sources.');for(const source of chunk.sources){text(source.id,'Source ID',100,1);text(source.title,'Source title',500,1);text(source.path,'Source path',500,1);if(source.path.includes('..')||source.path.startsWith('/')||source.path.includes('\\'))throw new Error('Source path must stay relative to the teaching content.');if(source.doi!==undefined&&!/^10\.\d{4,9}\/\S+$/.test(source.doi))throw new Error('Invalid source DOI.');}}return knowledge;}
  function tokens(value) {return String(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().match(/[a-z0-9]{3,}/g)||[];}
  function retrieveKnowledge(knowledge,question,language='en',options={}) {validateKnowledge(knowledge);const lang=language==='es'?'es':'en',search=new Set(tokens(question)),limit=options.limit===undefined?3:integer(options.limit,'Retrieval limit',1,6);return knowledge.chunks.map(chunk=>{const corpus=tokens([chunk.title[lang],chunk.question[lang],chunk.body[lang],...(chunk.tags||[])].join(' ')),set=new Set(corpus);return {chunk,score:(options.topic===chunk.id?1000:0)+[...search].filter(v=>set.has(v)).length};}).filter(r=>r.score>0).sort((a,b)=>b.score-a.score||a.chunk.id.localeCompare(b.chunk.id)).slice(0,limit).map(r=>({id:r.chunk.id,title:r.chunk.title[lang],body:r.chunk.body[lang],equation:r.chunk.equation||null,units:r.chunk.units||null,assumptions:copy(r.chunk.assumptions||[]),sources:copy(r.chunk.sources),score:r.score,isModelAnswer:false}));}
  function tutorHint(options,knowledge) {
    validateKnowledge(knowledge);const lang=options.language==='es'?'es':'en',chunk=knowledge.chunks.find(c=>c.id===options.topic);if(!chunk)throw new Error('Unknown research tutor topic.');const level=integer(options.level===undefined?0:options.level,'Hint level',0,2);let context=options.context===undefined?null:copy(options.context);if(context&&new TextEncoder().encode(canonical(context)).length>16000)throw new RangeError('Tutor simulation context exceeds local limit.');
    const levels=[chunk.question[lang],chunk.why[lang],chunk.body[lang]];
    return {topic:chunk.id,title:chunk.title[lang],level,text:levels[level],sources:copy(chunk.sources),equation:level===2?(chunk.equation||null):null,context,contextPolicy:'Context is supplied evidence, not independently inferred measurement; numerical values must come from the calculation engine.',isModelAnswer:false,mode:'reviewed-socratic-guide',humanGrade:null};
  }
  return {VERSION,SCHEMA,DAY,MODULE_SCOPE,competencies,rubricCriteria,submissionFields,intervalDays,pilotProtocol,sha256,canonical,createState,validateState,makeDiagnostic,gradeDiagnostic,recordAttempt,recordHint,completeActivity,progress,dueReviews,createSubmission,validateSubmission,createReview,importReview,addSubmission,addReview,revisionComparison,exportState,importState,createPilot,recordPilot,validatePilot,validateKnowledge,retrieveKnowledge,tutorHint};
});
