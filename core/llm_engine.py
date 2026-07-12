"""
LLM Engine - 大模型API统一封装
支持多种大模型后端：OpenAI、Claude、本地模型(Ollama等)
"""
import os
import json
import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    """大模型响应结构"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    metadata: Optional[Dict[str, Any]] = None

class BaseLLMProvider(ABC):
    """大模型提供者基类"""
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """发送聊天请求"""
        pass
    
    @abstractmethod
    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs):
        """流式聊天请求"""
        pass

class OpenAIProvider(BaseLLMProvider):
    """OpenAI API提供者"""
    
    def __init__(self, api_key: str, model: str = "gpt-4", base_url: str = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"
        
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """发送聊天请求到OpenAI API"""
        try:
            import aiohttp
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 4096),
                "stream": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"OpenAI API错误: {response.status} - {error_text}")
                    
                    result = await response.json()
                    
                    return LLMResponse(
                        content=result["choices"][0]["message"]["content"],
                        model=result["model"],
                        usage=result.get("usage", {}),
                        finish_reason=result["choices"][0]["finish_reason"]
                    )
                    
        except ImportError:
            raise ImportError("请安装aiohttp: pip install aiohttp")
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            raise
    
    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs):
        """流式聊天请求"""
        try:
            import aiohttp
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 4096),
                "stream": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"OpenAI API错误: {response.status} - {error_text}")
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            line = line[6:]
                            if line == '[DONE]':
                                break
                            try:
                                chunk = json.loads(line)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    delta = chunk['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        yield delta['content']
                            except json.JSONDecodeError:
                                continue
                                
        except ImportError:
            raise ImportError("请安装aiohttp: pip install aiohttp")
        except Exception as e:
            logger.error(f"OpenAI流式API调用失败: {e}")
            raise

class ClaudeProvider(BaseLLMProvider):
    """Claude API提供者"""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key
        self.model = model
        
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """发送聊天请求到Claude API"""
        try:
            import aiohttp
            
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            # 转换消息格式为Claude格式
            claude_messages = []
            system_message = None
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    claude_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            data = {
                "model": self.model,
                "max_tokens": kwargs.get("max_tokens", 4096),
                "messages": claude_messages
            }
            
            if system_message:
                data["system"] = system_message
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Claude API错误: {response.status} - {error_text}")
                    
                    result = await response.json()
                    
                    return LLMResponse(
                        content=result["content"][0]["text"],
                        model=result["model"],
                        usage=result.get("usage", {}),
                        finish_reason=result["stop_reason"]
                    )
                    
        except ImportError:
            raise ImportError("请安装aiohttp: pip install aiohttp")
        except Exception as e:
            logger.error(f"Claude API调用失败: {e}")
            raise
    
    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs):
        """流式聊天请求"""
        # Claude流式API实现
        yield "Claude流式API暂未实现"

class OllamaProvider(BaseLLMProvider):
    """Ollama本地模型提供者"""
    
    def __init__(self, model: str = "llama2", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """发送聊天请求到Ollama API"""
        try:
            import aiohttp
            
            data = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "num_predict": kwargs.get("max_tokens", 4096)
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama API错误: {response.status} - {error_text}")
                    
                    result = await response.json()
                    
                    return LLMResponse(
                        content=result["message"]["content"],
                        model=result["model"],
                        usage={
                            "prompt_tokens": result.get("prompt_eval_count", 0),
                            "completion_tokens": result.get("eval_count", 0),
                            "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                        },
                        finish_reason="stop"
                    )
                    
        except ImportError:
            raise ImportError("请安装aiohttp: pip install aiohttp")
        except Exception as e:
            logger.error(f"Ollama API调用失败: {e}")
            raise
    
    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs):
        """流式聊天请求"""
        try:
            import aiohttp
            
            data = {
                "model": self.model,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "num_predict": kwargs.get("max_tokens", 4096)
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama API错误: {response.status} - {error_text}")
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line:
                            try:
                                chunk = json.loads(line)
                                if 'message' in chunk and 'content' in chunk['message']:
                                    yield chunk['message']['content']
                            except json.JSONDecodeError:
                                continue
                                
        except ImportError:
            raise ImportError("请安装aiohttp: pip install aiohttp")
        except Exception as e:
            logger.error(f"Ollama流式API调用失败: {e}")
            raise

class LLMEngine:
    """大模型引擎 - 统一管理多种大模型后端"""
    
    def __init__(self, config_path: str = None):
        """
        初始化大模型引擎
        
        Args:
            config_path: 配置文件路径，如果为None则使用环境变量
        """
        self.providers = {}
        self.default_provider = None
        self.config = self._load_config(config_path)
        self._setup_providers()
    
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """加载配置"""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 默认配置
        return {
            "providers": {
                "openai": {
                    "api_key": os.getenv("OPENAI_API_KEY", ""),
                    "model": "gpt-4",
                    "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
                },
                "claude": {
                    "api_key": os.getenv("CLAUDE_API_KEY", ""),
                    "model": "claude-3-sonnet-20240229"
                },
                "ollama": {
                    "model": os.getenv("OLLAMA_MODEL", "llama2"),
                    "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                }
            },
            "default_provider": os.getenv("DEFAULT_LLM_PROVIDER", "openai"),
            "max_retries": 3,
            "timeout": 30
        }
    
    def _setup_providers(self):
        """设置大模型提供者"""
        providers_config = self.config.get("providers", {})
        
        # 初始化OpenAI提供者
        if "openai" in providers_config:
            openai_config = providers_config["openai"]
            if openai_config.get("api_key"):
                self.providers["openai"] = OpenAIProvider(
                    api_key=openai_config["api_key"],
                    model=openai_config.get("model", "gpt-4"),
                    base_url=openai_config.get("base_url")
                )
        
        # 初始化Claude提供者
        if "claude" in providers_config:
            claude_config = providers_config["claude"]
            if claude_config.get("api_key"):
                self.providers["claude"] = ClaudeProvider(
                    api_key=claude_config["api_key"],
                    model=claude_config.get("model", "claude-3-sonnet-20240229")
                )
        
        # 初始化Ollama提供者
        if "ollama" in providers_config:
            ollama_config = providers_config["ollama"]
            self.providers["ollama"] = OllamaProvider(
                model=ollama_config.get("model", "llama2"),
                base_url=ollama_config.get("base_url", "http://localhost:11434")
            )
        
        # 设置默认提供者
        default_provider = self.config.get("default_provider", "openai")
        if default_provider in self.providers:
            self.default_provider = default_provider
        elif self.providers:
            self.default_provider = list(self.providers.keys())[0]
        else:
            logger.warning("没有可用的大模型提供者")
    
    async def chat(self, messages: List[Dict[str, str]], 
                   provider: str = None, **kwargs) -> LLMResponse:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表，格式为[{"role": "user", "content": "..."}]
            provider: 指定提供者，如果为None则使用默认提供者
            **kwargs: 其他参数
            
        Returns:
            LLMResponse对象
        """
        provider_name = provider or self.default_provider
        
        if not provider_name or provider_name not in self.providers:
            raise ValueError(f"不可用的提供者: {provider_name}")
        
        provider = self.providers[provider_name]
        
        # 重试逻辑
        max_retries = self.config.get("max_retries", 3)
        for attempt in range(max_retries):
            try:
                return await provider.chat(messages, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"第{attempt + 1}次尝试失败: {e}，正在重试...")
                await asyncio.sleep(1 * (attempt + 1))
    
    async def stream_chat(self, messages: List[Dict[str, str]], 
                          provider: str = None, **kwargs):
        """
        流式聊天请求
        
        Args:
            messages: 消息列表
            provider: 指定提供者
            **kwargs: 其他参数
            
        Yields:
            流式响应内容
        """
        provider_name = provider or self.default_provider
        
        if not provider_name or provider_name not in self.providers:
            raise ValueError(f"不可用的提供者: {provider_name}")
        
        provider = self.providers[provider_name]
        
        async for chunk in provider.stream_chat(messages, **kwargs):
            yield chunk
    
    def get_available_providers(self) -> List[str]:
        """获取可用的提供者列表"""
        return list(self.providers.keys())
    
    def get_provider_info(self, provider: str = None) -> Dict[str, Any]:
        """获取提供者信息"""
        provider_name = provider or self.default_provider
        
        if not provider_name or provider_name not in self.providers:
            return {}
        
        provider = self.providers[provider_name]
        
        return {
            "name": provider_name,
            "type": type(provider).__name__,
            "model": getattr(provider, 'model', 'unknown')
        }

