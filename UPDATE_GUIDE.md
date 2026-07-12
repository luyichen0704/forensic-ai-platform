# 项目更新指南

## 便于更新的架构设计

### 1. 数据更新流程

```
更新步骤:
1. 运行搜索脚本发现新仓库
2. 人工挑选要学习的仓库
3. 运行学习脚本提取数据
4. 自动合并到案例库
5. 推送到GitHub
```

### 2. 快速更新命令

```bash
# 搜索新的Writeup仓库
python scripts/search_new_writeups.py

# 学习指定仓库
python scripts/learn_repo.py --url <仓库URL> --year <年份>

# 批量学习多个仓库
python scripts/batch_learn.py --file repos_to_learn.txt

# 更新案例库索引
python scripts/update_case_index.py

# 导出训练数据
python scripts/export_training_data.py --format jsonl
```

### 3. 数据目录结构

```
data/
├── cases/                    # 案例数据
│   ├── raw/                 # 原始数据
│   ├── processed/           # 处理后的数据
│   └── index.json           # 索引文件
├── knowledge/               # 知识库
│   ├── memory_forensics.json
│   ├── disk_forensics.json
│   └── ...
├── repos/                   # 仓库元数据
│   ├── learned.json         # 已学习的仓库
│   ├── pending.json         # 待学习的仓库
│   └── skipped.json         # 跳过的仓库
└── training/                # 训练数据
    ├── qa_pairs.jsonl       # 问答对
    └── ...
```

### 4. 更新脚本

- `scripts/search_new_writeups.py` - 搜索新仓库
- `scripts/learn_repo.py` - 学习单个仓库
- `scripts/batch_learn.py` - 批量学习
- `scripts/update_case_index.py` - 更新索引
- `scripts/export_training_data.py` - 导出训练数据
