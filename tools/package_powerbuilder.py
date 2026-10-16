"""Build a self-contained Windows EXE with the app and private PB runtime."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools import start_powerbuilder as application
from POWERBUILDER.verify.package_smoke import EXPECTED_CHECKS, verify

WORK = ROOT / "POWERBUILDER" / "build" / "package"
DIST = ROOT / "POWERBUILDER" / "dist"


def run_logged(command, cwd: Path, log: Path) -> None:
    result = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    content = result.stdout.decode("utf-8", errors="replace")
    log.write_text(content, encoding="utf-8")
    if result.returncode:
        print(content, flush=True)
        raise RuntimeError(f"命令执行失败（{result.returncode}），详见 {log}")


def batch_path(path: Path) -> str:
    text = str(path)
    if any(character in text for character in ('%', '"', '\r', '\n')):
        raise ValueError(f"构建路径包含不支持的字符：{path}")
    return '"' + text + '"'


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="打包 PowerBuilder 靶场为含运行时的单个 EXE。")
    parser.add_argument("--tools-path", type=Path)
    parser.add_argument("--runtime-path", type=Path)
    parser.add_argument("--output", type=Path, default=DIST / "PowerBuilder靶场.exe")
    args = parser.parse_args(argv)
    if os.name != "nt":
        raise RuntimeError("打包只能在 Windows 上进行。")
    compiler = application.resolve_tools(args.tools_path)
    if application.file_version(compiler) != application.RUNTIME_VERSION:
        raise RuntimeError(f"编译工具版本必须是 {application.RUNTIME_VERSION}")
    runtime = application.resolve_runtime(args.runtime_path)
    windows = Path(os.environ.get("WINDIR", r"C:\Windows"))
    makecab = windows / "System32" / "makecab.exe"
    vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    if not makecab.is_file() or not vswhere.is_file():
        raise FileNotFoundError("打包需要 Windows makecab 和 Visual Studio C++ 工具。")
    vs = subprocess.check_output([str(vswhere), "-latest", "-products", "*", "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"], encoding="utf-8").strip()
    if not vs:
        raise RuntimeError("没有找到 Visual Studio C++ x86 构建工具。")
    vsdev = Path(vs) / "Common7" / "Tools" / "VsDevCmd.bat"
    WORK.mkdir(parents=True, exist_ok=True)
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    print("[1/4] 在独立目录编译 PowerBuilder 程序", flush=True)
    app_dir = WORK / "app"
    script = application.prepare_build(ROOT / "POWERBUILDER" / "src", app_dir, runtime)
    application.run_compiler(compiler, script, app_dir)
    inventory = []
    license_map = []
    with tempfile.TemporaryDirectory(prefix="payload_", dir=WORK) as temporary:
        stage = Path(temporary)
        for source in sorted(runtime.iterdir()):
            if source.is_file():
                shutil.copy2(source, stage / source.name)
        legal = runtime / "ThirdPartyLegal"
        if legal.is_dir():
            for index, source in enumerate(sorted(path for path in legal.rglob("*") if path.is_file())):
                name = f"license-{index:04d}.txt"
                shutil.copy2(source, stage / name)
                license_map.append({"file": name, "original": str(source.relative_to(runtime))})
        for name in (application.EXE_NAME, "pb_range.pbd", "pb.ini"):
            shutil.copy2(app_dir / name, stage / name)
        # Native PB gives DLLs next to the application precedence over registry
        # runtime locations. This XML is portable and contains no local path.
        (stage / "PowerBuilderShootingRange.xml").write_text(
            '<?xml version="1.0" encoding="utf-8"?><Application><RuntimePath>.</RuntimePath></Application>\n', encoding="utf-8")
        (stage / "runtime-licenses.json").write_text(json.dumps(license_map, ensure_ascii=False, indent=2), encoding="utf-8")
        for path in sorted(stage.iterdir()):
            if not path.name.isascii() or any(c in path.name for c in '\\/:"<>|?*'):
                raise ValueError(f"不支持的 CAB 文件名：{path.name}")
            inventory.append({"name": path.name, "bytes": path.stat().st_size,
                              "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        print(f"[2/4] 压缩 {len(inventory)} 个应用、运行时和许可文件", flush=True)
        cabinet = WORK / "payload.cab"
        cabinet.unlink(missing_ok=True)
        ddf = WORK / "payload.ddf"
        directives = [".OPTION EXPLICIT", ".Set Cabinet=ON", ".Set Compress=ON", ".Set CompressionType=LZX", ".Set CompressionMemory=21", ".Set MaxDiskSize=0", '.Set CabinetNameTemplate=payload.cab', '.Set DiskDirectoryTemplate=.', f'.Set SourceDir={stage.name}']
        directives.extend('"' + item["name"] + '"' for item in inventory)
        ddf.write_text("\r\n".join(directives) + "\r\n", encoding="ascii")
        run_logged([str(makecab), "/F", str(ddf)], WORK, WORK / "cabinet.log")
        if not cabinet.is_file():
            raise RuntimeError("makecab 未生成 payload.cab。")
    print("[3/4] 编译静态链接的 x86 单文件启动器", flush=True)
    resource = WORK / "payload.rc"
    resource.write_text('101 RCDATA "' + str(cabinet).replace("\\", "\\\\") + '"\n', encoding="utf-16")
    batch = WORK / "compile.cmd"
    source = ROOT / "POWERBUILDER" / "packaging" / "single_exe.cpp"
    resource_out = WORK / "payload.res"
    object_out = WORK / "single_exe.obj"
    temporary_output = WORK / "PowerBuilderRange.new.exe"
    commands = ["@echo off", "chcp 65001 >nul", 'call ' + batch_path(vsdev) + ' -no_logo -arch=x86 -host_arch=x64', "if errorlevel 1 exit /b 1",
                'rc.exe /nologo /fo' + batch_path(resource_out) + ' ' + batch_path(resource), "if errorlevel 1 exit /b 1",
                'cl.exe /nologo /std:c++17 /utf-8 /O2 /MT /EHsc /W4 /DUNICODE /D_UNICODE /D_WIN32_WINNT=0x0A00 /DWINVER=0x0A00 /Fo' + batch_path(object_out) + ' /Fe' + batch_path(temporary_output) + ' ' + batch_path(source) + ' ' + batch_path(resource_out) + ' /link /SUBSYSTEM:WINDOWS /MACHINE:X86 /DYNAMICBASE /NXCOMPAT setupapi.lib shell32.lib ole32.lib user32.lib', "exit /b %errorlevel%"]
    batch.write_text("\r\n".join(commands) + "\r\n", encoding="utf-8")
    run_logged([str(windows / "System32" / "cmd.exe"), "/d", "/v:off", "/c", str(batch)], WORK, WORK / "compile.log")
    print(f"[4/4] 从独立中文目录验证内置 Runtime、{EXPECTED_CHECKS} 项应用自检及临时文件清理", flush=True)
    result = verify(temporary_output, WORK / "verify")
    # Publish only after the complete single-file artifact passes verification.
    shutil.copyfile(temporary_output, output)
    manifest = {"created_at": datetime.now(timezone.utc).isoformat(), "file": output.name,
                "bytes": output.stat().st_size, "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "architecture": "x86", "runtime_version": application.RUNTIME_VERSION,
                "verification": result, "files": inventory}
    (output.parent / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"单文件 EXE：{output}\n大小：{output.stat().st_size / 1024 / 1024:.1f} MiB\nSHA-256：{manifest['sha256']}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"打包失败：{error}", file=sys.stderr)
        raise SystemExit(1)
