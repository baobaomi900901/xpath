param(
    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Release",
    [string]$CompilerPath = $env:DELPHI_DCC32,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
if (-not $SkipBuild) {
    & (Join-Path $PSScriptRoot 'build.ps1') -Configuration $Configuration -CompilerPath $CompilerPath
}
$executable = Join-Path $PSScriptRoot "build\$Configuration\Win32VclShootingRange.exe"
if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
    throw "Executable not found: $executable. Run DELPHI\build.ps1 first."
}
$process = Start-Process -FilePath $executable -WorkingDirectory (Split-Path $executable -Parent) -WindowStyle Normal -PassThru
Start-Sleep -Milliseconds 800
if ($process.HasExited) {
    throw "Delphi target exited immediately (exit code $($process.ExitCode))."
}
Write-Host "Running OK, pid=$($process.Id): $executable"
