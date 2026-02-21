@echo off
chcp 65001 >nul
setlocal

:: ================================================
:: Everything About Agent - Enhanced Start Script
:: Windows Version with Error Handling & Logging
:: ================================================

set "SCRIPT_DIR=%~dp0"
set "LOG_DIR=%SCRIPT_DIR%logs"
set "PID_DIR=%SCRIPT_DIR%.pids"
set "WEB_DIR=%SCRIPT_DIR%docs\web"

:: Create directories
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "%PID_DIR%" mkdir "%PID_DIR%"

:: Log file with timestamp
set "TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"
set "LOG_FILE=%LOG_DIR%\startup_%TIMESTAMP%.log"

:: Start logging
call :LOG "================================================"
call :LOG "Everything About Agent - Start Menu (Windows)"
call :LOG "================================================"

::MENU
:MAIN_MENU
cls
echo ================================================
echo    Everything About Agent - Start Menu
echo ================================================
echo.
echo    1. Install/Update Dependencies
echo    2. Run System Verification
echo    3. Run Prompt Chaining Demo
echo    4. Run Routing Demo
echo    5. Start Web Frontend (Course Pages)
echo    6. Start Web with File Watcher
echo    7. Start MkDocs Documentation Server
echo    8. Stop All Services
echo    9. Check Service Status
echo   10. Run Diagnostics
echo   11. View Logs
echo   12. Exit
echo.
echo ================================================
set /p choice="Please select [1-12]: "

if "%choice%"=="1" goto INSTALL
if "%choice%"=="2" goto VERIFY
if "%choice%"=="3" goto CHAINING
if "%choice%"=="4" goto ROUTING
if "%choice%"=="5" goto WEB
if "%choice%"=="6" goto WEB_WATCH
if "%choice%"=="7" goto MKDOCS
if "%choice%"=="8" goto STOP_ALL
if "%choice%"=="9" goto STATUS
if "%choice%"=="10" goto DIAGNOSE
if "%choice%"=="11" goto VIEW_LOGS
if "%choice%"=="12" goto EXIT

echo Invalid choice, please try again.
pause
goto MAIN_MENU

:: ============================================================
:: INSTALL
:: ============================================================
:INSTALL
echo.
echo [INFO] Installing dependencies...
pip install -e . >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    echo Check log: %LOG_FILE%
) else (
    echo [OK] Dependencies installed
)
pause
goto MAIN_MENU

:: ============================================================
:: VERIFY
:: ============================================================
:VERIFY
echo.
echo [INFO] Running system verification...
python tests/test_system.py >> "%LOG_FILE%" 2>&1
echo [OK] Done
pause
goto MAIN_MENU

:: ============================================================
:: CHAINING
:: ============================================================
:CHAINING
echo.
echo [INFO] Running Prompt Chaining demo...
python src/agents/patterns/chaining.py >> "%LOG_FILE%" 2>&1
pause
goto MAIN_MENU

:: ============================================================
:: ROUTING
:: ============================================================
:ROUTING
echo.
echo [INFO] Running Routing demo...
python src/agents/patterns/routing.py >> "%LOG_FILE%" 2>&1
pause
goto MAIN_MENU

:: ============================================================
:: WEB - Start Web Frontend
:: ============================================================
:WEB
echo.
echo [INFO] Finding available port...

:: Use Python to find an available port
for /f "delims=" %%p in ('python -c "import socket; s=socket.socket(); s.bind(('',0)); print(s.getsockname()[1]); s.close()"') do set PORT=%%p

echo.
echo ================================================
echo    Everything About Agent - Web Server
echo ================================================
echo.
echo   ACCESS URL:  http://localhost:%PORT%
echo.
echo ================================================
echo.

cd /d "%WEB_DIR%"
start "Web Server - http://localhost:%PORT%" cmd /k "python -m http.server %PORT%"

timeout /t 2 >nul

:: Save PID
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%" ^| findstr LISTENING') do (
    echo %%a > "%PID_DIR%\web_server.pid"
)

:: Open browser
start http://localhost:%PORT%

echo [OK] Server started on port %PORT%
pause
goto MAIN_MENU

:: ============================================================
:: WEB_WATCH - Start Web with File Watcher
:: ============================================================
:WEB_WATCH
echo.
echo [INFO] Finding available port...

:: Use Python to find an available port
for /f "delims=" %%p in ('python -c "import socket; s=socket.socket(); s.bind(('',0)); print(s.getsockname()[1]); s.close()"') do set PORT=%%p

