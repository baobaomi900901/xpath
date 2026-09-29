from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import stat
import subprocess
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools import start_electron


MODULE_PATH = Path(__file__).with_name("start_electron.py")
ENTRY = {
    "major": "22", "electron": "22.3.27", "chromium": "108.0.5359.215", "node": "16.17.1",
    "archive": "electron-v22.3.27-win32-x64.zip",
    "url": "https://github.com/electron/electron/releases/download/v22.3.27/electron-v22.3.27-win32-x64.zip",
    "sha256": "a" * 64,
    "runtime_files": ["libEGL.dll", "libGLESv2.dll", "snapshot_blob.bin"],
}
SOURCE_FILES = ("package.json", "config.cjs", "main.cjs", "preload.cjs", "shell.html", "shell.css", "shell.js")
RUNTIME_FILES = ("chrome_100_percent.pak", "chrome_200_percent.pak", "icudtl.dat", "resources.pak",
                 "ffmpeg.dll", "v8_context_snapshot.bin", "locales/en-US.pak", "locales/zh-CN.pak",
                 "d3dcompiler_47.dll", "vk_swiftshader.dll", "vulkan-1.dll", "vk_swiftshader_icd.json")


def runtime_info(entry: dict = ENTRY) -> dict:
    return {key: entry[key] for key in ("major", "electron", "chromium", "node")}


def write_source(root: Path) -> Path:
    source = root / "src"
    source.mkdir(parents=True, exist_ok=True)
    for name in SOURCE_FILES:
        (source / name).write_text("fixture", encoding="utf-8")
    (source / "package.json").write_text(json.dumps({"name": "range", "version": "1.0.0", "main": "main.cjs"}))
    return source


def write_runtime(root: Path, entry: dict = ENTRY) -> Path:
    for name in (*RUNTIME_FILES, *entry["runtime_files"], "electron.exe"):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"runtime fixture")
    (root / "version").write_text(entry["electron"], encoding="utf-8")
    (root / "runtime-marker.json").write_text(json.dumps(dict(runtime_info(entry), sha256=entry["sha256"])))
    return root


def write_artifact(root: Path, entry: dict = ENTRY) -> Path:
    dist = write_runtime(root / "dist" / entry["major"], entry)
    executable = dist / ("electron-shooting-range-" + entry["major"] + ".exe")
    (dist / "electron.exe").replace(executable)
    app = dist / "resources" / "app"
    app.mkdir(parents=True, exist_ok=True)
    source = write_source(root)
    for name in SOURCE_FILES:
        (app / name).write_bytes((source / name).read_bytes())
    (app / "runtime.json").write_text(json.dumps(runtime_info(entry)))
    (dist / "version.json").write_text(json.dumps(runtime_info(entry)))
    return executable


def write_archive(path: Path, members: list[tuple[str, bytes]]) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as package:
        for name, content in members:
            member = zipfile.ZipInfo()
            # ZipInfo(name) normalizes Windows backslashes, concealing this malicious input.
            member.filename = name
            member.orig_filename = name
            package.writestr(member, content)
    return dict(ENTRY, sha256=hashlib.sha256(path.read_bytes()).hexdigest())


class LauncherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="electron-test-", dir=MODULE_PATH.parent)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_supported_cli_normalizes_selection(self) -> None:
        self.assertEqual(["22", "38", "44"], start_electron.parse_args(
            ["--versions", "44", "22", "38", "22"]).versions)
        self.assertEqual(["29"], start_electron.parse_args(["--version", "29"]).versions)
        self.assertIsNone(start_electron.parse_args([]).versions)

    def test_invalid_cli_fails_before_any_work(self) -> None:
        cases = (["--version", "23"], ["--version", "22", "--versions", "29"],
                 ["--skip-build", "--force-build"], ["--remote-debugging-port", "1023"],
                 ["--remote-debugging-port", "65536"], ["--remote-debugging-port", "abc"],
                 ["--remote-debugging-port", "+9222"], ["--remote-debugging-port", " 9222"],
                 ["--remote-debugging-port", "9_222"],
                 ["--versions", "22", "29", "--remote-debugging-port", "9222"])
        for arguments in cases:
            with self.subTest(arguments=arguments), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    start_electron.parse_args(arguments)
                self.assertEqual(2, error.exception.code)

    def test_base_url_accepts_router_roots_and_rejects_malformed_values(self) -> None:
        for url in ("http://localhost:7199/", "https://example.com/xpath/#/"):
            self.assertEqual(url, start_electron.validate_base_url(url))
        for url in ("https://example.com", "https://example.com/path", "/xpath/", "file:///tmp/", "https://",
                    "https://u:p@example.com/", "https://example.com/?", "https://example.com/#/route",
                    "http://localhost:0/", "http://localhost:abc/", "https://example.com/\n", "http://a\\b/"):
            with self.subTest(url=url), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    start_electron.parse_args(["--base-url", url])

    def test_base_url_rejects_malformed_encoded_hosts_and_del_characters(self) -> None:
        for url in ("http://%/", "http://exa%mple.com/", "http://%FF/", "http://%25/",
                    "http://%2F/", "http://%20/", "http://%00/", "http://%7F/",
                    "http://localhost/a\x7f/", "http://local\x7fhost/"):
            with self.subTest(url=url), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    start_electron.parse_args(["--base-url", url])

    def test_base_url_accepts_idn_ipv6_and_valid_encoded_hosts(self) -> None:
        for url in ("http://localhost:7199/", "http://[::1]:7199/", "https://例子.测试/#/",
                    "https://%65xample.com/", "https://%E4%BE%8B%E5%AD%90.%E6%B5%8B%E8%AF%95/#/"):
            with self.subTest(url=url):
                self.assertEqual(url, start_electron.validate_base_url(url))

    def test_official_manifest_is_pinned_to_exact_windows_x64_releases(self) -> None:
        manifest = start_electron.load_manifest()
        self.assertEqual({"22", "29", "38", "44"}, set(manifest))
        self.assertEqual("22.3.27", manifest["22"]["electron"])
        self.assertEqual("29.4.6", manifest["29"]["electron"])
        self.assertEqual("38.8.6", manifest["38"]["electron"])
        self.assertEqual("44.4.5", manifest["44"]["electron"])

    def test_manifest_rejects_inconsistent_archive_version_hash_and_source(self) -> None:
        original = start_electron.load_manifest()
        mutations = (lambda d: d.pop("29"), lambda d: d["22"].update(major="29"),
                     lambda d: d["22"].update(electron="29.1.0"), lambda d: d["22"].update(chromium="108"),
                     lambda d: d["22"].update(node="bad"), lambda d: d["22"].update(sha256="a" * 63),
                     lambda d: d["22"].update(archive="../electron.zip"),
                     lambda d: d["22"].update(url="https://evil.example/electron.zip"))
        path = self.root / "versions.json"
        for mutate in mutations:
            data = copy.deepcopy(original)
            mutate(data)
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.subTest(data=data), self.assertRaises(ValueError):
                start_electron.load_manifest(path)

    def test_archive_hash_is_checked_before_extraction(self) -> None:
        archive = self.root / "electron.zip"
        entry = write_archive(archive, [("electron.exe", b"exe")])
        start_electron.validate_archive(archive, entry)
        with self.assertRaisesRegex(ValueError, "SHA256"):
            start_electron.extract_runtime(archive, self.root / "runtime", "22", dict(entry, sha256="0" * 64))
        self.assertFalse((self.root / "runtime").exists())

    def test_cached_archive_is_verified_without_network(self) -> None:
        archive = self.root / "downloads" / ENTRY["archive"]
        entry = write_archive(archive, [("electron.exe", b"exe")])
        with patch.object(start_electron.urllib.request, "urlopen", side_effect=AssertionError("network")):
            self.assertEqual(archive, start_electron.download_archive(entry, archive.parent))

    def test_bad_download_does_not_publish_or_leave_partial_file(self) -> None:
        downloads = self.root / "downloads"
        with patch.object(start_electron.urllib.request, "urlopen", return_value=io.BytesIO(b"bad")):
            with redirect_stdout(io.StringIO()), self.assertRaises(ValueError):
                start_electron.download_archive(ENTRY, downloads)
        self.assertFalse((downloads / ENTRY["archive"]).exists())
        self.assertFalse((downloads / (ENTRY["archive"] + ".part")).exists())

    def test_download_verifies_then_atomically_publishes(self) -> None:
        data = b"valid archive fixture"
        entry = dict(ENTRY, sha256=hashlib.sha256(data).hexdigest())
        with patch.object(start_electron.urllib.request, "urlopen", return_value=io.BytesIO(data)) as request:
            with redirect_stdout(io.StringIO()):
                archive = start_electron.download_archive(entry, self.root / "downloads")
        self.assertEqual(data, archive.read_bytes())
        self.assertEqual(ENTRY["url"], request.call_args.args[0])
        self.assertFalse(archive.with_name(archive.name + ".part").exists())

    def test_secure_extraction_rejects_escape_symlink_and_duplicate_windows_paths(self) -> None:
        names = ("../outside.txt", "/absolute.txt", "C:/absolute.txt", "bad\\name.txt", "a/../b.txt",
                 "a/CON.txt", "a/file:stream", "a./file", "a/./file")
        for name in names:
            archive = self.root / "bad.zip"
            entry = write_archive(archive, [(name, b"bad")])
            with self.subTest(name=name), self.assertRaises(ValueError):
                start_electron.extract_runtime(archive, self.root / "runtime", "22", entry)
        for members in ([('FILE', b'1'), ('file', b'2')], [('file', b'1'), ('file/child', b'2')]):
            entry = write_archive(self.root / "bad.zip", members)
            with self.assertRaises(ValueError):
                start_electron.extract_runtime(self.root / "bad.zip", self.root / "runtime", "22", entry)
        with zipfile.ZipFile(self.root / "link.zip", "w") as package:
            link = zipfile.ZipInfo("symlink")
            link.create_system = 3
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            package.writestr(link, "../outside")
        entry = dict(ENTRY, sha256=hashlib.sha256((self.root / "link.zip").read_bytes()).hexdigest())
        with self.assertRaises(ValueError):
            start_electron.extract_runtime(self.root / "link.zip", self.root / "runtime", "22", entry)
        self.assertFalse((self.root.parent / "outside.txt").exists())

    def test_incomplete_extraction_leaves_existing_artifact_untouched(self) -> None:
        target = write_runtime(self.root / "runtime")
        (target / "electron.exe").write_bytes(b"existing exe")
        entry = write_archive(self.root / "incomplete.zip", [("electron.exe", b"new exe")])
        with self.assertRaises(FileNotFoundError):
            start_electron.extract_runtime(self.root / "incomplete.zip", target, "22", entry)
        self.assertEqual(b"existing exe", (target / "electron.exe").read_bytes())

    def test_complete_archive_extracts_validated_runtime_with_exact_marker(self) -> None:
        fixture = write_runtime(self.root / "fixture")
        members = [(p.relative_to(fixture).as_posix(), p.read_bytes())
                   for p in fixture.rglob("*") if p.is_file() and p.name != "runtime-marker.json"]
        entry = write_archive(self.root / "complete.zip", members)
        target = self.root / "runtime"
        self.assertEqual(target, start_electron.extract_runtime(self.root / "complete.zip", target, "22", entry))
        self.assertEqual(target, start_electron.validate_runtime("22", entry, target))
        marker = json.loads((target / "runtime-marker.json").read_text())
        self.assertEqual(entry["sha256"], marker["sha256"])

    def test_runtime_cache_rejects_stale_version_and_missing_core_file(self) -> None:
        runtime = write_runtime(self.root / "runtime")
        (runtime / "version").write_text("29.4.6")
        with self.assertRaises(ValueError):
            start_electron.validate_runtime("22", ENTRY, runtime)
        (runtime / "version").write_text(ENTRY["electron"])
        (runtime / "v8_context_snapshot.bin").unlink()
        with self.assertRaises(FileNotFoundError):
            start_electron.validate_runtime("22", ENTRY, runtime)

    def test_cached_runtime_rejects_links_to_files_outside_its_directory(self) -> None:
        runtime = write_runtime(self.root / "runtime")
        outside = self.root / "outside.txt"
        outside.write_text("external file")
        try:
            (runtime / "extra.txt").symlink_to(outside)
        except OSError:
            self.skipTest("symlink creation requires Windows privilege")
        with self.assertRaises(ValueError):
            start_electron.validate_runtime("22", ENTRY, runtime)

    def test_failed_directory_publish_restores_previous_artifact(self) -> None:
        target = self.root / "artifact"
        staging = self.root / "staging"
        target.mkdir()
        staging.mkdir()
        (target / "old.txt").write_text("previous")
        (staging / "new.txt").write_text("replacement")
        real_replace = start_electron.os.replace

        def fail_publish(source, destination):
            if Path(source) == staging:
                raise OSError("publish failed")
            real_replace(source, destination)

        with patch.object(start_electron.os, "replace", side_effect=fail_publish):
            with self.assertRaises(OSError):
                start_electron.replace_directory(staging, target)
        self.assertEqual("previous", (target / "old.txt").read_text())
        self.assertFalse(target.with_name("artifact.previous").exists())

    def test_artifact_validation_requires_runtime_locale_app_and_all_exact_versions(self) -> None:
        with patch.object(start_electron, "ELECTRON_ROOT", self.root):
            executable = write_artifact(self.root)
            self.assertEqual(executable, start_electron.validate_artifact("22", ENTRY))
            for name in ("ffmpeg.dll", "locales/zh-CN.pak", "resources/app/preload.cjs", "resources/app/shell.js"):
                file = executable.parent / name
                content = file.read_bytes()
                file.unlink()
                with self.subTest(name=name), self.assertRaises(FileNotFoundError):
                    start_electron.validate_artifact("22", ENTRY)
                file.write_bytes(content)
            for field in ("major", "electron", "chromium", "node"):
                (executable.parent / "version.json").write_text(json.dumps(dict(runtime_info(), **{field: "wrong"})))
                with self.subTest(field=field), self.assertRaises(ValueError):
                    start_electron.validate_artifact("22", ENTRY)
            (executable.parent / "version.json").write_text(json.dumps(runtime_info()))
            (executable.parent / "resources/app/runtime.json").write_text(json.dumps(dict(runtime_info(), electron="wrong")))
            with self.assertRaises(ValueError):
                start_electron.validate_artifact("22", ENTRY)

    def test_skip_build_validates_without_network_or_source_packaging(self) -> None:
        write_artifact(self.root)
        with patch.object(start_electron, "ELECTRON_ROOT", self.root), redirect_stdout(io.StringIO()):
            with patch.object(start_electron, "build_version", side_effect=AssertionError("build")):
                self.assertEqual(0, start_electron.main(["--version", "22", "--skip-build", "--no-launch"]))

    def test_each_versions_gpu_and_snapshot_files_are_required(self) -> None:
        manifest = start_electron.load_manifest()
        cases = (("22", "libEGL.dll"), ("29", "libGLESv2.dll"), ("38", "dxcompiler.dll"),
                 ("44", "dxil.dll"), ("44", "snapshot_blob.bin"), ("44", "vk_swiftshader.dll"))
        with patch.object(start_electron, "ELECTRON_ROOT", self.root):
            for major, name in cases:
                entry = manifest[major]
                executable = write_artifact(self.root, entry)
                (executable.parent / name).unlink()
                with self.subTest(major=major, name=name), self.assertRaises(FileNotFoundError):
                    start_electron.validate_artifact(major, entry)

    def test_all_selected_artifacts_prepared_before_launch(self) -> None:
        write_artifact(self.root)
        with patch.object(start_electron, "ELECTRON_ROOT", self.root):
            with patch.object(start_electron.subprocess, "Popen", side_effect=AssertionError("premature launch")):
                with self.assertRaises(FileNotFoundError):
                    start_electron.main(["--versions", "22", "29", "--skip-build"])

    def test_build_refreshes_source_from_valid_cached_runtime_without_download(self) -> None:
        source = write_source(self.root)
        write_runtime(self.root / ".cache/runtimes/22")
        with patch.object(start_electron, "ELECTRON_ROOT", self.root), redirect_stdout(io.StringIO()):
            with patch.object(start_electron, "download_archive", side_effect=AssertionError("download")):
                executable = start_electron.build_version("22", ENTRY)
                self.assertFalse((executable.parent / "electron.exe").exists())
                self.assertEqual(runtime_info(), json.loads((executable.parent / "resources/app/runtime.json").read_text()))
                (source / "shell.js").write_text("updated source")
                start_electron.build_version("22", ENTRY)
                self.assertEqual("updated source", (executable.parent / "resources/app/shell.js").read_text())

    def test_force_build_reextracts_verified_archive_and_removes_stale_dist_files(self) -> None:
        write_source(self.root)
        write_artifact(self.root)
        (self.root / "dist/22/stale.txt").write_text("stale")
        fixture = write_runtime(self.root / "fixture")
        entry = write_archive(self.root / "archive.zip", [(p.relative_to(fixture).as_posix(), p.read_bytes())
                              for p in fixture.rglob("*") if p.is_file() and p.name != "runtime-marker.json"])
        with patch.object(start_electron, "ELECTRON_ROOT", self.root), redirect_stdout(io.StringIO()):
            with patch.object(start_electron, "download_archive", return_value=self.root / "archive.zip") as download:
                executable = start_electron.build_version("22", entry, True)
        download.assert_called_once()
        self.assertFalse((executable.parent / "stale.txt").exists())

    def test_invalid_source_does_not_replace_existing_dist(self) -> None:
        executable = write_artifact(self.root)
        (self.root / "src/main.cjs").unlink()
        write_runtime(self.root / ".cache/runtimes/22")
        with patch.object(start_electron, "ELECTRON_ROOT", self.root), self.assertRaises(FileNotFoundError):
            start_electron.build_version("22", ENTRY)
        self.assertTrue(executable.exists())

    def test_build_rejects_destination_symlink_outside_electron_root(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("no symlink support")
        outside = self.root / "outside"
        outside.mkdir()
        contained = self.root / "contained"
        contained.mkdir()
        try:
            (contained / "dist").symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("symlink creation requires Windows privilege")
        write_source(contained)
        write_runtime(contained / ".cache/runtimes/22")
        with patch.object(start_electron, "ELECTRON_ROOT", contained), self.assertRaises(ValueError):
            start_electron.build_version("22", ENTRY)
        self.assertEqual([], list(outside.iterdir()))

    def test_launch_passes_loopback_arguments_and_removes_node_mode_from_environment(self) -> None:
        executable = self.root / "dist/22/electron-shooting-range-22.exe"
        process = subprocess.CompletedProcess([], 0)
        process.pid = 123
        process.poll = lambda: None
        with patch.dict(os.environ, {"ELECTRON_RUN_AS_NODE": "1"}):
            with patch.object(start_electron.subprocess, "Popen", return_value=process) as launch:
                with redirect_stdout(io.StringIO()):
                    start_electron.launch_versions(["22"], {"22": executable}, "http://localhost:7199/", 9222)
        self.assertEqual([str(executable), "--base-url=http://localhost:7199/", "--remote-debugging-port=9222",
                          "--remote-debugging-address=127.0.0.1"], launch.call_args.args[0])
        self.assertEqual(executable.parent, launch.call_args.kwargs["cwd"])
        self.assertNotIn("ELECTRON_RUN_AS_NODE", launch.call_args.kwargs["env"])

    def test_partial_launch_failure_reports_existing_pid_without_terminating(self) -> None:
        process = subprocess.CompletedProcess([], 0)
        process.pid = 321
        process.poll = lambda: None
        process.terminate = lambda: self.fail("must not terminate launched process")
        with patch.object(start_electron.subprocess, "Popen", side_effect=[process, OSError("launch denied")]):
            with redirect_stdout(io.StringIO()), self.assertRaisesRegex(RuntimeError, "321"):
                start_electron.launch_versions(["22", "29"], {"22": Path('22.exe'), "29": Path('29.exe')},
                                               "https://example.com/#/", None)

    def test_main_builds_all_versions_before_launch(self) -> None:
        events = []
        with patch.object(start_electron, "select_versions", return_value=["22", "38"]):
            with patch.object(start_electron, "build_version", side_effect=lambda v, e, f: events.append(v) or Path(v + '.exe')):
                with patch.object(start_electron, "launch_versions", side_effect=lambda *a: events.append("launch")):
                    self.assertEqual(0, start_electron.main([]))
        self.assertEqual(["22", "38", "launch"], events)


class SelectorTests(unittest.TestCase):
    def select(self, keys: list[str]) -> tuple[list[str], str]:
        output = io.StringIO()
        output.isatty = lambda: True
        with patch.object(start_electron.sys.stdin, "isatty", return_value=True), redirect_stdout(output):
            with patch.object(start_electron, "clear_screen") as clear:
                with patch.object(start_electron, "read_key", side_effect=keys):
                    selected = start_electron.select_versions()
        clear.assert_called_once_with()
        return selected, output.getvalue()

    def test_selector_multiselects_and_redraws_in_place(self) -> None:
        selected, output = self.select(["enter", "down", "down", "space", "down", "down", "enter"])
        self.assertEqual(["22", "38"], selected)
        self.assertIn("\x1b[H", output)
        self.assertIn("[✓] Electron 22", output)
        self.assertIn("[✓] Electron 38", output)
        self.assertIn("[ 已完成选择 ]", output)

    def test_selector_unchecks_wraps_focus_and_requires_selection(self) -> None:
        selected, output = self.select(["up", "enter", "up", "enter", "space", "enter", "down", "enter"])
        self.assertEqual(["44"], selected)
        self.assertIn("请至少选择一个 Electron 版本。", output)

    def test_cancel_does_not_build_or_load_manifest(self) -> None:
        with patch.object(start_electron, "select_versions", return_value=[]), redirect_stdout(io.StringIO()):
            with patch.object(start_electron, "load_manifest", side_effect=AssertionError("manifest")):
                self.assertEqual(0, start_electron.main([]))

    def test_interactive_multiple_versions_reject_shared_debug_port(self) -> None:
        with patch.object(start_electron, "select_versions", return_value=["22", "29"]):
            with patch.object(start_electron, "load_manifest", side_effect=AssertionError("manifest")):
                with self.assertRaisesRegex(ValueError, "单个版本"):
                    start_electron.main(["--remote-debugging-port", "9222"])

    def test_noninteractive_input_requires_explicit_versions(self) -> None:
        with patch.object(start_electron.sys.stdin, "isatty", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "--version"):
                start_electron.select_versions()


if __name__ == "__main__":
    unittest.main()
