"""测试 web.create 的 load_timeout 与 stop_if_timeout 参数。

靶场页面：http://localhost:7199/slow-load-30s.html
"""

from pathlib import Path

from uipilot import web

BASE_URL = "http://localhost:7199"
PAGE_URL = f"{BASE_URL}/slow-load-30s.html"
# 静态页文件位置：靶场/web/public/slow-load-30s.html


def test_timeout_continue_loading():
    """load_timeout=20，stop_if_timeout=False（默认）：超时抛 UIAError，但不停止加载。"""
    print("=== stop_if_timeout=False ===")
    try:
        web.create(PAGE_URL, "chrome", load_timeout=20, stop_if_timeout=False)
        print("未抛出异常（不符合预期）")
    except Exception as exc:
        print(f"捕获异常: {type(exc).__name__}: {exc}")


def test_timeout_stop_loading():
    """load_timeout=20，stop_if_timeout=True：超时抛 UIAError，并停止加载。"""
    print("=== stop_if_timeout=True ===")
    try:
        web.create(PAGE_URL, "chrome", load_timeout=20, stop_if_timeout=True)
        print("未抛出异常（不符合预期）")
    except Exception as exc:
        print(f"捕获异常: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    print("测试页面:", PAGE_URL)
    test_timeout_continue_loading()
    print()
    test_timeout_stop_loading()
