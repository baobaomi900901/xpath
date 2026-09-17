"""启动 Excel 插件靶场: localhost 证书 -> HTTPS 静态服务 -> sideload 到 Excel。"""

from __future__ import annotations

import argparse
import base64
import functools
import http.server
import os
import shutil
import ssl
import subprocess
import sys
import winreg
import xml.etree.ElementTree as ET
import zipfile
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
DIST_DIR = ADDIN_DIR / "dist"
SIDELOAD_WORKBOOK_NAME = "Excel 靶场插件.xlsx"
WEF_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Office" / "16.0" / "Wef"
# 桌面版 Excel 的开发者加载项目录: 值名是 manifest 里的插件 Id, 数据是 manifest 的绝对路径。
DEVELOPER_KEY = r"SOFTWARE\Microsoft\Office\16.0\WEF\Developer"
MANIFEST_NAMESPACE = "http://schemas.microsoft.com/office/appforoffice/1.1"
PLACEHOLDER_ADDIN_ID = "00000000-0000-0000-0000-000000000000"


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            # line_buffering: 输出被重定向/接管时也要立刻可见, 否则"端口被占用"这类报错会被缓冲区吞掉。
            stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)


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
    -CertStoreLocation Cert:\\CurrentUser\\My -NotAfter (Get-Date).AddYears(5) -FriendlyName 'xpath-excel-addin' `
    -Provider 'Microsoft Enhanced RSA and AES Cryptographic Provider' -KeyExportPolicy Exportable `
    -TextExtension @('2.5.29.19={{critical}}{{text}}ca=1')
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


def _der_length(length: int) -> bytes:
    if length < 0x80:
        return bytes([length])
    encoded = length.to_bytes((length.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(encoded)]) + encoded


def _der_integer(value: bytes) -> bytes:
    value = value.lstrip(b"\x00") or b"\x00"
    if value[0] & 0x80:  # DER 正整数最高位为 1 时要补一个 0x00
        value = b"\x00" + value
    return b"\x02" + _der_length(len(value)) + value


def _der_sequence(*parts: bytes) -> bytes:
    body = b"".join(parts)
    return b"\x30" + _der_length(len(body)) + body


def _rsa_private_key_der(parts: list[bytes]) -> bytes:
    """按 PKCS#1 把 RSA 私有参数编码成 DER(顺序固定, 见 RFC 3447)。"""

    modulus, exponent, private_exponent, prime1, prime2, exp1, exp2, coefficient = parts
    return _der_sequence(
        _der_integer(b"\x00"),  # version
        _der_integer(modulus),
        _der_integer(exponent),
        _der_integer(private_exponent),
        _der_integer(prime1),
        _der_integer(prime2),
        _der_integer(exp1),
        _der_integer(exp2),
        _der_integer(coefficient),
    )


def _pem(label: str, der: bytes) -> str:
    body = base64.b64encode(der).decode("ascii")
    lines = "\n".join(body[index:index + 64] for index in range(0, len(body), 64))
    return f"-----BEGIN {label}-----\n{lines}\n-----END {label}-----\n"


def _pem_from_cert_store() -> None:
    """只用 Windows 自带的 PowerShell 5.1 + .NET Framework 导出 PEM。

    证书是用传统 CSP 提供程序建的(见 ensure_certificate), 因此
    `RSACryptoServiceProvider.ExportParameters($true)` 可用——CNG 密钥在
    .NET Framework 下不支持导出参数, 这也是刻意选 CSP 的原因。
    拿到 RSA 参数后由 Python 编码成 PKCS#1 DER, 目标机器无需 openssl / PowerShell 7。
    """

    script = """
$ErrorActionPreference = 'Stop'
$cert = Get-ChildItem Cert:\\CurrentUser\\My | Where-Object { $_.Subject -eq 'CN=localhost' } |
    Sort-Object NotAfter -Descending | Select-Object -First 1
if (-not $cert) { throw 'My 存储里没有 CN=localhost 证书' }
$key = $cert.PrivateKey
if (-not ($key -is [System.Security.Cryptography.RSACryptoServiceProvider])) {
    throw '证书私钥不是 CSP 密钥; 请用 --renew-cert 重建证书'
}
$p = $key.ExportParameters($true)
[Convert]::ToBase64String($cert.RawData)
[Convert]::ToBase64String($p.Modulus)
[Convert]::ToBase64String($p.Exponent)
[Convert]::ToBase64String($p.D)
[Convert]::ToBase64String($p.P)
[Convert]::ToBase64String($p.Q)
[Convert]::ToBase64String($p.DP)
[Convert]::ToBase64String($p.DQ)
[Convert]::ToBase64String($p.InverseQ)
"""
    lines = [line.strip() for line in run_powershell(script).splitlines() if line.strip()]
    if len(lines) != 9:
        raise RuntimeError(f"期望 9 行证书/密钥参数, 实际 {len(lines)} 行")
    cert_der, *key_parts = (base64.b64decode(line) for line in lines)
    PEM_PATH.write_text(
        _pem("CERTIFICATE", cert_der) + _pem("RSA PRIVATE KEY", _rsa_private_key_der(key_parts)),
        encoding="ascii",
    )


