"""Launch the packaged EXE or build the native PowerBuilder range from source."""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import json
import locale
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

# Reuse the Win32 launcher's console keys, colors and output configuration.
if __package__:
    from . import start_win32 as console
else:
    import start_win32 as console

RANGE_DIR = Path(__file__).resolve().parents[1] / "POWERBUILDER"
BUILD_DIR = RANGE_DIR / "build" / "Release"
RUNTIME_VERSION = "25.0.0.3683"
EXE_NAME = "PowerBuilderShootingRange.exe"
REQUIRED_DLLS = ("pbvm.dll", "pbacc.dll", "PBAccessibility.dll", "pbdwe.dll")
MODES = ("exe", "dev")
MODE_LABELS = {"exe": "1. 启动 EXE", "dev": "2. 开发模式（从源码编译并启动）"}


def registry_location(key: str) -> str | None:
    if os.name != "nt":
        return None
    import winreg
    for view in (winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key, 0, winreg.KEY_READ | view) as handle:
                return winreg.QueryValueEx(handle, "Location")[0]
        except OSError:
            pass
    return None


def resolve_tools(explicit: Path | None = None) -> Path:
    configured = explicit or os.environ.get("POWERBUILDER_TOOLS")
    if configured:
        candidate = Path(configured).expanduser().resolve()
        compiler = candidate if candidate.suffix.lower() == ".exe" else candidate / "orcascr250.exe"
    else:
        location = registry_location(r"SOFTWARE\Appeon\AutoCompiler\25.0")
        fallback = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Appeon" / "PowerBuilderUtilities 25.0"
        compiler = Path(location or fallback) / "orcascr250.exe"
    if not compiler.is_file():
        raise FileNotFoundError(f"找不到 OrcaScript：{compiler}。请安装 PowerBuilder Utilities 2025 GA，或指定 --tools-path。")
    return compiler


def file_version(path: Path) -> str:
    class FixedFileInfo(ctypes.Structure):
        _fields_ = [(name, wintypes.DWORD) for name in (
            "signature", "struct_version", "file_ms", "file_ls", "product_ms", "product_ls",
            "flags_mask", "flags", "os", "type", "subtype", "date_ms", "date_ls")]
    version = ctypes.WinDLL("version", use_last_error=True)
    version.GetFileVersionInfoSizeW.argtypes = (wintypes.LPCWSTR, ctypes.POINTER(wintypes.DWORD))
    version.GetFileVersionInfoSizeW.restype = wintypes.DWORD
    version.GetFileVersionInfoW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p)
    version.VerQueryValueW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.UINT))
    ignored = wintypes.DWORD()
    size = version.GetFileVersionInfoSizeW(str(path), ctypes.byref(ignored))
    if not size:
        raise RuntimeError(f"无法读取文件版本：{path}")
    buffer = ctypes.create_string_buffer(size)
    if not version.GetFileVersionInfoW(str(path), 0, size, buffer):
        raise ctypes.WinError(ctypes.get_last_error())
    pointer, length = ctypes.c_void_p(), wintypes.UINT()
    if not version.VerQueryValueW(buffer, "\\", ctypes.byref(pointer), ctypes.byref(length)):
        raise RuntimeError(f"无法读取版本资源：{path}")
    info = ctypes.cast(pointer, ctypes.POINTER(FixedFileInfo)).contents
    return ".".join(str(value) for value in (info.file_ms >> 16, info.file_ms & 65535, info.file_ls >> 16, info.file_ls & 65535))


def validate_runtime(runtime: Path, *, version_reader=file_version) -> Path:
    for name in REQUIRED_DLLS:
        if not (runtime / name).is_file():
            raise FileNotFoundError(f"Runtime 缺少 {name}：{runtime}")
    actual = version_reader(runtime / "pbvm.dll")
    if actual != RUNTIME_VERSION:
        raise RuntimeError(f"Runtime 版本不匹配：需要 {RUNTIME_VERSION}，实际 {actual}。")
    return runtime


def resolve_runtime(explicit: Path | None = None) -> Path:
    configured = explicit or os.environ.get("POWERBUILDER_RUNTIME")
    if configured:
        runtime = Path(configured).expanduser().resolve()
    else:
        location = registry_location("SOFTWARE\\Sybase\\PowerBuilder Runtime\\" + RUNTIME_VERSION)
        fallback = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Appeon" / "Common" / "PowerBuilder" / f"Runtime {RUNTIME_VERSION}"
        runtime = Path(location or fallback)
    return validate_runtime(runtime)


def write_runtime_config(output: Path, runtime: Path) -> None:
    # Match the XML emitted by OrcaScript itself; the native loader expects
    # Application/RuntimePath. A different root can silently use the registry.
    root = ET.Element("Application")
    ET.SubElement(root, "RuntimePath").text = str(runtime)
    ET.ElementTree(root).write(output / Path(EXE_NAME).with_suffix(".xml"), encoding="utf-8", xml_declaration=True)
    (output / "pb.ini").write_text("[Application]\nAccessibility=1\n", encoding="utf-8")


