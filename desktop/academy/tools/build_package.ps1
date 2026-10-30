param([string]$Version = '1.3.1', [switch]$AllowDocumentaryMode)
$ErrorActionPreference = 'Stop'
$academyRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$workspaceRoot = [IO.Path]::GetFullPath((Join-Path $academyRoot '../..'))
$releaseRoot = [IO.Path]::GetFullPath((Join-Path $workspaceRoot ('desktop/publish/DiffAtOnce-Academy-' + $Version + '-win-x64')))
if ($Version -notmatch '^\d+\.\d+\.\d+$' -or -not $releaseRoot.StartsWith($workspaceRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid release target' }
$modelDirectory = if ($Version -eq '1.3.1') { Join-Path $academyRoot 'ai/release-v1.3.1' } elseif ($Version -eq '1.3.0') { Join-Path $academyRoot 'ai/release-v1.3' } else { Join-Path $academyRoot 'ai/release-v1.1' }
$manifestPath = Join-Path $modelDirectory 'manifest.json'
if ((Get-PSDrive -Name ([IO.Path]::GetPathRoot($releaseRoot).TrimEnd(':','\'))).Free -lt 8GB) { throw 'At least 8 GB free space is required for this package and verification.' }
if (-not $AllowDocumentaryMode) {
    if (-not (Test-Path -LiteralPath $manifestPath)) { throw 'A verified local tutor release is required; model is not present.' }
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    if (-not $manifest.fineTuned -or -not $manifest.qualityPassed) { throw 'The tutor has not passed its educational release gate.' }
    if ($manifest.NativeEvaluationPending -ne $false) { throw 'The native CPU tutor evaluation is still pending.' }
    if ($manifest.SupplementalNativeEvaluationPending -ne $false -or -not $manifest.SupplementalNativeEvaluationPassed) { throw 'The new mathematical tutor evaluation is still pending.' }
    if ($manifest.SupplementalSemanticEvaluationPending -ne $false -or -not $manifest.SupplementalSemanticEvaluationReportSha256) { throw 'The actual new tutor responses have not received scientific review.' }
    if ($manifest.SupplementalLLMApproved -ne $false -or $manifest.SupplementalAnswerMode -ne 'reviewed-documentary-guide') { throw 'Mathematical generation is not approved; the reviewed guide is required.' }
    $courseSha = (Get-FileHash -LiteralPath (Join-Path $academyRoot 'content/course.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($manifest.courseSha256 -ne $courseSha) { throw 'Course/model version mismatch.' }
    $derivationsSha = (Get-FileHash -LiteralPath (Join-Path $academyRoot 'content/derivations.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($manifest.SupplementalContentSha256 -ne $derivationsSha -or $manifest.SupplementalIncludedInTraining -ne $false) { throw 'Reviewed mathematics provenance mismatch.' }
    $bundle = Get-Content -LiteralPath (Join-Path $academyRoot 'web/bundle-manifest.json') -Raw | ConvertFrom-Json
    if ($bundle.derivationsSha256 -ne $derivationsSha -or $bundle.releaseStatus -match 'pending') { throw 'Web mathematics bundle is not frozen.' }
    if ($Version -eq '1.2.0') {
        $doctoral = Get-Content -LiteralPath (Join-Path $academyRoot 'content/doctoral-manifest.json') -Raw | ConvertFrom-Json
        $doctoralSha = (Get-FileHash -LiteralPath (Join-Path $academyRoot 'content/doctoral-manifest.json') -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($doctoral.releaseStatus -ne 'reviewed-teaching-software' -or $doctoral.includedInLLMTraining -ne $false -or $bundle.doctoralContentSha256 -ne $doctoralSha) { throw 'Doctoral teaching release is not reviewed or the bundle identity differs.' }
        foreach ($record in $doctoral.files) {
            $source = [IO.Path]::GetFullPath((Join-Path $academyRoot $record.path))
            if (-not $source.StartsWith($academyRoot + '\', [StringComparison]::OrdinalIgnoreCase) -or (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $record.sha256) { throw 'Doctoral source identity mismatch.' }
        }
    }
    if ($Version -in @('1.3.0','1.3.1')) {
        if (-not $manifest.ResearchQualityPassed -or -not $manifest.NativeResearchEvaluationPassed -or -not $manifest.NativeEvaluationPassed) { throw 'Research tutor GPU and native CPU gates must pass.' }
        $knowledgeSha = (Get-FileHash -LiteralPath (Join-Path $academyRoot 'content/research-tutor-knowledge.json') -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($manifest.ResearchKnowledgeSha256 -ne $knowledgeSha) { throw 'Research knowledge/model version mismatch.' }
        if ($bundle.version -ne $Version -or $bundle.releaseStatus -ne 'reviewed-teaching-software' -or $bundle.researchReleaseStatus -ne 'reviewed-teaching-software') { throw 'Research web bundle must be frozen after root review.' }
        if ($Version -eq '1.3.1') {
            $doctoralPath = Join-Path $academyRoot 'content/doctoral-manifest.json'
            $doctoral = Get-Content -LiteralPath $doctoralPath -Raw | ConvertFrom-Json
            $doctoralSha = (Get-FileHash -LiteralPath $doctoralPath -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($doctoral.version -ne $Version -or $doctoral.schema -ne 'academy-doctoral-content-identity/2' -or $doctoral.releaseStatus -ne 'identity-only' -or $doctoral.includedInLLMTraining -ne $false -or $doctoral.newTrainingPerformed -ne $false -or $bundle.doctoralContentSha256 -ne $doctoralSha -or $bundle.doctoralReleaseStatus -ne 'reviewed-teaching-software' -or -not $bundle.rootReview.passed -or $bundle.rootReview.sha256 -notmatch '^[a-f0-9]{64}$') { throw 'Current doctoral identity requires the separately hash-bound root software freeze.' }
            foreach ($record in $doctoral.files) {
                $source = [IO.Path]::GetFullPath((Join-Path $academyRoot $record.path))
                if (-not $source.StartsWith($academyRoot + '\', [StringComparison]::OrdinalIgnoreCase) -or (Get-Item -LiteralPath $source).Length -ne $record.bytes -or (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $record.sha256) { throw 'Current doctoral source identity mismatch.' }
            }
        }
        $modelPath = Join-Path $modelDirectory $manifest.File
        if ((Get-FileHash -LiteralPath $modelPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest.Sha256) { throw 'Qualified model hash mismatch.' }
    }
}
if (Test-Path -LiteralPath $releaseRoot) { throw 'Release target already exists; preserve it and choose a new version.' }
$project = Join-Path $academyRoot 'src/DiffAtOnce.Academy.App/DiffAtOnce.Academy.App.csproj'
& dotnet publish $project -c Release -r win-x64 --self-contained true --configfile (Join-Path $academyRoot 'NuGet.Config') --ignore-failed-sources -p:PublishTrimmed=false "-p:AcademyModelDirectory=$modelDirectory" -o $releaseRoot
if ($LASTEXITCODE -ne 0) { throw 'Publish failed.' }
Copy-Item -LiteralPath (Join-Path $academyRoot 'START_HERE_ES_EN.txt') -Destination (Join-Path $releaseRoot 'START_HERE_ES_EN.txt')
Get-ChildItem -LiteralPath $releaseRoot -Recurse -File | ForEach-Object {
    [PSCustomObject]@{path=[IO.Path]::GetRelativePath($releaseRoot,$_.FullName).Replace('\','/');bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $releaseRoot 'PACKAGE_SHA256.json') -Encoding utf8
Write-Output $releaseRoot
