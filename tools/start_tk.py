"""Launch the Tk range using this interpreter; no third party dependencies."""

import argparse
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parent.parent


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="启动 tkinter/ttk 桌面靶场（仅需 Python 标准库）。")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--no-launch", action="store_true", help="创建并销毁隐藏窗口，检查 Tk 环境与全部测试页")
    mode.add_argument("--foreground", action="store_true", help="前台运行，关闭窗口后返回退出码")
    args = parser.parse_args(argv)
    command = [sys.executable, "-m", "TK"]
    try:
        checked = subprocess.run(command + ["--check"], cwd=REPO_ROOT)
        if checked.returncode or args.no_launch:
            return checked.returncode
        if args.foreground:
            return subprocess.run(command, cwd=REPO_ROOT).returncode

        process = subprocess.Popen(
            command, cwd=REPO_ROOT, close_fds=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        try:
            exit_code = process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            print("已启动 Tk 靶场 (PID {})。".format(process.pid))
            return 0
        print("错误: Tk 靶场启动后立即退出（退出码 {}）。可使用 --foreground 查看错误。".format(exit_code), file=sys.stderr)
        return 1
    except OSError as error:
        print("错误: 无法运行 Tk 靶场: {}".format(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n已取消。")
        raise SystemExit(130)
