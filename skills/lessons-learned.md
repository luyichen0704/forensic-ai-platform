# PHP 混淆解密 + 数据库恢复 + 日志统计 Skill

## 一、PHP 混淆解密（白猿网络加密）

比赛中的 `set.php` 被严重混淆，核心支付配置 `payapi=13 → 无忧支付` 被隐藏。

### 识别特征
```php
$GLOBALS[B000B0000]=explode("|(|;|+", "H*|(|;|+4242424242304230");
$GLOBALS[B0000BBB0]=explode("|}|@|h", "H*|}|@|h4242424242304242|}|@|h7374726C656E...");
```

### 解密思路
1. 提取 3 个 GLOBALS 数组的 hex 数据
2. `pack("H*", hex_string)` 解码为可读字符串
3. 递归替换 `$GLOBALS[KEY][IDX]` 引用
4. 处理中间变量链：`$U4jcV1 → $U4jcVvP1 → pack(...)`

### 实战脚本框架
```python
import re

# 1. 提取 GLOBALS 数组
m = re.search(r'explode\("([^"]+)",\s*"([^"]+)"\)', content)
sep, raw = m.group(1), m.group(2)
arr = raw.split(sep)

# 2. hex 解码
decoded = [bytes.fromhex(x).decode('utf-8', errors='replace') if x != 'H*' else 'H*' for x in arr]

# 3. 替换 GLOBALS 引用
content = re.sub(r'\$GLOBALS\[KEY\]\[(\d+)\]', lambda m: f"'{decoded[int(m.group(1))]}'", content)

# 4. 处理 pack("H*", ...) 
content = re.sub(r"""pack\('H\*',\s*'([0-9a-fA-F]+)'\)""", 
    lambda m: f"'{bytes.fromhex(m.group(1)).decode()}'", content)
```

---

## 二、日志统计决定正确答案

### 问题：两个后台入口，哪个是真实用的？

```bash
# 统计访问量——数据说话！
zcat -f /var/log/nginx/access.log* | \
  awk '$7 ~ /\/fk\/(static|admin)\/login\.php/ {cnt[$7]++} END {for (p in cnt) print cnt[p], p}' | \
  sort -rn

# 输出:
# 33 /fk/static/login.php    ← 胜出
#  7 /fk/admin/login.php
```

### 分析 IP 访问频次
```bash
zcat -f /var/log/nginx/access.log* | \
  awk '$7 ~ /\/fk\/(static|admin)\/login\.php/ {cnt[$1]++} END {for (ip in cnt) print cnt[ip], ip}' | \
  sort -rn | head -5
```

---

## 三、数据库备份文件——服务器 vs 计算机

### 经典坑点
```
服务器 /opt/faka.sql      ← SHA256 = 1C6B88（旧备份，无订单数据）
服务器 /tmp/db_backup/*   ← 全是空压缩包
计算机 检材2 中的 sql 文件 ← SHA256 = FF8180（完整备份！含订单数据）
```

### 为什么数据库在计算机上？
**autobackup.sh 的逆推**：
```bash
cat /etc/cron.daily/autobackup.sh
# DB_USER="root"  DB_PASSWORD="Root@123456"
# REMOTE_SERVER="8.208.44.202"  ← 上传到境外
# mysqldump -h 127.0.0.1 fk | gzip > /tmp/db_backup/fk_xxx.sql.gz
# scp ... root@8.208.44.202:/root/
```

实际流程：
1. 服务器每天备份 → scp 到 8.208.44.202
2. 嫌疑人从 8.208.44.202 **下载到自己的 Windows 电脑**（检材2）
3. 比赛时检材2 的完整 sql 备份被火眼导出

### 教训
> **服务器上的备份不一定是完整的**。要追查备份脚本的目标路径，在计算机镜像中找同步下来的完整版本。

---

## 四、Steghide 密码爆破

### 场景
有 `important.jpg` 和 `常用密码.txt`，已知用了 steghide。

