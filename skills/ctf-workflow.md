# CTF Competition Workflow Skill

## 概述
CTF（Capture The Flag）电子取证竞赛的通用工具链和工作流程。整合所有 Skill，提供从拿到题目到提交 Flag 的完整流水线。

## 🚀 快速开始（比赛第一分钟）

```batch
REM 1. VeraCrypt 挂载检材到 Z: 盘
REM    (手动操作: VC → 选择文件 → 挂载到 Z:)

REM 2. 初始化环境
call E:\CompetitionTools\scripts\env-setup.bat
REM    → 自动检测 Z: 盘挂载状态

REM 3. 自动分析 Z: 盘
python E:\CompetitionTools\scripts\vc_mount_tool.py --scan -q "题目关键词"
REM    或持续监控模式:
python E:\CompetitionTools\scripts\vc_mount_tool.py --watch
```

> **核心设计**: 所有脚本接受任意路径（`-d Z:\` 或 `Z:\file`），
> 不依赖固定 `cases/` 目录。VC 挂载到哪个盘符就用哪个。

### E01 三件套 (比赛开局必做)
```batch
REM 1. 侦察所有 E01 (秒级)
python E:\CompetitionTools\scripts\e01_tool.py --all

REM 2. 你挂载 NTFS/EXT4 系统盘 → 出现盘符 (如 W:)
REM    我直接用: mmls W: / fls W: / strings W:\*

REM 3. 无盘符的 raw flash → 🥈 dissect.ewf 直接读 (车机/手机够用)
REM    需要全工具 → 🥉 aim_cli /convert 转 RAW (等几分钟)
```

## 工具总览

所有已安装工具在 E:\CompetitionTools 下：

```
E:\CompetitionTools\
├── scoop/shims/          # CLI 工具 (tshark, yara, hashcat, r2, jadx, adb, upx...)
├── scoop/apps/           # 完整应用 (wireshark, qemu, openjdk, imagemagick...)
├── bin/                  # Wrapper 脚本
│   ├── apktool-e.bat    # → D:\apktools\apktool.bat
│   ├── fireye-evidence.bat  # 火眼证据分析V4 (GUI)
│   ├── fireye-simulate.bat  # 火眼仿真取证V4 (GUI)
│   ├── tianhu.bat        # 天狐渗透工具箱V3 (GUI)
│   └── sam-crack.bat     # SAM 密码提取 (CLI)
├── skills/               # Skill 文件 (本目录)
├── wordlists/            # 字典文件
├── cases/                # 比赛题目存放
├── logs/                 # 操作日志
├── pyenvs/               # Python 虚拟环境
├── scripts/              # 自定义脚本
└── tools/                # 手动安装的工具
```

## 标准工作流

### 题目分类 → 工具选择

```
拿到文件
│
├─ 文件类型未知
│   └→ file-analysis.md: 文件分析 Skill
│
├─ 图片/音视频
│   └→ stego.md: 隐写分析 Skill
│       ├→ exiftool → strings → binwalk
│       ├→ zsteg / steghide
│       ├→ imagemagick 通道分离
│       └→ ffmpeg 频谱/逐帧
│
├─ pcap/pcapng
│   └→ network-forensics.md: 网络流量分析 Skill
│       ├→ capinfos → strings → tshark
│       ├→ --export-objects http
│       └→ TCP 流重组
│
├─ 磁盘镜像 (.dd/.img/.E01/.vmdk)
│   └→ disk-forensics.md: 磁盘取证 Skill
│       ├→ mmls → fsstat → fls
│       ├→ icat 提取文件
│       └→ blkls 未分配空间
│
├─ APK
│   └→ android-analysis.md: Android 分析 Skill
│       ├→ 7z x → strings → jadx
│       ├→ Native .so → radare2
│       └→ AndroidManifest 审查
│
├─ 二进制/可执行文件
│   └→ reverse-engineering.md: 逆向工程 Skill
│       ├→ strings → rabin2 → r2
│       ├→ upx -d (脱壳)
│       └→ YARA 规则扫描
│
├─ 密文/编码文本
│   └→ crypto.md: 密码学 Skill
│       ├→ 识别编码类型
│       ├→ hashcat 破解哈希
│       └→ openssl / RSA 分析
│
└─ 内存镜像 (.mem/.dump/.raw)
    └→ disk-forensics.md: Volatility 部分
        ├→ imageinfo → pslist → netscan
        ├→ filescan → dumpfiles
        └→ hashdump / cmdscan
