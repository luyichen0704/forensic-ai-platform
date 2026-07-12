#!/usr/bin/env python3
"""
通用文件格式分析器 — 陌生文件格式识别
=====================================
来源: 文件结构与数据分析专项 (2025-12-17)
场景: pak/enc/自定义格式 → 自动识别结构、熵分析、提取可读片段

用法:
  python format_analyzer.py unknown.bin
  python format_analyzer.py -d ./mystery_files/
"""
import os
import re
import sys
import math
import struct
import argparse
from pathlib import Path
from collections import Counter
from datetime import datetime


class FormatAnalyzer:
    def __init__(self, filepath: Path):
        self.fp = filepath
        self.data = b""
        self.size = 0

    def load(self) -> bool:
        try:
            self.size = self.fp.stat().st_size
            # 只读前 50MB
            read_size = min(self.size, 50 * 1024 * 1024)
            with open(self.fp, "rb") as f:
                self.data = f.read(read_size)
            return True
        except Exception as e:
            print(f"读取错误: {e}")
            return False

    # ================================================================
    # 1. 魔数检测
    # ================================================================
    MAGIC_SIGNATURES = {
        b"\x89PNG\r\n\x1a\n": "PNG 图片",
        b"\xff\xd8\xff": "JPEG 图片",
        b"GIF8": "GIF 图片",
        b"BM": "BMP 图片",
        b"II*\x00": "TIFF 图片 (little-endian)",
        b"MM\x00*": "TIFF 图片 (big-endian)",
        b"PK\x03\x04": "ZIP/JAR/APK/DOCX/XLSX/PPTX 压缩包",
        b"PK\x05\x06": "ZIP (空归档)",
        b"PK\x07\x08": "ZIP (分卷)",
        b"Rar!\x1a\x07": "RAR 压缩包 (v4)",
        b"Rar!\x1a\x07\x01\x00": "RAR 压缩包 (v5)",
        b"7z\xbc\xaf'\x1c": "7-Zip 压缩包",
        b"\x1f\x8b\x08": "GZip 压缩",
        b"BZh": "BZip2 压缩",
        b"\xfd7zXZ\x00": "XZ 压缩",
        b"LZIP": "LZip 压缩",
        b"MZ": "PE/DOS 可执行文件",
        b"\x7fELF": "ELF 可执行文件",
        b"\xca\xfe\xba\xbe": "Mach-O 可执行文件 (64-bit)",
        b"\xce\xfa\xed\xfe": "Mach-O 可执行文件 (32-bit)",
        b"\xfe\xed\xfa\xce": "Mach-O 可执行文件 (32-bit BE)",
        b"%PDF": "PDF 文档",
        b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1": "OLE2 文档 (DOC/XLS/PPT/MSI)",
        b"SQLite format 3\x00": "SQLite 数据库",
        b"\x00\x01\x00\x00Standard Jet DB": "Access 数据库 (MDB)",
        b"EVF\x09\x0d\x0a\xff\x00": "E01 取证镜像",
        b"EVF2\x0d\x0a\x81\x00": "Ex01 取证镜像",
        b"KDMV": "VMware 虚拟磁盘",
        b"VMDK": "VMware VMDK",
        b"qemu": "QEMU 虚拟磁盘 (qcow)",
        b"\xeb\x3c\x90": "FAT 引导扇区",
        b"\xeb\x52\x90NTFS    ": "NTFS 分区",
        b"\x4c\x49\x4e\x55\x58\x20\x46\x49\x4c\x45": "ext3/4 文件系统",
        b"\x00\x00\x00\x0c\x6a\x50\x20\x20\x0d\x0a": "JPEG 2000",
        b"\x1a\x45\xdf\xa3": "WebM/MKV",
        b"ftyp": "MP4/ISO Base Media",
        b"RIFF": "AVI/WAV/WebP",
        b"\x00\x00\x01\xba": "MPEG PS",
        b"\x00\x00\x01\xb3": "MPEG 视频",
        b"ID3": "MP3 (ID3 tag)",
        b"\xff\xfb": "MP3 (MPEG frame)",
        b"OggS": "OGG 音频/视频",
        b"fLaC": "FLAC 无损音频",
        b"\x2e\x73\x6e\x64": "AU 音频",
        b"gimp xcf": "GIMP 图像",
        b"<?xml": "XML 文档",
        b"<!DOCTYPE html": "HTML 文档",
        b"#!": "脚本文件 (Shebang)",
        b"\x1b\x4c\x75\x61": "Lua 字节码",
        b"\x4e\x45\x53\x1a": "NES ROM",
        b"\x80\x02\xec\x10": "GameMaker 数据",
        b"PAK": "PAK 游戏资源包",
        b"\xac\xed\x00\x05": "Java 序列化对象",
        b"\x50\x41\x52\x32": "Parquet 文件",
        b"\x4f\x62\x6a\x01": "Avro 对象容器",
    }

    def detect_magic(self) -> list[str]:
        """检测文件头魔数"""
        matches = []
        for magic, desc in self.MAGIC_SIGNATURES.items():
            if self.data[: len(magic)] == magic:
                matches.append(desc)

        # 额外检测: 纯文本
        if not matches:
            try:
                text = self.data[:4096].decode("utf-8")
                printable_ratio = sum(1 for c in text if c.isprintable() or c in "\n\r\t") / len(text)
                if printable_ratio > 0.95:
                    matches.append("纯文本 (UTF-8)")
            except Exception:
                pass

        # 额外检测: Base64
        if not matches and len(self.data) > 4:
            base64_pattern = re.compile(rb"^[A-Za-z0-9+/]+={0,2}$")
            sample = self.data[:100].replace(b"\n", b"").replace(b"\r", b"").strip()
            if base64_pattern.match(sample):
                matches.append("Base64 编码文本")

        # 额外检测: Hex 文本
        if not matches:
            hex_pattern = re.compile(rb"^[0-9a-fA-F\s]+$")
            sample = self.data[:100].replace(b"\n", b"").replace(b"\r", b"").strip()
            if hex_pattern.match(sample):
                matches.append("十六进制文本")

        return matches

    # ================================================================
    # 2. 熵分析
    # ================================================================
    def entropy_analysis(self) -> dict:
        """计算文件熵值 — 高熵=加密/压缩, 低熵=明文"""
        if not self.data:
            return {"entropy": 0, "interpretation": "空文件"}

        # 字节频率
        byte_counts = Counter(self.data)
        total = len(self.data)

        entropy = 0.0
        for count in byte_counts.values():
            p = count / total
            entropy -= p * math.log2(p)

        # 分块熵
        chunk_size = 1024
        chunk_entropies = []
        for i in range(0, min(total, chunk_size * 20), chunk_size):
            chunk = self.data[i : i + chunk_size]
            cc = Counter(chunk)
            ce = 0.0
            for c in cc.values():
                p = c / len(chunk)
                ce -= p * math.log2(p)
            chunk_entropies.append(round(ce, 2))

        # 解释
        if entropy > 7.8:
            interp = "极高熵 → 很可能是加密/压缩数据"
        elif entropy > 7.0:
            interp = "高熵 → 可能是压缩/加密数据"
        elif entropy > 5.0:
            interp = "中等熵 → 可能混合了代码和数据"
        elif entropy > 3.0:
            interp = "低熵 → 可读文本/代码"
        else:
            interp = "极低熵 → 重复数据/填充"

        return {
            "entropy": round(entropy, 2),
            "max_possible": 8.0,
            "interpretation": interp,
            "chunk_entropies": chunk_entropies[:10],
        }

    # ================================================================
    # 3. 结构模式检测
    # ================================================================
    def detect_structure(self) -> dict:
        """检测文件内部结构模式"""
        patterns = {}

        # 检测 4 字节对齐的"表格"结构（许多文件格式的特征）
        # 每隔固定间隔出现相同模式 → 可能是记录/条目
        record_size_candidates = self._detect_record_size()
        if record_size_candidates:
            patterns["record_sizes"] = record_size_candidates

        # 检测 0x00 和 0xFF 填充
        zeros_ratio = self.data[:10000].count(0) / min(len(self.data), 10000)
        ff_ratio = self.data[:10000].count(0xFF) / min(len(self.data), 10000)
        patterns["zeros_ratio"] = round(zeros_ratio, 2)
        patterns["0xFF_ratio"] = round(ff_ratio, 2)

        # 检测 ASCII 字符串密度
        ascii_count = sum(1 for b in self.data[:50000] if 0x20 <= b <= 0x7E)
        patterns["ascii_density"] = round(ascii_count / min(len(self.data), 50000), 2)

        return patterns

    def _detect_record_size(self) -> list[int]:
        """尝试检测固定记录大小"""
        candidates = []
        sample = self.data[:10000]

        for size in [4, 8, 16, 32, 64, 128, 256, 512, 1024]:
            if len(sample) < size * 3:
                continue
            # 检查每 size 字节的第一个字节是否相同
            first_bytes = [sample[i * size] for i in range(min(10, len(sample) // size))]
            if len(set(first_bytes)) <= 3 and len(first_bytes) >= 5:
                candidates.append(size)
        return candidates

    # ================================================================
    # 4. 可读字符串提取
    # ================================================================
    def extract_strings(self, min_len: int = 4) -> list[str]:
        """提取可打印字符串"""
        strings = []
        current = []

        for byte in self.data[:100000]:
            if 0x20 <= byte <= 0x7E:
                current.append(chr(byte))
            else:
                if len(current) >= min_len:
                    s = "".join(current)
                    strings.append(s)
                current = []

        if len(current) >= min_len:
            strings.append("".join(current))

        return strings

    # ================================================================
    # 5. 相近文件对比
    # ================================================================
    def diff_with_known_formats(self) -> dict:
        """与已知格式对比相似度"""
        # 简化的格式指纹
        fingerprints = {
            "PE 可执行文件": b"This program cannot be run in DOS mode",
            "ZIP 压缩包": b"PK\x03\x04",
            "GZip 压缩": b"\x1f\x8b\x08",
            "JPEG 图片": b"JFIF",
            "PNG 图片": b"IHDR",
            "PDF 文档": b"endobj",
            "SQLite 数据库": b"SQLite format 3",
            "RAR 压缩包": b"Rar!",
            "7z 压缩包": b"7z\xbc\xaf'\x1c",
        }

        results = {}
        for fmt_name, fingerprint in fingerprints.items():
            pos = self.data.find(fingerprint)
            if pos >= 0:
                results[fmt_name] = f"特征在偏移 0x{pos:x} 处"

        return results

    # ================================================================
    # 主报告
    # ================================================================
    def analyze(self):
        print(f"\n{'='*70}")
        print(f"文件格式分析器 — {self.fp.name}")
        print(f"{'='*70}")

        if not self.load():
            return

        # 基本信息
        print(f"\n--- 基本信息 ---")
        print(f"  文件大小: {self.size:,} bytes ({self.size/1024:.1f} KB / {self.size/(1024*1024):.1f} MB)")
        print(f"  文件扩展名: {self.fp.suffix or '(无)'}")

        # 魔数检测
        print(f"\n--- 魔数检测 ---")
        magic_matches = self.detect_magic()
        if magic_matches:
            for m in magic_matches:
                print(f"  ✅ {m}")
        else:
            print(f"  ❓ 未识别 → 可能是未知/自定义格式")

        # 相近格式
        diffs = self.diff_with_known_formats()
        if diffs:
            print(f"\n--- 与已知格式相似度 ---")
            for fmt, info in diffs.items():
                print(f"  🔍 {fmt}: {info}")

        # 熵分析
        entropy = self.entropy_analysis()
        print(f"\n--- 熵分析 ---")
        print(f"  熵值: {entropy['entropy']:.2f} / 8.0")
        print(f"  解读: {entropy['interpretation']}")
        print(f"  分块熵: {entropy['chunk_entropies'][:10]}")

        # 结构模式
        structure = self.detect_structure()
        print(f"\n--- 结构模式 ---")
        print(f"  0x00 比例: {structure['zeros_ratio']:.0%}")
        print(f"  0xFF 比例: {structure['0xFF_ratio']:.0%}")
        print(f"  可打印字符密度: {structure['ascii_density']:.0%}")
        if structure.get("record_sizes"):
            print(f"  可能的记录大小: {structure['record_sizes']}")

        # 可读字符串
        strings = self.extract_strings(6)
        if strings:
            print(f"\n--- 可读字符串 ({len(strings)} 个, 前 30 个) ---")
            # 过滤出有意义的字符串（至少包含一个字母）
            meaningful = [s for s in strings if any(c.isalpha() for c in s)]
            # 按长度排序，显示最可能包含信息的字符串
            meaningful.sort(key=len, reverse=True)
            for s in meaningful[:30]:
                display = s[:100] + ("..." if len(s) > 100 else "")
                print(f"  {display}")

            # 标记敏感字符串
            print(f"\n--- 敏感字符串检测 ---")
            sensitive_patterns = [
                (r"flag\{[^}]+\}", "CTF Flag"),
                (r"CTF\{[^}]+\}", "CTF Flag"),
                (r"https?://[^\s]+", "URL"),
                (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "Email"),
                (r"\b[A-Fa-f0-9]{32}\b", "MD5 哈希"),
                (r"\b[A-Fa-f0-9]{40}\b", "SHA1 哈希"),
                (r"\b[A-Fa-f0-9]{64}\b", "SHA256 哈希"),
            ]
            found_any = False
            for s in meaningful:
                for pattern, label in sensitive_patterns:
                    match = re.search(pattern, s)
                    if match:
                        print(f"  🔴 [{label}] {match.group()}")
                        found_any = True
            if not found_any:
                print(f"  (无明显敏感信息)")

        # 十六进制预览
        print(f"\n--- 十六进制预览 (前 256 字节) ---")
        for i in range(0, min(256, len(self.data)), 16):
            hex_str = " ".join(f"{b:02x}" for b in self.data[i : i + 16])
            ascii_str = "".join(chr(b) if 0x20 <= b <= 0x7E else "." for b in self.data[i : i + 16])
            print(f"  {i:08x}: {hex_str:<48s} |{ascii_str}|")

        # 建议
        print(f"\n--- 分析建议 ---")
        suggestions = []
        if not magic_matches:
            suggestions.append("1. 查看文件尾部是否追加了额外数据（binwalk）")
            suggestions.append("2. 尝试用已知格式的头修复（如添加 PNG header）")
            suggestions.append("3. 检查是否 XOR/ROT 加密（熵高 + 无魔数 → 可能是加密）")
        if entropy["entropy"] > 7.5:
            suggestions.append("4. 高熵 → 尝试 XOR 爆破或已知密钥解密")
        if structure["ascii_density"] > 0.5:
            suggestions.append("5. 大部分可打印 → 可能是文本/代码，查看 strings")
        if diffs:
            suggestions.append("6. 检测到已知格式特征 → 可能嵌入在其他格式中")

        for s in suggestions:
            print(f"  {s}")


def main():
    parser = argparse.ArgumentParser(description="通用文件格式分析器")
    parser.add_argument("files", nargs="+", help="要分析的文件")
    parser.add_argument("-d", "--dir", help="批量分析目录")
    args = parser.parse_args()

    files_to_analyze = []
    if args.dir:
        for ext in ["*"]:
            files_to_analyze.extend(Path(args.dir).glob(ext))
        files_to_analyze = [f for f in files_to_analyze if f.is_file()]
    if args.files:
        files_to_analyze.extend([Path(f) for f in args.files])

    for fp in files_to_analyze:
        if not fp.is_file():
            print(f"跳过: {fp} (不是文件)")
            continue
        try:
            analyzer = FormatAnalyzer(fp)
            analyzer.analyze()
        except Exception as e:
            print(f"分析错误: {fp} - {e}")


if __name__ == "__main__":
    main()
