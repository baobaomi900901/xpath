"""Publishing checks must also run when Python optimization is enabled."""
from copy import deepcopy
from pathlib import Path
import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from POWERBUILDER.verify.package_smoke import EXPECTED_CHECKS, verify


class PackageVerificationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="Appeon_package_checks_")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.executable = self.root / "package.exe"
        self.executable.write_bytes(b"mock executable")
        self.extracted = self.root / "PowerBuilderRange-test"
        self.report = {
            "bundled_runtime_verified": True,
            "loaded_runtime": str(self.extracted / "pbvm.dll"),
            "extraction_directory": str(self.extracted),
            "application": {"passed": True, "checks": EXPECTED_CHECKS, "failed": 0,
                            "pages": 50, "records": 1000},
        }

    def run_verification(self, report=None, returncode=0):
        def child(command, **kwargs):
            Path(command[-1]).write_text(json.dumps(report or self.report), encoding="utf-8")
            return subprocess.CompletedProcess(command, returncode)
        with patch("POWERBUILDER.verify.package_smoke.subprocess.run", side_effect=child):
            return verify(self.executable, self.root / "verification")

    def test_rejects_failed_exit_with_passing_report(self):
        with self.assertRaises(RuntimeError):
            self.run_verification(returncode=1)

    def test_rejects_failed_verification_fields(self):
        for field, value in (("bundled_runtime_verified", False), ("passed", False),
                             ("failed", 1), ("checks", EXPECTED_CHECKS - 1), ("pages", 49), ("records", 999)):
            with self.subTest(field=field):
                report = deepcopy(self.report)
                target = report if field == "bundled_runtime_verified" else report["application"]
                target[field] = value
                with self.assertRaises(RuntimeError):
                    self.run_verification(report)

    def test_rejects_runtime_outside_extraction_directory(self):
        report = deepcopy(self.report)
        report["loaded_runtime"] = str(self.root / "installed" / "pbvm.dll")
        with self.assertRaises(RuntimeError):
            self.run_verification(report)

    def test_rejects_uncleaned_extraction_directory(self):
        self.extracted.mkdir()
        with self.assertRaises(RuntimeError):
            self.run_verification()

    def test_accepts_valid_package_in_appeon_named_temp_directory(self):
        self.assertEqual(self.run_verification(), self.report)


if __name__ == "__main__":
    unittest.main()
