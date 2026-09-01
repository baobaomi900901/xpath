param(
    [ValidateSet("8", "11", "17", "21", "25")]
    [string[]]$Versions = @("21"),
    [switch]$ForceBuild
)

$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$ToolsDir = Join-Path $ProjectRoot ".tools"
$JdksRoot = Join-Path $ToolsDir "jdks\corretto"
$MavenVersion = "3.9.9"
$MavenHome = Join-Path $ToolsDir "apache-maven-$MavenVersion"
$MavenBin = Join-Path $MavenHome "bin\mvn.cmd"

function Ensure-Maven {
    if (Test-Path -LiteralPath $MavenBin) {
        return
    }

    Write-Host "Downloading Maven $MavenVersion ..."
    New-Item -ItemType Directory -Force -Path $ToolsDir | Out-Null
    $zipPath = Join-Path $ToolsDir "apache-maven-$MavenVersion-bin.zip"
    $url = "https://archive.apache.org/dist/maven/maven-3/$MavenVersion/binaries/apache-maven-$MavenVersion-bin.zip"

    Invoke-WebRequest -Uri $url -OutFile $zipPath
    Expand-Archive -LiteralPath $zipPath -DestinationPath $ToolsDir -Force
    Remove-Item -LiteralPath $zipPath -Force
}

function Get-JdkHome {
    param([string]$Version)

    $versionRoot = Join-Path $JdksRoot $Version
    $javac = Get-ChildItem -LiteralPath $versionRoot -Filter javac.exe -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.DirectoryName -like "*\bin" } |
        Select-Object -First 1

    if (-not $javac) {
        throw "Corretto JDK $Version not found under $versionRoot"
    }

    return $javac.Directory.Parent.FullName
}

function Test-BuildRequired {
    param([string]$JarPath)

    if (-not (Test-Path -LiteralPath $JarPath)) {
        return $true
    }

    $jarTime = (Get-Item -LiteralPath $JarPath).LastWriteTime
    $sourceFiles = @(
        (Join-Path $ProjectRoot "pom.xml")
    ) + @(Get-ChildItem -Path (Join-Path $ProjectRoot "src") -Recurse -File -ErrorAction SilentlyContinue)

    foreach ($file in $sourceFiles) {
        if ($file.LastWriteTime -gt $jarTime) {
            return $true
        }
    }

    return $false
}

Ensure-Maven

foreach ($version in $Versions) {
    $jarPath = Join-Path $ProjectRoot "target\jdk-$version\shooting-range-$version.jar"
    if (-not $ForceBuild -and -not (Test-BuildRequired -JarPath $jarPath)) {
        Write-Host "JDK $version artifact is up to date, skipping build."
        continue
    }

    $jdkHome = Get-JdkHome -Version $version
    Write-Host "Building Java shooting range for JDK $version ..."

    $previousJavaHome = $env:JAVA_HOME
    $previousPath = $env:Path
    Push-Location $ProjectRoot
    try {
        $env:JAVA_HOME = $jdkHome
        $env:Path = "$jdkHome\bin;$previousPath"

        $previousErrorAction = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        $output = & $MavenBin -q "-Dtarget.java.version=$version" -DskipTests package 2>&1
        $exitCode = $LASTEXITCODE
        $ErrorActionPreference = $previousErrorAction

        if ($exitCode -ne 0) {
            $output | ForEach-Object { Write-Host $_ }
            throw "Maven build for JDK $version failed with exit code $exitCode"
        }
    } finally {
        $env:JAVA_HOME = $previousJavaHome
        $env:Path = $previousPath
        Pop-Location
    }

    if (-not (Test-Path -LiteralPath $jarPath)) {
        throw "Build completed without producing $jarPath"
    }

    Write-Host "Build finished: $jarPath"
}
