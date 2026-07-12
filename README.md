# 基于大模型的自动化取证平台

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Gradio](https://img.shields.io/badge/Gradio-4.0+-orange.svg)](https://gradio.app/)

一个基于大语言模型(LLM)的智能电子取证分析平台，集成了自动化任务规划、知识库检索、多工具协同和插件扩展能力。

## 核心特性

### 🤖 智能分析引擎
- **多模型支持**: 集成OpenAI GPT-4、Claude、本地模型(Ollama)等多种大模型后端
- **智能任务规划**: 基于题目描述自动识别任务类型并生成分析步骤
- **知识库检索**: 向量化的技能知识库，支持语义搜索
- **工具调用系统**: 统一的工具注册、执行和输出解析

### 🔍 取证能力覆盖
- 磁盘取证 (E01/RAW/DD镜像分析)
- 网络流量分析 (PCAP/PCAPNG)
- 内存取证 (Volatility3)
- Android分析 (APK逆向)
- 密码学分析 (RSA/AES/哈希破解)
- 隐写分析 (图片/音频/视频)
- 逆向工程 (PE/ELF二进制)
- 服务器取证 (Web/数据库/日志)

### 🎯 自动化工作流
- **一键分析**: 输入题目描述和证据路径，自动执行完整分析流程
- **工具链编排**: 智能调度20+取证工具
- **证据链关联**: 多检材证据自动关联分析
- **报告生成**: 自动生成Markdown/HTML格式分析报告

### 🔌 插件系统
- **动态加载**: 支持运行时加载/卸载插件
- **钩子系统**: pre_analysis/post_analysis钩子
- **示例插件**: YARA扫描器、报告生成器

### 📚 案例库
- **100+取证案例**: 涵盖美亚杯、FIC、数证杯、盘古石等主流比赛
- **智能检索**: 按类别、比赛、年份、工具等多维度检索
- **训练数据导出**: 支持导出为JSONL格式用于模型训练
- **持续更新**: 支持从GitHub等来源持续收集新案例

---

## 项目结构

```
forensic-ai-platform/
├── agent/                          # AI核心引擎
│   ├── __init__.py
│   ├── core.py                    # Agent主循环
│   ├── llm.py                     # LLM封装
│   ├── knowledge_base.py          # 知识库管理
│   ├── tools/                     # 工具系统
│   │   ├── registry.py            # 工具注册表 (20+工具)
│   │   └── executor.py            # 工具执行器
│   └── parsers/                   # 输出解析器
│       └── output_parser.py       # 解析tshark/sleuthkit/volatility输出
├── web/                           # Web UI界面
│   └── app.py                    # Gradio取证专用界面
├── api/                           # RESTful API
│   └── main.py                   # FastAPI服务
├── plugins/                       # 插件系统
│   ├── manager.py                # 插件管理器
│   └── examples/                 # 示例插件
│       ├── yara_scanner/         # YARA规则扫描器
│       └── report_generator/     # 自动报告生成器
├── skills/                        # 取证技能库 (15个技能文档)
│   ├── disk-forensics.md
│   ├── network-forensics.md
│   ├── memory-forensics.md
│   ├── android-analysis.md
│   ├── crypto.md
│   ├── stego.md
│   ├── reverse-engineering.md
│   └── ...
├── cases/                          # 案例库
│   ├── raw/                       # 原始案例数据
│   ├── processed/                 # 处理后的案例
│   ├── index/                     # 案例索引
│   └── github/                    # GitHub收集的案例
├── scripts/                       # 工具脚本
│   ├── smart_hunter.py           # 智能搜索引擎
│   ├── evidence_linker.py        # 证据链关联
│   ├── extract_cases.py          # 案例提取器
│   └── ...
├── config/                        # 配置文件
│   ├── llm_config.json           # LLM配置
│   └── llm_config.example.json   # 配置模板
├── install.bat                    # 一键安装脚本
├── start.bat                      # 启动脚本
├── requirements.txt               # Python依赖
├── README.md
└── LICENSE
```

---

## 快速开始

### 1. 一键安装

```bash
# 克隆仓库
git clone https://github.com/luyichen0704/forensic-ai-platform.git
cd forensic-ai-platform

# 一键安装所有取证工具 (Windows)
install.bat
```

### 2. 配置API密钥

编辑 `config/llm_config.json`:

```json
{
  "provider": "openai",
  "api_key": "your-api-key-here",
  "model": "gpt-4",
  "base_url": "https://api.openai.com/v1"
}
```

支持的LLM提供者:
- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Claude**: claude-3-sonnet, claude-3-opus
- **Ollama**: llama2, mistral, qwen 等本地模型

### 3. 启动平台

```bash
# 方式1: 启动Web UI (推荐)
start.bat
# 选择选项 [1]

# 方式2: 命令行启动
python -m web.app          # Web UI (端口7860)
python -m api.main         # API服务 (端口8000)
```

### 4. 访问界面

- **Web UI**: http://localhost:7860
- **API文档**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 功能详解

### 🤖 AI取证助手

在聊天界面中描述你的取证任务，AI会自动:
1. 识别证据类型
2. 生成分析计划
3. 执行取证工具
4. 解析工具输出
5. 总结分析结果

**示例对话:**
```
用户: 分析E01磁盘镜像，找出删除的文件

AI: 我将为您分析E01磁盘镜像，查找已删除的文件。

分析计划:
1. 获取镜像基本信息
2. 分析分区结构
3. 扫描已删除文件
4. 恢复文件内容

正在执行分析...
```

### 🛠️ 工具管理

支持20+取证工具的统一管理:

| 类别 | 工具 | 用途 |
|------|------|------|
| 磁盘取证 | sleuthkit, autopsy | E01/RAW镜像分析 |
| 网络分析 | tshark, wireshark | PCAP流量分析 |
| 内存取证 | volatility3 | 内存转储分析 |
| Android | jadx, apktool | APK逆向分析 |
| 密码学 | hashcat, john | 密码破解 |
| 隐写 | steghide, zsteg | 隐写检测 |
| 逆向 | radare2 | 二进制分析 |

### 📚 知识库

内置15个取证技能文档，涵盖:
- 文件分析、磁盘取证、网络流量
- 内存取证、Android分析、密码学
- 隐写分析、逆向工程、服务器取证

支持语义搜索，快速找到相关技能。

### 🔌 插件系统

支持自定义插件扩展平台功能:

```python
from plugins.manager import ForensicPlugin, PluginMeta

class MyPlugin(ForensicPlugin):
    def get_meta(self) -> PluginMeta:
        return PluginMeta(
            name="my-plugin",
            version="1.0.0",
            description="我的自定义插件",
            author="Your Name",
            hooks=["pre_analysis", "post_analysis"]
        )
    
    def initialize(self, agent) -> bool:
        self.agent = agent
        return True
    
    def execute(self, **kwargs):
        # 插件逻辑
        return {"result": "success"}
```

---

## API接口

### 聊天接口

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "分析这个PCAP文件", "evidence_path": "capture.pcap"}'
```

### 分析任务

```bash
# 提交分析任务
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"evidence_path": "evidence.E01", "question": "找出删除的文件"}'

