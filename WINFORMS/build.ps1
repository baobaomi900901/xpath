param(
    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Release",
    [switch]$Run
)

$ErrorActionPreference = "Stop"
$project = Join-Path $PSScriptRoot "GuiAutomationRange.csproj"
$exe = Join-Path $PSScriptRoot "bin\$Configuration\GuiAutomationRange.exe"

function Find-MSBuild {
    $vswhere = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
    if (Test-Path -LiteralPath $vswhere) {
        $found = & $vswhere -latest -products * -requires Microsoft.Component.MSBuild -find "MSBuild\**\Bin\MSBuild.exe" 2>$null
        foreach ($candidate in @($found)) {
            if ($candidate -and (Test-Path -LiteralPath $candidate)) { return $candidate }
        }
    }

    $fallbacks = @(
        "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe",
        "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe",
        "C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe",
        "C:\Program Files (x86)\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe",
        "D:\Program Files\Microsoft Visual Studio\18\Community\MSBuild\Current\Bin\MSBuild.exe"
    )
    foreach ($candidate in $fallbacks) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    return $null
}

$msbuild = Find-MSBuild
if (-not $msbuild) {
    throw "MSBuild was not found. Install Visual Studio 2022 Build Tools with the .NET desktop build tools workload."
}

Write-Host "Building $project ($Configuration) with $msbuild"
& $msbuild $project "/p:Configuration=$Configuration" /m /nologo /v:minimal
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
if (-not (Test-Path -LiteralPath $exe)) {
    throw "Build finished without producing $exe"
}

$size = (Get-Item -LiteralPath $exe).Length
Write-Host ("Built: {0} ({1:N0} bytes)" -f $exe, $size)
if ($Run) {
    Start-Process -FilePath $exe -WorkingDirectory (Join-Path $PSScriptRoot "bin\$Configuration")
}
