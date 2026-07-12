#!/bin/bash

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
    echo "[错误] 当前目录不是Git仓库"
    echo "请先克隆仓库: git clone https://github.com/luyichen0704/forensic-ai-platform.git"
    exit 1
fi

# 拉取更新
echo "[1/4] 检查远程更新..."
git fetch origin

# 获取本地和远程版本
LOCAL=$(git rev-parse HEAD 2>/dev/null)
REMOTE=$(git rev-parse origin/main 2>/dev/null)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo
    echo "✅ 已是最新版本!"
    echo
    exit 0
fi

# 显示当前版本
echo
echo "当前版本:"
cat VERSION 2>/dev/null || echo "未知"
echo

# 显示更新内容
echo "[2/4] 更新内容:"
echo "----------------------------------------"
git log HEAD..origin/main --oneline
echo "----------------------------------------"
echo

# 确认更新
read -p "是否更新? (y/n): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "已取消更新"
    exit 0
fi

# 检查本地修改
echo
echo "[3/4] 检查本地修改..."
git status --short

read -p "是否有本地修改需要保留? (y/n): " stash
if [ "$stash" = "y" ] || [ "$stash" = "Y" ]; then
    echo "暂存本地修改..."
    git stash
    NEED_POP=1
fi

# 执行更新
echo
echo "[4/4] 正在更新..."
git pull origin main

if [ $? -eq 0 ]; then
    echo
    echo "========================================"
    echo "  ✅ 更新成功!"
    echo "========================================"
    echo
    
    # 显示新版本
    echo "新版本:"
    cat VERSION 2>/dev/null
    echo
    
    # 更新依赖
    if [ -f "requirements.txt" ]; then
        echo "更新Python依赖..."
        pip install -r requirements.txt -q 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✅ 依赖更新完成"
        else
            echo "⚠️  依赖更新失败，请手动执行: pip install -r requirements.txt"
        fi
    fi
    
    # 恢复本地修改
    if [ "$NEED_POP" = "1" ]; then
        echo
        echo "恢复本地修改..."
        git stash pop
        if [ $? -ne 0 ]; then
            echo "⚠️  恢复本地修改时有冲突，请手动解决"
        fi
    fi
    
    echo
    echo "========================================"
    echo "  更新完成! 可以开始使用了"
    echo "========================================"
else
    echo
    echo "❌ 更新失败"
    echo "可能原因:"
    echo "  1. 网络连接问题"
    echo "  2. 本地有冲突未解决"
    echo
    echo "手动更新命令: git pull origin main"
fi
