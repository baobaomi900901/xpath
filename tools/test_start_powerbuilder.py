from pathlib import Path
from contextlib import ExitStack, redirect_stdout
import io
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch
from tools import start_win32 as console

try:
    from tools import start_powerbuilder as launcher
except ImportError:
    launcher = None


class PowerBuilderLauncherTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(launcher, "PowerBuilder launcher has not been implemented")

    def test_explicit_tools_path_never_falls_back(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"
            with self.assertRaisesRegex(FileNotFoundError, "OrcaScript"):
                launcher.resolve_tools(missing)

    def test_runtime_requires_matching_core_and_accessibility_files(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            (runtime / "pbvm.dll").touch()
            with self.assertRaisesRegex(FileNotFoundError, "pbacc.dll"):
                launcher.validate_runtime(runtime, version_reader=lambda _: launcher.RUNTIME_VERSION)
            for name in ("pbacc.dll", "PBAccessibility.dll", "pbdwe.dll"):
                (runtime / name).touch()
            with self.assertRaisesRegex(RuntimeError, "版本"):
                launcher.validate_runtime(runtime, version_reader=lambda _: "25.1.0.6430")

    def test_prepare_build_preserves_unicode_and_enables_accessibility(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "src"
            source.mkdir()
            (source / "pb_range.sra").write_text("$PBExportHeader$pb_range.sra\n// 表单控件\n", encoding="utf-8")
            output = root / "build" / "Release"
            script = launcher.prepare_build(source, output, root / "Runtime with spaces")
            self.assertIn("表单控件", (output / "pb_range.sra").read_text(encoding="utf-16"))
            self.assertIn("Accessibility=1", (output / "pb.ini").read_text(encoding="utf-8"))
            self.assertIn("scc refresh target", script.read_text(encoding="utf-16"))
            self.assertIn("pb_range.sra", (output / "pb_range.pbg").read_text())
            self.assertIn("Runtime with spaces", (output / "PowerBuilderShootingRange.xml").read_text())
            self.assertEqual("Application", ET.parse(output / "PowerBuilderShootingRange.xml").getroot().tag)

    def test_compiler_error_is_not_reported_as_a_successful_build(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with patch.object(launcher.subprocess, "run") as run:
                run.return_value.returncode = 1
                run.return_value.stdout = b"C0001: syntax error"
                with self.assertRaisesRegex(RuntimeError, "build.log"):
                    launcher.run_compiler(Path("orcascr250.exe"), output / "build.orca", output)
            self.assertIn("syntax error", (output / "build.log").read_text(encoding="utf-8"))

    def test_skip_build_does_not_require_compiler(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with patch.object(launcher, "BUILD_DIR", output), patch.object(launcher, "resolve_tools") as resolve:
                with self.assertRaisesRegex(FileNotFoundError, "PowerBuilderShootingRange.exe"):
                    launcher.main(["--skip-build", "--no-launch"])
                resolve.assert_not_called()

    def test_skip_build_validates_an_explicit_runtime_path(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            for name in (launcher.EXE_NAME, "pb_range.pbd", "pb.ini", "PowerBuilderShootingRange.xml"):
                (output / name).touch()
            with patch.object(launcher, "BUILD_DIR", output), patch.object(launcher, "resolve_runtime", side_effect=FileNotFoundError("missing Runtime")) as resolve:
                with self.assertRaisesRegex(FileNotFoundError, "missing Runtime"):
                    launcher.main(["--skip-build", "--no-launch", "--runtime-path", str(output / "missing")])
                resolve.assert_called_once_with(output / "missing")

    def launcher_environment(self, root, keys):
        """Replace external build/process boundaries, retaining real CLI routing."""
        output = root / "build" / "Release"
        output.mkdir(parents=True)
        for name in (launcher.EXE_NAME, "pb_range.pbd"):
            (output / name).touch()
        launcher.write_runtime_config(output, root / "Runtime")
        packaged = root / "dist" / "PowerBuilder靶场.exe"
        packaged.parent.mkdir()
        packaged.touch()
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(launcher, "RANGE_DIR", root))
        stack.enter_context(patch.object(launcher, "BUILD_DIR", output))
        mocks = {}
        for name in ("resolve_tools", "resolve_runtime", "file_version", "prepare_build", "run_compiler"):
            mocks[name] = stack.enter_context(patch.object(launcher, name))
        mocks["resolve_tools"].return_value = root / "orcascr250.exe"
        mocks["resolve_runtime"].return_value = root / "Runtime"
        mocks["file_version"].return_value = launcher.RUNTIME_VERSION
        mocks["input"] = stack.enter_context(patch("builtins.input", return_value="1"))
        mocks["read_key"] = stack.enter_context(patch.object(console, "read_key", side_effect=keys))
        mocks["clear_screen"] = stack.enter_context(patch.object(console, "clear_screen"))
        mocks["output"] = io.StringIO()
        stack.enter_context(redirect_stdout(mocks["output"]))
        stack.enter_context(patch.object(launcher.sys.stdin, "isatty", return_value=True))
        stack.enter_context(patch.object(launcher.sys.stdout, "isatty", return_value=True))
        mocks["popen"] = stack.enter_context(patch.object(launcher.subprocess, "Popen"))
        mocks["popen"].return_value.poll.return_value = None
        stack.enter_context(patch.object(launcher.time, "sleep"))
        return output, packaged, mocks

    def test_menu_option_one_runs_packaged_exe_without_build_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            _, packaged, mocks = self.launcher_environment(Path(directory), ["enter", "down", "down", "enter"])
            self.assertEqual(launcher.main([]), 0)
            self.assertEqual(mocks["read_key"].call_count, 4)
            mocks["input"].assert_not_called()
            self.assertEqual(mocks["popen"].call_args.args[0], [str(packaged)])
            self.assertEqual(mocks["popen"].call_args.kwargs["cwd"], packaged.parent)
            mocks["resolve_tools"].assert_not_called()
            mocks["resolve_runtime"].assert_not_called()
            mocks["run_compiler"].assert_not_called()

    def test_menu_option_two_builds_and_runs_development_exe(self):
        with tempfile.TemporaryDirectory() as directory:
            output, _, mocks = self.launcher_environment(Path(directory), ["down", "space", "down", "enter"])
            self.assertEqual(launcher.main([]), 0)
            self.assertEqual(mocks["read_key"].call_count, 4)
            mocks["input"].assert_not_called()
            mocks["run_compiler"].assert_called_once()
            self.assertEqual(mocks["popen"].call_args.args[0], [str(output / launcher.EXE_NAME)])

    def test_menu_requires_a_selection_before_confirming(self):
        with tempfile.TemporaryDirectory() as directory:
            keys = ["up", "enter", "down", "enter", "up", "enter"]
            _, packaged, mocks = self.launcher_environment(Path(directory), keys)
            self.assertEqual(launcher.main([]), 0)
            self.assertEqual(mocks["read_key"].call_count, len(keys))
            self.assertIn("请选择一种启动方式", mocks["output"].getvalue())
            self.assertEqual(mocks["popen"].call_args.args[0], [str(packaged)])

    def test_selecting_development_replaces_exe_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            keys = ["enter", "down", "space", "down", "enter"]
            output, _, mocks = self.launcher_environment(Path(directory), keys)
            self.assertEqual(launcher.main([]), 0)
            mocks["run_compiler"].assert_called_once()
            self.assertEqual(mocks["popen"].call_args.args[0], [str(output / launcher.EXE_NAME)])

    def test_escape_cancels_without_building_or_launching(self):
        with tempfile.TemporaryDirectory() as directory:
            _, _, mocks = self.launcher_environment(Path(directory), ["escape"])
            self.assertEqual(launcher.main([]), 0)
            mocks["resolve_tools"].assert_not_called()
            mocks["popen"].assert_not_called()
            self.assertIn("已取消", mocks["output"].getvalue())

    def test_noninteractive_menu_explains_explicit_modes(self):
        with tempfile.TemporaryDirectory() as directory:
            _, _, mocks = self.launcher_environment(Path(directory), [])
            with patch.object(launcher.sys.stdin, "isatty", return_value=False):
                with self.assertRaisesRegex(RuntimeError, "--mode exe.*--mode dev"):
                    launcher.main([])
            mocks["read_key"].assert_not_called()
            mocks["popen"].assert_not_called()

    def test_packaged_exe_can_be_checked_without_prompt_or_runtime_installation(self):
        with tempfile.TemporaryDirectory() as directory:
            _, _, mocks = self.launcher_environment(Path(directory), [])
            self.assertEqual(launcher.main(["--mode", "exe", "--no-launch"]), 0)
            mocks["input"].assert_not_called()
            mocks["read_key"].assert_not_called()
            mocks["popen"].assert_not_called()
            mocks["resolve_tools"].assert_not_called()
            mocks["resolve_runtime"].assert_not_called()

    def test_missing_package_explains_how_to_build_it(self):
        with tempfile.TemporaryDirectory() as directory:
            _, packaged, _ = self.launcher_environment(Path(directory), [])
            packaged.unlink()
            with self.assertRaisesRegex(FileNotFoundError, "package_powerbuilder.py"):
                launcher.main(["--mode", "exe"])


if __name__ == "__main__":
    unittest.main()
