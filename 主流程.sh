#!/usr/bin/env bash
# TZG Dashboard Generator + Auto Deploy (macOS)
# 用法：
#   ./generate_and_deploy.sh             手動：只抓當月，瀏覽器看得見
#   ./generate_and_deploy.sh --auto      排程白天：抓上月 1 號~今天，headless，不睡眠
#   ./generate_and_deploy.sh --shutdown  排程晚上：抓上月 1 號~今天，headless，跑完睡眠
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

# 自動拉取最新版本（讓本機端的開發改動先同步進來，避免之後 push 衝突）
echo "==================================================="
echo " Pulling latest from GitHub..."
echo "==================================================="
if git pull --rebase --autostash origin main; then
    echo "[4b/6] Git pull OK"
else
    echo "WARNING: git pull 失敗，繼續用本地版本跑（之後 push 可能衝突）"
fi
echo

# ============ Step 5a: Auto Download from Shopline ============
if [ -f ".env" ]; then
    TODAY="$(date +%Y-%m-%d)"
    # 算各種日期（macOS BSD date）
    LASTMONTH_START="$(date -v-1m -v1d +%Y-%m-%d)"           # 上月 1 號
    LASTMONTH_END="$(date -v1d -v-1d +%Y-%m-%d)"             # 上月最後一天（本月 1 號 - 1）
    THISMONTH_START="$(date -v1d +%Y-%m-%d)"                 # 本月 1 號
    LASTMONTH="$(date -v-1m +%Y-%m)"

    if [ "$MODE" = "--shutdown" ] || [ "$MODE" = "--auto" ]; then
        echo "==================================================="
        echo " Downloading from Shopline (split: last month + this month)"
        echo "   Range A (上月): $LASTMONTH_START ~ $LASTMONTH_END"
        echo "   Range B (本月): $THISMONTH_START ~ $TODAY"
        echo "==================================================="
        echo "  ※ 拆兩段抓：Shopline 報表跨月查詢常漏抓本月即時訂單，"
        echo "    分開抓比較能拿到本月新單。"
        echo

        echo "--- [A] 抓上月整月 ---"
        TZG_HEADLESS=1 "$PYTHON" auto_shopline.py --start "$LASTMONTH_START" --end "$LASTMONTH_END"
        rc_a=$?

        echo
        echo "--- [B] 抓本月至今 ---"
        TZG_HEADLESS=1 "$PYTHON" auto_shopline.py --start "$THISMONTH_START" --end "$TODAY"
        rc_b=$?

        if [ $rc_a -ne 0 ] && [ $rc_b -ne 0 ]; then
            echo "WARNING: Shopline 兩段下載都失敗（A=$rc_a, B=$rc_b）。沿用既有資料..."
            echo
        else
            if [ $rc_a -ne 0 ]; then
                echo "WARNING: 上月下載失敗（A=$rc_a），但本月成功。"
            fi
            if [ $rc_b -ne 0 ]; then
                echo "WARNING: 本月下載失敗（B=$rc_b），但上月成功。"
            fi
            echo "[5a] Shopline download OK"
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

# 資料新鮮度檢查（資料 > 24h 沒更新 → macOS 通知 + 警示音）
STALE_HOURS=$("$PYTHON" -c "
import re
from datetime import datetime
try:
    html = open('output/dashboard_latest.html', encoding='utf-8').read()
    m = re.search(r'\"data_as_of\":\s*\"([^\"]+)\"', html)
    if m:
        d = datetime.strptime(m.group(1), '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        print(int(max(0, (datetime.now() - d).total_seconds() / 3600)))
    else:
        print(0)
except Exception:
    print(0)
" 2>/dev/null || echo "0")

if [ "$STALE_HOURS" -gt 24 ]; then
    echo "⚠️  資料停滯 $STALE_HOURS 小時，跳 macOS 通知提醒"
    osascript -e "display notification \"資料停滯 $STALE_HOURS 小時，Shopline 可能 session 過期，請進系統重新登入\" with title \"⚠️ TZG Dashboard 同步異常\" sound name \"Sosumi\"" 2>/dev/null || true
fi
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

# 手動模式：開啟本機 preview（排程模式不開）
if [ -z "$MODE" ] && [ -f "output/dashboard_latest.html" ]; then
    echo "Opening local preview..."
    open "output/dashboard_latest.html"
fi
# 註：23:59 排程跑完後的關機由 pmset repeat shutdown 排定（00:10），不在此腳本處理
