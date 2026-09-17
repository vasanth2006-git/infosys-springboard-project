@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo   ShopSense - Milestone 4 API Documentation Verification
echo ========================================================
echo.

:: 1. Check if python and uvicorn are available
echo [1/4] Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH.
    pause
    exit /b 1
)

:: 2. Check OpenAPI syntax by loading app instance in Python
echo.
echo [2/4] Validating FastAPI OpenAPI schema generation...
python -c "from main import app; openapi = app.openapi(); print(f'Successfully loaded OpenAPI schema! Title: {openapi[\"info\"][\"title\"]}, Total Paths: {len(openapi[\"paths\"])}')"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to load OpenAPI schema! Please check error output above.
    pause
    exit /b 1
)
echo       OpenAPI schema validated successfully!

:: 3. Check if server is running or start a temporary check
echo.
echo [3/4] Probing running server (http://localhost:8000/docs)...
curl -s -o nul -w "%%{http_code}" http://localhost:8000/docs > temp_status.txt 2>nul
set /p STATUS=<temp_status.txt 2>nul
del temp_status.txt 2>nul

if "%STATUS%"=="200" (
    echo       Server is RUNNING and /docs is accessible (HTTP 200 OK)!
) else (
    echo       Server is not running on port 8000.
    echo       To start the server, run:
    echo         uvicorn main:app --host 127.0.0.1 --port 8000 --reload
)

:: 4. Summary & Links
echo.
echo [4/4] Verification Summary:
echo ========================================================
echo   Interactive Swagger UI: http://localhost:8000/docs
echo   ReDoc Alternative UI:   http://localhost:8000/redoc
echo   OpenAPI JSON Spec:      http://localhost:8000/openapi.json
echo ========================================================
echo.
pause
