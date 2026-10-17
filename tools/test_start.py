"""CLI routing and console-independent launcher process checks."""
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from unittest.mock import Mock, patch

from tools import start


class StartTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="启动中心 CLI ")
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)

    def test_default_launch_detaches_and_preserves_absolute_custom_config(self):
        config = self.directory / "自定义 ranges.json"
        with patch.object(start, "launch_background", create=True, return_value=0) as launch, \
                patch("tkinter.Tk") as window, patch("tools.range_launcher.app.Launcher"):
            self.assertEqual(start.main(["--config", str(config)]), 0)
        launch.assert_called_once_with(config.resolve())
        window.assert_not_called()

    def test_foreground_waits_for_window_without_spawning_another_process(self):
        with patch.object(start, "launch_background", create=True) as launch, \
                patch("tkinter.Tk") as window, patch("tools.range_launcher.app.Launcher"):
            self.assertEqual(start.main(["--foreground"]), 0)
        launch.assert_not_called()
        window.return_value.mainloop.assert_called_once_with()

    def test_checks_stay_synchronous(self):
        with patch.object(start, "launch_background", create=True) as launch, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(start.main(["--check"]), 0)
        launch.assert_not_called()
        self.assertIn('"passed": true', output.getvalue())

    def test_background_child_has_no_terminal_streams_and_reports_log(self):
        process = Mock(pid=123, wait=Mock(side_effect=subprocess.TimeoutExpired("launcher", 1)))
        with patch.object(start, "ROOT", self.directory), \
                patch("subprocess.Popen", return_value=process) as spawn, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(start.launch_background(self.directory / "配置 ranges.json"), 0)
        command = spawn.call_args.args[0]
        self.assertEqual(command[0], sys.executable)
        self.assertEqual(Path(command[1]), Path(start.__file__).resolve())
        self.assertIn("--foreground", command)
        self.assertEqual(command[-1], str(self.directory / "配置 ranges.json"))
        options = spawn.call_args.kwargs
        self.assertEqual(options["stdin"], subprocess.DEVNULL)
        self.assertEqual(options["stderr"], subprocess.STDOUT)
        self.assertTrue(options["close_fds"])
        self.assertTrue(options["stdout"].closed)
        self.assertTrue(Path(options["stdout"].name).is_file())
        self.assertIn("123", output.getvalue())
        self.assertIn(str(options["stdout"].name), output.getvalue())
        if os.name == "nt":
            self.assertTrue(options["creationflags"] & subprocess.DETACHED_PROCESS)
            self.assertTrue(options["creationflags"] & subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            self.assertTrue(options["start_new_session"])

    def test_early_child_exit_reports_failure_with_log_path(self):
        with patch.object(start, "ROOT", self.directory), \
                patch("subprocess.Popen", return_value=Mock(wait=Mock(return_value=7))), \
                contextlib.redirect_stderr(io.StringIO()) as output:
            self.assertEqual(start.launch_background(self.directory / "ranges.json"), 1)
        self.assertIn("7", output.getvalue())
        self.assertIn(".log", output.getvalue())
        self.assertIn("--foreground", output.getvalue())

    @unittest.skipUnless(os.name == "nt" and shutil.which("uv"), "requires Windows and uv")
    def test_uv_returns_while_real_hidden_tk_child_remains_without_console(self):
        # Hide the real Tk window and close only this test's child automatically.
        # Production entry point, widgets, uv and process creation stay real.
        (self.directory / "sitecustomize.py").write_text(textwrap.dedent('''
            import ctypes
            import json
            import os
            from pathlib import Path
            import tkinter as tk

            probe = Path(os.environ["LAUNCHER_PROCESS_PROBE"])
            class HiddenTk(tk.Tk):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.withdraw()
                def mainloop(self, *args, **kwargs):
                    (probe / "started.json").write_text(json.dumps({
                        "pid": os.getpid(),
                        "console": ctypes.windll.kernel32.GetConsoleWindow(),
                    }), encoding="utf-8")
                    self.after(4000, self.quit)
                    try:
                        super().mainloop(*args, **kwargs)
                    finally:
                        self.destroy()
                        (probe / "finished").touch()
            tk.Tk = HiddenTk
        '''), encoding="utf-8")
        env = os.environ.copy()
        env.update(PYTHONPATH=str(self.directory), PYTHONIOENCODING="utf-8",
                   LAUNCHER_PROCESS_PROBE=str(self.directory))
        parent = subprocess.run(
            [shutil.which("uv"), "run", "--no-python-downloads", str(Path(start.__file__).resolve())],
            cwd=str(start.ROOT), env=env, capture_output=True, text=True, encoding="utf-8", timeout=12,
        )
        self.assertEqual(parent.returncode, 0, parent.stdout + parent.stderr)
        deadline = time.monotonic() + 3
        while not (self.directory / "started.json").exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        started = json.loads((self.directory / "started.json").read_text(encoding="utf-8"))
        try:
            self.assertIn(str(started["pid"]), parent.stdout)
            self.assertEqual(started["console"], 0)
            self.assertFalse((self.directory / "finished").exists(), "uv waited for the GUI child")
        finally:
            deadline = time.monotonic() + 6
            while not (self.directory / "finished").exists() and time.monotonic() < deadline:
                time.sleep(0.05)
        self.assertTrue((self.directory / "finished").exists(), "test child did not close normally")


if __name__ == "__main__":
    unittest.main()
