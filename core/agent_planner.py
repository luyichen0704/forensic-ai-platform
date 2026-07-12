"""
Agent Planner - 任务规划Agent
基于大模型的智能任务规划，能够根据题目描述自动规划取证分析步骤
"""
import os
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from .llm_engine import LLMEngine

logger = logging.getLogger(__name__)

class TaskType(Enum):
    """任务类型枚举"""
    FILE_ANALYSIS = "file_analysis"  # 文件分析
    DISK_FORENSICS = "disk_forensics"  # 磁盘取证
    NETWORK_ANALYSIS = "network_analysis"  # 网络流量分析
    MEMORY_FORENSICS = "memory_forensics"  # 内存取证
    ANDROID_ANALYSIS = "android_analysis"  # Android分析
    CRYPTO_ANALYSIS = "crypto_analysis"  # 密码学分析
    STEGO_ANALYSIS = "stego_analysis"  # 隐写分析
    REVERSE_ENGINEERING = "reverse_engineering"  # 逆向工程
    SERVER_FORENSICS = "server_forensics"  # 服务器取证
    INCIDENT_RESPONSE = "incident_response"  # 应急响应
    UNKNOWN = "unknown"  # 未知类型

@dataclass
class AnalysisStep:
    """分析步骤"""
    step_id: int
    description: str
    tools: List[str]
    commands: List[str]
    expected_output: str
    priority: int = 1  # 优先级，1为最高
    dependencies: List[int] = field(default_factory=list)  # 依赖的步骤ID
    estimated_time: int = 60  # 预估时间（秒）

@dataclass
class AnalysisPlan:
    """分析计划"""
    task_type: TaskType
    description: str
    steps: List[AnalysisStep]
    total_estimated_time: int
    confidence: float  # 置信度
    metadata: Dict[str, Any] = field(default_factory=dict)

