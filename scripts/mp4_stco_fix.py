#!/usr/bin/env python3
"""
MP4 STCO Table Fixer — 修复被恶意软件加密的 MP4 文件
=====================================================
来源: 2026 FIC 初赛 Writeup (https://mei-you-qian.github.io/)
场景: 勒索软件将 MP4 的 stco 表每个 chunk_offset 加了 1337

用法:
  python mp4_stco_fix.py encrypted.mp4          # 解密 (key=1337)
  python mp4_stco_fix.py encrypted.mp4 -k 1000  # 自定义 key
  python mp4_stco_fix.py *.mp4                  # 批量
"""
import sys
import struct
from pathlib import Path

KEY = 0x539  # 1337 (默认值, FIC 2026 使用)


def fix_one(path: Path, key: int, out_path: Path | None = None) -> bool:
    data = bytearray(path.read_bytes())

    idx = data.find(b"stco")
    if idx == -1:
        print(f"[-] {path}: stco atom not found")
        return False

    if len(data) < idx + 12:
        print(f"[-] {path}: invalid stco structure")
        return False

    entry_count = struct.unpack(">I", data[idx + 8 : idx + 12])[0]

    table_start = idx + 12
    table_end = table_start + entry_count * 4

    if len(data) < table_end:
        print(f"[-] {path}: stco table out of range, entry_count={entry_count}")
        return False

    print(f"[+] {path}: stco at 0x{idx:x}, entries={entry_count}")

    for i in range(entry_count):
        pos = table_start + i * 4
        old = struct.unpack(">I", data[pos : pos + 4])[0]

        if old < key:
            print(f"[!] offset too small at entry {i}, old={old}, skip")
            continue

        new = old - key
        data[pos : pos + 4] = struct.pack(">I", new)

    if out_path is None:
        out_path = path.with_name(path.stem + "_fixed" + path.suffix)

    out_path.write_bytes(data)
    print(f"[+] saved: {out_path}")
    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fix MP4 stco table (ransomware recovery)")
    parser.add_argument("files", nargs="+", help="MP4 files to fix")
    parser.add_argument("-k", "--key", type=int, default=KEY, help=f"Offset delta (default: {KEY})")
    parser.add_argument("-o", "--output", help="Output file (single file only)")
    args = parser.parse_args()

    for i, name in enumerate(args.files):
        path = Path(name)
        if not path.is_file():
            print(f"[-] not a file: {path}")
            continue

        out = Path(args.output) if args.output and len(args.files) == 1 else None
        fix_one(path, args.key, out)


if __name__ == "__main__":
    main()