def _pem_from_openssl() -> None:
    openssl = find_openssl()
    if openssl is None:
        raise RuntimeError("未找到 openssl")
    if not PFX_PATH.exists():
        raise RuntimeError(f"缺少 {PFX_PATH}")
    base = [str(openssl), "pkcs12", "-in", str(PFX_PATH),
            "-passin", f"pass:{PFX_PASSWORD}", "-nodes", "-out", str(PEM_PATH)]
    last_error = ""
    for extra in (["-legacy"], []):  # openssl 3.x 读 Windows 的 RC2 加密 PFX 需要 -legacy
        completed = subprocess.run(
            [*base, *extra], capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        if completed.returncode == 0:
            return
        last_error = completed.stderr.strip()
    raise RuntimeError(f"openssl 转换失败: {last_error}")


def _convert_with_pwsh() -> None:
    """用 PowerShell 7 的 .NET API 把 PFX 转成 PEM。"""

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
    """CPython 的 ssl 不支持直接读 PKCS#12, 需要准备 PEM(cert + key)。

    依次尝试三条路径, 第一条能用 Windows 自带组件完成, 保证换一台干净的 Windows 也能跑。
    """

    if PEM_PATH.exists() and (not PFX_PATH.exists() or PEM_PATH.stat().st_mtime >= PFX_PATH.stat().st_mtime):
        return

    failures: list[str] = []
    for name, build in (
        ("PowerShell 5.1 + .NET", _pem_from_cert_store),
        ("openssl", _pem_from_openssl),
        ("PowerShell 7", _convert_with_pwsh),
    ):
        try:
            build()
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            failures.append(f"{name}: {error}")
            continue
        if PEM_PATH.exists():
            print(f"已生成 PEM({name}): {PEM_PATH}")
            return

    raise RuntimeError("无法把证书转成 PEM;尝试过: " + " | ".join(failures))


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


def manifest_version(port: int = DEFAULT_PORT) -> str:
    root = ET.fromstring(render_manifest(port))
    element = root.find(f"{{{MANIFEST_NAMESPACE}}}Version")
    if element is None or not (element.text or "").strip():
        raise RuntimeError("manifest.xml 缺少 <Version>。")
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


# 靶场工作簿的最小 xlsx 部件。结构对齐官方 office-addin-dev-settings 附带的
# templates/ExcelWorkbookWithTaskPane.xlsx, 但由本脚本自行生成, 不引入外部二进制。
_XLSX_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml" />'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml" />'
    '<Override PartName="/xl/worksheets/sheet.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml" />'
    '<Override PartName="/xl/webextensions/taskpanes.xml" ContentType="application/vnd.ms-office.webextensiontaskpanes+xml" />'
    '<Override PartName="/xl/webextensions/webextension.xml" ContentType="application/vnd.ms-office.webextension+xml" />'
    "</Types>"
)

