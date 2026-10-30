"""Verify final shared runtime, packaged WPF, reviewed data and software QA."""
from pathlib import Path
import argparse,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text('utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('--package',type=Path,required=True);ap.add_argument('--ui-qa',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
if args.output.exists():raise FileExistsError('Preserve earlier verification reports')
checks=[]
def check(name,passed,detail=None):checks.append({'name':name,'passed':bool(passed),'detail':detail})
doc=read(ROOT/'content/doctoral-manifest.json');bundle=read(ROOT/'web/bundle-manifest.json');model=read(ROOT/'ai/release-v1.1/manifest.json')
check('reviewed-nine-activity-doctoral-content',doc['version']=='1.2.0' and doc['releaseStatus']=='reviewed-teaching-software' and len(doc['activities'])==9 and doc['includedInLLMTraining'] is False)
check('shared-web-identity',bundle['version']=='1.2.0' and bundle['doctoralContentSha256']==sha(ROOT/'content/doctoral-manifest.json') and bundle['doctoralHintMode']=='reviewed-documentary-only' and bundle['beatrix'] is False)
for record in doc['files']:
 path=ROOT/record['path'];check('frozen-source:'+record['path'],path.stat().st_size==record['bytes'] and sha(path)==record['sha256'])
for record in doc['qa']:
 path=ROOT/record['path'];obj=read(path);check('reviewed-qa:'+record['path'],sha(path)==record['sha256'] and obj.get('passed') is not False and not obj.get('failed') and all(c.get('passed') is not False for c in obj.get('checks',[])))
for folder in ['Content','Web/content']:
 for name in ['course.json','derivations.json','doctoral-cases.json','doctoral-manifest.json']:
  file=args.package/folder/name;check('packaged:'+folder+'/'+name,file.is_file() and sha(file)==sha(ROOT/'content'/name))
for lang in ['ES','EN']:
 for folder in ['Docs','Web/docs']:
  name='DOCTORAL_MANUAL_'+lang+'.pdf';check('manual:'+folder+'/'+name,sha(args.package/folder/name)==sha(ROOT/'docs'/name))
for name in ['doctoral-hub.js','doctoral-physics.js','doctoral-physics-ui.js','doctoral-inquiry.js','doctoral-inquiry-ui.js','doctoral-pedagogy.js','doctoral-pedagogy-ui.js','academy.js']:
 check('packaged-runtime:'+name,sha(args.package/'Web'/name)==sha(ROOT/'web'/name))
provenance=read(ROOT/'content/doctoral-data/monash-d2o-10/provenance.json')
for folder in ['Content','Web/content']:
 for record in provenance['files']:
  file=args.package/folder/'doctoral-data/monash-d2o-10'/record['path'];check('unchanged-public-raw:'+folder+'/'+record['path'],file.stat().st_size==record['bytes'] and sha(file)==record['sha256'])
check('original-course-model-manifest-unchanged',sha(args.package/'Models/Beatrix/manifest.json')=='0d51226febb02fe7832de8599698f601d09aa42c2779a2d348c0e71e3b24b1aa')
check('actual-original-GGUF-intact',sha(args.package/'Models/Beatrix'/model['File'])==model['Sha256'])
check('no-new-paper-LLM-claim',model['SupplementalIncludedInTraining'] is False and model['SupplementalLLMApproved'] is False and model['SupplementalAnswerMode']=='reviewed-documentary-guide')
ui=read(args.ui_qa);check('actual-packaged-WPF-self-test',ui['applicationVersion']=='1.2.0' and all(c['passed'] for c in ui['checks']),len(ui['checks']))
check('actual-local-Beatrix-inference-covered',any(c['check']=='beatrix_native_wpf' and c['passed'] for c in ui['checks']),[c['check'] for c in ui['checks'] if 'beatrix' in c['check']])
for forbidden in ['research','qa','tests','.git','node_modules']:
 check('no-private-build-directory:'+forbidden,not any(forbidden in p.relative_to(args.package).parts for p in args.package.rglob('*') if p.is_file()))
check('no-private-article-PDFs',not any('private' in p.name.lower() for p in args.package.rglob('*.pdf')))
result={'version':'1.2.0','passed':all(c['passed'] for c in checks),'checks':checks,'counts':{'passed':sum(c['passed'] for c in checks),'total':len(checks)},'scope':'Reviewed teaching software, packaged runtime identity and attributed public data. No instrument, absolute calibration, student-efficacy or production validation.','experimentalValidation':False,'deploymentVerified':False}
args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8');print(json.dumps(result['counts']|{'passed':result['passed']}))
if not result['passed']:raise SystemExit(1)
