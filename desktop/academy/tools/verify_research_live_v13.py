"""Read-only public Academy 1.3 integrity QA, explicitly run after upload.

Default mode only inspects the frozen LOCAL manifest. --run-assets performs
public HTTPS GETs on diffatonce.com, four at a time, with at most one retry.
No hosting access, authentication, writes to production, or downloaded file copies.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import socket
import ssl
import stat
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
FROZEN = ROOT / "website/release/public_html/assets/academy/v1.3.0"
QA = ROOT / "desktop/academy/qa/research-1.3/deploy"
ORIGIN = "https://diffatonce.com"
PREFIX = "/assets/academy/v1.3.0/"
MANIFEST = "WEB_RELEASE_SHA256.json"
MANIFEST_SHA = "8b73a0bea31c3d81bbfccbac404b8e34a75664a76aa95ed81de089e1cb0380c1"
REVIEW_SHA = "a7643a75c9c11ec79ef442bdaa8ba007492eb7dfd2202929771260740fae9ad6"
BLOCK = 256 * 1024
TRANSIENT = {408, 425, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524}


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(BLOCK), b""):
            digest.update(block)
    return digest.hexdigest()


def no_links(path):
    for part in [path, *path.parents]:
        if part.exists() or part.is_symlink():
            if part.is_symlink() or getattr(part.lstat(), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise ValueError("Link/reparse path rejected: " + str(part))


def relative(value):
    if not isinstance(value, str) or not value or any(v in value for v in ("\\", ":", "?", "#", "%", "\x00")):
        raise ValueError("Unsafe manifest-relative path")
    p = PurePosixPath(value)
    if p.is_absolute() or any(part in {"", ".", ".."} for part in value.split("/")):
        raise ValueError("Unsafe manifest-relative path")
    return p.as_posix()


def frozen_records():
    no_links(FROZEN)
    manifest = FROZEN / MANIFEST
    if sha(manifest) != MANIFEST_SHA:
        raise ValueError("Frozen manifest differs from the independently pinned release")
    data = json.loads(manifest.read_text(encoding="utf-8-sig"))
    if (data.get("version") != "1.3.0" or data.get("releaseStatus") != "reviewed-teaching-software"
            or data.get("researchReleaseStatus") != "reviewed-teaching-software"
            or data.get("publicRoot") != ORIGIN + PREFIX
            or data.get("rootReview", {}).get("sha256") != REVIEW_SHA
            or data.get("rootReview", {}).get("passed") is not True):
        raise ValueError("The final reviewed browser release is required")
    rows, seen = [], set()
    for item in data["files"]:
        name = relative(item["path"])
        if name.casefold() in seen or name == MANIFEST:
            raise ValueError("Duplicate/self member in frozen manifest")
        seen.add(name.casefold())
        size, digest = item["bytes"], item["sha256"]
        if not isinstance(size, int) or isinstance(size, bool) or size < 0 or not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError("Invalid size or SHA256 in frozen manifest")
        local = FROZEN / name
        no_links(local)
        if not local.is_file() or local.stat().st_size != size or sha(local) != digest:
            raise ValueError("Local frozen member changed: " + name)
        rows.append({"path": name, "bytes": size, "sha256": digest})
    if len(rows) != 286 or sum(r["bytes"] for r in rows) != 96046069:
        raise ValueError("Expected the exact reviewed 286-file release")
    originals = [r for r in rows if r["path"].startswith("content/research-data/") and not r["path"].endswith("/provenance.json")]
    if len(originals) != 72:
        raise ValueError("The eight public series must contain exactly 72 original files")
    # This file is intentionally excluded from its own files[] list. Its local
    # identity is pinned independently, then read back just like every asset.
    rows.append({"path": MANIFEST, "bytes": manifest.stat().st_size, "sha256": MANIFEST_SHA})
    return data, rows


class ScopedRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        url = urllib.parse.urlsplit(newurl)
        if url.scheme != "https" or url.netloc != "diffatonce.com" or not url.path.startswith(PREFIX) or url.fragment:
            raise ValueError("Asset redirect escaped the public versioned origin")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def open_asset(url, timeout):
    request = urllib.request.Request(url, headers={"Accept-Encoding": "identity", "User-Agent": "DiffAtOnce-Academy-public-integrity/1.3"}, method="GET")
    # A fresh opener has no cookie jar, account state or authorization headers.
    return urllib.request.build_opener(ScopedRedirect()).open(request, timeout=timeout)


def expected_media(name, content_type):
    media = (content_type or "").split(";", 1)[0].strip().lower()
    if name.endswith(".pdf"):
        return media == "application/pdf"
    if name.endswith((".js", ".mjs")):
        return media in {"application/javascript", "text/javascript", "application/x-javascript"}
    if name == "brand.png":
        return media == "image/png"
    return True


def verify_asset(record, timeout=30, opener=open_asset, pause=time.sleep):
    attempts, final = [], None
    path = PREFIX + urllib.parse.quote(relative(record["path"]), safe="/")
    for attempt in range(2):
        url = ORIGIN + path
        if attempt:
            url += "?" + urllib.parse.urlencode({"academy_integrity": record["sha256"][:20]})
        started, count, digest = time.monotonic(), 0, hashlib.sha256()
        detail = {"attempt": attempt + 1, "url": url, "method": "GET"}
        retry = False
        try:
            with opener(url, timeout) as response:
                detail.update(status=response.status, contentType=response.headers.get("Content-Type"), contentEncoding=response.headers.get("Content-Encoding", "identity"), contentLength=response.headers.get("Content-Length"), cacheStatus=response.headers.get("x-hcdn-cache-status"))
                encoding = detail["contentEncoding"].lower().strip()
                if encoding not in {"", "identity", "gzip"}:
                    raise ValueError("Unsupported content encoding despite identity request: " + encoding)
                stream = gzip.GzipFile(fileobj=response) if encoding == "gzip" else response
                for block in iter(lambda: stream.read(BLOCK), b""):
                    count += len(block)
                    if count > record["bytes"]:
                        raise ValueError("Response exceeds the exact expected decoded asset size")
                    digest.update(block)
                    if time.monotonic() - started > 120:
                        raise TimeoutError("Asset stream exceeded the bounded transfer time")
                detail.update(bytes=count, sha256=digest.hexdigest(), mediaTypePassed=expected_media(record["path"], detail["contentType"]))
                passed = response.status == 200 and count == record["bytes"] and digest.hexdigest() == record["sha256"] and detail["mediaTypePassed"]
                if not passed:
                    detail["error"] = "Status, bytes, SHA256 or executable/PDF media type differs"
                retry = response.status in TRANSIENT or response.status == 200 and not passed
        except urllib.error.HTTPError as exc:
            passed, retry = False, exc.code in TRANSIENT
            detail.update(status=exc.code, error="HTTP " + str(exc.code))
            exc.close()
        except (TimeoutError, socket.timeout, ConnectionError, EOFError, OSError) as exc:
            passed = False
            reason = exc.reason if isinstance(exc, urllib.error.URLError) else exc
            retry = not isinstance(reason, ssl.SSLCertVerificationError)
            detail["error"] = type(exc).__name__ + ": " + str(exc)
        except Exception as exc:
            passed = False
            retry = isinstance(exc, ValueError) and str(exc).startswith("Response exceeds")
            detail["error"] = type(exc).__name__ + ": " + str(exc)
        detail.update(passed=passed, elapsedSeconds=round(time.monotonic() - started, 3))
        attempts.append(detail)
        final = {"name": "public asset " + record["path"], "path": record["path"], "passed": passed, "expectedBytes": record["bytes"], "expectedSha256": record["sha256"], "attempts": attempts, "bytes": count, "sha256": digest.hexdigest(), "status": detail.get("status"), "contentType": detail.get("contentType")}
        if passed or not retry or attempt == 1:
            break
        pause(0.75)
    return final


def self_test():
    from email.message import Message
    body = b"streamed-test-body"
    row = {"path": "fixture.bin", "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
    class Response(io.BytesIO):
        status = 200
        headers = Message()
    count = [0]
    def retry_once(url, timeout):
        count[0] += 1
        if count[0] == 1:
            raise TimeoutError("controlled offline fixture")
        return Response(body)
    assert verify_asset(row, opener=lambda *_: Response(body), pause=lambda _: None)["passed"]
    assert verify_asset(row, opener=retry_once, pause=lambda _: None)["passed"] and count[0] == 2
    wrong = verify_asset(row, opener=lambda *_: Response(b"wrong"), pause=lambda _: None)
    assert not wrong["passed"] and len(wrong["attempts"]) == 2
    large = verify_asset(row, opener=lambda *_: Response(body * 2), pause=lambda _: None)
    assert not large["passed"] and len(large["attempts"]) == 2
    for unsafe in ("../x", "/absolute", "a//b", "a\\b", "https://example.org", "a%2fb", "a?b"):
        try:
            relative(unsafe)
        except ValueError:
            continue
        raise AssertionError("Unsafe path accepted")
    assert not expected_media("x.pdf", "text/html") and expected_media("x.js", "text/javascript")
    return {"passed": True, "scope": "Offline fixtures only: bounded retry, exact stream SHA/size, oversized response, media and path guards. No network requests."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--run-assets", action="store_true", help="Run public GET verification only after upload has completed")
    mode.add_argument("--self-test", action="store_true", help="Offline fake-stream checks; no public requests")
    parser.add_argument("--output", type=Path, default=QA / "public-assets-verification.json")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2)); return 0
    manifest, records = frozen_records()
    if not args.run_assets:
        print(json.dumps({"localInspectionOnly": True, "networkRequests": 0, "manifestSha256": MANIFEST_SHA, "rootReviewSha256": REVIEW_SHA, "filesIncludingManifest": len(records), "bytes": sum(r["bytes"] for r in records)}, indent=2)); return 0
    output = args.output.absolute()
    no_links(output)
    if ".." in output.parts or not output.is_relative_to(QA.absolute()) or output == QA.absolute() or output.exists():
        raise ValueError("Use a fresh JSON report inside the retained research deploy evidence")
    output.parent.mkdir(parents=True, exist_ok=True)
    started, checks = time.monotonic(), []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(verify_asset, item) for item in records]
        for future in as_completed(futures):
            checks.append(future.result())
            if len(checks) % 20 == 0 or len(checks) == len(records):
                print(json.dumps({"checked": len(checks), "total": len(records), "failed": sum(not c["passed"] for c in checks)}), flush=True)
    checks.sort(key=lambda c: c["path"])
    failed = sum(not c["passed"] for c in checks)
    groups = {}
    for name, predicate in {"newPublicOriginals": lambda p: p.startswith("content/research-data/") and not p.endswith("/provenance.json"), "publicProvenance": lambda p: p.startswith("content/research-data/") and p.endswith("/provenance.json"), "pdfManuals": lambda p: p.startswith("docs/") and p.endswith(".pdf"), "javascript": lambda p: p.endswith(".js"), "brand": lambda p: p == "brand.png", "manifestSelf": lambda p: p == MANIFEST}.items():
        selected = [c for c in checks if predicate(c["path"])]
        groups[name] = {"files": len(selected), "passed": bool(selected) and all(c["passed"] for c in selected)}
    report = {"version": "1.3.0", "origin": ORIGIN, "prefix": PREFIX, "createdUtc": datetime.now(timezone.utc).isoformat(), "passed": failed == 0, "passedChecks": len(checks) - failed, "failed": failed, "checkedFiles": len(checks), "concurrency": 4, "maximumAttemptsPerAsset": 2, "manifest": {"path": str(FROZEN / MANIFEST), "sha256": MANIFEST_SHA, "selfExplicitlyVerified": True}, "rootReviewSha256": REVIEW_SHA, "groups": groups, "elapsedSeconds": round(time.monotonic() - started, 2), "checks": checks, "fullFilesSaved": False, "scope": "Read-only public HTTPS GET release-byte verification. No hosting authentication, credentials, production writes or downloaded asset copies. Not a publication-state, hardware, scientific or educational efficacy certification."}
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    print(json.dumps({"passed": report["passed"], "checkedFiles": len(checks), "failed": failed, "output": str(output)}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
