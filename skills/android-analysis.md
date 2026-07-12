# Android Analysis Skill — CTF / Forensics

## 适用场景
APK 逆向、Android 取证、恶意 APP 分析、Native Library 分析、AndroidManifest 审查。

## 工具清单

| 工具 | 用途 | 路径 |
|------|------|------|
| `jadx` | APK → Java 反编译 | `E:\CompetitionTools\scoop\shims\jadx.cmd` |
| `jadx-gui` | 图形化反编译 | `E:\CompetitionTools\scoop\shims\jadx-gui.cmd` |
| `adb` | 设备调试 | `E:\CompetitionTools\scoop\shims\adb.exe` |
| `apktool-e` | APK 解包/重打包 | `E:\CompetitionTools\bin\apktool-e.bat` → `D:\apktools\apktool.bat` |
| `radare2` / `r2` | Native .so 逆向 | scooped |
| `strings` | 字符串提取 | git-bash |
| `rg` | 内容搜索 | scooped |
| `7z` | APK 解压 (ZIP格式) | scooped |
| `sqlite3` | 本地数据库分析 | scooped |
| `openssl` | 证书/签名分析 | scooped |

## Java 环境设置
```powershell
# jadx 需要 JDK 11+
$env:JAVA_HOME = 'E:\CompetitionTools\scoop\apps\openjdk\current'
```

## 分析流程

### 第一步：APK 解包
```bash
# APK 本质是 ZIP
7z x app.apk -oapk_extracted/
cd apk_extracted/

# 关键文件
ls -la
# AndroidManifest.xml  — 权限/组件声明
# classes.dex          — Java 字节码
# lib/                 — Native .so 库
# res/                 — 资源文件
# assets/              — 资产文件
# META-INF/            — 签名信息
```

### 第二步：快速字符串扫描
```bash
strings app.apk | rg -i "flag|ctf|password|secret|key|api"
strings app.apk | rg -i "http://|https://"
strings app.apk | rg -i "SELECT|INSERT|DELETE|DROP"
strings app.apk | rg -i "AES|DES|RSA|MD5|SHA|Base64"
strings app.apk | rg -i "/data/|/system/|/sdcard/"
strings app.apk | rg "flag\{.*\}"
```

### 第三步：jadx 反编译
```bash
# 命令行反编译到目录
jadx -d output_dir/ app.apk
jadx --no-res -d source_only/ app.apk

# 反编译完成后搜索
rg -r "flag" output_dir/
rg -r "password|secret|key" output_dir/
rg -r "http://|https://" output_dir/sources/
```

### 第四步：关键检查点

#### AndroidManifest.xml 审查
```
# 重点查看:
- package name（包名）
- permissions（权限）
- exported components（可导出组件）
- intent filters
- debuggable flag（可调试标志）
- backup flag（备份标志）
```

#### Java 代码分析（jadx 输出）
```bash
# 搜索加密/解密函数
rg -n "Cipher|encrypt|decrypt|AES|DES|RSA" output_dir/sources/

# 搜索网络请求
rg -n "HttpURLConnection|OkHttp|Retrofit|URL|Socket" output_dir/sources/

# 搜索 Native 方法调用
rg -n "System\.loadLibrary|native " output_dir/sources/

# 搜索数据库操作
rg -n "SQLiteDatabase|Room|Realm|SharedPreferences" output_dir/sources/

# 搜索反射
rg -n "Class\.forName|Method\.invoke|dexClassLoader" output_dir/sources/

# 搜索 WebView
rg -n "WebView|loadUrl|addJavascriptInterface" output_dir/sources/
```

### 第五步：Native Library (.so) 分析
```bash
# 列出所有 .so
fd "\.so$" apk_extracted/lib/

# 对每个 .so 进行基础分析
for lib in apk_extracted/lib/**/*.so; do
  echo "=== $lib ==="
  rabin2 -I "$lib"
  strings "$lib" | rg -i "flag|ctf|key|secret|native"
done

# 如果有 JNI 函数（命名规则: Java_com_example_MainActivity_xxx）
rabin2 -E apk_extracted/lib/arm64-v8a/libnative.so | rg "Java_"

# 反汇编特定 JNI 函数
r2 -A -q -c "s sym.Java_com_example_MainActivity_checkFlag; pdf" libnative.so
```

