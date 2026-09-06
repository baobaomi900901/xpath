from __future__ import annotations

import argparse
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
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

    def test_main_does_not_create_or_reexec_a_repo_local_python_environment(self) -> None:
        args = argparse.Namespace(
            versions=["8"],
            skip_build=True,
            force_build=False,
            no_launch=True,
        )

        with (
            patch.object(start_java, "configure_output"),
            patch.object(start_java, "ensure_local_environment", create=True) as ensure_environment,
            patch.object(start_java, "parse_args", return_value=args),
            patch.object(start_java, "validate_artifact", return_value=Path("shooting-range-8.jar")),
            redirect_stdout(io.StringIO()),
        ):
            result = start_java.main()

        self.assertEqual(0, result)
        ensure_environment.assert_not_called()


if __name__ == "__main__":
    unittest.main()
