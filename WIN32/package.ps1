param(
    [string]$OutputDirectory = (Join-Path $PSScriptRoot "dist"),
    [string]$BuildDirectory = (Join-Path $PSScriptRoot "build\package")
)

$ErrorActionPreference = "Stop"
$BuildDirectory = [System.IO.Path]::GetFullPath($BuildDirectory)
$OutputDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)

function Get-PackageSha256([string]$Path) {
    $Algorithm = [System.Security.Cryptography.SHA256]::Create()
    $InputStream = [System.IO.File]::OpenRead($Path)
    try {
        return [System.BitConverter]::ToString($Algorithm.ComputeHash($InputStream)).Replace("-", "").ToLowerInvariant()
    } finally {
        $InputStream.Dispose()
        $Algorithm.Dispose()
    }
}

# Build separately from the developer's running programs; no GUI is launched.
& (Join-Path $PSScriptRoot "build.ps1") -Configuration Release -BuildDirectory $BuildDirectory -BuildTests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$CachePath = Join-Path $BuildDirectory "CMakeCache.txt"
$CTestEntry = Select-String -LiteralPath $CachePath -Pattern '^CMAKE_CTEST_COMMAND:INTERNAL=(.+)$'
if (-not $CTestEntry) { throw "CTest path not found in $CachePath" }
$CTest = $CTestEntry.Matches[0].Groups[1].Value
& $CTest --test-dir $BuildDirectory -C Release --output-on-failure
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$VsWhere = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
$VsInstallPath = & $VsWhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if ($LASTEXITCODE -ne 0 -or -not $VsInstallPath) { throw "Visual Studio C++ tools not found" }
$ToolVersionPath = Join-Path $VsInstallPath.Trim() "VC\Auxiliary\Build\Microsoft.VCToolsVersion.default.txt"
$ToolVersion = (Get-Content -LiteralPath $ToolVersionPath -Raw).Trim()
$Dumpbin = Join-Path $VsInstallPath.Trim() "VC\Tools\MSVC\$ToolVersion\bin\Hostx64\x64\dumpbin.exe"
if (-not (Test-Path -LiteralPath $Dumpbin -PathType Leaf)) { throw "dumpbin not found: $Dumpbin" }

$Artifacts = [ordered]@{
    "win32-shooting-range-uia" = @{
        file = "UIA 版（标准 Win32 控件）.exe"
        description = "UIA: standard controls with form item Panes"
    }
    "win32-shooting-range-uia-no-pane" = @{
        file = "UIA 版（标准 Win32 控件_表单item 无 Pane 版本）.exe"
        description = "UIA: standard controls without form item Panes"
    }
    "win32-shooting-range-uia-random" = @{
        file = "UIA 版（标准 Win32 控件_随机表单）.exe"
        description = "UIA: random form order, control IDs and Pane class name"
    }
    "win32-shooting-range-msaa" = @{
        file = "MSAA 版（仅 IAccessible）.exe"
        description = "MSAA: IAccessible form item Panes"
    }
    "win32-shooting-range-canvas" = @{
        file = "自绘版（无内部无障碍树）.exe"
        description = "Canvas: internal grouping without an accessibility tree"
    }
    "win32-uia-pressure" = @{
        file = "UIA 压力靶场（通用版）.exe"
        description = "UIA pressure: command-line depth 500, 1000 or 2000 (default 500)"
    }
    "win32-uia-pressure-500" = @{
        file = "UIA 压力靶场（500 层）.exe"
        description = "UIA pressure: fixed 500 levels"
    }
    "win32-uia-pressure-1000" = @{
        file = "UIA 压力靶场（1000 层）.exe"
        description = "UIA pressure: fixed 1000 levels"
    }
    "win32-uia-pressure-2000" = @{
        file = "UIA 压力靶场（2000 层）.exe"
        description = "UIA pressure: fixed 2000 levels"
    }
    "uia-no-msaa-probe" = @{
        file = "UIA 检测工具（禁用 MSAA Proxy）.exe"
        description = "Console tool: inspect UIA with the MSAA proxy disabled"
    }
}
$Manifest = @()
$SystemDirectory = [System.Environment]::GetFolderPath("System")
$RuntimePattern = '^(MSVCP\d|VCRUNTIME\d|MSVCR\d|CONCRT\d|ucrtbase|ucrtbased|api-ms-win-crt-)'
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null

