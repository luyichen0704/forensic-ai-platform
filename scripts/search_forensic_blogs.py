"""
GitHub取证Writeup个人博客搜索
专门搜索个人博客和Writeup集合
"""
import requests
import json
import time
from typing import List, Dict, Any

# 个人博客和Writeup集合搜索关键词
BLOG_QUERIES = [
    "CTF forensics writeup blog",
    "digital forensics blog writeup",
    "取证 CTF writeup 个人",
    "美亚杯 writeup blog",
    "memory forensics blog",
    "disk forensics writeup",
    "network forensics PCAP blog",
    "malware analysis writeup blog",
    "incident response writeup",
    "DFIR writeup blog",
    "SANS forensics writeup",
    "autopsy writeup blog",
    "volatility writeup blog",
    "sleuthkit writeup",
    "forensics CTF writeup 2024",
    "forensics CTF writeup 2025",
]

# 已知的高质量取证博客
KNOWN_BLOGS = [
    # 个人Writeup博客
    "RykerWw/CTF-Writeups",
    "CHYbeta/CTF-Writeups",
    "RopEmperor/CTF-Writeups",
    "liupeirong/CTF-Writeups",
    "pberba/CTF-writeups",
    "jmhale/CTF-Writeups",
    "Rope8773/CTF-Writeups",
    "Capture-the-Flag/CTF-Writeups",
    
    # 取证专题博客
    "AndrewRathbun/DFIR-Tools",
    "EricZimmerman/ericzimmerman.github.io",
    "AndrewRathbun/DFIR-Summary",
    "ForensicArtifacts/artifacts",
    
    # 中文取证博客
    "Xinyuan-Lily/CTF-Writeups",
    "LiHua-Official/CTF-Writeups",
    "ForensicWiki/forensicwiki",
]

def search_repos(query: str, token: str = None) -> List[Dict[str, Any]]:
    """搜索仓库"""
    repos = []
    
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        url = "https://api.github.com/search/repositories"
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": 10
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
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
                    "type": "search"
                }
                repos.append(repo)
    
    except Exception as e:
        print(f"  搜索失败: {e}")
    
    return repos

def get_repo_info(repo_name: str, token: str = None) -> Dict[str, Any]:
    """获取仓库信息"""
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        url = f"https://api.github.com/repos/{repo_name}"
        response = requests.get(url, headers=headers, timeout=10)
        
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
                "type": "known"
            }
    except Exception as e:
        pass
    
    return None

def main():
    """主函数"""
    print("=" * 60)
    print("GitHub 取证Writeup博客搜索")
    print("=" * 60)
    
    all_repos = {}
    
    # 搜索博客
    print("\n[1/2] 搜索取证相关博客...")
    for query in BLOG_QUERIES[:8]:  # 只搜索前8个关键词
        print(f"\n搜索: {query}")
        repos = search_repos(query)
        
        for repo in repos:
            name = repo.get("name")
            if name not in all_repos:
                all_repos[name] = repo
        
        print(f"  找到 {len(repos)} 个仓库")
        time.sleep(2)  # 避免API限制
    
    # 获取已知博客信息
    print("\n[2/2] 获取已知博客信息...")
    for blog_name in KNOWN_BLOGS:
        info = get_repo_info(blog_name)
        if info and info.get("name") not in all_repos:
            all_repos[info.get("name")] = info
            print(f"  添加: {info.get('name')}")
        time.sleep(1)
    
    # 按stars排序
    sorted_repos = sorted(all_repos.values(), key=lambda x: x.get("stars", 0), reverse=True)
    
    # 保存结果
    output_file = "E:\\forensic-ai-platform\\cases\\github_blogs.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sorted_repos, f, ensure_ascii=False, indent=2)
    
    print(f"\n保存到: {output_file}")
    
    # 打印统计
    print("\n" + "=" * 60)
    print("搜索结果统计")
    print("=" * 60)
    print(f"总仓库数: {len(sorted_repos)}")
    
    # 打印推荐
    print("\n" + "=" * 60)
    print("推荐学习的取证博客/仓库")
    print("=" * 60)
    
    recommendations = [
        {
            "category": "CTF Writeup集合",
            "repos": [
                "ctfs/write-ups-*",
                "RykerWw/CTF-Writeups",
                "CHYbeta/CTF-Writeups",
            ]
        },
        {
            "category": "取证工具资源",
            "repos": [
                "ForensicArtifacts/artifacts",
                "EricZimmerman/ericzimmerman.github.io",
                "AndrewRathbun/DFIR-Tools",
            ]
        },
        {
            "category": "内存取证",
            "repos": [
                "volatilityfoundation/volatility3",
                "volatilityfoundation/volatility",
            ]
        },
        {
            "category": "磁盘取证",
            "repos": [
                "sleuthkit/sleuthkit",
                "ArsenalRecon/Arsenal-Image-Mounter",
            ]
        },
    ]
    
    for rec in recommendations:
        print(f"\n[{rec['category']}]")
        for repo in rec['repos']:
            print(f"  - {repo}")
    
    # 生成学习计划
    print("\n" + "=" * 60)
    print("学习计划建议")
    print("=" * 60)
    
    learning_plan = [
        "1. 学习ctfs/write-ups-*系列，了解CTF取证题目类型",
        "2. 学习ForensicArtifacts/artifacts，了解取证工件",
        "3. 学习EricZimmerman/ericzimmerman.github.io，了解DFIR工具",
        "4. 学习volatilityfoundation/volatility3，掌握内存取证",
        "5. 学习sleuthkit/sleuthkit，掌握磁盘取证",
        "6. 学习个人Writeup博客，了解实战解题思路",
    ]
    
    for step in learning_plan:
        print(step)

if __name__ == "__main__":
    main()
