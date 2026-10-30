"""Structural, provenance and exercise-contract checks for Academy content."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[1]
CONTENT = BASE / "content"
checks = []
def check(name, condition):
    checks.append({"name": name, "passed": bool(condition)})
def pair(value):
    return isinstance(value, dict) and all(isinstance(value.get(l), str) and value[l].strip() for l in ("es", "en"))

course = json.loads((CONTENT / "course.json").read_text(encoding="utf-8"))
source = json.loads((CONTENT / "source-index.json").read_text(encoding="utf-8"))
physics = json.loads((ROOT / "entregables/diffusion-motion-lab/physics-catalog.json").read_text(encoding="utf-8"))
scenes = {s["id"]: s for s in physics["scenes"]}
check("course title bilingual", pair(course["title"]))
check("24 modules", len(course["modules"]) == 24)
check("module ids unique", len({m["id"] for m in course["modules"]}) == 24)
check("module ordering", [m["order"] for m in course["modules"]] == list(range(1, 25)))
check("source original SHA unchanged", hashlib.sha256(Path(source["input"]["path"]).read_bytes()).hexdigest() == source["input"]["sha256"] == course["sourceSha256"])
check("all 81 source slides mapped", source["coverage"]["mappedSlides"] == 81 and not source["coverage"]["unmappedSlides"])
all_mapped = set()
for slide in source["slides"]:
    image = CONTENT / slide["image"]
    digest = hashlib.sha256(image.read_bytes()).hexdigest() if image.exists() else ""
    check(f"slide {slide['slide']} image source hash", any(i["sha256"] == digest for i in slide["images"]))
    check(f"slide {slide['slide']} literal accessible text and notes", bool(slide["text"].strip()) and bool(slide["notes"].strip()))
    check(f"slide {slide['slide']} valid module map", all(m in {x["id"] for x in course["modules"]} for m in slide["moduleIds"]))
    all_mapped.add(slide["slide"])
for module in course["modules"]:
    mid = module["id"]
    check(f"{mid} existing lab scene", module["scene"] in scenes)
    for field in ("chapter", "title", "objective", "why", "purpose", "mechanism", "takeaway"):
        check(f"{mid} bilingual {field}", pair(module[field]))
    check(f"{mid} practical steps", len(module["steps"]) >= 3 and all(pair(s["title"]) and pair(s["body"]) for s in module["steps"]))
    check(f"{mid} guided examples and counterexample", len(module["examples"]) >= 2 and any(e["id"] == "counterexample" for e in module["examples"]))
    check(f"{mid} bilingual examples", all(pair(e["title"]) and pair(e["instruction"]) for e in module["examples"]))
    valid_controls = {c["key"]: c for c in scenes[module["scene"]]["parameters"]}
    for example in module["examples"]:
        for key, value in example.get("params", {}).items():
            c = valid_controls.get(key)
            check(f"{mid}/{example['id']} parameter {key}", c is not None and isinstance(value, (float, int)) and c["min"] <= value <= c["max"])
    check(f"{mid} two graded questions", len(module["questions"]) >= 2)
    check(f"{mid} local question ids unique", len({q["id"] for q in module["questions"]}) == len(module["questions"]))
    for q in module["questions"]:
        check(f"{mid}/{q['id']} bilingual question/feedback/options", pair(q["question"]) and pair(q["explanation"]) and len(q["options"]) >= 3 and all(pair(o) for o in q["options"]))
        check(f"{mid}/{q['id']} correct answer bounds", isinstance(q["correctIndex"], int) and 0 <= q["correctIndex"] < len(q["options"]))
    check(f"{mid} bilingual pitfalls", bool(module["pitfalls"]) and all(pair(p) for p in module["pitfalls"]))
    source_slides = {s["slide"] for s in module["sources"] if "slide" in s}
    check(f"{mid} complete source mapping", source_slides == set(source["coverage"]["moduleToSlides"][mid]))
catalog = json.loads((CONTENT / "algorithm-catalog.json").read_text(encoding="utf-8"))
check("catalog 72 source records", len(catalog["records"]) == catalog["counts"]["records"] == 72)
check("catalog scopes/limits", all(r.get("use_es") and r.get("use_en") and r.get("limits_es") and r.get("limits_en") for r in catalog["records"]))
result = {"version": "1.0.0", "checkedDate": "2026-10-05", "checks": checks,
          "passed": sum(c["passed"] for c in checks), "failed": sum(not c["passed"] for c in checks),
          "evidenceBoundary": "Source/provenance, bilingual content and scene contracts only. Not scientific peer review, student usability, LLM evaluation or hardware validation.",
          "contentHashes": {name: hashlib.sha256((CONTENT / name).read_bytes()).hexdigest() for name in ("course.json", "source-index.json", "algorithm-catalog.json")}}
(CONTENT / "curriculum-verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: result[k] for k in ("passed", "failed", "contentHashes")}, indent=2))
if result["failed"]:
    print(json.dumps([c for c in checks if not c["passed"]], indent=2))
    raise SystemExit(1)
