# Steganography Skill — CTF / Forensics

## 适用场景
图片隐写、音频隐写、视频隐写、LSB 隐写、频域隐写、文本隐写、二维码/条形码。

## 工具清单

| 工具 | 用途 | 路径 |
|------|------|------|
| `exiftool` | 元数据提取 | scooped |
| `binwalk` | 嵌套文件提取 | Python Scripts |
| `imagemagick` | 图片处理/通道分离 | scooped |
| `ffmpeg` | 音视频处理 | scooped |
| `zsteg` | PNG/BMP LSB 检测 | `E:\CompetitionTools\scoop\apps\ruby\current\bin\zsteg` |
| `stegoveritas` | 综合隐写分析框架 | `pip` (Python) |
| `stegseek` (待装) | steghide 密码爆破 | 手动编译 |
| `steghide` (待装) | JPEG/BMP/WAV 隐写提取 | 手动安装 |
| `strings` | 字符串提取 | git-bash |
| `7z` | 归档提取 | scooped |
| `rg` | 内容搜索 | scooped |
| `auto_scanner.py` | 一键自动扫描 | `E:\CompetitionTools\scripts\auto_scanner.py` |

## 分析流程

### 图片隐写检查清单

#### 1. 基础元数据
```bash
exiftool -a -u -g1 image.png
exiftool image.png | rg -i "flag|ctf|comment|artist|copyright|description"
```

#### 2. 字符串扫描
```bash
strings image.png | rg -i "flag|ctf|secret|password|key|{.*}"
strings -n 8 image.jpg
```

#### 3. LSB 隐写检测
```bash
# zsteg (PNG/BMP) — pip install zsteg
zsteg -a image.png
zsteg -a -v image.png       # 详细输出
zsteg image.png -E b1,r,lsb,xy  # 提取特定通道

# 手动 LSB 提取思路:
# magick 分离 RGB 通道 → 查看 LSB 平面 → 组装数据
magick image.png -channel R -separate r.png
magick image.png -channel G -separate g.png
magick image.png -channel B -separate b.png
```

#### 4. 嵌套文件
```bash
binwalk -e image.jpg
binwalk -Me image.png
7z x image.jpg -oextracted/
```

#### 5. steghide (JPEG/BMP/WAV)
```bash
# 提取（需密码）
steghide extract -sf image.jpg -p password

# 爆破密码 — stegseek
stegseek image.jpg /path/to/wordlist.txt
stegseek --crack image.jpg wordlist.txt result.out

# 检测是否含 steghide 数据
steghide info image.jpg
```

#### 6. 图片差异比较
```bash
# 两张相似图片找差异
magick compare img1.png img2.png diff.png
magick composite -compose difference img1.png img2.png diff.png

# 像素级差异
magick compare -metric AE img1.png img2.png null:
```

#### 7. 颜色通道分析
```bash
# 分离通道
magick image.png -separate channel_%d.png

# 提取特定颜色平面（如蓝色 LSB）
magick image.png -channel B -evaluate And 1 blue_lsb.png
magick blue_lsb.png -negate blue_lsb_inv.png

# 调整对比度查看隐藏信息
magick image.png -auto-level -equalize enhanced.png
```

#### 8. 二维码/条形码
```bash
# zbarimg (需手动安装)
zbarimg qrcode.png
zbarimg --raw qrcode.png

# 二维码修复
magick damaged_qr.png -threshold 50% -morphology Close Square fixed_qr.png
```

#### 9. PNG Chunk 分析
```bash
pngcheck -v image.png
pngcheck -c image.png     # 检查颜色类型

# 查看是否有异常 chunk（如 tEXt, zTXt 中的隐藏数据）
pngcheck -v image.png 2>&1 | rg "tEXt|zTXt|iTXt"
```

### 音频隐写

```bash
# 频谱分析 — 用 ffmpeg 转换后查看
ffmpeg -i audio.wav -lavfi showspectrumpic=s=1024x512 spectrogram.png

# 慢速/倒放
ffmpeg -i audio.wav -af "atempo=0.5" slow.wav
ffmpeg -i audio.wav -af "areverse" reversed.wav

# DTMF 音检测
# 使用 multimon-ng 或在线工具
```

### 视频隐写

```bash
# 逐帧提取
ffmpeg -i video.mp4 -vf "fps=1" frames/%04d.png

# 检查特定帧
ffmpeg -i video.mp4 -vf "select=eq(n\,100)" -vframes 1 frame_100.png

# 音频轨道提取
ffmpeg -i video.mp4 -vn audio_only.wav
```

### 文本/文档隐写

```bash
# 空白字符隐写（空格/制表符）
xxd document.txt | head -50

# Word 文档
7z x document.docx -oout/
rg -r "flag|ctf" out/

# PDF 隐藏对象
strings document.pdf | rg -i "flag|ctf"

# 零宽字符检测
rg $'\u200b|\u200c|\u200d|\uFEFF' document.txt
```

