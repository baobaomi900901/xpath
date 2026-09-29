"""Prepare and launch pinned, official Windows x64 Electron runtimes (Python 3.8+)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path


VERSIONS = ("22", "29", "38", "44")
DEFAULT_BASE_URL = "https://baobaomi900901.github.io/xpath/#/"
REPO_ROOT = Path(__file__).resolve().parents[1]
ELECTRON_ROOT = REPO_ROOT / "ELECTRON"
MANIFEST_PATH = ELECTRON_ROOT / "versions.json"
RUNTIME_FILES = (
    "chrome_100_percent.pak", "chrome_200_percent.pak", "icudtl.dat", "resources.pak",
    "ffmpeg.dll", "v8_context_snapshot.bin", "locales/en-US.pak", "locales/zh-CN.pak",
    "d3dcompiler_47.dll", "vk_swiftshader.dll", "vulkan-1.dll", "vk_swiftshader_icd.json",
)
SOURCE_FILES = ("package.json", "config.cjs", "main.cjs", "preload.cjs", "shell.html", "shell.css", "shell.js")
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
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetStdHandle.argtypes = [wintypes.DWORD]
    kernel.GetStdHandle.restype = wintypes.HANDLE
    kernel.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    handle = kernel.GetStdHandle(-11)
    mode = wintypes.DWORD()
    if not kernel.GetConsoleMode(handle, ctypes.byref(mode)):
        return False
    return bool(kernel.SetConsoleMode(handle, mode.value | 0x0004))


def clear_screen() -> None:
    os.system("cls")


def read_key() -> str:
    import msvcrt

    key = msvcrt.getwch()
    if key in ("\x00", "\xe0"):
        return {"H": "up", "P": "down"}.get(msvcrt.getwch(), "other")
    return {"\r": "enter", " ": "space", "\x1b": "escape", "\x03": "interrupt"}.get(key, "other")


def draw_version_selector(selected: set[str], focused: int, message: str) -> None:
    options: tuple[str | None, ...] = (*VERSIONS, None)
    lines = ["请选择运行版本(可多选):", ""]
    for index, version in enumerate(options):
        prefix = ">" if index == focused else " "
        if version is None:
            lines.extend(("", f"{prefix} [ 已完成选择 ]"))
        else:
            option = f"[✓] Electron {version}" if version in selected else f"[ ] Electron {version}"
            if COLOR_ENABLED and version in selected:
                option = f"\x1b[92m{option}\x1b[0m"
            lines.append(f"{prefix} {option}")
    lines.extend(("↑/↓ 移动，Enter/空格勾选，在“已完成选择”上按 Enter，Esc 取消。", message))
    sys.stdout.write("\x1b[H" + "".join(f"\x1b[2K{line}\n" for line in lines))
    sys.stdout.flush()


def select_versions() -> list[str]:
    if os.name != "nt" or not sys.stdin.isatty() or not sys.stdout.isatty():
        raise RuntimeError("交互式版本选择需要 Windows 终端；请使用 --version 或 --versions 指定版本。")
    selected: set[str] = set()
    focused = 0
    message = ""
    options: tuple[str | None, ...] = (*VERSIONS, None)
    clear_screen()
    while True:
        draw_version_selector(selected, focused, message)
        key = read_key()
        if key == "up":
            focused = (focused - 1) % len(options)
            message = ""
        elif key == "down":
            focused = (focused + 1) % len(options)
            message = ""
        elif key in ("enter", "space") and options[focused] is not None:
            version = options[focused]
            if version in selected:
                selected.remove(version)
            else:
                selected.add(version)
            message = ""
        elif key == "enter":
            if not selected:
                message = "请至少选择一个 Electron 版本。"
            else:
                return normalize_versions(list(selected))
        elif key == "escape":
            return []
        elif key == "interrupt":
            raise KeyboardInterrupt


def normalize_versions(requested: list[str]) -> list[str]:
    requested_set = set(requested)
    return [version for version in VERSIONS if version in requested_set]


def validate_base_url(value: str) -> str:
    try:
        parsed = urllib.parse.urlsplit(value)
        port = parsed.port
        hostname = parsed.hostname or ""
        if re.search(r"%(?![0-9a-fA-F]{2})", hostname):
            raise ValueError("Malformed percent-encoded hostname")
        decoded_hostname = urllib.parse.unquote(hostname, encoding="utf-8", errors="strict")
        valid_hostname = bool(decoded_hostname) and not any(
            character.isspace() or ord(character) < 32 or ord(character) == 127
            or character in '/\\#?@%[]^|<>' for character in decoded_hostname
        ) and (":" not in decoded_hostname or (":" in hostname and "%" not in hostname))
        valid = (
            parsed.scheme in ("http", "https") and valid_hostname
            and parsed.username is None and parsed.password is None
            and "?" not in value and parsed.fragment in ("", "/")
            and ("#" not in value or parsed.fragment == "/")
            and value.endswith("/") and (not parsed.path or parsed.path.endswith("/"))
            and (port is None or 1 <= port <= 65535)
            and "\\" not in value and not any(
                character.isspace() or ord(character) < 32 or ord(character) == 127 for character in value)
        )
    except ValueError:
        valid = False
    if not valid:
        raise argparse.ArgumentTypeError(
            "--base-url 必须是无凭据、无查询参数的绝对 http(s) 地址，"
            "以 / 或 #/ 结尾，例如 http://localhost:7199/。"
        )
    return value


def debugging_port(value: str) -> int:
    if re.fullmatch(r"[0-9]+", value) is None:
        raise argparse.ArgumentTypeError("调试端口必须是 1024..65535 的整数。") from None
    port = int(value)
    if not 1024 <= port <= 65535:
        raise argparse.ArgumentTypeError("调试端口必须位于 1024..65535。")
    return port


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="下载、打包并启动 Windows x64 Electron 多版本靶场。")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--version", choices=VERSIONS, help="跳过菜单并选择一个 Electron 主版本。")
    selection.add_argument("--versions", nargs="+", choices=VERSIONS, help="跳过菜单并选择多个 Electron 主版本。")
    builds = parser.add_mutually_exclusive_group()
    builds.add_argument("--skip-build", action="store_true", help="仅验证现有产物，不下载或打包。")
    builds.add_argument("--force-build", action="store_true", help="从已校验归档重新解压并干净打包。")
    parser.add_argument("--no-launch", action="store_true", help="准备和验证全部产物后退出。")
    parser.add_argument("--base-url", type=validate_base_url, default=DEFAULT_BASE_URL,
                        help="WEB 路由根地址，可使用本地 BrowserRouter 或以 #/ 结尾的 HashRouter。")
    parser.add_argument("--remote-debugging-port", type=debugging_port,
                        help="单版本 loopback 调试端口（1024..65535）。")
    args = parser.parse_args(argv)
    requested = args.versions or ([args.version] if args.version else None)
    args.versions = normalize_versions(requested) if requested else None
    if args.remote_debugging_port is not None and args.versions is not None and len(args.versions) != 1:
        parser.error("--remote-debugging-port 只能与单个版本一起使用。")
    return args


def runtime_info(entry: dict) -> dict:
    return {key: entry[key] for key in ("major", "electron", "chromium", "node")}


def load_manifest(path: Path | None = None) -> dict[str, dict]:
    path = path or MANIFEST_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ValueError(f"Electron 版本清单不是有效 JSON: {path}: {error}") from error
    if not isinstance(data, dict) or set(data) != set(VERSIONS):
        raise ValueError(f"Electron 版本清单必须且只能包含 {', '.join(VERSIONS)}: {path}")
    for major, entry in data.items():
        if not isinstance(entry, dict):
            raise ValueError(f"Electron {major} 清单条目必须为对象。")
        electron = entry.get("electron")
        archive = f"electron-v{electron}-win32-x64.zip"
        url = f"https://github.com/electron/electron/releases/download/v{electron}/{archive}"
        if (
            entry.get("major") != major or not isinstance(electron, str)
            or re.fullmatch(rf"{major}\.\d+\.\d+", electron) is None
            or not isinstance(entry.get("chromium"), str)
            or re.fullmatch(r"\d+\.\d+\.\d+\.\d+", entry["chromium"]) is None
            or not isinstance(entry.get("node"), str)
            or re.fullmatch(r"\d+\.\d+\.\d+", entry["node"]) is None
            or entry.get("archive") != archive or entry.get("url") != url
            or not isinstance(entry.get("sha256"), str)
            or re.fullmatch(r"[0-9a-fA-F]{64}", entry["sha256"]) is None
        ):
            raise ValueError(f"Electron {major} 清单中的版本、官方 Windows x64 URL、文件名或 SHA256 不一致: {path}")
        runtime_files = entry.get("runtime_files")
        if (not isinstance(runtime_files, list) or not runtime_files
                or any(not isinstance(name, str) or not safe_windows_basename(name) for name in runtime_files)
                or len({name.casefold() for name in runtime_files}) != len(runtime_files)):
            raise ValueError(f"Electron {major} runtime_files 必须为非空、无重复的安全 Windows 文件名列表: {path}")
    return data


def require_file(path: Path, context: str) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise FileNotFoundError(f"{context} 缺少非空文件: {path}；请重新准备对应版本。")


def confined_path(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        raise ValueError(f"Electron 文件操作超出预期目录: {path} (根目录 {root})") from None
    return path


def validate_archive(archive: Path, entry: dict) -> None:
    digest = hashlib.sha256()
    with archive.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != entry["sha256"].lower():
        raise ValueError(f"Electron 下载 SHA256 不匹配: {archive}；请删除此归档后重试。")


def download_archive(entry: dict, downloads: Path | None = None) -> Path:
    if downloads is None:
        downloads = confined_path(ELECTRON_ROOT / ".cache" / "downloads", ELECTRON_ROOT)
    downloads.mkdir(parents=True, exist_ok=True)
    archive = confined_path(downloads / entry["archive"], downloads)
    if archive.exists():
        validate_archive(archive, entry)
        return archive
    partial = confined_path(archive.with_name(archive.name + ".part"), downloads)
    received = 0
    print(f"正在下载 Electron {entry['electron']} Windows x64 ...")
    try:
        with urllib.request.urlopen(entry["url"], timeout=60) as response, partial.open("wb") as stream:
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                stream.write(block)
                received += len(block)
                print(f"\r已下载: {received / 1024 / 1024:.1f} MiB", end="", flush=True)
        print()
        validate_archive(partial, entry)
        os.replace(partial, archive)
    finally:
        partial.unlink(missing_ok=True)
    return archive


def safe_windows_basename(name: str) -> bool:
    return bool(
        name and name not in (".", "..") and not name.endswith((".", " "))
        and not any(ord(character) < 32 or character in '/\\:<>"|?*' for character in name)
        and not re.fullmatch(r"(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", name, re.IGNORECASE)
    )


def safe_member_path(member: zipfile.ZipInfo) -> tuple[str, ...]:
    # ZipInfo normalizes Windows separators and truncates NUL; inspect its original name.
    name = member.orig_filename
    components = name.rstrip("/").split("/")
    mode = member.external_attr >> 16
    if (not name or name != member.filename or "\\" in name or any(not safe_windows_basename(part) for part in components)
            or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)):
        raise ValueError(f"Electron 归档包含不安全或非普通文件条目: {name!r}")
    return tuple(components)


def read_json_marker(path: Path, context: str) -> dict:
    require_file(path, context)
    try:
        marker = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ValueError(f"{context} JSON 无效: {path}；请重新准备对应版本。") from error
    if not isinstance(marker, dict):
        raise ValueError(f"{context} 必须为对象: {path}")
    return marker


def validate_runtime_payload(version: str, entry: dict, runtime: Path, executable: str) -> None:
    for relative in (*RUNTIME_FILES, *entry["runtime_files"], executable, "version"):
        confined_path(runtime / relative, runtime)
        require_file(runtime / relative, f"Electron {version} 运行资源")
    if (runtime / "version").read_text(encoding="utf-8").strip() != entry["electron"]:
        raise ValueError(f"Electron {version} 运行时版本与 versions.json 不一致: {runtime / 'version'}")


def validate_runtime(version: str, entry: dict, runtime: Path | None = None) -> Path:
    runtime = runtime or ELECTRON_ROOT / ".cache" / "runtimes" / version
    validate_runtime_payload(version, entry, runtime, "electron.exe")
    for path in runtime.rglob("*"):
        confined_path(path, runtime)
        if path.is_symlink():
            raise ValueError(f"Electron 缓存运行时不允许符号链接: {path}")
    marker = read_json_marker(runtime / "runtime-marker.json", f"Electron {version} 缓存版本标记")
    expected = dict(runtime_info(entry), sha256=entry["sha256"])
    if any(marker.get(key) != value for key, value in expected.items()):
        raise ValueError(f"Electron {version} 缓存标记与 versions.json 不一致: {runtime}")
    return runtime


def replace_directory(staging: Path, target: Path) -> None:
    """Publish validated staging, retaining the old directory if publishing fails."""
    confined_path(staging, target.parent)
    confined_path(target, target.parent)
    backup = target.with_name(target.name + ".previous")
    confined_path(backup, target.parent)
    if backup.exists():
        raise FileExistsError(f"Electron 上次替换备份仍存在，请检查后移走: {backup}")
    had_previous = target.exists()
    if had_previous:
        os.replace(target, backup)
    try:
        for attempt in range(5):
            try:
                os.replace(staging, target)
                break
            except PermissionError:
                if attempt == 4:
                    raise
                time.sleep(0.2 * (attempt + 1))
    except BaseException:
        if had_previous:
            os.replace(backup, target)
        raise
    if had_previous:
        shutil.rmtree(backup)


def extract_runtime(archive: Path, target: Path, version: str, entry: dict) -> Path:
    validate_archive(archive, entry)
    confined_path(target, target.parent)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"{version}-staging-", dir=target.parent) as temporary:
        staging = Path(temporary) / "runtime"
        staging.mkdir()
        with zipfile.ZipFile(archive) as package:
            members = []
            seen = {}
            for member in package.infolist():
                parts = safe_member_path(member)
                normalized = "/".join(parts).casefold()
                if normalized in seen:
                    raise ValueError(f"Electron 归档包含 Windows 重名条目: {member.filename!r}")
                seen[normalized] = member.is_dir()
                members.append((member, parts))
            for normalized, directory in seen.items():
                parts = normalized.split("/")
                for count in range(1, len(parts)):
                    if seen.get("/".join(parts[:count])) is False:
                        raise ValueError(f"Electron 归档文件与目录冲突: {normalized!r}")
            for member, parts in members:
                destination = confined_path(staging.joinpath(*parts), staging)
                if member.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                else:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with package.open(member) as source, destination.open("xb") as output:
                        shutil.copyfileobj(source, output, length=1024 * 1024)
        validate_runtime_payload(version, entry, staging, "electron.exe")
        (staging / "runtime-marker.json").write_text(
            json.dumps(dict(runtime_info(entry), sha256=entry["sha256"]), indent=2) + "\n", encoding="utf-8")
        validate_runtime(version, entry, staging)
        replace_directory(staging, target)
    return target


def ensure_runtime(version: str, entry: dict, force: bool = False) -> Path:
    runtime = confined_path(ELECTRON_ROOT / ".cache" / "runtimes" / version, ELECTRON_ROOT)
    if runtime.exists() and not force:
        return validate_runtime(version, entry, runtime)
    downloads = confined_path(ELECTRON_ROOT / ".cache" / "downloads", ELECTRON_ROOT)
    archive = download_archive(entry, downloads)
    print(f"正在解压 Electron {version} 运行时 ...")
    return extract_runtime(archive, runtime, version, entry)


def validate_source(source: Path) -> None:
    for relative in SOURCE_FILES:
        confined_path(source / relative, source)
        require_file(source / relative, "Electron 宿主源码")
    package = read_json_marker(source / "package.json", "Electron 应用包")
    if package.get("main") != "main.cjs":
        raise ValueError(f"Electron package.json 的 main 必须为 main.cjs: {source}")
    for path in source.rglob("*"):
        confined_path(path, source)
        if path.is_symlink():
            raise ValueError(f"Electron 宿主源码不允许符号链接: {path}")


def artifact_path(version: str) -> Path:
    return ELECTRON_ROOT / "dist" / version / f"electron-shooting-range-{version}.exe"


def validate_artifact(version: str, entry: dict | None = None, dist: Path | None = None) -> Path:
    entry = entry or load_manifest()[version]
    dist = dist or confined_path(ELECTRON_ROOT / "dist" / version, ELECTRON_ROOT)
    executable = dist / f"electron-shooting-range-{version}.exe"
    validate_runtime_payload(version, entry, dist, executable.name)
    app = dist / "resources" / "app"
    confined_path(app, dist)
    validate_source(app)
    for marker in (dist / "version.json", app / "runtime.json"):
        actual = read_json_marker(marker, f"Electron {version} 产物版本标记")
        if any(actual.get(key) != value for key, value in runtime_info(entry).items()):
            raise ValueError(f"Electron {version} 产物版本与 versions.json 不一致: {marker}；请重新打包。")
    return executable


def build_version(version: str, entry: dict, force: bool = False) -> Path:
    source = confined_path(ELECTRON_ROOT / "src", ELECTRON_ROOT)
    validate_source(source)
    target = confined_path(ELECTRON_ROOT / "dist" / version, ELECTRON_ROOT)
    runtime = ensure_runtime(version, entry, force)
    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"正在打包 Electron {version} 靶场 ...")
    with tempfile.TemporaryDirectory(prefix=f"{version}-staging-", dir=target.parent) as temporary:
        staging = Path(temporary) / "app"
        shutil.copytree(runtime, staging)
        (staging / "electron.exe").rename(staging / f"electron-shooting-range-{version}.exe")
        app = staging / "resources" / "app"
        if app.exists():
            confined_path(app, staging)
            shutil.rmtree(app)
        shutil.copytree(source, app)
        info = json.dumps(runtime_info(entry), indent=2) + "\n"
        (app / "runtime.json").write_text(info, encoding="utf-8")
        (staging / "version.json").write_text(info, encoding="utf-8")
        validate_artifact(version, entry, staging)
        replace_directory(staging, target)
    executable = validate_artifact(version, entry)
    print(f"打包完成: {executable}")
    return executable


def launch_versions(versions: list[str], executables: dict[str, Path], base_url: str, port: int | None) -> None:
    launched: list[tuple[str, subprocess.Popen]] = []
    environment = {key: value for key, value in os.environ.items() if key.upper() != "ELECTRON_RUN_AS_NODE"}
    try:
        for version in versions:
            executable = executables[version]
            command = [str(executable), f"--base-url={base_url}"]
            if port is not None:
                command.extend((f"--remote-debugging-port={port}", "--remote-debugging-address=127.0.0.1"))
            process = subprocess.Popen(command, cwd=executable.parent, close_fds=True, env=environment)
            launched.append((version, process))
            time.sleep(0.2)
            if process.poll() is not None:
                raise RuntimeError(f"Electron {version} 启动后立即退出，退出码 {process.returncode}。")
            print(f"已启动 Electron {version} 靶场 (PID {process.pid})。")
    except Exception as error:
        processes = ", ".join(f"Electron {version}: PID {process.pid}" for version, process in launched) or "无"
        raise RuntimeError(f"Electron 启动失败: {error}；已经启动的进程: {processes}。请检查这些进程的窗口或错误日志。") from error


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    versions = args.versions if args.versions is not None else select_versions()
    if not versions:
        print("已取消。")
        return 0
    if args.remote_debugging_port is not None and len(versions) != 1:
        raise ValueError("--remote-debugging-port 只能与单个版本一起使用。")
    manifest = load_manifest()
    executables = {}
    for version in versions:
        entry = manifest[version]
        executables[version] = (validate_artifact(version, entry) if args.skip_build
                                else build_version(version, entry, args.force_build))
    if not args.no_launch:
        launch_versions(versions, executables, args.base_url, args.remote_debugging_port)
    return 0


if __name__ == "__main__":
    configure_output()
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n已取消。", file=sys.stderr)
        raise SystemExit(130)
    except Exception as error:
        print(f"错误: {error}", file=sys.stderr)
        raise SystemExit(1)
