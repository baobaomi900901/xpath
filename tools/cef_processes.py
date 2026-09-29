"""Stop selected CEF executables by their full Windows image paths."""

from __future__ import annotations

import math
import os
import time
from pathlib import Path


def _canonical_path(path: Path) -> str:
    return os.path.normcase(os.path.realpath(os.path.abspath(str(path))))


def cleanup_cef_processes(executables: list[Path], timeout: float = 10.0) -> list[int]:
    """Force-stop matching browser/worker images and confirm their exit.

    Only exact canonical executable paths are selected. Repeated snapshots catch
    workers created during cleanup; every operation shares the overall timeout.
    Returned PIDs include matching processes that exited naturally during the
    termination race. Importing this module never opens or stops any process.
    """
    if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("CEF 进程清理 timeout 必须是有限的正数。")
    selected = {_canonical_path(path) for path in executables}
    if not selected:
        return []
    selected_names = {os.path.basename(path).casefold() for path in selected}
    deadline = time.monotonic() + timeout
    backend = _create_backend()
    stopped: list[int] = []

    def remaining() -> float:
        duration = deadline - time.monotonic()
        if duration <= 0:
            raise RuntimeError(f"CEF 进程清理超时 ({timeout:g} 秒)；已确认退出 PID: {stopped}。请检查仍在启动的同版本进程。")
        return duration

    while True:
        remaining()
        snapshot = backend.snapshot()
        remaining()
        selected_seen = False
        for pid, basename in snapshot:
            remaining()
            # This is only a query filter. A filename never authorizes a kill.
            if basename.casefold() not in selected_names:
                continue
            query_handle = backend.open(pid)
            if query_handle is None:
                selected_seen = True  # Exit races can leave newly spawned workers.
                continue
            try:
                image = backend.image(query_handle)
                matches = image is not None and _canonical_path(image) in selected
            finally:
                backend.close(query_handle)
            remaining()
            if image is None:
                selected_seen = True
            if not matches:
                continue
            selected_seen = True
            handle = backend.open(pid, terminate=True)
            if handle is None:
                continue
            try:
                # OpenProcess can acquire a reused PID. Verify the newly held
                # object, then use this same HANDLE for termination and waiting.
                image = backend.image(handle)
                if image is None or _canonical_path(image) not in selected:
                    continue
                backend.terminate(handle, remaining())
                if not backend.wait(handle, remaining()):
                    raise RuntimeError(f"等待 CEF PID {pid} 退出超时 ({timeout:g} 秒)；已确认退出 PID: {stopped}。")
                if pid not in stopped:
                    stopped.append(pid)
            except (PermissionError, RuntimeError) as error:
                raise type(error)(f"清理 CEF PID {pid} ({image}) 失败: {error}") from error
            finally:
                backend.close(handle)
        remaining()
        if not selected_seen:
            return stopped


def _create_backend():
    if os.name != "nt":
        raise RuntimeError("CEF 进程清理仅支持 Windows。")
    return _WindowsBackend()


