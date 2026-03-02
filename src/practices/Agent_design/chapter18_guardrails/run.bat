@echo off
setlocal EnableDelayedExpansion
echo ==================================================
echo    Chapter 18: Guardrails (安全护栏) - Practice
echo ==================================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not found in PATH.
    echo Please install Python 3.10+ and ensure it's in PATH.
    pause
    exit /b 1
)

:: Check for Ollama (optional but recommended)
echo Checking Ollama service...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo Warning: Ollama service not detected at localhost:11434
    echo Please ensure Ollama is running: ollama serve
    echo.
    choice /C YN /M "Continue anyway"
    if !errorlevel! equ 2 exit /b 1
)

:: Navigate to script directory
cd /d "%~dp0"

:: Set Python path for imports
set PYTHONPATH=%~dp0\..\..\..\..

:: Run the practice script
echo.
echo Starting practice...
echo --------------------------------------------------
python chapter18_guardrails_practice.py

if %errorlevel% neq 0 (
    echo.
    echo Error: Script execution failed.
    pause
    exit /b 1
)

echo.
echo --------------------------------------------------
echo Practice completed successfully!
echo.
pause

