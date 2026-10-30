"""Prepare/freeze the Academy 1.3 browser assets without modifying its sources.

--prepare updates only local generated content, manuals and bundle identities.
--freeze requires the root review JSON and its exact SHA256. It never replaces
an existing final version or asserts review from content alone. No model, private
paper, student record, credentials, scientific original or other product is used.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat

VERSION = "1.3.0"
# The licensed collection has its own immutable identity across software patches.
LIBRARY_VERSION = "1.3.0"
ACADEMY = Path(__file__).resolve().parents[1]
WORKSPACE = ACADEMY.parents[1]
WEB = ACADEMY / "web"
DEFAULT_RELEASE = WORKSPACE / "website/release/public_html/assets/academy/v1.3.0"
BLOCK = 1024 * 1024
TOP_FILES = (
    "index.html", "academy.css", "academy.js", "calculators.js", "mathjax-config.js", "waveform-lab.js", "product.css", "brand.png",
    "doctoral-hub.js", "doctoral-hub.css", "doctoral-physics.js", "doctoral-physics-ui.js", "doctoral-physics.css",
    "doctoral-inquiry.js", "doctoral-inquiry-ui.js", "doctoral-inquiry.css", "doctoral-pedagogy.js", "doctoral-pedagogy-ui.js", "doctoral-pedagogy.css",
    "research-journey.js", "learning-path.js", "research-studio.js", "research-studio.css", "research-pilot-panel.js", "spatial-encoding.js", "spatial-worker.js",
)
CONTENT_FILES = ("course.json", "derivations.json", "doctoral-cases.json", "doctoral-manifest.json", "research-library.json", "research-tutor-knowledge.json", "source-index.json", "algorithm-catalog.json")
MANUALS = ("RESEARCH_MANUAL_ES.pdf", "RESEARCH_MANUAL_EN.pdf", "ACADEMY_MANUAL_ES.pdf", "ACADEMY_MANUAL_EN.pdf")
LEGACY_MANUALS = ("DOCTORAL_MANUAL_ES.pdf", "DOCTORAL_MANUAL_EN.pdf")
REQUIRED_ENGINES = tuple("web/" + name for name in ("index.html", "academy.js", "learning-path.js", "research-journey.js", "research-studio.js", "research-studio.css", "research-pilot-panel.js", "spatial-encoding.js", "spatial-worker.js")) + ("content/research-library.json", "content/research-tutor-knowledge.json")
LEGACY_HASHES = {"content/course.json": "f9a17df9645b541abc70907e5d04cd38c213293443ce1d37c2c0d94f8aea0cb9", "content/derivations.json": "e07920a25ae8642ffa55a83a75a4db7eb8a6ead09a5c8195ae23ef91d6c9b02e"}
DATA_DOI = "10.26180/33075584.v1"


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(BLOCK), b""): digest.update(chunk)
    return digest.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def relative_path(value):
    if not isinstance(value, str) or "\\" in value or "\x00" in value:
        raise ValueError("A relative POSIX path is required")
    p = PurePosixPath(value)
    if p.is_absolute() or not p.parts or any(part in {"", ".", ".."} for part in p.parts) or ":" in value:
        raise ValueError("Unsafe relative path: " + value)
    return p.as_posix()


def safe_file(base, path):
    base, path = Path(base), Path(path)
    rel = path.relative_to(base)
    current = base
    for part in rel.parts:
        current /= part
        info = current.lstat()
        if current.is_symlink() or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError("Linked source/destination excluded: " + str(rel))
    if not path.is_file() or not path.resolve().is_relative_to(base.resolve()):
        raise ValueError("File escapes the intended root: " + str(rel))
    return path


def safe_tree(base):
    base = Path(base)
    if not base.is_dir(): raise FileNotFoundError(base)
    if base.is_symlink() or getattr(base.lstat(), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        raise ValueError("Linked tree excluded: " + str(base))
    for current, directories, files in os.walk(base, followlinks=False):
        for name in sorted(directories):
            p = Path(current) / name
            if p.is_symlink() or getattr(p.lstat(), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise ValueError("Linked directory excluded: " + str(p))
        directories[:] = sorted(directories)
        for name in sorted(files):
            p = Path(current) / name
            yield safe_file(base, p)


def record(path, base):
    safe_file(base, path)
    return {"path": path.relative_to(base).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)}


def enough_space(path, estimated_bytes):
    current = Path(path)
    while not current.exists(): current = current.parent
    free = shutil.disk_usage(current).free
    if free < int(estimated_bytes * 1.15) + 32 * BLOCK:
        raise OSError("Insufficient free space for the explicit build; no cleanup is performed automatically")
    return free


def safe_write_parents(path):
    absolute = Path(path).absolute()
    if not absolute.is_relative_to(WORKSPACE.absolute()): raise ValueError("Build output must stay within its source workspace")
    current = WORKSPACE
    for part in absolute.relative_to(WORKSPACE.absolute()).parts[:-1]:
        current /= part
        if current.exists() and (current.is_symlink() or getattr(current.lstat(), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise ValueError("Linked output parent excluded: " + str(current))


def write_changed(path, data):
    path = Path(path)
    safe_write_parents(path)
    if path.exists():
        safe_file(path.parent, path)
        if path.read_bytes() == data: return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def copy_changed(source, destination):
    safe_file(ACADEMY, source)
    destination = Path(destination)
    safe_write_parents(destination)
    if destination.exists():
        safe_file(destination.parent, destination)
        if source.stat().st_size == destination.stat().st_size and sha(source) == sha(destination): return
    destination.parent.mkdir(parents=True, exist_ok=True)
    expected = sha(source)
    shutil.copy2(source, destination)
    if sha(source) != expected or sha(destination) != expected:
        raise ValueError("Source changed or copy verification failed: " + str(source))


def public_metadata(name):
    source = ACADEMY / "content" / name
    if name not in {"source-index.json", "algorithm-catalog.json"}: return source.read_bytes()
    data = read_json(source)
    if name == "source-index.json": data.get("input", {}).pop("path", None)
    else:
        data.get("sourceProvenance", {}).pop("path", None)
        for item in data.get("records", []):
            if re.match(r"^[a-z]:[\\/]", str(item.get("source", "")), re.I): item["source"] = "https://diffatonce.com/caracteristicas"
    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")


def licensed_data_sources():
    catalog = read_json(ACADEMY / "content/research-library.json")
    if catalog.get("version") != LIBRARY_VERSION or catalog.get("sourceDOI") != DATA_DOI or catalog.get("license", {}).get("name") != "CC BY 4.0" or len(catalog.get("cases", [])) != 8:
        raise ValueError("The eight licensed public research cases and source are required")
    selected, originals = {}, 0
    for case in catalog["cases"]:
        prefix = relative_path(case["datasetBase"])
        if not re.fullmatch(r"content/research-data/[a-z0-9-]+", prefix): raise ValueError("Unapproved public subset path")
        manifest_path = ACADEMY / prefix / "provenance.json"
        manifest = read_json(safe_file(ACADEMY, manifest_path))
        if manifest.get("sourceDOI") != DATA_DOI or manifest.get("license", {}).get("name") != "CC BY 4.0" or manifest.get("absoluteCalibrationValidated") is not False:
            raise ValueError("Public subset provenance/license/qualification differs")
        selected[prefix + "/provenance.json"] = manifest_path
        for item in manifest["files"]:
            name = prefix + "/" + relative_path(item["path"])
            path = safe_file(ACADEMY, ACADEMY / name)
            if path.stat().st_size != item["bytes"] or sha(path) != item["sha256"]: raise ValueError("Public original differs: " + name)
            if item.get("url") and item["url"] != name: raise ValueError("Public provenance URL escapes its approved subset")
            if name in selected: raise ValueError("Duplicate public original")
            selected[name] = path; originals += 1
    if originals != 72: raise ValueError("Expected 72 unchanged originals in the eight research series")
    prefix = "content/doctoral-data/monash-d2o-10"
    manifest_path = ACADEMY / prefix / "provenance.json"
    manifest = read_json(safe_file(ACADEMY, manifest_path))
    if manifest.get("sourceDOI") != DATA_DOI or manifest.get("license", {}).get("name") != "CC BY 4.0": raise ValueError("Legacy public source/license differs")
    selected[prefix + "/provenance.json"] = manifest_path
    for item in manifest["files"]:
        name = prefix + "/" + relative_path(item["path"]); path = safe_file(ACADEMY, ACADEMY / name)
        if path.stat().st_size != item["bytes"] or sha(path) != item["sha256"]: raise ValueError("Legacy public original differs: " + name)
        selected[name] = path
    return dict(sorted(selected.items()))


def qa_passes(data):
    if data.get("passed") is False or data.get("failed", 0) != 0: return False
    for key in ("checks", "tests"):
        rows = data.get(key)
        if isinstance(rows, list) and rows:
            return all(isinstance(row, dict) and row.get("passed") is True for row in rows)
    count = data.get("passed")
    if isinstance(count, int) and not isinstance(count, bool): return count > 0 and data.get("failed") == 0
    if count is True and data.get("allPagesVisuallyReviewed") is True and data.get("outputs"):
        return all(isinstance(row, dict) and re.fullmatch(r"[a-f0-9]{64}", str(row.get("sha256", ""))) for row in data["outputs"])
    return False


def check_report_sources(data, report_name):
    for item in data.get("sources", []):
        if isinstance(item, dict) and item.get("sha256") and (item.get("file") or item.get("path")):
            raw = item.get("path") or "web/" + item["file"]
            p = ACADEMY / relative_path(raw)
            if sha(safe_file(ACADEMY, p)) != item["sha256"]: raise ValueError("QA source identity is stale: " + raw)
    simple = data.get("sourceSha256")
    if isinstance(simple, str):
        targets = {"research-journey": "web/research-journey.js", "research-pilot-panel": "web/research-pilot-panel.js", "spatial-encoding": "web/spatial-encoding.js", "learning-path": "web/learning-path.js"}
        matches = [target for marker, target in targets.items() if marker in report_name]
        if len(matches) == 1 and sha(ACADEMY / matches[0]) != simple: raise ValueError("QA was run against an earlier source: " + matches[0])


def check_review(path, expected_sha256):
    path = Path(path).resolve()
    if not path.is_relative_to(ACADEMY.resolve()): raise ValueError("Root review must remain within the Academy evidence directory")
    safe_file(ACADEMY, path)
    if not re.fullmatch(r"[a-fA-F0-9]{64}", expected_sha256 or "") or sha(path) != expected_sha256.lower(): raise ValueError("Root review SHA256 mismatch")
    review = read_json(path)
    if review.get("version") != VERSION or review.get("passed") is not True: raise ValueError("Root review has not passed for version 1.3.0")
    checked = {}
    for group in ("engines", "qa", "manuals"):
        rows = review.get(group)
        if not isinstance(rows, list) or not rows: raise ValueError("Review requires explicit " + group + " identities")
        checked[group] = set()
        for row in rows:
            name = relative_path(row["path"])
            if name in checked[group]: raise ValueError("Duplicate review identity: " + name)
            source = safe_file(ACADEMY, ACADEMY / name)
            if sha(source) != row.get("sha256") or "bytes" in row and source.stat().st_size != row["bytes"]: raise ValueError("Reviewed file changed: " + name)
            if group == "qa":
                data = read_json(source)
                if not qa_passes(data): raise ValueError("QA contains failures or has no concrete passing checks: " + name)
                check_report_sources(data, name)
            if group == "manuals":
                if source.read_bytes()[:5] != b"%PDF-" or source.stat().st_size < 20000: raise ValueError("Final PDF manual is missing/invalid: " + name)
            checked[group].add(name)
    if not set(REQUIRED_ENGINES).issubset(checked["engines"]): raise ValueError("Review does not cover all active research engines/UI/content")
    if not {"docs/" + n for n in MANUALS}.issubset(checked["manuals"]): raise ValueError("Review does not cover all four final ES/EN manuals")
    return {"path": path.relative_to(ACADEMY).as_posix(), "sha256": sha(path), "passed": True, "engines": len(checked["engines"]), "qaReports": len(checked["qa"]), "manuals": len(checked["manuals"])}


def scope_files():
    paths = [WEB / n for n in TOP_FILES if n.startswith(("research-", "spatial-", "learning-"))]
    paths += [WEB / "content" / n for n in ("course.json", "derivations.json", "doctoral-cases.json", "research-library.json", "research-tutor-knowledge.json")]
    paths += [WEB / name for name in licensed_data_sources()]
    if VERSION == "1.3.1":
        # This source identity already binds all doctoral engines; it does not
        # include this research identity or the bundle, so no hash cycle exists.
        paths += [WEB / "content/doctoral-manifest.json"]
    return sorted(set(paths))


def prepare():
    for name in TOP_FILES: safe_file(ACADEMY, WEB / name)
    for name, digest in LEGACY_HASHES.items():
        if sha(ACADEMY / name) != digest: raise ValueError("Frozen original curriculum identity changed: " + name)
    data_files = licensed_data_sources()
    enough_space(WEB, sum(p.stat().st_size for p in data_files.values()) + sum((ACADEMY / "docs" / n).stat().st_size for n in MANUALS if (ACADEMY / "docs" / n).is_file()))
    if VERSION == "1.3.1":
        from build_doctoral_identity_v131 import build_manifest
        write_changed(ACADEMY / "content/doctoral-manifest.json", encoded(build_manifest(ACADEMY)))
    for name in CONTENT_FILES:
        safe_file(ACADEMY, ACADEMY / "content" / name)
        write_changed(WEB / "content" / name, public_metadata(name))
    for name, source in data_files.items(): copy_changed(source, WEB / name)
    for name in (*MANUALS, *LEGACY_MANUALS):
        source = ACADEMY / "docs" / name
        if source.is_file(): copy_changed(source, WEB / "docs" / name)
    # Existing prepared legacy Lab, slides, MathJax and brand are read-only.
    for name in ("lab/index.html", "mathjax/tex-svg-full.js", "content/slides/slide-01.png"):
        if name.endswith("slide-01.png"):
            if not any((WEB / "content/slides").glob("*.png")): raise FileNotFoundError("Prepared legacy slide images are required")
        else: safe_file(ACADEMY, WEB / name)
    identity = {"schema": "academy-research-content-identity/1", "version": VERSION,
        "scope": "Exact public research engines and curriculum/data identity only; no review, hardware or educational validation is asserted here.",
        "files": [record(p, WEB) for p in scope_files()]}
    write_changed(WEB / "content/research-manifest.json", encoded(identity))
    research_sha = sha(WEB / "content/research-manifest.json")
    previous = read_json(WEB / "bundle-manifest.json") if (WEB / "bundle-manifest.json").is_file() else {}
    bundle = {**previous, "version": VERSION, "application": "DiffAtOnce Academy", "edition": "browser-no-beatrix", "releaseStatus": "local-qa-pending-root-review", "researchReleaseStatus": "pending-root-review",
        "courseSha256": sha(WEB / "content/course.json"), "derivationsSha256": sha(WEB / "content/derivations.json"), "researchContentSha256": research_sha,
        "researchIdentityFile": "content/research-manifest.json", "researchLibrarySha256": sha(WEB / "content/research-library.json"), "researchTutorKnowledgeSha256": sha(WEB / "content/research-tutor-knowledge.json"),
        "researchStages": 12, "researchPilot": "voluntary-local-pre-post-delayed-seven-days", "publicResearchSeries": 8, "unchangedResearchOriginalFiles": 72,
        "localProgressOnly": True, "localNotebookOnly": True, "beatrix": False, "browserLLM": False, "researchHintMode": "reviewed-documentary-source-guidance",
        "scientificScope": "Teaching models and attributed public data. b/D remain conditional; no instrument operation, absolute calibration, chemical identity or measured student efficacy is established.",
        "manuals": ["docs/" + n for n in MANUALS], "excluded": ["GGUF/model weights", "private article PDFs", "student records", "QA artifacts", "credentials", "instrument access"]}
    bundle.pop("rootReview", None)
    if VERSION == "1.3.1":
        doctoral = read_json(WEB / "content/doctoral-manifest.json")
        bundle.update(doctoralContentSha256=sha(WEB / "content/doctoral-manifest.json"),
            doctoralCasesSha256=sha(WEB / "content/doctoral-cases.json"),
            doctoralReleaseStatus="pending-root-review", doctoralActivities=len(doctoral["activities"]),
            doctoralIncludedInLLMTraining=False, doctoralHintMode="reviewed-documentary-only",
            doctoralIdentitySchema=doctoral["schema"],
            doctoralOriginalVersion=doctoral["historicalQualification"]["version"],
            doctoralOriginalManifestSha256=doctoral["historicalQualification"]["manifestSha256"])
    write_changed(WEB / "bundle-manifest.json", encoded(bundle))
    return {"version": VERSION, "prepared": True, "published": False, "releaseStatus": bundle["releaseStatus"], "researchContentSha256": research_sha,
            "publicResearchSeries": 8, "unchangedResearchOriginalFiles": 72, "finalManualsPresent": sum((WEB / "docs" / n).is_file() for n in MANUALS)}


def public_files():
    selected = {n: safe_file(ACADEMY, WEB / n) for n in TOP_FILES}
    selected["bundle-manifest.json"] = safe_file(ACADEMY, WEB / "bundle-manifest.json")
    for folder in ("content", "lab", "mathjax", "screenshots", "docs"):
        for source in safe_tree(WEB / folder):
            name = source.relative_to(WEB).as_posix()
            if any(part in {"qa", "tests", "__pycache__", "node_modules", ".git"} or part.startswith(".") for part in source.relative_to(WEB).parts): raise ValueError("Unapproved public tree member: " + name)
            if source.suffix.lower() in {".gguf", ".safetensors", ".zip", ".exe", ".dll", ".pdb", ".py", ".ps1", ".pyc", ".log"}: raise ValueError("Runtime/private file in public tree: " + name)
            if source.suffix.lower() == ".pdf" and name not in {"docs/" + n for n in (*MANUALS, *LEGACY_MANUALS)}: raise ValueError("Unrecognized PDF in public assets: " + name)
            selected[name] = source
    allowed_content = {"content/" + n for n in CONTENT_FILES} | {"content/research-manifest.json"} | set(licensed_data_sources())
    for name in selected:
        if name.startswith("content/") and not name.startswith("content/slides/") and name not in allowed_content: raise ValueError("Unapproved public content file: " + name)
    if len(selected) != len({n.casefold() for n in selected}): raise ValueError("Case-insensitive public path collision")
    return dict(sorted(selected.items()))


def verify_frozen(folder):
    folder = Path(folder)
    safe_file(folder, folder / "WEB_RELEASE_SHA256.json")
    manifest = read_json(folder / "WEB_RELEASE_SHA256.json")
    if manifest.get("version") != VERSION or manifest.get("releaseStatus") != "reviewed-teaching-software": raise ValueError("Existing final folder is not the reviewed version")
    expected = {relative_path(r["path"]): r for r in manifest["files"]}
    actual = {p.relative_to(folder).as_posix(): p for p in safe_tree(folder) if p.relative_to(folder).as_posix() != "WEB_RELEASE_SHA256.json"}
    if set(actual) != set(expected): raise ValueError("Final public membership differs")
    for name, path in actual.items():
        r = expected[name]
        if path.stat().st_size != r["bytes"] or sha(path) != r["sha256"]: raise ValueError("Final public bytes differ: " + name)
    if sha(folder / "content/research-manifest.json") != manifest["researchContentSha256"]: raise ValueError("Final research identity differs")
    if read_json(folder / "bundle-manifest.json")["researchContentSha256"] != manifest["researchContentSha256"]: raise ValueError("Learning scope and public identity differ")
    if VERSION == "1.3.1":
        bundle = read_json(folder / "bundle-manifest.json")
        if bundle.get("doctoralReleaseStatus") != "reviewed-teaching-software" or bundle.get("doctoralContentSha256") != sha(folder / "content/doctoral-manifest.json"):
            raise ValueError("Frozen doctoral approval and identity differ")
        if bundle.get("rootReview", {}).get("sha256") != manifest.get("rootReview", {}).get("sha256"):
            raise ValueError("Doctoral approval is not bound to the same root review")
    return manifest


def freeze(review_path, review_sha256, output=None):
    output = DEFAULT_RELEASE if output is None else output
    review = check_review(review_path, review_sha256)
    safe_write_parents(Path(output).absolute() / "placeholder")
    output = Path(output).resolve()
    if output.name != "v" + VERSION or not output.is_relative_to(WORKSPACE.resolve()) or output.is_relative_to(ACADEMY.resolve()): raise ValueError("Choose a new workspace versioned public folder named v" + VERSION + " outside Academy sources")
    if output.exists():
        existing = verify_frozen(output)
        if existing.get("rootReview", {}).get("sha256") != review["sha256"]: raise FileExistsError("Existing final version belongs to another review; it is never overwritten")
        # A repeated --prepare honestly resets the local bundle to pending.
        # Restore only that generated metadata after checking every other local
        # member against the already reviewed final tree; never replace sources.
        prepare()
        current = public_files(); expected = {r["path"]: r for r in existing["files"]}
        if set(current) != set(expected): raise ValueError("Local public membership changed after the final freeze")
        for name, path in current.items():
            if name != "bundle-manifest.json" and (path.stat().st_size != expected[name]["bytes"] or sha(path) != expected[name]["sha256"]):
                raise ValueError("Local asset changed after the final freeze: " + name)
        write_changed(WEB / "bundle-manifest.json", (output / "bundle-manifest.json").read_bytes())
        check_review(review_path, review_sha256)
        return {"frozen": True, "alreadyPresent": True, "path": str(output), "files": len(existing["files"]), "researchContentSha256": existing["researchContentSha256"]}
    prepared = prepare()
    check_review(review_path, review_sha256)
    bundle = read_json(WEB / "bundle-manifest.json")
    bundle.update(releaseStatus="reviewed-teaching-software", researchReleaseStatus="reviewed-teaching-software", rootReview=review)
    if VERSION == "1.3.1": bundle["doctoralReleaseStatus"] = "reviewed-teaching-software"
    write_changed(WEB / "bundle-manifest.json", encoded(bundle))
    selected = public_files(); records = [record(p, WEB) for p in selected.values()]
    enough_space(output, sum(r["bytes"] for r in records))
    pending = output.with_name(output.name + ".pending-" + prepared["researchContentSha256"][:12])
    if pending.exists(): raise FileExistsError("Preserve/review existing pending build before retry: " + str(pending))
    pending.mkdir(parents=True)
    for r in records:
        source, target = selected[r["path"]], pending / r["path"]
        copy_changed(source, target)
        if sha(target) != r["sha256"]: raise ValueError("Input changed during freeze: " + r["path"])
    manifest = {**bundle, "publicRoot": "https://diffatonce.com/assets/academy/v" + VERSION + "/", "files": records, "manifestSelfHash": "Excluded from its own file list; outer deployment/package digest covers this file.", "published": False}
    (pending / "WEB_RELEASE_SHA256.json").write_bytes(encoded(manifest))
    verify_frozen(pending)
    check_review(review_path, review_sha256)
    if output.exists(): raise FileExistsError("Final output appeared during freeze; preserve pending evidence")
    pending.rename(output)
    return {"frozen": True, "published": False, "path": str(output), "files": len(records), "bytes": sum(r["bytes"] for r in records), "researchContentSha256": prepared["researchContentSha256"], "rootReviewSha256": review["sha256"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--freeze", action="store_true")
    mode.add_argument("--inspect", action="store_true")
    parser.add_argument("--review", type=Path)
    parser.add_argument("--review-sha256")
    parser.add_argument("--output", type=Path, default=DEFAULT_RELEASE)
    args = parser.parse_args()
    if args.prepare: result = prepare()
    elif args.inspect:
        data = licensed_data_sources()
        result = {"version": VERSION, "readOnly": True, "requiredEngines": REQUIRED_ENGINES, "requiredManuals": ["docs/" + n for n in MANUALS], "publicSubsetFilesIncludingProvenance": len(data), "newResearchSeries": 8, "newResearchOriginalFiles": 72, "modelWeightsIncluded": False}
    else:
        if not args.review or not args.review_sha256: parser.error("--freeze requires --review and --review-sha256")
        result = freeze(args.review, args.review_sha256, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__": raise SystemExit(main())
