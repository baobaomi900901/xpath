import sys


for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")


try:
    from .app import main
except ImportError as error:
    print("错误: 无法加载 tkinter/ttk: {}。请使用包含 Tcl/Tk 的 Python 安装，并勾选 tcl/tk and IDLE。".format(error),
          file=sys.stderr)
    raise SystemExit(1)


if __name__ == "__main__":
    import tkinter as tk

    try:
        raise SystemExit(main())
    except tk.TclError as error:
        print("错误: Tcl/Tk 初始化或窗口操作失败: {}".format(error), file=sys.stderr)
        raise SystemExit(1)
