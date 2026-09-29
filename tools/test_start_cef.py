from __future__ import annotations

import copy
import hashlib
import io
import json
import subprocess
import sys
import tarfile
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools import start_cef

MODULE_PATH = Path(__file__).with_name("start_cef.py")
CEF_VERSION = "109.1.18+gf1c41e4+chromium-109.0.5414.120"
ENTRY = {
    "cef_version": CEF_VERSION,
    "chromium_version": "109.0.5414.120",
    "archive": f"cef_binary_{CEF_VERSION}_windows64_minimal.tar.bz2",
    "sha1": "a" * 40,
    "size": 1024,
    "runtime_files": json.loads((MODULE_PATH.parents[1] / "CEF" / "versions.json").read_text(encoding="utf-8"))["109"]["runtime_files"],
}
RUNTIME_FILES = (
    "libcef.dll", "chrome_elf.dll", "icudtl.dat", "resources.pak",
    "chrome_100_percent.pak", "chrome_200_percent.pak", "locales/en-US.pak", "locales/zh-CN.pak",
)


def write_sdk(root: Path, entry: dict = ENTRY) -> None:
    files = {
        "include/cef_version.h": (
            f'#define CEF_VERSION "{entry["cef_version"]}"\n'
            '#define CEF_VERSION_MAJOR 109\n'
            '#define CHROME_VERSION_MAJOR 109\n'
            '#define CHROME_VERSION_MINOR 0\n'
            '#define CHROME_VERSION_BUILD 5414\n'
            '#define CHROME_VERSION_PATCH 120\n'
        ),
        "Release/libcef.dll": "dll", "Release/libcef.lib": "lib",
        "Resources/icudtl.dat": "data", "libcef_dll/CMakeLists.txt": "cmake",
    }
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def write_artifact(root: Path, version: str, entry: dict) -> Path:
    dist = root / "dist" / version
    for name in (*RUNTIME_FILES, *entry["runtime_files"], f"cef-shooting-range-{version}.exe"):
        path = dist / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fixture")
    (dist / "version.json").write_text(json.dumps(entry), encoding="utf-8")
    return dist / f"cef-shooting-range-{version}.exe"


class LauncherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="cef-test-", dir=MODULE_PATH.parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_no_version_requests_interactive_selection_and_supported_base_urls(self) -> None:
        self.assertIsNone(start_cef.parse_args([]).versions)
        for url in ("http://localhost:7199/", "https://example.com/xpath/#/"):
            self.assertEqual(url, start_cef.parse_args(["--base-url", url]).base_url)

    def test_cli_normalizes_duplicate_versions_in_supported_order(self) -> None:
        self.assertEqual(["109", "133", "154"], start_cef.parse_args(
            ["--versions", "154", "109", "133", "109"]
        ).versions)
        self.assertEqual(["125"], start_cef.parse_args(["--version", "125"]).versions)

    def test_cli_rejects_invalid_versions_options_and_ports(self) -> None:
        cases = (
            ["--version", "110"], ["--version", "109", "--versions", "125"],
            ["--remote-debugging-port", "1023"], ["--remote-debugging-port", "65536"],
            ["--remote-debugging-port", "abc"],
            ["--versions", "109", "125", "--remote-debugging-port", "9222"],
            ["--skip-build", "--force-build"],
        )
        for args in cases:
            with self.subTest(args=args), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    start_cef.parse_args(args)
                self.assertEqual(2, error.exception.code)

    def test_cli_rejects_nonabsolute_credentials_query_and_malformed_urls(self) -> None:
        for url in (
            "/xpath/", "file:///tmp/", "https://", "https://u:p@example.com/",
            "https://example.com/?secret=1", "https://example.com/#/click-test",
            "http://localhost:bad/", "http://localhost:0/", "http://a/\n",
        ):
            with self.subTest(url=url), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    start_cef.parse_args(["--base-url", url])

    def test_manifest_accepts_actual_pinned_versions(self) -> None:
        manifest = start_cef.load_manifest()
        self.assertEqual(set(start_cef.VERSIONS), set(manifest))

    def test_manifest_rejects_missing_inconsistent_and_malformed_metadata(self) -> None:
        original = json.loads((MODULE_PATH.parents[1] / "CEF" / "versions.json").read_text())
        mutations = [
            lambda data: data.pop("125"),
            lambda data: data["109"].update(size=-1),
            lambda data: data["109"].update(size=True),
            lambda data: data["109"].update(sha1="not-a-hash"),
            lambda data: data["109"].update(archive="../sdk.tar.bz2"),
            lambda data: data["109"].update(chromium_version="125.0.0.0"),
            lambda data: data["109"].update(cef_version="109.0.0+fake"),
        ]
        for mutate in mutations:
            data = copy.deepcopy(original)
            mutate(data)
            manifest = self.root / "versions.json"
            manifest.write_text(json.dumps(data))
            with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                start_cef.load_manifest(manifest)
        manifest.write_text("not json")
        with self.assertRaises(ValueError):
            start_cef.load_manifest(manifest)

    def test_manifest_requires_unique_safe_runtime_basenames(self) -> None:
        original = json.loads(start_cef.MANIFEST_PATH.read_text(encoding="utf-8"))
        invalid_values = (
            None, [], "libcef.dll", [123], [""], ["libcef.dll", "LIBCEF.dll"],
            ["../libcef.dll"], ["C:\\libcef.dll"], ["nested/libcef.dll"],
            ["libcef.dll:stream"], ["CON"], ["libcef.dll "], ["bad\nname.dll"],
            ["file?.dll"], [".."], ["/libcef.dll"],
        )
        manifest = self.root / "versions.json"
        for invalid in invalid_values:
            data = copy.deepcopy(original)
            data["109"]["runtime_files"] = invalid
            manifest.write_text(json.dumps(data), encoding="utf-8")
            with self.subTest(runtime_files=invalid), self.assertRaises(ValueError):
                start_cef.load_manifest(manifest)
        data = copy.deepcopy(original)
        data["109"].pop("runtime_files", None)
        manifest.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(ValueError):
            start_cef.load_manifest(manifest)

    def test_sdk_validation_checks_full_version_major_and_chromium_macros(self) -> None:
        sdk = self.root / "sdk"
        write_sdk(sdk)
        self.assertEqual(sdk, start_cef.validate_sdk("109", ENTRY, sdk))
        header = sdk / "include" / "cef_version.h"
        original = header.read_text()
        for before, after in (
            (CEF_VERSION, "109.0.0+different"), ("MAJOR 109", "MAJOR 125"),
            ("CHROME_VERSION_PATCH 120", "CHROME_VERSION_PATCH 999"),
        ):
            header.write_text(original.replace(before, after))
            with self.subTest(before=before), self.assertRaises(ValueError):
                start_cef.validate_sdk("109", ENTRY, sdk)

    def test_sdk_validation_rejects_missing_required_files(self) -> None:
        sdk = self.root / "sdk"
        write_sdk(sdk)
        (sdk / "Release" / "libcef.lib").unlink()
        with self.assertRaises(FileNotFoundError):
            start_cef.validate_sdk("109", ENTRY, sdk)

    def make_tar(self, entries: list[tuple[str, bytes | str]]) -> Path:
        archive = self.root / ENTRY["archive"]
        with tarfile.open(archive, "w:bz2") as package:
            for name, value in entries:
                info = tarfile.TarInfo(name)
                if isinstance(value, str):
                    info.type = {"symlink": tarfile.SYMTYPE, "hardlink": tarfile.LNKTYPE,
                                 "device": tarfile.CHRTYPE}[value]
                    info.linkname = "elsewhere"
                    package.addfile(info)
                else:
                    info.size = len(value)
                    package.addfile(info, io.BytesIO(value))
        return archive

    def test_extract_sdk_strips_one_expected_root_and_validates_before_publish(self) -> None:
        source = self.root / "source"
        write_sdk(source)
        prefix = ENTRY["archive"][:-len(".tar.bz2")]
        entries = [(f"{prefix}/{path.relative_to(source).as_posix()}", path.read_bytes())
                   for path in source.rglob("*") if path.is_file()]
        archive = self.make_tar(entries)
        target = self.root / "sdk" / "109"
        self.assertEqual(target, start_cef.extract_sdk(archive, target, "109", ENTRY))
        self.assertTrue((target / "include" / "cef_version.h").is_file())
        self.assertFalse((target / prefix).exists())

    def test_extract_sdk_rejects_unsafe_paths_roots_links_devices_and_case_collisions(self) -> None:
        prefix = ENTRY["archive"][:-len(".tar.bz2")]
        cases = (
            [(f"{prefix}/../../outside", b"x")], [("/absolute", b"x")],
            [("C:/outside", b"x")], [("unexpected/file", b"x")],
            [(f"{prefix}/link", "symlink")], [(f"{prefix}/link", "hardlink")],
            [(f"{prefix}/device", "device")], [(f"{prefix}/file:stream", b"x")],
            [(f"{prefix}/CON", b"x")], [(f"{prefix}\\file", b"x")],
            [(f"{prefix}/file", b"x"), (f"{prefix}/FILE", b"x")],
        )
        for entries in cases:
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                start_cef.extract_sdk(self.make_tar(entries), self.root / "sdk" / "109", "109", ENTRY)
            self.assertFalse((self.root / "sdk" / "109").exists())
        self.assertFalse((self.root / "outside").exists())

    def test_extract_sdk_never_publishes_incomplete_archive(self) -> None:
        prefix = ENTRY["archive"][:-len(".tar.bz2")]
        archive = self.make_tar([(f"{prefix}/README.txt", b"incomplete")])
        target = self.root / "sdk" / "109"
        with self.assertRaises(FileNotFoundError):
            start_cef.extract_sdk(archive, target, "109", ENTRY)
        self.assertFalse(target.exists())

    def test_extract_sdk_retries_transient_windows_atomic_rename_failure(self) -> None:
        source = self.root / "source"
        write_sdk(source)
        prefix = ENTRY["archive"][:-len(".tar.bz2")]
        archive = self.make_tar([(f"{prefix}/{path.relative_to(source).as_posix()}", path.read_bytes())
                                 for path in source.rglob("*") if path.is_file()])
        target = self.root / "sdk" / "109"
        real_replace = start_cef.os.replace
        attempts = 0

        def replace_with_one_failure(staging: Path, destination: Path) -> None:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise PermissionError("transient Windows file scanner lock")
            real_replace(staging, destination)

        with patch.object(start_cef.os, "replace", side_effect=replace_with_one_failure):
            try:
                extracted = start_cef.extract_sdk(archive, target, "109", ENTRY)
            except PermissionError:
                self.fail("atomic SDK publish should retry a transient Windows lock")
            self.assertEqual(target, extracted)
        self.assertEqual(2, attempts)
        self.assertTrue((target / "Release" / "libcef.dll").is_file())

    def test_cache_reuse_requires_exact_sdk_major_source_and_x64(self) -> None:
        build = self.root / "build"
        build.mkdir()
        sdk = self.root / "sdk"
        data = {
            "CEF_RANGE_MAJOR:STRING": "109", "CEF_ROOT:PATH": str(sdk),
            "CMAKE_HOME_DIRECTORY:INTERNAL": str(self.root), "CMAKE_GENERATOR_PLATFORM:INTERNAL": "x64",
        }
        cache = build / "CMakeCache.txt"
        with patch.object(start_cef, "CEF_ROOT", self.root):
            cache.write_text("\n".join(f"{key}={value}" for key, value in data.items()))
            start_cef.validate_build_cache(build, "109", sdk)
            for key, bad_value in (("CEF_RANGE_MAJOR:STRING", "125"), ("CEF_ROOT:PATH", str(self.root / "other")),
                                   ("CMAKE_HOME_DIRECTORY:INTERNAL", str(self.root / "other-source")),
                                   ("CMAKE_GENERATOR_PLATFORM:INTERNAL", "Win32")):
                invalid = dict(data, **{key: bad_value})
                cache.write_text("\n".join(f"{name}={value}" for name, value in invalid.items()))
                with self.subTest(key=key), self.assertRaises(ValueError):
                    start_cef.validate_build_cache(build, "109", sdk)

    def test_archive_validation_checks_hash_and_size(self) -> None:
        archive = self.root / "archive"
        archive.write_bytes(b"sdk archive")
        entry = dict(ENTRY, size=archive.stat().st_size,
                     sha1=hashlib.sha1(archive.read_bytes()).hexdigest())
        start_cef.validate_archive(archive, entry)
        for bad in (dict(entry, size=1), dict(entry, sha1="0" * 40)):
            with self.assertRaises(ValueError):
                start_cef.validate_archive(archive, bad)

    def test_cached_archive_reuse_does_not_access_network(self) -> None:
        downloads = self.root / "downloads"
        downloads.mkdir()
        archive = downloads / ENTRY["archive"]
        archive.write_bytes(b"sdk archive")
        entry = dict(ENTRY, size=archive.stat().st_size,
                     sha1=hashlib.sha1(archive.read_bytes()).hexdigest())
        with patch.object(start_cef.urllib.request, "urlopen", side_effect=AssertionError("network")):
            self.assertEqual(archive, start_cef.download_archive(entry, downloads))

    def test_download_streams_validates_then_atomically_publishes(self) -> None:
        content = b"download fixture" * 1000
        entry = dict(ENTRY, size=len(content), sha1=hashlib.sha1(content).hexdigest())
        downloads = self.root / "downloads"
        with patch.object(start_cef.urllib.request, "urlopen", return_value=io.BytesIO(content)) as request:
            with redirect_stdout(io.StringIO()):
                archive = start_cef.download_archive(entry, downloads)
        self.assertEqual(content, archive.read_bytes())
        self.assertFalse(archive.with_name(archive.name + ".part").exists())
        self.assertIn("https://cef-builds.spotifycdn.com/cef_binary_109.1.18%2B", request.call_args.args[0])
        self.assertNotIn("context", request.call_args.kwargs)

    def test_bad_download_does_not_publish_or_leave_partial_file(self) -> None:
        downloads = self.root / "downloads"
        with patch.object(start_cef.urllib.request, "urlopen", return_value=io.BytesIO(b"bad")):
            with redirect_stdout(io.StringIO()), self.assertRaises(ValueError):
                start_cef.download_archive(ENTRY, downloads)
        self.assertFalse((downloads / ENTRY["archive"]).exists())
        self.assertFalse((downloads / (ENTRY["archive"] + ".part")).exists())

    def test_artifact_validation_requires_runtime_files_and_matching_marker(self) -> None:
        executable = write_artifact(self.root, "109", ENTRY)
        with patch.object(start_cef, "CEF_ROOT", self.root):
            self.assertEqual(executable, start_cef.validate_artifact("109", ENTRY))
            (executable.parent / "libcef.dll").unlink()
            with self.assertRaises(FileNotFoundError):
                start_cef.validate_artifact("109", ENTRY)
            (executable.parent / "libcef.dll").write_bytes(b"dll")
            (executable.parent / "version.json").write_text(json.dumps(dict(ENTRY, cef_version="wrong")))
            with self.assertRaises(ValueError):
                start_cef.validate_artifact("109", ENTRY)

    def test_skip_build_refuses_missing_version_specific_snapshots_and_gpu_files(self) -> None:
        manifest = json.loads(start_cef.MANIFEST_PATH.read_text(encoding="utf-8"))
        cases = (
            ("109", "v8_context_snapshot.bin"), ("125", "snapshot_blob.bin"),
            ("128", "libEGL.dll"), ("133", "dxcompiler.dll"),
            ("154", "v8_context_snapshot.bin"),
        )
        with patch.object(start_cef, "CEF_ROOT", self.root):
            for version, filename in cases:
                executable = write_artifact(self.root, version, manifest[version])
                (executable.parent / filename).unlink()
                with self.subTest(version=version, filename=filename), redirect_stdout(io.StringIO()):
                    with self.assertRaisesRegex(FileNotFoundError, filename.replace(".", "\\.")):
                        start_cef.main(["--version", version, "--skip-build", "--no-launch"])

    def test_artifact_validation_respects_each_versions_manifest_runtime_files(self) -> None:
        manifest = json.loads(start_cef.MANIFEST_PATH.read_text(encoding="utf-8"))
        with patch.object(start_cef, "CEF_ROOT", self.root):
            for version, entry in manifest.items():
                executable = write_artifact(self.root, version, entry)
                self.assertEqual(executable, start_cef.validate_artifact(version, entry))
            latest = self.root / "dist" / "154"
            self.assertFalse((latest / "snapshot_blob.bin").exists())
            self.assertFalse((latest / "libEGL.dll").exists())

    def test_skip_build_refuses_missing_selected_or_fallback_locale(self) -> None:
        entry = json.loads(start_cef.MANIFEST_PATH.read_text(encoding="utf-8"))["109"]
        with patch.object(start_cef, "CEF_ROOT", self.root):
            for locale in ("zh-CN.pak", "en-US.pak"):
                executable = write_artifact(self.root, "109", entry)
                (executable.parent / "locales" / locale).unlink()
                with self.subTest(locale=locale), redirect_stdout(io.StringIO()):
                    with self.assertRaisesRegex(FileNotFoundError, locale.replace(".", "\\.")):
                        start_cef.main(["--version", "109", "--skip-build", "--no-launch"])

    def test_skip_build_validates_existing_binary_without_sdk_tools_or_download(self) -> None:
        write_artifact(self.root, "109", ENTRY)
        with (
            patch.object(start_cef, "CEF_ROOT", self.root),
            patch.object(start_cef, "ensure_sdk", side_effect=AssertionError("sdk")),
            patch.object(start_cef, "detect_build_tools", side_effect=AssertionError("tools")),
            redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(0, start_cef.main(["--version", "109", "--skip-build", "--no-launch"]))

    def test_skip_build_missing_binary_fails_without_download(self) -> None:
        with patch.object(start_cef, "CEF_ROOT", self.root), self.assertRaises(FileNotFoundError):
            start_cef.main(["--version", "109", "--skip-build", "--no-launch"])

    def test_all_versions_are_validated_before_any_launch(self) -> None:
        write_artifact(self.root, "109", ENTRY)
        with (
            patch.object(start_cef, "CEF_ROOT", self.root),
            patch.object(start_cef.subprocess, "Popen", side_effect=AssertionError("premature launch")),
            self.assertRaises(FileNotFoundError),
        ):
            start_cef.main(["--versions", "109", "125", "--skip-build"])

    def test_build_configures_exact_version_and_runs_release_incrementally(self) -> None:
        sdk = self.root / "sdk"
        write_sdk(sdk)
        executable = write_artifact(self.root, "109", ENTRY)
        with (
            patch.object(start_cef, "CEF_ROOT", self.root),
            patch.object(start_cef, "ensure_sdk", return_value=sdk),
            patch.object(start_cef, "detect_build_tools", return_value=(Path("cmake.exe"), "Visual Studio 18 2026")),
            patch.object(start_cef.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as run,
            redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(executable, start_cef.build_version("109", ENTRY, False))
        configure, build = [call.args[0] for call in run.call_args_list]
        self.assertIn(f"-DCEF_ROOT={sdk}", configure)
        self.assertIn("-DCEF_RANGE_MAJOR=109", configure)
        self.assertIn("-DUSE_SANDBOX=OFF", configure)
        self.assertIn("-DCMAKE_POLICY_VERSION_MINIMUM=3.5", configure)
        self.assertIn("Release", build)
        self.assertIn("cef-shooting-range-109", build)

    def test_launch_passes_arguments_and_uses_matching_dist_directory(self) -> None:
        executable = write_artifact(self.root, "109", ENTRY)
        process = subprocess.CompletedProcess([], 0)
        process.pid = 123
        process.poll = lambda: None
        with patch.object(start_cef.subprocess, "Popen", return_value=process) as launch:
            with redirect_stdout(io.StringIO()):
                start_cef.launch_versions(["109"], {"109": executable}, "http://localhost:7199/", 9222)
        self.assertEqual([str(executable), "--base-url=http://localhost:7199/", "--remote-debugging-port=9222"],
                         launch.call_args.args[0])
        self.assertEqual(executable.parent, launch.call_args.kwargs["cwd"])

    def test_partial_launch_failure_reports_pid_and_does_not_terminate_process(self) -> None:
        process = subprocess.CompletedProcess([], 0)
        process.pid = 321
        process.poll = lambda: None
        process.terminate = lambda: self.fail("must not terminate launched process")
        paths = {version: self.root / version / "range.exe" for version in ("109", "125")}
        with patch.object(start_cef.subprocess, "Popen", side_effect=[process, OSError("launch denied")]):
            with redirect_stdout(io.StringIO()), self.assertRaisesRegex(RuntimeError, "321"):
                start_cef.launch_versions(["109", "125"], paths, "https://example.com/#/", None)

    def test_launch_detects_a_real_process_that_exits_during_startup(self) -> None:
        real_popen = subprocess.Popen
        process = real_popen([sys.executable, "-c", "import sys,time; time.sleep(0.03); sys.exit(7)"])
        try:
            with patch.object(start_cef.subprocess, "Popen", return_value=process), redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(RuntimeError, "7"):
                    start_cef.launch_versions(["109"], {"109": self.root / "range.exe"}, "https://example.com/#/", None)
        finally:
            process.wait(timeout=10)


class VersionSelectorTests(unittest.TestCase):
    def select(self, keys: list[str]) -> tuple[list[str], str]:
        output = io.StringIO()
        with (
            patch.object(start_cef.sys.stdin, "isatty", return_value=True),
            patch.object(start_cef, "clear_screen") as clear,
            patch.object(start_cef, "read_key", side_effect=keys),
            redirect_stdout(output),
        ):
            # The redirected output is a test sink, not a noninteractive caller.
            output.isatty = lambda: True
            selected = start_cef.select_versions()
        clear.assert_called_once_with()
        return selected, output.getvalue()

    def test_selector_multiselects_and_redraws_in_place(self) -> None:
        selected, output = self.select(["enter", "down", "down", "space", "down", "down", "down", "enter"])
        self.assertEqual(["109", "128"], selected)
        self.assertIn("\x1b[H", output)
        self.assertIn("[✓] CEF 109", output)
        self.assertIn("[✓] CEF 128", output)
        for version in start_cef.VERSIONS:
            self.assertIn(f"CEF {version}", output)
        self.assertIn("[ 已完成选择 ]", output)

    def test_selector_unchecks_and_wraps_focus(self) -> None:
        selected, _ = self.select(["enter", "space", "up", "up", "enter", "down", "enter"])
        self.assertEqual(["154"], selected)

    def test_empty_confirmation_keeps_menu_open(self) -> None:
        selected, output = self.select(["up", "enter", "down", "enter", "up", "enter"])
        self.assertEqual(["109"], selected)
        self.assertIn("请至少选择一个 CEF 版本。", output)

    def test_escape_cancels_selection(self) -> None:
        selected, _ = self.select(["enter", "escape"])
        self.assertEqual([], selected)

    def test_interrupt_aborts_selection(self) -> None:
        with self.assertRaises(KeyboardInterrupt):
            self.select(["interrupt"])

    def test_main_uses_selection_and_prepares_all_before_launch(self) -> None:
        with (
            patch.object(start_cef, "select_versions", return_value=["109", "128"]) as select,
            patch.object(start_cef, "build_version", side_effect=lambda v, e, f: Path(v + '.exe')) as build,
            patch.object(start_cef, "launch_versions") as launch,
        ):
            self.assertEqual(0, start_cef.main([]))
        select.assert_called_once_with()
        self.assertEqual(["109", "128"], [call.args[0] for call in build.call_args_list])
        self.assertEqual(["109", "128"], launch.call_args.args[0])
        self.assertEqual({"109": Path('109.exe'), "128": Path('128.exe')}, launch.call_args.args[1])

    def test_main_cancel_does_not_load_manifest_build_or_launch(self) -> None:
        with (
            patch.object(start_cef, "select_versions", return_value=[]),
            patch.object(start_cef, "load_manifest") as manifest,
            patch.object(start_cef, "build_version") as build,
            patch.object(start_cef, "launch_versions") as launch,
            redirect_stdout(io.StringIO()) as output,
        ):
            self.assertEqual(0, start_cef.main([]))
        self.assertIn("已取消", output.getvalue())
        manifest.assert_not_called()
        build.assert_not_called()
        launch.assert_not_called()

    def test_interactive_multiple_versions_reject_shared_debug_port(self) -> None:
        with (
            patch.object(start_cef, "select_versions", return_value=["109", "125"]),
            patch.object(start_cef, "load_manifest") as manifest,
        ):
            with self.assertRaisesRegex(ValueError, "单个版本"):
                start_cef.main(["--remote-debugging-port", "9222"])
        manifest.assert_not_called()

    def test_explicit_versions_skip_interactive_menu(self) -> None:
        with (
            patch.object(start_cef, "select_versions") as select,
            patch.object(start_cef, "validate_artifact", return_value=Path('154.exe')),
            redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(0, start_cef.main(["--version", "154", "--skip-build", "--no-launch"]))
        select.assert_not_called()

    def test_noninteractive_input_requires_explicit_versions(self) -> None:
        with patch.object(start_cef.sys.stdin, "isatty", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "--version"):
                start_cef.select_versions()


if __name__ == "__main__":
    unittest.main()
