#!/usr/bin/env python3
"""
Excel Coordinate Encrypt/Decrypt — (x,y) 坐标加密工具
=====================================================
来源: 2026 FIC 初赛 Writeup (https://mei-you-qian.github.io/)
算法: encoded = (((x + 100) ^ 85) * 1000) + ((y + 100) ^ 85)

用法:
  python excel_crypt.py decrypt 123456789    # 解密单个值
  python excel_crypt.py encrypt 100 200      # 加密坐标
  python excel_crypt.py decrypt-file data.txt  # 批量解密文件
"""
import sys
import re


def encrypt(x: int, y: int) -> int:
    """将 (x, y) 坐标加密为单个整数"""
    return (((x + 100) ^ 85) * 1000) + ((y + 100) ^ 85)


def decrypt(encoded: int) -> tuple[int, int]:
    """将加密值解密回 (x, y) 坐标"""
    x = ((encoded // 1000) ^ 85) - 100
    y = ((encoded % 1000) ^ 85) - 100
    return x, y


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python excel_crypt.py decrypt <encoded_value>")
        print("  python excel_crypt.py encrypt <x> <y>")
        print("  python excel_crypt.py decrypt-file <file>")
        return

    cmd = sys.argv[1]

    if cmd == "encrypt" and len(sys.argv) >= 4:
        x, y = int(sys.argv[2]), int(sys.argv[3])
        result = encrypt(x, y)
        print(f"encrypt({x}, {y}) = {result}")

    elif cmd == "decrypt" and len(sys.argv) >= 3:
        encoded = int(sys.argv[2])
        x, y = decrypt(encoded)
        print(f"decrypt({encoded}) = ({x}, {y})")

    elif cmd == "decrypt-file" and len(sys.argv) >= 3:
        with open(sys.argv[2]) as f:
            content = f.read()
        # 匹配所有整数（可能是加密值）
        numbers = re.findall(r'\d{6,}', content)
        print(f"Found {len(numbers)} potential encoded values:")
        for n in numbers:
            val = int(n)
            x, y = decrypt(val)
            print(f"  {val} → ({x}, {y})")

    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()
