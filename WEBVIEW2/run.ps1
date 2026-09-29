param(
    [ValidateSet('Debug', 'Release')]
    [string]$Configuration = 'Release'
)
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'build.ps1') -Configuration $Configuration
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$Executable = Join-Path $PSScriptRoot "build\$Configuration\webview2-shooting-range.exe"
if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) {
    throw "Executable not found: $Executable. Run WEBVIEW2/build.ps1 first."
}
# The startup check runs hidden; show the interactive range only after it succeeds.
if (-not ('WebView2RangeWindow' -as [type])) { Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class WebView2RangeWindow {
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr window, int command);
    private delegate bool EnumWindowProc(IntPtr window, IntPtr parameter);
    [DllImport("user32.dll")] private static extern bool EnumWindows(EnumWindowProc callback, IntPtr parameter);
    [DllImport("user32.dll")] private static extern uint GetWindowThreadProcessId(IntPtr window, out uint processId);
    [DllImport("user32.dll")] private static extern IntPtr GetWindow(IntPtr window, uint command);
    public static IntPtr Find(int processId) {
        IntPtr result = IntPtr.Zero;
        EnumWindows((window, parameter) => {
            uint owner;
            GetWindowThreadProcessId(window, out owner);
            if (owner == (uint)processId && GetWindow(window, 4) == IntPtr.Zero) {
                result = window;
                return false;
            }
            return true;
        }, IntPtr.Zero);
        return result;
    }
}
'@
}
$RangeProcess = Start-Process -FilePath $Executable -WorkingDirectory (Split-Path $Executable) -WindowStyle Hidden -PassThru
try {
    $Deadline = [DateTime]::UtcNow.AddSeconds(10)
    do {
        $RangeProcess.Refresh()
        if ($RangeProcess.HasExited) {
            throw "Application exited immediately, code=$($RangeProcess.ExitCode)"
        }
        $RangeWindow = [WebView2RangeWindow]::Find($RangeProcess.Id)
        if ($RangeWindow -ne [IntPtr]::Zero) { break }
        Start-Sleep -Milliseconds 100
    } while ([DateTime]::UtcNow -lt $Deadline)
    if ($RangeWindow -eq [IntPtr]::Zero) { throw 'Timed out waiting for application main window.' }
    [void][WebView2RangeWindow]::ShowWindow($RangeWindow, 5)
    Write-Host "Running WebView2 range, pid=$($RangeProcess.Id)"
} catch {
    try { if (-not $RangeProcess.HasExited) { $RangeProcess.Kill() } } catch { }
    throw
}