class _WindowsBackend:
    """Thin Win32 seam; all process identity decisions live above it."""

    def __init__(self) -> None:
        import ctypes
        from ctypes import wintypes

        self.ctypes = ctypes
        self.wintypes = wintypes
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        class ProcessEntry(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
                ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", wintypes.LONG),
                ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260),
            ]

        self.ProcessEntry = ProcessEntry
        signatures = {
            "CreateToolhelp32Snapshot": ([wintypes.DWORD, wintypes.DWORD], wintypes.HANDLE),
            "Process32FirstW": ([wintypes.HANDLE, ctypes.POINTER(ProcessEntry)], wintypes.BOOL),
            "Process32NextW": ([wintypes.HANDLE, ctypes.POINTER(ProcessEntry)], wintypes.BOOL),
            "OpenProcess": ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
            "QueryFullProcessImageNameW": ([wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                           ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL),
            "TerminateProcess": ([wintypes.HANDLE, wintypes.UINT], wintypes.BOOL),
            "WaitForSingleObject": ([wintypes.HANDLE, wintypes.DWORD], wintypes.DWORD),
            "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
        }
        for name, (arguments, result) in signatures.items():
            function = getattr(self.kernel32, name)
            function.argtypes = arguments
            function.restype = result

    def _error(self, operation: str, pid: int | None = None, code: int | None = None):
        code = self.ctypes.get_last_error() if code is None else code
        process = f" PID {pid}" if pid is not None else ""
        message = f"{operation}{process} 失败: {self.ctypes.WinError(code)}"
        if code == 5:
            return PermissionError(message + "；请关闭对应程序或使用有权限的终端重试。")
        return RuntimeError(message)

    def snapshot(self) -> list[tuple[int, str]]:
        snapshot = self.kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
        if snapshot == self.ctypes.c_void_p(-1).value or not snapshot:
            raise self._error("创建 Windows 进程快照")
        try:
            entry = self.ProcessEntry()
            entry.dwSize = self.ctypes.sizeof(entry)
            processes: list[tuple[int, str]] = []
            if not self.kernel32.Process32FirstW(snapshot, self.ctypes.byref(entry)):
                error = self.ctypes.get_last_error()
                if error == 18:  # ERROR_NO_MORE_FILES: empty snapshot.
                    return processes
                raise self._error("读取 Windows 进程快照", code=error)
            while True:
                processes.append((entry.th32ProcessID, entry.szExeFile))
                if not self.kernel32.Process32NextW(snapshot, self.ctypes.byref(entry)):
                    error = self.ctypes.get_last_error()
                    if error != 18:
                        raise self._error("遍历 Windows 进程快照", code=error)
                    return processes
        finally:
            self.close(snapshot)

    def open(self, pid: int, terminate: bool = False):
        permissions = 0x1000 | 0x100000  # QUERY_LIMITED_INFORMATION | SYNCHRONIZE.
        if terminate:
            permissions |= 0x0001  # PROCESS_TERMINATE.
        handle = self.kernel32.OpenProcess(permissions, False, pid)
        if not handle:
            error = self.ctypes.get_last_error()
            if error in (87, 1168):  # Process disappeared after the snapshot.
                return None
            raise self._error("打开 CEF 进程", pid, error)
        return handle

    def image(self, handle) -> Path | None:
        buffer = self.ctypes.create_unicode_buffer(32768)
        length = self.wintypes.DWORD(len(buffer))
        if self.kernel32.QueryFullProcessImageNameW(handle, 0, buffer, self.ctypes.byref(length)):
            return Path(buffer.value)
        error = self.ctypes.get_last_error()
        if self.wait(handle, 0):
            return None
        raise self._error("读取 CEF 进程完整映像路径", code=error)

    def terminate(self, handle, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        if self.kernel32.TerminateProcess(handle, 1):
            return True
        error = self.ctypes.get_last_error()
        if self.wait(handle, 0):
            return False
        # Windows also returns ACCESS_DENIED for an object already terminating.
        # Its handle may not be signalled yet. Treat the race as benign only
        # after this exact held object exits, within the caller's shared budget.
        if error == 5 and self.wait(handle, max(0, deadline - time.monotonic())):
            return False
        raise self._error("终止 CEF 进程", code=error)

    def wait(self, handle, timeout: float) -> bool:
        # Round down to keep the entire cleanup within its shared deadline.
        milliseconds = min(int(max(0, timeout) * 1000), 0xFFFFFFFE)
        result = self.kernel32.WaitForSingleObject(handle, milliseconds)
        if result == 0:  # WAIT_OBJECT_0: process exited.
            return True
        if result == 0x00000102:  # WAIT_TIMEOUT.
            return False
        raise self._error("等待 CEF 进程退出")

    def close(self, handle) -> None:
        if not self.kernel32.CloseHandle(handle):
            raise self._error("关闭 Windows 进程句柄")
