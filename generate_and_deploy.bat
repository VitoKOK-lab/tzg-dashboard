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
"C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe" --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python from https://www."C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe".org/downloads/
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

REM ============ Step 5a: Auto Download from Shopline ============
if exist ".env" (
    REM ── 取得今天日期 ──
    for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value ^| find "="') do set _dt=%%I
    set _YEAR=!_dt:~0,4!
    set _MONTH=!_dt:~4,2!
    set _DAY=!_dt:~6,2!
    set /a _DAYNUM=1!_DAY! - 100
    set _TODAY=!_YEAR!-!_MONTH!-!_DAY!

    REM ── 算出「上個月 1 號」（給 1-7 號廣域下載用）──
    set /a _LM_M=1!_MONTH! - 100 - 1
    set _LM_Y=!_YEAR!
    if !_LM_M! LEQ 0 (
        set /a _LM_M=12
        set /a _LM_Y=!_YEAR! - 1
    )
    if !_LM_M! LSS 10 (set _LM_MM=0!_LM_M!) else (set _LM_MM=!_LM_M!)
    set _LASTMONTH=!_LM_Y!-!_LM_MM!
    set _LASTMONTH_START=!_LM_Y!-!_LM_MM!-01

    REM ── 排程模式（--shutdown）+ 每月 1-7 號：一次抓「上月 1 號 ~ 今天」 ──
    REM    這樣只下載 1 次，同時涵蓋上月補抓（防漏抓+跨月退款）和當月最新資料。
    REM    手動執行：只抓當月（預設行為）→ 等待時間最短。
    if "%1"=="--shutdown" if !_DAYNUM! LEQ 7 (
        echo ===================================================
        echo  Downloading from Shopline ^(wide range: !_LASTMONTH_START! ~ !_TODAY!^)
        echo  Day !_DAYNUM!/7 of month - includes last-month safety net
        echo ===================================================
        echo.
        "C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe" auto_shopline.py --start !_LASTMONTH_START! --end !_TODAY!
        if errorlevel 1 (
            echo WARNING: Shopline download failed. Continuing with existing data...
            echo.
        ) else (
            echo [5a] Shopline wide-range download OK
            echo.
            REM 重建上月封存（從剛下載的 shopline_*.xlsx 撈該月資料）
            echo  Rebuilding last-month archive ^(!_LASTMONTH!^)...
            "C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe" generate_monthly_archive.py --month !_LASTMONTH! --force
            if errorlevel 1 (
                echo WARNING: Last-month archive rebuild failed, continuing...
                echo.
            ) else (
                echo [5a+] Last-month archive OK
                echo.
            )
        )
    ) else (
        echo ===================================================
        echo  Downloading from Shopline ^(current month^)...
        echo ===================================================
        echo.
        "C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe" auto_shopline.py
        if errorlevel 1 (
            echo WARNING: Shopline download failed. Continuing with existing data...
            echo.
        ) else (
            echo [5a] Shopline download OK
            echo.
        )
    )
) else (
    echo [5a] .env not found, skipping auto-download
    echo      To enable: copy .env.example .env and fill in credentials
    echo.
)

REM ============ Step 5: Generate Dashboard ============
echo ===================================================
echo  Generating Dashboard...
echo ===================================================
echo.

"C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe" generate_daily.py

if errorlevel 1 (
    echo.
    echo ERROR: Dashboard generation failed!
    pause
    exit /b 1
)

echo.
echo [5/6] Dashboard generated OK
echo.

REM ============ Step 5b: Generate Monthly Review ============
echo ===================================================
echo  Generating Monthly Review...
echo ===================================================
echo.

"C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe" generate_monthly_review.py
if errorlevel 1 (
    echo WARNING: Monthly review generation failed, continuing...
    echo.
) else (
    echo [5b/6] Monthly review generated OK
    echo.
)


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

REM Stage dashboard files
git add output/dashboard_latest.html
if exist "output/monthly_review.html" git add output/monthly_review.html

REM Check if there are changes
git diff-index --quiet HEAD output/dashboard_latest.html output/monthly_review.html 2>nul
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

REM 如果以 --shutdown 參數執行（排程自動執行模式），完成後詢問關機
if "%1"=="--shutdown" (
    powershell.exe -WindowStyle Normal -ExecutionPolicy Bypass -File "%~dp0shutdown_prompt.ps1"
) else (
    pause
)
endlocal
