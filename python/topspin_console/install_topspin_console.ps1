[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string] $TopSpinHome
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$sourceFile = Join-Path $PSScriptRoot 'dist\dosy_workshop.py'
if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) {
    throw "No existe el archivo autocontenido: $sourceFile"
}

$rootItem = Get-Item -LiteralPath $TopSpinHome
if (-not $rootItem.PSIsContainer) {
    throw 'TopSpinHome debe ser el directorio de instalacion de TopSpin.'
}
$installRoot = [IO.Path]::GetFullPath($rootItem.FullName)
if (($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'Indique el directorio real de TopSpin en lugar de un enlace de directorio.'
}
$pythonDirectory = Join-Path $installRoot 'exp\stan\nmr\py'
if (-not (Test-Path -LiteralPath $pythonDirectory -PathType Container)) {
    throw "No se reconoce la carpeta Python de TopSpin: $pythonDirectory"
}
$checkedDirectory = $installRoot
foreach ($segment in @('exp', 'stan', 'nmr', 'py')) {
    $checkedDirectory = Join-Path $checkedDirectory $segment
    if (((Get-Item -LiteralPath $checkedDirectory).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "La ruta Python contiene un enlace de directorio: $checkedDirectory. Use la copia manual."
    }
}

$userDirectory = [IO.Path]::GetFullPath((Join-Path $pythonDirectory 'user'))
$rootPrefix = $installRoot.TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if (-not $userDirectory.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'El destino no pertenece a la instalacion indicada.'
}
if (Test-Path -LiteralPath $userDirectory) {
    $userItem = Get-Item -LiteralPath $userDirectory
    if (-not $userItem.PSIsContainer) {
        throw "El destino de scripts no es una carpeta: $userDirectory"
    }
    if (($userItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw 'La carpeta py/user es un enlace. Copie el script manualmente en la ubicacion que utilice TopSpin.'
    }
} else {
    [IO.Directory]::CreateDirectory($userDirectory) | Out-Null
}

$destinationFile = Join-Path $userDirectory 'dosy_workshop.py'
$sourceHash = (Get-FileHash -LiteralPath $sourceFile -Algorithm SHA256).Hash
$backupFile = $null

if (Test-Path -LiteralPath $destinationFile) {
    $destinationItem = Get-Item -LiteralPath $destinationFile
    if ($destinationItem.PSIsContainer -or (($destinationItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) {
        throw 'El destino existente no es un archivo regular.'
    }
    $existingHash = (Get-FileHash -LiteralPath $destinationFile -Algorithm SHA256).Hash
    if ($existingHash -eq $sourceHash) {
        [pscustomobject]@{
            Status = 'AlreadyCurrent'
            Destination = $destinationFile
            SHA256 = $sourceHash
            Backup = $null
            TopSpinStarted = $false
        }
        return
    }
    $stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
    $suffix = [Guid]::NewGuid().ToString('N').Substring(0, 8)
    $backupFile = $destinationFile + '.backup-' + $stamp + '-' + $suffix
    [IO.File]::Copy($destinationFile, $backupFile, $false)
    if ((Get-FileHash -LiteralPath $backupFile -Algorithm SHA256).Hash -ne $existingHash) {
        throw "No se ha verificado la copia anterior: $backupFile"
    }
}

$temporaryFile = Join-Path $userDirectory ('.dosy_workshop-' + [Guid]::NewGuid().ToString('N') + '.tmp')
try {
    [IO.File]::Copy($sourceFile, $temporaryFile, $false)
    if ((Get-FileHash -LiteralPath $temporaryFile -Algorithm SHA256).Hash -ne $sourceHash) {
        throw 'La copia temporal no coincide con el archivo de origen.'
    }
    if (Test-Path -LiteralPath $destinationFile) {
        if ($null -eq $backupFile) {
            throw 'El destino aparecio durante la instalacion. Repita el comando para conservar su copia.'
        }
        if ((Get-FileHash -LiteralPath $destinationFile -Algorithm SHA256).Hash -ne $existingHash) {
            throw 'El destino cambio durante la instalacion; se ha conservado sin sustituirlo.'
        }
        [IO.File]::Replace($temporaryFile, $destinationFile, [NullString]::Value)
    } else {
        [IO.File]::Move($temporaryFile, $destinationFile)
    }
} finally {
    if (Test-Path -LiteralPath $temporaryFile -PathType Leaf) {
        Remove-Item -LiteralPath $temporaryFile
    }
}

$installedHash = (Get-FileHash -LiteralPath $destinationFile -Algorithm SHA256).Hash
if ($installedHash -ne $sourceHash) {
    throw "El hash instalado no coincide. Revise el destino y su copia: $destinationFile"
}
[pscustomobject]@{
    Status = 'Installed'
    Destination = $destinationFile
    SHA256 = $installedHash
    Backup = $backupFile
    TopSpinStarted = $false
}
