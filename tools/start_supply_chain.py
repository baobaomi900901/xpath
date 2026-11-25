"""Build, launch, reset and independently evaluate the supply-chain GUI benchmark."""
from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO = REPO_ROOT / "SCENARIOS" / "supply_chain"
RUNTIME = SCENARIO / "runtime"
BUILD = SCENARIO / "build"
sys.path.insert(0, str(REPO_ROOT))

from SCENARIOS.supply_chain.fixtures import PROFILES, create_run
from SCENARIOS.supply_chain.evaluate import evaluate, write_report
from SCENARIOS.supply_chain.server import make_server


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="库存补货综合靶场：Web → Win32 → Java")
    parser.add_argument("command", nargs="?", default="launch", choices=("launch", "build", "reset", "serve", "stop", "evaluate", "task", "check"))
    parser.add_argument("--profile", choices=PROFILES, default="standard")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--agent", default="unspecified", help="用于评测报告的 Agent 名称")
    parser.add_argument("--track", choices=("cli", "sdk"), default="cli")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--obstacles", action="store_true", help="增加GUI障碍：Win32/Java惰性创建控件，Web每次刷新随机元素ID")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开 A，可自行打开任务中的网址")
    parser.add_argument("--no-apps", action="store_true", help="仅启动服务，用于开发或远程界面检查")
    parser.add_argument("--foreground", action="store_true", help="在当前进程运行服务，Ctrl+C 关闭服务与桌面应用")
    parser.add_argument("--run-dir", type=Path, help="评测/显示任务的历史运行目录；serve 内部也使用该参数")
    args = parser.parse_args(argv)
    if not 0 <= args.seed <= 999999:
        parser.error("seed 必须在 0 到 999999 之间")
    if not 1024 <= args.port <= 65535:
        parser.error("port 必须在 1024 到 65535 之间")
    return args


def read_current(runtime=RUNTIME):
    file = Path(runtime) / "current.json"
    return json.loads(file.read_text(encoding="utf-8")) if file.is_file() else None


def task_text(context, track, url):
    template = (SCENARIO / "task.md").read_text(encoding="utf-8")
    for key, value in dict(batch_id=context["batch_id"], today=context["today"], deadline=context["deadline"],
                           plant=context["plant"], warehouse=context["warehouse"], track=track.upper(), url=url).items():
        template = template.replace("{{" + key + "}}", str(value))
    return template


def new_run(args, runtime=RUNTIME):
    runtime = Path(runtime).resolve()
    path = runtime / "runs" / uuid.uuid4().hex
    fixture = create_run(path, args.profile, args.seed, args.agent, args.track, obstacles=args.obstacles)
    url = f"http://127.0.0.1:{args.port}"
    control = dict(url=url, run_dir=str(path), run_id=fixture["context"]["run_id"], token=secrets.token_urlsafe(32))
    (path / "control.json").write_text(json.dumps(control), encoding="utf-8")
    (path / "task.md").write_text(task_text(fixture["context"], args.track, url), encoding="utf-8")
    (runtime / "current.json").write_text(json.dumps(control), encoding="utf-8")
    return path


def get_health(url):
    try:
        with urllib.request.urlopen(url + "/health", timeout=1) as response:
            return json.load(response)
    except (OSError, ValueError):
        return None


def stop_current(runtime=RUNTIME):
    current = read_current(runtime)
    if not current:
        return
    health = get_health(current["url"])
    if health is None:
        return
    if health.get("run_id") != current["run_id"]:
        raise RuntimeError("端口正在运行其他批次，拒绝关闭无关服务")
    request = urllib.request.Request(current["url"] + "/__control/stop",
                                     data=urllib.parse.urlencode(dict(token=current["token"])).encode())
    with urllib.request.urlopen(request, timeout=3) as response:
        response.read()
    marker = Path(current["run_dir"]) / "stopped.json"
    limit = time.monotonic() + 8
    while time.monotonic() < limit:
        if marker.exists():
            return
        time.sleep(.1)
    raise RuntimeError("旧服务尚未完全退出，请检查 service.log 后重试")


def java_tools():
    candidates = []
    if os.environ.get("JAVA_HOME"):
        candidates.append(Path(os.environ["JAVA_HOME"]) / "bin")
    executable = shutil.which("javac")
    if executable:
        candidates.append(Path(executable).parent)
    repo_jdks = REPO_ROOT / "JAVA" / ".tools" / "jdks" / "corretto"
    for version in ("21", "17", "11", "8", "25"):
        candidates.extend(p.parent for p in (repo_jdks / version).glob("**/bin/javac.exe"))
    suffix = ".exe" if os.name == "nt" else ""
    for folder in candidates:
        javac, java = folder / ("javac" + suffix), folder / ("java" + suffix)
        javaw = folder / ("javaw" + suffix)
        if javac.is_file() and java.is_file():
            return javac, java, javaw if javaw.is_file() else java
    raise RuntimeError("未找到 JDK，请安装 JDK 8+ 并设置 JAVA_HOME 或 PATH")


def build_apps():
    if os.name != "nt":
        raise RuntimeError("Win32 综合靶场需在 Windows 上构建运行")
    cmake = shutil.which("cmake")
    if not cmake:
        raise RuntimeError("未找到 CMake，请安装 CMake 和 MSVC C++ 工具")
    subprocess.run([cmake, "-S", str(SCENARIO / "win32"), "-B", str(BUILD / "win32")], check=True)
    subprocess.run([cmake, "--build", str(BUILD / "win32"), "--config", "Release"], check=True)
    javac, _, _ = java_tools()
    (BUILD / "java").mkdir(parents=True, exist_ok=True)
    subprocess.run([str(javac), "-encoding", "UTF-8", "-source", "8", "-target", "8", "-d", str(BUILD / "java"),
                    *map(str, sorted((SCENARIO / "java").glob("*.java")))], check=True)
    check_apps()


