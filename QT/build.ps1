param(
    [string[]]$Versions = @("5.15.2", "6.8.3"),
    [string]$QtRoot,
    [string]$MingwBin,
    [string]$SdkRoot,
    [switch]$InstallSdk
)
$ErrorActionPreference = "Stop"
$launchArgs = @((Join-Path $PSScriptRoot "..\tools\start_qt.py"), "--versions") + $Versions + @("--no-launch")

if ($QtRoot) { $launchArgs += @("--qt-root", $QtRoot) }
if ($MingwBin) { $launchArgs += @("--mingw-bin", $MingwBin) }
if ($SdkRoot) { $launchArgs += @("--sdk-root", $SdkRoot) }
if ($InstallSdk) { $launchArgs += "--install-sdk" }
& python @launchArgs
exit $LASTEXITCODE
