@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo    ShopSense - Weekly AI Agent Workflow Runner
echo ========================================================
echo.

set "PY_EXE="

if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    goto :python_found
)

if exist "C:\Users\vasanthkumar\AppData\Local\Programs\Python\Python313\python.exe" (
    set "PY_EXE=C:\Users\vasanthkumar\AppData\Local\Programs\Python\Python313\python.exe"
    goto :python_found
)

if exist ".venv\Scripts\python.exe" (
    set "PY_EXE=.venv\Scripts\python.exe"
    goto :python_found
)

if exist "venv\Scripts\python.exe" (
    set "PY_EXE=venv\Scripts\python.exe"
    goto :python_found
)

python --version >nul 2>&1
if !errorlevel! equ 0 (
    set "PY_EXE=python"
    goto :python_found
)

echo [ERROR] Python 3.11+ executable not found!
pause
exit /b 1

:python_found
echo Using Python: "!PY_EXE!"
echo Running Weekly AI Agent Workflow against MySQL...
echo.

"!PY_EXE!" run_weekly_agent.py %*

set EXIT_CODE=!errorlevel!
echo.
pause
exit /b !EXIT_CODE!
