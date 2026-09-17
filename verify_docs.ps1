# ShopSense - Milestone 4 API Documentation Verification Script

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  ShopSense - Milestone 4 API Documentation Verification" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Validate Python and OpenAPI schema import
Write-Host "`n[1/3] Validating FastAPI OpenAPI schema generation..." -ForegroundColor Yellow
try {
    $pyCode = @'
from main import app
s = app.openapi()
title = s.get("info", {}).get("title", "ShopSense API")
paths = len(s.get("paths", {}))
schemas = len(s.get("components", {}).get("schemas", {}))
print(f"OK: {title} with {paths} paths and {schemas} schemas.")
'@
    $valOutput = python -c $pyCode 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "      $valOutput" -ForegroundColor Green
    } else {
        Write-Error "[ERROR] Failed to generate OpenAPI schema:`n$valOutput"
        exit 1
    }
} catch {
    Write-Error "[ERROR] Python execution failed: $_"
    exit 1
}

# 2. Check if server is running on port 8000
Write-Host "`n[2/3] Probing running server (http://localhost:8000/docs)..." -ForegroundColor Yellow
try {
    $res = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 3
    if ($res.StatusCode -eq 200) {
        Write-Host "      Server is RUNNING and /docs is accessible (HTTP 200 OK)!" -ForegroundColor Green
        Write-Host "      Response payload: $($res.Content.Length) bytes received" -ForegroundColor Green
    }
} catch {
    Write-Host "      Server is not currently running on port 8000." -ForegroundColor Yellow
    Write-Host "      Launch server with: uvicorn main:app --host 127.0.0.1 --port 8000 --reload" -ForegroundColor Gray
}

# 3. Summary
Write-Host "`n[3/3] Verification Summary:" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Interactive Swagger UI: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "  ReDoc Alternative UI:   http://localhost:8000/redoc" -ForegroundColor Green
Write-Host "  OpenAPI JSON Spec:      http://localhost:8000/openapi.json" -ForegroundColor Green
Write-Host "========================================================`n" -ForegroundColor Cyan
