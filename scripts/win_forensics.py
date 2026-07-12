#!/usr/bin/env python3
"""
Windows 取证快速分析器
======================
覆盖: 注册表解析 · Prefetch 分析 · 事件日志摘要 · LNK 文件解析 · 浏览器历史

用法:
  python win_forensics.py -d ./windows_partition/
  python win_forensics.py -d ./windows_partition/ --type registry
"""
import os
import re
import sys
import struct
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


class WinForensics:
    def __init__(self, root_dir: str):
        self.root = Path(root_dir)
        self.findings = defaultdict(list)

    def find_path(self, *patterns: str) -> Path | None:
        """在 Windows 分区中查找路径"""
        for pattern in patterns:
            # 尝试多个基路径
            for base in ["", "Windows", "Users", "ProgramData", "Program Files"]:
                full = self.root / base / pattern
                if full.exists():
                    return full
                # 也搜索子目录
                matches = list(self.root.rglob(pattern))
                if matches:
                    return matches[0]
        return None

    # ================================================================
    # 1. 注册表解析
    # ================================================================
    def parse_registry(self):
        """解析关键注册表项"""
        print("\n--- 注册表分析 ---")

        # SAM 文件位置
        sam_paths = [
            "Windows/System32/config/SAM",
            "Windows/System32/config/SYSTEM",
            "Windows/System32/config/SOFTWARE",
            "Windows/System32/config/SECURITY",
            "Windows/System32/config/NTUSER.DAT",
        ]

        for p in sam_paths:
            full = self.root / p
            if full.exists():
                size_mb = full.stat().st_size / (1024 * 1024)
                print(f"  📁 {p} ({size_mb:.1f} MB)")

        # 用户 NTUSER.DAT
        for ntuser in self.root.rglob("NTUSER.DAT"):
            rel = ntuser.relative_to(self.root)
            print(f"  👤 {rel}")
            self.findings["registry"].append(str(rel))

    # ================================================================
    # 2. Prefetch 分析
    # ================================================================
    def parse_prefetch(self):
        """分析 Prefetch 文件 — 重建程序执行历史"""
        print("\n--- Prefetch 分析 ---")

        prefetch_dir = self.root / "Windows/Prefetch"
        if not prefetch_dir.exists():
            prefetch_dir = self.root / "Windows/Prefetch"  # 直接搜索
            matches = list(self.root.rglob("*.pf"))
            if not matches:
                print("  未找到 Prefetch 文件")
                return
            prefetch_files = [(m, m.stat()) for m in matches]
        else:
            prefetch_files = [(pf, pf.stat()) for pf in prefetch_dir.glob("*.pf")]

        # 按修改时间排序
        prefetch_files.sort(key=lambda x: x[1].st_mtime, reverse=True)

        print(f"  共 {len(prefetch_files)} 个 Prefetch 文件")
        suspicious_keywords = [
            "cmd", "powershell", "wmic", "regedit", "net", "netstat",
            "whoami", "tasklist", "procdump", "mimikatz", "psexec",
            "nc", "ncat", "certutil", "bitsadmin", "rundll32",
            "mshta", "cscript", "wscript", "schtasks",
            "encrypt", "decrypt", "ransom", "locker", "miner",
            "7z", "winrar", "veracrypt", "bitlocker",
            "putty", "winscp", "filezilla", "teamviewer", "anydesk",
        ]

        for i, (pf_path, stat) in enumerate(prefetch_files[:50]):  # 最近 50 个
            name = pf_path.stem.lower()
            mtime = datetime.fromtimestamp(stat.st_mtime)
            run_count = self._extract_prefetch_run_count(pf_path)

            flagged = any(kw in name for kw in suspicious_keywords)
            marker = "🔴" if flagged else "  "
            print(f"  {marker} {pf_path.name[:50]:50s}  {mtime.strftime('%Y-%m-%d %H:%M')}  run={run_count}")

            if flagged:
                matched = [kw for kw in suspicious_keywords if kw in name]
                self.findings["prefetch_suspicious"].append(f"{pf_path.name} → {matched}")

    def _extract_prefetch_run_count(self, pf_path: Path) -> int:
        """从 Prefetch 文件提取运行次数"""
        try:
            with open(pf_path, "rb") as f:
                f.seek(0x90)  # Windows 10+ run count offset
                return struct.unpack("<I", f.read(4))[0]
        except Exception:
            return 0

    # ================================================================
    # 3. 事件日志摘要
    # ================================================================
    def parse_event_logs(self):
        """提取 Windows 事件日志关键信息"""
        print("\n--- 事件日志分析 ---")

        log_dir = self.find_path("System32/winevt/Logs")
        if not log_dir:
            log_dir = self.find_path("winevt/Logs")
        if not log_dir:
            print("  未找到事件日志目录")
            return

        key_logs = {
            "Security.evtx": "安全日志（登录/权限变更）",
            "System.evtx": "系统日志（服务/驱动）",
            "Application.evtx": "应用日志（程序崩溃）",
            "Microsoft-Windows-TerminalServices-LocalSessionManager%4Operational.evtx": "RDP 连接",
            "Microsoft-Windows-TaskScheduler%4Operational.evtx": "计划任务",
            "Microsoft-Windows-PowerShell%4Operational.evtx": "PowerShell 执行",
        }

        for log_name, desc in key_logs.items():
            log_path = log_dir / log_name
            if log_path.exists():
                size_mb = log_path.stat().st_size / (1024 * 1024)
                mtime = datetime.fromtimestamp(log_path.stat().st_mtime)
                print(f"  📋 {desc}: {log_name} ({size_mb:.1f} MB, last: {mtime.strftime('%Y-%m-%d %H:%M')})")
                self.findings["event_logs"].append(f"{desc} → {size_mb:.1f} MB")
            else:
                # 通配符搜索
                matches = list(log_dir.glob(log_name.replace("%4", "*")))
                for m in matches:
                    print(f"  📋 {desc}: {m.name} ({m.stat().st_size / 1024:.1f} KB)")

        # 列出最大的 10 个日志（可能包含异常活动）
        all_logs = sorted(
            [(lg, lg.stat().st_size) for lg in log_dir.glob("*.evtx")],
            key=lambda x: x[1], reverse=True
        )[:10]
        print(f"\n  最大的 10 个日志文件:")
        for lg, size in all_logs:
            print(f"    {lg.name}: {size / (1024*1024):.1f} MB")

    # ================================================================
    # 4. LNK 文件分析
    # ================================================================
    def parse_lnk_files(self):
        """分析 .lnk 文件 — 最近打开的文件"""
        print("\n--- LNK 文件分析 ---")

        # 常见 LNK 位置
        lnk_dirs = [
            "Users/*/AppData/Roaming/Microsoft/Windows/Recent",
            "Users/*/AppData/Roaming/Microsoft/Office/Recent",
        ]

        all_lnks = []
        for pattern in lnk_dirs:
            for lnk in self.root.glob(pattern + "/*.lnk"):
                mtime = datetime.fromtimestamp(lnk.stat().st_mtime)
                all_lnks.append((lnk, mtime))

        # 也全局搜索
        if len(all_lnks) < 10:
            for lnk in list(self.root.rglob("*.lnk"))[:100]:
                if lnk not in [l for l, _ in all_lnks]:
                    mtime = datetime.fromtimestamp(lnk.stat().st_mtime)
                    all_lnks.append((lnk, mtime))

        all_lnks.sort(key=lambda x: x[1], reverse=True)

        print(f"  共 {len(all_lnks)} 个 LNK 文件")
        for lnk, mtime in all_lnks[:30]:
            try:
                # 提取 LNK 目标路径
                with open(lnk, "rb") as f:
                    f.seek(0x4C)
                    flags = struct.unpack("<I", f.read(4))[0]
                has_target = bool(flags & 0x01)
                marker = "🔗" if has_target else "  "
                rel = lnk.relative_to(self.root) if self.root in lnk.parents else lnk
                print(f"  {marker} {str(rel)[:60]:60s}  {mtime.strftime('%Y-%m-%d %H:%M')}")
            except Exception:
                pass

    # ================================================================
    # 5. 浏览器历史数据库
    # ================================================================
    def parse_browser_history(self):
        """提取浏览器历史记录"""
        print("\n--- 浏览器历史分析 ---")

        browser_patterns = {
            "Chrome": "Users/*/AppData/Local/Google/Chrome/User Data/Default/History",
            "Edge": "Users/*/AppData/Local/Microsoft/Edge/User Data/Default/History",
            "Firefox": "Users/*/AppData/Roaming/Mozilla/Firefox/Profiles/*/places.sqlite",
        }

        for browser, pattern in browser_patterns.items():
            for db_path in self.root.glob(pattern):
                try:
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.cursor()

                    # 最近的 20 条历史
                    rows = cursor.execute(
                        "SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 20"
                    ).fetchall()

                    if rows:
                        print(f"\n  🌐 {browser} ({len(rows)} 条最近记录):")
                        for url, title, timestamp in rows:
                            # Chrome 时间戳是 1601-01-01 起的微秒
                            try:
                                ts = datetime(1601, 1, 1) + timedelta(microseconds=timestamp)
                                ts_str = ts.strftime("%Y-%m-%d %H:%M")
                            except Exception:
                                ts_str = str(timestamp)
                            title_str = (title or "")[:50]
                            url_str = (url or "")[:80]
                            print(f"    {ts_str} | {title_str}")
                            print(f"           {url_str}")

                            # 标记可疑 URL
                            suspicious_domains = [
                                "pastebin", "anonfiles", "mega.nz", "mediafire",
                                "transfer.sh", "file.io", "gofile", "wormhole",
                                "bitcoin", "monero", "wallet", "ransom",
                                "phishing", "malware", "exploit", "payload",
                            ]
                            if any(d in (url or "").lower() for d in suspicious_domains):
                                print(f"           🔴 可疑!")
                                self.findings["suspicious_urls"].append(url)

                    conn.close()
                except Exception as e:
                    print(f"  ⚠ {browser} 解析错误: {e}")

    # ================================================================
    # 6. 程序安装/卸载记录
    # ================================================================
    def parse_installed_programs(self):
        """列出已安装程序"""
        print("\n--- 已安装程序 ---")
        # 检查 Program Files 目录
        for pf in ["Program Files", "Program Files (x86)"]:
            pf_dir = self.root / pf
            if pf_dir.exists():
                programs = [d for d in pf_dir.iterdir() if d.is_dir()]
                for prog in sorted(programs, key=lambda x: x.name.lower()):
                    # 标记取证/安全相关工具
                    sec_tools = [
                        "wireshark", "nmap", "metasploit", "burp", "sqlmap",
                        "veracrypt", "truecrypt", "bitlocker", "keepass",
                        "tor", "vpn", "proxy", "tunnel", "hashcat", "john",
                        "python", "java", "golang", "nodejs", "git",
                        "teamviewer", "anydesk", "putty", "winscp", "filezilla",
                    ]
                    flagged = any(t in prog.name.lower() for t in sec_tools)
                    marker = "🔧" if flagged else "  "
                    print(f"  {marker} {prog.name}")

    # ================================================================
    # 主流程
    # ================================================================
    def run(self):
        print(f"Windows 取证分析器 — 目标: {self.root}")
        print("=" * 60)

        # 基础信息
        print(f"\n--- 基础信息 ---")
        for p in ["Windows/System32", "Users", "ProgramData", "Program Files"]:
            if (self.root / p).exists():
                print(f"  ✅ {p}")
            else:
                print(f"  ❌ {p} (未找到)")

        self.parse_registry()
        self.parse_prefetch()
        self.parse_event_logs()
        self.parse_lnk_files()
        self.parse_browser_history()
        self.parse_installed_programs()

        # 汇总
        print(f"\n{'='*60}")
        print(f"分析完成 — 关键发现:")
        for category, items in self.findings.items():
            if items:
                print(f"  [{category}]: {len(items)} 项")
                for item in items[:5]:
                    print(f"    → {item}")

        print(f"\n提示: 使用 fireye-evidence 在 GUI 中查看完整注册表和事件日志")
        return self.findings


def main():
    parser = argparse.ArgumentParser(description="Windows 取证快速分析器")
    parser.add_argument("-d", "--dir", required=True, help="Windows 分区挂载目录")
    parser.add_argument("--type", choices=["registry", "prefetch", "logs", "lnk", "browser", "all"],
                       default="all", help="分析类型")
    args = parser.parse_args()

    wf = WinForensics(args.dir)
    wf.run()


if __name__ == "__main__":
    main()
