# CTF和取证Writeup仓库挑选列表

请标记要学习的仓库: [x] 表示学习，[ ] 表示跳过

## CTF Writeup集合 (高优先级)

| 选择 | 仓库 | Stars | 描述 | 学习状态 |
|------|------|-------|------|----------|
| [x] | ctfs/write-ups-2013 | - | CTF 2013 Writeup | 待学习 |
| [x] | ctfs/write-ups-2014 | - | CTF 2014 Writeup | 待学习 |
| [x] | ctfs/write-ups-2015 | 1997 | CTF 2015 Writeup | ✅ 已学习 |
| [x] | ctfs/write-ups-2016 | 1626 | CTF 2016 Writeup | ✅ 已学习 |
| [x] | ctfs/write-ups-2017 | 2149 | CTF 2017 Writeup | ✅ 已学习 |
| [x] | ctfs/write-ups-2018 | 267 | CTF 2018 Writeup | 待学习 |
| [x] | ctfs/write-ups-2019 | - | CTF 2019 Writeup | 待学习 |
| [x] | ctfs/write-ups-2020 | - | CTF 2020 Writeup | 待学习 |
| [x] | ctfs/write-ups-2021 | - | CTF 2021 Writeup | 待学习 |
| [x] | ctfs/write-ups-2022 | - | CTF 2022 Writeup | 待学习 |
| [x] | ctfs/write-ups-2023 | - | CTF 2023 Writeup | 待学习 |
| [x] | ctfs/write-ups-2024 | - | CTF 2024 Writeup | 待学习 |

## 取证工具 (高优先级)

| 选择 | 仓库 | Stars | 描述 | 学习状态 |
|------|------|-------|------|----------|
| [x] | volatilityfoundation/volatility3 | 4239 | 内存取证框架 | ✅ 已学习 |
| [x] | sleuthkit/sleuthkit | 3108 | 磁盘取证工具 | ✅ 已学习 |
| [ ] | ArsenalRecon/Arsenal-Image-Mounter | 771 | 磁盘镜像挂载 | - |

## 取证资源 (中优先级)

| 选择 | 仓库 | Stars | 描述 | 学习状态 |
|------|------|-------|------|----------|
| [x] | ForensicArtifacts/artifacts | - | 取证工件定义 | 待学习 |
| [x] | EricZimmerman/KapeFiles | - | KAPE取证工具 | 待学习 |
| [x] | EricZimmerman/ericzimmerman.github.io | - | DFIR工具集 | 待学习 |

## 个人博客 (中优先级)

| 选择 | 仓库 | Stars | 描述 | 学习状态 |
|------|------|-------|------|----------|
| [x] | Mei-You-Qian/Mei-You-Qian.github.io | - | 取证博客 | ✅ 已学习 |
| [x] | RykerWw/CTF-Writeups | - | CTF Writeup | 待学习 |
| [x] | CHYbeta/CTF-Writeups | - | CTF Writeup | 待学习 |
| [x] | RopEmperor/CTF-Writeups | - | CTF Writeup | 待学习 |
| [x] | liupeirong/CTF-Writeups | - | CTF Writeup | 待学习 |
| [x] | pberba/CTF-writeups | - | CTF Writeup | 待学习 |

## 安全知识库 (中优先级)

| 选择 | 仓库 | Stars | 描述 | 学习状态 |
|------|------|-------|------|----------|
| [x] | ffffffff0x/1earn | 5693 | 安全知识框架 | 待学习 |
| [x] | Abdowaer098/Wa3r-OffSec-Kit | 217 | 安全工具集 | 待学习 |
| [x] | vmayoral/robot_hacking_manual | 402 | 机器人安全 | 待学习 |

## 特定比赛Writeup (低优先级)

| 选择 | 仓库 | Stars | 描述 | 学习状态 |
|------|------|-------|------|----------|
| [ ] | jon-brandy/hackthebox | 195 | HackTheBox | - |
| [ ] | ghost-in-the-shellcode/CTF-Writeups | - | CTF Writeup | - |
| [ ] | PPP/writeups | - | PPP战队 | - |
| [ ] | RPISEC/CTF-Writeups | - | RPISEC战队 | - |
| [ ] | shellphish/writeups | - | Shellphish战队 | - |

---

## 学习优先级

### 第一优先级 (立即学习)
- ctfs/write-ups-2013 ~ 2024 (CTF Writeup集合)
- ForensicArtifacts/artifacts (取证工件)

### 第二优先级 (近期学习)
- EricZimmerman/* (DFIR工具)
- ffffffff0x/1earn (安全知识框架)
- 个人Writeup博客

### 第三优先级 (按需学习)
- 特定比赛Writeup
- 专题Writeup

---

## 学习命令

```bash
# 学习单个仓库
python scripts/learn_repo.py --url https://github.com/ctfs/write-ups-2018.git --year 2018

# 批量学习
python scripts/batch_learn.py --file selected_repos.txt

# 更新案例库索引
python scripts/update_case_index.py
```
