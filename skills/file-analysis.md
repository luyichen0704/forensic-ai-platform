# File Analysis Skill — CTF / Forensics

## 适用场景
未知文件识别、文件类型伪造检测、损坏文件修复、隐藏数据提取、磁盘镜像文件分析。

## 工具清单（已安装）

| 工具 | 用途 | 路径 |
|------|------|------|
| `file` (git-bash) | 文件类型识别 | `C:\Program Files\Git\usr\bin\file.exe` |
| `strings` (git-bash) | 提取可打印字符串 | `C:\Program Files\Git\usr\bin\strings.exe` |
| `xxd` (git-bash) | 十六进制查看/转换 | `C:\Program Files\Git\usr\bin\xxd.exe` |
| `exiftool` | 元数据提取 | `E:\CompetitionTools\scoop\shims\exiftool.exe` |
| `binwalk` | 固件/文件嵌套分析 | Python Scripts |
| `7z` | 解压/提取多种格式 | `E:\CompetitionTools\scoop\shims\7z.exe` |
| `rg` | 文件内容搜索 | `E:\CompetitionTools\scoop\shims\rg.exe` |
| `fd` | 文件查找 | `E:\CompetitionTools\scoop\shims\fd.exe` |
| `imagemagick` | 图片属性/转换 | scooped |
| `sqlite3` | SQLite 数据库分析 | `E:\CompetitionTools\scoop\shims\sqlite3.exe` |
| `openssl` | 解密/哈希计算 | scooped |
| `olevba` | Office 文档宏分析 | `pip` (oletools) |
| `auto_scanner.py` | 一键自动扫描 | `E:\CompetitionTools\scripts\auto_scanner.py` |

## 分析流程

### 第一步：基础识别
```bash
# 1. 文件类型和大小
file unknown.bin
exiftool unknown.bin

# 2. 查看十六进制头部（检查 magic bytes）
xxd unknown.bin | head -20
xxd -l 256 unknown.bin

# 3. 计算哈希
md5sum unknown.bin; sha1sum unknown.bin; sha256sum unknown.bin

# 4. 字符串提取
strings unknown.bin | head -100
strings -n 6 unknown.bin    # 最小长度 6
strings -e l unknown.bin    # UTF-16 LE (Windows)
```

### 第二步：嵌套结构分析
```bash
# 检查是否包含其他文件
binwalk unknown.bin
binwalk -e unknown.bin      # 自动提取嵌套文件
binwalk -Me unknown.bin     # 递归提取

# 检查压缩/归档
7z l unknown.bin            # 列出内容
7z x unknown.bin -oout/     # 提取到 out/
```

### 第三步：常见文件格式检查

#### 图片文件
```bash
# JPEG: 检查 EXIF, 缩略图, 量化表
exiftool -a -u -g1 image.jpg
exiftool -b -ThumbnailImage image.jpg > thumb.jpg

# PNG: 检查 chunk 结构
pngcheck -v image.png
# 检查 IDAT 之后是否有隐藏数据
binwalk image.png

# 修复损坏的图片头
magick identify -verbose image.png
```

#### 压缩包
```bash
# ZIP: 检查加密/伪加密
7z l -slt archive.zip
zipinfo archive.zip

# RAR/7z 密码尝试
7z t archive.rar            # 测试完整性
```

#### PDF / Office 文档
```bash
# 提取嵌入对象
binwalk -e document.pdf
7z x document.docx -oout/

# 搜索隐藏文本
rg -i "flag|ctf|password|key" document.pdf
```

#### 磁盘镜像 / 固件
```bash
# 识别文件系统
mmls disk.img
fsstat -o <offset> disk.img

# 提取文件
fls -o <offset> -r disk.img
icat -o <offset> disk.img <inode> > extracted
```

### 第四步：自动化批量分析
```bash
# 批量 exiftool
exiftool -r -csv ./case_files/ > metadata.csv

# 批量文件类型统计
fd -t f . ./cases/ -x file {} \; > file_types.txt
```

## 常见 Flag 藏匿方式

1. **文件末尾追加**: `cat original.jpg flag.txt > fake.jpg`
   → `strings fake.jpg | tail -20`

2. **EXIF 字段**: 藏在 Comment / Artist / Copyright 字段
   → `exiftool -a image.jpg | rg -i "flag|ctf"`

3. **文件嵌套**: 图片里藏 zip
   → `binwalk -e image.jpg && cd _image.jpg.extracted/`

4. **隐写到 LSB**: LSB 隐写 → 见 stego skill

5. **伪造扩展名**: .docx 实际是 .zip
   → `file fake.docx` 检查真实类型

6. **Base64/Hex 编码**: 字符串中的编码 flag
   → `strings unknown.bin | rg "[A-Za-z0-9+/=]{20,}"`

7. **NTFS 备用数据流 (ADS)**
   → `dir /R` 查看 ADS, `more < file.txt:streamname`

## 提示
- **先 `file` 后 `binwalk`**，避免误判
- **不要直接运行未知可执行文件**，在沙箱中分析
- **记录每个步骤的哈希**，确保证据链完整性
- **优先 `strings` 快速扫描**，再进入深度分析
