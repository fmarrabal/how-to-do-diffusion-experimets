"""Prepare an empty scratch directory from the final frozen public dataset.

Run from the Academy root. No training, downloads or existing-file replacement.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

HERE = Path(__file__).resolve().parent
ACADEMY = HERE.parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("scratch", type=Path)
    args = parser.parse_args()
    target = args.scratch.resolve()
    if target.exists():
        raise SystemExit("Use an absent scratch directory; existing evidence is preserved.")
    plan = json.loads((HERE / "split-plan.json").read_text(encoding="utf-8"))
    for split, expected in plan["dataset_sha256"].items():
        if sha(HERE / f"{split}.jsonl") != expected:
            raise SystemExit("Frozen dataset hash mismatch: " + split)
    sources = {"course.json": ACADEMY / "content/course.json", "research-tutor-knowledge.json": ACADEMY / "content/research-tutor-knowledge.json"}
    for name, key in (("course.json", "course_sha256"), ("research-tutor-knowledge.json", "research_knowledge_sha256")):
        if sha(sources[name]) != plan[key]:
            raise SystemExit("Reviewed source hash mismatch: " + name)
    target.mkdir(parents=True)
    for name in ("train.jsonl", "dev.jsonl", "test.jsonl", "split-plan.json"):
        shutil.copyfile(HERE / name, target / name)
    for name, source in sources.items():
        shutil.copyfile(source, target / name)
    print(json.dumps({"prepared": True, "counts": plan["split_counts"], "scope": "Frozen public summaries/synthetic examples only; no training performed."}))


if __name__ == "__main__":
    main()
