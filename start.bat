@echo off
chcp 65001 >nul 2>nul
title Forensic AI Platform
cd /d "%~dp0"

echo ========================================
echo   Forensic AI Platform
echo ========================================
echo.

python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+
    pause
    exit /b 1
)

if not exist "config\llm_config.json" (
    echo [INFO] Creating default config...
    if exist "config\llm_config.example.json" (
        copy "config\llm_config.example.json" "config\llm_config.json" >nul
        echo Config created: config\llm_config.json
        echo Please edit this file to add your API key.
        echo.
    )
)

echo Starting Web UI...
echo URL: http://localhost:7860
echo Press Ctrl+C to stop
echo.
python -m web.app

pause