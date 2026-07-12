# 跨检材关联 + 网络搜索 Skill

## 一、核心思维模型：证据链溯源

```
检材1 (手机)     检材2 (计算机)      检材3 (服务器)       外部
───────────     ────────────       ────────────         ────
聊天记录 ─────→ 下载的文件           聊天记录 ←──→ 数据贩子
浏览器历史 ────→ 搜索关键词
                备份脚本 ──────────→ scp ──────────→ 境外服务器
                                                                 │
                嫌疑人下载 ←────────────────────────────── 完整备份
```

### 铁律
> **凡是跨设备出现的信息，必定在某处留有传输痕迹。**

---

## 二、跨检材关联方法

### 2.1 密码/凭据传播链

同一个嫌疑人，密码有规律可循：

```
zznote → steghide密码: JHTJ@202605
        → VC外层密码:   JHTJ！@#￥A313
        → VC隐藏密码:   JHTJ@20260512（推测）
        → 格式规则:      4字母 + 1符号 + 8位日期
        → 密码.txt 里有格式说明
```

**搜索策略**：
```bash
# 在所有检材中搜索同一密码前缀
for evidence in 检材1 检材2 检材3; do
    strings $evidence | grep -i "JHTJ" 
done

# 找到了 → 记录位置 → 交叉验证 → 推导完整密码
```

### 2.2 数据库备份传播链

```
服务器 autobackup.sh:
  mysqldump → gzip → /tmp/db_backup/fk_xxx.sql.gz
                       │
                       └→ scp root@8.208.44.202:/root/
                              │
嫌疑人下载到计算机:             │
  D:\BaiduNetdiskDownload\faka.sql (SHA256 = FF8180)
```

**搜索策略**：
```bash
# 1. 在服务器上找到备份脚本
grep -r "mysqldump\|scp\|backup" /etc/cron* /root/

# 2. 提取目标 IP 和路径
cat /etc/cron.daily/autobackup.sh | grep -E "REMOTE|scp|rsync"

# 3. 在计算机检材中搜索同名/同内容文件
fls -r -o $OFFSET computer.E01 | grep -i "faka.*sql\|backup.*sql"

# 4. 搜索计算机上所有 .sql 文件
fls -r -o $OFFSET computer.E01 | grep "\.sql$"

# 5. 找到后对比哈希，确认是完整的版本
sha256sum faka_from_computer.sql   # FF8180（完整版）
sha256sum /opt/faka.sql            # 1C6B88（服务器旧版，缺数据）
```

### 2.3 聊天记录跨平台迁移

```
连趣交友 (com.lianqujiaoyou.chat)
  └→ "你手机有i聊应用吗？"
  └→ "安装好了，怎么加你？"
  
UNI App (uni.app.UNI04963C4)  ← 这才是"i聊"！
  └→ 付款方式、银行卡号、压缩包密码
```

**搜索策略**：
```bash
# 1. 列出手机上所有聊天类 App
tar tf phone.tar | grep -E "com\..*(chat|liao|msg|im)" | sort -u

# 2. 对每个 App 的数据库，搜索转账/付款关键词
for db in *.db; do
    sqlite3 $db "SELECT * FROM messages WHERE content LIKE '%付款%' OR content LIKE '%银行卡%'"
done

# 3. 如果某个 App 没有聊天数据 → 检查是否用另一个名字
#    连趣聊了前半段 → i聊（UNI App）聊了后半段
```

### 2.4 浏览器下载链

```
土狗浏览器 (com.tugoubutu.liulanqi)
  └→ 搜索 "steghide隐写工具下载" → sourceforge.net

鲁班浏览器 (com.meiit.browser)  
  └→ 百度网盘下载 数据.zip
```

**搜索策略**：
```bash
# 识别手机上所有浏览器
tar tf phone.tar | grep -E "com\..*browser" | sort -u

# 检查每个浏览器的下载数据库
for browser in com.tugoubutu.liulanqi com.meiit.browser com.heytap.browser; do
    echo "=== $browser ==="
    sqlite3 data/$browser/databases/download*.db "SELECT * FROM downloads"
done

# 检查本地存储（LevelDB）中的访问历史
strings data/$browser/*/Local Storage/leveldb/*.log | grep -i "http\|\.zip\|download"
```

