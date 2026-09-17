"""启动 Excel 插件靶场: localhost 证书 -> HTTPS 静态服务 -> sideload 到 Excel。"""

from __future__ import annotations

import argparse
import functools
import http.server
import os
import shutil
import ssl
import subprocess
import sys
import winreg
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ADDIN_DIR = REPO_ROOT / "OFFICE" / "excel-addin"
CERT_DIR = ADDIN_DIR / ".certs"
PFX_PATH = CERT_DIR / "localhost.pfx"
CER_PATH = CERT_DIR / "localhost.cer"
PEM_PATH = CERT_DIR / "localhost.pem"
PFX_PASSWORD = "xpath-excel-addin"
DEFAULT_PORT = 7300
MANIFEST_PORT_ANCHOR = "localhost:7300"
SIDELOAD_NAME = "xpath-excel-addin.manifest.xml"
WEF_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Office" / "16.0" / "Wef"
EXCEL_REGISTRY_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\excel.exe"
# 桌面版 Excel 的开发者加载项目录: 值名是 manifest 里的插件 Id, 数据是 manifest 的绝对路径。
DEVELOPER_KEY = r"SOFTWARE\Microsoft\Office\16.0\WEF\Developer"
MANIFEST_NAMESPACE = "http://schemas.microsoft.com/office/appforoffice/1.1"


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def powershell_environment() -> dict[str, str]:
    """Windows PowerShell 5.1 必须只看到自己的模块路径。

    若继承 PowerShell 7 的 PSModulePath, Microsoft.PowerShell.Security / PKI 会因
    类型数据重复而加载失败, 表现为 `Cert:` 提供程序不存在。
    """

    environment = os.environ.copy()
    home = environment.get("USERPROFILE", "")
    program_files = environment.get("ProgramFiles", r"C:\Program Files")
    system_root = environment.get("SystemRoot", r"C:\Windows")
    environment["PSModulePath"] = ";".join(
        (
            str(Path(home) / "Documents" / "WindowsPowerShell" / "Modules"),
            str(Path(program_files) / "WindowsPowerShell" / "Modules"),
            str(Path(system_root) / "system32" / "WindowsPowerShell" / "v1.0" / "Modules"),
        )
    )
    return environment


def run_powershell(script: str) -> str:
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=powershell_environment(),
    )
    if completed.returncode != 0:
        raise RuntimeError(f"PowerShell 执行失败: {completed.stderr.strip() or completed.stdout.strip()}")
    return completed.stdout.strip()


def _escape(path: Path) -> str:
    return str(path).replace("'", "''")


def certificate_ready() -> bool:
    if not (PFX_PATH.exists() and CER_PATH.exists()):
        return False
    # 必须同时满足: My 存储里的证书未过期, 且同一指纹已进入 Root 存储(建立信任链)。
    script = (
        "$cert = Get-ChildItem Cert:\\CurrentUser\\My | Where-Object { $_.Subject -eq 'CN=localhost' }"
        " | Sort-Object NotAfter -Descending | Select-Object -First 1;"
        " $root = Get-ChildItem Cert:\\CurrentUser\\Root | Where-Object { $_.Subject -eq 'CN=localhost' };"
        " if ($cert -and $root -and $cert.NotAfter -gt (Get-Date).AddDays(30)"
        " -and $root.Thumbprint -eq $cert.Thumbprint) { 'ok' }"
    )
    try:
        return run_powershell(script).strip() == "ok"
    except RuntimeError:
        return False


