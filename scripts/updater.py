"""
项目自动更新器 - 让用户轻松同步最新版本
支持: Git拉取、增量更新、版本检查
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

class ProjectUpdater:
    """项目更新器"""
    
    def __init__(self, project_dir: str = None):
        self.project_dir = project_dir or os.getcwd()
        self.version_file = os.path.join(self.project_dir, "VERSION")
        self.config_file = os.path.join(self.project_dir, "update_config.json")
        
    def get_current_version(self) -> str:
        """获取当前版本"""
        if os.path.exists(self.version_file):
            with open(self.version_file, 'r') as f:
                return f.read().strip()
        return "0.0.0"
    
    def get_remote_version(self) -> Optional[str]:
        """获取远程版本"""
        try:
            # 获取远程VERSION文件
            result = subprocess.run(
                ["git", "show", "origin/main:VERSION"],
                capture_output=True,
                text=True,
                cwd=self.project_dir
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None
    
    def check_for_updates(self) -> Dict[str, Any]:
        """检查更新"""
        # 先fetch最新信息
        subprocess.run(
            ["git", "fetch", "origin"],
            capture_output=True,
            cwd=self.project_dir
        )
        
        current = self.get_current_version()
        remote = self.get_remote_version()
        
        # 获取更新日志
        changelog = self._get_changelog()
        
        return {
            "current_version": current,
            "remote_version": remote,
            "update_available": current != remote,
            "changelog": changelog
        }
    
    def _get_changelog(self) -> str:
        """获取更新日志"""
        try:
            result = subprocess.run(
                ["git", "log", "HEAD..origin/main", "--oneline", "-10"],
                capture_output=True,
                text=True,
                cwd=self.project_dir
            )
            if result.returncode == 0:
                return result.stdout
        except:
            pass
        return ""
    
    def update(self, force: bool = False) -> Dict[str, Any]:
        """执行更新"""
        print("=" * 50)
        print("  项目更新")
        print("=" * 50)
        
        # 检查是否有本地修改
        has_changes = self._has_local_changes()
        
        if has_changes and not force:
            print("\n⚠️  检测到本地有修改:")
            self._show_local_changes()
            print("\n选择:")
            print("  1. 暂存本地修改并更新 (git stash)")
            print("  2. 放弃本地修改并更新 (git checkout)")
            print("  3. 取消更新")
            
            choice = input("\n请选择 (1/2/3): ").strip()
            
            if choice == "1":
                subprocess.run(["git", "stash"], cwd=self.project_dir)
                print("✅ 本地修改已暂存")
            elif choice == "2":
                subprocess.run(["git", "checkout", "."], cwd=self_dir)
                print("✅ 本地修改已放弃")
            else:
                print("❌ 更新已取消")
                return {"success": False, "reason": "用户取消"}
        
        # 执行更新
        print("\n📥 正在拉取最新代码...")
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            capture_output=True,
            text=True,
            cwd=self.project_dir
        )
        
        if result.returncode == 0:
            print("✅ 更新成功!")
            print(f"\n{result.stdout}")
            
            # 更新依赖
            print("\n📦 更新依赖...")
            self._update_dependencies()
            
            # 如果之前有暂存的修改，尝试恢复
            if has_changes:
                print("\n🔄 恢复本地修改...")
                stash_result = subprocess.run(
                    ["git", "stash", "pop"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_dir
                )
                if stash_result.returncode != 0:
                    print("⚠️  恢复本地修改时有冲突，请手动解决")
            
            return {
                "success": True,
                "current_version": self.get_current_version(),
                "output": result.stdout
            }
        else:
            print(f"❌ 更新失败: {result.stderr}")
            return {"success": False, "reason": result.stderr}
    
    def _has_local_changes(self) -> bool:
        """检查是否有本地修改"""
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=self.project_dir
        )
        return bool(result.stdout.strip())
    
    def _show_local_changes(self):
        """显示本地修改"""
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True,
            cwd=self.project_dir
        )
        print(result.stdout)
    
    def _update_dependencies(self):
        """更新依赖"""
        requirements = os.path.join(self.project_dir, "requirements.txt")
        if os.path.exists(requirements):
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", requirements, "-q"],
                capture_output=True
            )
            print("✅ 依赖更新完成")

class UpdateServer:
    """更新服务器 - 用于分发更新"""
    
    def __init__(self, repo_url: str):
        self.repo_url = repo_url
    
    def generate_update_script(self, output_path: str = "update.bat"):
        """生成更新脚本"""
        script_content = f"""@echo off
