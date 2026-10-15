param(
    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Release",
    [string]$BuildDirectory = (Join-Path $PSScriptRoot "build"),
    [switch]$BuildTests
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
    "2026" { "Visual Studio 18 2026" }
    "17" { "Visual Studio 17 2022" }
    "2022" { "Visual Studio 17 2022" }
    "16" { "Visual Studio 16 2019" }
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

$BuildDir = [System.IO.Path]::GetFullPath($BuildDirectory)
$TestsValue = if ($BuildTests) { "ON" } else { "OFF" }
& $CMake -S $PSScriptRoot -B $BuildDir -G $Generator -A x64 "-DWIN32_SHOOTING_RANGE_BUILD_TESTS=$TestsValue"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $CMake --build $BuildDir --config $Configuration
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$UiaExe = Join-Path $BuildDir "$Configuration\win32-shooting-range-uia.exe"
$UiaNoPaneExe = Join-Path $BuildDir "$Configuration\win32-shooting-range-uia-no-pane.exe"
$UiaRandomExe = Join-Path $BuildDir "$Configuration\win32-shooting-range-uia-random.exe"
$MsaaExe = Join-Path $BuildDir "$Configuration\win32-shooting-range-msaa.exe"
$CanvasExe = Join-Path $BuildDir "$Configuration\win32-shooting-range-canvas.exe"
$PressureExe = Join-Path $BuildDir "$Configuration\win32-uia-pressure.exe"
$Pressure500Exe = Join-Path $BuildDir "$Configuration\win32-uia-pressure-500.exe"
$Pressure1000Exe = Join-Path $BuildDir "$Configuration\win32-uia-pressure-1000.exe"
$Pressure2000Exe = Join-Path $BuildDir "$Configuration\win32-uia-pressure-2000.exe"
$ProbeExe = Join-Path $BuildDir "$Configuration\uia-no-msaa-probe.exe"
Write-Host "Built UIA OK: $UiaExe"
Write-Host "Built UIA without form panes OK: $UiaNoPaneExe"
Write-Host "Built UIA with random form OK: $UiaRandomExe"
Write-Host "Built MSAA OK: $MsaaExe"
Write-Host "Built Canvas OK: $CanvasExe"
Write-Host "Built UIA pressure OK: $PressureExe"
Write-Host "Built UIA pressure 500 OK: $Pressure500Exe"
Write-Host "Built UIA pressure 1000 OK: $Pressure1000Exe"
Write-Host "Built UIA pressure 2000 OK: $Pressure2000Exe"
Write-Host "Built UIA probe OK: $ProbeExe"
