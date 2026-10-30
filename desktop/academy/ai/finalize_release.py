"""Close a hybrid local tutor package only after actual CPU evidence passes.
Does not rewrite the completed training/free-generation evaluation or weights.
"""
import hashlib
import json
import shutil
from pathlib import Path
from datetime import datetime,timezone

here=Path(__file__).resolve().parent
release=here/"release"
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda:stream.read(1024*1024),b""):h.update(data)
    return h.hexdigest()

manifest=json.loads((release/"manifest.json").read_text(encoding="utf-8"))
if not manifest.get("NativeEvaluationPending"):raise RuntimeError("Native package already closed; preserve it.")
cpu=json.loads((here/"native-evaluation-v2-hybrid.json").read_text(encoding="utf-8"))
evaluation=json.loads((release/"evaluation_report.json").read_text(encoding="utf-8"))
if not cpu["passed"] or not evaluation["quality_passed"]:raise RuntimeError("Actual CPU or held-out free-generation gate failed.")
if sha(release/"model.gguf")!=manifest["Sha256"]:raise RuntimeError("GGUF changed after conversion.")
for name,key in (("training_report.json","TrainingReportSha256"),("evaluation_report.json","EvaluationReportSha256")):
    if sha(release/name)!=manifest[key]:raise RuntimeError("Completed evidence changed.")
course=json.loads((here.parent/"content/course.json").read_text(encoding="utf-8"))
modules={m["id"]:m for m in course["modules"]}
if sha(here.parent/"content/course.json")!=manifest["CourseSha256"]:raise RuntimeError("Course version changed.")
cases={c["id"]:c for c in cpu["checks"]}
for identifier,module,language in (("native_es_pulse-calibration","pulse-calibration","es"),("native_en_sequence-b","sequence-b","en"),("native_es_spen","spen","es"),("native_en_time-resolved","time-resolved","en")):
    answer=cases[identifier]["detail"]
    expected=modules[module]["why"][language]+"\n\n"+modules[module]["mechanism"][language]
    if not answer["IsModelAnswer"] or not answer["IncludesCourseQuote"] or answer["CourseQuote"]!=expected or not answer["GeneratedText"]:raise RuntimeError("Hybrid source/generated separation is not proven.")
    allowed={s["id"] for s in modules[module]["sources"]}
    if any(s["Id"] not in allowed for s in answer["Sources"]):raise RuntimeError("Unsupported source in hybrid answer.")

for source,target in (("native-evaluation-v2-hybrid.json","native_evaluation_report.json"),("environment_report.json","environment_report.json"),("environment_git_provenance_normalized.json","environment_git_provenance_normalized.json"),("prompt-parity-report.json","prompt-parity-report.json"),("completion-loss-verification.json","completion-loss-verification.json"),("tutor-missing-native-backend-v2.json","missing_native_backend_report.json")):
    shutil.copyfile(here/source,release/target)
history=[]
for filename in ("native-evaluation-v2.json","native-evaluation-v2-focused.json","native-evaluation-v2-anchored.json","native-evaluation-v2-compatible.json"):
    data=json.loads((here/filename).read_text(encoding="utf-8"))
    history.append(dict(file=filename,sha256=sha(here/filename),software_passed=data["passed"],scope=data["scope"],limitations="Earlier probes are preserved. Basic software PASS in the first probe did not demonstrate causal completeness; focused/anchored/compatible probes recorded omission or numeric-guard failures. Final hybrid causal coverage is partly literal course text, not claimed as unconstrained generation."))
(release/"native-probe-history.json").write_text(json.dumps(dict(probes=history,all_original_reports_preserved=True),indent=2),encoding="utf-8")
manifest.update(NativeEvaluationPending=False,NativeEvaluationPassed=True,NativeEvaluationReportSha256=sha(release/"native_evaluation_report.json"),EnvironmentReportSha256=sha(release/"environment_report.json"),AnswerMode="hybrid-reviewed-course-and-local-llm",IncludesLiteralCourseText=True,GeneratedOnlyLimitations=["Open SPEN reconstruction answers can omit Fourier detail.","Open time-resolved answers can describe the model without explicitly explaining the concentration-to-attenuation confound."],TutorSourceSha256=sha(here.parent/"src/DiffAtOnce.Academy.Tutor/TutorService.cs"),Bytes=(release/"model.gguf").stat().st_size,ClosedUtc=datetime.now(timezone.utc).isoformat())
(release/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print(json.dumps(dict(path=str(release),native_checks=len(cpu["checks"]),native_sha256=manifest["NativeEvaluationReportSha256"],manifest_sha256=sha(release/"manifest.json"),hybrid=True,experimental_validation=False)))
