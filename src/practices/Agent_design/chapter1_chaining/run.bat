@echo off
setlocal
echo Starting Chapter 1: Prompt Chaining Practice...
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not found in PATH. Please install Python 3.8+.
    pause
    exit /b 1
)

:: Navigate to script directory
cd /d "%~dp0"

:: Run the script
python chapter1_chaining_practice.py

echo.
echo Execution finished.
pause
