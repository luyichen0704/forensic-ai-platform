#!/usr/bin/env python3
"""
CTF 电子取证智能分析引擎
=========================
解决"文件大、信息密度低"的核心问题：
1. 基于题目关键词定向搜索，而非全盘扫描
2. 多检材证据链自动关联
3. 分层分析：先浅后深，命中即停
4. 嫌疑人操作路径重建

用法:
  python smart_hunter.py -c ./case/ -q "李安弘 邮件 发送用户"
  python smart_hunter.py -c ./case/ -q "保险柜 密码"
  python smart_hunter.py -c ./case/ --auto   # 全自动模式
"""
import os
import re
import sys
import json
import hashlib
import subprocess
import sqlite3
import struct
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

# ============================================================
# 配置
# ============================================================

# 高价值文件扩展名（跳过 .dll .exe .sys 等系统文件）
HIGH_VALUE_EXTS = {
    ".txt", ".doc", ".docx", ".xls", ".xlsx", ".pdf", ".csv",
    ".json", ".xml", ".ini", ".cfg", ".conf", ".yaml", ".yml",
    ".log", ".db", ".sqlite", ".sqlite3", ".pst", ".ost",
    ".eml", ".msg", ".png", ".jpg", ".jpeg", ".bmp", ".gif",
    ".mp4", ".avi", ".mp3", ".wav", ".zip", ".rar", ".7z",
    ".enc", ".pem", ".key", ".crt", ".cer", ".pfx",
    ".bash_history", ".zsh_history", ".history",
    ".lnk", ".dat", ".bak", ".old", ".tmp",
}

# 低价值目录（跳过）
SKIP_DIRS = {
    "Windows", "WinSxS", "System32", "SysWOW64",
    "Program Files", "Program Files (x86)",
    "ProgramData", "node_modules", "__pycache__",
    ".git", ".svn", "Microsoft", "Microsoft.NET",
    "assembly", "Installer", "Boot", "Recovery",
    "Fonts", "Resources", "WinSxS",
}

# 高价值目录（优先搜索）
HIGH_VALUE_DIRS = {
    "Users", "home", "root", "Desktop", "Documents", "文档",
    "Downloads", "下载", "Pictures", "图片", "Videos", "视频",
    "AppData", ".config", ".local", ".ssh", ".gnupg",
    "Recent", "Recycle", ".Trash", "tmp", "temp",
    "var/log", "var/mail", "etc", "opt",
}

# Flag 关键词模式
FLAG_KEYWORDS = [
    "flag", "ctf", "CTF", "FLAG",
    "password", "密码", "口令",
    "secret", "key", "token", "apikey", "api_key",
    "private", "PRIVATE KEY",
]

