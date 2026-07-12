# 基于大模型的自动化取证平台

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

一个基于大语言模型(LLM)的智能电子取证分析平台，集成了自动化任务规划、知识库检索和多工具协同能力。

## 核心特性

### 智能分析引擎
- **多模型支持**: 集成OpenAI GPT-4、Claude、本地模型(Ollama)等多种大模型后端
- **智能任务规划**: 基于题目描述自动识别任务类型并生成分析步骤
- **知识库检索**: 向量化的技能知识库，支持语义搜索

### 取证能力覆盖
- 磁盘取证 (E01/RAW/DD镜像分析)
- 网络流量分析 (PCAP/PCAPNG)
- 内存取证 (Volatility3)
- Android分析 (APK逆向)
- 密码学分析 (RSA/AES/哈希破解)
- 隐写分析 (图片/音频/视频)
- 逆向工程 (PE/ELF二进制)
- 服务器取证 (Web/数据库/日志)

### 自动化工作流
- 一键分析: 输入题目描述和证据路径，自动执行完整分析流程
- 工具链编排: 智能调度20+取证工具
- 证据链关联: 多检材证据自动关联分析
- 报告生成: 自动生成结构化分析报告

## 项目结构

```
forensic-ai-platform/
├── core/                          # 核心AI引擎
│   ├── __init__.py
│   ├── llm_engine.py             # 大模型API封装
│   ├── agent_planner.py          # 任务规划Agent
│   └── knowledge_base.py         # 知识库管理
├── skills/                        # 取证技能库
│   ├── file-analysis.md          # 文件分析
│   ├── disk-forensics.md         # 磁盘取证
│   ├── network-forensics.md      # 网络流量分析
│   ├── memory-forensics.md       # 内存取证
│   ├── android-analysis.md       # Android分析
│   ├── crypto.md                 # 密码学
│   ├── stego.md                  # 隐写分析
│   ├── reverse-engineering.md    # 逆向工程
│   └── ...
├── scripts/                       # 工具脚本
│   ├── smart_hunter.py           # 智能搜索引擎
│   ├── evidence_linker.py        # 证据链关联
│   ├── e01_tool.py               # E01工具
│   └── ...
├── config/                        # 配置文件
│   └── llm_config.json           # LLM配置
├── templates/                     # 模板文件
│   └── skill-template.md         # 技能模板
├── docs/                          # 文档
│   └── ...
├── tests/                         # 测试
│   └── ...
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
└── setup.py
```

## 快速开始

### 1. 环境准备

```bash
# 克隆仓库
git clone https://github.com/luyichen0704/forensic-ai-platform.git
cd forensic-ai-platform

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置大模型

复制配置模板并填入API密钥:

```bash
cp config/llm_config.example.json config/llm_config.json
```

编辑 `config/llm_config.json`:

```json
{
  "providers": {
    "openai": {
      "api_key": "your-openai-api-key",
      "model": "gpt-4"
    },
    "claude": {
      "api_key": "your-claude-api-key",
      "model": "claude-3-sonnet-20240229"
    },
    "ollama": {
      "model": "llama2",
      "base_url": "http://localhost:11434"
    }
  },
  "default_provider": "openai"
}
```

### 3. 使用示例

```python
import asyncio
from core import LLMEngine, AgentPlanner, KnowledgeBase

async def analyze():
    # 初始化引擎
    llm = LLMEngine("config/llm_config.json")
    planner = AgentPlanner(llm)
    kb = KnowledgeBase("skills/")
    
    # 创建分析计划
    plan = await planner.create_plan(
        topic="分析E01磁盘镜像，找出删除的文件",
        artifact_path="evidence.E01"
    )
    
    print(planner.format_plan(plan))
    
    # 搜索相关技能
    results = kb.search("磁盘取证 E01", top_k=3)
    for result in results:
        print(f"技能: {result.skill.name}, 分数: {result.score:.2f}")

asyncio.run(analyze())
```

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户界面层                            │
│              (Web UI / CLI / API)                       │
├─────────────────────────────────────────────────────────┤
│                   智能调度层                             │
│    Agent Planner (任务规划) + Tool Router (工具路由)      │
├─────────────────────────────────────────────────────────┤
│                   知识检索层                             │
│        Knowledge Base (向量化知识库)                     │
├─────────────────────────────────────────────────────────┤
│                   AI引擎层                              │
│      LLM Engine (OpenAI/Claude/Ollama)                  │
├─────────────────────────────────────────────────────────┤
│                   工具执行层                             │
│    20+取证工具 (sleuthkit/tshark/volatility3/...)       │
└─────────────────────────────────────────────────────────┘
```

## 开发路线图

- [x] Phase 1: AI核心集成 (LLM引擎 + 任务规划 + 知识库)
- [ ] Phase 2: 智能分析引擎升级
- [ ] Phase 3: Web UI界面开发
- [ ] Phase 4: API接口和插件系统
- [ ] Phase 5: 案例库和持续学习

## 参考项目

- [forensic-agent-skills](https://github.com/Blackhole-Hu/forensic-agent-skills) - 取证Agent技能库参考
- [CTF-Autopilot](https://github.com/your-repo) - 原始CTF取证框架

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

- GitHub: [@luyichen0704](https://github.com/luyichen0704)
