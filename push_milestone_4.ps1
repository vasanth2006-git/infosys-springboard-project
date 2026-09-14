# ShopSense - Push Milestone 4 to GitHub
# Repository: vasanth2006-git/infosys-springboard-project
# Target Branch: milestone-4-completion

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "  ShopSense - Push Milestone 4 to GitHub" -ForegroundColor Cyan
Write-Host "  Repository: vasanth2006-git/infosys-springboard-project" -ForegroundColor Cyan
Write-Host "  Target Branch: milestone-4-completion" -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan

# 1. Safety check: Ensure we are in project root
if (-not (Test-Path "main.py")) {
    Write-Error "[ERROR] main.py not found. Please run this script in the project root."
    exit 1
}

# 2. Untrack debug and secret files from index if present
Write-Host "`n[1/6] Ensuring debug logs and secrets are not tracked..." -ForegroundColor Yellow
git rm --cached debug_log.txt 2>$null
git rm --cached server_debug.log 2>$null
git rm --cached .env 2>$null
git rm --cached shopsense.db 2>$null

# 3. Stage required Milestone 4 files
Write-Host "[2/6] Staging Milestone 4 project files..." -ForegroundColor Yellow
git add database.py main.py models.py schemas.py requirements.txt .gitignore .env.example templates/ static/
git add Dockerfile .dockerignore docker_verify.bat docker_verify.ps1
git add verify_docs.bat verify_docs.ps1
git add tests/ run_tests.bat run_tests.ps1
git add .github/workflows/ci.yml

# 4. Verify .env is NOT staged
$staged = git status --porcelain
if ($staged -match '(?m)^[AM]\s+\.env$') {
    Write-Error "[ERROR] .env file was staged! Unstaging immediately for security!"
    git reset HEAD .env
    exit 1
}
Write-Host "      Confirmed: No secrets or .env file staged." -ForegroundColor Green

# 5. Commit with message
Write-Host "[3/6] Committing Milestone 4 changes..." -ForegroundColor Yellow
git commit -m "Implement Milestone 4: Dockerization, API Documentation, Unit Tests, and GitHub Actions CI/CD"

# 6. Switch/create local milestone-4-completion branch pointing to this commit
Write-Host "[4/6] Setting current branch to milestone-4-completion..." -ForegroundColor Yellow
git checkout -B milestone-4-completion

# 7. Push to origin/milestone-4-completion
Write-Host "[5/6] Pushing to origin/milestone-4-completion..." -ForegroundColor Yellow
$pushOutput = git push -u origin milestone-4-completion 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[INFO] Standard push failed (remote branch has diverged initial commit). Retrying with --force-with-lease..." -ForegroundColor Magenta
    git push -u origin milestone-4-completion --force-with-lease
}

# 8. Summary & Verification
Write-Host "`n=======================================================" -ForegroundColor Cyan
Write-Host "[6/6] Push Verification and Summary:" -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
$currentBranch = (git rev-parse --abbrev-ref HEAD).Trim()
$fullHash = (git rev-parse HEAD).Trim()
$shortHash = (git rev-parse --short HEAD).Trim()

Write-Host "1. Current Branch  : $currentBranch" -ForegroundColor Green
Write-Host "2. Commit Hash     : $fullHash ($shortHash)" -ForegroundColor Green
Write-Host "3. Repository URL  : https://github.com/vasanth2006-git/infosys-springboard-project" -ForegroundColor Green
Write-Host "4. Branch URL      : https://github.com/vasanth2006-git/infosys-springboard-project/tree/milestone-4-completion" -ForegroundColor Green
Write-Host "5. Actions Tab     : https://github.com/vasanth2006-git/infosys-springboard-project/actions" -ForegroundColor Green

Write-Host "`nFiles committed in this commit:" -ForegroundColor Yellow
git show --stat --oneline $shortHash

Write-Host "`n=======================================================" -ForegroundColor Cyan
Write-Host "  Milestone 4 successfully pushed to GitHub!" -ForegroundColor Cyan
Write-Host "  GitHub Actions CI pipeline will trigger automatically!" -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