### 第六步：资源文件检查
```bash
# assets 目录（常藏 flag）
fd . apk_extracted/assets/ -t f

# 检查图片元数据
exiftool apk_extracted/res/drawable/*.png apk_extracted/res/drawable/*.jpg

# 检查 raw 资源
fd . apk_extracted/res/raw/ -t f

# 检查字符串资源
rg "flag|ctf" apk_extracted/res/values/strings.xml
```

### 第七步：动态分析（可选，需模拟器）
```bash
# 安装 APK
adb install app.apk

# 查看日志（flag 可能输出到 logcat）
adb logcat | rg -i "flag|ctf"

# 查看应用数据
adb shell run-as com.example.app ls /data/data/com.example.app/
adb shell run-as com.example.app cat /data/data/com.example.app/shared_prefs/*.xml

# 提取应用数据库
adb shell run-as com.example.app cp /data/data/com.example.app/databases/app.db /sdcard/
adb pull /sdcard/app.db .
sqlite3 app.db .dump
```

### 第八步：证书/签名分析
```bash
# 查看签名信息
openssl pkcs7 -inform DER -in META-INF/CERT.RSA -noout -print_certs -text
openssl pkcs7 -inform DER -in META-INF/CERT.RSA -print_certs -text | rg -i "issuer|subject|not after|not before"

# 提取证书
7z x META-INF/CERT.RSA
```

### 第九步：常见 CTF Android 题型

#### 1. 简单 Flag 隐藏
```
- strings 直接找到（assets/strings.xml/代码中）
- Base64 编码在代码中
- 资源文件中（图片、音频、自定义文件）
```

#### 2. Native 加密验证
```
- Java 调用 Native checkFlag() → 逆向 .so
- JNI_OnLoad 中动态注册 → 找 RegisterNatives 调用
- Native 函数中有 XOR/AES 解密逻辑
```

#### 3. 网络通信类
```
- 找到 URL/API endpoint
- 分析请求参数和响应处理
- 复现请求获取 flag
```

#### 4. SQLite 数据库类
```
- 数据库文件在 assets/ 中
- sqlite3 打开分析
- 可能有加密数据库（找密码）
```

#### 5. 加固/加壳
```
- 检查 Application 类是否被替换
- lib/ 中的 .so 可能是壳
- 检查是否有多个 dex 文件
```

## 快速检查脚本
```bash
#!/bin/bash
APK="$1"
echo "=== STRINGS ===" && strings "$APK" | rg -i "flag|ctf|secret|password|key"
echo "=== META ===" && 7z l "$APK" | rg -i "META-INF|lib/|assets/"
echo "=== PERMISSIONS ===" && 7z x -so "$APK" AndroidManifest.xml 2>/dev/null | strings | rg "permission|exported"
echo "=== NATIVE LIBS ===" && 7z l "$APK" | rg "\.so$"
```

## 提示
- **APK = ZIP**，先 `7z x` 解包再看内容
- **先用 jadx-gui 图形化浏览**，再命令行批量搜索
- **strings 扫整个 APK** 比单独分析代码更快找到 flag
- **注意 ProGuard 混淆后的类名**：a.b.c.d → 需要耐心分析
- **检查 `assets/` 和 `res/raw/`**，flag 常藏在这些地方

---

## APK 加密 + 壳 深度分析 (2026 盘古石杯)

### SQLCipher 密钥派生
```java
// PBKDF2WithHmacSHA256 + 三段盐值拼接 + 10000 迭代
PBKDF2_ITERATIONS = 10000;
KEY_LENGTH = 256;
salt = getSaltPart1() + getSaltPart2() + getSaltPart3();
// "Pr3d1ct0r" + "v2.0_S@lt" + "X9kZ!qW3"
```
配置文件藏密码: `shared_prefs/*.xml → flutter.db_password`

