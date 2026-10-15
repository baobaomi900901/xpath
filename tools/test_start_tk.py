import contextlib
import io
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

from tools import start_tk


class LauncherTests(unittest.TestCase):
    def test_check_uses_current_interpreter_and_absolute_repo_cwd(self):
        with patch.object(start_tk.subprocess, "run", return_value=Mock(returncode=0)) as run:
            self.assertEqual(0, start_tk.main(["--no-launch"]))
        self.assertEqual([sys.executable, "-m", "TK", "--check"], run.call_args.args[0])
        self.assertEqual(start_tk.REPO_ROOT, run.call_args.kwargs["cwd"])
        self.assertTrue(start_tk.REPO_ROOT.is_absolute())

    def test_failed_environment_check_does_not_launch(self):
        with patch.object(start_tk.subprocess, "run", return_value=Mock(returncode=3)), \
                patch.object(start_tk.subprocess, "Popen") as launch:
            self.assertEqual(3, start_tk.main([]))
        launch.assert_not_called()

    def test_foreground_returns_the_app_exit_code(self):
        with patch.object(start_tk.subprocess, "run", side_effect=[
            Mock(returncode=0), Mock(returncode=7),
        ]) as run:
            self.assertEqual(7, start_tk.main(["--foreground"]))
        self.assertEqual([sys.executable, "-m", "TK"], run.call_args.args[0])

    def test_background_launch_checks_early_exit(self):
        process = Mock(pid=123, wait=Mock(side_effect=subprocess.TimeoutExpired("TK", 1)))
        with patch.object(start_tk.subprocess, "run", return_value=Mock(returncode=0)), \
                patch.object(start_tk.subprocess, "Popen", return_value=process) as launch, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(0, start_tk.main([]))
        self.assertIn("123", output.getvalue())
        self.assertEqual([sys.executable, "-m", "TK"], launch.call_args.args[0])
        self.assertEqual(start_tk.REPO_ROOT, launch.call_args.kwargs["cwd"])

    def test_immediate_exit_is_reported_as_failure_even_with_zero_exit_code(self):
        for exit_code in (0, 1):
            with self.subTest(exit_code=exit_code), \
                    patch.object(start_tk.subprocess, "run", return_value=Mock(returncode=0)), \
                    patch.object(start_tk.subprocess, "Popen", return_value=Mock(wait=Mock(return_value=exit_code))), \
                    contextlib.redirect_stderr(io.StringIO()) as output:
                self.assertEqual(1, start_tk.main([]))
                self.assertIn("退出", output.getvalue())


if __name__ == "__main__":
    unittest.main()
