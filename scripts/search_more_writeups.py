"""
搜索更多CTF和取证Writeup仓库
创建列表供用户人工挑选
"""
import requests
import json
import time
from typing import List, Dict, Any
from pathlib import Path
import os

class WriteupRepoSearcher:
    """Writeup仓库搜索器"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.repos: List[Dict[str, Any]] = []
        
        # 搜索关键词列表
        self.search_queries = [
            # CTF Writeup通用搜索
            "CTF writeup forensics",
            "CTF writeup misc",
            "CTF writeup crypto",
            "CTF writeup reverse",
            "CTF writeup pwn",
            "CTF writeup web",
            
            # 取证专项搜索
            "digital forensics writeup",
            "memory forensics writeup",
            "disk forensics writeup",
            "network forensics PCAP",
            "malware analysis writeup",
            "incident response writeup",
            "DFIR writeup",
            
            # 中文搜索
            "电子取证 writeup",
            "取证 CTF",
            "美亚杯 writeup",
            "数证杯 writeup",
            "FIC 取证",
            "盘古石 取证",
            
            # 年份搜索
            "CTF writeup 2024",
            "CTF writeup 2025",
            "forensics CTF 2024",
            "forensics CTF 2025",
            
            # 特定比赛搜索
            "picoCTF writeup",
            "CTFtime writeup",
            "HackTheBox forensics",
            "TryHackMe forensics",
            
            # 工具相关
            "volatility writeup",
            "autopsy writeup",
            "sleuthkit writeup",
            "Wireshark PCAP writeup",
        ]
        
        # 已知的高质量仓库
        self.known_repos = [
            # CTF Writeup集合
            "ctfs/write-ups-2013",
            "ctfs/write-ups-2014",
            "ctfs/write-ups-2015",
            "ctfs/write-ups-2016",
            "ctfs/write-ups-2017",
            "ctfs/write-ups-2018",
            "ctfs/write-ups-2019",
            "ctfs/write-ups-2020",
            "ctfs/write-ups-2021",
            "ctfs/write-ups-2022",
            "ctfs/write-ups-2023",
            "ctfs/write-ups-2024",
            
            # 取证工具
            "volatilityfoundation/volatility3",
            "volatilityfoundation/volatility",
            "sleuthkit/sleuthkit",
            "ArsenalRecon/Arsenal-Image-Mounter",
            
            # 取证资源
            "ForensicArtifacts/artifacts",
            "EricZimmerman/KapeFiles",
            "EricZimmerman/ericzimmerman.github.io",
            
            # 个人Writeup博客
            "RykerWw/CTF-Writeups",
            "CHYbeta/CTF-Writeups",
            "RopEmperor/CTF-Writeups",
            "liupeirong/CTF-Writeups",
            "pberba/CTF-writeups",
            "jmhale/CTF-Writeups",
            
            # 中文博客
            "Mei-You-Qian/Mei-You-Qian.github.io",
            "Xinyuan-Lily/CTF-Writeups",
            
            # 专题Writeup
            "ghost-in-the-shellcode/CTF-Writeups",
            "PPP/writeups",
            "RPISEC/CTF-Writeups",
            "shellphish/writeups",
        ]
    
    def search_repos(self, max_per_query: int = 5) -> List[Dict[str, Any]]:
        """搜索仓库"""
        print("=" * 60)
        print("搜索CTF和取证Writeup仓库")
        print("=" * 60)
        
        all_repos = {}
        
        # 搜索GitHub
        for i, query in enumerate(self.search_queries[:15], 1):  # 只搜索前15个关键词
            print(f"\n[{i}/15] 搜索: {query}")
            
            repos = self._search_github(query, max_per_query)
            
            for repo in repos:
                name = repo.get("name")
                if name not in all_repos:
                    all_repos[name] = repo
            
            print(f"  找到 {len(repos)} 个仓库")
            time.sleep(2)  # 避免API限制
        
        # 获取已知仓库信息
        print("\n获取已知仓库信息...")
        for repo_name in self.known_repos:
            if repo_name not in all_repos:
                info = self._get_repo_info(repo_name)
                if info:
                    all_repos[repo_name] = info
                    print(f"  添加: {repo_name}")
                time.sleep(1)
        
        # 转换为列表并排序
        self.repos = sorted(all_repos.values(), 
                           key=lambda x: x.get("stars", 0), 
                           reverse=True)
        
        print(f"\n共找到 {len(self.repos)} 个仓库")
        
        return self.repos
    
    def _search_github(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """搜索GitHub"""
        repos = []
        
        try:
            url = "https://api.github.com/search/repositories"
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": max_results
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get("items", []):
                    repo = {
                        "name": item.get("full_name"),
                        "description": item.get("description", ""),
                        "stars": item.get("stargazers_count", 0),
                        "forks": item.get("forks_count", 0),
                        "language": item.get("language", ""),
                        "url": item.get("html_url"),
                        "topics": item.get("topics", []),
                        "updated_at": item.get("updated_at", ""),
                        "size": item.get("size", 0),
                    }
                    repos.append(repo)
        
        except Exception as e:
            print(f"  搜索失败: {e}")
        
        return repos
    
    def _get_repo_info(self, repo_name: str) -> Dict[str, Any]:
        """获取仓库信息"""
        try:
            url = f"https://api.github.com/repos/{repo_name}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                info = response.json()
                return {
                    "name": info.get("full_name"),
                    "description": info.get("description", ""),
                    "stars": info.get("stargazers_count", 0),
                    "forks": info.get("forks_count", 0),
                    "language": info.get("language", ""),
                    "url": info.get("html_url"),
                    "topics": info.get("topics", []),
                    "updated_at": info.get("updated_at", ""),
                    "size": info.get("size", 0),
                }
        except Exception as e:
            pass
        
        return None
    
    def categorize_repos(self) -> Dict[str, List[Dict[str, Any]]]:
        """对仓库进行分类"""
        categories = {
            "CTF Writeup集合": [],
            "取证工具": [],
            "取证资源": [],
            "个人博客": [],
            "中文博客": [],
            "专题Writeup": [],
            "其他": [],
        }
        
        for repo in self.repos:
            name = repo.get("name", "").lower()
            desc = repo.get("description", "").lower()
            
            if "ctfs/write-ups" in name:
                categories["CTF Writeup集合"].append(repo)
            elif any(kw in name for kw in ["volatility", "sleuthkit", "autopsy", "arsenal"]):
                categories["取证工具"].append(repo)
            elif any(kw in name for kw in ["forensic", "artifact", "kape"]):
                categories["取证资源"].append(repo)
            elif any(kw in name for kw in ["writeup", "write-up", "ctf"]) and "个人" not in desc:
                categories["个人博客"].append(repo)
            elif any(kw in desc for kw in ["中文", "chinese", "中国"]):
                categories["中文博客"].append(repo)
            elif any(kw in name for kw in ["forensics", "memory", "disk", "network", "malware"]):
                categories["专题Writeup"].append(repo)
            else:
                categories["其他"].append(repo)
        
        return categories
    
    def save_results(self):
        """保存结果"""
        # 保存所有仓库
        all_file = self.output_dir / "all_writeup_repos.json"
        os.makedirs(all_file.parent, exist_ok=True)
        
        with open(all_file, 'w', encoding='utf-8') as f:
            json.dump(self.repos, f, ensure_ascii=False, indent=2)
        
        # 保存分类结果
        categories = self.categorize_repos()
        cat_file = self.output_dir / "categorized_repos.json"
        
        with open(cat_file, 'w', encoding='utf-8') as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)
        
        # 生成挑选列表
        self._generate_selection_list(categories)
        
        print(f"\n保存完成:")
        print(f"  - 所有仓库: {all_file}")
        print(f"  - 分类结果: {cat_file}")
        print(f"  - 挑选列表: {self.output_dir / 'repos_to_select.md'}")
    
    def _generate_selection_list(self, categories: Dict[str, List[Dict[str, Any]]]):
        """生成挑选列表"""
        output_file = self.output_dir / "repos_to_select.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# CTF和取证Writeup仓库挑选列表\n\n")
            f.write("请标记要学习的仓库: [x] 表示学习，[ ] 表示跳过\n\n")
            
            for cat_name, repos in categories.items():
                if not repos:
                    continue
                
                f.write(f"## {cat_name}\n\n")
                f.write("| 选择 | 仓库 | Stars | 描述 | 大小 |\n")
                f.write("|------|------|-------|------|------|\n")
                
                for repo in repos:
                    name = repo.get("name", "")
                    stars = repo.get("stars", 0)
                    desc = repo.get("description", "")[:50]
                    size = repo.get("size", 0)
                    
                    # 格式化大小
                    if size > 1000:
                        size_str = f"{size/1000:.1f}MB"
                    else:
                        size_str = f"{size}KB"
                    
                    f.write(f"| [ ] | {name} | {stars} | {desc} | {size_str} |\n")
                
                f.write("\n")
            
            f.write("---\n\n")
            f.write("## 学习优先级建议\n\n")
            f.write("1. **高优先级**: Stars > 1000 的仓库\n")
            f.write("2. **中优先级**: Stars 100-1000 的仓库\n")
            f.write("3. **低优先级**: Stars < 100 的仓库\n\n")
            f.write("## 学习方式\n\n")
            f.write("```bash\n")
            f.write("# 学习单个仓库\n")
            f.write("python scripts/learn_repo.py --url <仓库URL> --year <年份>\n\n")
            f.write("# 批量学习（从文件读取）\n")
            f.write("python scripts/batch_learn.py --file selected_repos.txt\n")
            f.write("```\n")

def main():
    """主函数"""
    output_dir = r"E:\forensic-ai-platform\data\repos"
    
    searcher = WriteupRepoSearcher(output_dir)
    searcher.search_repos(max_per_query=5)
    searcher.save_results()

if __name__ == "__main__":
    main()
