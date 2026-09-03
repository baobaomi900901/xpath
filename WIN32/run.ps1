param(
    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Release",
    [ValidateSet("uia", "msaa", "canvas")]
    [string]$Backend = "uia",
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

if (-not $SkipBuild) {
    & (Join-Path $PSScriptRoot "build.ps1") -Configuration $Configuration
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$Exe = Join-Path $PSScriptRoot "build\$Configuration\win32-shooting-range-$Backend.exe"
if (-not (Test-Path -LiteralPath $Exe)) {
    Write-Error "Executable not found: $Exe"
    exit 1
}

$Process = Start-Process -FilePath $Exe -WorkingDirectory (Split-Path $Exe) -PassThru
Start-Sleep -Milliseconds 700
if ($Process.HasExited) {
    Write-Error "Application exited immediately, code=$($Process.ExitCode)"
    exit $Process.ExitCode
}

Write-Host "Running OK, pid=$($Process.Id)"
