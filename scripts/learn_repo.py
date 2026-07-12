"""
学习单个仓库脚本
用法: python learn_repo.py --url <仓库URL> --year <年份>
"""
import argparse
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.extract_batch_writeups import BatchWriteupExtractor

def main():
    parser = argparse.ArgumentParser(description='学习单个CTF/取证Writeup仓库')
    parser.add_argument('--url', required=True, help='仓库URL')
    parser.add_argument('--year', type=int, required=True, help='年份')
    parser.add_argument('--output', default=r'E:\forensic-ai-platform\cases', help='输出目录')
    
    args = parser.parse_args()
    
    print(f"开始学习仓库: {args.url}")
    print(f"年份: {args.year}")
    print(f"输出目录: {args.output}")
    
    extractor = BatchWriteupExtractor(args.output)
    extractor.extract_from_repo(args.url, args.year)
    extractor.save_cases()
    
    print("\n学习完成！")

if __name__ == "__main__":
    main()
