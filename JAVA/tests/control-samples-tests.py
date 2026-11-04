"""Compile and run Swing sample checks with the explicitly installed local JDKs."""
import argparse
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--versions", nargs="+", choices=("8", "11", "17", "21", "25"),
                        default=["8", "11", "17", "21", "25"])
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = root / "src/main/java/com/xpath/shootingrange/ui"
    for version in args.versions:
        compilers = list((root / ".tools/jdks/corretto" / version).glob("*/bin/javac.exe"))
        if len(compilers) != 1:
            raise RuntimeError(f"Expected one local JDK {version} compiler, found {compilers}")
        compiler = compilers[0]
        output = root / "target/control-samples-tests" / version
        output.mkdir(parents=True, exist_ok=True)
        subprocess.run([str(compiler), "-encoding", "UTF-8", "-d", str(output),
                        *[str(source / f"{name}.java") for name in
                          ("SamplePanelLayout", "ControlSamplesPanel", "DynamicSamplesPanel")],
                        str(root / "tests/ControlSamplesPanelTest.java")], check=True)
        subprocess.run([str(compiler.with_name("java.exe")), "-Djava.awt.headless=true",
                        "-cp", str(output), "ControlSamplesPanelTest"], check=True)
        print(f"JDK {version} control samples passed.", flush=True)


if __name__ == "__main__":
    main()
