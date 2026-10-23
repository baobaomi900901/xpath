param(
    [string[]]$Versions = @("5.15.2", "6.8.3"),
    [string]$QtRoot,
    [string]$MingwBin,
    [string]$SdkRoot,
    [switch]$InstallSdk,
    [ValidateSet("widgets", "quick", "profile")][string[]]$Frontends = @("widgets", "quick"),
    [ValidateSet("grouped", "flat", "random")][string]$FormMode = "grouped",
    [switch]$SkipBuild,
    [switch]$SelfTest
)
$ErrorActionPreference = "Stop"
$launchArgs = @((Join-Path $PSScriptRoot "..\tools\start_qt.py"), "--versions") + $Versions + @("--frontends") + $Frontends + @("--form-mode", $FormMode)
if ($SkipBuild) { $launchArgs += "--skip-build" }
if ($SelfTest) { $launchArgs += "--self-test" }

if ($QtRoot) { $launchArgs += @("--qt-root", $QtRoot) }
if ($MingwBin) { $launchArgs += @("--mingw-bin", $MingwBin) }
if ($SdkRoot) { $launchArgs += @("--sdk-root", $SdkRoot) }
if ($InstallSdk) { $launchArgs += "--install-sdk" }
& python @launchArgs
exit $LASTEXITCODE
