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
    "2026" { "Visual Studio 18 2026" }
    "2022" { "Visual Studio 17 2022" }
    "2019" { "Visual Studio 16 2019" }
    default { Write-Error "Unsupported Visual Studio product line: $VsVersion"; exit 1 }
}

$CMakeCommand = Get-Command cmake -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
if ($CMakeCommand) {
    $CMake = $CMakeCommand.Source
} else {
    $VsInstallPath = & $VsWhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    if (-not $VsInstallPath) {
        Write-Error "Visual Studio installation path not found."
        exit 1
    }
    $CMake = Join-Path $VsInstallPath.Trim() "Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
    if (-not (Test-Path -LiteralPath $CMake -PathType Leaf)) {
        Write-Error "CMake not found. Install C++ CMake tools for Windows in Visual Studio Installer, or add CMake to PATH."
        exit 1
    }
}

$BuildDir = Join-Path $PSScriptRoot "build"
& $CMake -S $PSScriptRoot -B $BuildDir -G $Generator -A x64
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $CMake --build $BuildDir --config $Configuration
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$UiaExe = Join-Path $BuildDir "$Configuration\win32-shooting-range-uia.exe"
$MsaaExe = Join-Path $BuildDir "$Configuration\win32-shooting-range-msaa.exe"
$CanvasExe = Join-Path $BuildDir "$Configuration\win32-shooting-range-canvas.exe"
$ProbeExe = Join-Path $BuildDir "$Configuration\uia-no-msaa-probe.exe"
Write-Host "Built UIA OK: $UiaExe"
Write-Host "Built MSAA OK: $MsaaExe"
Write-Host "Built Canvas OK: $CanvasExe"
Write-Host "Built UIA probe OK: $ProbeExe"
