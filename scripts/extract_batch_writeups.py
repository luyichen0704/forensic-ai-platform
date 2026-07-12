"""
CTF Writeup批量提取器 - 批量从ctfs/write-ups仓库中提取取证案例
"""
import os
import json
import re
import subprocess
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

class BatchWriteupExtractor:
    """批量Writeup提取器"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.cases: List[ForensicCase] = []
        
        # 取证相关关键词
        self.forensic_keywords = [
            "forensic", "forensics", "取证", "memory", "disk", "network",
            "pcap", "capture", "traffic", "volatility", "autopsy",
            "sleuthkit", "e01", "image", "dump", "malware", "reverse",
            "stego", "steganography", "crypto"
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
            "hashcat": r"hashcat",
            "john": r"john",
            "openssl": r"openssl",
        }
    
    def extract_from_repo(self, repo_url: str, year: int):
        """从仓库提取案例"""
        print(f"\n{'='*60}")
        print(f"处理 {year} 年CTF Writeup")
        print(f"{'='*60}")
        
        # 克隆仓库（浅克隆，只获取文件列表）
        temp_dir = Path(f"E:\\temp_writeups_{year}")
        
        if not temp_dir.exists():
            print(f"克隆仓库: {repo_url}")
            result = subprocess.run(
                ["git", "clone", "--depth", "1", "--no-checkout", repo_url, str(temp_dir)],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                print(f"克隆失败: {result.stderr}")
                return
        
        # 获取文件列表
        print("获取文件列表...")
        result = subprocess.run(
            ["git", "-C", str(temp_dir), "ls-tree", "--name-only", "HEAD"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"获取文件列表失败: {result.stderr}")
            return
        
        # 解析比赛目录
        lines = result.stdout.strip().split('\n')
        comp_dirs = [line for line in lines if not line.startswith('.') and not line.endswith('.md')]
        
        print(f"找到 {len(comp_dirs)} 个比赛目录")
        
        # 遍历每个比赛
        for comp_dir in comp_dirs:
            self._process_competition(temp_dir, comp_dir, year)
        
        # 清理临时目录
        print(f"清理临时目录...")
        subprocess.run(["Remove-Item", "-Path", str(temp_dir), "-Recurse", "-Force"], 
                       capture_output=True, shell=True)
        
        print(f"\n共提取 {len(self.cases)} 个案例")
    
    def _process_competition(self, repo_dir: Path, comp_name: str, year: int):
        """处理比赛"""
        print(f"\n处理比赛: {comp_name}")
        
        # 获取比赛目录下的文件
        result = subprocess.run(
            ["git", "-C", str(repo_dir), "ls-tree", "--name-only", f"HEAD:{comp_name}"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return
        
        # 解析题目目录
        lines = result.stdout.strip().split('\n')
        challenge_dirs = [line for line in lines if not line.startswith('.')]
        
        print(f"  找到 {len(challenge_dirs)} 个题目")
        
        # 遍历每个题目
        for challenge_dir in challenge_dirs:
            self._process_challenge(repo_dir, comp_name, challenge_dir, year)
    
    def _process_challenge(self, repo_dir: Path, comp_name: str, challenge_name: str, year: int):
        """处理题目"""
        # 检查是否是取证相关
        if not self._is_forensic_challenge(challenge_name):
            return
        
        try:
            # 获取README内容
            readme_path = f"{comp_name}/{challenge_name}/README.md"
            result = subprocess.run(
                ["git", "-C", str(repo_dir), "show", f"HEAD:{readme_path}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                # 尝试其他README文件
                for readme_name in ["README", "readme.md", "writeup.md", "solution.md"]:
                    alt_path = f"{comp_name}/{challenge_name}/{readme_name}"
                    result = subprocess.run(
                        ["git", "-C", str(repo_dir), "show", f"HEAD:{alt_path}"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        break
            
            if result.returncode != 0:
                return
            
            content = result.stdout
            
            # 提取案例信息
            case = self._extract_case(content, comp_name, challenge_name, year)
            if case:
                self.cases.append(case)
                print(f"    提取: {challenge_name}")
        
        except Exception as e:
            pass
    
    def _is_forensic_challenge(self, challenge_name: str) -> bool:
        """检查是否是取证题目"""
        name_lower = challenge_name.lower()
        
        for keyword in self.forensic_keywords:
            if keyword in name_lower:
                return True
        
        return False
    
    def _extract_case(self, content: str, comp_name: str, challenge_name: str, year: int) -> ForensicCase:
        """提取案例"""
        # 提取标题
        title = self._extract_title(content, challenge_name)
        
        # 识别类别
        category = self._identify_category(content, challenge_name)
        
        # 提取工具
        tools = self._extract_tools(content)
        
        # 提取技术
        techniques = self._extract_techniques(content)
        
        # 提取Flag
        flags = self._extract_flags(content)
        
        # 生成ID
        content_hash = hashlib.md5(content.encode()).hexdigest()[:16]
        case_id = f"{comp_name}_{year}_{content_hash}"
        
        # 生成标签
        tags = [category, comp_name] if category else [comp_name]
        tags.extend(tools[:3])
        
        return ForensicCase(
            case_id=case_id,
            title=title,
            category=category or "Misc",
            competition=comp_name,
            year=year,
            difficulty=self._estimate_difficulty(content),
            tools_used=tools,
            techniques=techniques,
            description=self._extract_description(content),
            solution_steps=self._extract_solution_steps(content),
            key_findings=self._extract_findings(content),
            flags=flags,
            tags=list(set(tags))[:10],
            content_hash=content_hash
        )
    
    def _extract_title(self, content: str, challenge_name: str) -> str:
        """提取标题"""
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        
        return challenge_name.replace('-', ' ').title()
    
    def _identify_category(self, content: str, challenge_name: str) -> str:
        """识别类别"""
        content_lower = content.lower()
        name_lower = challenge_name.lower()
        
        categories = {
            "Forensics": ["forensic", "forensics", "取证", "memory", "disk", "network", "pcap"],
            "Crypto": ["crypto", "cipher", "encrypt", "decrypt", "密码"],
            "Web": ["web", "http", "sql", "xss"],
            "Pwn": ["pwn", "buffer", "overflow", "shellcode"],
            "Reverse": ["reverse", "逆向", "disassemble"],
            "Stego": ["stego", "steganography", "隐写"],
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in content_lower or keyword in name_lower:
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
        
        code_blocks = re.findall(r'```[\s\S]*?```', content)
        for block in code_blocks[:3]:
            findings.append(block[:200])
        
        return findings
    
    def _extract_description(self, content: str) -> str:
        """提取描述"""
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
        raw_file = self.output_dir / "raw" / "ctf_batch_cases.json"
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
        
        print(f"\n保存完成: {len(new_cases)} 个新案例")
        print(f"总案例数: {len(existing_cases)}")

def main():
    """主函数"""
    output_dir = r"E:\forensic-ai-platform\cases"
    
    extractor = BatchWriteupExtractor(output_dir)
    
    # 处理2015年
    extractor.extract_from_repo(
        "https://github.com/ctfs/write-ups-2015.git",
        2015
    )
    
    # 保存结果
    extractor.save_cases()

if __name__ == "__main__":
    main()
