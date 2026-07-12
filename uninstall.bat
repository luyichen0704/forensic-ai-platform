@echo off
chcp 65001 >nul 2>nul
title Forensic AI Platform - Uninstaller
cd /d "%~dp0"

echo ========================================
echo   Forensic AI Platform - Uninstaller
echo ========================================
echo.
echo Starting uninstaller...
echo.

python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please delete the folder manually.
    pause
    exit /b 1
)

python uninstaller_gui.py

if %errorLevel% neq 0 (
    echo.
    echo [ERROR] Uninstaller exited with error
    pause
)