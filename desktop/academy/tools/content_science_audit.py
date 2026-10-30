"""Independent checks of bilingual worked numerical claims and content coverage.

Reads the teaching documents, computes reference values using SI analytic
identities, and checks the precision actually printed in each language. It does
not modify teaching content, original presentations, model weights or reports.
The catalogue and conceptual-question review remain documentary, not execution
of every named algorithm or experimental validation.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re

BASE = Path(__file__).resolve().parents[1]

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def audit(course_path, derivations_path):
    course = json.loads(course_path.read_text(encoding="utf-8-sig"))
    derivations = json.loads(derivations_path.read_text(encoding="utf-8-sig"))
    modules = {m["id"]: m for m in course["modules"]}
    chapters = {c["id"]: c for c in derivations["chapters"]}
    checks = []
    def check(name, condition, **evidence):
        checks.append({"name": name, "passed": bool(condition), **evidence})
    def example(chapter, key):
        return next(e for e in chapters[chapter]["examples"] if e["id"] == key)
    def claim(name, text, pattern, expected, decimals=None, relative=None):
        match = re.search(pattern, text)
        if not match:
            check(name, False, reason="Documented numerical claim not found", pattern=pattern)
            return
        displayed = float(match.group(1).rstrip("."))
        tolerance = 0.5 * 10 ** (-decimals) if decimals is not None else abs(expected) * relative
        check(name, abs(displayed - expected) <= tolerance, displayed=displayed,
              expected=expected, absoluteTolerance=tolerance,
              evidence="Independent analytic value versus printed rounding precision")

    check("24-course-modules", len(modules) == 24)
    check("48-course-examples", sum(len(m["examples"]) for m in modules.values()) == 48)
    check("48-course-questions", sum(len(m["questions"]) for m in modules.values()) == 48)
    check("20-mathematical-chapters", len(chapters) == 20)
    check("111-numbered-equation-mappings", len(derivations["equationCoverage"]) == 111)
    pair_count = {"course": 0, "derivations": 0}
    def pairs(value, key, location):
        if isinstance(value, dict):
            if "es" in value or "en" in value:
                check(location+"-bilingual", all(isinstance(value.get(l), str) and value[l].strip() for l in ("es", "en")))
                pair_count[key] += 1
            for name, child in value.items(): pairs(child, key, location+"/"+name)
        elif isinstance(value, list):
            for i, child in enumerate(value): pairs(child, key, location+"/"+str(i))
    pairs(course, "course", "course")
    pairs(derivations, "derivations", "derivations")

    factor = next(e for e in modules["temperature-standard"]["examples"] if e["id"] == "factors")
    ft = 293 / 301
    total = .89 * ft
    d_corrected = .33 * total
    for language in ("es", "en"):
        text = factor["instruction"][language]
        claim("thermal-factor-"+language, text, r"fT=293/301≈([0-9.]+)", ft, decimals=4)
        claim("combined-factor-"+language, text, r"ftotal≈([0-9.]+)", total, decimals=4)
        claim("corrected-D-"+language, text, r"D (?:corregido|corrected)≈([0-9.]+)" if language == "es" else r"corrected D≈([0-9.]+)", d_corrected, decimals=4)

    # Independent reference values use the given parameters, not a rendering or
    # simulation implementation. Each assertion checks both documented languages.
    e = example("units-probability", "rms")
    rms_um = math.sqrt(2 * e["parameters"]["D_m2_s"] * e["parameters"]["time_s"]) * 1e6
    for language in ("es", "en"):
        claim("rms-displacement-"+language, e["solution"][language], r"=([0-9.]+)µm", rms_um, decimals=2)
    e = example("propagator", "gaussian-example")
    gaussian = math.exp(-e["parameters"]["phaseVariance"] / 2)
    for language in ("es", "en"):
        claim("Gaussian-phase-average-"+language, e["solution"][language], r"=([0-9.]+)\. ", gaussian, decimals=4)
    e = example("coherence-pathways", "stored-example")
    p = e["parameters"]
    attenuation = math.exp(-p["D_m2_s"] * p["q0_per_m"]**2 * p["storage_s"])
    for language in ("es", "en"):
        claim("stored-grating-attenuation-"+language, e["solution"][language], r"exp\(−0\.4\)=([0-9.]+)", attenuation, decimals=4)
    e = example("gradient-shapes", "sine-example")
    p = e["parameters"]
    ratio = 4 / math.pi**2 * (p["Delta_s"]-p["delta_s"]/4) / (p["Delta_s"]-p["delta_s"]/3)
    for language in ("es", "en"):
        claim("half-sine-equation-bias-"+language, e["solution"][language], r"=([0-9.]+)\. ", ratio, decimals=4)
    e = example("monopolar-pgse", "pgse-number")
    p = e["parameters"]
    q = p["gamma_rad_s_T"] * p["g_T_m"] * p["delta_s"]
    b = q*q*(p["Delta_s"]-p["delta_s"]/3)
    echo = math.exp(-p["D_m2_s"]*b)
    check("PGSE-stored-b-matches-SI-parameters", math.isclose(p["b_s_m2"], b, rel_tol=1e-12), expected=b, actual=p["b_s_m2"])
    check("PGSE-stored-echo-matches-SI-parameters", math.isclose(p["E"], echo, rel_tol=1e-12), expected=echo, actual=p["E"])
    for language in ("es", "en"):
        claim("PGSE-q-"+language,e["solution"][language],r"q0=([0-9.]+)",q,decimals=2)
        claim("PGSE-b-"+language,e["solution"][language],r"b=([0-9.e+]+)",b,relative=5e-6)
        claim("PGSE-E-"+language,e["solution"][language],r"exp\(−Db\)=([0-9.]+)",echo,decimals=6)
    e = example("stimulated-echo-led", "ste-relaxation-example")
    p = e["parameters"]
    ste = .5*math.exp(-p["txy_s"]/p["T2_s"]-p["tz_s"]/p["T1_s"])
    transverse = math.exp(-(p["txy_s"]+p["tz_s"])/p["T2_s"])
    for language in ("es", "en"):
        claim("STE-relaxation-"+language,e["solution"][language],r"0\.100/1\)=([0-9.]+)",ste,decimals=4)
        claim("transverse-relaxation-"+language,e["solution"][language],r"0\.110/0\.050\)=([0-9.]+)",transverse,decimals=4)
    e = example("bipolar", "bipolar-timing")
    p = e["parameters"]
    ratio = (p["Delta_s"]-p["delta_s"]/3-p["tau_s"]/2)/(p["Delta_s"]-p["delta_s"]/3)
    for language in ("es", "en"):
        text=e["solution"][language]
        claim("bipolar-time-ratio-"+language,text,r"(?:cociente es|ratio is) ([0-9.]+)",ratio,decimals=5)
        claim("bipolar-time-decrease-"+language,text,r"(?:cae un|falls by) ([0-9.]+)%",(1-ratio)*100,decimals=2)
    e = example("double-ste", "double-correction")
    p=e["parameters"]
    ratio=(p["Delta_s"]-2*p["delta_s"]/3)/(p["Delta_s"]-p["delta_s"]/3)
    for language in ("es", "en"):
        claim("double-STE-time-ratio-"+language,e["solution"][language],r"(?:es|is) ([0-9.]+) (?:del|of)",ratio,decimals=5)
    e=example("cross-terms","cross-term-bias");p=e["parameters"]
    for language in ("es", "en"):
        claim("cross-term-plus-"+language,e["solution"][language],r"E\+/E0=e\^\(−0\.3\)=([0-9.]+)",math.exp(-p["D_m2_s"]*(p["b_encoding_s_m2"]+p["b_cross_plus_s_m2"])),decimals=5)
        claim("cross-term-minus-"+language,e["solution"][language],r"E−/E0=e\^\(−0\.1\)=([0-9.]+)",math.exp(-p["D_m2_s"]*(p["b_encoding_s_m2"]-p["b_cross_plus_s_m2"])),decimals=5)

    row=next(r for r in derivations["equationCoverage"] if r["sourceId"]=="Kuchel2012" and r["paperEquation"]=="38")
    check("Spanish-equation38-explicit-zero-background", "g0=0" in row["notes"]["es"] and "g00" not in row["notes"]["es"])
    return {"version":"1.3-audit", "checkedAtUtc":datetime.now(timezone.utc).isoformat(),
        "passed":all(c["passed"] for c in checks),"checks":checks,
        "counts":{"checks":len(checks),"passed":sum(c["passed"] for c in checks),"courseBilingualPairs":pair_count["course"],"derivationBilingualPairs":pair_count["derivations"],
                  "courseModules":len(modules),"courseExamples":sum(len(m["examples"]) for m in modules.values()),"courseQuestions":sum(len(m["questions"]) for m in modules.values()),
                  "mathematicalChapters":len(chapters),"mathematicalSteps":sum(len(c["steps"]) for c in chapters.values()),"mathematicalExamples":sum(len(c["examples"]) for c in chapters.values()),"mathematicalQuestions":sum(len(c["questions"]) for c in chapters.values()),"numberedEquations":len(derivations["equationCoverage"])},
        "contentHashes":{"course":digest(course_path),"derivations":digest(derivations_path)},
        "scope":"Document structure/bilingual parity and independent SI calculations of printed worked claims. Conceptual peer review, every catalogued algorithm, hardware calibration, chemical identification and educational effectiveness are not established by these checks."}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course",type=Path,default=BASE/"content/course.json")
    parser.add_argument("--derivations",type=Path,default=BASE/"content/derivations.json")
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    report=audit(args.course,args.derivations)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"passed":report["passed"],"counts":report["counts"],"failures":[c for c in report["checks"] if not c["passed"]]},ensure_ascii=False))
    raise SystemExit(0 if report["passed"] else 1)

if __name__=="__main__":main()
