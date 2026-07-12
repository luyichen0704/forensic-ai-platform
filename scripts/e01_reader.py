#!/usr/bin/env python3
"""
E01 Reader — 使用 libewf.dll 直接读取 E01
用法:
  python e01_reader.py info Z:\黄志远\car.E01
  python e01_reader.py extract Z:\黄志远\car.E01 output.raw
"""
import ctypes, sys, os
from ctypes import c_void_p, c_char_p, c_int, c_size_t, c_uint64, POINTER, byref, create_string_buffer

LIBEWF_PATH = r"D:\BaiduNetdiskDownload\BootMagixV4\libewf.dll"
lib = ctypes.WinDLL(LIBEWF_PATH)

# === Function signatures ===
lib.libewf_handle_initialize.argtypes = [POINTER(c_void_p), POINTER(c_void_p)]
lib.libewf_handle_initialize.restype = c_int

lib.libewf_handle_open.argtypes = [c_void_p, POINTER(c_char_p), c_int, c_int, POINTER(c_void_p)]
lib.libewf_handle_open.restype = c_int

lib.libewf_handle_get_media_size.argtypes = [c_void_p, POINTER(c_void_p)]
lib.libewf_handle_get_media_size.restype = c_uint64

lib.libewf_handle_read_buffer.argtypes = [c_void_p, c_void_p, c_size_t, POINTER(c_void_p)]
lib.libewf_handle_read_buffer.restype = ctypes.c_ssize_t

lib.libewf_handle_seek_offset.argtypes = [c_void_p, c_uint64, c_int, POINTER(c_void_p)]
lib.libewf_handle_seek_offset.restype = c_uint64

lib.libewf_handle_close.argtypes = [c_void_p, POINTER(c_void_p)]
lib.libewf_handle_close.restype = c_int

lib.libewf_handle_get_bytes_per_sector.argtypes = [c_void_p, POINTER(c_int), POINTER(c_void_p)]
lib.libewf_handle_get_bytes_per_sector.restype = c_int


def e01_info(path):
    """读取 E01 文件信息"""
    h = c_void_p()
    e = c_void_p()

    if lib.libewf_handle_initialize(byref(h), byref(e)) != 1:
        return None

    fname = path.encode("utf-8")
    fnames = (c_char_p * 1)(fname)
    if lib.libewf_handle_open(h, fnames, 1, 0, byref(e)) != 1:
        lib.libewf_handle_close(h, byref(e))
        return None

    size = lib.libewf_handle_get_media_size(h, byref(e))
    bps = c_int()
    lib.libewf_handle_get_bytes_per_sector(h, byref(bps), byref(e))

    # Read the first 512 bytes to check filesystem
    raw = ctypes.create_string_buffer(512)
    lib.libewf_handle_seek_offset(h, 0, 0, byref(e))
    n = lib.libewf_handle_read_buffer(h, raw, 512, byref(e))
    first_bytes = raw.raw[:n] if n > 0 else b""

    lib.libewf_handle_close(h, byref(e))

    # Detect filesystem type from first bytes
    fs_type = "unknown"
    if first_bytes[:4] == b"\xeb\x52\x90NTFS":
        fs_type = "NTFS"
    elif first_bytes[:3] == b"\xeb\x3c\x90":
        fs_type = "FAT32"
    elif b"EFI PART" in first_bytes:
        fs_type = "GPT"
    elif first_bytes[510:512] == b"\x55\xaa":
        fs_type = "MBR"
    elif first_bytes[:4] == b"\x7fELF":
        fs_type = "ELF (not a disk)"
    elif first_bytes[:4] == b"\x89PNG":
        fs_type = "PNG (not a disk)"

    return {
        "path": path,
        "media_size": size,
        "media_size_mb": size / (1024 * 1024),
        "bytes_per_sector": bps.value,
        "filesystem": fs_type,
        "first_hex": first_bytes[:32].hex(),
    }


def e01_extract(path, output, chunk_mb=100):
    """提取 E01 为 RAW"""
    h = c_void_p()
    e = c_void_p()

    if lib.libewf_handle_initialize(byref(h), byref(e)) != 1:
        return False

    fname = path.encode("utf-8")
    fnames = (c_char_p * 1)(fname)
    if lib.libewf_handle_open(h, fnames, 1, 0, byref(e)) != 1:
        return False

    size = lib.libewf_handle_get_media_size(h, byref(e))
    chunk = chunk_mb * 1024 * 1024
    total = 0

    with open(output, "wb") as f:
        while total < size:
            read_size = min(chunk, size - total)
            buf = ctypes.create_string_buffer(read_size)
            lib.libewf_handle_seek_offset(h, total, 0, byref(e))
            n = lib.libewf_handle_read_buffer(h, buf, read_size, byref(e))
            if n <= 0:
                break
            f.write(buf.raw[:n])
            total += n
            pct = total / size * 100
            print(f"\r  {total/(1024*1024):.0f}/{size/(1024*1024):.0f} MB ({pct:.1f}%)", end="")

    lib.libewf_handle_close(h, byref(e))
    print()
    return total >= size


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("E01 Reader (uses libewf.dll from BootMagixV4)")
        print("  python e01_reader.py info <E01 file>")
        print("  python e01_reader.py extract <E01 file> <output.raw>")
        print()
        # 检测 Z:
        z = "Z:\\"
        if os.path.exists(z):
            print(f"Z: drive available:")
            for d in sorted(os.listdir(z)):
                dp = os.path.join(z, d)
                if os.path.isdir(dp):
                    for f in sorted(os.listdir(dp)):
                        if f.lower().endswith(".e01"):
                            fp = os.path.join(dp, f)
                            sz = os.path.getsize(fp)
                            print(f"  {d}/{f} ({sz/(1024*1024):.0f} MB)")
        sys.exit(0)

    cmd, path = sys.argv[1], sys.argv[2]

    if cmd == "info":
        info = e01_info(path)
        if info:
            for k, v in info.items():
                if isinstance(v, float):
                    print(f"{k}: {v:.1f}")
                else:
                    print(f"{k}: {v}")
        else:
            print(f"FAILED to read: {path}")
            sys.exit(1)
    elif cmd == "extract":
        out = sys.argv[3]
        e01_extract(path, out)
