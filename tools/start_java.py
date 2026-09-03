from __future__ import annotations

import argparse
import locale
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path


VERSIONS = ("8", "11", "17", "21", "25")
MAVEN_VERSION = "3.9.9"

REPO_ROOT = Path(__file__).resolve().parents[1]
JAVA_ROOT = REPO_ROOT / "JAVA"
JAVA_TOOLS = JAVA_ROOT / ".tools"
JDKS_ROOT = JAVA_TOOLS / "jdks" / "corretto"
MAVEN_HOME = JAVA_TOOLS / f"apache-maven-{MAVEN_VERSION}"
MAVEN_CMD = MAVEN_HOME / "bin" / "mvn.cmd"
LOCAL_ENV = REPO_ROOT / ".tools" / "java-launcher"
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


def ensure_local_environment() -> None:
    local_python = LOCAL_ENV / "Scripts" / "python.exe"
    if not local_python.exists():
        uv = shutil.which("uv")
        if uv is None:
            raise RuntimeError("uv 未安装或不在 PATH 中。")
        print(f"正在创建 Python 环境: {LOCAL_ENV}")
        subprocess.run(
            [uv, "venv", str(LOCAL_ENV), "--python", "3.13"],
            cwd=REPO_ROOT,
            check=True,
        )

    if Path(sys.prefix).resolve() != LOCAL_ENV.resolve():
        completed = subprocess.run(
            [str(local_python), str(Path(__file__).resolve()), *sys.argv[1:]],
            cwd=REPO_ROOT,
        )
        raise SystemExit(completed.returncode)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="选择、构建并启动多个 Java 靶场版本。")
    parser.add_argument("--versions", nargs="+", choices=VERSIONS, help="跳过菜单并指定 JDK 版本。")
    parser.add_argument("--skip-build", action="store_true", help="跳过构建，直接使用现有 JAR。")
    parser.add_argument("--force-build", action="store_true", help="即使产物为最新也执行构建。")
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


def draw_version_selector(selected: set[str], focused: int, message: str) -> None:
    options: tuple[str | None, ...] = (*VERSIONS, None)
    lines = ["请选择运行版本(可多选):", ""]

    for index, version in enumerate(options):
        prefix = ">" if index == focused else " "
        if version is None:
            lines.extend(("", f"{prefix} [ 已完成选择 ]"))
        else:
            option = f"[✓] JDK {version}" if version in selected else f"[ ] JDK {version}"
            lines.append(f"{prefix} {green(option) if version in selected else option}")

    lines.append(message)
    frame = "\x1b[H" + "".join(f"\x1b[2K{line}\n" for line in lines)
    sys.stdout.write(frame)
    sys.stdout.flush()


def select_versions() -> list[str]:
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
                message = "请至少选择一个 JDK 版本。"
            else:
                return [version for version in VERSIONS if version in selected]
        elif key == "escape":
            return []
        elif key == "interrupt":
            raise KeyboardInterrupt


def normalize_versions(requested: list[str]) -> list[str]:
    requested_set = set(requested)
    return [version for version in VERSIONS if version in requested_set]


def find_jdk_executable(version: str, executable: str) -> Path:
    version_root = JDKS_ROOT / version
    candidates = sorted(
        (
            path
            for path in version_root.rglob(executable)
            if path.is_file() and path.parent.name.lower() == "bin"
        ),
        key=lambda path: len(path.parts),
    )
    if not candidates:
        raise FileNotFoundError(f"在 {version_root} 下找不到 {executable}。")
    return candidates[0]


