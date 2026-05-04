#!/usr/bin/env bash
# TZG Dashboard Generator + Auto Deploy (macOS)
# 用法：
#   ./generate_and_deploy.sh             手動：只抓當月，瀏覽器看得見
#   ./generate_and_deploy.sh --shutdown  排程：抓上月 1 號~今天，headless，跑完睡眠
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON="${TZG_PYTHON:-python3}"
MODE="${1:-}"

echo
echo "==================================================="
echo " TZG Dashboard Generator + Auto Deploy"
echo "==================================================="
echo

# ============ Step 1: Python check ============
if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "ERROR: $PYTHON not found! 請先安裝 Python 3。"
    exit 1
fi
echo "[1/6] Python OK ($($PYTHON --version))"

# ============ Step 2: data folder check ============
if [ ! -d "data" ]; then
    echo "ERROR: data directory not found!"
    exit 1
fi
echo "[2/6] data directory OK"

# ============ Step 3: script check ============
if [ ! -f "generate_daily.py" ]; then
    echo "ERROR: generate_daily.py not found!"
    exit 1
fi
echo "[3/6] generate_daily.py OK"

# ============ Step 4: Git check ============
if ! command -v git >/dev/null 2>&1; then
    echo "ERROR: Git not found!"
    exit 1
fi
echo "[4/6] Git OK"
echo

# ============ Step 5a: Auto Download from Shopline ============
if [ -f ".env" ]; then
    TODAY="$(date +%Y-%m-%d)"
    # 算「上月 1 號」與「上月 YYYY-MM」（macOS BSD date）
    LASTMONTH_START="$(date -v-1m -v1d +%Y-%m-%d)"
    LASTMONTH="$(date -v-1m +%Y-%m)"

    if [ "$MODE" = "--shutdown" ]; then
        echo "==================================================="
        echo " Downloading from Shopline (rolling window, headless)"
        echo " Range: $LASTMONTH_START ~ $TODAY"
        echo "==================================================="
        echo
        TZG_HEADLESS=1 "$PYTHON" auto_shopline.py --start "$LASTMONTH_START" --end "$TODAY"
        rc=$?
        if [ $rc -ne 0 ]; then
            echo "WARNING: Shopline download failed. Continuing with existing data..."
            echo
        else
            echo "[5a] Shopline rolling-window download OK"
            echo
            echo " Rebuilding last-month archive ($LASTMONTH)..."
            "$PYTHON" generate_monthly_archive.py --month "$LASTMONTH" --force \
                || echo "WARNING: Last-month archive rebuild failed, continuing..."
            echo
            echo " Cleanup old downloads..."
            "$PYTHON" cleanup_old_downloads.py
            echo
        fi
    else
        echo "==================================================="
        echo " Downloading from Shopline (current month, manual)"
        echo "==================================================="
        echo
        "$PYTHON" auto_shopline.py
        if [ $? -ne 0 ]; then
            echo "WARNING: Shopline download failed. Continuing with existing data..."
            echo
        else
            echo "[5a] Shopline download OK"
            echo
        fi
    fi
else
    echo "[5a] .env not found, skipping auto-download"
    echo "     To enable: cp .env.example .env and fill in credentials"
    echo
fi

# ============ Step 5: Generate Dashboard ============
echo "==================================================="
echo " Generating Dashboard..."
echo "==================================================="
echo
if ! "$PYTHON" generate_daily.py; then
    echo
    echo "ERROR: Dashboard generation failed!"
    exit 1
fi
echo
echo "[5/6] Dashboard generated OK"
echo

# ============ Step 5b: Generate Monthly Review ============
echo "==================================================="
echo " Generating Monthly Review..."
echo "==================================================="
echo
if ! "$PYTHON" generate_monthly_review.py; then
    echo "WARNING: Monthly review generation failed, continuing..."
    echo
else
    echo "[5b/6] Monthly review generated OK"
    echo
fi

# ============ Step 6: Git commit + push ============
echo "==================================================="
echo " Deploying to GitHub..."
echo "==================================================="
echo

if [ ! -d ".git" ]; then
    echo "ERROR: This folder is not a Git repository!"
    exit 1
fi

TIMESTAMP="$(date +'%Y-%m-%d %H:%M')"

git add output/dashboard_latest.html
[ -f "output/monthly_review.html" ] && git add output/monthly_review.html

if git diff --cached --quiet; then
    echo "No changes to deploy. Dashboard content is identical."
    echo
else
    if ! git commit -m "Update dashboard $TIMESTAMP"; then
        echo "ERROR: Git commit failed!"
        exit 1
    fi
    if ! git push origin main; then
        echo "ERROR: Git push failed!"
        echo "Possible reasons: 未登入 GitHub / 網路 / 分支衝突"
        exit 1
    fi
    echo
    echo "[6/6] Deployed to GitHub OK"
    echo
fi

echo "==================================================="
echo " SUCCESS! All done."
echo "==================================================="
echo
echo "Your dashboard is now live on GitHub Pages."
echo "It may take 1-2 minutes for the new version to appear."
echo

# 手動模式：開啟本機 preview
if [ "$MODE" != "--shutdown" ] && [ -f "output/dashboard_latest.html" ]; then
    echo "Opening local preview..."
    open "output/dashboard_latest.html"
fi

# 排程模式：跳出睡眠提示（不需 sudo）
if [ "$MODE" = "--shutdown" ]; then
    "$SCRIPT_DIR/sleep_prompt.sh" &
fi
