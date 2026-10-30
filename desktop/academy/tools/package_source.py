"""Create a deterministic, allowlisted Academy source archive after release freeze.

Standard library only. Never modifies selected inputs or replaces an archive.
The source ZIP deliberately excludes GGUF/base/merged weights and user progress.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "DiffAtOnce-Academy-source/"
MANIFEST = "SOURCE_SHA256.json"
FIXED_TIME = (1980, 1, 1, 0, 0, 0)
BLOCK = 1024 * 1024
SKIP_DIRS = {
    "bin", "obj", ".git", ".vs", ".idea", ".venv", "venv", "__pycache__",
    ".pytest_cache", "node_modules", "checkpoints", "checkpoint", "merged",
    "base", "base-1.7b", "work-v1", "no-backend-v2", "runtime-data", "qa",
}
SAFE_EXT = {
    ".cs", ".audit", ".csproj", ".sln", ".slnx", ".props", ".targets",
    ".xaml", ".resx", ".config", ".json", ".jsonl", ".md", ".txt",
    ".html", ".js", ".cjs", ".mjs", ".css", ".svg", ".png", ".jpg",
    ".jpeg", ".ico", ".gif", ".mp4", ".pdf", ".py", ".ps1", ".jinja",
    ".safetensors", ".lock", ".toml", ".yaml", ".yml", ".xml", ".nuspec",
}
AI_REPORTS = (
    "completion-loss-verification.json", "prompt-budget-report.json",
    "native-evaluation-v2.json", "tutor-course-boundary-smoke-v2.json",
    "native-evaluation-v2-focused.json", "native-evaluation-v2-anchored.json",
    "native-evaluation-v2-compatible.json", "native-evaluation-v2-hybrid.json",
    "prompt-parity-report.json", "native-probe-history.json",
    "environment_git_provenance_normalized.json",
    "tutor-missing-native-backend-v2.json", "smoke-course.json",
    "environment-report.json", "environment_report.json", "training-environment.json",
    "conversion-provenance.json", "converter-provenance.json",
    "requirements.lock.txt", "requirements-rebuild.txt",
)
WORK_FILES = (
    "course.json", "train.jsonl", "dev.jsonl", "test.jsonl", "split-plan.json",
    "training_report.json", "evaluation_report.json",
)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(BLOCK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def encoded(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def is_reparse(path: Path) -> bool:
    info = path.lstat()
    return path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def safe_file(root: Path, path: Path) -> Path:
    # Check every lexical parent before resolve, so a junction cannot escape root.
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        current /= part
        if is_reparse(current):
            raise ValueError(f"Symlink/junction is not a source input: {relative}")
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Not a regular source file inside Academy: {relative}")
    return path


def select_sources(root: Path, extra_evidence: list[str]) -> dict[str, Path]:
    selected: dict[str, Path] = {}

    def add(path: Path, required=True):
        if not path.exists():
            if required:
                raise FileNotFoundError(path)
            return
        safe_file(root, path)
        relative = path.relative_to(root).as_posix()
        parts = {part.lower() for part in path.relative_to(root).parts}
        if path.suffix.lower() not in SAFE_EXT and path.name not in {"LICENSE", "NOTICE"}:
            raise ValueError(f"Unexpected source extension: {relative}")
        if path.suffix.lower() == ".safetensors" and relative != "ai/work-v2/adapter/adapter_model.safetensors":
            raise ValueError(f"Only the selected LoRA adapter is allowed: {relative}")
        if any(part.startswith(".env") or "credential" in part or "secret" in part for part in parts):
            raise ValueError(f"Private configuration is not allowed: {relative}")
        progress_data = path.name.lower().startswith("progress") and path.suffix.lower() in {".json", ".jsonl", ".previous", ".bak"}
        if progress_data or path.suffix.lower() in {".gguf", ".pdb", ".dll", ".exe"}:
            raise ValueError(f"Runtime/user output is not allowed: {relative}")
        selected[relative] = path

    def tree(folder: Path):
        if not folder.is_dir():
            raise FileNotFoundError(folder)
        for current, directories, files in os.walk(folder, followlinks=False):
            directories[:] = sorted(d for d in directories if d.lower() not in SKIP_DIRS and not d.startswith("."))
            for d in directories:
                if is_reparse(Path(current) / d):
                    raise ValueError(f"Unexpected linked directory: {Path(current) / d}")
            for name in sorted(files):
                if name.startswith(".") or name.endswith((".pyc", ".tmp", ".bak", ".previous")):
                    continue
                add(Path(current) / name)

    for name in ("README.md", "START_HERE_ES_EN.txt", "SOURCE_BUILD.md", "NuGet.Config", "lab-source-hashes.json"):
        add(root / name)
    for folder in ("src", "tests", "content", "lab", "THIRD_PARTY"):
        tree(root / folder)
    # Top-level final manuals/guides/reports only; never docs/qa renders.
    for path in sorted((root / "docs").iterdir()):
        if path.is_file() and path.suffix.lower() in {".md", ".pdf", ".json"}:
            add(path)
    for pattern in ("*.py", "*.ps1"):
        for path in sorted((root / "tools").glob(pattern)):
            add(path)
    for path in sorted((root / "ai").glob("*.py")):
        add(path)
    add(root / "ai/README_ES_EN.md")
    for name in AI_REPORTS:
        add(root / "ai" / name, required=False)
    # Extra additive provenance/lockfiles may be placed here before freeze.
    for folder in ("ai/reproducibility", "ai/reports"):
        if (root / folder).is_dir():
            tree(root / folder)
    # NativeCheck's compiled regression folders can have arbitrary names;
    # only its direct project/source/documentation files are source inputs.
    for path in sorted((root / "ai/NativeCheck").iterdir()):
        if path.is_file() and path.suffix.lower() in {".cs", ".csproj", ".md", ".config"}:
            add(path)
    add(root / "ai/NativeCheck/NativeCheck.csproj")
    add(root / "ai/NativeCheck/Program.cs")
    for name in WORK_FILES:
        add(root / "ai/work-v2" / name)
    tree(root / "ai/work-v2/adapter")
    for path in sorted((root / "ai/release").iterdir()):
        if path.is_file() and path.suffix.lower() in {".json", ".txt", ".md"}:
            add(path)
    add(root / "ai/release/manifest.json")
    add(root / "ai/release/QWEN_LICENSE.txt")
    if (root / "ai/release/native-probes").is_dir():
        tree(root / "ai/release/native-probes")
    add(root / "ai/base-1.7b/base-provenance.json", required=False)

    def evidence_path(value: str) -> Path:
        # Historical manifests can record absolute Windows paths. Rebind only
        # their explicit Academy suffix; never read an arbitrary outside path.
        normalized = value.replace("\\", "/")
        marker = "/desktop/academy/"
        if marker in normalized:
            normalized = normalized.split(marker, 1)[1]
        elif normalized.startswith("desktop/academy/"):
            normalized = normalized[len("desktop/academy/"):]
        rel = PurePosixPath(normalized)
        if rel.is_absolute() or ".." in rel.parts or ":" in normalized:
            raise ValueError(f"Evidence path must be Academy-relative: {value}")
        if len(rel.parts) < 3 or rel.parts[0] != "qa":
            raise ValueError(f"Evidence must identify one file under qa/: {value}")
        path = root.joinpath(*rel.parts)
        if not ((path.name.startswith("academy-") and path.suffix == ".png") or path.name in {"ui-self-test.json", "spen-context.json"}):
            raise ValueError(f"Not a selected UI evidence file: {value}")
        return path

    # Include exactly the captures used by final manuals, with their checked
    # hashes. Unreferenced historical QA directories and learner state stay out.
    manual = read_json(root / "docs/manual-build-manifest.json")
    for record in manual.get("screenshots", []):
        path = evidence_path(record["path"])
        safe_file(root, path)
        if sha(path) != record["sha256"]:
            raise ValueError(f"Manual screenshot changed after review: {path.name}")
        add(path)
    for value in extra_evidence:
        add(evidence_path(value))
    folded = [name.casefold() for name in selected]
    if len(folded) != len(set(folded)):
        raise ValueError("Source paths collide on a case-insensitive filesystem")
    return dict(sorted(selected.items()))


def validate_training(root: Path, selected: dict[str, Path]):
    """Check existing evidence identity; do not rewrite or upgrade its status."""
    training = read_json(root / "ai/work-v2/training_report.json")
    evaluation = read_json(root / "ai/work-v2/evaluation_report.json")
    checks = {
        "ai/work-v2/course.json": training["course_sha256"],
        "content/course.json": training["course_sha256"],
        "ai/work-v2/split-plan.json": training["split_plan_sha256"],
        "ai/work-v2/adapter/adapter_model.safetensors": training["adapter_sha256"],
        "ai/academy_pipeline_v2.py": training["pipeline_sha256"],
        "ai/work-v2/training_report.json": evaluation["training_report_sha256"],
    }
    checks.update({f"ai/work-v2/{split}.jsonl": digest for split, digest in training["dataset_hashes"].items()})
    if evaluation["test_sha256"] != training["dataset_hashes"]["test"]:
        raise ValueError("Evaluation and training name different frozen test sets")
    release = {key.lower(): value for key, value in read_json(root / "ai/release/manifest.json").items()}
    checks.update({
        "ai/release/training_report.json": release["trainingreportsha256"],
        "ai/release/evaluation_report.json": release["evaluationreportsha256"],
    })
    for key, name in (
        ("nativeevaluationreportsha256", "ai/release/native_evaluation_report.json"),
        ("environmentreportsha256", "ai/release/environment_report.json"),
        ("tutorsourcesha256", "src/DiffAtOnce.Academy.Tutor/TutorService.cs"),
    ):
        if key in release:
            checks[name] = release[key]
    if release["coursesha256"] != training["course_sha256"]:
        raise ValueError("Release and training course identities differ")
    environment_path = root / "ai/environment_report.json"
    if environment_path.exists():
        environment = read_json(environment_path)
        for key, source in (
            ("training_report_sha256", "ai/work-v2/training_report.json"),
            ("evaluation_report_sha256", "ai/work-v2/evaluation_report.json"),
            ("course_sha256", "content/course.json"),
        ):
            if sha(selected[source]) != environment[key]:
                raise ValueError(f"Additive environment report identity mismatch: {key}")
        if environment["pipeline"]["sha256"] != training["pipeline_sha256"]:
            raise ValueError("Environment and training pipeline identities differ")
    for name, expected in checks.items():
        if name not in selected or sha(selected[name]) != expected:
            raise ValueError(f"Evidence hash mismatch: {name}")


def zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(PREFIX + name, date_time=FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    return info


def validate_manual_review(root: Path) -> None:
    review = read_json(root / "docs/manual-visual-review.json")
    if review.get("supersededByRebuild") or review.get("currentBuildNeedsFinalVisualReview"):
        raise ValueError("Final manual visual review is still pending or superseded")
    reviewed = {item["file"]: item for item in review.get("manuals", [])}
    for filename in ("MANUAL_ES.pdf", "MANUAL_EN.pdf"):
        item = reviewed.get(filename)
        if not item or item.get("result") != "passed" or sha(root / "docs" / filename) != item.get("sha256"):
            raise ValueError(f"Manual visual-review record does not match final PDF: {filename}")


def verify_archive(path: Path, manifest: dict) -> None:
    expected = {PREFIX + record["path"]: record for record in manifest["files"]}
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != set(expected) | {PREFIX + MANIFEST}:
            raise ValueError("Archive membership differs from allowlist")
        broken = archive.testzip()
        if broken:
            raise ValueError(f"ZIP CRC check failed: {broken}")
        if archive.read(PREFIX + MANIFEST) != encoded(manifest):
            raise ValueError("Internal source manifest changed")
        for name, record in expected.items():
            digest = hashlib.sha256()
            count = 0
            with archive.open(name) as stream:
                for chunk in iter(lambda: stream.read(BLOCK), b""):
                    count += len(chunk)
                    digest.update(chunk)
            if count != record["bytes"] or digest.hexdigest() != record["sha256"]:
                raise ValueError(f"Archive readback mismatch: {name}")


def package(root: Path, output: Path, evidence: list[str]) -> dict:
    output = output.resolve()
    if output.suffix.lower() != ".zip":
        raise ValueError("Output must be an explicit .zip filename")
    sidecar = output.with_suffix(".sha256.json")
    partial = output.with_name(output.name + ".partial")
    for path in (output, sidecar, partial):
        if path.exists():
            raise FileExistsError(f"Refuse to overwrite: {path}")
    selected = select_sources(root, evidence)
    validate_training(root, selected)
    validate_manual_review(root)
    records = [{"path": name, "bytes": path.stat().st_size, "sha256": sha(path)} for name, path in selected.items()]
    manifest = {
        "format": "diffatonce-academy-source-v1", "archiveRoot": PREFIX,
        "selection": "Final source/assets/docs; v2 adapter and evidence; manual-referenced captures plus explicit selected UI evidence.",
        "excluded": ["compiled bin/obj", "user progress/notebooks", "secrets/configuration", "old unreferenced QA", "base/merged/checkpoint weights", "all GGUF weights", "Python/.NET environments"],
        "reproducibility": "Sorted names, fixed 1980 timestamps, mode 0644, ZIP DEFLATE level 9. Byte-identical with identical inputs and Python/zlib implementation.",
        "preservesInputBytes": True, "experimentalValidation": False,
        "manifestSelfHash": "Not recursive: this file is covered by the external ZIP SHA-256.",
        "files": records,
    }
    by_name = {record["path"]: record for record in records}
    output.parent.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    try:
        with partial.open("xb") as raw:
            created.append(partial)
            with zipfile.ZipFile(raw, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9, allowZip64=True) as archive:
                for name in sorted([*selected, MANIFEST]):
                    info = zip_info(name)
                    if name == MANIFEST:
                        archive.writestr(info, encoded(manifest), compresslevel=9)
                        continue
                    digest, length = hashlib.sha256(), 0
                    # ZipInfo passed to open does not inherit ZipFile's level.
                    info._compresslevel = 9
                    with selected[name].open("rb") as source, archive.open(info, "w", force_zip64=True) as target:
                        for chunk in iter(lambda: source.read(BLOCK), b""):
                            target.write(chunk)
                            digest.update(chunk)
                            length += len(chunk)
                    if length != by_name[name]["bytes"] or digest.hexdigest() != by_name[name]["sha256"]:
                        raise ValueError(f"Input changed during packaging: {name}; wait for release freeze")
        verify_archive(partial, manifest)
        archive_hash, archive_bytes = sha(partial), partial.stat().st_size
        # Exclusive final creation prevents overwrites even after the preflight.
        with output.open("xb") as target:
            created.append(output)
            with partial.open("rb") as source:
                shutil.copyfileobj(source, target, BLOCK)
        if sha(output) != archive_hash:
            raise ValueError("Final archive copy hash mismatch")
        result = {
            "archive": output.name, "bytes": archive_bytes, "sha256": archive_hash,
            "fileCount": len(records), "zipEntryCount": len(records) + 1,
            "crcVerified": True, "allEntriesReadAndHashed": True,
            "sourceManifest": manifest,
        }
        with sidecar.open("xb") as stream:
            created.append(sidecar)
            stream.write(encoded(result))
        partial.unlink()
        return {key: value for key, value in result.items() if key != "sourceManifest"}
    except BaseException:
        # Only artifacts created exclusively by this invocation are removed.
        for path in reversed(created):
            if path.exists():
                path.unlink()
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New archive filename; all existing output/sidecar/partial paths are refused")
    parser.add_argument("--evidence", action="append", default=[], help="One final qa/.../ui-self-test.json, spen-context.json or academy-*.png; repeat as needed")
    args = parser.parse_args()
    print(json.dumps(package(ROOT, args.output, args.evidence), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
