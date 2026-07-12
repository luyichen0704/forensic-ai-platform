# Cryptography Skill — CTF

## 适用场景
古典密码、现代密码、编码/解码、哈希破解、RSA/ECC 攻击、侧信道攻击。

## 工具清单

| 工具 | 用途 | 路径 |
|------|------|------|
| `openssl` | SSL/TLS/RSA/证书操作 | `E:\CompetitionTools\scoop\apps\openssl\current\bin\openssl.exe` |
| `hashcat` | GPU 哈希破解 | `E:\CompetitionTools\scoop\shims\hashcat.cmd` |
| `python` | 编码解码脚本 | Python313 |
| `xxd` | 十六进制转换 | git-bash |
| `strings` | 字符串提取 | git-bash |
| `rg` | 内容搜索 | scooped |
| `yq` / `jq` | JSON/YAML 处理 | scooped |
| `rsa_fermat.py` | RSA Fermat 分解脚本 | `E:\CompetitionTools\scripts\rsa_fermat.py` |

## 分析流程

### 第一步：识别编码/密码类型

| 模式 | 识别特征 | 解码工具 |
|------|----------|----------|
| Base64 | `[A-Za-z0-9+/=]+` | `base64 -d` / `echo xx \| openssl base64 -d` |
| Base32 | `[A-Z2-7=]+` | `base32 -d` |
| Hex | `[0-9a-fA-F]+` | `xxd -r -p` / Python `bytes.fromhex()` |
| Base58 | `[1-9A-HJ-NP-Za-km-z]+` (no 0OIl) | Python `base58` |
| Base85 | 含特殊字符的短编码 | Python `base64.a85decode()` |
| URL 编码 | `%XX%XX` | Python `urllib.parse.unquote()` |
| Rot13/Caesar | 字母移位 | `tr 'A-Za-z' 'N-ZA-Mn-za-m'` |
| Morse | `.-` 组合 | 在线 / Python |
| XOR | 未知密钥异或 | 频率分析 |
| RSA | `n=, e=, c=` 或 `.pem` | `openssl rsa` / RsaCtfTool |

### 第二步：常用编解码 Bash

```bash
# Base64
echo "SGVsbG8=" | openssl base64 -d
echo "Hello" | openssl base64

# 多层 Base64
cat encoded.txt | base64 -d | base64 -d | base64 -d

# Hex
echo "48656c6c6f" | xxd -r -p
echo -n "Hello" | xxd -p

# Rot13
echo "Uryyb" | tr 'A-Za-z' 'N-ZA-Mn-za-m'

# URL 解码
python3 -c "import urllib.parse; print(urllib.parse.unquote('%48%65%6c%6c%6f'))"

# XOR (已知单字节 key)
python3 -c "
data = bytes.fromhex('...')
key = 0x42
print(bytes([b ^ key for b in data]))
"
```

### 第三步：古典密码

```bash
# Caesar 爆破（所有移位）
python3 -c "
import string
ct = 'khoor'
for shift in range(1, 26):
    pt = ''.join(chr((ord(c) - 97 - shift) % 26 + 97) if c.isalpha() else c for c in ct.lower())
    print(f'{shift:2}: {pt}')
"

# Vigenère — 需要猜密钥
# 使用在线工具或 Python 库

# 替换密码 — 频率分析
python3 -c "
from collections import Counter
ct = '...'
freq = Counter(ct.replace(' ', ''))
print(freq.most_common())
# 英文常见: E T A O I N S H R → 对照替换
"
```

### 第四步：哈希破解

```bash
# 识别哈希类型
# MD5:    32 hex → hashcat mode 0
# SHA1:   40 hex → hashcat mode 100
# SHA256: 64 hex → hashcat mode 1400
# SHA512: 128 hex → hashcat mode 1700
# NTLM:   32 hex → hashcat mode 1000
# bcrypt: $2a$... → hashcat mode 3200

# hashcat 字典攻击
hashcat -m 0 -a 0 hash.txt wordlist.txt

# hashcat 规则攻击
hashcat -m 0 -a 0 hash.txt wordlist.txt -r rules/best64.rule

# hashcat 掩码攻击（已知部分密码格式: flag{???}）
hashcat -m 0 -a 3 hash.txt "flag{?l?l?l?l?l}"

# openssl 验证
echo -n "password" | openssl md5
echo -n "password" | openssl sha256
```

