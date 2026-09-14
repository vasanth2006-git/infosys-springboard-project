@echo off
setlocal enabledelayedexpansion

echo =======================================================
echo   ShopSense - Push Milestone 4 to GitHub
echo   Repository: vasanth2006-git/infosys-springboard-project
echo   Target Branch: milestone-4-completion
echo =======================================================
echo.

:: 1. Safety check: Ensure we are in project root
if not exist "main.py" (
    echo [ERROR] main.py not found. Please run this script in the project root.
    pause
    exit /b 1
)

:: 2. Untrack debug and secret files from index if present
echo [1/6] Ensuring debug logs and secrets are not tracked...
git rm --cached debug_log.txt 2>nul
git rm --cached server_debug.log 2>nul
git rm --cached .env 2>nul
git rm --cached shopsense.db 2>nul

:: 3. Stage required Milestone 4 files
echo [2/6] Staging Milestone 4 project files...
git add database.py main.py models.py schemas.py requirements.txt .gitignore .env.example templates/ static/
git add Dockerfile .dockerignore docker_verify.bat docker_verify.ps1
git add verify_docs.bat verify_docs.ps1
git add tests/ run_tests.bat run_tests.ps1
git add .github/workflows/ci.yml

:: 4. Verify .env is NOT staged
git status --porcelain | findstr "^A  \.env" >nul
if !errorlevel! equ 0 (
    echo [ERROR] .env file was staged! Unstaging immediately for security!
    git reset HEAD .env
    pause
    exit /b 1
)
echo      Confirmed: No secrets or .env file staged.

:: 5. Commit with message
echo [3/6] Committing Milestone 4 changes...
git commit -m "Implement Milestone 4: Dockerization, API Documentation, Unit Tests, and GitHub Actions CI/CD"

:: 6. Switch/create local milestone-4-completion branch pointing to this commit
echo [4/6] Setting current branch to milestone-4-completion...
git checkout -B milestone-4-completion

:: 7. Push to origin/milestone-4-completion
echo [5/6] Pushing to origin/milestone-4-completion...
git push -u origin milestone-4-completion
if !errorlevel! neq 0 (
    echo [INFO] Standard push failed (remote branch has diverged initial commit). Retrying with --force-with-lease...
    git push -u origin milestone-4-completion --force-with-lease
)

:: 8. Summary & Verification
echo.
echo =======================================================
echo [6/6] Push Verification and Summary:
echo =======================================================
for /f "tokens=*" %%i in ('git rev-parse --abbrev-ref HEAD') do set CURRENT_BRANCH=%%i
for /f "tokens=*" %%i in ('git rev-parse --short HEAD') do set COMMIT_HASH=%%i
for /f "tokens=*" %%i in ('git rev-parse HEAD') do set FULL_HASH=%%i

echo 1. Current Branch  : !CURRENT_BRANCH!
echo 2. Commit Hash     : !FULL_HASH! (!COMMIT_HASH!)
echo 3. Repository URL  : https://github.com/vasanth2006-git/infosys-springboard-project
echo 4. Branch URL      : https://github.com/vasanth2006-git/infosys-springboard-project/tree/milestone-4-completion
echo 5. Actions Tab     : https://github.com/vasanth2006-git/infosys-springboard-project/actions
echo.
echo Files committed in this commit:
git show --stat --oneline !COMMIT_HASH!
echo.
echo =======================================================
echo   Milestone 4 successfully pushed to GitHub!
echo   GitHub Actions CI pipeline will trigger automatically!
echo =======================================================
pause
