@echo off
chcp 65001 >nul
echo ========================================
echo   取证AI平台 - 安装程序
echo ========================================
echo.
echo 正在启动安装向导...
echo.

:: 检查Python
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] 未找到Python
    echo 请先安装Python 3.8+: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: 启动安装向导
start pythonw installer_gui.py