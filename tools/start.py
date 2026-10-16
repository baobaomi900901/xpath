"""Open the configurable desktop launcher using only Python's standard library."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__:
    from .range_launcher.config import build_command, default_values, load_catalog
else:
    from range_launcher.config import build_command, default_values, load_catalog

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="可视化靶场启动中心（Python 标准库 / Tk）。")
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("ranges.json"))
    checks = parser.add_mutually_exclusive_group()
    checks.add_argument("--check", action="store_true", help="校验配置和默认启动命令，不创建窗口或启动靶场")
    checks.add_argument("--self-test", action="store_true", help="检查隐藏界面的动态选项，不启动任何靶场")
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
