"""Stream an allowlisted, reviewed Academy 1.3 source ZIP without an expanded copy.

No GGUF, base model, adapter/checkpoint, environment, private paper, student data,
downloaded full dataset archive, QA output or previous binary package is selected.
Every ZIP member is read back for CRC, SHA256, size and exact membership.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import zipfile
import build_research_release_v13 as B

ACADEMY, VERSION = B.ACADEMY, B.VERSION
PREFIX = "DiffAtOnce-Academy-1.3.0-source/"
TREE_PREFIX = "desktop/academy/"
BLOCK = 1024 * 1024
SKIP_DIRS = {"bin", "obj", "qa", ".git", ".vs", ".venv", "venv", "__pycache__", "node_modules", "checkpoints", "checkpoint", "merged", "base", "base-1.7b", "work-v1", "work-v2", "work-v3", "runtime-data", "student-work"}
CODE_EXTS = {".cs", ".csproj", ".xaml", ".sln", ".slnx", ".props", ".targets", ".resx", ".config", ".md", ".txt", ".py", ".ps1", ".html", ".js", ".cjs", ".mjs", ".css", ".svg", ".png", ".jpg", ".jpeg", ".ico", ".gif", ".mp4", ".xml", ".nuspec", ".toml", ".yml", ".yaml", ".jinja"}
PRIVATE_EXTS = {".gguf", ".safetensors", ".bin", ".zip", ".rar", ".7z", ".exe", ".dll", ".pdb", ".pyc", ".log", ".tmp", ".bak"}
ROOT_README = """DiffAtOnce Academy 1.3 - source / codigo fuente

ES: este ZIP preserva desktop/academy con el codigo WPF, el runtime web compartido,
el recorrido de investigacion, el piloto local voluntario, manuales ES/EN y casos
publicos con licencia CC BY 4.0, atribucion y SHA256. No incluye pesos de modelos,
adaptadores, entornos, articulos privados, datos de estudiantes, QA ni compilados.
Las series publicas son datos reales; una agrupacion del deposito no demuestra
controles de conveccion/temperatura ni replicas identicas. Sin b documentados no
se obtiene D. Los datos originales estan intactos; no se incluye el deposito completo.

EN: this archive preserves desktop/academy with WPF source, the shared browser
runtime, research pathway, voluntary local pilot, ES/EN manuals and licensed
CC BY 4.0 public cases with attribution and SHA256. It excludes model weights,
adapters, environments, private papers, learner data, QA outputs and binaries.
Repository grouping does not establish paired convection/temperature controls.
Undocumented b values cannot produce a validated D. Original files remain intact.

From this extracted folder / Desde esta carpeta:
    cd desktop/academy
    python tools/build_research_release_v13.py --prepare
    python -m http.server 8918 --bind 127.0.0.1 --directory web

Browser / Navegador:
    http://127.0.0.1:8918/index.html?view=research&lang=es
    http://127.0.0.1:8918/index.html?view=research&lang=en

Windows x64 + .NET SDK 8 or newer + Microsoft Edge WebView2 Runtime:
    dotnet restore src/DiffAtOnce.Academy.App/DiffAtOnce.Academy.App.csproj --configfile NuGet.Config
    dotnet build src/DiffAtOnce.Academy.App/DiffAtOnce.Academy.App.csproj -c Release --no-restore
    dotnet run --project src/DiffAtOnce.Academy.App -c Release --no-build

ES: sin pesos compatibles, Beatrix identifica honestamente la guia documental.
El paquete fuente no acredita inferencia LLM ni un nuevo ajuste fino. Los metadatos
historicos del tutor conservan sus identidades originales; no son nuevos resultados.
El navegador no ejecuta un LLM. El piloto empieza con cero participantes y requiere
consentimiento explicito; no se incluyen alumnos ni resultados. La retencion exige
siete dias reales. Los argumentos se revisan por separado mediante rubrica humana.

EN: without compatible weights, Beatrix identifies documentary guidance honestly.
Source packaging does not establish LLM inference or a new fine-tune. Historical
tutor metadata remain historical. The browser has no LLM. The pilot starts with
zero participants, requires explicit consent and includes no learners/outcomes.
Delayed retention requires seven real days; prose uses a separate human rubric.

Numerical checks / Pruebas numericas (Node.js 18+):
    node web/tests/research-journey.test.cjs
    node web/tests/spatial-encoding.test.cjs
    node web/tests/learning-path.test.cjs
    node web/tests/research-pilot-panel.test.cjs
    node web/tests/research-independent-review.cjs

