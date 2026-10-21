param(
    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Release",
    [string]$CompilerPath = $env:DELPHI_DCC32,
    [string[]]$DevExpressPaths = @($env:DELPHI_DEVEXPRESS_PATHS -split ';' | Where-Object { $_ })
)

$ErrorActionPreference = "Stop"

if ($CompilerPath) {
    if (-not (Test-Path -LiteralPath $CompilerPath -PathType Leaf)) {
        throw "Delphi compiler not found: $CompilerPath"
    }
} else {
    # Prefer Delphi 2010, the original target of this VCL project.
    $registryRoots = @(
        'HKCU:\Software\CodeGear\BDS\7.0',
        'HKLM:\SOFTWARE\WOW6432Node\CodeGear\BDS\7.0',
        'HKLM:\SOFTWARE\CodeGear\BDS\7.0'
    )
    foreach ($registryRoot in $registryRoots) {
        $installation = Get-ItemProperty -LiteralPath $registryRoot -ErrorAction SilentlyContinue
        if ($installation.RootDir) {
            $candidate = Join-Path $installation.RootDir 'bin\dcc32.exe'
            if (Test-Path -LiteralPath $candidate -PathType Leaf) {
                $CompilerPath = $candidate
                break
            }
        }
    }
    if (-not $CompilerPath) {
        $compilerCommand = Get-Command dcc32.exe -ErrorAction SilentlyContinue
        if ($compilerCommand) { $CompilerPath = $compilerCommand.Source }
    }
    if (-not $CompilerPath) {
        throw 'Delphi Win32 compiler not found. Set DELPHI_DCC32 or pass -CompilerPath with the full path to dcc32.exe.'
    }
}

$CompilerPath = (Resolve-Path -LiteralPath $CompilerPath).Path
$delphiRoot = Split-Path (Split-Path $CompilerPath -Parent) -Parent
$buildDir = Join-Path $PSScriptRoot "build\$Configuration"
$dcuDir = Join-Path $buildDir 'dcu'
$executable = Join-Path $buildDir 'Win32VclShootingRange.exe'
New-Item -ItemType Directory -Force -Path $dcuDir | Out-Null

$compilerArguments = @(
    '-B', '-Q', '-CG', '--no-config', '--codepage:65001',
    "-E$buildDir"
)
$unitPaths = @(Join-Path $PSScriptRoot 'vendor\VirtualTreeView')
if ($DevExpressPaths.Count -gt 0) {
    foreach ($unitPath in $DevExpressPaths) {
        if (-not (Test-Path -LiteralPath $unitPath -PathType Container)) {
            throw "DevExpress library directory not found: $unitPath"
        }
        $unitPaths += (Resolve-Path -LiteralPath $unitPath).Path
    }
    foreach ($unitName in @('cxGrid', 'cxTL')) {
        $found = $false
        foreach ($unitPath in $unitPaths) {
            if ((Test-Path -LiteralPath (Join-Path $unitPath "$unitName.pas")) -or
                (Test-Path -LiteralPath (Join-Path $unitPath "$unitName.dcu"))) { $found = $true }
        }
        if (-not $found) { throw "DevExpress unit $unitName.pas/.dcu not found in -DevExpressPaths." }
    }
    $compilerArguments += '-DWITH_DEVEXPRESS'
    Write-Host 'DevExpress: enabled (matching static-link VCL libraries required).'
} else {
    Write-Host 'DevExpress: unavailable; TcxGrid/TcxTreeList pages will show dependency notices.'
}
$compilerArguments += @("-I$($unitPaths -join ';')", "-R$($unitPaths -join ';')")
$legacyLibrary = Join-Path $delphiRoot 'lib'
$modernLibrary = Join-Path $delphiRoot 'lib\win32\release'
if (Test-Path -LiteralPath (Join-Path $legacyLibrary 'Forms.dcu')) {
    $compilerArguments += @("-U$((@($legacyLibrary) + $unitPaths) -join ';')", "-N0$dcuDir")
} elseif (Test-Path -LiteralPath (Join-Path $modernLibrary 'Vcl.Forms.dcu')) {
    $compilerArguments += @("-U$((@($modernLibrary) + $unitPaths) -join ';')", "-NU$dcuDir", '-NSSystem;Winapi;Vcl;Data;Datasnap;System.Win;Vcl.Win')
} else {
    throw "VCL Win32 libraries not found under $delphiRoot"
}
if ($Configuration -eq 'Debug') {
    $compilerArguments += @('-$D+', '-$L+', '-$O-', '-$Q+', '-$R+', '-V')
} else {
    $compilerArguments += @('-$D-', '-$L-', '-$Y-', '-$O+')
}
$compilerArguments += 'Win32VclShootingRange.dpr'

Write-Host "Compiler: $CompilerPath"
Push-Location $PSScriptRoot
try {
    & $CompilerPath @compilerArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Delphi build failed (exit code $LASTEXITCODE). Close the running target before rebuilding."
    }
} finally {
    Pop-Location
}
if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
    throw "Build did not produce the executable: $executable"
}
Write-Host "Built OK: $executable"