foreach ($Target in $Artifacts.Keys) {
    $Source = Join-Path $BuildDirectory "Release\$Target.exe"
    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) { throw "Missing build artifact: $Source" }
    $DependencyOutput = & $Dumpbin /dependents $Source
    if ($LASTEXITCODE -ne 0) { throw "Dependency inspection failed: $Source" }
    $Dependencies = @($DependencyOutput | ForEach-Object {
        if ($_ -match '^\s+([a-zA-Z0-9_.-]+\.dll)\s*$') { $Matches[1] }
    } | Sort-Object -Unique)
    if ($Dependencies.Count -eq 0) { throw "No DLL dependencies were parsed for $Source" }
    foreach ($Dependency in $Dependencies) {
        if ($Dependency -match $RuntimePattern) { throw "EXE still needs a separate C++ runtime DLL: $Dependency ($Target)" }
        if ($Dependency -notmatch '^(api-ms-|ext-ms-)' -and
            -not (Test-Path -LiteralPath (Join-Path $SystemDirectory $Dependency) -PathType Leaf)) {
            throw "EXE has a non-system DLL dependency: $Dependency ($Target)"
        }
    }
    $FileName = $Artifacts[$Target].file
    $Destination = Join-Path $OutputDirectory $FileName
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
    $Manifest += [ordered]@{
        file = $FileName
        description = $Artifacts[$Target].description
        architecture = "x64"
        bytes = (Get-Item -LiteralPath $Destination).Length
        sha256 = Get-PackageSha256 $Destination
        systemDlls = $Dependencies
    }
    Write-Host "Packaged standalone EXE: $Destination"
}

$ManifestPath = Join-Path $OutputDirectory "manifest.json"
$Manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $ManifestPath -Encoding UTF8
$ReadmePath = Join-Path $OutputDirectory "README.txt"
$Readme = @(
    "Win32 shooting ranges - Windows x64 standalone EXEs",
    "",
    "Each range can be copied and run as a single EXE. No Python, build tools or VC++ redistributable are needed.",
    "Windows system DLLs are required. GUI programs were not launched during packaging.",
    "The 500/1000/2000 pressure EXEs use the level count in their file name without command-line arguments.",
    "The generic $($Artifacts['win32-uia-pressure'].file) also accepts a command-line depth, e.g. 1000.",
    "The probe is a console diagnostic tool; its default target is the MSAA Only range.",
    ('Example: & ".\{0}" --title "<window title>"' -f $Artifacts['uia-no-msaa-probe'].file),
    "",
    "Files:"
)
foreach ($Entry in $Manifest) { $Readme += "$($Entry.file) - $($Entry.description)" }
$Readme += @("", "SHA-256 hashes and verified DLL imports are recorded in manifest.json.")
$Readme | Set-Content -LiteralPath $ReadmePath -Encoding UTF8

$ZipPath = Join-Path $OutputDirectory "win32-shooting-ranges-x64.zip"
$PackageFiles = @($Manifest | ForEach-Object { Join-Path $OutputDirectory $_.file }) + @($ManifestPath, $ReadmePath)
Add-Type -AssemblyName System.IO.Compression
$ZipStream = [System.IO.File]::Open($ZipPath, [System.IO.FileMode]::Create)
try {
    $Archive = [System.IO.Compression.ZipArchive]::new($ZipStream, [System.IO.Compression.ZipArchiveMode]::Create)
    try {
        foreach ($PackageFile in $PackageFiles) {
            $Entry = $Archive.CreateEntry([System.IO.Path]::GetFileName($PackageFile))
            $InputStream = [System.IO.File]::OpenRead($PackageFile)
            $EntryStream = $Entry.Open()
            try {
                $InputStream.CopyTo($EntryStream)
            } finally {
                $EntryStream.Dispose()
                $InputStream.Dispose()
            }
        }
    } finally {
        $Archive.Dispose()
    }
} finally {
    $ZipStream.Dispose()
}
Write-Host "Packaged $($Manifest.Count) independent EXEs: $OutputDirectory"
Write-Host "ZIP archive: $ZipPath"
