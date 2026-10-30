"""Prepare scoped local PHP changes, with verified backups; no remote writes."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[3]
SITE=ROOT/'website/release'
FILES=['public_html/index.php','diffatonce-app/academy-data.php','diffatonce-app/academy-product.php','diffatonce-app/academy-home.php']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
backup=ROOT/'website/backups/academy-before-v1.2-20261005'
if backup.exists():raise FileExistsError('Preserve the previous local backup; do not repeat this migration.')
records=[]
for name in FILES:
 source=SITE/name;target=backup/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
 if sha(source)!=sha(target):raise ValueError('Backup readback mismatch')
 records.append({'path':name,'bytes':source.stat().st_size,'sha256':sha(source)})
(backup/'SHA256.json').write_text(json.dumps(records,indent=2),'utf-8')
file=SITE/'diffatonce-app/academy-data.php';text=file.read_text('utf-8')
text=text.replace("const ACADEMY_RELEASE = '1.1.0';","const ACADEMY_RELEASE = '1.2.0';").replace("/assets/academy/v1.1.0","/assets/academy/v1.2.0").replace("const ACADEMY_DOWNLOAD = '/downloads/diffatonce-academy-1.1.0-win-x64';","const ACADEMY_DOWNLOAD = '/downloads/diffatonce-academy-1.2.0-win-x64';\nconst ACADEMY_DOWNLOAD_PREVIOUS = '/downloads/diffatonce-academy-1.1.0-win-x64';")
text=text.replace("'en' : 'es'); }","'en' : 'es') . '&view=doctoral'; }")
text=text.replace('function academy_download(): void {',"function academy_download(string $version = '1.2.0'): void {\n    if (!in_array($version, ['1.1.0', '1.2.0'], true)) { http_response_code(404); return; }")
text=text.replace("$name = 'DiffAtOnce-Academy-1.1.0-win-x64.zip';","$name = 'DiffAtOnce-Academy-' . $version . '-win-x64.zip';")
file.write_text(text,'utf-8')
file=SITE/'public_html/index.php';text=file.read_text('utf-8').replace("if ($path===ACADEMY_DOWNLOAD) { academy_download(); exit; }","if ($path===ACADEMY_DOWNLOAD) { academy_download('1.2.0'); exit; }\nif ($path===ACADEMY_DOWNLOAD_PREVIOUS) { academy_download('1.1.0'); exit; }");file.write_text(text,'utf-8')
file=SITE/'diffatonce-app/academy-product.php';text=file.read_text('utf-8')
text=text.replace('/screenshots/academy-web-','/screenshots/doctor-').replace("-overview.png",'-home.png')
section='''
<section class="container section" id="doctoral"><div class="section-head"><div><p class="eyebrow"><?=t('NUEVO · LABORATORIO DOCTORAL','NEW · DOCTORAL LABORATORY')?></p><h2><?=t('Predice. Comprueba. Defiende.','Predict. Check. Defend.')?></h2></div><p><?=t('Nueve actividades enlazan mecanismos físicos, decisiones experimentales y evidencia. Un caso Bruker público te lleva desde el FID hasta una conclusión con límites.','Nine activities connect physical mechanisms, experimental decisions and evidence. A public Bruker case takes you from the FID to a bounded conclusion.')?></p></div><div class="academy-capabilities">
<article><span class="academy-number">01–03</span><h3><?=t('Entender la medida','Understand the measurement')?></h3><p><?=t('Moléculas, fases, suma vectorial y eco sincronizados; constructor de coherencia y93 pasos guiados con predicciones, unidades y cálculos.','Synchronized molecules, phases, vector sums and echo; coherence builder and93 guided steps with predictions, units and calculations.')?></p></article>
<article><span class="academy-number">04–06</span><h3><?=t('Resolver las dificultades','Resolve the difficulties')?></h3><p><?=t('Calibración y presupuesto virtuales, causas ocultas y controles discriminantes. Compara ajustes, regularización ILT, análisis conjunto e incertidumbre condicional.','Virtual calibration and acquisition budget, hidden causes and discriminating controls. Compare fits, ILT regularization, joint analysis and conditional uncertainty.')?></p></article>
<article><span class="academy-number">07–09</span><h3><?=t('Sostener una conclusión','Support a conclusion')?></h3><p><?=t('Procesa16 FID reales con atribución y hashes. Investiga una muestra cambiante con adquisición secuencial y modelos UF/SPEN. Exporta evidencias para evaluación humana.','Process16 real FIDs with attribution and hashes. Investigate a changing sample with sequential acquisition and UF/SPEN models. Export evidence for human assessment.')?></p></article></div><div class="academy-actions"><a class="button" href="<?=e(academy_app_url())?>"><?=t('Abrir el recorrido doctoral','Open the doctoral pathway')?> →</a><a class="button secondary" href="<?=ACADEMY_ASSETS?>/docs/DOCTORAL_MANUAL_<?=lng()==='en'?'EN':'ES'?>.pdf"><?=t('Manual doctoral PDF','Doctoral PDF manual')?> ↓</a></div><p class="academy-product-scope"><?=t('Dato real: Silva, McKay y Junkers, Monash/Figshare, DOI10.26180/33075584.v1, CC BY4.0. La escala b guardada y D ajustada son nominales/condicionales; no constituyen calibración absoluta. Las nuevas pistas son documentales revisadas, sin generación LLM.','Real data: Silva, McKay and Junkers, Monash/Figshare, DOI10.26180/33075584.v1, CC BY4.0. Saved b and fitted D remain nominal/conditional, not absolute calibration. New hints use reviewed documentary content without LLM generation.')?></p></section>
'''
text=text.replace('<section class="container section"><div class="section-head">',section+'<section class="container section"><div class="section-head">',1)
file.write_text(text,'utf-8')
file=SITE/'diffatonce-app/academy-home.php';text=file.read_text('utf-8').replace('24 lecciones, 48 ejemplos y 17 escenas interactivas.','Nueve actividades doctorales,24 lecciones,48 ejemplos y17 escenas interactivas.').replace('24 lessons, 48 examples and 17 interactive scenes.','Nine doctoral activities,24 lessons,48 examples and17 interactive scenes.');file.write_text(text,'utf-8')
print(json.dumps({'localPrepared':True,'published':False,'backedUp':len(records),'backup':str(backup)}))
