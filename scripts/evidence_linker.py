#!/usr/bin/env python3
"""
证据链关联器 — 多检材之间建立关联
================================
当有多个检材（手机、电脑、服务器）时，自动发现跨检材的关联

用法:
  python evidence_linker.py -e evidence1/ evidence2/ evidence3/
"""
import os
import re
import json
import hashlib
from pathlib import Path
from collections import defaultdict
import argparse


class EvidenceLinker:
    def __init__(self, evidence_dirs: list[str]):
        self.dirs = [Path(d) for d in evidence_dirs]
        self.links = []
        self.artifacts = defaultdict(list)  # artifact_type → [(dir, path, value)]

    def extract_email_addresses(self):
        """从所有检材提取邮箱地址 → 跨检材关联"""
        pattern = re.compile(rb"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
        for d in self.dirs:
            for root, _, files in os.walk(d):
                for fname in files:
                    fp = Path(root) / fname
                    try:
                        if fp.stat().st_size > 50 * 1024 * 1024:
                            continue
                        with open(fp, "rb") as f:
                            data = f.read(1024 * 1024)
                        emails = set(pattern.findall(data))
                        for email in emails:
                            self.artifacts["email"].append((d.name, str(fp.relative_to(d)), email.decode()))
                    except Exception:
                        pass

        # 跨检材相同邮箱 → 关联
        email_map = defaultdict(list)
        for dname, fpath, email in self.artifacts["email"]:
            email_map[email].append((dname, fpath))

        for email, sources in email_map.items():
            if len(set(s[0] for s in sources)) >= 2:  # 出现在 ≥2 个检材中
                self.links.append({
                    "type": "cross_evidence_email",
                    "email": email,
                    "sources": sources,
                })

    def extract_ip_addresses(self):
        """提取 IP 地址 → 网络关联"""
        pattern = re.compile(rb"\b(?:\d{1,3}\.){3}\d{1,3}\b")
        ip_map = defaultdict(list)
        for d in self.dirs:
            for root, _, files in os.walk(d):
                for fname in files:
                    fp = Path(root) / fname
                    try:
                        if fp.stat().st_size > 50 * 1024 * 1024:
                            continue
                        with open(fp, "rb") as f:
                            data = f.read(1024 * 1024)
                        ips = set(pattern.findall(data))
                        for ip in ips:
                            ip_str = ip.decode()
                            # 排除常见内部 IP
                            if not ip_str.startswith(("127.", "0.", "255.")):
                                ip_map[ip_str].append((d.name, str(fp.relative_to(d))))
                    except Exception:
                        pass

        for ip, sources in ip_map.items():
            if len(set(s[0] for s in sources)) >= 2:
                self.links.append({
                    "type": "cross_evidence_ip",
                    "ip": ip,
                    "sources": sources,
                })

    def extract_hash_correlations(self):
        """通过文件哈希关联 → 同一文件出现在不同检材"""
        hash_map = defaultdict(list)
        for d in self.dirs:
            for root, _, files in os.walk(d):
                for fname in files[:200]:  # 每检材最多 200 个文件
                    fp = Path(root) / fname
                    try:
                        if fp.stat().st_size > 100 * 1024 * 1024:
                            continue
                        with open(fp, "rb") as f:
                            h = hashlib.md5(f.read()).hexdigest()
                        hash_map[h].append((d.name, str(fp.relative_to(d)), fname))
                    except Exception:
                        pass

        for h, sources in hash_map.items():
            if len(set(s[0] for s in sources)) >= 2:
                self.links.append({
                    "type": "same_file_different_evidence",
                    "hash": h,
                    "filename": sources[0][2],
                    "sources": sources,
                })

    def link_encrypted_files_to_keys(self):
        """加密文件(.enc) → 密钥文件(.pem/.key) 关联"""
        enc_files = []
        key_files = []

        for d in self.dirs:
            for root, _, files in os.walk(d):
                for fname in files:
                    fp = Path(root) / fname
                    if fname.endswith(".enc"):
                        enc_files.append((d.name, str(fp.relative_to(d)), fp))
                    elif fname.endswith((".pem", ".key", "id_rsa", "id_ed25519")):
                        key_files.append((d.name, str(fp.relative_to(d)), fp))

        if enc_files and key_files:
            self.links.append({
                "type": "encrypted_file_key_pair",
                "encrypted": [(d, p) for d, p, _ in enc_files],
                "keys": [(d, p) for d, p, _ in key_files],
            })

    def run(self):
        print("证据链关联分析中...")
        self.extract_email_addresses()
        self.extract_ip_addresses()
        self.extract_hash_correlations()
        self.link_encrypted_files_to_keys()

        print(f"\n发现 {len(self.links)} 条证据链关联:\n")
        for i, link in enumerate(self.links, 1):
            print(f"{'='*60}")
            print(f"关联 #{i}: {link['type']}")
            print(f"{'='*60}")

            if link["type"] == "cross_evidence_email":
                print(f"  邮箱: {link['email']}")
                for src in link["sources"]:
                    print(f"    → {src[0]}/{src[1]}")
            elif link["type"] == "cross_evidence_ip":
                print(f"  IP: {link['ip']}")
                for src in link["sources"]:
                    print(f"    → {src[0]}/{src[1]}")
            elif link["type"] == "same_file_different_evidence":
                print(f"  文件: {link['filename']} (MD5: {link['hash'][:16]}...)")
                for src in link["sources"]:
                    print(f"    → {src[0]}/{src[1]}")
            elif link["type"] == "encrypted_file_key_pair":
                print(f"  加密文件 ({len(link['encrypted'])}):")
                for d, p in link["encrypted"][:5]:
                    print(f"    → {d}/{p}")
                print(f"  密钥文件 ({len(link['keys'])}):")
                for d, p in link["keys"][:5]:
                    print(f"    → {d}/{p}")
            print()

        return self.links


def main():
    parser = argparse.ArgumentParser(description="跨检材证据链关联分析")
    parser.add_argument("-e", "--evidence", nargs="+", required=True, help="检材目录列表")
    parser.add_argument("-o", "--output", help="输出 JSON 文件")
    args = parser.parse_args()

    linker = EvidenceLinker(args.evidence)
    links = linker.run()

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(links, f, ensure_ascii=False, indent=2, default=str)
        print(f"结果已保存: {args.output}")


if __name__ == "__main__":
    main()
