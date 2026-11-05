param(
    [ValidateSet("8", "11", "17", "21", "25")]
    [string[]]$Versions = @("21"),
    [switch]$SkipBuild,
    [switch]$ForceBuild,
    [switch]$NoLaunch
)

$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$JdksRoot = Join-Path $ProjectRoot ".tools\jdks\corretto"

if (-not $SkipBuild) {
    & (Join-Path $ProjectRoot "build.ps1") -Versions $Versions -ForceBuild:$ForceBuild
}

foreach ($version in $Versions) {
    $jarPath = Join-Path $ProjectRoot "target\jdk-$version\shooting-range-$version.jar"
    if (-not (Test-Path -LiteralPath $jarPath)) {
        throw "JDK $version artifact not found: $jarPath. Build it before using -SkipBuild."
    }

    $versionRoot = Join-Path $JdksRoot $version
    $java = Get-ChildItem -LiteralPath $versionRoot -Filter javaw.exe -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.DirectoryName -like "*\bin" } |
        Select-Object -First 1

    if (-not $java) {
        throw "Corretto JDK $version not found under $versionRoot"
    }

    if ($NoLaunch) {
        Write-Host "Validated JDK ${version}: $jarPath"
        continue
    }

    $process = Start-Process -FilePath $java.FullName -ArgumentList "-jar `"$jarPath`"" -PassThru
    Write-Host "Started JDK $version shooting range (PID $($process.Id))."
}
