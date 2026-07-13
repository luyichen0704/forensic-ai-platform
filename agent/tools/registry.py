"""
取证工具注册表 - 管理所有取证工具的元数据
不包含工具二进制，只记录命令模板和安装方式
"""
import os
import shutil
import subprocess
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ToolCategory(Enum):
    """工具类别"""
    DISK_FORENSICS = "disk_forensics"
    NETWORK_ANALYSIS = "network_analysis"
    MEMORY_FORENSICS = "memory_forensics"
    FILE_ANALYSIS = "file_analysis"
    ANDROID_ANALYSIS = "android_analysis"
    CRYPTO = "crypto"
    STEGO = "stego"
    REVERSE = "reverse"
    SYSTEM = "system"
    ENCODING = "encoding"

@dataclass
class ToolInfo:
    """工具信息"""
    name: str
    category: ToolCategory
    description: str
    command_template: str
    install_command: str
    check_command: str
    output_format: str = "text"  # text, json, xml, binary
    requires_evidence: bool = True
    priority: int = 1  # 1-5, 1为最高
    dependencies: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)

class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self.tools: Dict[str, ToolInfo] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """注册默认工具集"""
        
        # ==================== 磁盘取证工具 ====================
        self.register(ToolInfo(
            name="sleuthkit",
            category=ToolCategory.DISK_FORENSICS,
            description="The Sleuth Kit - 磁盘镜像取证工具套件",
            command_template="fls -r {evidence_path}",
            install_command="scoop install sleuthkit",
            check_command="fls -V",
            output_format="text",
            examples=[
                "fls -r image.E01",
                "icat image.E01 inode > recovered_file",
                "mmls image.E01"
            ]
        ))
        
        self.register(ToolInfo(
            name="autopsy",
            category=ToolCategory.DISK_FORENSICS,
            description="Autopsy - 数字取证平台",
            command_template="autopsy {evidence_path}",
            install_command="下载安装 Autopsy: https://www.autopsy.com/",
            check_command="autopsy --version",
            output_format="gui",
            requires_evidence=True
        ))
        
        self.register(ToolInfo(
            name="e01tools",
            category=ToolCategory.DISK_FORENSICS,
            description="E01镜像处理工具",
            command_template="ewfinfo {evidence_path}",
            install_command="pip install libewf-python",
            check_command="ewfinfo -V",
            output_format="text"
        ))
        
        # ==================== 网络分析工具 ====================
        self.register(ToolInfo(
            name="tshark",
            category=ToolCategory.NETWORK_ANALYSIS,
            description="TShark - 网络协议分析器",
            command_template="tshark -r {evidence_path} {args}",
            install_command="scoop install wireshark",
            check_command="tshark --version",
            output_format="text",
            examples=[
                "tshark -r capture.pcap -q -z io,phs",
                "tshark -r capture.pcap -Y 'http.request'",
                "tshark -r capture.pcap -q -z conv,ip"
            ]
        ))
        
        self.register(ToolInfo(
            name="tcpdump",
            category=ToolCategory.NETWORK_ANALYSIS,
            description="Tcpdump - 网络抓包工具",
            command_template="tcpdump -r {evidence_path} {args}",
            install_command="scoop install tcpdump",
            check_command="tcpdump --version",
            output_format="text"
        ))
        
        # ==================== 内存取证工具 ====================
        self.register(ToolInfo(
            name="volatility3",
            category=ToolCategory.MEMORY_FORENSICS,
            description="Volatility 3 - 内存取证框架",
            command_template="vol -f {evidence_path} {plugin} {args}",
            install_command="pip install volatility3",
            check_command="vol --version",
            output_format="text",
            examples=[
                "vol -f memory.raw windows.info",
                "vol -f memory.raw windows.pslist",
                "vol -f memory.raw windows.netscan"
            ]
        ))
        
        # ==================== 文件分析工具 ====================
        self.register(ToolInfo(
            name="file",
            category=ToolCategory.FILE_ANALYSIS,
            description="File - 文件类型识别",
            command_template="file {evidence_path}",
            install_command="安装 Git for Windows",
            check_command="file --version",
            output_format="text"
        ))
        
        self.register(ToolInfo(
            name="strings",
            category=ToolCategory.FILE_ANALYSIS,
            description="Strings - 提取可打印字符串",
            command_template="strings {evidence_path} {args}",
            install_command="安装 Git for Windows",
            check_command="strings --version",
            output_format="text",
            examples=[
                "strings file.bin | head -100",
                "strings -n 8 file.bin",
                "strings -e l file.bin (Unicode)"
            ]
        ))
        
        self.register(ToolInfo(
            name="exiftool",
            category=ToolCategory.FILE_ANALYSIS,
            description="ExifTool - 元数据提取工具",
            command_template="exiftool {evidence_path}",
            install_command="scoop install exiftool",
            check_command="exiftool -ver",
            output_format="text"
        ))
        
        self.register(ToolInfo(
            name="binwalk",
            category=ToolCategory.FILE_ANALYSIS,
            description="Binwalk - 固件分析工具",
            command_template="binwalk {evidence_path} {args}",
            install_command="pip install binwalk",
            check_command="binwalk --help",
            output_format="text",
            examples=[
                "binwalk firmware.bin",
                "binwalk -e firmware.bin (提取)"
            ]
        ))
        
        self.register(ToolInfo(
            name="xxd",
            category=ToolCategory.FILE_ANALYSIS,
            description="xxd - 十六进制转储",
            command_template="xxd {evidence_path} {args}",
            install_command="安装 Git for Windows",
            check_command="xxd --version",
            output_format="text"
        ))
        
        # ==================== Android分析工具 ====================
        self.register(ToolInfo(
            name="jadx",
            category=ToolCategory.ANDROID_ANALYSIS,
            description="JADX - Android反编译器",
            command_template="jadx -d {output_dir} {evidence_path}",
            install_command="scoop install jadx",
            check_command="jadx --version",
            output_format="text",
            examples=[
                "jadx -d output app.apk",
                "jadx --show-bad-code app.apk"
            ]
        ))
        
        self.register(ToolInfo(
            name="apktool",
            category=ToolCategory.ANDROID_ANALYSIS,
            description="ApkTool - APK反编译工具",
            command_template="apktool d {evidence_path} -o {output_dir}",
            install_command="scoop install apktool",
            check_command="apktool --version",
            output_format="text"
        ))
        
        # ==================== 密码学工具 ====================
        self.register(ToolInfo(
            name="hashcat",
            category=ToolCategory.CRYPTO,
            description="Hashcat - 密码破解工具",
            command_template="hashcat -m {hash_type} {hash_file} {wordlist}",
            install_command="scoop install hashcat",
            check_command="hashcat --version",
            output_format="text",
            examples=[
                "hashcat -m 0 hash.txt wordlist.txt (MD5)",
                "hashcat -m 1000 hash.txt wordlist.txt (NTLM)"
            ]
        ))
        
        self.register(ToolInfo(
            name="john",
            category=ToolCategory.CRYPTO,
            description="John the Ripper - 密码破解工具",
            command_template="john {hash_file} --wordlist={wordlist}",
            install_command="scoop install john",
            check_command="john --version",
            output_format="text"
        ))
        
        self.register(ToolInfo(
            name="openssl",
            category=ToolCategory.CRYPTO,
            description="OpenSSL - 加密工具",
            command_template="openssl {command} {args}",
            install_command="scoop install openssl",
            check_command="openssl version",
            output_format="text",
            examples=[
                "openssl enc -d -aes-256-cbc -in encrypted.bin",
                "openssl dgst -sha256 file.txt"
            ]
        ))
        
        # ==================== 隐写分析工具 ====================
        self.register(ToolInfo(
            name="steghide",
            category=ToolCategory.STEGO,
            description="Steghide - 隐写提取工具",
            command_template="steghide extract -sf {evidence_path} {args}",
            install_command="scoop install steghide",
            check_command="steghide --version",
            output_format="text",
            examples=[
                "steghide extract -sf image.jpg",
                "steghide extract -sf image.jpg -p password"
            ]
        ))
        
        self.register(ToolInfo(
            name="zsteg",
            category=ToolCategory.STEGO,
            description="zsteg - PNG/BMP隐写检测",
            command_template="zsteg {evidence_path} {args}",
            install_command="gem install zsteg",
            check_command="zsteg --version",
            output_format="text"
        ))
        
        self.register(ToolInfo(
            name="stegoveritas",
            category=ToolCategory.STEGO,
            description="StegoVeritas - 综合隐写分析",
            command_template="stegoveritas {evidence_path} {args}",
            install_command="pip install stegoveritas",
            check_command="stegoveritas --help",
            output_format="text"
        ))
        
        # ==================== 逆向工程工具 ====================
        self.register(ToolInfo(
            name="radare2",
            category=ToolCategory.REVERSE,
            description="Radare2 - 逆向工程框架",
            command_template="r2 -A {evidence_path}",
            install_command="scoop install radare2",
            check_command="r2 -v",
            output_format="text",
            examples=[
                "r2 -A binary.exe",
                "r2 -c 'aaa; pdf' binary.exe"
            ]
        ))
        
        self.register(ToolInfo(
            name="objdump",
            category=ToolCategory.REVERSE,
            description="objdump - 目标文件分析",
            command_template="objdump -d {evidence_path}",
            install_command="安装 Git for Windows 或 MinGW",
            check_command="objdump --version",
            output_format="text"
        ))
        
        # ==================== 系统工具 ====================
        self.register(ToolInfo(
            name="grep",
            category=ToolCategory.SYSTEM,
            description="grep - 文本搜索",
            command_template="grep {args} {pattern} {evidence_path}",
            install_command="scoop install ripgrep (rg)",
            check_command="grep --version",
            output_format="text",
            examples=[
                "grep -r 'password' .",
                "rg -i 'secret' file.txt"
            ]
        ))
        
        self.register(ToolInfo(
            name="7z",
            category=ToolCategory.SYSTEM,
            description="7-Zip - 压缩解压工具",
            command_template="7z {command} {evidence_path} {args}",
            install_command="scoop install 7zip",
            check_command="7z",
            output_format="text"
        ))
        
        self.register(ToolInfo(
            name="sqlite3",
            category=ToolCategory.SYSTEM,
            description="SQLite3 - 数据库查询",
            command_template="sqlite3 {evidence_path} \"{query}\"",
            install_command="scoop install sqlite",
            check_command="sqlite3 --version",
            output_format="text"
        ))
        
        # ==================== 编码工具 ====================
        self.register(ToolInfo(
            name="base64",
            category=ToolCategory.ENCODING,
            description="Base64编解码",
            command_template="echo '{text}' | base64 -d",
            install_command="系统自带",
            check_command="base64 --version",
            output_format="text"
        ))
        
    def register(self, tool: ToolInfo):
        """注册工具"""
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[ToolInfo]:
        """获取工具信息"""
        return self.tools.get(name)
    
    def get_tools_by_category(self, category: ToolCategory) -> List[ToolInfo]:
        """按类别获取工具"""
        return [t for t in self.tools.values() if t.category == category]
    
    def get_all_tools(self) -> List[ToolInfo]:
        """获取所有工具"""
        return list(self.tools.values())
    
    def check_tool_available(self, name: str) -> bool:
        """检查工具是否可用"""
        tool = self.tools.get(name)
        if not tool:
            return False
        
        try:
            result = subprocess.run(
                tool.check_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def check_all_tools(self) -> Dict[str, bool]:
        """检查所有工具状态"""
        status = {}
        for name, tool in self.tools.items():
            status[name] = self.check_tool_available(name)
        return status
    
    def get_missing_tools(self) -> List[ToolInfo]:
        """获取缺失的工具"""
        missing = []
        for name, tool in self.tools.items():
            if not self.check_tool_available(name):
                missing.append(tool)
        return missing
    
    def get_install_script(self, os_type: str = "windows") -> str:
        """生成安装脚本"""
        if os_type == "windows":
            lines = ['@echo off', 'echo 正在安装取证工具...', '']
            
            # 按类别分组
            categories = {}
            for tool in self.tools.values():
                if tool.install_command.startswith("scoop"):
                    cat = tool.category.value
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append(tool)
            
            for cat, tools in categories.items():
                lines.append(f'echo 安装 {cat} 工具...')
                for tool in tools:
                    pkg = tool.install_command.replace("scoop install ", "")
                    lines.append(f'scoop install {pkg}')
                lines.append('')
            
            lines.append('echo 安装完成！')
            lines.append('pause')
            return '\n'.join(lines)
        
        else:  # linux/mac
            lines = ['#!/bin/bash', 'echo "正在安装取证工具..."', '']
            
            for tool in self.tools.values():
                if tool.install_command.startswith("pip"):
                    lines.append(tool.install_command)
                elif tool.install_command.startswith("apt"):
                    lines.append(tool.install_command)
            
            lines.append('')
            lines.append('echo "安装完成！"')
            return '\n'.join(lines)

# 全局实例
registry = ToolRegistry()
