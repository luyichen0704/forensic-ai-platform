#!/usr/bin/env python3
"""
APK 批量分析器 — 手机取证"APK 工厂"专用
========================================
来源: 2025数证杯决赛经验 — 手机取证 = 大量 APK + JSON 配置

用法:
  python apk_batch_analyzer.py -d ./phone/apks/               # 批量分析
  python apk_batch_analyzer.py -d ./phone/apks/ --jadx-dir ./sources/  # 反编译
  python apk_batch_analyzer.py -d ./phone/ --find-configs     # 查找所有 JSON 配置
"""
import os
import re
import json
import sys
import zipfile
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse


class APKBatchAnalyzer:
    def __init__(self, target_dir: str, jadx_dir: str | None = None, max_workers: int = 8):
        self.target_dir = Path(target_dir)
        self.jadx_dir = Path(jadx_dir) if jadx_dir else None
        self.max_workers = max_workers
        self.findings = []

    def find_apks(self) -> list[Path]:
        """递归查找所有 APK 文件"""
        apks = list(self.target_dir.rglob("*.apk"))
        # 也检查 .zip 中嵌套的 APK
        zips = list(self.target_dir.rglob("*.zip"))
        for zf in zips:
            try:
                with zipfile.ZipFile(zf) as z:
                    apks_in_zip = [zf / n for n in z.namelist() if n.endswith(".apk")]
            except Exception:
                pass

        print(f"发现 {len(apks)} 个 APK 文件")
        return apks

    def extract_manifest_info(self, apk_path: Path) -> dict:
        """从 APK 中快速提取 AndroidManifest.xml 关键信息（不解包全量）"""
        info = {"name": apk_path.name, "path": str(apk_path), "size": apk_path.stat().st_size}
        try:
            with zipfile.ZipFile(apk_path) as z:
                # 提取包名
                if "AndroidManifest.xml" in z.namelist():
                    raw = z.read("AndroidManifest.xml")
                    # 尝试 AXMLL 解析（二进制 XML）
                    try:
                        import xmltodict
                        from androguard.core.bytecodes.axml import AXMLPrinter
                        axml = AXMLPrinter(raw)
                        xml_str = axml.get_xml()
                        d = xmltodict.parse(xml_str)
                        manifest = d.get("manifest", {})
                        info["package"] = manifest.get("@package", "unknown")

                        # 提取权限
                        uses_perms = manifest.get("uses-permission", [])
                        if not isinstance(uses_perms, list):
                            uses_perms = [uses_perms]
                        info["permissions"] = [p.get("@android:name", "") for p in uses_perms]

                        # 提取可导出组件
                        app = manifest.get("application", {})
                        for comp_type in ["activity", "service", "receiver", "provider"]:
                            comps = app.get(comp_type, [])
                            if not isinstance(comps, list):
                                comps = [comps]
                            exported = [c.get("@android:name", "") for c in comps
                                       if c.get("@android:exported") == "true"]
                            if exported:
                                info.setdefault("exported_components", {})[comp_type] = exported
                    except ImportError:
                        # 降级：简单字符串提取
                        text = raw.decode("utf-8", errors="replace")
                        pkg_match = re.search(r'package="([^"]+)"', text)
                        if pkg_match:
                            info["package"] = pkg_match.group(1)

                # 查找 assets/ 中的 JSON 配置
                json_configs = [n for n in z.namelist() if n.endswith((".json", ".cfg", ".ini")) and n.startswith("assets/")]
                if json_configs:
                    info["json_configs"] = json_configs

                # 查找 native libraries
                native_libs = [n for n in z.namelist() if n.endswith(".so")]
                if native_libs:
                    info["native_libs"] = native_libs

                # 查找加密算法使用痕迹
                dex_files = [n for n in z.namelist() if n.endswith(".dex")]
                info["dex_count"] = len(dex_files)

        except Exception as e:
            info["error"] = str(e)

        return info

    def batch_analyze_manifests(self, apks: list[Path]) -> list[dict]:
        """并行分析所有 APK 的 Manifest"""
        results = []
        print(f"并行分析 {len(apks)} 个 APK 的 Manifest...")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.extract_manifest_info, apk): apk for apk in apks}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        # 按包名排序
        results.sort(key=lambda x: x.get("package", "zzz"))
        return results

    def find_json_configs(self) -> list[Path]:
        """查找所有 JSON/配置文件（适配手机镜像）"""
        configs = []
        for ext in ["*.json", "*.cfg", "*.ini", "*.conf", "*.xml", "*.plist", "*.yaml", "*.yml",
                     "Adlockdown.json", "com.apple.*.plist"]:
            configs.extend(self.target_dir.rglob(ext))
        return configs

    def analyze_json_config(self, config_path: Path) -> dict | None:
        """分析单个 JSON 配置文件，提取敏感字段"""
        try:
            with open(config_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            sensitive_fields = {}
            # 敏感关键词
            keywords = [
                "password", "passwd", "pass", "pwd", "secret", "key", "token",
                "apikey", "api_key", "access_key", "private", "credential",
                "username", "user", "login", "email", "phone", "mobile",
                "serial", "serialNumber", "IMEI", "UDID", "deviceId",
                "host", "port", "server", "endpoint", "url", "proxy",
                "encrypt", "decrypt", "cipher", "hash", "rsa", "aes",
            ]

            for kw in keywords:
                pattern = rf'["\']?{kw}["\']?\s*[:=]\s*["\']?([^"\',\s}}]+)'
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    sensitive_fields[kw] = matches[:5]  # 最多 5 个匹配

            if sensitive_fields:
                return {
                    "path": str(config_path),
                    "size": len(content),
                    "sensitive": sensitive_fields,
                }
        except Exception:
            pass
        return None

    def batch_analyze_configs(self, configs: list[Path]) -> list[dict]:
        """并行分析所有 JSON 配置"""
        results = []
        print(f"并行分析 {len(configs)} 个配置文件...")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.analyze_json_config, c): c for c in configs}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        return results

    def run(self):
        print(f"APK 批量分析器 — 目标: {self.target_dir}")
        print("=" * 60)

        # Phase 1: APK 分析
        apks = self.find_apks()
        if apks:
            manifest_results = self.batch_analyze_manifests(apks)

            # 输出 APK 分析报告
            print(f"\n{'='*60}")
            print(f"APK 分析报告 ({len(manifest_results)} 个)")
            print(f"{'='*60}")

            for r in manifest_results:
                pkg = r.get("package", "unknown")
                perms = r.get("permissions", [])
                exported = r.get("exported_components", {})
                native = r.get("native_libs", [])
                configs = r.get("json_configs", [])
                dex_count = r.get("dex_count", 0)

                print(f"\n📱 {r['name']}")
                print(f"   包名: {pkg}")
                print(f"   大小: {r['size']:,} bytes")
                print(f"   DEX: {dex_count} 个")
                print(f"   Native .so: {len(native)} 个")
                print(f"   JSON 配置: {len(configs)} 个")

                # 标记高风险 APK
                flags = []
                if any("SEND_SMS" in p for p in perms):
                    flags.append("⚠ SMS 权限")
                if any("READ_CONTACTS" in p for p in perms):
                    flags.append("⚠ 读取联系人")
                if any("ACCESS_FINE_LOCATION" in p for p in perms):
                    flags.append("⚠ 定位权限")
                if any("CAMERA" in p for p in perms):
                    flags.append("⚠ 相机权限")
                if any("RECORD_AUDIO" in p for p in perms):
                    flags.append("⚠ 录音权限")
                if exported:
                    flags.append(f"🔴 可导出组件: {list(exported.keys())}")
                if "error" in r:
                    flags.append(f"❌ 解析错误: {r['error']}")

                for flag in flags:
                    print(f"   {flag}")

            self.findings.extend(manifest_results)

        # Phase 2: JSON 配置分析
        configs = self.find_json_configs()
        if configs:
            config_results = self.batch_analyze_configs(configs)

            print(f"\n{'='*60}")
            print(f"JSON 配置分析 ({len(config_results)} 个命中)")
            print(f"{'='*60}")

            for r in sorted(config_results, key=lambda x: len(x.get("sensitive", {})), reverse=True)[:30]:
                print(f"\n📄 {Path(r['path']).name}")
                print(f"   路径: {r['path']}")
                for field, values in r.get("sensitive", {}).items():
                    print(f"   {field}: {values}")

        # 汇总
        print(f"\n{'='*60}")
        print(f"分析完成: {len(apks)} APK + {len(configs)} 配置文件")
        print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="APK 批量分析器 — 手机取证专用")
    parser.add_argument("-d", "--dir", required=True, help="目标目录（手机镜像提取后的文件）")
    parser.add_argument("--jadx-dir", help="jadx 反编译输出目录")
    parser.add_argument("--find-configs", action="store_true", help="仅查找 JSON 配置")
    parser.add_argument("-w", "--workers", type=int, default=8, help="并行线程数")

    args = parser.parse_args()

    analyzer = APKBatchAnalyzer(args.dir, args.jadx_dir, args.workers)
    analyzer.run()


if __name__ == "__main__":
    main()
