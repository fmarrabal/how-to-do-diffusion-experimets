"""Read-only targeted resolution of a multipart-range expectation mismatch.

One bounded GET on the fixed public release; no site change or full ZIP retry.
"""
from email import policy
from email.parser import BytesParser
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
path = Path(__file__).with_name("verify_production_v12_r3.py")
spec = importlib.util.spec_from_file_location("verifier", path)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)
output = ROOT / "desktop/academy/qa/doctoral-1.2/production-final-activation-r3-multipart"
if output.exists():
    raise ValueError("Use a new targeted QA directory")
output.mkdir()
report = {"origin": verifier.ORIGIN, "path": verifier.ROUTE,
          "scope": "One public GET with a multipart Range; maximum 65536 response bytes. No account, site changes or full ZIP repetition.",
          "requestRange": "bytes=0-9,20-29", "expectedFullBytes": verifier.SIZE,
          "parts": [], "passed": False}
try:
    with verifier.request(verifier.ROUTE, byte_range=report["requestRange"]) as response:
        body = response.read(65537)
        report.update(status=response.status, headers=dict(response.headers.items()), responseBytes=len(body), responseSha256=hashlib.sha256(body).hexdigest())
        if len(body) > 65536:
            raise ValueError("Response exceeded the bounded probe")
        content_type = response.headers.get("Content-Type", "")
        if response.status == 416:
            report["passed"] = response.headers.get("Content-Range") == f"bytes */{verifier.SIZE}"
            report["interpretation"] = "Origin rejects the multi-range request as documented."
        elif response.status == 206 and content_type.lower().startswith("multipart/byteranges;"):
            message = BytesParser(policy=policy.default).parsebytes(("Content-Type: " + content_type + "\r\nMIME-Version: 1.0\r\n\r\n").encode("ascii") + body)
            expected = {f"bytes 0-9/{verifier.SIZE}": (0, 9), f"bytes 20-29/{verifier.SIZE}": (20, 29)}
            with verifier.ZIP.open("rb") as local:
                for part in message.iter_parts():
                    content_range = part.get("Content-Range")
                    payload = part.get_payload(decode=True)
                    target = expected.pop(content_range, None)
                    same = False
                    if target:
                        local.seek(target[0])
                        same = payload == local.read(target[1] - target[0] + 1)
                    report["parts"].append({"contentRange": content_range, "contentType": part.get_content_type(), "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(), "exactLocalBytes": same})
            report["passed"] = not expected and len(report["parts"]) == 2 and all(p["exactLocalBytes"] for p in report["parts"]) and response.headers.get("Content-Range") is None
            report["interpretation"] = "Public delivery supports a correct multipart/byteranges representation; each part has its own Content-Range and matches the frozen ZIP. A top-level Content-Range is not expected."
        else:
            report["interpretation"] = "Unexpected public multi-range representation."
except Exception as error:
    report["error"] = str(error)
(output / "multipart-range-resolution.json").write_text(json.dumps(report, indent=2), "utf-8")
print(json.dumps(report, indent=2))
raise SystemExit(0 if report["passed"] else 1)
