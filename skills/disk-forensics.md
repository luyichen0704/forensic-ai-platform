# Disk Forensics Skill — CTF / Forensics

## 适用场景
磁盘镜像分析、文件系统取证、已删除文件恢复、分区分析、内存镜像初步分析、时间线重建。

## ⚡ E01 三件套 (实战验证)

### 核心认知
```
E01 能读 ≠ sleuthkit 能读
但不需要每个 E01 都转 RAW —— 根据场景选工具
```

### 🥇 AIM 挂载 (首选 — 需要你操作一次)
```bash
# 你: AIM GUI → 挂载 NTFS/EXT4 E01 → 自动出现盘符 (如 W:)
# 我: 所有 40+ 工具直接可用
mmls W:
fls -o $OFFSET -r W:
strings W:\Users\*\Desktop\*
```
**适合**: NTFS/EXT4 系统盘。挂载一次，全工具激活。
**限制**: raw flash (car.E01) 无盘符，需管理员装驱动一次。

### 🥈 dissect.ewf 直接读 (零操作)
```bash
python -c "from dissect.evidence.ewf import EWF; ..."
```
**适合**: 已知偏移读取、快速探查、raw flash、手机镜像。
**限制**: 仅 Python 能用，sleuthkit/strings/7z 不行。

### 🥉 aim_cli /convert 转 RAW (零权限，等待几分钟)
```bash
python E:\CompetitionTools\scripts\e01_convert.py "Z:\xxx.E01"
mmls E:\raw\xxx.raw
fls -o $OFFSET -r E:\raw\xxx.raw
```
**适合**: 无盘符但需要全工具分析、批量转换。
**限制**: 耗时（大文件数分钟），占空间（RAW = E01 × 5-9倍）。

### 决策速查
| 检材类型 | AIM 挂载 | 方案 |
|----------|:---:|------|
| NTFS/EXT4 系统盘 (PC/Server) | ✅ 有盘符 | 🥇 你挂载 → 我秒出 |
| raw flash / 车机固件 | ❌ 无盘符 | 🥈 dissect.ewf 已经够用 |
| raw flash 需全工具 | ❌ 无盘符 | 🥉 转 RAW (15GB很快) |
| 手机镜像 (>200GB) | ❌ 太大 | 🥈 dissect.ewf (实际数据仅~5%) |
| vSAN 数据盘 | ❌ 高熵 | 不分析 |

### 快速命令
```bash
# 侦察 (秒级)
python E:\CompetitionTools\scripts\e01_tool.py --all

# 挂载后的盘符直接用 (秒级)
mmls W: 2>/dev/null && fls -o $OFFSET W:

# 无盘符时转 RAW (分钟级)
python E:\CompetitionTools\scripts\e01_convert.py "Z:\xxx.E01"
```

## 工具清单

### 🧰 Sleuth Kit 4.15.0 — 完整 26 工具（scoop 安装）

#### 分区 / 卷系统（5 个）
| 工具 | 功能 | 关键参数 |
|------|------|---------|
| `mmls` | 分区表枚举（MBR/GPT） | `-t dos\|gpt` `-o imgoffset` |
| `mmstat` | 快速识别卷系统类型 | `-t vstype` `-o imgoffset` |
| `mmcat` | 提取指定卷数据 | `-o imgoffset vol_id` |
| `img_stat` | 镜像元信息（大小/类型） | |
| `img_cat` | 导出原始镜像内容 | `-o imgoffset` |

#### 文件系统层（4 个）
| 工具 | 功能 | 关键参数 |
|------|------|---------|
| `fsstat` | 文件系统详情（大小/簇/块） | `-f fstype` `-o imgoffset` |
| `fls` | 列出文件/目录 | **`-r` 递归** **`-d` 仅已删除** `-m` mactime格式 `-p` 全路径 |
| `ils` | 列出所有 inode（含 orphan） | `-o imgoffset` |
| `istat` | inode 详情（数据块地址列表） | `-r` 显示 run list |

#### 文件提取（5 个）
| 工具 | 功能 | 关键参数 |
|------|------|---------| 
| `icat` | 按 inode 导出文件内容 | **`-r` 恢复已删除** `-s` 含slack |
| `fcat` | 按 inode 导出（与icat类似） | |
| `ffind` | 文件名 → inode 查找 | |
| `ifind` | 数据块 → 归属 inode（谁在用这个块） | `-d` 含已删除 |
| `tsk_recover` | 批量恢复所有文件 | **`-e` 含已删除** `-a` 仅已分配 |

#### 块级操作（4 个）
| 工具 | 功能 | 关键参数 |
|------|------|---------|
| `blkcat` | 按块号导出数据 | |
| `blkls` | 批量导出块数据 | **`-A` 仅未分配** `-s` 仅slack `-e` 所有块 |
| `blkstat` | 显示块分配状态 | |
| `blkcalc` | 未分配块 → 原始块映射 | |