### 壳脱壳
```bash
# 密钥分 3 段混淆:
#   Base64("U2gzbGxf") = Sh3ll_
#   XOR(0x5D217075634E5A, 17) = L0ad3r_K  
#   reverse("!4202_y3") = 3y_2024!
# → 完整密钥: Sh3ll_L0ad3r_K3y_2024!
```

### 反调试检测
```
Frida:   扫描 127.0.0.1:27042 (Frida 默认端口)
Xposed:  检测 de.robv.android.xposed.XposedBridge 类
脱壳:    检测到附加 → java.lang.System.exit(0)
Hook:    initDexFromMemory() — 内存加载 DEX 字节数组
```

### Flutter 应用
```
特征: libflutter.so, flutter_assets/
配置: shared_prefs/*.xml → flutter.db_password / auth_token / user_id
数据库: SQLCipher 加密, 密码从 shared_prefs 提取
```

---

## 鸿蒙APP逆向 + 魔改XOR (2026平航杯)

### 鸿蒙HAP包解析
```bash
# .app → 改.zip解压 → .hap (鸿蒙包)
# modules.abc → abc-decompiler 反编译 → AuthPage 类
# libcrypto.so → IDA分析 → ROT16/自定义XOR
```

### 魔改XOR解密 (非标准XOR)
```python
# out[i] = in[i] ^ (key[i % klen] + (i % klen))
# 注意: key 用 password_hash (非明文密码)!
dec = bytes(b ^ ((key[i % len(key)] + (i % len(key))) & 0xff)
           for i, b in enumerate(data))
```

### Native SO 分析口诀
```
shift+F12 → 找导出函数名(q1/w1/z1)
w1 = 密码变换 (ROT16/MD5/自定义)
z1 = 验证函数 (明文→w1→与hash比较)
salt 是否参与校验 → 看w1/z1是否接收salt参数
```

---

## 手机取证数据源优先级 (盘古石2026实战教训)

### 第一步: packages.xml (秒级, 全覆盖)
```bash
# 优先读 /data/system/packages.xml — 列出所有安装应用
# 不要跳过这步直接猜哪个app是目标!
# 每个 <package> 有: name, version, versionCode, firstInstallTime
```

### 第二步: 根据题目关键词定位app
```
短视频 → 搜索包名含 aweme/gifmaker/kuaishou/bili
龙虾   → 搜 "龙虾" → 但不要假设它做所有事!
控制PC → 搜包名含 discord/teamviewer/anydesk/remote/agent
通联工具 → 搜 social/im/chat/message
理财   → 搜 okex/binance/wallet/finance/eastmoney
```

### 第三步: 依次检查每个app的数据目录
```
优先级:
  1. shared_prefs/*.xml         ← 用户名/密码/配置/首次打开时间
  2. databases/*.db              ← 结构化数据
  3. files/kv-storage/           ← Discord 专用! (不是databases/)
  4. files/*.json/*.log          ← 应用日志
  5. app_flutter/               ← Flutter 应用的加密数据库
```

## Discord C2 取证 (盘古石2026)
```
Discord 用来做 C2 (命令与控制) 很常见!
数据路径: /data/data/com.discord/files/kv-storage/
           @account.<id>/a/message0.db

关键字段:
  - 用户名/登录名: message0 表的 user 字段
  - 配对码: YAML session 记录中的 "pairing code"
  - 攻击命令: 消息内容中的 nmap/scan/hydra
  - IP 列表: 从命令中提取 "扫描192.168.x.x"

从 session 记录可以重建完整攻击时间线!
```

## SocialChat 通联工具取证
```
数据路径: /data/data/com.socialchat.social_chat_app/databases/social_chat.db
加密方式: AES-256-CBC (不是SQLCipher!)
密钥来源: user 表的 config_data JSON → base64(enc_key) + base64(enc_iv)
解密后:
  - conversation 表 → 会话列表 (含军师id)
  - message 表 → 加密消息
  - 发送文件数 → 解密后统计 content-type=105 的消息
```