def ensure_certificate(renew: bool) -> None:
    CERT_DIR.mkdir(parents=True, exist_ok=True)
    if not renew and certificate_ready():
        print(f"复用现有 localhost 证书: {PFX_PATH}")
        return

    print("正在创建并信任 localhost 证书 ...")
    script = f"""
$ErrorActionPreference = 'Stop'
Get-ChildItem Cert:\\CurrentUser\\My | Where-Object {{ $_.Subject -eq 'CN=localhost' }} | Remove-Item -Force
$cert = New-SelfSignedCertificate -DnsName 'localhost', '127.0.0.1' -Subject 'CN=localhost' `
    -CertStoreLocation Cert:\\CurrentUser\\My -NotAfter (Get-Date).AddYears(5) -FriendlyName 'xpath-excel-addin'
Export-PfxCertificate -Cert $cert -FilePath '{_escape(PFX_PATH)}' `
    -Password (ConvertTo-SecureString -String '{PFX_PASSWORD}' -Force -AsPlainText) | Out-Null
Export-Certificate -Cert $cert -FilePath '{_escape(CER_PATH)}' | Out-Null
# 非交互会话下 Import-Certificate 写 Root 存储会要求 UI 同意, 用 certutil 静默写入。
& certutil.exe -user -addstore -f Root '{_escape(CER_PATH)}' | Out-Null
if ($LASTEXITCODE -ne 0) {{
    Import-Certificate -FilePath '{_escape(CER_PATH)}' -CertStoreLocation Cert:\\CurrentUser\\Root | Out-Null
}}
$cert.Thumbprint
"""
    thumbprint = run_powershell(script)
    print(f"证书已就绪: {thumbprint}")


def find_openssl() -> Path | None:
    found = shutil.which("openssl")
    if found:
        return Path(found)
    for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
        if not base:
            continue
        candidate = Path(base) / "Git" / "usr" / "bin" / "openssl.exe"
        if candidate.is_file():
            return candidate
    return None


def _convert_with_pwsh() -> None:
    """用 PowerShell 7 的 .NET API 把 PFX 转成 PEM(无 openssl 时的兜底)。"""

    script = f"""
$ErrorActionPreference = 'Stop'
$cert = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new(
    '{_escape(PFX_PATH)}', '{PFX_PASSWORD}',
    [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::Exportable)
[System.IO.File]::WriteAllText('{_escape(PEM_PATH)}',
    $cert.ExportCertificatePem() + "`n" + $cert.GetRSAPrivateKey().ExportPkcs8PrivateKeyPem())
"""
    completed = subprocess.run(
        ["pwsh", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise RuntimeError(f"pwsh 转换 PEM 失败: {completed.stderr.strip() or completed.stdout.strip()}")


def ensure_pem() -> None:
    """CPython 的 ssl 不支持直接读 PKCS#12, 需要把 PFX 转成 PEM。"""

    if PEM_PATH.exists() and PEM_PATH.stat().st_mtime >= PFX_PATH.stat().st_mtime:
        return

    openssl = find_openssl()
    if openssl is not None:
        base = [str(openssl), "pkcs12", "-in", str(PFX_PATH),
                "-passin", f"pass:{PFX_PASSWORD}", "-nodes", "-out", str(PEM_PATH)]
        for extra in (["-legacy"], []):  # openssl 3.x 读 Windows 的 RC2 加密 PFX 需要 -legacy
            completed = subprocess.run(
                [*base, *extra], capture_output=True, text=True,
                encoding="utf-8", errors="replace",
            )
            if completed.returncode == 0:
                print(f"已由 openssl 生成 PEM: {PEM_PATH}")
                return
        print(f"openssl 转换失败, 改用 pwsh 兜底: {completed.stderr.strip()}")

    try:
        _convert_with_pwsh()
    except FileNotFoundError as error:
        raise RuntimeError(
            "需要 openssl(随 Git for Windows 安装)或 PowerShell 7(pwsh) 之一来把 PFX 转成 PEM。"
        ) from error
    print(f"已由 pwsh 生成 PEM: {PEM_PATH}")


class NoStoreHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        super().end_headers()

    def log_message(self, format: str, *args) -> None:  # noqa: A002 - 与基类签名保持一致
        sys.stdout.write(f"[https] {self.address_string()} {format % args}\n")
        sys.stdout.flush()


def create_server(port: int) -> http.server.ThreadingHTTPServer:
    handler = functools.partial(NoStoreHandler, directory=str(ADDIN_DIR))
    try:
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    except OSError as error:
        raise RuntimeError(f"端口 {port} 无法监听({error});请用 --port 指定其它端口。") from error
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=str(PEM_PATH))
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    return httpd


def render_manifest(port: int) -> str:
    source = (ADDIN_DIR / "manifest.xml").read_text(encoding="utf-8")
    return source.replace(MANIFEST_PORT_ANCHOR, f"localhost:{port}")


def manifest_addin_id(port: int = DEFAULT_PORT) -> str:
    root = ET.fromstring(render_manifest(port))
    element = root.find(f"{{{MANIFEST_NAMESPACE}}}Id")
    if element is None or not (element.text or "").strip():
        raise RuntimeError("manifest.xml 缺少 <Id>, 无法注册到 Excel 开发者目录。")
    return element.text.strip()


def sideload(port: int) -> tuple[Path, str]:
    """写入 manifest 并把插件注册进 Excel 的开发者加载项目录。

    实测(与 office-addin-dev-settings register 行为一致): 桌面版 Excel 认的是
    HKCU\\...\\WEF\\Developer\\<插件 Id> = manifest 绝对路径, 只往 Wef 目录拷文件不会生效。
    """

    WEF_DIR.mkdir(parents=True, exist_ok=True)
    target = WEF_DIR / SIDELOAD_NAME
    target.write_text(render_manifest(port), encoding="utf-8")
    addin_id = manifest_addin_id(port)
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, DEVELOPER_KEY, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, addin_id, 0, winreg.REG_SZ, str(target))
    return target, addin_id