def check_apps():
    required = [BUILD / "win32" / "Release" / "supply-chain-supplier.exe", BUILD / "java" / "SupplyChainPurchase.class"]
    for file in required:
        if not file.is_file():
            raise RuntimeError(f"缺少构建产物：{file}，请先运行 build")
    java_tools()


def app_commands(url, obstacles=False, javaw=None):
    if javaw is None:
        _, _, javaw = java_tools()
    extra = ["--obstacles"] if obstacles else []
    return [[str(BUILD / "win32" / "Release" / "supply-chain-supplier.exe"), "--url", url, *extra],
            [str(javaw), "-cp", str(BUILD / "java"), "SupplyChainPurchase", "--url", url, *extra]]


def serve(args, path):
    control = json.loads((path / "control.json").read_text(encoding="utf-8"))
    server = make_server(path, args.port, control_token=control["token"])
    children = []
    logs = []
    try:
        (path / "service.json").write_text(json.dumps(dict(pid=os.getpid(), url=control["url"])), encoding="utf-8")
        if not args.no_apps:
            commands = app_commands(control["url"], server.store.fixture["context"].get("obstacles", False))
            for index, command in enumerate(commands):
                output = (path / f"app-{index + 1}.log").open("wb")
                logs.append(output)
                children.append(subprocess.Popen(command, cwd=REPO_ROOT, stdin=subprocess.DEVNULL,
                                                   stdout=output, stderr=subprocess.STDOUT,
                                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)))
            # Catch immediate loader/JVM failures instead of claiming the whole range is ready.
            until = time.monotonic() + .8
            while time.monotonic() < until:
                for index, child in enumerate(children):
                    if child.poll() is not None:
                        raise RuntimeError(f"应用 {index + 1} 启动后立即退出（{child.returncode}），请查看 app-{index + 1}.log；受限沙箱中请通过普通桌面终端启动。")
                time.sleep(.05)
        if not args.no_browser:
            webbrowser.open(control["url"])
        print(f"综合靶场已启动：{control['url']}\n运行目录：{path}", flush=True)
        server.serve_forever(poll_interval=.1)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        for child in children:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=2)
        for output in logs:
            output.close()
        (path / "stopped.json").write_text(json.dumps(dict(pid=os.getpid(), stopped=True)), encoding="utf-8")


def selected_run(args):
    if args.run_dir:
        return args.run_dir.resolve()
    current = read_current()
    if not current:
        raise RuntimeError("尚无测试批次，请先 launch 或 reset")
    return Path(current["run_dir"])


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args(argv)
    try:
        if args.command == "build":
            stop_current()
            build_apps()
        elif args.command == "check":
            check_apps()
            print("Win32 / Java 产物与 Java 运行时检查通过")
        elif args.command == "stop":
            stop_current()
            print("当前场景服务与所属桌面应用已停止；历史结果保留。")
        elif args.command == "task":
            print((selected_run(args) / "task.md").read_text(encoding="utf-8"))
        elif args.command == "evaluate":
            path = selected_run(args)
            report = evaluate(path)
            write_report(path, report)
            print(f"{'通过' if report['passed'] else '未通过'}；采购单 {report['actual_order_count']}/{report['expected_order_count']}；金额 {report['actual_total']}/{report['expected_total']}")
            print(f"报告：{path / 'evaluation.md'}")
            return 0 if report["passed"] else 1
        elif args.command == "serve":
            if not args.run_dir:
                raise RuntimeError("serve 是内部启动命令，必须提供 --run-dir")
            serve(args, args.run_dir.resolve())
        else:
            # Release our own previous executable before the linker attempts to replace it.
            stop_current()
            if args.command == "launch":
                if not args.skip_build:
                    build_apps()
                else:
                    check_apps()
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                try:
                    probe.bind(("127.0.0.1", args.port))
                except OSError:
                    raise RuntimeError("指定端口已有其他服务，请更换 --port") from None
            path = new_run(args)
            if args.command == "reset":
                print(f"新批次已创建，旧结果保留：{path}")
                print(f"参测任务：{path / 'task.md'}")
                return 0
            if args.foreground:
                serve(args, path)
            else:
                command = [sys.executable, str(Path(__file__).resolve()), "serve", "--run-dir", str(path), "--port", str(args.port)]
                for flag in ("no_apps", "no_browser"):
                    if getattr(args, flag):
                        command.append("--" + flag.replace("_", "-"))
                with (path / "service.log").open("wb") as output:
                    process = subprocess.Popen(command, cwd=REPO_ROOT, stdin=subprocess.DEVNULL, stdout=output,
                                               stderr=subprocess.STDOUT, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                limit = time.monotonic() + 12
                run_id = json.loads((path / "fixture.json").read_text(encoding="utf-8"))["context"]["run_id"]
                while time.monotonic() < limit:
                    health = get_health(f"http://127.0.0.1:{args.port}")
                    if health and health.get("run_id") == run_id:
                        print(f"综合靶场已启动：http://127.0.0.1:{args.port}\n参测任务：{path / 'task.md'}\n停止命令：python tools/start_supply_chain.py stop")
                        return 0
                    if process.poll() is not None:
                        break
                    time.sleep(.15)
                raise RuntimeError(f"启动未就绪，请检查 {path / 'service.log'}")
        return 0
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        print(f"错误：{error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