```

## 通用分析命令模板

### 对任意文件的第一轮快速扫描
```bash
FILE="$1"
echo "===== FILE TYPE ====="
file "$FILE"
echo "===== SIZE ====="
ls -lh "$FILE"
echo "===== HASH ====="
md5sum "$FILE"; sha256sum "$FILE"
echo "===== STRINGS (flag) ====="
strings "$FILE" | rg -i "flag|ctf|{.*}|password|secret|key|token"
echo "===== STRINGS (URLs) ====="
strings "$FILE" | rg -i "http://|https://|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
echo "===== EXIF ====="
exiftool "$FILE" 2>/dev/null | rg -i "flag|ctf|comment|description"
echo "===== BINWALK ====="
binwalk "$FILE" 2>/dev/null | head -30
echo "===== NESTED FILES ====="
7z l "$FILE" 2>/dev/null
```

### 批量处理目录下所有文件
```bash
for f in ./cases/*; do
  echo "========================================="
  echo "ANALYZING: $f"
  echo "========================================="
  strings "$f" | rg -i "flag|ctf" && echo ">>> FLAG FOUND in $f <<<"
done
```

## 常用环境变量设置

```powershell
# 新开终端后，一次性设置所有关键 PATH
$env:Path = @(
  'E:\CompetitionTools\scoop\shims',
  'E:\CompetitionTools\scoop\apps\imagemagick\current',
  'E:\CompetitionTools\scoop\apps\openssl\current\bin',
  'E:\CompetitionTools\scoop\apps\qemu\current',
  'E:\CompetitionTools\scoop\apps\openjdk\current\bin',
  'E:\CompetitionTools\bin',
  $env:Path
) -join ';'

# jadx 需要
$env:JAVA_HOME = 'E:\CompetitionTools\scoop\apps\openjdk\current'
```

## 快速参考卡

### 文件 → 工具映射
| 文件扩展名/类型 | 优先工具 |
|---|---|
| .jpg/.jpeg | exiftool → steghide → binwalk |
| .png | pngcheck → zsteg → imagemagick |
| .wav/.mp3 | ffmpeg (频谱) → strings |
| .pcap/.pcapng | tshark → strings → HTTP export |
| .dd/.img/.raw | mmls → fsstat → fls |
| .apk | 7z → strings → jadx |
| .exe/.elf | strings → rabin2 → r2 |
| .zip/.rar/.7z (加密) | hashcat (John) → 7z x |
| .pdf/.docx/.xlsx | binwalk → 7z → strings |
| .mem/.dump | vol (imageinfo → pslist → dumpfiles) |

### 如果找不到 Flag
```
1. 再跑一次 strings | rg -i flag  ← 最容易遗漏
2. 检查文件末尾追加内容
3. 检查 NTFS ADS (dir /R)
4. 检查文件创建/修改时间
5. 对比原版文件（如果有）
6. 检查是否有加密/压缩层
7. 查看 EXIF 的 ALL 字段: exiftool -a -u -g1
8. 检查是否有反取证措施（时间戳修改、加密）
9. 🆕 stego 图片 → 用密码本批量爆破 steghide/outguess
10. 🆕 数据库备份 → 服务器 + 计算机两处都要查
```

### 🆕 多入口统计——数据说话
```bash
# 两个后台入口，哪个是真的？
zcat -f /var/log/nginx/access.log* | \
  awk '$7 ~ /login\.php/ {cnt[$7]++} END {for (p in cnt) print cnt[p], p}' | \
  sort -rn
# 33 /fk/static/login.php  ← 真后台
#  7 /fk/admin/login.php   ← 假后台
```

### 文件分析深度递进
```
Level 1: file + strings + exiftool               (30秒)
Level 2: binwalk + 7z l + 十六进制头             (2分钟)
Level 3: binwalk -e + 递归提取 + 内容分析         (5分钟)
Level 4: 手动 hex 分析 + 文件雕刻                  (30分钟+)
```

## 比赛纪律

1. **每个操作记录到 E:\CompetitionTools\logs**：时间 + 命令 + 输出摘要
2. **原始文件只读**：复制到 cases/ 再分析，不要修改原始证据
3. **Flag 格式验证**：获取后确认格式（如 `flag{...}`、`CTF{...}`）
4. **优先自动扫描**：先用脚本批量跑，再针对可疑文件深入
5. **时间管理**：每个题目设定时间上限，超时先跳过
6. **团队协作**：使用 `E:\CompetitionTools\cases\<题目名>\` 隔离不同题目

## 提示
- **strings + rg flag 是所有分析的第一步**，能解决 30-40% 的简单题
- **先通读所有 Skill 文件了解工具用法**，比赛时直接查对应的 Skill
- **记录自己的脚本** 到 `E:\CompetitionTools\scripts\`，下次复用
- **wordlists/ 放常用字典**（rockyou.txt 等）
- **pyenvs/ 创建项目虚拟环境**，避免依赖冲突

## GUI 取证工具（比赛时手动启动）

| Wrapper | 实际路径 | 用途 |
|---------|----------|------|
| `fireye-evidence` | `E:\BaiduNetdiskDownload\GoldenEyesV4\GoldenEyesV4.exe` | 火眼证据分析：文件解析、内存取证、邮件、注册表、时间线、报表 |
| `fireye-simulate` | `D:\BaiduNetdiskDownload\BootMagixV4\BootMagixV4.exe` | 火眼仿真取证：虚拟机引导、磁盘挂载、系统模拟 |
| `tianhu` | `E:\BaiduNetdiskDownload\天狐渗透工具箱-社区版V3.0\` | 天狐渗透工具箱：Web渗透、漏洞扫描、WEBSHELL管理 |
| `sam-crack` | `D:\BaiduNetdiskDownload\BootMagixV4\SAMClear.exe` | SAM 密码哈希提取 (CLI) |
| 🆕 `autopsy` | `winget: SleuthKit.Autopsy 4.22+` | **Autopsy 法证平台**：GUI 磁盘/手机分析、时间线、MCP Server、自动化报告 |

**注意**: GUI 工具只能由选手手动操作，Reasonix 无法直接控制 GUI 界面。
比赛时可通过终端 `fireye-evidence` / `fireye-simulate` / `tianhu` 快速启动。

### 🆕 Autopsy 4.22.1 — GUI 法证平台

**安装路径**: `C:\Program Files\Autopsy-4.22.1\bin\autopsy64.exe`

```powershell
# 安装（一次性）
winget install SleuthKit.Autopsy

# 启动 GUI
C:\Program Files\Autopsy-4.22.1\bin\autopsy64.exe

# 命令行模式（自动化分析）
autopsy64.exe --createCase --caseDir=C:\cases\case1 --ingest

# 多开（不同案件隔离）
autopsy64.exe --caseDir=C:\cases\case2
```

**核心能力**:
| 模块 | 功能 |
|------|------|
| 磁盘分析 | 自动识别分区/文件系统，时间线可视化 |
| 手机取证 | Android/iOS 镜像解析（SQLite/通话/短信/GPS） |
| 关键词搜索 | 索引化全文搜索 + 正则 + 日期过滤 |
| 媒体预览 | 图片缩略图网格/视频播放/EXIF 面板 |
| 通信分析 | 微信/QQ/Telegram 数据库自动解析 |
| 插件系统 | Java/Python 扩展，社区 300+ 插件 |
| 报告生成 | HTML/PDF/Excel 一键导出 |
| MCP Server | 🆕 4.23.0（升级后）：AI 通过 MCP 对接 Autopsy |

## CLI 工具速查卡（比赛时最常用）

```bash
# === 磁盘镜像 ===
mmls image.E01                        # 看分区
fls -o $OFFSET -r -p image.E01        # 全路径递归列文件
fls -o $OFFSET -d -r image.E01        # 仅已删除
icat -o $OFFSET image.E01 $INODE      # 导出文件
icat -r -o $OFFSET image.E01 $INODE   # 恢复已删除
blkls -A -o $OFFSET image.E01 | strings | rg flag  # 未分配空间搜flag

# === 网络流量 ===
tshark -r file.pcap -T fields -e ip.src -e ip.dst -e http.request.uri
tshark -r file.pcap -Y "http" --export-objects http,./out/
tshark -r file.pcap -q -z io,phs      # 协议统计

# === PE/逆向 ===
rabin2 -I sample.exe                  # PE头信息
radare2 -c "izz" sample.exe           # 字符串
strings sample.exe | rg -i "flag\|password\|key"

# === 模式匹配 ===
yara -r rules.yar ./target/           # 规则扫描
yarac rules.yar compiled.yarc         # 编译规则

# === 元数据 ===
exiftool -a -u image.jpg              # 全量EXIF
exiftool -r -ext jpg ./dir/           # 批量图片

# === 数据库 ===
sqlite3 data.db ".tables"             # 列出表
sqlite3 data.db "SELECT * FROM urls"  # 浏览器历史
```

## Scoop 已安装全部 CLI 工具列表

```
磁盘取证: mmls mmstat mmcat img_stat img_cat fsstat fls ils istat
          icat fcat ffind ifind blkcat blkls blkstat blkcalc
          jls jcat hfind tsk_recover tsk_loaddb tsk_gettimes
          tsk_comparedir tsk_imageinfo pstat
网络分析: tshark wireshark capinfos editcap mergecap text2pcap
逆向工程: radare2 rabin2 radiff2 rahash2 rasm2 rax2 r2
模式匹配: yara yarac (4.5.5)
元数据:   exiftool (13.58)
数据库:   sqlite3 sqlite3_analyzer sqldiff
通用:     7z curl wget ffmpeg jq yq pandoc rg fd adb fastboot upx
密码:     hashcat (pip)
内存:     volatility3 (pip 2.27.0)
GUI:      fireye-evidence fireye-simulate tianhu autopsy 🆕
```
