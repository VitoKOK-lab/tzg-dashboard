@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

cd /d "%~dp0"

echo.
echo ===================================================
echo  TZG Dashboard Generator + Auto Deploy
echo ===================================================
echo.

REM ============ Step 1: Python check ============
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [1/6] Python OK

REM ============ Step 2: data folder check ============
if not exist "data" (
    echo ERROR: data directory not found!
    pause
    exit /b 1
)
echo [2/6] data directory OK

REM ============ Step 3: script check ============
if not exist "generate_daily.py" (
    echo ERROR: generate_daily.py not found!
    pause
    exit /b 1
)
echo [3/6] generate_daily.py OK

REM ============ Step 4: Git check ============
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git not found!
    echo Please install Git from https://git-scm.com/download/win
    pause
    exit /b 1
)
echo [4/6] Git OK
echo.

REM ============ Step 5: Generate Dashboard ============
echo ===================================================
echo  Generating Dashboard...
echo ===================================================
echo.

python generate_daily.py

if errorlevel 1 (
    echo.
    echo ERROR: Dashboard generation failed!
    pause
    exit /b 1
)

echo.
echo [5/6] Dashboard generated OK
echo.

REM ============ Step 6: Git commit + push ============
echo ===================================================
echo  Deploying to GitHub...
echo ===================================================
echo.

REM Check if current folder is a git repo
if not exist ".git" (
    echo ERROR: This folder is not a Git repository!
    echo Please run: git init  and link it to your GitHub repo first.
    pause
    exit /b 1
)

REM Get current date/time for commit message
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value ^| find "="') do set datetime=%%I
set TIMESTAMP=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2% %datetime:~8,2%:%datetime:~10,2%

REM Stage only the output file (you can change this to "git add ." if you want to push everything)
git add output/dashboard_latest.html

REM Check if there are changes
git diff-index --quiet HEAD output/dashboard_latest.html
if !errorlevel! == 0 (
    echo No changes to deploy. Dashboard content is identical.
    echo.
    goto :end
)

REM Commit
git commit -m "Update dashboard %TIMESTAMP%"
if errorlevel 1 (
    echo ERROR: Git commit failed!
    pause
    exit /b 1
)

REM Push
git push origin main
if errorlevel 1 (
    echo ERROR: Git push failed!
    echo Possible reasons:
    echo   - Not logged in to GitHub
    echo   - Network issue
    echo   - Branch conflict
    pause
    exit /b 1
)

echo.
echo [6/6] Deployed to GitHub OK
echo.

:end
echo ===================================================
echo  SUCCESS! All done.
echo ===================================================
echo.
echo Your dashboard is now live on GitHub Pages.
echo It may take 1-2 minutes for the new version to appear.
echo.

REM Open latest HTML locally for preview
if exist "output\dashboard_latest.html" (
    echo Opening local preview...
    start "" "output\dashboard_latest.html"
)

pause
endlocal
