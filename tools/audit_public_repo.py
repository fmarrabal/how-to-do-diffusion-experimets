#!/usr/bin/env python3
"""Check teaching distribution integrity, portability and local Markdown links.

Standard library only. No instrument, model/API call or original input access.
--write-manifest records current distribution hashes after all checks pass.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = {".git", "__pycache__", ".pytest_cache", ".jython_cache", "cache"}
MANIFEST = ROOT / "provenance/repository-files.json"
PRIVATE_PATH = re.compile(r"(?<![A-Za-z0-9])[CE]:[\\/]+(?:Users|ARTICULOS-CIENTIFICOS|EXPERIMENTOS-RMN|BBBB_EXPERIMENTOS_DIFUSION)[\\/]+[^\s\"'<>]+", re.I)
TOKEN = re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{35,}|sk-[A-Za-z0-9]{32,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)")
LINK = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]+)\)")
NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files():
    return sorted(path for path in ROOT.rglob("*") if path.is_file() and
                  not any(part in SKIP_PARTS for part in path.relative_to(ROOT).parts) and
                  not path.name.endswith((".pyc", ".class")) and not path.name.startswith("~$"))


def audit():
    errors = []
    checked = files()
    for path in checked:
        relative = path.relative_to(ROOT).as_posix()
        if path.stat().st_size >= 50 * 1024 * 1024:
            errors.append("Review oversized distribution file: " + relative)
        if path.name in {"fid", "ser", "1r", "1i", "2rr", "acqus", "procs", ".env"}:
            errors.append("Original/private input in release: " + relative)
        if path.suffix.lower() in {".md", ".txt", ".py", ".pyw", ".ps1", ".json", ".csv", ".html"}:
            text = path.read_text(encoding="utf-8-sig")
            # The privacy regex source is intentionally present in the audit
            # and preparation tools; actual path/token values must not be.
            if PRIVATE_PATH.search(text):
                errors.append("Absolute local path in text: " + relative)
            if TOKEN.search(text):
                errors.append("Potential secret in text: " + relative)
            if re.search(r"\bZ\d{6}_\d{4}\b", text):
                errors.append("Probe serial in text: " + relative)
            if path.suffix.lower() == ".md":
                if text.count("```") % 2:
                    errors.append("Unbalanced code fences: " + relative)
                for link in LINK.findall(text):
                    target = link.strip().strip("<>")
                    # Support ordinary optional Markdown link titles.
                    target = target.split(' "', 1)[0]
                    url = urlsplit(target)
                    if url.scheme or target.startswith(("#", "//")):
                        continue
                    dest = (path.parent / unquote(url.path)).resolve()
                    if ROOT != dest and ROOT not in dest.parents:
                        errors.append("Link escapes repository: " + relative)
                    elif not dest.exists():
                        errors.append("Broken local link in %s: %s" % (relative, target))
    presentation_manifest = json.loads((ROOT / "provenance/presentation-manifest.json").read_text(encoding="utf-8"))
    for item in presentation_manifest["files"]:
        path = ROOT / item["file"]
        if digest(path) != item["public_sha256"]:
            errors.append("Presentation manifest hash mismatch: " + item["file"])
    for lang in ("en", "es"):
        path = ROOT / ("presentations/%s/workshop-%s.pptx" % (lang, lang))
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                errors.append("Corrupt presentation: " + lang)
            slides = [name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)]
            notes = [name for name in archive.namelist() if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)]
            hidden = sum(ET.fromstring(archive.read(name)).get("show", "1") == "0" for name in slides)
            videos = [name for name in archive.namelist() if name.startswith("ppt/media/") and name.endswith(".mp4")]
            if (len(slides), len(notes), hidden, len(videos)) != (45, 45, 20, 7):
                errors.append("Incomplete presentation: " + lang)
            for name in archive.namelist():
                if name.endswith((".xml", ".rels")) and PRIVATE_PATH.search(archive.read(name).decode("utf-8")):
                    errors.append("Local textual path in presentation: " + lang + "/" + name)
        text = (ROOT / "docs" / lang / "presentation-content.md").read_text(encoding="utf-8")
        if len(re.findall(r"^## \d{2}\. ", text, flags=re.M)) != 45:
            errors.append("Incomplete GitHub presentation transcript: " + lang)
    for path in (ROOT / "python/ramp_generator").glob("config_*.json"):
        if json.loads(path.read_text(encoding="utf-8"))["example_only"] is not True:
            errors.append("Shipped example is operational rather than blocked: " + path.name)
    return checked, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    checked, errors = audit()
    if errors:
        for error in errors:
            print("FAIL: " + error, file=sys.stderr)
        return 1
    if args.write_manifest:
        payload = {"schema_version": 1, "scope": "Public teaching distribution; integrity, not experimental validation",
                   "files": [{"file": path.relative_to(ROOT).as_posix(), "sha256": digest(path),
                              "bytes": path.stat().st_size} for path in checked if path != MANIFEST]}
        MANIFEST.write_bytes((json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    elif MANIFEST.exists():
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
        for item in payload["files"]:
            path = ROOT / item["file"]
            if not path.exists() or digest(path) != item["sha256"]:
                print("FAIL: repository hash mismatch: " + item["file"], file=sys.stderr)
                return 1
        expected = {item["file"] for item in payload["files"]}
        actual = {path.relative_to(ROOT).as_posix() for path in checked if path != MANIFEST}
        if expected != actual:
            print("FAIL: manifest does not cover current distribution files", file=sys.stderr)
            return 1
    else:
        print("FAIL: missing repository manifest; run --write-manifest after review", file=sys.stderr)
        return 1
    print("PASS: %d public files; complete EN/ES decks and notes; links, paths, safety and hashes reviewed. No hardware." % len(checked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
