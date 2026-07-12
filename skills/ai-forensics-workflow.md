# AI 辅助电子取证工作流 Skill

## 概述
来源: 小谢取证公众号 — Trae 助力电子数据取证系列 (6+ 篇文章)

核心思想: 用 AI IDE (Trae/ClaudeCode/Cursor) + MCP 插件实现半自动化取证。

## 适用场景

| 场景 | AI 工具 | MCP 插件 | 效果 |
|------|---------|----------|------|
| PCAP 流量分析 | Trae | wireshark-mcp | 自动识别攻击IP/被攻击IP/webshell文件名/密码 |
| APK 逆向 | Trae | jadx-mcp-server | 自动反编译并提取包名/入口点/敏感信息 |
| 网站取证 | Trae | 浏览器自动化 | 自动识别后台地址/登录绕过/数据库操作 |
| 二进制逆向 | Trae | idapromcp / r2-mcp | 自动分析函数逻辑 |
| 综合取证 | ClaudeCode | 全部 MCP | 多工具联动自动分析 |

## 流量分析 AI 工作流（已验证有效）

来源: 小谢取证"电子数据取证之使用Trae进行流量包解析"

### 已验证可自动回答的题型:

```
✅ SHA1 值 → AI 可自动计算
✅ 攻击/被攻击 IP → AI 通过统计 + TCP 握手自动识别
✅ 上传的木马文件名 → AI 通过 HTTP PUT/POST 自动发现
✅ webshell 连接密码 → AI 追踪 HTTP 流自动提取
✅ webshell 连接密钥 → AI 识别 AES 密钥
✅ 后门反连 IP:PORT → AI 追踪 TCP 流自动提取
✅ 黑客第一条命令 → AI 解密流量自动提取
⚠ 加解密相关 → 目前 AI 效果一般，需人工辅助
```

### AI 提示词模板:

```
你是一名电子数据取证专家。请分析以下 pcap 文件：
1. 计算文件的 SHA1 值
2. 识别攻击者和被攻击者的 IP 地址（通过统计分析和 TCP 握手）
3. 找出黑客上传的木马文件名（关注 HTTP PUT/POST 请求）
4. 找出 webshell 的连接密码
5. 追踪 TCP 流，找出黑客执行的第一条命令
6. 识别后门反连的 IP 和端口
7. 找出黑客新增的后门用户名和密码
```

## APK 逆向 AI 工作流

来源: 小谢取证"电子数据取证之使用Trae进行APP逆向分析"

### MCP 工具链:
```
jadx-mcp-server    → 反编译 APK
idapromcp          → Native .so 分析
frida-mcp          → 动态插桩
```

### AI 提示词模板:
```
请分析这个 APK 文件：
1. 包名和入口 Activity
2. 申请的权限列表（标记危险权限）
3. 可导出组件
4. 搜索代码中的 URL、IP 地址、邮箱
5. 搜索加密算法使用（AES/DES/RSA/MD5/Base64）
6. 查找硬编码的密钥、密码、API Key
7. 分析 Native .so 的导出函数
```

## 网站取证 AI 工作流

来源: 小谢取证"电子数据取证之使用Trae进行网站取证"

### 分析目标:
```
1. 识别 CMS/框架（WordPress/ThinkPHP/Laravel 等）
2. 找到后台登录地址
3. 分析登录逻辑（有无验证码绕过/SQL注入）
4. 数据库配置文件位置及密码
5. 是否留有后门文件
6. 最近被修改的文件
```

## Tool Mapping: AI ↔ 我们已有的 CLI 工具

小谢取证推荐的工具和我们已有工具的对应关系:

| 小谢推荐 | 我们已有 | 状态 |
|----------|---------|------|
| Wireshark MCP → tshark | ✅ `tshark` (scoop) | CLI 全覆盖 |
| jadx-mcp-server → jadx | ✅ `jadx` (scoop) | CLI 可用 |
| idapromcp → IDA | ⚠️ 替代: `r2` (scoop) | r2 CLI 全覆盖 |
| Trae/ClaudeCode | ✅ Reasonix (本工具) | 当下正在使用 |
| Volatility | ✅ `volatility3` (pip) | 全插件可用 |
| 宝塔面板分析 | ✅ `server-forensics.md` | 新 Skill |
| 国产 OS 取证 | ✅ 脚本待创建 | 下一步 |

## 实战: 用 Reasonix + CLI 实现 AI 取证

```
用户: 分析这个 pcap 文件，找出攻击信息和 webshell 密码

Reasonix 执行:
  1. capinfos capture.pcap                    → 文件信息
  2. tshark -r capture.pcap -q -z io,phs      → 协议统计
  3. tshark -r capture.pcap -q -z conv,ip     → IP 会话统计
  4. tshark -r capture.pcap -Y "http.request"  → HTTP 请求
  5. tshark -r capture.pcap -Y "http.request.method==PUT"
  6. tshark -r capture.pcap -q -z follow,tcp,ascii,N
  7. strings capture.pcap | rg "password|pass|key"
  
  汇总 → 输出攻击IP/被攻击IP/webshell文件名/密码/密钥/命令
```

## MCP 服务器配置建议

在 Reasonix 中可添加这些 MCP 服务器增强取证能力:

```bash
# wireshark/tshark MCP (需单独搭建)
add_mcp_server --name tshark --transport stdio --command tshark

# 文件系统 MCP (直接访问检材)
add_mcp_server --name filesystem --from_catalog filesystem --args E:\CompetitionTools\cases
```

## 比赛 AI 使用原则

```
✅ 适合 AI:  统计计算、模式匹配、批量转换、已知格式解析
⚠ 需验证:  复杂加密解密、自定义协议、深度逆向
❌ 不适合:  需要背景知识的逻辑推理、跨检材关联判断

黄金法则: AI 出结果 → 人工验证 → 确认后提交
```

## 参考资源

- 小谢取证公众号 (WeChat)
- Forensics-Wiki: https://www.forensics-wiki.com/
- XD Forensics Wiki: https://xdforensics-wiki.github.io/
- Wire MCP: GitHub 搜索 "wire mcp"
- jadx-mcp-server: GitHub 搜索 "jadx-mcp"
