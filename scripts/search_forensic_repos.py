"""
GitHub取证Writeup仓库搜索
搜索GitHub上的取证比赛Writeup和个人博客
"""
import requests
import json
import time
from typing import List, Dict, Any

# 取证相关搜索关键词
SEARCH_QUERIES = [
    "forensics writeup CTF",
    "digital forensics writeup",
    "电子取证 writeup",
    "美亚杯 writeup",
    "FIC 取证",
    "数证杯 writeup",
    "盘古石 取证",
    "memory forensics writeup",
    "disk forensics writeup",
    "network forensics PCAP",
    "malware analysis writeup",
    "incident response writeup",
    "CTF forensics tools",
    "volatility writeup",
    "autopsy writeup",
    "sleuthkit writeup",
]

# 已知的高质量取证仓库
KNOWN_REPOS = [
    # 取证工具和资源
    "volatilityfoundation/volatility3",
    "sleuthkit/sleuthkit",
    "ArsenalRecon/Arsenal-Image-Mounter",
    
    # CTF Writeup集合
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
    
    # 取证资源
    "ForensicArtifacts/artifacts",
    "EricZimmerman/KapeFiles",
    "volatilityfoundation/volatility",
    
    # 个人Writeup博客
    "RykerWw/CTF-Writeups",
    "CHYbeta/CTF-Writeups",
    "RopEmperor/CTF-Writeups",
    "liupeirong/CTF-Writeups",
]

def search_github_repos(query: str, token: str = None) -> List[Dict[str, Any]]:
    """搜索GitHub仓库"""
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
                }
                repos.append(repo)
        else:
            print(f"  API请求失败: {response.status_code}")
    
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
            return response.json()
    except Exception as e:
        print(f"  获取仓库信息失败: {e}")
    
    return None

def main():
    """主函数"""
    print("=" * 60)
    print("GitHub 取证Writeup仓库搜索")
    print("=" * 60)
    
    all_repos = []
    
    # 搜索仓库
    print("\n[1/2] 搜索取证相关仓库...")
    for query in SEARCH_QUERIES[:5]:  # 只搜索前5个关键词
        print(f"\n搜索: {query}")
        repos = search_github_repos(query)
        all_repos.extend(repos)
        print(f"  找到 {len(repos)} 个仓库")
        time.sleep(2)  # 避免API限制
    
    # 去重
    unique_repos = {}
    for repo in all_repos:
        name = repo.get("name")
        if name not in unique_repos:
            unique_repos[name] = repo
    
    # 获取已知仓库信息
    print("\n[2/2] 获取已知仓库信息...")
    for repo_name in KNOWN_REPOS[:10]:  # 只获取前10个
        info = get_repo_info(repo_name)
        if info:
            unique_repos[repo_name] = {
                "name": info.get("full_name"),
                "description": info.get("description", ""),
                "stars": info.get("stargazers_count", 0),
                "forks": info.get("forks_count", 0),
                "language": info.get("language", ""),
                "url": info.get("html_url"),
                "topics": info.get("topics", []),
                "updated_at": info.get("updated_at", ""),
            }
        time.sleep(1)
    
    # 按stars排序
    sorted_repos = sorted(unique_repos.values(), key=lambda x: x.get("stars", 0), reverse=True)
    
    # 保存结果
    output_file = "E:\\forensic-ai-platform\\cases\\github_repos.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sorted_repos, f, ensure_ascii=False, indent=2)
    
    print(f"\n保存到: {output_file}")
    
    # 打印统计
    print("\n" + "=" * 60)
    print("搜索结果统计")
    print("=" * 60)
    print(f"总仓库数: {len(sorted_repos)}")
    print(f"Stars > 100: {sum(1 for r in sorted_repos if r.get('stars', 0) > 100)}")
    print(f"Stars > 1000: {sum(1 for r in sorted_repos if r.get('stars', 0) > 1000)}")
    
    # 打印Top 10
    print("\nTop 10 仓库:")
    print("-" * 60)
    for i, repo in enumerate(sorted_repos[:10], 1):
        print(f"{i}. {repo.get('name')}")
        print(f"   Stars: {repo.get('stars', 0)} | 描述: {repo.get('description', '')[:50]}...")
    
    # 生成推荐列表
    print("\n" + "=" * 60)
    print("推荐学习的仓库")
    print("=" * 60)
    
    recommendations = [
        {
            "name": "ctfs/write-ups-*",
            "description": "CTF比赛Writeup集合，包含大量取证题目",
            "priority": "高"
        },
        {
            "name": "ForensicArtifacts/artifacts",
            "description": "取证工件定义，用于自动化取证",
            "priority": "高"
        },
        {
            "name": "EricZimmerman/KapeFiles",
            "description": "KAPE取证工具文件",
            "priority": "中"
        },
        {
            "name": "volatilityfoundation/volatility3",
            "description": "内存取证框架",
            "priority": "高"
        },
        {
            "name": "sleuthkit/sleuthkit",
            "description": "磁盘取证工具包",
            "priority": "高"
        },
    ]
    
    for rec in recommendations:
        print(f"\n[{rec['priority']}] {rec['name']}")
        print(f"    {rec['description']}")

if __name__ == "__main__":
    main()
