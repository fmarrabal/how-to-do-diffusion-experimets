"""Stream the reviewed Academy 1.3.1 audit-source distribution.

--inspect is read-only. Packaging requires the current hash-bound root review,
the separately frozen public v1.3.1 bundle and all final bilingual manuals.
Existing source archives, partial files and receipts are never overwritten.
No models, hardlinked inputs, private papers, learner records or QA trees enter
the source allowlist. This script does not prepare, freeze, train or deploy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import zipfile

import build_audit_release_v131 as A
import package_research_source_v13 as S

B = A.B
VERSION = "1.3.1"
PREFIX = "DiffAtOnce-Academy-1.3.1-source/"
TREE_PREFIX = S.TREE_PREFIX
BLOCK = 1024 * 1024
MODEL_METADATA = ("manifest.json", "QWEN_LICENSE.txt", "NOTICE_ACADEMY.txt",
                  "original_manifest_v1.3.json", "training_report.json",
                  "evaluation_report.json", "split-plan.json",
                  "compatibility_semantic_review.json", "COMPATIBILITY_ES.md", "COMPATIBILITY_EN.md",
                  "native_evaluation_report.json", "compatibility_guard_evaluation.json", "compatibility_guard_review.json",
                  "compatibility_guard_closure.json", "compatibility_approval.json")
PUBLICATION_NOTES = """# Academy 1.3.1 source / codigo fuente

ES: parche auditado del curso y los motores WPF/web. Consulte los manuales ES/EN
en desktop/academy/docs y las notas de auditoria incluidas. Las fuentes originales
de entrenamiento y sus identidades se conservan: este paquete no realiza un nuevo
ajuste fino ni acredita inferencia por si solo. Los pesos se excluyen; una
compilacion sin pesos compatibles usa guia documental. La web no ejecuta un LLM.

EN: audited curriculum and WPF/browser-engine patch. Read the ES/EN manuals in
desktop/academy/docs and the included audit notes. Original training sources
and identities are retained: source packaging neither retrains a model nor
establishes inference. Weights are excluded; a build without compatible weights
uses documentary guidance. The browser does not run an LLM.

From the extracted root / Desde la raiz extraida:
    cd desktop/academy
    python tools/build_audit_release_v131.py --prepare
    python -m http.server 8918 --bind 127.0.0.1 --directory web

Open / Abrir:
    http://127.0.0.1:8918/index.html?view=research&lang=es
    http://127.0.0.1:8918/index.html?view=research&lang=en

Windows x64, .NET SDK 8 or newer, Microsoft Edge WebView2 Runtime:
    dotnet restore src/DiffAtOnce.Academy.App/DiffAtOnce.Academy.App.csproj --configfile NuGet.Config
    dotnet build src/DiffAtOnce.Academy.App/DiffAtOnce.Academy.App.csproj -c Release --no-restore
    dotnet run --project src/DiffAtOnce.Academy.App -c Release --no-build

Read SOURCE_BUILD_V13.md as the base build guide together with the 1.3.1 audit
notes. --prepare creates pending local metadata only. It is not a public freeze,
model qualification or deployment. Final packaging requires a separate reviewed
web freeze and current root-review hash. Original 1.3.0 artifacts are preserved.
The original public 1.3.0 WEB_RELEASE_SHA256.json is retained verbatim at its
workspace-relative path so the 1.3.1 builder can check its immutability guard.
It is provenance metadata; the former runtime and private QA are not included.

Numerical regression / Regresion numerica (Node.js 18+):
    node web/tests/research-audit-regressions.test.cjs
    node web/tests/research-journey.test.cjs
    node web/tests/spatial-encoding.test.cjs
    node web/tests/research-independent-review.cjs

Optional browser tests require your own Playwright and Edge/Chromium. Manual
authors may set ACADEMY_NODE and ACADEMY_PDFTOPPM, or place node/pdftoppm on PATH.
manual_verify.py also accepts --pdftoppm. Regenerating a manual requires reviewed
captures and a new complete visual review; the final PDFs are supplied directly.

Three authoring-only path transformations are recorded in SOURCE_SHA256.json:
manual provenance commands, research manual Node discovery and Poppler discovery.
The teaching engines, original experimental values and final PDF bytes are not
changed by those transformations. Public data retain their deposition attribution,
license metadata and upstream third-party rights. No blanket reuse license is
created by this archive.

