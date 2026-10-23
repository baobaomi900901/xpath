"""Windows process-level acceptance: usable windows and no CDP listeners.

Uses only the Python standard library. No debugger is enabled by this test.
"""
from __future__ import annotations

import argparse
import ctypes as c
from ctypes import wintypes as w
import json
import msvcrt
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


class PipeProbe:
    """Real Windows CDP pipe transport, including inheritable child handles."""
    def __init__(self, enabled):
        self.enabled = enabled
        self.fds = []
        self.args = []
        self.launch_options = {}
        if enabled:
            child_read, self.parent_write = os.pipe()
            self.parent_read, child_write = os.pipe()
            self.fds = [child_read, self.parent_write, self.parent_read, child_write]
            handles = [msvcrt.get_osfhandle(child_read), msvcrt.get_osfhandle(child_write)]
            for handle in handles:
                os.set_handle_inheritable(handle, True)
            startup = subprocess.STARTUPINFO()
            startup.lpAttributeList = {'handle_list': handles}
            self.launch_options = {'startupinfo': startup, 'close_fds': True}
            self.args = [f'--remote-debugging-io-pipes={handles[0]},{handles[1]}']
            self.kernel = c.WinDLL('kernel32', use_last_error=True)
            self.kernel.PeekNamedPipe.argtypes = [w.HANDLE, c.c_void_p, w.DWORD,
                                                  c.c_void_p, c.POINTER(w.DWORD), c.c_void_p]
            self.kernel.PeekNamedPipe.restype = w.BOOL

    def __enter__(self):
        return self

    def __exit__(self, *_):
        for descriptor in self.fds:
            os.close(descriptor)

    def send(self):
        if self.enabled:
            os.write(self.parent_write, b'{"id":1,"method":"Browser.getVersion"}\0')

    def assert_disabled(self):
        if self.enabled:
            available = w.DWORD()
            if not self.kernel.PeekNamedPipe(msvcrt.get_osfhandle(self.parent_read),
                                             None, 0, None, c.byref(available), None):
                raise c.WinError(c.get_last_error())
            assert not available.value, 'CDP pipe responded to Browser.getVersion'


