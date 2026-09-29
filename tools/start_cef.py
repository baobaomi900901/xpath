from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath


VERSIONS = ("109", "125", "128", "133", "154")
DEFAULT_BASE_URL = "https://baobaomi900901.github.io/xpath/#/"
REPO_ROOT = Path(__file__).resolve().parents[1]
CEF_ROOT = REPO_ROOT / "CEF"
MANIFEST_PATH = CEF_ROOT / "versions.json"
DOWNLOAD_BASE_URL = "https://cef-builds.spotifycdn.com/"
RUNTIME_FILES = (
    "libcef.dll", "chrome_elf.dll", "icudtl.dat", "resources.pak",
    "chrome_100_percent.pak", "chrome_200_percent.pak",
)
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
            option = f"[✓] CEF {version}" if version in selected else f"[ ] CEF {version}"
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
                message = "请至少选择一个 CEF 版本。"
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
        valid = (
            parsed.scheme in ("http", "https") and bool(parsed.hostname)
            and parsed.username is None and parsed.password is None
            and "?" not in value and parsed.fragment in ("", "/")
            and ("#" not in value or parsed.fragment == "/")
            and (not parsed.path or parsed.path.endswith("/"))
            and (port is None or 1 <= port <= 65535)
            and "\\" not in value and not any(character.isspace() or ord(character) < 32 for character in value)
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
    try:
        port = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("调试端口必须是 1024..65535 的整数。") from None
    if not 1024 <= port <= 65535:
        raise argparse.ArgumentTypeError("调试端口必须位于 1024..65535。")
    return port


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="下载、构建并启动 Windows x64 CEF 多版本靶场。")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--version", choices=VERSIONS, help="跳过菜单并选择一个 CEF 主版本。")
    selection.add_argument("--versions", nargs="+", choices=VERSIONS, help="跳过菜单并选择多个 CEF 主版本。")
    builds = parser.add_mutually_exclusive_group()
    builds.add_argument("--skip-build", action="store_true", help="仅验证现有产物，不下载或构建。")
    builds.add_argument("--force-build", action="store_true", help="重新配置并执行干净的 Release 构建。")
    parser.add_argument("--no-launch", action="store_true", help="准备和验证全部产物后退出。")
    parser.add_argument("--base-url", type=validate_base_url, default=DEFAULT_BASE_URL,
                        help="WEB 路由根地址，可使用本地 BrowserRouter 或以 #/ 结尾的 HashRouter。")
    parser.add_argument("--remote-debugging-port", type=debugging_port,
                        help="单版本调试端口（1024..65535）。")
    args = parser.parse_args(argv)
    requested = args.versions or ([args.version] if args.version else None)
    args.versions = normalize_versions(requested) if requested else None
    if args.remote_debugging_port is not None and args.versions is not None and len(args.versions) != 1:
        parser.error("--remote-debugging-port 只能与单个版本一起使用。")
    return args


def load_manifest(path: Path | None = None) -> dict[str, dict]:
    path = path or MANIFEST_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ValueError(f"CEF 版本清单不是有效 JSON: {path}: {error}") from error
    if not isinstance(data, dict) or set(data) != set(VERSIONS):
        raise ValueError(f"CEF 版本清单必须且只能包含 {', '.join(VERSIONS)}: {path}")
    for major, entry in data.items():
        if not isinstance(entry, dict):
            raise ValueError(f"CEF {major} 清单条目必须为对象。")
        cef_version = entry.get("cef_version")
        chromium_version = entry.get("chromium_version")
        if (
            not isinstance(cef_version, str)
            or re.fullmatch(rf"{major}\.\d+\.\d+\+g[0-9a-f]+\+chromium-{major}\.\d+\.\d+\.\d+", cef_version) is None
            or not isinstance(chromium_version, str)
            or cef_version.split("+chromium-")[-1] != chromium_version
            or entry.get("archive") != f"cef_binary_{cef_version}_windows64_minimal.tar.bz2"
            or not isinstance(entry.get("sha1"), str)
            or re.fullmatch(r"[0-9a-fA-F]{40}", entry["sha1"]) is None
            or type(entry.get("size")) is not int or entry["size"] <= 0
        ):
            raise ValueError(f"CEF {major} 清单中的版本、Windows x64 文件名、SHA1 或大小不一致: {path}")
        runtime_files = entry.get("runtime_files")
        if (
            not isinstance(runtime_files, list) or not runtime_files
            or any(not isinstance(name, str) or not safe_windows_basename(name) for name in runtime_files)
            or len({name.casefold() for name in runtime_files}) != len(runtime_files)
        ):
            raise ValueError(f"CEF {major} 清单 runtime_files 必须为非空、无重复的安全 Windows 文件名列表: {path}")
    return data


