"""Run the single EXE from a Unicode directory with only Windows on PATH."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile

EXPECTED_CHECKS = 3093


def require(condition: bool, message: str, report: dict) -> None:
    # These are release gates, so they must survive python -O.
    if not condition:
        raise RuntimeError(f"{message}: {report}")


def verify(executable: Path, work_root: Path) -> dict:
    work_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="单文件 空格_", dir=work_root) as directory:
        working = Path(directory)
        copied = working / "PowerBuilder 靶场.exe"
        shutil.copyfile(executable, copied)
        report_path = working / "自检报告.json"
        environment = os.environ.copy()
        environment["PATH"] = str(Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32")
        for name in ("POWERBUILDER_RUNTIME", "POWERBUILDER_TOOLS", "UIAUTOMA_SDK_SOURCE"):
            environment.pop(name, None)
        completed = subprocess.run([str(copied), "--self-test", "--report", str(report_path)],
                                   cwd=working, env=environment, timeout=90)
        if not report_path.is_file():
            raise RuntimeError(f"Single EXE produced no report (exit {completed.returncode})")
        result = json.loads(report_path.read_text(encoding="utf-8-sig"))
        require(completed.returncode == 0, "Single EXE exited unsuccessfully", result)
        require(result["bundled_runtime_verified"] is True, "Bundled runtime was not verified", result)
        require(result["application"]["passed"] is True, "Application self-test failed", result)
        require(result["application"]["failed"] == 0, "Application reported failed checks", result)
        require(result["application"]["checks"] == EXPECTED_CHECKS, "Application check count changed", result)
        require(result["application"]["pages"] == 50, "Unexpected table page count", result)
        require(result["application"]["records"] == 1000, "Unexpected table record count", result)
        runtime = Path(result["loaded_runtime"])
        require(runtime.name.lower() == "pbvm.dll", "Unexpected runtime module", result)
        require(runtime.parent == Path(result["extraction_directory"]), "Runtime loaded outside extraction directory", result)
        require(not runtime.parent.exists(), "Package did not clean its extraction directory", result)
        return result


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    root = Path(__file__).resolve().parents[2]
    exe = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "POWERBUILDER" / "dist" / "PowerBuilder靶场.exe"
    print(json.dumps(verify(exe, root / ".private" / "pb-package-tests"), ensure_ascii=False, indent=2))
