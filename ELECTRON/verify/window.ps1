param(
    [Parameter(Mandatory = $true)][int]$ProcessId,
    [ValidateSet('Inspect', 'Accessibility', 'Msaa', 'Resize', 'Close')][string]$Action = 'Inspect'
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class ElectronRangeWindow {
    private delegate bool EnumWindow(IntPtr hwnd, IntPtr value);
    [DllImport("user32.dll")] private static extern bool EnumWindows(EnumWindow callback, IntPtr value);
    [DllImport("user32.dll")] private static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint pid);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] private static extern int GetClassName(IntPtr hwnd, System.Text.StringBuilder name, int length);
    [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr window, int x, int y, int width, int height, bool repaint);
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr window, uint message, IntPtr wp, IntPtr lp);
    public static IntPtr Find(int pid) {
        IntPtr result=IntPtr.Zero;
        EnumWindows((hwnd, value) => {
            uint owner;
            GetWindowThreadProcessId(hwnd, out owner);
            var name=new System.Text.StringBuilder(256);
            GetClassName(hwnd, name, name.Capacity);
            if (owner == pid && name.ToString() == "Chrome_WidgetWin_1") { result=hwnd; return false; }
            return true;
        }, IntPtr.Zero);
        return result;
    }
}
'@
$RangeProcess = Get-Process -Id $ProcessId
$Window = $RangeProcess.MainWindowHandle
if ($Window -eq [IntPtr]::Zero) { $Window = [ElectronRangeWindow]::Find($ProcessId) }
if ($Window -eq [IntPtr]::Zero) { throw 'Electron main window missing' }
switch ($Action) {
    'Close' {
        [void][ElectronRangeWindow]::PostMessage($Window, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)
        exit 0
    }
    'Resize' { [void][ElectronRangeWindow]::MoveWindow($Window, 40, 40, 1040, 760, $true) }
    'Msaa' {
        Add-Type -AssemblyName Accessibility
        Add-Type -ReferencedAssemblies Accessibility @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
using Accessibility;
public sealed class MsaaNode {
    public string name;
    public string role;
    public int depth;
}
public static class ElectronRangeMsaa {
    private delegate bool EnumWindow(IntPtr hwnd, IntPtr value);
    [DllImport("user32.dll")] private static extern bool EnumChildWindows(IntPtr hwnd, EnumWindow callback, IntPtr value);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] private static extern int GetClassName(IntPtr hwnd, StringBuilder name, int length);
    [DllImport("oleacc.dll")] private static extern int AccessibleObjectFromWindow(IntPtr hwnd, uint id, ref Guid iid, [MarshalAs(UnmanagedType.Interface)] out IAccessible value);
    [DllImport("oleacc.dll")] private static extern int AccessibleChildren(IAccessible parent, int start, int count, [Out, MarshalAs(UnmanagedType.LPArray, ArraySubType=UnmanagedType.Struct)] object[] children, out int obtained);
    private static void Visit(IAccessible accessible, object child, int depth, List<MsaaNode> nodes) {
        if (depth > 40 || nodes.Count >= 2000) return;
        try { nodes.Add(new MsaaNode { name=accessible.get_accName(child), role=Convert.ToString(accessible.get_accRole(child)), depth=depth }); } catch { return; }
        if (!Equals(child, 0)) return;
        int count;
        try { count=Math.Min(accessible.accChildCount, 2000 - nodes.Count); } catch { return; }
        if (count <= 0) return;
        var values = new object[count];
        int obtained;
        if (AccessibleChildren(accessible, 0, count, values, out obtained) < 0) return;
        for (int i=0; i<obtained; i++) {
            var inner = values[i] as IAccessible;
            if (inner != null) Visit(inner, 0, depth + 1, nodes);
            else if (values[i] is int) Visit(accessible, values[i], depth + 1, nodes);
        }
    }
    public static List<MsaaNode> Read(IntPtr window) {
        var nodes = new List<MsaaNode>();
        EnumChildWindows(window, (hwnd, value) => {
            var name = new StringBuilder(256);
            GetClassName(hwnd, name, name.Capacity);
            if (name.ToString() == "Chrome_RenderWidgetHostHWND") {
                var iid = new Guid("618736e0-3c3d-11cf-810c-00aa00389b71");
                IAccessible accessible;
                if (AccessibleObjectFromWindow(hwnd, 0xfffffffc, ref iid, out accessible) >= 0 && accessible != null) Visit(accessible, 0, 0, nodes);
            }
            return true;
        }, IntPtr.Zero);
        return nodes;
    }
}
'@
        [pscustomobject]@{ title = $RangeProcess.MainWindowTitle; nodes = @([ElectronRangeMsaa]::Read($Window)) } | ConvertTo-Json -Depth 5 -Compress
        exit 0
    }
    'Accessibility' {
        Add-Type -AssemblyName UIAutomationClient
        Add-Type -AssemblyName UIAutomationTypes
        $Root = [System.Windows.Automation.AutomationElement]::FromHandle($Window)
        $Elements = $Root.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Automation]::RawViewCondition)
        $Nodes = @()
        foreach ($Element in $Elements) {
            try {
                $Current = $Element.Current
                $Nodes += [pscustomobject]@{
                    name = $Current.Name
                    type = $Current.ControlType.ProgrammaticName
                    class = $Current.ClassName
                    id = $Current.AutomationId
                    framework = $Current.FrameworkId
                }
            } catch [System.Windows.Automation.ElementNotAvailableException] { }
        }
        [pscustomobject]@{ title = $RangeProcess.MainWindowTitle; nodes = $Nodes } | ConvertTo-Json -Depth 5 -Compress
        exit 0
    }
}
[pscustomobject]@{ title = $RangeProcess.MainWindowTitle } | ConvertTo-Json -Compress
