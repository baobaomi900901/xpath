param([Parameter(Mandatory=$true)][int]$TargetPid, [string]$QtVersion, [string]$Frontend)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class QtWindowProbe {
    public delegate bool EnumCallback(IntPtr hwnd, IntPtr parameter);
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumCallback callback, IntPtr parameter);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint pid);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetWindowText(IntPtr hwnd, System.Text.StringBuilder text, int count);
    public static IntPtr Find(int pid) {
        IntPtr result = IntPtr.Zero;
        EnumWindows((hwnd, parameter) => {
            uint owner; GetWindowThreadProcessId(hwnd, out owner);
            var text = new System.Text.StringBuilder(256);
            GetWindowText(hwnd, text, text.Capacity);
            if (owner == pid && text.ToString().StartsWith("Qt ")) { result = hwnd; return false; }
            return true;
        }, IntPtr.Zero);
        return result;
    }
}
'@
$results = @()
$outputDir = Join-Path $PSScriptRoot "artifacts"
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
$version = $QtVersion
$frontend = $Frontend
$process = Get-Process -Id $TargetPid
$root = $null
for ($attempt = 0; $attempt -lt 40 -and -not $root; $attempt++) {
    Start-Sleep -Milliseconds 250
    $handle = [QtWindowProbe]::Find($process.Id)
    if ($handle -ne [IntPtr]::Zero) { $root = [System.Windows.Automation.AutomationElement]::FromHandle($handle) }
}
if (-not $root) { throw "No UIA window: $version / $frontend" }
for ($attempt = 0; $attempt -lt 40; $attempt++) {
    $nodes = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)
    $names = @($nodes | ForEach-Object { $_.Current.Name })
    if ($names -contains "姓名") { break }
    Start-Sleep -Milliseconds 250
}
$names | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $outputDir "$version-$frontend-uia-names.json") -Encoding UTF8
foreach ($expected in @("姓名", "密码", "邮箱", "年龄", "保存", "重置")) {
    if ($names -notcontains $expected) { throw "Missing UIA name: $version / $frontend / $expected" }
}
$edit = @($nodes | Where-Object { $_.Current.Name -eq "姓名" -and $_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Edit })[0]
if (-not $edit) { throw "Missing name edit: $version / $frontend" }
$value = $edit.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
$value.SetValue("UIA 验收")
if ($value.Current.Value -ne "UIA 验收") { throw "ValuePattern write failed" }
$reset = @($nodes | Where-Object { $_.Current.Name -eq "重置" -and $_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button })[0]
$reset.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
Start-Sleep -Milliseconds 200
if ($value.Current.Value -ne "") { throw "UIA reset failed" }
$results += [PSCustomObject]@{ qtVersion=$version; frontend=$frontend; title=$root.Current.Name; descendants=$nodes.Count; valueAndInvoke=$true }
$results | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $outputDir "$version-$frontend-uia.json") -Encoding UTF8
$results | Format-Table
