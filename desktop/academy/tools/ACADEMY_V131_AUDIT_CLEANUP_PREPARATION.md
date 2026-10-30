# Academy 1.3.1: preparar retención / prepare retention

ES: este procedimiento sólo prepara un plan revisable; no autoriza ni ejecuta
borrados. EN: this procedure prepares a reviewable plan only; it neither
authorizes nor performs deletion. The original 1.3.0 package remains current
until the new 1.3.1 package, ZIP, manuals, model compatibility and web pass their
final independent checks and the release index is promoted separately.

`New-AcademyAuditCleanupPlanV131.ps1 -Describe` prints a non-applicable gate
contract without hashing packages, writing a plan or changing the index.
The planner reuses the reviewed 1.3 planner's integrity checks but accepts only
the two explicit obsolete binary targets:

- `desktop/publish/DiffAtOnce-Academy-1.3.0-win-x64`
- `desktop/publish/DiffAtOnce-Academy-1.3.0-win-x64.zip`

No bin/obj leaves, source archives, originals, calibration, research reports,
models, adapters/checkpoints or other applications are candidates. The new
1.3.1 package and the sealed Resin/Prime packages are protected. Other publish
siblings, the complete Academy tree, research work and artifact evidence are
explicitly excluded. Historical model evidence can remain failed or conditional;
preserving it does not qualify the model.

The previous release is fixed to the original 1.3.0 complete inventory
`qa/research-1.3/retention/new-package-inventory.json`, SHA256
`c88be72fa7f0cfa18b481c4febeeb53acc615514e9c1816bdc56dc8b5a18c3ed`;
1,197 files / 2,300,453,483 uncompressed bytes. Its ZIP has 2,094,584,667 bytes,
SHA256 `fd8884e5a42923569d0c11b73b8745879143425e6cf58ac23cd9a4840bc79b8d`.
Its readback receipt SHA256 is
`2204bfb768f96ef64d42559e18a3f993339148ecd50ad1037960c64ac149d611`.
The separately retained pre-promotion release index must have SHA256
`14e5b90757fb2fd5781a32dc50381461f1471ab00366c59fea2dfa7f7d33bfe7`.

Only after final review, supply a fresh hash-pinned gate following `-Describe`:
exact new package inventory, complete ZIP CRC/SHA receipt, retained old index,
separately promoted current index and concrete passing reports for actual-package
QA, web QA, full manual-page visual review and independent review. All paths
must be explicit local paths within this workspace. No links are traversed;
unexpected old-package additions or modified files block plan generation.
Model/experimental/scientific originals are never inferred to be disposable.

ES: revisa el plan y ejecuta primero la cobertura y el dry-run de las herramientas
canónicas. Sólo tras revisión del propietario puede ejecutarse con su SHA256 y
recibo. EN: review the plan, then run canonical coverage and dry-run checks first.
Only after owner review can the exact plan SHA256 be used for execution and a
durable receipt. This script never invokes those tools, terminates processes,
changes an index, rewrites proofs or deletes files:

```powershell
# Run after final evidence and separately promoted index exist; placeholders fail.
pwsh -File desktop/academy/tools/New-AcademyAuditCleanupPlanV131.ps1 -Describe
pwsh -File desktop/academy/tools/New-AcademyAuditCleanupPlanV131.ps1 `
  -GatePath '<absolute hash-bound final gate.json>' `
  -GateSha256 '<exact SHA256>' -PlanPath '<fresh desktop/artifacts plan.json>'
# Separately: desktop/tools/project-hygiene/Test-PlanCoverage.ps1
# Separately: desktop/tools/project-hygiene/Invoke-MultiProjectCleanup.ps1 dry-run
```

The source distribution includes this recipe and planner for transparency. It
does not include the private release QA tree or multi-gigabyte binary packages;
an extracted public source ZIP cannot fabricate or satisfy the cleanup gate.
