"""Exercise actual Qt windows through an out-of-process Windows UIA client."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.start_qt import VERSIONS, validate_artifact, runtime_environment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--versions', nargs='+', choices=VERSIONS, default=list(VERSIONS))
    args = parser.parse_args()
    for version in args.versions:
        for frontend in ('widgets', 'quick'):
            exe = validate_artifact(version, frontend)
            process = subprocess.Popen([str(exe)], cwd=exe.parent, env=runtime_environment(),
                                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            try:
                subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                                str(Path(__file__).with_name('uia-smoke.ps1')), '-TargetPid', str(process.pid),
                                '-QtVersion', version, '-Frontend', frontend], check=True, timeout=45)
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=10)


if __name__ == '__main__':
    main()
