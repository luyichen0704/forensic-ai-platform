#!/usr/bin/env python3
"""
RSA Fermat Factorization — 当 p 和 q 接近时快速分解 n
=====================================================
来源: 2026 FIC 初赛 Writeup (https://mei-you-qian.github.io/)
场景: RSA 题目中 p 和 q 生成过于接近，可用 Fermat 方法直接分解

用法:
  python rsa_fermat.py <n> <e> <c>
  python rsa_fermat.py -f public.pem -c flag.enc
"""
import sys
from math import isqrt


def fermat_factor(n: int) -> tuple[int, int] | None:
    """Fermat 分解法: 当 |p - q| 较小时快速分解 n"""
    a = isqrt(n) + 1
    max_iter = 1_000_000  # 安全上限

    for _ in range(max_iter):
        b2 = a * a - n
        b = isqrt(b2)
        if b * b == b2:
            p = a - b
            q = a + b
            return p, q
        a += 1

    return None


def rsa_decrypt(n: int, e: int, c: int) -> bytes:
    """使用已知 n, e, c 尝试 Fermat 分解并解密"""
    factors = fermat_factor(n)
    if factors is None:
        print("[-] Fermat factorization failed (p and q not close enough)")
        sys.exit(1)

    p, q = factors
    print(f"[+] p = {p}")
    print(f"[+] q = {q}")

    phi = (p - 1) * (q - 1)
    d = pow(e, -1, phi)
    m = pow(c, d, n)

    # 尝试转换为字节
    try:
        m_bytes = m.to_bytes((m.bit_length() + 7) // 8, "big")
        print(f"[+] decrypted ({len(m_bytes)} bytes): {m_bytes}")
        return m_bytes
    except Exception:
        print(f"[+] decrypted (int): {m}")
        return str(m).encode()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="RSA Fermat factorization and decryption")
    parser.add_argument("n", nargs="?", type=int, help="Modulus n")
    parser.add_argument("e", nargs="?", type=int, default=65537, help="Public exponent (default: 65537)")
    parser.add_argument("c", nargs="?", type=int, help="Ciphertext")
    parser.add_argument("-f", "--publickey", help="Public key PEM file")
    parser.add_argument("--cfile", help="Encrypted flag file")
    args = parser.parse_args()

    n, e, c = args.n, args.e, args.c

    # 从 PEM 文件读取
    if args.publickey:
        try:
            from Crypto.PublicKey import RSA
            with open(args.publickey) as f:
                key = RSA.import_key(f.read())
            n = key.n
            e = key.e
            print(f"[+] Loaded public key: n={n.bit_length()} bits, e={e}")
        except ImportError:
            print("[-] Need pycryptodome for PEM support: pip install pycryptodome")
            sys.exit(1)

    if n is None:
        print("[-] Need n (modulus) or public key file")
        sys.exit(1)

    # 从文件读取密文
    if args.cfile:
        with open(args.cfile, "rb") as f:
            c = int.from_bytes(f.read(), "big")
        print(f"[+] Loaded ciphertext ({c.bit_length()} bits)")

    if c is None:
        print("[*] No ciphertext provided — only factoring n")
        factors = fermat_factor(n)
        if factors:
            print(f"[+] p = {factors[0]}")
            print(f"[+] q = {factors[1]}")
        else:
            print("[-] Factorization failed")
        return

    rsa_decrypt(n, e, c)


if __name__ == "__main__":
    main()
