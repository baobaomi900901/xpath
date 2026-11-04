"""Collect the Win32 BPL import closure for a local DevExpress evaluation build."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct


def imported_modules(path: Path) -> list[str]:
    data = path.read_bytes()
    pe = struct.unpack_from("<I", data, 60)[0]
    optional = pe + 24
    if data[:2] != b"MZ" or data[pe:pe + 4] != b"PE\0\0":
        raise ValueError(f"Invalid PE file: {path}")
    if struct.unpack_from("<H", data, pe + 4)[0] != 0x14C or struct.unpack_from("<H", data, optional)[0] != 0x10B:
        raise ValueError(f"A Win32 package is required: {path}")
    sections = []
    table = optional + struct.unpack_from("<H", data, pe + 20)[0]
    for index in range(struct.unpack_from("<H", data, pe + 6)[0]):
        size, address, raw_size, raw_offset = struct.unpack_from("<IIII", data, table + 40 * index + 8)
        sections.append((address, max(size, raw_size), raw_offset))

    def offset(rva: int) -> int:
        for address, size, raw_offset in sections:
            if address <= rva < address + size:
                return raw_offset + rva - address
        raise ValueError(f"Invalid import address in {path}")

    directory = struct.unpack_from("<I", data, optional + 104)[0]
    if not directory:
        return []
    result = []
    position = offset(directory)
    while any(data[position:position + 20]):
        name = offset(struct.unpack_from("<I", data, position + 12)[0])
        result.append(data[name:data.index(0, name)].decode("ascii"))
        position += 20
    return result


def collect(executable: Path, search_paths: list[Path]) -> list[Path]:
    queue = [executable]
    found: dict[str, Path] = {}
    for binary in queue:
        for name in imported_modules(binary):
            if not name.lower().endswith(".bpl") or name.lower() in found:
                continue
            if Path(name).name != name or "/" in name or "\\" in name:
                raise ValueError(f"Invalid package name: {name}")
            source = next((folder / name for folder in search_paths if (folder / name).is_file()), None)
            if source is None:
                raise FileNotFoundError(f"Missing runtime package {name}, required by {binary.name}")
            found[name.lower()] = source
            queue.append(source)
    return [found[name] for name in sorted(found)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("search_paths", nargs="+", type=Path)
    args = parser.parse_args()
    executable = args.executable.resolve(strict=True)
    packages = collect(executable, [path.resolve(strict=True) for path in args.search_paths])
    manifest = {"purpose": "local evaluation only; not for redistribution", "packages": []}
    for source in packages:
        target = executable.parent / source.name
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)
        manifest["packages"].append({"name": source.name, "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
    (executable.parent / "runtime-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (executable.parent / "LOCAL-EVALUATION-ONLY.txt").write_text(
        "Local DevExpress evaluation build. Keep the EXE and all BPL files together.\n"
        "Do not redistribute this evaluation build or its trial runtime packages.\n"
        "Official DevExpress trial prompts and restrictions remain enabled.\n", encoding="utf-8")
    print(f"Packaged {len(packages)} Win32 runtime BPL files for local evaluation.")


if __name__ == "__main__":
    main()
