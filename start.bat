@echo off
chcp 65001 >nul
setlocal

:MENU
cls
echo ================================================
echo    Everything About Agent - Start Menu
echo ================================================
echo.
echo    1. Install/Update Dependencies
echo    2. Run System Verification
echo    3. Run Prompt Chaining Demo
echo    4. Run Routing Demo
echo    5. Exit
echo.
echo ================================================
set /p choice="Please select [1-5]: "

if "%choice%"=="1" goto INSTALL
if "%choice%"=="2" goto VERIFY
if "%choice%"=="3" goto CHAINING
if "%choice%"=="4" goto ROUTING
if "%choice%"=="5" goto EXIT

echo Invalid choice, please try again.
pause
goto MENU

:INSTALL
echo.
echo Installing dependencies...
pip install -e .
echo.
echo Done!
pause
goto MENU

:VERIFY
echo.
echo Running system verification...
python tests/test_system.py
echo.
pause
goto MENU

:CHAINING
echo.
echo Running Prompt Chaining demo...
python src/agents/patterns/chaining.py
echo.
pause
goto MENU

:ROUTING
echo.
echo Running Routing demo...
python src/agents/patterns/routing.py
echo.
pause
goto MENU

:EXIT
echo.
echo Goodbye! Happy Coding!
exit /b 0
