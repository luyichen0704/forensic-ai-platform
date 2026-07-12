# 电子取证竞赛优化策略 — 大文件低密度场景

## 核心问题

| 特征 | 痛点 | 传统做法 | 优化做法 |
|------|------|----------|----------|
| 磁盘镜像 50-200GB+ | 全盘扫描不现实 | 等火眼慢慢解析 | **线索驱动定向搜索** |
| 99% 是系统文件 | 90% 时间花在无关数据 | `strings \| rg flag` 暴力 | **先理解题目 → 预测目标位置** |
| Flag 在 1-2 个文件 | 大海捞针 | 逐个文件手动翻 | **并行扫描 + 命中即停** |
| 多检材联动 | 孤立分析效率低 | 一个一个看 | **先建证据链，跨检材关联** |

## 策略 1: 线索驱动定向搜索

### 不要做的事
```bash
# ❌ 全盘扫描 — 浪费时间
strings disk.img | rg flag
mmls disk.img && fls -o 2048 -r disk.img | rg flag
```

### 应该做的事
```bash
# ✅ 先读题目，推断目标
# 题目: "李安弘曾收到一封免费领取token的钓鱼邮件，其发送用户邮箱为"
# → 目标: 邮件数据 → 路径: mail/, .pst, .ost, thunderbird/
# → 关键词: "token", "免费", "领取"

python smart_hunter.py -c ./case/ -q "李安弘 邮件 发送用户 邮箱"
```

### 题目关键词 → 目标路径映射

| 题目关键词 | 最可能的位置 |
|-----------|-------------|
| 邮件/email | /mail/, .pst, .ost, thunderbird/, outlook/ |
| 浏览器记录 | History, Bookmark, places.sqlite, Login Data |
| 聊天记录 | WeChat/, QQ/, Telegram/, signal/ |
| 密码/登录 | /etc/shadow, SAM, NTUSER.DAT, .bash_history |
| VPN/代理 | clash/, v2ray/, shadowsocks/, wireguard/ |
| AI/模型 | config/, settings/, llm_cache.db, ~/.config/ |
| 备忘录 | sticky notes, notepad, memo, notes/ |
| 照片/图片 EXIF | Pictures/, DCIM/, Screenshots/ |
| APK/应用 | .apk, app/, downloads/ |
| 加密文件 | .enc, .gpg, Veracrypt 容器, .7z/.rar (加密) |

## 策略 2: 分层扫描（先浅后深，命中即停）

```
Level 0 (5秒):   strings DISK | rg "flag|ctf"           ← 最快，覆盖 30%
Level 1 (30秒):  smart_hunter.py 定向扫描                ← 覆盖 50%
Level 2 (2分钟): 火眼加载 + 仿真系统启动                   ← 覆盖 15%
Level 3 (10分钟): icat 逐个提取 + 深度 hex 分析            ← 覆盖 5%

规则: Level N 命中 flag 后不再进入 Level N+1
```

## 策略 3: 嫌疑人操作路径重建

博客最核心技巧 — 不要找 Flag，找"嫌疑人做了什么"：

```
1. 搜索浏览器历史 → 知道嫌疑人搜了什么
2. 搜索 .bash_history → 知道嫌疑人执行了什么命令
3. 搜索最近文件 (Recent/) → 知道嫌疑人打开/编辑了什么
4. 搜索下载记录 → 知道嫌疑人下载了什么工具
5. 找到工具 → 逆向工具逻辑 → 解密目标文件
```

### 命令模板
```bash
# 1. 浏览器搜索历史
sqlite3 History.db "SELECT url, title FROM urls WHERE title LIKE '%加密%' OR url LIKE '%encrypt%'"

# 2. Shell 历史
strings .bash_history | rg -i "curl|wget|apt|pip|git clone|python|openssl|encrypt|decrypt"

# 3. 最近文件
fls -o 2048 -r disk.img | rg -i "Recent|recently|last"

# 4. 下载目录
fls -o 2048 disk.img/Users/*/Downloads/ | head -50
```

