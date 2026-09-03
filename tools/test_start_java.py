from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from tools import start_java


class VersionSelectorTests(unittest.TestCase):
    def test_selector_redraws_in_place_after_clearing_once(self) -> None:
        keys = ["enter", *("down" for _ in range(5)), "enter"]
        output = io.StringIO()

        with (
            patch.object(start_java, "clear_screen") as clear_screen,
            patch.object(start_java, "read_key", side_effect=keys),
            redirect_stdout(output),
        ):
            selected = start_java.select_versions()

        self.assertEqual(["8"], selected)
        clear_screen.assert_called_once_with()
        self.assertIn("\x1b[H", output.getvalue())


if __name__ == "__main__":
    unittest.main()