def prepare_build(source: Path, output: Path, runtime: Path) -> Path:
    objects = sorted(path for path in source.glob("*.sr*") if path.is_file())
    if not objects:
        raise FileNotFoundError(f"找不到 PowerScript 导出对象：{source}")
    output.mkdir(parents=True, exist_ok=True)
    executable = output / EXE_NAME
    if executable.exists():
        try:
            with executable.open("ab"):
                pass
        except OSError as error:
            raise RuntimeError("靶场 EXE 正在使用，请关闭对应窗口后重新构建。") from error
    # Delete only named build products; never recurse over a user supplied path.
    for name in (EXE_NAME, "pb_range.pbd", "pb_range.pbl"):
        (output / name).unlink(missing_ok=True)
    for path in objects:
        (output / path.name).write_text(path.read_text(encoding="utf-8-sig"), encoding="utf-16")
    (output / "pb_range.pbt").write_text(
        'Save Format v3.0(19990112)\nappname "pb_range";\napplib "pb_range.pbl";\nliblist "pb_range.pbl";\ntype "pb";\n', encoding="utf-8")
    listing = '\n'.join(f'"{path.name}" "pb_range.pbl";' for path in objects)
    (output / "pb_range.pbg").write_text(
        'Save Format v3.0(19990112)\n@begin Libraries\n"pb_range.pbl" "";\n@end;\n@begin Objects\n' + listing + '\n@end;\n', encoding="utf-8")
    script = output / "build.orca"
    script.write_text(
        'start session\n'
        'scc set connect property localprojpath "' + str(output) + '"\n'
        'scc set connect property logfile "' + str(output / "import.log") + '"\n'
        'scc connect offline\n'
        'scc set target "pb_range.pbt" "refresh_all importonly"\n'
        'scc refresh target "3pass"\n'
        'scc close\n'
        'set exeinfo property productname "PowerBuilder Shooting Range"\n'
        'set exeinfo property fileversion "1.0.0.0"\n'
        'build library "pb_range.pbl" "" pbd\n'
        'build executable "' + EXE_NAME + '" "" "" "y" newvstylecontrols\n'
        'end session\n', encoding="utf-16")
    write_runtime_config(output, runtime)
    return script


