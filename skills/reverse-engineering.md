# Reverse Engineering Skill — CTF

## 适用场景
二进制逆向、恶意软件分析、固件分析、脱壳、符号执行、反汇编。

## 工具清单

| 工具 | 用途 | 路径 |
|------|------|------|
| `radare2` / `r2` | 反汇编/调试/分析 | `E:\CompetitionTools\scoop\shims\r2.exe` |
| `rabin2` | 二进制信息提取 | `E:\CompetitionTools\scoop\shims\rabin2.exe` |
| `rahash2` | 哈希计算 | `E:\CompetitionTools\scoop\shims\rahash2.exe` |
| `rasm2` | 汇编/反汇编 | `E:\CompetitionTools\scoop\shims\rasm2.exe` |
| `rax2` | 数值转换 | `E:\CompetitionTools\scoop\shims\rax2.exe` |
| `upx` | 脱壳 | `E:\CompetitionTools\scoop\shims\upx.exe` |
| `strings` | 字符串提取 | git-bash |
| `xxd` | 十六进制查看 | git-bash |
| `file` | 文件类型 | git-bash |
| `yara` | 模式匹配/规则扫描 | `E:\CompetitionTools\scoop\shims\yara.exe` |
| `python` | 脚本分析 | Python313 |

## 分析流程

### 第一步：初步侦察
```bash
# 文件类型
file binary
rabin2 -I binary       # 详细信息
rabin2 -z binary       # 字符串（含地址）
rabin2 -i binary       # 导入函数
rabin2 -E binary       # 导出函数
rabin2 -R binary       # 重定位
rabin2 -s binary       # 节信息

# 字符串提取（快速发现线索）
strings binary | rg -i "flag|ctf|correct|wrong|password|key|secret"
strings binary | rg -i "congratulations|success|you win"
strings binary | rg -i "/bin/sh|system|exec"

# 熵检查（是否有加壳/加密段）
rabin2 -e binary
```

### 第二步：反汇编分析 (radare2)

```bash
# 启动分析
r2 -A binary              # 自动分析

# === r2 内部常用命令 ===
# aaa     — 完整分析
# afl     — 列出所有函数
# s main  — 跳转到 main
# pdf     — 反汇编当前函数
# VV      — 进入可视化模式
# pdc     — 伪代码反编译
# iz      — 列出字符串（含地址）
# ii      — 列出导入
# ie      — 入口点
# axt <addr> — 交叉引用
# ood     — 重新打开为调试模式
# dc      — 继续执行（调试）
# dr=     — 显示寄存器
# db <addr> — 设置断点
# q       — 退出

# 一键分析脚本
r2 -A -q -c 'aaa; afl; iz; pdc @ main' binary
```

### 第三步：关键函数定位

```bash
# 查找 main 函数
r2 -A -q -c 's main; pdf' binary

# 查找比较函数（常见: strcmp, strncmp, memcmp）
r2 -A -q -c 'axt sym.imp.strcmp' binary
r2 -A -q -c 'axt sym.imp.strncmp' binary

# 查找"正确"输出附近的代码（从字符串地址交叉引用）
# 1. iz 找到 "Correct!" 地址
# 2. axt <addr> 找到引用该字符串的代码

# 批量反编译所有自定义函数（排除 libc 等）
r2 -A -q -c 'aaa; afl~[0]' binary | while read addr size name; do
  r2 -A -q -c "s $addr; pdc" binary
done
```

### 第四步：脱壳

```bash
# UPX 壳
upx -d packed.exe -o unpacked.exe
upx -t packed.exe         # 测试是否是 UPX

# 检查其他壳的签名
rabin2 -I binary | rg -i "packer|protector"

# 手动脱壳思路:
# 1. 找到 OEP (Original Entry Point)
# 2. 在 OEP 设断点
# 3. 运行到 OEP
# 4. 内存 dump
```

### 第五步：数据提取

```bash
# 提取嵌入数据段
rabin2 -O binary          # 列出可提取的节
rabin2 -x 0x1000 binary   # 提取特定节的十六进制

# 从特定偏移读取数据
r2 -q -c "px 256 @ 0x402000" binary   # 256字节 hex dump
r2 -q -c "p8 256 @ 0x402000" binary   # 256字节 raw bytes

# 搜索模式
r2 -q -c "/ flag{" binary             # 搜索字符串 "flag{"
r2 -q -c "/x 7b000000" binary         # 搜索 hex 模式
```

### 第六步：YARA 规则扫描

```bash
# 编写规则文件 scan.yar
cat > scan.yar << 'EOF'
rule suspicious_strings {
    strings:
        $s1 = "flag{"
        $s2 = "password" nocase
        $s3 = "/bin/sh"
        $s4 = { 89 E5 83 EC }        // x86 function prologue
    condition:
        any of them
}
EOF

# 扫描
yara scan.yar binary
yara -s scan.yar binary     # 显示匹配字符串
```

### 第七步：常见 CTF RE 题型

#### 简单比较
```bash
# Flag 明文存储在字符串中
strings binary | rg "flag{"

# 简单 XOR 加密的 Flag
# 找 XOR 循环 → 提取 key 和数据 → 解密

# 逐字符比较 → 可以用 angr 或手动追踪
```

#### 算法逆向
```bash
# 自定义加密算法 → 识别算法结构（Feistel, S-box 等）
# 写逆运算 Python 脚本

# TEA/XTEA/RC4 → 找 magic constant
# TEA: 0x9E3779B9
# MD5: 初始化常量
```

#### VM 逆向
```bash
# 自定义 VM
# 1. 识别 opcode 表
# 2. 反汇编 VM bytecode
# 3. 追踪执行流
# 4. 提取 flag 检查逻辑
```

### 数值转换工具 (rax2)
```bash
rax2 0x41414141       # hex → int
rax2 -k 65            # int → hex
rax2 -s 0x41 0x41 0x41 0x41  # hex → string
rax2 -S AAAA          # string → hex
rax2 -b 01100001      # binary → int
```

### 汇编/反汇编 (rasm2)
```bash
rasm2 -a x86 -b 64 "mov eax, 1"
rasm2 -a x86 -b 64 -d "b801000000"
rasm2 -a x86 -b 64 -L   # 列出所有汇编程序
```

## 提示
- **先 `strings`** — 40% 的 RE 题 flag 就在明文字符串中
- **`rabin2 -z` 看地址** — 比 `strings` 多了地址信息
- **XOR 是最常见的混淆** — 找异或循环和 key
- **`axt` 交叉引用** — 从关键字符串反查代码逻辑
- **多注意 `strcmp` 调用前后的数据操作** — 通常是对输入的变换
