param(
    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Release",
    [switch]$NoBuild,
    [switch]$NoLaunch
)

$ErrorActionPreference = "Stop"
$exe = Join-Path $PSScriptRoot "bin\$Configuration\GuiAutomationRange.exe"
if (-not $NoBuild -or -not (Test-Path -LiteralPath $exe)) {
    & (Join-Path $PSScriptRoot "build.ps1") -Configuration $Configuration
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
if (-not $NoLaunch) {
    Start-Process -FilePath $exe -WorkingDirectory (Split-Path -Parent $exe)
} else {
    Write-Host "Built: $exe"
}
