"""Open the configurable desktop launcher using only Python's standard library."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

if __package__:
    from .range_launcher.config import build_command, default_values, load_catalog
else:
    from range_launcher.config import build_command, default_values, load_catalog

ROOT = Path(__file__).resolve().parents[1]


def launch_background(config):
    """Keep the GUI and its output independent of the invoking terminal."""
    log_dir = ROOT / ".private" / "range-launcher" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = log_dir / "launcher-{}-{}.log".format(stamp, uuid4().hex[:8])
    command = [sys.executable, str(Path(__file__).resolve()), "--foreground", "--config", str(config)]
    options = {"creationflags": subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    with log_path.open("wb") as output:
        process = subprocess.Popen(
            command, cwd=str(ROOT), stdin=subprocess.DEVNULL,
            stdout=output, stderr=subprocess.STDOUT, close_fds=True, **options,
        )
    try:
        exit_code = process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        print("已后台启动靶场启动中心（PID {}），终端可继续使用。".format(process.pid))
        print("启动日志：{}".format(log_path))
        return 0
    print("启动中心提前退出（退出码 {}）。日志：{}；可使用 --foreground 查看错误。".format(exit_code, log_path), file=sys.stderr)
    return 1


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="可视化靶场启动中心（Python 标准库 / Tk）。")
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("ranges.json"))
    checks = parser.add_mutually_exclusive_group()
    checks.add_argument("--check", action="store_true", help="校验配置和默认启动命令，不创建窗口或启动靶场")
    checks.add_argument("--self-test", action="store_true", help="检查隐藏界面的动态选项，不启动任何靶场")
    checks.add_argument("--foreground", action="store_true", help="前台运行以查看调试输出，关闭窗口后归还终端")
    args = parser.parse_args(argv)
    config = args.config.expanduser().resolve()
    if args.check:
        catalog = load_catalog(config)
        commands = []
        for item in catalog["ranges"]:
            command, cwd = build_command(item, item["default_profile"], default_values(item), ROOT)
            commands.append({"id": item["id"], "command": command, "cwd": str(cwd)})
        print(json.dumps({"passed": True, "ranges": len(commands), "commands": commands}, ensure_ascii=False, indent=2))
        return 0
    if not args.foreground and not args.self_test:
        return launch_background(config)
    try:
        import tkinter as tk
        if __package__:
            from .range_launcher.app import Launcher
        else:
            from range_launcher.app import Launcher
    except ImportError as error:
        raise RuntimeError("当前 Python 缺少 Tk；请使用包含 Tcl/Tk 的 Python 运行此启动器。") from error
    root = tk.Tk()
    if args.self_test:
        root.withdraw()
        try:
            application = Launcher(root, ROOT, config)
            print(json.dumps(application.check_ui(), ensure_ascii=False, indent=2))
        finally:
            root.destroy()
        return 0
    Launcher(root, ROOT, config, ROOT / ".private" / "range-launcher" / "state.json")
    root.mainloop()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
    except Exception as error:
        print(f"启动中心错误：{error}", file=sys.stderr)
        raise SystemExit(1)
