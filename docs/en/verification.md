# Verification and reproducibility

[Home](../../README.md) · [Español](../es/verificacion.md)

Run these from the repository root with Python 3:

```console
python python/run_tests.py
python tools/audit_public_repo.py
```

The first command runs six groups of synthetic/offline tests. TopCmds calls are stubs, including the simulated acquisition path. It does not import a vendor API, start TopSpin, connect to an instrument or acquire data. The second command verifies distribution hashes, local Markdown links, complete 45-slide/45-note presentations with 20 hidden slides and seven embedded videos, blocked example configurations, and textual privacy/secret checks.

[verification.json](../verification.json) records 63 CPython and 16 isolated Jython checks at preparation time, plus static installer and source-only rebuild checks. These are software QA, not instrument qualification or chemical/physical validation. This packaging turn did not visually test the native GUI or run acquisition on TopSpin 3.6.4.

To rebuild the standalone scripts from public source:

```console
python python/build_bundles.py
python python/run_tests.py
```

The generated engine and v2/v3 bundles should remain byte-identical if the included source and documented sequence model have not changed. [build_sources_sha256.json](../../python/build_sources_sha256.json) records inputs and outputs. The original research workspace and proprietary vendor code are not required.

Only a maintainer reviewing an intentional release change should regenerate the repository file manifest with `python tools/audit_public_repo.py --write-manifest`. Do not use regeneration to conceal an unexplained checksum difference. GitHub Actions workflows are absent and are not activated by these commands.

Presentation provenance records original archive/member hashes and modified note parts. All slide, chart, workbook, image and embedded-video bytes were preserved. The static PDF pages and original scientific figure labels are unchanged. Source-only hashes demonstrate distribution integrity, not correctness of a gradient calibration or validation of a new ultrafast sequence.