## 快速检查脚本模板
```bash
#!/bin/bash
FILE="$1"
echo "=== EXIF ===" && exiftool "$FILE" | rg -i "flag|ctf|comment"
echo "=== STRINGS ===" && strings "$FILE" | rg -i "flag|ctf|{.*}"
echo "=== BINWALK ===" && binwalk "$FILE"
echo "=== NESTED ===" && 7z l "$FILE" 2>/dev/null
```

## 提示
- **先 `strings` 后 `exiftool`**，这两步常能直接出 flag
- **检查文件大小异常**：原图 2MB 但尺寸很小 → 可能藏了东西
- **所有工具对同一个文件跑一遍**，不同工具发现不同层面的数据
- **LSB 不一定只在最低位**，可能在第 2、3 位也有

---

## 补充专题: ctf-skills 高级隐写技术 (2025-2026)

### 二进制边界隐写
```python
# 1 像素边框 = 二进制 → 顺时针: 上 → 右 → 下(逆) → 左(逆)
```

### 多层 PDF 隐写 (6 种技术)
1. `strings pdf \| grep hidden` — 隐藏注释
2. `%%EOF` 后追加数据 — GPG/加密
3. 链接注释中的 flag (URI `\{` `\}` 转义)
4. 模糊图片 → Wiener 反卷积
5. 压缩对象流 → `mutool clean -d` → 解压后 strings
6. PDF 元数据 (`pdfinfo` / `exiftool`)

### PDF 隐写完整 checklist
```bash
strings -a file.pdf | grep -o 'FLAG{.*}'
exiftool file.pdf
pdfimages -all file.pdf img && zsteg -a img-*.ppm
mutool clean -d file.pdf clean.pdf && strings clean.pdf
# 检查 FlateDecode 压缩流:
python -c "import re,zlib;d=open('f.pdf','rb').read()
[print(zlib.decompress(s)) for s in re.findall(b'stream...(.*?)...endstream',d,re.S)]"
```

### SVG 隐写
- 动画关键帧: `<animate>` + `keyTimes/values` 交替 = 二进制/Morse
- 微坐标: 450.xxxxx → `viewBox` 放大 1000 倍

### PNG 高级技巧
```bash
# PNG chunk 重排: IHDR → ancillary → IDAT → IEND
# APNG: acTL chunk = 多帧, apngdis 提取
# PNG 高度 CRC 爆破: 改小高度隐藏下方内容 → 穷举匹配 CRC
```

### GIF 帧差分 + Morse
```bash
convert anim.gif frame_%03d.gif
for f in frame_*.gif; do compare -fuzz 10% $f base.gif diff_$f; done
# diff 图中的点 = Morse 码
```

### 双层字节+行交错
```python
# 文件 = 偶数字节(PNG1) + 奇数字节(PNG2)
png1 = data[0::2]; png2 = data[1::2]
# 如果内容仍有条纹 → 行级再解交错
```

### 视频多流隐藏
```bash
ffprobe video.mp4  # 检查是否有 Stream #0:1
ffmpeg -i video.mp4 -map 0:1 -c copy second.mp4
```

### Angecryption (AES-CBC 加密生成有效文件)
```
AES-CBC 加密文件A → 密文恰好是有效文件B 的内容
→ 用AES解密B得到A (flag)
```

### QR 码修复
```bash
# 3 个 Finder Pattern (7x7) + Timing Pattern + Alignment Pattern
# 凭已知结构放置 ~50% 模块 → 回溯搜索剩余
# 分块 QR: 目录名 = base64(索引) → 排序 → 拼接
```

### 终端图像协议 Kitty
```
\x1b_G...;BASE64\x1b\\ → zlib → RGB → 恢复图片
```

### ANSI 终端艺术隐写
```python
# strip ANSI escape codes → 提取 ASCII flag 字符
clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', data)
```

### 立体图 (Magic Eye / Autostereogram)
```python
diff = abs(img[:, shift:] - img[:, :-shift])  # 相减 → flag 浮现
```

### 编码隐写
- **base65536**: CJK 字符墙 = 2字节/字符 → `pip install base65536`
- **IEEE 754**: 浮点数 → `struct.pack('>f', v)` = 4 ASCII 字节
- **BCD**: 每 nibble 1 位数字 → 2 位 ASCII
- **UTF-16 端序反转**: 日语乱码 → `.encode('utf-16-be').decode('utf-16-le')`

### 异语编程语言速查
| 语言 | 特征 |
|------|------|
| Brainfuck | `++++++++++[>+++++++>` |
| Whitespace | 只有空格/制表/换行 (或 S/T/L 替代) |
| Piet | PNG 彩色像素块 = 代码 |
| 自定义 BF 变体 | 主题词汇 (arch/linux/btw) 替代 BF 操作符 |
