import copy
import contextlib
import json
from pathlib import Path
import subprocess
import sys
import shutil
import time
import unittest
from uuid import uuid4
from unittest.mock import patch

from tools.range_launcher.config import (
    build_command, default_values, load_catalog, save_catalog, validate_catalog,
)
from tools.range_launcher.runner import Runner


@contextlib.contextmanager
def temporary_directory(prefix=".range-test-"):
    # Python 3.13+ mkdtemp's Windows 0o700 ACL excludes restricted sandbox
    # tokens. Normal mkdir inherits the writable workspace's permissions.
    folder = Path(__file__).resolve().parent / (prefix + uuid4().hex)
    folder.mkdir()
    try:
        yield str(folder)
    finally:
        shutil.rmtree(str(folder))


def catalog():
    return {
        "schema_version": 1,
        "ranges": [{
            "id": "sample", "label": "示例靶场", "category": "桌面",
            "description": "A launcher fixture", "command": ["{python}", "{root}/script.py"],
            "cwd": ".", "profiles": [
                {"id": "run", "label": "运行", "args": ["--foreground"]},
                {"id": "check", "label": "检查", "args": ["--check"]},
            ], "default_profile": "run", "options": [
                {"id": "version", "label": "版本", "type": "choice", "flag": "--version",
                 "default": "v1", "required": True, "choices": [
                     {"value": "v1", "label": "第一版"}, {"value": "v2", "label": "第二版"},
                 ]},
                {"id": "features", "label": "功能", "type": "multi", "flag": "--features",
                 "default": ["a"], "choices": [
                     {"value": "a", "label": "甲"}, {"value": "b", "label": "乙"},
                 ]},
                {"id": "title", "label": "标题", "type": "text", "flag": "--title",
                 "default": "默认标题", "profiles": ["run"]},
                {"id": "verbose", "label": "详细日志", "type": "bool", "flag": "--verbose",
                 "default": False},
                {"id": "port", "label": "端口", "type": "integer", "flag": "--port",
                 "default": 8080, "min": 1, "max": 65535},
            ],
        }],
    }


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.data = catalog()
        self.item = self.data["ranges"][0]

    def test_valid_catalog_and_independent_defaults(self):
        self.assertIsNone(validate_catalog(self.data))
        values = default_values(self.item)
        self.assertEqual(values["version"], "v1")
        values["features"].append("b")
        self.assertEqual(self.item["options"][1]["default"], ["a"])

    def test_empty_catalog_is_valid_for_bootstrap(self):
        self.assertIsNone(validate_catalog({"schema_version": 1, "ranges": []}))

    def test_missing_and_duplicate_range_ids_are_useful_errors(self):
        del self.item["id"]
        with self.assertRaisesRegex(ValueError, "id"):
            validate_catalog(self.data)
        self.data = catalog()
        self.data["ranges"].append(copy.deepcopy(self.data["ranges"][0]))
        with self.assertRaisesRegex(ValueError, "sample"):
            validate_catalog(self.data)

    def test_duplicate_option_profile_and_choice_ids_rejected(self):
        for target in ("options", "profiles"):
            with self.subTest(target=target):
                data = catalog()
                data["ranges"][0][target].append(copy.deepcopy(data["ranges"][0][target][0]))
                with self.assertRaisesRegex(ValueError, "duplicate|重复"):
                    validate_catalog(data)
        self.item["options"][0]["choices"].append({"value": "v1", "label": "again"})
        with self.assertRaisesRegex(ValueError, "v1"):
            validate_catalog(self.data)

    def test_unknown_profiles_rejected_in_defaults_and_allowlists(self):
        self.item["default_profile"] = "missing"
        with self.assertRaisesRegex(ValueError, "missing"):
            validate_catalog(self.data)
        self.item["default_profile"] = "run"
        self.item["options"][0]["profiles"] = ["missing"]
        with self.assertRaisesRegex(ValueError, "missing"):
            validate_catalog(self.data)

    def test_duplicate_profile_and_choice_labels_rejected_for_ui_mapping(self):
        self.item["profiles"][1]["label"] = self.item["profiles"][0]["label"]
        with self.assertRaisesRegex(ValueError, "label"):
            validate_catalog(self.data)
        self.data = catalog()
        choices = self.data["ranges"][0]["options"][0]["choices"]
        choices[1]["label"] = choices[0]["label"]
        with self.assertRaisesRegex(ValueError, "label"):
            validate_catalog(self.data)

    def test_invalid_schema_types_and_commands_rejected(self):
        cases = [("schema_version", True), ("schema_version", 2), ("ranges", {})]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                data = catalog()
                data[key] = value
                with self.assertRaises(ValueError):
                    validate_catalog(data)
        for command in ([], "python script.py", ["python", None]):
            with self.subTest(command=command):
                self.item["command"] = command
                with self.assertRaisesRegex(ValueError, "command"):
                    validate_catalog(self.data)

    def test_invalid_defaults_rejected_with_option_id(self):
        for index, value in ((0, "missing"), (1, ["missing"]), (2, 3), (3, "false"),
                             (4, 0), (4, 70000), (4, True), (4, "8080")):
            with self.subTest(index=index, value=value):
                data = catalog()
                option = data["ranges"][0]["options"][index]
                option["default"] = value
                with self.assertRaisesRegex(ValueError, option["id"]):
                    validate_catalog(data)

    def test_required_multi_and_invalid_bounds_rejected(self):
        option = self.item["options"][1]
        option.update(required=True, default=[])
        with self.assertRaisesRegex(ValueError, "features"):
            validate_catalog(self.data)
        option.update(required=False)
        self.item["options"][4].update(min=100, max=10)
        with self.assertRaisesRegex(ValueError, "port"):
            validate_catalog(self.data)

    def test_required_multi_cannot_be_cleared_at_launch_time(self):
        self.item["options"][1]["required"] = True
        with self.assertRaisesRegex(ValueError, "features"):
            build_command(self.item, "run", {"features": []}, Path.cwd())

    def test_command_expands_paths_and_keeps_order_and_argument_boundaries(self):
        with temporary_directory(prefix=".range-test-root-") as folder:
            root = Path(folder)
            values = default_values(self.item)
            values.update(version="v2", features=["b", "a"], title='中文 空格 & "引号"',
                          verbose=True, port="9000")
            command, cwd = build_command(self.item, "run", values, root, "Python With Space.exe")
            self.assertEqual(command, [
                "Python With Space.exe", str(root) + "/script.py", "--foreground",
                "--version", "v2", "--features", "b", "a", "--title", '中文 空格 & "引号"',
                "--verbose", "--port", "9000",
            ])
            self.assertEqual(cwd, root.resolve())

    def test_empty_optional_values_never_replaced_with_defaults(self):
        values = default_values(self.item)
        values.update(features=[], title="", port="", verbose=False)
        command, _ = build_command(self.item, "run", values, Path.cwd())
        self.assertEqual(command[2:], ["--foreground", "--version", "v1"])

    def test_missing_values_use_defaults_and_inactive_options_are_skipped(self):
        command, _ = build_command(self.item, "check", {"title": object()}, Path.cwd())
        self.assertIn("--check", command)
        self.assertNotIn("--title", command)
        self.assertIn("8080", command)

    def test_command_rejects_unknown_profile_and_invalid_active_values(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            build_command(self.item, "missing", {}, Path.cwd())
        for values in ({"version": ""}, {"version": "missing"}, {"features": ["bad"]},
                       {"port": "-1"}, {"port": "1.5"}, {"verbose": "false"}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                build_command(self.item, "run", values, Path.cwd())

    def test_relative_cwd_and_unknown_external_executable_can_be_previewed(self):
        self.item.update(command=["external-not-installed.exe", "{powershell}"], cwd="subdir")
        with patch("tools.range_launcher.config.shutil.which", return_value=None):
            command, cwd = build_command(self.item, "run", {}, Path.cwd())
        self.assertEqual(command[0], "external-not-installed.exe")
        self.assertIn(command[1], ("powershell", "powershell.exe"))
        self.assertEqual(cwd, (Path.cwd() / "subdir").resolve())

    def test_save_load_backup_and_invalid_save_preserves_existing_file(self):
        with temporary_directory() as folder:
            path = Path(folder) / "ranges.json"
            save_catalog(path, self.data)
            self.assertEqual(load_catalog(path), self.data)
            old_bytes = path.read_bytes()
            self.item["label"] = "新名称"
            save_catalog(path, self.data)
            self.assertEqual(path.with_suffix(".json.bak").read_bytes(), old_bytes)
            self.assertEqual(load_catalog(path)["ranges"][0]["label"], "新名称")
            self.item["default_profile"] = "invalid"
            with self.assertRaises(ValueError):
                save_catalog(path, self.data)
            self.assertEqual(load_catalog(path)["ranges"][0]["label"], "新名称")

    def test_failed_atomic_replace_keeps_previous_catalog(self):
        with temporary_directory() as folder:
            path = Path(folder) / "ranges.json"
            save_catalog(path, self.data)
            before = path.read_bytes()
            self.item["label"] = "changed"
            with patch("tools.range_launcher.config.os.replace", side_effect=OSError("locked")):
                with self.assertRaisesRegex(OSError, "locked"):
                    save_catalog(path, self.data)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(sorted(p.name for p in Path(folder).iterdir()), ["ranges.json", "ranges.json.bak"])

    def test_load_accepts_utf8_bom_and_reports_invalid_json(self):
        with temporary_directory() as folder:
            path = Path(folder) / "ranges.json"
            path.write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8-sig")
            self.assertEqual(load_catalog(path), self.data)
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "ranges.json"):
                load_catalog(path)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = temporary_directory(prefix=".range-test-日志-")
        self.root = Path(self.temp.__enter__())
        self.runner = Runner(self.root / "logs")

    def tearDown(self):
        # Only reap children created by these tests; never terminate a process.
        for job in self.runner.jobs.values():
            job._process.wait(timeout=10)
        self.temp.__exit__(None, None, None)

    def collect(self, timeout=10):
        events = []
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            events.extend(self.runner.poll())
            if all(job.state != "running" for job in self.runner.jobs.values()):
                return events
            time.sleep(0.01)
        self.fail("short test child failed to finish")

    def test_real_child_receives_safe_unicode_arguments_and_merged_output(self):
        args = ['中文 空格 & "quoted"', "$(literal)", ""]
        code = "import json,sys;print(json.dumps(sys.argv[1:],ensure_ascii=False));print('错误日志',file=sys.stderr)"
        command = [sys.executable, "-c", code] + args
        job = self.runner.start("sample", "示例", command, self.root)
        self.assertIs(self.runner.jobs["sample"], job)
        self.assertEqual((job.id, job.label, job.command, job.cwd), ("sample", "示例", command, self.root))
        events = self.collect()
        output = "".join(e["text"] for e in events if e["kind"] == "output")
        self.assertIn(json.dumps(args, ensure_ascii=False), output)
        self.assertIn("错误日志", output)
        self.assertEqual((job.state, job.returncode), ("succeeded", 0))
        self.assertTrue(job.log_path.is_file())
        self.assertEqual(events[-1]["kind"], "status")
        self.assertEqual(events[-1]["state"], "succeeded")
        self.assertEqual(events[-1]["returncode"], 0)
        self.assertEqual(self.runner.poll(), [])

    def test_nonzero_exit_is_failed_and_tail_output_precedes_status(self):
        job = self.runner.start("fail", "失败", [sys.executable, "-c", "import sys;print('tail',end='');sys.exit(7)"], self.root)
        job._process.wait(timeout=10)
        events = self.collect()
        self.assertEqual((job.state, job.returncode), ("failed", 7))
        self.assertEqual([e["kind"] for e in events], ["output", "status"])
        self.assertEqual(events[0]["text"], "tail")

    def test_running_duplicate_rejected_and_finished_job_can_restart(self):
        command = [sys.executable, "-c", "import time;time.sleep(0.15)"]
        first = self.runner.start("same", "first", command, self.root)
        with self.assertRaisesRegex(ValueError, "same"):
            self.runner.start("same", "second", command, self.root)
        self.collect()
        second = self.runner.start("same", "second", [sys.executable, "-c", "pass"], self.root)
        self.assertNotEqual(first.log_path, second.log_path)
        self.collect()

    def test_start_failure_is_clear_and_does_not_leave_running_job(self):
        with self.assertRaises(OSError):
            self.runner.start("missing", "missing", ["range-missing-executable-849236.exe"], self.root)
        self.assertNotIn("missing", self.runner.jobs)

    def test_stdout_file_handle_is_closed_in_parent_after_spawn(self):
        real_popen = subprocess.Popen
        captured = {}

        def spawn(*args, **kwargs):
            captured.update(kwargs)
            return real_popen(*args, **kwargs)

        with patch("tools.range_launcher.runner.subprocess.Popen", side_effect=spawn):
            self.runner.start("child", "child", [sys.executable, "-c", "print('ok')"], self.root)
        self.assertTrue(captured["stdout"].closed)
        self.assertIs(captured["stderr"], subprocess.STDOUT)
        self.assertIs(captured["stdin"], subprocess.DEVNULL)
        self.assertFalse(captured["shell"])
        self.assertEqual(captured["env"]["PYTHONIOENCODING"], "utf-8")
        self.assertEqual(captured["env"]["PYTHONUNBUFFERED"], "1")
        self.collect()

    def test_large_log_is_bounded_per_poll_without_losing_utf8(self):
        code = "import sys;sys.stdout.write('中' * 100000)"
        job = self.runner.start("large", "large", [sys.executable, "-c", code], self.root)
        job._process.wait(timeout=10)
        events = self.runner.poll()
        output = "".join(e["text"] for e in events if e["kind"] == "output")
        self.assertLess(len(output), 100000)
        self.assertEqual(job.state, "running")
        events.extend(self.collect())
        output = "".join(e["text"] for e in events if e["kind"] == "output")
        self.assertEqual(output, "中" * 100000)
        self.assertEqual(events[-1]["kind"], "status")

    def test_log_names_cannot_escape_log_directory(self):
        job = self.runner.start("../nested/test", "child", [sys.executable, "-c", "pass"], self.root)
        self.assertEqual(job.log_path.parent, (self.root / "logs").resolve())
        self.collect()


if __name__ == "__main__":
    unittest.main()
