#Requires -Version 7.0
[CmdletBinding()]
param(
    [switch]$Describe,
    [string]$GatePath,
    [string]$GateSha256,
    [string]$PlanPath
)
# Planning only: no deletion, process termination, index change or executor call.
# Invoke the canonical coverage checker and dry-run separately after owner review.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$cmp = [StringComparison]::OrdinalIgnoreCase
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..')).TrimEnd([char[]]'\/')
# Fixed 1.3.0-to-1.3.1 audit-patch retention only; never discovers targets.
$contract = [ordered]@{
    Schema = 'academy.release-cleanup-gate.v1'; Version = '1.3.1'; Passed = $true
    NewPackage = @{ Path = '<absolute new Academy-1.3.1-win-x64 directory>'; Product = 'Academy-1.3.1'; InventoryPath = '<normalized complete relative-member inventory>'; InventorySha256 = '<SHA256>' }
    NewZip = @{ Path = '<absolute verified 1.3.1 ZIP>'; Bytes = '<integer>'; Sha256 = '<SHA256>'; VerificationPath = '<package_portable verification.json>'; VerificationSha256 = '<SHA256>' }
    OriginalIndex = @{ Path = '<retained pre-promotion RELEASES_CURRENT.md backup>'; Sha256 = '14E5B90757FB2FD5781A32DC50381461F1471AB00366C59FEA2DFA7F7D33BFE7' }
    CurrentIndex = @{ Path = '<workspace>/desktop/RELEASES_CURRENT.md'; Sha256 = '<promoted index SHA256>' }
    Evidence = @('actual-package-qa','web-qa','manual-review','independent-review') | ForEach-Object { @{Role=$_;Path='<concrete passing report>';Sha256='<SHA256>'} }
}
if ($Describe) {
    [ordered]@{ ReadOnly = $true; ApplicablePlanCreated = $false; Planner = $PSCommandPath; RequiredGate = $contract; BaseTargets = 2; GeneratedOutputsIncluded = $false; CanonicalExecutor = 'desktop/tools/project-hygiene/Invoke-MultiProjectCleanup.ps1'; CoverageChecker = 'desktop/tools/project-hygiene/Test-PlanCoverage.ps1'; Notes = @('No plan can be written without all real hash-bound evidence and a promoted index.','This script never runs cleanup or changes the release index.','Evidence requires concrete all-passing checks or complete rendered-page review; Passed alone is insufficient.','ZIP readback proof is reused after checking its pinned receipt, archive SHA256, size and package membership.','No bin/obj, source archive, model, research report or scientific-original path is selected.') } | ConvertTo-Json -Depth 10
    return
}
if (-not $GatePath -or -not $GateSha256 -or -not $PlanPath) { throw 'Planning requires -GatePath, -GateSha256 and -PlanPath. Use -Describe for the non-applicable preparation contract.' }
function Field($o,[string]$name,$default=$null) { if ($null-ne$o-and$null-ne$o.PSObject.Properties[$name]) { return $o.$name }; return $default }
function Full([string]$path) {
    if ([string]::IsNullOrWhiteSpace($path) -or -not [IO.Path]::IsPathFullyQualified($path) -or $path -match '[*?\x00-\x1f]' -or $path.StartsWith('\\') -or $path.StartsWith('//') -or @($path-split'[\\/]' | Where-Object {$_-in@('.','..')}).Count) { throw 'Use an exact local absolute path without dot segments or wildcard.' }
    if ($path.Substring([IO.Path]::GetPathRoot($path).Length).Contains(':')) { throw 'Alternate data stream rejected.' }
    $f=[IO.Path]::GetFullPath($path).TrimEnd([char[]]'\/'); if($f.Length-le2){throw 'Drive root rejected.'}; return $f
}
function Within([string]$path,[string]$parent) { $path.Equals($parent,$cmp)-or$path.StartsWith($parent+[IO.Path]::DirectorySeparatorChar,$cmp) }
function Overlap([string]$a,[string]$b) { (Within $a $b)-or(Within $b $a) }
function NoLinks([string]$path) {
    $cursor=$path
    while($cursor) { if(Test-Path -LiteralPath $cursor) { if((Get-Item -LiteralPath $cursor -Force).Attributes-band[IO.FileAttributes]::ReparsePoint){throw "Link/reparse ancestor rejected: $cursor"} };$next=[IO.Path]::GetDirectoryName($cursor);if($next-eq$cursor){break};$cursor=$next }
}
function LocalPath([string]$path) { $f=Full $path;if(-not(Within $f $repo)){throw 'All inputs and outputs must remain inside the exact source workspace.'};NoLinks $f;return $f }
function Hash([string]$path) { NoLinks $path;$before=Get-Item -LiteralPath $path -Force;if($before-isnot[IO.FileInfo]){throw "File required: $path"};$length=$before.Length;$mtime=$before.LastWriteTimeUtc.Ticks;$value=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash;$after=Get-Item -LiteralPath $path -Force;if($after.Length-ne$length-or$after.LastWriteTimeUtc.Ticks-ne$mtime){throw "File changed during hashing: $path"};return $value }
function Pin([string]$path,[string]$sha) { $f=LocalPath $path;if($sha-notmatch'^[a-fA-F0-9]{64}$'-or(Hash $f)-ne$sha){throw "Pinned evidence hash mismatch: $f"};return $f }
function ReadJson([string]$path,[string]$sha) { $f=Pin $path $sha;return Get-Content -LiteralPath $f -Raw | ConvertFrom-Json -Depth 100 }
function Integer($n,[string]$label) { if($null-eq$n-or[string]$n-notmatch'^\d+$'){throw "Nonnegative integer required: $label"};return [long]$n }
function Snapshot([string]$root) {
    NoLinks $root;$first=Get-Item -LiteralPath $root -Force
    if($first-isnot[IO.DirectoryInfo]){throw "Directory required: $root"}
    $stack=[Collections.Generic.Stack[IO.DirectoryInfo]]::new();$stack.Push($first)
    $result=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::OrdinalIgnoreCase)
    while($stack.Count) {
        $dir=$stack.Pop();$dir.Refresh();if(-not$dir.Exists-or($dir.Attributes-band[IO.FileAttributes]::ReparsePoint)){throw "Changed/linked directory: $($dir.FullName)"}
        foreach($item in $dir.EnumerateFileSystemInfos()) {
            $item.Refresh();if(-not$item.Exists-or-not(Within $item.FullName $root)-or($item.Attributes-band[IO.FileAttributes]::ReparsePoint)){throw "Unsafe/changed child: $($item.FullName)"}
            if($item-is[IO.DirectoryInfo]){$stack.Push($item)}else{
                $relative=[IO.Path]::GetRelativePath($root,$item.FullName).Replace('\','/')
                if($result.ContainsKey($relative)){throw "Duplicate member: $relative"}
                $result.Add($relative,[pscustomobject]@{Path=$relative;FullPath=$item.FullName;Bytes=[long]$item.Length;LastWriteTicks=$item.LastWriteTimeUtc.Ticks})
            }
        }
    }
    return ,$result
}
function Stable($before,$after,[string]$root) {
    if($before.Count-ne$after.Count){throw "Membership changed: $root"}
    foreach($key in $before.Keys) { if(-not$after.ContainsKey($key)-or$before[$key].Bytes-ne$after[$key].Bytes-or$before[$key].LastWriteTicks-ne$after[$key].LastWriteTicks){throw "Member changed: $root/$key"} }
}
function Relative([string]$root,[string]$member) {
    if([string]::IsNullOrWhiteSpace($member)-or[IO.Path]::IsPathRooted($member)-or$member-match'[:*?\x00-\x1f]'-or@($member-split'[\\/]'|Where-Object {$_-in@('.','..','')}).Count){throw "Relative inventory member required: $member"}
    $path=Full(Join-Path $root $member);if(-not(Within $path $root)-or$path-eq$root){throw 'Inventory escaped package.'};return $path
}
function VerifyInventory([string]$root,$inventory,[string]$label) {
    $before=Snapshot $root;$seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase);$files=[Collections.Generic.List[object]]::new();[long]$bytes=0
    foreach($item in @($inventory)) {
        $name=[string](Field $item 'File' (Field $item 'Path'));$file=Relative $root $name;$member=[IO.Path]::GetRelativePath($root,$file).Replace('\','/')
        if(-not$seen.Add($member)-or-not$before.ContainsKey($member)){throw "Missing/duplicate sealed member in $label : $member"}
        $size=Integer (Field $item 'Bytes') "$label/$member bytes";$sha=[string](Field $item 'Sha256')
        if($before[$member].Bytes-ne$size-or$sha-notmatch'^[a-fA-F0-9]{64}$'-or(Hash $file)-ne$sha){throw "Sealed member modified in $label : $member"}
        $bytes+=$size;$files.Add([pscustomobject]@{Path=$member;Bytes=$size;Sha256=$sha})
    }
    if($seen.Count-ne$before.Count-or$seen.Count-eq0){throw "Entire package inventory does not match $label; preserve unexpected additions."}
    Stable $before (Snapshot $root) $root
    return [pscustomobject]@{Path=$root;Kind='directory';Bytes=$bytes;FileCount=[long]$files.Count;Files=$files.ToArray();Initial=$before}
}
function InventoryFor($document,[string]$root,[string]$product) {
    $records=@(Field $document 'Packages' $document);$matches=@($records|Where-Object { ([string](Field $_ 'Product' (Field $_ 'Name' '')))-eq$product -and (Full([string](Field $_ 'Path')))-eq$root })
    if($matches.Count-ne1){throw "Exactly one normalized package inventory required: $product"}
    return @(Field $matches[0] 'Inventory' (Field $matches[0] 'Files' @()))
}
function Passing($report,[string]$role) {
    $passed=Field $report 'passed' (Field $report 'Passed' $null)
    if($passed-is[bool]-and-not$passed){throw "Report explicitly failed: $role"}
    $checks=@(Field $report 'checks' @())
    if($checks.Count-gt0) {
        if(@($checks|Where-Object { (Field $_ 'passed' $null)-isnot[bool]-or(Field $_ 'passed' $null)-ne$true }).Count){throw "Incomplete/failed concrete checks: $role"};return
    }
    if((Field $report 'allPagesVisuallyReviewed' $false)-eq$true-and@(Field $report 'outputs' @()).Count-gt0){return}
    $count=Field $report 'passed' $null;$failed=Field $report 'failed' $null
    if($count-isnot[bool]-and$null-ne$count-and$null-ne$failed-and(Integer $count 'passed')-gt0-and(Integer $failed 'failed')-eq0){return}
    if((Field $report 'structurePassed' $false)-eq$true-and(Field $report 'allPagesVisuallyReviewed' $false)-eq$true){return}
    throw "Concrete passing checks or complete visual review required; a Passed flag is insufficient: $role"
}
function ReleaseRows([string]$text,[string]$label) {
    # Compare literal row content; LF and CRLF are equivalent terminators.
    $pattern='(?m)^(\| '+[regex]::Escape($label)+' \|[^\r\n]+)\r?$'
    return @([regex]::Matches($text,$pattern)|ForEach-Object {$_.Groups[1].Value})
}
function AssertIdle([object[]]$targets,[string[]]$buildRoots) {
    $observed=[Collections.Generic.List[object]]::new()
    foreach($process in Get-CimInstance -ClassName Win32_Process -ErrorAction Stop) {
        $name=[string]$process.Name;$image=[string]$process.ExecutablePath;$command=[string]$process.CommandLine
        $academyProcess=$name-match'^(DiffAtOnce\.Academy|ResearchNativeProbe)(\.exe)?$'
        $buildProcess=$name-match'^(dotnet|MSBuild|VBCSCompiler|csc|python|python3|pwsh|powershell)(\.exe)?$'
        if($academyProcess-and$command-match'--(?:self|tutor)-test'){throw "Academy self-test is active; finish it normally before cleanup (PID $($process.ProcessId))."}
        if($academyProcess-and[string]::IsNullOrWhiteSpace($image)){throw "Ambiguous Academy process image; defer cleanup (PID $($process.ProcessId))."}
        foreach($target in $targets) {
            if($image-and(Within $image $target.Path)){throw "Target is running; close normally (PID $($process.ProcessId), $name)."}
            if($command-and$command.IndexOf($target.Path,$cmp)-ge0){throw "Active command references a target; defer cleanup (PID $($process.ProcessId), $name)."}
        }
        if($buildProcess) {
            if([string]::IsNullOrWhiteSpace($command)-and$name-match'^(dotnet|MSBuild|VBCSCompiler|csc)'){throw "Cannot establish build process scope; defer cleanup (PID $($process.ProcessId), $name)."}
            foreach($buildRoot in $buildRoots) {
                $projectToken=[IO.Path]::GetFileName($buildRoot)
                if($command-and(($command.Replace('/','\').IndexOf($buildRoot,$cmp)-ge0)-or($projectToken-ne'work-v3'-and$command.IndexOf($projectToken,$cmp)-ge0)-or($projectToken-eq'work-v3'-and$command.IndexOf('ResearchNativeProbe',$cmp)-ge0))){throw "Academy build/test command is active; defer cleanup (PID $($process.ProcessId), $name)."}
            }
        }
        if($academyProcess-or$buildProcess){$observed.Add(@{Pid=[long]$process.ProcessId;Name=$name;ImageKnown=![string]::IsNullOrWhiteSpace($image);TargetReference=$false})}
    }
    # Full command lines are inspected only in memory and never saved.
    return $observed.ToArray()
}
# Pin the exact preparation recipe and all historical evidence before creating output.
$recipe=Join-Path $PSScriptRoot 'ACADEMY_V131_AUDIT_CLEANUP_PREPARATION.md'
$recipeSha=Hash $recipe
$gateFile=Pin $GatePath $GateSha256;$gate=ReadJson $gateFile $GateSha256
if((Field $gate 'Schema')-ne'academy.release-cleanup-gate.v1'-or(Field $gate 'Version')-ne'1.3.1'-or(Field $gate 'Passed')-isnot[bool]-or(Field $gate 'Passed')-ne$true){throw 'Only the exact final Academy 1.3.1 audit cleanup gate is admissible.'}
$planFile=LocalPath $PlanPath;$proofRoot=Join-Path $repo 'desktop/artifacts'
if(-not(Within $planFile $proofRoot)-or$planFile-eq$proofRoot-or[IO.Path]::GetExtension($planFile)-ne'.json'-or(Test-Path -LiteralPath $planFile)){throw 'Use a fresh exact .json plan file inside desktop/artifacts.'}
$publish=Join-Path $repo 'desktop/publish';$academy=Join-Path $repo 'desktop/academy'
$oldRoot=Join-Path $publish 'DiffAtOnce-Academy-1.3.0-win-x64';$oldZip=$oldRoot+'.zip'
$newRoot=LocalPath([string]$gate.NewPackage.Path);$newZip=LocalPath([string]$gate.NewZip.Path)
if($newRoot-ne(Join-Path $publish 'DiffAtOnce-Academy-1.3.1-win-x64')-or$newZip-ne($newRoot+'.zip')-or$gate.NewPackage.Product-ne'Academy-1.3.1'){throw 'Only the exact verified Academy 1.3.1 package and ZIP can replace 1.3.0.'}
$oldInventoryPath=Join-Path $repo 'desktop/academy/qa/research-1.3/retention/new-package-inventory.json'
$oldInventorySha='C88BE72FA7F0CFA18B481C4FEBEEB53ACC615514E9C1816BDC56DC8B5A18C3ED'
$oldInventory=ReadJson $oldInventoryPath $oldInventorySha
$oldZipReceiptPath=Join-Path $publish 'DiffAtOnce-Academy-1.3.0-win-x64.verification.json'
$oldZipReceipt=ReadJson $oldZipReceiptPath '2204BFB768F96EF64D42559E18A3F993339148ECD50AD1037960C64AC149D611'
if($oldZipReceipt.passed-ne$true-or$oldZipReceipt.files-ne1197-or$oldZipReceipt.uncompressed_bytes-ne2300453483-or$oldZipReceipt.bytes-ne2094584667-or$oldZipReceipt.sha256-ne'fd8884e5a42923569d0c11b73b8745879143425e6cf58ac23cd9a4840bc79b8d'){throw 'Historical ZIP identity differs.'}
$oldIndexSha='14E5B90757FB2FD5781A32DC50381461F1471AB00366C59FEA2DFA7F7D33BFE7'
if($gate.OriginalIndex.Sha256-ne$oldIndexSha){throw 'Original index identity differs from the pinned pre-promotion snapshot.'}
$oldIndexFile=Pin ([string]$gate.OriginalIndex.Path) $oldIndexSha;$indexFile=Pin ([string]$gate.CurrentIndex.Path) ([string]$gate.CurrentIndex.Sha256)
if($indexFile-ne(Join-Path $repo 'desktop/RELEASES_CURRENT.md')-or$oldIndexFile-eq$indexFile-or$gate.CurrentIndex.Sha256-eq$oldIndexSha){throw 'A retained old index backup and a separately promoted current index are required.'}
$oldText=Get-Content -LiteralPath $oldIndexFile -Raw;$newText=Get-Content -LiteralPath $indexFile -Raw
foreach($label in @('ResinAtOnce','DiffAtOnce Prime')) {
    $oldRows=@(ReleaseRows $oldText $label);$newRows=@(ReleaseRows $newText $label)
    if($oldRows.Count-ne1-or$newRows.Count-ne1-or$oldRows[0]-ne$newRows[0]){throw "Unrelated latest-release row changed: $label"}
}
$newAcademyRow=@(ReleaseRows $newText 'DiffAtOnce Academy')
if($newAcademyRow.Count-ne1-or-not$newAcademyRow[0].Contains('[1.3.1]')-or-not$newAcademyRow[0].Replace('\','/').Contains($newRoot.Replace('\','/')+'/DiffAtOnce.Academy.exe')){throw 'Current index does not select the exact protected Academy 1.3.1 executable.'}
$evidence=[Collections.Generic.List[object]]::new()
foreach($role in @('actual-package-qa','web-qa','manual-review','independent-review')) {
    $matches=@($gate.Evidence|Where-Object Role -eq $role);if($matches.Count-ne1){throw "Exactly one final evidence reference required: $role"}
    $ref=$matches[0];$report=ReadJson ([string]$ref.Path) ([string]$ref.Sha256);Passing $report $role
    $evidence.Add(@{Role=$role;Path=(LocalPath $ref.Path);Sha256=$ref.Sha256})
}
$allowed=@($publish)
$candidates=[Collections.Generic.List[object]]::new();$candidates.Add(@{Path=$oldRoot;Classification='obsolete-package'});$candidates.Add(@{Path=$oldZip;Classification='obsolete-package-archive'})
$processBefore=@(AssertIdle $candidates.ToArray() @())
# Complete old inventory: extras are never silently discarded.
$oldState=VerifyInventory $oldRoot (InventoryFor $oldInventory $oldRoot 'Academy-1.3.0') 'historical Academy 1.3.0'
if($oldState.FileCount-ne1197-or$oldState.Bytes-ne2300453483){throw 'The complete original 1.3.0 inventory count/size changed.'}
$oldZipItem=Get-Item -LiteralPath (Pin $oldZip $oldZipReceipt.sha256) -Force;if($oldZipItem.Length-ne2094584667){throw 'Old ZIP length differs.'}
$newInventoryPath=Pin $gate.NewPackage.InventoryPath $gate.NewPackage.InventorySha256;$newInventory=ReadJson $newInventoryPath $gate.NewPackage.InventorySha256
$newState=VerifyInventory $newRoot (InventoryFor $newInventory $newRoot 'Academy-1.3.1') 'new Academy 1.3.1'
$newZipReceiptPath=Pin $gate.NewZip.VerificationPath $gate.NewZip.VerificationSha256;$zipProof=ReadJson $newZipReceiptPath $gate.NewZip.VerificationSha256
if($zipProof.passed-isnot[bool]-or$zipProof.passed-ne$true-or$zipProof.scope-ne'Complete archive membership, byte count, CRC and SHA-256 readback; software package integrity only.'-or(Full $zipProof.archive)-ne$newZip-or$zipProof.files-ne$newState.FileCount-or$zipProof.uncompressed_bytes-ne$newState.Bytes-or$zipProof.sha256-ne$gate.NewZip.Sha256-or$zipProof.bytes-ne(Integer $gate.NewZip.Bytes 'new ZIP bytes')){throw 'ZIP verification does not bind the complete verified new package.'}
$newZipItem=Get-Item -LiteralPath (Pin $newZip $gate.NewZip.Sha256) -Force;if($newZipItem.Length-ne$zipProof.bytes){throw 'New ZIP length differs.'}
# Reuse the hash-pinned full-CRC/SHA receipt. Read only the central directory and
# tiny PACKAGE_SHA256.json member to bind that ZIP to this exact package, avoiding
# another multi-GB decompression/readback. Counts alone would not establish this.
$packageRows=@($newState.Files|Where-Object Path -eq 'PACKAGE_SHA256.json')
if($packageRows.Count-ne1){throw 'Complete normalized inventory must include PACKAGE_SHA256.json itself.'}
$packageManifestPath=Join-Path $newRoot 'PACKAGE_SHA256.json'
$packageManifest=@(ReadJson $packageManifestPath $packageRows[0].Sha256)
$sealedByName=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::OrdinalIgnoreCase)
foreach($row in $newState.Files){$sealedByName.Add($row.Path,$row)}
$manifestNames=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach($row in $packageManifest){
    $member=[IO.Path]::GetRelativePath($newRoot,(Relative $newRoot $row.path)).Replace('\','/')
    if(-not$manifestNames.Add($member)-or-not$sealedByName.ContainsKey($member)-or$row.sha256-ne$sealedByName[$member].Sha256-or(Integer $row.bytes 'package manifest size')-ne$sealedByName[$member].Bytes){throw 'Package manifest differs from the full normalized inventory.'}
}
if($manifestNames.Count-ne$newState.FileCount-1-or$manifestNames.Contains('PACKAGE_SHA256.json')){throw 'Package manifest membership is incomplete.'}
$archive=[IO.Compression.ZipFile]::OpenRead($newZip)
try{
    $archiveNames=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase);$prefix=[IO.Path]::GetFileName($newRoot)+'/'
    foreach($entry in $archive.Entries){
        if(-not$entry.FullName.StartsWith($prefix,[StringComparison]::Ordinal)-or$entry.FullName.EndsWith('/')-or$entry.FullName.Contains('\')){throw 'ZIP has an unexpected member path.'}
        $member=$entry.FullName.Substring($prefix.Length);$null=Relative $newRoot $member
        if(-not$archiveNames.Add($member)-or-not$sealedByName.ContainsKey($member)-or$entry.Length-ne$sealedByName[$member].Bytes){throw 'ZIP central-directory membership/size differs from the package.'}
    }
    if($archiveNames.Count-ne$newState.FileCount){throw 'ZIP member count differs from the complete package.'}
    $entry=$archive.GetEntry($prefix+'PACKAGE_SHA256.json');if($null-eq$entry){throw 'ZIP lacks the package manifest.'}
    $stream=$entry.Open();$hasher=[Security.Cryptography.SHA256]::Create()
    try{$archiveManifestSha=[Convert]::ToHexString($hasher.ComputeHash($stream))}finally{$stream.Dispose();$hasher.Dispose()}
    if($archiveManifestSha-ne$packageRows[0].Sha256){throw 'ZIP package manifest differs from the verified retained package.'}
}finally{$archive.Dispose()}
$newZipAfter=Get-Item -LiteralPath $newZip -Force
if($newZipAfter.Length-ne$newZipItem.Length-or$newZipAfter.LastWriteTimeUtc.Ticks-ne$newZipItem.LastWriteTimeUtc.Ticks){throw 'New ZIP changed during central-directory verification.'}
$retainedPath=Join-Path $repo 'desktop/artifacts/neural-integration-audit-20261028-r1/cleanup-r1/protected-packages.json';$retainedSha='05C0AA3DEE71922FB4C3FEDE162D93E69CAA6F7ED4CBE695FABCCF651149DCB5'
$retained=ReadJson $retainedPath $retainedSha;$deliveryPath=Join-Path $repo 'desktop/artifacts/neural-integration-audit-20261028-r1/DELIVERY_VERIFIED.json';$deliverySha='AE1A795E8192652C31679A95526FBB0E8E0986E93385B86E0FFCFB89DF38238C';$null=Pin $deliveryPath $deliverySha
if($retained.SealSha256-ne$deliverySha-or(Full $retained.SealPath)-ne$deliveryPath){throw 'Resin/Prime retained seal differs.'}
$protected=[Collections.Generic.List[object]]::new();$protected.Add(@{Path=$newRoot;Product='Academy-1.3.1';InventoryPath=$newInventoryPath;InventorySha256=$gate.NewPackage.InventorySha256})
$retainedStates=[Collections.Generic.List[object]]::new()
foreach($product in @('ResinAtOnce-0.51.83','DiffAtOncePrime-0.15.82')) {
    $root=Join-Path $publish $product;$state=VerifyInventory $root (InventoryFor $retained $root $product) $product;$retainedStates.Add($state)
    $protected.Add(@{Path=$root;Product=$product;InventoryPath=$retainedPath;InventorySha256=$retainedSha})
}
$entries=[Collections.Generic.List[object]]::new()
$entries.Add(@{Path=$oldRoot;Kind='directory';Classification='obsolete-package';Bytes=$oldState.Bytes;FileCount=$oldState.FileCount;ExpectedFiles=@($oldState.Files|ForEach-Object{@{Path=$_.Path;Sha256=$_.Sha256}})})
$entries.Add(@{Path=$oldZip;Kind='file';Classification='obsolete-package-archive';Bytes=[long]$oldZipItem.Length;FileCount=1;ExpectedSha256=$oldZipReceipt.sha256})
$exclusions=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
function Exclude([string]$path) { $f=LocalPath $path;foreach($target in $candidates){if(Overlap $f $target.Path){throw "Excluded/target overlap: $f"}};$null=$exclusions.Add($f) }
# Enumerate only exact siblings, never discover additional deletable content.
foreach($item in (Get-Item -LiteralPath $publish).EnumerateFileSystemInfos()){if($item.FullName-ne$oldRoot-and$item.FullName-ne$oldZip){Exclude $item.FullName}}
# Academy source, models, reports and all generated leaves remain outside scope.
Exclude $academy
Exclude (Join-Path $repo '.codex-work')
Exclude (Join-Path $repo 'desktop/artifacts')
foreach($path in @($gateFile,$indexFile,$oldIndexFile,$recipe,$oldInventoryPath,$oldZipReceiptPath,$newInventoryPath,$newZipReceiptPath,$retainedPath,$deliveryPath,$PSCommandPath)+@($evidence|ForEach-Object Path)){Exclude $path}
foreach($protectedPackage in $protected){Exclude $protectedPackage.Path}
foreach($target in $candidates){if(Overlap $planFile $target.Path){throw 'Plan path overlaps a deletion target.'}}
# Repeat only fresh metadata snapshots and small evidence hashes; no repeated ZIP expansion.
Stable $oldState.Initial (Snapshot $oldRoot) $oldRoot;Stable $newState.Initial (Snapshot $newRoot) $newRoot
foreach($state in $retainedStates){Stable $state.Initial (Snapshot $state.Path) $state.Path}
$null=Pin $indexFile $gate.CurrentIndex.Sha256;$null=Pin $gateFile $GateSha256;$null=Pin $recipe $recipeSha
foreach($ref in $evidence){$null=Pin $ref.Path $ref.Sha256}
$processAfter=@(AssertIdle $candidates.ToArray() @())
$plan=[ordered]@{
    Schema='projects.verified-cleanup-plan.v2';CreatedUtc=[DateTimeOffset]::UtcNow.ToString('O');Purpose='Academy 1.3.1 audit retention; only the exact verified old 1.3.0 package directory and ZIP.'
    AllowedRoots=$allowed;ProtectedPaths=$protected.ToArray();ExcludedPaths=@($exclusions|Sort-Object);Entries=$entries.ToArray()
    Gate=@{Path=$gateFile;Sha256=$GateSha256};OriginalIndex=@{Path=$oldIndexFile;Sha256=$oldIndexSha};CurrentIndex=@{Path=$indexFile;Sha256=$gate.CurrentIndex.Sha256}
    NewPackage=@{Path=$newRoot;InventoryPath=$newInventoryPath;InventorySha256=$gate.NewPackage.InventorySha256;FileCount=$newState.FileCount;Bytes=$newState.Bytes}
    NewZip=@{Path=$newZip;Bytes=$newZipItem.Length;Sha256=$gate.NewZip.Sha256;VerificationPath=$newZipReceiptPath;VerificationSha256=$gate.NewZip.VerificationSha256}
    RetainedEvidence=$evidence.ToArray();SourceRetention='The entire Academy source/model/report tree, research work, manuals, source archives, receipts and every publish sibling other than the exact old folder/ZIP are excluded. No bin/obj leaves are selected.'
    Planner=@{Path=$PSCommandPath;Sha256=(Hash $PSCommandPath);RecipePath=$recipe;RecipeSha256=$recipeSha;NoDeletionPerformed=$true;IndexNotModified=$true;CanonicalExecutor='desktop/tools/project-hygiene/Invoke-MultiProjectCleanup.ps1'}
    Processes=@{Before=$processBefore;After=$processAfter;FullCommandLinesSaved=$false};OwnerReviewRequiredBeforeExecutor=$true
}
$expectedCount=2;if($entries.Count-ne$expectedCount){throw 'Exact target count changed.'}
$parent=[IO.Path]::GetDirectoryName($planFile);NoLinks $parent;$null=[IO.Directory]::CreateDirectory($parent);NoLinks $parent
$data=[Text.UTF8Encoding]::new($false).GetBytes(($plan|ConvertTo-Json -Depth 100)+"`n")
$stream=[IO.FileStream]::new($planFile,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None,4096,[IO.FileOptions]::WriteThrough)
try{$stream.Write($data,0,$data.Length);$stream.Flush($true)}finally{$stream.Dispose()}
[ordered]@{Plan=$planFile;PlanSha256=(Hash $planFile);Targets=$entries.Count;Bytes=($entries|Measure-Object Bytes -Sum).Sum;ApplicablePlanCreated=$true;DeletionPerformed=$false;IndexModified=$false;Next='Owner review, then canonical Test-PlanCoverage.ps1 and Invoke-MultiProjectCleanup.ps1 dry-run with exact PlanSha256.'}|ConvertTo-Json -Depth 5
