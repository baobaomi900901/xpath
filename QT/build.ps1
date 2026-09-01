param(
    [string]$QtRoot = "D:\Qt\5.15.2\mingw81_64",
    [string]$MingwBin = "D:\Qt\Tools\mingw810_64\bin"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path (Join-Path $QtRoot "bin\qmake.exe"))) {
    Write-Error "Qt not found at $QtRoot"
    exit 1
}
if (-not (Test-Path (Join-Path $MingwBin "g++.exe"))) {
    Write-Error "MinGW not found at $MingwBin"
    exit 1
}

$QtBin = Join-Path $QtRoot "bin"
$NinjaDir = "D:\Qt\Tools\Ninja"
$env:PATH = (@($MingwBin, $NinjaDir, $QtBin) + $env:PATH) -join ";"
$env:CMAKE_PREFIX_PATH = $QtRoot

Write-Host "Using Qt at: $QtRoot"
Write-Host "Using MinGW at: $MingwBin"

$BuildDir = Join-Path $PSScriptRoot "build"
$Gcc = Join-Path $MingwBin "gcc.exe"
$Gxx = Join-Path $MingwBin "g++.exe"

& cmake -S $PSScriptRoot -B $BuildDir -G "Ninja" `
    ("-DCMAKE_PREFIX_PATH=" + $QtRoot) `
    ("-DCMAKE_C_COMPILER=" + $Gcc) `
    ("-DCMAKE_CXX_COMPILER=" + $Gxx)
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& cmake --build $BuildDir
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$Exe = Join-Path $BuildDir "acc-hidden-profile.exe"
& (Join-Path $QtBin "windeployqt.exe") --qmldir (Join-Path $PSScriptRoot "qml") $Exe
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ("Built OK: " + $Exe)