#### 日志 / 哈希 / 辅助（8 个）
| 工具 | 功能 |
|------|------|
| `jls` | 列出文件系统日志条目（NTFS $LogFile） |
| `jcat` | 按 sector 导出日志内容 |
| `hfind` | 哈希数据库查询（NSRL/md5sum/EnCase） |
| `tsk_loaddb` | 导出取证数据到 SQLite |
| `tsk_gettimes` | 提取所有文件 MAC 时间 |
| `tsk_comparedir` | 目录对比（含哈希） |
| `tsk_imageinfo` | 多镜像信息汇总 |
| `pstat` | 进程/swap 信息 |
| `fcat` | 替代 icat 的文件提取 |

#### 快速命令链（TSK 三部曲）
```bash
# 1. 侦察
mmls image.E01                         # 分区布局
fsstat -o 2048 image.E01               # 文件系统详情

# 2. 遍历
fls -o 2048 -r -p image.E01            # 全路径递归
fls -o 2048 -d -r image.E01            # 仅已删除文件

# 3. 提取
icat -o 2048 image.E01 12345-128-4 > file.txt  # 按 inode 导出
icat -r -o 2048 image.E01 12345-128-4          # 恢复已删除
tsk_recover -e -o 2048 image.E01 ./out/         # 批量恢复
blkls -A -o 2048 image.E01 | strings | rg flag  # 未分配空间搜索
```

#### 🆕 Autopsy 4.22+ — GUI 法证平台（winget 安装）

| 功能 | 说明 |
|------|------|
| 案件管理 | 多证据源统一时间线 |
| 手机取证 | Android/iOS 镜像直接解析 |
| 关键词搜索 | 索引化全文搜索 + 正则 |
| 媒体预览 | 内置图片/视频查看器 |
| MCP Server | 🆕 4.23.0：AI 工具通过 MCP 对接 Autopsy |
| 自动化报告 | HTML/PDF 一键生成 |

```bash
# Autopsy 启动（已安装 4.22.1）
C:\Program Files\Autopsy-4.22.1\bin\autopsy64.exe
# winget 安装（一次性）:
winget install SleuthKit.Autopsy
```

### 其他取证工具

| 工具 | 用途 | 路径 |
|------|------|------|
| `vol` | 内存取证(vol2) | Python Scripts |
| `volatility3` | 内存取证框架 vol3 | `pip` (Python, 2.27.0) |
| `strings` | 字符串提取 | git-bash |
| `rg` | 内容搜索（ripgrep） | scooped |
| `7z` | 解压 E01/RAW 等 | scooped |
| `qemu-img` | 虚拟磁盘转换 | scooped |
| `yara` | 模式匹配规则扫描 | scooped (4.5.5) |
| `exiftool` | 元数据提取 | scooped (13.58) |
| `sqlite3` | 数据库分析 | scooped |

## 分析流程

### 第一步：镜像识别
```bash
# 基础信息
file disk.img
img_stat disk.img
fsstat disk.img

# 查看分区布局
mmls disk.img
mmls -t dos disk.img    # MBR
mmls -t gpt disk.img    # GPT
```

输出示例：
```
DOS Partition Table
Offset Sector: 0
Units are in 512-byte sectors

Slot  Start    End      Length   Description
00:   0000002048  0000206847  0000204800  NTFS (0x07)
01:   0000206848  0000411647  0000204800  Linux (0x83)
```

### 第二步：文件系统分析
```bash
OFFSET=2048   # 从 mmls 获取

# 文件系统信息
fsstat -o $OFFSET disk.img

# 列出所有文件（含已删除）
fls -o $OFFSET -r disk.img
fls -o $OFFSET -r -m / disk.img > bodyfile.txt

# 只列已删除文件
fls -o $OFFSET -r -d disk.img

# 查找特定文件
fls -o $OFFSET -r disk.img | rg -i "flag|password|secret|confidential"
fls -o $OFFSET -r disk.img | rg "\.txt$|\.docx$|\.pdf$|\.xlsx$"
```

### 第三步：文件提取
```bash
OFFSET=2048
INODE=12345    # 从 fls 获取

# 提取单个文件
icat -o $OFFSET disk.img $INODE > recovered_file

# 提取到目录
icat -o $OFFSET disk.img $INODE > recovered/$(fls -o $OFFSET -r disk.img | grep $INODE | awk '{print $NF}')

# 提取未分配空间
blkls -o $OFFSET disk.img > unallocated.bin
strings unallocated.bin | rg -i "flag|ctf|password"

# 批量恢复
tsk_recover -o $OFFSET disk.img ./recovered/
```

