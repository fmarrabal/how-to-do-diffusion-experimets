"""Create a new, allowlisted Academy 1.2 source ZIP with full CRC/SHA readback.

Preserves prior source packages/scripts. Includes the explicitly licensed small
DOSY subset and documentary tutor metadata, never GGUF/base/adapter weights,
private papers, downloaded full archives, learner exports or credentials.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import zipfile

ACADEMY = Path(__file__).resolve().parents[1]
PREFIX = "DiffAtOnce-Academy-1.2.0-source/"
SOURCE_PREFIX = PREFIX + "desktop/academy/"
BLOCK = 1024 * 1024
FIXED_TIME = (1980, 1, 1, 0, 0, 0)
SKIP_DIRS = {"bin", "obj", ".git", ".vs", ".venv", "venv", "__pycache__", "node_modules", "qa", "research", "screenshots", "release", "checkpoints", "checkpoint", "merged", "base", "base-1.7b", "runtime-data"}
SAFE_EXTS = {".cs", ".audit", ".csproj", ".xaml", ".sln", ".slnx", ".props", ".targets", ".resx", ".json", ".jsonl", ".config", ".md", ".txt", ".py", ".ps1", ".html", ".js", ".cjs", ".mjs", ".css", ".svg", ".png", ".jpg", ".jpeg", ".ico", ".gif", ".mp4", ".pdf", ".xml", ".nuspec", ".toml", ".yml", ".yaml", ".jinja"}
RAW_DATA_PREFIXES = ("content/doctoral-data/monash-d2o-10/", "web/content/doctoral-data/monash-d2o-10/")
GENERATED_PDFS = {"docs/MANUAL_ES.pdf", "docs/MANUAL_EN.pdf", "docs/DOCTORAL_MANUAL_ES.pdf", "docs/DOCTORAL_MANUAL_EN.pdf", "web/docs/DOCTORAL_MANUAL_ES.pdf", "web/docs/DOCTORAL_MANUAL_EN.pdf"}
MANIFEST = "SOURCE_SHA256.json"

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(BLOCK), b""): h.update(chunk)
    return h.hexdigest()

def encoded(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def safe_file(root: Path, path: Path):
    rel = path.relative_to(root)
    current = root
    for part in rel.parts:
        current /= part
        info = current.lstat()
        if current.is_symlink() or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError(f"Linked source excluded: {rel}")
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Source escapes Academy: {rel}")

def select_sources(root):
    selected = {}
    def add(path, required=True):
        if not path.exists():
            if required: raise FileNotFoundError(path)
            return
        safe_file(root, path)
        name = path.relative_to(root).as_posix()
        low = name.lower()
        if any(part.startswith(".env") or any(term in part for term in ("credential", "secret", "student-work", "notebook-export")) for part in Path(name).parts):
            raise ValueError(f"Private/learner file excluded: {name}")
        if path.suffix.lower() in {".gguf", ".safetensors", ".bin", ".zip", ".rar", ".dll", ".exe", ".pdb", ".pyc", ".tmp", ".bak", ".previous", ".log"}:
            raise ValueError(f"Runtime/model/archive excluded: {name}")
        if low.endswith(".pdf") and name not in GENERATED_PDFS:
            raise ValueError(f"Only generated final manuals may be included as PDFs: {name}")
        raw = name.startswith(RAW_DATA_PREFIXES)
        if not raw and path.suffix.lower() not in SAFE_EXTS and path.name not in {"LICENSE", "NOTICE"}:
            raise ValueError(f"Unexpected source extension: {name}")
        selected[name] = path
    def tree(folder):
        if not folder.is_dir(): raise FileNotFoundError(folder)
        for current, dirs, files in os.walk(folder, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d.lower() not in SKIP_DIRS and not d.lower().endswith("-qa") and not d.startswith("."))
            for name in sorted(files):
                if name.startswith(".") or Path(name).suffix.lower() in {".pyc", ".tmp", ".bak", ".previous", ".log", ".gguf", ".safetensors", ".dll", ".pdb", ".exe"}: continue
                add(Path(current) / name)
    for name in ("README.md", "START_HERE_ES_EN.txt", "SOURCE_BUILD_V12.md", "NuGet.Config", "lab-source-hashes.json"):
        add(root / name)
    for folder in ("src", "tests", "content", "lab", "web", "THIRD_PARTY"):
        tree(root / folder)
    for path in sorted((root / "docs").iterdir()):
        if path.is_file() and path.suffix.lower() in {".md", ".pdf", ".json"}:
            if path.suffix.lower() == ".pdf" and path.name not in {"MANUAL_ES.pdf", "MANUAL_EN.pdf", "DOCTORAL_MANUAL_ES.pdf", "DOCTORAL_MANUAL_EN.pdf"}:
                continue  # Never include an unrecognised/private PDF accidentally placed in docs.
            add(path)
    for path in sorted((root / "tools").iterdir()):
        if path.is_file() and path.suffix.lower() in {".py", ".ps1"}: add(path)
    # Metadata/report inclusion is explicit. No training examples/student text,
    # model weights, native binaries, caches or arbitrary AI folders are traversed.
    for folder in ("ai/release-v1.1",):
        for path in sorted((root / folder).iterdir()):
            if path.is_file() and path.suffix.lower() in {".json", ".txt", ".md"}: add(path)
    for name in ("ai/README_ES_EN.md", "ai/environment_report.json", "ai/environment_git_provenance_normalized.json", "ai/base-1.7b/base-provenance.json", "ai/web-feasibility/FEASIBILITY_ES_EN.md"):
        add(root / name, required=False)
    for path in sorted((root / "ai/NativeCheck").iterdir()):
        if path.is_file() and path.suffix.lower() in {".cs", ".csproj", ".md", ".config"}: add(path)
    if len(selected) != len({p.casefold() for p in selected}): raise ValueError("Case-insensitive path collision")
    return dict(sorted(selected.items()))

def validate_release(root, selected, require_manuals=True):
    d = read_json(root / "content/derivations.json")
    if d.get("releaseStatus") != "reviewed" or sha(root / "content/derivations.json") != "e07920a25ae8642ffa55a83a75a4db7eb8a6ead09a5c8195ae23ef91d6c9b02e":
        raise ValueError("Reviewed mathematics identity differs")
    m = read_json(root / "content/doctoral-manifest.json")
    if m.get("version") != "1.2.0" or m.get("releaseStatus") != "reviewed-teaching-software" or m.get("includedInLLMTraining") is not False:
        raise ValueError("Doctoral source is not frozen/reviewed or claims new training")
    for item in m.get("files", []):
        path = root / item["path"]
        safe_file(root, path)
        if sha(path) != item["sha256"]: raise ValueError(f"Doctoral manifest mismatch: {item['path']}")
    corpus_sha = sha(root / "content/course.json")
    if corpus_sha != "f9a17df9645b541abc70907e5d04cd38c213293443ce1d37c2c0d94f8aea0cb9": raise ValueError("Original training course changed")
    ai = read_json(root / "ai/release-v1.1/manifest.json")
    if ai.get("SupplementalLLMApproved") is not False or ai.get("SupplementalAnswerMode") != "reviewed-documentary-guide": raise ValueError("New mathematics LLM inference is not approved")
    provenance = read_json(root / "content/doctoral-data/monash-d2o-10/provenance.json")
    if provenance["license"]["name"] != "CC BY 4.0" or provenance["sourceDOI"] != "10.26180/33075584.v1": raise ValueError("Public data license/source differs")
    expected = {f["path"]: f for f in provenance["files"]}
    for prefix in RAW_DATA_PREFIXES:
        for relative, record in expected.items():
            path = root / prefix / relative
            if path.stat().st_size != record["bytes"] or sha(path) != record["sha256"]: raise ValueError(f"Public raw subset altered: {prefix}{relative}")
    if require_manuals:
        build = read_json(root / "qa/doctoral-1.2/manuals/manuals-build-report.json")
        review = read_json(root / "qa/doctoral-1.2/manuals/manuals-visual-qa.json")
        if build.get("version") != "1.2.0" or review.get("passed") is not True or review.get("allPagesVisuallyReviewed") is not True:
            raise ValueError("Final doctoral manual visual QA is not complete")
        for name in ("DOCTORAL_MANUAL_ES.pdf", "DOCTORAL_MANUAL_EN.pdf"):
            p = root / "docs" / name
            if not p.is_file() or p.stat().st_size < 20000: raise ValueError(f"Wait for final doctoral manual: {name}")
            language = "es" if "_ES." in name else "en"
            reviewed = [r for r in review.get("outputs", []) if str(r.get("language", "")).lower() == language]
            built = [r for r in build.get("outputs", []) if str(r.get("language", "")).lower() == language]
            if len(reviewed) != 1 or len(built) != 1 or reviewed[0].get("sha256") != sha(p) or built[0].get("sha256") != sha(p):
                raise ValueError(f"Final manual differs from its build/visual review: {name}")
    return {"doctoralManifestSha256": sha(root / "content/doctoral-manifest.json"), "courseSha256": corpus_sha, "derivationsSha256": sha(root / "content/derivations.json"), "includedInNewLLMTraining": False, "LLMWeightsIncluded": False, "rawSubsetLicense": provenance["license"], "rawSubsetDOI": provenance["sourceDOI"], "experimentalValidation": False}

ROOT_README = """DiffAtOnce Academy 1.2 source / Código fuente\n\nES: Desde esta carpeta, abre desktop/academy/SOURCE_BUILD_V12.md.\nEl árbol preserva desktop/academy para los scripts portables. No contiene\npesos LLM, datos de estudiantes, artículos privados ni el depósito DOSY\ncompleto. Sí contiene un subset DOSY CC BY 4.0 original con atribución y hashes.\nLas actividades nuevas usan pistas revisadas, sin nuevo entrenamiento LLM.\n\nEN: From this folder, read desktop/academy/SOURCE_BUILD_V12.md.\nThe desktop/academy hierarchy is preserved for portable scripts. No LLM\nweights, learner data, private papers or the full DOSY deposit are included.\nAn unchanged CC BY 4.0 DOSY subset is included with attribution and hashes.\nNew activities use reviewed hints without new LLM training.\n"""

def zip_info(name):
    info = zipfile.ZipInfo(name, date_time=FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    info._compresslevel = 6
    return info

def verify_archive(path, manifest, readme):
    expected = {SOURCE_PREFIX + f["path"]: f for f in manifest["files"]}
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != set(expected) | {PREFIX + MANIFEST, PREFIX + "README_SOURCE_ES_EN.txt"}:
            raise ValueError("ZIP membership differs from the explicit source manifest")
        if archive.testzip(): raise ValueError("ZIP CRC verification failed")
        if archive.read(PREFIX + MANIFEST) != encoded(manifest) or archive.read(PREFIX + "README_SOURCE_ES_EN.txt") != readme:
            raise ValueError("Internal source manifest/readme mismatch")
        for name, record in expected.items():
            digest, length = hashlib.sha256(), 0
            with archive.open(name) as stream:
                for block in iter(lambda: stream.read(BLOCK), b""):
                    digest.update(block)
                    length += len(block)
            if digest.hexdigest() != record["sha256"] or length != record["bytes"]: raise ValueError(f"ZIP readback mismatch: {name}")

def package(output):
    output = Path(output).resolve()
    if output.suffix.lower() != ".zip": raise ValueError("Choose an explicit new .zip filename")
    sidecar = output.with_suffix(".sha256.json")
    partial = Path(str(output) + ".partial")
    for p in (output, sidecar, partial):
        if p.exists(): raise FileExistsError(f"Existing artifact preserved: {p}")
    selected = select_sources(ACADEMY)
    gates = validate_release(ACADEMY, selected)
    records = [{"path": name, "bytes": p.stat().st_size, "sha256": sha(p)} for name, p in selected.items()]
    manifest = {"schema": "academy-source-release/1.2", "version": "1.2.0", "files": records, "evidence": gates, "scope": "Source/code/manual/software QA provenance; not student-learning or experimental validation.", "excluded": ["model weights and adapters", "private papers", "full research downloads", "learner exports and notes", "credentials", "bin/obj", "QA screenshots"], "manifestSelfHash": "Covered by the outer ZIP hash; no recursive self-hash."}
    readme = ROOT_README.encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    by_name = {f["path"]: f for f in records}
    with partial.open("xb") as raw, zipfile.ZipFile(raw, "w", allowZip64=True) as archive:
        archive.writestr(zip_info(PREFIX + MANIFEST), encoded(manifest))
        archive.writestr(zip_info(PREFIX + "README_SOURCE_ES_EN.txt"), readme)
        for name, path in selected.items():
            digest, length = hashlib.sha256(), 0
            with path.open("rb") as source, archive.open(zip_info(SOURCE_PREFIX + name), "w", force_zip64=True) as target:
                for block in iter(lambda: source.read(BLOCK), b""):
                    target.write(block)
                    digest.update(block)
                    length += len(block)
            if digest.hexdigest() != by_name[name]["sha256"] or length != by_name[name]["bytes"]:
                raise ValueError(f"Input changed while packaging; preserve partial evidence: {name}")
    verify_archive(partial, manifest, readme)
    # Refuse overwrite even if another process created the final file meanwhile.
    with output.open("xb") as target, partial.open("rb") as source:
        for block in iter(lambda: source.read(BLOCK), b""): target.write(block)
    digest = sha(output)
    if digest != sha(partial): raise ValueError("Final ZIP copy differs from verified partial")
    result = {"archive": output.name, "bytes": output.stat().st_size, "sha256": digest, "fileCount": len(records), "zipEntryCount": len(records) + 2, "crcVerified": True, "allEntriesReadAndHashed": True, "membershipVerified": True, "sourceManifest": manifest}
    with sidecar.open("xb") as stream: stream.write(encoded(result))
    # Single explicitly-created file only; failed partials are preserved.
    partial.unlink()
    return {k: v for k, v in result.items() if k != "sourceManifest"}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--inspect", action="store_true", help="Inspect allowlist only; no output/model/experiment writes")
    args = parser.parse_args()
    if args.inspect:
        selected = select_sources(ACADEMY)
        print(json.dumps({"files": len(selected), "bytes": sum(p.stat().st_size for p in selected.values()), "modelWeightsIncluded": False, "sourceFiles": list(selected)}, indent=2))
        return 0
    if not args.output: parser.error("--output is required unless --inspect")
    print(json.dumps(package(args.output), indent=2))
    return 0

if __name__ == "__main__": sys.exit(main())
