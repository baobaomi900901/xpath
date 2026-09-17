"""卸载 Excel 插件靶场: 移除 sideload manifest, 可选移除 localhost 证书。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from start_excel_addin import (  # noqa: E402 - 复用启动器的常量与 PowerShell 桥
    CERT_DIR,
    CER_PATH,
    PEM_PATH,
    PFX_PATH,
    SIDELOAD_NAME,
    WEF_DIR,
    configure_output,
    run_powershell,
)


def remove_sideload() -> None:
    target = WEF_DIR / SIDELOAD_NAME
    if not target.exists():
        print(f"sideload manifest 不存在, 无需移除: {target}")
        return
    try:
        target.unlink()
    except OSError as error:
        raise RuntimeError(
            f"删除失败({error})。请完全退出 Excel 后重试, 或手动删除: {target}"
        ) from error
    print(f"已移除 sideload manifest: {target}")


def remove_certificate() -> None:
    script = """
$ErrorActionPreference = 'Continue'
Get-ChildItem Cert:\\CurrentUser\\Root | Where-Object { $_.Subject -eq 'CN=localhost' } | Remove-Item -Force
Get-ChildItem Cert:\\CurrentUser\\My | Where-Object { $_.Subject -eq 'CN=localhost' } | Remove-Item -Force
'removed'
"""
    print(run_powershell(script))
    for path in (PFX_PATH, CER_PATH, PEM_PATH):
        path.unlink(missing_ok=True)
    if CERT_DIR.exists() and not any(CERT_DIR.iterdir()):
        CERT_DIR.rmdir()
    print("已移除 localhost 证书。")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="卸载 Excel 插件靶场。")
    parser.add_argument("--keep-cert", action="store_true", help="保留 localhost 证书。")
    parser.add_argument("--no-sideload", action="store_true", help="只处理证书, 不删除 sideload manifest。")
    return parser.parse_args()


def main() -> int:
    configure_output()
    args = parse_args()

    if args.no_sideload:
        print("已跳过 sideload 清理。")
    else:
        remove_sideload()

    if args.keep_cert:
        print("已保留 localhost 证书。")
    else:
        remove_certificate()

    print("\n请完全退出并重新打开 Excel, 'Excel 靶场插件' 选项卡才会消失。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
    except Exception as error:  # noqa: BLE001 - CLI 顶层兜底
        print(f"错误: {error}", file=sys.stderr)
        raise SystemExit(1)
