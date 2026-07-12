"""
磁盘取证知识提取器 - 从sleuthkit手册中提取磁盘取证知识
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

class DiskForensicsExtractor:
    """磁盘取证知识提取器"""
    
    def __init__(self, source_dir: str, output_dir: str):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.knowledge: List[ForensicKnowledge] = []
    
    def extract_knowledge(self):
        """提取磁盘取证知识"""
        print("开始提取磁盘取证知识...")
        
        man_dir = self.source_dir / "man"
        
        if not man_dir.exists():
            print(f"手册目录不存在: {man_dir}")
            return
        
        # 遍历所有手册文件
        for man_file in man_dir.glob("*.1"):
            self._extract_from_man(man_file)
        
        print(f"共提取 {len(self.knowledge)} 条知识")
    
    def _extract_from_man(self, man_file: Path):
        """从手册文件提取知识"""
        try:
            content = man_file.read_text(encoding='utf-8', errors='ignore')
            
            # 提取命令名称
            command_name = man_file.stem
            
            # 提取描述
            description = self._extract_description(content)
            
            # 提取用法
            usage = self._extract_usage(content)
            
            # 提取示例
            examples = self._extract_examples(content)
            
            # 提取选项
            options = self._extract_options(content)
            
            # 生成用例
            use_cases = self._generate_use_cases(command_name, description)
            
            if description:
                knowledge = ForensicKnowledge(
                    knowledge_id=f"sleuthkit_{command_name}",
                    title=f"TSK {command_name}",
                    category="磁盘取证",
                    tool="sleuthkit",
                    description=description,
                    commands=[usage] if usage else [f"{command_name} [options] image"],
                    use_cases=use_cases,
                    examples=examples,
                    tips=options[:5] if options else []
                )
                
                self.knowledge.append(knowledge)
                print(f"  提取命令: {command_name}")
        
        except Exception as e:
            print(f"  提取失败 {man_file}: {e}")
    
    def _extract_description(self, content: str) -> str:
        """提取描述"""
        # 提取NAME部分
        name_match = re.search(r'NAME\n(.*?)(?=\n[A-Z]+|\Z)', content, re.DOTALL)
        if name_match:
            name_text = name_match.group(1).strip()
            # 清理格式
            name_text = re.sub(r'\\f[BIRP]', '', name_text)
            return name_text[:500]
        
        # 提取第一段
        lines = content.split('\n')
        desc_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('.') and not line.startswith('\\'):
                desc_lines.append(line)
                if len(' '.join(desc_lines)) > 100:
                    break
        
        return ' '.join(desc_lines)[:500] if desc_lines else ""
    
    def _extract_usage(self, content: str) -> str:
        """提取用法"""
        # 提取SYNOPSIS部分
        synopsis_match = re.search(r'SYNOPSIS\n(.*?)(?=\n[A-Z]+|\Z)', content, re.DOTALL)
        if synopsis_match:
            synopsis = synopsis_match.group(1).strip()
            # 清理格式
            synopsis = re.sub(r'\\f[BIRP]', '', synopsis)
            synopsis = re.sub(r'\n', ' ', synopsis)
            return synopsis[:200]
        
        return ""
    
    def _extract_examples(self, content: str) -> List[str]:
        """提取示例"""
        examples = []
        
        # 提取EXAMPLES部分
        example_match = re.search(r'EXAMPLES?\n(.*?)(?=\n[A-Z]+|\Z)', content, re.DOTALL)
        if example_match:
            example_text = example_match.group(1)
            # 提取命令示例
            cmd_pattern = r'\$?\s*(tsk_\w+|fls|icat|mmls|blkls|ffind|ils|istat|img_stat)\s+[^\n]+'
            matches = re.findall(cmd_pattern, example_text)
            examples.extend(matches[:5])
        
        return examples
    
    def _extract_options(self, content: str) -> List[str]:
        """提取选项"""
        options = []
        
        # 提取OPTIONS部分
        option_match = re.search(r'OPTIONS\n(.*?)(?=\n[A-Z]+|\Z)', content, re.DOTALL)
        if option_match:
            option_text = option_match.group(1)
            # 提取选项说明
            opt_pattern = r'-([a-zA-Z])\s+(.*?)(?=\n\s*-|\Z)'
            matches = re.findall(opt_pattern, option_text, re.DOTALL)
            
            for opt, desc in matches[:10]:
                desc = desc.strip()
                desc = re.sub(r'\n', ' ', desc)
                options.append(f"-{opt}: {desc[:100]}")
        
        return options
    
    def _generate_use_cases(self, command_name: str, description: str) -> List[str]:
        """生成用例"""
        use_cases = []
        
        # 根据命令名称推断用例
        use_case_mapping = {
            "fls": ["列出文件系统内容", "恢复删除文件", "查看文件时间线"],
            "icat": ["提取文件内容", "恢复特定文件", "查看文件数据"],
            "mmls": ["查看分区表", "分析磁盘布局", "识别分区类型"],
            "blkls": ["查看数据块", "分析未分配空间", "恢复文件碎片"],
            "ffind": ["查找文件名", "根据inode找文件", "定位文件位置"],
            "ils": ["列出inode信息", "查看文件元数据", "分析文件属性"],
            "istat": ["查看inode详情", "分析文件时间", "查看文件大小"],
            "img_stat": ["查看镜像信息", "分析镜像格式", "验证镜像完整性"],
            "img_cat": ["提取镜像数据", "导出原始数据", "转换镜像格式"],
            "mactime": ["生成时间线", "分析文件活动", "事件关联"],
            "tsk_recover": ["恢复删除文件", "文件恢复", "数据恢复"],
            "tsk_loaddb": ["加载数据库", "导入证据", "批量分析"],
            "hfind": ["查找哈希值", "哈希匹配", "文件校验"],
            "sigfind": ["查找文件签名", "识别文件类型", "文件雕刻"],
            "sorter": ["排序文件", "分类文件", "文件分析"],
        }
        
        if command_name in use_case_mapping:
            use_cases = use_case_mapping[command_name]
        elif description:
            use_cases = [description[:50]]
        
        return use_cases
    
    def save_knowledge(self):
        """保存知识"""
        output_file = self.output_dir / "knowledge" / "disk_forensics.json"
        os.makedirs(output_file.parent, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(k) for k in self.knowledge], f, 
                     ensure_ascii=False, indent=2)
        
        print(f"\n保存完成: {output_file}")
        print(f"共 {len(self.knowledge)} 条知识")

def main():
    """主函数"""
    source_dir = r"E:\temp_sleuthkit"
    output_dir = r"E:\forensic-ai-platform"
    
    extractor = DiskForensicsExtractor(source_dir, output_dir)
    extractor.extract_knowledge()
    extractor.save_knowledge()

if __name__ == "__main__":
    main()
