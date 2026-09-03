from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WIN32_ROOT = REPO_ROOT / "WIN32"
BUILD_SCRIPT = WIN32_ROOT / "build.ps1"
BACKENDS = ("uia", "msaa", "canvas")
BACKEND_LABELS = {
    "uia": "UIA 版（标准 Win32 控件）",
    "msaa": "MSAA 版（仅 IAccessible）",
    "canvas": "自绘版（无内部无障碍树）",
}
COLOR_ENABLED = False


def configure_output() -> None:
    global COLOR_ENABLED
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    COLOR_ENABLED = enable_virtual_terminal()


def enable_virtual_terminal() -> bool:
    if os.name != "nt" or not sys.stdout.isatty():
        return False

    import ctypes

    stdout_handle = ctypes.windll.kernel32.GetStdHandle(-11)
    mode = ctypes.c_ulong()
    if not ctypes.windll.kernel32.GetConsoleMode(stdout_handle, ctypes.byref(mode)):
        return False
    return bool(ctypes.windll.kernel32.SetConsoleMode(stdout_handle, mode.value | 0x0004))


def green(text: str) -> str:
    if not COLOR_ENABLED:
        return text
    return f"\x1b[92m{text}\x1b[0m"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="构建并启动 Win32 靶场。")
    parser.add_argument(
        "--configuration",
        choices=("Debug", "Release"),
        default="Release",
        help="构建配置，默认为 Release。",
    )
    parser.add_argument(
        "--backends",
        nargs="+",
        choices=BACKENDS,
        help="跳过菜单并指定一个或多个运行版本。",
    )
    parser.add_argument("--skip-build", action="store_true", help="跳过构建，直接使用现有 EXE。")
    parser.add_argument("--no-launch", action="store_true", help="仅验证构建产物，不启动程序。")
    return parser.parse_args()


def clear_screen() -> None:
    os.system("cls")


def read_key() -> str:
    if os.name != "nt":
        raise RuntimeError("交互式版本选择目前仅支持 Windows。")

    import msvcrt

    key = msvcrt.getwch()
    if key in ("\x00", "\xe0"):
        extended = msvcrt.getwch()
        return {"H": "up", "P": "down"}.get(extended, "other")
    return {
        "\r": "enter",
        " ": "space",
        "\x1b": "escape",
        "\x03": "interrupt",
    }.get(key, "other")


def draw_backend_selector(selected: set[str], focused: int, message: str) -> None:
    options: tuple[str | None, ...] = (*BACKENDS, None)
    lines = ["请选择运行版本（可多选）:", ""]

    for index, backend in enumerate(options):
        prefix = ">" if index == focused else " "
        if backend is None:
            lines.extend(("", f"{prefix} [ 已完成选择 ]"))
        else:
            marker = "✓" if backend in selected else " "
            option = f"[{marker}] {BACKEND_LABELS[backend]}"
            lines.append(f"{prefix} {green(option) if backend in selected else option}")

    lines.append(message)
    frame = "\x1b[H" + "".join(f"\x1b[2K{line}\n" for line in lines)
    sys.stdout.write(frame)
    sys.stdout.flush()


def select_backends() -> list[str]:
    selected: set[str] = set()
    focused = 0
    message = ""
    options: tuple[str | None, ...] = (*BACKENDS, None)

    clear_screen()
    while True:
        draw_backend_selector(selected, focused, message)
        key = read_key()
        if key == "up":
            focused = (focused - 1) % len(options)
            message = ""
        elif key == "down":
            focused = (focused + 1) % len(options)
            message = ""
        elif key in ("enter", "space") and options[focused] is not None:
            backend = options[focused]
            if backend in selected:
                selected.remove(backend)
            else:
                selected.add(backend)
            message = ""
        elif key == "enter":
            if not selected:
                message = "请至少选择一个版本。"
            else:
                return [backend for backend in BACKENDS if backend in selected]
        elif key == "escape":
            return []
        elif key == "interrupt":
            raise KeyboardInterrupt


def normalize_backends(requested: list[str]) -> list[str]:
    requested_set = set(requested)
    return [backend for backend in BACKENDS if backend in requested_set]


def find_powershell() -> str:
    for command in ("pwsh", "powershell"):
        executable = shutil.which(command)
        if executable:
            return executable
    raise FileNotFoundError("找不到 pwsh 或 powershell，无法执行 Win32 构建脚本。")


def executable_path(configuration: str, backend: str) -> Path:
    return WIN32_ROOT / "build" / configuration / f"win32-shooting-range-{backend}.exe"


def build(configuration: str) -> None:
    if not BUILD_SCRIPT.exists():
        raise FileNotFoundError(f"Win32 构建脚本不存在: {BUILD_SCRIPT}")

    powershell = find_powershell()
    print(f"正在构建 Win32 靶场 ({configuration}) ...")
    completed = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(BUILD_SCRIPT),
            "-Configuration",
            configuration,
        ],
        cwd=WIN32_ROOT,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"Win32 构建失败，退出码 {completed.returncode}。")


def validate_artifact(configuration: str, backend: str) -> Path:
    executable = executable_path(configuration, backend)
    if not executable.is_file():
        raise FileNotFoundError(f"Win32 程序不存在: {executable}")
    return executable


def launch_backends(backends: list[str], executables: dict[str, Path]) -> None:
    processes: list[tuple[str, subprocess.Popen[bytes]]] = []
    try:
        for backend in backends:
            process = subprocess.Popen([str(executables[backend])], cwd=WIN32_ROOT, close_fds=True)
            processes.append((backend, process))

        time.sleep(0.7)
        for backend, process in processes:
            if process.poll() is not None:
                raise RuntimeError(
                    f"Win32 靶场 {backend.upper()} 版启动后立即退出，退出码 {process.returncode}。"
                )
            print(f"已启动 Win32 靶场 {backend.upper()} 版 (PID {process.pid})。")
    except Exception:
        for _, process in processes:
            if process.poll() is None:
                process.terminate()
        raise


def main() -> int:
    configure_output()
    if os.name != "nt":
        raise RuntimeError("Win32 靶场只能在 Windows 上运行。")

    args = parse_args()
    backends = normalize_backends(args.backends) if args.backends else select_backends()
    if not backends:
        clear_screen()
        print("已取消。")
        return 0

    if not args.skip_build:
        build(args.configuration)

    executables = {
        backend: validate_artifact(args.configuration, backend)
        for backend in backends
    }
    if args.no_launch:
        for backend in backends:
            print(f"已验证 Win32 靶场 {backend.upper()} 版: {executables[backend]}")
        return 0

    launch_backends(backends, executables)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n已取消。")
        raise SystemExit(130)
    except Exception as error:
        print(f"错误: {error}", file=sys.stderr)
        raise SystemExit(1)
