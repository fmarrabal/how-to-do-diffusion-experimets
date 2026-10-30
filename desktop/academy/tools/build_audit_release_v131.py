"""Prepare or freeze the explicitly reviewed Academy 1.3.1 audit patch.

The original 1.3.0 release is immutable. Three literal curriculum corrections
are bound separately from the original training identity. A final freeze still
requires the exact root review, fresh QA and all four bilingual PDF manuals.
"""
from pathlib import Path
import argparse
import json
import build_research_release_v13 as B

VERSION = "1.3.1"
APPROVED_CONTENT = {
    "content/course.json": "acf7755db563e592af97de0a6a269243342e8e430beec0267da277e794445f18",
    "content/derivations.json": "7e49f5963739ec9e7c2678194b746526a254d573fc3d6eaab5cb8ae27be375b5",
}
ORIGINAL_MANIFEST_SHA256 = "8b73a0bea31c3d81bbfccbac404b8e34a75664a76aa95ed81de089e1cb0380c1"

def configure():
    original = B.WORKSPACE / "website/release/public_html/assets/academy/v1.3.0/WEB_RELEASE_SHA256.json"
    if B.sha(original) != ORIGINAL_MANIFEST_SHA256:
        raise ValueError("The preserved Academy 1.3.0 release has changed")
    for name, digest in APPROVED_CONTENT.items():
        if B.sha(B.ACADEMY / name) != digest:
            raise ValueError("Curriculum differs from the reviewed three-literal correction: " + name)
    B.VERSION = VERSION
    B.DEFAULT_RELEASE = B.WORKSPACE / "website/release/public_html/assets/academy/v1.3.1"
    B.LEGACY_HASHES = dict(APPROVED_CONTENT)
    B.CONTENT_FILES = tuple(dict.fromkeys((*B.CONTENT_FILES, "doctoral-manifest-v1.2.0.json")))
    B.REQUIRED_ENGINES = tuple(dict.fromkeys((*B.REQUIRED_ENGINES,
        "content/course.json", "content/derivations.json", "web/calculators.js", "web/waveform-lab.js",
        "web/doctoral-inquiry.js", "web/doctoral-pedagogy.js", "web/doctoral-pedagogy-ui.js",
        "content/doctoral-manifest.json", "content/doctoral-manifest-v1.2.0.json",
        "tools/build_doctoral_identity_v131.py")))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--review", type=Path)
    parser.add_argument("--review-sha256")
    parser.add_argument("--output", type=Path)
    args=parser.parse_args();configure()
    if args.prepare:
        result=B.prepare()
    elif args.freeze:
        if not args.review or not args.review_sha256:
            parser.error("Freeze requires the current root review and exact SHA256")
        result=B.freeze(args.review,args.review_sha256,args.output or B.DEFAULT_RELEASE)
    else:
        result={"version":VERSION,"readOnly":True,"approvedRuntimeContent":APPROVED_CONTENT,
                "originalReleasePreserved":True,"modelRetrained":False}
    print(json.dumps(result,indent=2))

if __name__ == "__main__":main()
