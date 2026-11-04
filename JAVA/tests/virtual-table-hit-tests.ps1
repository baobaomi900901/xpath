param([string[]]$Versions = @("8", "11", "17", "21", "25"))

$ErrorActionPreference = "Stop"
$javaRoot = Split-Path -Parent $PSScriptRoot
$testOutput = Join-Path $javaRoot "target/virtual-table-hit-tests"
New-Item -ItemType Directory -Force -Path $testOutput | Out-Null

foreach ($version in $Versions) {
    $jdkRoot = Join-Path $javaRoot ".tools/jdks/corretto/$version"
    $compiler = Get-ChildItem -LiteralPath $jdkRoot -Filter javac.exe -File -Recurse |
        Select-Object -First 1
    if (-not $compiler) { throw "JDK $version compiler is missing" }
    $runtime = Join-Path $compiler.DirectoryName "java.exe"
    & $compiler.FullName -encoding UTF-8 -d $testOutput `
        (Join-Path $javaRoot "src/main/java/com/xpath/shootingrange/ui/VirtualTableHitPanel.java") `
        (Join-Path $PSScriptRoot "VirtualTableHitPanelTest.java")
    if ($LASTEXITCODE -ne 0) { throw "JDK $version test compilation failed" }
    & $runtime '-Djava.awt.headless=true' -cp $testOutput VirtualTableHitPanelTest `
        (Join-Path $javaRoot "target/virtual-table-hit-preview-$version.png")
    if ($LASTEXITCODE -ne 0) { throw "JDK $version virtual table hit tests failed" }
    Write-Host "JDK $version virtual table hit tests passed."
}
