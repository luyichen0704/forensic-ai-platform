@echo off
chcp 65001 >nul 2>nul
title Forensic AI Platform - Installer
cd /d "%~dp0"

echo ========================================
echo   Forensic AI Platform - Installer
echo ========================================
echo.
echo Starting installer...
echo.

python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python not found!
    echo.
    echo Please install Python 3.8+ from:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

if not exist "installer_gui.py" (
    echo [ERROR] installer_gui.py not found!
    echo Please run this script in the correct directory.
    pause
    exit /b 1
)

python installer_gui.py

if %errorLevel% neq 0 (
    echo.
    echo [ERROR] Installer exited with error code: %errorLevel%
    pause
)