### 2.5 同一嫌疑人多设备操作时间线

```
服务器操作时间线:
  2026-05-11 服务器初始化（install.lock = 2023/3/15）
  2026-05-12 嫌疑人部署守卫脚本
  2026-05-13 嫌疑人修改上传限制为 60M
  2026-05-14 数据库备份最后一次执行

计算机操作时间线:
  2026-05-12 16:36 嫌疑人安装 i聊
  2026-05-12 16:48 数据贩子发送数据 → 嫌疑人下载
  2026-05-12 17:00 百度网盘下载完成（filelist.db 时间戳）

手机操作时间线:
  2026-05-12 15:35 连趣联系数据贩子
  2026-05-12 16:33 切换到 i聊 谈论价格
  2026-05-12 16:48 数据.zip 下载到手机
```

**关联验证**：如果手机下载时间(16:48) ≈ 计算机聊天时间(16:48) → 同一事件，证据可信。

---

## 三、网络搜索实战技巧

### 3.1 比赛后搜索 Writeup

```bash
# 微信公众号搜索（百度/搜狗微信入口）
site:mp.weixin.qq.com "獬豸杯" "wp" OR "writeup"

# 直接搜索题目关键词
"2026獬豸杯" OR "獬豸杯2026" wp

# GitHub 搜索（代码/工具/规则）
site:github.com "獬豸杯" OR "xiezhi" forensics

# CSDN/知乎
site:blog.csdn.net 电子取证 CTF writeup 2025
site:zhihu.com 电子取证 比赛
```

### 3.2 工具/格式查找

```bash
# 文件魔数/签名
"RNSMa file magic" OR "RNSM ransomware"

# 加密算法识别
"BCRYPT_AES_ALGORITHM" Chaining Mode CBC

# 数据库表结构
"shua_orders" OR "pre_orders" table structure

# PHP 混淆模式
"GLOBALS[B000" OR "$GLOBALS[AAAAAA]" PHP obfuscation
```

### 3.3 绕过下载限制

```bash
# GitHub 被墙 → 检查是否间歇性恢复
python -c "import socket; s=socket.socket(); s.settimeout(5); print(s.connect_ex(('github.com',443)))"
# 返回 0 = 通，返回非 0 = 不通

# 替代方案
# 1. winget（Windows 包管理器）绕过 GitHub DNS
# 2. pip 使用阿里云镜像: pip install -i https://mirrors.aliyun.com/pypi/simple
# 3. scoop 的 bucket 也在 GitHub → 不通时手动下载 zip
# 4. curl 通过服务器中转（如果服务器能通）
ssh root@server "curl -L https://github.com/xxx/releases/download/v1.0/tool.zip" > tool.zip
```

---

## 四、实战检查清单

### 拿到多检材时：

```
□ 列出所有检材中出现的 IP 地址 → 交叉匹配
□ 列出所有检材中的用户名/ID → 交叉匹配
□ 搜索所有检材中的相同密码前缀/模式
□ 追踪每个 "备份/上传/同步" 操作的目标
□ 对每个聊天 App → 找出前半段和后半段在哪
□ 对每个浏览器 → 确认搜索和下载是同一个还是不同浏览器
□ 对比各检材的操作时间线 → 验证事件关联性
□ 服务器上的不完整文件 → 在计算机镜像中找完整版
```

---

## 五、比赛复盘——我们错在哪里

| 场景 | 错误 | 正确做法 |
|------|------|---------|
| 服务器 /opt/faka.sql 无订单数据 | 以为这就是全部 | 追 autobackup.sh → 在计算机找完整版 |
| 后台路径 | 看了 /fk/admin/ 就交卷 | 统计两个入口的访问量再决定 |
| 管理员密码 | 用旧备份的 wy0719 | 用真实 DB 的 SHA256(明文+2025baofu!) 解密 |
| 支付接口 | "alipay_api" = 支付宝 | payapi=13 → 无忧支付（需解密 set.php） |
| Steghide 提取 | 没意识到 payload.out 里有截断 ZIP | 尝试恢复截断 ZIP 拿到重点客户名单 |
| 浏览器 | 搜 steghide 的土狗浏览器 | 百度网盘下载用的是鲁班浏览器 |
