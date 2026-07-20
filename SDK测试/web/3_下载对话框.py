"""测试 handle_save_dialog() 处理网页下载对话框。

靶场页面：http://localhost:7199/download-dialog-test
"""

from pathlib import Path

from uipilot import web

BASE_URL = "http://localhost:7199"
PAGE_URL = f"{BASE_URL}/download-dialog-test"
SAVE_DIR = Path(__file__).resolve().parent / "downloads"
SAVE_DIR.mkdir(exist_ok=True)


def test_save_dialog_ok():
    """点击下载按钮，handle_save_dialog 确认保存。"""
    print("=== handle_save_dialog(dialog_result='ok') ===")
    print("页面:", PAGE_URL)
    print("保存目录:", SAVE_DIR)

    browser = web.create(PAGE_URL, "chrome")

    # TODO: 点击下载按钮，例如 id="btn-download-blob-txt"
    # browser.find_element(...).click()

    saved_path = web.handle_save_dialog(
        str(SAVE_DIR),
        dialog_result="ok",
        mode="chrome",
        file_name="notes.txt",
        wait_complete=True,
    )
    print("保存路径:", saved_path)


def test_save_dialog_cancel():
    """点击下载按钮，handle_save_dialog 取消保存。"""
    print("=== handle_save_dialog(dialog_result='cancel') ===")

    browser = web.create(PAGE_URL, "chrome")

    # TODO: 点击下载按钮

    saved_path = web.handle_save_dialog(
        str(SAVE_DIR),
        dialog_result="cancel",
        mode="chrome",
    )
    print("结果:", saved_path)


if __name__ == "__main__":
    test_save_dialog_ok()
