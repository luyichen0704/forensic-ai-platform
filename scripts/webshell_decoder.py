#!/usr/bin/env python3
"""
Webshell 流量解密器 — AES + Base64 + Gzip 多层解码
===================================================
来源: 小谢取证"电子数据取证之使用Trae进行流量包解析"
场景: webshell 通信流量通常经过多层编码 —
      AES 加密 → Base64 ×2 → Gzip 压缩 → URL 编码

用法:
  python webshell_decoder.py -d "URL_ENCODED_PAYLOAD" -k "mykey"
  python webshell_decoder.py -f payloads.txt -k "mykey"
  python webshell_decoder.py --auto pcap_file          # 自动从 pcap 提取并解密
"""
import re
import sys
import gzip
import base64
import struct
import argparse
import subprocess
from pathlib import Path
from urllib.parse import unquote
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


class WebshellDecoder:
    """webshell 流量多层解密器"""

    def __init__(self, key: str = "xc", key_length: int = 16):
        # AES-128-ECB: key 补齐到 16 字节
        self.key = key.encode().ljust(key_length, b"\x00")[:key_length]
        self.key_length = key_length

    # ================================================================
    # 层层解码
    # ================================================================
    def url_decode(self, data: str) -> str:
        """URL 解码"""
        return unquote(data)

    def base64_decode_multi(self, data: str, max_depth: int = 3) -> bytes:
        """多层 Base64 解码（递归直到不可解）"""
        result = data.encode() if isinstance(data, str) else data
        for _ in range(max_depth):
            try:
                # 尝试标准 Base64 解码
                decoded = base64.b64decode(result)
                # 检查结果是否仍然是 Base64
                try:
                    decoded.decode("ascii")
                    if all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in decoded.decode("ascii")):
                        result = decoded
                        continue
                except Exception:
                    pass
                return decoded
            except Exception:
                break
        return result

    def gunzip_decode(self, data: bytes) -> bytes:
        """Gzip 解压"""
        try:
            return gzip.decompress(data)
        except Exception:
            return data

    def aes_ecb_decrypt(self, data: bytes) -> bytes:
        """AES-128-ECB 解密"""
        try:
            cipher = AES.new(self.key, AES.MODE_ECB)
            decrypted = cipher.decrypt(data)
            return unpad(decrypted, AES.block_size)
        except Exception:
            return data

    def full_decode(self, payload: str) -> str:
        """完整解码链路: URL → Base64×2 → Gzip → AES"""
        steps = []
        current = payload
        steps.append(("原始", current[:80]))

        # Step 1: URL decode
        if "%" in current:
            current = self.url_decode(current)
            steps.append(("URL解码", current[:80]))

        # Step 2: Base64 decode (multi-layer)
        decoded = self.base64_decode_multi(current)
        steps.append(("Base64 (多层)", decoded[:80].hex() if decoded else ""))
        current = decoded

        # Step 3: Gzip decompress
        try:
            decompressed = self.gunzip_decode(current)
            if decompressed != current:
                steps.append(("Gzip解压", decompressed[:80].hex()))
                current = decompressed
        except Exception:
            pass

        # Step 4: AES decrypt
        try:
            decrypted = self.aes_ecb_decrypt(current)
            if decrypted != current:
                steps.append(("AES解密", decrypted.decode("utf-8", errors="replace")[:200]))
                current = decrypted.decode("utf-8", errors="replace")
        except Exception:
            pass

        # 打印步骤
        for step_name, value in steps:
            print(f"  [{step_name}] {value}")

        return current if isinstance(current, str) else current.decode("utf-8", errors="replace")

    # ================================================================
    # 从 PCAP 自动提取 webshell payload
    # ================================================================
    def extract_from_pcap(self, pcap_path: str, filter_expr: str = "http") -> list[str]:
        """从 PCAP 中提取 webshell 通信 payload"""
        payloads = []

        # 使用 tshark 提取 HTTP 请求中的 mypass/password/cmd 参数
        if not Path(pcap_path).exists():
            print(f"PCAP 文件不存在: {pcap_path}")
            return payloads

        # 提取 HTTP POST 请求体
        try:
            result = subprocess.run(
                ["tshark", "-r", pcap_path, "-Y", "http.request.method == POST",
                 "-T", "fields", "-e", "urlencoded-form.key", "-e", "urlencoded-form.value"],
                capture_output=True, text=True, timeout=30
            )
            if result.stdout:
                for line in result.stdout.strip().split("\n"):
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        key, value = parts[0], parts[1]
                        if any(kw in key.lower() for kw in ["pass", "cmd", "key", "code", "mypass"]):
                            payloads.append(value)
        except Exception:
            pass

        # 提取 HTTP 请求中的 URL 参数
        try:
            result = subprocess.run(
                ["tshark", "-r", pcap_path, "-Y", "http.request.uri",
                 "-T", "fields", "-e", "http.request.uri"],
                capture_output=True, text=True, timeout=30
            )
            if result.stdout:
                for line in result.stdout.strip().split("\n"):
                    if "pass=" in line or "cmd=" in line or "key=" in line:
                        payloads.append(line)
        except Exception:
            pass

        return payloads

    def analyze_pcap(self, pcap_path: str):
        """自动化 pcap webshell 分析"""
        print(f"分析 PCAP: {pcap_path}")
        print("=" * 60)

        payloads = self.extract_from_pcap(pcap_path)

        if not payloads:
            print("未找到 webshell 相关 payload，尝试手动参数:")
            return

        print(f"找到 {len(payloads)} 个可疑 payload\n")

        for i, payload in enumerate(payloads[:10]):  # 最多分析 10 个
            print(f"\n--- Payload #{i+1} ---")
            print(f"原始: {payload[:100]}...")
            try:
                decoded = self.full_decode(payload)
                print(f"解密结果: {decoded[:500]}")
            except Exception as e:
                print(f"解密失败: {e}")


