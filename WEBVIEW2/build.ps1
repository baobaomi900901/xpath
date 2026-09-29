param(
    [ValidateSet('Debug', 'Release')]
    [string]$Configuration = 'Release'
)
$ErrorActionPreference = 'Stop'
$SdkVersion = (Get-Content -LiteralPath (Join-Path $PSScriptRoot 'sdk-version.txt') -Raw).Trim()
$SdkDirectory = Join-Path $PSScriptRoot ".tools\microsoft.web.webview2.$SdkVersion"
$SdkHeader = Join-Path $SdkDirectory 'build\native\include\WebView2.h'
$SdkLibrary = Join-Path $SdkDirectory 'build\native\x64\WebView2LoaderStatic.lib'
if (-not ((Test-Path -LiteralPath $SdkHeader) -and (Test-Path -LiteralPath $SdkLibrary))) {
    $CacheDirectory = Join-Path $PSScriptRoot '.tools'
    New-Item -ItemType Directory -Path $CacheDirectory -Force | Out-Null
    $Archive = Join-Path $CacheDirectory "microsoft.web.webview2.$SdkVersion.zip"
    $SdkUrl = "https://api.nuget.org/v3-flatcontainer/microsoft.web.webview2/$SdkVersion/microsoft.web.webview2.$SdkVersion.nupkg"
    Write-Host "Downloading official WebView2 SDK $SdkVersion ..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -UseBasicParsing -Uri $SdkUrl -OutFile $Archive -TimeoutSec 120
    $ExpectedHash = 'F492BBF547D0DA329553B6727435B677579B1E9F91CC9E4A1AD029366D5F23D0'
    if ((Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash -ne $ExpectedHash) {
        throw 'WebView2 SDK checksum mismatch.'
    }
    Expand-Archive -LiteralPath $Archive -DestinationPath $SdkDirectory -Force
    if (-not ((Test-Path -LiteralPath $SdkHeader) -and (Test-Path -LiteralPath $SdkLibrary))) {
        throw 'WebView2 SDK extraction incomplete.'
    }
}

$VsWhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
if (-not (Test-Path -LiteralPath $VsWhere)) {
    throw 'Visual Studio Installer not found. Install Desktop development with C++.'
}
$VsInstallPath = & $VsWhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$VsVersion = & $VsWhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property catalog_productLineVersion
if (-not $VsInstallPath -or -not $VsVersion) { throw 'MSVC C++ build tools not found.' }
$Generator = switch ($VsVersion.Trim()) {
    { $_ -in '18', '2026' } { 'Visual Studio 18 2026' }
    { $_ -in '17', '2022' } { 'Visual Studio 17 2022' }
    { $_ -in '16', '2019' } { 'Visual Studio 16 2019' }
    default { throw "Unsupported Visual Studio version: $VsVersion" }
}
$CMakeCommand = Get-Command cmake -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
$CMakeCandidates = @()
if ($CMakeCommand) {
    $CMakeCandidates += $CMakeCommand.Source
}
$CMakeCandidates += Join-Path $VsInstallPath.Trim() 'Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
$CMake = $null
foreach ($Candidate in ($CMakeCandidates | Select-Object -Unique)) {
    if (-not (Test-Path -LiteralPath $Candidate -PathType Leaf)) { continue }
    try {
        $CapabilitiesJson = & $Candidate -E capabilities
        if ($LASTEXITCODE -ne 0) { continue }
        $Capabilities = ($CapabilitiesJson -join "`n") | ConvertFrom-Json
        $SupportedVersion = ($Capabilities.version.major -gt 3) -or
            (($Capabilities.version.major -eq 3) -and ($Capabilities.version.minor -ge 20))
        if ($SupportedVersion -and ($Capabilities.generators.name -contains $Generator)) {
            $CMake = $Candidate
            break
        }
    } catch {
        Write-Verbose "Cannot inspect CMake: $Candidate"
    }
}
if (-not $CMake) {
    throw "No compatible CMake found for $Generator. Install C++ CMake tools for Windows, or update PATH CMake (VS 2019: 3.20+, VS 2022: 3.21+, VS 2026: 4.2+)."
}
Write-Host "Using CMake: $CMake"
$BuildDirectory = Join-Path $PSScriptRoot 'build'
& $CMake -S $PSScriptRoot -B $BuildDirectory -G $Generator -A x64 "-DWEBVIEW2_SDK_DIR=$SdkDirectory"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $CMake --build $BuildDirectory --config $Configuration
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Built OK: $(Join-Path $BuildDirectory "$Configuration\webview2-shooting-range.exe")"
