# Network Forensics Skill — CTF 流量分析完全指南

## 适用场景
PCAP/PCAPNG 流量分析、TLS 解密、协议分析、隐蔽信道检测、攻击溯源、恶意流量检测。

来源: ctf-skills (ljagiello) + 小谢取证 + 实战经验

## 工具清单

| 工具 | 用途 | 路径 |
|------|------|------|
| `tshark` | 命令行流量分析 | `E:\CompetitionTools\scoop\shims\tshark.exe` |
| `capinfos` | PCAP 文件信息 | `E:\CompetitionTools\scoop\shims\capinfos.exe` |
| `editcap` | PCAP 分割/过滤 | `E:\CompetitionTools\scoop\shims\editcap.exe` |
| `mergecap` | PCAP 合并 | `E:\CompetitionTools\scoop\shims\mergecap.exe` |
| `strings` | 字符串提取 | git-bash |
| `rg` | 内容搜索 | scooped |
| `openssl` | SSL/TLS/RSA 解密 | scooped |
| `hashcat` | NTLMv2/WPA 破解 | scooped |
| `python` | 自定义解码脚本 | Python313 |
| `webshell_decoder.py` | Webshell 流量解密 | `E:\CompetitionTools\scripts\webshell_decoder.py` |

## 🚀 快速开局三板斧

```bash
# 1. 概览
capinfos capture.pcap && tshark -r capture.pcap -q -z io,phs

# 2. Flag 搜索
strings capture.pcap | rg -i "flag|ctf|password|secret|key|token|\{.*\}"

# 3. HTTP 对象导出（最重要的一步！）
tshark -r capture.pcap --export-objects http,./http_objects/
ls -la ./http_objects/
# 80% 的流量题 flag 在这一步就能找到
```

---

## 专题 1: TLS/SSL 解密

### 方法 A: Keylog 文件
```bash
# 如果提供了 sslkeys.log
tshark -r capture.pcap \
  -o "tls.keylog_file:sslkeys.log" \
  -Y http
```
Keylog 格式: `CLIENT_RANDOM <32字节hex> <48字节hex>`

### 方法 B: RSA 私钥
```bash
# 仅 RSA 密钥交换有效（ECDHE 不行）
tshark -r capture.pcap \
  -o "tls.keys_list:192.168.1.1,443,http,server.key" \
  -Y http
```

### 方法 C: 弱 RSA 密钥分解
```bash
# 提取证书 → 分解 n → 生成私钥
tshark -r capture.pcap -Y "tls.handshake.type==11" \
  -T fields -e tls.handshake.certificate | head -1
# 用 rsa_fermat.py 分解:
python E:\CompetitionTools\scripts\rsa_fermat.py -f cert.pem
# 再用 rsatool 生成私钥
```

### 方法 D: Coredump 提取 Master Key
```bash
# 从 coredump/内存镜像中搜索 Session ID → 读取前 48 字节 master_key
# 格式: RSA Session-ID:<hex> Master-Key:<hex>
```

---

## 专题 2: 隐蔽信道检测速查表

| 信道类型 | 检测特征 | 提取方法 |
|----------|----------|----------|
| **ICMP 长度** | ping -s 长度值在 32-126 范围 | `tshark -T fields -e icmp.data_len` |
| **ICMP 时间** | reply 延迟呈双峰分布 | 计算 RTT 时间差 → 阈值分 0/1 |
| **ICMP 字节旋转** | 载荷非零但无意义 | `bytes((b - SHIFT) % 256)` |
| **TCP Flags** | 异常 Flag 组合 (FIN+SYN) | 6-bit flag → base64 查表 |
| **DNS 尾字节** | 大量相同域名查询 | 提取每个查询最后一个字符 |
| **DNS 隧道 (dnscat2)** | 长 subdomain + hex 编码 | 去 9 字节头 → base32/hex 解码 |
| **DNS 二进制 Oracle** | NOERROR/NXDOMAIN 二元响应 | 逐 bit 试探 → 组装 flag |
| **HTTP 上传隐写** | POST 到 /upload | `--export-objects http` → 检查导出文件 |
| **BCD 编码 (UDP)** | 挑战名提示编码比例 | 每字节 2 位 BCD 数字 |
| **分片归档重组** | 多个等大小 HTTP 传输 | 按目录列表时间戳排序 → 拼接 |

