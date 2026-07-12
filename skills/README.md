# Competition Tools — 完整索引

## 🏗 框架层 (`_framework/`)
| 文件 | 职责 |
|------|------|
| `competition-autopilot.md` | 总控入口 — 用户给题目+附件，自动分流分析 |
| `tool-router.md` | Win/WSL 路由判断 |
| `triage-files.md` | 第一轮只读初筛 |
| `large-artifact-strategy.md` | ≥1GB 大文件策略 |
| `case-notes.md` | 笔记 + Writeup 模板 |

## 专项 Skill (15 个)

## 已安装 Skill 列表

| # | Skill 文件 | 主题 | 适用场景 |
|---|-----------|------|----------|
| 1 | `file-analysis.md` | 文件分析 | 未知文件识别、类型伪造、嵌套提取、hex分析 |
| 2 | `stego.md` | 隐写分析 | 图片/音频/视频隐写、LSB、steghide |
| 3 | `network-forensics.md` | 网络流量分析 | PCAP分析、协议分析、HTTP/DNS/FTP流量 |
| 4 | `disk-forensics.md` | 磁盘取证 | 磁盘镜像、文件系统、Volatility内存取证 |
| 5 | `crypto.md` | 密码学 | 编码/解码、古典密码、RSA、哈希破解 |
| 6 | `reverse-engineering.md` | 逆向工程 | 二进制逆向、radare2、脱壳、YARA |
| 7 | `android-analysis.md` | Android分析 | APK逆向、jadx、Native .so分析 |
| 8 | `ctf-workflow.md` | CTF工作流 | 总流程编排、文件→工具映射、快速参考 |
| 9 | `optimization-strategy.md` | 大文件优化 | 线索驱动搜索、分层扫描、并行处理 |
| 10 | `incident-response.md` | 应急响应 | 挖矿/勒索/Webshell/持久化检测 |
| 11 | `server-forensics.md` | 服务器取证 | ESXi/Hyper-V/KVM/Docker/宝塔/国产OS |
| 12 | `ai-forensics-workflow.md` | AI辅助取证 | Trae/MCP/Reasonix 自动化取证工作流 |

## 自研脚本清单

| 工具 | 路径 |
|------|------|
| Scoop CLI | `E:\CompetitionTools\scoop\shims\*` |
| Python | `C:\Users\<user>\AppData\Local\Programs\Python\Python313\python.exe` |
| Git Bash | `C:\Program Files\Git\usr\bin\*` |
| OpenJDK | `E:\CompetitionTools\scoop\apps\openjdk\current\` |
| Wrapper脚本 | `E:\CompetitionTools\bin\` |
| Ruby Gems | `E:\CompetitionTools\scoop\apps\ruby\current\gems\bin\` |
| Python Scripts | `%LOCALAPPDATA%\Programs\Python\Python313\Scripts\` |
| 自定义脚本 | `E:\CompetitionTools\scripts\` |

## 新增工具 (第三轮)

| 工具 | 类型 | 用途 |
|------|------|------|
| `volatility3` (2.27.0) | pip | 内存取证框架 (Win/Linux/Mac) |
| `zsteg` (0.2.14) | Ruby gem | PNG/BMP LSB 隐写检测 |
| `stegoveritas` (1.11) | pip | 综合隐写分析框架 |
| `oletools` (0.60.2) | pip | Office 文档宏分析 (olevba, oledump...) |
| `pwntools` (4.14.1) | pip | Pwn/二进制利用工具 |
| `pycryptodome` (3.23.0) | pip | 密码学库 |
| `auto_scanner.py` | 自研 | 一键自动扫描脚本 |
| `rsa_fermat.py` | 自研 | RSA Fermat 分解脚本 |
| `mp4_stco_fix.py` | 自研 | MP4 stco 表修复 (反勒索) |
| `webshell_decoder.py` | 自研 | Webshell 流量解密 (AES+Base64+Gzip) |
| `apk_batch_analyzer.py` | 自研 | APK 批量分析 + JSON 配置提取 |
| `win_forensics.py` | 自研 | Windows 取证 (注册表/Prefetch/日志) |
| `format_analyzer.py` | 自研 | 未知文件格式分析器 |
| `smart_hunter.py` | 自研 | 智能定向搜索引擎 |
| `evidence_linker.py` | 自研 | 多检材证据链关联 |
| `auto_scanner.py` | 自研 | 一键全扫描 |
| `rsa_fermat.py` | 自研 | RSA Fermat 分解 |
| `mp4_stco_fix.py` | 自研 | MP4 stco 表修复 |
| `excel_crypt.py` | 自研 | Excel 坐标加解密 |

## 使用方式

每个 Skill 文件包含：
1. 适用场景说明
2. 工具清单及路径
3. 分步分析流程（含具体命令）
4. 常见题型和 Flag 藏匿方式
5. 提示和注意事项

比赛时直接打开对应 Skill 文件，按流程执行命令。
