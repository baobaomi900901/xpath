"""测试网页原生对话框处理（alert / confirm / prompt）。

靶场页面：http://localhost:7199/web-dialog-test
"""

import uipilot

BASE_URL = "http://localhost:7199"
PAGE_URL = f"{BASE_URL}/web-dialog-test"


def test_alert_accept():
    """Alert：仅确认按钮，调用 accept 关闭。"""
    print("=== alert → web.dialog.accept ===")
    with uipilot.Client(timeout=5) as client:
        client.inner.web_navigate(PAGE_URL, mode="chrome", timeout_ms=20_000).raise_for_error()
        # TODO: 点击 id="btn-alert"
        client.inner.web_dialog_accept(timeout_ms=5000).raise_for_error()
    print("Alert 已确认")


def test_confirm_accept():
    """Confirm：点击确定。"""
    print("=== confirm → web.dialog.accept ===")
    with uipilot.Client(timeout=5) as client:
        client.inner.web_navigate(PAGE_URL, mode="chrome", timeout_ms=20_000).raise_for_error()
        # TODO: 点击 id="btn-confirm"
        client.inner.web_dialog_accept(timeout_ms=5000).raise_for_error()
    print("Confirm 已确认")


def test_confirm_dismiss():
    """Confirm：点击取消。"""
    print("=== confirm → web.dialog.dismiss ===")
    with uipilot.Client(timeout=5) as client:
        client.inner.web_navigate(PAGE_URL, mode="chrome", timeout_ms=20_000).raise_for_error()
        # TODO: 点击 id="btn-confirm"
        client.inner.web_dialog_dismiss(timeout_ms=5000).raise_for_error()
    print("Confirm 已取消")


def test_prompt_with_text():
    """Prompt：输入文本并确认。"""
    print("=== prompt → web.dialog.prompt ===")
    with uipilot.Client(timeout=5) as client:
        client.inner.web_navigate(PAGE_URL, mode="chrome", timeout_ms=20_000).raise_for_error()
        # TODO: 点击 id="btn-prompt"
        client.inner.web_dialog_prompt("UiPilot", timeout_ms=5000).raise_for_error()
    print("Prompt 已输入并确认")


def test_prompt_dismiss():
    """Prompt：点击取消。"""
    print("=== prompt → web.dialog.dismiss ===")
    with uipilot.Client(timeout=5) as client:
        client.inner.web_navigate(PAGE_URL, mode="chrome", timeout_ms=20_000).raise_for_error()
        # TODO: 点击 id="btn-prompt"
        client.inner.web_dialog_dismiss(timeout_ms=5000).raise_for_error()
    print("Prompt 已取消")


if __name__ == "__main__":
    print("测试页面:", PAGE_URL)
    test_alert_accept()
