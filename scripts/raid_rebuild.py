#!/usr/bin/env python3
"""
RAID 重建工具 — 从多个磁盘镜像重建 RAID 0/1/5
=============================================
CTF 取证中 RAID 阵列重建是高频难点。

用法:
  python raid_rebuild.py -d disk1.img disk2.img disk3.img --type raid5
  python raid_rebuild.py -d disk1.img disk2.img --type raid0  # RAID 0
  python raid_rebuild.py -d *.img --auto                      # 自动检测

支持的 RAID 类型:
  RAID 0  — 条带化, 无冗余
  RAID 1  — 镜像, 每块盘相同
  RAID 5  — 分布式奇偶校验, 可缺一块盘
"""
import os
import sys
import struct
import hashlib
import argparse
from pathlib import Path
from collections import Counter


class RAIDRebuilder:
    def __init__(self, disks: list[str], output: str = "rebuilt.img"):
        self.disk_paths = [Path(d) for d in disks]
        self.output = Path(output)
        self.disks = []
        self.num_disks = len(disks)

    def load_disks(self) -> bool:
        """加载所有磁盘到内存"""
        print(f"加载 {self.num_disks} 个磁盘镜像...")
        sizes = []
        for dp in self.disk_paths:
            if not dp.exists():
                print(f"错误: {dp} 不存在")
                return False
            size = dp.stat().st_size
            sizes.append(size)
            print(f"  {dp.name}: {size:,} bytes ({size/(1024*1024):.0f} MB)")

        # 检查大小一致性
        if len(set(sizes)) > 1:
            print(f"警告: 磁盘大小不一致 {[s/(1024*1024) for s in sizes]} MB")
            min_size = min(sizes)
            print(f"使用最小大小: {min_size/(1024*1024):.0f} MB")
        else:
            min_size = sizes[0]

        # 加载到内存
        self.disk_size = min_size
        for dp in self.disk_paths:
            with open(dp, "rb") as f:
                self.disks.append(f.read(min_size))
        return True

    # ================================================================
    # 自动检测
    # ================================================================
    def auto_detect(self) -> dict:
        """自动检测 RAID 类型和参数"""
        result = {"type": "unknown", "stripe_size": 0, "parity_position": "left-symmetric"}

        # 1. 检测 RAID 1 (镜像)
        if self.num_disks >= 2:
            same_count = sum(1 for i in range(min(len(d) for d in self.disks))
                           if self.disks[0][i] == self.disks[1][i])
            similarity = same_count / min(len(self.disks[0]), len(self.disks[1]))
            if similarity > 0.99:
                result["type"] = "raid1"
                result["stripe_size"] = self.disk_size
                print(f"检测到 RAID 1 (相似度 {similarity:.1%})")
                return result

        # 2. 检测 RAID 0/5 — 找 stripe size
        if self.num_disks >= 2:
            stripe = self._detect_stripe_size()
            if stripe:
                result["stripe_size"] = stripe

                # 判断 RAID 0 vs RAID 5
                # RAID 5: 其中之一是奇偶校验 (高熵)
                if self.num_disks >= 3:
                    entropies = [self._calc_entropy(d[:100000]) for d in self.disks]
                    max_entropy = max(entropies)
                    # 如果某块盘的熵显著高于其他 → 奇偶校验盘
                    if max_entropy > 7.5 and max_entropy - min(entropies) > 1.0:
                        result["type"] = "raid5"
                        result["parity_disk"] = entropies.index(max_entropy)
                        print(f"检测到 RAID 5 (stripe={stripe}, 校验盘=#{result['parity_disk']})")
                    else:
                        result["type"] = "raid5"
                        result["parity_position"] = "left-symmetric"
                        print(f"检测到 RAID 5 (stripe={stripe}, 左对称校验)")
                else:
                    result["type"] = "raid0"
                    print(f"检测到 RAID 0 (stripe={stripe})")
                return result

        print("无法自动检测 RAID 类型，请手动指定 --type")
        return result

    def _detect_stripe_size(self) -> int | None:
        """检测条带大小: 找重复模式"""
        # 常见条带大小: 4K, 8K, 16K, 32K, 64K, 128K, 256K, 512K, 1M
        candidates = [4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288, 1048576]

        best_score = 0
        best_stripe = None

        for stripe in candidates:
            if stripe > self.disk_size // 4:
                continue

            # 采样检查: 每个条带边界是否对齐
            score = 0
            samples = min(10, self.disk_size // stripe - 1)
            for i in range(samples):
                offset = i * stripe
                # 检查是否在条带边界出现文本/数据变化
                chunk = self.disks[0][offset:offset + min(256, stripe)]
                # 检查是否有结构化数据 (ASCII 或已知 magic)
                ascii_count = sum(1 for b in chunk if 0x20 <= b <= 0x7E)
                if 10 < ascii_count < 200:
                    score += 1

            if score > best_score:
                best_score = score
                best_stripe = stripe

        if best_stripe and best_score >= 3:
            return best_stripe
        return None

    def _calc_entropy(self, data: bytes) -> float:
        """计算字节熵"""
        counts = Counter(data)
        total = len(data)
        entropy = -sum((c / total) * (__import__('math').log2(c / total))
                      for c in counts.values())
        return entropy

    # ================================================================
    # RAID 0 重建
    # ================================================================
    def rebuild_raid0(self, stripe_size: int) -> bytes:
        """RAID 0: 数据按条带依次分布在各磁盘"""
        total_stripes = self.disk_size // stripe_size
        result = bytearray()

        for stripe_idx in range(total_stripes):
            disk_idx = stripe_idx % self.num_disks
            offset = (stripe_idx // self.num_disks) * stripe_size
            if offset + stripe_size <= len(self.disks[disk_idx]):
                result.extend(self.disks[disk_idx][offset:offset + stripe_size])

        return bytes(result)

    # ================================================================
    # RAID 1 重建
    # ================================================================
    def rebuild_raid1(self) -> bytes:
        """RAID 1: 任取一块盘即可"""
        return self.disks[0]

    # ================================================================
    # RAID 5 重建 (左对称)
    # ================================================================
    def rebuild_raid5_left_symmetric(self, stripe_size: int) -> bytes:
        """RAID 5 左对称: 校验块从最后一个磁盘开始向左旋转"""
        result = bytearray()
        data_disks = self.num_disks - 1
        total_stripes = self.disk_size // stripe_size

        for stripe_idx in range(total_stripes):
            # 校验块位置: (self.num_disks - 1) - (stripe_idx % self.num_disks)
            parity_pos = (self.num_disks - 1) - (stripe_idx % self.num_disks)
            offset = (stripe_idx // data_disks) * stripe_size

            for disk_idx in range(self.num_disks):
                if disk_idx == parity_pos:
                    continue  # 跳过校验块
                if offset + stripe_size <= len(self.disks[disk_idx]):
                    result.extend(self.disks[disk_idx][offset:offset + stripe_size])

        return bytes(result)

    # ================================================================
    # RAID 5 重建 (缺一块盘 — 用奇偶校验恢复)
    # ================================================================
    def rebuild_raid5_missing_disk(self, stripe_size: int, missing_idx: int) -> bytes:
        """RAID 5 缺盘重建: 用其他盘 + 校验盘 XOR 恢复"""
        result = bytearray()
        data_disks = self.num_disks  # 含校验盘，但缺一块
        total_stripes = self.disk_size // stripe_size

        for stripe_idx in range(total_stripes):
            parity_pos = (self.num_disks - 1) - (stripe_idx % self.num_disks)
            offset = (stripe_idx // data_disks) * stripe_size

            for disk_idx in range(self.num_disks):
                if disk_idx == missing_idx:
                    # 用 XOR 恢复缺失盘的数据
                    recovered = bytearray(stripe_size)
                    for other_idx in range(self.num_disks):
                        if other_idx != missing_idx and other_idx != parity_pos:
                            if offset + stripe_size <= len(self.disks[other_idx]):
                                chunk = self.disks[other_idx][offset:offset + stripe_size]
                                for j in range(min(len(chunk), stripe_size)):
                                    recovered[j] ^= chunk[j]
                    # XOR 校验盘
                    if offset + stripe_size <= len(self.disks[parity_pos]):
                        parity_chunk = self.disks[parity_pos][offset:offset + stripe_size]
                        for j in range(min(len(parity_chunk), stripe_size)):
                            recovered[j] ^= parity_chunk[j]
                    result.extend(recovered[:stripe_size])
                elif disk_idx == parity_pos:
                    continue
                else:
                    if offset + stripe_size <= len(self.disks[disk_idx]):
                        result.extend(self.disks[disk_idx][offset:offset + stripe_size])

        return bytes(result)

    # ================================================================
    # 主流程
    # ================================================================
    def run(self, raid_type: str = "auto", stripe_size: int = 65536, missing: int = -1):
        if not self.load_disks():
            return None

        # 自动检测
        if raid_type == "auto":
            info = self.auto_detect()
            raid_type = info.get("type", "raid0")
            if info.get("stripe_size"):
                stripe_size = info["stripe_size"]
            if info.get("parity_position"):
                parity_pos = info["parity_position"]
            print(f"使用: type={raid_type}, stripe={stripe_size}")

        # 重建
        print(f"\n重建 {raid_type.upper()} (stripe={stripe_size})...")

        if raid_type == "raid0":
            result = self.rebuild_raid0(stripe_size)
        elif raid_type == "raid1":
            result = self.rebuild_raid1()
        elif raid_type == "raid5":
            if missing >= 0:
                print(f"  缺盘模式: disk #{missing}")
                result = self.rebuild_raid5_missing_disk(stripe_size, missing)
            else:
                result = self.rebuild_raid5_left_symmetric(stripe_size)
        else:
            print(f"不支持的 RAID 类型: {raid_type}")
            return None

        # 保存
        self.output.write_bytes(result)
        print(f"\n重建完成: {self.output} ({len(result):,} bytes)")

        # 快速验证
        self._verify(result)

        return result

    def _verify(self, data: bytes):
        """验证重建结果"""
        print(f"\n验证:")
        # 检查文件系统签名
        signatures = {
            b"\xeb\x52\x90NTFS    ": "NTFS",
            b"\xeb\x3c\x90": "FAT",
            b"LVM2": "LVM",
            b"\x53\xEF": "ext3/ext4 (可能性)",
            b"\x7fELF": "ELF 可执行文件",
            b"PK\x03\x04": "ZIP 归档",
        }
        for magic, desc in signatures.items():
            if data[:len(magic)] == magic:
                print(f"  ✅ 文件头: {desc}")
                return

        # 检查 UEFI/GPT
        if b"EFI PART" in data[:1024]:
            print(f"  ✅ 文件头: GPT 分区表")
            return

        # MBR
        if data[510:512] == b"\x55\xaa":
            print(f"  ✅ MBR 签名 (0x55AA)")
            return

        print(f"  ⚠ 未识别文件系统签名 — 可能需要调整 stripe_size 或 RAID 类型")


def main():
    parser = argparse.ArgumentParser(description="RAID 重建工具 — 从磁盘镜像恢复 RAID 阵列")
    parser.add_argument("-d", "--disks", nargs="+", required=True, help="磁盘镜像文件")
    parser.add_argument("-t", "--type", default="auto",
                       choices=["auto", "raid0", "raid1", "raid5"],
                       help="RAID 类型 (默认: auto)")
    parser.add_argument("-s", "--stripe", type=int, default=65536,
                       help="条带大小 (默认: 65536 = 64K)")
    parser.add_argument("-m", "--missing", type=int, default=-1,
                       help="RAID 5 缺失盘索引 (0-based)")
    parser.add_argument("-o", "--output", default="rebuilt.img",
                       help="输出文件")
    args = parser.parse_args()

    rebuilder = RAIDRebuilder(args.disks, args.output)
    rebuilder.run(args.type, args.stripe, args.missing)


if __name__ == "__main__":
    main()
