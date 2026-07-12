#!/usr/bin/env python3
"""E01 Reader - stream decompress via zlib, no libewf needed."""
import sys, os, struct, zlib

def stream_decompress(path):
    """Stream through E01, decompressing zlib blocks as found."""
    with open(path, "rb") as f:
        # Read header (first 4KB)
        header = f.read(4096)

        # Find "sectors" section to know where data starts
        idx = header.find(b"sectors")
        if idx < 0:
            idx = header.find(b"sectors2")
        if idx < 0:
            print("Cannot find sectors section")
            return b""

        # Section header: name(16) + next_offset(8) + size(8) + pad(40) = 76 bytes
        # But name might not be exactly 16 bytes, scan for the struct
        # Actually: the section starts with the name, then 8+8+40 bytes
        # Let me just jump to where the actual data starts
        # First skip past the name and padding
        pos = idx
        while pos < len(header) and header[pos] != 0:
            pos += 1
        while pos < len(header) and header[pos] == 0:
            pos += 1
        data_start = pos + 16  # skip next_offset(8) + size(8)

        f.seek(data_start)

        result = bytearray()
        buf = b""
        chunk_size = 1024 * 1024  # Read 1MB at a time

        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break

            buf += chunk
            # Search for and decompress zlib blocks in the buffer
            i = 0
            while i < len(buf) - 2:
                if buf[i] == 0x78 and buf[i + 1] in (0x01, 0x5E, 0x9C, 0xDA):
                    # Found zlib header, try to decompress
                    for wbits in [15, -15]:
                        try:
                            dec = zlib.decompress(buf[i:i + 65536], wbits)
                            result.extend(dec)
                            i += 1
                            break
                        except:
                            continue
                    i += 1
                else:
                    i += 1

            # Keep only the last 64KB for cross-chunk zlib boundaries
            buf = buf[-65536:]

            if len(result) > 0:
                mb = len(result) / (1024 * 1024)
                print(f"\r  {mb:.0f} MB decompressed", end="")

    print(f"\r  Done: {len(result)/(1024*1024):.1f} MB")
    return bytes(result)


def main():
    if len(sys.argv) < 3:
        print("e01_pure.py info|extract <file> [output]")
        sys.exit(0)

    cmd, path = sys.argv[1], sys.argv[2]
    fsize = os.path.getsize(path)
    print(f"File: {path} ({fsize/(1024**2):.0f} MB)")

    if cmd == "info":
        data = stream_decompress(path)
        print(f"Decompressed: {len(data):,} bytes ({len(data)/(1024**2):.1f} MB)")
        if len(data) >= 512:
            if data[510:512] == b'\x55\xaa':
                print("MBR: YES")
                for i in range(4):
                    off = 446 + i * 16
                    e = data[off:off+16]
                    if e[4] != 0:
                        start = int.from_bytes(e[8:12], "little")
                        ssize = int.from_bytes(e[12:16], "little")
                        ptype = e[4]
                        desc = {0x07: "NTFS", 0x83: "Linux", 0x82: "Swap",
                                0x0B: "FAT32", 0x0E: "FAT16", 0xEE: "GPT"}
                        desc = desc.get(ptype, f"0x{ptype:02X}")
                        print(f"  Part{i}: {desc} start={start} size={ssize} ({ssize*512/(1024**2):.0f}MB)")
            if b"EFI PART" in data[:1024]:
                print("GPT: YES")
            print(f"First 64 bytes: {data[:64].hex()}")

    elif cmd == "extract":
        output = sys.argv[3]
        data = stream_decompress(path)
        with open(output, "wb") as f:
            f.write(data)
        print(f"Extracted: {output}")


if __name__ == "__main__":
    main()