### ICMP 长度隐蔽信道
```python
# 最简单: payload 长度 = ASCII 字符
from scapy.all import rdpcap, ICMP
pkts = rdpcap('capture.pcap')
flag = ''.join(
    chr(len(p[ICMP].payload))
    for p in pkts if ICMP in p and p[ICMP].type == 8
)
print(flag)
```

### TCP Flags 隐蔽信道
```python
# 6 个 Flag 位 = 0-63 → base64 查表
b64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
encoded = ''.join(b64[p[TCP].flags & 0x3F] for p in suspicious_packets)
flag = base64.b64decode(encoded)
```

### 时间间隔隐蔽信道
```python
# 两个不同间隔 = 二进制的 0 和 1
times = [float(p.time) for p in pkts]
intervals = [times[i+1] - times[i] for i in range(len(times)-1)]
threshold = 0.05  # 50ms 分界线
bits = [0 if dt < threshold else 1 for dt in intervals]
flag = bytes(int(''.join(str(b) for b in bits[i:i+8]), 2)
             for i in range(0, len(bits)-7, 8)).decode()
```

### DNS 尾字节隐写
```python
# 每个 DNS 查询的最后一个字符组成 FLAG
from scapy.all import rdpcap, DNSQR
data = []
for pkt in rdpcap('capture.pcap'):
    if pkt.haslayer(DNSQR):
        qname = pkt[DNSQR].qname.decode().rstrip('.')
        if qname: data.append(qname[-1])
print(''.join(data))
```

---

## 专题 3: 认证凭据提取

### HTTP Basic/Digest
```bash
tshark -r capture.pcap -Y "http.authorization" -T fields -e http.authorization
```

### FTP
```bash
tshark -r capture.pcap -Y "ftp.request.command==USER || ftp.request.command==PASS" \
  -T fields -e ftp.request.command -e ftp.request.arg
```

### NTLMv2 Hash 提取 + 破解
```bash
# 提取 NTLMv2 认证数据
tshark -r capture.pcap -Y "ntlmssp.messagetype==0x00000003" \
  -T fields -e ntlmssp.ntlmv2_response.ntproofstr \
  -e ntlmssp.auth.username -e ntlmssp.auth.domain

# 破解
hashcat -m 5600 ntlmv2_hash.txt wordlist.txt
```

### Kerberos / Timeroasting (MS-SNTP)
```bash
# NTP 请求中包含 RID → 响应 HMAC-MD5 → hashcat -m 31300
```

### RADIUS 破解
```bash
# 提取 → radius2john → john → 解密密码字段
```

### SMTP/IMAP/POP3
```bash
tshark -r capture.pcap -Y "smtp || imap || pop" -T fields \
  -e smtp.req.command -e smtp.req.parameter
```

### WordPress / CMS 凭据
```bash
# 搜索 wp-config.php / .env 等配置文件
tshark -r capture.pcap -q -z "follow,tcp,ascii,N" | rg -i "DB_PASSWORD|password"
```

---

## 专题 4: Webshell 流量分析

来源: 小谢取证流量分析文章

### 特征识别
```
- HTTP PUT 方法上传文件 (少见!)
- POST 到 .jsp / .php 但返回 200
- URL 参数: pass= / cmd= / key= / mypass=
- Content-Type: application/octet-stream (非表单)
- 周期性心跳包
```

### 常见编码链
```
冰蝎 (Behinder):   URL → Base64 → XOR
哥斯拉 (Godzilla):  URL → Base64×2 → Gzip → AES-ECB
蚁剑 (AntSword):    URL → Base64 → 明文命令
```

### 解密模板
```bash
# 冰蝎类: XOR + Base64
python E:\CompetitionTools\scripts\webshell_decoder.py -d "PAYLOAD" -k "e45e329feb5d925b" --template php_xor_base64

# 哥斯拉类: AES + Base64 + Gzip
python E:\CompetitionTools\scripts\webshell_decoder.py -d "PAYLOAD" -k "3c6e0b8a9c15224a" --template php_aes_base64_gzip

# 自定义: AES + Base64
python E:\CompetitionTools\scripts\webshell_decoder.py -d "PAYLOAD" -k "xc"
```

### PCAP 自动化提取
```bash
# 从 pcap 提取 webshell payload 并自动解密
python E:\CompetitionTools\scripts\webshell_decoder.py --auto capture.pcap
```

---

## 专题 5: PCAP 修复

