param(
    [string]$QtRoot = "D:\Qt\5.15.2\mingw81_64",
    [string]$MingwBin = "D:\Qt\Tools\mingw810_64\bin",
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$BuildDir = Join-Path $Root "build"
$ExeName = "acc-hidden-profile.exe"
$Exe = Join-Path $BuildDir $ExeName
$RunDir = "D:\Qt\run\acc-hidden-profile"

if (-not $SkipBuild) {
    & (Join-Path $Root "build.ps1") -QtRoot $QtRoot -MingwBin $MingwBin
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

if (-not (Test-Path $Exe)) {
    Write-Error ("Executable not found: " + $Exe)
    exit 1
}

if (Test-Path $RunDir) {
    Remove-Item $RunDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

$excludeDirs = @("CMakeFiles", "acc-hidden-profile_autogen")
$excludeFiles = @("build.ninja", "CMakeCache.txt", "cmake_install.cmake", ".ninja_deps", ".ninja_log")
Get-ChildItem $BuildDir | ForEach-Object {
    if ($_.PSIsContainer) {
        if ($excludeDirs -contains $_.Name) { return }
        Copy-Item $_.FullName (Join-Path $RunDir $_.Name) -Recurse -Force
    } else {
        if ($excludeFiles -contains $_.Name) { return }
        Copy-Item $_.FullName (Join-Path $RunDir $_.Name) -Force
    }
}

# Avoid double-loading QtQuick modules from both deploy dir and Qt install.
Remove-Item Env:QML2_IMPORT_PATH -ErrorAction SilentlyContinue
Remove-Item Env:QML_IMPORT_PATH -ErrorAction SilentlyContinue
Remove-Item Env:QT_PLUGIN_PATH -ErrorAction SilentlyContinue

$RunExe = Join-Path $RunDir $ExeName
Write-Host ("Starting: " + $RunExe)

Get-Process -Name "acc-hidden-profile" -ErrorAction SilentlyContinue | Stop-Process -Force

$proc = Start-Process -FilePath $RunExe -WorkingDirectory $RunDir -PassThru
Start-Sleep -Milliseconds 1000

if ($proc.HasExited) {
    Write-Error ("App exited immediately, code=" + $proc.ExitCode)
    exit $proc.ExitCode
}

Write-Host ("Running OK, pid=" + $proc.Id)