# ================================================================
# 多种 webshell 类型的解码模板
# ================================================================
WEBSHELL_TEMPLATES = {
    "php_xor_base64": {
        "description": "PHP XOR + Base64 (冰蝎/Behinder 类)",
        "key": "e45e329feb5d925b",  # 冰蝎默认 16 字节密钥
        "chain": ["url_decode", "base64_decode", "xor_decrypt"],
    },
    "php_aes_base64_gzip": {
        "description": "PHP AES + Base64 + Gzip (哥斯拉/Godzilla 类)",
        "key": "3c6e0b8a9c15224a",  # 哥斯拉默认密钥
        "chain": ["url_decode", "base64_decode", "gunzip", "aes_decrypt"],
    },
    "jsp_aes_base64": {
        "description": "JSP AES + Base64",
        "key": "xc",
        "chain": ["url_decode", "base64_decode", "aes_decrypt"],
    },
}

def identify_webshell_type(payloads: list[str]) -> str:
    """尝试自动识别 webshell 类型"""
    for name, tmpl in WEBSHELL_TEMPLATES.items():
        # 简单启发式检测
        combined = " ".join(payloads[:3])
        if "pass=" in combined and "%" in combined:
            return name
    return "php_aes_base64_gzip"  # 默认


def main():
    parser = argparse.ArgumentParser(
        description="Webshell 流量解密器 — AES/Base64/Gzip/URL 多层解码"
    )
    parser.add_argument("-d", "--data", help="单个 payload 字符串")
    parser.add_argument("-f", "--file", help="包含 payload 的文件 (每行一个)")
    parser.add_argument("-k", "--key", default="xc", help="AES 密钥 (默认: xc)")
    parser.add_argument("--auto", help="自动分析 PCAP 文件")
    parser.add_argument("--template", choices=list(WEBSHELL_TEMPLATES.keys()),
                       help="使用预设 webshell 模板")
    args = parser.parse_args()

    key = args.key
    if args.template:
        tmpl = WEBSHELL_TEMPLATES[args.template]
        key = tmpl["key"]
        print(f"使用模板: {args.template} → {tmpl['description']}")
        print(f"密钥: {key}")

    decoder = WebshellDecoder(key=key)

    # 自动分析 pcap
    if args.auto:
        decoder.analyze_pcap(args.auto)
        return

    # 单条解密
    if args.data:
        print(f"密钥: {key}")
        print(f"输入: {args.data[:100]}...")
        decoder.full_decode(args.data)
        return

    # 批量文件解密
    if args.file:
        with open(args.file) as f:
            payloads = [line.strip() for line in f if line.strip()]
        print(f"加载 {len(payloads)} 条 payload")
        for i, payload in enumerate(payloads):
            print(f"\n--- #{i+1} ---")
            decoder.full_decode(payload)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