Optional browser harnesses require Playwright and Edge/Chromium. Where an original
development harness referenced the author's local Playwright module, this archive
uses require('playwright'); configure/install your own official testing dependency.
No Node/Python/training environment is required to use the released WPF application.

--prepare creates local pending-review metadata only. Public freeze additionally
requires an explicit root review JSON with current engine, QA and final-manual
hashes. Previous final releases are not replaced. Software integrity and analytic
checks are not hardware calibration, chemical identity or educational efficacy.

Read Docs/ACADEMY_MANUAL_ES.pdf and Docs/RESEARCH_MANUAL_ES.pdf in the portable
application, or docs/ACADEMY_MANUAL_EN.pdf and docs/RESEARCH_MANUAL_EN.pdf here.
SOURCE_SHA256.json records exact selected members, transformations and provenance.
The adjacent ZIP .sha256.json verifies the final archive and full member readback.
"""


def source_tree(folder):
    if not folder.is_dir(): raise FileNotFoundError(folder)
    for current, dirs, files in os.walk(folder, followlinks=False):
        for name in list(dirs):
            p = Path(current) / name
            if p.is_symlink() or getattr(p.lstat(), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT: raise ValueError("Linked source directory excluded: " + str(p))
        dirs[:] = sorted(d for d in dirs if d.lower() not in SKIP_DIRS and not d.lower().endswith("-qa") and not d.startswith("."))
        for name in sorted(files): yield B.safe_file(ACADEMY, Path(current) / name)


def sanitize_metadata(value):
    if isinstance(value, list): return [sanitize_metadata(v) for v in value]
    if isinstance(value, dict): return {k: sanitize_metadata(v) for k, v in value.items()}
    if isinstance(value, str) and re.match(r"^(?:[a-z]:[\\/]|file:///|\\\\|/Users/|/home/)", value, re.I): return "[local-authoring-path-omitted]"
    return value


def selected_sources():
    selected = {}
    def add(p, required=True):
        if not p.exists():
            if required: raise FileNotFoundError(p)
            return
        B.safe_file(ACADEMY, p)
        name = p.relative_to(ACADEMY).as_posix()
        if any(part.lower() in SKIP_DIRS or part.startswith(".env") or any(token in part.lower() for token in ("credential", "student-work", "notebook-export")) for part in Path(name).parts): raise ValueError("Private/generated source excluded: " + name)
        if p.suffix.lower() in PRIVATE_EXTS: raise ValueError("Model/binary/archive excluded: " + name)
        selected[TREE_PREFIX + name] = {"path": p}
    for name in ("README.md", "START_HERE_ES_EN.txt", "SOURCE_BUILD_V12.md", "SOURCE_BUILD_V13.md", "NuGet.Config", "lab-source-hashes.json"):
        add(ACADEMY / name)
    for folder in ("src", "tests", "THIRD_PARTY", "lab"):
        for p in source_tree(ACADEMY / folder):
            if p.name.startswith(".") or p.suffix.lower() in PRIVATE_EXTS: continue
            if p.suffix.lower() in CODE_EXTS or p.name in {"LICENSE", "NOTICE"} or p.name == "ilt-numpy-reference.json": add(p)
    for name in B.CONTENT_FILES: add(ACADEMY / "content" / name)
    for p in B.safe_tree(ACADEMY / "content/slides"): add(p)
    for p in B.licensed_data_sources().values(): add(p)
    # Exact public-runtime membership avoids traversing web/tests/QA/student data.
    for p in B.public_files().values(): add(p)
    for p in source_tree(ACADEMY / "web/tests"):
        if p.suffix.lower() in {".js", ".cjs", ".mjs", ".py", ".md"}: add(p)
    for p in (ACADEMY / "docs").iterdir():
        if not p.is_file(): continue
        if p.suffix.lower() == ".md" or p.name in {*B.MANUALS, *B.LEGACY_MANUALS, "MANUAL_ES.pdf", "MANUAL_EN.pdf"}: add(p)
    for p in (ACADEMY / "tools").iterdir():
        if p.is_file() and p.suffix.lower() in {".py", ".ps1"}: add(p)
    for name in ("README_ES_EN.md", "RESEARCH_TRAINING_V3_ES_EN.md", "academy_research_pipeline_v3.py", "academy_pipeline_v2.py", "academy_pipeline_v1.py", "download_ranged_base.py", "check_converter_provenance.py", "prepare_prompt_parity.py", "test_completion_loss.py", "finalize_release.py"):
        add(ACADEMY / "ai" / name, required=False)
    for folder in ("ai/NativeCheck", "ai/PromptParity", "ai/NativeResearchCheck"):
        if (ACADEMY / folder).is_dir():
            for p in source_tree(ACADEMY / folder):
                if p.suffix.lower() in {".cs", ".csproj", ".md", ".config"}: add(p)
    for name in ("manifest.json", "QWEN_LICENSE.txt", "NOTICE_ACADEMY.txt"):
        add(ACADEMY / "ai/release-v1.1" / name)
        add(ACADEMY / "ai/release-v1.3" / name)
    for name in ("train.jsonl", "dev.jsonl", "test.jsonl", "split-plan.json", "prepare_reproduction.py"):
        add(ACADEMY / "ai/release-v1.3/training-data" / name)
    # Model provenance is small published metadata, not a base-model traversal.
    p = ACADEMY / "ai/base-1.7b/base-provenance.json"
    if p.is_file():
        B.safe_file(ACADEMY, p)
        selected[TREE_PREFIX + "ai/base-provenance.json"] = {"data": B.encoded(sanitize_metadata(B.read_json(p))), "originalPath": "ai/base-1.7b/base-provenance.json", "originalSha256": B.sha(p), "transformation": "metadata-only; omitted local authoring paths; no base-model files"}
    for name, item in selected.items():
        p = item.get("path")
        if not p: continue
        relative = p.relative_to(ACADEMY).as_posix()
        if relative == "content/source-index.json" or relative == "content/algorithm-catalog.json":
            item.update(data=B.public_metadata(p.name), originalSha256=B.sha(p), transformation="same public metadata sanitization as the browser; authoring filesystem paths omitted")
        elif p.suffix.lower() in {".json"} and not relative.startswith(("content/doctoral-data/", "content/research-data/", "web/content/doctoral-data/", "web/content/research-data/")):
            original = B.read_json(p); sanitized = sanitize_metadata(original)
            if sanitized != original: item.update(data=B.encoded(sanitized), originalSha256=B.sha(p), transformation="local authoring paths removed from metadata; scientific values unchanged")
        elif p.suffix.lower() in {".mjs", ".cjs", ".js"} and (relative.startswith("web/tests/") or relative.startswith("web/test_")):
            source = p.read_text(encoding="utf-8-sig")
            portable = re.sub(r"(['\"])[A-Za-z]:[\\/](?:Users|Documents and Settings)[^'\"]*[\\/]node_modules[\\/]playwright\1", "'playwright'", source)
            if portable != source: item.update(data=portable.encode("utf-8"), originalSha256=B.sha(p), transformation="development Playwright import made portable; install/configure your own testing dependency")
    selected["README_SOURCE_ES_EN.txt"] = {"data": ROOT_README.encode("utf-8")}
    if len(selected) != len({n.casefold() for n in selected}): raise ValueError("Case-insensitive source path collision")
    return dict(sorted(selected.items()))


def entry_records(selected):
    records = []
    for name, item in selected.items():
        if "data" in item: length, digest = len(item["data"]), hashlib.sha256(item["data"]).hexdigest()
        else: length, digest = item["path"].stat().st_size, B.sha(item["path"])
        r = {"path": name, "bytes": length, "sha256": digest}
        for key in ("originalPath", "originalSha256", "transformation"):
            if key in item: r[key] = item[key]
        records.append(r)
    return records


def zip_info(name):
    z = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0)); z.compress_type = zipfile.ZIP_DEFLATED; z.create_system = 3; z.external_attr = 0o100644 << 16
    return z


def verify_archive(path, manifest):
    expected = {PREFIX + r["path"]: r for r in manifest["files"]}
    with zipfile.ZipFile(path) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())) or set(archive.namelist()) != set(expected) | {PREFIX + "SOURCE_SHA256.json"}: raise ValueError("Source archive membership differs")
        if archive.read(PREFIX + "SOURCE_SHA256.json") != B.encoded(manifest): raise ValueError("Source manifest changed inside ZIP")
        for name, r in expected.items():
            digest, count = hashlib.sha256(), 0
            with archive.open(name) as stream:
                for block in iter(lambda: stream.read(BLOCK), b""): digest.update(block); count += len(block)
            if count != r["bytes"] or digest.hexdigest() != r["sha256"]: raise ValueError("Source archive member differs: " + name)
    return True


def package(output, review_path, review_sha256, web_release):
    review = B.check_review(review_path, review_sha256); frozen = B.verify_frozen(web_release)
    if frozen.get("rootReview", {}).get("sha256") != review["sha256"]: raise ValueError("Source gate and frozen web release use different reviews")
    selected = selected_sources(); records = entry_records(selected)
    for name in (*B.MANUALS,):
        if TREE_PREFIX + "docs/" + name not in selected: raise ValueError("Final manual omitted from source")
    if "<Version>1.3.0</Version>" not in (ACADEMY / "src/DiffAtOnce.Academy.App/DiffAtOnce.Academy.App.csproj").read_text(): raise ValueError("WPF source version differs")
    for r in frozen["files"]:
        p = B.safe_file(ACADEMY, B.WEB / r["path"])
        if p.stat().st_size != r["bytes"] or B.sha(p) != r["sha256"]: raise ValueError("Local runtime changed after reviewed web freeze: " + r["path"])
    output = Path(output).absolute(); B.safe_write_parents(output)
    if output.suffix.lower() != ".zip" or output.is_relative_to(ACADEMY): raise ValueError("Use a new .zip output outside Academy sources")
    sidecar = output.with_suffix(output.suffix + ".sha256.json")
    manifest = {"schema": "academy-reviewed-source/1", "version": VERSION, "files": records, "researchContentSha256": frozen["researchContentSha256"], "rootReview": review,
        "publicWebManifestSha256": B.sha(Path(web_release) / "WEB_RELEASE_SHA256.json"), "modelWeightsIncluded": False, "studentDataIncluded": False, "privatePapersIncluded": False, "expandedSourceCopyCreated": False,
        "experimentalValidation": False, "educationalEfficacyEstablished": False, "manifestSelfHash": "Excluded from its own member list; the outer ZIP SHA256 covers this manifest."}
    if output.exists():
        if not sidecar.is_file(): raise FileExistsError("Preserve existing archive without its verification receipt")
        receipt = B.read_json(sidecar)
        if receipt.get("sha256") != B.sha(output) or receipt.get("sourceManifest") != manifest: raise FileExistsError("Existing source package differs; it is never overwritten")
        verify_archive(output, manifest)
        return {"archive": output.name, "alreadyPresent": True, "sha256": receipt["sha256"], "bytes": output.stat().st_size}
    if sidecar.exists(): raise FileExistsError("Existing sidecar is preserved")
    partial = output.with_suffix(output.suffix + ".partial")
    if partial.exists(): raise FileExistsError("Existing partial package is preserved: " + str(partial))
    B.enough_space(output, sum(r["bytes"] for r in records)); output.parent.mkdir(parents=True, exist_ok=True)
    by_name = {r["path"]: r for r in records}
    with partial.open("xb") as stream, zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
        archive.writestr(zip_info(PREFIX + "SOURCE_SHA256.json"), B.encoded(manifest))
        for name, item in selected.items():
            expected = by_name[name]
            if "data" in item: archive.writestr(zip_info(PREFIX + name), item["data"]); continue
            digest, count = hashlib.sha256(), 0
            with item["path"].open("rb") as source, archive.open(zip_info(PREFIX + name), "w", force_zip64=True) as destination:
                for block in iter(lambda: source.read(BLOCK), b""): destination.write(block); digest.update(block); count += len(block)
            if count != expected["bytes"] or digest.hexdigest() != expected["sha256"]: raise ValueError("Source changed during packaging: " + name)
    verify_archive(partial, manifest); B.check_review(review_path, review_sha256)
    if output.exists(): raise FileExistsError("Final output appeared during packaging; partial preserved")
    # Windows rename refuses an existing destination. On POSIX create an
    # exclusive hard link first, so final packages are never overwritten.
    if os.name == "nt": partial.rename(output)
    else: os.link(partial, output); partial.unlink()
    result = {"archive": output.name, "bytes": output.stat().st_size, "sha256": B.sha(output), "fileCount": len(records), "zipEntryCount": len(records) + 1,
        "crcVerified": True, "allEntriesReadAndHashed": True, "membershipVerified": True, "expandedSourceCopyCreated": False, "sourceManifest": manifest}
    with sidecar.open("xb") as stream: stream.write(B.encoded(result))
    return {k: v for k, v in result.items() if k != "sourceManifest"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--review-sha256")
    parser.add_argument("--web-release", type=Path, default=B.DEFAULT_RELEASE)
    args = parser.parse_args()
    if args.inspect:
        selected = selected_sources(); records = entry_records(selected)
        print(json.dumps({"version": VERSION, "readOnly": True, "files": len(records), "bytes": sum(r["bytes"] for r in records), "modelWeightsIncluded": False, "expandedSourceCopyCreated": False, "paths": [r["path"] for r in records]}, indent=2))
    else:
        if not args.output or not args.review or not args.review_sha256: parser.error("Packaging requires --output, --review and --review-sha256")
        print(json.dumps(package(args.output, args.review, args.review_sha256, args.web_release), indent=2))
    return 0


if __name__ == "__main__": raise SystemExit(main())