chcp 65001 >nul
echo ========================================
echo   取证AI平台 - 自动更新
echo ========================================
echo.

:: 检查Git
where git >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] 未找到Git，请先安装Git
    echo 下载: https://git-scm.com/downloads
    pause
    exit /b 1
)

:: 检查是否是Git仓库
if not exist ".git" (
    echo [提示] 首次使用，请先克隆仓库
    echo git clone {self.repo_url}
    pause
    exit /b 1
)

:: 拉取更新
echo [1/3] 检查更新...
git fetch origin

:: 检查是否有更新
for /f "tokens=*" %%i in ('git rev-parse HEAD') do set LOCAL=%%i
for /f "tokens=*" %%i in ('git rev-parse origin/main') do set REMOTE=%%i

if "%LOCAL%"=="%REMOTE%" (
    echo.
    echo ✅ 已是最新版本!
    pause
    exit /b 0
)

:: 显示更新内容
echo.
echo [2/3] 更新内容:
git log HEAD..origin/main --oneline
echo.

:: 确认更新
set /p confirm=是否更新? (y/n): 
if /i not "%confirm%"=="y" (
    echo 已取消
    pause
    exit /b 0
)

:: 执行更新
echo.
echo [3/3] 正在更新...
git pull origin main

if %errorLevel% equ 0 (
    echo.
    echo ✅ 更新完成!
    echo.
    
    :: 更新依赖
    if exist "requirements.txt" (
        echo 更新依赖...
        pip install -r requirements.txt -q
        echo 依赖更新完成
    )
) else (
    echo.
    echo ❌ 更新失败，请手动处理
)

pause
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"✅ 更新脚本已生成: {output_path}")
    
    def generate_update_sh(self, output_path: str = "update.sh"):
        """生成Linux/Mac更新脚本"""
        script_content = f"""#!/bin/bash

echo "========================================"
echo "  取证AI平台 - 自动更新"
echo "========================================"
echo

# 检查Git
if ! command -v git &> /dev/null; then
    echo "[错误] 未找到Git，请先安装Git"
    exit 1
fi

# 检查是否是Git仓库
if [ ! -d ".git" ]; then
    echo "[提示] 首次使用，请先克隆仓库"
    echo "git clone {self.repo_url}"
    exit 1
fi

# 拉取更新
echo "[1/3] 检查更新..."
git fetch origin

# 检查是否有更新
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo
    echo "✅ 已是最新版本!"
    exit 0
fi

# 显示更新内容
echo
echo "[2/3] 更新内容:"
git log HEAD..origin/main --oneline
echo

# 确认更新
read -p "是否更新? (y/n): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "已取消"
    exit 0
fi

# 执行更新
echo
echo "[3/3] 正在更新..."
git pull origin main

if [ $? -eq 0 ]; then
    echo
    echo "✅ 更新完成!"
    echo
    
    # 更新依赖
    if [ -f "requirements.txt" ]; then
        echo "更新依赖..."
        pip install -r requirements.txt -q
        echo "依赖更新完成"
    fi
else
    echo
    echo "❌ 更新失败，请手动处理"
fi
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # 设置执行权限
        os.chmod(output_path, 0o755)
        
        print(f"✅ 更新脚本已生成: {output_path}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='项目更新工具')
    parser.add_argument('--check', action='store_true', help='检查更新')
    parser.add_argument('--update', action='store_true', help='执行更新')
    parser.add_argument('--force', action='store_true', help='强制更新')
    parser.add_argument('--generate-scripts', action='store_true', help='生成更新脚本')
    
    args = parser.parse_args()
    
    updater = ProjectUpdater()
    
    if args.check:
        info = updater.check_for_updates()
        print(f"当前版本: {info['current_version']}")
        print(f"远程版本: {info['remote_version']}")
        print(f"有更新: {'是' if info['update_available'] else '否'}")
        if info['changelog']:
            print(f"\n更新日志:\n{info['changelog']}")
    
    elif args.update:
        updater.update(force=args.force)
    
    elif args.generate_scripts:
        server = UpdateServer("https://github.com/luyichen0704/forensic-ai-platform.git")
        server.generate_update_script()
        server.generate_update_sh()
    
    else:
        # 默认检查更新
        info = updater.check_for_updates()
        if info['update_available']:
            print(f"🔄 发现新版本!")
            print(f"当前: {info['current_version']}")
            print(f"最新: {info['remote_version']}")
            print(f"\n更新内容:\n{info['changelog']}")
            
            choice = input("\n是否更新? (y/n): ").strip()
            if choice.lower() == 'y':
                updater.update()

if __name__ == "__main__":
    main()