def ensure_maven() -> None:
    if MAVEN_CMD.exists():
        return

    JAVA_TOOLS.mkdir(parents=True, exist_ok=True)
    archive = JAVA_TOOLS / f"apache-maven-{MAVEN_VERSION}-bin.zip"
    url = (
        "https://archive.apache.org/dist/maven/maven-3/"
        f"{MAVEN_VERSION}/binaries/apache-maven-{MAVEN_VERSION}-bin.zip"
    )
    print(f"正在下载 Maven {MAVEN_VERSION} ...")
    try:
        urllib.request.urlretrieve(url, archive)
        with zipfile.ZipFile(archive) as package:
            package.extractall(JAVA_TOOLS)
    finally:
        archive.unlink(missing_ok=True)

    if not MAVEN_CMD.exists():
        raise RuntimeError(f"Maven 解压后未找到: {MAVEN_CMD}")


def artifact_path(version: str) -> Path:
    return JAVA_ROOT / "target" / f"jdk-{version}" / f"shooting-range-{version}.jar"


def build_required(jar_path: Path) -> bool:
    if not jar_path.exists():
        return True

    jar_time = jar_path.stat().st_mtime
    inputs = [JAVA_ROOT / "pom.xml", *(JAVA_ROOT / "src").rglob("*")]
    return any(path.is_file() and path.stat().st_mtime > jar_time for path in inputs)


def build_version(version: str, force: bool) -> Path:
    jar_path = artifact_path(version)
    if not force and not build_required(jar_path):
        print(f"JDK {version} 产物已是最新，跳过构建。")
        return jar_path

    ensure_maven()
    javac = find_jdk_executable(version, "javac.exe")
    jdk_home = javac.parent.parent
    env = os.environ.copy()
    env["JAVA_HOME"] = str(jdk_home)
    env["PATH"] = f"{jdk_home / 'bin'}{os.pathsep}{env.get('PATH', '')}"

    print(f"正在构建 JDK {version} 靶场 ...")
    completed = subprocess.run(
        [
            str(MAVEN_CMD),
            "-q",
            f"-Dtarget.java.version={version}",
            "-DskipTests",
            "package",
        ],
        cwd=JAVA_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding=locale.getpreferredencoding(False),
        errors="replace",
    )
    if completed.returncode != 0:
        if completed.stdout:
            print(completed.stdout, file=sys.stderr)
        raise RuntimeError(f"JDK {version} Maven 构建失败，退出码 {completed.returncode}。")
    if not jar_path.exists():
        raise RuntimeError(f"构建完成但未生成产物: {jar_path}")

    print(f"构建完成: {jar_path}")
    return jar_path


def validate_artifact(version: str) -> Path:
    jar_path = artifact_path(version)
    if not jar_path.exists():
        raise FileNotFoundError(f"JDK {version} 产物不存在: {jar_path}")
    find_jdk_executable(version, "javaw.exe")
    return jar_path


def launch_versions(versions: list[str], jars: dict[str, Path]) -> None:
    processes: list[tuple[str, subprocess.Popen[bytes]]] = []
    try:
        for version in versions:
            javaw = find_jdk_executable(version, "javaw.exe")
            process = subprocess.Popen(
                [str(javaw), "-jar", str(jars[version])],
                cwd=JAVA_ROOT,
                close_fds=True,
            )
            processes.append((version, process))

        for version, process in processes:
            if process.poll() is not None:
                raise RuntimeError(f"JDK {version} 靶场启动后立即退出，退出码 {process.returncode}。")
            print(f"已启动 JDK {version} 靶场 (PID {process.pid})。")
    except Exception:
        for _, process in processes:
            if process.poll() is None:
                process.terminate()
        raise


def main() -> int:
    configure_output()
    ensure_local_environment()
    args = parse_args()

    versions = normalize_versions(args.versions) if args.versions else select_versions()
    if not versions:
        clear_screen()
        print("已取消。")
        return 0

    if args.skip_build:
        jars = {version: validate_artifact(version) for version in versions}
    else:
        jars = {version: build_version(version, args.force_build) for version in versions}

    if args.no_launch:
        for version in versions:
            print(f"已验证 JDK {version}: {jars[version]}")
        return 0

    launch_versions(versions, jars)
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
