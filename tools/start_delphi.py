from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


DELPHI_ROOT = Path(__file__).resolve().parents[1] / "DELPHI"


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="构建并启动 Delphi VCL GUI 自动化靶场。")
    parser.add_argument("--configuration", choices=("Debug", "Release"), default="Release")
    parser.add_argument("--compiler-path", help="dcc32.exe 完整路径；默认优先使用 Delphi 2010。")
    parser.add_argument("--devexpress-trial-library", default=os.environ.get("DELPHI_DEVEXPRESS_TRIAL_LIBRARY"),
                        help="Delphi 11 DevExpress 试用版 Library/RS28 目录，仅用于本机评估。")
    parser.add_argument("--skip-build", action="store_true", help="使用已有 EXE，无需 Delphi 编译器。")
    parser.add_argument("--no-launch", action="store_true", help="仅构建或检查产物，不打开窗口。")
    args = parser.parse_args()
    if args.devexpress_trial_library:
        args.devexpress_trial_library = str(Path(args.devexpress_trial_library).expanduser().resolve())
    if os.name != "nt":
        raise RuntimeError("Delphi VCL 靶场只能在 Windows 上运行。")
    if not args.skip_build:
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        if not powershell:
            raise FileNotFoundError("找不到 PowerShell，无法构建。")
        command = [
            powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
            str(DELPHI_ROOT / "build.ps1"), "-Configuration", args.configuration,
        ]
        if args.compiler_path:
            command.extend(["-CompilerPath", args.compiler_path])
        if args.devexpress_trial_library:
            command.extend(["-DevExpressTrialLibrary", args.devexpress_trial_library])
        subprocess.run(command, cwd=DELPHI_ROOT, check=True)
    executable = DELPHI_ROOT / "build" / args.configuration / "Win32VclShootingRange.exe"
    if args.devexpress_trial_library:
        executable = DELPHI_ROOT / "build" / "DevExpressTrial" / args.configuration / "Win32VclShootingRange.exe"
    if not executable.is_file():
        raise FileNotFoundError(f"程序不存在：{executable}。请先构建。")
    if args.no_launch:
        print(f"已验证 Delphi VCL 靶场：{executable}")
        return 0
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 1  # SW_SHOWNORMAL, including from a hidden host terminal.
    process = subprocess.Popen(
        [str(executable)], cwd=executable.parent, close_fds=True, startupinfo=startupinfo,
    )
    time.sleep(0.8)
    if process.poll() is not None:
        raise RuntimeError(f"程序启动后立即退出，退出码 {process.returncode}。")
    print(f"已启动 Delphi VCL 靶场（PID {process.pid}）：{executable}")
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