def find_excel() -> Path | None:
    try:
        import winreg
    except ImportError:
        return None
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            with winreg.OpenKey(root, EXCEL_REGISTRY_KEY) as handle:
                return Path(winreg.QueryValue(handle, None))
        except OSError:
            continue
    return None


def excel_running() -> bool:
    completed = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq EXCEL.EXE", "/NH"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return "EXCEL.EXE" in completed.stdout.upper()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="启动 Excel 插件靶场。")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"HTTPS 端口, 默认 {DEFAULT_PORT}。")
    parser.add_argument("--no-launch", action="store_true", help="不自动拉起 Excel。")
    parser.add_argument("--renew-cert", action="store_true", help="强制重建 localhost 证书。")
    parser.add_argument("--skip-sideload", action="store_true", help="只起服务, 不写入 Wef 目录。")
    parser.add_argument("--prepare-only", action="store_true", help="只准备证书与 sideload, 不启动服务。")
    return parser.parse_args()


def main() -> int:
    configure_output()
    args = parse_args()

    if not (ADDIN_DIR / "manifest.xml").is_file():
        print(f"错误: 找不到 {ADDIN_DIR / 'manifest.xml'}", file=sys.stderr)
        return 1

    try:
        ensure_certificate(args.renew_cert)
        ensure_pem()
    except RuntimeError as error:
        print(f"错误: {error}", file=sys.stderr)
        return 1

    if args.skip_sideload:
        print("已跳过 sideload。")
    else:
        try:
            target, addin_id = sideload(args.port)
            print(f"已注册到 Excel 开发者目录: {addin_id} -> {target}")
        except (OSError, RuntimeError) as error:
            print(f"错误: 注册加载项失败({error})。可用 --skip-sideload 只起服务。", file=sys.stderr)

    excel = find_excel()
    if excel is None:
        print("未检测到 Excel, 仅启动服务;请在装有 Excel 桌面版的机器上重复本步骤。")
    elif args.no_launch or args.prepare_only:
        print("已跳过启动 Excel。")
    elif excel_running():
        print("检测到 Excel 正在运行: 请完全退出并重新打开 Excel, Ribbon 才会出现新选项卡。")
    else:
        subprocess.Popen([str(excel)])
        print(f"已启动 Excel: {excel}")

    url = f"https://localhost:{args.port}/src/taskpane.html"
    print(f"\n服务地址: {url}")
    print("在 Excel 中: 顶部 'Excel 靶场插件' 选项卡 -> '打开面板'。")
    print("按 Ctrl+C 停止服务。\n")

    if args.prepare_only:
        print("已按 --prepare-only 结束(未启动服务)。")
        return 0

    try:
        server = create_server(args.port)
    except RuntimeError as error:
        print(f"错误: {error}", file=sys.stderr)
        return 1

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止服务。")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
    except Exception as error:  # noqa: BLE001 - CLI 顶层兜底
        print(f"错误: {error}", file=sys.stderr)
        raise SystemExit(1)
