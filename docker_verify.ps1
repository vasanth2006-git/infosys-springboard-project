# ShopSense - Milestone 4 Dockerization Verification Script

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  ShopSense - Milestone 4 Dockerization Verification" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Check Docker availability
Write-Host "`n[1/5] Checking Docker availability..." -ForegroundColor Yellow
try {
    $null = docker --version
} catch {
    Write-Error "[ERROR] Docker command not found. Ensure Docker Desktop is installed and in PATH."
    exit 1
}

$dockerInfo = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "[ERROR] Docker daemon is not running. Please launch Docker Desktop."
    exit 1
}
Write-Host "      Docker daemon is active." -ForegroundColor Green

# 2. Clean up previous container
Write-Host "`n[2/5] Cleaning up existing containers if present..." -ForegroundColor Yellow
docker rm -f shopsense-test 2>$null | Out-Null

# 3. Build image
Write-Host "`n[3/5] Building Docker image (shopsense-app:latest)..." -ForegroundColor Yellow
docker build -t shopsense-app:latest .
if ($LASTEXITCODE -ne 0) {
    Write-Error "[ERROR] Docker build failed!"
    exit 1
}
Write-Host "      Docker image built successfully!" -ForegroundColor Green

# 4. Run container
Write-Host "`n[4/5] Starting container on port 8000..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "      Using .env file with host.docker.internal database route..." -ForegroundColor Gray
    docker run -d --name shopsense-test -p 8000:8000 --env-file .env -e MYSQL_HOST=host.docker.internal shopsense-app:latest
} else {
    docker run -d --name shopsense-test -p 8000:8000 shopsense-app:latest
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "[ERROR] Failed to start container!"
    exit 1
}

Write-Host "      Waiting 4 seconds for container to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 4

# 5. Health check & Reachability
Write-Host "`n[5/5] Checking container status and HTTP reachability..." -ForegroundColor Yellow
docker ps --filter "name=shopsense-test" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

Write-Host "`nContainer Logs:" -ForegroundColor Cyan
Write-Host "--------------------------------------------------------" -ForegroundColor Gray
docker logs --tail 20 shopsense-test
Write-Host "--------------------------------------------------------" -ForegroundColor Gray

Write-Host "`nProbing HTTP endpoint (http://localhost:8000/login)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/login" -UseBasicParsing -TimeoutSec 5
    Write-Host "HTTP Response Status: $($response.StatusCode) OK" -ForegroundColor Green
    Write-Host "Page Title / Length: $($response.Content.Length) bytes received" -ForegroundColor Green
} catch {
    Write-Host "HTTP Probe: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host "  Dockerization Verification Complete!" -ForegroundColor Cyan
Write-Host "  Application URL: http://localhost:8000/login" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "`nTo stop and remove the test container when done, run:" -ForegroundColor Yellow
Write-Host "  docker rm -f shopsense-test`n" -ForegroundColor White