# 题目 → 搜索策略映射
QUESTION_STRATEGIES = {
    "邮件|email|mail|发送|收件|发件": {
        "paths": ["mail", "Mail", "email", "Email", ".pst", ".ost", ".eml", ".msg", "thunderbird", "outlook"],
        "content_patterns": ["@", "From:", "To:", "Subject:", "smtp", "imap", "pop3"],
        "tools": ["strings", "rg"],
    },
    "密码|password|口令|登录|login": {
        "paths": ["shadow", "passwd", "SAM", "SYSTEM", "ntuser", ".bash_history", "keepass", "lastpass"],
        "content_patterns": [r"password[:=]\s*\S+", r"passwd[:=]\s*\S+", r"pwd[:=]\s*\S+", r"login.*password"],
        "tools": ["strings", "rg", "sam-crack"],
    },
    "浏览器|browser|chrome|firefox|edge|历史|history|书签|bookmark": {
        "paths": ["History", "Bookmarks", "Login Data", "Cookies", "Web Data", "places.sqlite", "formhistory.sqlite"],
        "content_patterns": [r"https?://", r"\.com", r"\.cn", r"\.org"],
        "tools": ["sqlite3", "strings"],
    },
    "聊天|chat|微信|wechat|QQ|telegram|discord|消息|message|记录": {
        "paths": ["WeChat", "wechat", "Tencent", "QQ", "Telegram", "Discord", "Messages", "msg", "聊天"],
        "content_patterns": ["msg", "message", "chat", "text", "content"],
        "tools": ["strings", "rg"],
    },
    "照片|图片|photo|image|pic|png|jpg|截图|screenshot": {
        "paths": ["Pictures", "图片", "Photos", "Screenshots", "截图", "DCIM", "Camera"],
        "content_patterns": [],
        "tools": ["exiftool", "zsteg", "binwalk"],
    },
    "文档|document|doc|docx|pdf|xls|xlsx|表格|合同|报告|report": {
        "paths": ["Documents", "文档", "Desktop", "下载", "Downloads"],
        "content_patterns": [],
        "tools": ["strings", "olevba"],
    },
    "vpn|代理|proxy|端口|port|网络|network": {
        "paths": ["vpn", "proxy", "network", "wireguard", "openvpn", "clash", "v2ray", "shadowsocks"],
        "content_patterns": [r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+", r"port[:=]\s*\d+", r"listen", r"socks"],
        "tools": ["strings", "rg"],
    },
    "勒索|ransomware|加密|encrypt|解密|decrypt|锁|lock": {
        "paths": ["ransom", "locker", "encrypt", "decrypt", "readme", "HOW_TO_DECRYPT"],
        "content_patterns": [r"bitcoin", r"wallet", r"decrypt", r"contact", r"email", r"@tutanota", r"@proton"],
        "tools": ["strings"],
    },
    "apk|app|应用|android|安卓|手机|mobile": {
        "paths": ["apk", ".apk", "Android", "mobile", "app"],
        "content_patterns": [],
        "tools": ["jadx", "strings", "7z"],
    },
    "AI|模型|model|apikey|api_key|gpt|llm|openrouter|deepseek": {
        "paths": ["AI", "model", "config", "llm", "gpt", "openrouter", "deepseek", "chatgpt"],
        "content_patterns": [r"sk-[a-zA-Z0-9]{20,}", r"api[_-]?key[:=]\s*\S+", r"model[:=]\s*\S+"],
        "tools": ["strings", "rg", "sqlite3"],
    },
    "备忘录|记事本|note|memo|记录|reminder|todo": {
        "paths": ["note", "memo", "notes", "todo", "reminder", "记事本", "备忘录", "sticky"],
        "content_patterns": [r"电话|phone|tel|手机|mobile|联系|contact"],
        "tools": ["strings"],
    },
    "保险柜|保险箱|safe|vault|黄金|gold|贵重|valuable": {
        "paths": ["safe", "vault", "保险", "gold", "贵重", "important", "重要"],
        "content_patterns": [r"密码|password|code|编号|number|组合|combination"],
        "tools": ["strings", "rg"],
    },
}


class SmartHunter:
    def __init__(self, case_dir: str, questions: list[str] | None = None):
        self.case_dir = Path(case_dir)
        self.questions = questions or []
        self.findings = []
        self.scanned_files = set()
        self.start_time = datetime.now()

    def log(self, level: str, msg: str):
        elapsed = (datetime.now() - self.start_time).total_seconds()
        prefix = {"+": "✓", "-": "✗", "*": "→", "!": "⚠"}
        print(f"[{elapsed:5.1f}s] {prefix.get(level, level)} {msg}")

    # ================================================================
    # 阶段 1: 题目解析 → 生成搜索计划
    # ================================================================
    def analyze_questions(self) -> dict:
        """根据题目文本自动推断搜索策略"""
        if not self.questions:
            return {"strategy": "auto", "paths": [], "patterns": [], "tools": ["strings"]}

        combined_paths = set()
        combined_patterns = set()
        combined_tools = set()

        for q in self.questions:
            matched = False
            for pattern, strategy in QUESTION_STRATEGIES.items():
                if re.search(pattern, q, re.IGNORECASE):
                    self.log("+", f"题目匹配: '{q[:40]}...' → {pattern[:30]}")
                    combined_paths.update(strategy["paths"])
                    combined_patterns.update(strategy["content_patterns"])
                    combined_tools.update(strategy["tools"])
                    matched = True
            if not matched:
                self.log("!", f"未匹配策略: '{q[:40]}...'，使用通用策略")

        if not combined_paths:
            combined_paths = {"."}
            combined_patterns = {"flag", "password", "secret", "key"}
            combined_tools = {"strings", "rg"}

        return {
            "paths": list(combined_paths),
            "patterns": list(combined_patterns),
            "tools": list(combined_tools),
        }

    # ================================================================
    # 阶段 2: 智能文件发现（分层：先高价值目录，再扩展）
    # ================================================================
    def discover_files(self, strategy: dict) -> list[Path]:
        """分层发现文件：先高价值目录 → 再扩展"""
        target_paths = strategy.get("paths", [])
        files = []

        self.log("*", f"发现文件（策略: {target_paths[:5]}...）")

        # Level 1: 精确匹配高价值路径
        for target in target_paths:
            for root, dirs, filenames in os.walk(self.case_dir, topdown=True):
                # 跳过系统目录
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

                for fname in filenames:
                    ext = Path(fname).suffix.lower()
                    rel_path = os.path.relpath(os.path.join(root, fname), self.case_dir)

                    # 路径或文件名匹配目标关键词
                    if any(t.lower() in rel_path.lower() for t in target_paths):
                        if ext in HIGH_VALUE_EXTS or ext == "":
                            files.append(Path(root) / fname)
                            self.scanned_files.add(str(Path(root) / fname))

        self.log("+", f"发现 {len(files)} 个高价值文件")

        # Level 2: 扩展搜索（仅当 Level 1 结果 < 100 时）
        if len(files) < 100:
            extra = []
            for root, dirs, filenames in os.walk(self.case_dir, topdown=True):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for fname in filenames:
                    fp = Path(root) / fname
                    if str(fp) not in self.scanned_files:
                        ext = fp.suffix.lower()
                        if ext in HIGH_VALUE_EXTS:
                            extra.append(fp)
            files.extend(extra[:200])  # 最多再取 200 个
            self.log("+", f"扩展发现 {len(extra[:200])} 个文件，总计 {len(files)}")

        return files

    # ================================================================
    # 阶段 3: 并行快速扫描（字符串优先，命中即深度）
    # ================================================================
    def quick_scan_file(self, filepath: Path, patterns: list[str]) -> dict | None:
        """对单个文件执行快速字符串扫描"""
        try:
            # 跳过过大的文件 (>500MB)
            size = filepath.stat().st_size
            if size > 500 * 1024 * 1024:
                return None

            # 只扫描前 10MB
            read_size = min(size, 10 * 1024 * 1024)

            with open(filepath, "rb") as f:
                data = f.read(read_size)

            # 字符串提取
            text_data = data.decode("utf-8", errors="replace").lower()

            hits = []
            for pattern in patterns:
                try:
                    matches = re.findall(pattern, text_data, re.IGNORECASE)
                    if matches:
                        hits.extend(matches[:5])
                except re.error:
                    # 普通子串匹配
                    if pattern.lower() in text_data:
                        hits.append(pattern)

            if hits:
                return {
                    "file": str(filepath),
                    "size": size,
                    "hits": list(set(hits)),
                    "ext": filepath.suffix.lower(),
                }
        except Exception:
            pass
        return None

    def parallel_scan(self, files: list[Path], patterns: list[str], max_workers: int = 8) -> list[dict]:
        """并行扫描文件"""
        results = []
        self.log("*", f"并行扫描 {len(files)} 个文件（{max_workers} 线程）...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.quick_scan_file, fp, patterns): fp
                for fp in files
            }
            done = 0
            for future in as_completed(futures):
                done += 1
                result = future.result()
                if result:
                    results.append(result)
                    if len(results) <= 20:  # 只显示前 20 个
                        self.log("+", f"命中: {Path(result['file']).name} → {result['hits'][:3]}")

                if done % 50 == 0:
                    self.log("*", f"进度: {done}/{len(files)}")

        # 按文件大小排序（小文件优先 → 通常是配置文件/文档）
        results.sort(key=lambda x: x["size"])
        return results

    # ================================================================
    # 阶段 4: 深度分析（仅对命中文件）
    # ================================================================
    def deep_analyze(self, hit_files: list[dict]):
        """对扫描命中的文件执行深度分析"""
        for hit in hit_files[:30]:  # 最多深度分析 30 个
            fp = Path(hit["file"])
            ext = hit["ext"]
            self.log("*", f"深度分析: {fp.name} (ext={ext}, size={hit['size']})")

            # 根据文件类型选择分析工具
            if ext in (".db", ".sqlite", ".sqlite3"):
                self.analyze_sqlite(fp)
            elif ext in (".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"):
                self.analyze_office(fp)
            elif ext in (".png", ".jpg", ".jpeg", ".bmp", ".gif"):
                self.analyze_image(fp)
            elif ext in (".zip", ".rar", ".7z"):
                self.analyze_archive(fp)
            elif ext in (".pem", ".key", ".crt", ".cer"):
                self.analyze_crypto(fp)

    def analyze_sqlite(self, fp: Path):
        try:
            conn = sqlite3.connect(str(fp))
            cursor = conn.cursor()
            tables = cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            for (table,) in tables:
                try:
                    cols = cursor.execute(f"PRAGMA table_info({table})").fetchall()
                    col_names = [c[1] for c in cols]
                    # 查找包含敏感关键词的列
                    for cn in col_names:
                        if any(kw in cn.lower() for kw in ["pass", "key", "token", "secret", "user", "login", "cred", "apikey"]):
                            rows = cursor.execute(
                                f"SELECT {cn} FROM {table} LIMIT 10"
                            ).fetchall()
                            for row in rows:
                                val = str(row[0])[:200]
                                self.log("!", f"  [SQLite] {fp.name}: {table}.{cn} = {val}")
                except Exception:
                    pass
            conn.close()
        except Exception:
            pass

    def analyze_office(self, fp: Path):
        try:
            result = subprocess.run(
                ["olevba", str(fp)], capture_output=True, text=True, timeout=30
            )
            for line in result.stdout.split("\n"):
                if any(kw in line.lower() for kw in FLAG_KEYWORDS):
                    self.log("!", f"  [OLE] {fp.name}: {line.strip()[:120]}")
        except Exception:
            pass

    def analyze_image(self, fp: Path):
        try:
            result = subprocess.run(
                ["exiftool", str(fp)], capture_output=True, text=True, timeout=15
            )
            for line in result.stdout.split("\n"):
                if any(kw in line.lower() for kw in FLAG_KEYWORDS + ["comment", "warning"]):
                    self.log("!", f"  [EXIF] {fp.name}: {line.strip()[:120]}")
        except Exception:
            pass

    def analyze_archive(self, fp: Path):
        try:
            result = subprocess.run(
                ["7z", "l", str(fp)], capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                lines = result.stdout.split("\n")
                self.log("*", f"  [Archive] {fp.name}: {len(lines)-10} entries")
                for line in lines[-10:]:
                    if line.strip():
                        self.log("*", f"    {line.strip()[:100]}")
        except Exception:
            pass

    def analyze_crypto(self, fp: Path):
        try:
            with open(fp) as f:
                content = f.read()
            if "PRIVATE KEY" in content:
                self.log("!", f"  [CRYPTO] {fp.name}: 私钥文件！")
            if "PUBLIC KEY" in content:
                self.log("*", f"  [CRYPTO] {fp.name}: 公钥文件")
        except Exception:
            pass

    # ================================================================
    # 阶段 5: 证据链关联
    # ================================================================
    def correlate_evidence(self, findings: list[dict]):
        """尝试建立证据之间的关联"""
        self.log("*", "证据链关联分析...")

        # 按文件类型分组
        by_type = defaultdict(list)
        for f in findings:
            by_type[f.get("ext", "unknown")].append(f)

        # 检测关联模式
        correlations = []

        # 模式 1: .enc + .pem/.key → 加密文件 + 密钥
        if by_type.get(".enc") and (by_type.get(".pem") or by_type.get(".key")):
            correlations.append("检测到加密文件(.enc) + 密钥文件(.pem/.key) → 尝试解密")

        # 模式 2: .zip/.rar/.7z + 字符串中的 password → 加密压缩包 + 密码线索
        if by_type.get(".zip") or by_type.get(".rar") or by_type.get(".7z"):
            for f in findings:
                if any(kw in str(f.get("hits", [])).lower() for kw in ["password", "密码", "pass"]):
                    correlations.append(f"加密压缩包 + 密码线索({f['file']}) → 尝试解压")
                    break

        # 模式 3: 多个文件命中同一关键词 → 可能属于同一证据链
        keyword_groups = defaultdict(list)
        for f in findings:
            for hit in f.get("hits", []):
                keyword_groups[hit].append(f["file"])
        for kw, files in keyword_groups.items():
            if len(files) >= 3:
                correlations.append(f"关键词 '{kw}' 出现在 {len(files)} 个文件中 → 证据链")

        for c in correlations:
            self.log("!", f"  {c}")

    # ================================================================
    # 主流程
    # ================================================================
    def hunt(self):
        self.log("+", f"Smart Hunter 启动 — 案件目录: {self.case_dir}")
        self.log("+", f"题目数: {len(self.questions)}")

        # Step 1: 解析题目 → 搜索策略
        strategy = self.analyze_questions()
        self.log("+", f"策略: paths={len(strategy['paths'])}, patterns={len(strategy['patterns'])}, tools={strategy['tools']}")

        # Step 2: 发现文件
        files = self.discover_files(strategy)
        if not files:
            self.log("-", "未发现目标文件，扩展为全盘搜索")
            files = self.discover_files({"paths": ["."], "patterns": ["flag"], "tools": ["strings"]})

        # Step 3: 并行快速扫描
        hits = self.parallel_scan(files, strategy["patterns"])
        self.log("+", f"扫描完成: {len(hits)}/{len(files)} 个文件命中")

        # Step 4: 深度分析
        if hits:
            self.deep_analyze(hits)

        # Step 5: 证据链
        self.correlate_evidence(hits)

        # 结果
        self.log("+", f"总耗时: {(datetime.now() - self.start_time).total_seconds():.1f}s")
        self.log("+", f"命中文件: {len(hits)}")

        return {
            "strategy": strategy,
            "total_files": len(files),
            "hits": hits,
            "time": (datetime.now() - self.start_time).total_seconds(),
        }


def main():
    parser = argparse.ArgumentParser(description="CTF 电子取证智能分析引擎")
    parser.add_argument("-c", "--case", required=True, help="案件目录路径")
    parser.add_argument("-q", "--questions", nargs="*", help="题目文本，支持多个")
    parser.add_argument("--auto", action="store_true", help="自动模式（不指定题目，通用扫描）")
    parser.add_argument("-w", "--workers", type=int, default=8, help="并行线程数")
    args = parser.parse_args()

    questions = args.questions or []
    if args.auto:
        questions = ["flag password secret key token 密码"]

    hunter = SmartHunter(args.case, questions)
    results = hunter.hunt()

    # 输出 JSON 结果（可被其他工具消费）
    output_file = Path(args.case) / "smart_hunter_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n结果已保存: {output_file}")


if __name__ == "__main__":
    main()
