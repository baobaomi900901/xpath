param(
    [ValidateSet("8", "11", "17", "21", "25")]
    [string[]]$Versions,
    [switch]$SkipBuild,
    [switch]$ForceBuild,
    [switch]$NoLaunch
)

$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$Options = @(
    [pscustomobject]@{ Version = "8"; Label = "JDK 8" },
    [pscustomobject]@{ Version = "11"; Label = "JDK 11" },
    [pscustomobject]@{ Version = "17"; Label = "JDK 17" },
    [pscustomobject]@{ Version = "21"; Label = "JDK 21" },
    [pscustomobject]@{ Version = "25"; Label = "JDK 25" },
    [pscustomobject]@{ Version = $null; Label = "已完成选择" }
)

function Write-SelectorLine {
    param(
        [string]$Text,
        [bool]$Focused
    )

    if ($Focused) {
        Write-Host $Text -ForegroundColor Black -BackgroundColor Gray
    } else {
        Write-Host $Text
    }
}

function Read-JdkSelection {
    $selected = @{}
    $focusedIndex = 0
    $message = ""

    while ($true) {
        Clear-Host
        Write-Host "请选择运行版本(可多选):"
        Write-Host ""

        for ($index = 0; $index -lt $Options.Count; $index++) {
            $option = $Options[$index]
            $prefix = if ($index -eq $focusedIndex) { ">" } else { " " }

            if ($null -eq $option.Version) {
                $line = "$prefix [ 已完成选择 ]"
            } else {
                $mark = if ($selected.ContainsKey($option.Version)) { "x" } else { " " }
                $line = "$prefix [$mark] $($option.Label)"
            }

            Write-SelectorLine -Text $line -Focused ($index -eq $focusedIndex)
        }

        if ($message) {
            Write-Host ""
            Write-Host $message -ForegroundColor Yellow
        }

        $key = [Console]::ReadKey($true)
        switch ($key.Key) {
            "UpArrow" {
                $focusedIndex = ($focusedIndex - 1 + $Options.Count) % $Options.Count
                $message = ""
            }
            "DownArrow" {
                $focusedIndex = ($focusedIndex + 1) % $Options.Count
                $message = ""
            }
            "Spacebar" {
                $option = $Options[$focusedIndex]
                if ($null -ne $option.Version) {
                    if ($selected.ContainsKey($option.Version)) {
                        $selected.Remove($option.Version)
                    } else {
                        $selected[$option.Version] = $true
                    }
                }
                $message = ""
            }
            "Enter" {
                $option = $Options[$focusedIndex]
                if ($null -ne $option.Version) {
                    if ($selected.ContainsKey($option.Version)) {
                        $selected.Remove($option.Version)
                    } else {
                        $selected[$option.Version] = $true
                    }
                    $message = ""
                    continue
                }

                if ($selected.Count -eq 0) {
                    $message = "请至少选择一个 JDK 版本。"
                    continue
                }

                return @($Options |
                    Where-Object { $null -ne $_.Version -and $selected.ContainsKey($_.Version) } |
                    ForEach-Object { $_.Version })
            }
            "Escape" {
                return @()
            }
        }
    }
}

$selectedVersions = @()
if ($PSBoundParameters.ContainsKey("Versions") -and $Versions.Count -gt 0) {
    $selectedVersions = @($Versions)
} else {
    $selectedVersions = @(Read-JdkSelection)
    if ($selectedVersions.Count -eq 0) {
        Clear-Host
        Write-Host "已取消。"
        exit 0
    }
    Clear-Host
}

Write-Host "Selected JDK versions: $($selectedVersions -join ', ')"
& (Join-Path $ProjectRoot "run.ps1") `
    -Versions $selectedVersions `
    -SkipBuild:$SkipBuild `
    -ForceBuild:$ForceBuild `
    -NoLaunch:$NoLaunch