# 查询任务状态
curl "http://localhost:8000/api/tasks/{task_id}"
```

### 工具管理

```bash
# 获取工具列表
curl "http://localhost:8000/api/tools"

# 执行工具
curl -X POST "http://localhost:8000/api/tools/tshark/execute?evidence_path=capture.pcap"
```

### 插件管理

```bash
# 列出插件
curl "http://localhost:8000/api/plugins"

# 执行插件
curl -X POST "http://localhost:8000/api/plugins/yara-scanner/execute" \
  -H "Content-Type: application/json" \
  -d '{"target": "suspicious.exe"}'
```

---

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户界面层                              │
│           Web UI (Gradio) / REST API / CLI                  │
├─────────────────────────────────────────────────────────────┤
│                      插件系统层                              │
│        Plugin Manager (动态加载/钩子系统)                    │
├─────────────────────────────────────────────────────────────┤
│                      智能调度层                              │
│    Agent Core (任务规划) + Tool Registry (工具注册)          │
├─────────────────────────────────────────────────────────────┤
│                      知识检索层                              │
│           Knowledge Base (向量化技能知识库)                  │
├─────────────────────────────────────────────────────────────┤
│                      AI引擎层                               │
│        LLM Engine (OpenAI / Claude / Ollama)                │
├─────────────────────────────────────────────────────────────┤
│                      工具执行层                              │
│      Tool Executor + Output Parser (20+取证工具)            │
└─────────────────────────────────────────────────────────────┘
```

---

## 开发路线图

- [x] **Phase 1**: AI核心集成 (LLM引擎 + 任务规划 + 知识库)
- [x] **Phase 2**: 智能分析引擎升级 (工具调用系统)
- [x] **Phase 3**: Web UI界面开发 (Gradio + 密钥配置)
- [x] **Phase 4**: API接口和插件系统 (FastAPI + Plugin Manager)
- [ ] **Phase 5**: 案例库和持续学习

---

## 依赖说明

### Python依赖

```bash
pip install -r requirements.txt
```

主要依赖:
- `gradio` - Web UI框架
- `fastapi` - API框架
- `aiohttp` - 异步HTTP客户端
- `sentence-transformers` - 向量嵌入模型

### 取证工具

通过 `install.bat` 自动安装:
- sleuthkit - 磁盘取证
- wireshark/tshark - 网络分析
- volatility3 - 内存取证
- jadx - Android逆向
- hashcat - 密码破解
- yara - 恶意代码检测
- 等20+工具

---

## 参考项目

- [Open WebUI](https://github.com/open-webui/open-webui) - Web UI参考
- [forensic-agent-skills](https://github.com/Blackhole-Hu/forensic-agent-skills) - 取证Agent技能库参考
- [Gradio](https://gradio.app/) - Web UI框架
- [FastAPI](https://fastapi.tiangolo.com/) - API框架

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 🔄 项目更新

### 一键更新（推荐）

**Windows用户:**
```bash
update.bat
```

**Linux/Mac用户:**
```bash
chmod +x update.sh
./update.sh
```

### 手动更新

```bash
# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt
```

### 检查更新

```bash
python scripts/updater.py --check
```

### 更新脚本功能

- ✅ 自动检测是否有新版本
- ✅ 显示更新内容（git log）
- ✅ 支持暂存本地修改（git stash）
- ✅ 自动更新Python依赖
- ✅ 版本号管理（VERSION文件）

---

## 贡献

欢迎提交Issue和Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 联系方式

- GitHub: [@luyichen0704](https://github.com/luyichen0704)
- 项目链接: [https://github.com/luyichen0704/forensic-ai-platform](https://github.com/luyichen0704/forensic-ai-platform)

---

## 致谢

感谢所有开源项目的贡献者，特别是:
- Open WebUI 团队
- Gradio 团队
- FastAPI 团队
- 取证社区的各位专家
