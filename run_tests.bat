@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo   ShopSense - Milestone 4 Unit Test Runner
echo ========================================================
echo.

:: 1. Locate Python Executable
echo [1/3] Detecting Python environment...
set "PY_EXE="

if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    goto :python_found
)

if exist "C:\Users\vasanthkumar\AppData\Local\Programs\Python\Python313\python.exe" (
    set "PY_EXE=C:\Users\vasanthkumar\AppData\Local\Programs\Python\Python313\python.exe"
    goto :python_found
)

python --version >nul 2>&1
if !errorlevel! equ 0 (
    set "PY_EXE=python"
    goto :python_found
)

if exist "%LOCALAPPDATA%\Programs\Python\Launcher\py.exe" (
    set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Launcher\py.exe"
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

if exist "C:\Program Files\Python313\python.exe" (
    set "PY_EXE=C:\Program Files\Python313\python.exe"
    goto :python_found
)

echo [ERROR] Python executable not found in PATH or standard installation paths!
pause
exit /b 1

:python_found
echo       Using Python: "!PY_EXE!"
"!PY_EXE!" --version

:: 2. Check and Install pytest and httpx if needed
echo.
echo [2/3] Checking pytest and testing dependencies...
"!PY_EXE!" -c "import pytest, httpx" >nul 2>&1
if !errorlevel! neq 0 (
    echo [INFO] Installing pytest and httpx...
    "!PY_EXE!" -m pip install pytest httpx
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install pytest.
        pause
        exit /b 1
    )
) else (
    echo       Dependencies satisfied.
)

:: 3. Run Test Suite
echo.
echo [3/3] Running ShopSense automated unit test suite...
echo ========================================================
"!PY_EXE!" -m pytest tests -v
set TEST_EXIT_CODE=!errorlevel!
echo ========================================================

if !TEST_EXIT_CODE! equ 0 (
    echo.
    echo [SUCCESS] ALL UNIT TESTS PASSED!
) else (
    echo.
    echo [FAILURE] Unit tests completed with failures (Exit Code: !TEST_EXIT_CODE!).
)

echo.
pause
exit /b !TEST_EXIT_CODE!