_XLSX_PARTS = {
    "_rels/.rels": (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="/xl/workbook.xml" Id="R717b618cfe814096" />'
        '<Relationship Type="http://schemas.microsoft.com/office/2011/relationships/webextensiontaskpanes" '
        'Target="/xl/webextensions/taskpanes.xml" Id="R5841e3d9dba14e5e" />'
        "</Relationships>"
    ),
    "xl/workbook.xml": (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<x:workbook xmlns:x="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<x:sheets><x:sheet name="Sheet1" sheetId="1" r:id="Rce87e4c0887747bb" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" /></x:sheets>'
        "</x:workbook>"
    ),
    "xl/_rels/workbook.xml.rels": (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="/xl/worksheets/sheet.xml" Id="Rce87e4c0887747bb" />'
        "</Relationships>"
    ),
    "xl/worksheets/sheet.xml": (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<x:worksheet xmlns:x="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><x:sheetData /></x:worksheet>'
    ),
    "xl/webextensions/taskpanes.xml": (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<wetp:taskpanes xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:wetp="http://schemas.microsoft.com/office/webextensions/taskpanes/2010/11">'
        '<wetp:taskpane dockstate="" visibility="1" width="350" row="1">'
        '<wetp:webextensionref '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:id="Rb105cb1fbb9747f6" />'
        "</wetp:taskpane></wetp:taskpanes>"
    ),
    "xl/webextensions/_rels/taskpanes.xml.rels": (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Type="http://schemas.microsoft.com/office/2011/relationships/webextension" '
        'Target="/xl/webextensions/webextension.xml" Id="Rb105cb1fbb9747f6" />'
        "</Relationships>"
    ),
    # storeType="Registry" 表示到开发者注册表目录里按 Id 找 manifest(见 DEVELOPER_KEY)。
    "xl/webextensions/webextension.xml": (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<we:webextension xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:we="http://schemas.microsoft.com/office/webextensions/webextension/2010/11" '
        f'id="{{{PLACEHOLDER_ADDIN_ID}}}">'
        f'<we:reference id="{PLACEHOLDER_ADDIN_ID}" version="1.0.0.0" store="developer" storeType="Registry" />'
        "<we:alternateReferences /><we:properties></we:properties><we:bindings />"
        '<we:snapshot xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" />'
        "</we:webextension>"
    ),
}


def build_sideload_workbook(port: int = DEFAULT_PORT) -> Path:
    """生成内嵌 webextension 引用的靶场工作簿。

    桌面版 Excel 的加载项是**文档级绑定**: 注册表开发者目录只提供 manifest 的来源,
    真正让 Ribbon 出现的是文档里 storeType="Registry" 的 webextension 引用。
    这与官方 `office-addin-dev-settings sideload` 生成临时工作簿再打开的做法同构。
    """

    addin_id = manifest_addin_id(port)
    version = manifest_version(port)
    webextension = (
        _XLSX_PARTS["xl/webextensions/webextension.xml"]
        .replace(PLACEHOLDER_ADDIN_ID, addin_id)
        .replace('version="1.0.0.0"', f'version="{version}"')
    )

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    target = DIST_DIR / SIDELOAD_WORKBOOK_NAME
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        # [Content_Types].xml 必须是包里的第一个条目
        archive.writestr("[Content_Types].xml", _XLSX_CONTENT_TYPES)
        for name, content in _XLSX_PARTS.items():
            archive.writestr(name, webextension if name.endswith("webextension.xml") else content)
    return target


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="启动 Excel 插件靶场。")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"HTTPS 端口, 默认 {DEFAULT_PORT}。")
    parser.add_argument("--no-launch", action="store_true", help="只起服务, 不自动打开靶场工作簿。")
    parser.add_argument("--renew-cert", action="store_true", help="强制重建 localhost 证书。")
    parser.add_argument("--skip-sideload", action="store_true", help="只起服务, 不注册加载项也不生成靶场工作簿。")
    parser.add_argument("--prepare-only", action="store_true", help="只做证书、注册与工作簿, 不启动服务。")
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

    workbook: Path | None = None
    if args.skip_sideload:
        print("已跳过加载项注册与靶场工作簿生成。")
    else:
        try:
            target, addin_id = sideload(args.port)
            print(f"已注册到 Excel 开发者目录: {addin_id} -> {target}")
            workbook = build_sideload_workbook(args.port)
            print(f"已生成靶场工作簿: {workbook}")
        except (OSError, RuntimeError) as error:
            print(f"错误: 注册加载项失败({error})。可用 --skip-sideload 只起服务。", file=sys.stderr)

    if workbook is None:
        print("未生成靶场工作簿, 仅提供服务。")
    elif args.no_launch or args.prepare_only:
        print(f"已跳过打开靶场工作簿(可手动打开: {workbook})。")
    else:
        os.startfile(workbook)  # noqa: S606 - Windows 专用, 交给默认程序打开生成的 xlsx
        print(f"已打开靶场工作簿: {workbook}")

    url = f"https://localhost:{args.port}/src/taskpane.html"
    print(f"\n服务地址: {url}")
    print("打开靶场工作簿后: 顶部 'Excel 靶场插件' 选项卡 -> 组 '登录靶场' -> '打开面板'。")
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