## 策略 4: 并行处理

```bash
# ❌ 串行 — 一个一个等
for f in *.pcap; do tshark -r $f -Y http; done

# ✅ 并行 — 同时跑
ls *.pcap | xargs -P 8 -I {} tshark -r {} -Y http

# ✅ Python 并行扫描
python smart_hunter.py -c ./case/ -w 16   # 16 线程
```

## 策略 5: 配置文件优先于文档正文

```
搜索优先级:
1. *.conf, *.cfg, *.ini, *.json, *.yaml     ← 配置
2. *.db, *.sqlite, *.sqlite3                ← 数据库
3. *.log, *.txt, *.md                       ← 文本
4. *.doc, *.docx, *.pdf, *.xlsx             ← 文档
5. *.png, *.jpg, *.mp4                      ← 媒体
```

## 策略 6: 多检材联动流程

```
拿到 N 个检材:
│
├─ Step 1: 运行 evidence_linker.py 建立关联
│   ├─ 相同邮箱 → 同一人
│   ├─ 相同 IP → 同一网络
│   ├─ 相同文件哈希 → 复制/传输
│   └─ .enc + .key → 加密文件 + 密钥
│
├─ Step 2: 从最容易被攻破的检材入手
│   手机 > 电脑 > 服务器 > 加密容器
│
├─ Step 3: 提取的密码/密钥 → 其他检材
│   "VC密码：9ed2@99y8.com.cn" (从手机) → 解锁电脑分区
│
└─ Step 4: 建立时间线
    邮件时间 → 下载时间 → 感染时间 → 加密时间
```

## 策略 7: 仿真优先原则

```
对于完整系统镜像（有 OS）:
  先仿真 → GUI 查看 → 比静态分析快 10 倍

fireye-simulate   ← 启动火眼仿真
# 在仿真系统中:
# - 桌面文件 一目了然
# - 应用设置 直接查看
# - 系统信息 直接获取
# - 浏览器 直接打开查看历史
```

## 比赛时间分配建议 (4 小时制)

```
0:00-0:05  通读所有题目，标记关键词
0:05-0:15  运行 smart_hunter.py 定向扫描
0:15-0:30  strings 批量扫 + evidence_linker 关联
0:30-1:30  火眼加载 + 仿真（后台）+ 手动分析命中文件
1:30-3:00  深度分析（逆向 / 解密 / 数据库）
3:00-3:30  复查 + 补充
3:30-4:00  收尾 + 写报告
```

## 工具速查

| 工具 | 位置 | 用途 |
|------|------|------|
| `smart_hunter.py` | `E:\CompetitionTools\scripts\` | 智能定向搜索 |
| `evidence_linker.py` | `E:\CompetitionTools\scripts\` | 多检材关联 |
| `auto_scanner.py` | `E:\CompetitionTools\scripts\` | 单文件全扫描 |
| `rsa_fermat.py` | `E:\CompetitionTools\scripts\` | RSA 快速分解 |
| `mp4_stco_fix.py` | `E:\CompetitionTools\scripts\` | MP4 修复 |
| `excel_crypt.py` | `E:\CompetitionTools\scripts\` | Excel 加解密 |
| `fireye-evidence` | `E:\CompetitionTools\bin\` | 火眼证据分析 |
| `fireye-simulate` | `E:\CompetitionTools\bin\` | 火眼仿真 |
| `sam-crack` | `E:\CompetitionTools\bin\` | SAM 密码提取 |
| `apk_batch_analyzer.py` | `E:\CompetitionTools\scripts\` | APK 批量分析 + JSON 配置 |
| `win_forensics.py` | `E:\CompetitionTools\scripts\` | Windows 取证（注册表/Prefetch/日志/LNK） |
| `format_analyzer.py` | `E:\CompetitionTools\scripts\` | 未知文件格式分析 |
| `evidence_linker.py` | `E:\CompetitionTools\scripts\` | 多检材证据链关联 |
