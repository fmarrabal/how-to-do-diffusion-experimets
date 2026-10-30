"""Deterministic doctoral 1.3.1 software identity, without rebadging 1.2 QA.

The original 1.2 manifest is retained verbatim. This generator hashes current
teaching sources and itself; it excludes its generated output and bundle/review
files so there is no circular hash. It never approves a release, trains a model,
operates an instrument or creates learner/pilot records. The separate root-bound
bundle changes from pending to reviewed only at the public software freeze.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

VERSION = "1.3.1"
ORIGINAL_FILE = "content/doctoral-manifest-v1.2.0.json"
ORIGINAL_SHA256 = "0f87e569f19c032af756c02cdd0aceb33b38fb87cdd9dd78727f9f246d8a588c"
EXTRA_FILES = (
    "content/course.json", "content/derivations.json", ORIGINAL_FILE,
    "web/calculators.js", "web/waveform-lab.js",
    "docs/AUDIT_1_3_1_ES_EN.md", "docs/RESEARCH_GUIDE_ES.md", "docs/RESEARCH_GUIDE_EN.md",
    "docs/ACADEMY_MANUAL_ES.pdf", "docs/ACADEMY_MANUAL_EN.pdf",
    "docs/RESEARCH_MANUAL_ES.pdf", "docs/RESEARCH_MANUAL_EN.pdf",
    "tools/build_doctoral_identity_v131.py",
)
FORBIDDEN_CIRCULAR = {
    "content/doctoral-manifest.json", "web/content/doctoral-manifest.json",
    "content/research-manifest.json", "web/content/research-manifest.json",
    "web/bundle-manifest.json",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source(root, name):
    if not isinstance(name, str) or "\\" in name or ":" in name:
        raise ValueError("Expected a relative POSIX source path")
    relative = PurePosixPath(name)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise ValueError("Unsafe doctoral source path")
    if name in FORBIDDEN_CIRCULAR:
        raise ValueError("Generated identities cannot hash themselves or each other")
    root = Path(root).resolve()
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink() or getattr(current.lstat(), "st_file_attributes", 0) & 1024:
            raise ValueError("Linked doctoral source excluded: " + name)
    if not current.is_file() or not current.resolve().is_relative_to(root):
        raise ValueError("Doctoral source escapes its root")
    return current


def build_manifest(root, *, original_sha256=ORIGINAL_SHA256):
    """Read only; the reviewed prepare builder writes the returned identity."""
    root = Path(root)
    original_path = source(root, ORIGINAL_FILE)
    if sha(original_path) != original_sha256:
        raise ValueError("The original doctoral 1.2 history has changed")
    original = json.loads(original_path.read_text(encoding="utf-8-sig"))
    if original.get("version") != "1.2.0" or original.get("includedInLLMTraining") is not False:
        raise ValueError("Original documentary/training provenance differs")
    names = sorted({row["path"] for row in original["files"]} | set(EXTRA_FILES))
    if len(names) != len({name.casefold() for name in names}):
        raise ValueError("Case-insensitive doctoral source collision")
    files = []
    for name in names:
        path = source(root, name)
        files.append({"path": name, "bytes": path.stat().st_size, "sha256": sha(path)})
    preserved = {key: original[key] for key in (
        "application", "activities", "guidedSteps", "objectiveTasks",
        "documentaryTasksRequiringHumanReview", "numericSubchecks", "scope",
        "modelBoundaries", "publicDataset",
    )}
    return {
        **preserved,
        "schema": "academy-doctoral-content-identity/2",
        "version": VERSION,
        "releaseStatus": "identity-only",
        "releaseApprovalFile": "bundle-manifest.json",
        "releaseApprovalField": "doctoralReleaseStatus",
        "approvalScope": "Only a separate hash-bound root software review/freeze may approve the current bundle. This file records identity, not a current QA, hardware, chemical or educational-efficacy result.",
        "includedInLLMTraining": False,
        "newTrainingPerformed": False,
        "hintMode": "reviewed-documentary-only",
        "studentRecordsIncluded": False,
        "pilotOutcomesClaimed": False,
        "historicalQualification": {
            "version": original["version"],
            "manifestFile": ORIGINAL_FILE,
            "manifestSha256": original_sha256,
            "releaseStatus": original["releaseStatus"],
            "includedInLLMTraining": original["includedInLLMTraining"],
            "qa": original["qa"],
            "scope": "Unmodified original 1.2 teaching-software/QA history only. It does not qualify modified 1.3.1 sources, model compatibility or a learner cohort.",
        },
        "auditPatch": {
            "notes": "docs/AUDIT_1_3_1_ES_EN.md",
            "scope": "Literal ES/EN thermal rounding and equation-prose corrections, explicit estimator/nullspace boundaries, signed/minimum-b processing controls and finite/range guards. See separate current source-bound software QA and root review.",
            "currentQAApprovalAsserted": False,
            "experimentalValidation": False,
            "educationalEfficacyEstablished": False,
        },
        "files": files,
        "identitySelfHash": "Excluded: this output, generated mirrors, bundle and root review are not source members. The bundle SHA256 binds this complete identity.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    manifest = build_manifest(args.root)
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