def run_compiler(compiler: Path, script: Path, output: Path) -> None:
    result = subprocess.run([str(compiler), "/D", f"runtime_version={RUNTIME_VERSION}", str(script)],
                            cwd=output, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    content = result.stdout.decode(locale.getpreferredencoding(False), errors="replace").replace("\r\r\n", "\n").replace("\r\n", "\n")
    (output / "build.log").write_text(content, encoding="utf-8")
    print(content, end="", flush=True)
    if result.returncode != 0:
        raise RuntimeError(f"PowerBuilder 编译失败（{result.returncode}），详见 {output / 'build.log'}")
    for name in (EXE_NAME, "pb_range.pbd"):
        if not (output / name).is_file():
            raise RuntimeError(f"编译器未生成 {name}，详见 {output / 'build.log'}")


def draw_mode_selector(selected: str | None, focused: int, message: str) -> None:
    options = (*MODES, None)
    lines = ["请选择 PowerBuilder 靶场启动方式（单选）:", ""]
    for index, mode in enumerate(options):
        prefix = ">" if index == focused else " "
        if mode is None:
            lines.extend(("", f"{prefix} [ 已完成选择 ]"))
        else:
            marker = "✓" if mode == selected else " "
            option = f"[{marker}] {MODE_LABELS[mode]}"
            lines.append(f"{prefix} {console.green(option) if mode == selected else option}")
    lines.extend(("", "↑/↓ 移动，Enter/空格选择，在“已完成选择”上按 Enter 启动，Esc 取消。", message))
    sys.stdout.write("\x1b[H" + "".join(f"\x1b[2K{line}\n" for line in lines))
    sys.stdout.flush()


def select_mode() -> str | None:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise RuntimeError("交互式选择需要 Windows 终端；请使用 --mode exe 或 --mode dev 指定模式。")
    options = (*MODES, None)
    selected = None
    focused = 0
    message = ""
    console.clear_screen()
    while True:
        draw_mode_selector(selected, focused, message)
        key = console.read_key()
        if key == "up":
            focused = (focused - 1) % len(options)
            message = ""
        elif key == "down":
            focused = (focused + 1) % len(options)
            message = ""
        elif key in ("enter", "space") and options[focused] is not None:
            selected = None if selected == options[focused] else options[focused]
            message = ""
        elif key == "enter":
            if selected is None:
                message = "请选择一种启动方式。"
            else:
                return selected
        elif key == "escape":
            return None
        elif key == "interrupt":
            raise KeyboardInterrupt


def launch_application(executable: Path, *, no_launch: bool, self_test: bool, packaged: bool = False) -> int:
    if no_launch:
        print(f"已验证 PowerBuilder 靶场：{executable}")
        return 0
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = 0 if self_test else 1
    command = [str(executable)]
    if self_test:
        report = executable.parent / ("package-self-test.json" if packaged else "self-test.json")
        report.unlink(missing_ok=True)
        command.append("--self-test")
        if packaged:
            command.extend(["--report", str(report)])
    process = subprocess.Popen(command, cwd=executable.parent, startupinfo=startup)
    if self_test:
        try:
            process.wait(timeout=90 if packaged else 45)
        except subprocess.TimeoutExpired:
            process.terminate()  # Only the self-test process created by this call.
            process.wait(timeout=5)
            raise RuntimeError("PB 自检超时，已关闭本次自检进程。")
        if process.returncode != 0 or not report.is_file():
            raise RuntimeError(f"PB 自检失败：退出码 {process.returncode}，报告 {report}")
        result = json.loads(report.read_text(encoding="utf-8-sig"))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        passed = result.get("passed") is True
        if packaged:
            passed = (result.get("bundled_runtime_verified") is True
                      and result.get("application", {}).get("passed") is True)
        if not passed:
            raise RuntimeError(f"PB 自检未通过：{report}")
    else:
        time.sleep(0.8)
        if process.poll() is not None:
            raise RuntimeError(f"程序启动后立即退出：{process.returncode}")
        print(f"已启动 PowerBuilder 靶场（PID {process.pid}）：{executable}")
    return 0


def main(argv=None) -> int:
    console.configure_output()
    parser = argparse.ArgumentParser(description="启动 PowerBuilder 靶场（Windows 10/11）；无参数时选择 EXE 或开发模式。")
    parser.add_argument("--mode", choices=("exe", "dev"), help="exe：运行单文件包；dev：从源码编译并启动")
    parser.add_argument("--tools-path", type=Path, help="Utilities 目录或 orcascr250.exe 路径")
    parser.add_argument("--runtime-path", type=Path, help=f"Runtime {RUNTIME_VERSION} 目录")
    parser.add_argument("--skip-build", action="store_true", help="运行已有产物，不调用编译器")
    parser.add_argument("--no-launch", action="store_true", help="只构建或检查产物，不创建靶场窗口")
    parser.add_argument("--self-test", action="store_true", help="运行 PB 自检，写入 self-test.json 后自动关闭")
    arguments = list(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(arguments)
    if os.name != "nt":
        raise RuntimeError("PowerBuilder 靶场只能在 Windows 上运行。")
    mode = args.mode or ("dev" if arguments else select_mode())
    if mode is None:
        console.clear_screen()
        print("已取消。")
        return 0
    if mode == "exe":
        if args.skip_build or args.tools_path or args.runtime_path:
            parser.error("--skip-build、--tools-path 和 --runtime-path 仅适用于开发模式。")
        executable = RANGE_DIR / "dist" / "PowerBuilder靶场.exe"
        if not executable.is_file():
            raise FileNotFoundError(f"单文件 EXE 不存在：{executable}。请运行 python .\\tools\\package_powerbuilder.py 打包，或选择开发模式。")
        return launch_application(executable, no_launch=args.no_launch, self_test=args.self_test, packaged=True)
    if not args.skip_build:
        compiler = resolve_tools(args.tools_path)
        if file_version(compiler) != RUNTIME_VERSION:
            raise RuntimeError(f"Utilities 版本须为 {RUNTIME_VERSION}：{compiler}")
        runtime = resolve_runtime(args.runtime_path)
        script = prepare_build(RANGE_DIR / "src", BUILD_DIR, runtime)
        run_compiler(compiler, script, BUILD_DIR)
        write_runtime_config(BUILD_DIR, runtime)
    executable = BUILD_DIR / EXE_NAME
    if not executable.is_file():
        raise FileNotFoundError(f"程序不存在：{executable}。请先构建。")
    for name in ("pb_range.pbd", "pb.ini", "PowerBuilderShootingRange.xml"):
        if not (BUILD_DIR / name).is_file():
            raise FileNotFoundError(f"运行文件缺失：{BUILD_DIR / name}")
    if args.skip_build:
        if args.runtime_path or os.environ.get("POWERBUILDER_RUNTIME"):
            runtime = resolve_runtime(args.runtime_path)
        else:
            config_path = BUILD_DIR / "PowerBuilderShootingRange.xml"
            try:
                runtime_path = ET.parse(config_path).findtext("RuntimePath")
            except ET.ParseError as error:
                raise RuntimeError(f"Runtime 配置无效：{config_path}，可通过 --runtime-path 重新指定。") from error
            if not runtime_path:
                raise RuntimeError(f"Runtime 配置缺少 RuntimePath：{config_path}")
            candidate = Path(runtime_path)
            if not candidate.is_absolute():
                candidate = BUILD_DIR / candidate
            runtime = validate_runtime(candidate.resolve())
        write_runtime_config(BUILD_DIR, runtime)
    return launch_application(executable, no_launch=args.no_launch, self_test=args.self_test)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n已取消。")
        raise SystemExit(130)
    except Exception as error:
        print(f"错误：{error}", file=sys.stderr)
        raise SystemExit(1)
