param([string]$TopSpinRoot = 'C:\Bruker\TopSpin3.8.0')
$ErrorActionPreference = 'Stop'
$javaExe = Join-Path $TopSpinRoot 'jre\bin\java.exe'
$jythonJar = Join-Path $TopSpinRoot 'classes\lib\jython-2.7.2.jar'
if (-not (Test-Path -LiteralPath $jythonJar)) {
    $jythonJar = Get-ChildItem -LiteralPath (Join-Path $TopSpinRoot 'classes\lib') -Filter 'jython*.jar' | Select-Object -First 1 -ExpandProperty FullName
}
if (-not (Test-Path -LiteralPath $javaExe) -or -not $jythonJar) {
    throw 'TopSpin Java/Jython runtime not found. Pass -TopSpinRoot with the installed TopSpin directory.'
}
$jythonHome = Join-Path $TopSpinRoot 'jython'
$guiScript = Join-Path $PSScriptRoot 'dist\spectrometer_calibration_gui.py'
Push-Location $PSScriptRoot
try { & $javaExe "-Dpython.home=$jythonHome" -jar $jythonJar $guiScript --demo }
finally { Pop-Location }