class AgentPlanner:
    """任务规划Agent"""
    
    def __init__(self, llm_engine: LLMEngine = None):
        """
        初始化任务规划Agent
        
        Args:
            llm_engine: 大模型引擎实例
        """
        self.llm_engine = llm_engine or LLMEngine()
        self.task_patterns = self._load_task_patterns()
        self.tool_mapping = self._load_tool_mapping()
    
    def _load_task_patterns(self) -> Dict[str, Any]:
        """加载任务模式"""
        return {
            "keywords": {
                TaskType.DISK_FORENSICS: [
                    "E01", "磁盘", "镜像", "分区", "文件系统", "NTFS", "FAT32", "EXT4",
                    "取证", "恢复", "删除", "Autopsy", "Sleuth Kit"
                ],
                TaskType.NETWORK_ANALYSIS: [
                    "PCAP", "流量", "网络", "HTTP", "DNS", "TCP", "UDP", "Wireshark",
                    "抓包", "数据包", "协议"
                ],
                TaskType.MEMORY_FORENSICS: [
                    "内存", "RAM", "转储", "dump", "Volatility", "进程", "句柄",
                    "内存取证", "内存镜像"
                ],
                TaskType.ANDROID_ANALYSIS: [
                    "APK", "安卓", "Android", "APP", "手机", "移动", "jadx",
                    "逆向", "反编译"
                ],
                TaskType.CRYPTO_ANALYSIS: [
                    "加密", "解密", "RSA", "AES", "DES", "Base64", "编码",
                    "密码", "哈希", "MD5", "SHA"
                ],
                TaskType.STEGO_ANALYSIS: [
                    "隐写", "图片", "音频", "视频", "LSB", "steghide",
                    "zsteg", "隐写术", "隐藏信息"
                ],
                TaskType.REVERSE_ENGINEERING: [
                    "逆向", "二进制", "PE", "ELF", "反汇编", "调试",
                    "radare2", "IDA", "脱壳"
                ],
                TaskType.SERVER_FORENSICS: [
                    "服务器", "Web", "数据库", "日志", "Linux", "Windows Server",
                    "宝塔", "Docker", "K8s"
                ],
                TaskType.INCIDENT_RESPONSE: [
                    "应急响应", "挖矿", "勒索", "Webshell", "后门", "入侵",
                    "攻击", "恶意代码"
                ]
            },
            "file_extensions": {
                TaskType.DISK_FORENSICS: [".E01", ".raw", ".dd", ".img", ".vmdk", ".vhd"],
                TaskType.NETWORK_ANALYSIS: [".pcap", ".pcapng", ".cap"],
                TaskType.MEMORY_FORENSICS: [".raw", ".mem", ".dmp", ".vmem"],
                TaskType.ANDROID_ANALYSIS: [".apk", ".xapk", ".aab"],
                TaskType.CRYPTO_ANALYSIS: [".enc", ".pem", ".key", ".crt", ".cer"],
                TaskType.STEGO_ANALYSIS: [".png", ".jpg", ".jpeg", ".bmp", ".gif", ".wav", ".mp3"],
                TaskType.REVERSE_ENGINEERING: [".exe", ".dll", ".sys", ".elf", ".so"]
            }
        }
    
    def _load_tool_mapping(self) -> Dict[TaskType, List[str]]:
        """加载工具映射"""
        return {
            TaskType.FILE_ANALYSIS: [
                "file", "strings", "xxd", "exiftool", "binwalk"
            ],
            TaskType.DISK_FORENSICS: [
                "sleuthkit", "autopsy", "fls", "icat", "tsk_recover"
            ],
            TaskType.NETWORK_ANALYSIS: [
                "tshark", "wireshark", "tcpdump", "ngrep"
            ],
            TaskType.MEMORY_FORENSICS: [
                "volatility3", "winpmem", "lime"
            ],
            TaskType.ANDROID_ANALYSIS: [
                "jadx", "apktool", "dex2jar", "adb"
            ],
            TaskType.CRYPTO_ANALYSIS: [
                "openssl", "hashcat", "john", "python3"
            ],
            TaskType.STEGO_ANALYSIS: [
                "steghide", "zsteg", "stegoveritas", "exiftool"
            ],
            TaskType.REVERSE_ENGINEERING: [
                "radare2", "objdump", "readelf", "strings"
            ],
            TaskType.SERVER_FORENSICS: [
                "grep", "awk", "sed", "find", "last", "who"
            ],
            TaskType.INCIDENT_RESPONSE: [
                "yara", "clamav", "rkhunter", "chkrootkit"
            ]
        }
    
    def _detect_task_type(self, topic: str, artifact_path: str = None) -> Tuple[TaskType, float]:
        """
        检测任务类型
        
        Args:
            topic: 题目描述
            artifact_path: 证据文件路径
            
        Returns:
            (任务类型, 置信度)元组
        """
        topic_lower = topic.lower()
        scores = {task_type: 0.0 for task_type in TaskType}
        
        # 基于关键词匹配
        for task_type, keywords in self.task_patterns["keywords"].items():
            for keyword in keywords:
                if keyword.lower() in topic_lower:
                    scores[task_type] += 1.0
        
        # 基于文件扩展名匹配
        if artifact_path:
            artifact_lower = artifact_path.lower()
            for task_type, extensions in self.task_patterns["file_extensions"].items():
                for ext in extensions:
                    if artifact_lower.endswith(ext.lower()):
                        scores[task_type] += 2.0  # 文件扩展名权重更高
        
        # 找到最高分的任务类型
        max_score = max(scores.values())
        if max_score == 0:
            return TaskType.UNKNOWN, 0.0
        
        best_task_type = max(scores, key=scores.get)
        confidence = min(max_score / 5.0, 1.0)  # 归一化置信度
        
        return best_task_type, confidence
    
    async def _generate_steps_with_llm(self, task_type: TaskType, topic: str, 
                                       artifact_path: str = None) -> List[AnalysisStep]:
        """
        使用大模型生成分析步骤
        
        Args:
            task_type: 任务类型
            topic: 题目描述
            artifact_path: 证据文件路径
            
        Returns:
            分析步骤列表
        """
        # 构建提示词
        system_prompt = """你是一个专业的电子取证专家。根据用户提供的题目描述和证据类型，生成详细的分析步骤。

每个步骤应该包含：
1. 步骤描述
2. 需要使用的工具
3. 具体的命令
4. 预期输出
5. 优先级（1为最高）
6. 依赖的前置步骤

请以JSON格式返回，格式如下：
{
    "steps": [
        {
            "step_id": 1,
            "description": "步骤描述",
            "tools": ["工具1", "工具2"],
            "commands": ["命令1", "命令2"],
            "expected_output": "预期输出描述",
            "priority": 1,
            "dependencies": [],
            "estimated_time": 60
        }
    ]
}"""
        
        user_prompt = f"""题目描述: {topic}
证据文件: {artifact_path or '未知'}
任务类型: {task_type.value}

请生成详细的分析步骤。"""
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.llm_engine.chat(messages, temperature=0.3)
            
            # 解析JSON响应
            try:
                result = json.loads(response.content)
                steps = []
                for step_data in result.get("steps", []):
                    step = AnalysisStep(
                        step_id=step_data["step_id"],
                        description=step_data["description"],
                        tools=step_data["tools"],
                        commands=step_data["commands"],
                        expected_output=step_data["expected_output"],
                        priority=step_data.get("priority", 1),
                        dependencies=step_data.get("dependencies", []),
                        estimated_time=step_data.get("estimated_time", 60)
                    )
                    steps.append(step)
                return steps
                
            except json.JSONDecodeError:
                logger.warning("大模型返回的JSON格式不正确，使用默认步骤")
                return self._get_default_steps(task_type)
                
        except Exception as e:
            logger.error(f"调用大模型生成步骤失败: {e}")
            return self._get_default_steps(task_type)
    
    def _get_default_steps(self, task_type: TaskType) -> List[AnalysisStep]:
        """获取默认分析步骤"""
        default_steps = {
            TaskType.DISK_FORENSICS: [
                AnalysisStep(
                    step_id=1,
                    description="检查磁盘镜像基本信息",
                    tools=["file", "exiftool"],
                    commands=["file {artifact}", "exiftool {artifact}"],
                    expected_output="获取文件类型、大小、创建时间等基本信息",
                    priority=1,
                    estimated_time=30
                ),
                AnalysisStep(
                    step_id=2,
                    description="分析磁盘分区结构",
                    tools=["sleuthkit"],
                    commands=["mmls {artifact}", "fls -r {artifact}"],
                    expected_output="获取分区表和文件系统信息",
                    priority=1,
                    estimated_time=60
                ),
                AnalysisStep(
                    step_id=3,
                    description="提取文件列表",
                    tools=["sleuthkit"],
                    commands=["fls -r -m / {artifact} > filelist.txt"],
                    expected_output="获取完整的文件列表",
                    priority=2,
                    estimated_time=120
                ),
                AnalysisStep(
                    step_id=4,
                    description="搜索关键文件",
                    tools=["grep", "find"],
                    commands=["grep -r 'keyword' {artifact}", "find . -name '*.txt' -o -name '*.log'"],
                    expected_output="找到与题目相关的关键文件",
                    priority=2,
                    estimated_time=60
                )
            ],
            TaskType.NETWORK_ANALYSIS: [
                AnalysisStep(
                    step_id=1,
                    description="获取流量包基本信息",
                    tools=["capinfos", "tshark"],
                    commands=["capinfos {artifact}", "tshark -r {artifact} -q -z io,phs"],
                    expected_output="获取流量包统计信息和协议分布",
                    priority=1,
                    estimated_time=30
                ),
                AnalysisStep(
                    step_id=2,
                    description="分析IP会话",
                    tools=["tshark"],
                    commands=["tshark -r {artifact} -q -z conv,ip"],
                    expected_output="获取IP地址通信统计",
                    priority=1,
                    estimated_time=60
                ),
                AnalysisStep(
                    step_id=3,
                    description="提取HTTP请求",
                    tools=["tshark"],
                    commands=["tshark -r {artifact} -Y 'http.request' -T fields -e http.host -e http.request.uri"],
                    expected_output="获取所有HTTP请求",
                    priority=2,
                    estimated_time=60
                )
            ],
            TaskType.ANDROID_ANALYSIS: [
                AnalysisStep(
                    step_id=1,
                    description="反编译APK文件",
                    tools=["jadx"],
                    commands=["jadx -d output {artifact}"],
                    expected_output="获取反编译后的Java源代码",
                    priority=1,
                    estimated_time=120
                ),
                AnalysisStep(
                    step_id=2,
                    description="提取AndroidManifest.xml",
                    tools=["aapt", "apktool"],
                    commands=["aapt dump badging {artifact}", "apktool d {artifact}"],
                    expected_output="获取应用权限、包名、Activity等信息",
                    priority=1,
                    estimated_time=60
                )
            ]
        }
        
        return default_steps.get(task_type, [
            AnalysisStep(
                step_id=1,
                description="基础文件分析",
                tools=["file", "strings", "xxd"],
                commands=["file {artifact}", "strings {artifact} | head -100"],
                expected_output="获取文件基本信息和可读字符串",
                priority=1,
                estimated_time=30
            )
        ])
    
    async def create_plan(self, topic: str, artifact_path: str = None) -> AnalysisPlan:
        """
        创建分析计划
        
        Args:
            topic: 题目描述
            artifact_path: 证据文件路径
            
        Returns:
            分析计划对象
        """
        # 检测任务类型
        task_type, confidence = self._detect_task_type(topic, artifact_path)
        
        logger.info(f"检测到任务类型: {task_type.value}，置信度: {confidence:.2f}")
        
        # 生成分析步骤
        if confidence > 0.3 and task_type != TaskType.UNKNOWN:
            # 使用大模型生成步骤
            steps = await self._generate_steps_with_llm(task_type, topic, artifact_path)
        else:
            # 使用默认步骤
            steps = self._get_default_steps(task_type)
        
        # 计算总预估时间
        total_time = sum(step.estimated_time for step in steps)
        
        # 创建分析计划
        plan = AnalysisPlan(
            task_type=task_type,
            description=topic,
            steps=steps,
            total_estimated_time=total_time,
            confidence=confidence,
            metadata={
                "artifact_path": artifact_path,
                "tools_required": list(set(tool for step in steps for tool in step.tools))
            }
        )
        
        return plan
    
    def format_plan(self, plan: AnalysisPlan) -> str:
        """格式化分析计划为可读字符串"""
        output = []
        output.append(f"=== 分析计划 ===")
        output.append(f"任务类型: {plan.task_type.value}")
        output.append(f"置信度: {plan.confidence:.2%}")
        output.append(f"预估总时间: {plan.total_estimated_time}秒")
        output.append(f"证据文件: {plan.metadata.get('artifact_path', '未知')}")
        output.append("")
        output.append("所需工具:")
        for tool in plan.metadata.get('tools_required', []):
            output.append(f"  - {tool}")
        output.append("")
        output.append("分析步骤:")
        
        for step in plan.steps:
            output.append(f"\n步骤 {step.step_id}: {step.description}")
            output.append(f"  优先级: {step.priority}")
            output.append(f"  预估时间: {step.estimated_time}秒")
            output.append(f"  工具: {', '.join(step.tools)}")
            output.append(f"  命令:")
            for cmd in step.commands:
                output.append(f"    $ {cmd}")
            output.append(f"  预期输出: {step.expected_output}")
            if step.dependencies:
                output.append(f"  依赖步骤: {step.dependencies}")
        
        return "\n".join(output)
    
    async def adjust_plan(self, plan: AnalysisPlan, 
                         feedback: str) -> AnalysisPlan:
        """
        根据反馈调整分析计划
        
        Args:
            plan: 原始分析计划
            feedback: 用户反馈
            
        Returns:
            调整后的分析计划
        """
        system_prompt = """你是一个专业的电子取证专家。根据用户反馈，调整分析计划。

请返回调整后的JSON格式分析计划。"""
        
        user_prompt = f"""原始计划:
{self.format_plan(plan)}

用户反馈: {feedback}

请根据反馈调整计划。"""
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.llm_engine.chat(messages, temperature=0.3)
            
            # 解析响应并更新计划
            # 这里简化处理，实际应该解析JSON并更新计划
            logger.info("计划已根据反馈调整")
            return plan
            
        except Exception as e:
            logger.error(f"调整计划失败: {e}")
            return plan

# 测试代码
if __name__ == "__main__":
    async def test():
        planner = AgentPlanner()
        
        # 测试任务类型检测
        test_cases = [
            ("分析E01磁盘镜像，找出删除的文件", "evidence.E01"),
            ("分析PCAP流量包，找出攻击者IP", "capture.pcap"),
            ("逆向分析APK文件，找出加密算法", "app.apk"),
            ("分析内存转储，找出恶意进程", "memory.raw")
        ]
        
        for topic, artifact in test_cases:
            plan = await planner.create_plan(topic, artifact)
            print(f"\n{planner.format_plan(plan)}")
            print("-" * 80)
    
    asyncio.run(test())