class Windows:
    def __init__(self):
        self.kernel = c.WinDLL('kernel32', use_last_error=True)
        self.user = c.WinDLL('user32', use_last_error=True)
        self.ip = c.WinDLL('iphlpapi', use_last_error=True)
        self.callback = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
        class Entry(c.Structure):
            _fields_ = [('size', w.DWORD), ('usage', w.DWORD), ('pid', w.DWORD),
                        ('heap', c.c_size_t), ('module', w.DWORD), ('threads', w.DWORD),
                        ('parent', w.DWORD), ('priority', w.LONG), ('flags', w.DWORD),
                        ('name', w.WCHAR * 260)]
        self.Entry = Entry
        for library, name, args, result in [
            (self.kernel, 'CreateToolhelp32Snapshot', [w.DWORD, w.DWORD], w.HANDLE),
            (self.kernel, 'Process32FirstW', [w.HANDLE, c.POINTER(Entry)], w.BOOL),
            (self.kernel, 'Process32NextW', [w.HANDLE, c.POINTER(Entry)], w.BOOL),
            (self.kernel, 'CloseHandle', [w.HANDLE], w.BOOL),
            (self.user, 'EnumWindows', [self.callback, w.LPARAM], w.BOOL),
            (self.user, 'EnumChildWindows', [w.HWND, self.callback, w.LPARAM], w.BOOL),
            (self.user, 'GetWindowThreadProcessId', [w.HWND, c.POINTER(w.DWORD)], w.DWORD),
            (self.user, 'IsWindowVisible', [w.HWND], w.BOOL),
            (self.user, 'GetWindowTextW', [w.HWND, w.LPWSTR, c.c_int], c.c_int),
            (self.user, 'GetClassNameW', [w.HWND, w.LPWSTR, c.c_int], c.c_int),
            (self.user, 'PostMessageW', [w.HWND, w.UINT, w.WPARAM, w.LPARAM], w.BOOL),
            (self.user, 'GetDlgItem', [w.HWND, c.c_int], w.HWND),
            (self.user, 'IsWindowEnabled', [w.HWND], w.BOOL),
            (self.ip, 'GetExtendedTcpTable', [c.c_void_p, c.POINTER(w.DWORD), w.BOOL,
                                            w.ULONG, c.c_int, w.ULONG], w.DWORD),
        ]:
            function = getattr(library, name)
            function.argtypes, function.restype = args, result

    def tree(self, root):
        handle = self.kernel.CreateToolhelp32Snapshot(2, 0)
        if handle == c.c_void_p(-1).value:
            raise c.WinError(c.get_last_error())
        parents = {}
        try:
            entry = self.Entry()
            entry.size = c.sizeof(entry)
            ok = self.kernel.Process32FirstW(handle, c.byref(entry))
            while ok:
                parents[entry.pid] = entry.parent
                ok = self.kernel.Process32NextW(handle, c.byref(entry))
        finally:
            self.kernel.CloseHandle(handle)
        owned = {root}
        while True:
            found = {pid for pid, parent in parents.items() if parent in owned}
            if found <= owned:
                return owned
            owned |= found

    def listeners(self, owned):
        result = []
        for family, row_size, port_offset, pid_offset in [(2, 24, 8, 20), (23, 56, 20, 52)]:
            size = w.DWORD()
            error = self.ip.GetExtendedTcpTable(None, c.byref(size), False, family, 3, 0)
            if error not in (0, 122):
                raise OSError(error, 'GetExtendedTcpTable sizing failed')
            for _ in range(3):
                buffer = c.create_string_buffer(size.value)
                error = self.ip.GetExtendedTcpTable(buffer, c.byref(size), False, family, 3, 0)
                if error != 122:
                    break
            if error:
                raise OSError(error, 'GetExtendedTcpTable failed')
            data = buffer.raw
            for index in range(int.from_bytes(data[:4], 'little')):
                row = data[4 + index * row_size:4 + (index + 1) * row_size]
                pid = int.from_bytes(row[pid_offset:pid_offset + 4], 'little')
                if pid in owned:
                    port = int.from_bytes(row[port_offset:port_offset + 2], 'big')
                    result.append({'pid': pid, 'port': port, 'family': family})
        return result

    def windows(self, owned):
        result = []
        @self.callback
        def visit(hwnd, _):
            pid = w.DWORD()
            self.user.GetWindowThreadProcessId(hwnd, c.byref(pid))
            if pid.value in owned and self.user.IsWindowVisible(hwnd):
                title = c.create_unicode_buffer(1024)
                self.user.GetWindowTextW(hwnd, title, len(title))
                if title.value:
                    result.append((hwnd, title.value))
            return True
        self.user.EnumWindows(visit, 0)
        return result

    def ready(self, hwnd, kind):
        name = c.create_unicode_buffer(256)
        self.user.GetClassNameW(hwnd, name, len(name))
        expected = {'cef': 'XPathCefRange', 'webview2': 'XPathWebView2Range',
                    'electron': 'Chrome_WidgetWin_1'}
        if name.value != expected[kind]:
            return False
        if kind != 'electron':
            refresh = self.user.GetDlgItem(hwnd, 1003)
            if not refresh or not self.user.IsWindowEnabled(refresh):
                return False
        browser = []
        @self.callback
        def child(child_hwnd, _):
            child_class = c.create_unicode_buffer(256)
            self.user.GetClassNameW(child_hwnd, child_class, len(child_class))
            if child_class.value == 'Chrome_RenderWidgetHostHWND' and self.user.IsWindowVisible(child_hwnd):
                browser.append(child_hwnd)
            return True
        self.user.EnumChildWindows(hwnd, child, 0)
        return bool(browser)


