param(
    [Parameter(Mandatory = $true)][int]$ProcessId,
    [ValidateSet('Inspect', 'Select', 'KeyNext', 'Refresh', 'Resize', 'MinimizeRestore', 'Close')]
    [string]$Action = 'Inspect',
    [ValidateRange(0, 2)][int]$Index = 0
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Add-Type @'
using System;
using System.Text;
using System.Runtime.InteropServices;
public static class NativeRange {
    [DllImport("user32.dll")] public static extern IntPtr GetDlgItem(IntPtr hwnd, int id);
    [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr hwnd, uint msg, IntPtr wp, IntPtr lp);
    [DllImport("user32.dll", CharSet = CharSet.Unicode, EntryPoint = "SendMessageW")]
    public static extern IntPtr GetListText(IntPtr hwnd, uint msg, IntPtr wp, StringBuilder text);
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr hwnd, uint msg, IntPtr wp, IntPtr lp);
    [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr hwnd, int x, int y, int width, int height, bool repaint);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hwnd, int command);
    [DllImport("user32.dll")] public static extern bool IsWindowEnabled(IntPtr hwnd);
    public static string Text(IntPtr hwnd) {
        var text = new StringBuilder(2048);
        GetListText(hwnd, 0x000D, (IntPtr)text.Capacity, text);
        return text.ToString();
    }
}
'@
$RangeProcess = Get-Process -Id $ProcessId
$Window = $RangeProcess.MainWindowHandle
if ($Window -eq [IntPtr]::Zero) { throw 'Main window missing' }
$Menu = [NativeRange]::GetDlgItem($Window, 1001)
if ($Menu -eq [IntPtr]::Zero) { throw 'Native menu missing' }
switch ($Action) {
    'Select' {
        [void][NativeRange]::SendMessage($Menu, 0x0186, [IntPtr]$Index, [IntPtr]::Zero)
        [void][NativeRange]::SendMessage($Window, 0x0111, [IntPtr](1001 + (1 -shl 16)), $Menu)
    }
    'KeyNext' {
        [void][NativeRange]::SendMessage($Menu, 0x0100, [IntPtr]0x28, [IntPtr]::Zero)
        [void][NativeRange]::SendMessage($Menu, 0x0101, [IntPtr]0x28, [IntPtr]::Zero)
    }
    'Refresh' {
        [void][NativeRange]::SendMessage([NativeRange]::GetDlgItem($Window, 1003), 0x00F5, [IntPtr]::Zero, [IntPtr]::Zero)
    }
    'Resize' { [void][NativeRange]::MoveWindow($Window, 40, 40, 1040, 760, $true) }
    'MinimizeRestore' {
        [void][NativeRange]::ShowWindow($Window, 6)
        Start-Sleep -Milliseconds 200
        [void][NativeRange]::ShowWindow($Window, 9)
    }
    'Close' {
        [void][NativeRange]::PostMessage($Window, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)
        exit 0
    }
}
$Items = @()
for ($ItemIndex = 0; $ItemIndex -lt 3; $ItemIndex++) {
    $Text = New-Object System.Text.StringBuilder 256
    [void][NativeRange]::GetListText($Menu, 0x0189, [IntPtr]$ItemIndex, $Text)
    $Items += $Text.ToString()
}
[pscustomobject]@{
    title = [NativeRange]::Text($Window)
    items = $Items
    selected = [NativeRange]::SendMessage($Menu, 0x0188, [IntPtr]::Zero, [IntPtr]::Zero).ToInt32()
    address = [NativeRange]::Text([NativeRange]::GetDlgItem($Window, 1002))
    status = [NativeRange]::Text([NativeRange]::GetDlgItem($Window, 1004))
    refreshEnabled = [NativeRange]::IsWindowEnabled([NativeRange]::GetDlgItem($Window, 1003))
} | ConvertTo-Json -Compress
