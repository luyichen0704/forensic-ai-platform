"""
内存取证知识提取器 - 从volatility3文档中提取内存取证知识
"""
import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class ForensicKnowledge:
    """取证知识"""
    knowledge_id: str
    title: str
    category: str
    tool: str
    description: str
    commands: List[str]
    use_cases: List[str]
    examples: List[str]
    tips: List[str]

class MemoryForensicsExtractor:
    """内存取证知识提取器"""
    
    def __init__(self, source_dir: str, output_dir: str):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.knowledge: List[ForensicKnowledge] = []
    
    def extract_knowledge(self):
        """提取内存取证知识"""
        print("开始提取内存取证知识...")
        
        # 提取插件知识
        self._extract_plugin_knowledge()
        
        # 提取使用教程
        self._extract_tutorials()
        
        print(f"共提取 {len(self.knowledge)} 条知识")
    
    def _extract_plugin_knowledge(self):
        """提取插件知识"""
        plugins_dir = self.source_dir / "volatility3" / "framework" / "plugins"
        
        if not plugins_dir.exists():
            print(f"插件目录不存在: {plugins_dir}")
            return
        
        # 遍历Windows插件
        windows_dir = plugins_dir / "windows"
        if windows_dir.exists():
            for plugin_file in windows_dir.glob("*.py"):
                self._extract_from_plugin(plugin_file, "windows")
        
        # 遍历Linux插件
        linux_dir = plugins_dir / "linux"
        if linux_dir.exists():
            for plugin_file in linux_dir.glob("*.py"):
                self._extract_from_plugin(plugin_file, "linux")
        
        # 遍历Mac插件
        mac_dir = plugins_dir / "mac"
        if mac_dir.exists():
            for plugin_file in mac_dir.glob("*.py"):
                self._extract_from_plugin(plugin_file, "mac")
    
    def _extract_from_plugin(self, plugin_file: Path, os_type: str):
        """从插件文件提取知识"""
        try:
            content = plugin_file.read_text(encoding='utf-8', errors='ignore')
            
            # 提取插件名称
            plugin_name = plugin_file.stem
            
            # 提取描述
            description = self._extract_description(content)
            
            # 提取命令
            commands = self._extract_commands(content, plugin_name, os_type)
            
            # 提取用例
            use_cases = self._extract_use_cases(content, plugin_name)
            
            if description or commands:
                knowledge = ForensicKnowledge(
                    knowledge_id=f"{os_type}_{plugin_name}",
                    title=f"{os_type}.{plugin_name}",
                    category="内存取证",
                    tool="volatility3",
                    description=description,
                    commands=commands,
                    use_cases=use_cases,
                    examples=[],
                    tips=[]
                )
                
                self.knowledge.append(knowledge)
                print(f"  提取插件: {os_type}.{plugin_name}")
        
        except Exception as e:
            print(f"  提取失败 {plugin_file}: {e}")
    
    def _extract_description(self, content: str) -> str:
        """提取描述"""
        # 提取docstring
        match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if match:
            return match.group(1).strip()[:500]
        
        # 提取注释
        lines = content.split('\n')
        desc_lines = []
        for line in lines:
            line = line.strip()
            if line.startswith('#') and len(line) > 2:
                desc_lines.append(line[2:])
            elif desc_lines:
                break
        
        return ' '.join(desc_lines)[:500] if desc_lines else ""
    
    def _extract_commands(self, content: str, plugin_name: str, os_type: str) -> List[str]:
        """提取命令"""
        commands = []
        
        # 生成标准命令
        commands.append(f"vol -f <memory_dump> {os_type}.{plugin_name}")
        
        # 提取命令行参数
        arg_pattern = r'(?:add_argument|argparse)\s*\(\s*["\']([^"\']+)["\']'
        matches = re.findall(arg_pattern, content)
        
        for match in matches[:3]:
            commands.append(f"vol -f <memory_dump> {os_type}.{plugin_name} {match}")
        
        return commands
    
    def _extract_use_cases(self, content: str, plugin_name: str) -> List[str]:
        """提取用例"""
        use_cases = []
        
        # 根据插件名称推断用例
        use_case_mapping = {
            "pslist": ["列出所有进程", "检测恶意进程", "分析进程树"],
            "pstree": ["显示进程父子关系", "分析进程创建链"],
            "netscan": ["扫描网络连接", "检测异常连接", "分析C2通信"],
            "filescan": ["扫描文件对象", "恢复删除文件"],
            "cmdline": ["提取命令行参数", "分析恶意命令"],
            "dlllist": ["列出加载的DLL", "检测注入的DLL"],
            "handles": ["列出进程句柄", "分析资源访问"],
            "malfind": ["检测恶意代码注入", "查找隐藏代码"],
            "psxview": ["检测进程隐藏", "交叉验证进程列表"],
            "hivelist": ["列出注册表hive", "分析注册表"],
            "hashdump": ["提取密码哈希", "离线密码破解"],
            "timeliner": ["生成时间线", "事件关联分析"],
        }
        
        if plugin_name in use_case_mapping:
            use_cases = use_case_mapping[plugin_name]
        
        return use_cases
    
    def _extract_tutorials(self):
        """提取教程"""
        doc_dir = self.source_dir / "doc" / "source"
        
        if not doc_dir.exists():
            return
        
        # 遍历教程文件
        for tutorial_file in doc_dir.glob("getting-started-*.rst"):
            try:
                content = tutorial_file.read_text(encoding='utf-8', errors='ignore')
                
                # 提取操作系统类型
                os_type = "unknown"
                if "windows" in tutorial_file.name:
                    os_type = "windows"
                elif "linux" in tutorial_file.name:
                    os_type = "linux"
                elif "mac" in tutorial_file.name:
                    os_type = "mac"
                
                # 提取命令示例
                commands = self._extract_tutorial_commands(content)
                
                # 创建教程知识
                knowledge = ForensicKnowledge(
                    knowledge_id=f"tutorial_{os_type}",
                    title=f"Volatility3 {os_type.title()} 教程",
                    category="内存取证教程",
                    tool="volatility3",
                    description=f"Volatility3 {os_type} 内存取证教程",
                    commands=commands,
                    use_cases=["内存取证入门", "Volatility3使用"],
                    examples=self._extract_tutorial_examples(content),
                    tips=self._extract_tutorial_tips(content)
                )
                
                self.knowledge.append(knowledge)
                print(f"  提取教程: {os_type}")
            
            except Exception as e:
                print(f"  提取教程失败: {e}")
    
    def _extract_tutorial_commands(self, content: str) -> List[str]:
        """提取教程命令"""
        commands = []
        
        # 提取代码块中的命令
        code_blocks = re.findall(r'.. code-block:: shell-session\n\n(.*?)(?=\n\n|\Z)', content, re.DOTALL)
        
        for block in code_blocks:
            lines = block.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('$ '):
                    commands.append(line[2:])
        
        return commands[:10]
    
    def _extract_tutorial_examples(self, content: str) -> List[str]:
        """提取教程示例"""
        examples = []
        
        # 提取示例部分
        example_pattern = r'Example\n.*?\n(.*?)(?=\n\n|\Z)'
        matches = re.findall(example_pattern, content, re.DOTALL)
        
        for match in matches[:3]:
            examples.append(match.strip()[:200])
        
        return examples
    
    def _extract_tutorial_tips(self, content: str) -> List[str]:
        """提取教程提示"""
        tips = []
        
        # 提取note部分
        note_pattern = r'\.\. note::\s*(.*?)(?=\n\n|\Z)'
        matches = re.findall(note_pattern, content, re.DOTALL)
        
        for match in matches[:3]:
            tips.append(match.strip()[:200])
        
        return tips
    
    def save_knowledge(self):
        """保存知识"""
        output_file = self.output_dir / "knowledge" / "memory_forensics.json"
        os.makedirs(output_file.parent, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(k) for k in self.knowledge], f, 
                     ensure_ascii=False, indent=2)
        
        print(f"\n保存完成: {output_file}")
        print(f"共 {len(self.knowledge)} 条知识")

def main():
    """主函数"""
    source_dir = r"E:\temp_volatility3"
    output_dir = r"E:\forensic-ai-platform"
    
    extractor = MemoryForensicsExtractor(source_dir, output_dir)
    extractor.extract_knowledge()
    extractor.save_knowledge()

if __name__ == "__main__":
    main()