### 第五步：RSA 攻击

```bash
# 从 PEM 提取参数
openssl rsa -pubin -in public.pem -text -noout
openssl rsa -in private.pem -text -noout

# 已知 p, q, e 计算私钥
python3 -c "
from Crypto.Util.number import inverse, long_to_bytes
p = ...
q = ...
e = 65537
c = ...
n = p * q
phi = (p-1) * (q-1)
d = inverse(e, phi)
m = pow(c, d, n)
print(long_to_bytes(m))
"

# 小 e 攻击 (e=3)
python3 -c "
from gmpy2 import iroot
c = ...
e = 3
m, exact = iroot(c, e)
print(bytes.fromhex(hex(m)[2:]))
"

# 共模攻击 (Same n, different e)
# Wiener 攻击 (d 很小)
# Fermat 分解 (p 和 q 很接近)
# 使用 RsaCtfTool: python RsaCtfTool.py --publickey public.pem --uncipherfile flag.enc
```

### 第六步：CTF 常见密码模式

```bash
# 文件即密钥
openssl enc -d -aes-256-cbc -in encrypted.bin -out decrypted.bin -pass file:key.txt

# 密钥在 EXIF 中
KEY=$(exiftool -Comment image.jpg | awk -F': ' '{print $2}')
openssl enc -d -aes-256-cbc -in flag.enc -out flag.txt -pass pass:"$KEY"

# XOR 文件
python3 -c "
with open('encrypted', 'rb') as f: data = f.read()
key = b'FLAG'
print(bytes([data[i] ^ key[i % len(key)] for i in range(len(data))]))
"
```

### 常用 Python 库速查
```python
import base64, binascii, hashlib, codecs
from Crypto.Util.number import long_to_bytes, bytes_to_long, inverse, GCD
from Crypto.Cipher import AES, DES, ARC4
import gmpy2
```

## 提示
- **Base64 末尾 `=` 是最明显标志**，但也可能有 Base64url (无 `=`)
- **多层编码很常见**：Hex → Base64 → Base32 → 原文
- **未知密文先用 CyberChef** (https://gchq.github.io/CyberChef/)
- **哈希破解先查在线彩虹表**：crackstation.net, hashes.com

---

## 实战技法: DIDCTF 取证密码破解

### ZIP 明文攻击 (Known Plaintext Attack)
```bash
# 场景: 压缩包内有一个已知内容的文件(如 readme.txt)
# 1. 准备明文文件, 内容与压缩包内完全一致
echo "This is the table to get the key" > readme.txt
# 2. 用 7z zip 格式压缩 (必须和原压缩包算法一致!)
7z a -tzip -mx0 plain.zip readme.txt     # -mx0 = 不压缩
# 3. CRC 校验一致后, 用 ARCHPR/AZPR 明文攻击
# 原理: CRC32 碰撞 → 推算出密钥 → 解密整个压缩包
```

### 捕获包中的密码提取
```bash
# 蚁剑流量中压缩命令: zip -P <password> xxx.zip
tshark -r capture.pcap -Y "http.request.uri contains zip" -T fields -e urlencoded-form.value
# 密码直接出现在命令参数中
```

### 比赛常见弱密码优先级
```bash
# 1. 比赛/平台名: DIDCTF, pgs, meiya, 盘古石
# 2. 默认密码: 123456, admin, password, pgs123456
# 3. 题目描述中的关键词
# 4. 同检材中其他文件的内容
# 5. 纯数字短密码 (4-6位, john快速爆破)

---

## 虚拟货币钱包取证 (2026平航杯)
```bash
# 浏览器扩展 → 钱包 → 助记词(12词) → 恢复钱包
# 助记词可能在: 输入法自定义短语 / 日记 / 便签
# 钱包地址格式: 0x + 40位hex
```

## 密码哈希分析
```bash
# 识别加密类型
$2a$10$... = bcrypt
$6$...     = SHA512 (hashcat -m 1800)
sha256($pass.$salt) = 常见自实现
# 盐值通常在同文件/代码中: "JinQin_Secret" / "Pr3d1ct0r"
```
