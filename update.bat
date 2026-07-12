@echo off
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
    echo [错误] 当前目录不是Git仓库
    echo 请先克隆仓库: git clone https://github.com/luyichen0704/forensic-ai-platform.git
    pause
    exit /b 1
)

:: 拉取更新
echo [1/4] 检查远程更新...
git fetch origin

:: 获取本地和远程版本
for /f "tokens=*" %%i in ('git rev-parse HEAD 2^>nul') do set LOCAL=%%i
for /f "tokens=*" %%i in ('git rev-parse origin/main 2^>nul') do set REMOTE=%%i

if "%LOCAL%"=="%REMOTE%" (
    echo.
    echo ✅ 已是最新版本!
    echo.
    pause
    exit /b 0
)

:: 显示当前版本
echo.
echo 当前版本:
type VERSION 2>nul || echo "未知"
echo.

:: 显示更新内容
echo [2/4] 更新内容:
echo ----------------------------------------
git log HEAD..origin/main --oneline
echo ----------------------------------------
echo.

:: 确认更新
set /p confirm=是否更新? (y/n): 
if /i not "%confirm%"=="y" (
    echo 已取消更新
    pause
    exit /b 0
)

:: 检查本地修改
echo.
echo [3/4] 检查本地修改...
git status --short

set /p stash=是否有本地修改需要保留? (y/n): 
if /i "%stash%"=="y" (
    echo 暂存本地修改...
    git stash
    set NEED_POP=1
)

:: 执行更新
echo.
echo [4/4] 正在更新...
git pull origin main

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo   ✅ 更新成功!
    echo ========================================
    echo.
    
    :: 显示新版本
    echo 新版本:
    type VERSION 2>nul
    echo.
    
    :: 更新依赖
    if exist "requirements.txt" (
        echo 更新Python依赖...
        pip install -r requirements.txt -q 2>nul
        if %errorLevel% equ 0 (
            echo ✅ 依赖更新完成
        ) else (
            echo ⚠️  依赖更新可能需要管理员权限
        )
    )
    
    :: 恢复本地修改
    if "%NEED_POP%"=="1" (
        echo.
        echo 恢复本地修改...
        git stash pop
        if %errorLevel% neq 0 (
            echo ⚠️  恢复本地修改时有冲突，请手动解决
        )
    )
    
    echo.
    echo ========================================
    echo   更新完成! 可以开始使用了
    echo ========================================
) else (
    echo.
    echo ❌ 更新失败
    echo 可能原因:
    echo   1. 网络连接问题
    echo   2. 本地有冲突未解决
    echo.
    echo 手动更新命令: git pull origin main
)

echo.
pause
