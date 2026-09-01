$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BuildScript = Join-Path $ProjectRoot "build.ps1"
$StartScript = Join-Path $ProjectRoot "start.ps1"
$Versions = @("8", "11", "17", "21", "25")
$ExpectedClassMajor = @{
    "8" = 52
    "11" = 55
    "17" = 61
    "21" = 65
    "25" = 69
}

function Assert-True {
    param(
        [bool]$Condition,
        [string]$Message
    )

    if (-not $Condition) {
        throw $Message
    }
}

function Get-ClassMajorVersion {
    param([string]$JarPath)

    $tempRoot = Join-Path $ProjectRoot "target\test-class-version"
    $extractRoot = Join-Path $tempRoot ([Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $extractRoot | Out-Null

    try {
        Push-Location $extractRoot
        try {
            & jar xf $JarPath "com/xpath/shootingrange/Main.class"
            if ($LASTEXITCODE -ne 0) {
                throw "Unable to extract Main.class from $JarPath"
            }
        } finally {
            Pop-Location
        }

        $classPath = Join-Path $extractRoot "com\xpath\shootingrange\Main.class"
        $bytes = [System.IO.File]::ReadAllBytes($classPath)
        return ($bytes[6] -shl 8) -bor $bytes[7]
    } finally {
        Remove-Item -LiteralPath $extractRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Assert-True (Test-Path -LiteralPath $StartScript) "start.ps1 is missing"

& $BuildScript -Versions $Versions -ForceBuild
Assert-True ($LASTEXITCODE -eq 0) "Multi-JDK build failed"

foreach ($version in $Versions) {
    $jarPath = Join-Path $ProjectRoot "target\jdk-$version\shooting-range-$version.jar"
    Assert-True (Test-Path -LiteralPath $jarPath) "JDK $version artifact is missing: $jarPath"

    $major = Get-ClassMajorVersion -JarPath $jarPath
    Assert-True ($major -eq $ExpectedClassMajor[$version]) `
        "JDK $version artifact has class major $major; expected $($ExpectedClassMajor[$version])"
}

& $StartScript -Versions @("8", "25") -SkipBuild -NoLaunch
Assert-True ($LASTEXITCODE -eq 0) "Non-interactive start validation failed"

Write-Host "Multi-JDK integration tests passed."