# 配置文件模板
CONFIG_TEMPLATE = {
    "providers": {
        "openai": {
            "api_key": "your-openai-api-key",
            "model": "gpt-4",
            "base_url": "https://api.openai.com/v1"
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
    "default_provider": "openai",
    "max_retries": 3,
    "timeout": 30
}

def create_config_template(output_path: str = "llm_config.json"):
    """创建配置文件模板"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(CONFIG_TEMPLATE, f, indent=2, ensure_ascii=False)
    logger.info(f"配置文件模板已创建: {output_path}")

if __name__ == "__main__":
    # 测试代码
    async def test():
        engine = LLMEngine()
        print(f"可用提供者: {engine.get_available_providers()}")
        
        if engine.default_provider:
            print(f"默认提供者: {engine.default_provider}")
            print(f"提供者信息: {engine.get_provider_info()}")
            
            # 测试聊天
            try:
                messages = [
                    {"role": "system", "content": "你是一个专业的电子取证专家"},
                    {"role": "user", "content": "请解释什么是E01文件格式？"}
                ]
                response = await engine.chat(messages)
                print(f"响应: {response.content[:100]}...")
            except Exception as e:
                print(f"测试失败: {e}")
        else:
            print("没有可用的大模型提供者，请配置API密钥")
    
    asyncio.run(test())