echo.
echo ================================================
echo    Everything About Agent - Web Server (File Watcher)
echo ================================================
echo.
echo   ACCESS URL:  http://localhost:%PORT%
echo.
echo   Features: Auto-reload on file changes
echo.
echo ================================================
echo.

:: Check watchdog
python -c "import watchdog" 2>nul
if errorlevel 1 (
    echo [INFO] Installing watchdog...
    pip install watchdog >> "%LOG_FILE%" 2>&1
)

cd /d "%SCRIPT_DIR%"
python scripts/file_watcher.py --port %PORT% --dir "%WEB_DIR%"

pause
goto MAIN_MENU

:: ============================================================
:: MKDOCS - Start MkDocs Documentation Server
:: ============================================================
:MKDOCS
echo.
echo [INFO] Finding available port...

:: Use Python to find an available port
for /f "delims=" %%p in ('python -c "import socket; s=socket.socket(); s.bind(('',0)); print(s.getsockname()[1]); s.close()"') do set PORT=%%p

echo.
echo ================================================
echo    Everything About Agent - MkDocs Docs
echo ================================================
echo.
echo   ACCESS URL:  http://localhost:%PORT%
echo.
echo   Features: Material theme, 20 design patterns
echo.
echo ================================================
echo.

:: Check mkdocs
python -c "import mkdocs" 2>nul
if errorlevel 1 (
    echo [INFO] Installing mkdocs...
    pip install mkdocs mkdocs-material >> "%LOG_FILE%" 2>&1
)

cd /d "%SCRIPT_DIR%"
start "MkDocs Server" cmd /k "chcp 65001 >nul && python -m mkdocs serve --dev-addr 0.0.0.0:%PORT%"

timeout /t 2 >nul

:: Save PID
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%" ^| findstr LISTENING') do (
    echo %%a > "%PID_DIR%\mkdocs_server.pid"
)

:: Open browser
start http://localhost:%PORT%

echo [OK] MkDocs server started on port %PORT%
pause
goto MAIN_MENU

:: ============================================================
:: STOP_ALL - Stop All Services
:: ============================================================
:STOP_ALL
echo.
echo [INFO] Stopping all services...

:: Kill by PID file
if exist "%PID_DIR%\web_server.pid" (
    set /p WPID=<"%PID_DIR%\web_server.pid"
    taskkill /PID !WPID! /F >nul 2>&1
    del "%PID_DIR%\web_server.pid"
)

:: Kill MkDocs by PID file
if exist "%PID_DIR%\mkdocs_server.pid" (
    set /p MPID=<"%PID_DIR%\mkdocs_server.pid"
    taskkill /PID !MPID! /F >nul 2>&1
    del "%PID_DIR%\mkdocs_server.pid"
)

:: Kill any on random ports
for /f "tokens=5" %%a in ('netstat -ano ^| findstr "10000-65535" ^| findstr LISTENING 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo [OK] Services stopped
pause
goto MAIN_MENU

:: ============================================================
:: STATUS
:: ============================================================
:STATUS
echo.
echo ================================================
echo    Service Status
echo ================================================
echo.

:: Check Python processes
echo [Python Processes]
tasklist | findstr /I "python.exe" >nul
if errorlevel 1 (
    echo   None running
) else (
    tasklist | findstr /I "python.exe"
)
echo.

:: Check PID file
if exist "%PID_DIR%\web_server.pid" (
    set /p WPID=<"%PID_DIR%\web_server.pid"
    echo [Web Server] PID: !WPID!
) else (
    echo [Web Server] Not running
)
echo.

pause
goto MAIN_MENU

:: ============================================================
:: DIAGNOSE
:: ============================================================
:DIAGNOSE
echo.
echo [INFO] Running diagnostics...
python scripts/diagnose.py
pause
goto MAIN_MENU

:: ============================================================
:: VIEW_LOGS
:: ============================================================
:VIEW_LOGS
echo.
echo [Logs]
if exist "%LOG_DIR%" (
    dir /B /O-D "%LOG_DIR%\*.log" 2>nul | findstr /N "^" | findstr "^[1-5]:"
) else (
    echo   No logs
)
echo.
pause
goto MAIN_MENU

:: ============================================================
:: EXIT
:: ============================================================
:EXIT
echo.
echo Goodbye!
exit /b 0

:: ============================================================
:: Helper Functions
:: ============================================================

:LOG
echo [%date% %time%] %~1 >> "%LOG_FILE%"
goto :eof
