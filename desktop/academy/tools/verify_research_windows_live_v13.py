"""Verify the actual public Academy 1.3 Windows archive after root activates it.

Default: local readiness only, no network. --run probes public GET ranges.
--run --full additionally streams the entire ZIP through SHA256, saving no copy.
The independently pinned local archive verification receipt is mandatory to run.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from verify_research_live_v13 import ROOT, QA, BLOCK, no_links, sha, TRANSIENT

ORIGIN = "https://diffatonce.com"
ROUTE = "/downloads/diffatonce-academy-1.3.0-win-x64"
NAME = "DiffAtOnce-Academy-1.3.0-win-x64.zip"
ARCHIVE = ROOT / "desktop/publish" / NAME
VERIFICATION = ARCHIVE.with_suffix(".verification.json")


class DownloadRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        value = urllib.parse.urlsplit(newurl)
        if value.scheme != "https" or value.netloc != "diffatonce.com" or value.path != ROUTE:
            raise ValueError("Download redirect escaped the single public fixed route")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def request(byte_range=None):
    headers = {"Accept-Encoding": "identity", "User-Agent": "DiffAtOnce-Academy-public-archive-QA/1.3"}
    if byte_range:
        headers["Range"] = byte_range
    req = urllib.request.Request(ORIGIN + ROUTE, headers=headers, method="GET")
    try:
        return urllib.request.build_opener(DownloadRedirect()).open(req, timeout=45)
    except urllib.error.HTTPError as exc:
        return exc


def range_probe(spec, size, local, expected_status=206):
    attempts = []
    for attempt in range(2):
        started = time.monotonic()
        try:
            with request(spec) as response:
                status = response.status
                record = {"attempt": attempt + 1, "status": status, "contentRange": response.headers.get("Content-Range"), "contentLength": response.headers.get("Content-Length"), "contentType": response.headers.get("Content-Type"), "acceptRanges": response.headers.get("Accept-Ranges"), "contentDisposition": response.headers.get("Content-Disposition"), "method": "GET"}
                if expected_status == 416:
                    body = response.read(65537)
                    record.update(responseBytes=len(body), passed=status == 416 and response.headers.get("Content-Range") == f"bytes */{size}" and len(body) <= 65536)
                else:
                    first, last = map(int, spec.removeprefix("bytes=").split("-"))
                    length = last - first + 1
                    body = response.read(length + 1)
                    local.seek(first)
                    exact = body == local.read(length)
                    record.update(responseBytes=len(body), bytesEqualLocal=exact, passed=status == 206 and exact and response.headers.get("Content-Range") == f"bytes {first}-{last}/{size}" and response.headers.get("Content-Length") == str(length) and response.headers.get_content_type() == "application/zip" and response.headers.get("Accept-Ranges") == "bytes" and response.headers.get("Content-Disposition") == f'attachment; filename="{NAME}"')
                retry = status in TRANSIENT
        except Exception as exc:
            record = {"attempt": attempt + 1, "passed": False, "error": str(exc), "method": "GET"}
            retry = isinstance(exc, (TimeoutError, ConnectionError))
        record["elapsedSeconds"] = round(time.monotonic() - started, 3)
        attempts.append(record)
        if record["passed"] or not retry or attempt == 1:
            break
        time.sleep(.75)
    return {"name": "public Windows range " + spec, "passed": record["passed"], "range": spec, "attempts": attempts}


def multipart_probe(size, local):
    """Accept only explicit origin416 or an exact bounded CDN two-part206."""
    spec, attempts = "bytes=0-9,20-29", []
    for attempt in range(2):
        started = time.monotonic()
        try:
            with request(spec) as response:
                body = response.read(65537)
                content_type = response.headers.get("Content-Type", "")
                record = {"attempt": attempt + 1, "method": "GET", "status": response.status, "contentType": content_type, "contentRange": response.headers.get("Content-Range"), "responseBytes": len(body), "parts": [], "passed": False}
                if len(body) <= 65536 and response.status == 416:
                    record["passed"] = response.headers.get("Content-Range") == f"bytes */{size}"
                    record["policy"] = "origin-416"
                elif len(body) <= 65536 and response.status == 206 and response.headers.get_content_type() == "multipart/byteranges" and response.headers.get("Content-Range") is None:
                    message = BytesParser(policy=policy.default).parsebytes(("Content-Type: " + content_type + "\r\nMIME-Version: 1.0\r\n\r\n").encode("ascii") + body)
                    expected = {f"bytes 0-9/{size}": (0, 9), f"bytes 20-29/{size}": (20, 29)}
                    for part in message.iter_parts():
                        value = part.get("Content-Range")
                        selected = expected.pop(value, None)
                        payload = part.get_payload(decode=True)
                        exact = False
                        if selected is not None and isinstance(payload, bytes) and part.get("Content-Transfer-Encoding", "binary").lower() in {"binary", "8bit"}:
                            local.seek(selected[0])
                            exact = payload == local.read(selected[1] - selected[0] + 1)
                        record["parts"].append({"contentRange": value, "bytes": len(payload) if isinstance(payload, bytes) else None, "exactLocalBytes": exact})
                    record["passed"] = message.is_multipart() and not message.defects and not expected and len(record["parts"]) == 2 and all(p["exactLocalBytes"] for p in record["parts"])
                    record["policy"] = "validated-cdn-multipart-206"
                retry = response.status in TRANSIENT
        except Exception as exc:
            record = {"attempt": attempt + 1, "method": "GET", "passed": False, "error": str(exc)}
            retry = isinstance(exc, (TimeoutError, ConnectionError))
        record["elapsedSeconds"] = round(time.monotonic() - started, 3)
        attempts.append(record)
        if record["passed"] or not retry or attempt == 1:
            break
        time.sleep(.75)
    return {"name": "public Windows exact multipart range policy", "range": spec, "passed": record["passed"], "attempts": attempts}


def full_stream(size, expected_sha):
    # Deliberately no automatic whole-archive retransmission: preserve any failure
    # as evidence and let root decide after inspecting the partial-byte receipt.
    started, count, digest, last_progress = time.monotonic(), 0, hashlib.sha256(), 0
    result = {"name": "full public Windows archive SHA256", "passed": False, "method": "GET", "maximumAttempts": 1, "savedArchiveCopy": False}
    try:
        with request() as response:
            result.update(status=response.status, contentLength=response.headers.get("Content-Length"), contentType=response.headers.get("Content-Type"))
            if response.status != 200 or response.headers.get("Content-Length") != str(size) or response.headers.get_content_type() != "application/zip" or response.headers.get("Content-Encoding", "identity").lower() not in {"identity", ""}:
                raise ValueError("Full archive response status, size, type or encoding differs")
            for block in iter(lambda: response.read(1024 * 1024), b""):
                count += len(block)
                if count > size:
                    raise ValueError("Full response exceeds the exact sealed archive size")
                digest.update(block)
                if time.monotonic() - started > 1800:
                    raise TimeoutError("Full public ZIP exceeded its bounded transfer duration")
                if count - last_progress >= 128 * 1024 * 1024:
                    last_progress = count
                    print(json.dumps({"stage": "public-Windows-stream-SHA256", "bytes": count, "expectedBytes": size}), flush=True)
            result["passed"] = count == size and digest.hexdigest() == expected_sha
    except Exception as exc:
        result["error"] = type(exc).__name__ + ": " + str(exc)
    result.update(bytes=count, expectedBytes=size, sha256=digest.hexdigest(), expectedSha256=expected_sha, elapsedSeconds=round(time.monotonic() - started, 2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--verification-sha256")
    parser.add_argument("--output", type=Path, default=QA / "public-windows-verification.json")
    args = parser.parse_args()
    if not args.run:
        print(json.dumps({"preparedOnly": True, "networkRequests": 0, "archiveExists": ARCHIVE.is_file(), "verificationExists": VERIFICATION.is_file(), "archive": str(ARCHIVE), "requiredRunArguments": "--run --verification-sha256 <independently pinned receipt SHA>; add --full for complete archive SHA256"}, indent=2))
        return 0
    for path in (ARCHIVE, VERIFICATION):
        no_links(path)
    if not re.fullmatch(r"[a-fA-F0-9]{64}", args.verification_sha256 or "") or sha(VERIFICATION) != args.verification_sha256.lower():
        raise ValueError("A current independently pinned archive readback receipt is required")
    seal = json.loads(VERIFICATION.read_text(encoding="utf-8-sig"))
    size, expected_sha = seal.get("bytes"), seal.get("sha256")
    if seal.get("passed") is not True or Path(seal.get("archive", "")) != ARCHIVE or not isinstance(size, int) or size <= 0 or not re.fullmatch(r"[a-f0-9]{64}", expected_sha or "") or ARCHIVE.stat().st_size != size or sha(ARCHIVE) != expected_sha:
        raise ValueError("Actual local archive does not match its complete passing readback receipt")
    output = args.output.absolute()
    no_links(output)
    if ".." in output.parts or not output.is_relative_to(QA.absolute()) or output == QA.absolute() or output.exists():
        raise ValueError("Choose a fresh JSON report inside retained research deploy evidence")
    output.parent.mkdir(parents=True, exist_ok=True)
    checks = []
    with ARCHIVE.open("rb") as local:
        for first, last in ((0, 4095), (size // 2, size // 2 + 4095), (size - 8192, size - 1), (1048550, 1048635)):
            checks.append(range_probe(f"bytes={first}-{last}", size, local))
        for spec in (f"bytes={size}-", "bytes=200-100", "bytes=-0"):
            checks.append(range_probe(spec, size, local, expected_status=416))
        checks.append(multipart_probe(size, local))
    if args.full and all(c["passed"] for c in checks):
        checks.append(full_stream(size, expected_sha))
    elif args.full:
        checks.append({"name": "full public Windows archive SHA256", "passed": False, "skipped": "Range/header preflight failed; complete stream was not started"})
    report = {"version": "1.3.0", "url": ORIGIN + ROUTE, "createdUtc": datetime.now(timezone.utc).isoformat(), "passed": all(c["passed"] for c in checks), "passedChecks": sum(c["passed"] for c in checks), "failed": sum(not c["passed"] for c in checks), "fullArchiveRequested": args.full, "fullArchiveSHACompared": args.full and checks[-1].get("sha256") == expected_sha and checks[-1]["passed"], "localArchive": {"path": str(ARCHIVE), "bytes": size, "sha256": expected_sha}, "localVerification": {"path": str(VERIFICATION), "sha256": args.verification_sha256.lower()}, "checks": checks, "scope": "Only actual fixed public Windows GET ranges and explicitly requested full stream, compared with the sealed actual local package. No hosting login, credentials, production change, downloaded archive copy, publication-state assertion or scientific validation."}
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    print(json.dumps({"passed": report["passed"], "failed": report["failed"], "fullArchiveSHACompared": report["fullArchiveSHACompared"], "output": str(output)}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
