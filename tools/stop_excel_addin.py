"""卸载 Excel 插件靶场: 移除 sideload manifest, 可选移除 localhost 证书。"""

from __future__ import annotations

import argparse
import subprocess
import sys
import winreg
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from start_excel_addin import (  # noqa: E402 - 复用启动器的常量与 PowerShell 桥
    CERT_DIR,
    CER_PATH,
    DEVELOPER_KEY,
    DIST_DIR,
    PEM_PATH,
    PFX_PATH,
    SIDELOAD_NAME,
    SIDELOAD_WORKBOOK_NAME,
    WEF_DIR,
    configure_output,
    manifest_addin_id,
)


def remove_sideload() -> None:
    target = WEF_DIR / SIDELOAD_NAME

    # 先摘掉开发者目录里的注册项: 这才是 Excel 认的入口。
    try:
        addin_id = manifest_addin_id()
    except Exception:  # noqa: BLE001 - manifest 缺失也要能继续清理文件和注册表
        addin_id = None
    if addin_id:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, DEVELOPER_KEY, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, addin_id)
            print(f"已从 Excel 开发者目录移除: {addin_id}")
        except FileNotFoundError:
            print(f"开发者目录中没有该插件, 无需移除: {addin_id}")

    if not target.exists():
        print(f"sideload manifest 不存在, 无需移除: {target}")
    else:
        try:
            target.unlink()
        except OSError as error:
            raise RuntimeError(
                f"删除失败({error})。请完全退出 Excel 后重试, 或手动删除: {target}"
            ) from error
        print(f"已移除 sideload manifest: {target}")

    # 靶场工作簿是可再生成的产物; Excel 打开后还会留下 ~$ 锁文件, 一并清掉。
    if DIST_DIR.exists():
        for path in (DIST_DIR / SIDELOAD_WORKBOOK_NAME, *DIST_DIR.glob(f"~${SIDELOAD_WORKBOOK_NAME}")):
            if path.exists():
                path.unlink(missing_ok=True)
                print(f"已移除 {path.name}")
        if not any(DIST_DIR.iterdir()):
            DIST_DIR.rmdir()


def remove_certificate() -> None:
    # Root 存储的增删在非交互会话下都会被 "UI is not allowed" 拒绝, 与安装时对称, 统一用 certutil。
    for store in ("Root", "My"):
        completed = subprocess.run(
            ["certutil.exe", "-user", "-delstore", store, "localhost"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        print(f"  {store} 存储: {'已清理 CN=localhost' if completed.returncode == 0 else '无需清理'}")
    for path in (PFX_PATH, CER_PATH, PEM_PATH):
        path.unlink(missing_ok=True)
    if CERT_DIR.exists() and not any(CERT_DIR.iterdir()):
        CERT_DIR.rmdir()
    print("已移除 localhost 证书材料。")


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
