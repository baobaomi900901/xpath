from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


REPO_ROOT = Path(__file__).resolve().parents[1]
WEBVIEW2_ROOT = REPO_ROOT / "WEBVIEW2"


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="构建并启动 WebView2 浏览器套壳靶场。")
    parser.add_argument("--configuration", choices=("Debug", "Release"), default="Release")
    parser.add_argument("--no-launch", action="store_true", help="仅构建并验证产物，不打开窗口。")
    args = parser.parse_args()
    if os.name != "nt":
        raise RuntimeError("WebView2 靶场只能在 Windows 上运行。")
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if not powershell:
        raise FileNotFoundError("找不到 PowerShell，无法构建。")
    subprocess.run([
        powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
        str(WEBVIEW2_ROOT / "build.ps1"), "-Configuration", args.configuration,
    ], cwd=WEBVIEW2_ROOT, check=True)
    executable = WEBVIEW2_ROOT / "build" / args.configuration / "webview2-shooting-range.exe"
    if not executable.is_file():
        raise FileNotFoundError(f"程序不存在：{executable}。请先构建。")
    if args.no_launch:
        print(f"已验证 WebView2 靶场：{executable}")
        return 0
    process = subprocess.Popen([str(executable)], cwd=executable.parent, close_fds=True)
    time.sleep(0.7)
    if process.poll() is not None:
        raise RuntimeError(f"程序启动后立即退出，退出码 {process.returncode}。")
    print(f"已启动 WebView2 浏览器靶场（PID {process.pid}）。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n已取消。", file=sys.stderr)
        raise SystemExit(130)
    except Exception as error:
        print(f"错误：{error}", file=sys.stderr)
        raise SystemExit(1)
