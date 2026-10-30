"""Freeze reviewed educational code/data identity after independent software QA.

This is not instrument, experimental or student-efficacy validation.
"""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text('utf-8-sig'))
reports=[
 'qa/doctoral-1.2/physics-independent-qa-final.json',
 'qa/doctoral-1.2/physics-browser-final-r3/browser-qa.json',
 'web/tests/doctoral-inquiry-report.json',
 'web/tests/doctoral-inquiry-browser-qa/doctoral-inquiry-browser-report.json',
 'qa/doctoral-1.2/pedagogy-numerical-qa-final-r2.json',
 'qa/doctoral-1.2/pedagogy-browser-final-r3/browser-qa.json',
 'qa/doctoral-1.2/browser-integrated-final/integrated-qa.json',
 'qa/doctoral-1.2/browser-regression-final/browser-qa.json',
 'qa/doctoral-1.2/inquiry-independent-review.json'
]
checked=[]
for name in reports:
 obj=read(ROOT/name)
 if obj.get('failed',0) or obj.get('passed') is False or any(c.get('passed') is False for c in obj.get('checks',[])):
  raise ValueError('QA has failures: '+name)
 checked.append({'path':name,'sha256':sha(ROOT/name),'passed':obj.get('passed'),'checks':len(obj.get('checks',[]))})
for name,expected in {'content/course.json':'f9a17df9645b541abc70907e5d04cd38c213293443ce1d37c2c0d94f8aea0cb9','content/derivations.json':'e07920a25ae8642ffa55a83a75a4db7eb8a6ead09a5c8195ae23ef91d6c9b02e','ai/release-v1.1/manifest.json':'0d51226febb02fe7832de8599698f601d09aa42c2779a2d348c0e71e3b24b1aa'}.items():
 if sha(ROOT/name)!=expected:raise ValueError('Frozen original content/model manifest changed: '+name)
files=[p for p in (ROOT/'web').glob('doctoral-*') if p.suffix in ['.js','.css']]
files += [ROOT/'web/index.html',ROOT/'web/academy.js',ROOT/'content/doctoral-cases.json']
files += [p for p in (ROOT/'content/doctoral-data').rglob('*') if p.is_file()]
files += [ROOT/'src/DiffAtOnce.Academy.App'/n for n in ['DoctoralWindow.cs','MainWindow.xaml','MainWindow.xaml.cs','DiffAtOnce.Academy.App.csproj']]
files += [ROOT/'docs'/('DOCTORAL_MANUAL_'+lang+'.pdf') for lang in ['ES','EN']]
records=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)]
obj={'version':'1.2.0','application':'DiffAtOnce Academy doctoral laboratory','releaseStatus':'reviewed-teaching-software','includedInLLMTraining':False,'hintMode':'reviewed-documentary-only','activities':['sync','sequence','guided','campaign','blind','inverse','cases','advanced','assessment'],'guidedSteps':93,'objectiveTasks':79,'documentaryTasksRequiringHumanReview':14,'numericSubchecks':16,'scope':'Educational software and attributed public experimental data. No instrument operation, absolute calibration, chemical identification or student-efficacy validation claim.','modelBoundaries':{'freeDiffusion':'Unbounded Brownian motion; finite initial slab and uniform detection.','sequence':'Ideal coherence-pathway rectangles and RF transfer factors; no hardware pulse compiler.','convection':'Uniform translation changes phase; velocity distributions can reduce magnitude.','inverse':'Conditional noise/bootstrap, not full systematic uncertainty; joint templates known.','advanced':'Ideal spatial UF and SPEN-inspired point-spread surrogate, not quantitative chirp/Bloch simulation.','realData':'Original public dstegp3s data; saved b and fitted D nominal/conditional; absoluteCalibrationValidated=false.'},'publicDataset':{'doi':'10.26180/33075584.v1','license':'CC BY4.0','rawFilesRetained':True,'archiveSha256':'be65cb5cd54cffdac4ad3b6bca5d90fce175ba652d7127262513eef4e21f5dbc'},'qa':checked,'files':records}
(ROOT/'content/doctoral-manifest.json').write_text(json.dumps(obj,indent=2,ensure_ascii=False),'utf-8')
print(json.dumps({'frozen':True,'files':len(records),'qaReports':len(checked),'sha256':sha(ROOT/'content/doctoral-manifest.json')}))
