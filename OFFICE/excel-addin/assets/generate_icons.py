"""用 Python 标准库生成插件所需的 PNG 图标(无需 Pillow)。"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent
GREEN = (33, 115, 70)
WHITE = (255, 255, 255)


def _chunk(tag: bytes, data: bytes) -> bytes:
    payload = tag + data
    return struct.pack(">I", len(data)) + payload + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)


def _pixel(x: int, y: int, size: int) -> tuple[int, int, int]:
    margin = max(1, size // 8)
    border = margin * 2
    if x < border or y < border or x >= size - border or y >= size - border:
        return WHITE
    # 左上到右下的对角线 + 右上到左下的对角线, 组成 X
    if abs(x - y) <= margin or abs((size - 1 - x) - y) <= margin:
        return WHITE
    return GREEN


def render_png(size: int) -> bytes:
    rows = bytearray()
    for y in range(size):
        rows.append(0)  # filter type 0
        for x in range(size):
            rows.extend(_pixel(x, y, size))
    header = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", zlib.compress(bytes(rows), 9))
        + _chunk(b"IEND", b"")
    )


def main() -> int:
    for size in (16, 32, 80):
        target = OUTPUT_DIR / f"icon-{size}.png"
        target.write_bytes(render_png(size))
        print(f"已生成 {target} ({target.stat().st_size} 字节)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