### 第四步：时间线分析
```bash
# 生成 bodyfile
fls -o $OFFSET -r -m / disk.img > bodyfile.txt

# MAC 时间分析 (Modified, Accessed, Changed)
# bodyfile 格式: MD5|name|inode|mode|UID|GID|size|atime|mtime|ctime|crtime
sort -t'|' -k8 bodyfile.txt | tail -100   # 按访问时间排序
sort -t'|' -k9 bodyfile.txt | tail -100   # 按修改时间排序

# 使用 mactime 生成时间线
mactime -b bodyfile.txt -d > timeline.csv
```

### 第五步：常见证据位置

#### Windows 取证
```bash
# 注册表文件
icat -o $OFFSET disk.img <inode> > NTUSER.DAT
icat -o $OFFSET disk.img <inode> > SAM
icat -o $OFFSET disk.img <inode> > SYSTEM

# 用户目录关键文件
# /Users/<user>/AppData/Local/Google/Chrome/User Data/Default/History
# /Users/<user>/AppData/Roaming/Microsoft/Windows/Recent/
# /Users/<user>/AppData/Local/Microsoft/Windows/WebCache/

# 回收站
# /$Recycle.Bin/

# 事件日志
# /Windows/System32/winevt/Logs/

# Prefetch
# /Windows/Prefetch/

# LNK 文件
fls -o $OFFSET -r disk.img | rg "\.lnk$"

# 浏览器历史 - sqlite3 分析
sqlite3 History.db "SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 50"
```

#### Linux 取证
```bash
# Shell 历史
icat -o $OFFSET disk.img <inode> > .bash_history

# SSH 密钥/known_hosts
fls -o $OFFSET -r disk.img | rg -i "\.ssh/|authorized_keys|known_hosts"

# 登录日志 (如果有 /var/log)
fls -o $OFFSET -r disk.img | rg -i "auth\.log|syslog|wtmp|lastlog"

# Cron 任务
fls -o $OFFSET -r disk.img | rg -i "cron"
```

### 第六步：已删除文件恢复
```bash
# 列出已删除文件（前面带 * 且在 fls -d 中）
fls -o $OFFSET -d -r disk.img

# 尝试恢复已删除文件
for inode in $(fls -o $OFFSET -d -r disk.img | awk '{print $2}' | tr -d ':'); do
  icat -o $OFFSET disk.img $inode > recovered/del_$inode 2>/dev/null
done

# 从未分配空间恢复
blkls -o $OFFSET disk.img > unalloc.bin
foremost unalloc.bin -o foremost_out/
```

### 第七步：内存镜像 (Volatility)
```bash
# 镜像识别
vol -f memory.dump imageinfo

# 进程列表
vol -f memory.dump --profile=<profile> pslist
vol -f memory.dump --profile=<profile> psscan   # 含已结束进程

# 网络连接
vol -f memory.dump --profile=<profile> netscan
vol -f memory.dump --profile=<profile> connections

# 命令行历史
vol -f memory.dump --profile=<profile> cmdscan
vol -f memory.dump --profile=<profile> consoles

# 文件扫描
vol -f memory.dump --profile=<profile> filescan | rg -i "flag|password|secret"

# 提取文件
vol -f memory.dump --profile=<profile> dumpfiles -Q <offset> -D out/

# 注册表
vol -f memory.dump --profile=<profile> hivelist
vol -f memory.dump --profile=<profile> printkey -K "Software\Microsoft\Windows\CurrentVersion"

# 密码哈希
vol -f memory.dump --profile=<profile> hashdump

# 恶意代码检测
vol -f memory.dump --profile=<profile> malfind
vol -f memory.dump --profile=<profile> ldrmodules
```

## 快速命令速查
```bash
# 一键预览镜像
mmls disk.img && fsstat -o 2048 disk.img && fls -o 2048 -r disk.img | head -50

# 搜索所有已删除的 txt/doc
fls -o 2048 -d -r disk.img | rg "\.txt|\.doc|\.pdf"

# 提取未分配空间并搜索 flag
blkls -o 2048 disk.img | strings | rg -i "flag|ctf"
```

## 提示
- **`mmls` → `fsstat` → `fls` 是固定三部曲**
- **未分配空间是 Flag 最常藏匿的地方**：已删除文件 ≠ 内容消失
- **`strings` 直接跑镜像，不等 `fls`，最快发现 Flag**
- **注意时区**：FAT 时间用本地时区，NTFS 用 UTC

---

## 补充专题: ctf-skills 实战技术 (2025-2026)

### KAPE 取证包快速分析
```bash
# KAPE triage ZIP 结构: 已预提取的 Windows 取证产物
# 优先查看:
# 1. PowerShell 历史 (ConsoleHost_history.txt)
# 2. Amcache (执行历史 + SHA1)
# 3. $MFT (resident data for small files → flag 可能内嵌)
# 4. SAM/SYSTEM → impacket 提哈希
```