def safe_windows_basename(name: str) -> bool:
    return bool(
        name and not name.endswith((".", " "))
        and not any(ord(character) < 32 or character in '/\\:<>"|?*' for character in name)
        and not re.fullmatch(r"(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", name, re.IGNORECASE)
    )


def require_file(path: Path, context: str) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise FileNotFoundError(f"{context} 缺少非空文件: {path}；请重新准备 SDK 或构建对应版本。")


def validate_sdk(version: str, entry: dict, sdk: Path | None = None) -> Path:
    sdk = sdk or CEF_ROOT / ".cache" / "sdk" / version
    header_path = sdk / "include" / "cef_version.h"
    for relative in ("include/cef_version.h", "Release/libcef.dll", "Release/libcef.lib", "libcef_dll/CMakeLists.txt"):
        require_file(sdk / relative, f"CEF {version} SDK")
    if not (sdk / "Resources").is_dir():
        raise FileNotFoundError(f"CEF {version} SDK 缺少 Resources 目录: {sdk}")
    header = header_path.read_text(encoding="utf-8")
    expected = {
        "CEF_VERSION": f'"{entry["cef_version"]}"', "CEF_VERSION_MAJOR": version,
    }
    for macro, value in zip(("MAJOR", "MINOR", "BUILD", "PATCH"), entry["chromium_version"].split(".")):
        expected[f"CHROME_VERSION_{macro}"] = value
    for name, value in expected.items():
        values = re.findall(rf"^\s*#\s*define\s+{name}\s+([^\r\n]+)", header, re.MULTILINE)
        if len(values) != 1 or values[0].strip() != value:
            raise ValueError(f"CEF {version} SDK 的 {name} 与清单不一致: {header_path}；请移走此 SDK 后重试。")
    return sdk


def validate_archive(archive: Path, entry: dict) -> None:
    if archive.stat().st_size != entry["size"]:
        raise ValueError(f"CEF 下载大小不匹配: {archive}；期望 {entry['size']} 字节。")
    digest = hashlib.sha1()
    with archive.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != entry["sha1"].lower():
        raise ValueError(f"CEF 下载 SHA1 不匹配: {archive}；请删除此归档后重试。")


def download_archive(entry: dict, downloads: Path | None = None) -> Path:
    downloads = downloads or CEF_ROOT / ".cache" / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    archive = downloads / entry["archive"]
    if archive.exists():
        validate_archive(archive, entry)
        return archive
    partial = archive.with_name(archive.name + ".part")
    url = DOWNLOAD_BASE_URL + urllib.parse.quote(entry["archive"], safe="")
    received = 0
    last_progress = -1
    print(f"正在下载 CEF {entry['cef_version']} ({entry['size'] / 1024 / 1024:.1f} MiB) ...")
    try:
        with urllib.request.urlopen(url, timeout=60) as response, partial.open("wb") as stream:
            while block := response.read(1024 * 1024):
                received += len(block)
                if received > entry["size"]:
                    raise ValueError(f"CEF 下载超过清单中的大小: {url}")
                stream.write(block)
                progress = received * 100 // entry["size"]
                if progress != last_progress:
                    print(f"\r下载进度: {progress:3d}% ({received / 1024 / 1024:.1f} MiB)", end="", flush=True)
                    last_progress = progress
        print()
        validate_archive(partial, entry)
        os.replace(partial, archive)
    finally:
        partial.unlink(missing_ok=True)
    return archive


def safe_member_path(member: tarfile.TarInfo, expected_root: str) -> tuple[str, ...]:
    name = member.name
    path = PurePosixPath(name)
    if (
        not name or "\\" in name or path.is_absolute() or ".." in path.parts
        or not path.parts or path.parts[0] != expected_root
        or not (member.isdir() or member.isfile())
    ):
        raise ValueError(f"CEF 归档包含不安全或非预期条目: {name!r}")
    for component in path.parts:
        if not safe_windows_basename(component):
            raise ValueError(f"CEF 归档包含不安全的 Windows 文件名: {name!r}")
    if len(path.parts) == 1 and not member.isdir():
        raise ValueError(f"CEF 归档根条目必须是目录: {name!r}")
    return path.parts[1:]


