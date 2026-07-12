#!/usr/bin/env python3
"""
VC Mount Auto-Detector — 自动发现挂载盘符并分析
==============================================
比赛场景: VeraCrypt 容器挂载到 Z:/Y:/X: 等盘符
用法:
  python vc_mount_tool.py                  # 自动检测并扫描
  python vc_mount_tool.py -q "题目文本"     # 带关键词定向搜索
  python vc_mount_tool.py --watch           # 持续监控，挂载后自动分析
"""
import os
import sys
import time
import string
import argparse
from pathlib import Path
from datetime import datetime


# 可能的挂载盘符（Z 优先，向后递减）
CANDIDATE_DRIVES = ["Z:", "Y:", "X:", "W:", "V:", "U:", "T:"]


def detect_mounted_drives() -> list[str]:
    """检测所有已挂载的盘符"""
    mounted = []
    for drive in CANDIDATE_DRIVES:
        if os.path.exists(drive):
            mounted.append(drive)
    return mounted


def get_drive_stats(drive: str) -> dict:
    """获取盘符的基本统计信息"""
    total_files = 0
    total_dirs = 0
    top_dirs = []

    try:
        root = Path(drive)
        for entry in sorted(root.iterdir()):
            if entry.is_dir():
                total_dirs += 1
                top_dirs.append(entry.name)
            else:
                total_files += 1
    except PermissionError:
        pass

    # 尝试获取总大小
    total_size = 0
    for entry in Path(drive).rglob("*"):
        try:
            if entry.is_file():
                total_size += entry.stat().st_size
        except Exception:
            pass
        if total_size > 10 * 1024 * 1024 * 1024:  # 超过 10GB 停止
            total_size = -1
            break

    return {
        "drive": drive,
        "dirs": total_dirs,
        "files_top_level": total_files,
        "size_estimate": total_size if total_size >= 0 else ">10 GB",
    }


def quick_flag_hunt(drive: str, max_files: int = 500) -> list[dict]:
    """在挂载盘上快速搜索 flag 关键词"""
    import subprocess

    findings = []
    keywords = [b"flag{", b"CTF{", b"password", b"secret", b"key", b"token"]
    count = 0

    print(f"\n  Flag hunt ({max_files} files max)...")

    for root, dirs, files in os.walk(drive):
        # 跳过系统目录加速
        dirs[:] = [d for d in dirs if d not in
                   {"Windows", "WinSxS", "System32", "Program Files", "$Recycle.Bin"}]

        for fname in files:
            if count >= max_files:
                break
            fpath = os.path.join(root, fname)
            try:
                size = os.path.getsize(fpath)
                if size > 50 * 1024 * 1024:  # 跳过 >50MB
                    continue
                with open(fpath, "rb") as f:
                    data = f.read(min(size, 1024 * 1024))
                for kw in keywords:
                    if kw in data.lower():
                        findings.append({
                            "file": fpath,
                            "keyword": kw.decode(),
                            "size": size,
                        })
                        print(f"  [HIT] {fpath} → {kw.decode()}")
                        break
                count += 1
                if count % 100 == 0:
                    print(f"  ... {count} files scanned")
            except Exception:
                pass

    return findings


def watch_mode(interval: int = 5):
    """监控模式: 持续检测，发现挂载后自动分析"""
    print(f"WATCH MODE — checking every {interval}s for new mounts...")
    print("Mount VeraCrypt to Z: and I'll auto-analyze.\n")

    known_drives = set()

    while True:
        current = set(detect_mounted_drives())
        new_drives = current - known_drives

        if new_drives:
            for drive in sorted(new_drives, reverse=True):
                print(f"\n{'='*60}")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] NEW MOUNT: {drive}")
                print(f"{'='*60}")

                stats = get_drive_stats(drive)
                print(f"  Directories: {stats['dirs']}")
                print(f"  Top-level files: {stats['files_top_level']}")
                if isinstance(stats['size_estimate'], str):
                    print(f"  Size: {stats['size_estimate']}")
                else:
                    print(f"  Size: {stats['size_estimate'] / (1024*1024):.0f} MB")

                # 自动开始 flag 搜索
                findings = quick_flag_hunt(drive, max_files=300)
                if findings:
                    print(f"\n  Found {len(findings)} flag candidates!")
                else:
                    print(f"\n  No flags found in quick scan.")

            known_drives = current

        # 检测卸载
        unmounted = known_drives - current
        if unmounted:
            for d in unmounted:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] UNMOUNTED: {d}")

        known_drives = current
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="VC Mount Auto-Detector")
    parser.add_argument("-q", "--questions", nargs="*", help="题目文本（定向搜索）")
    parser.add_argument("--watch", action="store_true", help="监控模式")
    parser.add_argument("-d", "--drive", help="指定盘符 (默认: 自动检测)")
    parser.add_argument("--scan", action="store_true", help="立即全面扫描")
    args = parser.parse_args()

    # 监控模式
    if args.watch:
        watch_mode()
        return

    # 检测挂载
    drives = [args.drive] if args.drive else detect_mounted_drives()

    if not drives:
        print("No mounted drives found (checked Z Y X W V U T)")
        print("\nMount your VeraCrypt container, then run:")
        print("  python vc_mount_tool.py --scan")
        print("  OR")
        print("  python vc_mount_tool.py --watch  (auto-detect)")
        sys.exit(1)

    drive = drives[0]  # 优先使用第一个（字母序最大 = Z 优先）
    print(f"Using: {drive}")

    # 基础统计
    stats = get_drive_stats(drive)
    print(f"\n--- Drive Stats ---")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    # 快速 flag 搜索
    findings = quick_flag_hunt(drive)

    # 如果有题目，定向搜索
    if args.questions:
        print(f"\n--- Smart Search: {' '.join(args.questions)} ---")
        # 调用 smart_hunter
        import subprocess
        cmd = [
            sys.executable,
            str(Path(__file__).parent / "smart_hunter.py"),
            "-c", drive,
            "-q",
        ] + args.questions
        try:
            subprocess.run(cmd)
        except Exception as e:
            print(f"  Smart hunter error: {e}")

    # 汇总
    print(f"\n{'='*60}")
    print(f"SUMMARY: {len(findings)} flag candidates on {drive}")
    if findings:
        for f in findings[:10]:
            print(f"  → {f['file']}  [{f['keyword']}]")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