### NTFS 备用数据流 (ADS)
```bash
fls -r disk.img | grep ":"       # 所有 ADS
icat disk.img 66-128-4 > hidden  # 按 inode-type-id 提取
```

### USN Journal 分析
```bash
# $Extend\$J — 文件系统变更日志，日志清除后仍可用
# 用于: 已删除文件时间线 / PowerShell 执行时间 / wmiexec 痕迹
```

### VM 取证 (OVA/VMDK)
```bash
7z l disk.vmdk | head -100          # 直接读取 VMDK 不需挂载!
7z x disk.vmdk -oout "Windows/System32/config/SAM" -r
```

### VMware 快照 → 内存镜像
```bash
vmss2core -W snapshot.vmss snapshot.vmem  # → memory.dmp → Volatility
```

### Docker 取证
```bash
docker history IMAGE --no-trunc   # 构建历史 (含 ARG/ENV 密码)
# 每层 layer.tar 含文件变更; 删除的文件在前几层仍可见
```

### GIMP 裸看内存镜像
```
Volatility 失败时: GIMP → Open as Raw Image Data → RGB, width=1920
→ 滚动偏移量 → 屏幕截图直接显示!
```

### Windows 取证关键 Event ID
| ID | 含义 |
|----|------|
| 4720 | 用户创建 |
| 4624 | 登录成功 |
| 4688 | 进程创建 |
| 1102 | 日志被清除(!) |
| 1149 | RDP 认证(含源IP) |

### 反取证检测清单
```
日志清除时仍有: USN Journal / SAM 注册表 / PowerShell 历史 /
Prefetch / MFT / Defender MPLog / 浏览器历史 / 注册表时间戳
```

### cipher.exe 擦除检测
```bash
# EFSTMPWP 目录 = cipher.exe /w 痕迹 → 空闲空间已被覆盖，放弃文件恢复
find /mnt -name 'EFSTMPWP'
```

### Registry + SAM
```bash
# OEMInformation → 检查 SupportURL (后门 C2)
# SAM + SYSTEM → impacket secretsdump → hashcat -m 1000
```

---

## USB 设备取证 (DIDCTF 2026)

```bash
# 火眼: 注册表时间线 → 搜索 USB → 找 VID/PID/序列号/最后插拔时间
# 属性ID 0x64 (100) = FirstInstallTime, 0x65 (101) = LastConnectedTime
# volatility3: vol -f mem.dmp windows.registry.printkey
# VID_0781 = SanDisk, VID_058F = Alcor, VID_0951 = Kingston
```

## BitLocker 恢复密钥
```bash
# .bek 文件 = BitLocker 恢复密钥文件 (可能在其他分区或U盘)
fls -r disk.img | grep "\.bek$"
icat disk.img <inode> > recovery_key.bek
```

### BitLocker 从内存恢复 (盘古石杯2026)
```bash
# 1. 从文档文件夹找恢复密钥文本
strings disk.img | grep "BitLocker.*恢复密钥"
# 2. 用内存镜像恢复: efdd / passware kit
#    efdd: Decrypt disk → 选分区 → 指定内存镜像 → 自动提取密钥
# 3. 验证恢复密钥: 每组6位数字 % 11 == 0 (BitLocker 校验规则)
# 4. 仿真: manage-bde -unlock D: -RecoveryPassword <密钥>
```

## AI 工具取证 (2026新增)
```bash
# AI 编程助手 (Claude): .claude/settings.json → 模型/token
# AI 换脸 (FaceFusion): 默认端口 7860, 模型 .onnx, 日志 .jobs/
# AI 语音 (ChatTTS): 默认端口 8080, 随机种子 42, 输出 audio.wav
# 翻墙软件 (Clash Verge): 配置文件 .yaml, 默认端口 7890
# 直播软件 (OBS): 输出→音频码率 (如128)
```

## 回收站取证
```bash
# $Recycle.Bin/<SID>/$Ixxx.xxx → 元数据 (原始路径+删除时间)
# $Recycle.Bin/<SID>/$Rxxx.xxx → 文件内容
fls -r disk.img | grep '\$Recycle'
strings \$I* | grep "C:"   # 查看原始路径
```

## 浏览器密码提取
```bash
# Chrome/Edge: Login Data → sqlite3
sqlite3 "Login Data" "SELECT origin_url,username_value,password_value FROM logins"
# Firefox: logins.json + key4.db
# 火眼: 自动解析 "自动填充" 中的密码
```

## 模拟器识别
```bash
# 火眼 → 已安装软件 → 搜索:
#   nox (夜神), MEMU (逍遥), LDPlayer (雷电), BlueStacks
# 或查看 Program Files 目录
```