```bash
# pcapfix 自动修复
pcapfix -d corrupted.pcap    # → fixed_corrupted.pcap

# 手动修复头部 (magic bytes)
python3 -c "
import struct
with open('broken.pcap','rb') as f: data = bytearray(f.read())
data[0:4] = struct.pack('<I', 0xa1b2c3d4)  # magic
data[4:6] = struct.pack('<H', 2)           # major version
data[6:8] = struct.pack('<H', 4)           # minor version
with open('fixed.pcap','wb') as f: f.write(data)
"
```

---

## 专题 6: WPA/WEP WiFi 解密

```bash
aircrack-ng capture.pcapng                      # 识别加密
aircrack-ng -a 1 capture.pcapng                 # WEP PTW 攻击
aircrack-ng -a 2 -w rockyou.txt capture.pcapng  # WPA 字典
airdecap-ng -p "passphrase" -e "SSID" capture.pcapng  # 解密
```

---

## 专题 7: SMB3 加密流量

```bash
# 1. 提取 NTLMv2 hash
tshark -r capture.pcap -Y "ntlmssp.messagetype==0x00000003" -T fields \
  -e ntlmssp.ntlmv2_response.ntproofstr -e ntlmssp.auth.username

# 2. 破解 → 推导 Session Key → AES-128-GCM 解密 SMB3 载荷
```

---

## 专题 8: 多层 PCAP / 分片重组

```bash
# 检测: 多个等大小 HTTP 传输 → 可能是分片归档
# 1. 导出所有对象
tshark -r capture.pcap --export-objects http,./parts/

# 2. 检查第一个文件 magic bytes (7z/ZIP header)
xxd ./parts/第一个文件 | head -1

# 3. 从目录列表获取时间戳 → 排序 → 拼接
cat part1 part2 part3 ... > archive.7z

# 4. 从聊天流提取密码
tshark -r capture.pcap -q -z "follow,tcp,ascii,N"
```

---

## 专题 9: 常见攻击模式速查

| 攻击阶段 | 流量特征 | 提取方法 |
|----------|----------|----------|
| 端口扫描 | 大量 SYN → 不同端口 | `tshark -q -z conv,tcp` |
| 目录爆破 | 大量 404 + 规律 URI | `tshark -Y "http.response.code==404"` |
| SQL 注入 | UNION/SLEEP/BENCHMARK 在 URL | `strings pcap \| rg "UNION\|SLEEP\|BENCHMARK"` |
| 文件上传 | POST multipart/form-data | `--export-objects http` |
| 反弹 Shell | `/bin/sh -i` / `bash -i` / `nc -e` | TCP stream follow |
| 横向移动 | SMB/RDP/WMI 流量到多台机器 | `tshark -q -z endpoints,ip` |
| C2 通信 | 周期性 Beacon (固定间隔) | 时间间隔分析 |
| DNS 隧道 | 超长 subdomain + 高频查询 | `tshark -Y "dns.qry.name matches \".{52,}\""` |
| 数据外传 | POST 大量数据 / DNS TXT 大包 | 包大小统计 |

---

## 专题 10: 高级隐蔽信道 (ctf-skills 2025-2026 真题)

### Brotli 解压炸弹缝分析
```python
# 极高压缩比的 Br 文件 → 找重复块 → 异常处 = flag
import brotli
with open('flag.txt.br', 'rb') as f: data = f.read()
# 检测 105 字节重复周期 → 断层处解压
```

### XOR + ZIP 多层 PCAP
```
TCP stream 标记为 TLS → 实际含 PK header → 提取 ZIP
→ mDNS TXT 记录有 XOR key → 解密 → 两个数据集按可打印性合并
```

### dnscat2 重组
```python
# 提取 DNS 查询 subdomain → hex 解码 → 去 9 字节头 → 去重 → 拼接
```

---

## 常用 Filter 速查表

```
# HTTP
http.request.method == "POST"
http.response.code == 200
http contains "flag"

# DNS
dns.qry.name contains "evil"
dns.flags.rcode == 0          # NOERROR
dns.flags.rcode == 3          # NXDOMAIN

# TCP
tcp.port == 4444
tcp.flags.syn == 1 && tcp.flags.ack == 0
tcp.stream eq 5

# TLS
tls.handshake.type == 1       # Client Hello
tls.handshake.type == 11      # Certificate
tls.handshake.certificate

# 认证
ntlmssp.messagetype == 0x00000003   # NTLM Auth
kerberos.msg_type == 10             # AS-REQ
http.authorization

# 文件传输
data.data contains "PK"       # ZIP header
ftp-data
smb2.cmd == 5                 # SMB Read
http.content_type contains "application/zip"

# 异常
tcp.flags == 0x29             # Xmas scan
tcp.flags == 0x00             # NULL scan
icmp.type == 8                # Echo Request (隐蔽信道常见)
frame contains "eval("        # Webshell
```

