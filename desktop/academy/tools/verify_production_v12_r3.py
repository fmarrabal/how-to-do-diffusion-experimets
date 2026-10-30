"""Read-only public release verification, run only after deployment is active.

GET/HEAD only, fixed DiffAtOnce origin, normal TLS, no account/credentials.
Default verifies the 187 assets and small installer ranges; it never fetches the
full Windows ZIP unless --full-windows is explicitly supplied after upload.
Only a fresh local QA report is written. Production content is never changed.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from email import policy
from email.parser import BytesParser
import gzip
import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
ASSETS = ROOT / "website/release/public_html/assets/academy/v1.2.0"
ZIP = ROOT / "desktop/publish/DiffAtOnce-Academy-1.2.0-win-x64.zip"
ORIGIN = "https://diffatonce.com"
PREFIX = "/assets/academy/v1.2.0/"
ROUTE = "/downloads/diffatonce-academy-1.2.0-win-x64"
SIZE = 2061185273
ZIP_SHA = "49b17756359f870acf768aa216834bf13a34f953d4c19f535e084e9797aaea99"


class SameOriginRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlsplit(newurl)
        if parsed.scheme != "https" or parsed.netloc != "diffatonce.com":
            raise ValueError("Redirect outside the explicitly scoped origin")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def request(path, method="GET", byte_range=None):
    if not path.startswith("/") or path.startswith("//"):
        raise ValueError("Only absolute paths on the scoped origin")
    headers = {"Accept-Encoding": "identity", "User-Agent": "DiffAtOnce-Academy-release-verification/1.2"}
    if byte_range:
        headers["Range"] = byte_range
    req = urllib.request.Request(ORIGIN + path, headers=headers, method=method)
    opener = urllib.request.build_opener(SameOriginRedirect())
    try:
        return opener.open(req, timeout=45)
    except urllib.error.HTTPError as error:
        return error


def asset(record, cache_key=None):
    path = record["path"]
    try:
        public_path = PREFIX + urllib.parse.quote(path, safe="/")
        if cache_key:
            public_path += "?" + urllib.parse.urlencode({"academy_integrity": cache_key})
        with request(public_path) as response:
            stream = gzip.GzipFile(fileobj=response) if response.headers.get("Content-Encoding") == "gzip" else response
            digest = hashlib.sha256()
            count = 0
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                count += len(block)
                if count > record["bytes"]:
                    raise ValueError("Response exceeds the exact expected asset size")
                digest.update(block)
            actual = digest.hexdigest()
            return {"name": "asset " + path, "passed": response.status == 200 and count == record["bytes"] and actual == record["sha256"], "path": path, "requestedPath": public_path, "status": response.status, "bytes": count, "expectedBytes": record["bytes"], "sha256": actual, "expectedSha256": record["sha256"], "contentType": response.headers.get("Content-Type"), "cacheControl": response.headers.get("Cache-Control"), "cacheStatus": response.headers.get("x-hcdn-cache-status")}
    except Exception as error:
        return {"name": "asset " + path, "passed": False, "path": path, "error": str(error)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--full-windows", action="store_true", help="Explicitly request a full public ZIP stream after confirming upload")
    mode.add_argument("--assets-only", action="store_true", help="Verify public resources only before PHP activation; never request installer routes")
    parser.add_argument("--windows-only", action="store_true", help="Skip the already verified static resources and check only the public Windows download")
    parser.add_argument("--images-only", action="store_true", help="With --assets-only, check the 88 PNG/JPEG files after the scoped header experiment")
    parser.add_argument("--cache-key", help="Fresh public version query for readback; does not purge or change global CDN settings")
    args = parser.parse_args()
    if args.images_only and not args.assets_only:
        parser.error("--images-only requires --assets-only; no installer requests allowed")
    if args.windows_only and (args.assets_only or args.images_only or args.cache_key):
        parser.error("--windows-only cannot be combined with asset or cache options")
    output = args.output.resolve()
    qa_root = ROOT / "desktop/academy/qa/doctoral-1.2"
    if not output.is_relative_to(qa_root) or output == qa_root or output.exists():
        raise ValueError("Use a new QA directory inside desktop/academy/qa/doctoral-1.2")
    manifest_path = ASSETS / "WEB_RELEASE_SHA256.json"
    manifest = json.loads(manifest_path.read_text("utf-8-sig"))
    records = list(manifest["files"])
    if len(records) != 187:
        raise ValueError("Expected frozen 187-file browser release")
    records.append({"path": "WEB_RELEASE_SHA256.json", "bytes": manifest_path.stat().st_size, "sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest()})
    if args.images_only:
        records = [r for r in records if r["path"].lower().endswith((".png", ".jpg", ".jpeg"))]
        if len(records) != 88:
            raise ValueError("Expected exactly 88 frozen PNG/JPEG images")
    if args.windows_only:
        records = []
    output.mkdir(parents=True)
    checks = []
    observations = {}
    started = time.time()

    def check(name, passed, detail=None):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            for index, result in enumerate(pool.map(lambda record: asset(record, args.cache_key), records), 1):
                checks.append(result)
                if index % 20 == 0 or index == len(records):
                    print(json.dumps({"stage": "asset-hashes", "checked": index, "total": len(records), "failed": sum(not x["passed"] for x in checks)}), flush=True)
        if args.images_only:
            check("all PNG/JPEG responses carry no-transform", all("no-transform" in (r.get("cacheControl") or "") for r in checks), {"images": len(records)})
        elif not args.windows_only:
            for language in ("ES", "EN"):
                result = next(r for r in checks if r.get("path") == "docs/DOCTORAL_MANUAL_" + language + ".pdf")
                check("PDF media type " + language, str(result.get("contentType", "")).split(";")[0] == "application/pdf", result.get("contentType"))
            data = [r for r in checks if r.get("path", "").startswith("content/doctoral-data/monash-d2o-10/")]
            check("public original raw subset plus provenance exact", len(data) == 11 and all(r["passed"] for r in data), {"files": len(data), "absoluteCalibrationValidated": False})
        if args.windows_only:
            observations["staticAssetsSkipped"] = "Static assets and authored runtime already verified in separate immutable reports."

        if args.assets_only:
            observations["installerRoutesSkipped"] = "Assets-only verification before PHP activation; no installer requests made."
        else:
            with request(ROUTE, "HEAD") as response:
                headers = dict(response.headers.items())
                check("Windows fixed route HEAD200 and exact bytes", response.status == 200 and response.headers.get("Content-Length") == str(SIZE), {"status": response.status, "headers": headers})
                check("Windows attachment and range headers", response.headers.get("Content-Disposition") == 'attachment; filename="DiffAtOnce-Academy-1.2.0-win-x64.zip"' and response.headers.get("Accept-Ranges") == "bytes" and response.headers.get_content_type() == "application/zip", headers)
                if response.status != 200 or response.headers.get("Content-Length") != str(SIZE):
                    raise ValueError("Windows route is not the complete expected release; ranges and full transfer skipped")
            if ZIP.stat().st_size != SIZE:
                raise ValueError("Local frozen Windows ZIP size differs")
            with ZIP.open("rb") as local:
                for first, last in ((0, 4095), (SIZE // 2, SIZE // 2 + 4095), (SIZE - 8192, SIZE - 1), (1048550, 1048635)):
                    byte_range = f"bytes={first}-{last}"
                    with request(ROUTE, byte_range=byte_range) as response:
                        body = response.read(last - first + 2)
                        local.seek(first)
                        expected = local.read(last - first + 1)
                        check("Windows range " + byte_range, response.status == 206 and body == expected and response.headers.get("Content-Range") == f"bytes {first}-{last}/{SIZE}", {"status": response.status, "bytes": len(body), "contentRange": response.headers.get("Content-Range")})
                for byte_range in (f"bytes={SIZE}-", "bytes=200-100", "bytes=-0"):
                    with request(ROUTE, byte_range=byte_range) as response:
                        check("Windows rejected range " + byte_range, response.status == 416 and response.headers.get("Content-Range") == f"bytes */{SIZE}", {"status": response.status, "contentRange": response.headers.get("Content-Range")})
                with request(ROUTE, byte_range="bytes=0-9,20-29") as response:
                    detail = {"status": response.status, "contentType": response.headers.get("Content-Type"), "contentRange": response.headers.get("Content-Range"), "parts": []}
                    correct = response.status == 416 and detail["contentRange"] == f"bytes */{SIZE}"
                    if response.status == 206 and (detail["contentType"] or "").lower().startswith("multipart/byteranges;"):
                        body = response.read(65537)
                        if len(body) > 65536:
                            raise ValueError("Multipart response exceeded the bounded range probe")
                        message = BytesParser(policy=policy.default).parsebytes(("Content-Type: " + detail["contentType"] + "\r\nMIME-Version: 1.0\r\n\r\n").encode("ascii") + body)
                        expected_parts = {f"bytes 0-9/{SIZE}": (0, 9), f"bytes 20-29/{SIZE}": (20, 29)}
                        for part in message.iter_parts():
                            target = expected_parts.pop(part.get("Content-Range"), None)
                            payload = part.get_payload(decode=True)
                            exact = False
                            if target:
                                local.seek(target[0])
                                exact = payload == local.read(target[1] - target[0] + 1)
                            detail["parts"].append({"contentRange": part.get("Content-Range"), "bytes": len(payload), "exactLocalBytes": exact})
                        correct = detail["contentRange"] is None and not expected_parts and len(detail["parts"]) == 2 and all(p["exactLocalBytes"] for p in detail["parts"])
                        detail["responseBytes"] = len(body)
                    check("Windows multipart range policy and exact bytes", correct, detail)

            with request("/downloads/diffatonce-academy-1.1.0-win-x64", "HEAD") as response:
                observations["previousRelease"] = {"status": response.status, "bytes": response.headers.get("Content-Length"), "available": response.status == 200, "scope": "Observation only; previous production availability was not established by local tests."}

            if args.full_windows:
                with request(ROUTE) as response:
                    if response.status != 200 or response.headers.get("Content-Length") != str(SIZE):
                        raise ValueError("Full Windows response does not have the expected status and size")
                    digest = hashlib.sha256()
                    count = 0
                    last_report = 0
                    for block in iter(lambda: response.read(1024 * 1024), b""):
                        count += len(block)
                        if count > SIZE:
                            raise ValueError("Windows stream exceeds expected bytes")
                        digest.update(block)
                        if count - last_report >= 128 * 1024 * 1024:
                            last_report = count
                            print(json.dumps({"stage": "Windows-full-SHA", "bytes": count, "expectedBytes": SIZE}), flush=True)
                    check("full public Windows SHA256", response.status == 200 and count == SIZE and digest.hexdigest() == ZIP_SHA, {"bytes": count, "sha256": digest.hexdigest(), "expectedSha256": ZIP_SHA})
    except Exception as error:
        check("production verifier completion", False, str(error))
    report = {"version": "1.2.0", "origin": ORIGIN, "scope": "Read-only public GET/HEAD; no external account, no authentication and no site changes. Software release verification only.", "fullWindowsRequested": args.full_windows, "windowsOnly": args.windows_only, "assetsOnly": args.assets_only, "imagesOnly": args.images_only, "cacheKey": args.cache_key, "checkedAssetFiles": len(records), "fullBodyBuffered": False, "expectedFrozenRuntimeFiles": 187, "elapsedSeconds": time.time() - started, "passed": sum(r["passed"] for r in checks), "failed": sum(not r["passed"] for r in checks), "observations": observations, "checks": checks}
    (output / "production-read-only-qa.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("passed", "failed", "fullWindowsRequested", "elapsedSeconds")}), flush=True)
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
