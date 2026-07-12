"""
CTF Writeup提取器 - 从ctfs/write-ups仓库中提取取证案例
"""
import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
import hashlib

@dataclass
class ForensicCase:
    """取证案例"""
    case_id: str
    title: str
    category: str
    competition: str
    year: int
    difficulty: str
    tools_used: List[str]
    techniques: List[str]
    description: str
    solution_steps: List[str]
    key_findings: List[str]
    flags: List[str]
    tags: List[str]
    content_hash: str

class CTFWriteupExtractor:
    """CTF Writeup提取器"""
    
    def __init__(self, source_dir: str, output_dir: str):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.cases: List[ForensicCase] = []
        
        # 取证相关关键词
        self.forensic_keywords = [
            "forensic", "forensics", "取证", "memory", "disk", "network",
            "pcap", "capture", "traffic", "volatility", "autopsy",
            "sleuthkit", "e01", "image", "dump", "malware", "reverse",
            "stego", "steganography", "crypto", "web", "pwn"
        ]
        
        # 工具识别
        self.tool_patterns = {
            "volatility": r"vol(?:atility)?[\s\-]",
            "tshark": r"tshark[\s\-]",
            "wireshark": r"wireshark",
            "sleuthkit": r"(?:fls|icat|mmls|tsk)",
            "foremost": r"foremost",
            "binwalk": r"binwalk",
            "strings": r"strings[\s\-]",
            "exiftool": r"exiftool",
            "steghide": r"steghide",
            "zsteg": r"zsteg",
            "stegsolve": r"stegsolve",
            "jadx": r"jadx",
            "apktool": r"apktool",
            "hashcat": r"hashcat",
            "john": r"john",
            "openssl": r"openssl",
            "xxd": r"xxd",
            "radare2": r"r2",
            "gdb": r"gdb",
        }
    
    def extract_from_ctf(self, year: int):
        """从CTF Writeup中提取案例"""
        print(f"开始扫描 {year} 年CTF Writeup...")
        
        # 遍历所有比赛目录
        for comp_dir in self.source_dir.iterdir():
            if comp_dir.is_dir() and not comp_dir.name.startswith('.'):
                print(f"处理比赛: {comp_dir.name}")
                self._extract_from_competition(comp_dir, year)
        
        print(f"共提取 {len(self.cases)} 个案例")
    
    def _extract_from_competition(self, comp_dir: Path, year: int):
        """从比赛目录提取案例"""
        comp_name = comp_dir.name
        
        # 遍历所有题目目录
        for challenge_dir in comp_dir.iterdir():
            if challenge_dir.is_dir():
                # 检查是否是取证相关
                if self._is_forensic_challenge(challenge_dir):
                    self._extract_from_challenge(challenge_dir, comp_name, year)
    
    def _is_forensic_challenge(self, challenge_dir: Path) -> bool:
        """检查是否是取证题目"""
        dir_name = challenge_dir.name.lower()
        path_str = str(challenge_dir).lower()
        
        # 检查目录名
        for keyword in self.forensic_keywords:
            if keyword in dir_name:
                return True
        
        # 检查README内容
        readme_files = list(challenge_dir.glob("README*")) + list(challenge_dir.glob("*.md"))
        for readme in readme_files:
            try:
                content = readme.read_text(encoding='utf-8', errors='ignore').lower()
                for keyword in self.forensic_keywords:
                    if keyword in content:
                        return True
            except:
                pass
        
        return False
    
    def _extract_from_challenge(self, challenge_dir: Path, comp_name: str, year: int):
        """从题目目录提取案例"""
        try:
            # 查找README文件
            readme_content = ""
            readme_files = list(challenge_dir.glob("README*")) + list(challenge_dir.glob("*.md"))
            
            for readme in readme_files:
                try:
                    readme_content = readme.read_text(encoding='utf-8', errors='ignore')
                    break
                except:
                    continue
            
            if not readme_content:
                return
            
            # 提取标题
            title = self._extract_title(readme_content, challenge_dir)
            
            # 识别类别
            category = self._identify_category(readme_content, challenge_dir)
            
            # 提取工具
            tools = self._extract_tools(readme_content)
            
            # 提取技术
            techniques = self._extract_techniques(readme_content)
            
            # 提取Flag
            flags = self._extract_flags(readme_content)
            
            # 提取解题步骤
            steps = self._extract_solution_steps(readme_content)
            
            # 生成ID
            content_hash = hashlib.md5(readme_content.encode()).hexdigest()[:16]
            case_id = f"{comp_name}_{year}_{content_hash}"
            
            # 生成标签
            tags = [category, comp_name] if category else [comp_name]
            tags.extend(tools[:3])
            
            case = ForensicCase(
                case_id=case_id,
                title=title,
                category=category or "Misc",
                competition=comp_name,
                year=year,
                difficulty=self._estimate_difficulty(readme_content),
                tools_used=tools,
                techniques=techniques,
                description=self._extract_description(readme_content),
                solution_steps=steps,
                key_findings=self._extract_findings(readme_content),
                flags=flags,
                tags=list(set(tags))[:10],
                content_hash=content_hash
            )
            
            self.cases.append(case)
            print(f"  提取案例: {title}")
            
        except Exception as e:
            print(f"  提取失败: {e}")
    
    def _extract_title(self, content: str, challenge_dir: Path) -> str:
        """提取标题"""
        # 从Markdown标题提取
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        
        # 使用目录名
        return challenge_dir.name.replace('-', ' ').title()
    
    def _identify_category(self, content: str, challenge_dir: Path) -> str:
        """识别类别"""
        content_lower = content.lower()
        dir_name = challenge_dir.name.lower()
        
        categories = {
            "Forensics": ["forensic", "forensics", "取证", "memory", "disk", "network", "pcap"],
            "Crypto": ["crypto", "cipher", "encrypt", "decrypt", "密码"],
            "Web": ["web", "http", "sql", "xss", "injection"],
            "Pwn": ["pwn", "buffer", "overflow", "shellcode", "rop"],
            "Reverse": ["reverse", "reverse engineering", "逆向", "disassemble"],
            "Stego": ["stego", "steganography", "隐写", "lsb"],
            "Misc": ["misc", "miscellaneous", "杂项"],
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in content_lower or keyword in dir_name:
                    return category
        
        return "Misc"
    
    def _extract_tools(self, content: str) -> List[str]:
        """提取工具"""
        tools = []
        
        for tool_name, pattern in self.tool_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                tools.append(tool_name)
        
        return list(set(tools))
    
    def _extract_techniques(self, content: str) -> List[str]:
        """提取技术点"""
        techniques = []
        
        patterns = {
            "内存分析": r"(?:memory|内存|volatility).*(?:analysis|分析|dump)",
            "流量分析": r"(?:traffic|流量|pcap|capture).*(?:analysis|分析)",
            "文件恢复": r"(?:recover|恢复|extract|提取).*(?:file|文件)",
            "密码破解": r"(?:crack|破解|brute|爆破).*(?:password|密码)",
            "隐写提取": r"(?:stego|隐写|hide|隐藏).*(?:extract|提取)",
            "逆向分析": r"(?:reverse|逆向|disassemble|反汇编).*(?:analysis|分析)",
        }
        
        for technique, pattern in patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                techniques.append(technique)
        
        return techniques
    
    def _extract_flags(self, content: str) -> List[str]:
        """提取Flag"""
        flags = []
        
        patterns = [
            r'flag\{[^}]+\}',
            r'FLAG\{[^}]+\}',
            r'Flag\{[^}]+\}',
            r'ctf\{[^}]+\}',
            r'CTF\{[^}]+\}',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            flags.extend(matches)
        
        return list(set(flags))
    
    def _extract_solution_steps(self, content: str) -> List[str]:
        """提取解题步骤"""
        steps = []
        
        # 查找有序列表
        step_pattern = r'(?:^|\n)(?:\d+[\.\)、]|[-*])\s+(.+?)(?=\n\d+[\.\)、]|[-*]|\Z)'
        matches = re.findall(step_pattern, content, re.DOTALL)
        
        for match in matches[:10]:
            step = match.strip()
            if step and len(step) > 10:
                steps.append(step)
        
        return steps
    
    def _extract_findings(self, content: str) -> List[str]:
        """提取关键发现"""
        findings = []
        
        # 查找代码块
        code_blocks = re.findall(r'```[\s\S]*?```', content)
        for block in code_blocks[:3]:
            findings.append(block[:200])
        
        return findings
    
    def _extract_description(self, content: str) -> str:
        """提取描述"""
        # 提取前200字
        lines = content.split('\n')
        desc_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('!'):
                desc_lines.append(line)
                if len(' '.join(desc_lines)) > 200:
                    break
        
        return ' '.join(desc_lines)[:300]
    
    def _estimate_difficulty(self, content: str) -> str:
        """估算难度"""
        if len(content) > 5000:
            return "hard"
        elif len(content) > 2000:
            return "medium"
        else:
            return "easy"
    
    def save_cases(self):
        """保存案例"""
        # 保存原始数据
        raw_file = self.output_dir / "raw" / f"ctf_{self.cases[0].competition}_{self.cases[0].year}.json" if self.cases else None
        
        if raw_file:
            os.makedirs(raw_file.parent, exist_ok=True)
            with open(raw_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(c) for c in self.cases], f, 
                         ensure_ascii=False, indent=2)
        
        # 追加到总案例文件
        all_cases_file = self.output_dir / "raw" / "all_cases.json"
        existing_cases = []
        
        if all_cases_file.exists():
            with open(all_cases_file, 'r', encoding='utf-8') as f:
                existing_cases = json.load(f)
        
        # 合并案例
        existing_ids = {c.get("case_id") for c in existing_cases}
        new_cases = [asdict(c) for c in self.cases if c.case_id not in existing_ids]
        existing_cases.extend(new_cases)
        
        with open(all_cases_file, 'w', encoding='utf-8') as f:
            json.dump(existing_cases, f, ensure_ascii=False, indent=2)
        
        print(f"保存完成: {len(new_cases)} 个新案例")

def main():
    """主函数"""
    source_dir = r"E:\temp_writeups_2017"
    output_dir = r"E:\forensic-ai-platform\cases"
    
    extractor = CTFWriteupExtractor(source_dir, output_dir)
    extractor.extract_from_ctf(2017)
    extractor.save_cases()

if __name__ == "__main__":
    main()
