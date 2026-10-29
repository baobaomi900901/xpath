param([string[]]$Versions = @("8", "11", "17", "21", "25"))

$ErrorActionPreference = "Stop"
$javaRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $javaRoot
$testOutput = Join-Path $javaRoot "target/custom-controls-tests"
New-Item -ItemType Directory -Force -Path $testOutput | Out-Null
Push-Location $repoRoot
try {
    foreach ($version in $Versions) {
        $jdkRoot = Join-Path $javaRoot ".tools/jdks/corretto/$version"
        $compiler = Get-ChildItem -LiteralPath $jdkRoot -Filter javac.exe -Recurse |
            Select-Object -First 1
        if (-not $compiler) { throw "JDK $version compiler is missing" }
        $runtime = Join-Path $compiler.DirectoryName "java.exe"
        & $compiler.FullName -encoding UTF-8 -d $testOutput `
            (Join-Path $javaRoot "src/main/java/com/xpath/shootingrange/ui/CustomControlsPanel.java") `
            (Join-Path $PSScriptRoot "CustomControlsPanelTest.java")
        if ($LASTEXITCODE -ne 0) { throw "JDK $version test compilation failed" }
        & $runtime '-Djava.awt.headless=true' -cp $testOutput CustomControlsPanelTest
        if ($LASTEXITCODE -ne 0) { throw "JDK $version custom controls tests failed" }
        Write-Host "JDK $version custom controls tests passed."
    }
} finally {
    Pop-Location
}