## 快速检查清单

```
□ capinfos → 文件大小/包数/时长
□ strings | rg flag → 30秒快速扫
□ --export-objects http → HTTP 文件提取（最优先!）
□ tshark -q -z io,phs → 协议分布
□ tshark -q -z conv,tcp → 端口/会话统计
□ TCP stream follow → 每个流看看内容
□ DNS 查询 → 隐蔽信道?
□ ICMP 载荷 → 隐蔽信道?
□ TLS → 有 keylog/key/弱密钥?
□ 认证包 → NTLMv2/FTP/HTTP 凭据提取?
□ 异常 → PCAP 需要修复?
```

## 提示

- **`--export-objects http` 是最强命令** — 80% 的 HTTP 题靠这一步直接出
- **先 strings 后 tshark** — strings 最快覆盖 60% 简单题
- **隐蔽信道先看 ICMP** — 载荷长度/时间间隔/字节旋转
- **DNS 隧道先看 subdomain 长度** — >52 字符基本是隧道
- **Webshell 流量看 PUT 方法 + URL 参数 pass=/cmd=**
- **大文件用 editcap 切片**: `editcap -c 10000 big.pcap small.pcap`
- **PCAP 打不开先 pcapfix** — 头部损坏是常见题型
- **WPA 加密先 aircrack-ng** — 密码常在 rockyou.txt 中

---

## 实战技法: DIDCTF 2025-2026

### WPA/WiFi 攻击分析
```bash
# WPA 4次握手检测
tshark -r capture.pcap -Y "eapol"            # 完整的4个EAPOL帧 = 1组有效握手
# WiFi SSID 识别
tshark -r capture.pcap -Y "wlan.fc.type_subtype == 0x0b || wlan.fc.type_subtype == 0x00 || wlan.fc.type_subtype == 0x01"
# 破解: aircrack-ng -a 2 -w wordlist.txt capture.pcap
```

### 路由器管理页爆破 + 密码提取
```bash
# 路由器的WiFi密码可能在管理页HTTP响应中
tshark -r capture.pcap -Y "http.response" -T fields -e http.response.code -e http.file_data
# 爆破成功后返回 302 Found → 下一个请求变 200 OK → 密码在上一请求的 POST body
```

### FTP 文件传输取证
```bash
# FTP 需要同时过滤 ftp 和 ftp-data 才能看到传输的文件
tshark -r capture.pcap -Y "ftp || ftp-data"
# STOR = 上传, RETR = 下载
# 导出 FTP 文件: File → Export Objects → FTP-DATA
```

### Webshell 流量解密 (蚁剑/冰蝎)
```bash
# 蚁剑: URL参数值去前2字符 → base64 → 命令
# 冰蝎: AES-128-CBC + Base64, key 在请求体明文
# Godzilla: AES + Base64×2 + Gzip
# 导出响应体为原始数据 → AES在线解密 → base64解码 → 命令输出
```

### 反弹 Shell 分析
```bash
# 典型反弹shell: /bin/sh -c "mkfifo /tmp/f; ... | nc IP PORT"
tshark -r capture.pcap -Y "tcp.port eq <PORT>"     # 追踪反弹shell端口
# 过滤规则: ip.src == 受害者 && tcp.dstport == $PORT   # 受害者发出的数据
# 追踪TCP流即可看到执行的命令和响应
```

### Web 日志应急分析
```bash
# Apache 访问日志: 提取IP统计
python -c "
from collections import Counter
ips = [line.split()[0] for line in open('access.log') if '2015' in line]
print(Counter(ips).most_common(5))
"
# SSH 登录审计
grep "Accepted password" /var/log/auth.log    # 成功登录
grep "Failed password" /var/log/auth.log      # 失败尝试 (爆破检测)
# Windows 事件日志: 搜索 "审核成功" / "审核失败" → 登录事件
```

### hashcat SHA512 破解 ($6$ 格式)
```bash
# $6$salt$hash → hashcat mode 1800
hashcat -m 1800 hash.txt wordlist.txt
# 常见弱密码: 123456, password, admin, 与用户名相同
```
