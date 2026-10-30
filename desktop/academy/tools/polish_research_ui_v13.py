from pathlib import Path

P=Path(__file__).resolve().parents[1]/'web/research-studio.js'


def main():
    text=P.read_text(encoding='utf-8')
    replacements=[
      ("s.evidence==='experimental-public'?t('EXPERIMENTAL PÚBLICO','PUBLIC EXPERIMENT')", "s.kind==='experimental'?t('DATOS EXPERIMENTALES','EXPERIMENTAL DATA')"),
      ("caseEvidence:caseState.evidence||'synthetic-education-only'", "caseEvidence:caseState.evidenceStatus||'synthetic-education-only'"),
      ("${fidPlot(a.series?.[0])}", "${fidPlot(a.series?.[0]?{...a.series[0],dwell_s:a.series[0].dwell_s||caseState.sample.dwell_s}:null)}"),
      ("${fidPlot(librarySession.series?.[0])}", "${fidPlot(librarySession.series?.[0]?{...librarySession.series[0],dwell_s:librarySession.dwell_s}:null)}"),
      ("librarySession.series.map(fid=>P.processFID(fid,", "librarySession.series.map(fid=>P.processFID({...fid,dwell_s:librarySession.dwell_s,sfMHz:librarySession.sfMHz,carrierPpm:librarySession.carrierPpm},"),
      ("P.fitAttenuation(bs,areas,{method:'nonlinear'})", "P.fitAttenuation(bs,areas,{method:'signal'})"),
      ("metadata:{provenance:librarySession.provenance,bSource:librarySession.userBSource,originalsUnchanged:true}});save();active='inference'", "metadata:{provenance:librarySession.provenance,bSource:librarySession.userBSource,originalsUnchanged:true,provenanceVerified:true}});caseState=J.process(caseState,{});save();active='inference'"),
      ("source:'local-user-import',license:null", "source:'local-user-import',license:'User-supplied, private local use; permission not independently verified'"),
      ("fileName:file.name}});save();message=", "fileName:file.name}});caseState=J.process(caseState,{});save();message="),
      ("form=null,hintLevel=0", "form=null,diagnosticResult=null,hintLevel=0"),
      ("form=L.makeDiagnostic({seed:", "diagnosticResult=null;form=L.makeDiagnostic({seed:"),
      ("message=JSON.stringify(L.gradeDiagnostic(form,answers));save();", "diagnosticResult=L.gradeDiagnostic(form,answers);message=t('Respuestas objetivas correctas: ','Correct objective answers: ')+diagnosticResult.score+' / '+diagnosticResult.total;save();"),
      ("active=step.dataset.step;hintLevel=0;hint=null;retrieval=[];render();options.onView", "active=step.dataset.step;hintLevel=0;hint=null;retrieval=[];render();container.querySelector('.rs-main')?.scrollIntoView({block:'start'});options.onView"),
    ]
    for old,new in replacements:
      if new in text:continue
      if text.count(old)!=1:raise ValueError('Source anchor: '+old[:80])
      text=text.replace(old,new,1)
    start=text.index('   function competencies(){')
    end=text.index('   const rubricNames=',start)
    text=text[:start]+r'''   function competencies(){
     const p=L.progress(learning,{now:now()}),rows=p.competencies||[];
     const statusLabel=s=>({ 'not-started':t('Por explorar','Not started'),'practising':t('En práctica','Practising'),'demonstrated':t('Demostrada en variantes objetivas','Demonstrated on objective variants') }[s]||s);
     return card(t('Demostrar comprensión en otro caso','Demonstrate understanding on another case'),`<p>${t('Completar una actividad y dominar una competencia son registros diferentes. La práctica permite pistas; transferencia y retención requieren variantes nuevas. La navegación permanece libre.','Completing an activity and mastering a competency are different records. Practice permits hints; transfer and retention require new variants. Navigation stays free.')}</p><div class="rs-metrics">${metric(t('Actividades completadas','Completed activities'),p.completedCount)}${metric(t('Competencias demostradas','Demonstrated competencies'),p.masteredCount+' / 7')}${metric(t('Respuestas registradas','Recorded answers'),p.attemptsCount)}</div><div class="rs-toolbar">${button('pretest','Diagnóstico inicial','Initial diagnostic')}${button('practice','Practicar','Practice')}${button('posttest','Caso de transferencia','Transfer case')}${button('delayed','Revisión diferida','Delayed review')}</div>${form?`<div class="rs-form">${qList().map(q=>`<label>${esc(loc(q.prompt)||q.id)}${q.type==='choice'?`<select data-answer="${esc(q.id)}"><option value="">${t('Selecciona','Choose')}</option>${(q.choices||[]).map((c,i)=>`<option value="${i}">${esc(loc(c))}</option>`).join('')}</select>`:`<input type="number" step="any" data-answer="${esc(q.id)}">`}<small>${esc(q.unit||'')}</small></label>`).join('')}</div><div class="rs-toolbar">${button('grade-diagnostic','Comprobar decisiones objetivas','Check objective decisions',true)}</div>`:''}${diagnosticResult?`<div>${diagnosticResult.results.map(r=>`<div class="rs-review"><b>${r.correct?'✓':t('Revisar','Review')}</b><p>${esc(loc(r.explanation))}</p><span class="rs-caption">${t('Valor de referencia del ejercicio:','Exercise reference value:')} ${esc(fmt(r.expected))} ${esc(r.unit||'')}</span></div>`).join('')}</div>`:''}${rows.map(c=>`<div class="rs-competency"><strong>${esc(loc(c.title))}</strong><span class="rs-badge">${esc(statusLabel(c.status))}</span><p>${c.correct} / ${c.attempts} ${t('respuestas correctas','correct answers')} · ${c.distinctSuccessfulCases} ${t('casos diferentes','different cases')}</p><p class="rs-caption">${t('Transferencia','Transfer')}: ${c.transferDemonstrated?'✓':'○'} · ${t('Retención diferida','Delayed retention')}: ${c.delayedRetentionDemonstrated?'✓':'○'} ${c.due?' · '+t('Revisión pendiente','Review due'):''}</p></div>`).join('')}<p class="rs-scope">${t('El piloto docente requiere participantes y consentimiento reales. Se registran pretest, transferencia y retención; estos indicadores no sustituyen una evaluación docente independiente.','The teaching pilot requires actual participants and consent. Pretest, transfer and retention are recorded; these indicators do not replace independent educational evaluation.')}</p>`);
   }
'''+text[end:]
    P.write_text(text,encoding='utf-8')
    print('Research UI data contracts, experimental labels and competency feedback updated')


if __name__=='__main__':main()