def extract_sdk(archive: Path, target: Path, version: str, entry: dict) -> Path:
    if target.exists():
        return validate_sdk(version, entry, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    expected_root = entry["archive"][:-len(".tar.bz2")]
    with tempfile.TemporaryDirectory(prefix=f"{version}-staging-", dir=target.parent) as temporary:
        staging = Path(temporary) / "sdk"
        staging.mkdir()
        with tarfile.open(archive, "r:bz2") as package:
            members: list[tuple[tarfile.TarInfo, tuple[str, ...]]] = []
            seen: set[str] = set()
            for member in package:
                relative = safe_member_path(member, expected_root)
                if not relative:
                    continue
                normalized = "/".join(relative).casefold()
                if normalized in seen:
                    raise ValueError(f"CEF 归档包含重名条目: {member.name!r}")
                seen.add(normalized)
                members.append((member, relative))
            for member, relative in members:
                destination = staging.joinpath(*relative)
                if member.isdir():
                    destination.mkdir(parents=True, exist_ok=True)
                else:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with package.extractfile(member) as source, destination.open("xb") as output:
                        shutil.copyfileobj(source, output, length=1024 * 1024)
        validate_sdk(version, entry, staging)
        for attempt in range(5):
            try:
                os.replace(staging, target)
                break
            except PermissionError:
                if attempt == 4:
                    raise
                time.sleep(0.2 * (attempt + 1))
    return target


def ensure_sdk(version: str, entry: dict) -> Path:
    sdk = CEF_ROOT / ".cache" / "sdk" / version
    if sdk.exists():
        return validate_sdk(version, entry, sdk)
    archive = download_archive(entry)
    print(f"正在解压 CEF {version} SDK ...")
    return extract_sdk(archive, sdk, version, entry)


def detect_build_tools() -> tuple[Path, str]:
    if os.name != "nt":
        raise RuntimeError("CEF 靶场构建仅支持 Windows x64。")
    installer = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
    vswhere = installer / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    if not vswhere.is_file():
        raise FileNotFoundError("未找到 vswhere.exe；请安装 Visual Studio 2022/2026 的“使用 C++ 的桌面开发”工作负载。")
    common = [str(vswhere), "-latest", "-products", "*", "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64"]

    def property_value(name: str) -> str:
        result = subprocess.run([*common, "-property", name], capture_output=True, text=True,
                                encoding="utf-8", errors="replace", check=True)
        return result.stdout.strip()

    product_line = property_value("catalog_productLineVersion")
    generators = {"18": "Visual Studio 18 2026", "2026": "Visual Studio 18 2026",
                  "17": "Visual Studio 17 2022", "2022": "Visual Studio 17 2022"}
    if product_line not in generators:
        raise RuntimeError(f"未找到支持的 MSVC 2022/2026 C++ 工具链 (检测值 {product_line!r})；请在 Visual Studio Installer 中安装。")
    cmake_command = shutil.which("cmake")
    if cmake_command:
        cmake = Path(cmake_command)
    else:
        installation = property_value("installationPath")
        cmake = Path(installation) / "Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe"
        if not installation or not cmake.is_file():
            raise FileNotFoundError("未找到 CMake；请安装 Visual Studio 的“适用于 Windows 的 C++ CMake 工具”或将 CMake 加入 PATH。")
    return cmake, generators[product_line]


def validate_build_cache(build: Path, version: str, sdk: Path) -> None:
    cache = build / "CMakeCache.txt"
    if not cache.is_file():
        return
    values: dict[str, str] = {}
    for line in cache.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line and ":" in line and not line.startswith(("#", "//")):
            key, value = line.split("=", 1)
            values[key.split(":", 1)[0]] = value
    expected = {"CEF_RANGE_MAJOR": version, "CEF_ROOT": str(sdk), "CMAKE_HOME_DIRECTORY": str(CEF_ROOT)}
    for key, value in expected.items():
        cached = values.get(key)
        matches = cached == value if key == "CEF_RANGE_MAJOR" else (
            cached is not None and os.path.normcase(str(Path(cached).resolve())) == os.path.normcase(str(Path(value).resolve()))
        )
        if not matches:
            raise ValueError(f"构建缓存 {cache} 中的 {key} 与 CEF {version} 不一致；请移走此 build/{version} 目录后重试。")
    if values.get("CMAKE_GENERATOR_PLATFORM") != "x64":
        raise ValueError(f"构建缓存不是 Windows x64: {cache}；请移走此构建目录后重试。")


def artifact_path(version: str) -> Path:
    return CEF_ROOT / "dist" / version / f"cef-shooting-range-{version}.exe"


def validate_artifact(version: str, entry: dict | None = None) -> Path:
    entry = entry or load_manifest()[version]
    executable = artifact_path(version)
    require_file(executable, f"CEF {version} 产物")
    for relative in (*RUNTIME_FILES, *entry["runtime_files"]):
        require_file(executable.parent / relative, f"CEF {version} 运行资源")
    locales = executable.parent / "locales"
    for locale in ("zh-CN.pak", "en-US.pak"):
        require_file(locales / locale, f"CEF {version} 语言资源")
    marker = executable.parent / "version.json"
    require_file(marker, f"CEF {version} 版本标记")
    try:
        actual = json.loads(marker.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ValueError(f"CEF {version} 版本标记无效: {marker}；请重新构建。") from error
    if not isinstance(actual, dict) or any(actual.get(key) != entry[key] for key in ("cef_version", "chromium_version")):
        raise ValueError(f"CEF {version} 产物版本与 versions.json 不一致: {marker}；请重新构建。")
    return executable


def build_version(version: str, entry: dict, force: bool = False) -> Path:
    sdk = ensure_sdk(version, entry)
    cmake, generator = detect_build_tools()
    build = CEF_ROOT / "build" / version
    validate_build_cache(build, version, sdk)
    configure = [
        str(cmake), "-S", str(CEF_ROOT), "-B", str(build), "-G", generator, "-A", "x64",
        f"-DCEF_ROOT={sdk}", f"-DCEF_RANGE_MAJOR={version}", "-DUSE_SANDBOX=OFF", "-DCMAKE_POLICY_VERSION_MINIMUM=3.5",
    ]
    command = [str(cmake), "--build", str(build), "--config", "Release", "--target", f"cef-shooting-range-{version}", "--parallel"]
    if force:
        command.append("--clean-first")
    print(f"正在构建 CEF {version} Release ...")
    for operation, args in (("配置", configure), ("构建", command)):
        result = subprocess.run(args, cwd=CEF_ROOT)
        if result.returncode:
            raise RuntimeError(f"CEF {version} CMake {operation}失败，退出码 {result.returncode}；请检查上面的编译输出。")
    executable = validate_artifact(version, entry)
    print(f"构建完成: {executable}")
    return executable


def launch_versions(versions: list[str], executables: dict[str, Path], base_url: str, port: int | None) -> None:
    launched: list[tuple[str, subprocess.Popen]] = []
    try:
        for version in versions:
            executable = executables[version]
            command = [str(executable), f"--base-url={base_url}"]
            if port is not None:
                command.append(f"--remote-debugging-port={port}")
            process = subprocess.Popen(command, cwd=executable.parent, close_fds=True)
            launched.append((version, process))
            time.sleep(0.2)
            if process.poll() is not None:
                raise RuntimeError(f"CEF {version} 启动后立即退出，退出码 {process.returncode}。")
            print(f"已启动 CEF {version} 靶场 (PID {process.pid})。")
    except Exception as error:
        processes = ", ".join(f"CEF {version}: PID {process.pid}" for version, process in launched) or "无"
        raise RuntimeError(f"CEF 启动失败: {error}；已经启动的进程: {processes}。请检查这些进程的窗口或错误日志。") from error


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    versions = args.versions if args.versions is not None else select_versions()
    if not versions:
        print("已取消。")
        return 0
    if args.remote_debugging_port is not None and len(versions) != 1:
        raise ValueError("--remote-debugging-port 只能与单个版本一起使用。")
    manifest = load_manifest()
    executables: dict[str, Path] = {}
    for version in versions:
        executables[version] = (validate_artifact(version, manifest[version]) if args.skip_build
                                else build_version(version, manifest[version], args.force_build))
    if args.no_launch:
        for version in versions:
            print(f"已验证 CEF {version}: {executables[version]}")
        return 0
    launch_versions(versions, executables, args.base_url, args.remote_debugging_port)
    return 0


if __name__ == "__main__":
    configure_output()
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n已取消。")
        raise SystemExit(130)
    except Exception as error:
        print(f"错误: {error}", file=sys.stderr)
        raise SystemExit(1)
