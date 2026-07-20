"""测试 handle_upload_dialog() 处理网页上传对话框。

靶场页面：http://localhost:7199/upload-dialog-test
"""

from pathlib import Path

from uipilot import web

BASE_URL = "http://localhost:7199"
PAGE_URL = f"{BASE_URL}/upload-dialog-test"
SAMPLES_DIR = Path(__file__).resolve().parents[2] / "靶场/web/public/samples"


def test_upload_dialog_ok():
    """点击上传控件，handle_upload_dialog 确认选择文件。"""
    print("=== handle_upload_dialog(dialog_result='ok') ===")
    print("页面:", PAGE_URL)

    upload_file = SAMPLES_DIR / "demo.txt"
    print("上传文件:", upload_file)

    browser = web.create(PAGE_URL, "chrome")

    # TODO: 点击上传控件，例如 id="input-upload-single"
    # browser.find_element(...).click()

    web.handle_upload_dialog(
        str(upload_file),
        dialog_result="ok",
        mode="chrome",
    )
    print("上传完成")


def test_upload_dialog_multiple():
    """多文件上传测试。"""
    print("=== handle_upload_dialog 多文件 ===")

    files = [
        str(SAMPLES_DIR / "demo.txt"),
        str(SAMPLES_DIR / "report.csv"),
    ]

    browser = web.create(PAGE_URL, "chrome")

    # TODO: 点击 id="input-upload-multiple"

    web.handle_upload_dialog(files, dialog_result="ok", mode="chrome")
    print("多文件上传完成")


def test_upload_dialog_cancel():
    """点击上传控件，handle_upload_dialog 取消选择。"""
    print("=== handle_upload_dialog(dialog_result='cancel') ===")

    browser = web.create(PAGE_URL, "chrome")

    # TODO: 点击上传控件

    web.handle_upload_dialog(
        str(SAMPLES_DIR / "demo.txt"),
        dialog_result="cancel",
        mode="chrome",
    )
    print("已取消上传")


if __name__ == "__main__":
    test_upload_dialog_ok()