### 批量爆破脚本
```python
import subprocess, os

steghide = r"steghide.exe"
image = r"important.jpg"
wordlist = r"常用密码.txt"
output_dir = r"./output"
output_file = os.path.join(output_dir, "extracted.txt")
os.makedirs(output_dir, exist_ok=True)

with open(wordlist, "r", encoding="utf-8") as f:
    passwords = [line.strip() for line in f if line.strip()]

for i, passwd in enumerate(passwords):
    print(f"\r{i+1}/{len(passwords)}", end="", flush=True)
    try:
        result = subprocess.run(
            [steghide, "extract", "-sf", image, "-p", passwd, "-f", "-xf", output_file],
            capture_output=True, timeout=10
        )
        if result.returncode == 0:
            print(f"\n✅ FOUND: {passwd}")
            break
    except subprocess.TimeoutExpired:
        continue
```

---

## 五、截断 ZIP 文件恢复

### 场景
Steghide 提取出的 `payload.out` 是一个被截断的 ZIP（外层 ZIP 数据流尾部损坏）。

### 恢复思路
1. 搜索 ZIP 文件头 `PK\x03\x04`
2. 逐项解压 deflate 压缩的内部文件
3. 重点关注 `xl/worksheets/sheet1.xml` 和 `xl/sharedStrings.xml`
4. 用正则提取 XML 中的行数据和共享字符串

### 实战代码
```python
import struct, zlib, re

data = open('payload.out', 'rb').read()
idx = data.find(b'PK\x03\x04')
inner = data[idx:]

# 解压外层 deflate
nlen = struct.unpack_from('<H', inner, 26)[0]
elen = struct.unpack_from('<H', inner, 28)[0]
d = zlib.decompressobj(-15)
xlsx_data = d.decompress(inner[30+nlen+elen:], max_length=50000)

# 遍历内层 ZIP，提取 sharedStrings 和 sheet1
off = 0
while off < len(xlsx_data) - 4:
    if xlsx_data[off:off+4] != b'PK\x03\x04':
        off += 1; continue
    nlen = struct.unpack_from('<H', xlsx_data, off+26)[0]
    elen = struct.unpack_from('<H', xlsx_data, off+28)[0]
    name = xlsx_data[off+30:off+30+nlen].decode('utf-8')
    csize = struct.unpack_from('<I', xlsx_data, off+18)[0]
    method = struct.unpack_from('<H', xlsx_data, off+8)[0]
    dstart = off + 30 + nlen + elen
    raw = xlsx_data[dstart:dstart+csize]
    xml = (zlib.decompress(raw, -15) if method == 8 else raw).decode('utf-8')
    
    if 'sharedStrings' in name:
        strings = re.findall(r'<t[^>]*>([^<]+)</t>', xml)
    elif 'sheet1' in name:
        rows = re.findall(r'<row[^>]*>(.*?)</row>', xml, re.DOTALL)
    off = dstart + csize
```

---

## 六、SHA256 正确计算姿势

### 火眼坑点
> 火眼挂载的 E01 中，特定文件右键计算哈希会失败（"特定镜像触发火眼解密失败"）。

### 解决方案
```bash
# ❌ 不要在火眼挂载盘上右键 → 属性 → 哈希
# ✅ 仿真启动后，把文件 copy 到本地再算
copy X:\faka.sql D:\temp\
certutil -hashfile D:\temp\faka.sql SHA256
```

---

## 七、Administrator 权限绕过

### 场景
H: 盘挂载后 `Users\Administrator` 无读取权限。

### 方案
```bash
# 用 TSK 直接读 E01——绕过 Windows ACL
mmls image.E01
fls -o <offset> image.E01 <Users_inode>      # 找到 Administrator inode
fls -o <offset> image.E01 <Admin_inode>      # 列出子目录
icat -o <offset> image.E01 <file_inode>      # 直接读取文件内容

# 删除文件也能通过 fls -d 发现
fls -o <offset> -d -r image.E01
```

---

## 八、结论——为什么别人能找到离线数据库

| 我们的做法 | 正确做法 |
|-----------|---------|
| 在服务器 `/opt/` 找 faka.sql | 追 autobackup.sh → 发现 scp 到 8.208.44.202 → 在**检材2 计算机**上找同步下来的完整副本 |
| 算了服务器上的 SHA256 | 计算机上完整备份的 SHA256 才是 FF8180 |
| 以为 DB 在 192.168.203.155 | 数据库曾被本地化/备份到嫌疑人电脑 |
| 只看了一个后台入口 | 统计两个入口的访问量后再决定 |
