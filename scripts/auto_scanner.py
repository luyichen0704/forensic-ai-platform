#!/usr/bin/env python3
"""
CTF Auto Scanner — 对任意文件执行第一轮全面扫描
==============================================
自动运行: file → hash → strings → exiftool → binwalk → 嵌套文件检测
并将可疑发现高亮输出。

用法:
  python auto_scanner.py <file>
  python auto_scanner.py -d ./cases/   # 扫描目录
"""
import subprocess
import sys
import os
import hashlib
import re
from pathlib import Path
from datetime import datetime

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

FLAG_PATTERNS = [
    rb"flag\{[^}]+\}",
    rb"CTF\{[^}]+\}",
    rb"[A-Za-z0-9+/=]{24,}={0,2}",  # Base64-like
    rb"https?://[^\s<>\"']+",
    rb"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
]

SENSITIVE_KEYWORDS = [
    b"flag", b"ctf", b"password", b"secret", b"key", b"token",
    b"admin", b"root", b"login", b"api_key", b"private",
]


def section(title: str, color: str = CYAN) -> None:
    print(f"\n{color}{'=' * 60}{RESET}")
    print(f"{BOLD}{color}{title}{RESET}")
    print(f"{color}{'=' * 60}{RESET}")


def run_cmd(cmd: list[str], timeout: int = 30) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=timeout, text=False)
        return (result.stdout + result.stderr).decode("utf-8", errors="replace")
    except Exception as e:
        return f"[ERROR] {e}"


def scan_file(filepath: Path) -> list[str]:
    findings = []
    fname = str(filepath)

    # 1. 基本信息
    section(f"FILE: {filepath.name}")

    # 大小
    size = filepath.stat().st_size
    print(f"  Size: {size:,} bytes ({size / 1024:.1f} KB)")

    # 类型
    out = run_cmd(["file", fname])
    print(f"  Type: {out.strip()}")

    # 哈希
    with open(filepath, "rb") as f:
        data = f.read()
    md5 = hashlib.md5(data).hexdigest()
    sha256 = hashlib.sha256(data).hexdigest()
    print(f"  MD5:    {md5}")
    print(f"  SHA256: {sha256}")

    # 2. 字符串扫描
    section("STRINGS SCAN")
    try:
        strings_output = subprocess.run(
            ["strings", fname], capture_output=True, timeout=30
        ).stdout

        # 搜索 flag 模式
        for pattern in FLAG_PATTERNS:
            matches = re.findall(pattern, strings_output)
            for m in matches:
                try:
                    decoded = m.decode("utf-8", errors="replace")
                except Exception:
                    decoded = str(m)
                print(f"{GREEN}[FLAG?] {decoded}{RESET}")
                findings.append(f"Flag candidate: {decoded}")

        # 搜索敏感关键词
        for kw in SENSITIVE_KEYWORDS:
            if kw in strings_output.lower():
                count = strings_output.lower().count(kw)
                print(f"{YELLOW}[KW] '{kw.decode()}' found {count} times{RESET}")
    except FileNotFoundError:
        print("  (strings not available in PATH)")

    # 3. EXIF
    section("EXIF SCAN")
    exif_out = run_cmd(["exiftool", fname])
    for line in exif_out.split("\n"):
        if any(kw in line.lower() for kw in ["flag", "ctf", "comment", "warning"]):
            print(f"{YELLOW}{line}{RESET}")
    # 只显示关键行
    summary_lines = [l for l in exif_out.split("\n") if l.strip() and ":" in l]
    if len(summary_lines) > 20:
        print(f"  ({len(summary_lines)} EXIF fields total, showing first 20)")
        for line in summary_lines[:20]:
            print(f"  {line}")
    else:
        for line in summary_lines:
            print(f"  {line}")

    # 4. Binwalk
    section("BINWALK SCAN")
    binwalk_out = run_cmd(["binwalk", fname], timeout=60)
    lines = [l for l in binwalk_out.split("\n") if l.strip()]
    if len(lines) > 30:
        print(f"  ({len(lines)} entries, showing first 30)")
        for line in lines[:30]:
            print(f"  {line}")
    else:
        for line in lines:
            print(f"  {line}")

    # 5. 嵌套文件检测
    section("NESTED FILES")
    out_7z = run_cmd(["7z", "l", fname])
    if "Type = zip" in out_7z or "Type = 7z" in out_7z or "Type = gzip" in out_7z:
        print(f"{YELLOW}  Archive detected!{RESET}")
        for line in out_7z.split("\n")[-20:]:
            print(f"  {line}")
    else:
        print("  Not a known archive format")

    # 6. 十六进制头部
    section("HEX HEADER (first 256 bytes)")
    hex_out = run_cmd(["xxd", "-l", "256", fname])
    print(hex_out[:2000])

    # 7. 文件末尾检查
    section("TAIL CHECK (last 50 strings)")
    tail = data[-4096:] if len(data) > 4096 else data
    try:
        tail_strings = subprocess.run(
            ["strings"], input=tail, capture_output=True, timeout=10
        ).stdout
        for line in tail_strings.decode("utf-8", errors="replace").split("\n")[-20:]:
            if line.strip():
                print(f"  {line}")
    except Exception:
        pass

    return findings


def main():
    print(f"{BOLD}{GREEN}CTF Auto Scanner{RESET}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version}")

    if len(sys.argv) < 2:
        print("\n用法:")
        print("  python auto_scanner.py <file>")
        print("  python auto_scanner.py -d <directory>")
        sys.exit(1)

    if sys.argv[1] == "-d" and len(sys.argv) >= 3:
        dirpath = Path(sys.argv[2])
        if not dirpath.is_dir():
            print(f"[-] Not a directory: {dirpath}")
            sys.exit(1)
        for f in sorted(dirpath.iterdir()):
            if f.is_file():
                try:
                    scan_file(f)
                except Exception as e:
                    print(f"{RED}[ERROR] {f.name}: {e}{RESET}")
        return

    filepath = Path(sys.argv[1])
    if not filepath.is_file():
        print(f"[-] Not a file: {filepath}")
        sys.exit(1)

    findings = scan_file(filepath)

    section("SUMMARY", GREEN)
    if findings:
        print(f"{GREEN}Found {len(findings)} potential flag(s):{RESET}")
        for f in findings:
            print(f"  {GREEN}→ {f}{RESET}")
    else:
        print(f"{YELLOW}No obvious flags found — try deeper analysis tools.{RESET}")


if __name__ == "__main__":
    main()
