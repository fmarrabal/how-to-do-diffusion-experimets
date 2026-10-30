"""Aggregate immutable release and targeted resolution reports; no network.

The full 2 GB transfer is never repeated. Historical 10/11 remains preserved.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
QA = ROOT / "desktop/academy/qa/doctoral-1.2"
historical_path = QA / "production-final-activation-r3-windows/production-read-only-qa.json"
probe_path = QA / "production-final-activation-r3-multipart/multipart-range-resolution.json"
pins = {historical_path: "efa569189f6110a1d5fc619e8a75b0bbeb87f21cfea7efc954f9b2f9cbad053c",
        probe_path: "dc70e8d19c10b2ade09cd87f105cb67a8f1153d74dfc0797c880f1cccb183c40"}
for path, expected in pins.items():
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError("Immutable input report hash mismatch: " + str(path))
historical = json.loads(historical_path.read_text("utf-8"))
probe = json.loads(probe_path.read_text("utf-8"))
failed = [c for c in historical["checks"] if not c["passed"]]
if len(failed) != 1 or failed[0]["name"] != "Windows rejected range bytes=0-9,20-29" or not probe["passed"]:
    raise ValueError("Unexpected historical failure or unsuccessful targeted resolution")
full = next(c for c in historical["checks"] if c["name"] == "full public Windows SHA256")
if not full["passed"] or full["detail"]["bytes"] != 2061185273 or full["detail"]["sha256"] != "49b17756359f870acf768aa216834bf13a34f953d4c19f535e084e9797aaea99":
    raise ValueError("Full transfer verification is incomplete")
checks = [c for c in historical["checks"] if c["passed"]]
checks.append({"name": "Windows public multipart byte-range representation and exact bytes", "passed": True,
               "detail": {"status": probe["status"], "contentType": probe["headers"]["Content-Type"],
                          "responseBytes": probe["responseBytes"], "parts": probe["parts"],
                          "interpretation": probe["interpretation"]}})
report = {"version": "1.2.0", "origin": historical["origin"],
          "scope": "Final aggregate of one complete public Windows SHA transfer and one bounded 242-byte multipart resolution. No repeated full transfer, site modification, account access or static/runtime recheck.",
          "fullWindowsRequested": True, "windowsOnly": True, "fullWindowsTransferredOnce": True,
          "fullBodyBuffered": False, "checkedAssetFiles": 0,
          "fullTransferVerifierElapsedSeconds": historical["elapsedSeconds"],
          "passed": len(checks), "failed": 0, "checks": checks,
          "observations": historical["observations"],
          "historicalFailurePreserved": {"path": str(historical_path.relative_to(ROOT)).replace("\\", "/"), "sha256": pins[historical_path], "passed": historical["passed"], "failed": historical["failed"], "resolvedCheck": failed[0]["name"]},
          "targetedResolution": {"path": str(probe_path.relative_to(ROOT)).replace("\\", "/"), "sha256": pins[probe_path], "passed": True},
          "protocolBasis": [{"url": "https://www.rfc-editor.org/rfc/rfc9110.html#section-15.3.7.2", "finding": "Multiple-part 206 responses use multipart/byteranges and Content-Range in each part, with no top-level Content-Range."}, {"url": "https://www.rfc-editor.org/rfc/rfc9110.html#section-14.6", "finding": "The boundary separates parts with their own Content-Type and Content-Range."}],
          "resolution": "The original test incorrectly required 416 for a valid multi-range request. Public delivery returned a standards-compliant 206 multipart body; both 10-byte ranges exactly matched the frozen ZIP. No production change was necessary."}
output = QA / "production-final-activation-r3-windows-resolved"
if output.exists():
    raise ValueError("Use a new final QA directory")
output.mkdir()
path = output / "production-read-only-qa.json"
path.write_text(json.dumps(report, indent=2), "utf-8")
print(json.dumps({"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "passed": report["passed"], "failed": report["failed"], "fullWindowsRequested": report["fullWindowsRequested"], "fullPublicWindowsSHA256": full["detail"]}, indent=2))
