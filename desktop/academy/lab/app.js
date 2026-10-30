/* Local, deterministic educational animation player. No network/API requests. */
(function () {
  'use strict';
  const ids = ['brownian','spin-echo','gradients-b','attenuation-mixture','pulse-90','acquisition-window','convection','overlap-joint','ilt','ultrafast','dt2','spen','time-resolved','restricted','exchange','anisotropy','prototype-1d'];
  const $ = id => document.getElementById(id);
  const duration = 18;
  const paramsByScene = {};
  const fallback = ids.map((id,i) => ({id,title:{es:id,en:id},question:{es:'Explora el mecanismo',en:'Explore the mechanism'},summary:{es:'Simulación didáctica',en:'Educational simulation'},limits:{es:[],en:[]},references:[],equation:'',terms:[]}));
  const catalog = window.DiffusionCatalog?.scenes || fallback;
  const state = {scene:ids[0],lang:'es',time:0,playing:false,last:0,recording:null,cleanupRecording:null};
  const cnv=$('motion-canvas'),ctx=cnv.getContext('2d');
  const ec=$('export-canvas'),ex=ec.getContext('2d');
  const ui = {
    'offline-label':['Sin conexión · reproducible','Offline · reproducible'],
    'intro-eyebrow':['DEL MOVIMIENTO AL MAPA','FROM MOTION TO A MAP'],
    'intro-title':['La difusión se mueve.<br>La RMN la codifica.','Diffusion moves.<br>NMR encodes it.'],
    'intro-copy':['Explora lo que sucede entre un gradiente y un mapa DOSY. Cambia los parámetros. Observa dónde se pierde información.','Explore what happens between a gradient and a DOSY map. Change the parameters. See where information is lost.'],
    'library-label':[ids.length+' experimentos visuales',ids.length+' visual experiments'],
    'library-toggle':['Explorar todas las escenas','Explore all scenes'],
    'skip-link':['Saltar al experimento','Skip to experiment'],
    'guide-link':['Guía de las simulaciones','Simulation guide'],
    'featured-eyebrow':['SIMULACIONES CALCULADAS · v2','COMPUTED SIMULATIONS · v2'],
    'featured-title':['De la señal al resultado.','From signal to result.'],
    'featured-spen':['Señal compleja → reconstrucción → D','Complex signal → reconstruction → D'],
    'featured-tr-title':['Difusión resuelta en el tiempo','Time-resolved diffusion'],
    'featured-tr':['La muestra cambia mientras medimos','The sample changes while we measure'],
    'featured-uf':['Codificación espacial → perfil → D','Spatial encoding → profile → D'],
    'results-eyebrow':['RESULTADOS DEL MODELO','MODEL RESULTS'],
    'results-title':['Compara el valor conocido con el recuperado.','Compare known and recovered values.'],
    'calculated-label':['CALCULADO','COMPUTED'],
    'simulation-label':['SIMULACIÓN DIDÁCTICA','EDUCATIONAL SIMULATION'],
    'time-label':['Progreso de la animación / s','Animation progress / s'],'controls-heading':['Cambia el experimento','Change the experiment'],
    'reset-btn':['Restablecer','Reset parameters'],'question-label':['LA PREGUNTA','THE QUESTION'],
    'limits-label':['QUÉ REPRESENTA EL MODELO','WHAT THE MODEL REPRESENTS'],
    'sources-label':['Fuentes científicas','Scientific sources'],
    'download-label':['Llévalo a tu presentación','Take it to your presentation'],
    'download-copy':['Vídeos MP4 en ambos idiomas y una imagen de la escena actual.','MP4 videos in both languages and a still image of the current scene.'],
    'record-btn':['Grabar WebM','Record WebM'],
    'historical-label':['Ejemplo aportado: mapa D–T₂ histórico','Supplied example: historical D–T₂ map'],
    'historical-copy':['Figura aportada previamente por el usuario. Es un resultado histórico, distinto de estas simulaciones y de la validación del prototipo actual.','Figure previously supplied by the researcher. It is a historical result, distinct from these simulations and from validation of the current prototype.'],
    'provenance-link':['Procedencia de la imagen','Image provenance'],
    'footer-copy':['Movimiento ilustrativo; señales y mapas simulados. No se modifican datos experimentales ni calibraciones.','Illustrative motion; simulated signals and maps. No experimental data or calibrations are modified.']
  };
  const tr = (es,en) => state.lang==='es'?es:en;
  const groupLabels = [
    {i:0,es:'01 / Movimiento y codificación',en:'01 / Motion and encoding'},
    {i:4,es:'02 / Medir es difícil',en:'02 / Measurement is difficult'},
    {i:7,es:'03 / Reconstruir la información',en:'03 / Reconstructing information'},
    {i:9,es:'04 / Codificación espacial',en:'04 / Spatial encoding'},
    {i:12,es:'05 / Observar una muestra que cambia',en:'05 / Watching a changing sample'},
    {i:13,es:'06 / Más allá del modelo simple',en:'06 / Beyond the simple model'}
  ];
  const sceneData = id => catalog.find(s=>s.id===id) || fallback.find(s=>s.id===id);
  function controlsFor(id) {return window.QuantitativeScenes?.controls?.[id] || window.AdvancedScenes?.controls?.[id] || window.MotionScenes?.controls?.[id] || [];}
  function defaultsFor(id) {
    return Object.fromEntries(controlsFor(id).map(c=>[c.id,c.value]));
  }
  function parameters(id) {if(!paramsByScene[id])paramsByScene[id]=defaultsFor(id);return paramsByScene[id];}
  function finite(value,name) {const n=Number(value);if(!Number.isFinite(n))throw new TypeError(name+' must be finite');return n;}
  function controlNumber(value,definition) {const [mantissa,exponent='0']=String(definition.step).split('e');const decimals=Math.max(0,(mantissa.split('.')[1]||'').length-Number(exponent));return Number(value).toFixed(Math.min(8,decimals));}
  function normalizedParams(id,overrides={}) {
    if(!overrides||typeof overrides!=='object'||Array.isArray(overrides))throw new TypeError('params must be an object');
    const defs=controlsFor(id),p=defaultsFor(id);
    for(const [key,value] of Object.entries(overrides)){const d=defs.find(c=>c.id===key);if(!d)throw new RangeError('Unknown parameter: '+key);p[key]=Math.max(d.min,Math.min(d.max,finite(value,key)));}
    return p;
  }
  function checkedLanguage(lang) {if(!['es','en'].includes(lang))throw new RangeError('Supported languages: es, en');return lang;}
  function quantitativeModel(id,p) {const names={spen:'spen',ultrafast:'ultrafast','time-resolved':'timeResolved'};return names[id]&&window.DiffusionModels?.[names[id]]?.(p);}
  function updateResults() {
    const report=window.QuantitativeScenes?.diagnostics?.(state.scene,parameters(state.scene));
    $('model-results').hidden=!report;$('csv-btn').hidden=!report;
    $('result-metrics').replaceChildren();$('result-notes').replaceChildren();
    if(!report)return;
    for(const m of report.metrics||[]){const box=document.createElement('div');box.className='result-metric';box.dataset.kind=m.kind||'estimate';const label=document.createElement('span');label.className='metric-label';label.textContent=m.label?.[state.lang]||'';const value=document.createElement('strong');const digits=m.digits??3;const rounded=Math.abs(m.value)<0.5*Math.pow(10,-digits)?0:m.value;value.textContent=Number.isFinite(m.value)?Number(rounded).toFixed(digits):tr('No estimable','Not estimable');const unit=document.createElement('span');unit.className='metric-unit';unit.textContent=m.unit||'';box.append(label,value,unit);$('result-metrics').append(box);}
    for(const note of report.notes?.[state.lang]||[]){const li=document.createElement('li');li.textContent=note;$('result-notes').append(li);}
  }
  function wrap(c,text,x,y,width,lineHeight,maxLines=4) {
    const words=String(text).split(' '); let row='',line=0;
    words.forEach(word=>{const test=row?row+' '+word:word;if(c.measureText(test).width>width&&row){if(line<maxLines)c.fillText(row,x,y+line*lineHeight);line++;row=word;}else row=test;});
    if(line<maxLines)c.fillText(row,x,y+line*lineHeight);
    return Math.min(line+1,maxLines)*lineHeight;
  }
  function paint(target,c,id,t,p,lang,w,h) {
    const s=sceneData(id),idx=ids.indexOf(id);
    const small=w<600,scale=w/1440,head=small?140:Math.max(94,122*scale),foot=small?145:Math.max(100,110*scale);
    c.setTransform(1,0,0,1,0,0);c.textAlign='left';c.textBaseline='alphabetic';c.globalAlpha=1;c.setLineDash([]);c.clearRect(0,0,w,h);c.fillStyle='#07131f';c.fillRect(0,0,w,h);
    const glow=c.createRadialGradient(w*.75,h*.25,0,w*.75,h*.25,w*.9);glow.addColorStop(0,'#123049');glow.addColorStop(1,'#07131f');c.fillStyle=glow;c.fillRect(0,0,w,h);
    const pad=small?19:Math.max(26,42*scale);
    c.fillStyle='#9cc3d7';c.font=`600 ${small?10:Math.max(10,13*scale)}px "Segoe UI",sans-serif`;
    c.fillText('DIFFATONCE / MOTION LAB',pad,small?25:30*scale+6);
    c.textAlign='right';c.fillStyle='#a6e7dd';c.fillText(lang==='es'?'SIMULACIÓN':'SIMULATION',w-pad,small?25:30*scale+6);c.textAlign='left';
    c.fillStyle='#e8f6ff';c.font=`600 ${small?22:Math.max(24,36*scale)}px "Segoe UI",sans-serif`;
    wrap(c,s.title?.[lang]||id,pad,small?61:72*scale+5,w-pad*2,small?27:43*scale,2);
    c.save();c.translate(0,head);const bodyScale=Math.max(1,w/1280);c.scale(bodyScale,bodyScale);window.DiffusionRenderScale=bodyScale;const bodyW=w/bodyScale,bodyH=(h-head-foot)/bodyScale;
    const handled=window.QuantitativeScenes?.render(c,id,t,p,lang,bodyW,bodyH)||window.ThreeScenes?.render(c,id,t,p,lang,bodyW,bodyH)||window.AdvancedScenes?.render(c,id,t,p,lang,bodyW,bodyH);
    if(!handled) {
      if(window.MotionScenes)window.MotionScenes.render(c,id,t,p,lang,bodyW,bodyH);
      else{c.fillStyle='#b7d8ea';c.font='20px sans-serif';c.fillText('Preparing scenes…',pad,70);}
    }
    c.restore();c.textAlign='left';c.textBaseline='alphabetic';c.globalAlpha=1;c.setLineDash([]);
    c.strokeStyle='#294553';c.lineWidth=1;c.beginPath();c.moveTo(pad,h-foot);c.lineTo(w-pad,h-foot);c.stroke();
    c.fillStyle='#afcbdc';c.font=`${small?11:Math.max(11,15*scale)}px "Segoe UI",sans-serif`;
    const parameterText=controlsFor(id).slice(0,4).map(d=>`${d.label?.[lang]||d.id} ${controlNumber(p[d.id]??d.value,d)} ${d.unit||''}`).join('   ·   ');
    wrap(c,parameterText||s.question?.[lang]||'',pad,h-foot+25,w-pad*2,18,small?2:1);
    c.fillStyle='#829faf';c.font=`${small?11:Math.max(11,13*scale)}px "Segoe UI",sans-serif`;
    wrap(c,s.equationConditions?.[lang]||'',pad,h-foot+(small?66:49),w-pad*2,17,2);
    c.fillStyle='#7193a7';c.font=`${small?10:Math.max(10,12*scale)}px "Segoe UI",sans-serif`;
    c.fillText(lang==='es'?'Esquema pedagógico · no es una secuencia ejecutable':'Educational schematic · not an executable pulse sequence',pad,h-17);
    if(!small){c.textAlign='right';c.fillText(`${String(idx+1).padStart(2,'0')} / ${ids.length}   ·   ${Math.min(duration,Math.max(0,t)).toFixed(1)} s`,w-pad,h-17);c.textAlign='left';}
    c.fillStyle='#36566c';c.fillRect(0,h-3,w,3);c.fillStyle='#53d4ff';c.fillRect(0,h-3,w*Math.min(1,t/duration),3);
    return {phase:Math.min(1,t/duration),scene:id,language:lang,parameters:Object.assign({},p)};
  }
  function draw() {
    const w=Math.max(300,Math.round(cnv.parentElement.clientWidth));
    const h=window.QuantitativeScenes?.controls?.[state.scene]&&w<750?1100:w<600?1000:Math.round(w*.61+100);
    const dpr=Math.min(2,window.devicePixelRatio||1);
    if(cnv.width!==Math.round(w*dpr)||cnv.height!==Math.round(h*dpr)){cnv.width=Math.round(w*dpr);cnv.height=Math.round(h*dpr);cnv.style.height=h+'px';}
    // Render at physical resolution through an intermediate logical canvas.
    if(!draw.buffer)draw.buffer=document.createElement('canvas');
    const buffer=draw.buffer;if(buffer.width!==w||buffer.height!==h){buffer.width=w;buffer.height=h;}
    paint(buffer,buffer.getContext('2d'),state.scene,state.time,parameters(state.scene),state.lang,w,h);
    ctx.setTransform(1,0,0,1,0,0);ctx.clearRect(0,0,cnv.width,cnv.height);ctx.drawImage(buffer,0,0,cnv.width,cnv.height);
    $('time-slider').value=state.time;$('time-output').textContent=state.time.toFixed(1)+' / 18.0 s';
  }
  function setPlay(on) {state.playing=on;state.last=0;$('play-btn').textContent=on?tr('Ⅱ Pausar','Ⅱ Pause'):tr('▶ Reproducir','▶ Play');$('play-btn').setAttribute('aria-pressed',String(on));}
  function navigate(id,{keepTime=false}={}) {
    if(state.recording)return;
    if(!ids.includes(id))return;state.scene=id;if(!keepTime)state.time=0;setPlay(false);$('record-status').textContent='';parameters(id);updateUI();draw();
    const url=new URL(location.href);url.searchParams.set('scene',id);url.searchParams.set('lang',state.lang);history.replaceState(null,'',url);
  }
  function updateUI() {
    document.documentElement.lang=state.lang;
    $('guide-link').href='GUIDE_V2_'+state.lang.toUpperCase()+'.md';
    for(const [id,text] of Object.entries(ui)){if(id==='intro-title')$(id).innerHTML=text[state.lang==='es'?0:1];else $(id).textContent=text[state.lang==='es'?0:1];}
    $('lang-btn').textContent=state.lang==='es'?'EN ↗':'ES ↗';
    $('lang-btn').setAttribute('aria-label',tr('Cambiar a inglés','Switch to Spanish'));
    $('scene-list').setAttribute('aria-label',tr('Biblioteca de simulaciones','Simulation library'));
    $('stage').setAttribute('aria-label',tr('Animación y controles de reproducción','Animation and playback controls'));
    $('scenario-presets').setAttribute('aria-label',tr('Escenarios de simulación','Simulation scenarios'));
    document.querySelector('.historical-example img').alt=tr('Mapa D–T₂ histórico aportado por el investigador','Historical D–T₂ map supplied by the researcher');
    $('scene-list').replaceChildren();ids.forEach((id,i)=>{
      const group=groupLabels.find(g=>g.i===i);if(group){const label=document.createElement('div');label.className='library-group';label.textContent=group[state.lang];$('scene-list').append(label);}
      const button=document.createElement('button');button.type='button';button.className='scene-nav'+(id===state.scene?' active':'');button.setAttribute('aria-current',id===state.scene?'true':'false');
      const number=document.createElement('span');number.textContent=String(i+1).padStart(2,'0');const text=document.createElement('strong');text.textContent=sceneData(id).title?.[state.lang]||id;button.append(number,text);button.addEventListener('click',()=>navigate(id));$('scene-list').append(button);
    });
    const s=sceneData(state.scene);$('scene-title').textContent=s.title?.[state.lang]||s.id;
    $('chapter-label').textContent=groupLabels.slice().reverse().find(g=>g.i<=ids.indexOf(s.id))[state.lang];
    $('scene-question').textContent=s.question?.[state.lang]||'';$('scene-summary').textContent=s.summary?.[state.lang]||'';$('scene-equation').textContent=typeof s.equation==='string'?s.equation:(s.equation?.[state.lang]||'');$('equation-conditions').textContent=s.equationConditions?.[state.lang]||'';
    $('equation-terms').replaceChildren();(s.terms||[]).forEach(term=>{const dt=document.createElement('dt');dt.textContent=term.symbol;const dd=document.createElement('dd');dd.textContent=(term[state.lang]||term.description?.[state.lang]||'')+(term.unit?' / '+term.unit:'');$('equation-terms').append(dt,dd);});
    $('scene-limits').replaceChildren();(s.limits?.[state.lang]||[]).forEach(text=>{const li=document.createElement('li');li.textContent=text;$('scene-limits').append(li);});
    $('scene-sources').replaceChildren();(s.references||[]).forEach(ref=>{const li=document.createElement('li');const a=document.createElement('a');a.href=ref.url;a.textContent=ref.title||ref.id;a.target='_blank';a.rel='noopener';li.append(a);$('scene-sources').append(li);});
    $('parameter-controls').replaceChildren();controlsFor(state.scene).forEach(d=>{
      const label=document.createElement('label');label.className='parameter';const title=document.createElement('span');title.className='parameter-title';const name=document.createElement('span');name.textContent=d.label?.[state.lang]||d.id;const out=document.createElement('output');const input=document.createElement('input');input.type='range';input.id='param-'+d.id;out.setAttribute('for',input.id);input.setAttribute('aria-label',(d.label?.[state.lang]||d.id)+' / '+(d.unit||''));input.min=d.min;input.max=d.max;input.step=d.step;input.value=parameters(state.scene)[d.id]??d.value;const val=()=>out.textContent=controlNumber(input.value,d)+' '+(d.unit||'');val();input.addEventListener('input',()=>{parameters(state.scene)[d.id]=Number(input.value);val();$('scenario-presets').querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed','false'));updateResults();draw();});title.append(name,out);label.append(title,input);$('parameter-controls').append(label);
    });
    $('scenario-presets').replaceChildren();(window.QuantitativeScenes?.presets?.[state.scene]||[]).forEach(preset=>{const button=document.createElement('button');button.type='button';button.textContent=preset.label[state.lang];const same=Object.entries(preset.params).every(([key,v])=>parameters(state.scene)[key]===v);button.setAttribute('aria-pressed',String(same));button.addEventListener('click',()=>{paramsByScene[state.scene]=normalizedParams(state.scene,preset.params);updateUI();draw();});$('scenario-presets').append(button);});
    $('video-es').href='videos/'+s.id+'_ES.mp4';$('video-en').href='videos/'+s.id+'_EN.mp4';
    const revised=!!window.QuantitativeScenes?.controls?.[s.id];$('video-es').hidden=s.id==='time-resolved';$('video-en').hidden=s.id==='time-resolved';
    $('video-es').textContent=revised?tr('Esquema v1 · ES ↓','v1 schematic · ES ↓'):'MP4 · ES ↓';$('video-en').textContent=revised?tr('Esquema v1 · EN ↓','v1 schematic · EN ↓'):'MP4 · EN ↓';
    $('download-copy').textContent=revised?tr('CSV: señal sintética calculada. PNG y WebM: simulación actual con tus parámetros. Los MP4 v1 conservan el esquema anterior.','CSV: computed synthetic signal. PNG and WebM: current simulation with your parameters. v1 MP4 files retain the earlier schematic.'):tr('Vídeos MP4 en ambos idiomas y una imagen de la escena actual.','MP4 videos in both languages and a still image of the current scene.');
    if(s.id==='time-resolved')$('download-copy').textContent=tr('CSV: serie sintética calculada. Exporta PNG o graba un WebM de esta simulación con tus parámetros.','CSV: computed synthetic time series. Export a PNG or record this simulation with your parameters as WebM.');
    updateResults();
    cnv.setAttribute('aria-label',(s.title?.[state.lang]||s.id)+'. '+(s.summary?.[state.lang]||''));
    $('prev-btn').setAttribute('aria-label',tr('Escena anterior','Previous scene'));$('next-btn').setAttribute('aria-label',tr('Escena siguiente','Next scene'));$('restart-btn').setAttribute('aria-label',tr('Reiniciar animación','Restart animation'));$('fullscreen-btn').setAttribute('aria-label',tr('Pantalla completa','Full screen'));setPlay(state.playing);
  }
  function downloadBlob(blob,name) {const a=document.createElement('a');const u=URL.createObjectURL(blob);a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),10000);}
  function frame(now) {
    if(state.playing){if(state.last)state.time=Math.min(duration,state.time+(now-state.last)/1000);state.last=now;draw();if(state.recording)paint(ec,ex,state.scene,state.time,parameters(state.scene),state.lang,ec.width,ec.height);if(state.time>=duration){setPlay(false);if(state.recording)state.recording.stop();}}
    requestAnimationFrame(frame);
  }
  $('play-btn').addEventListener('click',()=>{if(state.time>=duration)state.time=0;setPlay(!state.playing);draw();});
  $('restart-btn').addEventListener('click',()=>{state.time=0;draw();});
  $('prev-btn').addEventListener('click',()=>navigate(ids[(ids.indexOf(state.scene)+ids.length-1)%ids.length]));
  $('next-btn').addEventListener('click',()=>navigate(ids[(ids.indexOf(state.scene)+1)%ids.length]));
  $('time-slider').addEventListener('input',e=>{setPlay(false);state.time=Number(e.target.value);draw();});
  $('reset-btn').addEventListener('click',()=>{paramsByScene[state.scene]=defaultsFor(state.scene);updateUI();draw();});
  document.querySelectorAll('[data-open-scene]').forEach(button=>button.addEventListener('click',()=>{navigate(button.dataset.openScene);$('main-content').scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});}));
  $('csv-btn').addEventListener('click',()=>{const model=quantitativeModel(state.scene,parameters(state.scene));if(!model?.rows?.length)return;const keys=[...new Set(model.rows.flatMap(row=>Object.keys(row)))];const cell=v=>'"'+String(v??'').replaceAll('"','""')+'"';const csv=[keys.map(cell).join(','),...model.rows.map(row=>keys.map(key=>cell(row[key])).join(','))].join('\r\n');downloadBlob(new Blob(['\ufeff'+csv],{type:'text/csv;charset=utf-8'}),state.scene+'_synthetic_v2.csv');$('record-status').textContent=tr('CSV de señales sintéticas descargado. Unidades en las cabeceras.','Synthetic-signal CSV downloaded. Units are included in column headers.');});
  $('lang-btn').addEventListener('click',()=>{state.lang=state.lang==='es'?'en':'es';navigate(state.scene,{keepTime:true});});
  $('fullscreen-btn').addEventListener('click',async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await $('stage').requestFullscreen();}catch(e){$('record-status').textContent=tr('El navegador no permite pantalla completa.','This browser does not allow full screen.');}});
  $('png-btn').addEventListener('click',()=>{ec.width=1920;ec.height=1080;paint(ec,ex,state.scene,state.time,parameters(state.scene),state.lang,1920,1080);ec.toBlob(blob=>{if(blob)downloadBlob(blob,state.scene+'_'+state.lang.toUpperCase()+'.png');},'image/png');});
  $('record-btn').addEventListener('click',()=>{
    if(state.recording){try{state.recording.stop();}catch(e){state.cleanupRecording?.(true);}setPlay(false);return;}
    if(!window.MediaRecorder||!ec.captureStream){$('record-status').textContent=tr('Este navegador no admite grabación. Usa los MP4.','Recording is unsupported in this browser. Use the MP4 files.');return;}
    const mime=['video/webm;codecs=vp9','video/webm;codecs=vp8','video/webm'].find(m=>MediaRecorder.isTypeSupported(m));
    if(!mime){$('record-status').textContent=tr('No hay un codificador WebM disponible.','No WebM encoder is available.');return;}
    const id=state.scene,lang=state.lang,chunks=[];let failed=false,stream,recorder,cleaned=false;
    const lockedControls=[...$('scene-list').querySelectorAll('button'),...$('parameter-controls').querySelectorAll('input'),...$('scenario-presets').querySelectorAll('button'),...document.querySelectorAll('[data-open-scene]'),...['lang-btn','play-btn','prev-btn','next-btn','restart-btn','reset-btn','time-slider','png-btn','csv-btn'].map($)];
    const cleanup=(error=false)=>{if(cleaned)return;cleaned=true;failed=failed||error;stream?.getTracks().forEach(track=>track.stop());state.recording=null;state.cleanupRecording=null;setPlay(false);lockedControls.forEach(el=>el.disabled=false);$('record-btn').textContent=tr('Grabar WebM','Record WebM');if(!failed&&chunks.length){downloadBlob(new Blob(chunks,{type:'video/webm'}),id+'_'+lang.toUpperCase()+'_custom_v2.webm');$('record-status').textContent=tr('Vídeo descargado; no incluye audio.','Video downloaded; no audio included.');}else{$('record-status').textContent=tr('La grabación no pudo completarse. Puedes exportar la imagen PNG.','Recording could not complete. You can export the PNG image.');}draw();};
    try{ec.width=1920;ec.height=1080;state.time=0;paint(ec,ex,id,0,parameters(id),lang,1920,1080);stream=ec.captureStream(24);recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:7000000});state.recording=recorder;state.cleanupRecording=cleanup;
      recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data);};recorder.onerror=()=>{failed=true;if(recorder.state!=='inactive'){try{recorder.stop();}catch(e){cleanup(true);}}else cleanup(true);};recorder.onstop=()=>cleanup();
      lockedControls.forEach(el=>el.disabled=true);$('record-btn').textContent=tr('■ Detener grabación','■ Stop recording');$('record-status').textContent=tr('Grabando 18 s con tus parámetros. Mantén esta pestaña activa.','Recording 18 s with your parameters. Keep this tab active.');recorder.start();setPlay(true);
    }catch(e){cleanup(true);}
  });
  document.addEventListener('keydown',e=>{if(['INPUT','TEXTAREA','SELECT','BUTTON','A','SUMMARY'].includes(document.activeElement?.tagName))return;if(e.code==='Space'){e.preventDefault();$('play-btn').click();}if(e.key==='ArrowRight')$('next-btn').click();if(e.key==='ArrowLeft')$('prev-btn').click();});
  window.addEventListener('resize',draw);
  window.DiffusionMotion={
    listScenes:()=>ids.map(id=>({id,title:sceneData(id).title})),
    renderFrame:({scene=state.scene,lang='es',time=0,width=1920,height=1080,params={}}={})=>{
      if(!ids.includes(scene))throw new Error('Unknown scene: '+scene);
      if(state.recording)throw new Error('Wait for recording to finish');checkedLanguage(lang);const t=Math.max(0,Math.min(duration,finite(time,'time')));width=Math.round(finite(width,'width'));height=Math.round(finite(height,'height'));if(width<256||height<256||width>4096||height>4096)throw new RangeError('Export dimensions must be 256–4096 px');const scale=width/1440,head=width<600?140:Math.max(94,122*scale),foot=width<600?145:Math.max(100,110*scale);if((height-head-foot)/Math.max(1,width/1280)<(width<750?500:270))throw new RangeError('Export height is too small for the scene layout');const p=normalizedParams(scene,params);ec.width=width;ec.height=height;const metrics=paint(ec,ex,scene,t,p,lang,width,height);return {ready:true,canvasId:'export-canvas',canvasSelector:'#export-canvas',metrics};
    },getState:()=>({scene:state.scene,lang:state.lang,time:state.time,playing:state.playing,params:Object.assign({},parameters(state.scene))}),
    setScene:(id,lang=state.lang)=>{if(!ids.includes(id))throw new RangeError('Unknown scene: '+id);if(state.recording)throw new Error('Wait for recording to finish');state.lang=checkedLanguage(lang);navigate(id);},setTime:t=>{if(state.recording)throw new Error('Wait for recording to finish');const value=finite(t,'time');setPlay(false);state.time=Math.max(0,Math.min(duration,value));draw();},
    getSyntheticData:()=>quantitativeModel(state.scene,parameters(state.scene)),
    scientificStatus:'pedagogical-simulation',version:'2.0',duration
  };
  const query=new URLSearchParams(location.search);if(query.has('export'))document.body.classList.add('export-mode');if(query.has('presentation'))document.body.classList.add('presentation');if(window.matchMedia?.('(max-width:760px)').matches)document.querySelector('.library-browser')?.removeAttribute('open');state.lang=query.get('lang')==='en'?'en':'es';state.scene=ids.includes(query.get('scene'))?query.get('scene'):ids[0];parameters(state.scene);updateUI();draw();requestAnimationFrame(frame);
})();
