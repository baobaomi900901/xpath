"""Hidden-widget integration checks; no real shooting range is launched."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import time
import tkinter as tk
import unittest
from unittest.mock import patch

from tools.range_launcher.app import Launcher
from tools.range_launcher.config import build_command, load_catalog

ROOT = Path(__file__).resolve().parents[1]


class LauncherInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="启动中心 UI ")
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "ranges.json"
        catalog = deepcopy(load_catalog(ROOT / "tools" / "ranges.json"))
        catalog["ranges"] = [item for item in catalog["ranges"] if item["id"] in ("win32", "powerbuilder")]
        self.path.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
        self.root = tk.Tk()
        self.root.withdraw()
        self.application = Launcher(self.root, ROOT, self.path)
        self.addCleanup(self.close_application)

    def close_application(self):
        if not self.application.closed:
            self.root.update_idletasks()
            self.application.close()

    def test_switching_to_exe_omits_saved_development_arguments(self):
        app = self.application
        app._show_item("powerbuilder")
        app.profile.set("开发模式（构建并启动）")
        app._profile_changed()
        app.option_vars["tools_path"][1].set(r"C:\工具 With Spaces")
        app.option_vars["skip_build"][1].set(True)
        app.profile.set("运行单文件 EXE")
        app._profile_changed()
        setting = app.settings["powerbuilder"]
        command, _ = build_command(app.items["powerbuilder"], setting["profile"], setting["values"], ROOT)
        self.assertEqual(command[-2:], ["--mode", "exe"])
        self.assertNotIn("--tools-path", command)
        self.assertNotIn("--skip-build", command)
        self.assertEqual(setting["values"]["tools_path"], r"C:\工具 With Spaces")

    def test_failed_start_does_not_block_other_checked_ranges(self):
        app = self.application
        for variable in app.checked.values():
            variable.set(True)
        def start(item_id, label, command, cwd):
            if item_id == "win32":
                raise OSError("测试：缺少产物")
            job = SimpleNamespace(label=label, log_path=self.path.parent / "job.log", state="running")
            app.runner.jobs[item_id] = job
            return job
        with patch.object(app.runner, "start", side_effect=start) as launch, patch.object(app.runner, "poll", return_value=[]):
            app.start_selected()
            deadline = time.monotonic() + 3
            while app.pending and time.monotonic() < deadline:
                self.root.update()
                time.sleep(0.01)
            self.assertFalse(app.pending)
            self.assertEqual(launch.call_count, 2)
        self.assertEqual(app.status_vars["win32"].get(), "启动失败")
        self.assertEqual(app.status_vars["powerbuilder"].get(), "执行中")
        self.assertIn("缺少产物", app.log.get("1.0", "end"))

    def test_repeated_click_does_not_queue_same_pending_task_twice(self):
        app = self.application
        app.checked["powerbuilder"].set(True)
        app.start_selected()
        app.start_selected()
        self.assertEqual(len(app.queue), 1)
        self.assertEqual(app.pending, {"powerbuilder"})

    def test_invalid_catalog_reload_preserves_last_valid_interface(self):
        self.path.write_text("{invalid", encoding="utf-8")
        app = self.application
        self.assertFalse(app.reload_catalog())
        self.assertEqual(set(app.items), {"win32", "powerbuilder"})
        app._show_item("powerbuilder")
        self.assertIn("--mode exe", app.preview.get("1.0", "end"))

    def test_editor_invalid_save_preserves_original_configuration(self):
        app = self.application
        original = self.path.read_bytes()
        app.edit_catalog()
        app.editor.withdraw()
        app.editor.text.delete("1.0", "end")
        app.editor.text.insert("1.0", '{"schema_version":1,"ranges":[{}]}')
        app.editor.save()
        self.assertEqual(self.path.read_bytes(), original)
        self.assertIn("保存失败", app.editor.status.get())

    def test_preferences_survive_reopening_without_launching(self):
        app = self.application
        state = self.path.parent / "state.json"
        app.state_path = state
        app.checked["powerbuilder"].set(True)
        self.root.update_idletasks()
        app.close()
        self.root = tk.Tk()
        self.root.withdraw()
        self.application = Launcher(self.root, ROOT, self.path, state)
        self.assertTrue(self.application.checked["powerbuilder"].get())
        self.assertFalse(self.application.checked["win32"].get())
        self.assertFalse(self.application.runner.jobs)

    def test_empty_profile_allowlist_hides_option_like_command_builder(self):
        catalog = load_catalog(self.path)
        item = next(item for item in catalog["ranges"] if item["id"] == "powerbuilder")
        item["options"][0]["profiles"] = []
        self.path.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
        self.application.reload_catalog()
        self.application._show_item("powerbuilder")
        self.assertNotIn("tools_path", self.application.option_vars)

    def test_restore_current_defaults_uses_config_and_keeps_range_checked(self):
        app = self.application
        app.checked["powerbuilder"].set(True)
        app._show_item("powerbuilder")
        app.profile.set("开发模式（构建并启动）")
        app._profile_changed()
        self.assertTrue(callable(getattr(app, "reset_current", None)))
        app.reset_current()
        self.assertEqual(app.settings["powerbuilder"]["profile"], "exe")
        self.assertTrue(app.checked["powerbuilder"].get())
        self.assertNotIn("tools_path", app.option_vars)

    @unittest.skipUnless((ROOT / "POWERBUILDER" / "dist" / "PowerBuilder靶场.exe").is_file(), "requires packaged PowerBuilder artifact")
    def test_real_launcher_check_runs_through_dashboard_without_opening_range(self):
        app = self.application
        app.clear_selection()
        app.checked["powerbuilder"].set(True)
        app._show_item("powerbuilder")
        app.option_vars["no_launch"][1].set(True)
        setting = app.settings["powerbuilder"]
        command, _ = build_command(app.items["powerbuilder"], setting["profile"], setting["values"], ROOT)
        self.assertIn("--no-launch", command)
        app.start_selected()
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            self.root.update()
            job = app.runner.jobs.get("powerbuilder")
            if job and job.state != "running":
                break
            time.sleep(0.02)
        job = app.runner.jobs.get("powerbuilder")
        self.assertIsNotNone(job)
        self.assertEqual(job.state, "succeeded")
        self.assertEqual(job.returncode, 0)
        self.assertIn("已验证 PowerBuilder 靶场", app.log.get("1.0", "end"))

    def test_editor_repairs_non_utf8_catalog_and_backs_up_original_bytes(self):
        original = load_catalog(self.path)
        app = self.application
        for encoding in ("utf-16", "gb18030"):
            with self.subTest(encoding=encoding):
                raw = json.dumps(original, ensure_ascii=False).encode(encoding)
                self.path.write_bytes(raw)
                self.assertFalse(app.reload_catalog())
                try:
                    app.edit_catalog()
                except UnicodeError as error:
                    self.fail(f"维护界面应可修正文件编码：{error}")
                app.editor.withdraw()
                self.assertEqual(app.editor.data(), original)
                self.assertIn("UTF-8", app.editor.status.get())
                self.assertEqual(self.path.read_bytes(), raw)
                app.editor.save()
                self.assertEqual(load_catalog(self.path), original)
                self.assertEqual(self.path.with_suffix(".json.bak").read_bytes(), raw)
                app.editor.destroy()
                app.editor = None


if __name__ == "__main__":
    unittest.main()
