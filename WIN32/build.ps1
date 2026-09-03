param(
    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Release"
)

$ErrorActionPreference = "Stop"

$VsWhere = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
if (-not (Test-Path -LiteralPath $VsWhere)) {
    Write-Error "Visual Studio Installer not found. Install Visual Studio with Desktop development with C++."
    exit 1
}

$VsVersion = & $VsWhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property catalog_productLineVersion
if (-not $VsVersion) {
    Write-Error "MSVC C++ build tools not found. Install the Desktop development with C++ workload."
    exit 1
}

$Generator = switch ($VsVersion.Trim()) {
    "18" { "Visual Studio 18 2026" }
    "17" { "Visual Studio 17 2022" }
    "16" { "Visual Studio 16 2019" }
    default { Write-Error "Unsupported Visual Studio product line: $VsVersion"; exit 1 }
}

$BuildDir = Join-Path $PSScriptRoot "build"
& cmake -S $PSScriptRoot -B $BuildDir -G $Generator -A x64
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& cmake --build $BuildDir --config $Configuration
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$UiaExe = Join-Path $BuildDir "$Configuration\win32-shooting-range-uia.exe"
$MsaaExe = Join-Path $BuildDir "$Configuration\win32-shooting-range-msaa.exe"
$CanvasExe = Join-Path $BuildDir "$Configuration\win32-shooting-range-canvas.exe"
$ProbeExe = Join-Path $BuildDir "$Configuration\uia-no-msaa-probe.exe"
Write-Host "Built UIA OK: $UiaExe"
Write-Host "Built MSAA OK: $MsaaExe"
Write-Host "Built Canvas OK: $CanvasExe"
Write-Host "Built UIA probe OK: $ProbeExe"
