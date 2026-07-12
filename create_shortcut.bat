@echo off
chcp 65001 >nul 2>nul
title Create Desktop Shortcut
cd /d "%~dp0"

echo ========================================
echo   Create Desktop Shortcut
echo ========================================
echo.

powershell -ExecutionPolicy Bypass -File "create_shortcut.ps1"

echo.
pause