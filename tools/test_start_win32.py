from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from tools import start_win32


class Win32BackendTests(unittest.TestCase):
    def test_random_backend_is_selectable_with_the_existing_uia_version(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            start_win32.draw_backend_selector({"uia", "uia-random"}, 0, "")
        with patch("sys.argv", ["start_win32.py", "--backends", "uia", "uia-random"]), redirect_stderr(output):
            try:
                args = start_win32.parse_args()
            except SystemExit:
                self.fail("The launcher must accept the randomized UIA backend")
        self.assertEqual(["uia", "uia-random"], args.backends)
        self.assertIn("UIA 版（标准 Win32 控件_随机表单）", output.getvalue())
        self.assertEqual("win32-shooting-range-uia-random.exe",
                         start_win32.executable_path("Release", "uia-random").name)

    def test_selector_can_select_both_uia_variants(self) -> None:
        keys = ["enter", "down", "enter", *("down" for _ in range(len(start_win32.BACKENDS) - 1)), "enter"]
        output = io.StringIO()
        with (
            patch.object(start_win32, "clear_screen"),
            patch.object(start_win32, "read_key", side_effect=keys),
            redirect_stdout(output),
        ):
            selected = start_win32.select_backends()
        self.assertEqual(["uia", "uia-no-pane"], selected)
        self.assertIn("UIA 版（标准 Win32 控件_表单item 无 Pane 版本）", output.getvalue())

    def test_no_pane_backend_has_its_own_executable(self) -> None:
        with patch("sys.argv", ["start_win32.py", "--backends", "uia", "uia-no-pane"]), redirect_stderr(io.StringIO()):
            try:
                args = start_win32.parse_args()
            except SystemExit:
                self.fail("The launcher must accept the uia-no-pane backend")
        self.assertEqual(["uia", "uia-no-pane"], args.backends)
        self.assertEqual("win32-shooting-range-uia-no-pane.exe",
                         start_win32.executable_path("Release", "uia-no-pane").name)
        self.assertNotEqual(start_win32.executable_path("Release", "uia"),
                            start_win32.executable_path("Release", "uia-no-pane"))


if __name__ == "__main__":
    unittest.main()
