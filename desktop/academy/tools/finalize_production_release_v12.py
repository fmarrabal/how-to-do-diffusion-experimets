"""Finalize local release records only after actual public verification passes."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[3]
QA = ROOT / "desktop/academy/qa/doctoral-1.2"
RELEASE = ROOT / "desktop/publish/academy-web-1.2.0-20261005-r3"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows-report", type=Path, required=True)
    args = parser.parse_args()
    sources = {
        "public_assets": QA / "production-assets-bare-after-purge-r3/production-read-only-qa.json",
        "public_runtime": QA / "production-runtime-completion-r3.json",
        "public_product": QA / "production-final-activation-r3-product/production-ui-qa.json",
        "public_windows": args.windows_report.resolve(),
        "installed_php": QA / "server-php-readback-20261005/stored-php-verification.json",
        "originals_rechecked": QA / "pre-activation-live-recheck-20261005/recheck.json",
    }
    reports = {key: json.loads(path.read_text(encoding="utf-8")) for key, path in sources.items()}
    for key, report in reports.items():
        assert report.get("passed") and not report.get("failed", 0), key
    assert reports["public_assets"]["checkedAssetFiles"] == 188
    assert reports["public_runtime"]["checksPassed"] == 89
    assert reports["public_product"]["passed"] == 41
    assert len(reports["installed_php"]["checks"]) == 7
    assert len(reports["originals_rechecked"]["files"]) == 4
    windows = reports["public_windows"]
    assert windows["fullWindowsRequested"] is True
    full = next(c for c in windows["checks"] if c["name"] == "full public Windows SHA256")
    assert full["passed"] and full["detail"]["bytes"] == 2061185273
    assert full["detail"]["sha256"] == "49b17756359f870acf768aa216834bf13a34f953d4c19f535e084e9797aaea99"
    timestamp = datetime.now(timezone.utc).isoformat()
    evidence = [{"name": key, "path": str(path.relative_to(ROOT)),
                 "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                for key, path in sources.items()]
    record = {
        "version": "1.2.0", "published": True, "verifiedAtUtc": timestamp,
        "destination": "https://diffatonce.com", "scope": "Academy only",
        "productEs": "https://diffatonce.com/academy",
        "productEn": "https://diffatonce.com/en/academy",
        "windowsDownload": "https://diffatonce.com/downloads/diffatonce-academy-1.2.0-win-x64",
        "windowsBytes": full["detail"]["bytes"], "windowsSha256": full["detail"]["sha256"],
        "verification": evidence,
        "backup": "website/backups/academy-live-before-v1.2-20261005",
        "serverBackup": "diffatonce-app/backup-academy-before-1.2-20261005",
        "imageDelivery": "Academy PNG/JPEG only: no-transform; domain-specific cache purge; all 188 ordinary-URL files exact",
        "beatrix": "Original 24-lesson locally fine-tuned model preserved in Windows. New doctoral/article hints are reviewed documentary content, without new LLM fine-tuning.",
        "scientificScope": "Educational simulations and attributed public experimental data with nominal/conditional b and D. Software verification does not establish instrument calibration, chemical identity or educational efficacy.",
        "windowsPackaging": "Portable ZIP; extract before running. WebView2 required. Not an installer.",
        "historicalReports": "Earlier upload progress and resolved failed checks are retained; this record establishes the final deployment status.",
    }
    final = RELEASE / "PRODUCTION_RELEASE_VERIFIED.json"
    assert not final.exists(), "Preserve an existing final record rather than overwrite"
    final.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    for name in ("upload-manifest.json", "deployment-plan-r3.json"):
        path = RELEASE / name
        backup = path.with_name(path.stem + ".before-production-final.json")
        assert not backup.exists(), backup
        shutil.copy2(path, backup)
        data = json.loads(path.read_text(encoding="utf-8"))
        data.update(published=True, verifiedAtUtc=timestamp, productionEvidence=str(final.relative_to(ROOT)))
        if "notEvidenceOf" in data:
            data["notEvidenceOf"] = "Instrument calibration, chemical identity or educational efficacy"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    text = f"""# DiffAtOnce Academy 1.2 · Publicación verificada / Verified deployment

Fecha UTC / UTC date: {timestamp}

ES: Academy 1.2 está publicada en https://diffatonce.com/academy y en inglés en
https://diffatonce.com/en/academy. Incluye nueve actividades doctorales, 93 pasos
guiados, derivaciones, simulaciones, un caso Bruker público y manuales ES/EN.
La navegación, la portada y la familia de productos incluyen Academy.

Se verificaron 188 archivos públicos byte a byte, 89 comprobaciones del runtime,
41 del producto/navegación ES/EN y los siete PHP instalados. La descarga pública
completa de Windows contiene {full['detail']['bytes']:,} bytes y coincide por SHA-256:
{full['detail']['sha256']}.

Windows es un ZIP portátil con Beatrix local: extraer antes de ejecutar.
Beatrix conserva el ajuste fino de las 24 lecciones originales. Los contenidos
doctorales nuevos ofrecen guías documentales revisadas, sin nuevo ajuste fino.
Los modelos UF/SPEN son educativos; el dato Bruker conserva b y D nominales/
condicionales. Estas comprobaciones acreditan el software y su publicación.

EN: Academy 1.2 is deployed at the two product URLs above. The nine doctoral
activities connect physical mechanisms, experimental decisions and evidence.
Both manuals and the complete portable Windows ZIP are available. All 188
ordinary-URL public files, 89 runtime checks, 41 product/navigation checks,
seven installed PHP files and the complete Windows download passed verification.

Windows retains local Beatrix fine-tuned for the original 24 lessons. New
doctoral/article hints use reviewed documentary content without new fine-tuning.
UF/SPEN are educational models; public Bruker b/D remain nominal/conditional.
Software and deployment checks do not establish instrument or teaching validation.

Original shared PHP files and earlier release packages are preserved. Earlier
progress notes and resolved failed checks remain historical evidence. The final
machine-readable record is PRODUCTION_RELEASE_VERIFIED.json in this directory.
"""
    (RELEASE / "RELEASE_VERIFIED_ES_EN.md").write_text(text, encoding="utf-8")
    print(json.dumps({"published": True, "record": str(final), "evidenceFiles": len(evidence)}))


if __name__ == "__main__":
    main()
