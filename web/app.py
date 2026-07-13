"""
Web UI - 取证平台专用界面
基于Gradio构建，集成Open WebUI风格
"""
import os
import json
import asyncio
import gradio as gr
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class ForensicWebUI:
    """取证平台Web UI"""
    
    def __init__(self, agent=None):
        """初始化UI"""
        from agent.core import ForensicAgent
        from agent.tools.registry import registry
        
        self.agent = agent or ForensicAgent()
        self.tool_registry = registry
        self.config = self._load_config()
        
    def _load_config(self) -> dict:
        """加载配置"""
        config_path = "config/llm_config.json"
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_config(self, config: dict):
        """保存配置"""
        config_path = "config/llm_config.json"
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def create_ui(self) -> gr.Blocks:
        """创建UI界面"""
        
        # 自定义CSS
        custom_css = """
        .forensic-header {
            background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .tool-card {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
        }
        .status-ok { color: #4caf50; }
        .status-error { color: #f44336; }
        """
        
        with gr.Blocks(title="Forensic AI Platform") as ui:
            
            # ==================== 页面标题 ====================
            gr.HTML("""
            <div class="forensic-header">
                <h1>🔍 基于大模型的自动化取证平台</h1>
                <p>AI-Powered Digital Forensics Platform</p>
            </div>
            """)
            
            with gr.Tabs():
                
                # ==================== Tab 1: AI取证助手 ====================
                with gr.TabItem("🤖 AI取证助手", id="chat"):
                    with gr.Row():
                        with gr.Column(scale=3):
                            chatbot = gr.Chatbot(
                                label="取证对话",
                                height=500
                            )
                            
                            with gr.Row():
                                msg_input = gr.Textbox(
                                    label="输入问题",
                                    placeholder="描述你的取证任务，例如：分析E01磁盘镜像，找出删除的文件",
                                    lines=2,
                                    scale=4
                                )
                                send_btn = gr.Button("发送", variant="primary", scale=1)
                            
                            with gr.Row():
                                clear_btn = gr.Button("🗑️ 清空对话")
                                export_btn = gr.Button("📥 导出报告")
                        
                        with gr.Column(scale=1):
                            gr.Markdown("### 💡 快速任务")
                            
                            quick_tasks = [
                                ("💾 磁盘取证", "分析E01磁盘镜像，提取文件列表和关键证据"),
                                ("🌐 流量分析", "分析PCAP流量包，找出攻击者IP和恶意请求"),
                                ("🧠 内存取证", "分析内存转储，找出恶意进程和网络连接"),
                                ("📱 APK分析", "逆向分析Android APK，提取敏感信息"),
                                ("🔐 密码破解", "破解密码哈希或加密文件"),
                                ("🖼️ 隐写分析", "检测图片中的隐写信息"),
                            ]
                            
                            for label, task in quick_tasks:
                                btn = gr.Button(label, size="sm")
                                btn.click(
                                    lambda t=task: t,
                                    outputs=msg_input
                                )
                            
                            gr.Markdown("### 📋 分析进度")
                            progress_output = gr.Textbox(
                                label="执行状态",
                                lines=8,
                                interactive=False
                            )
                
                # ==================== Tab 2: 工具管理 ====================
                with gr.TabItem("🛠️ 工具管理", id="tools"):
                    with gr.Row():
                        with gr.Column(scale=2):
                            gr.Markdown("### 📦 工具状态")
                            
                            # 工具状态表格
                            tool_status = gr.Dataframe(
                                headers=["工具", "类别", "状态", "描述"],
                                datatype=["str", "str", "str", "str"],
                                label="取证工具列表"
                            )
                            
                            with gr.Row():
                                refresh_btn = gr.Button("🔄 刷新状态")
                                install_btn = gr.Button("📥 安装缺失工具", variant="primary")
                        
                        with gr.Column(scale=1):
                            gr.Markdown("### ⚙️ 工具配置")
                            
                            tool_select = gr.Dropdown(
                                label="选择工具",
                                choices=[t.name for t in self.tool_registry.get_all_tools()],
                                interactive=True
                            )
                            
                            tool_info = gr.Markdown("选择工具查看详情")
                            
                            test_btn = gr.Button("🧪 测试工具")
                            test_output = gr.Textbox(label="测试结果", lines=3)
                
                # ==================== Tab 3: 证据分析 ====================
                with gr.TabItem("📁 证据分析", id="evidence"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("### 📤 上传证据")
                            
                            evidence_file = gr.File(
                                label="选择证据文件",
                                file_types=[".E01", ".raw", ".dd", ".pcap", ".pcapng", ".mem", ".apk", ".exe"],
                                type="filepath"
                            )
                            
                            evidence_type = gr.Dropdown(
                                label="证据类型",
                                choices=["自动检测", "磁盘镜像", "网络流量", "内存转储", "Android应用", "可执行文件"],
                                value="自动检测"
                            )
                            
                            analysis_depth = gr.Slider(
                                label="分析深度",
                                minimum=1,
                                maximum=5,
                                value=3,
                                step=1
                            )
                            
                            analyze_btn = gr.Button("🔍 开始分析", variant="primary", size="lg")
                        
                        with gr.Column(scale=2):
                            gr.Markdown("### 📊 分析结果")
                            
                            analysis_output = gr.Markdown(
                                value="等待分析...",
                                label="分析报告"
                            )
                            
                            with gr.Row():
                                download_btn = gr.Button("📥 下载报告")
                                share_btn = gr.Button("🔗 分享结果")
                
                # ==================== Tab 4: 知识库 ====================
                with gr.TabItem("📚 知识库", id="knowledge"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("### 🔍 搜索技能")
                            
                            search_input = gr.Textbox(
                                label="搜索",
                                placeholder="输入关键词搜索取证技能..."
                            )
                            
                            category_filter = gr.Dropdown(
                                label="类别过滤",
                                choices=["全部", "磁盘取证", "网络分析", "内存取证", "Android", "密码学", "隐写", "逆向"],
                                value="全部"
                            )
                            
                            search_btn = gr.Button("🔍 搜索")
                        
                        with gr.Column(scale=2):
                            gr.Markdown("### 📖 技能文档")
                            
                            skill_list = gr.Dataframe(
                                headers=["技能名称", "类别", "相关度"],
                                datatype=["str", "str", "number"],
                                label="搜索结果"
                            )
                            
                            skill_content = gr.Markdown(
                                value="选择技能查看详情...",
                                label="技能内容"
                            )
                
                # ==================== Tab 5: 设置 ====================
                with gr.TabItem("⚙️ 设置", id="settings"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("### 🔑 API配置")
                            
                            # API预设选择
                            api_preset = gr.Dropdown(
                                label="API预设 (快速选择)",
                                choices=[
                                    "自定义",
                                    "OpenAI 官方",
                                    "Claude 官方",
                                    "Ollama 本地",
                                    "DeepSeek",
                                    "月之暗面 Kimi",
                                    "智谱 GLM",
                                    "百度文心",
                                    "第三方中转站"
                                ],
                                value="自定义",
                                info="选择预设可自动填充配置"
                            )
                            
                            llm_provider = gr.Dropdown(
                                label="LLM提供者",
                                choices=["openai", "claude", "ollama"],
                                value=self.config.get("provider", "openai")
                            )
                            
                            api_key = gr.Textbox(
                                label="API Key",
                                type="password",
                                placeholder="输入API密钥...",
                                value=self.config.get("api_key", "")
                            )
                            
                            base_url = gr.Textbox(
                                label="API Base URL",
                                placeholder="https://api.openai.com/v1",
                                value=self.config.get("base_url", ""),
                                info="支持第三方中转站，修改此地址即可"
                            )
                            
                            model_name = gr.Textbox(
                                label="模型名称",
                                placeholder="gpt-4",
                                value=self.config.get("model", "gpt-4")
                            )
                            
                            # 预设配置说明
                            preset_info = gr.Markdown(
                                """
**常用第三方中转站配置:**
- 只需修改 `API Base URL` 为中转站地址
- API Key 使用中转站提供的密钥
- 模型名称按中转站要求填写
                                """
                            )
                            
                            save_config_btn = gr.Button("💾 保存配置", variant="primary")
                            config_status = gr.Markdown("")
                        
                        with gr.Column(scale=1):
                            gr.Markdown("### 🧪 连接测试")
                            
                            test_message = gr.Textbox(
                                label="测试消息",
                                value="你好，请简单介绍你的功能",
                                lines=2
                            )
                            
                            test_llm_btn = gr.Button("🧪 测试LLM连接")
                            test_result = gr.Markdown("")
                            
                            gr.Markdown("### 📊 系统信息")
                            
                            system_info = gr.Markdown(self._get_system_info())
                            
                            refresh_info_btn = gr.Button("🔄 刷新信息")
            
            # ==================== 事件绑定 ====================
            
            # 聊天功能
            def chat(message, history):
                """处理聊天消息"""
                if not message:
                    return "", history
                
                # 添加用户消息
                history.append((message, None))
                
                # 异步执行分析
                async def run_analysis():
                    try:
                        # 检查是否包含证据路径
                        evidence_path = self._extract_evidence_path(message)
                        
                        if evidence_path:
                            result = await self.agent.analyze(message, evidence_path)
                            response = self._format_analysis_result(result)
                        else:
                            response = await self._chat_with_llm(message, history)
                        
                        return response
                    except Exception as e:
                        return f"抱歉，处理过程中出现错误: {str(e)}"
                
                # 执行并返回
                loop = asyncio.new_event_loop()
                response = loop.run_until_complete(run_analysis())
                loop.close()
                
                history[-1] = (message, response)
                return "", history
            
            send_btn.click(chat, [msg_input, chatbot], [msg_input, chatbot])
            msg_input.submit(chat, [msg_input, chatbot], [msg_input, chatbot])
            clear_btn.click(lambda: [], outputs=chatbot)
            
            # 工具管理
            def refresh_tool_status():
                """刷新工具状态"""
                status = self.tool_registry.check_all_tools()
                data = []
                for tool in self.tool_registry.get_all_tools():
                    available = status.get(tool.name, False)
                    status_text = "✅ 可用" if available else "❌ 未安装"
                    data.append([tool.name, tool.category.value, status_text, tool.description])
                return data
            
            refresh_btn.click(refresh_tool_status, outputs=tool_status)
            
            def show_tool_info(tool_name):
                """显示工具信息"""
                tool = self.tool_registry.get_tool(tool_name)
                if tool:
                    return f"""
### {tool.name}

**类别:** {tool.category.value}

**描述:** {tool.description}

**安装命令:**
```
{tool.install_command}
```

**使用示例:**
{chr(10).join(f'- `{ex}`' for ex in tool.examples)}
"""
                return "工具未找到"
            
            tool_select.change(show_tool_info, inputs=[tool_select], outputs=[tool_info])
            
            # API预设选择处理
            def apply_preset(preset):
                """应用API预设"""
                presets = {
                    "OpenAI 官方": {
                        "provider": "openai",
                        "base_url": "https://api.openai.com/v1",
                        "model": "gpt-4"
                    },
                    "Claude 官方": {
                        "provider": "claude",
                        "base_url": "",
                        "model": "claude-3-sonnet-20240229"
                    },
                    "Ollama 本地": {
                        "provider": "ollama",
                        "base_url": "http://localhost:11434",
                        "model": "llama2"
                    },
                    "DeepSeek": {
                        "provider": "openai",
                        "base_url": "https://api.deepseek.com/v1",
                        "model": "deepseek-chat"
                    },
                    "月之暗面 Kimi": {
                        "provider": "openai",
                        "base_url": "https://api.moonshot.cn/v1",
                        "model": "moonshot-v1-8k"
                    },
                    "智谱 GLM": {
                        "provider": "openai",
                        "base_url": "https://open.bigmodel.cn/api/paas/v4",
                        "model": "glm-4"
                    },
                    "百度文心": {
                        "provider": "openai",
                        "base_url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop",
                        "model": "ernie-4.0"
                    },
                    "第三方中转站": {
                        "provider": "openai",
                        "base_url": "https://your-proxy.com/v1",
                        "model": "gpt-4"
                    }
                }
                
                if preset in presets:
                    p = presets[preset]
                    return p["provider"], p["base_url"], p["model"]
                return "openai", "", "gpt-4"
            
            api_preset.change(
                apply_preset,
                inputs=[api_preset],
                outputs=[llm_provider, base_url, model_name]
            )
            
            # 配置保存
            def save_config(provider, api_key, base_url, model):
                """保存配置"""
                config = {
                    "provider": provider,
                    "api_key": api_key,
                    "base_url": base_url,
                    "model": model
                }
                self._save_config(config)
                self.config = config
                return "✅ 配置已保存！重启服务后生效。"
            
            save_config_btn.click(
                save_config,
                [llm_provider, api_key, base_url, model_name],
                outputs=config_status
            )
            
            # LLM测试
            async def test_llm(message):
                """测试LLM连接"""
                try:
                    from agent.llm import LLMEngine
                    llm = LLMEngine()
                    response = await llm.chat([
                        {"role": "user", "content": message}
                    ])
                    return f"✅ 连接成功！\n\n**响应:** {response.content[:200]}..."
                except Exception as e:
                    return f"❌ 连接失败: {str(e)}"
            
            def run_test_llm(message):
                loop = asyncio.new_event_loop()
                result = loop.run_until_complete(test_llm(message))
                loop.close()
                return result
            
            test_llm_btn.click(run_test_llm, inputs=test_message, outputs=test_result)
            
            # 证据分析
            def analyze_evidence(file, depth):
                """分析证据"""
                if not file:
                    return "请先上传证据文件"
                
                async def run():
                    result = await self.agent.analyze(
                        f"深度分析这个证据文件，分析深度: {depth}",
                        file
                    )
                    return self._format_analysis_result(result)
                
                loop = asyncio.new_event_loop()
                result = loop.run_until_complete(run())
                loop.close()
                return result
            
            analyze_btn.click(analyze_evidence, [evidence_file, analysis_depth], outputs=analysis_output)
            
            # 页面加载时刷新工具状态
            ui.load(refresh_tool_status, outputs=tool_status)
        
        return ui
    
    def _extract_evidence_path(self, message: str) -> Optional[str]:
        """从消息中提取证据路径"""
        import re
        patterns = [
            r'[A-Za-z]:\\[^\s]+\.(?:E01|raw|dd|img|pcap|pcapng|mem|apk)',
            r'/[^\s]+\.(?:E01|raw|dd|img|pcap|pcapng|mem|apk)',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                return matches[0]
        return None
    
    def _format_analysis_result(self, result: dict) -> str:
        """格式化分析结果"""
        output = []
        output.append("## 📊 分析结果\n")
        
        if result.get("findings"):
            output.append("### 🔍 关键发现\n")
            for i, finding in enumerate(result["findings"][:10], 1):
                output.append(f"{i}. {finding}")
            output.append("")
        
        if result.get("artifacts"):
            output.append("### 📦 提取的证据\n")
            for artifact in result["artifacts"][:5]:
                output.append(f"- **{artifact.get('type', '未知')}**: {artifact.get('value', artifact.get('name', 'N/A'))}")
            output.append("")
        
        if result.get("summary"):
            output.append("### 📝 分析总结\n")
            output.append(result["summary"])
        
        return "\n".join(output)
    
    async def _chat_with_llm(self, message: str, history: list) -> str:
        """与LLM对话"""
        from agent.llm import LLMEngine
        
        llm = LLMEngine()
        
        system_prompt = """你是一个专业的电子取证专家AI助手。你的任务是帮助用户分析电子证据，找出关键信息。

你可以帮助用户：
1. 解答取证相关问题
2. 提供分析思路和方法
3. 解释取证工具的使用
4. 分析取证结果

请用中文回答，保持专业且易懂。"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加历史消息
        for user_msg, bot_msg in history[-5:]:
            if user_msg:
                messages.append({"role": "user", "content": user_msg})
            if bot_msg:
                messages.append({"role": "assistant", "content": bot_msg})
        
        messages.append({"role": "user", "content": message})
        
        response = await llm.chat(messages)
        return response.content
    
    def _get_system_info(self) -> str:
        """获取系统信息"""
        import platform
        import sys
        
        info = f"""
| 项目 | 值 |
|------|-----|
| 系统 | {platform.system()} {platform.release()} |
| Python | {sys.version.split()[0]} |
| 架构 | {platform.machine()} |
| LLM提供者 | {self.config.get('provider', '未配置')} |
| 模型 | {self.config.get('model', '未配置')} |
"""
        return info
    
    def launch(self, **kwargs):
        """启动UI"""
        ui = self.create_ui()
        ui.launch(**kwargs)

def create_app() -> gr.Blocks:
    """创建应用"""
    webui = ForensicWebUI()
    return webui.create_ui()

if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
