@echo off
chcp 65001 >nul
title UV Environment Setup

echo ================================================
echo    UV Environment Setup (Windows)
echo ================================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    exit /b 1
)

echo [1/4] Checking Python...
python --version

echo.
echo [2/4] Running UV setup script...
python scripts\setup_uv.py
if errorlevel 1 (
    echo [ERROR] Setup failed
    exit /b 1
)

echo.
echo ================================================
echo    Setup Complete!
echo ================================================
echo.
echo Next steps:
echo   1. Run: .\activate_venv.ps1
echo   2. Run: python src\agents\patterns\chaining.py
echo.
pause
