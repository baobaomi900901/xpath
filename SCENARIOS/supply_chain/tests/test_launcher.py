import json
import unittest
from pathlib import Path

from tools import start_supply_chain as launcher
from support import WorkspaceTemporaryDirectory


class LauncherTests(unittest.TestCase):
    def test_defaults_and_explicit_tracks(self):
        args = launcher.parse_args([])
        self.assertEqual(args.command, "launch")
        self.assertEqual(args.profile, "standard")
        self.assertEqual(args.port, 8765)
        self.assertFalse(args.obstacles)
        self.assertEqual(launcher.parse_args(["reset", "--track", "sdk", "--seed", "7"]).track, "sdk")

    def test_obstacles_are_persisted_and_forwarded_to_both_desktop_apps(self):
        with WorkspaceTemporaryDirectory() as temp:
            args = launcher.parse_args(["reset", "--obstacles", "--profile", "basic"])
            path = launcher.new_run(args, Path(temp))
            fixture = json.loads((path / "fixture.json").read_text(encoding="utf-8"))
            metadata = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
            self.assertTrue(fixture["context"]["obstacles"])
            self.assertTrue(metadata["obstacles"])
            commands = launcher.app_commands("http://127.0.0.1:8765", fixture["context"]["obstacles"], Path("javaw.exe"))
            self.assertEqual(len(commands), 2)
            self.assertTrue(all(command[-1] == "--obstacles" for command in commands))
            defaults = launcher.app_commands("http://127.0.0.1:8765", False, Path("javaw.exe"))
            self.assertTrue(all("--obstacles" not in command for command in defaults))

    def test_obstacles_leave_seeded_business_data_unchanged(self):
        with WorkspaceTemporaryDirectory() as temp:
            args = launcher.parse_args(["reset", "--profile", "standard", "--seed", "42"])
            baseline = launcher.new_run(args, Path(temp))
            args.obstacles = True
            obstacle = launcher.new_run(args, Path(temp))
            first = json.loads((baseline / "fixture.json").read_text(encoding="utf-8"))
            second = json.loads((obstacle / "fixture.json").read_text(encoding="utf-8"))
            for key in ("inventory", "quotes", "suppliers"):
                self.assertEqual(first[key], second[key])
            self.assertFalse(first["context"]["obstacles"])
            self.assertTrue(second["context"]["obstacles"])

    def test_run_creation_does_not_delete_or_overwrite_prior_results(self):
        with WorkspaceTemporaryDirectory() as temp:
            root = Path(temp)
            args = launcher.parse_args(["reset", "--profile", "basic", "--seed", "7", "--agent", "demo"])
            first = launcher.new_run(args, root)
            marker = first / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            second = launcher.new_run(args, root)
            self.assertNotEqual(first, second)
            self.assertTrue(marker.exists())
            self.assertEqual(Path(json.loads((root / "current.json").read_text())["run_dir"]), second)

    def test_generated_task_contains_business_rules_and_no_answers(self):
        with WorkspaceTemporaryDirectory() as temp:
            args = launcher.parse_args(["reset", "--profile", "basic", "--track", "sdk"])
            path = launcher.new_run(args, Path(temp))
            text = (path / "task.md").read_text(encoding="utf-8")
            self.assertIn("SDK", text)
            self.assertIn("2026-11-24", text)
            self.assertIn("127.0.0.1:8765", text)
            self.assertNotIn("Q001", text)
            self.assertNotIn("1700", text)
            self.assertNotIn("/api/", text)

    def test_catalog_has_real_entry_and_config_validates(self):
        from tools.range_launcher.config import load_catalog
        config = load_catalog(launcher.REPO_ROOT / "tools" / "ranges.json")
        self.assertIn("supply-chain", [r["id"] for r in config["ranges"]])


if __name__ == "__main__":
    unittest.main()