No GGUF/base model, adapters/checkpoints, runtime environments, private papers,
learner records, raw local exports, private QA or compiled binaries are included.
Public-series D fitting remains blocked without documented b. Monte Carlo
intervals identify the monoexponential estimator; they do not quantify ILT peaks
or centroids. Written arguments require human review. The voluntary local pilot
starts without participants and does not establish educational effectiveness.

SOURCE_SHA256.json records exact members and publication transformations. Its
self-hash is excluded; the outer ZIP SHA256 binds it. Every ZIP member is read
back for CRC, size and SHA256. Software/reference checks are not physical
calibration, molecular identity or measured learning outcomes.
"""


def configure():
    A.configure()
    if B.VERSION != VERSION or B.DEFAULT_RELEASE.name != "v1.3.1":
        raise ValueError("Audit builder did not configure the exact 1.3.1 release")


def portable_helper(relative: str, data: bytes):
    """Only remove author-machine executable paths; retain numerical code."""
    text = data.decode("utf-8-sig")
    before = text
    if relative == "docs/MANUAL_PROVENANCE.md":
        text = re.sub(r"&\s*'[A-Za-z]:/Users/[^']+/dependencies/python/python\.exe'", "python", text)
    elif relative == "tools/build_research_manuals_v13.py":
        old = re.search(r'^RUNTIME\s*=\s*Path\(r?"[A-Za-z]:[^\n]+\)\s*$', text, re.M)
        if old:
            text = text[:old.start()] + 'NODE = os.environ.get("ACADEMY_NODE") or shutil.which("node") or "node"\n' + text[old.end():]
            if not re.search(r"^import os$", text, re.M): text = text.replace("import json\n", "import json\nimport os\n", 1)
            if not re.search(r"^import shutil$", text, re.M): text = text.replace("import re\n", "import re\nimport shutil\n", 1)
            text = text.replace('node = RUNTIME / "node/bin/node.exe"', 'node = NODE')
            if re.search(r"\bRUNTIME\b", text): raise ValueError("Unreviewed research-manual runtime dependency remains")
    elif relative == "tools/manual_verify.py":
        old = re.search(r'^POPLER\s*=\s*Path\("[A-Za-z]:[^\n]+\)\s*$', text, re.M)
        if old:
            text = text[:old.start()] + text[old.end():]
            if not re.search(r"^import os$", text, re.M): text = text.replace("import json\n", "import json\nimport os\n", 1)
            if not re.search(r"^import shutil$", text, re.M): text = text.replace("import os\n", "import os\nimport shutil\n", 1)
            needle = ";args=parser.parse_args()"
            if needle not in text: raise ValueError("Unknown manual-verifier argument contract")
            replacement = ';parser.add_argument("--pdftoppm",default=os.environ.get("ACADEMY_PDFTOPPM") or shutil.which("pdftoppm") or "pdftoppm");args=parser.parse_args();POPLER=Path(args.pdftoppm)'
            text = text.replace(needle, replacement, 1)
    if text == before: return data, None
    return text.encode("utf-8"), "Author-machine executable paths made configurable via PATH/environment; manual rendering/verification equations and supplied PDF bytes unchanged."


def selected_sources():
    configure()
    selected = S.selected_sources()
    for name in MODEL_METADATA:
        path = B.safe_file(B.ACADEMY, B.ACADEMY / "ai/release-v1.3.1" / name)
        relative = path.relative_to(B.ACADEMY).as_posix()
        data = path.read_bytes()
        item = {"path": path}
        if path.suffix.lower() == ".json":
            original = B.read_json(path)
            sanitized = S.sanitize_metadata(original)
            if sanitized != original:
                item.update(data=B.encoded(sanitized), originalSha256=B.sha(path),
                            transformation="Metadata-only local authoring paths omitted; original model/training identities retained.")
        selected[TREE_PREFIX + relative] = item
    selected["README_SOURCE_ES_EN.txt"] = {"data": PUBLICATION_NOTES.encode("utf-8")}
    for name, item in selected.items():
        path = item.get("path")
        if not path: continue
        if path.stat().st_nlink > 1: raise ValueError("Hardlinked source input excluded: " + name)
        relative = path.relative_to(B.ACADEMY).as_posix()
        raw = item.get("data", path.read_bytes())
        if relative in {"docs/MANUAL_PROVENANCE.md", "tools/build_research_manuals_v13.py", "tools/manual_verify.py"}:
            portable, transformation = portable_helper(relative, raw)
            if transformation: item.update(data=portable, originalSha256=B.sha(path), transformation=transformation)
        if path.suffix.lower() in {".py", ".ps1", ".md", ".json", ".jsonl", ".js", ".mjs", ".cjs", ".cs", ".txt", ".xaml", ".csproj"}:
            text = item.get("data", raw).decode("utf-8-sig")
            if re.search(r"[A-Za-z]:[\\/]+(?:Users|Documents and Settings)[\\/]+[^\\/\s]+[\\/]", text):
                raise ValueError("Unreviewed author-home path in public source: " + name)
            if re.search(r"(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-proj-[A-Za-z0-9_-]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)", text):
                raise ValueError("Credential-shaped literal excluded from public source: " + name)
    original_name = "website/release/public_html/assets/academy/v1.3.0/WEB_RELEASE_SHA256.json"
    original = B.safe_file(B.WORKSPACE, B.WORKSPACE / original_name)
    if B.sha(original) != A.ORIGINAL_MANIFEST_SHA256:
        raise ValueError("Original public release provenance changed during selection")
    selected[original_name] = {"data": original.read_bytes(), "originalPath": original_name,
                               "originalSha256": A.ORIGINAL_MANIFEST_SHA256,
                               "transformation": "Original public release manifest retained verbatim as build-guard provenance; no former runtime files."}
    recipe = B.ACADEMY / "tools/ACADEMY_V131_AUDIT_CLEANUP_PREPARATION.md"
    if recipe.is_file():
        B.safe_file(B.ACADEMY, recipe)
        selected[TREE_PREFIX + "tools/" + recipe.name] = {"path": recipe}
    if len(selected) != len({name.casefold() for name in selected}): raise ValueError("Case-insensitive source path collision")
    return dict(sorted(selected.items()))


def verify_archive(path, manifest):
    expected = {PREFIX + row["path"]: row for row in manifest["files"]}
    with zipfile.ZipFile(path) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())) or set(archive.namelist()) != set(expected) | {PREFIX + "SOURCE_SHA256.json"}:
            raise ValueError("Source archive membership differs")
        if archive.read(PREFIX + "SOURCE_SHA256.json") != B.encoded(manifest): raise ValueError("Archive manifest differs")
        for name, row in expected.items():
            digest, length = hashlib.sha256(), 0
            with archive.open(name) as stream:
                for block in iter(lambda: stream.read(BLOCK), b""): digest.update(block); length += len(block)
            if length != row["bytes"] or digest.hexdigest() != row["sha256"]: raise ValueError("Source archive member differs: " + name)
    return True


def package(output, review_path, review_sha256, web_release):
    configure()
    if Path(web_release).resolve() != B.DEFAULT_RELEASE.resolve(): raise ValueError("Use only the exact separately frozen public v1.3.1 folder")
    review, frozen = B.check_review(review_path, review_sha256), B.verify_frozen(web_release)
    if frozen.get("rootReview", {}).get("sha256") != review["sha256"]: raise ValueError("Root review and frozen public release disagree")
    project = B.ACADEMY / "src/DiffAtOnce.Academy.App/DiffAtOnce.Academy.App.csproj"
    if "<Version>1.3.1</Version>" not in project.read_text(encoding="utf-8-sig"): raise ValueError("WPF source version differs")
    for row in frozen["files"]:
        source = B.safe_file(B.ACADEMY, B.WEB / row["path"])
        if source.stat().st_size != row["bytes"] or B.sha(source) != row["sha256"]: raise ValueError("Runtime changed after final freeze: " + row["path"])
    selected = selected_sources(); records = S.entry_records(selected)
    if not {TREE_PREFIX + "docs/" + name for name in B.MANUALS}.issubset(selected): raise ValueError("Final bilingual manual omitted")
    output = Path(output).absolute()
    if ".." in output.parts:
        raise ValueError("Use an exact output path without parent traversal")
    B.safe_write_parents(output)
    if output.name != "DiffAtOnce-Academy-1.3.1-source.zip" or output.is_relative_to(B.ACADEMY):
        raise ValueError("Use a new exact DiffAtOnce-Academy-1.3.1-source.zip outside Academy sources")
    sidecar = output.with_suffix(output.suffix + ".sha256.json")
    manifest = {"schema": "academy-reviewed-source/1", "version": VERSION, "files": records,
                "researchContentSha256": frozen["researchContentSha256"], "rootReview": review,
                "publicWebManifestSha256": B.sha(Path(web_release) / "WEB_RELEASE_SHA256.json"),
                "modelMetadataFile": TREE_PREFIX + "ai/release-v1.3.1/manifest.json",
                "modelWeightsIncluded": False, "newTrainingPerformed": False, "studentDataIncluded": False,
                "privatePapersIncluded": False, "privateQaIncluded": False, "expandedSourceCopyCreated": False,
                "experimentalValidation": False, "educationalEfficacyEstablished": False,
                "manifestSelfHash": "Excluded from its own member list; final outer ZIP SHA256 binds this manifest."}
    if output.exists():
        if not sidecar.is_file(): raise FileExistsError("Preserve existing archive without a receipt")
        receipt = B.read_json(sidecar)
        if receipt.get("sha256") != B.sha(output) or receipt.get("sourceManifest") != manifest: raise FileExistsError("Preserve existing source package; it differs")
        verify_archive(output, manifest)
        return {"archive": output.name, "alreadyPresent": True, "bytes": output.stat().st_size, "sha256": receipt["sha256"]}
    partial = output.with_suffix(output.suffix + ".partial")
    if sidecar.exists() or partial.exists(): raise FileExistsError("Preserve existing receipt/partial archive")
    B.enough_space(output, sum(row["bytes"] for row in records)); output.parent.mkdir(parents=True, exist_ok=True)
    expected = {row["path"]: row for row in records}
    with partial.open("xb") as target, zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
        archive.writestr(S.zip_info(PREFIX + "SOURCE_SHA256.json"), B.encoded(manifest))
        for name, item in selected.items():
            if "data" in item: archive.writestr(S.zip_info(PREFIX + name), item["data"]); continue
            digest, length = hashlib.sha256(), 0
            with item["path"].open("rb") as source, archive.open(S.zip_info(PREFIX + name), "w", force_zip64=True) as dest:
                for block in iter(lambda: source.read(BLOCK), b""): dest.write(block); digest.update(block); length += len(block)
            if length != expected[name]["bytes"] or digest.hexdigest() != expected[name]["sha256"]: raise ValueError("Source changed while packaging: " + name)
    verify_archive(partial, manifest); B.check_review(review_path, review_sha256)
    if S.entry_records(selected_sources()) != records: raise ValueError("Source allowlist/bytes changed during packaging; partial preserved")
    if output.exists(): raise FileExistsError("Final archive appeared during verification; partial preserved")
    if os.name == "nt": partial.rename(output)
    else: os.link(partial, output); partial.unlink()
    receipt = {"archive": output.name, "bytes": output.stat().st_size, "sha256": B.sha(output),
               "fileCount": len(records), "zipEntryCount": len(records) + 1, "crcVerified": True,
               "allEntriesReadAndHashed": True, "membershipVerified": True,
               "expandedSourceCopyCreated": False, "sourceManifest": manifest}
    with sidecar.open("xb") as stream: stream.write(B.encoded(receipt))
    return {key: value for key, value in receipt.items() if key != "sourceManifest"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--review-sha256")
    parser.add_argument("--web-release", type=Path)
    args = parser.parse_args(); configure()
    if args.inspect:
        selected = selected_sources(); records = S.entry_records(selected)
        print(json.dumps({"version": VERSION, "readOnly": True, "files": len(records), "bytes": sum(row["bytes"] for row in records),
                          "modelWeightsIncluded": False, "newTrainingPerformed": False, "expandedSourceCopyCreated": False,
                          "transformations": [row for row in records if row.get("transformation")], "paths": list(selected)}, indent=2))
    else:
        if not args.output or not args.review or not args.review_sha256: parser.error("Packaging requires --output, --review and --review-sha256")
        print(json.dumps(package(args.output, args.review, args.review_sha256, args.web_release or B.DEFAULT_RELEASE), indent=2))
    return 0


if __name__ == "__main__": raise SystemExit(main())
