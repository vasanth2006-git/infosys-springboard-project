@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo   ShopSense - Milestone 4 Dockerization Verification
echo ========================================================
echo.

:: 1. Check if Docker is installed and running
echo [1/5] Checking Docker availability...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker command not found. Please ensure Docker Desktop is installed and in your PATH.
    pause
    exit /b 1
)

docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker daemon is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)
echo       Docker daemon is active.

:: 2. Clean up any previous test container
echo.
echo [2/5] Cleaning up existing containers if present...
docker rm -f shopsense-test >nul 2>&1

:: 3. Build Docker image
echo.
echo [3/5] Building Docker image (shopsense-app:latest)...
docker build -t shopsense-app:latest .
if %errorlevel% neq 0 (
    echo [ERROR] Docker build failed!
    pause
    exit /b 1
)
echo       Docker image built successfully!

:: 4. Start Docker container
echo.
echo [4/5] Starting container on port 8000...
if exist ".env" (
    echo       Using .env file with host.docker.internal database route...
    docker run -d --name shopsense-test -p 8000:8000 --env-file .env -e MYSQL_HOST=host.docker.internal shopsense-app:latest
) else (
    docker run -d --name shopsense-test -p 8000:8000 shopsense-app:latest
)

if %errorlevel% neq 0 (
    echo [ERROR] Failed to start container!
    pause
    exit /b 1
)

:: Wait for application to initialize inside container
echo       Waiting 4 seconds for container to initialize...
timeout /t 4 /nobreak >nul

:: 5. Verification & Health Check
echo.
echo [5/5] Checking container status and HTTP reachability...
docker ps --filter "name=shopsense-test" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo Container Logs:
echo --------------------------------------------------------
docker logs --tail 20 shopsense-test
echo --------------------------------------------------------

echo.
echo Probing HTTP endpoint (http://localhost:8000/login)...
curl -s -o nul -w "HTTP Response Code: %%{http_code}\n" http://localhost:8000/login
if %errorlevel% neq 0 (
    powershell -Command "try { $res = Invoke-WebRequest -Uri 'http://localhost:8000/login' -UseBasicParsing; Write-Host ('HTTP Status: ' + $res.StatusCode) -ForegroundColor Green } catch { Write-Host ('HTTP Probe Error: ' + $_.Exception.Message) -ForegroundColor Red }"
)

echo.
echo ========================================================
echo   Dockerization Verification Complete!
echo   Application URL: http://localhost:8000/login
echo ========================================================
echo.
echo To stop and remove the test container when done, run:
echo   docker rm -f shopsense-test
echo.
pause
