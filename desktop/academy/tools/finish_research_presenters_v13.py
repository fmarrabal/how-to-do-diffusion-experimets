from pathlib import Path
P=Path(__file__).resolve().parents[1]/'web/research-studio.js'


def main():
 s=P.read_text(encoding='utf-8')
 changes=[
  ("let submissions=[],reviews=[],draft=", "let spatialParameters=root.AcademySpatialEncoding.defaults(),predictionsByStage={};\n   let submissions=[],reviews=[],draft="),
  ("a?.regularization??.02", "a?.parameters?.regularization??.02"),
  ("'P90',c?.p90Us||9,'µs','min=\"0.1\" max=\"200\"'", "'P90',c?.p90Us||9,'µs','min=\"0.1\" max=\"100\"'"),
  ("'min=\"30\" max=\"1000\" step=\"1\"'", "'min=\"30\" max=\"500\" step=\"1\"'"),
  ("[['all','Todo el espectro','Whole spectrum']", "[['all','Ambas señales sintéticas (1,45–2,65 ppm)','Both synthetic signals (1.45–2.65 ppm)']"),
  ("const d=root.AcademySpatialEncoding.defaults(),s=spatial;", "const d=spatialParameters,s=spatial;"),
  ("working=true;message=t('Calculando el programa", "spatialParameters={...spatialParameters,...parameters};working=true;message=t('Calculando el programa"),
  ("${s?plot([{name:'Mx'", "${s?plot([{name:'Mx'"),
  ("<pre class=\"rs-pre\">${esc(JSON.stringify(s.metrics,null,2))}</pre>", "${spatialMetrics(s)}"),
  ("${convergence?`<pre class=\"rs-pre\">${esc(JSON.stringify(convergence,null,2))}</pre>`:''}", "${convergence?convergenceMetrics(convergence):''}"),
  ("<pre class=\"rs-pre\">${esc(JSON.stringify(u.sourceContributions,null,2))}</pre>", "${uncertaintyMetrics(u)}"),
  ("<pre class=\"rs-pre\">${esc(JSON.stringify(u.unquantifiedSources||[],null,2))}</pre>", "<p class=\"rs-caption\">${(u.unquantifiedSources||[]).map(v=>esc(loc(v.label)||loc(v)||v.id||JSON.stringify(v))).join(' · ')}</p>"),
  ("<pre class=\"rs-pre\">${esc(JSON.stringify({selected:m.selected,plans:m.plans,heldoutRanking:m.heldoutRanking},null,2))}</pre>", "${measurementMetrics(m)}"),
  ("${reviews.map(r=>`<div class=\"rs-review\"><strong>${t('Revisión humana','Human review')}</strong><pre class=\"rs-pre\">${esc(JSON.stringify(r,null,2))}</pre></div>`).join('')}", "${reviews.map(r=>reviewMetrics(r)).join('')}"),
  ("number('score-'+id,id,2", "number('score-'+id,criterionLabel(id),2"),
  ("<div data-tutor-answer>", "<div data-tutor-answer>"),
  ("${retrieval.map(c=>`<div><h4>${esc(loc(c.title)||c.id)}</h4><p class=\"rs-caption\">${esc(loc(c.body)||loc(c.text)||'')}</p></div>`).join('')}", "${retrieval.map(c=>`<div><h4>${esc(loc(c.title)||c.id)}</h4><p class=\"rs-caption\">${esc(loc(c.body)||loc(c.text)||'')}</p>${sourceLinks(c.sources)}</div>`).join('')}${hint?sourceLinks(hint.sources):''}"),
  ("predictionsByStage={};", "predictionsByStage={};"),
  ("if(el)prediction=el.value.slice(0,4000);", "if(el){prediction=el.value.slice(0,4000);predictionsByStage[active]=prediction;}"),
  ("draft:clone(draft),prediction};", "draft:clone(draft),prediction,predictionsByStage:clone(predictionsByStage)};"),
  ("active=step.dataset.step;hintLevel=0", "active=step.dataset.step;prediction=predictionsByStage[active]||'';hintLevel=0"),
  ("active=steps[j][0];hintLevel=0", "active=steps[j][0];prediction=predictionsByStage[active]||'';hintLevel=0"),
  ("prediction:prediction,processing:", "prediction:Object.entries(predictionsByStage).map(([stage,text])=>stage+': '+text).join('\\n\\n'),processing:"),
  ("diagnosticResult=null;form=L.makeDiagnostic", "diagnosticResult=null;hintLevel=0;form=L.makeDiagnostic"),
  ("context:{caseId:caseState.id,stage:active,prediction,analysis:caseState.analysis,uncertainty:caseState.uncertainty}", "context:{caseId:caseState.id,stage:active,prediction,parameters:caseState.design?.parameters,analysis:caseState.analysis?{D_m2_s:caseState.analysis.D_m2_s,residualRms:caseState.analysis.residualRms,method:caseState.analysis.method}:null,uncertainty:caseState.uncertainty?{interval95:caseState.uncertainty.interval95,boundaryDraws:caseState.uncertainty.boundaryDraws,coverageValidated:false}:null}"),
 ]
 for old,new in changes:
  if old==new or new in s:continue
  if s.count(old)!=1:raise ValueError('UI anchor '+old[:100]+' count '+str(s.count(old)))
  s=s.replace(old,new,1)
 helpers=r'''
   function table(headers,rows){return `<div class="rs-scroll"><table class="rs-data"><thead><tr>${headers.map(h=>`<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map(v=>`<td>${esc(v)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;}
   function sourceLinks(sources){return `<div class="rs-source">${(sources||[]).map(v=>v.doi?`<a href="https://doi.org/${esc(v.doi)}" target="_blank" rel="noopener">${esc(v.title||v.doi)}</a>`:`<span>${esc(v.title||v.id||'')}</span>`).join(' · ')}</div>`;}
   function criterionLabel(id){return ({physics:t('Física y ecuación','Physics and equation'),'experimental-design':t('Diseño y controles','Design and controls'),'processing-reproducibility':t('Procesado reproducible','Reproducible processing'),uncertainty:t('Incertidumbre','Uncertainty'),'defensible-conclusion':t('Conclusión defendible','Defensible conclusion')})[id]||id;}
   function uncertaintyMetrics(u){return table([t('Fuente','Source'),'SD(D) / m² s⁻¹',t('SD relativa','Relative SD')],(u.sourceContributions||[]).map(v=>[loc(v.label)||v.id,fmt(v.Dsd_m2_s),fmt(v.relativeSd*100)+' %']))+`<p class="rs-caption">${t('Ajustes Monte Carlo en el límite','Monte Carlo fits at boundary')}: ${u.boundaryDraws||0} / ${u.samples}. ${u.boundaryDraws?t('Revisa el intervalo: algunos ajustes llegaron al límite del modelo.','Review the interval: some fits reached the model boundary.'):t('Intervalo de sensibilidad condicional al modelo.','Model-conditional sensitivity interval.')}</p>`;}
   function measurementMetrics(m){const planLabels={'higher-b':t('Mayor rango b','Higher b range'),replicate:t('Réplicas','Replicates'),reverse:t('Orden inverso','Reverse order'),delta:t('Cambiar Δ','Change Δ'),'flow-compensated':t('Compensar flujo','Compensate flow')};const plans=table([t('Diseño','Design'),t('Separación prevista / ruido','Predicted separation / noise')],(m.plans||[]).map(p=>[planLabels[p.id]||p.id,fmt(p.separationToNoise)]));const selected=m.selected,curves=(selected?.predictions||[]).map(p=>({name:p.id,data:selected.bs.map((b,i)=>({x:b*1e-9,y:p.signal[i]}))}));if(m.observations){const ob=m.observations;const bs=ob.bs||selected?.bs||[],ys=ob.signal||ob.signals||ob.y||[];curves.push({name:t('Control reservado','Held-out control'),data:bs.map((b,i)=>({x:b*1e-9,y:ys[i]}))});}return plans+plot(curves,'b / 10⁹ s m⁻²','S / S₀')+(m.heldoutRanking?table([t('Modelo','Model'),t('Error en datos reservados','Held-out error')],m.heldoutRanking.map(r=>[r.id,fmt(r.rms??r.residualRms??r.sse,5)])):'');}
   function spatialMetrics(s){return `<div class="rs-metrics">${metric(t('Resolución nominal / mm','Nominal resolution / mm'),fmt(s.metrics.nominalSpatialResolutionMm))}${metric(t('Desplazamiento RMS / µm','RMS displacement / µm'),fmt(s.metrics.diffusionRmsUm))}${metric(t('Barrido RF / Hz','RF sweep / Hz'),fmt(s.metrics.rfSweepBandwidthHz))}${metric(t('Máxima norma |M|','Maximum |M|'),fmt(s.metrics.maxBlochNorm))}</div>${(s.diagnostics.warnings||[]).map(w=>`<div class="rs-review">${esc(loc(w))}</div>`).join('')}<p class="rs-caption">${t('Integral física durante RF: no es el b de DOSY.','Physical integral during RF: not DOSY b.')}</p>`;}
   function convergenceMetrics(c){const e=c.errors;return table([t('Observable','Observable'),t('Refinar tiempo','Refine time'),t('Refinar espacio','Refine space')],[[t('Magnetización','Magnetisation'),fmt(e.timeMagnetizationRelative*100)+' %',fmt(e.spaceMagnetizationRelative*100)+' %'],[t('Lectura','Readout'),fmt(e.timeReadoutRelative*100)+' %',fmt(e.spaceReadoutRelative*100)+' %']])+`<p class="rs-caption">${t('La sensibilidad depende del observable. Una lectura convergente no garantiza que cada detalle del perfil espacial lo esté.','Sensitivity depends on the observable. Converged readout does not ensure every detail of the spatial profile is converged.')}</p>`;}
   function reviewMetrics(r){return `<article class="rs-review"><h4>${t('Devolución humana','Human feedback')} · ${t('entrega','submission')} ${r.submissionRevision}</h4>${table([t('Criterio','Criterion'),t('Puntuación','Score'),t('Comentario','Feedback')],rubricNames.map(id=>[criterionLabel(id),(r.scores?.[id]??'—')+' / 4',r.comments?.[id]||'']))}${(r.questions||[]).map(q=>`<p>${esc(q)}</p>`).join('')}</article>`;}
'''
 if 'function uncertaintyMetrics(' not in s:s=s.replace('   function introQuestion(text)',helpers+'   function introQuestion(text)',1)
 P.write_text(s,encoding='utf-8')
 print('Readable bilingual scientific results, retained parameters and feedback ready')


if __name__=='__main__':main()
