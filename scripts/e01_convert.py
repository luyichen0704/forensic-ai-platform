#!/usr/bin/env python3
"""E01 → RAW 批量转换 (使用 Arsenal Image Mounter CLI, 无需管理员)"""
import sys, os, subprocess
from pathlib import Path

AIM_CLI = r"C:\Users\luyic\Downloads\Arsenal.Image.Mounter.Pro.v.3.0.64\Arsenal.Image.Mounter.v.3.0.64\aim_cli.exe"
RAW_DIR = r"E:\raw"

os.makedirs(RAW_DIR, exist_ok=True)

def convert(e01_path, raw_name=None):
    """单个 E01 转换"""
    e01_path = str(Path(e01_path))
    if raw_name is None:
        raw_name = Path(e01_path).stem + ".raw"
    out_path = os.path.join(RAW_DIR, raw_name)

    if os.path.exists(out_path):
        print(f"  SKIP: {out_path} already exists")
        return True

    print(f"  Converting: {e01_path} → {out_path}")
    result = subprocess.run(
        [AIM_CLI, "/filename=" + e01_path, "/provider=LibEWF", "/convert=" + out_path],
        capture_output=True, text=True, timeout=3600
    )
    if "successfully" in result.stdout.lower():
        print(f"  DONE: {out_path}")
        return True
    else:
        print(f"  FAILED: {result.stderr or result.stdout}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python e01_convert.py Z:/path/file.E01")
        print("  python e01_convert.py --batch  (批量转换 P0 列表)")
        sys.exit(0)

    if sys.argv[1] == "--batch":
        # P0 转换列表
        p0 = [
            (r"Z:\刘洋\liuyang_pc.E01", "liuyang_pc.raw"),
            (r"Z:\黄志远\PC.E01", "huangzhiyuan_pc.raw"),
            (r"Z:\服务器\server01\server01-disk01.E01", "srv1-disk01.raw"),
            (r"Z:\服务器\server02\server02-disk01.E01", "srv2-disk01.raw"),
            (r"Z:\服务器\server03\server03-disk01.E01", "srv3-disk01.raw"),
        ]
        for e01, name in p0:
            if os.path.exists(e01):
                convert(e01, name)
            else:
                print(f"  MISSING: {e01}")
    else:
        convert(sys.argv[1])
