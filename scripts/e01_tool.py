#!/usr/bin/env python3
"""E01 Reader — 使用 Lovelymem 的 dissect.ewf 模块 (已验证可用)"""
import sys, os, struct

DISSECT_PATH = r"E:\BaiduNetdiskDownload\Lovelymem\Lovelymem_20260312\Tools\MemProcFs\python\Lib\site-packages"
sys.path.insert(0, DISSECT_PATH)

from dissect.evidence.ewf import EWF


def e01_info(path):
    """读取 E01 分区信息"""
    ewf = EWF([path])
    stream = ewf.open()
    data = stream.read(4096)
    stream.close()

    info = {"size": ewf.size, "mbr": False, "gpt": False, "partitions": []}

    if len(data) >= 512 and data[510:512] == b"\x55\xaa":
        info["mbr"] = True
        for i in range(4):
            off = 446 + i * 16
            if data[off + 4] != 0:
                start = int.from_bytes(data[off + 8 : off + 12], "little")
                psize = int.from_bytes(data[off + 12 : off + 16], "little")
                ptype = data[off + 4]
                desc = {
                    0x07: "NTFS", 0x83: "Linux", 0x82: "Swap",
                    0x0B: "FAT32", 0x0C: "FAT32", 0xEE: "GPT", 0x0E: "FAT16",
                }.get(ptype, f"0x{ptype:02X}")
                info["partitions"].append({
                    "num": i, "type": ptype, "desc": desc,
                    "start": start, "size": psize,
                    "size_mb": psize * 512 / (1024 * 1024),
                })

    if b"EFI PART" in data[:1024]:
        info["gpt"] = True

    return info


def e01_read(path, offset, size):
    """从 E01 读取解压后数据"""
    ewf = EWF([path])
    stream = ewf.open()
    stream.seek(offset)
    data = stream.read(size)
    stream.close()
    return data


def main():
    if len(sys.argv) < 2:
        print("Usage: python e01_tool.py <E01_file>")
        print("       python e01_tool.py --all  (scan all E01 on Z:)")
        sys.exit(0)

    if sys.argv[1] == "--all":
        z = "Z:\\"
        for root, dirs, files in os.walk(z):
            for f in files:
                if f.lower().endswith(".e01"):
                    fp = os.path.join(root, f)
                    rel = os.path.relpath(fp, z)
                    try:
                        info = e01_info(fp)
                        parts = ", ".join(
                            f"{p['desc']}({p['size_mb']:.0f}MB)" for p in info["partitions"][:3]
                        ) or "no partitions"
                        print(f"  {rel} ({info['size']/(1024**2):.0f}MB) [{parts}]")
                    except Exception as e:
                        print(f"  {rel} ERROR: {e}")
        sys.exit(0)

    path = sys.argv[1]
    info = e01_info(path)
    print(f"File: {path}")
    print(f"  Size: {info['size']/(1024**2):.0f} MB")
    print(f"  MBR: {info['mbr']}, GPT: {info['gpt']}")
    if info["partitions"]:
        print("  Partitions:")
        for p in info["partitions"]:
            print(f"    {p['num']}: {p['desc']} start={p['start']} size={p['size_mb']:.0f}MB")


if __name__ == "__main__":
    main()