def verify(kind, version, scenario):
    executable = (ROOT / 'WEBVIEW2/build/Release/webview2-shooting-range.exe' if kind == 'webview2'
                  else ROOT / kind.upper() / 'dist' / version / f'{kind}-shooting-range-{version}.exe')
    assert executable.is_file(), f'Missing executable: {executable}'
    with socket.socket() as reserve:
        reserve.bind(('127.0.0.1', 0))
        port = reserve.getsockname()[1]
    args = {
        'normal': [], 'port': [f'--remote-debugging-port={port}'],
        'split': ['--remote-debugging-port', str(port)],
        'duplicate': ['--remote-debugging-port=0', f'--remote-debugging-port={port}'],
        'zero': ['--remote-debugging-port=0'], 'pipe': ['--remote-debugging-pipe'],
        'environment': [],
        'nested': [f'--edge-webview-switches=--remote-debugging-port={port}'],
    }[scenario]
    api = Windows()
    profile_root = ROOT / 'WEBVIEW2/verify/artifacts'
    profile_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='xpath-no-cdp-', dir=profile_root,
                                     ignore_cleanup_errors=True) as profile, PipeProbe(scenario == 'pipe') as probe:
        env = dict(os.environ)
        for name in ('ELECTRON_RUN_AS_NODE', 'NODE_OPTIONS', 'WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS',
                     'WEBVIEW2_WAIT_FOR_SCRIPT_DEBUGGER', 'WEBVIEW2_PIPE_FOR_SCRIPT_DEBUGGER'):
            env.pop(name, None)
        env['WEBVIEW2_USER_DATA_FOLDER'] = profile
        if scenario == 'environment':
            env['WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS'] = f'--remote-debugging-port={port}'
        process = subprocess.Popen([str(executable), *args, *probe.args], cwd=executable.parent, env=env,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **probe.launch_options)
        windows = []
        ready_at = None
        try:
            probe.send()
            deadline = time.monotonic() + 35
            while time.monotonic() < deadline:
                assert process.poll() is None, f'Process exited: {process.returncode}'
                owned = api.tree(process.pid)
                listening = api.listeners(owned)
                assert not listening, f'Unexpected listener: {listening}'
                probe.assert_disabled()
                windows = api.windows(owned)
                usable = [(hwnd, title) for hwnd, title in windows if api.ready(hwnd, kind)]
                if usable:
                    ready_at = ready_at or time.monotonic()
                    if time.monotonic() - ready_at >= 2:
                        return {'kind': kind, 'version': version, 'scenario': scenario,
                                'port': port, 'pid': process.pid, 'title': usable[0][1], 'passed': True}
                else:
                    ready_at = None
                time.sleep(0.1)
            raise AssertionError(f'Browser window not ready: {windows}')
        finally:
            for hwnd, _ in windows:
                api.user.PostMessageW(hwnd, 0x10, 0, 0)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Only the process tree created above is eligible for cleanup.
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                process.wait(timeout=5)
            time.sleep(0.3)


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', choices=['cef', 'electron', 'webview2'])
    parser.add_argument('--versions', nargs='+')
    parser.add_argument('--scenarios', nargs='+', default=['normal', 'port', 'split', 'duplicate', 'zero', 'pipe'])
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/no-cdp-results.json')
    args = parser.parse_args()
    results = []
    versions = {'cef': ['109', '125', '128', '133', '154'], 'electron': ['22', '29', '38', '44'], 'webview2': ['Release']}
    for kind in ([args.kind] if args.kind else versions):
        scenarios = list(args.scenarios)
        if kind == 'webview2' and 'normal' in scenarios:
            scenarios += [name for name in ('environment', 'nested') if name not in scenarios]
        for version in args.versions or versions[kind]:
            for scenario in scenarios:
                try:
                    result = verify(kind, version, scenario)
                except Exception as error:
                    result = {'kind': kind, 'version': version, 'scenario': scenario,
                              'passed': False, 'error': str(error)}
                results.append(result)
                print(json.dumps(result, ensure_ascii=False), flush=True)
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    return int(any(not result['passed'] for result in results))


if __name__ == '__main__':
    raise SystemExit(main())
