from pathlib import Path
P=Path(__file__).resolve().parents[1]/'web/research-studio.js'


def main():
 s=P.read_text(encoding='utf-8')
 changes=[
  ("ready=false,message='',error=false,working=false,worker=null;", "ready=false,message='',error=false,working=false,worker=null,workerReject=null,spatialFrame=0,spatialTimer=null;"),
  ("samples:120", "samples:120"),
  ("t('Dificultad oculta','Hidden difficulty')", "t('Escenario de práctica','Practice scenario')"),
  ("const u=caseState.uncertainty;return card", "const u=caseState.uncertainty,up=u?.parameters||{};return card"),
  ("'),120,'','min=\"30\"", "'),up.samples||120,'','min=\"30\""),
  ("'),.02,'fraction')", "'),up.gradientRelativeSd??.02,t('fracción','fraction'))"),
  ("'),.3,'K')}${number('processingRelativeSd'", "'),up.temperatureSdK??.3,'K')}${number('processingRelativeSd'"),
  ("'),.01,'fraction')}${number('noiseRelativeSd'", "'),up.processingRelativeSd??.01,t('fracción','fraction'))}${number('noiseRelativeSd'"),
  ("'),.01,'fraction')}${number('sequenceRelativeSd'", "'),up.noiseRelativeSd??.01,t('fracción','fraction'))}${number('sequenceRelativeSd'"),
  ("'),.01,'fraction')}</div><div class=\"rs-toolbar\">${button('uncertainty'", "'),up.sequenceRelativeSd??.01,t('fracción','fraction'))}</div><div class=\"rs-toolbar\">${button('uncertainty'"),
  ("d.coilVariation,'fraction')", "d.coilVariation,t('fracción','fraction'))"),
  ("${convergence?convergenceMetrics(convergence):''}<p class=\"rs-scope\">", "${convergence?convergenceMetrics(convergence):''}${s?`<h4>${t('Evolución calculada','Calculated evolution')}</h4><div data-spatial-timeline>${timelinePlot()}</div><label>${t('Instante del programa','Programme time')}<input type=\"range\" data-field=\"spatial-frame\" min=\"0\" max=\"${s.snapshots.length-1}\" value=\"${spatialFrame}\" step=\"1\"></label><div class=\"rs-toolbar\">${button('play-spatial','Reproducir / pausar','Play / pause')}</div>`:''}<p class=\"rs-scope\">"),
  ("worker=new Worker('spatial-worker.js');worker.onmessage=", "workerReject=reject;worker=new Worker('spatial-worker.js');worker.onmessage="),
  ("worker?.terminate();worker=null;e.data.ok?", "worker?.terminate();worker=null;workerReject=null;e.data.ok?"),
  ("if(mode==='convergence')convergence=result;else spatial=result;", "if(mode==='convergence')convergence={errors:result.errors,interpretation:result.interpretation};else{spatial=result;spatialFrame=0;}"),
  ("}finally{working=false;worker?.terminate();worker=null;render();}}", "}catch(e){if(e.name==='AbortError'){message=t('Cálculo cancelado.','Calculation cancelled.');}else throw e;}finally{working=false;worker?.terminate();worker=null;workerReject=null;render();}}"),
  ("else if(name==='cancel-spatial'){worker?.terminate();worker=null;working=false;message=t('Cálculo cancelado.','Calculation cancelled.');}", "else if(name==='cancel-spatial'){worker?.terminate();worker=null;const reject=workerReject;workerReject=null;reject?.(new DOMException('Cancelled','AbortError'));working=false;message=t('Cálculo cancelado.','Calculation cancelled.');}"),
  ("async function change(e){const el=e.target;if(!el.files?.length)return;", "async function change(e){const el=e.target;if(el.dataset.field==='spatial-frame'){spatialFrame=Number(el.value);const target=container.querySelector('[data-spatial-timeline]');if(target)target.innerHTML=timelinePlot();return;}if(!el.files?.length)return;"),
  ("else if(name==='export'){save();", "else if(name==='play-spatial'){if(spatialTimer){clearInterval(spatialTimer);spatialTimer=null;}else spatialTimer=setInterval(()=>{if(!alive||active!=='spatial'||!spatial){clearInterval(spatialTimer);spatialTimer=null;return;}spatialFrame=(spatialFrame+1)%spatial.snapshots.length;const target=container.querySelector('[data-spatial-timeline]');if(target)target.innerHTML=timelinePlot();const slider=field('spatial-frame');if(slider)slider.value=spatialFrame;},450);return;}\n     else if(name==='export'){save();"),
  ("pilotController=null;worker?.terminate();container.removeEventListener", "pilotController=null;worker?.terminate();workerReject?.(new DOMException('Closed','AbortError'));clearInterval(spatialTimer);container.removeEventListener"),
 ]
 for old,new in changes:
  if old==new or new in s:continue
  if s.count(old)!=1:raise ValueError('Interaction anchor '+old[:75]+' count '+str(s.count(old)))
  s=s.replace(old,new,1)
 marker='   function sourceLinks(sources)'
 timeline=r'''   function timelinePlot(){if(!spatial?.snapshots?.length)return '';const frame=spatial.snapshots[Math.max(0,Math.min(spatialFrame,spatial.snapshots.length-1))];return `<p class="rs-caption">t = ${fmt(frame.timeMs)} ms · ${esc(({rf:t('RF chirp','RF chirp'),evolve:t('Difusión y relajación','Diffusion and relaxation'),readout:t('Lectura','Readout')})[frame.kind]||frame.kind)}</p>`+plot([{name:'Mx',data:spatial.zMm.map((x,i)=>({x,y:frame.mx[i]}))},{name:'My',data:spatial.zMm.map((x,i)=>({x,y:frame.my[i]}))},{name:'Mz',data:spatial.zMm.map((x,i)=>({x,y:frame.mz[i]}))}],'z / mm','M / M₀');}
'''
 if 'function timelinePlot(' not in s:s=s.replace(marker,timeline+marker,1)
 # Show correlations as a matrix, not as an unlabelled numeric dump.
 old="+`<p class=\"rs-caption\">${t('Ajustes Monte Carlo en el límite'"
 new="+table([t('Correlación entre ventanas','Between-window correlation'),'Σ','1','2'],(u.correlation||[]).map((r,i)=>[[t('Ambas','Both'),'1','2'][i]||String(i),...r.map(v=>fmt(v,3))]))+`<p class=\"rs-caption\">${t('Ajustes Monte Carlo en el límite'"
 if old in s:s=s.replace(old,new,1)
 P.write_text(s,encoding='utf-8')
 print('Animation, Monte Carlo form persistence, correlation matrix and cancellation ready')


if __name__=='__main__':main()
